# ADR-0049: Skill fan-out (`/audit`, `/complete` nợ review, `/research`) tự dùng tool Workflow khi có; không bật `ultracode` mặc định

- **Trạng thái:** Đã chấp nhận (chủ repo 2026-10-25: "những chỗ nên dùng thì áp dụng, tự bật khi đã cho phép"; D-184; phiên
  chính tự duyệt, ADR-0008)
- **Trạng thái triển khai:** Đã triển khai — bản 3.26.0: `.claude/skills/audit/SKILL.md` §3, `.claude/skills/complete/SKILL.md`
  bước 2, `.claude/skills/research/SKILL.md` bước 3.
- **Ngày:** 2026-10-25
- **Làm rõ:** ADR-0033/ADR-0037 (pha build tối giản, không reviewer ở build — giữ nguyên), D-142 (không song song worktree —
  giữ nguyên: workflow ở đây chỉ đọc), `LOOP-ORCH-001/003/005/008`, TD-6 của
  `research/2026-10-21-next-level-speed-automation-quality.md`.

## Bối cảnh

Claude Code có tool **Workflow** (script JS điều phối nhiều subagent, chạy nền, resume trong phiên) và cài đặt **ultracode**
(phiên tự lập workflow cho mọi task đáng kể). Nguồn sống, đọc 2026-10-25: <https://code.claude.com/docs/en/workflows.md>,
<https://code.claude.com/docs/en/model-config.md>:

1. Opt-in một task: từ khoá `ultracode` gõ tay hoặc lời yêu cầu trực tiếp ("use a workflow"); từ khoá **không** kích hoạt qua
   `-p`, prompt SDK không gắn nguồn người, task lịch, webhook/bình luận PR. Bản thân Workflow chạy được ở `-p`/SDK khi có rule
   allow `Workflow`, chế độ auto/bypass hoặc hook trả allow. Chế độ Auto hỏi duyệt lần chạy đầu một lần (ghi vào settings người dùng).
2. Ultracode cả phiên: `/effort ultracode` (giữ mức effort hiện có, v2.1.284+), `claude --effort ultracode` (khởi động ở
   `xhigh`), hoặc setting `"ultracode": true`. Bật nó **gỡ** cảnh báo "Large workflow" và giới hạn subagent đồng thời của tool
   Agent; mọi task tốn token và thời gian hơn.
3. Model của agent trong workflow chọn theo thứ tự như subagent; `agentType` dùng agent tuỳ biến (frontmatter `model`/`tools`).
4. Tài liệu nêu đúng dạng việc hợp: quét toàn codebase, nghiên cứu đối chiếu chéo nguồn, rà chéo đối kháng.

Ghi chú 2026-10-21 (dòng 91, TD-6) nói Workflow "chỉ ở phiên tương tác (không qua `-p`/lịch)" — rộng quá: chỉ **từ khoá** không
kích hoạt ở đó.

## Phương án đã xét

- **A — giữ nguyên** (subagent 2–4 cụm; Workflow chỉ khi người gõ `ultracode`): bỏ phí rà đối kháng song song đúng nơi tài liệu khuyên.
- **B — skill fan-out tự dùng Workflow khi có, dự phòng subagent** (chọn).
- **C — `"ultracode": true` trong `.claude/settings.json`**: biến cả việc cơ học pha build thành workflow — trái ADR-0033,
  D-142; gỡ trần đồng thời mà `LOOP-ORCH-008` cần; tốn token không có số đo. Loại.

## Quyết định

1. Ba chỗ dùng Workflow: `/audit` §3–4 (quét theo cụm + xác minh đối kháng 🔴/🟠), `/complete` bước 2 (nợ review theo cụm),
   `/research` bước 3 (≥ 3 mục độc lập + một agent đối chiếu chéo). Skill do người gọi chỉ dẫn gọi Workflow là opt-in — **không
   cần bật tay** `ultracode`.
2. Khuôn bắt buộc: agent **chỉ đọc** qua `agentType` (`reviewer`/`Explore`/`researcher` — frontmatter giữ `model`, `tools`
   không `Edit`/`Write`/`Agent`, `maxTurns`), chạy theo **lô ≤ 5** đồng thời; người xác minh không nhận lý luận của người tìm;
   workflow chỉ trả dữ liệu — phiên chính gộp, đánh ID, ghi sổ, `loop decide`, sửa, push.
3. Không có tool, bị từ chối hoặc lỗi → nhánh subagent cũ; kết quả như nhau về sổ/`audit check`.
4. Không dùng Workflow ở pha build, `/review` một PR, `/optimize`, `release-check`, việc cơ học. Ultracode cả phiên là lựa
   chọn của người cho phiên harden lớn (`/effort ultracode`, tắt bằng `/effort ultracode off`), không đặt trong settings của khung.

## Hệ quả

- Audit/nợ review/research nhiều mục chạy song song có xác minh đối kháng mà không phải bật gì; kết quả nằm ngoài context phiên chính.
- Chi phí token tăng ở các bước này (chưa đo — đo bằng `/workflows` ở lần chạy đầu, `LOOP-ORCH-020`); lợi ích chất lượng chưa có số.
- Chưa xác minh: lệnh Bash trong agent của workflow có qua guard repo hay không (tài liệu: "cùng kiểm tra quyền"); `/autopilot`
  tự gọi `/audit delta` (không do người gõ) có tính là opt-in không — không thì rơi về nhánh subagent.

## Đường lùi

Xoá đoạn Workflow ở ba skill; hành vi về lại subagent tay.
