# PLAN-harden-2026-11-01.md — Khung X-Templates · /complete trước 3.30.0 (D-299, D-300)

> Lập ngày 2026-11-01 ở đầu `/complete`. Duyệt: D-300 (phiên chính tự duyệt). Pha `harden`; review 1 lần theo ADR-0062.
> Nguồn việc: `release-check` NO-GO (`audit --strict` 100 lỗi: 18 🔴 + 28 🟠 + 54 🟢 nợ review; `review_debt` 5 file; `verify`)
> và audit delta `d3e3e77..HEAD` (`docs/ops/AUDIT-REPORT-2026-11-01-complete.md`). Hướng sửa họ lách guard: ADR-0063 (D-299).
>
> **Cú pháp bắt buộc cho máy:** mỗi task một dòng `- [ ] \`T-NNNN\` <việc> — Gate: \`<lệnh>\``. `topo:` theo ADR-0061.

## Tóm tắt (cổng duyệt)
- Hiện trạng: `main` `7b55ead` (#393). Guard: 34/41 mẫu tái hiện của sổ còn lọt (đo bằng `bash_decision` 2026-11-01).
- Phạm vi: lát A–D guard theo ADR-0063 (tập con chuẩn: từ vựng/mở rộng · mã động · đăng review · container/sổ giai đoạn/hiệu
  năng) · lát E `xt.py` (scanner prompt-assets, `next-step`, `pr debt`) · lát F sổ: 🟢 nợ review rẻ thì sửa, còn lại
  `chấp nhận` có chủ + hạn · lát G: `loop verify --all`, `release-check`, GO-NO-GO (người ký).
- Không làm: 🟢 `mở` không phải nợ review (giữ nguyên); đổi luật review/merge.
- Cách làm: mỗi lát một PR, test đỏ trước (mẫu tái hiện của sổ), lát guard `(topo: review)` → một review tập trung trước
  merge; đo chặn oan trên kho 1567 lệnh Bash thật trước mỗi PR guard (chỉ chấp nhận đổi quyết định khi lệnh đó sai thật).

## Ngân sách (4 con số)
- Số vòng tối đa: bỏ trống (`--single-session`) · Chi phí: 0 đồng ngoài phiên · Timeout Gate: 1200 giây · Hạn: 48 giờ sau `loop init`

## Task
### Lát A — guard: tập con từ vựng + mở rộng
- [ ] `T-3630` ADR-0063 lớp từ vựng/mở rộng: AUD-SEC-196, 202, 214, 229–234, 238, 240, 242, 243, 245, 246, 249 (+181/231 phần backtick) (topo: review; files: .claude/hooks/guard.py, tests/test_guard_strict.py, tests/, tests/fixtures/autonomy/) — Gate: `python3 -m unittest -q tests.test_guard_strict && python3 scripts/xt.py autonomy-bench`
### Lát B — guard: mã động
- [ ] `T-3631` `bash -c`/`eval` thân động, lệnh `"$@"`, ống/`>(…)` vào shell, sed `e`/`s///e` mọi dấu phân cách, awk `system(`/ống, `-f -`, gọi lệnh dạng danh sách của Perl/Ruby/PHP, ghi `BASH_ENV`/biến prompt qua `printf -v`/`mapfile`: AUD-SEC-235, 237, 252, 287, 288, 290–292 + 🟠 mới của audit delta (sau: T-3630; topo: review; files: .claude/hooks/guard.py, tests/test_guard_strict.py, tests/fixtures/autonomy/) — Gate: `python3 -m unittest -q tests.test_guard_strict && python3 scripts/xt.py autonomy-bench`
### Lát C — guard: đăng dấu review
- [ ] `T-3632` Lệnh `gh` đăng nội dung chỉ nhận thân chữ nguyên văn/file chữ; thân mang `xt-review` → chặn: AUD-SEC-180, 186, 191, 192, 193, 244, 253 (sau: T-3631; topo: review; files: .claude/hooks/guard.py, tests/test_guard_strict.py, tests/fixtures/autonomy/) — Gate: `python3 -m unittest -q tests.test_guard_strict && python3 scripts/xt.py autonomy-bench`
### Lát D — guard: container, sổ giai đoạn, hiệu năng
- [ ] `T-3633` AUD-SEC-247 (`_container_asks` không hạ deny thành ask), AUD-SEC-248 (ghi đè `STAGE.json` mức thư mục), 🟠 PERF mới (đánh giá vị từ stdin một lần mỗi khâu) (sau: T-3632; topo: review; files: .claude/hooks/guard.py, tests/test_guard_strict.py, tests/fixtures/autonomy/) — Gate: `python3 -m unittest -q tests.test_guard_strict && python3 scripts/xt.py autonomy-bench`
### Lát E — xt.py
- [ ] `T-3634` AUD-SEC-259–263, 276 (scanner prompt-assets), AUD-HAR-169 (`next-step --package`), AUD-HAR-182 (`pr debt --fixed`), AUD-CI-024 (Kiểm `BASE-REPO-005`) (sau: T-3633; topo: review; files: scripts/xt.py, tests/test_xt_cli.py, tests/test_merge.py, tests/test_next_step.py, BLUEPRINT.md) — Gate: `python3 -m unittest -q tests.test_xt_cli tests.test_merge tests.test_next_step && python3 -m mypy --strict scripts/xt.py`
### Lát F — sổ
- [ ] `T-3635` AUD-DOC-159; 🟢 nợ review: sửa nhóm tài liệu rẻ, còn lại `chấp nhận` (chủ + hạn, lý do từng dòng); 🔴/🟠 lát A–E `đã sửa` (sau: T-3634; files: docs/, CHANGELOG.md) — Gate: `python3 scripts/xt.py audit check docs/ops/AUDIT-STATUS.md --strict`
### Lát G — phát hành
- [ ] `T-3636` `loop verify --all` xanh, `release-check` chỉ còn hàng chờ người (`prod_switch`, chữ ký GO-NO-GO) (sau: T-3635; topo: audit) — Gate: `python3 scripts/xt.py audit check docs/ops/AUDIT-STATUS.md --strict && python3 scripts/xt.py blueprint-status BLUEPRINT.md --strict`
