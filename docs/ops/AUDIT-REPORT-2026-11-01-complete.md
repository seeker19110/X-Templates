# AUDIT-REPORT 2026-11-01 — đầu `/complete` (trước 3.30.0)

> Delta `d3e3e77..7b55ead` (#392 guard lượt 2, #393 PROGRESS) + `457a69e..7b55ead` cho `scripts/xt.py` (#390) — phần
> `release-check` báo `review_debt`. Chế độ: `/audit delta` gọi từ `/complete` → nhánh subagent (1 cụm `reviewer-alt` Opus
> effort max, 1 xác minh đối kháng `reviewer` Sonnet).

## 1. Tóm tắt

| Mức | Mới | Ghi chú |
|---|---|---|
| 🔴 | 0 | |
| 🟠 | 8 (AUD-SEC-294…301) | 4 trên đường mã #392 (SEC-294…297), 4 có từ trước (SEC-298…301); cả 8 tái hiện được bằng công cụ thật khi xác minh |
| 🟢 | 2 (AUD-PERF-010, AUD-SEC-302) | PERF-010 hạ từ 🟠: không tái hiện được "> 8 s ở 40 token", đo tuyến tính ~0,018 s/token |

Sổ trước audit: 18 🔴 + 28 🟠 mở (gần hết họ lách bộ phân tích bash của guard) + 54 🟢 nợ review. Hướng sửa: ADR-0063
(tập con chuẩn, D-299) — đo trên 1567 lệnh Bash thật của các phiên, lớp từ vựng/mở rộng đổi quyết định của 1 lệnh (chặn
đúng: backtick không thoát trong nháy kép). Kế hoạch: `docs/autopilot/PLAN-harden-2026-11-01.md` (D-300).

## 2. Phạm vi

`audit plan` @ `c8d7830` (cùng cây với `main` `7b55ead`): quét lại ARCH/SEC/CODE/TEST/XFEAT/HAR (guard + test + fixture),
DOC (CHANGELOG, PROGRESS, DECISIONS, PLAN-fix, sổ). CFG/DEP/CI/A11Y không đổi từ SHA quét. `doctor --fix`: 0 lỗi.

| Cụm | Kết luận | Chưa rà |
|---|---|---|
| guard + `xt.py` (SEC/CODE/TEST/PERF/ARCH/XFEAT/HAR) | xong | gawk `--source`/`-e` chỉ kiểm qua guard (máy có mawk 1.3.4); timeout hook 600 s không đo thật |
| DOC (phiên chính) | xong — 0 mới | |

## 3. Lệnh đã chạy (exit)

- `python3 -m unittest -q tests.test_guard_audit1019 tests.test_hooks` → 0 (411 test) · `python3 scripts/xt.py autonomy-bench` → 0 (guard 924/924)
- `python3 -m unittest -q tests.test_app_pr tests.test_merge tests.test_xt_cli` → 0 (424 test)
- Mỗi payload qua `guard.bash_decision` ở HEAD và base `d3e3e77`; công cụ thật (GNU sed 4.9, mawk 1.3.4, bash 5.2.21,
  perl/ruby/php) chạy tải vô hại `touch MARKn` trong thư mục scratch.

## 4. Chi tiết (tái hiện)

| ID | Tái hiện | Xác minh đối kháng |
|---|---|---|
| AUD-SEC-294 | `echo 'touch M' \| sed 'sx^xxe'` → guard cho chạy, sed chạy lệnh | tái hiện được |
| AUD-SEC-295 | `echo 'touch M' \| sed '/t/Ie'` | tái hiện được |
| AUD-SEC-296 | `echo 'touch M' \| awk -- '-1 {system($0)}'` | tái hiện được |
| AUD-SEC-297 | `awk '{system($0)}' < <(echo 'touch M')`; đối chứng `bash < <(…)` bị chặn | tái hiện được |
| AUD-SEC-298 | `perl -e 'system("touch", "M")'`, ruby, php `pcntl_exec`; đối chứng Python `subprocess.run([…])` bị chặn | tái hiện được |
| AUD-SEC-299 | `printf -v BASH_ENV '%s' f.sh; export BASH_ENV; bash -c true` | tái hiện được |
| AUD-SEC-300 | `mapfile -t PS4 <<< '$(touch M)'; set -x; true` | tái hiện được |
| AUD-SEC-301 | `echo 'touch M' \| tee >(bash)` | tái hiện được |
| AUD-PERF-010 (🟢) | `printf '%s\n' a0…aN \| sed '<~4000 ký tự>'` | không tái hiện được ở quy mô báo → 🟢 |
| AUD-SEC-302 (🟢) | `echo 'BEGIN{system("touch M")}' \| awk -f -`; `echo '1e touch M' \| sed -n -f - f` | tái hiện được |

## 5. Kế hoạch sửa (D-300)

Lát A–D guard theo ADR-0063, lát E `xt.py`, lát F sổ (🟢 nợ review), lát G `release-check` — chi tiết ở PLAN.
