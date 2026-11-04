# AUDIT-REPORT — X-Templates · 2026-10-25 (delta `e5ff88c..3ba5828`)

> Commit quét: `main` `3ba5828` (3.22.0) · Phạm vi: delta `e5ff88c..3ba5828` (#246–#253, D-161, D-168…D-172) — nhóm 1 ARCH, 2 SEC,
> 3 CODE, 4 TEST, 8 CI, 9 DOC, 12 XFEAT, 13 HAR, kèm xác minh lại 64 bằng chứng blueprint · Lý do: `release-check` NO-GO, hàng
> `review_debt` (ADR-0031) — guard/xt.py/install.py/workflow đổi sau SHA quét `e5ff88c` · Người quét: 3 subagent `reviewer-alt`
> (Opus, effort max) — cụm A guard (SEC), cụm B `xt.py`/`install.py`/CI/test (CODE, ARCH, TEST, CI, XFEAT), cụm C tài liệu/harness/
> blueprint (DOC, HAR); phiên chính tự đo (gate, pip-audit, zizmor, regex bí mật) · Xác minh đối kháng: phiên chính tái hiện độc
> lập hai 🟠 (xem §4) · `xt.py audit check docs/ops/AUDIT-STATUS.md` → exit 0

## 1. Tóm tắt

| Mức | Mở | Đã sửa | Chấp nhận | Bác bỏ |
|---|---|---|---|---|
| 🔴 | 0 | 0 | 0 | 0 |
| 🟠 | 2 | 0 | 0 | 0 |
| 🟢 | 14 | 0 | 0 | 0 |

16 phát hiện mới: SEC-105/106, HAR-106…110, XFEAT-024/025, CI-018, CODE-023, ARCH-004, DOC-081…083. Hai 🟠: một cách lách luật
reviewer (`LOOP-ORCH-005`) bằng tiền tố bộ chạy `ollama:`, và một cổng tài liệu khẳng định có (`harness-check` kiểm reviewer chỉ
đọc) mà mã không có. Không có 🔴; guard #248 không hồi quy. Hai 🟠 không chặn phát hành bản hiện tại nhưng nên sửa trước khi
dự án đích dựa vào `--clean` để merge.

## 2. Phạm vi và tín hiệu

`audit plan`: 437 file · python 58, js/ts 9, shell 13 · test 52 · CI 10 workflow · REPO KHUNG; nhóm 10 DATA N/A. Quét lại 8 nhóm
(ARCH 3 file đổi, SEC 4, CODE 3, TEST 6, CI 1, DOC 44, XFEAT 3, HAR 12); PERF/A11Y/DEP/CFG không bị chạm (giữ kết quả cũ).
Delta mã: `guard.py` +107 (glob tên lệnh, D-155/D-163…D-167), `xt.py` +202 (thang reviewer D-161, `delegation_rate`),
`install.py` +8 (gộp mệnh đề trùng), `pr-review.yml` +12, test +850. Công cụ thiếu: gitleaks, semgrep, osv-scanner, bandit,
lychee, actionlint, vulture… → các phần đó là `chưa biết:` (regex bí mật trên diff thay một phần cho gitleaks).

## 3. Lệnh đã chạy

| Nhóm | Lệnh | Exit | Kết quả chính |
|---|---|---|---|
| mọi nhóm | `scripts/dev-task.sh gate` (HEAD gộp, mã trùng `main`) | 0 | 4m22s, coverage dòng + nhánh 100 %, mypy strict, ruff C901 |
| SEC | guard `e5ff88c` so HEAD, cùng payload (cụm A) | 0 | 13 ca phá huỷ: 0 hồi quy · 31 ca glob: old=cho phép → new=chặn · 33 ca hợp lệ: 0 chặn oan · DoS fail-closed · 6/6 đột biến bị test bắt |
| CODE/TEST | ruff, mypy --strict, 29 đột biến (cụm B) | 0 | C901 cao nhất 9; 29/29 đột biến không tương đương bị giết |
| DEP | `pip-audit --require-hashes --strict` ×3 khoá (venv ghim) | 0 | 0 lỗ hổng (dev, audit, e2e) |
| CI | `zizmor --offline .github/workflows` | 0 | 14 medium đều `artipacked` (AUD-CI-007, trước 15); 0 high |
| CFG | regex khoá API/PEM/token trên `git diff e5ff88c HEAD` | 0 | sạch |
| HAR | `doctor --json`, `harness-check`, `blueprint-status --strict --run` | 0 / 0 / 1 | doctor 0 lỗi; 2 lệnh Kiểm đỏ do môi trường (AUD-HAR-108) |
| DOC | `validate`, `check-links`, `checks`, đối chiếu 404 lần nhắc `xt.py <lệnh>` với argparse | 0 | 186 file, 2 757 mục; 0 lệnh/cờ lạ |
| HAR | 64 bằng chứng blueprint `Bằng chứng ←` file đổi (cụm C) | — | 53 đúng · 9 lệch (MUST vẫn đạt) · 2 chưa biết |

## 4. Phát hiện chi tiết

### AUD-SEC-105 🟠 Lách `LOOP-ORCH-005` bằng tiền tố bộ chạy `ollama:`
- **Bằng chứng:** đo được — `_model_tail` (#249) chỉ bỏ tiền tố đứng trước `/`; với `ollama:`, `ollama-`, `llamacpp:`, `gpt4all:` regex
  họ khớp vào chính tiền tố (khớp trái nhất) nên họ thành `llama`/`gpt`, máy coi là khác nhà cung cấp (scripts/xt.py `_model_tail`,
  `model_family`, `review_family_config_error`).
- **Tái hiện (phiên chính):** 1. `git init` một dự án tạm. 2. `CLAUDE_PROJECT_DIR=<tạm> python3 -I scripts/xt.py pr reviewed --pr 7
  --head <40 ký tự> --clean --reviewer-model ollama:qwen3-coder --author-model qwen3-coder --no-publish` → **exit 0 "review sạch"**
  (reviewer = người viết). 3. Cùng cặp viết `ollama/qwen3-coder` → exit 2 "cùng họ". 4. `ollama-gemma3:27b` / `gemma3:27b` → exit 0.
  `ci-check` cũng nhận cấu hình kiểu này (`review_family_config_error` → None).
- **Xác minh đối kháng:** cụm B phát hiện; phiên chính tái hiện độc lập cả 4 bước (kết quả như trên). Tên dạng này có dùng thật đến đâu: suy luận.
- **Đề xuất sửa:** tên chứa token họ của ≥ 2 nhà cung cấp → coi mơ hồ và từ chối (fail-closed, cùng tinh thần AUD-HAR-064), hoặc
  tách tiền tố trước `:`/`-` như với `/`; thêm ca vào `test_clean_review_judges_name_tail` · **Gate:** `python3 -m unittest tests.test_merge_review_source -k clean_review_judges_name_tail`

### AUD-HAR-106 🟠 `harness-check` không kiểm reviewer chỉ đọc, dù tài liệu khẳng định có
- **Bằng chứng:** đo được — `LOOP-ORCH-005` (Kiểm) và bảng Cổng của `orchestration-and-subagents.md` ghi `tools:` của `reviewer*`
  không chứa `Edit`/`Write` do `harness-check` kiểm; `_harness_agents` (scripts/xt.py:4666-4677) chỉ kiểm `tools:` có mặt, không `*`,
  không `permissionMode`.
- **Tái hiện:** cụm C chạy đúng regex đó trong bộ nhớ trên `tools: Read, Glob, Grep, Bash, Edit, Write, Agent` (model haiku) →
  không bị coi là lỗi. Script của phiên chính bị guard chặn (HOOK_BYPASS, D-105: nhắc `.claude`) — theo `LOOP-STOP-025` không
  thử đường khác; xác nhận bằng đọc mã (đoạn hàm trên: không có điều kiện nào về `Edit`/`Write`/`Agent`).
- **Xác minh đối kháng:** cụm C phát hiện; phiên chính đọc mã xác nhận (tái hiện bằng script bị chặn — ghi rõ).
- **Đề xuất sửa:** `harness-check`: `reviewer*` chỉ được có `Read/Glob/Grep/Bash`, không agent nào có `Agent`; thêm test; hoặc hạ chữ
  tài liệu nếu chọn không cưỡng chế · **Gate:** `python3 -m unittest discover -s tests -k harness_agents_readonly`

## 5. Kế hoạch sửa theo đợt (tự duyệt — D-173)

| Đợt | Phát hiện | PR dự kiến | Gate của đợt |
|---|---|---|---|
| 1 | AUD-SEC-105, AUD-HAR-106 (🟠) + AUD-SEC-106, AUD-XFEAT-024, AUD-HAR-107 (🟢 rẻ cùng vùng) — mỗi lỗi có test đỏ trước khi sửa | `fix(review): …; cắt 3.22.1` | `scripts/dev-task.sh gate` |
| 2 (sau) | AUD-HAR-110 sinh lại `BLUEPRINT.md` + sửa bằng chứng 9 mục | `docs(blueprint): …` | `xt.py blueprint-status BLUEPRINT.md --strict` |

Trần byte: `scripts/` còn 4 532 B, `.claude/hooks/` còn 917 B — đợt 1 phải gọn (không nới trần, ADR-0043).

## 6. Nợ 🟢 giữ lại

| ID | Chủ | Hạn | Lý do chưa sửa |
|---|---|---|---|
| AUD-CODE-023 (đua ghi `reviews.json`) | phiên chính | 2026-11-08 | cần thiết kế khoá/đọc lại; có từ trước diff, mô phỏng một tiến trình |
| AUD-CI-018 (model mặc định lặp hai chỗ) | phiên chính | 2026-11-08 | sửa workflow cần review ruleset; đợt riêng với test ghim |
| AUD-ARCH-004 (sắp chạm trần byte) | phiên chính | trước lát mã kế | kế hoạch cắt mã/chữ, không nới trần |
| AUD-XFEAT-025 (thang theo họ không theo thế hệ) | chủ repo | 2026-11-08 | giới hạn thiết kế đã ghi ADR-0044, cần quyết định chủ repo |
| AUD-HAR-108/109 (Kiểm đỏ do môi trường; clone nông `boundary`) | phiên chính | 2026-11-08 | gợi ý lệnh, không đổi kết quả fail-closed |
| AUD-HAR-110 (BLUEPRINT.md cũ) | phiên chính | 2026-11-08 | PR sinh lại riêng (diff lớn) |
| AUD-DOC-081/082/083 (AGENTS.md §8, ngày nguồn, Opus@max + skill + ADR-0044) | phiên chính | 2026-11-08 | `AGENTS.md` sát trần 7 168 B; gom khi cắt chữ |
