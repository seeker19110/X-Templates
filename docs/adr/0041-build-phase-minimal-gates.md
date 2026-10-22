# ADR-0041: Pha `build` — test tối thiểu, CI là cổng; sàn M/L và thiết kế đầy đủ dời sang `harden`

- **Trạng thái:** Đã chấp nhận (chủ repo 2026-10-22: "pha dev code ít nhất, nhanh nhất, test tối thiểu, CI xanh là được
  merge; pha production mới audit, tấn công tìm lỗ hổng, tối ưu hiệu năng")
- **Trạng thái triển khai:** Đã triển khai — `scripts/xt.py` `gate_floor_keys` (pha build → không áp sàn), `cmd_floor` in lý
  do; skill `.claude/skills/autopilot/SKILL.md` Pha 1 + bước 6; `framework/11-autonomous-loop/README.md` bước 12; test
  `tests/test_xt_core.py::GateFloorCliTest::test_gate_floor_cli_build_phase_not_applied`.
- **Ngày:** 2026-10-22
- **Làm rõ:** ADR-0031/0033/0037 (pha build/harden, tối giản pha build, reviewer chỉ ở harden), ADR-0040 (quyền cục bộ ở
  pha build), `LOOP-HARNESS-023` (sàn Gate M/L), ADR-0039 (CI mẫu chạy `floor --run`).

## Bối cảnh

Sau ADR-0031/0033/0037, pha build đã bỏ reviewer và audit theo mốc. Còn ba chỗ làm chậm mà không đổi được merge:

1. **Sàn Gate M/L** (`format_check`, `coverage`, kiểm kiểu, `e2e` — `LOOP-HARNESS-023`) chạy ở CI mẫu (`floor --run`), ở
   `loop verify` và được `doctor`/`loop init` đòi — tức đòi coverage có ngưỡng ngay từ lát đầu.
2. **Cổng đầy đủ cục bộ trước khi đẩy** (`dev-task.sh gate`) chạy lại đúng lệnh CI sẽ chạy.
3. **Trần 150 dòng mỗi PR** — lý do của nó là làn review (ADR-0024), mà pha build không review.
4. **Thiết kế đầy đủ ở G4** (C4, `API-CONTRACT.md`, `THREAT-MODEL.md` từ quy mô M) trước dòng code đầu tiên.

## Quyết định

1. Pha `build` (`delivery_phase` ở cây làm việc): sàn Gate M/L **không áp** — `gate_floor_keys` trả rỗng nên `floor`
   (CI mẫu), `loop verify`, `doctor`, `loop init` đều không đòi. Cổng còn lại: `gate` của dự án (lint/typecheck/test do dự án
   khai) và CI xanh. Đặt `harden` → sàn trở lại ngay; `release-check` đã đòi `harden` (ADR-0031) nên không phát hành được
   khi chưa qua sàn.
2. Skill `/autopilot`: pha build bỏ `dev-task.sh gate` trước khi đẩy (cổng commit `gate-fast` vẫn chạy; CI là cổng), bỏ
   trần 150 dòng; thiết kế chỉ phần code cần (schema, hợp đồng API khi có), C4/threat model đầy đủ ở harden.
3. Không đổi: CI mẫu (`floor --run` tự không áp ở build), ruleset, guard; merge vẫn cần CI xanh + không xung đột (ADR-0036).

## Lý do

- Quyết định của chủ repo; tiêu chí cuối giữ nguyên, chỉ dời **thời điểm** kiểm (như ADR-0029/0031): `release-check` chặn
  phát hành tới khi `harden` + sàn + audit + review sạch.
- Một chỗ chặn (`gate_floor_keys`) cho mọi lối dùng sàn — không rẽ nhánh ở từng lệnh.

## Phương án đã cân nhắc

- **Gỡ bước `floor` khỏi CI mẫu** và thêm lại ở harden: buộc dự án đích gộp tay `ci.yml` hai lần. Loại.
- **Giữ sàn, chỉ hạ ngưỡng coverage ở build**: là nới cổng (`LOOP-CI-001`). Loại.

## Hệ quả

- Lát đầu của dự án M/L không bị đỏ vì thiếu `format_check`/`coverage`; nợ dồn về harden (audit delta + sàn + reviewer).
- PR pha build lớn hơn và CI có thể đỏ nhiều hơn vì bỏ gate cục bộ — chấp nhận để đổi lấy tốc độ.

## Đường lùi

Đặt `delivery_phase: harden`. Revert gỡ hẳn.
