# X-Templates — khung tham chiếu phát triển phần mềm

> Thư viện **yêu cầu có ID** cho mọi loại phần mềm và ngành nghề, kèm công cụ ghép thành checklist dự án, kiểm "xong" bằng máy,
> và harness để AI agent **tự làm đến khi hoàn thành** mà vẫn dừng đúng chỗ cần người.
> Nội dung tiếng Việt; phiên bản, chuẩn và luật xác minh từ nguồn sống ngày 2026-10-13.

## Có gì trong khung

| Mảng | Nội dung | Số file |
|---|---|---|
| [`00-method`](framework/00-method/README.md) | Nguyên tắc P1–P12, vòng đời G0–G8, quy ước module, cách ghép blueprint, luật bằng chứng, audit | 6 |
| [`01-baseline`](framework/01-baseline/README.md) | Thứ **mọi** phần mềm đều cần: repo, cổng chất lượng, bảo mật tối thiểu, lỗi/log, cấu hình, tài liệu, đúng dữ liệu, phụ thuộc | 8 |
| [`02-profiles`](framework/02-profiles/README.md) | 14 hồ sơ loại phần mềm: web, mobile, desktop, site tĩnh, API, CLI, thư viện, data/ML, **AI agent**, **hệ agentic**, game, blockchain, IoT, monorepo | 14 |
| [`03-industries`](framework/03-industries/README.md) | 8 gói ngành có khung pháp lý Việt Nam + quốc tế: fintech, y tế, giáo dục, TMĐT, chính phủ, SaaS đa tenant, truyền thông, logistics | 8 |
| [`04-standards`](framework/04-standards/README.md) | Tiêu chuẩn: bảo mật, tiếp cận, API/web, dữ liệu, quy trình, AI — phiên bản hiện hành và cách chứng minh | 6 |
| [`05`](framework/05-architecture/README.md)–[`09`](framework/09-database/README.md) | Kiến trúc · Thiết kế & UI/UX · Frontend · Backend · Cơ sở dữ liệu | 35 |
| [`10-workflow`](framework/10-workflow/README.md) | Git, review, CI/CD, phát hành, môi trường, spec-driven, tài liệu, đội & WIP | 8 |
| [`11-autonomous-loop`](framework/11-autonomous-loop/README.md) | Vòng lặp tự động: 4 con số, bằng chứng, điểm dừng, điều phối subagent, tự sửa CI, ngân sách context, phản hồi từ dự án đích | 7 |
| [`12-security`](framework/12-security/README.md) | Threat model, AppSec, bí mật, chuỗi cung ứng, hạ tầng, bảo mật AI, log & audit | 7 |
| [`13-ai-engineering`](framework/13-ai-engineering/README.md) | LLM app, RAG, agent & tool, hệ agentic, eval, guardrail, MCP/A2A, quan sát & chi phí, dữ liệu | 9 |
| [`14`](framework/14-testing-quality/README.md)–[`18`](framework/18-cross-cutting/README.md) | Kiểm thử · Vận hành · Tuân thủ & quyền riêng tư · Sản phẩm & dự án · Xuyên suốt (i18n, hiệu năng, DX, tài liệu cho AI, đơn vị/tiền/thời gian, bền vững, OSS) | 37 |
| [`templates`](framework/templates/README.md) | PROJECT, PLAN, PROGRESS, SPEC, ADR, THREAT-MODEL, RUNBOOK, POST-MORTEM, DPIA, GO-NO-GO, RELEASE-NOTES, API-CONTRACT, AGENTS, CLAUDE, xt.yaml, AUDIT-STATUS, AUDIT-REPORT | 17 |

Mỗi yêu cầu là một dòng có **ID ổn định**, mức **MUST/SHOULD/MAY**, cách **Kiểm** bằng máy và **Nguồn**:

```markdown
- [ ] `BE-AUTH-003` **MUST** Băm mật khẩu bằng Argon2id với tham số OWASP. → Kiểm: test đọc hash có tiền tố `$argon2id$`. · Nguồn: ASVS 5.0 V6
```

Chỉ mục đầy đủ theo vai đọc: [`framework/README.md`](framework/README.md).

## Dùng cho một dự án

```bash
# 1) Cài khung vào dự án (chỉ cần Python >= 3.11; không đè file đã có)
git clone https://github.com/seeker19110/X-Templates /tmp/x-templates
python3 /tmp/x-templates/scripts/install.py /đường/dẫn/dự-án --with-github

# 2) Chọn hồ sơ, ngành, quy mô rồi ghép checklist
cd /đường/dẫn/dự-án
python3 .xtemplates/scripts/xt.py list profiles
python3 .xtemplates/scripts/xt.py compose --profile web-app --industry ecommerce --scale M --out BLUEPRINT.md

# 3) Theo dõi; --strict trả exit 1 khi còn MUST chưa đạt hoặc lệnh `— Kiểm:` của mục đã tick đỏ (--run; cổng phát hành)
python3 .xtemplates/scripts/xt.py blueprint-status BLUEPRINT.md --strict --run
```

Dự án đã cài bản ≤ 2.x (thư mục `.xstored/`, `xs.py`, `xs.yaml`): chạy lại bước 1 — `install.py` tự chuyển sang
`.xtemplates/`, `xt.py`, `xt.yaml` và liệt kê file còn nhắc tên cũ để sửa tay ([ADR-0007](docs/adr/0007-rename-technical-identifiers-to-xtemplates.md)).

Quy mô quyết định khối lượng: `web-app` có 70 MUST ở **S** (prototype), 468 ở **M** (production), 1.124 ở **L** (đo 2026-10-14).
`--out BLUEPRINT.md` ghi file chính chỉ chứa MUST theo quy mô (web-app + ecommerce: 41 KB ở S thay vì ~690 KB) và
`BLUEPRINT-BACKLOG.md` chứa SHOULD/MAY ([ADR-0012](docs/adr/0012-blueprint-by-scale-and-task-iteration-cap.md)).
Ghép thêm module ngoài hồ sơ bằng `--add`, ví dụ web app có tính năng AI: `--add "13-ai-engineering/*"`.

## Chạy tự động đến khi xong

Trong Claude Code, sau khi cài khung, gõ `/autopilot <mô tả yêu cầu>`:

1. Agent lập kế hoạch G0–G4: `PROJECT.md`, `BLUEPRINT.md`, nghiên cứu phiên bản, spec, thiết kế, `PLAN.md` có task và lệnh kiểm.
2. Phiên chính tự duyệt kế hoạch theo tiêu chí chất lượng cuối và ghi `D-NNN` (ADR-0008); bạn can thiệp lúc nào cũng được.
3. Vòng lặp chạy: làm task, `xt.py loop record` ghi bằng chứng, commit, mỗi lát một PR mở kèm auto-merge ở L3 (ADR-0015), trừ ngoại lệ cứng auth/tiền/dữ liệu thật/mật mã khi `merge_hard_exceptions: human` (ADR-0016, ADR-0020). Stop hook đọc bằng chứng trên đĩa để quyết làm tiếp.
4. Dừng khi xong có bằng chứng, khi chạm ngân sách, khi cùng một lỗi lặp 3 lần, hoặc ở **điểm dừng bắt buộc**:
   thao tác không đảo ngược, tiền thật, dữ liệu người dùng thật, deploy/publish, đổi cấu hình cổng (mâu thuẫn spec không
   còn là điểm dừng: phiên chính tự quyết, ghi `D-NNN`).

Hook trong [`.claude/`](.claude/settings.json) chặn lệnh phá huỷ và `curl | sh`, hỏi trước khi deploy hoặc nới cấu hình cổng,
chạy cổng chất lượng trước mỗi commit. Luật cho mọi harness ở [`AGENTS.md`](AGENTS.md). Giao thức đầy đủ:
[`framework/11-autonomous-loop/README.md`](framework/11-autonomous-loop/README.md).

## Công cụ

| Lệnh | Việc |
|---|---|
| `python3 scripts/xt.py validate` · `python3 scripts/xt.py list profiles` | Kiểm quy ước toàn khung: frontmatter, ID duy nhất, MUST có cách kiểm, liên kết |
| `python3 scripts/xt.py compose ...` | Ghép blueprint theo hồ sơ, ngành, quy mô; ghép lại vào file có sẵn thì giữ trạng thái theo ID |
| `python3 scripts/xt.py blueprint-status FILE --strict [--run] [--json]` | Đếm đạt/miễn/chưa; dòng mục sai định dạng, mục MUST ít hơn bảng đầu trang hay miễn trừ thiếu lý do ở phần ghi chú = lỗi; `--run` chạy lại lệnh `— Kiểm: \`…\`` của mục đã tick trong thư mục chứa FILE, đỏ = chưa đạt (`LOOP-DESIGN-023`); cổng phát hành; `FILE` là `-` thì đọc stdin (không `--run`) |
| `python3 scripts/xt.py doctor [--fix] [--json]` | Audit khung đã cài trước `/autopilot`: Python/git/bash, hook + file hook + cú pháp, skill/subagent, `*.xtemplates-new` chưa gộp, `AGENTS.md`/`CLAUDE.md`, `xt.yaml`, `.gitignore`, state, khung `validate`, `PROGRESS.md`; `--fix` sửa phần an toàn (không đụng hook/settings), exit 1 khi còn lỗi |
| `python3 scripts/xt.py loop init/status/record/block/defer/decide/checkpoint/resume/stop` | Vòng lặp autopilot có bằng chứng, chạy một phiên đến khi xong (ADR-0009); `decide` ghi quyết định tự duyệt D-NNN (ADR-0008) |
| `python3 scripts/xt.py grant-check GROUP [KHOÁ=GIÁ_TRỊ …]` | Việc production có nằm trong mục Ủy quyền production của PLAN.md không: exit 0 làm, 1 `loop defer` (ADR-0022) |
| `python3 scripts/xt.py guard-check -- <lệnh>` | exit 126 nếu guard của dự án cấm lệnh — `dev-task.sh` gọi trước mỗi lệnh `xt.yaml`; Gate/`Kiểm:` do `loop record`/`verify`/`blueprint-status --run` chạy cũng qua cùng kiểm (LOOP-STOP-027) |
| `python3 scripts/xt.py merge-gate --pr N --head SHA` | Required check `merge-gate` (job `.github/workflows/merge-gate.yml`): exit 1 khi `merge-check` báo `hard` mà PR đang bật auto-merge, 3 khi head khác `--head` (ADR-0023) |
| `python3 scripts/xt.py merge-watch [--pr N] [--interval 30]` | Chạy nền sau khi mở PR: gọi `merge-check` mỗi 30 giây tới khi PR đã merge hoặc cần hành động (ADR-0021) |
| `python3 scripts/xt.py merge-check [--pr N] [--json]` | Máy quyết khi nào merge PR đã mở: `merge` · `wait` · `update` · `fix` · `human` · `closed`; `merge_autonomy`: L3 (mặc định) bật auto-merge (làn nhanh khi mở, làn chuẩn sau review sạch — ADR-0024) trừ ngoại lệ cứng (`merge_hard_exceptions: auto` thì cả ngoại lệ cứng — ADR-0020), L2 chỉ làn nhanh, L1 người merge (ADR-0013, ADR-0015, ADR-0016) |
| `python3 scripts/xt.py feedback add/collect/list/aggregate` | Phản hồi lỗi do khung + cách khắc phục từ dự án đích (`docs/xtemplates-feedback/FB-NNN.md`, qua `redact`); repo khung gộp theo (loại, ID) — ADR-0010 |
| `python3 scripts/install.py DỰ_ÁN [--with-github]` | Cài khung + harness vào dự án đích |
| `python3 scripts/xt.py progress-check [FILE]` | `PROGRESS.md` ≤ 8 KB, đúng 4 mục, SHA ở Bàn giao phiên là tổ tiên HEAD và có trên nhánh chính (`XT_PROGRESS_BASE`, mặc định `origin/HEAD` → `origin/main` → `origin/master`; CI cần `fetch-depth: 0`) |
| `python3 scripts/xt.py changelog-check [FILE]` | `CHANGELOG.md` theo Keep a Changelog 1.1.0: `## [Unreleased]` đầu tiên, bản `## [X.Y.Z] - YYYY-MM-DD` giảm dần, nhóm chuẩn, không trùng nhóm trong Unreleased; bản mới nhất == `VERSION` cùng thư mục (nếu có) |
| `python3 scripts/xt.py ci-check [DIR]` | Fitness function cho workflow CI: `permissions:` cấp workflow, không `write-all`, `uses:` ghim SHA 40 ký tự (`docker://` ghim `@sha256:`), job có `timeout-minutes`, không `continue-on-error`, workflow có `pull_request` thì job không `environment:` không chạm `secrets.*` ngoài `GITHUB_TOKEN` (`WF-CI-023`; ngoại lệ `# ci-check-allow: <lý do>`) |
| `python3 scripts/xt.py contrast FILE.css… [--pairs F] [--require-on a,b] [--json]` | Tương phản WCAG của cặp token màu trong CSS ở mọi theme (`:root`, `.dark`, `[data-theme=dark]`, `prefers-color-scheme`): tự suy cặp `--X-foreground`/`--on-X` trên `--X`, `--foreground` trên `--background`, `--ring` ≥ 3:1; cặp khác khai ở `--pairs` (`FG on BG [min N]`); chữ < 4,5:1 hoặc phi văn bản < 3:1 → exit 1; `--primary`/`--destructive` thiếu token chữ cũng đỏ (`UX-DS-003/020`) |
| `python3 scripts/xt.py vendor-check [--dirs a,b] [--allow X] [--strict] [--json]` | Mã UI vendor: thư mục `vendor`/`third_party`/… có `LICENSE`/`NOTICE`/`SOURCE`, không điều khoản hạn chế (Commons Clause, phi thương mại, Fair Use, BUSL, SSPL); dò danh sách theo dõi `ui-vendor-watchlist.json` (Preline, magic-portfolio, React Bits, Tailwind Plus) trong `package.json`/ghi nguồn; cảnh báo chỉ đỏ khi `--strict` (`CMP-LIC-022`) |
| `python3 scripts/xt.py perf sample --out F [--runs N --warmup W] -- <lệnh>` | Chạy lệnh nhiều lần, ghi mẫu thời gian tường + commit + môi trường (vòng tối ưu, `LOOP-OPT-*`) |
| `python3 scripts/xt.py perf compare TRƯỚC SAU [--exact] [--no-regress] [--json]` | So hai bộ mẫu bằng Mann-Whitney U + sàn nhiễu: `improved`/`regressed`/`neutral`/`insufficient` (exit 0 = `improved`) |
| `python3 scripts/xt.py perf guard --base REF [--locked GLOB…] [--strict]` | Worktree (cả file chưa theo dõi) không được đụng/xoá bộ đo, test tương đương; báo dòng đáng ngờ (cache/memoize, `sleep`, đổi đồng hồ, soi stack) |
| `python3 scripts/xt.py audit plan [--blueprint F] [--status F] [--json]` | Dò stack → nhóm audit áp dụng/rút gọn/N/A kèm lý do, công cụ có/thiếu, bằng chứng blueprint trỏ file đã đổi sau khi ghi, nhóm cần quét lại theo `docs/ops/AUDIT-STATUS.md` |
| `python3 scripts/xt.py audit check STATUS [--strict]` | Kiểm sổ audit (schema phát hiện, SHA quét là tổ tiên HEAD, chấp nhận rủi ro có chủ + hạn); `--strict` = Definition of Complete |
| `python3 scripts/xt.py stats` | Đếm file theo loại và mục theo mức |
| `python3 scripts/xt.py --version` · `--help` | Phiên bản khung (file `VERSION`) · ví dụ và mã thoát (0 ổn · 1 chưa đạt · 2 sai cách dùng) |
| `python3 scripts/check-links.py` | Kiểm liên kết Markdown toàn repo |
| `scripts/dev-task.sh gate` | Cổng commit: chạy lệnh trong `xt.yaml` (build · typecheck · lint · test), CI chạy đúng lệnh này |

Biến môi trường (đều tuỳ chọn): `XT_FRAMEWORK` (thư mục khung, mặc định cạnh `scripts/`) · `XT_FRAMEWORK_LINK` (gốc liên kết
trong blueprint, mặc định `.xtemplates/framework`) · `XT_RECORD_TIMEOUT` (giây, mặc định 1800) · `XT_PROGRESS_BASE` (nhánh chính cho `progress-check`, mặc định `origin/HEAD` → `origin/main` → `origin/master`; rỗng = tắt) · `CLAUDE_PROJECT_DIR` (gốc dự án cho
`loop`; không đặt thì: bản cài `.xtemplates/scripts/xt.py` → cha của `.xtemplates`; nếu không, thư mục cha gần nhất có
`.autopilot`/`xt.yaml`/`.xtemplates`, rồi gần nhất có `.git` — thư mục cha là repo khác (vd `$HOME` dotfiles) sẽ thắng; không thấy thì cwd) · `CLAUDE_CONFIG_DIR` (thư mục cấu hình người dùng của Claude Code mà `doctor`/`loop init` đọc; mặc định `~/.claude` + `~/.claude.json`) · `XT_DEBUG=1` (in traceback khi lỗi).

Kiểm tra trước khi đóng góp (cần Python ≥ 3.11 và shellcheck; ruff/mypy/coverage khoá kèm hash ở `requirements-dev.txt`):

```bash
pip install --require-hashes -r requirements-dev.txt
scripts/dev-task.sh gate                 # build · typecheck · lint · test — phần lõi của CI job quality
python3 -m unittest discover -s tests    # chỉ test (cổng test còn đòi coverage dòng + nhánh 100%, xem xt.yaml)
```

## Quyết định thiết kế

- [ADR-0001](docs/adr/0001-framework-as-id-library-with-machine-composition.md): khung là thư viện ID, máy ghép và máy kiểm "xong".
- [ADR-0002](docs/adr/0002-harness-stop-points-and-evidence-hooks.md): hook chặn hành động nguy hiểm, Stop hook đọc bằng chứng.
- [ADR-0003](docs/adr/0003-scale-s-floor-only.md): ở quy mô S chỉ sàn (baseline, hồ sơ, ngành) là MUST.
- [ADR-0004](docs/adr/0004-scale-m-module-must-cap.md): ở quy mô M mỗi module tối đa 4 MUST, phần vượt là `MUST@L`.
- [ADR-0005](docs/adr/0005-audit-with-machine-support.md): audit có máy đỡ — sổ máy đọc, `xt.py audit plan/check`.
- [ADR-0007](docs/adr/0007-rename-technical-identifiers-to-xtemplates.md): định danh kỹ thuật theo tên X-Templates
  (`.xtemplates/`, `xt.py`, `xt.yaml`, `XT_*`); `install.py` tự chuyển dự án đã cài bản ≤ 2.x. Thay ADR-0006.
- [ADR-0008](docs/adr/0008-main-session-self-approves-decisions.md): phiên chính tự duyệt điểm quyết định chuyên môn
  theo tiêu chí chất lượng cuối, ghi `D-NNN`; điểm dừng về hành động không tự duyệt (cơ chế sau: ADR-0018).
- [ADR-0009](docs/adr/0009-single-session-autopilot.md): autopilot chạy một phiên đến khi xong (compaction có checkpoint),
  việc cần người `loop defer` gom cuối phiên.
- [ADR-0010](docs/adr/0010-feedback-from-target-projects.md): phản hồi từ dự án đích về khung qua `FB-NNN` + Routine gộp
  → PR nháp, người duyệt trước khi công khai.
- [ADR-0011](docs/adr/0011-gate-fail-closed-in-autopilot.md): trong vòng autopilot, `lint`/`test` rỗng hoặc no-op làm cổng đỏ.
- [ADR-0012](docs/adr/0012-blueprint-by-scale-and-task-iteration-cap.md): `BLUEPRINT.md` chỉ chứa MUST theo quy mô,
  SHOULD/MAY ở `BLUEPRINT-BACKLOG.md`; trần vòng một phiên chỉ đếm task.
- [ADR-0013](docs/adr/0013-machine-decides-when-to-merge.md): `xt.py merge-check` quyết khi nào merge PR; guard chỉ cho
  tự merge làn nhanh ở L2 với lệnh ghim head.
- [ADR-0015](docs/adr/0015-auto-merge-on-open-l3.md): mức `merge_autonomy: L3` (mặc định, chủ repo yêu cầu) — auto-merge
  của GitHub cho mọi làn; GitHub merge khi required check xanh (làn chuẩn bật sau review sạch — ADR-0024).
- [ADR-0014](docs/adr/0014-pr-per-slice-and-machine-merge.md): mỗi lát code một PR; máy tự merge khi `merge-check` cho
  phép bằng lệnh ghim head (`gh pr merge`, REST `PUT …/merge` có `sha`, MCP `merge_pull_request` có `expectedHeadSha`).
- [ADR-0016](docs/adr/0016-l3-keeps-hard-exceptions.md): ở L3 PR chạm tiền/dữ liệu người dùng thật/auth/mật mã/bí mật
  vẫn người merge (`merge-check` trả `hard`, guard không bật auto-merge) — tắt được bằng ADR-0020.
- [ADR-0017](docs/adr/0017-allow-all-bash-behind-fences.md): `permissions.allow` gồm `Bash` — mọi lệnh Bash không hỏi;
  hàng rào là `deny`/`ask` của settings và hook guard.
- [ADR-0018](docs/adr/0018-deny-dangerous-allow-rest.md): guard không hỏi người — lệnh nguy hiểm/không đảo ngược bị
  chặn, còn lại cho chạy; `XT_GUARD_POLICY=strict` giữ hành vi hỏi cũ.
- [ADR-0019](docs/adr/0019-hard-exceptions-denied-under-no-ask.md): dưới chính sách không hỏi, merge/bật auto-merge PR
  ngoại lệ cứng (`hard`) bị chặn — người merge.
- [ADR-0020](docs/adr/0020-hard-exceptions-owner-opt-out.md): chủ dự án tắt được chốt người của ngoại lệ cứng
  (`xt.yaml` `merge_hard_exceptions: auto` đã commit ở nhánh đích; thiếu khoá = `human`; PR đổi khoá luôn người merge);
  repo khung `auto`, mẫu dự án đích `human`.
- [ADR-0021](docs/adr/0021-merge-watch-after-opening-pr.md): mở PR xong chạy nền `xt.py merge-watch` (30 giây/lần, gọi lại
  `merge-check`) tới khi PR đã merge hoặc cần hành động.
- [ADR-0022](docs/adr/0022-production-grants-in-plan.md): duyệt kế hoạch = một lần người duyệt mục Ủy quyền production
  (`- grant:` trong PLAN.md, máy kiểm `xt.py grant-check`); PR đổi grant/khoá luôn người merge; hạn mức autopilot mặc định x2.
- [ADR-0023](docs/adr/0023-merge-gate-required-check.md): required check `merge-gate` (`pull_request_target`, mã của
  nhánh mặc định) đỏ khi `merge-check` báo `hard` trên head hiện tại mà PR đang bật auto-merge — auto-merge không ghim head.
- [ADR-0024](docs/adr/0024-auto-merge-after-clean-review.md): merge theo làn — PR quan trọng (làn chuẩn) `reviewer` rà sạch
  mới bật auto-merge, PR làn nhanh bật khi mở; không bật được thì merge bằng lệnh ghim head của `merge-check`.

Nghiên cứu nền ngày 2026-10-13 ở [`research/`](research/): phân tích khung cũ, trích xuất catalog `seeker19110/stored`,
AI agent và giao thức, cơ chế Claude Code. Khung cũ khôi phục được bằng `git archive 1b80fe4`.

## Đóng góp

Xem [`CONTRIBUTING.md`](CONTRIBUTING.md) và [`framework/00-method/conventions.md`](framework/00-method/conventions.md).
Báo lỗ hổng: [`SECURITY.md`](SECURITY.md). Giấy phép: [MIT](LICENSE).
