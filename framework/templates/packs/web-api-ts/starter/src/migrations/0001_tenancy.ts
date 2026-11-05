// 0001 — tenant, người dùng, phiên đăng nhập; vai trò `app_rw` và hàm ngữ cảnh `app.current_tenant()`.
// Migration đã áp ở môi trường chung KHÔNG sửa — sửa bằng migration mới. Mỗi migration có `down` đã chạy thử trong test.
// Mỗi khối SQL mở bằng `SET LOCAL lock_timeout`/`statement_timeout` (DB-MIG-005: FK tới bảng đang phục vụ cũng khoá bảng
// được trỏ) — hết thời gian thì migration lỗi, transaction lùi, chạy lại `migrate up`; migration mới làm theo.
import { type Kysely, sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    SET LOCAL lock_timeout = '5s';
    SET LOCAL statement_timeout = '60s';
    DO $$ BEGIN
      IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_rw') THEN
        CREATE ROLE app_rw NOLOGIN;
      END IF;
    END $$;
    CREATE SCHEMA app;
    CREATE FUNCTION app.current_tenant() RETURNS uuid LANGUAGE plpgsql STABLE AS $f$
    DECLARE v text := current_setting('app.tenant_id', true);
    BEGIN
      IF v IS NULL OR v = '' THEN
        RAISE EXCEPTION 'app.tenant_id chưa đặt' USING ERRCODE = '42501', HINT = 'TENANT_CONTEXT_MISSING';
      END IF;
      RETURN v::uuid;
    END $f$;
    GRANT USAGE ON SCHEMA app TO app_rw;
    CREATE TABLE tenants (
      id uuid PRIMARY KEY,
      name text NOT NULL CHECK (length(btrim(name)) BETWEEN 1 AND 200),
      created_at timestamptz NOT NULL DEFAULT now()
    );
    CREATE TABLE users (
      id uuid PRIMARY KEY,
      tenant_id uuid NOT NULL REFERENCES tenants (id),
      email text NOT NULL UNIQUE CHECK (email = lower(email)),
      password_hash text NOT NULL,
      created_at timestamptz NOT NULL DEFAULT now()
    );
    CREATE TABLE sessions (
      token_hash text PRIMARY KEY,
      user_id uuid NOT NULL REFERENCES users (id) ON DELETE CASCADE,
      tenant_id uuid NOT NULL REFERENCES tenants (id),
      expires_at timestamptz NOT NULL,
      created_at timestamptz NOT NULL DEFAULT now()
    );
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  // Vai trò `app_rw` là của cả cluster (cơ sở dữ liệu khác có thể dùng) — không xoá ở đây.
  await sql`
    SET LOCAL lock_timeout = '5s';
    SET LOCAL statement_timeout = '60s';
    DROP TABLE sessions;
    DROP TABLE users;
    DROP TABLE tenants;
    REVOKE USAGE ON SCHEMA app FROM app_rw;
    DROP FUNCTION app.current_tenant();
    DROP SCHEMA app;
  `.execute(db);
}
