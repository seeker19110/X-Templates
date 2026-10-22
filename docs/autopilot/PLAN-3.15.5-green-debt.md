# PLAN-3.15.5-green-debt.md — Khung X-Templates · dọn 🟢 rẻ của sổ audit (guard, quyền đọc, cổng) → bản 3.15.5

> Lập ngày 2026-10-22. Chủ repo gọi `/autopilot` không kèm yêu cầu: không PR mở, vòng lặp tắt, PROGRESS không còn task
> máy làm được (mọi task hoãn đều chờ người). Phiên chính chọn các 🟢 `mở` của [`AUDIT-STATUS.md`](../ops/AUDIT-STATUS.md)
> có đường tái hiện máy kiểm được và bản vá nhỏ, không cần quyết chính sách của chủ repo (D-138, ADR-0008).
>
> **Cú pháp bắt buộc cho máy:** mỗi task một dòng `- [ ] \`T-NNNN\` <việc> — Gate: \`<lệnh>\``.

## Tóm tắt (cổng duyệt — phiên chính tự duyệt, D-138)
- Phạm vi: AUD-SEC-076, AUD-SEC-100, AUD-CFG-004 (Lát 1 — guard, quyền đọc); AUD-XFEAT-002, AUD-TEST-019 (Lát 2 — cổng).
  Mỗi bug: test tái hiện đỏ trước, sửa, xanh.
- Không làm: 🟢 cần quyết chính sách (AUD-SEC-043 `npx`, AUD-SEC-060 ghi ngoài dự án, AUD-HAR-028 heuristic test),
  việc chờ chủ repo (HAR-036, SEC-026, CI-006/007/009), tách `xt.py` (AUD-ARCH-001).
- Stack: Python ≥ 3.11 stdlib, bash; 0 phụ thuộc mới; cổng `scripts/dev-task.sh gate` (mypy --strict, coverage 100 %).
- Nhánh: phiên một nhánh → lát tuần tự, mỗi lát một PR ≤ 150 dòng mã.
- Rủi ro: luật guard mới chặn oan (đỡ: ca hợp lệ trong cùng lớp test); thêm `Read` deny chặn đọc khoá công khai (đỡ: chỉ
  tên khoá riêng `id_rsa`/`id_ed25519`, không `*.pub`); bộ phân loại Auto chặn sửa guard → `loop defer`.

## Ngân sách (4 con số)
- Số vòng tối đa: `max(40, 8 × task)` (`loop init --single-session` tính)
- Chi phí: 0 đồng ngoài phiên
- Timeout mỗi lệnh Gate: 1800 giây (`XT_RECORD_TIMEOUT` mặc định)
- Ngày hết hạn: 12 giờ sau `loop init` (`--hours 12`)

## Điểm dừng bắt buộc (`loop defer`; `loop block` khi mọi việc còn lại phụ thuộc)
- Sửa `.claude/hooks/guard.py` hoặc `.claude/settings.json` bị bộ phân loại chặn → `loop defer` kèm bản vá đề xuất
- Đổi ruleset sống, secret, quyền repo: chủ repo

## Task

### Lát 1 — Guard và quyền đọc
- [x] `T-2201` Guard: `shutil.rmtree(os.environ.get("HOME"))` (và `environ.get('HOME', …)`) là xoá home → deny; `rsync --delete-missing-args`/`--delete-excluded`/`--delete-delay` (tên có `-`) lên đích ngoài dự án → deny (AUD-SEC-076) (files: .claude/hooks/guard.py, tests/test_guard_audit1019.py) — Gate: `python3 -m unittest tests.test_guard_audit1019 -k delete_outside_project -k delete_inside_project`
- [x] `T-2202` Guard: `git -C ~+/x commit` / `git -C ~-/x commit` — `~+`/`~-` là `$PWD`/`$OLDPWD`, không phải thư mục con tên `~+` → `commit_dir` không biết (rỗng, cổng chạy ở gốc), như `cd ~+` (AUD-SEC-100) (sau: T-2201; files: .claude/hooks/guard.py, tests/test_hooks.py) — Gate: `python3 -m unittest tests.test_hooks -k commit_dir`
- [x] `T-2203` `.claude/settings.json` `permissions.deny` thêm `Read` cho mọi mẫu bí mật của guard (`.envrc`, `.npmrc`, `.pypirc`, `.netrc`, `*.p12`, `*.pfx`, `id_rsa`, `id_ed25519`); test đối chiếu `SECRET_PATTERNS` ↔ `Read(...)` để hai danh sách không lệch lại (AUD-CFG-004) (files: .claude/settings.json, tests/test_hooks.py) — Gate: `python3 -m unittest tests.test_hooks -k read_deny_covers_secret`

### Lát 2 — Cổng nhất quán
- [x] `T-2211` Khoá trùng trong `xt.yaml`: `dev-task.sh` lấy dòng **cuối** như `xt.py` (`_yaml_keys`), `doctor` báo lỗi `xt-yaml` "khoá trùng" (AUD-XFEAT-002) (files: scripts/dev-task.sh, scripts/xt.py, tests/test_doctor.py, tests/test_hooks.py) — Gate: `python3 -m unittest tests.test_doctor -k duplicate_key && python3 -m unittest tests.test_hooks -k duplicate_key`
- [x] `T-2212` `xt.py test-weights`: id đỏ khi đo → ghi tạm file mới, chạy lại riêng các id đỏ; xanh hết → giữ file (trọng số lần chạy lại), còn đỏ → trả file cũ, exit 1 — hết gà–trứng của `test_committed_weights_cover_every_class` (AUD-TEST-019) (sau: T-2211; files: scripts/xt.py, tests/test_ci_shard.py) — Gate: `python3 -m unittest tests.test_ci_shard -k test_weights`
- [x] `T-2213` Sổ audit (5 phát hiện → `đã sửa` kèm PR), VERSION 3.15.5, CHANGELOG `[3.15.5]`, PROGRESS (sau: T-2212; files: docs/ops/AUDIT-STATUS.md, VERSION, CHANGELOG.md, PROGRESS.md) — Gate: `python3 scripts/xt.py audit check docs/ops/AUDIT-STATUS.md && scripts/dev-task.sh lint`
