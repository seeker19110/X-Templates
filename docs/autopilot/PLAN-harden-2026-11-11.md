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
- [x] `T-3718` 🟠 AUD-SEC-541 xt.py: `loop decide-prod` trong phiên agent → exit 2 (topo: review) — Gate: `python3 -m unittest tests.test_xt_cli tests.test_release_contract`
- [x] `T-3719` 🟠 AUD-CODE-064 gói web-api-ts: `build.ts` cho tar ghi thẳng file, digest không đổi — Gate: `python3 -m unittest tests.test_packs`
- [x] `T-3720` 🟠 AUD-DEP-021 CI: quét lockfile npm của gói theo PR + lịch, khối npm ở dependabot — Gate: `python3 scripts/xt.py ci-check`

### Lát 3 — 🔴 guard có từ trước
- [x] `T-3721` 🔴 AUD-SEC-610 guard: dấu tách dính dấu chuyển hướng vẫn tách lệnh (topo: review) — Gate: `python3 -m unittest tests.test_hooks tests.test_guard_fuzz`
- [x] `T-3722` 🔴 AUD-SEC-611 guard: quét thân hàm shell (topo: review) — Gate: `python3 -m unittest tests.test_hooks tests.test_guard_fuzz`
- [~] `T-3723` 🔴 AUD-SEC-606 guard: bỏ thoát kiểu bash trong nháy kép trước khi quét chuỗi lồng (sau: T-3721, T-3722; topo: review) — Bỏ: gộp vào T-3766 (ADR-0076, D-430) — Gate: `python3 -m unittest tests.test_hooks tests.test_guard_fuzz`
- [~] `T-3724` 🔴 AUD-SEC-609 guard: lệnh có luật mà đối số chứa thay lệnh/thay tiến trình không đọc chắc → BUDGET (sau: T-3723; topo: review) — Bỏ: gộp vào T-3763 (ADR-0076, D-430) — Gate: `python3 -m unittest tests.test_hooks tests.test_guard_fuzz`
- [~] `T-3748` 🔴 AUD-SEC-656 guard: nhánh `except ValueError` của `tokenize` (nháy không đóng, `\` lẻ cuối) tách `(`, `)`, `<`, `>` như `_unglue` hoặc BUDGET (sau: T-3721; topo: review) — Bỏ: gộp vào T-3761 (ADR-0076, D-430) — Gate: `python3 -m unittest tests.test_hooks tests.test_guard_fuzz`
- [~] `T-3749` 🔴 AUD-SEC-657 guard: chuyển hướng fd có tên `{fd}>file CMD` đứng đầu lệnh không làm `{fd}` thành tên lệnh (sau: T-3721; topo: review) — Bỏ: gộp vào T-3764 (ADR-0076, D-430) — Gate: `python3 -m unittest tests.test_hooks tests.test_guard_fuzz`
- [~] `T-3750` 🔴 AUD-SEC-659 guard: `exec -la x CMD`/`exec -ca x CMD` — cờ gộp của `exec` có `a` ăn đối số (sau: T-3721; topo: review) — Bỏ: gộp vào T-3764 (ADR-0076, D-430) — Gate: `python3 -m unittest tests.test_hooks tests.test_guard_fuzz`
- [~] `T-3751` 🔴 AUD-SEC-660 guard: gán biến sau định nghĩa hàm, trước lời gọi → thân dùng biến không biết giá trị thì BUDGET (sau: T-3722; topo: review) — Bỏ: gộp vào T-3765 (ADR-0076, D-430) — Gate: `python3 -m unittest tests.test_hooks tests.test_guard_fuzz`
- [~] `T-3752` 🔴 AUD-SEC-661 guard: shell trong nhóm/thân hàm đọc stdin của nhóm/lời gọi → BUDGET (sau: T-3722; topo: review) — Bỏ: gộp vào T-3765 (ADR-0076, D-430) — Gate: `python3 -m unittest tests.test_hooks tests.test_guard_fuzz`

### Lát 4 — tối ưu có số
- [x] `T-3725` AUD-PERF-027 `check-links.py`: `mask_code_spans`/`table_cells` nhảy bằng regex, output y hệt — Gate: `python3 -m unittest tests.test_check_links`
- [ ] `T-3726` AUD-PERF-028/029/030 xt.py: `doctor` nạp guard một lần, `audit plan` blame một lần, `same_command` theo khoá — Gate: `python3 -m unittest tests.test_doctor tests.test_xt`

### Lát 5 — nợ còn lại của đợt và quét lại
- [x] `T-3727` 🟠 AUD-DATA-011 gói: test quét `CREATE INDEX` trên bảng có sẵn phải CONCURRENTLY (0005 vào danh sách đã phát hành) + hướng dẫn migration không transaction (sau: T-3719) — Gate: `python3 -m unittest tests.test_packs`
- [ ] `T-3728` 🟢 AUD-XFEAT-048 skill autopilot nhắc `stage-approve`; AUD-PERF-031 sửa số ở `_lib.sh` — Gate: `scripts/dev-task.sh gate-fast`
- [x] `T-3730` 🔴 AUD-SEC-619 install.py: thư mục cha là symlink trên đường ghi harness/`.github`/adapter không ghi ra ngoài dự án (D-NNN chọn từ chối hay `under_symlink`; topo: review) — Gate: `python3 -m unittest tests.test_install`
- [x] `T-3736` 🟠 AUD-HAR-378 xt.py: lời báo vòng bị chặn chọn lối ra theo ca (`_loop_exit`/`_blocked_exit`) — Gate: `python3 -m unittest tests.test_release_contract`
- [x] `T-3737` 🟠 AUD-HAR-379 xt.py: cờ `loop block` theo sang đợt `loop init` mới hoặc `loop init` từ chối (topo: review) — Gate: `python3 -m unittest tests.test_xt_cli tests.test_release_contract`
- [x] `T-3731` 🔴 AUD-SEC-621 guard: chặn plumbing đẩy `git send-pack`/`git http-push` (topo: review) — Gate: `python3 -m unittest tests.test_hooks.GuardRemoteDeleteTest`
- [x] `T-3732` 🟠 AUD-SEC-622 guard: graphql `updateRefs` → REMOTE_DELETE (topo: review) — Gate: `python3 -m unittest tests.test_hooks.GuardRemoteDeleteTest`
- [ ] `T-3733` 🟠 AUD-SEC-623 guard: `gh repo sync --force` → như force-push (topo: review) — Gate: `python3 -m unittest tests.test_hooks -k repo_sync`
- [ ] `T-3734` 🟠 AUD-SEC-624 guard: ghi công AI của gh đọc khoá ở gốc dự án (topo: review) — Gate: `python3 -m unittest tests.test_hooks.GuardAiAttributionTest tests.test_guard_fuzz.GuardFuzzTest`
- [ ] `T-3735` 🟠 AUD-SEC-625 xt.py: khoá agent của `stage approve`/promotion đọc remote tươi, fail-closed (topo: review) — Gate: `python3 -m unittest tests.test_stage_agent_approval tests.test_release_signoff`
- [ ] `T-3738` 🟠 AUD-SEC-626 guard: graphql gỡ bảo vệ nhánh/ruleset/environment → deny như REST (topo: review) — Gate: `python3 -m unittest tests.test_hooks`
- [x] `T-3739` 🔴 AUD-SEC-628 formatter không chạm `GO-NO-GO*.md` (hoặc guard xét output formatter) (topo: review) — Gate: `python3 -m unittest tests.test_hooks tests.test_guard_go_no_go`
- [ ] `T-3740` 🟠 AUD-SEC-629/630/631 GO_SIGN: NUL ô Tên, khoảng trắng Unicode cuối `subject:`, BOM một chiều (topo: review) — Gate: `python3 -m unittest tests.test_guard_go_no_go`
- [~] `T-3741` 🔴 AUD-SEC-632…635 guard: đọc lệnh con git chắc (chuyển hướng giữa, `git-<tên>`, autocorrect, tên mờ → BUDGET) (topo: review) — Bỏ: đã sửa ở #522 (AUD-SEC-632…635 `đã sửa`; họ còn lại theo dõi ở AUD-SEC-680/681/701) — Gate: `python3 -m unittest tests.test_hooks tests.test_guard_fuzz`
- [~] `T-3758` 🔴 AUD-SEC-700 guard: `{fd}>tệp` đứng đầu lệnh không vô hiệu luật (`_strip_prefixes` bỏ cả `{fd}` lẫn chuyển hướng như số fd) (topo: review) — Bỏ: gộp vào T-3764 (ADR-0076, D-430) — Gate: `python3 -m unittest tests.test_hooks tests.test_guard_fuzz`
- [x] `T-3747` 🔴 AUD-SEC-650/651 install.py/xt.py: thư mục git hook (`core.hooksPath` → thư mục là symlink) và sổ giai đoạn (`--stage-init`: `docs`, `.autopilot` là symlink) không ghi ra ngoài dự án (topo: review) — Gate: `python3 -m unittest tests.test_install tests.test_stage`
- [ ] `T-3746` 🔴 AUD-SEC-648/649 guard hoặc `dev-task.sh format`: dòng §5 không ở dạng bảng chuẩn không được thành chữ ký qua formatter cả repo; mẫu `.prettierignore` cho `GO-NO-GO*.md` (topo: review) — Gate: `python3 -m unittest tests.test_hooks tests.test_guard_go_no_go`
- [~] `T-3743` 🔴 AUD-SEC-644 guard: biến chưa gán dính sau viết tắt không mơ hồ của cờ nguy hiểm (`git push --delet$X`, `--mirro$X`) → BUDGET (topo: review) — Bỏ: đã sửa ở #523 (AUD-SEC-644 `đã sửa`; họ còn lọt AUD-SEC-690/710/711 ở T-3762) — Gate: `python3 -m unittest tests.test_hooks tests.test_guard_fuzz`
- [~] `T-3744` 🔴 AUD-SEC-645 guard: CR trần ngoài nháy không tách từ như bash (`--repo x<CR>-h`) → BUDGET hoặc bỏ `\r` khỏi tập khoảng trắng (topo: review) — Bỏ: đã sửa ở #523 (AUD-SEC-645 `đã sửa`; chặn oan hẹp ở AUD-SEC-712) — Gate: `python3 -m unittest tests.test_hooks tests.test_guard_fuzz`
- [ ] `T-3745` 🟠 AUD-SEC-646/647 guard: `_discards_whole_tree` biết `--end-of-options`; `pax` giữ `--` riêng (topo: review) — Gate: `python3 -m unittest tests.test_hooks`
- [ ] `T-3742` 🟠 AUD-SEC-636 guard: quét lệnh git lồng (`rebase --exec`, `bisect run`, `submodule foreach`, `--receive-pack`/`--upload-pack`) (topo: review) — Gate: `python3 -m unittest tests.test_hooks`
- [ ] `T-3768` 🔴 AUD-SEC-727 guard: `rg --pre CMD` chạy lệnh mà guard không xét (`rg --pre rm x .autopilot` cho qua) — quét CMD như lệnh hay BUDGET; kiểm thêm nghi ngờ cùng họ `bat`/`ag`/`ack --pager CMD`, `ugrep --filter`, `rg --hostname-bin` (chạy lệnh từ đối số) (topo: review) — Gate: `python3 -m unittest tests.test_hooks tests.test_guard_fuzz`
- [x] `T-3769` 🔴 AUD-SEC-730 guard: ngoặc trong `${…}` không nháy tách token (`rm -rf ${x:-(a)} /`, `git push ${x:-(a)} origin feat/me --force` cho qua) → BUDGET (D-415) (topo: review) — Gate: `python3 -m unittest tests.test_hooks tests.test_guard_fuzz`
- [ ] `T-3772` 🔴 AUD-SEC-750 guard: nháy lồng với số `'` chẵn trong `"$(…)"` nuốt lệnh giữa vào một token (`echo "$(echo "'")"; rm -rf /; echo "$(echo "'")"` cho qua) → BUDGET (D-415), đo chặn oan trên transcript (topo: review) — Gate: `python3 -m unittest tests.test_hooks tests.test_guard_fuzz`
- [~] `T-3753` 🔴 AUD-SEC-663 guard: từ khoá `time` (`time d=/; rm -rf $d`, `time for/{/if/function …`) không làm mất phép gán và thân cấu trúc (topo: review) — Bỏ: gộp vào T-3764 (ADR-0076, D-430) — Gate: `python3 -m unittest tests.test_hooks tests.test_guard_fuzz`
- [~] `T-3754` 🔴 AUD-SEC-664 guard: thân `coproc [TÊN] { … }` quét như lệnh thường (topo: review) — Bỏ: gộp vào T-3764 (ADR-0076, D-430) — Gate: `python3 -m unittest tests.test_hooks tests.test_guard_fuzz`
- [~] `T-3755` 🔴 AUD-SEC-665 guard: thay lệnh `${ …; }`/`${| …; }` của bash 5.3 được quét hoặc BUDGET (topo: review) — Bỏ: gộp vào T-3761 (ADR-0076, D-430) — Gate: `python3 -m unittest tests.test_hooks tests.test_guard_fuzz`
- [~] `T-3756` 🔴 AUD-SEC-666 guard: extglob `!(…)`/`?(…)`/`*(…)`/`+(…)`/`@(…)` ở lệnh có luật → BUDGET (D-415) (topo: review) — Bỏ: gộp vào T-3761 (ADR-0076, D-430) — Gate: `python3 -m unittest tests.test_hooks tests.test_guard_fuzz`
- [~] `T-3759` 🔴 AUD-SEC-690/710/711 guard: mở rộng dính vào cờ/lệnh con git ngoài phạm vi #523 — cụm cờ ngắn và tên lệnh con có mở rộng (`-d$X`, `push$X`), mở rộng dính TRƯỚC cờ (`$X--delete`), cờ dài ngoài `GIT_DANGER_LONG` (`--creat$X`, `--stdi$X`, `--no-verif$X`) → BUDGET (D-415) (sau: T-3743; topo: review) — Bỏ: gộp vào T-3762 (ADR-0076, D-430) — Gate: `python3 -m unittest tests.test_hooks tests.test_guard_fuzz`
- [ ] `T-3729` Quét lại nhóm TEST, DOC, HAR (`chưa quét`) + sổ `đã sửa` cho các lát trên (D-480; sau: T-3724, T-3726) — Gate: `python3 scripts/xt.py audit check docs/ops/AUDIT-STATUS.md && test "$(git grep -c -E '^\| (4 \| TEST|9 \| DOC|13 \| HAR) \| [^|]+ \| đã quét \|' -- docs/ops/AUDIT-STATUS.md)" = docs/ops/AUDIT-STATUS.md:3`

### Lát 6 — ADR-0076 cổng tập con dương
> Thay các task guard `[~]` "gộp vào T-376x" ở trên (D-430…D-432); mỗi lát một PR, test đỏ trước, review `reviewer-alt`,
> đo trước/sau trên lệnh thật — hơn 0,2 % đổi từ cho qua sang chặn thì không merge, mở D mới (D-431).

- [x] `T-3760` lát 0: bộ lệnh lành làm ca `control` (`adr76-ctl-*`) + `GATE_NAMES` + test khớp tên luật rẽ nhánh; không đổi hành vi (topo: review) — Gate: `python3 -m unittest tests.test_hooks tests.test_guard_fuzz tests.test_guard_strict tests.test_xt_core tests.test_ci_shard && python3 scripts/xt.py autonomy-bench`
- [x] `T-3762` 🔴 AUD-SEC-690/710/711/726 lát 2: khung `_ruled_word_why` trong `_allowlist_why` + P2 (mở rộng trước `=` ở cờ), P3 (mở rộng liền `-…`), P1 lệnh con cấp hai; thêm (review #526): (i) quyết `printf` (đang `GATE_PASSIVE` dù `printf -v` ghi biến; `read`/`let` ở `GATE_NAMES`) bằng số đo chặn oan, (ii) gỡ AUD-SEC-721/722/724/725 khỏi `tests/fixtures/autonomy/scope.json` khi có ca corpus, (iii) D-435: luật hẹp "cờ của trình thông dịch có mở rộng/glob → BUDGET" (`python3 "$X"-c '…'`, `python3 -$X '…'`, `node -$X '…'` — AUD-SEC-726) (sau: T-3760; topo: review) — Gate: `python3 -m unittest tests.test_hooks tests.test_guard_fuzz tests.test_guard_strict tests.test_xt_core tests.test_ci_shard && python3 scripts/xt.py autonomy-bench`
- [x] `T-3761` 🔴 AUD-SEC-665/666/656 lát 1: P6 — `${ `/`${|` ở `STRICT_LIVE` và thân heredoc không nháy, extglob trần (`_extglob_why`), `#` trong số học (`_arith_hash_why`), `\` lẻ cuối lệnh (`_strict_why`), `shlex` lỗi ở lệnh chặt (`tokenize(strict)`) → BUDGET (sau: T-3760; topo: review) — Gate: `python3 -m unittest tests.test_hooks tests.test_guard_fuzz tests.test_guard_strict tests.test_xt_core tests.test_ci_shard && python3 scripts/xt.py autonomy-bench`
- [x] `T-3763` 🔴 AUD-SEC-609 lát 3: P4 — `<(…)`/`>(…)` làm đối số, `$(…)`/backtick trần còn từ theo sau hay dính chữ → BUDGET (sau: T-3762; topo: review) — Gate: `python3 -m unittest tests.test_hooks tests.test_guard_fuzz tests.test_guard_strict tests.test_xt_core tests.test_ci_shard && python3 scripts/xt.py autonomy-bench`
- [x] `T-3764` 🔴 AUD-SEC-657/700/664/663/659 lát 4: P0 tiền tố — `{tên}>`/`{tên}<`, `coproc`, `time` rồi gán/từ khoá/`{`/`function`, `exec` có cờ ngoài `-a TÊN`, cờ trình bọc có mở rộng (sau: T-3762; topo: review) — Gate: `python3 -m unittest tests.test_hooks tests.test_guard_fuzz tests.test_guard_strict tests.test_xt_core tests.test_ci_shard && python3 scripts/xt.py autonomy-bench`
- [ ] `T-3765` 🔴 AUD-SEC-680/660/661 lát 5: P5 chuyển hướng rồi còn từ thường (git/gh) và P7 hàm/stdin (sau: T-3762; topo: review) — Gate: `python3 -m unittest tests.test_hooks tests.test_guard_fuzz tests.test_guard_strict tests.test_xt_core tests.test_ci_shard && python3 scripts/xt.py autonomy-bench`
- [ ] `T-3766` 🔴 AUD-SEC-606/691 lát 6: P8 thân `sh -c`/`eval`/`trap` nháy kép có `\$`/`` \` `` và đọc lại hậu tố cho lệnh lạ có tên có luật trong 3 đối số đầu (D-432; "tên có luật" = một hàm `_is_ruled_name` = `_GATE_BRANCHED` ∪ `INTERP_RE` ∪ tiền tố (`mkfs*`, `git-<lệnh con>`), không phải `GATE_NAMES` hay riêng `_GATE_BRANCHED` — `ssh-agent python3 -c …` và `ssh-agent python3.12 -c …` phải bị quét, review #525/#526) (sau: T-3762; topo: review) — Gate: `python3 -m unittest tests.test_hooks tests.test_guard_fuzz tests.test_guard_strict tests.test_xt_core tests.test_ci_shard && python3 scripts/xt.py autonomy-bench`
- [ ] `T-3767` 🔴 AUD-SEC-648 lát riêng: phía Write/Edit — dòng §5 GO-NO-GO có ô tên/ngày mà không ở dạng bảng chuẩn thì chặn lúc ghi (D-432; ngoài cổng) (topo: review) — Gate: `python3 -m unittest tests.test_hooks tests.test_guard_go_no_go tests.test_guard_fuzz tests.test_guard_strict tests.test_xt_core tests.test_ci_shard && python3 scripts/xt.py autonomy-bench`
- [ ] `T-3770` 🔴 AUD-SEC-741/742/744/746 lát 2c (review #529): cổng kích hoạt ở `git-<lệnh con>` (`_is_ruled_name` có tiền tố `git-`), P1 cấp hai thêm `config` và trên lệnh con đã giải alias (`git -c alias.s=stash s drop$X`), `$X` trần đứng riêng làm lệch vị trí (`python3 -c $X '…'`, `bash $X -c …`, `gh pr -t $X y merge`), giá trị cờ luật đọc có mở rộng (`--method DELETE$X`, `push.default=matching$X`) → BUDGET; sửa AUD-SEC-741 làm gãy ví dụ dấu `GIT_DYN_FLAG_MARK` của `ReasonCodeLockTest` (`/usr/lib/git-core/git-push --delet$X …`) — cập nhật ví dụ khi đó (sau: T-3762; topo: review) — Gate: `python3 -m unittest tests.test_hooks tests.test_guard_fuzz tests.test_guard_strict tests.test_xt_core tests.test_ci_shard && python3 scripts/xt.py autonomy-bench`
- [ ] `T-3771` 🔴 AUD-SEC-743/745 (review #529; cần phiên chính quyết phạm vi trước): vùng cờ trình thông dịch sau trình chạy có `--` (`uv run -- python3 "$X"-c`, `npx -- node`, `poetry run --`, `pnpm/npm exec --`) và lệnh con cấp một có mở rộng/glob của công cụ khác git/gh (`kubectl delete$X`, `terraform destroy$X`, `npm publish$X`, `pip install$X`) (sau: T-3762; topo: review) — Gate: `python3 -m unittest tests.test_hooks tests.test_guard_fuzz tests.test_guard_strict tests.test_xt_core tests.test_ci_shard && python3 scripts/xt.py autonomy-bench`
- [ ] `T-3773` 🔴 AUD-SEC-752/753 guard (review #529, có từ trước): lệnh nhắc `IFS` thì bỏ miễn trừ tham số "ra số" (`$?`/`$#`/`$$`, `$((…))`) ở cả `SPLIT_NUM_RE`/`_unsafe_dollar` và cổng ADR-0076 (`IFS=0; git push -d$? origin feat/other`, `IFS=0; rm -rf /tmp/rvx$?/zz` → BUDGET); `git commit --no-verif` (viết tắt) nhận là bỏ hook như `PUSH_NO_VERIFY_RE` (topo: review) — Gate: `python3 -m unittest tests.test_hooks tests.test_guard_fuzz tests.test_guard_strict tests.test_xt_core tests.test_ci_shard && python3 scripts/xt.py autonomy-bench`
- [ ] `T-3790` 🔴 AUD-SEC-780 guard (tìm ở lát 4 #530, có từ trước): lệnh chỉ có gán + chuyển hướng (`>o d=/; rm -rf $d`, `2>o d=/`, `d=/ >o`, `{fd}>o d=/`, `>o export d=/`) giữ gán trong shell mà `_record_assigns` bỏ qua → BUDGET (D-415), đo chặn oan trên transcript (topo: review) — Gate: `python3 -m unittest tests.test_hooks tests.test_guard_fuzz tests.test_guard_strict tests.test_xt_core tests.test_ci_shard && python3 scripts/xt.py autonomy-bench`
