# ADR-0055: Preset chính sách cài đặt tùy chọn

- **Trạng thái:** Đã chấp nhận, D-219.
- **Ngày:** 2026-10-28.

## Bối cảnh và phương án

Dự án đích mới mặc định L3/auto/build theo ADR-0047. Nhóm muốn người duyệt merge cần tự sửa ba khóa;
đổi mặc định toàn bộ lại làm thay lựa chọn đã được chủ dự án chấp nhận. Cân nhắc (1) đổi mặc định,
(2) chỉ thêm hướng dẫn sửa tay, (3) preset tùy chọn có provenance và xem trước. Chọn 3.

## Quyết định

`install.py --preset safe|autonomous`: safe tạo `merge_autonomy: L1`, `merge_hard_exceptions: human`,
`delivery_phase: harden`; autonomous giữ chính sách mẫu hiện tại. Không truyền cờ giữ hành vi cũ.
Preset chỉ chọn lúc tạo xt.yaml mới; cài lại không chuyển chế độ dự án hoặc ghi đè tùy chỉnh, kể cả
khi truyền preset khác. Manifest giữ preset thực sự áp dụng; plan, template hash và cập nhật dùng
cùng lựa chọn để lần nâng sau không đổi ngầm safe về autonomous. Legacy giữ lựa chọn hiện có.
Nếu provenance mất/hỏng mà hash file cũ vẫn còn, không tự cập nhật ba khóa policy khác với file hiện có:
giữ `xt.yaml`, xuất `.xtemplates-new` cho phần đổi để chủ dự án đối chiếu. Plan và ghi thật cùng phân loại;
không suy preset từ nội dung dự án hoặc tạo provenance giả. Cập nhật không đổi policy vẫn tự động.

Tên safe chỉ diễn tả chính sách merge/review; không tạo sandbox, không giới hạn mạng hoặc bảo đảm an
toàn tuyệt đối. Dự án vẫn cần khai lệnh Gate thật và kiểm tra runtime trước khi chạy không người trực.

## Kiểm chứng và đường lùi

Kiểm cài mới/default, plan chỉ đọc, cài lại không cờ, cờ khác, tùy chỉnh và legacy/symlink. Không sửa
xt.yaml của repo khung. Revert cờ preset hoặc tiếp tục cài không cờ, cấu hình đang dùng vẫn được giữ.
