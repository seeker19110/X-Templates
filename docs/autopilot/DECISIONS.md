# Nhật ký quyết định tự duyệt

> Ghi bởi `xt.py loop decide`. Phiên chính tự duyệt điểm quyết định theo tiêu chí chất lượng cuối (`LOOP-STOP-018`, ADR-0008 của khung). Người xem lại bất cứ lúc nào; đổi ý → quyết định mới ghi "thay D-NNN", không sửa mục cũ.
> Bản tháng trước: [`DECISIONS-2026-10.md`](DECISIONS-2026-10.md) (D-001…D-287), [`DECISIONS-2026-11.md`](DECISIONS-2026-11.md) (D-292…D-360) — máy đọc cả bản tháng (T-3651).

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

### D-363 · 2026-11-05T00:42:29+00:00 · T-3700/T-3701: ca FLOW perf trial gọi xt.py nào — bản sao .xtemplates/scripts/xt.py trong repo đồ chơi (giống dự án đích, mất coverage) hay ROOT/scripts/xt.py (coverage tính được)? Kèm: tên trường sổ jsonl và schema chưa chốt

- Phương án: (1) Gọi ROOT/scripts/xt.py; luật ADR §5 'exec công cụ chấm từ blob gốc' chỉ exec khi byte của file đang chạy KHÁC blob ở base (bằng nhau thì chạy tiếp, không exec) — không có cờ/biến môi trường riêng cho test; T-3701 chốt tên trường perf-trials.jsonl (event, reason), schema 1, setup là chuỗi shell và ghi vào ADR §3; vế held-out so cả gốc của AUD-HAR-231 thêm test đơn vị ở T-3705 · (2) Gọi bản sao trong repo đồ chơi; test_perf_trial phủ 100 % trong tiến trình bằng cách tắt exec qua biến môi trường
- Chọn: Gọi ROOT/scripts/xt.py; luật ADR §5 'exec công cụ chấm từ blob gốc' chỉ exec khi byte của file đang chạy KHÁC blob ở base (bằng nhau thì chạy tiếp, không exec) — không có cờ/biến môi trường riêng cho test; T-3701 chốt tên trường perf-trials.jsonl (event, reason), schema 1, setup là chuỗi shell và ghi vào ADR §3; vế held-out so cả gốc của AUD-HAR-231 thêm test đơn vị ở T-3705
- Lý do (tiêu chí chất lượng cuối): (1) không thêm cửa sau tắt exec (biến môi trường tắt bộ chấm là bề mặt lách); so byte với blob gốc là điều kiện đúng nghĩa: cùng byte thì chính là công cụ gốc; (3) coverage 100 % giữ được qua coverage subprocess sẵn có; (3) tên trường chốt một nơi (ADR §3)
- Đường lùi: Gọi bản sao (phương án 2) nếu so byte gây sai khi dự án đích sửa dòng cuối file (CRLF)

### D-364 · 2026-11-05T01:20:18+00:00 · Sửa #441 lộ thêm hai lỗ có từ trước: (1) ghi qua thư mục mở trên fd — printf x > /dev/fd/3/guard.py 3< .claude/hooks (guard bỏ qua đích dưới /dev/); (2) bash ./link <<'EOF' với link → /dev/stdin (_stdin_shell không lần symlink theo thư mục chạy)

- Phương án: (1) (1) sửa ngay: đích có tiền tố /dev/fd/N/…, /dev/std*/…, /proc/*/fd/N/… coi là thư mục không biết (D-106), áp _where lên phần đuôi (AUD-SEC-521); (2) chấp nhận có hạn 2027-01-21 theo ADR-0067, cùng lớp AUD-SEC-519 (AUD-SEC-522) · (2) Chặn thẳng mọi đích ghi đi qua fd và sửa cả (2) bằng truyền thư mục ứng viên vào _stdin_shell
- Chọn: (1) sửa ngay: đích có tiền tố /dev/fd/N/…, /dev/std*/…, /proc/*/fd/N/… coi là thư mục không biết (D-106), áp _where lên phần đuôi (AUD-SEC-521); (2) chấp nhận có hạn 2027-01-21 theo ADR-0067, cùng lớp AUD-SEC-519 (AUD-SEC-522)
- Lý do (tiêu chí chất lượng cuối): (1) lỗ (1) ghi được hook nên sửa; cách (a) chặt mà gần như không chặn oan (4) — chặn thẳng thô hơn; (2) cần sửa nhiều chỗ gọi, cùng lớp giới hạn đã chấp nhận ở D-362 — (5) không chặn 3.30.0
- Đường lùi: Chặn thẳng mọi đích ghi qua fd nếu (a) lọt biến thể

### D-365 · 2026-11-05T01:46:16+00:00 · T-3701/T-3702 perf trial: duyệt sáu quyết định nhỏ của người viết và chọn thời điểm gỡ ID FLOW khỏi XFAIL

- Phương án: (1) Nhận cả sáu (done= cho ca đã xanh; log đòi HEAD^{tree} = cây giữ/log gần nhất; điểm nóng nhận file có ở HEAD do lần giữ trước thêm; khoá mặc định **/ và từ chối khoá lạ; đếm ba lần qua mọi vòng, base từ SHA máy chủ; setup qua /bin/sh -c) — thư mục tạm của exec blob gốc phải dọn ở T-3703; gỡ ID khỏi XFAIL ở T-3707 cùng lúc sửa Gate T-3700 · (2) Giữ cơ chế done= vĩnh viễn
- Chọn: Nhận cả sáu (done= cho ca đã xanh; log đòi HEAD^{tree} = cây giữ/log gần nhất; điểm nóng nhận file có ở HEAD do lần giữ trước thêm; khoá mặc định **/ và từ chối khoá lạ; đếm ba lần qua mọi vòng, base từ SHA máy chủ; setup qua /bin/sh -c) — thư mục tạm của exec blob gốc phải dọn ở T-3703; gỡ ID khỏi XFAIL ở T-3707 cùng lúc sửa Gate T-3700
- Lý do (tiêu chí chất lượng cuối): (1) năm điểm chặt hơn hoặc trung tính; điểm nóng do lần giữ thêm đã qua máy kiểm; (3) XFAIL không còn ca là rác — gỡ ở task cuối giữ Gate T-3700 đúng nghĩa; (2) rò thư mục tạm có task chủ
- Đường lùi: Giữ done= nếu sửa Gate T-3700 làm loop verify lịch sử đỏ

### D-366 · 2026-11-05T02:10:21+00:00 · Review #442 🔴: 'máy chủ' của D-361 là URL origin cục bộ — agent đổi set-url/config remote.*.url/insteadOf/GIT_CONFIG_*/packed-refs/.git/refs/remotes để tự chọn gốc vòng; 🟠 hạ cấp gốc bằng nhánh từ tổ tiên cũ; 🟠 diff.ignoreSubmodules lách luật HEAD^{tree}; 🟠 HOME từ env (usercustomize); 🟠 os.walk nuốt lỗi quyền; 5 🟢

- Phương án: (1) Hai lớp: (guard) deny mọi đổi URL/pushurl/refspec/insteadOf của remote kể cả -c và GIT_CONFIG_* đi kèm xt.py, và mọi ghi thẳng .git/packed-refs, .git/refs/remotes/** (Bash lẫn Edit/Write); (xt.py) perf trial lọc env git theo allowlist, bỏ cấu hình git toàn cục/hệ thống khi gọi ls-remote (GIT_CONFIG_NOSYSTEM, GIT_CONFIG_GLOBAL=/dev/null), từ chối khi có insteadOf áp lên URL origin, ghi URL origin vào sổ ở start đầu và từ chối khi đổi. Gốc = ĐẦU nhánh mặc định do máy chủ báo (start đòi HEAD chứa đầu nhánh, không còn merge-base tuỳ tổ tiên) — chặn hạ cấp. So HEAD^{tree} bằng SHA rev-parse, mọi diff thêm --ignore-submodules=none --no-ext-diff --no-textconv. HOME = pwd.getpwuid, PYTHONNOUSERSITE=1. os.walk onerror → exit 2; dọn chmod. Sửa cả 5 🟢 (exec giữ gốc dự án qua CLAUDE_PROJECT_DIR; đọc __file__ /dev/fd → không exec sai; mỗi cây một mkdtemp + remote remove origin trong clone; cây đo phải ngoài cây agent; escape mốc PERF-LOG) và khoá mặc định thêm setup.py, requirements*.txt. ADR §1/§4 ghi giới hạn còn lại: cùng uid sửa trực tiếp file trong .git ngoài guard (lớp hai: sandbox, ADR-0067) · (2) Chỉ ghi giới hạn vào ADR, giữ mã
- Chọn: Hai lớp: (guard) deny mọi đổi URL/pushurl/refspec/insteadOf của remote kể cả -c và GIT_CONFIG_* đi kèm xt.py, và mọi ghi thẳng .git/packed-refs, .git/refs/remotes/** (Bash lẫn Edit/Write); (xt.py) perf trial lọc env git theo allowlist, bỏ cấu hình git toàn cục/hệ thống khi gọi ls-remote (GIT_CONFIG_NOSYSTEM, GIT_CONFIG_GLOBAL=/dev/null), từ chối khi có insteadOf áp lên URL origin, ghi URL origin vào sổ ở start đầu và từ chối khi đổi. Gốc = ĐẦU nhánh mặc định do máy chủ báo (start đòi HEAD chứa đầu nhánh, không còn merge-base tuỳ tổ tiên) — chặn hạ cấp. So HEAD^{tree} bằng SHA rev-parse, mọi diff thêm --ignore-submodules=none --no-ext-diff --no-textconv. HOME = pwd.getpwuid, PYTHONNOUSERSITE=1. os.walk onerror → exit 2; dọn chmod. Sửa cả 5 🟢 (exec giữ gốc dự án qua CLAUDE_PROJECT_DIR; đọc __file__ /dev/fd → không exec sai; mỗi cây một mkdtemp + remote remove origin trong clone; cây đo phải ngoài cây agent; escape mốc PERF-LOG) và khoá mặc định thêm setup.py, requirements*.txt. ADR §1/§4 ghi giới hạn còn lại: cùng uid sửa trực tiếp file trong .git ngoài guard (lớp hai: sandbox, ADR-0067)
- Lý do (tiêu chí chất lượng cuối): (1) phương án 1 đóng mọi đường đã tái hiện bằng hai lớp độc lập; đòi HEAD chứa đầu nhánh chặt hơn merge-base và bỏ lựa chọn tổ tiên của agent; phần còn lại là giới hạn cùng uid đã được ADR-0067 chấp nhận — ghi rõ, sửa tiền đề D-361; (3) mỗi điểm có test tái hiện
- Đường lùi: Trở về merge-base nếu đòi HEAD chứa đầu nhánh làm vòng tối ưu phải gộp main quá thường

### D-367 · 2026-11-05T04:10:16+00:00 · Chủ repo 2026-11-05: tận dụng tối đa nhân CPU khi chạy test, áp cho cả dự án đích — dev-task tự dò hiện chạy pytest/unittest một tiến trình

- Phương án: (1) dev-task tự dò: pytest → 'pytest -q -n auto' khi import được xdist (không thì 'pytest -q' kèm gợi ý cài pytest-xdist), unittest → mỗi module test một tiến trình qua xargs -P; số tiến trình = XT_JOBS nếu đặt, mặc định nproc; Go/Rust/Node giữ (đã song song mặc định); thêm mục SHOULD ở quality-gates.md (test chạy song song theo số nhân + test độc lập thứ tự) và CHANGELOG 'Dự án đích'; dự án đích đã khai lệnh test trong xt.yaml: không đè, PR nâng bản đề xuất cờ song song phù hợp · (2) Chỉ ghi hướng dẫn trong tài liệu, không đổi dev-task
- Chọn: dev-task tự dò: pytest → 'pytest -q -n auto' khi import được xdist (không thì 'pytest -q' kèm gợi ý cài pytest-xdist), unittest → mỗi module test một tiến trình qua xargs -P; số tiến trình = XT_JOBS nếu đặt, mặc định nproc; Go/Rust/Node giữ (đã song song mặc định); thêm mục SHOULD ở quality-gates.md (test chạy song song theo số nhân + test độc lập thứ tự) và CHANGELOG 'Dự án đích'; dự án đích đã khai lệnh test trong xt.yaml: không đè, PR nâng bản đề xuất cờ song song phù hợp
- Lý do (tiêu chí chất lượng cuối): (4) dự án dùng lệnh tự dò được lợi ngay; (2) chỉ đổi lệnh tự dò, lệnh khai báo trong xt.yaml giữ nguyên, XT_JOBS=1 trả về tuần tự; (1) test phụ thuộc thứ tự lộ ra là lỗi thật (frontend-testing.md đã nêu) — mục SHOULD đòi test độc lập
- Đường lùi: XT_JOBS=1 hoặc khai lệnh test tường minh trong xt.yaml

### D-368 · 2026-11-05T05:06:07+00:00 · Review #443 (perf trial finish): 🔴 status --check không ràng HEAD (commit lạ sau lần giữ vẫn exit 0); 🟠 candidate_files thành pathspec glob cuốn sổ .autopilot vào stash; 🟠 cache đĩa (HOME/XDG/TMPDIR một lần mỗi cây, kênh scratch) tính thành tăng tốc; 🟠 candidate tự mang interpreter (.venv/bin, node_modules/.bin đầu PATH không khoá); 6 🟢

- Phương án: (1) Sửa hết trong #443: check đòi cây sạch ngoài .autopilot và HEAD^{tree} == cây neo (sai → exit 1 'commit lạ sau lần giữ'); mọi pathspec qua --pathspec-from-file=- --pathspec-file-nul + GIT_LITERAL_PATHSPECS=1 (sửa luôn Argument list too long); HOME/XDG_*/TMPDIR tạo mới MỖI mẫu, file khớp scratch xoá giữa các mẫu wall; khoá mặc định thêm **/.venv/**, **/node_modules/**, .gitignore và thu hồi khi file candidate nằm dưới thư mục PATH của cây; 🟢: PERF_SUSPECT_RE thêm atexit/sys.stdout/builtins (so toàn stdout với gốc để T-3705), SIGTERM dọn cây + giết nhóm tiến trình + pha về started, README mô tả finish/status --check và sửa 'merge-base' theo D-366, test thứ tự xen kẽ, thông báo --no-apply trỏ T-3706 · (2) Chỉ sửa 🔴, ghi nợ 🟠/🟢
- Chọn: Sửa hết trong #443: check đòi cây sạch ngoài .autopilot và HEAD^{tree} == cây neo (sai → exit 1 'commit lạ sau lần giữ'); mọi pathspec qua --pathspec-from-file=- --pathspec-file-nul + GIT_LITERAL_PATHSPECS=1 (sửa luôn Argument list too long); HOME/XDG_*/TMPDIR tạo mới MỖI mẫu, file khớp scratch xoá giữa các mẫu wall; khoá mặc định thêm **/.venv/**, **/node_modules/**, .gitignore và thu hồi khi file candidate nằm dưới thư mục PATH của cây; 🟢: PERF_SUSPECT_RE thêm atexit/sys.stdout/builtins (so toàn stdout với gốc để T-3705), SIGTERM dọn cây + giết nhóm tiến trình + pha về started, README mô tả finish/status --check và sửa 'merge-base' theo D-366, test thứ tự xen kẽ, thông báo --no-apply trỏ T-3706
- Lý do (tiêu chí chất lượng cuối): (1) ba 🟠 là đường giữ oan/hỏng sổ đã tái hiện — lệnh này sắp thành Gate thật ở T-3707 cùng bản 3.30.0, nợ sẽ chặn release-check anyway; (3) mỗi điểm có ca tái hiện chuyển thành test; (5) sửa một lần rẻ hơn ghi nợ rồi PR riêng
- Đường lùi: Tách 🟢 sang PR sau nếu PR quá lớn để review

### D-369 · 2026-11-05T05:08:03+00:00 · Review #444 (T-3708): bộ chia unittest theo module tự viết gây xanh giả (lớp định nghĩa ở module khác bị bỏ), đỏ giả (setUpClass/setUpModule skip → zero_tests_red exit 5; load_tests/doctest, FunctionTestCase, stdout lúc import lẫn vào danh sách); pytest -n ép cả khi cấu hình tắt xdist; BASE-GATE-020 chép QA-STRAT-007; CI đỏ BASE-CFG-003 (XT_JOBS thiếu README)

- Phương án: (1) Unittest trở về discover tuần tự như cũ (bỏ bộ chia); chỉ pytest + xdist song song: python3 -m pytest -q -n <JOBS>, dò bằng importlib.util.find_spec('xdist'), bỏ -n khi PYTEST_DISABLE_PLUGIN_AUTOLOAD đặt hoặc cấu hình pytest (pytest.ini/pyproject/setup.cfg/tox.ini) có 'no:xdist'; XT_JOBS có trần 4×nproc; README thêm XT_JOBS; BASE-GATE-020 chỉ giữ ý song song, trỏ QA-STRAT-007 cho độc lập thứ tự, sửa '→ Kiểm'; CHANGELOG ghi cwd vào sys.path; sửa hàm phụ tests_dir bị gom thành test · (2) Sửa bộ chia unittest (TestLoader ghi module, gom output, dò không-test toàn cục)
- Chọn: Unittest trở về discover tuần tự như cũ (bỏ bộ chia); chỉ pytest + xdist song song: python3 -m pytest -q -n <JOBS>, dò bằng importlib.util.find_spec('xdist'), bỏ -n khi PYTEST_DISABLE_PLUGIN_AUTOLOAD đặt hoặc cấu hình pytest (pytest.ini/pyproject/setup.cfg/tox.ini) có 'no:xdist'; XT_JOBS có trần 4×nproc; README thêm XT_JOBS; BASE-GATE-020 chỉ giữ ý song song, trỏ QA-STRAT-007 cho độc lập thứ tự, sửa '→ Kiểm'; CHANGELOG ghi cwd vào sys.path; sửa hàm phụ tests_dir bị gom thành test
- Lý do (tiêu chí chất lượng cuối): (1) bộ chia tự viết sai ở 7 dạng hợp lệ của unittest — xanh giả là lỗi nặng nhất của một cổng; discover tuần tự đúng sẵn; (3) pytest-xdist là công cụ chuẩn, đã kiểm; (4) dự án Python muốn song song dùng pytest-xdist (BASE-GATE-020 nói cách); (5) tốc độ chỉ phá hoà
- Đường lùi: Mở task riêng cho bộ chia unittest có TestLoader ghi module nếu dự án đích unittest-thuần cần tốc độ

### D-370 · 2026-11-05T07:03:50+00:00 · Review #445 (perf trial T-3705…T-3707): 🔴 Gate mẫu <(git cat-file …) xanh khi không đọc được công cụ (pipefail không áp cho process substitution); 🔴 SIGTERM sau đóng băng đưa pha về started không tốn lượt → rút lại hạt giống held-out vô hạn; 🟠 held-out chỉ đòi improved còn target chỉ xét chỉ số chính; 🟠 chưa so đầu ra chỉ số chính với gốc (atexit print); 🟠 chết giữa dòng decide và state decided → --resume ghi decide trùng; 🟠 --no-apply kept rồi abort làm vòng kẹt

- Phương án: (1) Sửa hết trong #445: Gate mẫu fail-closed '<(git cat-file blob refs/remotes/origin/HEAD:… || echo raise SystemExit\(2\))' + test qua run_gate_shell khi thiếu origin/HEAD và sai đường; ngắt sau đóng băng tiêu lần đo lại duy nhất (chung bộ đếm resumes), ngắt/chết lần hai → incomplete, sửa ADR §9; target đòi cả held-out gộp đạt; chỉ số chính gom đầu ra và so với gốc như held-out (khác → inequivalent); finish/--resume kiểm dòng decide đã có trước khi ghi; abort sau --no-apply kept ghi dòng aborted và thu hồi nhất quán (không kẹt); 🟢 lý do kept không nhắc held-out khi không khai, lệnh stash in ra theo pathspec nghĩa đen · (2) Chỉ sửa hai 🔴, ghi nợ 🟠
- Chọn: Sửa hết trong #445: Gate mẫu fail-closed '<(git cat-file blob refs/remotes/origin/HEAD:… || echo raise SystemExit\(2\))' + test qua run_gate_shell khi thiếu origin/HEAD và sai đường; ngắt sau đóng băng tiêu lần đo lại duy nhất (chung bộ đếm resumes), ngắt/chết lần hai → incomplete, sửa ADR §9; target đòi cả held-out gộp đạt; chỉ số chính gom đầu ra và so với gốc như held-out (khác → inequivalent); finish/--resume kiểm dòng decide đã có trước khi ghi; abort sau --no-apply kept ghi dòng aborted và thu hồi nhất quán (không kẹt); 🟢 lý do kept không nhắc held-out khi không khai, lệnh stash in ra theo pathspec nghĩa đen
- Lý do (tiêu chí chất lượng cuối): (1) bốn 🟠 là đường giữ oan/kẹt đã tái hiện trên chính Gate sắp phát hành ở 3.30.0 — nợ sẽ chặn release-check; (3) mỗi điểm có kịch bản tái hiện chuyển thành test; ADR §9 đã hứa 'đo lại tới khi may không làm được quá một lần'
- Đường lùi: Tách 🟠 sang PR sau nếu PR quá lớn để review

### D-371 · 2026-11-05T08:07:48+00:00 · Audit delta T-3557 (#435–#445): 5 🟠 — F1 vòng /optimize không tới done (commit sổ sách làm status --check đỏ, merge mở vòng mới), F2 start từ chối khi PLAN-opt/D-NNN commit trên nhánh, F3 module giả (unittest.py/pytest.py) ở gốc lừa equiv, F4 Gate dự phòng perf-gate.sh bị guard chặn (đường lùi khai ở ADR-0071/D-356/CHANGELOG không dùng được), F5 trial_verdict không có test bắt đảo luật giữ; ~20 🟢

- Phương án: (1) Sửa hết 🟠 + 🟢 rẻ trong hai PR song song trước khi cắt 3.30.0: (A, xt.py perf trial) so cây neo ở start/log/status --check bỏ qua đường sổ sách docs/autopilot/**, PROGRESS.md, đường PERF-LOG (cấu hình không được trỏ lệnh đo/khoá vào các đường này — kiểm ở start), check nhận lần giữ của vòng trước khi cây neo == HEAD^{tree} trừ sổ sách; file mới của candidate trùng tên mô-đun nhập được ở cây gốc (unittest, pytest, …) → tampered, khoá mặc định thêm cấu hình runner (.pytest.ini, jest/vitest config, .mocharc*); test đơn vị trial_verdict + GIT_CONFIG cô lập; 🟢 interrupt ghim candidate_fp, log dùng trial_live, ⚠ khi ls-remote rơi về ref cục bộ, tree_fingerprint --ignore-submodules=none; đường lùi = gỡ skill khỏi perf trial, dùng perf compare/guard tay (bỏ lời hứa perf-gate.sh qua loop); đồng bộ ADR/README/skill/optimization-loop/CHANGELOG. (B, phần còn lại) harness-files.md theo #442, DEPENDENCIES.md thêm Gitleaks CLI, GlobCommandNameTest dùng thời gian CPU, dev-task coi pytest.py/conftest gốc là cấu hình cổng, PLAN-upgrade tick T-3670/T-3671; 🟢 nghi ngờ chưa tái hiện ghi sổ mở · (2) Cắt 3.30.0 ngay, chấp nhận có hạn các 🟠
- Chọn: Sửa hết 🟠 + 🟢 rẻ trong hai PR song song trước khi cắt 3.30.0: (A, xt.py perf trial) so cây neo ở start/log/status --check bỏ qua đường sổ sách docs/autopilot/**, PROGRESS.md, đường PERF-LOG (cấu hình không được trỏ lệnh đo/khoá vào các đường này — kiểm ở start), check nhận lần giữ của vòng trước khi cây neo == HEAD^{tree} trừ sổ sách; file mới của candidate trùng tên mô-đun nhập được ở cây gốc (unittest, pytest, …) → tampered, khoá mặc định thêm cấu hình runner (.pytest.ini, jest/vitest config, .mocharc*); test đơn vị trial_verdict + GIT_CONFIG cô lập; 🟢 interrupt ghim candidate_fp, log dùng trial_live, ⚠ khi ls-remote rơi về ref cục bộ, tree_fingerprint --ignore-submodules=none; đường lùi = gỡ skill khỏi perf trial, dùng perf compare/guard tay (bỏ lời hứa perf-gate.sh qua loop); đồng bộ ADR/README/skill/optimization-loop/CHANGELOG. (B, phần còn lại) harness-files.md theo #442, DEPENDENCIES.md thêm Gitleaks CLI, GlobCommandNameTest dùng thời gian CPU, dev-task coi pytest.py/conftest gốc là cấu hình cổng, PLAN-upgrade tick T-3670/T-3671; 🟢 nghi ngờ chưa tái hiện ghi sổ mở
- Lý do (tiêu chí chất lượng cuối): (1) F1/F2 làm tính năng chính của bản (/optimize qua perf trial) không dùng được theo đúng tài liệu — phát hành như vậy là khai xong sai; F3/F5 là đường giữ oan/test không bắt; (2) miễn sổ sách chỉ cho đường không thuộc lệnh đo/khoá, kiểm ở start; (5) hai PR song song theo vùng file
- Đường lùi: Bỏ miễn sổ sách, đòi PLAN-opt + D-NNN vào main trước start (tài liệu hoá F2) nếu miễn bị lách

### D-372 · 2026-11-05T09:06:50+00:00 · Review #447: miễn sổ sách của D-371 (trọn thư mục docs/autopilot) bị lách — symlink từ cây mã vào docs/autopilot/fast.py, sửa file đó sau lần giữ, Gate xanh cho mã chưa đo (hồi quy so main); 🟠 F3 bỏ sót gói namespace; 🟠 Gate nhận lần giữ vòng trước khi main đã đổi mã

- Phương án: (1) Thu hẹp miễn về đúng file sổ sách thường: docs/autopilot/PLAN*.md, DECISIONS*.md, PERF-LOG (đường cấu hình), PROGRESS.md — file thường, không symlink; cây candidate/HEAD có symlink trỏ vào đường sổ sách → tampered; candidate (diff start_head..candidate) nhắc chuỗi đường sổ sách (docs/autopilot, PROGRESS.md) ngoài chính các file sổ sách → tampered; F3 coi gói namespace là nhập được; check chỉ nhận lần giữ vòng trước khi cây gốc vòng mới == cây gốc vòng trước trừ sổ sách hoặc == HEAD^{tree} (squash-merge); ghi rủi ro còn lại (đường dựng lúc chạy, cùng uid) vào ADR §2 và optimization-loop.md · (2) Bỏ hẳn miễn sổ sách (đường lùi D-371): F1/F2 quay lại, /optimize không tới done
- Chọn: Thu hẹp miễn về đúng file sổ sách thường: docs/autopilot/PLAN*.md, DECISIONS*.md, PERF-LOG (đường cấu hình), PROGRESS.md — file thường, không symlink; cây candidate/HEAD có symlink trỏ vào đường sổ sách → tampered; candidate (diff start_head..candidate) nhắc chuỗi đường sổ sách (docs/autopilot, PROGRESS.md) ngoài chính các file sổ sách → tampered; F3 coi gói namespace là nhập được; check chỉ nhận lần giữ vòng trước khi cây gốc vòng mới == cây gốc vòng trước trừ sổ sách hoặc == HEAD^{tree} (squash-merge); ghi rủi ro còn lại (đường dựng lúc chạy, cùng uid) vào ADR §2 và optimization-loop.md
- Lý do (tiêu chí chất lượng cuối): (1) phương án 1 đóng cả R1, R1b (symlink → tampered; nhắc đường → tampered) và giữ được F1/F2; phần còn lại là đường dựng lúc chạy cùng lớp giới hạn đã chấp nhận (ADR-0067); (4) phương án 2 làm tính năng chính không dùng được theo tài liệu; thay D-371 ở phần phạm vi miễn
- Đường lùi: Bỏ hẳn miễn (đường lùi D-371) nếu review sau lại lách được

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
