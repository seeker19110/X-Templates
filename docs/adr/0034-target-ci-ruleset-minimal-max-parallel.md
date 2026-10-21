# ADR-0034: CI, E2E và ruleset dự án đích — tối thiểu khi triển khai ban đầu, song song tối đa

- **Trạng thái:** Đã chấp nhận; ruleset mẫu dự án đích 3 check → 2 check (`quality`, `gitleaks`) theo ADR-0036 (2026-10-21)
- **Trạng thái triển khai:** Đã triển khai trong repo — mẫu `framework/templates/ci.yml` (bỏ job `test-plan`, matrix tĩnh,
  job `e2e`, `protection-guard` vào `quality.needs`), `framework/templates/ruleset-main.json`; `scripts/dev-task.sh` task
  `test-mode` · `e2e-mode` · `e2e`; `scripts/install.py` `GITHUB_FILES`; test `tests/test_ci_template.py`
  (`CiTemplateTest`, `DevTaskCiModeTest`), `tests/test_install.py::InstallTest::test_with_github_ruleset_template_minimal_and_parallel`.
- **Ngày:** 2026-10-21
- **Làm rõ:** `WF-CI-024` (fan-out/fan-in), `QA-E2E-020`…`026`, `BASE-GATE-007`, `WF-CI-001`, `WF-GIT-002`; quyết định
  D-115, D-116, D-117.

## Bối cảnh

Chủ repo yêu cầu (2026-10-21): CI, E2E và ruleset ở dự án đích **tối thiểu khi triển khai ban đầu** và **chạy song song
tối đa**; CD **không** thuộc phạm vi ("bỏ cd" — bản nháp đầu của PR có mẫu CD, đã gỡ). Bản 3.11 có ba chỗ ngược yêu cầu:

1. CI mẫu có job `test-plan` chạy **trước** mọi shard test (một vòng xếp hàng + checkout trên đường găng).
2. Không có E2E trong mẫu: dự án phải tự viết YAML theo `QA-E2E-020…026` — nhiều mục SHOULD (gộp blob, build một lần,
   chọn theo ảnh hưởng) mà ngày đầu chưa cần.
3. Ruleset mẫu (dùng chung file với repo khung) đòi `dep-audit` — mẫu không có job này nên PR đầu tiên treo — đòi
   `protection-guard` như check riêng, và đòi "up to date" (`strict`), nên mỗi lần merge mọi PR khác phải cập nhật rồi
   chạy lại CI: merge bị tuần tự hoá.

## Quyết định

1. **CI (D-115):** mọi job cổng chạy cùng lúc, matrix **tĩnh** (`test` ×4, `e2e` ×2); mỗi shard tự đọc `xt.yaml` qua
   `dev-task.sh test-mode`/`e2e-mode` và bỏ qua phần không áp dụng có log; `e2e` không `needs: build` (lệnh `e2e` tự build).
   Khoá rỗng ⇒ bỏ qua, trừ `lint`/`test` (D-096 giữ nguyên). Chỉ còn hai fan-in bắt buộc: `coverage` (gộp dữ liệu shard để
   đòi đúng ngưỡng) và `quality` (một required check).
2. **Ruleset (D-116, D-117):** mẫu riêng `framework/templates/ruleset-main.json` — giữ cấm xoá, cấm force-push, PR bắt
   buộc (squash, resolve thread), `bypass_actors: []`; 3 required check có job thật: `quality`, `gitleaks` (bí mật lộ là
   không đảo ngược), `merge-gate` (chặn auto-merge ngoại lệ cứng, ADR-0023); `protection-guard` và quét phụ thuộc là job
   con trong `quality.needs`; `strict_required_status_checks_policy: false`. Repo khung giữ ruleset riêng (5 check,
   strict). `BASE-GATE-007` nhận hai cách đạt: strict, hoặc không strict kèm CI chạy lại trên push nhánh mặc định.
3. **CD:** không có mẫu; dự án tự viết theo `WF-CI-012`/`WF-CI-013` khi có môi trường deploy.

## Lý do

- Đường găng = job chậm nhất, không cộng thêm job lập kế hoạch; shard thừa thoát sau checkout vài giây.
- Ngày đầu dự án chỉ điền lệnh vào `xt.yaml`; mọi phần chưa dùng bỏ qua có log thay vì phải viết YAML.
- `protection-guard` chỉ chặn lỗi cấu hình làm PR treo chờ check không có (fail-closed), nên làm job con không mở lỗ.
- Không strict: N PR xanh merge liên tiếp thay vì N vòng cập nhật + CI nối tiếp. Lỗi kết hợp hai PR bị CI trên `main` bắt;
  PR đẩy sau đó test trên merge ref mới.

## Hệ quả

- Dự án không chia shard tốn thêm 3 job test + 1 job e2e ngắn mỗi run (vài giây mỗi job; phút tính tiền làm tròn lên ở
  repo private) — đổi lấy wall time.
- `main` có thể đỏ trong khoảng giữa hai merge; sửa/revert trước khi merge PR khác, deploy (nếu dự án có) chỉ từ `main` xanh.
- `e2e` đổi nghĩa: CI nay chạy nó (trước: chỉ agent chạy tay). Dự án đã khai `e2e` mà runner thiếu trình duyệt/server thì
  khai `e2e_setup`, hoặc để `e2e: ""` tới khi sẵn sàng.
- Dự án đích: chạy lại `install.py --with-github` (file đã sửa ra `.xtemplates-new`), import lại ruleset để có 3 check, không
  strict.

## Đường lùi

Revert PR. Dự án đích: đặt `strict_required_status_checks_policy: true` (một dòng JSON) hoặc thêm lại context
`protection-guard`; đưa job `test-plan` từ bản 3.11.1 về — mẫu là copy-if-absent nên dự án đã cài không bị đổi.
