# PLAN-3.22-adr0045-rest.md — Khung X-Templates · trả nốt nợ ADR-0045 → bản 3.21.0

> Lập ngày 2026-10-25. Chủ repo: "tiếp tục trả nợ ADR-0045 còn lại". Phiên chính tự duyệt (D-170).
>
> **Cú pháp bắt buộc cho máy:** mỗi task một dòng `- [ ] \`T-NNNN\` <việc> — Gate: \`<lệnh>\``.

## Tóm tắt (cổng duyệt — phiên chính tự duyệt, D-170)
- Phạm vi: bốn mục **SHOULD mới**, mỗi mục ở nhà đúng — `AI-EVAL-021` (eval khởi đầu ~10 ca, bộ chung có chủ + bộ theo skill,
  timestamp replay), `AI-AGENT-024` (gom tool theo ý định, tool search khi vượt ~30–50 định nghĩa, ràng buộc cứng trong
  tool), `XC-DOCAI-021` (mỗi skill một DRI + eval riêng, đội trung tâm nhỏ duyệt), `AI-APP-019` (tri thức tham chiếu sau
  tool tra/skill, không dán bằng code); `LOOP-CTX-010` hạ MAY "Ngừng dùng — gộp vào `LOOP-ORCH-012`"; văn xuôi: bảng "Cách
  xây" của `llm-app-foundations.md`, README mảng 11, `templates/AGENTS.md` §8. Sửa hai chỗ chữ ở CHANGELOG `[3.20.1]`.
- Giữ nguyên: `AI-AGENT-006` (MUST@L, trần chặt hơn ngưỡng 30–50 của nguồn — "tends to degrade", chưa có số của dự án);
  `AI-APP-007`, `AI-APP-010`; `templates/CLAUDE.md` (câu "điều phối" vẫn đúng).
- Không làm: `delegation_rate` trong `loop stats` (mã `xt.py`, test 100 %, cần số từ ≥ 2 vòng — `LOOP-ORCH-020`).
- Rủi ro: `templates/AGENTS.md` sát trần 8 192 B (dư 4 B) → cắt chữ khác cùng mục; thư mục 11 dư ~2,1 KB (README + CTX).
  Thêm mục + hạ MAY → bản MINOR 3.21.0, dự án đích ghép lại blueprint. Đường lùi: revert PR.
- Cách làm: SPEC là chữ cuối → phiên chính tự làm, `loop record` không `--executor` (điểm đo thứ ba của `LOOP-ORCH-020`).

## Ngân sách (4 con số)
- Số vòng tối đa: `max(40, 8 × task)`
- Chi phí: 0 đồng ngoài phiên
- Timeout mỗi lệnh Gate: 1800 giây
- Ngày hết hạn: 3 giờ sau `loop init` (`--hours 3`)

## Điểm dừng bắt buộc (`loop defer`; `loop block` khi mọi việc còn lại phụ thuộc)
- Tag `v3.21.0` qua `release-tag.yml` sau merge; nâng khung ở dự án đích: chủ dự án

## Task

### Lát 1 — Bốn mục mới, một mục ngừng dùng, văn xuôi
- [x] `T-3101` Bốn mục SHOULD mới `AI-EVAL-021`, `AI-AGENT-024`, `XC-DOCAI-021`, `AI-APP-019` (mỗi mục `→ Kiểm:` + `· Nguồn:` có bài claude.com/kit) (files: framework/13-ai-engineering/evaluation.md, framework/13-ai-engineering/agents-and-tools.md, framework/13-ai-engineering/llm-app-foundations.md, framework/18-cross-cutting/docs-for-ai-agents.md) — Gate: `python3 scripts/xt.py validate && python3 scripts/check-links.py && grep -q "AI-EVAL-021" framework/13-ai-engineering/evaluation.md && grep -q "AI-AGENT-024" framework/13-ai-engineering/agents-and-tools.md && grep -q "XC-DOCAI-021" framework/18-cross-cutting/docs-for-ai-agents.md && grep -q "AI-APP-019" framework/13-ai-engineering/llm-app-foundations.md`
- [ ] `T-3102` `LOOP-CTX-010` → MAY "Ngừng dùng"; bảng "Cách xây" thành từ vựng; README mảng 11 hàng điều phối; `templates/AGENTS.md` §8 trong trần 8 192 B (sau: T-3101; files: framework/11-autonomous-loop/context-and-token-budget.md, framework/11-autonomous-loop/README.md, framework/13-ai-engineering/llm-app-foundations.md, framework/templates/AGENTS.md) — Gate: `python3 -m unittest tests.test_docs_budget && python3 scripts/xt.py validate && python3 scripts/check-links.py && grep -q "Ngừng dùng" framework/11-autonomous-loop/context-and-token-budget.md && grep -q "LOOP-ORCH-020" framework/templates/AGENTS.md`
- [ ] `T-3103` CHANGELOG `[3.21.0]` + sửa hai chỗ chữ ở `[3.20.1]`, VERSION 3.21.0, PROGRESS.md ≤ 8 KB (sau: T-3102; files: CHANGELOG.md, VERSION, PROGRESS.md) — Gate: `scripts/dev-task.sh lint`
