# ADR-0067: Tên tệp/mô-đun DỰNG LÚC CHẠY trong lệnh tự ghi tệp — giới hạn phân tích tĩnh, chấp nhận có hạn

- **Trạng thái:** Đã chấp nhận 2026-11-03 (phiên chính tự duyệt theo tiêu chí chất lượng cuối, ADR-0008 — **D-331**,
  thu hẹp sau review #428 — **D-332**).
- **Trạng thái triển khai:** đã làm (sổ + tài liệu, #428); đánh giá sandbox opt-in ở `PROGRESS.md` *Tiếp theo*.
- **Ngày:** 2026-11-03.
- **Thay một phần:** ADR-0065 §Quyết định ("dạng lách mới thì mở rộng điều kiện kích hoạt, không thêm miễn trừ") —
  CHỈ cho lớp hẹp ở §Quyết định dưới đây. **Giữ:** ADR-0002, ADR-0063/0065/0066 cho mọi lớp khác; không nới luật nào.
- **Liên quan:** ADR-0018/0019, ADR-0061 (`max_rethink`), ADR-0062 (🔴 không thành nợ), ADR-0064 (sandbox kiểm bằng
  `doctor`), D-322, D-326, D-329; mốc xét lại hàng rào 2027-01-21 (`LOOP-DESIGN-014`).

## Bối cảnh

ADR-0066 (#427) chặn tệp do chính lệnh ghi mà TÊN được nhắc lại nguyên văn ở lệnh đơn khác. Review #427/#428 (bash 5.2.21,
stub `git`) chỉ ra phần còn lại của AUD-SEC-406 gồm hai loại khác nhau về bản chất:

- **Tên dựng lúc chạy** — tên tệp/mô-đun KHÔNG xuất hiện nguyên văn mà do shell/trình thông dịch tính ra:
  `python3 -m "${y:-x}"`, `python3 -m "$(printf '\x78')"`, `python3 -m "${m,,}"`, `__import__("X".lower())`,
  `f=s.sh; printf … > "$f"; PATH=.:$PATH s.sh`. Đóng lớp này bằng cách "mở rộng điều kiện kích hoạt" (ADR-0065) nghĩa là
  chặn MỌI mở rộng (kể cả trong nháy kép) và mọi chữ trong `-c`/`-e` của mọi lệnh có ghi tệp — vì tên có thể là kết quả
  của tính toán tuỳ ý (đọc tệp, giải mã, đổi hoa) mà phân tích tĩnh không giải được theo nguyên lý.
- **Dạng nguyên văn chưa phủ** — tên nằm ngay trên dòng lệnh: trình ghi chưa liệt kê (`sponge`, `tar -x`, `unzip`,
  `openssl … -out`, `xxd -r`), tệp nạp ngầm (`Makefile`/`GNUmakefile`, `package.json`, `conftest.py`, `~/.bashrc`),
  `~` sau `HOME=` gán bằng chữ, `patch`/`git apply` có đích trong thân heredoc. Lớp này sửa được bằng luật tĩnh.

ADR-0065 loại phương án "chấp nhận + giao sandbox" vì sandbox chưa bắt buộc ở mọi quy mô; điều kiện đó vẫn đúng. Điều mới:
ở lớp tên dựng lúc chạy, phương án thay (chặn mọi mở rộng trong lệnh ghi tệp) đã đo: luật hẹp hơn của #426/#427 chặn oan
6 % lệnh thật, bản rộng chặn cả `"$f"` trong nháy kép mà ADR-0065 khuyên dùng — tức mâu thuẫn chính câu `viết lại:` của nó.

Lớp ngoài thật (đọc 2026-11-03): ruleset GitHub nhánh mặc định (`non_fast_forward`, `deletion`, required checks
quality/protection-guard/gitleaks/dep-audit; `required_approving_review_count: 0` — review là quy trình do harness cưỡng
chế, KHÔNG phải ranh giới máy chủ). Sandbox Bash của Claude Code (<https://code.claude.com/docs/en/sandboxing>): mặc định
tắt, Linux cần bubblewrap + socat, không khởi động được thì chạy không sandbox trừ `failIfUnavailable`; khi bật, tệp
settings là "protected paths". **Nhóm "tắt hook cục bộ" (ghi `.claude/`) không có lớp cứng nào khi sandbox tắt.**

## Các phương án đã cân nhắc

1. **Chặn mọi mở rộng/chữ `-c` trong lệnh có ghi tệp** — chặn oan lớn, trái câu `viết lại:` của ADR-0065.
2. **Vá theo từng dạng tên dựng** — mỗi lượt lộ dạng mới (#420…#427), không điểm dừng (ADR-0061).
3. **Chấp nhận có hạn ĐÚNG lớp tên dựng lúc chạy** (chọn); mọi dạng nguyên văn vẫn là 🔴 `mở` phải sửa.

## Quyết định

Chọn **3**. Phát hiện chỉ được ghi `chấp nhận` theo ADR này khi đủ cả: (a) tên tệp/mô-đun mà lệnh chạy KHÔNG xuất hiện
nguyên văn ở đâu trong lệnh (do mở rộng/tính toán lúc chạy sinh ra); (b) mọi dạng cùng hành vi với tên nguyên văn đã bị
guard chặn (có test); (c) không phải hồi quy hay lỗ do miễn trừ mới (ADR-0062). Chủ: phiên chính; hạn 2027-01-21.
Tệp nạp ngầm, trình ghi chưa liệt kê, `~` sau `HOME=` chữ, `patch`/`git apply` **không** thuộc lớp này.

## Hệ quả

- AUD-SEC-406 thu về đúng phần tên dựng lúc chạy → `chấp nhận`. Phần nguyên văn tách ID 🔴 `mở` mới (trình ghi chưa
  liệt kê; tệp nạp ngầm); AUD-SEC-414 về `mở` — `audit check --strict` đỏ tới khi sửa (task `T-3663`).
- Dự án đích: bật ruleset nhánh chính; trên máy dev nên bật `/sandbox` — guard không che được tên dựng lúc chạy.
- Hết hạn 2027-01-21 → `audit check` đỏ (chấp nhận quá hạn), buộc xét lại cùng mốc hàng rào.
- Đường lùi: đổi AUD-SEC-406 về `mở`.
