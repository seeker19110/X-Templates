# ADR-0065: Guard xét mở rộng động theo danh sách trắng — không suy cấu trúc lệnh để miễn

- **Trạng thái:** Đã chấp nhận 2026-11-03 (phiên chính tự duyệt theo tiêu chí chất lượng cuối, ADR-0008 — **D-322**).
- **Trạng thái triển khai:** Đã làm bốn lớp A–D trong `.claude/hooks/guard.py` (`_allowlist_why`, gọi sau luật cũ ở
  `_argv_shell_why`), PR nhánh `adr-guard`; đóng AUD-SEC-388 (gồm chỉ số `${#a[k]}`, `[k]=` khởi tạo mảng có nháy của review #423 và dạng toán hạng có nháy/thoát của review lượt 2 —
  base và lượt 1 cùng lọt)/391/392/393/396/398/401. Còn mở hai lỗ có từ trước ngoài
  phạm vi lớp này: AUD-SEC-399 (mảng nhiễm làm đối số), AUD-SEC-400 (ghi script rồi chạy trong cùng lệnh).
- **Ngày:** 2026-11-03.
- **Thay:** cách vá AUD-SEC-388 theo cấu trúc lệnh của #420/#422 (D-321). **Giữ:** ADR-0063 (ngoài tập con đọc chắc →
  `BUDGET`), mọi luật hiện có — lớp mới OR với luật cũ (bài học #352, #372).
- **Liên quan:** ADR-0002 (fail-closed hành động nguy hiểm), ADR-0018/0019 (guard không hỏi người), ADR-0056 (lỗi có từ
  trước không chặn PR, sổ audit chặn phát hành), ADR-0063.

## Bối cảnh

Bash tách từ của mở rộng không nháy theo `IFS` hiện hành; guard tách theo khoảng trắng. `IFS=/; c=git/push/--force/
origin/main; $c` chạy `git push --force origin main` mà guard thấy lệnh `$c` (AUD-SEC-388, review #420). Họ lỗi rộng hơn
`IFS`: mọi chỗ bash gán biến theo tên đọc lúc chạy (`read "$n"`, `declare -n`, `${!n:=…}`, số học đánh giá đệ quy giá trị
biến) hay chạy lại chữ dữ liệu như mã (`mapfile -C`, `${x@P}`) đều làm guard đọc lệnh khác bash.

Ba lượt vá theo cấu trúc lệnh (#372 lượt cũ, #420, #422 hai lượt — D-321) đều lọt dạng mới: review #422 tìm 5 dạng base
cũng lọt — hàm `function f { IFS=/; }`, vùng `((` giả trong nháy, từ lệnh có nháy `'env'`, `read` định nghĩa trong `eval`,
`IFS=/ exec read`. Review nội bộ blk-guard (#422) thêm AUD-SEC-391 (từ lệnh là mảng dựng từ dữ liệu: `read -ra a <<< 'git
push --force origin main'; "${a[@]}"`) và AUD-SEC-392 (heredoc không nháy đổ vào shell — thân mở rộng hai lần). Review
nhánh `adr-guard` (2026-11-03) tìm tiếp các dạng lách bản nháp đầu của chính ADR này: `function NAME {` che từ lệnh,
`bash 0<<EOF`, `\$` trong nháy kép đọc lại bởi `mapfile -C`/`${y@P}`, `${!y:=/}` trong thân heredoc của builtin (`: <<E`),
giá trị cờ không nháy (`read -t $T v` với T=`1 IFS` thành `read -t 1 IFS v`), sed `Wfile` dính liền. Mọi dạng đã chạy thật
trên bash 5.2.21 / GNU sed 4.9 với stub `git` (không đụng repo thật).

## Các phương án đã cân nhắc

1. **Vá tiếp từng dạng theo cấu trúc** (lần thứ tư) — ít chặn oan nhất, nhưng mỗi lượt review lộ dạng mới (#372, D-321);
   không có điểm dừng, trái tiêu chí (1).
2. **Danh sách trắng neo chặt** (chọn) — không suy cấu trúc (hàm, vòng, vùng số học, lớp lồng) để MIỄN; chỉ miễn theo GIÁ
   TRỊ chắc chắn (`$?`/`$#`/`$$`/`$!`/`${#…}`, `$((…))` đóng như bash, `$'…'`). Dạng lách mới thì MỞ RỘNG điều kiện kích
   hoạt/vùng bị coi là không đọc chắc, không thêm miễn trừ.
3. **Chấp nhận lớp IFS là giới hạn đã biết, giao sandbox** — trái tiêu chí (1) khi sandbox chưa bắt buộc ở mọi quy mô.

## Quyết định

Lớp `_allowlist_why` (OR, sau luật cũ, trên lệnh gốc và mọi script lồng guard quét), lý do có `ADR-0065` và một dòng
`viết lại:`, mã `BUDGET` (mã của lệnh lồng bị chặn đi lên lệnh gốc):

| Lớp | Điều kiện chặn | ID |
|---|---|---|
| A — từ lệnh | từ lệnh (sau gán đầu lệnh, từ khoá, lệnh bọc guard biết; mọi từ ngay sau `{` trơn — `function f {`, `coproc f {`) có `$`/backtick, kể cả trong nháy; không tách chắc → chặn. Tên sau `command -v`/`-V` chỉ được tra (không chạy) — không phải từ lệnh | AUD-SEC-391 |
| B — tách/gán động | lệnh **kích hoạt** (chữ thô nhắc `IFS` mọi dạng chỉ-chữ-số; tên đích không nguyên văn — kể cả `unset`; nameref/`declare -u`; `${!…}`; đổi hoa từ dữ liệu; số học nhắc tên/mở rộng — cả toán hạng có nháy/thoát mà bash bỏ nháy rồi mới đánh giá: `[[ 'k' -eq 0 ]]`, `[[ $'\153' … ]]`, `[[ \k … ]]`, chỉ số `-v` ở `[[ ]]`/`test`/`[`; `source`/`.`; `mapfile -C`; giá trị cờ không nháy của read/mapfile/readarray/wait/unset/printf; thân `eval`/`trap`; thân heredoc không nháy) mà còn `$` không nằm trực tiếp trong nháy kép (không nháy, nháy đơn, trong `${…}`/`$(…)`, `\$` kể cả trong nháy kép) | AUD-SEC-388 |
| C — heredoc đọc lại | heredoc dấu kết không nháy có `$`/backtick mà lệnh có shell đọc stdin (cả fd tường minh `bash 0<<E`, `bash 2>/dev/null <<E`); trình thông dịch (perl/python/ruby/node…) cùng thân có dấu mở rộng lần hai (`\$`, backtick, `$` trong `$(…)`/`${…}`) | AUD-SEC-392, 401 |
| D — dữ liệu thành mã | `mapfile`/`readarray -C`, `${x@P}` (trên chữ bash còn mở rộng) — luôn chặn | AUD-SEC-388 |

Kèm hai sửa cùng PR: ống xét cả trên token còn nháy (`find docs \( -name STAGE.json \) | xargs rm` — AUD-SEC-393); miễn
trừ AUD-SEC-384 không áp khi xargs đọc đối số từ tệp, sed đọc chương trình từ tệp hay có lệnh ghi/chạy THẬT (`w`/`W`/`e`
ở vị trí lệnh, cờ `w`/`e` của `s` — đọc chương trình như GNU sed, chữ `w` trong mẫu/thay thế không tính; đọc không chắc →
không miễn); regex lệnh ghi của sed (đích trong vùng rào) nhận `w`/`W` dính liền tên tệp và sau xuống dòng
(AUD-SEC-396/398).

**Vì sao toán hạng có nháy cũng kích hoạt (review lượt 2):** `[[ … ]]` bỏ nháy toán hạng rồi mới đánh giá số học;
`-v` đánh giá chỉ số mảng. `read -r k < f; [[ 'k' -eq 0 ]]` (f chứa `IFS=4`) gán `IFS` như `[[ k -eq 0 ]]` — bản lượt 1
tìm tên trên chữ đã xoá nháy đơn nên lọt (đã chạy bash 5.2.21; `[ k -eq 0 ]`/`test` không đánh giá số học). Sửa theo
hướng của ADR này: mở rộng vùng đọc (chữ giữ nháy, chỉ bỏ comment), không thêm miễn trừ.

**Vì sao trigger B rộng hơn "lvalue có `$`" của D-322:** bash đánh giá số học ĐỆ QUY giá trị biến — `(( a ))` với `a`
đọc từ tệp trong `eval` (`a=ifs=47` qua `declare -u`) gán được `IFS` mà không lvalue nào có `$` (đã chạy bash 5.2.21). Vì
vậy mọi biểu thức số học nhắc tên/mở rộng đều kích hoạt (giữ D-321). **Vì sao `\$` trong nháy kép không được miễn:**
bản nháp đầu miễn vì "lớp lồng quét lại" (`sh -c "…\$c"`), nhưng `mapfile -C "git \$x #"` và `${y@P}` đọc lại chữ đó trong
shell này mà không lớp lồng nào quét — miễn theo cấu trúc là đúng loại suy luận ADR này bỏ.

## Hệ quả

- **Đo chặn oan** (lệnh Bash thật trong transcript phiên của máy — dữ liệu phiên, không đưa vào repo; cùng phép so của
  ADR-0063): 4 437 lệnh khác nhau, so `apply_policy(bash_decision(cmd, root))` với guard `main` (`4ad6451`). Bản nháp đầu
  đổi 59 lệnh cho qua → chặn; bản này thêm 5 (cùng lớp B: `\$` trong nháy kép khi lệnh nhắc `IFS` — câu hỏi
  `loop decide`, mẫu `grep` của chính phiên sửa guard). Mọi lệnh đổi đều là cho qua → chặn, không lệnh nào nới. Đo lại
  sau review lượt 2 (4 647 lệnh): so `main` (`89ffeb7`) 89 cho qua → chặn, so nhánh nền `4ad6451` 77, 0 lệnh nới; bản
  lượt 2 không đổi quyết định lệnh thật nào so lượt 1 (0/0). 38/89 là thay lệnh không nháy cùng số học nhắc tên
  (`n=$(…); sed -n "$((n-25)),…"`, `for i in $(seq …); do … $((i*2))`, `start=$(date +%s)` … `$((end-start))`) — chặn có
  chủ đích vì `n=$(printf 'IFS=4'); (( n ))` gán `IFS` (đã chạy), ghi ở AUD-SEC-397; viết lại `n="$(…)"`, `for ((…))`,
  `cmd | while read -r i`.
- **Đổi kỳ vọng có chủ ý** (test/fixture, không nới): 7 ca control D-270/ADR-0063 (`for ((i=0;i<3;i++)); do echo $i;
  done`, `x=$(( (a+b) * 2 )); echo $x`, `(( count++ )); echo $count`, `echo ${arr[$((i+1))]}` ×2, `echo "$(( $(wc -l <
  notes.txt) + 1 ))"`, `let 'x = 1 << 2'; echo $x`) và 7 ca og-388 (`while IFS= read -r f; do wc -l $f; done`,
  `IFS=$'\n'; for f in $(ls)`, `grep -c IFS $f`, `git log -S IFS … $(git ls-files)`, heredoc dữ liệu nhắc IFS cùng
  `ls $HOME`, `export $(grep -v '^#' .env | xargs)`, `while IFS=\| read -r a b; do echo $a`) cho qua → `BUDGET`; ba ca
  t405-338 (`python3 -c` gọi `bash -c` có brace `#`) đổi mã RULE_DENY → BUDGET; vòng review `adr-guard` thêm: `x='a'; echo
  ${x@P}`, `git commit -m "… \$IFS"`, `read -t $T -n 1 key; echo $key` cho qua → chặn.
- **Cách viết thay** (dòng `viết lại:` của lý do chặn): mở rộng trong nháy kép (`"$c"`, `"${a[@]}"`, `"$(…)"`, `"$i"`);
  tên lệnh nguyên văn (`git push …`, không `$PYTHON -m`/`"${cmd[@]}"` — dùng `python3 -m`); `.env` qua
  `set -a; . ./.env; set +a`; giá trị cờ trong nháy (`read -t "$T"`); thông điệp commit nhắc `$IFS` qua
  `git commit -F- <<'EOF'`; heredoc vào shell/trình thông dịch có nháy (`<<'EOF'`), dữ liệu truyền qua biến môi
  trường/đối số; thay `mapfile -C` bằng vòng `while IFS= read -r l`; số học trên kết quả lệnh qua biến trung gian
  (`a="$(wc -c < f)"; [ "$((a + b))" -le N ]`); mỏ neo `$` của regex trong nháy đơn khi lệnh nhắc `IFS` thay bằng
  `grep -x` hay `"${s% (#[0-9]*)}"`.
- **Cổng của chính repo:** ba lệnh `Kiểm` của `BLUEPRINT.md` (BASE-REPO-005/006, XC-DOCAI-006) bị bản nháp đầu chặn khi
  `blueprint-status --run` chạy qua guard (LOOP-STOP-027, exit 126) — viết lại theo các dạng trên, cùng kết quả (exit 0
  cả bản cũ lẫn mới trên repo; mẫu xấu `v3.1`, tổng 40 001 byte vẫn đỏ). `xt.yaml` `test_list`/`test_unit` có từ lệnh
  động `"${XT_PY:-python3}"` → shard CI (`dev-task.sh test-shard`) và `gate` exit 126 (review lượt 2 🔴) — viết lại
  `if [ "${XT_PY:-python3}" = python3 ]; then python3 …; elif [ "$XT_PY" = python3.11 ]; then python3.11 …; else exit 2; fi`;
  test `test_xt_yaml_commands_pass_repo_guard` khoá mọi lệnh `xt.yaml` qua guard của repo.
- **Còn mở (có từ trước, không thuộc lớp từ lệnh):** AUD-SEC-399 `git "${a[@]}"` sau `read -ra`/`mapfile` (đối số từ dữ
  liệu); AUD-SEC-400 `printf '…' > s.sh; bash s.sh` (guard không đọc tệp do chính lệnh ghi). Câu `viết lại:` của lớp C
  không còn gợi "ghi script ra tệp rồi chạy".
- **Dự án đích:** chặn mới ở các mẫu trên — chạy lại `install.py` để nhận guard mới; agent đọc dòng `viết lại:`. Lệnh
  cổng do harness chạy qua guard (`xt.yaml`, `— Kiểm:` của BLUEPRINT, Gate của PLAN — LOOP-STOP-027) mà từ lệnh động
  (`$PYTHON -m …`, `"$VENV/bin/x"`, `${PY:-python3} …`) sẽ exit 126 sau `install.py`: viết tên lệnh nguyên văn
  (`python3 -m …`, `.venv/bin/x`), chọn trình thông dịch bằng `if`/`elif` trên tên nguyên văn.

## Đường lùi

Revert PR của ADR này: `_allowlist_why` là một lời gọi OR cuối `_argv_shell_why`, gỡ nó trả về hành vi `main` (luật cũ của
AUD-SEC-388 lượt 2 vẫn còn). Lớp A–D độc lập nhau (mỗi lớp một hàm `_dyn_head_why`/`_reread_why`/`_split_why`/
`_here_shell_why`); chặn oan đo được đáng kể ở một lớp thì thu hẹp đúng lớp đó bằng ADR mới, không thêm miễn trừ theo cấu
trúc.
