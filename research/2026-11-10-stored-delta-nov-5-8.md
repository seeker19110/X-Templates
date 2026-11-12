---
title: Đề xuất từ stored PR119–149 — đợt 5–8/11/2026, XT-H-117…125
kind: research
updated: 2026-11-10
---

# Đề xuất từ stored: connector MCP, tên chuẩn dependency, rà thiết kế khi lập kế hoạch, bộ nhớ nhiều harness, mô hình miền

Bổ sung cho [đợt mở rộng 28 chuyên mục](2026-11-02-stored-delta-28-sections.md). File này chỉ là **research note đề xuất**: chưa sửa yêu cầu trong `framework/`, chưa cấp ID mới, chưa đổi mức hiện có và chưa triển khai công cụ.

## 1. Phạm vi và cách đối chiếu

- Nguồn: `seeker19110/stored` từ `79c8635` đến merge [`82ab9b2`](https://github.com/seeker19110/stored/commit/82ab9b2f880ca067a11f58bdaa68fe254b621d69) ngày 2026-11-10 (PR #119…#149). Catalog hiện có 1074 hồ sơ; các mục liên quan: 06 §7z–§7zb, 10 §6h, 19 §3h, 20 §3za–§3zb, 22 §9k, 24 §6c.
- Bàn giao máy đọc: [XT-H-117…125](https://github.com/seeker19110/stored/blob/82ab9b2f880ca067a11f58bdaa68fe254b621d69/data/xt-handoff.json), [bảng phía stored](https://github.com/seeker19110/stored/blob/82ab9b2f880ca067a11f58bdaa68fe254b621d69/X-TEMPLATES.md) (§4f, §5c).
- Khung đối chiếu: `framework/` tại `aeb195c` ngày 2026-11-10. Đã rà 116 bàn giao cũ để tránh trùng; XT-H-121 hạ xuống **sâu hơn** vì `PRF-CLI-008` đã đòi checksum và chữ ký. Phân loại 5 **nông hơn**, 4 **sâu hơn**, 0 **chưa có**.
- Bằng chứng upstream là đọc mã/README/docs ghi ngày, không chạy công cụ; tiêu chí kiểm trong đề xuất là việc cần triển khai nếu được chấp nhận.

## 2. Bản đồ 9 đề xuất

| Bàn giao | Phạm vi | ID gần nhất | Cột |
|---|---|---|---|
| XT-H-117 | Bộ nhớ dùng chung nhiều harness (ai-memory) có handoff có kiểu, mỗi handoff có chủ và chỉ được nhận một lần; nguồn sự thật là wiki Markdown trong git, chỉ mục SQLite dựng lại được; mặc định không gọi LLM. | `LOOP-HARNESS-019`, `LOOP-HARNESS-021`, `WF-DOC-016` | nông hơn |
| XT-H-118 | Review kế hoạch giao diện của gstack (/plan-design-review) chấm từng mặt 0–10, nói rõ thế nào là 10, hỏi người dùng một quyết định cho mỗi chỗ hở, chỉ áp cách sửa đã chọn rồi chấm lại. | `LOOP-STOP-018`, `WF-SDD-011`, `LOOP-DESIGN-021` | nông hơn |
| XT-H-119 | Bắt “AI slop” giao diện bằng luật tất định không cần LLM (Impeccable 62 luật) và quy trình kiểm trước sửa sau (unslop liệt kê từng dấu hiệu kèm vị trí, đề xuất hướng rồi mới sửa; màn đã tốt chỉ chỉnh nhỏ). | `UX-VISUAL-011` | sâu hơn |
| XT-H-120 | Agent tự xem kết quả render trước khi xuất: Chrome DevTools MCP chụp khung trang HTML, MCP for Blender có tool look (viewport, camera, nhiều góc, dải khung hình); kiểm file video cuối bằng ffprobe. | `LOOP-DESIGN-021` | sâu hơn |
| XT-H-121 | Script cài của ai-memory tải bản phát hành theo OS/CPU, so SHA-256 với checksum đã công bố và từ chối cài khi lệch; lệnh setup in kế hoạch (--plan), hỏi trước khi nối từng agent, chạy lại không đổi gì. | `PRF-CLI-008`, `LOOP-HARNESS-025` | sâu hơn |
| XT-H-122 | Connector MCP của SaaS hành động thay người dùng: Slack MCP cần app đã duyệt và scope theo tool, Granola có chế độ chỉ đọc và tắt transcript, Kondo giữ mọi tin agent viết ở dạng nháp tới khi người bấm gửi. | `LOOP-STOP-002`, `LOOP-STOP-014`, `LOOP-STOP-023`, `SEC-AI-007` | nông hơn |
| XT-H-123 | Repo và package đổi tên hoặc đổi chủ vẫn chạy bằng tên cũ: blender-mcp thành mcp-for-blender (uvx blender-mcp vẫn chạy), ComfyUI chuyển org, Notion khuyên bỏ server tự host sang bản remote. | `SEC-SUPPLY-026` | nông hơn |
| XT-H-124 | Số sao trong infographic là ảnh chụp cũ hoặc ghép sai repo: gstack ghi 82,7k khi API là 140,7k, social-media-skills ghi 59,2k nhưng repo cùng tên lớn nhất chỉ 4,6k. | `SEC-SUPPLY-026` | sâu hơn |
| XT-H-125 | Business Ontology cho AI agent: Object, Property, Relationship, Business Rules, KPI và Action cần một mô hình máy đọc được làm nguồn chung; luật viết thành SHACL chạy được (pySHACL), KPI định nghĩa một lần (MetricFlow), Core chung và module theo ngành (LinkML imports). | `PRF-DATA-002`, `DB-MODEL-010`, `UX-CONTENT-008` | nông hơn |

## 3. Delta và phép kiểm đề xuất

### XT-H-117

**Hồ sơ nguồn:** [10-local-llm-rag-memory/README.md#6h](https://github.com/seeker19110/stored/blob/82ab9b2f880ca067a11f58bdaa68fe254b621d69/10-local-llm-rag-memory/README.md#6h-hồ-sơ-akitaonrailsai-memory-bộ-nhớ-dài-hạn-dùng-chung-cho-20-coding-agent-wiki-markdown-trong-git-mặc-định-không-gọi-llm-ảnh-readme-người-dùng-gửi-đọc-mã-8112026).

**Khung đã có:** LOOP-HARNESS-019/021 coi memory ngoài là công cụ tra cứu cho một harness, chỉ bật một công cụ, kho ngoài repo, quyền chủ sở hữu; WF-DOC-016 ghi bàn giao vào PROGRESS.md.

**Phần cần bổ sung:** Chưa có luật cho trường hợp một server memory phục vụ nhiều harness hoặc nhiều người: bàn giao giữa Claude Code và Codex, phân tách tri thức dự án với handoff cá nhân, và tránh hai phiên cùng nhận một việc.

**Đề xuất SHOULD:** Khi dùng một server memory chung cho nhiều harness hoặc nhiều người, SHOULD: PROGRESS.md vẫn là nguồn bàn giao chính; handoff trong memory có chủ, trạng thái và chỉ được nhận một lần; server bind loopback hoặc có xác thực, token chỉ chủ sở hữu đọc; tri thức theo dự án tách khỏi handoff cá nhân; nguồn lưu ở dạng file đọc được (Markdown/git) để rà và khôi phục. Kiểm fixture hai phiên cùng nhận một handoff: chỉ một phiên nhận được, phiên kia thấy đã có chủ.

**Đối chiếu khung:** [LOOP-HARNESS-019](https://github.com/seeker19110/X-Templates/blob/aeb195c2b6ae5074d70efe592d218e9c1147c05e/framework/11-autonomous-loop/harness-files.md#L330), [LOOP-HARNESS-021](https://github.com/seeker19110/X-Templates/blob/aeb195c2b6ae5074d70efe592d218e9c1147c05e/framework/11-autonomous-loop/harness-files.md#L332), [WF-DOC-016](https://github.com/seeker19110/X-Templates/blob/aeb195c2b6ae5074d70efe592d218e9c1147c05e/framework/10-workflow/documentation-workflow.md#L60).

**Nguồn triển khai upstream:** [nguồn 1](https://github.com/akitaonrails/ai-memory/blob/fec76f18c15835bb2dc5c2be3081ce4db0c1270e/README.md) · [nguồn 2](https://github.com/akitaonrails/ai-memory/blob/fec76f18c15835bb2dc5c2be3081ce4db0c1270e/DATA_HANDLING.md).

### XT-H-118

**Hồ sơ nguồn:** [20-claude-plugins-ecosystem/README.md#3za](https://github.com/seeker19110/stored/blob/82ab9b2f880ca067a11f58bdaa68fe254b621d69/20-claude-plugins-ecosystem/README.md#3za-hồ-sơ-garrytangstack-đội-kỹ-sư-ảo-cho-claude-code-plan-design-review-chấm-thiết-kế-010-ảnh-thẻ-skill-người-dùng-gửi-đọc-mã-7112026).

**Khung đã có:** LOOP-STOP-018 ghi điểm quyết định có ≥ 2 phương án; WF-SDD-011 duyệt cách xác minh trước khi code; LOOP-DESIGN-021 kiểm UI sau khi làm bằng ảnh và gắn nhãn asserted-not-measured.

**Phần cần bổ sung:** Chưa có bước rà thiết kế ở giai đoạn kế hoạch cho task UI theo từng mặt (cấu trúc thông tin, trạng thái, responsive, a11y…) và chưa có quy tắc “một quyết định cho một chỗ hở, áp đúng cách sửa đã chọn”.

**Đề xuất SHOULD:** Với task có giao diện, SHOULD rà kế hoạch trước khi code theo danh sách mặt thiết kế cố định; mỗi mặt ghi điểm, lý do và điều kiện cụ thể để đạt mức tốt nhất; mỗi chỗ hở là một quyết định riêng ghi bằng loop decide, chỉ áp cách sửa đã chọn rồi chấm lại. Điểm là nhận định (asserted-not-measured), không thay Gate; mỗi chỗ hở đã chọn sửa phải đổi thành tiêu chí kiểm được trong PLAN. Kiểm: PLAN của task UI có bảng mặt thiết kế và mỗi dòng dưới mức tốt nhất có quyết định hoặc tiêu chí đi kèm.

**Đối chiếu khung:** [LOOP-STOP-018](https://github.com/seeker19110/X-Templates/blob/aeb195c2b6ae5074d70efe592d218e9c1147c05e/framework/11-autonomous-loop/stop-points-and-escalation.md#L232), [WF-SDD-011](https://github.com/seeker19110/X-Templates/blob/aeb195c2b6ae5074d70efe592d218e9c1147c05e/framework/10-workflow/spec-driven-development.md#L52), [LOOP-DESIGN-021](https://github.com/seeker19110/X-Templates/blob/aeb195c2b6ae5074d70efe592d218e9c1147c05e/framework/11-autonomous-loop/loop-design.md#L82).

**Nguồn triển khai upstream:** [nguồn 1](https://github.com/garrytan/gstack/blob/297f50c7e1d46aab1404f5f2e8a9584af76ad6b2/README.md) · [nguồn 2](https://github.com/garrytan/gstack/blob/297f50c7e1d46aab1404f5f2e8a9584af76ad6b2/plan-design-review/SKILL.md).

### XT-H-119

**Hồ sơ nguồn:** [06-ui-ux-design/README.md#7zb](https://github.com/seeker19110/stored/blob/82ab9b2f880ca067a11f58bdaa68fe254b621d69/06-ui-ux-design/README.md#7zb-đọc-lại-heydamirunslop-skill-biến-ui-vibecoded-thành-giao-diện-có-chủ-đích-114k-sau-10-ngày-ảnh-người-dùng-gửi-đọc-mã-8112026), [19-agentic-video-media/README.md#3h](https://github.com/seeker19110/stored/blob/82ab9b2f880ca067a11f58bdaa68fe254b621d69/19-agentic-video-media/README.md#3h-kiểm-ảnh-ai-video-stack-remotion-skills-blender-và-blender-mcp-faster-whisper-chatterbox-gsap-ảnh-người-dùng-gửi-đọc-mã-8112026).

**Khung đã có:** UX-VISUAL-011 đã có script check:ui-ux-guard (grep gradient ngoài token, transition: all, emoji, backdrop-filter) và review ảnh hero.

**Phần cần bổ sung:** Thêm ví dụ công cụ tất định có sẵn (Impeccable detector) và fixture: màn có gradient tím + emoji nhãn phải bị bắt; màn sạch không bị đề xuất thiết kế lại. Không cần ID mới.

**Xử lý:** chỉ thêm ví dụ/fixture vào ID hiện có, không cần ID mới.

**Đối chiếu khung:** [UX-VISUAL-011](https://github.com/seeker19110/X-Templates/blob/aeb195c2b6ae5074d70efe592d218e9c1147c05e/framework/06-design-ux/motion-and-visual-quality.md#L61).

**Nguồn triển khai upstream:** [nguồn 1](https://github.com/heydamir/unslop/blob/a6f121eee5f29c2f74976b75456feae8b66afb3a/README.md) · [nguồn 2](https://github.com/heydamir/unslop/blob/a6f121eee5f29c2f74976b75456feae8b66afb3a/skills/unslop/SKILL.md) · [nguồn 3](https://github.com/pbakaus/impeccable/blob/924bbd194d02e5e15a227e75b5901fb0d7a4ecad/README.md).

### XT-H-120

**Hồ sơ nguồn:** [19-agentic-video-media/README.md#3h](https://github.com/seeker19110/stored/blob/82ab9b2f880ca067a11f58bdaa68fe254b621d69/19-agentic-video-media/README.md#3h-kiểm-ảnh-ai-video-stack-remotion-skills-blender-và-blender-mcp-faster-whisper-chatterbox-gsap-ảnh-người-dùng-gửi-đọc-mã-8112026).

**Khung đã có:** LOOP-DESIGN-021 đã đòi ảnh màn đã đổi, chuỗi frame cho animation, nhãn measured/unmeasured.

**Phần cần bổ sung:** Mở rộng ví dụ sang artifact không phải web: video (lấy frame từ chính file MP4 đã encode, ffprobe kiểm codec/thời lượng/fps) và cảnh 3D (render nhiều góc). Kiểm trên artifact xuất cuối, không chỉ trang nguồn.

**Xử lý:** chỉ thêm ví dụ/fixture vào ID hiện có, không cần ID mới.

**Đối chiếu khung:** [LOOP-DESIGN-021](https://github.com/seeker19110/X-Templates/blob/aeb195c2b6ae5074d70efe592d218e9c1147c05e/framework/11-autonomous-loop/loop-design.md#L82).

**Liên quan đợt trước:** XT-H-061; chỉ giữ phần delta nêu trên.

**Nguồn triển khai upstream:** [nguồn 1](https://github.com/ChromeDevTools/chrome-devtools-mcp/blob/0b37364dc0a88a804c6d73d3335e776adc7f33c4/README.md) · [nguồn 2](https://github.com/ahujasid/mcp-for-blender/blob/2e4b0bc294694b1570d76ed01be657c22e6d02a0/README.md) · [nguồn 3](https://github.com/ahujasid/mcp-for-blender/blob/2e4b0bc294694b1570d76ed01be657c22e6d02a0/LICENSE) · [nguồn 4](https://github.com/FFmpeg/FFmpeg/blob/2bf291526e50480d2c355b4c6c8dd04863212aa1/README.md).

### XT-H-121

**Hồ sơ nguồn:** [10-local-llm-rag-memory/README.md#6h](https://github.com/seeker19110/stored/blob/82ab9b2f880ca067a11f58bdaa68fe254b621d69/10-local-llm-rag-memory/README.md#6h-hồ-sơ-akitaonrailsai-memory-bộ-nhớ-dài-hạn-dùng-chung-cho-20-coding-agent-wiki-markdown-trong-git-mặc-định-không-gọi-llm-ảnh-readme-người-dùng-gửi-đọc-mã-8112026).

**Khung đã có:** PRF-CLI-008 (MUST@M) đã đòi checksums.txt SHA-256 kèm chữ ký/attestation và cấm hướng dẫn curl | sh không kiểm checksum; LOOP-HARNESS-025 thử guard chặn curl | sh.

**Phần cần bổ sung:** Thêm ví dụ tốt và hai ý vận hành: lệnh setup in kế hoạch không đổi gì (--plan), hỏi trước khi sửa cấu hình của agent khác, chạy lại không đổi thêm. Checksum cùng bản phát hành chỉ bảo vệ đường truyền (XT-H-046), nên vẫn cần chữ ký/attestation như PRF-CLI-008. Không cần ID mới.

**Xử lý:** chỉ thêm ví dụ/fixture vào ID hiện có, không cần ID mới.

**Đối chiếu khung:** [PRF-CLI-008](https://github.com/seeker19110/X-Templates/blob/aeb195c2b6ae5074d70efe592d218e9c1147c05e/framework/02-profiles/cli-tool.md#L63), [LOOP-HARNESS-025](https://github.com/seeker19110/X-Templates/blob/aeb195c2b6ae5074d70efe592d218e9c1147c05e/framework/11-autonomous-loop/harness-files.md#L336).

**Liên quan đợt trước:** XT-H-046; chỉ giữ phần delta nêu trên.

**Nguồn triển khai upstream:** [nguồn 1](https://github.com/akitaonrails/ai-memory/blob/fec76f18c15835bb2dc5c2be3081ce4db0c1270e/README.md) · [nguồn 2](https://github.com/akitaonrails/ai-memory/blob/fec76f18c15835bb2dc5c2be3081ce4db0c1270e/DATA_HANDLING.md).

### XT-H-122

**Hồ sơ nguồn:** [20-claude-plugins-ecosystem/README.md#3zb](https://github.com/seeker19110/stored/blob/82ab9b2f880ca067a11f58bdaa68fe254b621d69/20-claude-plugins-ecosystem/README.md#3zb-kiểm-ảnh-8-plugin-8-kỹ-năng-8-mcp-bộ-cài-sẵn-cho-claude-ảnh-phandonggiang-người-dùng-gửi-đọc-mã-8112026).

**Khung đã có:** LOOP-STOP-002 đưa hành động đối ngoại qua guard; LOOP-STOP-014 cho routine chỉ đề xuất; LOOP-STOP-023 cấm agent tự thêm MCP giữa phiên. SEC-AI-007 đòi identity theo người dùng/phiên, token TTL ngắn, scope hẹp.

**Phần cần bổ sung:** Chưa có bảng khai từng connector SaaS: scope, đọc/ghi, chế độ nháp; guard dựa trên lệnh shell có thể không thấy tool MCP gửi tin.

**Đề xuất SHOULD:** Với connector MCP của dịch vụ ngoài (chat, email, ghi chú, CRM), SHOULD khai trong repo từng connector: scope đã cấp, tool đọc và tool ghi, chế độ chỉ đọc hoặc nháp nếu có; ưu tiên chế độ nháp hoặc chỉ đọc cho phiên không người trực; tool gửi/đăng của connector được coi là hành động đối ngoại như LOOP-STOP-002. Kiểm fixture: phiên không người trực gọi tool gửi tin của connector phải bị chặn hoặc chỉ tạo nháp.

**Đối chiếu khung:** [LOOP-STOP-002](https://github.com/seeker19110/X-Templates/blob/aeb195c2b6ae5074d70efe592d218e9c1147c05e/framework/11-autonomous-loop/stop-points-and-escalation.md#L216), [LOOP-STOP-014](https://github.com/seeker19110/X-Templates/blob/aeb195c2b6ae5074d70efe592d218e9c1147c05e/framework/11-autonomous-loop/stop-points-and-escalation.md#L228), [LOOP-STOP-023](https://github.com/seeker19110/X-Templates/blob/aeb195c2b6ae5074d70efe592d218e9c1147c05e/framework/11-autonomous-loop/stop-points-and-escalation.md#L237), [SEC-AI-007](https://github.com/seeker19110/X-Templates/blob/aeb195c2b6ae5074d70efe592d218e9c1147c05e/framework/12-security/ai-security.md#L59).

**Nguồn triển khai upstream:** [nguồn 1](https://docs.slack.dev/ai/mcp-server/) · [nguồn 2](https://www.trykondo.com) · [nguồn 3](https://docs.granola.ai/help-center/sharing/integrations/mcp).

### XT-H-123

**Hồ sơ nguồn:** [19-agentic-video-media/README.md#3h](https://github.com/seeker19110/stored/blob/82ab9b2f880ca067a11f58bdaa68fe254b621d69/19-agentic-video-media/README.md#3h-kiểm-ảnh-ai-video-stack-remotion-skills-blender-và-blender-mcp-faster-whisper-chatterbox-gsap-ảnh-người-dùng-gửi-đọc-mã-8112026).

**Khung đã có:** SEC-SUPPLY-026 đòi đọc lịch sử thật thay số commit/sao khi đánh giá bảo trì.

**Phần cần bổ sung:** Chưa có kiểm tên chuẩn: dependency trỏ tên cũ qua redirect hoặc alias, hoặc bản đã được chủ dự án khuyên ngừng dùng.

**Đề xuất SHOULD:** Với dependency, MCP server và skill bên thứ ba, SHOULD ghim tên chuẩn hiện tại (owner/repo, tên package) và định kỳ so tên khai báo với tên API trả về; báo khi repo redirect, package đổi tên, hoặc README ghi deprecated/khuyên bản khác. Kiểm fixture: khai báo repo cũ đã redirect thì công cụ kiểm báo tên chuẩn mới.

**Đối chiếu khung:** [SEC-SUPPLY-026](https://github.com/seeker19110/X-Templates/blob/aeb195c2b6ae5074d70efe592d218e9c1147c05e/framework/12-security/supply-chain.md#L72).

**Liên quan đợt trước:** XT-H-030; chỉ giữ phần delta nêu trên.

**Nguồn triển khai upstream:** [nguồn 1](https://github.com/ahujasid/mcp-for-blender/blob/2e4b0bc294694b1570d76ed01be657c22e6d02a0/README.md) · [nguồn 2](https://github.com/ahujasid/mcp-for-blender/blob/2e4b0bc294694b1570d76ed01be657c22e6d02a0/LICENSE) · [nguồn 3](https://github.com/makenotion/notion-mcp-server/blob/cf16e5c20bfbfb98ecec1227f210ef0ae3abebe5/README.md).

### XT-H-124

**Hồ sơ nguồn:** [20-claude-plugins-ecosystem/README.md#3f5](https://github.com/seeker19110/stored/blob/82ab9b2f880ca067a11f58bdaa68fe254b621d69/20-claude-plugins-ecosystem/README.md#3f5-đọc-lại-2112026-ảnh-readme-mới-bốn-commit-thêm-rồi-gỡ-claude-reel-editor-banner-giữ-số-cũ-ảnh-người-dùng-gửi), [20-claude-plugins-ecosystem/README.md#3za](https://github.com/seeker19110/stored/blob/82ab9b2f880ca067a11f58bdaa68fe254b621d69/20-claude-plugins-ecosystem/README.md#3za-hồ-sơ-garrytangstack-đội-kỹ-sư-ảo-cho-claude-code-plan-design-review-chấm-thiết-kế-010-ảnh-thẻ-skill-người-dùng-gửi-đọc-mã-7112026).

**Khung đã có:** SEC-SUPPLY-026 đã nói số sao không là bằng chứng bảo trì.

**Phần cần bổ sung:** Thêm ví dụ: khi nguồn là ảnh hay bài đăng, đối chiếu owner/repo và số liệu bằng API tại ngày đọc, ghi ngày; không dùng số trong ảnh để chọn công cụ.

**Xử lý:** chỉ thêm ví dụ/fixture vào ID hiện có, không cần ID mới.

**Đối chiếu khung:** [SEC-SUPPLY-026](https://github.com/seeker19110/X-Templates/blob/aeb195c2b6ae5074d70efe592d218e9c1147c05e/framework/12-security/supply-chain.md#L72).

**Nguồn triển khai upstream:** [nguồn 1](https://github.com/garrytan/gstack/blob/297f50c7e1d46aab1404f5f2e8a9584af76ad6b2/README.md) · [nguồn 2](https://github.com/garrytan/gstack/blob/297f50c7e1d46aab1404f5f2e8a9584af76ad6b2/plan-design-review/SKILL.md) · [nguồn 3](https://github.com/charlie947/social-media-skills/blob/10ca79c0ec0be0f7654d19cd4f0c86b6fa6ed23b/LICENSE) · [nguồn 4](https://github.com/charlie947/social-media-skills/blob/10ca79c0ec0be0f7654d19cd4f0c86b6fa6ed23b/README.md).

### XT-H-125

**Hồ sơ nguồn:** [24-ai-data-engineering/README.md#6c](https://github.com/seeker19110/stored/blob/82ab9b2f880ca067a11f58bdaa68fe254b621d69/24-ai-data-engineering/README.md#6c-business-ontology-cho-doanh-nghiệp-quy-trình-8-bước-core-mở-rộng-theo-ngành-kiến-trúc-5-lớp-và-công-cụ-mở-cho-từng-bước-3-infographic-người-dùng-gửi-8112026).

**Khung đã có:** PRF-DATA-002 có data contract; DB-MODEL-010 có từ điển dữ liệu; UX-CONTENT-008 có GLOSSARY.

**Phần cần bổ sung:** Ba nguồn tách nhau (glossary, schema, comment) và chưa có luật cho luật nghiệp vụ dạng chạy được hay KPI một định nghĩa khi agent đọc dữ liệu nghiệp vụ.

**Đề xuất SHOULD:** Với sản phẩm cho AI agent đọc/ghi dữ liệu nghiệp vụ, SHOULD có một mô hình miền máy đọc được (thực thể, thuộc tính, trạng thái, quan hệ) làm nguồn sinh glossary, schema hoặc tài liệu cho agent; luật nghiệp vụ quan trọng viết thành kiểm chạy được trên dữ liệu mẫu; KPI định nghĩa một lần trong code và dùng chung cho BI, API, agent. Kiểm: thêm một thuộc tính vào mô hình thì glossary/schema sinh lại khớp; bản ghi vi phạm một luật mẫu bị bộ kiểm báo.

**Đối chiếu khung:** [PRF-DATA-002](https://github.com/seeker19110/X-Templates/blob/aeb195c2b6ae5074d70efe592d218e9c1147c05e/framework/02-profiles/data-ml.md#L63), [DB-MODEL-010](https://github.com/seeker19110/X-Templates/blob/aeb195c2b6ae5074d70efe592d218e9c1147c05e/framework/09-database/data-modeling.md#L58), [UX-CONTENT-008](https://github.com/seeker19110/X-Templates/blob/aeb195c2b6ae5074d70efe592d218e9c1147c05e/framework/06-design-ux/content-and-microcopy.md#L47).

**Nguồn triển khai upstream:** [nguồn 1](https://github.com/linkml/linkml/blob/5dcae0f60bb524b3aec2b8a488fcce3546da8149/README.md) · [nguồn 2](https://github.com/RDFLib/pySHACL/blob/df57bd4390bd397811d7c2d3b7cf0e49cd21c189/README.md) · [nguồn 3](https://github.com/dbt-labs/metricflow/blob/fe4b8c1ccb72a8ca77494b345777eff20a714119/README.md).

## 4. Thứ tự gợi ý và giới hạn áp dụng

1. **Hành động đối ngoại đi đường MCP:** XT-H-122. Guard theo lệnh shell không thấy tool gửi tin của connector; khai connector, xếp tool gửi/đăng vào nhóm `LOOP-STOP-002`, phiên không người trực chỉ tạo nháp.
2. **Kiểm rẻ trong `doctor`:** XT-H-123 (so `owner/repo` khai báo với tên API trả về, bắt redirect và README ghi deprecated), đi cùng XT-H-030.
3. **Mẫu PLAN cho task UI:** XT-H-118. Bảng mặt thiết kế và quyết định cho từng chỗ hở; điểm số giữ nhãn asserted-not-measured như `LOOP-DESIGN-021`.
4. **Có điều kiện theo dự án:** XT-H-117 (chỉ khi dùng memory chung nhiều harness/người), XT-H-125 (profile dữ liệu/ERP có agent đọc dữ liệu nghiệp vụ).
5. **Chỉ ví dụ:** XT-H-119, 120, 121, 124.

Phiên triển khai tiếp theo tự quyết cách gộp vào ID hiện có hay cấp ID mới; cập nhật module/README/CHANGELOG và ADR khi quy tắc khung yêu cầu. Research note này không cài thêm stack, không sửa blueprint dự án đích và không tự bật auto-merge.

## 5. Nguồn và trạng thái xác minh

- [stored: phương pháp và mức bằng chứng](https://github.com/seeker19110/stored/blob/82ab9b2f880ca067a11f58bdaa68fe254b621d69/METHOD.md), [catalog](https://github.com/seeker19110/stored/blob/82ab9b2f880ca067a11f58bdaa68fe254b621d69/data/projects.json), [nguồn](https://github.com/seeker19110/stored/blob/82ab9b2f880ca067a11f58bdaa68fe254b621d69/SOURCES.md) (các mục "Bổ sung" từ 2026-11-05).
- Nguồn trực tiếp và ngày/SHA ở từng hồ sơ phía stored; chỗ **(chưa xác minh)** giữ nguyên mức đó. Kondo, Granola, Slack là docs của nhà cung cấp, không có mã nguồn.
- Đã so với các note stored-delta trước và 116 bàn giao cũ; dòng có related_handoffs chỉ đề xuất phần sâu hơn.
