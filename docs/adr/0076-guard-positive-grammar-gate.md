# ADR-0076: Guard — lệnh có luật chỉ chạy khi mọi từ thuộc ngữ pháp đọc chắc (cổng tập con dương)

- **Trạng thái:** Đã chấp nhận 2026-11-13 — chủ repo chọn hướng "khoá tập con đọc chắc" khi số 🔴 guard tăng ròng
  (13 → 18 trong một phiên `/complete`); phiên chính chốt thiết kế theo tiêu chí chất lượng cuối (ADR-0008) —
  **D-430** (ngữ pháp dương), **D-431** (mã `BUDGET`, cổng hẹp, ngưỡng dừng), **D-432** (691 và 648).
- **Trạng thái triển khai:** chưa bắt đầu — sáu lát và một lát riêng ở §Quyết định; PR của ADR này chỉ có tài liệu.
- **Ngày:** 2026-11-13.
- **Thay:** cách mở rộng tập con đọc chắc bằng bảng cấm theo từng cú pháp (`STRICT_PLAIN/LIVE/RAW/BARE`, ADR-0063/0065).
  **Giữ:** ADR-0002 (fail-closed về hành động nguy hiểm, fail-open về luồng), ADR-0018/0019 (guard không hỏi người),
  ADR-0063 (ngoài tập con → `BUDGET`), ADR-0065 (danh sách trắng cho mở rộng động), ADR-0066, ADR-0067 (tên/đường dẫn dựng
  lúc chạy chấp nhận tới 2027-01-21); mọi luật hiện có — lớp mới OR với luật cũ (bài học #352, #372).
- **Liên quan:** ADR-0056 (lỗi có từ trước không chặn PR, sổ audit chặn phát hành), ADR-0072 (trần byte và chi phí compile
  `guard.py`), D-415 (ca không đọc chắc → chặn, không thêm cách đọc mới), D-429 (CR trần ngoài nháy → `BUDGET`).
- **Thiết kế và số đo:** phương án do agent `Plan` lập 2026-11-13 trên `HEAD` `753687bf` — mọi số dòng dưới đây thuộc
  `.claude/hooks/guard.py` ở bản đó và sẽ trôi; nhà của số là mã.

## Bối cảnh

Guard đọc lệnh Bash bằng bộ tách từ tự viết (`tokenize` bằng `shlex`, `_raw_tokens` giữ nháy). Mỗi cú pháp bash mà bash
hiểu khác guard là một lỗ cho qua. ADR-0063 (2026-11-01) đã quyết "ngoài tập con đọc chắc → chặn, không vá từng ca", nhưng
tập con được cài bằng **bảng cấm** (các cặp regex–lý do `STRICT_*` ở dòng 1449–1503): cú pháp chưa liệt kê mặc định được
cho qua. Mười hai ngày sau còn 16 🔴 cùng họ, và phiên `/complete` 2026-11-12…13 cho thấy xu hướng:

| Lát guard | 🔴 do diff gây ra | 🔴 có từ trước mới tìm ra |
|---|---|---|
| AUD-SEC-611 (#517 → #521) | 1 | 4 (`time`, `coproc`, `${ …; }`, extglob) |
| AUD-SEC-632…635 (#522) | 3 | 2 (`{fd}>tệp` đứng đầu, alias bị che) |
| AUD-SEC-644/645 (#523) | 1 | 2 (biến dính trước cờ, cờ dài ngoài danh sách) |

Số 🔴 mở đi từ 13 lên 18 dù đã đóng 10 mục: mỗi review độc lập (`reviewer-alt`, effort cao nhất) lại thêm khoảng hai.
Vá thêm vào bảng cấm là cùng một lỗi cốt lõi dưới tên khác — `time`, `coproc`, `${ ` thêm vào `STRICT_*` vẫn là liệt kê
cái đã biết.

## Các phương án đã cân nhắc

1. **Tiếp tục vá từng biến thể vào bảng cấm.** Không có điểm dừng (bảng trên); mỗi lát ~1–2 giờ và sinh thêm lỗi.
2. **Parser bash thật** (`bashlex`, `tree-sitter`). Chính xác nhất nhưng phá ràng buộc "chỉ stdlib Python ≥ 3.11" của khung
   và `guard.py` (hook chạy `python3 -I`); cần vendor, ADR riêng, nhiều ngày. Loại.
3. **Cấm mọi mở rộng trần ở lệnh có luật.** Đo thô: 2,0 % lệnh thật bị chặn thêm (374/18.274). Chặn oan quá cao. Loại.
4. **Sandbox hệ điều hành thay guard.** ADR-0066 đã ghi nó không chặn được `git push --force`; đánh giá riêng trước
   2027-01-21 (D-331/D-332, ADR-0072) — không thay thế quyết định này.
5. **Ngữ pháp dương (chọn).** Lệnh có luật chỉ qua khi mọi từ thuộc dạng được phép; cú pháp bash mới mặc định nằm ngoài
   tập con. Lệch của bộ đọc tự viết nghiêng về chặn thay vì về cho qua.

## Quyết định

Thêm một mắt xích **`_ruled_word_why`** vào chuỗi OR của `_allowlist_why` (dòng ~2108–2114). Nhờ vậy nó tự chạy sau luật
cũ qua `_argv_shell_check` (lệnh luật cũ đã chặn giữ mã cũ), tự áp cho script lồng nguyên văn, bỏ qua chữ lỏng
(`budget.loose`) và mang mã **`BUDGET`** (deny ở mọi chính sách — `BUDGET ∈ UNSURE_CODES`; không thêm mã, không tách
ask/deny vì ADR-0018/0019). Mỗi lý do có dòng `viết lại: …` (D-415).

**Bộ đọc:** chỉ dùng đường có sẵn — `_raw_tokens(cmd, True)` → `_plain_argvs` → `_brace_segments` → `_strip_prefixes`,
phân loại ký tự bằng `_CodeView(word).kind/top` như `_gh_lead_flag`; một lượt, tuyến tính theo độ dài lệnh.
**Kích hoạt:** lệnh đơn có từ bỏ nháy mà basename thuộc `GATE_NAMES` (frozenset gom từ bảng có sẵn: `git`, `gh`, `SHELLS`,
`eval`/`source`, `WRAPPERS` và mọi tên `_scan_command` có nhánh; một test khẳng định hai tập khớp nhau). Lệnh không có tên
có luật (`python3 scripts/xt.py …`, `scripts/dev-task.sh …`, `pytest`) không qua cổng.

**Ngữ pháp được phép khi lệnh có luật** (ngoài đó → `BUDGET`):

| Vị trí | Ngoài tập con (chặn) | 🔴 đóng |
|---|---|---|
| P0 tiền tố | `{tên}>`/`{tên}<`; `coproc`; `time` rồi tới gán/từ khoá/`{`/`function`; `exec` có cờ ngoài `-a TÊN`; cờ/thời lượng của trình bọc có mở rộng | 657/700, 664, 663, 659 |
| P1 lệnh con (git cả cấp hai của `stash`/`remote`/`worktree`/`reflog`) | có `$`, backtick, glob, extglob | 690 (phần `stash drop$X`) |
| P2 từ dạng cờ | `$`/backtick/glob TRƯỚC `=` ở cờ ngắn lẫn dài, không tra `GIT_DANGER_LONG` | 690, 711 |
| P3 từ mở đầu bằng mở rộng | mở rộng liền sau là chữ `-…` (`$X--delete`, `"$X"-f`, `$(true)--hard`) | 710 |
| P4 thay lệnh/tiến trình | `<(…)`/`>(…)` làm đối số; `$(…)`/backtick trần còn từ theo sau hay dính chữ sau | 609 |
| P5 chuyển hướng | chuyển hướng rồi còn từ thường (git/gh; đo rồi mới mở rộng) | 680 |
| P6 toàn lệnh | `${ `/`${\|`; extglob trần ngoài `((…))`; `\` lẻ cuối lệnh; nháy không đóng ở lệnh gốc | 665, 666, 656 |
| P7 hàm và stdin | lệnh gốc khai hàm mà thân có tên có luật hay shell đọc stdin | 660, 661 |
| P8 thân `sh -c`/`eval`/`trap` trong nháy kép | có `\$`, `` \` `` | 606 |

Giữ nguyên (không chặn): glob ở đối số không phải cờ (`rm -f *.tmp`, `git add docs/*.md`), biến trần hay nháy kép ở vị
trí giá trị (`git push -u origin "$B"`, `gh pr view $PR`, `rm -rf "$TMP"/x`), heredoc có nháy cho `git commit`/`gh`, `"$(…)"`
trong nháy kép, CR (D-429).

**Hai 🔴 ngoài lớp cú pháp (D-432):** 691 (`ssh-agent bash -c '…'`) bằng **đọc lại hậu tố** — lệnh lạ không thuộc bảng thụ
động (`echo`/`grep`/`cat`…) mà có tên có luật trong 3 đối số đầu thì quét hậu tố từ tên đó như một lệnh; chỉ thêm chặn
(`gitleaks git --no-banner` vẫn qua), không dựng bảng trình bọc (lại là danh sách cấm). 648 (formatter chạm dòng ký
GO-NO-GO) ở **phía Write/Edit**: dòng §5 có ô tên/ngày mà không ở dạng bảng chuẩn thì chặn lúc ghi — ngoài cổng.

**Lát triển khai** (mỗi lát ≤ ~150 dòng mã, một PR, test đỏ trước, review `reviewer-alt`):

| Lát | Nội dung | Đóng |
|---|---|---|
| 0 | Dựng bộ lệnh lành làm ca `control` (khối lệnh trong `.claude/skills/*/SKILL.md`, `scripts/dev-task.sh`, `AGENTS.md`) + `GATE_NAMES` + test khớp; chưa đổi hành vi | — |
| 1 | P6 vào `STRICT_LIVE`/`STRICT_BARE` và `_strict_why`; `\` lẻ → `BUDGET` | 665, 666, 656 |
| 2 | Khung `_ruled_word_why` + P2, P3, P1 cấp hai | 690, 710, 711 |
| 3 | P4 | 609 |
| 4 | P0 | 657/700, 664, 663, 659 |
| 5 | P5 (git/gh) và P7 | 680, 660, 661 |
| 6 | P8 và hậu tố cho 691 | 606, 691 |
| Riêng | 648 phía Write/Edit | 648 |

**Ngưỡng dừng (D-431):** mỗi lát đo trước/sau trên các lệnh Bash thật trong transcript phiên (dữ liệu phiên, không đưa vào
repo — cùng phép đo ADR-0063/0065); lát nào làm hơn **0,2 %** lệnh thật đổi từ cho qua sang chặn thì không merge và mở D mới.

## Hệ quả

- **Đo chặn oan (thiết kế, chưa phải triển khai).** Trên 18.274 lệnh Bash khác nhau (27.542 lượt) của repo này: có tên có
  luật 9.392; cổng hẹp P0–P7 khớp 33, trong đó **13 (0,07 %)** hiện đang cho qua; biến thể chặt (cấm mọi từ mở đầu bằng mở
  rộng ở git/gh/rm…) 75 (0,41 %); cấm mọi mở rộng trần 374 (2,0 %). Corpus có cả phiên sửa guard nên số bị thổi lên.
  Nền hiện tại: `deny BUDGET` ≈ 3,1 % lệnh bash trong `.autopilot/guard-log.jsonl` — chặn oan đã không nhỏ nên mỗi lát phải đo.
- **Đóng 18 🔴 đang mở của họ này** theo bảng lát (606, 609, 656/657/659/660/661, 663–666, 680, 690, 700, 710, 711 và 648; 691
  bằng hậu tố) — mới là các biến thể ĐÃ biết. **Không đóng được** hai lớp sau, và đó là chỗ review còn có thể tìm ra thêm —
  ghi thẳng, không giấu:
  1. **Giá trị biến không biết** (`git reset "$X"` với X=`--hard`, `rm -rf $d`) — không phải lỗi đọc cú pháp; cần phạm vi
     chấp nhận của ADR-0067 (hạn **2027-01-21**) hoặc sandbox. Biến thể chặt đóng thêm một phần với giá 0,41 % — **chưa làm**.
  2. **Ngữ nghĩa CLI của từng chương trình** (trình bọc nhận lệnh qua chuỗi: `su -c`, `watch '…'`) — cổng cú pháp không thấy.
  Vì vậy sổ audit sẽ **còn 🔴 cùng họ sau các lát trên** nếu review tìm ra thêm ở hai lớp này; ngưỡng dừng và D-430 cho phép
  ghi chấp nhận có hạn thay vì vá tiếp.
- **Lệnh lành phải viết lại** (đường thoát cho agent): `git diff --stat $(git merge-base HEAD origin/main) HEAD` → `MB=$(…)`
  rồi `"$MB"`; `time PATH=…:$PATH cmd` → `time env PATH=… cmd`; `bash -c "echo \$HOME"` → thân nháy đơn;
  `git log 2>/dev/null --oneline` → chuyển hướng ra cuối; việc lặp nhiều → subcommand `xt.py`.
- **Chi phí:** `guard.py` 928.462 B so với trần `.claude/hooks/` 1.417.969 B (ADR-0043/0072); sáu lát ≈ 700 dòng (~70 KB)
  vẫn trong trần; cổng chỉ quét một lượt nên không thêm bậc hai, nhưng chi phí compile mỗi lệnh Bash tăng theo kích thước
  (đo lại ở T-3709).
- **Rủi ro kỹ thuật:** cổng đứng trên `_raw_tokens` — cũng là bộ đọc tự viết; ngữ pháp dương làm lệch của nó nghiêng về chặn.
  `!(` có thể trùng `(( !(a) ))` — cần ca đối chứng ở lát 1. Agent hiện gần như không dùng được hàm shell (mọi lệnh khai hàm
  thật đều đã bị luật khác chặn) nên P7 không thêm chặn oan đo được.
- **Dự án đích:** chặn mới ở các mẫu trên — chạy lại `install.py` để nhận guard mới; agent đọc dòng `viết lại:` của lý do.

## Xác nhận

- Mỗi lát: ≥ 1 ca corpus `BUDGET` + ≥ 1 ca đối chứng `allowed: true` cho mỗi 🔴 (ví dụ `git tag -a v1 -m "$M"`,
  `git push -u origin "$B"`, `git diff "$A".."$B"`, `gh pr view $PR`, `rm -rf "$TMP"/x`, commit bằng heredoc);
  `python3 scripts/xt.py autonomy-bench` exit 0 với false-green 0 và chặn oan 0; `python3 -m unittest tests.test_hooks
  tests.test_guard_fuzz tests.test_guard_strict tests.test_xt_core tests.test_ci_shard` xanh (test shard có dung sai
  trọng số; chạy `dev-task.sh test-weights` khi thêm lớp test).
- Số đo trước/sau ghi vào mô tả PR; đột biến một dòng của cổng phải làm đỏ test.
- `implementation-status` do PR từng lát cập nhật.

## Đường lùi

Các lát độc lập nhau: revert một PR đưa lát đó về bảng cấm `STRICT_*` của ADR-0063/0065; mã `BUDGET` và chính sách không
đổi nên không cần dọn. Muốn nới ngưỡng hay đổi mã → D mới, không sửa ADR này.
