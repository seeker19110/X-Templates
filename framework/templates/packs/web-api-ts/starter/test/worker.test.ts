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
    await sleep(300); // lease hết hạn — coi như worker treo
    const again = await claim(db, a.id, "sync", "w3", 5000);
    expect(again?.id).toBe(job.id);
    expect(again?.attempts).toBe(2);
    if (!again) throw new Error("không có job");
    expect(again.lease).not.toBe(job.lease);
    expect(await complete(db, a.id, job, "gửi")).toBe(false); // worker cũ mất quyền
    expect(await complete(db, a.id, again, "gửi")).toBe(true);
    expect(await complete(db, a.id, again, "gửi")).toBe(false); // hoàn tất lần hai không ghi effect mới
  });

  it("fail cũ cùng workerId không reset job đang chạy", async () => {
    // AUD-DATA-006: cùng workerId (vd tên máy) claim lại job hết lease; handler của lần chạy cũ báo lỗi muộn.
    const id = await enqueue(db, a.id, "same-worker", "k8", {});
    const first = await claim(db, a.id, "same-worker", "w", 100);
    expect(first?.id).toBe(id);
    if (!first) throw new Error("không có job");
    await sleep(150); // lần chạy 1 treo quá lease
    const second = await claim(db, a.id, "same-worker", "w", 5000);
    expect(second?.id).toBe(id);
    if (!second) throw new Error("không có job");
    expect(await fail(db, a.id, first, "lỗi muộn của lần chạy 1")).toBe(false);
    expect(await complete(db, a.id, first, "lần 1")).toBe(false); // lần chạy 1 đã mất quyền
    const mid = await withTenant(db, a.id, (tx) =>
      tx
        .selectFrom("jobs")
        .select(["status", "attempts", "last_error"])
        .where("id", "=", id)
        .executeTakeFirst(),
    );
    expect(mid).toEqual({ status: "running", attempts: 2, last_error: null });
    expect(await claim(db, a.id, "same-worker", "w2", 5000)).toBeNull(); // không có lần chạy thứ ba song song
    expect(await complete(db, a.id, second, "lần 2")).toBe(true);
    expect(await fail(db, a.id, second, "fail sau done")).toBe(false); // không lùi job đã done
    const end = await withTenant(db, a.id, (tx) =>
      tx.selectFrom("jobs").select("status").where("id", "=", id).executeTakeFirst(),
    );
    expect(end?.status).toBe("done");
    expect(await reconcile(db, a.id)).toEqual([]);
  });

  it("token giả bị từ chối; lease hết hạn chưa ai claim lại thì chủ token vẫn trả job về hàng đợi", async () => {
    const id = await enqueue(db, a.id, "token", "k9", {});
    const run = await claim(db, a.id, "token", "w", 100);
    if (!run) throw new Error("không có job");
    const forged = { id, lease: "00000000-0000-4000-8000-000000000000" };
    expect(await complete(db, a.id, forged, "giả")).toBe(false);
    expect(await fail(db, a.id, forged, "giả")).toBe(false);
    await sleep(150); // hết lease nhưng chưa ai claim lại
    expect(await complete(db, a.id, run, "muộn")).toBe(false); // hết lease thì không hoàn tất
    expect(await fail(db, a.id, run, "hết giờ")).toBe(true); // nhưng được trả về hàng đợi
    const row = await withTenant(db, a.id, (tx) =>
      tx.selectFrom("jobs").select(["status", "lease_token"]).where("id", "=", id).executeTakeFirst(),
    );
    expect(row).toEqual({ status: "queued", lease_token: null });
  });

  it("đồng thời: fail của lần chạy cũ và complete của lần chạy mới — chỉ lần mới có hiệu lực", async () => {
    for (let i = 0; i < 5; i++) {
      const id = await enqueue(db, a.id, "race", `k10-${i}`, {});
      const old = await claim(db, a.id, "race", "w", 50);
      await sleep(80);
      const cur = await claim(db, a.id, "race", "w", 5000);
      if (!old || !cur) throw new Error("không có job");
      const [failed, done, doneAgain] = await Promise.all([
        fail(db, a.id, old, "muộn"),
        complete(db, a.id, cur, "xong"),
        complete(db, a.id, cur, "xong"),
      ]);
      expect(failed).toBe(false);
      expect([done, doneAgain].filter(Boolean)).toHaveLength(1); // complete trùng: đúng một lần ghi effect
      const row = await withTenant(db, a.id, (tx) =>
        tx.selectFrom("jobs").select(["status", "attempts"]).where("id", "=", id).executeTakeFirst(),
      );
      expect(row).toEqual({ status: "done", attempts: 2 });
    }
    expect(await reconcile(db, a.id)).toEqual([]);
  });

  it("crash giữa chừng (effect chưa ghi) → chạy lại → effect đúng một lần, reconcile rỗng", async () => {
    const id = await enqueue(db, a.id, "charge", "k3", {});
    const first = await claim(db, a.id, "charge", "w1", 100);
    expect(first?.id).toBe(id);
    await sleep(150); // w1 chết trước complete
    const retry = await claim(db, a.id, "charge", "w2", 5000);
    expect(retry?.id).toBe(id);
    if (!retry) throw new Error("không có job");
    expect(await complete(db, a.id, retry, "đã thu")).toBe(true);
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
      if (!job) throw new Error("không có job");
      expect(await fail(db, b.id, job, `lỗi ${i}`)).toBe(true);
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
