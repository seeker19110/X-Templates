# AUDIT-REPORT — Khung X-Templates · 2026-10-27 (delta 2, lát 1)

> Commit quét: `6acc57380efc98736928fad9e7de26da7fb4916d` (`main`, sau #291, #293–#301) · Chế độ: **delta** từ `95fa52a` (ARCH, SEC, CODE, TEST, PERF, A11Y, CI, DOC, XFEAT, HAR, CFG) · Quy trình: [`framework/00-method/audit.md`](../../framework/00-method/audit.md)
> Người quét: phiên chính + 3 subagent `reviewer` read-only (SEC/CFG/DEP/CI · ARCH/CODE/TEST/PERF/XFEAT · DOC/HAR/A11Y), task T-3556 của PLAN-harden-2026-10-27-loops · Xác minh đối kháng: `reviewer-alt` (Opus 5.5, effort max) cho 5 🟠 của người tìm, `reviewer` thứ hai cho 2 🟠 do người xác minh tìm thêm
> `python3 scripts/xt.py audit check docs/ops/AUDIT-STATUS.md` → exit 0 · `--strict` đỏ tới khi 5 🟠 sửa (D-214)

## 1. Tóm tắt

| Mức | Mới | Ghi chú |
|---|---|---|
| 🔴 | 0 | — |
| 🟠 | 5 | AUD-SEC-116, AUD-SEC-119, AUD-PERF-003, AUD-XFEAT-026, AUD-XFEAT-027 — đều quanh vòng tối ưu (`perf guard`, `perf sample`, Gate mẫu) |
| 🟢 | 20 | AUD-SEC-115/117/118, AUD-XFEAT-028/029, AUD-TEST-023/024, AUD-CODE-024, AUD-DOC-091…097, AUD-HAR-117…120; cập nhật AUD-TEST-020 |

Kết luận: **chặn cắt 3.28.0 tới khi 5 🟠 sửa** (PLAN: "🔴/🟠 sửa trước khi cắt bản"). Mã lát 1 (`rev`/khoá, `task_runs`,
attach/resolve/unblock, `pr rethink`, mẫu perf v2) không có 🟠 riêng; 🟠 nằm ở đường chấm điểm tối ưu mà 3.28.0 đưa tới dự án đích
(Gate mẫu cho candidate gian lận báo `improved` giả, đo thời gian lượng tử 50 ms) — phần lớn có từ trước delta (`ac1bd2f`, 3.20.0).

## 2. Phạm vi (`xt.py audit plan`)

PR trong diff: #291 bump `claude-code-action` v1.0.262 · #293 FLOW-07/08/18/19 + sổ mốc Lát 0 · #294 `rev` + khoá, `task_runs` ·
#295 `loop attach/resolve/unblock` · #296 chữ `loop resume` · #297 PLAN review theo pha · #298 ngân sách review (`rethink`, ADR-0053) ·
#299 PROGRESS · #300 `perf sample` v2 · #301 `perf compare` từ chối cặp không so được.
Giữ nguyên: DEP (không manifest/lockfile đổi — #291 kiểm ở CI), DATA (N/A).

## 3. Lệnh đã chạy

| Nhóm | Lệnh | Exit | Kết quả chính |
|---|---|---|---|
| tất cả | `scripts/dev-task.sh gate` (ở `7bd84f3`, cây = `6acc573`) | 0 | 5 lệnh xanh; coverage 100 % (12640 stmt, 4692 nhánh); 397 s real |
| tất cả | `xt.py blueprint-status BLUEPRINT.md --strict --run` | 0 | — |
| CI/DEP | `xt.py ci-check` · `git ls-remote` claude-code-action | 0 | 10 workflow; `925afb5…` = `v1.0.262` |
| SEC | `ruff check --select S scripts/xt.py` | 1 | 17 = base `95fa52a` (không mới) |
| CODE | `ruff check` · `mypy --strict scripts/xt.py` | 0 | C901 ≤ 10 |
| TEST | `XT_FLOW_STRICT=FLOW-01…08,18,19 unittest tests.test_flow` · 27 đột biến | 0 | 26/27 đột biến bị bắt (sống: AUD-TEST-024) |
| DOC | `validate` · `check-links` · `changelog-check` · `progress-check` · `test_docs_budget` | 0 | — |
| HAR | `doctor --json` (không `--fix`) · `autonomy-bench` · `unittest tests.test_merge tests.test_flow` | 0 | 0 phát hiện; 167 OK |
| A11Y | `git diff --stat 9e1d6f3 HEAD -- scripts/app …` · check run `app-e2e` #301 | 0 | UI không đổi; e2e xanh |

Chưa biết / bị chặn: gitleaks toàn lịch sử cục bộ (tải công cụ bị bộ phân loại chặn — dựa job CI `gitleaks` xanh ở #300/#301);
zizmor/actionlint (máy không có); guard chặn dựng bản sao cho đột biến AUD-HAR-117 (giữ `suy luận:`).

## 4. Phát hiện 🟠 (đã xác minh đối kháng)

1. **AUD-SEC-116** — `perf guard --strict` dò dòng đáng ngờ trên `git diff --unified=0` không `--text`: file có thuộc tính `-diff`
   (`.gitattributes` trong cây, `.git/info/attributes`, `core.attributesFile`) thành "Binary files differ" → 0 dòng → exit 0. Tái hiện: thêm
   `lru_cache` → exit 1; thêm `* -diff` → exit 0; thêm `--text` → dòng hiện lại.
2. **AUD-SEC-119** — Gate mẫu lấy script/baseline từ tên `origin/main`; `git update-ref refs/remotes/origin/main HEAD` (và `tag`, `branch -f`,
   `fetch .`) qua guard (`guard-check` exit 0, đối chứng `reset --hard` 126) → Gate chạy script agent viết.
3. **AUD-PERF-003** — `_perf_run` đo quanh `Popen.wait(timeout)` (thăm dò ≤ 50 ms): `sleep 0.059` vs `0.058` qua lệnh cố định → "improved
   −43,81 %, p=0,0058" (thật −1,7 %); 0,080 → 0,059 → `neutral` (thật −26 %).
4. **AUD-XFEAT-026** — Gate mẫu ghi `before.json` vào cây agent; candidate sửa `samples` lúc đo → "improved −98,25 %" dù chậm hơn; qua
   `loop record` tick `[x]`.
5. **AUD-XFEAT-027** — Gate mẫu chạy công cụ chấm ở `$wt`; candidate tìm `$wt` qua `git worktree list`, sửa `_perf_compare_cmd` → "improved"
   giả, `trap` xoá dấu vết; biến thể `usercustomize.py` khi không `-I`.

Hạ mức sau xác minh: AUD-SEC-115 (`perf guard --base=--output=`) 🟠→🟢 (người gọi phải tự viết `--base`; Gate mẫu chặn trước);
AUD-XFEAT-028 (`task_runs` ID blueprint) 🟠→🟢 (chủ ý D-206, fail-closed).

## 5. Kế hoạch (D-214)

Bốn task, mỗi task một PR, trước T-3556/T-3546: **T-3560** `perf guard` `--text` + cảnh báo `.gitattributes` + `--base` qua `perf_rev`
(SEC-116, SEC-115) · **T-3561** `perf sample` đo không lượng tử (PERF-003) · **T-3562** Gate mẫu: `before.json` ngoài cả hai cây + sha256
giữ trong biến shell, công cụ chấm từ SHA gốc chạy `python3 -I`, giới hạn còn lại (cùng uid) ghi tới `perf trial` (XFEAT-026/027) ·
**T-3563** guard chặn ghi ref remote-tracking và tag/nhánh trùng tên remote (SEC-119). Sau đó quét lại nhóm bị chạm → `audit check --strict`.
Nợ 🟢: AUD-DOC-091/092 ở T-3546; AUD-HAR-120 sửa trong PR này; còn lại giữ `mở`; AUD-SEC-117 `chấp nhận` (chủ phiên chính, hạn 2027-01-21).
