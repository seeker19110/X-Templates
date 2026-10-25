# ADR-0046: `/autopilot` dừng ở "build xong" (pha build, không đòi hết MUST blueprint); `/complete` là nhà của pha harden — audit, nợ review, hoàn thiện, phát hành

- **Trạng thái:** Đã chấp nhận (chủ repo yêu cầu 2026-10-25: "/autopilot là pha build, code nhanh nhất có thể, loại bỏ tất cả
  các rào cản, phiên chính tự quyết định với mục tiêu chất lượng cao; thêm /complete mới audit, review, fix, refactor… hoàn
  thiện dự án"; phiên chính tự duyệt thiết kế theo tiêu chí chất lượng cuối — D-174); mục 5: `merge_hard_exceptions` của mẫu
  dự án đích đổi sang `auto` theo chủ repo 2026-10-25 (D-176, 3.24.0) — sàn còn lại giữ nguyên; mục 1 "dừng ở build xong" đổi
  thành vòng: đợt build xong → `/audit delta` → sửa/đợt kế, lặp tới khi hết việc và `/audit full` sạch, rồi **đề xuất** `/complete`
  (không tự chạy — chủ repo 2026-10-25, D-177/D-178)
- **Trạng thái triển khai:** Đã triển khai (PR #259 + PR cắt bản 3.23.0) — PLAN `docs/autopilot/PLAN-3.23.0-complete.md`: `scripts/xt.py`
  (`_verdict_blueprint` theo pha, chuỗi lý do `_with_dispatch`/`_release_phase`, `DOCTOR_SKILLS`), skill mới
  `.claude/skills/complete/SKILL.md`, skill `/autopilot` viết lại cho pha build, `tests/test_docs_budget.py` (`CAPS`),
  `tests/test_xt_core.py`, `tests/test_delivery_phase.py`, `tests/test_install.py`, `tests/test_doctor.py`, tài liệu (README mảng 11, `loop-design.md` bảng verdict, `lifecycle.md`,
  `audit.md`, mẫu PLAN/AGENTS, AGENTS.md, CLAUDE.md, README gốc), bản 3.23.0.
- **Ngày:** 2026-10-25
- **Làm rõ:** ADR-0031 (mục Hệ quả "Trước G7: đặt `harden` → audit delta → `release-check`" nay là nội dung của `/complete`),
  ADR-0033 (quyết định 1 "gom audit về trước G7" = gom về `/complete`), ADR-0037 (mục 3–4: chuyển `harden` chỉ khi lên
  production — việc của `/complete`; một chiều, skill không tự đổi pha), ADR-0041 (mục 2: phần harden của skill `/autopilot`
  chuyển sang `/complete`); ADR-0008 (tự duyệt), ADR-0009 (một phiên), ADR-0018/0040 (sàn an toàn — không đổi);
  nghiên cứu `research/2026-10-25-autopilot-build-complete-harden.md`.

## Bối cảnh

Khung đã có pha giao hàng ở máy: `delivery_phase: build` bỏ reviewer (ADR-0037), audit theo mốc (ADR-0033), sàn Gate M/L,
cổng đầy đủ trước push và trần 150 dòng (ADR-0041), nới guard cho việc cục bộ (ADR-0040). Nhưng skill `/autopilot` vẫn là
**một** checklist cho cả hai pha: mục Kết thúc đòi "PR đặt `delivery_phase: harden` → audit delta → `release-check` →
`GO-NO-GO.md`" trong cùng lần chạy, và các bước 1, 6 rẽ nhánh build/harden. Đo tại HEAD `c054540` (2026-10-25):

- Rào cản **máy** còn lại ở pha build chỉ còn một: verdict `done` của vòng (`_verdict_blueprint`, `scripts/xt.py:1789–1817`)
  đòi blueprint 0 MUST mở, không rẽ theo pha; `compose --profile web-app --scale M` sinh 473 MUST mở ngay sau khi ghép (S 70,
  L 1 146); MUST `Miễn` cần `Duyệt:` của người (`LOOP-STOP-024`). Vòng build không thể `done` nếu không làm hết hoặc
  `loop defer` hàng trăm mục — tức `done` đang mang tiêu chí G7, không phải "build xong".
- Stop hook (`hook_stop`, 2851–2880) **không** gọi `release-check`; khối "harden → audit → release-check → GO-NO-GO" chỉ do
  văn bản đòi (skill dòng 30–31, README mảng 11 bước 16, `lifecycle.md` quy tắc 6). Mọi chốt G7 nằm trong `release_check`
  (8398–8427), độc lập với verdict của vòng.
- Chuỗi G0–G4 đầy đủ (PROJECT.md, researcher + ADR stack, SPEC-*.md, thiết kế) do skill đòi ở mọi quy mô; máy chỉ đọc
  PLAN + `xt.yaml` + bằng chứng.
- Ràng buộc: trần byte ADR-0043 (`AGENTS.md` dư 6 B, `framework/templates/AGENTS.md` dư 4 B, skill `/autopilot` dư 23 B,
  README mảng 11 dư 329 B — tại `c054540`; sau khi `main` lên 3.22.1 còn dư 2 B và 288 B); hai module 11 đã đủ 4 MUST; không tên model trong artefact; repo khung luôn `harden` (D-136).

## Phương án đã xét

1. **Giữ một skill, chỉ cắt mục Kết thúc.** Rẻ nhất về byte; nhưng `done` vẫn đòi 0 MUST mở (rào cản máy không gỡ), skill
   vẫn rẽ nhánh hai pha, và harden không có nhà — người dùng không biết "hoàn thiện" bắt đầu ở đâu.
2. **Hai skill + bỏ `--blueprint` ở `loop init` pha build** (0 code, đường có sẵn: 1792–1797). Gỡ rào cản `done`; nhưng mất
   `scope` khoá quy mô, `_scope_drift`, chạy lại `— Kiểm:` ở `verify --all` và `loop defer` theo MUST — tức mất lưới an toàn
   có sẵn để đổi lấy 0 dòng mã.
3. **(Chọn) Hai skill + verdict `done` theo pha trong `_verdict_blueprint` + Pha 1 mức S ở build.** Thêm ~15 dòng mã có test;
   giữ `--blueprint` và mọi kiểm khác; `/complete` là nhà của harden; sàn an toàn không đổi.
4. **Đảo ngược: `/autopilot` tự đặt lại `build` cho đợt mới ở dự án đã phát hành.** Nhanh hơn cho đợt sau; trái ADR-0037 một
   chiều và tiêu chí 1 (dự án có người dùng thật không được merge không review theo mặc định). Loại.

## Quyết định

1. **`/autopilot` là checklist pha build và dừng ở "build xong".** `done` của máy = mọi task có bằng chứng xanh + `loop verify
   --all` khớp cây (máy không kiểm PR; PR của lát merge theo `pr next`/`merge-watch` ở bước 6 của skill). Mục Kết thúc không còn `release-check`/`GO-NO-GO`; báo cáo cuối ghi số
   MUST blueprint mở, nợ review và dòng bắt buộc "chưa phát hành — gõ `/complete`". Skill **tôn trọng pha trong `xt.yaml`**:
   ở `harden` (repo khung, dự án đã phát hành) chạy luật harden của README mảng 11 — một dòng, không rẽ nhánh dài.
2. **Pha build dùng đầu ra mức S cho G0–G4** (nhà: `lifecycle.md` quy tắc 6): đọc repo → `compose` (không tick) → PLAN có Gate
   máy + Given/When/Then và ca biên ngắn trong dòng task hoặc là chính test; `PROJECT.md`/SPEC riêng/ADR stack/researcher
   chỉ khi thêm phụ thuộc, dịch vụ, luật ngành hoặc nghiệp vụ không tầm thường; thiết kế chỉ phần code cần (ADR-0041). Phần
   đầy đủ theo quy mô thật (C4, `API-CONTRACT.md`, `THREAT-MODEL.md`, SPEC đủ ca biên) trả ở `/complete`.
3. **Verdict `done` ở pha build không đòi blueprint 0 MUST mở.** `_verdict_blueprint`: khi `_phase_in_tree(base) == "build"` và
   còn `open_must` → `done` kèm `open_must: N` và lý do "còn N MUST blueprint mở — trả ở `/complete`"; `bad_waivers`/`bad_lines`
   vẫn `continue`, `_scope_drift` vẫn `verify`; `_still_open`/`_with_pending_human` giữ (MUST đã `loop defer` vẫn ra
   `done-pending-human`); `final_check` (`loop verify --all`) giữ. Chuỗi lý do ở `_with_dispatch` và `_release_phase` trỏ
   `/complete`; giá trị `milestone_audit: g7` giữ nguyên tên.
4. **`/complete` là nhà của pha harden** (skill mới, ≤ 6 144 B, có trần trong `CAPS`; `DOCTOR_SKILLS` thêm `complete`): (0) tên
   phiên, `doctor --fix`, đọc pha; khuyến nghị phiên mới sau `/handover` · (1) chưa `harden` → PR đặt `delivery_phase: harden`,
   khai khoá sàn M/L và `attack`/`perf` → merge (PR đụng `xt.yaml` luôn tính harden — D-137) · (2) `/audit` full lần đầu /
   delta bản sau; nợ review = audit delta chia theo PR/lát đã merge kể từ SHA quét, mỗi cụm nhỏ cho reviewer năng lực cao hơn,
   xác minh đối kháng 🔴/🟠 · (3) gieo `docs/autopilot/PLAN-harden-<ngày>.md`: 🔴/🟠 (test tái hiện đỏ trước), MUST mở
   (`blueprint-status --strict --json`), sàn (`xt.py floor`), thiết kế đầy đủ, refactor từ nhóm CODE/ARCH, perf theo
   `optimization-loop.md`, hàng FAIL của `release-check --json`; tự duyệt D-NNN · (4) vòng lặp như `/autopilot` Pha 2 với luật
   harden (`milestone_audit: now`, PR ≤ 150 dòng, `dev-task.sh gate` trước push, reviewer khi `pr next` đòi, reviewer-alt rà
   diff ngoại lệ cứng trước PR) · (5) `loop verify --all` → `release-check` không NO-GO → `GO-NO-GO.md`, `loop stats`,
   `feedback collect`. Sau phát hành dự án **giữ `harden`** (ADR-0037); dựng nhanh đợt lớn mới là quyết định của chủ dự án
   qua PR sửa `xt.yaml`.
5. **"Loại bỏ tất cả rào cản" = rào cản quy trình, không phải sàn an toàn.** Giữ nguyên ở mọi pha: guard chặn hành động
   không đảo ngược/đối ngoại/bí mật/tắt hook/ghi tay `.autopilot/`/giả dấu review/ghi công AI (ADR-0018/0040), điểm dừng tiền
   thật/dữ liệu thật/khoá thật (`loop defer`), Gate máy mỗi task qua `loop record`, cổng commit `gate-fast` (ADR-0011), CI xanh
   và merge ghim head (ADR-0036), `loop verify --all` trước khi dừng (`LOOP-DESIGN-022`), `release-check` FAIL `phase` ở build,
   `LOOP-STOP-024` (MUST `Miễn` cần người), `merge_hard_exceptions: human` ở mẫu dự án đích (chủ dự án tự đặt `auto`, ADR-0020).
   Bị chặn là kết luận (`LOOP-STOP-025`). Skill ghi một dòng "Sàn không bỏ" trỏ `stop-points-and-escalation.md` §Điểm dừng.

## Lý do

- Tiêu chí 1 (đúng và an toàn): mọi chốt phát hành ở máy (`release_check`) không đổi và không phụ thuộc verdict của vòng;
  gỡ rào cản `done` chỉ dời **thời điểm** đòi MUST từ cuối G6 sang G7 — đúng tinh thần ADR-0029/0031 "cùng tiêu chí cuối,
  khác thời điểm kiểm". Sàn an toàn giữ nguyên.
- Tiêu chí 2 (đường lùi): revert PR mã trả verdict về như cũ; đặt `harden` trả lại mọi hàng rào ở PR kế; skill cũ còn ở
  `.xtemplates-new` khi dự án đích đã sửa.
- Tiêu chí 3 (bền, đơn giản): một hàm rẽ theo pha có test; không lệnh/hook/ID mới; `/complete` chỉ nối lệnh có sẵn (một chủ
  đề một nhà: audit ở `/audit`, luật làn ở `LOOP-STOP-022`, G7 ở `release-check`).
- Tiêu chí 4 (trải nghiệm): người dùng có điểm dừng tự nhiên và biết gõ gì tiếp; `/complete` lặp lại được mỗi bản phát hành.
- Tiêu chí 5: tăng tốc **chưa đo** — ghi là ước lượng; phép đo ở `research` §10.

## Hệ quả

- Tốt: vòng build không kẹt ở MUST tài liệu/a11y/runbook; harden có nhà và checklist; không hạ sàn phát hành ở mức máy.
- Xấu / đánh đổi chấp nhận: nhánh chính ở build có thể lâu hơn ở "chất lượng build" (ADR-0037 đã chấp nhận); không có máy
  nào buộc dự án đích chạy `release-check` trước deploy ngoài FAIL `phase` khi được gọi — đỡ bằng lý do `done` và báo cáo
  cuối; pha cho verdict đọc cây làm việc còn guard/merge đọc cả nhánh đích (bất đối xứng có sẵn từ ADR-0041 — chốt thật là
  `release-check` và merge); MUST sàn bảo mật/cấu hình phụ thuộc PLAN build có task dựng nền (máy chưa có khái niệm "MUST sàn").
- **Nợ ghi rõ:** job CI theo tag chạy `release-check` ở mẫu dự án đích (chưa có điểm móc "deploy", ADR-0042); định nghĩa máy
  đọc "MUST sàn" nếu số đo cho thấy MUST bảo mật bị bỏ quên ở build; `release-check --skip-run` nếu đo thấy chậm ở M/L;
  README gốc §Quyết định thiết kế còn thiếu ADR-0037…0045 (bổ sung cùng lát tài liệu).
- Dự án đích: chạy lại `install.py` (skill `/complete` mới, `/autopilot` đổi, `xt.py` đổi); dự án đã sửa `autopilot/SKILL.md`
  nhận bản mới ở `.xtemplates-new` và gộp tay.

## Đường lùi

Revert PR mã (verdict về như cũ) và PR skill; ADR này đổi "Bị thay bởi ADR-NNNN". Dự án đích đặt `delivery_phase: harden`
để trả lại hành vi cũ ngay ở PR kế mà không cần nâng khung.

## Xác nhận

- `python3 -m unittest tests.test_xt_core tests.test_delivery_phase` xanh: pha build + MUST mở → `done` kèm `open_must`;
  harden/vắng/giá trị lạ → `continue` như cũ; build + `bad_waivers` → `continue`; build + MUST đã defer → `done-pending-human`.
- `python3 scripts/xt.py doctor` liệt kê thiếu `skills/complete/SKILL.md` khi xoá file; `tests/test_install.py` kiểm skill
  được cài; `tests/test_docs_budget.py` có trần cho `.claude/skills/complete/SKILL.md`.
- `grep -c "release-check\|GO-NO-GO" .claude/skills/autopilot/SKILL.md` = 0; `grep -c "/complete" AGENTS.md
  framework/templates/AGENTS.md CLAUDE.md framework/11-autonomous-loop/README.md framework/00-method/lifecycle.md` ≥ 1 mỗi file.
- Không tên model/URL phiên trong diff (guard `ai_attribution` ở commit; đọc lại chữ mới).
