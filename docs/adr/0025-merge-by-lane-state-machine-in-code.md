# ADR-0025: Máy trạng thái "merge theo làn" trong code — `xt.py pr next`

- **Trạng thái:** Đã chấp nhận
- **Trạng thái triển khai:** Đã triển khai — `scripts/xt.py` (`pr_next`, `cmd_pr`: `pr next`, `pr reviewed`, sổ
  `.autopilot/reviews.json`), test `tests/test_merge.py` `PrNextTest`, `PrNextCliTest`; văn xuôi rút gọn ở `AGENTS.md` §3,
  `framework/templates/AGENTS.md` §7, skill `/autopilot` bước 10/13, `framework/11-autonomous-loop/README.md`,
  `LOOP-STOP-022`, `LOOP-DESIGN-020`
- **Ngày:** 2026-10-18
- **Thay một phần:** ADR-0024 — cách thực thi (luật giữ nguyên, chuyển từ văn xuôi sang code); quyết định D-038

## Bối cảnh

ADR-0024 viết quy trình "merge theo làn" thành bảy bước văn xuôi có nhánh lồng (làn nhanh/chuẩn, head = H, tắt
auto-merge trước push, PR từng vào làn chuẩn, PR chồng, `hard`, GitHub báo PR đã sẵn sàng). Đoạn văn chép ở năm chỗ
(`AGENTS.md`, mẫu `AGENTS.md`, skill, `LOOP-STOP-022`, `LOOP-DESIGN-020`); mỗi lần đổi luật phải sửa cả năm (D-031 ghi
9 file). Model phải nhớ đúng bảy nhánh ở mọi sự kiện PR — loại lỗi thực thi mà harness sinh ra để loại bỏ.

## Quyết định

Lệnh `xt.py pr next --pr N [--json]` là hàm thuần (`pr_next`) trên ba đầu vào: quyết định của `merge-check` (dùng lại
đúng `_merge_eval`, không có luật thứ hai), PR đang bật auto-merge hay không (REST `auto_merge`), và sổ review của PR ở
`.autopilot/reviews.json`. Nó trả MỘT hành động — `done` · `closed` · `disable-auto-merge` · `defer-human` · `retarget` ·
`update` · `fix` · `review` · `enable-auto-merge` · `merge` (dưới L3: lệnh ghim head, không bao giờ bật auto-merge) · `wait` — kèm `do` (bước cụ thể) và `fallback` (merge ghim head khi
GitHub báo PR đã sẵn sàng). `xt.py pr reviewed --pr N --head <SHA đủ 40 ký tự> --clean|--blocking` ghi kết quả review
gắn với đúng commit đã rà. Lần đầu `pr next` thấy làn `chuẩn` thì ghi `standard_seen`, nên push sau đó không hạ PR về
làn nhanh. `pr next` **không gọi GitHub**: agent làm `do` qua `gh`/MCP, guard vẫn là lớp chặn (merge chỉ khi
`merge-check` = `merge` và ghim head). Văn xuôi các nơi rút về "chạy `pr next`, làm đúng `do`" và một câu tóm luật.

## Lý do

- Tiêu chí 1/3 (đúng, bền lâu, test được): bảng trạng thái có test cho cả bảy bước thay cho trí nhớ của model; một nhà
  cho luật (code + `LOOP-STOP-022`), các nơi khác chỉ trỏ tới.
- Không tự thực thi: giữ phiên chặn GraphQL dùng được (MCP), không cần token riêng, không trùng đường merge của guard.

## Các phương án đã cân nhắc

- **Lệnh tự bật/tắt auto-merge và merge**: trùng đường merge mà guard đang chặn, cần quyền ghi riêng. Loại.
- **Giữ văn xuôi, thêm checklist**: không giảm lỗi thực thi, vẫn chép năm nơi. Loại.

## Hệ quả

- Dự án đích cài khung trước bản này chưa có `pr next`: mẫu `AGENTS.md` nhắc chạy lại `install.py`.
- Sổ review nằm trong `.autopilot/` (cục bộ, gitignore): phiên mới không thấy review của phiên trước → `pr next` đòi rà
  lại cả PR nếu PR đang ở làn chuẩn. Giới hạn: `standard_seen` cũng cục bộ — PR từng ở làn chuẩn, sang phiên mới và nay
  ở làn nhanh (đã gỡ nhãn `risk:`, thu nhỏ diff) thì `pr next` coi là làn nhanh và cho bật auto-merge không rà. Chấp
  nhận vì làn hiện tại của PR do vị từ máy tính lại trên chính diff đó; lưu dấu làn chuẩn lên PR (nhãn) là việc sau nếu
  số đo cho thấy cần.
- Rủi ro còn lại của ADR-0024 giữ nguyên (auto-merge không ghim head); `pr next` trả `disable-auto-merge` ngay khi thấy
  head chưa được rà mà auto-merge còn bật, nên cửa sổ rủi ro chỉ còn giữa push và lần chạy `pr next` kế tiếp.
