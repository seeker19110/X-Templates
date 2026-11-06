// Contract: (1) contract/openapi.json không đổi KHÔNG tương thích so với contract/baseline.json (bản đã phát hành):
// không bỏ đường/phương thức/mã phản hồi thành công, không bỏ trường bắt buộc của phản hồi, không đổi kiểu, không thêm
// trường bắt buộc vào request. Thêm mới thì được; phát hành bản mới → chép openapi.json đè baseline.json trong cùng PR.
// (2) Phản hồi thật của server có đủ trường bắt buộc đúng kiểu như openapi.json khai.
import { readFileSync } from "node:fs";
import { afterAll, beforeAll, describe, expect, it } from "vitest";
import type { Db } from "../src/db.ts";
import { call, dropDatabase, freshDatabase, loginAs, loginBurst, seedTenant, serve } from "./helpers.ts";

type Schema = {
  $ref?: string;
  type?: string;
  required?: string[];
  properties?: Record<string, Schema>;
  items?: Schema;
};
type Op = {
  requestBody?: { content: Record<string, { schema: Schema }> };
  responses: Record<string, { content?: Record<string, { schema: Schema }> }>;
};
type Doc = { paths: Record<string, Record<string, Op>>; components: { schemas: Record<string, Schema> } };

const load = (f: string): Doc =>
  JSON.parse(readFileSync(new URL(`../contract/${f}`, import.meta.url), "utf8")) as Doc;
const current = load("openapi.json");
const baseline = load("baseline.json");

function resolve(doc: Doc, s: Schema): Schema {
  return s.$ref ? resolve(doc, doc.components.schemas[s.$ref.split("/").pop() ?? ""] ?? {}) : s;
}

function bodySchema(
  doc: Doc,
  part: { content?: Record<string, { schema: Schema }> } | undefined,
): Schema | null {
  const s = part?.content?.["application/json"]?.schema;
  return s ? resolve(doc, s) : null;
}

// Trả danh sách vi phạm khi `next` không còn đáp ứng được người dùng của `prev` (phản hồi) — đệ quy theo thuộc tính.
function responseBreaks(prev: Schema | null, next: Schema | null, at: string): string[] {
  if (!prev) return [];
  if (!next) return [`${at}: mất schema`];
  const p = resolve(baseline, prev);
  const n = resolve(current, next);
  if (p.type !== n.type) return [`${at}: đổi kiểu ${p.type} → ${n.type}`];
  const out: string[] = [];
  for (const key of p.required ?? []) {
    if (!(n.required ?? []).includes(key)) out.push(`${at}.${key}: không còn bắt buộc/bị bỏ`);
    out.push(...responseBreaks(p.properties?.[key] ?? null, n.properties?.[key] ?? null, `${at}.${key}`));
  }
  if (p.items) out.push(...responseBreaks(p.items, n.items ?? null, `${at}[]`));
  return out;
}

// Request: client cũ gửi theo `prev` phải còn hợp lệ với `next` — không thêm trường bắt buộc, không đổi kiểu trường đã
// có (kể cả trường tuỳ chọn, đệ quy theo thuộc tính và phần tử mảng).
function requestBreaks(prev: Schema | null, next: Schema | null, at: string): string[] {
  if (!next) return [];
  const n = resolve(current, next);
  const p = prev ? resolve(baseline, prev) : null;
  if (p && p.type !== n.type) return [`${at}: request đổi kiểu ${p.type} → ${n.type}`];
  const added = (n.required ?? []).filter((k) => !(p?.required ?? []).includes(k));
  const out = added.map((k) => `${at}.${k}: request thêm trường bắt buộc`);
  for (const [key, sub] of Object.entries(p?.properties ?? {})) {
    const nextSub = n.properties?.[key];
    if (nextSub) out.push(...requestBreaks(sub, nextSub, `${at}.${key}`));
  }
  if (p?.items && n.items) out.push(...requestBreaks(p.items, n.items, `${at}[]`));
  return out;
}

function breakingChanges(): string[] {
  const out: string[] = [];
  for (const [path, ops] of Object.entries(baseline.paths)) {
    for (const [method, op] of Object.entries(ops)) {
      const next = current.paths[path]?.[method];
      if (!next) {
        out.push(`${method.toUpperCase()} ${path}: bị bỏ`);
        continue;
      }
      const at = `${method.toUpperCase()} ${path}`;
      out.push(
        ...requestBreaks(bodySchema(baseline, op.requestBody), bodySchema(current, next.requestBody), at),
      );
      for (const [code, resp] of Object.entries(op.responses)) {
        if (!next.responses[code]) {
          out.push(`${at} ${code}: mã phản hồi bị bỏ`);
          continue;
        }
        out.push(
          ...responseBreaks(
            bodySchema(baseline, resp),
            bodySchema(current, next.responses[code]),
            `${at} ${code}`,
          ),
        );
      }
    }
  }
  return out;
}

function conforms(schema: Schema, value: unknown, at: string): string[] {
  const s = resolve(current, schema);
  const kind = Array.isArray(value) ? "array" : value === null ? "null" : typeof value;
  if (s.type && s.type !== kind) return [`${at}: cần ${s.type}, nhận ${kind}`];
  const out: string[] = [];
  const obj = (value ?? {}) as Record<string, unknown>;
  for (const key of s.required ?? []) {
    if (!(key in obj)) out.push(`${at}.${key}: thiếu`);
    else if (s.properties?.[key]) out.push(...conforms(s.properties[key], obj[key], `${at}.${key}`));
  }
  if (s.items && Array.isArray(value)) {
    for (const [i, v] of value.entries()) out.push(...conforms(s.items, v, `${at}[${i}]`));
  }
  return out;
}

function schemaFor(path: string, method: string, status: number): Schema {
  const s = current.paths[path]?.[method]?.responses[String(status)]?.content?.["application/json"]?.schema;
  if (!s) throw new Error(`${method} ${path} ${status}: không có trong contract`);
  return s;
}

describe("contract tĩnh", () => {
  it("không thay đổi không tương thích so với baseline", () => {
    expect(breakingChanges()).toEqual([]);
  });
});

describe("contract khi chạy", () => {
  let db: Db;
  let name: string;
  let base: string;
  let close: () => Promise<void>;

  beforeAll(async () => {
    ({ db, name } = await freshDatabase());
    ({ base, close } = await serve(db));
  });

  afterAll(async () => {
    await close();
    await dropDatabase(db, name);
  });

  it("mọi phản hồi khớp schema đã khai", async () => {
    const t = await seedTenant(db, "c");
    const checks: [string, string, string, unknown?][] = [
      ["/healthz", "get", "/healthz"],
      ["/v1/login", "post", "/v1/login", { email: t.email, password: t.password }],
      ["/v1/login", "post", "/v1/login", { email: t.email, password: "sai" }],
      ["/v1/notes", "get", "/v1/notes"], // không token → 401
    ];
    const problems: string[] = [];
    for (const [spec, method, path, body] of checks) {
      const r = await call(base, method.toUpperCase(), path, body);
      problems.push(...conforms(schemaFor(spec, method, r.status), r.json, `${method} ${path} ${r.status}`));
    }
    const token = await loginAs(base, t);
    const created = await call(base, "POST", "/v1/notes", { body: "c" }, token);
    problems.push(...conforms(schemaFor("/v1/notes", "post", created.status), created.json, "post notes"));
    const bad = await call(base, "POST", "/v1/notes", { body: "" }, token);
    problems.push(...conforms(schemaFor("/v1/notes", "post", bad.status), bad.json, "post notes 422"));
    const list = await call(base, "GET", "/v1/notes", undefined, token);
    problems.push(...conforms(schemaFor("/v1/notes", "get", list.status), list.json, "get notes"));
    const one = await call(base, "GET", `/v1/notes/${String(created.json.id)}`, undefined, token);
    problems.push(...conforms(schemaFor("/v1/notes/{id}", "get", one.status), one.json, "get note"));
    const missing = await call(
      base,
      "GET",
      "/v1/notes/00000000-0000-4000-8000-000000000000",
      undefined,
      token,
    );
    problems.push(
      ...conforms(schemaFor("/v1/notes/{id}", "get", missing.status), missing.json, "get note 404"),
    );
    expect(problems).toEqual([]);
    expect([created.status, bad.status, list.status, one.status, missing.status]).toEqual([
      201, 422, 200, 200, 404,
    ]);
  });

  it("đăng nhập quá tải (503 busy) khớp schema đã khai", async () => {
    const t = await seedTenant(db, "d");
    const small = await serve(db, { loginConcurrency: 1 });
    try {
      const busy = (await loginBurst(small.base, t, 4)).filter((r) => r.status === 503);
      expect(busy.length).toBeGreaterThan(0);
      for (const r of busy) {
        expect(conforms(schemaFor("/v1/login", "post", 503), r.json, "post login 503")).toEqual([]);
      }
    } finally {
      await small.close();
    }
  });
});
