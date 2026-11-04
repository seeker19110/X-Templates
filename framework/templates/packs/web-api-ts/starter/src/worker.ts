// Worker hàng đợi (tuyến API/worker, ADR-0068 lát D). Bảo đảm:
// - enqueue lũy đẳng: cùng (tenant, kind, idempotency_key) → cùng một job (ON CONFLICT DO NOTHING rồi đọc lại);
// - claim bằng FOR UPDATE SKIP LOCKED + lease `locked_until`: worker chết/hết giờ → lease hết hạn → worker khác lấy lại;
// - tác dụng phụ ghi vào `job_effects` (khoá chính job_id) CÙNG transaction với đánh dấu `done` — chạy lại sau crash
//   không ghi hai lần; `reconcile` liệt kê job `done` thiếu effect hoặc effect thiếu job `done` (phải rỗng).
import { sql } from "kysely";
import { type Db, type Tx, withTenant } from "./db.ts";

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

export interface Claimed {
  id: string;
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
    const res = await sql<Claimed>`
      UPDATE jobs SET status = 'running', attempts = attempts + 1, locked_by = ${workerId},
        locked_until = now() + make_interval(secs => ${leaseMs / 1000}), updated_at = now()
      WHERE id = (
        SELECT id FROM jobs
        WHERE kind = ${kind} AND attempts < ${MAX_ATTEMPTS}
          AND (status = 'queued' OR (status = 'running' AND locked_until < now()))
        ORDER BY created_at LIMIT 1 FOR UPDATE SKIP LOCKED)
      RETURNING id, kind, payload, attempts`.execute(tx);
    return res.rows[0] ?? null;
  });
}

// Hoàn tất: chỉ worker còn giữ lease mới được ghi; effect và `done` cùng một transaction.
export async function complete(
  db: Db,
  tenantId: string,
  workerId: string,
  jobId: string,
  effect: string,
): Promise<boolean> {
  return withTenant(db, tenantId, async (tx: Tx) => {
    const owned = await tx
      .updateTable("jobs")
      .set({ status: "done", locked_by: null, locked_until: null, updated_at: new Date() })
      .where("id", "=", jobId)
      .where("status", "=", "running")
      .where("locked_by", "=", workerId)
      .where("locked_until", ">=", sql<Date>`now()`) // đồng hồ của DB, không phải của tiến trình
      .executeTakeFirst();
    if (Number(owned.numUpdatedRows) !== 1) {
      return false;
    }
    await tx.insertInto("job_effects").values({ job_id: jobId, effect }).execute();
    return true;
  });
}

export async function fail(
  db: Db,
  tenantId: string,
  workerId: string,
  jobId: string,
  error: string,
): Promise<void> {
  await withTenant(db, tenantId, (tx) =>
    tx
      .updateTable("jobs")
      .set(() => ({
        status: sql<
          "failed" | "queued"
        >`CASE WHEN attempts >= ${MAX_ATTEMPTS} THEN 'failed' ELSE 'queued' END`,
        locked_by: null,
        locked_until: null,
        last_error: error.slice(0, 1000),
        updated_at: new Date(),
      }))
      .where("id", "=", jobId)
      .where("locked_by", "=", workerId)
      .execute(),
  );
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
