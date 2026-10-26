# ADR-0051: Tách "gắn phiên mới" khỏi "giải quyết việc chờ / mở block" — `loop attach`, `loop resolve`, `loop unblock`; `loop resume` giữ nghĩa cũ và in cảnh báo

- **Trạng thái:** Đã chấp nhận (chủ repo 2026-10-26: "làm lát 1 đi, bắt đầu bằng /adr nối phiên"; phiên chính tự duyệt thiết kế theo tiêu chí chất lượng cuối, ADR-0008 — D-201)
- **Trạng thái triển khai:** Chưa triển khai — lát 1 của [nghiên cứu 2026-10-26](../../research/2026-10-26-autopilot-complete-optimize.md) §4A/§9.1/§11; PR triển khai là PR kế (mỗi lát một PR ≤ 150 dòng ở pha harden).
- **Ngày:** 2026-10-26
- **Thay một phần:** ADR-0009 mục 2 ("`loop resume` đưa việc chờ lại hàng làm" — `resume` không còn là lối nối phiên; nghĩa cũ vẫn có, chuyển sang `resolve` + `unblock`).
- **Làm rõ:** `LOOP-DESIGN-005` (cùng chữ ký lỗi 3 lần → `blocked`: nối phiên không được đặt lại đếm), `LOOP-STOP-021` (`loop defer`), `LOOP-HARNESS-024` (`loop init` không ghi đè vòng sống: lối ra "tiếp vòng cũ").

## Bối cảnh

`_loop_resume` (`scripts/xt.py:6940`) làm bốn việc cùng lúc: gắn `session_id` phiên hiện tại, mở `blocked`, đặt `same_failure_count` về 0
và `last_failure_signature` về `null`, **xoá toàn bộ `deferred`**. Máy lại chỉ người dùng tới đúng lệnh này ở hai chỗ khác nghĩa:
(1) người đã xử lý điểm dừng (nghĩa gốc, ADR-0009); (2) phiên đổi (`/clear`, phiên cloud mới) — `SESSION_MISMATCH_NOTE`
(`:2863`, in ở `loop status` `:6352`) và README mảng 11 bước 13.

Tái hiện 2026-10-26 trên `main` 3.27.0 (`research/evidence/2026-10-26-three-loops/resume-head.json`, exit 0): vòng có `iterations` 7,
`same_failure_count` 2, `deferred` T-900, `session_id` cũ → sau `resume` chỉ để gắn phiên: `deferred` **mất**, đếm lỗi 2 → 0,
chữ ký → `null`; `iterations`/`deadline` giữ. Việc chờ người biến mất nghĩa là máy sẽ giao lại task cần khoá/quyền chỉ người có;
đếm lỗi về 0 nghĩa là task đang lặp lỗi được thêm ba lần thử. Cả hai đều xảy ra dù chẳng ai "xử lý" điều gì. `_carry_previous`
chỉ cứu việc chờ khi `loop init` lại, không cứu `resume`.

Ràng buộc: dự án đích đã cài bản cũ (skill `/autopilot` bước 4, README, SessionStart, hook) vẫn nhắc `loop resume` tới khi chạy
lại `install.py`; `defer` từ chối task đang lỗi (`_defer_problem` `:6583`) — thiết kế mới phải giữ để `resolve`/`unblock` không
thành lối né "lỗi lặp lần 3 → BLOCKED"; README mảng 11 hết dư (0 B) và skill `/autopilot` còn 1 B nên chữ mới phải thay chữ cũ
cùng độ dài.

## Yếu tố quyết định

- Đúng và an toàn: mỗi lệnh một nghĩa; nối phiên không được giải phóng việc chờ người hay chữ ký lỗi.
- Giữ đường lùi: không phá phiên/dự án đích đang chạy bản cũ; bỏ lệnh mới là một commit.
- Kiểm được: mỗi nghĩa một test; trạng thái cũ (không có trường mới) đọc được.
- Gọn: không thêm trạng thái nếu `session_id` + `deferred` hiện có đủ.

## Các phương án đã cân nhắc

1. **Ba lệnh con riêng; `loop resume` cũ chạy như trước và in cảnh báo** (chọn).
2. **Đổi nghĩa `loop resume`**: mặc định chỉ gắn phiên, thêm `--resolve ID`, `--unblock`.
3. **Ba lệnh con riêng; `loop resume` thoát exit 2** buộc chọn một lệnh trong một bản (đề xuất ban đầu của nghiên cứu §9.1).
4. **Giữ `resume`**, chỉ sửa SessionStart/README để đổi phiên không trỏ tới `resume`.

## Quyết định

Chọn **phương án 1**.

- `loop attach [--reason TEXT]`: chỉ khi vòng `active`. Đặt `session_id` = phiên hiện tại (ngoài Claude Code → `""`, như `resume`),
  ghi `attached_at`, `attach_reason`. **Không chạm** `deferred`, `same_failure_count`, `last_failure_signature`, `blocked`,
  `iterations`, `deadline`, `scope`. Đã gắn đúng phiên này → exit 0 không đổi gì (idempotent). Vòng không `active` → exit 2 kèm lối ra:
  kết thúc `blocked`/`done-pending-human` → `loop unblock`; `done`/`budget` → `loop init --plan <đợt kế>` (ADR-0047).
- `loop resolve --task ID --reason TEXT` (cả hai bắt buộc): chỉ gỡ **một** mục `deferred`. ID không có trong `deferred` → exit 2
  kèm danh sách đang chờ. Ghi `resolved[]` `{id, reason, deferred_reason, at}`; không chạm `active`, `blocked`, đếm lỗi, vòng, hạn.
  Task trở lại hàng làm theo PLAN (mục đã tick/đã đạt vẫn không tính). Vòng đã kết thúc thì in nhắc `loop unblock` để chạy tiếp.
- `loop unblock --reason TEXT` (bắt buộc lý do): vòng kết thúc hoặc `blocked` do `loop block`/lỗi lặp được **người** xem rồi mở: `active`
  True, `blocked` False, xoá `blocked_reason`/`ended`/`final_verdict`, đặt đếm lỗi và chữ ký về 0/`null`, gắn phiên hiện tại. **Giữ**
  `deferred`, `iterations`, `deadline`. Ghi `unblocked[]` `{reason, prior_verdict, prior_reason, at}`. Không đổi trần: hết ngân sách → `loop init`
  đợt kế, không mở khoá lại bằng lệnh này.
- `loop resume` **giữ nguyên hành vi** (cả bốn việc) và in một dòng stderr trỏ ba lệnh mới. Gỡ `resume` ở một ADR sau, khi `docs/ops/TARGETS.md`
  cho thấy dự án đích đã chạy lại `install.py` ≥ 1 bản (không bỏ bằng PR này).
- Chữ đổi cùng PR triển khai, thay chữ cũ cùng độ dài: `SESSION_MISMATCH_NOTE` → `loop attach`; `_live_loop` (vòng `blocked` do người) →
  `loop unblock --reason`; `loop init` vòng sống → `loop attach`; `doctor` cảnh báo `BLOCKED` → `loop unblock`; README mảng 11 bước 9/13/14;
  skill `/autopilot` bước 4; `loop-design.md` bẫy "Nhiều lần `loop init`"; `harness-files.md` bảng `state.json` (trường mới); `xt.py --help`.
  ID checklist không đổi; chữ `LOOP-HARNESS-024`/`LOOP-STOP-021` đổi nên dự án đích ghép lại blueprint (CHANGELOG mục "Dự án đích").

Phiên bản/nguồn: không dính phiên bản/chuẩn ngoài; hành vi hiện tại do code và test chứng minh (`resume-head.json`).

### Hệ quả

- Tốt: đổi phiên không còn xoá việc chờ người hay đặt lại đếm lỗi; việc "người đã xử lý" thành hai bước có dấu vết (`resolved[]`, `unblocked[]`)
  và có lý do bắt buộc; phiên đang chạy bản cũ không vỡ.
- Xấu / đánh đổi chấp nhận: thêm ba lệnh con (byte `scripts/`, trần thư mục còn ≈ 1 MiB — ADR-0050); trong một giai đoạn tồn tại hai
  cách làm cùng việc (`resume` cũ và ba lệnh mới); "người xử lý xong → chạy tiếp" nay là `resolve` rồi `unblock` (hai lệnh, đổi lấy dấu vết từng việc).
- Việc phải làm tiếp: PR triển khai (code + test + chữ đồng bộ); ADR gỡ `resume` khi dự án đích đã cập nhật; ba mục còn lại của lát 1
  (không-tiến-triển theo task, `rev` cho `state.json`, perf metadata v2) mỗi mục một quyết định riêng, không gộp vào ADR này.

### Xác nhận

Test mới (trong PR triển khai, cùng corpus luồng FLOW-01…02 của nghiên cứu §10): `attach` giữ `deferred` + đếm lỗi + `blocked`; `attach` vòng không
`active` → exit 2 kèm lối ra; `resolve` đúng một ID, ID lạ → exit 2; `unblock` giữ `deferred`, ghi `unblocked[]`, thiếu lý do → exit 2; `resume` cũ
vẫn qua test hiện có và in cảnh báo; state cũ không có `resolved`/`unblocked`/`attached_at` đọc được. Tái hiện `resume-head.json` chạy với `attach` cho `deferred` còn
nguyên. `implementation-status` cập nhật theo PR.

## Ưu / nhược từng phương án

### 1. Ba lệnh con + `resume` giữ nghĩa cũ (chọn)
- Tốt: mỗi lệnh một nghĩa; không phá bản cài cũ; đường lùi một commit; gỡ `resume` làm sau bằng bằng chứng.
- Xấu: hai cách cùng tồn tại một thời gian; thêm bề mặt CLI.

### 2. Đổi nghĩa `resume` bằng cờ
- Tốt: ít lệnh nhất.
- Xấu: lệnh quen tay đổi nghĩa không báo — dự án đích chạy bản cũ (hoặc agent theo skill cũ) gọi `resume` kỳ vọng "mở block" nhận "chỉ gắn phiên" và kẹt, hoặc ngược lại; trái tiêu chí 1 và 2.

### 3. Ba lệnh con + `resume` exit 2
- Tốt: ép chọn nghĩa ngay.
- Xấu: mọi tài liệu/hook/skill của dự án đích chưa chạy lại `install.py` (kể cả SessionStart đang in `loop resume`) gọi vào lỗi; vòng đang chạy giữa phiên vỡ — trái tiêu chí 2.

### 4. Chỉ sửa chữ hướng dẫn
- Tốt: không thêm lệnh.
- Xấu: hai nghĩa vẫn dồn vào một lệnh; người dùng tới `resume` bằng thói quen hay lời nhắc cũ vẫn mất việc chờ; không giải quyết nguyên nhân.

## Thông tin thêm

- Liên quan: [nghiên cứu 2026-10-26](../../research/2026-10-26-autopilot-complete-optimize.md) §3 (đính chính R1), §4A, §9.1, §10 (FLOW-01/02); ADR-0009; ADR-0047; `LOOP-DESIGN-005`; `LOOP-STOP-021`; `LOOP-HARNESS-024`.
- Thời điểm xem lại: khi ADR gỡ `loop resume` được đề xuất, hoặc sau pilot lát 4 của nghiên cứu nếu số lần dùng `unblock`/`resolve` cho thấy hai bước quá nặng.
