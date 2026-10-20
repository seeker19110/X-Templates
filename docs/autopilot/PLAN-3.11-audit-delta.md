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
- [ ] `T-1601` Audit delta `f36ea90..0afa30d` nhóm 1/2/3/4/8/9/12/13 + bằng chứng blueprint cũ; sổ ghi SHA quét `0afa30d`, báo cáo `docs/ops/AUDIT-REPORT-2026-10-20-delta2.md` — Gate: `python3 scripts/xt.py audit check docs/ops/AUDIT-STATUS.md --strict`

### Lát B — sửa 🔴/🟠 (thêm task theo phát hiện của T-1601)

### Lát C — quét lại theo diff bản sửa, phát hành
- [ ] `T-1690` Quét lại theo diff bản sửa của lát B; sổ ghi SHA quét = HEAD lát B — Gate: `python3 scripts/xt.py audit check docs/ops/AUDIT-STATUS.md --strict`
- [ ] `T-1691` `release-check` GO trên cây cuối (sau `loop verify --all`) — Gate: `python3 scripts/xt.py release-check`
