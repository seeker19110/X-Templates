# PLAN-3.21-single-loop.md — Khung X-Templates · một vòng lặp agent hay agent con chuyên biệt: đổi tiêu chí, giữ harness, đo trước → bản 3.20.0

> Lập ngày 2026-10-24. Chủ repo gửi bài claude.com *Building agents: When to fold subagents into your main agent loop*
> (2026-10-22) + kit `anthropics/single-agent-loop-kit`, yêu cầu kiểm chứng rồi "lập PLAN cho mục 1 và 2 rồi làm" (mục 1 =
> `agentic-systems.md`, mục 2 = `orchestration-and-subagents.md`). Phiên chính tự duyệt (D-162).
>
> **Cú pháp bắt buộc cho máy:** mỗi task một dòng `- [ ] \`T-NNNN\` <việc> — Gate: \`<lệnh>\``.

## Tóm tắt (cổng duyệt — phiên chính tự duyệt, D-162)
- Dữ kiện (xác minh 2026-10-24, chi tiết ở `research/2026-10-24-single-agent-loop.md`): bài nói một vòng lặp + skill
  "frequently outperformed" cả một-prompt lẫn router + agent con theo miền — *thường*, không *luôn*; 3 điều kiện giữ agent con
  (context phình đo được · song song với context vứt được · chọn sai tool/chỉ thị mâu thuẫn); quy tắc "đo trước, đổi một thứ
  một lần, giữ cái đứng vững". Kit: "does not assume a single loop always wins. It measures."; *Not maintained*; mới chạy
  thật 2 lần trên một ví dụ, bước merge/upkeep chưa chạy.
- Phạm vi: (1) `framework/13-ai-engineering/agentic-systems.md` — `AI-AGENTIC-001` (MUST@L, giữ ID) thành luật đổi kiến
  trúc hai chiều qua cùng eval end-to-end; `AI-AGENTIC-011` (giữ ID) là nhà **ba lý do context** + kiểm kê agent con; mục mới
  `AI-AGENTIC-019` (SHOULD, trình tự gộp có đo); Nguyên tắc 1–2, bảng Pattern, mục "Kết luận cho từng agent con", §Handoff
  (schema kết quả), bẫy, cổng, Nguồn. (2) `framework/11-autonomous-loop/orchestration-and-subagents.md` — header, Nguyên tắc 3
  (tách vì context — giả định, đo), hàng `executor` nói thật "tầng mặc định của harness, chưa phải lý do context", hàng "Làm
  trực tiếp" thành nhóm đo (`loop record` không `--executor`), `context_reason` trong gói giao việc, `LOOP-ORCH-017` MAY → SHOULD
  (Kiểm từ `loop stats --all --json`), mục mới `LOOP-ORCH-020` (SHOULD: giữ mặc định giao việc tới khi có số), bẫy, cổng, Nguồn.
  Kèm research note, ADR-0045, `conventions.md` §7 (một dòng trỏ), CHANGELOG + VERSION 3.20.0, PROGRESS.
- Không làm (ghi nợ ở ADR-0045): đổi `scripts/xt.py`/hook/`.claude/agents/*`/skill `/autopilot`/`AGENTS.md` (sát trần
  7 168 B); `LOOP-ORCH-019` (luật không nhét vào `· Nguồn:`); `LOOP-ORCH-008` (vế "token agent con tính vào ngân sách" chỉ là
  docstring kit, chưa chạy thật); R04/R07/R09/R10/R11 có nhà khác (`evaluation.md`, `AI-AGENT-006`, `XC-DOCAI`, `AI-APP-007`);
  `llm-app-foundations.md`/`02-profiles/*` còn chép thang cũ → lát sau.
- Rủi ro: thư mục `11-autonomous-loop` sát trần byte ADR-0043 (dư 7 578 B; ước +3,5 KB) — Gate T-2903 chạy
  `test_docs_budget`; đổi chữ quy phạm `AI-AGENTIC-001/011`, `LOOP-ORCH-017` làm blueprint dự án đích thấy "Cũ" (chủ đích,
  ghi CHANGELOG); `context_reason`/`executor: null` là lời khai — luật ghi rõ, số đo chỉ có ở phiên thật. Đường lùi: revert
  PR; ID mới hạ MAY "Ngừng dùng".
- Cách làm: task là chữ do phiên chính viết (SPEC = nội dung cuối), giao `executor` chỉ là chép lại → phiên chính tự làm,
  `loop record` không `--executor` — điểm đo đầu của `LOOP-ORCH-020` (ghi ở báo cáo cuối). Review trước PR: `reviewer-alt`
  năng lực cao hơn phiên chính (`LOOP-ORCH-005`).

## Ngân sách (4 con số)
- Số vòng tối đa: `max(40, 8 × task)` (`loop init --single-session` tính)
- Chi phí: 0 đồng ngoài phiên (không phụ thuộc mới)
- Timeout mỗi lệnh Gate: 1800 giây (`XT_RECORD_TIMEOUT` mặc định)
- Ngày hết hạn: 4 giờ sau `loop init` (`--hours 4`)

## Điểm dừng bắt buộc (`loop defer`; `loop block` khi mọi việc còn lại phụ thuộc)
- Tag `v3.20.0` qua `release-tag.yml` sau khi PR merge (REST `workflow_dispatch`); GO-NO-GO chờ chủ repo ký như các bản trước
- Nâng khung ở dự án đích (`install.py` + `compose` lại): chủ dự án

## Task

### Lát 1 — Nguồn, luật, bản 3.20.0
- [x] `T-2901` Research note `research/2026-10-24-single-agent-loop.md` (dữ kiện bài + kit theo mục H2/H3, bản đồ phủ, điều bài không nói, bằng chứng mỏng, phép đo tiếp) và `docs/adr/0045-split-by-context-measure-before-fold.md` (files: research/2026-10-24-single-agent-loop.md, docs/adr/0045-split-by-context-measure-before-fold.md) — Gate: `python3 scripts/xt.py validate && python3 scripts/check-links.py && test -s docs/adr/0045-split-by-context-measure-before-fold.md && test -s research/2026-10-24-single-agent-loop.md`
- [x] `T-2902` `agentic-systems.md`: `AI-AGENTIC-001`/`011` đổi chữ giữ ID, `AI-AGENTIC-019` mới, Nguyên tắc 1–2 và 5, bảng Pattern, mục "Kết luận cho từng agent con", §Handoff, bẫy, cổng, Nguồn; `conventions.md` §7 một dòng trỏ; `13-ai-engineering/README.md` hàng chỉ mục (sau: T-2901; files: framework/13-ai-engineering/agentic-systems.md, framework/13-ai-engineering/README.md, framework/00-method/conventions.md) — Gate: `python3 scripts/xt.py validate && python3 scripts/check-links.py && grep -q "AI-AGENTIC-019" framework/13-ai-engineering/agentic-systems.md`
- [ ] `T-2903` `orchestration-and-subagents.md`: header, Nguyên tắc 3, bảng "Khi nào tách subagent" (hàng `executor`, hàng "Làm trực tiếp"), `context_reason`, `LOOP-ORCH-017` MAY → SHOULD, `LOOP-ORCH-020` mới, bẫy, cổng, Nguồn — trong trần byte ADR-0043 (sau: T-2902; files: framework/11-autonomous-loop/orchestration-and-subagents.md) — Gate: `python3 -m unittest tests.test_docs_budget && python3 scripts/xt.py validate && python3 scripts/check-links.py && grep -q "LOOP-ORCH-020" framework/11-autonomous-loop/orchestration-and-subagents.md`
- [ ] `T-2904` CHANGELOG `[3.20.0]` (Changed/Added nêu ID), VERSION 3.20.0, PROGRESS.md (≤ 8 KB) (sau: T-2903; files: CHANGELOG.md, VERSION, PROGRESS.md) — Gate: `scripts/dev-task.sh lint`
