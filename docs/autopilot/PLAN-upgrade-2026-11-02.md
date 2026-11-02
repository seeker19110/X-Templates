# PLAN-upgrade-2026-11-02.md — Khung X-Templates · gom mọi đề xuất 2026-11-02 (audit D-302 + ADR-0064 D-303) + phần mở của PLAN-harden

> Lập ngày 2026-11-02 theo yêu cầu chủ dự án "cập nhật tất cả đề xuất, nâng cấp trong hôm nay rồi tối ưu lại và triển khai".
> Duyệt: D-304 (phiên chính tự duyệt). Pha `harden`; review 1 lần theo ADR-0062. Nguồn việc: `docs/ops/AUDIT-REPORT-2026-11-02-full.md`
> §5 (D-302, đợt P0/P1/P2), [ADR-0064](../adr/0064-multi-provider-harness.md) §Quyết định (lát A–E, D-303), và 5 task còn mở của
> [`PLAN-harden-2026-11-01.md`](PLAN-harden-2026-11-01.md) (chép nguyên dòng, cùng ID — file đó không còn là PLAN đang chạy).
>
> **Cú pháp bắt buộc cho máy:** mỗi task một dòng `- [ ] \`T-NNNN\` <việc> — Gate: \`<lệnh>\``. `topo:` theo ADR-0061.

## Tóm tắt (cổng duyệt)
- Hiện trạng: `main` `9069947` (#402); `audit check --strict` đỏ (4 🔴 guard SEC-247/309/310/311, 16 🟠, nợ review); 3.30.0 NO-GO.
- Tối ưu so với ba danh sách gốc: (a) gộp việc trùng — AUD-SEC-329 (mã lý do) và AUD-DOC-181 (ADR-0017 lệch mã) vào lát A của
  ADR-0064 (`T-3640`); AUD-HAR-036/198 (matcher) đi cùng AUD-CI-027/028 phần an toàn (`T-3650`); AUD-TEST-051 (mutation) đi cùng
  AUD-HAR-199 (đo chặn oan) vì cùng chạm guard + lịch tuần (`T-3655`); (b) thứ tự theo rủi ro rồi phụ thuộc: 🔴 guard → 🟠 xt.py/
  harness → lõi trung lập + sandbox → P1 → adapter → nội dung → sổ/phát hành; (c) **không làm trong PLAN này** (cần ADR/đợt riêng,
  ghi ở cuối): AUD-ARCH-008 tách `xt.py` (D-142 chờ số đo — đo ở `T-3640`/`T-3652`), AUD-DOC-179 module mới cho 4 hồ sơ + 393
  Kiểm "nửa" (đợt nội dung riêng), AUD-PERF-014 (`app --smoke` 30 s — đo route trước, 🟢).
- Cách làm: mỗi lát một PR ≤ ~150 dòng mã (task lớn tách PR trong lát), test đỏ trước (mẫu tái hiện của sổ), lát guard
  `(topo: review)`; corpus 991 ca không đổi quyết định; đo chặn oan trên kho lệnh thật trước mỗi PR guard; sau mỗi PR cập nhật
  dòng sổ `đã sửa #N`.

## Ngân sách (4 con số)
- Số vòng tối đa: bỏ trống (`--single-session`) · Chi phí: 0 đồng ngoài phiên · Timeout Gate: 1200 giây · Hạn: 96 giờ sau `loop init`

## Điểm dừng bắt buộc về hành động
- Merge PR: máy (`pr next` → `merge`) hoặc `pr-steward`; phiên này bị bộ phân loại Auto chặn lệnh merge → không thử cách khác
  (LOOP-STOP-025), chờ steward.
- Cài công cụ agent hãng khác để chạy thật (lát B), bật sandbox mặc định cho dự án đích, đổi mức `LOOP-HARNESS-022` lần nữa,
  cắt bản 3.30.0 và ký GO-NO-GO: việc người → `loop defer`.

## Thứ tự & lý do
1. Lát 1 🔴 guard (PLAN-harden `T-3637`, `T-3633`): lý do `audit --strict` đỏ, chặn phát hành.
2. Lát 2 🟠 mới của audit (sổ review không khoá, G7 không ép GO-NO-GO, matcher hook, CI an toàn): rẻ, đóng lệch quy trình.
3. Lát 3 ADR-0064 A/E/F: lõi trung lập + sandbox kiểm bằng máy + research lại — nền cho adapter.
4. Lát 4 P1 chất lượng/vận hành: sổ, cache guard, YAML/REST, CI/SBOM, mutation + đo chặn oan, golden test.
5. Lát 5 ADR-0064 B/C/D: 6 adapter (OSI trước), sàn git hook, vòng lặp ngoài.
6. Lát 6 nội dung khung rẻ (P2): gộp trùng PII/OIDC, `validate` kiểm ID trỏ + độ tươi, 7 template, không copy `research/`.
7. Lát 7 phần còn lại PLAN-harden (`T-3634`, `T-3635`, `T-3636`) + vệ sinh PROGRESS → `release-check` chỉ còn hàng chờ người.

## Task

### Lát 1 — guard 🔴 (P0; chép từ PLAN-harden-2026-11-01)
- [x] `T-3637` Shell lồng theo argv đã chuẩn hoá (review lát B): đầu `sh -c`/`eval` sau cờ/lệnh bọc/tên có nháy, shell đọc script dựng lúc chạy qua `<<<`/heredoc không nháy/`<(…)`/`source <(…)`, ống vào shell qua lệnh bọc/`2>&1`/khâu giữa/hàm — AUD-SEC-309…311; kèm AUD-SEC-247 (container lan BUDGET, cùng lớp "không đọc chắc thì không hạ thành hỏi") (topo: review; files: .claude/hooks/guard.py, tests/test_guard_strict.py, tests/fixtures/autonomy/) — Gate: `python3 -m unittest -q tests.test_guard_strict && python3 scripts/xt.py autonomy-bench`
- [x] `T-3633` AUD-SEC-248 (ghi đè `STAGE.json` mức thư mục), AUD-SEC-307 (chuỗi trong lời gọi thực thi `os.system`/`subprocess.run(["bash","-c",S])` qua tập con — nợ review #395, thêm 2026-11-02 theo AUD-DOC-185), 🟢 AUD-PERF-010 (đánh giá vị từ stdin một lần mỗi khâu); AUD-SEC-247 đã làm cùng T-3637 (sau: T-3637; topo: review; files: .claude/hooks/guard.py, tests/test_guard_strict.py, tests/fixtures/autonomy/) — Gate: `python3 -m unittest -q tests.test_guard_strict && python3 scripts/xt.py autonomy-bench`

### Lát 2 — 🟠 mới của audit 2026-11-02 (P0)
- [ ] `T-3648` AUD-CODE-036: `pr reviewed`/`pr debt`/`pr rethink` đọc–sửa–ghi `reviews.json` trong `_state_lock` (như `state.json`, ADR-0054); test race hai tiến trình đỏ trước (sau: T-3637; topo: review; files: scripts/xt.py, tests/test_merge.py) — Gate: `python3 -m unittest -q tests.test_merge && python3 -m mypy --strict scripts/xt.py`
- [ ] `T-3649` AUD-HAR-197: `release-check` thêm hàng `go_no_go_file` (BLOCKER ở M/L: `docs/ops/GO-NO-GO-*-v<VERSION>.md` tồn tại và không còn `[ ]` BLOCKER; S = SHOULD) + GO-NO-GO 3.29.0 hồi tố có ghi chú "lập sau phát hành"; mẫu GO-NO-GO và `release-check --help` cập nhật (sau: T-3648; topo: self; files: scripts/xt.py, tests/test_xt_cli.py, docs/ops/, framework/templates/GO-NO-GO.md, CHANGELOG.md) — Gate: `python3 -m unittest -q tests.test_xt_cli && python3 -m mypy --strict scripts/xt.py`
- [ ] `T-3650` AUD-HAR-036/198 + AUD-CI-027 + AUD-CI-028 (phần an toàn): matcher PreToolUse thêm `NotebookEdit` (guard `edit` đọc `notebook_path`), matcher MCP ghi thêm `create_branch|create_repository|fork_repository|issue_write|sub_issue_write|delete_file`; `doctor` kiểm hai matcher; `secret-scan.yml` thêm `schedule` tuần; `persist-credentials: false` ở mọi `actions/checkout` của `ci.yml` (sau: T-3649; topo: review; files: .claude/settings.json, .claude/hooks/guard.py, .claude/hooks/pre-edit-guard.sh, scripts/xt.py, tests/test_hooks.py, tests/test_doctor.py, .github/workflows/ci.yml, .github/workflows/secret-scan.yml, tests/test_ci.py, framework/templates/) — Gate: `python3 -m unittest -q tests.test_hooks tests.test_doctor tests.test_ci && python3 scripts/xt.py ci-check`

### Lát 3 — ADR-0064 lõi trung lập, sandbox, research lại
- [ ] `T-3640` `guard.py core`: schema trung lập `{tool, command|path|tool_name, input, cwd, project_dir}` → `{decision, code, reason}`; mỗi luật trả `code` tường minh, `REASON_CODES` chỉ còn fallback (AUD-SEC-329); chế độ `bash|edit|mcp|permission` thành adapter Claude gọi lõi; deny luôn in JSON + exit 2; test duyệt mọi mã có ≥ 1 ca end-to-end; đo thời gian hook trước/sau; ADR-0017 §2 ghi chú lệch mã (AUD-DOC-181, không sửa nội dung ADR cũ — thêm "Ghi chú 2026-11-02") (sau: T-3650; topo: review; files: .claude/hooks/guard.py, .claude/hooks/pre-bash-guard.sh, .claude/hooks/_lib.sh, tests/test_hooks.py, tests/test_guard_corpus.py, tests/test_guard_strict.py, docs/adr/0017-allow-all-bash-behind-fences.md) — Gate: `python3 -m unittest -q tests.test_hooks tests.test_guard_corpus tests.test_guard_strict && python3 scripts/xt.py autonomy-bench`
- [ ] `T-3641` `xt.py doctor` nhóm `sandbox`: đọc cấu hình theo công cụ (Claude `sandbox.enabled` + `allowedDomains`; Codex `sandbox_mode`; Gemini `tools.sandbox`; Cursor `sandbox.json`; Copilot `/sandbox`; Grok `--sandbox`; OpenCode không có → cảnh báo cần devcontainer/`srt`), đỏ khi `loop init --single-session` không người trực mà không có sandbox; Kiểm của `LOOP-HARNESS-022` trỏ doctor (sau: T-3640; topo: review; files: scripts/xt.py, tests/test_doctor.py, framework/11-autonomous-loop/harness-files.md, CHANGELOG.md) — Gate: `python3 -m unittest -q tests.test_doctor && python3 scripts/xt.py validate`
- [ ] `T-3647` `/research` lại 4 mục chưa xác minh (shell tool tôn trọng `SHELL`/`PATH`; hook Cursor trong CLI/`-p`; payload stdin của Copilot; mã thoát headless từng công cụ) ghi vào `research/2026-11-02-multi-provider-harness.md` §6 → §3; bảng công cụ × hook × sandbox vào `harness-files.md`; ADR-0064 `Trạng thái triển khai` theo PR (sau: T-3640; topo: self; files: research/, framework/11-autonomous-loop/harness-files.md, docs/adr/0064-multi-provider-harness.md, CHANGELOG.md) — Gate: `python3 scripts/xt.py checks && python3 scripts/check-links.py`

### Lát 4 — P1 chất lượng và vận hành
- [ ] `T-3651` AUD-DOC-180 lưu trữ sổ: dòng `đã sửa` của PR đã merge trước 3.28.0 sang `docs/ops/AUDIT-STATUS-ARCHIVE.md` (máy đọc cả hai file ở `audit check`, `pr debt`, `release-check`), `DECISIONS.md` tách theo tháng (`DECISIONS-2026-10.md`), CHANGELOG < 3.20 sang `CHANGELOG-ARCHIVE.md` (`changelog-check` vẫn xanh); trần `docs/ops` và `docs/autopilot` vào `DIR_CAPS` = kích thước sau lưu trữ + 5 % (sau: T-3647; topo: review; files: docs/ops/, docs/autopilot/, CHANGELOG.md, tests/test_docs_budget.py, scripts/xt.py, tests/test_xt.py) — Gate: `python3 scripts/xt.py audit check docs/ops/AUDIT-STATUS.md && python3 -m unittest -q tests.test_docs_budget tests.test_xt tests.test_merge`
- [ ] `T-3652` AUD-PERF-013 cache bytecode guard có kiểm sha256 nguồn (giữ lý lẽ AUD-SEC-074): `_lib.sh py_run` chỉ nạp cache khi sha256 nguồn khớp khoá cache trong thư mục do `install.py`/`doctor --fix` tạo, sai khớp → compile từ nguồn như cũ; đo 5 lần trước/sau (sau: T-3640; topo: review; files: .claude/hooks/_lib.sh, .claude/hooks/guard.py, scripts/install.py, scripts/xt.py, tests/test_hooks.py) — Gate: `python3 -m unittest -q tests.test_hooks && bash -n .claude/hooks/_lib.sh && shellcheck --severity=warning .claude/hooks/_lib.sh`
- [ ] `T-3653` AUD-CODE-037/038: `yaml_scalar`/`yaml_get` ca biên (`"a" "b"`, `'it''s'`) + `doctor` cảnh báo khoá thụt lề bị bỏ; `latest_framework_tag` qua `_gh_api` (timeout tham số, fail-open giữ nguyên); một runner `_run(cmd, cwd, timeout, env)` thay 4 biến thể (sau: T-3649; topo: self; files: scripts/xt.py, scripts/dev-task.sh, tests/test_xt_core.py, tests/test_doctor.py) — Gate: `python3 -m unittest -q tests.test_xt_core tests.test_doctor && python3 -m mypy --strict scripts/xt.py`
- [ ] `T-3654` AUD-CI-028 + AUD-DEP-010: `cache: pip` theo hash requirements ở mọi job cài `requirements-dev.txt`; `fetch-depth: 0` chỉ ở job cần lịch sử (xác minh test không cần); SBOM CycloneDX từ `pip-audit -f cyclonedx-json` làm artefact ở `dep-audit`; `attest-build-provenance` ở `release-tag.yml` (`id-token: write`, `attestations: write`) (sau: T-3650; topo: review; files: .github/workflows/ci.yml, .github/workflows/dep-audit.yml, .github/workflows/release-tag.yml, tests/test_ci.py, docs/ops/DEPENDENCIES.md, CHANGELOG.md) — Gate: `python3 -m unittest -q tests.test_ci && python3 scripts/xt.py ci-check`
- [ ] `T-3655` AUD-TEST-051 + AUD-HAR-199: mutation có kết quả trên `decide/apply_policy/_strict_why` (mutator stdlib đảo `deny↔""`/`ask↔""`, ≤ 20 phút, workflow lịch tuần, đỏ khi mutant sống > 0 ở tập này) + `runs.jsonl`/hook ghi đếm `BUDGET`/`deny` theo phiên, `loop stats` báo tỉ lệ chặn; lý do BUDGET kèm một dòng "viết lại: …" (sau: T-3640; topo: review; files: scripts/xt.py, .claude/hooks/guard.py, .github/workflows/, tests/test_xt_loop.py, tests/test_hooks.py, CHANGELOG.md) — Gate: `python3 -m unittest -q tests.test_xt_loop tests.test_hooks && python3 scripts/xt.py ci-check`
- [ ] `T-3656` AUD-TEST-050: 58 `assertEqual` stdout nguyên văn ở `tests/test_xt_cli.py` → so dữ liệu `--json`/mã thoát/`assertRegex` theo mã lỗi (giữ 1–2 golden có chủ đích) (sau: T-3653; topo: self; files: tests/test_xt_cli.py) — Gate: `python3 -m unittest -q tests.test_xt_cli`

### Lát 5 — ADR-0064 adapter (nguồn `framework/templates/harness/<tool>/`, `install.py --harness`), sàn git hook, vòng lặp ngoài
- [ ] `T-3642` Adapter Codex (`.codex/hooks.json`, `permissionDecision: deny`, `ask` → `deny`) và Gemini CLI (`hooks` trong `.gemini/settings.json`, `BeforeTool`, `decision: deny`) + cầu nối `GEMINI.md` ≤ 5 dòng trỏ `AGENTS.md`; `install.py --harness codex,gemini`; fixture payload thật (bản + ngày) ở `tests/fixtures/harness/`; ≥ 10 ca `autonomy-bench` mỗi công cụ; test "deny tường minh khi hook lỗi" (sau: T-3640, T-3647; topo: review; files: framework/templates/harness/, scripts/install.py, tests/test_install.py, tests/fixtures/harness/, tests/fixtures/autonomy/) — Gate: `python3 -m unittest -q tests.test_install tests.test_autonomy_bench && python3 scripts/xt.py autonomy-bench`
- [ ] `T-3643` Adapter Cursor (`.cursor/hooks.json` `version: 1`, `beforeShellExecution` `permission`, `failClosed: true`) và Copilot CLI (`.github/hooks/xt.json`, `preToolUse` `permissionDecision` + `permissionDecisionReason`) + cầu nối `.cursor/rules/xt.mdc`, `.github/copilot-instructions.md` ≤ 5 dòng; kiểm không nạp hai lần khi công cụ cũng đọc `.claude/settings.json` (sau: T-3642; topo: review; files: framework/templates/harness/, scripts/install.py, tests/test_install.py, tests/fixtures/harness/) — Gate: `python3 -m unittest -q tests.test_install tests.test_autonomy_bench && python3 scripts/xt.py autonomy-bench`
- [ ] `T-3644` Adapter Grok Build (`.grok/hooks/xt.json`, khoá camelCase `toolName`/`toolInput`, `decision: deny`; ghi rõ Stop không chặn) và OpenCode (`.opencode/plugins/xt.ts` ≤ 20 dòng gọi `xt.py guard-check` rồi `throw`; không logic trong TS) (sau: T-3643; topo: review; files: framework/templates/harness/, scripts/install.py, tests/test_install.py, tests/fixtures/harness/) — Gate: `python3 -m unittest -q tests.test_install tests.test_autonomy_bench && python3 scripts/xt.py autonomy-bench`
- [ ] `T-3645` `install.py` cài git hook `pre-commit` (chạy `dev-task.sh gate-fast` theo `commit_gate`, kiểm `ai_attribution`) và `pre-push` (chặn push nhánh chính, force) — copy-if-absent, không đè hook người dùng; mẫu `AGENTS.md` §7 ghi git hook là sàn cho công cụ không có hook chặn (sau: T-3647; topo: self; files: scripts/install.py, framework/templates/, tests/test_install.py) — Gate: `python3 -m unittest -q tests.test_install`
- [ ] `T-3646` `xt.py loop run --agent claude|codex|gemini|cursor|copilot|grok|opencode [--dry-run]`: gọi headless từng task theo bảng lệnh trong ADR-0064, giữa các lượt `loop record`/`loop verify`, dừng theo `defer`/`block` và ngân sách `LOOP-*`; không tin exit code của agent; test với agent giả (script in JSON) xanh/đỏ theo bằng chứng (sau: T-3640, T-3647; topo: review; files: scripts/xt.py, tests/test_xt_loop.py, framework/11-autonomous-loop/README.md, CHANGELOG.md) — Gate: `python3 -m unittest -q tests.test_xt_loop && python3 scripts/xt.py checks`

### Lát 6 — nội dung khung (P2 rẻ)
- [ ] `T-3657` AUD-DOC-176: 5 MUST PII-log (`CMP-PRIV-008`, `OPS-OBS-008`, `AI-OBS-004`, `AI-GUARD-004`) trỏ nhà `BASE-ERR-007`, giữ góc riêng, bỏ vế trùng; `BASE-DEP-013`/`PRF-LIB-005` trỏ `SEC-SUPPLY-021`; `WF-CI-011`/`OPS-DEPLOY-007`/`OPS-IAC-014` trỏ `SEC-SECRET-009` (giữ ID, giữ mức, cập nhật `updated`) (sau: T-3647; topo: self; files: framework/, CHANGELOG.md) — Gate: `python3 scripts/xt.py validate && python3 scripts/check-links.py`
- [ ] `T-3658` AUD-DOC-182 + AUD-DOC-177: `validate` kiểm mọi ID được trỏ (`\b[A-Z]{2,5}-[A-Z0-9]{2,8}-\d{3}\b` ngoài dòng định nghĩa) tồn tại; 6 trích dẫn `XT-H-0xx` đổi thành `stored§XT-H-0xx`; `validate --stale <ngày>` đọc "xác minh YYYY-MM-DD" cảnh báo > 180 ngày (sau: T-3657; topo: self; files: scripts/xt.py, framework/, tests/test_xt.py, CHANGELOG.md) — Gate: `python3 -m unittest -q tests.test_xt && python3 scripts/xt.py validate`
- [ ] `T-3659` AUD-DOC-178: 7 template mà MUST đang đòi file (`TARGETS.md`/SLO, `RPO-RTO.md`, `RISKS.md`, `limitations.md`, `GLOSSARY.md`, `privacy/processors.md` + `data-map.yaml`, `VULN-SLA.md`) theo quy ước `templates/README.md`; mục MUST liên quan trỏ mẫu (sau: T-3658; topo: self; files: framework/templates/, framework/, CHANGELOG.md) — Gate: `python3 scripts/xt.py validate && python3 scripts/check-links.py`
- [ ] `T-3660` AUD-XFEAT-046: `install.py` chỉ copy file trong `research/` được module `framework/` trỏ tới (hoặc đổi liên kết sang URL repo khung), `check-links` xanh ở dự án đích; đo lại kích thước `.xtemplates/` (sau: T-3659; topo: self; files: scripts/install.py, tests/test_install.py, framework/) — Gate: `python3 -m unittest -q tests.test_install && python3 scripts/check-links.py`

### Lát 7 — phần còn lại PLAN-harden, sổ, phát hành (chép từ PLAN-harden-2026-11-01)
- [ ] `T-3634` AUD-SEC-259–263, 276 (scanner prompt-assets), AUD-HAR-169 (`next-step --package`), AUD-HAR-182 (`pr debt --fixed`), AUD-CI-024 (Kiểm `BASE-REPO-005`) (sau: T-3633; topo: review; files: scripts/xt.py, tests/test_xt_cli.py, tests/test_merge.py, tests/test_next_step.py, BLUEPRINT.md) — Gate: `python3 -m unittest -q tests.test_xt_cli tests.test_merge tests.test_next_step && python3 -m mypy --strict scripts/xt.py`
- [ ] `T-3661` AUD-DOC-175 + AUD-CI-026: `/handover` vệ sinh PROGRESS.md (SHA bàn giao, dời mục đã xong, gắn hạn việc chờ người, ≤ 8 KB); Kiểm `BASE-SEC-006` dạng `<(…)` an toàn pipefail (sau: T-3634; topo: self; files: PROGRESS.md, BLUEPRINT.md, framework/01-baseline/security-minimum.md) — Gate: `python3 scripts/xt.py checks && python3 scripts/xt.py blueprint-status BLUEPRINT.md --strict --run`
- [ ] `T-3635` AUD-DOC-159; 🟢 nợ review: sửa nhóm tài liệu rẻ, còn lại `chấp nhận` (chủ + hạn, lý do từng dòng); 🔴/🟠 lát A–E `đã sửa` (sau: T-3634; files: docs/, CHANGELOG.md) — Gate: `python3 scripts/xt.py audit check docs/ops/AUDIT-STATUS.md --strict`
- [ ] `T-3636` `loop verify --all` xanh, `release-check` chỉ còn hàng chờ người (`prod_switch`, chữ ký GO-NO-GO) (sau: T-3635; topo: audit) — Gate: `python3 scripts/xt.py audit check docs/ops/AUDIT-STATUS.md --strict && python3 scripts/xt.py blueprint-status BLUEPRINT.md --strict`

## Không làm trong PLAN này (ghi để không quên)
| Việc | Lý do | Nhà kế tiếp |
|---|---|---|
| AUD-ARCH-008 tách `xt.py` thành gói | D-142 "chưa đo"; `T-3640`/`T-3652` đo thời gian lát trước/sau rồi mới quyết | ADR mới sau PLAN này |
| AUD-DOC-179 module riêng mobile/desktop/IoT/game, 393 Kiểm "nửa", trần tổng MUST | đợt nội dung lớn, cần research theo hồ sơ | PLAN nội dung riêng |
| AUD-PERF-014 `app --smoke` 30 s | 🟢; đo từng route trước (`xt_app`) | khi chạm `scripts/xt_app` |

## Phụ thuộc ngoài
| Việc | Bên ngoài | Ngày cam kết | Kế hoạch B |
|---|---|---|---|
| Merge PR | `pr-steward` (cron 10 phút / `check_suite`) vì phiên bị chặn lệnh merge | — | chủ dự án chạy lệnh `pr next` in ra |
| Hợp đồng hook 6 công cụ | docs chính chủ, đổi nhanh | mốc xét lại 2027-01-21 | fixture theo phiên bản đỏ → sửa adapter |
| Chạy thật công cụ hãng khác | chủ dự án cài trên máy có sandbox | — | `loop defer`; test payload giả |
