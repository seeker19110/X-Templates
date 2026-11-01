# AUDIT-REPORT 2026-11-01 — audit cuối pha (PLAN-upgrade-2026-11-01 + ADR-0062)

> Delta `e09f776..457a69e` (#378–#387). Cấu hình chủ dự án 2026-11-01 "[ON] Audit tổng thể cuối mỗi giai đoạn" (ADR-0062 §5).
> Chế độ: `/audit delta`, gọi từ autopilot → nhánh subagent (3 cụm `reviewer` read-only + 1 xác minh đối kháng model khác).

## 1. Tóm tắt

| Mức | Mới | Ghi chú |
|---|---|---|
| 🔴 | 0 | |
| 🟠 | 6 (AUD-SEC-270, 271, 272; AUD-PERF-004; AUD-CODE-034; AUD-DOC-162) | cả 6 tái hiện được khi xác minh đối kháng |
| 🟢 | 7 (AUD-DOC-163, 164, 165; AUD-XFEAT-043; AUD-SEC-273; AUD-CI-025; AUD-TEST-042) | 2 hạ từ 🟠 khi xác minh (DOC-163, XFEAT-043) |

Nợ review trong đợt (đã ghi trước audit, không đếm lại): AUD-SEC-254…269, AUD-HAR-181…190.

Kết luận: 4 trong 6 🟠 là **hồi quy/thiếu sót của chính đợt này** (#383 guard: SEC-270/271, PERF-004; #387: SEC-272, CODE-034; #385: DOC-162). `release-check` vẫn NO-GO (`audit --strict`: 🔴 mở có từ trước + nợ review + 7 nhóm `chưa quét`).

## 2. Phạm vi và tín hiệu

`audit plan` @ HEAD: quét lại ARCH (4 file), SEC (6), CODE (4), TEST (15), DEP (1), CI (1), DOC (37), XFEAT (4), HAR (10); CFG đi cùng cụm SEC.
`doctor --json`: `ok: true`, 0 phát hiện. `blueprint-status`: MUST 64 đạt · 6 miễn · 0 chưa.

| Cụm | Kết luận | Chưa rà (→ nhóm `chưa quét`) |
|---|---|---|
| SEC/CFG/DEP/CI | xong | hash `platformdirs==4.13.7` trên PyPI (lệnh tra bị guard chặn — `curl … \| python3`); gitleaks/semgrep/actionlint/zizmor/pip-audit không có → `chưa biết:` |
| ARCH/CODE/TEST/PERF | INCONCLUSIVE (hết ngân sách) | `scripts/install.py`; `_pr_debt`/`merge_eligibility`/`plan_waves`/release-check trong `xt.py`; `tests/test_merge.py` (+444) và fixture; vị trí `prompt_assets_scan` |
| DOC/HAR/XFEAT | INCONCLUSIVE (hết ngân sách) | `.claude/hooks/guard.py` (+172) đọc toàn bộ; phần `xt.py` ngoài điểm neo; `scripts/xt_app/api_pr.py`; DECISIONS/PLAN/research/ADR-0045/0060/0061 |

## 3. Lệnh đã chạy

| Lệnh | Exit | Kết quả |
|---|---|---|
| `python3 scripts/xt.py loop verify --all` | 0 | 12 Gate + 68 lệnh kiểm blueprint xanh |
| `python3 scripts/xt.py validate` · `check-links.py` · `doctor --json` | 0 | sạch |
| `python3 -m ruff check --select C901 scripts .claude/hooks` | 0 | sạch |
| `python3 -m unittest -q tests.test_guard_audit1019.ToolExecSitesTest tests.test_guard_audit1019.BashHookSitesTest tests.test_xt_cli.PromptAssetsScanTest` | 0 | 12 test |
| probe cụm/xác minh (`scratchpad/audit-*/`, `scratchpad/verify/`) | — | xem từng mục |

## 4. Chi tiết 🟠

### AUD-SEC-270 — sed `e` còn lọt (bản sửa #383 chưa đủ)
- Tái hiện: `sed '/x/Ie <tải>' f`, `sed '/x/M e <tải>' f`, `sed '\%x%e <tải>' f`, `sed '\,x, e <tải>' f`, `sed -n 'e<tải>' f` → guard `''`; GNU sed 4.9 thật tạo file đánh dấu cả 5.
- Xác minh đối kháng: tái hiện được 5/5. **Gate:** 5 ca thêm vào `ToolExecSitesTest` → deny.

### AUD-SEC-271 — `+=` lọt PS4/BASH_ENV
- Tái hiện: `PS4+='$(<tải>)'; set -x; true`, `BASH_ENV+=f bash -c true` → `''`; bash 5.2 chạy tải. Xác minh: tái hiện được. **Gate:** ca `+=` trong `BashHookSitesTest`.

### AUD-SEC-272 — miễn trừ `settings.json` của scanner quá rộng
- Tái hiện: `vendor/pack/settings.json` chứa token `ghp_…` + câu injection trong `deny`/`ask` → 0 phát hiện; cùng nội dung ở `other.json` → secret + injection. Xác minh: tái hiện được. **Gate:** fixture vendor trong `PromptAssetsScanTest`.

### AUD-PERF-004 — guard chậm gần n³ với `%(`/`q(` lặp
- Tái hiện: `perl -e 'system 1;' + '%('*n`: base 0,00/0,00/0,01 s; head 1,9/15,1/42,6 s (n=100/300/600), quyết định `''` (cho chạy). Hook timeout 600 s, `onFailure: block` — không fail-open nhưng treo. Xác minh: tái hiện được. **Gate:** ca `cpu_budget`.

### AUD-CODE-034 — `--patterns` rỗng tắt luật injection
- Tái hiện: file mẫu rỗng/chỉ dòng trắng → exit 0 "không vi phạm" với câu injection ở `.claude/skills/`. Xác minh: tái hiện được. **Gate:** ca patterns rỗng → lỗi.

### AUD-DOC-162 — tài liệu "pha build không reviewer" trái ADR-0062
- `stop-points-and-escalation.md` (~136, `LOOP-STOP-022` vế 3), `orchestration-and-subagents.md:~50`, `/autopilot` bước 6, mẫu `xt.yaml:~32` (+ `lifecycle.md:43`, `/gate`). Mã: `review_deferrable` trả sai cho `hard`/`hard_waived`/`high_risk`. Xác minh: tái hiện được.

## 5. Kế hoạch sửa (D-NNN ở DECISIONS.md)

- **Đợt 1 (PR guard, rủi ro trung bình — 1 review):** AUD-SEC-270, 271, AUD-PERF-004 (+ nợ AUD-SEC-254 `BASH_ENV` vị trí dữ liệu, AUD-SEC-256 biến thể) — test đỏ trước, luật OR với luật cũ, ca bench.
- **Đợt 2 (PR xt.py):** AUD-SEC-272, AUD-CODE-034, AUD-HAR-181 (hồi quy `pr next` sau rethink), AUD-HAR-182 (`--fixed` đòi test), nợ 🟢 rẻ của scanner (SEC-259/264/266/273) — test đỏ trước.
- **Đợt 3 (PR tài liệu, rủi ro thấp):** AUD-DOC-162, 163, 164, 165, AUD-XFEAT-043, AUD-HAR-185/187/189 (thứ tự acceptance/rollback cần mã → đợt 2).
- Sau đợt 3: audit delta lại các nhóm `chưa quét` (ARCH/CODE/TEST/PERF/DOC/XFEAT/HAR) với ngân sách đủ.
- Nợ 🟢 còn lại: giữ `mở`, trả trước khi cắt 3.30.0.
