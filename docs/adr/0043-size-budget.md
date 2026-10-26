# ADR-0043: Ngân sách kích thước — đóng băng bề mặt khung 3.x

- **Trạng thái:** Đã chấp nhận (phiên chính tự duyệt theo D-142 — PLAN-3.16.0-ceiling, chủ repo: "theo khuyến nghị đi"); số trần thư mục nâng bởi [ADR-0050](0050-raise-dir-size-caps.md)
- **Trạng thái triển khai:** Đã triển khai — `tests/test_docs_budget.py` `DIR_CAPS`, `test_dir_totals_stay_under_caps`
  (T-2407).
- **Ngày:** 2026-10-23
- **Làm rõ:** D-111 (trần byte từng file hướng dẫn, PLAN-3.12-lean), AUD-ARCH-001 (xt.py một file lớn), research
  [`2026-10-23-ceiling-analysis.md`](../../research/2026-10-23-ceiling-analysis.md) §5–§8.

## Bối cảnh

Khung lớn dần theo mỗi bản sửa: đo 2026-10-23 (file git theo dõi) `scripts/*.py` + `scripts/xt_app/` 677.958 B
(`xt.py` 10.586 dòng), `.claude/hooks/` 351.803 B (`guard.py` 6.170 dòng), `framework/11-autonomous-loop/` 221.245 B.
Mỗi lỗi sửa thêm một nhánh, mỗi ý mới thêm một lệnh; không có gì buộc gỡ cái cũ. Bề mặt lớn = chi phí đọc của agent mỗi
phiên, thời gian test, và chỗ cho lỗi guard (fail-open) — research §8 kết luận trần phát triển kế tiếp là "không thêm bề
mặt". Trần byte từng file hướng dẫn (D-111) đã giữ được `AGENTS.md`/`CLAUDE.md` gọn; chưa có trần cho mã và module.

## Phương án đã xét

1. **Trần tổng byte theo thư mục do test giữ** (= hiện tại + 5 %). Rẻ (một test), máy kiểm, buộc cắt chỗ khác khi thêm.
   Nhược: đếm byte không đo độ phức tạp; dư 5 % chỉ đủ vài bản sửa.
2. **Trần số lệnh/khoá/module** (đếm subcommand `xt.py`, khoá `xt.yaml`, file module). Đo đúng "bề mặt" hơn nhưng nhiều
   định nghĩa, dễ lách (gộp lệnh), cần nhiều test.
3. **Không trần, chỉ review** — hiện trạng; đã chứng minh không đủ (bề mặt tăng mỗi bản).

## Quyết định

Chọn **phương án 1**. Ba nhóm, mỗi nhóm một trần tổng byte = kích thước tại 2026-10-23 + 5 %: mã CLI (`scripts/*.py` +
`scripts/xt_app/`), hàng rào (`.claude/hooks/`), giao thức vòng tự trị (`framework/11-autonomous-loop/`). Vượt trần là
CI đỏ; cách xanh duy nhất là cắt trong cùng nhóm (gỡ nhánh chết, gộp, chuyển chữ về "nhà"). **Đóng băng bề mặt 3.x:**
không nới số trong test; mở băng (nâng trần, thêm nhóm, bỏ trần) cần ADR mới nêu số đo và cái được đổi lại.

## Hệ quả

- Tốt: mọi PR thêm bề mặt phải tự trả giá ngay trong PR; tách `xt.py` (AUD-ARCH-001) không bị chặn (cùng nhóm).
- Xấu: bản sửa lỗi cần thêm vài trăm byte khi nhóm đã sát trần phải cắt chỗ khác trước — chậm hơn, đó là mục đích.
- Nợ: chưa trần cho `framework/` ngoài vòng tự trị, `tests/`; byte không phải độ phức tạp (C901 ≤ 10 vẫn giữ riêng).
- Đường lùi: revert commit T-2407 (một test + ADR này đổi trạng thái "Bị thay bởi ADR-NNNN").
