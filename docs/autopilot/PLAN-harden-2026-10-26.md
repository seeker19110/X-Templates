# PLAN-harden-2026-10-26.md — Khung X-Templates · gắn lệnh kiểm máy cho MUST đã tick

> Lập ngày 2026-10-26 theo `/complete` (pha harden). Nguồn: `release-check` tại `339759f` GO (chờ người), hàng SHOULD
> `unchecked_must` WARN 57/64 MUST đạt không có lệnh kiểm. Phiên chính tự duyệt (D-193).
>
> **Cú pháp bắt buộc cho máy:** mỗi task một dòng `- [ ] \`T-NNNN\` <việc> — Gate: \`<lệnh>\``.

## Tóm tắt (cổng duyệt — phiên chính tự duyệt, D-193)
- Hiện trạng: 0 🔴/🟠 mở, mọi BLOCKER PASS, mọi GO-NO-GO đã ký. Nợ còn lại có số: 57/64 MUST `[x]` chỉ có bằng chứng
  bằng lời — `loop verify --all` không chạy lại được, mục có thể âm thầm hỏng.
- Phạm vi: gắn `— Kiểm: \`…\`` (chỉ đọc, offline, < 5 giây) cho 19 MUST mà repo đã đạt và kiểm được bằng lệnh tất định:
  BASE-REPO-002/003/004/007/008, BASE-SEC-004/007/009, BASE-DEP-001/002/004/007, BASE-DOC-003/006,
  BASE-GATE-001/002/004, PRF-CLI-002/005. SEC-004/007 dùng luật bandit của ruff (AST; SEC-004 thêm `git grep` cấu hình/shell sau review #274) — đột biến
  `shell=True`/`os.system`/`verify=False`/`_create_unverified_context` bị bắt (exit 1). Mục tiêu: `unchecked_must` 57 → 38.
- Không làm: BASE-ERR-001 (ruff S110 báo `scripts/xt.py:2048` `except Exception: pass` có chủ đích — sửa mã là lát riêng
  cần review, ghi 🟢 ở sổ khi audit kế); MUST cần API sống (ruleset thật, tag) hay đánh giá người (ADR đủ chất lượng).
- Rủi ro: lệnh kiểm do harness chạy qua guard (LOOP-STOP-027) — chỉ đọc. Kiểm REPO-008 đọc `main.json` (bản khai),
  không phải ruleset sống. Đường lùi: revert PR (chỉ `BLUEPRINT.md`, PLAN, PROGRESS).
- Cách làm: phiên chính tự làm (hàng "Làm trực tiếp"); một PR tài liệu, làn nhanh.

## Ngân sách (4 con số)
- Số vòng tối đa: 20 (`--single-session`) · Chi phí: 0 đồng ngoài phiên · Timeout Gate: 900 giây · Hạn: 2 giờ sau `loop init`

## Điểm dừng bắt buộc (`loop defer`)
- Không có.

## Task
- [x] `T-3501` Gắn `— Kiểm:` cho 19 MUST đã tick (files: BLUEPRINT.md) — Gate: `for id in BASE-REPO-002 BASE-REPO-003 BASE-REPO-004 BASE-REPO-007 BASE-REPO-008 BASE-SEC-004 BASE-SEC-007 BASE-SEC-009 BASE-DEP-001 BASE-DEP-002 BASE-DEP-004 BASE-DEP-007 BASE-DOC-003 BASE-DOC-006 BASE-GATE-001 BASE-GATE-002 BASE-GATE-004 PRF-CLI-002 PRF-CLI-005; do grep -qE "^- \[x\] .$id. .*— Kiểm: " BLUEPRINT.md || exit 1; done && python3 scripts/xt.py blueprint-status BLUEPRINT.md --strict --run`
- [x] `T-3502` PROGRESS ghi kết quả (sau: T-3501; files: PROGRESS.md) — Gate: `grep -q 'PLAN-harden-2026-10-26' PROGRESS.md && test "$(wc -c < PROGRESS.md)" -le 7900 && scripts/dev-task.sh lint`
