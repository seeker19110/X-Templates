# ADR-0014: Mỗi lát code một PR; máy tự merge khi `merge-check` cho phép, lệnh merge ghim head

- **Trạng thái:** Đã chấp nhận
- **Trạng thái triển khai:** Đã triển khai (`.claude/hooks/guard.py` `_gh_api_merge_rule`, `mcp_decision`,
  `_merge_verdict`; `.claude/hooks/pre-mcp-guard.sh`; `scripts/xt.py` `merge_decision` trả `repo`; mục `LOOP-DESIGN-020`;
  `xt.yaml` của repo khung `merge_autonomy: L2`; test `tests/test_hooks.py::MergeGuardTest`)
- **Ngày:** 2026-10-16
- **Mở rộng:** ADR-0013 (máy quyết khi nào merge) — không thay; quyết định D-010

## Bối cảnh

Chủ repo yêu cầu (2026-10-16): "tạo PR và auto merge theo từng lát code". Hiện autopilot commit dồn trên một nhánh rồi
mở "PR cuối" (11-autonomous-loop/README.md bước 15); ADR-0013 đã có máy quyết thời điểm merge (`xt.py merge-check`) và
chỉ cho tự merge làn nhanh ở L2, nhưng chỉ qua `gh pr merge` — lệnh này dùng GraphQL nên không chạy được ở phiên Claude
Code chặn GraphQL (D-009), và tool MCP merge không đi qua hook nào (AUD-SEC-020).

Dữ kiện (xác minh 2026-10-16):
- REST `PUT /repos/{owner}/{repo}/pulls/{n}/merge` nhận `sha` ("SHA that pull request head must match"), trả 409 khi
  lệch (docs.github.com/en/rest/pulls/pulls#merge-a-pull-request).
- Tool MCP `merge_pull_request` có `expectedHeadSha`; `enable_pr_auto_merge` không có tham số head và "fails … if the PR
  is already mergeable (clean status)" (mô tả tool của GitHub MCP server).
- `gh pr merge --auto`: "Automatically merge only after necessary requirements are met"; tài liệu không nói hành vi khi
  PR đã sẵn sàng (cli.github.com/manual/gh_pr_merge) — (chưa xác minh) phần này.

## Quyết định

1. **Lát = đơn vị PR.** Mỗi lát dọc chạy được (một task hoặc nhóm task PLAN có Gate xanh) có nhánh riêng tách từ nhánh
   đích mới nhất và một PR nhỏ, mở ngay khi Gate của lát xanh. Bỏ "PR cuối". Lát phụ thuộc PR chưa merge → nhánh chồng
   lên nhánh đó, PR nhắm nhánh đó; merge theo FIFO (`LOOP-ORCH-013`). Không xoá nhánh khi merge (xoá nhánh là điểm dừng),
   nên GitHub không tự đổi đích: sau khi PR đáy merge: đổi đích PR chồng về nhánh mặc định (`gh pr edit <N> --base main` hoặc API), `git fetch origin main && git merge origin/main` vào nhánh chồng (squash để lại commit trùng của lát đáy; merge, không rebase/force-push), push, chạy lại `merge-check` — PR còn nhắm nhánh khác nhánh mặc định thì `merge-check` trả `wait`.
2. **Máy tự merge, không dùng auto-merge của GitHub.** Sau khi mở PR và ở mỗi vòng/sự kiện PR: `xt.py merge-check --pr N`;
   `merge` → chạy lệnh merge ghim head; `wait`/`update`/`fix` → làm theo `next` rồi làm lát khác; `human` → `loop defer`.
   Auto-merge của GitHub bị loại: bật xong thì commit đẩy sau vẫn tự merge mà không qua vị từ làn nhanh.
3. **Ba đường merge, một chốt.** Guard `allow` khi `merge-check` = `merge`, head đã kiểm = head ghim trong lệnh, lệnh
   đứng một mình và trơn:
   - `gh pr merge N --squash --match-head-commit <sha>` (như ADR-0013);
   - `gh api -X PUT repos/{owner}/{repo}/pulls/N/merge -f sha=<sha> [-f merge_method=squash|merge|rebase]` — chỉ dạng
     placeholder `{owner}/{repo}` (repo hiện tại, cùng repo `merge-check` đọc);
   - tool MCP `…__merge_pull_request` có `expectedHeadSha`, `owner/repo` trùng `repo` mà `merge-check` trả.
   Mọi dạng khác (`enable_pr_auto_merge`, `--auto`, khoá/cờ lạ) → hỏi người.
4. **Ngoại lệ giữ nguyên:** làn chuẩn (bí mật, auth, thanh toán, mật mã, schema, cổng/CI/harness/luật agent, phụ thuộc,
   > 150 dòng, > 1 gói, đổi mã không đổi test) luôn để người merge (`WF-REVIEW-007` MUST).
5. **Repo khung bật `merge_autonomy: L2`** (theo yêu cầu trên). Mẫu dự án đích giữ mặc định L1.

## Lý do

- Ghim head ở cả ba đường giữ nguyên bảo đảm của ADR-0013: thứ được merge đúng là thứ máy đã kiểm.
- REST và MCP làm luật chạy được ở phiên chặn GraphQL — nơi autopilot của khung thường chạy.
- PR theo lát: diff nhỏ để review/vị từ làn nhanh có nghĩa; lỗi lộ ở lát của nó, không ở "PR cuối" hàng nghìn dòng.

## Các phương án đã cân nhắc

- **Auto-merge của GitHub khi mở PR**: không ghim head, cần GraphQL, thất bại khi PR đã clean. Loại (D-010).
- **Auto-merge mọi PR khi CI xanh, bỏ vị từ làn nhanh**: trái `WF-REVIEW-007`; audit 2026-10-16 (AUD-HAR-021…023) cho thấy
  chỉ "CI xanh" chưa đủ. Loại.
- **Một PR cho cả PLAN như cũ**: không đáp ứng yêu cầu. Loại.

## Hệ quả

- Ở repo khung, phần lớn PR chạm `.claude/`, `scripts/dev-task.sh`, `xt.yaml` hoặc `AGENTS.md` → làn chuẩn → người merge;
  tự merge áp cho PR nội dung `framework/` + test nhỏ.
- Agent phải chạy `merge-check` lại sau mỗi sự kiện PR; không có webhook thì mỗi vòng autopilot (bước 10).
- Giới hạn: guard phân tích tĩnh (như ADR-0013); `merge-check` đọc repo theo `gh` ở thư mục dự án.
