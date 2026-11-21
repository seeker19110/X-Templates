# PLAN-harden-2026-11-21.md — hoàn thiện khung: khép rủi ro có hạn, cắt 3.35.0, đưa một sản phẩm thật lên production

> Lập 2026-11-21 theo chủ dự án ("lên kế hoạch chi tiết để hoàn thiện dự án, rồi tạo pr draft"). Duyệt: D-533 (phiên
> chính tự duyệt, ADR-0008) · Blueprint: BLUEPRINT.md · Quy trình: ADR-0080. Nguồn số đo:
> [dự án đích 2026-11-19](../../research/2026-11-19-target-project-speed.md), [sổ audit](../ops/AUDIT-STATUS.md),
> `release-check` ở `29ddf2d8`. Mỗi lát một PR; bug và hành vi mới có test đỏ trước.
>
> **Cú pháp bắt buộc cho máy:** mỗi task một dòng `- [ ] \`T-NNNN\` <việc> — Gate: \`<lệnh>\``.

## Tóm tắt (cổng duyệt)
- Mục tiêu: khung "hoàn thiện" khi (1) không còn rủi ro có hạn treo, (2) 3.35.0 qua G7, (3) một sản phẩm đã dựng bằng
  khung chạy production có receipt và số đo. Chỉ số: thời gian từ bản được duyệt tới artifact chạy, số lần cần người,
  lỗi lọt sau merge, kết quả diễn tập quay lui.
- Dữ kiện đo 2026-11-21:
  - G7 ở `29ddf2d8`: NO-GO, chỉ đỏ hàng `review_debt` (81 tệp ngoài tài liệu đổi sau SHA quét). Blueprint 65 MUST đạt,
    5 miễn, 0 mở.
  - Sổ audit: 🔴 và 🟠 không còn `mở`; `chấp nhận` có 1 🔴 (AUD-SEC-406) và 24 🟠, trong đó 23 mục hạn 2027-01-21 và
    4 mục hạn 2027-01-31; 🟢 mở 325 (SEC 84, HAR 78, DOC 54).
  - CI `main` lượt 44880422059: shard `test 6/8` chạy 9 phút 21 giây dưới trần 10 phút; shard nhanh nhất 2 phút 23 giây.
  - GitHub chặn mặc định `pull_request_target` ở repo public từ 2026-12-02, trừ khi Actions event policy cho phép
    (github.blog/changelog/2026-11-02-pull_request_target-blocked-by-default-december-2 — đọc 2026-11-21).
  - 44 task `[ ]` nằm ở 10 PLAN khác (11 thuộc PLAN-factory-e2e); phần lớn task guard của PLAN-harden-2026-11-11 trỏ
    mục sổ đã `đã sửa`.
  - Registry: 7 dự án đích, mọi dự án `environments: []`. Research 2026-11-19: viết mã không phải nghẽn, nghẽn là quãng
    từ "mã xong" tới bản chạy có người dùng.
  - Phiên lập PLAN này mất bốn bước tay mới có CPython 3.15.2 (container có 3.13; uv 0.11 chỉ biết 3.15.0b4).
- Thứ tự và lý do: Lát 1 trước vì có hạn ngoài và `main` đỏ chặn mọi merge · Lát 2 để PLAN khớp sổ trước cổng ký ·
  Lát 3 cắt bản gom 38 mục Unreleased, sau đó phát hành theo tuần · Lát 4 chứng minh hiệu quả đầu cuối trên sản phẩm
  có sẵn · Lát 5 dùng số đo của Lát 4 để chọn việc kế · Lát 6 xử lý hạn 2027-01-21.
- Quan hệ với PLAN khác: [PLAN-factory-e2e](PLAN-factory-e2e.md) giữ 11 task (song song T-3850…T-3854, vòng học, pilot 2
  T-3863); Lát 4 ở đây lấy sản phẩm có sẵn, không thay T-3863 (ý tưởng mới). T-3975 thay T-3555, T-3977 thay T-3965,
  T-3982 và T-3983 thay T-3892; ba PLAN đã đóng dời vào `docs/archive/autopilot/`.
- Không làm ở PLAN này: adapter host mới, chế độ Lite/Full, `xt.pyz`, hạ Python, worker song song, video và showcase,
  tách `guard.py` một lần lớn. Xét lại ở T-3989 khi có số đo.

## Ngân sách (4 con số)
- Số vòng tối đa: bỏ trống (`--single-session`) · Chi phí ngoài phiên: 0 đồng tới hết Lát 3 · Timeout Gate: 1200 giây ·
  Hạn: 2026-12-02 cho Lát 1, 2027-01-21 cho Lát 6

## Hạn
| Loại | Ngày | Hậu quả nếu trễ | Cách xử lý khi trễ |
|---|---|---|---|
| Hạn thật | 2026-12-02 | GitHub không chạy `pr-review.yml` | T-3975; trễ thì chủ repo bật event policy cho đúng workflow |
| Hạn thật | 2026-12-31 | Rà `seeker19110/stored` quá hạn xét | chờ chủ repo (PROGRESS) |
| Hạn thật | 2027-01-21 | 23 mục `chấp nhận` hết hạn, `audit check` đỏ | T-3991 |
| Hạn mong muốn | 2026-12-05 | 3.35.0 chậm, dự án đích theo `main` | cắt bản với phần đã merge |

## Điểm dừng bắt buộc về hành động
- Việc cần người cho T-3986: VPS, tên miền, dòng `- grant:` production và `promotion: approved` của hotel-manager. Chưa
  có thì `loop defer --task T-3986`, làm Lát 5 phần không phụ thuộc.
- Giữ `pull_request_target` bằng Actions event policy là quyền quản trị repo; agent chỉ làm hướng gỡ (T-3975).
- Việc của người đã ghi ở PROGRESS §Tiếp theo mục 4 và T-1834 (gỡ context `merge-gate`) giữ nguyên.
- Tiền thật, dữ liệu người dùng thật: `- grant:` hoặc `loop defer`.

## Task

### Lát 1 — Rủi ro có hạn và cổng đang sát trần
- [ ] `T-3974` CI: đo lại `tests/shard-weights.json` bằng `dev-task.sh test-weights`, tách các lớp nặng nhất sang shard khác nhau; test mới khẳng định mọi lớp của `test_list` có trọng số trong tệp; thân PR ghi thời lượng từng shard của lượt CI, shard chậm nhất không quá 7 phút; không nới trần 10 phút (files: tests/shard-weights.json, tests/test_ci_shard.py) — Gate: `python3 -m unittest tests.test_ci_shard tests.test_ci`
- [ ] `T-3975` Bỏ `pull_request_target` khỏi `pr-review.yml` trước 2026-12-02; chọn bằng D-NNN giữa `pull_request` kèm environment, `workflow_run` và gỡ workflow; giữ tính chất PR không sửa được công cụ review và secret không lộ cho mã PR (topo: review; files: .github/workflows/pr-review.yml, tests/test_ci.py, CHANGELOG.md) — Gate: `! grep -rq pull_request_target .github/workflows/ && python3 -m unittest tests.test_ci`
- [ ] `T-3976` 🟠 AUD-HAR-454: guard trả deny mang mã `DERIVED_STEWARD` cho cả 5 đường merge PR làn derived; ca đối chứng làn nhanh và làn chuẩn vẫn allow; ADR-0087 và sổ ghi `đã sửa` (topo: review; files: .claude/hooks/guard.py, scripts/xt.py, tests/test_derived.py, tests/test_hooks.py, docs/ops/AUDIT-STATUS.md) — Gate: `python3 -m unittest tests.test_derived tests.test_hooks && git grep -q -F 'AUD-HAR-454 | 🟠 | đã sửa' -- docs/ops/`
- [ ] `T-3977` 🟢 AUD-HAR-443: cổng commit loại tệp chưa track khỏi tập tệp đổi khi lệnh là `git commit` đứng một mình (D-518 nêu tiền đề đúng) (topo: review; files: .claude/hooks/guard.py, .claude/hooks/pre-bash-guard.sh, scripts/dev-task.sh, tests/test_commit_gate.py) — Gate: `python3 -m unittest tests.test_commit_gate && git grep -q -F 'AUD-HAR-443 | 🟢 | đã sửa' -- docs/ops/`
- [ ] `T-3978` Tài liệu lệch mã: README ghi 8 màn (thêm Registry) ở cả hai chỗ; issue form phản hồi để trường "Cách đã khắc phục trong dự án" thành tuỳ chọn (files: README.md, .github/ISSUE_TEMPLATE/feedback-du-an-dich.yml) — Gate: `python3 scripts/xt.py checks && git grep -q '8 màn' -- README.md && ! git grep -q '7 màn' -- README.md`

### Lát 2 — PLAN khớp sổ
- [ ] `T-3979` Đối chiếu từng task `[ ]` của PLAN-harden-2026-11-11, PLAN-harden-2026-11-01 và PLAN-harden-2026-10-31 với sổ audit: mục đã `đã sửa` thì `[~]` kèm PR hoặc SHA đã sửa; mục còn mở (AUD-PERF-028…031, AUD-XFEAT-048, quét lại T-3729) thành task mới của PLAN kế; PLAN đóng dời vào kho — Gate: `! git grep -q -E '^- \[ \] .T-' -- docs/autopilot/PLAN-harden-2026-11-11.md docs/autopilot/PLAN-harden-2026-11-01.md docs/autopilot/PLAN-harden-2026-10-31.md`
- [ ] `T-3980` Quyết bằng D-NNN cho task mở lẻ: T-1690, T-1691, T-1745, T-2812, T-3554, T-3557, T-3669, T-3709 (làm ở lát nào hoặc `[~]` có lý do); PROGRESS mục Hoãn khớp; T-1834 giữ chờ người (sau: T-3979; files: docs/autopilot/, PROGRESS.md) — Gate: `python3 scripts/xt.py progress-check && python3 -m unittest tests.test_plan_files tests.test_green_release`
- [ ] `T-3981` 🟢 AUD-HAR-436 mở rộng: `progress-check` cảnh báo PROGRESS chậm `main` quá số PR khai trong `xt.yaml`, và báo task `[ ]` mà mọi mục `AUD-` nó nêu đã `đã sửa` (topo: review; files: scripts/xt.py, tests/test_plan_stale.py, CHANGELOG.md) — Gate: `python3 -m unittest tests.test_plan_stale`

### Lát 3 — Cổng ký và cắt 3.35.0
- [ ] `T-3982` `/audit delta` từ SHA quét gần nhất tới đầu `main` (81 tệp của hàng `review_debt`), xác minh đối kháng mọi 🔴/🟠, sổ và báo cáo delta (sau: T-3976, T-3977; topo: audit; files: docs/ops/) — Gate: `python3 scripts/xt.py audit check docs/ops/AUDIT-STATUS.md --strict`
- [ ] `T-3983` Trả nợ review theo lô trên diff tích luỹ, chia theo module, `reviewer-alt` chỉ đọc; 🔴 sửa kèm test đỏ trước, 🟠/🟢 ghi sổ có chủ và hạn (sau: T-3982; topo: review) — Gate: `python3 scripts/xt.py release-check`
- [ ] `T-3984` Cắt 3.35.0: `VERSION`, CHANGELOG gom Unreleased kèm mục "Dự án đích", GO-NO-GO phần máy, `release-sign` sau merge, tag qua `release-tag.yml` (sau: T-3983, T-3975, T-3974) — Gate: `python3 scripts/xt.py changelog-check && grep -qx '3.35.0' VERSION && python3 scripts/xt.py release-check`
- [ ] `T-3985` ADR nhịp phát hành: `main` merge liên tục, tag cho dự án đích gom theo tuần, bản vá bảo mật là ngoại lệ; dự án đích ghim khung trong pha build (đề xuất D của research 2026-11-19: 53 tag trong 24 ngày, nâng khung chiếm 16–22 % commit) (sau: T-3984) — Gate: `git grep --untracked -qiE '^# ADR-[0-9]+: .*nhịp phát hành' -- docs/adr`

### Lát 4 — Một sản phẩm thật lên production (hotel-manager)
- [ ] `T-3986` Production hotel-manager trong phiên của repo đó: bản dev bằng compose của dự án có receipt; `deploy run` production với `grant`, digest trùng bản dev, smoke, diễn tập quay lui; báo cáo ghi thời gian từ bản được duyệt tới artifact chạy, số lần cần người, chi phí nếu đo được; `registry pull` điền `environments` và `release` (cần: VPS, tên miền, grant; files: docs/ops/PILOT-PROD-hotel-manager.md, docs/ops/registry.json, tests_e2e/verify_prod_pilot.py) — Gate: `python3 tests_e2e/verify_prod_pilot.py docs/ops/PILOT-PROD-hotel-manager.md && python3 scripts/xt.py registry`
- [ ] `T-3987` Điền `type`, `risk`, `pack` cho 7 dự án trong registry từ `xt.yaml` và blueprint của từng dự án; TARGETS khớp (files: docs/ops/registry.json, docs/ops/TARGETS.md) — Gate: `python3 scripts/xt.py registry && python3 -m unittest tests.test_registry && ! git grep -q '"type": null' -- docs/ops/registry.json`

### Lát 5 — Quyết việc kế bằng số đo
- [ ] `T-3988` Đo nguồn gốc miễn trừ trên blueprint M của hotel-manager và X-Company: bao nhiêu trong 282 phản hồi `mien-tru` thuộc module dự án không có; từ một nửa trở lên thì ADR cho `compose` nhận dữ kiện phủ định ở M/L, dưới mức đó thì đóng (đề xuất F đã rút ở quy mô S) — Gate: `git grep --untracked -qE '^title: .*nguồn gốc miễn trừ' -- research`
- [ ] `T-3989` Research sau pilot: từ số đo T-3986 xếp thứ tự gói Next.js (3/4 dự án dùng), worker song song T-3850…T-3854, bot nâng khung T-3865, nghiệm thu host Codex/Gemini, mục "Không làm" của PLAN này; D-NNN và cập nhật PLAN-factory-e2e (sau: T-3986) — Gate: `git grep --untracked -qE '^title: .*sau pilot production' -- research`
- [ ] `T-3990` Đường vào cho người mới: `dev-task.sh setup` dựng interpreter CPython 3.15.x khi `python3` không phải 3.15 hoặc in đúng một lệnh cần chạy; README "Bắt đầu" tách hai lối checklist và factory; một lượt cài từ máy sạch ghi từng bước hỏng, Windows qua WSL (topo: review; files: scripts/dev-task.sh, README.md, docs/ops/ONBOARDING-RUN.md, tests/test_dev_task_setup.py, CHANGELOG.md) — Gate: `python3 -m unittest tests.test_dev_task_setup && test -s docs/ops/ONBOARDING-RUN.md`

### Lát 6 — Hạn 2027-01-21
- [ ] `T-3991` Xét lại 23 mục `chấp nhận` hạn 2027-01-21 và 4 mục hạn 2027-01-31: mỗi mục sửa, hoặc gia hạn kèm D-NNN, hoặc chuyển sang hàng rào phía server (ruleset tag `v*` của T-3858, sandbox Bash D-331/D-332); lớp đã có hàng rào server thì không vá thêm biến thể shell trong guard (topo: review; files: docs/ops/AUDIT-STATUS.md) — Gate: `! git grep -q -E 'chấp nhận.*hạn: 2027-01-(21|31)' -- docs/ops/AUDIT-STATUS.md`
- [ ] `T-3992` ADR tách dần `guard.py` và `xt.py` (D-142): mỗi PR dời một họ luật sang module nạp theo đường tệp như `xt_derived.py`, `autonomy-bench` và `guard.json` cho quyết định không đổi, đo thời gian hook trước và sau theo T-3709 (sau: T-3991) — Gate: `git grep --untracked -qiE '^# ADR-[0-9]+: .*tách dần' -- docs/adr`

## Phụ thuộc ngoài
| Việc | Bên ngoài | Kế hoạch B |
|---|---|---|
| T-3986 | Chủ dự án cấp VPS, tên miền, grant | dev tự host có receipt; production `loop defer` |
| T-3975 | Chính sách GitHub 2026-12-02 | chủ repo bật event policy cho `pr-review.yml` |
| T-3988, T-3987 | Quyền đọc repo dự án đích | clone nông repo public; repo private chờ phiên có quyền |

## Ước lượng (phiên agent, chưa đo)
Lát 1: 5 PR · Lát 2: 2–3 PR · Lát 3: 1 đợt audit + 2–4 PR sửa + PR cắt bản · Lát 4: tuỳ ngày có VPS · Lát 5: 3 PR ·
Lát 6: 2 PR, làm trước 2027-01-21. Không cộng thành ngày hứa.
