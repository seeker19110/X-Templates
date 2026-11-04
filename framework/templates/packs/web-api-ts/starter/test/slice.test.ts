// Lát dọc (research §5 của khung): migrate → đăng nhập → tạo dữ liệu → chặn tenant khác (API + RLS) → migration lùi/tiến.

import type { Kysely } from "kysely";
import { sql } from "kysely";
import { afterAll, beforeAll, describe, expect, it } from "vitest";
import type { Db } from "../src/db.ts";
import { withTenant } from "../src/db.ts";
import { MIGRATIONS, migrate } from "../src/migrate.ts";
import { call, dropDatabase, freshDatabase, loginAs, seedTenant, serve, type Tenant } from "./helpers.ts";

let db: Db;
let name: string;
let base: string;
let close: () => Promise<void>;
let a: Tenant;
let b: Tenant;

beforeAll(async () => {
  ({ db, name } = await freshDatabase());
  ({ base, close } = await serve(db));
  a = await seedTenant(db, "a");
  b = await seedTenant(db, "b");
});

afterAll(async () => {
  await close();
  await dropDatabase(db, name);
});

describe("đăng nhập", () => {
  it("sai mật khẩu → 401, không lộ email có tồn tại", async () => {
    const wrong = await call(base, "POST", "/v1/login", { email: a.email, password: "sai" });
    const ghost = await call(base, "POST", "/v1/login", { email: "khong-co@example.test", password: "sai" });
    expect(wrong).toEqual({ status: 401, json: { error: "invalid_credentials" } });
    expect(ghost).toEqual(wrong);
  });

  it("không token / token giả → 401", async () => {
    expect((await call(base, "GET", "/v1/notes")).status).toBe(401);
    expect((await call(base, "GET", "/v1/notes", undefined, "gia")).status).toBe(401);
  });
});

describe("cô lập tenant", () => {
  it("tenant B không đọc được ghi chú của A qua API", async () => {
    const ta = await loginAs(base, a);
    const tb = await loginAs(base, b);
    const created = await call(base, "POST", "/v1/notes", { body: "bí mật của A" }, ta);
    expect(created.status).toBe(201);
    const id = String(created.json.id);
    expect((await call(base, "GET", `/v1/notes/${id}`, undefined, ta)).status).toBe(200);
    expect(await call(base, "GET", `/v1/notes/${id}`, undefined, tb)).toEqual({
      status: 404,
      json: { error: "not_found" },
    });
    const listB = await call(base, "GET", "/v1/notes", undefined, tb);
    expect(listB.json.notes).toEqual([]);
  });

  it("RLS chặn ở tầng cơ sở dữ liệu, kể cả khi truy vấn quên lọc tenant", async () => {
    await withTenant(db, a.id, (tx) =>
      tx.insertInto("notes").values({ body: "x", created_by: a.userId }).execute(),
    );
    const seenByB = await withTenant(db, b.id, (tx) => tx.selectFrom("notes").select("tenant_id").execute());
    expect(seenByB.every((r) => r.tenant_id === b.id)).toBe(true);
    const ofA = await sql<{
      n: number;
    }>`SELECT count(*)::int AS n FROM notes WHERE tenant_id = ${a.id}`.execute(db);
    expect(ofA.rows[0]?.n).toBeGreaterThan(0); // kết nối quản trị (bỏ qua RLS) thấy dòng của A — B thì không
    expect(seenByB).toEqual([]);
  });

  it("ghi dữ liệu mang tenant khác bị từ chối (WITH CHECK)", async () => {
    await expect(
      withTenant(db, b.id, (tx) =>
        tx
          .insertInto("notes")
          .values({ body: "giả mạo", created_by: b.userId, tenant_id: a.id } as never)
          .execute(),
      ),
    ).rejects.toThrow(/row-level security/);
  });

  it("thiếu ngữ cảnh tenant → lỗi, không trả dữ liệu", async () => {
    await expect(
      db.transaction().execute(async (tx) => {
        await sql`SET LOCAL ROLE app_rw`.execute(tx);
        return tx.selectFrom("notes").selectAll().execute();
      }),
    ).rejects.toThrow(/app.tenant_id/);
  });
});

describe("migration", () => {
  it("lùi hết rồi tiến lại: không còn bảng ứng dụng sau khi lùi, schema dựng lại đủ", async () => {
    const scratch = await freshDatabase();
    try {
      const raw = scratch.db as unknown as Kysely<unknown>;
      await migrate(raw, "reset");
      const left = await sql<{ n: number }>`
        SELECT count(*)::int AS n FROM pg_tables
        WHERE schemaname IN ('public', 'app') AND tablename NOT LIKE 'kysely_%'`.execute(raw);
      expect(left.rows[0]?.n).toBe(0);
      const steps = await migrate(raw, "up");
      expect(steps).toEqual(Object.keys(MIGRATIONS).map((m) => `Up ${m} Success`));
      const rls = await sql<{ relname: string }>`
        SELECT relname FROM pg_class WHERE relrowsecurity AND relforcerowsecurity ORDER BY relname`.execute(
        raw,
      );
      expect(rls.rows.map((r) => r.relname)).toEqual(["job_effects", "jobs", "notes"]);
    } finally {
      await dropDatabase(scratch.db, scratch.name);
    }
  });

  it("từng migration lùi một bước rồi tiến lại đều chạy", async () => {
    const scratch = await freshDatabase();
    try {
      const raw = scratch.db as unknown as Kysely<unknown>;
      for (const _ of Object.keys(MIGRATIONS)) {
        await migrate(raw, "down");
      }
      expect(await migrate(raw, "up")).toHaveLength(Object.keys(MIGRATIONS).length);
    } finally {
      await dropDatabase(scratch.db, scratch.name);
    }
  });
});
