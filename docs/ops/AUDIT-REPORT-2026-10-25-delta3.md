# AUDIT-REPORT — X-Templates · 2026-10-25 (delta `00ead5f..daefc7c`)

> Commit quét: `main` `daefc7c` (3.25.0) · Phạm vi: delta `00ead5f..daefc7c` (#261 sổ audit, #262 ADR-0047 / 3.24.0, #263 ADR-0048 /
> 3.25.0; D-176…D-183) — nhóm 1 ARCH, 2 SEC, 3 CODE, 4 TEST, 8 CI, 9 DOC, 11 CFG, 12 XFEAT, 13 HAR · Lý do: `release-check` NO-GO hàng
> `review_debt` (10 file ngoài tài liệu đổi sau SHA quét `00ead5f`: `release-tag.yml`, `VERSION`, mẫu `xt.yaml`, `scripts/xt.py`, 6 file
> test) · Người quét: reviewer năng lực cao nhất (`reviewer-alt`, effort max) rà **cả PR ở head** mỗi lượt — #262 năm lượt, #263 bốn
> lượt (ADR-0044, `LOOP-ORCH-005`); phiên chính chạy công cụ máy · Xác minh đối kháng: mọi 🔴/🟠 có đường tái hiện của reviewer và
> được sửa trong chính PR kèm test (đột biến bị bắt), CI xanh ở head; **không có reviewer thứ hai** tái hiện độc lập (`audit.md` §5
> bước 4) — bù bằng test/đột biến · `xt.py audit check docs/ops/AUDIT-STATUS.md` → exit 0

## 1. Tóm tắt

| Mức | Mở | Đã sửa | Chấp nhận | Bác bỏ |
|---|---|---|---|---|
| 🔴 | 0 | 2 | 0 | 0 |
| 🟠 | 0 | 13 | 0 | 0 |
| 🟢 | 3 | 29 | 0 | 0 |

Số đếm lấy từ báo cáo review (sổ `reviews.json` chỉ lưu head/verdict). Bốn ghi chú review không sửa: hai **có sẵn
trước PR** thành hàng 🟢 mở (AUD-HAR-114 ← #262 lượt 2 🟢9; AUD-DOC-086 ← 🟢10); hai **không tính là phát hiện** (#262 lượt 4 F-3:
`budget` không đòi kiểm cuối là thiết kế — skill coi `budget` = dừng, không khai xong; #263 lượt 4 🟢3: nghi ngờ, không có quy ước). Mọi 🔴/🟠 phát hiện trong review được sửa **trước khi merge** (không vào sổ dạng mở): #262 — 🔴 lượt 1 (`_live_loop` coi vòng `done`
là vòng sống), 4 🟠 lượt 2 (verify cuối, ID chờ người dùng lại, chữ `LOOP-STOP-005`/`LOOP-HARNESS-024`), 1 🟠 lượt 3 (thứ tự PLAN
đợt kế → `verify --all` → `init`), 1 🟠 lượt 4 (test nhánh `budget` không chạm `final_check`); #263 — 🔴 lượt 1 (trần 4 MUST@M,
ADR-0004 → D-181), 2 🟠 lượt 1, 3 🟠 lượt 2, 2 🟠 lượt 3. Một 🟢 mới còn mở: AUD-HAR-113 (BLUEPRINT.md chưa ghép lại sau 3.25.0).

## 2. Phạm vi và tín hiệu

Delta mã (`git diff --stat 00ead5f daefc7c -- . ':!*.md'`): `scripts/xt.py` +69/−10 (`_live_loop` theo `final_check`, `_deferred_to_keep`
so `task_req_rev`, thông báo exit 2 riêng cho đợt đã xong, `DOCTOR_SKILLS` thêm `optimize`), test +115/−3 (`LoopInitCarryTest` 4 ca mới
có git, `test_init_after_done_starts_next_batch` mở rộng, doctor/install skill `optimize`), `release-tag.yml` thêm trigger `push`
`paths: [VERSION]`, mẫu `xt.yaml` `merge_hard_exceptions: auto`; skill `/optimize` mới, `/autopilot` và `/complete` đổi; tài liệu khung
(`optimization-loop.md` `LOOP-OPT-016`, mức 004/005; `stop-points-and-escalation.md`; mẫu GO-NO-GO dòng 20 + §2c; `lifecycle.md`;
ADR-0047/0048). PERF/A11Y/DEP/DATA không bị chạm (giữ kết quả cũ).

## 3. Lệnh đã chạy

| Nhóm | Lệnh | Exit | Kết quả |
|---|---|---|---|
| mọi nhóm | `scripts/dev-task.sh gate` trước mỗi lần đẩy (#262: 4 lần; #263: 5 lần) | 0 | coverage dòng + nhánh 100 %, `mypy --strict`, ruff C901 ≤ 10 |
| CODE/TEST | reviewer: đột biến `_live_loop` (M1–M6: bỏ `final_check` cho `done`/`done-pending-human`, `budget` đòi kiểm cuối, không so spec) và `DOCTOR_SKILLS` | — | mọi đột biến bị test bắt sau lượt sửa cuối |
| CI/SEC | `zizmor 1.31.1 --offline .github/workflows/` | 13 | 14 medium, đều `artipacked` (AUD-CI-007, như lần trước); trigger `push` mới không thêm phát hiện |
| CI/SEC | reviewer #262 lượt 2: `release-tag.yml` — `branches: [main]` + `paths: [VERSION]`, `if: github.ref == 'refs/heads/main'`, quyền tối thiểu, action ghim SHA, không `pull_request(_target)`, `inputs.sha` qua env, SemVer kiểm trước khi ghép tag, tag trùng → exit 1 | — | không phát hiện; run đầu thật (`v3.24.0`, `v3.25.0`) xanh |
| SEC/CFG | regex khoá/bí mật trên dòng `+` của diff; `git log --format=%B 00ead5f..daefc7c` theo `AI_ATTRIBUTION_RE` | 0 | 0 bí mật; 0 tên model/URL phiên |
| DOC/HAR | `xt.py validate`, `check-links.py`, `test_docs_budget`, `progress-check` | 0 | skill `/optimize` 6 106/6 144 B; thư mục `11-autonomous-loop` 232 297/232 307 B |
| CFG | mẫu `xt.yaml` `merge_hard_exceptions: auto`: thiếu khoá → `human` (`merge_hard_mode`, fail-closed); gitleaks CI success ở `daefc7c` | 0 | rủi ro chủ repo chấp nhận (D-176, ADR-0047 §Hệ quả) |
| HAR | `xt.py doctor`; `loop verify --all` sau tag `v3.25.0` | 0 | 0 lỗi; 6 Gate + 11 lệnh kiểm blueprint xanh |

## 4. Phát hiện mở

- **AUD-HAR-113** 🟢: `BLUEPRINT.md` (sinh ở #257, khung 3.22.x) chưa ghép lại sau 3.24.0/3.25.0 — thiếu `LOOP-OPT-016`, chữ cũ của
  `LOOP-OPT-002`/`011`, `LOOP-STOP-005`, `LOOP-HARNESS-024`. Đo được: `grep -c LOOP-OPT-016 BLUEPRINT.md` = 0. Sửa: `compose` lại + tái
  kiểm bằng chứng như #257, ở lát riêng.
- **AUD-HAR-114** 🟢 (có sẵn trước PR): PLAN đợt trước bị đổi tên/xoá trước `loop init` đợt kế → `loop_verdict` = `blocked` ("không
  thấy PLAN") → exit 2 "Đang có vòng" dù đợt đã xong; lối ra là `loop stop`. Sửa: in verdict/lý do trong thông báo exit 2.
- **AUD-DOC-086** 🟢 (có sẵn trước PR): `RUNBOOK-PR-STEWARD.md` §4 không nói push `main` chứa ≥ 2 commit đổi `VERSION` (không squash)
  chỉ tag đầu push — đường lùi `workflow_dispatch --sha`; một dòng.

## 5. Ghi nhận về quy trình

- Worktree dưới `/tmp` làm `test_guard_audit1020b` đỏ oan (guard coi `$PWD/..` là thư mục tạm, ADR-0040) — đặt worktree ngoài `/tmp`.
- `pr-title` đỏ một lần do tiêu đề PR sửa tay dài 73 ký tự — chạy `xt.py pr title-check` trước mọi lần đổi tiêu đề.
- Hai 🟢 cuối của review (PROGRESS "lượt 2", dòng PLAN-3.25 còn nhắc `floor`) sửa cùng PR sổ này; chú thích test lượt 5 #262
  để PR mã kế (PR sổ không sửa mã — sửa file `tests/` sau SHA quét tự tạo nợ `review_debt`, review #264 🔴).
- Thân PR tạo qua tool MCP bị gắn footer có URL phiên (`LOOP-HARNESS-027`) — viết lại thân không footer ngay sau khi mở PR.
- Sau merge: `loop verify --all` rồi `release-check` — hàng `review_debt` phải PASS (bằng chứng ghi ở PROGRESS).
