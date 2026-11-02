# AUDIT-REPORT — Khung X-Templates · 2026-11-02 (toàn bộ)

> Commit quét: `1e3c060` (#398, `main`); sau quét merge #399 (lát C guard, `c346bdb`) — 7 🟠 dấu review đã sửa, 4 🔴 và AUD-SEC-248 kiểm lại ở `c346bdb` vẫn tái hiện · Phạm vi: toàn bộ 13 nhóm (A11Y chỉ smoke, DATA N/A) · Người quét: phiên chính + 4 cụm
> song song (mã `xt.py`/`install.py`/`xt_app` · harness `.claude/` + guard · nội dung `framework/` · CI/vận hành/sổ) ·
> Xác minh đối kháng: 15 phát hiện quan trọng nhất, mỗi phát hiện một agent độc lập cố bác bỏ bằng lệnh thật →
> 9 CONFIRMED · 6 PARTIAL (số liệu đính chính, ghi ở §4) · 0 REFUTED.
> `xt.py audit check docs/ops/AUDIT-STATUS.md` → exit 0 · `--strict` → exit 1 (4 🔴 có từ trước + 3 🟠 mới + nợ review).

## 1. Tóm tắt

| Mức | Mở (mới hôm nay) | Mở có từ trước | Ghi chú |
|---|---|---|---|
| 🔴 | 0 | 4 (AUD-SEC-247, 309, 310, 311) | cùng lớp "shell dựng lúc chạy" — tái hiện lại ở HEAD: `cat f.sh \| sh 2>&1` → quyết định rỗng |
| 🟠 | 3 (AUD-CODE-036, AUD-HAR-197, AUD-SEC-329) | 13 (sau #399) | 🟠 có từ trước tái hiện: AUD-SEC-248 (`cp -rT scripts docs/autopilot` cho qua) |
| 🟢 | 21 (AUD-HAR-198/199, CODE-037/038, ARCH-008, PERF-013/013, TEST-050/050, CI-027/028, DEP-010, DOC-175…181, XFEAT-046) | 305 | AUD-HAR-036 (NotebookEdit) xác nhận còn đúng |

Kết luận một câu: **3.30.0 vẫn NO-GO** vì 4 🔴 guard có từ trước; ba 🟠 mới không chặn phát hành nhưng hai trong đó (sổ review mất bản ghi khi chạy song song, G7 không ép GO-NO-GO) làm bằng chứng của quy trình kém tin cậy nên sửa trước khi cắt bản.

Đánh giá chung: cổng đầy đủ xanh (mypy strict, ruff, coverage 100 % dòng + nhánh, 2.178 test), 19/19 action ghim SHA, requirements ghim hash, khung 2.814 mục hợp lệ. Ba trần đang chạm: (a) guard mô phỏng bash + blacklist regex đã hết dư địa (9.392 dòng, 361 hàm luật, vẫn 4 🔴; ~8 % lệnh thường ngày trong mẫu thử bị chặn oan); (b) sổ sách phình nhanh hơn mã và không có trần (docs/ops 874 KB, docs/autopilot 645 KB); (c) khối lượng blueprint lệch (static-site M 384 MUST > game 363) và 25 % MUST có Kiểm chưa ra lệnh/ngưỡng.

## 2. Phạm vi và tín hiệu

`audit plan` không chạy riêng (quét toàn bộ, không delta). Stack: Python ≥ 3.11 stdlib, bash, GitHub Actions; UI `scripts/app` (A11Y chỉ `app --smoke`, không axe lại — giữ SHA cũ). DATA N/A (không CSDL). Công cụ cổng cài bằng `scripts/dev-task.sh setup` (10 s).

Số đo nền (hôm nay): `xt.py` 14.774 dòng / 828 hàm · `guard.py` 9.392 dòng / 580 hàm · test 44.215 dòng, 315 lớp, 772 s tuần tự · CI ~2,6 phút/run trên `main` · guard 0,21–0,28 s mỗi lệnh Bash · cài vào dự án đích 0,6 s, `.xtemplates/` 4,7 MB · blueprint web-app + ecommerce M: 489 MUST, 242 KB.

## 3. Lệnh đã chạy

| Nhóm | Lệnh | Exit | Kết quả chính |
|---|---|---|---|
| Cổng | `scripts/dev-task.sh gate` | 0 | GATE XANH (5 lệnh), coverage TOTAL 100 % |
| Khung | `python3 scripts/xt.py validate` · `stats` | 0 | 186 file, 2.814 mục (MUST 1.541 · SHOULD 902 · MAY 371) |
| Harness | `python3 scripts/xt.py doctor` | 0 | 0 lỗi, 1 cảnh báo (công cụ cổng chưa cài trước `setup`) |
| Sổ | `python3 scripts/xt.py audit check docs/ops/AUDIT-STATUS.md --strict` | 1 | 🔴 mở 4 · 🟠 mở 20 · 🟢 mở 304 (trước khi ghi phát hiện mới) |
| App | `python3 scripts/xt.py app --smoke` | 0 | mọi route 200; 30 s wall / 3,6 s CPU |
| Dự án đích | `install.py <repo trống> --with-github` → `doctor` → `compose --profile web-app --industry ecommerce --scale M` | 0 | cảnh báo đúng (`xt.yaml` trống); 489 MUST, 242 KB |
| Guard | `python3 .claude/hooks/guard.py bash` với payload PreToolUse giả | — | `cat f.sh \| sh 2>&1`, `cp -rT scripts docs/autopilot` → quyết định rỗng; đối chứng `cp -rT scripts .autopilot` → deny |
| Guard | `python3 -m unittest -q tests.test_guard_corpus tests.test_guard_audit1019 tests.test_hooks` | 0 | 34 + 109 + 302 test; corpus 991 ca (220 cho phép, 771 chặn) |
| Mã | `python3 -I` + `ast` trên `scripts/xt.py` | 0 | 810 hàm cấp đầu, 7 hàm > 60 dòng, chu trình `loop↔CLI↔doctor` |
| CI | `grep` trên `.github/workflows/*.yml` | 0 | 19/19 `uses:` ghim SHA; 0 cache pip; `fetch-depth: 0` ×7; 9 checkout không `persist-credentials: false` |
| Xác minh | Workflow 15 agent độc lập, mỗi agent một phát hiện | — | 9 CONFIRMED · 6 PARTIAL · 0 REFUTED |

## 4. Phát hiện chi tiết (🟠 mới; 🟢 chỉ ghi sổ)

### AUD-CODE-036 🟠 `pr reviewed`/`pr debt`/`pr rethink` đọc–ghi `reviews.json` không khoá
- **Bằng chứng:** đo được — `scripts/xt.py:12192` đọc sổ → `:12217` ghi → `:12222` gọi mạng `_publish_review` → `:12226` ghi lại `data` cũ; `_write_reviews` `:11271-11274` chỉ `write_atomic`, không `_state_lock`/`rev` như `state.json` (`:1326-1390`). Cùng mẫu ở `pr debt` (`:12161/:12175`) và `pr rethink` (`:12770-12782`).
- **Tái hiện:** 1. `gh` giả: PR 1 ngủ 3 s khi đăng, PR 2 trả ngay. 2. Chạy song song `pr reviewed --pr 1 --head A --clean` và `pr reviewed --pr 2 --head B --blocking`. 3. Cả hai exit 0, in "đã ghi/đã đăng" → `reviews.json` chỉ còn PR 1, bản ghi PR 2 mất.
- **Xác minh đối kháng:** CONFIRMED (agent độc lập tái hiện bằng hai tiến trình thật). Mức tác động vừa: `pr next` đọc review từ comment trên GitHub, sổ cục bộ để phát hiện review chưa đăng — mất dấu khi publish thất bại (exit 3).
- **Đề xuất sửa:** đưa ba đường ghi qua `_state_lock`/hàm `update_*` kiểu đọc–sửa–ghi trong khoá; test race hai tiến trình đỏ trước. **Gate:** `python3 -m unittest -q tests.test_merge -k reviews_lock`

### AUD-HAR-197 🟠 `release-check` không ép file GO-NO-GO khớp VERSION; 3.29.0 phát hành không có GO-NO-GO
- **Bằng chứng:** đo được — `ls docs/ops | grep GO-NO-GO` → mới nhất `GO-NO-GO-2026-10-28-v3.28.0.md`; `VERSION` = 3.29.0; PROGRESS.md:8 "3.29.0 đã phát hành… GO chờ người"; `scripts/xt.py:11151` `release_check` hàng: blueprint · audit · verify · tree · prod_switch · phase · stage · review_debt · attack/perf/migration_check/acceptance/rollback · unchecked_must — không hàng nào kiểm GO-NO-GO; commit cắt bản `3a3c101` (#348) không thêm file.
- **Tái hiện:** 1. `cat VERSION`. 2. `ls docs/ops/GO-NO-GO-*` → không có `v3.29.0`. 3. `grep -n go_no_go scripts/xt.py` → rỗng.
- **Xác minh đối kháng:** CONFIRMED.
- **Đề xuất sửa:** hàng `go_no_go_file` (BLOCKER ở M/L: `docs/ops/GO-NO-GO-*-v<VERSION>.md` tồn tại, không còn `[ ]` BLOCKER); bổ sung GO-NO-GO 3.29.0 hồi tố có ghi chú. **Gate:** `python3 scripts/xt.py release-check`

### AUD-SEC-329 🟠 Chính sách guard suy từ chuỗi lý do tiếng Việt; đổi câu chữ biến deny thành cho qua
- **Bằng chứng:** đo được — `.claude/hooks/guard.py:9169-9224` `REASON_CODES`/`DANGER_MARKERS` khớp cụm chữ trong lý do; `:9248` `reason_code` dò `m in reason` khi nơi sinh chưa đặt `code` (chỉ 2 nơi đặt tường minh: `:9084` BUDGET, `:9324` UNPARSED); 20/34 dấu là chuỗi literal (vd `:1829` "push thẳng nhánh chính"). Test `:5223` chỉ kiểm `DANGER_MARKERS == REASON_CODES` (tautology); end-to-end ~10 lệnh nguy hiểm + `assert_code` cho HOOK_BYPASS/REMOTE_REF_FORGE/PUSH_MAIN; STASH_DROP, HOST_CONTAINER, SECRET_WRITE, STAGE_APPROVE không có test khoá. ADR-0018 §Hệ quả (dòng 43) thừa nhận.
- **Tái hiện:** 1. `apply_policy` với ask "push thẳng nhánh chính…" → deny/PUSH_MAIN. 2. Đổi chữ thành "đẩy thẳng lên nhánh chính…" → `''` OTHER_ASK (cho qua).
- **Xác minh đối kháng:** PARTIAL — đúng cốt lõi; chiều rủi ro chủ yếu deny → cho qua; 14/34 dấu dùng hằng chung nên bền.
- **Đề xuất sửa:** mỗi luật trả `code` tường minh, `REASON_CODES` chỉ còn fallback; test duyệt mọi mã có ≥ 1 ca end-to-end; cập nhật ADR-0017 §2 cho khớp mã (AUD-DOC-181). **Gate:** `python3 -m unittest -q tests.test_hooks -k reason_code`

### Đính chính sau xác minh đối kháng (so với báo cáo của các cụm quét)
- `uses:` trong `ci.yml` là 19 (không phải 33); checkout không `persist-credentials` là 9 (không 7); 6 job cài cả 3.11 + 3.14 là chủ ý ghi ở dòng 49.
- Lệnh `gh` dựng tay trong vùng steward là 7 (không ~11) và đều POST/PUT — không phải ứng viên hiển nhiên cho `_gh_api` (GET); trùng lặp thật chỉ ở `latest_framework_tag` (`:5139-5159`).
- Trần `DIR_CAPS` so bề mặt gốc 2026-10-23 là 2,6× / 4,0× / 5,8× theo nhóm (không đồng loạt 2,5×) và là quyết định có ghi ở ADR-0050 (mốc xét lại 2027-01-21); phần chưa có trần là docs/ops và docs/autopilot.
- Assert theo đồng hồ ở `tests/test_perf.py:173/199/217` có biên ≥ 4,5× giá trị đo dưới tải 4× — không tái hiện chập chờn → 🟢.
- Chi phí guard mỗi lệnh: compile nguồn 0,12–0,16 s (không 0,18 s) + thân module 45 ms + khởi động 20 ms; nguyên nhân là bộ nạp cố ý compile từ nguồn (AUD-SEC-074), không phải cờ `-B`.
- `OPS-OBS-008` và `AI-OBS-004` chỉ chung một vế; `BASE-DEP-013`/`PRF-LIB-005` lặp `SEC-SUPPLY-021` (không phải `SEC-SECRET-009`).
- `yaml_scalar` có test gián tiếp qua `_yaml_keys`/`commit_gate`, thiếu test trực tiếp và ca biên.

## 5. Kế hoạch sửa theo đợt (tự duyệt — D-302; chủ dự án triển khai)

| Đợt | Phát hiện | PR dự kiến | Gate của đợt |
|---|---|---|---|
| P0 (trước 3.30.0) | AUD-SEC-309/310/311/247 (lát C ADR-0063: nhận `sh -c`/`eval`/ống vào shell trên token; `_container_asks` giữ deny) | `fix(guard): shell lồng theo argv đã chuẩn hoá — ADR-0063 lát C` | `python3 -m unittest -q tests.test_guard_strict tests.test_hooks` · `python3 scripts/xt.py autonomy-bench` |
| P0 | AUD-SEC-248 (bảo vệ `docs/autopilot/` theo tiền tố như `.autopilot/`) | `fix(guard): docs/autopilot theo tiền tố thư mục` | `python3 -m unittest -q tests.test_hooks -k ledger` |
| P0 | AUD-CODE-036 (khoá `reviews.json`) | `fix(xt): khoá đọc–ghi reviews.json như state.json` | `python3 -m unittest -q tests.test_merge -k reviews_lock` |
| P0 | AUD-HAR-197 (hàng `go_no_go_file` + GO-NO-GO 3.29.0 hồi tố) | `feat(release-check): hàng go_no_go_file` | `python3 scripts/xt.py release-check` |
| P0 | AUD-HAR-036/198 (matcher `NotebookEdit` + MCP ghi), AUD-CI-027 (`schedule` secret-scan), AUD-DOC-175 (PROGRESS) | `fix(harness): phủ NotebookEdit và MCP ghi; ci: lịch gitleaks` | `python3 -m unittest -q tests.test_hooks tests.test_ci` |
| P1 (2–4 tuần) | AUD-DOC-180 (lưu trữ sổ + trần docs/ops, docs/autopilot), AUD-SEC-329 (mã lý do), AUD-PERF-013 (cache guard kiểm sha256), AUD-HAR-199 (đo chặn oan trong `runs.jsonl`), AUD-CODE-037/038, AUD-CI-028, AUD-DEP-010 (SBOM + attestation), AUD-TEST-050/050 | mỗi mục một PR | theo Gate từng dòng sổ |
| P2 (cần ADR) | Sandbox/egress bắt buộc cho autopilot không người trực (guard dừng mở rộng luật lớp xoá/ghi/mạng); tách `xt.py` thành gói theo lát (AUD-ARCH-008, trả lời D-142 bằng số đo); nội dung AUD-DOC-176…178/181; AUD-XFEAT-046 (không copy `research/`) | ADR mới + PLAN riêng | `python3 scripts/xt.py validate` · `release-check` |

## 6. Nợ 🟢 giữ lại

| ID | Chủ | Hạn | Lý do chưa sửa |
|---|---|---|---|
| AUD-HAR-198, CODE-037, CODE-038, ARCH-008, PERF-013, PERF-014, TEST-050, TEST-051, CI-027, CI-028, DEP-010, DOC-175…181, XFEAT-046, HAR-199 | chủ dự án | theo đợt P0/P1/P2 (D-302) | ghi `mở`, chưa `chấp nhận` — chủ dự án triển khai sau audit này |
