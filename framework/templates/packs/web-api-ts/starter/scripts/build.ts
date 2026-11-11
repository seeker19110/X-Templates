// Build artifact tái lập được: dist/app.tgz (mã nguồn chạy trực tiếp bằng Node 24 + lock) và dist/app.tgz.sha256.
// Cùng commit → cùng digest (tar sắp tên, mtime/owner cố định, gzip -n), nên "promote đúng digest" kiểm được: digest ghi ở
// GO-NO-GO.md phải khớp `release-check` (khoá `release_artifacts` của xt.yaml, ADR-0068 lát A).
import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";

const FILES = ["package.json", "pnpm-lock.yaml", "src", "contract"];

mkdirSync("dist", { recursive: true });
// tar ghi thẳng ra dist/app.tar, không đọc qua stdout của execFileSync (maxBuffer mặc định 1 MiB → ENOBUFS khi cây đóng
// gói lớn hơn, AUD-CODE-064). dist/ không nằm trong FILES nên bản tar không tự gói mình.
execFileSync("tar", [
  "--sort=name",
  "--mtime=1970-01-01 00:00:00Z",
  "--owner=0",
  "--group=0",
  "--numeric-owner",
  "--mode=u=rwX,go=rX", // quyền file không theo umask của máy build — digest chỉ phụ thuộc nội dung
  "--exclude=*.test.ts",
  "-cf",
  "dist/app.tar",
  ...FILES,
]);
execFileSync("gzip", ["-n", "-9", "-f", "dist/app.tar"]);
execFileSync("mv", ["dist/app.tar.gz", "dist/app.tgz"]);
const digest = createHash("sha256").update(readFileSync("dist/app.tgz")).digest("hex");
writeFileSync("dist/app.tgz.sha256", `${digest}  app.tgz\n`);
console.log(`dist/app.tgz sha256:${digest}`);
