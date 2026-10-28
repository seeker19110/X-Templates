# AUDIT-REPORT — Khung X-Templates · 2026-10-28 (delta)

> Commit quét: `fcf83b3f830c74067030d27ab01b56f4c2f10db5` (`main`, sau #303–#306) · Chế độ: **delta** từ `6acc573` (ARCH, SEC, CODE, TEST, DOC, XFEAT, HAR) · Quy trình: [`framework/00-method/audit.md`](../../framework/00-method/audit.md)
> Người quét: phiên chính, task T-3556 của PLAN-harden-2026-10-27-loops · Mỗi PR #303–#306 được `reviewer-alt` (effort max) rà ở head (#306 qua `rethink`, D-216) · Xác minh đối kháng: `reviewer` thứ hai tái hiện độc lập các lỗi guard có từ trước
> `python3 scripts/xt.py audit check docs/ops/AUDIT-STATUS.md` → exit 0 · `--strict` đỏ tới khi AUD-SEC-125 🔴 và AUD-SEC-121 🟠 sửa (T-3564, D-217)

## 1. Tóm tắt

| Mức | Mới | Ghi chú |
|---|---|---|
| 🔴 | 1 | AUD-SEC-125 (tiền tố `NAME+=v` vô hiệu mọi luật guard) |
| 🟠 | 4 | AUD-SEC-121 mở (sửa ở T-3564); AUD-SEC-126, AUD-SEC-127, AUD-SEC-128 chấp nhận (D-218, hạn 2027-01-21) |
| 🟢 | 8 mới (6 `mở` + 2 `đã sửa`) | mở: AUD-SEC-120/122/123/124, AUD-TEST-025, AUD-ARCH-005 · đã sửa (#307): AUD-DOC-098, AUD-HAR-121; cập nhật AUD-TEST-020, AUD-DOC-093 |

Đã đóng: 5 🟠 của lần quét trước (AUD-SEC-116 #303, AUD-PERF-003 #304, AUD-XFEAT-026/027 #305, AUD-SEC-119 #306) và 🟢 AUD-SEC-115 (#303).

Kết luận: **chặn cắt 3.28.0 tới khi AUD-SEC-125/121 sửa**. Mã của #303–#306 không có phát hiện riêng; các lỗi mới nằm ở lớp phân tích
tiền tố/wrapper của guard, có từ trước delta, do xác minh đối kháng tìm ra khi đối chiếu tuỳ chọn/biến môi trường của shell và git.

## 2. Phạm vi

PR trong diff `6acc573..fcf83b3`: #303 `perf guard` `--text` + `--base` qua `perf_rev` · #304 `perf sample` đo không lượng tử · #305 Gate mẫu tối ưu
(`before.json` ngoài cây, công cụ chấm từ SHA gốc) · #306 guard chặn ghi ref remote-tracking. Giữ nguyên: PERF, A11Y, DEP, CI, CFG (không file nhóm đổi), DATA (N/A).

## 3. Lệnh đã chạy

| Nhóm | Lệnh | Exit | Kết quả chính |
|---|---|---|---|
| tất cả | `scripts/dev-task.sh gate` | 0 | coverage 100 % (13100 stmt, 4840 nhánh); 402 s (≈ 6 phút 42 s), ở HEAD sau sửa review #307 |
| tất cả | Gate của 5 🟠 cũ (`unittest -k test_guard_text_attr`, `test_sample_timing_resolution`, `test_gate_example_tamper`, `test_guard_remote_ref`) | 1 ở `6acc573` · 0 ở HEAD | đỏ trước, xanh sau |
| CODE | `ruff check` · `ruff --select C901` · `mypy --strict` | 0 | sạch |
| TEST | `XT_FLOW_STRICT=FLOW-01…08,18,19 unittest tests.test_flow` | 0 | xanh |
| DOC | `validate` · `check-links` · `changelog-check` · `progress-check` · `test_docs_budget` | 0 | — |
| HAR | `doctor --json` (không `--fix`) | 0 | 0 phát hiện |
| HAR | `autonomy-bench` | 0 | 523 ca (guard 385/385), false-green 0, 0 chặn oan; thêm 3 ca guard AUD-SEC-119 |
| ARCH | `guard-check` đo thời gian | 0 | ≈ 0,5 s mỗi lệnh |
| SEC | `guard-check` các ca đối kháng (§4) | 0 hoặc 126 | tái hiện được |

## 4. Phát hiện 🔴/🟠 (đã xác minh đối kháng)

1. **AUD-SEC-125 🔴 mở** — `ENV_ASSIGN_RE` (.claude/hooks/guard.py:774) không nhận `NAME+=v` là gán, nên `_strip_prefixes` coi nó là tên lệnh và mọi luật
   bị bỏ qua. Tái hiện: `guard-check -- "X+=1 rm -rf /"` → 0 (`rm -rf /` → 126); `X+=1 git push --force origin main` → 0; `bash -c 'X+=1 env | grep ^X='` in `X=1`
   (shell thật coi là gán). Gate: `python3 -m unittest -q -k test_guard_assign_append tests.test_hooks`.
2. **AUD-SEC-121 🟠 mở** — `parallel ::: "<lệnh>"`: chuỗi lệnh sau `:::` không được quét. Tái hiện: `guard-check -- 'parallel ::: "rm -rf /"'` → 0, cũng → 0 ở `6acc573`;
   dạng `parallel git …` → 126 (guard.py:5509-5515). Cần `parallel` cài sẵn. Gate: `python3 -m unittest -q -k test_guard_parallel_args tests.test_hooks`.
3. **AUD-SEC-126 🟠 chấp nhận** — biến đã export không vào lần quét `eval`/`bash -c`/`sh -c`: `export GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=core.fsmonitor GIT_CONFIG_VALUE_0=./x.sh; eval git status` → 0
   (không có `eval` → 126). Phạm vi gồm cả alias: `export GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=alias.p GIT_CONFIG_VALUE_0="push --force origin main"; eval git p` → 0
   (cũng `reset --hard`, `!rm -rf /` qua `eval`/`bash -c` sau `export`). Người xác minh đề xuất 🔴, hạ 🟠 theo D-218 (đính chính lý do "chỉ dẫn tới chạy chương trình" của D-217, sai cho nhánh alias):
   lối lách đòi che giấu cú pháp cố ý; guard là lớp chặn sai lầm bằng phân tích tĩnh, không phải ranh giới cách ly (D-015, tiền lệ D-164/D-167); lớp đỡ: sandbox/egress (LOOP-HARNESS-022), `deny` của settings, bộ phân loại Auto.
4. **AUD-SEC-127 🟠 chấp nhận** — giá trị biến đã theo dõi cũ sau `read`/`printf -v`/`source`/`for`: `export F=false; read F < v.txt; git --config-env=core.fsmonitor=F status` → 0. Cùng lý do mục 3 (D-218).
5. **AUD-SEC-128 🟠 chấp nhận** — `core.hooksPath` đặt một lần không thuộc `GIT_EXEC_KEY_RE` (guard.py:3642): `git -c core.hooksPath=./evil merge x` → 0 cả ở strict;
   `=/dev/null commit` → 0 ở mặc định. `/dev/null` tương đương `--no-verify` mà chính sách mặc định cho; `./evil` = chạy script.

Ba mục chấp nhận: chủ phiên chính, hạn 2027-01-21, D-218 (đính chính D-217); Gate máy không có (ghi bước kiểm tay).

## 5. Kế hoạch (D-217, D-218)

**T-3564** sửa AUD-SEC-125 (nhận `NAME+=v` là tiền tố gán) và AUD-SEC-121 (`parallel :::` quét chuỗi lệnh như shell lồng; files: `.claude/hooks/guard.py`, `tests/test_hooks.py`;
test tái hiện đỏ trước) → `xt.py audit check --strict` → **T-3546** cắt 3.28.0. T-3556 chuyển thành sau T-3564. Nợ 🟢: AUD-DOC-098 và AUD-HAR-121 sửa trong PR sổ này (#307);
AUD-SEC-120/122…124, AUD-TEST-025, AUD-ARCH-005 giữ `mở`; ba lối chấp nhận xét lại bằng T-3565/T-3566 nếu cần (đường lùi D-217/D-218). Các lối lách guard còn lại (`a[0]=`, `echo … | parallel`, `sem`) là giới hạn đã biết, ghi ở `harness-files.md` khi merge T-3564.
