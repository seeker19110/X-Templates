# ADR-0026: Ghi/xoá tay `.autopilot/` bị chặn, không chỉ "hỏi"

- **Trạng thái:** Đã chấp nhận
- **Trạng thái triển khai:** Đã triển khai — `.claude/hooks/guard.py` (`DANGER_MARKERS` thêm "tay bằng chứng"; `edit_decision`
  và `_write_asks` vốn đã nhận diện `.autopilot/` là `evidence`), test `tests/test_hooks.py`; danh sách chặn trong
  `CLAUDE.md` và `framework/templates/CLAUDE.md`
- **Ngày:** 2026-10-18
- **Thay một phần:** ADR-0018 — riêng mục "ghi tay `.autopilot/`" chuyển từ nhóm *cho chạy* sang nhóm *máy chặn*

## Bối cảnh

ADR-0018 chỉ chặn việc nguy hiểm/không đảo ngược; các `ask` khác được cho qua. Guard đã nhận diện ghi vào `.autopilot/`
(bằng chứng `evidence/T-xxx.json`, `verified.json` của kiểm lại cuối, `runs.jsonl`, `state.json`, sổ review `reviews.json`)
từ AUD-HAR-024, nhưng chỉ trả `ask` — dưới chính sách mặc định thành cho qua. Vậy agent viết được `verified.json` xanh hay
review sạch mà không chạy Gate/không có reviewer: đúng thứ P1 "bằng chứng, không lời khai" cấm, và lớp đỡ duy nhất của
Stop hook (`final_check`) đọc chính các file đó. Rà autopilot 2026-10-18 xếp đây là lỗ nghiêm trọng thứ hai.

## Quyết định

Ghi/xoá `.autopilot/` qua Edit/Write hoặc Bash (chuyển hướng, `tee`, `cp`/`mv`, `rm`, `find -delete`/`-exec rm`, `sed -i`…) bị **chặn** ở chính sách mặc
định: thêm dấu "tay bằng chứng" vào `DANGER_MARKERS`. Chỉ `xt.py` (chạy như một lệnh, guard không thấy file nó ghi) được
ghi. Cần sửa tay (gỡ vòng hỏng) thì người làm, hoặc `xt.py loop init --force`.

## Hệ quả

- Giả mạo bằng chứng phải đi đường vòng có chủ ý (`python3 -c` ghi file — giới hạn đã biết của quét chuỗi, review và
  `loop verify` chạy lại Gate là lớp sau), không còn là một lệnh `echo … > .autopilot/verified.json`.
- Agent không tự xoá `.autopilot/` để "làm lại từ đầu" được nữa; dùng `loop init --force`.
- `XT_GUARD_POLICY=strict` không đổi (vẫn hỏi).
