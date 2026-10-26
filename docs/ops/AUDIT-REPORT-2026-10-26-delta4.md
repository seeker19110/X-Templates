# AUDIT-REPORT — X-Templates · 2026-10-26 (delta `daefc7c..ce5d9a7`)

> Commit quét: `main` `ce5d9a7` (3.26.1, tag `v3.26.1` annotated tạo bởi `release-tag.yml`) · Phạm vi: delta `daefc7c..ce5d9a7`
> (#264 sổ delta3, #265 ADR-0049 / 3.26.0, #266–#267 GO-NO-GO v3.25.0, #268 D-192 / 3.26.1) — nhóm 1 ARCH, 2 SEC, 3 CODE, 4 TEST, 9 DOC,
> 12 XFEAT, 13 HAR theo `xt.py audit plan --status` · Lý do: `release-check` NO-GO hàng `review_debt` (`scripts/xt.py`, `tests/test_xt_loop.py`,
> `VERSION` đổi sau SHA quét `daefc7c`) · Người quét: reviewer năng lực cao nhất (`reviewer-alt`, effort max) rà **cả PR ở head** — #268 ba
> lượt (lượt 1 và 2 `--blocking`, lượt 3 sạch); #265 do phiên khác mở, máy ghi xong (`pr next` = DONE); #264/#266/#267 chỉ tài liệu ·
> Xác minh đối kháng: mọi 🟠 có đường tái hiện của reviewer và được sửa trong PR kèm test đỏ trước khi sửa; đột biến `_live_loop`
> bị bắt (A, B, F, G); không có reviewer thứ hai tái hiện độc lập · `xt.py audit check docs/ops/AUDIT-STATUS.md --strict` → exit 0

## 1. Tóm tắt

| Mức | Mở | Đã sửa | Chấp nhận | Bác bỏ |
|---|---|---|---|---|
| 🔴 | 0 | 0 | 0 | 0 |
| 🟠 | 0 | 3 | 0 | 0 |
| 🟢 | 2 | 9 | 0 | 0 |

Số đếm lấy từ báo cáo review #268 (sổ `reviews.json` chỉ lưu head/verdict). 🟠 sửa trong PR: lượt 1 — gợi `loop stop` cho mọi `blocked`
(kể cả `loop block`/lỗi lặp, nơi khung bảo `loop resume`), mẹo `XT_FRAMEWORK_LINK=framework` chưa có nhà bền; lượt 2 — chọn lối ra theo
tiền tố chữ lý do (`loop block --reason "PLAN không …"` bị gợi `loop stop`) → nay theo nguồn (`_verdict_loop_state`). Hai 🟢 mở mới từ
lượt 3 (khoảng trống test, đột biến sống): AUD-TEST-021, AUD-TEST-022. Một ghi chú không tính là phát hiện: lượt 3 🟢3 (cửa sổ µs
giữa hai lần đọc `deadline` — nghi ngờ, không tái hiện tất định, vô hại).

## 2. Phạm vi và tín hiệu

Delta mã (`git diff --stat daefc7c ce5d9a7 -- . ':!*.md'`): `scripts/xt.py` +19/−15 (`_live_loop` nói verdict + một lối ra theo nguồn,
`_loop_init` không nối đuôi trái nhau; chú thích cắt gọn — `scripts/` dưới trần ADR-0043), `tests/test_xt_loop.py` +33/−1 (2 test mới),
`VERSION`. Tài liệu: skill `/audit`, `/research`, ADR-0049, mẫu AUDIT-REPORT (#265); `BLUEPRINT.md` ghép lại (AUD-HAR-113); README
§Biến môi trường; RUNBOOK §4; GO-NO-GO v3.25.0. CI/CFG/DEP/PERF/A11Y không bị chạm; DATA N/A.

## 3. Lệnh đã chạy

| Nhóm | Lệnh | Exit | Kết quả |
|---|---|---|---|
| mọi nhóm | `scripts/dev-task.sh gate` trước mỗi lần đẩy #268 (3 lần) | 0 | coverage dòng + nhánh 100 % (12 069 stmt, 4 510 nhánh), `mypy --strict`, ruff C901 ≤ 10 |
| CODE/TEST | reviewer lượt 3: đột biến `_live_loop`/`_loop_init` (A đảo lối ra, B luôn giữ đuôi, F luôn resume, G luôn stop) | 1 | bị test bắt; C, D, E sống sót → AUD-TEST-021/022 |
| CODE/XFEAT | reviewer lượt 3: tái hiện tay 7 ca exit 2 (`continue`, `loop block`, lỗi lặp ×3, PLAN đổi tên, PLAN rỗng, block + PLAN mất, đợt `done`) | — | mỗi ca một lối ra, không còn gợi ý trái nhau |
| HAR/DOC | `XT_FRAMEWORK_LINK=framework xt.py compose --profile cli-tool --scale S --full` so không biến (reviewer lượt 1–2) | 0 | có biến: giữ 104 mục, file trùng byte `BLUEPRINT.md`; không biến: 19 mục (15 MUST + 4 SHOULD) bị đặt lại |
| SEC | grep tên model/URL phiên trên diff, commit, thân PR #268 | 1 | 0 khớp |
| HAR | `xt.py doctor`; `loop verify --all` sau tag `v3.26.1`; `release-check` | 0 | 0 lỗi; verify xanh; xem §4 |

## 4. Phát hiện mở

- **AUD-TEST-021** 🟢: nguồn `blocked` "lỗi lặp ≥ 3" (khai "→ resume" ở CHANGELOG 3.26.1) chưa có test ở `loop init` — đột biến E
  (`_verdict_loop_state(prev)` → `prev.get("blocked")`) sống sót toàn suite.
- **AUD-TEST-022** 🟢: `test_init_refuses_live_loop` (ca vòng sống `continue`) chỉ assert `LOOP-HARNESS-024` — đột biến C (mất đuôi
  `resume`/`--force`) và D (ca `continue` in `verdict \`blocked\``) sống sót.

## 5. Ghi nhận về quy trình

- `scripts/` sát trần byte (ADR-0043): mỗi sửa `xt.py` phải cắt chú thích bù — giữ.
- Container khởi động lại giữa review lượt 2 #268 (mất kết quả) — giao lại cùng phạm vi; không ảnh hưởng nhánh.
