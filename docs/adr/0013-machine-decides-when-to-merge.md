# ADR-0013: Máy quyết khi nào merge PR đã mở; chỉ tự merge làn nhanh ở L2

- **Trạng thái:** Đã chấp nhận
- **Trạng thái triển khai:** Đã triển khai (`scripts/xt.py` `merge-check`, `merge_decision`, `merge_lane_reasons`,
  `merge_config`, `_doctor_merge`; `.claude/hooks/guard.py` `gh_pr_merge_rule`; `pre-bash-guard.sh` trả `allow`;
  `.claude/settings.json` bỏ `Bash(gh pr merge *)` khỏi `permissions.ask`; test `tests/test_merge.py`,
  `tests/test_hooks.py::MergeGuardTest`)
- **Ngày:** 2026-10-16

## Bối cảnh

Chủ repo yêu cầu (2026-10-16): "tự động quyết định khi nào merge PR đã mở". Khung đã mô tả **làn nhanh** (5 điều kiện
+ 3 ngoại lệ cứng, `LOOP-STOP-009`) và thang tự chủ L0–L4, nhưng chỉ bằng chữ: không có máy phân làn, `gh pr merge` luôn
`ask`. Hệ quả: PR xanh nằm chờ, còn agent tự đoán "khi nào merge được" từ văn xuôi — đúng kiểu lời khai mà P1 cấm.

Dữ kiện đã xác minh (code.claude.com/docs/en/hooks, /permissions, /permission-modes; 2026-10-16): luật
`permissions.ask` khớp lệnh **vẫn hỏi** dù hook PreToolUse trả `allow`, kể cả ở chế độ `auto` và `bypassPermissions`;
hook `allow` bỏ lời hỏi của luồng quyền thường; hook im lặng không phải là cho phép.

## Quyết định

1. **`xt.py merge-check [--pr N] [--pr-json F] [--json]`** đọc `gh pr view --json …` và trả một verdict theo thứ tự:
   `closed` (không còn OPEN) → `wait` (nháp) → `fix` (xung đột) → `fix` (CI đỏ) → `wait` (CI đang chạy) → `human` (không
   có check CI nào) → `fix` (reviewer đòi sửa) → `update` (tụt sau nhánh đích) → `wait` (mergeable chưa tính) → `human`
   (làn chuẩn) → `human` (mức tự chủ < L2) → `human` (ruleset đòi review người) → `merge`. Kèm `next`: lệnh/việc kế tiếp.
   Exit 0 chỉ khi `merge`.
2. **Vị từ làn nhanh thành mã**: không đường dẫn nhạy cảm (bí mật, auth, thanh toán, mật mã, schema/migration,
   cổng/CI/harness, manifest/lockfile phụ thuộc, cộng glob `merge_risk_paths`), không nhãn `risk:*`, ≤ 150 dòng (không
   tính tài liệu, lockfile), ≤ 1 gói (gói = thư mục cấp 1, hoặc cấp 2 dưới `packages/ apps/ services/ libs/ crates/
   modules/`; tài liệu và test không tính), đổi mã thì phải đổi test. Bắt rộng có chủ đích: báo oan chỉ làm người phải
   bấm merge.
3. **Mức tự chủ ở `xt.yaml`**: `merge_autonomy: L0…L4`, mặc định `L1` (người merge mọi PR). Giá trị lạ → L1. `xt.yaml`
   là file cổng nên agent sửa nó phải qua `ask` của `pre-edit-guard` — agent không tự cấp L2 được.
4. **Thi hành ở guard**: `gh pr merge` vẫn `ask`, trừ khi đủ cả bốn: lệnh Bash chỉ gồm đúng lệnh merge đó; có
   `--match-head-commit <sha>`; không `--admin`/`--repo`; `xt.py merge-check` (bản cài cùng hook, không theo `PATH`) trả
   `merge` với `head` trùng `<sha>`. Khi đó guard trả `allow`. `--match-head-commit` làm GitHub từ chối merge nếu có
   commit mới sau lần kiểm.
5. **Settings**: bỏ `Bash(gh pr merge *)` khỏi `permissions.ask` (giữ thì không bao giờ tự merge được). `install.py`
   giữ permissions của dự án đã cài, nên `doctor` cảnh báo khi `merge_autonomy ≥ L2` mà dòng đó còn.
6. Mục checklist: mới `LOOP-STOP-022` (SHOULD); `LOOP-STOP-002` thêm ngoại lệ duy nhất này; `LOOP-STOP-009` *Kiểm* trỏ
   `merge-check`.

## Lý do

- Thời điểm merge phụ thuộc trạng thái máy đọc được (CI, mergeable, review) — đưa cho máy, không cho phán đoán.
- Mặc định L1 giữ nguyên hành vi an toàn hiện có cho mọi dự án; người bật L2 bằng một dòng, đúng thang L0–L4 đã có.
- Ghim head + lệnh đứng một mình: `allow` của hook bỏ hỏi cho **cả** lệnh Bash, nên không được ghép lệnh khác vào.

## Các phương án đã cân nhắc

- **Workflow GitHub tự bật auto-merge theo vị từ**: cần quyền `contents: write` trong CI và đổi ruleset; ngược
  `LOOP-STOP-014` (Routine không người trực chỉ đề xuất). Loại.
- **Giữ `ask` trong settings, hook trả `allow`**: tài liệu Claude Code nói luật ask vẫn hỏi. Loại.
- **Mặc định L2**: tự merge ngay trên dự án chưa có lịch sử đo (`LOOP-STOP-009` đòi đủ điều kiện lên mức). Loại.

## Hệ quả

- Guard gọi `gh` (qua `xt.py`) cho mỗi `gh pr merge`: chậm tới vài giây; lỗi mạng → `ask` (fail-closed cho merge).
- Giới hạn đã biết: guard phân tích tĩnh, không thấy `gh pr merge` giấu trong `eval`/alias/chuỗi ghép lúc chạy (như
  mọi luật khác của guard); khi đó lệnh đi luồng quyền thường. Trước đây luật settings là lớp thứ hai cho trường hợp
  này; nay chỉ còn `--admin` bị ruleset GitHub chặn nếu nhánh có bảo vệ.
- Chưa làm: merge theo thứ tự FIFO giữa nhiều PR (`LOOP-ORCH-013`) — `merge-check` xét từng PR.
