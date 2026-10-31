# AUDIT-REPORT — delta sau 3.29.0 (quét lại), 2026-10-31

> Phạm vi: `6799550..78fb359` (#316–#358; HEAD quét `4ff383a` cùng cây với `78fb359` trên `main`). Quét lại 8 nhóm `chưa quét` của báo cáo 2026-10-30 (ba cụm lớn INCONCLUSIVE) bằng 11 cụm nhỏ (~400–600 dòng diff mỗi cụm), chạy bằng workflow; mọi 🟠 qua một reviewer độc lập khác người tìm. Kèm phát hiện của review #359 (sau merge).

## Tóm tắt

| Mức | Mới | ID |
|---|---|---|
| 🔴 | 0 | |
| 🟠 | 8 | AUD-HAR-149, AUD-HAR-151, AUD-HAR-154, AUD-HAR-155, AUD-SEC-186, AUD-SEC-188, AUD-DOC-123, AUD-DOC-124 |
| 🟢 | 33 | AUD-SEC-184, AUD-CODE-027, AUD-HAR-150, AUD-SEC-185, AUD-HAR-152, AUD-HAR-153, AUD-CODE-028, AUD-CODE-029, AUD-CODE-030, AUD-HAR-156, AUD-SEC-187, AUD-HAR-157, AUD-HAR-158, AUD-HAR-159, AUD-HAR-160, AUD-SEC-189, AUD-HAR-161, AUD-CODE-031, AUD-HAR-162, AUD-CI-022, AUD-TEST-033, AUD-TEST-034, AUD-TEST-035, AUD-TEST-036, AUD-DOC-121, AUD-XFEAT-036, AUD-XFEAT-037, AUD-DOC-122, AUD-DOC-125, AUD-DOC-126, AUD-DOC-127, AUD-DOC-128, AUD-DOC-129 |

Mọi cụm kết luận được (`xong`), không cụm nào bị chặn → 8 nhóm `đã quét` ở `78fb359`.

## Lệnh đã chạy (phiên chính)

| Lệnh | Kết quả |
|---|---|
| `scripts/dev-task.sh gate` (`4ff383a`) | exit 0 (5 lệnh, coverage 100 %) |
| `xt.py blueprint-status BLUEPRINT.md --strict --run` | exit 0 (MUST 64 đạt · 6 miễn · 0 chưa) |
| `xt.py doctor` | 0 lỗi · 0 cảnh báo |
| `xt.py audit plan` | 12 nhóm áp dụng, DATA N/A; 69 bằng chứng blueprint trỏ file đã đổi — lệnh `— Kiểm:` của chúng chạy xanh trong `--run` ở trên |
| `xt.py autonomy-bench` | 606 ca, false-green 0 |
| cụm `ci`: `zizmor --min-severity medium` HEAD so `6799550` | không phát hiện mới; actionlint `chưa biết:` (không có trong container) |
| gitleaks, semgrep, osv-scanner, pip-audit cục bộ | `chưa biết:` — không có trong container; CI `gitleaks`/`dep-audit` xanh trên #358/#359 |

## Cụm và người rà

11 cụm `reviewer` read-only: `xt-a`…`xt-e` (`scripts/xt.py` theo dải dòng), `guard-a`/`guard-b` (`.claude/hooks/guard.py`), `misc` (install, dev-task, skills, templates), `ci` (workflows + zizmor), `test`, `doc`. Xác minh đối kháng: mỗi 🟠 một `reviewer` khác (effort high), nhận phát hiện + vị trí, không nhận lý luận người tìm — cả 7 tái hiện được (hai phát hiện trùng gốc STAGE.json-thư-mục gộp làm một).

## Chi tiết 🟠

- **AUD-HAR-149** (xt-a) — `scripts/xt.py:7226-7235 (evidence_fingerprint), :7201-7208 (_signoff_excluded), :7499-7509 (_stage_changed), :7255-7263 (_changed_since)`: Vân tay nội dung (`evidence_fingerprint`) và so file đổi (`_stage_changed`/`_changed_since`) lệch khi dự án nằm ở thư mục con của repo (monorepo `apps/web`, kiểu cài mà `loop_root` của delta này hỗ trợ). `ls-tree --full-tree` trả đường dẫn tính từ gốc repo, còn `_signoff_excluded`/`skip` so với đường dẫn tính từ dự án, nên sổ giai đoạn và PROGRESS của dự án không được loại. Ngoài ra vân tay phủ cả repo trong khi diff chỉ phủ `.`. Hệ quả: vừa `stage submit` rồi commit sổ, `next-step` đã báo `stage-reopen` (bản trình cũ), và commit ở app khác cũng làm bản trình hay gói nghiệm thu hết hạn. Vòng trình → mở lại → trình lặp không dừng.
- **AUD-HAR-151** (xt-c) — `/home/user/X-Templates/scripts/xt.py:7462-7465 (và 7452, 7471)`: Gói nghiệm thu cũ vẫn được trả là 'còn hiệu lực' khi có kết quả `release-check` mới hơn trên cùng nội dung cây. Lúc đó `human_pending` chỉ hợp gói cũ với `deferred` mà bỏ qua `rel["human"]` mới. Khi DECISIONS.md đổi (file này nằm ngoài vân tay và ngoài `_changed_since`), việc chờ người mới như `prod_switch` không hiện: reason ghi 'chờ người: không' và `missing` thiếu 'người xác nhận prod_switch'. Cùng gốc: `fresh` (dòng 7452) coi kết quả `release-check` là đúng cây hiện tại, dù DECISIONS.md, file mà hàng `prod_switch` đọc, đã đổi sau đó.
- **AUD-HAR-154** (xt-d) — `.claude/hooks/guard.py:237 (classify_path so `rel == STAGE_LEDGER`, không xét thư mục tổ tiên); ảnh hưởng scripts/xt.py:10070 read_stage`: Guard chỉ rào đúng đường `docs/autopilot/STAGE.json`. Xoá hoặc dời thư mục cha của sổ giai đoạn (`rm -r docs/autopilot`, `git rm -r docs/autopilot`, `mv docs/autopilot …`, `git mv docs/autopilot …`) vẫn được cho chạy, trong khi `rm -r .autopilot` thì bị chặn. Sổ đã commit: mọi lệnh `stage`/`loop init|next|record` gặp StageError, cần người khôi phục. Sổ chưa commit (ngay sau `stage init`/`approve`) hoặc bản clone nông: khoá giai đoạn biến mất (`stage status` báo 'Chưa dùng giai đoạn sản phẩm').
- **AUD-HAR-155** (xt-e) — `scripts/xt.py:11605 (show), scripts/xt.py:11598-11617 (_review_drift, tập miễn sổ); bên gọi _debt_problem và _pr_rethink`: `pr debt` không bao giờ dùng được khi dự án nằm ở thư mục con của repo (monorepo `apps/web`, layout khung có hỗ trợ: AUD-XFEAT-003, AUD-HAR-125). `_review_drift` đọc sổ bằng `git show <head>:docs/ops/AUDIT-STATUS.md`. Git hiểu đường dẫn này tính từ gốc repo chứ không từ thư mục dự án, nên lệnh lỗi và `pr debt` luôn exit 2. Dù sửa thành `./`, phép miễn `- {AUDIT_STATUS_DEFAULT}` vẫn so sai vì `git diff --name-only` trả đường dẫn tính từ gốc repo (`apps/web/docs/ops/AUDIT-STATUS.md`), nên commit chỉ sửa sổ vẫn bị tính là sửa thêm. Hệ quả: `pr next` trả `debt` nhưng `pr debt` luôn từ chối. `pr rethink` đi từ `debt` cũng không đặt được dấu head, nên bước kế là `review` thay vì `fix`, tức review lại head chưa sửa và đốt mất lần sửa (giống AUD-HAR-135, nhưng do layout). Lỗi theo hướng chặt hơn, không lách được rào, nhưng quy trình ADR-0059 hỏng với monorepo.
- **AUD-SEC-186** (guard-a) — `.claude/hooks/guard.py:2802 (STDIN_READERS chỉ có cat/tac/head/tail), :2854-2867 (_reader_files), :2870 (_subst_files); framework/11-autonomous-loop/harness-files.md:86-88`: Dấu review đăng tay vẫn lọt khi thân lấy từ file có sẵn qua `$(…)` dùng lệnh đọc khác `cat/tac/head/tail` (`grep . f`, `sed '' f`, `sed -n p f`, `awk 1 f`, `cut -c1- f`, `more f`). Tài liệu nói guard đã bắt "file đọc trong `$(…)`", nên khe này chưa được ghi. File mang dấu tạo được ở lượt trước: Write và `printf … > /tmp/b.md` đều cho qua.
- **AUD-SEC-188** (guard-b) — `.claude/hooks/guard.py:4703 (`elif x[:2] in ("-t", "-b", "-F") and len(x) > 2`)`: Lách luật ghi công AI (LOOP-HARNESS-027) bằng cờ ngắn gộp ở `gh pr create`: `_gh_pr_text_args` chỉ nhận `-t/-b/-F` khi chúng đứng đầu token (`x[:2]`), nên `-dt '…Claude Opus…'` và `-db 'Generated by Claude Opus 5'` lọt qua. Diff đã sửa đúng dạng gộp kiểu pflag này cho `_gh_pr_titles` (review #343) nhưng không áp cho parser anh em, dù hunk 4690 có chạm vào hàm này. Lỗi có từ trước, base 6799550 cũng lọt.
- **AUD-DOC-123** (review #359): `LOOP-CI-020` Kiểm canary "tạo file" không phân biệt "không nạp" với "nạp nhưng không làm được" khi agent chỉ có công cụ đọc (`pr-review.yml:91` `--allowedTools "Read,Grep,Glob"`); "sau job" không kiểm được trên runner GitHub-hosted
- **AUD-DOC-124** (review #359): `AI-PROTO-019` danh sách từ cấm mới hẹp hơn regex cũ: `card`, `creditCard`, `cardNo`, `card_num`, `passphrase`, `passcode` lọt qua lint

Tái hiện từng bước: cột Bằng chứng của từng dòng trong `AUDIT-STATUS.md` (lệnh + output, script ở scratch của phiên).

## Kế hoạch sửa (tự duyệt, D-NNN ở `PLAN-harden-2026-10-31.md`)

1. Đợt guard (SEC): STAGE.json qua thư mục cha/đích thư mục; dấu review qua lệnh đọc khác `cat`; cờ gộp `gh pr create -dt/-db`; cùng AUD-SEC-180/181 (có từ trước).
2. Đợt `xt.py` monorepo (HAR): vân tay/so file đổi và `pr debt` khi dự án ở thư mục con.
3. Đợt `xt.py` gói nghiệm thu: hợp `rel.human` mới khi gói còn khớp vân tay.
4. Đợt tài liệu: hai 🟠 của review #359 + 🟢 tài liệu.
Mỗi đợt một PR ≤ 150 dòng, test tái hiện đỏ trước khi sửa. 🟢 còn lại giữ `mở` làm nợ có chủ trong PLAN.

## Nợ 🟢

33 mục 🟢 mới (danh sách ở Tóm tắt), chủ: phiên `/complete` kế; xếp vào PLAN-harden theo cụm file sau các đợt 🟠.
