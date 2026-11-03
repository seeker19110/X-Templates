# ADR-0066: Guard xét tệp do chính lệnh ghi theo TÊN tệp được nhắc lại, không liệt kê trình chạy

- **Trạng thái:** Đã chấp nhận 2026-11-03 (phiên chính tự duyệt theo tiêu chí chất lượng cuối, ADR-0008 — **D-327**).
- **Trạng thái triển khai:** một phần (#427) — `_reuse_why` trong `.claude/hooks/guard.py`; review #427 thu về luật chặn
  (**D-329**); AUD-SEC-406 còn `mở` (tên dựng lúc chạy, tên ngầm — xem Hệ quả).
- **Ngày:** 2026-11-03.
- **Thay:** cách đóng AUD-SEC-400 bằng danh sách trình chạy/trình ghi (`_script_run_why`, #426). **Giữ:** ADR-0063,
  ADR-0065, miễn D-324 (heredoc có nháy ghi bằng `cat`/`tee` rồi chạy ngay — quét thân như script) — lớp mới OR với
  luật cũ (bài học #352, #372).
- **Liên quan:** ADR-0002 (fail-closed hành động nguy hiểm), ADR-0018/0019 (guard không hỏi người), ADR-0043 (trần byte),
  ADR-0056 (lỗi có từ trước không chặn PR, sổ audit chặn phát hành), D-324, D-326.

## Bối cảnh

Guard không đọc nội dung tệp lúc chạy (đã kiểm: `bash s.sh` với tệp có thật — #426). Vì vậy một lệnh ghi tệp rồi chạy
chính tệp đó trong cùng lệnh (`printf 'git push --force origin main\n' > s.sh; bash s.sh`) cho guard thấy hai lệnh vô
hại (AUD-SEC-400). #426 đóng dạng này bằng cách liệt kê trình chạy (`bash`/`sh`/`source`/`python3 F`…) và trình ghi
(`>`/`tee`/`cp`…). Review #426 (2026-11-03, bash 5.2.21 + stub `git`) chứng minh danh sách luôn thiếu — AUD-SEC-406:
trình chạy `python3 -m x`, `python3 -c 'import x'`, `node -e 'require("./x.js")'`, `chmod +x s.sh; PATH=.:$PATH s.sh`,
`find d -name s.sh` kèm `-exec bash {}`, `bash --rcfile s.sh -i`, `PYTHONSTARTUP=x.py python3 -i`, `awk -f`, `sed -f`,
`make -f`; trình ghi `python3 -c "open('s.sh','w')…"`, `iconv -o s.sh`, `uniq IN OUT`. Sáu dạng đã chạy push thật.
Cùng lúc, luật "có `cd`/`pushd`/`popd` thì mất miễn D-324" (#426, D-326) chặn oan dạng phổ biến nhất của phiên —
`cd <repo> && cat > f <<'EOF' … EOF … python3 f` (238/317 lệnh cho qua → chặn trên 5 171 lệnh thật).

## Yếu tố quyết định

- (1) đúng và an toàn: không còn phụ thuộc danh sách trình chạy — dạng chạy mới không mở lại lỗ.
- (3) đơn giản, test được: một luật theo dữ liệu có sẵn (đích ghi của lệnh), không suy cấu trúc mới (tinh thần ADR-0065).
- (4) trải nghiệm: không chặn oan dạng `cd X && cat > f <<'EOF' … python3 f`.

## Các phương án đã cân nhắc

1. **Vá tiếp danh sách** trình chạy/trình ghi — mỗi review lộ dạng mới (#422/#423/#426); trái (1).
2. **Theo tên tệp** (chọn): tệp là đích ghi của lệnh (mọi cách guard nhận ra) mà TÊN của nó (đường dẫn, tên gốc, hay
   tên gốc bỏ đuôi — `x.py` → `x` cho `-m x`/`import x`/`require("./x")`) xuất hiện lại ở BẤT KỲ chỗ nào khác của lệnh
   (đối số, gán biến môi trường như `PATH=`/`PYTHONSTARTUP=`, mẫu glob của `find -name`, chữ trong `-c`/`-e`) → BUDGET,
   trừ miễn D-324. Trình ghi: thêm giá trị `--output[=]` và `-o` (đọc cụm cờ ngắn như getopt; trừ lệnh mà `-o` không
   phải tệp ra — `grep`, `ls`, `ssh`, shell…, riêng `git grep`) và đích ghi mà bộ quét script sẵn có
   (`python3 -c`, `node -e`…) nhận ra (`open(…,'w')`, `writeFile`) vào tập đích ghi.
3. **Sandbox bắt buộc** (Claude Code sandbox) — không chặn được `git push --force` (mạng tới GitHub là việc bình thường),
   chưa bắt buộc ở mọi quy mô; trái (1) với lớp force-push/ghi hook.
4. **Bỏ luật ghi-rồi-chạy**, dựa vào ruleset GitHub chặn force-push — không che `rm -rf ~`, ghi `.claude/hooks`.

## Quyết định

Chọn **2**. Miễn D-324 giữ như #426 (D-329 thu hồi ý định "chỉ mất khi `cd` nằm giữa"): có `cd`/`pushd`/`popd` ở bất
kỳ đâu, hay lệnh gán biến trước trình chạy (`CDPATH=`, `HOME=` đổi đích `cd`) → không miễn. Tên tệp có mở rộng (`$f`,
`${d}/x.py`) giữ luật `_script_run_why`: chỉ chặn khi lệnh khác CHẠY một tệp (tên có mở rộng coi như trùng) — lệnh lạ
nhận tên có mở rộng (`python3 -m "$m"`) không bị luật này bắt. Tên quá ngắn/chung (≤ 2 ký tự sau khi bỏ đuôi, như `a`, `x`) vẫn tính — chặn oan chấp nhận, viết lại bằng tên rõ.

## Hệ quả

- Đóng các dạng NGUYÊN VĂN của AUD-SEC-406 (tên tệp nhắc lại). Chưa đóng — AUD-SEC-406 còn `mở`, cần ADR riêng
  (review #427): tên dựng lúc chạy (`python3 -m "${y:-x}"`, `-m "$(printf '\x78')"`, `-m "${m,,}"`,
  `__import__("X".lower())`, tệp tên biến + `PATH=.`) — ADR-0063/0065 không chặn hết các mở rộng này; tên ngầm có từ
  trước (`> Makefile; make`, `> package.json; npm test`, `> conftest.py; pytest`, `> ~/.bashrc; bash -ic`, `patch` với
  `+++ s.sh`).
- Chặn oan mới có thể: lệnh ghi tệp dữ liệu rồi đọc lại bằng công cụ khác (`git diff > p.diff && grep x p.diff`). Giới
  hạn bằng danh sách TRẮNG lệnh chỉ đọc không chạy mã (`cat head tail grep rg wc diff cmp sort uniq-không-đích cut ls
  stat file jq`, `git add/diff/show/apply --check`; D-329 bỏ `less` — `LESSOPEN` chạy lệnh) cùng tệp KHÔNG có đuôi script (`.sh .bash .zsh .py .js .mjs .cjs
  .ts .rb .pl .php .lua .awk .sed .mk`, `Makefile`): nhắc lại tên ở lệnh trong danh sách trắng thì không tính. Hướng an
  toàn: lệnh lạ (chưa biết có chạy mã không) bị tính — ngược với danh sách trình chạy của #426. Đo lại transcript như
  #426, ghi số vào PR.
- Triển khai (#427) thêm ba miễn theo giá trị, mỗi miễn không mở đường chạy mã: (a) tên gốc bỏ đuôi chỉ tính khi đuôi
  không phải dữ liệu (`.txt .log .md .json .diff .html .csv .yaml …` — không trình nạp mô-đun nào tìm `x` ra `x.log`);
  (b) tệp không đuôi script chỉ là ĐỐI SỐ dữ liệu sau chương trình `-c`/`-` của PYTHON (D-329: perl `do $ARGV[0]` lọt
  bộ đọc) mà `_read_only_script` xác nhận chỉ đọc và không nhắc tên tệp (`python3 -c '…json.load(open(sys.argv[1]))'
  p.json`); (c) tệp
  nội dung của `gh pr|issue … -F`/`--body-file`/`< F` (gh gửi chữ, không chạy; nội dung do luật đăng bài D-270 xét).
  Lệnh chỉ đọc mà stdout đổ vào lệnh lạ (`cat f | python3 x`) hay nằm trong `$(…)` vẫn tính.
- D-328 (sau đo lần đầu: 340 qua→chặn): danh sách trắng thêm lệnh không chạy mã theo tên tệp — `mkdir echo touch
  chmod md5sum sha*sum`, `printf` không `-v`, `sed -n` chỉ in (không `-i`/`-f`, chương trình không `w`/`W`/`e`/`r`/`R`);
  `chmod +x F` rồi chạy F vẫn bị bắt ở lệnh chạy. Không miễn tệp dữ liệu vào script có sẵn/`-m` (phương án C bị loại).
- D-329 (review #427, 7 🔴): mọi miễn của danh sách trắng (lệnh đọc, dữ liệu sau `-c`, tệp nội dung `gh`) không áp
  khi từ lệnh trùng tên gốc tệp vừa ghi (`> ~/.local/bin/ls; ls`), tệp nằm dưới `~`/`$HOME`/`$PWD`, hay lệnh gán biến
  `PATH`/`GIT_*`/`LESS*` (`GIT_EXTERNAL_DIFF=sh`, `LESSOPEN='|sh %s'`); `git grep` là lệnh duy nhất được miễn `-o` theo
  lệnh con (`git archive -o` là ghi). AUD-SEC-410 mở lại: trả sớm theo token của `find_root_scan` để lọt
  `git rebase --exec 'find . -delete'`, `make --eval=…` (xoá repo thật) — cần miễn theo lệnh dữ liệu biết chắc.
- Chặn oan có chủ đích (đổi kỳ vọng test/bench): tệp vừa ghi đi vào script có sẵn hay `-m` (`python3 sum.py < in.txt`,
  `bash run.sh < in.txt`, `python3 -m json.tool out.json` — gỡ một phần AUD-SEC-407); `cd`/gán biến trước heredoc ghi
  rồi chạy (D-324 như #426); **dự án đích** build rồi chạy trong một lệnh (`go build -o bin/app … && ./bin/app`,
  `gcc -o hello … && ./hello`) — viết lại thành hai lệnh Bash. Lệnh Kiểm `UX-DS-021` viết lại dạng ống (không ghi
  `lint.json` rồi đọc lại).
  Đo 5 445 lệnh Bash thật (2026-11-03, sau D-329): so main 91a07493 — 338 qua→chặn (194 tệp dữ liệu vào lệnh lạ, 135
  tệp script sửa rồi đọc/chạy lại, 9 AUD-SEC-400), 0 chặn→qua.
- Đường lùi: revert PR triển khai.
