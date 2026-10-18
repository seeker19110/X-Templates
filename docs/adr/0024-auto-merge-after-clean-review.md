# ADR-0024: Merge theo làn — PR quan trọng review sạch rồi bật auto-merge, PR khác bật khi mở

- **Trạng thái:** Đã chấp nhận — cách thực thi bị thay một phần bởi ADR-0025 (`xt.py pr next`; luật giữ nguyên)
- **Trạng thái triển khai:** Đã triển khai — quy định ở `AGENTS.md` §3, `framework/templates/AGENTS.md`, skill `/autopilot`
  bước 10, `framework/11-autonomous-loop/README.md`, `LOOP-STOP-022`, `LOOP-DESIGN-020`, `WF-REVIEW-007`; không đổi code
  guard (`merge-check` vẫn quyết `merge`/`hard`; merge trực tiếp chỉ qua lệnh ghim head mà guard đã cho phép)
- **Ngày:** 2026-10-18
- **Thay một phần:** ADR-0015 — thời điểm bật auto-merge ("mở PR là bật auto-merge"); quyết định D-030, D-031

## Bối cảnh

Chủ repo yêu cầu (2026-10-18): "bật auto-merge khi review sạch, không bật được thì tự merge, áp dụng cho cả dự án đích
sau này", rồi "áp luôn cho mọi PR"; cùng ngày đổi lại: "chỉ review lại trước những PR quan trọng, rồi sau đó tạo PR auto
merge, còn lại bật auto merge tự động". Ở PR #102, bốn vòng `reviewer` độc lập bắt được ba lỗ an ninh thật (tự cấp ủy quyền
production) trước khi merge; nếu bật auto-merge ngay khi mở PR như ADR-0015 thì PR đã merge từ vòng đầu.

## Quyết định

(1) mở PR → chạy nền `merge-watch`, chạy `merge-check`: `hard` → (7); PR chồng → chưa bật, đổi đích về nhánh mặc định rồi xử lý theo làn như PR mới mở; làn `nhanh` → **bật auto-merge ngay** (`gh pr merge <N> --auto --squash`/MCP `enable_pr_auto_merge`), không chờ review; làn `chuẩn` = **PR quan trọng** (đường dẫn nhạy cảm cổng/CI/hook/schema/phụ thuộc, nhãn `risk:`, > 150 dòng, nhiều gói, đổi mã không đổi test — vị từ `LOOP-STOP-009`) → chưa bật, `reviewer` (model khác người viết) rà diff ở commit H, ghi H trong báo cáo.

(2) **review sạch ở H** = không còn lỗi chặn, mọi mục "nên sửa" đã sửa hoặc trả lời lý do.

(3) cần push (sửa mục nên sửa, sửa CI, merge nhánh đích) hoặc gắn nhãn `risk:`: PR đang bật auto-merge thì **tắt auto-merge TRƯỚC khi push/gắn nhãn** (`gh pr merge <N> --disable-auto`/MCP `disable_pr_auto_merge`), push/gắn nhãn, chạy lại `merge-check`: vẫn làn `nhanh` → bật lại (trừ PR đã từng vào làn `chuẩn` hoặc đã có review báo lỗi chặn: chỉ bật khi review sạch ở head, bất kể làn hiện tại); làn `chuẩn` → rà diff H..head (chưa rà lần nào thì rà cả PR; push chỉ là merge nhánh đích thì rà phần giải xung đột: `git show --remerge-diff`), head mới thành H.

(4) làn `chuẩn`: review sạch ở H và `merge-check` có `head` = H, không `hard`, không phải PR chồng, verdict `wait` (CI còn chạy — ca thường) hoặc `merge` → bật auto-merge.

(5) không bật được — GitHub báo PR đã "clean status" (CI đã xanh, verdict `merge`) hoặc repo tắt auto-merge — thì khi verdict `merge` chạy đúng lệnh `next` (ghim head `--match-head-commit`/MCP `expectedHeadSha`; làn `chuẩn` chỉ khi head = H), khi `wait` thì chờ `merge-watch` rồi chạy lại `merge-check`.

(6) làn `chuẩn`: `merge-watch` thoát 0 trước khi review sạch → chưa làm gì, review sạch xong chạy lại `merge-check` rồi làm (4)/(5).

(7) `hard` → người merge (`loop defer`; job CI `merge-gate` đỏ khi PR `hard` đang bật auto-merge — ADR-0023); còn lỗi chặn → sửa theo (3), rà lại.

## Lý do

- Chủ repo chọn rõ: review trước chỉ cho PR quan trọng. "Quan trọng" = làn `chuẩn` của `merge-check` (D-031): vị từ
  máy có sẵn, test được, bắt rộng có chủ đích (báo oan chỉ tốn một lượt review). Vị từ chung không coi `scripts/xt.py`
  của repo khung là nhạy cảm (ở dự án đích nó nằm trong `.xtemplates/`, đã là cổng/CI): repo khung khai
  `merge_risk_paths` (`scripts/*`, `framework/11-autonomous-loop/*`, `framework/10-workflow/code-review.md`, `framework/templates/*`, `docs/adr/*`) để PR nhỏ
  sửa bộ máy merge/ủy quyền hay luật vòng tự động — loại lỗ #102 bắt được — vẫn phải review. PR nhỏ một gói, có test, không chạm vùng nhạy cảm bật auto-merge khi mở như ADR-0015.
- Lệnh `next` ghim head **tại lúc chạy `merge-check`**, không phải commit đã rà (review lần đầu của PR này bắt lỗi khẳng
  định ngược). Vì vậy quy trình buộc so `head` với H và rà lại khi khác; guard vẫn đòi `merge-check` = `merge`.

## Các phương án đã cân nhắc

- **Mọi PR chờ review** (D-030): chậm và tốn mọi PR nhỏ; chủ repo đổi sang chỉ PR quan trọng. Loại.
- **Agent tự phán đoán PR nào quan trọng**: không kiểm được. **Chỉ PR `hard`**: bỏ sót sửa guard/CI. Loại.
- **Giữ ADR-0015 (bật khi mở)**: PR tự merge trước khi review xong. Loại.

## Hệ quả

- Mỗi PR làn chuẩn thêm một lượt `reviewer` (vài phút, tốn token); PR làn nhanh merge ngay khi CI xanh.
- Push vào PR làn nhanh có thể đổi nó sang làn chuẩn: vì vậy (3) tắt auto-merge trước push và chạy lại `merge-check`.
- Auto-merge không ghim head (`gh pr merge --auto` không nhận head): vì vậy bước (3) tắt auto-merge TRƯỚC mỗi push; PR
  `hard` còn có job CI `merge-gate` đỏ khi đang bật auto-merge (ADR-0023).
- Rủi ro còn lại: lỡ push vào PR làn nhanh khi auto-merge còn bật (trái bước (3)) mà push đó đẩy PR sang làn chuẩn, CI
  xanh trước khi agent tắt → GitHub merge head chưa rà; `merge-gate` chỉ chặn `hard`. Đỡ bằng kỷ luật bước (3).
- Dự án đích muốn PR nhỏ ở vùng riêng (ví dụ xuất dữ liệu khách — PII chỉ nhận qua nhãn `risk:pii`) luôn được review thì
  khai `merge_risk_paths`.
