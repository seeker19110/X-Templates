# ADR-0059: Review 2 lần, sửa 1 lần — hết lượt thì ghi nợ và tiếp tục, nợ trả cuối pha

- **Trạng thái:** Đã chấp nhận (chủ dự án 2026-10-30: "luật mới áp dụng cho cả dự án khung và đích: review 2 lần, sửa 1 lần, còn đâu ghi nợ và tiếp tục, nợ sẽ sửa cuối pha"; phiên chính tự duyệt cách máy hoá theo tiêu chí chất lượng cuối, ADR-0008 — D-257)
- **Trạng thái triển khai:** Đã triển khai — `scripts/xt.py` `_pr_next_review` (`debt`), `pr debt` (`_pr_debt`, `_debt_problem`), dấu `verdict=debt` (`review_comment_body`, `published_reviews`), `REVIEW_DEBT_RE`/`is_review_debt` (`audit check --strict`, `audit_open_count`, `_harden_sources`); guard chặn đăng tay dấu `debt`; test `PrNextTest.test_review_round_budget_stops_fix_review_loop`, `PrNextCliTest.test_debt_records_ledger_findings`, `PrStewardTest.test_debt_mark_counts_as_review_at_head`, ca `autonomy-bench` `review-adr0059-debt-mark-at-head`.
- **Ngày:** 2026-10-30
- **Thay:** quyết định 2 của ADR-0053 (`rethink` khi hết lượt). Giữ: đếm lượt (`REVIEW_ROUNDS = 2`), `pr rethink` (nay chỉ cho 🔴), review trước PR dùng cho đúng head.
- **Làm rõ:** ADR-0027/0028 (dấu `xt-review v1`, `review_gate` — một điều kiện merge), ADR-0031 (nợ review của pha build), ADR-0056 (lỗi có từ trước không chặn PR).

## Bối cảnh

ADR-0053 dừng vòng sửa–review ở lượt hai bằng `rethink`: PR đứng lại tới khi có quyết định đổi chiến lược (D-NNN). Thực tế
#341 cần D-256 để thu hẹp, nhiều PR khác dừng ở lượt ba chỉ vì 🟢/🟠 nhỏ — PR không vào nhánh chính dù lỗi chặn thật đã sửa.
Chủ dự án đặt luật mới cho khung và mọi dự án đích: **review 2 lần, sửa 1 lần; còn lại ghi nợ và tiếp tục; nợ sửa cuối pha.**

## Các phương án đã cân nhắc

1. **Máy hoá, 🔴 không ghi nợ** (chọn): hết lượt → `pr next` trả `debt`; phát hiện 🟠/🟢 còn lại vào sổ audit, `pr debt` đăng dấu
   `verdict=debt` (review hợp lệ ở head); còn 🔴 → `pr rethink` như cũ; nợ mở chặn `audit check --strict` tới khi trả.
2. Như 1 nhưng ghi nợ mọi mức, kể cả 🔴.
3. Chỉ sửa tài liệu/skill (kỷ luật), máy giữ `rethink`.

Phương án 2 đúng chữ của luật nhưng đưa lỗi chặn đã biết vào nhánh chính — dự án đích có thể triển khai liên tục từ `main`;
tiêu chí (1) chọn cách hiểu chặt hơn, người đổi được bằng một dòng ở `_debt_problem`. Phương án 3: máy vẫn trả `rethink`, PR
vẫn đứng — trái luật mới.

## Quyết định

1. **Ngân sách:** `review_rounds` như ADR-0053 (review đã đăng chưa sạch sau review sạch/ghi nợ cuối và sau `pr rethink` cuối);
   trần 2 = một lượt toàn PR + một lượt delta sau **một** lần sửa.
2. **`pr next` trả `debt`** khi PR cần review ở head (strict, không hoãn), head chưa sạch và đã hết lượt. `do`: mỗi phát hiện
   🟠/🟢 còn lại → một dòng `mở` ở `docs/ops/AUDIT-STATUS.md` có `nợ-review: #N` ở Ghi chú; commit chỉ sổ, push; rồi
   `xt.py pr debt --pr N --findings AUD-…[,AUD-…]`. Còn 🔴 → `loop decide` + `pr rethink` (mở thêm hai lượt).
3. **`pr debt`** chỉ nhận khi: `pr next` đang là `debt`; commit (không phải merge) sau review chưa sạch cuối **chỉ** đổi sổ audit
   (sửa 1 lần — sửa thêm thì cần lượt review mới qua `pr rethink`); mỗi ID là dòng `mở`, không 🔴, Ghi chú `nợ-review: #N` của
   đúng PR, trong sổ **ở head**. Ghi bản ghi `{head, clean: true, debt: [ID…]}` vào `.autopilot/reviews.json` và đăng dấu
   `<!-- xt-review v1 head=<SHA> verdict=debt -->`; đăng lỗi → `pr next` trả `republish-review` với lệnh `pr debt`.
4. **Một điều kiện merge (ADR-0028):** dấu `debt` của người có quyền ghi = review hợp lệ ở head — `merge-check`, guard, steward,
   `pr next` đọc như dấu sạch (sửa sau khi đăng với `review_identity` → không hợp lệ, như dấu sạch). Guard chặn đăng tay dấu
   `debt` như dấu `clean`/`blocking` (AUD-SEC-069).
5. **Nợ trả cuối pha:** dòng `mở` có `nợ-review: #N` ở mọi mức làm `audit check --strict` đỏ (`release-check` hàng `audit`
   BLOCKER), tính vào việc mở của `loop next-step` (build: `replan` trước `ready-for-complete`/trình MVP; harden: gom thành task).

## Hệ quả

- Tốt: PR không đứng vì 🟠/🟢 sau hai lượt; nợ không mất — có ID ở sổ, chặn phát hành tới khi trả; dấu vết đủ để người xem lại.
- Xấu: nhánh chính mang 🟠 đã biết trong một khoảng; `pr debt` tin mức mà phiên chính ghi vào sổ (reviewer gắn mức, sổ do người
  viết PR chép) — reviewer lượt sau/audit delta là lớp đỡ. Với `review_identity` cấu hình, dấu `debt` do tác giả đăng không
  được tính (như dấu sạch) — ghi nợ cần tài khoản reviewer.
- Steward không ghi nợ: `debt` chỉ vào bản tóm tắt như `review`/`fix`.

## Đường lùi

Trả nhánh `debt` của `_pr_next_review` về `rethink` (ADR-0053); `pr debt`, dấu `verdict=debt` và `nợ-review:` vô hại khi không
dùng. Revert squash PR triển khai.
