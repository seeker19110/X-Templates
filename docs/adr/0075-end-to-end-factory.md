# ADR-0075: Xưởng đầu-cuối — ý tưởng tới bản dev không cần người, song song theo file, mọi quy mô, thiết lập một lần sau bản dev

- **Trạng thái:** Đã chấp nhận 2026-11-11 — chủ dự án trả lời ba câu hỏi của phiên: *"1. song song nếu không chạm cùng
  file · 2. thiết lập sau khi lên bản dev · 3. ở mọi quy mô"*; phiên chính chốt cách máy hoá theo tiêu chí chất lượng cuối
  (ADR-0008) — **D-419**.
- **Trạng thái triển khai:** chưa bắt đầu — [`PLAN-factory-e2e.md`](../autopilot/PLAN-factory-e2e.md) (D-420); PR của ADR
  này chỉ có tài liệu, không đổi mã, khoá, ID hay mức.
- **Ngày:** 2026-11-11.
- **Nghiên cứu:** [`research/2026-11-11-factory-end-to-end.md`](../../research/2026-11-11-factory-end-to-end.md) (đọc repo
  ở `e1c74e6`; dữ kiện ngoài chưa tra — việc đầu của PLAN).
- **Thay một phần (có hiệu lực khi lát tương ứng có mã):** D-142 mục "không song song worktree" · ADR-0061 mặc định `self`
  và điều kiện "tăng số agent chỉ khi có số" · ADR-0074 điều kiện `scale: S` cùng dòng 20 BLOCKER (M/L) của mẫu GO-NO-GO ·
  ADR-0058/0069 giai đoạn 2/3 chỉ người.
- **Giữ:** `HARD_GATED_KEYS` và luật bất đối xứng (máy tự siết, nới qua PR người merge một lần); nhóm máy chặn của guard;
  tiền, dữ liệu người dùng thật, pháp nhân đứng tên qua `- grant:` và `loop defer`; các mục còn lại của D-142 (không tách
  `xt.py`, không merge queue, không reviewer LLM mọi PR, không thu nhỏ guard); một gói trong 3.x (ADR-0068); trần byte
  (ADR-0043/0050); `LOOP-ORCH-008` (trần cứng 5 mỗi đợt).
- **Đặc tả:** `docs/specs/SPEC-factory-*.md` (bảy file, D-422…D-424) — nhà của giao ước khoá, lệnh, sổ và scenario; ADR
  này chỉ giữ quyết định.
- **Đính chính 2026-11-11 (review #502 và review đặc tả; thân ADR bên dưới giữ nguyên văn đã chấp nhận):**
  - "Thay một phần" còn thiếu **ADR-0048 §Quyết định 1** — nhà của dòng 20 GO-NO-GO (M/L: người dùng thử, "không thay
    được bằng E2E"). ADR này thay đúng điểm đó ở M/L; mục C4 của research 2026-11-08 ("M/L giữ BLOCKER") vì vậy cũng
    đổi. Dòng trạng thái ADR-0048 đã ghi.
  - §Quyết định 4 viết "duyệt giai đoạn ở S/M/L": chủ dự án chỉ nói "ở mọi quy mô". Mở **giai đoạn 2/3** cho agent là
    cách phiên hiểu rộng (nối lát S10 của research 2026-11-08), không phải nguyên văn — giới hạn giai đoạn 1 không phụ
    thuộc quy mô. Chủ dự án không muốn thì bỏ F-142 của đặc tả scale.
  - Ký ở M/L dùng **khoá trần riêng** `release_signoff_scale` (mặc định S), không tái dùng `release_signoff: agent` —
    dự án đã bật quyền ở S không bị nới khi nâng khung.
  - §Hệ quả "còn ≈ 456 KB dưới trần" là so với trần cứng; cổng "2× mốc gần nhất" (ADR-0072) chỉ còn ≈ 119 KB.
  - §Các phương án "ADR-0068 lát C–E": lát B–E đã có mã (PLAN-factory-BE); phần còn lại của lộ trình cũ là fixture host
    thật và PR nâng dự án đích.
  - §Bối cảnh bỏ sót cơ chế đã có mà đặc tả dựng lên trên: `loop run` (vòng ngoài headless), `QA-STRAT-023` (test chấp
    nhận viết từ SPEC bởi ngữ cảnh khác người viết), khoá `acceptance`/`acceptance_report`, `preview_smoke`.
  - §Quyết định 6 "chữ ký chưa có thì không tag, không phân phối": đặc tả cài bằng tag do workflow có cổng tạo và ghi
    nguồn cài vào manifest, không chặn `install.py` theo `promotion` (trạng thái tức thời, sẽ làm đỏ mọi lần cài từ
    nhánh chính và CI).

## Bối cảnh

Khúc giữa của dây chuyền (PLAN → mã → PR → merge → `release-check`) đã tự động. Hai đầu hở: người vẫn tạo repo, cài
khung và mở phiên; và không có lệnh triển khai, receipt hay smoke nào — registry ghi cả 4 dự án đích `environments: []`,
`release: null`. Ở giữa, song song chỉ bật khi người lập PLAN ghi tay, agent chỉ ký phát hành ở quy mô S, và người viết
mã cũng là người viết kiểm thử nghiệm thu. Chủ dự án muốn: người chỉ nêu ý tưởng, ra sản phẩm triển khai được — nhanh,
tự động hoàn toàn, chất lượng — và đã trả lời ba câu hỏi mở.

## Yếu tố quyết định

1. Đúng và an toàn: bỏ một chốt người thì cơ chế máy bù phải có trước; không báo xanh sai; phiên không tự cấp quyền.
2. Đường lùi: mỗi năng lực một khoá hoặc một dòng PLAN; mỗi lát một PR.
3. Đơn giản, bền: dựng trên `xt.py`, `install.py`, gói và registry sẵn có; không nền tảng mới.
4. Trải nghiệm cuối: người đưa một câu ý tưởng, nhận một bản chạy và một danh sách việc làm một lần.
5. Tốc độ/chi phí: chỉ phá hoà.

## Các phương án đã cân nhắc

1. Giữ lộ trình cũ: ADR-0068 lát C–E và S1–S11 của research 2026-11-08, tuần tự, agent ký chỉ ở S.
2. Nền tảng điều phối tập trung (đã loại ở ADR-0068 phương án 2).
3. **Dây chuyền đầu-cuối trên lõi hiện có**, theo ba trả lời của chủ dự án (chọn).

## Quyết định

Chọn **phương án 3**.

1. **Đơn vị thành công:** một ý tưởng bằng chữ → **bản dev** có receipt, không câu hỏi nào cho người. Chỉ số chính: thời
   gian và chi phí từ ý tưởng tới bản dev; kèm thời gian chờ người và lỗi lọt sau merge.
2. **Bản dev** (cách hiểu của phiên, chủ dự án sửa nếu lệch): bản ứng viên có digest, chạy ở môi trường tự host không cần
   tài khoản hay khoá của chủ (container cục bộ hoặc runner CI), smoke xanh, receipt máy đọc (môi trường · digest · thời
   điểm · kết quả smoke). Không tiền, không dữ liệu người dùng thật.
3. **Song song theo file** (câu 1):
   - Hai việc chạy song song khi `files:` của chúng đã khai và đôi một không giao; thiếu `files:` → đứng riêng (như
     `plan waves` hiện nay). Thêm: diff thật của việc phải nằm trong `files:` đã khai — ra ngoài thì Gate đỏ.
   - Khi đợt có ≥ 2 việc đủ điều kiện, song song là mặc định, không cần người lập PLAN ghi tay.
   - File mọi PR cùng chạm (`PROGRESS.md`, `CHANGELOG.md`, sổ quyết định, sổ audit) chỉ do phiên điều phối ghi lúc tích
     hợp, hoặc ghi theo mảnh riêng từng PR — chọn ở PLAN.
   - Mỗi lát song song một worktree, một nhánh, một PR. Trần đợt giữ 4 (cứng 5) tới khi có số đo.
   - Giữa các dự án: mỗi repo một worker; giới hạn là trần chi phí.
   - Đo xung đột tích hợp và lỗi lọt; xấu hơn tuần tự thì lùi về `self` bằng một khoá.
4. **Mọi quy mô** (câu 3): agent ký phát hành và duyệt giai đoạn ở S/M/L khi khoá đã commit ở nhánh chính cho phép. Ở
   M/L, dòng "người đã dùng thử" được thay bằng hàng bằng chứng máy (nghiệm thu độc lập + receipt bản dev + diễn tập quay
   lui), ghi rõ "máy mô phỏng — chưa người dùng thật". Mục MUST của thư viện đang buộc người ở M/L được đối chiếu theo
   khoá, giữ ID.
5. **Thiết lập một lần sau bản dev** (câu 2): không việc người nào nằm trên đường tới bản dev. Khi receipt bản dev xanh,
   máy in **một** checklist (GitHub App/token, đích và khoá production, trần chi phí, khoá `HARD_GATED` cần bật, ruleset
   lệch); chủ làm một lần, sau đó đường production mở.
6. **Chất lượng bù cho chốt người đã bỏ**, merge **trước** phần nới: bộ nghiệm thu do agent khác người viết sinh từ spec và
   khoá bằng digest; triển khai đúng digest đã kiểm; smoke đỏ thì tự quay lui; chữ ký chưa có thì không tag, không phân
   phối.

### Hệ quả

- Tốt: dây chuyền kín từ ý tưởng tới bản chạy; việc người gom về một lần; song song có điều kiện máy kiểm thay cho lời
  khai; quy mô không còn là lý do chờ người.
- Xấu / đánh đổi: thêm mã vào nhóm `scripts` (còn ≈ 456 KB dưới trần, đo 2026-11-11); song song tốn token hơn; ở M/L
  "máy mô phỏng" không thay được người dùng thật — khoảng cách giữa "qua cổng" và "đúng ý định" chỉ thu hẹp, không mất.
- Khuyến nghị của phiên (không đổi quyết định): dự án có dữ liệu cá nhân thật hoặc thuộc ngành quản lý nên để khoá ký ở
  `human` cho tới khi có số lỗi lọt của chính dự án đó.
- Không làm: tự bật khoá `HARD_GATED`; cấp token admin cho agent; coi im lặng là duyệt; tách `xt.py`; gói thứ hai trong
  3.x (UI vào cùng gói).

### Xác nhận

- Bản dev: từ repo sạch, workflow của gói dựng bản dev, ghi receipt, ca sai cố ý (sai digest, smoke đỏ) làm cổng đỏ.
- Đầu vào: một lệnh từ thư mục trống ra repo có khung + gói, `doctor` sạch.
- Song song: việc ghi ra ngoài `files:` đã khai làm `loop record` đỏ; `loop stats` có số xung đột tích hợp.
- Mọi quy mô: `release-sign` ở blueprint M ký khi đủ hàng bằng chứng máy và từ chối khi thiếu; khoá vẫn trong
  `HARD_GATED_KEYS`.
- Thiết lập: `admin-plan` chỉ đọc, in đủ mục thiếu, không tự áp.
- Dây chuyền: hai báo cáo pilot (ý tưởng → bản dev; đủ dây chuyền) có thời gian, chi phí, số lần phải hỏi người.
- Mốc xét lại: 2027-01-21 (cùng ADR-0064/0068), hoặc khi pilot 1 có số.

## Ưu / nhược từng phương án

### 1. Giữ lộ trình cũ
- Tốt: không đổi quyết định nào.
- Xấu: không có bản chạy; người vẫn là đầu vào và đầu ra của dây chuyền; M/L luôn chờ người.

### 2. Nền tảng tập trung
- Tốt: một trải nghiệm.
- Xấu: trái ADR-0010 và mặc định tự host; quyền tập trung chưa ai vận hành.

### 3. Dây chuyền đầu-cuối trên lõi hiện có (chọn)
- Tốt: đúng yêu cầu chủ dự án; đường lùi từng khoá; tái dùng cơ chế.
- Xấu: nhiều lát; rủi ro chất lượng dồn vào bộ nghiệm thu độc lập — phải làm trước phần nới.
