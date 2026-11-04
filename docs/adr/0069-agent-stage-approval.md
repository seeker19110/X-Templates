# ADR-0069: Agent tự nghiệm thu giai đoạn sản phẩm khi `xt.yaml` khai `stage_approval: agent`

- **Trạng thái:** Đã chấp nhận 2026-11-04 (chủ dự án: "cho phép Agent quyết định khi nào đã đạt và tuyên bố đạt MVP";
  phiên chính chốt cách làm theo tiêu chí chất lượng cuối, ADR-0008 — **D-352**; ghi lúc đầu là D-342 rồi D-347, đánh số lại khi gộp
  `main` vì #438 đã dùng D-342 và #439 đã dùng D-347).
- **Trạng thái triển khai:** đã làm cùng PR: `scripts/xt.py` (`stage_agent_approval`, `stage approve` trong phiên agent,
  `stage_facts.agent_approval`, `next-step` trả `stage-approve`), `.claude/hooks/guard.py` (`agent_stage_approval`,
  `_plain_approve`, `_stage_approve_denied`), `tests/test_stage_agent_approval.py`, mẫu `framework/templates/xt.yaml`.
- **Ngày:** 2026-11-04.
- **Thay một phần:** ADR-0058 §Quyết định 3 ("chỉ người duyệt") — chỉ cho `stage approve` khi khoá có hiệu lực. **Giữ:**
  sổ `STAGE.json`, `submit`/`reopen`/`new-cycle`, khoá PLAN, hàng `stage` của `release-check`, `init --adopt` chỉ người,
  guard chặn ghi tay sổ, mọi dạng lệnh mờ.
- **Liên quan:** ADR-0008 (phiên chính tự duyệt), ADR-0026 (ghi tay bằng chứng), ADR-0040 (`delivery_phase` đọc cả cây lẫn
  bản đã commit), ADR-0058, ADR-0068 (xưởng: ràng buộc "GO của máy · nghiệm thu · quyền deploy · đã deploy" vẫn là bốn việc),
  `LOOP-STOP-024`, AUD-SEC-155.

## Bối cảnh

ADR-0058 (chủ dự án 2026-10-29) đặt điểm chờ người ở ranh giới mỗi giai đoạn: `stage approve` từ chối khi tiến trình mang
biến phiên agent, guard chặn lệnh đó, chủ dự án phải gõ lệnh ở terminal **ngoài** phiên agent — chủ chỉ dùng app thì MVP kẹt
ở `awaiting_approval` (ADR-0058 §Hệ quả). Phân tích 2026-11-04 (research xưởng §9, workflow đo tốc độ) cho thấy đây là chi
phí thời gian duy nhất mà ba giai đoạn thêm vào dự án đích; chủ dự án quyết đổi: **agent được quyết định và tuyên bố đạt
MVP**. Câu hỏi: cho phép thế nào mà không mất lớp chặn nhầm (D-015) cho dự án vẫn muốn người duyệt, và không để phiên tự
cấp quyền cho mình?

## Yếu tố quyết định

1. Đúng và an toàn: quyền phải đến từ cấu hình **đã commit ở nhánh chính**, không từ cây làm việc của chính phiên; bản được
   duyệt phải đúng bản đã trình và còn nguyên (không file đổi sau khi trình); `init --adopt` (công nhận lịch sử) vẫn là việc
   của người; dạng lệnh mờ vẫn bị chặn.
2. Đường lùi một dòng: bỏ khoá hoặc đặt `human` là về ADR-0058.
3. Đơn giản: dùng lại `_stage_changed` (vân tay bản trình), `_committed_xt_text`, mẫu `build_phase` của guard; không sổ mới.
4. Tốc độ dự án đích: hết điểm chờ người giữa chu kỳ khi chủ dự án chọn thế.

## Các phương án đã cân nhắc

1. **Khoá `stage_approval: human|agent`** có hiệu lực khi cả cây lẫn bản đã commit ở nhánh chính khai `agent`; agent chỉ
   duyệt bản trình còn nguyên; `init --adopt` và dạng mờ giữ luật cũ; mặc định mã `human`, mẫu dự án đích đặt `agent`.
2. Bỏ hẳn kiểm người/agent ở `stage approve` và luật `STAGE_APPROVE` của guard.
3. Giữ ADR-0058; agent chỉ ghi đề xuất duyệt vào sổ, người vẫn `approve`.

## Quyết định

Chọn **phương án 1** (D-352).

- **`xt.yaml`**: `stage_approval: agent` — agent được `stage approve`; vắng/khác → chỉ người (ADR-0058). Có hiệu lực khi
  **cả** xt.yaml ở cây làm việc **lẫn** bản đã commit ở nhánh chính của remote (`origin/HEAD` → `origin/main` →
  `origin/master`, ref đầu tiên đọc được) đều khai; không đọc được/không có remote → chỉ người.
- **`xt.py stage approve` trong phiên agent** (`stage_agent_approval` đúng): duyệt đúng bản đã trình (`--sha` khớp) **và**
  bản còn nguyên trên cây (`_stage_changed` = `[]`; file đổi, vân tay lệch hay SHA mất → từ chối, lối ra `stage reopen` rồi
  trình lại); sự kiện `approve` ghi `by: "agent"`, `session`, `note` (tiêu chí MVP đã đạt). Người duyệt như cũ.
- **`loop next-step`**: `stage_facts` thêm `agent_approval`; MVP đã trình → `stage-approve` (đối chiếu tiêu chí MVP của
  PLAN với bản trình: đạt → `approve`, không đạt → `reopen`) thay `wait-approval`; `stage-submit` và khoá `/complete`
  (`_harden_stage_lock`) ghi lối ra tương ứng. Không có khoá → hành vi ADR-0058 nguyên vẹn.
- **Guard**: `stage approve` **viết rõ chữ** (không `$(…)`/biến/glob/`xargs`, không `init`/`--adopt`) được cho qua khi
  `agent_stage_approval(root)` (đọc cả cây lẫn bản đã commit như `build_phase`; `XT_GUARD_POLICY=strict` không nới); mọi
  dạng khác giữ `STAGE_APPROVE` deny. Ghi tay `STAGE.json` vẫn chặn.
- **Mẫu dự án đích** `framework/templates/xt.yaml`: `stage_approval: agent` (quyết định chủ dự án). Dự án đã cài nhận khoá
  mới dạng chú thích khi nâng (`install.py` nối khoá mới) — bật là quyết định của từng dự án.

### Hệ quả

- Tốt: hết điểm chờ người ở ranh giới giai đoạn cho dự án chọn `agent`; vòng `/autopilot` → MVP → `/complete` chạy liền
  một phiên (ADR-0009); dự án giữ `human` không đổi gì.
- Xấu / đánh đổi: "nghiệm thu MVP" trở thành lời tự khai của agent có bằng chứng máy (kiểm lại cuối, smoke, bản trình còn
  nguyên) chứ không phải người xem bản thử — chủ dự án chấp nhận; `release-check` hàng `stage` vẫn chỉ xét giai đoạn ≥ 2,
  nên GO sản xuất có thể không có người nào từng duyệt MVP (lớp đỡ còn lại: chữ ký GO-NO-GO §5, `prod_switch`). Ai có quyền
  ghi nhánh chính đổi được khoá — cùng mức tin cậy với `delivery_phase`/`merge_hard_exceptions`.
- Chưa làm: `stage approve` của agent chưa đòi `loop verify --all` lại lúc duyệt (bản trình còn nguyên nên bằng chứng lúc
  `submit` còn hiệu lực); agent khác Claude có thể không mang biến phiên (ADR-0058 đã ghi) — khi đó `xt.py` coi là người.

### Xác nhận

- `python3 -m unittest tests.test_stage_agent_approval`: khoá cần cả cây lẫn bản đã commit; agent duyệt được bản còn
  nguyên; bản đổi → từ chối (người vẫn duyệt được); `init --adopt` từ chối; `next-step` trả `stage-approve`; guard cho
  qua dạng chữ rõ, chặn dạng mờ/`--adopt`/strict/khoá chưa commit.
- Corpus guard (`tests/fixtures/autonomy/guard.json`) không đổi quyết định: repo khung không khai khoá.
- Mốc xét lại: cùng ADR-0058 — khi có số đo thời gian tới nghiệm thu ở ≥ 1 dự án đích (research xưởng §8).

## Ưu / nhược từng phương án

### 1. Khoá `stage_approval` (chọn)
- Tốt: opt-in theo dự án, quyền ở nhánh chính, bản trình còn nguyên, đường lùi một dòng.
- Xấu: thêm một khoá và một nhánh guard phải giữ đồng bộ với `xt.py`.

### 2. Bỏ hẳn kiểm người/agent
- Tốt: ít mã nhất.
- Xấu: mất lớp chặn nhầm cho mọi dự án, kể cả dự án muốn người duyệt; không có đường lùi theo dự án.

### 3. Agent chỉ đề xuất, người vẫn duyệt
- Tốt: giữ nguyên ADR-0058.
- Xấu: không đáp ứng yêu cầu "agent tuyên bố đạt MVP"; điểm chờ người vẫn còn.
