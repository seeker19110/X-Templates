# ADR-0018: Không hỏi người — nguy hiểm thì chặn, còn lại cho chạy

- **Trạng thái:** Đã chấp nhận
- **Trạng thái triển khai:** Đã triển khai — `guard.py` (`apply_policy`, `DANGER_MARKERS`), `.claude/settings.json`
  `permissions.ask` rỗng, `_lib.sh` `ask_strict` cho nhánh lỗi hạ tầng của `pre-bash-guard.sh`/`pre-mcp-guard.sh`
  (thiếu python3/`guard.py`, guard lỗi khi merge, commit vào repo ngoài dự án: cho qua, không chạy cổng của repo lạ);
  test `tests/test_hooks.py::GuardPolicyTest`, `MergeHookFailClosedTest`, `CommitGateForeignRepoTest`.
- **Ngày:** 2026-10-17
- **Thay một phần:** ADR-0017 §2 (giữ `ask`), ADR-0002 (hỏi ở điểm dừng hành động) — với hook guard của khung

## Bối cảnh

Chủ repo yêu cầu (2026-10-17): "cấm các lệnh nguy hiểm, còn đâu cho phép hết" — mỗi câu hỏi quyền khi không có người
làm dự án ngưng chạy. Trước đây guard trả `ask` cho hai nhóm khác nhau: việc **không đảo ngược** (push thẳng `main`,
xoá dữ liệu ngoài dự án, `gh repo delete`, `terraform destroy`, container `--privileged`, tắt hook…) và việc **đối
ngoại nhưng đảo ngược/kiểm soát được** (publish, deploy, `ssh`, cài gói, sửa cấu hình cổng, merge PR…).

## Quyết định

1. Bộ luật của `guard.py` giữ nguyên (tính `ask` đầy đủ). Đầu ra đi qua `apply_policy`: `ask` có lý do thuộc
   `DANGER_MARKERS` → `deny`; `ask` khác → cho qua. `deny`/`allow` giữ nguyên.
2. Lệnh huỷ hạ tầng/repo (`gh repo delete|archive`, `gh secret`, `kubectl delete`, `terraform|tofu|pulumi destroy`)
   mang lý do riêng `DESTROY_ASK` để bị chặn; publish/deploy khác vẫn `EXTERNAL_ASK` → cho qua.
3. `permissions.ask` trong settings rỗng. `deny` của settings và guard giữ nguyên.
4. `XT_GUARD_POLICY=strict` giữ hành vi cũ (hỏi) — chỉ chặt hơn, không phải công tắc tắt hook (`LOOP-HARNESS-018`).

## Lý do

- Người dùng có quyền cuối (AGENTS.md §1); dừng chờ người khi vắng mặt làm hỏng mục tiêu autopilot (ADR-0009).
- Ít code: một hàm ở đầu ra thay vì sửa từng luật; bộ luật và ~130 test cũ giữ nguyên (chạy ở `strict`).
- An toàn: việc không đảo ngược bị chặn hẳn (chặt hơn hỏi); việc còn lại có đường lùi (revert, unpublish, CI).

## Các phương án đã cân nhắc

- **Chỉ bỏ toàn bộ `ask`, giữ `deny` cũ**: push `main`, xoá ngoài dự án, `repo delete` chạy không hỏi. Loại.
- **Sửa từng luật trả `deny`/rỗng**: nhiều chỗ sửa, mất hành vi cũ làm đường lùi. Loại.

## Hệ quả

- Không còn lớp người duyệt cho publish/deploy/merge PR/sửa cổng/ra mạng; lớp đỡ là `deny`, CI, ruleset nhánh, review.
- `DANGER_MARKERS` khớp chuỗi lý do: đổi lời lý do của luật nguy hiểm phải cập nhật danh sách (test `GuardPolicyTest`).
