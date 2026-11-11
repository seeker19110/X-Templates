# SPEC-factory-parallel — Song song theo file, worker ngoài phiên, số đo

| Trường | Giá trị |
|---|---|
| ID tính năng | F-131 (phạm vi file do máy kiểm + song song mặc định), F-132 (file mọi PR cùng chạm), F-133 (worker ngoài phiên + hàng đợi), F-134 (số đo) — chủ dự án 2026-11-11 "song song nếu không chạm cùng file", ADR-0075 §Quyết định 3 |
| Trạng thái | Approved for implementation (phiên chính tự duyệt, ADR-0008 — D-422; sửa sau review độc lập — D-423) |
| Phiên bản | 1 — ADR của T-3850 ghi quyết định kiến trúc (thay một phần D-142) và liên kết về đây, không chép lại |
| Dữ kiện | [`research/2026-11-11-factory-e2e-facts.md`](../../research/2026-11-11-factory-e2e-facts.md) §2, §3 |
| Kế hoạch | [`PLAN-factory-e2e.md`](../autopilot/PLAN-factory-e2e.md) T-3850…T-3854 |

## 1. User story
Là chủ dự án muốn nhanh, tôi muốn các lát việc không đụng cùng file được làm cùng lúc, mỗi lát một nhánh và một PR, kể
cả khi tôi không mở phiên nào — với điều kiện "không đụng cùng file" là thứ máy kiểm trên diff thật chứ không phải lời
khai của người lập kế hoạch, và có số đo để biết song song có thật sự nhanh hơn mà không lọt thêm lỗi.

## 2. Giao ước

### 2.1 Đơn vị song song và phạm vi file (F-131)
- **Đơn vị song song là một worktree được giao một tập task**: một task (subagent trong phiên) hoặc cả một lát (worker).
  Lúc tạo worktree, máy ghi vào state tập task được giao (`assigned`) và điểm rẽ nhánh.
- **Phạm vi của worktree** = hợp `files:` của mọi task trong `assigned` + phần được phép ở §2.2. Mỗi `loop record` trong
  worktree so tập file đổi kể từ điểm rẽ nhánh (`git diff --name-only <điểm rẽ>` + file chưa track; đổi tên tính cả
  đường cũ và mới) với phạm vi đó. Có file ngoài → bằng chứng ghi exit ≠ 0, lý do liệt kê file.
- Hai worktree chạy cùng lúc được khi mọi task được giao đều khai `files:` và hai hợp `files:` không giao (thư mục chứa
  nhau tính là giao). Task thiếu `files:` không bao giờ vào đơn vị song song.
- Task chạy tuần tự trong cây chính: cùng phép so, nhưng chỉ ghi `scope_outside` vào bằng chứng (cảnh báo) — không gán
  chắc được file cho task khi nhiều task nối nhau trong một cây.
- `loop status --json`: khi có ≥ 2 task sẵn sàng (`sau:` đã thoả) có `files:` đôi một không giao (đúng phép so của `plan
  waves`), trả `topology: "parallel"` và `wave: [ID…]`, tối đa `worker_max_parallel` (mặc định 4; giá trị > 5 bị từ chối
  như `plan waves --max` hiện nay). Task ghi `(topo: self)` hoặc `(topo: audit)` đứng riêng; `(topo: review)` vào đợt
  được, vẫn cần reviewer trước PR.
- Khoá lùi `xt.yaml`: `parallel: off` → hành vi trước ADR-0075. Vắng = bật.
- **State dùng chung:** bằng chứng từng task nằm ở `.autopilot/` của worktree chính (xác định qua `git rev-parse
  --git-common-dir`), ghi dưới khoá file, kèm `worktree` và `branch`. Kết quả "kiểm lại cuối" và bộ đếm lỗi lặp giữ
  **riêng theo worktree** (khoá theo đường worktree) — worktree này chạy `loop verify --all` không làm worktree khác
  thành "chưa kiểm".

### 2.2 File nhiều PR cùng chạm (F-132)
| File | Trong worktree song song | Cổng |
|---|---|---|
| `CHANGELOG.md` | Không sửa. Mỗi PR thêm một **mảnh** `changelog.d/<tên nhánh hoặc ID task>.md`; phiên điều phối gộp lúc cắt bản bằng `xt.py changelog compile` (xoá mảnh) | `changelog-check` chấp nhận mảnh thay cho dòng trong `[Unreleased]`; trùng tên mảnh → đỏ |
| File PLAN | Chỉ được đổi dấu `[ ]` → `[x]` trên dòng của task trong `assigned`. Mọi thay đổi khác ở PLAN → đỏ | `loop record` so diff PLAN theo dòng |
| `PROGRESS.md`, sổ quyết định, sổ audit, dấu tick blueprint | Không sửa. Phiên điều phối ghi trong **một PR sổ sách sau mỗi đợt** | `loop record` đỏ nếu worktree song song chạm |
| Sổ theo git do lệnh ghi (`STAGE.json`, sổ nghiệm thu, sổ triển khai) | Không ghi. `stage …`, `acceptance lock/amend`, `deploy run` là bước tích hợp của phiên điều phối, chạy sau khi các PR của đợt đã merge; trong worktree song song các lệnh ghi này exit 2 | chính lệnh từ chối |

Dòng task của các lát khác nhau cách nhau bởi tiêu đề `### Lát`, nên hai PR tick hai lát khác nhau gộp được không xung
đột. Subagent và worker lát không tự quyết (luật sẵn có) nên không ghi sổ quyết định; số D-NNN chỉ cấp ở phiên điều phối.

### 2.3 Worker ngoài phiên và hàng đợi (F-133)
Hai vai, không lẫn:

| Vai | Làm gì | Được quyết định (D-NNN)? |
|---|---|---|
| **Worker lát** | Làm các task của một lát đã có trong PLAN, trong một worktree, ra một PR | Không — gặp điểm quyết định thì `loop defer` |
| **Phiên điều phối headless** | Vai phiên chính nhưng không có người mở: lập/duyệt PLAN, giao lát, tích hợp, ghi sổ (dùng cho kênh ý tưởng — SPEC-factory-intake) | Có, theo ADR-0008 |

Worker lát:
- `xt.py loop run --agent <A> --worktree --slice "<tên mục ### của PLAN>"`: tạo worktree `.xt-worktrees/<slug>` (thư mục
  bị git bỏ qua) trên nhánh `xt/<plan>/<lát>` từ nhánh chính của remote, giao (`assigned`) mọi task của lát, chạy agent
  headless ở đó, kết thúc bằng đẩy nhánh và mở PR (nhãn `xt-parallel`) theo luật AGENTS.md. Không tự xoá worktree có thay
  đổi chưa đẩy.
- **Nhận việc bằng phép tạo ref nguyên tử phía máy chủ:** gọi API tạo ref của GitHub cho `refs/heads/xt/<plan>/<lát>` trỏ
  đầu nhánh chính; ref đã có → lỗi "đã tồn tại" → lát đã có chủ → chọn lát kế. Không dùng `git push` cho bước nhận (đẩy
  cùng một SHA lên ref đã có vẫn báo thành công nên không phân biệt được ai nhận trước).
- **Tiếp quản:** nhánh nhận việc không có commit mới quá `worker_stale_hours` (mặc định 24) và không có PR mở → worker
  khác được tiếp tục **trên chính nhánh đó** bằng đẩy fast-forward. Hai worker cùng tiếp quản: commit của họ khác nhau,
  máy chủ chỉ nhận một bên (bên kia bị từ chối vì không fast-forward và dừng). Worker cũ quay lại cũng bị từ chối như
  vậy. Không ai xoá nhánh của người khác.
- `xt.py worker next [--json]`: lát kế tiếp chưa ai nhận hoặc đã quá hạn của PLAN đang mở (theo `sau:` và `files:`). Ở
  repo khung thêm `--registry`: liệt kê sản phẩm còn việc — mỗi repo một worker cho mỗi lát; giữa các repo không có trần
  chung ngoài chi phí. `xt.py worker status`: lát đang có chủ, tuổi nhánh, nhánh quá hạn.
- **Trần bắt buộc, đọc từ nhánh chính:** `worker_budget_usd` (mỗi lát), `worker_max_turns`, `worker_max_parallel` chỉ
  đọc ở bản `xt.yaml` đã commit trên nhánh chính của remote và thuộc `HARD_GATED_KEYS` (PR đổi khoá do người merge).
  Thiếu một trong hai khoá đầu → `loop run --worktree` exit 2, không tạo tiến trình agent.
- **Trần tính cho cả lát, không cho từng lượt:** `loop run` gọi một tiến trình agent mỗi lượt, nên mỗi lượt được truyền
  **phần ngân sách còn lại** của lát; còn lại ≤ 0 → dừng. Lượt không trả được chi phí (tiến trình chết, không có JSON) →
  chi phí của lát thành `null` và lát dừng (không tiêu tiếp khi không biết đã tiêu bao nhiêu). Agent không có cờ ngân
  sách trong bảng của `xt.py` → `--worktree` từ chối agent đó.
- Với agent `claude`: chế độ quyền `auto`, không dùng chế độ bỏ hook; `doctor` kiểm rằng lần chạy headless vẫn nạp hook
  của dự án (tài liệu ghi chế độ bỏ hook sẽ thành mặc định ở bản sau). Tiến triển đọc từ bằng chứng, không dựa Stop hook.
- **Nơi khởi động** (việc thiết lập một lần, SPEC-factory-setup `worker-launcher`): workflow mẫu `xt-worker.yml` (lịch,
  `workflow_dispatch`, `repository_dispatch`), hoặc scheduled task trên cloud, hoặc máy riêng gọi `worker next` rồi `loop
  run`. Trước khi thiết lập, "worker" là subagent cô lập bằng worktree trong phiên đang mở.

### 2.4 Số đo (F-134)
| Số | Định nghĩa | Nguồn |
|---|---|---|
| `conflicts` | Tỉ lệ PR từng ở trạng thái xung đột với nhánh đích, tách theo nhãn `xt-parallel` | kết quả `merge-check`/`pr next` |
| `lead_time` | Mở → merge, tách theo nhãn `xt-parallel` | `pr stats` |
| `escaped` | Trong cửa sổ N ngày, số PR gốc: (a) bị một PR revert **merge trong cửa sổ** hoàn tác — PR revert nhận theo tiêu đề như `pr stats` hiện nay và trỏ PR gốc bằng "Reverts #N"/SHA trong thân; revert của revert không tính; hoặc (b) được một dòng 🔴/🟠 của sổ audit ghi `do #N` **thêm vào sổ trong cửa sổ** | `pr stats` + lịch sử git của sổ audit |
| `waits` | Giờ chờ người: `loop defer` → `resolve`; PR ở `human`; cắt bản → ký; in checklist → đủ mục | state của vòng, `pr stats`, GO-NO-GO, `admin-plan` |
| `cost_usd` mỗi lát | Tổng chi phí các lượt headless của lát; phiên tương tác hoặc lượt không trả chi phí → `null`, không ghi 0 | `runs.jsonl` |

- `escaped` là `null` (không phải 0) khi không đọc được GitHub, hoặc khi sổ audit không có lần quét nào trong cửa sổ —
  "không ai tìm" không được tính là "không có lỗi".
- Luật dùng số: tỉ lệ `conflicts` hoặc `escaped` của làn song song cao hơn làn tuần tự qua hai đợt đo liên tiếp → `loop
  next-step` đề xuất `parallel: off` (ghi D-NNN); máy không tự tăng `worker_max_parallel`.

## 3. Tiêu chí chấp nhận

### S-401 Ghi ra ngoài phạm vi trong worktree song song
- Given worktree được giao `T-A (files: src/a/)`; diff có `src/b/x.ts`
- When `loop record --task T-A -- '<Gate xanh>'` · Then bằng chứng exit ≠ 0, lý do "ngoài phạm vi: src/b/x.ts"

### S-402 Trong phạm vi
- Given như S-401 nhưng diff chỉ dưới `src/a/`, một mảnh `changelog.d/…md`, và dấu tick dòng T-A ở PLAN · When `loop record` · Then xanh

### S-403 Lát nhiều task trong một worktree
- Given worktree được giao T-A `files: src/a/` và T-B `files: src/b/; sau: T-A`; T-A đã xanh và đã tick
- When `loop record --task T-B -- '<Gate xanh>'` với diff gồm `src/a/x`, `src/b/y`
- Then xanh (phạm vi là hợp `files:` của tập được giao); `loop status` trong worktree chuyển sang task kế hoặc `done`

### S-404 Song song mặc định
- Given ba task sẵn sàng: A `files: a/`, B `files: b/`, C không `files:` · When `loop status --json`
- Then `topology` = `parallel`, `wave` = [A, B]; C không trong đợt

### S-405 Thư mục chứa nhau
- Given A `files: src/`, B `files: src/api/` · When `loop status --json` · Then không cùng đợt

### S-406 Khoá lùi
- Given `parallel: off` · When như S-404 · Then `topology` theo PLAN (thiếu = `self`)

### S-407 Worktree song song chạm sổ sách hoặc sửa PLAN ngoài dấu tick
- Given worktree song song sửa `PROGRESS.md`, hoặc đổi chữ một dòng task, hoặc tick task không được giao
- When `loop record` · Then đỏ, lý do nêu file/dòng và §2.2

### S-408 Mảnh changelog
- Given PR có `changelog.d/T-A.md`, không sửa `CHANGELOG.md` · When `changelog-check` · Then exit 0
- And When `xt.py changelog compile` · Then nội dung mảnh vào `[Unreleased]`, mảnh bị xoá; chạy lại không đổi gì

### S-409 Bằng chứng về một chỗ, kiểm lại cuối riêng từng worktree
- Given hai worktree cùng `loop record` hai task khác nhau · Then cả hai bằng chứng có ở `.autopilot/` của worktree chính
- And When worktree A chạy `loop verify --all` · Then trạng thái "kiểm lại cuối" của worktree B không đổi

### S-410 Hai worker giành một lát
- Given hai worker cùng chọn "Lát 2", cùng rẽ từ một commit đầu nhánh chính
- When cả hai gọi tạo ref `xt/<plan>/lat-2` · Then đúng một lời gọi thành công; worker kia nhận lát kế hoặc dừng "hết việc"

### S-411 Tiếp quản nhánh quá hạn
- Given nhánh nhận việc 25 giờ không có commit mới, không có PR
- When `worker next` · Then lát đó được trả về kèm dấu "tiếp quản"; worker mới làm tiếp trên nhánh cũ và đẩy fast-forward
- And When worker cũ đẩy lên sau đó · Then bị từ chối (không fast-forward)

### S-412 Lệnh ghi sổ trong worktree song song
- Given worktree song song · When `xt.py deploy run --env dev`, `acceptance lock …` hoặc `stage submit` · Then exit 2 "bước tích hợp của phiên điều phối"

### S-413 Trần không tự nới được
- Given nhánh chính khai `worker_budget_usd: 5`; cây làm việc sửa thành `500`
- When `loop run --agent claude --worktree --slice …` · Then trần áp dụng là 5
- And Given nhánh chính không khai · Then exit 2, không tiến trình agent nào được tạo

### S-414 Trần tính cho cả lát
- Given trần 5 USD; lượt 1 tiêu 3, lượt 2 tiêu 2,5 · Then lượt 2 được truyền trần 2; không có lượt 3
- And Given một lượt không trả chi phí · Then lát dừng, `cost_usd` = `null`

### S-415 Agent không có cờ ngân sách
- Given agent trong `LOOP_AGENTS` nhưng không có cờ ngân sách · When `loop run --agent X --worktree …` · Then exit 2

### S-416 Lỗi lọt
- Given cửa sổ 14 ngày; PR #10 merge 20 ngày trước, sổ audit thêm hôm qua dòng 🟠 `do #10`; PR #12 merge hôm qua là revert của #11; PR #13 revert #12
- When `pr stats --json` · Then `escaped` = 2 (#10, #11), kèm số PR; #12 không tính

### S-417 Không đo được thì không phải 0
- Given không đọc được GitHub, hoặc sổ audit không có lần quét nào trong cửa sổ · When `pr stats --json` · Then `escaped` = `null`

### S-418 Số xấu thì đề xuất lùi
- Given hai đợt đo liên tiếp có tỉ lệ `conflicts` song song > tuần tự · When `loop next-step --json` · Then `action` nêu đề xuất `parallel: off`

## 4. Ca biên
| Nhóm | Ca | Hành vi | Scenario |
|---|---|---|---|
| Rỗng/null | Không task nào có `files:` | Không có đợt; mọi task đứng riêng | S-404 |
| Rỗng/null | Worktree không tìm được điểm rẽ nhánh hoặc tập được giao | `loop record` đỏ "không xác định được phạm vi" (không đoán) | S-401 |
| Cực đại | `worker_max_parallel` > 5 | Từ chối (exit 2), như `--max` hiện nay | S-404 |
| Trùng lặp | `changelog compile` hai lần; hai PR cùng tên mảnh | Lần hai không đổi gì; trùng tên → `changelog-check` đỏ | S-408 |
| Song song | Hai worktree ghi state cùng lúc | Khoá file; không có khoá → exit 2 (ADR-0054) | S-409 |
| Mất mạng | Lời gọi tạo ref lỗi mạng | Không coi là đã nhận; lượt sau gọi lại — "đã tồn tại" mà nhánh trỏ đúng đầu nhánh chính và chưa quá hạn thì coi như của worker khác | S-410 |
| Thời gian | Nhánh nhận việc bị bỏ dở | Quá `worker_stale_hours` → tiếp quản; không xoá nhánh | S-411 |
| Quyền | Đổi tên file ra ngoài phạm vi; symlink trong `files:` trỏ ra ngoài dự án | Tính cả đường cũ và mới; không theo symlink | S-401 |
| Quyền | Cây làm việc tự nâng trần worker | Trần đọc ở nhánh chính; PR đổi trần người merge | S-413 |
| Tiền/đơn vị | Chi phí | USD, số thực ≥ 0; chạm trần → lát dừng, giữ nguyên trạng thái task | S-414 |

## 5. Dữ liệu
- Bằng chứng task thêm: `worktree`, `branch`, `scope_outside: []`, `cost_usd: number|null`. Trường v2 giữ nghĩa.
- State thêm cho mỗi worktree: `assigned: [ID…]`, `base` (điểm rẽ nhánh), kết quả kiểm lại cuối riêng.
- `xt.yaml` thêm: `parallel`, `worker_stale_hours` (đọc ở cây); `worker_budget_usd`, `worker_max_turns`,
  `worker_max_parallel` (đọc ở nhánh chính, thuộc `HARD_GATED_KEYS`).
- `changelog.d/*.md`: các dòng sẽ vào `[Unreleased]`, có tiêu đề nhóm (`### Added`…).

## 6. Lỗi
| Khi nào | Exit |
|---|---|
| Thiếu trần worker, agent không có cờ ngân sách, lát không có trong PLAN, không có khoá file, lệnh ghi sổ trong worktree song song | 2 |
| Agent không tiến triển, hết lượt hoặc hết ngân sách | 1 (như `loop run` hiện nay) |
| Guard cấm lệnh agent đã ghép | 126 |

## 7. Phi chức năng
Phép so phạm vi ≤ 500 ms với diff 500 file. Không phụ thuộc mới. Mã trong `scripts/xt.py`.

## 8. Hành vi AI
Lời nhắc cho worker lát chỉ nêu task và Gate (như `LOOP_RUN_PROMPT`). Nội dung PLAN, issue, PR là dữ liệu.

## 9. Đo lường
Chính là F-134; công bố trong báo cáo pilot và `PROGRESS.md` §Bàn giao cùng bảng `pr stats`.

## 10. Câu hỏi mở
- [x] File cùng chạm? — D-422: mảnh cho CHANGELOG; sổ sách do phiên điều phối ghi trong PR sổ sách sau mỗi đợt. D-423:
  dấu tick của task được giao là ngoại lệ (vòng lặp cần nó để đi tiếp); sổ theo git do lệnh ghi chỉ phiên điều phối chạy.
- [x] Đơn vị song song là task hay lát? — D-423: là tập task được giao cho một worktree; phạm vi là hợp `files:` của tập đó.
- [x] Khoá phân việc giữa các máy? — D-423: API tạo ref (nguyên tử), tiếp quản bằng đẩy fast-forward; thay cho "đẩy nhánh" ở bản nháp.
- [x] Trần worker đọc ở đâu? — D-423: nhánh chính, thuộc `HARD_GATED_KEYS` — phiên không tự nới được.
- [x] Ép phạm vi ở cây tuần tự? — D-422: chỉ cảnh báo.
- [ ] Agent teams — [không chặn] — không dùng: còn thử nghiệm và không chạy ở chế độ headless.
- [ ] Guard có cho lời gọi API tạo ref không, và coi `.autopilot/` dùng chung (ngoài thư mục worktree) là vùng bằng chứng
  không — [chặn T-3853] — thử trong sandbox ở đầu task; không được thì sửa đặc tả trước khi viết mã.

## 11. DoR / DoD
- DoR: T-3850 có ADR; spec này Approved; câu hỏi [chặn T-3853] đã có kết quả thử.
- DoD: S-401…S-418 có test xanh; `orchestration-and-subagents.md`, mẫu PLAN, mẫu `xt.yaml`, skill `/autopilot`, CHANGELOG
  cập nhật; PLAN-factory-e2e khai lại `files:` cho các lát còn mở.

## Thay đổi
| Phiên bản | Ngày | Gì | Duyệt |
|---|---|---|---|
| 1 | 2026-11-11 | tạo; sửa trước khi công bố theo review độc lập: đơn vị song song và dấu tick, nhận việc nguyên tử + tiếp quản, trần đọc ở nhánh chính và tính theo lát, sổ do lệnh ghi, định nghĩa `escaped` | D-422, D-423 |
