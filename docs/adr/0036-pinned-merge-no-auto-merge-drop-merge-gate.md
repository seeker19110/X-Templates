# ADR-0036: Máy chỉ merge ghim head, không dùng auto-merge của GitHub; bỏ required check `merge-gate`

- **Trạng thái:** Đã chấp nhận (chủ repo chọn 2026-10-21, D-122 — ghi đè D-120/D-121); thay ADR-0023 và ADR-0035 (không triển khai tiếp);
  đổi **cơ chế** của ADR-0015, ADR-0024, ADR-0025, ADR-0027 (luật làn, ngoại lệ cứng, review sạch ở head giữ nguyên) — bảng ở §Ảnh hưởng.
- **Trạng thái triển khai:** Lát 0 của `docs/autopilot/PLAN-3.13-next-level.md` (T-1805…T-1810); stub `merge-gate.yml` xoá ở T-1834 sau khi chủ
  repo gỡ context khỏi ruleset sống của ba repo. Cập nhật dòng này khi PR merge.
- **Ngày:** 2026-10-21
- **Làm rõ:** ADR-0014 (merge ghim head là luật gốc), ADR-0028 (một điều kiện merge), ADR-0034 (ruleset dự án đích);
  quyết định D-119…D-122; nghiên cứu `research/2026-10-21-next-level-speed-automation-quality.md` §4.2 (K-1).

## Bối cảnh

- Required check `merge-gate` (ADR-0023) chỉ tồn tại vì **auto-merge của GitHub không ghim head**: bật auto-merge trên PR sạch rồi push commit
  chạm ngoại lệ cứng thì GitHub vẫn merge khi check xanh. Mọi lớp đỡ sau đó (`pull_request_target`, ADR-0035 `workflow_run` + check-run
  REST, steward đánh giá lại D-119, chuyển tiếp hai trigger D-120) đều là chi phí để giữ được auto-merge.
- GitHub chặn mặc định `pull_request_target` ở repo public từ 2026-11-02 (K-1): `merge-gate.yml` hiện tại ngừng báo → mọi PR treo ở ba repo
  đã cài. Hướng A (ADR-0035) cần ~500 dòng mã mới, hai PR, và dựa trên giả định chưa xác minh (ruleset tính check-run tạo qua API là context
  bắt buộc; GitHub tính check-run nào khi một head có nhiều cái cùng tên).
- Chủ repo hỏi "có bảo đảm code nhanh, ruleset tối thiểu không?" và chọn phương án bỏ hẳn (D-122). Máy đã có sẵn đường merge ghim head:
  `pr next` → `merge` (`gh pr merge --match-head-commit` / REST `sha=` / MCP `expectedHeadSha`), steward `PUT pulls/N/merge` `sha=<head>`.

## Quyết định

1. **Máy không bao giờ bật auto-merge của GitHub.** Mọi đường merge của máy (phiên agent qua `pr next`, `pr-steward --apply`) là merge
   **ghim head** sau khi `merge-check` = `merge` ở đúng head đó. CI chưa xong → `wait` (`merge-watch` của phiên chờ; steward chạy lại theo
   `workflow_run` của `CI` xong và lịch 10 phút). Luật làn (ADR-0024/0025), ngoại lệ cứng (ADR-0016/0020), review sạch ở head (ADR-0032),
   nhãn `xt-standard-lane`, `merge_autonomy` L1/L2/L3, cập nhật nhánh tụt (D-061) **giữ nguyên** — chỉ cơ chế đổi: L3 = máy merge ghim head
   mọi làn (nhanh khi CI xanh, chuẩn khi CI xanh + review sạch ở head); L2 chỉ làn nhanh; L1 người merge.
2. **`pr next`:** bỏ hành động `enable-auto-merge` và khoá `fallback`. Auto-merge đang bật (chỉ có thể do người bật): verdict `merge` → `merge`
   ghim head ngay (D-063 giữ: ghim head an toàn hơn chờ GitHub); mọi trường hợp khác → `disable-auto-merge` (dọn dẹp — không để auto-merge
   treo trên PR chưa đủ điều kiện). Bỏ nhánh `base_has_required` (D-062 hết đối tượng — không còn auto-merge để kìm; CI làm bằng chứng đã do
   `merge-check` đòi, `NON_CI_CHECKS`) cùng `_base_has_required`/`baseHasRequired`.
3. **Guard chặn phẳng việc bật auto-merge** ở mọi mức tự chủ, mọi PR, mọi chính sách (kể cả `XT_GUARD_POLICY=strict`): `gh pr merge … --auto`
   (mọi vị trí cờ, kể cả `--admin`/`-R`), GraphQL `enablePullRequestAutoMerge`, MCP `enable_pr_auto_merge` → `deny`, mã `AUTO_MERGE_ENABLE`,
   không gọi `merge-check`. Tắt auto-merge (`--disable-auto`, MCP disable) vẫn cho qua. Merge ghim head qua `merge-check` như ADR-0014.
4. **Bỏ required check `merge-gate`** khỏi `.github/rulesets/main.json` (repo khung: còn `quality`, `protection-guard`, `gitleaks`,
   `dep-audit`) và `framework/templates/ruleset-main.json` (dự án đích: `quality`, `gitleaks`). Lệnh `xt.py merge-gate` (kể cả `--event`/
   `--check-run` của T-1802) và test tương ứng gỡ; ADR-0035 không triển khai.
5. **Chuyển tiếp an toàn:** `merge-gate.yml` thành **stub** `on: pull_request` (trần, không `branches:`/`paths:`), một job tên `merge-gate` luôn
   exit 0, `permissions: contents: read`, không checkout, không `uses:`, không secret — chỉ giữ context required check còn trong ruleset
   **sống** tới khi chủ repo gỡ ở ba repo (kiểm `gh api repos/<o>/<r>/rules/branches/main`). Xoá stub trước khi gỡ ruleset = mọi PR treo
   "Expected". `install.py --with-github` vẫn phát stub (cập nhật tại chỗ khi file còn nguyên hash). `NON_CI_CHECKS` giữ tên `merge-gate` khi còn
   stub (stub xanh không phải bằng chứng CI — AUD-HAR-058). T-1834: xoá stub + mục `GITHUB_FILES` + tên trong `NON_CI_CHECKS`/fixture sau khi
   ba ruleset sống đã gỡ.
6. **`pr-steward.yml`:** `workflow_run` chỉ còn `workflows: [CI]`; không cần bật "Allow auto-merge" ở Settings — khuyên chủ repo **tắt** để đóng
   hẳn cửa sổ người bật nhầm. `XT_STEWARD_TOKEN` trở thành việc cần làm thật: merge bằng `GITHUB_TOKEN` không kích workflow `push` trên nhánh
   chính (trước đây auto-merge của GitHub kích).
7. **Dự án đích** nhận `xt.py` + stub qua `install.py --with-github` (T-1843 mở PR), import lại ruleset mẫu 2 check hoặc gỡ `merge-gate` trong
   ruleset sống; không cần event policy nào.

## Lý do (tiêu chí chất lượng cuối, AGENTS.md §4)

- (1) Đúng, an toàn, chặt hơn: mọi merge của máy ghim head đã đánh giá — lỗ ADR-0023 đóng tận gốc thay vì vá bằng check. Không còn giả định
  chưa xác minh về check-run API. Không còn `pull_request_target` ở workflow nào ngoài `pr-review.yml` (đang tắt).
- (2) Đường lùi: PR revert + thêm lại context `merge-gate` vào ruleset (chủ repo); stub giữ mọi PR chạy trong lúc chuyển.
- (3) Đơn giản, chuẩn, test được: xoá ~700 dòng (mã + test) thay vì thêm; một luật, một cơ chế, giống merge queue/bot merge của ngành.
- (4) Trải nghiệm: ruleset dự án đích còn 2 check; không việc cấu hình GitHub nào ngoài gỡ một context.
- (5) Tốc độ: trong phiên merge vẫn ngay khi `merge-check` = `merge`; phiên tắt thì steward merge khi CI xong (≤ 1 sự kiện) hoặc lịch 10 phút.

## Các phương án đã cân nhắc

- **A — ADR-0035** (`workflow_run` + check-run REST, chuyển tiếp D-120, steward đánh giá lại D-119): tự chủ hoàn toàn nếu giả định đúng, nhưng
  nhiều máy móc nhất; D-121 chọn A vì không cần chủ repo — chủ repo chọn B.
- **Event policy cho `pull_request_target`** (chủ repo, ba repo, theo path): không đổi mã nhưng phụ thuộc cấu hình ngoài repo, dự án mới không có.
- **`merge-gate` thành job trong `ci.yml`** (`pull_request`): PR sửa được cổng (ADR-0023 đã loại).
- **Giữ auto-merge, steward tắt khi `hard`**: cửa sổ giữa push và steward vẫn mở cho máy — không chặt.

## Hệ quả

- **Cửa sổ còn lại:** người bật auto-merge tay (khi repo còn "Allow auto-merge") → GitHub có thể merge head chưa ghim tới khi steward/`pr next`
  tắt (`workflow_run` CI xong hoặc lịch ≤ 10 phút). Lớp đỡ: ruleset (required check CI, resolve thread, không bypass), guard không cho agent bật,
  khuyên tắt "Allow auto-merge". Máy không còn đường nào merge head chưa đánh giá.
- `pr next --json` bỏ khoá `fallback` (giao diện máy đọc đổi — CHANGELOG). Hành động còn: `merge`, `wait`, `disable-auto-merge`, `update`,
  `review`, `fix`, `republish-review`, `retarget`, `defer-human`, `done`, `closed`, `error`.
- Steward merge bằng `GITHUB_TOKEN` không kích `push` trên nhánh chính: CI của `main` không chạy sau merge do steward → đặt `XT_STEWARD_TOKEN`
  (fine-grained PAT/App: contents + pull requests: write). Trong phiên, agent merge bằng token người dùng → bình thường.
- Khoá `auto_merge_ok` của `merge_eligibility` giữ tên (guard, `merge-check --json`, > 50 ca fixture đọc) — nghĩa còn lại: "không ngoại lệ cứng
  và review hợp lệ"; đổi tên là lát riêng.
- Thân ADR-0015/0016/0019/0020/0022/0024/0025/0027/0028/0031/0033 vẫn tả auto-merge là cơ chế: theo `conventions.md` chỉ đổi dòng trạng thái;
  bảng dưới là nơi duy nhất nói phần nào hết hiệu lực.
- PR chuyển đổi: GitHub chạy cả job cũ (`pull_request_target`, bản nhánh đích) lẫn stub (`pull_request`, bản head) → hai check-run cùng tên
  `merge-gate` đều xanh (job cũ chỉ đỏ khi `hard` + auto-merge bật — máy không bật). Dự án đích chưa gộp stub (file đã sửa → `.xtemplates-new`)
  sẽ treo PR từ 2026-11-02 tới khi gộp stub hoặc gỡ context.

## Ảnh hưởng tới ADR trước

| ADR | Còn hiệu lực | Hết hiệu lực (thay bởi ADR này) |
|---|---|---|
| 0014 | §2 merge ghim head (khôi phục ở mọi mức) | — |
| 0015 | L3 = máy merge mọi làn trừ ngoại lệ cứng | cơ chế bật auto-merge khi mở PR; guard cho bật ở L3 |
| 0016, 0019, 0020, 0022 §Giới hạn | luật ngoại lệ cứng, `merge_hard_exceptions`, grant trong PLAN | vế "bật auto-merge" trong cơ chế chặn |
| 0021 | `merge-watch` chờ CI, in `pr next` | — (nay là đường chờ duy nhất của phiên) |
| 0023 | — | toàn bộ: required check `merge-gate` bỏ, `xt.py merge-gate` gỡ |
| 0024 | làn chuẩn merge sau review sạch ở head H | bước bật auto-merge sau review |
| 0025 | máy trạng thái `pr next` trong mã | hành động `enable-auto-merge`, khoá `fallback` |
| 0027 | steward trên GitHub, idempotent theo (repo, PR, head, hành động) | D-062/D-063 (không còn auto-merge); `workflow_run` chỉ `CI` |
| 0028 | một điều kiện merge cho merge-check/pr next/guard/steward | `merge-gate` là người dùng của `merge_eligibility` |
| 0034 | CI/E2E tối thiểu, song song tối đa | ruleset mẫu 3 check → 2 check (`quality`, `gitleaks`) |
| 0035 | — | không triển khai (mã T-1802 gỡ) |

## Xác nhận

`! grep -q pull_request_target .github/workflows/merge-gate.yml && grep -q "pull_request:" .github/workflows/merge-gate.yml`;
`! grep -q '"merge-gate"' .github/rulesets/main.json framework/templates/ruleset-main.json`; `! grep -q "enable-auto-merge" scripts/xt.py`;
`python3 -m unittest tests.test_hooks -k auto_merge && python3 scripts/xt.py autonomy-bench`; `python3 -m unittest tests.test_merge
tests.test_merge_review_source tests.test_delivery_phase tests.test_install tests.test_ci tests.test_ci_template`; trên PR thật: `pr next` trả
`wait` rồi `merge`, PR vào `main` bằng merge ghim head, không auto-merge.

## Đường lùi

Revert PR Lát 0; chủ repo thêm lại context `merge-gate` vào ruleset; quay về ADR-0023 (cần event policy `pull_request_target` sau 2026-11-02).

## Nguồn (đọc 2026-10-21)

- <https://docs.github.com/en/rest/pulls/pulls#merge-a-pull-request> — tham số `sha`: merge chỉ khi head đúng SHA.
- <https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/incorporating-changes-from-a-pull-request/automatically-merging-a-pull-request>
  — auto-merge của GitHub merge khi mọi yêu cầu đạt, không ghim head.
- <https://github.blog/changelog/2026-09-17-workflow-execution-protections-in-github-actions-generally-available/> — event policy mặc định
  chặn `pull_request_target` ở repo public từ 2026-11-02.
- `docs/autopilot/DECISIONS.md` D-119…D-122; `docs/adr/0023`, `0035`; `scripts/xt.py` `pr_next`, `_steward_command` (đọc 2026-10-21).
