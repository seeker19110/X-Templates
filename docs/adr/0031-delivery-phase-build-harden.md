# ADR-0031: Pha giao hàng `delivery_phase: build|harden` — merge nhanh trước, review và audit sâu trước phát hành

- **Trạng thái:** Đã chấp nhận; Hệ quả "audit delta mỗi mốc" ở pha build thay bởi ADR-0033; mục "Ranh giới ngoại lệ cứng" (`hard_waived` vẫn cần review) và nhãn `risk:` ở pha build thay bởi ADR-0037 (reviewer chỉ ở pha harden); mục Hệ quả "Trước G7: đặt `harden` → audit delta → `release-check`" nay là nội dung của `/complete` (ADR-0046)
- **Trạng thái triển khai:** Đã triển khai trong repo — `scripts/xt.py` `delivery_phase`/`delivery_phase_error`/
  `review_deferrable`/`review_deferred`, `merge_eligibility` (`review: deferred`, `review_deferred`), `merge_check_result`, `pr_next`,
  `release_check` (hàng `phase`, `review_debt`), `doctor`/`ci-check`; mẫu `framework/templates/xt.yaml`
  (`delivery_phase: build`); test `tests/test_delivery_phase.py`, ca `pr-phase-*`/`review-phase-*` của
  `tests/fixtures/autonomy/`.
- **Ngày:** 2026-10-20
- **Làm rõ:** ADR-0016/0020 (ngoại lệ cứng), ADR-0024 (auto-merge sau review sạch), ADR-0025 (`pr next`), ADR-0028 (một
  điều kiện merge), ADR-0029 (chất lượng theo pha, `release-check`); nghiên cứu
  `research/2026-10-19-rapid-build-then-harden.md` §8 (PD-02, PD-04).

## Bối cảnh

Chủ repo yêu cầu quy trình autopilot ở dự án đích **code nhanh – merge nhanh, sau mới audit sâu và hoàn thiện**. Từ
ADR-0024/0028, mọi PR làn chuẩn (mọi PR có mã > 150 dòng, nhiều gói, đụng cấu hình cổng…) phải chờ một reviewer khác họ
model rà sạch đúng head mới được merge. Ở giai đoạn dựng sản phẩm (G6), phần lớn PR là làn chuẩn, nên mỗi lát chờ một
vòng review; review đầy đủ ở mỗi PR lặp lại việc mà audit delta theo mốc (ADR-0029) và audit toàn diện ở G7 vẫn làm.
`lifecycle.md` quy tắc 6 đã nói "nhanh ở G6, tin cậy ở G7" nhưng máy merge chưa có khái niệm pha. §8 của nghiên cứu
(PD-02) để `delivery_phase` chờ số; chủ repo quyết làm ngay, ở dạng tối thiểu: một khoá `xt.yaml`, không thêm trạng thái
vào state.

## Quyết định

1. **Khoá `delivery_phase: build|harden` trong `xt.yaml`.** Vắng/rỗng = `harden` (hành vi trước đây — dự án cũ không đổi).
   Mẫu dự án đích mới đặt `build`; repo khung khai tường minh `harden`. `xt.py doctor` (lỗi `xt-yaml`) và `ci-check` từ
   chối giá trị khác.
2. **Pha có hiệu lực khi CẢ nhánh đích đã commit LẪN cây làm việc đều `build`** (`delivery_phase`), như
   `pr_title_check`: PR không tự chuyển sang build cho chính nó; giá trị lạ → `harden` kèm ghi chú.
3. **Pha build, PR không thuộc ngoại lệ cứng** (`review_deferrable`): thiếu review ở head (`missing`, kể cả review
   `inconclusive` hay sạch ở head cũ) thành `review: deferred` — hợp lệ cho `eligible`/`auto_merge_ok` (ADR-0028), nên
   `merge-check --json` có `review_deferred: true`, `merge-gate` xanh, guard cho bật auto-merge/merge ghim head, steward
   xử lý như PR đã rà. Điều kiện còn lại không đổi: CI xanh, không xung đột, không tụt sau, verdict `merge` của
   `merge_decision`. `pr next` đi thẳng tới bật auto-merge/merge và ghi "pha build: bỏ qua review, ghi nợ (ADR-0031)".
4. **Review `blocking` chặn ở mọi pha — kể cả ở head cũ; nhãn `risk:` cũng giữ review.** Review đã đăng báo lỗi chặn ở
   head thì PR phải sửa như cũ. Ở pha build, `missing` chỉ thành `deferred` (`review_deferred`) khi review KẾT LUẬN mới
   nhất của PR, bất kể head, không phải `blocking`: nếu không, một lần push đổi head sẽ "rửa" lỗi chặn thành nợ — nên
   review `blocking` ở head cũ mà chưa có review sạch sau nó giữ `missing` (cần review lại head hiện tại); review
   `inconclusive` không gỡ lỗi chặn trước nó; chưa từng có review, chỉ có review `inconclusive`, hay review gần nhất sạch
   ở head cũ thì vẫn hoãn. PR mang nhãn `risk:` bất kỳ (`risk_labels` của `merge_decision`) cũng giữ `missing`: ADR-0025
   dùng gắn nhãn `risk:` làm phanh thủ công, nên pha build không được bỏ qua nó (cách hiểu chặt, AGENTS.md §4 tiêu chí 1).
5. **Nợ review có hạn — trả trước G7.** PR merge ở pha build không có review sạch là nợ review; không thêm sổ mới:
   `xt.py release-check` thêm hai hàng BLOCKER — `phase` FAIL khi `delivery_phase: build` (hay giá trị lạ): "đặt
   `delivery_phase: harden` rồi chạy audit delta"; `review_debt` FAIL khi có file ngoài tài liệu (`DOC_PATH_RE`) đổi sau
   SHA quét của sổ audit mà chưa được phủ — file thuộc nhóm audit nào (`_path_groups`) so với SHA của nhóm đó, file không
   thuộc nhóm nào (cấu hình cổng như `ruff.toml`) so với SHA quét mới nhất. Sổ vắng/không đọc được hay không có nhóm đã
   quét → `N/A` (hàng `audit` đã chặn — một vấn đề một hàng).

## Ranh giới ngoại lệ cứng

Pha không chạm ngoại lệ cứng (tiền, dữ liệu người dùng thật, auth, mật mã, bí mật — `merge_hard_reasons`, `LOOP-STOP-005`):
`hard` vẫn tính như cũ, guard không đổi, người merge khi `merge_hard_exceptions: human`. Khi `merge_hard_exceptions: auto`
(ADR-0020) miễn người merge, PR đó (`hard_waived`) **vẫn cần review sạch ở head** ở pha build — miễn người merge không
phải miễn review; cách hiểu chặt hơn với bảo mật (AGENTS.md §4 tiêu chí 1).

## Lý do

- Một khoá phẳng trong `xt.yaml` thay vì biến trong state: không migration, đọc ở nhánh đích như các khoá merge khác,
  agent không tự đổi được bằng sửa tại chỗ.
- Hoãn review chứ không bỏ: nợ được đo bằng chính sổ audit đã có (SHA quét + `audit plan`), G7 không qua được khi còn nợ.
- Giữ một nhà cho điều kiện merge (ADR-0028): pha chỉ thêm một trạng thái của `merge_eligibility`, mọi lối đọc cùng kết quả.

## Hệ quả

- Dự án đích mới (mẫu `xt.yaml`) chạy ở build: PR làn chuẩn merge khi CI xanh; reviewer vẫn được giao khi phiên chính
  chọn, nhưng không chặn merge. Dự án cũ chạy lại `install.py` nhận `xt.py` mới; `xt.yaml` copy-if-absent — tự thêm
  `delivery_phase: build` nếu muốn.
- Chất lượng ở pha build dựa vào cổng commit/CI (sàn máy G5), audit delta mỗi mốc (ADR-0029) và audit toàn diện ở G7.
- Trước G7: đặt `delivery_phase: harden` (PR làn chuẩn từ đó lại cần review sạch), chạy audit delta theo
  `xt.py audit plan --status docs/ops/AUDIT-STATUS.md`, cập nhật sổ, rồi `xt.py release-check`.

## Đường lùi

Đặt `delivery_phase: harden` (hoặc xoá khoá) — merge trở lại đúng ADR-0024/0028 ngay ở PR kế. Revert commit gỡ hẳn
cơ chế; không có dữ liệu/trạng thái mới cần dọn.
