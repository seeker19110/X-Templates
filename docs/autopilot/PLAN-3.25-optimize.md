# PLAN-3.25-optimize.md — Khung X-Templates · `/optimize`, số field qua file, người ký một lần (ADR-0048) → bản 3.25.0

> Lập ngày 2026-10-25. Chủ repo đề xuất dòng chảy build → complete → optimize → ký → production → số thật → optimize → ký;
> chốt phương án B (D-180). Quyết định: ADR-0048. Phiên chính tự duyệt (ADR-0008).
>
> **Cú pháp bắt buộc cho máy:** mỗi task một dòng `- [ ] \`T-NNNN\` <việc> — Gate: \`<lệnh>\``.

## Tóm tắt (cổng duyệt — phiên chính tự duyệt, D-180)
- Phạm vi: (1) sổ: ADR-0048 + PLAN + D-180 · (2) skill mới `/optimize` (≤ 6 144 B, trần trong `CAPS`), `DOCTOR_SKILLS` đòi,
  AGENTS.md/CLAUDE.md/mẫu AGENTS §Skill · (3) `optimization-loop.md`: `LOOP-OPT-005` MUST@M, mục mới `LOOP-OPT-016` + §Số
  field (định dạng `docs/ops/FIELD-<ngày>.json`), `stop-points-and-escalation.md` hàng "Dữ liệu người dùng thật" thêm "không
  đọc production để tối ưu" · (4) mẫu GO-NO-GO: dòng người dùng thử luồng chính + chế độ delta; `lifecycle.md` §Ánh xạ vòng
  G7↔G8; `/complete` bước 3(f)/5 trỏ `/optimize`; README gốc §Quyết định thiết kế ADR-0048 · (5) CHANGELOG `[3.25.0]`,
  VERSION, PROGRESS.
- Không làm (ADR-0048 §Phương án): `xt.py field check`/đọc dashboard; cổng chờ người trong `/complete`; pha mới; sửa
  `/autopilot` (skill còn 1 B dưới trần — `/optimize` đi qua `/complete`); ID checklist mới ngoài `LOOP-OPT-016`.
- Rủi ro: trần byte (skill autopilot 6 143/6 144, README mảng 11 12 288/12 288 — **không chạm** hai file này; AGENTS.md và mẫu
  AGENTS sát trần — đo `wc -c` trước commit); `validate` đòi `updated` và prefix; C901/mypy/coverage khi đổi `DOCTOR_SKILLS`
  (test doctor/install). Đường lùi: ADR-0048 §Đường lùi, revert từng PR.
- Repo khung ở pha harden: mỗi lát một PR ≤ 150 dòng (không tính `.md`), `dev-task.sh gate` trước push, `pr next` đòi review →
  `reviewer-alt` (Fable, effort max — người viết là phiên chính); nhánh phiên một tên → lát tuần tự, sau mỗi merge gộp
  `origin/main`.
- Cách làm: SPEC = ADR-0048 là chữ cuối; phiên chính tự làm (hàng "Làm trực tiếp", `LOOP-ORCH-020`), `loop record` không
  `--executor`.

## Ngân sách (4 con số)
- Số vòng tối đa: `max(40, 8 × task)` (`--single-session`)
- Chi phí: 0 đồng ngoài phiên (không phụ thuộc mới)
- Timeout mỗi lệnh Gate: 1800 giây
- Ngày hết hạn: 8 giờ sau `loop init` (`--hours 8`)

## Điểm dừng bắt buộc (`loop defer`)
- Tag `v3.25.0` do `release-tag.yml` tạo sau merge lát cuối (cần `XT_RELEASE_TOKEN`); nâng khung ở dự án đích: chủ dự án.

## Thứ tự & lý do
1. Lát 1 — sổ (ADR, PLAN, D-180): quyết định có dấu vết trước khi đổi skill/chữ quy phạm.
2. Lát 2 — skill `/optimize` + `DOCTOR_SKILLS` + test + §Skill ba file: skill phải tồn tại trước khi `doctor` đòi.
3. Lát 3 — chữ quy phạm (`optimization-loop.md`, `stop-points-and-escalation.md`): nhà của luật, CHANGELOG mục checklist.
4. Lát 4 — mẫu GO-NO-GO, `lifecycle.md`, `/complete`, README gốc + cắt bản.

## Task

### Lát 1 — Sổ
- [x] `T-3301` ADR-0048, PLAN này, D-180 trong DECISIONS (files: docs/adr/0048-optimize-skill-and-field-loop.md, docs/autopilot/PLAN-3.25-optimize.md, docs/autopilot/DECISIONS.md) — Gate: `python3 scripts/check-links.py && grep -q "D-180" docs/autopilot/DECISIONS.md && test -f docs/adr/0048-optimize-skill-and-field-loop.md`

### Lát 2 — Skill
- [x] `T-3302` Skill mới `.claude/skills/optimize/SKILL.md` (đầu vào chỉ ngân sách đỏ: `release-check` hàng `perf`, `floor --run`, `--field docs/ops/FIELD-<ngày>.json` ≤ 30 ngày; PLAN-opt mỗi ngân sách một task, Gate `perf-gate` từ commit gốc; luật harden; dừng khi đạt; ≤ 6 144 B) + trần trong `CAPS`; AGENTS.md §8, CLAUDE.md, mẫu AGENTS §Skill thêm `/optimize` trong trần (files: .claude/skills/optimize/SKILL.md, tests/test_docs_budget.py, AGENTS.md, CLAUDE.md, framework/templates/AGENTS.md) — Gate: `python3 -m unittest tests.test_docs_budget && python3 scripts/check-links.py && test -f .claude/skills/optimize/SKILL.md && grep -q "skills/optimize/SKILL.md" tests/test_docs_budget.py && grep -q "perf compare" .claude/skills/optimize/SKILL.md && grep -q "/optimize" AGENTS.md && grep -q "/optimize" CLAUDE.md && grep -q "/optimize" framework/templates/AGENTS.md`
- [x] `T-3303` `DOCTOR_SKILLS` thêm `optimize`; `tests/test_install.py` kiểm skill được cài; `tests/test_doctor.py` kiểm thiếu `skills/optimize/SKILL.md` (sau: T-3302; files: scripts/xt.py, tests/test_install.py, tests/test_doctor.py) — Gate: `python3 -m unittest tests.test_doctor tests.test_install -k skill && grep -q '"optimize"' scripts/xt.py`

### Lát 3 — Chữ quy phạm
- [ ] `T-3304` `optimization-loop.md`: `LOOP-OPT-005` MUST@M (giữ ID), mục `LOOP-OPT-016` SHOULD (số field qua file có nguồn/ngày, agent không đọc production), §Số field (định dạng `docs/ops/FIELD-<ngày>.json`), §Vị trí trong vòng đời thêm `/optimize`; `stop-points-and-escalation.md` hàng "Dữ liệu người dùng thật" thêm "không cấp khoá đọc production để tối ưu — số qua file"; `updated` (sau: T-3302; files: framework/11-autonomous-loop/optimization-loop.md, framework/11-autonomous-loop/stop-points-and-escalation.md) — Gate: `python3 scripts/xt.py validate && python3 scripts/check-links.py && grep -q 'LOOP-OPT-016' framework/11-autonomous-loop/optimization-loop.md && grep -q 'LOOP-OPT-005. \*\*MUST@M\*\*' framework/11-autonomous-loop/optimization-loop.md && grep -q 'FIELD-' framework/11-autonomous-loop/stop-points-and-escalation.md`

### Lát 4 — Mẫu, vòng đời, cắt bản
- [ ] `T-3305` Mẫu GO-NO-GO: dòng "Người đã dùng thử luồng chính + đọc SPEC/threat model" (BLOCKER M/L, SHOULD S) và §Chế độ delta; `lifecycle.md` §Ánh xạ vòng G7 → ký → G8 → số field → `/optimize` → ký delta; `/complete` bước 3(f) và 5 trỏ `/optimize`; README gốc §Quyết định thiết kế dòng ADR-0048 (sau: T-3304; files: framework/templates/GO-NO-GO.md, framework/00-method/lifecycle.md, .claude/skills/complete/SKILL.md, README.md) — Gate: `python3 -m unittest tests.test_docs_budget && python3 scripts/xt.py validate && python3 scripts/check-links.py && grep -q "dùng thử luồng chính" framework/templates/GO-NO-GO.md && grep -q "/optimize" framework/00-method/lifecycle.md && grep -q "/optimize" .claude/skills/complete/SKILL.md && grep -q "ADR-0048" README.md`
- [ ] `T-3306` CHANGELOG `[3.25.0]` (mục checklist: `LOOP-OPT-005` đổi mức, `LOOP-OPT-016` mới; "Dự án đích: chạy lại `install.py`"), VERSION 3.25.0, PROGRESS.md ≤ 7 900 B, dòng Trạng thái ADR-0048 "Đã triển khai" (sau: T-3305; files: CHANGELOG.md, VERSION, PROGRESS.md, docs/adr/0048-optimize-skill-and-field-loop.md) — Gate: `scripts/dev-task.sh lint && test "$(cat VERSION)" = 3.25.0 && grep -q '^## \[3.25.0\]' CHANGELOG.md`
