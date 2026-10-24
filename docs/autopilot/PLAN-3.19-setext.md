# PLAN-3.19-setext.md — Khung X-Templates · tiêu đề setext nhiều dòng/trong `>` cho `check-links` → bản 3.18.1

> Lập ngày 2026-10-24. Chủ repo gọi lại `/autopilot` sau PLAN-3.18-feedback2 (done, `v3.18.0`, #241). Việc máy làm được
> còn lại duy nhất: 🟢 review #238 (ghi ở PROGRESS và GO-NO-GO 3.18.0). Phiên chính tự duyệt (D-158).
>
> **Cú pháp bắt buộc cho máy:** mỗi task một dòng `- [ ] \`T-NNNN\` <việc> — Gate: \`<lệnh>\``.

## Tóm tắt (cổng duyệt — phiên chính tự duyệt, D-158)
- Phạm vi: `check-links.py` sinh anchor cho tiêu đề setext có đoạn nhiều dòng (GitHub nối các dòng bằng khoảng trắng) và
  tiêu đề setext trong trích dẫn `>`; hiện báo oan "anchor không có" → `lint` đỏ oan ở dự án đích.
- Cách: test tái hiện đỏ trước; gom đoạn văn (bỏ tiền tố `>`) đến dòng trống, dòng gạch `===`/`---` biến cả đoạn thành
  tiêu đề. Thà nhận thừa anchor còn hơn đỏ oan (cùng nguyên tắc `slugs`).
- Không làm: các việc chờ người trong PROGRESS; nợ #191 (`install.py`) giữ tới pha harden.
- Rủi ro: `---` dưới đoạn văn bị coi là tiêu đề dù tác giả định viết đường kẻ — GitHub cũng hiểu như vậy; chỉ thêm anchor.

## Ngân sách (4 con số)
- Số vòng tối đa: `max(40, 8 × task)` (`loop init --single-session` tính)
- Chi phí: 0 đồng ngoài phiên (không phụ thuộc mới)
- Timeout mỗi lệnh Gate: 1800 giây (`XT_RECORD_TIMEOUT` mặc định)
- Ngày hết hạn: 6 giờ sau `loop init` (`--hours 6`)

## Điểm dừng bắt buộc (`loop defer`; `loop block` khi mọi việc còn lại phụ thuộc)
- Nâng khung ở dự án đích (PR `install.py`): chủ dự án merge

## Task

### Lát 1 — Anchor setext
- [x] `T-2701` `check-links.py`: tiêu đề setext gồm cả đoạn nhiều dòng (nối bằng khoảng trắng) và setext trong `>`; dòng trống cắt đoạn; test tái hiện (files: scripts/check-links.py, tests/test_check_links.py, CHANGELOG.md, VERSION) — Gate: `python3 -m unittest discover -s tests -k check_links_anchor && python3 scripts/check-links.py`
