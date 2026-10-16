# Changelog

Định dạng theo [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/); phiên bản theo [SemVer 2.0.0](https://semver.org/lang/vi/).
Thay đổi **mục checklist** (thêm ID, đổi mức, ngừng dùng) ghi rõ ID để dự án đích ghép lại blueprint theo ID.

## [Unreleased]

### Changed
- CI: workflow `portability.yml` (job `macos-bash32`, bash 3.2/BSD) bỏ trigger `pull_request`, chỉ chạy khi push vào `main` —
  PR không còn chờ runner macOS; job không phải required check nên ruleset không đổi.
- **Autopilot chạy một phiên đến khi xong** (ADR-0009). Context đầy → compaction có checkpoint, không bàn giao; bàn giao
  chỉ khi ≥ 80% trần vòng/giờ/tiền. Việc cần người không chặn cả vòng (`loop defer`), gom cuối phiên. Mục checklist:
  `LOOP-CTX-003` → `MAY` Ngừng dùng, thay bằng **`LOOP-CTX-017`** (MUST, mới); `LOOP-CTX-008` → `MAY`, thay bằng
  **`LOOP-CTX-018`** (SHOULD); `LOOP-CTX-012` → `MAY`, thay bằng **`LOOP-CTX-019`** (SHOULD: vượt ngân sách thì thu hẹp phạm vi
  bằng `D-NNN`, không chia phiên); mới **`LOOP-CTX-020`** (SHOULD, chế độ quyền không hỏi), **`LOOP-STOP-021`** (SHOULD,
  `loop defer`); `LOOP-CTX-009` nơi ghi checkpoint đổi từ PROGRESS sang `.autopilot/state.json` + thêm *Kiểm* (ID, mức giữ).
  `loop status` khi vòng đã kết thúc báo verdict cuối thay vì "chưa bật". Skill `/autopilot` có bước 0 (chế độ quyền, hook);
  `AGENTS.md`, mẫu `AGENTS.md`/`CLAUDE.md`/`PLAN.md`, giao thức `11-autonomous-loop/README.md`, skill `/handover` theo luật mới.
  Dự án đích: chạy lại `install.py` (`merge_hooks` thêm `PreCompact`; AGENTS.md/skill copy-if-absent → gộp tay `*.xtemplates-new`).
- **Phiên chính tự duyệt điểm quyết định theo tiêu chí chất lượng cuối; mặc định tự host** (ADR-0008, repo khung + dự án
  đích). Tách *điểm quyết định chuyên môn* (duyệt PLAN, spec hở/nhiều cách hiểu/mâu thuẫn, chọn công nghệ/thiết kế, bảo
  mật/pháp lý mơ hồ) khỏi *điểm dừng về hành động* (giữ nguyên, thêm đăng ký dịch vụ trả phí/nhập khoá thật). Tiêu chí theo
  thứ tự: đúng & an toàn · giữ đường lùi · bền lâu · trải nghiệm cuối · tốc độ/chi phí chỉ phá hoà. Phương án cần tài
  khoản/khoá/thông tin chỉ chủ dự án có → tự host, đề xuất dịch vụ khi chạy thật ghi `--prod`, quyết ở G7. Mục checklist:
  `LOOP-STOP-004` → `MAY` Ngừng dùng, thay bằng **`LOOP-STOP-018`** (MUST@L, mới); `PM-SPEC-007` → `MAY` Ngừng dùng, thay
  bằng **`PM-SPEC-020`** (MUST, mới: spec hở → câu hỏi mở + `D-NNN`, không lấp ngầm); `WF-SDD-004` → `MAY` gộp vào
  `PM-SPEC-020`; `PM-REQ-008` → `MAY` Ngừng dùng, thay bằng **`PM-REQ-019`** (MUST, mới); mới **`LOOP-STOP-019`** (SHOULD,
  báo cáo liệt kê D-NNN), **`LOOP-STOP-020`** (SHOULD, mặc định tự host); `PM-REQ-013` chấp nhận `D-NNN` thay chữ ký người
  (ID, mức giữ). `AGENTS.md` repo khung: §4 mới (điểm quyết định), §5 điểm dừng về hành động, các mục sau +1; mẫu
  `templates/AGENTS.md` §5–6 tương tự; `templates/GO-NO-GO.md` mục 18 BLOCKER: mọi đề xuất "Khi chạy thật" đã được chủ dự án
  quyết; `templates/PLAN.md`/`SPEC.md`/`PROJECT.md`, skill `/autopilot`, subagent `executor` theo luật mới. Dự án đích: chạy lại
  `install.py` (AGENTS.md/skill copy-if-absent → gộp tay bản `*.xtemplates-new`) và `compose --out BLUEPRINT.md`.
- CI: trigger `pull_request` thêm loại `edited` (cùng `opened`, `synchronize`, `reopened`) để sửa tiêu đề PR là chạy lại bước kiểm tiêu đề Conventional Commits ≤ 72 ký tự. Trước đây payload chụp tiêu đề lúc push và re-run dùng lại payload cũ, nên tiêu đề đã sửa vẫn đỏ cho tới commit kế tiếp.
- **Phá vỡ (bản kế tiếp 3.0.0)** — định danh kỹ thuật theo tên X-Templates, thay ADR-0006 bằng ADR-0007:
  `.xstored/` → `.xtemplates/`, `scripts/xs.py` → `scripts/xt.py`, `xs.yaml` → `xt.yaml`, `XS_*` → `XT_*`
  (`XT_ROOT`, `XT_DEBUG`, `XT_FRAMEWORK`, `XT_FRAMEWORK_LINK`, `XT_PROGRESS_BASE`, `XT_RECORD_TIMEOUT`),
  `*.xstored-new` → `*.xtemplates-new`; test `tests/test_xs*.py` → `tests/test_xt*.py`. Dự án đã cài: chạy lại `install.py`
  từ bản mới — tự chép manifest hash, xoá `.xstored/`, đổi `xs.yaml` → `xt.yaml`, liệt kê file người dùng còn nhắc tên cũ
  (`*.md` gốc, `.claude/`, `.github/workflows/`) để sửa tay. Phần *Kiểm* của các mục nhắc `xs.py`/`.xstored` đổi theo
  (ID, mức giữ nguyên). Tài liệu lịch sử (`research/`, báo cáo audit đã ký, ADR-0001…0006, mục CHANGELOG cũ) giữ tên cũ.
- Đổi tên repo `seeker19110/X-stored` → `seeker19110/X-Templates` (GitHub chuyển hướng 301 từ tên cũ): cập nhật tên khung,
  URL clone trong README + bước CI chạy lệnh README, docstring/`--help` của `install.py`/`xs.py`, harness `.claude/`, mẫu dự án đích.
  Giữ nguyên để không phá dự án đã cài: thư mục `.xstored/`, `xs.py`, `xs.yaml`, biến `XS_*`, đuôi `.xstored-new`; giữ tên cũ
  ở tài liệu lịch sử (`research/`, báo cáo audit đã ký, trích dẫn "khung cũ X-stored") — ADR-0006.
- `LOOP-HARNESS-012` → `MAY` Ngừng dùng, thay bằng **`LOOP-HARNESS-018`** (SHOULD, mới): hook **không** có biến môi trường
  tắt riêng (agent tự đặt được = nới hàng rào ADR-0002); tắt có chủ đích qua `disableAllHooks` của Claude Code. Dự án đích
  ghép lại blueprint: bỏ trạng thái của 012, đánh giá 018 mới. Test `HookFailOpenTest`: 5 hook × stdin rỗng/rác (dự án tạm có
  `xs.py`) → exit 0, không ra quyết định; không hook nào chứa `DISABLE`/`SKIP_HOOK`; mọi hook trong `settings.json` được phủ.
- Quy mô M: mỗi module/chuẩn tối đa 4 MUST hiệu lực, `xs.py validate` chặn khi vượt (ADR-0004). 671 mục `MUST`/`MUST@M` của
  `kind: module`/`standard` → `MUST@L` (ID, nội dung giữ nguyên; xem từng ID: `git diff 55de4d1 -- framework | grep '^+- \[ \].*MUST@L'`).
  Blueprint M: `web-app` 1.094 → 470 MUST, `api-service` 912 → 402, `cli-tool` 547 → 271; S và L không đổi.
  Dự án đích: chạy lại `compose --out BLUEPRINT.md` — trạng thái giữ theo ID.

### Added
- **Audit khung trước `/autopilot`**: `xt.py doctor [--fix] [--json]` kiểm khung đã cài trong dự án (hoặc repo khung) —
  Python ≥ 3.11/git/bash, hook bắt buộc trong `.claude/settings.json` (SessionStart · PreCompact · PreToolUse · Stop; thiếu
  PostToolUse chỉ cảnh báo), file hook và file chúng nạp (`_lib.sh`, `guard.py`) tồn tại + đúng cú pháp (`bash -n`/`compile`),
  skill/subagent, `*.xtemplates-new` chưa gộp, `AGENTS.md`/`CLAUDE.md` (`@AGENTS.md` ngoài code block), `xt.yaml` đủ 4 khoá và
  cảnh báo cổng no-op khi để trống, `.autopilot/` trong `.gitignore`, `.autopilot/state.json` hỏng/BLOCKED/trỏ PLAN mất, tên cũ
  `.xstored/`/`xs.yaml`, repo git, khung `validate` xanh, `progress-check`. `--fix` chỉ sửa phần an toàn, đảo ngược được (tạo file
  thiếu từ mẫu khung không đè, thêm dòng `@AGENTS.md`/`.autopilot/`, đổi `xs.yaml` → `xt.yaml`, chuyển state hỏng sang
  `state.json.hong-<giờ>`); hook/settings không tự sửa (điểm dừng) — báo người chạy lại `install.py`. Exit 1 khi còn lỗi ✗.
  Skill `/autopilot` bước 0 chạy `doctor --fix` đầu tiên; `loop init` chạy phần nhanh và cảnh báo trên stderr khi còn lỗi (không
  chặn). Mục mới **`LOOP-HARNESS-020`** (SHOULD). Giao thức `11-autonomous-loop/README.md` thêm Pha 0; `AGENTS.md`, mẫu
  `AGENTS.md`, skill `/audit` (nhóm 13 dùng `doctor --json`), lời nhắc cuối `install.py` theo đó.
- **Phản hồi từ dự án đích về khung** (ADR-0010): `xt.py feedback add` (lỗi do khung + cách khắc phục → `docs/xtemplates-feedback/FB-NNN.md`,
  gộp một dòng, `redact`, kèm phiên bản khung), `feedback collect` (tự gom MUST bị miễn và lý do autopilot `blocked`, không trùng),
  `feedback list`, `feedback aggregate --from <dự-án>=<thư-mục>` (repo khung gộp theo (loại, ID); đủ ngưỡng khi ≥ 2 dự án hoặc có tái hiện).
  Module mới `framework/11-autonomous-loop/framework-feedback.md` — **`LOOP-FB-001`** (SHOULD), **`LOOP-FB-002`** (SHOULD),
  **`LOOP-FB-003`** (MUST: không bí mật/dữ liệu/mã dự án), **`LOOP-FB-004`** (SHOULD). `docs/ops/TARGETS.md` (danh sách dự án kéo
  phản hồi), issue template `.github/ISSUE_TEMPLATE/feedback-du-an-dich.yml`; `AGENTS.md` mẫu, `/autopilot`, `/handover` gọi
  `feedback collect`. README liệt kê đủ lệnh `loop` (`defer`/`decide`/`checkpoint`). Dự án đích: chạy lại `install.py` + `compose`.
- `loop decide`: `--choice` ưu tiên khớp nguyên văn (phương án là số), số thứ tự chỉ nhận chữ số ASCII; `--log` phải là
  file trong dự án. `loop checkpoint`: tên file giữ Unicode (`core.quotePath=false`), thiếu git không mất checkpoint,
  repo chưa commit không ghi `HEAD`; bằng chứng mới nhất hỏng thì lùi về file trước, gồm cả ID blueprint. `loop status`
  ẩn checkpoint cũ hơn bằng chứng mới nhất; `loop stop` ghi verdict cuối `stopped` (review độc lập trước merge).
- Hook **`PreCompact`** (`.claude/hooks/pre-compact.sh`) → `xt.py loop checkpoint`: trước khi nén ghi task đang làm, lệnh kiểm
  cuối + exit code, file chưa commit, lỗi lặp vào `.autopilot/state.json`; luôn exit 0 (exit 2 sẽ chặn nén); SessionStart sau
  nén in lại qua `loop status`. `HookFailOpenTest` phủ 6 hook.
- `xt.py loop defer --task <T-NNN|ID blueprint> --reason R` + verdict **`done-pending-human`** (Stop hook cho dừng, liệt kê
  việc chờ); `loop resume` đưa việc chờ lại hàng làm. `loop init --single-session` (trần vòng `max(20, 4 × (task chưa làm + MUST mở
  của blueprint))` khi không khai `--max-iterations`). `defer` từ chối lý do rỗng, ID không còn mở, task đang lỗi. `loop hook-stop` ghi `permission_mode` từ stdin và cảnh báo khi `default`/`plan`/`acceptEdits`.
- `xt.py loop decide --question Q --option A --option B [--option …] --choice N|văn bản --why W --revert R [--prod P] [--log F]`:
  ghi quyết định tự duyệt `D-NNN` (tăng dần theo số lớn nhất trong file) vào `docs/autopilot/DECISIONS.md`; exit 2 khi < 2
  phương án khác nhau, lựa chọn không khớp, hoặc câu hỏi/lý do/đường lùi rỗng; mỗi trường gộp một dòng; không đổi state autopilot.
- `XC-DOCAI-019` **SHOULD** (mới) từ catalog `seeker19110/stored` 20 §3h: khi cấp skill cho agent **theo stack**, ưu tiên installer dò stack có **cổng xuất xứ** (manifest + SHA-256 từng file + review nội dung + cảnh báo trước khi cài + `skills-lock.json`) hơn chép tay hoặc marketplace tự cập nhật; mẫu tham chiếu `autoskills` (midudev). License của nó là **CC BY-NC 4.0** (phi thương mại) nên chỉ gọi CLI đã xuất bản như bước dev tuỳ chọn, **không** đưa vào `dependencies`/bước build phân phối và **không** vendor registry/mã (CMP-LIC cấm CC BY-NC mặc định). Dự án đích: chạy lại `compose`.
- 8 mục **SHOULD** mới từ catalog `seeker19110/stored` cập nhật 13–15/10: `SEC-SUPPLY-025` (đánh giá trên repo gốc, không mirror),
  `SEC-SUPPLY-026` (số commit/sao không phải bằng chứng bảo trì; loại tool dual-use đã bị lạm dụng), `CMP-LIC-019` (đổi license
  không CLA/DCO là rủi ro), `WF-REVIEW-019` (mục "Hỗ trợ AI" trong PR template), `AI-AGENT-019` (mức tin cậy theo người gửi
  kiểm bằng code trước tool call), `AI-AGENT-020` (memory CoALA; procedural memory đổi qua PR), `LOOP-HARNESS-019` (memory
  ngoài chỉ tra cứu), `XC-DOCAI-018` (không chồng pack chỉnh giọng). Phần *Kiểm* của `BE-FILE-011` thêm `tarfile` `filter="data"`
  (ID, mức giữ). Đính chính trong `research/…stored-catalog-extraction.md`: `ponytail` là repo thật. Dự án đích: chạy lại `compose`.
- `xs.py changelog-check [FILE]`: Keep a Changelog 1.1.0 (`[Unreleased]` đầu tiên, bản có ngày ISO 8601 giảm dần, nhóm chuẩn,
  ngày hợp lệ và giảm dần, không trùng nhóm trong Unreleased, bỏ qua code block, cho `[YANKED]`, bản mới nhất == `VERSION`);
  chạy trong cổng `lint` (BASE-REPO-007, AUD-DOC-020).
- Guard Bash hỏi người khi lệnh mở phiên Claude Code bỏ qua hook của dự án: `claude` hoặc gói `@anthropic-ai/claude-code`
  (npx, `npm exec`, `pnpm`/`yarn dlx`, `node …/cli.js`) với `--bare`, `--safe-mode`, `--settings`, `--setting-sources`,
  `--restricted`; gán `CLAUDE_CODE_SIMPLE`/`CLAUDE_CODE_SAFE_MODE`; `disableAllHooks` trong tham số claude hoặc lệnh ghi file.
  Nhắc tên như dữ liệu (`grep`, `git commit -m`) không hỏi. Giới hạn: `sh -c`/`eval`/alias/biến chứa cờ (phân tích tĩnh).
  Phần *Kiểm* của `LOOP-HARNESS-018` thêm điều này (ID, mức giữ).
- Workflow `release-tag.yml` (chạy tay trên `main`): tạo annotated tag `v<VERSION>` khi `CHANGELOG.md` có mục tương ứng
  và tag chưa tồn tại — đường phát hành không cần push tag từ máy (`BASE-REPO-006`).
- Audit có máy đỡ (ADR-0005): phương pháp `framework/00-method/audit.md` (13 nhóm, thêm *Harness & quy trình agent*;
  mức 🔴/🟠/🟢; bằng chứng đo được/suy luận/chưa biết; xác minh đối kháng; quét lại theo diff; Definition of Complete),
  mẫu `templates/AUDIT-STATUS.md` (sổ máy đọc) + `templates/AUDIT-REPORT.md`, skill `/audit` viết lại.
- `xs.py audit plan [--blueprint] [--status] [--json]`: tín hiệu repo → nhóm áp dụng/rút gọn/N/A, công cụ có/thiếu,
  mục blueprint có bằng chứng/miễn trừ trỏ file đã đổi sau khi ghi, nhóm cần quét lại theo SHA trong sổ.
- `xs.py audit check STATUS [--strict]`: schema sổ audit, SHA quét là tổ tiên HEAD, chấp nhận rủi ro có chủ + hạn chưa quá.
- `xs.py progress-check [FILE]`: `PROGRESS.md` ≤ 8192 byte, đúng 4 mục theo thứ tự, mọi SHA ở Bàn giao phiên là tổ tiên HEAD
  và đã có trên nhánh chính (`XS_PROGRESS_BASE`, mặc định `origin/main`) — chặn SHA của nhánh PR mà squash-merge sẽ xoá;
  clone nông → báo cần `fetch-depth: 0`. Thay các lệnh rời `wc -c`/`git merge-base` trong phần Kiểm của `LOOP-HARNESS-004/005`,
  `WF-DOC-004`, `BASE-DOC-008`, `QA-STATIC-018`, `PM-PLAN-009` (ID và mức giữ nguyên).
- `xs.py ci-check [DIR]`: fitness function cho workflow CI (`WF-CI-020`) — `permissions:` cấp workflow, không `write-all`,
  `uses:` ghim SHA 40 ký tự (`docker://` ghim `@sha256:`), job có `timeout-minutes`, không `continue-on-error`; ngoại lệ ghi `# ci-check-allow: <lý do>`.
- Cổng `lint` của repo chạy hai lệnh trên; job `quality` checkout `fetch-depth: 0`.
- Repo khung trả nợ AUD-CODE-001: 11 hàm vượt độ phức tạp vòng 10 (`validate` 37, `audit_check` 31, `install` 21…)
  tách theo trách nhiệm, hành vi không đổi (so output/exit code 64 lệnh trước–sau); `ruff.toml` bật C901
  (`max-complexity = 10`) nên cổng `lint` chặn hàm mới vượt ngưỡng.
- Repo khung trả nợ AUD-CODE-002 và AUD-TEST-001: cổng `typecheck` chạy `mypy --strict` (0 lỗi); cổng `test` đo coverage
  dòng + nhánh tính cả code chạy trong subprocess (`.coveragerc`: `patch = subprocess`) và chặn dưới 100%
  (`coverage report --fail-under=100` — ratchet `BASE-GATE-013`); `coverage` 7.16.2 (Apache-2.0) khoá kèm hash.
- CI repo: `concurrency` chỉ hủy run cũ của PR, không hủy run trên `main` (`WF-CI-008`).

### Fixed
- **Hook `guard.py` bỏ sót/nhận nhầm lệnh (5 lỗi, đều có tái hiện)**: (1) tokenizer để shlex mở comment ở `#` GIỮA từ nên
  `echo ${#A[@]}; rm -rf ~`, `open http://x/#/rooms && git push --force origin main` không bị chặn và `git add a#b.ts && git commit`
  mất cờ `commit` (cổng commit không chạy) — nay `#` chỉ là comment khi đứng đầu từ, ngoài nháy, như bash; (2) here-string `<<<`
  bị coi là heredoc nên dòng lệnh sau nó (`wc -w <<< x` + xuống dòng + `git reset --hard`) bị cắt như thân heredoc;
  (3) `git push` không refspec, hoặc đích `HEAD`/`@`/`HEAD:HEAD`, khi nhánh hiện tại là `main`/`master` không hỏi — nay hỏi như
  `git push origin main` (nhánh lấy bằng `git symbolic-ref` ở thư mục lệnh chạy, theo `cd`/`-C`; lỗi/quá hạn/không phải repo →
  giữ hành vi cũ; thư mục không rõ → gốc dự án); (4) `git switch -f`/`--force`/`--discard-changes` không bị chặn như
  `checkout -f`, `rm -rf .git` (kể cả `./.git`, `sub/.git`) không nằm trong đích nguy hiểm; (5) `git commit -m"x"`/`-am"done"`
  (giá trị dính liền) bị hiểu có `-n` nên báo `no_verify` sai — cờ ngắn `-m`/`-F`/`-c`/`-C`/`-t`/`-u`/`-S` nay coi phần sau là dữ
  liệu (`-nm x` vẫn là `no_verify`). Test: `test_guard_hash_is_comment_only_at_word_start`,
  `test_guard_here_string_is_not_heredoc`, `test_guard_push_without_refspec_follows_current_branch`,
  `test_guard_current_branch_errors_are_unknown`, `test_guard_push_main_ask_through_hook_with_cwd`,
  `test_guard_git_switch_force_is_discard`, `test_guard_rm_dot_git`, `test_guard_commit_attached_values_are_data`.
- **Bằng chứng/cổng xanh giả khi lệnh có ống `|`** (phản hồi từ dự án đích, có tái hiện): `xt.py loop record` chạy lệnh
  bằng `/bin/sh` (`shell=True`) nên `false | cat` ghi `exit_code: 0`; `dev-task.sh` chạy lệnh khai báo bằng `bash -c` mới,
  không thừa hưởng `set -o pipefail`. Nay cả hai chạy `bash -o pipefail -c`; thiếu bash → `loop record` ghi exit 127.
  Test: `test_pipeline_failure_is_not_green`, `test_missing_bash_records_127`, `test_declared_pipeline_failure_fails_gate`.
- **Hook cổng commit chạy cổng của sai repo** (tái hiện trong phiên dự án đích): `cd ../repo-khac && git commit` hay
  `git -C ../repo-khac commit` chạy cổng của dự án phiên (`CLAUDE_PROJECT_DIR`) — đỏ/xanh không liên quan tới commit. `guard.py`
  nay theo `cwd` của payload + `cd <dir>` + `-C <dir>` trả `commit_dir`; `pre-bash-guard.sh` chạy cổng ở gốc git của thư mục đó
  khi nó có `xt.yaml`/`.xtemplates` hoặc nằm ngoài dự án (repo lồng không có khung riêng như submodule → cổng dự án như cũ;
  `cd -`/`cd "$X"` không rõ đích → gốc dự án như cũ). Test: `test_guard_commit_dir_follows_cd_and_git_C`, `CommitGateRepoTest`.
- **Verdict autopilot "done" sai** (review đối kháng, có tái hiện): bằng chứng của vòng/PLAN trước (cùng ID task) được tính
  cho PLAN mới — nay evidence có `finished` trước `started` của `loop init` → `verify`; task `[~]` không lý do được tính xong
  — nay phải ghi `— Bỏ: <lý do>` (mẫu `PLAN.md` cập nhật); dòng task sai định dạng (thụt lề, thiếu backtick, ID ngắn, ô lạ) bị bỏ
  qua im lặng — nay `verify`; Gate có thông tin đăng nhập dev (`postgres://app:app@…`) không bao giờ khớp evidence đã che → `verify`
  mãi, đốt hết ngân sách vòng — nay so Gate ở dạng đã che.
- **`blueprint-status --strict` xanh giả**: mục MUST đổi ô lạ (`[-]`), thụt lề, thiếu backtick hay bị xoá không còn được đếm
  → "0 MUST mở". Nay dòng giống mục mà sai định dạng và tổng MUST ít hơn bảng đầu trang là lỗi (`bad_lines` trong `--json`).
  Lý do miễn trừ phải nằm ở phần ghi chú (sau `· Nguồn:` cuối; chấp nhận `— Miễn:`, `- Miễn:`, `(Miễn: …)`), vì chữ của
  `LOOP-HARNESS-007` tự chứa "— Miễn:" nên mục đó `[~]` không lý do từng lọt.
- **`compose --out` (ghép lại) làm mất ghi chú và mục riêng của dự án**: ghi chú khác đúng mẫu ` — Bằng chứng:` (vd
  ` - Bằng chứng:`, `(Miễn: …)`) bị bỏ trong khi ô vẫn `[x]`; mục có ID không thuộc khung (mục riêng của dự án) bị xoá không
  cảnh báo. Nay chữ của mục không đổi thì giữ nguyên phần đuôi; chữ đổi thì nhận ghi chú dạng nới; mục riêng giữ ở mục
  "Mục riêng của dự án" cuối file (in danh sách ra stderr); mục khung đã ngừng dùng vẫn bỏ như cũ.
- **SessionStart mất 4 mục của `PROGRESS.md` dạng NFD** (soạn trên macOS): awk so byte nên không khớp tên mục; nay chuẩn hoá
  NFC trước (như `progress-check`).
- **Header `BLUEPRINT.md` trỏ sai đường dẫn công cụ ở dự án đích**: `compose` ghi `python3 scripts/xt.py blueprint-status`
  dù dự án đích dùng `.xtemplates/scripts/xt.py`; nay suy theo gốc liên kết (`XT_FRAMEWORK_LINK`). Dự án đích: chạy lại
  `compose --out BLUEPRINT.md` (giữ trạng thái theo ID).
- `xs.py progress-check`: khi đang merge, SHA bàn giao là tổ tiên của một đầu trong file `MERGE_HEAD` (kể cả octopus) cũng hợp lệ — giải xung đột
  `PROGRESS.md` bằng SHA của nhánh chính không còn bị cổng commit chặn (commit merge sẽ chứa SHA đó); hết merge thì luật cũ (AUD-HAR-020).
- Audit 2026-10-15 đợt 3: `loop init --blueprint` không tồn tại → exit 2 (AUD-HAR-016); `xs.py` không có
  `CLAUDE_PROJECT_DIR` lấy gốc = cha của `.xstored/` (bản cài, như dev-task.sh), nếu không thì thư mục cha gần nhất có
  `.autopilot`/`xs.yaml`/`.xstored`, rồi mới `.git` (repo git lồng không thắng gốc dự án) (AUD-XFEAT-001); cổng `test` dùng `COVERAGE_FILE` riêng mỗi lần chạy, hai cổng song song không xoá dữ liệu của nhau
  (AUD-TEST-002; thư mục tạm xoá sau khi chạy); bỏ 9 `noqa` vô hiệu (AUD-CODE-003); comment ci.yml nêu đủ 4 required check (AUD-DOC-021).
- `xs.py loop hook-stop` khi lỗi in thêm stacktrace + chuỗi nguyên nhân (`traceback.format_exception`) ra stderr,
  vẫn fail-open (BASE-ERR-009, AUD-HAR-014). Blueprint repo khung: `BASE-REPO-007` mở lại vì bằng chứng cũ sai
  (AUD-HAR-015); 20 bằng chứng lệch dòng/số đếm cập nhật theo mã hiện tại (AUD-HAR-018).
- Hàng rào hook (audit 2026-10-15): guard bóc wrapper `timeout`/`setsid` và giá trị của cờ wrapper (`nice -n 5`,
  `stdbuf -o L`, `xargs -n 1`, `time -f`, `timeout -k 5 10`) — trước đó mọi luật lọt, kể cả `timeout 60 git commit` không
  qua cổng (AUD-SEC-011). `pre-bash-guard` chạy cổng commit TRƯỚC khi hỏi người: `git commit … && git push origin main`
  không còn bỏ cổng (AUD-HAR-013). Luật hook-bypass: bắt `npx`/`npm exec`/`pnpm exec`/`bunx claude`, đường dẫn gói tương
  đối, `export`/`declare` biến tắt hook và ghi vào rc shell/`.json`/`.env`; hết báo nhầm `echo`, `git commit -m`, ghi file
  thường, `claude -- …` (AUD-SEC-012/013/014); quét đệ quy lệnh trong `bash -c`/`sh -c` cho luật này. Giới hạn còn lại
  (phân tích tĩnh): cờ gộp có giá trị (`xargs -tn 1`), `exec -a`, `eval`, alias, biến chứa lệnh/cờ.
- `xs.py audit check`/`audit plan --status` không còn văng traceback với sổ có số nhóm là chữ số Unicode (`²`) hoặc
  `hạn:` không phải ngày có thật (`2026-13-45`) — nay báo lỗi sổ rõ ràng.
- `xs.py loop` verdict `done` không còn khai "blueprint không còn MUST mở" khi không kiểm blueprint (`loop init` thiếu
  `--blueprint` hoặc file không còn) — lý do nay nói rõ blueprint không được kiểm (P1: không khai điều chưa đo).
- **Audit 2026-10-14 đợt 5 — tài liệu và bằng chứng** (AUD-DOC-001…018, CI-001, CI-005, HAR-006):
  - Ngừng dùng (→ `MAY`, "gộp vào" nhà, ID giữ nguyên): `WF-DOC-004`, `PM-PLAN-009`, `QA-STATIC-018` → `LOOP-HARNESS-004/005`;
    `LOOP-CI-003`, `LOOP-STOP-008` → `LOOP-DESIGN-005`; `LOOP-HARNESS-009/010/011`, `WF-DOC-014` → `XC-DOCAI-002/003/007`.
    Bản đồ "một chủ đề một nhà" thêm dòng PROGRESS/PLAN/file harness. Dự án đích: ghép lại `BLUEPRINT.md` (trạng thái giữ theo ID).
  - Số MUST theo quy mô đo lại (web-app ~70 S · ~468 M · ~1.124 L); "4 con số" theo `LOOP-DESIGN-001`; bộ khoá `xs.yaml` và
    thành phần cổng commit thống nhất; bỏ tên công cụ/job không tồn tại; script dự án tự viết ghi rõ; required check thật
    (`quality`, `protection-guard`, `gitleaks`, `dep-audit`) và hành vi `protection-guard` (đỏ khi lệch tên, cảnh báo khi ruleset chưa import).
  - 4 link ngoài 404 thay bằng nguồn chính thống còn sống (eCFR/Federal Register COPPA, FHIR VN, tài liệu Solidity); báo cáo dark
    patterns của FTC bỏ link (chưa tìm được bản thay).
  - `check-links.py`: fence `~~~`, link `<…>`, chặn link ra ngoài repo, đúng gốc khi chạy từ `.xstored/scripts/` (AUD-DOC-019, AUD-HAR-012);
    `install.py` cài thêm `check-links.py`, ghi settings/manifest nguyên tử; `xs.py` gọi git có timeout (BASE-ERR-004).
  - Workflow `dep-audit` (pip-audit khoá hash, mỗi PR + hằng tuần) và required check `dep-audit` (BASE-DEP-004, AUD-DEP-003).
  - BLUEPRINT ghép lại và xác minh lại 67 bằng chứng/miễn trừ (`xs.py audit plan` không còn bằng chứng cũ); `BASE-GATE-004` (mypy strict)
    mở lại đúng sự thật — nợ có hạn AUD-CODE-002.
- **Audit 2026-10-14 đợt 4 — CI và phụ thuộc** (AUD-DEP-001/002, CI-002, CI-004): công cụ cổng khoá kèm hash ở
  `requirements-dev.txt` (ruff 0.17.0, mypy 2.4.0 + bắc cầu; `uv pip compile --generate-hashes`), CI cài `--require-hashes`,
  Dependabot thêm ecosystem `pip`; nâng action ghim SHA lên bản chạy Node 24 — checkout v7.0.1, setup-python v7.0.0,
  codeql-action v4.38.3, gitleaks-action v3.0.0 (đã đọc release notes 2026-10-14: không đổi input repo dùng);
  ruleset mẫu `strict_required_status_checks_policy: true` (khớp `BASE-GATE-007`); lychee chấp nhận 202 (trang chặn bot).
- **Audit 2026-10-14 đợt 3 — install** (AUD-HAR-003/004/010, CI-003): dự án đã có `.claude/settings.json` được gộp khoá `hooks`
  của khung (giữ quyền và hook riêng) thay vì chỉ sinh `.xstored-new`; manifest `.xstored/harness.sha256.json` cho phép cập nhật
  tại chỗ file harness người dùng chưa sửa (bản sửa hook tới được dự án đã cài), file đã sửa vẫn sinh `.xstored-new`;
  đích là symlink thì bỏ qua; `--with-github` cảnh báo ruleset mẫu đòi required check nào.
- **Audit 2026-10-14 đợt 2 — hook** (AUD-SEC-001…010, HAR-011, HAR-005): phân tích lệnh chuyển sang `.claude/hooks/guard.py`
  (thư viện chuẩn) — tách theo token shell (`|`/`;` trong nháy và thân heredoc là dữ liệu), bỏ gán biến/`command`/`env`/tuỳ chọn
  toàn cục git trước khi so luật; chặn thêm `git checkout .`/`restore .`, `rm -Rf /`, `rm -r -f /`, `sh -c "$(curl …)"`,
  `bash <(curl …)`, `curl … | python3`, push xoá/ghi đè nhánh chính, force gộp cờ (`-uf`); hỏi khi push `feat:main`, `stash drop/clear`,
  ghi file cổng/bí mật qua Bash, `commit --no-verify` (cờ trong message không còn làm bỏ cổng). Payload qua stdin (lệnh > 128 KB
  không còn lọt). pre-edit-guard khớp cấu hình ở thư mục con (monorepo) và đường dẫn chuẩn hoá; thêm `.envrc`, `.npmrc`, `.pypirc`, `.netrc`.
  SessionStart cắt PROGRESS 8 KB không cắt giữa ký tự UTF-8. `settings.json` bỏ `ask` cho mọi `git push` (hook hỏi đúng push nhánh chính).
- **Audit 2026-10-14 đợt 1** (`docs/ops/AUDIT-STATUS.md`):
  - `dev-task.sh` ở dự án đích (`.xstored/scripts/`) lấy gốc = cha của `.xstored/`; trước đó thiếu `CLAUDE_PROJECT_DIR` thì
    không thấy `xs.yaml` và báo "GATE XANH" giả (AUD-HAR-001 🔴). Cổng không chạy lệnh nào giờ báo "KHÔNG CHẠY LỆNH NÀO", không còn chữ xanh.
  - `xs.py loop record`: một đối số = chuỗi shell nguyên văn, nhiều đối số ghép bằng `shlex.join`; chỉ bỏ `--` đầu tiên;
    so Gate theo token shell (AUD-HAR-002). Task `[x]` không có Gate không được tính xong (AUD-HAR-008).
  - Che bí mật trong bằng chứng: Bearer/Basic, `AKIA…`, `ghp_…`/`github_pat_`/`xox…`/`sk-…`, `://user:pass@`, JSON `"password": "…"`,
    `--password x`, khối PEM; che cả trường `cmd` (AUD-CFG-001).
  - `write_atomic` dùng tệp tạm ngẫu nhiên tạo độc quyền (không đi theo symlink đặt sẵn) và bằng chứng ghi nguyên tử (AUD-HAR-009);
    `--task` không nhận ký tự xuống dòng cuối (AUD-HAR-007).
- `install.py`: `PROGRESS.md` cài vào dự án đích là phần trong khối ```markdown của mẫu (4 mục), không phải cả trang hướng dẫn.
- Skill `/handover`, mẫu PROGRESS, `LOOP-HARNESS-005`: SHA bàn giao phải đã có trên nhánh chính (ID, mức giữ nguyên).
- `tests/test_hooks.py`: test "Stop hook cho dừng khi autopilot tắt" dùng dự án tạm, không đọc `.autopilot/` của repo thật
  (trước đó đỏ khi autopilot đang bật trên chính repo — đúng lúc cổng commit chạy).

## [2.0.0] - 2026-10-14

### Fixed (dogfood: áp khung lên chính repo, blueprint cli-tool quy mô S)
- `scripts/dev-task.sh`: đường dẫn file truyền qua `$1`, không nội suy vào `bash -c` (tên file `x$(lệnh).py` từng chạy được lệnh);
  khoá `""` trong `xs.yaml` nghĩa là cố ý bỏ qua, không tự dò; nháy chỉ bỏ khi bọc hai đầu.
- `xs.py loop record --task` kiểm định dạng ID (trước đó `--task ../../x` ghi ra ngoài `.autopilot/evidence/`); `output_tail` che giá trị giống bí mật.
- `xs.py compose`: lọc `applies_to` cho cả `kind: standard`; đổi gốc liên kết tương đối trong mục (trước đó mọi BLUEPRINT.md có link gãy);
  ghép lại vào file có sẵn **giữ trạng thái + ghi chú theo ID** (trước đó ghi đè làm mất tick).
- `xs.py`: `--hours 0` có hạn; đọc blueprint chuẩn hoá NFC; thư mục khung/file thiếu báo một dòng, exit 2; ghi file nguyên tử.
- `.claude/hooks/pre-bash-guard.sh`: bỏ `mapfile` và `sed '\n'` để chạy với bash 3.2/BSD (macOS); `pre-edit-guard.sh` hỏi khi sửa `xs.yaml`, `scripts/dev-task.sh`.

### Added
- `xs.py --version` (file `VERSION`), `--help` có ví dụ + mã thoát, `blueprint-status --json` và `-` đọc stdin.
- Cổng repo: `ruff.toml` (format + lint E9/F), mypy 2.4.0, CI chạy đúng `scripts/dev-task.sh gate`, test trên Python 3.11 và 3.13,
  chạy nguyên văn khối lệnh README, kiểm tiêu đề PR; workflow `links.yml` (link ngoài hằng tuần), `portability.yml` (macOS bash 3.2).
- `BLUEPRINT.md` của chính repo (cli-tool, S): 54 MUST đạt · 11 miễn · 5 chờ admin/phát hành.
- `BASE-GATE-019` (MUST@M): ruleset không bypass + review bắt buộc, tách khỏi `BASE-GATE-007`.

### Changed
- Sàn Python 3.11 (3.9/3.10 hết hỗ trợ). `BASE-ERR-005/006`, `PRF-CLI-008/009/011` → `MUST@M`; `BASE-ERR-002/003`, `BASE-CFG-007/008`,
  `BASE-SEC-010`, `PRF-CLI-005`, `BASE-REPO-002`, `BASE-DOC-007`, `BASE-DEP-006`, `BASE-GATE-001` viết lại để áp được cho CLI/thư viện.
- Ngừng dùng thêm: `BASE-DOC-002` (→ `BASE-REPO-007`), `BASE-SEC-003` (→ `BASE-DEP-004`).


### Added
- Khung v2: thư viện yêu cầu có ID — 18 mảng (`framework/01-baseline` … `18-cross-cutting`), 14 hồ sơ loại phần mềm,
  8 gói ngành, 6 bản đồ tiêu chuẩn, 15 mẫu tài liệu (`framework/templates/`), phương pháp `framework/00-method/`.
- `scripts/xs.py`: `validate` · `list` · `compose` (`--profile`, `--industry`, `--scale`, `--add`, `--include-may`) ·
  `blueprint-status --strict` · `loop init/status/record/block/resume/stop/hook-stop` · `stats`.
- `scripts/install.py` (cài vào `.xstored/` + harness copy-if-absent), `scripts/check-links.py`, `scripts/dev-task.sh` (đọc `xs.yaml`).
- Harness `.claude/`: 5 hook (session-start, pre-bash-guard, pre-edit-guard, auto-format, stop-guard), 8 skill
  (autopilot, blueprint, gate, research, audit, review, adr, handover), 3 subagent (researcher, executor, reviewer).
- `AGENTS.md` (luật dùng chung) + `CLAUDE.md` (`@AGENTS.md`); mẫu `AGENTS.md`/`CLAUDE.md`/`xs.yaml` cho dự án đích.
- CI: job `quality` (validate, link, shellcheck, JSON, 50 test, ghép thử mọi hồ sơ × ngành, cài thử), `protection-guard`,
  `gitleaks`, CodeQL Python; action ghim SHA; Dependabot github-actions; ruleset mẫu; PR template; CONTRIBUTING; SECURITY; LICENSE MIT.
- ADR-0001 (khung = thư viện ID + máy ghép/kiểm), ADR-0002 (harness hook + điểm dừng + bằng chứng), ADR-0003 (quy mô S chỉ sàn là MUST).
- `xs.py loop resume` (tiếp tục sau BLOCKED, giữ số vòng/bằng chứng); hook chặn `git commit --allow-empty`; `install.py --with-github`.
- README gốc; PROGRESS.md theo mẫu 4 mục.
- `research/`: 4 bản nghiên cứu nền ngày 2026-10-13 (khung cũ, catalog `stored`, AI agent, cơ chế Claude Code).

### Changed (rà chéo nhất quán 2026-10-14)
- OWASP Top 10 for LLM Applications: chuyển sang ấn bản **2026** (công bố 04/08/2026); mã LLM0x đổi theo bảng ánh xạ trong `12-security/ai-security.md`.
- EU AI Act Điều 50: áp dụng từ 02/08/2026 (không bị Omnibus 2026/1744 hoãn); chỉ đánh dấu máy đọc Điều 50(2) cho hệ đã lưu hành có hạn 02/12/2026.
- Mọi dẫn chiếu NĐ 13/2023 như văn bản hiện hành → Luật 91/2025/QH15 + NĐ 356/2025/NĐ-CP.
- `SEC-WEB-007` (CSRF) chấp nhận token **hoặc** kiểm `Origin`/`Sec-Fetch-Site`; `XC-UNITS-005` (tiền) chốt số nguyên mặc định, `numeric` chỉ khi có ADR; `BASE-REPO-013` lên MUST; `BE-INT-008` MUST → MUST@M.
- WCAG 2.2 REC 2023-10-05 (cập nhật 2024-12-12); SLSA Build L2 @M / L3 @L; CycloneDX 1.7; OpenAPI 3.1.x mặc định.
- `00-method/conventions.md`: thêm bản đồ "một chủ đề một nhà" và cách gộp mục trùng.

### Deprecated
- 50 mục trùng nội dung chuyển sang `MAY` "Ngừng dùng — gộp vào <ID nhà>" (không vào blueprint mặc định, ID không cấp lại):
  AI-PROTO-009, AI-PROTO-013, ARC-INT-013, BASE-CFG-004, BASE-CFG-009, BASE-CFG-010, BASE-CFG-013, BASE-CFG-015, BASE-CFG-017, BASE-DATA-004, BASE-DATA-007, BASE-DATA-013, BASE-DATA-015, BASE-DATA-016, BASE-ERR-018, BASE-ERR-019, BASE-REPO-009, BASE-SEC-008, BASE-SEC-012, BE-AUTH-012, BE-AUTH-019, BE-AUTH-021, BE-JOB-002, BE-JOB-011, FE-SEC-006, FE-SEC-016, FE-SEC-020, LOOP-CTX-007, PRF-AGENT-015, QA-PERF-001, QA-PERF-003, QA-PERF-004, QA-PERF-005, SEC-AI-012, SEC-LOG-003, SEC-LOG-004, SEC-SECRET-003, SEC-WEB-003, SEC-WEB-005, SEC-WEB-024, SEC-WEB-025, STD-PROC-006, STD-PROC-007, STD-PROC-008, UX-RESP-004, WF-ENV-001, WF-ENV-002, WF-ENV-003, WF-ENV-004, WF-ENV-015.

### Removed
- Khung v1 (văn xuôi + scaffold Next.js/Supabase, commit `1b80fe4`) — khôi phục bằng `git archive 1b80fe4`.
