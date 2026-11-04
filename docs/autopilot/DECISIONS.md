# Nhật ký quyết định tự duyệt

> Ghi bởi `xt.py loop decide`. Phiên chính tự duyệt điểm quyết định theo tiêu chí chất lượng cuối (`LOOP-STOP-018`, ADR-0008 của khung). Người xem lại bất cứ lúc nào; đổi ý → quyết định mới ghi "thay D-NNN", không sửa mục cũ.
> Bản tháng trước: [`DECISIONS-2026-10.md`](DECISIONS-2026-10.md) (D-001…D-287), [`DECISIONS-2026-11.md`](DECISIONS-2026-11.md) (D-292…D-330) — máy đọc cả bản tháng (T-3651).

### D-331 · 2026-11-03T15:49:52+00:00 · Hai 🔴 mở AUD-SEC-406 (tên dựng/ngầm) và AUD-SEC-414 (HOME/CDPATH trước cd, patch) thuộc lớp lách guard bằng tên/mã dựng lúc chạy — vá tiếp, chặn rộng, bật sandbox bắt buộc, hay chấp nhận có hạn?

- Phương án: (1) Vá tiếp từng dạng · (2) Chặn mọi mở rộng/tệp ghi trong lệnh chạy mã · (3) Bật sandbox bắt buộc trong settings của khung · (4) ADR-0067: chấp nhận có hạn 2027-01-21 lớp lách bằng tên/mã dựng lúc chạy khi mọi dạng nguyên văn đã chặn; ranh giới cứng ở ruleset GitHub/CI/review; đánh giá sandbox opt-in trước hạn
- Chọn: ADR-0067: chấp nhận có hạn 2027-01-21 lớp lách bằng tên/mã dựng lúc chạy khi mọi dạng nguyên văn đã chặn; ranh giới cứng ở ruleset GitHub/CI/review; đánh giá sandbox opt-in trước hạn
- Lý do (tiêu chí chất lượng cuối): (3) phân tích tĩnh shell không đầy đủ theo nguyên lý — vá tiếp là vòng không điểm dừng kèm hồi quy (#426/#427); (1) không nới luật, không khai đóng, force-push/xoá nhánh chính bị ruleset máy chủ chặn; (2) chỉ đổi trạng thái sổ; chặn rộng/sandbox bắt buộc gây chặn oan lớn hoặc chưa chạy được ở cloud
- Đường lùi: Đổi AUD-SEC-406/414/410/413 về mở

### D-332 · 2026-11-03T16:19:32+00:00 · Review #428 chặn: ADR-0067 chấp nhận quá phạm vi (AUD-SEC-414 và phần nguyên văn của 406 — sponge/tar/unzip/openssl/xxd, tệp nạp ngầm — vẫn lọt dù nguyên văn; nói quá lớp ngoài; đảo ADR-0065 không ghi) — sửa thế nào?

- Phương án: (1) Giữ chấp nhận, sửa câu chữ · (2) Thu hẹp ADR-0067 về ĐÚNG lớp tên dựng lúc chạy (điều kiện a/b/c), ghi Thay một phần ADR-0065; 414 về mở; tách 2 ID 🔴 mở mới (trình ghi chưa liệt kê; tệp nạp ngầm); task T-3663 sửa luật tĩnh; T-3635 bỏ tick; sửa mô tả lớp ngoài (review không là ranh giới máy chủ; tắt hook cục bộ không có lớp cứng khi sandbox tắt)
- Chọn: Thu hẹp ADR-0067 về ĐÚNG lớp tên dựng lúc chạy (điều kiện a/b/c), ghi Thay một phần ADR-0065; 414 về mở; tách 2 ID 🔴 mở mới (trình ghi chưa liệt kê; tệp nạp ngầm); task T-3663 sửa luật tĩnh; T-3635 bỏ tick; sửa mô tả lớp ngoài (review không là ranh giới máy chủ; tắt hook cục bộ không có lớp cứng khi sandbox tắt)
- Lý do (tiêu chí chất lượng cuối): (1) cách hiểu chặt: dạng nguyên văn sửa được bằng luật tĩnh nên không được chấp nhận; cổng --strict không xanh giả; (3) giữ điểm dừng cho đúng lớp không giải được tĩnh
- Đường lùi: Đổi các dòng sổ về trạng thái trước #428

### D-333 · 2026-11-03T17:43:50+00:00 · T-3663: luật AUD-SEC-415 chặn lệnh Kiểm PRF-CLI-004 (git ls-files --error-unmatch scripts/xt.py … && python3 scripts/xt.py --help) — viết lại lệnh Kiểm hay miễn git ls-files?

- Phương án: (1) Viết lại lệnh Kiểm: bỏ scripts/xt.py khỏi git ls-files (CI chỉ có tệp đã track), theo tiền lệ UX-DS-021 · (2) Thêm git ls-files vào danh sách đọc REUSE_GIT_READS
- Chọn: Viết lại lệnh Kiểm: bỏ scripts/xt.py khỏi git ls-files (CI chỉ có tệp đã track), theo tiền lệ UX-DS-021
- Lý do (tiêu chí chất lượng cuối): (1) không thêm miễn trừ mới vào guard (bài học hồi quy #426/#427); lệnh Kiểm lỏng hơn chút ở máy dev nhưng CI giữ nguyên ý (tệp tồn tại = đã track); (3) đơn giản
- Đường lùi: Trả lệnh Kiểm cũ và thêm miễn ls-files bằng ADR

### D-334 · 2026-11-03T19:08:57+00:00 · Nợ #429 (PR #430): AUD-SEC-419 — duyệt 2 lệnh chặn→qua có chủ đích (shellcheck, git log là lệnh đọc; mất miễn khi GIT_*/-C/-c/*PAGER=) và chấp nhận phần (b) git apply/patch từ tệp diff vẫn BUDGET?

- Phương án: (1) Duyệt: (a) gỡ chặn oan bằng danh sách đọc có điều kiện mất miễn; (b) chấp nhận chặn oan có chủ đích tới 2027-01-21 · (2) Giữ chặn cả (a)
- Chọn: Duyệt: (a) gỡ chặn oan bằng danh sách đọc có điều kiện mất miễn; (b) chấp nhận chặn oan có chủ đích tới 2027-01-21
- Lý do (tiêu chí chất lượng cuối): (1) shellcheck/which/type/command -v/git log không chạy mã tệp; git log chỉ chạy textconv/pager qua cấu hình mà guard đã chặn (HOOK_BYPASS) hoặc qua GIT_*/-c/*PAGER= — đã làm mất miễn; (b) diff từ tệp không đọc được đích nên giữ chặn là hướng an toàn; (4) gỡ chặn oan đo được
- Đường lùi: Bỏ shellcheck/which/type/command -v/git log khỏi danh sách đọc

### D-335 · 2026-11-03T20:51:21+00:00 · Đính chính D-334 (review #430/#431): lý do 'git log chỉ chạy textconv/pager qua cấu hình mà guard đã chặn (HOOK_BYPASS)' sai tiền đề — ghi thô ~/.gitconfig từng lọt (AUD-SEC-424, nay chặn ở #431) và pager không chạy khi không TTY — giữ hay bỏ miễn git log?

- Phương án: (1) Giữ miễn git log (D-334), sửa lý do: an toàn dựa trên chặn ghi mọi tệp cấu hình git (.git/config, config.worktree, gitconfig toàn cục — #431/#432) + mất miễn khi GIT_*/-C/-c; pager không chạy khi không TTY · (2) Bỏ miễn git log
- Chọn: Giữ miễn git log (D-334), sửa lý do: an toàn dựa trên chặn ghi mọi tệp cấu hình git (.git/config, config.worktree, gitconfig toàn cục — #431/#432) + mất miễn khi GIT_*/-C/-c; pager không chạy khi không TTY
- Lý do (tiêu chí chất lượng cuối): (1) sau #431/#432 mọi đường ghi cấu hình git đã chặn nên git log không chạy được mã mới; (4) gỡ chặn oan; thay lý do D-334
- Đường lùi: Bỏ git log khỏi danh sách đọc

### D-336 · 2026-11-03T21:58:57+00:00 · AUD-SEC-434 (phía đọc cấu hình git: HOME=/XDG_CONFIG_HOME=/GIT_CONFIG_GLOBAL=tệp vừa ghi ở lệnh trước, declare -x GIT_CONFIG_*) — vá theo tệp ghi hay luật phía đọc? (kèm đính chính D-335)

- Phương án: (1) Tiếp tục chặn phía ghi theo từng tệp/đường · (2) Luật phía đọc: lệnh git có HOME=/XDG_CONFIG_HOME=/GIT_CONFIG_GLOBAL|SYSTEM=(khác /dev/null)/GIT_CONFIG_PARAMETERS/GIT_CONFIG_COUNT|KEY_n|VALUE_n gán bằng mọi cách (đầu lệnh, export, declare -x, env, typeset -x) trong cùng lệnh → commit/push xử như bỏ qua hook (luật no_verify sẵn có); lệnh git khác → BUDGET; giữ chặn phía ghi
- Chọn: Luật phía đọc: lệnh git có HOME=/XDG_CONFIG_HOME=/GIT_CONFIG_GLOBAL|SYSTEM=(khác /dev/null)/GIT_CONFIG_PARAMETERS/GIT_CONFIG_COUNT|KEY_n|VALUE_n gán bằng mọi cách (đầu lệnh, export, declare -x, env, typeset -x) trong cùng lệnh → commit/push xử như bỏ qua hook (luật no_verify sẵn có); lệnh git khác → BUDGET; giữ chặn phía ghi
- Lý do (tiêu chí chất lượng cuối): (1) đóng cả lớp: tệp ghi ở lệnh trước không cần dò, git chỉ đọc cấu hình lạ khi có biến này; OR với luật cũ; (3) một luật thay cho vá từng tệp (#431/#432 lặp); đính chính D-335: miễn git log an toàn nhờ luật phía đọc này + chặn ghi tệp cấu hình
- Đường lùi: Bỏ luật phía đọc

### D-337 · 2026-11-03T22:44:43+00:00 · T-3666/AUD-SEC-434: luật phía đọc D-336 áp cho biến trỏ TỆP cấu hình (HOME, XDG_CONFIG_HOME, GIT_CONFIG_GLOBAL|SYSTEM) hay cả GIT_CONFIG_PARAMETERS/GIT_CONFIG_COUNT|KEY_n|VALUE_n?

- Phương án: (1) Chỉ biến trỏ tệp; biến cấu hình một lần guard đọc được nguyên giá trị nên xét bằng luật khoá sẵn có (hooksPath, khoá chạy lệnh, alias) · (2) Đủ danh sách D-336, chấp nhận chặn oan push/alias qua biến môi trường
- Chọn: Chỉ biến trỏ tệp; biến cấu hình một lần guard đọc được nguyên giá trị nên xét bằng luật khoá sẵn có (hooksPath, khoá chạy lệnh, alias)
- Lý do (tiêu chí chất lượng cuối): (1) giá trị GIT_CONFIG_PARAMETERS/KEY_n/VALUE_n nằm ngay trong lệnh — luật khoá đã chặn khoá nguy hiểm (không có tệp ẩn để đọc); chỉ biến trỏ tệp mới đưa nội dung guard không thấy; (4) giữ hành vi đúng của test adapter/alias; thu hẹp D-336 theo bằng chứng
- Đường lùi: Mở rộng luật phía đọc cho đủ danh sách

### D-338 · 2026-11-03T23:42:17+00:00 · Đính chính D-336 (review #433): 'git chỉ đọc cấu hình lạ khi có các biến này' sai — GIT_DIR/--git-dir, GIT_TEMPLATE_DIR/--template, GIT_EXEC_PATH/--exec-path, hard link cũng dẫn git tới cấu hình/mã ngoài; luật phía đọc mở rộng thế nào?

- Phương án: (1) Mở rộng luật phía đọc (D-336/337) thêm GIT_DIR/--git-dir/GIT_COMMON_DIR (khác .git của dự án), GIT_TEMPLATE_DIR/--template, GIT_EXEC_PATH/--exec-path; chặn ghi qua hard link bằng so inode — T-3667 · (2) Chấp nhận lớp này theo ADR-0067
- Chọn: Mở rộng luật phía đọc (D-336/337) thêm GIT_DIR/--git-dir/GIT_COMMON_DIR (khác .git của dự án), GIT_TEMPLATE_DIR/--template, GIT_EXEC_PATH/--exec-path; chặn ghi qua hard link bằng so inode — T-3667
- Lý do (tiêu chí chất lượng cuối): (1) các dạng này nguyên văn trong một lệnh nên luật tĩnh bắt được (ADR-0067 chỉ chấp nhận tên dựng lúc chạy); (3) cùng một luật phía đọc, không thêm miễn trừ
- Đường lùi: Bỏ các biến/cờ mới khỏi luật phía đọc

### D-340 · 2026-11-04T01:05:06+00:00 · Audit delta 2026-11-04: xử lý nợ Git guard sau #434 thế nào?

- Phương án: (1) Sửa các đường lách Git guard tái hiện được, giữ test hồi quy có đối chứng và chạy cổng đầy đủ trước PR · (2) Giữ các phát hiện mở và hoãn sang đợt sandbox
- Chọn: Sửa các đường lách Git guard tái hiện được, giữ test hồi quy có đối chứng và chạy cổng đầy đủ trước PR
- Lý do (tiêu chí chất lượng cuối): Hai ca scratch cho Git đọc cấu hình đổi hook hoặc chạy alias mà guard cho qua. Chặn ở đầu đọc và ghi theo phạm vi hẹp, giữ đường lùi bằng một lát PR. Chạy phiên tương tác.
- Đường lùi: Revert commit sửa guard và mở lại phát hiện với bằng chứng tái hiện.

### D-341 · 2026-11-04T05:34:12+00:00 · Nhận 90 bài học stored XT-H-027…116 (chủ dự án yêu cầu 2026-11-04): mức và phạm vi?

- Phương án: (1) Một PR nội dung: bổ sung vào ID có sẵn giữ mức; ID mới mặc định SHOULD; đổi mức chỉ khi đề xuất có và module còn chỗ (WF-CI-016 SHOULD→MUST@L vì ci-cd-pipeline đủ 4 MUST@M; CMP-AI-017 MAY→SHOULD; mới MUST@L: SEC-SUPPLY-033, AI-AGENTIC-020); công cụ (ci-check agent-action, bước actionlint/zizmor trong templates/ci.yml, release-check provenance, baseline.json) tách task T-3669 · (2) Áp đúng mức đề xuất (WF-CI-016 MUST@M, nhiều MUST@L) và làm công cụ cùng PR
- Chọn: Một PR nội dung: bổ sung vào ID có sẵn giữ mức; ID mới mặc định SHOULD; đổi mức chỉ khi đề xuất có và module còn chỗ (WF-CI-016 SHOULD→MUST@L vì ci-cd-pipeline đủ 4 MUST@M; CMP-AI-017 MAY→SHOULD; mới MUST@L: SEC-SUPPLY-033, AI-AGENTIC-020); công cụ (ci-check agent-action, bước actionlint/zizmor trong templates/ci.yml, release-check provenance, baseline.json) tách task T-3669
- Lý do (tiêu chí chất lượng cuối): (1) MUST@M vượt trần 4 MUST/module (ADR-0004) và mục MUST cần Kiểm máy có thật — công cụ chưa có thì không nâng; (2) mỗi đổi mức một dòng CHANGELOG, đường lùi rõ; (3) nội dung và công cụ tách lát, PR nội dung dễ review; dữ kiện xác minh nguồn sống trước khi ghép (P2)
- Đường lùi: Hạ các mức đã nâng về mức cũ ở PR sau; ID mới đổi MAY + Ngừng dùng

### D-342 · 2026-11-04T08:39:09+00:00 · T-3671 lỗ 5 (AUD-SEC-457): cd tới thư mục không có nối bằng ; / xuống dòng / || — đích ghi sau đó giải thế nào?

- Phương án: (1) Xét cả hai nhánh: đường đã giải và thư mục không biết (D-106), lấy kết quả chặt hơn · (2) Chỉ coi thư mục là không biết (None) như spec ban đầu
- Chọn: Xét cả hai nhánh: đường đã giải và thư mục không biết (D-106), lấy kết quả chặt hơn
- Lý do (tiêu chí chất lượng cuối): (1) phương án 2 mở lỗ mới đo được: mkdir .autopilot; cd .autopilot; echo x > v (lúc kiểm chưa có thư mục, lúc chạy có) và đỏ 3 test cũ; xét cả hai nhánh giữ mọi chặn cũ và thêm chặn mới; cd X && … giữ nguyên
- Đường lùi: Gỡ _failed_cd_scan

### D-343 · 2026-11-04T08:39:10+00:00 · T-3671 lỗ 4 (AUD-SEC-456): git config --rename-section — chặn mọi rename hay chỉ khi đích ngoài danh sách section an toàn?

- Phương án: (1) Chặn khi nguồn là section bảo vệ (core/include/includeIf/alias/biến) hoặc đích có tên con hay ngoài danh sách an toàn (user, author, committer, color, push, pull, status, log, i18n, column, advice, rerere, gc, pack, tag, fetch) · (2) Chặn mọi --rename-section
- Chọn: Chặn khi nguồn là section bảo vệ (core/include/includeIf/alias/biến) hoặc đích có tên con hay ngoài danh sách an toàn (user, author, committer, color, push, pull, status, log, i18n, column, advice, rerere, gc, pack, tag, fetch)
- Lý do (tiêu chí chất lượng cuối): (1) đổi tên vào section bảo vệ (vd user→core) hay từ section bảo vệ đều bị chặn; (4) không chặn oan đổi tên section vô hại; danh sách chặt theo git-config(1), thêm section mới cần quyết định mới
- Đường lùi: Chặn mọi --rename-section

### D-344 · 2026-11-04T08:39:11+00:00 · Thay D-123 (AUD-CI-031, review PR 435): mẫu secret-scan dùng gitleaks-action hay CLI?

- Phương án: (1) CLI gitleaks 8.30.1 ghim SHA-256 kiểm trước khi giải nén, quyền contents: read, quét lịch sử + diff merge (#435 đã làm, chủ repo mở); dương tính giả ở commit merge tạm miễn bằng vân tay file:rule:line trong .gitleaksignore hay gitleaks:allow · (2) Quay lại gitleaks-action
- Chọn: CLI gitleaks 8.30.1 ghim SHA-256 kiểm trước khi giải nén, quyền contents: read, quét lịch sử + diff merge (#435 đã làm, chủ repo mở); dương tính giả ở commit merge tạm miễn bằng vân tay file:rule:line trong .gitleaksignore hay gitleaks:allow
- Lý do (tiêu chí chất lượng cuối): (1) action bỏ sót commit thứ 31+ (AUD-CI-030) và cần secret giấy phép cho org; CLI ghim checksum là chuỗi cung ứng chặt hơn; (3) giữ tên required check gitleaks; thay D-123 vì chủ repo đã tự làm lát CLI ở #435
- Đường lùi: Khôi phục gitleaks-action ghim SHA ở secret-scan.yml và mẫu

### D-345 · 2026-11-04T08:39:12+00:00 · Đính chính D-338 (AUD-SEC-451, review PR 435): D-338 ghi 'không thêm miễn trừ' nhưng #434/#435 thêm miễn .git của dự án (gốc, dấu / cuối, --separate-git-dir của chính dự án); 4 dạng còn bị chặn oan (GIT_DIR=.git/worktrees/w, GIT_DIR=$CLAUDE_PROJECT_DIR/.git, GIT_DIR=$(git rev-parse --git-dir), touch sub/.git) — sửa hay chấp nhận?

- Phương án: (1) Chấp nhận có hạn 2027-01-21: lý do chặn có câu viết lại (bỏ GIT_DIR khi chạy trong dự án, dùng git -C; tạo tệp rỗng bằng tên khác); miễn trừ đã thêm chỉ là .git của chính dự án, ghi đúng ở D này · (2) Thêm miễn cho từng dạng
- Chọn: Chấp nhận có hạn 2027-01-21: lý do chặn có câu viết lại (bỏ GIT_DIR khi chạy trong dự án, dùng git -C; tạo tệp rỗng bằng tên khác); miễn trừ đã thêm chỉ là .git của chính dự án, ghi đúng ở D này
- Lý do (tiêu chí chất lượng cuối): (1) giá trị dựng lúc chạy ($(…), biến) guard không giải chắc — miễn là nới (ADR-0067 chỉ chấp nhận, không miễn); worktree gitdir trỏ commondir có thể khác; (4) cả 4 dạng có cách viết tương đương không bị chặn
- Đường lùi: Thêm miễn cho .git/worktrees/<tên> có commondir trỏ .git dự án

### D-346 · 2026-11-04T11:44:42+00:00 · Đính chính D-342 (review PR 438, T-3672): cd hỏng xét theo thư mục 'không biết' chặn oan lệnh thường; cd - theo OLDPWD tự theo dõi bị lách (OLDPWD=X cd -, PWD=X) — mô hình thư mục chạy thế nào?

- Phương án: (1) Tập ứng viên: cd không chắc hiệu lực (; / xuống dòng / || không theo exit, sau !, đường có .. mà phần trước chưa có, đích bị xoá/dời trước đó, cdable_vars) → {thư mục trước} ∪ {đích}; cd trong ống/nền/nhóm ống không đổi thư mục lệnh sau; cd - và cd -- - luôn KHÔNG BIẾT (None, D-106); CDPATH giữ None; luật đích xét mọi ứng viên, chặt nhất thắng · (2) Giữ D-342 (None khi cd hỏng) và theo dõi OLDPWD
- Chọn: Tập ứng viên: cd không chắc hiệu lực (; / xuống dòng / || không theo exit, sau !, đường có .. mà phần trước chưa có, đích bị xoá/dời trước đó, cdable_vars) → {thư mục trước} ∪ {đích}; cd trong ống/nền/nhóm ống không đổi thư mục lệnh sau; cd - và cd -- - luôn KHÔNG BIẾT (None, D-106); CDPATH giữ None; luật đích xét mọi ứng viên, chặt nhất thắng
- Lý do (tiêu chí chất lượng cuối): (1) đóng cả lớp cd hỏng/ống/nền đã tái hiện bằng bash 5.2 thật (AUD-SEC-459/460) và hồi quy cd - (AUD-SEC-466); (4) gỡ 4 chặn oan đo được (AUD-SEC-463); một mô hình thay cho vá từng ca; thay D-342
- Đường lùi: Khôi phục _failed_cd_scan (D-342)

### D-347 · 2026-11-04T13:24:36+00:00 · Audit delta guard 2026-11-04 (sau 438): mô hình tập ứng viên theo từng bước (D-346) vẫn lọt 4 🔴 mới + 3 🔴 có từ trước (cd trong if/while/hàm/eval, cd -P, lastpipe, || exit/return, repo trần chỉ xét ứng viên đầu) — mô phỏng luồng điều khiển bash không hội tụ; chọn mô hình nào?

- Phương án: (1) Hợp mọi đích (bảo thủ): từ lệnh cd/pushd/popd/eval-chứa-cd ĐẦU TIÊN trở đi (trừ chuỗi chỉ gồm cd đích nguyên văn nối bằng && từ đầu lệnh, không khối điều khiển/hàm/ống), mọi lệnh sau xét trên HỢP {thư mục đầu} ∪ {mọi đích cd nguyên văn đã giải theo chữ và theo realpath}; có đích không biết (biến, cd -, .. lặp trong vòng, eval) → None (D-106); mọi phép xét đích ghi/repo trần/Git dir giả/pending xét đủ mọi ứng viên; bỏ miễn || exit|return; alias đặt cùng lệnh lưu trong ScanBudget cho shell lồng/eval · (2) Tiếp tục vá D-346 theo từng ca (lastpipe, exit, -P, khối điều khiển…)
- Chọn: Hợp mọi đích (bảo thủ): từ lệnh cd/pushd/popd/eval-chứa-cd ĐẦU TIÊN trở đi (trừ chuỗi chỉ gồm cd đích nguyên văn nối bằng && từ đầu lệnh, không khối điều khiển/hàm/ống), mọi lệnh sau xét trên HỢP {thư mục đầu} ∪ {mọi đích cd nguyên văn đã giải theo chữ và theo realpath}; có đích không biết (biến, cd -, .. lặp trong vòng, eval) → None (D-106); mọi phép xét đích ghi/repo trần/Git dir giả/pending xét đủ mọi ứng viên; bỏ miễn || exit|return; alias đặt cùng lệnh lưu trong ScanBudget cho shell lồng/eval
- Lý do (tiêu chí chất lượng cuối): (1) hợp mọi đích là xấp xỉ trên đúng (sound) cho mọi luồng điều khiển: bash chỉ có thể đứng ở thư mục đầu hoặc một đích đã cd tới — không cần mô phỏng if/while/hàm/ống/exit; (3) một luật thay cho vá 7 ca, test được; (4) giữ gỡ chặn oan AUD-SEC-463 vì ứng viên là thư mục biết, không phải None; đánh đổi: thêm chặn oan khi đích cd là thư mục canh — chấp nhận theo tiêu chí (1) > (4); thay D-346
- Đường lùi: Khôi phục _CwdWalk theo D-346

### D-348 · 2026-11-04T14:31:31+00:00 · T-3673 (AUD-SEC-475): tệp archive do tar -c/zip/ar/jar/cpio -o/pax -w/7z a/python -m zipfile -c tạo ra vào write_targets kéo theo luật ADR-0066 — tạo archive rồi nhắc lại ở lệnh khác cùng lệnh Bash bị BUDGET (tar -czf a.tgz src && tar -tzf a.tgz) — giữ hay miễn?

- Phương án: (1) Giữ chặt (A): như mọi tệp tự ghi theo ADR-0066; lý do chặn có câu viết lại (tách lệnh) · (2) Chỉ xét archive ở _write_asks (B) · (3) Giữ A + miễn khi lệnh sau chỉ đọc archive (C)
- Chọn: Giữ chặt (A): như mọi tệp tự ghi theo ADR-0066; lý do chặn có câu viết lại (tách lệnh)
- Lý do (tiêu chí chất lượng cuối): (1) archive vừa tạo có thể được chạy như script (tar -cf x p && sh x) — miễn theo kiểu lệnh đọc là bề mặt lách mới; (3) nhất quán ADR-0066, không thêm miễn trừ (ADR-0065); (4) chi phí: agent tách lệnh, đo trên lệnh/CI repo này không dùng dạng đó
- Đường lùi: Phương án C với test cho từng lệnh chỉ đọc

### D-351 · 2026-11-04T18:39:44+00:00 · Review #439 🔴 AUD-SEC-490: cd tương đối trong thân vòng lặp/hàm chỉ giải từ tập lúc gặp, không giải lại từ đích cd đứng sau (cuối thân vòng, nơi gọi hàm) — D-347 khai 'đúng cho mọi luồng điều khiển' là sai; sửa thế nào?

- Phương án: (1) Đích cd tương đối (kể cả ..) trong thân vòng lặp/hàm/trap → thêm None (thư mục không biết, D-106); đích tuyệt đối giữ như cũ · (2) Lặp điểm bất động trên mọi lệnh cd của thân vòng/hàm cho tới khi tập ổn định, quá CWD_UNION_MAX thì None
- Chọn: Đích cd tương đối (kể cả ..) trong thân vòng lặp/hàm/trap → thêm None (thư mục không biết, D-106); đích tuyệt đối giữ như cũ
- Lý do (tiêu chí chất lượng cuối): (1) cả hai đều sound; (3) phương án 1 là một luật, không cần mô phỏng thêm, test được, khép cả nơi gọi hàm lẫn trap; (4) chặn oan thêm chỉ khi cd tương đối nguyên văn trong vòng/hàm rồi ghi đích nhạy cảm/chạy git — dạng hiếm (corpus review 10 815 lệnh không đổi quyết định nào ở head); (1) > (4). Đính chính D-347: câu 'đúng cho mọi luồng điều khiển' chỉ đúng khi đích cd trong vòng/hàm là tuyệt đối.
- Đường lùi: Lặp điểm bất động (phương án 2) nếu đo thấy chặn oan trên lệnh thật

### D-352 · 2026-11-04T10:29:48+00:00 · Chủ dự án 2026-11-04: cho phép agent quyết định khi nào đã đạt và tuyên bố đạt MVP — đảo một phần ADR-0058 (duyệt giai đoạn chỉ người). Làm thế nào?

- Phương án: (1) Khoá xt.yaml stage_approval: human|agent, có hiệu lực khi cả cây làm việc lẫn bản đã commit ở nhánh chính khai agent (như delivery_phase của guard); agent stage approve chỉ khi bản trình còn nguyên (vân tay/SHA khớp), init --adopt và dạng mờ vẫn chỉ người; next-step trả stage-approve; mặc định mã là human, mẫu dự án đích đặt agent · (2) Bỏ hẳn kiểm người/agent ở stage approve và luật STAGE_APPROVE của guard (mọi dự án agent tự duyệt) · (3) Giữ ADR-0058, agent chỉ ghi đề xuất duyệt vào sổ, người vẫn approve
- Chọn: Khoá xt.yaml stage_approval: human|agent, có hiệu lực khi cả cây làm việc lẫn bản đã commit ở nhánh chính khai agent (như delivery_phase của guard); agent stage approve chỉ khi bản trình còn nguyên (vân tay/SHA khớp), init --adopt và dạng mờ vẫn chỉ người; next-step trả stage-approve; mặc định mã là human, mẫu dự án đích đặt agent
- Lý do (tiêu chí chất lượng cuối): (1) đúng/an toàn: quyền do xt.yaml đã commit ở nhánh chính cấp, phiên không tự cấp cho mình; bản trình phải còn nguyên; init --adopt, dạng mờ, strict vẫn chặn; (2) đường lùi: xoá khoá hoặc đặt human là về ADR-0058, một dòng xt.yaml; (3) đơn giản: dùng lại _stage_changed, _committed_xt_text, mẫu build_phase của guard, không thêm sổ; phương án 2 bỏ luôn lớp chặn nhầm cho mọi dự án; phương án 3 không đáp ứng yêu cầu agent tự tuyên bố đạt MVP
- Đường lùi: Đặt stage_approval: human (hoặc bỏ khoá) trong xt.yaml của dự án; ở khung: revert PR ADR-0069, giữ ADR-0058 nguyên bản
- Đính chính số (khi gộp `main` 2026-11-04): ghi lúc đầu là D-342 trên nhánh `claude/amazing-brahmagupta-9jqbg1`; `main` (#438) đã cấp D-342 cho quyết định khác — đánh số lại thành D-347 để không tái sử dụng ID; commit cũ của nhánh còn ghi D-342.
- Đính chính số (khi gộp `main` #439, 2026-11-05): `main` đã cấp D-347/D-348/D-351 cho quyết định khác — D-347 của nhánh `claude/amazing-brahmagupta-9jqbg1` đánh số lại thành D-352 để không tái sử dụng ID.

### D-353 · 2026-11-04T11:11:50+00:00 · ADR-0068 định hướng xưởng phần mềm: chủ dự án trả lời bốn câu hỏi ở research 2026-11-04 §9 thế nào?

- Phương án: (1) 1a gói đầu tiên trong repo khung tại framework/templates/packs/<stack>/ (phiên bản theo VERSION), chuyển repo riêng khi ≥ 2 gói hoặc owner khác; 2a stack của dự án đích hotel-manager (lát B và C dùng chung một gói; stack xác minh khi đọc repo ở PLAN lát B); 3a evidence v3 chỉ thêm trường, release-check --json thêm promotion/subject, giữ go/verdict/exit code ≥ 1 bản minor; 4a tuyến hai API/worker cùng stack, host Codex và Gemini CLI trước, công bố hỗ trợ chỉ khi checks-run · (2) Giữ ADR-0068 ở trạng thái Đề xuất, chưa lập PLAN
- Chọn: 1a gói đầu tiên trong repo khung tại framework/templates/packs/<stack>/ (phiên bản theo VERSION), chuyển repo riêng khi ≥ 2 gói hoặc owner khác; 2a stack của dự án đích hotel-manager (lát B và C dùng chung một gói; stack xác minh khi đọc repo ở PLAN lát B); 3a evidence v3 chỉ thêm trường, release-check --json thêm promotion/subject, giữ go/verdict/exit code ≥ 1 bản minor; 4a tuyến hai API/worker cùng stack, host Codex và Gemini CLI trước, công bố hỗ trợ chỉ khi checks-run
- Lý do (tiêu chí chất lượng cuối): Chủ dự án chốt 2026-11-04 (1a, 2a hotel-manager, 3a, 4a) đúng với đề xuất của phiên theo tiêu chí chất lượng cuối: (1) đúng/an toàn — trường cũ giữ nghĩa, quyền promote ở CI/IAM hệ đích; (2) đường lùi — xoá thư mục gói, đặt lại khoá; (3) đơn giản — một gói, một VERSION, tái dùng install.py manifest và cơ chế sẵn có; ràng buộc §3b giữ nguyên (D-142, ADR-0043/0050/0058/0064)
- Đường lùi: Đổi trạng thái ADR-0068 về Đề xuất hoặc viết ADR mới thay; chưa lát nào có mã nên chỉ cần revert tài liệu
- Đính chính số (khi gộp `main` 2026-11-04): ghi lúc đầu là D-343 trên nhánh `claude/amazing-brahmagupta-9jqbg1`; `main` (#438) đã cấp D-343 cho quyết định khác — đánh số lại thành D-348 để không tái sử dụng ID; commit cũ của nhánh còn ghi D-343.
- Đính chính số (khi gộp `main` #439, 2026-11-05): `main` đã cấp D-347/D-348/D-351 cho quyết định khác — D-348 của nhánh `claude/amazing-brahmagupta-9jqbg1` đánh số lại thành D-353 để không tái sử dụng ID.

### D-354 · 2026-11-04T15:17:01+00:00 · Chủ dự án 2026-11-04: tài liệu repo khung giữ cả lịch sử đã bỏ — làm lại thành dự án không lịch sử, giữ nguyên, hay dời lịch sử vào kho?

- Phương án: (1) Dời lịch sử của chính repo khung (PLAN đã đóng, báo cáo audit/GO-NO-GO/đo cũ) sang docs/archive/ bằng git mv, sửa liên kết; giữ nguyên framework/ (ID Ngừng dùng, Nguồn+ngày, lý do luật), sổ audit, sổ quyết định, PLAN còn mở, đầu vào sống của công cụ; bộ cấp số task quét cả kho; .ignore để ripgrep bỏ qua kho · (2) Làm lại thành dự án mới không lịch sử (xoá ID Ngừng dùng, Nguồn, ADR, CHANGELOG cũ, repo mới) · (3) Giữ nguyên hiện trạng
- Chọn: Dời lịch sử của chính repo khung (PLAN đã đóng, báo cáo audit/GO-NO-GO/đo cũ) sang docs/archive/ bằng git mv, sửa liên kết; giữ nguyên framework/ (ID Ngừng dùng, Nguồn+ngày, lý do luật), sổ audit, sổ quyết định, PLAN còn mở, đầu vào sống của công cụ; bộ cấp số task quét cả kho; .ignore để ripgrep bỏ qua kho
- Lý do (tiêu chí chất lượng cuối): (1) đúng/an toàn: installer chỉ chép framework/ và research được trỏ nên docs/ không tới dự án đích; framework/ giữ cam kết ID ổn định (conventions.md) và P2; bộ cấp số task vẫn thấy ID cũ nên không tái sử dụng T-NNNN; (2) đường lùi: git mv đảo ngược được, lịch sử file giữ; (3) đơn giản: theo tiền lệ T-3651 (file lưu trữ không tính trần); phương án 2 phá ID dự án đích đang tick, vi phạm P2 và AGENTS.md §9, rewrite history bị guard chặn; phương án 3 để docs/autopilot còn 2 KB dưới trần, chặn PLAN lát A ADR-0068
- Đường lùi: git mv ngược các file trong docs/archive/ về chỗ cũ, khôi phục liên kết bằng revert commit; bỏ docs/archive khỏi _plan_paths và .ignore
- Đính chính số (khi gộp `main` 2026-11-04): ghi lúc đầu là D-344 trong lát chưa commit; `main` (#438) đã cấp D-344 cho quyết định khác — đánh số lại thành D-349 để không tái sử dụng ID.
- Đính chính số (khi gộp `main` #439, 2026-11-05): `main` đã cấp D-347/D-348/D-351 cho quyết định khác — D-349 của nhánh `claude/amazing-brahmagupta-9jqbg1` đánh số lại thành D-354 để không tái sử dụng ID.

### D-355 · 2026-11-04T17:18:37+00:00 · ADR-0068 lát A: 'evidence v3' mở rộng ở đâu?

- Phương án: (1) Chỉ hợp đồng phát hành: release-check --json thêm schema 3, subject (head, vân tay cây, digest artifact), artifacts[], results[] theo adapter (JUnit XML/SARIF/pip-audit JSON qua khoá xt.yaml <key>_report), promotion (approved/pending_human/rejected/blocked); evidence v2 của loop record giữ nguyên · (2) Cả evidence của loop record lên v3 (artifacts/results theo task) cùng hợp đồng phát hành
- Chọn: Chỉ hợp đồng phát hành: release-check --json thêm schema 3, subject (head, vân tay cây, digest artifact), artifacts[], results[] theo adapter (JUnit XML/SARIF/pip-audit JSON qua khoá xt.yaml <key>_report), promotion (approved/pending_human/rejected/blocked); evidence v2 của loop record giữ nguyên
- Lý do (tiêu chí chất lượng cuối): (1) đúng phần Xác nhận A của ADR-0068 (promotion + fixture âm ở release-check), không đổi nghĩa go/verdict/human/exit; (2) chỉ thêm trường, khoá xt.yaml mới tuỳ chọn — bỏ khoá là về hành vi cũ; (3) một nhà cho hợp đồng phát hành, không chạm đường verify của loop (đã ổn định, coverage 100 %); evidence v3 của loop chờ khi có nhu cầu đo theo task
- Đường lùi: Bỏ khoá <key>_report/release_artifacts trong xt.yaml: release-check chạy như trước; revert các commit lát A trên nhánh
- Đính chính số (khi gộp `main` #439, 2026-11-05): `main` đã cấp D-347/D-348/D-351 cho quyết định khác — D-350 của nhánh `claude/amazing-brahmagupta-9jqbg1` đánh số lại thành D-355 để không tái sử dụng ID.

### D-358 · 2026-11-04T22:54:48+00:00 · Duyệt PLAN-harden-2026-11-05 (harden nhánh claude/amazing-brahmagupta-9jqbg1, không PR/merge theo chủ dự án)?

- Phương án: (1) Duyệt: 5 task T-3680…3684 (🔴 F1 hai lớp, 🟠 F2/F3, tài liệu); nợ 🟢 ghi sổ; guard của main để phiên guard · (2) Chỉ ghi nợ mọi phát hiện ADR-0069, không sửa trên nhánh
- Chọn: Duyệt: 5 task T-3680…3684 (🔴 F1 hai lớp, 🟠 F2/F3, tài liệu); nợ 🟢 ghi sổ; guard của main để phiên guard
- Lý do (tiêu chí chất lượng cuối): (1) F1 là nới hàng rào so với main (agent duyệt bản đã đổi, sổ ghi người) — phải sửa trước khi nhánh tới main; sửa hai lớp (xt.py đòi bản còn nguyên, guard dạng chữ rõ chặt) đóng cả đường né biến môi trường; (2) mọi thay đổi là siết, khoá vắng = như cũ; (3) không đụng phần guard của #439 để tránh xung đột với phiên guard
- Đường lùi: Revert các commit T-3680…3684 trên nhánh; ADR-0069 về hành vi commit e295301

### D-359 · 2026-11-04T23:16:33+00:00 · Duyệt PLAN-factory-BE: phạm vi lát B–E ADR-0068 trên nhánh (không PR/merge)

- Phương án: (1) B gói web-api-ts tối giản (node:http + kysely/pg + RLS + vitest + biome, không Next.js) + CI lát dọc + 3 ca sai; C install.py --pack (starter chỉ repo sạch, managed theo manifest, drift, lùi bằng cài lại bản cũ) + chạy --plan trên bản clone hotel-manager; D worker cùng gói (trùng/timeout/crash/reconcile), fixture host thật hoãn (cần tài khoản trả phí của chủ); E registry JSON + xt.py registry + trang app · (2) Gói đầy đủ như hotel-manager (Next.js 16 + better-auth) và chạy codex thật để lấy fixture · (3) Chỉ làm B, hoãn C–E tới khi B merge
- Chọn: B gói web-api-ts tối giản (node:http + kysely/pg + RLS + vitest + biome, không Next.js) + CI lát dọc + 3 ca sai; C install.py --pack (starter chỉ repo sạch, managed theo manifest, drift, lùi bằng cài lại bản cũ) + chạy --plan trên bản clone hotel-manager; D worker cùng gói (trùng/timeout/crash/reconcile), fixture host thật hoãn (cần tài khoản trả phí của chủ); E registry JSON + xt.py registry + trang app
- Lý do (tiêu chí chất lượng cuối): (1) đúng/an toàn: không dùng tài khoản trả phí của chủ khi chưa được giao, không đụng repo đích (không PR); (2) đường lùi: gói là thư mục xoá được, --pack opt-in; (3) đơn giản/test được: gói nhỏ chạy được trong CI với Postgres thật, cùng thư viện lõi hotel-manager (kysely/pg/RLS/vitest/biome) nên C dùng chung; Next.js thêm bề mặt lớn không cần cho lát dọc API
- Đường lùi: xoá framework/templates/packs/, bỏ cờ --pack, xoá registry; ADR-0068 trạng thái về 'lát B–E chưa làm'
