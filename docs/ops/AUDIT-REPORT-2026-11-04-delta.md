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

Kết quả quét cục bộ áp dụng cho lịch sử đã tải ở mốc quét. `ci-check` kiểm cấu hình tĩnh. Semgrep, OSV Scanner, Bandit và actionlint chưa chạy trong lượt này. Kiểm tra trình duyệt và a11y nằm ngoài phạm vi delta.

## 4. Git guard

Lượt xác minh độc lập tái hiện cả năm mục bằng Git 2.53.0, repo tạm và payload `PreToolUse` giả. Quyết định rỗng nghĩa là guard cho qua. Vị trí mã ở mốc quét.

### AUD-SEC-445 🔴 Git dir tách riêng

`git init --separate-git-dir=<gitdir>` qua guard, dời metadata và để lại gitfile `.git`. Payload tiếp theo ghi `core.hooksPath = /dev/null` vào `<gitdir>/config` cũng qua. Git đọc lại `/dev/null` bằng `git config --get core.hooksPath`. Mẫu bảo vệ chỉ thấy đuôi `.git/` ở `.claude/hooks/guard.py:342, 8390–8398`.

### AUD-SEC-446 🔴 Cấu hình thực thi của repo bare

Ba lượt `git init --bare <gitdir>`, ghi alias `!` vào `<gitdir>/config` và `git -C <gitdir> <alias>` đều qua guard. Alias thật tạo tệp đánh dấu trong scratch. Với repo bare có hai commit, `git diff` cũng chạy được `diff.external` đã ghi. Đường dẫn cấu hình không khớp mẫu `.git/` ở `.claude/hooks/guard.py:342`.

### AUD-SEC-442 🟠 Danh sách miễn `--exec-path` tĩnh

`git --exec-path=/usr/local/libexec/git-core status` qua guard dù đường dẫn đó khác kết quả `git --exec-path`. `GIT_EXEC_PATH=/usr/lib/git-core git status` trả `BUDGET`. Nguy cơ thực thi phụ thuộc quyền ghi vào đường dẫn được miễn trong `_git_cfg_opts` ở `.claude/hooks/guard.py:431–443`.

### AUD-SEC-443 🟠 Ghi gitfile qua Edit, Write và trình thông dịch

Payload Edit và Write ghi `gitdir: <gitdir>` vào `sub/.git` được cho qua. `python3 -c "open('sub/.git', 'w').write(...)"` cũng qua. Bash xét tên tệp `.git`, còn Edit/Write và trình thông dịch chỉ xét mẫu `.git/` ở `.claude/hooks/guard.py:600–610, 8390–8392, 11758–11779`.

### AUD-SEC-447 🟠 Hard link tới hook

Trong repo tạm, `ln .git/hooks/pre-commit hk` tạo hai đường dẫn cùng thiết bị và inode. Chuyển hướng Bash, Edit và Python ghi `hk` đều qua guard và có thể đổi nội dung hook. `_git_config_inodes` chỉ thu thập inode cấu hình ở `.claude/hooks/guard.py:577–597`.

## 5. CI và tài liệu

- **AUD-CI-030 🟠 Secret scan bỏ sót commit của PR dài.** Workflow khai báo quét toàn bộ lịch sử nhưng action đang ghim chỉ gọi API danh sách commit của PR một lần. API trả mặc định 30 mục mỗi trang. Action lấy SHA đầu và cuối của trang để tạo phạm vi quét. Trong repo thử có 31 commit sau commit nền, mẫu thử chỉ xuất hiện ở commit cuối. Quét phạm vi tương đương action dừng ở commit 30 và exit 0. Quét toàn lịch sử bằng CLI exit 2 với đúng một kết quả từ mẫu thử. Checkout dùng `fetch-depth: 0` vẫn không mở rộng được phạm vi do action truyền cho CLI. Bước sửa giữ tên job `gitleaks` của ruleset và quét lịch sử từ checkout bằng CLI ghim phiên bản và checksum. [Workflow ở mốc quét](https://github.com/seeker19110/X-Templates/blob/23447d817d2bc8cf68093591177f85fd72a8a2f6/.github/workflows/secret-scan.yml#L24-L35) · [Mã nguồn action đã ghim](https://github.com/gitleaks/gitleaks-action/blob/e0c47f4f8be36e29cdc102c57e68cb5cbf0e8d1e/src/gitleaks.js#L151-L173) · [API danh sách commit của PR](https://docs.github.com/en/rest/pulls/pulls#list-commits-on-a-pull-request)
- **🟢 Hai bằng chứng Blueprint đã cũ.** `BASE-DEP-003` ghi `.python-version` là 3.13 trong khi tệp đã là 3.14. `BASE-SEC-006` ghi 10 workflow trong khi `git ls-files '.github/workflows/*.yml'` trả 11 tệp. [Blueprint ở mốc quét](https://github.com/seeker19110/X-Templates/blob/23447d817d2bc8cf68093591177f85fd72a8a2f6/BLUEPRINT.md)
- **🟢 Cần giữ đúng tệp nguồn phát hành đã ký.** `release-tag.yml` ký digest của `.tar.gz` trong `$RUNNER_TEMP` rồi chỉ đẩy tag. Hướng dẫn xác minh hiện yêu cầu người dùng tự dựng lại archive. Dựng archive `v3.29.0` hai lần với cùng prefix và chỉ đổi `tar.tar.gz.command` sang `gzip -cn` cho hai SHA-256 khác nhau (`7844cf1042f2…` và `1983bd6827e5…`). Người dùng cần lấy đúng byte đã ký để xác minh digest. [Workflow phát hành ở mốc quét](https://github.com/seeker19110/X-Templates/blob/23447d817d2bc8cf68093591177f85fd72a8a2f6/.github/workflows/release-tag.yml#L59-L78)

## 6. Kế hoạch sửa

| Đợt | Phát hiện | Thay đổi và kiểm tra |
|---|---|---|
| Git guard · D-340 | AUD-SEC-442…447 | Giới hạn nguồn cấu hình Git ở đầu đọc và bảo vệ gitfile, cấu hình Git và hook ở đầu ghi. Chạy test hồi quy có đối chứng, `scripts/dev-task.sh gate` và kiểm sổ strict. |
| Secret scan | AUD-CI-030 và bằng chứng Blueprint đã cũ | Giữ required check `gitleaks`, ghim CLI và checksum trong workflow repo và mẫu cài đặt, kiểm tra phạm vi lịch sử và cập nhật bằng chứng Blueprint theo cấu hình thật. |

## 7. Nợ 🟢

| Mục | Chủ | Hạn hoặc mốc rà lại |
|---|---|---|
| AUD-DOC-244 · lưu tệp gzip khớp digest provenance | Chủ workflow phát hành | Trước lần phát hành cần kiểm chứng provenance từ tệp tải về |
| AUD-CODE-047 · theo dõi dấu nháy thoát khi đọc scalar YAML | Chủ `dev-task.sh` và `xt.py` | Rà lần tới theo [sổ audit](AUDIT-STATUS.md) |

## 8. Kiểm lại thay đổi

- `pip-audit 2.10.1 --require-hashes --strict --disable-pip` trên ba lockfile `requirements-*.txt` exit 0, không có lỗ hổng đã biết.

- Git guard có test cho `--exec-path=` rỗng, ghi qua symlink tới gitfile, ghi hook qua hard link ở linked worktree, repo trần được Git dò từ thư mục con, và tạo repo trần rồi ghi cấu hình trong cùng lệnh Bash. Test đối chứng giữ các lệnh đọc và ghi file thường.
- Chạy đúng bước Bash trong workflow mới với tarball Gitleaks 8.30.1 từ nhà phát hành. SHA-256 khớp, quét 1.405 commit ở các ref cục bộ, 0 phát hiện, exit 0. Hai mẫu thử ở commit PR thứ 31 và ở diff merge đều làm job quét exit 1. SARIF che nội dung mẫu thử.
- `python3 -m unittest -q tests.test_ci tests.test_ci_template` exit 0 (73 test). `zizmor --offline --persona regular --min-severity high` exit 0 cho workflow đổi.
- AUD-SEC-444 chỉnh quy tắc dựa trên tham số gốc và nơi Git chạy. Guard vẫn yêu cầu dùng đường dẫn Git nguyên văn trong phạm vi được nhận diện. Tên Git dir dựng ở runtime và giới hạn sandbox được theo dõi theo ADR-0067.
