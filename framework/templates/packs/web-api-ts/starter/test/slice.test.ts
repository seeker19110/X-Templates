// Lát dọc (research §5 của khung): migrate → đăng nhập → tạo dữ liệu → chặn tenant khác (API + RLS) → migration lùi/tiến.

import { connect } from "node:net";
import type { Kysely } from "kysely";
import { sql } from "kysely";
import { afterAll, beforeAll, describe, expect, it } from "vitest";
import { purgeExpiredSessions } from "../src/auth.ts";
import type { Db } from "../src/db.ts";
import { withTenant } from "../src/db.ts";
import { MIGRATIONS, migrate } from "../src/migrate.ts";
import { DEFAULT_LOGIN_CONCURRENCY, loginConcurrencyFromEnv, Slots } from "../src/server.ts";
import {
  call,
  dropDatabase,
  freshDatabase,
  loginAs,
  loginBurst,
  seedTenant,
  serve,
  type Tenant,
} from "./helpers.ts";

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

  it("đăng nhập đồng thời vượt giới hạn → 503 busy kèm retry-after; chỗ được trả lại sau 200 và 401", async () => {
    const small = await serve(db, { loginConcurrency: 1 });
    try {
      const burst = await loginBurst(small.base, a, 4);
      const statuses = burst.map((r) => r.status).sort();
      expect(statuses[0]).toBe(200);
      expect(statuses.at(-1)).toBe(503);
      for (const r of burst.filter((x) => x.status === 503)) {
        expect(r.json).toEqual({ error: "busy" });
        expect(r.headers.get("retry-after")).toBe("1");
      }
      const wrong = await call(small.base, "POST", "/v1/login", { email: a.email, password: "sai" });
      expect(wrong.status).toBe(401);
      expect(typeof (await loginAs(small.base, a))).toBe("string"); // 401 không giữ chỗ
      expect((await loginBurst(small.base, a, 1))[0]?.status).toBe(200); // 200 không giữ chỗ
    } finally {
      await small.close();
    }
  });

  it("đầu vào sai bị từ chối trước khi giữ chỗ scrypt", async () => {
    const small = await serve(db, { loginConcurrency: 1 });
    try {
      const bad = await Promise.all(
        Array.from({ length: 4 }, () => call(small.base, "POST", "/v1/login", { email: "", password: "x" })),
      );
      expect(bad.map((r) => r.status)).toEqual([422, 422, 422, 422]);
    } finally {
      await small.close();
    }
  });

  it("Slots và LOGIN_CONCURRENCY: đầy thì từ chối, trả chỗ thì nhận lại, cấu hình sai thì ném", () => {
    const s = new Slots(2);
    expect([s.tryAcquire(), s.tryAcquire(), s.tryAcquire()]).toEqual([true, true, false]);
    s.release();
    expect(s.tryAcquire()).toBe(true);
    s.release();
    s.release();
    expect(s.used).toBe(0);
    expect(() => s.release()).toThrow();
    for (const bad of [0, -1, 1.5, Number.NaN]) {
      expect(() => new Slots(bad)).toThrow();
    }
    expect(loginConcurrencyFromEnv({})).toBe(DEFAULT_LOGIN_CONCURRENCY);
    expect(loginConcurrencyFromEnv({ LOGIN_CONCURRENCY: "" })).toBe(DEFAULT_LOGIN_CONCURRENCY);
    expect(loginConcurrencyFromEnv({ LOGIN_CONCURRENCY: "8" })).toBe(8);
    for (const bad of ["0", "-1", "1.5", "abc", " 2"]) {
      expect(() => loginConcurrencyFromEnv({ LOGIN_CONCURRENCY: bad })).toThrow(/LOGIN_CONCURRENCY/);
    }
  });

  it("mọi phản hồi mang x-content-type-options: nosniff (200, 401, 404)", async () => {
    for (const [path, status] of [
      ["/healthz", 200],
      ["/v1/notes", 401],
      ["/khong-co", 404],
    ] as const) {
      const res = await fetch(base + path);
      expect(res.status).toBe(status);
      expect(res.headers.get("x-content-type-options")).toBe("nosniff");
      await res.arrayBuffer();
    }
  });

  it("phiên hết hạn được dọn: của chính user khi đăng nhập, của mọi user bằng purgeExpiredSessions", async () => {
    const past = new Date(Date.now() - 3600_000);
    const expired = (t: Tenant, h: string) => ({
      token_hash: h,
      user_id: t.userId,
      tenant_id: t.id,
      expires_at: past,
    });
    await db
      .insertInto("sessions")
      .values([expired(a, "het-han-a"), expired(b, "het-han-b")])
      .execute();
    const hashes = async () =>
      (await db.selectFrom("sessions").select("token_hash").where("expires_at", "<=", past).execute()).map(
        (r) => r.token_hash,
      );
    const ta = await loginAs(base, a);
    expect(await hashes()).toEqual(["het-han-b"]); // đăng nhập của A chỉ dọn phiên của A
    expect(await purgeExpiredSessions(db)).toBeGreaterThanOrEqual(1);
    expect(await hashes()).toEqual([]);
    expect((await call(base, "GET", "/v1/notes", undefined, ta)).status).toBe(200); // phiên còn hạn không bị xoá
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
      expect(await migrate(raw, "up")).toEqual([]); // lần hai: no-op, không lỗi (DB-MIG-004)
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

describe("đầu vào thô", () => {
  it("request-target URL không parse được → 400, server vẫn sống", async () => {
    const { hostname, port } = new URL(base);
    const reply = await new Promise<string>((ok, bad) => {
      const sock = connect(Number(port), hostname, () =>
        sock.end("GET http://[::1 HTTP/1.1\r\nHost: x\r\n\r\n"),
      );
      let data = "";
      sock.on("data", (c) => {
        data += String(c);
      });
      sock.on("end", () => ok(data));
      sock.on("error", bad);
    });
    expect(reply.split("\r\n")[0]).toBe("HTTP/1.1 400 Bad Request");
    expect(reply).toContain('"invalid_url"');
    expect(reply.toLowerCase()).toContain("x-content-type-options: nosniff");
    expect((await call(base, "GET", "/healthz")).status).toBe(200);
  });
});
