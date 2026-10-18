# PROGRESS.md — Khung X-Templates

> Giai đoạn hiện tại: G8 Vận hành & tiến hoá (khung v2 đã phát hành) · Cập nhật: 2026-10-18 · Nhánh: seeker/quirky-knuth-v0uphi

## Đang làm
- Phát hành 3.0.0 (tag `v3.0.0`) + 3.0.1 (#115: mẫu PR/Dependabot cho dự án đích, merge-gate qua zizmor, doctor quét `.github/`). hotel-manager đã nâng 3.0.0 (hotel-manager#49, D-069 của dự án); x-company: chủ repo không cài. Chờ chủ repo: HAR-036/041, SEC-026, CI-006/007/009, SEC-043 (audit dự án con #97).

## Tiếp theo
1. Dự án thật đầu tiên: `seeker19110/hotel-manager` (đã cài `.xtemplates/`) — đo MUST hay bị miễn qua `feedback collect` + Routine. `seeker19110/x-hotel-manager` chỉ chứa bản sao lịch sử khung: chờ chủ repo quyết dọn hay tạo repo mới, và mô tả dự án con.
2. hotel-manager: chủ repo thêm `merge-gate` vào required check của ruleset `main` trên GitHub; khi nâng 3.0.1 thì giữ mẫu PR/Dependabot riêng (đã tuỳ biến), `merge-gate.yml` đã trùng bản 3.0.1.
3. Admin: tự kiểm Dependabot security updates (proxy chặn API); ô "extra approval for unattributed changes" của ruleset `main` còn bật — khác `.github/rulesets/main.json`, vô hại khi 0 approval.
4. Giới hạn đã biết, chưa sửa: guard không thấy lệnh trong alias/biến chứa cờ; CLI container ngoài docker/podman (`kubectl exec`, `nerdctl`, AUD-SEC-042); `xt.py` có thể lấy `$HOME` dotfiles (`.git`) làm gốc khi dự án chưa có dấu hiệu khung (README).
5. Giữ cổng: C901 ≤ 10, `mypy --strict`, coverage dòng + nhánh 100%, `changelog-check` — hàm mới vượt thì tách, không `noqa`/pragma.

6. Chưa làm từ đề xuất tối ưu autopilot: sàn quyền token (chủ repo đổi quyền token/tài khoản), đóng gói `xt.pyz` (ADR-0010 cần ≥ 2 dự án đích). Nợ 🟢 review #110 đã sửa.

## Quyết định
- 2026-10-13 Khung v2 = thư viện yêu cầu có ID + máy ghép blueprint + máy kiểm "xong" — ADR-0001.
- 2026-10-13 Harness: hook fail-open về luồng, fail-closed về hành động nguy hiểm; Stop hook đọc bằng chứng — ADR-0002.
- 2026-10-13 Quy mô S chỉ giữ MUST của baseline/hồ sơ/ngành — ADR-0003.
- 2026-10-13 Luật dữ liệu VN hiện hành: Luật 91/2025/QH15 + NĐ 356/2025 (thay NĐ 13/2023 từ 01/01/2026); Luật ANM 116/2025 (01/07/2026).
- 2026-10-14 OWASP LLM Top 10 ấn bản 2026 (04/08/2026); EU AI Act Đ.50 áp dụng 02/08/2026; bản đồ "một chủ đề một nhà" ghi vào conventions.
- 2026-10-14 Dogfood: compose giữ trạng thái theo ID; sàn Python 3.11; CI chạy đúng `dev-task.sh gate`; ruff + mypy ghim.
- 2026-10-14 Quy mô M: tối đa 4 MUST mỗi module/chuẩn, phần vượt `MUST@L`; web-app M 1.094 → 470 — ADR-0004.
- 2026-10-13 Mặc định OSI: OpenTofu (MPL-2.0) thay Terraform (BUSL-1.1), Valkey thay Redis 8; Lighthouse CI giữ có cảnh báo, ghi phương án thay.
- 2026-10-14 PROGRESS chỉ ghi SHA trên `main`: squash-merge làm SHA của nhánh PR không còn là tổ tiên HEAD — `xt.py progress-check` trong cổng `lint` sẽ đỏ.
- 2026-10-14 Audit có máy đỡ: sổ `docs/ops/AUDIT-STATUS.md` máy đọc, `audit check --strict` = Definition of Complete — ADR-0005.
- Nợ kỹ thuật chấp nhận: chọn 4 MUST/module là phán đoán, chờ dữ liệu miễn trừ từ dự án thật; số điều cụ thể của NĐ 356/2025 chưa đối chiếu bản gốc — trả khi audit dự án thật.
- 2026-10-14 Repo khung: cổng `typecheck` = `mypy --strict`; cổng `test` đòi coverage dòng + nhánh 100% (cả subprocess) — mã chết thì xoá, không dùng `pragma: no cover` trừ khi không thể chạy tới.
- 2026-10-14 Repo đổi tên X-stored → X-Templates; giữ `.xstored/`, `xs.py`, `XS_*` — ADR-0006 (bị thay bởi ADR-0007).
- 2026-10-15 Định danh kỹ thuật theo tên mới: `.xtemplates/`, `xt.py`, `xt.yaml`, `XT_*`; `install.py` tự chuyển bản ≤ 2.x, liệt kê file còn tên cũ; tài liệu lịch sử giữ tên cũ; bản kế tiếp 3.0.0 — ADR-0007.
- 2026-10-14 `LOOP-HARNESS-012` → 018: không biến tắt hook riêng; tắt có chủ đích qua `disableAllHooks` của Claude Code; test fail-open 5 hook.
- 2026-10-15 Commit/PR không ghi tên model hay URL phiên AI (giữ AGENTS.md §3; AUD-HAR-017).
- 2026-10-15 Tag phát hành tạo bằng workflow `release-tag.yml` (proxy chặn push tag từ phiên agent); `v2.0.0` → `55de4d1`.
- 2026-10-15 Guard hỏi khi mở phiên Claude bỏ qua hook (`--bare`, `--settings`, `disableAllHooks`…); cổng commit chạy trước khi hỏi người.
- 2026-10-15 `xt.py changelog-check` trong cổng `lint`; gốc dự án: `CLAUDE_PROJECT_DIR` → cha `.xtemplates` → dấu hiệu khung → `.git` → cwd.

- 2026-10-15 Phiên chính tự duyệt điểm quyết định chuyên môn theo 5 tiêu chí, ghi `loop decide` D-NNN; mặc định tự host — ADR-0008.
- 2026-10-15 Autopilot một phiên đến khi xong: context đầy → compaction + checkpoint (không bàn giao); bàn giao chỉ khi ≥ 80% trần vòng/giờ/tiền; việc cần người `loop defer`, gom cuối phiên; chạy bằng `claude --permission-mode auto` — ADR-0009.
- 2026-10-15 Phản hồi dự án đích → khung qua `FB-NNN` + Routine tuần → PR nháp, đủ ngưỡng ≥ 2 dự án hoặc tái hiện — ADR-0010.
- 2026-10-16 Audit khung trước `/autopilot`: `xt.py doctor --fix` là việc đầu tiên; `--fix` chỉ sửa phần đảo ngược được, hook/settings để người (`install.py`); `loop init` cảnh báo, không chặn (fail-open về luồng) — `LOOP-HARNESS-020`.
- 2026-10-17 CI: gỡ `portability.yml` (macOS bash 3.2, chỉ chạy sau merge từ 2026-10-16) theo yêu cầu chủ repo — CI không còn kiểm macOS (bash 3.2, sed/awk BSD, `python3` 3.9 hệ thống).
- 2026-10-16 Trong vòng autopilot, `lint`/`test` rỗng hoặc no-op (kể cả chỉ có comment) làm cổng đỏ — ADR-0011.
- 2026-10-16 Blueprint chỉ MUST theo quy mô, SHOULD/MAY ở BACKLOG; trần vòng một phiên chỉ đếm task — ADR-0012.
- 2026-10-16 Máy quyết khi nào merge (`xt.py merge-check`, REST); mỗi lát code một PR — ADR-0013, ADR-0014, D-010.
- 2026-10-16 L3 auto-merge (ADR-0015); ngoại lệ cứng người merge (ADR-0016), bỏ được bằng `merge_hard_exceptions: auto` (ADR-0020); nay merge theo làn (ADR-0024/0025).
- 2026-10-17 Guard: lệnh trong container chỉ xét luật ra khỏi máy dev; push vào PR đang auto-merge → chạy lại `merge-check` (D-015).
- 2026-10-17 Hook nạp guard/xt bằng import, pycache ở `~/.cache/xtemplates` (#93).
- 2026-10-18 Autopilot bớt lời khai: blueprint `[x]` mang `— Kiểm:` chạy lại (LOOP-DESIGN-023, D-034); sàn Gate M/L bằng khoá khai báo `format_check`/`coverage` (LOOP-HARNESS-023, D-035); số đo `loop stats` (LOOP-DESIGN-024, D-037); merge theo làn trong code `pr next` (ADR-0025, D-038). Chủ repo đừng merge tay PR đang chờ review (#107 merge ở commit cũ → #108).
## Bàn giao phiên
- 2026-10-18 · Commit cuối trên `main`: `f3a855f` (#115); tag `v3.0.0` → `0f49e9f`, `v2.0.0` → `55de4d1`; SHA quét audit `536584f` (delta #68–#80).
- Lệnh kiểm nhanh: `scripts/dev-task.sh gate` (`pip install --require-hashes -r requirements-dev.txt`, cần shellcheck; hook cổng commit dùng python hệ thống).
- Autopilot: PLAN T-1101…T-1104 done, `loop stats`: 4 task, 10 lần chạy, xanh lần đầu 4/4. Đang chặn: không.
- Câu hỏi cần người: mục chờ chủ repo ở Đang làm; Tiếp theo 1 (`x-hotel-manager`), 6 (quyền token).
