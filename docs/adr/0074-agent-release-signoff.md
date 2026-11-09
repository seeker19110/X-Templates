# ADR-0074: Agent ký §5 GO-NO-GO khi `xt.yaml` khai `release_signoff: agent`

- **Trạng thái:** Đã chấp nhận 2026-11-08 — chủ repo quyết trong phiên nghiên cứu tự động hoá: "cho agent ký GO-NO-GO";
  phiên chính chốt cách làm theo tiêu chí chất lượng cuối (ADR-0008) — **D-401**.
- **Trạng thái triển khai:** đã làm cùng PR: `scripts/xt.py` (`release_agent_signoff`, `release_sign`, lệnh
  `release-sign`, `promotion.by`, `release_signoff` vào `HARD_GATED_KEYS`), `.claude/hooks/guard.py`
  (`agent_release_signoff`, `_release_sign_form`, `_release_sign_denied` → `GO_SIGN`; sau phản biện: chặn gọi
  `release_sign` trong tiến trình, đổi nhánh mặc định, tool MCP ghi thẳng `main`), `tests/test_release_signoff.py`, mẫu
  `framework/templates/xt.yaml` (khoá để trống). `xt.yaml` của repo khung chỉ ghi khoá dạng chú thích — **bật ở PR riêng
  sau khi mã này lên `main`** (D-402).
- **Ngày:** 2026-11-08.
- **Thay một phần:** ADR-0068 §Quyết định 3a ("đã duyệt" vẫn là chữ ký người) — chỉ khi khoá có hiệu lực. **Giữ:** guard
  `GO_SIGN` chặn mọi đường ghi dòng ký khác (Edit/Write/Bash/MCP), dòng `subject:` gắn ứng viên (D-389), hạn
  `release_approval_days`, lời từ chối NO-GO đọc cả văn bản thô.
- **Liên quan:** ADR-0008, ADR-0058 (bốn việc: GO của máy · nghiệm thu · quyền deploy · đã deploy), ADR-0069 (mẫu khoá
  `stage_approval`), ADR-0020/0022 (khoá chỉ người đổi), nghiên cứu
  [`research/2026-11-08-full-automation.md`](../../research/2026-11-08-full-automation.md).

## Bối cảnh

Chữ ký §5 là việc người duy nhất còn đứng giữa "máy đạt" và `promotion: approved`. Đo 2026-11-08: từ lúc cắt 3.30.0 tới chữ
ký đầu tiên (3.32.0, #476) là 62 giờ không có bản nào `approved`; năm bản 3.29.0–3.31.1 không bao giờ được ký; một ngày có
sáu PR chỉ phục vụ luật dòng ký. Chủ repo quyết cho agent ký. Câu hỏi còn lại: ký thế nào để không mất tính trung thực (P1)
và không để phiên tự cấp quyền cho mình.

## Yếu tố quyết định

1. Đúng và an toàn: agent chỉ ký khi máy đã đạt mọi hàng BLOCKER; dòng ký nói thật ai ký (không mạo danh người); quyền đến
   từ cấu hình đã commit ở nhánh chính.
2. Đường lùi một dòng.
3. Dùng lại cơ chế sẵn có (`_main_key_is` như ADR-0069, `_subject_problem`, `_approval_problem`, `GO_SIGN`).

## Các phương án đã cân nhắc

1. **Khoá `release_signoff: agent` + lệnh `release-sign` có điều kiện máy** (chọn).
2. Bỏ luật `GO_SIGN`, agent sửa §5 bằng Edit như người.
3. Như 1 nhưng mẫu dự án đích bật sẵn `agent`.

## Quyết định

Chọn **phương án 1** (D-401).

- **Khoá** `release_signoff: agent` có hiệu lực khi xt.yaml ở cây làm việc **và** bản đã commit ở `origin/main` (→
  `origin/master`) đều khai; nằm trong `HARD_GATED_KEYS` nên PR đổi khoá luôn người merge.
- **`xt.py release-sign --note … [--file …]`** chạy `release-check` với blueprint và sổ audit ở **đường mặc định** (không
  nhận đường khác — làm giả được) và `--unchecked-must fail` (MUST tick không `— Kiểm:` chặn ký), rồi chỉ ký khi: không
  hàng BLOCKER nào FAIL (gồm cây sạch, sổ audit, nợ review); `promotion` không `rejected` (người đã NO-GO ở một GO-NO-GO
  khác của `VERSION` — agent không ký đè); việc người còn lại chỉ là `go_no_go`; `BLUEPRINT.md` khai `scale: S` (M/L có
  GO-NO-GO dòng 20 BLOCKER — người dùng thử thật); không còn việc `loop defer`; GO-NO-GO của `VERSION` chưa có dòng ký
  hay lời từ chối; **lịch sử git** (bản mirror mới của `origin` và repo cục bộ) không còn lời từ chối của người có
  hiệu lực (D-404, D-406); dòng `subject:` khớp ứng viên.
  Dòng ghi: `| Agent (`release_signoff`, ADR-0074) | agent | GO | <ngày UTC> |` cùng một dòng
  giải trình dưới bảng. Ghi xong đọc lại; dòng không hiện hoặc chưa đủ cho `promotion` thì trả file như cũ.
- **Lời từ chối trong lịch sử** (D-404, thay quét nhánh chính theo `VERSION` — vỡ khi NO-GO chỉ ở nhánh PR, dự án ở
  thư mục con, đổi `VERSION`, dòng thiếu ngày). **Neo tin cậy ở remote** (D-406 — quét lịch sử cục bộ lách được bằng
  lệnh guard cho qua: `merge -s ours`, `fetch --depth=1`, `branch -rd`/`filter-branch`, `push --delete` nhánh đã có PR, fetch repo
  ngoài, `log.showRoot false`): mỗi lần ký, `release-sign` clone `--mirror` mới của `origin` (URL thô ở `.git/config`;
  mọi ref, kể cả `refs/pull/*/head` GitHub giữ) vào thư mục tạm, rồi một lệnh `git log --all --full-history -p` ở
  mirror và ở repo cục bộ đọc dòng **thêm** của mọi tệp `GO-NO-GO*.md` (mọi thư mục/độ sâu từ gốc repo, không phân biệt
  hoa thường, mọi phiên bản). Môi trường git cô lập: bỏ `GIT_*` (trừ CA truyền tải; `GIT_ASKPASS` không giữ), không cấu hình
  global/system, `-c` ghim `log.showRoot`/`log.follow`/`core.commitGraph`…, không grafts/replace.
  Lời từ chối = HỢP hai nguồn (cục bộ bắt NO-GO chưa đẩy): dòng thân bảng có cột tiêu đề `Quyết định`/`Decision` (so
  không dấu; bảng không có cột đó không đọc theo vị trí, kể cả sau `## 5`), ô quyết định không rỗng không phải GO và ô
  tên của người (không rỗng/placeholder, khác `agent`; tên trống chỉ tính khi ô ghi NO-GO rõ — dòng mẫu không tính);
  ngày không xét. GO = ô bắt đầu bằng `GO` rồi hết chuỗi hay ký tự không phải chữ/số sau khi bỏ `*`/`_`/`` ` ``
  (`**GO**; D-126…`, `GO — ok`), không chứa NO-GO/`Không GO`. Mỗi lời từ chối tính ở lần thêm **mới nhất**. Hết hiệu
  lực **chỉ** khi một commit có ngày commit sau nó, **trên mirror**, thêm **lần đầu** một dòng ký GO của người ở §5 (tên
  + `YYYY-MM-DD`, dạng guard `GO_SIGN` chặn agent ghi) ở tệp cùng phiên bản `vX.Y.Z` hay cao hơn (tên tệp, không có thì
  tiêu đề `# `); lời từ chối không xác định phiên bản chỉ gỡ bằng GO cùng tệp. Không hết hạn theo tuổi (D-405): hạn
  `release_approval_days` đọc xt.yaml cây — agent đặt `1` là mọi NO-GO cũ hết hiệu lực. Không có `origin`, clone lỗi
  (offline, xác thực), repo cục bộ hay mirror nông, `git log` lỗi → không ký; repo chưa có commit → không có lời từ
  chối. Giới hạn còn lại: guard `GO_SIGN` lọt tên tệp dựng lúc chạy (dòng GO giả tên người) — ranh giới thật là
  sandbox; dòng chỉ thêm khi giải xung đột merge không thấy (`git log -p` không in diff merge); remote mà agent viết lại
  được lịch sử (force-push không bị chặn) thì neo không giữ. Xoá nhánh/tag remote khác nhánh hiện tại của phiên và
  viết lại mọi ref (`filter-branch --all`, `filter-repo`) guard chặn (`REMOTE_DELETE`, AUD-SEC-551, D-407; cả cờ gộp
  chữ số `push -4d|-4f` và `gh pr close --delete-branch`, AUD-SEC-556…558) — còn lọt: đổi sang nhánh của người khác
  rồi xoá nó (`harness-files.md`). **Khoá** đọc thêm ở xt.yaml của dự án tại nhánh mặc
  định (HEAD) của CHÍNH bản mirror vừa clone (AUD-SEC-552) — `origin/main` cục bộ chưa fetch không giữ được khoá đã tắt
  trên remote; clone mang riêng credential helper global của người dùng (`credential.helper`, `credential.<url>.helper`),
  mọi cấu hình khác vẫn cô lập (AUD-SEC-553). Helper đọc từ cấu hình global THẬT (`$HOME/.gitconfig`, không có thì
  `$HOME/.config/git/config`; bỏ `GIT_*`/`XDG_CONFIG_HOME` agent export được — AUD-SEC-559) và chạy trong thư mục tạm
  của clone (thấy mirror): helper agent ghi vào tệp thật bằng tên dựng lúc chạy hay `HOME` agent đặt — ranh giới còn
  lại là sandbox.
- **`promotion.by`** liệt kê ô tên đã ký — người đọc phân biệt được bản do agent ký. Dòng ký ô tên `agent` chỉ là duyệt
  khi khoá có hiệu lực; khoá tắt → `pending_human` (tắt khoá thu hồi luôn chữ ký agent chưa phát hành).
- **Guard** chỉ cho `[python3] <xt.py của dự án> release-sign` là **một lệnh đơn chữ rõ** chỉ với `--file`/`--note`,
  khi khoá có hiệu lực; mọi dạng khác → `GO_SIGN`. `XT_GUARD_POLICY=strict` không nới. Script Python nạp `xt` kèm tên
  chứa `sign`/`release` bị chặn như AUD-SEC-498 (vá biến/hàm trong tiến trình). Đổi nhánh mặc định
  (`gh repo edit --default-branch`, `PATCH default_branch=`) bị chặn như huỷ — nó dời ruleset `~DEFAULT_BRANCH` khỏi `main`;
  tool MCP ghi file thành commit lên `main`/`master` hay không nêu nhánh bị chặn như `push` thẳng nhánh chính.
- **Repo khung**: bật `agent` ở **PR riêng** sau khi mã này lên `main` (D-402) — PR mồi vừa thêm khoá vào
  `HARD_GATED_KEYS` vừa bật khoá thì steward (chạy `xt.py` của `main`, chưa biết khoá) có thể tự merge. **Mẫu dự án
  đích** để trống (người ký): dự án đích có thể có người dùng thật, DPIA hay người ký pháp lý — bật là quyết định của
  từng chủ dự án.

### Hệ quả

- Tốt: hết điểm chờ người cuối ở G7 cho repo khung; vòng `/complete` đi liền tới `approved`; chữ ký nói thật người ký.
- Xấu / đánh đổi: GO sản xuất có thể không người nào xem bản ứng viên (dòng 20 GO-NO-GO, "người đã dùng thử", không có
  máy kiểm) — chủ repo chấp nhận cho repo khung; vì vậy agent chỉ ký quy mô S. GitHub không phân biệt người với agent
  dùng chung tài khoản (ADR-0058), nên ranh giới là khoá đã commit và guard, không phải danh tính: ruleset đòi 0 approval,
  "người merge PR khoá" do guard (merge PR `hard` bị chặn) và steward giữ, không do máy chủ GitHub. Mọi rào ở đây là lớp
  chặn nhầm (D-015), không phải ranh giới cách ly: script trên đĩa nạp `xt` theo tên dựng lúc chạy vẫn là giới hạn của
  guard (`harness-files.md` §Giới hạn). `promotion` không kiểm tên người ký — dòng ký mang tên người chỉ được bảo vệ bởi
  `GO_SIGN`.
- Chưa làm: `loop next-step` vẫn trả `signoff-package`; skill `/complete` chỉ ra bước `release-sign`. Điều kiện "14 ngày
  không revert/🔴 lọt" của giám khảo chờ số đo (`waits`/`escaped`, lộ trình nghiên cứu S6).

### Xác nhận

- `python3 -m unittest tests.test_release_signoff`: khoá cần cả cây lẫn nhánh chính; từ chối khi FAIL, còn việc người
  khác, quy mô khác S, còn `loop defer`, ghi chú rỗng, subject lệch, đã ký, §5 sai dạng, `promotion` rejected, lời từ
  chối trong lịch sử (D-404: xoá ở nhánh PR/đã lên `main`, thư mục con `apps/web`, ô `Không GO`, đổi `VERSION`, dòng
  thiếu ngày/tên; GO người sau đó thì ký được; cũ 400 ngày hay `release_approval_days: 1` vẫn chặn — D-405; D-406:
  `merge -s ours`, `fetch --depth=1`, `branch -rd`, `push --delete` còn `refs/pull/*`, GO của repo ngoài, GO phiên bản
  thấp hơn, `log.showRoot false`, `insteadOf` tiêm qua env đều vẫn chặn; GO viết tự do và bảng §6 không chặn oan; không
  `origin`/clone lỗi → không ký; mẫu khung không tạo lời từ chối), lịch sử không đọc được, MUST
  không lệnh kiểm (với `release-check` thật); repo khung qua GitHub thật: clone mirror ~2,4 s, quét hai repo ~0,3 s; ký thành
  công ra `promotion.by = ["agent"]`, dòng `agent` khi khoá tắt → `pending_human`; guard cho dạng chữ rõ, chặn dạng nối lệnh, `env -u`, token mờ, `--status`/`--blueprint`,
  tuỳ chọn lạ, xt.py ngoài dự án, strict, gọi trong tiến trình, đổi nhánh mặc định, MCP ghi thẳng `main`.
- Phản biện đối kháng 3/3 bác bản đầu (nghiên cứu §8); bản này sửa đủ các lỗ đã nêu.
- Mốc xét lại: 2027-01-21 (cùng LOOP-DESIGN-014) hoặc khi một bản agent ký bị revert vì lỗi người xem được.

## Ưu / nhược từng phương án

### 1. Khoá + lệnh có điều kiện (chọn)
- Tốt: điều kiện do máy kiểm; dòng ký ghi `agent`; opt-in theo dự án; đường lùi một dòng.
- Xấu: thêm một khoá và một nhánh guard phải đồng bộ với `xt.py`.

### 2. Bỏ `GO_SIGN`
- Tốt: ít mã nhất.
- Xấu: agent ký được khi máy chưa đạt; ghi được tên người; mất lớp chặn nhầm cho mọi dự án.

### 3. Mẫu dự án đích bật sẵn
- Tốt: nhanh nhất cho dự án mới.
- Xấu: dự án có người dùng thật hay nghĩa vụ ký pháp lý nhận chữ ký máy mà không ai quyết.
