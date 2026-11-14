# Nhật ký quyết định tự duyệt

> Ghi bởi `xt.py loop decide`. Phiên chính tự duyệt điểm quyết định theo tiêu chí chất lượng cuối (`LOOP-STOP-018`, ADR-0008 của khung). Người xem lại bất cứ lúc nào; đổi ý → quyết định mới ghi "thay D-NNN", không sửa mục cũ.
> Bản tháng trước: [`DECISIONS-2026-10.md`](DECISIONS-2026-10.md) (D-001…D-287), [`DECISIONS-2026-11.md`](DECISIONS-2026-11.md) (D-292…D-372) — máy đọc cả bản tháng (T-3651).

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

### D-373 · 2026-11-05T10:50:02+00:00 · Audit ARCH T-3557: .claude/hooks/ đạt 843 817 B = 2,28× mốc 2026-10-26 (369 274 B) từ #433 — ADR-0050 đòi ADR xét lại khi vượt 2× trước 2027-01-21, chưa có ADR, không cổng máy nào bắt

- Phương án: (1) ADR-0072 xét lại: giữ trần nhóm hiện có (1 417 969 B, chưa chạm), chấp nhận mức tăng vì là bản vá an ninh guard (#433–#442, ADR-0065/0066/0067); đặt mốc mới 2026-11-05 cho .claude/hooks và scripts; thêm cổng máy trong tests/test_docs_budget.py: mỗi nhóm ≤ 2× mốc gần nhất trừ khi có ADR xét lại khai trong test; T-3709 đo chi phí compile guard.py mỗi lệnh Bash (AUD-PERF-013) và xét cache bytecode trước 2027-01-21 cùng đợt đánh giá sandbox · (2) Chấp nhận 🟠 có hạn 2027-01-21 không ADR
- Chọn: ADR-0072 xét lại: giữ trần nhóm hiện có (1 417 969 B, chưa chạm), chấp nhận mức tăng vì là bản vá an ninh guard (#433–#442, ADR-0065/0066/0067); đặt mốc mới 2026-11-05 cho .claude/hooks và scripts; thêm cổng máy trong tests/test_docs_budget.py: mỗi nhóm ≤ 2× mốc gần nhất trừ khi có ADR xét lại khai trong test; T-3709 đo chi phí compile guard.py mỗi lệnh Bash (AUD-PERF-013) và xét cache bytecode trước 2027-01-21 cùng đợt đánh giá sandbox
- Lý do (tiêu chí chất lượng cuối): (1) ADR-0050 ghi 'phải có ADR' — chấp nhận không ADR trái chính quyết định cũ; (3) cổng máy bắt lần vượt sau thay vì dựa vào audit; (2) giữ trần, không nới; chi phí compile chưa đo được trong phiên (guard chặn script đọc guard.py) nên giao task đo có hạn
- Đường lùi: Tách guard.py (ADR riêng) nếu T-3709 đo chi phí compile vượt ngân sách hook

### D-374 · 2026-11-05T11:29:58+00:00 · PR #448 (cắt 3.30.0): review lượt 1 chưa sạch (0 🔴, 3 🟠 GO-NO-GO lỗi thời, mốc scripts vô hiệu cổng 2×, test mốc không đọc ADR; 4 🟢) — PR cắt bản không ghi nợ (ADR-0059 §6); đi tiếp thế nào?

- Phương án: (1) Sửa HẾT 3 🟠 + 4 🟢 trong một commit trên PR, rồi review lượt 2 cả PR ở head mới bằng reviewer-alt (effort max) · (2) Tách ADR-0072 + cổng 2× sang PR riêng, PR cắt bản chỉ còn VERSION/CHANGELOG/báo cáo
- Chọn: Sửa HẾT 3 🟠 + 4 🟢 trong một commit trên PR, rồi review lượt 2 cả PR ở head mới bằng reviewer-alt (effort max)
- Lý do (tiêu chí chất lượng cuối): (1) các phát hiện đều nhỏ, sửa được ngay, có tái hiện; (3) tách PR làm báo cáo/ARCH lệch khỏi bản đang cắt; (5) một lượt sửa + một review rẻ hơn hai PR
- Đường lùi: Tách ADR-0072 sang PR riêng nếu review lượt 2 vẫn chặn ở phần đó

### D-375 · 2026-11-05T12:47:31+00:00 · AUD-HAR-301 (xboss nâng 3.30.0): harness_permissions: own đổi 11 lệnh hook dạng ${CLAUDE_PROJECT_DIR} sang tương đối — đúng giao ước đã ghi (harness-files.md, test own_permissions_keeps_project_permissions_and_relative_hooks, chủ repo duyệt 2026-10-22 cho dhcb); sửa trong 3.30.1?

- Phương án: (1) 3.30.1 giữ giao ước, ghi chú ở harness-files.md + CHANGELOG 'Dự án đích': dự án cần lệnh hook tuyệt đối thì không dùng own (hoặc gộp tay); 3.31.0 xét own giữ dạng lệnh sẵn có của dự án (ADR mới) · (2) Đổi giao ước ngay trong 3.30.1
- Chọn: 3.30.1 giữ giao ước, ghi chú ở harness-files.md + CHANGELOG 'Dự án đích': dự án cần lệnh hook tuyệt đối thì không dùng own (hoặc gộp tay); 3.31.0 xét own giữ dạng lệnh sẵn có của dự án (ADR mới)
- Lý do (tiêu chí chất lượng cuối): (2) bản vá không đổi giao ước đã được chủ repo duyệt; (1) xboss hiện chạy đúng (PR #706 xanh, hook tuyệt đối giữ ở lần cài này) — rủi ro chỉ ở lần cài sau, đã ghi; (3) đổi giao ước cần ADR và test mới
- Đường lùi: Đổi trong 3.30.x nếu dự án đích nào hỏng hook vì dạng tương đối trước 3.31.0

### D-376 · 2026-11-05T13:13:38+00:00 · PR #450 (cắt 3.30.1): review lượt 1 chặn — 🔴 trần docs/ops vượt 970 B (GO-NO-GO §2 khai test_docs_budget exit 0 khi file mới chưa vào index); 🟠 cổng ký tự vô hình bỏ sót research/ (install.py cài vào dự án đích), PROGRESS.md, xt.yaml, .github/; 🟠 mẫu xt.yaml nói own giữ dạng lệnh hook — ngược giao ước D-375; 5 🟢 (regex code span thiếu lookbehind/escape, test dán ký tự vô hình thật, PROGRESS, harness-files lặp ý, chuỗi VS dài vô hạn)

- Phương án: (1) Sửa HẾT trong một commit: lưu trữ dòng đã sửa đủ chỗ + đo lại sau git add; cổng quét mọi file tracked trừ tests/ (lỗi UTF-8 → báo, không bỏ qua); sửa chú thích mẫu xt.yaml + docstring install.py theo giao ước; 🟢: regex code span theo CommonMark tối thiểu (lookbehind backtick, \` escape) + test, test dùng escape, PROGRESS 3.30.1, harness-files một câu, giới hạn chuỗi selector ≤ 1 liên tiếp; rồi review lượt 2 cả PR · (2) Tách cổng ký tự vô hình mở rộng sang PR sau
- Chọn: Sửa HẾT trong một commit: lưu trữ dòng đã sửa đủ chỗ + đo lại sau git add; cổng quét mọi file tracked trừ tests/ (lỗi UTF-8 → báo, không bỏ qua); sửa chú thích mẫu xt.yaml + docstring install.py theo giao ước; 🟢: regex code span theo CommonMark tối thiểu (lookbehind backtick, \` escape) + test, test dùng escape, PROGRESS 3.30.1, harness-files một câu, giới hạn chuỗi selector ≤ 1 liên tiếp; rồi review lượt 2 cả PR
- Lý do (tiêu chí chất lượng cuối): (1) research/ được cài vào dự án đích — đúng lớp lỗi bản vá nhắm tới; (1) tài liệu own sai là gốc lỗi xboss; (3) đều nhỏ, có tái hiện; PR cắt bản không mang nợ (ADR-0059 §6)
- Đường lùi: Tách cổng mở rộng nếu quét mọi file chặn oan nội dung hợp lệ

### D-377 · 2026-11-05T13:50:11+00:00 · Nhánh ADR-0068 (3.31.0) sau gộp 3.30.0: 4 điểm mở — nhóm DATA ghi N/A dù gói web-api-ts có migration; AUD-SEC-498 🟠 python3 -c gọi xt.main lách guard; BASE-SEC-005 đỏ vì POSTGRES_PASSWORD literal trong pack-web-api.yml; AUD-SEC-502 phần baseline.json chép đè được trong cùng PR

- Phương án: (1) Chặt cả bốn: quét nhóm DATA cho gói (audit, không giải trình thay); thêm luật guard cho AUD-SEC-498 kèm test + ca autonomy-bench; CI dùng POSTGRES_HOST_AUTH_METHOD: trust cho service container (không literal mật khẩu, không nới lệnh kiểm); CI so contract với baseline.json của nhánh gốc, chỉ cho đổi baseline khi PR tăng phiên bản gói · (2) Giải trình DATA, chấp nhận có hạn AUD-SEC-498, thu hẹp lệnh kiểm BASE-SEC-005, giữ review tay baseline
- Chọn: Chặt cả bốn: quét nhóm DATA cho gói (audit, không giải trình thay); thêm luật guard cho AUD-SEC-498 kèm test + ca autonomy-bench; CI dùng POSTGRES_HOST_AUTH_METHOD: trust cho service container (không literal mật khẩu, không nới lệnh kiểm); CI so contract với baseline.json của nhánh gốc, chỉ cho đổi baseline khi PR tăng phiên bản gói
- Lý do (tiêu chí chất lượng cuối): (1) gói cài migration và guard vào dự án đích — lỗ ở đây nhân lên mọi dự án; không nới cổng (LOOP-CI-001); (3) mỗi điểm có test; (5) chỉ phá hoà
- Đường lùi: Chấp nhận có hạn từng điểm nếu sửa làm vỡ hành vi dự án đích đã dùng gói

### D-378 · 2026-11-05T14:28:05+00:00 · PR #450 (cắt 3.30.1): review lượt 2 còn 3 🟢 — F1 hồi quy so main (che code span theo cả dòng ghép backtick lẻ của hai ô bảng → link hỏng ở ô giữa không báo), F2 danh sách số vắng thiếu D-352…355, F3 lookbehind sai với backtick sau backtick đã escape; trần rethink đã dùng

- Phương án: (1) Thu hẹp: rút phần sửa check-links (AUD-CODE-061, FB-115) khỏi 3.30.1 — trả scripts/check-links.py và test về main, AUD-CODE-061 về mở (sửa ở 3.31.0 bằng bộ quét backtick theo CommonMark + tách ô GFM), CHANGELOG bỏ dòng; sửa F2; review lượt 3 chỉ delta · (2) Sửa F1/F3 bằng bộ quét mới ngay trong 3.30.1
- Chọn: Thu hẹp: rút phần sửa check-links (AUD-CODE-061, FB-115) khỏi 3.30.1 — trả scripts/check-links.py và test về main, AUD-CODE-061 về mở (sửa ở 3.31.0 bằng bộ quét backtick theo CommonMark + tách ô GFM), CHANGELOG bỏ dòng; sửa F2; review lượt 3 chỉ delta
- Lý do (tiêu chí chất lượng cuối): (1) bản vá không được mang hồi quy (F1); regex che code span đã hai lượt lộ ca sai — viết bộ quét đúng là việc của bản thường; (2) mục tiêu chính 3.30.1 (AI-GUARD-018, compose, cổng ký tự vô hình) đã sạch qua hai lượt review; FB-115 là báo oan có từ trước, giữ thêm một bản không tệ hơn
- Đường lùi: Đưa lại phần check-links vào 3.30.x nếu bộ quét mới xong trước khi dự án đích cần

### D-379 · 2026-11-05T14:57:43+00:00 · PR #450: review lượt 3 chặn vì phần sót của D-378 (CHANGELOG còn hứa check-links bỏ code span; GO-NO-GO số đo cũ)

- Phương án: (1) Đã sửa ở 31dbad4; review delta lượt 4 · (2) Tách PR
- Chọn: Đã sửa ở 31dbad4; review delta lượt 4
- Lý do (tiêu chí chất lượng cuối): (1) chỉ là chữ sót của D-378, đã sửa và đo lại sau git add; (5) tách PR không thêm an toàn
- Đường lùi: Tách PR nếu lượt 4 còn chặn

### D-380 · 2026-11-05T15:13:01+00:00 · gate-fast tự gây đỏ: test_fast/test chạy xargs -P nproc (16) khiến test đo thời gian (GlobCommandNameTest cpu-ratio, PerfGateExampleTest) đỏ do chính tải của cổng; covpar 8 tiến trình thì ổn định

- Phương án: (1) test_fast và test dùng -P bằng nửa số nhân (tối thiểu 1); không nới ngưỡng test nào · (2) Nới ngưỡng các test thời gian
- Chọn: test_fast và test dùng -P bằng nửa số nhân (tối thiểu 1); không nới ngưỡng test nào
- Lý do (tiêu chí chất lượng cuối): (1) cổng phải ổn định, không đỏ do chính nó; nới ngưỡng là nới cổng (LOOP-CI-001); (5) nửa số nhân vẫn nhanh gấp ~3 lần tuần tự (đo covpar 8: 5 phút 51 giây)
- Đường lùi: Trả về -P nproc nếu test thời gian được làm bền với tải

### D-381 · 2026-11-05T15:30:38+00:00 · PR #450: lượt 4 còn chữ sai (tiêu đề/thân PR khai check-links; GO-NO-GO số đo; PROGRESS)

- Phương án: (1) Sửa chữ tại chỗ, review lượt 5 · (2) Tách PR
- Chọn: Sửa chữ tại chỗ, review lượt 5
- Lý do (tiêu chí chất lượng cuối): (1) chỉ là chữ; (5) tách không thêm an toàn
- Đường lùi: Tách PR

### D-382 · 2026-11-05T22:05:08+00:00 · Hook PreToolUse Bash (guard) quá 600 s khi commit chạy cổng đủ bộ dưới tải

- Phương án: (1) Nâng timeout hook lên 1200 s · (2) Bỏ qua hook khi commit
- Chọn: Nâng timeout hook lên 1200 s
- Lý do (tiêu chí chất lượng cuối): Chủ dự án chọn; giữ hàng rào, chỉ nới thời gian chờ
- Đường lùi: Đặt lại 600 trong .claude/settings.json

### D-383 · 2026-11-06T01:32:34+00:00 · AUD-HAR-301: harness_permissions own đổi lệnh hook khung dạng CLAUDE_PROJECT_DIR sang tương đối (xboss hỏng khi phiên mở ngoài gốc repo)

- Phương án: (1) own giữ dạng lệnh hook sẵn có của dự án: có lệnh khung dạng CLAUDE_PROJECT_DIR thì giữ tuyệt đối, không có thì tương đối (ADR-0073) · (2) khoá riêng chọn dạng lệnh hook · (3) giữ giao ước, ghi chú dự án cần dạng tuyệt đối không dùng own
- Chọn: own giữ dạng lệnh hook sẵn có của dự án: có lệnh khung dạng CLAUDE_PROJECT_DIR thì giữ tuyệt đối, không có thì tương đối (ADR-0073)
- Lý do (tiêu chí chất lượng cuối): (1) đúng: dạng tuyệt đối chạy ở mọi cwd, không bao giờ hạ cấp hook của dự án; giao ước dhcb (tương đối) giữ nguyên vì dhcb không có lệnh tuyệt đối; (3) không thêm khoá cấu hình
- Đường lùi: Trả settings_changes về luôn _relative_hooks khi own; ADR mới thay ADR-0073

### D-384 · 2026-11-06T01:32:34+00:00 · AUD-HAR-300: .gitignore của dự án che file khung trong .xtemplates/

- Phương án: (1) install.py dò git check-ignore trên file vừa cài và cảnh báo, không sửa .gitignore · (2) install.py thêm !.xtemplates/** vào .gitignore
- Chọn: install.py dò git check-ignore trên file vừa cài và cảnh báo, không sửa .gitignore
- Lý do (tiêu chí chất lượng cuối): (1) an toàn: không đổi luật của dự án; !.xtemplates/** kéo cả file dự án cố ý bỏ qua (__pycache__, file tạm) vào repo
- Đường lùi: Bỏ warn_ignored_framework khỏi install()

### D-385 · 2026-11-06T03:26:13+00:00 · PR #454 (cắt 3.31.0): review lượt 1 BLOCKING (F1 test timeout đỏ giả ở main; F2–F7 chữ GO-NO-GO/CHANGELOG) — đã sửa hết ở 616f512, CI xanh

- Phương án: (1) Thêm một lượt sửa hết phát hiện rồi review lại chỉ delta 6f416ea..616f512 (ADR-0059 §6) · (2) Tách PR sửa test riêng, PR cắt bản chỉ chữ
- Chọn: Thêm một lượt sửa hết phát hiện rồi review lại chỉ delta 6f416ea..616f512 (ADR-0059 §6)
- Lý do (tiêu chí chất lượng cuối): (1) đã sửa hết kèm bằng chứng (0/48 dưới tải, mutant vẫn đỏ); (3) delta nhỏ, tách PR thêm vòng CI mà không giảm rủi ro
- Đường lùi: Đóng #454, tách PR test rồi cắt lại

### D-386 · 2026-11-06T03:58:20+00:00 · PR #454 (cắt 3.31.0): review lượt 2 BLOCKING chỉ vì F-A (CHANGELOG khai dự án đích nhận timeout hook khi cài lại, nhưng gộp hooks không đồng bộ timeout)

- Phương án: (1) Sửa tận gốc trong PR: install.py _sync_timeout (nâng, không hạ) + test, rồi review delta 6b7fedc..head · (2) Chỉ sửa chữ CHANGELOG thành bước tay, ghi sổ install.py làm sau
- Chọn: Sửa tận gốc trong PR: install.py _sync_timeout (nâng, không hạ) + test, rồi review delta 6b7fedc..head
- Lý do (tiêu chí chất lượng cuối): (1) dự án đích nhận đúng hạn chờ hook không cần tay — tránh kẹt hook 600 s như D-382; câu CHANGELOG thành đúng; (3) thay đổi nhỏ theo mẫu _sync_on_failure, có test đỏ trước
- Đường lùi: Bỏ _sync_timeout khỏi _merge_hook_events, CHANGELOG ghi bước tay

### D-387 · 2026-11-07T01:35:11+00:00 · Đưa sửa installer #455…#458 tới dự án đích thế nào

- Phương án: (1) Cắt 3.31.1 ngay (bản vá, chỉ installer), cập nhật các PR nâng 3.31.0 đang mở lên 3.31.1 · (2) Chờ gom vào 3.32.0
- Chọn: Cắt 3.31.1 ngay (bản vá, chỉ installer), cập nhật các PR nâng 3.31.0 đang mở lên 3.31.1
- Lý do (tiêu chí chất lượng cuối): (1) dự án đích đang nâng 3.31.0 gặp đúng các lỗi này (Prettier đỏ ở X-Company, diff settings.json phình ở dhcb); (2) bản vá nhỏ, không đổi ID/khoá, lùi được bằng cài lại 3.31.0; (3) theo semver patch
- Đường lùi: Dự án đích cài lại bằng bản khung 3.31.0

### D-388 · 2026-11-07T02:00:01+00:00 · PR #461 (cắt 3.31.1): review lượt 1 REQUEST CHANGES — 2 🟠 lời khai sai (trạng thái dự án đích; nguyên nhân review_debt) + 3 🟢

- Phương án: (1) Sửa hết trên nhánh (ADR-0059 §6: PR cắt bản không mang nợ) rồi review lại delta · (2) Ghi nợ và cắt bản như hiện tại
- Chọn: Sửa hết trên nhánh (ADR-0059 §6: PR cắt bản không mang nợ) rồi review lại delta
- Lý do (tiêu chí chất lượng cuối): (1) GO-NO-GO là tài liệu người ký — lời khai sai không được ship; review_debt sẽ đỏ cả trên main nếu không dời SHA nhóm 4; (3) sửa nhỏ, chỉ tài liệu/sổ/1 test
- Đường lùi: Revert commit sửa của lượt 2

### D-389 · 2026-11-07T04:00:25+00:00 · AUD-HAR-219: gắn chữ ký GO-NO-GO §5 với ứng viên thế nào để chữ ký ở commit A không duyệt cây đổi mã sau đó?

- Phương án: (1) Dòng 'subject: content <64 hex>' (evidence_fingerprint — vân tay nội dung trừ GO-NO-GO/DECISIONS/PROGRESS) và, khi khai release_artifacts, 'subject: digest <64 hex>'; so đủ 64 hex đúng ô · (2) Dòng subject theo SHA HEAD (40 hex) · (3) Giữ so 12 hex digest bất kỳ đâu, thêm cảnh báo
- Chọn: Dòng 'subject: content <64 hex>' (evidence_fingerprint — vân tay nội dung trừ GO-NO-GO/DECISIONS/PROGRESS) và, khi khai release_artifacts, 'subject: digest <64 hex>'; so đủ 64 hex đúng ô
- Lý do (tiêu chí chất lượng cuối): (1) đúng và an toàn: SHA HEAD đổi ngay khi commit chữ ký nên không ký được; vân tay nội dung đã loại file ký nên ổn định qua commit ký và squash, đổi khi mã đổi; so đúng ô đủ 64 hex bỏ khớp ngẫu nhiên. (2) đường lùi: khoá tuỳ chọn cũ giữ nguyên, chỉ thêm dòng. (3) tái dùng evidence_fingerprint có test
- Đường lùi: Revert PR; promotion quay về so 12 hex digest

### D-390 · 2026-11-07T04:00:30+00:00 · AUD-SEC-497: chặn agent tự ghi dòng ký §5 của GO-NO-GO*.md ở đâu?

- Phương án: (1) Guard: Edit/Write/MultiEdit vào GO-NO-GO*.md làm xuất hiện dòng ký mới (tên + ngày) ở §5 → deny; Bash ghi vào GO-NO-GO*.md → deny (sửa bằng Edit để guard so được) · (2) Chỉ dựa review PR · (3) Chặn mọi sửa GO-NO-GO*.md
- Chọn: Guard: Edit/Write/MultiEdit vào GO-NO-GO*.md làm xuất hiện dòng ký mới (tên + ngày) ở §5 → deny; Bash ghi vào GO-NO-GO*.md → deny (sửa bằng Edit để guard so được)
- Lý do (tiêu chí chất lượng cuối): (1) đúng và an toàn: mẫu ghi chữ ký là của người, agent tự ký được thì promotion approved không còn nghĩa; chặn mọi sửa thì agent không lập được phần máy. (3) đơn giản, test bằng payload giả. Giới hạn còn lại (script ghi file với tên dựng lúc chạy) ghi ở harness-files như AUD-SEC-406
- Đường lùi: Revert PR; guard thôi chặn, lớp sau là review PR

### D-391 · 2026-11-07T04:05:22+00:00 · AUD-TEST-061 lộ ra: SARIF thật của gitleaks 8.30.1 không ghi level, adapter coi là warning nên report có leak ra PASS — xử lý thế nào?

- Phương án: (1) Kết quả của công cụ quét bí mật (tool.driver.name gitleaks) là error bất kể level · (2) Giữ theo SARIF §3.27.10, dựa exit code công cụ · (3) Mọi warning là FAIL
- Chọn: Kết quả của công cụ quét bí mật (tool.driver.name gitleaks) là error bất kể level
- Lý do (tiêu chí chất lượng cuối): (1) đúng và an toàn: một leak ra PASS là xanh giả; release-check đọc report, không đọc exit code, nên --exit-code 0 làm cổng xanh. Phương án 3 làm FAIL giả với CodeQL/ruff warning. (3) hẹp, test được bằng fixture thật
- Đường lùi: Revert commit; gitleaks quay về luật level mặc định SARIF

### D-392 · 2026-11-07T04:49:32+00:00 · AUD-SEC-497 (tiếp): agent sửa tiêu đề phiên bản hay dòng subject của GO-NO-GO đã ký → chữ ký người chuyển sang ứng viên mới; guard có chặn?

- Phương án: (1) File trên đĩa đã có dòng ký §5: deny Edit/Write đổi dòng '# ' đầu tiên hoặc dòng 'subject:' (thêm/sửa/xoá) · (2) Giữ cho sửa, review PR là lớp sau
- Chọn: File trên đĩa đã có dòng ký §5: deny Edit/Write đổi dòng '# ' đầu tiên hoặc dòng 'subject:' (thêm/sửa/xoá)
- Lý do (tiêu chí chất lượng cuối): (1) đúng và an toàn: sau AUD-HAR-219 (D-389) chữ ký gắn ứng viên qua dòng subject — agent đổi được dòng đó là lách được cả hai sửa; agent cần đổi thì xoá dòng ký trước (được phép), người ký lại. (2) đường lùi: xoá dòng ký vẫn mở
- Đường lùi: Revert commit; guard chỉ chặn dòng ký

### D-393 · 2026-11-07T05:11:40+00:00 · AUD-HAR-319: subject.content loại file theo TÊN ở mọi cấp (src/DECISIONS.md, src/x/GO-NO-GO-y.md đổi mã vẫn approved) — sửa thế nào?

- Phương án: (1) Vân tay riêng cho subject: chỉ loại GO-NO-GO*.md ở GO_NO_GO_DIRS, sổ DECISIONS_LOG, PROGRESS.md gốc và .autopilot/; giữ evidence_fingerprint cũ cho gói stage · (2) Thu hẹp _signoff_excluded chung · (3) Chấp nhận, ghi giới hạn ở mẫu §1
- Chọn: Vân tay riêng cho subject: chỉ loại GO-NO-GO*.md ở GO_NO_GO_DIRS, sổ DECISIONS_LOG, PROGRESS.md gốc và .autopilot/; giữ evidence_fingerprint cũ cho gói stage
- Lý do (tiêu chí chất lượng cuối): (1) đúng và an toàn: approved phải phủ mọi mã; tập loại trừ hẹp đúng các file ký/sổ máy đọc. (2) đường lùi và không hồi quy: không đổi evidence_fingerprint/_changed_since mà gói stage và AUD-HAR-164 dựa vào. (3) test được bằng repo tạm
- Đường lùi: Revert; subject.content quay về evidence_fingerprint

### D-394 · 2026-11-07T05:35:38+00:00 · Nợ #462/#463: SARIF suppression vắng status, suppression của gitleaks, bản tháng DECISIONS trong vân tay subject — luật nào?

- Phương án: (1) Chặt: chỉ bỏ qua khi mọi suppression ghi rõ status accepted; công cụ quét bí mật không bao giờ bỏ qua (D-391); bản tháng DECISIONS vẫn tính vào vân tay · (2) Lỏng: vắng status = accepted, gitleaks cũng bỏ qua, loại bản tháng
- Chọn: Chặt: chỉ bỏ qua khi mọi suppression ghi rõ status accepted; công cụ quét bí mật không bao giờ bỏ qua (D-391); bản tháng DECISIONS vẫn tính vào vân tay
- Lý do (tiêu chí chất lượng cuối): (1) đúng và an toàn: mặc định khi vắng status chưa xác minh được trong SARIF 2.1.0 errata01 §3.35.3 — cách hiểu chặt; lệch về đỏ giả an toàn hơn xanh giả; bí mật bị chặn trong report vẫn là bí mật trong lịch sử. (2) nới sau được khi có nguồn
- Đường lùi: Đổi một biểu thức trong _sarif_suppressed / bỏ nhánh SECRET_SCANNERS

### D-395 · 2026-11-07T11:38:43+00:00 · Cắt bản sau #462…#469 — 3.31.2 hay 3.32.0?

- Phương án: (1) 3.32.0 (minor): đổi việc dự án đích phải làm (dòng subject GO-NO-GO, D-389) và guard chặn ký §5; không phá tương thích ngược dữ liệu · (2) 3.31.2 (patch)
- Chọn: 3.32.0 (minor): đổi việc dự án đích phải làm (dòng subject GO-NO-GO, D-389) và guard chặn ký §5; không phá tương thích ngược dữ liệu
- Lý do (tiêu chí chất lượng cuối): (1) đúng: SemVer — #463 thêm yêu cầu mới với dự án đích (GO-NO-GO cũ ở lại pending_human tới khi ký lại), không phải vá lỗi thuần; (3) theo chuẩn; nợ review đã trả hết (audit check --strict exit 0), release-check GO chờ người
- Đường lùi: Không merge PR cắt bản; hoặc cắt bản vá sau đó

### D-396 · 2026-11-07T12:18:23+00:00 · PR #470 (cắt 3.32.0): review lượt 1 APPROVE với 1 🟢 — câu GO-NO-GO khai sai trạng thái AUD-SEC-538, sót AUD-HAR-321

- Phương án: (1) Sửa một dòng GO-NO-GO trên nhánh theo đề xuất reviewer (ngoài vân tay subject) · (2) Ghi nhận, giữ nguyên
- Chọn: Sửa một dòng GO-NO-GO trên nhánh theo đề xuất reviewer (ngoài vân tay subject)
- Lý do (tiêu chí chất lượng cuối): (1) GO-NO-GO là tài liệu người ký — không ship lời khai sai; sửa không đổi subject.content (GO-NO-GO ngoài vân tay, đã kiểm)
- Đường lùi: Revert commit sửa

### D-397 · 2026-11-08T00:33:49+00:00 · AUD-HAR-325: install.py ghi git_hooks của manifest.json thế nào khi thư mục hook nằm ngoài cây dự án (git worktree, core.hooksPath ngoài)?

- Phương án: (1) Trong cây dự án → tương đối dự án (như cũ); trong git common dir → '.git/' + đường tương đối common dir (vd .git/hooks/pre-commit, đúng với mọi bản sao); ngoài cả hai → 'core.hooksPath/<tên>' (không ghi đường máy) · (2) Chỉ ghi tên hook · (3) Giữ tuyệt đối, sửa tay mỗi lần
- Chọn: Trong cây dự án → tương đối dự án (như cũ); trong git common dir → '.git/' + đường tương đối common dir (vd .git/hooks/pre-commit, đúng với mọi bản sao); ngoài cả hai → 'core.hooksPath/<tên>' (không ghi đường máy)
- Lý do (tiêu chí chất lượng cuối): (1) đúng và an toàn: manifest.json được commit — không lộ đường máy, giống nhau giữa bản sao chính và worktree; (2) giữ dạng tương đối cũ cho ca thường; (3) git_hooks chỉ để ghi nhận (AUD-HAR-204), không nơi nào đọc lại nên đổi dạng không phá
- Đường lùi: Revert PR; shown_path ghi tuyệt đối như cũ

### D-398 · 2026-11-08T01:54:45+00:00 · Dùng nguồn nào để xác minh artifact sau deploy trong pilot xboss?

- Phương án: (1) Dùng SHA và health do workflow deploy báo. · (2) Staging cô lập tải archive đúng run, kiểm hash và đối chiếu HTTP với bản cài.
- Chọn: Staging cô lập tải archive đúng run, kiểm hash và đối chiếu HTTP với bản cài.
- Lý do (tiêu chí chất lượng cuối): Chủ dự án chọn staging cô lập ngày 2026-11-08. Hash archive và probe HTTP độc lập kiểm được lỗi tráo artifact hoặc route cũ trong khi dùng dữ liệu giả.
- Đường lùi: Gỡ workflow pilot và bỏ biên nhận staging. Luồng production giữ quyền duyệt hiện hành.

### D-399 · 2026-11-08T02:27:59+00:00 · AUD-HAR-327: đóng đề xuất 'Khi chạy thật' thế nào mà không sửa mục cũ của sổ (LOOP-STOP-019)?

- Phương án: (1) Dòng THÊM mới máy đọc: lệnh 'xt.py loop decide-prod --ref D-NNN --choice …' ghi vào sổ hiện hành một mục có dòng 'Khi chạy thật đã quyết (D-NNN): …'; release-check trừ đề xuất có D-NNN đã có dòng quyết; nhãn cũ giữ nguyên · (2) Đổi nhãn dòng cũ (#477) · (3) Ghi quyết định ở GO-NO-GO §5, máy đọc từ đó
- Chọn: Dòng THÊM mới máy đọc: lệnh 'xt.py loop decide-prod --ref D-NNN --choice …' ghi vào sổ hiện hành một mục có dòng 'Khi chạy thật đã quyết (D-NNN): …'; release-check trừ đề xuất có D-NNN đã có dòng quyết; nhãn cũ giữ nguyên
- Lý do (tiêu chí chất lượng cuối): (1) đúng luật sổ chỉ thêm, dấu vết đầy đủ; máy đếm theo ID nên không lệch bản tháng; (2) đường lùi: xoá mục thêm; (3) một lệnh, test được; phương án 3 trộn hai việc (ký bản và quyết dịch vụ) và dời theo từng bản
- Đường lùi: Revert PR; quay về nhãn đổi tay

### D-400 · 2026-11-08T02:56:02+00:00 · Chủ dự án quyết đề xuất "Khi chạy thật" của D-126: Khi cần nhiều người hoặc dùng trên điện thoại: web app lưu trữ (phương án 3) dùng lại API JSON của SPEC-app, cần chủ repo chọn hosting và đăng nhập

- Phương án: (1) Chuyển theo đề xuất của D-126 · (2) Giữ tự host
- Chọn: giữ tự host xt.py app (cục bộ, không hosting/tài khoản), chưa chuyển sang web app lưu trữ; xét lại khi thật sự cần nhiều người hay dùng trên điện thoại — chủ repo quyết 2026-11-08
- Lý do (tiêu chí chất lượng cuối): chủ dự án quyết ở G7 (GO-NO-GO #18) — điểm dừng về hành động, không phải phiên tự duyệt
- Đường lùi: đổi ý → `loop decide` mới nhắc mục này và D-126 (kèm `--prod` nếu chuyển dịch vụ)
- Khi chạy thật đã quyết (D-126): giữ tự host xt.py app (cục bộ, không hosting/tài khoản), chưa chuyển sang web app lưu trữ; xét lại khi thật sự cần nhiều người hay dùng trên điện thoại — chủ repo quyết 2026-11-08

### D-401 · 2026-11-08T09:40:44+00:00 · Chủ repo 2026-11-08: 'cho agent ký GO-NO-GO' — agent ký §5 thế nào cho đúng và an toàn, áp ở đâu?

- Phương án: (1) Khoá release_signoff: agent theo mẫu ADR-0069 (cây + nhánh chính, HARD_GATED); lệnh xt.py release-sign chỉ ký khi release-check không FAIL BLOCKER, việc người còn lại chỉ là chữ ký, subject khớp; ô tên ghi agent; guard chỉ cho một lệnh đơn chữ rõ; repo khung bật, mẫu dự án đích để trống (opt-in) · (2) Bỏ luật GO_SIGN, agent ghi dòng ký bằng Edit như người · (3) Cùng khoá nhưng mẫu dự án đích bật sẵn agent như stage_approval
- Chọn: Khoá release_signoff: agent theo mẫu ADR-0069 (cây + nhánh chính, HARD_GATED); lệnh xt.py release-sign chỉ ký khi release-check không FAIL BLOCKER, việc người còn lại chỉ là chữ ký, subject khớp; ô tên ghi agent; guard chỉ cho một lệnh đơn chữ rõ; repo khung bật, mẫu dự án đích để trống (opt-in)
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1 (đúng/an toàn, cách hiểu chặt): chữ ký agent chỉ có khi máy đã đạt mọi hàng BLOCKER và ghi rõ là agent (không mạo danh người, P1); quyền đến từ cấu hình đã commit ở nhánh chính nên phiên không tự cấp; tiêu chí 2: đường lùi một dòng. Dự án đích có thể có người dùng thật/DPIA nên chỉ bật khi chủ dự án chọn (phương án 3 chặt kém hơn).
- Đường lùi: Đặt release_signoff: human hoặc xoá khoá ở xt.yaml (PR người merge); chữ ký agent cũ hết hạn sau release_approval_days

### D-402 · 2026-11-08T10:03:55+00:00 · Phản biện ADR-0074: PR mồi vừa thêm release_signoff vào HARD_GATED_KEYS vừa bật khoá — steward chạy xt.py của main (chưa biết khoá) có thể tự merge; điều kiện ký chưa xét loop defer và quy mô M/L; in-process và --blueprint/--status làm giả release-check; đổi nhánh mặc định dời ruleset khỏi main. Làm gì?

- Phương án: (1) Tách: PR này chỉ thêm mã + khoá dạng chú thích, PR sau bật khoá (người merge); release-sign đòi scale S và không còn loop defer; bỏ --blueprint/--status/--unchecked-must; guard chặn in-process sign/release, đổi nhánh mặc định, MCP ghi thẳng main · (2) Giữ một PR bật luôn khoá, ghi giới hạn vào ADR
- Chọn: Tách: PR này chỉ thêm mã + khoá dạng chú thích, PR sau bật khoá (người merge); release-sign đòi scale S và không còn loop defer; bỏ --blueprint/--status/--unchecked-must; guard chặn in-process sign/release, đổi nhánh mặc định, MCP ghi thẳng main
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1: khoá nới chỉ có hiệu lực khi người merge một PR mà máy đã biết là khoá chỉ người đổi; điều kiện ký chặt theo cách hiểu an toàn; đóng ba đường làm giả mà phản biện tìm ra. Tiêu chí 2: mỗi phần đảo ngược được bằng revert.
- Đường lùi: Revert từng thay đổi guard/xt.py; khoá vẫn tắt nên không có hiệu lực tới khi PR bật được merge

### D-403 · 2026-11-08T10:39:31+00:00 · Cắt bản sau #472…#479 (decide-prod, AUD-HAR-325/327…331) — 3.33.0 hay 3.32.1, cắt ngay hay chờ PR đang mở (#474, #480)?

- Phương án: (1) 3.33.0 (minor) cắt ngay từ main a09f7a7: thêm lệnh loop decide-prod và mẫu GO-NO-GO #18 trỏ lệnh này (đổi việc dự án đích); AUD-HAR-329 làm GO-NO-GO đã ký của dự án đích về chờ người — vá sớm; PR đang mở vào bản kế · (2) 3.32.1 (patch) cắt ngay · (3) Chờ #480/#474 merge rồi cắt chung
- Chọn: 3.33.0 (minor) cắt ngay từ main a09f7a7: thêm lệnh loop decide-prod và mẫu GO-NO-GO #18 trỏ lệnh này (đổi việc dự án đích); AUD-HAR-329 làm GO-NO-GO đã ký của dự án đích về chờ người — vá sớm; PR đang mở vào bản kế
- Lý do (tiêu chí chất lượng cuối): (1) đúng: SemVer — #478 thêm lệnh mới và đổi mẫu dự án đích, không phải vá thuần; AUD-HAR-329 đang làm chữ ký §5 của dự án đích về pending_human khi ghi quyết định vào bản tháng — giữ lại là để lỗi chạy tiếp; release-check trên main a09f7a7 ra GO (sau unshallow); (2) PR đang mở chưa review/CI đỏ (#480 gitleaks), chờ chúng là treo bản vá vô hạn; AGENTS §7 cắt bản sớm khi đổi việc dự án đích
- Đường lùi: Không merge PR cắt bản; hoặc cắt bản vá sau đó

### D-404 · 2026-11-09T01:53:24+00:00 · PR #480 (release-sign, ADR-0074): kiểm lại bản sửa ac81683 còn 2 🔴 (NO-GO người trên nhánh PR bị xoá rồi ký; dự án thư mục con quét rỗng) và 🟠 (ô Không GO/Hold, đổi VERSION né lọc, dòng NO-GO thiếu ngày, xoá đã lên main). Sửa thế nào?

- Phương án: (1) Quét LỊCH SỬ: release_sign từ chối khi bất kỳ blob GO-NO-GO*.md (mọi thư mục, mọi độ sâu, mọi phiên bản) từng xuất hiện trong lịch sử của mọi ref cục bộ và remote (git log --all) có dòng quyết định của người (tên khác agent) mà ô quyết định không phải GO — kể cả thiếu ngày/ô ?; lời từ chối chỉ hết hiệu lực khi một commit sau nó thêm dòng GO của người, hoặc quá release_approval_days tính từ ngày commit; không đọc được lịch sử → từ chối · (2) Vá từng lỗ trên cách quét hiện có (thêm ref nhánh PR, sửa đường thư mục con, coi ô ? là từ chối, bỏ lọc VERSION) · (3) Bỏ hẳn release-sign khỏi PR này, chỉ giữ nghiên cứu + ADR ở trạng thái Đề xuất
- Chọn: Quét LỊCH SỬ: release_sign từ chối khi bất kỳ blob GO-NO-GO*.md (mọi thư mục, mọi độ sâu, mọi phiên bản) từng xuất hiện trong lịch sử của mọi ref cục bộ và remote (git log --all) có dòng quyết định của người (tên khác agent) mà ô quyết định không phải GO — kể cả thiếu ngày/ô ?; lời từ chối chỉ hết hiệu lực khi một commit sau nó thêm dòng GO của người, hoặc quá release_approval_days tính từ ngày commit; không đọc được lịch sử → từ chối
- Lý do (tiêu chí chất lượng cuối): (1) đúng và an toàn: lịch sử git là nơi lời từ chối của người không xoá được bằng commit mới — đóng cùng lúc nhánh PR, xoá đã lên main, đổi tên/đổi VERSION, thư mục con (pathspec theo tên ở mọi độ sâu), dòng thiếu ngày/ô ?; phương án 2 vẫn là danh sách chặn từng lỗ (đã vỡ 2 lần); (2) giữ đường lùi: khoá release_signoff vẫn tắt mặc định, bỏ dòng khoá là về người ký; (3) một luật, test được bằng fixture sẵn có; phương án 3 bỏ yêu cầu của chủ repo (D-401) khi có cách làm đúng. Còn lại có từ trước, ghi nợ: neo tin cậy ref theo dõi cũ (agent không fetch) — cùng lớp release_agent_signoff/_main_key_is
- Đường lùi: Revert commit sửa; hoặc bỏ release-sign (phương án 3)

### D-405 · 2026-11-09T02:15:25+00:00 · D-404 (quét lịch sử lời từ chối GO-NO-GO): hạn hiệu lực theo release_approval_days đọc từ xt.yaml cây làm việc — agent đặt release_approval_days: 1 là mọi NO-GO cũ hết hiệu lực. Giữ hạn thế nào?

- Phương án: (1) Bỏ hết hạn theo tuổi: lời từ chối của người chỉ gỡ bằng một dòng GO của người ở commit sau (thay một phần D-404) · (2) Đưa release_approval_days vào HARD_GATED_KEYS (ảnh hưởng cả promotion) · (3) Hạn = max(cấu hình, 30 ngày) · (4) Đọc khoá cả ở nhánh chính như _main_key_is
- Chọn: Bỏ hết hạn theo tuổi: lời từ chối của người chỉ gỡ bằng một dòng GO của người ở commit sau (thay một phần D-404)
- Lý do (tiêu chí chất lượng cuối): (1) đúng và an toàn: không còn tham số agent sửa được trong điều kiện ký; người đã từ chối thì người gỡ — đúng ý ADR-0074 'Giữ: lời từ chối NO-GO'; phương án 3 vẫn hết hạn tự động, 2/4 thêm bề mặt cấu hình; (3) bỏ một nhánh mã và một nguồn cấu hình, test được; (4) dự án có NO-GO cũ mà người chưa ký GO lần nào sau đó thì agent không ký được — người ký một lần là gỡ
- Đường lùi: Khôi phục nhánh hết hạn theo release_approval_days (D-404 nguyên bản)

### D-406 · 2026-11-09T06:03:25+00:00 · PR #480 vòng kiểm 3: quét lịch sử git CỤC BỘ (D-404) lách được bằng lệnh guard cho qua — merge -s ours (giản lược lịch sử), fetch --depth=1 (shallow), branch -rd / filter-branch / push --delete (xoá ref), fetch repo ngoài (GO người lạ gỡ mọi NO-GO); config log.showRoot; gỡ lời từ chối toàn cục; chặn oan GO viết tự do. Neo tin cậy ở đâu?

- Phương án: (1) Neo ở REMOTE: release_sign tự clone --mirror mới của remote origin (gồm refs/pull/*/head GitHub giữ vĩnh viễn) vào thư mục tạm, cấu hình git cô lập (GIT_CONFIG_GLOBAL/NOSYSTEM, -c log.showRoot=true), quét git log --all --full-history -p ở đó; lời từ chối = hợp của bản mirror và lịch sử cục bộ; dòng GO gỡ lời từ chối CHỈ tính từ bản mirror và chỉ gỡ lời từ chối cùng phiên bản (vX.Y.Z trong tên tệp/tiêu đề) hoặc phiên bản lớn hơn; không clone được (mạng, không có origin) → từ chối; nhận ô GO viết tự do (bỏ **, sau GO là dấu câu/chữ) · (2) Vá tiếp trên lịch sử cục bộ: chặn branch -rd/fetch --depth/merge -s ours ở guard, --full-history, lọc ref ngoài · (3) Rút release-sign khỏi PR #480, giữ nghiên cứu + ADR-0074 ở trạng thái Đề xuất, làm lại ở PR riêng
- Chọn: Neo ở REMOTE: release_sign tự clone --mirror mới của remote origin (gồm refs/pull/*/head GitHub giữ vĩnh viễn) vào thư mục tạm, cấu hình git cô lập (GIT_CONFIG_GLOBAL/NOSYSTEM, -c log.showRoot=true), quét git log --all --full-history -p ở đó; lời từ chối = hợp của bản mirror và lịch sử cục bộ; dòng GO gỡ lời từ chối CHỈ tính từ bản mirror và chỉ gỡ lời từ chối cùng phiên bản (vX.Y.Z trong tên tệp/tiêu đề) hoặc phiên bản lớn hơn; không clone được (mạng, không có origin) → từ chối; nhận ô GO viết tự do (bỏ **, sau GO là dấu câu/chữ)
- Lý do (tiêu chí chất lượng cuối): (1) đúng và an toàn: agent không viết lại được lịch sử remote (guard chặn force-push, ruleset main) và không xoá được refs/pull/* — đóng cả lớp xoá ref/shallow/rewrite/repo ngoài một lần, thay vì danh sách chặn guard (đã vỡ 3 vòng); GO gỡ chỉ từ remote nên fetch repo ngoài không gỡ được; fail-closed khi offline; (2) đường lùi: khoá release_signoff vẫn tắt mặc định; (3) một nguồn tin cậy, test bằng remote bare cục bộ; (4) chi phí: clone mirror mỗi lần ký — chấp nhận, ký hiếm. Phương án 3 bỏ yêu cầu D-401 khi đã có cách làm đúng. Giới hạn còn lại đã khai: GO_SIGN lọt tên dựng lúc chạy (dòng GO giả tên người) — ranh giới là sandbox
- Đường lùi: Revert commit; hoặc phương án 3

### D-407 · 2026-11-09T07:58:16+00:00 · AUD-SEC-551 (nợ #480): guard cho git push --delete nhánh remote khác main và filter-branch -- --all; NO-GO của người trên nhánh chưa có PR bị xoá thì release-sign ký được. Sửa thế nào?

- Phương án: (1) Guard xếp vào nhóm không đảo ngược (deny): xoá nhánh/tag remote khác nhánh hiện tại của phiên — git push <remote> --delete|-d <ref>, git push <remote> :<ref>, git push --prune, gh api -X DELETE …/git/refs/…; và git filter-branch / filter-repo có --all hoặc --branches/--tags; xoá nhánh của chính phiên (HEAD hiện tại) vẫn cho · (2) Chỉ ghi luật: NO-GO của người phải đi qua PR (refs/pull/*) mới bền; không đổi guard · (3) release-sign từ chối khi reflog/ref theo dõi cục bộ có nhánh remote đã mất
- Chọn: Guard xếp vào nhóm không đảo ngược (deny): xoá nhánh/tag remote khác nhánh hiện tại của phiên — git push <remote> --delete|-d <ref>, git push <remote> :<ref>, git push --prune, gh api -X DELETE …/git/refs/…; và git filter-branch / filter-repo có --all hoặc --branches/--tags; xoá nhánh của chính phiên (HEAD hiện tại) vẫn cho
- Lý do (tiêu chí chất lượng cuối): (1) đúng và an toàn: xoá nhánh của người khác và viết lại mọi ref là hành động khó đảo ngược — đúng nhóm máy chặn của ADR-0018, và đóng đường xoá NO-GO khỏi neo D-406; phương án 2 để lỗ mở, 3 không đáng tin (reflog/ref cục bộ agent sửa được); (2) đường lùi: người tự chạy lệnh ngoài phiên; xoá nhánh của chính phiên vẫn được; (3) luật guard test được bằng payload giả + autonomy-bench (đo chặn oan trên corpus)
- Đường lùi: Gỡ luật mới khỏi guard (revert PR)

### D-408 · 2026-11-09T13:20:05+00:00 · AUD-SEC-571 (🔴): cờ ăn giá trị đứng trước lệnh con gh (cobra nhấc lên) lách các luật gh khác (api xoá repo, api xoá ref, api gộp PR, repo edit visibility). Sửa thế nào?

- Phương án: (1) Chuẩn hoá một lần ở đầu _gh_rule: tách cờ ăn giá trị trước lệnh con theo cobra stripFlags rồi dời đường lệnh con lên đầu, mọi luật gh đọc dạng đã chuẩn hoá; giữ cách đọc cũ làm đường chặt (deny nếu một trong hai cách đọc deny) · (2) Vá từng luật (api, các cặp trong GH_ASK)
- Chọn: Chuẩn hoá một lần ở đầu _gh_rule: tách cờ ăn giá trị trước lệnh con theo cobra stripFlags rồi dời đường lệnh con lên đầu, mọi luật gh đọc dạng đã chuẩn hoá; giữ cách đọc cũ làm đường chặt (deny nếu một trong hai cách đọc deny)
- Lý do (tiêu chí chất lượng cuối): (1) đúng và an toàn: đóng cả lớp một lần cho mọi luật gh hiện có và sau này — vá từng luật đã để lọt ở AUD-SEC-570 rồi 571; đọc cả hai cách (như push AUD-SEC-102) giữ chiều chặt; (3) một chỗ, test được bằng corpus; (2) đường lùi: revert
- Đường lùi: Revert PR sửa AUD-SEC-571

### D-409 · 2026-11-09T16:03:32+00:00 · AUD-SEC-575/577/578/579 + AUD-DOC-281: ngoài _gh_rule, các nơi khác trong guard đọc lệnh gh nguyên văn (_gh_kind cho alias/extension/lệnh lạ, luật dấu review, luật ghi công AI/tiêu đề PR, luật gửi bí mật) nên cờ đứng trước lệnh con lách được. Sửa thế nào?

- Phương án: (1) Một điểm vào duy nhất: mọi luật đọc lệnh gh nhận dạng chuẩn hoá cobra (đường lệnh con theo cobra stripFlags, KHÔNG phụ thuộc bảng nhóm khi xác định token đầu — để alias/extension/lệnh lạ cũng được nhận đúng) và dạng nguyên văn; quyết định chặt hơn thắng; thay D-408 ở phạm vi (D-408 chỉ áp trong _gh_rule) · (2) Vá từng luật còn lại
- Chọn: Một điểm vào duy nhất: mọi luật đọc lệnh gh nhận dạng chuẩn hoá cobra (đường lệnh con theo cobra stripFlags, KHÔNG phụ thuộc bảng nhóm khi xác định token đầu — để alias/extension/lệnh lạ cũng được nhận đúng) và dạng nguyên văn; quyết định chặt hơn thắng; thay D-408 ở phạm vi (D-408 chỉ áp trong _gh_rule)
- Lý do (tiêu chí chất lượng cuối): (1) đúng và an toàn: đã vá từng luật hai lần (570, 571) và vẫn sót ba lớp — một điểm vào đóng cả lớp kể cả luật thêm sau; đọc hai cách giữ chiều chặt; (3) một hàm, test bằng corpus đối chiếu dạng cờ-trước-lệnh-con với dạng chuẩn cho MỌI ca gh đang có
- Đường lùi: Revert PR sửa

### D-410 · 2026-11-10T06:37:59+00:00 · Review #491: phần gỡ chặn oan REVIEW_FORGE (AUD-HAR-364: GH_POST_ARGV_RE, _gh_wrapped điều kiện dương) nới hai đường giả dấu review mà main chặn (lệnh con dính mở rộng rỗng gh pr comment$Z; lệnh trong tham số sh -c và giá trị TÊN=… như GIT_EDITOR). Xử lý thế nào?

- Phương án: (1) Rút phần AUD-HAR-364 khỏi #491, khôi phục hành vi main cho lọc dấu review, thêm test ghim mọi dạng giả dấu reviewer tìm ra (deny REVIEW_FORGE); AUD-HAR-364 về mở, làm lại ở PR riêng với thiết kế chặt · (2) Vá ngay trong #491 (đuôi regex nhận $/backtick, quay về phép thử chữ ghép khi có token động, đọc giá trị TÊN=… như chữ shell)
- Chọn: Rút phần AUD-HAR-364 khỏi #491, khôi phục hành vi main cho lọc dấu review, thêm test ghim mọi dạng giả dấu reviewer tìm ra (deny REVIEW_FORGE); AUD-HAR-364 về mở, làm lại ở PR riêng với thiết kế chặt
- Lý do (tiêu chí chất lượng cuối): (1) đúng và an toàn: REVIEW_FORGE là luật 🔴; gỡ một chặn oan 🟢 không đáng đổi bằng hai đường giả dấu — rút về main là chắc chắn không nới; vá tại chỗ là thiết kế mới chưa được review; (2) đường lùi: PR riêng cho AUD-HAR-364; (3) test ghim giữ chiều chặt cho lần sau
- Đường lùi: Khôi phục phần AUD-HAR-364 ở PR riêng sau review

### D-411 · 2026-11-10T07:46:13+00:00 · AUD-SEC-587 (tên lệnh/cờ gh có mở rộng): ở XT_GUARD_POLICY=strict trả ask/BUDGET hay raise ScanTooComplex (chặn ở mọi chính sách như lớp A ADR-0065)?

- Phương án: (1) ask/BUDGET: mặc định chặn, strict hỏi người; lệnh có dấu review giữ mã REVIEW_FORGE · (2) ScanTooComplex: chặn ở mọi chính sách; ca REVIEW_FORGE đổi thành BUDGET
- Chọn: ask/BUDGET: mặc định chặn, strict hỏi người; lệnh có dấu review giữ mã REVIEW_FORGE
- Lý do (tiêu chí chất lượng cuối): (1) an toàn: không có đường cho qua — mặc định chặn, strict là chế độ người duyệt từng lệnh nên hỏi là đúng ngữ nghĩa strict; (3) giữ mã REVIEW_FORGE chính xác hơn cho lệnh giả dấu, test ghim D-410 không phải đổi
- Đường lùi: Đổi _gh_dyn_name sang raise ScanTooComplex

### D-412 · 2026-11-10T09:22:40+00:00 · Câu hỏi mở của executor #492 (mở rộng trong nháy kép đứng riêng ở vị trí cờ; mở rộng không nháy dính sau chữ; lệnh đăng chữ với biến đứng riêng): sửa ngay trong #492 hay ghi nợ?

- Phương án: (1) Ghi nợ 🟠 riêng (AUD-SEC-591…593), làm ở lát sau với thiết kế chung (xét phương án miễn đối số vị trí đầu) · (2) Mở rộng #492 chặn mọi token chỉ gồm mở rộng ở lệnh có luật cờ
- Chọn: Ghi nợ 🟠 riêng (AUD-SEC-591…593), làm ở lát sau với thiết kế chung (xét phương án miễn đối số vị trí đầu)
- Lý do (tiêu chí chất lượng cuối): (1) an toàn: #492 không nới gì, chỉ chặt thêm; các dạng còn hở đã hở trên main và có dòng sổ; (3) phương án chặn rộng chặn oan lệnh đóng/merge PR có số PR trong biến — cần đo trên lệnh thật trước khi chọn; lát nhỏ (P8)
- Đường lùi: Gộp vào lát sau

### D-413 · 2026-11-10T11:52:01+00:00 · release-sign (AUD-HAR-340, #493): không worktree nào có .autopilot/state.json thì sao?

- Phương án: (1) Từ chối ký (fail-closed); cần loop init trước — đường /complete đã có bước này · (2) Coi sổ vắng là không có việc chờ
- Chọn: Từ chối ký (fail-closed); cần loop init trước — đường /complete đã có bước này
- Lý do (tiêu chí chất lượng cuối): (1) đúng và an toàn: .autopilot/ không commit nên clone riêng không biết sổ dự án chính — coi vắng là sạch mở lại đúng lỗ AUD-HAR-340; (2) đường lùi: loop init tạo sổ rỗng; khoá release_signoff hiện chưa bật nên không chặn ai
- Đường lùi: Cho sổ vắng ở mọi worktree là không có việc chờ

### D-414 · 2026-11-10T15:03:52+00:00 · Workflow thiết kế AUD-SEC-591/592/593 phát hiện lỗi gốc: từ chỉ gồm toán tử shell trong nháy (';' hay dấu ống trong nháy đơn) làm tokenize/split_commands cắt lệnh ở MỌI luật (git push có --force sau ';' trong nháy được cho qua — đã tái hiện). Thứ tự làm và 4 điểm spec để phiên chính quyết?

- Phương án: (1) Sửa gốc tokenizer trước ở PR riêng (🔴), rồi PR cài spec 591/592/593 không cần vá tạm R0; nhận cả 4 khuyến nghị của spec: bỏ miễn trừ thân không nháy, pr close chế độ tail, bảng 12 hàng lệnh đăng chữ · (2) Cài spec kèm vá tạm R0 trong lớp gh trước, mở dòng 🔴 cho gốc làm sau
- Chọn: Sửa gốc tokenizer trước ở PR riêng (🔴), rồi PR cài spec 591/592/593 không cần vá tạm R0; nhận cả 4 khuyến nghị của spec: bỏ miễn trừ thân không nháy, pr close chế độ tail, bảng 12 hàng lệnh đăng chữ
- Lý do (tiêu chí chất lượng cuối): (1) đúng và an toàn: lỗi gốc lách cả luật force-push và no-verify, nặng hơn ba nợ 🟠 — sửa gốc đóng mọi luật, vá tạm chỉ đóng gh; (3) đơn giản hơn: không thêm R0 rồi gỡ; các khuyến nghị spec đều là cách hiểu chặt hơn và đã đo 0 chặn oan trên lệnh thật
- Đường lùi: Tách lại: R0 trong lớp gh

### D-415 · 2026-11-11T03:22:00+00:00 · Review #495 BLOCKING: 7 hồi quy 🔴 đều đến từ phần mở rộng (GlueWord, _SubstTrack/PROCSUB_WORD, đường lùi flat của tokenize), còn lõi LitWord được xác nhận đúng và không chặn oan. Sửa thế nào?

- Phương án: (1) Thu hẹp #495 về lõi: giữ LitWord + bỏ chuyển hướng ở chữ đọc lại (eval, echo nối ống sang sh) + watch; gỡ GlueWord, _SubstTrack/PROCSUB_WORD và đường lùi flat, trả hành vi của main cho thay tiến trình/thay lệnh; các dạng thay tiến trình/thay lệnh che phần sau (main cũng hở) ghi 🔴 mở riêng, làm ở PR sau theo hướng chặn khi không đọc chắc · (2) Vá từng hồi quy trong #495, giữ nguyên thiết kế mở rộng
- Chọn: Thu hẹp #495 về lõi: giữ LitWord + bỏ chuyển hướng ở chữ đọc lại (eval, echo nối ống sang sh) + watch; gỡ GlueWord, _SubstTrack/PROCSUB_WORD và đường lùi flat, trả hành vi của main cho thay tiến trình/thay lệnh; các dạng thay tiến trình/thay lệnh che phần sau (main cũng hở) ghi 🔴 mở riêng, làm ở PR sau theo hướng chặn khi không đọc chắc
- Lý do (tiêu chí chất lượng cuối): (1) đúng và an toàn: phần mở rộng đã hai lượt liên tiếp sinh hồi quy — mỗi lần vá thêm một cách đọc là thêm chỗ lệch với bash; gỡ về main chắc chắn không yếu hơn main ở lớp đó; lõi LitWord đóng đúng lỗ đã tái hiện; (2) đường lùi: PR riêng cho lớp thay tiến trình; (3) nhỏ, review được (P8) — diff hiện 647 dòng
- Đường lùi: Khôi phục phần mở rộng ở PR riêng

### D-416 · 2026-11-11T08:34:16+00:00 · Duyệt PLAN-harden-2026-11-11 (audit delta 454d146..7ca87a6: 3 🔴 mới, 5 🟠 mới, 4 🔴 guard có từ trước, tối ưu có số)

- Phương án: (1) Sửa mọi 🔴 (mới + có từ trước) và 🟠 mới theo lát ≤150 dòng, tối ưu rủi ro thấp có số; 🟠 guard có từ trước để PLAN kế · (2) Chỉ sửa 🔴 mới rồi cắt bản; phần còn lại ghi nợ · (3) Gom mọi 🔴/🟠 mở (kể cả 16 🟠 cũ) và cache bytecode guard vào một đợt
- Chọn: Sửa mọi 🔴 (mới + có từ trước) và 🟠 mới theo lát ≤150 dòng, tối ưu rủi ro thấp có số; 🟠 guard có từ trước để PLAN kế
- Lý do (tiêu chí chất lượng cuối): (1) đúng và an toàn: 7 🔴 mở đều là đường lách hàng rào hoặc ghi ngoài dự án — sửa hết trước khi cắt 3.34.0; (2) giữ đường lùi: mỗi lát một PR nhỏ, test đỏ trước; (3) bền: 609/606 theo bài học D-415 (không đọc chắc → BUDGET); cache bytecode ngược AUD-SEC-074 nên cần ADR riêng; (5) phương án 3 quá rộng cho một đợt
- Đường lùi: Revert từng PR lát; PLAN kế nhận phần còn lại

### D-417 · 2026-11-11T14:21:06+00:00 · AUD-SEC-615: guard GO_SIGN mô hình tool Edit thế nào khi ba lượt review liên tiếp đều tìm ra chỗ mô hình lệch tool thật (CR trần, new_string rỗng nuốt xuống dòng, khớp dự phòng nháy cong và escape unicode, old phải duy nhất)?

- Phương án: (1) Thêm tiếp từng mô hình Edit theo mã tool hiện hành · (2) Chặt: với file GO-NO-GO, Edit/MultiEdit chỉ cho qua khi không mang nội dung dạng dòng ký hay neo; mọi thay đổi chạm §5, tiêu đề, subject đi bằng Write cả file — Write là nội dung y nguyên nên guard đọc đúng như release-check; CR không kèm LF và BOM lệch đĩa thì chặn · (3) Giữ bản vá lượt 3, ghi nợ các ca còn lọt
- Chọn: Chặt: với file GO-NO-GO, Edit/MultiEdit chỉ cho qua khi không mang nội dung dạng dòng ký hay neo; mọi thay đổi chạm §5, tiêu đề, subject đi bằng Write cả file — Write là nội dung y nguyên nên guard đọc đúng như release-check; CR không kèm LF và BOM lệch đĩa thì chặn
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1 (đúng và an toàn, cách hiểu chặt hơn) và 3 (đơn giản, test được): mô hình theo mã tool bị minify sẽ lệch mỗi lần tool đổi bản — đúng bài học D-415 (ca không đọc chắc thì chặn, không thêm cách đọc mới). Write cả file không cần mô hình. Giá phải trả: agent sửa GO-NO-GO bằng Write thay Edit (tiêu chí 4, thấp hơn).
- Đường lùi: Bỏ luật chặn Edit trên GO-NO-GO và quay lại mô hình hai cách áp của lượt 3 (patch lượt 3 lưu ở scratch slices/sec615.patch trước khi sửa)

### D-418 · 2026-11-11T14:21:20+00:00 · D-417 nói Edit trên GO-NO-GO cho qua khi không mang nội dung dạng dòng ký — nhưng ca A1 của review lượt 3 (Edit xoá một ký tự làm hai dòng nối thành dòng ký) không mang nội dung như vậy. Phạm vi luật chặn Edit là gì?

- Phương án: (1) Chặn mọi Edit/MultiEdit lên file GO-NO-GO (kể cả file chưa ký); sửa GO-NO-GO chỉ bằng Write cả file hoặc xt.py release-sign · (2) Chỉ chặn Edit có nội dung dạng dòng ký/neo như chữ của D-417
- Chọn: Chặn mọi Edit/MultiEdit lên file GO-NO-GO (kể cả file chưa ký); sửa GO-NO-GO chỉ bằng Write cả file hoặc xt.py release-sign
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1: một Edit bất kỳ có thể nối dòng thành chữ ký mà chuỗi old/new không lộ gì; chỉ luật không phụ thuộc mô hình tool mới đóng được lớp này. Đính chính phạm vi D-417, không đổi hướng.
- Đường lùi: Nới về phương án 2 kèm mô hình Edit của lượt 3

### D-419 · 2026-11-11T17:40:19+00:00 · Chủ dự án 2026-11-11 (tầm nhìn xưởng tự động đầu-cuối: người chỉ nêu ý tưởng, ra sản phẩm triển khai được) trả lời ba câu hỏi của phiên: song song nếu không chạm cùng file; thiết lập sau khi lên bản dev; ở mọi quy mô — máy hoá thế nào?

- Phương án: (1) ADR-0075: dây chuyền đầu-cuối trên lõi hiện có — đơn vị thành công là ý tưởng tới bản dev có receipt không hỏi người; song song mặc định khi files: đã khai không giao và diff thật nằm trong files: (máy kiểm), file mọi PR cùng chạm do phiên điều phối ghi hoặc theo mảnh; agent ký và duyệt giai đoạn ở S/M/L qua khoá HARD_GATED với hàng bằng chứng máy thay dòng người dùng thử; việc người gom một checklist in ra khi bản dev xanh; cơ chế chất lượng bù (nghiệm thu độc lập, đúng digest, tự quay lui, chữ ký chặn phân phối) merge trước phần nới · (2) Giữ lộ trình cũ: ADR-0068 lát C–E và S1–S11 của research 2026-11-08, tuần tự, agent ký chỉ ở quy mô S · (3) Nền tảng điều phối tập trung quản agent, build, deploy nhiều dự án
- Chọn: ADR-0075: dây chuyền đầu-cuối trên lõi hiện có — đơn vị thành công là ý tưởng tới bản dev có receipt không hỏi người; song song mặc định khi files: đã khai không giao và diff thật nằm trong files: (máy kiểm), file mọi PR cùng chạm do phiên điều phối ghi hoặc theo mảnh; agent ký và duyệt giai đoạn ở S/M/L qua khoá HARD_GATED với hàng bằng chứng máy thay dòng người dùng thử; việc người gom một checklist in ra khi bản dev xanh; cơ chế chất lượng bù (nghiệm thu độc lập, đúng digest, tự quay lui, chữ ký chặn phân phối) merge trước phần nới
- Lý do (tiêu chí chất lượng cuối): Chủ dự án chốt ba trả lời; phiên chọn cách máy hoá theo tiêu chí chất lượng cuối: (1) đúng/an toàn — điều kiện song song do máy kiểm thay lời khai, khoá nới vẫn trong HARD_GATED_KEYS và người merge một lần, tiền/dữ liệu thật/pháp lý vẫn qua grant và loop defer, cơ chế bù có trước phần nới; (2) đường lùi — mỗi năng lực một khoá, mỗi lát một PR; (3) đơn giản — dựng trên xt.py, install.py, gói và registry sẵn có, không tách xt.py, một gói trong 3.x; phương án 2 không cho bản chạy và M/L luôn chờ người, phương án 3 đã loại ở ADR-0068. Thay một phần D-142 (không song song worktree), mặc định self của ADR-0061, điều kiện scale S của ADR-0074, giai đoạn 2/3 chỉ người của ADR-0058/0069 — có hiệu lực khi lát tương ứng có mã
- Đường lùi: PR này chỉ có tài liệu: revert là về hiện trạng; khi có mã, mỗi năng lực lùi bằng khoá của nó (song song về self, release_signoff và khoá giai đoạn về human hoặc bỏ khoá)

### D-420 · 2026-11-11T17:40:19+00:00 · Duyệt PLAN-factory-e2e (ADR-0075): 24 task T-3740…T-3763 trong 8 lát — thứ tự nào?

- Phương án: (1) Bản dev trước (Lát 0–2, pilot 1) → chất lượng bù (Lát 3) → song song (Lát 4) → mọi quy mô (Lát 5, sau Lát 3) → thiết lập một lần và production (Lát 6) → vòng học, kênh vào, pilot 2 (Lát 7) · (2) Song song và worker ngoài phiên trước để mọi lát sau chạy nhanh hơn, rồi mới bản dev · (3) Mở mọi quy mô trước (bỏ scale S của release-sign, giai đoạn 2/3) rồi mới nghiệm thu độc lập và bản dev
- Chọn: Bản dev trước (Lát 0–2, pilot 1) → chất lượng bù (Lát 3) → song song (Lát 4) → mọi quy mô (Lát 5, sau Lát 3) → thiết lập một lần và production (Lát 6) → vòng học, kênh vào, pilot 2 (Lát 7)
- Lý do (tiêu chí chất lượng cuối): (1) đúng/an toàn: phần nới ở M/L chỉ vào sau khi nghiệm thu độc lập, receipt và tự quay lui đã merge — phương án 3 bỏ chốt người khi chưa có gì bù; (2) đường lùi: lát dọc mỏng trước cho số đo thật (pilot 1) trước khi đổi mô hình điều phối; (3) đơn giản: trong repo khung phần lớn task cùng ghi scripts/xt.py nên song song trước (phương án 2) ít lợi mà thêm rủi ro tích hợp khi chưa có phép so diff với files:; đúng lời chủ dự án thiết lập sau khi lên bản dev — không việc người nào trước pilot 1; công nghệ bản dev chưa chọn, T-3740 tra nguồn sống rồi T-3741 chốt bằng ADR
- Đường lùi: Xoá hoặc sửa PLAN-factory-e2e.md bằng PR; task chưa có mã nên không cần hoàn tác gì khác
- Đính chính (2026-11-11, cùng PR): chủ dự án hỏi "có bao gồm các đề xuất bổ sung chưa" — đối chiếu bảy đề xuất thấy sót Routine tuần/phân loại phản hồi, PR nâng dự án đích sau tag và chi phí mỗi lát → thêm T-3764, T-3765, sửa T-3754; PLAN nay 26 task T-3740…T-3765, thứ tự lát không đổi.
- Đính chính số (khi gộp `main` #503, 2026-11-11): `main` đã cấp T-3740 cho việc khác ở PLAN-harden-2026-11-11 — task nghiên cứu của PLAN-factory-e2e đánh số lại thành T-3766 để không tái sử dụng ID; PLAN là T-3741…T-3766.
- Đính chính số (khi gộp `main` #504, 2026-11-11): `main` tiếp tục cấp T-3741, T-3742 cho việc khác ở PLAN-harden-2026-11-11 — cả dải của PLAN-factory-e2e dời sang T-3841…T-3866 (T-37xx → T-38xx, giữ hai chữ số cuối) để hết trùng với phiên đang cấp số tuần tự; các số T-37xx ở mục này và ở commit cũ của nhánh đọc theo phép dời đó.

### D-422 · 2026-11-11T19:40:12+00:00 · Chủ dự án 2026-11-11: còn gì cần viết đặc tả thì viết nốt trước — duyệt bảy đặc tả SPEC-factory-* (deploy, intake, acceptance, parallel, scale, setup, learning) của PLAN-factory-e2e với các lựa chọn thiết kế nào?

- Phương án: (1) Duyệt bộ bảy đặc tả với: receipt là sổ theo git do xt.py deploy ghi, release-check chỉ đọc sổ; hợp đồng triển khai trung lập công cụ, gói dùng Docker Engine + Compose; bản dev là môi trường dựng lại bằng một lệnh, không phải địa chỉ luôn bật; bộ nghiệm thu khoá bằng digest ở sổ riêng và phải đỏ trước khi viết mã; mở M/L bằng hai khoá trần riêng mặc định S và 1 thuộc HARD_GATED_KEYS, dòng người dùng thử ghi MÁY MÔ PHỎNG; mục MUST lớp B vẫn là việc người; mảnh changelog.d cho CHANGELOG, sổ sách còn lại do phiên điều phối ghi; worker bắt buộc có trần chi phí; admin-plan chỉ đọc; repo sản phẩm là repo riêng hoặc bundle; không đổi schema registry · (2) Chỉ viết ADR ở từng lát (T-3841, T-3850), không viết đặc tả trước · (3) Dùng lại release_signoff: agent và stage_approval: agent cho mọi quy mô, không thêm khoá trần
- Chọn: Duyệt bộ bảy đặc tả với: receipt là sổ theo git do xt.py deploy ghi, release-check chỉ đọc sổ; hợp đồng triển khai trung lập công cụ, gói dùng Docker Engine + Compose; bản dev là môi trường dựng lại bằng một lệnh, không phải địa chỉ luôn bật; bộ nghiệm thu khoá bằng digest ở sổ riêng và phải đỏ trước khi viết mã; mở M/L bằng hai khoá trần riêng mặc định S và 1 thuộc HARD_GATED_KEYS, dòng người dùng thử ghi MÁY MÔ PHỎNG; mục MUST lớp B vẫn là việc người; mảnh changelog.d cho CHANGELOG, sổ sách còn lại do phiên điều phối ghi; worker bắt buộc có trần chi phí; admin-plan chỉ đọc; repo sản phẩm là repo riêng hoặc bundle; không đổi schema registry
- Lý do (tiêu chí chất lượng cuối): (1) đúng/an toàn: scenario Given/When/Then có trước mã để bộ nghiệm thu độc lập bám vào; khoá trần riêng tránh nới ngầm dự án đã bật quyền ở S khi nâng khung (phương án 3 nới ngầm — research 2026-11-08 luận điểm 7); không đọc được không tính đạt; receipt do lệnh ghi và guard chặn ghi tay; lớp B giữ người đúng bảy loại máy không thể; (2) đường lùi: mỗi năng lực một khoá xt.yaml, khoá trống là hành vi cũ; (3) đơn giản: sổ theo git theo tiền lệ STAGE.json và kéo về được theo ADR-0010, không dịch vụ ngoài, không đổi schema registry, mã vẫn trong xt.py; công cụ container chọn theo dữ kiện tra 2026-11-11 (Apache-2.0, có sẵn trên runner ubuntu-latest); phương án 2 để người viết mã tự định nghĩa đạt là gì
- Đường lùi: Đặc tả chưa có mã: sửa hoặc thay bằng phiên bản 2 qua PR; từng lựa chọn đổi được ở task của nó bằng D-NNN mới ghi thay D này
- Ghi chú số: nhánh chính không có D-421 — số đó đã cấp cho bản nháp cùng quyết định này ở một nhánh cục bộ không đẩy (bản trước review); không tái sử dụng. Lựa chọn "worker nhận việc bằng nhánh remote" của bản nháp đã bị D-423 thay.

### D-423 · 2026-11-11T19:40:53+00:00 · Review độc lập bộ đặc tả SPEC-factory-* trước khi công bố trả 6 lỗi chặn, 18 mục nên sửa — sửa thiết kế thế nào?

- Phương án: (1) Sửa đặc tả trước khi mở PR: (1) đơn vị song song là tập task giao cho một worktree, phạm vi là hợp files:, worktree được tick dòng task của mình, sổ do lệnh ghi chỉ phiên điều phối chạy; (2) nhận việc bằng API tạo ref nguyên tử, nhánh quá hạn được tiếp quản bằng đẩy fast-forward; (3) trần worker đọc ở nhánh chính và thuộc HARD_GATED_KEYS, tính theo lát, cửa sổ lỗi lọt là hằng số; (4) chặn phân phối bằng tag do workflow có cổng tạo và ghi nguồn cài, không chặn install.py theo promotion; nâng dự án đích theo mô hình kéo; (5) đã có khoá nghiệm thu thì kiểm theo sổ, ghim lệnh và số ca; (6) production đòi HEAD nằm trong nhánh chính của remote, rollback cùng điều kiện quyền, digest_<env> bắt buộc, current là bản đang phục vụ; khoá trần đọc mới từ remote lấy mức thấp hơn, lệnh hàng bằng chứng phải trùng nhánh chính, không ghi đè dòng 20 của người; không thêm hàng deploy khi dự án chưa khai môi trường · (2) Công bố bản nháp và ghi 6 lỗi chặn thành nợ review, sửa khi cài · (3) Bỏ các phần bị bắt lỗi (worker ngoài phiên, production, mọi quy mô) khỏi đặc tả, chỉ giữ bản dev
- Chọn: Sửa đặc tả trước khi mở PR: (1) đơn vị song song là tập task giao cho một worktree, phạm vi là hợp files:, worktree được tick dòng task của mình, sổ do lệnh ghi chỉ phiên điều phối chạy; (2) nhận việc bằng API tạo ref nguyên tử, nhánh quá hạn được tiếp quản bằng đẩy fast-forward; (3) trần worker đọc ở nhánh chính và thuộc HARD_GATED_KEYS, tính theo lát, cửa sổ lỗi lọt là hằng số; (4) chặn phân phối bằng tag do workflow có cổng tạo và ghi nguồn cài, không chặn install.py theo promotion; nâng dự án đích theo mô hình kéo; (5) đã có khoá nghiệm thu thì kiểm theo sổ, ghim lệnh và số ca; (6) production đòi HEAD nằm trong nhánh chính của remote, rollback cùng điều kiện quyền, digest_<env> bắt buộc, current là bản đang phục vụ; khoá trần đọc mới từ remote lấy mức thấp hơn, lệnh hàng bằng chứng phải trùng nhánh chính, không ghi đè dòng 20 của người; không thêm hàng deploy khi dự án chưa khai môi trường
- Lý do (tiêu chí chất lượng cuối): (1) đúng/an toàn: cả sáu lỗi chặn đều có đường tái hiện và phần lớn là đường để phiên tự nới (trần chi phí và khoá ở cây làm việc, xoá khoá xt.yaml để tắt kiểm, mã chưa merge lên production, rollback không cần quyền) — đúng thứ luật bất đối xứng cấm; sửa ở đặc tả rẻ hơn sửa sau khi có mã và bộ nghiệm thu đã khoá theo đặc tả sai; (2) đường lùi: chưa có mã, đổi chữ là đủ; (3) đơn giản: mô hình kéo bỏ được token ghi chéo repo (ADR-0010), tag làm thuộc tính bền thay cho trạng thái tức thời; phương án 2 đưa lỗ đã biết vào nền của 26 task; phương án 3 bỏ ba phần chủ dự án yêu cầu
- Đường lùi: Sửa đặc tả bằng PR và D-NNN mới; chưa task nào có mã

### D-424 · 2026-11-11T20:21:32+00:00 · Review #505 (bộ đặc tả) trả 3 lỗi chặn — tag phiên bản ai cũng tạo được nên không phải thuộc tính bền; deploy rollback production chạy được lệnh của nhánh chưa merge; tiếp quản nhánh quá hạn không có đồng hồ, không có bước nhận, không giữ trần chi phí — sửa thế nào?

- Phương án: (1) Sửa trong PR: (1) thuộc tính bền của một bản là attestation do workflow phát hành ký, kiểm ở nơi dùng bằng lệnh chỉ đọc release-verify; ruleset tag và luật guard cấm phiên agent tạo tag phiên bản là lớp chặn thêm; (2) rollback ở môi trường khác dev cũng đòi HEAD nằm trong nhánh chính của remote, digest_<env> chạy không có biến đáp án; (3) bỏ tự tiếp quản: nhánh quá hạn chỉ báo, phiên điều phối giao lại bằng lệnh có D-NNN, thời điểm nhận nằm trong tên ref, chi phí cộng dồn đi theo nhánh, có trần số lượt; worktree song song do xt.py tạo và không tick PLAN; ở M/L và giai đoạn 2/3 agent chỉ ký/duyệt ứng viên đã nằm trên nhánh chính; canary bằng số ngày + danh sách thu hồi; các phần còn câu hỏi chặn (F-131, F-133, F-121, F-113, F-142) về Draft, task của chúng quyết trước khi viết mã · (2) Giữ thiết kế tiếp quản tự động và vá từng lỗ (commit nhận việc, nhịp sống, bộ đếm) · (3) Ghi cả ba thành nợ review, merge đặc tả như đang có
- Chọn: Sửa trong PR: (1) thuộc tính bền của một bản là attestation do workflow phát hành ký, kiểm ở nơi dùng bằng lệnh chỉ đọc release-verify; ruleset tag và luật guard cấm phiên agent tạo tag phiên bản là lớp chặn thêm; (2) rollback ở môi trường khác dev cũng đòi HEAD nằm trong nhánh chính của remote, digest_<env> chạy không có biến đáp án; (3) bỏ tự tiếp quản: nhánh quá hạn chỉ báo, phiên điều phối giao lại bằng lệnh có D-NNN, thời điểm nhận nằm trong tên ref, chi phí cộng dồn đi theo nhánh, có trần số lượt; worktree song song do xt.py tạo và không tick PLAN; ở M/L và giai đoạn 2/3 agent chỉ ký/duyệt ứng viên đã nằm trên nhánh chính; canary bằng số ngày + danh sách thu hồi; các phần còn câu hỏi chặn (F-131, F-133, F-121, F-113, F-142) về Draft, task của chúng quyết trước khi viết mã
- Lý do (tiêu chí chất lượng cuối): (1) đúng/an toàn: ba lỗi đều là đường đưa thứ chưa qua cổng tới nơi dùng (tag giả tới mọi dự án đích, lệnh nhánh chưa merge tới production, hai worker cùng tiêu trần); attestation là bằng chứng mà người tạo tag giả không làm ra được, khác với tên tag; một nơi quyết định giao lại thì không còn đua; (2) đường lùi: chưa có mã; phần Draft ghi rõ điều phải thử thật trước khi duyệt; (3) đơn giản: bỏ hẳn cơ chế tiếp quản tự động thay vì thêm ba cơ chế con để vá — hai lượt review liên tiếp đều tìm ra lỗ ở chính phần này nên thiết kế trên giấy chưa đủ tin, cần thử trên git/GitHub thật (phương án 2 đi tiếp trên giấy); phương án 3 đưa lỗ đã biết vào nền của 26 task
- Đường lùi: Sửa đặc tả bằng PR và D-NNN mới; chưa task nào có mã

### D-425 · 2026-11-11T23:57:24+00:00 · install.py gặp thư mục cha là symlink trên đường ghi harness/.github/adapter: từ chối cả lần cài hay bỏ qua file đó?

- Phương án: (1) Bỏ qua file đó (skipped-symlink) kèm cảnh báo, cài tiếp phần còn lại · (2) Từ chối cả lần cài (exit 2)
- Chọn: Bỏ qua file đó (skipped-symlink) kèm cảnh báo, cài tiếp phần còn lại
- Lý do (tiêu chí chất lượng cuối): Cùng quy ước AUD-HAR-010 cho symlink ở đích: đúng và an toàn (không ghi ra ngoài), đường lùi giữ nguyên, người dùng thấy cảnh báo; từ chối cả lần chặn dự án monorepo hợp lệ có .github là symlink
- Đường lùi: Đổi classify_copy trả lỗi thay vì skipped-symlink

### D-426 · 2026-11-12T00:07:26+00:00 · AUD-DATA-011: migration 0005 đã phát hành dựng index thường — sửa tại chỗ, thêm runner không transaction, hay giữ + test chặn migration mới?

- Phương án: (1) Giữ 0005, test buộc migration mới CONCURRENTLY (0005 miễn có dòng sổ), README nêu cách làm; chấp nhận tới 2027-01-21 · (2) Thêm runner kysely chạy migration không transaction (phạm vi lớn, API chưa xác minh) · (3) Sửa 0005 tại chỗ
- Chọn: Giữ 0005, test buộc migration mới CONCURRENTLY (0005 miễn có dòng sổ), README nêu cách làm; chấp nhận tới 2027-01-21
- Lý do (tiêu chí chất lượng cuối): Đúng và an toàn: DB-MIG-003 cấm sửa migration đã áp; runner mới cần xác minh API kysely và có phạm vi riêng; test chặn tái phát ngay, đường lùi giữ nguyên
- Đường lùi: Bỏ MigrationIndexTest và dòng README; mở lại dòng sổ

### D-427 · 2026-11-12T05:49:35+00:00 · AUD-DEP-021 (T-3720): quét lockfile npm của gói web-api-ts bằng công cụ nào trong dep-audit.yml?

- Phương án: (1) pnpm audit --audit-level moderate với pnpm đã ghim 12.16.1 (endpoint npm bulk advisory; không thêm action hay image bên thứ ba) · (2) google/osv-scanner-action v2.7.1 (ghim SHA; action chạy image Docker theo tag, gửi tên gói/phiên bản/hash tới api.osv.dev, cần security-events: write) · (3) Tải binary osv-scanner kèm kiểm SHA256SUMS và slsa-verifier (chuỗi cung ứng mạnh nhưng thêm 2 công cụ phải ghim và bảo trì)
- Chọn: pnpm audit --audit-level moderate với pnpm đã ghim 12.16.1 (endpoint npm bulk advisory; không thêm action hay image bên thứ ba)
- Lý do (tiêu chí chất lượng cuối): (1) đúng/an toàn: pnpm đã là phụ thuộc tin cậy của gói và pack-web-api.yml, tự đo 2026-11-12 trên lockfile thật: pnpm 12.16.1 audit → No known vulnerabilities, exit 0; phương án 2 thêm image chỉ ghim theo tag và gửi dữ liệu ra ngoài, phương án 3 thêm hai công cụ phải tự xác minh checksum; (2) đường lùi: một bước workflow; (3) đơn giản, theo chuẩn: BASE-DEP-004 chỉ đòi quét có nhịp. Ngưỡng moderate: đỏ ở mức vừa trở lên, tránh PR đỏ vì advisory thấp ở phụ thuộc gián tiếp. Chưa đo: hành vi khi lockfile ở định dạng v13 thử nghiệm
- Đường lùi: Xoá job pack-npm-audit khỏi dep-audit.yml và khối npm khỏi dependabot.yml; hoặc đổi sang phương án 2 bằng một PR

### D-428 · 2026-11-12T06:41:12+00:00 · Mốc «Lát 2 — 🟠 mới» đã xong: chạy audit delta ngay hay sau Lát 3 (🔴 guard)?

- Phương án: (1) Chạy audit delta ngay trước khi sang Lát 3 (quét lại 6 nhóm đổi file + 3 nhóm chưa quét) · (2) Sang Lát 3 trước; audit delta một lần sau Lát 3 cùng T-3729 (quét lại TEST/DOC/HAR) và trước release-check
- Chọn: Sang Lát 3 trước; audit delta một lần sau Lát 3 cùng T-3729 (quét lại TEST/DOC/HAR) và trước release-check
- Lý do (tiêu chí chất lượng cuối): (1) đúng/an toàn: mọi diff ngoài tài liệu từ 7ca87a6 (#497…#510, #512) đã qua review độc lập sạch ở head (ADR-0057), nên quét lại ngay trùng việc; Lát 3 là các 🔴 đã biết từ audit 11-11 — hoãn không che lỗi chưa biết trong khoảng này vì review từng PR đã rà delta. (2) đường lùi: audit delta vẫn chạy trước release-check (hàng audit và review_debt chặn GO), nên không bỏ qua, chỉ gộp một lần. (3) tiết kiệm: một lượt audit nhiều nhóm thay vì hai. Điều kiện đảo: nếu Lát 3 phát sinh 🔴 mới ngoài PLAN thì audit delta ngay.
- Đường lùi: Chạy audit delta ngay ở giữa Lát 3 bằng /audit delta; thêm 🔴/🟠 mới vào PLAN-harden-2026-11-11
- Đính chính (2026-11-12, review #512 🟠-1): lời "#512 … đã qua review độc lập sạch ở head" ở trên được viết trước khi #512 có review; review sạch của #512 ghi sau, ở head chứa chính D-428. Phạm vi lập luận: #497…#510 (đã có dấu review sạch trên PR). Chưa kiểm hàng `audit`/`review_debt` của `release-check` có đòi một lượt audit delta đã chạy hay chỉ đếm 🔴/🟠 mở và file đổi sau SHA quét (hàng `review_debt` đang báo 2 file của #512) — kỷ luật chạy audit delta trước release-check là của phiên chính.

### D-429 · 2026-11-12T15:13:01+00:00 · AUD-SEC-645: CR trần ngoài nháy xử lý thế nào ở guard?

- Phương án: (1) Bỏ \r khỏi lex.whitespace của tokenizer · (2) Luật STRICT_BARE: CR trần ngoài nháy → BUDGET (chặn ở mọi chính sách)
- Chọn: Luật STRICT_BARE: CR trần ngoài nháy → BUDGET (chặn ở mọi chính sách)
- Lý do (tiêu chí chất lượng cuối): (1) đúng và an toàn: shlex.split, str.split và regex \s ở các tầng khác vẫn tách từ ở CR nên sửa tokenizer không đóng được mọi tầng; BUDGET ở tập con chuẩn đóng cùng lúc, theo D-415 (không đọc chắc → chặn, không thêm cách đọc mới). Chi phí: dòng lệnh CRLF dán vào có CR trần bị chặn — bash vốn đọc sai các lệnh đó.
- Đường lùi: Xoá luật CR khỏi STRICT_BARE và ca corpus aud645-*, rồi chọn phương án 1 nếu đo được CRLF dán vào gây chặn oan thường xuyên

### D-430 · 2026-11-13T00:49:09+00:00 · Mở rộng tập con guard đọc chắc bằng cách nào để họ lỗi cú pháp shell hội tụ?

- Phương án: (1) Thêm từng cú pháp vào bảng cấm STRICT_* · (2) Ngữ pháp dương: lệnh có luật chỉ qua khi mọi từ thuộc dạng được phép (cổng _ruled_word_why trong _allowlist_why), cú pháp bash mới mặc định ngoài tập con · (3) Parser bash thật (bashlex/tree-sitter)
- Chọn: Ngữ pháp dương: lệnh có luật chỉ qua khi mọi từ thuộc dạng được phép (cổng _ruled_word_why trong _allowlist_why), cú pháp bash mới mặc định ngoài tập con
- Lý do (tiêu chí chất lượng cuối): (1) đúng và an toàn: bảng cấm cho qua mọi cú pháp chưa liệt kê nên 16 🔴 cùng họ vẫn mở sau 12 ngày (ADR-0063 đã hứa 'ngoài tập con → chặn'); ngữ pháp dương làm lệch của bộ đọc nghiêng về chặn. (3) stdlib-only loại phương án 3. Đo trên 18.274 lệnh thật: cổng hẹp chặn thêm 13 lệnh (0,07 %), dưới ngưỡng 0,2 %. Chủ repo đã chọn hướng 'khoá tập con đọc chắc'.
- Đường lùi: Revert từng lát (độc lập nhau); quay về bảng cấm STRICT_* của ADR-0063/0065

### D-431 · 2026-11-13T00:49:23+00:00 · Cổng tập con: mã lý do, độ rộng và ngưỡng dừng

- Phương án: (1) Mã BUDGET deny mọi chính sách, cổng hẹp (P0–P8), lớp giá trị biến không biết chấp nhận có hạn 2027-01-21 theo ADR-0067, ngưỡng dừng 0,2 % lệnh thật mỗi lát · (2) Mã mới tách ask/deny, biến thể chặt cấm mọi từ mở đầu bằng mở rộng (chặn thêm 0,41 %)
- Chọn: Mã BUDGET deny mọi chính sách, cổng hẹp (P0–P8), lớp giá trị biến không biết chấp nhận có hạn 2027-01-21 theo ADR-0067, ngưỡng dừng 0,2 % lệnh thật mỗi lát
- Lý do (tiêu chí chất lượng cuối): (1) an toàn: BUDGET đã thuộc UNSURE_CODES nên chặn ở mọi chính sách, ADR-0018/0019 cấm guard hỏi người nên không tách ask/deny; (4) trải nghiệm: cổng hẹp chặn 0,07 % so với 0,41 % của biến thể chặt, và 2,0 % nếu cấm mọi mở rộng trần; lớp 'giá trị biến không biết' (git reset "$X") cần phạm vi chấp nhận của ADR-0067 hoặc sandbox, không đóng được ở cú pháp. Mỗi lát có ca corpus chặn + ca đối chứng allow, lát nào làm hơn 0,2 % lệnh thật đổi từ cho qua sang chặn thì không merge và mở D mới.
- Đường lùi: Đổi mã BUDGET sang mã khác hoặc nới ngưỡng bằng D mới; revert từng lát

### D-432 · 2026-11-13T00:49:24+00:00 · Hai 🔴 ngoài lớp cú pháp: 691 (ssh-agent) và 648 (formatter chạm dòng ký GO-NO-GO)

- Phương án: (1) 691 bằng đọc lại hậu tố (lệnh lạ có tên có luật trong 3 đối số đầu thì quét hậu tố như một lệnh), không bảng trình bọc; 648 xử lý phía Write/Edit (dòng §5 có ô tên/ngày mà không ở dạng bảng chuẩn thì chặn lúc ghi), ngoài cổng · (2) Bảng trình bọc lệnh mở rộng mãi cho 691; 648 chặn formatter ở Bash
- Chọn: 691 bằng đọc lại hậu tố (lệnh lạ có tên có luật trong 3 đối số đầu thì quét hậu tố như một lệnh), không bảng trình bọc; 648 xử lý phía Write/Edit (dòng §5 có ô tên/ngày mà không ở dạng bảng chuẩn thì chặn lúc ghi), ngoài cổng
- Lý do (tiêu chí chất lượng cuối): (2) giữ đường lùi và (3) đơn giản, test được: bảng trình bọc lại là danh sách cấm phải vá mãi (cùng lỗi cốt lõi); đọc lại hậu tố chỉ thêm chặn, gitleaks git --no-banner vẫn qua. 648 là lỗi ghi file, không phải đọc lệnh Bash nên không thuộc cổng.
- Đường lùi: Bỏ lát 6 và luật Write/Edit của 648; quay về bảng trình bọc hoặc ghi chấp nhận có hạn

### D-433 · 2026-11-13T00:51:31+00:00 · Cắt chỗ nào để docs/autopilot về dưới trần byte khi thêm D-429…D-432?

- Phương án: (1) Dời PLAN-3.14-app.md (đã đóng, 0 task mở, 20 KB) sang docs/archive/autopilot theo ADR-0070 · (2) Nới trần byte của docs/autopilot
- Chọn: Dời PLAN-3.14-app.md (đã đóng, 0 task mở, 20 KB) sang docs/archive/autopilot theo ADR-0070
- Lý do (tiêu chí chất lượng cuối): (1) đúng quy tắc ADR-0043: cắt chỗ khác, không nới trần; PLAN không còn task mở, PROGRESS không nhắc, chỉ SPEC-app, ADR-0038, CHANGELOG-ARCHIVE trỏ tới nên viết lại ba liên kết là đủ; test_plan_waves nhúng cứng nên không phụ thuộc đường dẫn.
- Đường lùi: git mv ngược về docs/autopilot và hoàn lại ba liên kết

### D-434 · 2026-11-13T01:31:08+00:00 · GATE_NAMES có gồm cả tên thụ động/trình thông dịch (python3, echo, cat, ls…) mà _scan_command có nhánh không?

- Phương án: (1) Giữ nguyên: gom mọi tên _scan_command có nhánh vào GATE_NAMES · (2) Tách thêm GATE_PASSIVE (trình thông dịch không phải shell + bảng thụ động) khỏi GATE_NAMES; test buộc mỗi tên rẽ nhánh phải thuộc một trong hai tập
- Chọn: Tách thêm GATE_PASSIVE (trình thông dịch không phải shell + bảng thụ động) khỏi GATE_NAMES; test buộc mỗi tên rẽ nhánh phải thuộc một trong hai tập
- Lý do (tiêu chí chất lượng cuối): (1) đúng và nhất quán: ADR-0076 ghi python3 scripts/xt.py … không qua cổng và D-432 coi echo/grep/cat là bảng thụ động, nên cổng không được kích hoạt ở các tên đó; (4) trải nghiệm: phương án 1 kéo python3/echo vào cổng ở lát 2 và có rủi ro vượt ngưỡng chặn oan 0,2 % của D-431. Test hai tập vẫn bắt tên rẽ nhánh mới bị quên.
- Đường lùi: Gộp GATE_PASSIVE trở lại GATE_NAMES (một dòng) nếu đo thấy lát 2 cần kích hoạt ở tên thụ động

### D-435 · 2026-11-13T02:36:22+00:00 · Trình thông dịch (python3/node/perl/ruby/php) nằm ở GATE_PASSIVE (D-434) nên cổng P2/P3 không kích hoạt: python3 "$X"-c '…' (mở rộng dính vào cờ -c) vẫn lọt sau ADR-0076. Xử lý thế nào?

- Phương án: (1) Kích hoạt cổng P2/P3 cho trình thông dịch (bỏ python3/node/perl/ruby/php khỏi GATE_PASSIVE) · (2) Giữ PASSIVE nhưng thêm luật hẹp: cờ của trình thông dịch có mở rộng/glob → BUDGET (cờ -c/-e/-m/--eval… nguyên văn, mở rộng chỉ ở đối số sau)
- Chọn: Giữ PASSIVE nhưng thêm luật hẹp: cờ của trình thông dịch có mở rộng/glob → BUDGET (cờ -c/-e/-m/--eval… nguyên văn, mở rộng chỉ ở đối số sau)
- Lý do (tiêu chí chất lượng cuối): (1) an toàn và (4) trải nghiệm: bỏ trình thông dịch khỏi PASSIVE kéo mọi lệnh 'python3 scripts/xt.py …', 'python3 -m unittest …' qua cổng (hàng nghìn lệnh lành mỗi phiên) và là rủi ro vượt ngưỡng chặn oan 0,2 % của D-431; luật hẹp chỉ chạm lệnh mà CỜ có mở rộng (hiếm) nên đóng đúng lỗ python3 "$X"-c mà không đổi D-434. Cổng vẫn ngữ pháp dương: mọi từ ở vị trí cờ của trình thông dịch phải nguyên văn.
- Đường lùi: Bỏ luật hẹp, chuyển trình thông dịch về GATE_NAMES nếu đo cho thấy chặn oan thấp

### D-436 · 2026-11-13T02:51:24+00:00 · Cắt chỗ nào để docs/ops về dưới trần byte khi ghi AUD-SEC-724…728 (còn 996 B dưới trần)?

- Phương án: (1) Dời AUDIT-REPORT-2026-11-04-delta.md và AUDIT-REPORT-2026-11-05-delta.md (14,5 KB) sang docs/archive/ops theo ADR-0070 · (2) Dời GO-NO-GO của bản cũ (3.29.0…3.32.0) · (3) Nới trần byte của docs/ops
- Chọn: Dời AUDIT-REPORT-2026-11-04-delta.md và AUDIT-REPORT-2026-11-05-delta.md (14,5 KB) sang docs/archive/ops theo ADR-0070
- Lý do (tiêu chí chất lượng cuối): (1) đúng quy tắc ADR-0043/ADR-0070: cắt chỗ khác, không nới trần; giữ báo cáo đầy đủ gần nhất (2026-11-02-full) và delta gần nhất (2026-11-11); không công cụ nào đọc hai báo cáo theo đường dẫn (grep scripts/, tests/, .github/, .claude/, framework/), PROGRESS không nhắc; chỉ AUDIT-STATUS có hai liên kết, viết lại cùng liên kết trong hai báo cáo, check-links xanh. (2) bị loại: GO-NO-GO 3.30.0…3.31.1 còn chờ người ký (PROGRESS) và guard chặn dời GO-NO-GO*.md bằng Bash.
- Đường lùi: git mv ngược về docs/ops và hoàn lại liên kết

### D-437 · 2026-11-13T07:40:47+00:00 · Lát 2: P2 (không tra GIT_DANGER_LONG) buộc đổi expect của ca từng là đối chứng cho qua (--set-upstream$X, --verbose$X, --soft$X, curl -G -sSd$TOKEN…). Chấp nhận hay thu hẹp P2 bằng bảng cờ nguy hiểm theo lệnh con?

- Phương án: (1) A: đổi expect các ca đó sang BUDGET và ghi D (theo đúng ADR-0076, chặn oan đo được 0,005 %) · (2) B: thu hẹp P2 bằng bảng cờ nguy hiểm theo từng lệnh con (quay lại cách liệt kê mà ADR đã loại; 711 còn lọt dạng mới)
- Chọn: A: đổi expect các ca đó sang BUDGET và ghi D (theo đúng ADR-0076, chặn oan đo được 0,005 %)
- Lý do (tiêu chí chất lượng cuối): (1) đúng và an toàn: bảng cờ theo lệnh con chính là danh sách cấm đã gây 16 🔴 cùng họ (D-430); (4) trải nghiệm: đo trên 19.026 lệnh Bash thật chỉ 1 lệnh (0,005 %, dưới ngưỡng 0,2 % của D-431) đổi từ cho qua sang chặn — một vòng lặp git log -S"$id" có giá trị dính liền cờ ngắn. Cách viết lại có sẵn: tên cờ nguyên văn, mở rộng chỉ ở giá trị sau dấu = hoặc ở đối số kế.
- Đường lùi: Thu hẹp P2 bằng bảng cờ theo lệnh con (phương án B) nếu đo cho thấy chặn oan thường xuyên; khôi phục expect cũ của các ca control

### D-438 · 2026-11-13T07:40:48+00:00 · Lát 2: cổng _ruled_word_why ghi đè câu hỏi BUDGET đã có của luật cũ (gh … $(echo)-d ở strict đổi ask → deny; dấu GIT_DYN_FLAG_MARK không còn lệnh thật sinh ra). Chấp nhận hay cổng nhường khi luật cũ đã hỏi BUDGET?

- Phương án: (1) A: chấp nhận (BUDGET là deny ở mọi chính sách), đổi quyết định thô sang deny và thay ví dụ của dấu · (2) B: cổng nhường khi luật cũ đã hỏi BUDGET (sửa _argv_shell_check)
- Chọn: A: chấp nhận (BUDGET là deny ở mọi chính sách), đổi quyết định thô sang deny và thay ví dụ của dấu
- Lý do (tiêu chí chất lượng cuối): (1) an toàn: D-431 đặt BUDGET deny ở mọi chính sách và ADR-0018/0019 cấm guard hỏi người, nên 'ask' mang mã BUDGET vốn đã thành deny — quyết định CUỐI không đổi; phương án B thêm một nhánh ngoại lệ vào _argv_shell_check (thêm cách đọc mới, ngược D-415). Đây là siết (ask → deny), không phải hạ mã như lỗi review #523.
- Đường lùi: Thêm nhánh nhường BUDGET vào _argv_shell_check và khôi phục 5 dòng AS_MAIN raw ask

### D-439 · 2026-11-13T07:40:49+00:00 · printf ở GATE_PASSIVE dù printf -v ghi biến; pytest/tox/nox ở GATE_NAMES trong khi ADR-0076 ghi pytest không qua cổng. Xếp thế nào?

- Phương án: (1) printf → GATE_NAMES; pytest/tox/nox giữ GATE_NAMES (siết, chặn oan thêm đo được 0 ở cả hai), ADR dòng 56 được D này đính chính · (2) printf giữ PASSIVE; pytest/tox/nox → GATE_PASSIVE theo câu chữ ADR
- Chọn: printf → GATE_NAMES; pytest/tox/nox giữ GATE_NAMES (siết, chặn oan thêm đo được 0 ở cả hai), ADR dòng 56 được D này đính chính
- Lý do (tiêu chí chất lượng cuối): (1) an toàn: đo trên 19.026 lệnh Bash thật cả hai phương án chênh 0 lệnh; khi chi phí bằng nhau chọn bên chặt (printf -v ghi biến như read/let; pytest chạy mã từ conftest/-p). ADR-0076 không sửa (đã Accepted): câu 'pytest không qua cổng' bị D này thay — cổng chỉ chặn dạng cờ/lệnh con có mở rộng nên rất hiếm chạm pytest.
- Đường lùi: Chuyển printf về GATE_PASSIVE hoặc pytest/tox/nox sang GATE_PASSIVE (sửa PASSIVE_PIN và test ghim)

### D-451 · 2026-11-13T11:35:37+00:00 · Xếp hai sửa tài liệu pilot ở đâu?

- Phương án: (1) Tạo ca cho/chặn giả chỉ để gắn ID đã sửa · (2) Xếp hai sửa tài liệu vào nhóm tài liệu/bằng chứng có sẵn, giữ review nguồn sống và kiểm liên kết
- Chọn: Xếp hai sửa tài liệu vào nhóm tài liệu/bằng chứng có sẵn, giữ review nguồn sống và kiểm liên kết
- Lý do (tiêu chí chất lượng cuối): Nhóm cũ giữ nghĩa/ngưỡng, thêm hai ID. Review độc lập nguồn sống: workflow ghim/API environment/metadata; receipt chưa xác minh, không tạo ca giả.
- Đường lùi: Có adapter triển khai thật: thêm ca, gỡ hai ID khỏi scope.
### D-442 · 2026-11-13T10:37:42+00:00 · Khôi phục vòng bị chặn khi đổi PLAN hoặc ngân sách như thế nào?

- Phương án: (1) Từ chối mọi loop init tới khi loop unblock · (2) Giữ nguyên cờ blocked, lý do và thời điểm qua mọi loop init; chỉ loop unblock có lý do mới gỡ chặn
- Chọn: Giữ nguyên cờ blocked, lý do và thời điểm qua mọi loop init; chỉ loop unblock có lý do mới gỡ chặn
- Lý do (tiêu chí chất lượng cuối): Từ chối init gây bế tắc khi ngân sách hết hoặc PLAN mất vì unblock cũng từ chối. Mang cờ giữ nguyên hàng rào và bằng chứng gỡ chặn, đồng thời cho sửa PLAN/ngân sách. Hướng dẫn release dùng lối ra thật của vòng.
- Đường lùi: Hoàn lại bản vá và test trong PR riêng nếu hợp đồng vòng cần đổi.

### D-450 · 2026-11-13T11:35:35+00:00 · Đóng AUD-HAR-378/379 trong corpus khi adapter hiện tại chưa chạy vòng thật?

- Phương án: (1) Chỉ thêm ID hoặc miễn trừ vào scope · (2) Thêm adapter loop_block giới hạn, chạy CLI thật và kiểm trạng thái/hướng dẫn
- Chọn: Thêm adapter loop_block giới hạn, chạy CLI thật và kiểm trạng thái/hướng dẫn
- Lý do (tiêu chí chất lượng cuối): Hành vi block/init/unblock là quyết định tự chủ nên phải có bằng chứng corpus. Hai kịch bản carry/expired, mỗi kịch bản có control phục hồi; mutation bỏ cờ phải false_green, sai lối ra phải mismatch. Không gắn nhãn vào ca không liên quan hay nới yêu cầu phủ.
- Đường lùi: Tách adapter bằng PR riêng khi có nhóm corpus vòng lặp tương đương, giữ các ca và không khai đóng nợ nếu mất coverage.
### D-440 · 2026-11-13T10:26:25+00:00 · Lát 4: cờ exec ngoài -a TÊN (AUD-SEC-659) và {fd}> đứng đầu lệnh (AUD-SEC-657/700) — BUDGET như bảng P0 của ADR-0076 hay đọc lại như bash?

- Phương án: (1) BUDGET mọi lệnh có luật mà exec có cờ ngoài -a TÊN hoặc có {fd}> ở đầu (đúng chữ ADR; phải đổi ca đối chứng d432-ctl-432-exec-al (exec -al bash -c true, #433)) · (2) Đọc lại như bash: cụm cờ exec theo getopt (_wrapper_opt_takes_next, như _exec_login) và {tên} coi như số fd trong _strip_prefixes — dạng nguy hiểm ra cùng mã dạng trơn, dạng lành vẫn qua
- Chọn: Đọc lại như bash: cụm cờ exec theo getopt (_wrapper_opt_takes_next, như _exec_login) và {tên} coi như số fd trong _strip_prefixes — dạng nguy hiểm ra cùng mã dạng trơn, dạng lành vẫn qua
- Lý do (tiêu chí chất lượng cuối): (1) đúng và an toàn: đọc lại cho đúng mã luật cũ của dạng trơn (exec -la x git push --force → RULE_DENY như dạng không cờ; {fd}>o git reset --hard → RULE_DENY) — đóng đúng lỗ 657/659/700 mà KHÔNG làm đổi mã luật; (3) bền/đơn giản: dùng lại cơ chế getopt đã có của _exec_login thay vì liệt kê; (4) trải nghiệm: không đụng ca #433 (exec -al bash -c true) và đo thêm 0 lệnh thật bị chặn nếu chọn BUDGET cho {fd}> nên không cần siết thêm. Ngoại lệ ADR chỉ là lựa chọn cách đóng, không nới luật.
- Đường lùi: Chuyển sang BUDGET đúng chữ ADR (exec cờ lạ, {fd}> đầu lệnh có luật), đổi ca d432-ctl-432-exec-al sang BUDGET và ghi lý do

### D-441 · 2026-11-13T10:27:22+00:00 · docs/autopilot vượt trần byte 318 B sau D-440 và T-3790: cắt chỗ nào?

- Phương án: (1) Dời PLAN-harden-2026-11-05.md (đã đóng, 0 task mở, 3,5 KB) sang docs/archive/autopilot theo ADR-0070 · (2) Nới trần byte của docs/autopilot
- Chọn: Dời PLAN-harden-2026-11-05.md (đã đóng, 0 task mở, 3,5 KB) sang docs/archive/autopilot theo ADR-0070
- Lý do (tiêu chí chất lượng cuối): (1) đúng quy tắc ADR-0043: cắt chỗ khác, không nới trần; PLAN không còn task mở, PROGRESS không nhắc, các chỗ nhắc (ADR-0069, DECISIONS, CHANGELOG, guard.py) chỉ là văn xuôi nên không có liên kết nào hỏng; xt.py vẫn quét docs/archive/autopilot khi cấp số task nên T-NNNN không tái sử dụng.
- Đường lùi: git mv ngược PLAN-harden-2026-11-05.md về docs/autopilot

### D-443 · 2026-11-13T11:11:58+00:00 · Khôi phục CI #530 khi test_fast có nháy lồng ngoài ngữ pháp P0?

- Phương án: (1) Mở ngoại lệ số học có nháy lồng trong guard · (2) Giữ guard; lấy nproc vào biến rồi tính cùng ceil(N/2)
- Chọn: Giữ guard; lấy nproc vào biến rồi tính cùng ceil(N/2)
- Lý do (tiêu chí chất lượng cuối): Hai ngoại lệ parser thử nghiệm đều bị review độc lập tìm ra bypass thật bằng sentinel vô hại. Theo D-415, viết lại lệnh vào tập con đọc chắc; giữ fallback 2, tập test, runner, công thức và ngưỡng. Test so sánh 12 đầu vào số và ca nproc lỗi cho kết quả như cũ; hai payload phải vẫn BUDGET.
- Đường lùi: Hoàn lại cú pháp lệnh khi có parser nháy đủ bằng chứng; không nới guard hay cổng để phục hồi CI.
### D-444 · 2026-11-13T11:12:00+00:00 · P4 xử lý thay lệnh trần có hậu tố và câu hỏi GO_SIGN cũ thế nào?

- Phương án: (1) Ngoại lệ cho những câu hỏi hoặc control từng được phép · (2) Áp đúng P4; bare substitution còn chữ sau ra BUDGET, giữ các deny cũ
- Chọn: Áp đúng P4; bare substitution còn chữ sau ra BUDGET, giữ các deny cũ
- Lý do (tiêu chí chất lượng cuối): D-415: tập con đọc chắc. patch đổi raw ask GO_SIGN → deny BUDGET (default vẫn deny; strict siết ask), không nới ma trận build/harden. Mẫu 505 lượt không đổi quyết định, chưa đại diện lịch sử; bản nháp, AUD-SEC-609 mở.
- Đường lùi: Hoàn lại lát P4 bằng PR riêng nếu phép đo rộng hơn vượt 0,2%; không đổi ngưỡng hay che lỗ còn lại.

### D-447 · 2026-11-13T11:22:00+00:00 · P4 có giữ thay lệnh trần dính tiền tố ở từ cuối khi có thể thành đường gốc?

- Phương án: (1) Giữ phạm vi chỉ hậu tố, để AUD-SEC-609 mở · (2) Chặn cả tiền tố/hậu tố, chỉ giữ thay lệnh trần là nguyên từ cuối
- Chọn: Chặn cả tiền tố/hậu tố, chỉ giữ thay lệnh trần là nguyên từ cuối
- Lý do (tiêu chí chất lượng cuối): Guard-only probe rm -rf /$(echo) được cho qua, còn Bash stub rm chỉ in argv xác nhận đối số cuối thành /. Đây là cùng lỗi thu hẹp argv nên chọn cách chặt theo D-415; dạng có nháy giữ nguyên. Thay thế giới hạn chỉ hậu tố của D-444; cập nhật control dính tiền tố và test viết lại có nháy. Không đổi ngưỡng D-431.
- Đường lùi: Hoàn lại phần mở rộng P4 bằng PR riêng nếu số đo rộng hơn vượt ngưỡng, giữ ca khai thác và ghi rõ residual.
### D-445 · 2026-11-13T11:12:01+00:00 · Ngoặc trong tham số Bash không nháy làm lệch tokenizer, nên chặn ở đâu?

- Phương án: (1) Mở rộng parser để hiểu mọi dạng tham số lồng · (2) Precheck lexical theo ngữ cảnh nháy, ngoài tập con trả BUDGET
- Chọn: Precheck lexical theo ngữ cảnh nháy, ngoài tập con trả BUDGET
- Lý do (tiêu chí chất lượng cuối): D-415 ưu tiên chặn cú pháp chưa đọc chắc. Precheck trước tách argv đóng cả thay lệnh/thay tiến trình trong tham số; literal và dạng có nháy giữ nguyên. Một số lý do RULE_DENY thành BUDGET nhưng ma trận chính sách không nới deny; corpus cũ không đổi quyết định. RecursionError ở lối đọc sớm được tách thành lát kế, không khai đã đóng.
- Đường lùi: Hoàn lại precheck bằng PR riêng khi có parser tương đương được kiểm đối kháng; giữ các ca regression.

### D-452 · 2026-11-13T11:47:36+00:00 · Khởi tạo dự án mới offline nguyên tử và không chạy hook trước commit đầu thế nào?

- Phương án: (1) Bootstrap trực tiếp trong đích, giữ file dở khi hỏng · (2) Dựng ở sibling riêng, commit rồi hook/doctor, công bố bằng rename nguyên tử
- Chọn: Dựng ở sibling riêng, commit rồi hook/doctor, công bố bằng rename nguyên tử
- Lý do (tiêu chí chất lượng cuối): Đích thiếu hoặc rỗng; rename thất bại khi đích có nội dung hay symlink, tránh hai lần chạy ghi đè. Không nhúng đường staging vào file. Init không template, core.hooksPath chỉ repo mới; manifest khai trước đường hook cuối, commit đầu rồi mới copy hook và doctor trước công bố. Lọc GIT_* để không chạm repo khác; danh tính thiếu chỉ ghi tạm cục bộ. Ý tưởng luôn là dữ liệu, không remote/network.
- Đường lùi: Giữ installer cũ nguyên; bỏ nhánh --new bằng PR riêng nếu có lỗi nguyên tử, giữ regression và không tự sửa thư mục đã có dữ liệu.

### D-453 · 2026-11-13T12:04:43+00:00 · Khởi tạo offline có bỏ toàn bộ kiểm tra doctor hay chỉ probe phiên bản từ xa?

- Phương án: (1) Monkeypatch doctor hoặc bỏ các kiểm tra sâu khi bootstrap · (2) Thêm doctor --offline, chỉ bỏ kiểm phiên bản từ xa mang tính gợi ý
- Chọn: Thêm doctor --offline, chỉ bỏ kiểm phiên bản từ xa mang tính gợi ý
- Lý do (tiêu chí chất lượng cuối): F-111 phải tạo dự án không mạng, nhưng vẫn cần mọi kiểm tra cục bộ. Thêm cờ rõ nghĩa và giữ hành vi online mặc định; --new gọi doctor đã cài với --offline. Regression phải chứng minh không gọi probe mạng và vẫn kiểm hook/framework/cổng. Không giả VERSION hay thay kết quả doctor.
- Đường lùi: Bỏ nhánh --offline bằng PR riêng nếu doctor tách kiểm local/remote theo API tương đương; giữ hợp đồng offline của --new.

### D-455 · 2026-11-13T13:01:54+00:00 · Giữ inode của đích rỗng khi người gọi đang đứng trong thư mục đó như thế nào?

- Phương án: (1) Thay cả thư mục bằng rename rồi bắt người gọi cd lại hoặc từ chối dấu chấm · (2) Đích mới dùng staging; đích rỗng có sẵn giữ inode, claim .git độc quyền rồi bootstrap tại chỗ
- Chọn: Đích mới dùng staging; đích rỗng có sẵn giữ inode, claim .git độc quyền rồi bootstrap tại chỗ
- Lý do (tiêu chí chất lượng cuối): Probe shell thật thấy rename cả thư mục làm cwd cũ mất liên kết, dù tên đích có đủ file. Giữ inode cho đích có sẵn; ghi tương đối trong thư mục đã giữ, kiểm danh tính đích trước mỗi pha và không đi theo symlink thay thế. Khi hỏng giữ output dở và dữ liệu đồng thời, không xoá đệ quy đích có sẵn. Đích chưa tồn tại vẫn công bố staging nguyên tử. Chỉ thay nhánh đích rỗng của D-452; không thêm hạn chế dùng dấu chấm.
- Đường lùi: Hoàn lại nhánh tại chỗ khi có cách công bố giữ cwd tương đương; giữ probe shell/race và không xoá dữ liệu để khôi phục.

### D-457 · 2026-11-13T13:19:31+00:00 · Tạo chỗ cho các lát harden và xưởng dưới trần docs/autopilot bằng cách nào?

- Phương án: (1) Dời hai PLAN factory-A và factory-BE đã đóng, không còn trong PROGRESS, vào docs/archive/autopilot theo ADR-0070 · (2) Tăng trần byte docs/autopilot
- Chọn: Dời hai PLAN factory-A và factory-BE đã đóng, không còn trong PROGRESS, vào docs/archive/autopilot theo ADR-0070
- Lý do (tiêu chí chất lượng cuối): Hai PLAN có 13 task đều đóng, không được PROGRESS nhắc là việc sống; dời giữ nguyên lịch sử và số ID, viết lại liên kết. Không đổi trần hoặc dời PLAN đang chạy.
- Đường lùi: git mv ngược và hoàn lại liên kết trong PR riêng.

### D-459 · 2026-11-13T13:21:24+00:00 · P4: cùng thân bash -c chứa $(pwd)/sub bị tokenizer thay bằng $PWD, làm mất chặn khi bọc. Xử lý thế nào?

- Phương án: (1) Kiểm P4 trên đường thân shell literal nguyên văn đang có trước bước thay $(pwd), không thêm parser · (2) Miễn $(pwd) hoặc nới bất biến wrapper của fuzz
- Chọn: Kiểm P4 trên đường thân shell literal nguyên văn đang có trước bước thay $(pwd), không thêm parser
- Lý do (tiêu chí chất lượng cuối): Cùng byte thân lệnh phải giữ kết luận khi bọc bash -c. Miễn trừ hoặc bỏ invariant che một đường mất cú pháp. Dùng đường raw literal sẵn có giữ D415; phải giữ quoted/whole-final control và đo lại đúng source.
- Đường lùi: Revert bản bổ sung trong PR riêng; giữ audit609 mở và ca fuzz đỏ làm bằng chứng.

### D-460 · 2026-11-13T13:24:09+00:00 · F111: publish thư mục mới mà không thay inode thư mục xuất hiện đồng thời như thế nào?

- Phương án: (1) Mkdir đích thiếu với exist_ok=False rồi bootstrap qua cwd giữ inode; giữ output dở nếu lỗi, cùng cơ chế claim .git như đích rỗng đã có · (2) Giữ staging rồi thêm rename-noreplace riêng theo từng hệ điều hành
- Chọn: Mkdir đích thiếu với exist_ok=False rồi bootstrap qua cwd giữ inode; giữ output dở nếu lỗi, cùng cơ chế claim .git như đích rỗng đã có
- Lý do (tiêu chí chất lượng cuối): Path.rename ghi đè thư mục rỗng xuất hiện giữa chừng, làm cwd của người khác mất liên kết. Exclusive mkdir portable trong stdlib nhận một đích duy nhất; giữ inode và dữ liệu khi lỗi quan trọng hơn atomic publish. Chỉ ghi sau khi kiểm đầu vào. Từ chối nếu tiến trình khác tạo đích trước mkdir; không chuyển sang nhánh existing trong race. Thay D452 phần staging cho đích thiếu.
- Đường lùi: Khôi phục staging chỉ khi có primitive no-replace portable và probe giữ inode qua race xanh; giữ regression cạnh tranh.

### D-475 · 2026-11-13T14:49:02+00:00 · T3763 Gate gốc có ba ALLOW process-sub argv trái P4: giữ grammar hay miễn các lệnh cat/echo/source này?

- Phương án: (1) Giữ P4: đúng ba process-sub argv thành BUDGET rõ ràng, giữ đối chứng ALLOW bằng script/input file nguyên văn · (2) Thêm ngoại lệ cho nội dung process-sub được xem là lành
- Chọn: Giữ P4: đúng ba process-sub argv thành BUDGET rõ ràng, giữ đối chứng ALLOW bằng script/input file nguyên văn
- Lý do (tiêu chí chất lượng cuối): Gate riêng đã chạy801test891s, chỉ ba subtest bash x.sh <(cat f), bash <(echo echo-hi), source <(printf...) trái hợp đồng tất cả process-sub argv ngoài tập con (D444/ADR0076). Ngoại lệ theo nội dung lành quay lại bảng cấm. Đổi đúngbaexpect là siết theo spec, không hạ invariant hay phạm vi; hashguard/505sample0delta giữ nguyên. Fuzz đầy đủ đã qua ở lượt riêng.
- Đường lùi: Chỉ mở process-sub qua SPEC/ADR có bộ đọc và bằng chứng tương đương; không trả expect ALLOW khi parser chưa chắc.

### D-478 · 2026-11-13T16:30:30+00:00 · P4 gate-fast toàn repo còn hai ALLOW dùng thay lệnh trần/process-sub argv trái grammar: xử lý thế nào?

- Phương án: (1) Đúng hai input cũ thành BUDGET, thêm quoted/literal rewrites ALLOW ở default và strict; numeric-loop giữ nguyên assertion · (2) Miễn hai dạng lành cụ thể để giữ ALLOW cũ
- Chọn: Đúng hai input cũ thành BUDGET, thêm quoted/literal rewrites ALLOW ở default và strict; numeric-loop giữ nguyên assertion
- Lý do (tiêu chí chất lượng cuối): Full455classsummaries chỉ có hai mâu thuẫn grammar và mộtnumeric-loop chưa rõnguyênnhân. Probe2original+2rewrites default/strict8callsđúngkếtluận; numericquietbaseline75ebd025/candidateec758 đềuallowNONE với8sunchanged, CPU1.68/1.57s, chưađủquykếtlượtđỏdotải. Khôngthêmexemption, khôngnớiSCAN_SECONDS/timeout/invariant. Chỉbổsungfailurediagnostic nếu cầnđểgiữreason/code lầnsau.
- Đường lùi: Mở dạng ngoài grammar chỉ qua ADR có bằngchứng tươngđương; không trả ALLOW hoặc tăngbudget chỉđểcổngxanh.
### D-477 · 2026-11-13T15:59:22+00:00 · Lát T3736/T3737 vượt150dòng khi cần adapter corpus CLI thật: tách hình thức hay giữ một PR nguyên khối?

- Phương án: (1) Một PR cùng lifecyclefix, adapter giới hạn, hồi quy và auditrefs; mỗi phần cần để bằng chứng đúng hành vi · (2) Tách nhiều PR helper/adapter/fix làm mỗi phần dưới150dòng
- Chọn: Một PR cùng lifecyclefix, adapter giới hạn, hồi quy và auditrefs; mỗi phần cần để bằng chứng đúng hành vi
- Lý do (tiêu chí chất lượng cuối): Hai bug cùng hợp đồng blocked và recovery. Đóng HAR378379 đòi ca thật carry/expired/control cùng lúc, không gắnIDvào ca khôngliênquan hoặc miễntrừ scope. Gitfixture phải cáchly routing/config để tests khôngđụngrepo ngoài. Mộtlát rollbackđược, độc lậpreviewvàgate-fast xanh; tách chỉ đểđếm dòng làm review phải ghép nhiều phần bằngchứng.
- Đường lùi: Revert toàn PR hoặc tách adapter ở PR sau khi có nguồn bằngchứng tươngđương, không bỏ coverage hoặc khai đóng nợ khi mất ca.

### D-479 · 2026-11-14T02:39:45+00:00 · PR #513: nâng gói web-api-ts sau khi Biome kiểm YAML và kiểu Node vượt runtime?

- Phương án: (1) Nâng Kysely, Biome và Vitest; giữ @types/node 24.19.2 và chuẩn hoá khoảng trắng trước chú thích trong mẫu xt.yaml · (2) Giữ cả nhóm ở bản cũ và đợi Dependabot tách các nâng cấp
- Chọn: Nâng Kysely, Biome và Vitest; giữ @types/node 24.19.2 và chuẩn hoá khoảng trắng trước chú thích trong mẫu xt.yaml
- Lý do (tiêu chí chất lượng cuối): Kiểu Node bám runtime 24; cách sinh YAML giữ nguyên giá trị, vẫn được formatter kiểm; lint, typecheck, build và 34 test trên PostgreSQL đã chạy
- Đường lùi: Revert PR #513 để trở về lockfile và khoảng trắng mẫu trước nâng cấp

### D-480 · 2026-11-14T03:11:52+00:00 · T-3729: kiểm việc quét lại TEST, DOC, HAR bằng cổng nào?

- Phương án: (1) Kiểm sổ theo schema và đòi đúng ba nhóm có trạng thái đã quét · (2) Dùng audit check --strict cho cả sổ và mọi nợ phát hành
- Chọn: Kiểm sổ theo schema và đòi đúng ba nhóm có trạng thái đã quét
- Lý do (tiêu chí chất lượng cuối): Cổng cũ exit 0 khi cả ba nhóm chưa quét. Cổng theo phạm vi kiểm đúng việc và không buộc đóng nợ ngoài T-3729
- Đường lùi: Revert thay đổi Gate của T-3729, giữ cổng phát hành audit --strict

### D-481 · 2026-11-14T03:31:15+00:00 · Audit DOC: đồng bộ hướng dẫn G7/MVP với quyền opt-in đã triển khai ra sao?

- Phương án: (1) Trỏ README và vòng đời tới ADR-0069/0074, nêu người duyệt mặc định và phạm vi MVP · (2) Chép lại điều kiện chi tiết trong từng tài liệu
- Chọn: Trỏ README và vòng đời tới ADR-0069/0074, nêu người duyệt mặc định và phạm vi MVP
- Lý do (tiêu chí chất lượng cuối): Giữ một nhà cho điều kiện; lời hướng dẫn khớp code đang chạy và không thay đổi điều kiện phê duyệt
- Đường lùi: Revert lát tài liệu để phục hồi cách diễn đạt trước đó

### D-482 · 2026-11-14T03:45:11+00:00 · Giữ trần docs/autopilot khi hợp nhất các PR sau #532 bằng cách nào?

- Phương án: (1) Dời nguyên văn các quyết định cũ đã có trong bản phát hành sang sổ tháng theo D-314 · (2) Dời thêm PLAN đã đóng sang kho theo ADR-0070
- Chọn: Dời nguyên văn các quyết định cũ đã có trong bản phát hành sang sổ tháng theo D-314
- Lý do (tiêu chí chất lượng cuối): Các PR đang sửa PLAN hoặc cần nghiệm thu chúng; sổ tháng được máy đọc, giữ nguyên ID và giảm xung đột trên các mục đang dùng
- Đường lùi: Đưa các mục về đúng thứ tự trong DECISIONS.md và phục hồi mô tả phạm vi sổ tháng

### D-483 · 2026-11-14T04:00:47+00:00 · AUD-TEST-105: xử lý cặp mẫu retry CPU được ghép chéo thế nào?

- Phương án: (1) Dùng cặp nhỏ/lớn từ cùng lần đo lại · (2) Giữ cực trị từ hai lần đo và thêm báo cáo chỉ số riêng
- Chọn: Dùng cặp nhỏ/lớn từ cùng lần đo lại
- Lý do (tiêu chí chất lượng cuối): Nếu cả hai lượt đều vượt ngưỡng, phép kiểm phải đỏ; đối chiếu trong cùng lượt giữ tỷ lệ, sàn, độ dư và một lần retry
- Đường lùi: Revert thay đổi helper và ca đồng hồ giả nếu cần
### D-485 · 2026-11-14T07:23:00+00:00 · Chọn chính sách runtime cho X-Templates khi chuyển Python 3.15?

- Phương án: (1) Chỉ hỗ trợ dòng Python 3.15, ghim 3.15.2 trong repo và CI · (2) Dùng Python 3.15 mặc định, giữ cổng hỗ trợ 3.11 và 3.14
- Chọn: Chỉ hỗ trợ dòng Python 3.15, ghim 3.15.2 trong repo và CI
- Lý do (tiêu chí chất lượng cuối): Người dùng yêu cầu bỏ các dòng cũ. Một dòng Python giữ môi trường phát triển và CI nhất quán. Giữ kiểm thử nhánh main và ngưỡng coverage hiện hành.
- Đường lùi: Revert PR runtime và trả về bản khung trước khi nâng nếu dự án đích chưa chuyển được.

### D-484 · 2026-11-14T04:01:16+00:00 · T-3842: tách việc đưa CLI triển khai vào khung ra sao?

- Phương án: (1) Tách bộ đọc sổ và deploy status khỏi lệnh có hiệu ứng · (2) Đưa cùng lúc bộ đọc, chạy và quay lui
- Chọn: Tách bộ đọc sổ và deploy status khỏi lệnh có hiệu ứng
- Lý do (tiêu chí chất lượng cuối): Bộ đọc sổ có test offline và có thể dùng chung cho release-check và registry. Lát điều khiển cần giữ trạng thái khi thất bại và cổng quyền riêng.
- Đường lùi: Revert lát đọc sổ mà chưa cần thay đổi đích triển khai hay dữ liệu thật

### D-486 · 2026-11-14T08:41:08+00:00 · Cổng merge và thứ tự PR cho khung và dự án đích?

- Phương án: (1) CI xanh, ưu tiên số PR tăng dần · (2) Giữ review bắt buộc theo làn
- Chọn: CI xanh, ưu tiên số PR tăng dần
- Lý do (tiêu chí chất lượng cuối): Chủ dự án yêu cầu áp dụng cho cả dự án đích và không bắt buộc review; giữ check CI và ghim head
- Đường lùi: Đặt merge_review required và khôi phục thứ tự steward theo ADR-0079

### D-488 · 2026-11-14T13:06:45+00:00 · Cổng merge làm gì khi không xác minh được ruleset hoặc nguồn của check bắt buộc?

- Phương án: (1) Giữ hành vi hiện tại và dựa vào ruleset GitHub · (2) Không kết luận merge khi không đọc được ruleset hoặc không xác minh đúng app; giữ CI và ruleset
- Chọn: Không kết luận merge khi không đọc được ruleset hoặc không xác minh đúng app; giữ CI và ruleset
- Lý do (tiêu chí chất lượng cuối): Hai fixture độc lập tái hiện verdict merge sai; GitHub yêu cầu check từ app đã ghim, nên chờ bằng chứng đầy đủ giữ an toàn và đường lùi
- Đường lùi: Revert PR nếu giao diện GitHub không cung cấp đủ nguồn và khôi phục xử lý thủ công trong lúc sửa adapter

### D-489 · 2026-11-14T14:11:59+00:00 · T-3746 xử lý thế nào với GO-NO-GO có sẵn khi chạy formatter toàn repo?

- Phương án: (1) Chỉ hướng dẫn thêm mẫu bỏ qua cho từng formatter · (2) Dùng lại cơ chế giữ nội dung GO-NO-GO của format-file tại điểm vào format
- Chọn: Dùng lại cơ chế giữ nội dung GO-NO-GO của format-file tại điểm vào format
- Lý do (tiêu chí chất lượng cuối): Đo bằng DevTaskTest: formatter thay nội dung GO-NO-GO ở cả exit 0 và 7. Cơ chế dùng chung bảo toàn nội dung và không phụ thuộc stack.
- Đường lùi: Revert lát format và áp dụng quy tắc ignore của từng formatter.

### D-490 · 2026-11-14T14:34:42+00:00 · Duyệt PLAN-harden-2026-11-14-complete cho repo khung?

- Phương án: (1) Đóng audit và xin ký ngay theo kết quả CI gần nhất · (2) Giữ NO-GO, xử lý từng mục đỏ đã xác minh, ghi delta và chỉ tiến tới ký khi cổng G7 đạt
- Chọn: Giữ NO-GO, xử lý từng mục đỏ đã xác minh, ghi delta và chỉ tiến tới ký khi cổng G7 đạt
- Lý do (tiêu chí chất lượng cuối): Blueprint không có MUST mở nhưng sổ strict còn 16 mục đỏ, 47 mục cam và hai nhóm chưa quét. Cần bằng chứng trên đúng cây ứng viên và xác nhận độc lập các lỗi mới.
- Đường lùi: Dừng đợt harden và tiếp tục từ sổ audit hiện tại; giữ nguyên cổng phát hành.
