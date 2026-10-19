# PLAN.md — Khung X-Templates · bản 3.5.0: ghi công AI qua MCP/`gh pr` + kiểm tiêu đề PR cục bộ (2026-10-19)

> Lập ngày 2026-10-19. Chủ repo gọi `/autopilot` (không đối số); việc lấy từ PROGRESS *Tiếp theo* 1 (D-055).
> Kế hoạch trước (T-1201…T-1206, 3.4.1) xong ở #138–#139.

## Tóm tắt (cổng duyệt — phiên chính tự duyệt, D-055…056)
- Phạm vi: (A) `LOOP-HARNESS-027` bịt lỗ "commit qua tool MCP" + tiêu đề/thân PR (MCP `create_pull_request`/
  `update_pull_request`, `gh pr create|edit`, commit qua MCP `create_or_update_file`/`push_files`/`delete_file`/
  `merge_pull_request`); (B) `merge-check` trả `fix` khi tiêu đề PR sai Conventional Commits hoặc > 72 ký tự (D-056).
- Stack: Python ≥ 3.11 stdlib, không phụ thuộc mới; cổng `scripts/dev-task.sh gate` (mypy --strict, coverage 100%).
- Không làm: URL phiên do máy chủ MCP tự gắn sau hook (ngoài tầm guard — ghi giới hạn); task `[perf]` (D-041).
- Nhánh: lát A+B một PR (cùng sửa CHANGELOG/harness-files), phát hành một PR. Dự án đích chạy lại `install.py`
  (matcher hook mới) → bản minor.
- Rủi ro: chặn nhầm PR hợp lệ (đỡ: chỉ khi `ai_attribution: forbid`, cùng regex commit); hook MCP mới fail-closed
  nhầm (đỡ: tool không phải merge fail-open, D-057).

## Ngân sách (4 con số)
- Số vòng tối đa: 40 (`max(40, 8 × task chưa làm)`)
- Chi phí: 0 đồng ngoài phiên (không phụ thuộc mới)
- Timeout mỗi lệnh Gate: 1800 giây (`XT_RECORD_TIMEOUT` mặc định)
- Ngày hết hạn: 8 giờ sau `loop init` (`--hours 8`)

## Điểm dừng bắt buộc (`loop defer`; `loop block` khi mọi việc còn lại phụ thuộc)
- Ruleset đòi review của người (`merge-check` = `human`) → báo chủ repo, làm lát khác
- Force-push, xoá nhánh, đổi quyền/ruleset repo

## Task

### Lát A — guard ghi công AI ngoài `git commit` (D-055, D-057)
- [x] `T-1301` MCP ghi PR/commit (`create_pull_request`, `update_pull_request`, `create_or_update_file`, `push_files`, `delete_file`, `merge_pull_request`) có tên model/URL phiên ở repo `ai_attribution: forbid` → deny; matcher hook mở rộng, tool không phải merge fail-open — Gate: `python3 -m unittest tests.test_hooks`
- [x] `T-1302` `gh pr create|edit` với `--title/-t`, `--body/-b`, `--body-file/-F` (file, heredoc) ghi công AI → deny — Gate: `python3 -m unittest tests.test_hooks tests.test_guard_corpus`

### Lát B — tiêu đề PR (D-056)
- [x] `T-1303` `merge-check` đọc tiêu đề PR (REST + gh): sai `<type>(scope)!: mô tả` hoặc > 72 ký tự → verdict `fix` kèm lý do — Gate: `scripts/dev-task.sh gate`

### Lát C — phát hành
- [x] `T-1304` VERSION 3.5.0 + CHANGELOG `[3.5.0]` + PROGRESS; tag `v3.5.0` — Gate: `scripts/dev-task.sh gate`
