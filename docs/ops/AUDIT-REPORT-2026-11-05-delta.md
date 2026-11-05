# AUDIT-REPORT — X-Templates · 2026-11-05 (delta)

> Mốc quét `23447d8..6086e69` trên `main` (PR #435–#445), cộng hai PR sửa [#446](https://github.com/seeker19110/X-Templates/pull/446) và [#447](https://github.com/seeker19110/X-Templates/pull/447) (D-371, D-372). Task T-3557, trước cắt 3.30.0. Ba nhóm auditor độc lập: SEC/CFG/CI · XFEAT/DOC/HAR · CODE/TEST/PERF/DEP. Kết quả theo ID ở [sổ audit](AUDIT-STATUS.md).

## 1. Tóm tắt

| Mức | Nguồn | Số | ID | Trạng thái |
|---|---|---:|---|---|
| 🔴 | audit delta | 0 | — | — |
| 🟠 | audit delta | 5 | AUD-HAR-280…284 | đã sửa #447 |
| 🟢 | audit delta | 5 + 13 | AUD-HAR-285…289 · AUD-DOC-260/261, AUD-DEP-020, AUD-TEST-080…083, AUD-PERF-020…025 | HAR đã sửa #447; phần B đã sửa #446 trừ mục mở ở §4 |
| 🔴 | review #446/#447 | 3 | AUD-TEST-084, AUD-HAR-290, AUD-HAR-291 | đã sửa trong PR |
| 🟠 | review #446/#447 | 3 | AUD-TEST-085, AUD-HAR-292, AUD-HAR-293 | đã sửa trong PR |
| 🟢 | review #447, rà sau | 4 | AUD-HAR-294…297 | mở |
| 🟠 | audit ARCH (D-373) | 1 | AUD-ARCH-009 | đã sửa #448 (ADR-0072) |
| 🟢 | audit ARCH | 5 | AUD-ARCH-010…014 | mở |

Năm 🟠 đều nằm ở `perf trial` (ADR-0071) và đều tái hiện được trước khi sửa:

- **F1 · AUD-HAR-280** — vòng `/optimize` không tới `done`: tick PLAN/PROGRESS/DECISIONS sau lần giữ làm `perf trial status --check` exit 1 "commit lạ".
- **F2 · AUD-HAR-281** — `perf trial start` exit 2 khi PLAN-opt và D-NNN đã commit trên nhánh như skill yêu cầu.
- **F3 · AUD-HAR-282** — file mới của candidate trùng tên mô-đun (`unittest.py`) che runner của `equiv`, mã sai được giữ.
- **F4 · AUD-HAR-283** — Gate dự phòng `bash <(git show …:scripts/perf-gate.sh)` bị guard chặn (AUD-SEC-310), không chạy qua `loop record`.
- **F5 · AUD-HAR-284** — `trial_verdict` không có test bắt đảo luật giữ (đột biến M01/M02 sống).

Review #447 tìm thêm hai 🔴 lách phần miễn sổ sách của bản sửa F1 (symlink vào `docs/autopilot/`, kể cả symlink treo). D-372 thu hẹp phần miễn về file sổ sách thường. Review #446 tìm 🔴 AUD-TEST-084: `ratio=40` cho lọt đột biến bậc hai, tức nới cổng (`LOOP-CI-001`). Tỉ lệ đã trả về mặc định 10.

## 2. Phạm vi

`audit plan` nhận diện 578 tệp, 65 tệp test và 11 workflow. Có 12 nhóm áp dụng. Nhóm DATA là N/A vì repo không có migration, SQL hay schema CSDL. Mười nhóm của ba auditor nay có SHA quét `0a2583f`, là `main` sau #447. Phần `23447d8` trở về trước được phủ bởi delta 2026-11-04 và review PR sạch (ADR-0057). ARCH được quét sau, riêng một lượt (`9f123b1..0a2583f`), nay cũng ở `0a2583f`. A11Y giữ SHA cũ vì lượt này không đổi UI.

## 3. Lệnh đã chạy ở cây cắt bản

| Lệnh | Exit | Kết quả |
|---|---:|---|
| `python3 scripts/xt.py audit check docs/ops/AUDIT-STATUS.md --strict` | 0 | 0 🔴/🟠 `mở` |
| `python3 scripts/xt.py blueprint-status BLUEPRINT.md --strict --run` | 0 | MUST 64 đạt · 6 miễn · 0 chưa; 68 lệnh kiểm xanh |
| `python3 scripts/xt.py autonomy-bench` | 0 | 1776 ca, false-green 0, chặn oan 0 |
| `scripts/dev-task.sh gate` | 1 | build, `mypy --strict`, lint xanh; 2738 test OK. Coverage cục bộ 99 % vì `coverage` nằm ở site người dùng, còn hook gọi `python3 -I`. CI `0a2583f` đạt 100 % |

## 4. Nợ 🟢 còn mở

| Mục | Chủ | Rà lại |
|---|---|---|
| AUD-HAR-294…297 · che mô-đun ngoài Python và src-layout, test điểm nóng thoát sớm, symlink tuyệt đối ra ngoài cây | `perf trial` | audit kế |
| AUD-TEST-082 · `-n 0` trong cấu hình chưa được coi là tắt xdist; AUD-TEST-083 · test phụ thuộc đường venv | `dev-task.sh`, bộ test | audit kế |
| AUD-ARCH-010…014 · `xt.py` một file bị ADR-0071 khoá, cờ chế độ ngầm và flock thiếu dịch errno, danh sách tên biến lệch trong guard, sổ `perf trial` chưa có đường nâng schema, adapter gọi API private của guard | kiến trúc | audit kế |
| AUD-PERF-020…023 · chi phí duyệt cây, lỗi candidate ra exit 2, thư mục tạm sót, chỉ số phụ không có held-out; AUD-PERF-025 · CI chậm hơn 28 % | `perf trial`, CI | audit kế |

AUD-HAR-296 là suy luận từ cách F3 xét tên ở gốc cây. AUD-HAR-297 có từ trước D-371 và đã được nêu ở review #447. Cả hai chưa tái hiện.

## 5. Nhóm ARCH (D-373)

`.claude/hooks/` đạt 843 817 B, gấp 2,28 lần mốc 2026-10-26 (369 274 B). Nhóm vượt 2× từ `024ee79` (#433). ADR-0050 đòi ADR xét lại khi điều đó xảy ra, nhưng chưa có ADR và cũng không có cổng máy nào bắt (AUD-ARCH-009 🟠). Bản sửa ở #448 gồm [ADR-0072](../adr/0072-review-dir-caps-after-2x.md) và cổng `SIZE_MARKS` trong `tests/test_docs_budget.py`. ADR-0072 giữ trần, đặt mốc 2026-11-05 cho `.claude/hooks` và `scripts`. Cổng đỏ khi một nhóm vượt 2× mốc gần nhất. Chi phí compile `guard.py` mỗi lệnh Bash chưa đo, giao T-3709.
