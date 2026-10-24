# PLAN-3.17-feedback.md — Khung X-Templates · sửa lỗi dự án đích báo về → bản 3.17.0

> Lập ngày 2026-10-23. Chủ repo gọi lại `/autopilot` sau PLAN-3.16.0-ceiling (done). Nguồn: gộp phản hồi 4 dự án đích
> (T-2410, [TARGETS](../ops/TARGETS.md)) → phân loại 30 nhóm trên HEAD 3.16.0: 11 đã sửa · 15 còn lỗi (6 🟠, 9 🟢) · 3 thiết
> kế · 1 không phải lỗi (bảng phân loại ở scratchpad phiên — chứa trích dẫn dự án, không commit). Phiên chính tự duyệt (D-149).
>
> **Cú pháp bắt buộc cho máy:** mỗi task một dòng `- [ ] \`T-NNNN\` <việc> — Gate: \`<lệnh>\``.

## Tóm tắt (cổng duyệt — phiên chính tự duyệt, D-149)
- Phạm vi: 6 🟠 còn tái hiện được trên HEAD + 2 🟢 cùng file với 🟠 (rẻ). Mỗi lỗi: test tái hiện đỏ trước (payload giả —
  guard qua `bash_decision`/`apply_policy`, không chạy lệnh nguy hiểm thật), sửa, xanh.
- Ưu tiên: guard để lọt xoá gốc dự án (không đảo ngược) → xanh giả của `blueprint-status` → vòng tự trị (worktree, Stop hook
  của phiên khác) → `feedback collect` lộ dữ liệu dự án.
- Không làm: 7 🟢 còn lại (loop init/decide song song, kiểm LOOP-ORCH-003, BASE-SEC-002 tự khớp, anchor của check-links/
  compose) — ghi PROGRESS; nhóm "thiết kế" giữ nguyên (ADR-0017/0018, LOOP-STOP-021). Trần byte ADR-0043 giữ nguyên.
- Rủi ro: luật guard mới chặn oan lệnh hợp lệ (đỡ: bộ test chặn-nhầm hiện có + ca hợp lệ mới: xoá thư mục con, `rm -rf
  node_modules`, worktree khác repo); Stop hook gắn phiên làm vòng tự trị một phiên mất lượt (đỡ: test hook với payload có/
  không `session_id`).

## Ngân sách (4 con số)
- Số vòng tối đa: `max(40, 8 × task)` (`loop init --single-session` tính)
- Chi phí: 0 đồng ngoài phiên (không phụ thuộc mới)
- Timeout mỗi lệnh Gate: 1800 giây (`XT_RECORD_TIMEOUT` mặc định)
- Ngày hết hạn: 12 giờ sau `loop init` (`--hours 12`)

## Điểm dừng bắt buộc (`loop defer`; `loop block` khi mọi việc còn lại phụ thuộc)
- Đổi ruleset sống, secret, quyền repo đích: chủ repo
- Nâng khung ở dự án đích (PR `install.py`): chủ dự án merge

## Task

### Lát 1 — Guard (hàng rào)
- [x] `T-2501` Guard chặn xoá gốc dự án hoặc thư mục cha của nó: `rm -rf|-fr|-r -f ROOT`, `"$CLAUDE_PROJECT_DIR"`, `ROOT/..`, `../<tên gốc>`, `cd .. && rm -rf <gốc>`, `find ROOT -delete` (phản hồi dự án đích, 🟠); xoá thư mục con vẫn cho chạy (exec: deep) (files: .claude/hooks/guard.py, tests/test_guard_feedback1023.py, CHANGELOG.md) — Gate: `python3 -m unittest discover -s tests -k wipe_project_root`
- [x] `T-2502` Guard không chặn oan `rm -rf` một worktree đã đăng ký (`git worktree list`) của chính repo; vẫn chặn worktree đang đứng và gốc chính (🟢, cùng luật WIPE_OUTSIDE) (sau: T-2501; files: .claude/hooks/guard.py, tests/test_guard_feedback1023.py) — Gate: `python3 -m unittest discover -s tests -k wipe_own_worktree`
- [x] `T-2503` Lệnh Bash gộp sửa file với `git commit`: cổng commit chạy trên cây TRƯỚC lệnh → sửa + commit một lệnh lọt cổng (gặp ở phiên 2026-10-23), cổng đỏ thì phần sửa không chạy mà thông báo không nói (🟢). Guard từ chối `git commit` đi sau lệnh có thể ghi file (trừ `cd`, `git add`, `git status`, …), lý do "tách: sửa trước, commit lệnh riêng" (sau: T-2502; files: .claude/hooks/guard.py, .claude/hooks/pre-bash-guard.sh, tests/test_guard_feedback1023.py, framework/11-autonomous-loop/stop-points-and-escalation.md) — Gate: `python3 -m unittest discover -s tests -k commit_after_write`

### Lát 2 — `blueprint-status` không xanh giả
- [x] `T-2511` `[~]` mang cả "Không áp dụng" lẫn "Miễn" (hoặc thiếu `Duyệt:` khi là miễn MUST) → `--strict` đỏ như MUST mở (🟠) (files: scripts/xt.py, tests/test_xt.py, CHANGELOG.md) — Gate: `python3 -m unittest discover -s tests -k waiver_needs_approval`
- [x] `T-2512` Mục checklist ghi ID in đậm (`**ABC-001**`) thay vì backtick: nhận được hoặc báo lỗi định dạng; file blueprint 0 mục nhận diện được → `--strict` đỏ (cổng rỗng là đỏ — ADR-0011) (🟠) (sau: T-2511; files: scripts/xt.py, tests/test_xt.py) — Gate: `python3 -m unittest discover -s tests -k blueprint_bold_id`

### Lát 3 — Vòng tự trị
- [x] `T-2521` `loop record`/`loop status` chạy trong git worktree: Gate chạy và tick PLAN ở worktree đang đứng (gốc = `git rev-parse --show-toplevel` của cwd khi nằm trong cùng repo), không ở cây chính (🟠) (exec: deep) (files: scripts/xt.py, tests/test_xt_loop.py, CHANGELOG.md) — Gate: `python3 -m unittest discover -s tests -k loop_worktree_root`
- [x] `T-2522` Stop hook chỉ áp vòng cho đúng phiên đã `loop init` (ghi `session_id` khi init; payload khác phiên/không đọc được → không chặn, ghi log), không tăng `iterations` của vòng phiên khác (🟠) (sau: T-2521; exec: deep) (files: scripts/xt.py, tests/test_xt_loop.py) — Gate: `python3 -m unittest discover -s tests -k stop_hook_session_bound`

### Lát 4 — Phản hồi và phát hành
- [x] `T-2531` `feedback collect`: không chép nguyên văn lý do miễn trừ của dự án (chỉ ID + loại + tóm tắt chuẩn hoá), khử trùng theo (loại, ID) với FB đã có kể cả khi lý do đổi chữ (🟠) (files: scripts/xt.py, tests/test_xt_cli.py, CHANGELOG.md) — Gate: `python3 -m unittest discover -s tests -k feedback_collect_no_project_data`
- [x] `T-2539` VERSION 3.17.0 + CHANGELOG `[3.17.0]` (dự án đích chạy lại `install.py` — guard/hook đổi) + PROGRESS (7 🟢 còn lại) (sau: T-2503, T-2512, T-2522, T-2531; files: VERSION, CHANGELOG.md, PROGRESS.md) — Gate: `scripts/dev-task.sh gate`
