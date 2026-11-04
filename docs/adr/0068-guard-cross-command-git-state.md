# ADR-0068: Cấu hình/hook git ghi ở lệnh Bash TRƯỚC rồi dùng qua thư mục git ngoài dự án — giới hạn guard từng lệnh, chấp nhận có hạn

- **Trạng thái:** Đã chấp nhận 2026-11-04 (phiên chính tự duyệt theo tiêu chí chất lượng cuối, ADR-0008 — **D-339**).
- **Trạng thái triển khai:** đã làm (sổ + tài liệu, PR kế sau #434); đánh giá sandbox opt-in ở `PROGRESS.md` *Tiếp theo* (cùng ADR-0067).
- **Ngày:** 2026-11-04.
- **Giữ:** ADR-0063/0065/0066/0067, D-336…D-338 (luật phía đọc cấu hình git) — mọi luật hiện có giữ nguyên, không nới.
- **Liên quan:** ADR-0002, ADR-0018/0019, ADR-0061 (`max_rethink`), ADR-0062, ADR-0064 (sandbox kiểm bằng `doctor`); mốc xét lại hàng rào 2027-01-21 (`LOOP-DESIGN-014`).

## Bối cảnh

Guard quyết định trên MỘT lệnh Bash, không giữ trạng thái giữa các lệnh và không đọc nội dung tệp lúc chạy (ADR-0066). Chín lượt review đối kháng liên tiếp (#426…#434, 2026-11-03…04, git 2.43 thật) đóng dần các dạng NẰM TRỌN TRONG MỘT LỆNH: `.git/config`, `config.worktree`, gitconfig toàn cục (cả sau `cd`, qua symlink, hard link, trình thông dịch), biến trỏ tệp cấu hình (`HOME`, `XDG_CONFIG_HOME`, `GIT_CONFIG_GLOBAL|SYSTEM`, `GIT_DIR`, `--git-dir`, `--template`, `--exec-path`). Lớp còn lại không đóng được bằng phân tích từng lệnh: tạo hoặc ghi một thư mục git NGOÀI dự án ở lệnh trước (`git init --bare /tmp/gd`; ghi `/tmp/gd/config` có `[alias] x = !…`, `diff.external`, `core.fsmonitor`), rồi ở lệnh sau `git -C /tmp/gd x` / `cd /tmp/gd && git diff` — git dò thư mục git theo `-C`/`cd` như bình thường. Lệnh sau không có biến/cờ đặc biệt nào; lệnh trước chỉ ghi một tệp tên `config` ngoài dự án. Chặn cả hai phía nghĩa là chặn mọi `git -C <ngoài dự án>` hoặc mọi ghi tệp tên `config` — chặn oan rất lớn (worktree, clone tạm, CI).

## Các phương án đã cân nhắc

1. **Guard có trạng thái** (nhớ thư mục git do phiên tạo/ghi) — đổi mô hình guard (ADR-0018/0063: không trạng thái, fail-open về luồng); trạng thái giả mạo được bằng chính lệnh ghi; lớn, rủi ro.
2. **Chặn mọi git ngoài cây dự án** — chặn oan CI/worktree/clone tạm; trái (4).
3. **Chấp nhận có hạn lớp "trạng thái do lệnh trước để lại"** (chọn), mọi dạng một-lệnh vẫn phải sửa; sandbox opt-in là lớp cứng (ghi ngoài thư mục làm việc bị chặn).

## Quyết định

Chọn **3**. Phát hiện được ghi `chấp nhận` theo ADR này khi đủ cả: (a) cần ÍT NHẤT HAI lệnh Bash và lệnh dùng không chứa biến/cờ/đường nào chỉ ra cấu hình lạ (chỉ `-C`/`cd` tới thư mục git ngoài dự án); (b) mọi dạng gộp trong một lệnh của nó đã bị chặn (có test); (c) không phải hồi quy hay lỗ do miễn trừ mới. Chủ: phiên chính; hạn 2027-01-21. Thư mục git CỦA dự án (kể cả gitdir thật theo gitfile/`--separate-git-dir`) không thuộc lớp này.

## Hệ quả

- AUD-SEC-446 → `chấp nhận`; các dạng một-lệnh còn mở (AUD-SEC-442/443/445/447) sửa ở T-3668.
- Dự án đích: bật `/sandbox` trên máy dev (ghi ngoài thư mục làm việc bị chặn ở mức hệ điều hành); ruleset nhánh chính giữ chặn force-push/xoá.
- Hết hạn 2027-01-21 → `audit check` đỏ (chấp nhận quá hạn), buộc xét lại cùng ADR-0067.
- Đường lùi: đổi AUD-SEC-446 về `mở`.
