---
title: Dữ kiện sống cho bản dev tự host — ảnh container, compose, runner CI, worktree và phiên headless, scheduled task, GitHub App
kind: research
updated: 2026-11-12
---

# Dữ kiện sống cho bản dev tự host — nghiên cứu 2026-11-12 (T-3866)

Việc của [PLAN-factory-e2e](../docs/autopilot/PLAN-factory-e2e.md) Lát 0, theo [ADR-0075](../docs/adr/0075-end-to-end-factory.md):
tra nguồn sống cho ba nhóm quyết định sắp tới — hợp đồng triển khai dev (T-3841), song song và worker ngoài phiên
(T-3850), checklist thiết lập một lần (T-3859). **Chỉ dữ kiện, không chọn**; quyết định ở ADR sau. Mọi mục đọc ngày
**2026-11-12** qua ba lượt tra độc lập (subagent `researcher`); nguồn là trang chính thức hoặc registry. Trang dài đi qua
mô hình tóm tắt của công cụ fetch nên câu trích nguyên văn cần đối chiếu bản gốc trước khi đưa vào ADR. Năm của vài ngày
phát hành chỉ suy từ ngữ cảnh (đánh dấu "năm chưa xác minh").

**Quan hệ với [`2026-11-11-factory-e2e-facts.md`](2026-11-11-factory-e2e-facts.md)** (cùng T-3866, do PLAN dẫn): file này là
lượt tra độc lập thứ hai, cùng chủ đề; hai file không thay nhau. Ba chỗ lệch giữa hai file (nguồn đọc lại 2026-11-12):

| Điểm | File 2026-11-11 | File này |
|---|---|---|
| Claude Code CLI | "ổn định v2.1.322" | npm dist-tag: `latest` 2.1.322, `stable` 2.1.311 |
| App manifest | "`code` sống một giờ" | cả flow phải xong trong một giờ; hạn riêng của `code` chưa xác minh |
| Fine-grained PAT | hạn 1–366 ngày | tham số URL 1–366 hoặc `none` (chính sách org có thể chặn); mặc định 30 ngày |

Gói hiện có để đối chiếu: `web-api-ts` — Node 24 (`>=24.11.0 <25`), pnpm 12.16.1, Postgres 17 (ghim digest 17.11), `os:
linux`, host `claude-code` (`framework/templates/packs/web-api-ts/pack.json`).

## 1. Container và compose

| Mục | Dữ kiện | Nguồn |
|---|---|---|
| Docker Engine | 29.9.3 (2026-11-03); 29.10.0-rc.1 là pre-release. Nhánh 28 hết hỗ trợ 2026-05-13. Giấy phép Apache-2.0 | docs.docker.com/engine/release-notes · github.com/moby/moby · endoflife.date |
| Docker Compose (plugin) | v5.7.1 (nhãn Latest; "11 Nov", năm chưa xác minh) · Apache-2.0 · chưa archive. Bản Python v1 ở nhánh `v1` | github.com/docker/compose |
| Compose Spec | Spec ở `compose-spec/compose-spec`; trường `version:` chỉ thông tin, dùng sẽ cảnh báo "obsolete". `depends_on.condition`: `service_started` · `service_healthy` · `service_completed_successfully`. `healthcheck`: `test`, `interval`, `timeout`, `retries`, `start_period`, `start_interval`. Mặc định các số: theo `HEALTHCHECK` của Dockerfile (chưa đọc trang đó) | docs.docker.com/reference/compose-file |
| Docker Desktop | Điều khoản thương mại riêng; miễn phí khi mã nguồn mở phi thương mại hoặc dưới 250 nhân viên và dưới 10 triệu USD doanh thu. Trang cài Engine nói "hơn 250 / hơn 10 triệu" — biên lệch nhau, đọc lại nguyên văn khi áp dụng | docker.com/legal · docs.docker.com/engine/install |
| Podman | v6.2.0 ("10 Nov", năm chưa xác minh); Apache-2.0. endoflife.date chưa có nhánh 6.2 (chậm hơn GitHub) | github.com/containers/podman · endoflife.date |
| `podman compose` | Chỉ là wrapper gọi `docker-compose` hoặc `podman-compose` (ưu tiên `docker-compose` nếu có cả hai); đổi bằng `compose_providers` hoặc `PODMAN_COMPOSE_PROVIDER` | docs.podman.io |
| `podman-compose` | 1.6.0 (2026-06-03), **GPL-2.0-only**, Python ≥ 3.9 | pypi.org/pypi/podman-compose |
| Podman rootless | Cần dải `/etc/subuid`/`/etc/subgid`, `newuidmap`/`newgidmap`, mạng user-mode (pasta/passt) | github.com/containers/podman (tutorial rootless) |

## 2. Ảnh nền, digest, giới hạn pull

| Mục | Dữ kiện | Nguồn |
|---|---|---|
| Node 24 | Bản vá 24.22.3 (tag git `v24.22.3` → `e63cab04…`). Krypton: LTS từ 2025-10-28, **maintenance từ 2026-10-20**, EOL 2028-04-30. Node 26 LTS từ 2026-10-28. Tag Hub: `24`, `24.22.3`, `24-bookworm`, `24-bookworm-slim`, `24-trixie(-slim)`, `24-alpine`(=alpine3.24). `node:24` mặc định **bookworm** | hub.docker.com/_/node · nodejs/Release `schedule.json` · endoflife.date |
| Postgres 17 | Hub và postgresql.org: **17.11**; endoflife.date ghi 17.12 (2026-11-09) và git đã có tag `REL_17_12` (`702b3dc8…`) nhưng chưa thấy thông báo phát hành → **(17.12 chưa xác minh)**. EOL 2029-11-08. `postgres:17` mặc định **trixie**; có `17-bookworm`, `17-alpine` | postgresql.org/support/versioning · hub.docker.com/_/postgres · git.postgresql.org |
| Ghim digest | `FROM img:tag@sha256:…`; ghim giữ build ổn định nhưng "opt out of automated security fixes"; Docker Scout và Dependabot (`package-ecosystem: docker`) cập nhật digest đã ghim | docs.docker.com/build/building/best-practices |
| Lấy digest | `docker buildx imagetools inspect NAME` (`--format "{{json .Manifest}}"` có khoá `digest`); `crane digest IMAGE [--full-ref]`; `skopeo inspect docker://… --format '{{.Digest}}'` (`--raw` không hỗ trợ `--format`). Giấy phép crane/skopeo chưa đọc | docs.docker.com · github.com/google/go-containerregistry · github.com/containers/skopeo |
| Giới hạn pull Hub | Chưa đăng nhập: **100 pull / 6 giờ** theo IPv4 hoặc IPv6 /64; tài khoản cá nhân: 200; vượt → HTTP 429; ảnh multi-arch tính theo kiến trúc; `HEAD` không tính, `GET` tính | docs.docker.com/docker-hub/usage/pulls |
| Kho thay thế | `mirror.gcr.io`: cache ảnh Hub hay dùng, Google không quét, không bảo đảm còn lâu; `node`/`postgres` có trong cache hay không **chưa xác minh**. ECR Public: Docker Official Images có (blog AWS 2021), đường dẫn chính xác và tag 24/17 hiện hành **chưa xác minh** (trang JS); hạn mức chưa xác thực 500 GB/tháng. `ghcr.io`: không thấy nguồn cho `node`/`postgres` chính thức | docs.cloud.google.com/artifact-registry · aws.amazon.com/blogs/containers · github.com/docker-library/official-images |

## 3. Runner CI

| Mục | Dữ kiện | Nguồn |
|---|---|---|
| `ubuntu-latest` | = Ubuntu 24.04; nhãn `-latest` chuyển dần 1–2 tháng khi OS mới GA, nên ghim `ubuntu-24.04`. Có `ubuntu-26.04` (GA hay beta chưa rõ), `ubuntu-22.04`, `ubuntu-slim` | github.com/actions/runner-images |
| Phần mềm trên `ubuntu-24.04` (image 20261101.360.1) | Docker **28.0.4** (nhánh EOL), Compose **2.38.2**, Buildx 0.38.1, Node 22.23.4 mặc định (24.22.2 trong cached tools), Postgres 16.15 cài sẵn nhưng tắt. Image đổi hằng tuần | github.com/actions/runner-images (Ubuntu2404-Readme) |
| Cấu hình | Repo public 4 vCPU/16 GB; private 2 vCPU/8 GB; `ubuntu-slim` 1 vCPU, không Docker-in-Docker, job tối đa 15 phút | docs.github.com (GitHub-hosted runners) |
| `services:` | Cần runner Linux; ví dụ Postgres dùng `--health-cmd pg_isready --health-interval 10s --health-timeout 5s --health-retries 5`. Trang riêng cho `docker compose` trong job **chưa đọc** | docs.github.com (PostgreSQL service containers) |
| Giới hạn | Job hosted tối đa 6 giờ; self-hosted 5 ngày; workflow run 35 ngày; ma trận 256 job; job đồng thời hosted: Free 20 · Pro 40 · Team 60 · Enterprise 500 | docs.github.com/actions/reference/limits |
| Phí | Repo public + runner chuẩn: miễn phí. Private: hạn mức USD theo gói (Free 12 · Pro/Team 18 · Enterprise Cloud 300). Self-hosted không trừ hạn mức | docs.github.com (billing for Actions) |
| `actions/runner` | v2.338.2 (nhãn Latest, "26 Oct", năm chưa xác minh) · tag `d1eb12d4…`; dùng Node 24 nội bộ | github.com/actions/runner |
| ARC | Apache-2.0, chưa archive; chế độ hiện hành `gha-runner-scale-set` (0.15.1, "23 Oct"); chế độ cũ chỉ cộng đồng giữ; yêu cầu Kubernetes tối thiểu chưa thấy | github.com/actions/actions-runner-controller |

## 4. Receipt có digest

| Mục | Dữ kiện | Nguồn |
|---|---|---|
| `buildx build --metadata-file` | JSON có `containerimage.digest`, `containerimage.config.digest`, `containerimage.descriptor`, `buildx.build.ref`, `buildx.build.provenance` (mặc định mức `min`) | docs.docker.com/reference/cli/docker/buildx/build |
| Attestation | `--provenance` mặc định `mode=min`, chỉ gắn khi đẩy lên registry; `--sbom=true` là opt-in. Driver `docker` cần containerd image store, nếu không báo "Attestation is not supported" | docs.docker.com/build/metadata/attestations |
| `actions/attest` / `attest-build-provenance` | Cả hai v4.2.2 (tháng 8, năm chưa xác minh); `attest-build-provenance` từ v4 là wrapper, GitHub khuyên `actions/attest` cho việc mới; MIT theo trang repo (`actions/attest` chưa đọc LICENSE). Quyền: `id-token: write`, `contents: read`, `attestations: write` (+ `packages: write` cho ảnh); đầu vào `subject-name`, `subject-digest` | github.com/actions/attest · docs.github.com (artifact attestations) |
| `docker inspect` (`RepoDigests`, `Id`) | **Chưa tra** | — |

## 5. Worktree, phiên headless, song song

| Mục | Dữ kiện | Nguồn |
|---|---|---|
| git | 2.56.1 (tag `v2.56.1` có thật; ngày 2026-10-26 chưa xác minh — endoflife.date ghi nhánh 2.56 mới nhất là 2.56.0, 2026-09-28). `git worktree`: `add/list/lock/unlock/move/prune/remove/repair`; `add` từ chối nhánh đã checkout ở worktree khác (trừ `--force`); `--detach` được; ref dưới `refs/` dùng chung, `HEAD` riêng từng worktree. Mục BUGS: nhiều checkout "still experimental", submodule "incomplete… NOT recommended". Tài liệu **không nói** gì về xung đột khi merge hai worktree | git-scm.com/docs/git-worktree |
| Claude Code | npm `latest` = 2.1.322 (2026-11-10), `stable` = 2.1.311 | registry.npmjs.org · code.claude.com/docs/en/changelog |
| `claude -p` | Exit 0/khác 0; `--output-format json` có `result`, `session_id`, `total_cost_usd`; `stream-json` cần `--verbose`; `--max-turns` (không mặc định); `--max-budget-usd` (ước tính phía client, có thể vượt, tính cả subagent); `--permission-prompts none` (từ 2.1.259). Từ 2.1.302 `-p` không đặt chế độ thì bắt đầu ở **Manual** (lệnh cần duyệt bị từ chối); ở `auto`, bị chặn 3 lần liên tiếp hoặc 20 tổng thì tạm dừng và hỏi — không có người thì hành động đó không chạy nhưng lần chạy không dừng | code.claude.com/docs/en/headless · cli-reference · permission-modes |
| `--bare` vs hook | Không `--bare` thì `-p` **chạy hook** của `.claude/settings.json` và nối `.mcp.json` không hỏi tin cậy; `--bare` bỏ hook/skill/CLAUDE.md/MCP và không đọc OAuth (cần `ANTHROPIC_API_KEY`); tài liệu nói `--bare` sẽ thành mặc định của `-p` ở bản sau (khớp luật "không `--bare`" của CLAUDE.md) | code.claude.com/docs/en/headless |
| Worktree | `claude --worktree <tên>` tạo `<repo>/.claude/worktrees/<tên>`, nhánh `worktree-<tên>`; `-p` không tự dọn (khoá còn tới lần quét sau); subagent `isolation: worktree` tự xoá nếu không đổi; subagent trong worktree lấy `CLAUDE.md` từ cuộc hội thoại chính | code.claude.com/docs/en/worktrees · sub-agents |
| Song song subagent | Tối đa **20** đồng thời mỗi phiên (`CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS`); lồng tối đa 3 tầng (`CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`). Phiên cloud dùng chung rate limit tài khoản; tài liệu không ghi số | code.claude.com/docs/en/sub-agents · claude-code-on-the-web |

## 6. Scheduled task (cloud), phiên cloud, kênh vào

| Mục | Dữ kiện | Nguồn |
|---|---|---|
| Tính năng | "Cloud scheduled tasks" (trước là *routines*), trang `routines.md`, `/schedule`; **research preview** | code.claude.com/docs/en/routines |
| Lịch | Cron 5 trường, UTC trừ khi có `CRON_TZ=`; **tối thiểu 1 giờ** (nhanh hơn bị từ chối); chạy đầu giờ có thể trễ; chạy theo lịch 100/giờ/tài khoản; "Run now" và API fire 30/giờ/task, 100/giờ/tài khoản | …/routines · scheduled-tasks |
| Kênh kích hoạt | Schedule · API `/fire` với bearer token (token chỉ hiện một lần; header beta `experimental-cc-routine-2026-04-01`; trường `text` tự do) · sự kiện GitHub (cần cài Claude GitHub App; `/web-setup` chỉ cấp quyền clone) | …/routines |
| Repo và push | Mỗi repo thêm vào được clone mỗi lần chạy từ default branch; đẩy lên nhánh `claude/…` trừ khi prompt chỉ khác; mất kết nối GitHub quá 72 giờ thì task tự tắt | …/routines |
| Vì sao push 403 khi thiếu nguồn repo | Mọi thao tác GitHub đi qua proxy; proxy chỉ phục vụ repo đã gắn vào phiên (repo khác → 403 "is not enabled for this session"), từ chối xoá nhánh và đẩy tag, từ chối GraphQL (nên `gh pr`/`gh issue` 403). Khớp ghi chú S2 của PROGRESS | code.claude.com/docs/en/cloud-environments · claude-code-on-the-web |
| Mạng và tài nguyên | Mức mạng: None · Limited (allowlist) · Full (tên cũ Trusted/Custom vẫn mở được). ≈ 4 vCPU, 16 GB, 30 GB; lệnh foreground mặc định 2 phút, tối đa 10 phút, nền thêm 30 phút; SessionStart hook hết hạn 600 giây | …/cloud-environments |
| Bí mật | Biến môi trường của môi trường cloud hiện với mọi người dùng môi trường đó; tài liệu khuyên "network secrets" cho khoá API. Phiên cloud cần tài khoản claude.ai (không Bedrock/Vertex); tổ chức ZDR/HIPAA/CMEK không dùng được | …/cloud-environments |
| Auto-fix PR | Cần Claude GitHub App; có thể trả lời comment dưới tên tài khoản người dùng và kích workflow `issue_comment` | …/claude-code-on-the-web |

## 7. GitHub Actions, App, quyền

| Mục | Dữ kiện | Nguồn |
|---|---|---|
| `claude-code-action` | MIT (theo trang repo; chưa `git log` LICENSE); chưa archive; tag `v1.0.271` → `4fa93a88…` trùng `v1` (năm chưa xác minh). Cần `ANTHROPIC_API_KEY` hoặc `CLAUDE_CODE_OAUTH_TOKEN`; ví dụ quyền: `contents: write`, `pull-requests: write`, `issues: write`, `id-token: write`, `actions: read`. App chính thức cấp cả bộ quyền rộng, không chọn tập con được (muốn tối thiểu → App tự tạo) | github.com/anthropics/claude-code-action · code.claude.com/docs/en/github-actions |
| Ai kích hoạt được | Trên issue/PR: người kích hoạt phải có quyền ghi. `allowed_non_write_users` và `allowed_bots: '*'` bị chính `docs/security.md` gắn "RISKY". Nội dung issue/PR được lọc (HTML ẩn, ký tự vô hình) nhưng tài liệu nói "new bypass techniques may emerge"; với `pull_request_target` không checkout ref không tin cậy vào gốc workspace | …/docs/security.md |
| `pull_request_target` | GitHub: chạy ở ngữ cảnh default branch; "Avoid using this event if you need to build or run code from the pull request"; không checkout mã không tin cậy; giá trị `github.event.*` qua `env:` rồi dùng trong `run:`. Security Lab: nên tách `pull_request` (không đặc quyền) và `workflow_run` (đặc quyền); `persist-credentials: false` | docs.github.com (events, secure-use) · securitylab.github.com |
| `issues`/`issue_comment` | Chỉ chạy khi file workflow ở default branch | docs.github.com (events) |
| `GITHUB_TOKEN` | Sự kiện do nó tạo **không** kích workflow mới (ngoại lệ: `workflow_dispatch`, `repository_dispatch`); khuyến nghị token cài đặt của App hoặc PAT. Commit do Claude tạo bằng `GITHUB_TOKEN` cũng không kích CI | docs.github.com (GITHUB_TOKEN, triggering a workflow) · code.claude.com |
| App manifest | 3 bước: POST manifest tới `github.com/settings/apps/new` (org: `/organizations/ORG/settings/apps/new`) → GitHub redirect về `redirect_url?code=…&state=…` → `POST /app-manifests/{code}/conversions` (201/404/422) trả `id`, `pem`, `webhook_secret`, `client_id`, `client_secret`. Cả flow phải xong trong **1 giờ**. Trường: `name`, `url` (bắt buộc), `hook_attributes`, `redirect_url`, `callback_urls` (≤ 10), `public`, `default_events`, `default_permissions`. Người phải bấm tay: **Create GitHub App**, rồi **Install App** chọn repo | docs.github.com (registering a GitHub App from a manifest · installing your own GitHub App) |
| Quyền tối thiểu (App) | Tạo ref/commit: Contents write · PR: Pull requests write · **merge PR: Contents write** · đọc check: Checks read · đọc run: Actions read · `workflow_dispatch`: Actions write | docs.github.com (permissions required for GitHub Apps) |
| Token cài đặt | Hết hạn sau **1 giờ**; thu hẹp bằng `repositories`/`permissions` (≤ 500 repo). Rate limit: 5 000/giờ cơ sở, +50/giờ mỗi repo (> 20 repo) hoặc mỗi user (> 20 user), trần 12 500; `GITHUB_TOKEN` 1 000/giờ/repo. Thứ cấp: ≤ 100 request đồng thời, 900 điểm/phút (REST), "có thể đổi không báo trước" | docs.github.com (generating an installation access token · rate limits) |
| Ruleset | Bypass actors gồm **GitHub Apps**; chế độ "Always" hoặc "For pull requests only". Bật auto-merge: Settings → General → "Allow auto-merge"; mutation `enablePullRequestAutoMerge` là **GraphQL** (không có endpoint REST) với `expectedHeadOid` | docs.github.com (rulesets, managing auto-merge, GraphQL pulls) |
| Merge ghim head | `PUT /repos/{o}/{r}/pulls/{n}/merge` với `sha` ("SHA that pull request head must match"); sai → 409; `merge_method` merge/squash/rebase; không hỗ trợ stacked PR và merge queue | docs.github.com/en/rest/pulls/pulls |
| Fine-grained PAT | Mặc định hết hạn 30 ngày; `expires_in` 1–366 hoặc `none` (có thể bị chính sách org chặn); một chủ (user hoặc một org); org có thể bắt duyệt hoặc cấm hẳn; ≤ 50 token mỗi chủ; **không hỗ trợ Checks API**; merge = Contents write, tạo PR = Pull requests write, dispatch = Actions write | docs.github.com (managing personal access tokens · permissions for fine-grained PAT) |
| So App với PAT | App: quyền tối thiểu, giới hạn repo, token 1 giờ, hoạt động gắn app thay vì người; chủ làm một lần (Create + Install). Tài liệu không có bảng so sánh; best-practices: "Your app should never use a personal access token… to authenticate" | docs.github.com (best practices for creating a GitHub App) |

## 8. Điều lệch khỏi giả định hiện có của khung

1. **Runner hosted tụt sau bản stable:** `ubuntu-24.04` mang Docker 28.0.4 (nhánh đã EOL từ 2026-05-13) và Compose 2.38.2 (bản mới: 29.9.3 và 5.7.1). ADR cần xét việc ghi phiên bản Docker/Compose thực dùng vào receipt hoặc tự cài bản mới.
2. **Giới hạn pull Hub 100/6 giờ theo IP** và runner hosted dùng IP chung: ADR cần xét ghim digest và kho thay thế hoặc cache cho ảnh nền; kho thay thế nào có đủ `node`/`postgres` chưa xác minh (mục 2).
3. **Node 24 đã ở maintenance** từ 2026-10-20 (EOL 2028-04-30) trong khi `compat.node` của gói ghim `>=24.11.0 <25`; Node 26 là LTS từ 2026-10-28. Không đổi ở lát này — việc của `/upgrade`.
4. **Postgres 17.11 vs 17.12** không thống nhất giữa nguồn; gói đang ghim 17.11 — đúng với nguồn chính thức tại ngày đọc.
5. **`GITHUB_TOKEN` không kích workflow mới** và ruleset cho App bypass: bot mở/merge PR (T-3850, T-3865) cần token cài đặt của App hoặc PAT (tài liệu GitHub khuyến nghị cả hai) thay vì `GITHUB_TOKEN`. Bật auto-merge chỉ có GraphQL — bị proxy phiên cloud chặn (xem mục 6), nên merge ghim head bằng REST là đường khả thi (khớp ADR-0036).
6. **`claude -p` mặc định chạy hook** nếu không `--bare`; chế độ quyền của `-p` mặc định là Manual và chính `--permission-mode` quyết định mọi lời gọi (`--permission-prompts none` chỉ bỏ chờ host và không cho thử lại, không thay `--permission-mode`) — worker ngoài phiên cần đặt tường minh; `--max-budget-usd` là ước tính phía client và có thể vượt.
7. **Scheduled task tối thiểu 1 giờ**, còn ở research preview (header beta); không thay được worker cần phản hồi dưới giờ.

## 9. Chưa xác minh

- `docker inspect` (`RepoDigests`/`Id`); trang hướng dẫn `docker compose` trong job Actions; mặc định `healthcheck` ở Dockerfile.
- Ảnh `node`/`postgres` có trên `mirror.gcr.io` và `public.ecr.aws/docker/library` với tag 24/17 hiện hành; `ghcr.io` (không thấy nguồn, chưa chứng minh là không có).
- Postgres 17.12 đã phát hành chính thức chưa; năm của các ngày phát hành Compose v5.7.1, Podman 6.2.0, runner v2.338.2, `actions/attest` v4.2.2, ARC 0.15.1, `claude-code-action` v1.0.271.
- Giấy phép `crane`, `skopeo`, `actions/attest`; lịch sử LICENSE (`git log --follow`) của các repo — chưa clone vì proxy phiên chỉ phục vụ repo đã gắn. `gh api` tới repo ngoài bị 403.
- Ai được phép cài App lên repo của org; quyền App cần cho `enablePullRequestAutoMerge`; `POST /app-manifests/{code}/conversions` có cần xác thực không; code tự hết hạn đúng 1 giờ hay chỉ cả flow.
- Phần cuối các trang `permission-modes` và `sub-agents` (≈ 17–20 nghìn ký tự); các trang Agent SDK; mặc định telemetry của Claude Code và Action.
- Mô tả đầy đủ cờ `--worktree` và `--max-budget-usd` (dòng bảng CLI bị cắt khi đọc).

## 10. Rủi ro giấy phép và trạng thái

- Copyleft: `podman-compose` GPL-2.0-only; còn lại đã đọc đều Apache-2.0 hoặc MIT. Docker Desktop có điều khoản thương mại; Docker Engine độc lập Apache-2.0.
- Đang ở "research preview": cloud scheduled tasks và endpoint `/fire` (header beta; tên cũ *routines*; `--remote` là bí danh ngừng dùng của `--cloud`).
- `mirror.gcr.io` và ECR Public là cache/kho phụ, không phải nguồn chính thức; `mirror.gcr.io` tự nói không quét ảnh.
- `allowed_non_write_users` và `allowed_bots: '*'` của `claude-code-action`; auto-fix PR có thể kích workflow `issue_comment`; `pull_request_target` — nhắc lại việc "bỏ khỏi `pr-review.yml` trước 2026-12-02" ở PROGRESS.

## 11. Ứng viên cho T-3841 (chưa chọn)

Chỉ để ADR đi từ đó; ADR cân bằng tiêu chí chất lượng cuối (ADR-0008) và chọn.

| Quyết định | Ứng viên | Điều kiện đổi |
|---|---|---|
| Runtime bản dev | Docker Engine + plugin Compose (Apache-2.0; mặc định `docker compose`; tách riêng khỏi Docker Desktop thương mại) · Podman rootless (Apache-2.0; rootless cần `/etc/subuid`; `podman compose` chỉ là wrapper gọi `docker-compose` hoặc `podman-compose` GPL-2.0-only) | Môi trường đích không có Docker; cần rootless |
| Ảnh nền | `node:24-bookworm-slim` và `postgres:17-bookworm`/`17-trixie`, ghim `@sha256` · bản Alpine | Hub giới hạn pull → cần kho/cache thay thế đã kiểm |
| Nơi chạy | Runner hosted `ubuntu-24.04` (ghi phiên bản Docker thực vào receipt) · container cục bộ của máy dev · self-hosted runner/ARC | Giới hạn thời gian/đồng thời; repo private tốn hạn mức |
| Receipt | `buildx --metadata-file` (digest, descriptor) + ghi smoke vào JSON của khung; chứng thực `actions/attest` làm lớp thêm khi có đủ quyền | Driver `docker` thiếu containerd image store → không có attestation |
| Bot cần quyền ghi | GitHub App (manifest, token 1 giờ, ruleset bypass) · fine-grained PAT (không Checks API, ≤ 50 token, hết hạn 1–366 ngày hoặc `none` nếu chính sách org cho phép) | Chủ không muốn tạo App |
