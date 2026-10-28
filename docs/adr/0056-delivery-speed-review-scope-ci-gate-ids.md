# ADR-0056: Tốc độ giao hàng — lỗi có từ trước không chặn PR, CI là cổng đầy đủ ở mọi pha, đánh số D-NNN qua nhánh remote

- **Trạng thái:** Đã chấp nhận (chủ repo 2026-10-28: "nghiên cứu sâu và tối ưu lại quy trình, mục tiêu phát triển phần mềm càng nhanh càng tốt"; phiên chính tự duyệt theo tiêu chí chất lượng cuối, ADR-0008 — D-221)
- **Trạng thái triển khai:** Đã triển khai — `.claude/skills/review/SKILL.md` (Cách báo), `.claude/skills/gate/SKILL.md` bước 4, AGENTS.md §6, `scripts/xt.py` `_remote_decisions`/`_last_decision` (T-3577, test `DecideWorktreesTest.test_decide_remote_branch_numbers_do_not_collide`), `xt.yaml` khoá `setup`.
- **Ngày:** 2026-10-28
- **Làm rõ:** ADR-0033 và ADR-0046 (giữ "`gate` một lần trước khi đẩy" ở harden — nay chỉ khi không có CI hoặc trước cắt bản), ADR-0041 §2 (CI là cổng ở pha build — nay mọi pha), ADR-0053 (trần lượt review — giữ), ADR-0031 (nợ review/sổ audit chặn phát hành — giữ), T-2612 (đánh số qua worktree).

## Bối cảnh

Số đo ở [research/2026-10-28-velocity.md](../../research/2026-10-28-velocity.md): CI một lượt ≈ 2 phút; PR mã mở → merge trung vị
≈ 65 phút với 2–3 lượt review, lượt đầu `blocking` ở 5/5 PR lấy mẫu, mỗi lượt sửa → review lại 30–45 phút. #306 lượt 2 chặn vì
🔴 có từ trước, sửa luôn trong PR làm diff lên 1 607 dòng; cùng lớp lỗi cũ kéo sang #308 (D-216…D-218). Cổng cục bộ `gate`
(nối tiếp, có `test_floor` 160 s) chạy trước mỗi lần đẩy dù CI chạy đúng các lệnh đó song song và merge đòi CI xanh. Hai phiên ở
container khác nhau cùng giữ D-219 và `AUD-SEC-129` vì `loop decide` chỉ đọc sổ của các worktree cùng máy.

## Các phương án đã cân nhắc

1. **Bỏ nguyên nhân của vòng chậm, giữ mọi cổng chặn hợp nhất/phát hành** (chọn): phân loại lỗi có từ trước, CI là cổng đầy đủ,
   đánh số qua ref remote.
2. Nới cổng: bỏ review ở `harden`, hạ coverage, tăng `REVIEW_ROUNDS` — trái AGENTS.md §3 (không làm cổng xanh bằng cách nới).
3. Chỉ ghi khuyến nghị — không đổi được số lượt review vì luật hiện hành buộc mọi 🔴 chặn PR đang mở.

## Quyết định

1. **Lỗi có từ trước không chặn PR.** Reviewer tách phát hiện tái hiện được ở base mà diff không tạo ra, không làm tệ hơn và không
   nằm trên đường mã diff vừa thêm thành mục "Có từ trước" kèm mức thật; phiên chính ghi sổ audit + task mới. 🔴 mở trong sổ vẫn
   chặn phát hành (`audit check --strict`, hàng `audit` của `release-check`) — cổng dời từ merge sang phát hành, không biến mất.
2. **CI là cổng đầy đủ ở mọi pha** khi CI chạy đúng các khoá `xt.yaml` và merge đòi CI xanh: trước khi đẩy chỉ cần cổng commit
   `gate-fast` đã chạy ở mỗi commit. `gate` cục bộ còn cho lần đẩy cuối trước cắt bản, khi không có CI, hoặc khi người gọi `/gate`. Lý do giữ của
   ADR-0033 (auto-merge không ghim head) đã hết từ ADR-0036 (merge ghim head); CI đỏ chỉ tốn một lượt ≈ 2 phút.
3. **Đánh số D-NNN đọc thêm sổ ở 100 nhánh remote-tracking mới nhất** (một `git grep`, không gọi API; không phải repo git/không
   có remote → như cũ). Phiên `git fetch` trước `loop decide` để thấy nhánh mới; chỉ thấy D-NNN đã đẩy — hai phiên quyết định cùng lúc trước khi ai đẩy vẫn có thể trùng (đổi số khi gộp).
4. **`xt.yaml` khai `setup`** (cài công cụ ghim hash) để setup script của môi trường cloud gọi `scripts/dev-task.sh setup`.

## Hệ quả

- Tốt: bớt lượt review và PR phình vì lỗi cũ; mỗi lần đẩy bớt vài phút cổng cục bộ; hết trùng D-NNN với nhánh đã đẩy và đã fetch.
- Xấu: lỗi cũ nghiêm trọng có thể nằm trên `main` lâu hơn (tới khi task sửa chạy) — đỡ bằng sổ `--strict` chặn phát hành và task
  mới ngay; thỉnh thoảng một lượt CI đỏ mà `gate` cục bộ đã bắt được (coverage chỉ đo ở CI/`gate`).
- Chưa làm (cần số/ADR): máy báo PR > 150 dòng ở `pr next`; review sạch ở head thay một phần audit delta (đổi ADR-0031); ID
  `AUD-*`/số ADR quét nhánh remote; SessionStart báo nhánh có việc chưa vào `main`.

## Đường lùi

Từng điểm một commit: bỏ đoạn "Lỗi có từ trước" ở `/review`; khôi phục bước 4 của `/gate` và dòng AGENTS.md §6; bỏ
`_remote_decisions` khỏi `_last_decision`; xoá khoá `setup`.
