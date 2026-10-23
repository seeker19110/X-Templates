# PLAN-3.16.0-ceiling.md — Khung X-Templates · chặng "tháng tới" sau phân tích trần 2026-10-23 → bản 3.16.0

> Lập ngày 2026-10-23 theo [`research/2026-10-23-ceiling-analysis.md`](../../research/2026-10-23-ceiling-analysis.md) §5–§7
> (chủ repo: "theo khuyến nghị đi"). Phiên chính tự duyệt (D-142, ADR-0008). Mục tiêu: **không thêm bề mặt** — cắt lãng phí
> CI tự gây bằng cấu hình, chuyển chất lượng từ hình thức sang nội dung ở chỗ rẻ, và đo thật; mọi số kỳ vọng đo lại bằng
> `pr stats` sau 1 tuần (2026-10-30).
>
> **Cú pháp bắt buộc cho máy:** mỗi task một dòng `- [ ] \`T-NNNN\` <việc> — Gate: \`<lệnh>\``.

## Tóm tắt (cổng duyệt — phiên chính tự duyệt, D-142)
- Phạm vi: Lát 1 cấu hình CI/steward/ruleset (lỗ đo được: ¾ run huỷ cùng SHA do `edited`; 3 commit mới nhất trên `main`
  chưa qua CI; file ruleset cũ hơn ruleset sống; steward `wait` giả). Lát 2 chất lượng nội dung nơi ≤ 150 dòng mã (checker
  Nguồn, `unchecked_must` có cờ, trần tổng byte thư mục, `claude_min_version`). Lát 3 đo thật (`pr stats` đếm push và vượt
  trần 1.000 run; TARGETS/feedback). Lát 4 phát hành 3.16.0 (mẫu CI của dự án đích đổi → minor).
- Cách làm: mỗi lát một PR, test đỏ trước khi sửa với payload/file giả (hook và CI không chạy thật trong test); chạm cấu
  hình cổng/CI/hook phải nêu lý do + số đo trong commit (AGENTS.md §3); không nới cổng nào.
- Không làm (§8 research): tách `xt.py`; song song worktree; merge queue; reviewer LLM cho mọi PR; xoá stub `merge-gate.yml`
  (chờ T-1834 ở hotel-manager/X-Company); thu nhỏ `guard.py`; thêm module/ID; cache Playwright (D-133).
- Rủi ro: bỏ `edited` làm kiểm tiêu đề không chạy lại khi sửa tiêu đề (đỡ: workflow riêng vài giây nghe `edited`);
  `workflow_dispatch` CI trên `main` cần `actions: write` cho job steward (đỡ: quyền ở job-level, chỉ dispatch đúng
  `ci.yml` trên nhánh mặc định; ghi lý do trong workflow); checker Nguồn làm đỏ module thiếu URL (đỡ: 134/135 đã đạt, sửa
  file còn lại trong cùng PR); trần byte làm đỏ PR sửa lỗi cần thêm dòng (đỡ: trần = hiện tại + 5 %, muốn vượt phải cắt
  chỗ khác — đó là mục đích).

## Ngân sách (4 con số)
- Số vòng tối đa: `max(40, 8 × task)` (`loop init --single-session` tính)
- Chi phí: 0 đồng ngoài phiên (không phụ thuộc mới)
- Timeout mỗi lệnh Gate: 1800 giây (`XT_RECORD_TIMEOUT` mặc định)
- Ngày hết hạn: 12 giờ sau `loop init` (`--hours 12`)

## Điểm dừng bắt buộc (`loop defer`; `loop block` khi mọi việc còn lại phụ thuộc)
- Đặt `XT_STEWARD_TOKEN`, sửa ruleset sống, tạo Routine đọc repo đích private, quyền repo đích: chủ repo (LOOP-STOP-014)
- Ruleset đòi review của người → báo chủ repo, chuẩn bị lát kế ở nhánh cục bộ

## Task

### Lát 1 — Cắt lãng phí CI tự gây (cấu hình, không thêm lệnh xt.py)
- [x] `T-2401` Tách kiểm tiêu đề PR (Conventional Commits ≤ 72) ra `.github/workflows/pr-title.yml` (trigger `pull_request` `opened/edited/synchronize/reopened`, concurrency riêng, `contents: read`); bỏ `edited` khỏi `ci.yml` và mẫu `framework/templates/ci.yml` (sửa chú thích); test khẳng định CI nặng của cả hai file không còn `edited`; CHANGELOG ghi số đo (57–62/83 run huỷ cùng SHA, ~100 phút runner/tuần) (files: .github/workflows/ci.yml, .github/workflows/pr-title.yml, framework/templates/ci.yml, tests/test_ci.py, tests/test_ci_template.py, CHANGELOG.md) — Gate: `python3 -m unittest discover -s tests -k ci_no_edited_trigger && python3 scripts/xt.py ci-check`
- [x] `T-2402` CI chạy trên `main` sau merge của steward: `ci.yml` thêm `on: workflow_dispatch`; `xt.py pr steward --apply` sau merge thành công gọi `POST actions/workflows/ci.yml/dispatches` (`ref` = nhánh mặc định; `GITHUB_TOKEN` được tạo `workflow_dispatch` — docs GitHub) khi không có `XT_STEWARD_TOKEN`; job steward `actions: write` ở job-level kèm lý do; mẫu/danh sách copy `install.py` theo; test với payload giả (exec: deep) (sau: T-2401; files: scripts/xt.py, .github/workflows/pr-steward.yml, .github/workflows/ci.yml, framework/templates/ci.yml, scripts/install.py, tests/test_merge.py, CHANGELOG.md) — Gate: `python3 -m unittest discover -s tests -k steward_dispatch_ci`
- [x] `T-2403` Đồng bộ `.github/rulesets/main.json` với ruleset sống (`strict_required_status_checks_policy: false`, kiểm `gh api repos/seeker19110/X-Templates/rules/branches/main` 2026-10-23); `docs/ops/RUNBOOK-PR-STEWARD.md` và PROGRESS nói đúng hiện trạng; lý do trong commit (files: .github/rulesets/main.json, docs/ops/RUNBOOK-PR-STEWARD.md, PROGRESS.md) — Gate: `python3 scripts/xt.py checks`
- [x] `T-2404` Steward `wait` giả: run 39619253401 (#207) và 39630751648 (#208) trả `wait — CI đang chạy` khi check đã `completed` → #208 chờ 2,57 h; tái hiện bằng `statusCheckRollup`/check-run ghi lại từ REST, sửa chỗ đọc trạng thái (`_ci_buckets`/`_ci_blocker` hoặc nguồn rollup), test đỏ trước (exec: deep) (sau: T-2402; files: scripts/xt.py, tests/test_merge.py) — Gate: `python3 -m unittest discover -s tests -k ci_blocker_completed_not_wait`

### Lát 2 — Chất lượng nội dung nơi rẻ
- [x] `T-2405` `validate`: mục `## Nguồn` phải có ≥ 1 URL `https://` và dấu ngày (`xác minh YYYY-MM-DD` hoặc `(chưa xác minh)`); sửa `framework-feedback.md` (file duy nhất thiếu URL); `conventions.md` ghi máy kiểm; CHANGELOG (sau: T-2401; files: scripts/xt.py, framework/11-autonomous-loop/framework-feedback.md, framework/00-method/conventions.md, tests/test_xt.py, CHANGELOG.md) — Gate: `python3 scripts/xt.py validate && python3 -m unittest discover -s tests -k sources_section`
- [x] `T-2406` `blueprint-status --json` và `release-check` in số + tỉ lệ `unchecked_must`; cờ `--unchecked-must=fail` (mặc định `warn`) để dự án đích bật ở `harden` (repo khung chưa bật — 58 MUST, nợ ghi PROGRESS); mẫu GO-NO-GO tách hàng "máy đã chạy" / "người đã đọc" (sau: T-2405; files: scripts/xt.py, framework/templates/GO-NO-GO.md, tests/test_xt.py, CHANGELOG.md) — Gate: `python3 -m unittest discover -s tests -k unchecked_must`
- [x] `T-2407` Trần tổng byte thư mục trong `tests/test_docs_budget.py`: `scripts/*.py + scripts/xt_app`, `.claude/hooks/`, `framework/11-autonomous-loop/` = kích thước tại HEAD lát này + 5 %, không nới; ADR-0043 "ngân sách kích thước" (đóng băng bề mặt 3.x, mở băng cần ADR) (sau: T-2405; files: tests/test_docs_budget.py, docs/adr/0043-size-budget.md, CHANGELOG.md) — Gate: `python3 -m unittest tests.test_docs_budget`
- [x] `T-2408` `xt.yaml` repo khung khai `claude_min_version: 2.1.295` (`onFailure: block` của hook — changelog Claude Code); PROGRESS ghi lịch xét lại hàng rào 2027-01-21 (LOOP-DESIGN-014) (sau: T-2403; files: xt.yaml, PROGRESS.md) — Gate: `grep -q '^claude_min_version: 2' xt.yaml && grep -q 'xét lại hàng rào' PROGRESS.md && python3 scripts/xt.py checks`

### Lát 3 — Đo thật
- [ ] `T-2409` `pr stats`: đọc run theo `actions/workflows/<ci>/runs` chia cửa sổ `created` theo ngày để vượt trần 1.000 của listing (ghi `runs_truncated` khi vẫn chạm); thêm `pushes` (head SHA riêng biệt/PR), `first_push_green`, `cancelled_same_sha`; README/PROGRESS dùng số mới (sau: T-2404; files: scripts/xt.py, tests/test_merge.py, README.md) — Gate: `python3 -m unittest discover -s tests -k pr_stats_pushes`
- [ ] `T-2410` Vòng phản hồi: `docs/ops/TARGETS.md` thêm X-Company (và dhcb, xboss nếu biết `owner/repo`), ghi ngày kiểm; thử `feedback aggregate` một lần với repo đọc được; Routine tuần và quyền repo private → `loop defer` cho chủ repo (sau: T-2409; files: docs/ops/TARGETS.md) — Gate: `test -s docs/ops/TARGETS.md && python3 scripts/xt.py feedback aggregate --help >/dev/null`

### Lát 4 — Phát hành
- [ ] `T-2411` VERSION 3.16.0 + CHANGELOG `[3.16.0]` (mệnh đề "Dự án đích: chạy lại `install.py` — mẫu CI bỏ `edited`, thêm `pr-title.yml`") + PROGRESS (đo lại 2026-10-30 bằng `pr stats`); tag qua `release-tag.yml` (sau: T-2406, T-2407, T-2408, T-2410; files: VERSION, CHANGELOG.md, PROGRESS.md) — Gate: `scripts/dev-task.sh gate`
