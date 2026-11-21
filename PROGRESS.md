# PROGRESS.md — Khung X-Templates

> Giai đoạn hiện tại: G8 Vận hành & tiến hoá (khung 3.34.0, pha `harden` — D-136) · Cập nhật: 2026-11-21

## Đang làm

- 2026-11-19 **3.34.0 đã phát hành** (tag `v3.34.0` = `ef146b0`, agent ký GO-NO-GO §5 ở #674): harden ADR-0080 xong 14 đợt (D-494…D-509; guard mặc định chặn D-503; giới hạn đã biết ở `harness-files.md`, có hạn 2027-01-21). Đợt [audit 20/11](docs/ops/AUDIT-REPORT-2026-11-20-delta.md) rà 13 nhóm (SEC, PERF và DOC rút gọn); 🟠 chấp nhận AUD-DEP-037 (D-514).
- ADR-0081 (D-511, #673): `compose` giữ quy mô cũ (lỗi đọc → dừng), mặc định mới S; `doctor` ở build không cảnh báo chậm MINOR/PATCH ([đo](research/2026-11-19-target-project-speed.md)). Nâng khung kèm `actions/setup-python` 3.15.2 ở CI dự án (ADR-0078).
- D-524 (#694): [`plan waves --handoff`](docs/adr/0086-plan-wave-handoff.md) gộp ngữ cảnh đợt đầu và giảm tổng số đợt từ 463 xuống 444 khi phát lại 42 PLAN.
- D-522/523: trình MVP sau smoke; [vòng sửa–thử nhanh](docs/adr/0085-fast-development-feedback.md).
- **Factory**: [MVP ghi chú](docs/ops/FACTORY-PILOT-1.md) có bốn ca xanh (#699); quyền triển khai, trần duyệt và G7 đã nối (#701); `feedback routine-check` (#700). Điều kiện vận hành và số đo còn thiếu ở [PLAN](docs/autopilot/PLAN-factory-e2e.md).
- **Guard** (#704, D-530): chặn đường lách tag phiên bản (`--follow-tags`, `fetch` vào `refs/tags/`, cụm cờ `gh release`, glob) — AUD-SEC-996/997 đã sửa. AUD-SEC-999 (giá trị cờ `gh release` không nháy tách được) sửa ở #707. Nợ 🟢: AUD-HAR-449/450/451, AUD-SEC-998, AUD-TEST-133.
- Dự án đích ([registry](docs/ops/registry.json)): X-Company, xboss, dhcb, x-shop và hotel-manager ở 3.34.0. [Pilot lọc tầng](research/2026-11-20-hotel-floor-pilot.md) từ checkout đến merge mất 18 phút 11 giây. Còn mở AUD-TEST-061 (CodeQL), bài kiểm host Codex/Gemini.
- D-457: PLAN factory-A/BE đã lưu kho. `LOOP-ORCH-020`: chỉ tăng agent khi có số. [Đã phân loại 10 nhóm phản hồi công cụ](docs/ops/FEEDBACK-ROUTINE-CHECK.md). Hoãn: T-1690/T-1691 (quét lại SEC-091…099); rà `seeker19110/stored` chờ chủ repo (hạn xét 2026-12-31).

## Tiếp theo
1. Đợt 16–17 xong (D-516…D-518, #676–#680): CI `test` 8 shard (#696), ban đầu 6 shard, `test-select` chọn theo lớp, `/complete` chạy lại `doctor` sau `harden`, commit trong worktree cùng repo qua cổng commit. Còn mở: AUD-HAR-443 (T-3977). Nợ: AUD-TEST-131, AUD-HAR-444.
1a. Đợt 18 xong (ADR-0082, D-519/D-520, #684, #685, #689, #693): harness Codex sinh từ `.claude/` (`install.py --harness codex`, `--sync-codex`, `tests.test_codex_harness`); guard bảo vệ nó và tệp nối guard host khác, chặn khôi phục tệp hàng rào từ commit cũ và giải nén vào đích máy chặn (AUD-SEC-987…990, 992 đã sửa). Chưa chạy Codex thật; tin cậy hook bằng `/hooks`. Nợ 🟢: AUD-SEC-991/993, AUD-HAR-446.
2. **Hoàn thiện** theo [PLAN-harden-2026-11-21](docs/autopilot/PLAN-harden-2026-11-21.md) (D-533, T-3974…T-3992): hạn và shard CI sát trần → PLAN khớp sổ → cổng ký, cắt 3.35.0 → production hotel-manager (cần VPS, tên miền, grant) → việc kế theo số đo → hạn 2027-01-21. Ngoài PLAN: stored XT-H-117…139, `pre-push.sh`, AUD-TEST-126.
3. Hạn: 2026-12-02 GitHub chặn `pull_request_target` (T-3975); 2026-12-31 rà stored; **2027-01-21** xét lại hàng rào guard + đánh giá sandbox Bash opt-in (D-331/D-332, ADR-0072) và các chấp nhận AUD-SEC-406/931/943/955/965.
4. Ruleset `main` đủ 5 check (2026-11-20). Việc của người: xoá stash `d497-dup`, `d498-dup-x9`; `XT_STEWARD_TOKEN`, Dependabot security updates (RUNBOOK-PR-STEWARD §1).
5. Còn: máy hoá `LOOP-HARNESS-031`, `LOOP-STOP-030`; task `[perf]` trong `loop` (D-041); URL phiên do máy chủ MCP gắn vào thân PR; ép báo "đã đo/chưa đo" cho UI (`LOOP-DESIGN-021`); `xt.pyz` (ADR-0010).
6. Cách làm nhanh: CI là cổng đầy đủ; PR sổ gộp vào PR sửa (mở draft để steward không merge sớm); một executor cho một tệp nóng.
7. Giữ cổng: C901 ≤ 10, `mypy --strict`, coverage dòng + nhánh 100 %, `changelog-check`, trần byte (`tests/test_docs_budget.py`, ADR-0043), không ngưỡng thời gian/CPU cứng (BASE-GATE-005), tên định danh tránh secret/token/password/credential (CodeQL) — không `noqa`/pragma, không nới trần.

## Quyết định
> Chi tiết ở `docs/adr/` và `docs/autopilot/DECISIONS.md` (D-NNN); ở đây chỉ giữ điều chưa có nhà khác.
- Khung = thư viện yêu cầu có ID + ghép blueprint + máy kiểm "xong" (ADR-0001); hook fail-open về luồng, fail-closed về hành động nguy hiểm (ADR-0002); blueprint theo quy mô S/M (ADR-0003/0004/0012).
- Luật VN: Luật 91/2025/QH15 + NĐ 356/2025 (thay NĐ 13/2023 từ 01/01/2026); Luật ANM 116/2025 (01/07/2026). OWASP LLM Top 10 2026; EU AI Act Đ.50 áp dụng 02/08/2026. Mặc định OSI: OpenTofu, Valkey.
- Repo khung: Python 3.15.x (D-485, ADR-0078); `mypy --strict`; coverage 100 % (cả subprocess); `changelog-check`/`progress-check` trong `lint`; PROGRESS chỉ ghi SHA trên `main` (squash-merge). Tên: X-stored → X-Templates (ADR-0006/0007).
- Commit/PR không ghi tên model hay URL phiên AI (LOOP-HARNESS-027); tag phát hành qua `release-tag.yml` — gọi bằng REST `workflow_dispatch` (`gh workflow run` cần GraphQL, bị chặn trong phiên).
- Autopilot: tự duyệt (ADR-0008), một phiên (ADR-0009), phản hồi dự án đích (ADR-0010), cổng rỗng là đỏ (ADR-0011), `doctor --fix` đầu tiên; pha build/harden (ADR-0031), tối giản pha build (ADR-0033). Merge theo làn (ADR-0013…0016, 0020, 0024/0025, 0028/0032), steward (ADR-0027); cơ chế: merge ghim head, không auto-merge, không `merge-gate` (ADR-0036). Guard không hỏi người (ADR-0018/0019), ghi tay `.autopilot/` bị chặn (ADR-0026). Reviewer năng lực cao hơn người viết (D-161): cần review thì spawn agent mới và chỉ định `model`. Cấu hình agent theo loại việc, `max_rethink` 1/PR (ADR-0061).
- Phiên nhiều lát: mỗi lát một nhánh từ `origin/main`, mở PR tuần tự; guard chặn force-push; sửa PR đang mở khi cây bẩn → worktree riêng.
- Sửa thân PR (chân trang do máy chủ MCP gắn) từng kích `edited` → chỉ `pr-title.yml` nghe `edited`. Phiên khung không merge được PR ở repo khác → để `pr-steward` của dự án merge ghim head.
- CI đã gỡ macOS (2026-10-17). Nợ chấp nhận: 4 MUST/module là phán đoán; số điều NĐ 356/2025 chưa đối chiếu bản gốc. D-142 chưa làm: tách `xt.py`, merge queue, reviewer LLM mọi PR, thu nhỏ guard. ADR-0075 lập kế hoạch song song worktree theo file (T-3850).
- Coverage cục bộ < 100 % khi `coverage` cài ở site người dùng: hook chạy `python3 -I` nên tiến trình con không được đo — CI là cổng coverage (đo 2026-11-05).

## Bàn giao phiên
- Mốc `main` `29ddf2d8` (#709, làn derived ADR-0087). Cổng commit đỏ làm mất stage: `git add` lại, sau commit kiểm `git show --stat HEAD`. Xét PR xanh theo số tăng dần. Phiên "tiếp tục" đọc sổ [audit](docs/ops/AUDIT-STATUS.md), PLAN-harden-2026-11-21 và CHANGELOG.
- Container mới: `scripts/dev-task.sh setup`; trước khi đẩy `gate-fast`, CI là cổng đầy đủ. Subagent dùng scratch riêng dưới `/home/liend` (không `/tmp`: tmpfs, mất khi khởi động lại). Gate cục bộ: `coverage` và `pip` phải ở site-packages của `python3` (hook chạy `python3 -I`) — venv 3.15 đầu PATH; G7 cần `fetch --unshallow --tags`; `release-check` chạy ở worktree sạch (`.agents/`, `.codex/` chưa commit làm hàng `tree` đỏ).
