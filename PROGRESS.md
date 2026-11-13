# PROGRESS.md — Khung X-Templates

> Giai đoạn hiện tại: G8 Vận hành & tiến hoá (khung 3.33.0, pha `harden`) · Cập nhật: 2026-11-13 · Nhánh: feat/factory-new-project

## Đang làm

- Lát F-111 của [PLAN-factory-e2e](docs/autopilot/PLAN-factory-e2e.md): tạo dự án mới bằng `install.py --new`;
  [SPEC-intake](docs/specs/SPEC-factory-intake.md) giữ ranh giới dự án mới, không nhận dữ liệu có sẵn.
- `T-3845` đã qua Gate thật `python3 -m unittest tests.test_install_new`: 46 test, 264.308 giây, exit 0.
  Kiểm độc lập các ca race/identity đạt; 14 helper mới phủ dòng và nhánh 100 %. Đang xuất bản lát này.
- Cổng `scripts/dev-task.sh gate-fast` chuẩn exit 0 trong 1820.843 giây; lint/format, strict mypy và toàn bộ test
  được cổng chọn đạt. 675 tracked files và test mới không đổi trước/sau; không override hay retry.

## Tiếp theo

1. Mở PR xếp sau #532, đính bằng chứng hai cổng đã xanh và chờ CI/review đúng head.
2. Tích hợp với receipt dev, nghiệm thu khoá, UI và skill một bước; pilot ở cây sản phẩm riêng đã có dev và bundle tái lập.
3. Hoàn tất worker, xác minh nguồn phát hành, catalog thiết lập, production và vòng học theo PLAN. Không coi lát
   tạo dự án là nghiệm thu toàn xưởng; không ký GO khi thiếu bằng chứng hoặc quyền thật.

## Quyết định

- D-452/D-453: bootstrap Git và `doctor --offline` không phụ thuộc mạng, cấu hình Git cá nhân hay hooks ngoài.
- D-455/D-460: nhận đích bằng `mkdir` độc quyền trước bootstrap, giữ cwd và inode `.git`; lỗi giữ dữ liệu chẩn đoán.
  Không staging/rename đè thư mục xuất hiện đồng thời. Chi tiết trong [sổ quyết định](docs/autopilot/DECISIONS.md).
- Giữ Python ≥ 3.11, stdlib, `mypy --strict`, coverage dòng và nhánh 100 %, C901 ≤ 10 và mọi trần byte hiện có.

## Bàn giao phiên

- `main` nền `331145c1ce3b5a8fafaea3609012cb591342191d` (#529); HEAD dùng tiền đề archive của #532
  (chưa merge). Nguồn installer đã đóng băng;
  bằng chứng task do `loop record` ghi, không sửa tay `.autopilot`.
- Chưa có formal clean review hay xác nhận merge. `pr next` quyết bước tiếp theo, không force-push hoặc merge
  thiếu điều kiện. Sau cổng chỉ cập nhật PROGRESS để ghi kết quả thật; source, test, cấu hình và evidence giữ nguyên.
- Nguồn phát triển cục bộ không mang xác nhận attestation phát hành. Các khoá trả phí, dữ liệu thật và production
  được gom vào checklist sau dev; chưa có thao tác thuộc các nhóm đó trong lát này.
