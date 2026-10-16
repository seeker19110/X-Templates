@AGENTS.md

<!-- Claude Code chỉ đọc CLAUDE.md khi có cả hai file; dòng import trên nạp AGENTS.md (nguồn sự thật duy nhất, dùng chung mọi harness). Chỉ thêm vào đây những gì RIÊNG cho Claude Code. -->

## Riêng cho Claude Code
- Hook trong `.claude/settings.json`: SessionStart nạp PROGRESS + trạng thái autopilot (cả sau compaction); PreCompact ghi checkpoint (`xt.py loop checkpoint`, luôn exit 0); PreToolUse chặn lệnh phá huỷ/`curl|sh` (cả lồng trong `sh -c`/heredoc), chặn ghi file bí mật, hỏi khi deploy/publish/push nhánh chính/merge PR (kể cả `gh api` ghi và tool MCP merge — chỉ tự merge khi `xt.py merge-check` cho phép), khi sửa cấu hình cổng/CI/hook/migration đã có, khi làm yếu/xoá test đã có, khi ghi tay `.autopilot/`; chạy cổng chất lượng trước `git commit` (commit vào repo ngoài dự án thì hỏi); PostToolUse format file vừa sửa; Stop đọc bằng chứng autopilot (`xt.py loop hook-stop`) để quyết cho dừng hay làm tiếp.
- `permissions.defaultMode` trong settings dự án **bị Claude Code bỏ qua** với `auto`/`bypassPermissions`; muốn chạy không hỏi quyền hãy bật ở settings người dùng hoặc `--permission-mode` — autopilot một phiên cần `claude --permission-mode auto` (Stop hook cảnh báo khi phiên ở chế độ hỏi quyền). Hook `deny` vẫn chặn kể cả ở bypass.
- Skill gọi bằng `/autopilot`, `/blueprint`, `/gate`, `/research`, `/audit`, `/review`, `/adr`, `/handover` (định nghĩa ở `.claude/skills/*/SKILL.md`).
- Chạy headless cho CI: **không** dùng `--bare` (mất hook/skill/CLAUDE.md).
