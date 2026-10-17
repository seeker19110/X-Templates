# PLAN.md — Khung X-Templates · sửa audit dự án con (2026-10-17)

> Lập ngày 2026-10-17. Chủ repo gọi `/autopilot` ngay sau `/audit` (báo cáo `docs/ops/AUDIT-REPORT-2026-10-17-subprojects.md`).
> Kế hoạch trước (T-901…T-904) xong ở #84.

## Tóm tắt (cổng duyệt — phiên chính tự duyệt, D-021)
- Blueprint repo khung: không đổi mục; mục tiêu `audit check --strict` exit 0 sau khi sửa 🔴/🟠 (ARCH quét lại cuối).
- Stack: Python ≥ 3.11 stdlib (`guard.py`, `xt.py`, `install.py`), bash hook; không phụ thuộc mới.
- Phạm vi: guard merge ngoại lệ cứng fail-closed (AUD-SEC-044/045); chặn gỡ hàng rào (AUD-SEC-046); push refspec glob,
  huỷ đi đường khác, ghi `.env` qua Bash (AUD-SEC-047…049); dự án con: dev-task.sh ưu tiên `.xtemplates`, doctor lỗi khi
  hook chưa gộp, `feedback aggregate` nhận gốc repo, mẫu AGENTS/PROGRESS, tài liệu lệch (AUD-HAR-049…053, AUD-DOC-041…043).
- Không làm: thay đổi chính sách ADR-0018 (sửa nội dung hook qua Edit vẫn được — ADR-0018 cho phép); AUD-SEC-050
  (entrypoint git trong image, cùng nhóm AUD-SEC-042); AUD-HAR-054 nếu không nhỏ; mục chờ chủ repo cũ (HAR-036/041…).
- Giữ: `--disable-auto` và MCP `disable_pr_auto_merge` KHÔNG bị chặn (LOOP-STOP-005 đòi tắt auto-merge khi chạm `hard`).
- Nhánh: phiên chỉ push một nhánh → mỗi lát một commit trên `claude/blissful-thompson-4een2c`, một PR (D-016).
- Rủi ro: chặn oan merge hợp lệ khi merge-check lỗi mạng → chấp nhận (fail-closed riêng merge, ADR-0019), agent `loop defer`.

## Ngân sách (4 con số)
- Số vòng tối đa: 20 (`max(20, 4 × task)`)
- Chi phí: 0 đồng ngoài phiên (không phụ thuộc mới)
- Timeout mỗi lệnh Gate: 600 giây
- Ngày hết hạn: 6 giờ sau `loop init` (`--hours 6`)

## Điểm dừng bắt buộc (`loop defer`; `loop block` khi mọi việc còn lại phụ thuộc)
- Merge PR nếu `merge-check` trả `hard` (sửa guard bí mật có thể bị coi là bí mật/auth) — người merge
- Force-push, xoá nhánh, đổi quyền/ruleset repo

## Task

- [x] `T-1001` Guard: mọi lệnh merge/bật auto-merge (gh pr merge, gh pr -R … merge, gh api REST/graphql, MCP) kiểm `hard` qua merge-check kể cả không ghim head; merge-check lỗi/guard chết → deny; `--disable-auto`/disable MCP không bị chặn (AUD-SEC-044/045) — Gate: `python3 -m unittest tests.test_hooks`
- [x] `T-1002` Guard: Bash ghi/xoá/dời file hàng rào (`.claude/hooks/*`, `.claude/settings*.json`) → deny; Edit/Write ghi `disableAllHooks` → deny; thiếu guard.py → deny Bash trừ lệnh khôi phục (AUD-SEC-046) — Gate: `python3 -m unittest tests.test_hooks`
- [x] `T-1003` Guard: push refspec glob/`:`/`push.default=matching`/`remote.*.push`; `gh api -X DELETE repos/…`, `terraform|tofu apply -destroy`, `pulumi down`; ghi file bí mật qua `curl -o/-O`, `wget -O`, `git checkout/restore … -- <bí mật>`, interpreter (AUD-SEC-047…049) — Gate: `python3 -m unittest tests.test_hooks`
- [ ] `T-1004` Dự án con: hook ưu tiên `.xtemplates/scripts/dev-task.sh`; doctor `error` khi hook `.xtemplates-new` chưa gộp; `feedback aggregate` nhận gốc repo, thư mục thiếu → exit 2; PROGRESS mẫu qua progress-check; nhãn install lần đầu; mẫu AGENTS/skill gate/CLAUDE.md §; comment hook + ADR-0019 (AUD-HAR-049…053, AUD-DOC-041…043) — Gate: `python3 -m unittest discover -s tests`
- [x] `T-1005` Sổ audit đánh dấu đã sửa, quét lại ARCH, CHANGELOG, PROGRESS, cổng đầy đủ — Gate: `python3 scripts/xt.py audit check docs/ops/AUDIT-STATUS.md && python3 scripts/xt.py progress-check && scripts/dev-task.sh gate`
- [x] `T-1006` Sửa phát hiện review #97: cờ `-R` của gh trước `pr`, cờ giả chỉ cho push, graphql/REST merge viết lệch, `gh api` bí mật/quyền/ruleset, tải vào thư mục hàng rào, `$(…)` trong nháy kép/heredoc, `restore_re`, progress/redact — Gate: `python3 -m unittest discover -s tests`
