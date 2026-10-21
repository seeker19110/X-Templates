# ADR-0015: Mở PR là bật auto-merge (mức `merge_autonomy: L3`) — repo khung và dự án đích

- **Trạng thái:** Đã chấp nhận — bị thay một phần bởi ADR-0024 (thời điểm bật auto-merge: làn chuẩn sau review sạch; làn nhanh vẫn khi vừa mở); §1 (L3 merge cả làn chuẩn) và §4 (miễn `WF-REVIEW-007`) bị thay một phần bởi ADR-0016 —
  ngoại lệ cứng (tiền, dữ liệu thật, auth, mật mã, bí mật) vẫn người merge ở L3; cơ chế (bật auto-merge của GitHub, guard cho bật ở L3) thay bởi ADR-0036 (2026-10-21) — L3 giữ nghĩa
  máy merge mọi làn trừ ngoại lệ cứng, bằng merge ghim head; guard chặn phẳng việc bật auto-merge
- **Trạng thái triển khai:** Đã triển khai (`scripts/xt.py` `merge_decision` — L3 bỏ chặn làn chuẩn, trả `autonomy`,
  `stacked`; `.claude/hooks/guard.py` `_auto_merge_verdict`, `gh_pr_merge_rule` nhận `--auto`, `_mcp_auto_merge` cho
  `mcp__github__enable_pr_auto_merge`; `xt.yaml` và `framework/templates/xt.yaml` `merge_autonomy: L3`; test
  `tests/test_hooks.py::MergeGuardTest::test_l3_enables_auto_merge_on_open`, `tests/test_merge.py`)
- **Ngày:** 2026-10-16
- **Thay một phần:** ADR-0014 §2 (không dùng auto-merge của GitHub) và D-010 — quyết định D-011

## Bối cảnh

Chủ repo yêu cầu (2026-10-16): "mở pr luôn kèm auto merge để merge tự động — cả repo này lẫn repo đích". ADR-0014 chỉ
cho máy tự merge làn nhanh bằng lệnh ghim head, làn chuẩn (cổng/CI/hook/luật agent…) để người; thực tế ở repo khung gần
như mọi PR chạm `.claude/` nên PR xanh vẫn nằm chờ người bấm.

Dữ kiện (2026-10-16): repo bật `allow_auto_merge` và `delete_branch_on_merge`; ruleset `main` đòi 4 required check
(`quality`, `protection-guard`, `gitleaks`, `dep-audit`); tool MCP `enable_pr_auto_merge` bật được trong phiên chặn
GraphQL; GitHub chỉ merge khi required check/ruleset đạt.

## Quyết định

1. **Mức mới `merge_autonomy: L3`**: mở PR xong thì bật auto-merge ngay (`gh pr merge <N> --auto --squash`, hoặc tool
   MCP `enable_pr_auto_merge` với `mergeMethod: SQUASH`) cho **mọi làn**; GitHub merge khi CI bắt buộc xanh.
   `merge-check` ở L3 trả `merge` cho cả làn chuẩn (người vẫn quyết khi ruleset đòi review của người).
2. **Guard cho phép bật auto-merge khi** `merge-check` báo `autonomy` ≥ 3, PR còn mở, **không phải PR chồng** (nhắm
   nhánh khác nhánh mặc định — merge vào đó là merge vào nhánh sắp bị xoá) và (MCP) đúng repo; lệnh trơn, không
   `--admin`, không cờ lạ. Dưới L3 bật auto-merge vẫn hỏi.
3. **Mặc định L3** cho repo khung (`xt.yaml`) và mẫu dự án đích (`framework/templates/xt.yaml`). Dự án muốn người merge
   làn chuẩn đặt L2; muốn người merge mọi PR đặt L1.
4. Dự án ở L3 ghi miễn trừ `WF-REVIEW-007` (vùng nhạy cảm luôn người review) trong BLUEPRINT — chủ dự án đã chọn.

## Lý do

- Người dùng có quyền cuối (AGENTS.md §1); quyết định đã rõ.
- Giữ phần cốt lõi của an toàn: CI bắt buộc của ruleset vẫn chặn merge đỏ; `--admin` (vượt ruleset) vẫn hỏi; PR chồng
  không tự merge; guard và cổng commit vẫn chạy trên từng commit trước khi lên PR.

## Các phương án đã cân nhắc

- **Giữ ADR-0014 (máy chỉ tự merge làn nhanh)**: an toàn hơn cho thay đổi harness nhưng không đáp ứng yêu cầu. Loại.
- **L3 nhưng loại trừ `.claude/`**: chủ repo yêu cầu "luôn"; ở repo khung gần như mọi PR chạm `.claude/`. Loại.

## Hệ quả

- **Mất ghim head**: commit đẩy lên PR sau khi bật auto-merge cũng tự merge khi CI xanh — mỗi commit vẫn qua cổng commit
  (hook) và CI bắt buộc.
- **Mất vị từ làn nhanh** cho việc merge: thay đổi hook/guard/CI/luật agent tự merge mà không người xem — rủi ro agent tự
  nới hàng rào rồi tự đưa lên `main`; lớp đỡ còn lại là CI (test của guard) và review sau merge. Đổi về L2 để lấy lại.
- Repo không bật "Allow auto-merge" hoặc không có required check: `enable_pr_auto_merge` thất bại (PR đã clean) → dùng
  `merge-check` + lệnh merge ghim head như ADR-0014.
