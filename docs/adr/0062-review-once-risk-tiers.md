# ADR-0062: Review 1 lần theo ba mức rủi ro — 🔴 sửa, 🟠/🟢 ghi nợ rồi merge; cổng production đủ năm nhóm

- **Trạng thái:** Đã chấp nhận (chủ dự án 2026-11-01, áp cho khung và dự án đích: "[ON] Tạo PR ngay sau khi hoàn thành phần
  việc · [ON] Bắt buộc CI đạt trước khi merge · [OFF] Review AI chuyên sâu cho mọi PR · [ON] Review độc lập với thay đổi rủi
  ro cao · [ON] Auto-merge PR rủi ro thấp khi đạt điều kiện · [ON] Audit tổng thể cuối mỗi giai đoạn · [ON] Chặn Production
  nếu chưa đạt quality gates — chỉ review 1 lần: lỗi nghiêm trọng thì sửa, lỗi cam và xanh thì ghi nợ cho merge"; phiên chính
  tự duyệt cách máy hoá theo tiêu chí chất lượng cuối, ADR-0008 — D-295)
- **Trạng thái triển khai:** Đang triển khai — `scripts/xt.py`: `REVIEW_ROUNDS = 1`, `_pr_next_review` (`debt` sau một review
  đã kết luận), `pr debt --fixed` (`_debt_problem`, `_debt_row_problem`), `merge_decision` khoá `high_risk`,
  `review_deferrable`; `release-check` hàng `migration`/`rollback`/`acceptance` (lát kế); tài liệu ở AGENTS.md (cả mẫu),
  `LOOP-STOP-022`, skill `/review`, `/complete`.
- **Ngày:** 2026-11-01
- **Thay:** ADR-0059 §1–2 (ngân sách "review 2 lần, sửa 1 lần" và `rethink` khi còn 🔴); D-124 ("reviewer chỉ chạy ở pha
  harden") cho PR rủi ro cao. **Giữ:** ADR-0059 §3–6 (dấu `debt` là review hợp lệ ở head, nợ chặn `audit check --strict`, PR
  cắt bản không ghi nợ — rà tới sạch), ADR-0036 (merge ghim head, không auto-merge của GitHub), ADR-0037 (pha build hoãn
  review rủi ro trung bình thành nợ), ADR-0061 (`max_rethink`), `LOOP-ORCH-005` (reviewer năng lực cao hơn người viết).

## Bối cảnh

ADR-0059 cho mỗi PR hai lượt review và một lần sửa; 🔴 còn lại phải `pr rethink` (D-NNN) rồi sửa hết và rà lại. Chủ dự án đặt
cấu hình mới: review AI không chạy cho mọi PR, chỉ theo mức rủi ro, và **mỗi PR chỉ review một lần**: 🔴 sửa, 🟠/🟢 ghi nợ để
merge; audit tổng thể cuối mỗi pha gom lỗi và sửa theo nhóm; production chặn khi chưa đạt cổng chức năng, bảo mật, migration,
rollback, nghiệm thu.

## Các phương án đã cân nhắc

1. **Máy hoá đúng chữ, 🔴 không ghi nợ** (chọn): review 1 lần; 🔴 sửa trong một commit, ghi `đã sửa` ở sổ, `pr debt --fixed`
   (không review lại); 🟠/🟢 ghi nợ; ba mức rủi ro ánh xạ lên làn đã có; `release-check` thêm ba hàng.
2. Chỉ đổi tài liệu, máy giữ ADR-0059 — PR vẫn đứng ở lượt hai, trái cấu hình mới.
3. Review 1 lần nhưng bản sửa 🔴 phải rà lại delta — an toàn hơn nhưng trái "chỉ review 1 lần".

Phương án 3 đúng tiêu chí (1) hơn nếu chỉ xét từng PR; chủ dự án đã chọn rõ và đặt lưới đỡ ở cấp pha (audit cuối pha quét lại
mọi file đổi, `audit check --strict` chặn phát hành khi còn nợ) — phương án 1 giữ hai lưới đó và không ghi nợ 🔴.

## Quyết định

1. **Ba mức rủi ro** (ánh xạ lên `merge_lane_reasons`/`merge_hard_reasons`, không thêm khoá cấu hình):
   - **Thấp** = làn nhanh (không đường nhạy cảm, ≤ 150 dòng, một gói, có test): CI xanh + tác giả tự rà diff → máy merge ghim
     head (L2/L3) — không reviewer AI riêng.
   - **Trung bình** = làn chuẩn không thuộc mức cao (cổng/CI, phụ thuộc, nguồn gói, container, > 150 dòng, nhiều gói, đổi mã
     không đổi test, nhãn `risk:` thường): **một** review tập trung logic, phạm vi, test; pha build hoãn thành nợ (ADR-0037).
   - **Cao** (`high_risk` của `merge_decision`) = ngoại lệ cứng kể cả đã miễn (`merge_hard_exceptions: auto` — xác thực, phân
     quyền, thanh toán, mật mã, bí mật, `merge_risk_paths` dự án tự khai, nhãn `risk:auth|payment|pii|crypto|admin|secret`) hoặc
     schema/migration: **một** review độc lập bắt buộc (reviewer năng lực cao hơn người viết, `LOOP-ORCH-005`) ở **mọi pha** —
     `review_deferrable` trả sai cho PR này cả ở pha build.
2. **Review 1 lần** (`REVIEW_ROUNDS = 1`): sau một review đã kết luận còn lỗi, `pr next` trả `debt` (không `fix` rồi rà lại).
   `do`: mỗi 🟠/🟢 → dòng `mở` có `nợ-review: #N`; mỗi 🔴 → sửa trong **một** commit (kèm test hồi quy) và dòng `đã sửa` có
   `nợ-review: #N`; push → `pr debt --pr N --findings <🟠/🟢> --fixed <🔴>`.
3. **`pr debt`** nhận khi `pr next` là `debt`; cây ở head khác cây ở review cuối **chỉ** ở sổ/cập nhật nhánh, **hoặc** có
   `--fixed` (bản sửa 🔴 không rà lại); ID `--findings` là `mở` không 🔴, ID `--fixed` là 🔴 `đã sửa`, cả hai đúng tag PR, trong
   sổ ở head; 🔴 không bao giờ ghi nợ. Dấu đăng `verdict=debt` (một điều kiện merge — ADR-0028, ADR-0059 §4).
4. **`inconclusive` không tính lượt** (ADR-0029): review không kết luận được → cần review khác ở head, không `debt`.
   `review_identity`, PR cắt bản (ADR-0059 §6) → `rethink` như cũ; `max_rethink` (ADR-0061) giữ.
5. **Audit tổng thể cuối mỗi pha** (đã có: `milestone_audit`, `loop next-step` → `audit`): một lần, gom 🔴/🟠 + nợ review thành
   task theo nhóm, chạy lại kiểm liên quan; nợ `nợ-review` trả ở đây.
6. **Chặn production khi chưa đạt cổng** (`release-check` = NO-GO, `prod_switch`): hàng sẵn có (blueprint/verify = chức năng,
   audit/attack = bảo mật, review_debt, perf) cộng `migration` (thử migration tiến + lùi trên bản sao dữ liệu), `rollback`
   (diễn tập quay về bản trước), `acceptance` (kiểm thử nghiệm thu) — lệnh khai ở xt.yaml như `attack`/`perf` (ADR-0042).

## Hệ quả

- Tốt: PR không đứng sau review đầu; review AI chỉ tốn cho PR rủi ro trung bình/cao; PR rủi ro cao không còn trôi qua pha build
  không ai rà; production có cổng migration/rollback/nghiệm thu máy đọc.
- Xấu: bản sửa 🔴 vào nhánh chính không được rà lại — lưới đỡ là CI, test hồi quy bắt buộc kèm bản sửa, audit cuối pha và
  `release-check`; PR rủi ro cao ở pha build chậm hơn (thêm một review).
- Đường lùi: revert PR của ADR này (`REVIEW_ROUNDS = 2`, `_debt_problem` cũ, bỏ `high_risk`, bỏ ba hàng); dự án đích nâng khung.
