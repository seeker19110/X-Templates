# PROGRESS.md — Khung X-Templates

> Giai đoạn hiện tại: G8 Vận hành & tiến hoá (khung v2 đã phát hành) · Cập nhật: 2026-10-16 · Nhánh: claude/intelligent-meitner-vzr6r5

## Đang làm
- Audit delta #68–#80 (2026-10-17): 0 🔴, 4 🟠 sửa ở #81; autopilot T-801…T-804 sửa 🟢 guard (AUD-SEC-041, HAR-047) + đợt 2 tài liệu ở #82/#83; `audit check --strict` exit 0 (27 🟢 nợ). Chờ người: AUD-CI-009 (job Python 3.9 trong CI).

## Tiếp theo
1. Dự án thật đầu tiên: `seeker19110/hotel-manager` (đã cài `.xtemplates/`) — đo MUST hay bị miễn qua `feedback collect` + Routine. `seeker19110/x-hotel-manager` chỉ chứa bản sao lịch sử khung: chờ chủ repo quyết dọn hay tạo repo mới, và mô tả dự án con.
2. Dự án đã cài khung: chạy lại `install.py` (gộp tay `*.xtemplates-new`, ADR-0008) để nhận `.xtemplates/`/`xt.yaml` (ADR-0007), guard/hook mới, `PreCompact`, `doctor`; rồi `python3 .xtemplates/scripts/xt.py doctor --fix`.
3. Admin: tự kiểm Dependabot security updates (proxy chặn API); ô "extra approval for unattributed changes" của ruleset `main` còn bật — khác `.github/rulesets/main.json`, vô hại khi 0 approval.
4. Giới hạn đã biết, chưa sửa: guard không thấy lệnh trong alias/biến chứa cờ; CLI container ngoài docker/podman (`kubectl exec`, `nerdctl`, AUD-SEC-042); `xt.py` có thể lấy `$HOME` dotfiles (`.git`) làm gốc khi dự án chưa có dấu hiệu khung (README).
5. Giữ cổng: C901 ≤ 10, `mypy --strict`, coverage dòng + nhánh 100%, `changelog-check` — hàm mới vượt thì tách, không `noqa`/pragma.

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
- 2026-10-14 Sửa audit 5 đợt (#20–#24): `dev-task.sh` lấy gốc dự án đúng ở `.xstored/`; hook phân tích lệnh bằng `guard.py` (shlex); install gộp hook + manifest hash; công cụ cổng khoá hash + `dep-audit`; WF-DOC-004 bỏ điều kiện "nhánh còn trên remote" (xung đột squash).
- 2026-10-14 9 mục trùng chủ đề chuyển `MAY` "gộp vào" nhà (ID giữ, CHANGELOG).
- 2026-10-14 Repo khung: cổng `typecheck` = `mypy --strict`; cổng `test` đòi coverage dòng + nhánh 100% (cả subprocess) — mã chết thì xoá, không dùng `pragma: no cover` trừ khi không thể chạy tới.
- 2026-10-14 Repo đổi tên X-stored → X-Templates; giữ `.xstored/`, `xs.py`, `XS_*` — ADR-0006 (bị thay bởi ADR-0007).
- 2026-10-15 Định danh kỹ thuật theo tên mới: `.xtemplates/`, `xt.py`, `xt.yaml`, `XT_*`; `install.py` tự chuyển bản ≤ 2.x, liệt kê file còn tên cũ; tài liệu lịch sử giữ tên cũ; bản kế tiếp 3.0.0 — ADR-0007.
- 2026-10-14 `LOOP-HARNESS-012` → 018: không biến tắt hook riêng; tắt có chủ đích qua `disableAllHooks` của Claude Code; test fail-open 5 hook.
- 2026-10-15 Commit/PR không ghi tên model hay URL phiên AI (giữ AGENTS.md §3; AUD-HAR-017).
- 2026-10-15 Tag phát hành tạo bằng workflow `release-tag.yml` (proxy chặn push tag từ phiên agent); `v2.0.0` → `55de4d1`.
- 2026-10-15 Guard hỏi khi mở phiên Claude bỏ qua hook (`--bare`, `--settings`, `disableAllHooks`…); cổng commit chạy trước khi hỏi người.
- 2026-10-15 `xt.py changelog-check` trong cổng `lint`; gốc dự án: `CLAUDE_PROJECT_DIR` → cha `.xtemplates` → dấu hiệu khung → `.git` → cwd.
- 2026-10-15 Bằng chứng blueprint trích máy kiểm/test, không trích file trạng thái viết lại mỗi phiên (PROGRESS.md, PLAN) — nếu không `audit plan` cờ cũ sau mọi phiên (AUD-HAR-019).

- 2026-10-15 Phiên chính tự duyệt điểm quyết định chuyên môn (5 tiêu chí: đúng & an toàn · đường lùi · bền lâu · trải nghiệm · tốc độ phá hoà), ghi `loop decide` D-NNN; hành động vẫn dừng có hook; mặc định tự host, dịch vụ thật quyết ở G7 — ADR-0008 (repo khung + dự án đích).
- 2026-10-15 Autopilot một phiên đến khi xong: context đầy → compaction + checkpoint (không bàn giao); bàn giao chỉ khi ≥ 80% trần vòng/giờ/tiền; việc cần người `loop defer`, gom cuối phiên; chạy bằng `claude --permission-mode auto` — ADR-0009.
- 2026-10-15 Phản hồi dự án đích → khung: dự án ghi `docs/xtemplates-feedback/FB-NNN.md` (`redact`), khung kéo về bằng Routine hằng tuần → PR nháp, đủ ngưỡng khi ≥ 2 dự án hoặc có tái hiện; người duyệt trước khi công khai — ADR-0010.
- 2026-10-16 Audit khung trước `/autopilot`: `xt.py doctor --fix` là việc đầu tiên; `--fix` chỉ sửa phần đảo ngược được, hook/settings để người (`install.py`); `loop init` cảnh báo, không chặn (fail-open về luồng) — `LOOP-HARNESS-020`.
- 2026-10-17 CI: gỡ `portability.yml` (macOS bash 3.2, chỉ chạy sau merge từ 2026-10-16) theo yêu cầu chủ repo — CI không còn kiểm macOS (bash 3.2, sed/awk BSD, `python3` 3.9 hệ thống).
- 2026-10-16 Trong vòng autopilot, `lint`/`test` rỗng hoặc no-op (kể cả chỉ có comment) làm cổng đỏ — ADR-0011.
- 2026-10-16 Blueprint chỉ MUST theo quy mô, SHOULD/MAY ở BACKLOG; trần vòng một phiên chỉ đếm task — ADR-0012.
- 2026-10-16 Máy quyết khi nào merge (`xt.py merge-check`, REST); mỗi lát code một PR — ADR-0013, ADR-0014, D-010.
- 2026-10-16 Mở PR là bật auto-merge (`merge_autonomy: L3`, mặc định repo khung + mẫu dự án đích; chủ repo yêu cầu) — ADR-0015, D-011; ngoại lệ cứng (tiền, dữ liệu người dùng thật, auth, mật mã, bí mật) vẫn người merge ở L3 (`merge-check` trả `hard`) — ADR-0016, D-012.
- 2026-10-17 Guard: lệnh trong container chỉ xét luật ra khỏi máy dev; push vào PR đang auto-merge → chạy lại `merge-check` (D-015).
## Bàn giao phiên
- 2026-10-17 · Commit cuối trên `main`: `eafee57` (#82); tag `v2.0.0` → `55de4d1`; SHA quét audit `536584f` (delta #68–#80).
- Lệnh kiểm nhanh: `scripts/dev-task.sh gate` (`pip install --require-hashes -r requirements-dev.txt`, cần shellcheck; hook cổng commit dùng python hệ thống).
- Autopilot: PLAN T-801…T-804 (đóng audit delta). Đang chặn: không.
- Câu hỏi cần người: AUD-CI-009; Tiếp theo 1 (`x-hotel-manager`).
