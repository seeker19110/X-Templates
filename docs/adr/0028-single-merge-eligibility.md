# ADR-0028: Một điều kiện "được merge" cho merge-check, pr next, merge-gate, guard và steward

- **Trạng thái:** Đã chấp nhận
- **Trạng thái triển khai:** Đã triển khai trong repo — `scripts/xt.py` `review_gate`, `merge_eligibility`, `_merge_eval`
  (trường `review`/`eligible`/`auto_merge_ok`), `cmd_merge_gate`, `pr_next`; `.claude/hooks/guard.py`
  `_merge_verdict`/`_auto_merge_verdict`; test `tests/test_merge.py::MergeGateTest.test_merge_gate_missing_review`,
  `test_single_merge_condition`, `tests/test_hooks.py::MergeGuardTest.test_l3_enables_auto_merge_on_open`.
- **Ngày:** 2026-10-19
- **Làm rõ:** ADR-0023, ADR-0024, ADR-0027 — mục REC-03 của `docs/ops/REMEDIATION-PLAN-2026-10-19.md`, task T-1507

## Bối cảnh

"PR này đã đủ điều kiện merge chưa" được trả lời ở nhiều chỗ, mỗi chỗ một phần: `merge-check` (CI, xung đột, làn, `hard`)
không biết review; `pr next` biết review qua sổ cục bộ + dấu đã đăng; `merge-gate` (ADR-0023) chỉ biết `hard`; guard
(`gh pr merge`, MCP) tin `merge-check` = `merge`; `pr steward` đi qua `pr next`. Hệ quả đo được: PR làn chuẩn bật auto-merge
**trước** review sạch vẫn xanh ở `merge-gate`, guard cho bật, chỉ `pr next` bảo tắt — lời dặn, không phải cơ chế.

## Quyết định

1. **Hàm thuần `review_gate(d, reviews, standard_seen)`** quyết review ở head: `na` (làn nhanh, chưa từng vào làn chuẩn/bị
   chặn) · `ok` · `missing` · `blocking`. Review ở đúng head hiện tại quyết trước; chỉ khi chưa có mới xét review sạch mang
   qua bản "cập nhật nhánh" sạch (`base_merge_of`, ADR-0027). `pr_next` dùng đúng hàm này (không còn logic riêng).
2. **Hàm thuần `merge_eligibility(d, reviews, standard_seen)`** trả `eligible` (`merge-check` = merge **và** review hợp lệ)
   và `auto_merge_ok` (không `hard` **và** review hợp lệ — điều kiện để auto-merge của GitHub, vốn không ghim head, được phép
   đang bật). `_merge_eval` thêm `review`, `eligible`, `auto_merge_ok` vào quyết định của `merge-check --json`; exit code
   của `merge-check` giữ nguyên (`verdict` = merge).
3. **`merge-gate` đỏ** khi PR đang bật auto-merge mà `hard` **hoặc** review ở head là `missing`/`blocking` (trước đó chỉ
   `hard`). Không bật auto-merge → không chặn (merge tay ghim head đã có guard).
4. **Guard** (`gh pr merge`, `gh api …/merge`, MCP) hỏi khi `eligible` là `false` (merge) hoặc `auto_merge_ok` là `false`
   (bật auto-merge). Trường vắng (khung cũ) = như trước.
5. Có `review_identity` (xt.yaml đã commit ở nhánh đích; không đọc được ref thì lấy cây làm việc): chỉ dấu của đúng tài khoản đó
   tính, dấu bị sửa sau khi đăng (`updated_at` ≠ `created_at`) bị bỏ, và `pr next`/steward cũng bỏ sổ cục bộ của tác giả.
6. Nguồn review là **dấu đã đăng trên PR** (`xtReviews`, ADR-0027) — dùng chung giữa phiên, CI và steward; sổ cục bộ của một
   phiên (`pr reviewed --no-publish`) không đủ để guard/`merge-gate` cho qua.

## Lý do

- Một hàm = một sự thật: `pr next` bảo tắt auto-merge ⇔ `merge-gate` đỏ ⇔ guard hỏi khi bật (chỉ khi `XT_GUARD_POLICY=strict`: ở chính sách mặc định lý do không thuộc nhóm chặn nên guard cho qua — lớp chặn thật là `merge-gate`, và chỉ với PR đang bật auto-merge). Test bảng
  (`test_single_merge_condition`) chạy cùng một tập ca qua `merge_eligibility` và `pr_next`.
- `merge-gate` không đòi review ở PR không bật auto-merge để người/agent còn merge được PR đã đủ điều kiện theo thiết kế
  ADR-0023; chỗ hở thật chỉ là auto-merge không ghim head.

## Hệ quả

- Người bật auto-merge trước review sẽ thấy `merge-gate` đỏ; sau `xt.py pr reviewed` phải tắt/bật lại auto-merge để check
  chạy lại (comment không kích `pull_request_target`; `auto_merge_enabled` thì có).
- Giới hạn còn lại: `merge-gate` chạy ở CI checkout nông nên không kiểm xung đột cục bộ; steward vẫn tự bật auto-merge theo
  `pr next` khi phiên đã dừng.
