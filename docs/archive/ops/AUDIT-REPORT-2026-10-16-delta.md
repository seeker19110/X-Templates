# AUDIT-REPORT 2026-10-16 (delta #58–#66) — Khung X-Templates

> Quét lại theo diff sau các đợt sửa của `docs/ops/AUDIT-REPORT-2026-10-16.md`. SHA quét `main` `541e81f` (từ `58b8c8b`).
> Sổ: `docs/ops/AUDIT-STATUS.md` (ID mới AUD-SEC-028…032, AUD-CFG-006…008, AUD-CODE-007…010, AUD-TEST-006, AUD-HAR-040…045, AUD-DOC-031…037).

## Tóm tắt

| Mức | Mới | Ghi chú |
|---|---|---|
| 🔴 | 0 | 2 🔴 do người tìm báo (shell lồng, `gh api --input`) bị xác minh đối kháng hạ thành 🟠 |
| 🟠 | 4 | AUD-SEC-028, AUD-SEC-029, AUD-CFG-006, AUD-HAR-042 |
| 🟢 | 23 | 2 mục hạ thành `suy luận:` (AUD-SEC-030, AUD-HAR-041) |

Không thấy hồi quy AUD-SEC-001…027, AUD-HAR-001…039, AUD-DOC-001…030 trên các ca đã chạy.

## Phạm vi (`xt.py audit plan`)

37 file đổi (+1.915/−172). Quét lại 7 nhóm: ARCH, SEC, CODE, TEST, DOC, XFEAT, HAR. Không quét lại: PERF (rút gọn), DEP, CI, CFG (không có file đổi — riêng `redact` trong `xt.py` được xét ở CODE, ghi vào CFG). N/A: A11Y, DATA.
63 bằng chứng blueprint bị cờ "trỏ file đã đổi" — đã kiểm cả 63 (AUD-HAR-044/045).

## Lệnh đã chạy (phiên chính)

| Lệnh | Exit | Kết quả |
|---|---|---|
| `scripts/dev-task.sh gate` | 0 | 473 test OK; coverage dòng + nhánh 100% (3496 dòng, 1466 nhánh); mypy --strict, ruff, shellcheck, validate, link, progress/changelog/ci-check xanh |
| `python3 scripts/xt.py doctor --json` | 0 | 0 lỗi |
| `python3 scripts/xt.py blueprint-status BLUEPRINT.md` | 0 | MUST 62 đạt · 8 miễn · 0 chưa |
| `bandit -r scripts .claude/hooks` | 1 | chỉ Low: B603×8, B607×5, B404×3, B105×1 (báo nhầm: regex `SECRET_WORDS`) |
| `vulture scripts .claude/hooks --min-confidence 60` | 0 | 3 báo nhầm thuộc tính shlex (guard.py:302-304) |
| `git fetch --unshallow` + `gitleaks 8.28.0 git --log-opts=--all` | 0 | 182 commit, không lộ bí mật — lần đầu quét được toàn lịch sử (ghi vào AUD-CI-006) |

Subagent read-only: 3 người tìm (SEC/ARCH/XFEAT · CODE/TEST · DOC/HAR) + 1 người xác minh đối kháng (model khác), tái hiện độc lập từng 🔴/🟠.

## Chi tiết 🟠

### AUD-SEC-028 — shell lồng lọt guard
Tái hiện (`python3 -c 'import sys; sys.path.insert(0,".claude/hooks"); import guard; print(guard.bash_decision(CMD, …))'` hoặc payload vào `pre-bash-guard.sh`):
1. `bash <<< 'git reset --hard HEAD'` → không quyết định (bash thật chạy lệnh).
2. `bash -c -- 'git push --force origin main'`, `bash -c -e 'gh pr merge 7 --admin'` → `_shell_script_arg` lấy `--`/`-e` làm script.
3. `bash - <<'E' … E`, `bash /dev/stdin <<'E' … E` → coi là chạy file.
4. `printf '%s\n' 'rm -rf ~' | sh`, `echo '…' | tee /dev/null | bash` → nguồn ống chỉ nhận echo/printf liền trước, printf ghép chuỗi định dạng.
Đối chứng: `echo 'git reset --hard' | bash`, `bash -c '…'` → deny. Hạ 🔴 → 🟠: guard là lớp phòng vệ chiều sâu, agent phải chủ động bọc lệnh.

### AUD-SEC-029 — `gh api --input` không bị coi là ghi
gh 2.89.0 với server HTTPS cục bộ: có `--input` → POST. Guard không quyết định cho `gh api repos/{owner}/{repo}/rulesets --input f.json`, `…/merges --input b.json` (merge nhánh không qua `merge-check`), `--input=b.json …/git/refs`, `…/releases --input -`. `_gh_api_writes` chỉ xét `-f`/`-F`; comment cùng file nói "`--input` ngầm là POST". Hạ 🔴 → 🟠: ruleset `main` server-side vẫn chặn push thẳng.

### AUD-CFG-006 — `redact` lộ phần sau khi giá trị trong nháy chứa nháy loại kia
`redact('password: "it\'s a secret phrase"')` → `password: *** a secret phrase"`; chưa đóng nháy cũng lộ. Đường thật: `feedback aggregate` → PR nháp ở repo public (giảm nhẹ: có người duyệt PR nháp, gitleaks).

### AUD-HAR-042 — L3 tự merge cả PR chạm auth/thanh toán/mật mã
`merge_decision` với PR `src/auth/login.py` + `src/payment/charge.py`, nhãn `risk:auth`: L2 → `human`, L3 → `merge`. Trái `LOOP-STOP-005` (MUST: tiền thật, dữ liệu người dùng thật, xác thực/phân quyền, mật mã luôn có người duyệt) và "Ngoại lệ cứng … kể cả diff 1 dòng" (`stop-points-and-escalation.md:122,130`); ADR-0015 chỉ miễn `WF-REVIEW-007`; ruleset `main` 0 approval nên không còn chốt người nào.
Điểm quyết định cho đợt sửa (đề xuất): **giữ ngoại lệ cứng ở L3** — `merge-check` trả `human` khi PR mang nhãn/đường dẫn rủi ro của `LOOP-STOP-005`, các làn chuẩn khác (cổng/CI/harness, > 150 dòng…) vẫn auto-merge theo ADR-0015. Lý do: tiêu chí 1 (cách hiểu chặt hơn với bảo mật/tiền); yêu cầu "mở PR kèm auto-merge" vẫn giữ nguyên với repo khung (không có mã auth/thanh toán). Phương án kia: ghi miễn trừ `LOOP-STOP-005` ở L3 — mất chốt người duy nhất cho tiền/auth ở dự án đích.

## Nợ 🟢 (tóm tắt)

- Guard/hook: AUD-SEC-030 (L3 CLI không so repo, `gh repo set-default`), 031 (nhánh không python so chuỗi con), 032 (NUL → ngoại lệ fail-open), AUD-HAR-040 (hook MCP fail-open khi thiếu guard.py), 041 (matcher MCP hẹp; ruleset đỡ phía server).
- Mã: AUD-CODE-007 (check-run gộp theo tên che check không bắt buộc), 008 (so chuỗi ISO, không có đường thật), 009 (redact bậc hai ca từ dài lặp), 010 (lý do L3 ghi "làn nhanh"); AUD-CFG-007/008 (redact che nhầm `npm_…`, thiếu `pwd`/`pass`); AUD-TEST-006.
- Tài liệu L3 chưa lan hết: AUD-DOC-031…036; AUD-DOC-037 (`updated`); AUD-HAR-043 (PROGRESS lệch).
- Blueprint: AUD-HAR-044 (3 bằng chứng sai, 8 lệch dòng / 63), AUD-HAR-045 (cơ chế cờ ~83% báo nhầm).

## Chưa biết / chưa kiểm

- Claude Code có tự bóc `bash -c` trước khi khớp `permissions.deny` không: chưa biết.
- L3 với PR từ fork / PR không do phiên mở (guard cho bật auto-merge với mọi PR mở, không chồng): chưa tái hiện với GitHub thật.
- Hành vi GitHub tự đổi đích PR chồng khi nhánh đáy bị xoá: chưa xác minh từ nguồn sống.
- `BLUEPRINT.md` của repo khung còn 803 mục SHOULD (ADR-0012: blueprint chỉ MUST) và chữ cũ của vài mục (`LOOP-STOP-002`): chưa đối chiếu.
- PERF: thời gian test đo trong lúc subagent chạy song song (158 s) — không dùng làm số đo.

## Kế hoạch sửa (mỗi đợt ≤ 1 PR, test hồi quy đỏ trước khi sửa)

1. **Đợt A — guard** (🟠 AUD-SEC-028, 029; kèm 🟢 SEC-030 `set-default`, 031, 032, HAR-040): `_shell_script_arg` bỏ cờ sau `-c`, `<<<`/`-`/`/dev/stdin` là stdin, nguồn ống bất kỳ vào shell → hỏi khi không đọc được; `--input` không `-X GET` là ghi; hook MCP fail-closed khi thiếu guard.
2. **Đợt B — L3 giữ ngoại lệ cứng** (🟠 AUD-HAR-042; kèm CODE-010, CODE-007, DOC-031…036, DOC-037): `merge_decision` ở L3 trả `human` cho nhãn/đường dẫn `LOOP-STOP-005`; ADR-0016 + D-NNN; tài liệu L3 thống nhất.
3. **Đợt C — redact** (🟠 AUD-CFG-006; kèm CFG-007, 008, CODE-008, 009, TEST-006).
4. **Đợt D — sổ sách** (🟢 HAR-043, 044): PROGRESS, 11 bằng chứng blueprint. AUD-HAR-045 (đổi cơ chế cờ) để nợ có chủ, cân nhắc ADR riêng.
