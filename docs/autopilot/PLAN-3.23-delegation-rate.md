# PLAN-3.23-delegation-rate.md — Khung X-Templates · `delegation_rate` trong `xt.py loop stats` → bản 3.22.0

> Lập ngày 2026-10-25. Chủ repo: "tiếp tục trả nợ delegation_rate" (nợ cuối của ADR-0045). Phiên chính tự duyệt (D-171).
>
> **Cú pháp bắt buộc cho máy:** mỗi task một dòng `- [ ] \`T-NNNN\` <việc> — Gate: \`<lệnh>\``.

## Tóm tắt (cổng duyệt — phiên chính tự duyệt, D-171)
- Phạm vi: `loop_stats` thêm, qua helper `_delegation_stats(per)`: `delegated` (task có `executors` khác rỗng), `self_done`
  (task `executors` rỗng), `delegation_rate` (= giao / `task_count`, `None` khi rỗng), `first_pass_rate_delegated`,
  `first_pass_rate_self` (task `runs_to_green == 1` / số task của nhóm, `None` khi nhóm rỗng); bản chữ `loop stats` thêm một
  dòng "Giao việc: …". `LOOP-ORCH-020` Kiểm trỏ trường mới (hết đếm tay bằng `jq`).
- Không làm: đổi định dạng `runs.jsonl`/cờ `--executor`; chi phí/token mỗi task (harness chưa ghi); đổi mặc định giao việc
  (chờ số ≥ 10 task/nhóm × ≥ 2 vòng — `LOOP-ORCH-020`).
- Ràng buộc: `mypy --strict`, C901 ≤ 10, coverage dòng + nhánh 100 %, trần byte `scripts/` (còn dư ~6 KB).
- Rủi ro: task tự làm rồi chuyển cấp tính vào nhóm giao (ghi ở `LOOP-ORCH-020`); trường mới additive nên người đọc JSON cũ
  không vỡ. Đường lùi: revert PR.
- Cách làm: T-3201 là mã có test → giao `executor` (tầng mặc định, `loop record --executor executor`) — điểm đo "giao" đầu
  tiên của `LOOP-ORCH-020`; T-3202/T-3203 là chữ → phiên chính tự làm.

## Ngân sách (4 con số)
- Số vòng tối đa: `max(40, 8 × task)`
- Chi phí: 0 đồng ngoài phiên
- Timeout mỗi lệnh Gate: 1800 giây
- Ngày hết hạn: 3 giờ sau `loop init` (`--hours 3`)

## Điểm dừng bắt buộc (`loop defer`; `loop block` khi mọi việc còn lại phụ thuộc)
- Tag `v3.22.0` qua `release-tag.yml` sau merge; nâng khung ở dự án đích (`install.py`): chủ dự án

## Task

### Lát 1 — `delegation_rate`
- [x] `T-3201` `scripts/xt.py`: helper `_delegation_stats` + trường mới trong `loop_stats` + dòng "Giao việc" ở `_loop_stats`; test đủ nhánh trong `tests/test_xt_core.py` (files: scripts/xt.py, tests/test_xt_core.py) — Gate: `python3 -m unittest tests.test_xt_core && python3 -m mypy --strict --python-version 3.11 scripts/xt.py && python3 -m ruff check scripts tests && python3 -m ruff format --check scripts tests`
- [x] `T-3202` `LOOP-ORCH-020` Kiểm trỏ `delegation_rate`/`first_pass_rate_*`; ghi chú `LOOP-ORCH-017` (sau: T-3201; files: framework/11-autonomous-loop/orchestration-and-subagents.md) — Gate: `python3 -m unittest tests.test_docs_budget && python3 scripts/xt.py validate && python3 scripts/check-links.py && grep -q "delegation_rate" framework/11-autonomous-loop/orchestration-and-subagents.md`
- [x] `T-3203` CHANGELOG `[3.22.0]`, VERSION 3.22.0, PROGRESS.md ≤ 8 KB (sau: T-3202; files: CHANGELOG.md, VERSION, PROGRESS.md) — Gate: `scripts/dev-task.sh lint`
