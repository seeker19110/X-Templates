# Dự án đích kéo phản hồi về khung

> Danh sách repo đã cài khung (`.xtemplates/`) mà Routine hằng tuần của repo này đọc `docs/xtemplates-feedback/` để gộp
> phản hồi (ADR-0010, `framework/11-autonomous-loop/framework-feedback.md`). Một dòng một repo, dạng `- owner/repo — ghi chú`.
> Repo không còn dùng khung: xoá dòng. Repo private vẫn đọc được nếu phiên có quyền; báo cáo chỉ trích nội dung đã qua `redact`.

## Danh sách

- seeker19110/hotel-manager — có `.xtemplates/` (3.15.1), kiểm 2026-10-15; 2026-10-23: 188 FB-*.md
- seeker19110/X-Company — có `.xtemplates/` (3.15.1), kiểm 2026-10-23: 91 FB-*.md
- seeker19110/xboss — có `.xtemplates/` (2.0.0), kiểm 2026-10-23: 4 FB-*.md
- seeker19110/dhcb — có `.xtemplates/` (3.15.3), kiểm 2026-10-23: chưa có phản hồi

Lần gộp 2026-10-23 (T-2410, `feedback aggregate --from` bản clone nông cả 4 repo public, exit 0): đủ ngưỡng 63 nhóm —
`mien-tru` 47, `cong-cu` 10, `hook-chan-nham` 5, `hook-lot` 1; dưới ngưỡng 61. Nhóm `cong-cu` đủ ngưỡng cần phân loại
(đã sửa / còn lỗi) thành task: `merge-check` (phân trang `/repositories/{id}` bị proxy 403), `blueprint-status`, `doctor`,
`loop init` (×2), `pr steward`, `feedback collect`, `loop decide`, `loop record` (pipefail — đã sửa `1a877b0`),
`loop record/status` (worktree). Nội dung phản hồi giữ ở repo dự án (dữ liệu dự án), không chép vào đây.

## Đã xét, không đưa vào

- seeker19110/x-hotel-manager — 2026-10-15 `main` là bản sao lịch sử của chính repo khung (trùng commit `0d1b62c`), chưa cài khung dạng `.xtemplates/`.
