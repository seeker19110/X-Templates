---
title: Xưởng đầu-cuối — ý tưởng tới bản dev không cần người; khoảng hở của dây chuyền và ba quyết định của chủ dự án
kind: research
updated: 2026-11-11
---

# Xưởng đầu-cuối: dây chuyền còn hở ở đâu — nghiên cứu 2026-11-11

Đầu vào: chủ dự án 2026-11-11 *"với tầm nhìn xưởng lập trình phần mềm tự động từ đầu đến cuối thì dự án cần bổ sung nâng
cấp những gì? con người chỉ nêu ý tưởng và ra sản phẩm để deploy… yêu cầu phải nhanh, tự động hoàn toàn và chất lượng"*.
Khung ở 3.33.0, `main` `e1c74e6`. Nối tiếp [định hướng xưởng 2026-11-04](2026-11-04-software-factory-direction.md)
(ADR-0068) và [tự động hoá 2026-11-08](2026-11-08-full-automation.md); quyết định ở
[ADR-0075](../docs/adr/0075-end-to-end-factory.md), việc ở
[PLAN-factory-e2e](../docs/autopilot/PLAN-factory-e2e.md). Ghi chú này chỉ đọc repo; dữ kiện ngoài chưa tra (§5).

## 1. Kết luận

Khúc giữa của dây chuyền (PLAN → mã → PR → merge → `release-check`) đã do máy chạy. Hai đầu còn hở: từ "ý tưởng" tới một
repo đang chạy autopilot, và từ artifact tới một bản thật sự chạy ở đâu đó. Không dự án đích nào có bản triển khai được
khung ghi nhận; mốc xét lại của ADR-0068 ("lát A xong mà chưa dự án đích nào deploy thật") đã tới.

## 2. Dây chuyền theo trạm (đọc ở `e1c74e6`)

| Trạm | Đã có | Còn thiếu | Bằng chứng |
|---|---|---|---|
| 1 Nhận ý tưởng | `/autopilot "<mô tả>"`, tự duyệt quyết định (ADR-0008) | Người tạo repo, chạy `install.py`, mở phiên, chọn chế độ quyền; không có kênh vào ngoài phiên | `.claude/skills/autopilot/SKILL.md` bước 0; `install.py` không có cờ tạo dự án mới |
| 2 Dựng nền | `install.py --pack`, một gói API | Không UI, không ảnh container, không đích chạy | `framework/templates/packs/web-api-ts/README.md` ("không UI; không staging/deploy thật") |
| 3 Xây | Vòng lặp có bằng chứng; `topo: parallel` khi `files:` không giao, đợt ≤ 4 | Mặc định `self`; `files:` là lời khai (bằng chứng chỉ lưu danh sách + digest, không so diff thật); worker ngoài phiên chưa có | `xt.py` `evidence_meta`; `orchestration-and-subagents.md` bảng topology; T-3555 còn `[ ]` |
| 4 Kiểm | Gate, CI, review theo làn, audit, mutant của gói | Người viết mã cũng viết kiểm thử nghiệm thu; không có bộ nghiệm thu khoá với người viết | tìm trong `framework/11-autonomous-loop`, `14-testing-quality`: không có cơ chế |
| 5 Phát hành | `release-check`, `subject.digest`, `release-sign` | Agent chỉ ký ở `scale: S`; chữ ký không chặn tag hay phân phối | ADR-0074 §Quyết định; research 2026-11-08 §8 luận điểm 1 |
| 6 Triển khai | Mục `OPS-DEPLOY-*`, khoá `preview`/`rollback` | Không khoá `deploy`, không receipt, không smoke sau triển khai, không tự quay lui | `framework/templates/xt.yaml`; `docs/ops/registry.json`: 4/4 dự án `environments: []`, `release: null`, `pack: null` |
| 7 Vận hành, học | `/optimize`, `/incident`, `feedback aggregate` | Số field do người xuất; Routine tuần không đẩy được; 10 nhóm phản hồi chờ phân loại | `LOOP-OPT-016`; `PROGRESS.md` §Bàn giao |

Số đo dòng giao hàng gần nhất (`pr stats --days 7`, 2026-11-05, ở `PROGRESS.md`): 112 PR merge, lead time trung vị 0,7
giờ, xanh ngay lần đẩy đầu 77 %. Chưa có phép đo cho: thời gian từ ý tưởng tới bản chạy, thời gian chờ người, lỗi lọt
sau merge, chi phí mỗi lát.

## 3. Ba câu hỏi và trả lời của chủ dự án (2026-11-11)

| Câu hỏi của phiên | Trả lời | Hệ quả |
|---|---|---|
| Song song hay giữ tuần tự (D-142)? | "song song nếu không chạm cùng file" | Thay phần "không song song worktree" của D-142 và mặc định `self` của ADR-0061; điều kiện phải do máy kiểm |
| Khi nào làm các việc chỉ chủ làm được (App/token, đích + khoá, trần chi phí, bật khoá)? | "thiết lập sau khi lên bản dev" | Đường tới bản dev không được cần việc người nào; gom việc người thành một checklist in ra khi bản dev xanh |
| Tự động tới quy mô nào? | "ở mọi quy mô" | Bỏ giới hạn `scale: S` của `release-sign`, mở giai đoạn 2/3, đối chiếu các MUST buộc người ở M/L |

Cách hiểu "bản dev" của phiên (ghi để chủ sửa nếu lệch): bản ứng viên có digest, chạy ở môi trường tự host không cần
tài khoản hay khoá của chủ, smoke xanh, có receipt máy đọc.

## 4. Điểm phải giữ khi làm

- Luật bất đối xứng (research 2026-11-08 §1): máy tự siết được; nới chỉ qua PR đổi khoá `HARD_GATED_KEYS` do người merge
  một lần. "Mọi quy mô" là năng lực có sẵn ở mọi quy mô, không phải khoá tự bật.
- Bảy loại "máy không thể" (cùng nguồn §3) không đổi theo quy mô: tiền, dữ liệu người dùng thật, pháp nhân đứng tên vẫn
  qua `grant` và `loop defer`. Đính chính 2026-11-12: nguồn 2026-11-08 xếp dòng 20 GO-NO-GO ("người đã dùng thử", M/L) vào
  nhóm này; ADR-0075 quyết định **thay** dòng đó bằng hàng bằng chứng máy "máy mô phỏng" (ADR-0048 §Quyết định 1) — nên
  nhóm không đổi chỉ đúng với tiền/dữ liệu thật/pháp nhân.
- "Qua cổng của máy" chưa phải "đúng ý định" (cùng nguồn §4, số METR; chưa tra lại hôm nay). Bỏ chữ ký người ở M/L mà
  không có nghiệm thu độc lập là giảm chất lượng — nên cơ chế bù phải merge trước phần nới.
- File mọi PR cùng chạm (`PROGRESS.md`, `CHANGELOG.md`, sổ quyết định, sổ audit) làm "không chạm cùng file" luôn sai nếu
  không đổi cách ghi.
- Ràng buộc còn hiệu lực: không tách `xt.py`, một gói trong 3.x (ADR-0068), trần byte (ADR-0043; nhóm `scripts` đo
  hôm nay 1.303.886 B / 1.760.431 B).

## 5. Chưa xác minh (việc của T-3866)

Công cụ và phiên bản cho ảnh container/compose, runner CI cho bản dev, khả năng hiện hành của worktree, phiên headless và
scheduled task của Claude Code, GitHub App manifest: chưa tra nguồn sống trong ghi chú này — không chọn công nghệ ở đây.

## 6. Nhật ký xác minh (2026-11-11, `e1c74e6`)

| Mục | Lệnh | Kết quả |
|---|---|---|
| Registry không có bản triển khai | đọc `docs/ops/registry.json` | 4 sản phẩm, `environments: []`, `release: null`, `pack: null` |
| Mẫu không có khoá deploy | `grep -n "deploy" framework/templates/xt.yaml` | chỉ chú thích; có `preview`, `rollback`, `release_artifacts` |
| Gói không triển khai | `grep -n deploy framework/templates/packs/web-api-ts/README.md` | dòng 45 |
| `files:` không so diff thật | đọc `evidence_meta`, `evidence_stale` trong `scripts/xt.py` | `scope` = danh sách đã khai + digest |
| Song song đã có ở mức task | `xt.py plan waves --help`; bảng topology | `--max` mặc định 4; thiếu `files:` → đứng riêng |
| Agent ký chỉ ở S | `docs/adr/0074-agent-release-signoff.md` §Quyết định | "`BLUEPRINT.md` khai `scale: S`" |
| Trần nhóm `scripts` | `git ls-files -z -- 'scripts/*.py' scripts/xt_app/ \| xargs -0 cat \| wc -c` | 1.303.886 B |
| PR mở có trùng số ADR/D/T | liệt kê PR mở của repo | chỉ #482, #483 (Dependabot) |
