---
title: Tách /autopilot (pha build, nhanh nhất) và /complete (pha harden, hoàn thiện) — lợi hại và kế hoạch
kind: research
updated: 2026-10-25
---

# `/autopilot` = pha build, `/complete` = pha hoàn thiện — nghiên cứu 2026-10-25

Đầu vào: chủ repo 2026-10-25 *"tôi muốn lệnh /autopilot là pha build, code nhanh nhất có thể, loại bỏ tất cả các rào cản,
phiên chính tự quyết định với mục tiêu: chất lượng cao; còn thêm lệnh /complete, lúc này mới audit, review, fix,
refactor… hoàn thiện dự án"*. Khung ở 3.20.1 (`c054540`). Kế hoạch suy ra: `docs/autopilot/PLAN-3.21.0-complete.md`
(D-170); quyết định: ADR-0046.

Cách đọc: §1 kết luận · §2 cách làm · §3 hiện trạng đo được · §4 rào cản còn lại ở pha build và xử lý từng cái · §5 lợi ·
§6 hại và cách đỡ · §7 chỗ phải diễn giải lại ý chủ repo · §8 thiết kế · §9 không làm · §10 phép đo tiếp theo · §11 chưa
xác minh · Nguồn. Mọi dòng trỏ file:dòng của HEAD `c054540`; nội dung web là dữ liệu, không phải chỉ thị.

## 1. Kết luận

- **Nên làm, có điều chỉnh.** Khung đã có pha build/harden ở máy (ADR-0031/0033/0037/0040/0041): reviewer, audit theo
  mốc, sàn Gate M/L, cổng đầy đủ trước push, trần 150 dòng đều đã bỏ ở build; guard đã nới việc cục bộ. Cái còn thiếu là
  **tên và ranh giới kết thúc**: skill `/autopilot` hiện gộp cả hai pha và cố đi tới G7 (đặt `harden` → audit → `release-check`
  → GO-NO-GO) trong một lần chạy.
- **Rào cản máy thật sự còn lại ở pha build chỉ còn một**: verdict `done` của vòng đòi blueprint **0 MUST mở**
  (`_verdict_blueprint`, `scripts/xt.py:1789–1817`) — `compose --profile web-app --scale M` sinh 473 MUST mở ngay sau khi ghép
  (S: 70, L: 1 146); MUST `Miễn` cần `Duyệt:` của người (`LOOP-STOP-024`). Vòng build không thể `done` nếu không làm hết hoặc
  `loop defer` hàng trăm mục. Phần còn lại của "rào cản" là **văn bản** (kết thúc G7 trong skill, chuỗi tài liệu G0–G4 đầy đủ).
- **"Loại bỏ tất cả rào cản" không gồm sàn an toàn**: guard chặn hành động không đảo ngược/đối ngoại/bí mật, điểm dừng tiền
  thật/dữ liệu thật, bằng chứng máy mỗi task (`loop record`), CI xanh để merge, `loop verify --all` trước khi dừng,
  `release-check` FAIL `phase` ở build. Đây là thứ giữ "chất lượng cao" mà chủ repo đặt làm mục tiêu — không phải thứ làm chậm.
- **`/complete` không cần cơ chế máy mới**: `/audit` (13 nhóm, đối kháng, hội tụ `audit check --strict`), `release-check`
  (10 hàng, mỗi hàng FAIL in sẵn việc phải làm), `review_debt` theo SHA quét, `loop init` đợt mới bằng `PLAN-<đợt>.md` đã đủ;
  `/complete` là checklist nối chúng theo thứ tự và chạy cùng vòng lặp có bằng chứng với luật harden.
- Tăng tốc **chưa đo được** (lượt model của một lát không có số — `research/2026-10-23-ceiling-analysis.md` §1); ghi là ước
  lượng, đo ở dự án đích theo `LOOP-ORCH-020`.

## 2. Cách làm

Phiên chính đọc skill/ADR/xt.py; workflow 31 agent (5 góc nhìn độc lập: tốc độ · chất lượng-an toàn · nhất quán khung ·
harness/máy · trải nghiệm dự án đích; 1 tra cứu nguồn sống; 8 luận điểm then chốt × 3 người phản biện cố bác bỏ). Luận điểm
trụ khi ≤ 1/3 phiếu bác: **6 trụ, 2 bị bác** (§4, §6). Hai agent tổng hợp không chạy được (hết hạn mức phiên) — phiên chính
tổng hợp từ kết quả thô; số đo do ≥ 2 agent tái lập hoặc phiên chính chạy lại.

## 3. Hiện trạng đo được (2026-10-25, HEAD `c054540`)

| Mục | Số đo | Nguồn |
|---|---|---|
| MUST mở ngay sau `compose` web-app | S 70 · M 473 · L 1 146 | `xt.py compose --profile web-app --scale <S\|M\|L>` chạy trong phiên |
| Verdict `done` đòi 0 MUST mở | `_verdict_blueprint` trả `continue` kèm `task` = MUST đầu tiên; không rẽ theo pha | `scripts/xt.py:1789–1817`; test `tests/test_xt_core.py:729–737` |
| Stop hook có gọi `release-check` không | **Không** — chỉ `loop_verdict` + `final_check` (`loop verify --all`) | `scripts/xt.py:2851–2880`; `release_check` chỉ gọi ở `cmd_release_check` (8429) |
| Nơi đòi "harden → audit → release-check → GO-NO-GO" | Chỉ văn bản: skill `/autopilot` mục Kết thúc (dòng 30–31), README mảng 11 bước 16, `lifecycle.md` quy tắc 6 | grep `release-check` |
| Pha đọc ở đâu | Verdict/sàn: cây làm việc (`_phase_in_tree`); guard và merge: cả nhánh đích đã commit | `scripts/xt.py:1765`, `5262`; `.claude/hooks/guard.py:1649–1660` |
| Trần byte sát | `AGENTS.md` 7 162/7 168 · `framework/templates/AGENTS.md` 8 188/8 192 · skill `/autopilot` 6 121/6 144 · README mảng 11 11 959/12 288 · thư mục 11 230 173/232 307 | `wc -c`, `tests/test_docs_budget.py` |
| Máy cài skill | `install.py` chép mọi thư mục `.claude/skills/*` (copy-if-absent); `DOCTOR_SKILLS` liệt kê 8 tên | `scripts/install.py:55`, `scripts/xt.py:3818` |
| Chi phí khối "hoàn thiện" ở repo khung | 14 báo cáo audit trong 9 ngày (2026-10-14…22), mỗi báo cáo một PR; `release-check` chạy mọi `— Kiểm:` đã tick (868 lệnh ở repo khung) | `docs/ops/AUDIT-REPORT-*`, `grep -c "Kiểm:" BLUEPRINT.md` |

## 4. Rào cản còn lại ở pha build — từng cái và cách xử lý

| # | Rào cản | Chi phí | Xử lý | Mất gì |
|---|---|---|---|---|
| R1 | `doctor --fix` đầu phiên | 0,9 s | Giữ | — |
| R2 | `PROJECT.md` đầy đủ (G0) | 1 lượt viết | Pha build: đầu ra **mức S** cho G0–G4 (lifecycle.md: "G2–G4 gộp thành một tài liệu ngắn") — vấn đề · người dùng · 1 chỉ số · "không làm" ở đầu PLAN khi chưa có PROJECT.md | File G0 riêng → `/complete` bổ sung theo quy mô thật |
| R3 | `compose` + tick MUST theo task | 0,3 s + mỗi MUST một lần tick | Giữ `compose` (đầu vào của `/complete`); build chỉ tick MUST mà task tự nhiên chứng minh | Cảnh báo sớm "PLAN không phủ MUST" — `release-check` hàng `blueprint` vẫn chặn phát hành |
| R4 | `researcher` + ADR stack (G2) | ≥ 1 lượt subagent + web | Chỉ khi **thêm** phụ thuộc/dịch vụ/luật ngành; stack có sẵn đọc manifest (README b1); còn lại "(chưa xác minh)" đúng P2 | Bảng phiên bản có ngày → nhóm DEP của `/complete` |
| R5 | `SPEC-*.md` đầy đủ (G3) | 1 lượt/spec | Given/When/Then + ca biên ghi trong dòng task hoặc là chính test; SPEC riêng cho nghiệp vụ không tầm thường (tiền, quyền, trạng thái) | Quay lui G3 khó hơn — `/complete` viết SPEC đủ cho lát có 🔴/🟠 |
| R6 | Thiết kế đầy đủ G4 | — | ADR-0041 đã dời sang harden; giữ "chỉ phần code cần" | — |
| R7 | Tự duyệt PLAN `loop decide` | 0,25 s | Giữ (là cơ chế "tự quyết" có dấu vết, ADR-0008) | — |
| R8 | Gate mỗi task qua `loop record`, cổng commit `gate-fast` | giây | Giữ (P1; ADR-0011) | — |
| **R9** | **`done` đòi blueprint 0 MUST mở** | 70–1 146 mục | **Sửa máy**: ở pha build `done` khi mọi task xanh, ghi số MUST mở vào lý do "trả ở `/complete`"; giữ kiểm `bad_waivers`/`bad_lines`/`_scope_drift`, giữ `loop init --blueprint` | Lưới "mọi MUST" cuối G6 → `release-check` hàng `blueprint --strict --run` giữ ở G7 |
| R10 | `PROGRESS.md` mỗi lát | 1 Edit/lát | Giữ (ADR-0033) | — |
| R11 | PR mỗi lát, CI xanh, `pr next`/`merge-watch` | CI 94–162 s | Giữ (chủ repo: "CI xanh là merge"); không chờ merge | — |
| R12 | `loop verify --all` trước `done` | ≈ 1 lần cổng | Giữ (D-084: task sau phá task trước) | — |
| **R13** | **Kết thúc: PR đặt `harden` → audit delta → `release-check` → GO-NO-GO** | ≥ 2 PR + ≥ 5 lượt subagent + chạy `attack`/`perf` | **Bỏ khỏi `/autopilot`** → là nội dung của `/complete`; máy không đổi (Stop hook chưa từng gọi `release-check`) | Không — `release-check` FAIL `phase` ở build vẫn chặn phát hành |
| R14 | Skill gộp hai pha, rẽ nhánh build/harden ở bước 1, 6 | chọn sai nhánh | Tách skill; `/autopilot` giữ **một** dòng cho pha harden (repo khung luôn harden — D-136) | — |

Luận điểm "sau 5 ADR chỉ còn 3 rào cản" **bị bác** (3/3): còn R12 (`verify --all`) và cổng commit chạy cả khi chỉ sửa
tài liệu — nhưng cả hai là bằng chứng máy (P1), giữ có chủ đích; ghi vào §10 để đo.

## 5. Lợi

- Vòng build ra `done` khi **việc build xong** (task xanh + `verify --all` + PR merge), không kẹt ở hàng trăm MUST tài liệu/a11y/
  runbook vốn là việc của hoàn thiện. Người dùng có điểm dừng tự nhiên giữa hai pha và biết gõ gì tiếp.
- Khối tốn nhất (audit + nợ review + `release-check` + GO-NO-GO) ra khỏi vòng build; `/complete` lặp lại được mỗi bản phát
  hành mà không sửa máy (audit delta theo SHA nhóm, `review_debt`, `release-check` idempotent).
- Không hạ sàn phát hành ở mức máy: mọi chốt G7 nằm trong `release_check` (`scripts/xt.py:8398–8427`) và không phụ thuộc
  `_verdict_blueprint`; hàng `blueprint` gọi `blueprint_status` trực tiếp (8217–8242).
- Không đổi nghĩa ID checklist nào; không lệnh `xt.py` mới; skill mới được `install.py` chép tự động; đường lùi là revert
  (verdict về như cũ) hoặc đặt `harden`.
- Khớp nghiên cứu đã có: "nhanh nghĩa là không audit toàn repo mỗi lát, không phải bỏ cổng lát" (2026-10-19 §2);
  DORA *Working in small batches*: lô nhỏ "reduces the time it takes to get feedback on changes" (xác minh 2026-10-25).

## 6. Hại và cách đỡ

| Hại | Cách đỡ |
|---|---|
| MUST sàn bảo mật/cấu hình/dữ liệu bị để tới `/complete` ("thứ sai từ đầu thì làm lại cả hệ", lifecycle quy tắc 6) | Máy chưa có khái niệm "MUST sàn" (verdict hiện đòi *mọi* MUST — tiêu chí G7, không phải G5); sàn G5 thật là cổng commit/CI + guard + ngoại lệ cứng merge (ADR-0016). PLAN build: T-001 dựng nền phủ MUST baseline bảo mật/cấu hình/dữ liệu; `done` ở build in số MUST mở |
| "Nợ không bao giờ trả": không cơ chế máy nào buộc dự án đích chạy `release-check` trước deploy (CI mẫu, hook, ruleset đều không gọi) — luận điểm **trụ** 3/3 | Rủi ro đã chấp nhận ở ADR-0037 ("nhánh chính ở pha build không được coi là bản phát hành"). Đỡ thêm: lý do `done` ở build và báo cáo cuối `/autopilot` bắt buộc ghi "chưa phát hành — gõ `/complete`"; `release-check` giữ FAIL `phase`. Job CI theo tag chạy `release-check` ghi nợ (§9) |
| Người dùng hiểu "loại bỏ rào cản" = tắt guard, `bypassPermissions`, tắt hook | ADR-0046 và skill ghi **một** dòng "Sàn không bỏ" trỏ `stop-points-and-escalation.md` §Điểm dừng; bị chặn là kết luận (`LOOP-STOP-025`) |
| "Trả nợ review" = audit delta theo SHA quét trên diff gộp cả pha build — review LLM kém ở diff lớn (research 2026-10-21 §4.4: F1 0,66 ở < 10 dòng, 0,04 ở > 150 dòng) | `/complete` chia audit delta theo nhóm × theo PR/lát đã merge kể từ SHA quét (mỗi cụm ≤ ~150 dòng cho reviewer), giữ xác minh đối kháng 🔴/🟠, bug sửa bằng test tái hiện đỏ trước |
| Rút SPEC/PROJECT ở build mất ca biên, quay lui G3 khó | Gate của task có nghiệp vụ không tầm thường là test có ≥ 1 ca biên; `(exec: deep)` theo 4 khía cạnh; `/complete` viết SPEC đủ cho lát có 🔴/🟠 |
| Thêm skill = mở bề mặt, trái chặng "đóng băng và cắt" (research 2026-10-23 §7) | Skill mỏng ≤ 6 144 B chỉ nối lệnh có sẵn, có trần trong `CAPS`; chữ harden rời `/autopilot` nên tổng byte skill gần không đổi; không lệnh/hook/ID mới |
| Pha cho verdict đọc cây làm việc, guard/merge đọc cả nhánh đích — sửa `xt.yaml` tại chỗ sang `build` ở dự án harden được `done` sớm | Bất đối xứng có sẵn (ADR-0041 dùng cho sàn Gate); chốt thật là `release-check` (đọc `xt.yaml` của cây + sổ audit) và merge (nhánh đích) |
| PR chạm auth/tiền/PII vẫn chờ người merge ở build khi `merge_hard_exceptions: human` (mẫu dự án đích) | Là điểm dừng, không phải rào cản tốc độ; chủ dự án đích tự đặt `auto` (ADR-0020) kèm D-NNN nếu chấp nhận rủi ro — khung không quyết thay |

## 7. Chỗ phải diễn giải lại ý chủ repo (nói thẳng)

1. **"Loại bỏ tất cả rào cản"** → bỏ rào cản *quy trình* (R2–R5, R9, R13, R14); **không** bỏ sàn an toàn và bằng chứng máy
   (R7, R8, R11, R12, guard, điểm dừng). Lý do: mục tiêu "chất lượng cao" của chính yêu cầu; tiêu chí 1 (đúng và an toàn).
2. **"/autopilot là pha build"** → `/autopilot` **tôn trọng pha trong `xt.yaml`**, không tự đổi pha. Dự án đích mới ở `build`
   (mẫu); sau `/complete` dự án ở `harden` **một chiều** (ADR-0037 mục 3) — đợt tính năng sau phát hành chạy luật harden
   (reviewer theo `pr next`, sàn M/L, cổng trước push). Muốn dựng nhanh một đợt lớn mới ở dự án đã có người dùng thật là quyết
   định của chủ dự án qua PR sửa `xt.yaml` (PR đó luôn tính harden — D-137), không phải của skill.
3. **Repo khung luôn `harden`** (D-136): `/autopilot` ở chính repo khung chạy luật harden; `/complete` dùng cho repo khung khi
   phát hành (audit delta + `release-check`), như vẫn làm.
4. **"/complete mới audit, review, fix, refactor"** → đúng; thêm vào đó những thứ ADR-0041 đã dời sang harden: sàn Gate M/L,
   thiết kế đầy đủ (C4, `API-CONTRACT.md`, `THREAT-MODEL.md`), MUST blueprint còn mở, `attack`/`perf` (ADR-0042), GO-NO-GO.

## 8. Thiết kế (chi tiết ở ADR-0046)

- **`/autopilot`** (pha build; ở `harden` chạy luật harden): Bước 0 giữ, đọc pha; Pha 1 = đầu ra mức S cho G0–G4 (đọc repo →
  `compose` không tick → PLAN có Gate + Given/When/Then ngắn; research/ADR chỉ khi thêm phụ thuộc); Pha 2 giữ nguyên số bước;
  Kết thúc = `done` của máy (task xanh + `verify --all` + PR merge) + báo cáo ghi số MUST mở, nợ review và dòng "chưa phát hành
  — gõ `/complete`". Bỏ "Trước G7 ở pha build…", `release-check`, GO-NO-GO khỏi skill.
- **`/complete`** (pha harden): (0) tên phiên, `doctor --fix`, đọc pha — khuyến nghị phiên mới sau `/handover` (context sạch cho
  audit đối kháng); (1) chưa `harden` → PR đặt `delivery_phase: harden` + khai khoá sàn M/L và `attack`/`perf` → merge (review
  làn chuẩn trở lại từ đây); (2) `/audit` full lần đầu / delta bản sau, nợ review = audit delta chia theo PR/lát, đối kháng
  🔴/🟠; (3) gieo `docs/autopilot/PLAN-harden-<ngày>.md` từ 🔴/🟠 (test tái hiện đỏ trước), MUST mở (`blueprint-status --strict
  --json`), sàn (`xt.py floor`), thiết kế đầy đủ theo quy mô, refactor từ nhóm CODE/ARCH, perf theo `optimization-loop.md` (chỉ
  khi có số), `release-check --json` lần 1 (mỗi hàng FAIL = task); tự duyệt D-NNN; (4) vòng lặp như `/autopilot` Pha 2 với luật
  harden (`milestone_audit: now`, PR ≤ 150 dòng, `dev-task.sh gate` trước push, reviewer khi `pr next` đòi, reviewer-alt rà diff
  ngoại lệ cứng trước PR); (5) `loop verify --all` → `release-check` không NO-GO → `GO-NO-GO.md`, `loop stats`, `feedback
  collect`; sau phát hành giữ `harden`.
- **Máy**: `_verdict_blueprint` rẽ theo `_phase_in_tree`: build + còn MUST mở → `done` kèm `open_must` và lý do "trả ở
  `/complete`"; `bad_waivers`/`bad_lines` vẫn `continue`; `_scope_drift` vẫn `verify`; `_still_open`/`_with_pending_human` giữ
  (MUST đã `loop defer` vẫn ra `done-pending-human`). Chuỗi lý do ở `_with_dispatch` và `_release_phase` trỏ `/complete`.
  `DOCTOR_SKILLS` thêm `complete`; `CAPS` thêm trần 6 144 B cho skill mới.
- **Tài liệu** (một chủ đề một nhà): `lifecycle.md` quy tắc 6 là nhà của "đầu ra mức S ở pha build, đầy đủ ở `/complete`";
  README mảng 11 bước 12/16 + "Pha 3 — hoàn thiện"; `audit.md` §1; mẫu PLAN; AGENTS.md ×2 §7–8; CLAUDE.md; README gốc;
  dòng Trạng thái của ADR-0031/0033/0037/0041 ghi "làm rõ bởi ADR-0046". Bản **3.21.0** (skill mới + harness đổi → dự án đích
  chạy lại `install.py`).

## 9. Không làm và vì sao

- **Không bỏ `--blueprint` ở `loop init` pha build** (0 code) — mất `scope` khoá quy mô, `_scope_drift`, chạy lại `— Kiểm:` ở
  `verify --all` và `loop defer` theo MUST; sửa verdict theo pha giữ được tất cả (tiêu chí 1, 3).
- **Không lọc "MUST sàn" trong verdict** — ID chưa có nhãn sàn; định nghĩa bằng tiền tố là luật mới cần ADR riêng và số đo.
- **Không verdict mới `done-build`** — chạm `hook_stop`, SessionStart và ≥ 6 file test; `done` + trường `open_must` đủ.
- **Không lệnh `xt.py complete`/`release-check --skip-run`** — `release-check --json` đã in việc phải làm mỗi hàng; thêm lệnh là
  thêm bề mặt (research 2026-10-23 §7). Xét lại khi đo `release-check` ở dự án M/L thật.
- **Không nới guard, điểm dừng, `merge_hard_exceptions` mẫu, `verify --all`, cổng commit** — sàn an toàn và bằng chứng máy.
- **Không cho `/autopilot` tự đặt lại `build`** sau phát hành — ADR-0037 một chiều; quyết định của chủ dự án.
- **Không ID checklist mới** — hai module 11 đã đủ 4 MUST; luật nằm ở lifecycle quy tắc 6 + ADR-0046 + skill.
- **Chưa làm** job CI theo tag chạy `release-check` ở mẫu dự án đích (ADR-0042 chưa có điểm móc "deploy") — ghi nợ ở ADR-0046.

## 10. Phép đo tiếp theo

- Thời gian một lát và số lượt `loop record`/task ở ≥ 1 dự án đích chạy bản 3.21.0 (từ `.autopilot/runs.jsonl`
  `started`/`finished`) so với bản 3.20.x — ≥ 10 task mỗi bản (`LOOP-ORCH-020`).
- Tỉ lệ `done` ở build có `open_must > 0` và số MUST đó được đóng ở `/complete` (từ sổ audit + `blueprint-status`).
- Thời gian `release-check` ở dự án M/L thật (quyết `--skip-run` có đáng không).
- Chi phí `loop verify --all` và cổng commit khi chỉ sửa tài liệu — hai rào cản còn lại mà phản biện chỉ ra.

## 11. Chưa xác minh

- Tăng tốc thực tế của việc tách: lượt model mỗi lát chưa có số đo (`.autopilot/` cục bộ; `loop stats` trên clone = 0).
- Số liệu "50 % better delivery performance với review nhanh" chỉ thấy ở tóm tắt tìm kiếm, không có trong trang DORA 2023 đã
  mở — không dùng.
- Trích dẫn Claude Code docs (skills, sub-agents) và Anthropic engineering đi qua một lượt fetch; chỉ DORA *Working in small
  batches*, *Pervasive security*, *Balancing AI tensions* được kiểm lại nguyên văn lần hai.

## Nguồn

- Khung: ADR-0031, ADR-0033, ADR-0037, ADR-0040, ADR-0041, ADR-0042, ADR-0045 (`docs/adr/`); `framework/00-method/lifecycle.md`
  quy tắc 6; `framework/11-autonomous-loop/README.md`; `research/2026-10-19-rapid-build-then-harden.md`,
  `research/2026-10-21-next-level-speed-automation-quality.md`, `research/2026-10-23-ceiling-analysis.md` (đọc 2026-10-25).
- Claude Code — Skills (frontmatter `name`/`description`/`argument-hint` hợp lệ; thân skill chỉ nạp khi gọi):
  <https://code.claude.com/docs/en/skills> — xác minh 2026-10-25 (một lượt).
- Claude Code — Sub-agents (`model`, `effort`, `maxTurns`; lồng mặc định 3 tầng, tắt bằng `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH=1`
  hoặc bỏ `Agent` khỏi `tools`): <https://code.claude.com/docs/en/sub-agents> — xác minh 2026-10-25 (một lượt).
- Claude Code — Best practices ("Have Claude show evidence rather than asserting success"):
  <https://code.claude.com/docs/en/best-practices> — xác minh 2026-10-25 (một lượt).
- DORA — Working in small batches ("reduces the time it takes to get feedback on changes, making it easier to triage and
  remediate problems"): <https://dora.dev/capabilities/working-in-small-batches/> — xác minh 2026-10-25 (kiểm lại nguyên văn).
- DORA — Pervasive security ("Defects involving security, performance, and availability are expensive and time-consuming to
  remedy"): <https://dora.dev/capabilities/pervasive-security/> — xác minh 2026-10-25 (kiểm lại nguyên văn).
- DORA — Balancing AI tensions (2026-03-10; "Velocity gains for an individual author frequently translate into a significantly
  increased cognitive load for the reviewer"): <https://dora.dev/insights/balancing-ai-tensions/> — xác minh 2026-10-25.
- Anthropic — Harness design for long-running application development (2026-03-24; "agents reliably skew positive when grading
  their own work"): <https://www.anthropic.com/engineering/harness-design-long-running-apps> — xác minh 2026-10-25 (một lượt).
