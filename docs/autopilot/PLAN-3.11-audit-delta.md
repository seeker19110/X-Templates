# PLAN-3.11-audit-delta.md — Khung X-Templates · audit delta `f36ea90..0afa30d` → `release-check` GO

> Lập ngày 2026-10-20. Chủ repo gọi `/autopilot` không kèm yêu cầu mới → nối tiếp PROGRESS "Tiếp theo 0": sau #185/#186
> chạy `loop verify --all` rồi `release-check`. `release-check` tại `0afa30d` = NO-GO, hàng `review_debt` FAIL: 16 file
> ngoài tài liệu (`guard.py`, `pre-bash-guard.sh`, `pr-steward.yml`, `release-tag.yml`, `xt.py`, test) đổi sau SHA quét
> `f36ea90` của sổ audit (ADR-0031). Hàng `blueprint` đỏ chỉ vì clone nông thiếu tag (`git fetch --tags` → xanh).
>
> **Cú pháp bắt buộc cho máy:** mỗi task một dòng `- [ ] \`T-NNNN\` <việc> — Gate: \`<lệnh>\``.

## Tóm tắt (cổng duyệt — phiên chính tự duyệt)
- Phạm vi: audit delta `f36ea90..0afa30d` (3 commit #184…#186) theo nhóm bị chạm — 1 ARCH, 2 SEC, 3 CODE, 4 TEST, 8 CI,
  9 DOC, 12 XFEAT, 13 HAR — kèm xác minh lại bằng chứng blueprint `stale_evidence`; sửa mọi 🔴/🟠 (test tái hiện đỏ trước,
  sửa, xanh); quét lại theo diff của bản sửa; `release-check` GO.
- Stack: Python ≥ 3.11 stdlib, bash; không phụ thuộc mới; cổng `scripts/dev-task.sh gate` (mypy --strict, coverage 100 %).
- Không làm: tách `xt.py` (AUD-ARCH-001), nợ chờ chủ repo (`XT_RELEASE_TOKEN`, AUD-HAR-036, AUD-SEC-026, AUD-CI-006/007/009,
  AUD-SEC-043), task `[perf]` (D-041), cắt bản mới (chỉ khi bản sửa buộc dự án đích chạy lại `install.py`).
- Người quét: subagent theo nhóm; mọi 🔴/🟠 xác minh đối kháng bởi reviewer khác họ model với người quét.
- Nhánh: phiên bị ràng buộc `seeker/intelligent-fermat-aq178u` → lát đi tuần tự trên tên nhánh này, mỗi lát một PR (D-065).
- Rủi ro: sửa guard chặn oan lệnh hợp lệ (đỡ: bộ test chặn-nhầm + `autonomy-bench`); vòng quét–sửa không hội tụ (đỡ: quét
  lại chỉ theo diff bản sửa, bản sửa đã qua review PR).

## Ngân sách (4 con số)
- Số vòng tối đa: 40 (`max(40, 8 × task)` — `loop init` tính)
- Chi phí: 0 đồng ngoài phiên (không phụ thuộc mới)
- Timeout mỗi lệnh Gate: 1800 giây (`XT_RECORD_TIMEOUT` mặc định)
- Ngày hết hạn: 12 giờ sau `loop init` (`--hours 12`)

## Điểm dừng bắt buộc (`loop defer`; `loop block` khi mọi việc còn lại phụ thuộc)
- Đặt secret, đổi ruleset/quyền repo, xoá nhánh, force-push nhánh có lịch sử chưa merge
- Phát hiện cần chủ repo chọn hướng (đổi luật merge, đổi chính sách guard ảnh hưởng dự án đích) → ghi `loop defer`

## Task

### Lát A — audit delta
- [x] `T-1601` Audit delta `f36ea90..0afa30d` nhóm 1/2/3/4/8/9/12/13 + bằng chứng blueprint cũ; sổ ghi SHA quét `0afa30d`, báo cáo `docs/ops/AUDIT-REPORT-2026-10-20-delta2.md` — Gate: `python3 scripts/xt.py audit check docs/ops/AUDIT-STATUS.md`

> Gate T-1601 không `--strict`: `--strict` đòi 0 🔴/🟠 mở — đỏ đúng thiết kế khi audit vừa tìm ra lỗi; `--strict` ở T-1690.

### Lát B — sửa 🔴/🟠 (theo phát hiện của T-1601; 21 phát hiện: 🔴 1 · 🟠 3 · 🟢 17)
- [x] `T-1602` Guard: dấu che giả `\x01N\x02` fail-open (AUD-SEC-091 🔴, hồi quy) + quét bậc hai theo số chuỗi canh (AUD-SEC-092, hồi quy) — Gate: `python3 -m unittest tests.test_guard_audit1020b`
- [x] `T-1603` Guard: cờ trình thông dịch ghép/dính, `nodejs`, lệnh chạy hộ `uv/poetry/pipx/pipenv run`, `npx`, `npm exec --` (AUD-SEC-093) — Gate: `python3 -m unittest discover -s tests -k guard_interp_flag_forms`
- [x] `T-1604` Guard: sau `cd` quét `$(…)`/backtick/`<(…)`/lệnh bọc với thư mục đã đổi (AUD-SEC-094) — Gate: `python3 -m unittest discover -s tests -k guard_nested_cwd_runners`
- [x] `T-1605` Guard: `~+`/`~-` (AUD-SEC-097) và `source /dev/stdin` (AUD-SEC-098) — Gate: `python3 -m unittest discover -s tests -k guard_tilde_plus_minus`
- [x] `T-1606` merge-check: sổ review hỏng không văng (AUD-CODE-019), bản ghi cùng giây lấy bản cuối (AUD-XFEAT-018); test hook nhánh xt.py lỗi (AUD-TEST-016) — Gate: `python3 -m unittest discover -s tests -k local_blocking -k commit_gate_xt_py_broken`
- [x] `T-1608` Guard: `rm -rf $PWD/..`, `~+/..`, `$PWD`, `~-/x` (AUD-SEC-099, executor-deep tìm khi sửa T-1605) — Gate: `python3 -m unittest discover -s tests -k guard_rm_pwd`
- [x] `T-1607` Tài liệu + giới hạn 🟢 (AUD-SEC-095/096, XFEAT-019, HAR-100, DOC-072…075), trọng số shard (AUD-TEST-017), CHANGELOG — Gate: `scripts/dev-task.sh lint`

### Lát C — quét lại theo diff bản sửa, phát hành
- [ ] `T-1690` Quét lại theo diff bản sửa của lát B; sổ ghi SHA quét = HEAD lát B — Gate: `python3 scripts/xt.py audit check docs/ops/AUDIT-STATUS.md --strict`
- [ ] `T-1691` `release-check` GO trên cây cuối (sau `loop verify --all`) — Gate: `python3 scripts/xt.py release-check`
