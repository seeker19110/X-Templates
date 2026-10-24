# ADR-0044: Reviewer năng lực cao hơn người viết thay cho "khác họ model"

- **Trạng thái:** Đã chấp nhận (chủ repo 2026-10-24: "có thể cùng họ nhưng khác effort cũng được, review phải có năng
  lực cao hơn"; phiên chính tự duyệt thiết kế theo D-161)
- **Trạng thái triển khai:** Đã triển khai — `scripts/xt.py` (thang năng lực trong `pr reviewed --clean`, cờ
  `--reviewer-effort`/`--author-effort`, khoá `author_effort`/`reviewer_effort` của xt.yaml, `ci-check`);
  `.claude/agents/reviewer-alt.md` (`model: opus`, `effort: max`), `executor-deep.md` (`effort: high`).
- **Ngày:** 2026-10-24
- **Làm rõ:** D-045 ("khác họ" — phần so họ bị thay), ADR-0029 mục 3 (`reviewer-alt` họ khác — bị thay), D-160 (chuỗi
  model phiên chính Fable → Opus → Sonnet), `LOOP-ORCH-005`.

## Bối cảnh

D-045 đòi reviewer khác **họ** model với người viết, hiểu "họ" là Opus/Sonnet/… Hai hệ quả xấu: (1) Opus và Sonnet cùng
nhà cung cấp nên "khác họ" không bảo đảm khác điểm mù; (2) luật cho phép reviewer **yếu hơn** người viết —
`reviewer-alt` (Sonnet) chấm diff của `executor-deep` (Opus) và của phiên chính. Người chấm yếu hơn bỏ sót lỗi mà người
viết mạnh hơn gây ra. Frontmatter subagent của Claude Code nhận `effort: low|medium|high|xhigh|max` và `model: fable`
(code.claude.com/docs/en/sub-agents, xác minh 2026-10-24), nên "cùng model, effort cao hơn" làm được bằng cấu hình.

## Phương án đã xét

1. **Giữ "khác họ"** (D-045). Đơn giản; nhưng cho phép reviewer yếu hơn — trái yêu cầu chủ repo.
2. **Năng lực cao hơn, so theo thang (bậc model, effort)**: Haiku < Sonnet < Opus < Fable, rồi low < … < max; khác bậc
   thì bậc quyết, cùng họ thì effort reviewer phải cao hơn và cả hai phải khai; khác nhà cung cấp (không xếp hạng được)
   nhận như D-045. Máy kiểm được, giữ đường cho reviewer ngoài Claude.
3. **Năng lực cao hơn và bắt buộc khác nhà cung cấp**. Chặt nhất nhưng `pr-review.yml` (claude-code-action) chỉ chạy
   Claude, phiên khung không có reviewer ngoài — mọi PR làn chuẩn sẽ kẹt.

## Quyết định

Chọn **phương án 2**. `pr reviewed --clean` (và cấu hình `author_model_family`/`reviewer_model_family` khi `ci-check`)
từ chối khi reviewer không cao hơn người viết theo thang. Gán tầng: `reviewer` (Opus) chấm diff của `executor` (Sonnet);
`reviewer-alt` (Opus, effort `max`) chấm diff của `executor-deep` (Opus, effort `high`) và phiên chính; phiên chính chạy
Fable thì giao `reviewer-alt` với `model: fable` (effort `max` vẫn cao hơn phiên chính ở effort thấp hơn). Không có
reviewer nào cao hơn (phiên chính Fable@max) → reviewer khác nhà cung cấp, không có thì `pr reviewed --inconclusive`.

## Hệ quả

- Tốt: người chấm luôn mạnh hơn hoặc ngang bậc mà nghĩ sâu hơn người viết; thang ghi trong một hàm, test được.
- Xấu: review của `reviewer-alt` đắt hơn (Opus@max thay Sonnet); cùng họ phải khai effort hai phía — khai sai là lời
  khai, máy không đo được effort thật (như model, D-045 cũng tin lời khai).
- Nợ: khác nhà cung cấp vẫn nhận mà không xếp hạng; thêm model Claude mới phải thêm vào thang (tên lạ → không bậc → coi
  như khác nhà cung cấp nếu khác họ).
- Đường lùi: revert PR này; ADR này đổi trạng thái "Bị thay bởi ADR-NNNN".
