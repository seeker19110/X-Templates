# PROGRESS.md — Khung X-Templates

> Giai đoạn hiện tại: G8 Vận hành & tiến hoá (khung 3.33.0, pha `harden`) · Cập nhật: 2026-11-13 · Nhánh: fix/guard-parameter-parens

## Đang làm

- `T-3769` / `AUD-SEC-730`: từ chối ngoặc thô trong tham số Bash trước khi tokenizer mất đối số nguy hiểm;
  giữ literal, nháy kép và ngoặc thoát làm đối chứng (D-445).
- Gate task nguyên văn `python3 -m unittest tests.test_hooks tests.test_guard_fuzz`: exit 0, 479 test trong
  772.917 giây. Cổng `scripts/dev-task.sh gate-fast` hoàn tất exit 0 trong 1635.947 giây; lint, strict mypy và
  toàn bộ lớp test được cổng chọn đạt. Các lượt bị ngắt trước đó vẫn giữ là chưa kết luận, không tính PASS.
- [Số đo 505 lượt](research/evidence/2026-11-13-guard-parameter.json): không thay đổi quyết định trên 464 thân lệnh
  trong mẫu khớp nguồn; không suy thành bằng chứng cho toàn transcript. Fixture Git có kiểm giữ nguyên repo ngoài.

## Tiếp theo

1. Xuất bản lát này từ nền main, chờ CI và review đúng head; `pr next` quyết bước tiếp theo, không force-push.
2. Audit chỉ đóng khi có ref sửa được xác minh; hiện là bằng chứng của nhánh nguồn, chưa là PASS tích hợp.
3. Tiếp tục [PLAN-factory-e2e](docs/autopilot/PLAN-factory-e2e.md) ở các cây riêng. Pilot đã có bản dev thật;
   worker, phát hành, production và vòng học vẫn còn việc, chưa nghiệm thu toàn xưởng.

## Quyết định

- D-445 giữ precheck theo code-view có xét nháy và reader cân bằng sẵn có; không thêm parser hoặc đọc/chạy payload.
- Lý do chạm guard: tránh mất argv trước luật bảo vệ. Một số mã RULE_DENY chuyển sang BUDGET vẫn giữ deny ở cả
  default/strict và build/harden. Cạn ngăn xếp parser là lát riêng `T-3867`.
- Giữ mọi scope/timeout, Python ≥ 3.11, stdlib, C901 ≤ 10, strict mypy, coverage dòng/nhánh 100 % và trần byte.

## Bàn giao phiên

- Nền main `331145c1ce3b5a8fafaea3609012cb591342191d` (#529); nguồn guard và test đã đóng băng qua hai cổng.
  Không có formal clean review hoặc xác nhận merge của lát này.
- Cổng cuối đối chiếu 17 file trước/sau không đổi. Sau cổng chỉ cập nhật văn bản PROGRESS này và thân PR để ghi
  kết quả thật; mã, fixture, Gate và sổ bằng chứng máy giữ nguyên.
- Khi nhận kết quả CI, đọc đúng head và native exit; không dùng một phần log xanh hay kết quả cây khác để thay thế.
