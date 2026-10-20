# PROGRESS.md — Khung X-Templates

> Giai đoạn hiện tại: G8 Vận hành & tiến hoá (khung 3.10.0, pha `build`) · Cập nhật: 2026-10-20 · Nhánh: main

## Đang làm
- 2026-10-20 **PLAN-3.12-lean** (`docs/autopilot/PLAN-3.12-lean.md`, D-111, yêu cầu chủ repo "tối ưu toàn bộ, cả dự án đích"): Lát 1 tài liệu một nhà — PR #190 (head `8c94d97`; 2 vòng review đã đóng 7 🟠 + 4 🟢, chờ review lần 3 rồi merge; AGENTS 13,6→7,2 KB, mẫu AGENTS 15,9→8,2, CLAUDE 5,5→1,6, skill autopilot 17,5→6,1, README 11 20→11). Lát 2 harness (trong cây làm việc, chờ #190 merge để mở PR): Stop/PreCompact thoát sớm (260→7 ms), auto-format không gọi guard cho mẫu dựng sẵn, cổng commit đụng cấu hình = mọi lớp test không coverage (D-112), `xt.py checks`, `gate`/`gate-fast` hỏi guard MỘT lần (`guard-check --stdin`, T-1715), guard nạp từ nguồn không đọc pyc (T-1716), tách `CommitGateFastHookTest` 3 lớp ≤ 18 s + weights, `doctor --drift` đọc nhãn có SHA, `merge-watch` in `pr next` + `loop record` tự tick PLAN (D-113), `release-check` dùng lại verify; gộp phần công cụ của Lát 3: mẫu `xt.yaml` 9,1→3,1 KB, `install.py` hash file gốc + in bước "Dự án đích" + nối khoá mới (D-114). Lát 3 còn: cắt bản, tag, nâng hotel-manager/X-Company (đang 3.7.1), PROGRESS ≤ 6 KB.
- 2026-10-20 #189 merged (ADR-0033, D-110): pha build không audit theo mốc (`milestone_audit: g7`), reviewer chỉ khi `pr next` trả `review`, PROGRESS theo lát.
- Hoãn tới pha `harden`: PLAN-3.11 T-1690 (quét lại theo diff bản sửa SEC-091…099, sổ ghi SHA quét mới) và T-1691 `release-check` GO (hiện NO-GO đúng thiết kế vì `phase: build`).
- Rà `seeker19110/stored` 2026-10-18: chờ chủ repo HAR-036/041, SEC-026, CI-006/007/009, SEC-043 (#97).

## Tiếp theo
1. Sau PLAN-3.12: đặt `delivery_phase: harden` khi vào giai đoạn hoàn thiện → audit delta → `release-check`; 🟢 mở đáng làm: AUD-TEST-019 (`test-weights` gà–trứng), AUD-SEC-100 (`git -C ~+/x`); ca đối kháng do reviewer khác họ model viết cho `autonomy-bench` (hiện 0).
2. Chờ chủ repo: secret `XT_RELEASE_TOKEN` (đẩy tag khi commit đổi workflow), token/app reviewer (T-1508), xoá `/scratch.log` ở gốc hệ thống file container; hotel-manager thêm `merge-gate` vào required check; `x-hotel-manager` dọn/tạo mới.
3. Còn: task `[perf]` trong `loop` (D-041); URL phiên do máy chủ MCP tự gắn vào thân PR (ngoài tầm guard — PATCH lại thân PR sau khi mở); ép báo "đã đo/chưa đo" cho task UI (`LOOP-DESIGN-021`); sàn quyền token; `xt.pyz` (ADR-0010).
4. Giới hạn đã biết của guard: ghép tên hàm lúc chạy, giải mã qua `$(…)` (D-051); env `GIT_CONFIG_*`; CLI container ngoài docker/podman (AUD-SEC-042); chặn oan script Python chỉ đọc nhắc `.claude/hooks`/`.autopilot` (D-105).
5. Admin: Dependabot security updates (proxy chặn API); ô "extra approval for unattributed changes" của ruleset `main`.
6. Giữ cổng: C901 ≤ 10, `mypy --strict`, coverage dòng + nhánh 100 %, `changelog-check` — không `noqa`/pragma.

## Quyết định
> Chi tiết ở `docs/adr/` (ADR-0001…0033) và `docs/autopilot/DECISIONS.md` (D-NNN); ở đây chỉ giữ điều chưa có nhà khác.
- Khung = thư viện yêu cầu có ID + ghép blueprint + máy kiểm "xong" (ADR-0001); hook fail-open về luồng, fail-closed về hành động nguy hiểm (ADR-0002); blueprint theo quy mô S/M (ADR-0003/0004/0012).
- Luật VN: Luật 91/2025/QH15 + NĐ 356/2025 (thay NĐ 13/2023 từ 01/01/2026); Luật ANM 116/2025 (01/07/2026). OWASP LLM Top 10 2026; EU AI Act Đ.50 áp dụng 02/08/2026. Mặc định OSI: OpenTofu, Valkey.
- Repo khung: Python ≥ 3.11; `mypy --strict`; coverage dòng + nhánh 100 % (cả subprocess); `changelog-check`/`progress-check` trong `lint`; PROGRESS chỉ ghi SHA trên `main` (squash-merge). Tên: X-stored → X-Templates (ADR-0006/0007).
- Commit/PR không ghi tên model hay URL phiên AI (LOOP-HARNESS-027); tag phát hành qua workflow `release-tag.yml` (proxy chặn push tag).
- Autopilot: tự duyệt (ADR-0008), một phiên (ADR-0009), phản hồi dự án đích (ADR-0010), cổng rỗng là đỏ (ADR-0011), `doctor --fix` đầu tiên; pha build/harden (ADR-0031), tối giản pha build (ADR-0033). Merge: máy quyết theo làn (ADR-0013…0016, 0020, 0024/0025, 0028/0032), steward trên GitHub (ADR-0027). Guard không hỏi người (ADR-0018/0019), ghi tay `.autopilot/` bị chặn (ADR-0026).
- Phiên bị ràng buộc một nhánh → lát đi tuần tự; sau mỗi merge gộp `origin/main` vào nhánh (guard chặn force-push).
- CI không còn kiểm macOS (gỡ `portability.yml` 2026-10-17 theo chủ repo). Nợ chấp nhận: 4 MUST/module là phán đoán; số điều NĐ 356/2025 chưa đối chiếu bản gốc.

## Bàn giao phiên
- 2026-10-20 · Commit cuối trên `main`: `35f1e49` (#189); tag mới nhất `v3.10.0` → `31abded`; PLAN-3.12-lean đang chạy một phiên trên nhánh `seeker/jolly-bohr-hg41oi` (PR #190 Lát 1 chờ review lần 3 + merge; Lát 2 chờ commit sau đó).
- Lệnh kiểm nhanh: `scripts/dev-task.sh gate` (`pip install --require-hashes -r requirements-dev.txt`, cần shellcheck; hook cổng commit dùng python hệ thống).
- Autopilot: `loop status`. Đang chặn: không. Câu hỏi cần người: Tiếp theo 2.
