// `pnpm build` (scripts/build.ts) phải đóng được cây > 1 MiB: tar ghi thẳng ra file, không qua bộ đệm stdout của
// execFileSync (mặc định 1 MiB → ENOBUFS, AUD-CODE-064). Chạy trên bản sao tạm — không đụng dist/ của dự án.
import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { cpSync, mkdirSync, mkdtempSync, readdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { afterAll, beforeAll, expect, it } from "vitest";

let work: string;

function build(): string {
  return execFileSync(process.execPath, ["scripts/build.ts"], { cwd: work, encoding: "utf8" });
}

beforeAll(() => {
  work = mkdtempSync(join(tmpdir(), "build-"));
  for (const f of ["package.json", "pnpm-lock.yaml", "src", "contract"]) {
    cpSync(f, join(work, f), { recursive: true });
  }
  mkdirSync(join(work, "scripts"));
  cpSync("scripts/build.ts", join(work, "scripts/build.ts"));
  writeFileSync(join(work, "src/big.bin"), Buffer.alloc(1_100_000)); // > maxBuffer mặc định 1 MiB của Node
});

afterAll(() => {
  rmSync(work, { recursive: true, force: true });
});

it("đóng gói cây lớn hơn 1 MiB, digest khớp file và build lại ra cùng digest", () => {
  const out = build();
  const digest = createHash("sha256")
    .update(readFileSync(join(work, "dist/app.tgz")))
    .digest("hex");
  expect(readFileSync(join(work, "dist/app.tgz.sha256"), "utf8")).toBe(`${digest}  app.tgz\n`);
  expect(out).toContain(`sha256:${digest}`);
  expect(readdirSync(join(work, "dist")).sort()).toEqual(["app.tgz", "app.tgz.sha256"]); // không để lại app.tar tạm
  build();
  expect(readFileSync(join(work, "dist/app.tgz.sha256"), "utf8")).toBe(`${digest}  app.tgz\n`);
});
