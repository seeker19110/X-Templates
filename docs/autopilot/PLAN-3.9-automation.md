# PLAN-3.9-automation.md — Khung X-Templates · tăng tự động hóa, giữ bằng chứng (3.9.0 → 3.10.0)

> Lập ngày 2026-10-19 (Gate siết theo review khác model: tách `-k` theo ý, `sau:` tuần tự cho task cùng sửa `xt.py`) từ [`docs/ops/REMEDIATION-PLAN-2026-10-19.md`](../ops/REMEDIATION-PLAN-2026-10-19.md) (REC/AUTO, §7).
> Chạy **sau khi** PLAN 3.8.0 ([`PLAN.md`](PLAN.md), T-1401…T-1417) phát hành: `python3 scripts/xt.py loop init --plan
> docs/autopilot/PLAN-3.9-automation.md --single-session --max-iterations 176 --hours 24` (D-067). Duyệt kế hoạch: phiên
> chính tự duyệt theo tiêu chí chất lượng cuối (ADR-0008) và ghi D-NNN trước task đầu; reviewer khác model rà phần Gate
> (`LOOP-ORCH-018`) trước `loop decide`.
>
> **Cú pháp bắt buộc cho máy:** mỗi task một dòng `- [ ] \`T-NNNN\` <việc> — Gate: \`<lệnh>\``. Ghi chú `(sau: …; files: …)`
> là dependency **trong file này** và phạm vi ghi để phiên chính xếp thứ tự và tách song song (máy đọc từ T-1511 trở đi;
> trước đó phiên chính đọc tay). `cần: …` là điều kiện ngoài file (PR/task của PLAN 3.8.0 đã merge) — phiên chính kiểm bằng
> `git log origin/main`, không phải dependency máy.

## Tóm tắt (cổng duyệt)
- Phạm vi: §5–§6 của kế hoạch khắc phục — REC-01…04, 06…09 (P1/P2) và AUTO-01…07; REC-05 thí điểm một module; REC-12 ngoài phạm vi.
- Stack: Python ≥ 3.11 stdlib, bash, GitHub Actions; không phụ thuộc runtime mới (D-070); cổng `scripts/dev-task.sh gate`
  (mypy --strict, coverage dòng + nhánh 100 %, lint). Gate dạng `-k <tên>`: unittest trên Python 3.11 **exit 0 khi 0 test**
  (3.12+ exit 5) — tới khi T-1501 làm máy chặn, phiên chính đọc dòng `Ran N tests` trong evidence trước khi tick.
- Không làm: tách `xt.py` (AUD-ARCH-001), merge queue (cần `merge_group` ở CI — bước sau), hook `agent`/`prompt` làm cổng,
  tạo Routine/secret thay chủ repo (điểm dừng).
- Mỗi task một PR nhỏ; nhánh theo ràng buộc phiên (D-065); PR chạm `scripts/*`, `.claude/*`, `framework/11-*`, ADR đi
  làn chuẩn (reviewer khác model + `pr reviewed`), tài liệu đi làn nhanh. File PLAN này chứa lệnh Gate mà harness chạy
  nhưng hiện ở làn nhanh — T-1511 đưa `docs/autopilot/PLAN*.md` vào `merge_risk_paths`.
- Rủi ro: (1) siết `same_command`/required check làm vòng cũ ở dự án đích báo `verify` — đỡ: migration giữ evidence cũ,
  chỉ bắt chạy lại; (2) hook mới chặn oan `TaskUpdate` ngoài autopilot — đỡ: hook chỉ chặn khi `state.json.active` và subject
  có `T-NNNN`, fail-open khi lỗi; (3) workflow reviewer chạy tốn token — đỡ: `--max-turns`, `--max-budget-usd`, chỉ PR làn chuẩn,
  không chạy trên draft/fork.
- Dự án đích chạy lại `install.py` sau 3.9.0 (hook/guard/xt.py đổi) và 3.10.0 (workflow steward/reviewer, manifest).

## Ngân sách (4 con số)
- Số vòng tối đa: 176 (`max(40, 8 × 22 task)`)
- Chi phí: 0 đồng ngoài phiên; workflow reviewer (T-1508) chỉ chạy thật khi chủ repo cấp `XT_REVIEWER_TOKEN`/app — tới lúc đó
  là `loop defer`; trần mỗi lần chạy headless của nó: `--max-turns 40 --max-budget-usd 2`
- Timeout mỗi lệnh Gate: 1800 giây (`XT_RECORD_TIMEOUT` mặc định)
- Ngày hết hạn: 24 giờ sau `loop init` (`--hours 24`)

## Điểm dừng bắt buộc (`loop defer`; `loop block` khi mọi việc còn lại phụ thuộc)
- Cấp secret/token hoặc tạo GitHub App reviewer (`XT_REVIEWER_TOKEN`), tạo Routine (chạy dưới danh tính chủ tài khoản) → người
- Đổi ruleset `main` (thêm required check `pr-review`/`autonomy-bench`) → người (`merge-check` = `human` thì báo)
- Force-push nhánh có lịch sử chưa merge, xoá nhánh, đổi quyền repo → không làm
- Bật AUTO-03/04/05 ở dự án đích (`hotel-manager`) ở chế độ ghi → người duyệt sau pilot chỉ-lập-quyết-định

## Task

### Đợt 1 — Kết luận đạt đáng tin (REC-01/02/06/07/08)
- [x] `T-1501` `loop record`/`loop verify`: Gate exit 0 mà đầu ra khớp `^Ran 0 tests` (unittest, Python 3.11) → coi là đỏ (`zero_tests_red`), lý do ghi vào evidence; exit 5 (3.12+) giữ nguyên là đỏ; không bắt chuỗi `0 passed` (pytest tự exit 5) (REC-01; files: scripts/xt.py, tests/test_xt_core.py) — Gate: `python3 -m unittest discover -s tests -k zero_tests_red`
- [x] `T-1502` `same_command` giữ ngữ nghĩa shell (nháy đơn/kép khác nhau khi có `$`, backtick, `\`, `!`); evidence ghi `cmd_sha256`; `_verify_blueprint` không gộp lệnh khác nghĩa (REC-01; sau: T-1501; files: scripts/xt.py, tests/test_xt_core.py) — Gate: `python3 -m unittest discover -s tests -k command_identity`
- [x] `T-1503` `loop init` ghi `scope` (blueprint, profile, scale, rev, gate_floor) vào state; blueprint mất/hỏng → `verify`, sàn Gate đọc từ scope; migration state cũ (REC-02; sau: T-1502; files: scripts/xt.py, tests/test_xt.py) — Gate: `python3 -m unittest discover -s tests -k scope_contract && python3 -m unittest discover -s tests -k scope_blueprint_lost && python3 -m unittest discover -s tests -k scope_state_migration`
- [x] `T-1504` `_ci_buckets` trả `not_run` cho check bắt buộc SKIPPED/NEUTRAL/CANCELLED/STALE hoặc sai app; `_merge_blockers` → `human`; `_pr_rest` lấy app của check (REC-08; sau: T-1503; cần: T-1409 đã merge; files: scripts/xt.py, tests/test_merge.py) — Gate: `python3 -m unittest discover -s tests -k required_check_executed`
- [x] `T-1505` `carry_states` so phần quy phạm: đổi → `[ ]` + ghi chú `— Cũ (rev …)`, danh sách `stale`; `compose`/`blueprint-status` báo (REC-06; sau: T-1504; files: scripts/xt.py, tests/test_xt.py) — Gate: `python3 -m unittest discover -s tests -k requirement_revision`
- [x] `T-1506` `audit rescan` đối chiếu `audit_applicability` với nhóm N/A → "N/A→áp dụng"; `audit check --strict` đỏ tới khi quét/giải trình mới (REC-07; sau: T-1505; files: scripts/xt.py, tests/test_xt_cli.py) — Gate: `python3 -m unittest discover -s tests -k na_reevaluated`

### Đợt 2 — Review và merge nhất quán (REC-03/04, AUTO-03)
- [x] `T-1507` Hàm thuần `merge_eligibility(pr, rec, policy)` dùng chung cho `merge_decision`, `pr_next`, `merge-gate`, guard MCP/`gh`, steward; `merge-gate` đỏ khi auto-merge bật mà thiếu review hợp lệ ở head; ADR mới mở rộng ADR-0023 (REC-03; sau: T-1504; cần: T-1411 đã merge; files: scripts/xt.py, .claude/hooks/guard.py, docs/adr/) — Gate: `python3 scripts/xt.py validate && python3 -m unittest discover -s tests -k single_merge_condition && python3 -m unittest discover -s tests -k merge_gate_missing_review`
- [x] `T-1508` Workflow `pr-review.yml` (claude-code-action pin SHA, OIDC/token reviewer, `/review` + `--json-schema`, trần turn/tiền) + bước `pr reviewed` bằng danh tính reviewer; `xt.yaml` khai `review_identity:`, `author_model_family:`, `reviewer_model_family:` (PR không mang dữ liệu model tác giả — D-045 kiểm theo cấu hình, `ci-check` từ chối hai họ trùng); `published_reviews` chỉ tin danh tính đó khi cấu hình; chạy thật → `loop defer` chờ token (AUTO-03, D-069; sau: T-1507; files: .github/workflows/pr-review.yml, scripts/xt.py, xt.yaml, tests/test_merge.py) — Gate: `python3 scripts/xt.py ci-check && python3 -m unittest discover -s tests -k review_identity && python3 -m unittest discover -s tests -k same_family_rejected && python3 -m unittest discover -s tests -k published_reviews_identity`
- [x] `T-1509` Guard `Decision(action, code, confidence, missing)` + bảng `apply_policy` theo mã; UNPARSED/BUDGET/unsure trong nhóm chặn → deny ở bash/mcp/edit; hook `permission-request.sh` (command) cho headless; corpus chặn oan không tăng (REC-04; cần: #159 đã merge; files: .claude/hooks/guard.py, .claude/hooks/permission-request.sh, .claude/settings.json, tests/test_hooks.py, tests/test_guard_corpus.py) — Gate: `python3 -m unittest discover -s tests -k typed_decision && python3 -m unittest discover -s tests -k guard_corpus`

### Phát hành 3.9.0
- [x] `T-1510` VERSION 3.9.0 + CHANGELOG `[3.9.0]` + PROGRESS; tag qua `release-tag.yml`; sổ audit cập nhật phát hiện đã sửa kèm PR (sau: T-1501, T-1502, T-1503, T-1504, T-1505, T-1506, T-1507, T-1508, T-1509) — Gate: `scripts/dev-task.sh gate && python3 scripts/xt.py audit check docs/ops/AUDIT-STATUS.md && test "$(cat VERSION)" = 3.9.0`

### Đợt 3 — Bằng chứng và điều phối (AUTO-01/02/04, REC-11)
- [x] `T-1511` Parser PLAN đọc `(sau: …; files: …)`; `loop next --json` trả task sẵn sàng + cặp giao nhau file; `loop record` từ chối tick khi dependency mở; `loop status` báo chu trình; `docs/autopilot/PLAN*.md` vào `merge_risk_paths` (AUTO-01; sau: T-1503, T-1510; files: scripts/xt.py, xt.yaml, tests/test_xt_core.py, framework/templates/PLAN.md) — Gate: `python3 -m unittest discover -s tests -k task_dag`
- [x] `T-1512` `xt.py context --task T-NNNN --json`: ID yêu cầu, đoạn spec, Gate, files, số byte (REC-11; sau: T-1511; files: scripts/xt.py, tests/test_xt_cli.py) — Gate: `python3 -m unittest discover -s tests -k context_pack`
- [x] `T-1513` Evidence v2: `cmd_sha256`, `scope`, `req_rev`, `files_digest`; `loop verify` chạy lại Gate có digest đổi, `--all` chạy hết; evidence cũ thiếu trường → chạy lại (AUTO-02; sau: T-1502, T-1503, T-1505, T-1511; files: scripts/xt.py, tests/test_xt.py) — Gate: `python3 -m unittest discover -s tests -k evidence_v2`
- [x] `T-1514` Hook `task-completed.sh` (exit 2 khi `TaskUpdate` xong mà `T-NNNN` trong subject chưa có evidence xanh, chỉ khi loop active) và `subagent-stop.sh` (block executor thiếu "lệnh + exit code"); `onFailure: block` cho PreToolUse deny; `install.py` chép hook (AUTO-02, D-068; sau: T-1513; files: .claude/hooks/task-completed.sh, .claude/hooks/subagent-stop.sh, .claude/settings.json, scripts/install.py, tests/test_hooks.py) — Gate: `python3 -m unittest discover -s tests -k task_completed_hook && python3 -m unittest discover -s tests -k subagent_stop_hook && python3 -m unittest discover -s tests -k install_copies_hooks`
- [x] `T-1515` `loop ci-triage --run <id> --json`: phân loại lỗi từ log job (hạ tầng/test/lint/type/coverage/secret/migration), `state.json.episode` (rerun_used ≤ 1, fix_attempts, cost_usd|null), cùng chữ ký 3 lần → defer, secret/SAST → block (AUTO-04; sau: T-1513; files: scripts/xt.py, tests/test_xt_cli.py, framework/11-autonomous-loop/self-healing-ci.md) — Gate: `python3 -m unittest discover -s tests -k ci_triage`

### Đợt 4 — Steward theo sự kiện, nâng cấp, đánh giá, yêu cầu (AUTO-05/06/07, REC-05/09/10/13)
- [x] `T-1516` `install.py --plan` (JSON diff quyền/hook/file) + `.xtemplates/manifest.json` (hash file/rule khung); chỉ gỡ `ask` có trong manifest; rule trùng chuỗi không có nguồn gốc → giữ + báo (REC-09; sau: T-1510; files: scripts/install.py, tests/test_install.py) — Gate: `python3 -m unittest discover -s tests -k install_plan`
- [ ] `T-1517` `pr-steward.yml` thêm `check_suite: completed` + `workflow_run` (quality, merge-gate); hành động idempotent theo (repo, PR, head, hành động) đọc trạng thái trước khi làm; fixture event lặp/sai thứ tự/restart; mẫu Routine `pull_request.synchronize` cho `fix`/`update` ghi tài liệu (AUTO-05; sau: T-1507, T-1510; files: .github/workflows/pr-steward.yml, scripts/xt.py, tests/test_merge.py, framework/11-autonomous-loop/stop-points-and-escalation.md) — Gate: `python3 scripts/xt.py ci-check && python3 -m unittest discover -s tests -k steward_events`
- [ ] `T-1518` `doctor --drift --json` so manifest với bản cài và tag mới nhất; báo file/quyền/tài liệu lệch; mẫu Routine tuần cho dự án đích (AUTO-06; sau: T-1516; files: scripts/xt.py, tests/test_doctor.py) — Gate: `python3 -m unittest discover -s tests -k doctor_drift`
- [ ] `T-1519` ADR selection semantics + `essential: true` không bị trần MUST ở M khi feature fact bật; thí điểm `08-backend/authn-authz.md` (BE-AUTH-003/006/008/015); fixture S/M/L có/không auth (REC-05; sau: T-1518; files: scripts/xt.py, framework/08-backend/authn-authz.md, docs/adr/, tests/test_xt.py) — Gate: `python3 scripts/xt.py validate && python3 -m unittest discover -s tests -k essential_not_capped`
- [ ] `T-1520` Tài liệu một nhà cho chính sách tự chủ (REC-10); `check-links.py --external` phân loại 5xx/timeout · 301/404 · 403/429 + retry, `links.yml` dùng nó (REC-13; sau: T-1510; files: framework/11-autonomous-loop/, README.md, scripts/check-links.py, .github/workflows/links.yml, tests/test_check_links.py) — Gate: `scripts/dev-task.sh lint && python3 scripts/xt.py ci-check && python3 -m unittest discover -s tests -k link_classification && python3 -m unittest discover -s tests -k autonomy_policy_single_home`
- [ ] `T-1521` `xt.py autonomy-bench --json`: corpus PR/rollup/review/guard (mọi tái hiện §2, 🔴/🟠 đã sửa, ca đối kháng do reviewer khác model thêm) — **exit 1 khi false-green > 0**; `docs/ops/AUTONOMY-BASELINE.md`; chạy trong job `quality` (AUTO-07; sau: T-1507, T-1509; files: scripts/xt.py, tests/fixtures/autonomy/, docs/ops/AUTONOMY-BASELINE.md, .github/workflows/ci.yml) — Gate: `python3 scripts/xt.py autonomy-bench --json && python3 -m unittest discover -s tests -k autonomy_bench`

### Phát hành 3.10.0
- [ ] `T-1522` VERSION 3.10.0 + CHANGELOG `[3.10.0]` + PROGRESS; tag qua `release-tag.yml`; sổ audit cập nhật; dự án đích: hướng dẫn chạy lại `install.py` (sau: T-1511, T-1512, T-1513, T-1514, T-1515, T-1516, T-1517, T-1518, T-1519, T-1520, T-1521) — Gate: `scripts/dev-task.sh gate && python3 scripts/xt.py audit check docs/ops/AUDIT-STATUS.md && test "$(cat VERSION)" = 3.10.0`
