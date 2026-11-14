# ADR-0068: Định hướng xưởng phần mềm — lõi hiện có + gói sản phẩm có phiên bản + hợp đồng bằng chứng phát hành có kiểu

- **Trạng thái:** **Đã chấp nhận 2026-11-04** — chủ dự án trả lời bốn câu hỏi ở
  [`research/2026-11-04-software-factory-direction.md`](../../research/2026-11-04-software-factory-direction.md) §9:
  **1a · 2a hotel-manager · 3a · 4a** (tiền lệ ADR-0064: nháp cùng PR, chấp nhận cùng ngày; **D-353**). Bản nháp cùng ngày
  chỉ khác ở trạng thái và đoạn "Bốn câu hỏi" ở §Quyết định.
- **Trạng thái triển khai:** lát A đã làm 2026-11-05 trên nhánh, chưa merge (D-355,
  [`PLAN-factory-A.md`](../archive/autopilot/PLAN-factory-A.md) T-3675…3679: `report_result`, `<khoá>_report`, `release_artifacts`,
  `subject`/`promotion`, `schema: 3`; test `tests/test_release_contract.py`); evidence v2 của `loop record` giữ nguyên.
  Lát B–E làm 2026-11-05 trên nhánh, chưa merge (D-359, [`PLAN-factory-BE.md`](../archive/autopilot/PLAN-factory-BE.md)
  T-3685…3692): gói `framework/templates/packs/web-api-ts/` + workflow `pack-web-api.yml` (lát dọc, 5 ca sai cố ý);
  `install.py --pack` (fresh/brownfield/upgrade, kiểm trên bản clone hotel-manager); worker trong gói (tuyến API/worker);
  `docs/ops/registry.json` + `xt.py registry` + màn app. Còn: fixture payload host thật Codex/Gemini (cần CLI chạy bằng tài
  khoản của chủ dự án); PR nâng dự án đích (việc người). Ghi lúc chấp nhận: không thêm ID, không đổi mức, không đổi schema/CLI trong PR của ADR này. Về sau lát A–E cùng
  ADR-0069/0070 gộp một PR (#451) theo chủ dự án (D-358/D-359) — lệch Yếu tố 2 "mỗi lát một PR" (nợ AUD-HAR-221). Merge `13a8aa9` (2026-11-06): chữ "(đề xuất)" ở
  §Quyết định là chữ bản nháp được chấp nhận nguyên văn; mốc xét lại "lát A xong mà chưa có dự án đích deploy thật" đã tới
  — xét cùng mốc 2027-01-21.
- **Ngày:** 2026-11-04.
- **Nghiên cứu:** research cùng tên (đối chiếu X-Templates `e0ea0a6`/`9c03257` và stored `5d8f8a6` ngày 2026-11-04; nhật ký
  xác minh §10; điều chưa xác minh: trạng thái merge stored#131, stack dự án đích).
- **Liên quan (ràng buộc, không thay):** ADR-0001 (thư viện ID + compose), ADR-0008 (tự duyệt), ADR-0010 (phản hồi kéo về),
  ADR-0042/0062 §6 (`release-check`), ADR-0043/0050 + D-142 (đóng băng bề mặt 3.x, không tách `xt.py`), ADR-0058 (giai đoạn,
  `approve` chỉ người, `by` không phải chữ ký), ADR-0064 (harness đa host, mốc 4.0 2027-01-21), `QA-STRAT-024` (#436),
  `OPS-DEPLOY-001/005`, `WF-ENV-006`, `WF-REL-005`, `SEC-SUPPLY-013/014/033`, `BASE-GATE-014`, `LOOP-HARNESS-023`.

## Bối cảnh

Khung đã có vòng đời G0–G8, blueprint theo ID, vòng lặp có bằng chứng, `release-check`, sổ giai đoạn, harness đa host và
vòng phản hồi từ dự án đích. Điều chưa có: (1) một **gói sản phẩm** dựng được lát dọc từ repo sạch và nâng được ở dự án đã
cài; (2) **kết quả cổng có kiểu** — `_release_run` chỉ đọc exit code, `zero_tests_red` chỉ nhận `Ran 0 tests`, không hàng
nào đọc report/artifact/checksum; (3) **receipt triển khai** — khung ghi quyết định (`prod_switch`, GO-NO-GO §5, `stage
approve`) nhưng không đọc bản nào thực sự chạy ở đâu; ADR-0058 đã tách "GO của máy, nghiệm thu của người, quyền deploy, đã
deploy" thành bốn việc và chỉ làm hai việc đầu (ADR-0069 cho agent làm việc thứ hai khi dự án chọn, không đổi hai việc sau). stored (đợt 2026-11-04, 34 chuyên mục) ghép các mục thành chuỗi "nhu cầu →
quyết định → hợp đồng → thay đổi → kiểm chứng → bản phát hành → số đo thực địa" và tự ghi rằng các cổng đó là đề xuất, chưa
chạy ở đâu.

Câu hỏi: X-Templates có nên định vị là **bộ máy giao hàng có kiểm chứng** (xưởng) thay vì chỉ thư viện yêu cầu, và nếu có thì
bằng cách nào mà không đảo các quyết định 3.x đã chốt?

## Yếu tố quyết định

1. Đúng và an toàn: không báo xanh sai (0 test, scan pending, sai digest, ngoại lệ hết hạn phải chặn promote); quyền
   promote nằm ở CI/IAM của hệ đích, không ở lời agent (ADR-0058 phương án 3: repo một chủ không phân biệt người với agent).
2. Đường lùi: mỗi lát một PR; gói xoá được; trường cũ của evidence/`release-check` giữ nghĩa.
3. Đơn giản, bền: không tách `xt.py`, không nền tảng tập trung, không dependency mới cho CLI (D-142, ADR-0043/0050);
   tối đa một gói trong 3.x; registry là file.
4. Chi phí/tốc độ: tái dùng `install.py` manifest, `framework/templates/`, job `app-e2e`, `feedback aggregate`,
   `pr stats`/`loop stats`/`autonomy-bench` làm baseline.

## Các phương án đã cân nhắc

1. Giữ hiện trạng: mỗi đợt stored → research note → ID SHOULD; dự án tự nối cấu hình/bằng chứng.
2. Nền tảng tập trung quản agent/build/deploy nhiều dự án.
3. **Lõi hiện có + gói sản phẩm/adapter có phiên bản + registry file + hợp đồng bằng chứng có kiểu** (đề xuất).

## Quyết định (đề xuất)

Chọn **phương án 3**, năm lát theo research §7, thứ tự A → B → C → D → E, mỗi lát một PLAN riêng khi ADR này được chấp nhận:

- **A — Hợp đồng kết quả/phát hành có kiểu.** Evidence v3 **thêm trường** (schema, `artifacts[]`, `results[]` theo adapter),
  v2 vẫn hợp lệ; `release-check --json` thêm `promotion` và `subject`, **giữ** `go`/`verdict`/`human` và exit code ≥ 1 bản
  minor; adapter đầu: JUnit XML, SARIF, `pip-audit` JSON; fixture âm cho mọi ca ở research §6; không đổi `_release_run` cho
  khoá chưa khai adapter.
- **B — Gói Web/API nhiều tenant đầu tiên** tại `framework/templates/packs/<stack>/` (phiên bản theo `VERSION`), cài bằng
  `install.py --pack`; nghiệm thu = lát dọc research §5 chạy từ repo sạch trong CI, ca sai cố ý làm cổng đỏ.
- **C — Nâng một dự án đích** (ứng viên theo `docs/ops/TARGETS.md`, sau khi PR nâng 3.14 có kết luận): idempotent, giữ tùy
  biến, lộ drift, có rollback.
- **D — Tuyến API/worker + host thật** (Codex, Gemini trước; fixture thật `T-3642`…`T-3644`; công bố mức theo thang
  stored METHOD.md §2, "hỗ trợ" chỉ khi `checks-run`); gắn mốc 2027-01-21 của ADR-0064.
- **E — Registry nhiều sản phẩm** mở rộng `TARGETS.md` (core/gói/version/owner/release/ngoại lệ còn hạn) + trang đọc ở
  `xt.py app`; vòng học qua `feedback aggregate` với cùng ngưỡng ADR-0010.

Bốn câu hỏi chủ dự án đã chốt 2026-11-04 (D-353; phương án thay thế ở research §9):

1. **Nơi lưu gói (1a):** gói đầu tiên trong repo khung tại `framework/templates/packs/<stack>/`, phiên bản theo `VERSION`;
   chuyển repo riêng khi có ≥ 2 gói hoặc owner khác chủ khung. Gói không kéo dependency vào CLI stdlib.
2. **Stack và repo thử (2a):** stack của dự án đích **hotel-manager** — lát B (repo sạch) và lát C (brownfield) dùng chung
   một gói; stack cụ thể xác minh khi đọc repo lúc lập PLAN lát B (chưa đọc được trong phiên này); owner gói: chủ dự án.
3. **Schema bằng chứng (3a):** evidence v3 chỉ **thêm trường**, v2 vẫn hợp lệ; `release-check --json` thêm `promotion` và
   `subject`, giữ `go`/`verdict`/`human` và exit code ít nhất một bản minor; "đã duyệt" vẫn là `stage approve` (người, hoặc
   agent theo ADR-0069)/GO-NO-GO §5 — máy không tự nâng `pending_human` thành `approved`.
4. **Tuyến thứ hai và host (4a):** API/worker cùng stack với gói đầu, AI/data chờ dự án đích có nhu cầu và dữ liệu hợp lệ;
   host Codex và Gemini CLI trước (thứ tự ADR-0064), công bố "hỗ trợ" chỉ khi đạt `checks-run` với fixture payload thật.

### Hệ quả

- Tốt: xưởng dựng trên cơ chế sẵn có, không nền tảng mới; bằng chứng phát hành đọc được bằng máy; một gói chứng minh được
  "repo sạch → lát dọc" và "brownfield nâng được"; host khác Claude có mức hỗ trợ trung thực.
- Xấu / đánh đổi: thêm mã adapter và gói phải bảo trì (trần nhóm `scripts` còn ≈ 715 KB ngày 2026-11-04); gói phụ thuộc hệ
  sinh thái của một stack; lát C và D phụ thuộc chủ dự án (PR dự án đích, fixture host thật, dữ liệu thử).
- Không làm: nền tảng tập trung; đổi nghĩa `go`/`verdict`; cấp ID mới trong ADR này; tuyến AI/data trước khi có dự án đích
  có nhu cầu và dữ liệu hợp lệ.

### Xác nhận

- A: `release-check --json` có `promotion`; fixture âm (sai digest, report thiếu, 0 test, scan pending, approval hết hạn)
  → `promotion ≠ approved`; test cũ của `release-check`/`signoff-package` không đổi kỳ vọng.
- B: workflow CI dựng repo sạch từ gói và chạy lát dọc §5 xanh; ba ca sai cố ý (tenant chéo, migration lùi hỏng, contract
  đổi không tương thích) đỏ.
- C: `install.py --plan` trên dự án đích báo đúng file giữ/đè; nâng N → N+1 rồi `blueprint-status --run` xanh trở lại.
- D: `tests/fixtures/harness/<tool>/` có payload thật kèm bản + ngày; bảng mức hỗ trợ trong `harness/README.md`.
- E: `xt.py` đọc registry và liệt kê dự án lệch phiên bản gói/core.
- Mốc xét lại: 2027-01-21 (cùng ADR-0064/`LOOP-DESIGN-014`) hoặc khi lát A xong mà chưa có dự án đích nào deploy thật.

## Ưu / nhược từng phương án

### 1. Giữ hiện trạng
- Tốt: không thêm mã; stored tiếp tục là nguồn.
- Xấu: dự án đích vẫn tự nối bằng chứng; không đo được "promote đúng digest", "restore RPO/RTO".

### 2. Nền tảng tập trung
- Tốt: một trải nghiệm.
- Xấu: trái ADR-0010 (không token ghi chéo), tự host mặc định, D-142; quyền tập trung chưa có ai vận hành.

### 3. Lõi + gói + hợp đồng có kiểu (đề xuất)
- Tốt: tái dùng cơ chế; đường lùi từng lát; bằng chứng máy đọc.
- Trung lập: cần chủ dự án chốt stack/repo thử và cung cấp dữ liệu thử.
- Xấu: thêm bề mặt bảo trì; lát C/D chờ người.
