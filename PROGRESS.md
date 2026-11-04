# PROGRESS.md — Khung X-Templates

> Giai đoạn hiện tại: G8 Vận hành & tiến hoá (khung 3.29.0, pha `harden` — D-136) · Cập nhật: 2026-11-04 · Nhánh: main

## Đang làm
- 2026-11-04 **PLAN-upgrade-2026-11-02** (D-304): #413…#434 merge (D-311…D-339). Xong T-3633/3634/3651/3661/3662…3667; guard: ADR-0065 (danh sách trắng mở rộng động), ADR-0066 (tệp tự ghi theo tên nhắc lại), ADR-0067 (tên dựng lúc chạy — chấp nhận có hạn), ADR-0068 (trạng thái do lệnh trước để lại — chấp nhận có hạn), luật phía đọc cấu hình git (D-336…D-338). **Đang dở:** `T-3668` (nợ review #434 — AUD-SEC-442/443/444 + có từ trước 445 🔴 `--separate-git-dir`, 447 hard link hook) → T-3635 (`audit check --strict` xanh; hiện đỏ đúng 5 dòng này) → T-3636 (`loop verify --all`; `release-check` còn hàng `review_debt` = audit delta 41+ file ngoài tài liệu đổi sau SHA quét — chạy `xt.py audit plan --status docs/ops/AUDIT-STATUS.md`, quét lại nhóm, cập nhật SHA) → perf trial T-3551/3552/3557 (PLAN-harden-2026-10-27-loops, D-258) → cắt **3.30.0**.
- Bài học vòng guard #426…#434: mỗi miễn trừ mới (dù theo giá trị) đều mở lỗ ở lượt review sau — sửa 🔴 bằng THU HỒI miễn, không vá thêm; ghi sổ nợ TRƯỚC `pr reviewed --clean` (steward merge ngay); sau review chỉ commit sổ/fixture (đổi PLAN/DECISIONS phải chờ merge).
- Phép đo `LOOP-ORCH-020` tích luỹ từ PLAN-upgrade; tăng số agent chỉ khi có số (ADR-0061). Phản hồi dự án đích: 10 nhóm `cong-cu` chờ phân loại ([TARGETS](docs/ops/TARGETS.md)).
- Hoãn tới harden: T-1690/T-1691 (quét lại SEC-091…099). Rà `seeker19110/stored`: chờ chủ repo (HAR-036/041, SEC-026, CI-006/7/9, SEC-043; hạn xét: 2026-12-31).

## Tiếp theo
0. PLAN-3.14-app (`v3.14.0`): PR nâng dự án đích chờ chủ dự án: hotel-manager #117, X-Company #65 (hạn xét: 2026-11-30). `unchecked_must` 0/64.
1. PLAN-3.13: chờ người (hạn xét: 2026-12-31) T-1834 (gỡ `merge-gate` ở ruleset hotel-manager/X-Company rồi xoá stub); **Ruleset sống X-Templates**: không `merge-gate`, `strict: true` (D-144); còn tắt resolve thread + bật "Allow auto-merge" (RUNBOOK-PR-STEWARD §1); `XT_STEWARD_TOKEN` (T-2402 lớp đỡ tạm); App reviewer.
2. Sau PLAN-3.12: ca đối kháng cho `autonomy-bench`; guard chưa quét nội dung script gọi qua `bash x.sh`/`python3 x.py` (ghi vào LOOP-STOP-027 khi làm); `project-commands.sh` được `source` hai lần mỗi task.
3. Chờ chủ repo (hạn xét: 2026-12-31): token/app reviewer (T-1508); xoá `/scratch.log` ở gốc container; `x-hotel-manager` dọn/tạo mới; Dependabot security updates (proxy chặn API); Routine tuần `feedback aggregate` + quyền repo đích (T-2410). Event policy `pull_request_target` (repo public, rule mặc định tắt từ 2026-12-02; `pr-review.yml`).
4. Còn: máy hoá `LOOP-HARNESS-031` (dấu hook theo phiên), `LOOP-STOP-030` (ConfigChange); task `[perf]` trong `loop` (D-041); URL phiên do máy chủ MCP gắn vào thân PR (PATCH lại thân PR sau khi mở); ép báo "đã đo/chưa đo" cho task UI (`LOOP-DESIGN-021`); sàn quyền token; `xt.pyz` (ADR-0010).
5. Giới hạn guard đã biết: `fd -X rm` (T-2812); tên trần glob (`s?`), glob ngoài thư mục bin, extglob, glob trong container (D-164/D-167); ghép tên hàm lúc chạy, giải mã qua `$(…)` (D-051); còn mở AUD-SEC-442…447 (T-3668); chấp nhận tới 2027-01-21: tên dựng lúc chạy (ADR-0067), trạng thái do lệnh trước để lại (ADR-0068).
6. Giữ cổng: C901 ≤ 10, `mypy --strict`, coverage dòng + nhánh 100 %, `changelog-check`, trần byte file + tổng thư mục (`tests/test_docs_budget.py`, ADR-0043) — không `noqa`/pragma, không nới trần.
7. Đánh giá sandbox Bash opt-in cho khung (`doctor` cảnh báo khi tắt) trước 2027-01-21 — ADR-0067/0068 (D-331/332/339) (tắt hook cục bộ chưa có lớp cứng khi sandbox tắt).
8. Hàng rào (hook + `settings.json`, cần Claude Code ≥ 2.1.295 — `claude_min_version`): **xét lại hàng rào 2027-01-21** hoặc khi đổi model (LOOP-DESIGN-014).

## Quyết định
> Chi tiết ở `docs/adr/` (ADR-0001…0068) và `docs/autopilot/DECISIONS.md` (D-NNN); ở đây chỉ giữ điều chưa có nhà khác.
- Khung = thư viện yêu cầu có ID + ghép blueprint + máy kiểm "xong" (ADR-0001); hook fail-open về luồng, fail-closed về hành động nguy hiểm (ADR-0002); blueprint theo quy mô S/M (ADR-0003/0004/0012).
- Luật VN: Luật 91/2025/QH15 + NĐ 356/2025 (thay NĐ 13/2023 từ 01/01/2026); Luật ANM 116/2025 (01/07/2026). OWASP LLM Top 10 2026; EU AI Act Đ.50 áp dụng 02/08/2026. Mặc định OSI: OpenTofu, Valkey.
- Repo khung: Python ≥ 3.11; `mypy --strict`; coverage 100 % (cả subprocess); `changelog-check`/`progress-check` trong `lint`; PROGRESS chỉ ghi SHA trên `main` (squash-merge). Tên: X-stored → X-Templates (ADR-0006/0007).
- Commit/PR không ghi tên model hay URL phiên AI (LOOP-HARNESS-027); tag phát hành qua `release-tag.yml` — gọi bằng REST `workflow_dispatch` (`gh workflow run` cần GraphQL, bị chặn trong phiên).
- Autopilot: tự duyệt (ADR-0008), một phiên (ADR-0009), phản hồi dự án đích (ADR-0010), cổng rỗng là đỏ (ADR-0011), `doctor --fix` đầu tiên; pha build/harden (ADR-0031), tối giản pha build (ADR-0033). Merge theo làn (ADR-0013…0016, 0020, 0024/0025, 0028/0032), steward (ADR-0027); cơ chế: merge ghim head, không auto-merge, không `merge-gate` (ADR-0036). Guard không hỏi người (ADR-0018/0019), ghi tay `.autopilot/` bị chặn (ADR-0026). Reviewer năng lực cao hơn người viết (D-161): cần review thì spawn agent mới và chỉ định `model`. Cấu hình agent theo loại việc, `max_rethink` 1/PR (ADR-0061).
- Phiên nhiều lát: mỗi lát một nhánh 1-commit từ `origin/main` (hoặc xếp chồng rồi rebase sau khi lát trước merge), mở PR tuần tự; guard chặn force-push; sửa PR đang mở khi cây bẩn → worktree riêng.
- Sửa thân PR (chân trang do máy chủ MCP gắn) từng kích `edited` → chỉ `pr-title.yml` nghe `edited`. Phiên khung không merge được PR ở repo khác → để `pr-steward` của dự án merge ghim head.
- CI không còn kiểm macOS (gỡ `portability.yml` 2026-10-17). Nợ chấp nhận: 4 MUST/module là phán đoán; số điều NĐ 356/2025 chưa đối chiếu bản gốc. Không làm (D-142): tách `xt.py`, song song worktree, merge queue, reviewer LLM mọi PR, thu nhỏ guard.

## Bàn giao phiên
- `main` `23447d8` (#434). Merge: chạy đúng `do` của `pr next` (REST ghim head) ngay khi `merge`; steward hay merge trước (`405 Merge already in progress` = đã merge). `release-check` chạy trên worktree của `main`. Sửa guard: test đỏ trước, ca `autonomy-bench` cho mỗi 🟠; luật mới OR với luật cũ (bài học #352, #372).
- Chờ người: T-1834 gỡ `merge-gate` ở ruleset hai dự án đích rồi xoá stub (hạn xét: 2026-12-31); `prod_switch` 3.29.0 (hạn xét: 2026-11-30).
- Autopilot: không chạy (phiên tương tác). `pr stats --days 7` (2026-11-04):

| PR merge trong 7 ngày (từ 2026-10-28) | Giá trị |
|---|---|
| PR đã merge | 127 |
| Lead time mở → merge (trung vị · P95) | 0.64 giờ · 3.1 giờ |
| Run CI `pull_request` mỗi PR (trung vị · P95 · tổng) | 2 · 6 · 373 |
| Run `failure` · `cancelled` (tỉ lệ) | 27 · 34 (16%) |
| PR làn chuẩn (`xt-standard-lane`) | 111 |
| PR revert | 0 |
| Push (head SHA riêng biệt) mỗi PR (trung vị · P95 · tổng) | 2 · 6 · 372 |
| PR xanh ngay lần push đầu | 100/127 (79%) |
| Run `cancelled` cùng SHA với run khác | 1 |

- Container mới: `scripts/dev-task.sh setup`; trước khi đẩy `gate-fast`, CI là cổng đầy đủ. Subagent dùng thư mục scratch riêng (bài học audit 2026-11-01).
