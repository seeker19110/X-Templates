# Nhật ký quyết định tự duyệt

> Ghi bởi `xt.py loop decide`. Phiên chính tự duyệt điểm quyết định theo tiêu chí chất lượng cuối (`LOOP-STOP-018`, ADR-0008 của khung). Người xem lại bất cứ lúc nào; đổi ý → quyết định mới ghi "thay D-NNN", không sửa mục cũ.

### D-001 · 2026-10-15T14:17:22+00:00 · Phạm vi tự duyệt của phiên chính (ADR-0008)

- Phương án: (1) Tự duyệt cả quyết định chuyên môn lẫn hành động (deploy, xoá, tiền) · (2) Chỉ quyết định chuyên môn; hành động giữ điểm dừng có hook
- Chọn: Chỉ quyết định chuyên môn; hành động giữ điểm dừng có hook
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1 (đúng và an toàn): hành động không đảo ngược thì chất lượng cuối không cứu được; hook ask/deny của ADR-0002 vẫn cưỡng chế. Tiêu chí 2: lựa chọn chuyên môn sửa được, có D-NNN để xem lại.
- Đường lùi: ADR mới nới/thu hẹp danh sách điểm quyết định trong stop-points-and-escalation.md

### D-002 · 2026-10-15T14:17:22+00:00 · Mục checklist cũ đổi nghĩa (LOOP-STOP-004, PM-SPEC-007, PM-REQ-008, WF-SDD-004)

- Phương án: (1) Viết lại nội dung giữ ID · (2) MAY Ngừng dùng + ID mới (WF-SDD-004 gộp vào PM-SPEC-020)
- Chọn: MAY Ngừng dùng + ID mới (WF-SDD-004 gộp vào PM-SPEC-020)
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1: dự án đích đã tick theo nghĩa cũ sẽ mang trạng thái sai nếu viết lại; conventions.md cấm tái sử dụng nghĩa ID. Tiêu chí 3: gộp trùng chủ đề spec hở về một nhà.
- Đường lùi: Đổi mức các ID mới về MAY Ngừng dùng và trỏ lại ID cũ (không xoá ID)

### D-003 · 2026-10-15T14:17:22+00:00 · Nơi ghi dấu vết quyết định tự duyệt

- Phương án: (1) Mục Quyết định của PROGRESS.md · (2) File riêng docs/autopilot/DECISIONS.md, ghi bằng xt.py loop decide có kiểm đầu vào
- Chọn: File riêng docs/autopilot/DECISIONS.md, ghi bằng xt.py loop decide có kiểm đầu vào
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1/3: PROGRESS bị viết lại mỗi phiên và giới hạn 8 KB nên mất dấu vết; lệnh máy buộc ≥ 2 phương án, lý do, đường lùi (P1 bằng chứng).
- Đường lùi: --log trỏ file khác; file là Markdown thuần, chuyển tay được
