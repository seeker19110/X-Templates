# PLAN-upgrade-2026-11-01.md — Khung X-Templates · nâng cấp: Adaptive Agent (ADR-0061), stored e3fdcb0..e8b3831, sửa batch audit delta 2026-11-01

> Lập ngày 2026-11-01 theo `/complete` (pha harden) sau audit delta 2026-11-01 (báo cáo `docs/ops/AUDIT-REPORT-2026-11-01-delta.md`
> viết ở T-3608) và hai research note [`2026-11-01-adaptive-agent-topology.md`](../../research/2026-11-01-adaptive-agent-topology.md),
> [`2026-11-01-stored-delta-upgrade.md`](../../research/2026-11-01-stored-delta-upgrade.md).
> Duyệt: D-292 (phiên chính tự duyệt, `xt.py loop decide`).
>
> **Cú pháp bắt buộc cho máy:** mỗi task một dòng `- [ ] \`T-NNNN\` <việc> — Gate: \`<lệnh>\``. `topo:` theo ADR-0061 (thiếu = `self`).

## Tóm tắt (cổng duyệt)
- Hiện trạng: `main` `e09f776` (#377). Audit delta `78fb359..e09f776` (2026-11-01, 3 cụm reviewer read-only + xác minh đối kháng): 0 🔴 ngoài guard;
  SEC 3 🔴 (AUD-SEC-249/250/251) + 3 🟠 (248/252/253) chờ xác minh; HAR 1 🟠 (AUD-HAR-171 PROGRESS lỗi thời); 🟢 DOC/TEST/CODE/XFEAT/ARCH 14 mục.
- Phạm vi, theo thứ tự lợi ích/công sức: lát 1 tài liệu ADR-0061 · lát 2 harness topology · lát 3 KPI thời gian + trần `rethink` · lát 4 stored ưu tiên 1
  (XT-H-019/020/021) · lát 5 stored ưu tiên 2–3 (XT-H-024/026, XT-H-022) · lát 6 sửa batch audit (sổ + báo cáo + 🟠 HAR + 🟢 rẻ; 🔴 SEC sau xác minh)
  · lát 7 nợ lát E của PLAN-harden-2026-10-31 (AUD-DOC-123/124).
- Không làm trong PLAN này: stored §3 mục 4–8 (XT-H-023/025/027/029/032 và các dòng hẹp) — PLAN kế; `perf trial` (D-258); 🔴 guard có từ trước
  ngoài batch (AUD-SEC-202/232…247 — giữ `mở`, chủ: `/complete` kế, bài học #372: không vá từng ngữ cảnh).
- Cách làm (ADR-0061): mặc định `topo: self` — phiên chính tự viết, mỗi lát một PR ≤ ~150 dòng mã, test đỏ trước khi sửa; lát chạm `scripts/xt.py`/
  `install.py`/hook ghi `topo: review` (reviewer-alt rà trước PR); không `parallel` (các lát nối tiếp cùng chạm sổ/CHANGELOG).
- Rủi ro: đổi mặc định giao việc làm `loop stats` nhóm giao rỗng ở dự án không `parallel` (chấp nhận — đó là số đo thật); trần `rethink` 1 chặn PR
  nửa chừng → đã có `split-or-close`. Đường lùi: revert PR từng lát; `(topo: parallel)` trả hành vi cũ.

## Ngân sách (4 con số)
- Số vòng tối đa: bỏ trống (`--single-session`) · Chi phí: 0 đồng ngoài phiên · Timeout Gate: 900 giây · Hạn: 48 giờ sau `loop init`

## Điểm dừng bắt buộc (`loop defer`)
- Ký GO-NO-GO 3.30.0 (dòng 20) — người. Số `max_rethink`/đợt 4 là khởi điểm do chủ dự án đặt — chỉnh khi có số (`LOOP-ORCH-020` + KPI).

## Task
### Lát 1 — Tài liệu ADR-0061 (Adaptive Agent)
- [x] `T-3600` ADR-0061 + research note + `LOOP-ORCH-024`, bảng topology, chữ `LOOP-ORCH-010`/`LOOP-DESIGN-024`, mẫu PLAN `topo:`, skill `/autopilot` bước 5, README chỉ mục ADR (0054/0055/0060/0061 — AUD-DOC-130), CHANGELOG (files: docs/adr/, docs/autopilot/, research/, framework/11-autonomous-loop/, framework/templates/, .claude/skills/, README.md, CHANGELOG.md) — Gate: `python3 scripts/xt.py validate && python3 scripts/xt.py changelog-check && python3 -m unittest -q tests.test_docs_budget tests.test_skill_routing && python3 scripts/check-links.py`
### Lát 2 — Harness: topology
- [x] `T-3601` `loop status --json` trả `topology` (`self|review|parallel|audit` từ `(topo: …)`, thiếu = `self`), `executor: null` trừ `parallel` (tầng theo `exec:`; chuyển cấp sau 2 lần đỏ giữ ADR-0029); `plan waves --max` mặc định 4; test đỏ trước (sau: T-3600; topo: review; files: scripts/xt.py, tests/test_xt.py, tests/test_next_step.py) — Gate: `python3 -m unittest -q tests.test_xt tests.test_next_step tests.test_xt_cli && python3 -m mypy --strict scripts/xt.py && python3 -m ruff check --select C901 scripts`
### Lát 3 — Harness: KPI thời gian + trần rethink
- [x] `T-3602` `loop stats` thêm `time_to_green_hours` (trung vị/P95 theo task từ `started` lần đầu → `finished` lần xanh đầu; in ở bảng và `--json`) (sau: T-3601; topo: review; files: scripts/xt.py, tests/test_xt.py) — Gate: `python3 -m unittest -q tests.test_xt.LoopTest && python3 -m mypy --strict scripts/xt.py`
- [ ] `T-3603` `pr rethink` trần `max_rethink` (xt.yaml, mặc định 1; 0 = không trần; **không áp** cho PR cắt bản — ADR-0059 §6) — hết → `pr next` trả `split-or-close` kèm `do`; mẫu xt.yaml + CHANGELOG + ca `autonomy-bench` (sau: T-3602; topo: review; files: scripts/xt.py, tests/test_merge.py, framework/templates/xt.yaml, tests/fixtures/autonomy/pr.json) — Gate: `python3 -m unittest -q tests.test_merge tests.test_autonomy_bench && python3 scripts/xt.py autonomy-bench`
### Lát 4 — Stored ưu tiên 1: cấu hình mặc định an toàn
- [ ] `T-3604` XT-H-019/020: bổ sung `BASE-SEC-005` (`.env.example` không chứa bí mật dùng được; khởi động từ chối giá trị trùng mẫu) và `BASE-SEC-010` (publish Docker `127.0.0.1:P:P`, bind trong tài liệu khớp mã) ở `01-baseline/security-minimum.md` — giữ ID, thêm Kiểm; CHANGELOG (sau: T-3603; files: framework/01-baseline/security-minimum.md, CHANGELOG.md) — Gate: `python3 scripts/xt.py validate && python3 -m unittest -q tests.test_docs_budget`
- [ ] `T-3605` XT-H-021: `install.py` thêm `.claude/settings.local.json` vào `.gitignore` đích; `doctor` cảnh báo `enableAllProjectMcpServers: true` và `model` ngoài allowlist; SHOULD mới ở `harness-files.md`; test đỏ trước (sau: T-3604; topo: review; files: scripts/install.py, scripts/xt.py, tests/test_install.py, tests/test_doctor.py, framework/11-autonomous-loop/harness-files.md) — Gate: `python3 -m unittest -q tests.test_install tests.test_doctor && python3 -m mypy --strict scripts/xt.py scripts/install.py`
### Lát 5 — Stored ưu tiên 2–3: quét tài sản prompt, trust_remote_code
- [ ] `T-3606` XT-H-024/026: `prompt-assets-scan` thêm luật (lời bảo agent bỏ xác nhận/không từ chối; gói chạy không ghim; system prompt rò rỉ), quét cả README/`docs/`; fixture xấu đỏ, tốt xanh; bổ sung `SEC-AI-018` (sau: T-3605; topo: review; files: scripts/, tests/, framework/12-security/ai-security.md) — Gate: `python3 -m unittest -q tests.test_xt_cli.PromptAssetsScanTest && python3 scripts/xt.py validate`
- [ ] `T-3607` XT-H-022: MUST@L mới ở `12-security/supply-chain.md` — `trust_remote_code=True` phải ghim `revision=<sha40>` + owner allowlist + `HF_HUB_OFFLINE=1` sau tải đầu; Kiểm bằng `rg`; CHANGELOG (sau: T-3606; files: framework/12-security/supply-chain.md, CHANGELOG.md) — Gate: `python3 scripts/xt.py validate && python3 -m unittest -q tests.test_docs_budget`
### Lát 6 — Audit delta 2026-11-01: ghi sổ và sửa batch
- [ ] `T-3608` Ghi sổ + báo cáo `AUDIT-REPORT-2026-11-01-delta.md` (9 nhóm `đã quét` ở SHA quét; phát hiện mới AUD-SEC-248…254, AUD-HAR-171…173, AUD-DOC-130…135, AUD-TEST-037…039, AUD-CODE-032, AUD-XFEAT-038, AUD-ARCH-007; kết quả xác minh đối kháng; lưu ý scratchpad dùng chung) (sau: T-3607; files: docs/ops/AUDIT-STATUS.md, docs/ops/AUDIT-REPORT-2026-11-01-delta.md) — Gate: `python3 scripts/xt.py audit check docs/ops/AUDIT-STATUS.md`
- [ ] `T-3609` Sửa AUD-HAR-171 🟠: `PROGRESS.md` theo thực tế (#363…#377 merge, #372 đóng, ADR tới 0061, bàn giao SHA `main`) + 🟢 rẻ: AUD-DOC-131 (giới hạn `)#` trỏ AUD-SEC-242/235/247), AUD-DOC-132 (AUD-SEC-177/178/179/182/183 → đã sửa #361), AUD-DOC-133 (D-NNN cho ADR-0060), AUD-DOC-135 (nguồn số 100, BASE-DEP-019/020), nguồn `stored 23 §4.5` của LOOP-ORCH-008/010/014 → 23 §2 / 03 §5 (ID sổ ghi ở T-3608) (sau: T-3608; files: PROGRESS.md, docs/ops/AUDIT-STATUS.md, framework/11-autonomous-loop/harness-files.md, docs/adr/0060-task-skills.md, framework/01-baseline/) — Gate: `python3 scripts/xt.py progress-check && python3 scripts/xt.py audit check docs/ops/AUDIT-STATUS.md && python3 scripts/xt.py validate`
- [ ] `T-3610` 🟢 TEST/CODE/XFEAT: AUD-TEST-037 (biên 100/101 cho `merge_decision`), AUD-TEST-038 (`RmPwdParentTest` không phụ thuộc cây dưới TMPDIR), AUD-TEST-039 (bỏ ca corpus trùng), AUD-CODE-032 (xoá `_heredoc_spans` chết), AUD-XFEAT-038 (`pr title-check` miễn `Revert "…"`) (sau: T-3609; topo: review; files: scripts/xt.py, .claude/hooks/guard.py, tests/) — Gate: `python3 -m unittest -q tests.test_merge tests.test_xt_cli tests.test_guard_audit1020b tests.test_guard_audit1019 && python3 scripts/xt.py autonomy-bench`
- [ ] `T-3611` 🔴 SEC đã xác minh (danh sách chốt sau xác minh đối kháng; mỗi lớp một test đỏ trước, luật OR với luật cũ, ca `autonomy-bench`; không vá từng ngữ cảnh — ưu tiên lớp có mẫu lệnh rõ: AUD-SEC-251 công cụ tự chạy lệnh `sed e`/`awk system`/`perl`/`tar --to-command`/`m4`, AUD-SEC-250 `PS4`/`BASH_ENV`/`mapfile -C`/`complete -C`) (sau: T-3610; topo: review; files: .claude/hooks/guard.py, tests/test_guard_audit1019.py, tests/fixtures/autonomy/guard.json) — Gate: `python3 -m unittest -q tests.test_guard_audit1019 tests.test_hooks && python3 scripts/xt.py autonomy-bench`
### Lát 7 — Nợ lát E (PLAN-harden-2026-10-31)
- [ ] `T-3612` AUD-DOC-123/125 (`LOOP-CI-020` canary) và AUD-DOC-124/126/127/129 (`AI-PROTO-019` từ cấm) — thay T-3579/T-3580 (sau: T-3611; files: framework/11-autonomous-loop/, framework/13-ai-engineering/, docs/ops/AUDIT-STATUS.md) — Gate: `python3 scripts/xt.py validate && python3 scripts/xt.py audit check docs/ops/AUDIT-STATUS.md && python3 -m unittest -q tests.test_docs_budget`
