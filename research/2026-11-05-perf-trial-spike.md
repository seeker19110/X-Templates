---
title: Spike môi trường đo cho `perf trial` — worktree, cài editable, node_modules, submodule, thu hồi, gian lận (2026-11-05)
kind: research
updated: 2026-11-05
---

# Spike môi trường đo cho `perf trial` — nghiên cứu 2026-11-05 (T-3551)

> Đầu vào cho [ADR-0071](../docs/adr/0071-perf-trial.md) theo ràng buộc của
> [ADR-0052 §Quyết định 7](../docs/adr/0052-loop-state-rev-progress-perf-v2-next-step.md#quyết-định). Đo thật trên repo git
> tạm, không đụng repo khung; mọi lệnh, exit code và số giây trong `results.json` của
> [evidence/2026-11-05-perf-trial-spike/](evidence/2026-11-05-perf-trial-spike/) — chạy lại:
> `python3 spike.py <đường tới scripts/xt.py>` (dựng lại từ đầu, ~32 s). Số ở đây là **một máy, dự án đồ chơi**: đủ để chọn
> cơ chế, không đủ để hứa chi phí trên dự án thật (§5).

## 1. Máy và dự án mẫu

Máy: WSL2 Linux 6.18.33.1, i7-13800H, `nproc` 16, 16 GB · Python 3.14.4 (chạy `xt.py`) và 3.14.6 (uv tự tải cho venv) ·
git 2.53.0 · uv 0.12.9 (cache ấm sau lần chạy đầu) · node v24.21.0 · npm 10.9.8 · không có valgrind/Cachegrind.

Repo `proj`: gói Python `fastlib` (`pyproject.toml`, layout `src/`, cài `uv pip install -e .`), bộ đo `bench/run.py`,
test tương đương `tests/equiv/`, bộ sinh held-out `heldout/gen.py`, dự án Node `js/` phụ thuộc `jslib` qua `file:../jslib`
(`package-lock.json` đã commit, `npm ci --offline`), submodule `vendor/sub`, và `scripts/xt.py` = bản của `origin/main`
`739d02f`. Ba trạng thái: **B** (commit gốc — gọi `_step` thừa), **K** (`start_head` = lần giữ trước — bỏ lời gọi thừa),
**C** (candidate chưa commit trên K — nội tuyến `_step`, thêm một file chưa track). Đại lượng tất định = số lệnh bytecode
đếm bằng `sys.monitoring` (sự kiện `INSTRUCTION`), in ra stdout.

## 2. Môi trường đo: worktree, `--setup`, cây nào được đo

| Phép thử | Kết quả |
|---|---|
| `git worktree add --detach` (B, K) | exit 0, 0,006 s mỗi cây |
| `--setup` mỗi cây: `submodule update --init` · `uv venv` · `uv pip install -e .` · `npm ci --offline` | exit 0 cả 4 cây; 0,80–0,84 s/cây (editable 0,62 s, npm 0,15–0,19 s, submodule 0,02 s) |
| **Hiểm hoạ:** đo cây B bằng venv của cây agent (`proj/.venv/bin/python`) | `fastlib` nạp từ `proj/src` — **baseline đo mã candidate, không báo lỗi**. `.pth` editable ghi đường tuyệt đối `…/proj/src` |
| **Hiểm hoạ:** `node_modules` của cây B là symlink tới của cây agent | `jslib` phân giải về `…/proj/jslib` (cây candidate) |
| `node_modules/jslib` do npm tạo | symlink **tương đối** `../../jslib` → sau `npm ci` trong từng cây, phân giải đúng cây đó |
| Sau `--setup` riêng từng cây | `fastlib`/`jslib` phân giải trong chính cây (4/4); submodule ở commit = gitlink (4/4) |
| Candidate dựng lại ở worktree riêng (C2): `worktree add K` + `git diff --binary HEAD \| git apply` + chép file chưa track + `git checkout B -- bench tests/equiv heldout` + `--setup` | 0,85 s; diff `src/` trùng cây agent, có file mới |
| Công cụ chấm từ commit gốc: `git show B:scripts/xt.py > tool/xt.py` rồi `python3 -I tool/xt.py perf sample/compare/guard` | chạy được (xt.py một file, stdlib); `python3 -I <(git show B:scripts/xt.py) perf compare --help` exit 0 |
| `perf compare --base SHA` chạy với cwd ngoài repo | exit 2 "không phân giải được thành commit" — `--base` phân giải theo cwd |
| `env.python` trong mẫu | ghi bản Python chạy `xt.py` (3.14.4), **không** phải bản chạy bộ đo (3.14.6 trong venv) |

## 3. Số đo cùng lượt và nhiễu

| Đại lượng | B | K | C | So |
|---|---|---|---|---|
| Thời gian tường (trung vị 10 lần, `perf sample` của công cụ gốc) | 31,2 ms | 23,6 ms | 19,8 ms | B→C −36,6 %, K→C −16,4 % `improved` (p = 0,00018) |
| Số lệnh bytecode (3 lần mỗi cây) | 7 200 022 ×3 | 4 000 022 ×3 | 2 400 022 ×3 | tất định 3/3; B→C −66,7 %, K→C −40 % |
| `ru_maxrss` (KiB, 3 lần) | 20 940 ×3 | 20 940 ×3 | 20 940 ×3 | bộ đo đồ chơi không cấp phát — chưa thử trần chỉ số phụ thật |

Bốn cây × (2 + 10) lần chạy: 1,94 s; số lệnh 3 cây × 3 lần: 1,63 s. Số tất định chỉ có đường **mảng thô** vào
`perf compare --exact` → `improved` nhưng `unverified-manual: true` (ADR-0052 §4): `perf sample` không bắt stdout.

**A/A** (cùng cây, cùng lệnh; `aa.json`, 2 × 30 cặp, mỗi bên 10 lần sau 2 lần khởi động):

| Cách đo | `improved` sai | `regressed` sai | `neutral` | |Δ| lớn nhất |
|---|---|---|---|---|
| Theo khối (10 lần A rồi 10 lần B — như `perf sample` hai lượt) | **11/60 (18 %)** | 8/60 | 41/60 | 11,3 % |
| Xen kẽ (ABAB…, đổi thứ tự mỗi vòng) | 0/60 | 1/60 | 59/60 | 8,0 % |

Lượt `spike.py` thứ hai cũng cho 2/3 cặp A/A theo khối `regressed` (+11,2 %, +7,8 %). Trên máy này, hai lượt đo theo khối
của **cùng mã** cho kết luận có ý nghĩa gần 1/3 số lần: đo xen kẽ hoặc đại lượng tất định là điều kiện, không phải tối ưu.

## 4. Gian lận và lái baseline — máy thấy gì

| Ca | Cách làm | Máy hiện có thấy? |
|---|---|---|
| Bộ chấm bị sửa (file theo dõi) | candidate sửa `bench/run.py` đo `n // 10` | `perf guard --locked 'bench/*'` exit 1; `perf compare` exit 2 lệch `harness_sha256` |
| Bộ chấm bị sửa (file bị bỏ qua) | `.pth` trong `.venv` của cây agent chèn `fastlib` giả từ `.cache/` | `tree_fp` **không đổi**, `perf guard` exit 0; đo tại chỗ: 19 lệnh (bị lừa); đo ở cây C2 setup mới: 2 400 022 (không bị lừa) |
| Đường tắt theo input | `work(n)` trả hằng khi `n == 200000` (N của bộ đo) | bộ đo: 19 lệnh (−99,9997 %); held-out 5 giá trị N sinh từ hạt giống `os.urandom` **lúc finish**, bộ sinh lấy từ B: bằng K ±4 lệnh → không `improved` so với K |
| Baseline bị lái (sửa worktree gốc giữa lượt) | ghi đè `src/` của cây B sau setup | mẫu ghi `dirty: true` → `perf compare` exit 2 "baseline đo trên cây bẩn" |
| Baseline bị lái (dời ref) | `update-ref refs/remotes/origin/main` sang K sau khi ghim | SHA đã ghim không đổi — chỉ an toàn nếu máy ghim **SHA**, không đọc lại ref |
| Baseline bị lái (commit giữa chừng) | commit candidate | `HEAD ≠ start_head` — phát hiện được bằng một lệnh `rev-parse` |
| Held-out: tương đương | đầu ra 5 N trên B/K/C | bằng nhau (3 cây) |

## 5. Thu hồi bằng `git stash push --include-untracked`

`stash-variants.json` (repo nhỏ, `.autopilot/` có/không trong `.gitignore`):

| Biến thể | exit | Cây sau | `.autopilot/` |
|---|---|---|---|
| V1: `.autopilot/` bị ignore + pathspec `-- . ':(exclude).autopilot'` | **1** | **candidate còn nguyên, đã bị `git add`** — nhưng vẫn tạo mục stash | giữ |
| V2: bị ignore, không pathspec | 0 | sạch | giữ |
| V3: không ignore + pathspec loại trừ | 0 | sạch (trừ `.autopilot/`) | giữ |
| V4/V5: **danh sách file tường minh** (`git status --porcelain -z --untracked-files=all` trừ `.autopilot/`) | 0 | sạch | giữ |
| Không ignore, không pathspec (`spike.py` 11c) | 0 | sạch | **bị cuốn vào stash** |

Trên cây spike (V4): exit 0, 0,009 s, `tree_fingerprint` về đúng vân tay lúc start; mục stash có nhãn còn lại để khôi phục.
Không thu hồi: file bị ignore candidate tạo (`.cache/`, `.pth` trong `.venv`) và **sửa nội dung submodule** (stash báo "No
local changes to save", exit 0, vân tay ≠ lúc start). Cây giữ: `GIT_INDEX_FILE` tạm + `read-tree HEAD` + `add -A -- <danh
sách>` + `write-tree` = `HEAD^{tree}` sau khi commit đúng các file đó (true). `git add -A -- . ':(exclude).autopilot'` cũng
exit 1 như V1 khi `.autopilot/` bị ignore.

## 6. Kết luận cho thiết kế

1. Đo candidate **tại chỗ** không đủ: file bị bỏ qua (venv, cache) lừa được bộ đo mà `tree_fp`/`perf guard` không thấy.
   Dựng candidate ở worktree riêng từ `start_head` + diff, phủ bộ đo từ gốc, `--setup` mới: +0,85 s/lần thử ở đây.
2. `--setup` phải chạy **trong từng cây** và có kiểm "trỏ đúng cây" — chạy lệnh đo bằng interpreter/`node_modules` của cây
   agent làm baseline đo mã candidate mà không lỗi nào hiện ra. Môi trường con phải bỏ `VIRTUAL_ENV`/`PATH` trỏ vào cây agent
   (suy từ hàng "hiểm hoạ" §2; chưa đo riêng).
3. Đo **xen kẽ** ba cây trong một lượt; ưu tiên đại lượng tất định (cần đường mẫu v2 cho số đọc từ stdout).
4. Thu hồi bằng stash với **danh sách file tường minh**, rồi kiểm vân tay; lệch (submodule) → dừng, không thử cách khác.
5. Held-out sinh **sau khi** candidate đóng băng (hạt giống lúc finish, bộ sinh từ gốc) bắt được đường tắt theo input.
6. `env.python` cần ghi interpreter của lệnh đo, không chỉ của `xt.py`.

## 7. Chưa đo được

Dự án cỡ thật (`node_modules` hàng nghìn file, pip không cache/mạng lạnh, monorepo) · macOS và runner CI · Cachegrind
(máy không có valgrind) · chỉ số phụ bộ nhớ có cấp phát thật (FLOW-23 chưa tái hiện số) · crash/kill giữa lượt và `--resume`
(thiết kế, chưa chạy) · hai lần thử đồng thời · candidate sửa công cụ chấm/worktree đo **trong khi** đo (cùng uid — giới
hạn đã biết của `optimization-loop.md`) · submodule qua mạng · bộ phân loại Auto/guard với `git stash`/`git worktree` do
agent tự gõ (spike chạy qua tiến trình con, không qua hook).
