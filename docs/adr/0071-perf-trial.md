# ADR-0071: `perf trial` — máy quản lý trọn một lần thử tối ưu (đo cùng lượt ở worktree ghim, giữ/thu hồi, sổ bền) — lát 3 của ADR-0052

- **Trạng thái:** Đã chấp nhận (2026-11-05, phiên chính tự duyệt — D-356: nhận cả mười bốn đề xuất in đậm ở §Điểm đã chốt;
  chủ repo 2026-11-05 "làm hết đi"). Chưa triển khai — T-3680…T-3687 (PLAN-harden-2026-10-27-loops).
- **Ngày:** 2026-11-05.
- **Thực hiện:** [ADR-0052 §Quyết định 7](0052-loop-state-rev-progress-perf-v2-next-step.md#quyết-định) (D-203; ràng buộc đầu
  vào — bảng ở §Ràng buộc), thêm `LOOP-OPT-007` (held-out) và `LOOP-OPT-004` (falsifier) theo review #290 lượt 8.
- **Liên quan:** ADR-0048 (skill `/optimize`), ADR-0009 (một phiên), ADR-0018 (guard), ADR-0050 (trần thư mục),
  [`optimization-loop.md`](../../framework/11-autonomous-loop/optimization-loop.md) (`LOOP-OPT-002`/`-003`/`-004`/`-007`/
  `-008`/`-009`/`-010`/`-011`).
- **Nghiên cứu:** [spike 2026-11-05](../../research/2026-11-05-perf-trial-spike.md) (số đo dưới đây lấy từ đó);
  [nghiên cứu ba vòng §7.2, §9.3, §10](../../research/2026-10-26-autopilot-complete-optimize.md).

## Bối cảnh

Hôm nay một lần thử tối ưu là Gate do dự án tự viết (`perf-gate.sh` mẫu ở `optimization-loop.md`) cộng các bước agent tự làm
theo skill: ghi giả thuyết vào PERF-LOG, hoàn tác khi không `improved`, đếm ba lần không `improved`. `optimization-loop.md`
liệt kê bốn giới hạn của Gate mẫu và nói "rào thật là `perf trial`". Ở pha `harden` guard không nới lệnh git vứt thay đổi
cục bộ (`LOCAL_GIT`, ADR-0040 chỉ áp pha build), nên "agent tự hoàn tác" vốn đã vướng. Spike 2026-11-05 cho thấy:

- **Đo theo khối không tin được:** A/A cùng mã, 10 lần mỗi bên, đo theo khối (như hai lượt `perf sample`): 11/60 kết luận
  `improved` sai (18 %), 8/60 `regressed` sai; đo xen kẽ: 0/60 `improved`, 1/60 `regressed`. Số lệnh bytecode: trùng 3/3.
- **Cây đo sai mà không lỗi:** chạy bộ đo ở worktree gốc bằng venv của cây agent nạp `fastlib` từ cây candidate (`.pth`
  editable ghi đường tuyệt đối); `node_modules` mượn từ cây agent phân giải `jslib` về cây candidate. `--setup` riêng từng
  cây thì 4/4 trỏ đúng; tốn 0,80–0,84 s/cây (uv, cache ấm).
- **File bị bỏ qua lừa đo tại chỗ:** `.pth` trong `.venv` của cây agent chèn mô-đun giả → 19 lệnh thay 2 400 022; `tree_fp`
  không đổi, `perf guard` exit 0. Candidate dựng lại ở worktree riêng với `--setup` mới thì không bị lừa (+0,85 s).
- **Thu hồi:** `git stash push --include-untracked -- . ':(exclude).autopilot'` khi `.autopilot/` bị ignore → exit 1, **tạo
  mục stash nhưng để nguyên candidate, đã `git add`**. Danh sách file tường minh → exit 0, vân tay về đúng lúc start.
  Stash không thu hồi file bị ignore và sửa trong submodule (vân tay lệch).
- **Held-out sinh lúc finish** (hạt giống `os.urandom`, bộ sinh từ commit gốc) bắt đường tắt hard-code N của bộ đo:
  −99,9997 % trên bộ đo, ±4 lệnh so với `start_head` trên held-out.

## Yếu tố quyết định

Đúng và an toàn trước (không giữ nhầm, không mất sửa của người dùng, không thu hồi bằng lệnh phá huỷ) · giữ đường lùi (mỗi
lát một PR, `perf compare`/`perf guard` cũ giữ nguyên) · stdlib Python ≥ 3.11, không hard-code stack (`--setup` và lệnh đo
do dự án khai) · C901 ≤ 10, `mypy --strict`, coverage 100 % · không nới cổng/trần, skill `/optimize` còn 8 B dư (đổi chữ, không
nối) · không hứa chi phí chưa đo trên dự án thật.

## Các phương án đã cân nhắc

1. **Giữ Gate mẫu + skill tự hoàn tác** (hiện trạng) — bốn giới hạn đã ghi, đo theo khối, hoàn tác vướng guard pha harden.
2. **`perf trial` đo candidate tại chỗ** (cây agent) + kiểm file khoá — rẻ nhất; spike: file bị ignore lừa được, không công
   cụ nào thấy.
3. **`perf trial` dựng mọi cây đo ở worktree ghim ngoài cây agent** (gốc, `start_head`, candidate = `start_head` + diff,
   bộ đo phủ từ gốc), `--setup` từ gốc trong từng cây, đo xen kẽ — +~0,85 s/cây ở spike.
4. **Runner/sandbox ngoài phiên** — chặn được cả can thiệp cùng uid; cần quyền/chi phí của chủ dự án, đối chiếu ADR-0009
   — ngoài phạm vi (ADR-0052 §8).

Đề xuất **phương án 3**.

## Quyết định

### 1. Cấu hình lấy từ commit gốc

`perf trial` đọc một file JSON cấu hình bằng `git show <base_sha>:<đường>` (mặc định `perf/trial.json`, `--config` đổi được
ở lần `start` đầu của vòng), không đọc từ cây agent: `schema`, `setup` (lệnh chạy trong mỗi cây), `probe` (tuỳ chọn, in
đường mô-đun đã phân giải), `locked` (glob bộ đo, test tương đương, input; máy tự thêm chính file cấu hình và `xt.py`),
`metric` `{cmd, kind: wall|exact, unit, higher_is_better, runs}` (`exact` = số cuối stdout), `secondary[]` `{name, cmd,
kind, unit, ceiling}` (trần tuyệt đối), `equiv` (lệnh test tương đương), `heldout` `{gen, cmd}` (`gen <seed>` in danh sách
input; `cmd` có `{input}`), `timeout`. Thiếu file ở gốc → exit 2 (không có gì để tin).

### 2. Hợp đồng CLI

| Lệnh | Việc | Exit |
|---|---|---|
| `perf trial start --hotspot PATH[::SYM]… --hypothesis TEXT --falsifier EXPR [--base REF] [--config PATH] [--budget N]` | Lần `start` đầu của vòng ghim `base_sha` (phân giải `REF` một lần, mặc định `origin/main`; không đọc `XT_PROGRESS_BASE`); lần sau `--base` phải trùng. Đòi: không có lần thử mở; cây sạch ngoài `.autopilot/` (và PERF-LOG — Điểm mở 9); `HEAD^{tree}` = `kept_tree` gần nhất (vòng mới: = cây `base_sha` hoặc bỏ qua); `PATH` có ở gốc. Ghi `start_head`, `fp_start`, giả thuyết, falsifier vào state và một dòng `start` vào sổ | 0 · 2 từ chối, không ghi gì · 3 điểm nóng đã 3 lần liên tiếp không giữ, hoặc hết `--budget` |
| `perf trial finish [--resume] [--no-apply] [--json]` | Đóng băng candidate (`candidate_fp`), kiểm, đo, quyết, giữ hoặc thu hồi, ghi sổ rồi PERF-LOG (§4); `--no-apply` chỉ in quyết định và lệnh thu hồi | 0 giữ · 1 thu hồi xong (vân tay = `fp_start`) · 2 không quyết, cây không đụng (lý do + lối ra) |
| `perf trial status [--json]` | Pha, lần thử mở, đếm theo điểm nóng, lệnh kế (`finish`/`finish --resume`/`abort`) | 0 · 2 state hỏng |
| `perf trial abort --reason TEXT` | Thu hồi như `finish` thu hồi, ghi `aborted` (tính vào 3 lần) | 0 · 2 không có lần thử, `HEAD ≠ start_head`, hay vân tay lệch sau thu hồi |

Exit 2 luôn nghĩa "máy không quyết và không đụng cây"; agent không thử cách khác cho cùng hiệu ứng (`LOOP-STOP-025`).

### 3. Sổ máy (trong `.autopilot/`, ghi bởi `xt.py`, guard chặn ghi tay)

- `perf-trial.json` — lần thử đang mở: `id` (`PT-NNNN`), `base_sha`, `config_sha` (blob ở gốc), `tool_sha`, `hotspot`,
  `hypothesis`, `falsifier`, `start_head`, `fp_start`, `phase` (`started` → `measuring` → `decided` → `closed`),
  `candidate_fp`, `candidate_files[]`, `seed`, `worktrees{}`, `stash` (SHA commit stash), `verdict`, `rev`. Ghi qua khoá
  `flock` + `rev` như `update_state` (ADR-0052 §2); khoá riêng `perf-trial.lock` giữ suốt `finish` (một người đo).
- `perf-trials.jsonl` — chỉ nối, mỗi sự kiện một dòng (`start`, `decide`), `fsync`; nguồn của đếm ba lần, chống thử trùng
  (khoá `hotspot` + `candidate_fp`) và của PERF-LOG. Bền qua restart vì là file, không phải bộ nhớ phiên.

### 4. Máy trạng thái của `finish`

1. **Đóng băng:** `HEAD == start_head` (khác → exit 2, FLOW-28); `candidate_fp = tree_fingerprint`; `candidate_files` =
   `git status --porcelain -z --untracked-files=all` trừ `.autopilot/`; rỗng → thu hồi rỗng, `verdict: empty`; trùng khoá
   đã thử → exit 2. Phase `measuring`, sinh `seed` (ghi trước khi đo; resume dùng lại).
2. **Dựng cây** (tạm, ngoài cây agent, `git worktree add --detach`): gốc `base_sha`, `start_head`, candidate = `start_head` +
   `git diff --binary HEAD` + file chưa track + `git checkout <base_sha> -- <locked>`; `submodule update --init` theo
   `setup`. Mỗi cây chạy `setup` từ gốc với môi trường đã gỡ `VIRTUAL_ENV`, `PYTHONPATH`, `PYTHONHOME`, `NODE_PATH` và mục
   `PATH` nằm trong cây agent; rồi kiểm **trỏ đúng cây** (Điểm mở 4). Lỗi → exit 2.
3. **Bộ chấm bị sửa:** `candidate_files` khớp `locked` → không đo, thu hồi, `verdict: tampered` (FLOW-29, Điểm mở 12).
4. **Đo cùng lượt, xen kẽ:** chỉ số chính ở ba cây, vòng tròn đổi thứ tự (B K C, K C B, C B K…), `runs` mỗi cây; `exact` chạy
   ≥ 3 lần và đòi trùng nhau (lệch → `insufficient`); chỉ số phụ cùng lượt. Mẫu ghi theo v2 (ADR-0052 §4), thêm `kind` và
   `env.python` của lệnh đo. Kiểm vân tay cây gốc/`start_head` sau lượt (bẩn → exit 2, FLOW-28).
5. **Tương đương:** `equiv` exit 0 trên cây candidate (và trên cây gốc — đỏ ở gốc = cấu hình hỏng, exit 2).
6. **Held-out:** `heldout.gen <seed>` chạy ở cây gốc; đo `heldout.cmd` cho từng input ở `start_head` và candidate (§6).
7. **Quyết:** giữ ⇔ (4) `improved` so với gốc **và** so với `start_head` · (5) xanh · (6) đạt · mọi chỉ số phụ ≤ trần ·
   falsifier không trúng. Còn lại thu hồi, lý do đầu tiên vào `verdict`.
8. **Hành động:** giữ → để candidate trong cây, ghi `kept_tree` (index tạm: `read-tree HEAD` + `add -A -- <candidate_files>`
   + `write-tree`; spike: bằng `HEAD^{tree}` sau commit). Thu hồi → `git stash push --include-untracked -m "xt-perf-trial
   <id>" -- <candidate_files>` rồi đòi `tree_fingerprint == fp_start`; lệch (vd submodule) → phase giữ `decided`, exit 2,
   in SHA stash (FLOW-33). Không `checkout -- .`/`reset --hard`/`clean`; không `stash drop` (guard hỏi).
9. **Ghi sổ sau quyết định:** dòng `decide` vào `perf-trials.jsonl`, rồi một hàng PERF-LOG (giả thuyết, falsifier, số
   gốc→candidate, `start_head`→candidate, held-out, phụ, quyết, lý do), rồi dọn worktree, phase `closed`.

### 5. Công cụ chấm từ commit gốc

`finish`/`abort` gọi từ bất kỳ bản nào: so sha256 của chính file với blob `<base_sha>:<đường xt.py>`; khác → xuất blob ra
thư mục tạm và `exec python3 -I <tạm>/xt.py perf trial …` (spike: `xt.py` một file, chạy được qua `git show`). Skill/PLAN
dùng `python3 -I <(git show <base_sha>:<đường xt.py>) perf trial finish` làm Gate — đầu vào không lấy từ cây candidate.
Can thiệp cùng uid trong lúc đo vẫn là giới hạn đã biết (`optimization-loop.md`).

### 6. Held-out (`LOOP-OPT-007`)

Input held-out sinh **sau khi** candidate đóng băng, từ hạt giống 64 bit `os.urandom` ghi ở state, bằng `heldout.gen` của
gốc: agent không thể thấy input trước khi viết candidate. Lượt so thứ hai trên held-out: candidate phải `improved` so với
`start_head` (Điểm mở 7) và đầu ra bằng `start_head` khi `heldout.cmd` in đầu ra. Không khai `heldout` trong cấu hình →
cảnh báo, `LOOP-OPT-007` ghi "không áp dụng" vào PERF-LOG.

### 7. Giả thuyết và falsifier (`LOOP-OPT-004`)

`start` bắt buộc `--hypothesis` và `--falsifier`, trên cây sạch — thứ tự "ghi trước khi sửa" do máy chứng minh (`fp_start`
là cây không có candidate). Falsifier dạng `<chỉ số> <op> <phần trăm>` so với `start_head` (vd `primary > -5%`: đổi tệ hơn
−5 % là bác bỏ). Máy đánh giá ở bước 7; trúng → thu hồi (Điểm mở 8). Giả thuyết/falsifier không sửa được sau `start`.

### 8. Ba lần không giữ mỗi điểm nóng (`LOOP-OPT-011`)

Đếm từ `perf-trials.jsonl`: chuỗi lần thử liên tiếp cùng điểm nóng (đường chuẩn hoá) có `verdict` ≠ `kept`, kể cả `aborted`,
`tampered`, `incomplete`; về 0 khi một lần giữ. `start` exit 3 khi chuỗi ≥ 3 → đổi điểm nóng hoặc `loop defer`. `finish`
đòi `candidate_files` chạm ít nhất một đường của điểm nóng (không thì thu hồi, `verdict: off-hotspot`) — đổi tên điểm nóng
không lách được đếm.

### 9. Resume, abort, đồng thời

`finish` khi phase `measuring`/`decided` → exit 2 "chạy `finish --resume`". `--resume`: `measuring` + vân tay cây =
`candidate_fp` → đo lại từ đầu (bỏ mọi số dở, cùng `seed`), quyết một lần; vân tay khác → thu hồi, `verdict: incomplete`;
`decided` → làm nốt bước 8–9 (idempotent: không ghi trùng dòng `decide`). Worktree tạm mất sau reboot → dựng lại; `git
worktree prune` trước. Hai `finish` cùng lúc: `perf-trial.lock` không lấy được → exit 2 ngay.

### 10. Ca FLOW

| ID | Given / When | Then |
|---|---|---|
| FLOW-20 | candidate `neutral` → `finish` | thu hồi đúng `candidate_files`, `.autopilot/` và file người dùng ngoài danh sách còn nguyên, vân tay = `fp_start`, PERF-LOG có dòng bỏ — **đường thu hồi** |
| FLOW-21 | kill giữa lượt đo → `finish --resume` | không ghi `decide` trùng; cây = `fp_start` hoặc giữ đúng; `incomplete` khi cây đã đổi |
| FLOW-22 | 3 lần không giữ cùng điểm nóng, restart giữa chừng | `start` exit 3 |
| FLOW-23 | chỉ số chính `improved`, phụ vượt trần | thu hồi, exit 1 |
| FLOW-24…26 | (giữ chỗ nghiên cứu §10: field, steward — không dùng ở ADR này) | |
| FLOW-27 | candidate `improved` so với gốc và `start_head`, test + held-out xanh | exit 0, `kept_tree` = cây sau commit, `start` kế nhận — **đường giữ** |
| FLOW-28 | commit giữa chừng / dời `origin/main` sau ghim / sửa worktree gốc trong lượt | exit 2 không đụng cây / base không đổi / exit 2 — **baseline bị lái** |
| FLOW-29 | candidate sửa file khoá / `.pth` bị ignore trong `.venv` cây agent | `tampered`, thu hồi / số đo không đổi vì đo ở cây dựng lại — **bộ chấm bị sửa** |
| FLOW-30 | candidate hard-code input của bộ đo | held-out không `improved` → thu hồi |
| FLOW-31 | `start` thiếu giả thuyết/falsifier hoặc cây bẩn; falsifier trúng | exit 2; thu hồi |
| FLOW-32 | `setup` để mô-đun phân giải ra ngoài cây đo | exit 2 trước khi đo |
| FLOW-33 | candidate sửa nội dung submodule | stash không đưa về `fp_start` → exit 2, in SHA stash, không thử cách khác |
| FLOW-34 | hai `finish` đồng thời (barrier) | một đo, một exit 2 |

### Ràng buộc ADR-0052 §7 → cách đáp ứng

| Ràng buộc | Cách đáp ứng | Bằng chứng/ca |
|---|---|---|
| Baseline ghim một lần cho cả vòng, không `XT_PROGRESS_BASE`, không theo HEAD agent chọn | `start` đầu ghim SHA vào sổ; `--base` sau phải trùng; không đọc biến môi trường | spike: dời ref sau ghim, SHA không đổi · FLOW-28 |
| Candidate = phần chưa commit trên `start_head`; `finish` đòi `HEAD == start_head` | §4 bước 1 | FLOW-28 |
| Máy tự đo gốc/`start_head`/candidate cùng lượt, cùng môi trường | §4 bước 2 + 4: ba worktree, đo xen kẽ | A/A 18 % → 0 % |
| `--setup` ghim từ gốc; editable/`node_modules`/submodule không trỏ về cây candidate | `setup` từ cấu hình ở gốc, chạy trong từng cây, gỡ biến môi trường, kiểm trỏ đúng cây | spike §2: hiểm hoạ tái hiện, 4/4 đúng sau setup · FLOW-32 |
| Lệnh đo, glob bộ đo, test tương đương, chính `xt.py` từ gốc (`LOOP-OPT-002`/`-003`) | §1 cấu hình từ blob gốc; phủ `locked` từ gốc vào cây candidate; §5 công cụ chấm | FLOW-29 |
| Đại lượng tất định và chỉ số phụ (`-008`/`-009`) | `metric.kind: exact` (đòi trùng ≥ 3 lần), `secondary[]` có trần | spike: 3/3 trùng · FLOW-23 |
| Giữ chỉ khi `improved` so với cả giữ gần nhất và gốc, kèm test tương đương xanh | §4 bước 7 (`start_head` = cây giữ gần nhất nhờ ràng buộc dưới) | FLOW-27 |
| Thu hồi đúng file bằng `git stash push --include-untracked`, kiểm vân tay lúc start | §4 bước 8, danh sách file tường minh (pathspec loại trừ hỏng — spike V1) | FLOW-20, FLOW-33 |
| PERF-LOG ghi sau quyết định | §4 bước 9 | FLOW-20, FLOW-27 |
| `start` đòi cây sạch ngoài `.autopilot/` và `start_head` có tree = cây giữ gần nhất (hoặc đo luôn cây đó) | §2 `start` (Điểm mở 5, 9) | FLOW-31 |
| Ghi giả thuyết trước khi sửa (`LOOP-OPT-004`) + falsifier | §7 | FLOW-31 |
| Ba lần không `improved` mỗi điểm nóng bền qua restart (`LOOP-OPT-011`) | §8 từ `perf-trials.jsonl` | FLOW-22 |
| `--resume` sau crash | §9 | FLOW-21 |
| Chỉ số phụ vượt trần → đỏ | §4 bước 7 | FLOW-23 |
| Held-out `LOOP-OPT-007` (review #290 lượt 8) | §6 | FLOW-30 |
| Ca FLOW riêng cho giữ, thu hồi, baseline bị lái, bộ chấm bị sửa | §10 | FLOW-27/20/28/29 |

### Điểm đã chốt (D-356 chọn mọi đề xuất in đậm)

| # | Câu hỏi | Phương án | Dữ kiện | Đề xuất |
|---|---|---|---|---|
| 1 | Số ID FLOW | A: giữ nghĩa nghiên cứu §10 cho FLOW-20…23, ca mới từ FLOW-27 (24–26 giữ chỗ) · B: FLOW-20…23 = giữ/thu hồi/baseline/bộ chấm như PLAN T-3551, dời nghĩa cũ sang 27+ | §10 nghiên cứu và ADR-0052 §1 đã dùng FLOW-20…24 theo nghĩa A; Gate T-3552 chỉ nêu số | **A** (ID ổn định); Gate T-3552 thêm FLOW-27…34 |
| 2 | Candidate đo ở đâu | C1 tại chỗ · C2 worktree dựng lại | `.pth` bị ignore: C1 19 lệnh (bị lừa), C2 đúng; C2 +0,85 s | **C2** |
| 3 | Nguồn cấu hình | JSON ở đường khoá đọc từ gốc · khoá phẳng `xt.yaml` · cờ CLI lúc `start` | `xt.yaml` phẳng không chứa được danh sách chỉ số phụ; cờ CLI do agent chọn | **JSON từ gốc** |
| 4 | Kiểm "trỏ đúng cây" | `probe` dự án khai · quét `.pth` + symlink tìm đường cây agent · cả hai | `.pth` editable ghi đường tuyệt đối; npm tạo symlink tương đối | **cả hai** (quét bắt buộc, rẻ) |
| 5 | `HEAD^{tree}` ≠ `kept_tree` lúc `start` | từ chối · đo thêm cây giữ (4 cây) | 4 cây: +0,8 s; nhưng commit lạ giữa hai lần thử được tính công cho candidate | **từ chối**; vòng mới (`--base` mới) là lối ra |
| 6 | Nguồn held-out | hạt giống lúc finish · file của chủ dự án ngoài repo · file khoá trong repo | file trong repo agent đọc được; hạt giống lúc finish bắt được đường tắt ở spike | **hạt giống lúc finish**, file ngoài repo là tuỳ chọn thêm |
| 7 | Ngưỡng held-out | `improved` so với `start_head` · `--no-regress` | shortcut ở spike ±4 lệnh → cả hai đều thu hồi; tối ưu thật đúng một dải input sẽ bị chặn bởi `improved` | **`improved`** (chặt hơn) |
| 8 | Falsifier trúng | thu hồi · chỉ ghi sổ | `optimization-loop.md` bước 5: "số nào thì bỏ" | **thu hồi** |
| 9 | PERF-LOG (file theo dõi) và luật cây sạch | miễn PERF-LOG khi diff chỉ nối thêm · dựng PERF-LOG từ sổ lúc mở PR (`perf trial log`) | thu hồi xong mà ghi PERF-LOG làm cây bẩn cho `start` kế | **miễn khi chỉ nối thêm**, kiểm phần cũ không đổi |
| 10 | Ngữ nghĩa `--resume` | R1 đo lại khi vân tay = `candidate_fp` · R2 luôn thu hồi + `incomplete` | crash không do candidate; R2 mất candidate tốt và chống thử trùng chặn thử lại | **R1**, rơi về R2 khi cây đã đổi |
| 11 | Neo công cụ chấm | tự `exec` blob gốc · Gate dùng `<(git show …)` · cả hai | spike: cả hai chạy được | **cả hai** |
| 12 | Sửa file khoá | thu hồi + `tampered`, exit 1, tính lượt · exit 2 để nguyên | để nguyên không giúp gì; không tính lượt thì lách được đếm | **thu hồi, tính lượt** |
| 13 | Khoá điểm nóng | đường file (+ `::SYM`), kiểm diff chạm · chữ tự do | chữ tự do đổi tên được để reset đếm | **đường file + kiểm** |
| 14 | Đo xen kẽ | luôn xen kẽ · theo khối nhưng bắt buộc `exact` | A/A: theo khối 18 % `improved` sai | **luôn xen kẽ** |

### Kế hoạch tách T-3552 (mỗi task một PR, ≤ ~150–300 dòng mã, test kèm)

| Task | Phạm vi | Gate |
|---|---|---|
| T-3680 | Corpus: FLOW-20…23, 27…34 vào `tests/test_flow.py` với `XFAIL` (tái hiện ghi rõ), không mã | `python3 -m unittest -q tests.test_flow` |
| T-3681 | Cấu hình từ gốc, sổ `perf-trial.json`/`perf-trials.jsonl` (khoá, `rev`), `start`/`status`, đếm ba lần, chống thử trùng; `tests/test_perf_trial.py` + `tests/shard-weights.json` | `XT_FLOW_STRICT=FLOW-22,FLOW-31 python3 -m unittest -q tests.test_perf_trial tests.test_flow` |
| T-3682 | Môi trường đo: worktree tạm, dựng candidate + phủ `locked`, `setup` gỡ biến môi trường, kiểm trỏ đúng cây, dọn | `XT_FLOW_STRICT=FLOW-32 python3 -m unittest -q tests.test_perf_trial tests.test_flow` |
| T-3683 | Đo xen kẽ, `kind: exact`, chỉ số phụ có trần, `env.python` của lệnh đo | `XT_FLOW_STRICT=FLOW-23 python3 -m unittest -q tests.test_perf_trial tests.test_flow` |
| T-3684 | `finish`: đóng băng, HEAD, bộ chấm bị sửa, tương đương, quyết, giữ/thu hồi + kiểm vân tay, sổ, PERF-LOG, `abort` | `XT_FLOW_STRICT=FLOW-20,FLOW-27,FLOW-28,FLOW-29,FLOW-33 python3 -m unittest -q tests.test_perf_trial tests.test_flow` |
| T-3685 | Held-out (hạt giống lúc finish) + falsifier | `XT_FLOW_STRICT=FLOW-30,FLOW-31 python3 -m unittest -q tests.test_perf_trial tests.test_flow` |
| T-3686 | `--resume`, crash giữa lượt, `finish` đồng thời, `exec` công cụ từ gốc | `XT_FLOW_STRICT=FLOW-21,FLOW-34 python3 -m unittest -q tests.test_perf_trial tests.test_flow` |
| T-3687 | Skill `/optimize` bước 3 + `optimization-loop.md` (vòng, bảng công cụ, giới hạn) gọi `perf trial`; CHANGELOG "Dự án đích" | `XT_FLOW_STRICT=FLOW-20,FLOW-21,FLOW-22,FLOW-23,FLOW-27,FLOW-28,FLOW-29,FLOW-30,FLOW-31,FLOW-32,FLOW-33,FLOW-34 python3 -m unittest -q tests.test_perf_trial tests.test_flow tests.test_docs_budget && python3 scripts/xt.py changelog-check` |

Gate của T-3552 đổi theo Điểm mở 1 (A: thêm FLOW-27…34 vào `XT_FLOW_STRICT`); T-3552 tick khi T-3687 xanh. Đổi hành vi dự
án đích → cắt bản sau T-3687 (CHANGELOG mục "Dự án đích").

### Hệ quả

- Tốt: giữ/thu hồi do máy quyết trên số đo xen kẽ ở cây ghim; bốn giới hạn của Gate mẫu còn lại đúng một (cùng uid can
  thiệp trong lúc đo); PERF-LOG và đếm ba lần thành sản phẩm của máy; agent không cần lệnh git vứt thay đổi ở pha harden.
- Xấu: mỗi lần thử thêm 3 × `setup` (spike 0,8 s/cây với uv cache ấm; dự án thật có thể hàng phút — chưa đo); thêm
  ước 1 000–1 500 dòng `scripts/` + test (ước theo kế hoạch tách, chưa đo; nhóm còn ~1 MiB, ADR-0050); stash tích mục (không tự `drop`); dự án phải viết
  file cấu hình và commit nó trước vòng; `exact` cần bộ đo in số.
- Trung tính: `perf sample`/`compare`/`guard` giữ nguyên cho dùng tay và Gate mẫu cũ.

## Đường lùi

Mỗi task một PR, đảo ngược được. `perf trial` là lệnh mới — gỡ skill khỏi nó thì `/optimize` quay về Gate mẫu
`perf-gate.sh` (không đổi ở ADR này). `finish --no-apply` (in quyết định và lệnh thu hồi, không làm) là lối tạm khi thu hồi
tự động gây hại (nghiên cứu §12 lát 3). Sổ `.autopilot/perf-trials.jsonl` chỉ nối, xoá file là về trạng thái chưa có vòng.
