# ADR-0053: Ngân sách review mỗi PR — hai lượt chưa sạch rồi `rethink`; review trước PR dùng cho đúng head

- **Trạng thái:** Đã chấp nhận; quyết định 2 (`rethink` khi hết lượt) thay bởi [ADR-0059](0059-review-twice-fix-once-debt.md) — hết lượt trả `debt`, `pr rethink` chỉ còn cho 🔴 (chủ repo 2026-10-27: "kiểm tra bổ sung, sửa pr 297 rồi triển khai luôn"; phiên chính tự duyệt phạm vi theo tiêu chí chất lượng cuối, ADR-0008 — D-209)
- **Trạng thái triển khai:** Đã triển khai — `scripts/xt.py` `REVIEW_ROUNDS`, `review_rounds`, `_pr_next_review` (`rethink`), `_pr_rethink`; skill `/complete` bước 4, `/review`; `LOOP-STOP-022`; test `PrNextTest.test_review_round_budget_stops_fix_review_loop`, `PrNextCliTest.test_rethink_needs_new_decision_naming_pr`, `PrNextCliTest.test_rethink_decision_must_follow_every_unclean_review`, `PrNextCliTest.test_rethink_reads_decision_of_worktree`, 2 ca `autonomy-bench`. Quyết định 3 siết thêm bởi D-210/D-211 (review #298): chỉ khi `pr next` đang là `rethink`; câu hỏi của D-NNN nhắc `#N`; mốc D-NNN sau mọi review chưa sạch đã đăng và không ở tương lai; tra sổ của worktree đang sửa rồi của dự án. `pr rethink` là dấu vết quyết định, không phải hàng rào chống giả mạo (D-211).
- **Ngày:** 2026-10-27
- **Làm rõ:** [PLAN-phase-gated-review](../specs/PLAN-phase-gated-review.md) (PR #297 — chỉ phần §11 được duyệt), ADR-0025 (`pr next`), ADR-0028 (`merge_eligibility` — không đổi), ADR-0029 (`inconclusive`), ADR-0037 (review chỉ ở harden), ADR-0052 §3 (`task_runs` — cùng tinh thần cho task).

## Bối cảnh

Ở pha `harden`, PR làn chuẩn chỉ merge khi có review sạch ở đúng head (`review_gate`). Review `blocking` → sửa → push → `pr next`
trả `review` cho `H..head` → … không có trần: PR #282 qua **bảy lượt** review; lượt 3–5 mỗi lượt tìm thêm một đường lách
danh sách chặn, và chỉ khi đổi chiến lược (hook đóng hàng rào khi `guard.py` không nạp được — D-199/D-200) vòng mới dừng.
Lượt thứ ba trên cùng cách sửa là tín hiệu cách sửa sai, không phải thiếu một lượt review nữa.

Trùng lượt thứ hai: `/complete` bước 4 giao `reviewer-alt` rà diff ngoại lệ cứng **trước** khi mở PR; khi
`merge_hard_exceptions: auto` (repo khung) PR đó là làn chuẩn (`hard_waived`) nên `pr next` lại đòi review ở cùng commit.

PLAN-phase-gated-review (PR #297) đề xuất review một lần theo pha. Kiểm bổ sung 2026-10-27 trên `main` `ca02729`: phần lớn
hạ tầng kế hoạch cần đã có — dấu review theo head (`xt-review v1`, ADR-0027), rà delta `H..head`, mang review qua khi chỉ cập
nhật nhánh (`base_merge_of`), `rev` + khoá cho `state.json` và chặn không-tiến-triển theo task (ADR-0052). Phần thiếu thật là
**trần lượt review** và **review trùng ở cùng head**.

## Các phương án đã cân nhắc

1. **Trần lượt mỗi PR + dùng lại review trước PR** (chọn).
2. **Đủ RV-01…RV-07 của PLAN**: sổ pha, fingerprint finding, coverage manifest, một PR mỗi pha ở harden, pilot.
3. Chỉ sửa tài liệu, chưa đổi hành vi.

Phương án 2 trái P8 (nhỏ, đảo ngược được), giới hạn 150 dòng của `/review` và bằng chứng của ADR-0037 (review LLM trên diff
lớn kém tin cậy); engine pha mới trùng sổ review và `state.json` đã có. Mục tiêu "giảm 50 % chi phí" của PLAN chưa có số đo.
Phương án 3 để nguyên vòng lặp đã gây bảy lượt.

## Quyết định

1. **Đếm lượt:** `review_rounds` = số review **đã đăng** chưa sạch (`blocking` hoặc `inconclusive`) của PR, tính sau review sạch
   cuối và sau lần `pr rethink` cuối. Trần `REVIEW_ROUNDS = 2` (một lượt toàn PR + một lượt delta).
2. **`pr next` trả `rethink`** thay cho `review`/`fix` khi PR cần review ở head (strict, không hoãn) mà head chưa sạch và
   `review_rounds` ≥ trần. `do`: ghi `xt.py loop decide` đổi chiến lược (tách/thu hẹp PR, đổi thiết kế, đóng PR) rồi
   `xt.py pr rethink --pr N --decision D-NNN` (mở thêm hai lượt); việc cần người → `loop defer`. Auto-merge do người bật vẫn
   tắt trước như mọi bước chặn.
3. **`pr rethink --pr N --decision D-NNN`**: D-NNN phải có tiêu đề `### D-NNN ·` trong `docs/autopilot/DECISIONS.md` và chưa
   dùng cho PR đó; ghi `rethinks[]` `{decision, at}` vào `.autopilot/reviews.json`. Sổ cục bộ mất → mất lượt mở thêm (chặt hơn).
4. **Không nới cổng:** `merge_eligibility`, `merge-check`, guard, steward giữ nguyên — merge vẫn cần review sạch ở head;
   `rethink` chỉ đổi bước kế. Steward không đọc sổ cục bộ nên có thể báo `rethink` cho PR đã được mở thêm lượt — chỉ báo, không lệnh.
5. **Review trước PR = review của head đó:** `/complete` bước 4 — rà trước PR ở đúng commit được đẩy; mở PR xong ghi
   `pr reviewed --head <SHA đó>` theo kết luận, không giao lần hai. Head đổi thì như mọi PR (rà `H..head`).
6. **Không làm** phần còn lại của PLAN (một PR mỗi pha ở harden, sổ pha, fingerprint, coverage manifest, pilot). Xét lại khi
   có số lượt review/PR đo được (`pr stats`, ADR-0043) cho thấy trần này chưa đủ.

## Hệ quả

- Tốt: vòng sửa–review dừng ở lượt hai; lượt thêm phải có quyết định ghi lại (D-NNN) — đúng `LOOP-STOP-018`. Bớt một lượt
  review cho mỗi PR ngoại lệ cứng ở `/complete`.
- Xấu: PR lớn bị `inconclusive` hai lần cũng dừng ở `rethink` — đúng hướng (tách PR) nhưng thêm một bước. Một D-NNN chỉ mở
  được một lần cho mỗi PR; quyết định không kiểm được chất lượng nội dung, chỉ kiểm có dấu vết.
- Còn treo: `pr-review.yml` (chưa bật) review mỗi `synchronize` không qua `pr next`; khi bật phải bỏ qua PR đang `rethink`.

## Đường lùi

Đặt `REVIEW_ROUNDS` rất lớn hoặc bỏ nhánh `rethink` trong `_pr_next_review`; `pr rethink` và trường `rethinks` vô hại khi không dùng.
Revert squash PR triển khai.
