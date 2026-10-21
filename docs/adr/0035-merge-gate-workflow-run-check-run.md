# ADR-0035: `merge-gate` chạy theo `workflow_run` của CI và báo bằng check-run REST trên head PR

- **Trạng thái:** Bị thay bởi ADR-0036 (2026-10-21, D-122) — không triển khai tiếp; trước đó: thay ADR-0023 về trigger và cách báo
- **Trạng thái triển khai:** Không triển khai — mã T-1802 gỡ ở T-1808, T-1803 bỏ (ADR-0036). Kế hoạch cũ: Lát 0 của `docs/autopilot/PLAN-3.13-next-level.md`: T-1802 (`xt.py merge-gate
  --event FILE [--check-run]`, test `tests/test_merge.py`), T-1803 (`.github/workflows/merge-gate.yml`, test
  `tests/test_ci.py`). Cập nhật dòng này khi hai PR merge và check đã báo trên một PR thật.
- **Ngày:** 2026-10-21
- **Làm rõ:** ADR-0023 (thay về trigger), ADR-0027 (steward), ADR-0028 (một điều kiện merge), ADR-0034 (ruleset dự án đích);
  quyết định D-118; nghiên cứu `research/2026-10-21-next-level-speed-automation-quality.md` §4.2 và việc khẩn K-1.

## Bối cảnh

ADR-0023 đặt `merge-gate` trên `pull_request_target` vì workflow và `xt.py` lấy từ nhánh mặc định nên PR không sửa được
cổng. Dữ kiện mới (đọc 2026-10-21):

- GitHub "workflow execution protections" GA 2026-09-17. **Từ 2026-11-02**, repo public chưa có event policy sẽ bị event
  policy mặc định chặn `pull_request_target` (hiện ở evaluate mode). Docs khuyên tránh trigger này, ưu tiên
  `workflow_run`/`pull_request`; docs không nói repo của tài khoản cá nhân có thuộc diện không (chưa xác minh) — repo khung
  là public, user-owned, nên coi là thuộc diện.
- `merge-gate` là required check trong ruleset của repo khung và của mẫu dự án đích (ADR-0034). Check không báo thì ở
  trạng thái "Expected" và **mọi PR treo** ở cả ba repo đã cài.
- Ghi chú ngày của ADR-0023: GitHub công bố 2025-11-07, **hiệu lực từ 2025-12-08** — từ đó `pull_request_target` luôn lấy
  workflow và checkout từ nhánh mặc định.

## Quyết định

1. **Trigger.** `merge-gate.yml` chạy trên `workflow_run` (`workflows: [CI]`, `types: [completed]`). Workflow `workflow_run`
   luôn lấy từ nhánh mặc định, nên giữ tính chất ADR-0023 §2: PR không sửa được job hay `xt.py`. Job không checkout hay chạy
   code PR (checkout không `ref:`, `persist-credentials: false`), không tải artifact của run kích nó, không secret nào
   khác. Quyền: `contents: read`, `pull-requests: read`, `statuses: read`, `checks: write` (tạo check-run — chỉ job này).
   Tên job giữ `merge-gate` để `protection-guard` đối chiếu context ruleset như cũ.
2. **PR và head.** PR lấy từ `workflow_run.pull_requests[]`; rỗng (PR từ fork, push lên nhánh đích) → REST
   `pulls?head=<chủ repo head>:<head_branch>&state=open`; không có PR nào → exit 0, không tạo check. Head ghim =
   `workflow_run.head_sha` (thay `pull_request.head.sha`); exit 3 giữ nghĩa cũ (head của PR khác head của sự kiện).
3. **Báo bằng check-run.** `xt.py merge-gate --event "$GITHUB_EVENT_PATH" --check-run` chạy đúng luật hiện có
   (`_merge_eval`: đỏ khi `hard` hoặc review chưa sạch ở head **và** PR đang bật auto-merge — ADR-0023, ADR-0028) trên từng
   PR, rồi `POST repos/{o}/{r}/check-runs` tên `merge-gate` trên head (`status=completed`, `conclusion` `success` |
   `failure`; lý do ở `output.title`/`output.summary`). Tạo không được → **exit 2**: check không báo = fail-closed (PR treo
   thay vì lọt). Nhiều PR cùng head → mỗi PR một check-run, đỏ nếu bất kỳ PR nào block.
4. **Sự kiện không còn kích trực tiếp:** `labeled`, `unlabeled`, `edited`, `auto_merge_enabled`, `auto_merge_disabled`.
   Việc đó chuyển sang `pr-steward.yml` (ADR-0027) — đã nghe `workflow_run` của `CI` và `merge-gate`, cộng lịch 10 phút —
   gọi `pr next` và tắt auto-merge khi PR `hard` hoặc thiếu review sạch. Chuỗi `CI` → `merge-gate` → `pr-steward` sâu 2
   cấp (GitHub giới hạn chuỗi `workflow_run` ở 3 cấp — chưa xác minh lại 2026-10-21).
5. **`pr-review.yml`** vẫn `pull_request_target` (workflow đang tắt). Khi bật cần event policy riêng cho path đó — việc của
   chủ repo (REST `/actions/policies` bị proxy phiên chặn, agent không kiểm được).
6. **Dự án đích** nhận file mới bằng `install.py --with-github` (copy-if-absent: file còn đúng hash lần cài trước được
   cập nhật tại chỗ; file đã sửa ra `.xtemplates-new` để gộp tay). Chạy cả `xt.py` mới cùng lúc (bản cũ không có `--event`
   → exit 2). Ruleset không đổi: context vẫn `merge-gate`.

## Lý do

- Giữ luật, đổi trigger: cùng đường quyết định (`_merge_eval`), cùng exit code; chỉ nguồn sự kiện và cách báo đổi, nên test
  luật hiện có còn nguyên. `workflow_run` đúng hướng docs khuyên và bỏ được `zizmor: ignore[dangerous-triggers]` của
  `pull_request_target`.
- Đường "push sau khi bật auto-merge" (lỗ ADR-0023 đóng) vẫn đóng: push mới → CI chạy lại → `merge-gate` chỉ báo sau khi CI
  xong, trên head mới; tới lúc đó required check `merge-gate` ở "Expected" nên GitHub chưa merge. Nhãn `risk:` hay đổi
  nhánh đích xảy ra khi CI đang chạy được tính ở lần đánh giá cuối, vì `merge-gate` đọc lại PR sau CI.
- check-run tạo bằng REST là cách báo check lên head PR từ workflow `workflow_run` (check của job `workflow_run` gắn vào
  commit nhánh mặc định, không vào PR — chưa kiểm trên run thật).

## Các phương án đã cân nhắc

- **Giữ `pull_request_target` + event policy mở đường** (chủ repo, ba repo, theo path): không đổi mã, nhưng phụ thuộc cấu
  hình ngoài repo mà dự án đích mới cài không có; thiếu policy là mọi PR treo. Chỉ giữ làm đường lùi.
- **Chuyển `merge-gate` thành job trong `ci.yml` (`pull_request`)**: PR sửa được workflow/`xt.py` để tắt cổng (loại ở
  ADR-0023, vẫn đúng).
- **`workflow_run` + commit status API (`statuses: write`) thay check-run**: cùng hiệu lực với required check; chưa chọn vì
  check-run có `output` mang lý do đỏ, hiển thị trên PR. Chưa so sánh cách GitHub tính nhiều lần báo cùng tên.
- **Giữ thêm trigger `pull_request_target` song song**: vẫn bị event policy chặn, mất lợi ích. Loại.
- **Luôn đỏ khi `hard`** để khỏi cần bắt `auto_merge_enabled`: người cũng không merge được PR `hard` (D-029). Loại.

## Hệ quả

- `merge-gate` báo muộn hơn trước một nhịp: sau khi CI xong (trước: song song CI). Bù lại không cần đoán thứ tự với CI.
- **Cửa sổ mới:** `labeled`/`edited`/`auto_merge_enabled`/`auto_merge_disabled` không còn tính lại check ngay. PR đã có
  check xanh trên head, đang bật auto-merge mà còn bị chặn bởi điều kiện không phải check (thread chưa resolve, nhánh tụt
  sau nhánh đích), nếu bị gắn nhãn `risk:` hay đổi đích thì check cũ vẫn xanh tới lần steward chạy (lịch ≤ 10 phút, GitHub
  có thể trễ). Ngược lại, người tắt auto-merge trên PR đã đỏ không làm check xanh lại ngay: check chỉ tính lại khi CI chạy
  lại trên head đó (push hoặc re-run CI — chưa xác minh `workflow_run` bắn lại khi re-run).
- **Lớp đỡ cho cửa sổ:** (a) guard không cho agent bật auto-merge trên PR `hard`/thiếu review sạch, và kỷ luật
  `LOOP-STOP-005`/`LOOP-STOP-022` (tắt auto-merge trước khi push hoặc gắn nhãn `risk:`); (b) `pr-steward` tắt auto-merge của PR
  `hard` (`pr next` → `disable-auto-merge`) theo `workflow_run` và lịch; (c) ruleset không bypass, PR bắt buộc, resolve thread.
  Auto-merge của GitHub merge ngay khi mọi check xanh, nên cửa sổ chỉ thật khi PR còn bị chặn bởi điều kiện khác.
- Repo chưa có `merge-gate.yml` mới trên nhánh mặc định thì `workflow_run` không chạy cho PR thêm file này (như ADR-0023);
  PR Lát 0 không tự kiểm được workflow của chính nó — người kiểm trên PR kế tiếp.
- PR có xung đột (CI `pull_request` không chạy) hoặc CI không chạy cho head đó thì `merge-gate` không báo: fail-closed, PR
  vốn không merge được.
- **Rủi ro cần kiểm trước khi tag:** ruleset có tính check-run do API tạo là context `merge-gate` không (nguồn Any, không
  `integration_id`); và GitHub tính check-run nào khi một head có nhiều cái cùng tên (nhiều PR cùng head, hoặc đánh giá lại).
  Kiểm bằng PR Lát 0 trước khi gỡ trigger cũ ở dự án đích; chưa xác minh = chưa tag.

## Xác nhận

`! grep -q pull_request_target .github/workflows/merge-gate.yml`; `grep -q "checks: write" .github/workflows/merge-gate.yml`;
`python3 -m unittest tests.test_merge -k merge_gate -k check_run`; `python3 -m unittest tests.test_ci`; trên PR thật: CI xanh
và check `merge-gate` báo ở head, ruleset coi là đạt.

## Đường lùi

Revert PR; giữ file cũ (`pull_request_target`) kèm event policy cho path `.github/workflows/merge-gate.yml` ở
Settings → Actions → Policies (việc của chủ repo). Dự án đích đã sửa file giữ bản của mình (`kept-own`/`.xtemplates-new`).

## Nguồn (đọc 2026-10-21)

- <https://github.blog/changelog/2026-09-17-workflow-execution-protections-in-github-actions-generally-available/>
- <https://docs.github.com/en/actions/how-tos/administer/control-workflow-execution>
- <https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target>
- <https://github.blog/changelog/2025-11-07-actions-pull_request_target-and-environment-branch-protections-changes/>
- <https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/collaborating-on-repositories-with-code-quality-features/troubleshooting-required-status-checks>
