# AGENTS.md — scripts/

> Quy ước riêng của thư mục này, nạp khi làm việc ở `scripts/` (Claude Code: qua `CLAUDE.md` cùng thư mục). Luật chung: [`../AGENTS.md`](../AGENTS.md); mẫu theo thư mục: `XC-DOCAI-011`. Tệp này không được cài sang dự án đích (`install.py` copy theo danh sách tên tệp).

- **Chuẩn mã:** chỉ stdlib CPython 3.15.x; `mypy --strict --python-version 3.15`; C901 ≤ 10; không `noqa`/pragma. Tệp `.py` mới thêm vào lệnh `typecheck` ở `../xt.yaml`; dự án đích cần nó thì thêm vào `optional_scripts` của `install.py`.
- **Trần byte** (`tests/test_docs_budget.py`, ADR-0043): thêm mã hay chữ thì cắt chữ thừa chỗ khác trong cùng nhóm; không nới trần.
- **Tên định danh:** tránh `secret`/`token`/`password`/`credential`/`trusted` — CodeQL coi đó là dữ liệu nhạy cảm và báo `clear-text-*` khi giá trị đi vào log hay tệp (đã gặp với `trusted_archive`; đổi tên thay vì thêm chú thích bỏ qua).
- **Lệnh mới của `xt.py`:** thêm dòng ở bảng `../README.md` §Công cụ (`test_readme_lists_every_subcommand` kiểm), dòng ở `../CHANGELOG.md`, test có đủ nhánh (coverage 100 %).
- **Cổng cục bộ:** `scripts/dev-task.sh gate-fast`; CI là cổng đầy đủ. Chi tiết quy trình sửa khung: `../AGENTS.md` §7.
