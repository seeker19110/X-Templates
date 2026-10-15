# ADR-0008: Phiên chính tự duyệt điểm quyết định theo tiêu chí chất lượng cuối; mặc định tự host

- **Trạng thái:** Đã chấp nhận
- **Trạng thái triển khai:** Đã triển khai (`scripts/xt.py loop decide`; test `tests/test_xt_cli.py` `LoopCommandsTest.test_decide_*`;
  `framework/11-autonomous-loop/stop-points-and-escalation.md` `LOOP-STOP-018`…`020`; `AGENTS.md` §4–5;
  `framework/templates/AGENTS.md` §5–6)
- **Ngày:** 2026-10-15

## Bối cảnh

Chủ repo yêu cầu (2026-10-15), áp cho cả repo khung lẫn dự án đích:

1. "Khi cần quyết định, phiên chính được tự duyệt theo tiêu chí làm sao chất lượng sản phẩm sau này hoàn thành được
   chất lượng cao nhất."
2. "Để giảm tải phải hỏi và yêu cầu cung cấp thông tin từ chủ dự án, luôn chọn tự host tất cả và ghi đề xuất chuyển sang
   các dịch vụ khác khi chạy thật."

Trước ADR này, khung gộp hai loại "điểm dừng" vào một danh sách (AGENTS.md §4, `LOOP-STOP-004`, `WF-SDD-004`,
`PM-SPEC-007`, `PM-REQ-008`, cổng duyệt PLAN của autopilot): (a) **lựa chọn chuyên môn** — cách hiểu spec, công nghệ,
thiết kế, phạm vi; (b) **hành động** lên thế giới thật hoặc nới hàng rào — xoá, tiền, dữ liệu thật, deploy, đổi quyền.
Cả hai đều dừng chờ người, nên vòng lặp tự động đứng ở những câu hỏi mà agent trả lời được bằng dữ kiện trong repo.

## Quyết định

1. **Tách hai loại.** Điểm quyết định chuyên môn → **phiên chính** tự duyệt, không `loop block`, không chờ. Điểm dừng
   về hành động giữ nguyên (hook `ask`/`deny` vẫn cưỡng chế; ADR-0002 không đổi), thêm "đăng ký dịch vụ trả phí/nhập khoá
   thật" và "bế tắc máy".
2. **Tiêu chí chất lượng cuối**, xét theo thứ tự (thắng ở tiêu chí trên thì thắng, không cộng điểm): (1) đúng và an toàn
   — cách hiểu chặt hơn với bảo mật/dữ liệu/pháp lý · (2) giữ đường lùi khi thiếu dữ kiện chỉ người có · (3) bền lâu ·
   (4) trải nghiệm cuối · (5) tốc độ/chi phí chỉ để phá hoà.
3. **Mặc định tự host**: phương án cần tài khoản/khoá/thông tin chỉ chủ dự án có → chọn phương án tự host chạy được trong
   repo (giấy phép OSI; dịch vụ bắt buộc bên ngoài → adapter giả + contract test); đề xuất dịch vụ cho lúc chạy thật ghi
   `--prod`, chủ dự án quyết ở G7 (`GO-NO-GO.md` mục 18 là BLOCKER).
4. **Mọi quyết định có dấu vết máy**: `xt.py loop decide` ghi `D-NNN` vào `docs/autopilot/DECISIONS.md` (commit cùng thay
   đổi) — đòi ≥ 2 phương án khác nhau, lựa chọn khớp một phương án, lý do, đường lùi; trường gộp một dòng để không chèn
   được tiêu đề giả. Người đổi ý → quyết định mới "thay D-NNN".
5. **Chỉ phiên chính** tự duyệt; subagent (`executor`) trả phương án + dữ kiện về, không tự chọn.
6. ID cũ đổi nghĩa → `MAY` Ngừng dùng, ID mới thay: `LOOP-STOP-004` → `LOOP-STOP-018`; `PM-SPEC-007` → `PM-SPEC-020`;
   `PM-REQ-008` → `PM-REQ-019`; `WF-SDD-004` gộp vào `PM-SPEC-020` (một chủ đề một nhà). Mới: `LOOP-STOP-019` (báo cáo
   liệt kê D-NNN), `LOOP-STOP-020` (mặc định tự host).

## Lý do

- Câu hỏi chuyên môn dừng chờ người không làm sản phẩm tốt hơn khi agent có đủ dữ kiện; nó chỉ làm vòng lặp đứng. Rủi ro
  thật của tự động hoá nằm ở **hành động** (không đảo ngược, ra ngoài) — phần đó vẫn có người.
- Lỗi mà luật cũ chống ("agent tự lấp spec hở ngầm") vẫn bị chặn: lựa chọn phải tường minh, có phương án thay thế, có
  đường lùi, người xem lại được — khác với đoán im lặng.
- Thứ tự tiêu chí đặt "đúng và an toàn" và "giữ đường lùi" trước tốc độ: khi đoán sai ý định, chi phí sửa nhỏ.
- Tự host loại bỏ lý do phổ biến nhất phải hỏi chủ dự án giữa chừng (khoá API, tài khoản cloud, thẻ thanh toán), giữ dữ
  liệu trong nước khi phát triển (`CMP-VN-004`), và trì hoãn cam kết nhà cung cấp tới lúc có số liệu thật.

## Các phương án đã cân nhắc

- **Giữ nguyên, chỉ thêm cờ `--auto-approve` tuỳ chọn**: không đáp ứng yêu cầu (mặc định vẫn hỏi). Loại.
- **Tự duyệt cả hành động** (deploy, xoá, tiền): trái ADR-0002 (đặc quyền tách bằng code); một quyết định sai không đảo
  ngược được thì "chất lượng cuối" không cứu được. Loại.
- **Chỉ ghi quyết định vào PROGRESS.md**: PROGRESS bị viết lại mỗi phiên, giới hạn 8 KB — mất dấu vết. Loại; dùng file
  riêng chỉ thêm dòng.
- **Viết lại nghĩa của ID cũ**: dự án đích đã tick theo nghĩa cũ sẽ mang trạng thái sai. Loại; ngừng dùng + ID mới.
- **Mặc định dịch vụ quản lý (SaaS/cloud)**: chất lượng vận hành có thể cao hơn ở production nhưng buộc hỏi tài khoản/khoá
  từ đầu và khoá nhà cung cấp sớm. Giữ làm đề xuất `--prod`, quyết ở G7.

## Hệ quả

- Tốt: autopilot không còn đứng ở câu hỏi chuyên môn; người có một nơi (`DECISIONS.md`) để xem lại mọi lựa chọn và danh
  sách việc cần quyết khi lên production.
- Xấu/nợ: agent có thể chọn sai ý định kinh doanh — giảm bằng tiêu chí (2) và báo cáo cuối liệt kê D-NNN; tự host làm tăng
  việc vận hành nếu chủ dự án giữ nguyên ở production (GO-NO-GO mục 18 buộc quyết tường minh). Chưa có máy kiểm rằng
  `blocked_reason` không phải câu hỏi chuyên môn — kiểm bằng review.
- Dự án đích: chạy lại `install.py` (AGENTS.md là copy-if-absent → bản mới ở `*.xtemplates-new`, gộp tay §5–6) và
  `compose --out BLUEPRINT.md` (trạng thái giữ theo ID; đánh giá các ID mới).
