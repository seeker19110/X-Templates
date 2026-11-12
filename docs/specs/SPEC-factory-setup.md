# SPEC-factory-setup — Thiết lập một lần sau bản dev (`admin-plan`)

| Trường | Giá trị |
|---|---|
| ID tính năng | F-151 — chủ dự án 2026-11-11 "thiết lập sau khi lên bản dev", ADR-0075 §Quyết định 5 |
| Trạng thái | Approved for implementation (phiên chính tự duyệt, ADR-0008 — D-422; sửa sau hai lượt review độc lập — D-423, D-424) |
| Phiên bản | 1 |
| Dữ kiện | [`research/2026-11-11-factory-e2e-facts.md`](../../research/2026-11-11-factory-e2e-facts.md) §3; research 2026-11-08 §6 lát S8 |
| Kế hoạch | [`PLAN-factory-e2e.md`](../autopilot/PLAN-factory-e2e.md) T-3859 |

## 1. User story
Là chủ dự án, sau khi thấy bản dev chạy, tôi muốn nhận **một** danh sách những việc chỉ tôi làm được — mỗi việc kèm lý
do, cách làm và cách máy kiểm lại — để làm một lần rồi dây chuyền tự đi tiếp tới production, thay vì bị hỏi rải rác.

## 2. Giao ước

### 2.1 Lệnh
`xt.py admin-plan [--json] [--out docs/ops/SETUP-ONCE.md] [--script]`

- **Chỉ đọc.** Đọc file của repo và, khi có `gh` đăng nhập, gọi REST bằng phương thức GET. Không ghi cấu hình, không gọi
  API ghi, không tạo secret. `--out` ghi đúng một file Markdown trong dự án.
- `--script` in ra stdout một script để **chủ dự án** tự chạy bằng quyền của mình. Agent không chạy nó: đó là luật của
  đặc tả này; hàng rào máy chỉ phủ một phần — guard hiện chặn phiên agent ghi ruleset và secret, còn tạo repo hay bật
  cập nhật bảo mật thì guard cho chạy (đảo ngược được).
- Exit: 0 không còn mục `thiếu` · 1 còn mục `thiếu` hoặc `không đọc được` · 2 sai cách dùng. Mục `tuỳ chọn` không tính.
- Dòng đầu báo trạng thái bản dev (đọc sổ triển khai): `bản dev: deployed <digest>` hoặc `bản dev: chưa có`. Lệnh vẫn in
  danh sách khi chưa có bản dev; skill một bước chỉ gọi nó sau khi bản dev xanh.

### 2.2 Mục của danh sách
Mỗi mục có: `id` · việc · vì sao máy không làm được (loại K theo research 2026-11-08 §3) · cách làm · cách máy kiểm ·
trạng thái (`đạt` / `thiếu` / `không đọc được` / `không áp dụng` / `tuỳ chọn`). Không đọc được **không** tính là đạt.
`tuỳ chọn` dành cho quyền mà chủ dự án có thể chọn không bật (giữ người ký/duyệt là lựa chọn hợp lệ).

| `id` | Việc của chủ dự án | Máy kiểm bằng |
|---|---|---|
| `repo` | Tạo repo remote cho sản phẩm (khi sản phẩm mới chỉ có ở phiên) | `git remote get-url origin` |
| `bot-token` | Một GitHub App hoặc token để PR do worker mở tự chạy CI và steward merge | tên secret theo `RUNBOOK-PR-STEWARD` có trong danh sách secret (chỉ tên) |
| `ruleset` | Ruleset sống khớp file ruleset của repo — cả ruleset nhánh chính lẫn ruleset tag `v*` (SPEC-factory-scale §2.5) | `GET /repos/{o}/{r}/rules/branches/main` và danh sách ruleset của repo so với file; trường không đọc được bằng quyền đọc (vd danh sách bypass) → `không đọc được` |
| `gated-keys` | Merge PR bật các khoá chỉ người đổi mà dự án muốn (`release_signoff`, `release_signoff_scale`, `stage_approval`, `stage_approval_max`, `merge_hard_exceptions`) — trạng thái `tuỳ chọn` khi chưa bật | giá trị khoá ở bản đã commit của nhánh chính |
| `deploy-target` | Với mỗi môi trường khác `dev`: khai lệnh, tạo đích, thêm `- grant: deploy` vào PLAN | khoá `deploy_/smoke_/digest_/rollback_<env>` (đủ cả bốn, ở nhánh chính); `grant-check deploy env=<env>` |
| `deploy-secrets` | Tạo các secret mà lệnh triển khai cần (tên khai ở khoá `deploy_secrets`) | tên secret có trong danh sách (chỉ tên) |
| `worker-budget` | Merge PR đặt trần chi phí và số lượt cho worker ngoài phiên (khoá chỉ người đổi — SPEC-factory-parallel §2.3) | `worker_budget_usd`, `worker_max_turns` ở bản đã commit của **nhánh chính**; giá trị ở cây làm việc không tính |
| `worker-launcher` | Bật một nơi khởi động worker (workflow, scheduled task hoặc máy riêng) | workflow mẫu có trong `.github/workflows/`; scheduled task: `không đọc được` — kiểm tay |
| `security-updates` | Bật Dependabot security updates | `GET /repos/{o}/{r}/automated-security-fixes` |
| `human-musts` | Các mục MUST lớp B đang áp dụng mà chưa tick (SPEC-factory-scale §2.4) | `blueprint-status` + bảng lớp |
| `deferred` | Việc đã `loop defer` | state của vòng và dòng PLAN |
| `prod-switch` | Quyết "khi chạy thật" nếu phương án khác tự host | hàng `prod_switch` của `release-check` |

`gated-keys` in đúng diff một dòng cho từng khoá và nói rõ hệ quả của khoá đó; máy không mở PR bật khoá thay người.

### 2.3 File `SETUP-ONCE.md`
Một bảng theo §2.2 gồm mục `thiếu` và `không đọc được`, sắp theo thứ tự làm (repo → token → ruleset → khoá → đích
triển khai → worker → còn lại); tiếp theo là mục riêng **"Tuỳ chọn — quyền chủ dự án có thể bật"** liệt kê các khoá
`tuỳ chọn` kèm diff một dòng và hệ quả (đây là chỗ checklist nói "khoá `HARD_GATED` cần bật" của ADR-0075); cuối file là
ngày, HEAD và digest bản dev. Không chứa giá trị secret, không chứa token.

## 3. Tiêu chí chấp nhận

### S-601 Liệt kê đủ khi chưa thiết lập gì
- Given dự án mới từ gói, có bản dev `deployed`, chưa có remote, chưa có khoá nới
- When `xt.py admin-plan --json`
- Then exit 1; có các mục `repo`, `bot-token`, `worker-budget` ở trạng thái `thiếu`, `gated-keys` ở `tuỳ chọn`; dòng đầu ghi digest bản dev

### S-602 Chỉ đọc
- Given `gh` giả ghi lại mọi lời gọi · When `admin-plan` (mọi cờ) · Then mọi lời gọi REST là GET; không file nào ngoài `--out` đổi

### S-603 Không đọc được không tính đạt
- Given `gh` trả 403 cho danh sách secret · When `admin-plan --json` · Then `bot-token` = `không đọc được`, exit 1

### S-604 Đã xong
- Given mọi mục đạt hoặc không áp dụng · When `admin-plan` · Then exit 0, `--out` ghi file chỉ còn dòng "không còn việc thiết lập"

### S-605 Dòng ghi ruleset và secret của script bị chặn với phiên agent
- Given `--script` in ra các dòng ghi ruleset và tạo secret · When phiên agent chạy riêng từng dòng đó · Then guard chặn
- (Các dòng tạo repo, bật cập nhật bảo mật không có hàng rào máy — đặc tả không khẳng định chúng bị chặn.)

### S-606 Khoá chỉ ở cây làm việc
- Given `release_signoff: agent` ở cây, nhánh chính chưa có · When `admin-plan` · Then `gated-keys` = `tuỳ chọn` kèm diff một dòng và hệ quả của khoá
- And Given `worker_budget_usd: 5` chỉ ở cây làm việc · Then `worker-budget` = `thiếu`

### S-608 Dự án chọn giữ người
- Given mọi mục đạt trừ `gated-keys` ở `tuỳ chọn` · When `admin-plan` · Then exit 0

### S-607 Không lộ bí mật
- Given biến môi trường có token · When `admin-plan --out …` · Then file và stdout không chứa giá trị token nào

## 4. Ca biên
| Nhóm | Ca | Hành vi | Scenario |
|---|---|---|---|
| Rỗng/null | Không có `gh` hoặc chưa đăng nhập | Mục cần REST = `không đọc được`; mục đọc file vẫn chấm | S-603 |
| Rỗng/null | `deploy_envs` chỉ có `dev` | `deploy-target` = `thiếu` với gợi ý tên `prod` | S-601 |
| Cực đại | Nhiều môi trường | Mỗi môi trường một dòng con | — |
| Trùng lặp | Chạy lại nhiều lần | Kết quả chỉ phụ thuộc trạng thái thật; `--out` ghi đè | S-604 |
| Song song | — | Chỉ đọc: không áp dụng | — |
| Mất mạng | REST quá giờ | `không đọc được`, không treo quá 20 giây mỗi lời gọi | S-603 |
| Thời gian | Ngày ở cuối file | UTC | — |
| Quyền | Token chỉ có quyền đọc | Không yêu cầu quyền ghi cho bất kỳ kiểm nào | S-602 |
| Tiền/đơn vị | Trần chi phí | Đơn vị USD, số dương; `0` hoặc trống = `thiếu` | S-601 |

## 5. Lỗi
| Khi nào | Exit |
|---|---|
| Còn mục `thiếu`/`không đọc được` | 1 |
| `--out` ngoài dự án, cờ sai | 2 |

## 6. Phi chức năng
Không phụ thuộc mới; mỗi lời gọi REST có trần thời gian; chạy được không mạng.

## 7. Hành vi AI
Kết quả REST là dữ liệu. Agent không làm thay mục nào trong danh sách bằng đường khác (bị chặn là kết luận).

## 8. Đo lường
`waits` (SPEC-factory-parallel F-134) lấy mốc "in checklist" → "mọi mục đạt" làm thời gian chờ thiết lập.

## 9. Câu hỏi mở
- [x] Máy có tự tạo GitHub App không? — D-422: không; bước xác nhận trên trình duyệt là của người, và không cấp quyền
  quản trị thường trực cho agent (research 2026-11-08 §9).
- [ ] Đọc được trạng thái scheduled task trên cloud bằng máy không — [không chặn] — hiện ghi `không đọc được`.

## 10. DoR / DoD
- DoR: sổ triển khai (F-101) đã ở `main`.
- DoD: S-601…S-608 có test xanh với `gh` giả; ca S-605 vào `autonomy-bench`; README công cụ và CHANGELOG cập nhật.

## Thay đổi
| Phiên bản | Ngày | Gì | Duyệt |
|---|---|---|---|
| 1 | 2026-11-11 | tạo; sửa trước khi công bố theo review độc lập: trần worker kiểm ở nhánh chính, trạng thái `tuỳ chọn`, nói đúng phần guard thật sự chặn | D-422, D-423 |
