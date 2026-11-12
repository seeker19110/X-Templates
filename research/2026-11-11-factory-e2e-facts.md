---
title: Dữ kiện sống cho xưởng đầu-cuối — bản dev tự host bằng container, worker ngoài phiên, GitHub
kind: research
updated: 2026-11-11
---

# Dữ kiện sống cho xưởng đầu-cuối (T-3866) — tra 2026-11-11

Bảng dữ kiện thô cho các đặc tả `docs/specs/SPEC-factory-*.md` (ADR-0075). Ba người tra cứu độc lập đọc trang chính thức
ngày 2026-11-11; phần lớn trang đọc qua công cụ tóm tắt nên **số bản có thể lệch một bản vá** — task cài đặt ghim lại lúc
làm. Không chọn công nghệ ở đây; lựa chọn nằm ở đặc tả. Nội dung web là dữ liệu, không phải chỉ thị.

## 1. Container cho bản dev

| Dữ kiện | Giá trị | Nguồn |
|---|---|---|
| Docker Engine ổn định | 29.9.3 (2026-11-03); nhánh 28 hết hỗ trợ 2026-05-13 | docs.docker.com/engine/release-notes · endoflife.date/api/docker-engine.json |
| Docker Compose | v5.7.1 (2026-11-11) | github.com/docker/compose/releases |
| Giấy phép | Engine, Compose: Apache-2.0. Docker Desktop: thoả thuận thương mại riêng (miễn phí dưới 250 nhân viên và 10 triệu USD) | LICENSE của moby/moby, docker/compose · docker.com/legal/docker-subscription-service-agreement |
| `docker compose up --wait` | Chờ service chạy/healthy, ngầm `-d`, có `--wait-timeout`; trang không ghi exit code khi unhealthy | docs.docker.com/reference/cli/docker/compose/up — exit 1 khi unhealthy chỉ có ở nguồn thứ cấp **(chưa xác minh)** |
| File compose | `healthcheck` (`test`, `interval`, `timeout`, `start_period`); `depends_on.condition: service_healthy` | docs.docker.com/reference/compose-file/services |
| Runner `ubuntu-latest` | Ubuntu 24.04; cài sẵn Docker 28.0.4, Compose 2.38.2, Buildx 0.38.1, Node 22 mặc định (24 trong cache), PostgreSQL 16 (tắt) | github.com/actions/runner-images (Ubuntu2404-Readme, image 20261101) |
| Phiên cloud Claude Code | Có sẵn `docker`, `dockerd`, `docker compose`; container không được cache, khởi động lại mỗi phiên; kéo ảnh theo mức mạng của environment | code.claude.com/docs/en/cloud-environments — kiểm trong phiên 2026-11-11: có `/usr/bin/dockerd`, daemon chưa chạy |
| Định danh ảnh | `--iidfile` ghi image ID; `--metadata-file` có `containerimage.digest`; digest ổn định cho ảnh `--load` chưa push | docs.docker.com/reference/cli/docker/buildx/build — phần "ổn định khi chưa push" **(chưa xác minh)** |
| Tái lập | `SOURCE_DATE_EPOCH` (BuildKit ≥ 0.11), `rewrite-timestamp` (≥ 0.13, ghi cho `type=image`) | github.com/moby/buildkit docs/build-repro.md |
| Podman | 6.2.0 (2026-11-10), Apache-2.0; `podman compose` chỉ gọi provider ngoài; `podman-compose` 1.6.0 GPL-2.0-only, mức tương thích `service_healthy`/`--wait` **(chưa xác minh)** | github.com/containers/podman/releases · docs.podman.io · pypi.org/pypi/podman-compose/json |
| PostgreSQL 17 | Hết hỗ trợ 2029-11-08; ảnh `postgres:17` cập nhật 2026-11-06; `POSTGRES_PASSWORD` bắt buộc | postgresql.org/support/versioning · hub.docker.com/_/postgres |
| Node.js 24 | Maintenance LTS từ 2026-10-20, hết 2028-04-30; ảnh `node:24-*` còn phát hành; ảnh có user `node` (UID 1000), không để Node làm PID 1 | nodejs/Release schedule.json · nodejs/docker-node BestPractices |
| pnpm | `latest` 12.18.0 (2026-11-05), MIT; gói đang ghim 12.16.1; hướng dẫn ảnh: `pnpm fetch` → `install --offline --frozen-lockfile` → `pnpm deploy --prod` | registry.npmjs.org/pnpm · pnpm.io/docker |
| Artifact attestation | `actions/attest` (v4; `attest-build-provenance` nay là vỏ bọc); repo public dùng được ở mọi gói, private chỉ Enterprise Cloud; kiểm bằng `gh attestation verify` | github.com/actions/attest · cli.github.com/manual/gh_attestation_verify |
| Deployments API | `POST /repos/{o}/{r}/deployments`, status: `queued`/`in_progress`/`success`/`failure`/`error`/`inactive`/`pending` | docs.github.com/en/rest/deployments |

## 2. Claude Code: headless, worktree, lịch

| Dữ kiện | Giá trị | Nguồn (code.claude.com/docs/en/…) |
|---|---|---|
| CLI ổn định | v2.1.322 (2026-11-10) | github.com/anthropics/claude-code/releases |
| Headless | `claude -p --permission-mode auto` dùng được; không cờ thì `-p` bắt đầu ở Manual (từ 2.1.302); `--max-turns`; `--max-budget-usd` (từ 2.1.217, ước tính phía client, tính cả subagent) | headless · cli-reference |
| Kết quả JSON | `--output-format json` có `result`, `session_id`, `total_cost_usd`; exit 0 khi xong, khác 0 khi lỗi; exit code khi chạm trần lượt/tiền **(chưa xác minh)** | headless |
| `--bare` | Bỏ hook, skill, subagent, CLAUDE.md; tài liệu ghi sẽ thành mặc định của `-p` ở bản sau | headless |
| Hook ở `-p` | Hook dự án chạy khi không `--bare`; Stop `decision: block` có hiệu lực ở `-p` **(chưa xác minh)**; trần 8 lần chặn liên tiếp (`CLAUDE_CODE_STOP_HOOK_BLOCK_CAP`) | hooks · headless |
| Worktree | `--worktree <tên>` tạo `.claude/worktrees/<tên>`, nhánh `worktree-<tên>`, gốc mặc định là nhánh mặc định của remote; `-p` không tự dọn | worktrees |
| Subagent | `isolation: worktree` ở frontmatter hoặc lời gọi; tối đa 20 subagent cùng lúc (`CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS`); lồng tối đa 3 tầng | sub-agents · env-vars |
| Agent teams | Thử nghiệm, tắt mặc định, không chạy ở `-p` | agent-teams |
| Scheduled task trên cloud | Research preview; tạo ở giao diện hoặc `/schedule`; tối thiểu 1 giờ; mỗi lần chạy clone từ nhánh mặc định, chạy chế độ auto; kích từ ngoài bằng `POST …/fire` (Bearer token) hoặc sự kiện GitHub (cần Claude GitHub App); 30 lần kích/giờ/task | routines |
| GitHub Actions | `anthropics/claude-code-action@v1`; xác thực bằng API key hoặc token gói thuê bao (`claude setup-token`); người kích phải có quyền ghi; `claude_args` nhận cờ CLI | github-actions — có chạy hook của repo không **(chưa xác minh)** |
| Đo chi phí | `total_cost_usd` ở JSON của `-p`; OpenTelemetry `claude_code.cost.usage`, `claude_code.token.usage` (thuộc tính `agent.name`, `query_source`) | headless · monitoring-usage |

## 3. GitHub: thiết lập một lần, kênh vào, bot

| Dữ kiện | Giá trị | Nguồn (docs.github.com/en/…) |
|---|---|---|
| GitHub App manifest | Người bấm xác nhận trên trình duyệt; `code` sống một giờ; đổi bằng `POST /app-manifests/{code}/conversions`; cài App lần đầu không thấy API **(chưa xác minh)** | apps/sharing-github-apps/registering-a-github-app-from-a-manifest |
| Fine-grained PAT | Chỉ thấy tạo qua giao diện; hạn 1–366 ngày | authentication/…/managing-your-personal-access-tokens |
| Quyền theo việc | Tạo PR: Pull requests write · nội dung: Contents · chạy workflow: Actions write · secret: Secrets write · ruleset/environment/tạo repo: Administration write · đọc rule nhánh: Metadata read | rest/authentication/permissions-required-for-fine-grained-personal-access-tokens |
| Tạo repo | `POST /user/repos`, `POST /repos/{o}/{r}/generate`; token của App có tạo được repo trong tài khoản cá nhân không **(chưa xác minh)** | rest/repos/repos |
| Issue form | `.github/ISSUE_TEMPLATE/*.yml`, `type`: `markdown`/`textarea`/`input`/`dropdown`/`checkboxes`/`upload`; schema còn public preview; dạng body sinh ra **(chưa xác minh)** | communities/…/syntax-for-githubs-form-schema |
| Sự kiện `issues` | Workflow chạy từ file ở nhánh mặc định; `author_association` có `OWNER`/`MEMBER`/`COLLABORATOR`/…; giá trị từ sự kiện phải đi qua `env:`, không nội suy vào `run:` | actions/reference/…/events-that-trigger-workflows · actions/reference/security/secure-use |
| Kích workflow | `GITHUB_TOKEN` gọi `workflow_dispatch`/`repository_dispatch` thì có run; PR do `GITHUB_TOKEN` mở không chạy tự động, PR do token App/PAT mở thì chạy | actions/how-tos/…/trigger-a-workflow |
| Rule nhánh | `GET /repos/{o}/{r}/rules/branches/{branch}` (Metadata read); ghi cần Administration write | rest/repos/rules |
| Secret | `PUT /repos/{o}/{r}/actions/secrets/{name}` với giá trị mã hoá sealed box bằng public key của repo | rest/actions/secrets |
| Environment | Repo public dùng được ở gói Free; repo private của tài khoản Free không cấu hình được; ma trận reviewer/wait timer theo gói **(chưa xác minh)** | actions/how-tos/deploy/…/manage-environments |
| `pull_request_target` | Chặn mặc định ở repo public từ 2026-12-02; brownout 2026-11-16 | github.blog/changelog/2026-11-02-pull_request_target-blocked-by-default-december-2 |
| Dependabot security updates | `PUT /repos/{o}/{r}/automated-security-fixes` (Administration write) | rest/repos/repos |
| Giới hạn | `GITHUB_TOKEN` 1.000 request/giờ/repo; token App 5.000/giờ; tạo nội dung khoảng 80/phút, 500/giờ | rest/using-the-rest-api/rate-limits-for-the-rest-api |

## 4. Hệ quả cho đặc tả

- Bản dev không cần khoá của chủ ở: máy có Docker và runner `ubuntu-latest` (Docker cài sẵn). Phiên cloud: tài liệu ghi
  Docker dùng được, phiên này chỉ thấy có `dockerd` còn daemon chưa chạy — **chạy được hay không chưa xác minh**; việc
  người dùng xem được cổng của bản dev từ ngoài phiên cũng **chưa xác minh** (không có dữ kiện). Runner còn Docker 28 —
  lệnh của gói không được dựa vào tính năng chỉ có ở 29.
- Hợp đồng của khung phải trung lập công cụ (lệnh trong `xt.yaml`); Docker/Compose là lựa chọn của gói.
- Worker ngoài phiên có ba đường: `claude -p` (tự host, có trần lượt và tiền), scheduled task trên cloud (có `/fire`, còn
  research preview), GitHub Actions. PR do worker mở cần token App/PAT thì CI mới tự chạy — đó là việc thiết lập một lần.
- Điểm phải thử trong sandbox trước khi dựa vào: exit code của `up --wait`, digest ảnh chưa push, Stop hook ở `-p`, exit
  code khi chạm trần, token App tạo repo, khởi động daemon Docker và xem cổng trong phiên cloud, API quyền cộng tác viên
  cho kênh issue (`author_association` không nói lên quyền ghi), lời gọi API tạo ref qua guard.
