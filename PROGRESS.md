# PROGRESS.md — Khung X-Templates

> Giai đoạn hiện tại: G8 Vận hành & tiến hoá (khung 3.15.6, pha `harden` — D-136) · Cập nhật: 2026-10-23 · Nhánh: main

## Đang làm
- 2026-10-23 **PLAN-3.16.0-ceiling** (D-142): [phân tích trần](research/2026-10-23-ceiling-analysis.md) → 44 agent, 8 luận điểm, 4 bị bác. Lỗ đo được: ¾ run CI huỷ là cùng SHA do `edited` (`ci.yml:9`); `main` #227–#229 chưa có run CI (steward merge bằng GITHUB_TOKEN); steward `wait` giả (#208 chờ 2,57 h). Lát 1 cấu hình → Lát 2 chất lượng nội dung → Lát 3 đo thật → 3.16.0. Đo lại 2026-10-30 bằng `pr stats`.
- 2026-10-22 **ADR-0040…0042** (#212–#218; D-136, D-137): pha build nới việc trong dự án/tmp, build gọn, `release-check` chạy `attack`/`perf`; repo khung luôn harden. 3.15.0…3.15.4 (#219–#224): Gate hết giờ dừng cả nhóm tiến trình; hook khung 2.x không đăng ký đôi; skill trùng lệnh dự án không cài; `harness_permissions: own`, sibling hook có đường dẫn (xboss #664). Dự án đích: hotel-manager harden (#119, #120), 3.15.1 (#121, X-Company #70); dhcb, xboss (2.0.0) chờ 3.15.4.
- 2026-10-21 **PLAN-3.15-audit-gate** (D-130): [audit tại `ec4c7d2`](docs/ops/AUDIT-REPORT-2026-10-21.md) 7/7 tái hiện, đã sửa (#207). CI khung giữ fan-out ([số đo](docs/ops/CI-TIMING-2026-10-21.md), D-131 — số 94,5 s đo trước `app-e2e`; 2026-10-22 trung vị 162 s).
- 2026-10-22 **PLAN-3.15.5-green-debt** (D-138): dọn 5 🟢 (#225, #226, `v3.15.5`). **PLAN-3.16-audit-delta** (D-139/140): [audit delta tới `1139662`](docs/ops/AUDIT-REPORT-2026-10-22.md) + A11Y (#227): 0 🔴, 23 🟢; 🟠 AUD-SEC-103 sửa ở 3.15.6 (#228, `v3.15.6`).
- Nợ 🟢 #191: gom mệnh đề "Dự án đích" trùng của `install.py`. Hoãn tới harden: T-1690/T-1691 (quét lại SEC-091…099).
- Rà `seeker19110/stored` 2026-10-18: chờ chủ repo (HAR-036/041, SEC-026, CI-006/7/9, SEC-043).

## Tiếp theo
0. **PLAN-3.14-app xong** (ADR-0038, D-126, D-133…D-135): `v3.14.0` (`7f121a6`); `xt.py app` (14 API, 7 màn, E2E + axe ở `app-e2e`), `plan waves`. PR nâng dự án đích chờ chủ dự án: hotel-manager #117, X-Company #65. Nợ: 21 MUST blueprint repo khung đổi chữ từ 2026-10-15; 58 MUST tick không có lệnh kiểm (T-2406 thêm cờ, repo khung chưa bật).
1. PLAN-3.13: Lát 0–C merge (#198–#201), `v3.13.0` (#202); hoãn chờ người T-1814 (AUD-SEC-102 — bản vá trong task), T-1822, T-1832, T-1834. **Ruleset sống X-Templates**: không `merge-gate`, `strict: true` (chủ repo bật lại 2026-10-23, D-144 — khớp `main.json`); còn tắt resolve thread + bật "Allow auto-merge" (RUNBOOK-PR-STEWARD §1). **Chờ chủ repo**: hotel-manager, X-Company gỡ `merge-gate` khỏi ruleset (`gh api repos/<o>/<r>/rules/branches/main`) rồi mới xoá stub; tắt "Allow auto-merge"; `XT_STEWARD_TOKEN` (T-2402 là lớp đỡ tạm bằng `workflow_dispatch`); App reviewer.
2. Sau PLAN-3.12: 🟢 mở AUD-TEST-019, AUD-SEC-100; ca đối kháng cho `autonomy-bench`; guard chưa quét nội dung script gọi qua `bash x.sh`/`python3 x.py` (ghi vào LOOP-STOP-027 khi làm); `project-commands.sh` được `source` hai lần mỗi task.
3. Chờ chủ repo: token/app reviewer (T-1508); xoá `/scratch.log` ở gốc container; `x-hotel-manager` dọn/tạo mới; Dependabot security updates (proxy chặn API); Routine tuần `feedback aggregate` + quyền repo đích (T-2410).
4. Còn: task `[perf]` trong `loop` (D-041); URL phiên do máy chủ MCP gắn vào thân PR (PATCH lại thân PR sau khi mở); ép báo "đã đo/chưa đo" cho task UI (`LOOP-DESIGN-021`); sàn quyền token; `xt.pyz` (ADR-0010).
5. Giới hạn guard đã biết: ghép tên hàm lúc chạy, giải mã qua `$(…)` (D-051); env `GIT_CONFIG_*`; CLI container ngoài docker/podman (AUD-SEC-042); chặn oan script Python chỉ đọc nhắc `.claude/hooks`/`.autopilot` (D-105).
6. Giữ cổng: C901 ≤ 10, `mypy --strict`, coverage dòng + nhánh 100 %, `changelog-check`, trần byte (`tests/test_docs_budget.py`; T-2407 thêm trần tổng thư mục) — không `noqa`/pragma, không nới trần.

## Quyết định
> Chi tiết ở `docs/adr/` (ADR-0001…0042) và `docs/autopilot/DECISIONS.md` (D-NNN); ở đây chỉ giữ điều chưa có nhà khác.
- Khung = thư viện yêu cầu có ID + ghép blueprint + máy kiểm "xong" (ADR-0001); hook fail-open về luồng, fail-closed về hành động nguy hiểm (ADR-0002); blueprint theo quy mô S/M (ADR-0003/0004/0012).
- Luật VN: Luật 91/2025/QH15 + NĐ 356/2025 (thay NĐ 13/2023 từ 01/01/2026); Luật ANM 116/2025 (01/07/2026). OWASP LLM Top 10 2026; EU AI Act Đ.50 áp dụng 02/08/2026. Mặc định OSI: OpenTofu, Valkey.
- Repo khung: Python ≥ 3.11; `mypy --strict`; coverage 100 % (cả subprocess); `changelog-check`/`progress-check` trong `lint`; PROGRESS chỉ ghi SHA trên `main` (squash-merge). Tên: X-stored → X-Templates (ADR-0006/0007).
- Commit/PR không ghi tên model hay URL phiên AI (LOOP-HARNESS-027); tag phát hành qua `release-tag.yml` — gọi bằng REST `workflow_dispatch` (`gh workflow run` cần GraphQL, bị chặn trong phiên).
- Autopilot: tự duyệt (ADR-0008), một phiên (ADR-0009), phản hồi dự án đích (ADR-0010), cổng rỗng là đỏ (ADR-0011), `doctor --fix` đầu tiên; pha build/harden (ADR-0031), tối giản pha build (ADR-0033). Merge theo làn (ADR-0013…0016, 0020, 0024/0025, 0028/0032), steward (ADR-0027); cơ chế: merge ghim head, không auto-merge, không `merge-gate` (ADR-0036 thay 0023/0035). Guard không hỏi người (ADR-0018/0019), ghi tay `.autopilot/` bị chặn (ADR-0026). Reviewer khác HỌ model với người viết: agent được resume sau giới hạn phiên chạy model của phiên chính — cần review thì spawn agent mới và chỉ định `model`.
- Phiên bị ràng buộc một nhánh → lát đi tuần tự; sau mỗi merge gộp `origin/main` vào nhánh (guard chặn force-push); sửa PR đang mở khi cây làm việc bẩn → worktree tách riêng rồi `git reset --soft` + `reset` ở cây chính.
- Sửa thân PR (chân trang do máy chủ MCP gắn) từng kích `edited` → chạy lại CI nặng cùng SHA rồi `concurrency` huỷ run cũ; T-2401 đã bỏ `edited` khỏi `ci.yml`, chỉ `pr-title.yml` (vài giây) nghe `edited`. Phiên khung không merge được PR ở repo khác (guard: `merge-check` chỉ kiểm repo khung) → để `pr-steward` của dự án merge ghim head.
- CI không còn kiểm macOS (gỡ `portability.yml` 2026-10-17 theo chủ repo). Nợ chấp nhận: 4 MUST/module là phán đoán; số điều NĐ 356/2025 chưa đối chiếu bản gốc. Không làm (D-142): tách `xt.py`, song song worktree, merge queue, reviewer LLM mọi PR, thu nhỏ guard.

## Bàn giao phiên
- 2026-10-21 · `main` `3221f95` (#207). PLAN-3.15: #206 sổ + PLAN, #207 Lát 1–2. Lệnh merge của phiên bị bộ phân loại Auto chặn → `pr-steward` merge ghim head (cron 10 phút thực đo cách nhau ~4 giờ; D-132). Dự án đích: chạy lại `install.py --with-github` khi cắt 3.14.0.
- Lát E (ADR-0039, #204): mẫu CI 3 job + `gate-par`. Dự án đích: hotel-manager #114 13 → 10 job, CI 4m03s; X-Company #60 17 → 8 job, CI 8m14s → 4m52s, `gate` song song 49 s (tuần tự cũ ~220 s).
- Chờ người (`loop status` = done-pending-human): T-1814 vá guard (AUD-SEC-102), T-1822 đăng ký hook, T-1832 spike mutation trên CI, T-1834 gỡ `merge-gate` ở ruleset hai dự án đích rồi xoá stub; T-1823 chờ pha harden.
- `pr stats --days 7` (2026-10-23, REST đếm đủ): 174 PR merge · lead trung vị 9,4 phút (P95 1,58 h) · push đầu không đỏ 84 % · 0 revert. `pr stats` của khung cắt ở 1.000 run (T-2409).
- Kiểm nhanh: `scripts/dev-task.sh gate`. SessionStart gần trần 12 KB khi nhiều task hoãn — lý do hoãn viết ngắn.
