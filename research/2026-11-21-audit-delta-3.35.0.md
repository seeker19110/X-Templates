# Audit delta ngày 21/11/2026 (cổng ký 3.35.0)

Mốc rà là `main` tại `29ddf2d85a1c`; phần sửa vào `main` ở `51d4e6cd` (#710, #711, #712). Diff tích luỹ từ lần quét trước `4439d48`: 123 tệp, 10 581 dòng thêm. Năm reviewer độc lập (năng lực cao hơn người viết, `LOOP-ORCH-005`) chỉ đọc, mỗi lô một lượt; không lô nào kết luận sạch hoàn toàn vì hết trần lượt, nên cột "Chưa rà" ghi rõ. [Sổ audit](../docs/ops/AUDIT-STATUS.md).

## Lô và kết quả

| Lô | Phạm vi | 🔴 | 🟠 | 🟢 | Chưa rà |
|---|---|---|---|---|---|
| A | `guard.py` và hook, skill/agent, `test_hooks`, oracle guard, fixture | 0 | 0 | 5 | `test_guard_release_oracle.py` chi tiết, `guard.json`, chế độ strict, bench |
| B | `xt.py` làn merge/derived/steward, `xt_derived.py`, test merge | 0 | 1 | 1 | ~600 dòng `xt.py` ngoài làn merge (factory, stage, deploy preview, perf) |
| C | `xt_distribution/acceptance/deploy/scale/field`, test release | 0 | 3 | 1 | 8 tệp test mới chỉ chạy, chưa đọc; `test_perf` |
| D | workflow, `install.py`, mẫu dự án đích, `doctor`/`admin-plan` | 0 | 2 | 2 | `test_install*.py` chi tiết, `routine-check`, `field-export` |
| E | tài liệu khung, ADR 0081–0087, CHANGELOG, mẫu | 0 | 3 | 6 | ADR-0081…0085 so với mã, `docs/ops/FACTORY-PILOT-1*`, `packs/**` |

Tổng thô 9 🟠 gồm hai cặp trùng giữa lô C và D (`upgrade open-pr`, `xt-field.yml` mở PR bằng `GITHUB_TOKEN`) nên các lô cho 7 dòng 🟠 duy nhất; dòng thứ 8 (AUD-HAR-458) đến từ review #711.

## Phát hiện đã sửa trước khi ký (sổ: dòng `đã sửa` kèm PR)

- **AUD-XFEAT-051 (🟠, có từ trước, #710):** PR fork thường ở L2/L3 với CI xanh ra `merge`; nay `human`; làn `derived` giữ `wait`.
- **AUD-CI-038, AUD-HAR-457, AUD-XFEAT-052 (🟠, #711):** `upgrade open-pr` không chạy xong ở dự án thật; token steward lọt vào hook `push`; bản thu hồi giữ PR mở.
- **AUD-CI-039 (🟠, #711):** job lịch luôn bị bỏ qua, `xt-field.yml` mở PR bằng `GITHUB_TOKEN`; review #711 thêm điều kiện loại tag trùng tên nhánh mặc định. **AUD-HAR-458 (🟠, có từ trước, #711):** `pr-steward.yml` checkout không có `ref:` nên dispatch trên ref khác chạy mã ref đó với `XT_STEWARD_TOKEN`; nay luôn checkout nhánh mặc định.
- **AUD-DOC-308, AUD-DOC-309 (🟠, #710/#712):** tài liệu `--with-github`; `WF-REVIEW-007` lệch ADR-0079 (D-533). **AUD-DOC-310 (🟢):** sáu mục tài liệu.
- Lô A: năm 🟢 và lô B/C/D còn lại 🟢 ghi ở AUD-HAR-456, AUD-CI-037, AUD-XFEAT-050 (mở) hoặc đã gộp vào các dòng trên.

## Nợ ghi sổ (không chặn bản)

- 🟠 chấp nhận tới 2027-01-21: AUD-HAR-452, AUD-HAR-453 (D-532: `gh` sau trình bọc chưa mô hình; `"$@"` qua `bash -s`; cùng họ D-332, có từ trước); AUD-HAR-454, AUD-CI-036 (D-534: guard chỉ `ask` khi agent làm trái `pr next` với PR derived/fork — làn derived do #709 thêm; fork khung đổi tên repo lệch tên archive — do #708, an toàn).
- 🟢 mở: AUD-HAR-455/456, AUD-CI-037, AUD-DOC-307, AUD-XFEAT-050, AUD-TEST-135.

## Điều chưa xác minh

Hành vi trên GitHub thật: `commit_message` của REST merge thay hay nối thân; PR từ fork đã xoá còn merge được không; payload `schedule` thiếu `repository` (suy từ tài liệu nền tảng, điều kiện mới đúng cả hai trường hợp). Chưa chạy `upgrade open-pr` trên một dự án đích thật với `XT_STEWARD_TOKEN`; việc này nằm trong kế hoạch nâng 3.35.0 vào các dự án đích.
