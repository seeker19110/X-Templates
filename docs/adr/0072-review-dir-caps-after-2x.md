# ADR-0072: Xét lại trần thư mục sau khi `.claude/hooks/` vượt 2× mốc 2026-10-26 — giữ trần, mốc mới, cổng máy

- **Trạng thái:** Đã chấp nhận 2026-11-05 (phiên chính tự duyệt theo tiêu chí chất lượng cuối, ADR-0008 — **D-373**; audit
  delta T-3557 nhóm ARCH, AUD-ARCH-009).
- **Trạng thái triển khai:** Đã triển khai — `tests/test_docs_budget.py` `SIZE_MARKS`, `test_dir_totals_within_double_latest_mark`;
  đo chi phí compile `guard.py` giao `T-3709` (PLAN-upgrade-2026-11-02, hạn 2027-01-21).
- **Ngày:** 2026-11-05.
- **Xét lại:** [ADR-0050](0050-raise-dir-size-caps.md) §Hệ quả ("Nếu một nhóm vượt 2× kích thước 2026-10-26 trước mốc đó
  thì phải có ADR xét lại"). **Giữ:** ADR-0043 (đóng băng bề mặt 3.x), trần `DIR_CAPS` của ADR-0050 (không nới số).
- **Liên quan:** ADR-0065/0066/0067 (bản vá guard gây tăng), AUD-PERF-013 + D-307 (không cache bytecode khi khoá không ràng
  buộc được bytecode — AUD-SEC-074), AUD-ARCH-007/008 (tách `guard.py`/`xt.py`).

## Bối cảnh

ADR-0050 nâng mỗi trần thư mục thêm 1 MiB và đặt điều kiện theo dõi: nhóm nào vượt 2× kích thước 2026-10-26 trước mốc
2027-01-21 thì phải có ADR xét lại. Không cổng máy nào giữ điều kiện đó; audit delta T-3557 (nhóm ARCH) phát hiện nó đã
bị vượt mà chưa có ADR.

Số đo (file git theo dõi, `git ls-tree -r -l <sha>` cộng cột kích thước theo pathspec của nhóm trong `DIR_CAPS`; mốc
2026-10-26 = số ADR-0050 ghi, đo trên `main` + PR #282):

| Nhóm | Mốc 2026-10-26 | 2× mốc | `742434b` | Tỉ lệ | Trần `DIR_CAPS` |
|---|---:|---:|---:|---:|---:|
| `.claude/hooks/` | 369 274 | 738 548 | 843 817 | 2,29× | 1 417 969 |
| `scripts/*.py` + `scripts/xt_app/` | 711 824 | 1 423 648 | 1 164 066 | 1,64× | 1 760 431 |
| `framework/11-autonomous-loop/` | 232 297 | 464 594 | 292 202 | 1,26× | 1 280 883 |
| `docs/ops/` (trừ `*-ARCHIVE.md`) | 771 538 (2026-11-02, D-314) | 1 543 076 | 808 591 | 1,05× | 810 114 |
| `docs/autopilot/` (trừ `DECISIONS-*.md`) | 335 567 (2026-11-02, D-314) | 671 134 | 348 007 | 1,04× | 352 345 |

- Ba nhóm mã có cùng số ở `0a2583f` (`main` sau #447). `docs/ops/` ở đó là 809 909 B.
- `.claude/hooks/` vượt 2× từ commit `024ee79` (#433, 2026-11-03 UTC): 737 030 → 745 800 B. Đo `ls-tree` ở commit merge
  `45c553c` của #282 là 369 464 B (chênh 190 B so với số ADR-0050 ghi trên nhánh PR); bảng mốc dùng số ADR-0050 vì nó
  chặt hơn và là số quyết định cũ đã nêu.
- Gần như toàn bộ mức tăng nằm ở `guard.py`: 337 397 B (`45c553c`) → 544 348 B (`9f123b1`, audit ARCH 2026-11-02) →
  811 554 B (`0a2583f`); 10 048 → 14 661 dòng từ `9f123b1`. Nguồn là chuỗi bản vá an ninh guard #433–#442 theo
  ADR-0065/0066/0067 (luật tĩnh, danh sách trắng, chặn dạng nguyên văn), không phải tính năng mới.
- `scripts/` tăng 1,64× (`xt.py` 789 305 → 996 685 B từ `9f123b1`, phần lớn là `perf trial`, ADR-0071) — chưa vượt nhưng
  sẽ chạm 2× sau khoảng 260 KB nữa.
- Chi phí lúc chạy: mỗi lệnh Bash hook compile nguồn `guard.py` (cố ý không cache — AUD-SEC-074, D-307). Số đo cũ
  (AUD-PERF-013, `guard.py` 510 KB): compile 0,12–0,16 s mỗi lệnh. Ở 811 KB **(chưa đo)** — trong phiên audit guard chặn
  script đọc `guard.py` để đo, nên giao task đo riêng.

## Phương án đã xét

1. **Giữ trần, đặt mốc mới, thêm cổng máy** (chọn). Trần `DIR_CAPS` không đổi (hooks còn 574 152 B). Ghi mốc 2026-11-05
   cho `.claude/hooks/` và `scripts/`. Test đỏ khi nhóm vượt 2× mốc gần nhất mà chưa có ADR khai mốc mới. Đo chi phí compile
   trước khi quyết tách. Nhược: chấp nhận `guard.py` lớn thêm một thời gian; mốc mới nới điểm báo động 2× cho hai nhóm.
2. **Tách `guard.py` hoặc precompile ngay.** Giảm byte mỗi file và có thể giảm thời gian hook. Nhược: chưa có số đo chi phí
   hiện tại; precompile/cache bytecode đã bị D-307 bác vì khoá sha256 nguồn không ràng buộc bytecode (lớp AUD-SEC-074); tách
   guard đụng `PY_LOADER`, `install.py`, `doctor` và adapter ADR-0064 giữa đợt cắt 3.30.0 — rủi ro hàng rào cao, không đo
   được lợi ích.
3. **Nới trần** (hoặc bỏ điều kiện 2×). Rẻ nhất. Nhược: trái ADR-0043 (mở băng cần lý do và cái được đổi lại); trần hiện
   tại còn chỗ nên nới không giải quyết gì, chỉ bỏ tín hiệu.

## Quyết định

Chọn **phương án 1** (D-373):

- Trần `DIR_CAPS` giữ nguyên. Mức tăng `.claude/hooks/` được chấp nhận vì là bản vá an ninh guard (#433–#442).
- Bảng mốc `SIZE_MARKS` trong `tests/test_docs_budget.py`: mỗi nhóm `DIR_CAPS` có ít nhất một mốc (ngày, byte, ADR khai).
  Mốc so là mốc có ngày mới nhất; nhóm > 2× mốc đó là test đỏ. Mốc cũ không xoá.
- Mốc 2026-11-05 chỉ cho `.claude/hooks/` (843 817 B), đo ở `0a2583f`; nhóm không đổi byte tới `742434b` và ở commit thêm
  ADR này. `scripts` và `framework/11-autonomous-loop/` giữ mốc 2026-10-26 (ADR-0050). Ghi chú (review #448): D-373 và
  phương án 1 nêu mốc mới cho cả `scripts`; bỏ phần đó vì `scripts` mới 1,64×, chưa vượt 2× nên chưa có gì để xét lại.
  Đặt mốc sớm sẽ dời điểm báo động lên 2 328 132 B, trên trần. D-373 giữ nguyên vì sổ quyết định chỉ nối thêm.
  `docs/ops/` và `docs/autopilot/` chưa thuộc ADR-0050. Hai nhóm nhận số đo 2026-11-02 (D-314, T-3651) làm mốc; trần riêng
  của chúng (+5 %) vẫn chặt hơn nhiều.
- `T-3709` (trước 2027-01-21, cùng đợt đánh giá sandbox): đo chi phí compile `guard.py` mỗi lệnh Bash ở kích thước hiện tại,
  ghi số thật. Sau đó xét cache bytecode chỉ khi có cách ràng buộc bytecode thoả AUD-SEC-074; không có thì giữ compile từ
  nguồn hoặc đi đường tách.

## Hệ quả

- Tốt: lần vượt 2× kế tiếp đỏ ngay ở PR gây ra nó, không chờ audit. Mỗi lần nâng mốc phải có ADR nêu số đo.
- Xấu: điểm báo động 2× của hooks lùi tới 1 687 634 B, lớn hơn trần 1 417 969 B. Với nhóm này trần lại là chặn chính.
  Bù lại: T-3709 có hạn và có số đo.
- Cổng 2× chỉ chặn trước trần ở hai nhóm: `scripts` (2× = 1 423 648 B, trần 1 760 431 B) và
  `framework/11-autonomous-loop/` (464 594 B, trần 1 280 883 B). Ba nhóm còn lại có 2× mốc nằm trên trần, nên trần là chặn
  chính: `.claude/hooks/` (1 687 634 > 1 417 969), `docs/ops/` (1 543 076 > 810 114) và `docs/autopilot/`
  (671 134 > 352 345).
- Theo dõi: mốc 2027-01-21 của ADR-0050 giữ nguyên; xét lại khi T-3709 có số.
- Đường lùi: nếu T-3709 đo chi phí compile vượt ngân sách hook, tách `guard.py` (ADR riêng; AUD-ARCH-007). Gỡ cổng máy =
  revert commit thêm `SIZE_MARKS` (trần `DIR_CAPS` không phụ thuộc nó).
