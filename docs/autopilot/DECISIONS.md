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

### D-013 · 2026-10-16T22:55:56+00:00 · Duyệt PLAN T-701…T-704 (sửa audit delta #58–#66, 4 đợt)

- Phương án: (1) Duyệt PLAN 4 task như viết, mỗi đợt một PR kèm auto-merge, xung đột giải bằng merge main · (2) Gộp B+C+D thành một PR để tránh xung đột lặp
- Chọn: Duyệt PLAN 4 task như viết, mỗi đợt một PR kèm auto-merge, xung đột giải bằng merge main
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1/3: chủ repo đã duyệt 4 đợt và luật mỗi lát một PR (ADR-0014); PR nhỏ dễ review và dễ lùi; xung đột với phiên song song giải được bằng merge main, không cần gộp
- Đường lùi: Đóng PR đợt chưa merge, gộp nhánh còn lại thành một PR

### D-014 · 2026-10-17T06:16:30+00:00 · Duyệt PLAN T-801…T-804 (đóng audit delta #68–#80 sau đợt 1)

- Phương án: (1) Duyệt 4 task như viết: 2 lát guard + 1 lát tài liệu + sổ; mỗi lát một PR kèm auto-merge; AUD-CI-009 defer cho chủ repo · (2) Gộp mọi việc còn lại thành một PR
- Chọn: Duyệt 4 task như viết: 2 lát guard + 1 lát tài liệu + sổ; mỗi lát một PR kèm auto-merge; AUD-CI-009 defer cho chủ repo
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1/3: chủ repo đã duyệt kế hoạch đợt; mỗi lát một PR (ADR-0014) dễ review và dễ lùi; CI-009 đổi cấu hình CI là điểm dừng nên defer
- Đường lùi: Đóng PR lát chưa merge, gộp nhánh còn lại

### D-015 · 2026-10-17T06:16:30+00:00 · Sửa AUD-SEC-036 (auto-merge vẫn bật khi push sau chạm ngoại lệ cứng) bằng gì

- Phương án: (1) Quy trình: skill /autopilot + LOOP-STOP-005 bắt chạy lại merge-check sau mỗi push vào PR đang auto-merge, có hard thì tắt auto-merge · (2) Guard tự gọi merge-check mỗi git push (mạng mỗi lần push, chậm, fail-open khi lỗi) · (3) Chỉ ghi giới hạn, giữ mở
- Chọn: Quy trình: skill /autopilot + LOOP-STOP-005 bắt chạy lại merge-check sau mỗi push vào PR đang auto-merge, có hard thì tắt auto-merge
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1/3: đúng chỗ phát sinh (sau push), không thêm gọi mạng vào hook mỗi push; ruleset vẫn là chốt chặn; nửa sau (GitHub giữ auto-merge) chưa xác minh nên không đáng mã guard
- Đường lùi: Thêm kiểm vào guard ở lát sau nếu dự án thật gặp

### D-016 · 2026-10-17T06:22:13+00:00 · Lát T-802/T-803 khi phiên chỉ được push một nhánh và PR #82 (T-801) đang chờ review

- Phương án: (1) Xếp T-802, T-803 làm commit riêng trên cùng nhánh → vào PR #82; reviewer rà thêm diff mới trước khi bật auto-merge · (2) Chờ #82 merge rồi mới commit T-802/T-803 (cây làm việc bẩn, Stop hook đòi commit)
- Chọn: Xếp T-802, T-803 làm commit riêng trên cùng nhánh → vào PR #82; reviewer rà thêm diff mới trước khi bật auto-merge
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1/2/3: luật phiên cấm push nhánh khác; mỗi lát vẫn là commit riêng dễ revert; review vẫn chạy trước merge
- Đường lùi: git revert từng commit lát trên main

### D-017 · 2026-10-17T07:31:07+00:00 · Duyệt PLAN T-901…T-904 (trả nợ 🟢 audit tự làm được)

- Phương án: (1) Duyệt 4 task chỉ mã/test; mục chạm hook/settings/CI và chính sách npx để người · (2) Gồm cả sửa matcher settings/CI (điểm dừng)
- Chọn: Duyệt 4 task chỉ mã/test; mục chạm hook/settings/CI và chính sách npx để người
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1/2: đổi hook/settings/CI là điểm dừng bắt buộc; phần mã/test có test đỏ trước, đảo ngược được
- Đường lùi: git revert từng commit lát

### D-018 · 2026-10-17T10:39:51+00:00 · Bỏ lớp hỏi người của guard thế nào?

- Phương án: (1) Bỏ toàn bộ ask, giữ deny cũ · (2) Ask nguy hiểm → deny, còn lại cho qua (lớp chính sách ở đầu ra guard) · (3) Sửa từng luật
- Chọn: Ask nguy hiểm → deny, còn lại cho qua (lớp chính sách ở đầu ra guard)
- Lý do (tiêu chí chất lượng cuối): Chủ repo yêu cầu không dừng chờ; việc không đảo ngược vẫn bị chặn; ít code, giữ bộ luật làm đường lùi (strict)
- Đường lùi: XT_GUARD_POLICY=strict hoặc revert ADR-0018

### D-019 · 2026-10-17T11:53:48+00:00 · PR ngoại lệ cứng (ADR-0016) dưới chính sách không hỏi (ADR-0018) xử lý thế nào?

- Phương án: (1) Chặn: lý do ngoại lệ cứng thuộc DANGER_MARKERS, agent không merge/bật auto-merge, người merge · (2) Cho qua: chấp nhận agent tự merge, sửa ADR-0016 và LOOP-STOP-005
- Chọn: Chặn: lý do ngoại lệ cứng thuộc DANGER_MARKERS, agent không merge/bật auto-merge, người merge
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1: LOOP-STOP-005 là MUST, merge tiền/auth/bí mật không đảo ngược được bằng revert khi đã chạy thật; chặn chặt hơn hỏi nên vẫn đúng tinh thần ADR-0018 (không dừng chờ — agent loop defer việc đó)
- Đường lùi: Bỏ HARD_ASK khỏi DANGER_MARKERS hoặc revert ADR-0019

### D-020 · 2026-10-17T18:41:51+00:00 · Ngoại lệ cứng 'auth' (RISK_PATH_RES) bắt nhầm .claude/hooks/session-start.sh (session = phiên agent) → agent bị chặn merge PR harness

- Phương án: (1) Miễn nhóm auth cho đường dẫn harness agent (.claude/, .xtemplates/, .codex/, .gemini/, .cursor/); vẫn vào làn chuẩn qua cổng/CI · (2) Bỏ 'session' khỏi regex auth · (3) So khớp nguyên từ (token)
- Chọn: Miễn nhóm auth cho đường dẫn harness agent (.claude/, .xtemplates/, .codex/, .gemini/, .cursor/); vẫn vào làn chuẩn qua cổng/CI
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1: code phiên/đăng nhập của ứng dụng vẫn là ngoại lệ cứng (PA2 nới lỏng nó); PA3 không sửa được vì session-start tách token 'session'. File harness đã có nhóm cổng/CI; guard.py (cùng thư mục) vốn đã tự merge được ở L3 — chỉ tên file trùng chữ
- Đường lùi: Bỏ điều kiện AGENT_HARNESS_RE trong merge_hard_reasons

### D-021 · 2026-10-17T18:48:50+00:00 · Duyệt PLAN T-1001…T-1005 (sửa audit dự án con: 1 🔴, 5 🟠, 🟢 tự làm được)

- Phương án: (1) Sửa cả guard/hook (đợt 1–3) + install/doctor/feedback/mẫu (đợt 4); chủ repo gọi /autopilot ngay sau báo cáo nêu đợt 1–2 chạm hook = duyệt; ADR-0018 cho agent sửa hook kèm lý do · (2) Chỉ làm đợt 4, để đợt 1–3 (hook) chờ người
- Chọn: Sửa cả guard/hook (đợt 1–3) + install/doctor/feedback/mẫu (đợt 4); chủ repo gọi /autopilot ngay sau báo cáo nêu đợt 1–2 chạm hook = duyệt; ADR-0018 cho agent sửa hook kèm lý do
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1: 🔴 SEC-044 là lỗ ngoại lệ cứng đang mở trên main của mọi dự án con; chủ repo gọi /autopilot sau báo cáo; mọi sửa chỉ CHẶT hơn (deny), có test đỏ trước, đảo ngược bằng revert
- Đường lùi: git revert từng commit lát; XT_GUARD_POLICY không đổi

### D-022 · 2026-10-17T18:57:55+00:00 · Mở PR khi nào với một nhánh duy nhất cho 5 lát?

- Phương án: (1) Mở một PR khi T-1005 xong (mọi lát là commit riêng), reviewer khác rà toàn diff, rồi merge-check/auto-merge · (2) Mở PR ngay sau T-1001 và bật auto-merge: PR có thể merge trước lát sau → phải dựng lại nhánh từ main giữa chừng
- Chọn: Mở một PR khi T-1005 xong (mọi lát là commit riêng), reviewer khác rà toàn diff, rồi merge-check/auto-merge
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1/3: tránh PR đã merge bị đẩy thêm commit; mỗi lát vẫn là commit riêng, revert được; review một lần trên diff hoàn chỉnh (D-016)
- Đường lùi: git revert từng commit lát

### D-023 · 2026-10-17T23:48:07+00:00 · Đồng bộ tài liệu điểm dừng với ADR-0018/0019: việc máy cho chạy nhưng chạm tiền thật/dữ liệu người dùng thật/gửi tin tới người dùng thật xếp vào đâu?

- Phương án: (1) Ba nhóm: máy chặn (deny) · cho chạy (deploy/publish, merge thường, sửa cổng/CI/hook kèm lý do, thêm phụ thuộc/MCP, ra mạng) · vẫn cần người qua loop defer (merge ngoại lệ cứng, thao tác trên tiền thật/dữ liệu người dùng thật kể cả gửi tin tới người dùng thật, đăng ký dịch vụ trả phí/nhập khoá thật, bế tắc máy) · (2) Hai nhóm: chỉ máy chặn và cho chạy; bỏ hẳn danh sách việc cần người khỏi AGENTS.md
- Chọn: Ba nhóm: máy chặn (deny) · cho chạy (deploy/publish, merge thường, sửa cổng/CI/hook kèm lý do, thêm phụ thuộc/MCP, ra mạng) · vẫn cần người qua loop defer (merge ngoại lệ cứng, thao tác trên tiền thật/dữ liệu người dùng thật kể cả gửi tin tới người dùng thật, đăng ký dịch vụ trả phí/nhập khoá thật, bế tắc máy)
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1: ADR-0018 chỉ mở việc có đường lùi (revert, unpublish, CI); thanh toán thật, xoá/xuất dữ liệu người dùng thật, tin đã gửi không thu hồi được và trùng ngoại lệ cứng ADR-0016/0019 (LOOP-STOP-005 MUST); PA2 bỏ chốt người duy nhất của nhóm rủi ro cao nhất mà ADR không quyết
- Đường lùi: Bỏ nhóm 'vẫn cần người' trong AGENTS.md §5 và mẫu dự án đích; ADR-0018 không đổi
