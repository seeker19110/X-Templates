# ADR-0073: `harness_permissions: own` giữ dạng lệnh hook sẵn có của dự án

- **Trạng thái:** Đã chấp nhận 2026-11-06 (phiên chính tự duyệt theo tiêu chí chất lượng cuối, ADR-0008 — **D-383**;
  AUD-HAR-301, hẹn ở D-375).
- **Trạng thái triển khai:** Đã triển khai — `scripts/install.py` `_absolute_form`, `settings_changes`; test
  `tests/test_install.py` `test_own_permissions_keeps_absolute_hook_form`,
  `test_own_permissions_keeps_project_permissions_and_relative_hooks`.
- **Ngày:** 2026-11-06.
- **Thay một phần:** giao ước khoá `harness_permissions: own` ở
  [`harness-files.md`](../../framework/11-autonomous-loop/harness-files.md) (dhcb, chủ repo 2026-10-22: lệnh hook khung
  luôn ghi dạng tương đối `bash .claude/hooks/x.sh`, kể cả khi dự án đang dùng dạng `${CLAUDE_PROJECT_DIR}`). **Giữ:**
  `own` không thêm `allow`/`deny` của khung; dự án chưa có lệnh hook khung nào (cài mới, `--force-harness`) → tương đối.

## Bối cảnh

Nâng xboss lên 3.30.0 (`own`, hook khung đang ở dạng `bash "${CLAUDE_PROJECT_DIR}/.claude/hooks/x.sh"`): `install.py
--plan` đổi 11 lệnh sang dạng tương đối. Dạng tương đối chỉ chạy khi phiên mở ở gốc repo; mở ở thư mục con thì hook không
tìm thấy script — với guard (`onFailure: block`) là chặn mọi lệnh Bash, với hook khác là mất hàng rào. Giao ước cũ viết cho
dhcb, dự án vốn dùng dạng tương đối; nó không có lý do để hạ cấp dự án đã dùng dạng tuyệt đối. 3.30.1 giữ giao ước và ghi
chú (D-375), hẹn quyết định ở 3.31.0.

## Phương án

1. **Theo dạng sẵn có của dự án**: có ít nhất một lệnh hook khung dạng `${CLAUDE_PROJECT_DIR}/.claude/hooks/…` → ghi lệnh
   khung dạng tuyệt đối; không có → tương đối (như cũ).
2. Khoá riêng (vd `harness_hook_form: absolute|relative`) — thêm bề mặt cấu hình cho một khác biệt máy tự đọc được.
3. Giữ giao ước, dự án cần dạng tuyệt đối thì không dùng `own` — buộc chọn giữa giữ quyền riêng và hook chạy đúng.

## Quyết định

Chọn **phương án 1**. Dạng tuyệt đối chạy ở mọi cwd nên không bao giờ là hạ cấp; dự án trộn hai dạng được đưa về tuyệt đối.
dhcb (chỉ có dạng tương đối) không đổi gì.

## Hệ quả

- Tốt: nâng bản không còn đổi hook tuyệt đối của dự án `own` sang dạng hỏng khi phiên mở ngoài gốc repo; không thêm khoá.
- Xấu: dự án `own` muốn chuyển từ tuyệt đối sang tương đối phải sửa tay một lần (gỡ mọi lệnh dạng `${CLAUDE_PROJECT_DIR}`);
  sau đó lần cài kế giữ dạng tương đối.
- Mốc xét lại: khi một dự án đích báo hook `own` sai dạng sau khi nâng.
