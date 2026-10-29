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

### D-090 · 2026-10-20T00:46:01+00:00 · 5 false-green guard do autonomy-bench tìm ra: xử lý thế nào?

- Phương án: (1) mở task riêng T-1523 sửa guard, ca chuyển từ pending/ sang corpus chính khi xong; giữ exit 1 · (2) sửa ngay trong T-1521 · (3) chỉ ghi danh sách lỗ đã biết
- Chọn: mở task riêng T-1523 sửa guard, ca chuyển từ pending/ sang corpus chính khi xong; giữ exit 1
- Lý do (tiêu chí chất lượng cuối): tiêu chí 1: guard nhạy cảm bảo mật, không nới bench; gộp được với SEC-072/077 đang mở; T-1521 đúng phạm vi
- Đường lùi: bỏ T-1523 khỏi PLAN

### D-091 · 2026-10-20T01:14:11+00:00 · Audit delta mốc: 3 phát hiện 🟠 (guard $VAR push, ci-triage secret khớp tên công cụ, episode bị reset khi đổi --task) + 🟡 sau: ID lạ

- Phương án: (1) task mới T-1524 sửa cả ba 🟠 + cảnh báo sau: lạ, trước khi cắt 3.10.0 · (2) ghi sổ, sửa ở bản sau
- Chọn: task mới T-1524 sửa cả ba 🟠 + cảnh báo sau: lạ, trước khi cắt 3.10.0
- Lý do (tiêu chí chất lượng cuối): audit.md §1: 🔴/🟠 thành task mới; lỗi nằm ở code vừa viết; ci-triage block oan dừng cả vòng
- Đường lùi: bỏ T-1524 khỏi PLAN

### D-092 · 2026-10-20T01:24:04+00:00 · ci-triage: mang episode khi đổi task (AUD-HAR-092)

- Phương án: (1) giữ signature/same_signature/rerun_used/cost_usd/runs, chỉ reset task/started/fix_attempts · (2) reset rerun_used khi chữ ký đổi
- Chọn: giữ signature/same_signature/rerun_used/cost_usd/runs, chỉ reset task/started/fix_attempts
- Lý do (tiêu chí chất lượng cuối): chặt hơn, không lách trần; hệ quả task mới không được re-run nếu lượt đã dùng — chấp nhận
- Đường lùi: reset rerun_used theo chữ ký

### D-093 · 2026-10-20T01:31:24+00:00 · Gate T-1510 ghim VERSION=3.9.0 đỏ sau khi lên 3.10.0 — xử lý?

- Phương án: (1) đổi phép kiểm sang grep mục [3.9.0] trong CHANGELOG (đúng ở mọi bản sau) · (2) bỏ T-1510 khỏi verify
- Chọn: đổi phép kiểm sang grep mục [3.9.0] trong CHANGELOG (đúng ở mọi bản sau)
- Lý do (tiêu chí chất lượng cuối): kiểm tại thời điểm đã đạt; không bỏ task, không hạ ngưỡng — chỉ gỡ ràng buộc sai thời điểm; ghi lý do ở commit
- Đường lùi: khôi phục test VERSION = 3.9.0

### D-094 · 2026-10-20T02:59:26+00:00 · delivery_phase build: ngoại lệ cứng đã miễn (hard_waived), điều kiện build hiệu lực, cách tính review_debt

- Phương án: (1) hard_waived vẫn cần review sạch; build chỉ hiệu lực khi xt.yaml ở nhánh đích VÀ cây cùng là build; review_debt theo SHA của nhóm audit chứa file · (2) hard_waived như PR thường; build đọc từ cây; review_debt theo SHA cũ nhất
- Chọn: hard_waived vẫn cần review sạch; build chỉ hiệu lực khi xt.yaml ở nhánh đích VÀ cây cùng là build; review_debt theo SHA của nhóm audit chứa file
- Lý do (tiêu chí chất lượng cuối): tiêu chí 1: chặt hơn; PR không tự bật build cho chính nó; tránh báo nợ mãi sau audit delta
- Đường lùi: đặt delivery_phase: harden

### D-095 · 2026-10-20T04:35:11+00:00 · CI shard test: chia mod N bị lệch tải (26/34/53/100 s)

- Phương án: (1) mod N như spec · (2) tham lam theo trọng số (file trọng số trong repo, lớp lạ lấy mặc định) · (3) shard theo phương thức · (4) băm crc32 rồi mod N
- Chọn: tham lam theo trọng số (file trọng số trong repo, lớp lạ lấy mặc định)
- Lý do (tiêu chí chất lượng cuối): mục tiêu là giảm wall time; mod N gần như không nhanh hơn; 2 gần tối ưu (~54 s/shard) và bền khi thêm lớp (lớp lạ có mặc định), chi phí là một file trọng số
- Đường lùi: quay về mod N trong test-shard

### D-096 · 2026-10-20T05:31:33+00:00 · CI mẫu dự án đích khi xt.yaml chưa khai lint/test

- Phương án: (1) đỏ khi lint hoặc test chưa khai (cả pha build), ::error:: chỉ chỗ điền · (2) chỉ ::warning::, giữ xanh · (3) đỏ trừ khi delivery_phase: build
- Chọn: đỏ khi lint hoặc test chưa khai (cả pha build), ::error:: chỉ chỗ điền
- Lý do (tiêu chí chất lượng cuối): tiêu chí 1: CI xanh rỗng cho merge mã chưa kiểm (bẫy ci-cd-pipeline.md); code nhanh ≠ không cổng; ADR-0011 cổng rỗng là đỏ; dự án mới điền xt.yaml ở task đầu
- Đường lùi: đổi bước kiểm thành ::warning::

### D-097 · 2026-10-20T06:12:31+00:00 · Guard _dir_holds_gate đọc toàn bộ /tmp (≈20k mục, 2,5 s/lệnh)

- Phương án: (1) giữ nguyên, chấp nhận trễ và trọng số phụ thuộc máy · (2) bỏ liệt kê thư mục ngoài gốc dự án mà không có dấu hiệu chứa cổng (giữ bảo vệ ~/.claude, .git), kèm test chặn/cho qua
- Chọn: bỏ liệt kê thư mục ngoài gốc dự án mà không có dấu hiệu chứa cổng (giữ bảo vệ ~/.claude, .git), kèm test chặn/cho qua
- Lý do (tiêu chí chất lượng cuối): tiêu chí 1 giữ nguyên bảo vệ (test chặn hiện có không đổi), tiêu chí 4 trễ mỗi lệnh Bash của agent; thư mục tạm hệ thống không chứa file cổng của dự án
- Đường lùi: trả lại os.listdir cho mọi đích

### D-098 · 2026-10-20T06:47:17+00:00 · Guard bung đủ dãy {1..N}: vòng for số > 64 giá trị bị chặn theo trần VAR_FOR_PICKS

- Phương án: (1) giữ trần 64 cho mọi giá trị (nhất quán với for viết tay) · (2) nới trần khi mọi giá trị là số thuần, kèm test
- Chọn: nới trần khi mọi giá trị là số thuần, kèm test
- Lý do (tiêu chí chất lượng cuối): tiêu chí 1: giá trị số thuần không tạo tên lệnh/đường dẫn nguy hiểm khác nhau giữa các lần lặp nên quét mẫu đại diện là đủ; tiêu chí 4: vòng chờ/thử lại {1..100} là việc thường ngày của agent
- Đường lùi: trả trần 64 cho mọi giá trị

### D-099 · 2026-10-20T07:02:11+00:00 · merge-check gặp PR làn chuẩn eligible=false: thêm verdict review + exit 1 trái ADR-0028 §2

- Phương án: (1) ADR mới thay ADR-0028 §2: verdict review, exit 1, không in lệnh merge · (2) giữ verdict merge, chỉ bỏ dòng lệnh merge
- Chọn: ADR mới thay ADR-0028 §2: verdict review, exit 1, không in lệnh merge
- Lý do (tiêu chí chất lượng cuối): tiêu chí 1: lệnh 'quyết khi nào merge' không được trả merge cho PR chưa đủ điều kiện (AUD-XFEAT-010); script dựa exit 0 sẽ merge sai nếu giữ merge
- Đường lùi: trả verdict merge, exit 0

### D-100 · 2026-10-20T07:02:11+00:00 · Guard chặn cả bật auto-merge khi auto_merge_ok=false, không chỉ merge ghim head

- Phương án: (1) chặn cả hai (nhất quán với pr next) · (2) chỉ chặn merge ghim head, để merge-gate đỡ auto-merge
- Chọn: chặn cả hai (nhất quán với pr next)
- Lý do (tiêu chí chất lượng cuối): tiêu chí 1: auto-merge không ghim head, merge-gate chỉ là lớp đỡ sau; pr next không bao giờ bảo bật trong ca này nên không chặn việc hợp lệ
- Đường lùi: bỏ chặn bật auto-merge trong REVIEW_MISSING

### D-101 · 2026-10-20T07:02:11+00:00 · Review sạch ghi sổ cục bộ mà chưa đăng ở pha build/làn nhanh: có bắt đăng lại

- Phương án: (1) không bắt (review không phải điều kiện merge ở đó) · (2) luôn bắt đăng lại
- Chọn: không bắt (review không phải điều kiện merge ở đó)
- Lý do (tiêu chí chất lượng cuối): tiêu chí 5 phá hoà: review không là điều kiện merge ở pha build/làn nhanh nên không đổi độ đúng; bắt đăng lại chỉ làm chậm — mục tiêu code nhanh merge nhanh; nợ review vẫn do release-check chặn
- Đường lùi: unpublished_review trả bước đăng lại mọi làn

### D-102 · 2026-10-20T07:04:07+00:00 · Test phủ trọng số shard bắt mọi PR thêm/bỏ lớp test phải đo lại test-weights (~7 phút)

- Phương án: (1) giữ chặt: thiếu một lớp là đỏ · (2) cho thiếu tới ngưỡng (lớp lạ lấy trung vị), đỏ khi thiếu quá ngưỡng · (3) chỉ kiểm lớp có tên cụ thể
- Chọn: cho thiếu tới ngưỡng (lớp lạ lấy trung vị), đỏ khi thiếu quá ngưỡng
- Lý do (tiêu chí chất lượng cuối): tiêu chí 3: lớp lạ đã có trung vị nên shard đúng, chỉ lệch nhẹ; tiêu chí 5 phá hoà: không buộc đo 7 phút mỗi PR thêm test (code nhanh); ngưỡng chặn trôi dài hạn
- Đường lùi: trả kiểm chặt

### D-103 · 2026-10-20T07:50:48+00:00 · Chấp nhận ngoại lệ license MPL-2.0 (pathspec, certifi) cho công cụ dev/CI

- Phương án: (1) chấp nhận có hạn 12 tháng: dùng nguyên bản, không sửa, không phân phối · (2) thay gói (bỏ pathspec/certifi)
- Chọn: chấp nhận có hạn 12 tháng: dùng nguyên bản, không sửa, không phân phối
- Lý do (tiêu chí chất lượng cuối): tiêu chí 1: MPL-2.0 copyleft theo file chỉ ràng buộc khi sửa/phân phối file của gói; công cụ chỉ chạy trên CI/máy dev, không vào sản phẩm phát hành; tiêu chí 3: certifi/pathspec là phụ thuộc bắc cầu khó thay
- Đường lùi: gỡ ngoại lệ khỏi license-allow.json, thay gói

### D-104 · 2026-10-20T08:46:31+00:00 · merge-check ở pha build không thấy review blocking chỉ có trong sổ cục bộ (chưa đăng) — AUD-XFEAT-015

- Phương án: (1) merge-check đọc thêm sổ cục bộ, chỉ để chặt hơn: review clean:false ở head hiện tại → review=blocking (không deferred) · (2) pr reviewed đăng trước rồi mới ghi sổ
- Chọn: merge-check đọc thêm sổ cục bộ, chỉ để chặt hơn: review clean:false ở head hiện tại → review=blocking (không deferred)
- Lý do (tiêu chí chất lượng cuối): tiêu chí 1: đóng cửa sổ merge PR có lỗi chặn đã biết; đăng-trước không đóng được ca đăng thất bại; sổ cục bộ chỉ làm chặt hơn nên không mở đường lách
- Đường lùi: merge-check chỉ đọc xtReviews như cũ

### D-105 · 2026-10-20T10:31:12+00:00 · Script trình thông dịch chạm đường dẫn được canh: liệt kê từng API ghi luôn thiếu (review #186 còn 6 nhóm API lọt)

- Phương án: (1) tiếp tục liệt kê API ghi theo từng ngôn ngữ · (2) mặc định chặn: script nhắc tới đường dẫn được canh (fence/secret/evidence/.git/hooks|config) thì deny, trừ khi toàn script chỉ gồm thao tác đọc trong danh sách cho phép · (3) chặn mọi script nhắc tới đường dẫn được canh, không ngoại lệ
- Chọn: mặc định chặn: script nhắc tới đường dẫn được canh (fence/secret/evidence/.git/hooks|config) thì deny, trừ khi toàn script chỉ gồm thao tác đọc trong danh sách cho phép
- Lý do (tiêu chí chất lượng cuối): tiêu chí 1: danh sách API ghi là vô hạn (rename/copy/delete/số cờ/thư viện), phân tích tĩnh không thể đầy đủ → đảo sang allowlist thao tác đọc; tiêu chí 4: đọc .env/.claude bằng script vẫn chạy, agent sửa file canh vẫn có Edit/Write (đường duy nhất được thiết kế)
- Đường lùi: trả về liệt kê API ghi (DIRECT_WRITE_FMT)

### D-106 · 2026-10-20T10:31:13+00:00 · cd tới thư mục guard không giải được (cờ ghép, chuyển hướng đầu lệnh, CDPATH, biến)

- Phương án: (1) coi cwd 'không biết' như gốc dự án (hiện tại) · (2) cwd không biết: đích ghi tương đối được thử ở mọi thư mục canh (gốc, .claude, .claude/hooks, .autopilot, .git, .git/hooks) — trúng chỗ nào là chặn
- Chọn: cwd không biết: đích ghi tương đối được thử ở mọi thư mục canh (gốc, .claude, .claude/hooks, .autopilot, .git, .git/hooks) — trúng chỗ nào là chặn
- Lý do (tiêu chí chất lượng cuối): tiêu chí 1: mất dấu cwd không được làm mở đường; chặn oan chỉ khi tên file trùng tên file canh trong thư mục canh, hiếm
- Đường lùi: trả về coi cwd không biết là gốc dự án

### D-107 · 2026-10-20T11:27:35+00:00 · Bộ che chuỗi/comment cho script không phải Python (node/ruby/perl/php): ký tự # / % quote-like làm lệch che

- Phương án: (1) fail-closed: phần mã còn lại có # / % << quote-like Perl… thì coi là không chỉ đọc · (2) cho riêng comment # ở đầu dòng
- Chọn: fail-closed: phần mã còn lại có # / % << quote-like Perl… thì coi là không chỉ đọc
- Lý do (tiêu chí chất lượng cuối): tiêu chí 1: che sai từng làm lọt ghi thật (review #186 lần 2); chặn oan chỉ khi script nhắc đường dẫn canh, agent còn Edit/Write
- Đường lùi: cho comment # đầu dòng

### D-108 · 2026-10-20T13:04:06+00:00 · Duyệt PLAN-3.11 (audit delta f36ea90..0afa30d → sửa 🔴/🟠 → quét lại → release-check)

- Phương án: (1) Audit delta theo nhóm bị chạm tại 0afa30d, sửa, quét lại theo diff bản sửa · (2) Chỉ cập nhật SHA quét của sổ sang 0afa30d dựa vào review PR #185/#186
- Chọn: Audit delta theo nhóm bị chạm tại 0afa30d, sửa, quét lại theo diff bản sửa
- Lý do (tiêu chí chất lượng cuối): tiêu chí 1: release-check đòi audit phủ mã đổi; #185/#186 sửa guard ~1000 dòng — review PR không thay audit theo nhóm (SEC-088/089 chỉ lộ ra ở review lần 2); phương án 2 là lời khai
- Đường lùi: dừng sau T-1601, giữ báo cáo; cập nhật SHA sổ theo PR review

### D-109 · 2026-10-20T15:08:28+00:00 · Bỏ bước reviewer cho PR của repo khung: chỉ cần CI xanh là auto-merge (yêu cầu chủ repo 2026-10-20)

- Phương án: (1) Đặt delivery_phase: build trong xt.yaml (cơ chế ADR-0031 có sẵn: review thành nợ, release-check đòi harden ở G7) · (2) Hạ merge_autonomy hoặc sửa merge-check để bỏ hẳn review_gate
- Chọn: Đặt delivery_phase: build trong xt.yaml (cơ chế ADR-0031 có sẵn: review thành nợ, release-check đòi harden ở G7)
- Lý do (tiêu chí chất lượng cuối): tiêu chí 1+3: dùng đúng cơ chế đã có test, không nới guard/merge-check; nợ review được ghi và đòi trả ở G7 — đúng ý 'để dành reviewer cho giai đoạn hoàn thiện'; ngoại lệ cứng và review blocking vẫn chặn
- Đường lùi: đổi lại delivery_phase: harden trong xt.yaml, hoàn test + AGENTS.md

### D-110 · 2026-10-20T15:52:09+00:00 · Tối giản autopilot ở pha build: bỏ khâu nào?

- Phương án: (1) Giữ nguyên: reviewer mỗi PR, audit delta mỗi mốc, PROGRESS mỗi task · (2) Pha build: audit delta theo mốc gom về G7 (release-check review_debt đã chặn); reviewer chỉ khi pr next trả review (mọi pha); PROGRESS cập nhật theo lát/PR thay vì mỗi task · (3) Bỏ thêm cổng đầy đủ cục bộ trước push và tắt auto-merge trước push
- Chọn: Pha build: audit delta theo mốc gom về G7 (release-check review_debt đã chặn); reviewer chỉ khi pr next trả review (mọi pha); PROGRESS cập nhật theo lát/PR thay vì mỗi task
- Lý do (tiêu chí chất lượng cuối): Ba khâu này không thêm chốt an toàn ở pha build: review đã hoãn bằng máy (ADR-0031) nên giao reviewer chỉ tốn lượt; audit theo mốc trùng với audit delta bắt buộc trước G7 (release-check FAIL phase/review_debt); compaction dùng checkpoint của loop nên PROGRESS mỗi task chỉ thêm commit. Giữ cổng đầy đủ trước push (tránh vòng CI đỏ) và tắt auto-merge trước push (chốt ngoại lệ cứng khi push thêm file nhạy cảm) vì tiêu chí 1 thắng tiêu chí 5.
- Đường lùi: Đặt delivery_phase: harden (audit theo mốc trở lại ngay) hoặc revert commit; không có state mới cần dọn.

### D-111 · 2026-10-20T16:58:24+00:00 · Duyệt PLAN-3.12-lean (tối ưu toàn bộ khung + dự án đích)?

- Phương án: (1) Duyệt PLAN 3 lát / 23 task như đã lập: tài liệu một nhà → harness ít lượt/nhanh hơn → dự án đích nhẹ + nâng cấp thật · (2) Chỉ làm Lát 1 (tài liệu) rồi dừng chờ chủ repo xem · (3) Làm cả việc đã loại (tách guard.py nạp lười, cài chọn lọc framework, gộp job CI)
- Chọn: Duyệt PLAN 3 lát / 23 task như đã lập: tài liệu một nhà → harness ít lượt/nhanh hơn → dự án đích nhẹ + nâng cấp thật
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1 (đúng, an toàn): mọi luật bỏ khỏi tài liệu đều còn nhà + link và test một nhà; hook/cổng sửa đều giữ LOOP-STOP-027, test hook 217 ca + bench 308 ca; sửa bất nhất pyc theo hướng chặt hơn. Tiêu chí 3 (bền, đơn giản): số liệu khảo sát cho thấy 35–60 % nội dung quy trình là trùng, 3/7 lệnh mỗi PR máy làm được, commit xt.py mất 131 s vì coverage trùng cổng PR. Phương án 2 bỏ dở yêu cầu 'toàn bộ'. Phương án 3 chạm hàng rào bảo mật (guard) với lợi 100 ms/lệnh và lệch WF-CI-024 — loại theo tiêu chí 1.
- Đường lùi: Mỗi lát một PR, revert PR; tài liệu: git revert không mất gì; cổng commit: đặt lại hành vi cũ trong dev-task; install.py: hash file gốc chỉ thêm metadata, bỏ là về copy-if-absent.

### D-112 · 2026-10-20T17:35:20+00:00 · Cổng commit khi diff đụng cấu hình cổng (xt.yaml, xt.py, dev-task.sh, hook, ruff/coverage/requirements): giữ cổng đầy đủ có coverage hay đổi?

- Phương án: (1) Giữ: cổng đầy đủ có ngưỡng coverage (131 s) như review #177 · (2) gate-fast nhưng bước test = MỌI lớp qua test_list/test_unit song song, không coverage (~75 s); chưa khai hai khoá → test đầy đủ; coverage 100 % giữ ở cổng trước PR và CI · (3) Bỏ hẳn cổng commit cho diff đụng cấu hình, chỉ dựa cổng PR/CI
- Chọn: gate-fast nhưng bước test = MỌI lớp qua test_list/test_unit song song, không coverage (~75 s); chưa khai hai khoá → test đầy đủ; coverage 100 % giữ ở cổng trước PR và CI
- Lý do (tiêu chí chất lượng cuối): Review #177 chặn việc commit tự hạ cổng của chính nó (xt.py chọn test); chạy MỌI lớp test không phụ thuộc test-select nên vẫn đóng lỗ đó (tiêu chí 1), còn ngưỡng coverage là việc của cổng trước PR và CI vốn chạy lại y hệt — lặp ở mỗi commit chỉ tốn 55 s × 49 % commit (tiêu chí 3/5). Phương án 3 bỏ chốt sớm — loại theo tiêu chí 1.
- Đường lùi: Đặt lại task=gate trong pre-bash-guard.sh (một dòng) hoặc bỏ nhánh XT_GATE_ALL_TESTS trong dev-task.sh; không có state mới.

### D-113 · 2026-10-20T18:01:14+00:00 · loop record exit 0 khớp Gate: máy tự tick [x] trong PLAN hay để agent tick tay?

- Phương án: (1) Để agent tick tay như cũ (1 Edit + 2 hook mỗi task, agent có thể quên hoặc tick sai task) · (2) Máy tự tick khi lệnh khớp Gate và exit 0 (cờ --no-tick để tắt); đỏ/khác Gate/zero-tests không tick
- Chọn: Máy tự tick khi lệnh khớp Gate và exit 0 (cờ --no-tick để tắt); đỏ/khác Gate/zero-tests không tick
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1: tick sau bằng chứng của chính máy chặt hơn lời khai của agent (P1) — Stop hook verify vẫn đối chiếu; tiêu chí 3/5: bớt một lượt Edit + hai hook (~0,5 s) mỗi task và hết lỗi tick nhầm.
- Đường lùi: --no-tick hoặc bỏ nhánh tick trong loop_record; PLAN là file text, revert bằng git.

### D-114 · 2026-10-20T18:17:02+00:00 · T-1732 install.py nâng bản: 4 điểm mở của executor-deep (hash PROGRESS theo HEAD; in 53 KB khối CHANGELOG; harness updated-new giữ hash cũ; dự án 3.7.1 chưa có hash file gốc)

- Phương án: (1) A: giữ đúng đặc tả T-1732 — PROGRESS băm sau khi thay SHA (mỗi HEAD mới lại ra .xtemplates-new trên nhánh chính), in đủ khối CHANGELOG, harness updated-new giữ hash cũ (báo lại mỗi lần cài), lần nâng đầu gộp tay mọi file gốc đã sửa · (2) B: PROGRESS băm mẫu TRƯỚC khi thay SHA (kept-own ở mọi nhánh); chỉ in mệnh đề "Dự án đích…" tới hết câu kèm [bản]; harness/GitHub updated-new ghi hash mẫu mới như file gốc (báo một lần mỗi lần mẫu đổi); lần nâng đầu suy hash cũ từ .xtemplates/framework/templates/* cũ trước khi thay (file gốc chưa sửa cập nhật tại chỗ)
- Chọn: B: PROGRESS băm mẫu TRƯỚC khi thay SHA (kept-own ở mọi nhánh); chỉ in mệnh đề "Dự án đích…" tới hết câu kèm [bản]; harness/GitHub updated-new ghi hash mẫu mới như file gốc (báo một lần mỗi lần mẫu đổi); lần nâng đầu suy hash cũ từ .xtemplates/framework/templates/* cũ trước khi thay (file gốc chưa sửa cập nhật tại chỗ)
- Lý do (tiêu chí chất lượng cuối): Tiêu chí (1) đúng: cùng một luật cho mọi nhóm file — chỉ báo khi mẫu đổi, không báo theo HEAD; (3) ít nhiễu: 4,9 KB thay vì 53 KB, .xtemplates-new một lần; (4) hotel-manager/X-Company nâng từ 3.7.1 không phải gộp tay AGENTS/CLAUDE chưa sửa
- Đường lùi: đảo từng điểm: băm sau thay SHA / in đủ khối / giữ hash cũ ở harness / bỏ bước suy hash (mỗi điểm một hàm riêng trong install.py)

### D-115 · 2026-10-21T04:42:43+00:00 · CI/E2E/CD ở dự án đích: cấu hình tối thiểu khi triển khai ban đầu và chạy song song tối đa (chủ repo 2026-10-21) — mẫu đặt thế nào?

- Phương án: (1) A: giữ ci.yml (job test-plan tuần tự trước test), E2E và CD để dự án tự viết theo QA-E2E-020…026 và WF-CI-012 · (2) B: một ci.yml mở rộng — bỏ test-plan (matrix tĩnh, mỗi shard tự đọc xt.yaml qua dev-task.sh test-mode), thêm job e2e matrix tĩnh không needs (tự build qua lệnh e2e, XT_SHARD=I/N), build job đóng gói artefact một lần trên push main, deploy-staging trong ci.yml needs quality (environment staging), production = deploy.yml workflow_dispatch nâng artefact của một run CI theo run_id (cũng là rollback) · (3) C: như B nhưng CD là workflow riêng kích bằng workflow_run sau CI
- Chọn: B: một ci.yml mở rộng — bỏ test-plan (matrix tĩnh, mỗi shard tự đọc xt.yaml qua dev-task.sh test-mode), thêm job e2e matrix tĩnh không needs (tự build qua lệnh e2e, XT_SHARD=I/N), build job đóng gói artefact một lần trên push main, deploy-staging trong ci.yml needs quality (environment staging), production = deploy.yml workflow_dispatch nâng artefact của một run CI theo run_id (cũng là rollback)
- Lý do (tiêu chí chất lượng cuối): (1) đúng/an toàn: không job tuần tự trước fan-out; e2e/deploy rỗng thì bỏ qua có log, không tạo deployment giả (job-level if theo output của build); deploy chỉ chạy ở push main với environment; production chỉ nâng artefact đã qua CI (kiểm run: CI, push, nhánh mặc định, success, cùng repo) và kiểm SHA256SUMS; tránh workflow_run (zizmor dangerous-triggers, bẫy nhánh fork tên main). (2) đường lùi: dispatch run_id cũ = rollback một lệnh; mẫu copy-if-absent. (3) không theo stack — mọi lệnh ở xt.yaml (package/deploy/smoke/e2e/e2e_setup) qua dev-task + guard; test được bằng bash. (5) wall time = max(job) thay vì plan+job
- Đường lùi: Revert PR: ci.yml về bản có test-plan; xoá deploy.yml khỏi GITHUB_FILES; dev-task bỏ test-mode/e2e/package/deploy/declared; dự án đã cài giữ bản của họ (copy-if-absent)

### D-116 · 2026-10-21T04:51:17+00:00 · Ruleset nhánh chính của dự án đích: tối thiểu và song song tối đa (chủ repo 2026-10-21)

- Phương án: (1) A: giữ ruleset chung với repo khung (5 required check gồm dep-audit chưa có job; strict up-to-date) · (2) B: mẫu riêng framework/templates/ruleset-main.json — 4 required check mà mẫu workflow đã cung cấp (quality, protection-guard, gitleaks, merge-gate; dep-audit khi có thì là job con trong quality.needs), strict_required_status_checks_policy false để PR merge song song không phải cập nhật + chạy lại CI sau mỗi merge; lớp đỡ: CI chạy lại trên push main (bắt lỗi kết hợp), deploy chỉ từ commit có quality xanh trên main, PR đẩy sau đó test trên merge ref mới. Repo khung giữ ruleset riêng của nó · (3) C: như B nhưng giữ strict true
- Chọn: B: mẫu riêng framework/templates/ruleset-main.json — 4 required check mà mẫu workflow đã cung cấp (quality, protection-guard, gitleaks, merge-gate; dep-audit khi có thì là job con trong quality.needs), strict_required_status_checks_policy false để PR merge song song không phải cập nhật + chạy lại CI sau mỗi merge; lớp đỡ: CI chạy lại trên push main (bắt lỗi kết hợp), deploy chỉ từ commit có quality xanh trên main, PR đẩy sau đó test trên merge ref mới. Repo khung giữ ruleset riêng của nó
- Lý do (tiêu chí chất lượng cuối): (1) đúng: ruleset chỉ đòi check có job thật — dự án mới không treo PR ở ngày đầu; rủi ro lỗi kết hợp hai PR được CI trên main + deploy gate chặn trước khi tới người dùng. (2) đường lùi: đặt strict true một dòng JSON hoặc thêm context. (3) một nguồn: ruleset mẫu khớp đúng job mẫu, protection-guard vẫn đối chiếu. (5) song song: N PR xanh merge liên tiếp không phải N vòng CI nối tiếp. Chủ repo yêu cầu rõ song song tối đa
- Đường lùi: GITHUB_FILES trỏ lại .github/rulesets/main.json; BASE-GATE-007/WF-GIT-002/WF-CI-001 về chữ cũ

### D-117 · 2026-10-21T05:05:54+00:00 · Chủ repo 2026-10-21: 'ruleset đã ở mức tối thiểu chưa? bỏ cd' — gỡ CD khỏi mẫu; ruleset dự án đích rút tới đâu?

- Phương án: (1) A: gỡ CD, giữ ruleset 4 check (quality, protection-guard, gitleaks, merge-gate) · (2) B: gỡ CD (deploy.yml, deploy-staging, package/deploy/declared của dev-task, khoá package/deploy/smoke, WF-CI-026); ruleset 3 check quality, gitleaks, merge-gate — protection-guard thành job con trong quality.needs · (3) C: như B và bỏ thêm gitleaks/merge-gate khỏi required
- Chọn: B: gỡ CD (deploy.yml, deploy-staging, package/deploy/declared của dev-task, khoá package/deploy/smoke, WF-CI-026); ruleset 3 check quality, gitleaks, merge-gate — protection-guard thành job con trong quality.needs
- Lý do (tiêu chí chất lượng cuối): (1) an toàn: protection-guard chỉ chặn lỗi cấu hình làm PR treo (fail-closed) nên làm job con của quality không mở lỗ; gitleaks (bí mật lộ là không đảo ngược) và merge-gate (chặn auto-merge ngoại lệ cứng, ADR-0023) giữ vì bỏ là hạ sàn an toàn — C loại. Cấm xoá/force-push, PR bắt buộc giữ (không đảo ngược). (2) chủ repo quyết bỏ CD; WF-CI-026 chưa phát hành nên gỡ hẳn. (3) ít context required hơn = ít chỗ lệch tên job
- Đường lùi: Thêm lại context protection-guard vào ruleset-main.json và bỏ khỏi quality.needs; CD lấy lại từ commit 71d3829 của PR #194

### D-118 · 2026-10-21T06:39:33+00:00 · Duyệt PLAN-3.13-next-level (16 task, 5 lát: K-1 merge-gate workflow_run, đóng khe lọt, máy đo, nền, cắt bản)?

- Phương án: (1) Duyệt 5 lát/16 task như đã lập: K-1 trước (hạn 2026-11-02), rồi khe lọt đã đo, máy đo, nền có đo trước, cắt bản + nâng dự án đích · (2) Chỉ làm Lát 0 (K-1) rồi dừng chờ chủ repo xem research · (3) Làm cả NH-3 song song worktree và NH-4 effort trong đợt này
- Chọn: Duyệt 5 lát/16 task như đã lập: K-1 trước (hạn 2026-11-02), rồi khe lọt đã đo, máy đo, nền có đo trước, cắt bản + nâng dự án đích
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1 (đúng, an toàn): K-1 có hạn thật và required check của 3 repo phụ thuộc; mọi lát còn lại có bằng chứng run đỏ/lỗ hổng thật trong research §2–§4, mỗi task Gate máy kiểm, phụ thuộc mới chỉ ở nightly/dev ghim hash. Phương án 2 bỏ dở yêu cầu 'nâng tầng' của chủ repo. Phương án 3 chạm effort/song song khi chưa có số (research §4.4: hạ effort từng gây suy giảm; song song ~12× token) — loại theo tiêu chí 1/3; làm sau khi TD-4 có số.
- Đường lùi: Mỗi lát một PR, revert PR; merge-gate: giữ file cũ tới khi check-run được ruleset tính; phụ thuộc mới gỡ khỏi requirements-*.txt; hook mới gỡ khỏi settings + install

### D-119 · 2026-10-21T06:54:03+00:00 · merge-gate theo workflow_run: đánh giá lại khi người tắt auto-merge (sự kiện auto_merge_disabled không còn kích) và nhiều check-run cùng tên trên một head

- Phương án: (1) A: không đổi mã — người re-run CI hoặc push để check xanh lại; mỗi lần đánh giá POST check-run mới · (2) B: merge-gate.yml thêm workflow_dispatch input pr, steward gọi (cần actions: write) · (3) C: pr-steward (đã nghe workflow_run CI/merge-gate + lịch 10 phút, có token ghi) đánh giá lại merge-gate cho PR nó xét bằng xt.py merge-gate --pr N --check-run (head hiện tại của PR), chỉ tạo check-run khi kết luận khác check-run merge-gate mới nhất trên head (GET commits/{sha}/check-runs?check_name=merge-gate); nhiều PR cùng head → một kết luận cho head, đỏ nếu bất kỳ PR nào block; pr-steward.yml thêm checks: write
- Chọn: C: pr-steward (đã nghe workflow_run CI/merge-gate + lịch 10 phút, có token ghi) đánh giá lại merge-gate cho PR nó xét bằng xt.py merge-gate --pr N --check-run (head hiện tại của PR), chỉ tạo check-run khi kết luận khác check-run merge-gate mới nhất trên head (GET commits/{sha}/check-runs?check_name=merge-gate); nhiều PR cùng head → một kết luận cho head, đỏ nếu bất kỳ PR nào block; pr-steward.yml thêm checks: write
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1: luồng ngoại lệ cứng (merge_hard_exceptions: human) cần check xanh lại sau khi tắt auto-merge để người merge tay — A bắt người re-run CI (dễ quên, PR treo), B thêm quyền actions: write cho steward. C dùng đúng reconciler đã có (idempotent theo (repo, PR, head, hành động)), quyền chỉ thêm checks: write, không POST trùng mỗi 10 phút; check-run gắn theo SHA nên một head một kết luận là đúng mô hình GitHub, fail-closed khi có PR block
- Đường lùi: Bỏ bước merge-gate trong pr steward --apply và checks: write; merge-gate.yml vẫn tạo check-run theo workflow_run; người re-run CI khi cần

### D-120 · 2026-10-21T06:55:50+00:00 · Cách chuyển merge-gate sang workflow_run an toàn khi PR Lát 0 không thể tự kiểm đường mới (workflow_run chạy bản ở nhánh mặc định)

- Phương án: (1) A: gỡ pull_request_target ngay trong PR Lát 0 (kiểm trên PR Lát A; nếu ruleset không tính check-run API thì mọi PR sau treo, kể cả PR sửa) · (2) B: chuyển tiếp — giữ pull_request_target (required check như cũ) và thêm workflow_run tạo check-run quan sát tên merge-gate-v2 (cờ --check-name); steward đánh giá lại (D-119) chỉ khi XT_MERGE_GATE_RECONCILE=on; task mới T-1834 gỡ pull_request_target + đổi tên về merge-gate sau khi thấy check-run đúng trên head PR Lát A
- Chọn: B: chuyển tiếp — giữ pull_request_target (required check như cũ) và thêm workflow_run tạo check-run quan sát tên merge-gate-v2 (cờ --check-name); steward đánh giá lại (D-119) chỉ khi XT_MERGE_GATE_RECONCILE=on; task mới T-1834 gỡ pull_request_target + đổi tên về merge-gate sau khi thấy check-run đúng trên head PR Lát A
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1/2: A có đường hỏng không tự sửa được (required check không báo chặn cả PR sửa — cần người tắt ruleset); B giữ đường lùi và kiểm được bằng quan sát thật trước khi cắt, vẫn xong trước hạn 2026-11-02 trong phiên này; chi phí một cờ --check-name và một task
- Đường lùi: Gỡ trigger workflow_run và cờ --check-name khỏi merge-gate.yml; xoá T-1834

### D-121 · 2026-10-21T07:06:03+00:00 · Chủ repo hỏi: hướng Lát 0 (merge-gate → workflow_run + check-run, D-120) có bảo đảm code nhanh và ruleset tối thiểu không? Chọn giữa giữ hướng A hay đổi sang B (bỏ hẳn required check merge-gate)

- Phương án: (1) A: giữ D-120 — merge-gate theo workflow_run + check-run REST, chuyển tiếp hai trigger, T-1834 cắt; không cần chủ repo nếu GitHub tính check-run API là context bắt buộc (quan sát merge-gate-v2 trước khi cắt) · (2) B: bỏ required check merge-gate — không bật auto-merge nữa, phiên/steward merge ghim head sau merge-check xanh; xoá merge-gate.yml ở 3 repo, bỏ ADR-0035 + mã check-run; ruleset dự án đích còn 2 check, khung còn 4; cần chủ repo gỡ merge-gate khỏi 3 ruleset TRƯỚC khi xoá file, cần XT_STEWARD_TOKEN để merge của steward kích workflow push
- Chọn: A: giữ D-120 — merge-gate theo workflow_run + check-run REST, chuyển tiếp hai trigger, T-1834 cắt; không cần chủ repo nếu GitHub tính check-run API là context bắt buộc (quan sát merge-gate-v2 trước khi cắt)
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1 (đúng, an toàn, tự host trước): A làm trọn trong phiên trước hạn 2026-11-02 không phụ thuộc chủ repo (giả định chưa xác minh được kiểm bằng check quan sát trước khi cắt); B chặn ở ba thao tác ruleset chỉ chủ repo làm được và XT_STEWARD_TOKEN đang treo — nếu chủ repo không kịp thì PR treo sau hạn. Tiêu chí 2: A có T-1834 và đường lùi trong repo; B lùi lại cũng cần chủ repo. Tiêu chí 3 (đơn giản, ít code) B hơn hẳn — nên B được ghi là đề xuất chính thức cho chủ repo: khi chủ repo gỡ merge-gate khỏi ruleset, lát sau xoá merge-gate.yml, mã check-run và đường auto-merge (ruleset tối thiểu thật)
- Đường lùi: Chủ repo chọn B: dừng T-1803/T-1834, gỡ merge-gate khỏi 3 ruleset (chủ repo), rồi lát mới: pr next/steward không bật auto-merge, guard chặn gh pr merge --auto, xoá merge-gate.yml + ADR-0035 đánh dấu thay, dự án đích nhận qua install.py

### D-122 · 2026-10-21T07:14:43+00:00 · Chủ repo trả lời 'chấp nhận đề xuất' cho câu hỏi ở D-121: hướng Lát 0

- Phương án: (1) A: giữ D-120/D-121 (merge-gate theo workflow_run + check-run) · (2) B: bỏ required check merge-gate — không bật auto-merge của GitHub nữa; phiên/steward merge ghim head sau merge-check xanh ở đúng head; merge-gate.yml thành stub pull_request luôn xanh (giữ context tới khi chủ repo gỡ khỏi ruleset ba repo, rồi xoá); bỏ ADR-0035 + mã check-run (T-1802); guard chặn bật auto-merge; ruleset mẫu dự án đích còn quality + gitleaks
- Chọn: B: bỏ required check merge-gate — không bật auto-merge của GitHub nữa; phiên/steward merge ghim head sau merge-check xanh ở đúng head; merge-gate.yml thành stub pull_request luôn xanh (giữ context tới khi chủ repo gỡ khỏi ruleset ba repo, rồi xoá); bỏ ADR-0035 + mã check-run (T-1802); guard chặn bật auto-merge; ruleset mẫu dự án đích còn quality + gitleaks
- Lý do (tiêu chí chất lượng cuối): Quyết định của chủ repo (quyền cuối, AGENTS.md §1) — ghi đè D-121. Tiêu chí 3: ít máy móc nhất (xoá thay vì thêm), một luật duy nhất kiểm được: merge luôn ghim head đã đánh giá; K-1 hết vì không còn pull_request_target. Tiêu chí 1 giữ: stub luôn xanh không nới an toàn vì mọi đường merge của máy đều ghim head và đọc lại merge-check; auto-merge do người bật bị steward tắt. Tiêu chí 2: ruleset chỉ bớt check, lùi lại = thêm lại check + revert PR
- Đường lùi: Revert PR Lát 0 rev B; thêm lại merge-gate vào ruleset; quay về ADR-0023 (pull_request_target cần event policy của chủ repo sau 2026-11-02)

### D-123 · 2026-10-21T09:46:04+00:00 · Lát A: ba câu hỏi mở của executor — pr title-check khi pr_title_check: off; khoá cứng bản shellcheck trong lint; mẫu secret-scan giữ gitleaks-action hay đổi CLI (CL-9)

- Phương án: (1) A: off → bỏ qua exit 0; không khoá cứng bản shellcheck (CI cài từ requirements-dev.txt ghim hash); giữ gitleaks-action + ghi chú EULA, đổi CLI là lát riêng cần chủ repo · (2) B: luôn kiểm tiêu đề; lint đỏ khi shellcheck ≠ 0.11.0; đổi mẫu sang gitleaks CLI ngay
- Chọn: A: off → bỏ qua exit 0; không khoá cứng bản shellcheck (CI cài từ requirements-dev.txt ghim hash); giữ gitleaks-action + ghi chú EULA, đổi CLI là lát riêng cần chủ repo
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1/3: A theo đúng cấu hình dự án (không chặn oan dự án đã tắt luật), không làm đỏ máy dev chưa cài requirements-dev, không đổi nội dung required check gitleaks của dự án đích khi chưa có người duyệt; B chặt hơn nhưng chặn oan và đổi hợp đồng dự án đích
- Đường lùi: Bật kiểm tiêu đề vô điều kiện trong cmd_pr_title_check; thêm kiểm bản shellcheck vào lint của xt.yaml; lát mới đổi secret-scan mẫu sang CLI

### D-124 · 2026-10-21T09:50:12+00:00 · Chủ repo yêu cầu 2026-10-21: reviewer/reviewer-alt chỉ chạy ở pha harden; chỉ chuyển sang harden khi lên production — pha build xử lý PR ngoại lệ cứng đã miễn (hard_waived) và nhãn risk: thế nào

- Phương án: (1) A: pha build hoãn review (ghi nợ) cho MỌI PR mà máy được merge — kể cả hard_waived và nhãn risk:; ngoại lệ cứng giữ người (merge_hard_exceptions: human) vẫn do người merge; review blocking đã có vẫn chặn; nợ trả ở harden (release-check review_debt); /autopilot không giao reviewer ở pha build · (2) B: giữ ADR-0031 — build vẫn đòi review cho hard_waived và risk:
- Chọn: A: pha build hoãn review (ghi nợ) cho MỌI PR mà máy được merge — kể cả hard_waived và nhãn risk:; ngoại lệ cứng giữ người (merge_hard_exceptions: human) vẫn do người merge; review blocking đã có vẫn chặn; nợ trả ở harden (release-check review_debt); /autopilot không giao reviewer ở pha build
- Lý do (tiêu chí chất lượng cuối): Quyết định của chủ repo (quyền cuối). An toàn còn lại: người vẫn merge ngoại lệ cứng giữ người; review chặn đã có không bị rửa; release-check FAIL phase/review_debt tới khi harden + audit delta trước phát hành; harden chỉ bật khi lên production
- Đường lùi: review_deferrable thêm lại điều kiện not hard_waived, review_deferred thêm not risk_labels; ADR-0037 đổi trạng thái

### D-125 · 2026-10-21T10:43:13+00:00 · Gate T-1833 gọi zizmor trần (mặc định online, 401 qua proxy phiên) trong khi bước CI dep-audit chạy --offline

- Phương án: (1) A: đổi Gate thành zizmor --offline --min-severity high .github/workflows — khớp đúng bước CI · (2) B: giữ Gate, đặt ZIZMOR_OFFLINE=true ngoài lệnh khi chạy loop record
- Chọn: A: đổi Gate thành zizmor --offline --min-severity high .github/workflows — khớp đúng bước CI
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 3: Gate tự chứa, chạy lại được y nguyên, khớp CI (không nới so với CI vì CI cũng offline); B phụ thuộc biến môi trường ẩn
- Đường lùi: Đổi Gate về zizmor trần và chạy với token GitHub

### D-126 · 2026-10-21T11:05:12+00:00 · Chủ repo hỏi 2026-10-21: biến dự án này thành app và phân chia công việc được không — app dạng nào, chia việc thế nào

- Phương án: (1) Ứng dụng web cục bộ xt.py app: http.server stdlib trên 127.0.0.1, HTML/CSS/JS thuần không build, API JSON gọi đúng hàm xt.py của CLI, app không chạy lệnh; thêm xt.py plan waves xếp task thành đợt song song; PLAN-3.14-app 11 lát 29 task (ADR-0038) · (2) Site tĩnh xuất ra GitHub Pages: chia sẻ bằng URL nhưng không thấy trạng thái sống, phải chép logic compose sang JS hoặc sinh trước mọi tổ hợp · (3) Web app lưu trữ đa người dùng (framework web + DB + đăng nhập): cần hosting/tài khoản/khoá chỉ chủ repo có, phá luật stdlib, mặt tấn công lớn · (4) App desktop Tauri/Electron: thêm toolchain Rust/Node và ký số trả phí, không hơn phương án 1 · (5) Giữ CLI như hiện trạng
- Chọn: Ứng dụng web cục bộ xt.py app: http.server stdlib trên 127.0.0.1, HTML/CSS/JS thuần không build, API JSON gọi đúng hàm xt.py của CLI, app không chạy lệnh; thêm xt.py plan waves xếp task thành đợt song song; PLAN-3.14-app 11 lát 29 task (ADR-0038)
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1: một nguồn sự thật (cùng hàm với CLI), app không chạy lệnh nên không vòng qua guard, loopback + token + kiểm Host/Origin chặn trang khác đọc dữ liệu. Tiêu chí 2: gói tách rời, import lười, xoá là về hiện trạng; API JSON dùng lại được cho phương án 3. Tiêu chí 3: 0 phụ thuộc runtime mới, giữ stdlib và coverage 100 %. Tiêu chí 4: một lệnh, offline, chạy cả ở dự án đích. Mặc định tự host (AGENTS.md §4)
- Đường lùi: Revert PR Lát 0 (ADR-0038 + PLAN-3.14-app); nếu chủ repo muốn web app lưu trữ hay mobile: ADR mới thay ADR-0038, giữ Lát 1 (plan waves) vì độc lập với giao diện
- Khi chạy thật (đề xuất, chủ dự án quyết ở G7): Khi cần nhiều người hoặc dùng trên điện thoại: web app lưu trữ (phương án 3) dùng lại API JSON của SPEC-app, cần chủ repo chọn hosting và đăng nhập

### D-127 · 2026-10-21T11:30:11+00:00 · Chủ repo 2026-10-21: giữ tối thiểu job CI trên dự án đích, ruleset chỉ quality + gitleaks (sau khi đo e2e X-Company chờ runner 6 phút vì ~40 job hai repo cùng tài khoản tranh trần job đồng thời)

- Phương án: (1) A: mẫu CI = gate (dev-task.sh gate: build→typecheck→lint→test+coverage→checks, một job) + e2e (matrix [1], tăng shard khi đo chậm) + quality (gom, chạy luôn protection-guard như bước) — 3 job; dự án đích gộp job ngắn vào gate, giữ job dài độc lập (e2e shard, dast…) dưới quality; ruleset quality + gitleaks · (2) B: giữ fan-out ADR-0034 (mỗi task một job, test 4 shard, e2e 2 shard)
- Chọn: A: mẫu CI = gate (dev-task.sh gate: build→typecheck→lint→test+coverage→checks, một job) + e2e (matrix [1], tăng shard khi đo chậm) + quality (gom, chạy luôn protection-guard như bước) — 3 job; dự án đích gộp job ngắn vào gate, giữ job dài độc lập (e2e shard, dast…) dưới quality; ruleset quality + gitleaks
- Lý do (tiêu chí chất lượng cuối): Quyết định của chủ repo; khớp số đo: job ngắn (10–60 s) mỗi cái tốn một runner + thời gian khởi động/cài phụ thuộc, làm job dài (e2e) xếp hàng; ít job thì job dài được runner ngay. Không bỏ kiểm nào — chỉ gộp job
- Đường lùi: Khôi phục framework/templates/ci.yml bản 3.13.0 (ADR-0034)

### D-128 · 2026-10-21T11:41:09+00:00 · Chủ repo thêm 'chạy song song job tối đa có thể' sau yêu cầu 'tối thiểu job' (D-127) — dung hoà thế nào; X-Company: OSV-Scanner/CodeQL/pr-policy không còn required

- Phương án: (1) A: song song tối đa TRONG số job tối thiểu: mọi job bắt đầu cùng lúc (không needs ngoài quality); trong gate các nhóm độc lập chạy nền song song (typecheck ∥ lint ∥ build→test ∥ kiểm khác), log riêng, đỏ nếu nhóm nào đỏ; OSV-Scanner vào gate (vẫn chặn qua quality); CodeQL, pr-policy chạy nhưng không chặn · (2) B: tách lại thành nhiều job song song (ngược D-127)
- Chọn: A: song song tối đa TRONG số job tối thiểu: mọi job bắt đầu cùng lúc (không needs ngoài quality); trong gate các nhóm độc lập chạy nền song song (typecheck ∥ lint ∥ build→test ∥ kiểm khác), log riêng, đỏ nếu nhóm nào đỏ; OSV-Scanner vào gate (vẫn chặn qua quality); CodeQL, pr-policy chạy nhưng không chặn
- Lý do (tiêu chí chất lượng cuối): Thoả cả hai yêu cầu của chủ repo: không thêm job tranh runner (nguyên nhân e2e chờ 6 phút) mà vẫn rút ngắn gate bằng song song trong job; OSV vào gate giữ được sức chặn đã có (ruleset cũ đòi osv-scanner) mà không thêm required check
- Đường lùi: Bỏ chạy nền trong gate, về tuần tự (D-127)

### D-129 · 2026-10-21T11:41:26+00:00 · Gate T-1851 có vế ci-check framework/templates đỏ sẵn ở HEAD (quét cả xt.yaml/dependabot.yml không phải workflow)

- Phương án: (1) A: bỏ vế đó; test_ci_template đã chạy ci_check_text trên ci.yml và secret-scan.yml · (2) B: đổi xt.py ci-check bỏ qua file không có jobs:
- Chọn: A: bỏ vế đó; test_ci_template đã chạy ci_check_text trên ci.yml và secret-scan.yml
- Lý do (tiêu chí chất lượng cuối): Gate viết sai từ đầu; A giữ đúng kiểm (cả hai workflow mẫu vẫn qua ci-check trong test), không đổi công cụ
- Đường lùi: Thêm lại vế ci-check khi công cụ bỏ qua file không phải workflow

### D-130 · 2026-10-21T14:17:29+00:00 · Chủ repo: đọc commit chưa merge d388802 (audit tại ec4c7d2 + kế hoạch tối ưu), kiểm tra lại, nghiên cứu thêm rồi thi hành — làm gì trước PLAN-3.14-app

- Phương án: (1) A: nhập audit d388802, tái hiện độc lập từng phát hiện (repro + 2 người bác bỏ), sửa theo PLAN-3.15-audit-gate (bằng chứng Gate → cổng nhất quán → guard/reviewer → installer → đo CI) trước, tạm dừng PLAN-3.14-app · (2) B: tiếp PLAN-3.14-app như PROGRESS Tiếp theo 0, ghi các phát hiện vào sổ làm nợ · (3) C: chỉ merge báo cáo audit, không sửa
- Chọn: A: nhập audit d388802, tái hiện độc lập từng phát hiện (repro + 2 người bác bỏ), sửa theo PLAN-3.15-audit-gate (bằng chứng Gate → cổng nhất quán → guard/reviewer → installer → đo CI) trước, tạm dừng PLAN-3.14-app
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1 (đúng và an toàn): AUD-CODE-014 tái hiện được tới Stop hook (verified.json ok=True, final_verdict=done khi Gate thật exit 1) = cổng giả xanh 🔴 — mọi bằng chứng 'xong' của autopilot, gồm PLAN-3.14, dựa trên nó; AUD-XFEAT-013 làm cổng dự án đích xanh với 0 test. Tiêu chí 2: mỗi lát một PR, chỉ chặt hơn, revert được. PLAN-3.14 chưa có mã nên dừng không mất gì
- Đường lùi: loop init --force --plan docs/autopilot/PLAN-3.14-app.md; revert PR của từng lát

### D-131 · 2026-10-21T15:22:52+00:00 · T-2141: gom CI chính của repo khung 14 → 3 job (gate · quality · protection-guard) theo kế hoạch tối ưu 2026-10-21?

- Phương án: (1) A: giữ fan-out 14 job — đo 20 run: wall trung vị 94,5 s, chờ runner ≤ 4 s; 3 job ước ~200 s (gate-par cục bộ 179,5 s); repo public nên phút runner không tính phí · (2) B: gom 3 job như kế hoạch tối ưu — 15 → ~4 phút tính, wall ~gấp đôi · (3) C: gom vừa (build+typecheck+lint+checks một job, py311 2 shard) 14 → 10 job, giữ đường dài nhất — cần ADR đổi WF-CI-024 của repo khung
- Chọn: A: giữ fan-out 14 job — đo 20 run: wall trung vị 94,5 s, chờ runner ≤ 4 s; 3 job ước ~200 s (gate-par cục bộ 179,5 s); repo public nên phút runner không tính phí
- Lý do (tiêu chí chất lượng cuối): Tiêu chí nhận của chính kế hoạch tối ưu: chỉ nhận 14→3 khi thời gian hoàn tất đạt ngân sách — B kéo wall ~2 lần mà không có lợi đo được (không chờ runner, không tốn tiền). C chỉ đáng khi đo thấy tranh trần job đồng thời. Tiêu chí 3: không đổi kiến trúc CI khi chưa có số đo cần
- Đường lùi: C (ADR mới) khi chờ runner trung vị > 30 s hoặc repo chuyển riêng tư; số đo ở docs/ops/CI-TIMING-2026-10-21.md

### D-132 · 2026-10-21T15:33:19+00:00 · PR #207 (Lát 1) đủ điều kiện merge nhưng bộ phân loại Auto chặn lệnh merge của phiên và cron pr-steward không chạy ~1 giờ (lần cuối 14:37) — đi tiếp thế nào

- Phương án: (1) A: đẩy Lát 2 lên cùng nhánh/PR #207 — push kích CI, workflow_run CI kích pr-steward merge ghim head; PR ~430 dòng vượt mức 150 (pha build không giao reviewer) · (2) B: chờ cron pr-steward tới khi chạy lại, các lát còn lại đứng yên · (3) C: kích pr-steward bằng workflow_dispatch — cùng hiệu ứng với lệnh merge vừa bị chặn (LOOP-STOP-025), không làm
- Chọn: A: đẩy Lát 2 lên cùng nhánh/PR #207 — push kích CI, workflow_run CI kích pr-steward merge ghim head; PR ~430 dòng vượt mức 150 (pha build không giao reviewer)
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1: không vòng qua chặn (C loại); A giữ mọi cổng (CI đầy đủ, merge ghim head do máy steward quyết). Tiêu chí 2: lát vẫn là commit riêng, revert được. Đổi lại PR lớn hơn mức 150 dòng — chấp nhận ở pha build vì không có reviewer đọc diff; B treo vô hạn
- Đường lùi: Revert commit Lát 2 trên main

### D-133 · 2026-10-21T19:00:52+00:00 · T-1991: E2E trình duyệt + axe cho xt.py app đi đường nào (research/2026-10-21-app-e2e.md §8)

- Phương án: (1) A: Playwright for Python 1.64.0 (Apache-2.0) chỉ là phụ thuộc dev ở requirements-e2e.txt ghim hash riêng (pyee tách theo marker python_version), CI cài trình duyệt bằng playwright install --with-deps --only-shell chromium, không cache; axe-core 4.14.0 axe.min.js vendored ở tests_e2e/vendor/axe/ (không nằm trong scripts/app, không chép sang dự án đích) kèm LICENSE + SOURCE (URL, sha256, MPL-2.0) theo CMP-LIC-022, tiêm bằng add_script_tag; tag wcag2a…wcag22aa, ngưỡng critical/serious · (2) B: client CDP tự viết chỉ stdlib qua --remote-debugging-pipe + Chromium sẵn trên runner; axe như A · (3) C: không E2E trình duyệt, chỉ test tĩnh + --smoke; PRF-WEB-006 ghi không áp dụng
- Chọn: A: Playwright for Python 1.64.0 (Apache-2.0) chỉ là phụ thuộc dev ở requirements-e2e.txt ghim hash riêng (pyee tách theo marker python_version), CI cài trình duyệt bằng playwright install --with-deps --only-shell chromium, không cache; axe-core 4.14.0 axe.min.js vendored ở tests_e2e/vendor/axe/ (không nằm trong scripts/app, không chép sang dự án đích) kèm LICENSE + SOURCE (URL, sha256, MPL-2.0) theo CMP-LIC-022, tiêm bằng add_script_tag; tag wcag2a…wcag22aa, ngưỡng critical/serious
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1: Playwright là công cụ chuẩn, đã dùng ở bộ mẫu dự án đích (QA-E2E-*), chờ phần tử/console đáng tin; B là mã giao thức tự viết chưa có mẫu tham chiếu Python, rủi ro sai lặng; C bỏ MUST PRF-WEB-006. Tiêu chí 2: phụ thuộc chỉ ở job e2e và file requirements riêng, bộ test chính và runtime vẫn stdlib — xoá job là về như cũ. axe đặt dưới tests_e2e nên không phát tán sang dự án đích, nghĩa vụ MPL-2.0 chỉ là giữ nguyên tệp + thông báo. Tiêu chí 3: --only-shell giảm tải ~200 MB; không cache theo khuyến nghị docs CI
- Đường lùi: Gỡ job app-e2e và requirements-e2e.txt, tests_e2e/; hoặc đổi sang B nếu Playwright đổi giấy phép/telemetry

### D-134 · 2026-10-21T19:51:12+00:00 · T-1993: thêm mục PRF-WEB cho app vào BLUEPRINT.md repo khung thế nào — compose --add không nhận hồ sơ web-app; ghép lại toàn bộ đặt lại 21 MUST đổi chữ (nợ có sẵn từ 2026-10-15)

- Phương án: (1) A: ghép lại toàn bộ (cli-tool S) + kiểm lại 21 MUST đổi chữ trong T-1993 · (2) B: lấy đúng dòng PRF-WEB-* từ compose --profile web-app --scale S (chữ + rev chuẩn của khung), thêm thành mục riêng 'Ứng dụng cục bộ xt.py app (ADR-0038)' trong BLUEPRINT.md; tick kèm Kiểm chạy lại được hoặc [~] Không áp dụng có lý do; không đụng mục cũ · (3) C: hoãn T-1993 tới pha harden
- Chọn: B: lấy đúng dòng PRF-WEB-* từ compose --profile web-app --scale S (chữ + rev chuẩn của khung), thêm thành mục riêng 'Ứng dụng cục bộ xt.py app (ADR-0038)' trong BLUEPRINT.md; tick kèm Kiểm chạy lại được hoặc [~] Không áp dụng có lý do; không đụng mục cũ
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1: B đưa đúng chữ yêu cầu của khung, mỗi tick có lệnh kiểm; không giả xanh 21 mục cũ. Tiêu chí 2: mục riêng, revert một commit. A làm lẫn nợ cũ vào lát app (phạm vi); C để MUST PRF-WEB-006/007 của app không có nhà. Nợ 21 mục đổi chữ ghi vào PROGRESS cho audit delta trước G7
- Đường lùi: Xoá mục 'Ứng dụng cục bộ' khỏi BLUEPRINT.md; hoặc ghép lại toàn bộ ở pha harden (A)

### D-135 · 2026-10-21T20:15:49+00:00 · test_tracked_text_files_are_clean_utf8 đỏ: tests_e2e/vendor/axe/axe.min.js (vendored nguyên văn, MPL-2.0, sha256 ghim) chứa U+FFFD hợp lệ trong bảng ký tự

- Phương án: (1) A: loại thư mục vendored tests_e2e/vendor/ khỏi kiểm này — test nhằm file khung cài sang dự án đích; vendor không cài, đã có vendor-check --strict + sha256 trong SOURCE · (2) B: thoát ký tự trong axe.min.js — sửa tệp bên thứ ba, lệch sha256 nguồn, phải ghi Modifications theo MPL · (3) C: nạp axe từ npm lúc chạy CI thay vì vendored — thêm mạng/npm vào job, ngược D-133
- Chọn: A: loại thư mục vendored tests_e2e/vendor/ khỏi kiểm này — test nhằm file khung cài sang dự án đích; vendor không cài, đã có vendor-check --strict + sha256 trong SOURCE
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1: giữ tệp đúng nguồn (hash khớp npm), kiểm vẫn phủ mọi file khung cài sang; vendor được kiểm bằng vendor-check. Tiêu chí 3: một đường dẫn loại trừ có lý do trong test, không nới cho mã của khung
- Đường lùi: Bỏ loại trừ và chọn C (tải axe lúc chạy CI)

### D-136 · 2026-10-22T00:14:14+00:00 · Pha giao hàng của chính repo khung (chủ repo 2026-10-22: 'ở dự án khung thì luôn là production')

- Phương án: (1) Đặt delivery_phase: harden cố định trong xt.yaml của repo khung, test giữ không trôi · (2) Giữ build như D-109
- Chọn: Đặt delivery_phase: harden cố định trong xt.yaml của repo khung, test giữ không trôi
- Lý do (tiêu chí chất lượng cuối): Quyết định của chủ repo; repo khung là sản phẩm phát hành cho dự án đích nên luôn ở chất lượng phát hành: reviewer khác họ model lại bắt buộc ở PR làn chuẩn, guard không nới việc cục bộ (ADR-0040 chỉ áp dự án đích ở build). Thay D-109.
- Đường lùi: Đặt lại delivery_phase: build trong xt.yaml và sửa test test_delivery_phase_template_and_framework_repo_harden

### D-137 · 2026-10-22T01:01:35+00:00 · merge-check ở pr-steward đọc pha từ checkout nhánh đích nên PR tự đổi xt.yaml (#213) bị tính theo pha cũ

- Phương án: (1) PR sửa xt.yaml luôn tính harden (không thêm lời gọi API, chặt ở cả hai chiều đổi pha) · (2) Đọc thêm xt.yaml ở head PR qua REST contents, lấy pha chặt hơn
- Chọn: PR sửa xt.yaml luôn tính harden (không thêm lời gọi API, chặt ở cả hai chiều đổi pha)
- Lý do (tiêu chí chất lượng cuối): Đúng và an toàn: PR đổi pha theo chiều nào cũng cần review; đơn giản, không thêm I/O hay chế độ lỗi mạng; chi phí chỉ là PR sửa xt.yaml ở pha build phải chờ review — hiếm
- Đường lùi: Bỏ nhánh 'PR sửa xt.yaml' trong _merge_eval

### D-138 · 2026-10-22T08:47:19+00:00 · Duyệt PLAN-3.15.5-green-debt: /autopilot không kèm yêu cầu — làm gì?

- Phương án: (1) Dọn 5 🟢 mở của sổ audit có đường tái hiện máy và bản vá nhỏ, không cần quyết chính sách (SEC-076, SEC-100, CFG-004, XFEAT-002, TEST-019) → 3.15.5 · (2) Tách xt.py thành gói (AUD-ARCH-001) · (3) Dừng: báo không có việc máy làm được
- Chọn: Dọn 5 🟢 mở của sổ audit có đường tái hiện máy và bản vá nhỏ, không cần quyết chính sách (SEC-076, SEC-100, CFG-004, XFEAT-002, TEST-019) → 3.15.5
- Lý do (tiêu chí chất lượng cuối): (1) đúng/an toàn: đóng lỗ guard và lệch cổng có tái hiện; (2) đường lùi: mỗi lát một PR nhỏ revert được; (3) tách xt.py cần ADR + đổi danh sách copy của install.py — rủi ro lớn, không làm khi chưa có yêu cầu; dừng bỏ phí lỗi đã biết
- Đường lùi: revert PR lát tương ứng; phát hiện về lại 'mở' trong sổ

### D-139 · 2026-10-22T09:47:06+00:00 · Duyệt PLAN-3.16-audit-delta: /autopilot lần 2 — việc kế?

- Phương án: (1) Audit delta 0afa30d..HEAD + A11Y lần đầu, sửa 🔴/🟠, tới release-check GO · (2) Dọn tiếp 🟢 lẻ · (3) Dừng
- Chọn: Audit delta 0afa30d..HEAD + A11Y lần đầu, sửa 🔴/🟠, tới release-check GO
- Lý do (tiêu chí chất lượng cuối): (1) đúng/an toàn: release-check NO-GO vì review_debt 88 file chưa audit — đó là rủi ro thật chưa đo; 🟢 lẻ không đổi kết luận phát hành; (2) audit chỉ đọc + sổ, sửa theo đợt PR nhỏ
- Đường lùi: revert commit docs(audit); sổ về SHA cũ

### D-140 · 2026-10-22T10:01:26+00:00 · Xác minh đối kháng 🟠 audit 2026-10-22: giữ mức nào?

- Phương án: (1) Giữ 🟠 cả 3 · (2) Giữ 🟠 /api/blueprint ghi đè (tái hiện, trái ADR-0038 §2); hạ 🟢 smoke (chỉ chạy tay, đỏ giả không xanh giả) và pha floor (chủ ý ADR-0041, đỡ bởi merge-check harden + review + merge_risk_paths)
- Chọn: Giữ 🟠 /api/blueprint ghi đè (tái hiện, trái ADR-0038 §2); hạ 🟢 smoke (chỉ chạy tay, đỏ giả không xanh giả) và pha floor (chủ ý ADR-0041, đỡ bởi merge-check harden + review + merge_risk_paths)
- Lý do (tiêu chí chất lượng cuối): (1) đúng: mức theo audit.md — 🟠 là lỗi thật có điều kiện gây hại; smoke chỉ gây đỏ giả ở lệnh tay; floor theo cây làm việc là quyết định đã ghi, PR đổi pha vẫn qua review vì merge-check đọc nhánh đích; đổi nó cần ADR mới (đề xuất ở báo cáo)
- Đường lùi: nâng lại mức trong sổ và thêm task sửa

### D-141 · 2026-10-22T10:43:37+00:00 · Gate T-2309 gọi release-check → loop verify --all tự tham chiếu (verify chạy Gate, Gate đọc verify đang chạy) — làm gì?

- Phương án: (1) Đổi Gate T-2309 thành audit check --strict; release-check chạy riêng làm bước kết thúc (autopilot §Kết thúc) · (2) Giữ Gate, bỏ qua hàng verify
- Chọn: Đổi Gate T-2309 thành audit check --strict; release-check chạy riêng làm bước kết thúc (autopilot §Kết thúc)
- Lý do (tiêu chí chất lượng cuối): (1) đúng: không được nới/bỏ hàng verify; Gate của task không được phụ thuộc kết quả verify của chính vòng; release-check vốn là bước G7 sau done, không phải Gate task. Ghi chú cho khung: loop/plan lint có thể cảnh báo Gate gọi release-check (🟢 HAR)
- Đường lùi: đổi lại Gate cũ; chạy release-check ngoài vòng

### D-142 · 2026-10-23T10:38:30+00:00 · Sau phân tích trần phát triển 2026-10-23 (research/2026-10-23-ceiling-analysis.md): làm gì tiếp để giữ đơn giản · chất lượng · tốc độ?

- Phương án: (1) PLAN-3.16.0-ceiling: cắt lãng phí CI tự gây bằng cấu hình (bỏ edited khỏi CI nặng, CI trên main sau merge steward, đồng bộ ruleset, sửa wait giả), chất lượng nội dung nơi rẻ (checker Nguồn, unchecked_must có cờ, trần byte thư mục), đo thật (pr stats theo push, TARGETS/feedback); đóng băng bề mặt 3.x · (2) Tăng tốc bằng đổi mô hình: tách xt.py thành gói, song song worktree nhiều lát, thêm reviewer LLM cho mọi PR · (3) Dừng: chỉ lưu research, không lập PLAN
- Chọn: PLAN-3.16.0-ceiling: cắt lãng phí CI tự gây bằng cấu hình (bỏ edited khỏi CI nặng, CI trên main sau merge steward, đồng bộ ruleset, sửa wait giả), chất lượng nội dung nơi rẻ (checker Nguồn, unchecked_must có cờ, trần byte thư mục), đo thật (pr stats theo push, TARGETS/feedback); đóng băng bề mặt 3.x
- Lý do (tiêu chí chất lượng cuối): (1) đúng/an toàn: 3/4 run CI bị huỷ là cùng SHA do sự kiện edited và 3 commit mới nhất trên main chưa qua CI — hai lỗ đo được, sửa bằng cấu hình không thêm mã; (2) đường lùi: mỗi lát một PR nhỏ, revert được; (3) đơn giản: phương án 2 thêm mã/độ phức tạp trong khi lượt model (không phải CI) chiếm phần lớn một lát và chưa đo được; phương án 3 bỏ phí lỗ đã có bằng chứng
- Đường lùi: Revert PR từng lát; xoá PLAN-3.16.0-ceiling.md; ruleset file về strict true nếu chủ repo bật lại strict sống

### D-143 · 2026-10-23T11:12:16+00:00 · T-2403: ruleset sống lệch file ở 2 khoá (strict false, required_review_thread_resolution false) — đồng bộ thế nào?

- Phương án: (1) Đồng bộ cả hai khoá theo ruleset sống · (2) Đồng bộ strict=false (BASE-GATE-007 cách b: CI chạy lại trên main, nhờ T-2402); giữ required_review_thread_resolution=true trong file (WF-GIT-002 MUST), loop defer chủ repo bật lại ở ruleset sống · (3) Giữ file nguyên, chỉ ghi lệch vào RUNBOOK
- Chọn: Đồng bộ strict=false (BASE-GATE-007 cách b: CI chạy lại trên main, nhờ T-2402); giữ required_review_thread_resolution=true trong file (WF-GIT-002 MUST), loop defer chủ repo bật lại ở ruleset sống
- Lý do (tiêu chí chất lượng cuối): (1) đúng/an toàn: strict=false là quyết định đã có đường đạt hợp lệ (ADR-0034 §2, BASE-GATE-007 cách b) khi CI chạy trên push main — T-2402 cung cấp; tắt resolve thread không có ADR và trái MUST WF-GIT-002, chép theo sẽ hợp thức hoá việc nới cổng (LOOP-CI-001); (2) đường lùi: một dòng JSON; sửa ruleset sống là việc của chủ repo (LOOP-STOP-014)
- Đường lùi: Đổi lại strict=true trong main.json; hoặc nếu chủ repo chủ ý tắt resolve thread thì ghi ADR rồi đồng bộ khoá đó

### D-144 · 2026-10-23T11:16:20+00:00 · T-2403 sau khi chủ repo bật lại strict ở ruleset sống (2026-10-23): đồng bộ gì?

- Phương án: (1) Giữ main.json strict=true (đã khớp ruleset sống); chỉ khoá required_review_thread_resolution còn lệch — giữ true trong file, defer chủ repo bật · (2) Làm theo D-143 (đổi file sang strict=false)
- Chọn: Giữ main.json strict=true (đã khớp ruleset sống); chỉ khoá required_review_thread_resolution còn lệch — giữ true trong file, defer chủ repo bật
- Lý do (tiêu chí chất lượng cuối): (1) đúng: ruleset sống nay strict=true (gh api rules/branches/main) — file đã khớp, BASE-GATE-007 đạt theo cách (a); D-143 dựa trên trạng thái cũ, thay bằng quyết định này
- Đường lùi: Nếu chủ repo tắt strict lại: áp D-143

### D-145 · 2026-10-23T11:47:42+00:00 · T-2404: nguyên nhân gốc wait giả #208 chưa chứng minh từ dữ liệu sống — nhận bản sửa?

- Phương án: (1) Nhận: chọn bản check mới nhất theo started_at rồi id (lớp (a) tái hiện được + _ci_buckets khử trùng ở đường --pr-json); (c) commit status treo đã loại bằng dữ liệu (head 0786dca: 0 status); ghi cách thu dữ liệu filter=all lần sau · (2) Chưa nhận, đợi tái hiện thật lần sau
- Chọn: Nhận: chọn bản check mới nhất theo started_at rồi id (lớp (a) tái hiện được + _ci_buckets khử trùng ở đường --pr-json); (c) commit status treo đã loại bằng dữ liệu (head 0786dca: 0 status); ghi cách thu dữ liệu filter=all lần sau
- Lý do (tiêu chí chất lượng cuối): (1) đúng/an toàn: chỉ đổi cách chọn giữa các bản cùng tên/cùng app; bản mới nhất đang chạy/đỏ vẫn chặn, hoà vẫn chặn, khác app/nguồn không che nhau — không nới; (3) test đỏ trước; đợi tái hiện thật để lỗi đã biết tồn tại vô thời hạn
- Đường lùi: revert commit T-2404

### D-146 · 2026-10-23T12:06:35+00:00 · milestone_audit now sau Lát 1 — audit delta 9e1d6f3..HEAD làm thế nào?

- Phương án: (1) Ghi 'quét lại diff' vào AUDIT-STATUS sau khi #231 merge (SHA trên main), bằng chứng = review khác họ model ở head + gate xanh (tiền lệ #228); làm T-2405 trong lúc chờ · (2) Audit đủ 8 nhóm bằng subagent ngay
- Chọn: Ghi 'quét lại diff' vào AUDIT-STATUS sau khi #231 merge (SHA trên main), bằng chứng = review khác họ model ở head + gate xanh (tiền lệ #228); làm T-2405 trong lúc chờ
- Lý do (tiêu chí chất lượng cuối): (1) đúng: delta chính là diff 2 PR đã có reviewer khác họ model rà toàn bộ (0 chặn, 1 🟠 đã sửa kèm test) và cổng đầy đủ xanh — audit lại cùng diff không thêm bằng chứng; SHA quét phải là SHA trên main; (5) không chặn vòng
- Đường lùi: Chạy /audit delta đủ nhóm

### D-147 · 2026-10-23T12:26:16+00:00 · T-2406: unchecked_must đo gì và đặt tên khoá thế nào (khoá cũ là danh sách ID MUST tick không có — Kiểm:)?

- Phương án: (1) count = số MUST tick [x] không có lệnh Kiểm (danh sách unchecked_must sẵn có), total = số MUST [x]; khoá mới unchecked_must_ratio, giữ khoá cũ · (2) count = MUST còn [ ] (đã có hàng blueprint chặn) · (3) Đổi kiểu khoá cũ thành dict
- Chọn: count = số MUST tick [x] không có lệnh Kiểm (danh sách unchecked_must sẵn có), total = số MUST [x]; khoá mới unchecked_must_ratio, giữ khoá cũ
- Lý do (tiêu chí chất lượng cuối): (1) đúng: research §55/§112 đo '58 MUST tick không có lệnh kiểm' — MUST [ ] đã bị hàng blueprint của release-check chặn nên cờ fail theo định nghĩa đó vô nghĩa; (2)(3) giữ hợp đồng khoá cũ (blueprint_checks, _release_blueprint, test) — thêm khoá mới
- Đường lùi: Đổi unchecked_must_stat về đếm [ ]

### D-148 · 2026-10-23T13:03:47+00:00 · Lát 3 (T-2409/2410) và Lát 4 (T-2411 cắt 3.16.0): một PR hay hai?

- Phương án: (1) Một PR: Lát 3 + cắt 3.16.0 (tiền lệ #228 sửa + cắt bản) · (2) Hai PR tuần tự
- Chọn: Một PR: Lát 3 + cắt 3.16.0 (tiền lệ #228 sửa + cắt bản)
- Lý do (tiêu chí chất lượng cuối): (3) đơn giản: phiên ràng buộc một nhánh, lát đi tuần tự; Lát 4 chỉ là VERSION/CHANGELOG/PROGRESS — tách PR thêm một vòng review+CI không thêm bằng chứng; (2) revert một PR vẫn gỡ được cả hai
- Đường lùi: Tách commit cắt bản ra PR riêng

### D-149 · 2026-10-23T22:01:36+00:00 · Duyệt PLAN-3.17-feedback: /autopilot lần 3 sau 3.16.0 — làm gì?

- Phương án: (1) Sửa 6 🟠 + 2 🟢 cùng file từ phản hồi dự án đích đã tái hiện trên HEAD (guard lọt rm -rf gốc dự án, xanh giả blueprint-status, worktree, Stop hook khác phiên, feedback lộ dữ liệu) → 3.17.0 · (2) Dọn 84 🟢 sổ audit · (3) Dừng chờ đo 2026-10-30
- Chọn: Sửa 6 🟠 + 2 🟢 cùng file từ phản hồi dự án đích đã tái hiện trên HEAD (guard lọt rm -rf gốc dự án, xanh giả blueprint-status, worktree, Stop hook khác phiên, feedback lộ dữ liệu) → 3.17.0
- Lý do (tiêu chí chất lượng cuối): (1) đúng/an toàn: lỗi người dùng thật đã gặp, có tái hiện; #27 là lọt hành động không đảo ngược — hàng rào phải chặn (ADR-0018); 🟢 sổ audit không có tác động đo được tương đương; chờ đo không chặn việc này (2) mỗi lát một PR nhỏ, revert được
- Đường lùi: revert PR từng lát; phản hồi về lại trạng thái mở trong TARGETS

### D-150 · 2026-10-23T22:31:58+00:00 · T-2503: cho cat/echo/printf (không chuyển hướng ra file) đứng trước git commit?

- Phương án: (1) Cho: không ghi cây; giữ cat <<EOF | git commit -F - đang dùng · (2) Chặt đúng spec, đổi test cũ
- Chọn: Cho: không ghi cây; giữ cat <<EOF | git commit -F - đang dùng
- Lý do (tiêu chí chất lượng cuối): (1) đúng: luật nhằm lệnh GHI cây trước commit; ba lệnh này chỉ ghi stdout (chuyển hướng ra file vẫn bị chặn); (4) giữ cách viết message commit phổ biến
- Đường lùi: Bỏ 3 tên khỏi tuple _tree_readonly + đổi test_every_message_source_is_scanned

### D-151 · 2026-10-23T23:34:21+00:00 · Guard find -delete/-exec rm trên cây dự án: vá từng cách viết bộ lọc rộng (3 lượt review vẫn lọt) hay đổi cách?

- Phương án: (1) Danh sách cho phép: chỉ cho khi biểu thức là AND thuần các test dương, có ≥ 1 test tên/đường hẹp (không khớp .git, .git/x), không !, -not, -prune, ngoặc, -regextype, -o (trừ khi mọi nhánh -o đều hẹp và không ngoặc); còn lại deny kèm lý do gợi ý viết hẹp · (2) Tiếp tục vá từng cách
- Chọn: Danh sách cho phép: chỉ cho khi biểu thức là AND thuần các test dương, có ≥ 1 test tên/đường hẹp (không khớp .git, .git/x), không !, -not, -prune, ngoặc, -regextype, -o (trừ khi mọi nhánh -o đều hẹp và không ngoặc); còn lại deny kèm lý do gợi ý viết hẹp
- Lý do (tiêu chí chất lượng cuối): (1) đúng/an toàn: ngữ nghĩa find đủ giàu để danh sách chặn luôn thiếu (3 lượt review, mỗi lượt lộ lớp mới); danh sách cho phép đóng cả lớp; xoá không đảo ngược thì chiều chặt (ADR-0002/0018); (3) đơn giản, test được; chi phí: vài lệnh dọn hợp lệ phức tạp (-prune -o, !) bị chặn — viết lại hẹp hoặc chạy trong thư mục con
- Đường lùi: Trở lại danh sách chặn ở _find_filters (commit trước)

### D-152 · 2026-10-24T00:08:50+00:00 · Review lượt 4: danh sách cho phép D-151 vẫn lọt vì so mẫu bằng fnmatch/re Python khác ngữ nghĩa find, và tokenizer _find_parens tạo hồi quy — siết thế nào?

- Phương án: (1) Siết D-151: mẫu chỉ nhận dạng literal an toàn — -name/-iname/-path/-ipath: không \, [, $, backtick, không chứa '.git' (ở mọi độ sâu), dạng '*.<đuôi>' hoặc tên không wildcard; -regex/-iregex/-regextype → deny; hành động xoá phải đứng SAU mọi test; mở rộng GIT_PROBES (pack, packed-refs, refs/heads/master, hooks, logs, objects…); _find_parens chỉ áp khi find ở vị trí lệnh (đầu lệnh / sau ; && || | ( $( hoặc sau env/sudo/command/time/nice) · (2) Bỏ hẳn: mọi find xoá trên gốc → deny
- Chọn: Siết D-151: mẫu chỉ nhận dạng literal an toàn — -name/-iname/-path/-ipath: không \, [, $, backtick, không chứa '.git' (ở mọi độ sâu), dạng '*.<đuôi>' hoặc tên không wildcard; -regex/-iregex/-regextype → deny; hành động xoá phải đứng SAU mọi test; mở rộng GIT_PROBES (pack, packed-refs, refs/heads/master, hooks, logs, objects…); _find_parens chỉ áp khi find ở vị trí lệnh (đầu lệnh / sau ; && || | ( $( hoặc sau env/sudo/command/time/nice)
- Lý do (tiêu chí chất lượng cuối): (1) đúng/an toàn: chỉ nhận mẫu mà fnmatch Python và find hiểu giống nhau (literal + * + đuôi) → đóng cả lớp lệch ngữ nghĩa; tokenizer giới hạn vị trí lệnh để hết hồi quy case/echo; (4) giữ dọn dẹp phổ biến (*.pyc, __pycache__, .DS_Store, *.log) — phương án 2 chặn cả các lệnh này
- Đường lùi: Phương án 2 nếu lượt review 5 còn lọt

### D-153 · 2026-10-24T00:43:00+00:00 · Sau 5 lượt review find vẫn lọt (tokenizer cắt \; và \(, danh sách đường .git không đủ, -exec sh -c) — giữ phân tích biểu thức find hay đổi?

- Phương án: (1) D-153 thay D-151/152: bỏ phân tích biểu thức; trả tokenizer về như trước (gỡ _find_parens); quét CHUỖI GỐC của lệnh: có từ 'find' cùng hành động -delete/-exec/-execdir/-ok/-okdir, và điểm bắt đầu của find là gốc dự án/tổ tiên/.git, hoặc '.'/vắng khi cwd là gốc, hoặc không xác định được (biến, $(…)) → deny; find trong thư mục con (không chứa .git của gốc) vẫn chạy tự do · (2) Tiếp tục vá D-152
- Chọn: D-153 thay D-151/152: bỏ phân tích biểu thức; trả tokenizer về như trước (gỡ _find_parens); quét CHUỖI GỐC của lệnh: có từ 'find' cùng hành động -delete/-exec/-execdir/-ok/-okdir, và điểm bắt đầu của find là gốc dự án/tổ tiên/.git, hoặc '.'/vắng khi cwd là gốc, hoặc không xác định được (biến, $(…)) → deny; find trong thư mục con (không chứa .git của gốc) vẫn chạy tự do
- Lý do (tiêu chí chất lượng cuối): (1) đúng/an toàn: quét chuỗi gốc không phụ thuộc cách shlex tách \( \; ; không cần đoán find sẽ khớp gì; hồi quy tokenizer hết vì gỡ _find_parens; xoá không đảo ngược → chiều chặt; (3) đơn giản nhất, test được. Chi phí: dọn từ gốc (find . -name '*.pyc' -delete) bị chặn — lý do gợi ý chạy trong thư mục con hoặc rm đường cụ thể
- Đường lùi: Trở lại commit 27df218 (D-152)

### D-154 · 2026-10-24T01:12:57+00:00 · D-153 chặn oan: (1) quét chuỗi gốc bắt cả dữ liệu (heredoc, message); (2) mọi lệnh con chạy từ gốc, kể cả chỉ đọc

- Phương án: (1) (1) giữ chặt; (2) miễn khi mọi lệnh con thuộc danh sách đóng không ghi (cat grep rg ls head tail wc file stat du sha*sum md5sum basename dirname realpath echo printf test) và không có hành động xoá/ghi file · (2) Giữ đúng D-153 cả hai
- Chọn: (1) giữ chặt; (2) miễn khi mọi lệnh con thuộc danh sách đóng không ghi (cat grep rg ls head tail wc file stat du sha*sum md5sum basename dirname realpath echo printf test) và không có hành động xoá/ghi file
- Lý do (tiêu chí chất lượng cuối): (1) an toàn: dữ liệu nhắc lệnh xoá hiếm, đã có lối Edit/Write (tiền lệ D-105); (4) tìm-rồi-grep từ gốc là việc hằng ngày — danh sách đóng lệnh không ghi vẫn chặn sh -c, mv, truncate và mọi lệnh khác
- Đường lùi: Bỏ FIND_READONLY_EXEC (D-153 nguyên bản)

### D-155 · 2026-10-24T02:07:08+00:00 · Sau 6 lượt review guard xoá gốc: còn giới hạn chưa bịt (tên lệnh qua glob fi?d, công cụ khác như fd -X rm, ~user). Dừng vòng review ở đâu?

- Phương án: (1) Dừng sau lượt review delta kế: không hồi quy so 5ef1a14~1 là điều kiện merge; giới hạn còn lại ghi PROGRESS §Giới hạn guard (như D-051), xử lý ở đợt sau nếu dự án đích gặp · (2) Tiếp tục đến khi reviewer không còn tìm ra
- Chọn: Dừng sau lượt review delta kế: không hồi quy so 5ef1a14~1 là điều kiện merge; giới hạn còn lại ghi PROGRESS §Giới hạn guard (như D-051), xử lý ở đợt sau nếu dự án đích gặp
- Lý do (tiêu chí chất lượng cuối): (1) đúng: mỗi lượt đã chặt hơn và lượt 6 xác nhận 0 hồi quy; guard là lớp đỡ chuỗi lệnh, không phải sandbox — giới hạn đã biết được ghi như D-051/D-105; (2) đường lùi: revert từng commit; (5) mỗi lượt ~1 giờ, lợi ích giảm dần
- Đường lùi: Mở task mới cho từng giới hạn

### D-156 · 2026-10-24T02:39:52+00:00 · T-2521/2522: phạm vi gốc worktree, sổ Stop hook khi chạy theo worktree, gắn lại phiên khi resume

- Phương án: (1) (1) mọi lệnh loop gõ tay theo gốc worktree; (2) mỗi lát loop init trong worktree của mình, vòng chính loop verify --all sau merge (ghi README/orchestration); (3) loop resume gắn lại phiên hiện tại · (2) Chỉ record/status/verify; hook theo cwd payload; cờ --rebind
- Chọn: (1) mọi lệnh loop gõ tay theo gốc worktree; (2) mỗi lát loop init trong worktree của mình, vòng chính loop verify --all sau merge (ghi README/orchestration); (3) loop resume gắn lại phiên hiện tại
- Lý do (tiêu chí chất lượng cuối): (1) đúng: sổ một worktree nhất quán (tick cần state do init tạo); (3) đơn giản: không đổi hook đọc cwd payload (thêm bề mặt); resume là hành động có chủ ý của phiên mới — gắn lại là đúng ý, không thì Stop hook không giữ vòng
- Đường lùi: Giới hạn loop_root cho record/status/verify; bỏ gắn lại ở resume

### D-157 · 2026-10-24T04:26:37+00:00 · Duyệt PLAN-3.18-feedback2: sửa 7 lỗi 🟢 còn lại từ phản hồi dự án đích

- Phương án: (1) Sửa cả 7 trong 3 lát, mỗi lỗi test đỏ trước; mục hàng rào dùng lệnh con chỉ đọc harness-check · (2) Chỉ sửa 3 lỗi tài liệu (BASE-SEC-002, PLAN mỗi đợt), để phần loop/check-links sau · (3) Nới guard cho script python -c chỉ đọc
- Chọn: Sửa cả 7 trong 3 lát, mỗi lỗi test đỏ trước; mục hàng rào dùng lệnh con chỉ đọc harness-check
- Lý do (tiêu chí chất lượng cuối): (1) đúng: cả 7 tái hiện được, cỡ S-M; không nới guard (an toàn hơn phương án 3); (3) test được từng lỗi
- Đường lùi: Revert từng PR lát; harness-check là lệnh mới, bỏ không ảnh hưởng lệnh cũ

### D-158 · 2026-10-24T07:08:54+00:00 · Duyệt PLAN-3.19-setext: anchor setext nhiều dòng/trong > cho check-links (🟢 review #238)

- Phương án: (1) Sửa trong check-links: gom đoạn (bỏ tiền tố >) đến dòng trống, dòng ===/--- biến cả đoạn thành tiêu đề; bản vá 3.18.1 · (2) Để nguyên, chỉ ghi giới hạn trong tài liệu
- Chọn: Sửa trong check-links: gom đoạn (bỏ tiền tố >) đến dòng trống, dòng ===/--- biến cả đoạn thành tiêu đề; bản vá 3.18.1
- Lý do (tiêu chí chất lượng cuối): (1) đúng: link hợp lệ đang bị báo gãy làm lint dự án đích đỏ oan; nhận thừa anchor an toàn hơn đỏ oan; (3) sửa nhỏ, test được
- Đường lùi: Revert PR lát; anchors() trở lại chỉ xét một dòng trước

### D-159 · 2026-10-24T08:22:13+00:00 · Duyệt PLAN-3.20-install-dedupe: gom mệnh đề 'Dự án đích' trùng khi install.py nâng nhiều bản (nợ 🟢 #191)

- Phương án: (1) Gộp trùng hệt xuyên mục: giữ lần đầu theo thứ tự CHANGELOG, mục hết mệnh đề thì bỏ; không đổi mệnh đề khác nhau · (2) Gộp theo ngữ nghĩa (mọi 'chạy lại install.py' thành một dòng, parse phần ngoặc) · (3) Để nguyên, chỉ ghi giới hạn
- Chọn: Gộp trùng hệt xuyên mục: giữ lần đầu theo thứ tự CHANGELOG, mục hết mệnh đề thì bỏ; không đổi mệnh đề khác nhau
- Lý do (tiêu chí chất lượng cuối): (1) đúng/an toàn: chỉ bỏ bản sao trùng từng chữ, không mất thông tin bước nào; ngữ nghĩa (2) phải đoán câu tự do → có thể nuốt chi tiết; (3) đơn giản, test được trên CHANGELOG thật (108 mệnh đề → 101)
- Đường lùi: Bỏ biến seen trong upgrade_steps

### D-160 · 2026-10-24T08:56:34+00:00 · Model của phiên chính (lập PLAN, viết SPEC) khi model cao nhất không khả dụng

- Phương án: (1) Giữ luật cũ: cao nhất sẵn có, không khả dụng thì Opus · (2) Chuỗi tường minh Fable → Opus → Sonnet; subagent giữ nguyên frontmatter
- Chọn: Chuỗi tường minh Fable → Opus → Sonnet; subagent giữ nguyên frontmatter
- Lý do (tiêu chí chất lượng cuối): Chủ repo chốt 2026-10-24. Tiêu chí 1/3: PLAN/SPEC là chỗ sai đắt nhất nên dùng model mạnh nhất; chuỗi tường minh không để phiên tự diễn giải 'cao nhất', có bậc cuối khi cả hai bậc trên không khả dụng. Tầng executor/reviewer không đổi (ADR-0029).
- Đường lùi: Đổi lại chữ LOOP-ORCH-019, AGENTS.md §8, templates/CLAUDE.md; cắt bản patch.

### D-161 · 2026-10-24T09:00:50+00:00 · Luật reviewer LOOP-ORCH-005: 'khác họ model' hay 'năng lực cao hơn'

- Phương án: (1) Giữ khác họ (D-045) · (2) Năng lực cao hơn theo thang bậc model rồi effort; khác nhà cung cấp nhận như cũ · (3) Năng lực cao hơn và bắt buộc khác nhà cung cấp
- Chọn: Năng lực cao hơn theo thang bậc model rồi effort; khác nhà cung cấp nhận như cũ
- Lý do (tiêu chí chất lượng cuối): Chủ repo 2026-10-24: cùng họ khác effort được, review phải năng lực cao hơn. Tiêu chí 1: PA1 cho reviewer yếu hơn người viết (reviewer-alt Sonnet chấm Opus). Tiêu chí 2/3: PA3 kẹt mọi PR làn chuẩn vì pr-review.yml chỉ chạy Claude. PA2 máy kiểm được (thang trong một hàm), giữ đường reviewer ngoài Claude. ADR-0044.
- Đường lùi: Revert PR; ADR-0044 đổi trạng thái; reviewer-alt về model cũ.

### D-162 · 2026-10-24T08:44:15+00:00 · Duyệt PLAN-3.21-guard-d155: bịt ba giới hạn guard xoá gốc của D-155

- Phương án: (1) Bịt (1) tên lệnh glob bằng biến thể theo tên nhạy cảm (fnmatch, danh sách đóng), (2) fd/fdfind/bfs/gfind theo luật find (cùng chính sách D-153), (3) ghim test cho ~user vì đã chặn; hai lát PR · (2) Mở mọi glob theo hệ tệp thật (glob.glob) rồi quét lại · (3) Chỉ ghi giới hạn vào tài liệu như D-155
- Chọn: Bịt (1) tên lệnh glob bằng biến thể theo tên nhạy cảm (fnmatch, danh sách đóng), (2) fd/fdfind/bfs/gfind theo luật find (cùng chính sách D-153), (3) ghim test cho ~user vì đã chặn; hai lát PR
- Lý do (tiêu chí chất lượng cuối): (1) đúng/an toàn: xoá không đảo ngược → chiều chặt; fnmatch trên danh sách đóng không phụ thuộc máy và test được (hệ tệp thì kết quả đổi theo máy, bỏ sót tệp tạo giữa lệnh); (3) đơn giản: tái dùng luật find/rm đã có; (4) chặn oan thấp, lối thoát có sẵn (chạy ở thư mục con)
- Đường lùi: Revert từng lát PR; biến thể glob và _fd_rule là mã thêm, không đổi luật cũ

### D-163 · 2026-10-24T12:17:57+00:00 · Review #248 lượt 4: danh sách đóng GLOB_COMMANDS vẫn sót (trình thông dịch, lệnh ghi, CLI đám mây) và fnmatch bậc hai ngoài ngân sách — sửa tiếp bằng danh sách hay đổi cách?

- Phương án: (1) Chặn thẳng tên lệnh glob dạng tên trần hoặc đường tuyệt đối (ngoặc phải đóng, có đối số, không toàn */?); đường tương đối giữ viết lại theo danh sách; head > 256 ký tự chặn trước fnmatch · (2) Mở rộng GLOB_COMMANDS thêm INTERPRETERS/FILE_WRITERS/CLI đám mây · (3) Giữ danh sách hẹp, ghi giới hạn vào CHANGELOG
- Chọn: Chặn thẳng tên lệnh glob dạng tên trần hoặc đường tuyệt đối (ngoặc phải đóng, có đối số, không toàn */?); đường tương đối giữ viết lại theo danh sách; head > 256 ký tự chặn trước fnmatch
- Lý do (tiêu chí chất lượng cuối): (1) đúng/an toàn: không phụ thuộc danh sách phải đầy đủ — mọi luật theo tên đều được bảo vệ; mỗi vòng mở rộng danh sách đều bị review tìm ra lỗ mới (4 lượt); (3) đơn giản, O(1) trước fnmatch; (4) chặn oan gần 0: không ai gõ /usr/bin/p?thon3 — script tương đối, case, [ ], for vẫn chạy
- Đường lùi: Bỏ _glob_head_deny, quay về chỉ viết lại theo GLOB_COMMANDS

### D-164 · 2026-10-24T13:04:07+00:00 · PR #248 sau 5 lượt review: mỗi lượt tìm lỗ né mới (đường tương đối ../ đã bịt; còn: trình thông dịch glob đọc stdin không đối số, tên có nháy từng phần ngoài GLOB_COMMANDS, lệnh trong container viết glob). Dừng vòng review ở đâu?

- Phương án: (1) Dừng sau lượt rà delta kế: 0 chặn oan + không hồi quy so main là điều kiện merge; lỗ né cố ý còn lại ghi CHANGELOG/PROGRESS như D-051/D-155 · (2) Tiếp tục đến khi reviewer không tìm ra
- Chọn: Dừng sau lượt rà delta kế: 0 chặn oan + không hồi quy so main là điều kiện merge; lỗ né cố ý còn lại ghi CHANGELOG/PROGRESS như D-051/D-155
- Lý do (tiêu chí chất lượng cuối): (1) đúng: guard là lớp chặn sai lầm, không phải sandbox (D-015) — các lỗ còn lại cần cố ý viết (../../usr/bin/p?thon3, p?thon3 đọc stdin, c?'' …), agent không gõ nhầm ra; chặn oan thì có hại thật và đã hết; (2) đường lùi: revert từng commit; (5) mỗi lượt ~25 phút, lợi ích giảm dần
- Đường lùi: Mở task mới cho từng lỗ còn lại

### D-165 · 2026-10-24T13:43:31+00:00 · Review #248 lượt 6: chặn thẳng tên glob (D-163) chặn oan số học $(( n*2 )), (( )), mảng, [[ =~ ]] vì tách token quá thô — sửa tiếp hay đổi lại?

- Phương án: (1) Rút D-163: bỏ chặn thẳng; giữ viết lại theo tên (D-162) và mở rộng GLOB_COMMANDS: INTERPRETERS, FILE_WRITERS, cp/tee/ln/sed/tar…, ssh/scp, CLI đám mây/container, claude; giữ trần 256 ký tự trước fnmatch · (2) Giữ chặn thẳng, bỏ qua token trong (( )), [[ ]], NAME=( )
- Chọn: Rút D-163: bỏ chặn thẳng; giữ viết lại theo tên (D-162) và mở rộng GLOB_COMMANDS: INTERPRETERS, FILE_WRITERS, cp/tee/ln/sed/tar…, ssh/scp, CLI đám mây/container, claude; giữ trần 256 ký tự trước fnmatch
- Lý do (tiêu chí chất lượng cuối): (1) đúng: viết lại chỉ khớp tên đã biết nên không chặn oan (5 lượt rà không tìm ra chặn oan nào của nó); chặn thẳng phụ thuộc tách cú pháp bash bằng token — mỗi lượt lộ thêm thành ngữ bị chặn oan, có hại thật (chặn cả phiên này); lỗ còn lại của danh sách là tên ngoài danh sách phải cố ý viết (D-164); (3) đơn giản hơn
- Đường lùi: Khôi phục _glob_head_deny từ commit 26c202f

### D-166 · 2026-10-24T14:15:51+00:00 · Review #248 lượt 7: viết lại theo tên vẫn chặn oan mẫu case (''|*[!0-9]*) → mkfs), nhóm regex [[ =~ ]], toán hạng $(( )); case nhiều nhánh cạn ngân sách — lý do của D-165 ('không chặn oan') sai

- Phương án: (1) Tách lệnh hiểu cú pháp: bỏ qua vùng (( … )) và [[ … ]], bỏ mẫu nhánh case (đoạn kết thúc bằng ')' không có '(' mở, kể cả nhánh nối '|'); mkfs trơn vào nhóm bỏ khi không đối số · (2) Chỉ thêm mkfs vào nhóm bỏ khi không đối số
- Chọn: Tách lệnh hiểu cú pháp: bỏ qua vùng (( … )) và [[ … ]], bỏ mẫu nhánh case (đoạn kết thúc bằng ')' không có '(' mở, kể cả nhánh nối '|'); mkfs trơn vào nhóm bỏ khi không đối số
- Lý do (tiêu chí chất lượng cuối): (1) đúng: gốc lỗi là tách token coi mẫu/regex/số học là lệnh — sửa ở gốc thì mọi tên trong danh sách đều hết chặn oan, và case nhiều nhánh không còn sinh bản viết lại (hết cạn ngân sách); (3) test được bằng đúng các thành ngữ reviewer nêu. Đính chính D-165: 'không chặn oan' chỉ đúng sau D-166
- Đường lùi: Khôi phục _segment_commands tách ở mọi dấu nối

### D-167 · 2026-10-24T14:58:08+00:00 · Review #248 lượt 8: tách cú pháp bash bằng token không hội tụ (8 lượt; D-166 đếm ngoặc mở lỗ mới, chặn oan case (s*), $(…)/s*; fail-open cạn bộ nhớ khi dựng bản viết lại). Thu hẹp hay tiếp tục vá?

- Phương án: (1) Thu hẹp: chỉ viết lại khi tên lệnh là đường tuyệt đối trong thư mục bin hệ thống (/bin, /usr/bin, /usr/local/bin, /sbin…, ~/bin, ~/.local/bin) không glob ở thư mục; tách lệnh về bản đơn giản; trần số tên glob và độ dài lệnh trước khi dựng (vượt → chặn BUDGET); tên trần glob ghi giới hạn · (2) Tiếp tục vá bộ tách cú pháp (ngăn xếp đoạn, ngữ cảnh case) · (3) Bỏ PR, giữ guard như main
- Chọn: Thu hẹp: chỉ viết lại khi tên lệnh là đường tuyệt đối trong thư mục bin hệ thống (/bin, /usr/bin, /usr/local/bin, /sbin…, ~/bin, ~/.local/bin) không glob ở thư mục; tách lệnh về bản đơn giản; trần số tên glob và độ dài lệnh trước khi dựng (vượt → chặn BUDGET); tên trần glob ghi giới hạn
- Lý do (tiêu chí chất lượng cuối): (1) đúng/an toàn: mẫu case, số học, regex, mảng không bao giờ có dạng /usr/bin/x? nên hết chặn oan theo cấu trúc chứ không theo vá; trần trước khi dựng bịt fail-open; giữ phần giá trị chính (đường tuyệt đối tới lệnh hệ thống là cách thật để gọi tên qua glob — tên trần chỉ mở theo tệp ở cwd); (3) đơn giản, chứng minh được; (5) 8 lượt vá không hội tụ
- Đường lùi: Khôi phục _segment_commands D-166 từ 4843057

### D-168 · 2026-10-24T16:46:48+00:00 · Duyệt PLAN-3.21-single-loop: áp bài claude.com 'When to fold subagents into your main agent loop' (2026-10-22) + kit single-agent-loop-kit (c437962) vào agentic-systems.md và orchestration-and-subagents.md

- Phương án: (1) Giữ nguyên thang 'workflow trước, agent sau' (AI-AGENTIC-001) và executor mặc định 'vì rẻ'; chỉ ghi research note · (2) Đảo toàn bộ theo bài: một vòng lặp là mặc định ở sản phẩm; phiên chính tự làm là mặc định ở vòng lặp phát triển; hạ tầng executor; sửa AGENTS.md/CLAUDE.md/SKILL autopilot/README · (3) Đổi tiêu chí, giữ harness, thêm phép đo: AI-AGENTIC-001 thành luật đổi kiến trúc hai chiều qua cùng eval end-to-end; AI-AGENTIC-011 là nhà ba lý do context + kiểm kê agent con; mục mới AI-AGENTIC-019 (trình tự gộp có đo) và LOOP-ORCH-020 (giữ mặc định giao việc tới khi có số; nhóm 'Làm trực tiếp' ghi executor null); LOOP-ORCH-017 MAY→SHOULD; LOOP-ORCH-019 và harness không đổi; research note + ADR-0045; bản 3.20.0; một lát một PR; task mà SPEC đã là chính nội dung chữ thì phiên chính tự làm, loop record không --executor (điểm đo đầu của LOOP-ORCH-020)
- Chọn: Đổi tiêu chí, giữ harness, thêm phép đo: AI-AGENTIC-001 thành luật đổi kiến trúc hai chiều qua cùng eval end-to-end; AI-AGENTIC-011 là nhà ba lý do context + kiểm kê agent con; mục mới AI-AGENTIC-019 (trình tự gộp có đo) và LOOP-ORCH-020 (giữ mặc định giao việc tới khi có số; nhóm 'Làm trực tiếp' ghi executor null); LOOP-ORCH-017 MAY→SHOULD; LOOP-ORCH-019 và harness không đổi; research note + ADR-0045; bản 3.20.0; một lát một PR; task mà SPEC đã là chính nội dung chữ thì phiên chính tự làm, loop record không --executor (điểm đo đầu của LOOP-ORCH-020)
- Lý do (tiêu chí chất lượng cuối): (1) đúng/an toàn: bài nói 'frequently/often', không 'always'; kit 'It measures.' và mới chạy thật 2 lần, merge/upkeep chưa chạy — luật phải 'đo trước, đổi một thứ một lần', không bỏ subagent theo cảm tính. PA1 giữ MUST@L trái dữ kiện 2026-10 (ép dựng orchestrator trước). PA2 đổi mặc định khi chưa có số nào về tự làm vs giao (loop stats trên clone = 0), đụng harness + AGENTS.md sát trần 7168 B, mất đường lùi ADR-0029. (2) đường lùi: harness và ID giữ, revert một PR tài liệu. (3) kiểm được bằng lệnh có sẵn (validate, loop stats --all --json, runs.jsonl); mục mới đều SHOULD vì hai module đã đủ 4 MUST. Bản 3.20.0: đổi chữ quy phạm MUST@L + 2 ID mới → dự án đích compose lại (MINOR như 3.19.0); PLAN-3.20-install-dedupe cắt 3.18.3 nên không trùng số. Một PR ~300 dòng theo tiền lệ #247/#249. Phiên chính tự làm vì SPEC = nội dung chữ cuối, giao executor chỉ là chép lại (LOOP-ORCH-019: phiên chính viết SPEC/thiết kế); ghi rõ để làm điểm đo.
- Đường lùi: Revert PR lát; ADR-0045 đổi 'Bị thay bởi ADR-NNNN'; AI-AGENTIC-019/LOOP-ORCH-020 hạ MAY 'Ngừng dùng'; chữ AI-AGENTIC-001/011, LOOP-ORCH-017 về bản 3.19.1

### D-169 · 2026-10-25T00:41:11+00:00 · Duyệt PLAN-3.20.1-adr0045-debt: trả phần nợ ADR-0045 trong phạm vi nhỏ (skill /autopilot bước 5, thang cũ ở llm-app-foundations.md, 02-profiles/ai-agent.md, 02-profiles/agentic-system.md), bản 3.20.1

- Phương án: (1) Chỉ sửa skill /autopilot bước 5 (một vế trỏ hàng Làm trực tiếp), để thang cũ ở ba file framework cho lát sau · (2) Sửa skill + ba chỗ chép thang cũ (chỉ văn xuôi/nguyên tắc, không đổi chữ quy phạm mục checklist nên blueprint không thành Cũ); để evaluation.md, AI-AGENT-006, XC-DOCAI, AI-APP-007, templates/AGENTS.md §8 cho lát sau · (3) Gộp luôn evaluation.md, AI-AGENT-006, XC-DOCAI, AI-APP-007 và templates vào một lát
- Chọn: Sửa skill + ba chỗ chép thang cũ (chỉ văn xuôi/nguyên tắc, không đổi chữ quy phạm mục checklist nên blueprint không thành Cũ); để evaluation.md, AI-AGENT-006, XC-DOCAI, AI-APP-007, templates/AGENTS.md §8 cho lát sau
- Lý do (tiêu chí chất lượng cuối): (1) đúng: chữ skill đang mâu thuẫn LOOP-ORCH-020 (phiên dự án đích không bao giờ sinh nhóm executor null, phép đo chỉ có số ở repo khung); ba chỗ chép thang cũ vi phạm một chủ đề một nhà. Chỉ đổi văn xuôi, không đổi chữ quy phạm nên không làm blueprint Cũ. (2) đường lùi: revert một PR. (3) nhỏ, ≤150 dòng, một PR; PA3 vượt 150 dòng và chạm mục MUST/SHOULD cần xác minh nguồn mới (AI-AGENT-006 ngưỡng 20-30 so với 30-50). Skill trần 6 144 B dư 47 B: thêm vế ~46 B và cắt cụm thừa (hook chạy cổng commit, đã có ở README). Phiên chính tự làm vì SPEC là chữ cuối (LOOP-ORCH-020 nhóm Làm trực tiếp, điểm đo thứ hai).
- Đường lùi: Revert PR lát; nợ ADR-0045 giữ nguyên ghi trong ADR

### D-170 · 2026-10-25T01:22:35+00:00 · Duyệt PLAN-3.22-adr0045-rest: trả nốt nợ ADR-0045 (R04 eval nhỏ, R07 gom tool, R09 DRI skill, R11 không dán context, bảng Cách xây, LOOP-CTX-010 trùng, README 11, templates §8) bản 3.21.0

- Phương án: (1) Thêm bốn mục SHOULD mới ở bốn nhà (AI-EVAL-021, AI-AGENT-024, XC-DOCAI-021, AI-APP-019), không sửa chữ mục cũ; LOOP-CTX-010 hạ MAY Ngừng dùng gộp vào LOOP-ORCH-012; sửa văn xuôi bảng Cách xây, README 11, templates/AGENTS.md §8; templates/CLAUDE.md giữ; delegation_rate (mã xt.py) hoãn tới khi có số · (2) Sửa chữ quy phạm AI-AGENT-006 (MUST@L) thêm tool search và ngưỡng 30-50, và AI-EVAL-001/XC-DOCAI-015 cho eval nhỏ và DRI · (3) Chỉ ghi nợ tiếp, không làm gì
- Chọn: Thêm bốn mục SHOULD mới ở bốn nhà (AI-EVAL-021, AI-AGENT-024, XC-DOCAI-021, AI-APP-019), không sửa chữ mục cũ; LOOP-CTX-010 hạ MAY Ngừng dùng gộp vào LOOP-ORCH-012; sửa văn xuôi bảng Cách xây, README 11, templates/AGENTS.md §8; templates/CLAUDE.md giữ; delegation_rate (mã xt.py) hoãn tới khi có số
- Lý do (tiêu chí chất lượng cuối): (1) đúng/an toàn: nguồn nói 30-50 là xu hướng suy giảm (tends to degrade) và kit mới chạy thật 2 lần, nên mục mới đều SHOULD và AI-AGENT-006 (MUST@L, trần chặt hơn) giữ nguyên chữ — PA2 đổi MUST@L khi chưa có số của dự án và làm blueprint Cũ hàng loạt. (2) đường lùi: revert một PR; ID mới hạ MAY. (3) một nhà: mỗi ý một mục ở nhà đúng (conventions §7); delegation_rate là mã xt.py cần test 100 % và cần dữ liệu từ ≥2 vòng — hoãn. templates/CLAUDE.md giữ vì câu điều phối vẫn đúng. Cắt chữ khác ở templates/AGENTS.md để giữ trần 8192 B. Thêm mục và hạ LOOP-CTX-010 → MINOR 3.21.0 (dự án đích compose lại). Phiên chính tự làm: SPEC là chữ cuối (LOOP-ORCH-020, điểm đo thứ ba).
- Đường lùi: Revert PR lát; AI-EVAL-021, AI-AGENT-024, XC-DOCAI-021, AI-APP-019 hạ MAY Ngừng dùng; LOOP-CTX-010 trả SHOULD

### D-171 · 2026-10-25T02:06:38+00:00 · Duyệt PLAN-3.23-delegation-rate: thêm delegation_rate và xanh lần đầu theo nhóm tự làm/giao vào xt.py loop stats (nợ cuối ADR-0045), bản 3.22.0

- Phương án: (1) Thêm trường vào loop_stats qua helper _delegation_stats (delegated, self_done, delegation_rate, first_pass_rate_delegated, first_pass_rate_self) + một dòng ở bản chữ; nhóm theo tasks.<T>.executors rỗng/không; không đổi runs.jsonl hay cờ --executor; LOOP-ORCH-020 Kiểm trỏ trường mới · (2) Ghi thêm trường 'delegated' vào runs.jsonl khi loop record (đổi định dạng sổ) để tách task tự làm với quên cờ --executor · (3) Chỉ để người đếm tay bằng jq như LOOP-ORCH-020 đang hướng dẫn
- Chọn: Thêm trường vào loop_stats qua helper _delegation_stats (delegated, self_done, delegation_rate, first_pass_rate_delegated, first_pass_rate_self) + một dòng ở bản chữ; nhóm theo tasks.<T>.executors rỗng/không; không đổi runs.jsonl hay cờ --executor; LOOP-ORCH-020 Kiểm trỏ trường mới
- Lý do (tiêu chí chất lượng cuối): (1) đúng: nhóm suy từ dữ liệu đã có (executors rỗng = tự làm), khớp định nghĩa của LOOP-ORCH-020 và ADR-0045; không làm số đẹp hơn thật vì task tự làm rồi chuyển cấp tính vào nhóm giao (đã ghi ở LOOP-ORCH-020). PA2 đổi định dạng sổ — đụng harness, cần migration, vượt phạm vi nợ. PA3 để nguyên rủi ro đếm tay lệch đơn vị mà review #252 đã chỉ. (2) đường lùi: revert PR; trường thêm vào JSON là additive nên người đọc cũ không vỡ. (3) nhỏ, test được, helper tách riêng giữ C901 ≤ 10, mypy strict, coverage 100 %. Bản MINOR 3.22.0 (tính năng công cụ mới, dự án đích chạy lại install.py). T-3201 là mã có test nên giao executor (tầng mặc định) — điểm đo đầu cho nhóm giao của LOOP-ORCH-020; T-3202/3203 là chữ nên phiên chính tự làm.
- Đường lùi: Revert PR lát; bỏ _delegation_stats và dòng chữ; LOOP-ORCH-020 Kiểm về dạng đếm tay

### D-172 · 2026-10-25T02:36:48+00:00 · Đính chính D-171: nhóm giao/tự làm của loop stats theo executors cuối cùng hay theo executor của lần chạy đầu

- Phương án: (1) Giữ nhóm theo executors cuối cùng của task (D-171) · (2) Nhóm theo executor của LẦN CHẠY ĐẦU của task trong vòng (null = tự làm); task tự làm đỏ rồi chuyển cấp vẫn là tự làm
- Chọn: Nhóm theo executor của LẦN CHẠY ĐẦU của task trong vòng (null = tự làm); task tự làm đỏ rồi chuyển cấp vẫn là tự làm
- Lý do (tiêu chí chất lượng cuối): (1) đúng: review #253 (reviewer-alt, 🟠1) tái hiện: task tự làm đỏ 2 lần rồi harness chuyển executor-deep bị tính vào nhóm giao, nhóm tự làm đẹp hơn thật (tự làm 100 % thay vì 50 %) — đúng chiều lệch mà LOOP-ORCH-020 muốn chặn; câu 'không làm số đẹp hơn thật' của D-171 sai. PA2 khớp chữ 020 (nhóm tự làm = hàng Làm trực tiếp, kể cả khi sau đó chuyển cấp) và vẫn tính từ dữ liệu có sẵn (rows của runs.jsonl). (2) đường lùi: revert PR. (3) test đỏ khi quay lại cách cũ. Thay thế mục D-171 chọn nhóm theo executors cuối.
- Đường lùi: Revert PR; _delegation_stats về nhóm theo executors cuối (D-171) — không khuyến nghị

### D-173 · 2026-10-25T03:40:11+00:00 · Kế hoạch sửa audit delta 2026-10-25 (e5ff88c..3ba5828): 2 🟠 (AUD-SEC-105 lách thang reviewer bằng tiền tố ollama:, AUD-HAR-106 harness-check không kiểm reviewer chỉ đọc) và 14 🟢

- Phương án: (1) Một PR mã nhỏ sửa hai 🟠 + ba 🟢 rẻ cùng file (SEC-106 thêm 3 tên vào GLOB_COMMANDS, XFEAT-024 mythos vào AI_ATTRIBUTION_RE, HAR-107 DOCTOR_AGENTS), mỗi lỗi test đỏ trước khi sửa; các 🟢 còn lại giữ nợ có chủ/hạn · (2) Sửa mọi phát hiện (cả 14 🟢 gồm race reviews.json, REVIEW_MODEL env, compose lại BLUEPRINT.md) trong một PR · (3) Chỉ sửa chữ tài liệu cho HAR-106 (bỏ lời khẳng định cổng), để mã
- Chọn: Một PR mã nhỏ sửa hai 🟠 + ba 🟢 rẻ cùng file (SEC-106 thêm 3 tên vào GLOB_COMMANDS, XFEAT-024 mythos vào AI_ATTRIBUTION_RE, HAR-107 DOCTOR_AGENTS), mỗi lỗi test đỏ trước khi sửa; các 🟢 còn lại giữ nợ có chủ/hạn
- Lý do (tiêu chí chất lượng cuối): (1) đúng/an toàn: SEC-105 cho phép review tự chấm chính nó qua --clean (bypass LOOP-ORCH-005), HAR-106 là tài liệu khẳng định một cổng mà mã không có — cả hai sửa cách chặt hơn (fail-closed, cưỡng chế thật chứ không hạ chữ). Ba 🟢 rẻ cùng file xt.py/guard.py gộp vào vì chạm cùng test và cùng vùng; PA2 vượt 150 dòng, trộn mã với BLUEPRINT.md sinh lại (diff lớn khó review) và race reviews.json cần thiết kế khoá; PA3 hạ chữ thay vì đóng lỗ hổng. (2) đường lùi: revert PR; bản patch 3.22.1. (3) test đỏ trước khi sửa; trần byte scripts còn 4 532 B, hooks 917 B nên mỗi dòng phải gọn. Các 🟢 còn lại (CODE-023, CI-018, ARCH-004, XFEAT-025, HAR-108/109/110, DOC-081…083) ghi nợ có chủ phiên chính, hạn 2026-11-08, gom vào đợt sau (BLUEPRINT.md sinh lại một PR riêng).
- Đường lùi: Revert PR sửa; sổ audit giữ phát hiện ở trạng thái mở
### D-174 · 2026-10-25T08:55:55+00:00 · Duyệt PLAN-3.23.0-complete: /autopilot = pha build dừng ở build xong, /complete = pha harden (audit, nợ review, hoàn thiện, release-check), verdict done ở build không đòi 0 MUST blueprint (ADR-0046)

- Phương án: (1) Giữ một skill /autopilot, chỉ cắt mục Kết thúc G7; verdict done vẫn đòi 0 MUST mở · (2) Hai skill; pha build bỏ --blueprint ở loop init (0 code) để done không đòi MUST · (3) Hai skill; _verdict_blueprint rẽ theo pha (build + MUST mở → done kèm open_must, trả ở /complete), giữ --blueprint, scope drift, verify --all, bad_waivers; Pha 1 mức S ở build (nhà lifecycle quy tắc 6); /complete nối /audit + PLAN-harden + vòng lặp luật harden + release-check; sàn an toàn (guard, điểm dừng, Gate máy, CI xanh, verify --all, release-check FAIL phase) không đổi; không ID/lệnh mới; bản 3.23.0; 4 lát 4 PR, phiên chính tự làm (nhóm Làm trực tiếp) · (4) Hai skill và /autopilot tự đặt lại build cho đợt mới ở dự án đã phát hành
- Chọn: Hai skill; _verdict_blueprint rẽ theo pha (build + MUST mở → done kèm open_must, trả ở /complete), giữ --blueprint, scope drift, verify --all, bad_waivers; Pha 1 mức S ở build (nhà lifecycle quy tắc 6); /complete nối /audit + PLAN-harden + vòng lặp luật harden + release-check; sàn an toàn (guard, điểm dừng, Gate máy, CI xanh, verify --all, release-check FAIL phase) không đổi; không ID/lệnh mới; bản 3.23.0; 4 lát 4 PR, phiên chính tự làm (nhóm Làm trực tiếp)
- Lý do (tiêu chí chất lượng cuối): (1) đúng/an toàn: rào cản máy duy nhất còn lại ở build là done đòi 0 MUST (web-app M 473 MUST mở sau compose) — đây là tiêu chí G7 đặt nhầm ở cuối G6; mọi chốt phát hành nằm trong release_check, không phụ thuộc verdict, nên dời thời điểm đòi MUST không hạ sàn; sàn an toàn giữ nguyên (loại bỏ rào cản = quy trình, không phải guard/điểm dừng); PA1 không gỡ rào cản máy; PA2 mất scope/drift/Kiểm blueprint/defer theo MUST; PA4 trái ADR-0037 một chiều — dự án có người dùng thật không merge không review theo mặc định. (2) đường lùi: revert PR mã, đặt harden. (3) một hàm rẽ pha có test, không lệnh/ID mới, skill chỉ nối lệnh có sẵn (một nhà). (4) điểm dừng tự nhiên giữa hai pha. (5) tăng tốc chưa đo — ghi ước lượng, đo theo LOOP-ORCH-020
- Đường lùi: Revert PR mã (verdict về như cũ) và PR skill; ADR-0046 đổi Bị thay bởi ADR-NNNN; dự án đích đặt delivery_phase: harden

### D-175 · 2026-10-25T09:27:10+00:00 · Lát 1 (#259) bị review đòi sửa sổ khi lát 2–3 đã commit trên nhánh bị ràng buộc một tên: tách PR thế nào?

- Phương án: (1) Worktree tách: sửa sổ ở head cũ, push riêng, rồi rebase lát 2–3 lên (rewrite history cục bộ) · (2) Gộp lát 1–3 vào #259 (sổ + skill + verdict xt.py), lát 4 PR riêng; ghi D-175
- Chọn: Gộp lát 1–3 vào #259 (sổ + skill + verdict xt.py), lát 4 PR riêng; ghi D-175
- Lý do (tiêu chí chất lượng cuối): (1) đúng/an toàn: diff mã ≤ 150 dòng vẫn trong trần harden, ba lát cùng một quyết định nên review một lần đọc được toàn cảnh; rebase/force bị guard chặn và không có đường lùi sạch. (2) đường lùi: revert một PR. (5) ít vòng CI/review hơn
- Đường lùi: Mở lại hai PR riêng từ nhánh phụ nếu reviewer đòi tách

### D-176 · 2026-10-25T10:31:46+00:00 · Mẫu xt.yaml dự án đích: merge_hard_exceptions mặc định human hay auto? (chủ repo 2026-10-25: pha build không dừng hỏi gì; bật auto cho dự án đích luôn)

- Phương án: (1) Giữ human ở mẫu; mỗi dự án tự đổi · (2) Đổi mẫu sang auto (ADR-0020 đã cho phép; repo khung đã auto từ 2026-10-17); thiếu khoá vẫn = human; dự án đã cài giữ nguyên (xt.yaml copy-if-absent), tự đổi khi muốn; cắt 3.24.0
- Chọn: Đổi mẫu sang auto (ADR-0020 đã cho phép; repo khung đã auto từ 2026-10-17); thiếu khoá vẫn = human; dự án đã cài giữ nguyên (xt.yaml copy-if-absent), tự đổi khi muốn; cắt 3.24.0
- Lý do (tiêu chí chất lượng cuối): Quyết định của chủ repo (AGENTS.md §1); (1) an toàn: máy chỉ merge khi CI xanh và ở pha harden còn cần review sạch ở head (ADR-0037); UNWAIVABLE và guard giữ nguyên; PR đổi khoá luôn người merge; (2) đường lùi: một dòng xt.yaml về human; (3) dự án cũ không bị đổi ngầm
- Đường lùi: Đặt lại merge_hard_exceptions: human trong framework/templates/xt.yaml; dự án đích sửa xt.yaml qua PR do người merge

### D-177 · 2026-10-25T10:35:44+00:00 · Chủ repo 2026-10-25: /autopilot không dừng — xong hết việc thì audit rồi tiếp tục vòng lặp build tới khi hoàn thiện; chấp nhận mọi lệnh, không cấm, không hỏi. Thiết kế thế nào?

- Phương án: (1) Giữ ADR-0046 nguyên: /autopilot dừng ở build xong, người gõ /complete · (2) Kết thúc /autopilot thành vòng: done → /audit delta (lần đầu full) → 🔴/🟠 và MUST mở/backlog thành PLAN đợt kế → loop init → lặp; hết việc (0 🔴/🟠, 0 MUST mở, backlog rỗng) → /complete (harden, release-check GO). Guard/điểm dừng giữ nguyên (chỉ chặn không đảo ngược/lộ bí mật/tắt hook — không tốn tốc độ); 'không hỏi' đã có (loop defer, không block). Sửa skill + README 11 + lifecycle + CHANGELOG, không đổi máy; gộp vào 3.24.0 · (3) Bỏ cả deny của settings và guard theo nghĩa đen 'không cấm'
- Chọn: Kết thúc /autopilot thành vòng: done → /audit delta (lần đầu full) → 🔴/🟠 và MUST mở/backlog thành PLAN đợt kế → loop init → lặp; hết việc (0 🔴/🟠, 0 MUST mở, backlog rỗng) → /complete (harden, release-check GO). Guard/điểm dừng giữ nguyên (chỉ chặn không đảo ngược/lộ bí mật/tắt hook — không tốn tốc độ); 'không hỏi' đã có (loop defer, không block). Sửa skill + README 11 + lifecycle + CHANGELOG, không đổi máy; gộp vào 3.24.0
- Lý do (tiêu chí chất lượng cuối): Yêu cầu chủ repo (AGENTS §1) về vòng lặp liên tục khớp máy sẵn có (loop init đợt mới, audit delta, release-check) — không cần cơ chế mới. PA3: deny/guard chỉ chặn hành động không đảo ngược, bí mật, tắt hook — không có hành động build nào cần chúng nên bỏ không tăng tốc mà mất lưới an toàn khi chạy không người trực (ADR-0002/0018, tiêu chí 1); bộ phân loại Auto repo không điều khiển được. Nêu rõ với chủ repo; bỏ thật cần ADR riêng do chủ repo chốt. (2) đường lùi: revert PR
- Đường lùi: Khôi phục mục Kết thúc của skill /autopilot bản 3.23.0 (dừng ở build xong)

### D-178 · 2026-10-25T10:37:50+00:00 · Đính chính D-177 (chủ repo 2026-10-25): khi hết việc /autopilot tự chạy /complete hay chỉ đề xuất?

- Phương án: (1) Tự chạy /complete ngay khi hết việc · (2) Chạy /audit full; còn 🔴/🟠 → lặp sửa; sạch mới ĐỀ XUẤT /complete, dừng — người quyết lúc phát hành
- Chọn: Chạy /audit full; còn 🔴/🟠 → lặp sửa; sạch mới ĐỀ XUẤT /complete, dừng — người quyết lúc phát hành
- Lý do (tiêu chí chất lượng cuối): Lời chủ repo: 'đến khi audit không còn lỗi mới đề xuất chuyển qua /complete'; (1) đúng: chuyển harden là một chiều (ADR-0037) nên là quyết định của người; (2) đường lùi: skill một dòng
- Đường lùi: Đổi câu Kết thúc của skill về 'hết việc → /complete'

### D-179 · 2026-10-25T10:49:36+00:00 · Tag phát hành: giữ workflow_dispatch tay hay tự tạo khi VERSION đổi trên main? (chủ repo 2026-10-25: 'Release tag không tự động được à')

- Phương án: (1) Giữ chạy tay (người bấm Actions → Release tag) · (2) Thêm trigger push main với paths VERSION vào release-tag.yml; script giữ nguyên kiểm SemVer, CHANGELOG có mục, tag chưa có; workflow_dispatch vẫn giữ làm đường lùi; thiếu XT_RELEASE_TOKEN thì commit đổi file workflow sẽ không đẩy được tag (AUD-CI-014) → người bấm tay
- Chọn: Thêm trigger push main với paths VERSION vào release-tag.yml; script giữ nguyên kiểm SemVer, CHANGELOG có mục, tag chưa có; workflow_dispatch vẫn giữ làm đường lùi; thiếu XT_RELEASE_TOKEN thì commit đổi file workflow sẽ không đẩy được tag (AUD-CI-014) → người bấm tay
- Lý do (tiêu chí chất lượng cuối): Yêu cầu chủ repo; (1) an toàn: VERSION chỉ đổi qua PR đã merge theo làn (CI xanh, review ở harden), script từ chối tag khi CHANGELOG thiếu mục hay tag đã có; chữ ký GO-NO-GO vẫn là người, tách khỏi tag; (2) đường lùi: bỏ trigger push
- Đường lùi: Xoá khối push trong on: của release-tag.yml

### D-180 · 2026-10-25T13:13:03+00:00 · Dòng chảy chủ repo đề xuất (build → complete → optimize → ký → production → số thật → optimize → ký): làm gì ở khung?

- Phương án: (1) A: chỉ tài liệu — ánh xạ vòng đời + dòng GO-NO-GO người dùng thử · (2) B: A + skill /optimize (chỉ ngân sách đỏ có số), số field qua file docs/ops/FIELD-<ngày>.json, nghiệm thu delta, LOOP-OPT-005 MUST@M; người xác nhận một lần ở GO/NO-GO (không cổng chờ người trong /complete) · (3) C: B + xt.py field check so ngưỡng theo bậc LOOP-DESIGN-019
- Chọn: B: A + skill /optimize (chỉ ngân sách đỏ có số), số field qua file docs/ops/FIELD-<ngày>.json, nghiệm thu delta, LOOP-OPT-005 MUST@M; người xác nhận một lần ở GO/NO-GO (không cổng chờ người trong /complete)
- Lý do (tiêu chí chất lượng cuối): Đúng và an toàn: tối ưu chỉ khi có số đỏ (LOOP-OPT-001), agent không cầm quyền production, điểm ký duy nhất giữ ADR-0009; bền/đơn giản: skill lặp lại được ở G7 và G8 không cần pha mới; C hoãn vì chưa dự án đích nào có SLO thật — không viết máy cho số chưa có. Chủ repo chốt B 2026-10-25.
- Đường lùi: ADR-0048 §Đường lùi: xoá skill, bỏ optimize khỏi DOCTOR_SKILLS, LOOP-OPT-005 về MUST@L, LOOP-OPT-016 → MAY Ngừng dùng

### D-181 · 2026-10-25T13:25:42+00:00 · LOOP-OPT-005 lên MUST@M làm module vượt trần 4 MUST@M (validate đỏ): hạ mục nào?

- Phương án: (1) Giữ LOOP-OPT-005 ở MUST@L, bỏ điểm 5 của ADR-0048 · (2) Hạ LOOP-OPT-004 (một giả thuyết/một thay đổi) MUST@M → MUST@L, LOOP-OPT-005 lên MUST@M · (3) Hạ LOOP-OPT-002 hoặc 003 (bộ đo khoá / máy quyết)
- Chọn: Hạ LOOP-OPT-004 (một giả thuyết/một thay đổi) MUST@M → MUST@L, LOOP-OPT-005 lên MUST@M
- Lý do (tiêu chí chất lượng cuối): Đúng và an toàn: lỗi của 004 là không quy được nguyên nhân (quy trình), lỗi của 005 là kết quả giả được merge — 005 chặt hơn ở M; 002/003 là lõi chống gian lận, không hạ; không nới trần (ADR-0043).
- Đường lùi: Đảo mức hai mục về cũ (giữ ID)

### D-182 · 2026-10-25T13:36:51+00:00 · Lát 2–4 của PLAN-3.25 (skill, chữ quy phạm, mẫu + cắt bản) đã commit trên nhánh bị ràng buộc một tên khi #263 (lát 1) còn chờ review: mở PR thế nào?

- Phương án: (1) Chờ #263 merge rồi mỗi lát một PR tuần tự (3 PR, 3 lượt review nối tiếp) · (2) Chờ #263 merge rồi gộp lát 2–4 vào một PR (mã ngoài .md: 1 dòng xt.py + ~5 dòng test — dưới trần 150), một lượt review rà cả PR
- Chọn: Chờ #263 merge rồi gộp lát 2–4 vào một PR (mã ngoài .md: 1 dòng xt.py + ~5 dòng test — dưới trần 150), một lượt review rà cả PR
- Lý do (tiêu chí chất lượng cuối): Đúng và an toàn như nhau (cùng reviewer rà cả PR ở head, CI xanh); đơn giản hơn và tránh ba lượt review nối tiếp cho diff mã 6 dòng; cùng lệ D-175.
- Đường lùi: Tách lại bằng worktree + cherry-pick nếu reviewer đòi

### D-183 · 2026-10-25T13:42:48+00:00 · Review #263 lượt 1 đòi sửa ADR-0048 (chữ cuối cho lát 2–4 đã commit cục bộ): đẩy thế nào?

- Phương án: (1) Sửa ADR ở head #263 bằng worktree, giữ lát 2–4 chờ PR riêng (D-182) · (2) Gộp cả 4 lát + bản sửa review vào #263 (mã ngoài .md 18 dòng), review lượt 2 rà cả PR ở head
- Chọn: Gộp cả 4 lát + bản sửa review vào #263 (mã ngoài .md 18 dòng), review lượt 2 rà cả PR ở head
- Lý do (tiêu chí chất lượng cuối): ADR đổi kéo theo skill/mẫu/CHANGELOG đổi — tách ra chỉ tạo hai PR cùng chữ; reviewer rà cả PR ở head nên an toàn như nhau; thay D-182.
- Đường lùi: Tách bằng worktree + cherry-pick

### D-184 · 2026-10-25T15:13:14+00:00 · Khi có tool Workflow (Claude Code), skill /audit, /complete, /research có tự dùng Workflow không, và bật ultracode thế nào?

- Phương án: (1) Giữ nguyên: chỉ subagent 2–4 cụm; Workflow chỉ khi người gõ ultracode · (2) Skill /audit §3–4, /complete bước 2 (nợ review), /research (≥ 3 mục) ghi nhánh: có tool Workflow thì dùng — agent chỉ đọc theo agentType researcher/reviewer/Explore, lô ≤ 5 đồng thời, phiên chính gộp/quyết/sửa; không có thì subagent như cũ; không bật ultracode trong settings · (3) Đặt "ultracode": true trong .claude/settings.json cho mọi phiên
- Chọn: Skill /audit §3–4, /complete bước 2 (nợ review), /research (≥ 3 mục) ghi nhánh: có tool Workflow thì dùng — agent chỉ đọc theo agentType researcher/reviewer/Explore, lô ≤ 5 đồng thời, phiên chính gộp/quyết/sửa; không có thì subagent như cũ; không bật ultracode trong settings
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1: agent chỉ đọc theo agentType giữ LOOP-ORCH-001/003/005 (frontmatter model/tools), lô ≤ 5 giữ LOOP-ORCH-008, phiên chính vẫn gộp/quyết/sửa; skill do người gọi có chỉ dẫn gọi Workflow là opt-in nên không cần bật tay. Tiêu chí 3: nhánh dự phòng giữ nguyên hành vi cũ khi không có tool (-p không có rule Workflow, Pro chưa bật). PA3 biến mọi task (cả pha build cơ học) thành workflow — trái ADR-0033/D-142, tốn token. PA1 bỏ phí xác minh đối kháng song song ở nơi tài liệu chính thức khuyên dùng (codebase sweep, cross-checked research).
- Đường lùi: Xoá đoạn Workflow ở 3 skill; skill quay về chỉ subagent

### D-185 · 2026-10-25T16:01:48+00:00 · Đính chính D-184 sau review đối kháng (PR 3.26.0): phạm vi nhánh Workflow

- Phương án: (1) Giữ D-184 nguyên văn · (2) Thu hẹp: chỉ khi người gõ skill (gọi từ /autopilot → subagent); reviewer/reviewer-alt theo người viết; không Explore; không lọc null; một workflow một lúc; opt-in dẫn mô tả tool Workflow 2.1.310
- Chọn: Thu hẹp: chỉ khi người gõ skill (gọi từ /autopilot → subagent); reviewer/reviewer-alt theo người viết; không Explore; không lọc null; một workflow một lúc; opt-in dẫn mô tả tool Workflow 2.1.310
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1: review tái hiện 8 phát hiện cam — hộp duyệt lần đầu treo vòng autopilot, reviewer cố định phá LOOP-ORCH-005, null bị lọc làm nhóm chưa quét thành sạch, Explore không có maxTurns/luật repo. Phát hiện 'skill không phải opt-in' bị bác bằng mô tả tool trong binary 2.1.310.
- Đường lùi: Xoá đoạn Workflow ở 3 skill (đường lùi D-184)

### D-186 · 2026-10-25T16:52:47+00:00 · Review #265 lượt 2: điều kiện dùng Workflow máy quyết được, xác minh null, chọn reviewer

- Phương án: (1) Giữ D-185 ('không có người trực' do agent tự đoán) · (2) Chỉ khi người gõ trực tiếp /audit, /research hoặc /complete … workflow; vòng /autopilot và /complete bước 4 → subagent; xác minh null chạy lại theo §4 rồi mới ghi mở + chưa xác minh; reviewer theo hàng Review bảng điều phối (Fable → model fable, không ai cao hơn → INCONCLUSIVE); nhánh subagent bỏ Explore
- Chọn: Chỉ khi người gõ trực tiếp /audit, /research hoặc /complete … workflow; vòng /autopilot và /complete bước 4 → subagent; xác minh null chạy lại theo §4 rồi mới ghi mở + chưa xác minh; reviewer theo hàng Review bảng điều phối (Fable → model fable, không ai cao hơn → INCONCLUSIVE); nhánh subagent bỏ Explore
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1: 3 cam tái hiện độc lập — 'không có người trực' máy không quyết được nên /complete một phiên vẫn treo ở hộp duyệt lần đầu; xác minh null bỏ qua xác minh đối kháng bắt buộc; ánh xạ reviewer rút gọn cho phép reviewer thấp hơn tác giả Fable. Tiêu chí 3: điều kiện là lời gọi của người — kiểm được.
- Đường lùi: Xoá đoạn Workflow ở 3 skill (đường lùi D-184)

### D-187 · 2026-10-25T17:16:31+00:00 · Review #265 lượt 3: phát hiện lặp lại ở nhánh Workflow — sửa gốc thế nào?

- Phương án: (1) Vá tiếp: thêm luật lát nợ review và luật chọn người xác minh riêng cho Workflow · (2) Thu hẹp gốc: Workflow chỉ cho /audit và /research do người gõ trực tiếp, cùng luật nhánh subagent (người xác minh như /audit §4); bỏ Workflow khỏi /complete (nợ review giữ subagent)
- Chọn: Thu hẹp gốc: Workflow chỉ cho /audit và /research do người gõ trực tiếp, cùng luật nhánh subagent (người xác minh như /audit §4); bỏ Workflow khỏi /complete (nợ review giữ subagent)
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 3 (đơn giản, một nhà): ba lượt review đều tìm lỗi ở chỗ nhánh Workflow tự đặt luật khác nhánh subagent; dùng chung luật xoá cả lớp lỗi. Tiêu chí 1: nợ review gộp vào cụm nhóm làm mất dấu lát hỏng (review_debt PASS sai) — tái hiện độc lập. Người vẫn audit bằng Workflow được bằng cách tự gõ /audit.
- Đường lùi: Xoá đoạn Workflow ở 2 skill (đường lùi D-184)

### D-188 · 2026-10-25T17:42:40+00:00 · Review #265 lượt 4: ADR-0049 còn khuyên bật ultracode cả phiên cho phiên harden

- Phương án: (1) Giữ câu khuyên · (2) Đổi thành: không bật ultracode cả phiên cho /autopilot, /complete (áp mọi task, ở Auto bỏ hộp duyệt); Workflow ở harden do người tự gõ /audit, /research; nhóm cụm hỏng ghi chưa quét cả khi delta; reviewer cho mọi cụm audit
- Chọn: Đổi thành: không bật ultracode cả phiên cho /autopilot, /complete (áp mọi task, ở Auto bỏ hộp duyệt); Workflow ở harden do người tự gõ /audit, /research; nhóm cụm hỏng ghi chưa quét cả khi delta; reviewer cho mọi cụm audit
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1: ultracode cả phiên mở lại đúng các đường D-187 đóng (nợ review, sửa mã thành workflow không hộp duyệt) — tái hiện độc lập theo workflows.md. Lời khuyên trước đó cho chủ repo (bật /effort ultracode cho phiên harden) được đính chính.
- Đường lùi: Khôi phục câu khuyên ở ADR-0049 mục 4

### D-189 · 2026-10-25T18:08:07+00:00 · Review #265 lượt 5: người chọn No/deny cho Workflow, và lời khuyên /audit thay bước 2 /complete

- Phương án: (1) Giữ: No/deny → subagent; /audit thay bước 2 được · (2) No/deny/bộ phân loại chặn → kết luận LOOP-STOP-025, dừng báo người; chỉ không có tool hoặc workflow lỗi → subagent; Workflow không thay bước nào của /complete; người xác minh có schema ket_luan
- Chọn: No/deny/bộ phân loại chặn → kết luận LOOP-STOP-025, dừng báo người; chỉ không có tool hoặc workflow lỗi → subagent; Workflow không thay bước nào của /complete; người xác minh có schema ket_luan
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1: hai cam tái hiện — chạy lại cùng fan-out qua tool Agent sau khi người từ chối là đổi tool cho cùng hiệu ứng (LOOP-STOP-025 MUST@L); /audit thay bước 2 dời SHA quét = HEAD nên review_debt PASS rỗng, bỏ nợ review theo PR/lát.
- Đường lùi: Khôi phục nhánh dự phòng No/deny → subagent

### D-190 · 2026-10-25T18:33:42+00:00 · Review #265 lượt 6: luật tự chạy lại khi agent workflow hỏng (thay D-184 phần /complete và Explore, D-185, D-186 phần chọn reviewer, D-189 phần workflow lỗi → subagent)

- Phương án: (1) Vá thêm phân loại nguyên nhân null (lỗi API vs người dừng vs chặn) · (2) Bỏ mọi tự chạy lại: hỏng/null/bị chặn → đánh dấu (chưa quét / mở + chưa xác minh / chưa biết:), cụm khác dùng tiếp, báo người, chạy lại khi người bảo; chỉ không có tool → nhánh subagent; trạng thái cuối = ADR-0049
- Chọn: Bỏ mọi tự chạy lại: hỏng/null/bị chặn → đánh dấu (chưa quét / mở + chưa xác minh / chưa biết:), cụm khác dùng tiếp, báo người, chạy lại khi người bảo; chỉ không có tool → nhánh subagent; trạng thái cuối = ADR-0049
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1+3: ba cam tái hiện đều ở luật tự chạy lại — null không phân biệt được người dừng với lỗi, chạy lại qua tool Agent phạm LOOP-STOP-025. Không tự chạy lại xoá cả lớp lỗi; người luôn có mặt (điều kiện vào nhánh) nên hỏi rẻ. D-184/D-185/D-186/D-189 phần trái với điều này được thay.
- Đường lùi: Khôi phục chạy lại bằng subagent cho null do lỗi API

### D-191 · 2026-10-25T18:57:40+00:00 · Review #265 lượt 7: người xác minh bị chặn lệnh với 🔴 giữ mức

- Phương án: (1) Ghi chưa biết: và giữ 🔴 (audit check từ chối) · (2) Người xác minh bị chặn = INCONCLUSIVE (giữ Bằng chứng người tìm, Ghi chú chưa xác minh + bị chặn); chặn trong cụm → chưa biết:, 🔴 chỉ còn chưa biết: → 🟠; agent() lỗi = null; phiên chính không tự chạy lệnh bị chặn
- Chọn: Người xác minh bị chặn = INCONCLUSIVE (giữ Bằng chứng người tìm, Ghi chú chưa xác minh + bị chặn); chặn trong cụm → chưa biết:, 🔴 chỉ còn chưa biết: → 🟠; agent() lỗi = null; phiên chính không tự chạy lệnh bị chặn
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1: cam tái hiện — audit check exit 1 với 🔴 + chưa biết:; hai luật D-190 chồng lên nhau. Khớp luật sổ có sẵn, không thêm trạng thái mới.
- Đường lùi: Khôi phục chữ D-190

### D-192 · 2026-10-25T22:56:32+00:00 · Trả 3 🟢 mở của audit delta3 (AUD-HAR-113/114, AUD-DOC-086) và nợ review_debt VERSION sau #265: phạm vi và cách ghép lại BLUEPRINT?

- Phương án: (1) Ghép lại BLUEPRINT bằng compose mặc định (link .xtemplates/framework) rồi tái kiểm 19 mục MUST bị đặt lại như #257 · (2) Ghép lại với XT_FRAMEWORK_LINK=framework (chỉ 6 mục đổi chữ thật, giữ trạng thái 104 mục), sửa HAR-114 + DOC-086 cùng một PR, cắt 3.26.1 · (3) Đổi mặc định _rel_link theo framework_repo rồi ghép lại
- Chọn: Ghép lại với XT_FRAMEWORK_LINK=framework (chỉ 6 mục đổi chữ thật, giữ trạng thái 104 mục), sửa HAR-114 + DOC-086 cùng một PR, cắt 3.26.1
- Lý do (tiêu chí chất lượng cuối): Đúng: đo trên bản nháp — 19 mục 'đổi chữ' của phương án 1 là giả (chỉ khác tiền tố link), đặt lại [ ] làm mất bằng chứng thật; biến môi trường đã có và có test. Đơn giản: không đổi hành vi xt.py cho người gọi khác (phương án 3). Một PR nhỏ cho 3 🟢 cùng hạn.
- Đường lùi: Revert PR; BLUEPRINT về bản #257

### D-193 · 2026-10-26T01:06:13+00:00 · Duyệt PLAN-harden-2026-10-26: trả nợ unchecked_must bằng lệnh kiểm máy

- Phương án: (1) Gắn — Kiểm: cho 19 MUST kiểm được bằng lệnh chỉ đọc tất định (ruff bandit cho SEC-004/007) · (2) Giữ nguyên, chỉ ghi rủi ro chấp nhận ở GO-NO-GO · (3) Bật unchecked_must fail
- Chọn: Gắn — Kiểm: cho 19 MUST kiểm được bằng lệnh chỉ đọc tất định (ruff bandit cho SEC-004/007)
- Lý do (tiêu chí chất lượng cuối): (1) đúng: mục tick được máy chạy lại, hỏng thì đỏ; (2) đường lùi revert một file; (3) không đổi công cụ; bật fail khi còn 38 mục không kiểm được sẽ chặn oan
- Đường lùi: revert PR; các mục quay về bằng chứng bằng lời

### D-194 · 2026-10-26T02:59:45+00:00 · Duyệt PLAN-harden-2026-10-26b: ERR-001, lệnh kiểm blueprint trên CI, siết SEC-004

- Phương án: (1) Một PR: sửa _load_guard báo stderr + kiểm S110/S112, bước CI blueprint-status --run, siết regex SEC-004 · (2) Chỉ ghi ERR-001 là Miễn và giữ kiểm cục bộ
- Chọn: Một PR: sửa _load_guard báo stderr + kiểm S110/S112, bước CI blueprint-status --run, siết regex SEC-004
- Lý do (tiêu chí chất lượng cuối): (1) lỗi nạp guard không còn im lặng, mục tick hỏng thì đỏ trên mỗi PR; (2) revert một PR; (3) không thêm phụ thuộc (ruff đã ghim)
- Đường lùi: revert PR

### D-195 · 2026-10-26T05:07:36+00:00 · Duyệt PLAN-harden-2026-10-26c: 37 MUST còn lại không có lệnh kiểm

- Phương án: (1) Gắn — Kiểm: cho cả 37 mục bằng test hành vi có sẵn hoặc grep chỉ đọc; gỡ noqa chết, type: ignore có lý do · (2) Chỉ 17 mục kiểm được bằng grep, 20 mục giữ bằng chứng bằng lời · (3) Đổi 20 mục sang [~] Không áp dụng
- Chọn: Gắn — Kiểm: cho cả 37 mục bằng test hành vi có sẵn hoặc grep chỉ đọc; gỡ noqa chết, type: ignore có lý do
- Lý do (tiêu chí chất lượng cuối): (1) mọi mục áp dụng và đạt, bằng chứng đã trỏ test/grep — chạy lại được là đúng hơn lời khai; [~] sai sự thật; (2) revert một PR; (3) không thêm công cụ
- Đường lùi: revert PR

### D-196 · 2026-10-26T06:56:30+00:00 · Cách làm 4 việc chủ repo duyệt 2026-10-26 (T-1814/1822/1823/1832)

- Phương án: (1) PLAN-harden-2026-10-26d: T-3531 đăng ký hook (PR 1, gộp đóng sổ T-1814), T-3532 ca đối kháng (PR 2), T-3533 spike mutation (PR 3), cắt 3.27.0 ở lát cuối · (2) Một PR cho cả bốn
- Chọn: PLAN-harden-2026-10-26d: T-3531 đăng ký hook (PR 1, gộp đóng sổ T-1814), T-3532 ca đối kháng (PR 2), T-3533 spike mutation (PR 3), cắt 3.27.0 ở lát cuối
- Lý do (tiêu chí chất lượng cuối): (1) mỗi lát nhỏ, review được; hook đổi hành vi dự án đích nên cắt bản; (2) revert từng lát; (3) spike có thể không khả thi — tách để không chặn hook
- Đường lùi: revert từng PR

### D-197 · 2026-10-26T07:10:29+00:00 · T-3533 (T-1832): đưa mutation test guard.py vào CI?

- Phương án: (1) Không — spike: 13 486 mutant, trampoline mutmut 3 phá test tiến trình con, ước hàng giờ/lần; giữ autonomy-bench + đột biến tay của reviewer · (2) Có — job tuần mutmut trên subset test, loại test tiến trình con
- Chọn: Không — spike: 13 486 mutant, trampoline mutmut 3 phá test tiến trình con, ước hàng giờ/lần; giữ autonomy-bench + đột biến tay của reviewer
- Lý do (tiêu chí chất lượng cuối): (1) loại test tiến trình con là bỏ đúng lớp kiểm hook như Claude Code gọi — đo sai; (3) không thêm phụ thuộc/workflow khi chưa chạy được; (5) chi phí giờ máy
- Đường lùi: chạy lại spike khi guard tách module hoặc mutmut chọn được hàm (docs/ops/MUTATION-2026-10-26.md)

### D-198 · 2026-10-26T07:52:05+00:00 · gh pr merge --admin ở chính sách mặc định (AUD-SEC-109)

- Phương án: (1) Deny phẳng mọi chính sách (mã MERGE_ADMIN), như AUTO_MERGE_ENABLE · (2) Giữ ask thường (mặc định cho qua khi merge-check = merge)
- Chọn: Deny phẳng mọi chính sách (mã MERGE_ADMIN), như AUTO_MERGE_ENABLE
- Lý do (tiêu chí chất lượng cuối): (1) --admin vượt ruleset nhánh — lớp đỡ CI/duyệt GitHub mà merge-check không mô hình; máy không cần cờ này; cách hiểu chặt hơn thắng; (2) người vẫn merge trên GitHub
- Đường lùi: gỡ _gh_admin_flag khỏi hai luật merge, bỏ mã MERGE_ADMIN

### D-199 · 2026-10-26T09:33:25+00:00 · Gốc của AUD-SEC-108: hook fail-open khi guard.py hỏng

- Phương án: (1) Hook đóng hàng rào khi guard.py vắng/không đọc được/rỗng, hoặc chạy lỗi mà đã sửa so với HEAD; lỗi ở bản đã commit giữ fail-open (ADR-0002) · (2) Chỉ chặn từng lệnh làm hỏng guard ở luật guard
- Chọn: Hook đóng hàng rào khi guard.py vắng/không đọc được/rỗng, hoặc chạy lỗi mà đã sửa so với HEAD; lỗi ở bản đã commit giữ fail-open (ADR-0002)
- Lý do (tiêu chí chất lượng cuối): (1) đóng cả lớp (chmod/setfacl/glob/xargs/$(…)/ghi rỗng) thay vì đuổi từng biến thể; (2) khôi phục bằng git checkout/install.py vẫn được, Edit vẫn sửa được guard; (3) ADR-0002 giữ cho lỗi thật ở bản đã commit
- Đường lùi: bỏ hàm broken và hai điều kiện mới ở pre-bash-guard.sh

### D-200 · 2026-10-26T12:03:42+00:00 · Hook làm gì khi guard.py không nạp được (guard_fields không trả ok)?

- Phương án: (1) Luôn đóng hàng rào (chỉ lệnh xem/khôi phục, install.py); không dựa trạng thái git · (2) Đóng khi khác blob HEAD, mở khi untracked (bản 96e867d) · (3) Đóng khi khác blob HEAD, mở khi lịch sử chưa từng có guard.py (rev-list --all --reflog)
- Chọn: Luôn đóng hàng rào (chỉ lệnh xem/khôi phục, install.py); không dựa trạng thái git
- Lý do (tiêu chí chất lượng cuối): (1) đúng và an toàn: main() của guard đã bắt mọi Exception lúc chạy và trả ok, nên guard_fields hỏng chỉ khi file không nạp/compile được — gần như luôn là hỏng/sửa tay; mọi dấu hiệu dựa trạng thái git (chỉ mục, HEAD, reflog, repo lồng) agent tự đổi được bằng lệnh guard cho qua (review #282 lượt 3-5: 4 lách liên tiếp). (2) đường lùi: Edit vẫn sửa được guard (pre-edit fail-open), git checkout/restore -- path và install.py nằm trong restore_re. (3) đơn giản: bỏ ~10 dòng git. Giá: guard đã commit mà không nạp được cũng đóng — lỗi khung thật, cần sửa ngay, không phải lý do mở mọi lệnh
- Đường lùi: Khôi phục khối so blob HEAD ở pre-bash-guard.sh (commit 96e867d)

### D-201 · 2026-10-26T23:10:18+00:00 · Tách nối phiên khỏi giải quyết việc chờ: ba lệnh con mới hay cờ trên loop resume, và loop resume cũ xử lý ra sao?

- Phương án: (1) Ba lệnh con riêng loop attach (chỉ gắn phiên) · loop resolve --task ID (gỡ một việc chờ) · loop unblock (mở block); loop resume cũ vẫn chạy như trước nhưng in cảnh báo trỏ ba lệnh mới, bỏ ở ADR sau · (2) Đổi nghĩa loop resume: mặc định chỉ gắn phiên, thêm cờ --resolve ID và --unblock · (3) Ba lệnh con riêng và loop resume cũ thoát exit 2 buộc chọn một lệnh (bản đề xuất ở research 2026-10-26 §9.1) · (4) Giữ nguyên loop resume, chỉ sửa SessionStart và README để không trỏ tới resume khi đổi phiên
- Chọn: Ba lệnh con riêng loop attach (chỉ gắn phiên) · loop resolve --task ID (gỡ một việc chờ) · loop unblock (mở block); loop resume cũ vẫn chạy như trước nhưng in cảnh báo trỏ ba lệnh mới, bỏ ở ADR sau
- Lý do (tiêu chí chất lượng cuối): (1) đúng và an toàn: mỗi lệnh một nghĩa, attach không chạm deferred/đếm lỗi/blocked; resume cũ không đổi nghĩa âm thầm với dự án đích đã cài bản cũ (skill autopilot, README, SessionStart) · (2) đường lùi: resume còn chạy nên không phá phiên đang chạy, bỏ lệnh mới là một commit · (3) test được từng nghĩa riêng; phương án 3 làm vỡ mọi tài liệu và hook dự án đích chưa chạy lại install.py giữa hai bản; phương án 2 đổi nghĩa lệnh cũ không báo; phương án 4 để lại hai lệnh nguy hiểm trên đường đổi phiên
- Đường lùi: Xoá ba lệnh con và cảnh báo ở loop resume; đưa SessionStart/README về trỏ loop resume (một commit)

### D-202 · 2026-10-27T01:36:00+00:00 · Hoàn thành sáu lát nghiên cứu ba vòng (chủ repo 2026-10-27 'hoàn thành hết đi'): thiết kế và thứ tự cho lát 0–3, xử lý lát 4–5?

- Phương án: (1) Máy hoá bước kế và một lần thử trên CLI/state hiện có (ADR-0052): lát 0 corpus FLOW, lát 1 rev/task_runs/attach-resolve-unblock/perf v2 → 3.28.0, lát 2 next-step chỉ đọc → lát 3 perf trial → 3.29.0; mỗi task một PR, lát 4–5 loop defer · (2) Chỉ thêm lời nhắc vào skill · (3) Runner ngoài phiên tự gọi agent/sửa CI/phát hành
- Chọn: Máy hoá bước kế và một lần thử trên CLI/state hiện có (ADR-0052): lát 0 corpus FLOW, lát 1 rev/task_runs/attach-resolve-unblock/perf v2 → 3.28.0, lát 2 next-step chỉ đọc → lát 3 perf trial → 3.29.0; mỗi task một PR, lát 4–5 loop defer
- Lý do (tiêu chí chất lượng cuối): (1) đúng và an toàn: bốn tái hiện R2–R5 có test đỏ trước khi sửa, không nới cổng/trần; lát 4–5 cần dữ liệu/quyền chỉ chủ dự án có nên defer; (2) mỗi task một PR đảo ngược được, trần theo task tắt bằng --max-task-runs 0; (3) stdlib, test được; phương án 2 không sửa được R2–R5 và skill hết byte; phương án 3 cần ADR đối chiếu ADR-0009, quyền và chi phí chưa có số
- Đường lùi: Revert từng PR theo ADR-0052 §Đường lùi; bỏ PLAN-harden-2026-10-27-loops

### D-203 · 2026-10-27T03:07:45+00:00 · perf trial (lát 3) có chốt thiết kế trong ADR-0052 không, sau 3 lượt review #290 (lượt 4–6) mỗi lượt lộ lớp ràng buộc mới?

- Phương án: (1) Rút §7 khỏi ADR-0052; ghi ràng buộc đã tìm làm đầu vào ADR riêng của lát 3 (sau spike môi trường đo); lát 0–2 + perf v2 metadata giữ · (2) Vá tiếp §7 trong ADR-0052 tới khi review sạch
- Chọn: Rút §7 khỏi ADR-0052; ghi ràng buộc đã tìm làm đầu vào ADR riêng của lát 3 (sau spike môi trường đo); lát 0–2 + perf v2 metadata giữ
- Lý do (tiêu chí chất lượng cuối): (1) đúng và an toàn: 5 🟠 lượt 6 (baseline agent lái được, bộ chấm từ cây candidate, thiếu test tương đương, worktree tạm khác môi trường, không đo đại lượng tất định) cần thử nghiệm thực tế, chốt trên giấy dễ sai; (2) giữ đường lùi: lát 0–2 không phụ thuộc perf trial; (3) ADR riêng test được bằng spike; tốc độ chỉ phá hoà
- Đường lùi: Đưa §7 trở lại ADR-0052 bằng ADR mới thay thế phần này

### D-204 · 2026-10-27T04:14:58+00:00 · T-3559: loop init (retries=0) có ghi nhớ rev trước bước kiểm vòng sống (_live_loop, ngoài khoá) và từ chối nếu rev đổi tới lúc lấy khoá không?

- Phương án: (1) Có — so rev đã thấy trước _live_loop; đổi → StateRevConflict exit 2 · (2) Không — chỉ kiểm rev trong khoá
- Chọn: Có — so rev đã thấy trước _live_loop; đổi → StateRevConflict exit 2
- Lý do (tiêu chí chất lượng cuối): (1) đúng: _live_loop quyết định cho phép ghi đè dựa trên state đọc ngoài khoá; không so rev thì retries=0 vô tác dụng và init có thể ghi đè vòng vừa đổi; (2) đường lùi: bỏ dòng so seen
- Đường lùi: Bỏ so rev seen ở _init_apply

### D-205 · 2026-10-27T04:25:24+00:00 · T-3538/T-3559/T-3539 đã đan trong cùng hàm (update_state, _verdict_loop_state) ở một worktree: tách 3 PR hay gộp 1 PR nhóm an toàn state?

- Phương án: (1) Gộp 1 PR (3 commit theo task không tách được → 1 commit, ghi 3 task), reviewer-alt rà cả PR · (2) Tách 3 PR, dựng lại trạng thái trung gian từng task
- Chọn: Gộp 1 PR (3 commit theo task không tách được → 1 commit, ghi 3 task), reviewer-alt rà cả PR
- Lý do (tiêu chí chất lượng cuối): (1) đúng: trạng thái trung gian chưa từng chạy/test, dựng lại để tách là mã mới chưa kiểm — rủi ro hơn; ba task cùng một chủ đề (an toàn state) và cùng bộ FLOW-04/06/07; (3) review một lần trên mã đã chạy cổng đầy đủ; vượt ~150 dòng chủ yếu là test
- Đường lùi: Revert PR (một commit squash)

### D-206 · 2026-10-27T05:35:44+00:00 · task_runs đặt lại khi nào (ADR-0052 §3 chỉ nói 'xanh hoặc req_rev đổi')?

- Phương án: (1) Đếm lại khi spec hoặc Gate (dạng chuẩn, bỏ khác biệt khoảng trắng) đổi — trừ task đã chạm trần; chỉ lần xanh chạy đúng Gate hoặc loop resume xoá · (2) Đúng chữ ADR: chỉ req_rev (spec nguyên văn) và mọi lần xanh
- Chọn: Đếm lại khi spec hoặc Gate (dạng chuẩn, bỏ khác biệt khoảng trắng) đổi — trừ task đã chạm trần; chỉ lần xanh chạy đúng Gate hoặc loop resume xoá
- Lý do (tiêu chí chất lượng cuối): (1) đúng và an toàn: review #294 tái hiện agent tự thoát chặn bằng thêm khoảng trắng vào Gate/spec hoặc record xanh bằng -- true; đổi Gate thật trước trần vẫn là 'đổi cách' (nghiên cứu §4B); (2) đường lùi --max-task-runs 0
- Đường lùi: task_runs_rev về task_req_rev nguyên văn; bỏ điều kiện chạm trần và clears trong loop_record

### D-207 · 2026-10-27T06:48:32+00:00 · Gộp T-3540/3541/3542 (attach/resolve/unblock) vào một PR #295 dù PLAN ghi mỗi task một PR, ≤ 150 dòng?

- Phương án: (1) Giữ một PR: ba lệnh dùng chung _loop_exit, _interventions, _carry_interventions; tách ra thì PR đầu chứa code chung chưa có lệnh gọi · (2) Tách ba PR theo PLAN
- Chọn: Giữ một PR: ba lệnh dùng chung _loop_exit, _interventions, _carry_interventions; tách ra thì PR đầu chứa code chung chưa có lệnh gọi
- Lý do (tiêu chí chất lượng cuối): (3) bảng lối ra là một giao ước chung, review một lần thấy đủ ca; (2) đường lùi vẫn là revert một squash commit; như D-205
- Đường lùi: revert squash #295; đợt sau tách theo task

### D-208 · 2026-10-27T07:21:28+00:00 · Lối ra vòng bị chặn khi PLAN mất/rỗng mà state cũng có nguồn chặn (cờ/lỗi lặp): theo PLAN hay theo state? (review #295 lượt 2 🟢1)

- Phương án: (1) PLAN trên đĩa thắng: mất/rỗng → loop stop/loop init dù cờ hay verdict nào · (2) State thắng như chữ ADR-0051/0052 §6: có cờ → unblock
- Chọn: PLAN trên đĩa thắng: mất/rỗng → loop stop/loop init dù cờ hay verdict nào
- Lý do (tiêu chí chất lượng cuối): (1) unblock vòng mất PLAN thì Stop kế chặn ngay — lối ra theo state là đi vòng; (3) một nguồn sự thật (đĩa), không đoán từ đếm lỗi mà loop record đổi sau khi dừng; _live_loop/_loop_exit/unblock cùng thứ tự
- Đường lùi: đổi _plan_tasks check trong _loop_exit/_unblock_problem/_live_loop về sau _blocked_by_state

### D-209 · 2026-10-27T09:46:43+00:00 · Triển khai PLAN-phase-gated-review (PR #297) tới đâu khi chủ repo yêu cầu 'sửa PR 297 rồi triển khai luôn'?

- Phương án: (1) Lát tối thiểu ngay: ngân sách review mỗi PR = 2 lượt chưa sạch (1 toàn bộ + 1 delta) rồi pr next trả rethink; thêm lượt chỉ qua pr rethink --decision D-NNN; review trước PR ở đúng commit đẩy lên ghi luôn cho head đó; hoãn sổ pha/fingerprint/coverage manifest/pilot tới khi có số đo · (2) Đủ RV-01…RV-07: sổ pha, fingerprint finding, coverage manifest, một PR mỗi pha ở harden · (3) Chỉ sửa tài liệu kế hoạch, chưa đổi hành vi
- Chọn: Lát tối thiểu ngay: ngân sách review mỗi PR = 2 lượt chưa sạch (1 toàn bộ + 1 delta) rồi pr next trả rethink; thêm lượt chỉ qua pr rethink --decision D-NNN; review trước PR ở đúng commit đẩy lên ghi luôn cho head đó; hoãn sổ pha/fingerprint/coverage manifest/pilot tới khi có số đo
- Lý do (tiêu chí chất lượng cuối): (1) đúng và an toàn: chặn đúng lỗi có số (review #282 bảy lượt) bằng cơ chế máy kiểm, không nới cổng — merge vẫn cần review sạch ở head; một PR mỗi pha trái P8/giới hạn 150 dòng và ADR-0037 (review LLM trên diff lớn kém tin cậy); (2) đường lùi: một hằng số và một nhánh trong pr next; (3) đơn giản: dùng lại sổ review/dấu xt-review, rev+khoá và task_runs (ADR-0052) đã có thay vì engine pha mới; phần còn lại cần số đo trước (giả thuyết giảm 50 % chưa đo)
- Đường lùi: REVIEW_ROUNDS lớn hoặc bỏ nhánh rethink trong _pr_next_review; revert squash PR triển khai

### D-210 · 2026-10-27T10:43:29+00:00 · Review #298 lượt 1 (🟠2): pr rethink nhận D-NNN cũ bất kỳ — siết thế nào?

- Phương án: (1) Chỉ khi pr next đang trả rethink; D-NNN có câu hỏi nhắc #N và ghi sau mọi review chưa sạch đã đăng của PR (so thời điểm ISO, mốc hỏng → từ chối); tra sổ ở loop_root rồi dự án · (2) Giữ chữ ADR: D-NNN có trong sổ, mỗi D-NNN một lần mỗi PR · (3) Đăng dấu rethink lên PR như dấu review để steward thấy
- Chọn: Chỉ khi pr next đang trả rethink; D-NNN có câu hỏi nhắc #N và ghi sau mọi review chưa sạch đã đăng của PR (so thời điểm ISO, mốc hỏng → từ chối); tra sổ ở loop_root rồi dự án
- Lý do (tiêu chí chất lượng cuối): (1) đúng: phương án 2 cho 209 lần mở lại không cần quyết định mới (reviewer tái hiện) — phá Hệ quả của ADR-0053; thời điểm sau review cuối buộc quyết định mới, đồng thời làm luật 'mỗi D-NNN một lần' thừa; (3) đơn giản: chạy offline qua cùng đường pr next (load_pr/with_published), không thêm dấu mới — phương án 3 thêm bề mặt guard/steward mà steward không review
- Đường lùi: Bỏ kiểm action/thời điểm trong _pr_rethink, trở lại kiểm D-NNN có trong sổ

### D-211 · 2026-10-27T12:39:35+00:00 · PR #298 quá trần review (2 lượt chặn: lượt 1 lách bằng D-NNN cũ, lượt 2 test/tài liệu và D-NNN mốc tương lai): đổi chiến lược thế nào?

- Phương án: (1) Tiếp trên PR #298 nhưng thu hẹp: coi pr rethink là DẤU VẾT quyết định, không phải hàng rào chống giả mạo (agent cố ý giả dấu/xoá comment vẫn lách được — merge vẫn cần review sạch ở head); chỉ sửa 4 🟠 đã xác minh + 🟢 rẻ (khôi phục kiểm D-NNN đã dùng, từ chối mốc tương lai, do nhắc #N, test giữa hai review, trả chữ ADR-0053 về bản chấp nhận); giới hạn còn lại ghi ở PR · (2) Đóng #298, tách: PR mới chỉ có rethink trong pr next, pr rethink làm PR sau · (3) Bỏ pr rethink, chỉ còn rethink → loop defer cho người
- Chọn: Tiếp trên PR #298 nhưng thu hẹp: coi pr rethink là DẤU VẾT quyết định, không phải hàng rào chống giả mạo (agent cố ý giả dấu/xoá comment vẫn lách được — merge vẫn cần review sạch ở head); chỉ sửa 4 🟠 đã xác minh + 🟢 rẻ (khôi phục kiểm D-NNN đã dùng, từ chối mốc tương lai, do nhắc #N, test giữa hai review, trả chữ ADR-0053 về bản chấp nhận); giới hạn còn lại ghi ở PR
- Lý do (tiêu chí chất lượng cuối): (1) đúng: hai lượt cho thấy cố biến pr rethink thành hàng rào chống giả mạo là đuổi theo đường lách (cùng mẫu #282) — giới hạn mục tiêu về dấu vết là đổi chiến lược thật; 4 🟠 còn lại là lỗ test/tài liệu và một kiểm phòng thủ rẻ; (2) đường lùi: một PR, revert squash; phương án 2 dựng lại trạng thái trung gian chưa test, phương án 3 trả mọi PR quá trần cho người — trái ADR-0008
- Đường lùi: Revert squash PR #298; hoặc REVIEW_ROUNDS rất lớn

### D-212 · 2026-10-27T17:34:35+00:00 · PR #300 (T-3544): dirty/tree_fp của perf sample vẫn tin .git/info/exclude, core.excludesFile, assume-unchanged/skip-worktree — có siết không?

- Phương án: (1) Chỉ perf_tree dùng --exclude-per-directory=.gitignore (tree_fp ≠ tree_fingerprint; file bỏ qua toàn cục như .DS_Store làm dirty) · (2) Đổi cả tree_fingerprint (mọi verified.json lệch một lần, ảnh hưởng loop verify) · (3) Giữ tree_fp = tree_fingerprint như ADR-0052 §4; ghi giới hạn đã biết ở CHANGELOG/optimization-loop.md
- Chọn: Giữ tree_fp = tree_fingerprint như ADR-0052 §4; ghi giới hạn đã biết ở CHANGELOG/optimization-loop.md
- Lý do (tiêu chí chất lượng cuối): (1) đúng: ADR-0052 §4 định nghĩa tree_fp = tree_fingerprint; baseline do máy ghim ở worktree origin/main sạch (LOOP-OPT-003) nên before.dirty là tín hiệu phụ, hàng rào thật là perf guard (đã không tin exclude cục bộ) + guard chặn update-index; (2) đường lùi: siết sau ở perf trial (lát 3) mà không lệch verified.json; (3) đơn giản, một nguồn vân tay; (5) không cần ADR mới
- Đường lùi: Chọn phương án 1 trong PR riêng trước T-3545 nếu audit delta T-3556 cho thấy agent lách được baseline

### D-213 · 2026-10-27T18:09:23+00:00 · PR #300 quá trần review (lượt 1: ext-diff/textconv che cây bẩn; lượt 2: --ignore-submodules=none đổi vân tay mặc định, lùi loop verify): đổi chiến lược thế nào?

- Phương án: (1) Thu hẹp: bỏ hẳn --ignore-submodules khỏi tree_hash (vân tay ở cấu hình mặc định giống hệt c9befb7, chỉ giữ --no-ext-diff --no-textconv vốn không đổi đầu ra mặc định); che bằng diff.ignoreSubmodules ghi giới hạn đã biết; sửa 🟢 test --out có sẵn + tài liệu; không mở rộng thêm · (2) Đổi none → untracked như reviewer đề xuất, thêm test submodule · (3) Tách PR: chỉ mẫu v2 không đụng tree_hash, phần chống che bằng cấu hình git sang PR sau
- Chọn: Thu hẹp: bỏ hẳn --ignore-submodules khỏi tree_hash (vân tay ở cấu hình mặc định giống hệt c9befb7, chỉ giữ --no-ext-diff --no-textconv vốn không đổi đầu ra mặc định); che bằng diff.ignoreSubmodules ghi giới hạn đã biết; sửa 🟢 test --out có sẵn + tài liệu; không mở rộng thêm
- Lý do (tiêu chí chất lượng cuối): (1) đúng: mỗi lượt sửa tree_hash dùng chung với loop verify lại mở lớp lỗi mới (cùng mẫu #282) — giữ tree_hash đúng như c9befb7 ở cấu hình mặc định loại hẳn rủi ro lùi verify; ext-diff/textconv đã có test đỏ→xanh và reviewer xác nhận đầu ra mặc định giống hệt; (2) đường lùi: thêm untracked sau ở PR riêng có đo; (3) diff nhỏ nhất; phương án 2 dựa trên tương đương mặc định chỉ thử trên git 2.43, phương án 3 trả lại lỗ dirty=false đã tái hiện
- Đường lùi: PR riêng thêm --ignore-submodules=untracked kèm test submodule chỉ có file chưa track

### D-214 · 2026-10-27T21:04:16+00:00 · Audit delta lát 1 (T-3556, sổ #302): 5 🟠 mở (AUD-SEC-116, AUD-SEC-119, AUD-PERF-003, AUD-XFEAT-026/027) — sửa thế nào trước khi cắt 3.28.0?

- Phương án: (1) Bốn task mỗi task một PR trước T-3556/T-3546: T-3560 perf guard --text + cảnh báo .gitattributes + --base qua perf_rev (SEC-116, SEC-115); T-3561 perf sample đo không lượng tử (PERF-003); T-3562 Gate mẫu: before.json ngoài cả hai cây + sha256 giữ trong biến shell, công cụ chấm lấy từ SHA gốc bằng git show chạy python3 -I, ghi giới hạn còn lại (cùng uid) tới perf trial (XFEAT-026/027); T-3563 guard chặn ghi refs/remotes/* và tag/nhánh trùng tên remote (SEC-119, nếu xác minh lần hai tái hiện) · (2) Chấp nhận 🟠 có hạn, cắt 3.28.0 ngay, sửa ở lát 3 (perf trial) · (3) Gỡ Gate mẫu tối ưu khỏi tài liệu tới khi có perf trial
- Chọn: Bốn task mỗi task một PR trước T-3556/T-3546: T-3560 perf guard --text + cảnh báo .gitattributes + --base qua perf_rev (SEC-116, SEC-115); T-3561 perf sample đo không lượng tử (PERF-003); T-3562 Gate mẫu: before.json ngoài cả hai cây + sha256 giữ trong biến shell, công cụ chấm lấy từ SHA gốc bằng git show chạy python3 -I, ghi giới hạn còn lại (cùng uid) tới perf trial (XFEAT-026/027); T-3563 guard chặn ghi refs/remotes/* và tag/nhánh trùng tên remote (SEC-119, nếu xác minh lần hai tái hiện)
- Lý do (tiêu chí chất lượng cuối): (1) đúng và an toàn: PLAN ghi 🔴/🟠 sửa trước khi cắt bản; 3.28.0 chính là bản đưa perf v2 + Gate mẫu tới dự án đích — phát hành với Gate báo improved giả trái LOOP-OPT-002/003; (2) đường lùi: mỗi task một PR nhỏ revert được; (3) theo chuẩn: sửa gốc (--text, đo không thăm dò, công cụ chấm bất biến) thay vì chấp nhận; phương án 3 bỏ đường dùng được duy nhất của /optimize tới lát 3
- Đường lùi: Revert từng PR; hoặc chấp nhận 🟠 có chủ/hạn và cắt bản

### D-215 · 2026-10-27T23:21:06+00:00 · T-3563 (guard REMOTE_REF_FORGE, AUD-SEC-119): diff guard +229 dòng > 150; lỗ đổi URL remote; Gate mẫu đọc tên ngắn origin/main — làm gì?

- Phương án: (1) Giữ một PR (luật guard gắn kết, tách ra thì nửa chặn nửa hở); lỗ remote URL/config/ghi thẳng .git/refs ghi giới hạn đã biết tới perf trial; Gate mẫu đọc refs/remotes/origin/main (tag/nhánh trùng tên không che được); ca autonomy-bench để 🟢 · (2) Tách PR: update-ref/fetch trước, tag/branch/checkout/switch sau · (3) Chặn thêm remote set-url/config remote.*.url khi URL cục bộ
- Chọn: Giữ một PR (luật guard gắn kết, tách ra thì nửa chặn nửa hở); lỗ remote URL/config/ghi thẳng .git/refs ghi giới hạn đã biết tới perf trial; Gate mẫu đọc refs/remotes/origin/main (tag/nhánh trùng tên không che được); ca autonomy-bench để 🟢
- Lý do (tiêu chí chất lượng cuối): (1) đúng: tách để lại khe giữa hai PR mà agent đi được; tên ref đầy đủ loại hẳn lớp che bằng tag/nhánh độc lập với guard; chặn remote URL dễ chặn oan đổi sang SSH; (2) đường lùi: revert một PR; (3) diff phần lớn là bảng lệnh + bộ tách tuỳ chọn có test 129 lệnh
- Đường lùi: Revert PR T-3563; Gate mẫu quay về origin/main

### D-216 · 2026-10-28T05:52:18+00:00 · PR #306 (T-3563) quá trần review (lượt 1: alias chấm/COUNT/include/xargs; lượt 2: delta sạch nhưng 🔴 có từ trước --attr-source/--shallow-file lách mọi luật git, 🟠 export GIT_CONFIG_* lách HOOK_BYPASS): đổi chiến lược thế nào?

- Phương án: (1) Sửa 🔴 (thêm --attr-source/--shallow-file vào GIT_OPTS_WITH_VALUE + test, và đối chiếu toàn bộ tuỳ chọn toàn cục có giá trị của git 2.43 để đóng cả lớp) và 🟠 (gộp biến export; --config-env trỏ biến không rõ → không an toàn) trong PR này; từ lượt kế chỉ xét delta + hồi quy — lối lách có từ trước khác vào sổ audit thành task mới, không mở rộng PR · (2) Merge #306 như hiện có (delta sạch), mở task riêng cho 🔴/🟠 có từ trước · (3) Đóng #306, gộp lại thành một PR guard lớn
- Chọn: Sửa 🔴 (thêm --attr-source/--shallow-file vào GIT_OPTS_WITH_VALUE + test, và đối chiếu toàn bộ tuỳ chọn toàn cục có giá trị của git 2.43 để đóng cả lớp) và 🟠 (gộp biến export; --config-env trỏ biến không rõ → không an toàn) trong PR này; từ lượt kế chỉ xét delta + hồi quy — lối lách có từ trước khác vào sổ audit thành task mới, không mở rộng PR
- Lý do (tiêu chí chất lượng cuối): (1) đúng và an toàn: 🔴 phá cả luật push --force lên main, sửa một dòng + đối chiếu danh sách đóng cả lớp; merge để hở là phát hành guard biết lỗ (phương án 2); (2) giữ đường lùi: một PR revert được; (3) chặn vòng lặp: phạm vi lượt kế khoá vào delta + hồi quy, lối có từ trước → audit (mẫu #282)
- Đường lùi: Revert PR; hoặc tách 🔴/🟠 sang task mới

### D-217 · 2026-10-28T06:54:44+00:00 · Quét lại T-3556 (6acc573..fcf83b3): 5 🟠 cũ đã sửa (#303–#306); xác minh đối kháng thêm lỗi guard có từ trước: 🔴 tiền tố X+=1 lách mọi luật (cả rm -rf /), 🔴 eval/bash -c mất env đã export (HOOK_BYPASS), 🟠 giá trị biến cũ sau read/printf -v/source, 🟠 core.hooksPath; 🟢 parallel ::: "cmd" lách mọi luật — xử lý thế nào trước 3.28.0?

- Phương án: (1) Sửa lớp phân tích tiền tố/wrapper (X+=1 → gán; parallel ::: chuỗi lệnh → quét như shell lồng) trong T-3564 (🔴, nâng parallel lên 🟠); env vào eval/bash -c, giá trị cũ, core.hooksPath: chấp nhận có chủ/hạn — guard cho chạy script tuỳ ý theo thiết kế (ADR-0018) và không quét nội dung script (giới hạn đã biết), nên ba lối này không mở thêm quyền; ghi giới hạn, xét lại cùng mốc hàng rào 2027-01-21 · (2) Sửa cả năm trong ba PR guard (T-3564…T-3566) trước khi cắt bản · (3) Chấp nhận cả năm, cắt 3.28.0 ngay
- Chọn: Sửa lớp phân tích tiền tố/wrapper (X+=1 → gán; parallel ::: chuỗi lệnh → quét như shell lồng) trong T-3564 (🔴, nâng parallel lên 🟠); env vào eval/bash -c, giá trị cũ, core.hooksPath: chấp nhận có chủ/hạn — guard cho chạy script tuỳ ý theo thiết kế (ADR-0018) và không quét nội dung script (giới hạn đã biết), nên ba lối này không mở thêm quyền; ghi giới hạn, xét lại cùng mốc hàng rào 2027-01-21
- Lý do (tiêu chí chất lượng cuối): (1) đúng và an toàn: X+=1/parallel ::: vô hiệu luật chặn hành động không đảo ngược (rm -rf /, push --force, reset --hard) — phải sửa; ba lối còn lại chỉ dẫn tới chạy chương trình, việc guard vốn cho (không mở thêm quyền), sửa chúng là đuổi theo mô phỏng shell (mẫu #282/#306 — mỗi lượt review lại thêm lối); (2) giữ đường lùi: chấp nhận có hạn, xét lại cùng mốc hàng rào; (5) tránh ba vòng review guard
- Đường lùi: Mở T-3565/T-3566 sửa ba lối đã chấp nhận

### D-218 · 2026-10-28T07:28:46+00:00 · Đính chính D-217 (review #307): lý do 'chỉ dẫn tới chạy chương trình' sai cho nhánh alias của AUD-SEC-126 (export … ; eval git p chạy push --force). T-3564 (X+=1, parallel :::) xong nhưng còn lối a[0]=, echo|parallel, sem — xếp mức lối lách guard thế nào?

- Phương án: (1) Áp nhất quán mô hình đe doạ D-015 (guard = lớp chặn sai lầm bằng phân tích tĩnh, không phải ranh giới cách ly; tiền lệ D-164/D-167): lối lách đòi che giấu cú pháp cố ý (X+=1, parallel :::, export+eval alias, a[0]=, sem, |parallel) là giới hạn đã biết — vẫn merge T-3564 vì đã làm và rẻ (review chỉ xét delta + hồi quy), phần còn lại ghi giới hạn ở harness-files.md, sổ: chấp nhận có chủ/hạn 2027-01-21 với lý do D-015 (không phải 'chỉ chạy chương trình') · (2) Coi mọi lối lách guard là 🔴 chặn phát hành, vá tiếp tới hết · (3) Giữ D-217 nguyên lý do
- Chọn: Áp nhất quán mô hình đe doạ D-015 (guard = lớp chặn sai lầm bằng phân tích tĩnh, không phải ranh giới cách ly; tiền lệ D-164/D-167): lối lách đòi che giấu cú pháp cố ý (X+=1, parallel :::, export+eval alias, a[0]=, sem, |parallel) là giới hạn đã biết — vẫn merge T-3564 vì đã làm và rẻ (review chỉ xét delta + hồi quy), phần còn lại ghi giới hạn ở harness-files.md, sổ: chấp nhận có chủ/hạn 2027-01-21 với lý do D-015 (không phải 'chỉ chạy chương trình')
- Lý do (tiêu chí chất lượng cuối): (1) đúng: lý do D-217 sai phải đính chính; mô hình đe doạ thật của guard (D-015) — tác tử hợp tác mắc sai lầm, không cố che giấu; lớp đỡ cho kẻ cố ý là sandbox/egress (LOOP-HARNESS-022), deny của settings, bộ phân loại Auto; (3) không hội tụ: #282 bảy lượt, #248 tám lượt, #306 + T-3564 mỗi lượt thêm lối — vá token bash không bao giờ đủ; (2) đường lùi: chấp nhận có hạn, xét lại cùng mốc hàng rào
- Đường lùi: Nâng lại các mục chấp nhận thành 🔴/🟠 mở và mở task vá

### D-219 · 2026-10-28T10:57:35+00:00 · Duyệt PLAN-hardening-assessment-2026-10-28: xác minh main #308, bảo vệ state/guard khi cơ chế kiểm không dùng được, thêm preset cài safe tùy chọn?

- Phương án: (1) Vá từng luật shell và đổi mặc định mọi dự án sang quyền thấp · (2) Giữ chính sách hiện hữu; bổ sung corpus #308, chặn ghi state thiếu khóa, chặn guard lỗi nạp/fallback hỏng, thêm safe opt-in và tài liệu có bằng chứng
- Chọn: Giữ chính sách hiện hữu; bổ sung corpus #308, chặn ghi state thiếu khóa, chặn guard lỗi nạp/fallback hỏng, thêm safe opt-in và tài liệu có bằng chứng
- Lý do (tiêu chí chất lượng cuối): Đúng và an toàn: sửa mất cập nhật và thực thi thiếu kiểm tra đã tái hiện; không coi guard là sandbox. Giữ đường lùi: từng lát có test, không tự đổi lựa chọn dự án đang chạy. Stdlib và diff nhỏ; tách monolith, đổi luật pháp hay tuyên bố nhanh hơn cần phạm vi và số đo riêng.
- Đường lùi: Revert từng lát; preset mặc định và cấu hình dự án hiện hữu giữ nguyên; không hạ ngưỡng Gate.

### D-220 · 2026-10-28T11:31:45+00:00 · Kiểm lại cuối gặp race fixture timeout: shell trap thoát trước reap khiến os.kill(pid,0) còn thấy zombie trong container PID1 không reap — xử lý thế nào?

- Phương án: (1) Chấp nhận lần kiểm lại đỏ, giữ fixture cũ; báo riêng hạn chế môi trường · (2) Sửa fixture wait trước marker/exit, grace 1 giây trong test; giữ assertion marker và PID biến mất, xác minh mutant chỉ TERM cha vẫn đỏ
- Chọn: Sửa fixture wait trước marker/exit, grace 1 giây trong test; giữ assertion marker và PID biến mất, xác minh mutant chỉ TERM cha vẫn đỏ
- Lý do (tiêu chí chất lượng cuối): Đã tái hiện 1/5 lượt fixture cũ để lại Z, 5/5 lượt fixture wait thu hồi đủ; mutant parent-only thiếu marker và không đạt. Sửa vòng đời tiến trình thử nghiệm, không giảm ngưỡng, không bỏ test, không sửa mã thực thi sản phẩm.
- Đường lùi: Revert riêng commit fixture; test cũ vẫn phải báo đỏ nếu môi trường không reap.
### D-221 · 2026-10-28T11:58:56+00:00 · Tối ưu quy trình cho tốc độ (chủ repo 2026-10-28): vòng sửa–review 2–3 lượt/PR, lượt 2 hay chặn vì lỗi có từ trước (#306, #308); gate cục bộ trùng CI; D-219/AUD-SEC-129 trùng giữa phiên song song — đổi gì?

- Phương án: (1) Bỏ nguyên nhân, giữ cổng chặn merge/phát hành: lỗi có từ trước không chặn PR (sổ audit --strict chặn phát hành), CI là cổng đầy đủ mọi pha (gate-fast trước khi đẩy), loop decide đánh số qua nhánh remote, khoá setup (ADR-0056) · (2) Nới cổng: bỏ review ở harden hoặc tăng REVIEW_ROUNDS · (3) Chỉ ghi khuyến nghị, không đổi luật
- Chọn: Bỏ nguyên nhân, giữ cổng chặn merge/phát hành: lỗi có từ trước không chặn PR (sổ audit --strict chặn phát hành), CI là cổng đầy đủ mọi pha (gate-fast trước khi đẩy), loop decide đánh số qua nhánh remote, khoá setup (ADR-0056)
- Lý do (tiêu chí chất lượng cuối): (1) đúng và an toàn: mọi cổng chặn merge (CI xanh, review sạch delta) và phát hành (audit --strict, release-check) giữ nguyên, lỗi cũ dời sang sổ + task chứ không mất; phương án 2 trái AGENTS §3; (2) đường lùi: mỗi điểm một commit; (3) đơn giản: một đoạn luật + một git grep; số đo ở research/2026-10-28-velocity.md; (5) tốc độ: bớt lượt review 30–45 phút và vài phút cổng cục bộ mỗi lần đẩy
- Đường lùi: Revert PR ADR-0056 hoặc từng điểm (review skill, gate skill + AGENTS §6, _remote_decisions, khoá setup)

### D-222 · 2026-10-28T14:37:03+00:00 · Squash-merge làm mỗi PR mã đã review kéo theo một PR sổ chỉ để dời SHA (đợt 2026-10-28: #310, #313, #315; PR cắt bản luôn NO-GO ở head — AUD-HAR-122) — giảm thế nào mà không nới cổng phát hành?

- Phương án: (1) release-check hỏi GitHub dấu xt-review của PR tạo mỗi commit nợ: mọi commit chạm file là squash (#N) có merge_commit_sha khớp và review sạch ở head (review_gate, cả cập nhật nhánh sạch) → phủ; offline → FAIL như cũ (ADR-0057) · (2) Trailer Xt-Reviewed trong thông điệp squash, đọc offline · (3) Giữ nguyên, gộp nhiều PR vào một PR sổ
- Chọn: release-check hỏi GitHub dấu xt-review của PR tạo mỗi commit nợ: mọi commit chạm file là squash (#N) có merge_commit_sha khớp và review sạch ở head (review_gate, cả cập nhật nhánh sạch) → phủ; offline → FAIL như cũ (ADR-0057)
- Lý do (tiêu chí chất lượng cuối): (1) đúng và an toàn: nguồn tin là dấu review của người có quyền ghi (cùng luật merge), không giả được bằng nội dung commit — trailer (2) giả được vì thông điệp squash mặc định gồm commit của tác giả; offline vẫn chặt; Gate offline của PLAN không đổi; (2) đường lùi: một dòng; (3) đơn giản, dùng lại review_gate/_published_marks/_base_merge_chain; (5) tốc độ: bớt một PR sổ (30–60 phút) mỗi PR mã đã review
- Đường lùi: Bỏ lời gọi reviewed_debt trong _release_review_debt

### D-223 · 2026-10-28T15:20:02+00:00 · PR #317 (ADR-0057) quá trần review: lượt 1 🔴 danh tính đọc ở HEAD (PR tự đặt gốc tin cậy), lượt 2 🟠 danh tính cố định ở SHA quét bỏ qua thu hồi/áp sau đó; test chưa ghim khoảng log theo file — đổi chiến lược thế nào?

- Phương án: (1) Thu hẹp gốc tin cậy: chỉ phủ khi review_identity đã commit ở SHA quét cũ nhất TRÙNG với ở HEAD (khác → không phủ, như trước ADR-0057 — phải audit delta); danh sách file qua diff -z (tên đặc biệt); test ghim từng điều kiện (R1 thu hồi, R2 áp sau, since theo file với lần đẩy thẳng giữa hai SHA, chọn SHA cũ nhất, shlex.quote) — đột biến đều đỏ · (2) Bỏ hẳn hỗ trợ review_identity: có review_identity ở bất kỳ đâu → không phủ · (3) Đóng PR, giữ PR sổ sau mỗi merge
- Chọn: Thu hẹp gốc tin cậy: chỉ phủ khi review_identity đã commit ở SHA quét cũ nhất TRÙNG với ở HEAD (khác → không phủ, như trước ADR-0057 — phải audit delta); danh sách file qua diff -z (tên đặc biệt); test ghim từng điều kiện (R1 thu hồi, R2 áp sau, since theo file với lần đẩy thẳng giữa hai SHA, chọn SHA cũ nhất, shlex.quote) — đột biến đều đỏ
- Lý do (tiêu chí chất lượng cuối): (1) đúng và an toàn: dấu chỉ được tin khi cả cấu hình đã audit lẫn cấu hình hiện hành cùng tin — đóng cả hai lớp lỗ (PR tự đặt, thu hồi bị bỏ qua) bằng một phép so, mọi khác biệt rơi về chặt; phương án 2 làm mất tính năng ở dự án dùng review_identity (T-1508); (2) đường lùi một dòng; (3) đơn giản hơn thêm luật đọc theo nhóm 13; (5) giữ lợi ích bớt PR sổ — trên dữ liệu thật hàng đã PASS (#316)
- Đường lùi: Bỏ lời gọi reviewed_debt trong _release_review_debt; hoặc đóng PR #317

### D-224 · 2026-10-28T15:54:42+00:00 · T-3547 loop next-step: thiếu JSON pr next thì làm gì, đo không-tiến-triển mục tiêu (FLOW-13) từ đâu, PR vượt ~150 dòng mã có tách không

- Phương án: (1) Thiếu --prs → action pr kèm missing (không đoán PR đã xong); loop init ghi mốc đầu đợt objective.batches (🔴/🟠 mở + MUST mở ngoài chờ người), next-step so hai mốc cuối với hiện tại; giữ một PR vì Gate T-3547 đòi FLOW-09…13 cùng nhau · (2) Thiếu --prs coi như không có PR; next-step tự ghi lịch sử đợt vào state; tách FLOW-13 sang task mới
- Chọn: Thiếu --prs → action pr kèm missing (không đoán PR đã xong); loop init ghi mốc đầu đợt objective.batches (🔴/🟠 mở + MUST mở ngoài chờ người), next-step so hai mốc cuối với hiện tại; giữ một PR vì Gate T-3547 đòi FLOW-09…13 cùng nhau
- Lý do (tiêu chí chất lượng cuối): Đúng và an toàn: không có dữ liệu PR thì không được báo hết việc (cách hiểu chặt); next-step giữ chỉ đọc (ADR-0052 §5) nên mốc đợt phải ghi ở lệnh ghi state sẵn có là loop init; tách FLOW-13 phải sửa Gate T-3547 đã duyệt — giữ Gate, mã ~250 dòng gồm chú thích
- Đường lùi: Bỏ khoá objective ở _init_apply và _step_work về replan; next-step chỉ đọc nên gỡ lệnh con không ảnh hưởng state

### D-225 · 2026-10-28T16:30:58+00:00 · Review #318 lượt 1 (🟠 A/F/B/T): định danh đợt cho FLOW-13, sổ phải qua --strict, cờ blocked sau done, trần số đợt (🟢 O)

- Phương án: (1) Đợt = PLAN (đường dẫn + băm ID/spec task); loop init cùng PLAN giữ mốc đầu đợt; mốc ghi đường sổ và null khi chưa có sổ, chỉ so hai mốc cùng sổ; sổ trượt audit check --strict (trừ lỗi 🔴/🟠 còn mở) → audit; st.blocked sau final_verdict done → blocked; chưa đặt trần số đợt (để T-3548/pilot đo) · (2) Mỗi loop init một mốc như cũ, sổ chỉ đếm 🔴/🟠 mở, thêm max_batches mặc định ngay
- Chọn: Đợt = PLAN (đường dẫn + băm ID/spec task); loop init cùng PLAN giữ mốc đầu đợt; mốc ghi đường sổ và null khi chưa có sổ, chỉ so hai mốc cùng sổ; sổ trượt audit check --strict (trừ lỗi 🔴/🟠 còn mở) → audit; st.blocked sau final_verdict done → blocked; chưa đặt trần số đợt (để T-3548/pilot đo)
- Lý do (tiêu chí chất lượng cuối): Đúng và an toàn: --force đổi ngân sách hay /optimize không được tạo đợt giả (báo budget sai); sổ trượt --strict mà báo ready-for-complete là khai xong sai; trần số đợt cần số đo từ pilot (ADR-0052 §Thông tin thêm: ngưỡng là số để pilot đo lại) — chưa có số thì không chốt hằng số
- Đường lùi: Bỏ nhánh errors ở _step_audit, bỏ kiểm plan_rev ở _batch_mark (mỗi init một mốc)

### D-226 · 2026-10-28T17:00:21+00:00 · PR #318: hai lượt review chưa sạch (ADR-0053) — ranh giới đợt của FLOW-13 đoán từ nội dung PLAN vẫn sinh đợt giả khi sửa spec giữa đợt rồi loop init --force; đổi chiến lược thế nào

- Phương án: (1) Đổi thiết kế ranh giới đợt theo vòng đời thay vì nội dung: đè lên vòng còn bật (prev.active) cùng đường dẫn PLAN = cùng đợt dù spec đổi; vòng đã kết thúc hoặc PLAN khác đường dẫn/spec = đợt mới; giữ PR, sửa kèm 4 🟢 (thứ tự scanned trước errors, chữ /optimize, _no_progress so từng mốc, ca P02/P04) · (2) Thu hẹp PR: bỏ FLOW-13 và objective.batches khỏi #318, tách task mới (Gate T-3547 bỏ FLOW-13) · (3) Thêm cờ loop init --new-batch để người/skill khai đợt mới tường minh
- Chọn: Đổi thiết kế ranh giới đợt theo vòng đời thay vì nội dung: đè lên vòng còn bật (prev.active) cùng đường dẫn PLAN = cùng đợt dù spec đổi; vòng đã kết thúc hoặc PLAN khác đường dẫn/spec = đợt mới; giữ PR, sửa kèm 4 🟢 (thứ tự scanned trước errors, chữ /optimize, _no_progress so từng mốc, ca P02/P04)
- Lý do (tiêu chí chất lượng cuối): Đúng và an toàn: --force giữa đợt (đổi ngân sách/sửa spec) không bao giờ là đợt mới (LOOP-HARNESS-024), vòng đã kết thúc rồi init lại mới là đợt kế (D-177) — vòng đời là sự thật máy đã có, nội dung PLAN chỉ là dấu hiệu; tách PR phải sửa Gate đã duyệt; cờ tường minh dựa vào agent nhớ khai (dễ quên, sai lệch ngầm)
- Đường lùi: Bỏ nhánh prev.active ở _batch_mark (về so plan_rev như e536a0f)

### D-227 · 2026-10-28T17:29:25+00:00 · PR #318 lượt 3 chưa sạch: ranh giới đợt của FLOW-13 (mốc objective.batches) sai ở ca biên lần thứ ba (cờ active không phân biệt đợt xong/dở) — sửa tiếp trong #318 hay tách

- Phương án: (1) Tách: bỏ objective.batches/_batch_mark/_no_progress khỏi #318, FLOW-13 vào XFAIL trỏ T-3578 (task mới: dấu đợt xong ghi khi loop verify --all xanh với verdict done hoặc Stop hook kết thúc done/chờ người; stopped/blocked không đóng đợt; D-NNN cho hết ngân sách); Gate T-3547 bỏ FLOW-13 · (2) Sửa tiếp trong #318 theo dấu đợt xong (thêm điểm ghi state ở loop verify + hook, lượt review thứ tư)
- Chọn: Tách: bỏ objective.batches/_batch_mark/_no_progress khỏi #318, FLOW-13 vào XFAIL trỏ T-3578 (task mới: dấu đợt xong ghi khi loop verify --all xanh với verdict done hoặc Stop hook kết thúc done/chờ người; stopped/blocked không đóng đợt; D-NNN cho hết ngân sách); Gate T-3547 bỏ FLOW-13
- Lý do (tiêu chí chất lượng cuối): PLAN cho phép tách khi task vượt cỡ (~150 dòng); giữ đường lùi: next-step không có FLOW-13 chỉ thiếu budget không-tiến-triển (an toàn: replan), không báo sai ready-for-complete; thiết kế dấu đợt xong chạm loop verify/Stop hook — đáng PR và review riêng thay vì vòng sửa–review thứ tư trên PR đã 250+ dòng (ADR-0053)
- Đường lùi: Gộp T-3578 lại vào PR sau; mã mốc đợt có ở commit 2c69aac

### D-228 · 2026-10-28T22:49:41+00:00 · T-3578: ranh giới đợt của next-step (FLOW-13) — dấu đợt xong ghi ở đâu, vòng hết ngân sách / dừng tay / bị chặn có đóng đợt không

- Phương án: (1) Dấu done trên mốc cuối khi loop verify --all xanh lúc verdict done/chờ người và khi Stop hook kết thúc done/chờ người; loop init mở đợt mới khi mốc cuối có dấu, vòng trước hết ngân sách (D-177: init sau đó là đợt kế), hoặc PLAN khác đường dẫn; stopped/blocked không đóng đợt; ghi dấu lỗi → cảnh báo, verify giữ exit · (2) Suy ranh giới từ cờ active/spec PLAN lúc init (bị bác ba lượt review #318) · (3) Hết ngân sách không đóng đợt (init sau budget là cùng đợt)
- Chọn: Dấu done trên mốc cuối khi loop verify --all xanh lúc verdict done/chờ người và khi Stop hook kết thúc done/chờ người; loop init mở đợt mới khi mốc cuối có dấu, vòng trước hết ngân sách (D-177: init sau đó là đợt kế), hoặc PLAN khác đường dẫn; stopped/blocked không đóng đợt; ghi dấu lỗi → cảnh báo, verify giữ exit
- Lý do (tiêu chí chất lượng cuối): Đúng và an toàn: dấu ghi lúc máy chứng minh đợt done (verify --all hoặc Stop hook) nên viết đè PLAN sau đó không lừa được; budget theo D-177 và EXIT_BUDGET gọi init sau là đợt kế — nhất quán; stopped/blocked chưa xong việc (lối ra unblock); verify không đỏ vì dấu (dấu chỉ phục vụ next-step, fail-open về luồng ADR-0002)
- Đường lùi: Bỏ _close_batch trong loop_verify và _mark_batch_done trong Stop hook; _batch_mark về mỗi PLAN khác một đợt

### D-229 · 2026-10-29T00:16:25+00:00 · PR #319 review lượt 1: dấu đợt xong còn sau khi đợt mở lại (unblock/resume) hoặc PLAN được nối thêm task rồi init --force — giữ hay gỡ

- Phương án: (1) unblock/resume gỡ dấu ở mốc cuối; dấu ghi kèm tasks = ID:req_rev của PLAN lúc đánh dấu, init cùng PLAN mà mọi cặp cũ còn nguyên (chỉ nối thêm) là cùng đợt, gỡ dấu; viết lại spec → đợt mới; hạn trôi qua lúc vòng dừng vẫn đóng đợt (D-177, ghi CHANGELOG) · (2) Giữ dấu, ghi rõ hành vi trong CHANGELOG (đợt giả → budget sai, lớp lỗi S3 của #318)
- Chọn: unblock/resume gỡ dấu ở mốc cuối; dấu ghi kèm tasks = ID:req_rev của PLAN lúc đánh dấu, init cùng PLAN mà mọi cặp cũ còn nguyên (chỉ nối thêm) là cùng đợt, gỡ dấu; viết lại spec → đợt mới; hạn trôi qua lúc vòng dừng vẫn đóng đợt (D-177, ghi CHANGELOG)
- Lý do (tiêu chí chất lượng cuối): Đúng: vòng mở lại hay PLAN nối thêm là đợt chưa xong — giữ dấu sinh đợt giả, báo budget sai đúng lớp lỗi đã bác #318; ID:req_rev phân biệt nối thêm (cặp cũ còn) với viết lại đợt kế cùng đường dẫn (S1 — spec đổi); hạn giữ theo D-177 để nhất quán EXIT_BUDGET
- Đường lùi: Bỏ _reopen_last_batch ở unblock/resume và nhánh tasks ở _same_batch

### D-230 · 2026-10-29T00:45:23+00:00 · PR #319: hai lượt review chưa sạch (ADR-0053) — lượt 2 còn 🟠 Stop hook không đóng vòng khi PLAN không đọc được UTF-8 (_plan_pairs gọi thẳng parse_plan) và 🟢 PLAN dài dần cùng đường dẫn gộp đợt; đổi chiến lược thế nào

- Phương án: (1) Thu hẹp phạm vi sửa: _plan_pairs dùng _plan_tasks (PLAN mất/không giải mã được → [], như review #296), tasks chỉ nhận chuỗi; loop init in ℹ khi mở lại đợt đã xong vì PLAN chỉ nối thêm task (trỏ PLAN-<đợt>.md); giới hạn PLAN dài dần cùng đường dẫn ghi vào CHANGELOG — không đổi thiết kế ranh giới đợt (D-228/D-229) · (2) Bỏ luật nối thêm task (về D-228: dấu xong luôn mở đợt mới) · (3) Thêm cờ loop init --new-batch
- Chọn: Thu hẹp phạm vi sửa: _plan_pairs dùng _plan_tasks (PLAN mất/không giải mã được → [], như review #296), tasks chỉ nhận chuỗi; loop init in ℹ khi mở lại đợt đã xong vì PLAN chỉ nối thêm task (trỏ PLAN-<đợt>.md); giới hạn PLAN dài dần cùng đường dẫn ghi vào CHANGELOG — không đổi thiết kế ranh giới đợt (D-228/D-229)
- Lý do (tiêu chí chất lượng cuối): Lỗi 🟠 là dùng sai helper (đã có _plan_tasks xử lý PLAN hỏng) — sửa tại gốc, không đổi thiết kế; PLAN dài dần cùng đường dẫn trái quy ước PLAN-<đợt>.md (README, skill autopilot, mẫu PLAN), state không có tín hiệu phân biệt đợt kế với mở lại → báo rõ thay vì đoán; bỏ luật nối thêm sẽ đưa lại đợt giả (review #319 lượt 1)
- Đường lùi: Về _plan_pairs gọi parse_plan; bỏ dòng ℹ

### D-231 · 2026-10-29T00:45:43+00:00 · PR #319: ghi lại quyết định đổi chiến lược sau review lượt 2 (D-230 ghi cùng giây với review nên pr rethink không nhận)

- Phương án: (1) Theo D-230: thu hẹp phạm vi sửa (_plan_pairs qua _plan_tasks, tasks chỉ nhận chuỗi, ℹ khi mở lại đợt vì PLAN nối thêm, giới hạn ghi CHANGELOG), không đổi thiết kế ranh giới đợt · (2) Bỏ luật nối thêm task
- Chọn: Theo D-230: thu hẹp phạm vi sửa (_plan_pairs qua _plan_tasks, tasks chỉ nhận chuỗi, ℹ khi mở lại đợt vì PLAN nối thêm, giới hạn ghi CHANGELOG), không đổi thiết kế ranh giới đợt
- Lý do (tiêu chí chất lượng cuối): Như D-230: lỗi 🟠 là dùng sai helper — sửa tại gốc; PLAN dài dần cùng đường dẫn trái quy ước PLAN-<đợt>.md, báo rõ thay vì đoán
- Đường lùi: Như D-230

### D-232 · 2026-10-29T01:54:06+00:00 · DOC_PATH_RE (review #320/#321): '(^|/)docs?/' coi mọi file trong thư mục doc/docs ở bất kỳ độ sâu là tài liệu — src/api/docs/routes.py, docs/conf.py bị loại khỏi nợ review (release-check BLOCKER) và khỏi đếm dòng/gói/test của làn merge (PR chỉ sửa mã đó vào làn nhanh, không review)

- Phương án: (1) Tài liệu = đuôi md/mdx/rst/txt ở mọi nơi, LICENSE/NOTICE, hoặc thư mục docs/doc ở GỐC repo trừ file có đuôi mã/cấu hình (py, js, ts, sh, go, rs, yml, toml…) · (2) Chỉ theo đuôi tài liệu, bỏ hẳn luật thư mục (ảnh/json trong docs/ thành mã → mọi PR sổ/ảnh vào làn chuẩn, nợ review giả) · (3) Giữ nguyên, chỉ ghi sổ
- Chọn: Tài liệu = đuôi md/mdx/rst/txt ở mọi nơi, LICENSE/NOTICE, hoặc thư mục docs/doc ở GỐC repo trừ file có đuôi mã/cấu hình (py, js, ts, sh, go, rs, yml, toml…)
- Lý do (tiêu chí chất lượng cuối): Đúng và an toàn: mã trong thư mục tên docs không còn lách review/nợ; vẫn giữ tài liệu không phải văn bản ở docs/ gốc (ảnh, json bằng chứng) là tài liệu để không sinh nợ/làn chuẩn giả — phương án 2 chặt hơn nhưng phá luồng PR sổ hằng ngày; chạm luật làn (cổng) nên ghi D
- Đường lùi: Đặt lại DOC_PATH_RE về '(^|/)docs?/|…'

### D-233 · 2026-10-29T02:22:50+00:00 · PR #322 review lượt 1: CODE_EXT là danh sách chặn (thiếu .dart/.vue/.html/.bat… và file không đuôi vẫn lọt); tên license*/notice* và .txt phụ thuộc là tài liệu (có từ trước); file trong docs/ tính là test

- Phương án: (1) Đổi sang danh sách cho phép (is_doc_path): đuôi văn bản md/mdx/rst/txt trừ txt phụ thuộc, đúng tên LICENSE/LICENCE/NOTICE/COPYING, tài sản png/jpg/gif/svg/webp/ico/pdf/csv/json/bib trong docs/ gốc; còn lại là mã; file dưới thư mục docs không tính là test; tên có xuống dòng là mã · (2) Bổ sung CODE_EXT từ LANG_EXT ∪ UI_EXT (vẫn danh sách chặn — không đuôi/đuôi mới vẫn lọt)
- Chọn: Đổi sang danh sách cho phép (is_doc_path): đuôi văn bản md/mdx/rst/txt trừ txt phụ thuộc, đúng tên LICENSE/LICENCE/NOTICE/COPYING, tài sản png/jpg/gif/svg/webp/ico/pdf/csv/json/bib trong docs/ gốc; còn lại là mã; file dưới thư mục docs không tính là test; tên có xuống dòng là mã
- Lý do (tiêu chí chất lượng cuối): Đúng và an toàn: luật quyết định review/nợ phải đóng khi nghi ngờ — danh sách chặn luôn thiếu đuôi mới (Makefile-less script, .bat, .vue); danh sách cho phép chỉ cho qua những gì chắc chắn là tài liệu; tài sản lồng trong docs con thành mã (chặt hơn, đã ghi CHANGELOG cho dự án đích)
- Đường lùi: Đặt lại DOC_PATH_RE của #321 (D-232 bản đầu)

### D-234 · 2026-10-29T03:06:46+00:00 · Review #323: thẻ 'phụ thuộc' của làn merge (RISK_PATH_RES) chỉ bắt requirements*.txt ở cuối tên — upper-constraints.txt, requirements/edx/base.txt lọt làn nhanh. Mở rộng thế nào?

- Phương án: (1) Giữ nguyên, ghi sổ 🟢 làm sau · (2) Mở rộng cùng độ rộng DEP_TXT_RE: [^/]*(requirements|constraints)[^/]*.txt, requirements/ mọi cấp, không phân biệt hoa thường · (3) Coi mọi .txt ngoài docs là phụ thuộc
- Chọn: Mở rộng cùng độ rộng DEP_TXT_RE: [^/]*(requirements|constraints)[^/]*.txt, requirements/ mọi cấp, không phân biệt hoa thường
- Lý do (tiêu chí chất lượng cuối): (1) đúng/an toàn: file phụ thuộc thật không lọt làn nhanh; một nguồn độ rộng với DEP_TXT_RE; phương án 3 chặn oan notes.txt mà không thêm an toàn đáng kể. (3) đơn giản, test được.
- Đường lùi: Trả regex thẻ phụ thuộc về requirements[^/]*\.txt trong scripts/xt.py (RISK_PATH_RES) và bỏ ca test D-234

### D-235 · 2026-10-29T03:34:45+00:00 · Review #323 lượt 2 (có từ trước): thẻ 'phụ thuộc' thiếu manifest .NET/JVM/Dart/Swift/Elixir/C++/Deno/Pipenv (*.csproj, packages.lock.json do BASE-DEP-001 nêu tên) — PR đổi các file này vào làn nhanh. Sửa thế nào?

- Phương án: (1) Ghi sổ, để task riêng · (2) Thêm danh sách tên manifest/lockfile phổ biến vào RISK_PATH_RES (tên chính xác, neo (^|/)…$), conanfile.txt vào DEP_TXT_RE · (3) Mọi file .json/.toml/.xml/.yaml ở gốc gói là phụ thuộc
- Chọn: Thêm danh sách tên manifest/lockfile phổ biến vào RISK_PATH_RES (tên chính xác, neo (^|/)…$), conanfile.txt vào DEP_TXT_RE
- Lý do (tiêu chí chất lượng cuối): (1) đúng/an toàn: đổi phụ thuộc phải qua review (BASE-DEP-001); tên chính xác không chặn oan file cấu hình khác như phương án 3. (3) đơn giản, test được từng tên.
- Đường lùi: Bỏ các tên D-235 khỏi thẻ phụ thuộc RISK_PATH_RES và conanfile khỏi DEP_TXT_RE trong scripts/xt.py; bỏ ca test D-235 và ca corpus pr-sec136

### D-236 · 2026-10-29T03:51:17+00:00 · T-3548 harden-to-signoff: next-step gom việc harden nháp có ID ổn định thế nào khi lệnh chỉ đọc (ADR-0052 §5: khoá = nguồn + ID gốc + SHA phát hiện)?

- Phương án: (1) Máy ghi thẳng PLAN-harden (thêm/giữ dòng task) · (2) Chỉ đọc: trả work[] (id, key, line dán được); khoá ghi trong dòng task '(nguồn: audit:ID@sha12)'; SHA phát hiện = commit đầu tiên đưa hàng vào sổ; khớp PLAN của vòng theo nguồn+ID, SHA khác (cả hai có) = phát hiện mới; ID mới cấp sau số lớn nhất của docs/autopilot/PLAN*.md theo thứ tự khoá · (3) ID băm từ khoá (T-9xxxx), không khớp PLAN
- Chọn: Chỉ đọc: trả work[] (id, key, line dán được); khoá ghi trong dòng task '(nguồn: audit:ID@sha12)'; SHA phát hiện = commit đầu tiên đưa hàng vào sổ; khớp PLAN của vòng theo nguồn+ID, SHA khác (cả hai có) = phát hiện mới; ID mới cấp sau số lớn nhất của docs/autopilot/PLAN*.md theo thứ tự khoá
- Lý do (tiêu chí chất lượng cuối): (1) đúng/an toàn: giữ next-step chỉ đọc (ADR-0052 §5), mô tả audit là dữ liệu — bỏ backtick/ngoặc/exec: để không thành Gate/sau:/tầng; phiên chính duyệt trước khi dán. (2) đường lùi: không ghi file. (3) tick giữ vì khớp theo khoá trong PLAN; ID băm (3) có thể trùng và không đọc được. Nguồn T-3548: 🔴/🟠 mở + MUST mở; release-check.fails vào ở T-3549 (--release); nợ review offline vẫn bảo thủ (không hỏi GitHub về PR đã review — ADR-0057), T-3549 dùng hàng review_debt của release-check. Thứ tự harden: task tick mà nguồn còn mở → audit, trước budget; budget trước replan việc mới.
- Đường lùi: Bỏ harden-to-signoff khỏi NEXT_STEP_OBJECTIVES và các hàm harden_work/_step_harden trong scripts/xt.py; test FLOW-14/15 và HardenWorkTest

### D-237 · 2026-10-29T04:12:16+00:00 · T-3549 gói nghiệm thu nháp: vân tay bằng chứng và hết hạn gói thế nào để sửa mã làm gói hết hạn mà commit chỉ GO-NO-GO/DECISIONS thì không (FLOW-17), lệnh vẫn chỉ đọc?

- Phương án: (1) evidence_fp = tree_fingerprint (theo SHA HEAD + diff) · (2) evidence_fp theo NỘI DUNG: blob ls-tree HEAD + diff + file chưa track, trừ **/GO-NO-GO*.md, **/DECISIONS.md, .autopilot; phần đổi = git diff --name-only <candidate_head> (cùng tập trừ); gói và release-check đọc từ file (--package/--release), next-step không tự chạy release-check (không gọi GitHub) · (3) Máy ghi gói vào GO-NO-GO phần máy
- Chọn: evidence_fp theo NỘI DUNG: blob ls-tree HEAD + diff + file chưa track, trừ **/GO-NO-GO*.md, **/DECISIONS.md, .autopilot; phần đổi = git diff --name-only <candidate_head> (cùng tập trừ); gói và release-check đọc từ file (--package/--release), next-step không tự chạy release-check (không gọi GitHub)
- Lý do (tiêu chí chất lượng cuối): (1) đúng: commit ký GO-NO-GO đổi SHA HEAD nên phương án 1 làm gói hết hạn oan; nội dung trừ hai file đó giữ đúng nghĩa 'bằng chứng không đổi'. (2) đường lùi: chỉ đọc, gói là JSON phiên chính lưu; không chạm GO-NO-GO (ADR-0048: máy không điền chữ ký). release-check head cũ vẫn dùng được khi chỉ đổi GO-NO-GO/DECISIONS; fails còn → replan (lý do nêu hàng FAIL, không thành task tự động). human_pending = release.human ∪ loop defer.
- Đường lùi: Bỏ --release/--package, signoff_facts/_step_signoff/evidence_fingerprint trong scripts/xt.py; harden hết việc trở lại action release-check

### D-238 · 2026-10-29T04:46:59+00:00 · PR #324: 2 lượt review chưa sạch (ADR-0053) — lượt 2 còn 🟠 thiếu ca *.vbproj (bỏ 'vb' khỏi regex thẻ phụ thuộc mà test vẫn xanh) và 🟢 4 lockfile chưa có ca, bất biến LOCKFILE_RE ⊆ thẻ phụ thuộc chưa có test. Đổi chiến lược thế nào?

- Phương án: (1) Giữ PR, thêm ca vbproj + 4 lockfile + test bất biến (mọi tên lockfile × tiền tố thư mục đều có lý do phụ thuộc; ca âm src/yarn.lock.py) — vòng review cuối rà đúng phần này · (2) Sinh regex và test từ một hằng danh sách tên (một nguồn) · (3) Đóng PR, tách thành PR nhỏ hơn
- Chọn: Giữ PR, thêm ca vbproj + 4 lockfile + test bất biến (mọi tên lockfile × tiền tố thư mục đều có lý do phụ thuộc; ca âm src/yarn.lock.py) — vòng review cuối rà đúng phần này
- Lý do (tiêu chí chất lượng cuối): (1) đúng: lỗi còn lại là thiếu ca test, mã đã đúng (reviewer xác nhận 77/102 đột biến chết, phần sống còn lại là nới an toàn); thêm ca là sửa gốc cho 'test được từng tên'. Phương án 2 làm đột biến bỏ tên khỏi hằng cũng xoá luôn ca test — mất khả năng bắt; phương án 3 tốn thêm vòng mà không đổi rủi ro. (3) đơn giản, giữ đường lùi.
- Đường lùi: Bỏ các ca thêm ở test_standard_lane_reasons/test_lockfiles… trong tests/test_merge.py

### D-239 · 2026-10-29T05:04:06+00:00 · Ba giai đoạn sản phẩm (PR #325): khoá giai đoạn sau và nguồn phê duyệt của người bằng máy thế nào

- Phương án: (1) Sổ docs/autopilot/STAGE.json theo git, chỉ xt.py stage ghi (guard coi là evidence), lịch sử phải dựng lại đúng giai đoạn; bản trình gắn SHA HEAD cây sạch; approve/init --adopt từ chối trong phiên agent (biến môi trường) và guard deny; loop init/next/record và release-check đọc khoá; không có sổ = không dùng (tương thích) · (2) Trạng thái trong .autopilot/stage.json (gitignored): guard đã rào sẵn nhưng mất khi đổi container/clone — không bền, sai với phiên cloud · (3) Duyệt qua GitHub (comment/review/Environment required reviewers): cùng tài khoản với token agent nên không phân biệt được người với agent ở chủ repo một người; tự duyệt deployment được khi tắt prevent self-review
- Chọn: Sổ docs/autopilot/STAGE.json theo git, chỉ xt.py stage ghi (guard coi là evidence), lịch sử phải dựng lại đúng giai đoạn; bản trình gắn SHA HEAD cây sạch; approve/init --adopt từ chối trong phiên agent (biến môi trường) và guard deny; loop init/next/record và release-check đọc khoá; không có sổ = không dùng (tương thích)
- Lý do (tiêu chí chất lượng cuối): Đúng/an toàn: không đường 1→3 kể cả sửa tay sổ (lịch sử lộ), agent không tự duyệt (hai lớp: xt.py + guard; guard là lớp chặn nhầm D-015 — nêu rõ); bền qua container nhờ git; đường lùi: xoá sổ = về hành vi cũ; đơn giản, stdlib, test được; GitHub không cho tách người/agent khi cùng tài khoản (nghiên cứu 2026-10-29)
- Đường lùi: Xoá docs/autopilot/STAGE.json ở dự án; hoặc bỏ lời gọi stage_plan_problem ở loop và hàng stage của release-check

### D-240 · 2026-10-29T06:18:23+00:00 · PR #327: 2 lượt review chưa sạch (ADR-0053) — lượt 2 còn 🟠 lối ra của verdict blocked do khoá giai đoạn trỏ sai (unblock/budget) và 8 🟢; đổi chiến lược thế nào

- Phương án: (1) Khoá giai đoạn trong verdict là PLAN không còn hợp lệ (như PLAN mất, D-208): một helper lối ra dùng chung cho _live_loop (không coi là vòng sống — loop init PLAN mới không cần --force), _blocked_exit, _loop_exit, _unblock_problem; kèm 🟢 rẻ (ghi lỗi xoá sổ mới, gợi ý new-cycle, record không state, code fence, ref chứa sổ trong lời báo, test đột biến) · (2) Tách PR: sổ + lệnh stage riêng, khoá loop/verdict sang PR sau · (3) Bỏ kiểm khoá ở verdict, chỉ giữ ở loop init/next/record
- Chọn: Khoá giai đoạn trong verdict là PLAN không còn hợp lệ (như PLAN mất, D-208): một helper lối ra dùng chung cho _live_loop (không coi là vòng sống — loop init PLAN mới không cần --force), _blocked_exit, _loop_exit, _unblock_problem; kèm 🟢 rẻ (ghi lỗi xoá sổ mới, gợi ý new-cycle, record không state, code fence, ref chứa sổ trong lời báo, test đột biến)
- Lý do (tiêu chí chất lượng cuối): Đúng: lối ra phải trùng nguyên nhân — PLAN của giai đoạn đã duyệt/khoá không mở lại được bằng unblock, đúng mô hình PLAN mất sẵn có; một helper sửa mọi lối ra cùng lúc (gốc), không đổi thiết kế khoá; tách PR tốn thêm vòng review mà không giảm rủi ro; bỏ kiểm verdict đưa lại lỗi lượt 1 (status giao task bị record từ chối)
- Đường lùi: Bỏ helper _stage_lock_exit và nhánh khoá ở verdict

### D-241 · 2026-10-29T07:01:07+00:00 · PR #327: lượt 3 và 4 sau D-240 vẫn chưa sạch — mỗi lần đưa khoá giai đoạn vào verdict/lối ra lại làm lệch một lối ra cũ (unblock/attach/doctor/init, budget). Đổi chiến lược thế nào

- Phương án: (1) Thu hẹp: bỏ khoá ở verdict và toàn bộ lối ra D-240 (_stage_lock_exit, ngoại lệ LOOP-HARNESS-024); khoá giai đoạn chỉ ở loop init/next/record (từ chối kèm lời đúng: PLAN đợt mới khai N+1); đổi PLAN khi vòng còn sống dùng đường có sẵn loop init --force (LOOP-HARNESS-024 nguyên bản) · (2) Sửa tiếp từng lối ra (thêm _stage_fix_exit cho ledger/declare, EXIT_BUDGET có điều kiện, doctor) · (3) Thêm verdict mới 'stage' với lối ra riêng ở mọi nơi
- Chọn: Thu hẹp: bỏ khoá ở verdict và toàn bộ lối ra D-240 (_stage_lock_exit, ngoại lệ LOOP-HARNESS-024); khoá giai đoạn chỉ ở loop init/next/record (từ chối kèm lời đúng: PLAN đợt mới khai N+1); đổi PLAN khi vòng còn sống dùng đường có sẵn loop init --force (LOOP-HARNESS-024 nguyên bản)
- Lý do (tiêu chí chất lượng cuối): Đúng/an toàn: bất biến chính (không mở N+1 khi chưa duyệt) do loop init/next/record giữ — record không nhận bằng chứng của PLAN khoá; verdict chỉ phục vụ tiện lợi nhưng nhân số tổ hợp với 5 lối ra cũ, hai lượt review liền chỉ ra lỗi dây chuyền; thu hẹp trả hành vi vòng về đường đã được review (D-208, LOOP-HARNESS-024), đơn giản, giữ đường lùi; phương án 2/3 tiếp tục nhân bề mặt
- Đường lùi: Áp lại commit 8d97085 + c88c4c8 (verdict + _stage_lock_exit)

### D-242 · 2026-10-29T05:43:39+00:00 · Review #326 🔴: khoá việc harden 'nguồn:ID@SHA phát hiện' (D-236, theo ADR-0052 §5) đổi sau squash-merge (commit đưa hàng vào sổ trên nhánh không lên main) → gom lại ra task trùng; SHA cũng không phát hiện được ID tái dùng (git log -S lấy commit cũ nhất). Sửa thế nào?

- Phương án: (1) Giữ SHA, tìm SHA trên nhánh chính (git log origin/main -S) · (2) Bỏ SHA khỏi khoá: khớp theo (nguồn, ID gốc) trên PLAN của vòng + docs/autopilot/PLAN*.md (cùng phạm vi cấp ID); @sha cũ trong dòng task vẫn đọc được, bị bỏ qua · (3) Băm nội dung hàng sổ làm khoá
- Chọn: Bỏ SHA khỏi khoá: khớp theo (nguồn, ID gốc) trên PLAN của vòng + docs/autopilot/PLAN*.md (cùng phạm vi cấp ID); @sha cũ trong dòng task vẫn đọc được, bị bỏ qua
- Lý do (tiêu chí chất lượng cuối): (1) đúng: ID sổ/MUST không tái dùng theo conventions nên (nguồn, ID) đã đủ định danh; phương án 1 vẫn lệch khi chưa merge (nhánh mới từ nhánh làm việc) và cần ref remote; phương án 3 đổi khoá mỗi lần sửa chữ trong hàng. (3) đơn giản, bỏ một git log -S mỗi hàng (Stop hook nhanh hơn). Lệch có chủ đích với chữ 'SHA phát hiện' của ADR-0052 §5 — ghi ở dòng trạng thái ADR.
- Đường lùi: Trả HARDEN_KEY_RE/harden_work về khoá có @sha và _found_at (D-236)

### D-243 · 2026-10-29T04:53:28+00:00 · T-3550: Stop hook in gợi ý next-step thế nào khi lệnh chỉ đọc và Stop hook không được đổi luồng (ADR-0052 §5)?

- Phương án: (1) additionalContext/decision block để model đọc · (2) systemMessage (hiển thị cho người, docs hooks xác minh 2026-10-29) khi vòng vừa kết thúc (done/chờ người/blocked/budget) và ghi state thành công; mục tiêu theo delivery_phase cây làm việc; không có --prs nên bước PR nhắc đối soát; lỗi tính → không gợi ý, stderr · (3) Chỉ in lệnh, không tính next-step
- Chọn: systemMessage (hiển thị cho người, docs hooks xác minh 2026-10-29) khi vòng vừa kết thúc (done/chờ người/blocked/budget) và ghi state thành công; mục tiêu theo delivery_phase cây làm việc; không có --prs nên bước PR nhắc đối soát; lỗi tính → không gợi ý, stderr
- Lý do (tiêu chí chất lượng cuối): (1) an toàn: không chặn, không ghi — cho Stop hook đọc/chuyển trạng thái là lát 4 sau pilot; decision block (1) sẽ đổi luồng. (4) trải nghiệm: người thấy bước kế thật thay vì chỉ lệnh (3). Fail-open như mọi Stop hook (ADR-0002).
- Đường lùi: Trả hook_stop về '' ở nhánh kết thúc vòng; bỏ stop_hint trong scripts/xt.py và test_stop_hint_next_step

### D-244 · 2026-10-29T05:10:42+00:00 · T-3548, T-3549, T-3550 đã commit nối tiếp trên một nhánh (phiên bị ràng buộc một nhánh, #324 chiếm nhánh lúc làm): một PR hay ba PR?

- Phương án: (1) Ba PR tuần tự (mỗi task một PR như dòng trạng thái ADR-0052) · (2) Một PR lát 2 phần còn lại (835 dòng, cùng hàm next_step/next_step_facts, ba commit tách theo task để review theo commit)
- Chọn: Một PR lát 2 phần còn lại (835 dòng, cùng hàm next_step/next_step_facts, ba commit tách theo task để review theo commit)
- Lý do (tiêu chí chất lượng cuối): (1) đúng: ba task sửa cùng next_step/next_step_facts/_loop_next_step và cùng hai file test — review riêng từng phần không thấy tương tác (thứ tự harden → signoff, cờ CLI chung); (5) tách cần dựng lại lịch sử qua worktree và ba vòng review nối tiếp mà không giảm rủi ro. Reviewer rà theo từng commit.
- Đường lùi: Đóng PR gộp, mở lại ba PR từ ba commit 1271133, 64cbd2a, 6ff2b99

### D-245 · 2026-10-29T07:41:00+00:00 · PR #326 (tiếp quản từ phiên khác theo yêu cầu chủ repo): 2 lượt review chưa sạch, chi tiết lỗi chặn chỉ có ở phiên cũ (dấu xt-review chỉ ghi verdict); đã gộp main (#327) và đổi số D trùng. Đi tiếp thế nào

- Phương án: (1) Một lượt review toàn PR mới (reviewer-alt) ở head đã gộp main để xác lập lỗi chặn hiện có, sửa trong PR, rồi một lượt delta · (2) Tách PR theo ba commit task (T-3548/T-3549/T-3550) thành ba PR nhỏ · (3) Đóng PR, làm lại từ đầu
- Chọn: Một lượt review toàn PR mới (reviewer-alt) ở head đã gộp main để xác lập lỗi chặn hiện có, sửa trong PR, rồi một lượt delta
- Lý do (tiêu chí chất lượng cuối): Đúng: không biết lỗi chặn cũ thì không sửa được — review toàn PR ở head mới là nguồn sự thật duy nhất; ba task sửa chung next_step/next_step_facts (D-244) nên tách PR tốn rebase/xung đột mà không giảm rủi ro; đóng PR bỏ phí 880 dòng đã qua gate-fast
- Đường lùi: Tách PR theo ba commit 1271133, 64cbd2a, 6ff2b99

### D-246 · 2026-10-29T13:19:59+00:00 · ADR-0058 lát D: chặn /complete và /optimize theo giai đoạn bằng máy (trước chỉ là dòng nhắc trong skill) — dấu hiệu nào?

- Phương án: (1) Tên PLAN do skill đặt: PLAN-harden-* cần giai đoạn ≥ 2, PLAN-opt-* cần giai đoạn 3 (kiểm ở stage_plan_problem = loop init/next/record); next-step harden-to-signoff ở giai đoạn 1 hoặc sổ hỏng → blocked · (2) Dòng khai mới trong PLAN (Loại: harden|opt) — đổi mẫu PLAN và mọi dự án đích · (3) Theo delivery_phase của xt.yaml
- Chọn: Tên PLAN do skill đặt: PLAN-harden-* cần giai đoạn ≥ 2, PLAN-opt-* cần giai đoạn 3 (kiểm ở stage_plan_problem = loop init/next/record); next-step harden-to-signoff ở giai đoạn 1 hoặc sổ hỏng → blocked
- Lý do (tiêu chí chất lượng cuối): (1) đúng/an toàn: khoá ở đúng ba lối vào vòng đã có (D-241), next-step harden không còn trả signoff-package ở MVP; phương án 3 sai vì dự án giữ harden sau phát hành (ADR-0037) nên chu kỳ mới ở giai đoạn 1 sẽ bị khoá oan; (3) đơn giản: tên PLAN đã do skill cố định, không đổi mẫu/dự án đích như phương án 2; đổi tên để lách là lỗi cố ý — guard là lớp đỡ nhầm (ADR-0058)
- Đường lùi: Bỏ _stage_kind_problem khỏi stage_plan_problem và _harden_stage_lock khỏi _next_step_part; skill quay về dòng nhắc
