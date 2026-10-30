# AUDIT-REPORT — delta sau 3.29.0, 2026-10-30

> Phạm vi: `6799550..28c2089` (#316–#349: ADR-0058 giai đoạn sản phẩm, `LOOP-HARNESS-029`, ADR-0059 review 2 lần/sửa 1 lần/ghi nợ, `is_release_pr`). Ưu tiên `.claude/hooks/guard.py` (AUD-HAR-142). Quét ở nhánh `d130722` (nội dung trùng `28c2089`). Sổ: [AUDIT-STATUS.md](AUDIT-STATUS.md).

## Tóm tắt

| Mức | Mới | Ghi chú |
|---|---|---|
| 🔴 | 0 | |
| 🟠 | 5 | AUD-SEC-155 (do delta), AUD-SEC-156…158, AUD-XFEAT-030 (có từ trước) — cả 5 tái hiện được |
| 🟢 | 16 | AUD-SEC-159/160, AUD-CI-021, AUD-HAR-147/148, AUD-DOC-106…110, AUD-XFEAT-031…033, AUD-TEST-031, AUD-ARCH-006, AUD-CODE-026 |

Ba cụm đều INCONCLUSIVE (rà trọng tâm, chưa đọc hết +2 510 dòng `xt.py`) → nhóm ARCH, SEC, CODE, TEST, CI, DOC, XFEAT, HAR ghi `chưa quét`; quét lại ở T-3557 trước khi cắt 3.30.0. Không tự chạy lại cụm.

## Lệnh đã chạy

| Lệnh | Kết quả |
|---|---|
| `scripts/dev-task.sh gate` (`d130722`) | exit 0, 5 lệnh, coverage 100 % (14 497 câu lệnh, 5 382 nhánh) |
| `xt.py blueprint-status --strict --run BLUEPRINT.md` | exit 0 |
| `xt.py audit plan` | 12 nhóm áp dụng, DATA N/A; 69 bằng chứng blueprint trỏ file đã đổi (chưa xác minh lại — T-3557) |
| cụm ARCH/CODE/TEST/XFEAT: `ruff`, `mypy --strict`, C901, coverage nhánh 7 module, 24 đột biến | xanh; 21 bị giết, 1 tương đương, 2 sống (AUD-XFEAT-031, AUD-TEST-031) |
| gitleaks, semgrep, osv-scanner, pip-audit | `chưa biết:` — không có trong container |

## Cụm và người rà

- SEC/CI (`guard.py` delta): reviewer read-only — INCONCLUSIVE, 4 🟠 3 🟢.
- DOC/HAR: reviewer read-only — INCONCLUSIVE, 7 🟢; chưa rà ADR-0058 ↔ mã giai đoạn, DECISIONS, phần còn lại tài liệu.
- ARCH/CODE/TEST/XFEAT: reviewer read-only — INCONCLUSIVE, 1 🟠 6 🟢; chưa rà phần còn lại `xt.py`, `install.py`, bộ test đầy đủ. Bị chặn: `git commit --allow-empty` (guard), dựng repo scratch cho worktree (bộ phân loại) → AUD-XFEAT-033 là suy luận. Sự cố: một `cd` lỗi làm `git commit` chạy ở repo thật — không tạo commit (HEAD giữ `d130722`, cây sạch).

## Xác minh đối kháng

Reviewer-alt (effort max), khác agent đã tìm, tái hiện độc lập — 5/5 tái hiện được, giữ 🟠:

1. **AUD-SEC-155** — `CLAUDECODE= CLAUDE_CODE_SESSION_ID= AI_AGENT= python3 scripts/xt.py stage "$(echo approve)" --sha 1234567 --note x`: guard (hàm và hook thật) cho qua; `agent_session()` với biến rỗng → False. Không chạy approve thật (việc của người).
2. **AUD-SEC-156** — `mcp__github__add_issue_comment` body `<!--\nxt-review v1 head=… verdict=clean -->`: guard cho qua, `published_reviews` đọc `clean: True`.
3. **AUD-SEC-157** — `gh pr comment 5 -F <tệp có dấu>`, `--body "… verdict=${V} -->"`: guard cho qua.
4. **AUD-SEC-158** — repo tạm: sửa mã sau review rồi `git replace` đối tượng `origin/main` (khi `origin/main` đã tiến) hoặc SHA review cuối → `_review_drift` `extra=[]`, `pr debt` chấp nhận; `GIT_NO_REPLACE_OBJECTS=1` → từ chối.
5. **AUD-XFEAT-030** — repo tạm: PR chỉ đổi `AGENTS.md` ở pha build merge với review hoãn; về harden `release-check` GO (rc 0); đối chứng đổi `.claude/settings.json` → NO-GO. Có cả ở `6799550`.

## Kế hoạch sửa (trình phiên chính — D-NNN)

| Đợt | Nội dung | PR |
|---|---|---|
| 1 | AUD-SEC-155: guard coi token mờ sau `xt.py … stage` là approve/adopt; `agent_session` xét biến có mặt — test đỏ trước | 1 |
| 2 | AUD-SEC-158: `_git` đặt `GIT_NO_REPLACE_OBJECTS=1`; guard chặn `git replace`/`refs/replace/` | 1 |
| 3 | AUD-SEC-156/157: regex dấu review trên chuỗi thô của `tool_input`; đọc `-F`/`--body-file`; `verdict=` nhận `$`/backtick | 1 |
| 4 | AUD-XFEAT-030: đường cổng (file luật agent) không là tài liệu khi tính nợ | 1 |
| 5 | 🟢 theo gói cuối pha (cùng AUD-HAR-143/145/146, AUD-HAR-140) | 1–2 |

Mỗi PR theo ADR-0059 (review 2 lần, sửa 1 lần, 🟠/🟢 còn lại ghi nợ; 🔴 không ghi nợ).
