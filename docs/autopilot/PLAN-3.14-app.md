# PLAN-3.14-app.md — Khung X-Templates · ứng dụng cục bộ `xt.py app` và chia việc bằng máy

> Lập ngày 2026-10-21. Chủ repo hỏi: "biến dự án này thành app và phân chia công việc được không?". Phiên chính tự duyệt
> hướng và PLAN (D-126, ADR-0008). Kiến trúc và bảo mật: [ADR-0038](../adr/0038-local-app-on-xt.md).
>
> **Cú pháp bắt buộc cho máy:** mỗi task một dòng `- [ ] \`T-NNNN\` <việc> — Gate: \`<lệnh>\``.

## Tóm tắt (cổng duyệt — phiên chính tự duyệt, D-126)
- Vấn đề: khung chỉ dùng được qua 28 lệnh CLI, 186 file markdown và phiên agent. Việc người cần xem nằm rải rác (tiến độ
  blueprint, PLAN, việc chờ người, 125 quyết định, PR). Chia việc song song chỉ có `loop next`, cần vòng đang chạy và không
  xếp thành đợt.
- Kết quả khi xong: `python3 scripts/xt.py app` (và `.xtemplates/scripts/xt.py app` ở dự án đích) mở giao diện web trên
  127.0.0.1 gồm 7 màn: Tổng quan · Thư viện yêu cầu · Ghép blueprint · Tiến độ blueprint · Kế hoạch và phân chia việc ·
  Vòng tự động/việc chờ người/quyết định · PR. Thêm `xt.py plan waves` xếp task thành đợt chạy song song (dùng ngay ở Lát 1).
- Stack: Python ≥ 3.11 stdlib (`http.server`), HTML/CSS/JS thuần không build; 0 phụ thuộc runtime mới. Phụ thuộc dev chỉ ở
  Lát 10 (E2E: Playwright Python 1.64.0 Apache-2.0, axe-core 4.14.0 MPL-2.0 — xác minh 2026-10-21 trong ADR-0038), có D-NNN
  riêng.
- Không làm: web app lưu trữ hay đa người dùng, đăng nhập, app chạy lệnh (Gate/merge/push/defer — giữ ở CLI có guard),
  build JS/npm, app desktop/mobile (ADR-0038 §Phương án).
- Nhánh: phiên một nhánh → lát đi tuần tự, mỗi lát một PR (lát vượt 150 dòng thì tách theo task). 3.13.0 đã cắt (#202);
  việc còn lại của PLAN-3.13 (tag T-1842, dự án đích T-1843, task hoãn chờ người) không giao file với PLAN này, không chặn.
- Rủi ro: RK-1 trang web khác đọc dữ liệu qua trình duyệt (CSRF, DNS rebinding) → loopback + token + `Host`/`Origin`, test
  đối kháng ở T-1912 · RK-2 XSS từ nội dung markdown/tiêu đề PR → chỉ `textContent`, CSP không inline, test tĩnh T-1914 ·
  RK-3 app thành đường vòng qua guard → app không chạy lệnh, test cấm `subprocess` trong `scripts/xt_app/` ngoài `_gh_api`
  · RK-4 `xt.py` khởi động chậm hơn → import lười, test `xt_app` không có trong `sys.modules` sau lệnh khác · RK-5 E2E cần
  trình duyệt ở CI → lát riêng, research trước (T-1991).

## Ngân sách (4 con số)
- Số vòng tối đa: `max(40, 8 × task)` (`loop init --single-session` tính)
- Chi phí: 0 đồng ngoài phiên; token phiên theo hạn mức
- Timeout mỗi lệnh Gate: 1800 giây (`XT_RECORD_TIMEOUT` mặc định)
- Ngày hết hạn: 24 giờ sau `loop init` (`--hours 24`)

## Điểm dừng bắt buộc (`loop defer`; `loop block` khi mọi việc còn lại phụ thuộc)
- Tag `v3.14.0` khi thiếu secret `XT_RELEASE_TOKEN` (chủ repo đặt)
- Nâng dự án đích: chỉ mở PR, không merge thay chủ dự án đích

## Phân chia việc
Song song chỉ khi `files:` không giao nhau và `sau:` đã thoả (`LOOP-ORCH-006`), ≤ 5 đồng thời (`LOOP-ORCH-008`); hợp đồng
API T-1911 chốt trước mọi task màn (`LOOP-ORCH-007`). Từ Lát 1, `xt.py plan waves --plan docs/autopilot/PLAN-3.14-app.md`
tính lại bảng này từ dòng task.

| Đợt | Task chạy song song | Ai làm |
|---|---|---|
| 1 | T-1901 · T-1911 · T-1991 | `executor` · phiên chính (hợp đồng) · `researcher` |
| 2 | T-1902 · T-1912 · T-1914 | `executor` · `executor-deep` · `executor` |
| 3 | T-1913 · T-1915 · T-1921 · T-1922 · T-1941 | `executor` × 5 |
| 4 | T-1931 · T-1951 · T-1961 · T-1971 | `executor-deep` · `executor` · `executor` · `executor-deep` |
| 5 | T-1923 · T-1924 · T-1932 · T-1942 · T-1952 | `executor` × 5 (mỗi task một file `views/`) |
| 6 | T-1962 · T-1972 · T-1981 | `executor` × 3 |
| 7–12 | T-1982 → T-1992 → T-1993 → T-1996 → T-1997 → T-1998 | phiên chính · `executor-deep` · phiên chính (blueprint, phát hành, PR dự án đích) |

Bảng tính bằng `parse_plan` + `_path_overlap` của `xt.py` ngày 2026-10-21 (0 ghi chú hỏng, 0 chu trình): 29 task, 12 đợt
thay vì 29 bước nối tiếp.

Người (chủ repo): chỉ secret `XT_RELEASE_TOKEN` nếu chưa có và merge PR ở hai dự án đích. Phiên chính: quyết định D-NNN,
chạy lại Gate bằng `loop record` trước khi tick (`LOOP-ORCH-004`), mở PR, merge theo `pr next`.

## Task

### Lát 1 — Chia việc bằng máy: `xt.py plan waves`
- [x] `T-1901` `plan_waves(tasks, deferred, max_parallel=5)` (hàm thuần) + `xt.py plan waves [--plan P] [--max N] [--json]` (mặc định `docs/autopilot/PLAN.md`, không cần vòng): đợt k nhận task `[ ]` mà mọi `sau:` trong file đã đóng hoặc thuộc đợt < k; trong đợt xếp tham lam theo thứ tự PLAN thành nhóm có `files:` đôi một không giao (`_path_overlap`), task thiếu `files:` đứng riêng, ≤ N task/nhóm; task trên chu trình, `bad_links` hoặc đã defer → `blocked` kèm lý do; JSON `{"waves": [{"wave": 1, "tasks": [{"id", "title", "tier", "files"}]}], "blocked": [{"id", "reason"}]}`; văn bản in mỗi đợt một dòng (files: scripts/xt.py, tests/test_plan_waves.py) — Gate: `python3 -m unittest tests.test_plan_waves && python3 scripts/xt.py plan waves --plan docs/autopilot/PLAN-3.14-app.md --json`
- [x] `T-1902` Tài liệu: `orchestration-and-subagents.md` §Mô hình nhánh khi song song nhắc `plan waves` (đổi chữ, giữ ID), README §Công cụ thêm dòng `plan waves`, CHANGELOG Unreleased (sau: T-1901; files: framework/11-autonomous-loop/orchestration-and-subagents.md, README.md, CHANGELOG.md) — Gate: `python3 scripts/xt.py checks && python3 scripts/check-links.py && python3 -m unittest tests.test_docs_budget`

### Lát 2 — Khung sống của app (walking skeleton) và hợp đồng API
- [x] `T-1911` Hợp đồng `docs/specs/SPEC-app.md`: F-001…F-007 (mỗi màn), Given/When/Then tối thiểu mỗi màn; bảng API `GET /api/health`, `/api/overview`, `/api/catalog`, `/api/catalog/module?rel=`, `/api/compose/options`, `/api/compose?…`, `/api/blueprint?path=`, `/api/plans`, `/api/plan?path=`, `/api/loop`, `/api/decisions?q=`, `/api/adrs`, `/api/prs`, `/api/pr-stats?days=`, `POST /api/blueprint` — dạng JSON từng endpoint, lỗi `{"error": …}` với 400/401/403/404/405/413/415/421, giới hạn thân 64 KB; quy ước token (`#t=` → `sessionStorage`, xoá fragment bằng `history.replaceState`, header `X-XT-Token`) (files: docs/specs/SPEC-app.md) — Gate: `python3 scripts/check-links.py && grep -q "POST /api/blueprint" docs/specs/SPEC-app.md`
- [x] `T-1912` Máy chủ `scripts/xt_app/` (`__init__.py`, `server.py`) theo ADR-0038 §2: `ThreadingHTTPServer` bind `127.0.0.1` cứng, cổng 0 mặc định; handler trên `BaseHTTPRequestHandler`; token `secrets.token_urlsafe(32)` + `hmac.compare_digest`; kiểm `Host` (421), `Origin` (403), POST (`Content-Type`, ≤ 64 KB, `Sec-Fetch-Site`); file tĩnh theo bảng lập lúc khởi động từ `scripts/app/`; header bảo mật cố định; nạp mọi `xt_app.api_*` có `ROUTES`; log truy cập không ghi token; `GET /api/health`. Test đối kháng: thiếu/sai token, `Host: evil.example`, `Origin` lạ, `../` và `%2e%2e`, symlink trong `scripts/app/`, method lạ, thân quá cỡ, header bảo mật đủ trên mọi response (sau: T-1911; files: scripts/xt_app/__init__.py, scripts/xt_app/server.py, tests/test_app_server.py; exec: deep) — Gate: `python3 -m unittest tests.test_app_server`
- [x] `T-1913` Lệnh `xt.py app [--port N] [--no-open] [--smoke]`: import lười `xt_app` (dùng module `xt` đang chạy, không nạp lại), in URL `http://127.0.0.1:<port>/#t=<token>`, mở trình duyệt trừ `--no-open`, Ctrl-C thoát sạch exit 0; `--smoke` khởi động cổng 0, gọi mọi `GET /api/*` đã đăng ký kèm token, exit 0 khi tất cả 200 rồi tắt; test lệnh khác không nạp `xt_app` (sau: T-1912; files: scripts/xt.py, tests/test_app_cli.py) — Gate: `python3 -m unittest tests.test_app_cli && python3 scripts/xt.py app --smoke`
- [x] `T-1914` Vỏ UI `scripts/app/`: `index.html` (`lang="vi"`, nav 7 màn, không script/style inline), `app.css` (token màu sáng/tối theo `prefers-color-scheme`, focus thấy rõ, bố cục co từ 360 px), `app.js` (router hash, `api()` gắn token, trạng thái đang tải/rỗng/lỗi), `views/<màn>.js` cho 7 màn (khung "chưa làm"); `tests/test_app_static.py` kiểm: không `innerHTML`/`outerHTML`/`insertAdjacentHTML`/`document.write`/`eval`/`new Function`, không thuộc tính `on*=`/`style=` trong HTML, mọi view trong nav có file, UTF-8 (sau: T-1911; files: scripts/app/index.html, scripts/app/app.css, scripts/app/app.js, scripts/app/views/, tests/test_app_static.py) — Gate: `python3 -m unittest tests.test_app_static && python3 scripts/xt.py contrast scripts/app/app.css`
- [x] `T-1915` Cổng phủ gói mới (sửa cấu hình cổng — nêu lý do trong commit): `xt.yaml` `typecheck` thêm `scripts/xt_app`; kiểm `format`/`lint`/coverage (`source = scripts`) đã phủ `scripts/xt_app/`; `xt.py test-select` ánh xạ `scripts/xt_app/*.py` → `tests/test_app_*.py`; đo lại `tests/shard-weights.json` (sau: T-1912; files: xt.yaml, tests/shard-weights.json) — Gate: `scripts/dev-task.sh typecheck && scripts/dev-task.sh lint`

### Lát 3 — Tổng quan và Thư viện yêu cầu (F-001, F-002)
- [x] `T-1921` `api_overview.py`: `GET /api/overview` → tên dự án, `VERSION` khung (repo khung hoặc `.xtemplates/VERSION`), `loop_verdict` + lý do, MUST đạt/tổng của `BLUEPRINT.md` (vắng → `null`), số task mở của PLAN của vòng hoặc `docs/autopilot/PLAN.md`, số việc chờ người (sau: T-1912; files: scripts/xt_app/api_overview.py, tests/test_app_overview.py) — Gate: `python3 -m unittest tests.test_app_overview`
- [x] `T-1922` `api_catalog.py`: `GET /api/catalog` (cây mảng → file: `rel`, `title`, `kind`, `prefix`, số mục theo mức) và `GET /api/catalog/module?rel=` (mục: ID, mức, ngưỡng quy mô, nội dung, `Kiểm`, `Nguồn`) + `?q=` tìm theo ID/chữ; `load_docs` nạp một lần, nạp lại khi mtime đổi; `rel` lạ hoặc ngoài `framework/` → 404; đo cỡ JSON cây (ghi vào test, trần 300 KB) (sau: T-1912; files: scripts/xt_app/api_catalog.py, tests/test_app_catalog.py) — Gate: `python3 -m unittest tests.test_app_catalog`
- [x] `T-1923` `views/overview.js`: thẻ số (MUST %, task mở, việc chờ người, verdict vòng), mỗi thẻ dẫn sang màn chi tiết (sau: T-1913, T-1914, T-1921; files: scripts/app/views/overview.js) — Gate: `python3 -m unittest tests.test_app_static && python3 scripts/xt.py app --smoke`
- [x] `T-1924` `views/catalog.js`: cây mảng/module, lọc mức MUST/SHOULD/MAY, ô tìm ID/chữ, chi tiết mục, đường dẫn file nguồn (sau: T-1913, T-1914, T-1922; files: scripts/app/views/catalog.js) — Gate: `python3 -m unittest tests.test_app_static && python3 scripts/xt.py app --smoke`

### Lát 4 — Ghép blueprint (F-003)
- [x] `T-1931` `api_compose.py`: `GET /api/compose/options` (hồ sơ, ngành, module, fact `--feature`, quy mô) và `GET /api/compose?profile=&industry=&scale=&add=&feature=` → số MUST/SHOULD/MAY + markdown xem trước (cắt ở 512 KB); `POST /api/blueprint` ghi `BLUEPRINT.md` (+ `-BACKLOG`) bằng đúng hàm của `compose --out` (giữ tick/miễn trừ theo ID — tách hàm khỏi `cmd_compose` nếu cần, CLI không đổi hành vi), trả `kept`/`dropped`/`stale`; đường ghi ngoài dự án → 400 (sau: T-1912; files: scripts/xt_app/api_compose.py, tests/test_app_compose.py, scripts/xt.py; exec: deep) — Gate: `python3 -m unittest tests.test_app_compose && python3 -m unittest tests.test_xt`
- [x] `T-1932` `views/compose.js`: form chọn hồ sơ/ngành (nhiều)/quy mô/module thêm/fact, xem trước số mục và nội dung, tải `.md`, nút "Ghi BLUEPRINT.md" có bước xác nhận nêu số mục giữ/bỏ (sau: T-1913, T-1914, T-1931; files: scripts/app/views/compose.js) — Gate: `python3 -m unittest tests.test_app_static && python3 scripts/xt.py app --smoke`

### Lát 5 — Tiến độ blueprint (F-004)
- [x] `T-1941` `api_blueprint.py`: `GET /api/blueprint?path=BLUEPRINT.md` → `blueprint_status` + theo module (đạt/tổng MUST, SHOULD) + danh sách MUST chưa đạt (≤ 200, có `truncated`); `path` ngoài dự án hoặc không phải `.md` → 400 (sau: T-1912; files: scripts/xt_app/api_blueprint.py, tests/test_app_blueprint.py) — Gate: `python3 -m unittest tests.test_app_blueprint`
- [x] `T-1942` `views/blueprint.js`: thanh tiến độ tổng và theo module, danh sách MUST chưa đạt có lọc, lệnh kiểm `blueprint-status --strict` để chép (sau: T-1913, T-1914, T-1941; files: scripts/app/views/blueprint.js) — Gate: `python3 -m unittest tests.test_app_static && python3 scripts/xt.py app --smoke`

### Lát 6 — Kế hoạch và phân chia việc (F-005)
- [x] `T-1951` `api_plan.py`: `GET /api/plans` (mọi `docs/autopilot/PLAN*.md`: số task mở/xong/bỏ) và `GET /api/plan?path=` → task theo lát (ID, trạng thái, tiêu đề, Gate, phụ thuộc, phạm vi file, tầng) + `plan_waves` + `plan_overlaps` + chu trình + `unknown_after` + `bad_links` + việc đã defer (sau: T-1901, T-1912; files: scripts/xt_app/api_plan.py, tests/test_app_plan.py) — Gate: `python3 -m unittest tests.test_app_plan`
- [x] `T-1952` `views/plan.js`: chọn PLAN, bảng theo lát có lọc trạng thái, cột "Đợt" với nhóm chạy song song và tầng executor, Gate chép được, cảnh báo chu trình/ghi chú hỏng/giao file (sau: T-1913, T-1914, T-1951; files: scripts/app/views/plan.js) — Gate: `python3 -m unittest tests.test_app_static && python3 scripts/xt.py app --smoke`

### Lát 7 — Vòng tự động, việc chờ người, quyết định (F-006)
- [x] `T-1961` `api_loop.py`: `GET /api/loop` (verdict, lý do, số vòng/trần, hạn, việc defer kèm lý do, checkpoint, số đo `loop stats`; không có vòng → `inactive`), `GET /api/decisions?q=` (đọc `docs/autopilot/DECISIONS.md`: ID, thời điểm, câu hỏi, chọn, lý do, đường lùi; mới nhất trước), `GET /api/adrs` (số, tiêu đề, dòng trạng thái) (sau: T-1912; files: scripts/xt_app/api_loop.py, tests/test_app_loop.py) — Gate: `python3 -m unittest tests.test_app_loop`
- [x] `T-1962` `views/loop.js`: "Việc cần người" đứng đầu (defer + điểm dừng của PLAN), trạng thái vòng, danh sách D-NNN có tìm, ADR theo trạng thái (sau: T-1913, T-1914, T-1961; files: scripts/app/views/loop.js) — Gate: `python3 -m unittest tests.test_app_static && python3 scripts/xt.py app --smoke`

### Lát 8 — PR và merge, chỉ đọc (F-007)
- [x] `T-1971` `api_pr.py`: `GET /api/prs` (PR mở của repo qua `_gh_api` GET: số, tiêu đề, head SHA, hành động `pr next` tính chỉ đọc — không ghi sổ review, không gọi merge) và `GET /api/pr-stats?days=` (dùng hàm của `pr stats`); không có `gh`/chưa đăng nhập/hết giờ → 200 `{"available": false, "reason": …}`; test monkeypatch `_gh_api`, test cấm hành động ghi (sau: T-1912; files: scripts/xt_app/api_pr.py, tests/test_app_pr.py; exec: deep) — Gate: `python3 -m unittest tests.test_app_pr`
- [x] `T-1972` `views/pr.js`: bảng PR (làn, hành động kế, lý do), số đo lead time/CI, thông báo khi không có `gh`; lệnh `pr next --pr N` để chép, không nút merge (sau: T-1913, T-1914, T-1971; files: scripts/app/views/pr.js) — Gate: `python3 -m unittest tests.test_app_static && python3 scripts/xt.py app --smoke`

### Lát 9 — Cài vào dự án đích
- [x] `T-1981` `install.py` chép `scripts/xt_app/` và `scripts/app/` vào `.xtemplates/scripts/` (luôn cập nhật như `xt.py`, có trong `manifest.json`); `doctor` báo ⚠ khi thiếu file app (app tuỳ chọn, không ✗) (sau: T-1913, T-1914; files: scripts/install.py, tests/test_install.py, scripts/xt.py, tests/test_doctor.py) — Gate: `python3 -m unittest tests.test_install tests.test_doctor`
- [x] `T-1982` README §Ứng dụng (một lệnh chạy, 7 màn, mô hình bảo mật trỏ ADR-0038, không chạy lệnh) + thử thật trên dự án giả (sau: T-1981, T-1923, T-1924, T-1932, T-1942, T-1952, T-1962, T-1972; files: README.md) — Gate: `d="$(mktemp -d)" && python3 scripts/install.py "$d" >/dev/null && (cd "$d" && python3 .xtemplates/scripts/xt.py app --smoke); rc=$?; rm -rf "$d"; exit $rc`

### Lát 10 — E2E trình duyệt, tiếp cận, blueprint web
- [x] `T-1991` Nghiên cứu E2E (researcher): Playwright Python 1.64.0 so với điều khiển Chromium headless qua CDP chỉ stdlib; cách nạp axe-core 4.14.0 (vendored, MPL-2.0 cấp tệp, ghi nguồn theo `CMP-LIC-022`) không qua npm; cài trình duyệt ở CI (nguồn tải, giấy phép binary, telemetry); phiên chính ghi D-NNN chọn cách (files: research/) — Gate: `ls research/*-app-e2e.md`
- [ ] `T-1992` E2E `tests_e2e/` (ngoài `tests/`, bộ test chính không cần trình duyệt): viewport 1280×800 và 390×844, mọi màn tải không lỗi console, đi được bằng bàn phím, axe 0 vi phạm `critical`/`serious` (`PRF-WEB-006`); phụ thuộc ghim hash ở file requirements riêng, `license-check` + `vendor-check` xanh, `docs/ops/DEPENDENCIES.md`; job CI `app-e2e` vào `quality.needs` (sửa CI — nêu lý do trong commit) (sau: T-1991, T-1982; files: tests_e2e/, requirements-e2e.txt, .github/workflows/ci.yml, docs/ops/DEPENDENCIES.md, license-allow.json; exec: deep) — Gate: `python3 -m unittest discover -s tests_e2e`
- [ ] `T-1993` Blueprint repo khung: ghép thêm mục web áp cho app (`PRF-WEB-*`) giữ tick cũ; tick `[x]` kèm `— Kiểm:` chạy lại được, `[~] — Không áp dụng:` có lý do (HSTS trên HTTP loopback, Core Web Vitals/Lighthouse cho trang cục bộ) (sau: T-1992; files: BLUEPRINT.md, BLUEPRINT-BACKLOG.md) — Gate: `python3 scripts/xt.py blueprint-status BLUEPRINT.md --strict && grep -q "PRF-WEB-007" BLUEPRINT.md`

### Lát 11 — Cắt bản 3.14.0, dự án đích
- [ ] `T-1996` Cắt bản 3.14.0: `VERSION`, CHANGELOG `## [3.14.0]` (Dự án đích: chạy lại `install.py` để có `xt.py app` và `plan waves`), README, PROGRESS (sau: T-1993; files: VERSION, CHANGELOG.md, README.md, PROGRESS.md) — Gate: `python3 scripts/xt.py checks && grep -qx "3.14.0" VERSION`
- [ ] `T-1997` Tag `v3.14.0` qua `release-tag.yml` (`workflow_dispatch` REST) sau khi PR Lát 11 merge; thiếu `XT_RELEASE_TOKEN` hoặc tag không đẩy được → `loop defer` (sau: T-1996) — Gate: `git fetch -q --tags origin && git tag -l "v$(cat VERSION)" | grep -q .`
- [ ] `T-1998` Nâng `seeker19110/hotel-manager` và `seeker19110/X-Company` lên 3.14.0 (chạy lại `install.py`, mở PR, không merge thay chủ dự án) (sau: T-1997) — Gate: `for d in /home/user/hotel-manager /home/user/x-company; do (cd "$d" && grep -q "3.14.0" .xtemplates/VERSION && python3 .xtemplates/scripts/xt.py app --smoke) || exit 1; done`

## Ước lượng (giờ phiên agent; không cộng P50 làm ngày hứa)
| Lát | P50 | P90 |
|---|---|---|
| 1 | 1 | 2 |
| 2 | 3 | 6 |
| 3–8 (mỗi lát) | 1,5 | 3 |
| 9 | 1 | 2 |
| 10 | 3 | 6 |
| 11 | 1 | 2 |
Tổng: P50 ≈ 18 giờ · P90 ≈ 36 giờ (song song theo bảng Phân chia việc rút còn khoảng nửa).
