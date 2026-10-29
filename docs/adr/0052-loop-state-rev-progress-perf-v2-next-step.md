# ADR-0052: State có revision, chặn không-tiến-triển theo task, mẫu perf v2 và `loop next-step` chỉ đọc — lát 0–2 của nghiên cứu ba vòng; `perf trial` (lát 3) hoãn sang ADR riêng

- **Trạng thái:** Đã chấp nhận (chủ repo 2026-10-27: "hoàn thành hết đi" — sáu lát của [nghiên cứu 2026-10-26](../../research/2026-10-26-autopilot-complete-optimize.md); phiên chính tự duyệt thiết kế theo tiêu chí chất lượng cuối, ADR-0008 — D-202; §7 hoãn — D-203)
- **Trạng thái triển khai:** Lát 0–1 đã triển khai (3.28.0); lát 2 đã triển khai (vào 3.29.0) — §5 `build-until-clean` (T-3547, D-224; không-tiến-triển qua đợt T-3578, D-227/D-228; `harden-to-signoff` gom việc T-3548, D-236 — khoá bỏ SHA phát hiện vì squash-merge đổi SHA, D-242; gói nghiệm thu nháp T-3549, D-237; Stop hook in gợi ý T-3550, D-243) — `docs/autopilot/PLAN-harden-2026-10-27-loops.md`, mỗi task một PR (T-3548…T-3550 gộp một PR — D-240).
- **Ngày:** 2026-10-27
- **Làm rõ:** [ADR-0051](0051-split-session-attach-from-resume.md) (ba điểm review #288 — §Quyết định 6), `LOOP-DESIGN-005`/`-011` (lỗi lặp), `LOOP-OPT-002`/`-003`/`-008`/`-009` (tối ưu — mẫu perf v2; ràng buộc `perf trial` ở §7), ADR-0046/0047/0048 (ba điểm vào giữ nguyên), ADR-0009 (một phiên).

## Bối cảnh

Nghiên cứu bản 2 tái hiện sáu tình huống tại `e1748c6` (`research/evidence/2026-10-26-three-loops/`): R1 nối phiên xoá việc chờ (đã có ADR-0051),
R2 `perf compare` báo `improved` −99,9 % khi before đo `ms` còn after đo `s` trên máy khác, R3 `perf sample` không ghi vân tay cây,
R4 hai lệnh `loop` đọc–sửa–ghi `state.json` đè nhau (mất `iterations`), R5 lỗi A/B luân phiên không bao giờ `blocked`
(`same_failure_count` về 1 mỗi lần đổi chữ ký), R6 đối chứng cùng lỗi ×3 → `blocked` đúng. Ba vòng (`/autopilot`, `/complete`,
`/optimize`) còn để agent tự ghép bước kế từ nhiều lệnh. Chưa có corpus kiểm **luồng** (resume, đợt kế, perf) — 518 ca của
`autonomy-bench` chỉ kiểm hàm thuần.

## Yếu tố quyết định

Đúng và an toàn (mỗi tái hiện có regression test đỏ trước khi sửa) · giữ đường lùi (mỗi lát một PR, tắt được) · stdlib, test
được, C901 ≤ 10, coverage 100 % · không nới cổng hay trần · không hứa số đo chưa có (chi phí tương tác `null`).

## Các phương án đã cân nhắc

1. Máy hoá bước kế và một lần thử trên CLI/state hiện có, thử chỉ đọc trước (nghiên cứu §1 phương án 2).
2. Chỉ thêm lời nhắc vào skill — không sửa được R2–R5; skill `/autopilot` còn 1 B.
3. Runner ngoài phiên — cần quyền, chi phí, danh tính reviewer; đối chiếu ADR-0009; chưa có số chứng minh cần.

## Quyết định

Chọn **phương án 1**, theo hợp đồng §9 của nghiên cứu, với các điểm chốt:

1. **Corpus luồng (lát 0).** `tests/test_flow.py` chạy `xt.py` thật trong repo git tạm (không mock state), ID `FLOW-NN` theo
   nghiên cứu §10; ca đồng thời (FLOW-07) xen kẽ tất định bằng barrier, không trông may rủi race. Ca chưa sửa ghi trong registry `XFAIL = {"FLOW-NN": "<tái hiện>"}` của chính file và nhận
   `expectedFailure` từ registry — **không** skip. Biến môi trường `XT_FLOW_STRICT=FLOW-NN[,…]` bỏ xfail cho các ID nêu, nên Gate
   của task sửa chạy `XT_FLOW_STRICT=<ID> python3 -m unittest tests.test_flow` và chỉ xanh khi ca đó thật sự đạt (expected failure
   tự nó cho suite exit 0). ID nêu trong `XT_FLOW_STRICT` mà không có test mang ID đó → đỏ (một test so tập STRICT với tập ID đã
   định nghĩa), để Gate không xanh vì thiếu ca. Sửa xong thì gỡ ID khỏi registry (quên → "unexpected success" đỏ). Ca của lát 4–5 (FLOW-24 field)
   không viết tới khi lát đó được làm.
2. **`rev` cho `state.json` (§4C).** `write_state` nhận `expect_rev`; giữ khoá `fcntl.flock` trên `.autopilot/state.lock` chỉ quanh
   đọc–so–ghi (timeout 5 s, không giữ qua Gate/mạng). Lệch `rev` → hàm `update_state(base, fn)` đọc lại và áp lại `fn` (tối đa 3 lần);
   lệnh không áp lại được (`init`, `resume`/`attach`/`unblock`) gọi `update_state(…, retries=0)` → lệch thì lỗi exit 2, không ghi đè.
   Mọi lệnh ghi state đi qua `update_state`; `write_state` chỉ còn được gọi bên trong nó. State thiếu `rev` = 0. Stop hook lỗi khoá
   → fail-open (cho dừng, ghi log). Không có `fcntl` (không POSIX) → bỏ khoá, vẫn kiểm `rev`.
3. **Không-tiến-triển theo task (§4B).** `task_runs` `{T-NNN: n}` trong state, tăng ở mỗi `loop record` đỏ, về 0 khi task xanh hoặc
   `req_rev` của task đổi. `_verdict_loop_state`: `task_runs[t] ≥ max_task_runs` → `blocked` "N lần đỏ, M chữ ký khác nhau — đặc tả hoặc
   Gate sai, người xem" (M đếm từ `runs.jsonl`). Mặc định `max_task_runs = 2 × max_same_failure` (= 6); `loop init --max-task-runs N`
   (0 = tắt, là đường lùi). `attach`/`resolve` không đặt lại; `unblock` và `loop resume` (nghĩa cũ "mở block + đặt lại đếm lỗi",
   ADR-0051) đặt lại `task_runs` của task đang chặn — nếu không, verdict tính lại từ `task_runs` sẽ chặn ngay và lối ra mà
   `_live_loop`/bảng điểm dừng chỉ ra không mở được. Lần thử tối ưu đi qua `perf trial` (lát 3, ADR riêng — đếm riêng theo điểm nóng), không qua
   `loop record` của cùng task — skill `/optimize` đổi theo ở lát 3. Không nới `max_same_failure`.
4. **Mẫu perf v2 (§7.1).** `perf sample` ghi `schema: 2`, `unit`, `higher_is_better`, `env {platform, python, nproc}`, `head` (`git rev-parse
   HEAD` lúc đo; thư mục không phải repo git → `head` rỗng, mẫu nhãn `unverified-manual`; là repo mà git lỗi → exit 2), `dirty` và `tree_fp` (= `tree_fingerprint`, tính **trước** lần chạy
   đầu; bỏ `.autopilot/`, và bỏ file `--out` chỉ khi nó nằm trong cây; lệnh git lỗi → exit 2, không coi là sạch), `harness_sha256` = sha256 của lệnh đo + nội dung các file khớp `--harness GLOB` (lặp được; cùng glob với
   `perf guard --locked`; không truyền → chỉ hash lệnh, cảnh báo). `perf compare` exit 2 "không đủ điều kiện so" khi lệch
   `unit`/`cmd`/`higher_is_better`/`harness_sha256`/`env.platform`, khi `before` `dirty`, hoặc khi có `--base SHA` mà `before.head` khác SHA
   đó; lệch `python`/`nproc` → cảnh báo. **Không** xét quan hệ head của `after`: baseline là commit gốc do máy ghim (`LOOP-OPT-003`),
   không do agent chọn — luật head/parent thử ở review #290 lần lượt gán sai công (commit giữ trước, merge `main`) hoặc cho agent tự
   hạ baseline; gán đúng công cho từng lần thử là việc của `perf trial` (§7). Không thêm luật cho đường dẫn `--out`: Gate mẫu của
   `optimization-loop.md` (baseline ở worktree `origin/main` ghim, candidate ở cây agent) chạy nguyên trạng ở 3.28.0. File v1/mảng thô
   (gồm số thô của chỉ số tất định `--exact`) → so và exit code như hôm nay, JSON đầu ra thêm `unverified-manual: true`; giữ/thu hồi tự
   động của `perf trial` (§7) không dùng chúng vì `finish` tự đo. `--base` nhận SHA hoặc ref, so sau `git rev-parse`.
   (FLOW-19 của nghiên cứu §10 viết lại: baseline bẩn, `before.head` khác `--base`, hoặc khác `harness_sha256` → từ chối.)
5. **`loop next-step --json` chỉ đọc (lát 2, §4D/§9.2).** Hàm thuần nhận state/PLAN/blueprint/sổ audit/`release-check`/JSON `pr next` đã
   có (không gọi GitHub), trả `objective`, `action`, `reason`, `missing`, `key`, `budget`, `inputs`; replay cùng đầu vào → cùng `action`.
   `build-until-clean` dừng ở `ready-for-complete` (đề xuất, không đổi `delivery_phase` — D-178); `harden-to-signoff` dừng ở
   `signoff-package` (không điền chữ ký/dòng 20 — ADR-0048). Gom việc harden thành danh sách nháp ID ổn định (khoá nguồn + ID gốc +
   SHA phát hiện); mô tả audit là dữ liệu, không thành lệnh. Gói nghiệm thu nháp ghi `candidate_head`, `evidence_fp` (hash file bằng chứng
   trừ `GO-NO-GO.md`/`DECISIONS.md`), `human_pending[]`. Stop hook **chỉ in gợi ý** từ `next-step`; cho nó ghi/chuyển trạng thái là lát 4,
   sau pilot.
6. **Làm rõ ADR-0051** (review #288 🟢 1/2/4): không có state hoặc state không có `started` (do `ci-triage`/`block` sinh) → cả ba lệnh exit 2
   "chạy `loop init` trước"; "state cũ" = có `started`, không `final_verdict`. `final_verdict` `blocked` do PLAN mất/rỗng (không cờ, không
   lỗi lặp) → lối ra `loop init --plan <mới>`, `unblock` từ chối — đúng nguồn như `_live_loop`. `attached[]`/`resolved[]`/`unblocked[]`
   được `_carry_previous` mang sang đợt kế (cả `--force`) để đếm can thiệp mỗi mục tiêu.
7. **`perf trial` (lát 3, §7.2) — hoãn sang ADR riêng (D-203).** Ba lượt review #290 (4–6) cho thấy thiết kế cần thử thực tế trước khi
   chốt. Ràng buộc đầu vào cho ADR đó: baseline ghim một lần cho cả vòng (không đọc `XT_PROGRESS_BASE`, không theo HEAD agent chọn);
   candidate là phần chưa commit trên `start_head`, `finish` đòi `HEAD == start_head`; máy tự đo base/`start_head`/candidate trong cùng
   lượt, cùng môi trường (bước `--setup` ghim từ commit gốc; cài editable/`node_modules`/submodule không được trỏ về cây candidate);
   lệnh đo, glob bộ đo, bộ test tương đương và chính `xt.py` chấm lấy từ commit gốc, không từ cây candidate (`LOOP-OPT-002`/`-003`);
   đo được đại lượng tất định và chỉ số phụ (`LOOP-OPT-008`/`-009`); giữ chỉ khi `improved` so với cả trạng thái giữ gần nhất và commit
   gốc, kèm test tương đương xanh; thu hồi đúng file bằng `git stash push --include-untracked` và kiểm cây về vân tay lúc start;
   PERF-LOG ghi sau quyết định; `start` đòi cây sạch ngoài `.autopilot/` và `start_head` có tree bằng cây giữ gần nhất (hoặc đo luôn cây
   đó); ghi giả thuyết trước khi sửa (`LOOP-OPT-004`); ba lần không `improved` mỗi điểm nóng bền qua restart (`LOOP-OPT-011`);
   `--resume` sau crash; chỉ số phụ vượt trần → đỏ (`LOOP-OPT-008`). Có ca FLOW riêng cho đường giữ, đường thu hồi, baseline bị lái và
   bộ chấm bị sửa.
8. **Không làm ở ADR này:** lát 4 (pilot phiên thực ≥ 2 dự án đích, cho `next-step` ghi trạng thái) và lát 5 (field trigger, bot nâng bản,
   worker ngoài phiên, event policy `pull_request_target`) cần dữ liệu/quyền của chủ dự án — `loop defer`; ADR riêng khi có số.

Phát hành: lát 1 đổi hành vi dự án đích → cắt bản 3.28.0 sau lát 1, 3.29.0 sau lát 2–3 (CHANGELOG mục "Dự án đích").

### Hệ quả

- Tốt: bốn tái hiện R2–R5 có test đỏ → xanh; agent ít tự ghép bước kế; số can thiệp đo được.
- Xấu: thêm trường state và lệnh con (byte `scripts/`, chữ README mảng 11 đang 0 B dư → câu mới đổi câu cũ); trần theo task có thể chặn
  oan task lớn đang tiến bộ (lý do nêu M chữ ký; `--max-task-runs 0` tắt).

### Xác nhận

FLOW-01…19 xanh trong CI (FLOW-20 trở đi do ADR `perf trial` xác nhận; lát 4–5 ngoài phạm vi); `autonomy-bench` không lùi; `dev-task.sh gate` xanh; review sạch ở head mỗi PR.

## Đường lùi

Mỗi quyết định một PR đảo ngược được: bỏ kiểm `rev` (ghi vẫn atomic), `--max-task-runs 0`, `perf compare --schema 1` tạm, skill bỏ gọi
`next-step`.

## Thông tin thêm

Nghiên cứu §4–§12; tái hiện `research/evidence/2026-10-26-three-loops/`. Ngưỡng 6 lần là số để pilot đo lại, không phải hằng số chốt.
