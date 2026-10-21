# SPEC-app — Ứng dụng cục bộ `xt.py app`

| Trường | Giá trị |
|---|---|
| ID tính năng | F-001…F-007 (yêu cầu gốc: chủ repo 2026-10-21, D-126) |
| Trạng thái | Approved for implementation (phiên chính tự duyệt, ADR-0008) |
| Phiên bản | 1 — hợp đồng API chốt trước mọi task màn (`LOOP-ORCH-007`, T-1911) |
| Kiến trúc, bảo mật | [ADR-0038](../adr/0038-local-app-on-xt.md) — file này không chép lại, chỉ chốt giao ước |
| Kế hoạch | [`PLAN-3.14-app.md`](../autopilot/PLAN-3.14-app.md) |

## 1. User story
Là người dùng khung (chủ repo khung hoặc chủ dự án đích), tôi muốn mở một trang web cục bộ bằng một lệnh, để xem thư viện
yêu cầu, ghép blueprint, tiến độ, kế hoạch và việc chờ người mà không đọc markdown hay gõ nhiều lệnh. App **không chạy
lệnh** (Gate, merge, push, defer): chỉ hiển thị lệnh để chép. Ngoại lệ duy nhất: ghi `BLUEPRINT.md` (F-003).

## 2. Quy ước chung (mọi endpoint)

### 2.1 Khởi động và token
- `xt.py app` bind `127.0.0.1`, in `http://127.0.0.1:<port>/#t=<token>`; token = `secrets.token_urlsafe(32)`, sinh mỗi lần chạy.
- `app.js` đọc `t` từ `location.hash`, lưu `sessionStorage["xt-token"]`, rồi xoá fragment bằng
  `history.replaceState(null, "", location.pathname)`; mọi `fetch("/api/…")` gửi header `X-XT-Token: <token>`.
- Không có token trong `sessionStorage` (mở lại tab không có fragment) → UI hiện thông báo "Mở lại bằng URL in ở terminal".
- File tĩnh (`/`, `/app.css`, `/app.js`, `/views/*.js`) không cần token; mọi `/api/*` cần.

### 2.2 Thứ tự kiểm một request (dừng ở lỗi đầu tiên)
| # | Kiểm | Lỗi |
|---|---|---|
| 1 | `Host` ∈ {`127.0.0.1:<port>`, `localhost:<port>`} | 421 |
| 2 | Có `Origin` thì = `http://127.0.0.1:<port>` hoặc `http://localhost:<port>` | 403 |
| 3 | Đường dẫn có trong bảng tĩnh hoặc bảng `ROUTES` (không ghép đường từ URL; `..`, `%2e%2e`, symlink → không có trong bảng) | 404 |
| 4 | Method có trong `ROUTES` của đường đó (tĩnh: chỉ `GET`/`HEAD`) | 405 kèm `Allow` |
| 5 | `/api/*`: `X-XT-Token` khớp (`hmac.compare_digest`) | 401 |
| 6 | `POST`: `Content-Type` bắt đầu bằng `application/json` | 415 |
| 7 | `POST`: `Content-Length` có, ≤ 65 536 byte; `Sec-Fetch-Site` có thì = `same-origin` | 413 / 403 |
| 8 | `POST`: thân là JSON object UTF-8 | 400 |
| 9 | Tham số query thiếu/sai (theo từng endpoint) | 400 |
| 10 | Tài nguyên không có (file, `rel`, PLAN) | 404 |

### 2.3 Response
- Thành công: `200`, `Content-Type: application/json; charset=utf-8`, thân là object JSON (khoá dưới đây; được thêm khoá,
  không đổi nghĩa khoá đã có).
- Lỗi: mã ở 2.2, thân `{"error": "<thông điệp tiếng Việt một dòng>"}`; không traceback, không đường dẫn tuyệt đối ngoài dự án.
- Lỗi không lường trước trong handler → `500 {"error": "lỗi máy chủ"}`, chi tiết chỉ ra stderr (không token).
- Header cố định trên mọi response (kể cả lỗi, file tĩnh): theo ADR-0038 §2; `/api/*` thêm `Cache-Control: no-store`.
- Đường dẫn trong tham số (`path=`, `rel=`) là POSIX tương đối theo gốc dự án (hoặc theo `framework/`), không tuyệt đối,
  không `..`, sau `resolve()` phải nằm trong gốc tương ứng — sai → 400.

### 2.4 Đăng ký route
Mỗi `scripts/xt_app/api_<màn>.py` khai `ROUTES: Dict[Tuple[str, str], Callable[[Ctx], Tuple[int, Dict[str, Any]]]]`,
khoá `(method, path)`; `Ctx` có `base` (gốc dự án), `framework` (thư mục khung), `query` (`Dict[str, List[str]]`), `body`
(object JSON hoặc `None`). Máy chủ nạp mọi module `api_*`; trùng khoá → lỗi khi khởi động. `--smoke` gọi mọi route
`GET`; route có tham số bắt buộc khai query mẫu trong `SMOKE: Dict[path, query]` của module (vd
`{"/api/catalog/module": "rel=00-method/conventions"}`), máy chủ gom bằng `load_smoke()`.

## 3. API

| Endpoint | Tham số | Thân 200 (khoá) | Lỗi riêng | Task |
|---|---|---|---|---|
| `GET /api/health` | — | `ok: true`, `version` (VERSION khung), `project` (tên thư mục gốc) | — | T-1912 |
| `GET /api/overview` | — | `project`, `version`, `loop: {verdict, reason}`, `blueprint: {must_done, must_total} \| null`, `plan: {path, open} \| null`, `pending_human` (int) | — | T-1921 |
| `GET /api/catalog` | `q` (tuỳ chọn, ≥ 2 ký tự) | `areas: [{dir, title, modules: [{rel, title, kind, prefix, counts: {MUST, SHOULD, MAY}}]}]`; có `q` → thêm `hits: [{id, level, rel, text}]` (≤ 200, `truncated`) | 400 `q` < 2 ký tự | T-1922 |
| `GET /api/catalog/module` | `rel` (bắt buộc, theo `framework/`) | `rel`, `title`, `kind`, `items: [{id, level, scale, text, check, source}]` | 400 thiếu `rel`; 404 `rel` lạ | T-1922 |
| `GET /api/compose/options` | — | `profiles: [{slug, title}]`, `industries: [{slug, title}]`, `modules: [rel]`, `features: [str]`, `scales: ["S","M","L"]` | — | T-1931 |
| `GET /api/compose` | `profile` (bắt buộc), `scale` (bắt buộc), `industry`, `add`, `feature` (lặp được) | `counts: {MUST, SHOULD, MAY}`, `markdown` (≤ 512 KB), `truncated`, `promoted: [id]` | 400 hồ sơ/ngành/module/quy mô lạ | T-1931 |
| `POST /api/blueprint` | thân `{profile, scale, industry: [], add: [], feature: [], out: "BLUEPRINT.md"}` | `written: [path]`, `kept`, `dropped`, `stale` (int) | 400 `out` ngoài dự án/không `.md`/tham số lạ | T-1931 |
| `GET /api/blueprint` | `path` (mặc định `BLUEPRINT.md`) | `path`, `levels: {MUST: {done, open, waived}, …}`, `modules: [{module, must_done, must_total, should_done, should_total}]`, `open_must: [{id, module, text}]` (≤ 200), `truncated`, `bad_lines`, `check_cmd` | 400 path sai; 404 không có file khi `path` được truyền (vắng `path` mà chưa có `BLUEPRINT.md` → 200, `path: null`) | T-1941 |
| `GET /api/plans` | — | `plans: [{path, open, done, dropped, active}]` (mọi `docs/autopilot/PLAN*.md`; `active` = PLAN của vòng) | — | T-1951 |
| `GET /api/plan` | `path` (vắng → PLAN của vòng rồi `docs/autopilot/PLAN.md`, không có → 200 rỗng, như `plan waves`; có mà rỗng → 400), `max` (1–10, mặc định 5) | `path`, `sections: [{title, tasks: [{id, state, title, gate, after, files, tier}]}]`, `waves`, `blocked` (= `plan waves --json`), `overlaps`, `cycles`, `unknown_after`, `bad_links`, `deferred: {id: reason}` | 400 path sai/`max` sai; 404 | T-1951 |
| `GET /api/loop` | — | `verdict`, `reason`, `iterations`, `max_iterations`, `deadline`, `deferred: [{id, reason, at}]`, `checkpoint`, `stats` (như `loop stats --json` hoặc `null`) | — (không có vòng → `verdict: "inactive"`) | T-1961 |
| `GET /api/decisions` | `q` (tuỳ chọn) | `decisions: [{id, at, question, options, choice, why, revert}]` mới nhất trước (≤ 200, `truncated`) | — | T-1961 |
| `GET /api/adrs` | — | `adrs: [{number, title, status, path}]` | — | T-1961 |
| `GET /api/prs` | — | `available: true`, `prs: [{number, title, head_sha, lane, action, reasons}]`; không có `gh`/chưa đăng nhập/hết giờ → `available: false`, `reason` | — (luôn 200) | T-1971 |
| `GET /api/pr-stats` | `days` (1–90, mặc định 7) | như `pr stats --json`, thêm `available` | 400 `days` sai | T-1971 |

Đọc file mới mỗi request (hoặc cache theo `mtime`); không ghi gì ngoài `POST /api/blueprint`. `GET /api/prs` chỉ gọi REST
`GET` qua `_gh_api`, không ghi sổ review, không gọi merge.

## 4. Màn và tiêu chí chấp nhận

### F-001 Tổng quan (`#/`, `views/overview.js`)
- S-001 Given dự án có `BLUEPRINT.md` và vòng đang chạy, When mở app, Then thấy thẻ MUST đạt/tổng, số task mở, số việc chờ
  người, verdict vòng; bấm thẻ chuyển sang màn chi tiết tương ứng.
- S-002 Given không có `BLUEPRINT.md`, không có vòng, When mở app, Then thẻ blueprint ghi "chưa có" kèm lệnh `compose` để
  chép, thẻ vòng ghi `inactive`; không lỗi.

### F-002 Thư viện yêu cầu (`#/catalog`)
- S-003 Given khung hợp lệ, When mở màn, Then thấy cây mảng → module với số MUST/SHOULD/MAY; chọn module thấy từng mục
  (ID, mức, quy mô, nội dung, `Kiểm`, `Nguồn`).
- S-004 When gõ `BASE-SEC` hoặc một chữ ≥ 2 ký tự vào ô tìm, Then danh sách kết quả theo ID/chữ; < 2 ký tự không gọi API.

### F-003 Ghép blueprint (`#/compose`)
- S-005 Given chọn hồ sơ, quy mô, ngành, When xem trước, Then thấy số mục theo mức và nội dung markdown; tải được `.md`.
- S-006 Given `BLUEPRINT.md` đã có tick, When bấm "Ghi BLUEPRINT.md" và xác nhận (hộp thoại nêu số mục giữ/bỏ), Then file
  ghi bằng đúng đường của `compose --out` — tick theo ID giữ nguyên; API trả `kept`/`dropped`/`stale`.
- S-007 Given thân POST có `out: "../x.md"` hoặc `out: "a.txt"`, When gửi, Then 400, không ghi file nào.

### F-004 Tiến độ blueprint (`#/blueprint`)
- S-008 Given `BLUEPRINT.md`, When mở màn, Then thấy thanh tiến độ tổng và theo module, danh sách MUST chưa đạt có lọc, lệnh
  `blueprint-status --strict` để chép. Không có file → hướng dẫn sang F-003.

### F-005 Kế hoạch và phân chia việc (`#/plan`)
- S-009 Given nhiều `PLAN*.md`, When chọn một PLAN, Then bảng task theo lát có lọc trạng thái, cột "Đợt" (cùng kết quả
  `xt.py plan waves`), tầng executor, Gate chép được.
- S-010 Given PLAN có chu trình `sau:`, ghi chú hỏng hoặc task defer, When mở, Then các task đó nằm ở mục "Bị chặn" kèm lý do.

### F-006 Vòng tự động, việc chờ người, quyết định (`#/loop`)
- S-011 Given vòng có task defer, When mở màn, Then mục "Việc cần người" đứng đầu (ID, lý do, thời điểm) và điểm dừng của PLAN.
- S-012 When tìm "merge" trong quyết định, Then chỉ D-NNN có chữ đó; ADR liệt kê kèm dòng trạng thái.

### F-007 PR, chỉ đọc (`#/pr`)
- S-013 Given `gh` đã đăng nhập, When mở màn, Then bảng PR mở (làn, hành động kế, lý do), số đo lead time/CI, lệnh `pr next
  --pr N` để chép; không có nút merge.
- S-014 Given không có `gh`, When mở màn, Then thông báo lý do, các màn khác vẫn chạy.

## 5. Ca biên
| Nhóm | Ca cụ thể | Hành vi mong đợi | Scenario |
|---|---|---|---|
| Rỗng/null | Không blueprint, không vòng, không PLAN, `DECISIONS.md` vắng | 200 với `null`/danh sách rỗng, UI hiện trạng thái rỗng | S-002, S-008 |
| Cực đại/độ dài | Thân POST > 64 KB; markdown compose > 512 KB; > 200 kết quả | 413; cắt kèm `truncated: true` | S-005 |
| Trùng lặp/idempotency | Bấm "Ghi" hai lần cùng tham số | Lần hai ghi cùng nội dung (`compose --out` giữ tick theo ID) | S-006 |
| Song song | Hai tab cùng ghi `BLUEPRINT.md` | `write_atomic` — bản ghi sau thắng, file không hỏng | S-006 |
| Mất mạng giữa chừng | Máy chủ tắt khi đang dùng; `gh` hết giờ | UI hiện lỗi kết nối, nút thử lại; `/api/prs` → `available: false` | S-014 |
| Thời gian/múi giờ | Thời điểm D-NNN, defer, hạn vòng | Lưu ISO 8601 UTC như file nguồn; UI hiển thị theo giờ máy | S-011 |
| Quyền | Trang khác gọi API (CSRF), DNS rebinding, thiếu/sai token, `../`, symlink | 403/421/401/404 theo 2.2; test đối kháng T-1912 | 2.2 |
| Tiền/đơn vị | Không áp dụng — app không xử lý tiền | — | — |

## 6. Phi chức năng
- Tiếp cận: WCAG 2.2 AA (`PRF-WEB-006`), đi được bằng bàn phím, focus thấy rõ, `lang="vi"`, tương phản qua `xt.py contrast`.
- Bố cục co từ 360 px; sáng/tối theo `prefers-color-scheme`.
- `xt.py` khởi động lệnh khác không nạp `xt_app` (import lười, test ở T-1913).
- JS dựng DOM bằng `textContent`/`createElement` (test tĩnh T-1914).

## 7. Câu hỏi mở
Không còn — các điểm hở đã quyết ở ADR-0038 và D-126.
