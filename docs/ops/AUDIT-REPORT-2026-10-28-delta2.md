# AUDIT-REPORT — Củng cố sau đánh giá, 2026-10-28

> Gốc `main`: `07c428f` (#308); phạm vi tiếp theo là các commit `ce47da2` (corpus), `f4bd90f` (guard/state), `7f8b9a1` (preset) theo PLAN-hardening-assessment-2026-10-28, D-219, ADR-0054/0055. Đây là báo cáo delta; không thay báo cáo lịch sử trước #308.

## Phạm vi và kết quả

- #308 đã sửa AUD-SEC-125/121: test gán nối 3 ca, parallel 4 ca đạt; probe chỉ phân tích chặn 126 và đối chứng an toàn 0. Không chạy thao tác phá hủy.
- Corpus thêm 16 ca, có 4 đối chứng; gỡ hai bảo vệ trong bộ nhớ khiến hai ca tái hiện báo false-green. Benchmark 539 ca, không suy ra an toàn ngoài tập đã kiểm.
- AUD-CODE-025: fallback không khóa của state có thể mất cập nhật. Test mới đỏ trước, sau sửa lỗi trước callback, state không đổi; CLI exit 2, hook Stop giữ cho dừng và ghi lỗi. Đường có flock tiếp tục được kiểm bởi UpdateStateTest/FLOW-07.
- AUD-SEC-129: lỗi nạp/fallback guard từng cho qua hoặc dùng module dở. Canary tái hiện đỏ trước, sau sửa không chạy; no-harness và runtime fallback khỏe giữ tương thích. Rà độc lập còn tái hiện raw `ask` thành allow khi `apply_policy` lỗi ở mặc định: bổ sung canary với fallback thật và sửa đường đó.
- Preset safe là lựa chọn merge/review khi tạo `xt.yaml`, không đổi quyền OS/network. Rà độc lập phát hiện mất provenance có thể làm hạ safe về autonomous; 24 biến thể đỏ trước, sau sửa giữ policy và xuất `.xtemplates-new` nếu khác, không tạo provenance giả.

## Kiểm chứng

| Kiểm | Kết quả đã có |
|---|---|
| doctor trước thay đổi | exit 0, không phát hiện |
| Corpus | 539/539, false-green/false-red 0; 17 test benchmark đạt |
| GuardChokePointTest sau sửa cuối | 17 test đạt; test policy lỗi đỏ trước, xanh sau |
| UpdateStateTest | 18 test đạt; 3 test mới đỏ trước sửa |
| Installer | 96 test đạt; 24 biến thể mất provenance đỏ trước, xanh sau |
| Ruff, mypy strict | đạt trên code thay đổi |
| Full Gate | exit 0: 1.899 test; coverage 13.224 câu lệnh, 4.900 nhánh, 100%; Python 3.12.14. Sàn Python 3.11 bỏ qua có log vì máy không có; lượt đầu phát hiện tiêu đề ADR mới sai định dạng, đã sửa và test ADR xanh |

Hai mục CODE-025/SEC-129 đóng bằng commit `f4bd90f`; không dùng SHA #308 làm bằng chứng cho code mới. Review độc lập chấp thuận sau khi kiểm lại hai lỗi phát hiện thêm; không có phát hiện chặn còn mở trong diff đã rà. Audit strict và verify chạy lại trên cây bàn giao. Corpus chỉ kiểm hàm quyết định; state lock/loader/Gate có file thật được kiểm riêng ở UpdateStateTest/GuardChokePointTest, ghi rõ trong scope.json.

## Giới hạn và bàn giao

- Không đổi mặc định tự chủ của repo hoặc dự án đã cài; không tự bật/tắt sandbox, không cấu hình credential hay quyền persistent.
- Python cục bộ 3.12; browser E2E và ma trận CI sống chưa được xác nhận trong phiên này. Log Gate: `/tmp/xt-hardening-gate-final.log`; kiểm cây bàn giao lưu riêng ngoài repo để không đổi đầu vào đã kiểm.
- Fetch main và Git push dry-run thành công; `gh auth status` trong/ngoài sandbox báo token không hợp lệ, nên không suy ra trạng thái quyền API từ trạng thái Git. Xuất bản chỉ nhánh và PR nháp khi quyền cho phép; kết quả xác minh remote được bàn giao riêng. Không merge, deploy hoặc cắt tag; thay đổi ở Unreleased.
- Chưa thay việc xác nhận pháp lý bằng chuyên gia, pilot nhóm độc lập, hay số liệu ROI. Không tách monolith hoặc tuyên bố tăng tốc khi chưa có ngân sách vi phạm và phép đo phù hợp.
