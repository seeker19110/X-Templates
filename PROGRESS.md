# PROGRESS.md — Khung X-Templates

> Giai đoạn hiện tại: G8 Vận hành & tiến hoá (khung 3.13.0, pha `build`) · Cập nhật: 2026-10-21 · Nhánh: main

## Đang làm
- 2026-10-21 **PLAN-3.15-audit-gate** (D-130) xong phần mã: [audit tại `ec4c7d2`](docs/ops/AUDIT-REPORT-2026-10-21.md) (commit `d388802`) xác minh lại 7/7 tái hiện được; sửa AUD-CODE-014 🔴, XFEAT-013/020 🟠 ở #207, SEC-102, CI-016, CI-012, CFG-003 ở PR Lát 3–4; `audit check --strict` xanh. CI khung giữ fan-out ([số đo](docs/ops/CI-TIMING-2026-10-21.md), D-131). Mới AUD-XFEAT-021 🟢 (`go test` 0 test).
- 2026-10-21 **PLAN-3.13 Lát 0 (ADR-0036, D-122 — chủ repo chọn "ruleset tối thiểu")**: máy chỉ merge ghim head, không auto-merge của GitHub; bỏ required check `merge-gate` + lệnh `xt.py merge-gate`; guard deny phẳng bật auto-merge (`AUTO_MERGE_ENABLE`); `merge-gate.yml` thành stub `pull_request` giữ context tới khi chủ repo gỡ khỏi ruleset sống (T-1834 xoá); ruleset mẫu 2 check. K-1 đóng (không còn `pull_request_target` ngoài `pr-review.yml`). Nghiên cứu nền: [`research/2026-10-21-next-level-speed-automation-quality.md`](research/2026-10-21-next-level-speed-automation-quality.md) (#197).
- 2026-10-20 **PLAN-3.12-lean** (D-111) đã xong: Lát 1 #190, Lát 2 #191 (3.11.0), Lát 3 #192, Lát 4 #193 (3.11.1). Nợ 🟢 review #191: gom mệnh đề "Dự án đích" trùng khi `install.py` in bước nâng bản.
- Hoãn tới pha `harden`: PLAN-3.11 T-1690/T-1691 (quét lại SEC-091…099; `release-check` GO).
- Rà `seeker19110/stored` 2026-10-18: chờ chủ repo (HAR-036/041, SEC-026, CI-006/007/009, SEC-043 #97).

## Tiếp theo
0. **PLAN-3.14-app** (ADR-0038, D-126; vòng `loop init --plan docs/autopilot/PLAN-3.14-app.md`): Lát 1 + T-1911/T-1914 merge #209; T-1912 máy chủ, T-1991 research + D-133 (E2E Playwright dev-only, axe dưới `tests_e2e/`) trên nhánh; đợt kế theo `xt.py plan waves --plan docs/autopilot/PLAN-3.14-app.md`.
1. PLAN-3.13: Lát 0–C đã merge (#198–#201), 3.13.0 cắt (#202), tag `v3.13.0`, PR dự án đích hotel-manager #112 · X-Company #58; hoãn chờ người T-1814 (AUD-SEC-102 `git push origin 2>&1` trên `main` lọt kiểm nhánh — bản vá đề xuất trong task), T-1822, T-1832, T-1834. **Chờ chủ repo**: gỡ context `merge-gate` khỏi ruleset sống ở X-Templates, hotel-manager, X-Company (Settings → Rules; kiểm `gh api repos/<o>/<r>/rules/branches/main`) rồi mới xoá stub; tắt "Allow auto-merge"; `XT_STEWARD_TOKEN` (merge của steward mới kích CI trên `main`); ruleset khung `strict: false` (NH-1); App reviewer.
2. Sau PLAN-3.12: `delivery_phase: harden` khi vào hoàn thiện → audit delta → `release-check`; 🟢 mở: AUD-TEST-019, AUD-SEC-100; ca đối kháng cho `autonomy-bench`; guard chưa quét nội dung script gọi qua `bash x.sh`/`python3 x.py` (ghi vào LOOP-STOP-027 khi làm); `project-commands.sh` được `source` hai lần mỗi task (`guard_turn` + `run_task`).
3. Chờ chủ repo: token/app reviewer (T-1508); xoá `/scratch.log` ở gốc hệ thống file container; hotel-manager và X-Company gỡ `merge-gate` khỏi required check (ADR-0036); `x-hotel-manager` dọn/tạo mới; ô "extra approval for unattributed changes" của ruleset `main`; Dependabot security updates (proxy chặn API).
4. Còn: task `[perf]` trong `loop` (D-041); URL phiên do máy chủ MCP gắn vào thân PR (PATCH lại thân PR sau khi mở — đã làm cho #190/#191); ép báo "đã đo/chưa đo" cho task UI (`LOOP-DESIGN-021`); sàn quyền token; `xt.pyz` (ADR-0010).
5. Giới hạn guard đã biết: ghép tên hàm lúc chạy, giải mã qua `$(…)` (D-051); env `GIT_CONFIG_*`; CLI container ngoài docker/podman (AUD-SEC-042); chặn oan script Python chỉ đọc nhắc `.claude/hooks`/`.autopilot` (D-105).
6. Giữ cổng: C901 ≤ 10, `mypy --strict`, coverage dòng + nhánh 100 %, `changelog-check`, trần byte file hướng dẫn (`tests/test_docs_budget.py`) — không `noqa`/pragma, không nới trần.

## Quyết định
> Chi tiết ở `docs/adr/` (ADR-0001…0038) và `docs/autopilot/DECISIONS.md` (D-NNN); ở đây chỉ giữ điều chưa có nhà khác.
- Khung = thư viện yêu cầu có ID + ghép blueprint + máy kiểm "xong" (ADR-0001); hook fail-open về luồng, fail-closed về hành động nguy hiểm (ADR-0002); blueprint theo quy mô S/M (ADR-0003/0004/0012).
- Luật VN: Luật 91/2025/QH15 + NĐ 356/2025 (thay NĐ 13/2023 từ 01/01/2026); Luật ANM 116/2025 (01/07/2026). OWASP LLM Top 10 2026; EU AI Act Đ.50 áp dụng 02/08/2026. Mặc định OSI: OpenTofu, Valkey.
- Repo khung: Python ≥ 3.11; `mypy --strict`; coverage 100 % (cả subprocess); `changelog-check`/`progress-check` trong `lint`; PROGRESS chỉ ghi SHA trên `main` (squash-merge). Tên: X-stored → X-Templates (ADR-0006/0007).
- Commit/PR không ghi tên model hay URL phiên AI (LOOP-HARNESS-027); tag phát hành qua `release-tag.yml` — gọi bằng REST `workflow_dispatch` (`gh workflow run` cần GraphQL, bị chặn trong phiên).
- Autopilot: tự duyệt (ADR-0008), một phiên (ADR-0009), phản hồi dự án đích (ADR-0010), cổng rỗng là đỏ (ADR-0011), `doctor --fix` đầu tiên; pha build/harden (ADR-0031), tối giản pha build (ADR-0033). Merge theo làn (ADR-0013…0016, 0020, 0024/0025, 0028/0032), steward (ADR-0027); cơ chế: merge ghim head, không auto-merge, không `merge-gate` (ADR-0036 thay 0023/0035). Guard không hỏi người (ADR-0018/0019), ghi tay `.autopilot/` bị chặn (ADR-0026). Reviewer khác HỌ model với người viết: agent được resume sau giới hạn phiên chạy model của phiên chính — cần review thì spawn agent mới và chỉ định `model`.
- Phiên bị ràng buộc một nhánh → lát đi tuần tự; sau mỗi merge gộp `origin/main` vào nhánh (guard chặn force-push); sửa PR đang mở khi cây làm việc bẩn → worktree tách riêng rồi `git reset --soft` + `reset` ở cây chính.
- Sửa thân PR (gỡ chân trang URL phiên) kích `edited` → `concurrency` huỷ run CI đang chạy, `quality` của run cũ đỏ (không phải lỗi); `pr next` đọc run cũ tới khi run mới xong. Phiên khung không merge được PR ở repo khác (guard: `merge-check` chỉ kiểm repo khung) → để `pr-steward` của dự án merge ghim head.
- CI không còn kiểm macOS (gỡ `portability.yml` 2026-10-17 theo chủ repo). Nợ chấp nhận: 4 MUST/module là phán đoán; số điều NĐ 356/2025 chưa đối chiếu bản gốc.

## Bàn giao phiên
- 2026-10-21 · `main` `3221f95` (#207). PLAN-3.15: #206 sổ + PLAN, #207 Lát 1–2, PR Lát 3–5 mở. Lệnh merge của phiên bị bộ phân loại Auto chặn → `pr-steward` merge ghim head (cron 10 phút có lúc trễ ~1 giờ; D-132). Dự án đích: chạy lại `install.py --with-github` khi cắt 3.14.0 (mẫu CI thêm bước `floor --run`).
- Lát E (ADR-0039, #204): mẫu CI 3 job + `gate-par`. Dự án đích (PR mở, CI xanh): hotel-manager #114 13 → 10 job, CI 4m03s; X-Company #60 17 → 8 job, mọi job bắt đầu cùng lúc, CI 8m14s → 4m52s, `gate` song song 49 s (tuần tự cũ ~220 s).
- Chờ người (`loop status` = done-pending-human): T-1814 vá guard (AUD-SEC-102), T-1822 đăng ký hook, T-1832 spike mutation trên CI, T-1834 gỡ `merge-gate` ở ruleset hai dự án đích rồi xoá stub; T-1823 chờ pha harden.
- `pr stats --days 7`: 183 PR merge · lead time trung vị 0,16 giờ (P95 1,59) · 4 run CI/PR · 8 % run đỏ/huỷ · 0 revert.
- Kiểm nhanh: `scripts/dev-task.sh gate`. SessionStart gần trần 12 KB khi nhiều task hoãn — lý do hoãn viết ngắn.
