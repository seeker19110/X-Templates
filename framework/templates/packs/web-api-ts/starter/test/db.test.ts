// Giới hạn thời gian của kết nối ứng dụng (AUD-DATA-008): DB không trả lời, pool cạn, truy vấn chạy lâu → lỗi nhanh,
// không treo request. Không cần cơ sở riêng: chỉ chạy truy vấn không đụng bảng trên cơ sở quản trị.
import { type AddressInfo, createServer, type Server, type Socket } from "node:net";
import { sql } from "kysely";
import { afterAll, beforeAll, describe, expect, it } from "vitest";
import { createDb, DEFAULT_TIMEOUTS, timeoutsFromEnv } from "../src/db.ts";
import { adminUrl } from "./helpers.ts";

describe("timeoutsFromEnv", () => {
  it("mặc định, ghi đè, và giá trị sai bị từ chối (kể cả 0 = tắt giới hạn của pg)", () => {
    expect(timeoutsFromEnv({})).toEqual(DEFAULT_TIMEOUTS);
    expect(timeoutsFromEnv({ PG_CONNECT_TIMEOUT_MS: "", PG_STATEMENT_TIMEOUT_MS: "" })).toEqual(
      DEFAULT_TIMEOUTS,
    );
    expect(timeoutsFromEnv({ PG_CONNECT_TIMEOUT_MS: "1500", PG_STATEMENT_TIMEOUT_MS: "250" })).toEqual({
      connectMs: 1500,
      statementMs: 250,
    });
    for (const bad of ["0", "-5", "1.5", "abc", "1e3", " 10"]) {
      expect(() => timeoutsFromEnv({ PG_CONNECT_TIMEOUT_MS: bad })).toThrow(/PG_CONNECT_TIMEOUT_MS/);
      expect(() => timeoutsFromEnv({ PG_STATEMENT_TIMEOUT_MS: bad })).toThrow(/PG_STATEMENT_TIMEOUT_MS/);
    }
  });
});

describe("kết nối ứng dụng có giới hạn thời gian", () => {
  // Máy chủ TCP nhận kết nối nhưng không bao giờ trả lời — giống DB treo.
  let silent: Server;
  let silentPort: number;
  const sockets: Socket[] = [];

  beforeAll(async () => {
    silent = createServer((s) => {
      sockets.push(s);
    });
    await new Promise<void>((ok) => silent.listen(0, "127.0.0.1", ok));
    silentPort = (silent.address() as AddressInfo).port;
  });

  afterAll(async () => {
    for (const s of sockets) s.destroy();
    await new Promise<void>((ok) => silent.close(() => ok()));
  });

  it("mặc định đặt statement_timeout cho phiên", async () => {
    const db = createDb(adminUrl(), 1);
    try {
      const r = await sql<{ statement_timeout: string }>`SHOW statement_timeout`.execute(db);
      expect(r.rows[0]?.statement_timeout).toBe(`${DEFAULT_TIMEOUTS.statementMs / 1000}s`);
    } finally {
      await db.destroy();
    }
  });

  it("truy vấn quá statement_timeout → lỗi, không chờ hết", async () => {
    const db = createDb(adminUrl(), 1, { connectMs: 5_000, statementMs: 200 });
    try {
      const t0 = Date.now();
      await expect(sql`SELECT pg_sleep(5)`.execute(db)).rejects.toThrow(/statement timeout/);
      expect(Date.now() - t0).toBeLessThan(3_000);
    } finally {
      await db.destroy();
    }
  });

  it("DB không trả lời khi mở kết nối → lỗi sau connectMs", async () => {
    const db = createDb(`postgres://x@127.0.0.1:${silentPort}/x`, 1, { connectMs: 200, statementMs: 1_000 });
    try {
      const t0 = Date.now();
      await expect(sql`SELECT 1`.execute(db)).rejects.toThrow(/timeout/i);
      expect(Date.now() - t0).toBeLessThan(3_000);
    } finally {
      await db.destroy();
    }
  });

  it("pool cạn kết nối → chờ tối đa connectMs rồi lỗi", async () => {
    const db = createDb(adminUrl(), 1, { connectMs: 200, statementMs: 5_000 });
    try {
      let release = () => {};
      const held = new Promise<void>((ok) => {
        release = ok;
      });
      let started = () => {};
      const isHeld = new Promise<void>((ok) => {
        started = ok;
      });
      const holder = db.transaction().execute(async (tx) => {
        await sql`SELECT 1`.execute(tx);
        started();
        await held; // giữ kết nối duy nhất của pool
      });
      await isHeld;
      await expect(sql`SELECT 1`.execute(db)).rejects.toThrow(/timeout/i);
      release();
      await holder;
      expect((await sql<{ n: number }>`SELECT 1 AS n`.execute(db)).rows[0]?.n).toBe(1); // trả kết nối thì dùng lại được
    } finally {
      await db.destroy();
    }
  });
});
