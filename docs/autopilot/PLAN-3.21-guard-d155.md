# PLAN-3.21-guard-d155.md — Khung X-Templates · bịt giới hạn guard xoá gốc đã biết (D-155) → bản 3.19.2/3.19.3 (đánh lại sau #247/#249)

> Lập ngày 2026-10-24. Chủ repo yêu cầu bịt "giới hạn guard đã biết (D-155)" ở PROGRESS §Tiếp theo 5. Phiên chính tự
> duyệt (D-162). Tái hiện trên HEAD bằng `guard.bash_decision` (pha harden, chính sách mặc định).
>
> **Cú pháp bắt buộc cho máy:** mỗi task một dòng `- [ ] \`T-NNNN\` <việc> — Gate: \`<lệnh>\``.

## Tóm tắt (cổng duyệt — phiên chính tự duyệt, D-162)
- Ba giới hạn D-155, đo lại: (1) **tên lệnh qua glob** — `/usr/bin/fi?d <gốc> -delete`, `/bin/r? -rf <gốc>` đều cho chạy
  (guard so tên theo chữ); (2) **công cụ khác** — `fd . -X rm -rf`, `fdfind … --exec-batch rm`, cùng họ `bfs`/`gfind`
  (cú pháp `find`) cho chạy; (3) **`~user`** — ĐÃ chặn khi user tồn tại (đo bằng `pwd.getpwnam` giả: `rm -rf ~dev`
  với home của dev là cha gốc → deny; `~nouser` không tồn tại = thư mục tương đối, đúng như shell) → chỉ ghim bằng test.
- Cách: (1) khi tên một lệnh đơn (sau gán biến/wrapper) có ký tự glob, viết lại CHUỖI LỆNH GỐC cho MỖI tên nhạy cảm khớp
  mẫu (`fnmatch`; danh sách đóng: lệnh xoá/ghi/bọc có luật riêng, shell, `RUNNERS`) rồi quét như shell lồng — giữ
  heredoc/`<(`, chịu `ScanBudget`; không đoán theo hệ tệp, kết quả không phụ thuộc máy; (2) `fd`/`fdfind`: lệnh trong `-x/-X/--exec[-batch]` quét
  như `-exec` của find, đích tìm kiếm (đối số vị trí sau pattern, `--search-path`, `--base-directory`) chạm gốc → deny
  — cùng chính sách D-153; `bfs`/`gfind` dùng thẳng luật `find`.
- Không làm: quét hệ tệp để mở glob; tên lệnh ghép lúc chạy (D-051); `rg --files | xargs rm` (đã `ask` vì không đích).
- Rủi ro: chặn oan (`fd -X rm` ở gốc dự án bị chặn như `find -delete` — lối thoát: chạy ở thư mục con, như D-153);
  glob khớp tên nhạy cảm nhưng lệnh thật khác (`s* -x` → chặn vì khớp `sudo`; mẫu toàn `*`/`?` và `sudo`/`doas` trơn không đối số bỏ). Đường lùi: revert từng lát.

## Ngân sách (4 con số)
- Số vòng tối đa: `max(40, 8 × task)` (`loop init --single-session` tính)
- Chi phí: 0 đồng ngoài phiên (không phụ thuộc mới)
- Timeout mỗi lệnh Gate: 1800 giây (`XT_RECORD_TIMEOUT` mặc định)
- Ngày hết hạn: 6 giờ sau `loop init` (`--hours 6`)

## Điểm dừng bắt buộc (`loop defer`; `loop block` khi mọi việc còn lại phụ thuộc)
- Nâng khung ở dự án đích (PR `install.py`): chủ dự án merge

## Task

### Lát 1 — Tên lệnh glob + ghim `~user`
- [x] `T-2811` guard: tên lệnh có glob (`fi?d`, `r?`, `[r]m`, `r*`) viết lại chuỗi lệnh gốc theo tên nhạy cảm khớp mẫu rồi quét như shell lồng (`_glob_rewrites` ở `bash_decision`); test deny/cho chạy + ghim `~user` (home là cha/chính gốc → deny, user không tồn tại → không đổi); CHANGELOG + VERSION 3.19.2 (đánh lại sau #247/#249; D-163 chặn thẳng glob tên trần/tuyệt đối); 🟢 review #246 (CHANGELOG 3.18.3 ghi "108 → 101 mệnh đề, bỏ 7 bản sao"; docstring test; khoảng trắng mệnh đề) (files: .claude/hooks/guard.py, tests/test_guard_d155.py, tests/test_install.py, CHANGELOG.md, VERSION) — Gate: `python3 -m unittest tests.test_guard_d155 tests.test_install`

### Lát 2 — fd / bfs / gfind
- [ ] `T-2812` guard: `fd`/`fdfind` với `-x/-X/--exec/--exec-batch` quét lệnh con như `find -exec` và chặn đích tìm kiếm chạm gốc/`.git`/hệ thống khi lệnh con xoá; `bfs`/`gfind` dùng luật `find`; test; CHANGELOG + VERSION 3.19.3; PROGRESS bỏ ba giới hạn đã bịt (sau: T-2811; files: .claude/hooks/guard.py, tests/test_guard_d155.py, CHANGELOG.md, VERSION, PROGRESS.md) — Gate: `python3 -m unittest tests.test_guard_d155`
