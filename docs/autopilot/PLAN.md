# PLAN.md — Khung X-Templates · đóng audit delta #68–#80 (sau đợt 1)

> Lập ngày 2026-10-17. Chủ repo duyệt kế hoạch sửa ("duyệt kế hoạch, sửa đợt 1"), đợt 1 merge ở #81, rồi gọi `/autopilot`.
> Nguồn: `docs/ops/AUDIT-REPORT-2026-10-17-delta.md`, `docs/ops/AUDIT-STATUS.md`. Kế hoạch trước (T-701…T-704) xong ở #69–#75.

## Tóm tắt (cổng duyệt — phiên chính tự duyệt, D-014)
- Blueprint repo khung: không đổi mục; `audit check --strict` đã exit 0 (0 🟠 mở) sau #81.
- Stack: Python ≥ 3.11 stdlib (`guard.py`), tài liệu Markdown; không phụ thuộc mới.
- Phạm vi: đợt 2 tài liệu (AUD-DOC-038…040, AUD-SEC-036 bằng quy trình) + 2 🟢 guard từ review #81 (AUD-SEC-041, AUD-HAR-047).
  Mỗi lát một PR mở kèm auto-merge (L3); `merge-check` có `hard` thì không bật.
- Ngoài phạm vi, chờ người: AUD-CI-009 (thêm job Python 3.9 vào CI — đổi cấu hình CI là điểm dừng; chủ repo vừa gỡ macOS ở #79).
- Rủi ro: guard hỏi oan mới khi quét sâu lệnh trong container → test cả ca không hỏi; reviewer khác rà diff trước merge.

## Ngân sách (4 con số)
- Số vòng tối đa: 20 (`max(20, 4 × task)`)
- Chi phí: 0 đồng ngoài phiên (không phụ thuộc mới)
- Timeout mỗi lệnh Gate: 600 giây
- Ngày hết hạn: 4 giờ sau `loop init` (`--hours 4`)

## Điểm dừng bắt buộc (`loop defer`; `loop block` khi mọi việc còn lại phụ thuộc)
- Đổi cấu hình CI/cổng (AUD-CI-009) — chờ chủ repo
- Merge PR thuộc ngoại lệ cứng (ADR-0016) — không có trong kế hoạch này
- Force-push, xoá nhánh, đổi quyền/ruleset repo

## Task

- [x] `T-801` Guard quét lệnh `sh -c` trong container (`exec`/`run`/`compose run --entrypoint sh`) và sau wrapper (`uv run bash -c`) (AUD-SEC-041) — Gate: `python3 -m unittest tests.test_hooks.GuardEgressAuditTest`
- [x] `T-802` Mount đường dẫn tuyệt đối nằm trong gốc dự án không hỏi oan theo mảnh tên (AUD-HAR-047) — Gate: `python3 -m unittest tests.test_hooks.GuardEgressAuditTest tests.test_hooks.GuardEgressTest`
- [ ] `T-803` Đợt 2 tài liệu: README đếm file mảng 05–09 (AUD-DOC-038), dòng `portability.yml` cũ trong CHANGELOG (AUD-DOC-039), độ chắc nguồn QA-STRAT-023/UX-VIZ (AUD-DOC-040), quy trình chạy lại `merge-check` sau mỗi push vào PR đang auto-merge (AUD-SEC-036) — Gate: `python3 scripts/xt.py validate && python3 scripts/check-links.py && python3 scripts/xt.py changelog-check`
- [ ] `T-804` Sổ audit đánh dấu đã sửa (#PR), PROGRESS, cổng đầy đủ — Gate: `python3 scripts/xt.py audit check docs/ops/AUDIT-STATUS.md --strict && python3 scripts/xt.py progress-check && scripts/dev-task.sh gate`
