# ADR-0049: `/audit` và `/research` dùng tool Workflow khi người gõ trực tiếp; không bật `ultracode` mặc định

- **Trạng thái:** Đã chấp nhận (chủ repo 2026-10-25: "những chỗ nên dùng thì áp dụng, tự bật khi đã cho phép"; D-184…D-190
  — review #265 sáu lượt thu hẹp phạm vi; phiên chính tự duyệt, ADR-0008)
- **Trạng thái triển khai:** Đã triển khai — bản 3.26.0: `.claude/skills/audit/SKILL.md` §3, `.claude/skills/research/SKILL.md`
  bước 3.
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
   Agent, và ở Auto bỏ hộp duyệt lần chạy đầu; Claude tự lập workflow cho mọi task đáng kể (hiểu, sửa, kiểm) — mọi task tốn
   token và thời gian hơn.
3. Model của agent trong workflow chọn theo thứ tự như subagent; `model` truyền trong script là tham số theo lần gọi (thắng
   frontmatter). `agentType` (dùng agent tuỳ biến `.claude/agents/*.md`) có trong skill `/workflow-authoring`, không có ở hai
   trang trên — quan sát 2026-10-25 (Claude Code 2.1.310); `maxTurns` của frontmatter có áp cho agent của workflow: (chưa xác minh).
4. Mô tả tool Workflow trong Claude Code 2.1.310 (đọc 2026-10-25; trang công khai không ghi, cũng không nói ngược) liệt kê
   opt-in: từ khoá `ultracode`, ultracode bật cho phiên, người yêu cầu trực tiếp, "The user invoked a skill or slash command
   whose instructions tell you to call Workflow", người gọi workflow đã lưu theo tên. Opt-in khác duyệt quyền: chế độ Auto vẫn
   hỏi lần chạy đầu (ghi đồng ý vào settings người dùng), Manual hỏi mỗi lần; gói Pro phải bật ở `/config`.
5. Tài liệu nêu đúng dạng việc hợp: quét toàn codebase, nghiên cứu đối chiếu chéo nguồn, rà chéo đối kháng.

Ghi chú 2026-10-21 (dòng 91, TD-6) nói Workflow "chỉ ở phiên tương tác (không qua `-p`/lịch)" — rộng quá: chỉ **từ khoá** không
kích hoạt ở đó.

## Phương án đã xét

- **A — giữ nguyên** (subagent 2–4 cụm; Workflow chỉ khi người gõ `ultracode`): bỏ phí rà đối kháng song song đúng nơi tài liệu khuyên.
- **B — skill fan-out dùng Workflow khi người gõ trực tiếp, cùng luật nhánh subagent, dự phòng subagent** (chọn; lượt 1–2 có cả nợ review của `/complete` và luật người xác minh riêng — bỏ ở lượt 3, D-187).
- **C — `"ultracode": true` trong `.claude/settings.json`**: biến cả việc cơ học pha build thành workflow — trái ADR-0033,
  D-142; tốn token ở mọi task không có số đo. (Ultracode chỉ gỡ giới hạn subagent của tool Agent, không phải trần 5 của
  `LOOP-ORCH-008` — trần đó do khuôn "lô ≤ 5" của script giữ.) Loại.

## Quyết định

1. Hai chỗ dùng Workflow: `/audit` §3–4 (quét theo cụm + xác minh đối kháng 🔴/🟠) và `/research` bước 3 (≥ 3 mục độc lập +
   một agent đối chiếu chéo). Người gõ skill là đã opt-in (Bối cảnh 4) — **không cần bật tay** `ultracode`. Điều kiện máy quyết
   được: chỉ khi người **gõ trực tiếp** `/audit` hoặc `/research` trong phiên tương tác (người có mặt để duyệt lần đầu); gọi
   từ `/autopilot` hay `/complete` → nhánh subagent (hộp duyệt lần đầu sẽ treo vòng không hỏi người).
2. Khuôn (nhà: `/audit` §3) **cùng luật với nhánh subagent, chỉ khác cách chạy**: agent chỉ đọc qua `agentType`
   `reviewer` (`tools` không `Edit`/`Write`/`Agent`; `/research` dùng `researcher`; không dùng `Explore` — không có frontmatter repo); người xác
   minh đúng như `/audit` §4 (reviewer khác agent đã tìm, model khác nếu được), không nhận lý luận của người tìm; **lô ≤ 5**
   đồng thời, một workflow một lúc; workflow chỉ trả dữ liệu — phiên chính gộp, đánh ID, ghi sổ, `loop decide`, sửa, push.
3. Không lọc `null`, **không tự chạy lại** (`null` có thể do người dừng run/agent ở `/workflows`; chạy lại qua tool Agent là đổi
   tool cho cùng hiệu ứng, `LOOP-STOP-025`): cụm `null`/INCONCLUSIVE → ghi nhóm `chưa quét` (xoá SHA/Ngày, kể cả nhóm đang
   `đã quét` ở SHA cũ khi delta); xác minh `null`/INCONCLUSIVE → Trạng thái `mở`, giữ mức, Ghi chú `chưa xác minh` (`audit
   check` chỉ nhận `mở`/`đã sửa`/`chấp nhận`/`bác bỏ`), không tính là đã xác minh; lệnh bị chặn bên trong agent → mục đó
   `chưa biết:`, cụm khác vẫn dùng. Báo người (đang có mặt), chạy lại chỉ khi người bảo. Người chọn No, `deny`/bộ phân loại chặn
   lời gọi Workflow → dừng, báo người. Chỉ khi không có tool Workflow → nhánh subagent.
4. Không dùng Workflow cho nợ review của `/complete` (đơn vị là PR/lát, review theo `LOOP-ORCH-005` và hàng `review_debt` —
   ghép vào cụm nhóm làm mất dấu vết lát hỏng; review #265 lượt 3), task build, `/review` một PR, `/optimize`, `release-check`,
   việc cơ học. **Không bật ultracode cả phiên** (`/effort ultracode`, `--effort ultracode`, setting `ultracode`) cho phiên
   `/autopilot` hay `/complete`: ultracode áp cho mọi task (kể cả nợ review và sửa mã) và ở Auto bỏ hộp duyệt lần đầu — mở lại
   đúng các đường mục này đóng (ADR-0033, D-142, D-187). Muốn Workflow ở pha harden: người tự gõ `/audit` hoặc `/research`;
   phiên ultracode chỉ cho việc người tự điều khiển ngoài vòng lặp, tắt bằng `/effort ultracode off`.

## Hệ quả

- Audit/research nhiều mục do người gõ chạy song song có xác minh đối kháng mà không phải bật `ultracode`; kết quả nằm ngoài
  context phiên chính. Workflow không thay bước nào của `/complete` (bước 2 gồm cả nợ review theo PR/lát; `/audit` ghi SHA
  quét = HEAD nên một `/audit` thay bước 2 làm hàng `review_debt` PASS rỗng — review #265 lượt 5).
- Chi phí token tăng ở các bước này (chưa đo — đo bằng `/workflows` ở lần chạy đầu, `LOOP-ORCH-020`); lợi ích chất lượng chưa có số.
- Nhà luật `LOOP-ORCH-*` (`orchestration-and-subagents.md`) chưa có dòng về Workflow — thư mục sát trần byte (ADR-0043); khuôn
  nằm ở `/audit` §3 tới khi có chỗ.
- Chưa xác minh: frontmatter `maxTurns` và `effort` áp cho agent của workflow; guard `PreToolUse:Bash` áp cho agent của workflow
  (reviewer PR này quan sát có, chưa tái hiện độc lập).

## Đường lùi

Xoá đoạn Workflow ở hai skill; hành vi về lại subagent tay.
