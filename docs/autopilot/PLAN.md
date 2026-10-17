# PLAN.md — Khung X-Templates · trả nợ 🟢 audit tự làm được

> Lập ngày 2026-10-17. Chủ repo gọi lại `/autopilot` sau khi PLAN T-801…T-804 xong (#82, #83).
> Nguồn: `docs/ops/AUDIT-STATUS.md` (28 🟢 mở). Kế hoạch trước (T-801…T-804) xong ở #82/#83.

## Tóm tắt (cổng duyệt — phiên chính tự duyệt, D-017)
- Blueprint repo khung: không đổi mục; `audit check --strict` exit 0 (0 🟠 mở) — đây là trả nợ 🟢.
- Stack: Python ≥ 3.11 stdlib (`guard.py`, `xt.py`); không phụ thuộc mới.
- Phạm vi (chỉ mã/test, không chạm hook/settings/CI): guard git lọt (AUD-SEC-023/024), CLI container khác (AUD-SEC-042);
  `doctor` kiểm công cụ cổng (AUD-HAR-034); `feedback collect` không sinh phản hồi trong chính repo khung (AUD-HAR-048, mới);
  test sạch (AUD-TEST-003/004); `feedback aggregate` gộp đúng (AUD-CODE-004).
- Ngoài phạm vi, cần người (đổi cấu hình hook/settings/CI — điểm dừng): AUD-HAR-036/041 (matcher settings), AUD-SEC-026
  (timeout hook), AUD-CI-006/007/009 (workflow). Cần quyết chính sách: AUD-SEC-043 (`npx`/`dlx`).
- Nhánh: phiên chỉ push một nhánh → lát xếp nối thành commit riêng (D-016); bắt đầu sau khi #83 merge.
- Rủi ro: guard hỏi oan mới → test cả ca không hỏi; reviewer khác rà diff trước bật auto-merge.

## Ngân sách (4 con số)
- Số vòng tối đa: 20 (`max(20, 4 × task)`)
- Chi phí: 0 đồng ngoài phiên (không phụ thuộc mới)
- Timeout mỗi lệnh Gate: 600 giây
- Ngày hết hạn: 4 giờ sau `loop init` (`--hours 4`)

## Điểm dừng bắt buộc (`loop defer`; `loop block` khi mọi việc còn lại phụ thuộc)
- Đổi cấu hình hook/settings/CI (các mục ngoài phạm vi ở trên) — chờ chủ repo
- Merge PR thuộc ngoại lệ cứng (ADR-0016) — không có trong kế hoạch này
- Force-push, xoá nhánh, đổi quyền/ruleset repo

## Task

- [x] `T-901` Guard: git tuỳ chọn dài viết tắt (`reset --ha`, `push --mirr`), `push --all/--tags`, `dd of=/dev/…`, `find -delete`, `xargs rm -rf`, `exec -a` (AUD-SEC-023/024); `docker-compose`/`podman-compose`/`nerdctl`/`kubectl exec` (AUD-SEC-042) — Gate: `python3 -m unittest tests.test_hooks`
- [x] `T-902` `doctor` cảnh báo công cụ cổng thiếu trong PATH (AUD-HAR-034); `feedback collect` bỏ qua ở repo khung (AUD-HAR-048); test không rò stderr, kiểm verdict `budget` (AUD-TEST-003/004) — Gate: `python3 -m unittest tests.test_xt tests.test_xt_core tests.test_xt_cli tests.test_doctor`
- [x] `T-903` `feedback aggregate` gộp theo loại + ID + lý do chuẩn hoá, không theo ID task cục bộ; báo cáo in mọi triệu chứng khác nhau (AUD-CODE-004) — Gate: `python3 -m unittest tests.test_xt tests.test_xt_core`
- [ ] `T-904` Sổ audit đánh dấu đã sửa (#PR), PROGRESS, cổng đầy đủ — Gate: `python3 scripts/xt.py audit check docs/ops/AUDIT-STATUS.md --strict && python3 scripts/xt.py progress-check && scripts/dev-task.sh gate`
