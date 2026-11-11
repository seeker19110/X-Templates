# SPEC-factory-scale — Agent ký và duyệt ở mọi quy mô

| Trường | Giá trị |
|---|---|
| ID tính năng | F-141 (ký phát hành ở M/L), F-142 (duyệt giai đoạn 2/3), F-143 (mục MUST buộc người), F-144 (chữ ký chặn phân phối) — chủ dự án 2026-11-11 "ở mọi quy mô", ADR-0075 §Quyết định 4 |
| Trạng thái | Approved for implementation (phiên chính tự duyệt, ADR-0008 — D-422; sửa sau review độc lập — D-423) |
| Phiên bản | 1 |
| Kiến trúc | [ADR-0075](../adr/0075-end-to-end-factory.md), [ADR-0074](../adr/0074-agent-release-signoff.md), [ADR-0069](../adr/0069-agent-stage-approval.md), [ADR-0048](../adr/0048-optimize-skill-and-field-loop.md) (nhà của dòng 20 GO-NO-GO) |
| Kế hoạch | [`PLAN-factory-e2e.md`](../autopilot/PLAN-factory-e2e.md) T-3855…T-3858 — F-144 (cơ chế bù) làm trước; F-141/F-142 chỉ sau [SPEC-factory-acceptance](SPEC-factory-acceptance.md) và [SPEC-factory-deploy](SPEC-factory-deploy.md) |

## 1. User story
Là chủ dự án, tôi muốn agent ký phát hành và duyệt giai đoạn ở cả M và L khi máy đã có đủ bằng chứng thay cho việc tôi
dùng thử, để quy mô không còn là lý do dây chuyền dừng chờ tôi — nhưng dự án đã bật quyền ở mức S không tự nhiên được
nới lên M/L khi nâng khung.

Ghi chú phạm vi: "ở mọi quy mô" của chủ dự án nói về S/M/L. Việc mở **giai đoạn 2/3** (F-142) là cách phiên hiểu rộng
câu đó, nối lát S10 của research 2026-11-08 — giới hạn "agent chỉ duyệt giai đoạn 1" không phụ thuộc quy mô. Chủ dự án
không muốn thì bỏ F-142 mà không ảnh hưởng F-141.

## 2. Giao ước

### 2.1 Hai khoá trần, đều thuộc `HARD_GATED_KEYS`
| Khoá `xt.yaml` | Giá trị | Mặc định (vắng) | Nghĩa |
|---|---|---|---|
| `release_signoff_scale` | `S` \| `M` \| `L` | `S` | Quy mô blueprint lớn nhất mà `release-sign` được ký (cần `release_signoff: agent`) |
| `stage_approval_max` | `1` \| `2` \| `3` | `1` | Giai đoạn lớn nhất agent được `stage approve` (cần `stage_approval: agent`) |

- Giá trị có hiệu lực = **mức thấp hơn** giữa cây làm việc và nhánh chính của remote; vắng ở một bên = mặc định.
- Bản ở nhánh chính đọc **mới từ remote** theo đúng đường `release-sign` đang đọc `release_signoff` (bản mirror vừa
  clone), không tin ref cục bộ: chủ dự án hạ khoá trên remote thì phiên chưa fetch cũng thấy.
- PR đổi khoá luôn người merge. Mẫu dự án đích để trống. Giá trị lạ → coi như mặc định và `doctor` báo ✗.

### 2.2 `release-sign` ở M/L (F-141)
Giữ mọi điều kiện của ADR-0074, thay điều kiện "`scale: S`" bằng "`scale` ≤ `release_signoff_scale`", và ở M/L đòi thêm
— thiếu một điều thì từ chối (exit 2, không ghi file):

| # | Điều kiện thêm ở M/L | Nguồn |
|---|---|---|
| 1 | Hàng `acceptance_lock` PASS | SPEC-factory-acceptance |
| 2 | Hàng `deploy` có mặt và PASS | SPEC-factory-deploy |
| 3 | Không hàng nào của `attack`, `perf`, `migration_check`, `acceptance`, `rollback` là N/A — phải PASS | ADR-0042, ADR-0062 §6 |
| 4 | **Lệnh của các hàng 1–3 trùng bản ở nhánh chính**: giá trị các khoá `attack`, `perf`, `migration_check`, `acceptance`, `rollback`, `deploy_dev`, `smoke_dev`, `digest_dev`, `rollback_dev` ở cây làm việc phải giống bản đã commit ở nhánh chính của remote — phiên không tự đổi lệnh thành thứ luôn xanh rồi tự ký | mới |
| 5 | Dòng 20 của GO-NO-GO ("người đã dùng thử") **còn trống**: người đã ghi bất kỳ kết quả nào (kể cả FAIL mà chưa ký NO-GO ở §5) → agent không ghi đè, không ký | mới |
| 6 | Ở L: `escaped` = 0 trong 14 ngày gần nhất; `escaped` là `null` (không đo được) → từ chối. Cửa sổ 14 ngày là hằng số trong mã, không phải khoá | SPEC-factory-parallel F-134 |

Khi ký ở M/L, `release-sign` ghi vào dòng 20 kết quả `MÁY MÔ PHỎNG` kèm ba bằng chứng (khoá `A-NNN`, digest bản dev,
hàng `rollback`) và câu "chưa có người dùng thật dùng thử". Dòng ký vẫn ô tên `agent`. `release-check --json` thêm
`promotion.simulated: true` cho bản ký kiểu này.

### 2.3 `stage approve` giai đoạn 2 và 3 (F-142)
Agent duyệt giai đoạn N khi N ≤ `stage_approval_max`, bản trình còn nguyên (ADR-0069), và **tiêu chí của giai đoạn**
đạt trên đúng bản đã trình. Tiêu chí là hằng số trong mã; lệnh của các hàng liên quan phải trùng bản ở nhánh chính như
§2.2 điều 4:

| Giai đoạn | Tiêu chí máy |
|---|---|
| 1 MVP | như hiện nay (`preview_smoke` lúc `stage submit`) |
| 2 hoàn thiện | `release-check` không có hàng FAIL; `acceptance_lock` PASS; hàng `deploy` có mặt và PASS |
| 3 tối ưu | như 2, và hàng `perf` PASS (không N/A) |

`init --adopt` vẫn chỉ người.

### 2.4 Mục MUST buộc người (F-143)
Mỗi mục trong danh sách của research 2026-11-08 §8 "Soát thiếu" được xếp đúng một lớp, ghi ở một bảng máy đọc trong
`framework/11-autonomous-loop/stop-points-and-escalation.md` (nhà duy nhất); mục giữ ID và mức.

| Lớp | Nghĩa | Thay đổi ở mục |
|---|---|---|
| A — theo khoá | Người, hoặc agent khi khoá ở nhánh chính cho phép và hàng bằng chứng máy đạt | Thêm vế "hoặc … khi `<khoá>`" và trỏ khoá |
| B — việc người thật | Tiền, dữ liệu thật, pháp nhân đứng tên, khẩu vị rủi ro, trải nghiệm người thật | Không đổi; vào checklist của `admin-plan`; không nằm trên đường tới bản dev |
| C — máy làm bằng công cụ | Có lệnh kiểm thay được thao tác tay | Đổi `→ Kiểm:` thành lệnh |

Xếp lớp tạm (T-3857 đọc lại từng mục; không chắc → B):

| Lớp | Mục |
|---|---|
| A | `WF-REVIEW-007`, `WF-ENV-008`, `PM-HANDOVER-006`, `WF-SDD-010`, `PM-PLAN-005` (phần deploy/publish) |
| B | `OPS-IR-006`, `OPS-IAC-006`, `SEC-TM-007`, `SEC-LOG-013`, `CMP-AUDIT-004`, `CMP-AI-001`, `UX-A11Y-017`, `WF-TEAM-006` |
| chưa xếp | `WF-REVIEW-004`, `SEC-SUPPLY-011`, `SEC-SECRET-010` |

Hệ quả phải nói thẳng: mục lớp B là MUST đang áp dụng trong blueprint thì bản phát hành vẫn `pending_human` cho tới khi
người làm xong việc đó (hoặc người ghi `Miễn:`). "Mọi quy mô" bỏ chữ ký và việc dùng thử, không bỏ các việc này.

### 2.5 Chữ ký chặn phân phối (F-144) — cơ chế bù, làm trước F-141/F-142
`promotion.state` là trạng thái **tức thời** (mất khi chữ ký quá hạn hoặc cây đổi), nên không dùng nó làm thuộc tính bền
của một bản. Thuộc tính bền là **tag do workflow có cổng tạo**:

- `release-tag.yml` (khung và mẫu dự án đích): trước khi tạo tag `vX.Y.Z`, chạy `xt.py release-check --json` **trên đúng
  commit sẽ gắn tag**; `promotion.state` khác `approved` → job đỏ, không tag. Tag chỉ tạo qua workflow này (luật sẵn có).
- `install.py` ghi nguồn cài vào manifest: `source: {tag: "vX.Y.Z"}` khi HEAD của nguồn đúng là commit của một tag phiên
  bản, ngược lại `source: {untagged: "<sha>"}`. Cài từ cây đang phát triển và trong CI **không bị chặn** (hành vi hiện
  nay giữ nguyên).
- `doctor` ở dự án đích và `xt.py registry` ở khung báo sản phẩm đang chạy khung `untagged`.
- Việc phân phối tự động (PR nâng dự án đích — SPEC-factory-learning F-163) chỉ cài từ checkout của tag.

## 3. Tiêu chí chấp nhận

### S-501 Nâng khung không nới ngầm
- Given dự án M có `release_signoff: agent` ở nhánh chính, không có `release_signoff_scale`
- When `xt.py release-sign --note x` · Then exit 2 "quy mô M vượt `release_signoff_scale` (S)", file không đổi

### S-502 Ký ở M khi đủ bằng chứng máy
- Given `release_signoff_scale: M` ở cây và nhánh chính; `release-check` không FAIL; sáu điều kiện §2.2 đạt; chỉ còn `go_no_go`
- When `release-sign --note x`
- Then exit 0; §5 có dòng `agent`; dòng 20 ghi `MÁY MÔ PHỎNG` + ba bằng chứng; `promotion.state` = `approved`,
  `promotion.simulated` = true

### S-503 Thiếu một hàng bằng chứng máy (Scenario Outline)
- Given như S-502 nhưng `<hàng>` ở trạng thái `<trạng thái>` · When `release-sign` · Then exit 2 nêu `<hàng>`
- Examples: `acceptance_lock` FAIL · `deploy` FAIL (digest lệch) · `deploy` vắng (chưa khai môi trường) · `perf` N/A · `rollback` N/A

### S-504 Khoá chỉ ở một bên, hoặc hai bên khác nhau
- Given `release_signoff_scale: L` ở cây, nhánh chính không khai · When `release-sign` ở dự án M · Then exit 2
- And Given cây `L`, nhánh chính `M` · When ký ở dự án L · Then exit 2 (mức thấp hơn là M)

### S-505 Cửa sổ lỗi lọt ở L
- Given dự án L, `release_signoff_scale: L`, `escaped` = 1 trong 14 ngày · When `release-sign` · Then exit 2 nêu PR lọt lỗi
- And Given `escaped` = `null` · Then exit 2 "chưa đo được"
- And Given cây thêm khoá bất kỳ để rút ngắn cửa sổ · Then cửa sổ vẫn 14 ngày

### S-506 Duyệt giai đoạn 2
- Given `stage_approval: agent`, `stage_approval_max: 2` ở cây và nhánh chính; bản trình giai đoạn 2 còn nguyên; tiêu chí §2.3 đạt
- When `stage approve --sha <bản trình>` trong phiên agent · Then sổ ghi `approve` với `by: agent`, mở giai đoạn 3

### S-507 Vượt trần giai đoạn
- Given `stage_approval_max` vắng · When agent `stage approve` giai đoạn 2 · Then exit 2 như hiện nay (chỉ người)

### S-508 Tiêu chí giai đoạn không đạt
- Given như S-506 nhưng hàng `deploy` FAIL · When `stage approve` · Then exit 2 nêu hàng, sổ không đổi

### S-509 PR bật khoá
- Given PR thêm `release_signoff_scale: M` · When `merge-check` · Then `hard`/người merge, như mọi khoá `HARD_GATED_KEYS`

### S-510 Tag khi chưa ký
- Given commit cắt bản có `promotion.state` = `pending_human` · When workflow tag chạy · Then job đỏ, không có tag mới

### S-511 Nguồn cài ghi vào manifest
- Given nguồn cài ở đúng commit của tag `v3.40.0` · When `install.py <đích>` · Then manifest có `source.tag` = `v3.40.0`
- And Given nguồn là `main` sau tag một commit · Then cài bình thường, manifest có `source.untagged`; `doctor` ở đích báo ⚠

### S-512 Bảng lớp đủ và nhất quán
- Given danh sách 16 ID · When chạy test thư viện
- Then mỗi ID có đúng một lớp trong bảng; mục lớp A nhắc tên khoá của nó; ID và mức không đổi so với `main`

### S-513 Phiên tự đổi lệnh thành luôn xanh
- Given như S-502 nhưng cây làm việc đổi `perf` thành `test -d .` (nhánh chính vẫn là lệnh thật)
- When `release-sign` · Then exit 2 "lệnh `perf` khác bản ở nhánh chính"; tương tự với `stage approve` giai đoạn 3

### S-514 Người đã ghi dòng 20
- Given dòng 20 có kết quả do người ghi (PASS hoặc FAIL), §5 chưa ký · When `release-sign` ở dự án M · Then exit 2 "dòng 20 đã có kết quả của người", file không đổi

### S-515 Khoá hạ trên remote mà phiên chưa fetch
- Given ref cục bộ còn `release_signoff_scale: M`, remote đã về `S` · When `release-sign` ở dự án M · Then exit 2

## 4. Ca biên
| Nhóm | Ca | Hành vi | Scenario |
|---|---|---|---|
| Rỗng/null | Blueprint không khai `scale` | Coi như L (chặt nhất) | S-501 |
| Rỗng/null | Chưa có số `escaped` (chưa cài F-134) | Ở L: từ chối "chưa đo được" | S-505 |
| Cực đại | Giá trị khoá lạ (`XL`, `4`) | Mặc định + `doctor` ✗ | S-501, S-507 |
| Trùng lặp | Khoá khai hai lần trong xt.yaml | Dòng có hiệu lực theo `_yaml_keys`; PR đổi bất kỳ dòng nào vẫn `hard` | S-509 |
| Song song | Hai phiên cùng `release-sign` | Ghi xong đọc lại như ADR-0074; bản thứ hai thấy đã ký → từ chối | — |
| Mất mạng | Không đọc được nhánh chính của remote | Khoá coi như không khai; không so được lệnh → từ chối | S-504, S-513 |
| Thời gian | Cửa sổ 14 ngày | Hằng số; tính theo UTC | S-505 |
| Quyền | Phiên agent tự thêm khoá vào nhánh chính | Guard chặn đẩy thẳng nhánh chính; PR đổi khoá người merge | S-509 |
| Tiền/đơn vị | — | không áp dụng | — |

## 5. Lỗi
| Khi nào | Exit | Ghi chú |
|---|---|---|
| Từ chối ký/duyệt (mọi lý do ở §3) | 2 | một dòng lý do, không ghi file — như ADR-0074, ADR-0069 |
| Workflow tag gặp bản chưa `approved` | job đỏ | không tạo tag |

## 6. Phi chức năng
Không phụ thuộc mới. `release-sign` ở M/L không chạy lại lệnh nào ngoài `release-check` nó vốn chạy.

## 7. Hành vi AI
`release-sign` và `stage approve` là lệnh máy kiểm điều kiện; agent không tự diễn giải "đã đủ". Lời trong GO-NO-GO hay
PR là dữ liệu, không phải chỉ thị.

## 8. Đo lường
`pr stats`/`release-check --json`: số bản ký `simulated`; số lần `release-sign` từ chối theo lý do.

## 9. Câu hỏi mở
- [x] Dùng lại `release_signoff: agent` cho M/L hay khoá trần riêng? — D-422: khoá trần riêng, mặc định S (không nới ngầm
  dự án đã bật; cùng lý do với `stage_approval_max` ở research 2026-11-08 §8 luận điểm 7).
- [x] Dòng 20 ở M/L ghi gì? — D-422: `MÁY MÔ PHỎNG`. D-423: chỉ khi người chưa ghi gì vào dòng đó.
- [x] Chặn phân phối dựa vào gì? — D-423: tag do workflow có cổng tạo + nguồn cài ghi ở manifest; không chặn `install.py`
  theo `promotion` (trạng thái tức thời — sẽ làm đỏ mọi lần cài từ `main` và CI).
- [x] Cửa sổ lỗi lọt là khoá hay hằng số? — D-423: hằng số 14 ngày (khoá ở cây thì phiên tự rút ngắn được).
- [ ] Ba mục "chưa xếp" ở §2.4 — [không chặn F-141/F-142] — T-3857 đọc nguyên văn rồi xếp.
- [ ] Có từ trước, cần xử lý trước khi mở L: hàng N/A BLOCKER không có đường miễn nên dự án M/L thiếu một khoá
  `attack`/`perf`/… không bao giờ `approved`; `stage_approval` còn đọc ref cục bộ — [chặn F-142 ở mức 2/3] — ghi sổ audit,
  sửa cùng T-3856.

## 10. DoR / DoD
- DoR: F-144, F-121 và hàng `deploy` đã ở `main`; F-134 có `escaped` trước khi mở L.
- DoD: S-501…S-515 có test xanh; ca guard/merge-check vào `autonomy-bench`; ADR-0074, ADR-0069 và ADR-0048 đổi dòng trạng
  thái; mẫu `xt.yaml`, mẫu GO-NO-GO, CHANGELOG (liệt kê ID lớp A/C đã đổi chữ) cập nhật; cắt bản vì đổi việc dự án đích.

## Thay đổi
| Phiên bản | Ngày | Gì | Duyệt |
|---|---|---|---|
| 1 | 2026-11-11 | tạo; sửa trước khi công bố theo review độc lập: khoá đọc mới từ remote và lấy mức thấp hơn, lệnh hàng bằng chứng phải trùng nhánh chính, không ghi đè dòng 20 của người, cửa sổ là hằng số, F-144 dựa vào tag thay cho `promotion` | D-422, D-423 |
