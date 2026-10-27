# PLAN-harden-2026-10-27-loops.md — Khung X-Templates · nâng tự chủ ba vòng, lát 0–3

> Lập ngày 2026-10-27 theo `/complete` (pha harden) và yêu cầu chủ repo "hoàn thành hết đi" (sáu lát của
> [nghiên cứu 2026-10-26](../../research/2026-10-26-autopilot-complete-optimize.md) §11). Thiết kế: ADR-0051, ADR-0052. Phiên chính tự duyệt (D-202).
>
> **Cú pháp bắt buộc cho máy:** mỗi task một dòng `- [ ] \`T-NNNN\` <việc> — Gate: \`<lệnh>\``.

## Tóm tắt (cổng duyệt — phiên chính tự duyệt, D-202)
- Hiện trạng: `main` 3.27.0, audit delta `e8c8d96..137a047` 0 🔴/🟠 (#289); `release-check` chỉ còn chữ ký người.
- Phạm vi: lát 0 corpus luồng FLOW (§10) · lát 1 `rev` state, không-tiến-triển theo task, `loop attach/resolve/unblock`, mẫu perf v2 →
  3.28.0 · lát 2 `loop next-step` chỉ đọc, gom việc harden, gói nghiệm thu nháp · lát 3 `perf trial` → 3.29.0.
- Không làm (defer, cần người/dữ liệu): lát 4 pilot phiên thực ≥ 2 dự án đích; lát 5 field trigger, bot nâng bản, worker ngoài phiên,
  event policy `pull_request_target` (T-3554, T-3555).
- Cách làm: mỗi task một PR (≤ ~150 dòng mã, test đỏ trước khi sửa), `executor-deep` viết, `reviewer-alt` rà ở head, merge ghim head;
  phiên bị ràng một nhánh nên tuần tự, gộp `origin/main` sau mỗi merge.
- Rủi ro: chữ README mảng 11/skill hết byte → câu mới đổi câu cũ; trần theo task chặn oan (`--max-task-runs 0`). Đường lùi: ADR-0052 §Đường lùi.

## Ngân sách (4 con số)
- Số vòng tối đa: 200 (`--single-session`) · Chi phí: 0 đồng ngoài phiên (tương tác: `null`) · Timeout Gate: 900 giây · Hạn: 36 giờ sau `loop init`

## Điểm dừng bắt buộc (`loop defer`)
- T-3554, T-3555 (lát 4–5): dữ liệu phiên thực ở dự án đích, SLO field, quyền/chi phí ngoài phiên — chỉ chủ dự án có.
- Ký GO-NO-GO 3.28.0/3.29.0 (dòng 20) — người.

## Task
### Lát 0 — corpus luồng
- [ ] `T-3536` `tests/test_flow.py`: FLOW-01…08, 18, 19 trong repo git tạm với `xt.py` thật; ca chưa sửa `expectedFailure` kèm ID tái hiện, FLOW-05 xanh (files: tests/test_flow.py, tests/shard-weights.json) — Gate: `python3 -m unittest -q tests.test_flow && scripts/dev-task.sh lint`
### Lát 1 — nền chung (3.28.0)
- [ ] `T-3537` `_live_loop` xét trần vòng/hạn trước verdict (ADR-0051 §Quyết định, D-177) (sau: T-3536; files: scripts/xt.py, tests/test_xt_loop.py) — Gate: `python3 -m unittest -q tests.test_xt_loop tests.test_flow`
- [ ] `T-3538` `rev` + `update_state` + khoá `state.lock` cho mọi lệnh ghi state; FLOW-07 xanh (sau: T-3537; files: scripts/xt.py, tests/test_xt_loop.py, tests/test_flow.py) — Gate: `python3 -m unittest -q tests.test_xt_loop tests.test_flow tests.test_hooks`
- [ ] `T-3539` `task_runs` + `max_task_runs` + `loop init --max-task-runs`; FLOW-04/06 xanh (sau: T-3538; files: scripts/xt.py, tests/test_xt_loop.py, tests/test_flow.py) — Gate: `python3 -m unittest -q tests.test_xt_loop tests.test_flow`
- [ ] `T-3540` `loop attach` + lối ra theo nguồn (ADR-0052 §6); FLOW-01 xanh (sau: T-3539; files: scripts/xt.py, tests/test_xt_cli.py, tests/test_flow.py) — Gate: `python3 -m unittest -q tests.test_xt_cli tests.test_flow`
- [ ] `T-3541` `loop resolve`; FLOW-02/03 xanh (sau: T-3540; files: scripts/xt.py, tests/test_xt_cli.py, tests/test_flow.py) — Gate: `python3 -m unittest -q tests.test_xt_cli tests.test_flow`
- [ ] `T-3542` `loop unblock` + `_carry_previous` mang `attached/resolved/unblocked` (sau: T-3541; files: scripts/xt.py, tests/test_xt_cli.py, tests/test_xt_loop.py) — Gate: `python3 -m unittest -q tests.test_xt_cli tests.test_xt_loop tests.test_flow`
- [ ] `T-3543` `loop resume` cảnh báo + chữ đổi (SESSION_MISMATCH_NOTE, doctor, README mảng 11, skill `/autopilot`, `loop-design.md`, `stop-points-and-escalation.md`, `harness-files.md`, README bảng lệnh, BLUEPRINT LOOP-HARNESS-024/LOOP-STOP-021) + CHANGELOG "Dự án đích" (sau: T-3542) — Gate: `python3 -m unittest -q tests.test_hooks tests.test_xt_cli tests.test_docs_budget && python3 scripts/xt.py validate && python3 scripts/check-links.py && ! git grep -n 'dùng `loop resume` để gắn' -- framework .claude README.md`
- [ ] `T-3544` `perf sample` ghi mẫu v2 (sau: T-3543; files: scripts/xt.py, tests/test_perf.py) — Gate: `python3 -m unittest -q tests.test_perf`
- [ ] `T-3545` `perf compare` từ chối lệch trường trọng yếu, v1 → `unverified-manual`; FLOW-18/19 xanh (sau: T-3544; files: scripts/xt.py, tests/test_perf.py, tests/test_flow.py) — Gate: `python3 -m unittest -q tests.test_perf tests.test_flow`
- [ ] `T-3546` Cắt 3.28.0: VERSION, CHANGELOG, GO-NO-GO phần máy (sau: T-3545) — Gate: `python3 scripts/xt.py changelog-check && grep -qx '3.28.0' VERSION && python3 scripts/xt.py release-check --json > /dev/null; test $? -le 1`
### Lát 2 — bước kế chỉ đọc (3.29.0)
- [ ] `T-3547` `loop next-step --json` mục tiêu `build-until-clean`; FLOW-09…13 (sau: T-3546; files: scripts/xt.py, tests/test_next_step.py, tests/test_flow.py) — Gate: `python3 -m unittest -q tests.test_next_step tests.test_flow`
- [ ] `T-3548` `harden-to-signoff`: gom việc harden ID ổn định, nợ review theo head; FLOW-14/15 (sau: T-3547; files: scripts/xt.py, tests/test_next_step.py) — Gate: `python3 -m unittest -q tests.test_next_step tests.test_flow`
- [ ] `T-3549` Gói nghiệm thu nháp (`candidate_head`, `evidence_fp`, `human_pending`); FLOW-16/17 (sau: T-3548; files: scripts/xt.py, tests/test_next_step.py) — Gate: `python3 -m unittest -q tests.test_next_step tests.test_flow`
- [ ] `T-3550` Stop hook in gợi ý `next-step`; skill `/autopilot` `/complete` gọi `next-step` (đổi chữ trong trần byte) (sau: T-3549) — Gate: `python3 -m unittest -q tests.test_hooks tests.test_docs_budget tests.test_next_step`
### Lát 3 — một lần thử tối ưu
- [ ] `T-3551` `perf trial start/finish` + `.autopilot/perf-trials.jsonl`, trần 3 lần/điểm nóng; FLOW-20/22 (sau: T-3550; files: scripts/xt.py, tests/test_perf_trial.py, tests/test_flow.py) — Gate: `python3 -m unittest -q tests.test_perf_trial tests.test_flow`
- [ ] `T-3552` `perf trial --resume` sau crash, chỉ số phụ vượt trần đỏ; FLOW-21/23; skill `/optimize` gọi `perf trial` (sau: T-3551) — Gate: `python3 -m unittest -q tests.test_perf_trial tests.test_flow tests.test_docs_budget`
- [ ] `T-3553` Cắt 3.29.0 + `release-check` + PROGRESS (sau: T-3552) — Gate: `python3 scripts/xt.py changelog-check && grep -qx '3.29.0' VERSION && python3 scripts/xt.py progress-check`
### Lát 4–5 — cần người (defer)
- [ ] `T-3554` Lát 4: pilot `next-step` chế độ gợi ý trên repo khung + ≥ 2 dự án đích, so `action` với quyết định thật; rồi cho Stop hook đọc — Gate: `test -s docs/ops/PILOT-next-step.md`
- [ ] `T-3555` Lát 5: field trigger (SLO 7 ngày), bot nâng bản, worker ngoài phiên (ADR mới), event policy `pull_request_target` cho `pr-review.yml` — Gate: `test -s docs/adr/0053-*.md`
