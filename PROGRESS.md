# PROGRESS.md — Khung X-Templates

> Giai đoạn hiện tại: G8 Vận hành & tiến hoá (khung 3.4.1 — tag sau PR phát hành) · Cập nhật: 2026-10-18 · Nhánh: main

## Đang làm
- Rà `seeker19110/stored` 2026-10-18 (`10ecf8b..a1a1f51`): #117 guard (Gate/`Kiểm:`/`xt.yaml` qua guard, CLI agent tự duyệt, `--no-verify`, git hook/khoá chạy lệnh), #118 mục checklist mới, PR harness (`loop init` khoá, doctor thử guard, `claude_min_version`). Chờ chủ repo: HAR-036/041, SEC-026, CI-006/007/009, SEC-043 (#97).

## Tiếp theo
1. Nâng hotel-manager, X-Company lên 3.4.1. Còn (D-043): ghi công AI qua MCP/PR (máy chủ gắn URL phiên vào thân PR); kiểm tiêu đề PR ≤ 72 cục bộ; task `[perf]` trong `loop`.
2. hotel-manager: chủ repo thêm `merge-gate` vào required check ruleset `main`. `x-hotel-manager`: chờ chủ repo quyết dọn/tạo mới.
3. Hoãn từ rà stored: ép báo "đã đo/chưa đo" cho task UI trong `loop` (`LOOP-DESIGN-021` chưa có máy đỡ) — cần thiết kế bằng chứng ảnh chụp; sàn quyền token; `xt.pyz` (ADR-0010).
4. Giới hạn đã biết của guard: ghép tên hàm lúc chạy, giải mã qua `$(…)` (né cố ý, D-051); env `GIT_CONFIG_*`; CLI container ngoài docker/podman (AUD-SEC-042).
5. Admin: Dependabot security updates (proxy chặn API); ô "extra approval for unattributed changes" của ruleset `main`.
6. Giữ cổng: C901 ≤ 10, `mypy --strict`, coverage dòng + nhánh 100%, `changelog-check` — không `noqa`/pragma.

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
- 2026-10-18 Vòng tối ưu hiệu năng có máy quyết (`LOOP-OPT`, `xt.py perf`, D-041/042).
- 2026-10-18 Bộ tấn công guard (D-044); `pr reviewed --clean` đòi reviewer khác họ model (D-045); ghi tay `.autopilot/` bị chặn — ADR-0026 (D-046).
- 2026-10-18 Guard: ngân sách quét (vượt trần → chặn, D-050); biến tính được giá trị + lệnh mã hoá vào shell (D-052); cổng UI `xt.py contrast`/`vendor-check` + mẫu `verify-render` (D-048/049).
- 2026-10-18 Autopilot bớt lời khai: blueprint `[x]` mang `— Kiểm:` chạy lại (LOOP-DESIGN-023, D-034); sàn Gate M/L bằng khoá khai báo `format_check`/`coverage` (LOOP-HARNESS-023, D-035); số đo `loop stats` (LOOP-DESIGN-024, D-037); merge theo làn trong code `pr next` (ADR-0025, D-038). Chủ repo đừng merge tay PR đang chờ review (#107 merge ở commit cũ → #108).
## Bàn giao phiên
- 2026-10-18 · Commit cuối trên `main`: `2a4f4fe` (#138); tag `v3.4.1` (sau PR này), `v3.4.0` → `b20e6e6`, `v3.3.0` → `27e6bc3`, `v3.2.0` → `94858f7`, `v3.1.1` → `3a1c379`; SHA quét audit `536584f` (delta #68–#80).
- Lệnh kiểm nhanh: `scripts/dev-task.sh gate` (`pip install --require-hashes -r requirements-dev.txt`, cần shellcheck; hook cổng commit dùng python hệ thống).
- Autopilot: PLAN T-1201…T-1206 (3.4.1, D-051…053). Đang chặn: không.
- Câu hỏi cần người: Đang làm (chờ chủ repo), Tiếp theo 2.
