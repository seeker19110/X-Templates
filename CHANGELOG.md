# Changelog

Định dạng theo [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/); phiên bản theo [SemVer 2.0.0](https://semver.org/lang/vi/).
Thay đổi **mục checklist** (thêm ID, đổi mức, ngừng dùng) ghi rõ ID để dự án đích ghép lại blueprint theo ID.

## [Unreleased]

### Added
- CI fan-out/fan-in cho dự án đích (`WF-CI-024`, `WF-CI-001`): mẫu không phụ thuộc stack `framework/templates/ci.yml` — job song song `build` · `typecheck` · `lint` (mỗi job gọi `.xtemplates/scripts/dev-task.sh <task>`, lệnh lấy từ `xt.yaml`), `test-plan` + `test` (matrix `TEST_SHARDS` shard qua `dev-task.sh test-shard` khi `xt.yaml` khai đủ `test_list`/`test_unit`/`test_combine`, không thì một job chạy `dev-task.sh test`), `coverage` (gộp bằng `test-combine`; không chia shard thì bỏ qua theo bước, không theo job), `checks` (bước đầu `dev-task.sh require lint test` — D-096: ĐỎ ở mọi `delivery_phase` khi `lint` hoặc `test` của `xt.yaml` rỗng/no-op theo `is_noop`, kèm `::error::` nêu khoá cần điền và ví dụ Node/Python/Go, vì job `lint`/`test` gặp khoá rỗng chỉ in "skip" và xanh — "CI xanh rỗng"; `typecheck`/`build` rỗng vẫn được; `xt.py doctor`, `xt.py ci-check`, tiêu đề PR theo Conventional Commits — miễn `pr_title_check: off`/bot/`Revert`), `quality` TỔNG HỢP `needs` mọi job con `if: always()` đỏ khi kết quả ≠ `success`, `protection-guard` (đối chiếu ruleset ↔ job, như repo khung; không có ruleset → cảnh báo); action ghim SHA, `contents: read`, timeout mỗi job, concurrency theo PR. Mẫu `framework/templates/secret-scan.yml` (job `gitleaks`). `dev-task.sh setup`: chạy khoá mới `setup` của `xt.yaml` (cài phụ thuộc/toolchain, vd `npm ci`) — chỉ lệnh khai báo, vắng/rỗng → bỏ qua exit 0, qua guard (cấm → 126). `dev-task.sh require T…`: exit 1 khi task phân giải ra rỗng/no-op (tự dò được thì tính là có lệnh). Test `tests/test_ci_template.py`. **Dự án đích: chạy lại `install.py --with-github`** — CI mẫu ĐỎ tới khi khai `lint:` và `test:` thật trong `xt.yaml` (D-096; mẫu `xt.yaml` để rỗng); `quality` không còn phải tự viết (dự án đã có `ci.yml`/`secret-scan.yml` riêng: giữ nguyên, bản khung ở `*.xtemplates-new` để gộp tay); thêm `setup:` vào `xt.yaml` nếu job CI cần cài phụ thuộc; còn `dep-audit` (theo ngôn ngữ) là required check phải tự viết job hoặc bỏ khỏi ruleset.
- Cổng commit nhanh `commit_gate: fast|full` trong `xt.yaml` (vắng = `full` = hành vi cũ; giá trị lạ → `doctor`/`ci-check` từ chối): hook `pre-bash-guard.sh` chạy `dev-task.sh gate-fast` khi `fast` — `format_check` · lint · typecheck · `test_fast` với `XT_CHANGED_FILES` (file đổi so với HEAD + file mới), không build, không ngưỡng coverage; `test_fast` trống/no-op hoặc không biết file đổi → `test`. `dev-task.sh gate` giữ nguyên là cổng đầy đủ (CI `quality`, chạy một lần trước khi đẩy/mở PR); `--no-verify` vẫn không bỏ được cổng nào. `xt.py test-select [FILE…] [--tests DIR] [--unittest]` chọn test liên quan (chính file test, `test_<tên>.py`, test nhắc tên file, test quét theo đuôi; không ánh xạ được → cả suite). Repo khung và mẫu `framework/templates/xt.yaml` đặt `commit_gate: fast`; `/autopilot` Pha 2 bước 10: commit nhanh → cổng đầy đủ một lần → đẩy một lần, mở PR → review đúng head song song CI → `pr next`; không đẩy thêm sau review. Dự án đích: chạy lại `install.py`; đặt `commit_gate` (và `test_fast` nếu stack có lệnh test liên quan) trong `xt.yaml`. `test-select` chọn thêm test theo `import <module>` (không chỉ theo tên file); diff đụng `xt.yaml`, `ruff.toml`, `pyproject.toml`, `.coveragerc`, `requirements*.txt`, `scripts/dev-task.sh`, hook cổng hoặc `settings.json` thì commit luôn chạy cổng đầy đủ (commit không tự hạ cổng của chính nó).
- Pha giao hàng `delivery_phase: build|harden` trong `xt.yaml` ([ADR-0031](docs/adr/0031-delivery-phase-build-harden.md); PD-02/PD-04 rút gọn): vắng/rỗng = `harden` (hành vi cũ); mẫu `framework/templates/xt.yaml` đặt `build`, repo khung khai `harden`; `doctor` (lỗi `xt-yaml`) và `ci-check` từ chối giá trị lạ. Pha có hiệu lực khi cả nhánh đích đã commit lẫn cây làm việc đều `build`. Pha build: PR làn chuẩn KHÔNG thuộc ngoại lệ cứng merge khi CI xanh + không xung đột + không có review `blocking` (ở head, hoặc ở head cũ mà chưa có review sạch sau nó — push không "rửa" lỗi chặn) + không mang nhãn `risk:` — `merge_eligibility` trả `review: deferred`, `merge-check --json` có `review_deferred: true` (cùng `delivery_phase`), `merge-gate`/guard/steward theo cùng kết quả, `pr next` ghi "pha build: bỏ qua review, ghi nợ (ADR-0031)"; ngoại lệ cứng (kể cả đã miễn người bằng `merge_hard_exceptions: auto`) vẫn cần review sạch; guard không đổi. Nợ review trả ở G7: `release-check` thêm hàng BLOCKER `phase` (FAIL khi `build`/giá trị lạ) và `review_debt` (FAIL khi file ngoài tài liệu đổi sau SHA quét của sổ audit mà chưa được phủ — theo nhóm audit của file, file không thuộc nhóm nào so với SHA quét mới nhất). `LOOP-STOP-022` (mức không đổi) trỏ ADR-0031. Corpus `autonomy-bench` thêm 12 ca `pr-phase-*`/`review-phase-*` (tổng 291, `AUTONOMY-BASELINE.md` cập nhật). **Dự án đích:** chạy lại `install.py` (nhận `xt.py`, skill `/autopilot`), rồi đặt `delivery_phase` trong `xt.yaml` (copy-if-absent — dự án cũ tự thêm `delivery_phase: build` nếu muốn merge nhanh; trước G7 đặt `harden`).

### Changed
- `dev-task.sh test-shard` chia theo trọng số khi `xt.yaml` khai `test_weights` (D-095; `WF-CI-024` mức không đổi, nêu thêm cách chia này): `xt.py test-shard-plan I N --weights FILE` chia tham lam LPT (lớp nặng trước, vào shard nhẹ nhất; lớp chưa có trọng số lấy trung vị; file vắng → mọi lớp cùng trọng số = `k mod N`; JSON hỏng/giá trị không phải số giây ≥ 0 → exit 2); `dev-task.sh test-weights` (= `xt.py test-weights --unit CMD --out FILE`) đo lại từng lớp nối tiếp có coverage, ghi JSON khoá sắp xếp, lớp đỏ → không ghi — chạy tay, CI không chạy. Repo khung commit `tests/shard-weights.json`: 4 shard từ 63/58/80/164 s tổng trọng số (`k mod N`) còn 91/91/91/92 s. Không khai `test_weights` → hành vi cũ. Dự án đích: không bắt buộc (chạy lại `install.py` để nhận `dev-task.sh`/`xt.py` mới nếu muốn khai `test_weights`).
- Tách lớp test nặng để shard CI không bị một lớp chặn (mỗi lớp một tiến trình): `MergeGuardTest` → lớp gốc `MergeGuardBase` + `MergeGuardTest`/`MergeGuardPinnedMergeTest`/`MergeGuardHardUnpinnedTest`/`MergeGuardFailClosedTest`; `EvidenceHooksTest` → `EvidenceHooksBase` + `EvidenceHooksTest`/`TaskCompletedHookPassTest`/`EvidenceHooksStopInstallTest`; mẫu cặp của `GuardCorpusTest` (4000) và bảng `find` của `GuardRemainingGapsTest` chia theo chỉ số cho 4 lớp `GuardCorpusPairsPart*Test`/`GuardFindAutopilotPart*Test`, bảng ca `DevTaskWeightedShardTest` cho 2 lớp `DevTaskWeightedPartitionPart*Test` — giữ tên phương thức test, `GuardCorpusPartsTest`/`test_partition_case_parts_cover_table` khẳng định hợp các phần == bảng đầy đủ (1090 → 1100 test); `tests/shard-weights.json` đo lại: lớp nặng nhất 36,4 → 14,2 s, shard chậm nhất 52,3 → 35,5 s (đo cùng máy).
- `install.py --with-github` cài thêm `.github/workflows/ci.yml` và `secret-scan.yml` từ mẫu (copy-if-absent; AUD-CI-003 cập nhật: mọi workflow cài sang đều không phụ thuộc stack), ghi hash file `.github/` vào `.xtemplates/manifest.json` — chỉ khi file đích đúng bằng bản khung, file của dự án khác bản khung không được ghi hash (file chưa sửa được cập nhật tại chỗ ở lần cài sau; `doctor --drift` thấy file đã sửa/thiếu); cảnh báo ruleset chỉ còn nêu required check chưa có job (`dep-audit`) thay vì cả bốn; `--plan` liệt kê hai workflow mới.
- CI song song hoá theo mô hình fan-out/fan-in (**`WF-CI-024`** mới, SHOULD; `WF-CI-001` mức không đổi, ghi rõ `always()` thay `!cancelled()`): `ci.yml` tách cổng nối tiếp `gate` thành job `build` · `typecheck` · `lint` (mỗi job gọi đúng `scripts/dev-task.sh <task>`), `test` 4 shard theo lớp có coverage + job `coverage` gộp dữ liệu các shard (artefact) và đòi đúng ngưỡng 100 % như `xt.yaml` `test`; `py311` 3 shard trên nhánh tên `main`; `checks` thêm `setup-python` 3.13 và nhận `autonomy-bench`. `dev-task.sh` thêm `test-shard I N [DIR]` và `test-combine DIR` (đọc khoá mới `test_list`/`test_unit`/`test_combine` của `xt.yaml`; shard rỗng, `test_list` đỏ hoặc ít hơn `XT_MIN_TESTS` id → đỏ; qua guard như lệnh khác); `gate`/`gate-fast`/`test` giữ nguyên. Job `quality` thành job TỔNG HỢP `if: always()` `needs` mọi job con, đỏ khi bất kỳ kết quả ≠ `success` — đóng lỗ `!cancelled()`: run bị huỷ làm `quality` thành `skipped` mà GitHub tính required check đạt (auto-merge có thể merge mã chưa qua test). Ruleset không đổi (vẫn 5 required check). `tests/test_ci.py` giữ không trôi (mọi task của `gate` có job, `quality.needs` đủ, hợp các shard == tập lớp của discover). Dự án đích: nhận cùng mô hình qua mẫu `framework/templates/ci.yml` khi chạy lại `install.py --with-github` (xem mục Added; workflow của repo khung không cài sang; `dev-task.sh` có thêm hai lệnh con, chỉ chạy khi gọi).
- Tên phiên `<Tên repo> — <tên nhánh>` (`LOOP-HARNESS-028`, mức SHOULD giữ nguyên vì `harness-files.md` đã đủ 4 MUST ở quy mô M) trở thành bước bắt buộc của quy trình: skill `/autopilot` Bước 0 đặt tên phiên trước `doctor` (bullet tên phiên lên đầu; đang ở `main` thì tạo nhánh trước; tên phiên để danh sách phiên cho biết phiên nào giữ nhánh/PR nào — bỏ câu sai về Stop hook); `AGENTS.md` và mẫu `AGENTS.md` ghi "bắt buộc, đặt ngay đầu phiên". **Dự án đích:** chạy lại `install.py` (skill `/autopilot`; `AGENTS.md` copy-if-absent — tự chép dòng Tên phiên).
- Test dọn thư mục tạm: các `tempfile.mkdtemp()` không được dọn trong `tests/test_hooks.py`, `tests/test_guard_corpus.py`, `tests/test_install.py`, `tests/test_xt.py` chuyển sang `enterContext(tempfile.TemporaryDirectory())` (`enterClassContext` cho `setUpClass`) — mỗi lần chạy suite không còn để lại hàng trăm thư mục trong `/tmp` (chính thứ làm guard chậm, D-097). `.gitignore` thêm `.claude/worktrees/` (bản sao repo của subagent).

### Fixed
- Guard chậm khi đích ghi/dời là thư mục ngoài dự án (D-097): `_dir_holds_gate` từng `os.listdir` cả thư mục rồi phân loại từng mục — `mv x /tmp`, `cp a /tmp/` mất ~2,2 s/lệnh trên máy có ~22k mục trong `/tmp`, nay ~0,16 s. Đích ngoài gốc dự án chỉ kiểm đích danh tên file cổng chữ (`Makefile`, `pyproject.toml`, `xt.yaml`… ở mọi nơi; `settings.json` khi thư mục là `…/.claude`; `dependabot.yml` khi là `…/.github`) bằng `os.path.lexists`, không liệt kê; trong dự án giữ liệt kê như cũ. `~/.claude` có `settings.json` vẫn là cổng; `rm -rf` ngoài dự án vẫn bị chặn (luật riêng, không đổi). Thu hẹp có chủ đích: thư mục NGOÀI dự án chỉ chứa file cổng theo mẫu có `*` (`tsconfig.base.json`, `eslint.config.js`) không còn tính là cổng. Test `GuardOutsideDirTest` (mock `os.listdir` — đỏ trên bản cũ). Dự án đích: chạy lại `install.py` để nhận `guard.py` mới.
- Review delta PR #173: `ci_classify` lớp `secret` chỉ loại dòng giống dòng test đỏ (`FAILED a::t`, `FAIL pkg 0.1s`, `FAIL: test`, `--- FAIL: Test`, AssertionError) — dòng phát hiện thật có chữ FAILED/failed (`FAILED: gitleaks detected 2 leaks`, `semgrep scan failed: 5 findings`) và `0 findings, 2 blocking findings` vẫn block; `Finding:` của gitleaks tính là phát hiện. Task có ghi chú `sau:`/`files:` không đọc được (cả `SAU:`, `Files:`, `sau T-1`) không `ready` ở `loop next`, `loop record` từ chối (fail-closed). `_safe_rel_path` (doctor drift, `context`) chặn symlink ở thành phần giữa đường dẫn trỏ ra ngoài dự án. Corpus `ci_log` 25 ca (tổng 279).

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
  (trước đây chỉ `hard`); guard hỏi khi bật auto-merge/merge PR làn chuẩn thiếu review đã đăng ở head. **Dự án đích:** chạy lại
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
