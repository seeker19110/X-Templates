# Nhật ký quyết định tự duyệt

> Ghi bởi `xt.py loop decide`. Phiên chính tự duyệt điểm quyết định theo tiêu chí chất lượng cuối (`LOOP-STOP-018`, ADR-0008 của khung). Người xem lại bất cứ lúc nào; đổi ý → quyết định mới ghi "thay D-NNN", không sửa mục cũ.
> Bản tháng trước: [`DECISIONS-2026-10.md`](DECISIONS-2026-10.md) (D-001…D-287) — máy đọc cả bản tháng (T-3651).

### D-292 · 2026-11-01T03:17:20+00:00 · Duyệt PLAN-upgrade-2026-11-01 (ADR-0061 Adaptive Agent theo nhận định chủ dự án; stored ưu tiên 1-3; sửa batch audit delta) và cách máy hoá ADR-0061

- Phương án: (1) Bảng topology máy đọc, mặc định self, giữ hai tầng executor cho parallel, đợt 4, rethink tối đa 1 mỗi PR, thêm KPI thời gian vào loop stats; 7 lát mỗi lát một PR, tự làm (topo self), lát chạm harness topo review · (2) Giữ mặc định giao executor và chờ số đo LOOP-ORCH-020 như ADR-0045 · (3) Bỏ hẳn executor và executor-deep, chỉ một agent cộng reviewer
- Chọn: Bảng topology máy đọc, mặc định self, giữ hai tầng executor cho parallel, đợt 4, rethink tối đa 1 mỗi PR, thêm KPI thời gian vào loop stats; 7 lát mỗi lát một PR, tự làm (topo self), lát chạm harness topo review
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1: khớp thực tế vận hành phiên 2026-10-31 và dữ kiện sống 2026-11-01 (Harness design: đơn giản nhất, chỉ tăng khi cần; ROI: cost per task, PR cycle time); tiêu chí 2: đường lùi một dòng topo parallel trả hành vi cũ; tiêu chí 3: số đo LOOP-ORCH-020 vẫn chạy và có thêm trục thời gian; chủ dự án có quyền cuối, số 4 và 1 rethink ghi là khởi điểm tự đặt; phương án 2 không bao giờ có số, phương án 3 mất chuyển cấp ADR-0029
- Đường lùi: Revert PR từng lát; PLAN ghi topo parallel cho mọi task; max_rethink 0

### D-293 · 2026-11-01T04:33:04+00:00 · T-3606: khung chưa có scanner prompt-assets-scan (chỉ bảng ai-security.md:106 trỏ script dự án đích) — lát này làm gì?

- Phương án: (1) Tài liệu trước: SEC-AI-018 thêm luật XT-H-024 (lời bỏ xác nhận/không từ chối, gói không ghim, quét README/docs), CMP-LIC-024 mới cho XT-H-026; scanner thành T-3613 đợt kế (lát ≤ 150 dòng, mỗi lát một PR) · (2) Hiện thực xt.py prompt-assets-scan ngay (4 luật cũ + 2 mới + miễn trừ + test, ~300 dòng) trong lát này
- Chọn: Tài liệu trước: SEC-AI-018 thêm luật XT-H-024 (lời bỏ xác nhận/không từ chối, gói không ghim, quét README/docs), CMP-LIC-024 mới cho XT-H-026; scanner thành T-3613 đợt kế (lát ≤ 150 dòng, mỗi lát một PR)
- Lý do (tiêu chí chất lượng cuối): Đúng/an toàn ngang nhau (luật đã có nhà, scanner là công cụ cưỡng chế); phương án 1 nhỏ, đảo ngược được, đúng trần lát của ADR-0061; scanner là feature riêng cần spec miễn trừ + fixture, ghi task T-3613 kèm Gate test
- Đường lùi: Bỏ T-3613, sửa lại chữ SEC-AI-018/CMP-LIC-024 về bản trước (giữ ID)

### D-294 · 2026-11-01T04:46:03+00:00 · ADR-0060 (sáu skill theo tác vụ, #365) chưa có D-NNN — ghi hồi tố cách nào? (AUD-DOC-133)

- Phương án: (1) Ghi D-NNN hồi tố 2026-11-01 xác nhận phiên chính đã tự duyệt ADR-0060 theo tiêu chí chất lượng cuối; dòng Trạng thái ADR-0060 dẫn D-NNN kèm chữ 'hồi tố' · (2) Để trống, coi ADR-0060 là quyết định của chủ repo (yêu cầu 2026-10-31) không cần D-NNN
- Chọn: Ghi D-NNN hồi tố 2026-11-01 xác nhận phiên chính đã tự duyệt ADR-0060 theo tiêu chí chất lượng cuối; dòng Trạng thái ADR-0060 dẫn D-NNN kèm chữ 'hồi tố'
- Lý do (tiêu chí chất lượng cuối): AGENTS.md §4: quyết định chuyên môn phiên chính tự duyệt phải có D-NNN; ADR-0060 là thiết kế (chọn 6 skill, mẫu) dù yêu cầu từ chủ repo; ghi hồi tố giữ dấu vết, không sửa lịch sử
- Đường lùi: Xoá câu dẫn D-NNN ở ADR-0060 (giữ mục D trong sổ)

### D-295 · 2026-11-01T11:05:35+00:00 · Máy hoá cấu hình review/merge mới của chủ dự án 2026-11-01 (review 1 lần, 3 mức rủi ro, cổng production) cho khung và dự án đích thế nào?

- Phương án: (1) ADR-0062 thay ADR-0059 §1-2: review 1 lần; 🔴 sửa trong 1 commit rồi pr debt --fixed (không review lại), 🟠/🟢 ghi nợ; rủi ro thấp = làn nhanh (CI + tự rà diff, máy merge ghim head); trung bình = làn chuẩn, 1 review logic/phạm vi/test; cao = ngoại lệ cứng + schema/migration, review độc lập bắt buộc kể cả pha build; release-check thêm hàng migration/rollback/acceptance · (2) Chỉ sửa tài liệu/skill, giữ máy ADR-0059 (review 2 lần) — kỷ luật thay máy · (3) Review 1 lần nhưng 🔴 vẫn cần review lại delta sau sửa (giữ một phần ADR-0059)
- Chọn: ADR-0062 thay ADR-0059 §1-2: review 1 lần; 🔴 sửa trong 1 commit rồi pr debt --fixed (không review lại), 🟠/🟢 ghi nợ; rủi ro thấp = làn nhanh (CI + tự rà diff, máy merge ghim head); trung bình = làn chuẩn, 1 review logic/phạm vi/test; cao = ngoại lệ cứng + schema/migration, review độc lập bắt buộc kể cả pha build; release-check thêm hàng migration/rollback/acceptance
- Lý do (tiêu chí chất lượng cuối): Đúng chữ chủ dự án (người có quyền cuối, ADR-0008): 'chỉ review 1 lần: nghiêm trọng thì sửa, cam/xanh ghi nợ cho merge'. An toàn: 🔴 vẫn không ghi nợ (phải sửa, ghi đã sửa ở sổ tại head), cao rủi ro không hoãn review ở pha build (chặt hơn ADR-0037), audit cuối pha quét lại diff là lưới đỡ cho bản sửa không review lại; giữ đường lùi (revert ADR + REVIEW_ROUNDS). PA2 trái luật mới (PR vẫn đứng ở lượt 2); PA3 trái 'chỉ review 1 lần'.
- Đường lùi: Revert PR của ADR-0062: REVIEW_ROUNDS=2 và _debt_problem cũ (ADR-0059), bỏ hàng release-check mới; dự án đích nâng khung bản kế

### D-296 · 2026-11-01T14:49:58+00:00 · Kế hoạch sửa audit cuối pha 2026-11-01 (0 🔴, 6 🟠 mới, 7 🟢; 4 🟠 là hồi quy của đợt)?

- Phương án: (1) Ba đợt theo nhà file: guard (SEC-270/271, PERF-004, + nợ SEC-254/256) · xt.py (SEC-272, CODE-034, HAR-181/182 + 🟢 scanner rẻ) · tài liệu (DOC-162…165, XFEAT-043, HAR-185/187); mỗi đợt 1 PR, test đỏ trước, review 1 lần theo ADR-0062; rồi audit delta lại 7 nhóm chưa quét · (2) Một PR gộp mọi 🟠 · (3) Ghi nợ hết, sang đợt kế
- Chọn: Ba đợt theo nhà file: guard (SEC-270/271, PERF-004, + nợ SEC-254/256) · xt.py (SEC-272, CODE-034, HAR-181/182 + 🟢 scanner rẻ) · tài liệu (DOC-162…165, XFEAT-043, HAR-185/187); mỗi đợt 1 PR, test đỏ trước, review 1 lần theo ADR-0062; rồi audit delta lại 7 nhóm chưa quét
- Lý do (tiêu chí chất lượng cuối): Đúng/an toàn: hồi quy guard (perf treo hook, sed/+= lọt) sửa trước; PR theo nhà file nhỏ, review 1 lần đủ tập trung; PA2 quá lớn (>150 dòng, nhiều nhà); PA3 để lỗ bảo mật đã tái hiện
- Đường lùi: Revert PR từng đợt

### D-297 · 2026-11-01T16:50:34+00:00 · Quét lại T-3623: 5 🟠 mới (guard sed bậc hai, awk stdin, API shell Perl/Ruby/PHP, printf -v PS4; test perf xanh giả) — làm gì?

- Phương án: (1) Đợt 5 một PR guard sửa cả 5 (test đỏ trước, OR với luật cũ, bench), rồi Đợt 6 quét lại DOC/XFEAT/HAR cụm nhỏ · (2) Ghi nợ hết, sang cắt bản
- Chọn: Đợt 5 một PR guard sửa cả 5 (test đỏ trước, OR với luật cũ, bench), rồi Đợt 6 quét lại DOC/XFEAT/HAR cụm nhỏ
- Lý do (tiêu chí chất lượng cuối): 4/5 là lỗ guard đã tái hiện chạy thật (lệnh nguy hiểm lọt) — tiêu chí (1) an toàn; cùng nhà file nên một PR; PA2 để lỗ bảo mật vào bản phát hành
- Đường lùi: Revert PR đợt 5

### D-298 · 2026-11-01T17:44:20+00:00 · Sau PLAN-fix-2026-11-01 (#389–#392), máy đòi audit delta lại các PR sửa — làm tiếp hay dừng đợt?

- Phương án: (1) Dừng đợt: không quét delta lặp các PR sửa (đã review 1 lần theo ADR-0062); audit tổng thể kế tiếp ở đầu đợt /complete trước khi cắt 3.30.0, gom nợ còn lại (🟠 SEC-276/287/288/290/291/292, HAR-182 phần còn lại + 🔴 guard có từ trước) thành PLAN mới · (2) Quét delta tiếp sau mỗi đợt sửa
- Chọn: Dừng đợt: không quét delta lặp các PR sửa (đã review 1 lần theo ADR-0062); audit tổng thể kế tiếp ở đầu đợt /complete trước khi cắt 3.30.0, gom nợ còn lại (🟠 SEC-276/287/288/290/291/292, HAR-182 phần còn lại + 🔴 guard có từ trước) thành PLAN mới
- Lý do (tiêu chí chất lượng cuối): Cấu hình chủ dự án 2026-11-01: audit tổng thể MỘT lần cuối mỗi giai đoạn + review 1 lần mỗi PR; quét lặp các bản sửa đã cho thấy mỗi lượt sinh 🟠 mới ở chính bản sửa (vòng không hội tụ, chi phí lớn); nợ đã có ID ở sổ, release-check vẫn NO-GO nên không phát hành mang nợ
- Đường lùi: Chạy /audit delta 457a69e..HEAD bất kỳ lúc nào

### D-299 · 2026-11-01T23:29:52+00:00 · Đầu /complete trước 3.30.0: sổ còn 18 🔴 + 26 🟠 lách bộ phân tích bash của guard (AUD-SEC-180…292) — sửa thế nào?

- Phương án: (1) Vá từng phát hiện như các đợt trước (mỗi ca một luật nhận dạng) · (2) Tập con chuẩn: guard chặn (BUDGET, fail-closed) mọi cấu trúc nó không mô phỏng chắc ở vùng mã (backtick, comment có nháy, IFS mở rộng, bảng alias, ~N, PID-rồi-ngoặc, brace có thăng, nháy không đóng, bash -c/eval thân động, ghi biến prompt, ống vào shell) + lệnh gh đăng nội dung chỉ nhận thân chữ nguyên văn/file chữ — ADR-0063 · (3) Chấp nhận rủi ro các 🔴 lách cố ý (chủ + hạn), dựa vào bộ phân loại Auto
- Chọn: Tập con chuẩn: guard chặn (BUDGET, fail-closed) mọi cấu trúc nó không mô phỏng chắc ở vùng mã (backtick, comment có nháy, IFS mở rộng, bảng alias, ~N, PID-rồi-ngoặc, brace có thăng, nháy không đóng, bash -c/eval thân động, ghi biến prompt, ống vào shell) + lệnh gh đăng nội dung chỉ nhận thân chữ nguyên văn/file chữ — ADR-0063
- Lý do (tiêu chí chất lượng cuối): (1) an toàn: đóng theo lớp thay vì từng ca — #372 cho thấy vá từng ca không hội tụ (7 lượt review, mỗi lượt lộ ca mới); (3) đơn giản, test được: luật cấu trúc ngắn, mỗi lớp một test; đo trên 1567 lệnh Bash thật của các phiên: vùng mã chạm luật mới ~24 lệnh (đều là backtick trong message commit nháy kép — bash thực thi thật, tức lỗi) → chặn oan ~0; PA3 để 🔴 an toàn vào bản phát hành (vi phạm tiêu chí 1)
- Đường lùi: Revert PR của từng lớp; luật mới OR với luật cũ nên gỡ một lớp không mở lại lớp khác

### D-300 · 2026-11-01T23:53:42+00:00 · Duyệt PLAN-harden-2026-11-01 (/complete trước 3.30.0): 7 lát — A–D guard theo ADR-0063, E xt.py, F sổ (🟢 nợ review), G release-check

- Phương án: (1) Duyệt nguyên PLAN, mỗi lát một PR, lát guard một review tập trung trước merge · (2) Gộp lát A–D thành một PR guard lớn
- Chọn: Duyệt nguyên PLAN, mỗi lát một PR, lát guard một review tập trung trước merge
- Lý do (tiêu chí chất lượng cuối): (1) an toàn + (2) đường lùi: mỗi lớp một PR revert được độc lập; PR ≤ ~150 dòng mã theo luật harden; (3) test được: mỗi lát có mẫu tái hiện của sổ làm test đỏ trước; PA2 vượt trần dòng và khó review
- Đường lùi: Sửa PLAN (bỏ/tách task) bằng D mới; loop init lại

### D-301 · 2026-11-02T03:21:39+00:00 · Lát C (T-3632) sau review trước PR (4 🔴): nguồn thân của gh đăng được — danh sách đen từng dạng hay danh sách trắng?

- Phương án: (1) Vá thêm từng dạng reviewer nêu, giữ 17 ca đối chứng cũ ($(ls|wc), $(git log --oneline), xargs -I{}, nhóm < tệp) · (2) Danh sách trắng (ADR-0063 lát C): thân chỉ là chữ nguyên văn, $(cat <<'EOF'…), $(cat tệp nguyên văn), tệp/stdin-chuyển-hướng trên chính gh ở thư mục biết; endpoint api đọc dấu; 17 ca đối chứng cũ thành chặn
- Chọn: Danh sách trắng (ADR-0063 lát C): thân chỉ là chữ nguyên văn, $(cat <<'EOF'…), $(cat tệp nguyên văn), tệp/stdin-chuyển-hướng trên chính gh ở thư mục biết; endpoint api đọc dấu; 17 ca đối chứng cũ thành chặn
- Lý do (tiêu chí chất lượng cuối): (1) đúng và an toàn: dấu đi qua được tên tệp (ls), thông điệp commit (guard không chặn commit mang dấu: git log --oneline/%s, show --stat), tr/printf — danh sách đen không hội tụ (ADR-0063, #372). Đo 1567 lệnh Bash thật: luật gh mới đổi 0 quyết định; đường thay thế cho agent: ghi thân ra tệp rồi --body-file (lệnh riêng).
- Đường lùi: Trả _gh_strict_why về a41e64c và expect của 17 ca guard-control-* trong tests/fixtures/autonomy/guard.json
### D-302 · 2026-11-02T04:20:53+00:00 · Kế hoạch sửa sau audit toàn bộ 2026-11-02 (AUDIT-REPORT-2026-11-02-full.md): 3 🟠 mới + 21 🟢, 4 🔴 guard có từ trước — chủ dự án triển khai sau

- Phương án: (1) Ba đợt theo tác động/chi phí: P0 trước 3.30.0 (4 🔴 guard lát C ADR-0063 + SEC-248 tiền tố docs/autopilot, CODE-036 khoá reviews.json, HAR-197 hàng go_no_go_file, HAR-036/198 matcher hook, CI-027 schedule secret-scan, DOC-175 PROGRESS); P1 2–4 tuần (DOC-180 lưu trữ sổ + trần docs, SEC-329 mã lý do làm khoá chính, PERF-013 cache guard kiểm sha256, HAR-199 đo chặn oan, CODE-037/038, CI-028, DEP-010, TEST-051); P2 cần ADR (sandbox/egress bắt buộc cho autopilot, tách xt.py theo lát, nội dung DOC-176…178/181, XFEAT-046) · (2) Gộp tất cả vào PLAN-harden-2026-11-01 đang chạy, không phân đợt · (3) Chỉ sửa 🔴 rồi cắt 3.30.0, hoãn toàn bộ 🟠/🟢
- Chọn: Ba đợt theo tác động/chi phí: P0 trước 3.30.0 (4 🔴 guard lát C ADR-0063 + SEC-248 tiền tố docs/autopilot, CODE-036 khoá reviews.json, HAR-197 hàng go_no_go_file, HAR-036/198 matcher hook, CI-027 schedule secret-scan, DOC-175 PROGRESS); P1 2–4 tuần (DOC-180 lưu trữ sổ + trần docs, SEC-329 mã lý do làm khoá chính, PERF-013 cache guard kiểm sha256, HAR-199 đo chặn oan, CODE-037/038, CI-028, DEP-010, TEST-051); P2 cần ADR (sandbox/egress bắt buộc cho autopilot, tách xt.py theo lát, nội dung DOC-176…178/181, XFEAT-046)
- Lý do (tiêu chí chất lượng cuối): (1) an toàn: 🔴 và 🟠 chạm merge/hàng rào đi trước, mỗi đợt một PR nhỏ đảo ngược được; (3) bền và test được: 🟠 có Gate đỏ trước; P2 đổi cấu trúc nên cần ADR riêng thay vì chèn vào PLAN đang chạy (PA2 phình phạm vi lát guard, PA3 để lại 🟠 CODE-036/HAR-197 làm lệch G7 lặp lại)
- Đường lùi: Sửa thứ tự/đợt bằng D mới; mỗi PR revert độc lập

### D-303 · 2026-11-02T05:16:50+00:00 · ADR-0064 harness đa nhà cung cấp — ba lựa chọn triển khai sau khi chủ dự án trả lời 2026-11-02 (1: cả 6 công cụ; 2: nâng LOOP-HARNESS-022 nếu không làm chậm code; 3: vị trí luật 'cái nào tốt thì làm')

- Phương án: (1) Lát B làm cả 6 adapter (Codex, Gemini CLI, Cursor, Copilot CLI, Grok Build, OpenCode) theo thứ tự OSI trước; LOOP-HARNESS-022 nâng SHOULD → MUST@M chỉ cho phiên autopilot không người trực (doctor kiểm, chủ dự án chấp nhận chi phí cài một lần + allowlist); luật giữ ở .claude/hooks/guard.py làm nhà vật lý duy nhất, thêm chế độ core trung lập, adapter mỏng ở .xtemplates/harness/<tool>/ gọi lõi — không dời thư mục trong 3.x · (2) Như trên nhưng dời guard.py sang .xtemplates/harness/core.py ngay, .claude/hooks chỉ còn shim · (3) Chỉ Codex + Gemini đợt đầu, LOOP-HARNESS-022 giữ SHOULD
- Chọn: Lát B làm cả 6 adapter (Codex, Gemini CLI, Cursor, Copilot CLI, Grok Build, OpenCode) theo thứ tự OSI trước; LOOP-HARNESS-022 nâng SHOULD → MUST@M chỉ cho phiên autopilot không người trực (doctor kiểm, chủ dự án chấp nhận chi phí cài một lần + allowlist); luật giữ ở .claude/hooks/guard.py làm nhà vật lý duy nhất, thêm chế độ core trung lập, adapter mỏng ở .xtemplates/harness/<tool>/ gọi lõi — không dời thư mục trong 3.x
- Lý do (tiêu chí chất lượng cuối): (1) đúng và an toàn: MUST@M cho phiên không người trực đóng lỗ 'guard không phải sandbox' ở 5/7 công cụ tắt sandbox mặc định; chi phí là cài một lần + allowlist registry/git, không chạm vòng code (phiên tương tác không bị ép) nên không làm chậm tiến độ; (2) đường lùi: giữ guard.py tại chỗ là diff nhỏ nhất, revert từng adapter độc lập; dời thư mục (PA2) đụng DIR_CAPS, harness.sha256.json, hàng trăm tham chiếu test và cả 3 công cụ đang nạp .claude/settings.json — chỉ xét ở 4.0 cùng mốc 2027-01-21; (3) bền, test được: lõi một nơi, adapter là dữ liệu + fixture theo phiên bản; PA3 bỏ 4 công cụ chủ dự án đã chọn
- Đường lùi: Mỗi adapter một PR revert độc lập; mức LOOP-HARNESS-022 hạ lại bằng D mới + CHANGELOG; dời thư mục làm ADR riêng khi cần

### D-304 · 2026-11-02T05:23:27+00:00 · Gom mọi đề xuất/nâng cấp ngày 2026-11-02 (chủ dự án: 'cập nhật tất cả đề xuất, nâng cấp trong hôm nay rồi tối ưu lại và triển khai') thành một PLAN

- Phương án: (1) Một PLAN-upgrade-2026-11-02 thay PLAN-harden-2026-11-01: 5 task mở của harden chép cùng ID + P0/P1/P2 của D-302 + lát A–E ADR-0064 (D-303), gộp việc trùng (SEC-329↔lát A, DOC-181↔lát A, HAR-036/198↔CI-027/028, TEST-051↔HAR-199), xếp 🔴 guard → 🟠 audit → lõi/sandbox → P1 → adapter → nội dung → sổ/phát hành; để ngoài ARCH-008, DOC-179, PERF-014 · (2) Ba PLAN song song (harden, audit, harness) chạy lần lượt · (3) Chỉ chạy PLAN-harden tới 3.30.0 rồi mới lập PLAN cho audit + ADR-0064
- Chọn: Một PLAN-upgrade-2026-11-02 thay PLAN-harden-2026-11-01: 5 task mở của harden chép cùng ID + P0/P1/P2 của D-302 + lát A–E ADR-0064 (D-303), gộp việc trùng (SEC-329↔lát A, DOC-181↔lát A, HAR-036/198↔CI-027/028, TEST-051↔HAR-199), xếp 🔴 guard → 🟠 audit → lõi/sandbox → P1 → adapter → nội dung → sổ/phát hành; để ngoài ARCH-008, DOC-179, PERF-014
- Lý do (tiêu chí chất lượng cuối): (1) đúng và an toàn: 🔴 guard vẫn đi đầu, không task nào làm yếu cổng; một sổ máy đọc (loop status) thay ba; (3) đơn giản, test được: gộp 4 cặp trùng bớt ~4 PR, phụ thuộc sau: rõ trong một file; PA2 ba vòng loop init chồng nhau, PA3 trì hoãn 🟠 CODE-036/HAR-197 làm lệch G7 ngay ở lần cắt 3.30.0; việc để ngoài cần ADR/research riêng (D-142, đợt nội dung)
- Đường lùi: Tách lại PLAN bằng D mới; task giữ ID nên loop init mang bằng chứng theo

### D-305 · 2026-11-02T08:39:37+00:00 · AUD-TEST-052: test_quote_like_repeat_not_cubic đỏ ngẫu nhiên khi cổng chạy song song — sửa test thế nào?

- Phương án: (1) giữ ngưỡng tỉ lệ mặc định, chỉ đổi đồng hồ sang process_time · (2) dùng cpu_budget.assert_not_quadratic ratio 40 ở cỡ 16 (đồng hồ process_time) — chỉ canh bậc ba trở lên · (3) sửa _quote_exec_scripts thành tuyến tính rồi giữ ngưỡng cũ
- Chọn: dùng cpu_budget.assert_not_quadratic ratio 40 ở cỡ 16 (đồng hồ process_time) — chỉ canh bậc ba trở lên
- Lý do (tiêu chí chất lượng cuối): đo (review #405 R10): main và HEAD cùng bậc hai (n=16→64: 0,068→1,18 s CPU) do thân trích Θ(n²) theo đầu vào — có từ trước, không phải hồi quy; ngưỡng cũ chỉ xanh nhờ SLACK; tên test canh bậc ba và cpu_budget cho phép ratio 40 cho test canh hàm mũ; bậc ba vẫn bị bắt. Phương án 3 là việc tối ưu riêng, không thuộc lát sửa
- Đường lùi: trả ratio mặc định trong test_quote_like_repeat_not_cubic khi _quote_exec_scripts tuyến tính (mở task PERF)

### D-306 · 2026-11-02T08:59:29+00:00 · T-3653/AUD-CODE-038: gộp 4 runner subprocess (run_gate_shell, _git, _floor_run, _perf_run) thành một _run(cmd, cwd, timeout, env)?

- Phương án: (1) gộp thành một _run theo PLAN · (2) giữ 4 runner (mỗi cái một giao ước riêng), chỉ gộp đường GET REST: latest_framework_tag qua _gh_api
- Chọn: giữ 4 runner (mỗi cái một giao ước riêng), chỉ gộp đường GET REST: latest_framework_tag qua _gh_api
- Lý do (tiêu chí chất lượng cuối): đọc mã 2026-11-02: _floor_run đã gọi run_gate_shell (không phải biến thể); run_gate_shell = bash pipefail + guard (LOOP-STOP-027) + nhóm tiến trình + output qua file tạm (review #220); _git = GIT_SAFE_READ + không grafts (AUD-SEC-158) + errors=replace; _perf_run = đo không lượng tử bằng thread waitpid (AUD-PERF-003). Gộp phải mang cờ cho từng giao ước — thêm nhánh, dễ làm mất bảo đảm an toàn đã sửa (tiêu chí 1 > 3); xác minh đối kháng của audit cũng ghi PARTIAL. Đường REST trùng thật nên gộp
- Đường lùi: tách hàm chung khi có runner thứ năm cùng giao ước; phần AUD-CODE-038 về runner ghi bác bỏ kèm D này

### D-307 · 2026-11-02T09:22:29+00:00 · T-3652/AUD-PERF-013: cache bytecode guard.py khoá theo sha256 nguồn để bớt ~0,13 s mỗi lệnh Bash?

- Phương án: (1) cache marshal khoá sha256 nguồn trong thư mục do install/doctor tạo (theo PLAN) · (2) không cache; giữ compile từ nguồn (AUD-SEC-074), sổ ghi chấp nhận chi phí; tăng tốc thật đi qua tách guard/nạp lười (AUD-ARCH-008, cần ADR) · (3) tiến trình guard thường trú (daemon) giữ module đã nạp
- Chọn: không cache; giữ compile từ nguồn (AUD-SEC-074), sổ ghi chấp nhận chi phí; tăng tốc thật đi qua tách guard/nạp lười (AUD-ARCH-008, cần ADR)
- Lý do (tiêu chí chất lượng cuối): đọc mã + mô hình đe doạ 2026-11-02: khoá sha256 chỉ ràng buộc NGUỒN, không ràng buộc bytecode — ai ghi được file cache (đặt tên theo sha256 nguồn công khai) thì thay mã guard mà git diff không thấy (cache bị gitignore), đúng lớp lỗi AUD-SEC-074 (pyc giả khớp header). Không có bí mật nào để ký trong máy agent. Sửa thẳng guard.py thì hiện trong diff và review. Tiêu chí 1 (an toàn) > 5 (tốc độ): ~0,13 s × ~1.500 lệnh ≈ 3–4 phút/phiên được chấp nhận. Daemon thêm bề mặt tấn công và trạng thái sống lâu
- Đường lùi: nếu có nơi lưu agent không ghi được (thư mục người dùng chỉ đọc, ký bằng khoá ngoài máy agent) thì làm phương án 1 qua ADR mới

### D-308 · 2026-11-02T10:14:40+00:00 · T-3640/AUD-SEC-329: chính sách guard suy từ chuỗi lý do — sửa bằng cách mỗi luật trả code tường minh (PLAN) hay khoá bằng test?

- Phương án: (1) mỗi luật (100+ chỗ trả lý do) trả code tường minh, REASON_CODES chỉ còn fallback · (2) giữ REASON_CODES; ReasonCodeLockTest: mỗi mã trong REASON_CODES có ≥ 1 lệnh thật chạy end-to-end và khẳng định mã — đổi câu chữ lý do làm test đỏ thay vì âm thầm cho qua
- Chọn: giữ REASON_CODES; ReasonCodeLockTest: mỗi mã trong REASON_CODES có ≥ 1 lệnh thật chạy end-to-end và khẳng định mã — đổi câu chữ lý do làm test đỏ thay vì âm thầm cho qua
- Lý do (tiêu chí chất lượng cuối): rủi ro của AUD-SEC-329 là đổi câu chữ làm deny thành cho qua MÀ KHÔNG AI BIẾT; test khoá biến lỗi im lặng thành CI đỏ với diff nhỏ (66 dòng test, 31 dòng guard cho chế độ core), tái hiện của sổ ('push thẳng nhánh chính' → 'đẩy thẳng…') nay đỏ ở ca PUSH_MAIN. Sửa 100+ luật chạm toàn guard 9,4k dòng — rủi ro hồi quy cao hơn lợi ích khi đã có khoá (tiêu chí 1–3). ADR-0017 §2 (AUD-DOC-181) chưa làm, giữ nợ
- Đường lùi: khi đổi lớn bộ luật guard (tách guard_core) thì chuyển sang code tường minh từng luật, giữ ReasonCodeLockTest làm hàng rào

### D-309 · 2026-11-02T11:12:12+00:00 · T-3645: git hook pre-commit chạy lại cổng commit trong phiên Claude Code (hook Bash của khung đã chạy cổng trước git commit) — chạy hai lần hay bỏ qua?

- Phương án: (1) luôn chạy (cổng chạy hai lần mỗi commit trong phiên Claude) · (2) bỏ qua khi CLAUDECODE đặt VÀ dự án có .claude/hooks/pre-bash-guard.sh · (3) dấu tem (cây chỉ mục đã qua cổng) do hook Claude ghi, pre-commit so tem
- Chọn: bỏ qua khi CLAUDECODE đặt VÀ dự án có .claude/hooks/pre-bash-guard.sh
- Lý do (tiêu chí chất lượng cuối): Claude Code đặt CLAUDECODE cho shell của nó (kiểm 2026-11-02 trong phiên); hook Bash của khung đã chạy đúng cổng ngay trước commit, chạy lại chỉ tốn thời gian (gate-fast có thể vài phút). Tem trong .git cũng giả được như biến môi trường mà phức tạp hơn. Sàn git hook nhắm sai sót của công cụ không có hook chặn, không phải agent cố lách: agent đặt CLAUDECODE=1 để lách là hành vi lách (LOOP-STOP-025) — ghi giới hạn
- Đường lùi: bỏ điều kiện trong pre-commit (luôn chạy) nếu thấy công cụ khác đặt CLAUDECODE hay bị lách

### D-310 · 2026-11-02T11:25:40+00:00 · T-3642…3644 adapter: kiểm bằng gì và xử lý host tự đọc .claude/settings.json (Copilot, Cursor, Grok) thế nào?

- Phương án: (1) theo PLAN: ≥ 10 ca autonomy-bench mỗi công cụ (nhóm bench mới) + tránh nạp hai lần · (2) test bảng tests/test_adapters.py (≥ 10 ca/host qua hàm thật, giao thức chặn từng host, plugin OpenCode chạy thật bằng bun) + chấp nhận hook Claude chạy thêm ở Copilot/Cursor/Grok
- Chọn: test bảng tests/test_adapters.py (≥ 10 ca/host qua hàm thật, giao thức chặn từng host, plugin OpenCode chạy thật bằng bun) + chấp nhận hook Claude chạy thêm ở Copilot/Cursor/Grok
- Lý do (tiêu chí chất lượng cuối): bench cần nhóm ca mới trong engine autonomy-bench (đọc payload từng host) — nhiều mã hơn cho cùng bảo đảm mà test bảng cho; test chạy đúng hàm của adapter và guard thật. Hai lần chạy không đổi quyết định (cùng một guard, deny thắng); Copilot/Cursor không có cơ chế khử trùng theo nguồn, công tắc duy nhất là tắt toàn cục (disableAllHooks, Third-Party Imports) sẽ tắt luôn hook của khung — tiêu chí 1 > 5
- Đường lùi: thêm nhóm 'adapter' vào autonomy-bench khi số host/ca tăng; bỏ hook adapter của host nào đọc .claude/settings.json nếu đo được hook Claude chặn đúng ở host đó

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
