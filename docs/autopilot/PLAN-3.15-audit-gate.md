# PLAN-3.15-audit-gate.md — Khung X-Templates · sửa phát hiện audit 2026-10-21 (bằng chứng Gate, cổng nhất quán)

> Lập ngày 2026-10-21. Chủ repo: "đọc commit mới, kiểm tra lại, nghiên cứu thêm rồi thi hành" — commit chưa merge
> `d388802` (nhánh `docs/audit-workflow-optimization-20261021`): [audit tại `ec4c7d2`](../ops/AUDIT-REPORT-2026-10-21.md)
> và [kế hoạch tối ưu](../ops/OPTIMIZATION-PLAN-2026-10-21.md). Phiên chính tái hiện độc lập từng phát hiện (mỗi phát hiện
> một agent tái hiện + hai agent bác bỏ) rồi tự duyệt PLAN (D-130, ADR-0008). Kết quả xác minh: sổ
> [`AUDIT-STATUS.md`](../ops/AUDIT-STATUS.md) và báo cáo, mục "Xác minh lại 2026-10-21".
>
> **Cú pháp bắt buộc cho máy:** mỗi task một dòng `- [ ] \`T-NNNN\` <việc> — Gate: \`<lệnh>\``.

## Tóm tắt (cổng duyệt — phiên chính tự duyệt, D-130)
- Vấn đề: cổng xanh hiện hành chưa đủ làm bảo chứng — `same_command` nhận bằng chứng của lệnh khác nghĩa (🔴 cổng giả xanh
  tới Stop hook), `dev-task.sh` nhận `Ran 0 tests` exit 0, guard bỏ kiểm nhánh khi có chuyển hướng, reviewer CI nhận diff
  bị cắt, installer ghi workflow sai chỗ và ghi xuyên symlink.
- Thứ tự (theo kế hoạch tối ưu, đúng và an toàn trước tốc độ): Lát 1 bằng chứng Gate → Lát 2 cổng nhất quán → Lát 3
  guard/reviewer → Lát 4 installer → Lát 5 đo CI. PLAN-3.14-app (app cục bộ) tạm dừng tới khi Lát 1–3 merge: app hiển thị
  kết quả của chính các cổng này.
- Stack: Python ≥ 3.11 stdlib, bash; 0 phụ thuộc mới. Mỗi bug: test tái hiện đỏ trước, sửa, xanh; `autonomy-bench` thêm ca.
- Không làm: tách `xt.py` (AUD-ARCH-001), đổi kiến trúc CI khi chưa có số đo (Lát 5 chỉ đo + D-NNN), đổi ruleset sống.
- Nhánh: phiên một nhánh → lát tuần tự, mỗi lát một PR ≤ 150 dòng mã (tài liệu audit nhập ở PR riêng).
- Rủi ro: siết `same_command` làm evidence cũ ở vòng đang chạy của dự án đích thành `verify` (chỉ chặt hơn — chạy lại đúng
  Gate là đủ); sửa guard chặn oan (đỡ: bộ test chặn-nhầm + `autonomy-bench` + fuzz); bộ phân loại Auto chặn sửa
  `.claude/hooks/guard.py` như lần T-1814 → `loop defer`, không thử đường khác (LOOP-STOP-025).

## Ngân sách (4 con số)
- Số vòng tối đa: `max(40, 8 × task)` (`loop init --single-session` tính)
- Chi phí: 0 đồng ngoài phiên
- Timeout mỗi lệnh Gate: 1800 giây (`XT_RECORD_TIMEOUT` mặc định)
- Ngày hết hạn: 24 giờ sau `loop init` (`--hours 24`)

## Điểm dừng bắt buộc (`loop defer`; `loop block` khi mọi việc còn lại phụ thuộc)
- Sửa `.claude/hooks/guard.py` bị bộ phân loại chặn → `loop defer` kèm bản vá đề xuất
- Đổi ruleset sống, secret, quyền repo: chủ repo

## Task

### Lát 1 — Bằng chứng Gate
- [x] `T-2101` `same_command` so dạng chuẩn `canonical_command` (nháy, toán tử, heredoc, NBSP có nghĩa; chỉ space/tab ngoài nháy tự do) thay token identity; test đỏ trước/xanh sau cho 8 cặp của AUD-CODE-014, `loop record` không tick Gate khác nháy, `loop verify --all` chạy cả hai Gate chỉ khác nháy; 5 ca `autonomy-bench` (files: scripts/xt.py, tests/test_xt_core.py, tests/test_xt.py, tests/fixtures/autonomy/harness.json, CHANGELOG.md, framework/11-autonomous-loop/harness-files.md) — Gate: `python3 -m unittest tests.test_xt_core -k command_identity -k audit_code_014 -k same_command && python3 scripts/xt.py autonomy-bench`

### Lát 2 — Cổng nhất quán
- [x] `T-2111` `dev-task.sh`: lệnh test (`test`, `test_fast`, `test_floor`, `test_unit` của `test-shard`) exit 0 mà output có dòng `Ran 0 tests` → exit 5, cùng chữ ký với `zero_tests_red` của `xt.py` (cổng commit, `gate`, `gate-par`, shard, CI mẫu); test `DevTaskZeroTestsTest` (AUD-XFEAT-013) (sau: T-2101; files: scripts/dev-task.sh, tests/test_hooks.py, CHANGELOG.md) — Gate: `python3 -m unittest tests.test_hooks -k zero_tests`
- [x] `T-2112` Sàn M/L chạy ở CI mẫu: `xt.py floor [--run] [--json]` liệt kê/chạy khoá sàn đã khai (`gate_floor_commands`, bỏ lệnh trùng `test`/`lint`) qua `run_gate_shell`; khoá sàn thiếu/no-op → exit 1; quy mô S → exit 0 "không áp"; CI mẫu job `gate` thêm bước `xt.py floor --run` sau `gate-par`; README §Công cụ (AUD-XFEAT-020) (sau: T-2111; files: scripts/xt.py, tests/test_xt_core.py, framework/templates/ci.yml, tests/test_ci_template.py, README.md, CHANGELOG.md) — Gate: `python3 -m unittest tests.test_xt_core -k gate_floor_cli && python3 -m unittest tests.test_ci_template`

### Lát 3 — Guard và reviewer
- [ ] `T-2121` Guard: bỏ token chuyển hướng (`2>&1`, `>/dev/null`, `&>f`, `< f`) trước luật git/gh (`_drop_redirects` ở `command_rules`, một chỗ): `git push origin 2>&1` trên `main` → như `git push origin`; `gh pr merge N --squash --match-head-commit <sha> 2>&1` → như không chuyển hướng; ca `autonomy-bench` (AUD-SEC-102, thay T-1814) (files: .claude/hooks/guard.py, tests/test_hooks.py, tests/fixtures/autonomy/guard.json, CHANGELOG.md) — Gate: `python3 -m unittest tests.test_hooks -k redirect && python3 scripts/xt.py autonomy-bench`
- [ ] `T-2122` `pr-review.yml`: diff vượt trần byte → không gọi reviewer, ghi `pr reviewed --inconclusive` (đủ diff thì như cũ); test tĩnh trong `tests/test_ci.py` (AUD-CI-016) (files: .github/workflows/pr-review.yml, tests/test_ci.py, CHANGELOG.md) — Gate: `python3 -m unittest tests.test_ci -k pr_review`

### Lát 4 — Installer
- [ ] `T-2131` `install.py --with-github`: đích không phải gốc repo git (`git rev-parse --show-toplevel` khác đích) → không ghi `.github/`, in đường gốc và cách làm, exit 2; không phải repo git → như cũ (AUD-CI-012) (files: scripts/install.py, tests/test_install.py, CHANGELOG.md) — Gate: `python3 -m unittest tests.test_install -k with_github_subdir`
- [ ] `T-2132` `install.py`: không ghi xuyên symlink trong `.xtemplates/` (`VERSION`, `README.md`, `scripts/*`) và `.gitignore` — symlink → thay bằng file thật trong `.xtemplates/` (bản chỉ đọc của khung), `.gitignore` symlink → bỏ qua có log (AUD-CFG-003) (sau: T-2131; files: scripts/install.py, tests/test_install.py, CHANGELOG.md) — Gate: `python3 -m unittest tests.test_install -k symlink`

### Lát 5 — Đo CI repo khung
- [ ] `T-2141` Số đo CI repo khung từ API (wall time, runner-phút, job sau matrix, đường dài nhất) cho 10 run `main` gần nhất; so với phương án 3 job của kế hoạch tối ưu theo đúng tiêu chí nhận ở đó; ghi `docs/ops/CI-TIMING-2026-10-21.md` + D-NNN giữ/đổi (đổi kiến trúc → ADR riêng, PLAN sau) (files: docs/ops/CI-TIMING-2026-10-21.md, docs/autopilot/DECISIONS.md) — Gate: `test -f docs/ops/CI-TIMING-2026-10-21.md && grep -q "runner" docs/ops/CI-TIMING-2026-10-21.md`
- [ ] `T-2142` Sổ audit: phát hiện đã sửa ghi `đã sửa` kèm PR; `audit check` xanh; PROGRESS bàn giao (sau: T-2101, T-2111, T-2112, T-2121, T-2122, T-2131, T-2132, T-2141; files: docs/ops/AUDIT-STATUS.md, PROGRESS.md) — Gate: `python3 scripts/xt.py audit check docs/ops/AUDIT-STATUS.md`

## Ước lượng (giờ phiên agent)
| Lát | P50 | P90 |
|---|---|---|
| 1 | 0,5 | 1 |
| 2 | 1,5 | 3 |
| 3 | 1 | 2 |
| 4 | 1 | 2 |
| 5 | 0,5 | 1 |
