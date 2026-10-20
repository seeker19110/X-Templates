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

### D-024 · 2026-10-17T23:59:47+00:00 · Chủ repo chọn 'bỏ toàn bộ ngoại lệ cứng' (2026-10-17) — cài thế nào?

- Phương án: (1) Khoá xt.yaml merge_hard_exceptions: human|auto; thiếu khoá = human; repo khung + mẫu dự án đích đặt auto; merge-check vẫn liệt kê lý do (hard_waived) nhưng hard rỗng nên guard cho merge/auto-merge · (2) Xoá hẳn HARD_ASK và merge_hard_reasons khỏi code · (3) Dùng L4 làm mức bỏ ngoại lệ cứng
- Chọn: Khoá xt.yaml merge_hard_exceptions: human|auto; thiếu khoá = human; repo khung + mẫu dự án đích đặt auto; merge-check vẫn liệt kê lý do (hard_waived) nhưng hard rỗng nên guard cho merge/auto-merge
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 2 (đường lùi): đổi một dòng xt.yaml là bật lại chốt người, bản cài cũ thiếu khoá giữ hành vi an toàn; PA2 mất đường lùi và vết lý do; PA3 trái nghĩa L4 'làn kiến trúc luôn có người' trong bảng L0–L4. Lớp đỡ còn lại: required check gitleaks/CodeQL/dep-audit, guard deny việc không đảo ngược
- Đường lùi: merge_hard_exceptions: human trong xt.yaml (hoặc xoá khoá)

### D-025 · 2026-10-18T00:15:49+00:00 · Reviewer: mẫu templates/xt.yaml đặt merge_hard_exceptions: auto làm mọi dự án đích mới tự bỏ chốt người mà chưa ghi chấp nhận rủi ro (LOOP-STOP-005 MUST) — giữ auto hay về human?

- Phương án: (1) Mẫu về human; repo khung giữ auto (chủ repo chọn); dự án đích bật bằng một PR đổi khoá — PR đó luôn người merge (HARD_KEY_REASON) = lời chấp nhận rủi ro có dấu vết · (2) Giữ mẫu auto, doctor cảnh báo khi thiếu D-NNN
- Chọn: Mẫu về human; repo khung giữ auto (chủ repo chọn); dự án đích bật bằng một PR đổi khoá — PR đó luôn người merge (HARD_KEY_REASON) = lời chấp nhận rủi ro có dấu vết
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1: dự án đích có tiền/dữ liệu người dùng thật (vd hotel-manager); mặc định auto vi phạm MUST ngay khi cài và trái 'thiếu khoá = human'; PA1 vẫn cho chủ repo bật ở dự án của mình bằng một lần merge
- Đường lùi: Đặt merge_hard_exceptions: auto trong framework/templates/xt.yaml

### D-026 · 2026-10-18T00:34:11+00:00 · Cách làm 'mỗi PR kiểm merge mỗi 30 giây' (chủ repo: 2 phút rồi đổi 30 giây) — dùng gì, cho khung và dự án đích?

- Phương án: (1) Lệnh xt.py merge-watch (mặc định 30 s): vòng lặp trong tiến trình gọi lại merge-check, chạy nền, thoát khi verdict khác wait → agent được đánh thức; mọi harness dùng được; quy định thành bước bắt buộc sau khi mở PR · (2) /loop 30s trong phiên: mỗi lần kiểm là một lượt model, đốt token, chỉ chạy ở Claude Code, hết hạn 7 ngày · (3) Chỉ dựa vào sự kiện GitHub + auto-merge, không poll
- Chọn: Lệnh xt.py merge-watch (mặc định 30 s): vòng lặp trong tiến trình gọi lại merge-check, chạy nền, thoát khi verdict khác wait → agent được đánh thức; mọi harness dùng được; quy định thành bước bắt buộc sau khi mở PR
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 3 (bền, đơn giản, test được): poll tất định nằm trong code, không tốn token mỗi 30 s, test được bằng giả đồng hồ, dùng lại nguyên đường merge-check nên không có luật thứ hai; PA2 tốn token và chỉ một harness; PA3 trái yêu cầu chủ repo. Thêm: 30 s × ~6 lệnh REST mỗi lần ≈ 720 yêu cầu/giờ/PR, dưới hạn 5000/giờ của gh đã đăng nhập; nhiều PR song song thì nâng --interval
- Đường lùi: Bỏ bước merge-watch khỏi AGENTS.md/skill/mẫu; lệnh vẫn dùng được thủ công hoặc xoá cmd_merge_watch

### D-027 · 2026-10-18T00:53:38+00:00 · Hạn mức chạy autopilot 'x2, nếu không có thì x2 sau khi duyệt ở dự án đích' — hiểu và cài thế nào?

- Phương án: (1) Số mặc định nhân đôi (trần vòng max(40, 8×task chưa làm), 100 vòng khi không --single-session, merge-watch tối đa 240 phút, khuyến nghị --hours ≤ 16); chỉ áp khi PLAN bỏ trống số; số PLAN khai (--max-iterations, --hours) vẫn ưu tiên; có hiệu lực ở loop init = ngay sau duyệt PLAN ở dự án đích · (2) Chỉ nhân đôi ở dự án đích, repo khung giữ số cũ · (3) Nhân đôi cả số PLAN đã khai tường minh
- Chọn: Số mặc định nhân đôi (trần vòng max(40, 8×task chưa làm), 100 vòng khi không --single-session, merge-watch tối đa 240 phút, khuyến nghị --hours ≤ 16); chỉ áp khi PLAN bỏ trống số; số PLAN khai (--max-iterations, --hours) vẫn ưu tiên; có hiệu lực ở loop init = ngay sau duyệt PLAN ở dự án đích
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1/3: số tường minh là ý định đã ghi của chủ dự án nên không tự đổi; mặc định đổi ở một chỗ (loop init) nên dự án đích và repo khung dùng chung, không rẽ nhánh; PLAN trong mẫu đã nói 'bỏ trống = mặc định' nên khớp câu 'nếu không có thì x2'. Không nới hàng rào an toàn: breaker 80/90/100% và same_failure_count 3 giữ nguyên
- Đường lùi: Trả max(20, 4×task)/50/120 phút/--hours ≤ 8 trong xt.py, tài liệu và test

### D-028 · 2026-10-18T00:53:38+00:00 · Làm sao 'duyệt kế hoạch' bật tự động tới production mà vẫn có chốt người đúng một lần?

- Phương án: (1) Mục 'Ủy quyền production' trong PLAN.md dạng máy đọc (- grant: <nhóm> | khoá=giá trị …); xt.py grant-check kiểm đóng việc đang làm có nằm trong ủy quyền (thiếu = ngoài); PR đổi dòng grant hoặc khoá merge_hard_exceptions luôn người merge, nên người merge PR duyệt kế hoạch = lời chấp nhận rủi ro duy nhất · (2) Khoá cấu hình trong xt.yaml cho từng nhóm · (3) Chỉ dặn trong AGENTS.md, không máy kiểm
- Chọn: Mục 'Ủy quyền production' trong PLAN.md dạng máy đọc (- grant: <nhóm> | khoá=giá trị …); xt.py grant-check kiểm đóng việc đang làm có nằm trong ủy quyền (thiếu = ngoài); PR đổi dòng grant hoặc khoá merge_hard_exceptions luôn người merge, nên người merge PR duyệt kế hoạch = lời chấp nhận rủi ro duy nhất
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1/2/3: PLAN do phiên chính tự duyệt (ADR-0008) nên tự cấp ủy quyền cho chính mình là lỗ; bắt PR đổi grant cần người merge vá lỗ đó mà chỉ đòi người một lần; grant-check đóng khi thiếu nên mặc định không cho gì; PA3 là lời dặn không phải cơ chế
- Đường lùi: Bỏ nhánh PLAN.md khỏi _touches_hard_key và xoá cmd_grant_check; AGENTS.md §5 về như D-023

### D-029 · 2026-10-18T01:44:29+00:00 · Job CI bắt buộc merge-gate (đóng lỗ auto-merge không ghim head, ADR-0022): đỏ khi nào để chốt người vẫn merge được?

- Phương án: (1) Đỏ khi merge-check báo hard VÀ PR đang bật auto-merge (REST auto_merge); chạy lại khi bật/tắt auto-merge (pull_request_target auto_merge_enabled/disabled); PR hard không auto-merge thì xanh kèm cảnh báo để người merge tay · (2) Luôn đỏ khi hard: người cũng không merge được vì ruleset không có bypass_actors và tác giả PR là chủ repo (không tự approve được) — PR đổi grant/khoá thành không merge được · (3) Luôn đỏ khi hard + thêm bypass (vai trò admin) vào ruleset: người merge bằng bypass, nhưng bypass vượt MỌI required check (quality, gitleaks…)
- Chọn: Đỏ khi merge-check báo hard VÀ PR đang bật auto-merge (REST auto_merge); chạy lại khi bật/tắt auto-merge (pull_request_target auto_merge_enabled/disabled); PR hard không auto-merge thì xanh kèm cảnh báo để người merge tay
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1 (đúng, an toàn): lỗ là auto-merge bật trước rồi push commit hard — PA1 bắt đúng đường đó bằng máy trên head hiện tại; merge tay của agent đã có guard ghim head (merge-check lúc merge), merge tay của người là chốt người theo thiết kế ADR-0016/0022. PA2 làm hỏng chốt người (người không merge được nếu không sửa ruleset). PA3 nới mọi cổng khác. Tiêu chí 3: logic ở xt.py merge-gate có test, workflow chỉ gọi lệnh
- Đường lùi: Đổi điều kiện trong cmd_merge_gate thành chỉ xét hard (PA2) kèm thêm bypass vào ruleset (PA3), hoặc bỏ merge-gate khỏi ruleset và xoá merge-gate.yml

### D-030 · 2026-10-18T01:48:48+00:00 · Chủ repo: 'bật auto-merge khi review sạch, không bật được thì tự merge, áp cho mọi PR, cả dự án đích' — cài vào khung thế nào?

- Phương án: (1) Mọi PR: mở → reviewer (model khác) rà diff → không còn lỗi chặn (nên sửa đã sửa/trả lời) và merge-check không hard → bật auto-merge; enable lỗi (PR đã sẵn sàng/repo tắt auto-merge) → merge trực tiếp bằng lệnh ghim head trong next của merge-check; còn lỗi chặn → sửa, đẩy, rà lại; ghi ở AGENTS.md, mẫu AGENTS.md, skill /autopilot, LOOP-STOP-022, LOOP-DESIGN-020 · (2) Chỉ PR làn chuẩn chờ review, làn nhanh bật auto-merge khi mở
- Chọn: Mọi PR: mở → reviewer (model khác) rà diff → không còn lỗi chặn (nên sửa đã sửa/trả lời) và merge-check không hard → bật auto-merge; enable lỗi (PR đã sẵn sàng/repo tắt auto-merge) → merge trực tiếp bằng lệnh ghim head trong next của merge-check; còn lỗi chặn → sửa, đẩy, rà lại; ghi ở AGENTS.md, mẫu AGENTS.md, skill /autopilot, LOOP-STOP-022, LOOP-DESIGN-020
- Lý do (tiêu chí chất lượng cuối): Chủ repo chọn rõ 'áp cho mọi PR'; tiêu chí 1: đã thấy ở #102 mỗi vòng review bắt thêm lỗ an ninh thật trước khi merge; merge trực tiếp chỉ qua lệnh ghim head nên không merge commit chưa được rà; không đổi code guard (merge-check verdict merge vẫn là điều kiện)
- Đường lùi: Về 'mở PR là bật auto-merge' (ADR-0015) trong 5 chỗ tài liệu

### D-031 · 2026-10-18T02:24:00+00:00 · Chủ repo đổi quy tắc: 'chỉ review lại trước những PR quan trọng, rồi sau đó tạo PR auto merge, còn lại bật auto merge tự động' — 'PR quan trọng' xác định thế nào?

- Phương án: (1) PR quan trọng = merge-check báo làn chuẩn (vị từ máy LOOP-STOP-009: đường dẫn nhạy cảm cổng/CI/hook/schema/phụ thuộc, nhãn risk:, ngoại lệ cứng, > 150 dòng, nhiều gói, đổi mã không đổi test): review ở commit H rồi mới bật auto-merge; làn nhanh bật auto-merge ngay khi mở; tắt auto-merge trước mỗi push rồi chạy lại merge-check (làn đổi sang chuẩn thì rà) · (2) Agent tự phán đoán PR nào quan trọng theo nội dung diff · (3) Chỉ PR có ngoại lệ cứng (hard) là quan trọng
- Chọn: PR quan trọng = merge-check báo làn chuẩn (vị từ máy LOOP-STOP-009: đường dẫn nhạy cảm cổng/CI/hook/schema/phụ thuộc, nhãn risk:, ngoại lệ cứng, > 150 dòng, nhiều gói, đổi mã không đổi test): review ở commit H rồi mới bật auto-merge; làn nhanh bật auto-merge ngay khi mở; tắt auto-merge trước mỗi push rồi chạy lại merge-check (làn đổi sang chuẩn thì rà)
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1+3: vị từ máy có sẵn, test được, không phụ thuộc phán đoán; bắt rộng có chủ đích (báo oan chỉ tốn một lượt review); gồm mọi vùng từng lộ lỗ an ninh ở #102 (xt.py cổng/CI, nhiều gói); phương án 3 bỏ sót sửa guard/CI; phương án 2 không kiểm được
- Đường lùi: Về D-030 (review mọi PR) hoặc ADR-0015 (bật khi mở) trong cùng các chỗ tài liệu
- Đính chính (review lần bốn #103): vị từ chung KHÔNG coi `scripts/xt.py` của repo khung là nhạy cảm — PR nhỏ sửa nó
  từng vào làn nhanh. Vá: `xt.yaml` của repo khai `merge_risk_paths` (`scripts/*`, luật vòng tự động, mẫu, ADR); test
  `test_framework_repo_risk_paths`.

### D-032 · 2026-10-18T02:49:04+00:00 · Hai lỗ của merge-check từ review #103: merge_risk_paths đọc ở cây làm việc (checkout cũ làm rơi glob); khoá merge_hard_exceptions dò bằng chuỗi trong patch (báo hard nhầm) — sửa thế nào?

- Phương án: (1) Glob = hợp cây làm việc và xt.yaml đã commit ở nhánh đích; khoá: so giá trị hiệu lực đã parse (cùng bộ đọc merge_hard_mode, thiếu = human) ở đáy/đầu PR qua REST contents, không đọc được hay vắng cả hai đầu → hard · (2) Glob chỉ đọc ở nhánh đích; khoá giữ dò chuỗi nhưng chỉ trên dòng +/- của patch
- Chọn: Glob = hợp cây làm việc và xt.yaml đã commit ở nhánh đích; khoá: so giá trị hiệu lực đã parse (cùng bộ đọc merge_hard_mode, thiếu = human) ở đáy/đầu PR qua REST contents, không đọc được hay vắng cả hai đầu → hard
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1: hợp glob không bao giờ ít hơn nguồn nào (sửa tại chỗ chỉ chặt hơn, gỡ glob phải qua PR làn chuẩn); so giá trị parse bằng đúng bộ đọc của merge_hard_mode nên khớp nghĩa tuyệt đối, vẫn đóng khi không xác minh được; dò dòng +/- vẫn sai với khoá lặp/viết lại và còn phụ thuộc patch (thiếu khi diff lớn)
- Đường lùi: Về dò chuỗi patch (_touches_hard_key cũ) và merge_config(project_dir()) ở _merge_eval
- Đính chính (review #105): "khớp nghĩa tuyệt đối" sai — giá trị sau merge do merge 3 chiều theo dòng quyết định,
  khoá lặp bị dòng sau che lọt qua phép so giá trị hiệu lực. Sửa: so danh sách MỌI dòng khoá theo thứ tự; đáy là
  merge-base (REST compare) thay `base.sha`, áp cả ủy quyền PLAN.md.

### D-033 · 2026-10-18T03:09:25+00:00 · Đóng tiếp lỗ chốt merge (review #105 + yêu cầu chủ repo 'sửa luôn merge_autonomy đọc từ nhánh đích'): mức tự chủ lấy từ đâu, và ủy quyền PLAN.md/khoá lặp lọt qua merge 3 chiều thì chặn thế nào?

- Phương án: (1) merge_autonomy = min(cây làm việc, nhánh đích đã commit), không đọc được → L1; PLAN.md: so danh sách mọi dòng grant theo thứ tự kèm cờ fence ở merge-base/head, đầu PR có grant trong fence hoặc nhóm lặp → hard; xt.yaml: đầu PR có > 1 dòng khoá → hard · (2) merge_autonomy chỉ đọc nhánh đích; PLAN.md giữ so hiệu lực, cấm thêm dòng grant qua PR làn nhanh
- Chọn: merge_autonomy = min(cây làm việc, nhánh đích đã commit), không đọc được → L1; PLAN.md: so danh sách mọi dòng grant theo thứ tự kèm cờ fence ở merge-base/head, đầu PR có grant trong fence hoặc nhóm lặp → hard; xt.yaml: đầu PR có > 1 dòng khoá → hard
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1: min không bao giờ cao hơn nhánh đích (nâng mức phải qua PR đã merge, PR đó quyết ở mức cũ), vẫn cho chủ hạ tại chỗ; mỗi nhóm grant một dòng, không fence và cùng chuỗi dòng ở mọi bên thì merge 3 chiều chỉ ra tập con của merge-base — chặt hơn, không nới; so hiệu lực bị tái hiện lọt (PR chèn live bị sandbox che + PR dời sandbox = live)
- Đường lùi: merge_autonomy về merge_config(project_dir()); _plan_grants_changed về so parse_grants

### D-034 · 2026-10-18T03:10:09+00:00 · Blueprint tick là lời khai (blueprint_status chỉ đếm ô [x]) — biến thành bằng chứng máy thế nào?

- Phương án: (1) Ghi chú — Kiểm: `<lệnh>` trên mục [x]; blueprint-status --run và loop verify chạy lại; đỏ = chưa đạt; MUST tick không có lệnh chỉ báo (unchecked_must), không đỏ · (2) Bắt buộc mọi MUST [x] có lệnh kiểm, thiếu là đỏ ngay · (3) Thêm trường check: máy đọc vào mục khung (framework), compose sinh lệnh
- Chọn: Ghi chú — Kiểm: `<lệnh>` trên mục [x]; blueprint-status --run và loop verify chạy lại; đỏ = chưa đạt; MUST tick không có lệnh chỉ báo (unchecked_must), không đỏ
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1/3: lệnh do dự án khai nên đúng stack, máy chạy lại được và test được; đi qua loop verify có sẵn nên Stop hook chặn 'done' sai mà không thêm luật mới; PA2 làm hỏng blueprint đã tick của dự án đang chạy (hotel-manager) và nhiều mục chỉ kiểm bằng tài liệu/URL; PA3 không khả thi vì phần Kiểm của khung là văn xuôi theo nhiều stack. Đường lùi giữ: siết PA2 sau khi unchecked_must có số đo
- Đường lùi: Bỏ cờ --run và _verify_blueprint; CHECK_CMD_RE/ghi chú — Kiểm: vẫn vô hại như ghi chú thường

### D-035 · 2026-10-18T03:20:01+00:00 · Gate do agent tự khai không có sàn (ADR-0011 chỉ chặn rỗng/no-op) — đặt sàn ở đâu để có răng mà ít code?

- Phương án: (1) gate_floor_issues trong xt.py: doctor cảnh báo + loop init nhắc + loop verify ĐỎ ở M/L (kiểm kiểu, kiểm format, ngưỡng coverage, e2e theo hồ sơ), dấu hiệu tất định từ xt.yaml + file cấu hình · (2) Mở rộng is_noop trong dev-task.sh để cổng commit đỏ ngay khi dưới sàn · (3) Chỉ ghi luật vào AGENTS.md/skill, không máy kiểm
- Chọn: gate_floor_issues trong xt.py: doctor cảnh báo + loop init nhắc + loop verify ĐỎ ở M/L (kiểm kiểu, kiểm format, ngưỡng coverage, e2e theo hồ sơ), dấu hiệu tất định từ xt.yaml + file cấu hình
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1/3: răng đặt ở loop verify — điểm máy đã chặn done — nên không thêm luồng mới, logic Python có test và chạy chung cho mọi stack; PA2 phải dò stack bằng bash ở mọi commit, chậm và khó test, lại chặn cả commit sửa tài liệu; PA3 là lời dặn, chính là lỗ đang vá. Chỉ áp M/L vì S là sàn baseline (ADR-0003); sàn là dấu hiệu tất định, ngưỡng thấp vẫn qua — review bù
- Đường lùi: Xoá _doctor_gate_floor khỏi doctor_findings và nhánh floor trong loop_verify/_loop_init; hằng FLOOR_* không ảnh hưởng gì khác
- Đính chính (review #107): dò tên công cụ bằng regex đỏ oan với stack lạ (deno, dotnet, gradle, dart) và lọt với cờ
  trùng tên (`black -l`, `go test -cover`, `fail_under` khi không bật coverage). Thay bằng khoá khai báo `format_check`,
  `coverage` (+ `typecheck`/`build`, `e2e` theo stack/hồ sơ) phải khác rỗng/no-op và `loop verify` chạy chúng; bỏ mọi regex tên công cụ.

### D-036 · 2026-10-18T03:56:29+00:00 · Phạm vi /autopilot không đối số sau việc 1–2: làm tiếp những đề xuất nào (3 máy trạng thái merge, 4 sàn quyền token, 5 số đo vòng, 6 đóng gói xt.pyz)?

- Phương án: (1) Làm 5 (số đo vòng) và 3 (máy trạng thái merge theo làn trong code, rút văn xuôi), cộng đưa #108 về main; 4 và 6 không làm trong lượt này · (2) Làm cả 3, 4, 5, 6 · (3) Chỉ đưa #108 về main
- Chọn: Làm 5 (số đo vòng) và 3 (máy trạng thái merge theo làn trong code, rút văn xuôi), cộng đưa #108 về main; 4 và 6 không làm trong lượt này
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1/3: 5 và 3 chỉ sửa xt.py có test, giảm lỗi thực thi (văn xuôi merge theo làn 7 nhánh lồng, sửa 9 file mỗi lần đổi luật); 5 làm trước để có số đo cho mọi tinh chỉnh sau. 4 cần chủ repo đổi quyền token/tài khoản — không làm được từ repo. 6 đổi hợp đồng cài đặt của dự án đích: ADR-0010 đòi đủ ngưỡng phản hồi (≥ 2 dự án hoặc có tái hiện), hiện mới 1 dự án đích
- Đường lùi: Thêm task 4/6 vào PLAN sau khi có dữ liệu từ dự án đích hoặc chủ repo quyết quyền token

### D-037 · 2026-10-18T03:56:29+00:00 · Số đo vòng autopilot (LOOP-DESIGN-016/018) lấy từ đâu khi evidence/T-xxx.json bị ghi đè mỗi lần record?

- Phương án: (1) loop record nối một dòng vào .autopilot/runs.jsonl (task, exit, chữ ký lỗi, thời điểm, head); lệnh mới xt.py loop stats tính số lần chạy/task, tỉ lệ xanh lần đầu, task bị blocked/defer, vòng đã dùng · (2) Đọc git log + PLAN để suy ra · (3) Gửi số đo ra dịch vụ ngoài
- Chọn: loop record nối một dòng vào .autopilot/runs.jsonl (task, exit, chữ ký lỗi, thời điểm, head); lệnh mới xt.py loop stats tính số lần chạy/task, tỉ lệ xanh lần đầu, task bị blocked/defer, vòng đã dùng
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1/3: chỉ ghi nối cục bộ (.autopilot/ đã gitignore, không lộ ra repo), tất định, test được; git log không thấy lần Gate đỏ; dịch vụ ngoài cần tài khoản (mặc định tự host)
- Đường lùi: Bỏ dòng ghi runs.jsonl trong loop_record và xoá _loop_stats

### D-038 · 2026-10-18T03:56:29+00:00 · Quy trình merge theo làn (7 bước văn xuôi, chép ở AGENTS/skill/LOOP-STOP-022/mẫu) đưa vào code thế nào mà guard vẫn là người chặn?

- Phương án: (1) Lệnh xt.py pr next --pr N: hàm thuần đọc merge-check JSON + sổ review .autopilot/reviews.json (pr reviewed --pr N --head H --clean|--blocking) và trả MỘT hành động kế tiếp (bật/tắt auto-merge, rà H..head, merge ghim head, chờ, đổi đích, defer); không tự gọi GitHub; văn xuôi các nơi rút về 'chạy pr next, làm đúng next' · (2) Lệnh tự thực thi (gọi gh/MCP bật auto-merge, merge) · (3) Giữ văn xuôi, thêm checklist
- Chọn: Lệnh xt.py pr next --pr N: hàm thuần đọc merge-check JSON + sổ review .autopilot/reviews.json (pr reviewed --pr N --head H --clean|--blocking) và trả MỘT hành động kế tiếp (bật/tắt auto-merge, rà H..head, merge ghim head, chờ, đổi đích, defer); không tự gọi GitHub; văn xuôi các nơi rút về 'chạy pr next, làm đúng next'
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1/3: quyết định tất định có test thay cho 7 nhánh lồng mà model phải nhớ; không tự thực thi nên guard/MCP vẫn là lớp chặn và phiên chặn GraphQL vẫn dùng được; PA2 trùng đường merge của guard và cần token; PA3 không giảm lỗi
- Đường lùi: Giữ lệnh nhưng trả văn xuôi cũ ở AGENTS/skill/LOOP-STOP-022 (ADR-0024)

### D-039 · 2026-10-18T03:56:50+00:00 · Duyệt PLAN 2026-10-18 (T-1101…T-1104: #108 về main, số đo vòng, máy trạng thái merge pr next)

- Phương án: (1) Duyệt như viết: 4 task, 3 lát, mỗi lát một PR, 40 vòng/8 giờ · (2) Gộp B và C một PR
- Chọn: Duyệt như viết: 4 task, 3 lát, mỗi lát một PR, 40 vòng/8 giờ
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1/3: mỗi task có Gate máy kiểm, lát nhỏ độc lập về hành vi, không phụ thuộc mới, không đụng điểm dừng; mỗi lát một PR theo ADR-0014
- Đường lùi: Sửa PLAN và loop init lại

### D-040 · 2026-10-18T05:22:04+00:00 · Dự án đích không biết khung đã cài lỗi thời (VERSION 2.0.0 trong khi 58 commit, 35 mục CHANGELOG đòi chạy lại install.py) — làm gì rẻ mà chắc?

- Phương án: (1) Cắt bản phát hành 3.0.0 (ADR-0007 đã định) qua release-tag.yml; doctor (đầy đủ) đọc tag vX.Y.Z mới nhất qua gh api, cảnh báo khi .xtemplates/VERSION cũ hơn; fail-open khi không có gh/mạng; luật cắt bản khi thay đổi buộc dự án đích làm gì ghi ở AGENTS.md §7 · (2) Đóng gói xt.pyz tự cập nhật · (3) Chỉ ghi nhắc trong CHANGELOG
- Chọn: Cắt bản phát hành 3.0.0 (ADR-0007 đã định) qua release-tag.yml; doctor (đầy đủ) đọc tag vX.Y.Z mới nhất qua gh api, cảnh báo khi .xtemplates/VERSION cũ hơn; fail-open khi không có gh/mạng; luật cắt bản khi thay đổi buộc dự án đích làm gì ghi ở AGENTS.md §7
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1/3: giải đúng chỗ đau (không biết mình cũ) bằng vài chục dòng có test, không đổi đường nạp guard; fail-open nên không chặn phiên offline; 3.0.0 vì ADR-0007 đổi định danh là phá vỡ. xt.pyz đổi cấu trúc khi mới 1 dự án đích (ADR-0010); nhắc bằng lời là lời khai
- Đường lùi: Bỏ _doctor_version khỏi doctor_findings; tag đã cắt giữ nguyên

### D-041 · 2026-10-18T11:57:47+00:00 · Vòng tối ưu hiệu năng trong autopilot: đưa vào khung thế nào?

- Phương án: (1) Module LOOP-OPT + công cụ xt.py perf sample/compare/guard (thống kê Mann-Whitney + sàn nhiễu, khoá bộ đo, Gate lấy công cụ từ commit gốc) · (2) Chỉ thêm văn xuôi vào XC-PERF, không máy đỡ · (3) Tích hợp sâu vào loop (kiểu task [perf], loop init kiểm Gate)
- Chọn: Module LOOP-OPT + công cụ xt.py perf sample/compare/guard (thống kê Mann-Whitney + sàn nhiễu, khoá bộ đo, Gate lấy công cụ từ commit gốc)
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1/3: số đo là tín hiệu agent dễ làm giả nhất (METR, GSO, SWE-fficiency) nên cần máy quyết giữ/hoàn tác và khoá bộ đo; stdlib, có test; tích hợp loop để sau khi có dữ liệu dùng thật
- Đường lùi: Bỏ mục LOOP-OPT (đổi MAY + Ngừng dùng) và lệnh perf; không đụng lệnh khác

### D-042 · 2026-10-18T11:57:47+00:00 · perf guard: file chưa theo dõi lọc ignore thế nào để vừa không lọt file khoá mới vừa không đỏ oan vì file sinh khi đo?

- Phương án: (1) Không lọc ignore (mọi file chưa theo dõi) · (2) Lọc theo --exclude-standard (gồm core.excludesFile, .git/info/exclude) · (3) Lọc theo .gitignore trong cây; có .gitignore đổi/mới thì kiểm khoá trên mọi file chưa theo dõi
- Chọn: Lọc theo .gitignore trong cây; có .gitignore đổi/mới thì kiểm khoá trên mọi file chưa theo dõi
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1/3/4: (1) đỏ oan __pycache__/.venv dẫn agent nới --locked; (2) excludesFile/info/exclude đổi được không để dấu; (3) chỉ tin .gitignore đã commit ở base, đổi nó thì quay về kiểm toàn bộ
- Đường lùi: Đổi PERF_UNTRACKED và nhánh _perf_is_ignore_file trong perf_diff

### D-043 · 2026-10-18T11:57:47+00:00 · Phát hành 3.2.0 ngay, hay gộp đợt nâng cấp autopilot (reviewer khác model có máy kiểm, LOOP-DESIGN-022 thành MUST@M) vào cùng bản?

- Phương án: (1) Phát hành 3.2.0 ngay với phần đã review sạch; đợt nâng cấp ra bản sau · (2) Gộp đợt nâng cấp vào 3.2.0
- Chọn: Phát hành 3.2.0 ngay với phần đã review sạch; đợt nâng cấp ra bản sau
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 2/5: 3.2.0 có ba thay đổi đã review sạch mà dự án đích cần (guard ghi công AI, LOOP-OPT, perf); gộp thêm phải review lại, chậm bản mà không tăng an toàn; đợt sau ra vài giờ sau
- Đường lùi: Cắt bản kế tiếp (3.2.1/3.3.0) chứa đợt nâng cấp

### D-044 · 2026-10-18T12:19:52+00:00 · Bộ test tấn công guard: làm ngay sinh biến thể + bộ lệnh hợp lệ, hay để sau đợt nâng autopilot?

- Phương án: (1) Làm ngay: sinh biến thể tất định từ lệnh hạt giống + bộ lệnh hợp lệ chống chặn nhầm · (2) Để sau đợt 1 (reviewer khác model, LOOP-DESIGN-022)
- Chọn: Làm ngay: sinh biến thể tất định từ lệnh hạt giống + bộ lệnh hợp lệ chống chặn nhầm
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1/3/5: #125/#127/#128 mỗi vòng review đều tìm lỗ mới qua cổng xanh 100%; máy sinh biến thể bắt trước reviewer, bộ hợp lệ giữ không chặn nhầm; chỉ thêm test, rẻ
- Đường lùi: Xoá tests/test_guard_corpus.py

### D-045 · 2026-10-18T12:31:38+00:00 · Máy kiểm 'reviewer khác model' (LOOP-STOP-022) thế nào khi không có biến môi trường cho biết model phiên chính?

- Phương án: (1) pr reviewed --clean bắt khai --reviewer-model/--author-model, cùng họ thì từ chối, ghi vào sổ · (2) Đọc model từ transcript của phiên qua hook · (3) Giữ lời dặn trong tài liệu
- Chọn: pr reviewed --clean bắt khai --reviewer-model/--author-model, cùng họ thì từ chối, ghi vào sổ
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1/3: bắt đúng lỗi thật (reviewer ghim opus khi phiên chính là Opus), ghi vết soát được, stdlib có test; transcript là định dạng nội bộ dễ đổi; lời dặn đã thất bại
- Đường lùi: Bỏ _review_models_error, để --reviewer-model/--author-model tuỳ chọn

### D-046 · 2026-10-18T12:54:52+00:00 · Ghi/xoá tay .autopilot/ (bằng chứng, verified.json, sổ review): hỏi rồi cho qua như ADR-0018, hay chặn?

- Phương án: (1) Chặn ở chính sách mặc định (dấu 'tay bằng chứng' trong DANGER_MARKERS), chỉ xt.py ghi; người sửa tay hoặc loop init --force · (2) Giữ hỏi→cho qua, dựa vào loop verify chạy lại Gate · (3) Ký HMAC evidence bằng khoá ngoài agent
- Chọn: Chặn ở chính sách mặc định (dấu 'tay bằng chứng' trong DANGER_MARKERS), chỉ xt.py ghi; người sửa tay hoặc loop init --force
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1/3: bằng chứng ghi tay là đúng thứ P1 cấm và Stop hook đọc chính các file này; guard đã nhận diện sẵn, chỉ thiếu dấu; HMAC cần khoá agent không đọc được — chưa có chỗ giữ trong phiên agent
- Đường lùi: Bỏ 'tay bằng chứng' khỏi DANGER_MARKERS (ADR-0026 → bị thay)

### D-047 · 2026-10-18T13:45:07+00:00 · Bịt lỗ guard còn lại (biến gán chữ, lệnh bọc flock/watch/script/su/busybox/coproc, $'…', ${IFS}, <( ), os.system, find/xargs vào .autopilot/): quét ở độ sâu nào và nhận diện lệnh bọc thế nào?

- Phương án: (1) Bản viết lại CÙNG lệnh (thay biến, hậu tố đối số của lệnh bọc) quét ở cùng độ sâu; lệnh bọc nhận theo danh sách + thử mọi hậu tố của đối số; chuỗi trong lời gọi thực thi (os.system, subprocess, execSync) là lệnh · (2) Tăng MAX_NEST để vừa độ sâu mới; nhận lệnh bọc bằng bảng cờ riêng từng lệnh · (3) Hạ các dạng này xuống ask (opaque) — để cho qua theo ADR-0018
- Chọn: Bản viết lại CÙNG lệnh (thay biến, hậu tố đối số của lệnh bọc) quét ở cùng độ sâu; lệnh bọc nhận theo danh sách + thử mọi hậu tố của đối số; chuỗi trong lời gọi thực thi (os.system, subprocess, execSync) là lệnh
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1/3: bản viết lại không phải shell lồng nên không nên tốn độ sâu (var_eval + env đẩy chạm trần 3 và thành ask → lọt); hậu tố thay bảng cờ vì tuỳ chọn mỗi lệnh khác nhau và bảng sai là lỗ mới; ask thì cho qua nên không chặn gì. Chặn chỉ tính trên lệnh sẽ bị chặn nếu chạy trực tiếp nên không thêm chặn nhầm
- Đường lùi: Bỏ _var_scripts/_runner_scripts/_procsub_scripts/_exec_api_scripts khỏi _scan_nested, expand_ansi_c/IFS_RE khỏi tokenize; ca trong GuardRemainingGapsTest chuyển lại KNOWN_GAPS

### D-048 · 2026-10-18T14:03:18+00:00 · Cổng render UI lấy từ XIAS (vendor mã MIT, giữ ghi chú bản quyền) hay tự viết mẫu?

- Phương án: (1) Chép verify_states/target_size/overflow/axe_audit của plugin87/ux-ui-agent-skills (MIT) vào khung, giữ ghi chú bản quyền · (2) Tự viết mẫu verify-render.mjs (Playwright + axe) theo ý tưởng, không chép mã, chạy thử trên fixture; ghi XIAS là nguồn ý tưởng · (3) Chỉ ghi vào checklist, không kèm mã
- Chọn: Tự viết mẫu verify-render.mjs (Playwright + axe) theo ý tưởng, không chép mã, chạy thử trên fixture; ghi XIAS là nguồn ý tưởng
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1/3: stored §7d.2 thấy XIAS chép dữ liệu từ hai kho MIT khác không ghi nguồn và cổng gọi chromium channel 'chrome' (fail ở sandbox, 49/52 khi tự chạy); chép nguyên kéo theo nghĩa vụ bản quyền + lỗi môi trường. Mẫu tự viết nhỏ (≈100 dòng), dùng Chromium của Playwright, đã chạy: tốt exit 0, xấu exit 1 (hover 1,76:1, tràn ngang, primary 4,10:1), thiếu đích/Chromium exit 2
- Đường lùi: Xoá framework/templates/ui-gates/ và dòng bảng ở templates/README.md, UX-A11Y-028/029 và Cổng tự động trong accessibility.md trở về chỉ mô tả Playwright

### D-049 · 2026-10-18T14:03:18+00:00 · Kiểm tương phản token và license vendor: viết trong xt.py (stdlib Python) hay thành script Node/gói riêng?

- Phương án: (1) Thêm xt.py contrast và xt.py vendor-check (stdlib, có test, 100% coverage), danh sách theo dõi license ở JSON trong framework/ · (2) Script Node check-contrast.mjs chép vào từng dự án (như checklist cũ gợi ý) · (3) Dùng linter DESIGN.md của Google cho mọi việc tương phản
- Chọn: Thêm xt.py contrast và xt.py vendor-check (stdlib, có test, 100% coverage), danh sách theo dõi license ở JSON trong framework/
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1/3: khung chỉ phụ thuộc stdlib Python, mọi dự án đích đã có xt.py (không cần Node cho dự án không có frontend), test được và đo coverage; DESIGN.md lint chỉ phủ khi có DESIGN.md và tương phản chỉ là warning exit 0 nên không thay được cổng token CSS. Giữ lint DESIGN.md làm mục riêng UX-DS-021. Danh sách theo dõi license để JSON có ngày xác minh nên sửa không cần đổi mã
- Đường lùi: Xoá cmd_contrast, cmd_vendor_check và hằng liên quan khỏi xt.py, tests/test_ui_gates.py, ui-vendor-watchlist.json; đổi Kiểm của UX-DS-003/011/020, UX-A11Y-002, CMP-LIC-022, FE-START-* về lệnh mô tả

### D-050 · 2026-10-18T14:20:18+00:00 · Quét guard bị nổ tổ hợp (biến nhân đôi, lệnh bọc lồng) làm hook quá hạn và lệnh chạy không qua guard: xử lý thế nào?

- Phương án: (1) Ngân sách quét mỗi quyết định (600 lệnh con, 8 giây, tập script đã quét, 4 lần viết lại lồng) — hết thì CHẶN · (2) Chỉ cắt độ dài giá trị biến và số hậu tố, không có ngân sách chung · (3) Bỏ quét biến/lệnh bọc (về trạng thái 3.3.0)
- Chọn: Ngân sách quét mỗi quyết định (600 lệnh con, 8 giây, tập script đã quét, 4 lần viết lại lồng) — hết thì CHẶN
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1/3: reviewer #134 tái hiện N=21 lần nhân đôi mất 177 s, N=22 vượt timeout hook 600 s nên rm -rf ~ chạy không qua guard; cắt từng chỗ để lại các đường nổ khác (flock lồng, biến chuỗi) — ngân sách chung là hàng rào duy nhất bảo đảm kết thúc; hết ngân sách thì chặn (fail-closed) vì lệnh bình thường dùng < 20 lệnh con; tập script đã quét biến nổ tổ hợp thành đa thức
- Đường lùi: Bỏ ScanBudget và tham số budget/rewrites khỏi bash_decision/_scan_scripts/_scan_nested; hạn chế bằng VAR_VALUE_MAX và RUNNER_SUFFIXES

### D-051 · 2026-10-18T23:12:57+00:00 · Duyệt PLAN 3.4.1 (bịt Còn lọt của guard + contrast CSS lồng)

- Phương án: (1) Làm cả guard và contrast, 3 PR, giữ getattr ghép chuỗi ngoài phạm vi · (2) Chỉ vá base64 và .autopilot, để phần còn lại
- Chọn: Làm cả guard và contrast, 3 PR, giữ getattr ghép chuỗi ngoài phạm vi
- Lý do (tiêu chí chất lượng cuối): Chủ repo đã nhận đề xuất làm hết; ghép chuỗi lúc chạy là né cố ý, ngoài phạm vi guard chống tai nạn
- Đường lùi: revert từng PR

### D-052 · 2026-10-18T23:22:42+00:00 · Guard: xử lý biến từ thay lệnh/read và lệnh mã hoá vào shell thế nào

- Phương án: (1) Tính giá trị khi nguồn là chữ (echo/printf/read <<<, base64/xxd/rev) rồi quét; nguồn mã hoá không giải được thì chặn · (2) Chặn mọi biến không rõ giá trị dùng làm lệnh · (3) Giữ hỏi (cho qua theo ADR-0018)
- Chọn: Tính giá trị khi nguồn là chữ (echo/printf/read <<<, base64/xxd/rev) rồi quét; nguồn mã hoá không giải được thì chặn
- Lý do (tiêu chí chất lượng cuối): Bịt đúng ca tai nạn có chữ nguyên văn mà không chặn nhầm $(git …)/read từ biến; lệnh mã hoá không giải được không có lý do hợp lệ để agent chạy
- Đường lùi: revert PR guard 3.4.1

### D-053 · 2026-10-18T23:22:42+00:00 · contrast: xử lý CSS lồng (&.dark) thế nào

- Phương án: (1) Ghép selector con với cha (& thay bằng cha, không & là con cháu), khai báo con tách khỏi cha · (2) Bỏ qua khối lồng
- Chọn: Ghép selector con với cha (& thay bằng cha, không & là con cháu), khai báo con tách khỏi cha
- Lý do (tiêu chí chất lượng cuối): Đúng ngữ nghĩa CSS Nesting; bỏ qua làm mất token tối và vẫn rò khai báo
- Đường lùi: revert PR contrast

### D-054 · 2026-10-19T02:05:01+00:00 · PR đủ tiêu chuẩn vẫn không vào main khi không có phiên agent chạy pr next (phiên dừng, container khởi động lại, PR của phiên khác) — quản lý thế nào

- Phương án: (1) PR steward chạy trên GitHub Actions (lịch 10 phút + comment review + chạy tay) gọi pr next cho mọi PR mở và tự bật auto-merge/merge ghim head; pr reviewed đăng kết quả review lên PR (marker, không tên model) để steward đọc · (2) Bật auto-merge cho mọi PR ngay khi mở, để ruleset/required check chặn · (3) Giữ như cũ, dặn phiên agent đặt send_later check-in
- Chọn: PR steward chạy trên GitHub Actions (lịch 10 phút + comment review + chạy tay) gọi pr next cho mọi PR mở và tự bật auto-merge/merge ghim head; pr reviewed đăng kết quả review lên PR (marker, không tên model) để steward đọc
- Lý do (tiêu chí chất lượng cuối): Không phụ thuộc phiên sống; giữ nguyên luật merge theo làn (review sạch ở đúng head) vì dùng chính pr next; sổ review lên GitHub nên không mất khi container khởi động lại; phương án 2 bỏ qua review làn chuẩn, phương án 3 vẫn mất khi phiên chết
- Đường lùi: xoá workflow pr-steward.yml; pr reviewed --no-publish

### D-055 · 2026-10-19T01:20:43+00:00 · Việc kế tiếp sau 3.4.1 (PROGRESS Tiếp theo 1): làm gì trước?

- Phương án: (1) Guard ghi công AI qua MCP/gh pr (PR title/body, commit qua MCP) + merge-check kiểm tiêu đề PR cục bộ, phát hành 3.5.0 · (2) Task [perf] trong loop (D-041 phương án 3) · (3) Chỉ nâng dự án đích
- Chọn: Guard ghi công AI qua MCP/gh pr (PR title/body, commit qua MCP) + merge-check kiểm tiêu đề PR cục bộ, phát hành 3.5.0
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1: LOOP-HARNESS-027 ghi rõ lỗ commit qua MCP — phiên cloud được hệ thống dặn gắn URL phiên vào thân PR, đúng lỗ đó; tiêu đề PR sai là CI đỏ một vòng. Dự án đích đã ở nhánh 3.4.1; [perf] D-041 đã cân và hoãn
- Đường lùi: Revert PR; matcher hook về như cũ

### D-056 · 2026-10-19T01:20:43+00:00 · Tiêu đề PR sai Conventional Commits/> 72 ký tự: merge-check xử lý thế nào?

- Phương án: (1) verdict fix (chặn merge) kèm lý do — tiêu đề thành subject squash trên nhánh chính · (2) Chỉ ghi chú, không chặn · (3) Chỉ kiểm ở CI repo khung
- Chọn: verdict fix (chặn merge) kèm lý do — tiêu đề thành subject squash trên nhánh chính
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1/3: squash-merge lấy tiêu đề PR làm commit trên main, bỏ qua cổng commit cục bộ; cổng khung đòi conventional commit; sửa tiêu đề rẻ, không cần push
- Đường lùi: Bỏ nhánh title trong merge_decide

### D-057 · 2026-10-19T01:20:44+00:00 · PR body/commit qua MCP có ghi công AI ở repo ai_attribution: forbid: hook chặn thế nào, khi thiếu python/guard lỗi?

- Phương án: (1) Mở rộng matcher pre-mcp-guard sang tool ghi PR/commit; deny khi khớp; tool không phải merge thì fail-open khi guard không chạy · (2) Hook riêng mới
- Chọn: Mở rộng matcher pre-mcp-guard sang tool ghi PR/commit; deny khi khớp; tool không phải merge thì fail-open khi guard không chạy
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 3: một chỗ quyết MCP (mcp_decision), một hook; fail-open về luồng cho tool không nguy hiểm (ADR-0002), fail-closed giữ nguyên cho merge
- Đường lùi: Matcher về mcp__.*(merge_pull_request|auto_merge).*

### D-058 · 2026-10-19T03:51:24+00:00 · Steward ở repo thuộc org: tin MEMBER thế nào; pr_title_check: off đọc ở đâu?

- Phương án: (1) Giữ chỉ OWNER/COLLABORATOR (repo org luôn defer-human) · (2) Tin mọi MEMBER · (3) MEMBER tin khi REST collaborators/<login>/permission trả admin/write; không hỏi được thì không tin. pr_title_check off cần cả nhánh đích lẫn cây làm việc
- Chọn: MEMBER tin khi REST collaborators/<login>/permission trả admin/write; không hỏi được thì không tin. pr_title_check off cần cả nhánh đích lẫn cây làm việc
- Lý do (tiêu chí chất lượng cuối): Đúng và an toàn: MEMBER có thể chỉ có quyền đọc nên không tin mặc định, nhưng hỏi quyền thật thì repo org vẫn dùng được steward; luật nới chỉ hiệu lực khi đã merge vào nhánh đích như merge_autonomy
- Đường lùi: Bỏ nhánh MEMBER trong steward_untrusted/published_reviews và MEMBER khỏi trigger workflow

### D-059 · 2026-10-19T05:04:02+00:00 · vendor-check có quét skill chép vào .claude/skills không, và phân biệt skill của khung/tự viết thế nào?

- Phương án: (1) Không quét; chỉ ghi tài liệu · (2) Quét .claude/skills khi --dirs chỉ định; bỏ qua skill có trong manifest harness của install.py; skill tự viết khai --own · (3) Đòi mọi skill (kể cả của khung) có LICENSE
- Chọn: Quét .claude/skills khi --dirs chỉ định; bỏ qua skill có trong manifest harness của install.py; skill tự viết khai --own
- Lý do (tiêu chí chất lượng cuối): Đúng và an toàn: UX-DS-022 đòi skill chép có SOURCE/LICENSE nhưng trước đây máy không kiểm được; manifest là nguồn sự thật về file khung cài, nên không báo nhầm; skill tự viết khai tường minh
- Đường lùi: Bỏ nhánh SKILLS_DIR/--own trong cmd_vendor_check
- Giới hạn chấp nhận (review #148): manifest là file trong repo nên ai sửa được CI/manifest thì cũng bỏ qua được skill (như `--own`); skill vendor trùng tên skill của khung bị bỏ qua.

### D-060 · 2026-10-19T06:07:33+00:00 · merge-check gặp mergeable_state BLOCKED: phân biệt thiếu check bắt buộc với cần review thế nào?

- Phương án: (1) Giữ: BLOCKED luôn = cần review · (2) Khi BLOCKED, đọc REST rules/branches; check bắt buộc vắng trên head (sau khi mọi check xong) → human với lý do thiếu check; không đọc được → hành vi cũ · (3) Gọi GraphQL mergeStateStatus/required checks
- Chọn: Khi BLOCKED, đọc REST rules/branches; check bắt buộc vắng trên head (sau khi mọi check xong) → human với lý do thiếu check; không đọc được → hành vi cũ
- Lý do (tiêu chí chất lượng cuối): Đúng: X-Company#23 bị báo cần review trong khi ruleset đòi 0 review và chỉ thiếu job dast; REST chạy được ở phiên chặn GraphQL; chỉ gọi thêm khi BLOCKED; fail về hành vi cũ
- Đường lùi: Bỏ _required_checks và nhánh missingRequired
- Giới hạn chấp nhận (review #150): check cùng tên của app khác che được check thiếu (khi đó vẫn báo "cần review"); branch protection cổ điển không có trong `rules/branches` (giữ hành vi cũ); workflow riêng chưa kịp đăng ký check ngay sau push có thể bị báo thiếu một lượt — `pr-steward`/lần chạy sau tự sửa.

### D-061 · 2026-10-19T07:22:23+00:00 · PR tụt sau main (ruleset đòi nhánh cập nhật) bị kẹt tới khi phiên agent cập nhật nhánh và review lại — steward xử lý thế nào?

- Phương án: (1) Giữ: người/phiên agent update-branch, review lại ở head mới · (2) Steward gọi REST update-branch ghim expected_head_sha; review sạch mang sang head mới khi head là merge commit có cha đầu là head đã review và tập thay đổi so với base (tên file, tên cũ, trạng thái, blob sha) không đổi — tối đa 5 bước · (3) Steward update-branch và bỏ yêu cầu review lại cho mọi merge base
- Chọn: Steward gọi REST update-branch ghim expected_head_sha; review sạch mang sang head mới khi head là merge commit có cha đầu là head đã review và tập thay đổi so với base (tên file, tên cũ, trạng thái, blob sha) không đổi — tối đa 5 bước
- Lý do (tiêu chí chất lượng cuối): Đúng: merge base sạch không đổi nội dung PR (so blob sha từng file qua REST compare) nên review cũ vẫn phủ đúng mã; merge có xung đột hoặc đổi file nào thì tập thay đổi khác → review lại; ghim expected_head_sha tránh ghi đè push mới; hôm nay kẹt 4 lần (X-Company#23 ×2, hotel-manager#87, X-Templates#151)
- Đường lùi: Bỏ baseMergeOf trong _pr_rest và nhánh update trong _steward_command/_steward_one
- Bổ sung (review #153): không mang review khi nhánh đích, kể từ merge-base với head đã review, chạm file nào của PR (merge "giữ bản của mình" giữ blob phía PR nhưng gỡ thay đổi của nhánh đích); steward chạy bằng GITHUB_TOKEN (`XT_STEWARD_UPDATE=off`) không cập nhật nhánh vì commit đó không kích CI. Giới hạn chấp nhận: so blob không thấy đổi quyền file (`chmod`) trong merge commit.

### D-062 · 2026-10-19T08:52:23+00:00 · pr-steward bật auto-merge khi nhánh đích không có check bắt buộc thì GitHub merge ngay lúc bật (trước khi CI chạy xong) — chốt ở đâu?

- Phương án: (1) Chốt trong workflow như hotel-manager T-1107: đếm required check bằng gh api, không có thì bỏ --apply · (2) Chốt trong xt.py pr steward: nhánh đích không có check bắt buộc (ruleset hoặc branch protection cổ điển) thì bỏ lệnh bật auto-merge, vẫn tắt auto-merge/merge ghim head khi merge-check đã thấy CI xanh
- Chọn: Chốt trong xt.py pr steward: nhánh đích không có check bắt buộc (ruleset hoặc branch protection cổ điển) thì bỏ lệnh bật auto-merge, vẫn tắt auto-merge/merge ghim head khi merge-check đã thấy CI xanh
- Lý do (tiêu chí chất lượng cuối): Đúng và an toàn: chỉ chặn đúng lệnh nguy hiểm (auto-merge không chờ CI), giữ hành động an toàn (tắt auto-merge, merge ghim head sau khi CI xanh); test được bằng unittest thay vì bash trong YAML; mọi dự án đích nhận qua install.py không phải sửa workflow; đọc cả branch protection cổ điển; không đọc được → coi như không có (chiều chặt)
- Đường lùi: Bỏ _base_has_required và nhánh lọc --auto trong _steward_one

### D-063 · 2026-10-19T09:17:56+00:00 · PR đủ điều kiện (merge-check = merge) mà auto-merge đã bật nhưng GitHub chưa merge, hoặc nhánh đích không có check bắt buộc — pr next/steward làm gì?

- Phương án: (1) Giữ: auto-merge bật thì chờ GitHub; phiên agent vẫn được bảo bật auto-merge · (2) Đủ điều kiện là merge ghim head ngay (kể cả khi auto-merge đang bật); nhánh đích không có check bắt buộc thì pr next không bao giờ trả enable-auto-merge mà chờ CI xanh rồi merge ghim head — chốt ở pr_next cho cả phiên agent lẫn steward
- Chọn: Đủ điều kiện là merge ghim head ngay (kể cả khi auto-merge đang bật); nhánh đích không có check bắt buộc thì pr next không bao giờ trả enable-auto-merge mà chờ CI xanh rồi merge ghim head — chốt ở pr_next cho cả phiên agent lẫn steward
- Lý do (tiêu chí chất lượng cuối): Chủ repo yêu cầu đủ điều kiện là luôn được merge (X-Templates#155 treo ở trạng thái clean, phải merge tay); merge ghim head chỉ khi merge-check thấy mọi check xanh và GitHub báo sạch nên không mở rủi ro mới; một chỗ chốt trong pr_next thay cho bộ lọc riêng của steward (D-062), phiên agent cũng được che
- Đường lùi: Bỏ nhánh verdict merge khi auto_merge và nhánh base_has_required trong _pr_next_final; trả lại bộ lọc --auto ở _steward_one

### D-064 · 2026-10-19T11:13:18+00:00 · Duyệt kế hoạch sửa audit 2026-10-19 (5 đợt, T-1401…T-1417, bản 3.8.0)

- Phương án: (1) Sửa mọi 🔴/🟠 + 🟢 cùng file khi rẻ, mỗi lát một PR, phát hành 3.8.0 · (2) Chỉ sửa 2 🔴 (đợt 1), phần còn lại để sau · (3) Gộp mọi đợt vào một PR
- Chọn: Sửa mọi 🔴/🟠 + 🟢 cùng file khi rẻ, mỗi lát một PR, phát hành 3.8.0
- Lý do (tiêu chí chất lượng cuối): Chủ repo gọi /autopilot ngay sau /audit dừng chờ duyệt kế hoạch 5 đợt; đúng và an toàn: 🔴/🟠 là hàng rào hứa chặn mà lọt và cổng máy xanh giả — để lại là nợ an toàn; mỗi lát một PR giữ đường lùi (revert từng lát) và review khác model theo làn
- Đường lùi: Dừng sau lát bất kỳ; revert PR của lát; phát hiện còn lại giữ 'mở' trong AUDIT-STATUS

### D-065 · 2026-10-19T11:13:18+00:00 · Phiên bị ràng buộc một tên nhánh (seeker/beautiful-turing-hv6jb9) trong khi AGENTS.md đòi mỗi lát một PR, nhánh riêng

- Phương án: (1) Tuần tự: mỗi lát một PR trên cùng tên nhánh; lát sau chuẩn bị ở nhánh cục bộ, PR trước merge thì đặt lại nhánh từ main · (2) Đẩy nhiều nhánh <type>/<mô-tả> song song · (3) Mọi lát một PR
- Chọn: Tuần tự: mỗi lát một PR trên cùng tên nhánh; lát sau chuẩn bị ở nhánh cục bộ, PR trước merge thì đặt lại nhánh từ main
- Lý do (tiêu chí chất lượng cuối): Giữ cả hai luật: ràng buộc nhánh của phiên (không push nhánh khác khi chưa được phép) và một lát một PR (review/đường lùi riêng); chi phí chỉ là chờ CI/review giữa các lát
- Đường lùi: Chủ repo cho phép nhánh khác → tách lát còn lại sang nhánh <type>/<mô-tả> riêng

### D-066 · 2026-10-19T12:05:59+00:00 · Bản nâng cấp kế hoạch #160 đi đâu khi phiên bị ràng buộc nhánh seeker/stoic-edison-i2llue?

- Phương án: (1) Push lên nhánh docs/remediation-plan-2026-10-19 của #160 · (2) PR mới trên nhánh phiên (gộp commit #160), thay #160; #160 giữ làm lịch sử nháp · (3) Chỉ comment góp ý vào #160
- Chọn: PR mới trên nhánh phiên (gộp commit #160), thay #160; #160 giữ làm lịch sử nháp
- Lý do (tiêu chí chất lượng cuối): Ràng buộc nhánh của phiên (không push nhánh khác khi chưa được phép) và một lát một PR; #160 là nháp nên không mất gì
- Đường lùi: Đóng PR mới, mở lại #160 và chép nội dung sang

### D-067 · 2026-10-19T12:05:59+00:00 · Kế hoạch triển khai máy đọc được đặt ở đâu khi PLAN.md đang được vòng 3.8.0 (#159…) dùng?

- Phương án: (1) Chèn T-14xx mới vào docs/autopilot/PLAN.md hiện hành · (2) File riêng docs/autopilot/PLAN-3.9-automation.md, chạy loop init --plan sau khi 3.8.0 xong · (3) Chỉ mô tả trong REMEDIATION-PLAN, không có task máy đọc
- Chọn: File riêng docs/autopilot/PLAN-3.9-automation.md, chạy loop init --plan sau khi 3.8.0 xong
- Lý do (tiêu chí chất lượng cuối): Không làm lệch verdict/ngân sách vòng đang chạy (loop status đọc PLAN.md); vẫn parse_plan được và duyệt một lần (ADR-0008); tách PR nhỏ, đảo ngược được
- Đường lùi: Chép task sang PLAN.md khi 3.8.0 phát hành

### D-068 · 2026-10-19T12:05:59+00:00 · Cổng bằng chứng ở tầng Claude Code cho task/subagent dùng cơ chế nào?

- Phương án: (1) Giữ chỉ Stop + PreToolUse hiện có · (2) Thêm command hook TaskCompleted, SubagentStop, PermissionRequest đọc .autopilot/ (docs hooks xác minh 2026-10-19); hook prompt/agent LLM chỉ bổ trợ · (3) Dùng hook agent (LLM) làm cổng chính
- Chọn: Thêm command hook TaskCompleted, SubagentStop, PermissionRequest đọc .autopilot/ (docs hooks xác minh 2026-10-19); hook prompt/agent LLM chỉ bổ trợ
- Lý do (tiêu chí chất lượng cuối): Cổng máy tất định, test bằng payload giả như tests/test_hooks.py; LLM-judge là lời khai (P1, LOOP-DESIGN-004); PermissionRequest ở headless không có quyết định = deny nên là nhà đúng của typed decision (REC-04)
- Đường lùi: Gỡ ba hook khỏi settings.json, giữ Stop hook

### D-069 · 2026-10-19T12:05:59+00:00 · Review độc lập tự động (AUTO-03) dựa vào gì?

- Phương án: (1) Sản phẩm Claude Code Review của Anthropic (Team/Enterprise; check run không bao giờ fail) · (2) Reviewer tự dựng: workflow riêng chạy claude -p --json-schema bằng danh tính GitHub riêng, đăng pr reviewed; model khác tác giả · (3) Giữ reviewer subagent trong phiên tác giả
- Chọn: Reviewer tự dựng: workflow riêng chạy claude -p --json-schema bằng danh tính GitHub riêng, đăng pr reviewed; model khác tác giả
- Lý do (tiêu chí chất lượng cuối): Cần danh tính tách quyền ghi và kết quả có schema để làm required gate; Code Review không fail nên không làm cổng được và chỉ có ở Team/Enterprise; subagent trong phiên tác giả chung vùng quyền ghi (REC-03)
- Đường lùi: Tắt workflow reviewer, quay về reviewer subagent + pr reviewed tay

### D-070 · 2026-10-19T12:06:00+00:00 · Bộ điều phối task (AUTO-01) viết bằng gì?

- Phương án: (1) Agent SDK Python (thêm phụ thuộc) · (2) Python stdlib trong xt.py (loop next/dispatch) gọi claude -p --output-format json như subprocess · (3) Orchestrator riêng ngoài repo
- Chọn: Python stdlib trong xt.py (loop next/dispatch) gọi claude -p --output-format json như subprocess
- Lý do (tiêu chí chất lượng cuối): AGENTS §7: xt.py chỉ stdlib ≥ 3.11, CI 3.11/3.13; claude -p là đường tài liệu hỗ trợ cho ngôn ngữ khác; đơn giản, test được bằng subprocess giả
- Đường lùi: Thêm Agent SDK khi cần callback canUseTool hoặc stream

### D-071 · 2026-10-19T12:26:11+00:00 · Lát C (merge), D (cổng máy), E (tài liệu + sổ audit) đã commit và qua cổng ở nhánh cục bộ trong lúc chờ #159 — mở 3 PR tuần tự hay một PR

- Phương án: (1) Ba PR tuần tự trên cùng tên nhánh (D-065) · (2) Một PR gộp C+D+E, commit tách theo lát
- Chọn: Một PR gộp C+D+E, commit tách theo lát
- Lý do (tiêu chí chất lượng cuối): Đúng và an toàn như nhau (mỗi lát một commit có test đỏ trước, cổng xanh trên cây gộp, reviewer khác model rà cả diff); ràng buộc một tên nhánh buộc ba PR chờ nối tiếp nhau (mỗi vòng CI + review), gộp giữ đường lùi bằng revert từng commit
- Đường lùi: Revert commit của lát cần bỏ; hoặc tách lại PR theo commit

### D-072 · 2026-10-19T13:19:28+00:00 · Review #162 (reviewer khác model) báo 2 lỗi chặn (vendor-check lọt mã C/C++, perf guard bỏ sót .gitignore tự che trong thư mục mới) nhưng phiên này bị ràng buộc nhánh seeker/sleepy-dijkstra-wnl2b5, không push được nhánh của #162 — sửa ở đâu?

- Phương án: (1) Push sửa lên nhánh của #162 (vi phạm ràng buộc nhánh phiên) · (2) Ghi pr reviewed --blocking cho #162; mở PR mới trên nhánh phiên = #162 + commit sửa, thay #162 (như D-066 với #160); đóng #162 · (3) Chờ chủ repo cho phép push nhánh #162
- Chọn: Ghi pr reviewed --blocking cho #162; mở PR mới trên nhánh phiên = #162 + commit sửa, thay #162 (như D-066 với #160); đóng #162
- Lý do (tiêu chí chất lượng cuối): Giữ ràng buộc nhánh của phiên và một lát một PR; PR mới mang nguyên commit của #162 nên review tăng trưởng chỉ cần rà commit sửa; không chờ người (ADR-0008)
- Đường lùi: Đóng PR mới, mở lại #162 và chép commit sửa sang nhánh của #162 khi được phép

### D-073 · 2026-10-19T15:03:20+00:00 · Duyệt PLAN-3.9-automation (T-1501…T-1522, 3.9.0 → 3.10.0) sau khi 3.8.0 phát hành: chạy loop init như thế nào?

- Phương án: (1) Duyệt nguyên văn, chạy ngay · (2) Duyệt sau khi siết Gate theo review khác model (tách -k theo ý, sau: tuần tự cho task cùng sửa xt.py, trần headless cho T-1508), rồi loop init --single-session --max-iterations 176 --hours 24 · (3) Hoãn tới khi sửa xong 🔴 AUD-SEC-072 của audit
- Chọn: Duyệt sau khi siết Gate theo review khác model (tách -k theo ý, sau: tuần tự cho task cùng sửa xt.py, trần headless cho T-1508), rồi loop init --single-session --max-iterations 176 --hours 24
- Lý do (tiêu chí chất lượng cuối): Reviewer Sonnet (LOOP-ORCH-018) tìm 4 Gate chỉ chứng minh test tồn tại hoặc thiếu ý của task; siết rẻ và đúng (1) đúng và an toàn; PLAN-3.9 độc lập về file với sửa guard nên không phải chờ — sửa guard đợi người duyệt kế hoạch audit riêng
- Đường lùi: loop stop; loop init lại với PLAN cũ (git revert commit siết Gate)

### D-074 · 2026-10-19T15:03:20+00:00 · T-1501 và T-1502 (cùng sửa scripts/xt.py phần evidence, đã xong cục bộ) — một PR hay hai?

- Phương án: (1) Hai PR tuần tự trên cùng tên nhánh (D-065) · (2) Một PR gộp, hai commit theo task
- Chọn: Một PR gộp, hai commit theo task
- Lý do (tiêu chí chất lượng cuối): Hai task cùng hàm run_gate_shell/loop_record, review một lần rẻ hơn; commit tách theo task giữ đường lùi; ràng buộc một tên nhánh buộc hai vòng CI + review nối tiếp (như D-071)
- Đường lùi: Revert commit của task cần bỏ

### D-075 · 2026-10-19T17:23:30+00:00 · Tầng executor ghi trong PLAN/artefact commit bằng gì

- Phương án: (1) Tên model (sonnet/opus) trong dòng task · (2) Tên tầng (exec: deep), model thật chỉ trong frontmatter .claude/agents/*.md
- Chọn: Tên tầng (exec: deep), model thật chỉ trong frontmatter .claude/agents/*.md
- Lý do (tiêu chí chất lượng cuối): AGENTS.md §3/LOOP-HARNESS-027 cấm tên model trong artefact đẩy lên repo; một nguồn sự thật cho model (P5); đổi model chỉ sửa agent file
- Đường lùi: Bỏ EXEC_TIER_RE, xoá executor-deep.md — về một tầng như trước

### D-076 · 2026-10-19T17:23:31+00:00 · Reviewer cho diff của executor-deep (opus) khi reviewer.md ghim opus

- Phương án: (1) Một reviewer, bỏ luật khác họ cho tầng sâu · (2) Thêm reviewer-alt (sonnet), phiên chính chọn reviewer khác họ với agent đã viết · (3) Phiên chính tự review
- Chọn: Thêm reviewer-alt (sonnet), phiên chính chọn reviewer khác họ với agent đã viết
- Lý do (tiêu chí chất lượng cuối): Giữ D-045/LOOP-ORCH-005 (người chấm khác họ người viết) — (1) đúng và an toàn; agent file rẻ, test được; phiên chính tự review mất tính độc lập
- Đường lùi: Xoá reviewer-alt.md, dùng XT_REVIEWER_MODEL

### D-077 · 2026-10-19T17:23:31+00:00 · Chuyển cấp Sonnet→Opus là luật mới hay dạng của LOOP-ORCH-014

- Phương án: (1) Luật mới với ngưỡng riêng, đếm riêng · (2) Một dạng đổi cách của LOOP-ORCH-014: đỏ 2 lần → tầng sâu; max_same_failure 3 giữ nguyên
- Chọn: Một dạng đổi cách của LOOP-ORCH-014: đỏ 2 lần → tầng sâu; max_same_failure 3 giữ nguyên
- Lý do (tiêu chí chất lượng cuối): Không nhân đôi bộ đếm; nguyên tắc 'lần 2 đổi cách, lần 3 hỏi người' đã có máy kiểm; ngưỡng 2 là tham số khởi đầu đo bằng loop stats
- Đường lùi: Đặt ESCALATE_AFTER rất lớn (tắt chuyển cấp tự động)

### D-078 · 2026-10-19T17:23:31+00:00 · Cổng G7 máy đọc: lệnh mới hay mở rộng blueprint-status

- Phương án: (1) Thêm cờ vào blueprint-status · (2) Lệnh release-check gom blueprint + audit + kiểm lại cuối + cây git + đề xuất Khi chạy thật
- Chọn: Lệnh release-check gom blueprint + audit + kiểm lại cuối + cây git + đề xuất Khi chạy thật
- Lý do (tiêu chí chất lượng cuối): blueprint-status một việc một nhà; GO-NO-GO cần nhiều nguồn và bảng N/A chờ người; JSON và Markdown cùng nguồn (PD-08)
- Đường lùi: Xoá cmd_release_check; GO-NO-GO điền tay như trước

### D-079 · 2026-10-19T18:08:50+00:00 · Cổng commit của repo khung mất ~190 s (test 97 %) — rút thời gian bằng cách nào

- Phương án: (1) Hook commit chỉ chạy test liên quan file đổi, CI chạy trọn (BASE-GATE cho phép) · (2) Giữ trọn bộ test + coverage 100 % nhưng chạy mỗi lớp test một tiến trình song song theo số CPU (coverage parallel=True đã có) · (3) Chấp nhận 190 s
- Chọn: Giữ trọn bộ test + coverage 100 % nhưng chạy mỗi lớp test một tiến trình song song theo số CPU (coverage parallel=True đã có)
- Lý do (tiêu chí chất lượng cuối): (1) đúng và an toàn: không bỏ kiểm nào ở hook, cùng ngưỡng; đo 180 s → 66 s trên 4 CPU; CI cũng nhanh theo; phương án test liên quan cần bản đồ file→test và có thể lọt lỗi chéo
- Đường lùi: Trả dòng test: trong xt.yaml về discover tuần tự

### D-080 · 2026-10-19T18:24:22+00:00 · merge_risk_paths của repo khung có giữ tài liệu thuần không

- Phương án: (1) Giữ như D-031 (ADR, 11-autonomous-loop, code-review.md vào làn chuẩn) · (2) Bỏ tài liệu thuần, giữ scripts/* và framework/templates/*
- Chọn: Bỏ tài liệu thuần, giữ scripts/* và framework/templates/*
- Lý do (tiêu chí chất lượng cuối): Chủ repo yêu cầu 2026-10-19 (giảm vòng review cho PR docs); lớp đỡ còn validate, check-links, revert; templates giữ vì thành file thật ở dự án đích
- Đường lùi: Đặt lại chuỗi D-031 trong xt.yaml

### D-081 · 2026-10-19T22:57:52+00:00 · Duyệt PLAN-3.9-automation (T-1509…T-1522)

- Phương án: (1) Chạy theo PLAN đã lập, review khác model đã rà Gate · (2) Hoãn, chờ chủ repo duyệt rescan audit trước
- Chọn: Chạy theo PLAN đã lập, review khác model đã rà Gate
- Lý do (tiêu chí chất lượng cuối): PLAN đã có D-066…D-070; không chặn bởi audit rescan (độc lập); tiêu chí 1: Gate đã siết
- Đường lùi: loop block + revert PR từng lát

### D-082 · 2026-10-19T23:05:41+00:00 · PermissionRequest hook: guard không phản đối thì trả allow hay im lặng?

- Phương án: (1) A: im lặng (headless tự deny, tương tác hiện hộp thoại) · (2) B: trả allow cho mọi thứ guard không chặn
- Chọn: A: im lặng (headless tự deny, tương tác hiện hộp thoại)
- Lý do (tiêu chí chất lượng cuối): tiêu chí 1: chiều chặt, đúng REC-04 'không quyết định ⇒ deny'; B mở rộng tự duyệt ngoài permissions.allow và cần ADR
- Đường lùi: đổi nhánh in allow trong guard.py permission + ADR

### D-083 · 2026-10-19T23:08:39+00:00 · Audit delta ở mốc 3.9.0: làm ngay hay gộp vào mốc 3.10.0?

- Phương án: (1) Audit delta đủ 13 nhóm ngay · (2) Gộp vào mốc 3.10.0; bây giờ chỉ review khác họ model diff T-1509 (phần guard)
- Chọn: Gộp vào mốc 3.10.0; bây giờ chỉ review khác họ model diff T-1509 (phần guard)
- Lý do (tiêu chí chất lượng cuối): sổ rescan tại a4f929c còn chờ duyệt và đã phủ phần lớn; diff mốc nhỏ (T-1501…1509 đã qua Gate + coverage 100%); rủi ro cao nhất là guard nên review riêng
- Đường lùi: chạy audit plan/check đủ nhóm trước T-1511

### D-084 · 2026-10-19T23:30:13+00:00 · final_check/release-check có đòi lần verify cuối là mode=all?

- Phương án: (1) a: nhận cả verify một phần · (2) b: đòi mode=all trước done (giữ LOOP-DESIGN-022), một phần chỉ giữa vòng
- Chọn: b: đòi mode=all trước done (giữ LOOP-DESIGN-022), một phần chỉ giữa vòng
- Lý do (tiêu chí chất lượng cuối): tiêu chí 1: files: khai thiếu làm lọt hồi quy; làm trong T-1514 (đụng Stop hook) + sửa tài liệu loop-design/README/SKILL
- Đường lùi: bỏ đòi mode trong final_check

### D-085 · 2026-10-19T23:31:24+00:00 · install.py: đường nâng cấp một lần cho ask cũ chưa có manifest?

- Phương án: (1) giữ và báo ask_unproven, không suy diễn · (2) thêm cờ adopt-legacy-ask
- Chọn: giữ và báo ask_unproven, không suy diễn
- Lý do (tiêu chí chất lượng cuối): REC-09 cấm suy diễn nguồn gốc; ghi CHANGELOG; thêm cờ khi có dự án đích cần
- Đường lùi: thêm cờ adopt-legacy-ask sau

### D-086 · 2026-10-19T23:41:06+00:00 · T-1514: ID ngoài PLAN trong subject; SubagentStop chặn mấy lần; có đòi lệnh kèm exit code?

- Phương án: (1) ID ngoài PLAN vẫn đòi evidence; SubagentStop chặn một lần rồi cho dừng; chỉ đòi mẫu exit code · (2) bỏ qua ID ngoài PLAN; chặn mọi lần; đòi cả lệnh
- Chọn: ID ngoài PLAN vẫn đòi evidence; SubagentStop chặn một lần rồi cho dừng; chỉ đòi mẫu exit code
- Lý do (tiêu chí chất lượng cuối): tiêu chí 1 với evidence, tránh kẹt vòng subagent và chặn oan (phiên chính vẫn kiểm bằng loop record)
- Đường lùi: đổi trong hook task-completed/subagent-stop

### D-087 · 2026-10-19T23:47:36+00:00 · episode ci-triage: reset ở đâu?

- Phương án: (1) giữ nguyên: resume không đụng, init --force xoá · (2) loop init mang episode vòng cũ sang · (3) resume xoá episode
- Chọn: giữ nguyên: resume không đụng, init --force xoá
- Lý do (tiêu chí chất lượng cuối): T-1515 đúng spec; lỗ init --force đổi ngân sách ghi vào PROGRESS để xử ở task sau, không mở rộng phạm vi
- Đường lùi: thêm mang episode trong loop init

### D-088 · 2026-10-20T00:08:58+00:00 · T-1517: concurrency steward và sự kiện không gắn PR

- Phương án: (1) concurrency theo PR; sự kiện không gắn PR quét mọi PR mở · (2) một nhóm chung; bỏ qua sự kiện không gắn PR
- Chọn: concurrency theo PR; sự kiện không gắn PR quét mọi PR mở
- Lý do (tiêu chí chất lượng cuối): bước đọc lại trước khi làm đỡ race; push main cần update PR tụt base (tiêu chí 1)
- Đường lùi: đổi group về pr-steward

### D-089 · 2026-10-20T00:15:07+00:00 · doctor --drift: lệch modified có làm exit đỏ? so ask?

- Phương án: (1) modified không đỏ; chỉ so allow/deny; hook mới ở mức warn · (2) mọi lệch đều đỏ, so cả ask
- Chọn: modified không đỏ; chỉ so allow/deny; hook mới ở mức warn
- Lý do (tiêu chí chất lượng cuối): modified là tuỳ chỉnh hợp lệ; ADR-0018 gỡ ask có chủ đích; tránh đỏ oan ở dự án cài bản cũ
- Đường lùi: đổi một dòng trong drift_report
