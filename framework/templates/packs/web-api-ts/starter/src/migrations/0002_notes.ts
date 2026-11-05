// 0002 — dữ liệu nghiệp vụ mẫu `notes`, cô lập theo tenant bằng RLS (ENABLE + FORCE; `app_rw` không sở hữu bảng).
import { type Kysely, sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    SET LOCAL lock_timeout = '5s';
    SET LOCAL statement_timeout = '60s';
    CREATE TABLE notes (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
      tenant_id uuid NOT NULL DEFAULT app.current_tenant() REFERENCES tenants (id),
      body text NOT NULL CHECK (length(body) BETWEEN 1 AND 10000),
      created_by uuid NOT NULL REFERENCES users (id),
      created_at timestamptz NOT NULL DEFAULT now()
    );
    CREATE INDEX notes_tenant_created ON notes (tenant_id, created_at DESC);
    ALTER TABLE notes ENABLE ROW LEVEL SECURITY;
    ALTER TABLE notes FORCE ROW LEVEL SECURITY;
    CREATE POLICY notes_tenant ON notes
      USING (tenant_id = app.current_tenant())
      WITH CHECK (tenant_id = app.current_tenant());
    GRANT SELECT, INSERT, UPDATE, DELETE ON notes TO app_rw;
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`
    SET LOCAL lock_timeout = '5s';
    SET LOCAL statement_timeout = '60s';
    REVOKE ALL ON notes FROM app_rw;
    DROP TABLE notes;
  `.execute(db);
}
