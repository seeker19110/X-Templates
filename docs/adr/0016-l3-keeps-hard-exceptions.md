# ADR-0016: Ở `merge_autonomy: L3` vẫn để người merge ngoại lệ cứng (tiền, dữ liệu thật, auth, mật mã, bí mật)

- **Trạng thái:** Đã chấp nhận — thay một phần bởi ADR-0020 (`merge_hard_exceptions: auto`); vế "bật auto-merge" trong cơ chế
  chặn hết hiệu lực theo ADR-0036 (2026-10-21): guard chặn merge ghim head PR `hard`, máy không bật auto-merge ở PR nào
- **Trạng thái triển khai:** Đã triển khai (`scripts/xt.py` `merge_hard_reasons`, `merge_decision` trả `hard`;
  `.claude/hooks/guard.py` `_auto_merge_verdict`; test `tests/test_merge.py::HardExceptionL3Test`,
  `GuardHardExceptionTest`)
- **Ngày:** 2026-10-16
- **Thay một phần:** ADR-0015 §1 ("L3 trả `merge` cho cả làn chuẩn") và §4 (miễn trừ `WF-REVIEW-007` toàn mục); làm
  rõ ADR-0014 §1 (xoá nhánh khi merge) — quyết định D-012

## Bối cảnh

Quét lại delta sau #58–#66 (`docs/ops/AUDIT-REPORT-2026-10-16-delta.md`, AUD-HAR-042, xác minh đối kháng):
`merge_decision` ở L3 trả `merge` cho PR `src/auth/login.py` + `src/payment/charge.py` (nhãn `risk:auth`), trong khi
`LOOP-STOP-005` (**MUST**) và "Ngoại lệ cứng" của `stop-points-and-escalation.md` nói việc chạm tiền thật, dữ liệu người
dùng thật, xác thực/phân quyền, mật mã **luôn có người duyệt trước merge, kể cả diff 1 dòng**. ADR-0015 chỉ miễn
`WF-REVIEW-007`. Ruleset `main` của repo khung có `required_approving_review_count: 0` → ở L3 không còn chốt người nào.

Cùng lần quét (AUD-DOC-034): ADR-0014 §1 ghi "không xoá nhánh khi merge … nên GitHub không tự đổi đích", nhưng repo khung
bật `delete_branch_on_merge` (nhánh của #66 bị xoá sau merge). Dữ kiện (xác minh 2026-10-16): xoá nhánh đầu của PR đã
merge thì GitHub đổi đích mọi PR mở nhắm nhánh đó sang nhánh đích của PR đã merge
(<https://docs.github.com/en/pull-requests/how-tos/commit-changes/managing-branches-within-your-repository>;
<https://github.blog/changelog/2020-05-19-pull-request-retargeting/>).

## Quyết định

1. **Ngoại lệ cứng ở mọi mức tự chủ, kể cả L3.** `merge-check` tính `hard` (danh sách lý do) độc lập với CI: đường dẫn
   bí mật/auth/thanh toán/mật mã (`RISK_PATH_RES`), nhãn `risk:auth|payment|pii|crypto|admin|secret`, và
   `merge_risk_paths` của dự án (chủ dự án tự khai là nhạy cảm). Có `hard` → verdict `human` (khi không bị chặn bởi
   trạng thái khác) và guard **không** bật auto-merge (`gh pr merge --auto`, MCP `enable_pr_auto_merge`) — kể cả lúc mới
   mở PR, CI còn chạy.
2. **Làn chuẩn còn lại vẫn auto-merge ở L3** như ADR-0015: cổng/CI/harness/luật agent, schema, phụ thuộc, > 150 dòng,
   nhiều gói, đổi mã không đổi test, nhãn `risk:upload`/`risk:external-api`. Lý do merge ghi rõ "L3: làn chuẩn".
3. **Miễn trừ `WF-REVIEW-007` ở L3 chỉ cho phần không phải ngoại lệ cứng** (`.github/`, hook, ruleset, migration);
   auth/thanh toán/mật mã/bí mật/PII giữ người review.
4. **ADR-0014 §1 đọc lại:** "không xoá nhánh" là luật cho **agent** (xoá nhánh là điểm dừng, AGENTS.md §5); chủ repo
   bật `delete_branch_on_merge` là cài đặt của người, được phép. Khi bật, GitHub tự đổi đích PR chồng về nhánh đích của
   PR đáy; agent vẫn `git merge origin/<mặc định>` vào nhánh chồng rồi chạy lại `merge-check` (bật auto-merge khi
   `stacked` thôi đúng).

## Lý do

- Tiêu chí 1 của ADR-0008 (cách hiểu chặt hơn với tiền/dữ liệu/bảo mật): yêu cầu "mở PR kèm auto-merge" của chủ repo
  nói chung, không nói bỏ chốt người cho tiền/auth; `LOOP-STOP-005` là MUST.
- Repo khung không có mã auth/thanh toán/mật mã → yêu cầu của chủ repo giữ nguyên ở đây.
- `hard` tính cả khi CI chưa xong vì auto-merge được bật lúc mở PR, trước khi có verdict `merge`.

## Các phương án đã cân nhắc

- **Ghi miễn trừ `LOOP-STOP-005` ở L3** (mọi PR auto-merge khi CI xanh): bỏ chốt người duy nhất cho tiền/auth ở dự án
  đích (ruleset thường 0 approval với đội 1 người). Loại (D-012).
- **Buộc ruleset đòi 1 approval khi L3**: đội 1 người không tự approve được PR của mình → chặn mọi merge. Loại.

## Hệ quả

- Dự án đích ở L3: PR chạm vùng ngoại lệ cứng hiện `human` trong `merge-check`, agent `loop defer`; báo cáo cuối liệt kê.
- Báo nhầm đường dẫn (vd `session_store.py` khớp "session") chỉ làm người phải bấm merge — chấp nhận, như `RISK_PATH_RES`.
- Dự án muốn tự merge cả vùng này phải sửa mã khung (không có cờ) — có chủ đích.
