# Nhật ký quyết định tự duyệt

> Ghi bởi `xt.py loop decide`. Phiên chính tự duyệt điểm quyết định theo tiêu chí chất lượng cuối (`LOOP-STOP-018`, ADR-0008 của khung). Người xem lại bất cứ lúc nào; đổi ý → quyết định mới ghi "thay D-NNN", không sửa mục cũ.

### D-001 · 2026-10-15T14:17:22+00:00 · Phạm vi tự duyệt của phiên chính (ADR-0008)

- Phương án: (1) Tự duyệt cả quyết định chuyên môn lẫn hành động (deploy, xoá, tiền) · (2) Chỉ quyết định chuyên môn; hành động giữ điểm dừng có hook
- Chọn: Chỉ quyết định chuyên môn; hành động giữ điểm dừng có hook
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1 (đúng và an toàn): hành động không đảo ngược thì chất lượng cuối không cứu được; hook ask/deny của ADR-0002 vẫn cưỡng chế. Tiêu chí 2: lựa chọn chuyên môn sửa được, có D-NNN để xem lại.
- Đường lùi: ADR mới nới/thu hẹp danh sách điểm quyết định trong stop-points-and-escalation.md

### D-002 · 2026-10-15T14:17:22+00:00 · Mục checklist cũ đổi nghĩa (LOOP-STOP-004, PM-SPEC-007, PM-REQ-008, WF-SDD-004)

- Phương án: (1) Viết lại nội dung giữ ID · (2) MAY Ngừng dùng + ID mới (WF-SDD-004 gộp vào PM-SPEC-020)
- Chọn: MAY Ngừng dùng + ID mới (WF-SDD-004 gộp vào PM-SPEC-020)
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1: dự án đích đã tick theo nghĩa cũ sẽ mang trạng thái sai nếu viết lại; conventions.md cấm tái sử dụng nghĩa ID. Tiêu chí 3: gộp trùng chủ đề spec hở về một nhà.
- Đường lùi: Đổi mức các ID mới về MAY Ngừng dùng và trỏ lại ID cũ (không xoá ID)

### D-003 · 2026-10-15T14:17:22+00:00 · Nơi ghi dấu vết quyết định tự duyệt

- Phương án: (1) Mục Quyết định của PROGRESS.md · (2) File riêng docs/autopilot/DECISIONS.md, ghi bằng xt.py loop decide có kiểm đầu vào
- Chọn: File riêng docs/autopilot/DECISIONS.md, ghi bằng xt.py loop decide có kiểm đầu vào
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1/3: PROGRESS bị viết lại mỗi phiên và giới hạn 8 KB nên mất dấu vết; lệnh máy buộc ≥ 2 phương án, lý do, đường lùi (P1 bằng chứng).
- Đường lùi: --log trỏ file khác; file là Markdown thuần, chuyển tay được

### D-004 · 2026-10-15T14:32:44+00:00 · Nơi ghi checkpoint trước compaction (ADR-0009)

- Phương án: (1) Hook tự sửa PROGRESS.md · (2) .autopilot/state.json qua xt.py loop checkpoint, SessionStart in lại qua loop status
- Chọn: .autopilot/state.json qua xt.py loop checkpoint, SessionStart in lại qua loop status
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1/3: hook sửa file đã commit làm bẩn cây làm việc và đua với agent; state.json gitignore, có test, fail-open; PROGRESS vẫn do agent cập nhật sau mỗi task.
- Đường lùi: Đổi đích ghi trong loop_checkpoint; hook không đổi

### D-005 · 2026-10-15T14:32:44+00:00 · Việc cần người giữa autopilot (ADR-0009)

- Phương án: (1) loop block dừng cả vòng (như cũ) · (2) loop defer bỏ qua việc đó, làm việc độc lập khác, gom cuối phiên (done-pending-human)
- Chọn: loop defer bỏ qua việc đó, làm việc độc lập khác, gom cuối phiên (done-pending-human)
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1 giữ nguyên (người vẫn làm hành động đó); tiêu chí 4/5: một lần can thiệp thay vì đứng giữa chừng; block vẫn còn khi mọi việc phụ thuộc.
- Đường lùi: Không gọi defer; loop block vẫn hoạt động như cũ

### D-006 · 2026-10-15T14:32:44+00:00 · Trần vòng mặc định ở chế độ một phiên

- Phương án: (1) Giữ 50 vòng · (2) max(20, 4 × task chưa làm), ghi đè bằng --max-iterations
- Chọn: max(20, 4 × task chưa làm), ghi đè bằng --max-iterations
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1: 50 vòng cắt PLAN lớn giữa chừng (verdict budget sớm) hoặc quá rộng cho PLAN nhỏ; ~4 vòng/task khớp 1 làm + 1 sửa + 1 verify + dự phòng; sàn 20 cho PLAN rất nhỏ.
- Đường lùi: loop init --max-iterations N

### D-007 · 2026-10-15T15:11:41+00:00 · Đường đưa phản hồi từ dự án đích về khung (ADR-0010)

- Phương án: (1) Dự án đích tự mở issue/PR vào repo khung bằng token · (2) Dự án ghi FB-NNN trong repo mình; Routine của khung kéo về, gộp, mở PR nháp
- Chọn: Dự án ghi FB-NNN trong repo mình; Routine của khung kéo về, gộp, mở PR nháp
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1: không cần token ghi chéo repo ở mọi dự án, người duyệt trước khi nội dung lên repo public; tiêu chí 3: một chỗ gom thì gộp trùng theo (loại, ID).
- Đường lùi: Thêm workflow đẩy ở dự án đích; định dạng FB-NNN giữ nguyên

### D-008 · 2026-10-16T05:14:34+00:00 · Phạm vi đọc cấu hình của kiểm memory trong xt.py doctor (LOOP-HARNESS-021)

- Phương án: (1) Chỉ cấp dự án: .claude/settings.json, .claude/settings.local.json, .mcp.json · (2) Cấp dự án + người dùng: thêm ~/.claude/settings.json và ~/.claude.json (mcpServers gốc và projects.<dự án>.mcpServers), theo CLAUDE_CONFIG_DIR
- Chọn: Cấp dự án + người dùng: thêm ~/.claude/settings.json và ~/.claude.json (mcpServers gốc và projects.<dự án>.mcpServers), theo CLAUDE_CONFIG_DIR
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1 (đúng): engram setup claude-code đăng ký MCP vào ~/.claude.json (internal/setup/setup.go), plugin thường bật ở ~/.claude/settings.json; chỉ đọc cấp dự án sẽ bỏ sót đúng ca phổ biến. Chỉ đọc tên khoá, không in giá trị; mức warn vì 021 là SHOULD; không tự sửa vì gỡ plugin là quyết định của người.
- Đường lùi: Bỏ _claude_user_paths khỏi _doctor_memory, giữ phần cấp dự án

### D-009 · 2026-10-16T05:26:25+00:00 · merge-check lấy dữ liệu PR khi phiên không có GraphQL (403 trong phiên Claude Code)

- Phương án: (1) Giữ gh pr view (GraphQL), lỗi thì rơi về REST · (2) Chỉ dùng REST (gh api) và dựng lại đúng dict dạng gh pr view --json; reviewDecision suy từ review mới nhất mỗi người + mergeable_state=blocked
- Chọn: Chỉ dùng REST (gh api) và dựng lại đúng dict dạng gh pr view --json; reviewDecision suy từ review mới nhất mỗi người + mergeable_state=blocked
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 3 (một đường, đơn giản, test được): rơi về khi lỗi sẽ che lỗi thật (vd 'no pull requests found' gọi lại lần nữa) và nhân đôi mã. Tiêu chí 1 (an toàn): REST không có reviewDecision, nhưng mergeable_state=blocked do GitHub tính gồm cả branch protection cổ điển mà REST không đọc được nếu không là admin; khi CI xanh mà blocked thì coi là cần người (REVIEW_REQUIRED → human), tức chặt hơn chứ không lỏng hơn. Lệnh merge vẫn bị GitHub chặn phía server nếu suy sai. --pr-json giữ định dạng cũ.
- Đường lùi: Đổi load_pr gọi lại gh pr view --json MERGE_FIELDS (hằng còn giữ)

### D-010 · 2026-10-16T11:31:37+00:00 · Cách tự merge PR theo từng lát (chủ repo yêu cầu 2026-10-16: tạo PR và auto merge theo từng lát code)

- Phương án: (1) Bật auto-merge của GitHub (gh pr merge --auto / enable_pr_auto_merge) ngay khi mở PR · (2) Máy tự merge khi xt.py merge-check = merge, lệnh merge ghim head (gh pr merge --match-head-commit, REST PUT …/merge sha=, MCP merge_pull_request expectedHeadSha); merge-check chạy mỗi vòng và khi có sự kiện PR
- Chọn: Máy tự merge khi xt.py merge-check = merge, lệnh merge ghim head (gh pr merge --match-head-commit, REST PUT …/merge sha=, MCP merge_pull_request expectedHeadSha); merge-check chạy mỗi vòng và khi có sự kiện PR
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1: auto-merge của GitHub không ghim head — commit đẩy sau khi bật vẫn tự merge mà không qua vị từ làn nhanh; enable_pr_auto_merge thất bại khi PR đã clean (tool MCP mô tả) và cần GraphQL (phiên Claude Code chặn); REST PUT …/merge nhận sha, 409 nếu lệch (docs.github.com REST pulls, 2026-10-16). Tiêu chí 3: một đường quyết (merge-check) cho cả gh/REST/MCP
- Đường lùi: Bỏ nhánh allow REST/MCP trong guard.py (_gh_api_merge_rule, mcp_decision) và đặt merge_autonomy: L1 — người merge mọi PR như trước

### D-011 · 2026-10-16T14:35:02+00:00 · Chủ repo yêu cầu 2026-10-16: mở PR luôn kèm auto-merge để merge tự động, cho cả repo khung lẫn dự án đích (thay D-010)

- Phương án: (1) Giữ D-010: chỉ máy tự merge làn nhanh bằng lệnh ghim head; làn chuẩn để người · (2) Mức merge_autonomy L3: bật auto-merge của GitHub ngay khi mở PR cho mọi làn; GitHub chỉ merge khi required check/ruleset đạt; guard vẫn cấm --admin, PR chồng, repo khác; mẫu dự án đích mặc định L3
- Chọn: Mức merge_autonomy L3: bật auto-merge của GitHub ngay khi mở PR cho mọi làn; GitHub chỉ merge khi required check/ruleset đạt; guard vẫn cấm --admin, PR chồng, repo khác; mẫu dự án đích mặc định L3
- Lý do (tiêu chí chất lượng cuối): Người dùng có quyền cuối (AGENTS.md §1) và đã quyết rõ; tiêu chí 1 giữ được phần cốt lõi: CI bắt buộc của ruleset vẫn chặn merge đỏ, --admin vẫn hỏi, PR chồng không bật (tránh merge vào nhánh sắp xoá). Mất: ghim head và vị từ làn nhanh — ghi rõ ở ADR-0015 và miễn trừ WF-REVIEW-007
- Đường lùi: Đặt merge_autonomy: L2 (hoặc L1) trong xt.yaml: guard thôi allow --auto/enable_pr_auto_merge, merge-check trả human cho làn chuẩn như ADR-0014

### D-012 · 2026-10-16T16:32:54+00:00 · Audit delta AUD-HAR-042: ở merge_autonomy L3, PR chạm tiền/dữ liệu người dùng thật/auth/mật mã/bí mật có tự merge không (LOOP-STOP-005 MUST và Ngoại lệ cứng nói luôn người duyệt; ADR-0015 chỉ miễn WF-REVIEW-007; ruleset main 0 approval)

- Phương án: (1) Giữ ngoại lệ cứng ở L3: merge-check trả human + trường hard cho đường dẫn bí mật/auth/thanh toán/mật mã, nhãn risk:auth/payment/pii/crypto/admin/secret và merge_risk_paths; guard không bật auto-merge cho PR đó; làn chuẩn còn lại vẫn auto-merge · (2) Ghi miễn trừ LOOP-STOP-005 ở L3: mọi PR auto-merge khi CI xanh, kể cả auth/thanh toán
- Chọn: Giữ ngoại lệ cứng ở L3: merge-check trả human + trường hard cho đường dẫn bí mật/auth/thanh toán/mật mã, nhãn risk:auth/payment/pii/crypto/admin/secret và merge_risk_paths; guard không bật auto-merge cho PR đó; làn chuẩn còn lại vẫn auto-merge
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1 (đúng và an toàn, cách hiểu chặt hơn với bảo mật/tiền/dữ liệu): yêu cầu 'mở PR kèm auto-merge' của chủ repo nói chung, không nói bỏ chốt người cho tiền/auth; LOOP-STOP-005 là MUST và ruleset không có review bắt buộc nên phương án 2 bỏ chốt người duy nhất. Repo khung không có mã auth/thanh toán nên yêu cầu của chủ repo giữ nguyên ở đây; dự án đích giữ người duyệt đúng chỗ rủi ro.
- Đường lùi: Bỏ nhánh hard trong merge_decision và guard._auto_merge_verdict (ADR-0016), ghi miễn trừ LOOP-STOP-005 vào BLUEPRINT dự án
