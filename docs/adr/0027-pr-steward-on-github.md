# ADR-0027: PR steward chạy trên GitHub — PR đủ tiêu chuẩn vào nhánh chính không cần phiên agent

- **Trạng thái:** Đã chấp nhận
- **Trạng thái triển khai:** Đã triển khai — `scripts/xt.py` (`pr steward`, `pr reviewed` đăng kết quả lên PR,
  `published_reviews`, `with_published`), `.github/workflows/pr-steward.yml` (cài vào dự án đích bằng
  `install.py --with-github`), test `tests/test_merge.py` `PrStewardTest`, mục `LOOP-STOP-029`
- **Ngày:** 2026-10-19
- **Bổ sung:** ADR-0021 (merge-watch), ADR-0025 (`pr next`); quyết định D-054

## Bối cảnh

Chủ repo thấy PR đủ tiêu chuẩn mà không tự vào `main`. Nguyên nhân có ở ba chỗ, cùng một gốc: mọi bước merge theo làn
(ADR-0025) đều do một **phiên agent đang sống** làm.

1. Chỉ phiên chạy `pr next` mới bật auto-merge. Phiên dừng, container khởi động lại (tác vụ nền mất — đã gặp
   2026-10-19), hoặc PR do phiên khác mở thì không ai bật.
2. Sổ review `.autopilot/reviews.json` nằm trong container của phiên: khởi động lại là mất, phiên khác không đọc được,
   nên PR làn chuẩn đã review sạch vẫn hiện "cần review".
3. `merge-watch` (ADR-0021) chạy nền trong phiên — cũng chết theo phiên.

## Quyết định

1. **Sổ review dùng chung trên PR.** `xt.py pr reviewed` ngoài sổ cục bộ còn đăng một comment lên PR: một dòng cho
   người đọc và dấu máy đọc `<!-- xt-review v1 head=<SHA> verdict=clean|blocking -->`. Dấu không mang tên model (luật
   `ai_attribution`) — việc kiểm "reviewer khác model" vẫn làm trước khi ghi. `pr next` đọc thêm các dấu này
   (REST `issues/N/comments`), chỉ tin comment của `OWNER`/`COLLABORATOR` (`MEMBER` của org có thể chỉ có quyền đọc).
2. **`xt.py pr steward [--apply]`**: với mọi PR mở (hoặc `--pr`), chạy đúng `pr next` rồi tự làm phần máy làm được:
   `enable-auto-merge` (bật; GitHub báo PR đã sẵn sàng thì merge ghim head qua REST), `merge` (merge ghim head),
   `disable-auto-merge`. Việc cần người hoặc agent (`review`, `fix`, `update`, `retarget`, `defer-human`) chỉ báo trong
   bản tóm tắt của run. **Chỉ PR cùng repo của tác giả có quyền ghi** (`OWNER`/`COLLABORATOR`, hoặc Dependabot):
   PR từ fork hay của người ngoài → `defer-human` — người ngoài mở PR tài liệu làn nhanh không được tự vào nhánh chính
   khi không ai xem. PR từng vào làn chuẩn được gắn nhãn `xt-standard-lane` (thay `standard_seen` của sổ cục bộ, mà CI
   không có) nên thu nhỏ diff sau đó vẫn cần review sạch ở head.
3. **Workflow `pr-steward.yml`** chạy `pr steward --apply` mỗi 10 phút, khi có comment review (của người có quyền
   ghi), và khi chạy tay. Không trigger `pull_request*`, chỉ checkout nhánh mặc định — code của PR không chạy với quyền
   ghi. Token: `XT_STEWARD_TOKEN` nếu có (merge kích workflow `push` trên nhánh chính), không thì `GITHUB_TOKEN`.

Luật merge không đổi: steward dùng chính `pr next`/`merge-check`. Làn chuẩn vẫn cần review sạch ở đúng head; ngoại lệ
cứng (`hard`) vẫn để người; guard vẫn chặn agent. Phiên agent đang sống vẫn làm như ADR-0025 (nhanh hơn); steward là
lưới an toàn khi không còn phiên nào.

## Lý do

- **Phương án 2 — bật auto-merge cho mọi PR ngay khi mở:** bỏ qua review làn chuẩn (ADR-0024) — GitHub chỉ đợi
  required check, không biết review của agent.
- **Phương án 3 — dặn phiên đặt check-in hẹn giờ:** vẫn chết theo phiên/container; không xử lý PR của phiên khác.
- Steward chạy ở GitHub nên sống độc lập với phiên; dùng chung code với `pr next` nên không có luật thứ hai.

## Hệ quả

- Repo phải bật **Allow auto-merge** (Settings → General). Không bật: steward vẫn merge ghim head khi PR đã sẵn sàng.
- Merge bằng `GITHUB_TOKEN` không kích workflow `push` trên nhánh chính (GitHub chặn đệ quy) — muốn CI chạy sau merge
  thì đặt secret `XT_STEWARD_TOKEN` (fine-grained PAT hoặc GitHub App: contents + pull requests: write).
- Độ trễ tối đa ~10 phút (lịch của GitHub có thể chậm hơn khi tải cao); comment review kích ngay.
- Ai có quyền ghi repo cũng đăng được dấu review sạch, và gỡ được nhãn `xt-standard-lane` — cùng mức tin như sổ cục bộ
  (agent ghi). Người ngoài không được, và PR của họ không bao giờ được steward tự merge.
- PR chưa có review vẫn nằm chờ — đó là đúng luật; bản tóm tắt của run liệt kê để người/phiên sau xử lý.
