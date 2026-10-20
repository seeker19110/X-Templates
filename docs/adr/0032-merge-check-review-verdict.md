# ADR-0032: `merge-check` trả verdict `review` (exit 1) khi PR chưa đủ điều kiện merge vì review

- **Trạng thái:** Đã chấp nhận
- **Trạng thái triển khai:** Đã triển khai trong repo (commit 061137b, #182) — `scripts/xt.py` `merge_check_result` (verdict
  `review`, bỏ `next_rest`, `_review_step`), `cmd_merge_check` (exit 0 chỉ khi `merge`), `merge-watch` thoát 1 cùng bước;
  test `tests/test_merge_review_source.py::MergeCheckReviewStepTest`
  (`test_merge_check_no_merge_command_without_review`, `test_merge_check_blocking_review_points_to_fix`,
  `test_merge_check_clean_review_still_merges`, `test_merge_check_build_phase_still_merges_without_review`,
  `test_merge_watch_no_merge_command_without_review`).
- **Ngày:** 2026-10-20
- **Thay:** §Quyết định 2 của [ADR-0028](0028-single-merge-eligibility.md) (câu "exit code của `merge-check` giữ nguyên
  (`verdict` = merge)"). Phần còn lại của ADR-0028 giữ nguyên. Quyết định tự duyệt D-099
  ([`DECISIONS.md`](../autopilot/DECISIONS.md)); lỗi gốc AUD-XFEAT-010.

## Bối cảnh

ADR-0028 §2 thêm `review`, `eligible`, `auto_merge_ok` vào `merge-check --json` nhưng giữ `verdict` và exit code như cũ:
PR làn chuẩn có CI xanh, không xung đột, chưa có review sạch ở head vẫn nhận `MERGE`, exit 0 và dòng gợi
`gh pr merge … --match-head-commit`. Audit rescan 2026-10-19 (AUD-XFEAT-010) ghi nhận hệ quả: lệnh có tên "quyết khi nào
merge" (ADR-0013) trả `merge` cho PR chưa đủ điều kiện; script/agent dựa exit 0 (đúng như AGENTS.md §6 dặn) sẽ merge PR
chưa review, chỉ guard hoặc `merge-gate` đỡ phía sau.

## Phương án đã xét

1. **Verdict mới `review`, exit 1, không in lệnh merge** khi `merge_decision` cho `merge` mà `eligible` là `false`.
   Ưu: một điều kiện merge thật sự (exit 0 ⇔ được merge); script cũ dựa exit code tự an toàn. Nhược: thêm một giá trị
   verdict; ai đọc `verdict` phải biết `review`.
2. **Giữ verdict `merge`/exit 0, chỉ bỏ dòng lệnh merge.** Ưu: không đổi giao ước. Nhược: exit 0 vẫn nói "merge được" —
   chỗ hở còn nguyên với mọi người gọi dựa exit code.

## Quyết định

Chọn phương án 1. Khi verdict của `merge_decision` là `merge` mà `merge_eligibility(...)["eligible"]` là `false`
(review ở head `missing` hoặc `blocking`), `merge-check` trả:

- `verdict: "review"`, exit 1, không có `next_rest` (không in lệnh merge ghim head);
- `reasons` thêm "chưa có review hợp lệ ở head (`missing`|`blocking`) — ADR-0028";
- `next` là bước review (`pr reviewed …`, rồi `pr next`) hoặc, với `blocking`, bước sửa rồi rà lại.

`merge-watch` thoát 1 với cùng bước. Pha `delivery_phase: build` (ADR-0031): review hoãn (`review: deferred`) là hợp lệ
nên `eligible` đúng và verdict vẫn là `merge`. Các verdict khác (`wait`, `human`, `hard`, …) không đổi. Trường `review`,
`eligible`, `auto_merge_ok` của `--json` giữ như ADR-0028.

## Hệ quả

- Tốt: `merge-check` exit 0 ⇔ PR được merge ngay (CI, xung đột, làn, ngoại lệ cứng và review); không còn gợi lệnh merge
  cho PR chưa rà.
- Xấu: công cụ ngoài so `verdict` với danh sách cố định cần nhận thêm `review`; bên trong khung, guard đọc `eligible`/
  `auto_merge_ok` (ADR-0028 §4) nên không đổi.
- Đường lùi: trả verdict `merge`, exit 0 (D-099).
