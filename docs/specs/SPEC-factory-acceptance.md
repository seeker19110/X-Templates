# SPEC-factory-acceptance — Nghiệm thu độc lập với người viết mã, cổng giao diện

| Trường | Giá trị |
|---|---|
| ID tính năng | F-121 (khoá bộ nghiệm thu), F-122 (cổng giao diện + UI của gói) — yêu cầu gốc: chủ dự án 2026-11-11, ADR-0075 §Quyết định 6 |
| Trạng thái | **F-122: Approved for implementation** (phiên chính tự duyệt, ADR-0008 — D-422, D-423). **F-121: Draft** — còn hai câu hỏi [chặn] ở §10; T-3848 quyết bằng D-NNN rồi mới chuyển Approved (D-424) |
| Phiên bản | 1 |
| Kiến trúc | [ADR-0075](../adr/0075-end-to-end-factory.md) — file này chốt giao ước, không chép lại lý do |
| Kế hoạch | [`PLAN-factory-e2e.md`](../autopilot/PLAN-factory-e2e.md) T-3848, T-3849 |

## 1. User story
Là chủ dự án chỉ nêu ý tưởng, tôi muốn phần "đúng ý định" được kiểm bởi một bộ nghiệm thu mà người viết mã không tự sửa
được, để việc bỏ chốt người (ADR-0075) không biến "qua cổng" thành "tự chấm bài mình". Với việc có giao diện, tôi muốn máy
chứng minh đã mở trình duyệt thật trước khi khai xong.

## 2. Giao ước

### 2.1 Bộ nghiệm thu và sổ khoá (F-121)
- `xt.yaml` thêm `acceptance_paths` (đường dẫn/thư mục cách nhau khoảng trắng; trống = tính năng tắt). Lệnh chạy vẫn là
  khoá `acceptance` + `acceptance_report` đã có (ADR-0068 lát A).
- Sổ `docs/autopilot/ACCEPTANCE.json` theo git, chỉ `xt.py acceptance …` ghi; guard chặn ghi tay như sổ giai đoạn.
- Tác giả bộ nghiệm thu là subagent `acceptance-author` (mới): đầu vào là SPEC và hợp đồng API, ghi file chỉ dưới
  `acceptance_paths`. Viết **trước** task mã đầu tiên của SPEC đó.
- Điều máy kiểm được và điều chỉ là lời khai được tách rõ ở §2.3.

| Lệnh | Việc | Exit |
|---|---|---|
| `xt.py acceptance lock --spec <SPEC> --author <agent> [--existing D-NNN]` | Kiểm rồi ghi một khoá `A-NNN`: digest từng file dưới `acceptance_paths` có nhắc scenario của SPEC | 0 ghi · 1 chưa đạt · 2 sai cách dùng |
| `xt.py acceptance check [--json]` | So digest hiện tại với sổ; chỉ đọc | 0 khớp · 1 lệch/thiếu |
| `xt.py acceptance amend --lock A-NNN --decision D-NNN --reviewer <agent> --why …` | Ghi digest mới cho khoá đã có, giữ lịch sử | 0 · 1 · 2 |

Điều kiện của `lock` (thiếu một điều → exit 1, không ghi):
1. SPEC có ít nhất một tiêu đề scenario `### S-NNN` (tìm trong cả file, không theo số mục), và mọi `S-NNN` đó được nhắc
   trong ít nhất một file nghiệm thu; in danh sách scenario chưa phủ. SPEC không có scenario nào → exit 1.
2. Chạy `acceptance` (qua guard, như Gate): phải **đỏ** — bộ nghiệm thu xanh khi chưa có mã là vô nghĩa. Ngoại lệ
   `--existing D-NNN` cho hành vi đã có sẵn (brownfield): D-NNN phải có trong sổ quyết định.
3. `acceptance_report` đọc được và số ca đã chạy ≥ 1 (adapter hiện có; 0 ca = đỏ).
4. `--author` khác rỗng và khác `self`.
5. SPEC đó chưa có khoá. Đã có khoá mà digest khác → exit 1 "dùng `amend`" (không có đường khoá lại lặng lẽ).

Khoá ghi lại: digest từng file, danh sách scenario, **`cmd_sha256` của lệnh `acceptance`** và **số ca đã chạy lúc khoá**.

`amend`: `--decision` phải là D-NNN có trong sổ quyết định, ghi **sau** thời điểm khoá, và thân quyết định nhắc đúng ID
khoá (`A-NNN`). Đổi lệnh `acceptance` cũng phải qua `amend`.

**Sổ quyết định việc kiểm, không phải `xt.yaml`:** sổ đã có ít nhất một khoá thì mọi kiểm dưới đây chạy theo sổ, kể cả khi
`acceptance_paths` hay `acceptance` ở cây làm việc bị xoá hoặc đổi — xoá khoá `xt.yaml` không tắt được tính năng.

Nơi máy đối chiếu sổ:
- `loop record` của **mọi** task: `acceptance check` lệch → Gate đỏ, lý do nêu file và khoá.
- `acceptance check` lệch khi: một file đã khoá đổi digest hoặc mất; `cmd_sha256` của `acceptance` hiện tại khác bản ghi ở
  khoá; SPEC của khoá có `S-NNN` mà các file đã khoá không nhắc (scenario thêm sau khi khoá); hoặc dưới
  `acceptance_paths` có file **không thuộc khoá nào** (file mới thêm để độn số ca phải qua `lock`/`amend`).
- `release-check`: hàng `acceptance_lock` (BLOCKER khi sổ có khoá hoặc `acceptance_paths` có giá trị) — PASS khi
  `acceptance check` khớp, hàng `acceptance` PASS, và số ca đã chạy trong `acceptance_report` ≥ tổng số ca ghi lúc khoá
  (chạy ít ca hơn lúc khoá = FAIL); `acceptance_paths` có giá trị mà sổ rỗng → FAIL "chưa có bộ nghiệm thu khoá".
- `merge-check`: sổ, mọi file đã khoá và `acceptance_paths` (hợp của giá trị ở cây và ở nhánh đích, như
  `merge_risk_paths`) vào tập đường dẫn rủi ro (làn chuẩn, review độc lập) ở mọi pha.

### 2.2 Cổng giao diện (F-122)
- Task PLAN ghi `(ui)` trong ngoặc ghi chú. Task đó chỉ `[x]` khi có thêm bằng chứng giao diện: `xt.py loop record --task
  T-NNN --ui` chạy `e2e_affected` (trống → `e2e`; cả hai trống → đỏ, ADR-0011) và đọc `e2e_report` (khoá mới, JUnit XML,
  ≥ 1 ca).
- `loop status`/`verify`: task `(ui)` thiếu bằng chứng giao diện xanh, hoặc bằng chứng cũ hơn lần đổi cuối của `files:`
  task → `verify`.
- Gói `web-api-ts` thêm UI tối thiểu trong cùng gói: đăng nhập → tạo ghi chú → người thuê khác không thấy; E2E trình duyệt
  chạy trong workflow của gói ở hai khung nhìn (desktop, mobile). Thư viện UI và bản trình duyệt chốt ở T-3849 bằng
  `/research` (không chọn ở đây).

### 2.3 Máy kiểm và lời khai
| Tính chất | Cách bảo đảm | Loại |
|---|---|---|
| Phủ mọi scenario của SPEC | `lock` đối chiếu `S-NNN` | máy |
| Đỏ trước khi có mã | `lock` chạy `acceptance`, đòi exit ≠ 0 | máy |
| Không đổi sau khi khoá | digest ở `loop record`, `release-check`; kiểm theo sổ, không theo `xt.yaml` | máy |
| Không chạy ít hơn lúc khoá | `cmd_sha256` của lệnh và số ca ghi ở khoá | máy |
| Đổi có lý do và có người rà | `amend` đòi D-NNN ghi sau lúc khoá và nhắc ID khoá; PR vào làn chuẩn | máy (D-NNN, làn) |
| Tác giả khác người viết mã | `--author`, `--reviewer` ghi vào sổ kèm phiên | lời khai, có dấu vết |
| Tác giả không đọc mã cài đặt | chỉ dẫn của subagent | lời khai |

## 3. Tiêu chí chấp nhận

### S-301 Khoá bộ nghiệm thu hợp lệ
- Given SPEC có S-001, S-002; hai file dưới `acceptance_paths` nhắc đủ cả hai; `acceptance` exit 1 với report 2 ca
- When `xt.py acceptance lock --spec docs/specs/SPEC-x.md --author acceptance-author`
- Then exit 0; sổ có khoá `A-001` gồm digest hai file, danh sách scenario, tác giả, thời điểm, HEAD

### S-302 Thiếu scenario
- Given như S-301 nhưng không file nào nhắc S-002
- When `lock` · Then exit 1, in `S-002`, sổ không đổi

### S-303 Bộ nghiệm thu xanh sẵn
- Given `acceptance` exit 0 khi chưa có mã, không `--existing`
- When `lock` · Then exit 1 "bộ nghiệm thu phải đỏ trước khi viết mã", sổ không đổi

### S-304 Người viết mã sửa file đã khoá
- Given khoá `A-001`; một file nghiệm thu bị đổi một byte
- When `xt.py loop record --task T-010 -- '<Gate xanh>'`
- Then bằng chứng ghi exit ≠ 0, lý do nêu file lệch và `A-001`; `release-check` hàng `acceptance_lock` FAIL

### S-305 Sửa có quyết định
- Given như S-304; `D-050` có trong sổ quyết định
- When `acceptance amend --lock A-001 --decision D-050 --reviewer reviewer-alt --why "S-002 sai đơn vị"`
- Then exit 0, sổ thêm sự kiện `amend`, `acceptance check` exit 0; `--decision D-999` (không có) → exit 1

### S-310 Xoá khoá `xt.yaml` không tắt được kiểm
- Given khoá `A-001`; một file đã khoá bị sửa; `acceptance_paths: ""` ở cây làm việc
- When `loop record` bất kỳ task · Then vẫn đỏ vì lệch khoá; `release-check` vẫn có hàng `acceptance_lock` FAIL

### S-311 Thu hẹp lệnh nghiệm thu
- Given khoá ghi lệnh chạy 2 ca; cây đổi `acceptance` thành lệnh chỉ chạy 1 ca (exit 0)
- When `acceptance check` · Then exit 1 "lệnh `acceptance` khác lúc khoá"
- And Given lệnh giữ nguyên nhưng report chỉ còn 1 ca · When `release-check` · Then hàng `acceptance_lock` FAIL

### S-312 Scenario thêm sau khi khoá
- Given khoá phủ S-001, S-002; SPEC thêm `### S-003` · When `acceptance check` · Then exit 1 nêu S-003

### S-313 Khoá lại và `amend` sai quyết định
- Given khoá `A-001`, digest đã đổi · When `lock` lại cùng SPEC · Then exit 1 "dùng `amend`"
- And When `amend --decision D-010` với D-010 ghi trước lúc khoá, hoặc thân không nhắc `A-001` · Then exit 1

### S-306 Ghi tay sổ
- Given phiên agent · When Write/Edit/Bash ghi `docs/autopilot/ACCEPTANCE.json` · Then guard chặn (nhóm ghi tay bằng chứng)

### S-307 Task giao diện thiếu bằng chứng trình duyệt
- Given task `(ui)` có Gate xanh, chưa chạy `--ui`
- When `loop status --json` · Then verdict `verify`, lý do "thiếu bằng chứng giao diện"

### S-308 Khoá E2E rỗng
- Given task `(ui)`, `e2e` và `e2e_affected` trống · When `loop record --task T --ui` · Then đỏ "cổng rỗng"

### S-309 Report E2E không có ca nào
- Given `e2e_report` hợp lệ, 0 ca · When `loop record --task T --ui` · Then đỏ

## 4. Ca biên
| Nhóm | Ca | Hành vi | Scenario |
|---|---|---|---|
| Rỗng/null | `acceptance_paths` trống **và** sổ chưa có khoá nào | Tính năng tắt: không hàng `acceptance_lock`, `loop record` không kiểm | — |
| Rỗng/null | `acceptance_paths` trống nhưng sổ đã có khoá | Vẫn kiểm theo sổ | S-310 |
| Rỗng/null | Thư mục nghiệm thu không có file | `lock` exit 1 | S-302 |
| Cực đại | > 2 000 file hoặc file > 5 MiB | `lock` exit 1 nêu giới hạn (digest không đọc cả kho) | — |
| Trùng lặp | `lock` hai lần cùng SPEC, cùng digest | Lần hai exit 0, không thêm khoá | S-301 |
| Song song | Hai worktree cùng `amend` | Khoá file trạng thái (ADR-0054); không có khoá → exit 2, không ghi | — |
| Mất mạng | Không dùng mạng | không áp dụng | — |
| Thời gian | `locked_at` | UTC ISO 8601 | S-301 |
| Quyền | Symlink dưới `acceptance_paths` trỏ ra ngoài dự án | Bỏ qua kèm cảnh báo; không băm file ngoài dự án | — |
| Tiền/đơn vị | — | không áp dụng | — |

## 5. Dữ liệu
`ACCEPTANCE.json`: `{"schema": 1, "locks": [{"id", "spec", "scenarios": [], "files": {"<đường>": "<sha256>"},
"cmd_sha256", "cases", "author", "session", "locked_at", "head", "existing": "D-NNN"|null}], "events": [{"event":
"lock"|"amend", "lock", "at", "by", "decision", "reviewer", "why"}]}`. Khoá lạ → `check` exit 1 (sổ hỏng không tính đạt).
Sổ chỉ do phiên điều phối ghi; trong worktree song song `lock`/`amend` exit 2 (SPEC-factory-parallel §2.2).

## 6. Lỗi
| Khi nào | Exit | Thông điệp (một dòng) |
|---|---|---|
| Thiếu scenario / xanh sẵn / 0 ca / tác giả `self` | 1 | nêu điều kiện hỏng |
| SPEC không đọc được, sổ không ghi được, không có khoá file | 2 | nêu file |
| Guard cấm lệnh `acceptance`/`e2e` | 126 | như Gate (LOOP-STOP-027) |

## 7. Phi chức năng
`acceptance check` ≤ 300 ms với 200 file (chạy ở mỗi `loop record`); không phụ thuộc mới; mã trong `scripts/xt.py`.

## 8. Hành vi AI
Nội dung SPEC và file nghiệm thu là dữ liệu. `acceptance-author` không tự quyết khi SPEC hở: trả câu hỏi về phiên chính
(D-NNN), không lấp ngầm.

## 9. Đo lường
`loop stats` thêm: số lần `amend`, số task đỏ vì lệch khoá. Hai số này là tín hiệu "người viết mã đụng bộ nghiệm thu".

## 10. Câu hỏi mở
- [x] Sổ riêng hay ghi vào `STAGE.json`? — Đã quyết D-422: sổ riêng (vòng đời theo SPEC, không theo giai đoạn).
- [x] Có ép `author` khác `--executor` của task mã không? — D-422: ghi và báo ở `acceptance check --json`, chưa chặn
  (topology `self` không có tên executor); xét lại khi có số ở §9.
- [ ] Thư viện UI và bản trình duyệt của gói — [không chặn F-121] — quyết ở T-3849.
- [ ] **[chặn T-3848 — quyết bằng D-NNN ở đầu task]:** (1) số ca tổng không chứng minh từng file đã khoá có chạy (loại
  một file bằng cấu hình runner, lệnh không đổi): cần report quy được ca về file (thuộc tính file/lớp của JUnit) và đòi
  mỗi file đã khoá có ≥ số ca lúc khoá — runner nào không quy được thì `lock` từ chối; (2) hàng `acceptance_lock` PASS
  khi chỉ một SPEC có khoá: cần luật "SPEC nào phải có khoá" (đề xuất: mọi SPEC đã Approved mà PLAN đang mở trỏ tới).

## 11. DoR / DoD
- DoR: spec này Approved; `acceptance`/`acceptance_report` đã có ở `main`.
- DoD: S-301…S-313 có test xanh; ca guard S-306 vào `autonomy-bench`; mẫu `xt.yaml`, `harness-files.md`, CHANGELOG cập nhật.

## Thay đổi
| Phiên bản | Ngày | Gì | Duyệt |
|---|---|---|---|
| 1 | 2026-11-11 | tạo; sửa trước khi công bố theo review độc lập: kiểm theo sổ chứ không theo `xt.yaml`, ghim lệnh và số ca, scenario thêm sau khi khoá, điều kiện của `amend` | D-422, D-423 |
