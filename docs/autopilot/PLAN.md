# PLAN.md — Khung X-Templates · sửa audit delta #58–#66 (4 đợt)

> Lập ngày 2026-10-16. Chủ repo duyệt kế hoạch 4 đợt ("duyệt, làm theo kế hoạch 4 đợt") rồi gọi `/autopilot`.
> Nguồn: `docs/ops/AUDIT-REPORT-2026-10-16-delta.md`. Kế hoạch trước (T-601…T-602) xong ở #41.

## Tóm tắt (cổng duyệt — phiên chính tự duyệt, D-013)
- Blueprint repo khung: MUST 62 đạt · 8 miễn · 0 chưa (không đổi mục blueprint trong kế hoạch này ngoài bằng chứng).
- Stack: Python ≥ 3.11 stdlib (`xt.py`, `guard.py`), bash hook; không phụ thuộc mới.
- Phạm vi: 4 🟠 (AUD-SEC-028, AUD-SEC-029, AUD-HAR-042, AUD-CFG-006) + 🟢 đi kèm; mỗi đợt một PR mở kèm auto-merge (L3).
- Đợt A (#69) và đợt B (nhánh `…-fixB`) đã code xong; còn: giải xung đột với #68/#70/#71 (chủ repo: "fix xung đột"),
  PR đợt B, đợt C (`redact`), đợt D (sổ audit, PROGRESS, bằng chứng blueprint).
- Rủi ro: các phiên khác merge vào `main` song song (#68–#71) → xung đột lặp lại; giải bằng merge `main` vào nhánh,
  không rebase/force-push.

## Ngân sách (4 con số)
- Số vòng tối đa: 20 (`max(20, 4 × task)`)
- Chi phí: 0 đồng ngoài phiên (không phụ thuộc mới)
- Timeout mỗi lệnh Gate: 600 giây
- Ngày hết hạn: 4 giờ sau `loop init` (`--hours 4`)

## Điểm dừng bắt buộc (`loop defer`; `loop block` khi mọi việc còn lại phụ thuộc)
- Merge PR thuộc ngoại lệ cứng (ADR-0016) — không có trong kế hoạch này
- Force-push, xoá nhánh, đổi quyền/ruleset repo
- Chủ repo từ chối một lệnh → không thử cách khác cho cùng hiệu ứng (`LOOP-STOP-025`)

## Task

- [x] `T-701` Đợt A: #69 giải xung đột với `main` (#68), test guard mới xanh trên cây đã merge, auto-merge bật — Gate: `python3 -m unittest tests.test_hooks`
- [x] `T-702` Đợt B: giải xung đột với `main`, commit, PR kèm auto-merge (ADR-0016, D-012; AUD-HAR-042, CODE-007/010, DOC-031…037) — Gate: `python3 -m unittest tests.test_merge && python3 scripts/xt.py validate && python3 scripts/check-links.py`
- [x] `T-703` Đợt C: `redact` — giá trị trong nháy chứa nháy loại kia, `pwd`/`pass`, không che nhầm `npm_config_*`/`hf_hub_*`, so ISO bằng `_parse_iso`, test thông điệp no-op (AUD-CFG-006/007/008, CODE-008/009, TEST-006) — Gate: `python3 -m unittest tests.test_xt tests.test_xt_core tests.test_xt_cli tests.test_hooks`
- [x] `T-704` Đợt D: sổ audit đánh dấu đã sửa (#PR), PROGRESS, 11 bằng chứng blueprint (AUD-HAR-043/044), AUD-HAR-045 nợ có chủ; cổng đầy đủ — Gate: `python3 scripts/xt.py audit check docs/ops/AUDIT-STATUS.md --strict && python3 scripts/xt.py blueprint-status BLUEPRINT.md --strict && scripts/dev-task.sh gate`
