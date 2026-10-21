# ADR-0039: CI dự án đích tối thiểu số job; ruleset chỉ `quality` và `gitleaks`

- **Trạng thái:** Đã chấp nhận (chủ repo yêu cầu 2026-10-21, D-127); thay ADR-0034 phần "mỗi task cổng một job, song song tối
  đa" của mẫu CI dự án đích. Ruleset 2 check của ADR-0034/ADR-0036 giữ.
- **Trạng thái triển khai:** PLAN-3.13 Lát E — T-1851 (mẫu khung), T-1852 (hotel-manager), T-1853 (X-Company).
- **Ngày:** 2026-10-21
- **Làm rõ:** ADR-0034 (CI/E2E tối thiểu, song song tối đa), ADR-0036 (bỏ `merge-gate`), `WF-CI-001`, `WF-CI-024`, `WF-CI-025`.

## Bối cảnh

Đo trên hai PR nâng 3.13.0 (2026-10-21): X-Company chạy ~17 job CI, hotel-manager ~13 job, đẩy cùng lúc. Mọi job của X-Company
bắt đầu trong 11:01:49–11:02:54, riêng `e2e` (không có `needs`) bắt đầu 11:07:39 — chờ runner vì các repo của cùng tài khoản dùng
chung trần job đồng thời. Phần lớn job chỉ chạy 10–60 giây nhưng mỗi job tốn checkout, cài phụ thuộc và một runner. Fan-out
"mỗi task một job" (ADR-0034) giả định runner không giới hạn; khi có trần, nhiều job ngắn làm job dài nhất (e2e) xếp hàng.
Chủ repo yêu cầu: "giữ tối thiểu các job chạy trên dự án đích, ruleset chỉ có gitleaks và quality".

## Quyết định

1. **Mẫu `framework/templates/ci.yml` còn 3 job:** `gate` (một job chạy `dev-task.sh gate` — build → typecheck → lint → test kèm
   coverage — rồi kiểm của khung: `require lint test`, `doctor`, `ci-check`, tiêu đề PR), `e2e` (`matrix.shard: [1]`; tăng số shard
   chỉ khi đo e2e là đường dài nhất), `quality` (gom `needs: [gate, e2e]`, `if: always()`, đỏ khi job con không `success`; chạy
   kiểm `protection-guard` như một bước). Không còn job `build`/`typecheck`/`lint`/`test` shard/`coverage`/`checks`/`protection-guard`
   riêng. `gitleaks` ở `secret-scan.yml` như cũ.
2. **Ruleset dự án đích chỉ `quality` và `gitleaks`.** Job khác của dự án chạy trên PR phải nằm trong `quality.needs` (không thêm
   required check).
3. **Dự án đích đã có CI riêng:** gộp job ngắn (build, typecheck, lint, test, coverage, checks, audit…) vào một job `gate`; giữ job
   dài và độc lập (e2e shard, DAST, Lighthouse…) riêng dưới `quality`. Không bỏ kiểm nào — chỉ gộp job.

## Lý do

Quyết định của chủ repo; khớp số đo. Ít job: tổng thời gian runner giảm (một lần cài phụ thuộc), job dài nhận runner ngay, ruleset
ngắn khó lệch với job thật. Đổi lại: các kiểm trong `gate` chạy tuần tự (lint đỏ thì test không chạy trong cùng lượt) — chấp nhận
vì cổng cục bộ `dev-task.sh gate` cũng tuần tự và đã chạy trước khi đẩy.

## Hệ quả

- `WF-CI-024`/`WF-CI-025` đổi chữ (giữ ID/mức): song song chỉ giữa các job dài; đo trước khi thêm job hay shard.
- Repo khung giữ CI fan-out riêng của nó (không thuộc dự án đích).
- Dự án đích nhận mẫu qua `install.py --with-github` (`ci.yml` đã sửa → `.xtemplates-new` để gộp tay).

## Đường lùi

Khôi phục `framework/templates/ci.yml` bản 3.13.0; dự án đích revert PR gộp job.
