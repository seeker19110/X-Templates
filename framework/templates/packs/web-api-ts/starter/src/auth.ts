// Mật khẩu: scrypt (node:crypto) với muối ngẫu nhiên; phiên: token ngẫu nhiên 32 byte, DB chỉ lưu sha256 của token.
import { createHash, randomBytes, randomUUID, scrypt as scryptCb, timingSafeEqual } from "node:crypto";
import { promisify } from "node:util";
import type { Db } from "./db.ts";

const scrypt = promisify(scryptCb) as (pw: string, salt: Buffer, len: number) => Promise<Buffer>;
const KEY_LEN = 32;
export const SESSION_HOURS = 12;

export async function hashPassword(password: string): Promise<string> {
  const salt = randomBytes(16);
  const key = await scrypt(password, salt, KEY_LEN);
  return `scrypt$${salt.toString("base64url")}$${key.toString("base64url")}`;
}

export async function verifyPassword(password: string, stored: string): Promise<boolean> {
  const [scheme, salt, key] = stored.split("$");
  if (scheme !== "scrypt" || !salt || !key) {
    return false;
  }
  const want = Buffer.from(key, "base64url");
  const got = await scrypt(password, Buffer.from(salt, "base64url"), want.length);
  return got.length === want.length && timingSafeEqual(got, want);
}

function tokenHash(token: string): string {
  return createHash("sha256").update(token).digest("hex");
}

export interface Principal {
  userId: string;
  tenantId: string;
}

// Mật khẩu giả để so khi email không tồn tại — thời gian trả lời không lộ email nào có thật.
const DUMMY = `scrypt$${randomBytes(16).toString("base64url")}$${randomBytes(KEY_LEN).toString("base64url")}`;

export async function login(db: Db, email: string, password: string): Promise<string | null> {
  const user = await db
    .selectFrom("users")
    .select(["id", "tenant_id", "password_hash"])
    .where("email", "=", email.trim().toLowerCase())
    .executeTakeFirst();
  const ok = await verifyPassword(password, user?.password_hash ?? DUMMY);
  if (!user || !ok) {
    return null;
  }
  const token = randomBytes(32).toString("base64url");
  await db
    .insertInto("sessions")
    .values({
      token_hash: tokenHash(token),
      user_id: user.id,
      tenant_id: user.tenant_id,
      expires_at: new Date(Date.now() + SESSION_HOURS * 3600_000),
    })
    .execute();
  return token;
}

export async function authenticate(db: Db, token: string): Promise<Principal | null> {
  const row = await db
    .selectFrom("sessions")
    .select(["user_id", "tenant_id"])
    .where("token_hash", "=", tokenHash(token))
    .where("expires_at", ">", new Date())
    .executeTakeFirst();
  return row ? { userId: row.user_id, tenantId: row.tenant_id } : null;
}

export async function createUser(db: Db, tenantId: string, email: string, password: string): Promise<string> {
  const id = randomUUID();
  await db
    .insertInto("users")
    .values({
      id,
      tenant_id: tenantId,
      email: email.trim().toLowerCase(),
      password_hash: await hashPassword(password),
    })
    .execute();
  return id;
}
