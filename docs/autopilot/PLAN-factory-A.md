# PLAN-factory-A.md — ADR-0068 lát A · hợp đồng kết quả/phát hành có kiểu

> Lập 2026-11-05 trên nhánh `claude/amazing-brahmagupta-9jqbg1` (chủ dự án: "hoàn thiện cho xong hết", không mở PR, không
> merge). Duyệt: D-350 (phạm vi: chỉ hợp đồng phát hành; evidence v2 của `loop record` giữ nguyên). Nguồn:
> [ADR-0068](../adr/0068-software-factory-direction.md) §Quyết định A + §Xác nhận A; research
> [`2026-11-04-software-factory-direction.md`](../../research/2026-11-04-software-factory-direction.md) §6–§7.
> Không chen mốc 3.30.0 của `main` (research §7): lát làm trên nhánh, chưa merge.
>
> **Cú pháp bắt buộc cho máy:** mỗi task một dòng `- [ ] \`T-NNNN\` <việc> — Gate: \`<lệnh>\``.

## Tóm tắt (cổng duyệt)
- Hợp đồng: `release-check --json` thêm `schema: 3`, `subject` (head, vân tay cây, digest artifact), `artifacts[]`,
  `results[]` (adapter đọc report), `promotion` (`approved` · `pending_human` · `rejected` · `blocked` + `reasons`).
  **Giữ** `go`/`verdict`/`human`/`fails`/`rows` và exit code (`go` → 0); `signoff-package` đọc như cũ.
- Khoá `xt.yaml` mới, tuỳ chọn (vắng = hành vi cũ): `<key>_report` cho mỗi khoá `RELEASE_RUN_KEYS` (đường report do lệnh
  sinh, nhận dạng theo nội dung: JUnit XML, SARIF 2.1.0, `pip-audit` JSON); `release_artifacts` (đường file cách nhau bởi
  khoảng trắng, sidecar `<file>.sha256` nếu có); `release_approval_days` (mặc định 30).
- Luật promotion: hàng BLOCKER FAIL → `blocked`; dòng ký §5 có quyết định NO-GO → `rejected`; còn N/A BLOCKER, chữ ký quá
  hạn, hoặc có digest mà GO-NO-GO không nhắc 12 ký tự đầu → `pending_human`; còn lại → `approved`. Máy không tự nâng
  `pending_human` (ADR-0068 câu 3).
- Ca phải từ chối (§Xác nhận A): sai digest, report thiếu, report cũ hơn lần chạy, 0 test, scan chưa xong, approval chờ/từ
  chối/hết hạn → `promotion ≠ approved`; ca dương: JUnit/SARIF/pip-audit sạch + GO-NO-GO ký còn hạn, nhắc digest →
  `approved`.

## Ngân sách (4 con số)
- Số vòng tối đa: bỏ trống · Chi phí: 0 đồng ngoài phiên · Timeout Gate: 1200 giây · Hạn: 24 giờ

## Điểm dừng bắt buộc về hành động
- Mở PR, merge, cắt bản: không làm (chủ dự án 2026-11-05). Ký GO-NO-GO: việc người.

## Task
- [x] `T-3673` Adapter report (`report_result`): JUnit XML (testcase/failure/error/skipped, 0 test chạy = FAIL), SARIF
  (run không có/`executionSuccessful: false` = chưa xong, `level: error` = FAIL), `pip-audit` JSON (vuln = FAIL, 0 gói hoặc
  mọi gói bị bỏ qua = chưa xong), dạng lạ/hỏng = INCONCLUSIVE — Gate: `python3 -m unittest tests.test_release_contract.ReportAdapterTest`
- [x] `T-3674` `_release_run` đọc `<key>_report`: exit 0 mà report thiếu, cũ hơn lúc chạy, hay kết quả khác PASS → hàng
  FAIL; kết quả vào `results[]` (kèm sha256 report); khoá vắng → như cũ (sau: T-3673) — Gate: `python3 -m unittest tests.test_release_contract.ReleaseReportTest`
- [x] `T-3675` `release_artifacts` → hàng `artifacts` (chỉ khi khai): thiếu file / sidecar lệch digest → FAIL BLOCKER;
  `subject` + `artifacts[]` trong JSON — Gate: `python3 -m unittest tests.test_release_contract.ReleaseArtifactTest`
- [x] `T-3676` `promotion` + `schema: 3` (sau: T-3674, T-3675): luật ở §Tóm tắt; text in dòng `promotion:`; test cũ của
  `release-check`/`signoff-package` không đổi kỳ vọng — Gate: `python3 -m unittest tests.test_release_contract.PromotionTest tests.test_xt_cli.ReleaseCheckTest`
- [x] `T-3677` Tài liệu: mẫu `framework/templates/xt.yaml` (khoá mới, ghi chú), nhà `release-check` ở khung, ADR-0068
  trạng thái triển khai lát A, CHANGELOG (sau: T-3676) — Gate: `scripts/dev-task.sh gate-fast`
