# PLAN-harden-2026-10-27-loops.md — Khung X-Templates · nâng tự chủ ba vòng, lát 0–3

> Lập ngày 2026-10-27 theo `/complete` (pha harden) và yêu cầu chủ repo "hoàn thành hết đi" (sáu lát của
> [nghiên cứu 2026-10-26](../../research/2026-10-26-autopilot-complete-optimize.md) §11). Thiết kế: ADR-0051, ADR-0052 (lát 3: ADR riêng, D-203). Phiên chính tự duyệt (D-202, D-203).
>
> **Cú pháp bắt buộc cho máy:** mỗi task một dòng `- [ ] \`T-NNNN\` <việc> — Gate: \`<lệnh>\``.

## Tóm tắt (cổng duyệt — phiên chính tự duyệt, D-202)
- Hiện trạng: `main` 3.27.0, audit delta `e8c8d96..137a047` 0 🔴/🟠 (#289); `release-check` chỉ còn chữ ký người.
- Phạm vi: lát 0 corpus luồng FLOW (§10) · lát 1 `rev` state, không-tiến-triển theo task, `loop attach/resolve/unblock`, mẫu perf v2 →
  3.28.0 · lát 2 `loop next-step` chỉ đọc, gom việc harden, gói nghiệm thu nháp · lát 3 ADR riêng + `perf trial` (D-203) → 3.29.0.
- Không làm (defer, cần người/dữ liệu): lát 4 pilot phiên thực ≥ 2 dự án đích; lát 5 field trigger, bot nâng bản, worker ngoài phiên,
  event policy `pull_request_target` (T-3554, T-3555).
- `release-check` không nằm trong Gate task, kể cả trong ống lệnh (`run_gate_shell` chạy `bash -o pipefail`; hàng `verify` đòi chính
  task đã xanh — tự tham chiếu, review #290): Gate audit gọi thẳng `xt.review_debt`; `release-check` chạy ở G7 sau `loop verify --all`.
- Cách làm: mỗi task một PR (≤ ~150 dòng mã, test đỏ trước khi sửa; vượt → tách task ID mới khi làm, ghi PLAN), `executor-deep` viết, `reviewer-alt` rà ở head, merge ghim head;
  phiên bị ràng một nhánh nên tuần tự, gộp `origin/main` sau mỗi merge.
- Rủi ro: chữ README mảng 11/skill hết byte → câu mới đổi câu cũ; trần theo task chặn oan (`--max-task-runs 0`). Đường lùi: ADR-0052 §Đường lùi.

## Ngân sách (4 con số)
- Số vòng tối đa: 200 (`loop init --single-session --max-iterations 200`; mặc định tự tính chỉ `max(40, 8 × task)`) · Chi phí: 0 đồng ngoài phiên (tương tác: `null`) · Timeout Gate: 900 giây · Hạn: 36 giờ sau `loop init`

## Điểm dừng bắt buộc (`loop defer`)
- T-3554, T-3555 (lát 4–5): dữ liệu phiên thực ở dự án đích, SLO field, quyền/chi phí ngoài phiên — chỉ chủ dự án có.
- Ký GO-NO-GO 3.28.0/3.29.0 (dòng 20) — người.

## Task
### Lát 0 — corpus luồng
- [x] `T-3536` `tests/test_flow.py` + registry `XFAIL`/`XT_FLOW_STRICT` (ADR-0052 §1): FLOW-01…06 trong repo git tạm với `xt.py` thật; FLOW-03/05 xanh, còn lại xfail (files: tests/test_flow.py, tests/shard-weights.json) — Gate: `python3 -m unittest -q tests.test_flow && XT_FLOW_STRICT=FLOW-05,FLOW-03 python3 -m unittest -q tests.test_flow && scripts/dev-task.sh lint`
- [x] `T-3537` `_live_loop` xét trần vòng/hạn trước verdict (ADR-0051 §Quyết định, D-177) (sau: T-3536; files: scripts/xt.py, tests/test_xt_loop.py) — Gate: `python3 -m unittest -q -k test_live_loop_budget tests.test_xt_loop && python3 -m unittest -q tests.test_flow`
- [x] `T-3558` FLOW-07 (hai tiến trình ×100, xen kẽ tất định bằng barrier — không phụ thuộc may rủi race), FLOW-08 (crash giữa `loop record`), FLOW-18/19 (perf theo vai) vào `tests/test_flow.py` — FLOW-07/18/19 xfail, FLOW-08 đối chứng xanh (sau: T-3537; files: tests/test_flow.py, tests/shard-weights.json) — Gate: `python3 -m unittest -q tests.test_flow && XT_FLOW_STRICT=FLOW-08 python3 -m unittest -q tests.test_flow`
### Lát 1 — nền chung (3.28.0)
- [ ] `T-3538` `rev` + `update_state` + khoá `state.lock`; `loop record` và Stop hook qua `update_state`; FLOW-07 xanh (sau: T-3558; files: scripts/xt.py, tests/test_xt_loop.py, tests/test_flow.py) — Gate: `XT_FLOW_STRICT=FLOW-07 python3 -m unittest -q tests.test_xt_loop tests.test_flow tests.test_hooks`
- [ ] `T-3559` Các lệnh ghi state còn lại (checkpoint, init, block, defer, resume, stop, ci-triage) qua `update_state`/kiểm `rev` (sau: T-3538; files: scripts/xt.py, tests/test_xt_loop.py) — Gate: `python3 -m unittest -q tests.test_xt_loop tests.test_xt_cli tests.test_hooks && test "$(git grep -c 'write_state(' -- scripts/xt.py | cut -d: -f2)" -le 2`
- [ ] `T-3539` `task_runs` + `max_task_runs` + `loop init --max-task-runs`; FLOW-04/06 xanh (sau: T-3559; files: scripts/xt.py, tests/test_xt_loop.py, tests/test_flow.py) — Gate: `XT_FLOW_STRICT=FLOW-04,FLOW-06 python3 -m unittest -q tests.test_xt_loop tests.test_flow`
- [ ] `T-3540` `loop attach` + lối ra theo nguồn (ADR-0052 §6); FLOW-01 xanh (sau: T-3539; files: scripts/xt.py, tests/test_xt_cli.py, tests/test_flow.py) — Gate: `XT_FLOW_STRICT=FLOW-01 python3 -m unittest -q tests.test_xt_cli tests.test_flow && test "$(git grep -c 'write_state(' -- scripts/xt.py | cut -d: -f2)" -le 2`
- [ ] `T-3541` `loop resolve`; FLOW-02/03 xanh (sau: T-3540; files: scripts/xt.py, tests/test_xt_cli.py, tests/test_flow.py) — Gate: `XT_FLOW_STRICT=FLOW-02,FLOW-03 python3 -m unittest -q tests.test_xt_cli tests.test_flow && test "$(git grep -c 'write_state(' -- scripts/xt.py | cut -d: -f2)" -le 2`
- [ ] `T-3542` `loop unblock` + `_carry_previous` mang `attached/resolved/unblocked` (sau: T-3541; files: scripts/xt.py, tests/test_xt_cli.py, tests/test_xt_loop.py) — Gate: `python3 -m unittest -q -k test_unblock_ tests.test_xt_cli && python3 -m unittest -q -k test_carry_interventions tests.test_xt_loop && python3 -m unittest -q tests.test_flow && test "$(git grep -c 'write_state(' -- scripts/xt.py | cut -d: -f2)" -le 2`
- [ ] `T-3543` `loop resume` cảnh báo + chữ đổi (SESSION_MISMATCH_NOTE, doctor, README mảng 11, skill `/autopilot`, `loop-design.md`, `stop-points-and-escalation.md`, `harness-files.md`, README bảng lệnh, BLUEPRINT LOOP-HARNESS-024/LOOP-STOP-021) + CHANGELOG "Dự án đích" (sau: T-3542) — Gate: `python3 -m unittest -q tests.test_hooks tests.test_xt_cli tests.test_docs_budget && python3 scripts/xt.py validate && python3 scripts/check-links.py && ! git grep -nE 'loop resume.{0,2} gắn lại' -- framework .claude README.md`
- [ ] `T-3544` `perf sample` ghi mẫu v2 (test: ngoài repo → nhãn; thiếu git / dubious ownership / HEAD chưa commit → exit 2 có thông báo — review #290 lượt 7–8) (sau: T-3543; files: scripts/xt.py, tests/test_perf.py) — Gate: `python3 -m unittest -q -k test_sample_v2 tests.test_perf`
- [ ] `T-3545` `perf compare` từ chối lệch trường trọng yếu/baseline bẩn/`--base` lệch, v1 → `unverified-manual`; FLOW-18/19 xanh (sau: T-3544; files: scripts/xt.py, tests/test_perf.py, tests/test_flow.py) — Gate: `XT_FLOW_STRICT=FLOW-18,FLOW-19 python3 -m unittest -q tests.test_perf tests.test_flow`
- [ ] `T-3556` Audit delta lát 1 (`/audit delta`, sổ + báo cáo; 🔴/🟠 sửa trước khi cắt bản) (sau: T-3545; files: docs/ops/AUDIT-STATUS.md) — Gate: `python3 scripts/xt.py audit check docs/ops/AUDIT-STATUS.md --strict && python3 -c "import sys; sys.path.insert(0,'scripts'); import xt; from pathlib import Path; d,s=xt.review_debt(Path('.'),Path('docs/ops/AUDIT-STATUS.md')); print(*d,sep=chr(10)); sys.exit(1 if d or not s else 0)"`
- [ ] `T-3546` Cắt 3.28.0: VERSION, CHANGELOG (mục "Dự án đích": `loop attach/resolve/unblock`, `--max-task-runs`; `perf compare` mẫu v2 từ chối so khi lệch đơn vị/lệnh/bộ đo/nền tảng hoặc baseline bẩn; `/optimize` tới 3.29.0 vẫn ghi lần thử qua `loop record` — trần `task_runs` có thể chặn, `--max-task-runs 0` khi tối ưu), GO-NO-GO phần máy (sau: T-3556) — Gate: `python3 scripts/xt.py changelog-check && grep -qx '3.28.0' VERSION && python3 scripts/xt.py progress-check && python3 scripts/xt.py blueprint-status BLUEPRINT.md --strict --run`
### Lát 2 — bước kế chỉ đọc (3.29.0)
- [ ] `T-3547` `loop next-step --json` mục tiêu `build-until-clean`; FLOW-09…13 (sau: T-3546; files: scripts/xt.py, tests/test_next_step.py, tests/test_flow.py, tests/shard-weights.json) — Gate: `XT_FLOW_STRICT=FLOW-09,FLOW-10,FLOW-11,FLOW-12,FLOW-13 python3 -m unittest -q tests.test_next_step tests.test_flow`
- [ ] `T-3548` `harden-to-signoff`: gom việc harden ID ổn định, nợ review theo head; FLOW-14/15 (sau: T-3547; files: scripts/xt.py, tests/test_next_step.py, tests/test_flow.py) — Gate: `XT_FLOW_STRICT=FLOW-14,FLOW-15 python3 -m unittest -q tests.test_next_step tests.test_flow`
- [ ] `T-3549` Gói nghiệm thu nháp (`candidate_head`, `evidence_fp`, `human_pending`); FLOW-16/17 (sau: T-3548; files: scripts/xt.py, tests/test_next_step.py, tests/test_flow.py) — Gate: `XT_FLOW_STRICT=FLOW-16,FLOW-17 python3 -m unittest -q tests.test_next_step tests.test_flow`
- [ ] `T-3550` Stop hook in gợi ý `next-step`; skill `/autopilot` `/complete` gọi `next-step` (đổi chữ trong trần byte) (sau: T-3549) — Gate: `python3 -m unittest -q -k test_stop_hint_next_step tests.test_hooks && python3 -m unittest -q tests.test_docs_budget tests.test_next_step`
### Lát 3 — một lần thử tối ưu
- [ ] `T-3551` ADR riêng cho `perf trial` từ ràng buộc ADR-0052 §7 (D-203) + held-out `LOOP-OPT-007` và falsifier `LOOP-OPT-004` (review #290 lượt 8): spike môi trường đo (worktree tạm, cài editable, `node_modules`, `--setup`), bộ chấm và bộ test tương đương từ commit gốc, đại lượng tất định; ID FLOW cho đường giữ/thu hồi/baseline bị lái/bộ chấm bị sửa — T-3552 STRICT cả các ID mới này khi tách task (sau: T-3550; files: docs/adr, research) — Gate: `git grep --untracked -qiE '^# ADR-[0-9]+: .*perf trial' -- docs/adr ':!docs/adr/0052-*'`
- [ ] `T-3552` Triển khai `perf trial` theo ADR của T-3551, skill `/optimize` và `optimization-loop.md` gọi nó (tách task khi làm; sau: T-3551; files: scripts/xt.py, tests/test_perf_trial.py, tests/test_flow.py, tests/shard-weights.json, .claude/skills/optimize/SKILL.md, framework/11-autonomous-loop/optimization-loop.md) — Gate: `XT_FLOW_STRICT=FLOW-20,FLOW-21,FLOW-22,FLOW-23 python3 -m unittest -q tests.test_perf_trial tests.test_flow tests.test_docs_budget`
- [ ] `T-3557` Audit delta lát 2–3 (sau: T-3552; files: docs/ops/AUDIT-STATUS.md) — Gate: `python3 scripts/xt.py audit check docs/ops/AUDIT-STATUS.md --strict && python3 -c "import sys; sys.path.insert(0,'scripts'); import xt; from pathlib import Path; d,s=xt.review_debt(Path('.'),Path('docs/ops/AUDIT-STATUS.md')); print(*d,sep=chr(10)); sys.exit(1 if d or not s else 0)"`
- [ ] `T-3553` Cắt 3.29.0 + PROGRESS (`release-check` ở G7 sau vòng) (sau: T-3557) — Gate: `python3 scripts/xt.py changelog-check && grep -qx '3.29.0' VERSION && python3 scripts/xt.py progress-check && python3 scripts/xt.py blueprint-status BLUEPRINT.md --strict --run`
### Lát 4–5 — cần người (defer)
- [ ] `T-3554` Lát 4: pilot `next-step` chế độ gợi ý trên repo khung + ≥ 2 dự án đích, so `action` với quyết định thật; rồi cho Stop hook đọc (sau: T-3550) — Gate: `test -s docs/ops/PILOT-next-step.md`
- [ ] `T-3555` Lát 5: field trigger (SLO 7 ngày), bot nâng bản, worker ngoài phiên (ADR mới), event policy `pull_request_target` cho `pr-review.yml` (sau: T-3553) — Gate: `git grep --untracked -qiE '^# ADR-[0-9]+: .*(worker ngoài phiên|field trigger)' -- docs/adr`
