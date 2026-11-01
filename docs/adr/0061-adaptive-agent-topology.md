# ADR-0061: Cấu hình agent theo loại việc — mặc định một agent chính tự làm, subagent theo độ độc lập, đo thời gian trước khi tăng

- **Trạng thái:** Đã chấp nhận (chủ dự án 2026-11-01: "sử dụng kiến trúc Adaptive Agent … cho Software Factory tự quyết theo
  độ độc lập của công việc … mặc định 1 agent sở hữu việc code và tích hợp … chỉ tạo subagent khi các tác vụ có thể chạy độc
  lập … 1 agent chính mạnh, có quyền tự gọi tối đa 2–4 subagent khi thật sự cần, đồng thời giới hạn vòng review và bảo đảm CI
  tự động"; phiên chính tự duyệt cách máy hoá theo tiêu chí chất lượng cuối, ADR-0008 — D-292)
- **Trạng thái triển khai:** Đang triển khai — lát 1 tài liệu (ADR này, `research/2026-11-01-adaptive-agent-topology.md`,
  `LOOP-ORCH-024`, bảng topology ở `orchestration-and-subagents.md`, `LOOP-DESIGN-024`, mẫu PLAN, skill `/autopilot` bước 5,
  README); lát 2–3 harness (`loop status.topology`, `executor: null` mặc định, `plan waves --max 4`, `loop stats
  time_to_green_hours`, `pr rethink` trần 1/PR) theo PLAN-upgrade-2026-11-01.
- **Ngày:** 2026-11-01
- **Thay một phần / làm rõ:** ADR-0045 — **thay** phần "harness giữ mặc định giao việc tới khi có số" (mặc định nay là
  `self` theo chỉ thị chủ dự án; dòng trạng thái ADR-0045 ghi); **giữ** tách agent chỉ vì context và phép đo của
  `LOOP-ORCH-020`, nay là điều kiện cho lần đổi **kế tiếp**. ADR-0029 (hai tầng executor — **giữ** cho hàng `parallel` và
  chuyển cấp); ADR-0053/0059 (ngân sách review — **siết**: `rethink` ≤ 1/PR, **trừ** PR cắt bản theo ADR-0059 §6/D-259);
  ADR-0031/0033/0056/0058 (audit theo mốc, CI là cổng đầy đủ, ba giai đoạn — không đổi).

## Bối cảnh

- Khung đang có hai mặc định trái với cách phiên thật vận hành: `loop status` trả `executor: executor` cho mọi task (giao
  subagent là mặc định), và `LOOP-ORCH-020` giữ mặc định đó "cho tới khi có ≥ 10 task/nhóm × 2 vòng" — điều kiện đặt ngày
  2026-10-24 chưa bao giờ tích luỹ được (`runs.jsonl` của clone = 0; PROGRESS "chờ" từ 2026-10-25). Trong khi đó phiên
  2026-10-31/11-01 (9 PR merge) vận hành đúng mô hình đề xuất: phiên chính tự viết mọi diff, chỉ giao `reviewer`/`researcher`/
  audit read-only, song song ≤ 3, không giao `executor` lần nào.
- Vòng review không có trần thật: ADR-0053 cho thêm lượt qua `pr rethink --decision D-NNN` không giới hạn số lần → PR #372
  (guard `$IFS#`) 7 lượt review đăng dấu (REST: 7 `xt-review … verdict=blocking`), mỗi lượt sửa lại mở lỗ mới, đóng không
  merge (D-284…D-286, D-288…D-291 ghi trên nhánh `seeker/wizardly-tesla-amsxmp` của PR đóng, không có trong sổ `main`). Chủ dự án yêu
  cầu "giới hạn vòng review, ưu tiên test tự động liên tục".
- Chủ dự án đưa bảng **loại việc → cấu hình** (sửa lỗi/tính năng nhỏ → 1 agent; xuyên module → agent chính + reviewer
  chuyên biệt; nhiều module độc lập → agent triển khai song song; audit lớn → một lượt audit rồi sửa batch) và 6 KPI
  (thời gian đến PR đạt CI · token/tính năng · số lần sửa lại · lỗi sau merge · tỉ lệ xong lần đầu · xung đột tích hợp).
  Khung đo được 4/6 bằng `loop stats` + `pr stats` + sổ audit (`do #N`); 2 KPI (token, xung đột) harness không thấy.
- Ràng buộc: `AGENTS.md` 7168/7168 B (không thêm chữ); `LOOP-ORCH-008` ≤ 5 là MUST@L có nguồn stored (trích dẫn `23 §4.5`
  hiện lệch — số ở 23 §2/03 §5, research §3 dòng 12; sửa ở T-3609, giữ ID); không
  tên model trong artefact (LOOP-HARNESS-027); mỗi PR pha harden ≤ ~150 dòng, review làn chuẩn.

## Phương án đã xét

1. **Giữ nguyên** (`executor` mặc định, chờ số đo `LOOP-ORCH-020`). Tốt: đúng chữ ADR-0045. Xấu: số không bao giờ tới vì
   không dự án nào chạy autopilot đủ dài; mặc định lệch thực tế vận hành; `rethink` vẫn không trần.
2. **Bỏ hẳn `executor`/`executor-deep`, chỉ một agent + reviewer.** Tốt: đơn giản nhất. Xấu: mất hàng "nhiều module độc
   lập" (chính đề xuất cũng giữ "agent triển khai" song song); mất chuyển cấp ADR-0029; đổi lớn không đo.
3. **(Chọn) Bảng topology máy đọc, mặc định `self`, giữ hai tầng cho `parallel`, trần đợt 4, `rethink` ≤ 1, thêm KPI thời
   gian.** Tốt: khớp đề xuất và thực tế vận hành; giữ đường lùi (một dòng `(topo: parallel; exec: deep)` trong PLAN đưa
   task về mặc định cũ); phép đo của `LOOP-ORCH-020` vẫn chạy (`executor: null` = nhóm tự làm) và có thêm trục thời gian để
   "chỉ tăng số agent khi thời gian giảm mà lỗi không tăng". Xấu: `topo:` là lời khai của người lập PLAN; số "4" và "1 lượt
   rethink" là khởi điểm do chủ dự án đặt, không có nguồn ngoài (ghi rõ, đo rồi chỉnh).

## Quyết định

1. **Bảng topology** (`orchestration-and-subagents.md` §"Cấu hình theo loại việc", `LOOP-ORCH-024` SHOULD): `self` (mặc
   định) · `review` · `parallel` · `audit`. PLAN ghi `(topo: …)`; thiếu = `self`. Chọn hàng theo thứ tự hỏi: độc lập file +
   hợp đồng rõ → `parallel`; xuyên module/bảo mật/kiến trúc/dữ liệu → `review`; audit/kiểm thử độc lập → `audit`; còn lại `self`.
2. **Harness** (lát 2–3): `loop status --json` trả `topology`; `executor: null` khi `self`/`review`/`audit`; `parallel` trả
   tầng theo `exec:` (mặc định `executor`, `exec: deep` → `executor-deep`); chuyển cấp sau 2 lần đỏ giữ nguyên (ADR-0029) —
   task `self` đỏ 2 lần → `executor-deep` (vẫn nhóm tự làm theo lần chạy đầu, D-172). `plan waves --max` mặc định 4
   (`LOOP-ORCH-008` giữ trần cứng 5). `loop stats` thêm `time_to_green_hours` (trung vị/P95, từ `started` lần chạy đầu tới
   `finished` lần xanh đầu của task). `pr rethink` tối đa `max_rethink` lần/PR (xt.yaml, mặc định 1); hết → `pr next` trả
   `split-or-close` (tách PR nhỏ hơn hoặc đóng, ghi sổ phần đã học). **Không áp** cho PR cắt bản (`is_release_pr`): giữ
   ADR-0059 §6/D-259 — rà tới sạch, mỗi lượt thêm một D-NNN.
3. **KPI** (`research/2026-11-01-adaptive-agent-topology.md` §4): báo cáo cuối lát ghi 6 KPI — 4 từ máy (`loop stats`:
   `first_pass_rate_*`, `runs_to_green`, `time_to_green_hours`; `pr stats`: `lead_time_hours`, `first_push_green`, `pushes`,
   `reverts`; sổ audit: phát hiện `do #N`), 2 ghi tay có nhãn "chưa đo bằng máy" (token từ `/usage`; số lần `update-branch`/
   xung đột). Điều kiện tăng số agent: theo `LOOP-ORCH-020` (≥ 10 task/nhóm × 2 vòng) **và** thời gian tới xanh/lead time giảm
   mà xanh lần đầu không giảm, `reverts`/`do #N` không tăng.
4. **Không đổi**: `LOOP-ORCH-001/003/005/008/009` (điều phối một tầng, quyền ⊆, reviewer cao hơn người viết, ≤ 5, không giao
   hành động đối ngoại); ADR-0037 (pha build: `pr next` không đòi review; `(topo: review)` là review tự giao theo §Hệ quả ADR-0037); `/audit`, `/complete`; ba giai đoạn (ADR-0058).

## Hệ quả

- Dự án đích: PLAN cũ không có `topo:` → mọi task thành `self`; muốn giữ cách cũ ghi `(topo: parallel)` cho task cần
  `executor`. Skill `/autopilot` bước 5 đọc `topology`. `plan waves` đợt nhỏ hơn (4) — PLAN > 4 task độc lập chạy thêm đợt.
- Phép đo `LOOP-ORCH-020` tiếp tục và có dữ liệu thật hơn vì nhóm tự làm là mặc định; nhóm giao chỉ còn `parallel`.
- Review: PR hết lượt + 1 rethink → tách/đóng thay vì lặp; bài học #372 thành luật.

## Đường lùi

- Lát 1 (tài liệu): revert PR; ID `LOOP-ORCH-024` → `MAY` + "Ngừng dùng" nếu bỏ.
- Lát 2–3 (harness): revert PR của lát; PLAN ghi `(topo: parallel)` cho mọi task = hành vi mặc định cũ; `max_rethink: 0`
  = không trần (hành vi ADR-0053).

## Nguồn

- Nhận định của chủ dự án 2026-11-01 (nguyên văn trong phiên; tóm tắt ở research note).
- `research/2026-11-01-adaptive-agent-topology.md` (đối chiếu đề xuất ↔ khung; KPI ↔ harness; nguồn sống đọc 2026-11-01).
- `research/2026-10-24-single-agent-loop.md`, ADR-0045, ADR-0029, ADR-0053, ADR-0059; PR #372 đóng không merge (D-284…D-286, D-288…D-291
  trên nhánh `seeker/wizardly-tesla-amsxmp`) — bằng chứng vòng review không trần.
- Nguồn sống (đọc 2026-11-01, chi tiết §3 của research note): Anthropic *Harness design for long-running application development*
  (2026-03-24: "find the simplest solution possible, and only increase complexity when needed"; evaluator chỉ đáng khi việc vượt khả
  năng solo); claude.com ROI Claude Code (2026-10-27: "cost per task", PR cycle time, review iterations/rework per PR); Claude Code docs
  sub-agents/agent-teams (đồng thời mặc định 20, lồng 3 tầng, "Start with 3-5 teammates" — trần 4/5 của khung là tự đặt, chặt hơn);
  OpenAI Codex docs (song song cho việc đọc nhiều, thận trọng với việc ghi); DORA metrics (lead time, change fail rate, rework rate).
