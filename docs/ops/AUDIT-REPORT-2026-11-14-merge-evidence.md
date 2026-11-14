# Audit TEST/HAR delta — 2026-11-14

Snapshot `5d34bb7b` (#558); phạm vi là thay đổi chính sách merge, không phải toàn bộ TEST/HAR. Hai nhóm giữ trạng thái chưa quét. CI #558 đo 24.629 dòng và 9.004 nhánh, 100% trên cây trùng `main`; coverage không chứng minh mọi hành vi.

- **AUD-HAR-407 🔴:** REST giả trả 403 khi đọc rules; PR BLOCKED chỉ có lint xanh vẫn cho `merge`. Cùng PR khi API báo context bắt buộc vắng thì không merge. Tái hiện qua CLI bằng hai fixture độc lập, Python 3.15.2; chưa thử vượt GitHub thật.
- **AUD-HAR-408 🔴:** rule giả ghim `quality` vào app 42 nhưng status thiếu nguồn được tính xanh; app 43 bị từ chối. [GitHub REST rules](https://docs.github.com/en/rest/repos/rules?apiVersion=2026-03-10) định nghĩa `integration_id` là nguồn bắt buộc. Ruleset sống có bốn check ghim app và không có actor bypass; chưa chứng minh merge thật có thể vượt ruleset.
- **AUD-HAR-409/410 🟠:** sai giá trị `merge_review` không báo; tài liệu còn mô tả review và thứ tự cũ. **AUD-TEST-106 🟢:** test event optional chưa phát hiện mutation chỉ xét PR gây sự kiện.
- **AUD-TEST-061/105 🟢:** #554 thêm SARIF CodeQL clean có nguồn; #546 sửa phép đo theo cặp. Bảy test fixture và đồng hồ giả đạt; fixture CodeQL chỉ chứng minh mẫu clean.

Xác minh đối kháng: hai fixture CLI độc lập chạy trên Python 3.15.2 tái hiện 407/408; API và PR là giả, không merge thật. `harness-check` exit 0; doctor exit 1 vì môi trường không bật sandbox. `tests.test_ci_template tests.test_install_new tests.test_merge.GreenMergePolicyTest`: 82 test đạt. Giới hạn: chưa rà toàn bộ delta TEST/HAR; giữ nhóm chưa quét.

Kế hoạch: D-488 xử lý 407/408 và thiếu context trước; sau đó sửa 409/410, bổ sung test 106. Không nới check hoặc ruleset. Các PR riêng chạy gate và CI; dự án đích đang tạm dừng.
