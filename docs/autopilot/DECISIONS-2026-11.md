# Nhật ký quyết định tự duyệt — tháng 11/2026 (phần đầu)

> Bản tháng của [`DECISIONS.md`](DECISIONS.md) (cách T-3651): 55 mục D-292…D-347 (2026-11-01…04; đợt 2 D-311…D-330 dời 2026-11-04, đợt 3 D-331…D-333, đợt 4 D-334…D-338, đợt 5 D-340, đợt 6 D-341…D-343 và đợt 7 D-344…D-347 dời 2026-11-05; không có D-339) dời nguyên văn để `docs/autopilot` còn trong trần byte (ADR-0043, không nới trần). `loop decide` vẫn ghi vào `DECISIONS.md`; mọi công cụ đọc cả bản tháng. Không sửa mục cũ — đổi ý ghi quyết định mới "thay D-NNN".

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
