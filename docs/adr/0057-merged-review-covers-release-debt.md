# ADR-0057: Review sạch ở head của PR đã merge phủ nợ review khi phát hành — bớt PR sổ sau squash-merge

- **Trạng thái:** Đã chấp nhận (chủ repo 2026-10-28: "làm hướng 1" — tối ưu tốc độ, ADR-0056 §Chưa làm; phiên chính tự duyệt theo tiêu chí chất lượng cuối, ADR-0008 — D-222)
- **Trạng thái triển khai:** Đã triển khai — `scripts/xt.py` `reviewed_debt`, `_merged_clean`, `_release_review_debt`; test `DeliveryPhaseReleaseTest.test_delivery_phase_review_debt_covered_by_merged_review`.
- **Ngày:** 2026-10-28
- **Làm rõ:** ADR-0031 (nợ review chặn phát hành — giữ; thêm một nguồn phủ), ADR-0027/0028 (dấu `xt-review v1`, `review_gate`), ADR-0056 (§Chưa làm: "review sạch ở head thay một phần audit delta"), AUD-HAR-122.

## Bối cảnh

Repo merge kiểu squash: SHA trong PR không bao giờ thành tổ tiên `main`, nên sổ audit chỉ phủ được thay đổi của một PR **sau** khi
PR đó merge — bằng một PR sổ riêng. Đợt 2026-10-28 cần #310, #313, #315 (và PR cắt bản #314 luôn NO-GO ở head của chính nó vì
`VERSION`): mỗi PR sổ ≈ 30–60 phút review + CI cho đúng một việc là dời SHA. Trong khi đó PR mã ở `harden` đã có review sạch ở
đúng head bởi reviewer năng lực cao hơn người viết — chính là audit delta cho diff đó (tiền lệ: #308, #313 dời SHA chỉ dựa vào review).

## Các phương án đã cân nhắc

1. **`release-check` hỏi GitHub dấu review của PR tạo ra mỗi commit nợ** (chọn): nguồn tin cậy là dấu `xt-review` của người có quyền
   ghi (cùng luật merge), không giả được bằng nội dung commit.
2. Trailer trong thông điệp commit squash (`Xt-Reviewed: …`): đọc offline, nhưng thông điệp squash mặc định gồm commit của tác giả
   PR — tác giả tự viết trailer được.
3. Giữ nguyên, chỉ gộp nhiều PR vào một PR sổ: vẫn tốn một PR và một lượt review mỗi đợt.

## Quyết định

1. Hàng `review_debt` của `release-check`: file nợ được coi là đã phủ khi **mọi** commit first-parent trên nhánh chính chạm file đó
   sau SHA quét cũ nhất là commit merge của một PR — tiêu đề kết thúc `(#N)`, PR #N `merged` với `merge_commit_sha` đúng commit —
   có review sạch ở head cuối theo `review_gate` (dấu đã đăng của người có quyền ghi; mang qua "cập nhật nhánh" sạch). Hàng ghi
   PASS kèm danh sách PR.
2. Không đọc được GitHub (offline, token thiếu quyền), commit không phải squash của PR, PR làn nhanh không có review → vẫn là nợ (FAIL
   như cũ — chặt). Gate máy đọc offline (`xt.review_debt` trong PLAN) không đổi.
3. Sổ audit vẫn là nơi ghi kết quả audit theo nhóm; PR sổ chỉ cần khi có audit thật (đợt quét, phát hiện mới), không cần để dời SHA
   sau mỗi PR mã đã review.

## Hệ quả

- Tốt: PR cắt bản và PR mã đã review không còn kéo theo PR sổ chỉ để dời SHA; `release-check` GO ngay sau merge khi mọi PR có review.
- Xấu: `release-check` cần mạng/`gh` để dùng nguồn phủ này (không có → như cũ); mỗi commit nợ một lượt REST; review chỉ phủ diff của
  PR, không thay audit đủ 13 nhóm theo định kỳ — đợt audit (`/audit`) vẫn chạy theo lịch của pha harden.

## Đường lùi

Bỏ lời gọi `reviewed_debt` trong `_release_review_debt` (một dòng) — hàng trở về chỉ dựa vào sổ.
