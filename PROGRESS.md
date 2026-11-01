# PROGRESS.md — Khung X-Templates

> Giai đoạn hiện tại: G8 Vận hành & tiến hoá (khung 3.29.0, pha `harden` — D-136) · Cập nhật: 2026-11-01 · Nhánh: main

## Đang làm
- 2026-11-01 **PLAN-upgrade-2026-11-01** (ADR-0061 "Adaptive Agent": mặc định một agent chính tự làm, `topo:` theo độ độc lập, đo trước khi tăng — D-292…D-294): lát 1 tài liệu (#378), lát 2 `loop status.topology`/`executor: null`/`plan waves --max 4` (#379), lát 3 `time_to_green_hours` + `max_rethink`/`split-or-close` (#380), lát 4–5 stored XT-H-019…026 (#381) merge; lát 6 (sổ + `AUDIT-REPORT-2026-11-01-delta.md`, PROGRESS này, T-3610) là #382. Nợ review #378–#381 trong sổ audit. Còn: T-3611 (AUD-SEC-251 🔴 + 250), T-3612 (lát E: AUD-DOC-123…129), T-3613 (scanner `xt.py prompt-assets-scan`, D-293).
- 2026-10-31 **PLAN-harden-2026-10-31** (D-268…D-291): #358–#371 (#369/#370 Dependabot), #373, #375–#377 merge; #372 (guard `$IFS#`) đóng không merge sau 7 lượt review — bài học thành `max_rethink` (ADR-0061); #374 đóng (mở lại thành #375). `release-check` NO-GO: `audit --strict` (🔴 mở AUD-SEC-251 + họ 191…247), `review_debt` → sửa T-3610/T-3611 rồi mới cắt **3.30.0**. #370 (Dependabot) đã review sạch nhưng `pr reviewed` không nhận tác giả bot (AUD-XFEAT-039) → steward merge.
- 2026-10-30 **3.29.0** đã phát hành (ADR-0058/0059, D-257/259); GO chờ người `prod_switch`. Kế: T-3557 → lát 3 `perf trial` → 3.30.0 (D-258).
- 2026-10-28 **ADR-0056** (#312): lỗi có từ trước không chặn PR, CI là cổng đầy đủ. **ADR-0054/0055** (#311). 🟢 treo: AUD-DOC-100, AUD-HAR-122/123, AUD-SEC-131.
- Phép đo `LOOP-ORCH-020` (tự làm/giao, `time_to_green_hours`) tích luỹ từ PLAN-upgrade; tăng số agent chỉ khi có số (ADR-0061).
- Đo lại `pr stats --days 7` 2026-10-30 (ADR-0043). Phản hồi dự án đích: 10 nhóm `cong-cu` chờ phân loại ([TARGETS](docs/ops/TARGETS.md)).
- Hoãn tới harden: T-1690/T-1691 (quét lại SEC-091…099). Rà `seeker19110/stored` 2026-10-18: chờ chủ repo (HAR-036/041, SEC-026, CI-006/7/9, SEC-043).

## Tiếp theo
0. PLAN-3.14-app (`v3.14.0`): PR nâng dự án đích chờ chủ dự án: hotel-manager #117, X-Company #65. `unchecked_must` 0/64.
1. PLAN-3.13: chờ người T-1834 (gỡ `merge-gate` ở ruleset hotel-manager/X-Company rồi xoá stub); **Ruleset sống X-Templates**: không `merge-gate`, `strict: true` (D-144); còn tắt resolve thread + bật "Allow auto-merge" (RUNBOOK-PR-STEWARD §1); `XT_STEWARD_TOKEN` (T-2402 lớp đỡ tạm); App reviewer.
2. Sau PLAN-3.12: ca đối kháng cho `autonomy-bench`; guard chưa quét nội dung script gọi qua `bash x.sh`/`python3 x.py` (ghi vào LOOP-STOP-027 khi làm); `project-commands.sh` được `source` hai lần mỗi task.
3. Chờ chủ repo: token/app reviewer (T-1508); xoá `/scratch.log` ở gốc container; `x-hotel-manager` dọn/tạo mới; Dependabot security updates (proxy chặn API); Routine tuần `feedback aggregate` + quyền repo đích (T-2410). Event policy `pull_request_target` (repo public, rule mặc định tắt từ 2026-12-02; `pr-review.yml`).
4. Còn: máy hoá `LOOP-HARNESS-031` (dấu hook theo phiên), `LOOP-STOP-030` (ConfigChange); task `[perf]` trong `loop` (D-041); URL phiên do máy chủ MCP gắn vào thân PR (PATCH lại thân PR sau khi mở); ép báo "đã đo/chưa đo" cho task UI (`LOOP-DESIGN-021`); sàn quyền token; `xt.pyz` (ADR-0010); `pr reviewed` nhận tác giả bot (AUD-XFEAT-039).
5. Giới hạn guard đã biết: `fd -X rm` (T-2812); tên trần glob (`s?`), glob ngoài thư mục bin, extglob, glob trong container (D-164/D-167); ghép tên hàm lúc chạy, giải mã qua `$(…)` (D-051); env `GIT_CONFIG_*`; CLI container ngoài docker/podman (AUD-SEC-042); chặn oan script Python chỉ đọc nhắc `.claude/hooks`/`.autopilot` (D-105); công cụ tự chạy lệnh sed/awk/perl/tar/m4 (AUD-SEC-251), `PS4`/`BASH_ENV` (AUD-SEC-250), chỉ số mảng số học (AUD-SEC-249).
6. Giữ cổng: C901 ≤ 10, `mypy --strict`, coverage dòng + nhánh 100 %, `changelog-check`, trần byte file + tổng thư mục (`tests/test_docs_budget.py`, ADR-0043) — không `noqa`/pragma, không nới trần.
7. Hàng rào (hook + `settings.json`, cần Claude Code ≥ 2.1.295 — `claude_min_version`): **xét lại hàng rào 2027-01-21** hoặc khi đổi model (LOOP-DESIGN-014).

## Quyết định
> Chi tiết ở `docs/adr/` (ADR-0001…0061) và `docs/autopilot/DECISIONS.md` (D-NNN); ở đây chỉ giữ điều chưa có nhà khác.
- Khung = thư viện yêu cầu có ID + ghép blueprint + máy kiểm "xong" (ADR-0001); hook fail-open về luồng, fail-closed về hành động nguy hiểm (ADR-0002); blueprint theo quy mô S/M (ADR-0003/0004/0012).
- Luật VN: Luật 91/2025/QH15 + NĐ 356/2025 (thay NĐ 13/2023 từ 01/01/2026); Luật ANM 116/2025 (01/07/2026). OWASP LLM Top 10 2026; EU AI Act Đ.50 áp dụng 02/08/2026. Mặc định OSI: OpenTofu, Valkey.
- Repo khung: Python ≥ 3.11; `mypy --strict`; coverage 100 % (cả subprocess); `changelog-check`/`progress-check` trong `lint`; PROGRESS chỉ ghi SHA trên `main` (squash-merge). Tên: X-stored → X-Templates (ADR-0006/0007).
- Commit/PR không ghi tên model hay URL phiên AI (LOOP-HARNESS-027); tag phát hành qua `release-tag.yml` — gọi bằng REST `workflow_dispatch` (`gh workflow run` cần GraphQL, bị chặn trong phiên).
- Autopilot: tự duyệt (ADR-0008), một phiên (ADR-0009), phản hồi dự án đích (ADR-0010), cổng rỗng là đỏ (ADR-0011), `doctor --fix` đầu tiên; pha build/harden (ADR-0031), tối giản pha build (ADR-0033). Merge theo làn (ADR-0013…0016, 0020, 0024/0025, 0028/0032), steward (ADR-0027); cơ chế: merge ghim head, không auto-merge, không `merge-gate` (ADR-0036). Guard không hỏi người (ADR-0018/0019), ghi tay `.autopilot/` bị chặn (ADR-0026). Reviewer năng lực cao hơn người viết (D-161): cần review thì spawn agent mới và chỉ định `model`. Cấu hình agent theo loại việc, `max_rethink` 1/PR (ADR-0061).
- Phiên nhiều lát: mỗi lát một nhánh 1-commit từ `origin/main` (hoặc xếp chồng rồi rebase sau khi lát trước merge), mở PR tuần tự; guard chặn force-push; sửa PR đang mở khi cây bẩn → worktree riêng.
- Sửa thân PR (chân trang do máy chủ MCP gắn) từng kích `edited` → chỉ `pr-title.yml` nghe `edited`. Phiên khung không merge được PR ở repo khác → để `pr-steward` của dự án merge ghim head.
- CI không còn kiểm macOS (gỡ `portability.yml` 2026-10-17). Nợ chấp nhận: 4 MUST/module là phán đoán; số điều NĐ 356/2025 chưa đối chiếu bản gốc. Không làm (D-142): tách `xt.py`, song song worktree, merge queue, reviewer LLM mọi PR, thu nhỏ guard.

## Bàn giao phiên
- `main` `bde7f10` (#381). Merge: chạy đúng `do` của `pr next` (REST ghim head) ngay khi `merge`; steward hay merge trước (`405 Merge already in progress` = đã merge). `release-check` chạy trên worktree của `main`. Sửa guard: test đỏ trước, ca `autonomy-bench` cho mỗi 🟠; luật mới OR với luật cũ (bài học #352, #372).
- Chờ người: T-1834 gỡ `merge-gate` ở ruleset hai dự án đích rồi xoá stub; `prod_switch` 3.29.0.
- Container mới: `scripts/dev-task.sh setup`; trước khi đẩy `gate-fast`, CI là cổng đầy đủ. Subagent dùng thư mục scratch riêng (bài học audit 2026-11-01).
