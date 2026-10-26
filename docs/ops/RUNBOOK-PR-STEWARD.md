# Runbook — `pr-steward` (`BASE-DOC-004`)

> Dịch vụ chạy liên tục duy nhất của khung: workflow [`pr-steward.yml`](../../.github/workflows/pr-steward.yml)
> ([ADR-0027](../adr/0027-pr-steward-on-github.md)) giữ cho PR đủ tiêu chuẩn "merge theo làn" vào nhánh chính kể cả khi
> không còn phiên agent nào. Không có deploy/rollback riêng: workflow là file trong repo, rollback = revert commit.

## 1. Steward làm gì, khi nào chạy

Mỗi lượt gọi `python3 scripts/xt.py pr steward --apply` (dự án đích: `.xtemplates/scripts/xt.py`). Lệnh duyệt PR đang mở,
với mỗi PR chạy cùng luật với `pr next`, rồi tự làm đúng các hành động sau:

| Hành động (`pr next`) | Steward làm |
|---|---|
| `merge` | `PUT pulls/<N>/merge` squash, ghim `sha=<head>` — chỉ khi `merge-check` = `merge` ở đúng head đó (kể cả PR người đã bật auto-merge: merge ghim head ngay). Thiếu `XT_STEWARD_TOKEN`: merge xong thì `POST actions/workflows/ci.yml/dispatches` trên nhánh đích (`→ dispatch CI ✓`; tên khác: biến `XT_CI_WORKFLOW`) |
| `disable-auto-merge` | `gh pr merge --disable-auto` — auto-merge do người bật trên PR chưa đủ điều kiện (dọn dẹp, không để GitHub merge head chưa đánh giá) |
| `update` | `PUT pulls/<N>/update-branch` ghim `expected_head_sha` — **chỉ khi có secret `XT_STEWARD_TOKEN`** |
| `review`, `fix`, `retarget`, `defer-human`, `wait` | chỉ ghi vào bản tóm tắt (Step Summary), không làm gì |

PR từ fork hoặc tác giả không có quyền ghi repo luôn thành `defer-human` (người merge). PR làn chuẩn được gắn nhãn
`xt-standard-lane`; không gắn được nhãn thì lượt đó không merge (exit 1, `warn`). Máy **không bao giờ bật auto-merge** của
GitHub (D-122, [ADR-0036](../adr/0036-pinned-merge-no-auto-merge-drop-merge-gate.md) — auto-merge không ghim head): mọi
merge là merge ghim head sau `merge-check` = `merge`; CI chưa xong → `wait`, lượt `workflow_run` của `CI` hoặc lịch 10 phút
xét lại.

Kích hoạt: `schedule` mỗi 10 phút (lưới bù) · `workflow_run` khi `CI` xong (stub `merge-gate` không kích, D-122) ·
`check_suite: completed` (check của app ngoài) · `issue_comment` mang dấu `xt-review v1` của OWNER/COLLABORATOR/MEMBER
hoặc `vars.XT_REVIEW_IDENTITY` · `workflow_dispatch` (nhập `pr` để chỉ xét một PR). Khoá idempotent (repo, PR, head, hành động) và đọc lại PR ngay trước
mỗi hành động, nên sự kiện lặp/sai thứ tự không lặp tác dụng phụ. Job chỉ checkout nhánh mặc định, không chạy mã của PR.

Điều kiện cần: **không** cần "Allow auto-merge" — nên **tắt** ở Settings → General để không ai bật nhầm. Nên đặt secret
`XT_STEWARD_TOKEN` (fine-grained PAT hoặc GitHub App: contents + pull requests: write): merge bằng `GITHUB_TOKEN` vẫn vào
nhưng GitHub không chạy workflow `push` cho commit đó — steward bù bằng `workflow_dispatch` của `ci.yml` trên nhánh đích
(GitHub cho `GITHUB_TOKEN` tạo sự kiện này; job cần `actions: write`, T-2402) — và không có token thì steward không cập
nhật nhánh tụt.

Ruleset sống của repo khung (kiểm `gh api repos/seeker19110/X-Templates/rules/branches/main` 2026-10-23, D-144): required
check `quality`, `protection-guard`, `gitleaks`, `dep-audit`; **"up to date" bật** (`strict: true`, khớp
`.github/rulesets/main.json`) → PR tụt sau `main` phải `update` trước khi merge, nên thiếu `XT_STEWARD_TOKEN` thì PR tụt
kẹt ở "chỉ báo" (cập nhật tay hoặc đặt token). Lệch file: ruleset sống **tắt** "Require conversation resolution"
(`required_review_thread_resolution: false`, file `true` — `WF-GIT-002`) và repo **bật** "Allow auto-merge" — chủ repo
bật/tắt lại ở Settings; file giữ chuẩn, không chép theo bản nới.

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
| Auto-merge người bật bị tắt | Đúng thiết kế (D-122): PR chưa đủ điều kiện ở head hiện tại → `disable-auto-merge` | Không bật lại; steward/`pr next` merge ghim head khi đủ điều kiện. Tắt "Allow auto-merge" ở Settings → General |
| PR đủ điều kiện mà chưa merge | CI chưa xong (`wait`); PR có nhãn `risk:`; push mới đổi head sau review; `merge_autonomy` L1/L2 (làn chuẩn ở L2 là người merge); lệnh `gh` lỗi (thiếu quyền token) | `pr next` cho `why`; review lại ở head mới; sửa quyền token |
| CI không chạy trên nhánh chính sau merge | Steward merge bằng `GITHUB_TOKEN` (thiếu `XT_STEWARD_TOKEN`) và dispatch CI lỗi: summary có `→ dispatch CI ✗ …` + `warn` (job đỏ) — thường thiếu `actions: write` (pr-steward.yml cũ), `ci.yml` thiếu `workflow_dispatch`, hoặc file CI tên khác | Chạy lại `install.py --with-github` (dự án đích); tên file CI khác: đặt biến `XT_CI_WORKFLOW`; chạy tay `gh workflow run ci.yml --ref main`; hoặc đặt secret `XT_STEWARD_TOKEN` (merge kích `push`) |
| PR tụt sau nhánh đích, không tự cập nhật | Chưa đặt `XT_STEWARD_TOKEN` (`XT_STEWARD_UPDATE=off`): commit cập nhật bằng `GITHUB_TOKEN` không kích CI nên PR kẹt chờ check; `why` ghi "đặt XT_STEWARD_TOKEN" | Đặt secret `XT_STEWARD_TOKEN`, hoặc cập nhật nhánh tay (`gh pr update-branch <N>`) |
| Run steward đỏ nhưng PR không bị gì | `warn` không gắn được nhãn `xt-standard-lane` (thiếu `issues: write`) hoặc `error` không đọc lại được PR | Xem Step Summary; lượt sau tự thử lại |
| Không thấy steward chạy | Workflow bị disable; cron GitHub bị tắt sau 60 ngày repo không hoạt động; `issue_comment` bị lọc (không phải dấu review của người có quyền ghi) | `gh workflow list`; chạy tay `gh workflow run pr-steward.yml` |
| Merge nhầm | PR đủ điều kiện máy nhưng nội dung sai | Revert commit squash qua PR mới; siết nhãn `risk:`/`merge_hard_exceptions`; ghi nguyên nhân (D-NNN nếu đổi luật) |
| Token lộ/hết hạn | `XT_STEWARD_TOKEN` | Thu hồi token ở GitHub, tạo mới, cập nhật secret (không dán giá trị vào log/commit). Chưa có token mới thì xoá secret: steward chạy bằng `GITHUB_TOKEN` — mất cập nhật nhánh, CI trên nhánh chính sau merge chạy nhờ `workflow_dispatch`, các việc khác như cũ |

Bí mật: chỉ `XT_STEWARD_TOKEN` (Settings → Secrets and variables → Actions) và biến `XT_REVIEW_IDENTITY` (tuỳ chọn);
giá trị không nằm trong repo. Liên hệ trực: chủ repo (sự cố bảo mật: `SECURITY.md`).

## 3. Tắt khẩn và khôi phục

Tắt (thứ tự nhanh nhất trước):

1. `gh workflow disable pr-steward.yml` (hoặc Actions → pr-steward → Disable workflow) — dừng mọi trigger, không đổi
   file. Run đang chạy: `gh run cancel <id>`.
2. Gỡ auto-merge đã bật cho từng PR: `gh pr merge <N> --disable-auto` (liệt kê: `gh pr list --json number,autoMergeRequest`).
3. Cắt quyền: xoá secret `XT_STEWARD_TOKEN`; Settings → General bỏ "Allow auto-merge"; ruleset nhánh chính yêu cầu review/check.
4. Dứt điểm lâu dài: PR xoá/sửa `pr-steward.yml`, nêu lý do trong PR. Máy không bật auto-merge (guard chặn mọi đường bật,
   ADR-0036), nên tắt steward là dừng mọi merge tự động ngoài phiên agent.

Khôi phục: `gh workflow enable pr-steward.yml` → `gh workflow run pr-steward.yml` → chạy
`python3 scripts/xt.py pr steward --json` đối chiếu kết quả → đặt lại secret nếu đã gỡ (không cần bật lại "Allow
auto-merge"). Sau tắt dài ngày PR cũ có thể tụt nhánh: cập nhật (steward có token hoặc `gh pr update-branch`) rồi review lại ở head mới.
Workflow bị sửa hỏng: revert commit qua PR; dự án đích chạy lại `install.py` để chép bản chuẩn.

## 4. Đẩy tag phát hành (`release-tag.yml`)

Workflow `release-tag.yml` tự chạy khi `VERSION` đổi trên `main` (từ 3.24.0, ADR-0047; `workflow_dispatch` là đường lùi) và đẩy tag bằng `GITHUB_TOKEN`; GitHub từ chối khi commit đích đổi file workflow so với tag trước
("refusing to allow a GitHub App to create or update workflow … without workflows permission", AUD-CI-014). Sửa: đặt secret
tuỳ chọn `XT_RELEASE_TOKEN` (fine-grained PAT, chỉ repo này: `contents: write` + `workflows: write`); workflow dùng nó ở bước
checkout, thiếu thì rơi về `GITHUB_TOKEN`. Thiếu secret mà commit có đổi workflow (lần đầu sau 3.24.0 chính là trường hợp này — `release-tag.yml` đổi): run tự động đỏ, người đẩy tag tay
(`git tag -a vX.Y.Z -m vX.Y.Z <sha> && git push origin vX.Y.Z`). Xoay/thu hồi như `XT_STEWARD_TOKEN` (§2).
Một push lên `main` chứa ≥ 2 commit đổi `VERSION` (merge không squash) chỉ tag commit ngọn của push (`GITHUB_SHA`); gắn tag cho
commit còn lại bằng `workflow_dispatch` với input `sha` = commit đó (AUD-DOC-086).
