# ADR-0023: Required check `merge-gate` — máy chặn auto-merge của PR ngoại lệ cứng trên head hiện tại

- **Trạng thái:** Thay bởi ADR-0035 (2026-10-21) về trigger; luật và exit code giữ
- **Trạng thái triển khai:** Đã triển khai trong repo — `scripts/xt.py` `cmd_merge_gate`, `_merge_eval`, `autoMergeRequest`
  trong `_pr_rest`; workflow `.github/workflows/merge-gate.yml`; ruleset mẫu `.github/rulesets/main.json` thêm context
  `merge-gate`; `scripts/install.py` copy workflow cùng ruleset (`--with-github`); test `tests/test_merge.py::MergeGateTest`.
  **Chờ người:** chủ repo thêm `merge-gate` vào ruleset `main` đang chạy trên GitHub (Settings → Rules) sau khi thấy job
  chạy trên một PR — đến lúc đó check chưa bắt buộc.
- **Ngày:** 2026-10-18
- **Ghi chú ngày hiệu lực (2026-10-21):** "từ 2025-11-07" ở §Quyết định 2 là ngày GitHub công bố; thay đổi có hiệu lực
  từ 2025-12-08 (`pull_request_target` luôn lấy workflow và checkout từ nhánh mặc định). Nội dung quyết định bên dưới giữ nguyên.
- **Làm rõ:** ADR-0016, ADR-0020, ADR-0022 (đóng mục "Giới hạn còn lại" thứ nhất) — quyết định D-029

## Bối cảnh

`xt.py merge-check` trả `hard` (người merge) cho PR chạm ngoại lệ cứng, đổi khoá `merge_hard_exceptions` hay đổi hiệu lực
dòng `- grant:` của `docs/autopilot/PLAN.md` (ADR-0016, ADR-0020, ADR-0022). Guard (`_auto_merge_verdict`) không bật
auto-merge cho PR `hard`, và merge tay của agent ghim head (`--match-head-commit` + `merge-check` lúc merge). Nhưng
auto-merge của GitHub **không ghim head**: bật cho PR vô hại rồi push commit thêm grant thì GitHub vẫn merge khi required
check xanh. Đỡ duy nhất là kỷ luật `LOOP-STOP-005` (chạy lại `merge-check` sau mỗi push) và review — lời dặn, không phải
cơ chế.

## Quyết định

1. **Lệnh `xt.py merge-gate [--pr N] [--pr-json F] [--head SHA] [--json]`**: dùng lại nguyên đường quyết định của
   `merge-check` (`_merge_eval`: xt.yaml, `merge_hard_exceptions` đã commit ở nhánh đích, REST). exit 1 khi `hard` ≠ rỗng
   **và** PR đang bật auto-merge (REST `auto_merge`); `hard` mà không auto-merge → exit 0 kèm cảnh báo; 2 = không đọc
   được PR (CI đỏ — đóng khi thiếu); 3 = head của PR khác `--head` (REST chưa thấy push, hoặc đã có push mới hơn).
2. **Workflow `merge-gate.yml`** trên `pull_request_target` với `opened, synchronize, reopened, edited, labeled,
   unlabeled, auto_merge_enabled, auto_merge_disabled`. `pull_request_target` có chủ đích: workflow và `xt.py` lấy từ
   **nhánh mặc định** (GitHub, từ 2025-11-07), nên PR không sửa được chính job hay lệnh kiểm nó — với `pull_request`, PR
   đổi `merge-gate.yml` hoặc `scripts/xt.py` là tắt được cổng. Job không checkout/chạy code PR (checkout không `ref:`,
   `persist-credentials: false`), chỉ đọc PR qua REST bằng `GITHUB_TOKEN` chỉ đọc (`contents`, `pull-requests`,
   `checks`, `statuses`: read — `merge-check` đọc check-run/status của head), không secret nào khác. `--head` ghim SHA
   của sự kiện; exit 3 thì thử lại 5 lần cách 10 giây rồi đỏ. Dự án đích dùng được nguyên file (tự dò
   `.xtemplates/scripts/xt.py`).
3. **Required check thứ năm** `merge-gate` trong ruleset mẫu, không gộp vào `quality`: `quality` chạy trên `pull_request`
   (code PR) nên không làm `needs` được job của workflow khác, và gộp vào thì PR lại sửa được cổng. `WF-CI-001` đổi từ 4
   thành 5 check.

## Lý do (D-029)

- Đỏ khi `hard` + auto-merge, không phải luôn đỏ khi `hard`: ruleset không có `bypass_actors` và PR do agent mở dưới tài
  khoản chủ repo (không tự approve được) — luôn đỏ thì chính người cũng không merge được PR `hard`, chốt người của
  ADR-0016/0022 thành khoá chết. Lỗ cần đóng chỉ là auto-merge; merge tay của agent đã có guard ghim head, merge tay của
  người là chốt người theo thiết kế.
- Bật auto-merge sinh sự kiện `auto_merge_enabled` → job chạy lại trên head đó → đỏ trước khi GitHub merge; người tắt
  auto-merge (`auto_merge_disabled`) → xanh lại để merge tay.
- Logic ở `xt.py` có test; workflow chỉ gọi lệnh.

## Các phương án đã cân nhắc

- **Luôn đỏ khi `hard`**: người cũng không merge được (xem trên). Loại.
- **Luôn đỏ + thêm bypass (vai trò admin) vào ruleset**: bypass vượt MỌI required check (`quality`, `gitleaks`…). Loại.
- **Job trong `ci.yml` (`pull_request`)**: PR sửa được workflow/`xt.py` để tắt cổng. Loại.
- **Chỉ kỷ luật `LOOP-STOP-005`**: hiện trạng, lời dặn không phải cơ chế. Loại.

## Hệ quả

- PR `hard` có auto-merge bật thì check `merge-gate` đỏ trên head hiện tại; push sau khi bật auto-merge được máy kiểm.
  Agent vẫn tắt auto-merge + `loop defer` theo `LOOP-STOP-005` (check đỏ chỉ chặn merge, không tự tắt auto-merge).
- Người bật auto-merge cho PR `hard` cũng bị chặn — PR `hard` merge tay.
- Repo chưa có `merge-gate.yml` trên nhánh mặc định thì job không chạy (kể cả PR thêm file này): check chỉ có hiệu lực
  sau khi merge và chủ repo thêm vào ruleset đang chạy. Dự án đích nhận workflow khi chạy lại `install.py --with-github`
  (copy-if-absent), rồi tự thêm context vào ruleset.
- **Giới hạn còn lại:**
  - Khe vài giây: bật auto-merge khi mọi check khác đã xanh và `merge-gate` cũ xanh (head chưa `hard` lúc chạy) — sự
    kiện `auto_merge_enabled` tạo run mới (đang chờ) trước khi GitHub merge trong thực tế, nhưng thứ tự này là hành vi
    của GitHub, chưa đo. Guard vẫn là lớp chặn chính cho việc bật auto-merge trên PR `hard`.
  - Check-run của `pull_request_target` được GitHub gắn vào head của PR (cách các repo dùng `pull_request_target` làm
    required check); chưa xác minh bằng run thật trên repo này — người kiểm trước khi bật trong ruleset (bước chờ người
    ở trên).
  - `merge-gate` đọc `merge_hard_exceptions` ở `origin/<nhánh đích>`; PR chồng mà job không lấy được nhánh đó thì tính
    `human` (chặt hơn).
