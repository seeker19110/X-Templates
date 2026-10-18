# PLAN.md — Khung X-Templates · bản 3.4.1: bịt phần "Còn lọt" của guard + contrast CSS lồng (2026-10-18)

> Lập ngày 2026-10-18. Chủ repo gọi `/autopilot` (không đối số) ngay sau đề xuất "làm tiếp các lỗ này thành 3.4.1".
> Kế hoạch trước (T-1101…T-1104) xong ở #109–#111.

## Tóm tắt (cổng duyệt — phiên chính tự duyệt, D-051)
- Phạm vi: mục "Còn lọt" của CHANGELOG 3.4.0 + ba điểm ghi nhận của review #134–#136.
- Stack: Python ≥ 3.11 stdlib, không phụ thuộc mới; cổng `scripts/dev-task.sh gate` (mypy --strict, coverage 100%).
- Không làm: ghép chuỗi tên hàm lúc chạy (`getattr(os, 'sys'+'tem')`) — né cố ý, ngoài phạm vi guard chống tai nạn
  (guard.py dòng 16); giữ trong `KNOWN_GAPS`.
- Nhánh: lát A+B một PR (`fix/guard-gaps-341`, cùng sửa CHANGELOG — tách thì xung đột), phát hành một PR.
- Rủi ro: chặn nhầm lệnh hợp lệ (đỡ bằng bộ lệnh hợp lệ trong `tests/test_guard_corpus.py`); quét chậm (ngân sách D-050).

## Ngân sách (4 con số)
- Số vòng tối đa: 56 (`max(40, 8 × task chưa làm)`)
- Chi phí: 0 đồng ngoài phiên (không phụ thuộc mới)
- Timeout mỗi lệnh Gate: 1800 giây (`XT_RECORD_TIMEOUT` mặc định)
- Ngày hết hạn: 8 giờ sau `loop init` (`--hours 8`)

## Điểm dừng bắt buộc (`loop defer`; `loop block` khi mọi việc còn lại phụ thuộc)
- Ruleset đòi review của người (`merge-check` = `human`) → báo chủ repo, làm lát khác
- Force-push, xoá nhánh, đổi quyền/ruleset repo

## Task

### Lát A — guard (D-052)
- [x] `T-1201` Biến từ `$(echo|printf …)`, `read … <<< '…'`, `${y:-…}` được thay giá trị và quét; `KNOWN_GAPS` bớt 3 dòng — Gate: `python3 -m unittest tests.test_guard_corpus`
- [x] `T-1202` Shell đọc từ ống sau bộ giải mã (`base64 -d`, `xxd -r`, `openssl … -d`): giải mã chữ được thì quét, không thì chặn — Gate: `python3 -m unittest tests.test_guard_corpus`
- [x] `T-1203` Ghi `.autopilot/` qua `sort -o`, `sed 'w …'`, `awk -i inplace`, `perl -e unlink`, `git restore|checkout .autopilot` bị chặn — Gate: `python3 -m unittest tests.test_guard_corpus tests.test_hooks`
- [x] `T-1204` `bash -c "$(cat <<'E' … E)"` được quét; code span trong thân heredoc message của commit không bị chặn nhầm; `for` > 64 từ và `subprocess.run([..]+[..])` — Gate: `scripts/dev-task.sh gate`

### Lát B — contrast (D-053)
- [x] `T-1205` `xt.py contrast`: khối lồng `:root{&.dark{…}}` (CSS nesting) thuộc theme tối, không rò sang theme sáng — Gate: `python3 -m unittest tests.test_ui_gates`

### Lát C — phát hành
- [x] `T-1206` VERSION 3.4.1 + CHANGELOG `[3.4.1]` + PROGRESS; tag `v3.4.1` — Gate: `scripts/dev-task.sh gate`
