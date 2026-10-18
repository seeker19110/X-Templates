# ADR-0024: Bật auto-merge khi review sạch; không bật được thì merge trực tiếp ghim head — mọi PR

- **Trạng thái:** Đã chấp nhận
- **Trạng thái triển khai:** Đã triển khai — quy định ở `AGENTS.md` §3, `framework/templates/AGENTS.md`, skill `/autopilot`
  bước 10, `framework/11-autonomous-loop/README.md`, `LOOP-STOP-022`, `LOOP-DESIGN-020`, `WF-REVIEW-007`; không đổi code
  guard (`merge-check` vẫn quyết `merge`/`hard`; merge trực tiếp chỉ qua lệnh ghim head mà guard đã cho phép)
- **Ngày:** 2026-10-18
- **Thay một phần:** ADR-0015 — thời điểm bật auto-merge ("mở PR là bật auto-merge"); quyết định D-030

## Bối cảnh

Chủ repo yêu cầu (2026-10-18): "bật auto-merge khi review sạch, không bật được thì tự merge, áp dụng cho cả dự án đích
sau này", rồi "áp luôn cho mọi PR". Ở PR #102, bốn vòng `reviewer` độc lập bắt được ba lỗ an ninh thật (tự cấp ủy quyền
production) trước khi merge; nếu bật auto-merge ngay khi mở PR như ADR-0015 thì PR đã merge từ vòng đầu.

## Quyết định

Mọi PR (mọi làn): (1) mở PR → chạy nền `merge-watch`; `reviewer` (model khác người viết) rà diff ở commit H, ghi H trong báo cáo.

(2) **review sạch ở H** = không còn lỗi chặn, mọi mục "nên sửa" đã sửa hoặc trả lời lý do.

(3) cần push sau H (sửa mục nên sửa, sửa CI, merge nhánh đích): PR đang bật auto-merge thì **tắt auto-merge TRƯỚC khi push** (`gh pr merge <N> --disable-auto`/MCP `disable_pr_auto_merge`), push, rà lại diff H..head (push chỉ là merge nhánh đích thì rà phần giải xung đột: `git show --remerge-diff`), head mới thành H.

(4) review sạch ở H và `merge-check` có `head` = H, không `hard`, không phải PR chồng, verdict `wait` (CI còn chạy — ca thường) hoặc `merge` → bật auto-merge (`gh pr merge <N> --auto --squash`/MCP `enable_pr_auto_merge`).

(5) không bật được — GitHub báo PR đã "clean status" (CI đã xanh, verdict `merge`) hoặc repo tắt auto-merge — thì khi verdict `merge` chạy đúng lệnh `next` (ghim `--match-head-commit H`/MCP `expectedHeadSha` H), khi `wait` thì chờ `merge-watch` rồi chạy lại `merge-check`.

(6) `merge-watch` thoát 0 trước khi review sạch → chưa làm gì, review sạch xong chạy lại `merge-check` rồi làm (4)/(5).

(7) `hard` → người merge (`loop defer`; job CI `merge-gate` đỏ khi PR `hard` đang bật auto-merge — ADR-0023); còn lỗi chặn → sửa theo (3), rà lại.

## Lý do

- Chủ repo chọn rõ "mọi PR". Tiêu chí 1: review độc lập trước merge đã chứng minh giá trị ở #102.
- Lệnh `next` ghim head **tại lúc chạy `merge-check`**, không phải commit đã rà (review lần đầu của PR này bắt lỗi khẳng
  định ngược). Vì vậy quy trình buộc so `head` với H và rà lại khi khác; guard vẫn đòi `merge-check` = `merge`.

## Các phương án đã cân nhắc

- **Chỉ PR làn chuẩn chờ review, làn nhanh bật khi mở**: rẻ hơn nhưng chủ repo chọn mọi PR. Loại.
- **Giữ ADR-0015 (bật khi mở)**: PR tự merge trước khi review xong. Loại.

## Hệ quả

- Mỗi PR thêm một lượt `reviewer` (vài phút, tốn token); dồn việc nhỏ vào một lát hợp lý để giảm số PR.
- Auto-merge không ghim head (`gh pr merge --auto` không nhận head): vì vậy bước (3) tắt auto-merge TRƯỚC mỗi push; PR
  `hard` còn có job CI `merge-gate` đỏ khi đang bật auto-merge (ADR-0023).
