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
