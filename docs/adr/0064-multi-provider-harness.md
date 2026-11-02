# ADR-0064: Harness đa nhà cung cấp — một lõi chính sách, adapter theo công cụ, vòng lặp ngoài, sandbox là ranh giới

- **Trạng thái:** **Đề xuất (nháp)** — chờ chủ dự án duyệt; chưa ghi D-NNN vì đổi cấu trúc harness (AGENTS.md §4: kiến
  trúc thêm ADR; chủ dự án yêu cầu "viết ADR nháp, research trước" 2026-11-02).
- **Trạng thái triển khai:** Chưa bắt đầu. Khi duyệt → PLAN riêng, mỗi lát một PR (§Quyết định, lát A–E).
- **Ngày:** 2026-11-02.
- **Nghiên cứu:** [`research/2026-11-02-multi-provider-harness.md`](../../research/2026-11-02-multi-provider-harness.md)
  (7 công cụ + chuẩn AGENTS.md + sandbox độc lập; mọi dữ kiện ghi ngày 2026-11-02, mục chưa xác minh ở §6 của file đó).
- **Liên quan:** ADR-0002 (fail-open luồng, fail-closed hành động nguy hiểm), ADR-0009 (một phiên, Stop hook), ADR-0018/0019
  (guard không hỏi người), ADR-0054 (`guard-check` là điểm nghẽn chung), ADR-0063 (tập con chuẩn), `XC-DOCAI-002` (cầu nối
  file hướng dẫn), `LOOP-HARNESS-022` (sandbox OS), `LOOP-ORCH-005` (reviewer năng lực cao hơn người viết),
  AUD-SEC-329 (mã lý do làm khoá chính), AUD-HAR-198 (matcher MCP).

## Bối cảnh và vấn đề

Harness của khung hôm nay gắn với Claude Code ở bốn chỗ: (1) `.claude/settings.json` khai hook theo tên sự kiện và hợp đồng
JSON của Claude Code (`tool_name`/`tool_input`, `hookSpecificOutput.permissionDecision`, `onFailure: block`,
`CLAUDE_PROJECT_DIR`); (2) vòng "chạy đến khi xong" dựa vào Stop hook + PreCompact checkpoint (ADR-0009); (3) skill
`SKILL.md` và subagent frontmatter là định dạng của Claude Code; (4) `doctor`, `install.py`, `harness-check` chỉ kiểm bộ
`.claude/`. Phần còn lại đã trung lập: `AGENTS.md` (với cầu `@AGENTS.md` trong `CLAUDE.md`), `xt.yaml` + `dev-task.sh`,
toàn bộ `xt.py` (loop, pr, merge-check, release-check, audit), CI/ruleset/`pr-steward` phía máy chủ, và lõi guard là Python
thuần đọc JSON với cửa trung lập `xt.py guard-check -- <lệnh>` (ADR-0054).

Nghiên cứu 2026-11-02 cho thấy mẫu số chung đủ rộng: 6/7 công cụ (Claude Code, Codex CLI, Gemini CLI, Cursor, Copilot CLI,
Grok Build) có hook **chặn tool call trước khi chạy** với hợp đồng gần giống nhau (JSON qua stdin; exit 2 hoặc JSON `deny`);
5/7 đọc `AGENTS.md` native; cả 7 chạy headless. Khác biệt nằm ở tên sự kiện/trường, trường quyết định, **ngữ nghĩa lỗi**
(exit code ≠ 0/2 không chặn ở 4/6; Codex không hỗ trợ `ask`; chỉ Copilot `preToolUse` fail-closed), hook kết thúc lượt chỉ
có ở 4/7, và **sandbox OS tắt mặc định ở 5/7**, không công cụ nào bọc file tool/MCP/hook. Ba công cụ (Cursor, Grok Build,
Copilot — mục cuối chưa xác minh lại) nạp thẳng `.claude/settings.json`, nên hợp đồng guard hiện tại đã vô tình là hợp đồng
đa công cụ mà không có test nào kiểm.

Câu hỏi: có nên và bằng cách nào để cùng một hàng rào máy (guard, bằng chứng, merge theo làn, điểm dừng) áp cho dự án đích
dùng agent của OpenAI, Google, xAI, Cursor, GitHub hay OpenCode — mà không chép luật ra nhiều nhà, không rời stdlib, và
không giả vờ guard là sandbox?

## Yếu tố quyết định

1. **Đúng và an toàn**: lớp nguy hiểm (xoá/ghi ngoài dự án, force-push, tắt hook, ghi tay bằng chứng, merge chưa đủ điều kiện,
   lộ bí mật) phải fail-closed **bất kể** công cụ fail-open khi hook lỗi → lõi phải in `deny` tường minh, không dựa vào exit code.
2. **Một chủ đề một nhà**: một bảng luật, một bộ test; adapter chỉ dịch tên sự kiện/trường, không chứa luật.
3. **Ràng buộc kỹ thuật của khung**: Python ≥ 3.11 stdlib, copy vào `.xtemplates/` dự án đích, test bằng payload giả, fail-open
   về luồng (ADR-0002).
4. **Không lock-in và tận dụng đa hãng**: reviewer khác hãng với người viết thoả `LOOP-ORCH-005` dễ hơn; dự án đích chọn công cụ
   theo giấy phép/giá (Codex, Gemini, Grok Build, OpenCode là OSI; Claude Code, Cursor, Copilot proprietary).
5. **Guard không phải sandbox** (`LOOP-HARNESS-022`, ADR-0054): mở rộng ra nhiều công cụ càng phải đặt ranh giới hậu quả ở
   sandbox/egress, không ở thêm luật regex (bài học AUD-SEC-180…311, ADR-0063).
6. **Chi phí bảo trì**: API hook đổi nhanh (Claude 33 sự kiện, Copilot GA 02/2026, Grok beta 05/2026) → adapter phải mỏng, có
   fixture payload theo phiên bản và mốc xét lại.

## Các phương án đã cân nhắc

1. **Giữ Claude-only** (hiện trạng): công cụ khác chỉ đọc `AGENTS.md`; hàng rào máy duy nhất là CI/ruleset/steward.
2. **Một lõi chính sách + adapter mỏng theo công cụ + sàn chung cho công cụ không hook + vòng lặp ngoài + sandbox kiểm bằng máy**.
3. **Dựa vào việc các công cụ tự nạp `.claude/settings.json`** (Cursor, Grok Build, Copilot?): không adapter, chấp nhận lệch
   ánh xạ và không kiểm.
4. **Proxy/MCP đứng giữa agent và mọi tool**: một tiến trình trung gian nhận mọi lời gọi tool rồi áp luật.

## Quyết định (đề xuất)

Chọn **phương án 2**, triển khai theo năm lát độc lập, mỗi lát một PR, lát sau không phụ thuộc lát trước trừ A:

- **Lát A — Lõi trung lập.** `guard.py` (giữ tên, vẫn một file stdlib) nhận **schema trung lập** `{"tool": "bash|edit|write|
  mcp", "command"|"path"|"tool_name", "input": {...}, "cwd", "project_dir"}` qua chế độ mới `guard.py core`, trả
  `{"decision": "allow|deny", "code", "reason"}`; mỗi luật trả `code` tường minh (đóng AUD-SEC-329); chế độ `bash|edit|mcp|
  permission` hiện có trở thành adapter Claude gọi lõi. Hợp đồng lõi là **nhà** của chính sách; `xt.py guard-check` dùng lõi.
  Đầu ra deny luôn in JSON tường minh và exit 2 cùng lúc (hai công cụ đọc theo hai cách).
- **Lát B — Adapter theo công cụ** trong `.xtemplates/harness/<tool>/`, mỗi adapter ≤ ~60 dòng Python hoặc JSON cấu hình, chỉ
  dịch: Codex (`.codex/hooks.json`, `permissionDecision: deny`; `ask` → `deny` vì Codex không hỗ trợ `ask`), Gemini CLI
  (`hooks` trong `.gemini/settings.json`, `BeforeTool`, `decision: deny`), Cursor (`.cursor/hooks.json` `version: 1`,
  `beforeShellExecution` `permission`, `failClosed: true`), Copilot CLI (`.github/hooks/xt.json`, `preToolUse`
  `permissionDecision` + `permissionDecisionReason` bắt buộc), Grok Build (`.grok/hooks/xt.json`, khoá camelCase
  `toolName`/`toolInput`, `decision: deny`), OpenCode (`.opencode/plugins/xt.ts` ~20 dòng gọi `python3 .xtemplates/scripts/
  xt.py guard-check` rồi `throw`). `install.py --harness <danh sách>` ghi adapter + **cầu nối file hướng dẫn** ≤ 5 dòng
  (`GEMINI.md`, `.cursor/rules/xt.mdc`, `.github/copilot-instructions.md`) đều trỏ `AGENTS.md` (`XC-DOCAI-002`); `CLAUDE.md`
  giữ `@AGENTS.md`. Mỗi adapter có fixture payload thật của công cụ (bản + ngày) trong `tests/fixtures/harness/<tool>/` và ca
  `autonomy-bench`.
- **Lát C — Sàn chung không phụ thuộc hook.** Git hook `pre-commit`/`pre-push` do `install.py` cài (chạy `dev-task.sh gate-fast`
  qua `commit_gate`, kiểm `ai_attribution`, chặn push nhánh chính) — áp cho mọi công cụ kể cả OpenCode và Grok (Stop không
  chặn); `xt.py guard-check --stdin` vẫn là điểm nghẽn của Gate/`Kiểm:` (LOOP-STOP-027). Wrapper shell trên `PATH` **không**
  đưa vào quyết định vì chưa xác minh công cụ nào tôn trọng `SHELL`/`PATH` (research §6) — xét lại khi có dữ kiện.
- **Lát D — Vòng lặp ngoài.** `xt.py loop run --agent claude|codex|gemini|cursor|copilot|grok|opencode` gọi agent headless
  **từng task** (`claude -p`, `codex exec`, `gemini -p`, `agent -p --force`, `copilot -p`, `grok -p`, `opencode run`), kiểm
  bằng chứng bằng `loop record`/`loop verify` giữa các lượt, dừng theo đúng điểm dừng (`defer`/`block`), ngân sách lượt theo
  `LOOP-*`. Stop hook của Claude/Codex/Copilot/Cursor là lớp **trong** tuỳ chọn; vòng ngoài là lớp chung. Mã thoát headless
  chưa xác minh ở phần lớn công cụ → vòng ngoài chỉ tin `loop verify`, không tin exit code của agent.
- **Lát E — Sandbox kiểm bằng máy.** `doctor` nhóm `sandbox` đọc cấu hình theo công cụ (Claude `sandbox.enabled` +
  `allowedDomains`; Codex `sandbox_mode` ≠ `danger-full-access`; Gemini `tools.sandbox`; Cursor `sandbox.json` + chế độ;
  Copilot `/sandbox`; Grok `--sandbox` profile; OpenCode: không có → cảnh báo đỏ "cần devcontainer/`srt`") và cảnh báo đỏ khi
  autopilot không người trực chạy ngoài sandbox; `LOOP-HARNESS-022` nâng **SHOULD → MUST@M** cho phiên không người trực
  (giữ ID). Khuyến nghị tham chiếu độc lập công cụ: `@anthropic-ai/sandbox-runtime` (`srt`, Apache-2.0, allowlist domain) hoặc
  devcontainer có egress allowlist — ghi là tham chiếu, không bắt buộc công cụ cụ thể.

Thứ tự đề xuất: A → E → B (Codex, Gemini trước vì OSI và có sandbox/hook rõ; Cursor/Copilot/Grok sau; OpenCode cuối vì cần
JS) → C → D. Skill/subagent **không** chuyển đổi trong ADR này: giữ `.claude/skills` là bản Claude; playbook trung lập là ADR
sau khi có ≥ 2 công cụ dùng thật.

Phiên bản/nguồn đã xác minh (2026-11-02): Claude Code 2.1.316 · Codex CLI 0.166.0 · Gemini CLI 0.66.0 · Cursor CLI
2026.10.22 · Copilot CLI 1.0.105 · Grok Build 1.0.70 · OpenCode 1.19.5 · sandbox-runtime 0.0.81 — URL ở research §3.
Chưa xác minh: shell tool tôn trọng `SHELL`/`PATH`; hook Cursor trong CLI; payload stdin của Copilot; mã thoát headless.

### Hệ quả

- Tốt: một bảng luật cho mọi công cụ; dự án đích chọn agent theo giấy phép/giá; reviewer khác hãng; `.claude/` hết vô tình là
  hợp đồng đa công cụ không test; đóng AUD-SEC-329 và một phần AUD-HAR-198 ngay ở lát A.
- Xấu / đánh đổi: thêm 6 adapter phải theo kịp API đổi nhanh (fixture theo phiên bản, mốc xét lại 2027-01-21 cùng
  `LOOP-DESIGN-014`); OpenCode cần một file TypeScript ngoài stdlib (giữ ≤ 20 dòng, chỉ gọi `xt.py`); vòng lặp ngoài kém mượt
  hơn Stop hook (mỗi lượt khởi động lại agent, mất context — bù bằng `loop checkpoint` + `context`); chi phí ước ~5 PR,
  mỗi PR ≤ 150 dòng mã theo luật harden.
- Nợ chấp nhận: không bọc file tool/MCP/hook bằng sandbox ở mọi công cụ (giới hạn của chính các công cụ); hook kết thúc lượt
  không có ở Gemini/Grok/OpenCode → chỉ vòng ngoài.
- Việc phải làm tiếp: PLAN riêng khi duyệt; `/research` lại 4 mục chưa xác minh trước lát B/C; cập nhật `harness-files.md`
  (bảng công cụ × hook × sandbox) và mẫu `AGENTS.md` §Cổng (git hook là sàn).

### Xác nhận

- Lát A: `python3 .claude/hooks/guard.py core < payload.json` trả `code` cho 100 % luật (test duyệt mọi mã có ≥ 1 ca);
  `tests/test_guard_corpus.py` 991 ca không đổi quyết định.
- Lát B: mỗi adapter có fixture thật + `autonomy-bench` ≥ 10 ca (5 chặn/5 cho) và test "deny tường minh khi hook lỗi".
- Lát C: repo đích mới sau `install.py`: `git commit` với `ai_attribution` vi phạm bị `pre-commit` chặn (exit ≠ 0).
- Lát D: `xt.py loop run --agent <x> --dry-run` in đúng lệnh headless; test với agent giả (script in JSON) xanh/đỏ theo bằng chứng.
- Lát E: `doctor` đỏ khi `autopilot` không người trực mà không có sandbox; xanh khi có.
- Mốc xét lại: 2027-01-21 hoặc khi một công cụ đổi hợp đồng hook (fixture đỏ).

## Ưu / nhược từng phương án

### 1. Giữ Claude-only
- Tốt: không thêm bề mặt; harness đã được kiểm kỹ (991 ca, coverage 100 %).
- Xấu: dự án đích dùng công cụ khác chỉ có "lời khai" `AGENTS.md`; ba công cụ nạp `.claude/settings.json` với ánh xạ lệch
  mà không ai kiểm; không tận dụng được reviewer khác hãng.

### 2. Lõi + adapter + sàn chung + vòng ngoài + sandbox (chọn)
- Tốt: một nhà luật, adapter mỏng dịch được; fail-closed tường minh độc lập ngữ nghĩa lỗi của công cụ; đúng tinh thần
  ADR-0054 (điểm nghẽn chung) và ADR-0063 (đóng theo lớp).
- Trung lập: thêm ~6 adapter + fixture; một file TS cho OpenCode.
- Xấu: API hook đổi nhanh; vòng ngoài kém mượt.

### 3. Dựa vào công cụ tự nạp `.claude/settings.json`
- Tốt: không làm gì thêm cho Cursor/Grok/Copilot.
- Xấu: ánh xạ do công cụ quyết (Cursor bỏ Notification/PermissionRequest; Grok chỉ PreToolUse); không phủ Codex/Gemini/
  OpenCode; không kiểm được bằng test của khung → vi phạm P1 (bằng chứng).

### 4. Proxy/MCP đứng giữa
- Tốt: một điểm chặn cho mọi tool kể cả MCP.
- Xấu: tool built-in (Bash/Edit) của mọi công cụ không đi qua MCP; cần tiến trình dài hạn, ngoài stdlib-copy; phức tạp hơn
  vấn đề cần giải.

## Thông tin thêm

- Nguồn: toàn bộ ở [`research/2026-11-02-multi-provider-harness.md`](../../research/2026-11-02-multi-provider-harness.md) §3
  (docs chính chủ 7 công cụ, registry npm, `git ls-remote`, agents.md, docs.kernel.org — xác minh 2026-11-02).
- Câu hỏi cho chủ dự án trước khi duyệt: (1) phạm vi lát B đợt đầu — Codex + Gemini (OSI, sandbox/hook rõ) hay cả 6; (2) có nâng
  `LOOP-HARNESS-022` lên MUST@M cho phiên không người trực không; (3) `.claude/` giữ là "bản Claude" hay dời luật sang
  `.xtemplates/harness/` và để `.claude/hooks` chỉ còn shim.
- Thời điểm xem lại: 2027-01-21 (cùng `LOOP-DESIGN-014`) hoặc khi fixture adapter đỏ.
