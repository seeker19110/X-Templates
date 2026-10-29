---
name: complete
description: Pha HARDEN — hoàn thiện dự án khi /autopilot hết việc và đề xuất /complete (hoặc người muốn phát hành): PR đặt delivery_phase: harden, audit toàn diện/delta (/audit), trả nợ review theo PR/lát, PLAN-harden (🔴/🟠, MUST blueprint còn mở, sàn Gate M/L, thiết kế đầy đủ, refactor, hiệu năng, tấn công thử) chạy cùng vòng lặp có bằng chứng với luật harden, rồi release-check GO + GO-NO-GO.md. Dùng khi người dùng muốn "hoàn thiện", "audit và sửa", "chuẩn bị phát hành", trước mỗi bản phát hành, hoặc gõ /complete.
argument-hint: "[full|delta] [phiên bản phát hành]"
---

# /complete — pha harden: audit, trả nợ, hoàn thiện, phát hành

Giao thức vòng lặp: `<FW>/11-autonomous-loop/README.md`; audit: `/audit` (`<FW>/00-method/audit.md`); cổng G7: `<XT> release-check`. File này chỉ nối các bước theo thứ tự (ADR-0046). `<FW>` = `.xtemplates/framework` (dự án đích) hoặc `framework` (repo khung); `<XT>` = `python3 .xtemplates/scripts/xt.py` (hoặc `python3 scripts/xt.py`). Sàn an toàn như `/autopilot` — không nới.

## Bước 0 — chuẩn bị
1. Tên phiên `<Tên repo> — <tên nhánh>`; `<XT> doctor --fix`; chế độ quyền Auto. Khuyến nghị phiên mới (context sạch cho audit đối kháng).
2. Đọc `delivery_phase` trong `xt.yaml`; `docs/ops/AUDIT-STATUS.md` (có sổ → `delta`, chưa → `full`); `<XT> blueprint-status BLUEPRINT.md --strict --json` (MUST mở); `<XT> loop status` (vòng build phải đã `done`/`done-pending-human`; còn `continue` → quay lại `/autopilot`); có sổ giai đoạn (`<XT> stage status`, ADR-0058): phải ở giai đoạn 2 — 1 chưa duyệt → chờ người, PLAN khai `Giai đoạn sản phẩm: 2 (C-NNN)`.

## Bước 1 — vào pha harden (một PR, một lần)
Còn `build` → PR đặt `delivery_phase: harden`, khai khoá sàn M/L (`format_check`, `coverage`, kiểm kiểu, `e2e` — `<XT> floor` liệt kê) và `attack`/`perf` (ADR-0042; chưa có công cụ → để rỗng kèm lý do) trong `xt.yaml`. PR đụng `xt.yaml` luôn tính harden (D-137): review rồi merge. Từ đây PR làn chuẩn cần review sạch ở head (`LOOP-STOP-022`), sàn Gate áp lại, guard không nới việc cục bộ.

## Bước 2 — audit và nợ review
`/audit full` (lần đầu) hoặc `/audit delta` (bản sau) đúng checklist của nó: `audit plan` → quét theo nhóm → **xác minh đối kháng 🔴/🟠** → sổ + báo cáo → kế hoạch sửa tự duyệt (D-NNN). Nợ review = file ngoài tài liệu đổi sau SHA quét, trừ file chỉ PR review sạch ở head đổi (`review_debt`, ADR-0057): chia theo PR/lát đã merge kể từ SHA đó (`gh pr list --state merged`), mỗi cụm ≤ ~150 dòng cho reviewer năng lực cao hơn người viết (`LOOP-ORCH-005`); phát hiện có đường tái hiện → vào sổ audit như 🔴/🟠/🟢.

## Bước 3 — PLAN-harden (tự duyệt)
`docs/autopilot/PLAN-harden-<ngày>.md` theo mẫu `<FW>/templates/PLAN.md`, mỗi task một Gate máy, thứ tự: (a) 🔴 rồi 🟠 — bug có test tái hiện đỏ trước khi sửa; (b) MUST blueprint còn mở — tick kèm `— Kiểm:`/`— Bằng chứng:`, `[~] — Không áp dụng:`, MUST muốn miễn → `loop defer` (người duyệt, `LOOP-STOP-024`); (c) sàn Gate M/L đỏ (`<XT> floor --run`); (d) thiết kế đầy đủ theo quy mô: C4, `API-CONTRACT.md`, `THREAT-MODEL.md`, SPEC đủ ca biên cho lát có 🔴/🟠, `PROJECT.md` (`lifecycle.md` G2–G4); (e) refactor từ nhóm CODE/ARCH có Gate (test giữ hành vi; độ phức tạp/trùng lặp đo được); (f) hiệu năng: hàng `perf` đỏ → task trong PLAN này theo `optimization-loop.md` (chỉ khi có số; `/optimize` là skill riêng sau `done` hoặc ở G8 — ADR-0048); (g) từng hàng FAIL của `<XT> release-check --json` (lần 1) thành task. Tóm tắt ≤ 30 dòng đầu PLAN → `<XT> loop decide --question "Duyệt PLAN-harden …"` → làm tiếp không chờ.

## Bước 4 — vòng lặp luật harden
`<XT> loop init --plan docs/autopilot/PLAN-harden-<ngày>.md --blueprint BLUEPRINT.md --single-session [--hours <H>]`, rồi mỗi vòng như `/autopilot` bước 5. Khác pha build: `milestone_audit: now` → audit delta trước mốc kế; mỗi lát một PR **≤ 150 dòng** (vượt → tách lát); đẩy theo `/gate` bước 4 (CI là cổng đầy đủ); diff ngoại lệ cứng → `reviewer-alt` rà **trước** khi mở PR, mở xong ghi `pr reviewed --head <SHA đã rà>` (không rà lại); `<XT> pr next` trả `review` → giao reviewer năng lực cao hơn người viết, ghi `<XT> pr reviewed` theo lệnh máy in (không kết luận được → `--inconclusive`); `rethink` → `loop decide` đổi cách (ADR-0053); `merge-watch` nền; việc cần người → `loop defer`.

## Bước 5 — phát hành (G7)
Stop hook `done` (sau `<XT> loop verify --all`) → `<XT> release-check` không NO-GO (`phase`, `stage`, `blueprint`, `audit`, `verify`, `review_debt`, `attack`/`perf`; FAIL → task mới, lặp bước 4) → `GO-NO-GO.md` theo mẫu `<FW>/templates/GO-NO-GO.md` (máy điền phần máy; **người ký** và xác nhận spec/UX/bảo mật tại dòng 20 — một lần, ADR-0048) trong PR lát cuối → có sổ: `<XT> stage submit` (người duyệt → mở giai đoạn 3) → `<XT> loop stats`, `<XT> feedback collect` → báo cáo ≤ 20 dòng: đã làm · bằng chứng · D-NNN · còn treo (đề xuất "Khi chạy thật", chữ ký) · đề xuất. Sau phát hành dự án **giữ `harden`** (ADR-0037); dựng nhanh đợt lớn mới là quyết định của chủ dự án (PR sửa `xt.yaml`).

## Không bao giờ
Nới guard/điểm dừng/cổng để xanh · tự đổi pha về `build` · bỏ xác minh đối kháng 🔴/🟠 · khai "phát hành được" khi `release-check` NO-GO hoặc chưa có chữ ký người.
