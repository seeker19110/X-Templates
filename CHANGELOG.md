# Changelog

Định dạng theo [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/); phiên bản theo [SemVer 2.0.0](https://semver.org/lang/vi/).
Thay đổi **mục checklist** (thêm ID, đổi mức, ngừng dùng) ghi rõ ID để dự án đích ghép lại blueprint theo ID.

## [Unreleased]

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
  `merge`); verdict `human` khi auto-merge đang bật → tắt trước; không gọi GitHub, guard vẫn là lớp chặn. `pr reviewed --pr N --head <SHA 40 ký tự>
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
