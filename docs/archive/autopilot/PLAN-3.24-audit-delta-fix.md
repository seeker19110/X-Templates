# PLAN-3.24-audit-delta-fix.md — Khung X-Templates · sửa audit delta `e5ff88c..3ba5828` → bản 3.22.1

> Lập ngày 2026-10-25. Chủ repo: "Audit delta xoá review_debt"; phiên chính tự duyệt kế hoạch sửa (D-173).

## Tóm tắt
- Phạm vi: AUD-SEC-105, AUD-HAR-106 (🟠) + AUD-SEC-106, AUD-XFEAT-024, AUD-HAR-107 (🟢 rẻ cùng vùng); mỗi lỗi có test đỏ trước khi sửa.
- Không làm: các 🟢 còn lại (nợ có chủ/hạn 2026-11-08), sinh lại BLUEPRINT.md (PR riêng).
- Ràng buộc: C901 ≤ 10, mypy --strict, coverage 100 %, trần byte; đường lùi: revert PR.
