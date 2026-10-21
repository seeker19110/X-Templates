# Audit X-Templates và bộ mẫu — 2026-10-21

> Commit quét: `main` `ec4c7d2da946730a945d719a3385ae381463987e` · Phạm vi: khung và bộ mẫu trong repo; không audit repo đích đang triển khai. PR này chỉ bổ sung báo cáo, bằng chứng rút gọn và [kế hoạch tối ưu](OPTIMIZATION-PLAN-2026-10-21.md); chưa sửa công cụ hoặc CI.

Khung có nền tảng kiểm soát chất lượng tốt: dependency khóa hash, action ghim SHA, mypy strict, coverage dòng/nhánh 100%, test chia theo lớp/trọng số và merge ghim HEAD. Tuy nhiên, đã tái hiện lỗi nhận bằng chứng Gate có thể làm bước xác minh xanh giả; CI mẫu còn lệch với `loop record` về số test thực chạy. Cổng xanh hiện hành chưa đủ để khẳng định các lỗi này được kiểm soát.

## Phát hiện ưu tiên

| Ưu tiên | Phát hiện | Bằng chứng và giới hạn | Đề xuất |
|---|---|---|---|
| 🔴 | **AUD-CODE-014 — đề nghị nâng từ 🟢 đang mở** | Với `X=''`, `test -n $X` exit 0, `test -n "$X"` exit 1 nhưng `same_command=True`. `tick_plan_task` tick sai; `_verify_gates(..., run_all=True)` bỏ Gate đỏ khi đứng sau Gate xanh. Đã tái hiện độc lập ở mức hàm; chưa kiểm toàn tuyến CLI/Stop hook/merge. | So khớp nguyên văn cho bằng chứng/khử trùng lặp; thêm regression cho expansion rỗng, quote, glob, assignment và heredoc. |
| 🟠 | **AUD-SEC-102 — còn tái hiện** | Trong repo tạm nhánh `main`, chỉ gọi guard: `git push origin` → `deny/PUSH_MAIN`; thêm `2>&1` hoặc `>/dev/null` → cho qua, mã `NONE`. Không push thật; ruleset từ xa vẫn có thể chặn. | Phân tích redirect đúng ngữ nghĩa trước luật Git; kiểm cả bare command, refspec, nhánh và đích không rõ. |
| 🟠 đề nghị | **AUD-XFEAT-013 — đề nghị nâng từ 🟢 đang mở** | Target có test thật, dùng Python 3.11 `unittest discover ... -k nonexistent_case`: `gate-par` exit 0, in `Ran 0 tests` và `GATE-PAR XANH`. `loop record` lại có cơ chế chặn. Đã tái hiện độc lập. | Dùng chung bộ nhận kết quả test cho commit/full/parallel/shard/CI/loop; ưu tiên outcome có cấu trúc của runner. |
| 🟠 khi bật reviewer | **Review thiếu diff — phát hiện đề xuất, chưa cấp ID** | `.github/workflows/pr-review.yml` cắt ở 400.000 byte: fixture 435.194 byte → exit 0, thay đổi auth cuối diff biến mất. Schema chỉ có clean/blocking, vẫn có đường ghi kết quả cho toàn HEAD. Chưa chạy bot hay chứng minh bot trả clean; workflow mặc định cần `XT_REVIEWER_ENABLED`. | Diff thiếu phải inconclusive hoặc chia đủ file/hunk, kiểm completeness và SHA trước khi xác nhận clean. |
| Khoảng trống hợp đồng CI | **Sàn khai riêng — phát hiện đề xuất, chưa cấp ID** | Fixture scale M/harden có 1 unittest: `coverage`/`format_check` riêng đều exit 1; `require lint test`, `gate-par`, `doctor`, `ci-check` đều exit 0. Template yêu cầu coverage nằm trong `test`, doctor chỉ kiểm khai lệnh; `loop verify` có chạy sàn. Không kết luận bypass toàn pipeline/G7. | Thống nhất thực thi sàn; trước khi sửa, coverage phải nằm trong `test`, format check trong lint. |

Các mức đề nghị và hai phát hiện chưa cấp ID chưa được cập nhật vào [ledger](AUDIT-STATUS.md). PR này không tuyên bố audit strict đã hoàn tất.

Vị trí nguồn tại SHA quét:

- `scripts/xt.py:1704`, `:1753`, `:1763` — shell identity; `:2253` — gộp Gate; `:2382` — tự tick.
- `.claude/hooks/guard.py:1039`, `:1736` — đối số vị trí và luật Git.
- `.github/workflows/pr-review.yml:60`, `:71`, `:81`, `:102` — cắt diff, prompt, schema và ghi kết quả.
- `scripts/dev-task.sh:231`, `:277`; `framework/templates/ci.yml:49`; `scripts/xt.py:3959` — runner, entry point CI và sàn của loop.

## Tái hiện lỗi Gate

Chạy từ gốc repo bằng Python ≥ 3.11; chỉ tạo fixture tạm, không push/merge:

```bash
python3 - <<'PY'
import os, subprocess, sys, tempfile
from pathlib import Path
sys.path.insert(0, "scripts")
import xt

os.environ["X"] = ""
plain, quoted = "test -n $X", 'test -n "$X"'
print("exit:", [subprocess.run(["bash", "-c", c]).returncode for c in (plain, quoted)])
print("same_command:", xt.same_command(plain, quoted))
with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    (root / "PLAN.md").write_text(f'- [ ] `T-001` quoted — Gate: `{quoted}`\n')
    print("tick:", xt.tick_plan_task(root, {"plan": "PLAN.md"}, "T-001", plain))
    tasks = [{"id": "T-001", "state": "x", "gate": plain},
             {"id": "T-002", "state": "x", "gate": quoted}]
    print("verify:", xt._verify_gates(root, tasks, 10, True))
PY
```

Kết quả tại SHA quét: exit `[0, 1]`, `same_command=True`, `tick=True`, verify chỉ có `T-001` exit 0. Đảo thứ tự Gate làm verify trả đỏ; đây là lỗi gộp bằng chứng, không chỉ khác cách trình bày shell.

## Bằng chứng kiểm tra

[Receipt JSON](evidence/audit-2026-10-21.json) lưu SHA, command, exit, số test, kết quả tái hiện và giới hạn; không phụ thuộc đường dẫn của phiên cloud.

| Kiểm tra | Kết quả tại SHA quét |
|---|---|
| `scripts/dev-task.sh gate`, Python 3.13.16 | exit 0; 234 lớp/1.363 test; coverage dòng + nhánh 100%; sàn 3.11.17 cũng đủ 234 lớp/1.363 test |
| Cùng full gate, Python 3.14.8 theo CI | exit 0; cùng số test và coverage; sàn 3.11 qua |
| `scripts/dev-task.sh gate-par`, Python 3.14.8 | exit 0; 5 task, cùng hai bộ 1.363 test, coverage 100%; một lượt đo 179,53 giây |
| Mypy strict, Ruff check/format, shellcheck, bash/JSON, link/license và `xt.py checks` | qua trong full gate |
| `xt.py doctor --json` | exit 0, `ok:true`, không findings sau activation |
| `xt.py autonomy-bench` | exit 0, 452 ca, false-green 0 trong corpus; không bao phủ hết lỗi ở trên |
| `pip-audit --require-hashes --strict --disable-pip -r requirements-dev.txt -r requirements-audit.txt` | exit 0, không CVE đã biết được báo lúc quét |
| `zizmor --offline --persona regular --min-severity high .github/workflows` | exit 0; không findings được báo, 16 ignored/13 suppressed |
| Gitleaks 8.30.1, artifact kiểm checksum từ release chính thức | exit 0, 244 commit/~9,83 MB, không leaks được báo |
| Cài/compose theo README, cài lại target không đổi | qua; strict blueprint mới exit 1 như dự kiến vì 489 MUST mở; không sinh `.xtemplates-new` |
| `xt.py audit check docs/ops/AUDIT-STATUS.md` thường và `--strict` | exit 1: tiền tố bằng chứng AUD-SEC-102 sai schema; strict còn chặn 🟠 đang mở |

Số test/coverage trên là kết quả ở commit quét, không thay thế CI của PR này. Ledger lúc quét có 73 khoản 🟢 mở; audit plan đánh dấu 61 tham chiếu blueprint có thể cũ và 9 nhóm cần rà theo diff. Không coi các cờ này là lỗi đã được xác nhận.

Trong môi trường cloud này, `.git` bảo vệ ở `/tmp` làm một test dò project root nhận nhầm thư mục. Cấu hình `TMPDIR` sang thư mục ghi được ngoài cây có marker đã giúp test qua; không đổi test hoặc xóa marker. Coverage `sysmon` dùng ở 3.14, core mặc định ở 3.13.

## Khoản nâng cấp tiếp theo và giới hạn

- Runtime phát triển ghim 3.13, quality CI dùng 3.14, sàn 3.11: cần thống nhất chủ đích, chưa tự nó chứng minh lỗi.
- AUD-CI-012 còn tái hiện: cài `--with-github` ở `mono/apps/web` đặt workflow trong thư mục con, GitHub không chạy chúng; cần kiểm Git root hoặc hỗ trợ prefix rõ ràng.
- AUD-CFG-003 còn tái hiện trong fixture: installer ghi xuyên symlink `.xtemplates/VERSION` vào file bên ngoài target; chưa chứng minh khai thác từ xa.
- AUD-ARCH-001: `xt.py` 10.144 dòng/580 hàm, `build_parser` 361 dòng; nên tách dần theo ADR và giữ CLI. Số dòng không tự chứng minh chạy chậm.
- AUD-TEST-019: refresh trọng số đo cả lớp kiểm chính file trọng số, có thể không tự hồi phục khi vượt trần; hiện thiếu 13 trọng số/thừa 1, chưa chạm ngưỡng lỗi.
- `harness-files.md:33` còn nói PLAN do “người duyệt”, lệch quy tắc phiên chính tự duyệt: cần rà tiếp chủ đề AUD-DOC-023.

Đã rà 11 nhóm áp dụng/rút gọn; UI/a11y và database N/A vì repo không có ứng dụng UI/CSDL. Chưa chạy CodeQL trực tuyến, kiểm ruleset/credentials reviewer/steward sống, chứng nhận pháp lý hay đo repo đích triển khai. Thời gian cục bộ một mẫu không chứng minh CI tăng tốc. [Kế hoạch tối ưu](OPTIMIZATION-PLAN-2026-10-21.md) ghi tiêu chí nhận thay đổi và thứ tự sửa.
