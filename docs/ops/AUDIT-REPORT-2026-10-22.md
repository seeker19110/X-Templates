# AUDIT-REPORT — X-Templates · 2026-10-22 (delta sau #186)

> Commit quét: `main` `1139662` (3.15.5) · Phạm vi: delta `0afa30d..1139662` (#187…#226 — 94 file mã/cấu hình, +15k
> dòng: app cục bộ `xt.py app` + `scripts/xt_app`, pha build/harden ADR-0040…0042, CI mẫu ADR-0039, merge ghim head
> ADR-0036, installer 3.15.x) cho nhóm 1–5, 7–9, 11–13; nhóm 6 A11Y quét lần đầu (N/A → áp dụng: `scripts/app`); 64 bằng
> chứng blueprint `stale_evidence` · Lý do: `release-check` @ `e7a717b` NO-GO, hàng `review_debt` (88 file đổi sau SHA
> quét, ADR-0031) và `audit` (nhóm 6) — PLAN-3.16-audit-delta (D-139) · Người quét: 3 subagent `reviewer` (Sonnet) song
> song theo cụm {SEC, CFG, DEP, CI} · {ARCH, CODE, TEST, PERF, XFEAT} · {DOC, HAR, A11Y}, read-only; phiên chính chạy
> pip-audit, zizmor, gitleaks · Xác minh đối kháng: phiên chính (Opus, khác họ người quét) tái hiện cả 4 🟠 (D-140) ·
> `xt.py audit check docs/ops/AUDIT-STATUS.md` → exit 0

## 1. Tóm tắt

| Mức | Mở | Đã sửa | Chấp nhận | Bác bỏ |
|---|---|---|---|---|
| 🔴 | 0 | 0 | 0 | 0 |
| 🟠 | 1 | 0 | 0 | 0 |
| 🟢 | 23 | 0 | 0 | 0 |

24 phát hiện mới: SEC-103/104, CI-017, HAR-101…105, DOC-076…080, A11Y-001…003, ARCH-003, CODE-020…022, TEST-020,
PERF-002, XFEAT-022/023. Một 🟠 (AUD-SEC-103: `POST /api/blueprint` ghi đè `.md` bất kỳ) chặn `audit check --strict` —
sửa ở đợt 1. Không có 🔴; guard pha build (ADR-0040) chỉ nới đúng danh sách ADR, không có lỗ mới.

## 2. Phạm vi và tín hiệu

`audit plan`: python 55, js/ts 9, shell 13 · 49 file test · UI 2 · CI 9 workflow · REPO KHUNG. Nhóm 10 DATA N/A (không
CSDL). Công cụ thiếu và đã bù: pip-audit, zizmor (venv tạm của phiên), gitleaks 8.28.0 (bản phát hành chính chủ, checksum
khớp). Còn thiếu (→ `chưa biết`): semgrep, osv-scanner, bandit, lint-imports, vulture, k6/lighthouse, trình đọc màn hình.

## 3. Lệnh đã chạy

| Nhóm | Lệnh | Exit | Kết quả chính |
|---|---|---|---|
| SEC | `gitleaks git --log-opts=--all --redact .` | 0 | 451 commit, 0 rò rỉ |
| SEC | `xt.py app --port 0 --no-open` + curl (Host/Origin/token/path) | 0 | 421/403/401/404 đúng; POST ghi đè `.md` → AUD-SEC-103 |
| SEC | ~85 lệnh harden + ~55 lệnh build qua `bash_decision`/`apply_policy` | 0 | không lỗ mới; pha build chỉ nới đúng ADR-0040 |
| DEP | `pip-audit --require-hashes --strict --disable-pip -r requirements-{dev,audit,e2e}.txt` | 0 | 0 lỗ hổng |
| CI | `zizmor --offline` (1.31.1) workflows + mẫu CI | 0 | 0 high; 15 medium `artipacked` (AUD-CI-007) |
| CODE | `ruff check --select C901 scripts`; `mypy --strict` xt.py, install.py, xt_app, guard.py | 0 | xanh |
| TEST | `scripts/dev-task.sh gate` | 0 | xanh, coverage 100 %, 334 s real |
| TEST | `xt.py autonomy-bench` | 0 | 460 ca, 0 false-green |
| A11Y | `python3 -m unittest discover -s tests_e2e` (`XT_E2E_CHROMIUM`) | 0 | 8 test; quét bổ sung 28 lượt → 0 vi phạm |
| HAR | `doctor --json`; `blueprint-status --strict --run`; `install.py --plan --with-github` | 0 | 0 lỗi; 64 bằng chứng: 52 đúng · 9 lệch · 3 sai |
| DOC | `xt.py checks`; `check-links.py` | 0 | xanh |

## 4. Phát hiện chi tiết

### AUD-SEC-103 🟠 `POST /api/blueprint` ghi đè file `.md` bất kỳ trong dự án
- **Bằng chứng:** đo được — scripts/xt_app/api_compose.py `_out_path` chỉ chặn đường tuyệt đối, `..`, thành phần ẩn,
  symlink, thư mục; không kiểm đích có phải blueprint. ADR-0038 §2: "ngoại lệ duy nhất: ghi `BLUEPRINT.md`".
- **Tái hiện:** 1. dự án tạm có `README.md` nội dung người dùng; 2. `make_server(...)`, POST `/api/blueprint`
  `{"profile":"cli-tool","scale":"S","out":"README.md"}` kèm token → 200 `written: [README.md, README-BACKLOG.md]`;
  3. README.md thành front-matter `kind: blueprint`. `out=docs/notes.md` cũng 200.
- **Xác minh đối kháng:** hai người quét (cụm SEC và cụm ARCH) tìm độc lập; phiên chính chạy lại → tái hiện được.
- **Đề xuất sửa:** chỉ ghi khi đích chưa tồn tại hoặc front-matter đích có `kind: blueprint`; ngược lại 400, file nguyên.
  **Gate:** `python3 -m unittest tests.test_app_compose -k overwrite`

### Hạ mức khi xác minh (D-140)
- **AUD-PERF-002** (🟠 → 🟢): `xt.py app --smoke` chạm GitHub và có thể `TimeoutError` — lệnh chỉ chạy tay ("kiểm bản
  cài", README), không ở CI/cổng; lỗi gây đỏ giả, không xanh giả.
- **AUD-XFEAT-022** (🟠 → 🟢): `floor` đọc pha ở cây làm việc, `merge-check`/guard đọc cả nhánh đích — chủ ý ADR-0041;
  PR tự đổi sang build vẫn qua review vì `merge-check` đọc nhánh đích và `xt.yaml` thuộc `merge_risk_paths`. Muốn đồng
  nhất thì cần ADR mới (đổi hành vi CI của dự án pha build).

## 5. Kế hoạch sửa theo đợt (tự duyệt — D-139/D-140)

| Đợt | Phát hiện | PR dự kiến | Gate của đợt |
|---|---|---|---|
| 1 | AUD-SEC-103 🟠; AUD-HAR-101…103 (bằng chứng sai); AUD-DOC-080 | `fix(app): /api/blueprint chỉ ghi blueprint; bằng chứng blueprint` | `python3 -m unittest tests.test_app_compose -k overwrite && python3 -m unittest tests.test_ci_shard -k test_weights` |

## 6. Nợ 🟢 giữ lại

Các 🟢 còn lại giữ `mở` trong sổ (tài liệu/chỉ mục ADR, bằng chứng lệch, a11y tinh chỉnh, lặp mã `xt_app`, hiệu năng app
và cổng) — làm theo lô ở lần dọn nợ kế; không cái nào chặn `audit check --strict`.
