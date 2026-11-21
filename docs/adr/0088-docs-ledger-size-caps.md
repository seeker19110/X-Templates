# ADR-0088: Nới trần byte của sổ sách `docs/ops` và `docs/autopilot`

- **Trạng thái:** Đã chấp nhận ngày 2026-11-21 theo yêu cầu của chủ dự án (nâng trần file lên mức thoải mái).
- **Trạng thái triển khai:** Đã triển khai — `tests/test_docs_budget.py` (`DIR_CAPS`).

## Bối cảnh

Trần tổng byte theo thư mục (ADR-0043) giữ `docs/ops` ở 810 114 B và `docs/autopilot` ở 352 345 B, tức kích thước đo
2026-11-02 cộng 5 % (D-314). Sổ audit, báo cáo cổng ký, GO-NO-GO và sổ quyết định tăng theo mỗi đợt harden. Đợt 3.35.0 kín
cả hai trần: mỗi PR sổ phải rút gọn dòng cũ, chuyển 24 dòng `đã sửa` sang lưu trữ và cắt chữ trong quyết định chỉ để vừa
số byte, tốn nhiều vòng cổng commit mà không tăng chất lượng. Ba nhóm còn lại đã được nới +1 MiB ở ADR-0050.

## Quyết định

1. `docs/ops` và `docs/autopilot` cộng 1 MiB như ADR-0050: trần lần lượt 1 858 690 B và 1 400 921 B. Cách đo, loại trừ
   file lưu trữ và luật "mốc ≤ 2×" của `SIZE_MARKS` giữ nguyên. Trần hiệu lực là số nhỏ hơn của hai luật: mốc 2×
   (1 543 076 B và 671 134 B) thấp hơn trần mới, nên chỗ trống thật còn khoảng 744 KB và 319 KB; muốn hơn nữa phải khai
   mốc mới ở `SIZE_MARKS` bằng một ADR sau.
2. Không đổi trần theo từng file (`AGENTS.md`, `PROGRESS.md`, `CLAUDE.md` mẫu, skill): các file này nạp vào ngữ cảnh mọi
   phiên, trần của chúng bảo vệ ngân sách ngữ cảnh chứ không phải dung lượng kho.
3. Lưu trữ vẫn là cách giữ sổ đang dùng gọn: dòng `đã sửa` cũ chuyển sang `*-ARCHIVE.md`, quyết định cũ sang bản tháng.

## Hệ quả

- Tốt: PR sổ và PR cắt bản không còn phải cắt chữ để vừa trần; lịch sử quyết định giữ nguyên văn.
- Xấu: sổ đang dùng có thể phình lại; máy kiểm mốc 2× (`SIZE_MARKS`) vẫn bắt khi một nhóm vượt gấp đôi mốc.
- Đường lùi: đưa hai số về 810 114 và 352 345 ở `DIR_CAPS`, chuyển bớt dòng sang lưu trữ.
