# ADR-0079: Merge tự động theo check và ưu tiên PR nhỏ

- **Trạng thái:** Đã chấp nhận ngày 2026-11-14 (D-486).
- **Trạng thái triển khai:** Đang kiểm chứng qua PR.

## Bối cảnh

Chủ repo yêu cầu tự động merge khi các check xanh, ưu tiên PR nhỏ, không bắt buộc review. Ruleset hiện yêu cầu
`quality`, `protection-guard`, `dep-audit`, `gitleaks` và nhánh cập nhật với `main`.

## Phương án đã xét

1. Giữ review bắt buộc cho PR làn chuẩn. Cách này giữ quy trình cũ và làm PR xanh chờ review.
2. Mặc định review không bắt buộc, giữ check và sắp PR theo tổng dòng thêm, xoá. Dự án có thể chọn lại review bắt buộc.

## Quyết định và hệ quả

Chọn phương án 2 cho khung và dự án đích. Mặc định `merge_review: optional`; dự án cần review đặt `merge_review: required`. Steward xét mọi PR đang mở theo số dòng thay đổi,
hoà thì theo số PR. Các lượt steward dùng một nhóm concurrency, lịch chạy bù sự kiện bị thay thế. Máy tiếp tục đọc lại
head, kiểm check và merge ghim SHA. PR xung đột hoặc tụt base cần được đồng bộ và chạy CI lại. Ruleset giữ các check CI bắt buộc và bỏ yêu cầu xử lý luồng review. Khi không có `XT_STEWARD_TOKEN`, steward báo các nhánh tụt để cập nhật; token riêng kích lại các workflow PR.

Khôi phục cổng review bằng `merge_review: required` trên nhánh đích. Khôi phục concurrency qua PR riêng.
