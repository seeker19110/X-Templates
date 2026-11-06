// Worker hàng đợi (tuyến API/worker, ADR-0068 lát D). Bảo đảm:
// - enqueue lũy đẳng: cùng (tenant, kind, idempotency_key) → cùng một job (ON CONFLICT DO NOTHING rồi đọc lại);
// - claim bằng FOR UPDATE SKIP LOCKED + lease `locked_until`: worker chết/hết giờ → lease hết hạn → worker khác lấy lại;
// - mỗi lần claim một `lease_token` mới; `complete`/`fail` chỉ tác động lần chạy mang đúng token và còn `running` —
//   lần chạy cũ (kể cả cùng workerId) không hoàn tất/reset được lần chạy mới (AUD-DATA-006);
// - tác dụng phụ ghi vào `job_effects` (khoá chính job_id) CÙNG transaction với đánh dấu `done` — chạy lại sau crash
//   không ghi hai lần BẢN GHI effect; tác dụng phụ ra ngoài DB (gửi mail, gọi API) vẫn at-least-once — handler phải lũy
//   đẳng phía bên kia (vd gửi kèm job id làm khoá ý định). `reconcile` liệt kê job `done` thiếu effect hoặc effect thiếu
//   job `done` (phải rỗng).
import { sql } from "kysely";
import { type Db, type Tx, UUID_RE, withTenant } from "./db.ts";

export const MAX_ATTEMPTS = 5;

export async function enqueue(
  db: Db,
  tenantId: string,
  kind: string,
  key: string,
  payload: Record<string, unknown>,
): Promise<string> {
  return withTenant(db, tenantId, async (tx) => {
    await tx
      .insertInto("jobs")
      .values({ kind, idempotency_key: key, payload: JSON.stringify(payload) })
      .onConflict((oc) => oc.columns(["tenant_id", "kind", "idempotency_key"]).doNothing())
      .execute();
    const row = await tx
      .selectFrom("jobs")
      .select("id")
      .where("kind", "=", kind)
      .where("idempotency_key", "=", key)
      .executeTakeFirstOrThrow();
    return row.id;
  });
}

// Quyền trên một lần chạy: id job + token của lần claim đó.
export interface Lease {
  id: string;
  lease: string;
}

export interface Claimed extends Lease {
  kind: string;
  payload: unknown;
  attempts: number;
}

// Worker nhận việc theo loại (`kind`): mỗi loại một hàng đợi logic, việc loại khác không chặn nhau.
export async function claim(
  db: Db,
  tenantId: string,
  kind: string,
  workerId: string,
  leaseMs: number,
): Promise<Claimed | null> {
  return withTenant(db, tenantId, async (tx) => {
    // Job hết lượt mà worker cuối chết (lease hết hạn) → `failed`, không kẹt `running` mãi (review lát B).
    await sql`
      UPDATE jobs SET status = 'failed', locked_by = NULL, locked_until = NULL, lease_token = NULL, updated_at = now(),
        last_error = coalesce(last_error, 'lease hết hạn ở lần thử cuối')
      WHERE kind = ${kind} AND status = 'running' AND locked_until < now() AND attempts >= ${MAX_ATTEMPTS}`.execute(
      tx,
    );
    // `locked_by` chỉ để quan sát (ai đang chạy); quyền hoàn tất/báo lỗi nằm ở `lease_token`.
    const res = await sql<Claimed>`
      UPDATE jobs SET status = 'running', attempts = attempts + 1, locked_by = ${workerId},
        lease_token = gen_random_uuid(),
        locked_until = now() + make_interval(secs => ${leaseMs / 1000}), updated_at = now()
      WHERE id = (
        SELECT id FROM jobs
        WHERE kind = ${kind} AND attempts < ${MAX_ATTEMPTS}
          AND (status = 'queued' OR (status = 'running' AND locked_until < now()))
        ORDER BY created_at LIMIT 1 FOR UPDATE SKIP LOCKED)
      RETURNING id, lease_token AS lease, kind, payload, attempts`.execute(tx);
    return res.rows[0] ?? null;
  });
}

// Hoàn tất: chỉ lần chạy còn giữ lease (đúng token, chưa hết hạn) mới được ghi; effect và `done` cùng một transaction.
export async function complete(db: Db, tenantId: string, job: Lease, effect: string): Promise<boolean> {
  if (!UUID_RE.test(job.lease)) {
    return false; // token không phải do `claim` cấp: không có quyền, không để Postgres ném lỗi cú pháp uuid
  }
  return withTenant(db, tenantId, async (tx: Tx) => {
    const owned = await tx
      .updateTable("jobs")
      .set({ status: "done", locked_by: null, locked_until: null, lease_token: null, updated_at: new Date() })
      .where("id", "=", job.id)
      .where("status", "=", "running")
      .where("lease_token", "=", job.lease)
      .where("locked_until", ">=", sql<Date>`now()`) // đồng hồ của DB, không phải của tiến trình
      .executeTakeFirst();
    if (Number(owned.numUpdatedRows) !== 1) {
      return false;
    }
    await tx.insertInto("job_effects").values({ job_id: job.id, effect }).execute();
    return true;
  });
}

// Báo lỗi lần chạy: trả `false` khi lần chạy đã mất quyền (job đã được claim lại, đã xong, hoặc token sai) — không đụng
// lần chạy khác. Lease đã hết hạn nhưng chưa ai claim lại thì vẫn trả job về hàng đợi (cùng token, không ai khác chạy).
export async function fail(db: Db, tenantId: string, job: Lease, error: string): Promise<boolean> {
  if (!UUID_RE.test(job.lease)) {
    return false;
  }
  const res = await withTenant(db, tenantId, (tx) =>
    tx
      .updateTable("jobs")
      .set(() => ({
        status: sql<
          "failed" | "queued"
        >`CASE WHEN attempts >= ${MAX_ATTEMPTS} THEN 'failed' ELSE 'queued' END`,
        locked_by: null,
        locked_until: null,
        lease_token: null,
        last_error: error.slice(0, 1000),
        updated_at: new Date(),
      }))
      .where("id", "=", job.id)
      .where("status", "=", "running")
      .where("lease_token", "=", job.lease)
      .executeTakeFirst(),
  );
  return Number(res.numUpdatedRows) === 1;
}

export interface Mismatch {
  job_id: string;
  problem: "done_without_effect" | "effect_without_done";
}

export async function reconcile(db: Db, tenantId: string): Promise<Mismatch[]> {
  return withTenant(db, tenantId, async (tx) => {
    const res = await sql<Mismatch>`
      SELECT j.id AS job_id, 'done_without_effect' AS problem
        FROM jobs j LEFT JOIN job_effects e ON e.job_id = j.id WHERE j.status = 'done' AND e.job_id IS NULL
      UNION ALL
      SELECT e.job_id, 'effect_without_done' FROM job_effects e JOIN jobs j ON j.id = e.job_id WHERE j.status <> 'done'
      ORDER BY 1`.execute(tx);
    return res.rows;
  });
}
