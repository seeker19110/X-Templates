# ADR-0020: Chủ dự án tắt được chốt người của ngoại lệ cứng (`merge_hard_exceptions: auto`)

- **Trạng thái:** Đã chấp nhận — cách nhận diện "PR chạm khoá" (§2) đổi từ dò chuỗi trong patch sang so giá trị đã
  parse ở đáy/đầu PR (D-032, 2026-10-18), rồi so danh sách mọi dòng khoá ở merge-base/đầu PR (D-033; CHANGELOG); vế "bật auto-merge" trong cơ chế chặn hết hiệu lực theo ADR-0036 (2026-10-21) — luật giữ; mẫu dự án đích đặt `auto` từ 3.24.0 (chủ repo 2026-10-25, D-176 — pha build không chờ người; thiếu khoá vẫn = `human`, dự án đã cài giữ giá trị cũ)
- **Trạng thái triển khai:** Đã triển khai — `scripts/xt.py` `merge_hard_mode`, `merge_decision(hard_auto=…)` trả
  `hard` rỗng + `hard_waived`, `HARD_KEY_REASON`/`_touches_hard_key`; `xt.yaml` đặt `merge_hard_exceptions: auto`,
  `framework/templates/xt.yaml` đặt `human` (D-025); test
  `tests/test_merge.py::HardExceptionL3Test::test_hard_auto_merges_and_keeps_reasons`, `MergeConfigTest::test_hard_mode`, `test_touches_hard_key`,
  `MergeCheckCliTest::test_hard_auto_from_xt_yaml`, `tests/test_hooks.py::MergeGuardTest::test_hard_exception_auto_lets_merge_through`
- **Ngày:** 2026-10-18
- **Thay một phần:** ADR-0016 (ngoại lệ cứng người merge "ở mọi mức") và ADR-0019 (merge ngoại lệ cứng bị chặn) — chỉ
  khi khoá là `auto`; quyết định D-024, D-025

## Bối cảnh

Chủ repo yêu cầu (2026-10-17) "nâng mức độ tự động lên cao nhất có thể", rồi chọn rõ phương án "Bỏ toàn bộ ngoại lệ
cứng" sau khi được nêu rủi ro (lỗi auth/thanh toán lên `main` không người xem). Trước đó khung đã ở L3 (ADR-0015), guard
không hỏi (ADR-0018), ruleset 0 approval; chốt người duy nhất còn lại agent gỡ được là ngoại lệ cứng: PR chạm tiền, dữ
liệu người dùng thật, auth, mật mã, bí mật (`merge-check` trả `hard` → guard chặn merge/bật auto-merge).

## Quyết định

1. Khoá `xt.yaml` `merge_hard_exceptions: human|auto`, đọc ở **nhánh đích đã commit** (`git show origin/<base>:./xt.yaml`),
   không ở cây làm việc — agent sửa file tại chỗ không tự gỡ được chốt. Không đọc được, thiếu khoá hoặc giá trị lạ →
   `human` (hành vi ADR-0016/0019; giá trị lạ kèm ghi chú).
2. PR có diff `xt.yaml` chạm khoá (hoặc diff thiếu patch) luôn là ngoại lệ cứng không miễn được (`HARD_KEY_REASON`):
   bật/tắt khoá phải do người merge — đó là lời chủ dự án chấp nhận rủi ro mà `LOOP-STOP-005` đòi.
3. `auto`: `merge-check` vẫn tính lý do ngoại lệ cứng nhưng trả `hard: []` và ghi lý do vào `hard_waived` + một dòng
   `reasons` (người đọc lại được). PR vẫn ở làn chuẩn: dưới L3 vẫn `human`; ở L3 merge khi CI xanh.
4. Repo khung đặt `auto` theo yêu cầu chủ repo; mẫu `templates/xt.yaml` đặt `human` (D-025): dự án đích có tiền/dữ
   liệu người dùng thật, mặc định `auto` vi phạm `LOOP-STOP-005` ngay khi cài. Chủ dự án bật bằng một PR đổi khoá.
5. Guard không đổi: nó chỉ đọc `hard` của `merge-check`. Mọi luật `deny` khác (không đảo ngược, tắt hook, ghi bí mật,
   gửi bí mật ra mạng) giữ nguyên.

## Lý do

- Người dùng có quyền cuối (AGENTS.md §1); chủ repo đã chọn sau khi thấy rủi ro.
- Khoá cấu hình giữ đường lùi một dòng (tiêu chí 2); bản cài cũ thiếu khoá không đổi hành vi.
- Lớp đỡ còn lại là máy: required check `quality` (test, coverage), `gitleaks` (bí mật), `codeql`, `dep-audit`,
  `protection-guard`; review của `reviewer` (model khác) trước merge theo skill `/autopilot`.

## Các phương án đã cân nhắc

- **Xoá hẳn `merge_hard_reasons`/`HARD_ASK`**: mất đường lùi và vết lý do trong `merge-check`. Loại.
- **Mẫu dự án đích cũng `auto`**: dự án mới bỏ chốt khi chưa ai chấp nhận rủi ro (reviewer, D-025). Loại.
- **Dùng L4 cho mức này**: trái nghĩa L4 trong bảng L0–L4 ("làn kiến trúc luôn có người"). Loại.
- **Chỉ bỏ auth + mật mã, giữ tiền/dữ liệu thật/bí mật**: chủ repo không chọn.

## Hệ quả

- `LOOP-STOP-005` (**MUST**) thêm điều kiện: người duyệt trước merge khi `merge_hard_exceptions: human`; `auto` là
  chủ dự án chấp nhận rủi ro, ghi bằng ADR/D-NNN của dự án.
- Thao tác lúc chạy trên tiền thật/dữ liệu người dùng thật (thanh toán thật, xoá/xuất dữ liệu production, gửi tin tới
  người dùng thật) vẫn là việc cần người (AGENTS.md §5, D-023) — khoá này chỉ nói về merge code.
- Dự án đích đã có `xt.yaml`: `install.py` giữ file, chỉ sinh `xt.yaml.xtemplates-new` (có khoá `human`); thiếu khoá vẫn
  là `human`. Muốn `auto`: mở PR thêm `merge_hard_exceptions: auto`, người merge.
- PR này (đặt `auto` ở repo khung) chạm khoá nên chính nó cần người merge.
