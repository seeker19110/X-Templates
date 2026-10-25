# ADR-0033: Pha build tối giản autopilot — audit theo mốc gom về G7, reviewer theo `pr next`, PROGRESS theo lát

- **Trạng thái:** Đã chấp nhận; quyết định 1 "gom audit về trước G7" = gom về `/complete` (ADR-0046)
- **Trạng thái triển khai:** Đã triển khai trong repo — `scripts/xt.py` `_with_dispatch` (`milestone_audit`: `now`|`g7`);
  (`_phase_in_tree`: `xt.yaml` không đọc được → `now`, fail-open); skill `.claude/skills/autopilot/SKILL.md` bước 10/13; `framework/11-autonomous-loop/README.md` bước 11/11b;
  `framework/00-method/audit.md` §1; test `tests/test_xt_core.py::LoopRecordBranchesTest.test_milestone_done_marks_section_transition`.
- **Ngày:** 2026-10-20
- **Làm rõ:** ADR-0029 (audit theo mốc — thay ở pha build), ADR-0031 (pha build/harden — mục Hệ quả "audit delta mỗi
  mốc" thay ở pha build); quyết định D-110.

## Bối cảnh

Chủ repo hỏi autopilot đã tối giản cho giai đoạn dev chưa. ADR-0031 cho máy merge bỏ review ở pha build, nhưng quy
trình vẫn giữ ba khâu không thêm chốt an toàn nào ở pha này:

1. **Giao reviewer mỗi PR** (skill bước 10 (c), "song song với CI") — ở pha build `pr next` chỉ trả `review` cho
   ngoại lệ cứng, PR mang nhãn `risk:`, hoặc PR từng có review báo lỗi chặn chưa được rà sạch sau đó (`review_deferred`,
   ADR-0031); với PR còn lại lượt review không đổi được merge, chỉ tốn một subagent mỗi PR.
2. **Audit delta mỗi mốc** (ADR-0029) — trùng với audit delta bắt buộc trước G7: `release-check` FAIL hàng `phase`
   (còn `build`) và `review_debt` (file đổi sau SHA quét) tới khi audit phủ toàn bộ diff. Code của mốc trước thường còn
   đổi ở mốc sau, nên quét giữa chừng quét lại cùng file.
3. **Cập nhật `PROGRESS.md` sau mỗi task** — một phiên chạy tới khi xong (ADR-0009); sau compaction SessionStart nạp lại PROGRESS
   nhưng vị trí việc đang làm (task, lệnh kiểm cuối, file chưa commit) lấy từ checkpoint của `loop` và `loop status`/PLAN,
   không từ PROGRESS; mỗi task thêm một lần sửa file trạng thái.

## Quyết định

1. **Pha build: audit delta theo mốc gom về trước G7.** `loop status` vẫn báo `milestone_done` (thông tin), thêm
   `milestone_audit: g7` và lý do "làm tiếp task kế"; pha harden (`milestone_audit: now`) giữ ADR-0029 nguyên vẹn. Pha
   đọc từ `xt.yaml` ở cây làm việc — đây chỉ là gợi ý thứ tự việc; chốt thật là `release-check` (đọc pha và sổ audit).
2. **Reviewer chỉ khi `pr next` trả `review`** (mọi pha): máy đã biết PR nào cần review (làn chuẩn pha harden, ngoại lệ
   cứng, nhãn `risk:`, PR từng bị review báo lỗi chặn — ADR-0024/0031). PR làn nhanh, và PR làn chuẩn ở pha build, không
   giao reviewer — đúng `AGENTS.md` §3 ("PR khác bật khi mở"); phiên chính vẫn được chủ động giao khi thấy rủi ro.
3. **`PROGRESS.md` cập nhật theo lát** — trong commit cuối của lát, trước cổng đầy đủ, không ghi số PR (chưa có) — và
   trước khi dừng, không sau mỗi task.

Giữ nguyên (tiêu chí 1 thắng tiêu chí 5, AGENTS.md §4): cổng đầy đủ `dev-task.sh gate` một lần trước khi đẩy (tránh vòng
CI đỏ); tắt auto-merge trước mỗi push (push thêm file ngoại lệ cứng không được tự merge khi auto-merge không ghim head —
ADR-0023/0025); `loop record`/`loop verify --all`; `merge-watch` chạy nền.

## Lý do

- Mỗi khâu bỏ đi đều đã có chốt máy ở chỗ khác (`pr next`/`merge_eligibility`, `release-check`, checkpoint của `loop`), nên
  bỏ không làm hạ sàn chất lượng phát hành — chỉ dời việc về đúng chỗ máy đòi.
- "Reviewer theo `pr next`" đưa quyết định review về một nhà (máy), skill không còn tả lại luật làn.

## Hệ quả

- Pha build: mỗi PR bớt một lượt subagent review, mỗi mốc bớt một lượt audit; audit delta ở G7 lớn hơn (phủ từ SHA quét
  cuối). 🔴 phát hiện muộn hơn — chấp nhận vì pha build vốn là "merge trước, review sau" (ADR-0031).
- Pha harden và dự án không khai `delivery_phase` (= harden): audit theo mốc như cũ; PR làn nhanh không còn được giao
  reviewer mặc định (trước đây skill giao cho mọi PR dù máy không đòi).
- Dự án đích: chạy lại `install.py` để nhận `xt.py` và skill `/autopilot` mới.

## Đường lùi

Đặt `delivery_phase: harden` — audit theo mốc trở lại ở task kế. Revert commit gỡ hẳn thay đổi; không có state mới cần
dọn (`milestone_audit` chỉ là trường thêm trong JSON của `loop status`).
