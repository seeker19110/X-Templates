---
title: The Claude Code guide for startups và docs Claude Code: đối chiếu với khung
kind: research
updated: 2026-11-21
---

# The Claude Code guide for startups — đối chiếu với khung, 2026-11-21

> Xuất phát: một bài đăng mạng xã hội tóm tắt "tài liệu 27 trang của Anthropic" thành 7 điểm. Ghi chú này tìm bản chính
> thức, kiểm từng điểm với docs Claude Code, rồi so với khung. Hai agent đọc trang độc lập (một bản tóm tắt, một bản
> trích nguyên văn); số trang đếm trực tiếp từ hai tệp PDF. Mục nào chưa kiểm được ghi **(chưa xác minh)**.

## Kết luận

1. **Tài liệu chính thức có thật:** *The Claude Code guide for startups*, đăng 2026-08-20,
   <https://claude.com/resources/articles/claude-code-guide-for-startups>; hai bản PDF gắn trên trang đều **27 trang**
   (đếm đối tượng trang). Năm chương: Everyone ships · Automate the tedium · Trust, but verify · Build for rebuilding ·
   Prototype, dogfood, productionize; checklist hợp nhất cho chương 1–4 nằm trên trang web.
2. **Khung đã phủ phần lớn:** 6/7 điểm đã có luật hoặc cơ chế tương ứng (bảng dưới). Điểm chưa có: **Plan Mode**.
3. **Áp dụng ở PR này (đề xuất để chủ duyệt):** `WF-SDD-018` (SHOULD, Plan Mode cho việc lớn làm tương tác);
   bổ sung `XC-DOCAI-011` (CLAUDE.md cầu nối cho AGENTS.md theo thư mục);
   `scripts/AGENTS.md` và `tests/AGENTS.md` cho chính repo khung (trước đây repo khung chưa tuân thủ `XC-DOCAI-011`).
4. **Không áp dụng / ghi nợ:** thay `loop record` bằng `/goal`; `isolation: worktree` cho subagent (cần ADR). Lý do ở dưới.
5. **Bài đăng lệch nhẹ so với nguồn:** (a) "CLI thay MCP cho mọi thứ" — docs vẫn dùng MCP cho hệ thống không có CLI;
   (b) "ba tầng" không phải thuật ngữ của docs; (c) cờ Plan Mode: thân chương 04 của guide ghi `--plan`, checklist ghi
   `/plan`, docs *Permission modes* chỉ có `claude --permission-mode plan` — khung theo docs.

## Bảng đối chiếu 7 điểm

| # | Điểm | Nguồn chính thức (trích ngắn) | Khung đã có | Quyết định |
|---|---|---|---|---|
| 1 | Kết nối công cụ, ưu tiên CLI | Guide ch.1: "Connecting via CLI can be more token-efficient when a mature command-line tool already exists". Best-practices: "If that system has a CLI, that's usually the easiest way in." / "For systems without a CLI, there's MCP." | `XC-DOCAI-024` (CLI + skill mặc định, MCP khi cần phiên bền); harness dùng `gh` | Giữ nguyên |
| 2 | CLAUDE.md theo tầng, skill nạp theo nhu cầu | Guide checklist ch.1: "Use CLAUDE.md files in each subdirectory of your repo…", "Use skills for on-demand procedural workflows." Memory: "Files in subdirectories load on demand."; "target under 200 lines per CLAUDE.md file." | `XC-DOCAI-006` (≤ 200 dòng), `-009` (skill), `-011` (AGENTS.md lồng). Gốc repo: `AGENTS.md` 48 dòng. Chưa có file theo thư mục | **Áp dụng:** `scripts/`, `tests/` + bổ sung `-011` |
| 3 | Việc bắt buộc → hook | Guide ch.3: hooks "can serve as hard gates". Best-practices: "adding IMPORTANT probably won't fix it". Memory: "context, not enforced configuration" | `XC-DOCAI-004`, `-014`; guard ADR-0002/0018. Chỉ dùng hook loại `command` (docs: hook `prompt`/`agent` không tất định) | Giữ nguyên |
| 4 | `/goal` giữ mục tiêu task dài | Docs *goal*: "a wrapper around a session-scoped prompt-based Stop hook"; evaluator "doesn't run commands or read files independently"; điều kiện ≤ 4.000 ký tự; không khả dụng khi `disableAllHooks` hoặc `allowManagedHooksOnly` | P1: "xong" = bằng chứng máy (`loop record` + Stop hook đọc đĩa); đã phân tích ở `research/2026-10-13-claude-code-hooks-skills.md` | **Không thay.** `/goal` là lời khai của model nhỏ; có thể dùng bổ sung ở phiên tương tác ngoài autopilot (không thành luật) |
| 5 | Fan out nhiều subagent | Guide ch.2: "Dynamic workflows can be used to fan multiple subagents to analyze large amounts of data in parallel…". Docs sub-agents: mặc định 20 subagent đồng thời (`CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS`) — chỉ từ bản tóm tắt | `orchestration-and-subagents.md`, ADR-0049, `LOOP-ORCH-020` (chỉ tăng agent khi có số), `XC-DOCAI-022` | Giữ nguyên |
| 6 | Plan Mode trước khi viết lại | Docs *Permission modes*: "Enter plan mode by pressing `Shift+Tab` or prefixing a single prompt with `/plan`."; `claude --permission-mode plan`; "At the approval prompt, press `Esc` first, since pressing `Shift+Tab` there approves the plan." Guide ch.4: "For non-trivial rewrites, start Claude Code in plan mode (/plan or hit Shift+Tab)." | Chưa có (autopilot dùng PLAN máy kiểm, không phải Plan Mode) | **Áp dụng:** `WF-SDD-018` |
| 7 | Git worktree cho V2/song song | Guide ch.4: "Use git worktrees to run a rebuild in an isolated copy of the repo while the current version stays untouched." Docs *worktrees*: `claude --worktree <tên>`, `.claude/worktrees/<tên>/`, `.worktreeinclude`, `isolation: worktree` cho subagent | `WF-GIT`, `orchestration-and-subagents.md`, ADR-0049/0058; repo dùng worktree riêng cho mọi lát | Giữ nguyên; xem Ghi nợ 1 |

## Ghi nợ và điều không làm (chờ chủ duyệt)

0. **Mẫu `AGENTS.md` của dự án đích** (`framework/templates/AGENTS.md`) đang 8 097/8 192 B (`tests/test_docs_budget.py`), `AGENTS.md` gốc 7 167/7 168 B. Hai dòng đề xuất cho §9 — "quy ước theo thư mục: `AGENTS.md` con kèm `CLAUDE.md` cầu nối, ≤ 200 dòng" và "việc lớn làm tương tác: Plan Mode, duyệt kế hoạch rồi mới sửa (`WF-SDD-018`)" — cần thêm ≈ 490 B, phải cắt chữ thừa ở chỗ khác (luật: không nới trần). Chưa làm vì chưa chọn được phần nào của hai tệp cô đọng này nên bỏ; chủ chọn thì thêm sau. Hai quy tắc đã nằm ở nhà của chúng (`WF-SDD-018`, `XC-DOCAI-011`).
1. **`isolation: worktree` cho subagent `executor`/`executor-deep`.** Docs: chạy subagent "in a temporary git worktree, giving it an isolated copy of the repository" (nhánh mặc định là default branch, tự dọn nếu không đổi). Có thể giảm xung đột khi nhiều executor chạy song song (cùng động cơ với D-142), nhưng đổi giao thức điều phối: kết quả nằm ở nhánh riêng và phiên chính phải gộp. Cần ADR và thử trên một PLAN thật trước khi bật.
2. **`.worktreeinclude`** (chép tệp gitignored như `.env` vào worktree mới): chưa đánh giá cho `.venv` của repo khung.
3. **Phiên bản:** changelog chính thức ghi Claude Code mới nhất 2.1.330 (2026-11-20); mẫu khung đặt `claude_min_version` 2.1.295; đọc `AGENTS.md` trực tiếp cần ≥ 2.1.277 → không cần nâng.
4. **Chưa đánh giá:** Code Review (research preview), Claude Tag (public beta), "dynamic workflows", company plugin marketplace — chỉ thấy nêu trong checklist của guide, chưa tìm docs chính thức.
5. **Evals** (guide ch.3: "Establish a process for creating and maintaining agent evaluations"): khung đã có `autonomy-bench` và `AI-EVAL-*`; không thêm.

## Chưa xác minh

- Vị trí và độ dài "một trang cuối" của checklist trong PDF: chỉ đếm được số trang (máy không có công cụ dựng trang PDF); nội dung checklist lấy từ trang web.
- Các đoạn Higgsfield, ClickHouse, Harvey trong guide: chỉ thấy qua kết quả tìm kiếm.
- Phiên bản đầu tiên có `/goal` và `--worktree`; docs "dynamic workflows" và hướng dẫn evals trong docs.
- Một số trang docs dài chỉ đọc phần đầu; các trích dẫn dùng ở đây đã kiểm bằng văn bản gốc của đúng mục được nêu.
- Bài đăng mạng xã hội gốc không được truy cập; chỉ đối chiếu theo nội dung chủ repo cung cấp.

## Nguồn (xác minh 2026-11-21)

- Anthropic, *The Claude Code guide for startups* (2026-08-20): <https://claude.com/resources/articles/claude-code-guide-for-startups>
- Claude Code docs: <https://code.claude.com/docs/en/best-practices> · <https://code.claude.com/docs/en/memory> · <https://code.claude.com/docs/en/permission-modes> · <https://code.claude.com/docs/en/goal> · <https://code.claude.com/docs/en/worktrees> · <https://code.claude.com/docs/en/sub-agents> · <https://code.claude.com/docs/en/hooks> · <https://code.claude.com/docs/en/skills> · <https://code.claude.com/docs/en/changelog>
