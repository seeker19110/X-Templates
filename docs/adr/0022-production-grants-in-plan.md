# ADR-0022: Duyệt kế hoạch = một lần người duyệt Ủy quyền production; hạn mức autopilot mặc định x2

- **Trạng thái:** Đã chấp nhận
- **Trạng thái triển khai:** Đã triển khai — `scripts/xt.py` `parse_grants`, `grant_violations`, `cmd_grant_check`,
  `_touches_hard_key` (PLAN.md), trần vòng `max(40, 8 × task)`; mẫu `templates/PLAN.md` mục "Ủy quyền production";
  `AGENTS.md` §5, mẫu `AGENTS.md` §6, skill `/autopilot` bước 8/9/13/14, `LOOP-STOP-026`; test `tests/test_grants.py`,
  `tests/test_merge.py::MergeConfigTest::test_touches_grant_lines_in_plan`
- **Ngày:** 2026-10-18
- **Làm rõ:** ADR-0020 (khoá `merge_hard_exceptions`), ADR-0021 (`--max-minutes` 120 → 240); **thay một phần** ADR-0012
  §5 (hệ số trần vòng) — quyết định D-027, D-028

## Bối cảnh

Chủ repo muốn bật tự động 100% khi duyệt kế hoạch phát triển; muốn lên production thì các phần quan trọng (auth, tiền,
dữ liệu, mật mã, bí mật; thanh toán thật, xoá/xuất dữ liệu production, gửi tin tới người dùng thật) phải được refactor
để máy làm được an toàn. Sau ADR-0020 chỉ còn hai chốt người: PR ngoại lệ cứng (tắt được bằng khoá) và các thao tác
production thật (`AGENTS.md` §5, D-023) — nhóm sau chưa có cách bật tự động.

## Quyết định

1. **Mục "Ủy quyền production" trong `PLAN.md`**: các dòng `- grant: <nhóm> | khoá=giá trị | …` (nhóm: `payments`,
   `data_delete`, `data_export`, `outbound_messages`, `auth_crypto`, `secrets`). `max_<khoá>` là trần số; `true` cho phép cả
   hai giá trị, `false` chỉ nhận `false`, `a,b` chỉ nhận giá trị trong danh sách. Mẫu mặc định chỉ sandbox.
2. **`xt.py grant-check <nhóm> khoá=giá trị …`**: exit 0 = trong ủy quyền, 1 = ngoài (kể cả nhóm vắng hay thiếu mục —
   đóng khi thiếu) → agent `loop defer`, 2 = tham số sai. Dòng trong code fence không tính.
3. **Chốt người đúng một lần**: PR có diff đổi dòng `- grant:` ở `docs/autopilot/PLAN.md` (hoặc đổi khoá
   `merge_hard_exceptions`) luôn là ngoại lệ cứng không miễn được (`HARD_KEY_REASON`, mở rộng `_touches_hard_key`). PLAN do
   phiên chính tự duyệt (ADR-0008), nên không có chốt này agent tự cấp ủy quyền cho chính nó. Người merge PR duyệt kế hoạch
   là lời chấp nhận rủi ro duy nhất của dự án.
4. **Refactor phía sản phẩm** (hạn mức theo thời gian không do agent giữ): idempotency + sổ cái + hạn mức mỗi giao dịch/ngày +
   `sandbox`/`live` sau feature flag có kill switch (thanh toán); xoá mềm + sao lưu có kiểm khôi phục (xoá); allowlist cột,
   ẩn danh, nhật ký mỗi lần xuất (xuất); allowlist người nhận, giới hạn tốc độ, canary (gửi tin); thư viện chuẩn, SAST (auth,
   mật mã); secret manager, token phạm vi hẹp, agent không đọc giá trị (bí mật). Khung đã có `DB-TX-001`, `WF-ENV-011`,
   `OPS-DEPLOY-006`, `WF-REL-014`, `BASE-SEC-016`; `LOOP-STOP-026` gắn chúng với ủy quyền.
5. **Hạn mức mặc định x2** (chỉ áp khi PLAN bỏ trống số, số PLAN khai tường minh ưu tiên; hiệu lực ở `loop init`, tức ngay
   sau duyệt PLAN): trần vòng `max(40, 8 × task chưa làm)` (một phiên) / 100 (không `--single-session`), `merge-watch`
   `--max-minutes` 240, khuyến nghị `--hours` ≤ 16 và `--max-iterations` 60–100. Breaker 80/90/100 % và
   `same_failure_count` 3 giữ nguyên.

## Lý do

- Tự động 100% thật không đạt (khoá/tài khoản cổng thanh toán, trách nhiệm pháp lý, lần bật `live` đầu chỉ chủ dự án có);
  chuyển "người duyệt từng việc" thành "người duyệt một chính sách có hạn mức máy kiểm" đưa mức tự động tới ~95–98 %.
- Đóng khi thiếu (tiêu chí 1): chưa ghi ủy quyền = chưa cho gì.
- Nhân đôi hạn mức chỉ nới giới hạn thời gian/số vòng, không nới hàng rào an toàn.

## Các phương án đã cân nhắc

- **Khoá cấu hình trong `xt.yaml` cho từng nhóm**: tách khỏi kế hoạch người duyệt, khó đọc cùng PLAN. Loại.
- **Chỉ dặn trong `AGENTS.md`**: lời dặn không phải cơ chế (`LOOP-STOP` nguyên tắc 5). Loại.
- **Nhân đôi cả số PLAN khai tường minh**: đổi ý định đã ghi của chủ dự án. Loại.

## Hệ quả

- Dự án đích có mục ủy quyền mặc định chỉ sandbox; muốn live phải mở PR sửa dòng `- grant:` và tự merge.
- Hạn mức theo thời gian (mỗi ngày/giờ) nằm ở code sản phẩm; `grant-check` chỉ kiểm trần một thao tác agent định làm.
- Dự án đích nhận lệnh và mục mẫu khi chạy lại `install.py` (gộp tay `*.xtemplates-new`).
