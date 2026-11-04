# AUDIT-REPORT — X-Templates · 2026-11-04 (delta)

> Mốc quét `23447d817d2b` trên `main`, sau [PR #434](https://github.com/seeker19110/X-Templates/pull/434). Phiên chính rà sổ và chạy cổng. Hai lượt rà độc lập tập trung vào Git guard và workflow GitHub. Kết quả theo ID được theo dõi tại [sổ audit](AUDIT-STATUS.md).

## 1. Tóm tắt ở mốc quét

| Mức | Mở từ #434 | ID |
|---|---:|---|
| 🔴 | 2 | AUD-SEC-445, AUD-SEC-446 |
| 🟠 | 3 | AUD-SEC-442, AUD-SEC-443, AUD-SEC-447 |
| 🟢 | 1 | AUD-SEC-444 |

Lượt xác minh độc lập tái hiện cả năm mục 🔴/🟠 trong repo thử. Hai mục 🔴 chặn phát hành ở mốc quét vì Git có thể nạp hook hoặc alias từ cấu hình đã được ghi qua guard. Lượt rà CI còn xác nhận AUD-CI-030, job `gitleaks` có thể bỏ sót commit của PR dài. Các mục CI và tài liệu bổ sung nằm ở §5.

## 2. Phạm vi và tín hiệu

`audit plan` nhận diện repo khung với 563 tệp theo dõi, 61 tệp test và 11 workflow. Có 12 nhóm áp dụng. Nhóm DATA là N/A vì repo không có migration, SQL hay schema CSDL. Kế hoạch đánh dấu tám nhóm cần rà lại (`ARCH`, `SEC`, `CODE`, `TEST`, `CI`, `DOC`, `XFEAT`, `HAR`) cùng 68 bằng chứng hoặc miễn trừ Blueprint trỏ tệp đã đổi. Delta này tập trung vào Git guard, secret scan, workflow phát hành và hai mục Blueprint đã đối chiếu. Các nhóm và bằng chứng còn lại giữ trạng thái rà theo sổ hiện hành.

## 3. Lệnh đã chạy ở mốc quét

| Lệnh | Exit | Kết quả |
|---|---:|---|
| `python3 scripts/xt.py audit plan` | 0 | Phạm vi ở §2 |
| `python3 scripts/xt.py audit check docs/ops/AUDIT-STATUS.md --strict` | 1 | Sáu mục #434 còn mở |
| `python3 scripts/xt.py doctor` | 0 | Cảnh báo về sandbox |
| `python3 scripts/xt.py ci-check` | 0 | 11 workflow qua kiểm cấu hình của repo |
| `gitleaks git --redact --no-banner --log-opts=--all` (CLI 8.30.1) | 0 | 1.312 commit, 0 bí mật phát hiện |

Kết quả quét cục bộ áp dụng cho lịch sử đã tải ở mốc quét. `ci-check` kiểm cấu hình tĩnh. Các kiểm tra độc lập qua Semgrep, OSV Scanner, Bandit, actionlint và zizmor chưa có số đo trong lượt này. Kiểm tra trình duyệt và a11y nằm ngoài phạm vi delta.

## 4. Git guard

Các bước tái hiện dưới đây dùng Git 2.53.0, repo tạm và payload `PreToolUse` giả. Guard trả quyết định rỗng khi cho qua. Vị trí mã trỏ tới mốc quét.

### AUD-SEC-445 🔴 `--separate-git-dir` chuyển cấu hình Git ra ngoài hàng rào

- **Bằng chứng đo được.** Trong repo thử, `git init --separate-git-dir=<gitdir>` được cho qua. Git chuyển thư mục quản trị và để lại gitfile `.git`. Ghi `core.hooksPath = /dev/null` vào `<gitdir>/config` ở lượt sau cũng được cho qua. `git config --get core.hooksPath` trả `/dev/null`. Guard vẫn nhận diện đường dẫn theo mẫu `.git/` ở `.claude/hooks/guard.py:342, 8390–8398`.
- **Tái hiện.** Tạo repo tạm, gửi payload cho `git init --separate-git-dir=<gitdir>` rồi thực hiện trong scratch. Gửi payload tiếp theo cho lệnh ghi cấu hình hook vào `<gitdir>/config` và kiểm tra Git đọc giá trị mới qua gitfile.
- **Xác minh đối kháng.** Tái hiện được cả hai quyết định của guard trên mốc quét.

### AUD-SEC-446 🔴 Repo bare bên ngoài nạp cấu hình thực thi

- **Bằng chứng đo được.** `git init --bare <gitdir>`, ghi alias `!` vào `<gitdir>/config` và gọi `git -C <gitdir> <alias>` ở các lượt riêng đều qua guard. Lệnh Git thật chạy alias và tạo tệp đánh dấu trong scratch. Ca đối chiếu thêm với `git diff` trên repo bare có hai commit cũng chạy được chương trình `diff.external` đã ghi. Đường dẫn cấu hình repo bare không khớp mẫu `.git/` ở `.claude/hooks/guard.py:342`.
- **Tái hiện.** Tạo repo bare tạm rồi ghi một alias shell vô hại dùng để tạo tệp đánh dấu. Gửi lệnh gọi alias qua guard trước khi chạy Git và xác nhận tệp được tạo.
- **Xác minh đối kháng.** Tái hiện được quyết định cho qua và tác động của alias.

### AUD-SEC-442 🟠 Miễn `--exec-path` theo danh sách đường dẫn tĩnh

- **Bằng chứng đo được.** `_git_cfg_opts` miễn các giá trị trong `GIT_SYSTEM_EXEC_PATHS`, kể cả `/usr/local/libexec/git-core` khi đó không phải thư mục lệnh con của Git đang chạy (`.claude/hooks/guard.py:431–443`). Dạng cờ với đường dẫn tĩnh được cho qua trong khi dạng biến môi trường `GIT_EXEC_PATH` bị tính `BUDGET`.
- **Tái hiện.** So `git --exec-path` với đường dẫn trong danh sách miễn, rồi gửi một payload Bash có `git --exec-path=/usr/local/libexec/git-core status` và một payload có `GIT_EXEC_PATH=/usr/lib/git-core git status`. Nguy cơ thực thi phụ thuộc quyền ghi vào thư mục được miễn.
- **Xác minh đối kháng.** Tái hiện được chênh lệch quyết định của guard.

### AUD-SEC-443 🟠 Ghi gitfile qua Edit, Write và trình thông dịch được cho qua

- **Bằng chứng đo được.** Luật tên tệp `.git` ở `.claude/hooks/guard.py:8390–8392` nằm ở nhánh Bash nhận đích ghi. Nhánh Edit/Write và nhánh quét chuỗi của trình thông dịch dùng mẫu `.git/` cho các tệp bên trong thư mục (`.claude/hooks/guard.py:600–610, 11758–11779`).
- **Tái hiện.** Gửi payload Write và Edit cho `sub/.git` với nội dung gitfile `gitdir: <gitdir>`. Gửi tiếp payload Bash có `python3 -c "open('sub/.git', 'w').write(...)"` với chuỗi đích nguyên văn. Cả ba payload được cho qua.
- **Xác minh đối kháng.** Tái hiện được các đường ghi nêu trên.

### AUD-SEC-447 🟠 Hard link tới hook giữ tên ngoài vùng bảo vệ

- **Bằng chứng đo được.** `_git_config_inodes` thu thập inode của cấu hình nhưng thiếu các tệp hook (`.claude/hooks/guard.py:577–597`). Đích ghi qua hard link ở ngoài `.git/hooks/` được cho qua.
- **Tái hiện.** Trong repo tạm, tạo hook `pre-commit` và dùng `ln .git/hooks/pre-commit hk` ở lượt đầu. Gửi lệnh chuyển hướng ghi `hk` ở lượt sau, rồi thử riêng Edit và Python ghi cùng đường dẫn. Cả ba được cho qua. Hai đường dẫn có cùng thiết bị và inode nên ghi qua `hk` thay nội dung hook.
- **Xác minh đối kháng.** Tái hiện được đường ghi qua hard link.

## 5. CI và tài liệu

- **AUD-CI-030 🟠 Secret scan bỏ sót commit của PR dài.** Workflow khai báo quét toàn bộ lịch sử nhưng action đang ghim chỉ gọi API danh sách commit của PR một lần. API trả mặc định 30 mục mỗi trang. Action lấy SHA đầu và cuối của trang để tạo phạm vi quét. Trong repo thử có 31 commit sau commit nền, mẫu thử chỉ xuất hiện ở commit cuối. Quét phạm vi tương đương action dừng ở commit 30 và exit 0. Quét toàn lịch sử bằng CLI exit 2 với đúng một kết quả từ mẫu thử. Checkout dùng `fetch-depth: 0` vẫn không mở rộng được phạm vi do action truyền cho CLI. Bước sửa giữ tên job `gitleaks` của ruleset và quét lịch sử từ checkout bằng CLI ghim phiên bản và checksum. [Workflow ở mốc quét](https://github.com/seeker19110/X-Templates/blob/23447d817d2bc8cf68093591177f85fd72a8a2f6/.github/workflows/secret-scan.yml#L24-L35) · [Mã nguồn action đã ghim](https://github.com/gitleaks/gitleaks-action/blob/e0c47f4f8be36e29cdc102c57e68cb5cbf0e8d1e/src/gitleaks.js#L151-L173) · [API danh sách commit của PR](https://docs.github.com/en/rest/pulls/pulls#list-commits-on-a-pull-request)
- **🟢 Hai bằng chứng Blueprint đã cũ.** `BASE-DEP-003` ghi `.python-version` là 3.13 trong khi tệp đã là 3.14. `BASE-SEC-006` ghi 10 workflow trong khi `git ls-files '.github/workflows/*.yml'` trả 11 tệp. [Blueprint ở mốc quét](https://github.com/seeker19110/X-Templates/blob/23447d817d2bc8cf68093591177f85fd72a8a2f6/BLUEPRINT.md)
- **🟢 Cần giữ đúng tệp nguồn phát hành đã ký.** `release-tag.yml` ký digest của `.tar.gz` trong `$RUNNER_TEMP` rồi chỉ đẩy tag. Hướng dẫn xác minh hiện yêu cầu người dùng tự dựng lại archive. Dựng archive `v3.29.0` hai lần với cùng prefix và chỉ đổi `tar.tar.gz.command` sang `gzip -cn` cho hai SHA-256 khác nhau (`7844cf1042f2…` và `1983bd6827e5…`). Người dùng cần lấy đúng byte đã ký để xác minh digest. [Workflow phát hành ở mốc quét](https://github.com/seeker19110/X-Templates/blob/23447d817d2bc8cf68093591177f85fd72a8a2f6/.github/workflows/release-tag.yml#L59-L78)

## 6. Kế hoạch sửa

| Đợt | Phát hiện | Thay đổi và kiểm tra |
|---|---|---|
| Git guard · D-340 | AUD-SEC-442/443/445/446/447 | Giới hạn nguồn cấu hình Git ở đầu đọc và bảo vệ gitfile, cấu hình Git và hook ở đầu ghi. Chạy test hồi quy có đối chứng, `scripts/dev-task.sh gate` và kiểm sổ strict. |
| Secret scan | AUD-CI-030 và bằng chứng Blueprint đã cũ | Giữ required check `gitleaks`, ghim CLI và checksum trong workflow repo và mẫu cài đặt, kiểm tra phạm vi lịch sử và cập nhật bằng chứng Blueprint theo cấu hình thật. |

## 7. Nợ 🟢

| Mục | Chủ | Hạn hoặc mốc rà lại |
|---|---|---|
| AUD-SEC-444 · ghi nhận ngoại lệ và các ca Git hợp lệ bị chặn oan | Phiên chính | 2027-01-21 theo [sổ audit](AUDIT-STATUS.md) |
| Lưu tệp gzip khớp digest provenance | Chủ workflow phát hành | Trước lần phát hành cần kiểm chứng provenance từ tệp tải về |
