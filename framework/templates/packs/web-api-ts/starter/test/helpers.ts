// Mỗi file test: một cơ sở dữ liệu mới trên Postgres thật (DATABASE_URL trỏ tới cơ sở quản trị, vai trò có CREATEDB).
// Không có DATABASE_URL → ném lỗi: test đỏ, không bỏ qua.
import { randomBytes, randomUUID } from "node:crypto";
import type { AddressInfo } from "node:net";
import type { Kysely } from "kysely";
import pg from "pg";
import { createUser } from "../src/auth.ts";
import { createDb, type Db } from "../src/db.ts";
import { migrate } from "../src/migrate.ts";
import { createApp } from "../src/server.ts";

export function adminUrl(): string {
  const url = process.env.DATABASE_URL;
  if (!url) {
    throw new Error("cần DATABASE_URL tới Postgres thật cho test tích hợp");
  }
  return url;
}

export function dbUrl(name: string): string {
  const u = new URL(adminUrl());
  u.pathname = `/${name}`;
  return u.toString();
}

export async function admin(statement: string): Promise<void> {
  const client = new pg.Client({ connectionString: adminUrl() });
  await client.connect();
  try {
    await client.query(statement);
  } finally {
    await client.end();
  }
}

export async function freshDatabase(): Promise<{ name: string; db: Db }> {
  const name = `t_${randomBytes(6).toString("hex")}`;
  await admin(`CREATE DATABASE ${name}`);
  const db = createDb(dbUrl(name));
  await migrate(db as unknown as Kysely<unknown>, "up");
  return { name, db };
}

export async function dropDatabase(db: Db, name: string): Promise<void> {
  await db.destroy();
  await admin(`DROP DATABASE IF EXISTS ${name} WITH (FORCE)`);
}

export interface Tenant {
  id: string;
  userId: string;
  email: string;
  password: string;
}

export async function seedTenant(db: Db, label: string): Promise<Tenant> {
  const id = randomUUID();
  await db.insertInto("tenants").values({ id, name: label }).execute();
  const email = `${label}-${id.slice(0, 8)}@example.test`;
  const password = randomBytes(12).toString("base64url");
  const userId = await createUser(db, id, email, password);
  return { id, userId, email, password };
}

export async function serve(db: Db): Promise<{ base: string; close: () => Promise<void> }> {
  const server = createApp(db);
  await new Promise<void>((ok) => server.listen(0, "127.0.0.1", ok));
  const { port } = server.address() as AddressInfo;
  return {
    base: `http://127.0.0.1:${port}`,
    close: () => new Promise<void>((ok) => server.close(() => ok())),
  };
}

export async function call(
  base: string,
  method: string,
  path: string,
  body?: unknown,
  token?: string,
): Promise<{ status: number; json: Record<string, unknown> }> {
  const headers: Record<string, string> = { "content-type": "application/json" };
  if (token) headers.authorization = `Bearer ${token}`;
  const init: RequestInit = { method, headers };
  if (body !== undefined) init.body = JSON.stringify(body);
  const res = await fetch(base + path, init);
  return { status: res.status, json: (await res.json()) as Record<string, unknown> };
}

export async function loginAs(base: string, t: Tenant): Promise<string> {
  const r = await call(base, "POST", "/v1/login", { email: t.email, password: t.password });
  if (r.status !== 200 || typeof r.json.token !== "string") {
    throw new Error(`đăng nhập hỏng: ${r.status}`);
  }
  return r.json.token;
}
