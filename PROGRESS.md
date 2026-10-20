# PROGRESS.md — Khung X-Templates

> Giai đoạn hiện tại: G8 Vận hành & tiến hoá (khung 3.10.0) · Cập nhật: 2026-10-20 · Nhánh: main

## Đang làm
- 2026-10-20 PR #189 (ADR-0033, D-110): tối giản autopilot ở pha build — `loop status` thêm `milestone_audit` (`g7` ở build: không audit theo mốc, gom về trước G7), skill `/autopilot` bước 10 theo `pr next` (reviewer chỉ khi `do` = `review`), PROGRESS theo lát. Review sạch (`reviewer-alt`), chờ merge.
- 2026-10-20 PLAN-3.11 (`docs/autopilot/PLAN-3.11-audit-delta.md`, D-108): `release-check` tại `0afa30d` NO-GO vì `review_debt` → audit delta `f36ea90..0afa30d` (`docs/ops/AUDIT-REPORT-2026-10-20-delta2.md`): 🔴 SEC-091 (byte dấu che làm guard fail-open — hồi quy #186), 🟠 SEC-093/094/097, sau đó 🔴 SEC-099 (`rm -rf $PWD/..` lọt) + 17 🟢; đã sửa hết 🔴/🟠 trên nhánh `seeker/intelligent-fermat-aq178u`, bench 438 ca 0 false-green. Còn: PR + review khác họ model, T-1690 quét lại theo diff bản sửa, T-1691 `release-check`.
- 2026-10-20 3.10.0 đã merge (#173…#177 trên `main`): PLAN-3.9 T-1501…T-1524 (evidence v2, `loop next/context/ci-triage`, hook task-completed/subagent-stop, steward theo sự kiện, `doctor --drift`, `install --plan` + manifest, `compose --feature` ADR-0030, `autonomy-bench` 291 ca, guard sửa SEC-072/077/078…081); tên phiên bắt buộc (#175); **`delivery_phase: build|harden`** (#176, ADR-0031: pha build PR chỉ cần CI xanh, ghi nợ review; `release-check` chặn bằng `phase` + `review_debt`; repo khung giữ `harden`, mẫu dự án đích đặt `build`); **`commit_gate: fast|full`** (#177: commit chạy `gate-fast`, cổng đầy đủ ở bước mở PR/CI; commit đụng cấu hình cổng luôn chạy đầy đủ). Tag `v3.10.0` → `31abded` đã có (không có `v3.9.0`: `main` chưa từng mang VERSION 3.9.0). #179–#184 đã merge: CI song song (build/typecheck/lint/test 4 shard/coverage/py311/checks, `quality` chỉ tổng hợp), tách test nặng, guard không liệt kê `/tmp`, đóng 11 🟠 audit + `license-check` + ADR-0032 (#182), miễn `BASE-GATE-009` (#183), `BASE-REPO-006` đạt (#184); #185/#186 sửa audit delta lần 1 + review (SEC-083…090). Còn: ca đối kháng do reviewer khác họ model viết = 0.
- 2026-10-19 3.8.0: sửa audit delta #94–#157 (D-064, D-065, D-071; chi tiết CHANGELOG [3.8.0]); sổ `docs/ops/AUDIT-STATUS.md`.  Tag `v3.8.0` → `c857fa0` đã có.
- 3.7.1: PR đủ điều kiện là merge ghim head ngay; không bật auto-merge khi nhánh đích thiếu check bắt buộc (#155/#156, D-062/D-063). 3.7.0: steward tự cập nhật nhánh tụt base, review sạch mang qua merge base không chạm file PR (#153, D-061); `merge-check` báo thiếu check bắt buộc (#150/#151, D-060); tên phiên `<repo> — <nhánh>` (#152, LOOP-HARNESS-028). 3.6.0: bàn giao UI/UX stored 06 §7i (#148, D-059: `vendor-check` kiểm skill chép vào `.claude/skills`, mã SPDX CC-BY-NC, `SOURCE` cần `License:`; chữ lớn 24 px/18,66 px đậm). 3.5.1 phát hành (#145/#146, D-058: steward ở repo org, `pr_title_check` đọc nhánh đích, nhãn lỗi không bật auto-merge); hotel-manager#84, X-Company#21 đã nâng. 3.5.0: guard ghi công AI qua `gh pr`/MCP, `merge-check` kiểm tiêu đề PR (#140, D-055…057); PR steward (#141, ADR-0027, D-054).
- Rà `seeker19110/stored` 2026-10-18 (`10ecf8b..a1a1f51`): #117 guard, #118 mục checklist mới, PR harness. Chờ chủ repo: HAR-036/041, SEC-026, CI-006/007/009, SEC-043 (#97).

## Tiếp theo
0. PLAN-3.11: sau khi PR merge — T-1690 (quét lại diff bản sửa, sổ ghi SHA quét mới), `loop verify --all`, T-1691 `release-check`; 🟢 mở đáng làm: AUD-TEST-019 (`test-weights` gà–trứng), AUD-SEC-100 (`git -C ~+/x`); giao `reviewer`/`reviewer-alt` viết ca đối kháng cho `autonomy-bench`; chờ chủ repo: secret `XT_RELEASE_TOKEN` (đẩy tag khi commit đổi workflow), token/app reviewer (T-1508), xoá `/scratch.log` ở gốc hệ thống file của container (executor lỡ tạo).
1. Còn: task `[perf]` trong `loop` (D-041); URL phiên do máy chủ MCP tự gắn vào thân PR (ngoài tầm guard).
2. hotel-manager: chủ repo thêm `merge-gate` vào required check ruleset `main`. `x-hotel-manager`: chờ chủ repo quyết dọn/tạo mới.
3. Hoãn từ rà stored: ép báo "đã đo/chưa đo" cho task UI trong `loop` (`LOOP-DESIGN-021` chưa có máy đỡ); sàn quyền token; `xt.pyz` (ADR-0010).
4. Giới hạn đã biết của guard: ghép tên hàm lúc chạy, giải mã qua `$(…)` (D-051); env `GIT_CONFIG_*`; CLI container ngoài docker/podman (AUD-SEC-042).
5. Admin: Dependabot security updates (proxy chặn API); ô "extra approval for unattributed changes" của ruleset `main`.
6. Giữ cổng: C901 ≤ 10, `mypy --strict`, coverage dòng + nhánh 100%, `changelog-check` — không `noqa`/pragma.

## Quyết định
> Chi tiết ở `docs/adr/` (ADR-0001…0032) và `docs/autopilot/DECISIONS.md` (D-NNN); ở đây chỉ giữ điều chưa có nhà khác.
- Khung = thư viện yêu cầu có ID + ghép blueprint + máy kiểm "xong" (ADR-0001); hook fail-open về luồng, fail-closed về hành động nguy hiểm (ADR-0002); blueprint theo quy mô S/M (ADR-0003/0004/0012).
- Luật VN: Luật 91/2025/QH15 + NĐ 356/2025 (thay NĐ 13/2023 từ 01/01/2026); Luật ANM 116/2025 (01/07/2026). OWASP LLM Top 10 2026; EU AI Act Đ.50 áp dụng 02/08/2026. Mặc định OSI: OpenTofu, Valkey.
- Repo khung: Python ≥ 3.11; `mypy --strict`; coverage dòng + nhánh 100% (cả subprocess); `changelog-check`/`progress-check` trong `lint`; PROGRESS chỉ ghi SHA trên `main` (squash-merge).
- Tên: X-stored → X-Templates; định danh `.xtemplates/`, `xt.py`, `xt.yaml`, `XT_*` (ADR-0006 → ADR-0007).
- Commit/PR không ghi tên model hay URL phiên AI (AGENTS.md §3, LOOP-HARNESS-027); tag phát hành qua workflow `release-tag.yml` (proxy chặn push tag).
- Autopilot: phiên chính tự duyệt (ADR-0008), một phiên đến khi xong (ADR-0009), phản hồi dự án đích (ADR-0010), cổng rỗng là đỏ (ADR-0011), `doctor --fix` đầu tiên (LOOP-HARNESS-020).
- Merge: máy quyết (ADR-0013/0014), L3 (ADR-0015), ngoại lệ cứng (ADR-0016/0020), theo làn `pr next` (ADR-0024/0025), steward trên GitHub (ADR-0027). Chủ repo đừng merge tay PR đang chờ review (#107 → #108).
- Guard: không hỏi người, chặn hành động không đảo ngược (ADR-0018/0019); ghi tay `.autopilot/` bị chặn (ADR-0026); ngân sách quét (D-050); `pr reviewed --clean` đòi reviewer khác họ model (D-045).
- Audit có máy đỡ, `audit check --strict` = Definition of Complete (ADR-0005). Autopilot bớt lời khai: `— Kiểm:` chạy lại, sàn Gate M/L, `loop stats`, `pr next` (D-034…038); vòng tối ưu hiệu năng (D-041/042); bộ tấn công guard (D-044); cổng UI `contrast`/`vendor-check` (D-048/049); guard trong container (D-015).
- CI không còn kiểm macOS (gỡ `portability.yml` 2026-10-17 theo chủ repo).
- Nợ kỹ thuật chấp nhận: chọn 4 MUST/module là phán đoán; số điều cụ thể của NĐ 356/2025 chưa đối chiếu bản gốc — trả khi audit dự án thật.

## Bàn giao phiên
- 2026-10-20 · Commit cuối trên `main`: `0afa30d` (#186); tag mới nhất `v3.10.0` → `31abded`, `v3.8.0` → `c857fa0`, `v3.7.1` → `9433792`, `v3.7.0` → `4d6d439`, `v3.6.0` → `18b5113`, `v3.5.1` → `794570e`, `v3.5.0` → `cf35b70`, `v3.4.1` → `bbb96ec`, `v3.4.0` → `b20e6e6`, `v3.3.0` → `27e6bc3`; PLAN-3.11 đang chạy.
- Lệnh kiểm nhanh: `scripts/dev-task.sh gate` (`pip install --require-hashes -r requirements-dev.txt`, cần shellcheck; hook cổng commit dùng python hệ thống).
- Autopilot: PLAN-3.11 một phiên (`loop status`). Đang chặn: không.
- Câu hỏi cần người: Đang làm (chờ chủ repo), Tiếp theo 2.
