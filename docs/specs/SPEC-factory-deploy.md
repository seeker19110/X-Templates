# SPEC-factory-deploy — Triển khai có receipt: bản dev, sổ triển khai, production

| Trường | Giá trị |
|---|---|
| ID tính năng | F-101 (lệnh triển khai + receipt + sổ), F-102 (bản dev của gói `web-api-ts`), F-103 (production) — chủ dự án 2026-11-11, ADR-0075 §Quyết định 2, 5, 6 |
| Trạng thái | Approved for implementation (phiên chính tự duyệt, ADR-0008 — D-422; sửa sau review độc lập — D-423) |
| Phiên bản | 1 — hợp đồng khoá và schema chốt trước task mã; ADR của T-3841 ghi quyết định kiến trúc và liên kết về đây, không chép lại |
| Dữ kiện | [`research/2026-11-11-factory-e2e-facts.md`](../../research/2026-11-11-factory-e2e-facts.md) §1 |
| Kế hoạch | [`PLAN-factory-e2e.md`](../autopilot/PLAN-factory-e2e.md) T-3841…T-3844, T-3860 |

## 1. User story
Là chủ dự án chỉ nêu ý tưởng, tôi muốn máy tự đưa đúng bản đã kiểm lên một môi trường chạy được, kiểm nó sống, và ghi
lại bản nào đang chạy ở đâu, để "đã phát hành" là dữ kiện máy đọc chứ không phải lời khai; hỏng thì máy tự quay về bản
trước. Trước khi tôi thiết lập gì, bản dev phải chạy được mà không cần tài khoản hay khoá của tôi.

## 2. Giao ước

### 2.1 Khoá `xt.yaml` (phẳng; trống = tính năng tắt)
| Khoá | Nghĩa |
|---|---|
| `deploy_envs` | Tên môi trường, cách nhau khoảng trắng; mỗi tên khớp `[a-z][a-z0-9]{0,15}`. `dev` là môi trường không cần uỷ quyền |
| `deploy_<env>` | Lệnh đưa ứng viên lên `<env>` |
| `smoke_<env>` | Lệnh kiểm sau khi đưa lên; exit 0 = sống. Trống → đỏ (cổng rỗng, ADR-0011) |
| `digest_<env>` | Lệnh in ra stdout **digest của bản đang phục vụ** ở `<env>` (một dòng). Bắt buộc: không có nó thì máy không biết bản đang chạy có phải ứng viên không |
| `rollback_<env>` | Lệnh quay về bản trước |
| `url_<env>` | Tuỳ chọn; địa chỉ ghi vào receipt |
| `deploy_secrets` | Tuỳ chọn; **tên** các secret mà lệnh triển khai cần, cách nhau khoảng trắng — chỉ để `admin-plan` kiểm có/thiếu, khung không đọc giá trị |

Khung không biết container hay máy chủ nào: mọi thứ nằm trong lệnh của dự án. Lệnh nhận biến môi trường:
`XT_DEPLOY_ENV`, `XT_DEPLOY_DIGEST` (= `subject.digest`), `XT_DEPLOY_ARTIFACTS` (đường artifact, cách nhau khoảng trắng),
`XT_DEPLOY_PREVIOUS` (digest bản đang phục vụ trước đó, rỗng nếu chưa có), `XT_DEPLOY_STATE` (thư mục cục bộ của môi
trường để lệnh giữ thứ cần cho quay lui).

### 2.2 Lệnh
| Lệnh | Việc | Exit |
|---|---|---|
| `xt.py deploy run --env E [--json]` | Triển khai ứng viên hiện tại lên E theo §2.3, ghi sổ | 0 `deployed` · 1 hỏng (đã quay lui hoặc quay lui hỏng) · 2 từ chối trước khi chạy · 126 guard cấm lệnh |
| `xt.py deploy rollback --env E` | Quay về bản trước theo §2.3 bước 2, 3, 6, ghi sổ | 0 · 1 · 2 · 126 |
| `xt.py deploy status [--env E] [--json]` | Đọc sổ; chỉ đọc | 0 · 2 sổ hỏng |

`deploy run` và `deploy rollback` là bước tích hợp của phiên điều phối: trong worktree song song chúng exit 2
(SPEC-factory-parallel §2.2).

### 2.3 Trình tự của `deploy run`
1. **Ứng viên:** `release_artifacts` phải khai, mọi artifact tồn tại và khớp sidecar `.sha256` nếu có → `subject`
   (`head`, `content`, `digest`) tính bằng đúng hàm của `release-check`. Thiếu → exit 2.
2. **Quyền** (E khác `dev`; áp cho cả `run` lẫn `rollback`): cây git sạch; `xt.py grant-check deploy env=E` exit 0;
   với `run` thêm: HEAD **nằm trong lịch sử nhánh chính của remote** (đọc mới từ remote, không tin ref cục bộ — mã chưa
   merge không lên production dù đã ký trên nhánh); `promotion.state` = `approved` cho đúng `subject` này; sổ có
   `dev.current` là bản `deployed` cùng `subject.digest`. Thiếu một điều → exit 2, không chạy gì.
3. **Guard:** `deploy_E`, `smoke_E`, `digest_E`, `rollback_E` qua `guard-check` trước khi chạy lệnh đầu
   (LOOP-STOP-027) → 126.
4. Chạy `deploy_E` (trần `XT_DEPLOY_TIMEOUT`, mặc định 1200 giây). Exit ≠ 0 → bước 6.
5. Chạy `smoke_E`, rồi `digest_E`. Smoke exit 0 **và** `digest_E` in đúng `XT_DEPLOY_DIGEST` → kết quả `deployed`, ghi
   sổ, exit 0. Digest khác hoặc lệnh hỏng → coi như smoke đỏ → bước 6.
6. **Quay lui:** có bản trước → chạy `rollback_E`, `smoke_E`, `digest_E`; cả ba đạt và digest là của bản trước →
   `rolled_back`; ngược lại `rollback_failed`. Chưa có bản trước → `failed`. Cả ba ghi sổ và exit 1.

### 2.4 Sổ triển khai
- `docs/ops/DEPLOYS.json`, theo git, chỉ `xt.py deploy` ghi; guard chặn ghi tay (nhóm bằng chứng, như sổ giai đoạn);
  nằm trong tập loại trừ của vân tay `subject.content` để commit sổ không làm lệch ứng viên.
- `envs.<E>.current` luôn là **bản đang phục vụ theo lần xác nhận gần nhất**: `deployed` → ứng viên; `rolled_back` (kể
  cả do lệnh `deploy rollback`) → bản trước; `rollback_failed` hoặc `failed` khi đã chạm môi trường → `null` kèm
  `unknown: true` (không biết bản nào đang chạy). Mọi lần chạy đều vào `events`.
- Receipt là lời khai của lệnh `deploy` về **một digest**; `runner` ghi nơi chạy. Bằng chứng mạnh nhất cho bản dev là
  job CI của gói chạy `deploy run` rồi `release-check` trong cùng một job. Nhập receipt từ nơi khác không có ở phiên bản
  này (§10).

### 2.5 Nơi đọc sổ
- `release-check`: hàng `deploy` — BLOCKER khi `deploy_envs` có giá trị. PASS khi `envs.dev.current` là bản `deployed`
  có `subject.digest`, `subject.content` trùng ứng viên đang kiểm; ngược lại FAIL kèm lệnh cần chạy.
- `deploy_envs` trống: **không có hàng ở mọi quy mô** — dự án đang chạy nâng khung không đổi `verdict`. Agent ký ở M/L và
  duyệt giai đoạn 2/3 thì đòi hàng này PASS (SPEC-factory-scale §2.2, §2.3): thiếu hàng chỉ chặn phần nới, không chặn
  đường người ký.
- `xt.py registry pull --from <thư mục chứa clone>` (repo khung): đọc sổ của từng sản phẩm, cập nhật `environments` (các
  môi trường có `current`). Với sản phẩm registry **đã có** `release` (có `version`): cập nhật `release.digest` và
  `release.date` theo `prod.current`. `release` đang `null` → để nguyên và báo "có bản production nhưng registry chưa có
  `release.version`" (schema registry không đổi; `version` vẫn do người hoặc bước cắt bản ghi).

### 2.6 Bản dev của gói `web-api-ts` (F-102)
- Gói thêm (thư mục `managed/`): Dockerfile, file compose cho `dev` (app + Postgres), script tương ứng các khoá;
  `pack.json` khai `deploy_envs: dev`, `deploy_dev`, `smoke_dev`, `digest_dev`, `rollback_dev`, `url_dev`.
- Ảnh dựng **từ artifact đã kiểm** (`dist/app.tgz`), gắn thẻ theo `XT_DEPLOY_DIGEST`; chạy bằng user không phải root; có
  healthcheck. App trả digest của bản mình ở điểm kiểm sức khoẻ; `digest_dev` đọc từ đó. Bản trước giữ ở
  `XT_DEPLOY_STATE` để quay lui không cần mạng.
- `smoke_dev` tự gọi HTTP: sức khoẻ, đăng nhập, tạo ghi chú, người thuê khác bị từ chối — không dựa vào exit code của
  `up --wait` (chưa xác minh từ nguồn chính thức).
- Lệnh chạy được với Docker 28 / Compose 2.38 (bản trên runner `ubuntu-latest`) và bản ổn định hiện hành.
- Workflow của gói: repo sạch → build → `deploy run --env dev` → `release-check` thấy hàng `deploy` PASS; các ca sai cố
  ý đều đỏ: artifact bị đổi sau khi tính digest, smoke đỏ (phải ra `rolled_back` và bản trước còn phục vụ), bản đang
  phục vụ báo digest khác, quay lui hỏng.
- Bản dev là môi trường dựng lại được bằng một lệnh, **không phải địa chỉ luôn bật**: trước khi chủ dự án thiết lập đích
  triển khai thì không có máy chủ nào để giữ nó chạy. Runner `ubuntu-latest` chạy được (Docker cài sẵn). Trong phiên
  cloud: có sẵn `dockerd` nhưng daemon phải tự khởi động và việc người dùng xem được cổng từ ngoài **chưa xác minh** —
  T-3844 thử trước khi skill dựa vào.

### 2.7 Production (F-103)
- Môi trường khác `dev` chỉ chạy được sau thiết lập một lần (SPEC-factory-setup): dòng `- grant: deploy | env=prod` ở
  PLAN do chủ dự án merge, lệnh và khoá của đích do dự án khai.
- Điều kiện ở §2.3 bước 2 thay cho "người duyệt khác người kích" của `WF-ENV-008` khi dự án chọn tự động (lớp A,
  SPEC-factory-scale §2.4).
- Smoke đỏ trên production → quay lui tự động; `rollback_failed` → `loop block` (bế tắc thật, cần người).

## 3. Tiêu chí chấp nhận

### S-101 Bản dev lên được
- Given `deploy_envs: dev`, các khoá `*_dev` exit 0, `digest_dev` in đúng digest ứng viên, một artifact hợp lệ, sổ chưa có
- When `xt.py deploy run --env dev --json`
- Then exit 0; sổ có `envs.dev.current.result` = `deployed`, `subject.digest` = digest ứng viên, các `exit_code` = 0

### S-102 Smoke đỏ, có bản trước
- Given `dev.current` là bản A; ứng viên B có `smoke_dev` exit 1 lần đầu, exit 0 sau quay lui; `digest_dev` sau quay lui in digest A
- When `deploy run --env dev` · Then exit 1; sự kiện `rolled_back`; `dev.current` là A

### S-103 Quay lui hỏng
- Given như S-102 nhưng `rollback_dev` exit 1 · When `deploy run` · Then exit 1, sự kiện `rollback_failed`, `dev.current` = `null` với `unknown: true`

### S-104 Lần đầu mà hỏng
- Given sổ trống, `deploy_dev` exit 1 · When `deploy run` · Then exit 1, sự kiện `failed`, không chạy `rollback_dev`

### S-105 Artifact bị đổi
- Given sidecar `.sha256` không khớp file · When `deploy run` · Then exit 2, không lệnh nào chạy, sổ không đổi

### S-106 Cổng rỗng
- Given `smoke_dev` hoặc `digest_dev` trống, hoặc là lệnh no-op (`true`, `:`) · When `deploy run` · Then exit 2 "cổng rỗng"

### S-107 Guard cấm lệnh
- Given `deploy_dev` chứa lệnh nhóm máy chặn · When `deploy run` · Then exit 126 trước khi chạy gì

### S-108 Production thiếu điều kiện (Scenario Outline)
- Given môi trường `prod`, thiếu `<điều kiện>` · When `deploy run --env prod` · Then exit 2 nêu `<điều kiện>`
- Examples: `grant` · `promotion` chưa `approved` · `dev.current` khác digest · cây bẩn · HEAD chưa nằm trong nhánh chính của remote

### S-109 Production đủ điều kiện
- Given đủ các điều kiện, mọi lệnh exit 0, `digest_prod` in đúng digest · When `deploy run --env prod` · Then exit 0, `envs.prod.current` = ứng viên

### S-110 Hàng `deploy` của release-check
- Given `dev.current` có digest D và content C
- When `release-check --json` với ứng viên (D, C) · Then hàng `deploy` PASS
- And When sửa một file mã rồi chạy lại · Then hàng `deploy` FAIL "bản dev chưa chạy ứng viên này"

### S-111 Commit sổ không làm lệch ứng viên
- Given S-101 xong · When commit `DEPLOYS.json` rồi `release-check --json` · Then `subject.content` không đổi, hàng `deploy` PASS

### S-112 Ghi tay sổ
- Given phiên agent · When Write/Edit/Bash ghi `docs/ops/DEPLOYS.json` · Then guard chặn

### S-113 Registry kéo về
- Given clone một sản phẩm có `envs.prod.current` digest D, ngày N; registry của sản phẩm đã có `release` với `version`
- When `xt.py registry pull --from <thư mục>` · Then `environments` chứa `prod`, `release.digest` = D, `release.date` = N; `xt.py registry` vẫn exit như trước
- And Given `release` là `null` · Then `release` vẫn `null`, lệnh in cảnh báo thiếu `release.version`

### S-114 Gói: lát dọc bản dev trên repo sạch
- Given repo sạch cài gói, runner có Docker · When workflow gói chạy
- Then bản dev `deployed`, `smoke_dev` qua đủ bốn kiểm, `release-check` hàng `deploy` PASS; các ca sai cố ý đỏ đúng lý do

### S-115 Bản đang phục vụ không phải ứng viên
- Given `deploy_dev` và `smoke_dev` exit 0 nhưng `digest_dev` in digest khác · When `deploy run`
- Then xử lý như smoke đỏ (quay lui nếu có bản trước); không ghi `deployed`

### S-116 Sau quay lui, hàng `deploy` không còn PASS cho bản đã bỏ
- Given `deploy run` B thành công, rồi `deploy rollback --env dev` về A thành công
- When `release-check` với ứng viên B · Then hàng `deploy` FAIL (`dev.current` là A)

### S-117 Quay lui production cũng cần quyền
- Given không có `grant` cho `prod` · When `xt.py deploy rollback --env prod` · Then exit 2, không lệnh nào chạy
- And Given `rollback_prod` chứa lệnh nhóm máy chặn · Then exit 126

### S-118 Dự án chưa khai môi trường
- Given dự án M đang `GO`, `deploy_envs` trống · When nâng khung rồi `release-check --json` · Then không có hàng `deploy`; `verdict` và `promotion` như trước khi nâng

## 4. Ca biên
| Nhóm | Ca | Hành vi | Scenario |
|---|---|---|---|
| Rỗng/null | `deploy_envs` trống | Lệnh `deploy` exit 2 "chưa khai môi trường"; không hàng `deploy` ở mọi quy mô | S-118 |
| Rỗng/null | Không khai `release_artifacts` | exit 2 — không triển khai thứ không có digest | S-105 |
| Cực đại | Lệnh vượt `XT_DEPLOY_TIMEOUT` | Coi như exit ≠ 0 → quay lui | S-102 |
| Cực đại | `events` dài | Giữ 50 sự kiện mới nhất; `current`/`previous` không bao giờ bị cắt | — |
| Trùng lặp | Chạy lại với cùng digest đang `current` | Vẫn chạy (lệnh của dự án phải lũy đẳng); receipt mới thay `current`, `previous` giữ nguyên | S-101 |
| Song song | Hai `deploy run` cùng môi trường | Khoá file trạng thái (ADR-0054); lệnh thứ hai exit 2 | — |
| Mất mạng | Lệnh hỏng giữa chừng; không đọc được nhánh chính của remote | exit ≠ 0 → quay lui; không đọc được remote → production exit 2 | S-102, S-108 |
| Thời gian | `started`/`finished` | UTC ISO 8601 | S-101 |
| Quyền | Tên môi trường lạ (`../x`, hoa, > 16 ký tự) | exit 2 | — |
| Quyền | Agent tự thêm `- grant: deploy` | Dòng `- grant:` chỉ đổi qua PR người merge (ADR-0022) | S-108 |
| Quyền | Mã chưa merge nhưng đã ký trên nhánh | Không lên production | S-108 |
| Tiền/đơn vị | Triển khai lên dịch vụ trả phí | Ngoài `dev`: chỉ khi có `grant`; không có → `loop defer` | S-108 |

## 5. Dữ liệu
`DEPLOYS.json`: `{"schema": 1, "envs": {"<E>": {"current": R|null, "previous": R|null, "unknown": bool}}, "events": [R…]}`.
`R` = `{"env", "result": "deployed"|"rolled_back"|"rollback_failed"|"failed", "subject": {"head", "content", "digest"},
"artifacts": [{"path", "sha256"}], "started", "finished", "deploy": {"cmd_sha256", "exit_code"}, "smoke": {…}|null,
"served_digest", "rollback": {…}|null, "previous_digest", "url", "runner": {"kind": "local"|"ci", "run_id", "run_url"},
"session"}`. Không ghi biến môi trường, đầu ra lệnh hay bí mật vào sổ.

## 6. Lỗi
| Khi nào | Exit | Thông điệp |
|---|---|---|
| Thiếu khoá, tên môi trường sai, artifact lệch, cổng rỗng, thiếu điều kiện production, sổ hỏng, chạy trong worktree song song | 2 | một dòng, nêu khoá/điều kiện |
| Triển khai, smoke hoặc đối chiếu digest hỏng | 1 | kết quả (`rolled_back`/`rollback_failed`/`failed`) và lệnh hỏng |
| Guard cấm | 126 | mã luật của guard |

## 7. Phi chức năng
`deploy status` ≤ 300 ms. Mã trong `scripts/xt.py`, chỉ stdlib. Đầu ra lệnh của dự án đi thẳng ra terminal, không lưu.

## 8. Hành vi AI
Agent không tự viết receipt, không tự nâng `promotion`. `rollback_failed` trên production là bế tắc thật: `loop block`,
không thử cách khác cho cùng hiệu ứng.

## 9. Đo lường
`deploy status --json` cho: số lần triển khai, tỉ lệ `rolled_back`, thời gian `started` → `finished` theo môi trường.

## 10. Câu hỏi mở
- [x] Receipt ở đâu? — D-422: sổ theo git (kéo về được theo ADR-0010, bền qua container), không dựa vào dịch vụ ngoài.
- [x] `release-check` tự chạy triển khai hay chỉ đọc sổ? — D-422: chỉ đọc; triển khai là một bước riêng có hiệu ứng.
- [x] Công cụ container của gói? — D-422: Docker Engine + Compose (Apache-2.0, có sẵn trên runner); hợp đồng của khung
  vẫn trung lập.
- [x] Làm sao biết bản đang chạy đúng là ứng viên? — D-423: khoá `digest_<env>` bắt buộc; `current` là bản đang phục vụ.
- [x] Thiếu `deploy_envs` ở M/L? — D-423: không thêm hàng (không buộc dự án đang chạy); chỉ phần nới mới đòi hàng PASS.
- [x] Mã chưa merge có lên production được không? — D-423: không; HEAD phải nằm trong nhánh chính của remote.
- [ ] Nhập receipt do CI ghi vào phiên (`deploy import --run`) — [không chặn] — chưa làm; cần kiểm run, SHA và workflow.
- [ ] Ghi thêm GitHub Deployment, attestation cho artifact, triển khai canary — [không chặn] — sau pilot 2.

## 11. DoR / DoD
- DoR: spec này Approved; T-3841 có ADR; `release_artifacts`/`subject` đã ở `main`.
- DoD: S-101…S-118 có test xanh; ca guard S-107, S-112, S-117 vào `autonomy-bench`; mẫu `xt.yaml`, `harness-files.md`,
  README gói, CHANGELOG cập nhật; hàng mới không đổi nghĩa `go`/`verdict`/exit code của `release-check` với dự án chưa
  khai `deploy_envs`.

## Thay đổi
| Phiên bản | Ngày | Gì | Duyệt |
|---|---|---|---|
| 1 | 2026-11-11 | tạo; sửa trước khi công bố theo review độc lập: `digest_<env>` và nghĩa của `current`, quyền cho `rollback`, HEAD phải ở nhánh chính, không thêm hàng khi chưa khai môi trường, `registry pull` giữ schema | D-422, D-423 |
