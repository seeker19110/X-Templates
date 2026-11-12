# SPEC-factory-parallel — Song song theo file, worker ngoài phiên, số đo

| Trường | Giá trị |
|---|---|
| ID tính năng | F-131 (phạm vi file do máy kiểm + song song mặc định), F-132 (file mọi PR cùng chạm), F-133 (worker ngoài phiên + hàng đợi), F-134 (số đo) — chủ dự án 2026-11-11 "song song nếu không chạm cùng file", ADR-0075 §Quyết định 3 |
| Trạng thái | **F-132, F-134: Approved for implementation** (phiên chính tự duyệt, ADR-0008 — D-422, D-423). **F-131, F-133: Draft** — hai lượt review độc lập đều tìm ra lỗ ở phần phân việc và state dùng chung; chỉ chuyển Approved sau khi T-3850 thử trên git/GitHub thật các điểm ở §10 (D-424) |
| Phiên bản | 1 — ADR của T-3850 ghi quyết định kiến trúc (thay một phần D-142) và liên kết về đây, không chép lại |
| Dữ kiện | [`research/2026-11-11-factory-e2e-facts.md`](../../research/2026-11-11-factory-e2e-facts.md) §2, §3 |
| Kế hoạch | [`PLAN-factory-e2e.md`](../autopilot/PLAN-factory-e2e.md) T-3850…T-3854 |

## 1. User story
Là chủ dự án muốn nhanh, tôi muốn các lát việc không đụng cùng file được làm cùng lúc, mỗi lát một nhánh và một PR, kể
cả khi tôi không mở phiên nào — với điều kiện "không đụng cùng file" là thứ máy kiểm trên diff thật chứ không phải lời
khai của người lập kế hoạch, và có số đo để biết song song có thật sự nhanh hơn mà không lọt thêm lỗi.

## 2. Giao ước

### 2.1 Đơn vị song song và phạm vi file (F-131 — Draft)
- **Đơn vị song song là một worktree được giao một tập task**: một task (subagent trong phiên) hoặc cả một lát (worker).
- **Worktree song song chỉ do `xt.py` tạo**: `xt.py loop worktree add --tasks T-…[,T-…]` chạy ở worktree chính, in đường
  dẫn, và ghi vào state tập task được giao (`assigned`) cùng điểm rẽ nhánh. Lệnh từ chối khi gọi từ trong một worktree
  song song (không tự mở rộng phạm vi của mình). Không dùng worktree do công cụ agent tự tạo — worktree không có
  `assigned` thì `loop record` đỏ "không xác định được phạm vi".
- **Phạm vi của worktree** = hợp `files:` của mọi task trong `assigned` + mảnh changelog của nó (§2.2). Mỗi `loop record`
  trong worktree so tập file đổi kể từ điểm rẽ nhánh (`git diff --name-only <điểm rẽ>` + file chưa track; đổi tên tính
  cả đường cũ và mới) với phạm vi đó. Có file ngoài → bằng chứng ghi exit ≠ 0, lý do liệt kê file.
- **"Xong" trong worktree song song là bằng chứng, không phải dấu tick:** trong worktree đó, task thuộc `assigned` có bằng
  chứng xanh được coi là đã đóng khi xét `sau:` và khi chọn task kế. Worktree song song **không sửa file PLAN**. Phiên
  điều phối tick ở nhánh chính sau khi PR của worktree đã merge, bằng cách chạy lại Gate (`loop record`) trên nhánh chính
  — dấu tick luôn có bằng chứng chạy trên đúng cây đã merge.
- Hai worktree chạy cùng lúc được khi mọi task được giao đều khai `files:` và hai hợp `files:` không giao (thư mục chứa
  nhau tính là giao). Task thiếu `files:` không bao giờ vào đơn vị song song.
- Task chạy tuần tự trong cây chính: cùng phép so, nhưng chỉ ghi `scope_outside` vào bằng chứng (cảnh báo).
- `loop status --json`: khi có ≥ 2 task sẵn sàng (`sau:` đã thoả) có `files:` đôi một không giao (đúng phép so của `plan
  waves`), trả `topology: "parallel"` và `wave: [ID…]`, tối đa `worker_max_parallel` (mặc định 4; giá trị > 5 bị từ chối
  như `plan waves --max` hiện nay). Task ghi `(topo: self)` hoặc `(topo: audit)` đứng riêng; `(topo: review)` vào đợt
  được, vẫn cần reviewer trước PR.
- Khoá lùi `xt.yaml`: `parallel: off` → hành vi trước ADR-0075. Vắng = bật.
- **State:** bằng chứng từng task nằm ở `.autopilot/` của worktree chính (xác định qua `git rev-parse --git-common-dir`),
  ghi dưới khoá file, kèm `worktree` và `branch`. Kết quả "kiểm lại cuối" và bộ đếm lỗi lặp giữ riêng theo worktree.
  Worker chạy ở **bản clone khác** không chia sẻ `.autopilot/` với ai: với nó, PR xanh và đã merge là bằng chứng; phiên
  điều phối tick sau khi merge như trên.

### 2.2 File nhiều PR cùng chạm (F-132)
| File | Trong worktree song song | Cổng |
|---|---|---|
| `CHANGELOG.md` | Không sửa. Mỗi PR thêm một **mảnh** `changelog.d/<tên nhánh hoặc ID task>.md`; phiên điều phối gộp lúc cắt bản bằng `xt.py changelog compile` (xoá mảnh) | `changelog-check` chấp nhận mảnh thay cho dòng trong `[Unreleased]`; trùng tên mảnh → đỏ |
| File PLAN, `PROGRESS.md`, sổ quyết định, sổ audit, dấu tick blueprint | Không sửa. Phiên điều phối ghi trong **một PR sổ sách sau mỗi đợt** | `loop record` đỏ nếu worktree song song chạm |
| Sổ theo git do lệnh ghi (`STAGE.json`, sổ nghiệm thu, sổ triển khai) | Không ghi. `stage …`, `acceptance lock/amend`, `deploy run` là bước tích hợp của phiên điều phối, chạy sau khi các PR của đợt đã merge; trong worktree song song các lệnh ghi này exit 2 | chính lệnh từ chối |

Subagent và worker lát không tự quyết (luật sẵn có) nên không ghi sổ quyết định; số D-NNN chỉ cấp ở phiên điều phối.

### 2.3 Worker ngoài phiên và hàng đợi (F-133 — Draft)
Hai vai, không lẫn:

| Vai | Làm gì | Được quyết định (D-NNN)? |
|---|---|---|
| **Worker lát** | Làm các task của một lát đã có trong PLAN, trong một worktree, ra một PR | Không — gặp điểm quyết định thì `loop defer` |
| **Phiên điều phối headless** | Vai phiên chính nhưng không có người mở: lập/duyệt PLAN, giao lát, tích hợp, ghi sổ (dùng cho kênh ý tưởng — SPEC-factory-intake) | Có, theo ADR-0008 |

Worker lát:
- `xt.py loop run --agent <A> --worktree --slice "<tên mục ### của PLAN>"`: tạo worktree `.xt-worktrees/<slug>` (thư mục
  bị git bỏ qua) trên nhánh nhận việc, giao (`assigned`) mọi task của lát, chạy agent headless ở đó, **đẩy sau mỗi task
  xanh**, kết thúc bằng mở PR (nhãn `xt-parallel`) theo luật AGENTS.md. Không tự xoá worktree có thay đổi chưa đẩy.
- **Nhận việc bằng phép tạo ref nguyên tử phía máy chủ:** gọi API tạo ref của GitHub cho
  `refs/heads/xt/<plan>/<lát>/r<N>-<UTC yyyymmddThhmm>` trỏ đầu nhánh chính (`N` = lượt giao, bắt đầu từ 1). Trước khi
  tạo, liệt kê các ref dưới `xt/<plan>/<lát>/`: đã có ref lượt `N` hiện hành → lát có chủ → chọn lát kế. Tạo xong liệt kê
  lại: thấy ref lượt `N` khác có thời điểm sớm hơn → nhường (bên muộn dừng). Thời điểm nhận nằm ngay trong tên ref nên
  không cần đồng hồ nào khác.
- **Không tự tiếp quản.** Nhánh nhận việc không có commit mới của worker quá `worker_stale_hours` (mặc định 24, tính từ
  thời điểm trong tên ref hoặc commit cuối) chỉ được **báo** bởi `xt.py worker status`. Giao lại là quyết định của phiên
  điều phối (hoặc người): `xt.py worker reassign --slice … --decision D-NNN` tạo ref lượt `N+1` **từ đầu nhánh lượt
  trước** (giữ phần đã làm). Một nơi quyết định nên không có đua; worker cũ còn sống đẩy lên nhánh lượt cũ không ảnh
  hưởng lượt mới. Quá `worker_max_reassign` lượt (mặc định 2) → `loop block`. PR của lượt cũ (nếu có) do phiên điều
  phối đóng khi mở PR lượt mới.
- **Chi phí cộng dồn đi theo nhánh:** mỗi commit worker đẩy mang trailer chi phí cộng dồn của lát; lượt giao lại đọc
  trailer cuối và chỉ được tiêu **phần còn lại** của `worker_budget_usd` — giao lại không cấp trần mới.
- `xt.py worker next [--json]`: lát kế tiếp chưa có ref lượt nào của PLAN đang mở (theo `sau:` và `files:`). Ở repo khung
  thêm `--registry`: liệt kê sản phẩm còn việc — mỗi repo một worker cho mỗi lát; giữa các repo không có trần chung ngoài
  chi phí. `xt.py worker status`: lát đang có chủ, lượt, tuổi, nhánh quá hạn.
- **Trần bắt buộc, đọc từ nhánh chính:** `worker_budget_usd` (mỗi lát, qua mọi lượt), `worker_max_turns`,
  `worker_max_parallel`, `worker_max_reassign` chỉ đọc ở bản `xt.yaml` đã commit trên nhánh chính của remote và thuộc
  `HARD_GATED_KEYS` (PR đổi khoá do người merge). Thiếu một trong hai khoá đầu → `loop run --worktree` exit 2, không tạo
  tiến trình agent.
- **Trần tính cho cả lát, không cho từng lượt chạy:** `loop run` gọi một tiến trình agent mỗi lượt, nên mỗi lượt được
  truyền phần ngân sách còn lại; còn lại ≤ 0 → dừng. Lượt không trả được chi phí (tiến trình chết, không có JSON) → chi
  phí của lát thành `null` và lát dừng. Agent không có cờ ngân sách trong bảng của `xt.py` → `--worktree` từ chối agent đó.
- Với agent `claude`: chế độ quyền `auto`, không dùng chế độ bỏ hook; `doctor` kiểm rằng lần chạy headless vẫn nạp hook
  của dự án. Tiến triển đọc từ bằng chứng, không dựa Stop hook.
- **Nơi khởi động** (việc thiết lập một lần, SPEC-factory-setup `worker-launcher`): workflow mẫu `xt-worker.yml` (lịch,
  `workflow_dispatch`, `repository_dispatch`), hoặc scheduled task trên cloud, hoặc máy riêng gọi `worker next` rồi `loop
  run`. Trước khi thiết lập, "worker" là subagent trong phiên đang mở, làm trong worktree do `loop worktree add` tạo.

### 2.4 Số đo (F-134)
| Số | Định nghĩa | Nguồn |
|---|---|---|
| `conflicts` | Tỉ lệ PR từng ở trạng thái xung đột với nhánh đích, tách theo nhãn `xt-parallel` | kết quả `merge-check`/`pr next` |
| `lead_time` | Mở → merge, tách theo nhãn `xt-parallel` | `pr stats` |
| `escaped` | Trong cửa sổ N ngày, số PR gốc: (a) bị một PR revert **merge trong cửa sổ** hoàn tác — PR revert nhận theo tiêu đề như `pr stats` hiện nay và trỏ PR gốc bằng "Reverts #N"/SHA trong thân; revert của revert không tính; hoặc (b) được một dòng 🔴/🟠 của sổ audit ghi `do #N` **thêm vào sổ trong cửa sổ** | `pr stats` + lịch sử git của sổ audit |
| `waits` | Giờ chờ người: `loop defer` → `resolve`; PR ở `human`; cắt bản → ký; in checklist → đủ mục | state của vòng, `pr stats`, GO-NO-GO, `admin-plan` |
| `cost_usd` mỗi lát | Chi phí cộng dồn của lát qua mọi lượt; phiên tương tác hoặc lượt không trả chi phí → `null`, không ghi 0 | trailer trên nhánh, `runs.jsonl` |

- `escaped` là `null` (không phải 0) khi không đọc được GitHub, hoặc khi sổ audit không có lần quét nào trong cửa sổ —
  "không ai tìm" không được tính là "không có lỗi". Giới hạn đã biết: dòng `do #N` do agent ghi khi audit; số này là sàn.
- Luật dùng số: tỉ lệ `conflicts` hoặc `escaped` của làn song song cao hơn làn tuần tự qua hai đợt đo liên tiếp → `loop
  next-step` đề xuất `parallel: off` (ghi D-NNN); máy không tự tăng `worker_max_parallel`.

## 3. Tiêu chí chấp nhận

### S-401 Ghi ra ngoài phạm vi trong worktree song song
- Given worktree được giao `T-A (files: src/a/)`; diff có `src/b/x.ts`
- When `loop record --task T-A -- '<Gate xanh>'` · Then bằng chứng exit ≠ 0, lý do "ngoài phạm vi: src/b/x.ts"

### S-402 Trong phạm vi
- Given như S-401 nhưng diff chỉ dưới `src/a/` và một mảnh `changelog.d/…md` · When `loop record` · Then xanh

### S-403 Lát nhiều task trong một worktree, không cần tick
- Given worktree được giao T-A `files: src/a/` và T-B `files: src/b/; sau: T-A`; T-A có bằng chứng xanh, PLAN chưa tick
- When `loop record --task T-B -- '<Gate xanh>'` với diff gồm `src/a/x`, `src/b/y`
- Then xanh (T-A coi là đã đóng trong worktree này; phạm vi là hợp `files:` của tập được giao); `loop status` trong
  worktree chuyển sang task kế hoặc `done`

### S-404 Song song mặc định
- Given ba task sẵn sàng: A `files: a/`, B `files: b/`, C không `files:` · When `loop status --json`
- Then `topology` = `parallel`, `wave` = [A, B]; C không trong đợt

### S-405 Thư mục chứa nhau
- Given A `files: src/`, B `files: src/api/` · When `loop status --json` · Then không cùng đợt

### S-406 Khoá lùi
- Given `parallel: off` · When như S-404 · Then `topology` theo PLAN (thiếu = `self`)

### S-407 Worktree song song chạm PLAN hoặc sổ sách
- Given worktree song song sửa `PROGRESS.md`, hoặc tick một dòng task ở PLAN · When `loop record` · Then đỏ, lý do nêu file và §2.2

### S-408 Mảnh changelog
- Given PR có `changelog.d/T-A.md`, không sửa `CHANGELOG.md` · When `changelog-check` · Then exit 0
- And When `xt.py changelog compile` · Then nội dung mảnh vào `[Unreleased]`, mảnh bị xoá; chạy lại không đổi gì

### S-409 Bằng chứng về một chỗ, kiểm lại cuối riêng từng worktree
- Given hai worktree cùng `loop record` hai task khác nhau · Then cả hai bằng chứng có ở `.autopilot/` của worktree chính
- And When worktree A chạy `loop verify --all` · Then trạng thái "kiểm lại cuối" của worktree B không đổi

### S-410 Hai worker giành một lát
- Given hai worker cùng chọn "Lát 2" cách nhau một phút · When cả hai tạo ref lượt 1 (tên mang thời điểm khác nhau)
- Then sau bước liệt kê lại, đúng một worker tiếp tục (thời điểm sớm hơn); worker kia dừng hoặc nhận lát kế

### S-411 Nhánh quá hạn chỉ được báo, không tự tiếp quản
- Given ref lượt 1 mang thời điểm 25 giờ trước, không có commit của worker
- When `worker next` · Then lát đó **không** được trả về; `worker status` báo quá hạn
- And When phiên điều phối `worker reassign --slice … --decision D-NNN` · Then có ref lượt 2 từ đầu nhánh lượt 1; ngân
  sách còn lại = trần trừ chi phí cộng dồn ở trailer cuối của lượt 1
- And Given đã có lượt 3 (vượt `worker_max_reassign` 2) · Then `reassign` từ chối, vòng `block`

### S-412 Lệnh ghi sổ và tạo worktree trong worktree song song
- Given worktree song song · When `xt.py deploy run --env dev`, `acceptance lock …`, `stage submit` hoặc `loop worktree add …` · Then exit 2

### S-413 Trần không tự nới được
- Given nhánh chính khai `worker_budget_usd: 5`; cây làm việc sửa thành `500`
- When `loop run --agent claude --worktree --slice …` · Then trần áp dụng là 5
- And Given nhánh chính không khai · Then exit 2, không tiến trình agent nào được tạo

### S-414 Trần tính cho cả lát
- Given trần 5 USD; lượt chạy 1 tiêu 3, lượt chạy 2 tiêu 2,5 · Then lượt 2 được truyền trần 2; không có lượt 3
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

### S-419 Cảnh báo phạm vi ở cây tuần tự
- Given cây chính, task có `files:`, diff ra ngoài · When `loop record` · Then theo exit của Gate; bằng chứng có `scope_outside`

### S-420 Tick sau merge có bằng chứng trên nhánh chính
- Given PR của worktree đã merge · When phiên điều phối `loop record --task T-A -- '<Gate>'` ở nhánh chính · Then task `[x]` với bằng chứng chạy trên cây đã merge; Gate đỏ trên nhánh chính → không tick

## 4. Ca biên
| Nhóm | Ca | Hành vi | Scenario |
|---|---|---|---|
| Rỗng/null | Không task nào có `files:` | Không có đợt; mọi task đứng riêng | S-404 |
| Rỗng/null | Worktree không có `assigned` (do công cụ khác tạo) | `loop record` đỏ "không xác định được phạm vi" (không đoán) | S-401 |
| Cực đại | `worker_max_parallel` > 5 | Từ chối (exit 2), như `--max` hiện nay | S-404 |
| Trùng lặp | `changelog compile` hai lần; hai PR cùng tên mảnh | Lần hai không đổi gì; trùng tên → `changelog-check` đỏ | S-408 |
| Song song | Hai worktree ghi state cùng lúc | Khoá file; không có khoá → exit 2 (ADR-0054) | S-409 |
| Mất mạng | Lời gọi tạo ref hoặc liệt kê ref lỗi mạng | Không coi là đã nhận; không làm việc khi chưa liệt kê lại được | S-410 |
| Thời gian | Đồng hồ worker lệch | Thời điểm trong tên ref là của worker; lệch chỉ ảnh hưởng thứ tự nhường và báo quá hạn, không gây tự tiếp quản | S-411 |
| Quyền | Đổi tên file ra ngoài phạm vi; symlink trong `files:` trỏ ra ngoài dự án | Tính cả đường cũ và mới; không theo symlink | S-401 |
| Quyền | Cây làm việc tự nâng trần worker | Trần đọc ở nhánh chính; PR đổi trần người merge | S-413 |
| Tiền/đơn vị | Chi phí | USD, số thực ≥ 0; chạm trần → lát dừng; giao lại không cấp trần mới | S-411, S-414 |

## 5. Dữ liệu
- Bằng chứng task thêm: `worktree`, `branch`, `scope_outside: []`, `cost_usd: number|null`. Trường v2 giữ nghĩa.
- State thêm cho mỗi worktree: `assigned: [ID…]`, `base` (điểm rẽ nhánh), kết quả kiểm lại cuối riêng.
- `xt.yaml` thêm: `parallel`, `worker_stale_hours` (đọc ở cây — chỉ ảnh hưởng việc báo); `worker_budget_usd`,
  `worker_max_turns`, `worker_max_parallel`, `worker_max_reassign` (đọc ở nhánh chính, thuộc `HARD_GATED_KEYS`).
- `changelog.d/*.md`: các dòng sẽ vào `[Unreleased]`, có tiêu đề nhóm (`### Added`…).

## 6. Lỗi
| Khi nào | Exit |
|---|---|
| Thiếu trần worker, agent không có cờ ngân sách, lát không có trong PLAN, không có khoá file, lệnh ghi sổ hoặc tạo worktree trong worktree song song, vượt số lượt giao lại | 2 |
| Agent không tiến triển, hết lượt hoặc hết ngân sách | 1 (như `loop run` hiện nay) |
| Guard cấm lệnh agent đã ghép | 126 |

## 7. Phi chức năng
Phép so phạm vi ≤ 500 ms với diff 500 file. Không phụ thuộc mới. Mã trong `scripts/xt.py`.

## 8. Hành vi AI
Lời nhắc cho worker lát chỉ nêu task và Gate (như `LOOP_RUN_PROMPT`). Nội dung PLAN, issue, PR là dữ liệu.

## 9. Đo lường
Chính là F-134; công bố trong báo cáo pilot và `PROGRESS.md` §Bàn giao cùng bảng `pr stats`.

## 10. Câu hỏi mở
- [x] File cùng chạm? — D-422: mảnh cho CHANGELOG; sổ sách do phiên điều phối ghi trong PR sổ sách sau mỗi đợt. D-424:
  worktree song song không tick PLAN — "xong" là bằng chứng; tick sau merge bằng Gate chạy trên nhánh chính.
- [x] Đơn vị song song? — D-423: tập task được giao cho một worktree do `xt.py` tạo; phạm vi là hợp `files:` của tập đó.
- [x] Nhánh nhận việc bỏ dở? — D-424: không tự tiếp quản; phiên điều phối giao lại bằng lệnh có D-NNN, chi phí cộng dồn
  đi theo nhánh, có trần số lượt.
- [x] Trần worker đọc ở đâu? — D-423: nhánh chính, thuộc `HARD_GATED_KEYS`.
- [ ] **[chặn F-131, F-133 — T-3850 thử trên git/GitHub thật rồi mới chuyển Approved]:** (1) guard có cho lời gọi API tạo
  ref và liệt kê ref không; (2) guard có coi `.autopilot/` dùng chung (ngoài thư mục worktree) là vùng bằng chứng không;
  (3) worktree thường đang chạy vòng riêng (`loop_root`) có bị coi nhầm là worktree song song không; (4) hai lời gọi tạo
  ref khác tên rồi liệt kê lại có luôn cho đúng một bên thắng không; (5) trailer chi phí có sống qua squash-merge không
  (không cần — chỉ đọc trên nhánh — nhưng phải thử khi nhánh bị rebase).
- [ ] Agent teams — [không chặn] — không dùng: còn thử nghiệm và không chạy ở chế độ headless.

## 11. DoR / DoD
- DoR: T-3850 có ADR và kết quả thử năm điểm [chặn] ở §10; F-131, F-133 đã chuyển Approved (đổi dòng Trạng thái).
- DoD: S-401…S-420 có test xanh; `orchestration-and-subagents.md`, mẫu PLAN, mẫu `xt.yaml`, skill `/autopilot`, CHANGELOG
  cập nhật; PLAN-factory-e2e khai lại `files:` cho các lát còn mở.

## Thay đổi
| Phiên bản | Ngày | Gì | Duyệt |
|---|---|---|---|
| 1 | 2026-11-11 | tạo; sửa theo hai lượt review độc lập: đơn vị song song, nhận việc nguyên tử, trần đọc ở nhánh chính và tính theo lát, sổ do lệnh ghi, định nghĩa `escaped` (D-423); bỏ tự tiếp quản, bỏ tick trong worktree, worktree do `xt.py` tạo, F-131/F-133 về Draft chờ thử thật (D-424) | D-422, D-423, D-424 |
