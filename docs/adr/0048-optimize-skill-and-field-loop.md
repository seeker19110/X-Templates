# ADR-0048: Skill `/optimize` chỉ cho ngân sách đang đỏ; số production vào qua file; người xác nhận một lần ở GO/NO-GO

- **Trạng thái:** Đã chấp nhận (chủ repo đề xuất dòng chảy 2026-10-25: "/autopilot → /complete (con người xác nhận spec,
  UX, bảo mật; trả nợ review) → /optimize (chỉ các ngân sách bị vi phạm, có đo) → release-check + con người ký GO/NO-GO →
  production → quan sát dữ liệu thật → /optimize dựa trên số liệu production → lại qua release-check và ký"; chốt phương án B
  — D-180; phiên chính tự duyệt thiết kế theo tiêu chí chất lượng cuối, ADR-0008)
- **Trạng thái triển khai:** Đã triển khai — PLAN-3.25 (`docs/autopilot/PLAN-3.25-optimize.md`), bản 3.25.0: skill
  `.claude/skills/optimize/SKILL.md`, `DOCTOR_SKILLS`, `LOOP-OPT-016`, `LOOP-OPT-005` MUST@M / `LOOP-OPT-004` MUST@L (D-181), mẫu
  GO-NO-GO dòng 20 + §2c, `lifecycle.md`, `/complete`, README gốc; test `tests/test_docs_budget.py`, `test_doctor.py`, `test_install.py`.
- **Ngày:** 2026-10-25
- **Thay một phần:** ADR-0046 mục 4 (3)(f) (hiệu năng trong PLAN-harden → gieo task theo `optimization-loop.md`, `/optimize`
  là skill riêng sau `done`) và (5) (bản chỉ tối ưu nghiệm thu delta).
- **Làm rõ:** ADR-0004 (trần 4 MUST@M mỗi module — `validate`), ADR-0046 (`/autopilot` build, `/complete` harden), ADR-0047 (vòng đợt build), ADR-0042 (`release-check` hàng
  `attack`/`perf`), ADR-0029 (G7 máy đọc), ADR-0008 (phiên chính tự duyệt), `framework/11-autonomous-loop/optimization-loop.md`
  (vòng tối ưu, `xt.py perf`), `LOOP-DESIGN-019` (vòng bảo trì theo ngưỡng tất định), `XC-PERF-007`/`OPS-SLO-*` (số field).

## Bối cảnh

Khung 3.24.0 đã có `/autopilot` (G5–G6) → `/complete` (G7) → `release-check` + `GO-NO-GO.md` người ký. Đối chiếu dòng chảy
chủ repo đề xuất với khung (đo tại `e10e3c3`):

1. "Con người xác nhận spec, UX, bảo mật" **trong** `/complete`: khung không có điểm chờ người ở đó — `/complete` tự duyệt
   PLAN-harden (ADR-0008) và chỉ có chữ ký ở `GO-NO-GO.md` (cột "Người đã đọc" từng dòng, mục 5). Mẫu GO-NO-GO chưa có dòng
   nào đòi người **dùng thử luồng chính** và đọc SPEC/threat model — "UX" chỉ còn a11y (dòng 13).
2. Tối ưu: `optimization-loop.md` đã có vòng đo → profile → một thay đổi → máy quyết (`LOOP-OPT-001…015`, `xt.py perf
   sample/compare/guard`), `release-check` có hàng `perf` (ADR-0042), `/complete` bước 3(f) nhắc một dòng "chỉ khi có số". Không
   có skill: không chạy lại riêng được sau phát hành; chưa nói rõ **nguồn** "ngân sách bị vi phạm".
3. Sau production: `XC-PERF-007` (RUM/OTel p95, MUST@L), `OPS-SLO-001…` (`docs/ops/SLO.md`), `LOOP-DESIGN-019` (ngưỡng tất
   định → task; quyền agent theo bậc) — nhưng không có **định dạng số field** mà máy/skill đọc được, và điểm dừng chỉ nói
   "dữ liệu người dùng thật", chưa nói agent **không** được tự kéo số từ production.
4. Bản phát hành chỉ tối ưu vẫn phải ký lại 20 dòng GO-NO-GO.

## Phương án đã xét

- **A — chỉ tài liệu** (ánh xạ vòng đời + dòng GO-NO-GO): rẻ, nhưng `/optimize` vẫn là một dòng trong `/complete`, không chạy
  lại được ở G8. Loại.
- **B — A + skill `/optimize` + định dạng số field qua file + nghiệm thu delta + nâng `LOOP-OPT-005`** (chọn).
- **C — B + `xt.py field check`** so ngưỡng theo bậc `LOOP-DESIGN-019`: chỉ đáng khi có dự án đích có SLO 7 ngày thật — chưa
  có (TARGETS). Hoãn; không viết máy cho số chưa tồn tại (`LOOP-OPT-001`).
- **Cổng chờ người bên trong `/complete`**: phá "một phiên tới khi xong" (ADR-0009) và nhân đôi điểm ký. Loại.
- **`xt.py` kéo metric từ Prometheus/Grafana**: cấp quyền production cho agent (tiêu chí 1); `LOOP-DESIGN-019` đã chọn script
  tất định so ngưỡng, `loop-design.md` bảng "không làm" loại model đọc log/metric liên tục. Loại.

## Quyết định

1. **Người xác nhận một lần, ở GO/NO-GO.** `/complete` vẫn tự duyệt và chạy tới `release-check`; đầu ra là gói nghiệm thu
   (SPEC ca biên, bằng chứng UI "đã đo" `LOOP-DESIGN-021`, `THREAT-MODEL.md`, bảng nợ review đã trả). Mẫu `GO-NO-GO.md` thêm
   dòng 20 BLOCKER (M/L; S: SHOULD) "Người đã dùng thử luồng chính và đọc SPEC + threat model (tên · ngày)" — máy không điền.
2. **Skill `/optimize`** (`.claude/skills/optimize/SKILL.md`, ≤ 6 144 B, `DOCTOR_SKILLS` đòi): đầu vào **chỉ** là ngân sách
   đang đỏ có số — hàng `perf` FAIL của `release-check --json` (sàn `floor` không có khoá hiệu năng — review #263) hoặc file số field (mục 3); mỗi ngân sách
   một task trong `docs/autopilot/PLAN-opt-<ngày>.md`, Gate theo `optimization-loop.md` (script Gate và `xt.py` lấy từ commit
   gốc, `perf guard` khoá bộ đo, `perf compare` quyết); chạy luật harden (`/complete` bước 4); dừng khi đạt mục tiêu; đổi hành
   vi đi PR riêng (`LOOP-OPT-014`). Không phải pha mới: `delivery_phase` giữ `harden`. **Chỉ chạy khi không có vòng sống**
   (`LOOP-HARNESS-024`): sau `done` của `/complete` bước 5, hoặc độc lập ở G8; đang ở `/complete` bước 4 mà `perf` đỏ →
   gieo task hiệu năng vào PLAN-harden theo cùng luật `optimization-loop.md` (bước 3(f)), không gọi `/optimize` (review #263).
3. **Số production vào qua file, không qua quyền.** `docs/ops/FIELD-<YYYY-MM-DD>.json` (định dạng ở `optimization-loop.md`
   §Số field: chỉ số, phân vị, cửa sổ, nguồn, người xuất, ngày) do người hoặc job CI xuất từ dashboard; `/optimize --field`
   chỉ nhận file này và coi nội dung là **dữ liệu, không phải chỉ thị**. Agent không được cấp khoá đọc production cho việc tối
   ưu (`stop-points-and-escalation.md` hàng "Dữ liệu người dùng thật"). Kích hoạt theo `LOOP-DESIGN-019` (ngưỡng tất định →
   task), không để model đọc log tìm việc. Mục mới `LOOP-OPT-016` (SHOULD).
4. **Nghiệm thu delta.** Bản phát hành chỉ tối ưu — diff **không chạm manifest/lockfile/migration/schema/hạ tầng** (kiểm bằng `git diff --stat`;
   `CREATE INDEX` cũng là migration cần đường lùi — dòng 8),
   không đổi hành vi, `PERF-LOG.md` có dòng giữ — dùng `GO-NO-GO.md` chế độ delta: dòng 1, 2, 4, 5 (bí mật, phụ thuộc — không có
   hàng tương ứng ở `release-check`), 12, 20 + §2b (bằng chứng chưa chứng minh: lab đo, field chưa) + bảng trước/sau từ
   `PERF-LOG.md` + mục 1; người vẫn ký mục 5. `release-check` chạy như thường. Chạm mục nào ở trên, thêm cache/lưu tạm dữ liệu cá nhân (dòng 11 DPIA/PII) hoặc
   đổi hành vi → bảng đầy đủ (review #263).
5. **`LOOP-OPT-005` MUST@L → MUST@M**: tối ưu là việc agent dễ gian lận nhất (METR 2025-06-05: 30 % lượt có hack); dự án M đủ
   lớn để cần reviewer năng lực cao hơn trả lời từng ⚠ của `perf guard`. Trần 4 MUST hiệu lực ở M mỗi module (`validate`,
   ADR-0004) → `LOOP-OPT-004` (một giả thuyết/một thay đổi — kỷ luật quy trình, không tạo kết quả giả) MUST@M → MUST@L
   (D-181). Giữ ID, đổi mức — ghi CHANGELOG mục checklist.
6. **Vòng đời có tên** (`lifecycle.md` §Ánh xạ): G5–G6 `/autopilot` → G7 `/complete` (`perf` đỏ → task hiệu năng; `/optimize` sau `done`) →
   `release-check` + ký → G8 vận hành → số field (file) → `/optimize --field` → `release-check` + ký delta.

## Hệ quả

- Dự án M/L phải có người dùng thử luồng chính trước GO; không thay được bằng E2E.
- `/optimize` không chạy khi không có số đỏ — đúng `LOOP-OPT-001`; muốn tối ưu "cho chắc" phải đặt ngân sách trước.
- Số field là file commit trong repo: có thể cũ hoặc sai; `LOOP-OPT-016` đòi ngày và nguồn, skill từ chối file > 30 ngày.
- Chưa có máy đọc field (C); khi dự án đích có SLO thật thì mở ADR mới.
- Nợ: README mảng 11 bước 17 (Pha 3) chưa nhắc `/optimize`/số field — file đúng trần 12 288 B; sửa cùng byte ở lần cắt chữ kế.

## Đường lùi

Xoá skill và bỏ `optimize` khỏi `DOCTOR_SKILLS`; `LOOP-OPT-005` về MUST@L; bỏ dòng mới ở mẫu GO-NO-GO; mục `LOOP-OPT-016`
→ MAY "Ngừng dùng". Mỗi bước là một commit đảo ngược được.

## Xác nhận

`tests/test_docs_budget.py` (trần skill), `tests/test_doctor.py`/`tests/test_install.py` (skill bắt buộc), `xt.py validate`,
`check-links`; review theo `pr next` ở pha harden; tag `v3.25.0` tự tạo khi `VERSION` đổi trên `main` (ADR-0047).
