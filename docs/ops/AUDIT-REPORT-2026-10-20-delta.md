# AUDIT-REPORT — X-Templates · 2026-10-20 (delta sau #183)

> Commit quét: `main` `f36ea90` · Phạm vi: delta `a4f929c..f36ea90` (12 commit, #172…#183) — nhóm 1 ARCH, 2 SEC, 3 CODE,
> 4 TEST, 8 CI, 9 DOC, 12 XFEAT, 13 HAR, kèm xác minh lại 58 bằng chứng blueprint `stale_evidence` · Người quét: subagent
> `reviewer` (Opus 5.5), song song theo nhóm · Xác minh đối kháng: `reviewer` Sonnet 5.5 (khác họ) tái hiện độc lập mọi
> 🔴/🟠, trừ AUD-SEC-087 (executor tìm ra khi sửa AUD-SEC-085; phiên chính giao review PR)
> `xt.py audit check docs/ops/AUDIT-STATUS.md --strict` → exit 0

## 1. Tóm tắt

| Mức | Mở | Đã sửa | Chấp nhận | Bác bỏ |
|---|---|---|---|---|
| 🔴 | 0 | 1 | 0 | 0 |
| 🟠 | 0 | 8 | 0 | 0 |
| 🟢 | 2 | 15 | 3 | 0 |

29 phát hiện mới: SEC-083…087, CI-014/015, HAR-093…098, DOC-065…071, XFEAT-015…017, TEST-012…015, CODE-018, DEP-005.
Kết luận: không còn 🔴/🟠 mở. Các bản sửa nằm sau SHA quét (`717c05d`…`c054a12`, `7df0d2e`, `b14f855`, `8f9d75b`, `c313f0f`,
`90a0b4a`) nên được review ở PR. AUD-CI-014 còn một bước do chủ repo làm: đặt secret `XT_RELEASE_TOKEN`.

## 2. Phạm vi và tín hiệu

Delta `a4f929c..f36ea90`: CI chạy song song theo job (#179), `license-check`, ADR-0031 (`delivery_phase`) và ADR-0032
(verdict `review`), `commit_gate: fast`, ba hook mới (`task-completed`, `subagent-stop`, `permission-request`) và luật
guard mới. Nhóm 5 PERF, 7 DEP, 11 CFG không quét lại (giữ kết quả tại `a4f929c`). Nhóm 6 A11Y và 10 DATA là N/A.

## 3. Lệnh đã chạy

| Nhóm | Lệnh | Exit | Kết quả chính |
|---|---|---|---|
| SEC | `gitleaks git --log-opts=--all --redact`; `gitleaks dir --redact` | 0 | 327 commit và cây làm việc không có rò rỉ |
| SEC | `guard.bash_decision` + `apply_policy` trên dự án giả (so với guard tại `a4f929c`) | 0 | AUD-SEC-083…086 |
| CI | `zizmor --offline .github/workflows …` | 14 | 2 high `dangerous-triggers` (AUD-CI-015), 24 artipacked (AUD-CI-007) |
| CI | `gh run view 39393364573 --log-failed` | 0 | `release-tag` bị từ chối đẩy tag (AUD-CI-014) |
| CODE/TEST | `scripts/dev-task.sh gate` (worktree dưới `/tmp`) | 1 | 1 ca đỏ do môi trường (AUD-TEST-012); coverage dòng + nhánh 100 % |
| DOC | `xt.py validate`, `check-links.py`, `progress-check`, `changelog-check`, `ci-check`, `license-check` | 0 | xanh |
| HAR | `xt.py blueprint-status BLUEPRINT.md --strict --run --json` | 1 | MUST mở `BASE-REPO-006` sai thực tế (AUD-HAR-095) |
| HAR | `xt.py audit plan --status docs/ops/AUDIT-STATUS.md --json` | 0 | 58 `stale_evidence`: 37 đúng, 21 sai hoặc lệch chi tiết |

## 4. Phát hiện 🔴/🟠

| ID | Mức | Tóm tắt | Gate | Sửa |
|---|---|---|---|---|
| AUD-SEC-083 | 🔴 | Script trình thông dịch ghi `.git/config`/`.git/hooks/*` không bị xét | `-k guard_interp_git_config` | 64f354f |
| AUD-SEC-084 | 🟠 | Ghi file hàng rào/bí mật/bằng chứng qua biến hoặc bí danh chỉ là ask thường | `-k guard_interp_alias_write` | c054a12 |
| AUD-SEC-085 | 🟠 | Đích ghi của script trình thông dịch bỏ qua `cd` | `-k guard_interp_cwd` | 4d40cfb |
| AUD-SEC-087 | 🟠 | Shell lồng sau `cd` được quét với thư mục ban đầu | `-k guard_nested_cwd` | 8f9d75b |
| AUD-HAR-093 | 🟠 | Merge không ghim head lọt luật `REVIEW_MISSING` | `-k default_policy_review_missing_unpinned` | 717c05d |
| AUD-HAR-094 | 🟠 | `PROGRESS.md` sai về tag và PR đã merge | `xt.py progress-check` + đọc tay | 7df0d2e |
| AUD-HAR-095 | 🟠 | `BASE-REPO-006` ghi thiếu tag, trong khi tag đã có | `git cat-file -t v<VERSION>` = `tag` | #184 |
| AUD-CI-014 | 🟠 | `release-tag.yml` đẩy tag bằng `GITHUB_TOKEN`, bị từ chối khi commit đổi workflow | tay: đặt secret rồi chạy workflow | 7df0d2e |
| AUD-XFEAT-015 | 🟠 | Pha build: review blocking chỉ có ở sổ cục bộ vẫn được `merge-check` trả `merge` | `-k merge_check_local` | b14f855 |

Lệnh test đầy đủ: `python3 -m unittest discover -s tests -k <mẫu>`. Bằng chứng và cách tái hiện chi tiết: từng dòng trong
[`AUDIT-STATUS.md`](AUDIT-STATUS.md).

## 5. Kế hoạch sửa đã làm

| Đợt | Phát hiện | Commit | Gate của đợt |
|---|---|---|---|
| A — guard | SEC-083/084/085, HAR-093; SEC-087 (phát hiện khi sửa) | 717c05d, 64f354f, 4d40cfb, c054a12, 8f9d75b | `scripts/dev-task.sh gate` |
| B — tài liệu/CI | CI-014/015, HAR-094/096/097, DOC-065/066/067/069/070, DEP-005; DOC-068; giới hạn SEC-086, HAR-098 | 7df0d2e, c313f0f, 90a0b4a | `scripts/dev-task.sh gate` |
| C — merge/test | XFEAT-015/016/017, TEST-012/013/014 | b14f855 | `scripts/dev-task.sh gate` |
| — | HAR-095 | #184 | `blueprint-status --strict --run` |

## 6. Nợ 🟢 giữ lại

| ID | Chủ | Hạn | Lý do chưa sửa |
|---|---|---|---|
| AUD-SEC-086 | phiên chính | — (mở) | Giới hạn của phân tích tĩnh; đã ghi ở `harness-files.md`; lớp đỡ là sandbox/egress allowlist |
| AUD-HAR-098 | phiên chính | — (mở) | Hook chỉ nhắc, chặn một lần; đã ghi giới hạn; Gate vẫn chạy lại bằng `loop record` |
| AUD-DOC-071 | phiên chính | 2027-01-20 | Quy ước "§N thay bởi ADR-X" trên dòng Trạng thái của ADR cũ |
| AUD-TEST-015 | phiên chính | 2027-01-20 | Ngưỡng thiếu trọng số 15 % theo D-102 |
| AUD-CODE-018 | phiên chính | 2027-01-20 | Python nhúng trong hook, đã có test hành vi |
