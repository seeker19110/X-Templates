// 0003 — hàng đợi việc nền theo tenant: khoá ý định chống trùng (tenant + kind + idempotency_key), lease
// (`locked_until`) để việc của worker chết được lấy lại, `job_effects` ghi tác dụng phụ đúng một lần (khoá chính job_id).
import { type Kysely, sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE jobs (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
      tenant_id uuid NOT NULL DEFAULT app.current_tenant() REFERENCES tenants (id),
      kind text NOT NULL CHECK (length(kind) BETWEEN 1 AND 100),
      idempotency_key text NOT NULL CHECK (length(idempotency_key) BETWEEN 1 AND 200),
      payload jsonb NOT NULL DEFAULT '{}',
      status text NOT NULL DEFAULT 'queued' CHECK (status IN ('queued', 'running', 'done', 'failed')),
      attempts integer NOT NULL DEFAULT 0 CHECK (attempts >= 0),
      locked_by text,
      locked_until timestamptz,
      last_error text,
      created_at timestamptz NOT NULL DEFAULT now(),
      updated_at timestamptz NOT NULL DEFAULT now(),
      UNIQUE (tenant_id, kind, idempotency_key)
    );
    CREATE INDEX jobs_ready ON jobs (status, locked_until);
    CREATE TABLE job_effects (
      job_id uuid PRIMARY KEY REFERENCES jobs (id),
      tenant_id uuid NOT NULL DEFAULT app.current_tenant() REFERENCES tenants (id),
      effect text NOT NULL,
      created_at timestamptz NOT NULL DEFAULT now()
    );
    ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
    ALTER TABLE jobs FORCE ROW LEVEL SECURITY;
    CREATE POLICY jobs_tenant ON jobs
      USING (tenant_id = app.current_tenant()) WITH CHECK (tenant_id = app.current_tenant());
    ALTER TABLE job_effects ENABLE ROW LEVEL SECURITY;
    ALTER TABLE job_effects FORCE ROW LEVEL SECURITY;
    CREATE POLICY job_effects_tenant ON job_effects
      USING (tenant_id = app.current_tenant()) WITH CHECK (tenant_id = app.current_tenant());
    GRANT SELECT, INSERT, UPDATE ON jobs, job_effects TO app_rw;
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`
    REVOKE ALL ON jobs, job_effects FROM app_rw;
    DROP TABLE job_effects;
    DROP TABLE jobs;
  `.execute(db);
}
