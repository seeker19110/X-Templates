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

### D-356 · 2026-11-04T22:53:05+00:00 · T-3551: chốt ADR-0071 perf trial — 14 điểm hở của bản nháp (ID FLOW, nơi đo candidate, nguồn cấu hình, kiểm trỏ đúng cây, start khi HEAD lệch cây giữ, held-out, falsifier, PERF-LOG, --resume, neo công cụ chấm, sửa file khoá, khoá điểm nóng, đo xen kẽ)

- Phương án: (1) Nhận cả 14 đề xuất của bản nháp: FLOW giữ nghĩa nghiên cứu §10 cho 20…23, ca mới FLOW-27…34; candidate đo ở worktree dựng lại; cấu hình JSON đọc từ commit gốc; kiểm trỏ đúng cây bằng probe + quét .pth/symlink; từ chối start khi HEAD^{tree} ≠ kept_tree; held-out hạt giống lúc finish, phải improved; falsifier trúng → thu hồi; PERF-LOG miễn khi chỉ nối thêm; --resume R1 rơi về R2; công cụ chấm neo cả exec blob gốc lẫn Gate <(git show); sửa file khoá → thu hồi + tính lượt; khoá điểm nóng theo đường file + kiểm diff; luôn đo xen kẽ · (2) Giữ phương án B cho ID FLOW (đổi nghĩa FLOW-20…23 theo PLAN) và đo candidate tại chỗ cho rẻ hơn
- Chọn: Nhận cả 14 đề xuất của bản nháp: FLOW giữ nghĩa nghiên cứu §10 cho 20…23, ca mới FLOW-27…34; candidate đo ở worktree dựng lại; cấu hình JSON đọc từ commit gốc; kiểm trỏ đúng cây bằng probe + quét .pth/symlink; từ chối start khi HEAD^{tree} ≠ kept_tree; held-out hạt giống lúc finish, phải improved; falsifier trúng → thu hồi; PERF-LOG miễn khi chỉ nối thêm; --resume R1 rơi về R2; công cụ chấm neo cả exec blob gốc lẫn Gate <(git show); sửa file khoá → thu hồi + tính lượt; khoá điểm nóng theo đường file + kiểm diff; luôn đo xen kẽ
- Lý do (tiêu chí chất lượng cuối): (1) spike đo được: đo theo khối 18 % improved sai trong A/A, đo tại chỗ bị .pth bị ignore lừa — các phương án chặt hơn chặn cả hai; (3) ID ổn định theo conventions (không đổi nghĩa ID đã dùng); (2) mỗi task một PR, perf trial là lệnh mới, Gate mẫu cũ giữ nguyên làm đường lùi; chi phí +0,8 s/cây chỉ phá hoà (5)
- Đường lùi: Gỡ skill /optimize khỏi perf trial, quay về Gate mẫu perf-gate.sh; finish --no-apply là lối tạm

### D-357 · 2026-11-04T22:54:48+00:00 · T-3680…T-3687 (perf trial, ADR-0071): mỗi task một PR (8 PR) hay gộp?

- Phương án: (1) 4 PR, mỗi PR hai task liền kề (3680+3681, 3682+3683, 3684+3685, 3686+3687), mỗi task một commit, nhánh xếp chồng, gộp origin/main sau mỗi merge (không force-push) · (2) 8 PR, mỗi task một PR như PLAN
- Chọn: 4 PR, mỗi PR hai task liền kề (3680+3681, 3682+3683, 3684+3685, 3686+3687), mỗi task một commit, nhánh xếp chồng, gộp origin/main sau mỗi merge (không force-push)
- Lý do (tiêu chí chất lượng cuối): (3) mỗi PR ~300–400 dòng vẫn review trọn được (review #439 ~1100 dòng chạm trần lượt); tiền lệ D-244 gộp T-3548…T-3550; (2) mỗi task một commit nên revert từng task được; (5) giảm nửa số vòng CI + review
- Đường lùi: Tách lại theo task nếu reviewer báo PR quá lớn (INCONCLUSIVE)

### D-360 · 2026-11-04T23:33:14+00:00 · Review #440 (ADR-0071) 4 🔴: (1) agent tự chọn baseline qua --base/vòng mới; (2) start bỏ qua kiểm cây, held-out chỉ so start_head; (3) PERF-LOG miễn ở start nhưng nằm trong candidate_files/vân tay → kẹt sau 2 lần thu hồi; (4) điểm nóng mồi reset bộ đếm ba lần. Kèm đính chính D-357 (repo squash-merge nên không revert được theo task).

- Phương án: (1) Sửa chặt: (1) base = merge-base(HEAD, nhánh mặc định được bảo vệ) do máy tính, bỏ --base, vòng mới chỉ khi merge-base đổi; (2) bỏ 'hoặc bỏ qua', finish kiểm file khoá không đổi base..start_head và held-out so cả với base; (3) PERF-LOG dựng từ perf-trials.jsonl bằng 'perf trial log', start/finish không ghi cây, bỏ miễn; (4) điểm nóng là danh sách đường chuẩn hoá (bỏ ::SYM), file candidate ngoài điểm nóng → thu hồi off-hotspot, start exit 3 nếu bất kỳ đường nào đã cạn · (2) Giữ --base nhưng ghim lúc loop init của PLAN-opt; PERF-LOG loại nhất quán khỏi candidate_files/vân tay/kept_tree; đếm ba lần theo hợp các điểm nóng
- Chọn: Sửa chặt: (1) base = merge-base(HEAD, nhánh mặc định được bảo vệ) do máy tính, bỏ --base, vòng mới chỉ khi merge-base đổi; (2) bỏ 'hoặc bỏ qua', finish kiểm file khoá không đổi base..start_head và held-out so cả với base; (3) PERF-LOG dựng từ perf-trials.jsonl bằng 'perf trial log', start/finish không ghi cây, bỏ miễn; (4) điểm nóng là danh sách đường chuẩn hoá (bỏ ::SYM), file candidate ngoài điểm nóng → thu hồi off-hotspot, start exit 3 nếu bất kỳ đường nào đã cạn
- Lý do (tiêu chí chất lượng cuối): (1) phương án 1 đóng cả bốn đường lách bằng dữ kiện agent không sửa được (nhánh bảo vệ cần review để đổi; sổ jsonl do máy ghi) — phương án 2 còn phụ thuộc state agent đọc/ghi được và loại trừ đặc biệt dễ sót; (3) ít luật hơn, test được. D-357 đính chính: mỗi task một commit chỉ giúp đọc/bisect trên nhánh, squash-merge làm revert theo PR; lý do giữ gộp 4 PR là (3)/(5) cỡ review và số vòng CI
- Đường lùi: Giữ --base với ghim lúc loop init (phương án 2) nếu dự án đích không có nhánh mặc định được bảo vệ

### D-361 · 2026-11-05T00:00:58+00:00 · ADR-0071 sau review #440: sáu chi tiết ngoài D-360 — lệnh prepare, mã thoát 4, Gate status --check, cây đo bằng clone --shared, khoá cả pyproject.toml/package.json, nhánh mặc định lấy từ origin/HEAD

- Phương án: (1) Nhận năm chi tiết như bản sửa (prepare riêng; exit 4; Gate perf trial status --check theo target; clone --shared để mã candidate không thấy cây gốc qua git worktree list — T-3702 đo, chậm/hỏng thì về worktree add và ghi giới hạn; khoá cả file pyproject.toml/package.json); riêng nhánh mặc định: lấy từ máy chủ (git ls-remote --symref origin HEAD) khi có mạng, ngoại tuyến mới dùng refs/remotes/origin/HEAD và guard phải chặn git remote set-head/ghi refs/remotes (T-3701 thêm test guard) · (2) Nhận nguyên sáu đề xuất, origin/HEAD cục bộ là nguồn nhánh mặc định
- Chọn: Nhận năm chi tiết như bản sửa (prepare riêng; exit 4; Gate perf trial status --check theo target; clone --shared để mã candidate không thấy cây gốc qua git worktree list — T-3702 đo, chậm/hỏng thì về worktree add và ghi giới hạn; khoá cả file pyproject.toml/package.json); riêng nhánh mặc định: lấy từ máy chủ (git ls-remote --symref origin HEAD) khi có mạng, ngoại tuyến mới dùng refs/remotes/origin/HEAD và guard phải chặn git remote set-head/ghi refs/remotes (T-3701 thêm test guard)
- Lý do (tiêu chí chất lượng cuối): (1) origin/HEAD cục bộ do agent đổi được bằng git remote set-head → chọn lại baseline, đúng lỗ 🔴1 mà D-360 đóng; nguồn máy chủ không đổi được nếu không có quyền admin repo; (1) khoá cả file chặt hơn khoá mục; (3) prepare/exit 4/status --check tách hành vi để mỗi task có Gate riêng, test được
- Đường lùi: Dùng origin/HEAD cục bộ (phương án 2) nếu dự án đích thường chạy ngoại tuyến và guard đã chặn set-head

### D-362 · 2026-11-05T00:17:42+00:00 · Review #441 (trả nợ #439) lại BLOCKING: 1 🔴 do diff (AUD-SEC-496 dò Git dir dừng ở thư mục con khi guard thừa hưởng GIT_OBJECT_DIRECTORY mà lệnh gỡ biến), 2 🟠 (AUD-SEC-493 heredoc/here-string có chuyển hướng thành UNSEEN; quyết định phụ thuộc kiểu stdin /dev/./stdin), 5 🟢, 4 có từ trước (🔴 /dev/./stdin không chuẩn hoá trong STDIN_SCRIPTS; 🟠 env -S; 🟠 . ./script có sẵn chứa cd; 🟢 giới hạn D-106 cd "$X"; ..) — vòng review guard không hội tụ, làm sao cắt 3.30.0?

- Phương án: (1) Sửa trong #441: hai 🔴 (dò cả hai nhánh có/không objdir, chặn nếu nhánh nào gặp khoá nguy hiểm; chuẩn hoá đường /dev, /proc trong STDIN_SCRIPTS và đường nguồn), hai 🟠 (heredoc có nháy/here-string giải như eval kể cả khi có chuyển hướng thêm; mọi đường dưới /dev hay /proc là UNSEEN sau chuẩn hoá), 🟢 chặn oan tar/unzip (repo chờ '' chỉ khi có repo trần chờ thật), gỡ FD_SCRIPT_RE trùng (giữ một định nghĩa + test), sửa chữ sổ/CHANGELOG; chấp nhận có hạn 2027-01-21 (ADR-0067): 🟢 mở rộng tên khớp với tập phủ định cpio (chưa thấy lỗ), 🟢 AUD-PERF-019 cách giảm khác, 🟠 env -S, 🟠 source script có sẵn chứa cd (guard không quét nội dung script — giới hạn đã ghi ở PROGRESS), 🟢 D-106 cd "$X" + .. · (2) Sửa hết mọi mục kể cả có từ trước rồi review lại
- Chọn: Sửa trong #441: hai 🔴 (dò cả hai nhánh có/không objdir, chặn nếu nhánh nào gặp khoá nguy hiểm; chuẩn hoá đường /dev, /proc trong STDIN_SCRIPTS và đường nguồn), hai 🟠 (heredoc có nháy/here-string giải như eval kể cả khi có chuyển hướng thêm; mọi đường dưới /dev hay /proc là UNSEEN sau chuẩn hoá), 🟢 chặn oan tar/unzip (repo chờ '' chỉ khi có repo trần chờ thật), gỡ FD_SCRIPT_RE trùng (giữ một định nghĩa + test), sửa chữ sổ/CHANGELOG; chấp nhận có hạn 2027-01-21 (ADR-0067): 🟢 mở rộng tên khớp với tập phủ định cpio (chưa thấy lỗ), 🟢 AUD-PERF-019 cách giảm khác, 🟠 env -S, 🟠 source script có sẵn chứa cd (guard không quét nội dung script — giới hạn đã ghi ở PROGRESS), 🟢 D-106 cd "$X" + ..
- Lý do (tiêu chí chất lượng cuối): (1) sửa mọi 🔴 và 🟠 thuộc diff, cùng 🔴 có từ trước rẻ (chuẩn hoá đường); phần còn lại là giới hạn phân tích tĩnh đã được ADR-0067 chấp nhận có hạn — hàng rào lớp hai (sandbox) xét trước 2027-01-21; (2) mỗi mục chấp nhận có dòng sổ + hạn, không ẩn; (5) phương án 2 không hội tụ (D-347: bốn lượt review liên tiếp đều lộ lỗ mới), chặn phát hành 3.30.0 vô hạn
- Đường lùi: Mở lại dòng chấp nhận thành mở và sửa trong PR guard kế tiếp

### D-364 · 2026-11-05T01:20:18+00:00 · Sửa #441 lộ thêm hai lỗ có từ trước: (1) ghi qua thư mục mở trên fd — printf x > /dev/fd/3/guard.py 3< .claude/hooks (guard bỏ qua đích dưới /dev/); (2) bash ./link <<'EOF' với link → /dev/stdin (_stdin_shell không lần symlink theo thư mục chạy)

- Phương án: (1) (1) sửa ngay: đích có tiền tố /dev/fd/N/…, /dev/std*/…, /proc/*/fd/N/… coi là thư mục không biết (D-106), áp _where lên phần đuôi (AUD-SEC-521); (2) chấp nhận có hạn 2027-01-21 theo ADR-0067, cùng lớp AUD-SEC-519 (AUD-SEC-522) · (2) Chặn thẳng mọi đích ghi đi qua fd và sửa cả (2) bằng truyền thư mục ứng viên vào _stdin_shell
- Chọn: (1) sửa ngay: đích có tiền tố /dev/fd/N/…, /dev/std*/…, /proc/*/fd/N/… coi là thư mục không biết (D-106), áp _where lên phần đuôi (AUD-SEC-521); (2) chấp nhận có hạn 2027-01-21 theo ADR-0067, cùng lớp AUD-SEC-519 (AUD-SEC-522)
- Lý do (tiêu chí chất lượng cuối): (1) lỗ (1) ghi được hook nên sửa; cách (a) chặt mà gần như không chặn oan (4) — chặn thẳng thô hơn; (2) cần sửa nhiều chỗ gọi, cùng lớp giới hạn đã chấp nhận ở D-362 — (5) không chặn 3.30.0
- Đường lùi: Chặn thẳng mọi đích ghi qua fd nếu (a) lọt biến thể
