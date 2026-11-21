# AGENTS.md — tests/

> Quy ước riêng của thư mục này, nạp khi làm việc ở `tests/` (Claude Code: qua `CLAUDE.md` cùng thư mục). Luật chung: [`../AGENTS.md`](../AGENTS.md); mẫu theo thư mục: `XC-DOCAI-011`.

- **Nhập test khác:** `sys.path.insert(0, str(Path(__file__).resolve().parent))` rồi `from test_x import …` (mẫu: `test_deploy_receipt.py`). Không `from tests.test_x import …`: cổng commit chạy từng lớp qua `test-select` và không nạp được gói `tests`.
- **Chạy:** `python3 -m unittest tests.test_x`. Toàn bộ kèm coverage: `PATH=<venv>:$PATH scripts/dev-task.sh test` (song song; khoảng 10–15 phút trên 16 lõi). Coverage dòng + nhánh 100 % do CI đo, cả tiến trình con.
- **Không ngưỡng giây/CPU cứng** (`BASE-GATE-005`): dùng `cpu_budget.assert_not_quadratic`; hạn chống treo qua `cpu_budget.run_with_deadline(…, hang="lý do")` (sàn `HANG_FLOOR`). Không `pragma: no cover`, `noqa`, skip.
- **Đổi `.claude/hooks/guard.py`:** chạy thêm `test_green_shell`, `test_green_gh`, `test_signoff2_scripts`, `test_audit_dot4_har` — chúng ghim các quyết định "được qua" và mã `BUDGET` cũ (AUD-SEC-747, 603). Luật guard mới phải là tập cha của luật cũ: so quyết định thô base với nhánh ở cả hai chính sách (mặc định và `XT_GUARD_POLICY=strict`). Fixture `fixtures/autonomy/guard.json`: ca chặn đi kèm ca đối chứng không chặn oan. Trần byte của `.claude/hooks` rất sát: thêm mã thì cắt chữ thừa chỗ khác.
- **Test cần git:** tự đặt `user.name`/`user.email` trong repo tạm; runner CI không có cấu hình toàn cục.
- **Bench tự hành:** ID 🔴/🟠 `đã sửa` là bắt buộc phủ; chưa có ca thì khai vào `fixtures/autonomy/scope.json` kèm lý do.
- **Test chạy lâu** (> ~1 s) ghi trọng số ở `shard-weights.json` để CI chia shard đều.
