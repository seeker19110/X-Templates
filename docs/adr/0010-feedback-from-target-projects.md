# ADR-0010: Phản hồi lỗi và cách khắc phục từ dự án đích về khung — dự án ghi, khung kéo về, người duyệt

- **Trạng thái:** Đã chấp nhận
- **Trạng thái triển khai:** Đã triển khai (`scripts/xt.py feedback add/collect/list/aggregate`; test `tests/test_xt_cli.py`
  `FeedbackTest`; module `framework/11-autonomous-loop/framework-feedback.md` `LOOP-FB-001`…`004`; `docs/ops/TARGETS.md`;
  `.github/ISSUE_TEMPLATE/feedback-du-an-dich.yml`; Routine hằng tuần của chủ repo)
- **Ngày:** 2026-10-15

## Bối cảnh

Chủ repo yêu cầu (2026-10-15): các dự án dùng khung gửi lỗi và cách khắc phục về để cải thiện khung. Dữ kiện đã có trong
dự án đích nhưng không ai đọc: MUST bị miễn trong `BLUEPRINT.md` (đúng dữ liệu "Tiếp theo 1" của PROGRESS cần — mục MUST
nào hay bị miễn), lý do autopilot `blocked`, lỗi hook/công cụ mà agent tự vá trong dự án. Dò 2026-10-15: trong các repo
của chủ repo, chỉ `seeker19110/hotel-manager` cài khung dạng `.xtemplates/`.

Ràng buộc: repo khung **public** — mọi thứ đưa về đều công khai; dự án đích có thể chứa dữ liệu khách hàng; hành động
đối ngoại (mở issue/PR ở repo khác, đăng nội dung) là điểm dừng về hành động (ADR-0008); Routine không người trực chỉ
đề xuất (`LOOP-STOP-014`).

## Quyết định

1. **Dự án đích ghi trong repo của mình.** `xt.py feedback add` → `docs/xtemplates-feedback/FB-NNN.md` (định dạng dòng
   `- Nhãn: giá trị` máy đọc; trường gộp một dòng, qua `redact`, kèm phiên bản khung). `feedback collect` tự gom MUST bị
   miễn và lý do `blocked`, khoá chống trùng ở dòng `Nguồn: collect:…`. Luật ở module `LOOP-FB`; `AGENTS.md` mẫu,
   `/autopilot` và `/handover` gọi `collect` trước báo cáo/bàn giao.
2. **Khung kéo về.** `docs/ops/TARGETS.md` liệt kê repo; Routine hằng tuần (phiên mới mỗi lần) clone nông từng repo, chạy
   `xt.py feedback aggregate --from <repo>=<thư-mục> …`, ghi `docs/ops/feedback/REPORT-<ngày>.md` và mở **PR nháp** vào repo
   khung. Không có tín hiệu mới → không mở PR.
3. **Ngưỡng sửa.** Gộp theo (loại, ID); nhóm "đủ ngưỡng" khi ≥ 2 dự án cùng báo hoặc có bước tái hiện. Sửa khung theo
   từng nhóm như mọi thay đổi khung (test, CHANGELOG, trỏ FB gốc).
4. **Người duyệt trước khi công khai.** PR nháp chỉ chứa nội dung đã qua `redact`; người đọc và merge. Issue template
   "Phản hồi từ dự án đích" cho người báo tay, có ô xác nhận không dữ liệu dự án.

## Lý do

- Kéo thay vì đẩy: dự án đích không cần token ghi vào repo khác (ít quyền hơn, ít rủi ro lộ), một chỗ gom thì gộp trùng
  được, và đúng luật Routine chỉ đề xuất.
- File trong repo dự án thay vì gửi ngay: ghi lúc vừa sửa (ngữ cảnh đủ), duyệt được bằng chính PR của dự án, không cần mạng.
- Ngưỡng ≥ 2 dự án hoặc có tái hiện: tránh khung đổi theo một ca đặc thù; vẫn sửa nhanh lỗi công cụ tái hiện được.

## Các phương án đã cân nhắc

- **Dự án đích tự mở issue ở repo khung** (workflow + PAT): cần token ghi chéo repo ở mọi dự án, khó kiểm nội dung trước
  khi công khai. Loại; giữ issue template cho người báo tay.
- **Telemetry tự động gửi về máy chủ**: cần dịch vụ, đồng ý của chủ dự án, rủi ro dữ liệu. Loại.
- **Chỉ issue template**: phụ thuộc người nhớ báo; mất tín hiệu máy (miễn trừ, blocked). Không đủ.

## Hệ quả

- Tốt: khung có dữ liệu thật về mục hay bị miễn, hook chặn nhầm, công cụ lỗi; mỗi đổi khung có bằng chứng từ dự án.
- Xấu/nợ: `redact` chỉ bắt dạng bí mật đã biết — tên khách hàng/đường dẫn nội bộ phải do người viết và người duyệt PR
  chặn. Routine đọc repo private cần quyền của phiên; repo ngoài tài khoản phải tự báo qua issue. Danh sách
  `TARGETS.md` cập nhật tay.
