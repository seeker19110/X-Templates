# ADR-0052: State có revision, chặn không-tiến-triển theo task, mẫu perf v2, `loop next-step` chỉ đọc và `perf trial` — lát 0–3 của nghiên cứu ba vòng

- **Trạng thái:** Đã chấp nhận (chủ repo 2026-10-27: "hoàn thành hết đi" — sáu lát của [nghiên cứu 2026-10-26](../../research/2026-10-26-autopilot-complete-optimize.md); phiên chính tự duyệt thiết kế theo tiêu chí chất lượng cuối, ADR-0008 — D-202)
- **Trạng thái triển khai:** Chưa triển khai — `docs/autopilot/PLAN-harden-2026-10-27-loops.md`, mỗi task một PR.
- **Ngày:** 2026-10-27
- **Làm rõ:** [ADR-0051](0051-split-session-attach-from-resume.md) (ba điểm review #288 — §Quyết định 6), `LOOP-DESIGN-005`/`-011` (lỗi lặp), `LOOP-OPT-002`/`-004`/`-007`/`-008`/`-011` (tối ưu), ADR-0046/0047/0048 (ba điểm vào giữ nguyên), ADR-0009 (một phiên).

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
   nghiên cứu §10. Ca chưa sửa ghi trong registry `XFAIL = {"FLOW-NN": "<tái hiện>"}` của chính file và nhận
   `expectedFailure` từ registry — **không** skip. Biến môi trường `XT_FLOW_STRICT=FLOW-NN[,…]` bỏ xfail cho các ID nêu, nên Gate
   của task sửa chạy `XT_FLOW_STRICT=<ID> python3 -m unittest tests.test_flow` và chỉ xanh khi ca đó thật sự đạt (expected failure
   tự nó cho suite exit 0). Sửa xong thì gỡ ID khỏi registry (quên → "unexpected success" đỏ). Ca của lát 4–5 (FLOW-24 field)
   không viết tới khi lát đó được làm.
2. **`rev` cho `state.json` (§4C).** `write_state` nhận `expect_rev`; giữ khoá `fcntl.flock` trên `.autopilot/state.lock` chỉ quanh
   đọc–so–ghi (timeout 5 s, không giữ qua Gate/mạng). Lệch `rev` → hàm `update_state(base, fn)` đọc lại và áp lại `fn` (tối đa 3 lần);
   lệnh không áp lại được (`init`, `resume`/`attach`/`unblock`) → lỗi exit 2, không ghi đè. State thiếu `rev` = 0. Stop hook lỗi khoá
   → fail-open (cho dừng, ghi log). Không có `fcntl` (không POSIX) → bỏ khoá, vẫn kiểm `rev`.
3. **Không-tiến-triển theo task (§4B).** `task_runs` `{T-NNN: n}` trong state, tăng ở mỗi `loop record` đỏ, về 0 khi task xanh hoặc
   `req_rev` của task đổi. `_verdict_loop_state`: `task_runs[t] ≥ max_task_runs` → `blocked` "N lần đỏ, M chữ ký khác nhau — đặc tả hoặc
   Gate sai, người xem" (M đếm từ `runs.jsonl`). Mặc định `max_task_runs = 2 × max_same_failure` (= 6); `loop init --max-task-runs N`
   (0 = tắt, là đường lùi). `attach`/`resolve` không đặt lại; `unblock` và `loop resume` (nghĩa cũ "mở block + đặt lại đếm lỗi",
   ADR-0051) đặt lại `task_runs` của task đang chặn — nếu không, verdict tính lại từ `task_runs` sẽ chặn ngay và lối ra mà
   `_live_loop`/bảng điểm dừng chỉ ra không mở được. `perf trial` đếm lần thử riêng (§7), không qua `task_runs`. Không nới `max_same_failure`.
4. **Mẫu perf v2 (§7.1).** `perf sample` ghi `schema: 2`, `unit`, `higher_is_better`, `env {platform, python, nproc}`, `head` (`git rev-parse
   HEAD` lúc đo), `dirty` (cây có diff/untracked ngoài `.autopilot/`), `tree_fp` (= `tree_fingerprint`), `harness_sha256` = sha256 của
   lệnh đo + nội dung các file khớp `--harness GLOB` (lặp được; cùng glob với `perf guard --locked`; không truyền → chỉ hash lệnh, cảnh báo).
   `perf compare` theo **vai**: `before` là baseline — phải `dirty: false` (đo trên cây sạch của `head`, vd worktree `origin/main` ghim SHA);
   `after` là candidate — hoặc cùng `head` với before (sửa chưa commit, luồng `perf trial`/`/optimize` bước 3), hoặc `head` là hậu duệ của
   head before (đã commit). Exit 2 "không đủ điều kiện so" khi: lệch `unit`/`cmd`/`higher_is_better`/`harness_sha256`/`env.platform`;
   before `dirty`; after không cùng head và không là hậu duệ. Lệch `python`/`nproc` → cảnh báo. File v1/mảng thô → so được nhưng JSON
   đầu ra `unverified-manual: true` và không bao giờ trả `improved` cho `--no-regress`/ratchet tự động. (FLOW-19 của nghiên cứu §10 viết
   lại theo vai: baseline bẩn, hoặc candidate không cùng/không hậu duệ head baseline → từ chối.)
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
7. **`perf trial` (lát 3, §7.2).** `perf trial start --hotspot H --hypothesis … --falsifier …` ghi `.autopilot/perf-trials.jsonl` **trước**
   khi sửa và ghim `base_sha` + danh sách file bộ đo; `perf trial finish --before … --after …` chạy `perf compare` v2 rồi giữ hoặc thu
   hồi **đúng file của lần thử** bằng `git stash push --include-untracked -m <nhãn> -- <files>` (không `checkout -- .`/`reset --hard`); `--resume` sau crash khôi
   phục và ghi "chưa hoàn tất". Khoá trùng = hotspot + hash diff. Ba lần không `improved` cùng hotspot (bền qua restart) → exit 2 "đổi
   điểm nóng" (`LOOP-OPT-011`). Chỉ số phụ vượt trần đã khai → đỏ dù chính `improved` (`LOOP-OPT-008`).
8. **Không làm ở ADR này:** lát 4 (pilot phiên thực ≥ 2 dự án đích, cho `next-step` ghi trạng thái) và lát 5 (field trigger, bot nâng bản,
   worker ngoài phiên, event policy `pull_request_target`) cần dữ liệu/quyền của chủ dự án — `loop defer`; ADR riêng khi có số.

Phát hành: lát 1 đổi hành vi dự án đích → cắt bản 3.28.0 sau lát 1, 3.29.0 sau lát 2–3 (CHANGELOG mục "Dự án đích").

### Hệ quả

- Tốt: bốn tái hiện R2–R5 có test đỏ → xanh; agent ít tự ghép bước kế; số can thiệp đo được.
- Xấu: thêm trường state và lệnh con (byte `scripts/`, chữ README mảng 11 đang 0 B dư → câu mới đổi câu cũ); trần theo task có thể chặn
  oan task lớn đang tiến bộ (lý do nêu M chữ ký; `--max-task-runs 0` tắt).

### Xác nhận

FLOW-01…23 xanh trong CI (trừ ca lát 4–5); `autonomy-bench` không lùi; `dev-task.sh gate` xanh; review sạch ở head mỗi PR.

## Đường lùi

Mỗi quyết định một PR đảo ngược được: bỏ kiểm `rev` (ghi vẫn atomic), `--max-task-runs 0`, `perf compare --schema 1` tạm, skill bỏ gọi
`next-step`, `perf trial` không `--apply`.

## Thông tin thêm

Nghiên cứu §4–§12; tái hiện `research/evidence/2026-10-26-three-loops/`. Ngưỡng 6 lần là số để pilot đo lại, không phải hằng số chốt.
