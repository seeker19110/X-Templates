# PLAN-3.18-feedback2.md — Khung X-Templates · 7 lỗi 🟢 dự án đích còn lại → bản 3.18.0

> Lập ngày 2026-10-24. Chủ repo gọi lại `/autopilot` sau PLAN-3.17-feedback (done, `v3.17.0`). Nguồn: bảng phân loại
> 30 nhóm phản hồi của PLAN-3.17 (scratchpad phiên, không commit) — 7 dòng `con-loi` 🟢 chưa sửa. Phiên chính tự duyệt (D-157).
>
> **Cú pháp bắt buộc cho máy:** mỗi task một dòng `- [ ] \`T-NNNN\` <việc> — Gate: \`<lệnh>\``.

## Tóm tắt (cổng duyệt — phiên chính tự duyệt, D-157)
- Phạm vi: 7 lỗi 🟢 tái hiện được trên HEAD 3.17.0 — lệnh kiểm `BASE-SEC-002` tự khớp; `compose` giữ anchor nội trang;
  `check-links.py` không kiểm `#anchor`; `loop init` sau vòng đã dừng mất danh sách chờ người và đòi chạy lại Gate cũ;
  máy mới đòi chạy lại Gate của mọi task `[x]` (thiếu hướng dẫn mỗi đợt một PLAN); `loop decide` ở hai worktree trùng
  D-NNN; lệnh kiểm chỉ đọc của mục hàng rào (`LOOP-ORCH-003`, `LOOP-STOP-001/002`) bị guard chặn → `loop verify` đỏ.
- Cách: mỗi lỗi một test tái hiện đỏ trước, sửa nhỏ nhất; mục hàng rào có lệnh con chỉ đọc `xt.py harness-check` thay vì
  để dự án tự viết `python3 -c` (guard chặn đúng — không nới guard).
- Không làm: nhóm `thiet-ke` (#12 nới `curl | python3 -c`, #22 `loop resume --task`, #24 `package.json` vào GATE_PATTERNS)
  — giữ nguyên; giới hạn guard D-155. Trần byte ADR-0043 giữ nguyên.
- Rủi ro: `check-links` kiểm anchor làm đỏ link cũ trong repo (đỡ: sửa link gãy trong cùng task); `loop init` mang bằng
  chứng cũ sang vòng mới làm lọt Gate cũ (đỡ: chỉ mang khi bằng chứng xanh và khớp dấu vân tay Gate hiện tại; `loop verify
  --all` cuối vẫn chạy lại mọi Gate).

## Ngân sách (4 con số)
- Số vòng tối đa: `max(40, 8 × task)` (`loop init --single-session` tính)
- Chi phí: 0 đồng ngoài phiên (không phụ thuộc mới)
- Timeout mỗi lệnh Gate: 1800 giây (`XT_RECORD_TIMEOUT` mặc định)
- Ngày hết hạn: 12 giờ sau `loop init` (`--hours 12`)

## Điểm dừng bắt buộc (`loop defer`; `loop block` khi mọi việc còn lại phụ thuộc)
- Đổi ruleset sống, secret, quyền repo đích: chủ repo
- Nâng khung ở dự án đích (PR `install.py`): chủ dự án merge

## Task

### Lát 1 — Liên kết và lệnh kiểm
- [x] `T-2601` Lệnh kiểm gợi ý của `BASE-SEC-002` không tự khớp chính dòng của mục: mẫu chặt `AKIA[0-9A-Z]{16}|-----BEGIN (RSA|EC|OPENSSH) PRIVATE KEY-----`; test quét khung + BLUEPRINT bằng mẫu ghi trong mục = 0 khớp (files: framework/01-baseline/security-minimum.md, BLUEPRINT.md, tests/test_xt.py) — Gate: `python3 -m unittest discover -s tests -k base_sec_002_selfmatch`
- [ ] `T-2602` `compose`: anchor nội trang `(#x)` trong mục module đổi thành `(<link_root>/<doc_rel>#x)` — link không gãy khi mục sang BLUEPRINT/BACKLOG (sau: T-2601; files: scripts/xt.py, tests/test_xt.py) — Gate: `python3 -m unittest discover -s tests -k rebase_links_anchor`
- [ ] `T-2603` `check-links.py` kiểm `#anchor` (cùng file và file `.md` khác) theo slug GitHub (chữ thường, bỏ dấu câu, giữ chữ Unicode, khoảng trắng → `-`, trùng → `-1`) + `<a id|name>`; sửa link gãy lộ ra trong repo (sau: T-2602; files: scripts/check-links.py, tests/test_check_links.py) — Gate: `python3 -m unittest discover -s tests -k check_links_anchor && python3 scripts/check-links.py`

### Lát 2 — Vòng tự trị
- [ ] `T-2611` `loop init` khi vòng trước đã dừng: giữ `deferred` của task còn mở trong PLAN mới; task `[x]` có bằng chứng xanh khớp dấu vân tay Gate hiện tại được mang sang (không đòi chạy lại); cảnh báo số task `[x]` thiếu bằng chứng cục bộ kèm gợi ý mỗi đợt một `PLAN-<đợt>.md` (files: scripts/xt.py, tests/test_xt_loop.py) — Gate: `python3 -m unittest discover -s tests -k loop_init_carry`
- [ ] `T-2612` `loop decide` lấy số D-NNN kế tiếp theo max của sổ ở mọi worktree cùng repo (`git worktree list`), không chỉ cây đang đứng (sau: T-2611; files: scripts/xt.py, tests/test_xt_loop.py) — Gate: `python3 -m unittest discover -s tests -k decide_worktrees`
- [ ] `T-2613` Mẫu PLAN + skill `/autopilot` + README vòng tự trị: mỗi đợt một `docs/autopilot/PLAN-<đợt>.md` (bằng chứng `.autopilot/` không theo git — máy mới chỉ chạy lại PLAN đang làm) (sau: T-2612; files: framework/templates/PLAN.md, .claude/skills/autopilot/SKILL.md, framework/11-autonomous-loop/README.md) — Gate: `grep -q 'PLAN-<đợt>' framework/templates/PLAN.md && grep -q 'PLAN-<đợt>' .claude/skills/autopilot/SKILL.md`

### Lát 3 — Lệnh kiểm hàng rào và phát hành
- [ ] `T-2621` `xt.py harness-check` (chỉ đọc, exit 0/1): guard của dự án chặn bộ lệnh mẫu của `LOOP-STOP-001/002`; `.claude/settings.json` `permissions.ask` rỗng; mọi agent khai `tools:` tường minh, không `permissionMode` (`LOOP-ORCH-003`). `loop verify` gặp exit 126 của guard thì gợi ý lệnh này. Đổi `→ Kiểm:` của ba mục sang lệnh này (files: scripts/xt.py, tests/test_xt_cli.py, framework/11-autonomous-loop/orchestration-and-subagents.md, framework/11-autonomous-loop/stop-points-and-escalation.md, CHANGELOG.md) — Gate: `python3 -m unittest discover -s tests -k harness_check`
- [ ] `T-2629` VERSION 3.18.0 + CHANGELOG `[3.18.0]` + PROGRESS (sau: T-2603, T-2613, T-2621; files: VERSION, CHANGELOG.md, PROGRESS.md) — Gate: `scripts/dev-task.sh gate`
