# ADR-0071: `perf trial` — máy quản lý trọn một lần thử tối ưu (đo cùng lượt ở cây dựng lại, giữ/thu hồi, sổ bền) — lát 3 của ADR-0052

- **Trạng thái:** Đã chấp nhận (2026-11-05, phiên chính tự duyệt — D-356: nhận cả mười bốn đề xuất in đậm ở §Điểm đã chốt;
  chủ repo 2026-11-05 "làm hết đi"; sửa theo review #440 — D-360: baseline do máy tính, không lối ra `--base`, PERF-LOG dựng từ
  sổ, điểm nóng là danh sách file). Chưa triển khai — T-3700…T-3707 (PLAN-harden-2026-10-27-loops).
- **Ngày:** 2026-11-05.
- **Thực hiện:** [ADR-0052 §Quyết định 7](0052-loop-state-rev-progress-perf-v2-next-step.md#quyết-định) (D-203; ràng buộc đầu
  vào — bảng ở §Ràng buộc) và §3 (lần thử tối ưu không đi qua `loop record`), thêm `LOOP-OPT-007` (held-out) và `LOOP-OPT-004`
  (falsifier) theo review #290 lượt 8.
- **Liên quan:** ADR-0048 (skill `/optimize`), ADR-0009 (một phiên), ADR-0018 (guard), ADR-0050 (trần thư mục),
  [`optimization-loop.md`](../../framework/11-autonomous-loop/optimization-loop.md) (`LOOP-OPT-001`…`-005`/`-007`…`-011`).
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
  cây thì 4/4 trỏ đúng; tốn 0,80–0,84 s/cây (uv, cache ấm, máy rảnh).
- **File bị bỏ qua lừa đo tại chỗ:** `.pth` trong `.venv` của cây agent chèn mô-đun giả → 19 lệnh thay 2 400 022; `tree_fp`
  không đổi, `perf guard` exit 0. Candidate dựng lại ở worktree riêng với `--setup` mới thì không bị lừa (+0,85 s).
- **Thu hồi:** `git stash push --include-untracked -- . ':(exclude).autopilot'` khi `.autopilot/` bị ignore → exit 1, **tạo
  mục stash nhưng để nguyên candidate, đã `git add`**. Danh sách file tường minh → exit 0, vân tay về đúng lúc start.
  Stash không thu hồi file bị ignore và sửa trong submodule ("No local changes to save", exit 0, vân tay lệch).
- **Held-out sinh lúc finish** (hạt giống `os.urandom`, bộ sinh từ commit gốc) bắt đường tắt hard-code N của bộ đo: bộ đo
  −99,9997 % so với gốc (−99,9995 % so với `start_head`); held-out +4 lệnh so với `start_head` (không `improved`).
- **Review #440** tái hiện thêm: dựng candidate bằng `git diff | git apply` bỏ lặng đổi gitlink submodule (apply exit 0, cây
  vẫn bản cũ); `src/sitecustomize.py` ngoài glob khoá lách được test tương đương; PERF-LOG miễn ở `start` nhưng nằm trong
  danh sách thu hồi → lần thu hồi thứ hai kẹt.

## Yếu tố quyết định

Đúng và an toàn trước (không giữ nhầm, không mất sửa của người dùng, không thu hồi bằng lệnh phá huỷ, agent không chọn được
baseline/cấu hình/công cụ chấm) · giữ đường lùi (mỗi PR đảo ngược được, `perf compare`/`perf guard` cũ giữ nguyên) · stdlib
Python ≥ 3.11, không hard-code stack (`setup` và lệnh đo do dự án khai) · C901 ≤ 10, `mypy --strict`, coverage 100 % · không
nới cổng/trần, skill `/optimize` còn 8 B dư (đổi chữ, không nối) · không hứa chi phí chưa đo trên dự án thật.

## Các phương án đã cân nhắc

1. **Giữ Gate mẫu + skill tự hoàn tác** (hiện trạng) — bốn giới hạn đã ghi, đo theo khối, hoàn tác vướng guard pha harden.
2. **`perf trial` đo candidate tại chỗ** (cây agent) + kiểm file khoá — rẻ nhất; spike: file bị ignore lừa được, không công
   cụ nào thấy.
3. **`perf trial` dựng mọi cây đo ngoài cây agent** (gốc, `start_head`, candidate dựng từ tree object), `setup` từ gốc trong
   từng cây với môi trường allowlist, đo xen kẽ — +~0,85 s/cây ở spike.
4. **Runner/sandbox ngoài phiên** — chặn được cả can thiệp cùng uid; cần quyền/chi phí của chủ dự án, đối chiếu ADR-0009
   — ngoài phạm vi (ADR-0052 §8).

Đề xuất **phương án 3**.

## Quyết định

### 1. Baseline và cấu hình do máy chọn (D-360)

**Baseline:** `base_sha = git merge-base HEAD <nhánh mặc định>`; nhánh mặc định lấy từ máy chủ
(`git ls-remote --symref origin HEAD`), ngoại tuyến mới dùng đích của `refs/remotes/origin/HEAD` (D-361 — bản cục bộ agent đổi
được bằng `remote set-head`); không xác định được → exit 2 kèm cách đặt. Không cờ `--base`, không đọc `XT_PROGRESS_BASE`. **Vòng** = các lần thử cùng `base_sha`;
lần `start` đầu ghi `base_sha` và tên nhánh mặc định vào sổ, lần sau tính lại và so: nhánh mặc định đổi tên → exit 2;
merge-base đổi (đã merge nhánh mặc định vào) → vòng mới. `fetch` dời nhánh mặc định không đổi merge-base. Giả định nhánh
mặc định được bảo vệ (đổi qua PR có review); guard chặn ghi ref dưới `refs/remotes/` (T-3563) — `remote set-head` T-3701 kiểm,
chưa bị chặn thì thêm luật guard kèm test (D-361). Dự án không có nhánh bảo vệ → đường lùi của D-360.

**Cấu hình:** JSON ở đường cố định `perf/trial.json`, đọc bằng `git cat-file blob <base_sha>:perf/trial.json` (không cờ
`--config`, không đọc cây agent): `schema`; `setup` (lệnh chạy trong mỗi cây); `probe` (tuỳ chọn, in đường mô-đun đã phân
giải); `locked` (glob bộ đo, test tương đương, input); `unlock` (gỡ khỏi khoá mặc định — đã qua review ở nhánh mặc định);
`metric` `{cmd, kind: wall|exact, unit, higher_is_better, runs}` (`exact` = số cuối stdout); `secondary[]` `{name, cmd, kind,
unit, higher_is_better, ceiling, regress}` (`ceiling` trần tuyệt đối, `regress` phần trăm lùi tối đa, mặc định 0); `target`
(mục tiêu số so với gốc, vd `primary <= -20%`, `LOOP-OPT-001`); `budget` (số lần thử tối đa mỗi vòng); `equiv`; `heldout`
`{gen, cmd}` (`gen` đọc hạt giống từ stdin, in danh sách input; `cmd` có `{input}`); `env` `{path, pass[], allow_prefix[]}`;
`scratch[]` (glob file lệnh đo được phép sinh, mặc định `**/__pycache__/**`); `timeout`. Thiếu file ở gốc → exit 2.

**Khoá mặc định** (máy thêm vào `locked`, cùng tinh thần file cổng của guard — `.claude/hooks/guard.py`
`GATE_FILE_PATTERNS`): chính file cấu hình, đường `xt.py` của khung; file khởi động trình chạy `**/sitecustomize.py`,
`**/usercustomize.py`, `**/*.pth`, `**/conftest.py`, `pytest.ini`, `tox.ini`, `setup.cfg`, `pyproject.toml`, `noxfile.py`,
`**/package.json`, `.npmrc`, `.yarnrc*`, `.pnpmfile.cjs`, `.python-version`, `.nvmrc`, `.tool-versions`, `.gitattributes`,
`.gitmodules` và lockfile (`*.lock`, `package-lock.json`, `pnpm-lock.yaml`). Đổi phụ thuộc/trình chạy không phải tối ưu thuần
(`LOOP-OPT-014`): PR riêng, hoặc gỡ bằng `unlock` ở nhánh mặc định.

### 2. Hợp đồng CLI

Mã thoát chung: **2** = máy từ chối **trước khi đụng cây agent** (cây agent không đổi; cây tạm có thể đã dựng rồi dọn);
**4** = đã thu hồi nhưng cây agent không về `fp_start` (in SHA stash và lối ra; không thử cách khác, `LOOP-STOP-025`).

| Lệnh | Việc | Exit |
|---|---|---|
| `perf trial start --hotspot PATH… --hypothesis TEXT --falsifier EXPR` | Tính `base_sha` (§1). Đòi: không có lần thử mở; cây sạch ngoài `.autopilot/` — không miễn file nào (`git status --porcelain --untracked-files=all --ignore-submodules=none`); `HEAD^{tree}` = cây của sự kiện `kept`/`log` gần nhất trong vòng, lần đầu vòng = cây `base_sha` (không ngoại lệ); file khoá không đổi `base_sha..HEAD`; mỗi `PATH` là đường file chuẩn hoá (có ở gốc hoặc chưa có ở `HEAD`), không khớp khoá; còn `budget`. Ghi `start_head`, `fp_start`, giả thuyết, falsifier, điểm nóng vào state và dòng `start` vào sổ | 0 · 2 từ chối, không ghi gì · 3 một đường điểm nóng đã cạn (§8) hoặc hết `budget` |
| `perf trial prepare` | Dựng ba cây cho lần thử đang mở, chạy `setup`, kiểm trỏ đúng cây (§4 bước 3), in kết quả, dọn; không đổi phase — để dự án thử cấu hình trước vòng | 0 · 2 |
| `perf trial finish [--resume] [--no-apply] [--json]` | Đóng băng, kiểm, đo, quyết, giữ hoặc thu hồi, ghi sổ (§4); `--no-apply` chỉ in quyết định và lệnh thu hồi | 0 giữ · 1 thu hồi xong (vân tay = `fp_start`) · 2 · 4 |
| `perf trial status [--json] [--check]` | Pha, lần thử mở, đếm theo đường, lệnh kế (`finish`/`finish --resume`/`abort`). `--check` = Gate của task tối ưu: lần giữ gần nhất của vòng đạt `target` so với gốc và không có lần thử mở | 0 · 1 `--check` chưa đạt · 2 state/sổ hỏng · 3 `--check` chưa đạt và mọi đường đã khai cạn hoặc hết `budget` (→ `loop defer`) |
| `perf trial abort --reason TEXT` | Lấy `perf-trial.lock`; thu hồi như `finish` thu hồi, ghi `aborted` (tính vào 3 lần) | 0 · 2 không có lần thử, `HEAD ≠ start_head`, không lấy được khoá · 4 |
| `perf trial log [--check]` | Dựng khối PERF-LOG của vòng (mốc `base_sha`) từ dòng `decide` của sổ, thay đúng khối đó trong `docs/autopilot/PERF-LOG.md`, phần còn lại giữ nguyên byte; ghi sự kiện `log` với cây = `HEAD^{tree}` + PERF-LOG mới (index tạm) — `start` kế đòi cây này sau khi commit. `--check`: so file với bản dựng | 0 · 1 `--check` lệch · 2 có lần thử mở, cây bẩn |

`finish`/`abort`/`start` không phải Gate và không đi qua `loop record` (ADR-0052 §3): thu hồi là kết quả bình thường, không
phải lần đỏ của task. Gate của task tối ưu là `perf trial status --check` (§5).

### 3. Sổ máy (trong `.autopilot/`, ghi bởi `xt.py`, guard chặn ghi tay)

- `perf-trial.json` — lần thử đang mở: `id` (`PT-NNNN`), `base_sha`, `default_ref`, `config_sha` (blob ở gốc), `tool_sha`,
  `hotspot[]`, `hypothesis`, `falsifier`, `start_head`, `fp_start`, `phase` (`started` → `measuring` → `decided` → `closed`),
  `candidate_fp`, `candidate_files[]`, `candidate_tree`, `rounds`, `resumes`, `stash` (SHA commit stash), `verdict`, `rev`.
  **Không** chứa hạt giống held-out (§6). Ghi qua khoá `flock` + `rev` như `update_state` (ADR-0052 §2); khoá riêng
  `perf-trial.lock` giữ suốt `finish` và `abort` (một người đo/thu hồi).
- `perf-trials.jsonl` — chỉ nối, mỗi sự kiện một dòng (`start`, `decide`, `log`), `fsync`; nguồn của đếm ba lần, chống thử
  trùng (khoá `hotspot` + `candidate_tree`) và của PERF-LOG. Bền qua restart vì là file, không phải bộ nhớ phiên. Tên trường
  (D-363, T-3701): mọi dòng có `event` (`start`|`decide`|`log`), `schema: 1`, `base_sha`, `at`; `start` thêm `id`,
  `default_ref`, `config_sha`, `tool_sha`, `hotspot[]`, `hypothesis`, `falsifier`, `start_head`, `fp_start`; `decide` thêm
  `id`, `hotspot[]`, `verdict`, `reason` (lý do — chữ hoặc JSON), `candidate_files[]`, `rounds` (`kept` bắt buộc
  `candidate_tree`); `log` thêm `tree`. Dòng hỏng (kể cả dòng cuối thiếu xuống dòng) → mọi lệnh exit 2, không đoán.
  `setup` của cấu hình là **một chuỗi lệnh shell**.

### 4. Máy trạng thái của `finish`

1. **Kiểm và đóng băng:** lấy `perf-trial.lock` (không được → exit 2, FLOW-34). Kiểm lại trường do `start` ghi: `base_sha`
   = merge-base tính lại, `config_sha`/`tool_sha` = blob ở gốc, dòng `start` trong sổ trùng state, `HEAD == start_head`
   (khác → exit 2, FLOW-28), `start_head^{tree}` = cây giữ gần nhất; lệch → exit 2. `candidate_files` = `git status
   --porcelain=v1 -z --untracked-files=all --no-renames --ignore-submodules=none` trừ `.autopilot/` (đổi tên = xoá + thêm, cả
   hai đường); rỗng → `verdict: empty`, đóng, exit 1. `candidate_tree` = index tạm (`GIT_INDEX_FILE`) `read-tree start_head` + `add -A
   -- <candidate_files>` + `write-tree`; `candidate_fp = tree_fingerprint`; trùng khoá đã thử → exit 2 (lối ra `abort`).
   Phase `measuring`, `rounds += 1`.
2. **Bộ chấm, điểm nóng:** `git diff --name-only --no-renames --no-ext-diff --no-textconv base_sha start_head` khớp `locked`
   → thu hồi, `verdict: tampered` (`start` đã chặn, đây là kiểm lại). `candidate_files` khớp `locked` → thu hồi, `tampered`
   (FLOW-29, điểm 12). Có file ngoài danh sách điểm nóng → thu hồi, `off-hotspot` (§8).
3. **Dựng cây** (thư mục tạm quyền 0700 ngoài cây agent): `git clone --shared --no-checkout` của repo agent (không đăng ký
   worktree trong `.git` của cây agent, nên `git worktree list` của cây agent không lộ cây đo; T-3702 đo 2026-11-05 trên repo
   khung 581 file, 7 lần, git 2.53: `clone --shared --no-checkout` + `checkout --detach` trung vị 0,065 s, `worktree add
   --detach` 0,059 s — giữ `clone --shared`; hook của clone tắt bằng `core.hooksPath=/dev/null`), checkout `base_sha`,
   `start_head` và `commit-tree <candidate_tree> -p
   start_head` (commit treo, không ref). Đòi `HEAD^{tree}` của từng cây = cây mong đợi; với candidate, mỗi file trong
   `candidate_files` trùng byte và mode với cây agent, gitlink submodule = `HEAD` của submodule ở cây agent và submodule không
   bẩn — lệch → thu hồi, `verdict: unbuildable` (submodule bẩn: FLOW-33). Không dựng bằng patch: `git apply` bỏ lặng đổi
   gitlink, `git diff` theo driver ngoài/textconv. Rồi `setup` của cấu hình gốc (`/bin/sh -c`, T-3702) chạy trong từng cây với **môi trường
   allowlist**: chỉ `HOME`, `LANG`, `LC_ALL`, `TZ`, `TERM` và `env.pass[]`; `TMPDIR` riêng từng cây; `PATH` = bin của chính
   cây (`.venv/bin`, `node_modules/.bin`) rồi `env.path` (mặc định `/usr/local/bin:/usr/bin:/bin`). Mọi biến khác (`NODE_OPTIONS`,
   `BASH_ENV`, `ENV`, `LD_PRELOAD`, `PYTHON*`, `VIRTUAL_ENV`, `NODE_PATH`, `PIP_*`, `UV_*`, `npm_config_*`…) bị bỏ. Mục `PATH`
   ghi được bởi uid hiện tại (vd `~/.local/bin`) → ⚠ vào sổ. **Kiểm trỏ đúng cây** (điểm 4): `probe` + quét `.pth`, symlink,
   `direct_url.json` editable, phụ thuộc `file:`/`link:` của manifest — đường phân giải ra ngoài cây đo và ngoài
   `sys.base_prefix` của interpreter cây/`env.allow_prefix[]` → exit 2 trước khi đo (FLOW-32). Chụp danh sách **đầy đủ** file
   mỗi cây (cả file bị ignore, trừ `.git`): đường, cỡ, mode, `mtime_ns`, sha256 (file ≤ 1 MiB ngoài `scratch`).
4. **Đo cùng lượt, xen kẽ:** chỉ số chính ở ba cây, vòng tròn đổi thứ tự (B K C, K C B, C B K…), `runs` mỗi cây; `exact` chạy
   ≥ 3 lần và đòi trùng nhau (lệch → `insufficient`); chỉ số phụ cùng lượt. Lệnh đo, `equiv`, held-out chạy với `HOME`,
   `XDG_*_HOME`, `TMPDIR` là thư mục tạm riêng từng cây, mới mỗi lượt (`setup` dùng `HOME` thật cho cache gói) — cache đĩa
   ngoài cây giữa các lần chạy không đi qua đường này. Mẫu ghi theo v2 (ADR-0052 §4), thêm `kind` và **trường mới**
   `env.cmd_python` (interpreter của lệnh đo; `env.python` giữ nghĩa cũ). Sau lượt so lại danh sách file của ba cây: khác
   ngoài `scratch` ở gốc/`start_head` → exit 2 (FLOW-28); ở candidate → thu hồi, `tampered`.
5. **Tương đương:** `equiv` exit 0 trên cây candidate (và trên cây gốc — đỏ ở gốc = cấu hình hỏng, exit 2).
6. **Held-out:** §6.
7. **Quyết:** giữ ⇔ (4) chỉ số chính `improved` so với gốc **và** so với `start_head` · (5) xanh · (6) đạt · mọi chỉ số phụ
   ≤ `ceiling` và không `regressed` quá `regress` so với `start_head` lẫn gốc (FLOW-44) · falsifier không trúng. Còn lại thu
   hồi, lý do đầu tiên vào `verdict`. Ghi ngay dòng `decide` (verdict, lý do, số gốc/`start_head`/candidate, held-out kèm hạt
   giống, phụ, `rounds`, `candidate_tree`, các ⚠ của heuristic `perf guard` trên diff `start_head`→candidate, ⚠ `PATH`) vào
   sổ; phase `decided`.
8. **Hành động:** giữ → để candidate trong cây, `kept_tree = candidate_tree` (spike: bằng `HEAD^{tree}` sau commit). Thu hồi →
   `git stash push --include-untracked -m "xt-perf-trial <id>" -- <candidate_files>` rồi đòi `tree_fingerprint == fp_start`;
   lệch (vd submodule) → phase giữ `decided`, exit 4, in SHA stash (FLOW-33). Không `checkout -- .`/`reset --hard`/`clean`;
   không `stash drop` (guard hỏi).
9. **Đóng:** dọn cây tạm, phase `closed`. `finish` không ghi PERF-LOG và không đụng file theo dõi nào ngoài thu hồi (D-360).

### 5. Công cụ chấm và Gate từ commit gốc

**Mọi** lệnh `perf trial` (cả `start`/`status`/`prepare`/`log`) tính `base_sha` rồi so sha256 của chính file với blob
`git cat-file blob <base_sha>:<đường xt.py>`; khác → xuất blob ra thư mục tạm và `exec python3 -I <tạm>/xt.py perf trial …`
(spike: `xt.py` một file, chạy được qua blob). Gate của task tối ưu trong PLAN-opt: ``python3 -I <(git cat-file blob
"$(git merge-base HEAD origin/HEAD)":<đường xt.py>) perf trial status --check`` — đầu vào không lấy từ cây candidate;
`--check` đọc số từ dòng `decide`, không đo lại. Can thiệp cùng uid trong lúc đo vẫn là giới hạn đã biết (§Hệ quả).

### 6. Held-out (`LOOP-OPT-007`)

Input held-out sinh **sau khi** candidate đóng băng, mỗi lượt đo (cả `--resume`) một hạt giống 64 bit `os.urandom` mới, chỉ
giữ trong bộ nhớ tiến trình `finish` và truyền qua stdin của `heldout.gen` (gốc) chạy ở cây gốc; ghi vào sổ ở dòng `decide`
sau khi đo xong. Agent không thấy input trước khi viết candidate; tiến trình cùng uid đọc được bộ nhớ/stdin trong lúc đo
(giới hạn đã biết). Quy tắc: **gộp** — tổng đại lượng trên mọi input (`exact`: tổng, mỗi input ≥ 3 lần trùng; `wall`: tổng
mỗi vòng xen kẽ, `runs` vòng) phải `improved` so với `start_head` **và** so với gốc (D-360); **từng input** — không
`regressed` so với `start_head`; đầu ra bằng gốc khi `heldout.cmd` in đầu ra. Không khai `heldout` → cảnh báo, dòng `decide`
ghi `LOOP-OPT-007` "không áp dụng".

### 7. Giả thuyết và falsifier (`LOOP-OPT-004`)

`start` bắt buộc `--hypothesis` và `--falsifier`, trên cây sạch — thứ tự "ghi trước khi sửa" do máy chứng minh (`fp_start`
là cây không có candidate). Falsifier dạng `<chỉ số> <op> <phần trăm>` so với `start_head` (vd `primary > -5%`: đổi tệ hơn
−5 % là bác bỏ). Máy đánh giá ở bước 7; trúng → thu hồi (điểm 8). Giả thuyết/falsifier không sửa được sau `start`.

### 8. Ba lần không giữ mỗi điểm nóng (`LOOP-OPT-011`, D-360)

Điểm nóng là **danh sách đường file chuẩn hoá** (không `::SYM`, không thư mục). Đếm từ `perf-trials.jsonl` **theo từng
đường**: lần thử có `verdict` ≠ `kept` (kể cả `aborted`, `tampered`, `off-hotspot`, `incomplete`, `unbuildable`) cộng 1 cho
**mọi** đường đã khai; lần `kept` đặt về 0 **chỉ** các đường candidate thật sự đổi. `start` exit 3 khi **bất kỳ** đường đã
khai có chuỗi ≥ 3 — khai kèm đường mới ("mồi") không mở lại đường đã cạn. `finish` đòi mọi file trong `candidate_files` thuộc
danh sách (không thì thu hồi, `verdict: off-hotspot`).

### 9. Resume, abort, đồng thời

`finish` khi phase `measuring`/`decided` → exit 2 "chạy `finish --resume`". `--resume` (lấy khoá): `measuring` + vân tay cây =
`candidate_fp` + `resumes == 0` → `resumes = 1`, đo lại từ đầu (bỏ mọi số dở, hạt giống mới), quyết một lần (FLOW-35); vân
tay khác **hoặc** đã resume một lần → thu hồi, `verdict: incomplete` (FLOW-21); `decided` → làm nốt bước 8–9, không ghi
`decide` trùng (FLOW-36). Mỗi lượt đo tăng `rounds` (ghi vào `decide` và PERF-LOG) — đo lại tới khi may không làm được quá
một lần. Cây tạm mất sau reboot → dựng lại. Hai `finish` (hay `finish` và `abort`) cùng lúc: `perf-trial.lock` không lấy
được → exit 2 ngay.

### 10. Ca FLOW

ID FLOW-20…23 giữ nghĩa nghiên cứu §10; FLOW-27…34 giữ nghĩa bản ADR trước review #440; ca review #440 cần thêm là FLOW-35…45.

| ID | Given / When | Then |
|---|---|---|
| FLOW-20 | candidate `neutral` → `finish` | thu hồi đúng `candidate_files`, `.autopilot/` và file người dùng ngoài danh sách còn nguyên, vân tay = `fp_start`, `perf trial log` có dòng bỏ — **đường thu hồi** |
| FLOW-21 | crash trước thu hồi (vân tay đã đổi hoặc đã resume một lần) → `finish --resume` | không thử trùng (một dòng `decide`), cây = `fp_start`, `verdict: incomplete` |
| FLOW-22 | 3 lần không giữ cùng điểm nóng, restart giữa chừng | `start` exit 3 |
| FLOW-23 | chỉ số chính `improved`, phụ vượt trần | thu hồi, exit 1 |
| FLOW-24…26 | (giữ chỗ nghiên cứu §10: field, steward — không dùng ở ADR này) | |
| FLOW-27 | candidate `improved` so với gốc và `start_head`, test + held-out xanh | exit 0, `kept_tree` = cây sau commit, `start` kế nhận — **đường giữ** |
| FLOW-28 | commit giữa chừng / dời `origin/main` sau ghim / sửa worktree gốc trong lượt | exit 2 không đụng cây / base không đổi / exit 2 — **baseline bị lái** |
| FLOW-29 | candidate sửa file khoá / `.pth` bị ignore trong `.venv` cây agent | `tampered`, thu hồi / số đo không đổi vì đo ở cây dựng lại — **bộ chấm bị sửa** |
| FLOW-30 | candidate hard-code input của bộ đo | held-out không `improved` → thu hồi |
| FLOW-31 | `start` thiếu giả thuyết/falsifier hoặc cây bẩn; falsifier trúng | exit 2; thu hồi |
| FLOW-32 | `setup` để mô-đun phân giải ra ngoài cây đo | exit 2 trước khi đo |
| FLOW-33 | candidate sửa nội dung submodule | stash không đưa về `fp_start` → exit 4, in SHA stash, không thử cách khác |
| FLOW-34 | hai `finish` đồng thời (barrier) | một đo, một exit 2 |
| FLOW-35 | kill giữa lượt đo, cây = `candidate_fp` → `finish --resume` | đo lại một lần, hạt giống khác lượt đầu, một dòng `decide` có `rounds: 2` |
| FLOW-36 | kill sau quyết, trước thu hồi (phase `decided`) → `finish --resume` | làm nốt thu hồi, cây = `fp_start`, không ghi `decide` trùng |
| FLOW-37 | `start` khi: cây chỉ bẩn ở `PERF-LOG.md`; commit lạ sau lần giữ (`HEAD^{tree}` ≠ cây giữ); lần đầu vòng mà `HEAD^{tree}` ≠ cây gốc; file khoá đổi `base..HEAD`; có cờ `--base` | exit 2, sổ và cây không đổi |
| FLOW-38 | commit cấu hình nới (`locked: []`, `equiv: "true"`) trên nhánh rồi `start`; merge nhánh mặc định vào nhánh | cấu hình đọc từ `base_sha` (bản chưa nới); vòng mới đòi cây gốc → exit 2 |
| FLOW-39 | đường A cạn (3 lần `abort`) → `start --hotspot A --hotspot B` | exit 3 |
| FLOW-40 | hai lần thu hồi liên tiếp (`abort`) → `perf trial log`, commit → `start` | `log` có cả hai dòng; `start` kế exit 0 (không kẹt vì PERF-LOG) |
| FLOW-41 | khai A, B; lần giữ chỉ đổi B / candidate đổi file C ngoài danh sách | đếm của A không về 0 / `off-hotspot`, thu hồi |
| FLOW-42 | phiên agent có `NODE_OPTIONS`, `LD_PRELOAD`, `PYTHONPATH`, `BASH_ENV` → `perf trial prepare` | `setup` và `probe` không thấy các biến đó |
| FLOW-43 | candidate đổi gitlink submodule (đã commit trong submodule) / đổi tên file / repo có `diff.external` | cây candidate có gitlink mới / `candidate_files` có cả hai đường / cây candidate trùng cây agent |
| FLOW-44 | chỉ số chính `improved`, bộ nhớ +40 % dưới trần, `regress` 0 | thu hồi, exit 1 |
| FLOW-45 | thu hồi rồi giữ một lần chưa đạt `target`, rồi giữ đạt | không dòng `loop record` nào cho task; `status --check` exit 1, rồi 0 |

### Ràng buộc ADR-0052 §7 (và §3) → cách đáp ứng

| Ràng buộc | Cách đáp ứng | Bằng chứng/ca |
|---|---|---|
| Baseline ghim một lần cho cả vòng, không `XT_PROGRESS_BASE`, không theo HEAD agent chọn | `base_sha` = merge-base với nhánh mặc định do máy tính, ghi sổ ở `start` đầu; không cờ `--base`, không biến môi trường; vòng mới chỉ khi merge-base đổi và khi đó đòi cây gốc (D-360) | spike: dời ref sau ghim, SHA không đổi · FLOW-28, FLOW-37, FLOW-38 |
| Candidate = phần chưa commit trên `start_head`; `finish` đòi `HEAD == start_head` | §4 bước 1 | FLOW-28 |
| Máy tự đo gốc/`start_head`/candidate cùng lượt, cùng môi trường | §4 bước 3 + 4: ba cây dựng từ object, đo xen kẽ | A/A 18 % → 0 % · FLOW-43 |
| `--setup` ghim từ gốc; editable/`node_modules`/submodule không trỏ về cây candidate | `setup` từ cấu hình gốc, chạy trong từng cây, môi trường allowlist, kiểm trỏ đúng cây, danh sách file đầy đủ trước/sau lượt | spike §2: hiểm hoạ tái hiện, 4/4 đúng sau setup · FLOW-32, FLOW-42 |
| Lệnh đo, glob bộ đo, test tương đương, chính `xt.py` từ gốc (`LOOP-OPT-002`/`-003`) | §1 cấu hình từ blob gốc ở đường cố định, khoá mặc định file khởi động trình chạy; §4 bước 2 kiểm `base..start_head` và candidate; §5 mọi lệnh `exec` blob gốc | FLOW-29, FLOW-38 |
| Đại lượng tất định và chỉ số phụ (`-008`/`-009`) | `metric.kind: exact` (đòi trùng ≥ 3 lần), `secondary[]` có trần và mức lùi | spike: 3/3 trùng · FLOW-23, FLOW-44 |
| Giữ chỉ khi `improved` so với cả giữ gần nhất và gốc, kèm test tương đương xanh | §4 bước 7 + §6 held-out so cả hai (`start_head` = cây giữ gần nhất nhờ luật `start`) | FLOW-27, FLOW-30 |
| Thu hồi đúng file bằng `git stash push --include-untracked`, kiểm vân tay lúc start | §4 bước 8, danh sách file tường minh (pathspec loại trừ hỏng — spike V1), `--no-renames` | FLOW-20, FLOW-33, FLOW-43 |
| PERF-LOG ghi sau quyết định | `perf trial log` dựng từ dòng `decide` của sổ; `start`/`finish` không ghi cây (D-360) | FLOW-20, FLOW-40 |
| `start` đòi cây sạch ngoài `.autopilot/` và `start_head` có tree = cây giữ gần nhất (hoặc đo luôn cây đó) | §2 `start`: cây giữ gần nhất, lần đầu vòng = cây gốc, không ngoại lệ, không miễn PERF-LOG (D-360) | FLOW-37 |
| Ghi giả thuyết trước khi sửa (`LOOP-OPT-004`) + falsifier | §7 | FLOW-31 |
| Ba lần không `improved` mỗi điểm nóng bền qua restart (`LOOP-OPT-011`) | §8 theo từng đường từ `perf-trials.jsonl` | FLOW-22, FLOW-39, FLOW-41 |
| `--resume` sau crash | §9: tối đa một lần, hạt giống mới, `rounds` ghi sổ | FLOW-21, FLOW-35, FLOW-36 |
| Chỉ số phụ vượt trần → đỏ | §4 bước 7 | FLOW-23, FLOW-44 |
| Held-out `LOOP-OPT-007` (review #290 lượt 8) | §6 | FLOW-30 |
| Ca FLOW riêng cho giữ, thu hồi, baseline bị lái, bộ chấm bị sửa | §10 | FLOW-27/20/28/29 |
| (§3) Lần thử tối ưu không đi qua `loop record` của task | §2: `finish`/`abort` không phải Gate; Gate = `status --check` theo `target` | FLOW-45 |

### Điểm đã chốt (D-356 chọn mọi đề xuất in đậm; D-360 và review #440 đổi các điểm ghi chú)

| # | Câu hỏi | Phương án | Dữ kiện | Đề xuất |
|---|---|---|---|---|
| 1 | Số ID FLOW | A: giữ nghĩa nghiên cứu §10 cho FLOW-20…23, ca mới từ FLOW-27 (24–26 giữ chỗ) · B: FLOW-20…23 = giữ/thu hồi/baseline/bộ chấm như PLAN T-3551, dời nghĩa cũ sang 27+ | §10 nghiên cứu và ADR-0052 §1 đã dùng FLOW-20…24 theo nghĩa A; Gate T-3552 chỉ nêu số | **A** (ID ổn định); Gate T-3552 thêm FLOW-27…45 (review #440: FLOW-21 về nghĩa nghiên cứu, thêm 35…45) |
| 2 | Candidate đo ở đâu | C1 tại chỗ · C2 cây dựng lại | `.pth` bị ignore: C1 19 lệnh (bị lừa), C2 đúng; C2 +0,85 s | **C2**, dựng từ tree object, không từ patch (review #440) |
| 3 | Nguồn cấu hình | JSON ở đường khoá đọc từ gốc · khoá phẳng `xt.yaml` · cờ CLI lúc `start` | `xt.yaml` phẳng không chứa được danh sách chỉ số phụ; cờ CLI do agent chọn | **JSON từ gốc** ở đường cố định, không `--config`/`--budget` (review #440) |
| 4 | Kiểm "trỏ đúng cây" | `probe` dự án khai · quét `.pth` + symlink tìm đường cây agent · cả hai | `.pth` editable ghi đường tuyệt đối; npm tạo symlink tương đối | **cả hai** (quét bắt buộc, rẻ), thêm manifest `file:` và môi trường allowlist (review #440) |
| 5 | `HEAD^{tree}` ≠ `kept_tree` lúc `start` | từ chối · đo thêm cây giữ (4 cây) | 4 cây: +0,8 s; nhưng commit lạ giữa hai lần thử được tính công cho candidate | **từ chối**, không lối ra `--base` — **D-360 bỏ** "vòng mới (`--base` mới)"; vòng mới chỉ khi merge-base đổi (§1) |
| 6 | Nguồn held-out | hạt giống lúc finish · file của chủ dự án ngoài repo · file khoá trong repo | file trong repo agent đọc được; hạt giống lúc finish bắt được đường tắt ở spike | **hạt giống lúc finish**, mới mỗi lượt đo, không ghi state trước khi đo xong (review #440); file ngoài repo là tuỳ chọn thêm |
| 7 | Ngưỡng held-out | `improved` so với `start_head` · `--no-regress` | đường tắt ở spike +4 lệnh → cả hai đều thu hồi; tối ưu thật đúng một dải input sẽ bị chặn bởi `improved` | **`improved`** (chặt hơn), so cả `start_head` lẫn gốc (D-360) |
| 8 | Falsifier trúng | thu hồi · chỉ ghi sổ | `optimization-loop.md` bước 5: "số nào thì bỏ" | **thu hồi** |
| 9 | PERF-LOG (file theo dõi) và luật cây sạch | miễn PERF-LOG khi diff chỉ nối thêm · dựng PERF-LOG từ sổ (`perf trial log`) | miễn ở `start` nhưng PERF-LOG vẫn vào `candidate_files`/vân tay → lần thu hồi thứ hai kẹt (review #440 chạy thật) | **D-360 đổi:** dựng từ sổ bằng `perf trial log`; `start`/`finish` không ghi cây; không miễn |
| 10 | Ngữ nghĩa `--resume` | R1 đo lại khi vân tay = `candidate_fp` · R2 luôn thu hồi + `incomplete` | crash không do candidate; R2 mất candidate tốt và chống thử trùng chặn thử lại | **R1** tối đa một lần, hạt giống mới, tính `rounds` (review #440); rơi về R2 khi cây đã đổi hoặc resume lần hai |
| 11 | Neo công cụ chấm | tự `exec` blob gốc · Gate dùng `<(git cat-file blob …)` · cả hai | spike: cả hai chạy được | **cả hai**, mọi lệnh con (review #440) |
| 12 | Sửa file khoá | thu hồi + `tampered`, exit 1, tính lượt · exit 2 để nguyên | để nguyên không giúp gì; không tính lượt thì lách được đếm | **thu hồi, tính lượt** |
| 13 | Khoá điểm nóng | đường file (+ `::SYM`), kiểm diff chạm · chữ tự do | chữ tự do đổi tên được để reset đếm; khai thêm đường "mồi" rồi giữ đặt lại cả đường đã cạn (review #440) | **D-360 đổi:** danh sách đường file, đếm theo từng đường, giữ chỉ đặt lại đường đã đổi, mọi file candidate thuộc danh sách |
| 14 | Đo xen kẽ | luôn xen kẽ · theo khối nhưng bắt buộc `exact` | A/A: theo khối 18 % `improved` sai | **luôn xen kẽ** |

### Kế hoạch tách T-3552

Mỗi task ≤ ~150–300 dòng mã, test kèm, một commit; D-357/D-360: bốn PR, mỗi PR hai task liền kề (3700+3701, 3702+3703,
3704+3705, 3706+3707). Gate mỗi task **đỏ trước khi làm** (ID STRICT còn trong `XFAIL`, hoặc kiểm ID tồn tại) và chỉ cần mã
của chính task đó và task trước. Số T-3700…T-3707 thay T-3680…T-3687 của bản trước (trùng ID nhánh khác — review #440).

| Task | Phạm vi | Gate |
|---|---|---|
| T-3700 | Corpus: FLOW-20…23, 27…45 vào `tests/test_flow.py` với `XFAIL` (tái hiện ghi rõ), không mã | `python3 -m unittest -q tests.test_flow && python3 -c "import sys; sys.path[:0] = ['tests', 'scripts']; import test_flow as t; s = {'FLOW-%d' % n for n in [20, 21, 22, 23, *range(27, 46)]}; sys.exit(bool(s - t.FLOW_IDS or s - t.XFAIL.keys()))"` |
| T-3701 | Cấu hình gốc + khoá mặc định, `base_sha` merge-base, sổ (khoá, `rev`), `start`/`status`/`abort` (thu hồi stash + vân tay, exit 4), đếm theo đường, `budget`, `log`; `tests/test_perf_trial.py` + `tests/shard-weights.json` | `XT_FLOW_STRICT=FLOW-22,FLOW-37,FLOW-38,FLOW-39,FLOW-40 python3 -m unittest -q tests.test_perf_trial tests.test_flow` |
| T-3702 | Môi trường đo: cây tạm dựng từ tree object, `setup` allowlist, kiểm trỏ đúng cây, danh sách file đầy đủ, dọn; `prepare` | `XT_FLOW_STRICT=FLOW-32,FLOW-42,FLOW-43 python3 -m unittest -q tests.test_perf_trial tests.test_flow` |
| T-3703 | `finish` lõi: kiểm trường, đóng băng, khoá/điểm nóng, đo xen kẽ chỉ số chính (`wall`/`exact`), kiểm cây sau lượt, tương đương, quyết, giữ/thu hồi + vân tay, dòng `decide`, `perf-trial.lock` | `XT_FLOW_STRICT=FLOW-20,FLOW-28,FLOW-29,FLOW-33,FLOW-41 python3 -m unittest -q tests.test_perf_trial tests.test_flow` |
| T-3704 | Chỉ số phụ (trần + mức lùi), `env.cmd_python`, ⚠ heuristic vào `decide`, `target` + `status --check` | `XT_FLOW_STRICT=FLOW-23,FLOW-44,FLOW-45 python3 -m unittest -q tests.test_perf_trial tests.test_flow` |
| T-3705 | Held-out (hạt giống mỗi lượt, gộp + từng input, so `start_head` và gốc) + falsifier | `XT_FLOW_STRICT=FLOW-27,FLOW-30,FLOW-31 python3 -m unittest -q tests.test_perf_trial tests.test_flow` |
| T-3706 | `--resume` (một lần, R2), crash giữa lượt, `finish`/`abort` đồng thời, `exec` công cụ từ blob gốc ở mọi lệnh con | `XT_FLOW_STRICT=FLOW-21,FLOW-34,FLOW-35,FLOW-36 python3 -m unittest -q tests.test_perf_trial tests.test_flow` |
| T-3707 | Skill `/optimize` bước 3 + `optimization-loop.md` (vòng, Gate mẫu → `status --check`, bảng công cụ, giới hạn, phần Kiểm của `LOOP-OPT-001`/`-002`/`-003`/`-007`/`-008`); CHANGELOG "Dự án đích" | `XT_FLOW_STRICT=FLOW-20,FLOW-21,FLOW-22,FLOW-23,FLOW-27,FLOW-28,FLOW-29,FLOW-30,FLOW-31,FLOW-32,FLOW-33,FLOW-34,FLOW-35,FLOW-36,FLOW-37,FLOW-38,FLOW-39,FLOW-40,FLOW-41,FLOW-42,FLOW-43,FLOW-44,FLOW-45 python3 -m unittest -q tests.test_perf_trial tests.test_flow tests.test_docs_budget && python3 scripts/xt.py changelog-check && git grep -q 'perf trial status --check' -- .claude/skills/optimize/SKILL.md && git grep -q 'perf trial status --check' -- framework/11-autonomous-loop/optimization-loop.md` |

Gate của T-3552 đổi theo điểm 1 (A: thêm FLOW-27…45 vào `XT_FLOW_STRICT`); T-3552 tick khi T-3707 xanh. Đổi hành vi dự
án đích → cắt bản sau T-3707 (CHANGELOG mục "Dự án đích").

### Hệ quả

- Tốt: giữ/thu hồi do máy quyết trên số đo xen kẽ ở cây dựng lại, baseline/cấu hình/công cụ chấm do máy lấy từ nhánh mặc
  định; PERF-LOG và đếm ba lần thành sản phẩm của máy; agent không cần lệnh git vứt thay đổi ở pha harden. Với bốn giới hạn
  của Gate mẫu: đóng (4) với cây agent (đo ở cây dựng lại, danh sách file đầy đủ so trước/sau lượt) và phần biến môi trường
  của (3) (allowlist); **còn** (1) tiến trình cùng uid can thiệp lúc đo (cây tạm, bộ nhớ/stdin của `finish`, ghi ra đường
  tuyệt đối ngoài cây), (2) kho git — object dùng chung qua `--shared`, config git toàn cục, và phần còn lại của (3) — cài
  Python/thư mục `PATH` ghi được bởi uid. Chỉ phương án 4 đóng được ba giới hạn này.
- Xấu: mỗi lần thử thêm 3 × `setup` (spike 0,8 s/cây với uv cache ấm, máy rảnh; dự án thật có thể hàng phút — chưa đo); thêm
  ước 1 000–1 500 dòng `scripts/` + test (ước theo kế hoạch tách, chưa đo; nhóm còn 715 223 B dưới trần, đo 2026-11-05,
  ADR-0050); stash tích mục (không tự `drop`); dự án phải viết `perf/trial.json`, commit nó vào nhánh mặc định trước vòng,
  và có nhánh mặc định được bảo vệ; `exact` cần bộ đo in số; khoá mặc định chặn đổi phụ thuộc trong lần thử.
- Trung tính: `perf sample`/`compare`/`guard` giữ nguyên cho dùng tay và Gate mẫu cũ.

## Đường lùi

Mỗi PR (hai task, D-357) đảo ngược được bằng revert commit squash của PR; trong PR, mỗi task một commit chỉ giúp đọc/bisect
(D-360). `perf trial` là lệnh mới — gỡ skill khỏi nó thì `/optimize` quay về Gate mẫu `perf-gate.sh` (không đổi ở ADR này).
`finish --no-apply` (in quyết định và lệnh thu hồi, không làm) là lối tạm khi thu hồi tự động gây hại (nghiên cứu §12 lát 3).
Sổ `.autopilot/perf-trials.jsonl` chỉ nối, xoá file là về trạng thái chưa có vòng. Dự án không có nhánh mặc định được bảo
vệ: D-360 phương án 2 (ghim lúc `loop init` của PLAN-opt).
