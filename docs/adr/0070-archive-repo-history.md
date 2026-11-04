# ADR-0070: Lịch sử của chính repo khung vào `docs/archive/`; `framework/` giữ nguyên

- **Trạng thái:** Đã chấp nhận 2026-11-04 (chủ dự án: tài liệu ghi cả những điều đã bỏ — "bỏ lịch sử sang một thư mục
  khác", rồi "chốt phương án"; phiên chính chọn bản hẹp theo tiêu chí chất lượng cuối, ADR-0008 — **D-354**; ghi lúc đầu là D-344 rồi D-349, đánh số lại khi gộp `main` vì #438 đã dùng D-344, #439 dùng D-347…351).
- **Trạng thái triển khai:** đã làm cùng commit: 61 file dời bằng `git mv`, liên kết Markdown tương đối viết lại,
  `scripts/xt.py` `PLAN_ARCHIVE_DIR` + `_plan_paths`, `.ignore`, `xt.yaml` `merge_risk_paths`, test
  `tests/test_plan_files.py` và `tests/test_next_step.py`.
- **Ngày:** 2026-11-04.
- **Liên quan:** ADR-0043/0050 (trần byte; file lưu trữ không tính — tiền lệ T-3651, D-314), ADR-0001 và
  `framework/00-method/conventions.md` (ID ổn định, không tái sử dụng), P2 (nguồn kèm ngày), AGENTS.md §9 (không xoá dấu vết),
  ADR-0068 (PLAN lát A cần chỗ trong `docs/autopilot`).

## Bối cảnh

Repo khung tích luỹ lịch sử của chính nó trong cây làm việc: 34 file PLAN (274 KB, 26 đã đóng), 28 báo cáo audit, GO-NO-GO
các bản cũ, ghi chép đo đạc. Đo 2026-11-04: `docs/ops` 1,08 MB, `docs/autopilot` 0,73 MB — còn ≈ 2 KB dưới trần
`tests/test_docs_budget.py`, chặn việc lập PLAN mới. Agent tìm kiếm trong repo gặp lẫn báo cáo tháng 10 với luật hiện hành.
Chủ dự án hỏi có nên làm lại thành dự án "không lịch sử".

Dữ kiện quyết định: `scripts/install.py` chỉ chép `framework/` và các file `research/` mà module trỏ tới — `docs/` không tới
dự án đích. Lịch sử trong `framework/` thì đang có tác dụng: mục "Ngừng dùng" (72 dòng) giữ cam kết ID; đuôi "Nguồn + ngày"
là P2; câu lý do giữ luật guard khỏi bị "đơn giản hoá". Ngoài ra bộ cấp số task (`_plan_paths`) quét `docs/autopilot/PLAN*.md`
để không cấp trùng `T-NNNN`.

## Các phương án đã cân nhắc

1. **Bản hẹp:** dời lịch sử của chính repo khung (`docs/`) vào `docs/archive/`; giữ nguyên `framework/`.
2. Làm lại thành dự án mới không lịch sử: xoá ID "Ngừng dùng", đuôi Nguồn, ADR/CHANGELOG cũ, có thể cả lịch sử git.
3. Giữ nguyên.

## Quyết định

Chọn **phương án 1** (D-354).

- **Dời** (`git mv`, giữ tên, giữ lịch sử file): PLAN không còn task mở và không được `PROGRESS.md` nhắc là việc sống →
  `docs/archive/autopilot/`; báo cáo audit, GO-NO-GO, ghi chép đo đạc cũ ở `docs/ops/` → `docs/archive/ops/` (kèm
  `evidence/` mà chúng trỏ tới).
- **Giữ tại chỗ:** `docs/autopilot/PLAN.md` (đường mặc định của `loop`), PLAN còn task mở hoặc được PROGRESS nhắc, sổ audit
  (`AUDIT-STATUS*.md`), sổ quyết định (`DECISIONS*.md`), `STAGE.json`; báo cáo audit đầy đủ gần nhất
  (`AUDIT-REPORT-2026-11-02-full.md`, sổ audit dẫn 12 lần) và delta gần nhất; GO-NO-GO của `VERSION` hiện hành (`release-check`
  tìm ở `docs/ops`); đầu vào sống của công cụ (`REMEDIATION-PLAN-2026-10-19.md` cho `autonomy-bench`,
  `AUTONOMY-BASELINE.md`, `DEPENDENCIES.md`, `RUNBOOK-*`, `TARGETS.md`); toàn bộ `framework/`, `docs/adr/`, `research/`,
  `CHANGELOG*.md`.
- **Liên kết:** mọi liên kết Markdown tương đối trỏ tới file đã dời, hoặc nằm trong file đã dời, được viết lại cho vị trí mới
  (chỉ đường dẫn, không đổi chữ — kể cả trong ADR cũ và CHANGELOG); `check-links` là cổng. Nhắc tên file trong backtick ở văn
  bản lịch sử giữ nguyên (đúng tại thời điểm viết).
- **ID task không tái sử dụng:** `_plan_paths` quét thêm `PLAN_ARCHIVE_DIR`; test khẳng định số lớn nhất ≥ mọi `T-NNNN` trong
  kho và kho chỉ chứa PLAN đã đóng.
- **Đọc ít nhiễu:** `.ignore` ở gốc — ripgrep/fd (công cụ tìm kiếm của agent) mặc định bỏ qua `docs/archive/` và các file
  lưu trữ cũ (`CHANGELOG-ARCHIVE.md`, `AUDIT-STATUS-ARCHIVE.md`, `DECISIONS-*.md`); chỉ định đường dẫn vẫn tìm được. Không
  ảnh hưởng git, CI, `check-links`, installer.
- **Trần byte:** `docs/archive/` nằm ngoài các nhóm `DIR_CAPS` như file `*-ARCHIVE.md`/`DECISIONS-*.md` (tiền lệ T-3651:
  lưu trữ đóng băng, không tính; lưu trữ thêm là cách làm trần còn chỗ) — không đổi số trần nào.
- **Rủi ro merge:** `merge_risk_paths` thêm `docs/archive/autopilot/PLAN*.md` — PLAN trong kho vẫn chứa lệnh Gate, sửa nó
  không vào làn nhanh.

### Hệ quả

- Tốt: `docs/autopilot` và `docs/ops` chỉ còn việc sống và đầu vào của công cụ; PLAN lát A của ADR-0068 có chỗ; tìm kiếm mặc
  định không lẫn lịch sử; dự án đích không đổi gì (không file nào của `framework/` hay mẫu bị dời).
- Xấu / đánh đổi: liên kết cũ từ bên ngoài repo (URL GitHub tới `docs/ops/AUDIT-REPORT-…` ở `main`) sẽ 404 sau khi merge —
  permalink theo SHA vẫn sống; nhắc tên file trong backtick ở văn bản lịch sử trỏ vị trí cũ; người tìm lịch sử phải tìm đích
  danh trong `docs/archive/`.
- Không làm (phương án 2): xoá ID "Ngừng dùng" (dự án đích đang tick theo ID; ghép lại blueprint làm mục biến mất), bỏ đuôi
  Nguồn (P2), bỏ câu lý do (luật guard bị "đơn giản hoá"), rewrite lịch sử git (guard chặn; không làm ai đọc chậm hơn).

### Xác nhận

- `python3 scripts/check-links.py` exit 0; `python3 -m unittest tests.test_plan_files tests.test_next_step` xanh.
- `rg -l <mẫu>` không trả file trong `docs/archive/`; `rg -l <mẫu> docs/archive/` trả.
- Dời lượt sau: cùng luật ở §Quyết định, ghi D-NNN; xét dời `framework/` chỉ khi có số đo cho thấy nhiễu còn đáng kể.

## Ưu / nhược từng phương án

### 1. Bản hẹp (chọn)
- Tốt: lấy phần nhiễu lớn nhất với rủi ro thấp; đảo ngược được bằng `git mv`.
- Xấu: phải giữ quy tắc "cái gì được dời" và viết lại liên kết mỗi lượt.

### 2. Dự án không lịch sử
- Tốt: cây làm việc gọn nhất.
- Xấu: phá cam kết ID với dự án đích, vi phạm P2 và AGENTS.md §9, mất lý do của luật; rewrite git bị chặn.

### 3. Giữ nguyên
- Tốt: không tốn công.
- Xấu: `docs/autopilot` hết chỗ dưới trần; nhiễu tăng theo mỗi đợt audit.
