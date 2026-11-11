# AUDIT-REPORT — X-Templates · 2026-11-11 (delta)

> Mốc quét `454d146..7ca87a6` trên `main` (TEST từ `c9f62ce`, A11Y từ `6acc573`, DATA từ `80566f7`). Sáu cụm reviewer read-only chạy trong một workflow, mỗi 🔴/🟠 một người xác minh độc lập (`reviewer-alt`, effort cao nhất, không nhận lý luận của người tìm), rồi một lượt đo hiệu năng chạy một mình. Kết quả theo ID ở [sổ audit](AUDIT-STATUS.md); kế hoạch sửa: [PLAN-harden-2026-11-11](../autopilot/PLAN-harden-2026-11-11.md) (D-416).

## 1. Tóm tắt

| Mức | Số | ID | Xác minh đối kháng |
|---|---:|---|---|
| 🔴 | 3 | AUD-SEC-614, AUD-SEC-615, AUD-SEC-616 | 614, 616 tái hiện được (616 nâng 🟠→🔴); 615 chưa xác minh — INCONCLUSIVE |
| 🟠 | 5 | AUD-HAR-377, AUD-SEC-541 (nâng 🟢→🟠), AUD-CODE-064, AUD-DEP-021, AUD-DATA-011 | cả 5 tái hiện được |
| 🟢 | 9 | AUD-SEC-617/618, AUD-XFEAT-048, AUD-TEST-100, AUD-PERF-027…031 | không bắt buộc |

- **AUD-SEC-614** — hồi quy của #488: `git push --force --end-of-options origin feat/other -h` được coi là xin trợ giúp. Git 2.43 đọc `-h` sau `--end-of-options` là refspec, nên force-push, `+refspec`, đẩy thẳng `main` và xoá nhánh từ xa đều lọt. Base `454d146` chặn.
- **AUD-SEC-615** — guard tách §5 của GO-NO-GO trên văn bản thô, `xt.py` đọc sau khi bỏ khối rào và chú thích HTML. Một tiêu đề mồi làm guard thấy §5 rỗng trong khi `release-check` vẫn đếm chữ ký: agent ghi được dòng ký người, hoặc chuyển chữ ký có sẵn sang ứng viên khác. Hai cụm (SEC-guard, TEST) tìm độc lập.
- **AUD-SEC-616** — `install.py --pack` ghi đè file ngoài dự án khi `<file>.xtemplates-new` là symlink (nhánh sớm của `managed_action` không kiểm symlink).

## 2. Phạm vi

`audit plan` ở `7ca87a6`: 653 file, 89 file test, 12 workflow, 13 nhóm áp dụng. Diff mã `454d146..7ca87a6`: 82 file, +16 647 dòng.

| Cụm | Nhóm | Kết luận |
|---|---|---|
| SEC-guard | SEC (guard), HAR (hook) | xong |
| SEC-chuỗi cung ứng | SEC, CFG, DEP, CI | xong |
| Mã Python | ARCH, CODE, XFEAT | xong |
| TEST | TEST | INCONCLUSIVE — chưa rà hết `tests/test_hooks.py` (+1 951 dòng), corpus `guard.json` |
| DOC/HAR | DOC, HAR (quy trình), XFEAT (tài liệu ↔ mã) | agent trả rỗng |
| A11Y/DATA | A11Y, DATA, PERF (UI) | xong |

Mười nhóm lên `7ca87a6`; TEST, DOC, HAR ghi `chưa quét` và quét lại ở T-3729 (không tự chạy lại trong lượt này, `/audit` §3).

## 3. Lệnh đã chạy

| Lệnh | Exit | Kết quả |
|---|---:|---|
| `python3 scripts/xt.py doctor --fix` | 0 | 0 lỗi, 1 cảnh báo (công cụ cổng thiếu — đã cài bằng `dev-task.sh setup`) |
| `python3 scripts/xt.py release-check` | 1 | NO-GO: `audit`, `review_debt` (2 file); `blueprint` PASS sau khi lấy đủ lịch sử + tag (clone nông làm 2 lệnh kiểm đỏ giả) |
| `python3 scripts/xt.py blueprint-status BLUEPRINT.md --strict` | 0 | MUST 64 đạt · 6 miễn · 0 chưa |
| `python3 scripts/xt.py audit check docs/ops/AUDIT-STATUS.md` | 0 | sau khi ghi sổ: 🔴 mở 7 · 🟠 mở 21 |
| `python3 -m unittest discover -s tests` (người đo, một mình) | 0 | 3 160 test, 1 245,8 s tuần tự |
| fuzz guard của cụm SEC-guard: 1 989 ca corpus × 10 vỏ bọc; 42 217 lệnh ngẫu nhiên | 0 | 0 ngoại lệ, 0 hồi quy so với base |

Chưa biết (công cụ không có trên máy): gitleaks, zizmor, actionlint, osv-scanner, pip-audit, E2E trình duyệt (job CI `app-e2e`), vitest của gói (cần Postgres). OSV API cho 108 gói npm của gói web-api-ts: 0 lỗ hổng (2026-11-11).

## 4. Xác minh đối kháng

| ID | Kết luận | Ghi chú |
|---|---|---|
| AUD-SEC-614 | tái hiện được | hook sống cho qua `git push --dry-run --force --end-of-options ../remote.git feat/me -h` → git báo forced update. Biến thể `--mirror` git tự từ chối; biến thể `--delete` là lách luật mới, không phải hồi quy so với base |
| AUD-SEC-615 | chưa xác minh — INCONCLUSIVE | bị chặn: guard chặn 3 probe nạp guard/xt trong tiến trình (HOOK_BYPASS, GO_SIGN, STAGE_APPROVE). Dò tĩnh của người xác minh khớp cả ba đường; test đỏ của T-3715 là bằng chứng chạy |
| AUD-SEC-616 | tái hiện được | file ngoài dự án bị ghi đè, exit 0; vị trí đúng `install.py` `managed_action` |
| AUD-HAR-377 | tái hiện được | `loop block` → scope check PASS, hàng `verify` PASS |
| AUD-SEC-541 | tái hiện được | chuỗi đi trọn chỉ khi dự án bật `release_signoff: agent` (khung đang tắt) → 🟠 |
| AUD-CODE-064 | tái hiện được | `src/big.bin` 1,1 MB → `spawnSync tar ENOBUFS` |
| AUD-DEP-021 | tái hiện được | bằng cấu hình: không workflow/dependabot nào phủ lockfile của gói |
| AUD-DATA-011 | tái hiện được (tĩnh) | hành vi khoá theo tài liệu PostgreSQL, chưa đo trên Postgres |

## 5. Hiệu năng (đo ở `7ca87a6`, 4 CPU, Python 3.13, một mình)

| Phép đo | Trung vị | Điểm nóng |
|---|---:|---|
| Hook guard mỗi lệnh Bash | 206 ms | `compile(guard.py)` 155–175 ms; `main()` 1,7 ms |
| `xt.py --help` | 281 ms | compile `xt.py` 211 ms |
| `xt.py doctor` | 1 440 ms | guard compile 6 lần (0,92 s) |
| `xt.py audit plan` | 3 096 ms | `git blame -L` 73 lần (2,6 s) |
| `xt.py release-check` | 150,6 s | 68 lệnh kiểm tuần tự (98 s, trong đó 11,3 s nạp lại guard); 123 lần `gh api` tuần tự (53 s) |
| `dev-task.sh gate-fast` | 3,18 s | `check-links.py` 1 056 ms, shellcheck 715 ms |

Làm ở đợt này (rủi ro thấp, giữ nguyên hành vi): AUD-PERF-027 (`check-links` 981 → 385 ms ở bản thử), AUD-PERF-028 (`doctor` → ≈ 0,7 s), AUD-PERF-029 (`audit plan` → ≈ 0,6 s), phần `same_command` của AUD-PERF-030. Không làm: cache bytecode cho guard/`xt.py` (−150…200 ms mỗi lời gọi) vì ngược AUD-SEC-074 — cần ADR (T-3709, hạn 2027-01-21); song song `gh api` và dòng `lint` chưa có số đo.

## 6. Kế hoạch sửa

Theo [PLAN-harden-2026-11-11](../autopilot/PLAN-harden-2026-11-11.md): Lát 1 ba 🔴 mới · Lát 2 🟠 mới · Lát 3 bốn 🔴 guard có từ trước (AUD-SEC-606/609/610/611) · Lát 4 tối ưu · Lát 5 nợ còn lại và quét lại ba nhóm. Nợ để PLAN kế (chủ: phiên guard kế, hạn xét 2026-12-31): 🟠 guard có từ trước AUD-SEC-544/545/554/588/591…593/600/604/607/608/612, AUD-HAR-369/371, AUD-DOC-273/274 — `audit check --strict` còn đỏ tới khi trả.
