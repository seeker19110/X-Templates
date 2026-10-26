# ADR-0050: Nâng trần tổng byte thư mục thêm 1 MiB mỗi nhóm

- **Trạng thái:** Đã chấp nhận (chủ repo 2026-10-26: "nâng lên thêm 1MB đi")
- **Trạng thái triển khai:** Đã triển khai — `tests/test_docs_budget.py` `DIR_CAPS` (trần cũ + 1 048 576 B).
- **Ngày:** 2026-10-26
- **Làm rõ:** ADR-0043 (đóng băng bề mặt 3.x — vẫn giữ trần, chỉ đổi số), D-111 (trần từng file hướng dẫn — không đổi).

## Bối cảnh

Đo 2026-10-26 (file git theo dõi, `main` + PR #282): `scripts/` 711 824 / 711 855 B (còn 31 B), `.claude/hooks/`
369 274 / 369 393 B (còn 119 B), `framework/11-autonomous-loop/` 232 297 / 232 307 B (còn 10 B). Từ PR #274 tới #282, mỗi
bản vá bảo mật guard/hook phải cắt chú thích cùng thư mục để bù chỗ. Chú thích bị cắt thường là ID audit và lý do của luật
guard, nên cổng đang đẩy dấu vết truy nguyên ra khỏi mã. Đó là mất chất lượng mà ADR-0043 không định đổi lấy.

## Phương án đã xét

1. **+1 MiB mỗi nhóm** (chủ repo chọn). Hết sức ép cắt chú thích trong nhiều bản tới. Nhược: trần gần như không còn ép bề
   mặt, nên chất lượng chuyển sang dựa vào review và C901.
2. **+5 % mỗi nhóm** (đề xuất của phiên chính). Thêm khoảng 18–36 KB, vẫn ép. Nhược: sẽ sát trần lại sau vài lát.
3. **Giữ băng** và tiếp tục cắt chú thích. Nhược: tiếp tục mất truy nguyên như đã nêu.

## Quyết định

Chọn **phương án 1** theo quyết định của chủ repo: mỗi trần trong `DIR_CAPS` = trần ADR-0043 + 1 048 576 B. Trần từng file
nạp đầu phiên (`CAPS`, D-111) giữ nguyên, vì mỗi byte ở đó tốn ngữ cảnh mọi phiên. Mở băng tiếp theo vẫn cần ADR mới.

## Hệ quả

- Tốt: bản vá không còn phải cắt chú thích để bù; ID audit và lý do giữ lại cạnh mã.
- Xấu: test trần thư mục gần như không còn ép bề mặt; tăng trưởng mã chỉ còn review và C901 ≤ 10 giữ.
- Theo dõi: xét lại cùng mốc hàng rào 2027-01-21. Nếu một nhóm vượt 2× kích thước 2026-10-26 trước mốc đó thì phải có ADR
  xét lại.
- Đường lùi: revert commit này (ADR-0043 dùng lại số cũ).
