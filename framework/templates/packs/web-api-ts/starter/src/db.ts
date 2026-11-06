// Kết nối và ngữ cảnh tenant. Mọi truy vấn dữ liệu nghiệp vụ chạy qua `withTenant`: vai trò `app_rw` (không sở hữu bảng,
// chịu RLS) + `app.tenant_id` đặt bằng SET LOCAL trong transaction — hết transaction là hết ngữ cảnh, kết nối trả về pool
// không mang tenant cũ. Thiếu ngữ cảnh → hàm `app.current_tenant()` ném lỗi (đóng an toàn).
import { type Generated, Kysely, PostgresDialect, sql, type Transaction } from "kysely";
import pg from "pg";

export interface Database {
  tenants: { id: string; name: string; created_at: Generated<Date> };
  users: {
    id: string;
    tenant_id: string;
    email: string;
    password_hash: string;
    created_at: Generated<Date>;
  };
  sessions: {
    token_hash: string;
    user_id: string;
    tenant_id: string;
    expires_at: Date;
    created_at: Generated<Date>;
  };
  notes: {
    id: Generated<string>;
    tenant_id: Generated<string>;
    body: string;
    created_by: string;
    created_at: Generated<Date>;
  };
  jobs: {
    id: Generated<string>;
    tenant_id: Generated<string>;
    kind: string;
    idempotency_key: string;
    payload: unknown;
    status: Generated<"queued" | "running" | "done" | "failed">;
    attempts: Generated<number>;
    locked_by: string | null;
    locked_until: Date | null;
    lease_token: string | null;
    last_error: string | null;
    created_at: Generated<Date>;
    updated_at: Generated<Date>;
  };
  job_effects: {
    job_id: string;
    tenant_id: Generated<string>;
    effect: string;
    created_at: Generated<Date>;
  };
}

export type Db = Kysely<Database>;
export type Tx = Transaction<Database>;

// Giới hạn thời gian (AUD-DATA-008): DB treo/đầy kết nối → request lỗi nhanh thay vì treo tới timeout của proxy.
// `connectMs`: mở kết nối mới VÀ chờ kết nối rảnh của pool; `statementMs`: `statement_timeout` của phiên cho mọi truy vấn
// ứng dụng (migration tự đặt `SET LOCAL statement_timeout` riêng, ghi đè trong transaction của nó).
export interface Timeouts {
  connectMs: number;
  statementMs: number;
}

export const DEFAULT_TIMEOUTS: Timeouts = { connectMs: 5_000, statementMs: 15_000 };

function positiveMs(env: NodeJS.ProcessEnv, key: string, fallback: number): number {
  const raw = env[key];
  if (raw === undefined || raw === "") return fallback;
  const n = Number(raw);
  // 0 với `pg` nghĩa là KHÔNG giới hạn — không cho tắt giới hạn qua env một cách vô tình.
  if (!/^\d+$/.test(raw) || !Number.isSafeInteger(n) || n < 1) {
    throw new Error(`${key} phải là số nguyên mili giây ≥ 1`);
  }
  return n;
}

// Ghi đè qua env: PG_CONNECT_TIMEOUT_MS, PG_STATEMENT_TIMEOUT_MS (giá trị sai → ném lỗi lúc khởi động).
export function timeoutsFromEnv(env: NodeJS.ProcessEnv = process.env): Timeouts {
  return {
    connectMs: positiveMs(env, "PG_CONNECT_TIMEOUT_MS", DEFAULT_TIMEOUTS.connectMs),
    statementMs: positiveMs(env, "PG_STATEMENT_TIMEOUT_MS", DEFAULT_TIMEOUTS.statementMs),
  };
}

export function createDb(url: string, max = 10, timeouts: Timeouts = timeoutsFromEnv()): Db {
  const pool = new pg.Pool({
    connectionString: url,
    max,
    connectionTimeoutMillis: timeouts.connectMs,
    statement_timeout: timeouts.statementMs,
  });
  return new Kysely<Database>({ dialect: new PostgresDialect({ pool }) });
}

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;

export async function withTenant<T>(db: Db, tenantId: string, fn: (tx: Tx) => Promise<T>): Promise<T> {
  if (!UUID_RE.test(tenantId)) {
    throw new Error("tenant_id không hợp lệ");
  }
  return db.transaction().execute(async (tx) => {
    await sql`SET LOCAL ROLE app_rw`.execute(tx);
    await sql`SELECT set_config('app.tenant_id', ${tenantId}, true)`.execute(tx);
    return fn(tx);
  });
}
