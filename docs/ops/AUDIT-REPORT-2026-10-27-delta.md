# AUDIT-REPORT — Khung X-Templates · 2026-10-27 (delta)

> Commit quét: `137a0478824d6c842e8ad31b3f61272ea022930f` (`main`, sau #275, #276, #284–#288) · Chế độ: **delta** từ `e8c8d96` (SEC, DEP, CI, DOC, HAR có file đổi) · Quy trình: [`framework/00-method/audit.md`](../../framework/00-method/audit.md)
> Người quét: phiên chính + 2 subagent `reviewer` read-only (SEC/DEP/CI · DOC/HAR), lệnh `/complete` Bước 2 · Xác minh đối kháng: không cần (0 🔴/🟠)
> `python3 scripts/xt.py audit check docs/ops/AUDIT-STATUS.md --strict` → exit 0

## 1. Tóm tắt

| Mức | Mới | Ghi chú |
|---|---|---|
| 🔴 | 0 | — |
| 🟠 | 0 | — |
| 🟢 | 9 | AUD-DEP-006/007/008, AUD-DOC-087…090, AUD-CI-019, AUD-HAR-116; cập nhật số đếm AUD-HAR-105 |

Kết luận: **không chặn phát hành.** Diff gồm bump phụ thuộc/action có hash và ghim SHA, sổ audit, nghiên cứu ba vòng
và ADR-0051 (chưa có code). Bốn 🟢 chữ (DEP-006/007, DOC-087, HAR-116) sửa ngay trong PR này; DOC-088 chấp nhận;
DOC-089 giữ mở (cần tải lại nguồn để đối chiếu).

## 2. Phạm vi (`xt.py audit plan`)

PR trong diff: #284 sổ audit · #276 action (setup-python v7.1.0, codeql-action v4.39.1, claude-code-action v1.0.261) ·
#275 dev-tools (ast-serialize 0.13.1, coverage 7.17.0, ruff 0.17.2, pip 26.2.2, platformdirs 4.13.5, playwright 1.64.1) ·
#285 số bản trong docs + `ignore` pyee major · #287 nghiên cứu ba vòng bản 2 · #288 ADR-0051 · #286 certifi.
Giữ nguyên: ARCH, CODE, TEST, XFEAT (không file mã đổi), PERF/A11Y/CFG (không file trong phạm vi), DATA (N/A).

## 3. Lệnh đã chạy

| Nhóm | Lệnh | Exit | Kết quả chính |
|---|---|---|---|
| tất cả | `scripts/dev-task.sh gate` | 0 | 5 lệnh xanh |
| tất cả | `xt.py blueprint-status BLUEPRINT.md --strict --run` | 0 | 68/68 lệnh Kiểm xanh; MUST 64 đạt, 6 miễn, 0 chưa |
| CI/SEC | `git ls-remote` 3 action | 0 | SHA ghim khớp tag |
| CI | `xt.py ci-check` · `unittest tests.test_ci` | 0 | 10 workflow; 36 test |
| CI/SEC | `zizmor --offline --persona regular --min-severity high .github/workflows` (1.31.1) · đủ mức trên `.github` | 0 · 13 | 0 phát hiện high; đủ mức `.github` 16 medium = base (14 `artipacked`, 2 `dependabot-cooldown` → AUD-CI-019) |
| DEP | `pip download --require-hashes --no-deps` · `pip install --dry-run --require-hashes` (3.11, 3.13), 3 khoá | 0 | hash đủ kể cả bắc cầu |
| DEP | `pip-audit --require-hashes --strict --disable-pip` 3 khoá (bản ghim) | 0 | không lỗ hổng (gồm certifi #286) |
| DEP | `xt.py license-check` | 0 | 9 gói khớp allowlist |
| DOC | `xt.py validate` · `changelog-check` · `progress-check` · `check-links.py` · `unittest tests.test_docs_budget` | 0 | — |
| HAR | `xt.py doctor --json` (không `--fix`) | 0 | 0 phát hiện |

Bị chặn (guard, `curl … \| python3`): tra PyPI JSON — hash/license lấy bằng `pip download` + đọc METADATA cục bộ thay thế;
còn chưa biết: metadata pyee 15.0.0, nội dung nguồn của AUD-DOC-089.

## 4. Phát hiện 🔴/🟠

Không có.

## 5. Kế hoạch

Đợt duy nhất = PR audit này: sửa chữ AUD-DEP-006/007, AUD-DOC-087, AUD-HAR-116 → `đã sửa`. Nợ 🟢 giữ: AUD-DOC-089 (mở),
AUD-DOC-088 (chấp nhận, chủ phiên chính, hạn 2027-01-20), AUD-HAR-105 (mở, đã cập nhật số đếm).
Ngoài diff: `artipacked` ×14 có sẵn từ base (AUD-CI-007); `dependabot-cooldown` ×2 ghi AUD-CI-019. Review #289 (🟠 1, 🟢 4) bổ sung:
`DEPENDENCIES.md` lệch `certifi` sau #286 (AUD-DOC-090, sửa), chữ e2e cũ ở `DEPENDENCIES.md` (gộp AUD-DEP-006),
`license-check --requirements requirements-audit.txt` exit 1 vì `sortedcontainers` khai `Apache 2.0` không SPDX (AUD-DEP-008, có từ trước).
