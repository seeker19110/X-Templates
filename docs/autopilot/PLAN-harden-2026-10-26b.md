# PLAN-harden-2026-10-26b.md — Khung X-Templates · ERR-001, lệnh kiểm blueprint trên CI, siết SEC-004

> Lập ngày 2026-10-26 theo `/complete` (pha harden), nối PLAN-harden-2026-10-26 (#274). Nguồn: đề xuất cuối #274 và
> 🟢 review lượt 4 của #274. Phiên chính tự duyệt (D-194).
>
> **Cú pháp bắt buộc cho máy:** mỗi task một dòng `- [ ] \`T-NNNN\` <việc> — Gate: \`<lệnh>\``.

## Tóm tắt (cổng duyệt — phiên chính tự duyệt, D-194)
- (1) BASE-ERR-001: `_load_guard` (`scripts/xt.py`) `except Exception: pass` → báo stderr loại + lời lỗi, giữ module dở
  (hành vi fail-open không đổi); test `test_broken_guard_module_fails_open` đỏ trước khi sửa; gắn `— Kiểm:` ruff
  S110/S112 (except rộng nuốt lỗi). Except hẹp có lối xử lý (`continue` bỏ file không đọc được, `pass` rồi trả bản
  không SHA) giữ — đó là xử lý, không phải nuốt.
- (2) CI job `checks`: `blueprint-status BLUEPRINT.md --strict --run` (+ cài `requirements-dev.txt` kèm hash cho ruff) —
  31 lệnh kiểm chạy trên MỖI PR thay vì chỉ `loop verify`/`release-check` cục bộ (sửa cấu hình CI: lý do này).
- (3) SEC-004: cụm cờ curl có chữ số (`-4k`), dừng ở `;`, `sslverify` mọi hoa/thường và `0|no|off|false`, JSON
  `"sslVerify": false`, `--proxy-insecure`, npm `strict-ssl false`; `git grep …; test $? -eq 1` để regex hỏng/path ngoài
  repo (exit 128) là đỏ (pathspec không tồn tại trong repo vẫn exit 1 — xanh).
- REPO-006 (review #277 🔴): kiểm tag gần nhất annotated + VERSION = tag hoặc bản đang cắt chưa có tag và chưa lên `main` (HEAD = `origin/main` được miễn khi tag đang tạo) — trước đây đòi tag `v<VERSION>` có sẵn nên PR cắt bản đỏ CI.
- Không làm: curl nhiều dòng (`\` nối dòng) — giới hạn của kiểm theo dòng, đã chấp nhận ở review #274.
- Rủi ro: C901/byte trần `scripts/` (cắt chú thích bù); CI thêm ~10 s. Đường lùi: revert PR.
- Cách làm: phiên chính tự làm; một PR làn chuẩn (mã + CI) → reviewer-alt.

## Ngân sách (4 con số)
- Số vòng tối đa: 20 (`--single-session`) · Chi phí: 0 đồng ngoài phiên · Timeout Gate: 1800 giây · Hạn: 3 giờ sau `loop init`

## Điểm dừng bắt buộc (`loop defer`)
- Không có.

## Task
- [x] `T-3511` `_load_guard` báo lỗi nạp ra stderr; test đỏ trước khi sửa; `— Kiểm:` BASE-ERR-001 = ruff S110/S112 (files: scripts/xt.py, tests/test_xt_core.py, BLUEPRINT.md) — Gate: `python3 -m unittest tests.test_xt_core.GuardChokePointTest.test_broken_guard_module_fails_open && python3 -m ruff check --quiet --select S110,S112 scripts .claude/hooks && grep -qE '^- \[x\] .BASE-ERR-001. .*— Kiểm: ' BLUEPRINT.md && python3 -m unittest tests.test_docs_budget`
- [x] `T-3512` CI job `checks` chạy `blueprint-status BLUEPRINT.md --strict --run` (files: .github/workflows/ci.yml) — Gate: `grep -q 'blueprint-status BLUEPRINT.md --strict --run' .github/workflows/ci.yml && python3 scripts/xt.py ci-check && python3 -m unittest tests.test_ci`
- [x] `T-3513` Siết SEC-004 theo 🟢 review #274 lượt 4 (files: BLUEPRINT.md) — Gate: `grep -qE '^- \[x\] .BASE-SEC-004. .*test [$][?] -eq 1' BLUEPRINT.md && python3 scripts/xt.py blueprint-status BLUEPRINT.md --strict --run`
- [x] `T-3514` CHANGELOG Unreleased, PROGRESS ≤ 7 900 B (sau: T-3511, T-3512, T-3513; files: CHANGELOG.md, PROGRESS.md) — Gate: `grep -q 'D-194' CHANGELOG.md && grep -q 'PLAN-harden-2026-10-26b' PROGRESS.md && test "$(wc -c < PROGRESS.md)" -le 7900 && scripts/dev-task.sh lint`
