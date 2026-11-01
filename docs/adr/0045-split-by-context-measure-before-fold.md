# ADR-0045: Tách agent chỉ vì context, đổi kiến trúc agent chỉ qua eval so sánh; vòng lặp phát triển giữ harness và đo trước khi đổi mặc định giao việc

- **Trạng thái:** Đã chấp nhận (phiên chính tự duyệt theo tiêu chí chất lượng cuối, ADR-0008 — D-168; chủ repo chốt phạm vi
  "mục 1 và 2" 2026-10-24); mặc định giao việc của harness thay bởi [ADR-0061](0061-adaptive-agent-topology.md) (D-292:
  `topo: self`); phép đo và điều kiện đổi của `LOOP-ORCH-020` giữ cho lần đổi kế
- **Trạng thái triển khai:** Đã triển khai — chỉ tài liệu: `framework/13-ai-engineering/agentic-systems.md` (`AI-AGENTIC-001`,
  `011` đổi chữ giữ ID; `019` mới; Nguyên tắc 1–2, 5; bảng Pattern; mục "Kết luận cho từng agent con đang có"; §Handoff; bẫy;
  cổng; Nguồn), `framework/11-autonomous-loop/orchestration-and-subagents.md` (header; Nguyên tắc 3; bảng "Khi nào tách
  subagent"; `context_reason`; `LOOP-ORCH-017` MAY → SHOULD; `LOOP-ORCH-020` mới; bẫy; cổng; Nguồn), `framework/00-method/
  conventions.md` §7, `research/2026-10-24-single-agent-loop.md`, CHANGELOG 3.20.0. Harness (`scripts/xt.py`, hook,
  `.claude/agents/*`, skill, `AGENTS.md`) **không đổi**.
- **Ngày:** 2026-10-24
- **Làm rõ:** ADR-0029 (hai tầng executor — **giữ**; `LOOP-ORCH-020` thêm điều kiện đo trước khi đổi tầng/mặc định); D-160 /
  `LOOP-ORCH-019` (chuỗi model phiên chính — giữ nguyên chữ); ADR-0043 (trần byte thư mục 11 — không nới); chữ cũ của
  `AI-AGENTIC-001` "thử workflow pattern trước, tự trị sau" **bị thay**. Không thay ADR nào.

## Bối cảnh

- Bài claude.com *Building agents: When to fold subagents into your main agent loop* (2026-10-22, xác minh 2026-10-24,
  `research/2026-10-24-single-agent-loop.md` §3): một vòng lặp + skill/tool nạp theo nhu cầu "frequently outperformed both the
  one-prompt-for-everything design and the subagent design on quality, and often at a lower cost and latency per task" — chữ
  "frequently/often", không "always"; ba điều kiện giữ agent con (context phình đo được · song song với context vứt được ·
  chọn sai tool/chỉ thị mâu thuẫn); 5 failure mode của tổ chức lớn (context, sprawl, Frankenprompt, eval cục bộ, latency;
  Conway); quy tắc kết bài: đo trước, đổi một thứ một lần, giữ cái đứng vững; fold từng cái, so từng task, chạy > 1 lần.
- Kit `anthropics/single-agent-loop-kit` (`c437962`, 2026-10-21, §4 của research note): "The kit does not assume a single loop
  always wins. It measures."; "Keeping a subagent is a fine outcome."; 5 kết luận `main/fold/merge/as-tool/keep`; ba tiêu chí
  "earned its own context". Nhưng "Reference implementation. Not maintained"; mới chạy thật 2 lần trên một ví dụ, merge/upkeep
  chưa chạy; write-up đã gỡ số.
- Khung hiện tại: Nguyên tắc 1 + `AI-AGENTIC-001` (MUST@L) cố định thang chaining → … → orchestrator-workers → tự trị, tức
  buộc đội sản phẩm dựng router + agent con trước — chính bẫy Conway bài nêu; module 11 chọn worker theo "độ phức tạp × độ khép
  kín" và lý do giao `executor` là "rẻ" — không phải lý do context; "làm trực tiếp" chỉ cho việc < 10 phút trong một file;
  chưa có số đo nào về tự làm so với giao (`research/2026-10-23-ceiling-analysis.md` §1: `loop stats` trên clone = 0).
- Ràng buộc: thư mục `11-autonomous-loop` dư 7 578 B dưới trần ADR-0043; mỗi module tối đa 4 MUST hiệu lực ở M (cả hai đã
  đủ 4); không tên model trong artefact (LOOP-HARNESS-027); `AGENTS.md` dư 6 B dưới trần 7 168 B; harness `loop record
  --executor` chỉ nhận `executor|executor-deep`, skill `/autopilot` bước 5 ghi "giao subagent theo trường `executor`".

## Phương án đã xét

1. **Giữ nguyên** thang "workflow trước, agent sau" + `executor` mặc định "vì rẻ"; chỉ ghi research note. Tốt: 0 byte, không
   churn blueprint. Xấu: MUST@L trái dữ kiện 2026-10 (ép dựng orchestrator trước); vòng lặp không có số để biết giao việc có
   đáng không.
2. **Đảo toàn bộ theo bài**: Nguyên tắc 1 thành "một vòng lặp luôn mặc định"; module 11 đổi mặc định sang "phiên chính tự
   làm", hạ/bỏ tầng executor; sửa `templates/AGENTS.md`, `CLAUDE.md`, README, skill. Tốt: đúng tinh thần bài ở sản phẩm.
   Xấu: bài không nói "always", kit nói "measure"; chưa có số đo cho vòng lặp phát triển; đụng harness + `AGENTS.md` sát
   trần; mất đường lùi ADR-0029 — chính là "đổi không đo" mà bài khuyên tránh.
3. **(Chọn) Đổi tiêu chí sản phẩm + giữ harness vòng lặp + thêm phép đo và điều kiện đổi**: `AI-AGENTIC-001` thành luật "mọi
   đổi kiến trúc agent, hai chiều, qua cùng eval end-to-end trước/sau, so từng ca; chưa có eval thì dựng eval nhỏ trước";
   `AI-AGENTIC-011` thành nhà ba lý do context + danh sách "không tách vì" + kiểm kê agent con; mục "Kết luận cho từng agent
   con đang có" (5 kết luận của kit); `AI-AGENTIC-019` trình tự gộp có đo; module 11: hàng `executor` nói thật là tầng mặc
   định của harness (chưa phải lý do context), hàng "Làm trực tiếp" thành nhóm đo (`loop record` không `--executor`),
   `context_reason` trong gói giao việc, `LOOP-ORCH-017` MAY → SHOULD với Kiểm từ `loop stats --all --json`, `LOOP-ORCH-020`
   giữ mặc định giao việc tới khi có số (≥ 10 task/nhóm × ≥ 2 vòng — khởi điểm tự đặt, không phải ngưỡng có nguồn). Tốt: khớp
   dữ kiện mà không cấm agent con; đo được ngay bằng harness hiện tại; mục mới đều SHOULD. Xấu: hai nhà trỏ chéo (11 → 13);
   `context_reason` và `executor: null` là lời khai; số đo chỉ có ở phiên thật.

## Quyết định

Chọn **phương án 3**. 5 workflow pattern giữ làm từ vựng; khởi điểm **khi bài toán đã cần agent** (ghi ngày, hạn sử dụng theo
thế hệ model — không ghi tên model) là một vòng lặp + skill/tool nạp theo nhu cầu; mọi tách/gộp qua eval so sánh; ba lý do
context có nhà ở `AI-AGENTIC-011`, module 11 trỏ sang. Vòng lặp phát triển giữ `researcher`/`executor`(-deep)/`reviewer` và
mặc định giao của harness: ba vai được **giả định** tương ứng ba lý do (`researcher` ≈ 1, `reviewer` ≈ 2 "kiểm mà không thấy
cách làm"; `executor` chưa có lý do đo được) — chưa có số, nên harness giữ nguyên và `LOOP-ORCH-020` quy định phép đo + điều
kiện đổi. `LOOP-ORCH-019` không đổi chữ (luật không nhét vào `· Nguồn:`). Nguồn đã xác minh 2026-10-24: bài
<https://claude.com/blog/building-agents-when-to-fold-subagents-into-your-main-agent-loop> (2026-10-22); kit
<https://github.com/anthropics/single-agent-loop-kit> (`c437962`, 2026-10-21).

## Hệ quả

- Tốt: đội sản phẩm có bảng `main/fold/merge/as-tool/keep` + trình tự có đo mà không phải đọc kit; MUST@L không còn ép dựng
  orchestrator trước; vòng lặp bắt đầu có số đo giao việc từ dữ liệu sẵn có (`runs.jsonl`, `loop stats`); không chạm
  `xt.py`/hook/agent/`AGENTS.md`.
- Xấu / đánh đổi: `AI-AGENTIC-001`/`011`, `LOOP-ORCH-017` đổi chữ quy phạm → blueprint dự án đích thấy "Cũ" (chủ đích);
  `context_reason`/`executor: null` máy không kiểm nội dung (như `--executor` hiện nay); `agentic-systems.md` dài hơn ≈ 60 %.
- **Nợ ghi rõ (ngoài phạm vi chủ repo chốt):** skill `/autopilot` bước 5 ("giao subagent theo trường `executor`"),
  `framework/templates/AGENTS.md` §8, `framework/templates/CLAUDE.md`, `framework/11-autonomous-loop/README.md` — vẫn đúng với
  harness hiện tại, thêm câu trỏ hàng "Làm trực tiếp"/`LOOP-ORCH-020` ở lần sửa kế (trần byte); `llm-app-foundations.md`
  Nguyên tắc 4/`AI-APP-010`, `02-profiles/ai-agent.md`, `02-profiles/agentic-system.md` còn chép thang cũ → trỏ về Nguyên tắc
  1/`AI-AGENTIC-001`; `evaluation.md` bậc "bắt đầu ~10 ca + bộ chung có chủ + bộ theo skill"; `AI-AGENT-006` tool
  search/deferred và đối chiếu ngưỡng 20–30 với 30–50; `XC-DOCAI` DRI + eval chung trước khi ship skill; `AI-APP-007` lý do
  kiến trúc; `LOOP-CTX-010` trùng `LOOP-ORCH-012`; `delegation_rate` trong `loop stats` sau khi đo tay ≥ 2 vòng.
- Việc phải làm tiếp: báo cáo cuối lát ghi nhóm tự làm/giao (điểm đo đầu: 4 task tài liệu của PLAN-3.21 do phiên chính tự
  làm, D-168); sau ≥ 2 vòng → research note + ADR kế về mặc định/tầng.
- Đường lùi: revert PR tài liệu; ADR này đổi "Bị thay bởi ADR-NNNN"; `AI-AGENTIC-019`/`LOOP-ORCH-020` giữ ID, hạ MAY "Ngừng dùng".

## Xác nhận

- `python3 scripts/xt.py validate` exit 0 (ID duy nhất; MUST trơn vẫn 4/4 ở cả hai module; `## Nguồn` có URL https + ngày).
- `python3 -m unittest tests.test_docs_budget` xanh (thư mục 11 ≤ 232 307 B).
- `python3 scripts/check-links.py` xanh.
- `grep -c 'AI-AGENTIC-011' framework/11-autonomous-loop/orchestration-and-subagents.md` ≥ 3; `grep -rn 'AI-AGENTIC-019\|LOOP-ORCH-020'
  framework/ CHANGELOG.md` có kết quả; `grep -c 'Workflow trước, agent sau' framework/13-ai-engineering/agentic-systems.md` = 0.
- Không tên model/URL phiên trong diff: guard `ai_attribution` ở commit + đọc lại diff (mẫu guard chỉ bắt dạng có tiền tố
  `claude`, nên đọc tay phần chữ mới).
- Số đo nối tiếp: sau ≥ 2 vòng autopilot, báo cáo cuối phiên nêu tỉ lệ tự làm/giao + xanh lần đầu hai nhóm (từ `loop stats
  --all --json`) — điều kiện mở ADR đổi harness.
