# ADR-0058: Ba giai đoạn sản phẩm (MVP → hoàn thiện → tối ưu) khoá bằng máy, người duyệt từng giai đoạn

- **Trạng thái:** Đã chấp nhận (chủ dự án 2026-10-29: ưu tiên tốc độ qua ba giai đoạn tuần tự, giai đoạn trước chưa xong thì giai đoạn sau bị khoá — đặc tả #325; phiên chính tự duyệt cách khoá theo tiêu chí chất lượng cuối, ADR-0008 — D-239)
- **Trạng thái triển khai:** Lát C–D (phần máy) đã triển khai: `stage submit` đòi kiểm lại cuối xanh trên cây (`loop verify --all`) khi dự án chạy vòng và ghi khoá `preview` của `xt.yaml`; `loop next-step` (build) trả `stage-submit`/`wait-approval` thay `ready-for-complete` ở giai đoạn 1; đã trình mà mã đổi sau bản trình (ngoài sổ/PROGRESS) hay vòng còn việc → `stage-reopen`; `stage submit` từ chối khi vòng chưa `done`. Lát A+B đã triển khai — `scripts/xt.py` `stage …`, `stage_plan_problem` ở `loop init/next/record`, hàng `stage` của `release-check`; guard: sổ là `evidence`, `stage approve`/`init --adopt` bị deny; test `tests/test_stage.py`. `/complete`/`/optimize` theo giai đoạn: `loop init/next/record` từ chối `PLAN-harden-*` ở giai đoạn 1 và `PLAN-opt-*` trước giai đoạn 3, `next-step` harden ở giai đoạn 1 → `blocked` (D-246). Lát E installer (D-249): `install.py --stage-init` tạo sổ giai đoạn 1 khi chưa có (không cờ thì không tạo; thư mục con của repo git: không tạo — `loop_root` lệch `release-check`), sổ có sẵn giữ nguyên và được kiểm bằng `xt.py` vừa cài. Gate MVP/preview, nâng dự án đích chưa làm — [đặc tả](../autopilot/upgrades/2026-10-29-three-stage-delivery.md) §8.
- **Ngày:** 2026-10-29
- **Làm rõ:** ADR-0031 (`delivery_phase: build|harden` là chế độ kiểm soát, KHÔNG phải giai đoạn sản phẩm — giữ nguyên), ADR-0046/0047 (`/autopilot` lặp tới hết việc, `/complete` harden), ADR-0048 (`/optimize`), ADR-0026 (ghi tay `.autopilot/` = bằng chứng giả), ADR-0052 §2 (khoá `state.lock`).

## Bối cảnh

Khung có chu trình G0–G8 và hai chế độ kiểm soát build/harden, nhưng không có khái niệm "bản thử đã được chủ dự án duyệt". Đợt build
`done` hay `done-pending-human` không chứng minh MVP đã được duyệt; không gì ngăn PLAN của phần "hoàn thiện" hay "tối ưu" chạy trước khi
MVP được xem. Yêu cầu: ba giai đoạn tuần tự trên chu trình 11 bước (Ý tưởng → … → Tăng trưởng), giai đoạn sau khoá bằng máy.

Dữ kiện (nghiên cứu 2026-10-29, nguồn ở đặc tả §10): Stage-Gate đặt quyết định Go/Kill/Hold/Recycle ở gate do người giữ nguồn lực;
GOV.UK service assessment "red" = ở lại giai đoạn hiện tại và đánh giá lại; GitHub Environments cho người kích hoạt tự duyệt khi tắt
"prevent self-review" và admin bypass được — với repo một chủ, mọi hành động GitHub của agent mang cùng tài khoản với chủ; SLSA
attestation = mệnh đề có chủ thể (artefact) + vị ngữ (metadata), gắn bên phát hành.

## Các phương án đã cân nhắc

1. **Sổ `docs/autopilot/STAGE.json` theo git, chỉ `xt.py stage` ghi** (chọn).
2. Trạng thái trong `.autopilot/stage.json`: guard đã rào sẵn nhưng thư mục gitignored — mất khi đổi container/clone, sai với phiên cloud.
3. Duyệt qua GitHub (comment, review, Environment required reviewers): cùng tài khoản với token của agent ở repo một chủ → không phân
   biệt được người với agent; tự duyệt deployment được khi tắt "prevent self-review".

## Quyết định

1. **Sổ** `docs/autopilot/STAGE.json` (`schema: 1`): `cycle` (C-NNN), `stage` 1|2|3, `status` `active|awaiting_approval|completed`,
   `submitted` (bản chờ duyệt), `history` (init · adopt · submit · reopen · approve). Giai đoạn chưa mở = khoá (không ghi riêng). Sổ
   chỉ hợp lệ khi **lịch sử phát lại theo thứ tự** ra đúng chu kỳ/giai đoạn/trạng thái/bản chờ duyệt hiện tại: sự kiện đầu là `init`
   (giai đoạn 1) hoặc `adopt` (2|3, có `by` + `evidence`) — `adopt` chỉ ở đầu; mở giai đoạn N+1 chỉ qua `approve` (có `by`) ngay sau
   `submit` cùng SHA 40 hex của giai đoạn N, không `reopen` xen giữa; chu kỳ mới chỉ khi chu kỳ trước `completed` và đúng số kế tiếp
   — sửa tay `stage`/`history` bị lộ (review #327). Sổ hỏng → mọi lệnh đọc nó chặn (không đoán). Không có sổ và **chưa từng có trong
   git** (`git log --all`) = dự án không dùng giai đoạn (hành vi cũ; repo khung không dùng); sổ vắng mà lịch sử git có (xoá, dời thư
   mục, nhánh tách trước sổ) → chặn.
2. **Lệnh** `xt.py stage` (cùng gốc với `loop` — worktree đang sửa; parser không nhận viết tắt cờ): `status` (chỉ đọc) · `init`
   (giai đoạn 1) · `submit --evidence` (agent trình bản **HEAD của cây sạch** — tính cả file chưa track, trừ chính sổ và `.autopilot/`)
   · `reopen --reason` (chủ dự án yêu cầu sửa → `active` cùng giai đoạn, giữ lịch sử) · `approve --sha --note` (**chỉ người**: ≥ 7 ký
   tự của bản đã trình; mở giai đoạn kế; duyệt giai đoạn 3 → `completed`, PLAN giai đoạn 3 của chu kỳ đó vẫn chạy — bảo trì/cải tiến
   bản đã phát hành) · `new-cycle --reason` (bài toán lớn mới sau `completed` → chu kỳ kế ở giai đoạn 1; vá bản đang chạy làm trên
   nhánh phát hành, nơi sổ còn ở chu kỳ cũ) · `init --adopt 2|3 --evidence` (**chỉ người**: dự án đã chạy, công nhận bằng chứng lịch
   sử, không ép chạy lại từ MVP). Đọc–sửa–ghi trong khoá `state.lock` (ADR-0052 §2); sổ kết quả phải hợp lệ mới ghi; file mới theo umask (ghi lỗi → xoá, không để sổ rỗng).
3. **Chỉ người duyệt — hai lớp chặn nhầm, không phải ranh giới cách ly (D-015):** `xt.py` từ chối `approve`/`init --adopt` khi tiến
   trình mang biến môi trường của phiên agent (`CLAUDECODE`, `CLAUDE_CODE_SESSION_ID`, `AI_AGENT`); guard deny lệnh đó (mã
   `STAGE_APPROVE`) và coi sổ là `evidence` (ghi tay qua Edit/Bash bị chặn như `.autopilot/`). `by` lấy từ `git config user.email`
   (thiếu thì `user.name`) của máy chạy lệnh. Lời "ok" trong chat, comment GitHub hay `loop decide` không phải phê duyệt.
4. **Khoá ở lối vào vòng:** PLAN khai **đúng một** dòng `Giai đoạn sản phẩm: N (C-NNN)` (dòng trong code fence không tính); khi
   có sổ, `loop init`, `loop next`, `loop record` từ chối PLAN không khai, khai nhiều dòng, khai giai đoạn/chu kỳ khác giai đoạn đang
   mở — kể cả PLAN sửa sau `loop init` hay người vừa duyệt. `record` không nhận bằng chứng của PLAN khoá nên không task nào của
   giai đoạn khoá được tick. Verdict của vòng (`loop status`, Stop hook) và các lối ra `unblock`/`attach`/`doctor` **không** đọc
   khoá (D-241, sau hai lượt review: đưa khoá vào verdict làm lệch lần lượt từng lối ra cũ); người vừa duyệt mà vòng còn bật thì
   lời từ chối của `record`/`next` chỉ lối ra: PLAN đợt mới khai N+1 rồi `loop init --plan … --force` (LOOP-HARNESS-024 nguyên
   bản: cố ý đổi PLAN). Đang `awaiting_approval` vẫn chạy PLAN của **cùng** giai đoạn; hết việc thì agent `stage submit`, báo
   người, dừng. `loop record` ngoài vòng (chưa `loop init`) không biết PLAN nên không kiểm giai đoạn.
5. **`release-check` thêm hàng `stage`:** sổ vắng (chưa từng có) → N/A SHOULD; giai đoạn 1 (kể cả chờ duyệt) → FAIL BLOCKER ("MVP
   chưa mở Production" — preview/demo không phải Production); giai đoạn 2/3 → PASS (phát hành ở giai đoạn 2 không đợi xong giai đoạn
   3); sổ hỏng/vắng mà git có → FAIL. Mọi hàng cũ giữ. Sổ không tính vào vân tay cây của `loop verify`.
6. GO của máy, nghiệm thu của người, quyền deploy và đã deploy là bốn việc khác nhau; `approve` chỉ là nghiệm thu giai đoạn.

## Hệ quả

- Tốt: máy không mở giai đoạn sau khi chưa có `approve`, agent không tự công nhận MVP (trong giới hạn lớp chặn nhầm); trạng thái bền
  qua container (git), lịch sử kiểm được; dự án chưa dùng không đổi.
- Xấu: máy so giai đoạn PLAN **tự khai**, không đọc nội dung task — review vẫn là lớp kiểm phạm vi. Chủ dự án phải chạy một lệnh ở
  terminal **ngoài phiên Claude Code** (Remote Control vẫn là phiên agent → bị từ chối) — chủ chỉ dùng app thì giai đoạn dừng ở
  `awaiting_approval`. Agent khác Claude có thể không mang các biến môi trường trên (chưa xác minh); guard chỉ chạy dưới Claude Code.
  Sổ "từng có" tính trên **mọi ref** (`git log --all --source`, lời báo nêu ref): `stage init` trên nhánh lát chặn mọi worktree
  khác tới khi merge; mỗi lệnh đọc khoá (`loop init/next/record`, `stage`, `release-check`) tốn một lượt `git log --all` khi chưa có sổ — tuyến tính theo số
  commit (đo ≈ 2,5 s ở 300k commit), repo cực lớn cần cache (việc sau). Ai có quyền ghi repo sửa được sổ và tự viết `approve` hợp lệ (như sổ audit); `by` là cấu hình git tự khai, không phải chữ ký. Squash
  merge làm SHA đã trình không còn trên nhánh chính — `approve` so chuỗi SHA đã trình. Chữ ký thật (attestation SLSA/in-toto, tag ký,
  tree-hash) là việc sau nếu cần.
- Định tuyến `/complete`/`/optimize` theo **tên PLAN skill đặt** (`PLAN-harden-*` từ giai đoạn 2, `PLAN-opt-*` giai đoạn 3 — D-246):
  đổi tên để lách là lỗi cố ý, cùng mức lớp đỡ như guard; không theo `delivery_phase` vì dự án giữ `harden` sau phát hành (ADR-0037).
- Chưa làm (đặc tả §8): Gate MVP riêng ngoài kiểm lại cuối (smoke trên bản preview), `/optimize` cho mục tiêu tính năng/mã nguồn
  khi chưa đỏ, nâng dự án đích.

## Đường lùi

Dự án: xoá sổ bị chặn có chủ đích (lịch sử git còn); muốn bỏ khoá thì người duyệt lần lượt tới giai đoạn 3 (PLAN giai đoạn 3 không
còn bị khoá) hoặc nâng khung lên bản bỏ ADR này. Khung: bỏ lời gọi `stage_plan_problem` ở `loop` và `_release_stage` ở
`release-check`; bỏ `STAGE_LEDGER`/`_approves_stage` ở guard.
