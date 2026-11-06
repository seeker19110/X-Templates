# PLAN-harden-2026-10-26c.md — Khung X-Templates · lệnh kiểm máy cho 37 MUST còn lại

> Lập ngày 2026-10-26 theo `/complete` (pha harden), nối PLAN-harden-2026-10-26/26b (#274, #277). Chủ repo: "làm hết
> 17 mục đó, còn 20 mục chọn theo hướng chất lượng, cứ thế mà quyết định". Phiên chính tự duyệt (D-195).
>
> **Cú pháp bắt buộc cho máy:** mỗi task một dòng `- [ ] \`T-NNNN\` <việc> — Gate: \`<lệnh>\``.

## Tóm tắt (cổng duyệt — phiên chính tự duyệt, D-195)
- Hiện trạng: `unchecked_must` 37/64 — MUST `[x]` chỉ có bằng chứng bằng lời. Đọc lại từng mục: gần như mọi bằng chứng
  đã trỏ một test hành vi có sẵn hoặc một phép grep — biến chúng thành `— Kiểm:` là hướng chất lượng (máy chạy lại, CI
  `checks` chạy trên mỗi PR từ D-194). Không mục nào đổi sang `[~]` (mọi mục đều áp dụng và đạt).
- 17 mục kiểm bằng lệnh chỉ đọc: DATA-001 (iconv UTF-8 + 0 BOM), DATA-006 (không `now()` naive trừ nhãn giờ hiển thị),
  REPO-001, REPO-005 (subject squash từ `v3.20.0` qua `pr title-check` — #247 trước đó dài 87 ký tự, lịch sử không sửa),
  GATE-003 (ruff + RUF100 + mọi `type: ignore` có lý do), GATE-006/008, DOC-001/005, DEP-003, ERR-004, SEC-002, REPO-013,
  PRF-CLI-001/003/004/006.
- 20 mục còn lại kiểm bằng test hành vi có sẵn hoặc grep đúng chữ MUST: CFG-001 (URL/IP literal ngoài allowlist),
  CFG-002/003/006/007, DATA-003/009, DEP-006, ERR-002/003/007/008/009/010, GATE-007 (bản khai `main.json`; ruleset
  sống `gh api …/rules/branches/main` khớp ngày 2026-10-26 theo review #279, lệnh kiểm giữ offline), SEC-001/005/006, PRF-CLI-007/010.
- Sửa kèm (GATE-003): gỡ 6 `noqa: E402/E731` chết (ruff chỉ bật E9/F/C901), 9 `type: ignore` thêm lý do. Review #279: siết
  CFG-001 (URL/IP literal), CFG-003 (mọi `XT_*` đọc từ env — Python, hằng `*_ENV`, shell `${XT_…[:+-]` — có trong README), CFG-006/PRF-CLI-010, SEC-002/005/006, DATA-001/006.
- Rủi ro: lệnh kiểm chậm (test chạy lại ~10 s tổng); REPO-005 phụ thuộc tag `v3.20.0` (CI fetch tag). Đường lùi: revert PR.
- Cách làm: phiên chính tự làm; một PR làn chuẩn → reviewer-alt.

## Ngân sách (4 con số)
- Số vòng tối đa: 20 (`--single-session`) · Chi phí: 0 đồng ngoài phiên · Timeout Gate: 1800 giây · Hạn: 3 giờ sau `loop init`

## Điểm dừng bắt buộc (`loop defer`)
- Không có.

## Task
- [x] `T-3521` Gắn `— Kiểm:` cho 37 MUST; sửa chú thích tắt luật (files: BLUEPRINT.md, tests/, .claude/hooks/guard.py) — Gate: `python3 scripts/xt.py blueprint-status BLUEPRINT.md --strict --run && ! python3 scripts/xt.py blueprint-status BLUEPRINT.md --run | grep -q 'unchecked_must'`
- [x] `T-3522` CHANGELOG Unreleased, PROGRESS ≤ 7 900 B (sau: T-3521; files: CHANGELOG.md, PROGRESS.md) — Gate: `grep -q 'D-195' CHANGELOG.md && grep -q 'PLAN-harden-2026-10-26c' PROGRESS.md && test "$(wc -c < PROGRESS.md)" -le 7900 && scripts/dev-task.sh lint`
