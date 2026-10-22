# PLAN-3.16-audit-delta.md — Khung X-Templates · audit delta `0afa30d..HEAD` → `release-check` GO

> Lập ngày 2026-10-22. Chủ repo gọi lại `/autopilot` sau PLAN-3.15.5 (done). `release-check` @ `e7a717b` NO-GO còn hai
> blocker máy làm được: `review_debt` (88 file ngoài tài liệu đổi sau SHA quét — ADR-0031) và `audit` (nhóm 6 A11Y ghi N/A
> nhưng `scripts/app` nay có UI). `prod_switch` là việc người (N/A, không chặn). Phiên chính tự duyệt (D-139, ADR-0008).
>
> **Cú pháp bắt buộc cho máy:** mỗi task một dòng `- [ ] \`T-NNNN\` <việc> — Gate: \`<lệnh>\``.

## Tóm tắt (cổng duyệt — phiên chính tự duyệt, D-139)
- Phạm vi: audit delta theo `framework/00-method/audit.md` cho mọi nhóm `audit plan` liệt kê "Quét lại" (1–5, 7–9, 11–13 từ
  `0afa30d`/`a4f929c`) + quét lần đầu nhóm 6 A11Y (`scripts/app`, 2 file UI); 64 bằng chứng blueprint trỏ file đã đổi.
- Cách làm: 3 cụm read-only song song ({SEC, CFG, DEP, CI} · {ARCH, CODE, TEST, PERF, XFEAT} · {DOC, HAR, A11Y}), phiên
  chính tự chạy cổng + công cụ cài được (pip-audit, zizmor, gitleaks nếu tải được); xác minh đối kháng mọi 🔴/🟠 bằng
  reviewer khác họ model; ghi sổ + `AUDIT-REPORT-2026-10-22.md` (commit `docs(audit)` riêng, không sửa mã).
- Sau audit: 🔴/🟠 thành task sửa (thêm vào mục "Sửa" dưới đây, mỗi đợt ≤ 1 PR, test đỏ trước); 🟢 giữ `mở`/`chấp nhận`.
- Không làm: tách `xt.py` (AUD-ARCH-001), 🟢 cần quyết chính sách, việc chờ chủ repo.
- Rủi ro: delta lớn (+15k dòng) → subagent bỏ sót (đỡ: chia cụm theo file, phiên chính tự chạy công cụ); guard chặn oan
  lệnh tái hiện của subagent (đỡ: ghi `chưa biết:` + cần gì, không vòng qua guard).

## Ngân sách (4 con số)
- Số vòng tối đa: `max(40, 8 × task)` (`loop init --single-session` tính)
- Chi phí: 0 đồng ngoài phiên (công cụ audit chỉ cài vào môi trường phiên, không thêm phụ thuộc repo)
- Timeout mỗi lệnh Gate: 1800 giây (`XT_RECORD_TIMEOUT` mặc định)
- Ngày hết hạn: 12 giờ sau `loop init` (`--hours 12`)

## Điểm dừng bắt buộc (`loop defer`; `loop block` khi mọi việc còn lại phụ thuộc)
- Phát hiện cần đổi ruleset sống, secret, quyền repo: chủ repo
- `prod_switch` (GO-NO-GO §5): chữ ký người — ngoài vòng này

## Task

### Lát 1 — Audit delta (sổ + báo cáo)
- [ ] `T-2301` Quét delta 12 nhóm áp dụng + A11Y lần đầu, xác minh đối kháng 🔴/🟠, ghi sổ (SHA quét = HEAD) và `docs/ops/AUDIT-REPORT-2026-10-22.md`; `audit check --strict` chỉ còn đỏ vì 🔴/🟠 mở (nếu có) (files: docs/ops/AUDIT-STATUS.md, docs/ops/AUDIT-REPORT-2026-10-22.md) — Gate: `python3 scripts/xt.py audit check docs/ops/AUDIT-STATUS.md`

### Lát 2 — Hội tụ
- [ ] `T-2309` `audit check --strict` exit 0 và `release-check` GO (trừ `prod_switch` của người) (sau: T-2301; files: docs/ops/AUDIT-STATUS.md, PROGRESS.md) — Gate: `python3 scripts/xt.py audit check docs/ops/AUDIT-STATUS.md --strict && XT_E2E_CHROMIUM="${XT_E2E_CHROMIUM:-}" python3 scripts/xt.py release-check`
