// Sao lưu → khôi phục vào cơ sở mới → dữ liệu, đăng nhập và RLS còn đúng (research §5: rollback/restore).
// Công cụ: `pg_dump`/`pg_restore` trên PATH, hoặc PG_TOOLS_CONTAINER=<container Postgres> để chạy qua `docker exec`
// (bản công cụ phải ≥ bản server — chạy trong chính container server là chắc nhất).
import { execFileSync } from "node:child_process";
import { randomBytes } from "node:crypto";
import { afterAll, beforeAll, expect, it } from "vitest";
import { createDb, type Db, withTenant } from "../src/db.ts";
import {
  admin,
  adminUrl,
  call,
  dbUrl,
  dropDatabase,
  freshDatabase,
  loginAs,
  seedTenant,
  serve,
} from "./helpers.ts";

function pgTool(tool: "pg_dump" | "pg_restore", db: string, args: string[], input?: Buffer): Buffer {
  const container = process.env.PG_TOOLS_CONTAINER;
  const user = decodeURIComponent(new URL(adminUrl()).username || "postgres");
  const [cmd, argv] = container
    ? ["docker", ["exec", "-i", container, tool, "-U", user, "-d", db, ...args]]
    : [tool, [`--dbname=${dbUrl(db)}`, ...args]];
  return execFileSync(cmd, argv, { input, maxBuffer: 256 * 1024 * 1024 });
}

let src: { name: string; db: Db };
let restoredName: string;
let restored: Db;

beforeAll(async () => {
  src = await freshDatabase();
  restoredName = `r_${randomBytes(6).toString("hex")}`;
});

afterAll(async () => {
  await dropDatabase(src.db, src.name);
  if (restored) {
    await dropDatabase(restored, restoredName);
  }
});

it("dữ liệu và quyền còn đúng sau khi khôi phục", async () => {
  const a = await seedTenant(src.db, "a");
  const b = await seedTenant(src.db, "b");
  await withTenant(src.db, a.id, (tx) =>
    tx.insertInto("notes").values({ body: "trước sao lưu", created_by: a.userId }).execute(),
  );

  const dump = pgTool("pg_dump", src.name, ["--format=custom", "--no-owner"]);
  expect(dump.length).toBeGreaterThan(0);
  await admin(`CREATE DATABASE ${restoredName}`);
  pgTool("pg_restore", restoredName, ["--no-owner", "--exit-on-error"], dump);

  restored = createDb(dbUrl(restoredName));
  const { base, close } = await serve(restored);
  try {
    const ta = await loginAs(base, a);
    const tb = await loginAs(base, b);
    const listA = await call(base, "GET", "/v1/notes", undefined, ta);
    expect((listA.json.notes as { body: string }[]).map((n) => n.body)).toEqual(["trước sao lưu"]);
    expect((await call(base, "GET", "/v1/notes", undefined, tb)).json.notes).toEqual([]);
    const seenByB = await withTenant(restored, b.id, (tx) => tx.selectFrom("notes").selectAll().execute());
    expect(seenByB).toEqual([]);
  } finally {
    await close();
  }
});
