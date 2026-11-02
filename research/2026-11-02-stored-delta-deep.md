---
title: Đề xuất từ catalog seeker19110/stored (e8b3831..5f9e546) — đọc mã kỹ, prompt cache, EGM
kind: research
updated: 2026-11-02
---

# Đề xuất từ stored (đợt 2026-11-01/02)

Bổ sung cho [`2026-11-01-stored-delta-upgrade.md`](2026-11-01-stored-delta-upgrade.md) (không sửa file đó). Ký hiệu `NN §x` là chuyên mục NN,
mục x của catalog. **File này chỉ là đề xuất**: chưa thêm ID, chưa sửa `framework/`; phiên X-Templates tự xác minh, cấp số ID và ghi
`CHANGELOG.md` khi nâng cấp.

## 1. Phạm vi

- `seeker19110/stored` `e8b3831..5f9e546` (PR #96–#99, 1–2/11/2026): đọc mã kỹ Kilo Code (01 §3j), Wan2.2 và palmier-pro (19 §3c),
  img2threejs (22 §9f); hồ sơ dự án đích X-Company (23 §8c); kiểm bài đăng prompt caching (03 §8h); kiểm ảnh
  `google/elephant-goldfish-model` (20 §3u).
- 9 dòng (`XT-H-052…060` phía stored, `data/xt-handoff.json`); ID đối chiếu bằng grep `framework/` ở commit `ff23040`.
- Thống kê: nông hơn 6 · chưa có 0 · sâu hơn 3 · không thêm 0. Mọi đề xuất mức SHOULD.
- Đợt trước (`2026-11-01-stored-delta-upgrade.md`): đã áp `XT-H-019/020/021/022/024/026` (CHANGELOG `ff23040`); các dòng nông hơn/chưa có còn lại
  vẫn chờ. `XT-H-054` gộp vào `XT-H-030` của đợt trước.

## 2. Bài học stored → ID

| # | Bài học (stored) | ID gần nhất | Cột | Đề xuất / trạng thái |
|---|---|---|---|---|
| XT-H-052 | Prompt cache gắn với **model** và khớp theo tiền tố từng byte (`tools` → `system` → `messages`): đổi model, đổi tập tool, sửa system prompt, bật/tắt thinking hay đổi `effort` ở cấp request giữa phiên đều ghi lại cache từ đầu. Bài đăng "10,69M token chỉ $9,93" khớp số học: 88% là cache read ($0,20/1M trên Opus 5.5, 0,05× input) (03 §8h) | `LOOP-DESIGN-012`, `AI-APP-011`, `LOOP-ORCH-019`, `LOOP-ORCH-023`, `LOOP-OPT-015` | nông hơn | **Đề xuất** (SHOULD): Bổ sung cho vòng autopilot (`11-autonomous-loop/orchestration-and-subagents.md`, cạnh `LOOP-ORCH-019`): phiên chính giữ một model suốt vòng; việc rẻ giao subagent thay vì đổi model phiên chính; thay đổi chỉ dẫn giữa phiên dùng system message giữa hội thoại thay vì sửa system prompt; không thêm/bớt tool giữa phiên. `AI-APP-011` đã phủ phía ứng dụng; `LOOP-DESIGN-012` đã có "prefix ổn định, chỉ nối thêm" nhưng chưa nói đổi model/tool/effort giữa phiên cũng phá cache. Kiểm: trong log usage của một lượt autopilot dài, `cache_read_input_tokens` tăng đều qua các lượt; lượt có `cache_creation_input_tokens` gần bằng cả hội thoại được ghi lý do (đổi model/tool). |
| XT-H-053 | EGM (google/elephant-goldfish-model, 9,2k★): review **tài liệu thiết kế trước khi code** bằng subagent ngữ cảnh mới; bản Claude Code khoá persona `tools: [Read, Grep, Glob]`, `omitClaudeMd: true`, từ chối review khi harness không tạo được subagent. Vòng review có luật dừng đo được: hai lượt sạch liên tiếp (không Blocker/Major chưa xử lý; reviewer không chạy được thì lượt không sạch), trần 5 lượt, phát hiện "churn" (lỗi mới nằm đúng phạm vi bản sửa vừa áp) rồi hỏi người (20 §3u) | `LOOP-DESIGN-013`, `LOOP-ORCH-005`, `LOOP-DESIGN-011` | nông hơn | **Đề xuất** (SHOULD): Bổ sung (`11-autonomous-loop/loop-design.md`, cạnh `LOOP-DESIGN-013`): spec/ADR có quyết định khó đảo ngược được rà bởi subagent ngữ cảnh mới chỉ đọc (khi harness hỗ trợ: tool chỉ đọc + không nạp file luật dự án) **trước** khi lập task code; vòng rà dừng theo luật ghi trong spec: hai lượt sạch liên tiếp, trần lượt, churn → hỏi/ghi nợ (khớp ADR-0062 "review 1 lần theo ba mức rủi ro" ở chỗ: lượt rà spec là bước thiết kế, không phải review PR). Kiểm: PR có spec mới kèm báo cáo rà (reviewer, lượt, kết luận); `pr next` đỏ khi spec đổi mà chưa có lượt rà sạch. |
| XT-H-054 | Tín hiệu "còn sống" phải lấy từ commit cuối **chạm mã nguồn**, không từ `pushed_at` hay commit README: Wan2.2 push 21/9/2026 nhưng commit mã cuối 20/9/2025; palmier-pro push 30/10 nhưng sau 24/8 chỉ sửa `appcast.xml`; img2threejs ~20k★ trong khi lõi dừng từ 6/9 và squash merge xoá trailer. Bổ sung bằng chứng cho XT-H-030 (đang chờ) (19 §3c, 22 §9f) | `OPS-MAINT-008`, `BASE-DEP-019` | nông hơn | **Đề xuất** (SHOULD): Gộp vào đề xuất XT-H-030 (`15-operations/maintenance-and-lifecycle.md`): kiểm bảo trì dùng `git log -1 -- <glob mã nguồn>` của nhánh mặc định, ghi rõ khi chỉ docs/metadata đổi; ghi tuổi repo và việc lịch sử bị squash/gộp trước khi dùng sao hay tỉ lệ trailer làm bằng chứng. Kiểm: script so `pushed_at` với commit mã cuối, lệch > 90 ngày → cảnh báo trong báo cáo chọn phụ thuộc. |
| XT-H-055 | License **mã nguồn** khác license **bản cài**: palmier-pro `LICENSE` GPL-3.0 (GitHub báo GPL) nhưng README và `BINARY_LICENSE.md` ghi mọi bản sau v0.7.6 là độc quyền, nút Download phát bản đóng; Sparkle (`SUFeedURL` + `SUPublicEDKey` cứng trong `Info.plist`) đưa người tự build bản GPL lên bản đóng như một bản cập nhật có chữ ký (19 §3c) | `CMP-LIC-021`, `PRF-DESK-002`, `CMP-LIC-004` | nông hơn | **Đề xuất** (SHOULD): Bổ sung `CMP-LIC-021` (`16-compliance-privacy/licensing-and-ip.md`): ghi riêng license mã nguồn và license bản phát hành (đọc README/FAQ/`BINARY_LICENSE`/EULA và asset release), lệch → `review`. Bẫy cho `PRF-DESK-002` (`02-profiles/desktop-app.md`): fork/tự build app đã đổi license phải gỡ hoặc trỏ lại feed cập nhật và khoá ký trước lần chạy đầu. Kiểm: `rg 'SUFeedURL\|SUPublicEDKey\|updater.*endpoints'` trong bản fork trỏ hạ tầng của dự án. |
| XT-H-056 | Mã **tải rồi import mã bên thứ ba lúc chạy** không ghim: Wan2.2 `--enable_tts` chạy `git clone --recursive` CosyVoice từ `main` vào thư mục hiện hành, thêm vào `sys.path` rồi import (`wan/speech2video.py:697-707`); `torch.load` không `weights_only` ở 5 chỗ trong khi cho phép `torch>=2.4` (19 §3c) | `SEC-SUPPLY-032`, `PRF-DATA-013`, `CMP-LIC-021` | nông hơn | **Đề xuất** (SHOULD): Mở rộng `SEC-SUPPLY-032` (`12-security/supply-chain.md`, hiện chỉ nói `trust_remote_code`) sang mọi đường tải-rồi-import lúc chạy (`git clone`, `pip install`, tải `.py`): ghim commit/hash hoặc cài sẵn có ghim; `torch.load` có `weights_only=True` hoặc torch ≥ 2.6. Kiểm: `rg -n 'git clone\|sys\.path\.(append\|insert)\|torch\.load\(' src` — mỗi chỗ có ghim hoặc `weights_only=True`. |
| XT-H-057 | Đường tắt telemetry bị **ghi đè**: Kilo `KILO_TELEMETRY_LEVEL` thắng `experimental.openTelemetry: false`; VS Code suy ra từ cài đặt toàn IDE, plugin JetBrains gắn cứng `"all"` (có test khẳng định); không mã nào đọc `DO_NOT_TRACK`. "Không cần API key" = mặc định đi qua gateway của nhà cung cấp (`ai-gateway.kilo.ai`, key `anonymous`) (01 §3j) | `SEC-INFRA-027`, `LOOP-HARNESS-030`, `AI-OBS-009` | nông hơn | **Đề xuất** (SHOULD): Bổ sung bảng công tắc của `SEC-INFRA-027` (`12-security/infrastructure-and-network.md`): mỗi công cụ ghi **mọi** đường bật/tắt theo client (CLI, VS Code, JetBrains) và thứ tự ưu tiên env > config; ghi endpoint model mặc định khi chưa có key. Kiểm: bảng có cột 'client' và 'endpoint mặc định'; công cụ có client ép telemetry → ghi chặn ở tường lửa hoặc không dùng client đó. |
| XT-H-058 | Máy chủ MCP cục bộ có tool **tốn tiền** hoặc gửi dữ liệu ra ngoài: palmier-pro `127.0.0.1:19789` bật mặc định, kiểm Origin nhưng **không token**, `generate_video` ("costs real money") và `send_feedback` không xác nhận; Kilo cài MCP từ marketplace ghi lệnh `command` vào cấu hình không kiểm hash (19 §3c, 01 §3j) | `SEC-INFRA-011`, `UX-AI-004`, `LOOP-STOP-023` | sâu hơn | Đã có: `SEC-INFRA-011` buộc token cho daemon/MCP cục bộ; `UX-AI-004` buộc xem trước hành động có tác dụng phụ; `LOOP-STOP-023` cấm agent tự cài MCP giữa phiên. Chỉ thêm palmier-pro, Kilo vào ví dụ bẫy. |
| XT-H-059 | Cổng **tất định trước** phán xét của model: img2threejs `divine_eye.py` loại cứng khi IoU bóng < 0,85 hoặc lệch tỉ lệ > 0,08 trước khi VLM chấm, VLM chỉ phân xử tín hiệu mềm; nhưng điểm cuối do **chính agent viết mã tự ghi** (`append_review.py --ai-vision-score`), người dùng báo không tái lập được demo (22 §9f) | `LOOP-DESIGN-013`, `AI-GUARD-010`, `CMP-AUDIT-020` | sâu hơn | Đã có: tách người sinh/người chấm (`LOOP-DESIGN-013`), không dùng cùng model tự chấm (`AI-GUARD-010`), điểm tự chấm chỉ là tín hiệu (`CMP-AUDIT-020`). |
| XT-H-060 | Installer skill **ghim tag** (img2threejs `bin/img2threejs.mjs` mặc định `v2.0.0`, từ chối nhánh và SHA ngắn) và CI chặn `SKILL.md` vượt 4.300 từ (22 §9f) | `WF-DOC-019`, `LOOP-CTX-013`, `XC-DOCAI-009` | sâu hơn | Đã có: lệnh cài ghim phiên bản (`WF-DOC-019`), SKILL.md nạp theo tầng và giới hạn độ dài (`LOOP-CTX-013`). |

## 3. Thứ tự gợi ý (lợi ích / công sức)

1. **XT-H-056** — một regex mở rộng phạm vi `SEC-SUPPLY-032` vừa thêm (tải-rồi-import lúc chạy, `torch.load` không `weights_only`): rẻ, cùng nhà.
2. **XT-H-052** — luật "giữ một model suốt vòng chính" cạnh `LOOP-ORCH-019`/`LOOP-DESIGN-012`; kiểm bằng log usage có sẵn của phiên.
3. **XT-H-057** — thêm cột "client" và "endpoint mặc định khi chưa có key" vào bảng công tắc của `SEC-INFRA-027`.
4. **XT-H-055** — tách license mã nguồn/bản phát hành ở `CMP-LIC-021`; bẫy feed cập nhật cho fork app desktop đã đổi license.
5. **XT-H-053** — bước rà spec/ADR bằng subagent ngữ cảnh mới với luật dừng (hai lượt sạch, trần, churn); cân nhắc ADR vì chạm quy trình
   thiết kế (khác review PR theo ADR-0062).
6. **XT-H-054** — gộp vào việc của `XT-H-030` (kiểm bảo trì theo commit mã nguồn, không theo `pushed_at`).

## 4. Lưu ý

- `XT-H-053` lấy từ `google/elephant-goldfish-model` (9,2k★, Apache-2.0): bản Claude Code khoá persona reviewer bằng `tools: [Read, Grep, Glob]`
  và `omitClaudeMd: true`; bản cho host khác chỉ dặn bằng lời. Câu "thousands of Google engineers" trong README chưa xác minh.
- `XT-H-052` dựa trên tài liệu prompt caching chính thức (cache gắn model, khớp tiền tố từng byte); giá trong bài đăng gốc khớp bảng giá
  nhưng nguồn case study chưa xác minh.
- Số liệu sao/ngày commit là ngày đọc 1–2/11/2026; mục ghi **(chưa xác minh)** ở stored giữ nguyên mức đó.
- Đợt trích kế tiếp của `stored` bắt đầu từ commit sau `5f9e546`.
