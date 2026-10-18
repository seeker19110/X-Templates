# ADR-0023: Bật auto-merge khi review sạch; không bật được thì merge trực tiếp ghim head — mọi PR

- **Trạng thái:** Đã chấp nhận
- **Trạng thái triển khai:** Đã triển khai — quy định ở `AGENTS.md` §3, `framework/templates/AGENTS.md`, skill `/autopilot`
  bước 10, `framework/11-autonomous-loop/README.md`, `LOOP-STOP-022`, `LOOP-DESIGN-020`, `WF-REVIEW-007`; không đổi code
  guard (`merge-check` vẫn quyết `merge`/`hard`; merge trực tiếp chỉ qua lệnh ghim head mà guard đã cho phép)
- **Ngày:** 2026-10-18
- **Làm rõ:** ADR-0015 ("mở PR là bật auto-merge") — quyết định D-029

## Bối cảnh

Chủ repo yêu cầu (2026-10-18): "bật auto-merge khi review sạch, không bật được thì tự merge, áp dụng cho cả dự án đích
sau này", rồi "áp luôn cho mọi PR". Ở PR #102, bốn vòng `reviewer` độc lập bắt được ba lỗ an ninh thật (tự cấp ủy quyền
production) trước khi merge; nếu bật auto-merge ngay khi mở PR như ADR-0015 thì PR đã merge từ vòng đầu.

## Quyết định

1. Mọi PR (mọi làn): mở PR → `reviewer` (model khác người viết) rà diff ở commit H (ghi H trong báo cáo). **Review sạch
   ở H** = báo cáo không còn lỗi chặn, mọi mục "nên sửa" đã sửa hoặc trả lời lý do. Mọi push sau H (kể cả push sửa mục
   "nên sửa") → rà lại diff H..head; head mới thành H.
2. Review sạch ở H, `merge-check` = `merge` với `head` = H, không có `hard` và không phải PR chồng → bật auto-merge của
   GitHub. Đã bật mà có push mới → tắt auto-merge, rà lại, chạy lại `merge-check`.
3. Không bật được (GitHub báo PR đã sẵn sàng — "clean status", hoặc repo tắt auto-merge) → merge trực tiếp bằng lệnh ghim
   head trong `next` của `merge-check` (`gh pr merge --match-head-commit` hoặc MCP `merge_pull_request` có
   `expectedHeadSha`) — chỉ khi sha trong `next` = H; `merge-check` = `wait` (CI còn chạy) thì chờ, không merge.
4. Còn lỗi chặn → sửa, đẩy, chờ CI, rà lại; không bật auto-merge giữa chừng.
5. PR `hard` vẫn do người merge (ADR-0016/0019/0020/0022).

## Lý do

- Chủ repo chọn rõ "mọi PR". Tiêu chí 1: review độc lập trước merge đã chứng minh giá trị ở #102.
- Lệnh `next` ghim head **tại lúc chạy `merge-check`**, không phải commit đã rà (review lần đầu của PR này bắt lỗi khẳng
  định ngược). Vì vậy quy trình buộc so `head` với H và rà lại khi khác; guard vẫn đòi `merge-check` = `merge`.

## Các phương án đã cân nhắc

- **Chỉ PR làn chuẩn chờ review, làn nhanh bật khi mở**: rẻ hơn nhưng chủ repo chọn mọi PR. Loại.
- **Giữ ADR-0015 (bật khi mở)**: PR tự merge trước khi review xong. Loại.

## Hệ quả

- Mỗi PR thêm một lượt `reviewer` (vài phút, tốn token); dồn việc nhỏ vào một lát hợp lý để giảm số PR.
- Auto-merge vẫn không ghim head: push thêm sau khi bật vẫn phải chạy lại `merge-check` (`LOOP-STOP-005`) và rà lại; job CI
  chạy `merge-check` là việc riêng (ADR-0022 "Giới hạn còn lại").
