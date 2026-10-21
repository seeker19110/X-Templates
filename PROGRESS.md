# PROGRESS.md — Khung X-Templates

> Giai đoạn hiện tại: G8 Vận hành & tiến hoá (khung 3.12.0, pha `build`) · Cập nhật: 2026-10-21 · Nhánh: main

## Đang làm
- 2026-10-21 **3.12.0 — CI/E2E/ruleset dự án đích tối thiểu, song song tối đa** (chủ repo; ADR-0034, D-115…D-117; CD bỏ theo chủ repo): #194 đã merge, tag `v3.12.0` → `5b8b8a6`. Mẫu `ci.yml` bỏ `test-plan` (matrix tĩnh), thêm job `e2e`, `protection-guard` vào `quality.needs`; mẫu `ruleset-main.json` (3 check, không strict); `dev-task.sh` thêm `test-mode`/`e2e-mode`/`e2e`.
- 2026-10-21 **Đã cài 3.12.0 cho hai dự án đích** (gộp tay `ci.yml`/ruleset của dự án): hotel-manager #111 **đã merge** — `typecheck`/`lint` song song với `gate` (build → test giữ chung: test quét bundle cần `.next`), e2e 4 → 6 shard, CI 4m30s → 3m34s, ruleset giữ (đã 3 check); X-Company #51 **đã merge** — `quality` nối tiếp 8m02s tách thành typecheck · lint · build · checks · test · coverage song song, `quality` gom mọi job, ruleset 13 → 4 check (`quality`, `gitleaks`, `merge-gate`, `pr-policy`), không strict — chủ repo đã import, `gh api …/rules/branches/main` khớp file.
- 2026-10-20 **PLAN-3.12-lean** (D-111) đã xong: Lát 1 #190, Lát 2 #191 (3.11.0), Lát 3 #192, Lát 4 #193 (3.11.1). Nợ 🟢 review #191: gom mệnh đề "Dự án đích" trùng khi `install.py` in bước nâng bản.
- Hoãn tới pha `harden`: PLAN-3.11 T-1690/T-1691 (quét lại SEC-091…099; `release-check` GO).
- Rà `seeker19110/stored` 2026-10-18: chờ chủ repo (HAR-036/041, SEC-026, CI-006/007/009, SEC-043 #97).

## Tiếp theo
1. Sau PLAN-3.12: `delivery_phase: harden` khi vào hoàn thiện → audit delta → `release-check`; 🟢 mở: AUD-TEST-019, AUD-SEC-100; ca đối kháng cho `autonomy-bench`; guard chưa quét nội dung script gọi qua `bash x.sh`/`python3 x.py` (ghi vào LOOP-STOP-027 khi làm); `project-commands.sh` được `source` hai lần mỗi task (`guard_turn` + `run_task`).
2. Chờ chủ repo: token/app reviewer (T-1508); xoá `/scratch.log` ở gốc hệ thống file container; hotel-manager thêm `merge-gate` vào required check; `x-hotel-manager` dọn/tạo mới; ô "extra approval for unattributed changes" của ruleset `main`; Dependabot security updates (proxy chặn API).
3. Còn: task `[perf]` trong `loop` (D-041); URL phiên do máy chủ MCP gắn vào thân PR (PATCH lại thân PR sau khi mở — đã làm cho #190/#191); ép báo "đã đo/chưa đo" cho task UI (`LOOP-DESIGN-021`); sàn quyền token; `xt.pyz` (ADR-0010).
4. Giới hạn guard đã biết: ghép tên hàm lúc chạy, giải mã qua `$(…)` (D-051); env `GIT_CONFIG_*`; CLI container ngoài docker/podman (AUD-SEC-042); chặn oan script Python chỉ đọc nhắc `.claude/hooks`/`.autopilot` (D-105).
5. Giữ cổng: C901 ≤ 10, `mypy --strict`, coverage dòng + nhánh 100 %, `changelog-check`, trần byte file hướng dẫn (`tests/test_docs_budget.py`) — không `noqa`/pragma, không nới trần.

## Quyết định
> Chi tiết ở `docs/adr/` (ADR-0001…0034) và `docs/autopilot/DECISIONS.md` (D-NNN); ở đây chỉ giữ điều chưa có nhà khác.
- Khung = thư viện yêu cầu có ID + ghép blueprint + máy kiểm "xong" (ADR-0001); hook fail-open về luồng, fail-closed về hành động nguy hiểm (ADR-0002); blueprint theo quy mô S/M (ADR-0003/0004/0012).
- Luật VN: Luật 91/2025/QH15 + NĐ 356/2025 (thay NĐ 13/2023 từ 01/01/2026); Luật ANM 116/2025 (01/07/2026). OWASP LLM Top 10 2026; EU AI Act Đ.50 áp dụng 02/08/2026. Mặc định OSI: OpenTofu, Valkey.
- Repo khung: Python ≥ 3.11; `mypy --strict`; coverage 100 % (cả subprocess); `changelog-check`/`progress-check` trong `lint`; PROGRESS chỉ ghi SHA trên `main` (squash-merge). Tên: X-stored → X-Templates (ADR-0006/0007).
- Commit/PR không ghi tên model hay URL phiên AI (LOOP-HARNESS-027); tag phát hành qua `release-tag.yml` — gọi bằng REST `workflow_dispatch` (`gh workflow run` cần GraphQL, bị chặn trong phiên).
- Autopilot: tự duyệt (ADR-0008), một phiên (ADR-0009), phản hồi dự án đích (ADR-0010), cổng rỗng là đỏ (ADR-0011), `doctor --fix` đầu tiên; pha build/harden (ADR-0031), tối giản pha build (ADR-0033). Merge theo làn (ADR-0013…0016, 0020, 0024/0025, 0028/0032), steward (ADR-0027). Guard không hỏi người (ADR-0018/0019), ghi tay `.autopilot/` bị chặn (ADR-0026). Reviewer khác HỌ model với người viết: agent được resume sau giới hạn phiên chạy model của phiên chính — cần review thì spawn agent mới và chỉ định `model`.
- Phiên bị ràng buộc một nhánh → lát đi tuần tự; sau mỗi merge gộp `origin/main` vào nhánh (guard chặn force-push); sửa PR đang mở khi cây làm việc bẩn → worktree tách riêng rồi `git reset --soft` + `reset` ở cây chính.
- Sửa thân PR (gỡ chân trang URL phiên) kích `edited` → `concurrency` huỷ run CI đang chạy, `quality` của run cũ đỏ (không phải lỗi); `pr next` đọc run cũ tới khi run mới xong. Phiên khung không bật được auto-merge ở repo khác (guard: `merge-check` chỉ kiểm repo khung) → để `pr-steward` của dự án làm.
- CI không còn kiểm macOS (gỡ `portability.yml` 2026-10-17 theo chủ repo). Nợ chấp nhận: 4 MUST/module là phán đoán; số điều NĐ 356/2025 chưa đối chiếu bản gốc.

## Bàn giao phiên
- 2026-10-21 · Commit cuối trên `main`: `9307e8b` (#195); tag `v3.12.0` → `5b8b8a6` (#194). Dự án đích: hotel-manager (#111) và X-Company (#51) đã chạy 3.12.0, ruleset GitHub khớp file. Nhánh `claude/peaceful-babbage-ap3k9u`: chỉ còn PR bàn giao này.
- Lệnh kiểm nhanh: `scripts/dev-task.sh gate` (`pip install --require-hashes -r requirements-dev.txt`, cần shellcheck; hook cổng commit dùng python hệ thống).
- Autopilot: `loop status`. Đang chặn: không. Câu hỏi cần người: Tiếp theo 2.
