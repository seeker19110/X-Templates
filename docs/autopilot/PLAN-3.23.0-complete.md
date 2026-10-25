# PLAN-3.23.0-complete.md — Khung X-Templates · `/autopilot` = pha build, `/complete` = pha harden (ADR-0046) → bản 3.23.0

> Lập ngày 2026-10-25. Chủ repo yêu cầu "/autopilot là pha build, code nhanh nhất có thể, loại bỏ tất cả rào cản, phiên chính
> tự quyết với mục tiêu chất lượng cao; thêm /complete mới audit, review, fix, refactor… hoàn thiện". Nghiên cứu:
> `research/2026-10-25-autopilot-build-complete-harden.md`; quyết định: ADR-0046. Phiên chính tự duyệt (D-174).
>
> **Cú pháp bắt buộc cho máy:** mỗi task một dòng `- [ ] \`T-NNNN\` <việc> — Gate: \`<lệnh>\``.

## Tóm tắt (cổng duyệt — phiên chính tự duyệt, D-174)
- Phạm vi: (1) `_verdict_blueprint` rẽ theo pha — build + MUST mở → `done` kèm `open_must`, lý do "trả ở `/complete`"; chuỗi lý
  do `_with_dispatch`/`_release_phase` trỏ `/complete`; `DOCTOR_SKILLS` thêm `complete` · (2) skill mới `/complete` (pha harden,
  ≤ 6 144 B, trần trong `CAPS`) · (3) skill `/autopilot` viết lại cho pha build: Pha 1 mức S, Kết thúc = build xong, một dòng
  "Sàn không bỏ", một dòng cho pha harden · (4) tài liệu: README mảng 11 (bước 12/16, Pha 3), `lifecycle.md` quy tắc 6 + ánh
  xạ, `audit.md` §1, mẫu PLAN/AGENTS, `orchestration-and-subagents.md` bảng review, `harness-files.md` bảng cổng, AGENTS.md
  §8, CLAUDE.md, README gốc (§Chạy tự động, §Công cụ, §Quyết định thiết kế bổ sung ADR-0037…0046), dòng Trạng thái
  ADR-0031/0033/0037/0041 · (5) CHANGELOG `[3.23.0]`, VERSION, PROGRESS.
- Không làm (ADR-0046 §Phương án/§Hệ quả): bỏ `--blueprint` ở build; lọc "MUST sàn"; verdict `done-build`; lệnh
  `xt.py complete`/`release-check --skip-run`; nới guard/điểm dừng/`verify --all`/cổng commit/`merge_hard_exceptions` mẫu;
  `/autopilot` tự đặt lại `build`; ID checklist mới; job CI theo tag chạy `release-check` (nợ).
- Rủi ro: trần byte (AGENTS.md dư 6 B, templates/AGENTS.md dư 4 B, skill autopilot dư 23 B, README mảng 11 dư 329 B) — Gate
  chạy `test_docs_budget`, đo `wc -c` trước commit; test ghim verdict cũ (`test_xt_core.py:729–766`) phải đổi có chủ đích; C901
  ≤ 10, `mypy --strict`, coverage 100 % (nhánh pha mới có test cả hai phía). Đường lùi: revert từng PR; đặt `harden`.
- Repo khung ở pha harden: mỗi lát một PR ≤ 150 dòng (không tính `.md`), `dev-task.sh gate` một lần trước push, PR làn chuẩn
  (`scripts/*`, `framework/templates/*`, `docs/autopilot/PLAN*.md`) chờ reviewer-alt rà sạch ở head; nhánh phiên bị ràng buộc
  một tên → lát đi tuần tự, sau mỗi merge gộp `origin/main`.
- Cách làm: SPEC = ADR-0046 + research §8 là chữ cuối → phiên chính tự làm, `loop record` không `--executor` (nhóm "Làm trực
  tiếp", điểm đo thứ ba của `LOOP-ORCH-020`); lát mã (T-3104/T-3105) cũng tự làm vì spec là một hàm + test ghim đã định.

## Ngân sách (4 con số)
- Số vòng tối đa: `max(40, 8 × task)` (`--single-session`)
- Chi phí: 0 đồng ngoài phiên (không phụ thuộc mới)
- Timeout mỗi lệnh Gate: 1800 giây (`XT_RECORD_TIMEOUT` mặc định)
- Ngày hết hạn: 8 giờ sau `loop init` (`--hours 8`)

## Điểm dừng bắt buộc (`loop defer`; `loop block` khi mọi việc còn lại phụ thuộc)
- Tag `v3.23.0` qua `release-tag.yml` sau merge lát cuối; nâng khung ở dự án đích (`install.py`): chủ dự án
- Ruleset đòi review của người (`merge-check` = `human`) → báo chủ repo, chuẩn bị lát kế ở nhánh cục bộ

## Thứ tự & lý do
1. Lát 1 — sổ: research + ADR-0046 + PLAN + D-174 (tài liệu; PLAN thuộc làn chuẩn) — lý do: quyết định có dấu vết trước khi đổi máy/skill.
2. Lát 2 — skill `/complete` mới + `/autopilot` pha build + AGENTS.md/CLAUDE.md + `CAPS` — lý do: skill phải tồn tại trước khi `DOCTOR_SKILLS` đòi nó.
3. Lát 3 — `xt.py` verdict theo pha + `DOCTOR_SKILLS` + test — lý do: rào cản máy duy nhất; làn chuẩn, cần review.
4. Lát 4 — tài liệu khung + README gốc + trạng thái ADR cũ + CHANGELOG/VERSION/PROGRESS — lý do: cắt bản sau khi mã và skill đã merge.

## Task

### Lát 1 — Sổ (research, ADR, PLAN)
- [x] `T-3101` Research note `research/2026-10-25-autopilot-build-complete-harden.md`, ADR-0046, PLAN này, D-174 trong DECISIONS (files: research/2026-10-25-autopilot-build-complete-harden.md, docs/adr/0046-autopilot-build-complete-harden.md, docs/autopilot/PLAN-3.23.0-complete.md, docs/autopilot/DECISIONS.md) — Gate: `python3 scripts/check-links.py && grep -q "D-174" docs/autopilot/DECISIONS.md && grep -q "ADR-0046" research/2026-10-25-autopilot-build-complete-harden.md && test -f docs/adr/0046-autopilot-build-complete-harden.md`

### Lát 2 — Skill
- [x] `T-3102` Skill mới `.claude/skills/complete/SKILL.md` (pha harden: PR đặt `harden` → `/audit` → nợ review theo PR/lát → PLAN-harden → vòng lặp luật harden → `release-check` GO → GO-NO-GO; ≤ 6 144 B) + trần trong `CAPS` của `tests/test_docs_budget.py` (files: .claude/skills/complete/SKILL.md, tests/test_docs_budget.py) — Gate: `python3 -m unittest tests.test_docs_budget && test -f .claude/skills/complete/SKILL.md && grep -q "skills/complete/SKILL.md" tests/test_docs_budget.py && grep -q "release-check" .claude/skills/complete/SKILL.md`
- [x] `T-3103` Skill `/autopilot` viết lại cho pha build (Pha 1 mức S, Kết thúc = build xong + "chưa phát hành — gõ /complete", một dòng "Sàn không bỏ", một dòng pha harden; giữ số bước Pha 2) + AGENTS.md §8 và CLAUDE.md thêm `/complete` trong trần (sau: T-3102; files: .claude/skills/autopilot/SKILL.md, AGENTS.md, CLAUDE.md) — Gate: `python3 -m unittest tests.test_docs_budget && python3 scripts/check-links.py && grep -q "/complete" AGENTS.md && grep -q "/complete" CLAUDE.md && grep -q "/complete" .claude/skills/autopilot/SKILL.md && ! grep -q "GO-NO-GO" .claude/skills/autopilot/SKILL.md`

### Lát 3 — Máy (`xt.py` + test)
- [x] `T-3104` `_verdict_blueprint` rẽ theo `_phase_in_tree`: build + MUST mở → `done` kèm `open_must` và lý do "trả ở /complete"; `bad_waivers`/`bad_lines` vẫn `continue`; chuỗi lý do `_with_dispatch` (`g7`) và `_release_phase` trỏ `/complete`; test ở `LoopVerdictBranchesTest` và lớp mới trong `test_delivery_phase.py` (hook-stop sau `verify --all` → `active=False`) (sau: T-3102; files: scripts/xt.py, tests/test_xt_core.py, tests/test_delivery_phase.py) — Gate: `scripts/dev-task.sh typecheck && python3 -m unittest tests.test_delivery_phase && python3 -m unittest tests.test_xt_core -k LoopVerdictBranchesTest -k LoopRecordBranchesTest`
- [x] `T-3105` `DOCTOR_SKILLS` thêm `complete`; `tests/test_install.py` kiểm skill được cài; `tests/test_doctor.py` kiểm thiếu `skills/complete/SKILL.md` (sau: T-3102; files: scripts/xt.py, tests/test_install.py, tests/test_doctor.py) — Gate: `python3 -m unittest tests.test_doctor tests.test_install -k skill && grep -q '"complete"' scripts/xt.py`

### Lát 4 — Tài liệu và cắt bản
- [ ] `T-3106` Tài liệu khung: README mảng 11 (bước 12/16, "Pha 3 — hoàn thiện"), `lifecycle.md` quy tắc 6 + ánh xạ tự động, `audit.md` §1, `00-method/README.md`, mẫu PLAN (header Mốc), mẫu AGENTS.md §7–8, `orchestration-and-subagents.md` bảng review, `harness-files.md` bảng cổng; cập nhật `updated` (sau: T-3103, T-3104; files: framework/11-autonomous-loop/README.md, framework/00-method/lifecycle.md, framework/00-method/audit.md, framework/00-method/README.md, framework/templates/PLAN.md, framework/templates/AGENTS.md, framework/11-autonomous-loop/orchestration-and-subagents.md, framework/11-autonomous-loop/harness-files.md) — Gate: `python3 -m unittest tests.test_docs_budget && python3 scripts/xt.py validate && python3 scripts/check-links.py && grep -q "/complete" framework/11-autonomous-loop/README.md && grep -q "/complete" framework/templates/AGENTS.md && grep -q "/complete" framework/00-method/lifecycle.md`
- [ ] `T-3107` README gốc (§Chạy tự động đến khi xong thêm bước `/complete`; §Công cụ; §Quyết định thiết kế bổ sung ADR-0037…0046) + dòng Trạng thái ADR-0031/0033/0037/0041 ghi "làm rõ bởi ADR-0046" (sau: T-3106; files: README.md, docs/adr/0031-delivery-phase-build-harden.md, docs/adr/0033-build-phase-lean-autopilot.md, docs/adr/0037-reviewers-only-in-harden.md, docs/adr/0041-build-phase-minimal-gates.md) — Gate: `python3 scripts/check-links.py && grep -q "ADR-0046" README.md && grep -q "ADR-0046" docs/adr/0031-delivery-phase-build-harden.md && grep -q "ADR-0046" docs/adr/0033-build-phase-lean-autopilot.md && grep -q "ADR-0046" docs/adr/0037-reviewers-only-in-harden.md && grep -q "ADR-0046" docs/adr/0041-build-phase-minimal-gates.md`
- [ ] `T-3108` CHANGELOG `[3.23.0]` ("Dự án đích: chạy lại `install.py`"), VERSION 3.23.0, PROGRESS.md ≤ 8 KB (sau: T-3107; files: CHANGELOG.md, VERSION, PROGRESS.md) — Gate: `scripts/dev-task.sh lint`
