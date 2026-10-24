# ADR-0029: Hai tầng executor có chuyển cấp, audit theo mốc, review chưa kết luận, cổng G7 máy đọc

- **Trạng thái:** Đã chấp nhận; audit theo mốc ở pha build thay bởi ADR-0033; mục 3 (reviewer khác họ) thay bởi ADR-0044
- **Trạng thái triển khai:** Đã triển khai trong repo — `scripts/xt.py` `EXEC_TIER_RE`/`executor_choice`/`milestone_done`/
  `_with_dispatch`, `loop record --executor`, `loop stats` (`escalated`, `escalation_rate`), `pr reviewed --inconclusive`
  (`review_gate` → `missing`), `release_check`/`cmd_release_check`; `.claude/agents/executor-deep.md`, `reviewer-alt.md`;
  test `tests/test_xt_core.py::LoopRecordBranchesTest.test_executor_tier_escalation_and_stats`,
  `test_milestone_done_marks_section_transition`, `tests/test_merge.py::PrNextCliTest.test_inconclusive_review_means_review_again`,
  `tests/test_xt_cli.py::ReleaseCheckTest`.
- **Ngày:** 2026-10-19
- **Làm rõ:** ADR-0008 (phiên chính tự duyệt), ADR-0009 (một phiên), ADR-0014 (PR mỗi lát), ADR-0028 (một điều kiện merge);
  quyết định D-075…D-078; nghiên cứu `research/2026-10-19-rapid-build-then-harden.md` (§7–§9).

## Bối cảnh

Chủ repo yêu cầu dự án đích **code nhanh nhưng sản phẩm vẫn chất lượng cao**, theo ba bản đề xuất (quy trình 5 giai
đoạn, kế hoạch nâng cấp PD-01…PD-12, phân vai Fable/Sonnet/Opus). Đối chiếu cho thấy khung đã có phần lớn cơ chế;
bốn chỗ thiếu thật:

1. Chỉ một `executor` (sonnet); không có tầng cho việc khó/rủi ro cao và không có luật chuyển cấp khi tầng mặc định đỏ
   lặp — `LOOP-ORCH-014` chỉ nói "đổi cách".
2. `audit.md` có quét theo diff nhưng không có nhịp "sau mỗi mốc" trong giao thức autopilot; `loop status` không biết
   khi nào một lát/mốc vừa xong.
3. `pr reviewed` chỉ có `--clean`/`--blocking`: reviewer hết ngân sách hoặc diff bị cắt chỉ còn cách im lặng hoặc báo chặn sai.
4. G7 có `blueprint-status --strict --run` và `GO-NO-GO.md` điền tay; không có một lệnh gom blueprint + sổ audit + kiểm
   lại cuối + cây git thành kết luận máy đọc.

Ràng buộc: tên model không được vào artefact commit (AGENTS.md §3, LOOP-HARNESS-027); reviewer phải khác họ model với
người viết (D-045, `LOOP-ORCH-005`); `max_same_failure: 3` và nguyên tắc "lần 2 đổi cách, lần 3 hỏi người" giữ nguyên;
chỉ stdlib Python ≥ 3.11; coverage 100 %.

## Quyết định

1. **Hai tầng executor, tên tầng không tên model** (D-075): `executor` (mặc định) và `executor-deep` (sâu) là hai agent
   file; model thật chỉ ở frontmatter `model:`. PLAN ghi `(exec: deep)` trong ngoặc của dòng task cho việc khởi đầu ở tầng
   sâu theo 4 khía cạnh (phức tạp · bất định · rủi ro · phạm vi ảnh hưởng). `parse_plan` đọc `tier`; `loop status --json`
   trả `executor`/`tier`.
2. **Chuyển cấp là một dạng "đổi cách" của `LOOP-ORCH-014`** (D-077): tầng mặc định đỏ `ESCALATE_AFTER = 2` lần cùng task
   trong vòng này (đếm từ `runs.jsonl`, bỏ lần chạy của tầng sâu) → `loop status` trả `escalated: true`, `executor:
   executor-deep`; gói bàn giao = diff + evidence lỗi + giả thuyết đã loại; `max_same_failure: 3` không đổi (lần chuyển cấp
   tiêu một lần thử). `loop record --executor <agent>` ghi agent vào evidence và `runs.jsonl`; `loop stats` có `escalated`,
   `escalation_rate`.
3. **Reviewer khác họ với agent đã viết** (D-076): thêm `reviewer-alt` (họ khác `reviewer`) cho diff của `executor-deep`
   hoặc của phiên chính cùng họ với `reviewer`. Reviewer không kết luận được trả INCONCLUSIVE; `pr reviewed --inconclusive`
   ghi sổ và đăng dấu `verdict=inconclusive`; `review_gate` coi là `missing` (cần review khác ở head), không phải `blocking`;
   `strict` bật như mọi review không sạch.
4. **Mốc = mục `##`/`###` của PLAN chứa task**: `milestone_done(tasks, t)` trả tên mục trước khi task kế là task đầu của
   mục mới và mọi task trước đã đóng; `loop status` ghi `milestone_done` và lý do "audit delta trước khi sang mốc kế";
   `audit.md` §1 thêm hàng "Sau mỗi mốc" (chỉ nhóm theo diff, 🔴/🟠 thành task mới trước mốc kế).
5. **`release-check`** (D-078): một lệnh gom `blueprint-status --strict --run`, `audit check --strict`, kiểm lại cuối
   (`final_check` khớp dấu vân tay cây), cây git sạch + HEAD, và số đề xuất "Khi chạy thật" chờ người → bảng
   PASS/FAIL/N-A có bằng chứng, `verdict` GO / GO (chờ người) / NO-GO, exit 1 khi NO-GO. Là phần máy của `GO-NO-GO.md`;
   chữ ký vẫn là người.
6. **Chất lượng theo pha** ghi thành quy tắc 6 của `lifecycle.md`: G5 sàn máy; G6 nhanh trên sàn (không audit toàn repo
   mỗi PR, không tối ưu không số); audit delta mỗi mốc; toàn diện ở G7. Cùng tiêu chí cuối, khác thời điểm kiểm.
7. **Phiên chính (điều phối) chạy model cao nhất sẵn có, không khả dụng thì Opus** — luật mở phiên (AGENTS.md §8, mẫu
   `CLAUDE.md`), không có cơ chế máy phát hiện; `author_model_family` phản ánh họ thật của phiên đang chạy.

## Lý do

- Routing "việc đơn giản → model rẻ hơn" và orchestrator-workers là mẫu Anthropic mô tả; khung chỉ thiếu *tầng*, không
  thiếu điều phối — thêm một agent file rẻ hơn một orchestrator mới, giữ ADR-0009 (phiên chính là vòng lặp).
- Đếm chuyển cấp bằng `runs.jsonl` đã có (`LOOP-DESIGN-024`) thay vì bộ đếm mới: không nhân đôi trạng thái; ngưỡng 2 là
  tham số khởi đầu, `loop stats` cho số để chỉnh.
- `inconclusive` → `missing` chứ không `blocking`: lỗi chặn là phát hiện có đường tái hiện; thiếu bằng chứng không phải
  phát hiện. Nhưng vẫn `strict` để PR không lọt làn nhanh sau một review không kết luận.
- `release-check` gom chứ không thay: mỗi nguồn vẫn một nhà (`blueprint-status`, `audit check`, `loop verify`); lệnh này
  chỉ đọc và kết luận, cùng nguồn cho JSON và Markdown (yêu cầu PD-08).
- Tên tầng trong PLAN giữ LOOP-HARNESS-027 và P5: đổi model = sửa một frontmatter.

## Hệ quả

- Dự án đích: chạy lại `install.py` để nhận `executor-deep.md`, `reviewer-alt.md`, `xt.py` mới; `AGENTS.md`/`CLAUDE.md`
  copy-if-absent — dự án cũ tự chép dòng §8 và dòng "Model/effort". PLAN cũ không có `exec:` vẫn chạy (tầng mặc định).
- `DOCTOR_AGENTS` giữ ba agent bắt buộc; hai agent mới là tuỳ chọn (thiếu → vòng lặp vẫn chạy một tầng, `loop status` vẫn
  trả tên agent — phiên chính giao `executor` nếu không có file).
- Guard không đổi: `pr reviewed --inconclusive` đi qua cùng đường đăng dấu (ADR-0027); `merge-gate`/steward coi
  `inconclusive` như chưa review.
- Chưa làm (chờ số từ `loop stats` và pilot): biến `delivery_phase` trong state (PD-02/PD-04), gate planner theo rủi ro
  (PD-05), máy kiểm protection của GitHub environment (PD-09).

## Đường lùi

Xoá hai agent file, bỏ `exec:` trong PLAN (parser bỏ qua), đặt `ESCALATE_AFTER` lớn; `release-check` và `--inconclusive` là
lệnh/cờ thêm, không đổi hành vi cũ — revert commit là đủ.

## Nguồn

- Anthropic, *Building effective agents* — routing, orchestrator-workers, "simplest solution possible":
  <https://www.anthropic.com/engineering/building-effective-agents> — xác minh 2026-10-19.
- DORA — *Working in small batches*, *Test automation*, *Pervasive security* — xác minh 2026-10-19
  (`research/2026-10-19-rapid-build-then-harden.md` §11).
- `seeker19110/stored` 23 §4.5 (thất bại 2× đổi cách, 3× hỏi người) qua `LOOP-ORCH-014`.
