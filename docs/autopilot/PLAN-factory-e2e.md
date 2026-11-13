# PLAN-factory-e2e.md — xưởng đầu-cuối: ý tưởng → bản dev → thiết lập một lần → production (ADR-0075)

> Lập 2026-11-11 theo chủ dự án ("song song nếu không chạm cùng file · thiết lập sau khi lên bản dev · ở mọi quy mô";
> "lên kế hoạch và tạo PR trước"). Duyệt: D-420 (phiên chính tự duyệt, ADR-0008). Nguồn:
> [ADR-0075](../adr/0075-end-to-end-factory.md) (D-419), research
> [`2026-11-11-factory-end-to-end.md`](../../research/2026-11-11-factory-end-to-end.md). Mỗi lát một PR; bug và hành vi
> mới có test đỏ trước; diff chạm guard/ký/quyền: reviewer độc lập rà trước khi mở PR.
>
> **Cú pháp bắt buộc cho máy:** mỗi task một dòng `- [ ] \`T-NNNN\` <việc> — Gate: \`<lệnh>\``.

## Tóm tắt (cổng duyệt)
- Mục tiêu: một câu ý tưởng → bản dev có receipt, không hỏi người; rồi một checklist thiết lập → production tự host.
  Chỉ số: thời gian và chi phí từ ý tưởng tới bản dev (pilot 1 đo lần đầu), thời gian chờ người, lỗi lọt sau merge.
- Thứ tự: bản dev trước (Lát 1–2, kết bằng pilot 1) → cơ chế chất lượng bù (Lát 3) → song song (Lát 4) → mọi quy mô
  (Lát 5, chỉ sau Lát 3) → thiết lập một lần và production (Lát 6) → vòng học, kênh vào, pilot 2 (Lát 7).
- Ràng buộc giữ: không tách `xt.py`; một gói trong 3.x (UI vào `web-api-ts`); trần byte; CLI chỉ stdlib; khoá nới nằm
  trong `HARD_GATED_KEYS`; mẫu dự án đích để khoá nới trống.
- `files:` chưa khai ở PLAN này: trước T-3851/T-3852 lời khai không được máy đối chiếu và mọi PR cùng chạm
  CHANGELOG/PROGRESS; khai lại khi hai task đó xong. Trong repo khung, phần lớn task cùng ghi `scripts/xt.py` nên song
  song lợi chủ yếu ở repo sản phẩm và giữa `xt.py` · `install.py` · gói · tài liệu.
- Đặc tả (D-422, D-423; mỗi task làm đúng scenario `S-NNN` của đặc tả lát mình): Lát 1 và T-3860 →
  [deploy](../specs/SPEC-factory-deploy.md) · Lát 2 và T-3862 → [intake](../specs/SPEC-factory-intake.md) · Lát 3 →
  [acceptance](../specs/SPEC-factory-acceptance.md) · Lát 4 → [parallel](../specs/SPEC-factory-parallel.md) · Lát 5 →
  [scale](../specs/SPEC-factory-scale.md) · T-3859 → [setup](../specs/SPEC-factory-setup.md) · T-3861, T-3864, T-3865 →
  [learning](../specs/SPEC-factory-learning.md).
- Dữ kiện sống của T-3866 có ở [`research/2026-11-11-factory-e2e-facts.md`](../../research/2026-11-11-factory-e2e-facts.md) và lượt tra
  thứ hai [`research/2026-11-12-dev-self-host-live-sources.md`](../../research/2026-11-12-dev-self-host-live-sources.md) (nêu ba chỗ lệch);
  công cụ container của gói đã chọn ở đặc tả deploy §10; ADR của T-3841 và T-3850 ghi quyết định kiến trúc và liên kết
  về đặc tả, không chép lại.
- Phần đặc tả còn **Draft** (có câu hỏi [chặn] sau hai lượt review — D-424): F-131/F-133 song song và worker (T-3850 thử
  trên git/GitHub thật), F-121 khoá nghiệm thu (T-3848), F-113 kênh issue (T-3862), F-142 giai đoạn 2/3 (T-3856). Task
  nêu trong ngoặc quyết bằng D-NNN và đổi dòng Trạng thái của đặc tả **trước** khi viết mã.
- Trần byte nhóm `scripts` (đo 2026-11-11: 1.304.426 B): còn ≈ 456 KB dưới trần cứng, nhưng cổng "2× mốc gần nhất"
  (ADR-0072) chỉ còn ≈ 119 KB — task nào làm nhóm vượt 2× thì ADR khai mốc mới đi cùng PR của task đó.
- Bảy đề xuất của phiên 2026-11-11 → task: triển khai thật T-3841…T-3844, T-3860 · ý tưởng → repo T-3845, T-3846,
  T-3862 · worker ngoài phiên T-3850, T-3853 · nghiệm thu độc lập T-3848 · gói có UI T-3849 · vòng học T-3861, T-3864,
  T-3865 · đo nền T-3854 và hai pilot.
- Việc cũ gộp vào đây: T-3555 phần worker ngoài phiên, field trigger, bot nâng bản (T-3850, T-3861, T-3865; phần event
  policy `pull_request_target` ở lại PLAN cũ); S2/S6/S8/S10 của research 2026-11-08 (T-3864, T-3854, T-3859, T-3856).

## Ngân sách (4 con số)
- Số vòng tối đa: bỏ trống · Chi phí: 0 đồng ngoài phiên tới hết Lát 5 · Timeout Gate: 1200 giây · Hạn: xét lại 2027-01-21

## Điểm dừng bắt buộc về hành động
- Không việc người nào trước pilot 1. Sau bản dev, chủ dự án làm **một lần** theo checklist của T-3859: GitHub App/token,
  đích và khoá production, trần chi phí scheduled task, merge PR bật khoá `HARD_GATED` (`release_signoff`, khoá giai đoạn).
- Tiền thật, dữ liệu người dùng thật, pháp nhân đứng tên: `- grant:` hoặc `loop defer`, ở mọi quy mô.

## Task

### Lát 0 — Dữ kiện sống và hợp đồng
- [x] `T-3866` `/research` nguồn sống có ngày: ảnh container + compose cho bản dev tự host, runner CI, worktree và phiên headless, scheduled task, GitHub App manifest — Gate: `git grep --untracked -qE '^title: .*bản dev tự host' -- research`
- [ ] `T-3841` ADR hợp đồng triển khai: khoá `xt.yaml` theo môi trường, schema receipt, hàng `release-check`, đích dev mặc định (sau: T-3866) — Gate: `git grep --untracked -qiE '^# ADR-[0-9]+: .*receipt' -- docs/adr`

### Lát 1 — Bản dev có receipt
- [ ] `T-3842` xt.py: lệnh triển khai đọc khoá `xt.yaml`, ghi receipt (môi trường · digest · thời điểm · smoke), smoke đỏ thì quay lui; fixture âm sai digest, smoke đỏ, receipt cũ (sau: T-3841; topo: review) — Gate: `python3 -m unittest tests.test_deploy_receipt`
- [ ] `T-3843` `release-check` đối chiếu digest ở receipt với `subject.digest`; `registry` đọc receipt vào `environments`/`release` (sau: T-3842; topo: review) — Gate: `python3 -m unittest tests.test_deploy_release_row`
- [ ] `T-3844` Gói `web-api-ts`: ảnh + compose dev (app + Postgres), khoá triển khai dev ở `pack.json`; workflow gói: repo sạch → bản dev → receipt → quay lui, ca sai cố ý đỏ (sau: T-3842) — Gate: `python3 -m unittest tests.test_pack_dev_deploy`

### Lát 2 — Ý tưởng tới repo đang chạy
- [x] `T-3845` `install.py`: một lệnh từ thư mục trống ra dự án mới (git, khung + gói, `PROJECT.md` 4 dòng Khung với giả định ghi "(mặc định khung — chưa chủ xác nhận)", blueprint, `doctor` sạch) (topo: review) — Gate: `python3 -m unittest tests.test_install_new`
- [ ] `T-3846` Skill một bước ý tưởng → bản dev (T-3845 → `/autopilot` → giai đoạn 1 → triển khai dev → báo cáo); repo sản phẩm là repo riêng hoặc bundle (sau: T-3844, T-3845, T-3848) — Gate: `python3 -m unittest tests.test_skill_factory`
- [ ] `T-3847` Pilot 1: một ý tưởng mẫu → bản dev có receipt trên repo sạch; ghi thời gian, chi phí, số lần phải hỏi người (sau: T-3846) — Gate: `test -s docs/ops/FACTORY-PILOT-1.md`

### Lát 3 — Chất lượng bù: nghiệm thu độc lập, UI
- [ ] `T-3848` Bộ nghiệm thu do agent khác người viết sinh từ SPEC trước khi viết mã, khoá bằng digest; việc đổi file đã khoá làm Gate đỏ trừ khi có D-NNN và reviewer độc lập; dựng trên `QA-STRAT-023` và khoá `acceptance`/`acceptance_report` sẵn có (topo: review) — Gate: `python3 -m unittest tests.test_acceptance_lock`
- [ ] `T-3849` Gói thêm UI tối thiểu và E2E trình duyệt trong workflow gói; kiểm giao diện thành Gate máy của task UI (sau: T-3844) — Gate: `python3 -m unittest tests.test_pack_ui`

### Lát 4 — Song song theo file
- [ ] `T-3850` ADR song song theo file và worker ngoài phiên — thay một phần D-142; đối chiếu `LOOP-STOP-014`, ADR-0009 §4, `LOOP-ORCH-006/007/020/024` ở mục Thay/Giữ; thử trên git/GitHub thật năm điểm [chặn] của đặc tả parallel §10 rồi chuyển F-131/F-133 sang Approved (sau: T-3866) — Gate: `git grep --untracked -qiE '^# ADR-[0-9]+: .*worker ngoài phiên' -- docs/adr`
- [ ] `T-3851` xt.py: diff thật của task nằm trong `files:` đã khai, ra ngoài thì `loop record` đỏ; đợt ≥ 2 task không giao thì `loop status` trả `parallel` mặc định; khoá lùi về `self` (sau: T-3850, T-3847; topo: review) — Gate: `python3 -m unittest tests.test_parallel_scope`
- [ ] `T-3852` File nhiều PR cùng chạm: mảnh `changelog.d/` + `changelog compile`; worktree song song không sửa PLAN (xong = bằng chứng; tick sau merge bằng Gate chạy trên nhánh chính); PROGRESS, sổ quyết định, sổ audit, sổ do lệnh ghi chỉ phiên điều phối ghi (sau: T-3850; topo: review) — Gate: `python3 -m unittest tests.test_shared_files`
- [ ] `T-3853` Worker ngoài phiên trên `loop run` sẵn có: mỗi lát một worktree, một nhánh, một PR; worktree do `xt.py` tạo; nhận việc bằng API tạo ref; nhánh quá hạn chỉ báo, giao lại bằng lệnh có D-NNN; trần chi phí đọc ở nhánh chính, cộng dồn theo lát qua mọi lượt; hàng đợi nhiều dự án đọc `registry.json` (sau: T-3851, T-3852; topo: review) — Gate: `python3 -m unittest tests.test_worker_queue`
- [ ] `T-3854` Số đo: xung đột tích hợp, lead time song song so tuần tự, lỗi lọt sau merge, thời gian chờ người, chi phí mỗi lát (sau: T-3851) — Gate: `python3 -m unittest tests.test_factory_metrics`

### Lát 5 — Mọi quy mô
- [ ] `T-3858` Chữ ký chặn phân phối (cơ chế bù — làm trước phần nới): commit cắt bản chưa `promotion: approved` thì workflow không ký, không tạo tag; `xt.py release-verify` kiểm attestation của workflow phát hành ở nơi dùng; ruleset tag `v*` và luật guard cấm phiên agent tạo tag phiên bản; `install.py` ghi nguồn cài vào manifest (topo: review) — Gate: `python3 -m unittest tests.test_promotion_gate`
- [ ] `T-3855` `release-sign` ở M/L: khoá trần `release_signoff_scale` (mặc định S, thuộc `HARD_GATED_KEYS`, đọc mới từ remote); hàng bằng chứng máy (nghiệm thu khoá + hàng `deploy` + diễn tập quay lui, lệnh trùng nhánh chính) thay dòng "người đã dùng thử" khi người chưa ghi, ghi "máy mô phỏng" (sau: T-3843, T-3848, T-3858, T-3854; topo: review) — Gate: `python3 -m unittest tests.test_release_signoff_scale`
- [ ] `T-3856` Khoá trần giai đoạn agent được duyệt (2/3) theo tiêu chí đăng ký trước; mặc định giữ 1 (sau: T-3843, T-3848, T-3858; topo: review) — Gate: `python3 -m unittest tests.test_stage_max`
- [ ] `T-3857` Thư viện: mục MUST buộc người ở M/L (research 2026-11-08 §8 "Soát thiếu") xếp lớp A/B/C, đối chiếu theo khoá, giữ ID, CHANGELOG ghi ID (sau: T-3855, T-3856; topo: review) — Gate: `python3 -m unittest tests.test_human_must_keys`

### Lát 6 — Thiết lập một lần, production
- [ ] `T-3859` `xt.py admin-plan` chỉ đọc: khi receipt dev xanh in một checklist (App/token, ruleset lệch, đích và khoá production, trần chi phí, khoá cần bật, mục MUST lớp B); không tự áp (sau: T-3843, T-3857; topo: review) — Gate: `python3 -m unittest tests.test_admin_plan`
- [ ] `T-3860` Triển khai production: chỉ khi có `grant`, `promotion: approved`, HEAD nằm trong nhánh chính của remote, digest trùng digest đã qua dev; smoke đỏ thì tự quay lui; `rollback` cùng điều kiện quyền và cũng đòi HEAD ở nhánh chính (sau: T-3859; topo: review) — Gate: `python3 -m unittest tests.test_deploy_prod`

### Lát 7 — Vòng học, kênh vào, nghiệm thu dây chuyền
- [ ] `T-3861` Số field do job CI xuất bằng khoá chỉ đọc; SLO đỏ mở task tối ưu; sự cố thành fixture hồi quy của gói (sau: T-3860) — Gate: `python3 -m unittest tests.test_field_trigger`
- [ ] `T-3862` Kênh vào: issue "ý tưởng" → worker chạy skill T-3846; nội dung issue là dữ liệu, chỉ tác giả có quyền ghi (sau: T-3846, T-3853; topo: review) — Gate: `python3 -m unittest tests.test_intake`
- [ ] `T-3864` Routine tuần: `feedback routine-check` đỏ khi có tín hiệu mới mà không có PR báo cáo (ADR-0010: không tín hiệu thì không PR); 10 nhóm phản hồi `cong-cu` phân loại thành task (sau: T-3859) — Gate: `python3 -m unittest tests.test_feedback_routine && test -s docs/ops/FEEDBACK-ROUTINE-CHECK.md`
- [ ] `T-3865` Nâng khung ở dự án đích theo mô hình kéo: workflow của từng dự án đọc tag mới, chỉ cài từ tag qua `release-verify`, tự mở PR; canary do dự án khai, dự án sau canary lấy bản mới nhất đủ ngày tuổi và chưa bị thu hồi (sau: T-3858; topo: review) — Gate: `python3 -m unittest tests.test_upgrade_bot`
- [ ] `T-3863` Pilot 2: ý tưởng → bản dev → checklist → production tự host; so với pilot 1; cắt bản (sau: T-3860, T-3862, T-3865) — Gate: `test -s docs/ops/FACTORY-PILOT-2.md`
