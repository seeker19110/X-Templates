# PLAN.md — Khung X-Templates · số đo vòng + máy trạng thái merge (2026-10-18)

> Lập ngày 2026-10-18. Chủ repo gọi `/autopilot` (không đối số) sau khi làm việc 1–2 của đề xuất tối ưu autopilot
> (#106 blueprint mang lệnh kiểm, #107 sàn Gate; bản sửa #107 ở #108). Kế hoạch trước (T-1001…T-1006) xong ở #97.

## Tóm tắt (cổng duyệt — phiên chính tự duyệt, D-039)
- Blueprint repo khung: không đổi mục ngoài phạm vi; mục mới chỉ khi cần (`LOOP-DESIGN-024` số đo vòng).
- Stack: Python ≥ 3.11 stdlib (`xt.py`), không phụ thuộc mới; cổng `scripts/dev-task.sh gate` (mypy --strict, coverage 100%).
- Phạm vi (D-036): (A) đưa bản sửa sàn Gate #108 về `main`; (B) số đo vòng — `loop record` ghi nối `.autopilot/runs.jsonl`,
  lệnh `xt.py loop stats` (D-037); (C) máy trạng thái merge theo làn `xt.py pr next` + sổ review `pr reviewed` (D-038,
  ADR-0025), rút văn xuôi ở AGENTS.md, mẫu AGENTS.md, skill `/autopilot`, `LOOP-STOP-022`, `LOOP-DESIGN-020` về "chạy
  `pr next`, làm đúng `next`".
- Không làm: sàn quyền token (cần chủ repo đổi tài khoản/token); đóng gói `xt.pyz` (ADR-0010 đòi ≥ 2 dự án đích).
- Nhánh: mỗi lát một PR; lát B, C trên `seeker/quirky-knuth-v0uphi` tạo lại từ `main` (PR trước đã merge), nối tiếp.
- Rủi ro: `pr next` lệch với guard (guard vẫn là lớp chặn, `pr next` chỉ khuyến nghị) — test bảng trạng thái đủ 7 bước
  ADR-0024; văn xuôi rút gọn mà dự án đích bản cũ chưa có lệnh → mẫu AGENTS.md nêu `install.py`.

## Ngân sách (4 con số)
- Số vòng tối đa: 40 (`max(40, 8 × task chưa làm)`)
- Chi phí: 0 đồng ngoài phiên (không phụ thuộc mới)
- Timeout mỗi lệnh Gate: 1800 giây (`XT_RECORD_TIMEOUT` mặc định)
- Ngày hết hạn: 8 giờ sau `loop init` (`--hours 8`)

## Điểm dừng bắt buộc (`loop defer`; `loop block` khi mọi việc còn lại phụ thuộc)
- Merge PR nếu `merge-check` trả `hard` (repo đặt `merge_hard_exceptions: auto` → không có `hard`)
- Ruleset đòi review của người (`merge-check` = `human`) → báo chủ repo, làm lát khác
- Force-push, xoá nhánh, đổi quyền/ruleset repo

## Task

### Lát A — sàn Gate dùng khoá khai báo (#108)
- [x] `T-1101` Review sạch rồi đưa #108 về `main` (merge ghim head đã rà) — Gate: `git fetch -q origin main && git grep -q 'def gate_floor_commands' origin/main -- scripts/xt.py`

### Lát B — số đo vòng (D-037)
- [x] `T-1102` `loop record` ghi nối `.autopilot/runs.jsonl`; `xt.py loop stats [--json]`: số lần chạy mỗi task, tỉ lệ xanh lần đầu, task cần ≥ 3 lần, blocked/defer, vòng đã dùng; mục `LOOP-DESIGN-024` — Gate: `python3 -m unittest tests.test_xt_core tests.test_xt_cli`

### Lát C — máy trạng thái merge theo làn (D-038, ADR-0025)
- [x] `T-1103` `xt.py pr reviewed --pr N --head SHA (--clean|--blocking)` ghi sổ `.autopilot/reviews.json`; `xt.py pr next --pr N [--json]` trả một hành động theo 7 bước ADR-0024 (hàm thuần trên merge-check JSON + sổ review + trạng thái auto-merge) — Gate: `python3 -m unittest tests.test_merge`
- [x] `T-1104` Rút văn xuôi merge theo làn về `pr next` ở AGENTS.md §3, mẫu `AGENTS.md`, skill `/autopilot` bước 10/13, `LOOP-STOP-022`, `LOOP-DESIGN-020`; ADR-0025; CHANGELOG — Gate: `scripts/dev-task.sh gate`
