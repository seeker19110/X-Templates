// Tuyến worker: trùng lặp, hết giờ, crash giữa chừng, reconcile, cô lập tenant của hàng đợi.
import { afterAll, beforeAll, describe, expect, it } from "vitest";
import { type Db, withTenant } from "../src/db.ts";
import { claim, complete, enqueue, fail, MAX_ATTEMPTS, reconcile } from "../src/worker.ts";
import { dropDatabase, freshDatabase, seedTenant, type Tenant } from "./helpers.ts";

let db: Db;
let name: string;
let a: Tenant;
let b: Tenant;

beforeAll(async () => {
  ({ db, name } = await freshDatabase());
  a = await seedTenant(db, "a");
  b = await seedTenant(db, "b");
});

afterAll(async () => {
  await dropDatabase(db, name);
});

const sleep = (ms: number) => new Promise((ok) => setTimeout(ok, ms));

describe("worker", () => {
  it("enqueue trùng khoá ý định (đồng thời) → một job; cùng khoá ở tenant khác là job khác", async () => {
    const [x, y] = await Promise.all([
      enqueue(db, a.id, "email", "k1", { to: 1 }),
      enqueue(db, a.id, "email", "k1", { to: 1 }),
    ]);
    expect(x).toBe(y);
    expect(await enqueue(db, b.id, "email", "k1", { to: 2 })).not.toBe(x);
  });

  it("hai worker tranh nhau: chỉ một nhận job; worker hết lease không hoàn tất được", async () => {
    await enqueue(db, a.id, "sync", "k2", {});
    const [c1, c2] = await Promise.all([
      claim(db, a.id, "sync", "w1", 200),
      claim(db, a.id, "sync", "w2", 200),
    ]);
    const got = [c1, c2].filter((c) => c !== null);
    expect(got).toHaveLength(1);
    const job = got[0];
    if (!job) throw new Error("không có job");
    const owner = c1 ? "w1" : "w2";
    await sleep(300); // lease hết hạn — coi như worker treo
    const again = await claim(db, a.id, "sync", "w3", 5000);
    expect(again?.id).toBe(job.id);
    expect(again?.attempts).toBe(2);
    expect(await complete(db, a.id, owner, job.id, "gửi")).toBe(false); // worker cũ mất quyền
    expect(await complete(db, a.id, "w3", job.id, "gửi")).toBe(true);
    expect(await complete(db, a.id, "w3", job.id, "gửi")).toBe(false); // hoàn tất lần hai không ghi effect mới
  });

  it("crash giữa chừng (effect chưa ghi) → chạy lại → effect đúng một lần, reconcile rỗng", async () => {
    const id = await enqueue(db, a.id, "charge", "k3", {});
    const first = await claim(db, a.id, "charge", "w1", 100);
    expect(first?.id).toBe(id);
    await sleep(150); // w1 chết trước complete
    const retry = await claim(db, a.id, "charge", "w2", 5000);
    expect(retry?.id).toBe(id);
    expect(await complete(db, a.id, "w2", id, "đã thu")).toBe(true);
    const effects = await withTenant(db, a.id, (tx) =>
      tx.selectFrom("job_effects").selectAll().where("job_id", "=", id).execute(),
    );
    expect(effects).toHaveLength(1);
    expect(await reconcile(db, a.id)).toEqual([]);
  });

  it("lỗi lặp lại → failed sau MAX_ATTEMPTS, không claim nữa", async () => {
    await enqueue(db, b.id, "flaky", "k4", {});
    for (let i = 0; i < MAX_ATTEMPTS; i++) {
      const job = await claim(db, b.id, "flaky", "w", 5000);
      expect(job?.attempts).toBe(i + 1);
      await fail(db, b.id, "w", String(job?.id), `lỗi ${i}`);
    }
    expect(await claim(db, b.id, "flaky", "w", 5000)).toBeNull();
    const rows = await withTenant(db, b.id, (tx) =>
      tx.selectFrom("jobs").select(["status", "attempts"]).where("kind", "=", "flaky").execute(),
    );
    expect(rows).toEqual([{ status: "failed", attempts: MAX_ATTEMPTS }]);
  });

  it("worker chết ở lần thử cuối → job thành failed, không kẹt running", async () => {
    await enqueue(db, b.id, "dies", "k7", {});
    for (let i = 0; i < MAX_ATTEMPTS; i++) {
      expect((await claim(db, b.id, "dies", "w", 50))?.attempts).toBe(i + 1);
      await sleep(80); // không complete/fail: worker chết, lease hết hạn
    }
    expect(await claim(db, b.id, "dies", "w", 50)).toBeNull();
    const rows = await withTenant(db, b.id, (tx) =>
      tx.selectFrom("jobs").select(["status", "locked_by"]).where("kind", "=", "dies").execute(),
    );
    expect(rows).toEqual([{ status: "failed", locked_by: null }]);
  });

  it("worker của tenant B không thấy job của A", async () => {
    await enqueue(db, a.id, "only-a", "k5", {});
    expect(await claim(db, b.id, "only-a", "wb", 5000)).toBeNull();
    expect((await claim(db, a.id, "only-a", "wa", 5000))?.kind).toBe("only-a");
  });

  it("reconcile phát hiện job done thiếu effect", async () => {
    const id = await enqueue(db, b.id, "manual", "k6", {});
    await withTenant(db, b.id, (tx) =>
      tx.updateTable("jobs").set({ status: "done" }).where("id", "=", id).execute(),
    );
    expect(await reconcile(db, b.id)).toEqual([{ job_id: id, problem: "done_without_effect" }]);
  });
});
