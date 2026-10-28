# PROGRESS.md — Khung X-Templates

> Giai đoạn hiện tại: G8 Vận hành & tiến hoá (khung 3.27.0, pha `harden` — D-136) · Cập nhật: 2026-10-28 · Nhánh: work

## Đang làm
- 2026-10-28 **PLAN-hardening-assessment-2026-10-28** (D-219, ADR-0054/0055): main `07c428f` (#308) đã vá SEC-125/121; thêm corpus, chặn state thiếu khóa/guard hỏng, preset safe tùy chọn. Gate xanh: 1.899 test, coverage 100%; review sạch, ba commit code đã tạo.
- PLAN-harden-2026-10-27-loops: lát 0–1 đã merge #290–#308; T-3556/cắt 3.28.0 theo audit delta mới.
- 2026-10-27 **ADR-0053** (#297 kế hoạch + kiểm bổ sung, #298 code; D-209…D-211): `pr next` trả `rethink` sau 2 review chưa sạch; thêm lượt qua `pr rethink --decision D-NNN` (D mới, nhắc #N). #300 dùng `rethink` thật (D-213). 🟢 treo của #298 vào sổ: AUD-DOC-095/096, AUD-HAR-117…119.
- **3.27.0** đã phát hành (#281–#283; D-196…D-200, ADR-0050): hook PostToolUseFailure và đóng hàng rào khi guard lỗi nạp. Chi tiết ở CHANGELOG; giới hạn đang áp dụng ở mục Tiếp theo.
- 2026-10-25 **3.26.0 Workflow** (D-184…D-191, ADR-0049): `/audit` §3, `/research` ≥ 3 mục dùng tool Workflow khi người gõ trực tiếp (cùng luật nhánh subagent, lô ≤ 5); không bật `ultracode`. Lần `/audit` Workflow đầu: ghi token, kiểm `maxTurns`/`effort`/guard có áp cho agent.
- 2026-10-26 **PLAN-harden-2026-10-26 + PLAN-harden-2026-10-26b** (D-193/194, `/complete`): 20 MUST tick có `— Kiểm:` (`unchecked_must` 57 → 37; PLAN-harden-2026-10-26c: → 0, D-195); CI `checks` chạy `blueprint-status --strict --run`; `_load_guard` báo lỗi nạp (ERR-001).
- 2026-10-25 **PLAN-3.23.0-complete** (D-174, ADR-0046): `/autopilot` = pha build, `/complete` = pha harden; 3.24.0 (ADR-0047): lặp build → audit delta tới khi hết việc, tag tự khi `VERSION` đổi (D-179). Mọi GO-NO-GO tới v3.25.0 đã ký GO 2026-10-26.
- PLAN-3.23-delegation-rate (D-171/172): chờ ≥ 10 task/nhóm × ≥ 2 vòng rồi mới xét đổi mặc định giao việc.
- Đo lại `pr stats --days 7` 2026-10-30 (ADR-0043). Phản hồi dự án đích: 10 nhóm `cong-cu` chờ phân loại ([TARGETS](docs/ops/TARGETS.md)).
- Rà `seeker19110/stored` 2026-10-18: chờ chủ repo (HAR-036/041, SEC-026, CI-006/7/9, SEC-043).

## Tiếp theo
0. PLAN-3.14-app (`v3.14.0`): PR nâng dự án đích chờ chủ dự án: hotel-manager #117, X-Company #65. `unchecked_must` 0/64.
1. PLAN-3.13: Lát 0–C merge (#198–#201), `v3.13.0` (#202); chờ người còn T-1834 (T-1814 xong ở T-2121; T-1822/1823/1832 duyệt 2026-10-26 → PLAN-harden-2026-10-26d). **Ruleset sống X-Templates**: không `merge-gate`, `strict: true` (chủ repo bật lại 2026-10-23, D-144 — khớp `main.json`); còn tắt resolve thread + bật "Allow auto-merge" (RUNBOOK-PR-STEWARD §1). **Chờ chủ repo**: hotel-manager, X-Company gỡ `merge-gate` khỏi ruleset (`gh api repos/<o>/<r>/rules/branches/main`) rồi mới xoá stub; tắt "Allow auto-merge"; `XT_STEWARD_TOKEN` (T-2402 là lớp đỡ tạm bằng `workflow_dispatch`); App reviewer.
2. Sau PLAN-3.12: ca đối kháng cho `autonomy-bench`; guard chưa quét nội dung script gọi qua `bash x.sh`/`python3 x.py` (ghi vào LOOP-STOP-027 khi làm); `project-commands.sh` được `source` hai lần mỗi task.
3. Chờ chủ repo: token/app reviewer (T-1508); xoá `/scratch.log` ở gốc container; `x-hotel-manager` dọn/tạo mới; Dependabot security updates (proxy chặn API); Routine tuần `feedback aggregate` + quyền repo đích (T-2410). Event policy `pull_request_target` (repo public, rule mặc định tắt từ 2026-12-02; `pr-review.yml`).
4. Còn: task `[perf]` trong `loop` (D-041); URL phiên do máy chủ MCP gắn vào thân PR (PATCH lại thân PR sau khi mở); ép báo "đã đo/chưa đo" cho task UI (`LOOP-DESIGN-021`); sàn quyền token; `xt.pyz` (ADR-0010).
5. Giới hạn guard đã biết: `fd -X rm` (T-2812); tên trần glob (`s?`), glob ngoài thư mục bin, extglob, glob trong container (D-164/D-167); ghép tên hàm lúc chạy, giải mã qua `$(…)` (D-051); env `GIT_CONFIG_*`; CLI container ngoài docker/podman (AUD-SEC-042); chặn oan script Python chỉ đọc nhắc `.claude/hooks`/`.autopilot` (D-105).
6. Giữ cổng: C901 ≤ 10, `mypy --strict`, coverage dòng + nhánh 100 %, `changelog-check`, trần byte file + tổng thư mục (`tests/test_docs_budget.py`, ADR-0043) — không `noqa`/pragma, không nới trần.
7. Hàng rào (hook + `settings.json`, cần Claude Code ≥ 2.1.295 — `claude_min_version`): **xét lại hàng rào 2027-01-21** hoặc khi đổi model (LOOP-DESIGN-014).

## Quyết định
> Chi tiết ở `docs/adr/` (ADR-0001…0051) và `docs/autopilot/DECISIONS.md` (D-NNN); ở đây chỉ giữ điều chưa có nhà khác.
- Khung = thư viện yêu cầu có ID + ghép blueprint + máy kiểm "xong" (ADR-0001); hook fail-open về luồng, fail-closed về hành động nguy hiểm (ADR-0002); blueprint theo quy mô S/M (ADR-0003/0004/0012).
- Luật VN: Luật 91/2025/QH15 + NĐ 356/2025 (thay NĐ 13/2023 từ 01/01/2026); Luật ANM 116/2025 (01/07/2026). OWASP LLM Top 10 2026; EU AI Act Đ.50 áp dụng 02/08/2026. Mặc định OSI: OpenTofu, Valkey.
- Repo khung: Python ≥ 3.11; `mypy --strict`; coverage 100 % (cả subprocess); `changelog-check`/`progress-check` trong `lint`; PROGRESS chỉ ghi SHA trên `main` (squash-merge). Tên: X-stored → X-Templates (ADR-0006/0007).
- Commit/PR không ghi tên model hay URL phiên AI (LOOP-HARNESS-027); tag phát hành qua `release-tag.yml` — gọi bằng REST `workflow_dispatch` (`gh workflow run` cần GraphQL, bị chặn trong phiên).
- Autopilot: tự duyệt (ADR-0008), một phiên (ADR-0009), phản hồi dự án đích (ADR-0010), cổng rỗng là đỏ (ADR-0011), `doctor --fix` đầu tiên; pha build/harden (ADR-0031), tối giản pha build (ADR-0033). Merge theo làn (ADR-0013…0016, 0020, 0024/0025, 0028/0032), steward (ADR-0027); cơ chế: merge ghim head, không auto-merge, không `merge-gate` (ADR-0036 thay 0023/0035). Guard không hỏi người (ADR-0018/0019), ghi tay `.autopilot/` bị chặn (ADR-0026). Reviewer năng lực cao hơn người viết (D-161): agent được resume sau giới hạn phiên chạy model của phiên chính — cần review thì spawn agent mới và chỉ định `model`.
- Phiên bị ràng buộc một nhánh → lát đi tuần tự; sau mỗi merge gộp `origin/main` vào nhánh (guard chặn force-push); sửa PR đang mở khi cây làm việc bẩn → worktree tách riêng rồi `git reset --soft` + `reset` ở cây chính.
- Sửa thân PR (chân trang do máy chủ MCP gắn) từng kích `edited` → chạy lại CI nặng cùng SHA rồi `concurrency` huỷ run cũ; T-2401 đã bỏ `edited` khỏi `ci.yml`, chỉ `pr-title.yml` (vài giây) nghe `edited`. Phiên khung không merge được PR ở repo khác (guard: `merge-check` chỉ kiểm repo khung) → để `pr-steward` của dự án merge ghim head.
- CI không còn kiểm macOS (gỡ `portability.yml` 2026-10-17 theo chủ repo). Nợ chấp nhận: 4 MUST/module là phán đoán; số điều NĐ 356/2025 chưa đối chiếu bản gốc. Không làm (D-142): tách `xt.py`, song song worktree, merge queue, reviewer LLM mọi PR, thu nhỏ guard.

## Bàn giao phiên
- Gốc `main` `07c428f` (#308); nhánh `work` đang củng cố theo D-219. Git dry-run đẩy được; gh auth báo token lỗi, quyền API xác minh riêng. Chỉ nhánh/PR nháp, không merge/tag. Gate cần mở localhost và không bị mount `/tmp/.git` giả ảnh hưởng.
- Chờ người: T-1834 gỡ `merge-gate` ở ruleset hai dự án đích rồi xoá stub.
- Kiểm nhanh: `scripts/dev-task.sh gate`. Lý do `loop defer` viết ngắn (SessionStart gần trần 12 KB).
