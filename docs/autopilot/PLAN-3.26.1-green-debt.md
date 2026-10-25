# PLAN-3.26.1-green-debt.md — Khung X-Templates · trả 3 🟢 mở của audit delta3 → bản 3.26.1

> Lập ngày 2026-10-25. Nguồn: `docs/ops/AUDIT-STATUS.md` AUD-HAR-113, AUD-HAR-114, AUD-DOC-086 (chủ: phiên chính, hạn
> 2026-11-08) và `release-check` NO-GO hàng `review_debt` (`VERSION` đổi ở #265 sau SHA quét `daefc7c`). Phiên chính tự
> duyệt (D-192).
>
> **Cú pháp bắt buộc cho máy:** mỗi task một dòng `- [ ] \`T-NNNN\` <việc> — Gate: \`<lệnh>\``.

## Tóm tắt (cổng duyệt — phiên chính tự duyệt, D-192)
- Phạm vi: (1) AUD-HAR-113: ghép lại `BLUEPRINT.md` với `XT_FRAMEWORK_LINK=framework` — đo trên bản nháp: chỉ 6 mục đổi
  chữ thật (`LOOP-OPT-016` mới, `LOOP-OPT-002/011`, `LOOP-STOP-005`, `LOOP-HARNESS-024`), giữ trạng thái 104 mục; không có
  biến này, `compose` ở repo khung viết link `.xtemplates/framework/…` nên 19 mục MUST "đổi chữ" giả và bị đặt lại `[ ]`
  (nguồn nhiễu của lần #257) · (2) AUD-HAR-114: `loop init` khi vòng cũ `blocked` (PLAN đợt trước đổi tên/xoá) in verdict
  và lý do, gợi `loop stop` · (3) AUD-DOC-086: RUNBOOK §4 một dòng về push có ≥ 2 commit đổi `VERSION` · (4) sổ audit:
  đánh dấu 3 🟢 đã sửa (SHA quét cập nhật ở PR sổ sau merge — PR có mã không tự trả `review_debt`); CHANGELOG
  `[3.26.1]`, VERSION, PROGRESS (ghi mẹo `XT_FRAMEWORK_LINK=framework`).
- Không làm: đổi mặc định `_rel_link` theo `framework_repo` (đổi hành vi cho mọi người gọi; biến môi trường đã có, ghi tài
  liệu là đủ); trả 57 MUST tick không có lệnh kiểm.
- Rủi ro: C901 ≤ 10 ở `_live_loop`/`_loop_init`; test mới phải đỏ trước khi sửa. Đường lùi: revert PR.
- Cách làm: phiên chính tự làm (hàng "Làm trực tiếp"); một PR, mã ngoài `.md` ≈ 25 dòng.

## Ngân sách (4 con số)
- Số vòng tối đa: 40 (`--single-session`) · Chi phí: 0 đồng ngoài phiên · Timeout Gate: 1800 giây · Hạn: 4 giờ sau `loop init`

## Điểm dừng bắt buộc (`loop defer`)
- Tag `v3.26.1` do `release-tag.yml` tạo sau merge.

## Task
- [x] `T-3401` Ghép lại `BLUEPRINT.md` bằng `XT_FRAMEWORK_LINK=framework python3 scripts/xt.py compose --profile cli-tool --scale S --full --out BLUEPRINT.md` (AUD-HAR-113) (files: BLUEPRINT.md) — Gate: `grep -q LOOP-OPT-016 BLUEPRINT.md && ! grep -q '— Cũ (rev' BLUEPRINT.md && ! grep -q '\.xtemplates/framework' BLUEPRINT.md && python3 scripts/xt.py blueprint-status BLUEPRINT.md --strict`
- [x] `T-3402` `loop init` khi vòng cũ `blocked` in verdict + lý do của `loop_verdict` và gợi `loop stop`; test `test_init_after_plan_renamed` đỏ trước khi sửa (AUD-HAR-114) (files: scripts/xt.py, tests/test_xt_loop.py) — Gate: `python3 -m unittest tests.test_xt_loop -k init_after_plan_renamed && grep -q init_after_plan_renamed tests/test_xt_loop.py && scripts/dev-task.sh typecheck`
- [x] `T-3403` RUNBOOK-PR-STEWARD §4: push `main` có ≥ 2 commit đổi `VERSION` chỉ tag đầu push — gắn tag cho commit sau bằng `workflow_dispatch` với `sha` (AUD-DOC-086) (files: docs/ops/RUNBOOK-PR-STEWARD.md) — Gate: `grep -q 'workflow_dispatch.*sha' docs/ops/RUNBOOK-PR-STEWARD.md && python3 scripts/check-links.py`
- [x] `T-3404` Sổ audit: 3 🟢 → đã sửa (quét delta `daefc7c..<merge>` cập nhật SHA ở PR sổ sau merge, như delta3); CHANGELOG `[3.26.1]`, VERSION 3.26.1, PROGRESS ≤ 7 900 B (sau: T-3401, T-3402, T-3403; files: docs/ops/AUDIT-STATUS.md, CHANGELOG.md, VERSION, PROGRESS.md) — Gate: `python3 scripts/xt.py audit check docs/ops/AUDIT-STATUS.md --strict && test "$(cat VERSION)" = 3.26.1 && grep -q '^## \[3.26.1\]' CHANGELOG.md && test "$(wc -c < PROGRESS.md)" -le 7900 && scripts/dev-task.sh lint`
