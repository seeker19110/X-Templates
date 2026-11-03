# ADR-0066: Guard xét tệp do chính lệnh ghi theo TÊN tệp được nhắc lại, không liệt kê trình chạy

- **Trạng thái:** Đã chấp nhận 2026-11-03 (phiên chính tự duyệt theo tiêu chí chất lượng cuối, ADR-0008 — **D-327**).
- **Trạng thái triển khai:** chưa (PR kế sau #426).
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
   trừ miễn D-324. Trình ghi: thêm giá trị của `-o`/`--output[=]` của mọi lệnh và đích ghi mà bộ quét script sẵn có
   (`python3 -c`, `node -e`…) nhận ra (`open(…,'w')`, `writeFile`) vào tập đích ghi.
3. **Sandbox bắt buộc** (Claude Code sandbox) — không chặn được `git push --force` (mạng tới GitHub là việc bình thường),
   chưa bắt buộc ở mọi quy mô; trái (1) với lớp force-push/ghi hook.
4. **Bỏ luật ghi-rồi-chạy**, dựa vào ruleset GitHub chặn force-push — không che `rm -rf ~`, ghi `.claude/hooks`.

## Quyết định

Chọn **2**. Thêm: miễn D-324 chỉ mất khi `cd`/`pushd`/`popd` nằm **giữa** lệnh ghi và lệnh chạy (đứng trước cả hai thì
thư mục chung, thân quét đúng thư mục). Tên tệp có mở rộng (`$f`, `${d}/x.py`) giữ luật hiện tại (BUDGET khi không giải
được). Tên quá ngắn/chung (≤ 2 ký tự sau khi bỏ đuôi, như `a`, `x`) vẫn tính — chặn oan chấp nhận, viết lại bằng tên rõ.

## Hệ quả

- Đóng AUD-SEC-406 (mọi dạng trong sổ có tên tệp nhắc lại); dạng ghi qua cơ chế guard không nhận ra VÀ không nhắc lại
  tên (tên dựng lúc chạy) đã là BUDGET theo ADR-0063/0065.
- Chặn oan mới có thể: lệnh ghi tệp dữ liệu rồi đọc lại bằng công cụ khác (`git diff > p.diff && grep x p.diff`). Giới
  hạn bằng danh sách TRẮNG lệnh chỉ đọc không chạy mã (`cat head tail grep rg wc diff cmp sort uniq-không-đích cut ls
  stat file jq less`, `git add/diff/show/apply --check`) cùng tệp KHÔNG có đuôi script (`.sh .bash .zsh .py .js .mjs .cjs
  .ts .rb .pl .php .lua .awk .sed .mk`, `Makefile`): nhắc lại tên ở lệnh trong danh sách trắng thì không tính. Hướng an
  toàn: lệnh lạ (chưa biết có chạy mã không) bị tính — ngược với danh sách trình chạy của #426. Đo lại transcript như
  #426, ghi số vào PR.
- Đường lùi: revert PR triển khai; AUD-SEC-406 về `mở`.
