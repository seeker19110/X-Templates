# ADR-0054: Không ghi state thiếu khóa, không thực thi với guard lỗi nạp

- **Trạng thái:** Đã chấp nhận, D-219.
- **Ngày:** 2026-10-28.
- **Làm rõ:** ADR-0052 §2 và ADR-0002; không sửa nội dung quyết định cũ.

## Bối cảnh

Kiểm revision rồi ghi state là hai bước riêng. Khi không có `fcntl` hoặc filesystem từ chối flock,
hai worker có thể cùng đọc revision và cùng thành công, mất một cập nhật. Tái hiện dùng barrier ngay
trước ghi; đối chứng Linux flock giữ đủ cập nhật. Ghi atomic chỉ tránh file dở, không thay cho khóa.

Hook Bash đã đóng khi guard không nạp được. CLI/Gate lại dùng module dở, hoặc cho qua khi cả fallback
không dùng được; module có hàm permissive được định nghĩa trước lỗi nạp vẫn có thể quyết định cho chạy.

## Các phương án

1. Tiếp tục không khóa, kiểm revision; dùng module guard dở để giữ tiến độ.
2. Khóa portable/SQLite và thay bộ máy state; chuẩn hóa mọi lỗi guard thành chặn.
3. Chặn ghi khi không có khóa thật; chặn lỗi nạp/fallback hỏng, giữ fallback runtime khỏe hiện hữu.

## Quyết định

Chọn 3: diff nhỏ, stdlib, không tạo cam kết khóa portable chưa kiểm chứng. Thiếu fcntl hoặc flock không
hỗ trợ → OSError rõ lý do, CLI exit 2; không gọi mutator, không ghi state. Đọc state vẫn được. Stop và
PreCompact hook giữ cơ chế cho dừng/compaction khi lỗi, kèm log; không giả cập nhật thành công.

Guard lỗi nạp trả trạng thái không dùng được; CLI/Gate chặn mã 126, không dùng định nghĩa từng phần.
Runtime guard lỗi nhưng `_failure_decision` khỏe giữ ADR-0002; fallback thiếu/lỗi → chặn. Dự án chưa
cài harness vẫn giữ tương thích; có harness thiếu guard đã thuộc đường chặn hiện có. Guard vẫn là lớp
giảm sai lầm; sandbox OS và egress mới là ranh giới cách ly, không được suy ra từ exit 0 của benchmark.
Nếu `apply_policy` lỗi hoặc thiếu, quyết định `ask` không được biến thành cho chạy ở chế độ mặc định;
chặn trường hợp đó. Quyết định cho/chặn rõ ràng từ guard cũ vẫn được giữ khi không có bộ chuyển policy.

## Kiểm chứng và đường lùi

Regression kiểm state không đổi và callback không được gọi; đối chứng flock và FLOW-07 không mất cập nhật.
Canary Gate không tạo khi guard hỏng; CLI đơn lẻ/stdin chặn, no-harness và fallback khỏe không lùi.
Revert từng lát nếu cần; không bỏ test hoặc hạ ngưỡng để hoàn tất cổng.
