# ADR-0047: Pha build không chờ người — mẫu dự án đích `merge_hard_exceptions: auto`; `/autopilot` lặp đợt build → audit → đợt kế tới khi hết việc, rồi đề xuất `/complete`

- **Trạng thái:** Đã chấp nhận (chủ repo yêu cầu 2026-10-25: "bật `merge_hard_exceptions: auto` cho dự án đích luôn";
  "`/autopilot` … tự quyết định tất cả … tự động merge và tiếp tục → xong hết mọi việc thì audit → lại tiếp tục vòng lặp build
  cho đến khi hoàn thiện"; "đến khi audit không còn lỗi mới đề xuất chuyển qua `/complete`"; "Release tag không tự động được à"
  — D-176, D-177, D-178, D-179; phiên chính tự duyệt thiết kế theo tiêu chí chất lượng cuối, ADR-0008)
- **Trạng thái triển khai:** Đã triển khai (PR #262, bản 3.24.0) — `framework/templates/xt.yaml` (`auto`); skill
  `.claude/skills/autopilot/SKILL.md` mục Kết thúc; `scripts/xt.py` `_live_loop` (vòng `done`/`done-pending-human` đã kiểm lại cuối trên cây
  hiện tại không chặn `loop init`), `_carry_previous` (PLAN khác vẫn mang việc chờ người còn mở cùng ID), chuỗi lý do `milestone_audit: g7`;
  `.github/workflows/release-tag.yml` (trigger `push` theo `VERSION`); test `tests/test_xt_cli.py::LoopCommandsTest::
  test_init_after_done_starts_next_batch`, `tests/test_xt_loop.py::LoopInitCarryTest::test_loop_init_carry_keeps_deferred_across_plans`;
  tài liệu README mảng 11 bước 16, `lifecycle.md`, `audit.md` §1, mẫu PLAN, README gốc, RUNBOOK-PR-STEWARD §4.
- **Ngày:** 2026-10-25
- **Thay một phần:** ADR-0020 (mẫu dự án đích `human` → `auto`; luật `auto`/`human` và "PR đổi khoá luôn người merge" giữ),
  ADR-0046 mục 1 ("dừng ở build xong" → vòng đợt) và mục 5 (sàn: `merge_hard_exceptions` không còn trong sàn mẫu).

## Bối cảnh

ADR-0046 cho `/autopilot` dừng ở "build xong" và để `/complete` lo harden. Chủ repo muốn pha build **không chờ người ở bất
cứ đâu** và **không dừng**: xong đợt thì audit, sửa, build tiếp tới khi hoàn thiện; chỉ khi audit không còn lỗi mới
*đề xuất* `/complete`; tag phát hành không cần bấm tay. Rào cản còn lại đo tại `d4c2dca`: (1) mẫu dự án đích
`merge_hard_exceptions: human` — PR chạm auth/tiền/PII chờ người merge (ADR-0016/0020); (2) skill bảo "`done` → `loop init`
đợt kế" nhưng máy coi vòng `done` còn `active` là vòng sống → `loop init` exit 2 `LOOP-HARNESS-024` cho tới khi Stop hook
chạy (review #262 🔴); (3) `loop init` với PLAN khác bỏ hết việc `loop defer` — mỗi đợt một PLAN nên việc chờ người mất
dấu (🟠); (4) "hết việc" chưa định nghĩa (🟠); (5) `release-tag.yml` chỉ `workflow_dispatch`, phiên agent bị bộ phân loại
chặn gọi REST.

## Phương án đã xét

1. **Bỏ guard/deny để "chấp nhận tất cả các lệnh"** — Loại: guard chỉ chặn không đảo ngược, lộ bí mật, tắt hook, ghi tay
   `.autopilot/`, merge chưa đủ điều kiện (ADR-0018); không phải rào cản tốc độ, bỏ là mất đường lùi (tiêu chí 2).
2. **Giữ máy, chỉ sửa chữ skill: "đợt xong → `loop stop` rồi `loop init`"** — rẻ, nhưng thêm một bước người/agent dễ quên và
   `loop stop` ghi `final_verdict` thừa; việc chờ người vẫn mất khi đổi PLAN.
3. **(Chọn) Mẫu `auto` + vòng build→audit→đợt kế ở skill + máy đỡ đúng ba chỗ** (`_live_loop` coi `done` là hết vòng;
   `_carry_previous` mang việc chờ người cùng ID sang PLAN khác, báo việc bị bỏ; tag tự khi `VERSION` đổi). Định nghĩa "hết việc"
   = PLAN hết task + 0 MUST mở ngoài việc chờ người + audit 0 🔴/🟠.
4. **`/autopilot` tự chạy `/complete` khi hết việc** — Loại theo chủ repo (D-178): phát hành là quyết định của người.

## Quyết định

1. Mẫu `framework/templates/xt.yaml`: `merge_hard_exceptions: auto`. Dự án đã cài giữ giá trị cũ (copy-if-absent); thiếu khoá
   = `human`; PR đổi khoá luôn người merge; `UNWAIVABLE`, guard, review sạch ở harden (ADR-0037) không đổi. **Rủi ro chủ repo
   nhận**: dự án có người dùng thật ở pha build merge PR chạm auth/tiền/PII không có người xem — muốn giữ chốt thì đặt `human`.
2. `/autopilot` không dừng ở `done`: `/audit delta` (lần đầu `full`; 🔴/🟠 → task) + MUST mở → `PLAN-<đợt>.md` kế → `loop init`
   → lặp. **Hết việc** = PLAN hết task, 0 MUST mở ngoài việc chờ người, 0 🔴/🟠 → `/audit full`; sạch → **đề xuất** `/complete`, dừng.
3. Máy: `loop init` coi vòng `done`/`done-pending-human` **đã `loop verify --all` trên cây hiện tại** như hết ngân sách (không
   chặn, không cần `--force`; vân tay cây gồm cả file chưa track nên thứ tự là: viết PLAN đợt kế + sổ audit → `loop verify --all`
   → `loop init`; cây đổi sau verify → exit 2 bảo verify lại, không gợi `resume`/`--force` — review #262 lượt 2–3); PLAN khác mang
   việc chờ người còn mở cùng ID, báo `⚠` việc không còn mở (chép task cùng ID rồi `loop defer` lại). Bằng chứng xanh vẫn chỉ
   mang khi cùng PLAN + blueprint.
4. `release-tag.yml` thêm `on: push: branches: [main], paths: [VERSION]`; kiểm SemVer/CHANGELOG/tag trùng giữ; `workflow_dispatch`
   là đường lùi. Lần đầu sau 3.24.0 run tự động có thể đỏ (commit đổi file workflow, thiếu `XT_RELEASE_TOKEN`, AUD-CI-014) → tag tay.

## Hệ quả

- Dự án đích chạy lại `install.py` (skill + `xt.py`); hook/guard/điểm dừng không đổi. `release-check` vẫn FAIL `phase`/
  `review_debt` ở build — G7 chỉ qua `/complete`.
- Chỉ số theo dõi: tỉ lệ PR ngoại lệ cứng merge ở build phải revert (`pr stats`), số đợt tới khi audit sạch.

## Đường lùi

Mẫu đặt lại `human`; skill mục Kết thúc về "dừng ở build xong" (ADR-0046); `_live_loop` bỏ hai verdict `done`; xoá khối `push`
trong `release-tag.yml`. Mỗi bước là một commit đảo ngược được.

## Xác nhận

`tests/test_xt_cli.py` (`test_init_after_done_starts_next_batch`), `tests/test_xt_loop.py` (`…_across_plans`),
`tests/test_docs_budget.py` (trần byte skill/README 11); review #262 (ghi `pr reviewed`, lượt cuối sạch ở head merge); tag `v3.24.0` tạo bởi run tự động hoặc tay.
