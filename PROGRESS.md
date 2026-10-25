# PROGRESS.md — Khung X-Templates

> Giai đoạn hiện tại: G8 Vận hành & tiến hoá (khung 3.22.1, pha `harden` — D-136) · Cập nhật: 2026-10-25 · Nhánh: main

## Đang làm
- 2026-10-25 **PLAN-3.23.0-complete** (D-174, ADR-0046, 3.23.0): `/autopilot` = pha build dừng ở build xong (verdict `done` không đòi 0 MUST ở build), `/complete` = pha harden (audit, nợ review, hoàn thiện, `release-check`). Lát 1 sổ (#259) → Lát 2 skill → Lát 3 `xt.py` + test → Lát 4 tài liệu + cắt bản. Điểm đo `LOOP-ORCH-020`: phiên chính tự làm.
- 2026-10-25 **PLAN-3.23-delegation-rate** (D-171/D-172, 3.22.0): `loop stats` thêm `delegation_rate`, `first_pass_rate_{delegated,self}` (nhóm theo executor lần chạy đầu); `LOOP-ORCH-020` Kiểm trỏ trường mới. Điểm đo: T-3201 do `executor` (xanh lần đầu), 2 task chữ tự làm. PLAN-3.22-adr0045-rest xong (D-170, `v3.21.0`, #252; `AI-EVAL-021`, `AI-AGENT-024`, `XC-DOCAI-021`, `AI-APP-019`; `LOOP-CTX-010` MAY). Còn: chờ ≥ 10 task/nhóm × ≥ 2 vòng rồi mới xét đổi mặc định giao việc.
- 2026-10-25 **Audit delta e5ff88c..3ba5828** (D-173; [báo cáo](docs/ops/AUDIT-REPORT-2026-10-25-delta.md)): 0 🔴, 2 🟠 (SEC-105, HAR-106) + 14 🟢. Sửa 2 🟠 + 3 🟢 ở 3.22.1 (#255, `9041f56`; mới 🟢 SEC-107/HAR-111). BLUEPRINT.md sinh lại + tái kiểm 19 mục (HAR-110): MUST 64 đạt, 0 chưa.
- 2026-10-24 **PLAN-3.18/3.19** (D-157/D-158; `v3.18.0`–`v3.18.2`, #238–#243, GO-NO-GO chờ ký; `v3.20.0` #250 cũng chờ ký): 7 🟢 phản hồi, `check-links` setext. Trước đó PLAN-3.17 xong (#235–#237, `v3.17.0`).
- 2026-10-23 **PLAN-3.16.0-ceiling xong** (D-142…D-148, ADR-0043; #231, #232, `v3.16.0`): chi tiết ở CHANGELOG. Đo lại 2026-10-30 bằng `pr stats --days 7`. Phản hồi dự án đích: 10 nhóm `cong-cu` đủ ngưỡng chờ phân loại ([TARGETS](docs/ops/TARGETS.md)).
- Hoãn tới harden: T-1690/T-1691 (quét lại SEC-091…099).
- Rà `seeker19110/stored` 2026-10-18: chờ chủ repo (HAR-036/041, SEC-026, CI-006/7/9, SEC-043).

## Tiếp theo
0. PLAN-3.14-app (`v3.14.0`): PR nâng dự án đích chờ chủ dự án: hotel-manager #117, X-Company #65. Nợ: 21 MUST blueprint repo khung đổi chữ từ 2026-10-15; 58/68 MUST tick không có lệnh kiểm (`unchecked_must`, chưa bật `fail`).
1. PLAN-3.13: Lát 0–C merge (#198–#201), `v3.13.0` (#202); hoãn chờ người T-1814 (AUD-SEC-102 — bản vá trong task), T-1822, T-1832, T-1834. **Ruleset sống X-Templates**: không `merge-gate`, `strict: true` (chủ repo bật lại 2026-10-23, D-144 — khớp `main.json`); còn tắt resolve thread + bật "Allow auto-merge" (RUNBOOK-PR-STEWARD §1). **Chờ chủ repo**: hotel-manager, X-Company gỡ `merge-gate` khỏi ruleset (`gh api repos/<o>/<r>/rules/branches/main`) rồi mới xoá stub; tắt "Allow auto-merge"; `XT_STEWARD_TOKEN` (T-2402 là lớp đỡ tạm bằng `workflow_dispatch`); App reviewer.
2. Sau PLAN-3.12: ca đối kháng cho `autonomy-bench`; guard chưa quét nội dung script gọi qua `bash x.sh`/`python3 x.py` (ghi vào LOOP-STOP-027 khi làm); `project-commands.sh` được `source` hai lần mỗi task.
3. Chờ chủ repo: token/app reviewer (T-1508); xoá `/scratch.log` ở gốc container; `x-hotel-manager` dọn/tạo mới; Dependabot security updates (proxy chặn API); Routine tuần `feedback aggregate` + quyền repo đích (T-2410).
4. Còn: task `[perf]` trong `loop` (D-041); URL phiên do máy chủ MCP gắn vào thân PR (PATCH lại thân PR sau khi mở); ép báo "đã đo/chưa đo" cho task UI (`LOOP-DESIGN-021`); sàn quyền token; `xt.pyz` (ADR-0010).
5. Giới hạn guard đã biết: `fd -X rm` (T-2812); tên trần glob (`s?`), glob ngoài thư mục bin, extglob, glob trong container (D-164/D-167); ghép tên hàm lúc chạy, giải mã qua `$(…)` (D-051); env `GIT_CONFIG_*`; CLI container ngoài docker/podman (AUD-SEC-042); chặn oan script Python chỉ đọc nhắc `.claude/hooks`/`.autopilot` (D-105).
6. Giữ cổng: C901 ≤ 10, `mypy --strict`, coverage dòng + nhánh 100 %, `changelog-check`, trần byte file + tổng thư mục (`tests/test_docs_budget.py`, ADR-0043) — không `noqa`/pragma, không nới trần.
7. Hàng rào (hook + `settings.json`, cần Claude Code ≥ 2.1.295 — `claude_min_version`): **xét lại hàng rào 2027-01-21** hoặc khi đổi model (LOOP-DESIGN-014).

## Quyết định
> Chi tiết ở `docs/adr/` (ADR-0001…0043) và `docs/autopilot/DECISIONS.md` (D-NNN); ở đây chỉ giữ điều chưa có nhà khác.
- Khung = thư viện yêu cầu có ID + ghép blueprint + máy kiểm "xong" (ADR-0001); hook fail-open về luồng, fail-closed về hành động nguy hiểm (ADR-0002); blueprint theo quy mô S/M (ADR-0003/0004/0012).
- Luật VN: Luật 91/2025/QH15 + NĐ 356/2025 (thay NĐ 13/2023 từ 01/01/2026); Luật ANM 116/2025 (01/07/2026). OWASP LLM Top 10 2026; EU AI Act Đ.50 áp dụng 02/08/2026. Mặc định OSI: OpenTofu, Valkey.
- Repo khung: Python ≥ 3.11; `mypy --strict`; coverage 100 % (cả subprocess); `changelog-check`/`progress-check` trong `lint`; PROGRESS chỉ ghi SHA trên `main` (squash-merge). Tên: X-stored → X-Templates (ADR-0006/0007).
- Commit/PR không ghi tên model hay URL phiên AI (LOOP-HARNESS-027); tag phát hành qua `release-tag.yml` — gọi bằng REST `workflow_dispatch` (`gh workflow run` cần GraphQL, bị chặn trong phiên).
- Autopilot: tự duyệt (ADR-0008), một phiên (ADR-0009), phản hồi dự án đích (ADR-0010), cổng rỗng là đỏ (ADR-0011), `doctor --fix` đầu tiên; pha build/harden (ADR-0031), tối giản pha build (ADR-0033). Merge theo làn (ADR-0013…0016, 0020, 0024/0025, 0028/0032), steward (ADR-0027); cơ chế: merge ghim head, không auto-merge, không `merge-gate` (ADR-0036 thay 0023/0035). Guard không hỏi người (ADR-0018/0019), ghi tay `.autopilot/` bị chặn (ADR-0026). Reviewer năng lực cao hơn người viết (D-161): agent được resume sau giới hạn phiên chạy model của phiên chính — cần review thì spawn agent mới và chỉ định `model`.
- Phiên bị ràng buộc một nhánh → lát đi tuần tự; sau mỗi merge gộp `origin/main` vào nhánh (guard chặn force-push); sửa PR đang mở khi cây làm việc bẩn → worktree tách riêng rồi `git reset --soft` + `reset` ở cây chính.
- Sửa thân PR (chân trang do máy chủ MCP gắn) từng kích `edited` → chạy lại CI nặng cùng SHA rồi `concurrency` huỷ run cũ; T-2401 đã bỏ `edited` khỏi `ci.yml`, chỉ `pr-title.yml` (vài giây) nghe `edited`. Phiên khung không merge được PR ở repo khác (guard: `merge-check` chỉ kiểm repo khung) → để `pr-steward` của dự án merge ghim head.
- CI không còn kiểm macOS (gỡ `portability.yml` 2026-10-17 theo chủ repo). Nợ chấp nhận: 4 MUST/module là phán đoán; số điều NĐ 356/2025 chưa đối chiếu bản gốc. Không làm (D-142): tách `xt.py`, song song worktree, merge queue, reviewer LLM mọi PR, thu nhỏ guard.

## Bàn giao phiên
- 2026-10-21 · `main` `3221f95` (#207). PLAN-3.15: #206 sổ + PLAN, #207 Lát 1–2. Lệnh merge của phiên bị bộ phân loại Auto chặn → `pr-steward` merge ghim head (cron 10 phút thực đo cách nhau ~4 giờ; D-132). Dự án đích: chạy lại `install.py --with-github` khi cắt 3.14.0.
- Chờ người (`loop status` = done-pending-human): T-1814 vá guard (AUD-SEC-102), T-1822 đăng ký hook, T-1832 spike mutation trên CI, T-1834 gỡ `merge-gate` ở ruleset hai dự án đích rồi xoá stub; T-1823 chờ pha harden.
- `pr stats --days 7` (2026-10-23, REST đếm đủ): 174 PR merge · lead trung vị 9,4 phút (P95 1,58 h) · push đầu không đỏ 84 % · 0 revert. `pr stats` của khung cắt ở 1.000 run (T-2409).
- Kiểm nhanh: `scripts/dev-task.sh gate`. SessionStart gần trần 12 KB khi nhiều task hoãn — lý do hoãn viết ngắn.
