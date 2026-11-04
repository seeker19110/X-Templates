# Nhật ký quyết định tự duyệt

> Ghi bởi `xt.py loop decide`. Phiên chính tự duyệt điểm quyết định theo tiêu chí chất lượng cuối (`LOOP-STOP-018`, ADR-0008 của khung). Người xem lại bất cứ lúc nào; đổi ý → quyết định mới ghi "thay D-NNN", không sửa mục cũ.
> Bản tháng trước: [`DECISIONS-2026-10.md`](DECISIONS-2026-10.md) (D-001…D-287), [`DECISIONS-2026-11.md`](DECISIONS-2026-11.md) (D-292…D-310) — máy đọc cả bản tháng (T-3651).

### D-311 · 2026-11-02T04:56:37+00:00 · AUD-XFEAT-039 (#401): PR Dependabot không ghi được review sạch — miễn luật năng lực cho tác giả bot thế nào?

- Phương án: (1) Không miễn: steward/người merge PR bot · (2) Miễn khi tác giả PR và MỌI commit không phải merge là bot tin cậy (TRUSTED_BOTS), kiểm qua REST đúng PR/head mà sổ ghi; reviewer chỉ cần họ model rõ · (3) Miễn theo login người mở PR
- Chọn: Miễn khi tác giả PR và MỌI commit không phải merge là bot tin cậy (TRUSTED_BOTS), kiểm qua REST đúng PR/head mà sổ ghi; reviewer chỉ cần họ model rõ
- Lý do (tiêu chí chất lượng cuối): Yêu cầu chủ dự án 2026-11-02 (mọi PR tự kiểm + tự merge). (1) an toàn: review #401 cho thấy phương án 3 né được bằng URL ghép/chữ số Unicode và commit người đẩy thêm; phương án 2 đóng cả hai. (3) đơn giản: dùng lại TRUSTED_BOTS của steward.
- Đường lùi: Bỏ nhánh TRUSTED_BOTS trong _review_models_error và _bot_author_error (scripts/xt.py), bỏ cờ trong pr-review.yml

### D-312 · 2026-11-02T16:17:51+00:00 · PR 401: sau review chặn ở 4b3ff99, mã đã đổi (bản sửa 🟠 AUD-SEC-353/354 ở 6886950 + gộp main xung đột _pr_reviewed với khoá sổ T-3648) — pr debt từ chối vì không có 🔴; đi tiếp thế nào? (#401)

- Phương án: (1) pr rethink: mở một lượt review mới ở head hiện tại (max_rethink 1), reviewer-alt rà toàn diff rồi pr reviewed · (2) Đổi mức hai dòng 🟠 thành 🔴 để pr debt --fixed nhận · (3) Để steward/người merge, phiên không đi tiếp
- Chọn: pr rethink: mở một lượt review mới ở head hiện tại (max_rethink 1), reviewer-alt rà toàn diff rồi pr reviewed
- Lý do (tiêu chí chất lượng cuối): (1) đúng và an toàn: mã sau review đổi thật ở đúng hàm vừa giải xung đột (_pr_reviewed + update_reviews) — cần một lượt rà độc lập ở head mới, không ghi nợ được; đổi mức để máy nhận là sửa lời khai cho khớp máy (phương án 2 sai P1); (2) giữ đường lùi: rethink dùng đúng trần max_rethink 1 (ADR-0061); chủ dự án yêu cầu 2026-11-02 giải xung đột và merge PR 401
- Đường lùi: Không review lại: đóng PR 401, mở PR mới từ main với cùng thay đổi và review một lần

### D-313 · 2026-11-02T16:18:45+00:00 · PR 401 kẹt sau D-312: pr rethink không mở lượt review (ADR-0062 trần 1), pr debt từ chối vì mã đổi sau review mà không có 🔴 — merge nội dung PR 401 thế nào? (#401)

- Phương án: (1) PR thay thế từ main: một commit = diff ròng của PR 401 (đã gộp main), review một lần ở head mới, đóng PR 401 kèm liên kết · (2) Đổi mức 🟠 AUD-SEC-353/354 thành 🔴 để pr debt --fixed nhận · (3) Revert bản sửa 🟠 ở PR 401 rồi ghi nợ
- Chọn: PR thay thế từ main: một commit = diff ròng của PR 401 (đã gộp main), review một lần ở head mới, đóng PR 401 kèm liên kết
- Lý do (tiêu chí chất lượng cuối): (1) đúng và an toàn: bản sửa 🟠 và phần giải xung đột ở _pr_reviewed chưa được rà — PR mới cho đúng một lượt review độc lập trên toàn diff; phương án 2 sửa lời khai cho khớp máy (sai P1); phương án 3 bỏ bản sửa an toàn đã có test. (2) đường lùi: PR 401 đóng chứ không xoá, mở lại được; chủ dự án yêu cầu 2026-11-02 giải xung đột và merge PR 401
- Đường lùi: Mở lại PR 401, đóng PR thay thế

### D-314 · 2026-11-02T19:44:29+00:00 · T-3651 DIR_CAPS cho docs/ops và docs/autopilot: có đếm file lưu trữ (AUDIT-STATUS-ARCHIVE.md, DECISIONS-YYYY-MM.md) vào trần không?

- Phương án: (1) Đếm cả file lưu trữ (trần = tổng sau lưu trữ + 5 %) · (2) Loại file lưu trữ khỏi pathspec; trần = file đang dùng + 5 %; lưu trữ đóng băng, không trần
- Chọn: Loại file lưu trữ khỏi pathspec; trần = file đang dùng + 5 %; lưu trữ đóng băng, không trần
- Lý do (tiêu chí chất lượng cuối): (1) đúng: mục tiêu AUD-DOC-180 là chặn sổ ĐANG ĐỌC/GHI phình (lint, audit check parse mỗi PR); đếm lưu trữ làm việc lưu trữ không bao giờ hạ tổng → trần chạm sau ~20 PR mà không có đường hợp lệ nào xuống dưới trừ xoá lịch sử (trái P1). (3) đơn giản: một pathspec loại trừ. Lưu trữ chỉ thêm khi chạy đợt lưu trữ có PR riêng
- Đường lùi: Bỏ hai pathspec :(exclude) và đặt trần theo tổng gồm lưu trữ

### D-315 · 2026-11-02T23:29:24+00:00 · AUD-DOC-183: D-303 ghi LOOP-HARNESS-022 → MUST@M nhưng ADR-0064/harness-files/CHANGELOG ghi MUST@L — đính chính mức nào?

- Phương án: (1) Giữ MUST@L, ghi D này đính chính D-303; ADR-0064 và CHANGELOG trỏ D-303 + D này · (2) Đổi sang MUST@M như chữ D-303
- Chọn: Giữ MUST@L, ghi D này đính chính D-303; ADR-0064 và CHANGELOG trỏ D-303 + D này
- Lý do (tiêu chí chất lượng cuối): (1) đúng: harness-files.md đã có 4 MUST trơn; MUST@M thành 5 MUST hiệu lực ở M, `xt.py validate` đỏ "trần 4" (ADR-0004, review orange-docs đã chạy). (3) theo chuẩn khung: trần MUST/module là luật. D-303 sai chữ, không sai ý (chủ dự án chọn bắt buộc khi chạy không người trực)
- Đường lùi: Hạ MUST khác của harness-files.md xuống SHOULD rồi đổi LOOP-HARNESS-022 sang MUST@M (cần D mới)

### D-316 · 2026-11-02T23:29:25+00:00 · AUD-DOC-194: T-3649 làm hàng release-check `go_no_go` BLOCKER ở mọi quy mô, khác PLAN (`go_no_go_file`, BLOCKER ở M/L, S = SHOULD) — giữ bản đã làm?

- Phương án: (1) Giữ: tên go_no_go, BLOCKER mọi quy mô; PLAN T-3649 ghi Đổi theo D này · (2) Sửa mã theo PLAN: S = SHOULD
- Chọn: Giữ: tên go_no_go, BLOCKER mọi quy mô; PLAN T-3649 ghi Đổi theo D này
- Lý do (tiêu chí chất lượng cuối): (1) đúng và an toàn: phát hành không có GO-NO-GO đã ký là lỗi ở mọi quy mô (3.29.0 thiếu file); chặt hơn PLAN. (3) đơn giản: một quy tắc; README, --help, mẫu GO-NO-GO đã khớp mã (orange-docs)
- Đường lùi: Thêm nhánh quy mô S → SHOULD trong _release_go_no_go

### D-317 · 2026-11-02T23:29:25+00:00 · AUD-DOC-228: validate --stale bỏ sót ~95 % ngày nguồn (dòng ghi đọc/rà YYYY-MM-DD) — sửa thế nào?

- Phương án: (1) (a) nới VERIFIED_AT_RE nhận đọc/rà, loại chưa/không … lại, 403 · (2) (b) chuẩn hoá ~248 dòng Nguồn sang chữ xác minh theo conventions §5 · (3) (c) chấp nhận có hạn — --stale chỉ tham khảo, không ở cổng
- Chọn: (c) chấp nhận có hạn — --stale chỉ tham khảo, không ở cổng
- Lý do (tiêu chí chất lượng cuối): (1) đúng: --stale không thuộc gate/CI nên không có xanh giả ở cổng; (a) đổi nghĩa 'xác minh' theo chữ tự do dễ đếm sai lần nữa (AUD-DOC-216), (b) chạm ~248 dòng ở nhiều module — làm cùng đợt nội dung AUD-DOC-179 (PLAN riêng). (5) chi phí: phá hoà
- Đường lùi: Làm (b) trong PLAN nội dung kế; hoặc (a) nếu đưa --stale vào cổng

### D-318 · 2026-11-02T23:50:44+00:00 · AUD-HAR-205 phần còn: loop run --agent host khác Claude chưa có cờ chế độ quyền — thêm cờ tự duyệt từng host hay mở --agent-args?

- Phương án: (1) Thêm cờ tự duyệt từng host (codex --full-auto, gemini --yolo, …) vào bảng lệnh · (2) Mở --agent-args cho người dùng tự truyền cờ; bảng lệnh không thêm cờ bỏ qua quyền; research cờ từng host rồi mới thêm · (3) Chấp nhận nợ, không làm
- Chọn: Mở --agent-args cho người dùng tự truyền cờ; bảng lệnh không thêm cờ bỏ qua quyền; research cờ từng host rồi mới thêm
- Lý do (tiêu chí chất lượng cuối): (1) an toàn: cờ tự duyệt chưa xác minh có thể là chế độ bỏ qua quyền (LOOP-STOP-028 cấm khung tự bật); cờ do người chạy truyền vào là quyết định của họ. (2) giữ đường lùi: thêm cờ đã research sau. Phần Claude đã sửa (--permission-mode auto). Việc này cần /research từng host nên làm sau PLAN này
- Đường lùi: Bỏ --agent-args

### D-319 · 2026-11-03T00:23:23+00:00 · Nhánh guard (#420): AUD-SEC-373 (sổ giai đoạn bảo vệ bằng liệt kê lệnh ghi) và AUD-SEC-374 (lời gọi thực thi sau literal lạ coi là trong chuỗi) — sửa tận gốc cần ADR; đóng PLAN thế nào? Kèm hệ quả chặn mới grep -rl … docs | xargs sed -i

- Phương án: (1) Chấp nhận có hạn 2027-01-31: ADR mới chọn bảo vệ theo tiền tố docs/ (như .autopilot/) hoặc vân tay sổ do xt.py stage ghi; tách literal theo họ trình thông dịch hoặc coi lời gọi trong vùng chưa chắc là lời gọi; nhận chặn mới (hướng chặt) · (2) Làm ngay trong PR này · (3) Để mở, chặn phát hành
- Chọn: Chấp nhận có hạn 2027-01-31: ADR mới chọn bảo vệ theo tiền tố docs/ (như .autopilot/) hoặc vân tay sổ do xt.py stage ghi; tách literal theo họ trình thông dịch hoặc coi lời gọi trong vùng chưa chắc là lời gọi; nhận chặn mới (hướng chặt)
- Lý do (tiêu chí chất lượng cuối): (1) an toàn: cả hai là giới hạn của cách liệt kê đã biết (ADR-0063) — bản sửa hiện tại đóng mọi dạng đã tái hiện; đổi mô hình bảo vệ là quyết định kiến trúc cần ADR + đo chặn oan trên kho lệnh thật, làm vội trong PR nợ dễ hồi quy (#372, ADR-0061). (2) giữ đường lùi: chấp nhận có hạn, chủ phiên chính. Chặn mới grep|xargs sed -i dưới docs là hướng chặt, đường thay thế: sửa từng file bằng Edit
- Đường lùi: Mở ADR sớm hơn và làm trước 3.30.0 nếu chủ dự án đòi

### D-320 · 2026-11-03T03:46:58+00:00 · T-3635: đóng 39 dòng nợ review còn mở sau hai lô sửa rẻ thế nào (24 chấp nhận, 2 bác bỏ, 2 đã sửa từ trước theo phân loại có bằng chứng; 11 sửa-ngay mà lô bỏ qua vì chạm file ngoài phạm vi lô)?

- Phương án: (1) Ghi theo phân loại; 11 dòng bỏ qua → chấp nhận hạn 2026-12-15 (đợt kế), chủ phiên chính · (2) Sửa nốt 11 dòng trong PR này · (3) Để mở
- Chọn: Ghi theo phân loại; 11 dòng bỏ qua → chấp nhận hạn 2026-12-15 (đợt kế), chủ phiên chính
- Lý do (tiêu chí chất lượng cuối): (1) đúng: mỗi dòng có lý do/bằng chứng phân loại đã chạy (reviewer agent, chỉ đọc); 11 dòng chưa sửa không được ghi đã sửa (P1). (2) giữ đường lùi: hạn ngắn, chủ rõ; PR này đã lớn (hai lô ~1.100 dòng), thêm sửa làm review kém (bài học #372). (3) audit check --strict nhận chấp nhận có chủ + hạn
- Đường lùi: Mở lại từng dòng (đổi chấp nhận → mở) khi có lô sửa

### D-321 · 2026-11-03T05:19:35+00:00 · AUD-SEC-388 lượt 2: 7 lệnh dạng n=$(…) + $((n±k)) + $var không nháy còn bị chặn (BUDGET) — giữ chặn hay tin lệnh chỉ in số (wc, date +%s, grep -c)?

- Phương án: (1) Giữ chặn; lý do chặn gợi viết "$var" · (2) Tin lệnh chỉ in số (heuristic)
- Chọn: Giữ chặn; lý do chặn gợi viết "$var"
- Lý do (tiêu chí chất lượng cuối): (1) an toàn: bash đánh giá đệ quy giá trị biến trong số học nên n=$(…) gán được IFS (đã tái hiện bash 5.2.21); danh sách lệnh 'chỉ in số' là danh sách trắng dễ lách (ADR-0063, bài học #372). (4) UX: đường viết thay một bước (nháy biến), đo 3884 lệnh thật chỉ 9 đổi quyết định
- Đường lùi: Thêm danh sách trắng lệnh đếm khi đo được chặn oan đáng kể

### D-322 · 2026-11-03T06:11:39+00:00 · PR 422: review tìm thêm 5 dạng lách IFS (function NAME { IFS=…}, "((" giả, từ lệnh có nháy, read định nghĩa trong eval, IFS=… exec read) — base cũng lọt cả 5; vá tiếp trong PR hay đổi cách?

- Phương án: (1) Vá tiếp 5 dạng trong PR này (lần thứ tư) · (2) Merge PR (chặt hơn base, không mở đường mới — ADR-0056); AUD-SEC-388 trả về mở, liệt kê dạng còn lọt; PR kế: ADR mới — luật chung theo ADR-0063: mọi gán IFS/tên-đích-động có mặt thì mọi mở rộng không đọc chắc → BUDGET, chỉ một mẫu cho phép neo chặt (while IFS= read -r v … "$v"), không suy theo cấu trúc · (3) Chấp nhận lớp IFS là giới hạn đã biết, giao sandbox
- Chọn: Merge PR (chặt hơn base, không mở đường mới — ADR-0056); AUD-SEC-388 trả về mở, liệt kê dạng còn lọt; PR kế: ADR mới — luật chung theo ADR-0063: mọi gán IFS/tên-đích-động có mặt thì mọi mở rộng không đọc chắc → BUDGET, chỉ một mẫu cho phép neo chặt (while IFS= read -r v … "$v"), không suy theo cấu trúc
- Lý do (tiêu chí chất lượng cuối): (1) an toàn: ba lượt vá theo cấu trúc lệnh đều lọt dạng mới (#372, ADR-0061 max_rethink) — hội tụ cần đổi mô hình (danh sách trắng, không suy cấu trúc), là quyết định kiến trúc → ADR; head chặn mọi dạng đã biết trước đó, 5 dạng mới base cũng lọt nên merge không làm tệ hơn. (2) giữ đường lùi: 🔴 vẫn mở ở sổ → release-check chặn phát hành tới khi xong. Phương án 3 trái tiêu chí 1 khi sandbox chưa bắt buộc ở mọi quy mô
- Đường lùi: Đóng PR 422, gom vào PR ADR mới

### D-323 · 2026-11-03T09:50:44+00:00 · AUD-SEC-388 sau ADR-0065 (sửa review lượt 2 đóng dạng toán hạng có nháy): giữ đã sửa hay trả về mở?

- Phương án: (1) Giữ đã sửa; review 1 lần của PR #423 (ADR-0062, reviewer-alt) là review độc lập lượt 3 — 🔴 mới thì sửa trong PR, không ghi nợ · (2) Trả về mở tới khi có review riêng lượt 3 rồi mới mở PR
- Chọn: Giữ đã sửa; review 1 lần của PR #423 (ADR-0062, reviewer-alt) là review độc lập lượt 3 — 🔴 mới thì sửa trong PR, không ghi nợ
- Lý do (tiêu chí chất lượng cuối): (1) đúng/an toàn: review đối kháng của PR vẫn chặn merge nếu còn dạng lọt (🔴 không thành nợ); (3) đơn giản: không tạo thêm vòng ngoài luồng review 1 lần; mọi dạng của review lượt 1-2 có test đỏ trước
- Đường lùi: Đổi hàng AUD-SEC-388 về mở trong sổ nếu review #423 hoặc audit sau tìm dạng lọt

### D-324 · 2026-11-03T11:38:52+00:00 · AUD-SEC-400 (ghi script rồi chạy cùng lệnh) chặn oan 6,8 % lệnh thật (260 dạng cat > f <<'EOF' … EOF; python3 f): giữ chặn hay quét thân heredoc có nháy như script?

- Phương án: (1) A: giữ chặn mọi ghi-rồi-chạy cùng lệnh; viết lại bằng Write rồi chạy ở lệnh riêng · (2) B: khi cat/tee là nơi duy nhất ghi tệp bằng > từ heredoc CÓ NHÁY và tệp được shell/trình thông dịch chạy cùng lệnh, guard quét thân heredoc như script của trình đó (như bash <<'EOF' / python3 - <<'EOF'); mọi dạng khác giữ chặn
- Chọn: B: khi cat/tee là nơi duy nhất ghi tệp bằng > từ heredoc CÓ NHÁY và tệp được shell/trình thông dịch chạy cùng lệnh, guard quét thân heredoc như script của trình đó (như bash <<'EOF' / python3 - <<'EOF'); mọi dạng khác giữ chặn
- Lý do (tiêu chí chất lượng cuối): (1) an toàn hơn A: A chỉ đẩy nội dung sang lệnh riêng mà guard không đọc tệp, B quét thật nội dung (bắt cả cat > x.sh <<'EOF' rm -rf ~ mà base cho qua); (4) gỡ ~260 chặn oan; (3) dùng lại đường quét heredoc sẵn có, không suy cấu trúc mới — đúng tinh thần ADR-0065 (miễn theo giá trị chắc chắn)
- Đường lùi: Bỏ nhánh miễn B trong _script_run_why, trả fixture d270 về BUDGET

### D-325 · 2026-11-03T12:02:49+00:00 · T-3635: 5 nợ review 🟢 còn mở cần sửa mã/thử nghiệm (AUD-SEC-376 cần PR thử trên GitHub, HAR-216 go_no_go fence, HAR-217 argparse --agent-args, HAR-218 research cờ host, SEC-381 danger prompt-assets) — sửa ngay trước 3.30.0 hay chấp nhận có hạn?

- Phương án: (1) Chấp nhận có hạn 2027-01-21 (chủ: phiên chính), lý do từng dòng; sửa ở PLAN sau 3.30.0 · (2) Sửa cả 5 trước khi cắt 3.30.0
- Chọn: Chấp nhận có hạn 2027-01-21 (chủ: phiên chính), lý do từng dòng; sửa ở PLAN sau 3.30.0
- Lý do (tiêu chí chất lượng cuối): (2) giữ đường lùi + (5) tốc độ: cả 5 là 🟢, không lùi so với base, không chặn hành động nguy hiểm mới; 376 cần dựng PR thử (ra khỏi máy), 218 cần /research — không làm trong lát khép PLAN; T-3635 cho phép chấp nhận (chủ + hạn)
- Đường lùi: Đổi các dòng về mở và thêm task vào PLAN kế

### D-326 · 2026-11-03T12:37:03+00:00 · Review #426: 🔴 AUD-SEC-399/400 khai đóng sớm (miễn D-324 quét sai thư mục/stdin/uniq, /dev/shm; mảng chữ nguyên văn và $@ không áp luật) + lỗ liệt kê trình chạy/writer có từ trước (python3 -m, PATH=., iconv -o, …) — xử lý thế nào?

- Phương án: (1) Sửa mọi dạng do mã mới cho qua (D-324 thu hẹp: không miễn khi có cd/pushd/popd, stdin/here-string/đối số của trình chạy, writer ngoài cat/tee; /dev/ chỉ bỏ null/std*/fd/tty; mảng chữ thay phần tử vào argv rồi áp luật, $@ sau set --/hàm là mảng nhiễm) thành ID 🔴 mới đã sửa; lỗ liệt kê có từ trước ghi ID 🔴 mở riêng (chặn phát hành, PLAN kế); 🟠/🟢 sửa luôn · (2) Bỏ hẳn miễn D-324 và mọi phần 399 mới, trả 399/400 về mở
- Chọn: Sửa mọi dạng do mã mới cho qua (D-324 thu hẹp: không miễn khi có cd/pushd/popd, stdin/here-string/đối số của trình chạy, writer ngoài cat/tee; /dev/ chỉ bỏ null/std*/fd/tty; mảng chữ thay phần tử vào argv rồi áp luật, $@ sau set --/hàm là mảng nhiễm) thành ID 🔴 mới đã sửa; lỗ liệt kê có từ trước ghi ID 🔴 mở riêng (chặn phát hành, PLAN kế); 🟠/🟢 sửa luôn
- Lý do (tiêu chí chất lượng cuối): (1) đóng mọi lỗ do PR này mở ra, ghi trung thực phần còn lại (không khai đóng sớm — bài học #423); (4) giữ gỡ chặn oan D-324; lỗ liệt kê là giới hạn mô hình danh sách đen, cần ADR riêng (sandbox/allowlist trình chạy) — không vá tiếp trong lát này
- Đường lùi: Revert commit sửa review #426

### D-327 · 2026-11-03T13:21:18+00:00 · AUD-SEC-406: lỗ liệt kê trình chạy/trình ghi của luật ghi-rồi-chạy (AUD-SEC-400) — đóng bằng cách nào; và chặn oan 'cd trước cat > f' của D-326?

- Phương án: (1) Vá tiếp danh sách trình chạy/trình ghi · (2) ADR-0066: xét theo TÊN tệp đích ghi được nhắc lại ở chỗ khác của lệnh (trừ lệnh chỉ đọc trong danh sách trắng với tệp không đuôi script), thêm -o/--output và đích ghi của bộ quét script; miễn D-324 chỉ mất khi cd nằm giữa ghi và chạy · (3) Bắt buộc sandbox Claude Code
- Chọn: ADR-0066: xét theo TÊN tệp đích ghi được nhắc lại ở chỗ khác của lệnh (trừ lệnh chỉ đọc trong danh sách trắng với tệp không đuôi script), thêm -o/--output và đích ghi của bộ quét script; miễn D-324 chỉ mất khi cd nằm giữa ghi và chạy
- Lý do (tiêu chí chất lượng cuối): (1) không phụ thuộc danh sách trình chạy — lệnh lạ bị tính (hướng an toàn); sandbox không chặn force-push qua mạng; (4) gỡ chặn oan cd-trước của D-326; (3) dùng dữ liệu đích ghi sẵn có, không suy cấu trúc mới (ADR-0065)
- Đường lùi: Revert PR triển khai; AUD-SEC-406 về mở

### D-328 · 2026-11-03T14:26:55+00:00 · ADR-0066 chặn mới 340/5237 lệnh (6,5 %): giữ nguyên, thêm lệnh không chạy mã vào danh sách trắng (B), miễn tệp dữ liệu đưa cho script có sẵn (C), hay B+C? Giữ 3 miễn theo giá trị (p.json đối số dữ liệu của -c chỉ đọc; tên gốc bỏ đuôi không tính với đuôi dữ liệu; tệp nội dung gh -F/--body-file/< F)?

- Phương án: (1) A: giữ nguyên · (2) B: thêm mkdir/echo/printf/chmod/sha*sum/md5sum/touch/sed -n chỉ in vào danh sách trắng; giữ 3 miễn theo giá trị · (3) B+C: thêm cả miễn tệp dữ liệu cho script có sẵn
- Chọn: B: thêm mkdir/echo/printf/chmod/sha*sum/md5sum/touch/sed -n chỉ in vào danh sách trắng; giữ 3 miễn theo giá trị
- Lý do (tiêu chí chất lượng cuối): (1) B chỉ thêm lệnh không chạy mã — không mở đường thực thi; C đảo phần AUD-SEC-407 vừa siết và tin vào nội dung script có sẵn (có thể exec đối số) → loại; 3 miễn theo giá trị có kiểm _read_only_script/đuôi dữ liệu/đọc nội dung — giữ (giữ 6 ca D-270); (4) bớt chặn oan ~24 ca
- Đường lùi: Bỏ các lệnh B khỏi danh sách trắng

### D-329 · 2026-11-03T15:12:36+00:00 · #427 review chặn: 7 🔴 (3 hồi quy do miễn mới — AUD-SEC-410 trả sớm mở lại find . -delete qua rebase --exec/make --eval; D-324 cd bỏ mất gán CDPATH; -oVALUE dính; 3 lỗ miễn mới — perl do $ARGV, chiếm tên lệnh đọc qua PATH, LESSOPEN/GIT_EXTERNAL_DIFF; AUD-SEC-406 khai đóng sai với tên dựng lúc chạy) — đổi chiến lược thế nào (max_rethink, ADR-0061)?

- Phương án: (1) Vá tiếp từng 🔴 trong PR · (2) Thu PR về luật CHẶN, bỏ/siết mọi miễn mới: AUD-SEC-410 về hành vi base (bỏ trả sớm); D-324 về hành vi #426 (có cd/pushd/popd/gán biến trước writer là mất miễn); _reuse_data_arg chỉ họ python; lệnh đọc mất miễn khi tên lệnh trùng tên gốc tệp vừa ghi hoặc lệnh có gán/export biến (GIT_*, LESS*, PATH), bỏ less; -o đọc cụm cờ kiểu getopt (miễn git grep theo n[:2]); AUD-SEC-406 giữ MỞ (tên dựng lúc chạy) — T-3635 bỏ tick, sửa câu ADR · (3) Đóng PR, giữ AUD-SEC-406 mở
- Chọn: Thu PR về luật CHẶN, bỏ/siết mọi miễn mới: AUD-SEC-410 về hành vi base (bỏ trả sớm); D-324 về hành vi #426 (có cd/pushd/popd/gán biến trước writer là mất miễn); _reuse_data_arg chỉ họ python; lệnh đọc mất miễn khi tên lệnh trùng tên gốc tệp vừa ghi hoặc lệnh có gán/export biến (GIT_*, LESS*, PATH), bỏ less; -o đọc cụm cờ kiểu getopt (miễn git grep theo n[:2]); AUD-SEC-406 giữ MỞ (tên dựng lúc chạy) — T-3635 bỏ tick, sửa câu ADR
- Lý do (tiêu chí chất lượng cuối): (1) gỡ mọi hồi quy và lỗ do miễn mới, giữ phần chặn đã chứng minh; khai trung thực 406 còn mở (bài học #423/#426); (2) đường lùi: revert PR; vá tiếp từng 🔴 (phương án 1) là mô hình #372 không điểm dừng
- Đường lùi: Đóng PR #427, revert về main

### D-330 · 2026-11-03T15:40:20+00:00 · docs/ops còn 6 B dưới trần (ADR-0043) và mọi dòng đã sửa có ở tag v3.29.0 đã lưu trữ hết — lấy chỗ cho sổ nợ review #427 thế nào?

- Phương án: (1) Nới trần docs/ops · (2) Lưu trữ đợt 2: dòng đã sửa có nguyên văn trên origin/main (PR sửa đã merge), cũ nhất trước, dời nguyên văn sang AUDIT-STATUS-ARCHIVE.md; ghi tiêu chí mới ở đầu file lưu trữ · (3) Rút gọn chữ các dòng đang mở
- Chọn: Lưu trữ đợt 2: dòng đã sửa có nguyên văn trên origin/main (PR sửa đã merge), cũ nhất trước, dời nguyên văn sang AUDIT-STATUS-ARCHIVE.md; ghi tiêu chí mới ở đầu file lưu trữ
- Lý do (tiêu chí chất lượng cuối): (1)(3) không nới cổng (LOOP-CI-001), không sửa chữ người khác; dòng đã sửa trên main là lịch sử đóng băng, máy đọc cả hai file; tiêu chí tag chỉ là mốc thuận tiện, mốc main vẫn bất biến
- Đường lùi: Dời các dòng về AUDIT-STATUS.md

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
