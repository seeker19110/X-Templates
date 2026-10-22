# ADR-0038: Ứng dụng cục bộ `xt.py app` — giao diện web trên chính hàm của `xt.py`, chỉ thư viện chuẩn, chỉ 127.0.0.1

- **Trạng thái:** Đã chấp nhận (phiên chính tự duyệt theo ADR-0008, D-126; chủ repo hỏi 2026-10-21 "biến dự án này thành
  app và phân chia công việc được không?").
- **Trạng thái triển khai:** xong ở 3.14.0 (#209, #210; tag `v3.14.0`) — [`PLAN-3.14-app.md`](../autopilot/PLAN-3.14-app.md) (T-1901…T-1998); chặn ghi đè `.md` không phải blueprint ở 3.15.6 (AUD-SEC-103).
- **Ngày:** 2026-10-21
- **Làm rõ:** ADR-0001 (khung = thư viện ID + máy ghép/kiểm), ADR-0018 (guard), ADR-0010 (`xt.pyz` chưa làm), AGENTS.md §7
  (`xt.py` chỉ stdlib Python ≥ 3.11); `LOOP-ORCH-006`/`007`/`008` (song song theo file, hợp đồng trước, ≤ 5 đồng thời).

## Bối cảnh

Khung chỉ dùng được qua CLI `xt.py` (28 lệnh), 186 file markdown (2.751 mục) và phiên agent. Việc người cần xem nằm rải
rác: tiến độ blueprint (`blueprint-status`), PLAN và task (`loop status`/`loop next`), việc chờ người (`loop defer`,
PROGRESS), 125 quyết định trong `DECISIONS.md`, trạng thái PR (`pr next`, `pr stats`). Chia việc song song hiện chỉ có
`loop next` (task sẵn sàng + cặp giao file), cần vòng đang chạy, không xếp thành đợt. Ràng buộc: `xt.py` chỉ stdlib, `mypy
--strict`, coverage 100 %, C901 ≤ 10; phần cài sang dự án đích không giả định stack (không Node); mặc định tự host; hành động
đổi trạng thái chỉ đi qua đường có guard.

## Phương án

1. **Ứng dụng web cục bộ `xt.py app`**: `http.server` stdlib trên 127.0.0.1, HTML/CSS/JS thuần (ES module, không build, không
   npm), API JSON gọi đúng hàm `xt.py` mà CLI đang dùng.
2. Site tĩnh xuất ra (GitHub Pages): chia sẻ bằng URL, nhưng không thấy trạng thái sống (vòng, PR, tiến độ) và phải chép
   logic `compose` sang JS (hai nguồn sự thật) hoặc sinh trước mọi tổ hợp hồ sơ × ngành × quy mô.
3. Web app lưu trữ (framework web + DB + đăng nhập): nhiều người, dùng trên điện thoại; cần hosting, tài khoản, khoá chỉ chủ
   dự án có (điểm dừng), phá luật stdlib, mặt tấn công lớn (xác thực, cô lập tenant), có chi phí.
4. App desktop (Tauri/Electron): thêm toolchain Rust/Node và ký số trả phí, không hơn phương án 1 về chức năng.
5. Giữ CLI (hiện trạng).

## Quyết định

Chọn **1**.

1. **Cấu trúc.** `scripts/xt_app/`: `server.py` (HTTP, bảo mật, định tuyến) và mỗi màn một module `api_<màn>.py` khai
   `ROUTES`, máy chủ tự nạp mọi `api_*` (thêm màn không sửa file chung). `scripts/app/`: `index.html`, `app.css`, `app.js`
   (vỏ, router hash, fetch có token) và `views/<màn>.js`. `xt.py app [--port N] [--no-open] [--smoke]` import lười (gói
   `xt_app` dùng module `xt` đang chạy, không nạp lại): lệnh khác không tốn thêm thời gian khởi động. Mỗi màn = một module
   Python + một module JS + một file test → giao song song theo file; hợp đồng API (`docs/specs/SPEC-app.md`) chốt trước.
2. **Bảo mật — một người, trên máy mình.**
   - Bind `127.0.0.1` cứng (`http.server` mặc định bind mọi interface), cổng mặc định 0 (ngẫu nhiên). Không có cờ đổi host.
   - Handler riêng trên `BaseHTTPRequestHandler`, không dùng `SimpleHTTPRequestHandler` (đi theo symlink, phục vụ được file
     ngoài thư mục gốc). File tĩnh tra theo bảng lập lúc khởi động từ `scripts/app/`, không ghép đường dẫn từ URL. API chỉ
     đọc file trong thư mục dự án.
   - Token ngẫu nhiên mỗi lần chạy (`secrets.token_urlsafe(32)`) nằm trong fragment URL in ra terminal (`#t=…`, không vào
     log hay `Referer`). Mọi `/api/*` đòi header token, so bằng `hmac.compare_digest`.
   - Chống DNS rebinding: `Host` phải là `127.0.0.1:<port>` hoặc `localhost:<port>`; có `Origin` thì phải trùng gốc của app.
     Request ghi (POST) đòi thêm `Content-Type: application/json`, thân ≤ 64 KB và `Sec-Fetch-Site: same-origin` khi trình
     duyệt gửi header này.
   - Header: CSP `default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self';
     base-uri 'none'; form-action 'none'; frame-ancestors 'none'`, `X-Content-Type-Options: nosniff`, `Referrer-Policy:
     no-referrer`, `Cross-Origin-Opener-Policy`/`Cross-Origin-Resource-Policy: same-origin`, `Permissions-Policy` tắt hết,
     `Cache-Control: no-store` cho API. Giá trị header không lấy từ đầu vào (`send_header` không kiểm CRLF). Không HSTS
     (HTTP loopback).
   - JS dựng DOM bằng `textContent`/`createElement`: không `innerHTML`, `eval`, `new Function`, script/style inline. Test
     tĩnh kiểm.
   - **App không chạy lệnh**: không Gate, `loop record`, merge, push, defer. Hành động đổi trạng thái giữ ở CLI và phiên
     agent có guard (ADR-0018); app chỉ hiển thị lệnh để chép. Ngoại lệ duy nhất: ghi `BLUEPRINT.md` bằng đúng đường
     `compose --out` (giữ tick theo ID). GitHub chỉ đọc qua `_gh_api` (GET).
3. **Màn** (thứ tự giá trị): Tổng quan · Thư viện yêu cầu · Ghép blueprint · Tiến độ blueprint · Kế hoạch và phân chia việc
   · Vòng tự động, việc chờ người, quyết định/ADR · PR và merge (cần `gh`, thiếu thì báo, không lỗi).
4. **Chia việc là tính năng máy, không chỉ là màn hình**: `xt.py plan waves [--plan P] [--max N] [--json]` xếp task mở
   thành **đợt** — task trong cùng đợt có `sau:` đã thoả, `files:` không giao nhau, ≤ N (mặc định 5, `LOOP-ORCH-008`),
   mang tầng executor. Autopilot và màn Kế hoạch dùng chung một hàm; không cần vòng đang chạy.
5. **Kiểm**: unittest cho API và HTTP (máy chủ cổng 0 trong thread, `http.client`), coverage 100 % như phần còn lại;
   `xt.py app --smoke` gọi mọi `GET /api/*` rồi thoát (dùng cho Gate và dự án đích); tương phản bằng `xt.py contrast
   scripts/app/app.css`; E2E trình duyệt desktop + mobile kèm axe (`PRF-WEB-006`) ở lát riêng, sau khi ghi D-NNN cho phụ
   thuộc dev.
6. **Dự án đích** nhận app qua `install.py` (chép `scripts/xt_app/` và `scripts/app/` cạnh `xt.py`); chạy `python3
   .xtemplates/scripts/xt.py app`.

Phiên bản và nguồn đã xác minh (2026-10-21):
- `http.server`: "not recommended for production. It only implements basic security checks"; bind mặc định mọi interface;
  `SimpleHTTPRequestHandler` đi theo symlink; `send_header` không kiểm CRLF; `ThreadingHTTPServer` từ 3.7; HTTPS chỉ từ 3.14
  — <https://docs.python.org/3/library/http.server.html>.
- Python 3.11 hết vá bảo mật 2027-10; 3.14.8 và 3.11.17 là bản vá mới nhất; 3.15.0 phát hành 2026-10-09 —
  <https://devguide.python.org/versions/>, <https://endoflife.date/api/python.json>.
- Chống DNS rebinding cho dịch vụ loopback: danh sách `Host` cho phép (<https://github.com/nccgroup/singularity/wiki/Preventing-DNS-Rebinding-Attacks>);
  kiểm `Origin`, bind 127.0.0.1, có xác thực (<https://modelcontextprotocol.io/specification/2025-06-18/basic/transports>).
  Chrome Local Network Access (hỏi quyền từ site công cộng vào loopback, từ Chrome 142) không thay được hai lớp này.
- CSP có `default-src`/`script-src` chặn script inline — <https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CSP>.
- E2E (lát riêng): Playwright Python 1.64.0 (Apache-2.0, Python ≥ 3.10, 2026-10-13) — <https://pypi.org/pypi/playwright/json>;
  axe-core 4.14.0 (MPL-2.0, 2026-10-05) — <https://registry.npmjs.org/axe-core/latest>; WCAG 2.2 vẫn là Recommendation
  hiện hành, WCAG 3.0 là Working Draft — <https://www.w3.org/TR/WCAG22/>.

## Lý do (tiêu chí chất lượng cuối)

1. **Đúng và an toàn**: một nguồn sự thật — app gọi cùng hàm với CLI nên không thể nói khác `loop status`; app không chạy
   lệnh nên không mở đường vòng qua guard; loopback + token + `Host`/`Origin` chặn trang web khác đọc dữ liệu.
2. **Giữ đường lùi**: gói tách rời, import lười; xoá `scripts/xt_app/`, `scripts/app/` và lệnh `app` là về hiện trạng. API
   JSON là hợp đồng dùng lại được nếu sau này cần phương án 3.
3. **Bền, đơn giản, test được**: 0 phụ thuộc runtime mới, không bước build; giữ luật stdlib và cổng 100 %.
4. **Trải nghiệm**: một lệnh mở trình duyệt, chạy offline, ở cả repo khung lẫn mọi dự án đích.

## Hệ quả

- Tốt: xem tiến độ, kế hoạch, việc chờ người, quyết định không cần đọc markdown hay gõ lệnh; `plan waves` giúp autopilot giao
  song song đúng luật file.
- Đánh đổi: một người trên một máy, không dùng từ xa hay trên điện thoại (muốn thế → ADR mới cho phương án 3). JS không có
  unit test riêng: giữ JS mỏng, logic ở Python. E2E thêm phụ thuộc dev (Playwright, axe-core vendored — MPL-2.0 cấp tệp,
  ghi nguồn theo `CMP-LIC-022`).
- Blueprint của repo khung (hồ sơ `cli-tool`) thêm các mục web áp cho app (`PRF-WEB-*`); mục không áp dụng ghi lý do (HSTS,
  Core Web Vitals trên loopback).

## Đường lùi

Revert các PR của PLAN-3.14-app; hoặc giữ `plan waves` (CLI) và bỏ phần web.
