# Nhật ký quyết định tự duyệt

> Ghi bởi `xt.py loop decide`. Phiên chính tự duyệt điểm quyết định theo tiêu chí chất lượng cuối (`LOOP-STOP-018`, ADR-0008 của khung). Người xem lại bất cứ lúc nào; đổi ý → quyết định mới ghi "thay D-NNN", không sửa mục cũ.
> Bản tháng trước: [`DECISIONS-2026-10.md`](DECISIONS-2026-10.md) (D-001…D-287), [`DECISIONS-2026-11.md`](DECISIONS-2026-11.md) (D-292…D-417) — máy đọc cả bản tháng (T-3651).

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

### D-491 · 2026-11-14T14:58:25+00:00 · AUD-CI-033 mã hoá liên kết Unicode ở đâu?

- Phương án: (1) Sửa từng liên kết Markdown khi lịch phát hiện lỗi · (2) Mã hoá path và query tại điểm gửi HTTP, giữ liên kết nguyên văn trong báo cáo
- Chọn: Mã hoá path và query tại điểm gửi HTTP, giữ liên kết nguyên văn trong báo cáo
- Lý do (tiêu chí chất lượng cuối): Hai kiểm độc lập xác nhận Unicode thô làm dừng cả báo cáo. Điểm gửi dùng chung xử lý cả URL hiện tại và URL mới, không mã hoá lại %xx.
- Đường lùi: Revert PR kiểm liên kết và mã hoá thủ công URL nguồn trong lúc điều tra.

### D-492 · 2026-11-14T15:33:02+00:00 · T-3867: guard làm gì khi bộ quét Bash ném RecursionError?

- Phương án: (1) Giữ xử lý lỗi chung và báo lỗi từ runner · (2) Trả deny BUDGET ở ranh giới quyết định Bash, giữ nguyên giải phóng context
- Chọn: Trả deny BUDGET ở ranh giới quyết định Bash, giữ nguyên giải phóng context
- Lý do (tiêu chí chất lượng cuối): Unit mock vô hại xác nhận RecursionError thoát ranh giới quyết định; deny BUDGET giữ chính sách khi không đủ khả năng quét.
- Đường lùi: Revert PR riêng và ghi T-3867 mở trong sổ.

### D-493 · 2026-11-15T01:41:32+00:00 · AUD-SEC-648: xử lý hàng ký mà formatter có thể chuẩn hóa thế nào?

- Phương án: (1) Chỉ bảo toàn trước/sau ở dev-task.sh · (2) Giữ bảo toàn formatter và nhận dạng hàng ký tiềm năng ở biên Write/MCP
- Chọn: Giữ bảo toàn formatter và nhận dạng hàng ký tiềm năng ở biên Write/MCP
- Lý do (tiêu chí chất lượng cuối): Hai lớp bảo vệ bổ sung cho nhau. Guard phát hiện thêm nội dung tiềm năng, G7 giữ đúng tiêu chí chữ ký chuẩn và quy trình ký của người.
- Đường lùi: Revert lát guard, giữ cơ chế bảo toàn của dev-task.sh.

### D-494 · 2026-11-16T16:05:46+00:00 · Pha harden: rà độc lập và audit đặt ở đâu để vòng chạy tới khi xong mà không ngừng giữa chừng?

- Phương án: (1) Giữ như cũ: audit và trả nợ review ở đầu /complete; phiên chính được gọi reviewer khi thấy rủi ro ở từng PR · (2) Vét việc trước, rà một lần ở cổng ký: trong vòng harden chỉ Gate máy + CI (reviewer chỉ khi pr next trả review); hết task mới audit delta + rà gom diff tích luỹ; phát hiện thành task, lặp tới khi release-check GO · (3) Bỏ rà độc lập, chỉ còn CI và release-check
- Chọn: Vét việc trước, rà một lần ở cổng ký: trong vòng harden chỉ Gate máy + CI (reviewer chỉ khi pr next trả review); hết task mới audit delta + rà gom diff tích luỹ; phát hiện thành task, lặp tới khi release-check GO
- Lý do (tiêu chí chất lượng cuối): Chủ dự án yêu cầu 2026-11-16 (lặp tới khi xong, không reviewer-alt tới cổng ký, trả hết nợ mới ký). Đo ở phiên 2026-11-16: 2 PR guard rà riêng sinh 5 mục đỏ mới và phiên ngừng lượt nhiều lần để chờ CI/reviewer (không có vòng sống giữ phiên); rà gom trên diff tích luỹ tốn ít lượt hơn và main chưa phát hành nên lỗi lọt giữa pha không tới dự án đích. Phương án 3 bỏ lớp rà trước chữ ký — kém an toàn.
- Đường lùi: Revert ADR-0080 và hai skill; đặt merge_review: required để có lại review từng PR.

### D-495 · 2026-11-16T16:25:06+00:00 · Duyệt PLAN-harden-2026-11-16 đợt 1 (14 mục 🔴 của guard, 9 lát)?

- Phương án: (1) Đợt 1 chỉ 🔴, gom theo gốc lỗi, mỗi lát một PR; 🟠 và nợ 🟢 ở đợt 2–3 (ADR-0080) · (2) Một PLAN 150 task theo next-step
- Chọn: Đợt 1 chỉ 🔴, gom theo gốc lỗi, mỗi lát một PR; 🟠 và nợ 🟢 ở đợt 2–3 (ADR-0080)
- Lý do (tiêu chí chất lượng cuối): Theo ADR-0080/D-494: vét việc theo mức rủi ro; PLAN 150 task quá dài để mỗi task có Gate máy riêng; gom theo gốc lỗi để một test hồi quy phủ cả họ. Hướng D-415 (không đọc chắc → BUDGET) giữ bản sửa nhỏ và đúng chiều chặt.
- Đường lùi: Bỏ PLAN này, lập lại theo next-step.

### D-496 · 2026-11-16T20:41:59+00:00 · Duyệt PLAN-harden-2026-11-17 đợt 2 (42 mục 🟠, 8 lát theo gốc lỗi)?

- Phương án: (1) Đợt 2 toàn bộ 🟠 gom 8 lát theo gốc lỗi, guard trước (rủi ro cao), sổ/SPEC sau; mỗi lát một PR · (2) Chỉ làm 🟠 bảo mật guard, để HAR/SPEC sang đợt 3
- Chọn: Đợt 2 toàn bộ 🟠 gom 8 lát theo gốc lỗi, guard trước (rủi ro cao), sổ/SPEC sau; mỗi lát một PR
- Lý do (tiêu chí chất lượng cuối): ADR-0080: vét hết việc trước cổng ký; trả hết nợ mới ký GO (yêu cầu chủ dự án 2026-11-16). Gom theo gốc lỗi để một test hồi quy phủ cả họ; guard trước vì là hàng rào an toàn; mục SPEC Draft đóng bằng quyết định ghi D-NNN hoặc chấp nhận có hạn.
- Đường lùi: Bỏ PLAN đợt 2, lập lại từ sổ.

### D-497 · 2026-11-17T00:44:47+00:00 · AUD-HAR-388/391/392 (đặc tả xưởng F-131/F-121/F-113 còn Draft, chưa có mã) đóng thế nào trong đợt harden?

- Phương án: (1) Chấp nhận có hạn: tính năng chưa có mã nên bản phát hành không mang rủi ro; câu hỏi chặn đã ghi ở §10 của SPEC và gắn T-3850/T-3848/T-3862, không bật trước khi D-NNN đầu task trả lời · (2) Viết luôn thiết kế trả lời câu hỏi chặn · (3) Để mở, chặn GO
- Chọn: Chấp nhận có hạn: tính năng chưa có mã nên bản phát hành không mang rủi ro; câu hỏi chặn đã ghi ở §10 của SPEC và gắn T-3850/T-3848/T-3862, không bật trước khi D-NNN đầu task trả lời
- Lý do (tiêu chí chất lượng cuối): Đúng và an toàn: không có hành vi nào để lỗi trong bản; trả lời câu hỏi chặn cần thử trên git/GitHub thật (T-3850) nên viết trước là đoán. Giữ đường lùi: Draft + [chặn] ở SPEC ngăn triển khai sớm. Phương án 3 khoá phát hành vì việc của tính năng tương lai.
- Đường lùi: Đổi ba hàng về mở.

### D-498 · 2026-11-17T02:34:43+00:00 · AUD-HAR-385 (_release_promotion không có đường miễn cho hàng N/A BLOCKER) xử lý thế nào trong đợt harden?

- Phương án: (1) Chấp nhận có hạn: hành vi hiện tại fail-closed (pending_human, người vẫn phát hành được), lối miễn cần chọn nơi ghi lý do được guard bảo vệ — làm cùng T-3858 (SPEC-factory-scale F-144) · (2) Thêm lối miễn ngay: lý do ghi trong bảng ký §5 · (3) Thêm lối miễn ngay: mục riêng đưa vào neo D-392
- Chọn: Chấp nhận có hạn: hành vi hiện tại fail-closed (pending_human, người vẫn phát hành được), lối miễn cần chọn nơi ghi lý do được guard bảo vệ — làm cùng T-3858 (SPEC-factory-scale F-144)
- Lý do (tiêu chí chất lượng cuối): Đúng và an toàn: hành vi hiện tại chặt (không phát hành sai), chỉ bất tiện cho dự án M/L thiếu khoá; thêm lối miễn mà guard chưa bảo vệ chỗ ghi lý do sẽ mở đường agent tự miễn. Chọn chỗ ghi (a hay b) là quyết định thiết kế gắn T-3858.
- Đường lùi: Đổi hàng về mở, thêm lối miễn theo (a) hoặc (b).
### D-499 · 2026-11-17T03:49:14+00:00 · 94 dòng 🟢 nợ review còn mở (audit check --strict đỏ): trả thế nào trong đợt 3 harden?
- Phương án: (1) Sửa mặc định kèm test hồi quy; chấp nhận có hạn 2027-01-21 khi là nghi ngờ chưa tái hiện, ranh giới sandbox, hiệu năng guard (đo ở T-3709), đổi thiết kế, hay lịch sử không viết lại được · (2) Sửa hết mọi mục, kể cả đổi thiết kế · (3) Chấp nhận hết có hạn, không sửa
- Chọn: Sửa mặc định kèm test hồi quy; chấp nhận có hạn 2027-01-21 khi là nghi ngờ chưa tái hiện, ranh giới sandbox, hiệu năng guard (đo ở T-3709), đổi thiết kế, hay lịch sử không viết lại được
- Lý do (tiêu chí chất lượng cuối): Đúng và an toàn: lỗi thật có tái hiện được sửa với test, chiều chặt hơn khi xung đột (D-415). Giữ đường lùi: mục chấp nhận có chủ và hạn, xét lại cùng mốc hàng rào 2027-01-21. Phương án 2 kéo thiết kế mới vào harden (rủi ro cao hơn lợi); phương án 3 bỏ lỗi đã biết. Test mới ở file riêng mỗi lát để chạy song song không đụng nhau.
- Đường lùi: Đổi các dòng chấp nhận về mở, lập lát sửa

### D-500 · 2026-11-17T05:59:16+00:00 · AUD-HAR-412: ở pha harden máy vẫn trả milestone_audit: now (audit delta theo mốc) trái ADR-0080 (vét việc không audit, audit dồn về cổng ký). Sửa máy hay sửa ADR?

- Phương án: (1) Sửa máy: ở delivery_phase harden, loop status không đòi audit theo mốc (milestone_audit bỏ/none), audit delta chỉ ở cổng ký; sửa README bước 10, autopilot bước 5, audit.md §1 cho khớp; giữ hành vi pha build · (2) Sửa ADR-0080 cho khớp máy: audit theo mốc cả ở harden · (3) Giữ cả hai, ghi chú ngoại lệ trong skill
- Chọn: Sửa máy: ở delivery_phase harden, loop status không đòi audit theo mốc (milestone_audit bỏ/none), audit delta chỉ ở cổng ký; sửa README bước 10, autopilot bước 5, audit.md §1 cho khớp; giữ hành vi pha build
- Lý do (tiêu chí chất lượng cuối): Đúng: chủ dự án yêu cầu không review/audit giữa đợt, chỉ ở cổng ký (D-494); máy in lệnh audit theo mốc làm vòng không hội tụ. Bền: một nguồn thật (máy) khớp ADR; test ghim cả hai pha. Phương án 2 đi ngược yêu cầu; 3 để mâu thuẫn tồn tại.
- Đường lùi: Revert PR sửa máy; milestone_audit trở lại ở harden

### D-501 · 2026-11-17T07:16:59+00:00 · Sau AUD-SEC-804, dòng quyết chạy thật vẫn có thể vào DECISIONS.md qua git merge/pull nhánh dựng bằng plumbing, MCP create_or_update_file, diff từ stdin — guard không bịt hết. Cứng hoá phía máy đọc (prod_switch) hay giữ chặn ở guard?

- Phương án: (1) Giữ chặn ở guard cho mọi đường ghi trực tiếp; ghi phần còn lại là giới hạn đã biết (AUD-SEC-814 chấp nhận có hạn 2027-01-21, xét cùng đợt xét lại hàng rào), không đổi xt.py trong bản này · (2) Cứng hoá xt.py: prod_switch chỉ nhận dòng quyết có dấu do decide-prod ghi (đổi hợp đồng dự án đích, cần cắt bản và di trú sổ cũ)
- Chọn: Giữ chặn ở guard cho mọi đường ghi trực tiếp; ghi phần còn lại là giới hạn đã biết (AUD-SEC-814 chấp nhận có hạn 2027-01-21, xét cùng đợt xét lại hàng rào), không đổi xt.py trong bản này
- Lý do (tiêu chí chất lượng cuối): Đúng và an toàn: mọi đường ghi một bước của agent đã bị chặn; đường còn lại cần chuỗi nhiều bước (dựng commit plumbing rồi merge) và vẫn hiện ra trong diff PR mà cổng merge thấy. Giữ đường lùi: phương án 2 đổi định dạng sổ của mọi dự án đích ngay trong bản harden, rủi ro hồi quy cao hơn lợi. Xét lại cùng mốc 2027-01-21 (LOOP-DESIGN-014).
- Đường lùi: Lập task cứng hoá prod_switch theo phương án 2 ở bản kế

### D-502 · 2026-11-17T08:32:56+00:00 · Cổng ký lần 2: reviewer đối kháng tìm thêm 8 🔴 guard (đều có từ trước, không hồi quy) ở các nhánh lần 1 chưa rà — mỗi vòng rà sâu hơn lại ra lỗ mới của bộ đọc shell heuristic. Đóng vòng harden thế nào cho hội tụ mà không hạ chuẩn?

- Phương án: (1) Sửa theo LỚP (không vá từng ca): mọi giá trị guard không tính chắc ở vị trí đích/cờ của lệnh có luật → BUDGET; kênh chạy lệnh (printf/echo escape vào shell, chỗ thay xargs, trình bọc lạ/viết tắt cờ, thân sh -c từ biến) → BUDGET. Cổng ký lần 3 chỉ rà diff sửa + hồi quy; lỗ mới thuộc lớp đã đóng → sửa; lỗ ngoài các lớp → ghi sổ, mức theo hậu quả, 🔴 vẫn sửa trước GO · (2) Tiếp tục vá từng ca và rà đối kháng không giới hạn tới khi một vòng không ra gì · (3) Chấp nhận các lỗ có từ trước tới 2027-01-21 (ADR-0067), chỉ sửa hồi quy
- Chọn: Sửa theo LỚP (không vá từng ca): mọi giá trị guard không tính chắc ở vị trí đích/cờ của lệnh có luật → BUDGET; kênh chạy lệnh (printf/echo escape vào shell, chỗ thay xargs, trình bọc lạ/viết tắt cờ, thân sh -c từ biến) → BUDGET. Cổng ký lần 3 chỉ rà diff sửa + hồi quy; lỗ mới thuộc lớp đã đóng → sửa; lỗ ngoài các lớp → ghi sổ, mức theo hậu quả, 🔴 vẫn sửa trước GO
- Lý do (tiêu chí chất lượng cuối): Đúng và an toàn: 🔴 vẫn phải sửa trước GO, nhưng sửa theo lớp đóng cả họ thay vì từng mẫu nên số vòng hội tụ. Phương án 2 không có điểm dừng (bộ đọc heuristic luôn còn mẫu mới); phương án 3 để lọt 🔴 đã tái hiện bằng bash thật. Hướng BUDGET khi không chắc khớp D-415; chặn oan được đo bằng blueprint --run và fuzz đối chứng.
- Đường lùi: Đổi D-502: quay về vá từng ca hoặc nới tiêu chí lần 3

### D-503 · 2026-11-17T11:44:41+00:00 · Cổng ký lần 3: các lớp D-502 (giá trị không tính chắc, kênh chạy lệnh) vẫn còn 14 biến thể 🔴 có từ trước — liệt kê tiếp không có điểm dừng. Đóng lớp thế nào cho hữu hạn?

- Phương án: (1) Mặc định chặn trong lệnh có luật: (a) từ có mở rộng, thay lệnh hay toán tử tham số ở vị trí đích, cờ hay tên lệnh con của lệnh có luật (xoá tệp, git, gh có luật, DATA_DESTROY) → BUDGET trừ danh sách cho phép hẹp đã tính chắc; (b) tên lệnh lạ hay trình bọc mà sau nó ở bất kỳ vị trí nào có tên lệnh có luật → quét mọi hậu tố hoặc BUDGET; (c) xargs đưa tới shell, trình bọc, lệnh xoá hay git → BUDGET trừ dạng trơn đã có luật. Cổng ký lần 4 kiểm bất biến mặc định chặn bằng fuzz đối kháng có hướng và hồi quy blueprint/idiom · (2) Tiếp tục liệt kê biến thể theo từng lớp mỗi vòng · (3) Chấp nhận phần còn lại tới 2027-01-21 vì guard là phòng thủ chiều sâu (ranh giới là sandbox, D-331/D-332)
- Chọn: Mặc định chặn trong lệnh có luật: (a) từ có mở rộng, thay lệnh hay toán tử tham số ở vị trí đích, cờ hay tên lệnh con của lệnh có luật (xoá tệp, git, gh có luật, DATA_DESTROY) → BUDGET trừ danh sách cho phép hẹp đã tính chắc; (b) tên lệnh lạ hay trình bọc mà sau nó ở bất kỳ vị trí nào có tên lệnh có luật → quét mọi hậu tố hoặc BUDGET; (c) xargs đưa tới shell, trình bọc, lệnh xoá hay git → BUDGET trừ dạng trơn đã có luật. Cổng ký lần 4 kiểm bất biến mặc định chặn bằng fuzz đối kháng có hướng và hồi quy blueprint/idiom
- Lý do (tiêu chí chất lượng cuối): Đúng và an toàn: đổi danh sách chặn mở thành danh sách cho phép đóng — biến thể chưa biết rơi vào BUDGET, vòng rà sau kiểm bất biến chứ không săn mẫu; chặt khi không chắc (D-415). Giữ đường lùi: danh sách cho phép mở rộng dần theo chặn oan đo được (blueprint --run, fuzz đối chứng). Phương án 2 không hội tụ (ba vòng đã chứng minh); phương án 3 để lọt 🔴 đã tái hiện bằng bash thật trong khi chủ dự án đòi trả hết nợ trước GO.
- Đường lùi: Gỡ cổng mặc định chặn, quay lại D-502

### D-504 · 2026-11-17T17:30:49+00:00 · Advisory GHSA-fc5q-39xc-vjpf (picomatch <= 4.0.7, ReDoS, high, công bố 2026-10-19) làm job pack-npm-audit đỏ mọi PR; npm chưa có bản vá (latest 4.0.7, first_patched_version null). picomatch chỉ đến qua devDependency vitest (vite → tinyglobby → fdir) của gói web-api-ts. Xử lý thế nào?

- Phương án: (1) Ngoại lệ có hạn theo BASE-DEP-004: pnpm auditConfig.ignoreGhsas cho đúng GHSA này trong starter, kèm tệp ngoại lệ có cve/reason/expires (hạn 2026-12-18) và test đỏ khi hết hạn hay khi ignore không có dòng ngoại lệ; giữ --audit-level moderate · (2) Hạ ngưỡng pnpm audit hoặc chỉ audit --prod · (3) Gỡ vitest khỏi gói starter
- Chọn: Ngoại lệ có hạn theo BASE-DEP-004: pnpm auditConfig.ignoreGhsas cho đúng GHSA này trong starter, kèm tệp ngoại lệ có cve/reason/expires (hạn 2026-12-18) và test đỏ khi hết hạn hay khi ignore không có dòng ngoại lệ; giữ --audit-level moderate
- Lý do (tiêu chí chất lượng cuối): Đúng và an toàn: phụ thuộc chạy thật (kysely, pg) không dính; mẫu glob trong chuỗi dev lấy từ repo, không từ người dùng; ngoại lệ hẹp đúng một GHSA, có hạn, máy đỏ khi hết hạn — cổng không bị nới cho advisory khác. Phương án 2 nới cổng (cấm, LOOP-CI-001); phương án 3 bỏ khả năng test của gói. Đây cũng là đường ngoại lệ có hạn AUD-DEP-024 còn thiếu.
- Đường lùi: Gỡ ignoreGhsas và tệp ngoại lệ khi picomatch có bản vá (nâng lockfile)

### D-505 · 2026-11-18T00:36:31+00:00 · Hạn DECISION_SECONDS của guard: 15 s hay 30 s? (T-3942) Chuỗi cd … && … 19 KB trước cho qua sau 34 s, nay BUDGET; lệnh 100 KB cần quyết định < 20 s để không vượt hạn hook 1200 s.

- Phương án: (1) Giữ 15 s: lệnh dài phải tách nhỏ, lệnh 100 KB quyết định ≤ 15 s · (2) Nâng ~30 s: giữ lệnh 19 KB nhưng lệnh 100 KB quá 20 s
- Chọn: Giữ 15 s: lệnh dài phải tách nhỏ, lệnh 100 KB quyết định ≤ 15 s
- Lý do (tiêu chí chất lượng cuối): Đúng và an toàn trên hết: quá hạn là BUDGET (chặn, không hỏi người), lỗ 256 KB chạy quá 1300 s vượt hạn hook đã đóng. Lệnh Bash 19 KB một dòng rất hiếm, tách nhỏ không mất gì; nâng hạn chỉ phục vụ tốc độ/tiện (tiêu chí 5).
- Đường lùi: Đổi hằng DECISION_SECONDS ở .claude/hooks/guard.py kèm test thời gian 100 KB

### D-506 · 2026-11-18T02:12:13+00:00 · Cổng ký lần 7 (b76d7af5) vẫn có 7 🔴/🟠 (4 ở lớp giá trị tính được, 3 ở lớp stdin/heredoc/.git/RUNNERS). Mỗi cổng ký lại thấy thêm cách che mới. Sửa tiếp thế nào để hội tụ?

- Phương án: (1) Đảo chiều lớp giá trị tính được: chỉ tin $(date/mktemp/git/cat) khi toàn lệnh chỉ có cấu trúc trong danh sách đóng (mọi gán biến lạ, hàm, trap, eval, hash/alias → bỏ ưu đãi), sửa tiếp theo lớp (stdin của công cụ ngoài, .git/**, RUNNERS) trong một đợt T-3945, rồi cổng ký 8 · (2) Từng ca như trước (thêm tên vào SHADOW, từng regex) · (3) Bỏ hẳn ưu đãi giá trị tính được cho mọi lệnh có luật (rm/mv…): chặn oan `rm -rf "$TMP"` với TMP=$(mktemp -d) phổ biến
- Chọn: Đảo chiều lớp giá trị tính được: chỉ tin $(date/mktemp/git/cat) khi toàn lệnh chỉ có cấu trúc trong danh sách đóng (mọi gán biến lạ, hàm, trap, eval, hash/alias → bỏ ưu đãi), sửa tiếp theo lớp (stdin của công cụ ngoài, .git/**, RUNNERS) trong một đợt T-3945, rồi cổng ký 8
- Lý do (tiêu chí chất lượng cuối): Đúng và an toàn (tiêu chí 1) và hội tụ: danh sách đóng không phụ thuộc cách che mới; giữ trải nghiệm cuối (tiêu chí 4) vì lệnh lành rm -rf "$TMP"/mv x "$(date +%F)" trong lệnh không có cấu trúc lạ vẫn qua. Phương án 2 là cách đã thất bại 6 vòng (D-502); phương án 3 chặn oan lệnh phổ biến.
- Đường lùi: Hoàn nguyên commit T-3945; quay về luật SHADOW theo tên của #654

### D-507 · 2026-11-18T05:57:25+00:00 · Cổng ký lần 8 (7b1ebc84) vẫn tìm 8 🔴/🟠 ở lô fuzz và 3 🔴 + 5 🟠 ở lô hồi quy; mỗi vòng reviewer mở rộng sang họ mới (8 vòng liên tiếp). Đóng vòng thế nào để hội tụ mà không hạ tiêu chí an toàn?

- Phương án: (1) Sửa nhóm lỗi có thể xảy ra do lỡ tay hoặc hồi quy/chặn oan lệnh phổ biến (rm trong .git qua glob/dotglob, mktemp -p/.. sau giá trị tính được, $(date) vào thư mục có sẵn, .git chung của worktree, push src:dst từ $(branch), pull/fetch/rebase với $(branch), [ -eq ] bị coi số học, SQL/manifest bị quét theo từ, bỏ nháy thân stdin, cờ dính -cVAL, vim/ex -c/+cmd, procsub vào công cụ đọc chương trình, ghi đè .git/HEAD bằng cp/tee/sed -i/ln/install); chấp nhận có chủ và hạn 2027-01-21 (cùng mốc xét sandbox D-331/D-332, ADR-0072) cho hai họ dựng lệnh lúc chạy cần nhiều bước hoặc xây chuỗi động: trồng lệnh vào thư mục PATH qua 3 lệnh rồi $(date), argv parallel dựng bằng nối chuỗi/biến/exec{...}; ghi rõ giới hạn ở harness-files.md; cổng ký 9 chấp nhận khi không còn 🔴/🟠 mở ngoài hai họ đã chấp nhận · (2) Tiếp tục sửa mọi ca fuzz mỗi vòng cho tới khi reviewer không tìm thêm (không có điểm dừng định trước) · (3) Dừng harden guard, ký GO với toàn bộ phát hiện chấp nhận
- Chọn: Phương án 1 (sửa nhóm lỗi do lỡ tay/chặn oan; chấp nhận hai họ dựng lệnh lúc chạy, hạn 2027-01-21)
- Lý do (tiêu chí chất lượng cuối): Đúng và an toàn trước: mọi lỗi có thể do lỡ tay hoặc làm hỏng lệnh lành phổ biến đều được sửa; chỉ hai họ cần chủ ý nhiều bước/dựng chuỗi động (không thể là tai nạn của agent) được chấp nhận, có chủ, có hạn, nêu ở tài liệu, và hàng rào thật là sandbox (ADR-0072) chứ không phải heuristic văn bản. Phương án 2 không có điểm dừng nên không hội tụ (8 vòng); phương án 3 bỏ cả lỗi lỡ tay.
- Đường lùi: Mở lại AUD-SEC chấp nhận thành mở và sửa ở đợt sau; không đổi mã

### D-508 · 2026-11-18T07:45:11+00:00 · Cổng ký lần 9 (e2f89c8b): lô hồi quy 0 🔴/3 🟠, lô fuzz 6 🔴/4 🟠 — phần lớn là dạng che giấu cố ý trong lệnh ghép/echo/fd (vd { python3; } <<< 'chương trình có rm -rf ~', echo '!r\m -rf ~' | ed, make -f /dev/fd/3). Phân loại và đóng thế nào?

- Phương án: (1) Sửa nhóm có thể do lỡ tay/hồi quy/chặn oan (here-string $ với công cụ không đọc chương trình, lối thoát vim/sqlite3/psql qua ống, for/select/exec{PATH} ghi PATH, $(date) qua biến và env -C, ghi đè .git/** bằng truncate/cp/> và gitdir/refs của worktree, sub/.git, ex -sc cụm cờ ngắn, test rò patch); với nhóm chương trình viết tường minh trong stdin của công cụ đọc chương trình che bằng lệnh ghép/echo/fd (N1, N4, N6, N9, N11, N12) chỉ sửa nếu gọn, không thì chấp nhận họ (c) có chủ và hạn 2027-01-21 cùng (a)/(b) · (2) Sửa toàn bộ N1–N13 bằng mọi giá · (3) Chấp nhận mọi phát hiện còn lại và ký GO
- Chọn: Sửa nhóm có thể do lỡ tay/hồi quy/chặn oan (here-string $ với công cụ không đọc chương trình, lối thoát vim/sqlite3/psql qua ống, for/select/exec{PATH} ghi PATH, $(date) qua biến và env -C, ghi đè .git/** bằng truncate/cp/> và gitdir/refs của worktree, sub/.git, ex -sc cụm cờ ngắn, test rò patch); với nhóm chương trình viết tường minh trong stdin của công cụ đọc chương trình che bằng lệnh ghép/echo/fd (N1, N4, N6, N9, N11, N12) chỉ sửa nếu gọn, không thì chấp nhận họ (c) có chủ và hạn 2027-01-21 cùng (a)/(b)
- Lý do (tiêu chí chất lượng cuối): Đúng và an toàn: mọi lỗi có thể do lỡ tay hoặc chặn oan lệnh phổ biến vẫn được sửa; nhóm (c) cần payload nguy hiểm viết tường minh vào stdin của trình thông dịch rồi che bằng cú pháp — không thể là tai nạn của agent và cùng bản chất với (a)/(b) đã chấp nhận ở D-507; có điều kiện 'sửa nếu gọn' để không bỏ lỡ cách sửa rẻ. Phương án 2 không có điểm dừng (9 vòng); phương án 3 bỏ cả lỗi lỡ tay.
- Đường lùi: Mở lại họ (c) thành AUD mở và sửa ở đợt sau; không đổi mã

### D-509 · 2026-11-18T23:15:12+00:00 · Cổng ký 11 (4d8c403f): lô A 7 🔴/7 🟠, lô C 2 🔴/4 🟠, lô B 0 🔴/7 🟠 (chặn oan phổ biến: git pull --rebase && git push). 11 vòng chưa hội tụ. Kết thúc harden thế nào để cắt 3.34.0?

- Phương án: (1) Một đợt sửa cuối (đợt 14) cho mọi 🔴/🟠 một bước có thể do lỡ tay và chặn oan phổ biến, rồi KHÔNG chạy thêm cổng ký fuzz toàn diện: kiểm bằng cổng máy + một lô chặn oan hồi quy, ký GO; họ lối thoát shell/che giấu cố ý ghi giới hạn đã biết (hạn 2027-01-21 cùng đánh giá sandbox ADR-0072) · (2) Tiếp tục lặp cổng ký tới khi sạch · (3) Ký GO ngay, ghi mọi phát hiện là giới hạn
- Chọn: Một đợt sửa cuối (đợt 14) cho mọi 🔴/🟠 một bước có thể do lỡ tay và chặn oan phổ biến, rồi KHÔNG chạy thêm cổng ký fuzz toàn diện: kiểm bằng cổng máy + một lô chặn oan hồi quy, ký GO; họ lối thoát shell/che giấu cố ý ghi giới hạn đã biết (hạn 2027-01-21 cùng đánh giá sandbox ADR-0072)
- Lý do (tiêu chí chất lượng cuối): Người dùng chọn phương án 1 (2026-11-19). Đúng và an toàn: mọi lỗ một bước dễ lỡ tay và chặn oan phổ biến vẫn được sửa; hàng rào thật cho dạng cố ý là sandbox (ADR-0072); 11 vòng cho thấy fuzz mở rộng không hội tụ nên dừng ở kiểm hồi quy.
- Đường lùi: Mở lại các AUD chấp nhận thành mở và sửa ở đợt sau

### D-510 · 2026-11-19T04:23:43+00:00 · Cổng commit đỏ ở phiên cloud chạy root vì hai ca đối chứng git submodule (AUD-SEC-805) phụ thuộc uid của máy chạy test — xử lý thế nào để commit bản nghiên cứu 2026-11-19?

- Phương án: (1) Ghim tiền đề exec-path mặc định không đổi được trong hai ca đối chứng (tests/git_fixture.py default_exec_path_fixed); không đổi guard, không bỏ khẳng định nào · (2) Không commit, giao bản nghiên cứu ngoài repo và chờ người sửa test · (3) Sửa guard để root vẫn tin exec-path mặc định
- Chọn: Ghim tiền đề exec-path mặc định không đổi được trong hai ca đối chứng (tests/git_fixture.py default_exec_path_fixed); không đổi guard, không bỏ khẳng định nào
- Lý do (tiêu chí chất lượng cuối): Đúng và an toàn: guard giữ nguyên, ca đối chứng vẫn khẳng định cùng quyết định; chạy không root (CI) kết quả không đổi (đã chạy cả hai uid). Phương án 3 nới hàng rào thật; phương án 2 để mất việc khi container bị thu hồi.
- Đường lùi: git revert commit test(guard) — hai ca trở lại phụ thuộc uid

### D-511 · 2026-11-19T05:08:01+00:00 · Chủ dự án 2026-11-19: 'code nhanh nhất là được, xong rồi tạo PR, chờ cắt bản xong rồi triển khai' — đổi gì ở khung để dự án đích viết mã nhanh nhất trong pha build?

- Phương án: (1) Đổi mặc định của máy theo pha: compose không --scale giữ quy mô bản cũ, chưa có thì S; doctor không cảnh báo chậm bản MINOR/PATCH ở pha build; M và nâng khung dồn về /complete (ADR-0081) · (2) Giữ mặc định, chỉ viết hướng dẫn nên chọn S và nâng khung theo pha · (3) Thêm fact phủ định cho compose để bỏ module không áp dụng
- Chọn: Đổi mặc định của máy theo pha: compose không --scale giữ quy mô bản cũ, chưa có thì S; doctor không cảnh báo chậm bản MINOR/PATCH ở pha build; M và nâng khung dồn về /complete (ADR-0081)
- Lý do (tiêu chí chất lượng cuối): Bền, đơn giản, test được: số đo 2026-11-19 cho thấy M từ đầu (473 so với 70 MUST) và nâng khung mỗi phiên (16–22 % commit) là hai khoản tốn nhất do mặc định của máy; hướng dẫn đã có mà không đổi kết quả; ở S không còn mục AI/realtime nên phương án 3 thừa. An toàn giữ nguyên: release-check và sàn Gate theo quy mô khai không đổi, ghép lại không ngầm hạ quy mô, chậm MAJOR vẫn báo.
- Đường lùi: Revert PR của ADR-0081; dự án cần M ghi rõ compose --scale M

### D-512 · 2026-11-19T05:50:07+00:00 · T-3958: ruleset main (repo khung + mẫu) để required_review_thread_resolution false từ #558 (ADR-0079), trái chữ WF-REVIEW-005/WF-GIT-002 (true, chặn merge). Sửa ruleset hay sửa yêu cầu?

- Phương án: (1) Giữ ruleset false; sửa WF-REVIEW-005/WF-GIT-002 (giữ ID, giữ MUST) thành có điều kiện: thread resolution bắt buộc khi merge_review: required hoặc có người review tay; optional thì pr next + review 1 lần thay thế · (2) Bật lại true ở cả hai ruleset (theo D-143), giữ chữ yêu cầu
- Chọn: Giữ ruleset false; sửa WF-REVIEW-005/WF-GIT-002 (giữ ID, giữ MUST) thành có điều kiện: thread resolution bắt buộc khi merge_review: required hoặc có người review tay; optional thì pr next + review 1 lần thay thế
- Lý do (tiêu chí chất lượng cuối): Đúng: ADR-0079 bỏ có chủ ý yêu cầu thread để steward tự merge; bật lại true làm PR xanh chờ người resolve, trái ADR. Blocker vẫn bị chặn bởi pr next + review 1 lần (ADR-0062). Bền: test ghim khoá ruleset khớp merge_review ở cả repo khung và mẫu. Thay D-143 ở khoá này.
- Đường lùi: Đặt merge_review: required và required_review_thread_resolution: true ở ruleset (test ghim đòi hai khoá đi cùng nhau)

### D-513 · 2026-11-19T05:53:17+00:00 · T-3958: GHSA-fc5q-39xc-vjpf (picomatch, ngoại lệ có hạn D-504) đã bị rút (OSV withdrawn 2026-11-18T15:38:56Z). Gỡ ngoại lệ thế nào?

- Phương án: (1) Gỡ id khỏi ignoreGhsas (để danh sách rỗng) và audit-exceptions.json (exceptions rỗng); giữ check-audit-exceptions.ts, bước CI và test cho ngoại lệ sau này · (2) Xoá hẳn pnpm-workspace.yaml, audit-exceptions.json cùng máy kiểm · (3) Giữ ngoại lệ tới hạn 2026-12-18
- Chọn: Gỡ id khỏi ignoreGhsas (để danh sách rỗng) và audit-exceptions.json (exceptions rỗng); giữ check-audit-exceptions.ts, bước CI và test cho ngoại lệ sau này
- Lý do (tiêu chí chất lượng cuối): Đúng: advisory bị rút nên pnpm audit không còn báo (kiểm cục bộ pnpm 12.16.1: No known vulnerabilities, exit 0 với danh sách rỗng); giữ ngoại lệ chết làm sổ sai và audit:exceptions vẫn phải gánh. Đường lùi: cơ chế kiểm hạn giữ nguyên cho ngoại lệ sau. Phương án 2 bỏ máy kiểm hạn (BASE-DEP-004), phương án 3 giữ ngoại lệ không còn lý do.
- Đường lùi: Thêm lại GHSA vào ignoreGhsas và dòng ngoại lệ (cve, lý do, người duyệt, hạn) nếu advisory được khôi phục

### D-514 · 2026-11-19T08:52:54+00:00 · Review #672 (reviewer-alt): check-audit-exceptions.ts (+ bộ đọc Python song sinh trong test) vẫn đọc rỗng, exit 0, với giá trị ignoreGhsas ở dòng kế sau khoá, alias YAML và khoá thoát ký tự — lỗ có từ trước PR này. Sửa trong PR cắt bản hay ghi nợ?

- Phương án: (1) Ghi nợ 🟠 chấp nhận có hạn 2027-01-21 (ADR-0062), sửa ở 3.35.0 bằng cách lấy auditConfig từ chính pnpm · (2) Sửa ngay trong PR cắt bản: ném lỗi khi dòng kế không phải mục danh sách, từ chối khoá có thoát ký tự · (3) Gỡ máy kiểm khỏi CI gói
- Chọn: Ghi nợ 🟠 chấp nhận có hạn 2027-01-21 (ADR-0062), sửa ở 3.35.0 bằng cách lấy auditConfig từ chính pnpm
- Lý do (tiêu chí chất lượng cuối): Đúng và an toàn: danh sách ignoreGhsas hiện rỗng và do chủ dự án/agent tự viết, dạng lách là cố ý che giấu; pnpm audit vẫn chạy và báo lỗ hổng thật; không tạo vòng sửa thứ 15 (D-509 chốt một đợt sửa cuối, ADR-0062 ghi nợ 🟠 sau review một lần). Sửa đúng cách cần đổi bộ đọc sang pnpm config, đáng làm kỹ ở 3.35.0.
- Đường lùi: Sửa ngay: thêm kiểm dòng kế/alias/khoá thoát vào check-audit-exceptions.ts và UNREAD_FORMS của test, đóng AUD-DEP-037

### D-515 · 2026-11-19T09:40:34+00:00 · Review #673 (reviewer-alt, lần 2): /complete không có bước nào chạy lại doctor sau khi đặt delivery_phase: harden nên 'nâng khung ở ranh giới pha' của ADR-0081 và LOOP-HARNESS-020 không xảy ra trong lượt đổi pha (Bước 0 chạy doctor khi còn build). Sửa trước khi ký GO hay ghi nợ?

- Phương án: (1) Ghi nợ 🟠 chấp nhận có hạn 2026-12-02 (ADR-0062), sửa ở 3.34.1: thêm 'chạy lại doctor' vào Bước 1 của /complete và cắt chữ chỗ khác (skill đang 6137/6144 byte) · (2) Sửa ngay: PR riêng, bản 3.34.1 trước khi nâng 4 dự án đích · (3) Hoàn nguyên ghim khung ở pha build (revert ADR-0081 phần doctor)
- Chọn: Ghi nợ 🟠 chấp nhận có hạn 2026-12-02 (ADR-0062), sửa ở 3.34.1: thêm 'chạy lại doctor' vào Bước 1 của /complete và cắt chữ chỗ khác (skill đang 6137/6144 byte)
- Lý do (tiêu chí chất lượng cuối): Đúng và an toàn: lỗi là thiếu một lời nhắc, không phải hành vi nguy hiểm; doctor --drift vẫn báo mọi độ chậm ở cả hai pha và chậm MAJOR vẫn được nhắc, nên dự án build không mất đường biết có bản mới. Tag v3.34.0 đã gắn trên ef146b0 và 4 dự án đích đang nâng lên đúng bản này; sửa skill cần PR, CI, bản 3.34.1 — không chặn chữ ký GO vì chữ ký tách khỏi tag (D-179) và không đổi mã chạy. Một vòng sửa nữa sau D-509 không được lợi hơn ghi nợ có hạn ngắn.
- Đường lùi: Sửa ngay trong 3.34.1: Bước 1 của /complete thêm doctor, cắt byte ở chỗ khác, CHANGELOG, bản nâng lại cho dự án đích

### D-516 · 2026-11-19T11:33:50+00:00 · Sau 3.34.0, chủ repo hỏi 'tự động tối đa, code nhanh nhất' và giao 'xử lý theo hướng tốt nhất'. Số đo phiên cắt bản: cổng commit ~12 phút (sửa 1 tệp .md kéo 331/700 lớp test vì test-select chọn theo TỆP và luật đuôi '*.md' khớp cả 'GO-NO-GO*.md'); tổng trọng số test 2 605 s / 4 shard = 651 s > trần 10 phút (shard 3/4 bị huỷ ở #672, #674); guard chặn oan lệnh chỉ-đọc dạng ghép ~15 lần. Làm gì trước?

- Phương án: (1) Ba lát nhỏ ngay: (1) CI test 6 shard, test-main 4 shard; (2) test-select chọn theo LỚP + glob phải khớp tên tệp đổi (đo thử: 331 → 64–80 lớp cho tệp .md); (3) /complete chạy lại doctor sau khi đặt harden (AUD-HAR-440). Nới guard cho lệnh chỉ-đọc dạng ghép để 3.35.0, sau khi tách guard.py (D-142), có corpus đối kháng · (2) Làm cả nới guard ngay trong đợt này · (3) Nâng trần thời gian job lên 15 phút và giữ test-select
- Chọn: Ba lát nhỏ ngay: (1) CI test 6 shard, test-main 4 shard; (2) test-select chọn theo LỚP + glob phải khớp tên tệp đổi (đo thử: 331 → 64–80 lớp cho tệp .md); (3) /complete chạy lại doctor sau khi đặt harden (AUD-HAR-440). Nới guard cho lệnh chỉ-đọc dạng ghép để 3.35.0, sau khi tách guard.py (D-142), có corpus đối kháng
- Lý do (tiêu chí chất lượng cuối): Đúng và an toàn: hai nghẽn lớn nhất đo được là cổng commit và shard vượt trần, sửa cả hai không đụng hàng rào và CI vẫn là cổng đầy đủ (100 % coverage) nên chọn sót ở cổng commit bị CI bắt. Nới guard là đổi hàng rào vừa qua 14 đợt harden (D-509 chốt không thêm vòng fuzz); chi phí thật của chặn oan là vài chục giây mỗi lần, nhỏ hơn nhiều so với 12 phút mỗi commit, nên làm sau trên guard đã tách module với corpus riêng. Nâng trần thời gian làm CI chậm hơn và che việc shard lệch.
- Đường lùi: Revert từng PR: ci.yml về 4/3 shard; test-select về chọn theo tệp; SKILL.md /complete về bản 3.34.0

### D-517 · 2026-11-19T13:24:50+00:00 · Đo sau đợt 16 cho thấy hai điều tôi đã nói sai/chưa thấy: (A) cổng commit ~12 phút ở checkout chính KHÔNG phải do test-select chọn 331 lớp — 4 tệp chưa track .codex/agents/*.toml không ánh xạ được nên MỌI commit ở đó chạy cả 697 lớp; (B) commit trong git worktree nằm dưới gốc dự án (.claude/worktrees/…, có xt.yaml) được hook coi là 'repo lồng có cổng riêng' → ask_strict → ở chính sách mặc định exit 0, cổng commit KHÔNG chạy (thử payload giả: worktree rc 0 sau 1 s, checkout chính chạy cổng). Xử lý thế nào?

- Phương án: (1) Đính chính trong sổ/PROGRESS và sửa cả hai ở đợt 17: (B) worktree CÙNG repo (cùng git common dir với dự án) → chạy cổng của dự án trên chính worktree đó; repo lồng khác giữ luật AUD-SEC-015; (A) tệp chưa track vẫn kéo test liên quan nhưng không còn đẩy lên 'cả bộ' khi không ánh xạ được — chỉ thay đổi đã track/đã stage mới đẩy · (2) Chỉ đính chính, thêm .codex/ và .agents/ vào .gitignore · (3) Giữ nguyên, coi CI là cổng duy nhất cho worktree
- Chọn: Đính chính trong sổ/PROGRESS và sửa cả hai ở đợt 17: (B) worktree CÙNG repo (cùng git common dir với dự án) → chạy cổng của dự án trên chính worktree đó; repo lồng khác giữ luật AUD-SEC-015; (A) tệp chưa track vẫn kéo test liên quan nhưng không còn đẩy lên 'cả bộ' khi không ánh xạ được — chỉ thay đổi đã track/đã stage mới đẩy
- Lý do (tiêu chí chất lượng cuối): Đúng và an toàn: (B) là lỗ của cổng commit — mọi commit của executor/phiên chính trong worktree hôm nay không qua cổng cục bộ (CI vẫn bắt, nhưng luật 'cổng commit do hook chạy' không đúng với worktree); sửa là làm chặt hơn. (A) tệp chưa track không stage không thể vào commit (guard buộc git commit đứng riêng), nên đẩy cả bộ vì chúng chỉ tốn 12 phút mà không thêm an toàn; .gitignore là quyết định về tệp của chủ repo (.codex/.agents do công cụ khác sinh), không thuộc phiên. Giữ nguyên là để sai lệch giữa tài liệu và hành vi.
- Đường lùi: Revert PR đợt 17: hook về luật repo lồng cũ; dev-task.sh/test-select về tính tệp chưa track như tệp đổi

### D-518 · 2026-11-19T14:21:46+00:00 · Review đợt 17 (reviewer-alt): T-3964 (cổng commit cho worktree cùng repo) đúng/an toàn; T-3965 (bỏ qua tệp chưa track không ánh xạ được) có 🟠 — tiền đề 'tệp chưa track không vào được commit' SAI: 'git add -A && git commit' được guard cho qua, hook chạy trước cả lệnh, nên tệp mới vào commit mà cổng chạy 0 test. Thêm: số '697 lớp' ở D-517 đo trên checkout chính đang ở nhánh release/3.34.0 cũ; trên main hiện tại 35 tệp chưa track đều ánh xạ được và kéo 449/702 lớp. Làm gì với T-3965?

- Phương án: (1) Rút T-3965 khỏi PR đợt 17 (chỉ ship T-3964 + hai 🟢 của reviewer); AUD-HAR-443 giữ mở với dữ kiện đã đính chính; làm lại sau: guard.py báo thêm trường 'lệnh là git commit đứng một mình' → chỉ khi đó loại MỌI tệp chưa track khỏi tập tệp đổi, còn lại giữ cách thận trọng · (2) Sửa T-3965 ngay trong PR này bằng cách dò chuỗi 'git add' trong lệnh ở hook · (3) Bỏ hẳn AUD-HAR-443
- Chọn: Rút T-3965 khỏi PR đợt 17 (chỉ ship T-3964 + hai 🟢 của reviewer); AUD-HAR-443 giữ mở với dữ kiện đã đính chính; làm lại sau: guard.py báo thêm trường 'lệnh là git commit đứng một mình' → chỉ khi đó loại MỌI tệp chưa track khỏi tập tệp đổi, còn lại giữ cách thận trọng
- Lý do (tiêu chí chất lượng cuối): Đúng và an toàn: bản T-3965 hiện tại làm cổng yếu đi (tệp mới vào commit không được test) nên không được merge; dò chuỗi trong hook là phân tích lệnh lần hai ngoài guard — đúng loại lỗi 14 đợt harden vừa dọn; trường mới phải do guard.py tính (một nơi đọc lệnh) và cần corpus riêng, hợp với đợt tách guard.py (D-142). T-3964 độc lập và đóng một 🟠 mở nên ship trước.
- Đường lùi: Khôi phục bản T-3965 từ /home/liend/xt-scratch-gatewt/full-before-split.patch nếu chứng minh được tiền đề (không khuyến nghị)

### D-519 · 2026-11-19T15:20:48+00:00 · Chủ repo: 'cái nào liên quan đến harness thì tích hợp hết' cho .agents/ và .codex/ chưa track ở gốc repo (do /import của Codex CLI sinh 2026-11-14: hooks.json đường tuyệt đối và không có PreToolUse, bản sao guard.py cũ ở commit 331145c1, agent TOML trỏ .Codex/… không tồn tại, 5/16 skill lạc hậu — research/2026-11-19-codex-harness.md). Tích hợp thế nào?

- Phương án: (1) ADR-0082: sinh từ .claude/ bằng máy — .codex/hooks.json chỉ PreToolUse gọi xt_adapter.py (một guard), .agents/skills là bản sao byte, .codex/agents/*.toml sinh từ .claude/agents; install.py --harness codex sinh cho dự án đích; repo khung commit đầu ra và test so từng byte · (2) Commit nguyên trạng tệp do /import sinh · (3) Symlink .agents/skills → .claude/skills, không làm agent
- Chọn: ADR-0082: sinh từ .claude/ bằng máy — .codex/hooks.json chỉ PreToolUse gọi xt_adapter.py (một guard), .agents/skills là bản sao byte, .codex/agents/*.toml sinh từ .claude/agents; install.py --harness codex sinh cho dự án đích; repo khung commit đầu ra và test so từng byte
- Lý do (tiêu chí chất lượng cuối): Đúng và an toàn: bản /import mang một guard thứ hai đã cũ và không gắn PreToolUse nên Codex trong repo không qua hàng rào; một nguồn (.claude/) + bộ sinh + test đồng bộ giữ 'một chủ đề một nhà' và không ghi đường của một máy vào repo. Symlink không chạy trên Windows/zip và trái luật không ghi xuyên symlink ở harness (AUD-SEC-650/651). Chủ repo đã đồng ý hướng này ('làm theo hướng của bạn').
- Đường lùi: Revert PR của ADR-0082: xoá .agents/skills, .codex/ khỏi repo và nhánh sinh trong install.py

### D-520 · 2026-11-19T17:03:58+00:00 · Review #684 lượt 3: gương Codex của dự án (.agents/skills/<tên>/SKILL.md = bản dự án tự sửa C, trùng đầu ra sinh từ .claude/ của dự án) được ghi nhận là tệp khung quản lý ở lần cài đầu (kept → ghi hash vào codex_files); lần cài sau có --force-harness thay .claude/ bằng bản khung F thì gương được cập nhật thành F, không có .xtemplates-new — trái câu tài liệu 'gương dự án tự có không bị ghi đè'. Sửa mã hay sửa tài liệu?

- Phương án: (1) Sửa tài liệu và tên test (b): tệp Codex là sản phẩm SINH từ .claude/; tệp trùng đầu ra sinh được ghi nhận (như mọi tệp harness trùng bản khung) và đi theo .claude/ ở các lần cài sau, kể cả khi --force-harness thay nguồn; chỉ tệp khác bản đã ghi nhận mới được giữ kèm .xtemplates-new · (2) Sửa mã (a): khi --force-harness, bỏ qua hash codex_files cho tệp có nguồn không phải bản khung → .xtemplates-new
- Chọn: Phương án (1): sửa tài liệu và tên test (b)
- Lý do (tiêu chí chất lượng cuối): Đúng: gương là bản sao byte của nguồn; khi người dùng chủ động --force-harness thay .claude/skills/<tên> thì gương giữ bản cũ sẽ LỆCH nguồn (test gương của dhcb đỏ) — đi theo nguồn mới là hành vi nhất quán với mọi tệp harness. Phương án (a) thêm ngoại lệ vào luật sở hữu và để gương lệch nguồn. Lần cài ĐẦU với --force-harness vẫn giữ gương và để .xtemplates-new.
- Đường lùi: Áp phương án (a) trong install.py

### D-521 · 2026-11-19T23:39:27+00:00 · Điều phối một dự án từ ý tưởng qua ba giai đoạn tới vận hành bằng gì?

- Phương án: (1) Dùng sổ giai đoạn, trạng thái vòng lặp và chứng cứ bản chạy hiện có; chốt phạm vi nghiệm thu ở Git; diễn tập trước chuyển giao cho CD của sản phẩm · (2) Tạo bộ điều phối riêng với sổ trạng thái, quyền duyệt và hạ tầng production mặc định
- Chọn: Phương án (1)
- Lý do (tiêu chí chất lượng cuối): Giữ một nguồn trạng thái cho mỗi quyết định, duyệt đúng bản, đo thời gian, kiểm lại được trên repo mới và repo có sẵn
- Đường lùi: Dự án tiếp tục dùng các lệnh stage, loop, release-check, deploy, perf riêng; kiểm lại hợp đồng khi đổi adapter.

### D-522 · 2026-11-20T01:05:30+00:00 · Trình MVP lúc nào?

- Phương án: (1) Sau smoke · (2) Sau audit
- Chọn: Sau smoke
- Lý do (tiêu chí chất lượng cuối): Duyệt bản dev; trả nợ ở pha 2 (ADR-0084).
- Đường lùi: Revert ADR-0084.

### D-523 · 2026-11-20T02:47:33+00:00 · Rút ngắn phản hồi từ sửa mã đến CI?

- Phương án: (1) Dựng lại sau mỗi lần sửa, chạy test theo tên · (2) Dùng watch lúc viết, giữ nghiệm thu bản đóng gói, xếp lớp test nặng trước và gom Gate một lượt
- Chọn: Dùng watch lúc viết, giữ nghiệm thu bản đóng gói, xếp lớp test nặng trước và gom Gate một lượt
- Lý do (tiêu chí chất lượng cuối): Giảm việc lặp, giữ tập test và thứ tự Gate theo PLAN.
- Đường lùi: Hoàn tác thay đổi của lượt này.

### D-524 · 2026-11-20T05:33:18+00:00 · Xếp việc và chuẩn bị ngữ cảnh cho đợt code kế như thế nào?

- Phương án: (1) Xếp toàn bộ theo tầng và đọc ngữ cảnh từng task · (2) So với lịch ưu tiên chuỗi phụ thuộc dài, chọn ít đợt hơn và lấy ngữ cảnh của đợt đầu trong một lệnh
- Chọn: So với lịch ưu tiên chuỗi phụ thuộc dài, chọn ít đợt hơn và lấy ngữ cảnh của đợt đầu trong một lệnh
- Lý do (tiêu chí chất lượng cuối): Phát lại 42 PLAN ở trần 4. Giữ lịch cũ khi hoà, kiểm giai đoạn trước khi xuất gói giao việc.
- Đường lùi: Hoàn tác thay đổi plan waves và dùng context --task.

### D-525 · 2026-11-20T10:04:23+00:00 · Khi nào chấp nhận kết quả nghiệm thu độc lập cho một SPEC?

- Phương án: (1) Chỉ đối chiếu tổng số test trong JUnit · (2) Khóa SPEC và tệp nghiệm thu trước khi viết mã, đối chiếu từng tệp với JUnit khi kiểm
- Chọn: Khóa SPEC và tệp nghiệm thu trước khi viết mã, đối chiếu từng tệp với JUnit khi kiểm
- Lý do (tiêu chí chất lượng cuối): Tổng số ca có thể giữ nguyên dù bỏ một tệp. Ánh xạ testcase về tệp trong phạm vi giúp phát hiện sai lệch và vẫn hỗ trợ classname ánh xạ duy nhất.
- Đường lùi: Hoàn tác tính năng opt-in và giữ kiểm commit độc lập hiện có.

### D-526 · 2026-11-20T10:21:45+00:00 · Quy mô và giai đoạn nào cho phép agent tự duyệt khi có bằng chứng máy?

- Phương án: (1) Chỉ duyệt MVP và quy mô S · (2) Hai trần độc lập, cấu hình phải được bật trên nhánh mặc định; M/L và giai đoạn 2/3 phải đủ bằng chứng
- Chọn: Hai trần độc lập, cấu hình phải được bật trên nhánh mặc định; M/L và giai đoạn 2/3 phải đủ bằng chứng
- Lý do (tiêu chí chất lượng cuối): Dự án chủ động tăng tốc ở giai đoạn đã sẵn sàng; mặc định giữ S và giai đoạn 1. L đòi thêm 14 ngày số đo thực.
- Đường lùi: Giảm các trần trên nhánh mặc định và đưa quyết định lại cho người phụ trách.

### D-527 · 2026-11-20T10:21:47+00:00 · Lúc nào adapter được thay đổi một môi trường đã được ủy quyền?

- Phương án: (1) Dùng receipt cũ và quyền được đọc khi bắt đầu · (2) Kiểm lại quyền tại thời điểm gọi lệnh, dùng đúng bytes đã thử, kiểm lại digest qua đích
- Chọn: Kiểm lại quyền tại thời điểm gọi lệnh, dùng đúng bytes đã thử, kiểm lại digest qua đích
- Lý do (tiêu chí chất lượng cuối): Quyền có thể thay đổi khi smoke và build chạy. Receipt phải chứng minh bản phục vụ thật. Mất quyền sau khi chạm đích thì ghi chưa rõ và dừng.
- Đường lùi: Tắt adapter và chẩn đoán phiên bản đang chạy bằng kênh vận hành của môi trường.

### D-529 · 2026-11-20T10:21:48+00:00 · Các MUST ở M/L yêu cầu con người được thực thi như thế nào?

- Phương án: (1) Yêu cầu cùng một lần xác nhận thủ công ở mọi mục · (2) Dùng một bảng 16 ID phân biệt ủy quyền gắn bằng chứng, trách nhiệm con người và kiểm tra tự động
- Chọn: Dùng một bảng 16 ID phân biệt ủy quyền gắn bằng chứng, trách nhiệm con người và kiểm tra tự động
- Lý do (tiêu chí chất lượng cuối): G7 và admin-plan đọc cùng bảng; phần việc còn cần người hiện rõ và điều kiện sẵn có của environment, CODEOWNERS vẫn có hiệu lực.
- Đường lùi: Đưa trần duyệt về mặc định và áp lại văn bản trước lần phân loại.

### D-530 · 2026-11-20T15:07:17+00:00 · F-144 có chặn tag major di động (v1, v1.2) không?

- Phương án: (1) Chặn cả tag major v<số>(.<số>)* · (2) Chỉ chặn vX.Y.Z kể cả hậu tố SemVer
- Chọn: Chỉ chặn vX.Y.Z kể cả hậu tố SemVer
- Lý do (tiêu chí chất lượng cuối): Dự án Action dời tag major mỗi bản, chặn ở guard là chặn oan; ruleset v* phía server vẫn giữ.
- Đường lùi: Mở RELEASE_VERSION_TAG sang v<số>(.<số>)* và đổi ca fixture.

### D-531 · 2026-11-20T16:16:56+00:00 · Agent duyệt giai đoạn 2/3 khi khoá chưa hiệu lực: sửa mã hay nới e2e?

- Phương án: (1) Nới assert e2e · (2) Kiểm khoá ở mọi giai đoạn, trước kiểm cây và trần
- Chọn: Kiểm khoá ở mọi giai đoạn, trước kiểm cây và trần
- Lý do (tiêu chí chất lượng cuối): S-507 ghi exit 2, chỉ người; PR đổi thứ tự mà không có quyết định. Siết lại là cách hiểu chặt hơn.
- Đường lùi: Chỉ kiểm ở giai đoạn 1 và nới assert e2e.

### D-532 · 2026-11-21T05:50:11+00:00 · #707 còn 2 lách có từ trước: vá tiếp hay merge?

- Phương án: (1) Vá vòng 6 · (2) Merge, ghi AUD-HAR-452/453 chấp nhận
- Chọn: Merge, ghi AUD-HAR-452/453 chấp nhận
- Lý do (tiêu chí chất lượng cuối): base cũng lọt, cùng họ D-332; #707 nhẹ hơn base = 0; hàng rào thật là ruleset tag v*.
- Đường lùi: Mở lại hai mục và vá.

### D-533 · 2026-11-21T08:44:47+00:00 · WF-REVIEW-007 (MUST) lệch ADR-0079: sửa câu chữ hay đổi mã?

- Phương án: (1) Sửa MUST cho khớp ADR-0079 · (2) Giữ MUST, đổi mã/ADR đòi review ở optional
- Chọn: Sửa MUST cho khớp ADR-0079
- Lý do (tiêu chí chất lượng cuối): ADR-0079 đã quyết hành vi; dự án siết bằng required.
- Đường lùi: Khôi phục câu MUST cũ

### D-534 · 2026-11-21T10:47:17+00:00 · AUD-HAR-454, AUD-CI-036: sửa hay chấp nhận có hạn?

- Phương án: (1) Sửa ngay · (2) Chấp nhận tới 2027-01-21
- Chọn: Chấp nhận tới 2027-01-21
- Lý do (tiêu chí chất lượng cuối): cần agent làm trái `pr next` hoặc fork đổi tên; an toàn; sửa đòi mã guard sát trần.
- Đường lùi: Mở lại và sửa

### D-535 · 2026-11-21T12:38:25+00:00 · BASE-REPO-006 chặn ký sau 15 phút kể từ VERSION: nới?

- Phương án: (1) Thêm điều kiện có docs/ops/GO-NO-GO-*-<VERSION>.md (glob neo hai đầu) · (2) Giữ, chủ repo tạo tag tay
- Chọn: Phương án (1)
- Lý do (tiêu chí chất lượng cuối): cửa sổ 15 phút ngắn hơn CI + review nên chữ ký ở PR sau không bao giờ được duyệt; GO-NO-GO vẫn chặn phát hành (`go_no_go`, `release-sign`).
- Đánh đổi chấp nhận: thiếu tag không còn bị BASE-REPO-006 báo khi đã có tệp GO-NO-GO (kể cả đã ký mà `release-tag.yml` hỏng); `go_no_go` và `release-check` vẫn đỏ/chờ. Có từ trước (AUD-HAR-460, chấp nhận tới 2027-01-21): BLUEPRINT.md tính là tài liệu nên đổi lệnh kiểm không sinh nợ review.
- Đường lùi: Bỏ điều kiện `git ls-files` khỏi lệnh kiểm BASE-REPO-006
