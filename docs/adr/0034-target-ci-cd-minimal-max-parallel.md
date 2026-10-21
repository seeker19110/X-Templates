# ADR-0034: CI/CD và ruleset dự án đích — tối thiểu khi triển khai ban đầu, song song tối đa

- **Trạng thái:** Đã chấp nhận
- **Trạng thái triển khai:** Đã triển khai trong repo — mẫu `framework/templates/ci.yml` (bỏ job `test-plan`, matrix tĩnh,
  job `e2e`, đóng gói trong `build`, `deploy-staging`), `framework/templates/deploy.yml` (production chạy tay),
  `framework/templates/ruleset-main.json`; `scripts/dev-task.sh` task `test-mode` · `e2e-mode` · `e2e` · `package` ·
  `deploy` · `declared`; `scripts/install.py` `GITHUB_FILES`; test `tests/test_ci_template.py` (`CiTemplateTest`,
  `DeployTemplateTest`, `DevTaskCdTest`), `tests/test_install.py::InstallTest::test_with_github_ruleset_template_minimal_and_parallel`.
- **Ngày:** 2026-10-21
- **Làm rõ:** `WF-CI-024` (fan-out/fan-in), `QA-E2E-020`…`026`, `WF-CI-012`, `BASE-GATE-007`; quyết định D-115, D-116.

## Bối cảnh

Chủ repo yêu cầu (2026-10-21): CI, E2E, CD và ruleset ở dự án đích **tối thiểu khi triển khai ban đầu** và **chạy song
song tối đa**. Bản 3.11 có ba chỗ ngược yêu cầu:

1. CI mẫu có job `test-plan` chạy **trước** mọi shard test (một vòng xếp hàng + checkout trên đường găng).
2. Không có E2E, không có CD trong mẫu: dự án phải tự viết YAML theo `QA-E2E-020…026` và `WF-CI-012` — nhiều mục SHOULD
   (gộp blob, build một lần, chọn theo ảnh hưởng) mà ngày đầu chưa cần.
3. Ruleset mẫu (dùng chung file với repo khung) đòi `dep-audit` — mẫu không có job này nên PR đầu tiên treo — và đòi
   "up to date" (`strict`), nên mỗi lần merge mọi PR khác phải cập nhật rồi chạy lại CI: merge bị tuần tự hoá.

## Quyết định

1. **CI (D-115):** mọi job cổng chạy cùng lúc, matrix **tĩnh** (`test` ×4, `e2e` ×2); mỗi shard tự đọc `xt.yaml` qua
   `dev-task.sh test-mode`/`e2e-mode` và bỏ qua phần không áp dụng có log; `e2e` không `needs: build` (lệnh `e2e` tự build).
   Khoá rỗng ⇒ bỏ qua, trừ `lint`/`test` (D-096 giữ nguyên).
2. **CD (D-115):** push `main` mà `xt.yaml` khai `deploy` ⇒ job `build` đóng gói một lần (`package` + `SHA256SUMS`) song
   song với test; `deploy-staging` (`needs: [build, quality]`, environment `staging`) chạy `deploy` rồi `smoke`; production
   = `deploy.yml` `workflow_dispatch` với `run_id` (job `verify-run` kiểm run: `ci.yml`, push, nhánh mặc định, success,
   cùng repo — rồi mới tới environment `production`); `run_id` cũ = rollback. Không dùng `workflow_run` (zizmor
   `dangerous-triggers`; PR fork mang nhánh tên `main` lọt bộ lọc `branches`).
3. **Ruleset (D-116):** mẫu riêng `framework/templates/ruleset-main.json` — 4 required check có job thật (`quality`,
   `protection-guard`, `gitleaks`, `merge-gate`), `strict_required_status_checks_policy: false`. Quét phụ thuộc là job con
   trong `quality.needs`. Repo khung giữ ruleset riêng (5 check, strict). `BASE-GATE-007` nhận hai cách đạt: strict, hoặc
   không strict kèm CI trên push nhánh mặc định + deploy chỉ từ commit có `quality` xanh.

## Lý do

- Đường găng = job chậm nhất, không cộng thêm job lập kế hoạch; shard thừa thoát sau checkout vài giây.
- Ngày đầu dự án chỉ điền lệnh vào `xt.yaml`; mọi phần chưa dùng bỏ qua có log thay vì phải viết YAML.
- Không strict: N PR xanh merge liên tiếp thay vì N vòng cập nhật + CI nối tiếp. Rủi ro lỗi kết hợp hai PR được chặn
  trước người dùng: CI chạy lại trên `main`, `deploy-staging` cần `quality` xanh của chính commit đó, PR đẩy sau test trên
  merge ref mới.

## Hệ quả

- Dự án không chia shard tốn thêm 3 job test + 1 job e2e ngắn mỗi run (vài giây mỗi job, phút tính tiền làm tròn lên ở
  repo private) — đổi lấy wall time.
- `main` có thể đỏ trong khoảng giữa hai merge; deploy dừng tới khi sửa/revert.
- `smoke` có nghĩa mới: kiểm sau deploy với `XT_DEPLOY_ENV`. Dự án đích: chạy lại `install.py --with-github` (file đã sửa
  ra `.xtemplates-new`), import lại ruleset nếu muốn bỏ `dep-audit`/strict.

## Đường lùi

Revert PR. Dự án đích: đặt `strict_required_status_checks_policy: true` (một dòng JSON); xoá `deploy.yml`/job
`deploy-staging`; đưa job `test-plan` từ bản 3.11.1 về — mẫu là copy-if-absent nên dự án đã cài không bị đổi.
