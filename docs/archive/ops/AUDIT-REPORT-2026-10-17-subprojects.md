# AUDIT-REPORT 2026-10-17 (delta #85–#93 + luồng dự án con) — Khung X-Templates

> Quét lại theo diff sau `536584f`, trọng tâm: những gì dự án con nhận khi cài khung (install, hook/guard, mẫu, doctor, feedback).
> SHA quét `main` `11f2770`. Người quét: phiên chính (cổng, công cụ) + 2 subagent `reviewer` (harness/guard; install/mẫu/dự án con).
> Xác minh đối kháng: một `reviewer` thứ ba, model khác, tự dựng dự án giả mới và tái hiện độc lập mọi 🔴/🟠 — không mục nào
> bị bác bỏ hoàn toàn; phần "`gh pr merge --auto` lọt" của AUD-SEC-044 bị bác (bị deny); 3 mục hạ 🟠 → 🟢 (HAR-049/050/051).
> Sổ: `docs/ops/AUDIT-STATUS.md` (ID mới AUD-SEC-044…050, AUD-HAR-049…054, AUD-DOC-041…043). `audit check` exit 0;
> `--strict` chưa vì còn 🔴/🟠 mở và ARCH chưa quét lại.

## Tóm tắt

| Mức | Mới | Ghi chú |
|---|---|---|
| 🔴 | 1 | AUD-SEC-044 — merge PR ngoại lệ cứng không ghim head lọt (trái ADR-0019) |
| 🟠 | 5 | AUD-SEC-045 (merge fail-open khi lỗi), 046 (gỡ hàng rào), 047 (push refspec glob), 048 (huỷ đường khác), 049 (ghi `.env` qua Bash) |
| 🟢 | 10 | SEC-050, HAR-049…054, DOC-041…043 |

Gốc chung của 🔴/🟠: ADR-0018 biến mọi `ask` thành cho chạy; các nhánh guard trước đây "hỏi" cho ca chưa phân loại kỹ
(merge không ghim, lỗi merge-check, sửa hook, biến thể lệnh) nay lọt im lặng. Ở `XT_GUARD_POLICY=strict` phần lớn quay về hỏi.

Phần chạy đúng (đo được): cài vào repo trống và repo có settings/hook/AGENTS.md riêng exit 0; settings gộp giữ quyền/hook/`env`
riêng, JSON hợp lệ; cài lần 2 idempotent; hook không hard-code đường dẫn repo khung cho `xt.py`; SessionStart không crash khi
thiếu PROGRESS.md; mọi lệnh/cờ nhắc trong mẫu AGENTS.md/CLAUDE.md có thật.

## Phạm vi

33 file đổi (+1.608/−249): guard.py, hook, settings, install.py, xt.py, test, ADR-0017…0019, mẫu dự án đích. Quét lại SEC,
CODE, TEST, DEP, CI, DOC, XFEAT, HAR. Không quét lại lượt này: ARCH (còn ở "Quét lại"), PERF (rút gọn), CFG (không đổi).
N/A: A11Y, DATA. Công cụ chạy được lượt này: ruff, mypy, coverage, shellcheck (shellcheck-py), gitleaks 8.28.0, pip-audit 2.9.0,
zizmor 1.14.2, actionlint 1.7.7. Thiếu: semgrep, bandit, osv-scanner, lint-imports, vulture, jscpd, lychee → `chưa biết:` cho phần chúng đo.

## Lệnh đã chạy

| Lệnh | Exit | Kết quả |
|---|---|---|
| `scripts/dev-task.sh gate` (sau `git fetch --unshallow`) | 0 | 538 test OK; coverage dòng + nhánh 100% (4301 dòng, 1818 nhánh); mypy --strict, ruff, shellcheck xanh |
| `xt.py progress-check` trước / sau unshallow | 1 / 0 | đỏ chỉ do clone nông |
| `xt.py doctor --json` | 0 | `ok: true`; cảnh báo gate-tools (trước khi cài) và SHA PROGRESS (clone nông) |
| `gitleaks git . --redact` | 0 | 194 commit, không rò rỉ |
| `pip-audit --require-hashes --strict -r requirements-{dev,audit}.txt` | 0 | không lỗ hổng |
| `zizmor --offline .github/workflows` | 13 | 7 `artipacked` medium — trùng AUD-CI-007 |
| `actionlint` | 0 | sạch |
| `install.py` vào 3 dự án giả + hook bằng payload JSON (scratchpad) | — | tái hiện các phát hiện dưới |

## Chi tiết 🔴/🟠 (tái hiện)

Dự án đích giả: copy `.claude/` + stub `.xtemplates/scripts/xt.py` cho `merge-check` trả
`{"verdict":"merge","hard":["auth"],"head":"abc123","repo":"o/r","autonomy":3}`; gọi hook PreToolUse bằng JSON qua stdin,
`CLAUDE_PROJECT_DIR` trỏ dự án giả. "Lọt" = hook không in quyết định nào → `allow: Bash` cho chạy.

- **AUD-SEC-044 🔴** Lọt: `gh pr merge 5 --squash`, `gh api -X PUT repos/o/r/pulls/5/merge`, `gh api graphql … mergePullRequest`,
  MCP `merge_pull_request` không `expectedHeadSha`. Deny: `--auto`, `--match-head-commit abc123`, MCP có ghim, `enable_pr_auto_merge`.
  Nguyên nhân: `_merge_verdict` chỉ chạy khi lệnh ghim head; không ghim → `EXTERNAL_ASK` → `apply_policy` bỏ. 🔴 vì là lệnh
  tự nhiên, không cần né, vi phạm thẳng ngoại lệ cứng (LOOP-STOP-005); ruleset không đòi approval nên GitHub không đỡ.
- **AUD-SEC-045 🟠** Stub exit 3 (giả lỗi mạng) → cả ca ghim head và `--auto` đều lọt. Cùng đường: guard.py chết hoặc thiếu
  python3 (`merge_like && ask_strict`). Hạ 🟠 vì cần lỗi đi kèm.
- **AUD-SEC-046 🟠** Write `.claude/settings.local.json` `{"disableAllHooks":true}`, Write `.claude/hooks/guard.py`,
  `rm`/`mv .claude/hooks/guard.py` → lọt. Sau khi thiếu guard.py: `git push origin main`, `gh repo delete o/r --yes`, `rm -rf ~`
  → lọt (`ask_strict` mặc định exit 0). Hồi quy AUD-SEC-019; trái ADR-0018 ("tắt/bỏ qua hook" thuộc nhóm chặn).
- **AUD-SEC-047 🟠** Từ nhánh `feat`: `git push origin 'refs/heads/*:refs/heads/*'`, `git push origin :`,
  `git -c push.default=matching push origin` → hook lọt; chạy git thật vào bare repo local → `main` remote đổi cả 3 ca.
  Ruleset `main` trên GitHub vẫn đỡ (vì vậy 🟠).
- **AUD-SEC-048 🟠** Lọt: `gh api -X DELETE repos/o/r`, `gh api --method DELETE repos/o/r`, `terraform apply -destroy`, `pulumi down`.
- **AUD-SEC-049 🟠** Lọt: `curl -o .env …`, `curl -O http://x/.env`, `wget -O .env`, `git checkout other -- .env`,
  `git restore --source=other .env`, `python3 -c "open('.env','w')…"`. `cp`/`tee`/`sed -i` bị deny.

## Kế hoạch sửa theo đợt (chờ duyệt)

| Đợt | Phát hiện | PR dự kiến | Gate |
|---|---|---|---|
| 1 | SEC-044, 045 (+ DOC-043 phần ADR-0019) | `fix(guard): mọi lệnh merge qua merge-check, hard hoặc lỗi → deny` — test đỏ trước | `python3 -m unittest discover -s tests -k guard_hard_merge` rồi `scripts/dev-task.sh gate` |
| 2 | SEC-046 (+ DOC-043 phần comment) | `fix(guard): chặn gỡ/sửa hook và disableAllHooks; thiếu guard.py → deny` | `-k guard_hook_tamper_denied` + gate |
| 3 | SEC-047, 048, 049, 050 | `fix(guard): push refspec glob, huỷ qua gh api/apply -destroy, ghi .env qua curl/git/interp` | `-k guard_push_glob_refspec` … + gate |
| 4 | HAR-049…053, DOC-041, 042 | `fix(install): dev-task.sh ưu tiên .xtemplates, doctor error khi hook chưa gộp, feedback aggregate nhận gốc repo, mẫu dự án đích` | test install/doctor/feedback + gate |
| — | HAR-054 | ghi chú: `redact` che đường dẫn home — gom vào đợt 4 nếu nhỏ, không thì nợ có chủ | — |

Lưu ý: đợt 1–2 sửa `.claude/hooks/` (cấu hình hook) — theo AGENTS.md §5 là điểm dừng cần người duyệt.

## Nợ 🟢 giữ lại

Các 🟢 mới gom vào đợt 3–4; chủ/hạn gán khi chuyển `chấp nhận`. Nợ cũ không đổi: AUD-CI-006/007/009, AUD-SEC-043, AUD-HAR-036/041, AUD-SEC-026.
