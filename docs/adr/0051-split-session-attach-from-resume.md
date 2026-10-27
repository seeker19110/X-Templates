# ADR-0051: Tách "gắn phiên mới" khỏi "giải quyết việc chờ / mở block" — `loop attach`, `loop resolve`, `loop unblock`; `loop resume` giữ nghĩa cũ và in cảnh báo

- **Trạng thái:** Đã chấp nhận (chủ repo 2026-10-26: "làm lát 1 đi, bắt đầu bằng /adr nối phiên"; phiên chính tự duyệt thiết kế theo tiêu chí chất lượng cuối, ADR-0008 — D-201)
- **Trạng thái triển khai:** Chưa triển khai — lát 1 của [nghiên cứu 2026-10-26](../../research/2026-10-26-autopilot-complete-optimize.md) §4A/§9.1/§11; PR triển khai là PR kế (mỗi lát một PR ≤ 150 dòng ở pha harden).
- **Ngày:** 2026-10-26
- **Làm rõ:** ADR-0009 mục 2 ("`loop resume` đưa việc chờ lại hàng làm" — nghĩa này giữ nguyên ở `resume`, tách thêm thành `resolve` + `unblock`; việc *thay* thật thuộc ADR gỡ `resume` sau), D-156 (3) (T-2522: dùng `loop resume` để gắn lại phiên sau `/clear` — D-201 thay phần này bằng `loop attach`), `LOOP-DESIGN-005` (cùng chữ ký lỗi 3 lần → `blocked`: nối phiên không được đặt lại đếm), `LOOP-STOP-021` (`loop defer`), `LOOP-HARNESS-024` (`loop init` không ghi đè vòng sống: lối ra "tiếp vòng cũ").

## Bối cảnh

`_loop_resume` (`scripts/xt.py:6940`) làm bốn việc cùng lúc: gắn `session_id` phiên hiện tại, mở `blocked`, đặt `same_failure_count` về 0
và `last_failure_signature` về `null`, **xoá toàn bộ `deferred`** (kèm hai việc phụ: bỏ `ended`/`final_verdict` — đã ở `unblock`; điền
`scope` cho state cũ — T-1503, chuyển ở ADR gỡ `resume`). Máy lại chỉ người dùng tới đúng lệnh này ở hai chỗ khác nghĩa:
(1) người đã xử lý điểm dừng (nghĩa gốc, ADR-0009); (2) phiên đổi (`/clear`, phiên cloud mới) — `SESSION_MISMATCH_NOTE`
(`:2863`, in ở `loop status` `:6352`) và README mảng 11 bước 13.

Tái hiện 2026-10-26 trên cây cùng `scripts/xt.py` với `main` 3.27.0 (`research/evidence/2026-10-26-three-loops/resume-head.json`, exit 0): vòng có `iterations` 7,
`same_failure_count` 2, `deferred` T-900, `session_id` cũ → sau `resume` chỉ để gắn phiên: `deferred` **mất**, đếm lỗi 2 → 0,
chữ ký → `null`; `iterations`/`deadline` giữ. Việc chờ người biến mất nghĩa là máy sẽ giao lại task cần khoá/quyền chỉ người có;
đếm lỗi về 0 nghĩa là task đang lặp lỗi được thêm ba lần thử. Cả hai đều xảy ra dù chẳng ai "xử lý" điều gì. `_carry_previous`
chỉ cứu việc chờ khi `loop init` lại, không cứu `resume`.

Ràng buộc: dự án đích đã cài bản cũ (skill `/autopilot` bước 4, README, SessionStart, hook) vẫn nhắc `loop resume` tới khi chạy
lại `install.py`; `defer` từ chối task đang lỗi (`_defer_problem` `:6583`) — thiết kế mới giữ luật này (`resolve` không nới `defer`); `unblock`
sau lỗi lặp đặt lại đếm như `resume` hôm nay, cùng mức tin cậy (§Hệ quả); README mảng 11 hết dư (0 B) và skill `/autopilot` còn 1 B nên mọi câu mới phải đổi câu cũ (bước 9/13 và skill
bước 4: `attach` = `resume` = 6 ký tự; bước 14 thành `resolve`/`unblock` dài hơn → cắt chỗ khác trong README).

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

- `loop attach [--reason TEXT]`: chỉ khi vòng `active`. Đặt `session_id` = phiên hiện tại, nối `attached[]` `{session, reason, at}` (danh sách để đếm can thiệp — nghiên cứu §11).
  **Không chạm** `deferred`, `same_failure_count`, `last_failure_signature`, `blocked`, `iterations`, `deadline`, `scope`. Đã gắn
  đúng phiên này → exit 0 không đổi state (idempotent). Ngoài Claude Code (không có phiên) → exit 2: lệnh chỉ để gắn phiên không
  được *gỡ* ràng buộc phiên (khác `resume` đặt `""`). Vòng không `active` → exit 2 kèm **lối ra theo `final_verdict`** (một hàm dùng chung cho cả ba lệnh): `blocked`/`stopped`
  hoặc không có `final_verdict` → `loop unblock --reason`; `done-pending-human` → người đã xử lý: `loop resolve --task <ID>` rồi
  `loop unblock`, chưa: `loop init --plan <đợt kế>` (việc chờ đi theo — ADR-0047 Quyết định 3); `done`/`budget` → `loop init --plan <đợt kế>`.
- `loop resolve --task ID --reason TEXT` (cả hai bắt buộc): chỉ gỡ **một** mục `deferred`. ID không có trong `deferred` → exit 2
  kèm danh sách đang chờ. Ghi `resolved[]` `{id, reason, deferred_reason, at}`; không chạm `active`, `blocked`, đếm lỗi, vòng, hạn.
  Task trở lại hàng làm theo PLAN (mục đã tick/đã đạt vẫn không tính). Gỡ xong là exit 0 kể cả khi vòng đã kết thúc;
  khi đó in thêm bước kế theo `final_verdict` (`done-pending-human`/`blocked`/`stopped` hoặc không có `final_verdict` → `loop unblock`; `done`/`budget` → `loop init`).
- `loop unblock --reason TEXT` (bắt buộc lý do) — người xem rồi mở. **Nhận**: vòng sống bị chặn (cờ `blocked` bất kể nguồn — `loop block`, `ci-triage` —
  hoặc lỗi lặp ≥ `max_same_failure`); vòng đã kết thúc với `final_verdict` `blocked`, `done-pending-human`, `stopped`, hoặc không có `final_verdict`
  (state cũ). **Từ chối** (exit 2 kèm lối ra): `final_verdict` `done`/`budget` → `loop init --plan <đợt kế>` (không hồi sinh đợt đã xong,
  không mở trần); vòng sống không bị chặn → `loop attach`, trừ khi verdict của nó là `budget` → `loop init`. Khi nhận: `active` True, `blocked` False, xoá `blocked_reason`/`ended`/
  `final_verdict`, đặt đếm lỗi và chữ ký về 0/`null`, gắn phiên hiện tại (ngoài Claude Code: **giữ** `session_id` cũ,
  không gỡ ràng buộc — phiên mới dùng `attach`). **Giữ** `deferred`, `iterations`, `deadline`. Ghi `unblocked[]`
  `{reason, prior_verdict, prior_reason, at}`. Mở `done-pending-human` mà chưa `resolve` việc nào thì lượt Stop kế lại kết thúc
  `done-pending-human` — lệnh in nhắc `resolve` trước. Lệnh tính verdict-sau-mở **trước khi ghi**: ra `budget` (vòng vừa bị chặn vừa hết
  vòng/hạn) → từ chối như `final_verdict` `budget` — exit 2, **không ghi gì**, in "hết ngân sách → `loop init --plan <đợt kế>`"
  (`_carry_previous` vẫn mang `deferred`). Mọi lối exit 2 của ba lệnh đều không đổi state. Để `loop init` mở được ở ca vòng
  **còn sống** vừa `blocked` vừa hết vòng/hạn (`_verdict_loop_state` xét `blocked` trước trần nên `_live_loop` coi là vòng sống và trỏ
  ngược `unblock` — chu trình), PR triển khai đổi `_live_loop`: kiểm trần vòng/hạn **trước** verdict, hết thì coi như `budget` (không chặn
  `loop init`) dù còn `blocked` — đúng chữ `LOOP-HARNESS-024` "còn active, chưa hết vòng/hạn" và D-177.
- `loop resume` **giữ nguyên hành vi** (cả bốn việc) và in một dòng stderr trỏ ba lệnh mới. Gỡ `resume` ở một ADR sau, khi `docs/ops/TARGETS.md`
  cho thấy dự án đích đã chạy lại `install.py` ≥ 1 bản (không bỏ bằng PR này).
- Chữ đổi cùng PR triển khai (mọi câu mới đổi câu cũ — §Bối cảnh): `SESSION_MISMATCH_NOTE` → `loop attach`; `loop init` vòng sống → `loop attach`; `doctor` cảnh báo `BLOCKED` → `loop unblock`; README mảng 11 bước 9/13/14;
  skill `/autopilot` bước 4; `loop-design.md` bẫy "Nhiều lần `loop init`"; `stop-points-and-escalation.md` hàng "Bế tắc máy";
  `harness-files.md` bảng `state.json` (trường mới); `xt.py --help`; assert chữ ở `tests/test_hooks.py`, `tests/test_xt_loop.py`,
  `tests/test_xt_cli.py`. `_live_loop` nhánh `blocked` (cả `loop block` lẫn lỗi lặp) → `loop unblock --reason`.
  ID checklist không đổi; chữ `LOOP-HARNESS-024`/`LOOP-STOP-021` đổi nên dự án đích ghép lại blueprint (CHANGELOG mục "Dự án đích").

Phiên bản/nguồn: không dính phiên bản/chuẩn ngoài; hành vi hiện tại do code và test chứng minh (`resume-head.json`).

### Hệ quả

- Tốt: đổi phiên không còn xoá việc chờ người hay đặt lại đếm lỗi; việc "người đã xử lý" thành hai bước có dấu vết (`resolved[]`, `unblocked[]`)
  và có lý do bắt buộc; phiên đang chạy bản cũ không vỡ.
- Mức tin cậy không đổi: guard không có luật cho lệnh con `loop`, nên agent vẫn tự chạy được `unblock`/`resolve` như `resume` hôm nay;
  điểm khác là `--reason` bắt buộc và `unblocked[]`/`resolved[]` để lại dấu vết cho review (cùng nợ ADR-0009 §Hệ quả đã ghi cho `defer`).
- Xấu / đánh đổi chấp nhận: thêm ba lệnh con (byte `scripts/`, trần thư mục còn ≈ 1 MiB — ADR-0050); trong một giai đoạn tồn tại hai
  cách làm cùng việc (`resume` cũ và ba lệnh mới); "người xử lý xong → chạy tiếp" nay là `resolve` rồi `unblock` (hai lệnh, đổi lấy dấu vết từng việc).
- Việc phải làm tiếp: PR triển khai (code + test + chữ đồng bộ); ADR gỡ `resume` khi dự án đích đã cập nhật; ba mục còn lại của lát 1
  (không-tiến-triển theo task, `rev` cho `state.json`, perf metadata v2) mỗi mục một quyết định riêng, không gộp vào ADR này.

### Xác nhận

Test mới (trong PR triển khai, cùng corpus luồng FLOW-01…02 của nghiên cứu §10): `attach` giữ `deferred` + đếm lỗi + `blocked`; `attach` cùng
phiên không đổi state; `attach` ngoài Claude Code → exit 2; `attach` vòng không `active` → exit 2 kèm đúng lối ra cho từng `final_verdict`
(`blocked`/`stopped`/`done-pending-human`/`done`/`budget`); `unblock` khi `done`/`budget` hoặc vòng sống không bị chặn → exit 2; `unblock` vòng vừa bị chặn vừa hết ngân sách → exit 2 "hết ngân sách" và state không đổi; `unblock` vòng sống `budget` không bị chặn → trỏ
`loop init`; `loop init` sau vòng sống `blocked` + hết vòng/hạn → exit 0, mang `deferred`; `attach`/`unblock` với state không có `final_verdict` → trỏ/nhận `unblock`; `resolve` trên vòng đã kết thúc → exit 0 kèm bước kế; `unblock`
ngoài Claude Code giữ `session_id`; `resolve` trên vòng `budget` gợi `loop init`; `resolve` đúng một ID, ID lạ → exit 2; `unblock` giữ `deferred`, ghi `unblocked[]`, thiếu lý do → exit 2; `resume` cũ
vẫn qua test hiện có và in cảnh báo; state cũ không có `resolved`/`unblocked`/`attached` đọc được. Tái hiện `resume-head.json` chạy với `attach` cho `deferred` còn
nguyên. `implementation-status` cập nhật theo PR.

## Đường lùi

Xoá ba lệnh con và cảnh báo ở `loop resume`; đưa SessionStart/README/skill về trỏ `loop resume` — một commit (D-201). State có
`resolved[]`/`unblocked[]`/`attached[]` vẫn đọc được bởi mã cũ (khoá thừa bị bỏ qua).

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
