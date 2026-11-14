# AUDIT-REPORT — X-Templates · 2026-11-14 (delta DOC)

> Snapshot `2bf2e1cfdd5f99bc5568f7036a5061c134316061` trên `main`. Tiếp phần DOC còn trống của
> [audit 2026-11-11](AUDIT-REPORT-2026-11-11-delta.md) trên phạm vi `454d146..2bf2e1cf`.
> Phát hiện mới: **1 🟢 mở** (`AUD-DOC-293`). Giữ `AUD-DOC-291` mở. TEST và HAR chưa quét đủ phạm vi.

## 1. Phạm vi

`xt.py audit plan --json` ở `2bf2e1cf` nhận diện repo khung có 672 file, 446 file Markdown,
92 file test và 12 workflow. Lượt này rà tài liệu thay đổi trong repo và đối chiếu phần hướng dẫn đang áp dụng với mã:

- `454d146..7ca87a6`: 108 tệp Markdown, gồm 43 tệp dời nguyên văn, 17 tệp dời kèm sửa liên kết và 48 tệp thêm hoặc sửa.
  Rà README, hướng dẫn phát hành, vòng đời, gói và hợp đồng registry.
- `7ca87a6..2bf2e1cf`: 40 tệp Markdown qua 35 commit, gồm 16 thêm, 19 sửa và 5 dời. Rà thay đổi hướng dẫn,
  liên kết lưu kho, ADR-0075–0077, PLAN và bảy SPEC factory. Hợp đồng receipt đã chốt ở T-3841;
  mã triển khai còn ở T-3842–T-3844 và T-3860.
- Cả khoảng `454d146..2bf2e1cf`: 132 tệp Markdown thay đổi theo diff hai đầu. Chưa biết tình trạng URL ngoài
  và các dữ kiện ở nguồn ngoài tại ngày quét. Các nguồn nghiên cứu có ngày được đọc theo mốc của chúng.

## 2. Kiểm chứng

| Snapshot | Lệnh | Exit | Kết quả |
|---|---|---:|---|
| `7ca87a6` và `2bf2e1cf` | `python3 scripts/check-links.py` | 0 | Liên kết và anchor nội bộ đạt |
| Cả hai snapshot | `python3 scripts/xt.py checks` | 0 | 5/5 mục, gồm tiến độ và CHANGELOG |
| `7ca87a6` | `python3 -m unittest tests.test_docs_budget tests.test_plan_files tests.test_check_links` | 0 | 49 test |
| `2bf2e1cf` | `python3 -m unittest tests.test_docs_budget tests.test_plan_files tests.test_content_facts tests.test_check_links tests.test_stage_agent_approval tests.test_registry` | 0 | 111 test |
| `2bf2e1cf` | `python3 scripts/xt.py plan waves --plan <PLAN đã lưu kho> --json` | 0 | Factory A, Factory B–E và App 3.14 đều có `waves: []`, `blocked: []` |
| `454d146..2bf2e1cf` | `git diff --check 454d146 2bf2e1cf -- '*.md'` | 0 | Diff không có lỗi khoảng trắng |
| Sổ sau lượt ghi | `python3 scripts/xt.py audit check docs/ops/AUDIT-STATUS.md` | 0 | 11 nhóm đã quét, 2 nhóm chưa quét |

## 3. Phát hiện và theo dõi

- **AUD-DOC-293 🟢**, mở. Hướng dẫn G7 và nghiệm thu MVP chỉ nêu người ký hoặc duyệt ở nhiều chỗ trong
  [README](../../README.md), [vòng đời](../../framework/00-method/lifecycle.md),
  [giao thức vòng lặp](../../framework/11-autonomous-loop/README.md) và [mẫu GO-NO-GO](../../framework/templates/GO-NO-GO.md).
  Mã CLI và [ADR-0069](../adr/0069-agent-stage-approval.md), [ADR-0074](../adr/0074-agent-release-signoff.md)
  có đường opt-in. D-481 chọn dẫn về ADR và giữ điều kiện máy. Gate sửa gồm kiểm liên kết sau cài vào dự án sạch.
  Chủ xử lý: người duy trì tài liệu khung trong đợt harden hiện tại.
- **AUD-DOC-291 🟢**, mở từ #510. [README gói](../../framework/templates/packs/web-api-ts/README.md) vẫn khai ngày
  2026-11-06 và dùng Kysely 0.29.6 khi mô tả giới hạn migration. Starter ở #513 ghim Kysely 0.29.8.
  Phiên bản ở đầu README ghi rõ là dữ kiện của dự án nguồn. Chủ xử lý: người duy trì gói `web-api-ts`.

Điều kiện phát hành vẫn theo `release-check`, gồm sổ audit `--strict`.

## 4. Bằng chứng HAR trên `2bf2e1cf`

- Rà 17 tệp quy trình, skill, installer và cấu hình trong `454d146..2bf2e1cf`. `python3 -m unittest -q tests.test_install tests.test_adapters tests.test_doctor tests.test_stage_agent_approval.StageAgentApprovalCliTest tests.test_release_contract.ReleaseBlockedLoopTest tests.test_release_contract.ReleaseVerifyWorktreeTest` exit 0, 256 ca (bỏ qua một ca OpenCode vì thiếu Bun).
- `doctor --json` trên clone sạch exit 0, cảnh báo sandbox. Cây chính có vòng một phiên exit 1 vì thiếu sandbox (LOOP-HARNESS-022). Giữ HAR chưa quét: chưa rà hết delta parser guard và chưa kiểm host hook, sandbox OS trên môi trường thật.

## 5. Bằng chứng TEST trên `2bf2e1cf`

- CI #532 có cùng cây Git với commit squash. [Coverage](https://github.com/seeker19110/X-Templates/actions/runs/43552760543/job/132320108268) đạt 100% trên 23.949 câu lệnh và 8.692 nhánh. CI Python 3.14, 3.11, app E2E và quality đều xanh.
- `python3 -m unittest -q tests.test_ci tests.test_report_fixtures tests.test_registry tests.test_perf_trial tests.test_docs_budget tests.test_check_links tests.test_plan_factory_order tests.test_spec_factory_facts tests.test_stage_agent_approval` exit 0, 288 ca; `python3 -m unittest -q tests.test_ci_shard tests.test_hooks.DevTaskTest` exit 0, 41 ca.
- Diff `454d146..2bf2e1cf` có 44 tệp `tests/` thay đổi. Diff AST của `test_hooks.py` có 153 test thêm, 6 sửa, 0 xoá; corpus guard thêm 824 ca. Giữ TEST chưa quét vì chưa đối chiếu hành vi dự kiến của từng ca đã đổi.
- **AUD-TEST-105 🟢**, mở. Với đồng hồ giả, tỷ lệ thử lại ở `tests/cpu_budget.py` xanh khi cả hai cặp đều đỏ: 0,20 s và 3,00 s vượt ngưỡng 2,50 s, 0,09 s và 1,44 s vượt 1,40 s. Hàm ghép số nhỏ lớn nhất với số lớn bé nhất của hai lần đo. Giữ các ngưỡng hiện có và kiểm từng cặp riêng. Chủ xử lý: người duy trì cổng kiểm thử.
