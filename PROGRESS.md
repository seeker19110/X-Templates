# PROGRESS.md — Khung X-Templates

> Giai đoạn hiện tại: G8 Vận hành & tiến hoá (khung 3.32.0, pha `harden` — D-136) · Cập nhật: 2026-11-08 · Nhánh: claude/festive-gauss-i861qa

## Đang làm
- 2026-11-08 nghiên cứu [tự động hoá tới mức máy làm được](research/2026-11-08-full-automation.md) (247 điểm chờ → 41 nhóm, lộ trình S1–S11) + **ADR-0074** agent ký §5 GO-NO-GO (chủ repo quyết, D-401; `xt.py release-sign`; phản biện 3/3 bác bản đầu → siết, D-402). Kế tiếp: PR riêng bật `release_signoff: agent` ở `xt.yaml` (HARD_GATED → **chủ repo merge**), rồi S1–S3 của nghiên cứu.
- 3.32.0 đã ký §5 (#476); D-126 đã quyết (D-400); GO-NO-GO 3.29.0…3.31.1 không ký — bản sau thay, không chặn gì. T-3557 (`PLAN-harden-2026-10-27-loops.md`) còn `[ ]` — tick qua `loop record` khi chạy lại Gate của nó.
- Dự án đích (`main` 2026-11-08, [registry](docs/ops/registry.json)): cả 4 (hotel-manager, X-Company, xboss, dhcb) ở 3.32.0 (#154, #102, #717, #1489). GO-NO-GO của dự án cần dòng `subject:` khi người ký lại (D-389).
- 2026-11-07 **cắt 3.32.0** (nhánh `chore/release-3.32.0` từ `f99c348`, D-395): #462 fixture output thật (gitleaks có leak ra PASS — AUD-HAR-315), #463 chữ ký GO-NO-GO gắn ứng viên bằng dòng `subject:` đủ 64 hex (AUD-HAR-219), #464/#468/#469 guard chặn agent tự ký GO-NO-GO (AUD-SEC-497, 533…540), #466/#467 trả nợ review. `audit check --strict` exit 0. **3.32.0 đã cắt** (`6bcd2c9`, tag `v3.32.0`), §5 đã ký (#476). Còn mở: AUD-TEST-061 (CodeQL); fixture host Codex/Gemini.
- Phép đo `LOOP-ORCH-020` tích luỹ; tăng số agent chỉ khi có số (ADR-0061). Phản hồi dự án đích: 10 nhóm `cong-cu` chờ phân loại ([TARGETS](docs/ops/TARGETS.md)).
- Hoãn tới harden: T-1690/T-1691 (quét lại SEC-091…099). Rà `seeker19110/stored`: chờ chủ repo (HAR-036/041, SEC-026, CI-006/7/9, SEC-043; hạn xét: 2026-12-31).

## Tiếp theo
1. Phản hồi dự án đích qua `xt.py feedback`; PR nâng do `pr-steward` của từng dự án merge.
2. **Kế tiếp:** AUD-HAR-325 đã sửa (#472, vào bản kế — dự án đích nhận khi nâng); chưa có việc cắt bản gấp. Mục 3–5 bên dưới.
3. PLAN-harden-2026-10-27-loops còn T-3554 (pilot `next-step`) và T-3555 (lát 5: field trigger, bot nâng bản, worker ngoài phiên). 🟢 mở của `perf trial`/`dev-task.sh` rà ở audit kế (sổ: AUD-HAR-294…297, AUD-TEST-082/083, AUD-PERF-020…025).
4. Còn: máy hoá `LOOP-HARNESS-031` (dấu hook theo phiên), `LOOP-STOP-030` (ConfigChange); task `[perf]` trong `loop` (D-041); URL phiên do máy chủ MCP gắn vào thân PR; ép báo "đã đo/chưa đo" cho task UI (`LOOP-DESIGN-021`); sàn quyền token; `xt.pyz` (ADR-0010); ca đối kháng cho `autonomy-bench`; `project-commands.sh` được `source` hai lần mỗi task.
5. Giới hạn guard đã biết: ở sổ audit và `harness-files.md`; tên dựng lúc chạy chấp nhận tới 2027-01-21 (AUD-SEC-406, ADR-0067). Đánh giá sandbox Bash opt-in cho khung trước 2027-01-21 (D-331/D-332); cùng đợt T-3709 đo chi phí compile `guard.py` mỗi lệnh Bash (ADR-0072, hạn 2027-01-21). **Xét lại hàng rào 2027-01-21** hoặc khi đổi model (LOOP-DESIGN-014; Claude Code ≥ `claude_min_version`).
6. Giữ cổng: C901 ≤ 10, `mypy --strict`, coverage dòng + nhánh 100 %, `changelog-check`, trần byte file + tổng thư mục (`tests/test_docs_budget.py`, ADR-0043) — không `noqa`/pragma, không nới trần.

## Quyết định
> Chi tiết ở `docs/adr/` (ADR-0001…0072) và `docs/autopilot/DECISIONS.md` (D-NNN); ở đây chỉ giữ điều chưa có nhà khác.
- Khung = thư viện yêu cầu có ID + ghép blueprint + máy kiểm "xong" (ADR-0001); hook fail-open về luồng, fail-closed về hành động nguy hiểm (ADR-0002); blueprint theo quy mô S/M (ADR-0003/0004/0012).
- Luật VN: Luật 91/2025/QH15 + NĐ 356/2025 (thay NĐ 13/2023 từ 01/01/2026); Luật ANM 116/2025 (01/07/2026). OWASP LLM Top 10 2026; EU AI Act Đ.50 áp dụng 02/08/2026. Mặc định OSI: OpenTofu, Valkey.
- Repo khung: Python ≥ 3.11; `mypy --strict`; coverage 100 % (cả subprocess); `changelog-check`/`progress-check` trong `lint`; PROGRESS chỉ ghi SHA trên `main` (squash-merge). Tên: X-stored → X-Templates (ADR-0006/0007).
- Commit/PR không ghi tên model hay URL phiên AI (LOOP-HARNESS-027); tag phát hành qua `release-tag.yml` — gọi bằng REST `workflow_dispatch` (`gh workflow run` cần GraphQL, bị chặn trong phiên).
- Autopilot: tự duyệt (ADR-0008), một phiên (ADR-0009), phản hồi dự án đích (ADR-0010), cổng rỗng là đỏ (ADR-0011), `doctor --fix` đầu tiên; pha build/harden (ADR-0031), tối giản pha build (ADR-0033). Merge theo làn (ADR-0013…0016, 0020, 0024/0025, 0028/0032), steward (ADR-0027); cơ chế: merge ghim head, không auto-merge, không `merge-gate` (ADR-0036). Guard không hỏi người (ADR-0018/0019), ghi tay `.autopilot/` bị chặn (ADR-0026). Reviewer năng lực cao hơn người viết (D-161): cần review thì spawn agent mới và chỉ định `model`. Cấu hình agent theo loại việc, `max_rethink` 1/PR (ADR-0061).
- Phiên nhiều lát: mỗi lát một nhánh 1-commit từ `origin/main` (hoặc xếp chồng rồi rebase sau khi lát trước merge), mở PR tuần tự; guard chặn force-push; sửa PR đang mở khi cây bẩn → worktree riêng.
- Sửa thân PR (chân trang do máy chủ MCP gắn) từng kích `edited` → chỉ `pr-title.yml` nghe `edited`. Phiên khung không merge được PR ở repo khác → để `pr-steward` của dự án merge ghim head.
- CI không còn kiểm macOS (gỡ `portability.yml` 2026-10-17). Nợ chấp nhận: 4 MUST/module là phán đoán; số điều NĐ 356/2025 chưa đối chiếu bản gốc. Không làm (D-142): tách `xt.py`, song song worktree, merge queue, reviewer LLM mọi PR, thu nhỏ guard.
- Coverage cục bộ < 100 % khi `coverage` cài ở site người dùng: hook chạy `python3 -I` nên tiến trình con không được đo — CI là cổng coverage (đo 2026-11-05).

## Bàn giao phiên
- `main` `a09f7a7` (#479). Nhánh `claude/festive-gauss-i861qa`: nghiên cứu tự động hoá + ADR-0074 (mã ký; khoá bật ở PR sau, D-402).
- Chờ người (một lần, gom theo lát S8 của nghiên cứu): fixture Codex/Gemini (tài khoản trả phí); T-1834 gỡ `merge-gate` ở ruleset hai dự án đích rồi xoá stub (hạn xét: 2026-12-31); ruleset X-Templates sống còn tắt resolve thread + bật "Allow auto-merge" (RUNBOOK-PR-STEWARD §1), `XT_STEWARD_TOKEN` (một GitHub App); Dependabot security updates. Máy làm được, chưa làm (lộ trình nghiên cứu): Routine tuần `feedback aggregate` có tồn tại nhưng push 403 vì thiếu nguồn repo (S2); bỏ `pull_request_target` khỏi `pr-review.yml` trước 2026-12-02 (S3); T-1508 ghi D-NNN không bật (S1).
- Autopilot: không chạy (phiên tương tác). `pr stats --days 7` (2026-11-05):

| PR merge trong 7 ngày (từ 2026-10-29) | Giá trị |
|---|---|
| PR đã merge | 112 |
| Lead time mở → merge (trung vị · P95) | 0.7 giờ · 9.12 giờ |
| Run CI `pull_request` mỗi PR (trung vị · P95 · tổng) | 2.5 · 6 · 338 |
| Run `failure` · `cancelled` (tỉ lệ) | 33 · 32 (19%) |
| PR làn chuẩn (`xt-standard-lane`) | 97 |
| PR revert | 0 |
| Push (head SHA riêng biệt) mỗi PR (trung vị · P95 · tổng) | 2.5 · 6 · 338 |
| PR xanh ngay lần push đầu | 86/112 (77%) |
| Run `cancelled` cùng SHA với run khác | 0 |

- Container mới: `scripts/dev-task.sh setup`; trước khi đẩy `gate-fast`, CI là cổng đầy đủ. Subagent dùng thư mục scratch riêng (bài học audit 2026-11-01). Gate cục bộ: `coverage` và `pip` phải ở site-packages của `python3` (hook chạy `python3 -I`, bỏ user site → mất coverage subprocess) — dùng venv.
