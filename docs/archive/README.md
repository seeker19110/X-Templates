# Kho lịch sử của repo khung

> Lịch sử của **chính repo X-Templates**: PLAN đã đóng, báo cáo audit, GO-NO-GO và ghi chép đo đạc cũ — dời khỏi
> `docs/autopilot/` và `docs/ops/` theo [ADR-0070](../adr/0070-archive-repo-history.md) (D-354). Nội dung giữ nguyên văn,
> đúng tại thời điểm viết; luật hiện hành ở `framework/`, quyết định ở `docs/adr/` và `docs/autopilot/DECISIONS*.md`.
> Không cài sang dự án đích. Tìm kiếm mặc định bỏ qua thư mục này (`.ignore`); truy vết thì tìm đích danh
> (`rg <mẫu> docs/archive/`).

| Thư mục | Nội dung | Còn được máy đọc |
|---|---|---|
| [`autopilot/`](autopilot/) | PLAN không còn task mở | `xt.py` quét `PLAN*.md` ở đây khi cấp số task mới — `T-NNN` không tái sử dụng |
| [`ops/`](ops/) | Báo cáo audit, GO-NO-GO các bản cũ, ghi chép đo CI/mutation/tối ưu | Không |

Dời thêm: chỉ PLAN đã đóng và không được `PROGRESS.md` nhắc; giữ tại chỗ báo cáo audit đầy đủ và delta gần nhất, GO-NO-GO của
`VERSION` hiện hành, file mà công cụ đọc. Dùng `git mv`, viết lại liên kết, `check-links` xanh, ghi D-NNN.
