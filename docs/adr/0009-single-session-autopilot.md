# ADR-0009: Autopilot chạy một phiên đến khi xong — compaction có checkpoint, việc cần người dồn cuối phiên

- **Trạng thái:** Đã chấp nhận; công thức trần vòng (§Quyết định 3) bị thay bởi ADR-0012 rồi ADR-0022 (hiện hành `max(40, 8 × task chưa làm)`)
- **Trạng thái triển khai:** Đã triển khai (`scripts/xt.py` `loop defer`, `loop checkpoint`, `loop init --single-session`,
  verdict `done-pending-human`, `hook-stop` đọc `permission_mode`; `.claude/hooks/pre-compact.sh` + `PreCompact` trong
  `.claude/settings.json`; test `tests/test_xt_cli.py`, `tests/test_xt_core.py`, `tests/test_hooks.py`)
- **Ngày:** 2026-10-15

## Bối cảnh

Chủ repo hỏi (2026-10-15) "làm sao để hoàn tất chỉ trong 1 phiên khi bắt đầu chạy auto?" rồi duyệt cả 4 đề xuất. Khung
đang **cố ý** chia nhiều phiên: `LOOP-CTX-003` (≥ 80% context → bàn giao, dừng), `LOOP-CTX-008` (xong mảng → phiên mới),
`LOOP-CTX-012` (PLAN vượt ngân sách → chia phiên). Sau ADR-0008 (tự duyệt quyết định chuyên môn), còn bốn thứ làm phiên
đứng hoặc kết thúc:

1. Hỏi quyền tool khi người vắng — `permissions.defaultMode: auto` bị Claude Code bỏ qua ở settings dự án.
2. Ngưỡng bàn giao vì context.
3. `loop block` dừng **cả** vòng lặp dù còn việc độc lập làm được.
4. Trần vòng mặc định 50, không theo khối lượng PLAN.

Dữ kiện đã xác minh (code.claude.com/docs/en/hooks.md, 2026-10-15): PreCompact nhận `trigger` (`manual`/`auto`) và
`custom_instructions`; exit 2 hoặc `"decision":"block"` **chặn** nén (nếu nén để cứu lỗi vượt context thì request
hỏng). SessionStart có `source` = `compact` sau khi nén, nhưng ví dụ input không có `permission_mode`. Input Stop có
`permission_mode` (`default` · `plan` · `acceptEdits` · `auto` · `dontAsk` · `bypassPermissions`).

## Quyết định

1. **Compaction thay bàn giao vì context.** Hook `PreCompact` → `xt.py loop checkpoint` ghi `state.json.checkpoint`
   (task đang làm, lệnh kiểm cuối + exit code, file chưa commit, lỗi lặp). Hook luôn exit 0, không in quyết định.
   SessionStart (mọi `source`, gồm `compact`) đã chạy `loop status`; `loop status` in thêm checkpoint. Bàn giao chỉ khi
   ≥ 80% **trần máy** (vòng/giờ/tiền).
2. **`loop defer`.** Việc cần người (task PLAN hoặc ID mục blueprint) bị bỏ qua để làm việc khác. Hết việc tự làm được
   → verdict `done-pending-human` (Stop hook cho dừng một lần, liệt kê việc chờ). `loop resume` đưa việc chờ lại hàng
   làm. Việc chờ đã được tick kèm bằng chứng (hoặc mục blueprint đã đạt) thì không tính. `loop block` chỉ dùng khi mọi
   việc còn lại phụ thuộc điểm dừng. Máy từ chối defer khi lý do rỗng, ID không còn mở (gõ nhầm/đã xong), hoặc task
   đang lỗi (`last_failure_task`) — defer không phải lối né trần "lỗi lặp lần 3 → BLOCKED".
3. **`loop init --single-session`.** Trần vòng `max(20, 4 × (task chưa làm + MUST mở của blueprint))` nếu không khai `--max-iterations`; Stop
   hook nhắc "context đầy → để compaction, không bàn giao".
4. **Chế độ quyền.** Stop hook ghi `permission_mode` vào state và cảnh báo trong lý do chặn khi là `default`/`plan`/
   `acceptEdits`. Skill `/autopilot` có bước 0 kiểm chế độ và hook. Không tự đổi chế độ: chỉ người bật được (cờ CLI
   hoặc settings người dùng) — đúng ADR-0002.
5. **Mục checklist:** `LOOP-CTX-003` → `LOOP-CTX-017` (MUST); `LOOP-CTX-008` → `LOOP-CTX-018`; `LOOP-CTX-012` →
   `LOOP-CTX-019` (vượt ngân sách thì thu hẹp phạm vi bằng `D-NNN`, không chia phiên); mới `LOOP-CTX-020` (chế độ quyền),
   `LOOP-STOP-021` (`loop defer`); `LOOP-CTX-009` giữ ID, nơi ghi checkpoint đổi từ PROGRESS sang `state.json`.
6. `inactive` sau khi vòng kết thúc báo verdict cuối, để phiên sau thấy ngay "còn việc chờ người".

## Lý do

- Context đầy là giới hạn của **bộ nhớ làm việc**, không phải của tiến độ: trạng thái thật đã nằm trên đĩa (PLAN,
  evidence, PROGRESS, DECISIONS). Cắt phiên vì context làm vòng lặp đứng tới khi có người mở phiên mới.
- Checkpoint ghi vào `state.json` (gitignore) thay vì PROGRESS: hook tự sửa file đã commit sẽ làm bẩn cây làm việc và
  đua với agent; PROGRESS vẫn do agent cập nhật sau mỗi task.
- `defer` giữ đúng điểm dừng về hành động (người vẫn làm việc đó) nhưng dồn chúng thành **một** lần can thiệp.
- Trần vòng theo PLAN: 50 vòng là quá ít cho PLAN lớn và quá nhiều cho PLAN 3 task.

## Các phương án đã cân nhắc

- **PostCompact hook tiêm ngữ cảnh**: PostCompact không có decision control/ngữ cảnh; SessionStart(compact) đã có sẵn
  và đã chạy. Loại.
- **Chặn auto-compact để buộc bàn giao** (giữ hành vi cũ): ngược yêu cầu; chặn nén khi đã vượt context làm request hỏng.
- **Hook tự đặt `permissions.defaultMode`**: Claude Code bỏ qua ở settings dự án; hook tự nâng quyền là vi phạm ADR-0002.
- **Song song nhiều phiên/Routine để "xong nhanh"**: không phải một phiên; tranh chấp file. Ngoài phạm vi.

## Hệ quả

- Tốt: một PLAN chạy tới `done`/`done-pending-human` trong một phiên khi người bật `--permission-mode auto`; việc cần người
  gom một lần.
- Xấu/nợ: máy không phân biệt được việc defer có thật là điểm dừng về hành động hay không (agent có thể defer task khó
  chưa từng chạy Gate) — kiểm bằng review: báo cáo `done-pending-human` liệt kê từng việc chờ + lý do. Chất lượng có thể giảm sau nhiều lần nén (đo theo `LOOP-CTX-015`); phiên rất dài tốn tiền — trần tiền
  (`--max-budget-usd`) vẫn là cổng. Chưa đo được context đang dùng từ hook (SessionStart có `context_tokens` theo docs,
  chưa dùng). Dự án đã cài khung: chạy lại `install.py` để `merge_hooks` thêm `PreCompact`.
