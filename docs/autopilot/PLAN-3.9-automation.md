# PLAN-3.9-automation.md — Khung X-Templates · tăng tự động hóa, giữ bằng chứng (3.9.0 → 3.10.0)

> Lập ngày 2026-10-19 từ [`docs/ops/REMEDIATION-PLAN-2026-10-19.md`](../ops/REMEDIATION-PLAN-2026-10-19.md) (REC/AUTO, §7).
> Chạy **sau khi** PLAN 3.8.0 ([`PLAN.md`](PLAN.md), T-1401…T-1417) phát hành: `python3 scripts/xt.py loop init --plan
> docs/autopilot/PLAN-3.9-automation.md --single-session --max-iterations 168 --hours 24` (D-067). Duyệt kế hoạch: phiên
> chính tự duyệt theo tiêu chí chất lượng cuối (ADR-0008) và ghi D-NNN trước task đầu; reviewer khác model rà phần Gate
> (`LOOP-ORCH-018`) trước `loop decide`.
>
> **Cú pháp bắt buộc cho máy:** mỗi task một dòng `- [ ] \`T-NNNN\` <việc> — Gate: \`<lệnh>\``. Ghi chú `(sau: …; files: …)`
> là dependency/phạm vi ghi để phiên chính xếp thứ tự và tách song song (máy đọc từ T-1510 trở đi; trước đó phiên chính đọc tay).

## Tóm tắt (cổng duyệt)
- Phạm vi: §5–§6 của kế hoạch khắc phục — REC-01…04, 06…09 (P1/P2) và AUTO-01…07; REC-05 thí điểm một module; REC-12 ngoài phạm vi.
- Stack: Python ≥ 3.11 stdlib, bash, GitHub Actions; không phụ thuộc runtime mới (D-070); cổng `scripts/dev-task.sh gate`
  (mypy --strict, coverage dòng + nhánh 100 %, lint). Gate dạng `-k <tên>` phải chạy ≥ 1 test (T-1501 làm máy chặn 0 test).
- Không làm: tách `xt.py` (AUD-ARCH-001), merge queue (cần `merge_group` ở CI — bước sau), hook `agent`/`prompt` làm cổng,
  tạo Routine/secret thay chủ repo (điểm dừng).
- Mỗi task một PR nhỏ; nhánh theo ràng buộc phiên (D-065); PR chạm `scripts/*`, `.claude/*`, `framework/11-*`, ADR đi
  làn chuẩn (reviewer khác model + `pr reviewed`), tài liệu đi làn nhanh.
- Rủi ro: (1) siết `same_command`/required check làm vòng cũ ở dự án đích báo `verify` — đỡ: migration giữ evidence cũ,
  chỉ bắt chạy lại; (2) hook mới chặn oan `TaskUpdate` ngoài autopilot — đỡ: hook chỉ chặn khi `state.json.active` và subject
  có `T-NNNN`, fail-open khi lỗi; (3) workflow reviewer chạy tốn token — đỡ: `--max-turns`, `--max-budget-usd`, chỉ PR làn chuẩn,
  không chạy trên draft/fork.
- Dự án đích chạy lại `install.py` sau 3.9.0 (hook/guard/xt.py đổi) và 3.10.0 (workflow steward/reviewer, manifest).

## Ngân sách (4 con số)
- Số vòng tối đa: 168 (`max(40, 8 × 21 task)`)
- Chi phí: 0 đồng ngoài phiên; workflow reviewer (T-1508) chỉ chạy thật khi chủ repo cấp `XT_REVIEWER_TOKEN`/app — tới lúc đó
  là `loop defer`
- Timeout mỗi lệnh Gate: 1800 giây (`XT_RECORD_TIMEOUT` mặc định)
- Ngày hết hạn: 24 giờ sau `loop init` (`--hours 24`)

## Điểm dừng bắt buộc (`loop defer`; `loop block` khi mọi việc còn lại phụ thuộc)
- Cấp secret/token hoặc tạo GitHub App reviewer (`XT_REVIEWER_TOKEN`), tạo Routine (chạy dưới danh tính chủ tài khoản) → người
- Đổi ruleset `main` (thêm required check `pr-review`/`autonomy-bench`) → người (`merge-check` = `human` thì báo)
- Force-push nhánh có lịch sử chưa merge, xoá nhánh, đổi quyền repo → không làm
- Bật AUTO-03/04/05 ở dự án đích (`hotel-manager`) ở chế độ ghi → người duyệt sau pilot chỉ-lập-quyết-định

## Task

### Đợt 1 — Kết luận đạt đáng tin (REC-01/02/06/07/08)
- [ ] `T-1501` `loop record`/`loop verify`: Gate in "Ran 0 tests"/"0 passed" → coi là đỏ (`zero_tests_red`), lý do ghi vào evidence (REC-01; files: scripts/xt.py, tests/test_xt_core.py) — Gate: `python3 -m unittest discover -s tests -k zero_tests_red`
- [ ] `T-1502` `same_command` giữ ngữ nghĩa shell (nháy đơn/kép khác nhau khi có `$`, backtick, `\`, `!`); evidence ghi `cmd_sha256`; `_verify_blueprint` không gộp lệnh khác nghĩa (REC-01; sau: T-1501; files: scripts/xt.py, tests/test_xt_core.py) — Gate: `python3 -m unittest discover -s tests -k command_identity`
- [ ] `T-1503` `loop init` ghi `scope` (blueprint, profile, scale, rev, gate_floor) vào state; blueprint mất/hỏng → `verify`, sàn Gate đọc từ scope; migration state cũ (REC-02; files: scripts/xt.py, tests/test_xt.py) — Gate: `python3 -m unittest discover -s tests -k scope_contract`
- [ ] `T-1504` `_ci_buckets` trả `not_run` cho check bắt buộc SKIPPED/NEUTRAL/CANCELLED/STALE hoặc sai app; `_merge_blockers` → `human`; `_pr_rest` lấy app của check (REC-08; sau: T-1409 đã merge; files: scripts/xt.py, tests/test_merge.py) — Gate: `python3 -m unittest discover -s tests -k required_check_executed`
- [ ] `T-1505` `carry_states` so phần quy phạm: đổi → `[ ]` + ghi chú `— Cũ (rev …)`, danh sách `stale`; `compose`/`blueprint-status` báo (REC-06; files: scripts/xt.py, tests/test_xt.py) — Gate: `python3 -m unittest discover -s tests -k requirement_revision`
- [ ] `T-1506` `audit rescan` đối chiếu `audit_applicability` với nhóm N/A → "N/A→áp dụng"; `audit check --strict` đỏ tới khi quét/giải trình mới (REC-07; files: scripts/xt.py, tests/test_xt_cli.py) — Gate: `python3 -m unittest discover -s tests -k na_reevaluated`

### Đợt 2 — Review và merge nhất quán (REC-03/04, AUTO-03)
- [ ] `T-1507` Hàm thuần `merge_eligibility(pr, rec, policy)` dùng chung cho `merge_decision`, `pr_next`, `merge-gate`, guard MCP/`gh`, steward; `merge-gate` đỏ khi auto-merge bật mà thiếu review hợp lệ ở head; ADR mới mở rộng ADR-0023 (REC-03; sau: T-1504, T-1411 đã merge; files: scripts/xt.py, .claude/hooks/guard.py, docs/adr/) — Gate: `python3 -m unittest discover -s tests -k single_merge_condition`
- [ ] `T-1508` Workflow `pr-review.yml` (claude-code-action pin SHA, OIDC/token reviewer, `/review` + `--json-schema`, model khác tác giả, trần turn/tiền) + bước `pr reviewed` bằng danh tính reviewer; `xt.yaml review_identity:`; `published_reviews` chỉ tin danh tính đó khi cấu hình; `ci-check` kiểm workflow; chạy thật → `loop defer` chờ token (AUTO-03, D-069; sau: T-1507; files: .github/workflows/pr-review.yml, scripts/xt.py, xt.yaml, tests/test_merge.py) — Gate: `python3 scripts/xt.py ci-check && python3 -m unittest discover -s tests -k review_identity`
- [ ] `T-1509` Guard `Decision(action, code, confidence, missing)` + bảng `apply_policy` theo mã; UNPARSED/BUDGET/unsure trong nhóm chặn → deny ở bash/mcp/edit; hook `permission-request.sh` (command) cho headless; corpus chặn oan không tăng (REC-04; sau: #159 đã merge; files: .claude/hooks/guard.py, .claude/hooks/permission-request.sh, .claude/settings.json, tests/test_hooks.py, tests/test_guard_corpus.py) — Gate: `python3 -m unittest discover -s tests -k typed_decision`

### Đợt 3 — Bằng chứng và điều phối (AUTO-01/02/04, REC-11)
- [ ] `T-1510` Parser PLAN đọc `(sau: …; files: …)`; `loop next --json` trả task sẵn sàng + cặp giao nhau file; `loop record` từ chối tick khi dependency mở; `loop status` báo chu trình (AUTO-01; sau: T-1503; files: scripts/xt.py, tests/test_xt_core.py, framework/templates/PLAN.md) — Gate: `python3 -m unittest discover -s tests -k task_dag`
- [ ] `T-1511` `xt.py context --task T-NNNN --json`: ID yêu cầu, đoạn spec, Gate, files, số byte (REC-11; sau: T-1510; files: scripts/xt.py, tests/test_xt_cli.py) — Gate: `python3 -m unittest discover -s tests -k context_pack`
- [ ] `T-1512` Evidence v2: `cmd_sha256`, `scope`, `req_rev`, `files_digest`; `loop verify` chạy lại Gate có digest đổi, `--all` chạy hết; evidence cũ thiếu trường → chạy lại (AUTO-02; sau: T-1502, T-1503, T-1505, T-1510; files: scripts/xt.py, tests/test_xt.py) — Gate: `python3 -m unittest discover -s tests -k evidence_v2`
- [ ] `T-1513` Hook `task-completed.sh` (exit 2 khi `TaskUpdate` xong mà `T-NNNN` trong subject chưa có evidence xanh, chỉ khi loop active) và `subagent-stop.sh` (block executor thiếu "lệnh + exit code"); `onFailure: block` cho PreToolUse deny; `install.py` chép hook (AUTO-02, D-068; sau: T-1512; files: .claude/hooks/task-completed.sh, .claude/hooks/subagent-stop.sh, .claude/settings.json, scripts/install.py, tests/test_hooks.py) — Gate: `python3 -m unittest discover -s tests -k task_completed_hook`
- [ ] `T-1514` `loop ci-triage --run <id> --json`: phân loại lỗi từ log job (hạ tầng/test/lint/type/coverage/secret/migration), `state.json.episode` (rerun_used ≤ 1, fix_attempts, cost_usd|null), cùng chữ ký 3 lần → defer, secret/SAST → block (AUTO-04; sau: T-1512; files: scripts/xt.py, tests/test_xt_cli.py, framework/11-autonomous-loop/self-healing-ci.md) — Gate: `python3 -m unittest discover -s tests -k ci_triage`

### Đợt 4 — Steward theo sự kiện, nâng cấp, đánh giá, yêu cầu (AUTO-05/06/07, REC-05/09/10/13)
- [ ] `T-1515` `install.py --plan` (JSON diff quyền/hook/file) + `.xtemplates/manifest.json` (hash file/rule khung); chỉ gỡ `ask` có trong manifest; rule trùng chuỗi không có nguồn gốc → giữ + báo (REC-09; files: scripts/install.py, tests/test_install.py) — Gate: `python3 -m unittest discover -s tests -k install_plan`
- [ ] `T-1516` `pr-steward.yml` thêm `check_suite: completed` + `workflow_run` (quality, merge-gate); hành động idempotent theo (repo, PR, head, hành động) đọc trạng thái trước khi làm; fixture event lặp/sai thứ tự/restart; mẫu Routine `pull_request.synchronize` cho `fix`/`update` ghi tài liệu (AUTO-05; sau: T-1507; files: .github/workflows/pr-steward.yml, scripts/xt.py, tests/test_merge.py, framework/11-autonomous-loop/stop-points-and-escalation.md) — Gate: `python3 scripts/xt.py ci-check && python3 -m unittest discover -s tests -k steward_events`
- [ ] `T-1517` `doctor --drift --json` so manifest với bản cài và tag mới nhất; báo file/quyền/tài liệu lệch; mẫu Routine tuần cho dự án đích (AUTO-06; sau: T-1515; files: scripts/xt.py, tests/test_doctor.py) — Gate: `python3 -m unittest discover -s tests -k doctor_drift`
- [ ] `T-1518` ADR selection semantics + `essential: true` không bị trần MUST ở M khi feature fact bật; thí điểm `08-backend/authn-authz.md` (BE-AUTH-003/006/008/015); fixture S/M/L có/không auth (REC-05; files: scripts/xt.py, framework/08-backend/authn-authz.md, docs/adr/, tests/test_xt.py) — Gate: `python3 scripts/xt.py validate && python3 -m unittest discover -s tests -k essential_not_capped`
- [ ] `T-1519` Tài liệu một nhà cho chính sách tự chủ (REC-10); `check-links.py --external` phân loại 5xx/timeout · 301/404 · 403/429 + retry, `links.yml` dùng nó (REC-13; files: framework/11-autonomous-loop/, README.md, scripts/check-links.py, .github/workflows/links.yml, tests/test_check_links.py) — Gate: `scripts/dev-task.sh lint && python3 -m unittest discover -s tests -k link_classification`
- [ ] `T-1520` `xt.py autonomy-bench --json`: corpus PR/rollup/review/guard (mọi tái hiện §2 và 🔴/🟠 đã sửa) → 0 false-green; `docs/ops/AUTONOMY-BASELINE.md`; chạy trong job `quality` (AUTO-07; sau: T-1507, T-1509; files: scripts/xt.py, tests/fixtures/autonomy/, docs/ops/AUTONOMY-BASELINE.md, .github/workflows/ci.yml) — Gate: `python3 scripts/xt.py autonomy-bench --json && python3 -m unittest discover -s tests -k autonomy_bench`

### Phát hành
- [ ] `T-1521` VERSION 3.9.0 sau đợt 1–2 và 3.10.0 sau đợt 3–4 + CHANGELOG `[X.Y.Z]` + PROGRESS; tag qua `release-tag.yml`; sổ audit cập nhật phát hiện đã sửa kèm PR — Gate: `scripts/dev-task.sh gate && python3 scripts/xt.py audit check docs/ops/AUDIT-STATUS.md`
