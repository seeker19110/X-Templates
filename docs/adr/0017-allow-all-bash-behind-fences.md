# ADR-0017: Cho phép mọi lệnh Bash, hàng rào là deny/ask + hook guard

- **Trạng thái:** Đã chấp nhận
- **Trạng thái triển khai:** Đã triển khai (`.claude/settings.json` `permissions.allow` gồm `Bash`; test
  `tests/test_hooks.py::SettingsJsonTest::test_bash_allowed_except_fences`)
- **Ngày:** 2026-10-16
- **Làm rõ:** ADR-0002 (harness fail-closed về hành động nguy hiểm) — không thay

## Bối cảnh

Chủ repo yêu cầu (2026-10-16): "chấp nhận tất cả mọi loại lệnh, trừ các lệnh cấm" — vẫn bị hỏi các lệnh git không cấm.
Nguyên nhân: `permissions.allow` của `.claude/settings.json` là danh sách hẹp (`git status/diff/log/add/commit/fetch/…`);
`git push`, `git checkout <nhánh>`, `git rm/mv/restore/rev-parse/remote/tag/cherry-pick`… nằm ngoài nên ở chế độ quyền
`default` phiên nào cũng hỏi. `permissions.defaultMode` `auto`/`bypassPermissions` bị Claude Code bỏ qua ở settings dự án
(ADR-0009), nên settings dự án chỉ mở rộng được bằng luật `allow`.

Dữ kiện (code.claude.com/docs/en/permissions, ADR-0013): thứ tự đánh giá là hook → `deny` → `ask` → chế độ → `allow`;
luật `Bash` không đối số khớp mọi lệnh Bash; `deny`/`ask` thắng `allow`; hook PreToolUse trả `deny`/`ask` vẫn có hiệu lực.

## Quyết định

1. `permissions.allow` gồm `Bash` (mọi lệnh) thay cho danh sách `Bash(...)` cũ — các mục cũ thừa nên bỏ.
2. Giữ nguyên hàng rào: `deny` (sudo, `rm -rf /`/`~`, force-push, `reset --hard`, `git clean`, `dd`, `mkfs`, đọc `.env`/khoá),
   `ask` (`git merge`, `git rebase`, `gh release`, `npm publish`, `docker push`) và hook guard `pre-bash-guard.sh`
   (lệnh phá huỷ, `curl|sh`, push thẳng nhánh chính, merge PR ngoài `merge-check`, xoá ngoài dự án, sửa cấu hình cổng…).
3. Áp cho repo khung và mẫu dự án đích (`install.py` copy cùng file; dự án đã có `settings.json` chỉ được gộp
   `hooks`, quyền riêng giữ nguyên — muốn thì thêm tay `Bash` vào `allow`).

## Lý do

- Người dùng có quyền cuối (AGENTS.md §1); "lệnh cấm" của khung là `deny` + guard, đã cưỡng chế bằng máy.
- Hỏi quyền cho lệnh vô hại làm autopilot đứng chờ người (`LOOP-CTX-020`) mà không thêm an toàn.

## Các phương án đã cân nhắc

- **Chỉ `Bash(git *)`**: hết hỏi git nhưng lệnh khác ngoài danh sách vẫn hỏi; không đáp ứng "mọi loại lệnh". Loại.
- **Bỏ thêm `git merge`/`git rebase` khỏi `ask`**: chủ repo chọn giữ. Loại.
- **Không đổi repo, người bật `--permission-mode auto`**: phải nhớ cờ mỗi phiên; không giúp phiên `default`. Loại.

## Hệ quả

- Lệnh guard không nhận ra (alias, biến chứa cờ, `eval` phức tạp — giới hạn đã biết ở CHANGELOG) và lệnh khi guard lỗi
  (fail-open về luồng) chạy không hỏi; trước đây lớp hỏi quyền mặc định đỡ phần này. Lớp đỡ còn lại: `deny`, CI, sandbox
  phiên (`LOOP-HARNESS-022`).
- Muốn lấy lại lớp hỏi mặc định: thay `Bash` bằng danh sách `Bash(...)` cụ thể trong settings của dự án.
