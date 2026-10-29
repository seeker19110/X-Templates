# ADR-0058: Ba giai đoạn sản phẩm (MVP → hoàn thiện → tối ưu) khoá bằng máy, người duyệt từng giai đoạn

- **Trạng thái:** Đã chấp nhận (chủ dự án 2026-10-29: ưu tiên tốc độ qua ba giai đoạn tuần tự, giai đoạn trước chưa xong thì giai đoạn sau bị khoá — đặc tả #325; phiên chính tự duyệt cách khoá theo tiêu chí chất lượng cuối, ADR-0008 — D-239)
- **Trạng thái triển khai:** Lát A+B đã triển khai — `scripts/xt.py` `stage …`, `stage_plan_problem` ở `loop init/next/record`, hàng `stage` của `release-check`; guard: sổ là `evidence`, `stage approve`/`init --adopt` bị deny; test `tests/test_stage.py`. Lát C–F (Gate MVP/preview, `/complete` `/optimize` theo giai đoạn, installer/migration, nâng dự án đích) chưa làm — [đặc tả](../autopilot/upgrades/2026-10-29-three-stage-delivery.md) §8.
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
   chỉ hợp lệ khi **lịch sử dựng lại đúng** giai đoạn/trạng thái hiện tại: mỗi lần mở giai đoạn N+1 phải có `approve` của giai đoạn N
   (40 hex `sha`, `by`) — sửa tay 1 → 3 bị lộ. Sổ hỏng → mọi lệnh đọc nó chặn (không đoán). Không có sổ = dự án không dùng giai đoạn
   (hành vi cũ; repo khung không dùng).
2. **Lệnh** `xt.py stage`: `status` (chỉ đọc) · `init` (giai đoạn 1) · `submit --evidence` (agent trình bản **HEAD của cây sạch**, trừ
   chính sổ) · `reopen --reason` (chủ dự án yêu cầu sửa → `active` cùng giai đoạn, giữ lịch sử) · `approve --sha --note` (**chỉ
   người**: SHA phải là bản đã trình; mở giai đoạn kế; duyệt giai đoạn 3 → `completed`) · `new-cycle --reason` (bài toán lớn mới sau
   `completed` → chu kỳ kế ở giai đoạn 1) · `init --adopt 2|3 --evidence` (**chỉ người**: dự án đã chạy, công nhận bằng chứng lịch sử,
   không ép chạy lại từ MVP). Đọc–sửa–ghi trong khoá `state.lock` (ADR-0052 §2); sổ kết quả phải hợp lệ mới ghi.
3. **Chỉ người duyệt — hai lớp chặn nhầm, không phải ranh giới cách ly (D-015):** `xt.py` từ chối `approve`/`init --adopt` khi tiến
   trình mang biến môi trường của phiên agent (`CLAUDECODE`, `CLAUDE_CODE_SESSION_ID`, `AI_AGENT`); guard deny lệnh đó (mã
   `STAGE_APPROVE`) và coi sổ là `evidence` (ghi tay qua Edit/Bash bị chặn như `.autopilot/`). `by` lấy từ `git config user.email`
   của máy chạy lệnh. Lời "ok" trong chat, comment GitHub hay `loop decide` không phải phê duyệt.
4. **Khoá ở mọi lối vào vòng:** PLAN khai `Giai đoạn sản phẩm: N (C-NNN)`; khi có sổ, `loop init`, `loop next` và `loop record` từ
   chối PLAN không khai, khai giai đoạn/chu kỳ khác giai đoạn đang mở, hoặc chu kỳ đã `completed` — kể cả PLAN sửa sau `loop init`.
   Đang `awaiting_approval` vẫn chạy PLAN của **cùng** giai đoạn (sửa theo phản hồi), không lấp thời gian chờ bằng giai đoạn sau.
5. **`release-check` thêm hàng `stage`:** sổ vắng → N/A SHOULD; giai đoạn 1 → FAIL BLOCKER ("MVP chưa mở Production" — preview/demo
   không phải Production); giai đoạn 2/3 → PASS (phát hành ở giai đoạn 2 không đợi xong giai đoạn 3); sổ hỏng → FAIL. Mọi hàng cũ giữ.
6. GO của máy, nghiệm thu của người, quyền deploy và đã deploy là bốn việc khác nhau; `approve` chỉ là nghiệm thu giai đoạn.

## Hệ quả

- Tốt: không còn đường 1 → 3 hay agent tự công nhận MVP; trạng thái bền qua container (git), lịch sử kiểm được; dự án cũ không đổi.
- Xấu: chủ dự án phải chạy một lệnh ở terminal (máy riêng/Remote Control) — phiên cloud chỉ trên app thì giai đoạn dừng ở
  `awaiting_approval` (`loop defer`); ai có quyền ghi repo sửa được sổ và tự viết `approve` (lớp chặn nhầm, không chống người cố ý —
  như sổ audit); `by` là cấu hình git tự khai, không phải chữ ký. Chữ ký thật (attestation SLSA/in-toto, tag ký) là việc sau nếu cần.
- Chưa làm (đặc tả §8): Gate MVP/preview, định tuyến `/complete`/`/optimize` theo giai đoạn, `/optimize` cho mục tiêu tính năng/mã
  nguồn khi chưa đỏ, `loop next-step` đề xuất `stage submit`, installer tạo sổ cho dự án mới, nâng dự án đích.

## Đường lùi

Dự án: xoá `docs/autopilot/STAGE.json` → về hành vi trước ADR này. Khung: bỏ lời gọi `stage_plan_problem` ở `loop` và
`_release_stage` ở `release-check`; bỏ `STAGE_LEDGER`/`_approves_stage` ở guard.
