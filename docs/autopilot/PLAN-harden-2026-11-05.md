# PLAN-harden-2026-11-05.md — harden nhánh `claude/amazing-brahmagupta-9jqbg1` (ADR-0068 lát A · ADR-0069 · ADR-0070)

> Lập 2026-11-05 theo `/complete` của chủ dự án, cùng ràng buộc của chủ dự án: **không mở PR, không merge vào `main`** —
> mọi lát là commit trên nhánh; PR/merge/ký GO-NO-GO là việc người. Duyệt: D-358 (phiên chính tự duyệt, ADR-0008).
> Nguồn: audit delta phần riêng của nhánh (`git diff origin/main...HEAD`) — review đối kháng ADR-0069 (REQUEST CHANGES
> 1 🔴 · 2 🟠 · 3 🟢) và ADR-0070 (APPROVE kèm nợ 1 🟠 · 4 🟢); lát A đã review (`57440e5`). Phần guard của `main`
> (#433…#439, AUD-SEC-492…496, AUD-PERF-019) thuộc phiên guard — không làm song song ở đây.
>
> **Cú pháp bắt buộc cho máy:** mỗi task một dòng `- [ ] \`T-NNNN\` <việc> — Gate: \`<lệnh>\``.

## Tóm tắt (cổng duyệt)
- `release-check` lần 1 (HEAD `43df14d`): NO-GO — `audit` (nợ #439, phiên guard), `review_debt` (19 file sau SHA quét);
  chờ người: `prod_switch`, `go_no_go`. gitleaks `origin/main..HEAD` sạch.
- 🔴 F1: ADR-0069 nới guard so với `main` — `env -u CLAUDECODE … xt.py stage approve` qua guard, xt.py coi là người →
  duyệt bản đã đổi, sổ ghi người. Sửa hai lớp: khoá bật thì MỌI `stage approve` đòi bản trình còn nguyên; guard chỉ cho
  đúng một lệnh đơn `python3 <xt.py của dự án> stage approve --sha … [--note …]`.
- 🟠 F2: `git remote set-head` lật `origin/HEAD` → tự cấp khoá; bỏ `origin/HEAD` khỏi ref đọc khoá, guard thêm
  `--no-replace-objects`. 🟠 F3: PR đổi `stage_approval` là khoá cứng như `merge_hard_exceptions`.
- 🟢 F6 agent chỉ duyệt MVP (giai đoạn 1); F5 tài liệu; ADR-0070 🟢 đã sửa (đường dẫn cũ, `.ignore` neo gốc, README).
- Nợ ghi sổ: F4 (`--note` có ký tự glob bị chặn oan), `python -c` gọi `xt.main` (có từ trước), ADR-0070 🟠 đóng gói lát,
  ID task trùng có từ trước, hạ trần byte sau lưu trữ.

## Ngân sách (4 con số)
- Số vòng tối đa: bỏ trống · Chi phí: 0 đồng ngoài phiên · Timeout Gate: 1200 giây · Hạn: 24 giờ

## Điểm dừng bắt buộc về hành động
- Mở PR, merge, cắt bản, ký GO-NO-GO, quyết "Khi chạy thật" (`prod_switch`): việc người (chủ dự án 2026-11-05).

## Task
- [x] `T-3680` 🔴 F1 xt.py: khoá `stage_approval: agent` bật → mọi `stage approve` đòi bản trình còn nguyên; agent chỉ duyệt giai đoạn 1 (F6) — Gate: `python3 -m unittest tests.test_stage_agent_approval`
- [x] `T-3681` 🔴 F1 guard: `_plain_approve` chỉ nhận một lệnh đơn `python3|python <xt.py của dự án> stage approve` với `--sha`/`--note`, không `env`/`unset`/gán biến/cờ trình thông dịch (sau: T-3680) — Gate: `python3 -m unittest tests.test_stage_agent_approval`
- [x] `T-3682` 🟠 F2: ref đọc khoá giai đoạn chỉ `origin/main` → `origin/master` (guard + xt.py), guard `git --no-replace-objects show` — Gate: `python3 -m unittest tests.test_stage_agent_approval`
- [x] `T-3683` 🟠 F3: `_hard_key_lines` gồm `stage_approval` — PR đổi khoá này luôn người merge — Gate: `python3 -m unittest tests.test_merge`
- [x] `T-3684` Tài liệu (F5) + ADR-0069 trạng thái + CHANGELOG + sổ nợ (sau: T-3683) — Gate: `scripts/dev-task.sh gate-fast`
