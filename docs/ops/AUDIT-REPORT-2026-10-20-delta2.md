# AUDIT-REPORT — X-Templates · 2026-10-20 lần 2 (delta sau #186)

> Commit quét: `main` `0afa30d` · Phạm vi: delta `f36ea90..0afa30d` (3 commit, #184…#186) — nhóm 1 ARCH, 2 SEC, 3 CODE,
> 4 TEST, 8 CI, 9 DOC, 12 XFEAT, 13 HAR, kèm xác minh lại 52 bằng chứng blueprint `stale_evidence` · Lý do: `release-check`
> tại `0afa30d` NO-GO, hàng `review_debt` (ADR-0031) — guard/xt.py/workflow đổi sau SHA quét `f36ea90` · Người quét:
> subagent `reviewer` (Opus) nhóm SEC/CODE của guard; `reviewer-alt` (Sonnet) nhóm ARCH/XFEAT/HAR của xt.py + hook và
> nhóm CI/DOC/TEST/HAR + bằng chứng blueprint · Xác minh đối kháng: `reviewer-alt` (Sonnet, khác họ người quét guard) tái
> hiện cả 8 phát hiện guard, so guard tại `f36ea90` · `xt.py audit check docs/ops/AUDIT-STATUS.md` → exit 0

## 1. Tóm tắt

| Mức | Mở | Đã sửa | Chấp nhận | Bác bỏ |
|---|---|---|---|---|
| 🔴 | 1 | 0 | 0 | 0 |
| 🟠 | 3 | 0 | 0 | 0 |
| 🟢 | 14 | 0 | 3 | 0 |

21 phát hiện mới: SEC-091…098, CODE-019, XFEAT-018/019, ARCH-002, HAR-099/100, TEST-016…018, DOC-072…075.
Hai hồi quy của #186: AUD-SEC-091 (🔴, fail-open toàn dòng lệnh) và AUD-SEC-092 (🟢, thời gian quét bậc hai). Các phát
hiện guard còn lại có sẵn ở `f36ea90` (cùng lệnh, cùng kết quả ở guard cũ và mới). Nhóm 8 CI không có phát hiện mới.

## 2. Phạm vi và tín hiệu

Delta: guard.py +913/−80 dòng (D-105 mặc định chặn script không chỉ đọc, D-106 thư mục không biết, D-107 bộ che chuỗi
đa ngôn ngữ, AUD-SEC-088/089), hook `pre-bash-guard.sh` đọc `commit_gate` bằng `xt.py commit-gate`, `merge-check` đọc
sổ review cục bộ chỉ để chặt hơn (D-104), `LICENSE_REQ_RE` nhận `[extras]`, `release-tag.yml` dùng `XT_RELEASE_TOKEN`,
chú thích zizmor ở `pr-steward.yml`. Nhóm 5 PERF, 7 DEP, 11 CFG không bị chạm (giữ kết quả tại `a4f929c`); 6 A11Y, 10 DATA N/A.

## 3. Lệnh đã chạy

| Nhóm | Lệnh | Exit | Kết quả chính |
|---|---|---|---|
| SEC | `bash_decision` + `apply_policy` guard HEAD cạnh guard `f36ea90` (importlib, dự án thật làm gốc, không chạy lệnh thử) | 0 | AUD-SEC-091…098 |
| SEC | fuzz 4.000 lệnh qua nhánh mới (cd/env/ipython/deno/lua/f-string/NFKC) | 0 | 0 ngoại lệ ngoài SEC-091 |
| SEC | regex bí mật (`ghp_`, `github_pat_`, `AKIA`, `sk-`, khoá riêng…) trên `git diff f36ea90..0afa30d` | 0 | 0 kết quả; gitleaks không có trên máy — lịch sử: chưa biết |
| CODE | `ruff check` (+ `--select C901`), `mypy --strict` cho guard.py, xt.py | 0 | xanh |
| CODE | hook `pre-bash-guard.sh` 10 lần, guard `f36ea90` vs HEAD | 0 | 133 → 142 ms/lần |
| TEST | `python3 -m unittest discover -s tests`; `scripts/dev-task.sh test` | 0 | 1.225 test; coverage dòng + nhánh 100 % |
| TEST | `xt.py autonomy-bench` | 0 | 411 ca, 0 false-green |
| CI | zizmor 1.31.1, actionlint 1.7.12, `xt.py ci-check` | 0 | không high; chỉ AUD-CI-013 cũ |
| DOC | `validate`, `check-links.py`, `progress-check`, `changelog-check`, `license-check` | 0 | xanh |
| HAR | `audit plan --status … --json` (52 `stale_evidence`), đọc từng mục ↔ file | 0 | 52/52 còn đúng |
| HAR | `blueprint-status BLUEPRINT.md --strict --run` (sau `git fetch --tags`) | 0 | BASE-REPO-006 đỏ chỉ do clone nông thiếu tag |

## 4. Phát hiện 🔴/🟠

| ID | Mức | Tóm tắt | Gate |
|---|---|---|---|
| AUD-SEC-091 | 🔴 | Byte `\x01N\x02` có sẵn trong script node/perl/ruby/php trùng dấu che của `_ro_mask` → IndexError → `main()` fail-open cả dòng lệnh (hồi quy #186) | `-k guard_ro_mask_marker` |
| AUD-SEC-093 | 🟠 | Cờ trình thông dịch ghép/dính (`-Ic`, `-c"…"`, `--eval=`, `-nr`, `-e'…'`), `nodejs`, lệnh chạy hộ (`uv run`, `npx`…) → script không được trích | `-k guard_interp_flag_forms` |
| AUD-SEC-094 | 🟠 | Sau `cd`: `$(…)`, backtick, `<(…)`, `script -c`, `flock`, `watch`, `busybox sh`, `su -c` quét với thư mục ban đầu (AUD-SEC-087 chưa đủ) | `-k guard_nested_cwd_runners` |
| AUD-SEC-097 | 🟠 | `~+`/`~-` không được giải → ghi tay `.autopilot/` lọt | `-k guard_tilde_plus_minus` |

Lệnh test đầy đủ: `python3 -m unittest discover -s tests -k <mẫu>`. Bằng chứng và đường tái hiện: từng dòng trong
[`AUDIT-STATUS.md`](AUDIT-STATUS.md).

Mức sau xác minh đối kháng: SEC-093 người quét đề 🔴 → 🟠 (guard là phân tích tĩnh — D-015 — nhưng các dạng cờ này là
cách viết thường gặp, không phải né cố ý); SEC-092 🟠 → 🟢 (hook `onFailure: block`: hết giờ là chặn, không vượt rào);
SEC-095/096 🟠 → 🟢 (phải cố ý dựng thứ tự lệnh / đường dẫn không nguyên văn — cùng loại D-051, AUD-SEC-090).

## 5. Kế hoạch sửa

Lát B của [`PLAN-3.11-audit-delta.md`](../autopilot/PLAN-3.11-audit-delta.md): mỗi bug test tái hiện đỏ trước rồi sửa;
🟢 rẻ cùng file (SEC-092/098, CODE-019, XFEAT-018, TEST-016/017, DOC-072…075, giới hạn SEC-095/096, XFEAT-019, HAR-100)
sửa hoặc ghi giới hạn trong cùng đợt; sau đó quét lại theo diff bản sửa (T-1690) và `release-check` (T-1691).

## 6. Nợ 🟢 giữ lại

| ID | Chủ | Hạn | Lý do chưa sửa |
|---|---|---|---|
| AUD-ARCH-002 | phiên chính | 2027-01-20 | ADR cũ không sửa; D-104 là nhà của quyết định |
| AUD-HAR-099 | phiên chính | 2027-01-20 | Fail-safe (chạy cổng đầy đủ); install.py không tạo symlink |
| AUD-TEST-018 | phiên chính | 2027-01-20 | CI và máy dev có chỗ ghi; skip có in lý do |
