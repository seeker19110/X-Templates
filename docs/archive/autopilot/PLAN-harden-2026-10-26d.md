# PLAN-harden-2026-10-26d.md — Khung X-Templates · việc chờ người đã duyệt: hook trích lỗi, ca đối kháng, mutation guard

> Lập ngày 2026-10-26 theo `/complete` (pha harden). Chủ repo duyệt 2026-10-26 ("xem nó là gì tôi duyệt luôn" → chọn
> T-1822, T-1832, T-1823, đóng sổ T-1814). T-1834 vẫn chờ chủ hai repo đích gỡ `merge-gate` khỏi ruleset. Phiên chính tự
> duyệt cách làm (D-196).
>
> **Cú pháp bắt buộc cho máy:** mỗi task một dòng `- [ ] \`T-NNNN\` <việc> — Gate: \`<lệnh>\``.

## Tóm tắt (cổng duyệt — phiên chính tự duyệt, D-196)
- T-3531 (thay T-1822): đăng ký hook `PostToolUseFailure` (matcher `Bash`) → `post-tool-failure.sh` → `xt.py loop
  triage-local` (đã có, có test). Payload xác minh với tài liệu sống 2026-10-26 (code.claude.com/docs/en/hooks
  §PostToolUseFailure: `tool_name`, `tool_input`, `error`, `is_interrupt`; ra `hookSpecificOutput.additionalContext`).
  `install.py` tự chép hook đã đăng ký; `doctor` cảnh báo khi thiếu sự kiện. Test "chưa đăng ký" giữ nhánh bằng mock.
- T-1814 đóng sổ: đã làm thay ở T-2121 (PLAN-3.15, AUD-SEC-102).
- T-3532 (thay T-1823): reviewer năng lực cao nhất viết ≥ 20 ca `origin: adversarial-reviewer` nhắm lách guard/merge vào
  `tests/fixtures/autonomy/`; ca lọt → phát hiện AUD + sửa (lát riêng nếu lớn).
- T-3533 (thay T-1832): spike `mutmut` trên `guard.py` ở venv tạm ngoài repo (≤ 20 phút), báo cáo
  `docs/ops/MUTATION-2026-10-26.md`; khả thi → đề xuất job tuần (phụ thuộc ghim hash) ở lát riêng; không → D-NNN.
- T-3534: CHANGELOG `[3.27.0]` (dự án đích chạy lại `install.py` để nhận hook), VERSION, PROGRESS.
- Rủi ro: hook mới chạy mỗi lần Bash lỗi — fail-open, ≤ 30 s timeout, chỉ in khi lệnh là cổng/Gate. Đường lùi: revert PR.

## Ngân sách (4 con số)
- Số vòng tối đa: 40 (`--single-session`) · Chi phí: 0 đồng ngoài phiên · Timeout Gate: 1800 giây · Hạn: 6 giờ sau `loop init`

## Điểm dừng bắt buộc (`loop defer`)
- T-1834: chủ hotel-manager, X-Company gỡ context `merge-gate` khỏi ruleset sống.

## Task
- [x] `T-3531` Đăng ký hook PostToolUseFailure; doctor; test (files: .claude/settings.json, scripts/install.py, scripts/xt.py, tests/test_hooks.py, tests/test_install.py) — Gate: `grep -q '"PostToolUseFailure"' .claude/settings.json && python3 -m unittest tests.test_hooks.HookFailOpenTest tests.test_install.InstallPlanTest.test_unregistered_framework_hook_is_not_installed && python3 scripts/xt.py doctor`
- [x] `T-3532` ≥ 20 ca adversarial-reviewer cho autonomy-bench (files: tests/fixtures/autonomy/, docs/ops/AUTONOMY-BASELINE.md) — Gate: `python3 scripts/xt.py autonomy-bench && test "$(cat tests/fixtures/autonomy/*.json | grep -c '"origin": "adversarial-reviewer"')" -ge 20`
- [x] `T-3533` Spike mutmut trên guard.py, báo cáo (files: docs/ops/MUTATION-2026-10-26.md) — Gate: `test -s docs/ops/MUTATION-2026-10-26.md && grep -qE 'killed|survived' docs/ops/MUTATION-2026-10-26.md`
- [x] `T-3534` CHANGELOG [3.27.0], VERSION 3.27.0, PROGRESS (sau: T-3531, T-3532, T-3533; files: CHANGELOG.md, VERSION, PROGRESS.md) — Gate: `test "$(cat VERSION)" = 3.27.0 && grep -q '^## \[3.27.0\]' CHANGELOG.md && test "$(wc -c < PROGRESS.md)" -le 7900 && scripts/dev-task.sh lint`
