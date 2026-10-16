# ADR-0011: Trong vòng autopilot, cổng không được xanh khi không kiểm gì

- **Trạng thái:** Đã chấp nhận
- **Trạng thái triển khai:** Đã triển khai (`scripts/dev-task.sh` `loop_noop`; `scripts/xt.py` `gate_noop_keys` +
  cảnh báo ở `loop init`; test `tests/test_hooks.py::DevTaskTest`, `tests/test_xt_cli.py::LoopCommandsTest`)
- **Ngày:** 2026-10-16

## Bối cảnh

Mẫu `framework/templates/xt.yaml` để mọi khoá là `""`. Với `dev-task.sh`, khoá `""` nghĩa là "cố ý bỏ qua": task in
`skip` và thoát 0; không khai gì cũng không dò được thì in `no-op` và thoát 0 (fail-open, ADR-0002). Hệ quả: một PLAN
có Gate `scripts/dev-task.sh gate` được `loop record` ghi bằng chứng **xanh** cho một cổng không chạy test nào, và
verdict tính task đó là xong. Lệnh `true`, `:`, `exit 0`, `echo …` trong `xt.yaml` cho cùng kết quả.

Fail-open đúng cho hook chạy ngoài vòng (dự án mới cài khung, chưa có stack, người đang commit tay). Trong vòng
autopilot thì cổng là **bằng chứng** mà verdict dựa vào, nên "không kiểm gì" phải khác "kiểm và qua".

## Quyết định

1. Khi `.autopilot/state.json` có `"active": true`, `dev-task.sh` coi `lint` và `test` là bắt buộc: lệnh phân giải
   được rỗng, hoặc chỉ là `true` · `:` · `exit` · `exit 0` · `echo …` · `printf …` → in lý do và thoát 3 (ĐỎ).
   `typecheck`, `build`, `format` giữ hành vi cũ (nhiều stack không có).
2. Ngoài vòng (không có state hoặc `"active": false`) giữ nguyên fail-open.
3. `xt.py loop init` không chặn khi `xt.yaml` để `lint`/`test` rỗng/no-op (task đầu của PLAN thường là điền
   `xt.yaml`), nhưng in cảnh báo `⚠ Cổng sẽ ĐỎ trong vòng (ADR-0011)` lên stderr. Khoá vắng hẳn không cảnh báo:
   `dev-task.sh` còn tự dò theo stack, và `xt.py doctor` đã báo thiếu khoá.

## Lý do

- Bằng chứng xanh của một cổng rỗng là lời khai trá hình, ngược P1. Lỗi này khó thấy: log ghi exit 0, PR có "Gate xanh".
- Chỉ chặn trong vòng giữ được ADR-0002 cho mọi ngữ cảnh khác.
- `lint` + `test` là hai khoá mọi stack đều có lệnh thật; ép cả `typecheck`/`build` sẽ buộc dự án khai lệnh giả để qua.

## Các phương án đã cân nhắc

- **`loop init` từ chối khi `xt.yaml` chưa có `test`** (đề xuất ban đầu): chặn luồng đã ghi trong tài liệu (PLAN điền
  `xt.yaml` ở task đầu, sau `loop init`). Cổng đỏ trong vòng đã đủ chặn bằng chứng giả; `init` chỉ cảnh báo. Loại.
- **Bỏ fail-open hẳn** (khoá rỗng luôn đỏ): làm hỏng commit tay ở dự án vừa cài khung; ngược ADR-0002. Loại.
- **Phát hiện no-op bằng cách đo thời gian/đầu ra lệnh**: đoán, dễ báo oan. Loại.

## Hệ quả

- Gate của task trong PLAN cũng có thể là `true`/`echo` và vẫn được ghi xanh — ADR này không chặn trường hợp đó (Gate
  của PLAN do `loop record` kiểm, không qua `dev-task.sh`). Là việc riêng.
- Dự án đang chạy vòng với `xt.yaml` rỗng sẽ thấy cổng đỏ ở lần chạy kế tiếp; cách sửa ghi ngay trong thông báo.
