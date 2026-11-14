# PLAN harden X-Templates 2026-11-14

- D-490 chọn xử lý mục đỏ đã có bằng chứng trước, giữ G7 làm cổng phát hành.
- Mốc audit `e0745c07`. Sổ: 16 🔴 và 47 🟠 còn mở, TEST/HAR chưa quét đủ. Blueprint không có MUST mở; sàn M/L không áp dụng cho khung quy mô S.
- Phạm vi đợt đầu: lỗi bảo toàn GO-NO-GO khi formatter gặp lỗi I/O, sau đó đồng bộ hướng dẫn merge và hoàn tất rà delta có bằng chứng. Các phát hiện mở tiếp tục theo sổ và PLAN harden 2026-11-11.
- G7 lần 1 tại `e0745c07` trả NO-GO: `audit` 159 lỗi, `review_debt` 10 tệp, `verify` thiếu dấu vân tay. Blueprint chạy đủ 68 lệnh xanh.
- Chỉ chuẩn bị ký khi G7 đạt. Pha harden giữ nguyên, dự án đích tạm dừng.

## Ngân sách
- Hạn: 24 giờ · Chi phí ngoài phiên: 0 · Timeout Gate: 1200 giây.

## Task
- [x] `T-3890` 🔴 AUD-SEC-648: bảo toàn GO-NO-GO khi lỗi I/O tại điểm vào formatter — Gate: `python3 -m unittest tests.test_hooks.DevTaskTest`
- [ ] `T-3891` Đồng bộ hướng dẫn harden/merge với ADR-0079 — Gate: `python3 scripts/xt.py validate && python3 scripts/check-links.py`
- [ ] `T-3892` Trả nợ audit và xác nhận các phát hiện còn mở theo sổ — Gate: `python3 scripts/xt.py audit check docs/ops/AUDIT-STATUS.md --strict`
Sau `loop verify --all`, chạy `release-check` trên ứng viên phát hành.
