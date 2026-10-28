# PLAN — Củng cố sau đánh giá 2026-10-28

> Phiên: X-Templates — work · G8/harden · D-219 · gốc `main` `07c428f` (#308).

- Vấn đề: corpus chưa giữ hai lỗi #308; state có thể mất cập nhật khi bỏ khóa; guard lỗi nạp có đường cho chạy; cài mới chưa có preset quyền hạn chế.
- Người dùng: người quản trị khung và dự án đích chạy agent phát triển phần mềm.
- Nghiệm thu: audit strict không còn hai lỗi đã sửa; corpus có ca hồi quy/đối chứng; lỗi khóa không ghi state; lỗi nạp không chạy Gate; cài safe không thay cấu hình hiện hữu; Gate giữ ngưỡng 100%.
- Không làm: đổi mặc định tự chủ đã được chọn, mô phỏng toàn bộ shell, tự cấu hình sandbox máy người dùng, viết lại monolith, khẳng định luật chưa xác minh, hứa tăng tốc khi chưa có số đo.
- Thiết kế: ADR-0054 (chặn ghi/thực thi khi thiếu cơ chế kiểm); ADR-0055 (preset cài đặt tùy chọn). Không thêm dependency, giữ CLI cũ tương thích ngoài trường hợp lỗi.
- Đường lùi: từng lát có thể revert riêng; không hạ cổng. Pilot bên ngoài và xác nhận pháp lý cần bằng chứng độc lập.

## Task

- [x] `T-3570` Bổ sung corpus #308 với ca nguy hiểm và đối chứng; Given main đã vá When benchmark chạy Then lỗi append/parallel được giữ bằng refs audit (files: tests/fixtures/autonomy/guard.json, tests/test_autonomy_bench.py) — Gate: `python3 -m unittest -q tests.test_autonomy_bench && python3 scripts/xt.py autonomy-bench`
- [x] `T-3571` Chặn guard lỗi nạp/fallback hỏng trên CLI/Gate; Given guard hỏng When Gate gọi Then không tạo canary, mã 126; không harness và runtime fallback khỏe giữ tương thích (exec: deep; files: scripts/xt.py, tests/test_xt_core.py) — Gate: `python3 -m unittest -q tests.test_xt_core`
- [x] `T-3572` Chặn ghi state khi thiếu fcntl/flock; Given state đang có When khóa không dùng được Then mutator không gọi và byte state không đổi, CLI exit 2, Stop hook vẫn cho dừng có log (sau: T-3571; files: scripts/xt.py, tests/test_xt_loop.py) — Gate: `python3 -m unittest -q tests.test_xt_loop tests.test_flow`
- [x] `T-3573` Preset install safe|autonomous tùy chọn; Given cài mới safe Then L1/human/harden; When cài lại Then giữ lựa chọn và tùy chỉnh, plan khớp ghi thực (files: scripts/install.py, tests/test_install.py) — Gate: `python3 -m unittest -q tests.test_install`
- [x] `T-3574` Tài liệu, audit delta, bàn giao; làm rõ phạm vi runtime, nguồn chưa xác minh và bằng chứng trong lần nâng cấp (sau: T-3570, T-3571, T-3572, T-3573; files: README.md, CHANGELOG.md, PROGRESS.md, docs/ops/AUDIT-STATUS.md) — Gate: `python3 scripts/xt.py validate && python3 scripts/check-links.py && python3 scripts/xt.py audit check docs/ops/AUDIT-STATUS.md --strict && python3 -m unittest -q tests.test_docs_budget`
- [ ] `T-3575` Đẩy nhánh đã kiểm, mở PR nháp khi quyền API cho phép; không merge/deploy; Given nhánh đã đẩy When API đọc PR Then có đúng một PR draft đang mở (sau: T-3574) — Gate: `gh api 'repos/seeker19110/X-Templates/pulls?head=seeker19110%3Aharden%2Fassessment-2026-10-28&state=open' --jq 'map(select(.draft)) | length' | grep -qx 1`
