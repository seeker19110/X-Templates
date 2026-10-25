---
name: autopilot
description: Chạy tự động pha BUILD từ yêu cầu đến "build xong" theo khung X-Templates — kế hoạch gọn (G0–G4 mức S), phiên chính tự duyệt theo tiêu chí chất lượng cuối, rồi vòng lặp có bằng chứng máy (xt.py loop) trong MỘT phiên tới khi done/blocked/budget; không audit sâu, không review, không phát hành — việc đó là /complete. Dùng khi người dùng mô tả dự án/tính năng mới, muốn "làm tự động đến khi xong", hoặc gõ /autopilot.
argument-hint: "[mô tả yêu cầu hoặc đường dẫn PROJECT.md]"
---

# /autopilot — pha build: nhanh nhất trên sàn máy, dừng ở "build xong"

Giao thức đầy đủ: `<FW>/11-autonomous-loop/README.md`; file này là checklist pha build (ADR-0046). `<FW>` = `.xtemplates/framework` (dự án đích) hoặc `framework` (repo khung); `<XT>` = `python3 .xtemplates/scripts/xt.py` (hoặc `python3 scripts/xt.py`). Máy in sẵn bước kế — làm theo, không đoán. Một phiên đến khi build xong (ADR-0009). Hoàn thiện, phát hành: `/complete`.
**Sàn không bỏ** (`stop-points-and-escalation.md` §Điểm dừng — không phải rào cản tốc độ): guard chặn không đảo ngược/đối ngoại/bí mật; điểm dừng tiền/dữ liệu/khoá thật (`loop defer`); Gate máy mỗi task; cổng commit; CI xanh để merge; `verify --all` trước khi dừng. Bị chặn là kết luận.

## Bước 0 — chuẩn bị
1. Tên phiên `<Tên repo> — <tên nhánh>` (SessionStart in sẵn; ở nhánh chính thì tạo nhánh `<type>/<mô-tả>` trước).
2. `<XT> doctor --fix` — ✗ còn lại → báo người **một lần** lệnh `install.py`, làm tiếp; ⚠ là việc của phiên (vd `xt.yaml` trống → task đầu điền lệnh thật).
3. Chế độ quyền Auto. Đọc `delivery_phase` trong `xt.yaml`: `build` → checklist này; `harden` (repo khung, dự án đã phát hành) → thêm luật PR của `/complete` bước 4; **không tự đổi pha** (ADR-0037).

## Pha 1 — kế hoạch gọn (G0–G4 mức S, `lifecycle.md` quy tắc 6), không code
Đọc repo trước (stack/CI/test từ file thật, không hỏi điều đã có) → `<XT> compose … --out BLUEPRINT.md` (không tick) → `docs/autopilot/PLAN.md` (đợt sau: `PLAN-<đợt>.md`) theo mẫu `<FW>/templates/PLAN.md`: 4 dòng Khung đầu PLAN (vấn đề · người dùng · 1 chỉ số · không làm) khi chưa có `PROJECT.md`; task ≤ 1 ngày, mỗi task một Gate máy kiểm + Given/When/Then và ca biên ngắn trong dòng task, `(sau: …; files: …)`, `(exec: deep)` cho việc khó/rủi ro; T-001 dựng nền (xt.yaml lệnh thật, CI, MUST sàn bảo mật/cấu hình/dữ liệu); Ủy quyền production nếu cần. `researcher` + ADR chỉ khi **thêm** phụ thuộc/dịch vụ/luật ngành; SPEC riêng chỉ cho nghiệp vụ không tầm thường (tiền, quyền, trạng thái); thiết kế chỉ phần code cần (ADR-0041) — phần đầy đủ trả ở `/complete`. **Tự duyệt PLAN**: tóm tắt ≤ 30 dòng đầu PLAN, `<XT> loop decide --question "Duyệt PLAN …" …`, báo người, làm tiếp không chờ.
Mọi điểm quyết định (spec hở, công nghệ, thiết kế, phạm vi, bảo mật/pháp lý mơ hồ): tự duyệt (AGENTS.md §Điểm quyết định), `<XT> loop decide …` → D-NNN; mặc định tự host.

## Pha 2 — vòng lặp có bằng chứng (G5–G6)
4. `<XT> loop init --plan docs/autopilot/PLAN.md --blueprint BLUEPRINT.md --single-session [--hours <H>]` (exit 2 "đang có vòng" → `<XT> loop resume`, không tự `--force`).
5. Mỗi vòng: `<XT> loop status --json` → làm đúng `task` (giao subagent theo trường `executor`, trừ hàng "Làm trực tiếp" (`LOOP-ORCH-020`); `milestone_audit: g7` → làm tiếp; `now` → audit delta trước, 🔴/🟠 thành task) → Gate chạy **y nguyên** qua `<XT> loop record --task T-NNN [--executor <agent>] -- '<Gate>'` → exit 0: máy tự tick `[x]`, commit nhỏ; exit ≠ 0: sửa — lần 2 cùng lỗi → đổi cách (D-NNN), máy chuyển cấp `executor-deep` sau 2 lần đỏ, BLOCKED sau 3. Không nới cổng.
6. Lát xong → một PR: `PROGRESS.md` (≤ 8 KB) vào commit cuối → đẩy **một lần** (CI là cổng — ADR-0041), `<XT> pr title-check '<tiêu đề>'`, mở PR → `<XT> pr next --pr <N>` → làm đúng `do` (build: merge ghim head khi CI xanh, review ghi nợ — ADR-0037) → `<XT> merge-watch --pr <N>` nền, làm lát kế ngay; PR đổi → lại `pr next`. Push thêm: gói sửa vào **một** commit. Không `sleep`. Pha harden: `/complete` bước 4.
7. Blueprint: tick `[x]` mục task vừa chứng minh kèm `— Kiểm: `<lệnh>`` chạy lại được (không có lệnh: `— Bằng chứng: <file|URL>`); `[~] — Không áp dụng: <điều kiện>`; MUST muốn miễn → `loop defer`. MUST còn mở không chặn `done` ở pha build — trả ở `/complete`.
8. Việc cần người (AGENTS.md §Điểm dừng): `<XT> loop defer --task <ID> --reason "…"` rồi làm tiếp; mọi việc còn lại phụ thuộc → `<XT> loop block --reason "…"`. Việc production: `<XT> grant-check <nhóm> khoá=giá trị` exit 0 mới làm.
9. Context đầy → compaction (checkpoint tự ghi); ≥ 80 % trần vòng/giờ/tiền → Bàn giao vào PROGRESS, commit + push.

## Kết thúc — "build xong", chưa phát hành
- Stop hook quyết: `continue`/`verify` → làm theo lý do nó in; `done`/`done-pending-human`/`blocked`/`budget` → dừng.
- `done` = mọi task có bằng chứng xanh + `verify --all` khớp cây + PR của lát đã merge → `<XT> loop stats`, `<XT> feedback collect` → báo cáo ≤ 20 dòng: đã làm · bằng chứng · D-NNN · nợ (số MUST mở, review hoãn) · còn treo (việc chờ người) · dòng bắt buộc **"Chưa phát hành — gõ `/complete`"** (nên phiên mới sau `/handover`). `blocked`/`budget`: lý do + bước kế, không khai "xong".
