# ADR-0019: Dưới chính sách không hỏi, merge ngoại lệ cứng bị chặn

- **Trạng thái:** Đã chấp nhận
- **Trạng thái triển khai:** Đã triển khai — `guard.py` `HARD_ASK` (thuộc `DANGER_MARKERS`), `_merge_verdict` kiểm
  `hard` trước verdict, `_auto_merge_verdict` dùng `HARD_ASK`; `pre-mcp-guard.sh` xuất `deny`; test
  `tests/test_hooks.py::MergeGuardTest::test_hard_exception_merge_denied_by_default`
- **Ngày:** 2026-10-17
- **Làm rõ:** ADR-0018 (danh sách việc nguy hiểm), ADR-0016 (ngoại lệ cứng người merge) — quyết định D-019

## Bối cảnh

ADR-0018 cho qua mọi `ask` không mang dấu `DANGER_MARKERS`. Lý do guard trả cho PR thuộc ngoại lệ cứng (`merge-check`
trả `hard`: tiền, dữ liệu người dùng thật, auth, mật mã, bí mật) là `EXTERNAL_ASK`, không mang dấu nguy hiểm, nên agent
tự merge/bật auto-merge được — trái `LOOP-STOP-005` (**MUST**, "kể cả L3") và ADR-0016. Merge thường còn chưa kiểm
`hard` (chỉ bật auto-merge kiểm), và `pre-mcp-guard.sh` bỏ qua quyết định `deny` nên tool MCP merge không bao giờ bị chặn.

## Quyết định

1. Lý do ngoại lệ cứng dùng chung hằng `HARD_ASK`, thuộc `DANGER_MARKERS` → mặc định **chặn**; `strict` vẫn hỏi.
2. `_merge_verdict` (merge ghim head qua `gh pr merge`, `gh api` REST, tool MCP) kiểm `hard` trước verdict.
3. `pre-mcp-guard.sh` xuất `deny` khi guard trả `deny`.

## Lý do

- Merge vào nhánh chính có code tiền/auth/bí mật chạy thật ngay khi deploy — revert không thu hồi được hậu quả.
- Chặn chặt hơn hỏi, không làm phiên đứng chờ: agent ghi `loop defer` rồi làm tiếp, người merge cuối phiên.

## Các phương án đã cân nhắc

- **Cho qua, sửa ADR-0016 và `LOOP-STOP-005`**: bỏ chốt người duy nhất cho nhóm rủi ro cao nhất. Loại.

## Hệ quả

- PR có nhãn `risk:auth|payment|pii|crypto|admin|secret`, đường dẫn nhạy cảm hoặc `merge_risk_paths` cần người merge
  trên GitHub; autopilot báo `done-pending-human` cho PR đó.
