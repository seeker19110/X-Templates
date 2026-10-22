# ADR-0042: `release-check` chạy tấn công thử (`attack`) và kiểm tải (`perf`) trước phát hành

- **Trạng thái:** Đã chấp nhận (chủ repo 2026-10-22: "pha production mới audit, tấn công tìm lỗ hổng, tối ưu hiệu năng")
- **Trạng thái triển khai:** Đã triển khai — `scripts/xt.py` `RELEASE_RUN_KEYS`, `_release_run`, hàng `attack`/`perf` của
  `release_check`; mẫu `framework/templates/xt.yaml`; bảng khoá ở `framework/11-autonomous-loop/harness-files.md`; test
  `tests/test_xt_cli.py::ReleaseCheckTest::test_release_attack_and_perf_rows`.
- **Ngày:** 2026-10-22
- **Làm rõ:** ADR-0029 (`release-check` G7 máy đọc), ADR-0031/0041 (pha build gọn, kiểm dồn về harden), `SEC-WEB-016`
  (DAST trước phát hành), `STD-API-013` (fuzz API), `framework/11-autonomous-loop/optimization-loop.md` (vòng tối ưu).

## Bối cảnh

Sau ADR-0041, pha build chỉ còn CI xanh; mọi kiểm nặng dồn về harden. `release-check` đã gom blueprint, sổ audit (13 nhóm,
gồm bảo mật — rà đọc mã), kiểm lại cuối, cây git, pha và nợ review — nhưng không có hàng nào **chạy** thử tấn công hay đo tải.
Các mục blueprint `SEC-WEB-016`/`STD-API-013`/hiệu năng chỉ được tick nếu dự án tự viết `— Kiểm:`; không có chỗ máy đòi.

## Quyết định

1. Hai khoá mới của `xt.yaml`: `attack` (tấn công thử — DAST/fuzz/kịch bản khai thác trên bản chạy cục bộ hay staging) và
   `perf` (kiểm tải có ngưỡng, đỏ khi vượt ngân sách). Dự án chọn công cụ; khung không đoán tên công cụ (như sàn Gate).
2. `release-check` thêm hàng `attack`, `perf`: lệnh khai → chạy qua guard (`run_gate_shell`), exit 0 PASS, khác FAIL
   (BLOCKER → NO-GO); chưa khai/no-op ở quy mô M/L → N/A BLOCKER (`GO (chờ người)` — người ký lý do không áp ở
   `GO-NO-GO.md`); quy mô S/không rõ → N/A SHOULD.
3. Lỗ tìm được và vượt ngân sách đi đúng đường đã có: 🔴/🟠 vào sổ audit (`/audit`, xác minh đối kháng) thành task; vượt
   ngân sách → `optimization-loop.md` (`perf sample`/`compare`/`guard`).

## Lý do

- Máy đòi điều chủ repo muốn ở production, không thêm cổng nào vào pha build.
- Không tự chọn công cụ: dự án web dùng ZAP/Schemathesis/k6, CLI hay thư viện dùng fuzz/benchmark riêng — khoá + lệnh là
  giao ước chung (P1: bằng chứng là exit code).

## Phương án đã cân nhắc

- **Chỉ thêm mục checklist**: không có máy đòi, dễ tick tay. Loại.
- **Gắn công cụ cố định (ZAP + k6) vào CI mẫu**: sai cho dự án không phải web, cần dịch vụ chạy. Loại.

## Hệ quả

- Dự án M/L phải khai `attack`/`perf` hoặc ký lý do không áp mới có GO trọn vẹn.
- `release-check` chạy lâu hơn (thời gian của hai lệnh); trần `XT_RECORD_TIMEOUT` áp dụng.

## Đường lùi

Revert; hoặc để trống hai khoá (M/L thành việc người ký).
