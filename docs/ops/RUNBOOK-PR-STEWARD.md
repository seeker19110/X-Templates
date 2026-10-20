# Runbook — `pr-steward` (`BASE-DOC-004`)

> Dịch vụ chạy liên tục duy nhất của khung: workflow [`pr-steward.yml`](../../.github/workflows/pr-steward.yml)
> ([ADR-0027](../adr/0027-pr-steward-on-github.md)) giữ cho PR đủ tiêu chuẩn "merge theo làn" vào nhánh chính kể cả khi
> không còn phiên agent nào. Không có deploy/rollback riêng: workflow là file trong repo, rollback = revert commit.

## 1. Steward làm gì, khi nào chạy

Mỗi lượt gọi `python3 scripts/xt.py pr steward --apply` (dự án đích: `.xtemplates/scripts/xt.py`). Lệnh duyệt PR đang mở,
với mỗi PR chạy cùng luật với `pr next`, rồi tự làm đúng các hành động sau:

| Hành động (`pr next`) | Steward làm |
|---|---|
| `enable-auto-merge` | `gh pr merge --auto --squash --match-head-commit <head>` (rồi merge ghim head nếu GitHub báo đã sẵn sàng) |
| `merge` | `PUT pulls/<N>/merge` squash, ghim `sha=<head>` |
| `disable-auto-merge` | `gh pr merge --disable-auto` |
| `update` | `PUT pulls/<N>/update-branch` ghim `expected_head_sha` — **chỉ khi có secret `XT_STEWARD_TOKEN`** |
| `review`, `fix`, `retarget`, `defer-human`, `wait` | chỉ ghi vào bản tóm tắt (Step Summary), không làm gì |

PR từ fork hoặc tác giả không có quyền ghi repo luôn thành `defer-human` (người merge). PR làn chuẩn được gắn nhãn
`xt-standard-lane`; không gắn được nhãn thì lượt đó không bật/merge (exit 1, `warn`). Nhánh đích không có check bắt buộc
thì không bật auto-merge (D-062), chỉ merge ghim head khi CI xanh.

Kích hoạt: `schedule` mỗi 10 phút (lưới bù) · `workflow_run` khi `CI`/`merge-gate` xong · `check_suite: completed` (check
của app ngoài) · `issue_comment` mang dấu `xt-review v1` của OWNER/COLLABORATOR/MEMBER hoặc `vars.XT_REVIEW_IDENTITY` ·
`workflow_dispatch` (nhập `pr` để chỉ xét một PR). Khoá idempotent (repo, PR, head, hành động) và đọc lại PR ngay trước
mỗi hành động, nên sự kiện lặp/sai thứ tự không lặp tác dụng phụ. Job chỉ checkout nhánh mặc định, không chạy mã của PR.

Điều kiện cần: Settings → General → **Allow auto-merge**; secret `XT_STEWARD_TOKEN` (fine-grained PAT hoặc GitHub App:
contents + pull requests: write) là tuỳ chọn nhưng cần để cập nhật nhánh và để merge kích workflow `push` trên nhánh chính.

## 2. Triệu chứng và chẩn đoán

Chẩn đoán chỉ đọc (không `--apply`), từ máy dev có `gh` đã đăng nhập:

```bash
python3 scripts/xt.py pr next --pr <N>                        # MỘT bước kế + lý do (why) + lệnh (do)
python3 scripts/xt.py pr steward --pr <N> --repo owner/repo   # đúng thứ steward sẽ làm với PR, không thực thi
python3 scripts/xt.py pr steward --json                       # mọi PR mở, máy đọc
python3 scripts/xt.py merge-check --pr <N>                    # vì sao chưa đủ điều kiện merge (CI, review, nhãn risk:)
```

Exit 1 của `pr steward` = có PR lỗi/cảnh báo (`error`/`warn`), không phải steward hỏng. Kết quả mỗi lượt nằm ở Step
Summary của run `pr-steward` (mục `## pr-steward`, mỗi PR một dòng).

| Triệu chứng | Nguyên nhân hay gặp | Xử lý |
|---|---|---|
| PR treo, không ai merge | `action` = `review` (chưa có dấu review sạch ở đúng head), `fix`, `wait` (CI chưa xanh), hoặc `defer-human` (fork/tác giả không quyền ghi, ngoại lệ cứng) | Đọc `why` của `pr next`; làm đúng `do`. Review xong: `xt.py pr reviewed --pr <N> --head <H> --clean ...` (đăng lên PR; steward kích bằng `issue_comment`) |
| Auto-merge không bật | Repo chưa bật "Allow auto-merge"; nhánh đích không có check bắt buộc (D-062); PR có nhãn `risk:`; push mới đổi head sau review; lệnh `gh` lỗi (thiếu quyền token) | `pr next` cho `why`; sửa cài đặt repo/ruleset; review lại ở head mới. Dưới `merge_autonomy: L3` steward không bật auto-merge mà merge ghim head |
| PR tụt sau nhánh đích, không tự cập nhật | Chưa đặt `XT_STEWARD_TOKEN` (`XT_STEWARD_UPDATE=off`): commit cập nhật bằng `GITHUB_TOKEN` không kích CI nên PR kẹt chờ check; `why` ghi "đặt XT_STEWARD_TOKEN" | Đặt secret `XT_STEWARD_TOKEN`, hoặc cập nhật nhánh tay (`gh pr update-branch <N>`) |
| Run steward đỏ nhưng PR không bị gì | `warn` không gắn được nhãn `xt-standard-lane` (thiếu `issues: write`) hoặc `error` không đọc lại được PR | Xem Step Summary; lượt sau tự thử lại |
| Không thấy steward chạy | Workflow bị disable; cron GitHub bị tắt sau 60 ngày repo không hoạt động; `issue_comment` bị lọc (không phải dấu review của người có quyền ghi) | `gh workflow list`; chạy tay `gh workflow run pr-steward.yml` |
| Merge nhầm | PR đủ điều kiện máy nhưng nội dung sai | Revert commit squash qua PR mới; siết nhãn `risk:`/`merge_hard_exceptions`; ghi nguyên nhân (D-NNN nếu đổi luật) |
| Token lộ/hết hạn | `XT_STEWARD_TOKEN` | Thu hồi token ở GitHub, tạo mới, cập nhật secret (không dán giá trị vào log/commit). Hết hạn: mất cập nhật nhánh, các việc khác vẫn chạy bằng `GITHUB_TOKEN` |

Bí mật: chỉ `XT_STEWARD_TOKEN` (Settings → Secrets and variables → Actions) và biến `XT_REVIEW_IDENTITY` (tuỳ chọn);
giá trị không nằm trong repo. Liên hệ trực: chủ repo (sự cố bảo mật: `SECURITY.md`).

## 3. Tắt khẩn và khôi phục

Tắt (thứ tự nhanh nhất trước):

1. `gh workflow disable pr-steward.yml` (hoặc Actions → pr-steward → Disable workflow) — dừng mọi trigger, không đổi
   file. Run đang chạy: `gh run cancel <id>`.
2. Gỡ auto-merge đã bật cho từng PR: `gh pr merge <N> --disable-auto` (liệt kê: `gh pr list --json number,autoMergeRequest`).
3. Cắt quyền: xoá secret `XT_STEWARD_TOKEN`; Settings → General bỏ "Allow auto-merge"; ruleset nhánh chính yêu cầu review/check.
4. Dứt điểm lâu dài: PR xoá/sửa `pr-steward.yml`, nêu lý do trong PR. Phiên agent tắt auto-merge trước mỗi push (ADR-0025).

Khôi phục: `gh workflow enable pr-steward.yml` → `gh workflow run pr-steward.yml` → chạy
`python3 scripts/xt.py pr steward --json` đối chiếu kết quả → đặt lại secret/bật "Allow auto-merge" nếu đã gỡ. Sau tắt
dài ngày PR cũ có thể tụt nhánh: cập nhật (steward có token hoặc `gh pr update-branch`) rồi review lại ở head mới.
Workflow bị sửa hỏng: revert commit qua PR; dự án đích chạy lại `install.py` để chép bản chuẩn.

## 4. Đẩy tag phát hành (`release-tag.yml`)

Workflow `release-tag.yml` đẩy tag bằng `GITHUB_TOKEN`; GitHub từ chối khi commit đích đổi file workflow so với tag trước
("refusing to allow a GitHub App to create or update workflow … without workflows permission", AUD-CI-014). Sửa: đặt secret
tuỳ chọn `XT_RELEASE_TOKEN` (fine-grained PAT, chỉ repo này: `contents: write` + `workflows: write`); workflow dùng nó ở bước
checkout, thiếu thì rơi về `GITHUB_TOKEN`. Thiếu secret mà commit có đổi workflow: người đẩy tag tay
(`git tag -a vX.Y.Z -m vX.Y.Z <sha> && git push origin vX.Y.Z`). Xoay/thu hồi như `XT_STEWARD_TOKEN` (§2).
