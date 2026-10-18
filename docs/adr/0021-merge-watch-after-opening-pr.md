# ADR-0021: Mở PR xong chạy nền `merge-watch` (30 giây/lần)

- **Trạng thái:** Đã chấp nhận
- **Trạng thái triển khai:** Đã triển khai — `scripts/xt.py` `cmd_merge_watch`, `_merge_check_json`, `_watch_final`; quy
  định ở `AGENTS.md`, `framework/templates/AGENTS.md`, skill `/autopilot` bước 13, `LOOP-STOP-022`; test
  `tests/test_merge.py::MergeWatchTest`
- **Ngày:** 2026-10-18
- **Làm rõ bởi:** ADR-0022 (`--max-minutes` mặc định 120 → 240, D-027)
- **Làm rõ:** ADR-0013 (máy quyết khi nào merge), ADR-0015 (auto-merge) — quyết định D-026

## Bối cảnh

Chủ repo yêu cầu (2026-10-18): mỗi khi có PR thì kiểm `merge-check` định kỳ, cho cả khung lẫn dự án phát triển sau
này; đề xuất đầu 2 phút, rồi đổi thành **30 giây**. Trước đó agent chỉ chạy `merge-check` ở đầu mỗi vòng
autopilot, hoặc chờ sự kiện GitHub.

## Quyết định

1. Lệnh `xt.py merge-watch [--pr N] [--interval 30] [--max-minutes 120]`: gọi lại **nguyên** đường `merge-check`
   (xt.yaml, ngoại lệ cứng, REST — không có luật riêng) mỗi `--interval` giây tới khi verdict ≠ `wait`.
2. Exit: 0 = PR đã merge hoặc verdict `merge`; 1 = cần hành động (`update`/`fix`/`human`/đóng không merge); 2 = lỗi
   đọc PR 3 lần liền (mạng chập chờn một hai lần không dừng); 3 = hết `--max-minutes` mà PR vẫn chờ.
3. Agent chạy lệnh **nền** (`run_in_background`) ngay sau khi mở PR rồi làm việc khác; lệnh thoát thì phiên được
   đánh thức. Harness không chạy nền được thì dùng `merge-check` mỗi vòng như trước.
4. Là bước bắt buộc cho mọi PR của repo khung và dự án đích (mẫu `AGENTS.md`), không phải khoá cấu hình.

## Lý do

- Vòng lặp nằm trong code: không tốn token mỗi 30 giây, test được bằng đồng hồ giả, dùng được ở mọi harness.
- Dùng lại `merge-check` nên mọi luật merge (ADR-0015/0016/0019/0020) áp y như cũ.
- Chi phí: mỗi lần kiểm gọi khoảng 6 lệnh REST, 30 giây/lần ≈ 720 yêu cầu/giờ cho mỗi PR, dưới hạn 5000/giờ của `gh`
  đã đăng nhập. Nhiều PR mở song song thì nâng `--interval`.

## Các phương án đã cân nhắc

- **`/loop 30s` trong phiên**: mỗi lần kiểm là một lượt model (đốt token), chỉ có ở Claude Code, hết hạn 7 ngày. Loại.
- **Chỉ dựa vào sự kiện GitHub và auto-merge**: trái yêu cầu chủ repo; sự kiện không phủ commit-status và nhánh tụt sau
  nhánh đích. Loại.

## Hệ quả

- `merge-watch` không merge gì: ở L3 GitHub tự merge, lệnh chỉ báo kết quả; dưới L3 agent chạy `next` khi exit 0.
- Quá 120 phút (mặc định) thì exit 3 để phiên không bị treo; chạy lại khi cần.
