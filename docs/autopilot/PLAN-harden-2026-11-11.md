# PLAN-harden-2026-11-11.md — harden sau audit delta `454d146..7ca87a6`

> Lập 2026-11-11 theo `/complete` (chủ dự án: "audit và hoàn thiện, tối ưu dự án"). Duyệt: D-416 (phiên chính tự duyệt,
> ADR-0008). Nguồn: [audit delta 2026-11-11](../ops/AUDIT-REPORT-2026-11-11-delta.md) + `release-check` lần 1 ở
> `7ca87a6` (NO-GO: `audit`, `review_debt`; chờ người: `go_no_go`). Mỗi lát một PR ≤ 150 dòng, bug có test đỏ trước khi
> sửa; diff chạm guard/bảo mật: reviewer đối kháng rà trước khi mở PR.
>
> **Cú pháp bắt buộc cho máy:** mỗi task một dòng `- [ ] \`T-NNNN\` <việc> — Gate: \`<lệnh>\``.

## Tóm tắt (cổng duyệt)
- `release-check` lần 1 (`7ca87a6`, đủ lịch sử + tag): NO-GO — `audit` (`--strict` 72 lỗi: 4 🔴 + 16 🟠 mở có từ trước,
  nợ review) và `review_debt` (2 file); `blueprint` PASS (68 lệnh kiểm xanh); `go_no_go` chờ người ký.
- Audit delta: 3 🔴 mới — AUD-SEC-614 (hồi quy #488: `--end-of-options` lách luật push), AUD-SEC-615 (lách GO_SIGN bằng
  mồi markdown), AUD-SEC-616 (`install.py --pack` ghi xuyên symlink ra ngoài dự án); 5 🟠 — AUD-HAR-377, AUD-SEC-541
  (nâng mức), AUD-CODE-064, AUD-DEP-021, AUD-DATA-011; 🟢 ghi sổ. Cụm TEST INCONCLUSIVE, cụm DOC/HAR rỗng → 3 nhóm
  `chưa quét`, quét lại ở Lát 5.
- 🔴 có từ trước (guard): AUD-SEC-606, 609, 610, 611 — Lát 3; 609/606 theo bài học D-415 (ca không đọc chắc → BUDGET,
  không thêm cách đọc mới).
- Tối ưu có số (đo ở `7ca87a6`): `check-links` −60 %, `doctor` −52 %, `audit plan` −75 % — Lát 4. Cache bytecode cho
  guard/xt.py (−150…200 ms mỗi lệnh) ngược AUD-SEC-074 → không làm ở đây, cần ADR (T-3709, hạn 2027-01-21).
- Ngoài phạm vi đợt này (ghi nợ, `--strict` còn đỏ tới khi trả): 🟠 guard có từ trước AUD-SEC-544/545/554/588/591…593/
  600/604/607/608/612, AUD-HAR-369/371, AUD-DOC-273/274 → PLAN kế; cắt 3.34.0 sau khi `release-check` GO.

## Ngân sách (4 con số)
- Số vòng tối đa: bỏ trống · Chi phí: 0 đồng ngoài phiên · Timeout Gate: 1200 giây · Hạn: 24 giờ

## Điểm dừng bắt buộc về hành động
- Ký GO-NO-GO §5, bật `release_signoff: agent`, quyết "Khi chạy thật": việc người.

## Task

### Lát 1 — 🔴 mới
- [x] `T-3714` 🔴 AUD-SEC-614 guard: `--end-of-options` không còn làm `-h` thành miễn trừ trợ giúp của `git push` (topo: review) — Gate: `python3 -m unittest tests.test_hooks`
- [x] `T-3715` 🔴 AUD-SEC-615 + AUD-TEST-100 guard: dòng ký GO_SIGN guard thấy ⊇ xt thấy (chú thích HTML, khối rào) (topo: review) — Gate: `python3 -m unittest tests.test_guard_go_no_go`
- [x] `T-3716` 🔴 AUD-SEC-616 install.py: `.xtemplates-new` là symlink → `skipped-symlink` (topo: review) — Gate: `python3 -m unittest tests.test_install_pack`

### Lát 2 — 🟠 mới
- [x] `T-3717` 🟠 AUD-HAR-377 xt.py: `release-sign` từ chối, hàng `verify` không PASS khi vòng `blocked` (topo: review) — Gate: `python3 -m unittest tests.test_release_signoff tests.test_release_contract`
- [ ] `T-3718` 🟠 AUD-SEC-541 xt.py: `loop decide-prod` trong phiên agent → exit 2 (topo: review) — Gate: `python3 -m unittest tests.test_xt_cli tests.test_release_contract`
- [x] `T-3719` 🟠 AUD-CODE-064 gói web-api-ts: `build.ts` cho tar ghi thẳng file, digest không đổi — Gate: `python3 -m unittest tests.test_packs`
- [ ] `T-3720` 🟠 AUD-DEP-021 CI: quét lockfile npm của gói theo PR + lịch, khối npm ở dependabot — Gate: `python3 scripts/xt.py ci-check`

### Lát 3 — 🔴 guard có từ trước
- [ ] `T-3721` 🔴 AUD-SEC-610 guard: dấu tách dính dấu chuyển hướng vẫn tách lệnh (topo: review) — Gate: `python3 -m unittest tests.test_hooks tests.test_guard_fuzz`
- [ ] `T-3722` 🔴 AUD-SEC-611 guard: quét thân hàm shell (topo: review) — Gate: `python3 -m unittest tests.test_hooks tests.test_guard_fuzz`
- [ ] `T-3723` 🔴 AUD-SEC-606 guard: bỏ thoát kiểu bash trong nháy kép trước khi quét chuỗi lồng (sau: T-3721, T-3722; topo: review) — Gate: `python3 -m unittest tests.test_hooks tests.test_guard_fuzz`
- [ ] `T-3724` 🔴 AUD-SEC-609 guard: lệnh có luật mà đối số chứa thay lệnh/thay tiến trình không đọc chắc → BUDGET (sau: T-3723; topo: review) — Gate: `python3 -m unittest tests.test_hooks tests.test_guard_fuzz`

### Lát 4 — tối ưu có số
- [x] `T-3725` AUD-PERF-027 `check-links.py`: `mask_code_spans`/`table_cells` nhảy bằng regex, output y hệt — Gate: `python3 -m unittest tests.test_check_links`
- [ ] `T-3726` AUD-PERF-028/029/030 xt.py: `doctor` nạp guard một lần, `audit plan` blame một lần, `same_command` theo khoá — Gate: `python3 -m unittest tests.test_doctor tests.test_xt`

### Lát 5 — nợ còn lại của đợt và quét lại
- [ ] `T-3727` 🟠 AUD-DATA-011 gói: test quét `CREATE INDEX` trên bảng có sẵn phải CONCURRENTLY (0005 vào danh sách đã phát hành) + hướng dẫn migration không transaction (sau: T-3719) — Gate: `python3 -m unittest tests.test_packs`
- [ ] `T-3728` 🟢 AUD-XFEAT-048 skill autopilot nhắc `stage-approve`; AUD-PERF-031 sửa số ở `_lib.sh` — Gate: `scripts/dev-task.sh gate-fast`
- [ ] `T-3730` 🔴 AUD-SEC-619 install.py: thư mục cha là symlink trên đường ghi harness/`.github`/adapter không ghi ra ngoài dự án (D-NNN chọn từ chối hay `under_symlink`; topo: review) — Gate: `python3 -m unittest tests.test_install`
- [ ] `T-3736` 🟠 AUD-HAR-378 xt.py: lời báo vòng bị chặn chọn lối ra theo ca (`_loop_exit`/`_blocked_exit`) — Gate: `python3 -m unittest tests.test_release_contract`
- [ ] `T-3737` 🟠 AUD-HAR-379 xt.py: cờ `loop block` theo sang đợt `loop init` mới hoặc `loop init` từ chối (topo: review) — Gate: `python3 -m unittest tests.test_xt_cli tests.test_release_contract`
- [x] `T-3731` 🔴 AUD-SEC-621 guard: chặn plumbing đẩy `git send-pack`/`git http-push` (topo: review) — Gate: `python3 -m unittest tests.test_hooks.GuardRemoteDeleteTest`
- [x] `T-3732` 🟠 AUD-SEC-622 guard: graphql `updateRefs` → REMOTE_DELETE (topo: review) — Gate: `python3 -m unittest tests.test_hooks.GuardRemoteDeleteTest`
- [ ] `T-3733` 🟠 AUD-SEC-623 guard: `gh repo sync --force` → như force-push (topo: review) — Gate: `python3 -m unittest tests.test_hooks -k repo_sync`
- [ ] `T-3734` 🟠 AUD-SEC-624 guard: ghi công AI của gh đọc khoá ở gốc dự án (topo: review) — Gate: `python3 -m unittest tests.test_hooks.GuardAiAttributionTest tests.test_guard_fuzz.GuardFuzzTest`
- [ ] `T-3735` 🟠 AUD-SEC-625 xt.py: khoá agent của `stage approve`/promotion đọc remote tươi, fail-closed (topo: review) — Gate: `python3 -m unittest tests.test_stage_agent_approval tests.test_release_signoff`
- [ ] `T-3738` 🟠 AUD-SEC-626 guard: graphql gỡ bảo vệ nhánh/ruleset/environment → deny như REST (topo: review) — Gate: `python3 -m unittest tests.test_hooks`
- [ ] `T-3739` 🔴 AUD-SEC-628 formatter không chạm `GO-NO-GO*.md` (hoặc guard xét output formatter) (topo: review) — Gate: `python3 -m unittest tests.test_hooks tests.test_guard_go_no_go`
- [ ] `T-3740` 🟠 AUD-SEC-629/630/631 GO_SIGN: NUL ô Tên, khoảng trắng Unicode cuối `subject:`, BOM một chiều (topo: review) — Gate: `python3 -m unittest tests.test_guard_go_no_go`
- [ ] `T-3741` 🔴 AUD-SEC-632…635 guard: đọc lệnh con git chắc (chuyển hướng giữa, `git-<tên>`, autocorrect, tên mờ → BUDGET) (topo: review) — Gate: `python3 -m unittest tests.test_hooks tests.test_guard_fuzz`
- [ ] `T-3743` 🔴 AUD-SEC-644 guard: biến chưa gán dính sau viết tắt không mơ hồ của cờ nguy hiểm (`git push --delet$X`, `--mirro$X`) → BUDGET (topo: review) — Gate: `python3 -m unittest tests.test_hooks tests.test_guard_fuzz`
- [ ] `T-3742` 🟠 AUD-SEC-636 guard: quét lệnh git lồng (`rebase --exec`, `bisect run`, `submodule foreach`, `--receive-pack`/`--upload-pack`) (topo: review) — Gate: `python3 -m unittest tests.test_hooks`
- [ ] `T-3729` Quét lại nhóm TEST, DOC, HAR (`chưa quét`) + sổ `đã sửa` cho các lát trên (sau: T-3724, T-3726) — Gate: `python3 scripts/xt.py audit check docs/ops/AUDIT-STATUS.md`
