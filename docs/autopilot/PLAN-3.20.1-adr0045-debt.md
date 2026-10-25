# PLAN-3.20.1-adr0045-debt.md — Khung X-Templates · trả nợ ADR-0045: skill `/autopilot` bước 5 và thang cũ "workflow trước, agent sau" → bản 3.20.1

> Lập ngày 2026-10-25. Chủ repo chọn "Nợ ADR-0045" khi gọi `/autopilot` không kèm yêu cầu mới. Phiên chính tự duyệt (D-169).
>
> **Cú pháp bắt buộc cho máy:** mỗi task một dòng `- [ ] \`T-NNNN\` <việc> — Gate: \`<lệnh>\``.

## Tóm tắt (cổng duyệt — phiên chính tự duyệt, D-169)
- Phạm vi: skill `/autopilot` bước 5 thêm vế "trừ hàng Làm trực tiếp (`LOOP-ORCH-020`)" (cắt cụm thừa để giữ trần 6 144 B);
  Nguyên tắc 4 của `llm-app-foundations.md`, đoạn "Quy tắc đầu tiên" của `02-profiles/ai-agent.md` và hàng "Điều phối đa
  agent" của `02-profiles/agentic-system.md` đổi chữ trỏ về `AI-AGENTIC-001`/`011` (một nhà). Chỉ văn xuôi — chữ quy phạm
  mục checklist không đổi nên blueprint dự án đích không thành "Cũ".
- Không làm (ghi nợ ADR-0045 giữ nguyên): `evaluation.md` bậc "eval nhỏ", `AI-AGENT-006` (cần xác minh ngưỡng 20–30 so với
  30–50), `XC-DOCAI` (DRI + eval chung), `AI-APP-007`, `templates/AGENTS.md` §8, `delegation_rate` trong `loop stats`.
- Rủi ro: skill sát trần (dư 47 B) — Gate chạy `test_docs_budget`. Đường lùi: revert PR.
- Cách làm: SPEC là chữ cuối → phiên chính tự làm, `loop record` không `--executor` (điểm đo thứ hai của `LOOP-ORCH-020`).

## Ngân sách (4 con số)
- Số vòng tối đa: `max(40, 8 × task)`
- Chi phí: 0 đồng ngoài phiên
- Timeout mỗi lệnh Gate: 1800 giây
- Ngày hết hạn: 3 giờ sau `loop init` (`--hours 3`)

## Điểm dừng bắt buộc (`loop defer`; `loop block` khi mọi việc còn lại phụ thuộc)
- Tag `v3.20.1` qua `release-tag.yml` sau merge; nâng khung ở dự án đích: chủ dự án

## Task

### Lát 1 — Skill và thang cũ
- [x] `T-3001` Skill `/autopilot` bước 5 trỏ hàng "Làm trực tiếp" trong trần byte; `llm-app-foundations.md` Nguyên tắc 4, `02-profiles/ai-agent.md`, `02-profiles/agentic-system.md` đổi chữ trỏ `AI-AGENTIC-001`/`011` (files: .claude/skills/autopilot/SKILL.md, framework/13-ai-engineering/llm-app-foundations.md, framework/02-profiles/ai-agent.md, framework/02-profiles/agentic-system.md) — Gate: `python3 -m unittest tests.test_docs_budget && python3 scripts/xt.py validate && python3 scripts/check-links.py && grep -q "LOOP-ORCH-020" .claude/skills/autopilot/SKILL.md && grep -q "AI-AGENTIC-001" framework/13-ai-engineering/llm-app-foundations.md`
- [ ] `T-3002` CHANGELOG `[3.20.1]`, VERSION 3.20.1, PROGRESS.md ≤ 8 KB (sau: T-3001; files: CHANGELOG.md, VERSION, PROGRESS.md) — Gate: `scripts/dev-task.sh lint`
