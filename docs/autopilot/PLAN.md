# PLAN.md — Khung X-Templates · sửa audit delta 2026-10-19 (#94–#157) → bản 3.8.0

> Lập ngày 2026-10-19. Chủ repo gọi `/autopilot` ngay sau `/audit` (báo cáo `docs/ops/AUDIT-REPORT-2026-10-19-delta.md`
> dừng chờ duyệt kế hoạch 5 đợt) — coi là duyệt kế hoạch sửa (D-064). Kế hoạch trước (T-1301…T-1304, 3.5.0) xong ở #140–#142.

## Tóm tắt (cổng duyệt — phiên chính tự duyệt, D-064…065)
- Phạm vi: mọi 🔴/🟠 mở của audit 2026-10-19 (2 🔴 + 17 🟠) và 🟢 cùng file khi rẻ. Mỗi bug: test tái hiện đỏ trước, sửa, xanh.
- Stack: Python ≥ 3.11 stdlib, bash; không phụ thuộc mới; cổng `scripts/dev-task.sh gate` (mypy --strict, coverage 100%).
- Không làm: tách `xt.py` (AUD-ARCH-001), tăng tốc test (AUD-PERF-001), nợ cũ chờ chủ repo (HAR-036, SEC-026, CI-006/007/009,
  SEC-043), task `[perf]` (D-041).
- Nhánh: phiên bị ràng buộc một tên nhánh `seeker/beautiful-turing-hv6jb9` → các lát đi **tuần tự** trên tên nhánh đó, mỗi lát
  một PR; lát sau chuẩn bị ở nhánh cục bộ, sau khi PR trước merge thì đặt lại nhánh từ `main` (D-065).
- Rủi ro: guard chặn nhầm lệnh hợp lệ khi thêm luật (đỡ: bộ test chặn-nhầm hiện có + test mới cho dạng hợp lệ); thay đổi
  `py_run` làm hook fail-open trên Python cũ (đỡ: giữ fail-closed khi thiếu guard, test hook thật).
- Dự án đích chạy lại `install.py` (hook/guard/xt.py đổi) → bản minor 3.8.0.

## Ngân sách (4 con số)
- Số vòng tối đa: 136 (`max(40, 8 × 17 task)` — `loop init` tính)
- Chi phí: 0 đồng ngoài phiên (không phụ thuộc mới)
- Timeout mỗi lệnh Gate: 1800 giây (`XT_RECORD_TIMEOUT` mặc định)
- Ngày hết hạn: 12 giờ sau `loop init` (`--hours 12`)

## Điểm dừng bắt buộc (`loop defer`; `loop block` khi mọi việc còn lại phụ thuộc)
- Ruleset đòi review của người (`merge-check` = `human`) → báo chủ repo, chuẩn bị lát kế ở nhánh cục bộ
- Force-push nhánh có lịch sử chưa merge, xoá nhánh, đổi quyền/ruleset repo

## Task

### Lát A — sổ audit + maxTurns (PR đầu, các commit đã có trên nhánh)
- [x] `T-1401` Mở PR cho `docs(audit)` + `chore(agents)` maxTurns, đi tới merge — Gate: `python3 scripts/xt.py audit check docs/ops/AUDIT-STATUS.md`

### Lát B — guard 🔴/🟠 (AUD-SEC-063…069, + 🟢 SEC-070/071 nếu rẻ)
- [x] `T-1402` Shell lồng quá `MAX_NEST` → deny (AUD-SEC-063) — Gate: `python3 -m unittest discover -s tests -k nest_too_deep_denied`
- [x] `T-1403` Brace expansion: bung hữu hạn rồi xét từng biến thể; vượt trần → deny (AUD-SEC-064) — Gate: `python3 -m unittest discover -s tests -k brace_expansion`
- [x] `T-1404` Hook chạy python cách ly (`-I`), pycache không nằm ở chỗ agent ghi được ngoài dự án (AUD-SEC-065) — Gate: `python3 -m unittest discover -s tests -k guard_cache_tamper`
- [x] `T-1405` `pre-mcp-guard.sh` so `tool_name` cấp đầu đã parse (AUD-SEC-066) — Gate: `python3 -m unittest discover -s tests -k mcp_disable_regex_scoped`
- [x] `T-1406` Gửi file bí mật qua `scp`/`rsync`/`nc`/`socat`/`gh gist` → deny (AUD-SEC-067) — Gate: `python3 -m unittest discover -s tests -k secret_exfil_other_channels`
- [x] `T-1407` Xoá/huỷ ngoài dự án (`rsync --delete`, `shred`, `mv ~`) → deny (AUD-SEC-068) — Gate: `python3 -m unittest discover -s tests -k delete_outside_project`
- [x] `T-1408` Dấu `xt-review v1` đăng tay qua `gh pr comment|review`/`gh api` → deny (AUD-SEC-069) — Gate: `python3 -m unittest discover -s tests -k review_marker_forge_denied`

### Lát C — merge/steward (AUD-HAR-058/059, AUD-XFEAT-003/004)
- [x] `T-1409` `merge-gate` (và check không kiểm mã) không là bằng chứng CI xanh (AUD-HAR-058) — Gate: `python3 -m unittest discover -s tests -k merge_gate_not_ci_evidence`
- [x] `T-1410` Dự án con: khoá `xt.yaml` và `merge_risk_paths` tính theo tiền tố dự án (AUD-XFEAT-003/004) — Gate: `python3 -m unittest discover -s tests -k subproject`
- [x] `T-1411` Review chặn ở đúng head hiện tại thắng review sạch mang sang (AUD-HAR-059) — Gate: `python3 -m unittest discover -s tests -k blocking_at_head_wins`

### Lát D — cổng máy xanh giả (AUD-XFEAT-005…009)
- [x] `T-1412` `perf guard` thấy file ignore tự che trong vùng khoá (AUD-XFEAT-005) — Gate: `python3 -m unittest discover -s tests -k perf_guard_self_ignored`
- [x] `T-1413` `contrast`: cặp không đọc được là đỏ; alpha `none` không sập (AUD-XFEAT-006/008) — Gate: `python3 -m unittest discover -s tests -k contrast_skip_is_red`
- [x] `T-1414` `vendor-check` khớp nguyên tên file ghi nguồn, bỏ file ẩn (AUD-XFEAT-007/009) — Gate: `python3 -m unittest discover -s tests -k vendor_notice_fullname`

### Lát E — tài liệu, bằng chứng blueprint, sổ audit, phát hành
- [x] `T-1415` Tài liệu + bằng chứng blueprint (AUD-DOC-044/045, AUD-HAR-060/061/062, 🟢 DOC-046…050, HAR-068/069) — Gate: `scripts/dev-task.sh lint`
- [x] `T-1416` Sổ audit: phát hiện đã sửa kèm PR, quét lại nhóm bị chạm — Gate: `python3 scripts/xt.py audit check docs/ops/AUDIT-STATUS.md`
- [x] `T-1417` VERSION 3.8.0 + CHANGELOG `[3.8.0]` + PROGRESS; tag `v3.8.0` qua `release-tag.yml` — Gate: `scripts/dev-task.sh gate`
