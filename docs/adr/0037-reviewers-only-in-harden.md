# ADR-0037: Reviewer chỉ chạy ở pha `harden`; chỉ chuyển sang `harden` khi lên production

- **Trạng thái:** Đã chấp nhận (chủ repo yêu cầu 2026-10-21, D-124); bổ sung ADR-0031 — thay mục "Ranh giới ngoại lệ cứng"
  về `hard_waived` và mục nhãn `risk:` ở pha build. ADR-0025 (nhãn `risk:` là phanh thủ công) còn hiệu lực ở pha `harden`. Chuyển `harden` là bước 1 của `/complete`, một chiều — skill không tự đổi pha (ADR-0046).
- **Trạng thái triển khai:** `scripts/xt.py` `review_deferrable`/`review_deferred`; `.claude/skills/autopilot/SKILL.md` bước 6;
  test `tests/test_delivery_phase.py`, ca `pr-phase-build-risk-label`, `pr-phase-build-hard-waived-needs-review`,
  `review-phase-build-hard-waived-asks-review` (PLAN-3.13 T-1815).
- **Ngày:** 2026-10-21
- **Làm rõ:** ADR-0031 (pha build/harden), ADR-0033 (tối giản pha build), ADR-0020 (ngoại lệ cứng miễn người), ADR-0036
  (merge ghim head); `LOOP-ORCH-005` (reviewer khác họ model).

## Bối cảnh

ADR-0031 hoãn review thành nợ ở pha build, trừ hai trường hợp vẫn đòi review sạch ở head: PR ngoại lệ cứng đã miễn người
merge (`hard_waived`, khi `merge_hard_exceptions: auto`) và PR mang nhãn `risk:`. Ở repo khung mọi PR chạm `scripts/`,
`framework/templates/`, `docs/autopilot/PLAN*.md` là `hard_waived` (`merge_risk_paths`), nên thực tế gần như mọi PR có mã đều
phải chờ `reviewer`/`reviewer-alt` (PR #198: hai lượt review). Chủ repo yêu cầu 2026-10-21: "chuyển reviewer và reviewer-alt
vào pha harden, chỉ khi lên product mới vào pha harden và cho phép reviewer và reviewer-alt".

## Quyết định

1. **Pha `build`: không giao `reviewer`/`reviewer-alt`.** Review thiếu ở head thành nợ (`review: deferred`) cho mọi PR mà máy
   được merge — kể cả `hard_waived` và PR mang nhãn `risk:`. `review_deferrable` = pha build và không `hard`.
2. **Giữ nguyên:** ngoại lệ cứng giữ người (`hard`, `merge_hard_exceptions: human`) vẫn do người merge; review `blocking`
   đã có vẫn chặn, và một lần push không "rửa" được nó (cần review lại head); CI xanh, không xung đột, merge ghim head
   (ADR-0036); pha xác định từ CẢ `xt.yaml` đã commit ở nhánh đích lẫn cây làm việc — PR không tự chuyển sang build.
3. **Chuyển sang `harden` chỉ khi lên production** (chuẩn bị phát hành G7): đặt `delivery_phase: harden`, chạy audit delta,
   từ đó PR làn chuẩn, `hard_waived` và nhãn `risk:` lại cần review sạch ở head bởi reviewer khác họ model. `release-check`
   FAIL hàng `phase` ở build và `review_debt` khi còn file ngoài tài liệu đổi sau SHA quét — nợ phải trả trước phát hành.
4. `/autopilot` bước 6: chỉ ở pha harden mới giao `reviewer-alt` rà diff ngoại lệ cứng trước khi mở PR; giao reviewer khi
   `pr next` trả `review` (ở build máy không trả `review` cho PR thiếu review).

## Lý do

- Quyết định của chủ repo (AGENTS.md §1). Bằng chứng nền: research 2026-10-21 §4.4 — review bằng LLM trên PR thật có F1
  thấp (0,066), reviewer khác model không tốt hơn đáng kể; chi phí là thời gian chờ mỗi PR. Lớp đỡ ở pha build là cổng máy
  (CI 100 % coverage, `autonomy-bench`, guard, fuzz guard) và audit delta + review trước phát hành.

## Hệ quả

- Lỗi logic hay bảo mật mà cổng máy không bắt được có thể vào nhánh chính ở pha build và chỉ lộ ở audit delta trước phát
  hành. Đây là rủi ro chủ repo chấp nhận; mọi nhánh chính ở pha build không được coi là bản phát hành.
- Nhãn `risk:` ở pha build chỉ còn là ghi chú (nợ có tên); muốn chặn PR cụ thể thì người merge tay hoặc đặt `harden`.
- Người hay agent vẫn có thể tự giao review ở build khi muốn; review sạch ở head xoá nợ của PR đó.

## Đường lùi

`review_deferrable` thêm lại `and not d.get("hard_waived")`, `review_deferred` thêm lại `and not d.get("risk_labels")`; hoặc đặt
`delivery_phase: harden` (review lại bắt buộc ngay ở PR kế).
