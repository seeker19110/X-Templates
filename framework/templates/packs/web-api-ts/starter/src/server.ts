// API HTTP tối giản (node:http, không framework). Hợp đồng: contract/openapi.json — test/contract.test.ts kiểm cả hai
// chiều (không đổi không tương thích so với contract/baseline.json; phản hồi thật có đủ trường bắt buộc).
import { createServer, type IncomingMessage, type Server, type ServerResponse } from "node:http";
import { authenticate, login, type Principal } from "./auth.ts";
import { createDb, type Db, withTenant } from "./db.ts";

const MAX_BODY = 64 * 1024;
const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;

// Số `POST /v1/login` chạy scrypt cùng lúc (mỗi lần ~128 MiB + ~0,3 s trên threadpool libuv dùng chung với DNS/fs):
// đầy → 503 `busy` + `retry-after`, không xếp hàng vô hạn (AUD-SEC-532). Ghi đè: env LOGIN_CONCURRENCY.
export const DEFAULT_LOGIN_CONCURRENCY = 2;
const RETRY_AFTER_S = "1";

class HttpError extends Error {
  readonly status: number;
  readonly code: string;
  readonly headers: Record<string, string>;
  constructor(status: number, code: string, headers: Record<string, string> = {}) {
    super(code);
    this.status = status;
    this.code = code;
    this.headers = headers;
  }
}

// Semaphore không chờ: `tryAcquire` trả false khi đầy (người gọi trả 503 ngay), `release` gọi đúng một lần mỗi lần lấy.
export class Slots {
  readonly limit: number;
  #used = 0;
  constructor(limit: number) {
    if (!Number.isSafeInteger(limit) || limit < 1) {
      throw new Error("số chỗ phải là số nguyên ≥ 1");
    }
    this.limit = limit;
  }
  get used(): number {
    return this.#used;
  }
  tryAcquire(): boolean {
    if (this.#used >= this.limit) return false;
    this.#used += 1;
    return true;
  }
  release(): void {
    if (this.#used < 1) throw new Error("release nhiều hơn acquire");
    this.#used -= 1;
  }
}

function send(
  res: ServerResponse,
  status: number,
  body: unknown,
  headers: Record<string, string> = {},
): void {
  const data = JSON.stringify(body);
  res.writeHead(status, {
    ...headers,
    "content-type": "application/json; charset=utf-8",
    "cache-control": "no-store",
    "x-content-type-options": "nosniff",
  });
  res.end(data);
}

async function readJson(req: IncomingMessage): Promise<Record<string, unknown>> {
  let size = 0;
  const chunks: Buffer[] = [];
  for await (const chunk of req) {
    size += (chunk as Buffer).length;
    if (size > MAX_BODY) {
      throw new HttpError(413, "body_too_large");
    }
    chunks.push(chunk as Buffer);
  }
  try {
    const value: unknown = JSON.parse(Buffer.concat(chunks).toString("utf8"));
    if (value && typeof value === "object" && !Array.isArray(value)) {
      return value as Record<string, unknown>;
    }
  } catch {
    // rơi xuống lỗi chung
  }
  throw new HttpError(400, "invalid_json");
}

async function principal(db: Db, req: IncomingMessage): Promise<Principal> {
  const auth = req.headers.authorization ?? "";
  const token = auth.startsWith("Bearer ") ? auth.slice(7) : "";
  const who = token ? await authenticate(db, token) : null;
  if (!who) {
    throw new HttpError(401, "unauthorized");
  }
  return who;
}

function text(body: Record<string, unknown>, key: string, max: number): string {
  const v = body[key];
  if (typeof v !== "string" || v.length < 1 || v.length > max) {
    throw new HttpError(422, `invalid_${key}`);
  }
  return v;
}

interface Ctx {
  db: Db;
  loginSlots: Slots;
}

type Handler = (ctx: Ctx, req: IncomingMessage, id: string) => Promise<[number, unknown]>;

const postLogin: Handler = async ({ db, loginSlots }, req) => {
  // Đọc + kiểm body trước khi giữ chỗ: client gửi chậm không chiếm chỗ của scrypt.
  const body = await readJson(req);
  const email = text(body, "email", 320);
  const password = text(body, "password", 1000);
  if (!loginSlots.tryAcquire()) {
    throw new HttpError(503, "busy", { "retry-after": RETRY_AFTER_S });
  }
  let token: string | null;
  try {
    token = await login(db, email, password);
  } finally {
    loginSlots.release();
  }
  if (!token) {
    throw new HttpError(401, "invalid_credentials");
  }
  return [200, { token }];
};

const listNotes: Handler = async ({ db }, req) => {
  const who = await principal(db, req);
  const notes = await withTenant(db, who.tenantId, (tx) =>
    tx
      .selectFrom("notes")
      .select(["id", "body", "created_at"])
      .orderBy("created_at", "desc")
      .limit(100)
      .execute(),
  );
  return [200, { notes }];
};

const createNote: Handler = async ({ db }, req) => {
  const who = await principal(db, req);
  const body = text(await readJson(req), "body", 10000);
  const note = await withTenant(db, who.tenantId, (tx) =>
    tx
      .insertInto("notes")
      .values({ body, created_by: who.userId })
      .returning(["id", "body", "created_at"])
      .executeTakeFirstOrThrow(),
  );
  return [201, note];
};

const getNote: Handler = async ({ db }, req, id) => {
  const who = await principal(db, req);
  const note = UUID_RE.test(id)
    ? await withTenant(db, who.tenantId, (tx) =>
        tx.selectFrom("notes").select(["id", "body", "created_at"]).where("id", "=", id).executeTakeFirst(),
      )
    : undefined;
  if (!note) {
    throw new HttpError(404, "not_found"); // tenant khác cũng là 404: không lộ id có tồn tại
  }
  return [200, note];
};

function route(method: string, path: string): [Handler, string] | null {
  if (method === "POST" && path === "/v1/login") return [postLogin, ""];
  if (method === "GET" && path === "/v1/notes") return [listNotes, ""];
  if (method === "POST" && path === "/v1/notes") return [createNote, ""];
  const m = /^\/v1\/notes\/([^/]+)$/.exec(path);
  if (method === "GET" && m?.[1]) return [getNote, m[1]];
  return null;
}

function parsePath(url: string | undefined): string {
  try {
    return new URL(url ?? "/", "http://localhost").pathname;
  } catch {
    throw new HttpError(400, "invalid_url");
  }
}

export function loginConcurrencyFromEnv(env: NodeJS.ProcessEnv = process.env): number {
  const raw = env.LOGIN_CONCURRENCY;
  if (raw === undefined || raw === "") return DEFAULT_LOGIN_CONCURRENCY;
  if (!/^\d+$/.test(raw) || Number(raw) < 1) {
    throw new Error("LOGIN_CONCURRENCY phải là số nguyên ≥ 1");
  }
  return Number(raw);
}

export interface AppOptions {
  loginConcurrency?: number;
}

export function createApp(db: Db, opts: AppOptions = {}): Server {
  const ctx: Ctx = { db, loginSlots: new Slots(opts.loginConcurrency ?? loginConcurrencyFromEnv()) };
  return createServer(async (req, res) => {
    // Mọi bước, kể cả parse URL, nằm trong try: llhttp nhận request-target mà WHATWG URL không parse được
    // (`GET http://[::1 HTTP/1.1`) — lỗi lọt ra ngoài handler async là unhandled rejection, Node thoát.
    try {
      const path = parsePath(req.url);
      if (req.method === "GET" && path === "/healthz") {
        send(res, 200, { status: "ok" });
        return;
      }
      const found = route(req.method ?? "", path);
      if (!found) {
        throw new HttpError(404, "not_found");
      }
      const [status, body] = await found[0](ctx, req, found[1]);
      send(res, status, body);
    } catch (err) {
      if (err instanceof HttpError) {
        send(res, err.status, { error: err.code }, err.headers);
      } else {
        console.error(err);
        send(res, 500, { error: "internal" });
      }
    }
  });
}

if (import.meta.main) {
  const url = process.env.DATABASE_URL;
  if (!url) {
    console.error("thiếu DATABASE_URL");
    process.exit(2);
  }
  const port = Number(process.env.PORT ?? 3000);
  createApp(createDb(url)).listen(port, () => console.log(`nghe :${port}`));
}
