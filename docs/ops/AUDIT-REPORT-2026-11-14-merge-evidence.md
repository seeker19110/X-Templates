# Audit TEST/HAR delta — 2026-11-14

Snapshot `5d34bb7b` (#558); phạm vi là thay đổi chính sách merge, không phải toàn bộ TEST/HAR. Hai nhóm giữ trạng thái chưa quét. CI #558 đo 24.629 dòng và 9.004 nhánh, 100% trên cây trùng `main`; coverage không chứng minh mọi hành vi.

- **AUD-HAR-407 🔴:** REST giả trả 403 khi đọc rules; PR BLOCKED chỉ có lint xanh vẫn cho `merge`. Cùng PR khi API báo context bắt buộc vắng thì không merge. Tái hiện qua CLI bằng hai fixture độc lập, Python 3.15.2; chưa thử vượt GitHub thật.
- **AUD-HAR-408 🔴:** rule giả ghim `quality` vào app 42 nhưng status thiếu nguồn được tính xanh; app 43 bị từ chối. [GitHub REST rules](https://docs.github.com/en/rest/repos/rules?apiVersion=2026-03-10) định nghĩa `integration_id` là nguồn bắt buộc. Ruleset sống có bốn check ghim app và không có actor bypass; chưa chứng minh merge thật có thể vượt ruleset.
- **AUD-HAR-409/410 🟠:** sai giá trị `merge_review` không báo; tài liệu còn mô tả review và thứ tự cũ. **AUD-TEST-106 🟢:** test event optional chưa phát hiện mutation chỉ xét PR gây sự kiện.
- **AUD-TEST-061/105 🟢:** #554 thêm SARIF CodeQL clean có nguồn; #546 sửa phép đo theo cặp. Bảy test fixture và đồng hồ giả đạt; fixture CodeQL chỉ chứng minh mẫu clean.

Xác minh đối kháng: hai fixture CLI độc lập chạy trên Python 3.15.2 tái hiện 407/408; API và PR là giả, không merge thật. `harness-check` exit 0; doctor exit 1 vì môi trường không bật sandbox. `tests.test_ci_template tests.test_install_new tests.test_merge.GreenMergePolicyTest`: 82 test đạt. Giới hạn: chưa rà toàn bộ delta TEST/HAR; giữ nhóm chưa quét.

Kế hoạch: D-488 xử lý 407/408 và thiếu context trước; sau đó sửa 409/410, bổ sung test 106. Không nới check hoặc ruleset. Các PR riêng chạy gate và CI; dự án đích đang tạm dừng.

## Delta harden tại e0745c07 (D-490)

- CI trên main run 43605248555 xanh; 226 test merge/app, 52 test steward/CI, 22 test bench đều exit 0. Bench đạt 2.684 ca, 0 false-green. Đây là quét lát #558–#566; TEST/HAR vẫn chưa quét đủ nhóm.
- T-3890: kiểm độc lập bằng lỗi I/O giả trên tệp mẫu cho thấy snapshot lỗi vẫn chạy formatter và restore lỗi mất bản sao. Sửa ở điểm vào formatter của khung; AUD-SEC-648 vẫn mở cho formatter gọi trực tiếp.
- T-3891: README, skill complete và runbook còn mô tả review cũ. Đối chiếu `GreenMergePolicyTest` 7/7 và ruleset sống ngày 2026-11-14.
- Nợ test mức xanh: kiểm thứ tự qua hai chữ số, cách ly GITHUB_STEP_SUMMARY và ghim điều kiện review vào đúng mệnh đề LOOP-STOP-002.

## T-3892 tại 4a3e7947

- TEST: CI 43610149568 xanh, 3.423 unit test, 8 E2E, 100 % dòng/nhánh. Hai lượt rà tập trung đạt 336 và 168 test. Đã rà cấu trúc 64 tệp đổi, chưa kiểm từng assertion/corpus và 84 miễn trừ mới. AUD-TEST-107/108 được xác minh độc lập với XML/corpus tạm.
- HAR: rà 10/11 tệp kể từ 454d146; còn nội bộ guard và bằng chứng cũ. Hai lượt test đạt 96 và 62 ca. AUD-HAR-401/406 tái hiện; AUD-HAR-411 xác minh độc lập. Không nâng SHA quét TEST/HAR.
- D-492/T-3867: giả lập RecursionError với lệnh vô hại. Kiểm độc lập cả hai lượt đọc, hook, adapter và Gate. Không kết luận đóng các mục đỏ khác.
