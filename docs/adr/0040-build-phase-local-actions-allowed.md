# ADR-0040: Pha `build` cho chạy mọi hành động chỉ tác động trong dự án hoặc thư mục tạm

- **Trạng thái:** Đã chấp nhận (chủ repo yêu cầu 2026-10-22: "pha build cho phép mọi quyền, chạy được mọi lệnh trong dự
  án, và tmp")
- **Trạng thái triển khai:** Đã triển khai — `.claude/hooks/guard.py` `build_phase`, `build_local_command`,
  `build_local_secret` (gọi ở `_scan_command`, `_write_asks`, `_interp_literal_ask`, `edit_decision`); `.claude/settings.json`
  bỏ 4 deny tĩnh; `scripts/install.py` `merge_permissions` gỡ `deny` khung từng đặt (manifest chứng minh) mà khung bỏ; test
  `tests/test_guard_build_phase.py`, `tests/test_install.py::…::test_install_removes_framework_deny_moved_to_guard`.
- **Ngày:** 2026-10-22
- **Làm rõ:** ADR-0017 (allow mọi Bash sau hàng rào), ADR-0018 (deny nguy hiểm, còn lại cho chạy), ADR-0031/0037 (pha
  build/harden — cách xác định pha dùng lại ở đây); `LOOP-HARNESS-022` (sandbox OS).

## Bối cảnh

Ở pha build chủ repo muốn agent làm nhanh nhất: mọi lệnh tác động trong dự án và `/tmp` đều chạy. Đo guard trên repo khung
(payload giả, 2026-10-22): xoá/ghi trong dự án và `/tmp`, cài phụ thuộc, deploy đã cho chạy; còn chặn `git reset --hard`,
`git clean -f`, `git checkout .`, `git stash drop`, ghi file bí mật (`.env`), `chmod 777`, `dd of=…` — bốn lệnh đầu và
`chmod`/`dd` còn bị chặn thêm bởi `permissions.deny` tĩnh trong `.claude/settings.json`, thứ không biết pha.

Có hai lớp khác ngoài guard. **Bộ phân loại của chế độ Auto** (Claude Code) chặn độc lập — chính phiên làm thay đổi này bị
nó chặn khi sửa `guard.py` và khi chạy test guard; repo không cấu hình được lớp này. Chế độ `bypassPermissions` bỏ lớp đó
và vẫn chạy hook PreToolUse lẫn `deny` (code.claude.com/docs/en/permission-modes, đọc 2026-10-22), nhưng không đặt được từ
settings dự án và có thể bị tổ chức tắt. **Sandbox** của Claude Code (`sandbox.enabled`) giới hạn ghi của Bash vào thư mục
làm việc + `$TMPDIR` ở mức hệ điều hành — đúng ranh giới "dự án và tmp" — nhưng trên Linux cần `bubblewrap` + `socat`
(container cloud hiện không có; thiếu thì chạy trần trừ khi `failIfUnavailable`), mạng đi qua allowlist, và cache ở home
(`~/.npm`, `~/.cache`) phải khai thêm (code.claude.com/docs/en/sandboxing, đọc 2026-10-22).

## Quyết định

1. **Guard theo pha.** `build_phase(root)`: `delivery_phase: build` ở CẢ `xt.yaml` của cây làm việc LẪN bản đã commit ở
   nhánh mặc định của remote (`origin/HEAD`, rồi `origin/main`, `origin/master`) — như `merge-check` (ADR-0031): nhánh
   không tự chuyển sang build cho chính nó; không đọc được → harden. `XT_GUARD_POLICY=strict` và `XT_GUARD_PHASE=harden`
   không nới (chỉ chặt hơn; bộ test luật cũ đặt `XT_GUARD_PHASE=harden`).
2. **Ở pha build cho chạy, khi đích chắc chắn trong dự án hoặc thư mục tạm** (thư mục đang đứng biết, không biến/backtick):
   `git reset --hard`, `clean -f`, `checkout -f`/`.`, `switch -f`, `restore .`, `stash drop/clear` (repo ở `cd`/`-C` tính
   vào); `chmod 777`; `dd of=`; ghi file bí mật bằng Edit/Write, bằng script trình thông dịch, hay `git checkout <ref> -- .env`.
3. **Giữ chặn ở mọi pha:** đích ngoài dự án/tmp hay không giải được; `git clean -x/-X` (xoá cả file bị bỏ qua, gồm
   `.autopilot/` — trạng thái vòng mà Stop hook đọc); ghi file bí mật bằng chuyển hướng Bash (`echo … > .env` — chủ repo từ
   chối nới, 2026-10-22); push nhánh chính, force-push, merge chưa đủ điều kiện, bật auto-merge; tắt hook, ghi hàng rào,
   ghi tay `.autopilot/`, giả dấu review; `sudo`, `mkfs`, `curl | sh`, container có quyền máy chủ; đọc file bí mật
   (`permissions.deny`); ghi công AI.
4. **Bỏ 4 deny tĩnh** (`Bash(git reset --hard *)`, `Bash(git clean -*)`, `Bash(chmod 777 *)`, `Bash(dd *)`) khỏi
   `.claude/settings.json`: guard đã chặn đúng các lệnh này ở harden (kiểm bằng `test_guard_build_phase`); deny tĩnh không
   biết pha. `install.py` gỡ chúng ở dự án đích khi manifest chứng minh khung đã đặt (như `ask`, REC-09).
5. **Chế độ quyền của phiên** (không cấu hình được từ repo): pha build chạy tốt nhất ở `bypassPermissions` khi tổ chức cho
   phép — guard vẫn chặn mục 3; còn lại dùng Auto và chấp nhận bộ phân loại có thể chặn thêm (`LOOP-STOP-025`), hoặc chế độ
   hỏi khi người trực. **Sandbox** là tuỳ chọn bật thêm (`LOOP-HARNESS-022`), khung không bật mặc định.

## Lý do

- Tiêu chí 1 (đúng và an toàn): phạm vi nới chỉ là trạng thái cục bộ của dự án — mất thay đổi chưa commit là rủi ro chủ
  repo chấp nhận ở pha build; mọi thứ ra ngoài máy hay phá hàng rào giữ nguyên.
- Tiêu chí 2 (đường lùi): đặt `delivery_phase: harden` hoặc `XT_GUARD_PHASE=harden` trả hành vi cũ tức thì; revert gỡ hẳn.
- Dùng lại cách xác định pha của `merge-check`: một nguồn sự thật, PR không tự cấp quyền.

## Các phương án đã cân nhắc

- **Bật sandbox mặc định ở settings mẫu.** Loại: thiếu `bubblewrap` thì chạy trần (lớp an toàn giả), có thì `npm`/`pip`
  vỡ vì cache ở home; mỗi stack cần allowlist riêng.
- **Guard chặn mọi ghi ngoài dự án/tmp ở pha build** (đúng nghĩa đen "chỉ trong dự án và tmp"). Loại: guard chỉ thấy
  chuyển hướng/đích tường minh, không thấy công cụ ghi cache ở home — vừa chặn oan vừa không phải ranh giới thật; ranh giới
  thật là sandbox OS (D-015).
- **Nới cả chuyển hướng Bash vào file bí mật.** Chủ repo từ chối lần sửa này (2026-10-22). Loại.

## Hệ quả

- Pha build: agent tự dọn cây làm việc, tạo `.env` cục bộ, đổi quyền file trong dự án mà không bị chặn.
- Mỗi tiến trình guard gọi `git show` tối đa 3 lần, và chỉ khi gặp lệnh/đích thuộc diện nới.
- Dự án đích: chạy lại `install.py` để nhận guard mới và gỡ deny tĩnh cũ.

## Đường lùi

`delivery_phase: harden`; hoặc `XT_GUARD_PHASE=harden` trong môi trường phiên; revert commit gỡ hẳn (deny tĩnh thêm lại
khi cài lại bản cũ).
