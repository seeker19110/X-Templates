# ADR-0063: Guard chỉ cho chạy tập con bash nó đọc chắc — ngoài tập con thì chặn, không vá từng ca

- **Trạng thái:** Đã chấp nhận (phiên chính tự duyệt theo tiêu chí chất lượng cuối, ADR-0008 — D-299)
- **Trạng thái triển khai:** Đang triển khai theo `docs/autopilot/PLAN-harden-2026-11-01.md` (mỗi lớp một PR)
- **Ngày:** 2026-11-01
- **Thay:** cách sửa "mỗi phát hiện một luật nhận dạng" cho họ lỗi lách bộ phân tích bash (AUD-SEC-180…302). **Giữ:**
  ADR-0002 (fail-closed về hành động nguy hiểm), ADR-0018/0019 (guard không hỏi người), mọi luật hiện có — luật mới OR
  với luật cũ (bài học #352, #372).

## Bối cảnh

`.claude/hooks/guard.py` mô phỏng cách bash đọc lệnh (nháy, comment, heredoc, thay lệnh, brace, tilde) để thấy lệnh nguy
hiểm. Mỗi chỗ mô phỏng lệch với bash là một đường lách: đầu `/complete` 2026-11-01 sổ audit còn 18 🔴 + 18 🟠 cùng họ (28 🟠 mở tính cả scanner `xt.py`). Vá
từng ca không hội tụ: #372 qua 7 lượt review, lượt nào cũng lộ ca mới; PLAN-fix-2026-11-01 (#389–#392) đóng 12 ca, audit
delta tìm thêm 8 🟠 cùng lớp (AUD-SEC-294…301).

## Các phương án đã cân nhắc

1. **Vá từng ca** — giữ hành vi rộng, nhưng chi phí tăng theo số ca và không có điểm dừng.
2. **Tập con chuẩn** (chọn) — guard chỉ cho chạy chữ nó đọc chắc như bash; gặp cấu trúc nó không mô phỏng chắc thì chặn
   (mã `BUDGET`, lý do ghi "ngoài tập con guard đọc chắc … (ADR-0063)"), agent viết lại lệnh đơn giản hơn.
3. **Chấp nhận rủi ro các ca lách cố ý** (chủ + hạn), dựa vào bộ phân loại Auto — để 🔴 an toàn vào bản phát hành.

## Quyết định

Guard thêm một lớp kiểm trước khi quét (`_strict_why`, gọi từ `_shell_precheck`) trên chữ bash thật sự đọc: lệnh gốc agent
gửi và script shell lồng lấy nguyên văn (`bash -c '…'`, `eval`, ống/heredoc vào shell). Ngoài tập con → chặn:

| Lớp | Cấu trúc bị chặn | Phát hiện |
|---|---|---|
| Từ vựng | backtick (dùng `$(…)`), nháy/ngoặc không đóng, `#` ngay sau `)`, nháy trong comment khi sau đó có `$'`, `$'…\'…'` cùng brace, ngoặc lẻ trong chuỗi nháy bên trong `$(…)`, nháy lồng trong `${…}`, thân heredoc không nháy có `'` cùng thay lệnh | AUD-SEC-181, 196, 202, 214, 229–231, 234, 242, 245, 246 |
| Mở rộng | `$IFS`/`${IFS…}` (cả trong nháy — `tokenize` thay `IFS` trên toàn chuỗi), `~N`, brace bung ra `#`, `$$(`, thay lệnh trong chỉ số mảng | AUD-SEC-232, 233, 238–240, 243, 249 |
| Mã động | `bash -c`/`eval` thân không phải chữ nguyên văn, lệnh `"$@"`, ống vào shell, sed/awk chạy chữ từ stdin, ghi biến prompt khi bật `xtrace` | AUD-SEC-235, 237, 252, 287, 288, 290–292, 294–302 (PR sau) |
| Đăng review | `gh` đăng nội dung chỉ nhận thân chữ nguyên văn hoặc file chữ, không thay lệnh/biến/stdin/`cd` | AUD-SEC-180, 186, 191–193, 244, 253 (PR sau) |

Không áp tập con cho chữ guard tự dựng hoặc trích theo chiều chặt — bản viết lại thay biến, lệnh `e` của sed, chuỗi trong
lời gọi thực thi Python/Node, và mọi con của chúng (`ScanBudget.loose`). Bash không đọc nguyên văn các chữ này; luật nguy
hiểm cũ vẫn áp đủ cho chúng.

## Hệ quả

- Đo 2026-11-01 trên 1567 lệnh Bash thật của các phiên (khối `tool_use` tên `Bash` trong transcript
  `~/.claude/projects/<repo>/*.jsonl` của máy phiên — dữ liệu phiên, không đưa vào repo): so
  `apply_policy(bash_decision(cmd, root))` của guard `main` với guard có lớp mới, đếm lệnh đổi quyết định. Kết quả lớp từ
  vựng + mở rộng: **1** lệnh đổi (cho qua → chặn) — backtick không thoát trong chuỗi nháy kép, bash thực thi thật. Đếm thô
  bằng regex trước đó (~24 lệnh chứa backtick ngoài nháy đơn, D-299) gồm cả lệnh guard cũ đã chặn vì lý do khác; con số
  quyết định là phép so trước/sau. PR guard sau lặp lại phép so này (PLAN-harden-2026-11-01).
- Test cũ coi `` `date` `` hay `$'it\'s'` + brace là đối chứng hợp lệ đổi kỳ vọng thành chặn (chặt hơn, không nới).
- Tên lệnh hoàn toàn động (`g${x}h`) vẫn là giới hạn chung của phân tích tĩnh (D-051), không thuộc lớp này.
- Đường lùi: revert PR của từng lớp; lớp độc lập nhau, gỡ một lớp không mở lại lớp khác.
