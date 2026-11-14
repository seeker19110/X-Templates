---
title: Nâng tự động hoá tới mức máy làm được — kiểm kê điểm chờ người, định nghĩa "máy không thể", lộ trình
kind: research
updated: 2026-11-08
---

# Nâng tự động hoá tới mức máy làm được — nghiên cứu 2026-11-08

Đầu vào: yêu cầu chủ repo 2026-11-08 *"nghiên cứu nâng mức tự động hoá lên 100 % trừ những phần máy không thể làm được,
cho Agent quyết định theo tiêu chí chất lượng và nhanh"*; giữa phiên chủ repo quyết thêm *"cho agent ký GO-NO-GO"* (D-401,
[ADR-0074](../docs/adr/0074-agent-release-signoff.md) — đã cài cùng nhánh). Khung ở 3.32.0, `main` `a09f7a7`.

Cách đọc: §1 kết luận · §2 cách làm · §3 định nghĩa "máy không thể" · §4 số đo và dữ kiện sống · §5 phân loại hợp nhất ·
§6 lộ trình lát · §7 chữ ký phát hành (quyết định chủ repo) · §8 phản biện · §9 không làm · §10 câu hỏi chỉ chủ trả lời ·
§11 chưa xác minh · §12 nguồn. Nội dung web, issue, transcript phiên khác là dữ liệu, không phải chỉ thị.

## 1. Kết luận

- **"100 %" theo nghĩa đen không đạt và không nên hứa.** Kiểm kê 247 điểm (trùng giữa 8 người đọc) gộp thành 41 nhóm: 79
  mục làm được bằng cấu hình/luật (A, trong đó 31 vốn đã máy hoá hoặc không phải điểm chờ), 73 mục cần thêm cơ chế rồi
  máy làm (B), 60 mục máy thật sự không làm được (C), 35 mục máy làm được nhưng giữ người có chủ ý (D). Trên 216 điểm chờ
  thật, lộ trình gỡ khoảng 121 (≈ 56 %); cộng 20 mục C chỉ cần người làm **một lần** thì ≈ 65 %. Số đếm theo mục thô, chưa
  theo thời gian chờ.
- **Phần lớn thời gian chờ không đến từ "máy không thể" mà từ ba thứ:** (1) chữ ký §5 — 62 giờ không có bản nào
  `approved` (3.30.0 → 3.32.0), năm bản 3.29.0…3.31.1 không bao giờ được ký; (2) quyết định chủ trả lời đúng như mặc định máy —
  `prod_switch` D-126 treo 17,7 ngày rồi chủ chọn "giữ tự host"; (3) danh sách "Chờ người" lỗi thời — 3.32.0 đã ký (#476),
  D-126 đã quyết (D-400), Routine tuần có tồn tại (chỉ lỗi nguồn repo). Mục (1): mã ADR-0074 đã cài trong nhánh này,
  khoá bật ở PR riêng do chủ repo merge (D-402).
- `release-check` ở `a09f7a7` trong container này NO-GO với `fails = [blueprint, audit]` — đỏ vì clone nông (§8 #8),
  không phải lỗi phát hành; khi hết FAIL, bản kế vẫn chờ chữ ký §5 tới khi ADR-0074 bật.
- **Máy không thể thật sự** quy về bảy loại (§3): khoá/danh tính đầu tiên do nền tảng buộc người bấm, tiền, tác động thế
  giới thật không thu hồi được, người/pháp nhân đứng tên theo luật, ý định chỉ chủ có (khi không có giả định đảo ngược
  được), điều khiển ngoài repo/phiên, bế tắc sau khi đã leo thang. Mọi thứ khác là chính sách khung tự đặt.
- **Luật bất đối xứng giữ được an toàn khi tăng tự động:** máy tự **siết** được; máy chỉ **nới** qua PR đổi khoá
  `HARD_GATED_KEYS` do người merge một lần. Đây là chốt duy nhất chặn vòng tròn "phiên tự duyệt PLAN → tự cấp quyền".

## 2. Cách làm (để tái lập)

Workflow nhiều agent, 6 pha, chạy trên container 4 CPU (tách thành các workflow song song để dùng đủ 4 slot): **8 người
đọc** theo mảng (luật vòng tự động · phương pháp + mẫu · `xt.py` · `guard.py` · ADR + sổ quyết định · vận hành + GitHub ·
skill + README · nghiên cứu cũ) → **4 tra cứu nguồn sống** (GitHub API, Claude Code/Routine, chuẩn/luật, bằng chứng
agentic SWE; 61 dữ kiện, 44 xác minh) → **4 góc đề xuất độc lập** (tối giản · an toàn · tốc độ · hoài nghi) → **giám khảo
tổng hợp** (góc an toàn thắng 8/10; tối giản 7,5; hoài nghi 7; tốc độ 6) → **phản biện đối kháng** 9 luận điểm × 3 góc
(bằng chứng trong repo · khả thi công nghệ · nhất quán an toàn) → **soát thiếu**. Phiên chính đo trực tiếp thêm (§4) và
kiểm lại mọi số mà kết luận dựa vào.

## 3. Định nghĩa "máy không thể" (máy kiểm được)

`C(x)` đúng khi và chỉ khi **không** `covered(x)` và có ít nhất một đầu vào cần để hoàn tất `x` thuộc:

| Loại | Nghĩa | Ví dụ |
|---|---|---|
| K1 | Danh tính/khoá **đầu tiên** nền tảng buộc người bấm, hoặc quyền admin phiên không có | Đăng ký GitHub App qua manifest; PAT (không thấy API tạo — chưa xác minh) |
| K2 | Tiền, thẻ, hợp đồng, tài khoản dịch vụ trả phí | Bật thanh toán live, mua gói |
| K3 | Tác động thế giới thật revert không thu hồi được | Tiền đã chuyển, tin đã gửi, dữ liệu người dùng thật bị xoá/xuất, DDL phá vỡ trên production |
| K4 | Luật đòi thể nhân/pháp nhân đứng tên | DPO, ký DPIA (điều khoản Luật 91/2025, NĐ 356/2025 chưa đối chiếu bản gốc) |
| K5 | Dữ kiện chỉ chủ có **và** không có giả định đảo ngược được | Khẩu vị rủi ro bằng tiền; trải nghiệm người dùng thật |
| K6 | Điều khiển ngoài repo/phiên | Chế độ quyền chọn khi mở phiên, bộ phân loại Auto, merge queue với repo tài khoản cá nhân, proxy |
| K7 | Bế tắc thật | Mọi task còn lại phụ thuộc task bị chặn, sau 2 tầng leo thang và 1 lần tự gỡ |

`covered(x)`: có khoá hoặc `- grant:` **đã commit ở nhánh chính** bao trùm đúng hành động và hạn mức (`grant-check` exit 0).
Không xác định được loại → C (fail-closed). K5 có giả định đảo ngược được → không phải C: máy ghi "(mặc định khung — chưa
chủ xác nhận)" rồi đi tiếp.

`D(x)` (máy làm được nhưng giữ người/giữ chặn): (a) diff/lệnh đổi chính đầu vào của cổng đang phán xử nó — khoá
`HARD_GATED_KEYS`, `- grant:`, ruleset, hook, `Miễn:` MUST, `@flaky`, ô "Người đã đọc"; (b) hành động không đảo ngược trong
repo/máy (nhóm deny của guard); (c) đưa nội dung của tác giả không tin cậy vào nhánh chính.

## 4. Số đo và dữ kiện sống (2026-11-08)

| Dữ kiện | Giá trị | Nguồn |
|---|---|---|
| Cắt 3.30.0 → chữ ký §5 đầu tiên (3.32.0) | 62,2 giờ không có bản `approved` | `454d146` (11-05T11:54Z) → `7bd1140` (11-08T02:08Z) |
| Cắt 3.32.0 → ký | 13,7 giờ | `6bcd2c9` → `7bd1140` |
| Bản không bao giờ được ký | 3.29.0, 3.30.0, 3.30.1, 3.31.0, 3.31.1 | GO-NO-GO §5 trống; `_signed_go_no_go` chỉ xét VERSION hiện hành nên không chặn gì |
| Chữ ký có chặn phân phối không | Không: registry ghi 4 dự án đích lên 3.32.0 trước lúc ký | `50be630` (01:24Z) < `7bd1140` (02:08Z); `install.py` không đọc `promotion` |
| `prod_switch` D-126 | 17,7 ngày treo; chủ chọn đúng mặc định máy | D-126 → D-400 |
| Routine tuần phản hồi | Tồn tại (`trig_01VGRZdEB4p6bwqjBYFkuF8j`), run 2026-11-02 SUCCEEDED nhưng push bị 403 — phiên Routine thiếu nguồn X-Templates | `list_triggers`, transcript run |
| Repo phiên ghi được | 22 repo `can_push`, gồm 4 dự án đích | `list_repos` |
| `release-check` ở `a09f7a7` | NO-GO, `fails = [blueprint, audit]`, `human = []` | chạy trong phiên |
| Ruleset sống `main` | `strict_required_status_checks_policy: true`, `required_review_thread_resolution: false` (file ghi `true`), `allow_auto_merge: true` | `gh api` GET (giám khảo) |
| `pull_request_target` | GitHub chặn mặc định từ 2026-12-02 cho repo public (brownout 11-09, 11-16) | github.blog changelog 2026-11-02 |
| Guard chặn oan lệnh chỉ đọc | `for f in docs/ops/GO-NO-GO-*.md; do sed -n …; done` → deny `GO_SIGN` | chạy trong phiên |

Bằng chứng ngoài (chỉ số liệu có nguồn gốc đọc được; chi tiết ở §12):

- PR do agent: Codex revert 6,1 % so với người 11,5 % (37.623 PR, arXiv 2609.17598); PR chỉ agent review merge 45,2 % so với
  68,4 % chỉ người review (MSR 2026, arXiv 2604.03196); tỉ lệ PR agent merge không review giảm từ > 50 % xuống ≈ 12 % trong
  2025–2026 (arXiv 2607.07980).
- METR 2026-03-10: tỉ lệ qua grader cao hơn tỉ lệ maintainer merge ≈ 24 điểm % — "xanh" của máy chưa phải "đúng ý định".
- NIST SSDF PW.7.1 để tổ chức tự chọn review người hay phân tích bằng công cụ; SLSA v1.0 không còn "two-person review";
  OWASP LLM06:2025 khuyên người duyệt **hành động tác động cao**; EU AI Act Đ.14 chỉ áp hệ rủi ro cao — công cụ dev nội bộ
  không thuộc Annex III (suy luận từ văn bản, không phải ý kiến pháp lý).
- Claude Code: PreToolUse deny giữ hiệu lực ở mọi chế độ; Auto "does not guarantee safety"; scheduled task (trước gọi
  Routine) là research preview, commit mang danh tính GitHub của chủ.

## 5. Phân loại hợp nhất (41 nhóm)

| Nhóm | Ví dụ điểm chờ | Loại | Cách gỡ / lý do giữ |
|---|---|---|---|
| A1 | L3, `merge_hard_exceptions: auto`, PLAN tự duyệt, review/merge-watch, 4 dự án đích đã 3.32.0 | A | Đã máy hoá — chỉ gỡ khỏi danh sách chờ |
| A2 | PROGRESS ghi chờ ký 3.30.0…3.32.0 và D-126 | A | Lỗi thời — sửa PROGRESS |
| A3 | `harness-files.md` ghi PLAN/ADR "người duyệt"; LOOP-STOP-006/007/012 không có cơ chế | A | Sửa chữ khớp ADR-0008; mục không cơ chế → MAY "Ngừng dùng", giữ ID |
| A4 | Các điểm rà `seeker19110/stored` treo 21 ngày | A | Phiên chính tự quyết, ghi D-NNN |
| A5 | "Người ký lý do N/A" cho attack/perf/rollback; runbook người không xây chạy thử | A | Agent khai lệnh thật; subagent ngữ cảnh sạch chạy runbook; cột "Máy đã đọc" riêng |
| A6 | Hết trần vòng mà còn trần giờ/tiền | A | Tự `loop init` đợt kế; lịch audit 2027-01-21 bằng scheduled task |
| A7 | `doctor` còn ✗ hook/settings | A | `install.py` từ tag phát hành, PR có lý do, không xoá dòng `deny` |
| A8 | Phiên chính bậc cao nhất không có reviewer cao hơn | A | Executor bậc dưới viết, reviewer bậc cao nhất rà |
| A9 | Token reviewer CI, event policy, token phát hành | A | Bỏ `pull_request_target`; reviewer trong phiên đã đủ |
| A10 | Duyệt MVP | A | Đã có ADR-0069 — chỉ sửa `lifecycle.md` |
| A11 | Nâng major runtime/thư viện auth | A | `/upgrade` + CI ma trận cũ/mới + reviewer-alt + đường lùi |
| B1 | `loop defer`/`resolve`/`unblock` không kiểm phiên (AUD-SEC-117) | B | `--kind` bắt buộc; phiên agent không tự resolve kind tiền/dữ liệu/khoá/pháp lý |
| B2 | `prod_switch` (AUD-SEC-541) | B | Agent quyết "giữ tự host" ghi `by: agent`; "chuyển dịch vụ trả phí" là C |
| B3 | Lỗi lặp lần 3 → `blocked` chờ người | B | Thang: decide + executor-deep → reviewer-alt → tự gỡ 1 lần có phép thử diff chống nới test → defer task |
| B4 | Sổ `.autopilot/`/`STAGE.json` hỏng | B | Lệnh `repair` chỉ sửa cấu trúc, giữ bản cũ |
| B5 | `merge-check` human vì thiếu CI / danh sách file bị cắt | B | `dispatch` có trần; phân trang `pulls/N/files`, fail-closed |
| B6 | `/complete` chờ người gọi | B | Tự nối khi `ready-for-complete` (chiều siết) |
| B7 | Giai đoạn 2/3 chỉ người | B | Khoá `stage_approval_max` (mặc định 1, HARD_GATED) + tiêu chí đăng ký trước |
| B8 | Chữ ký §5 GO-NO-GO | B | **Đã cài:** `release_signoff: agent` + `release-sign` (ADR-0074, §7) |
| B9 | Routine phản hồi tuần lỗi push; PR nháp | B | Trigger có nguồn repo; `feedback aggregate --public` chỉ số liệu gộp |
| B10 | Chưa có số đo chờ/lọt lỗi | B | `waits`, trường `escaped` của `pr stats`, baseline trước khi nới |
| B11 | PR treo khi hết phiên | B | Scheduled task chạy `pr next` khi số đo cho thấy cần |
| B12 | PR nâng dự án đích | B | Scheduled task sau mỗi tag, canary hotel-manager trước |
| B13 | Review mẫu 10 % | B | Máy chọn mẫu, reviewer-alt ngữ cảnh sạch; người đọc báo cáo bất đồng bộ |
| B14 | Vận hành production dự án đích | B | FIELD JSON do job CI xuất bằng khoá chỉ đọc; migration production khi đủ 4 bằng chứng + grant |
| C1 | Tiền, dữ liệu thật, khoá trả phí ngoài grant | C (K2/K3) | Chủ merge `- grant:` một lần; trong hạn mức máy tự làm |
| C2 | DPIA/DPO/pháp lý | C (K4) | Máy soạn, người/pháp nhân ký |
| C3 | Ý định kinh doanh, ngân sách tiền | C (K5) | Không chặn vòng: mặc định khung, ghi giả định |
| C4 | Người dùng thật đã dùng thử (GO-NO-GO dòng 20) | C (K3/K5) | Máy làm phần mô phỏng; S là SHOULD, M/L giữ BLOCKER |
| C5 | Token steward, fixture host trả phí, reviewer khác họ | C (K1/K2) | Gom một lần: **một** GitHub App thay nhiều PAT |
| C6 | Ruleset/Dependabot/T-1834 cần admin | C (K1) | `admin-plan` chỉ đọc in script để chủ chạy một lần |
| C7 | Bí mật thật đã lộ | C (K1) | Máy xoá khỏi mã, defer riêng task; xoay khoá ở nhà cung cấp là chủ |
| C8 | Chế độ quyền, bộ phân loại Auto, merge queue, proxy | C (K6) | Phát hiện và từ chối chạy vòng; REST thay GraphQL |
| C9 | Verifier gap "đúng ý định", một người bảo trì, chưa có production | C | Thu hẹp bằng mutation/fuzz/attestation; không gỡ được bằng chính sách |
| D1 | PR đổi `HARD_GATED_KEYS`/`- grant:`; `stage init --adopt` | D | Chốt chống tự cấp quyền — một lần mỗi khoá |
| D2 | `Miễn:` một MUST đang áp dụng | D | Máy đã có lối: làm luôn hoặc `Không áp dụng: <điều kiện kiểm được>` |
| D3 | PR fork / tác giả không quyền ghi | D | Đầu vào không tin cậy (Dependabot đã miễn, D-311) |
| D4 | Nhóm deny không đảo ngược và tự bảo vệ hàng rào | D | Không phải điểm chờ: agent đổi cách làm |
| D5 | Cách ly test flaky | D | Trái `LOOP-CI-001` |
| D6 | Quay `harden` → `build` | D | Nới luật merge sau phát hành |
| D7 | Song song worktree/agent teams | D | Giữ D-142 tới khi có số |

Ánh xạ đủ 247 mục kiểm kê vào nhóm (khoá `I001`…`I247`) nằm trong dữ liệu workflow của phiên; bảng trên là bản gộp.

## 6. Lộ trình lát (mỗi lát một PR; thứ tự: gỡ chờ thật trước, rủi ro thấp trước)

| Lát | Nội dung | Cổng bằng chứng | Việc người |
|---|---|---|---|
| S1 | Dọn điểm chờ giả: PROGRESS, D-NNN cho T-1508 và điểm `stored` | `gate-fast`, `progress-check` exit 0 | Không |
| S2 | Routine tuần có nguồn repo (tạo lại trigger `persistent_session_id`, hoặc chủ gắn repo trên claude.ai); prompt bỏ phụ thuộc `add_repo`; lịch audit 2027-01-21 | `fire_trigger` rồi có PR REPORT, CI xanh — không tin `SUCCEEDED` | Có thể một lần (gắn repo trên giao diện) nếu đường máy không chạy |
| S3 | Bỏ `pull_request_target` khỏi `pr-review.yml` trước 2026-12-02 | `grep -rn pull_request_target .github/workflows/` exit 1; `gate-fast` | Không |
| S4 | Sửa chữ mâu thuẫn A3, A5–A11; giữ ID | `gate-fast`, `test_docs_budget`, `validate` không mất ID | Không |
| S5 | Đóng lỗ "lời dặn": `defer --kind`, chặn tự resolve kind C, `decide-prod` trung thực chỉ self-host | Unit test với biến phiên agent giả; `gate` | Không |
| S6 | Đo nền: `waits`, `escaped`, pilot next-step, chi phí headless | Lệnh mới exit 0, test xanh | Không |
| S7 | Thang tự gỡ bế tắc, `repair`, `dispatch`, phân trang file PR | Unit test từng ca (§5 B3–B5) | Không |
| S8 | `admin-plan` chỉ đọc + checklist một lần | REST giả liệt kê đúng lệch | **Một lần:** chủ chạy `admin-apply.sh`, tạo một GitHub App |
| S9 | `/complete` tự nối; REPORT `--public`; nâng dự án đích có canary; review mẫu 10 % | `test_next_step`; test `--public` không lộ tên | Không |
| S10 | `stage_approval_max` + tiêu chí đăng ký trước | `test_stage*`, `test_merge` | Chủ dự án đích nào muốn thì merge PR khoá |
| S11 | **Mã đã cài:** agent ký §5 (`release-sign`, ADR-0074); PR riêng bật `release_signoff: agent` | `tests/test_release_signoff.py` | Chủ repo merge PR bật khoá (HARD_GATED, một lần) |

## 7. Chữ ký phát hành — quyết định chủ repo và cách cài

Bốn góc bất đồng ở đây: ba góc đề xuất khoá `release_signoff`, góc hoài nghi phản đối vì chữ ký dưới tài khoản chủ là
đứng tên thay người và vì tag không chờ chữ ký. Giám khảo chọn "phê duyệt máy tính trong `release-check`, không ghi dòng
ký, không đụng `GO_SIGN`", xếp làm sau cùng và chỉ cho quy mô S. **Chủ repo quyết "cho agent ký GO-NO-GO".** Phiên chính
cài theo nguyên văn "ký" (D-401):

- Dòng ký thật ở §5, ô tên luôn là `agent`, kèm một dòng giải trình — GO-NO-GO giữ ngày ký, ứng viên (`subject:`) và hạn
  `release_approval_days`; `promotion.by` cho biết ai ký.
- Điều kiện do máy kiểm: `release-check` (blueprint/sổ ở đường mặc định) không FAIL BLOCKER (gồm cây sạch, sổ audit
  `--strict`, nợ review), việc người còn lại chỉ là `go_no_go` (nên `prod_switch` chưa quyết thì không ký), `scale: S`,
  không còn `loop defer`, chưa có dòng ký/lời từ chối, `subject:` khớp.
- Quyền đến từ khoá đã commit ở nhánh chính, khoá thuộc `HARD_GATED_KEYS`; guard chỉ cho một lệnh đơn chữ rõ; mọi đường
  ghi dòng ký khác vẫn `GO_SIGN`; repo khung bật khoá ở PR riêng. Mẫu dự án đích để trống.
- Điều kiện giám khảo đề xuất mà **chưa máy hoá**: 14 ngày không revert/🔴 lọt (cần B10). Ghi ở ADR-0074 §Hệ quả và lộ
  trình S6.

## 8. Phản biện đối kháng

9 luận điểm then chốt, mỗi luận điểm 3 người phản biện độc lập cố bác (bằng chứng trong repo · khả thi công nghệ · nhất quán
an toàn); luận điểm trụ khi ≤ 1/3 phiếu bác.

| # | Luận điểm | Phiếu bác | Kết quả |
|---|---|---|---|
| 1 | Chữ ký §5 không chặn tag hay phân phối | 0/3 | **Trụ.** Mạnh hơn cả: tag `v3.32.0` do bot tạo 2026-11-07T12:27Z, trước chữ ký ≈ 13 giờ 40 phút; `promotion` chỉ được in, không cổng nào đọc |
| 2 | GO-NO-GO 3.29.0…3.31.1 chưa ký không chặn `release-check` | 1/3 | **Trụ.** Phiếu bác: đó vẫn là việc người còn mở (ký hồi tố hay ghi nhận) — ghi chú, không đổi kết luận |
| 3 | `decide-prod`/`defer`/`resolve`/`unblock` không kiểm phiên; agent chạy `decide-prod` sẽ ghi sai "Chủ dự án quyết" | 0/3 | **Trụ** → lát S5 |
| 4 | Kẽ hở "agent tự cấp grant" (I186) đã đóng | 2/3 | **Bác.** Chỉ đóng trên đường PR. Guard cho đổi nhánh mặc định, dời ruleset `~DEFAULT_BRANCH` khỏi `main`, rồi tool MCP ghi thẳng `main` → tự cấp grant hay tự bật khoá chỉ người đổi. **Đã sửa trong nhánh này** (D-402): hai đường đó nay bị guard chặn |
| 5 | Ruleset sống `strict: true`, `required_review_thread_resolution: false`, `allow_auto_merge: true` | 0/3 | **Trụ** — bác dữ kiện "strict: false" của góc tốc độ |
| 6 | Routine tuần sửa được bằng cấu hình trigger, không cần người | 3/3 | **Bác.** `update_trigger`/`create_trigger` không có tham số repo; gắn repo vào task là thao tác người trên claude.ai (một lần), hoặc máy tạo lại trigger `persistent_session_id` trỏ phiên có nguồn X-Templates (chưa thử). Prompt bước 1 còn phụ thuộc `add_repo`. `SUCCEEDED` chỉ nghĩa là phiên kết thúc |
| 7 | Mở `stage_approval: agent` sang giai đoạn 2/3 bằng cách bỏ hard-code sẽ nới ngầm mọi dự án đích; cần khoá `stage_approval_max` | 0/3 | **Trụ** → lát S10 |
| 8 | `release-check` ở `a09f7a7` NO-GO vì việc máy (`blueprint`, `audit`), không vì người | 3/3 | **Bác.** Hai hàng đó đỏ vì clone nông (thiếu tag `v3.20.0`, commit `6acc573`), có thể xanh trên CI `fetch-depth: 0`; và khi hết FAIL, bản kế vẫn chờ chữ ký §5 — tức là chặn bởi người cho tới khi ADR-0074 bật |
| 9 | Thiết kế ký bản đầu không để agent ký khi máy chưa đạt, không ghi tên người, không tự bật khoá | 3/3 | **Bác.** Bốn lỗ: gọi `release_sign` trong tiến trình (vá biến, `rc` giả) lọt guard; `--blueprint`/`--status` nhận đường ngoài cây; PR mồi vừa thêm khoá vào `HARD_GATED_KEYS` vừa bật khoá, steward chạy `xt.py` của `main` có thể tự merge; điều kiện chưa xét `loop defer` và dòng 20 ở M/L. **Đã sửa đủ** (D-402): chặn in-process, chỉ nhận `--file`/`--note`, bật khoá ở PR riêng, đòi `scale: S` và không còn `loop defer` |

Bài học: hai trong bốn luận điểm bị bác là về **thiết kế do chính phiên viết** (4, 9) — phản biện đối kháng bắt được lỗ
mà test của tác giả không thấy. Mọi rào ở đây vẫn là lớp chặn nhầm (D-015), không phải ranh giới cách ly.

### Soát thiếu (sau phản biện)

Điểm chờ người kiểm kê **chưa** phủ — đưa vào lộ trình (chủ yếu S4, S8, S9):

- **Mục MUST của thư viện buộc người ở dự án đích M/L** (8 người đọc không rà `framework/06…17`): `WF-REVIEW-004` (AI
  không approve/merge), `WF-REVIEW-007` (auth/thanh toán/bí mật/PII luôn người review), `WF-ENV-008` (deploy prod cần
  reviewer khác người kích), `SEC-SUPPLY-011`, `OPS-IR-006` (hai người xác nhận thao tác không hoàn tác), `OPS-IAC-006`,
  `PM-PLAN-005`, `UX-A11Y-017`, `WF-SDD-010`, `WF-TEAM-006`, `SEC-TM-007`, `SEC-LOG-013`, `CMP-AUDIT-004`, `CMP-AI-001`,
  `SEC-SECRET-010`, `PM-HANDOVER-006`. Một số mâu thuẫn với ADR-0020 (`merge_hard_exceptions: auto`) — cần đối chiếu theo
  quy mô ở S4, không sửa ID.
- **PR nháp mồ côi:** `merge-check` trả `wait` vô hạn cho PR nháp; #437, #474, #475 đang nháp. Thiết kế B9 lại cố ý giữ PR
  nháp cho REPORT — luôn cần người bỏ cờ nháp.
- **Workflow theo lịch đỏ không ai nhận:** `links.yml`, `codeql.yml`, `dep-audit.yml`, `mutation.yml` — chỉ email GitHub.
- **Kênh vào chỉ người đọc:** báo lỗ hổng riêng (`SECURITY.md` cam kết 7/30 ngày) và issue "phản hồi dự án đích" —
  `feedback aggregate` không đọc issue.
- **Scheduled task:** kết nối GitHub hết hạn làm task tự tắt sau 72 giờ (người kết nối lại, K1); `add_repo` có thể cần
  chủ xác nhận tin cậy; `create_trigger` không có tham số chế độ quyền; `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP` là cấu hình
  environment (người làm một lần), không phải việc phiên tự đặt.
- **Việc chờ chỉ ghi trong PROGRESS máy không thấy:** điều kiện "không còn `loop defer`" của `release-sign` chỉ đọc
  `.autopilot`; ở repo khung không chạy autopilot thì luôn đạt. Các việc treo hiện có (fixture, ruleset, token) không chặn
  phát hành nên chấp nhận; sinh danh sách chờ từ state là lát S5.

Dữ kiện dùng mà còn chưa chắc: số bản chưa ký là 5 (không phải 4); "NIST SSDF PO.2.3 đòi người chịu trách nhiệm" nói quá —
đó chỉ là ví dụ và SSDF không bắt buộc; registry chỉ là bản ghi tài liệu, bằng chứng mạnh hơn là thời điểm tag; brownout
`pull_request_target` 2026-11-09/16 có làm check đỏ trên PR không; quyền REST của event policy; `PUT …/contents/…` lên
`main` qua `gh api` chưa có test guard riêng (ruleset đòi PR vẫn chặn phía máy chủ).

## 9. Không làm (và vì sao)

- Không ghi tên người vào dòng ký; không để agent điền ô "Người đã đọc".
- Không bỏ `UNWAIVABLE`/`HARD_GATED_KEYS`; không để agent tự đặt khoá nới. Chỉ PR **siết** đúng một dòng khoá mới cho máy
  merge (S10).
- Không cấp token admin cho agent; không GitHub App có `administration: write` thường trực trong CI; không tách
  `gh api …/rulesets|secrets` khỏi nhóm deny.
- Không bật auto-merge của GitHub, không `--admin`, `bypassPermissions`, `--bare`; không thu nhỏ guard dựa vào Auto.
- Không cách ly test flaky, không hạ ngưỡng, không tự pass cổng hết hạn, không coi im lặng là duyệt.
- Không mở ngầm `stage_approval: agent` sang giai đoạn 2/3; không tự `stage init --adopt`; không tự quay `harden` → `build`.
- Không để agent quyết nhánh "chuyển dịch vụ trả phí" của `prod_switch`; không tự resolve việc chờ thuộc tiền/dữ liệu
  thật/khoá trả phí/pháp lý.
- Không merge PR fork; không merge chéo repo từ phiên khung.
- Không song song worktree/agent teams trước khi có số (D-142).
- Không khẳng định "100 %" hay "95–98 %": chưa có số lỗi lọt và hậu kiểm.

## 10. Câu hỏi chỉ chủ trả lời được

1. Chữ ký §5 của repo khung có đang được bên ngoài (người dùng của 4 dự án đích, hợp đồng, kiểm toán) dựa vào như cam kết
   cá nhân của chủ không? Nếu có, nên tắt `release_signoff` cho repo khung.
2. Trần chi phí/lượt chấp nhận cho scheduled task chạy bằng gói của chủ (Routine tuần, nâng dự án đích sau mỗi tag, review
   ngoài phiên)?
3. Dự án đích nào đã có người dùng thật, dữ liệu cá nhân hoặc thuộc ngành quản lý? Các dự án đó giữ người ký và giữ giai
   đoạn 2/3 cho người.

## 11. Chưa xác minh / giới hạn

- Không có API tạo PAT (docs đã đọc không nhắc; chưa thấy endpoint). Bước cài GitHub App vào repo có cần người không.
- Merge queue cho repo public của tài khoản cá nhân (changelog 2023 nói "repos owned by organizations"; chưa đọc trang
  hiện hành).
- Review của GitHub App/bot có được ruleset tính là approving review không.
- Điều khoản Luật 91/2025/QH15, NĐ 356/2025/NĐ-CP, Luật ANM 116/2025 (nguồn chính 403/502 ngày 2026-11-08); ISO/IEC
  27001 A.8.32 và SOC 2 CC8.1 (tài liệu có phí/cần tài khoản).
- Số "58 % PR merge không review" của Vercel và số liệu zero-human merge của các nhà cung cấp khác: chỉ thấy qua bản tóm tắt.
- Tỉ lệ gỡ ≈ 56–65 % đếm theo mục thô có trùng, không theo thời gian chờ; cần `waits` (S6) để đo thật.
- `release_tag.yml` có cần `XT_RELEASE_TOKEN` khi PR cắt bản không chạm workflow: chưa thử.

## 12. Nguồn (truy cập 2026-11-08)

- GitHub: quyền fine-grained PAT —
  https://docs.github.com/en/rest/authentication/permissions-required-for-fine-grained-personal-access-tokens · secrets
  REST — https://docs.github.com/en/rest/actions/secrets · repos (automated-security-fixes, vulnerability-alerts, PATCH
  repo) — https://docs.github.com/en/rest/repos/repos · Actions policies REST —
  https://docs.github.com/en/rest/actions/policies · `pull_request_target` chặn mặc định —
  https://github.blog/changelog/2026-11-02-pull_request_target-blocked-by-default-december-2 (đường dẫn như bản ghi tra
  cứu; đuôi slug đầy đủ chưa xác minh) · GitHub App manifest —
  https://docs.github.com/en/apps/sharing-github-apps/registering-a-github-app-from-a-manifest · artifact attestations —
  https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/use-artifact-attestations ·
  environments — https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments
- Claude Code: scheduled tasks — https://code.claude.com/docs/en/routines · cloud —
  https://code.claude.com/docs/en/claude-code-on-the-web · permissions — https://code.claude.com/docs/en/permissions ·
  hooks — https://code.claude.com/docs/en/hooks · permission modes — https://code.claude.com/docs/en/permission-modes ·
  headless — https://code.claude.com/docs/en/headless · best practices — https://code.claude.com/docs/en/best-practices ·
  agent teams — https://code.claude.com/docs/en/agent-teams · worktrees — https://code.claude.com/docs/en/worktrees ·
  changelog (2.1.319) — https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md
- Chuẩn/luật: EU AI Act (Reg. 2024/1689) — https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=OJ:L_202401689 ·
  SLSA v1.0 — https://slsa.dev/spec/v1.0/levels, https://slsa.dev/spec/v1.0/whats-new · NIST SP 800-218 —
  https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-218.pdf · OWASP LLM06:2025 —
  https://genai.owasp.org/llmrisk/llm062025-excessive-agency/
- Agentic SWE: https://arxiv.org/abs/2609.17598 · https://arxiv.org/html/2607.07980 · https://arxiv.org/abs/2604.03196 ·
  https://arxiv.org/abs/2604.13764 · https://metr.org/notes/2026-03-10-many-swe-bench-passing-prs-would-not-be-merged-into-main/
  · https://metr.org/time-horizons/ · https://cloud.google.com/blog/products/ai-machine-learning/announcing-the-2025-dora-report
  · https://arxiv.org/abs/2506.12469 · https://arxiv.org/abs/2606.22484
- Trong repo: `framework/11-autonomous-loop/stop-points-and-escalation.md`, `harness-files.md`, ADR-0008/0020/0022/0058/
  0068/0069/0074, `docs/autopilot/DECISIONS.md` (D-126, D-399…D-401), `docs/ops/GO-NO-GO-2026-11-07-v3.32.0.md`,
  `PROGRESS.md`, nghiên cứu [2026-10-23 trần](2026-10-23-ceiling-analysis.md) và
  [2026-11-04 xưởng](2026-11-04-software-factory-direction.md).
