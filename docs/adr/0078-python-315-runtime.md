# ADR-0078: Dùng một dòng Python 3.15 cho công cụ X-Templates

- **Trạng thái:** Đã chấp nhận ngày 2026-11-14 (D-485).
- **Trạng thái triển khai:** Đang kiểm chứng trên nhánh nâng runtime.

## Bối cảnh

Repo trước đây ghim 3.14 cho công việc chính và kiểm thêm sàn 3.11. Yêu cầu mới là bỏ các dòng Python cũ
trong repo và công cụ được cài sang dự án đích. CPython 3.15.2 là bản ổn định đã xác minh ngày 2026-11-14.
[Python.org](https://www.python.org/downloads/release/python-3152/),
[danh mục Python của GitHub Actions](https://github.com/actions/python-versions/blob/main/versions-manifest.json)

## Phương án đã cân nhắc

1. Chỉ dùng dòng 3.15 cho khung. CI và môi trường phát triển của repo dùng cùng bản vá đã ghim.
2. Dùng 3.15 làm mặc định, tiếp tục hỗ trợ 3.11 và 3.14. Cách này giữ khả năng chạy trên máy cũ và thêm
   việc xác minh nhiều phiên bản cho mỗi thay đổi của khung.

## Quyết định và hệ quả

Chọn phương án 1. Bộ cài và CLI chấp nhận dòng CPython 3.15.x. Repo và các workflow do khung quản lý ghim
3.15.2. Job kiểm thử checkout mang tên `main` vẫn chạy toàn bộ bộ test bằng cùng Python. Job coverage
giữ ngưỡng 100% dòng và nhánh. Ruff lint và mypy kiểm theo 3.15. Formatter giữ cú pháp nhóm ngoại lệ có ngoặc
để bộ cài và CLI vẫn báo được lỗi phiên bản trên Python cũ. CI mẫu dùng đường dẫn interpreter của khung để giữ nguyên
PATH của ứng dụng. Các dự án đích chọn runtime ứng dụng qua cấu hình của chính dự án.

Trước khi nâng khung đã cài, đặt Python 3.15 trên PATH của máy dev. Khi cài lại với `--with-github`, gộp thay đổi
từ `.github/workflows/ci.yml.xtemplates-new` nếu bộ cài xuất file này. Với steward workflow dùng chung, chỉ định
Python 3.15 trước khi gọi `xt.py` nếu bản workflow đang dùng chưa cài Python cho khung. Nếu cần quay
lui, revert PR này và cài lại phiên bản khung trước khi nâng.

## Xác nhận

Cài các lockfile bằng `--require-hashes`, chạy các bài kiểm installer và CLI, `scripts/dev-task.sh gate` và
kiểm CI trên head của PR. Dùng chính phiên bản 3.15.2 cho các lần kiểm.
