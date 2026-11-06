---
title: Đề xuất X-Templates thành xưởng phần mềm dựa trên 34 chuyên mục stored
kind: research
updated: 2026-11-04
---

# Đề xuất định hướng xưởng phát triển phần mềm

> **Trạng thái: định hướng đã được chủ dự án chấp nhận 2026-11-04** qua [ADR-0068](../docs/adr/0068-software-factory-direction.md)
> (trả lời §9: 1a · 2a hotel-manager · 3a · 4a — D-353; tiền lệ ADR-0064: nháp cùng PR, chấp nhận cùng ngày). Bản nháp ở PR #437 chỉ thêm
> nghiên cứu, ADR và liên kết chỉ mục (mã lát A–E về sau ở PR #451); bản nháp chưa thêm
> ID, đổi mức yêu cầu, cấu hình mặc định, hành vi CLI, schema hay dependency. Các đường chạy và tiêu chí dưới đây là mục tiêu
> triển khai ở các PR riêng, chưa là kết quả đã kiểm chứng.
>
> Bản 2 (cùng ngày, hoàn thiện sau rà soát PR #437): sửa một vị trí nguồn, đối chiếu với quyết định hiện hành (§3b), ánh xạ
> hợp đồng bằng chứng lên ID đã có (§6), ứng viên cụ thể cho từng lát (§7), chỉ số có baseline (§8), và đề xuất trả lời bốn
> câu hỏi mở kèm phương án thay thế (§9). Nhật ký xác minh ở §10.

## 1. Mục tiêu và phạm vi bằng chứng

Định vị đề xuất: **X-Templates là bộ máy giao hàng phần mềm có kiểm chứng**, giúp biến yêu cầu thành sản phẩm có thể phát hành, vận hành, nâng cấp và phục hồi. Đơn vị thành công là một lát nghiệp vụ được nghiệm thu trên sản phẩm, gắn với artifact và kết quả thực địa.

Đối chiếu ngày 2026-11-04:

- X-Templates **3.29.0**, commit [e0ea0a6c97576f96611e42dad05d21907745c4f7](https://github.com/seeker19110/X-Templates/tree/e0ea0a6c97576f96611e42dad05d21907745c4f7) (bản 2 đối chiếu lại ở `9c03257` — `main` sau #436; `scripts/xt.py` không đổi giữa hai commit nên số dòng dưới đây giữ nguyên): đọc tài liệu, implementation và CI; chưa chạy sản phẩm/deployment để xác minh các tuyến đề xuất.
- stored, commit [5d8f8a6d6a5245fa3cf543cac57d2d2bb5b8f2d9](https://github.com/seeker19110/stored/tree/5d8f8a6d6a5245fa3cf543cac57d2d2bb5b8f2d9) (PR seeker19110/stored#131; trạng thái merge chưa xác minh được trong phiên — API ngoài phạm vi, chỉ đọc được nội dung tại commit): 34 chuyên mục, 1.040 hồ sơ (README stored dòng 15); đợt mới 1.003 → 1.040: 37 hồ sơ mới và 16 hồ sơ đọc sâu/cập nhật metadata (README stored dòng 386), không xác minh lại toàn bộ lịch sử.
- Đầu vào chính: [FACTORY.md](https://github.com/seeker19110/stored/blob/5d8f8a6d6a5245fa3cf543cac57d2d2bb5b8f2d9/FACTORY.md), [GUIDES.md](https://github.com/seeker19110/stored/blob/5d8f8a6d6a5245fa3cf543cac57d2d2bb5b8f2d9/GUIDES.md), [phương pháp](https://github.com/seeker19110/stored/blob/5d8f8a6d6a5245fa3cf543cac57d2d2bb5b8f2d9/METHOD.md) và [bàn giao XT-H-113…116](https://github.com/seeker19110/stored/blob/5d8f8a6d6a5245fa3cf543cac57d2d2bb5b8f2d9/data/xt-handoff.json). Chính FACTORY.md §9 ghi: các cổng/pipeline trong đó là **tổng hợp đề xuất**, stored chỉ chạy validator catalog, không chạy sản phẩm hay deployment nào.

Kết quả kiểm tài liệu/CLI của repo khung, nếu có trong PR, chỉ chứng minh thay đổi này giữ hợp đồng hiện tại; không chứng minh xưởng đã vận hành. Các vị trí nguồn trong bảng dưới áp dụng snapshot X-Templates đã nêu.

## 2. Nền hiện có và phần nên làm sâu

| Năng lực | Đã có ở snapshot | Phần nâng tiếp được đề xuất |
|---|---|---|
| Vòng đời và composition | G0–G8, S/M/L, build/harden; `compose` sinh blueprint/backlog, giữ ID và đánh dấu mục đổi nội dung | Một gói sản phẩm ghép đúng control với stack, cấu hình chạy và acceptance suite; giữ quy trình hiện có |
| Cài và nâng khung | Installer cài thư viện, CLI, harness, Git hooks và CI; hash/manifest giữ file tùy chỉnh, có `--plan` và bản `.xtemplates-new` khi cần gộp | Mở rộng ownership, compatibility và migration sang phiên bản gói sản phẩm; kiểm cả repo mới và brownfield |
| Bằng chứng task | Evidence v2 gắn command hash, scope, revision yêu cầu và digest file | Bổ sung environment/tool/dataset và kết quả có kiểu; nối đến artifact build/deploy |
| Phát hành | `release-check` (ADR-0042, ADR-0062 §6: `attack`/`perf`/`migration_check`/`acceptance`/`rollback`), gói nghiệm thu có `candidate_head`/`evidence_fp`, sổ giai đoạn `xt.py stage` (ADR-0058) | Quyết định phát hành rõ trạng thái và chủ thể; receipt của artifact/môi trường thực sự triển khai |
| Agent host | Lõi guard chung, sáu adapter ngoài Claude, Git hook sàn và vòng lặp ngoài (ADR-0064) | Conformance theo host/version trên công cụ thật, trust activation và ranh giới sandbox được kiểm |
| Vòng học | Feedback aggregation nhiều dự án (ADR-0010, `LOOP-FB-*`) và control về metrics, budget, SLO | Incident → control → fixture regression → bản gói sửa lỗi → danh sách dự án cần nâng |

Nguồn: [composition](../framework/00-method/composition.md), [installer](../scripts/install.py), [evidence](https://github.com/seeker19110/X-Templates/blob/e0ea0a6c97576f96611e42dad05d21907745c4f7/scripts/xt.py#L2260), [signoff](https://github.com/seeker19110/X-Templates/blob/e0ea0a6c97576f96611e42dad05d21907745c4f7/scripts/xt.py#L8033), [ADR-0064](../docs/adr/0064-multi-provider-harness.md), [giới hạn adapter](../framework/templates/harness/README.md), [feedback](https://github.com/seeker19110/X-Templates/blob/e0ea0a6c97576f96611e42dad05d21907745c4f7/scripts/xt.py#L11196), [ADR-0058](../docs/adr/0058-product-stages-machine-lock.md), [phản hồi dự án đích](../framework/11-autonomous-loop/framework-feedback.md).

Các khoảng cần nâng dưới đây được kết luận từ những đường gọi đã đọc; không khẳng định toàn repo không có cơ chế tương tự. Đặc biệt, adapter đã có implementation/test payload; chính ADR-0064 ghi chưa chạy thật từng host (fixture payload thật `tests/fixtures/harness/<tool>/` là việc còn mở của `T-3642`…`T-3644`). Mức hỗ trợ công bố nên phản ánh bằng chứng này.

## 3. Phân vai và lựa chọn kiến trúc

| Thành phần | Trách nhiệm | Hợp đồng bàn giao |
|---|---|---|
| stored | Nghiên cứu lựa chọn, cơ chế, license, nguồn và giới hạn | Hồ sơ có SHA, phạm vi, mức bằng chứng, alternative và bài học đối chiếu ID |
| X-Templates | Controls, composition, adapter, gói được hỗ trợ, chính sách và nâng cấp | Gói có phiên bản/owner, phép nghiệm thu, fixture âm, compatibility và migration notes |
| Repo sản phẩm | Nghiệp vụ, implementation, hạ tầng và vận hành cụ thể | Acceptance results, artifact digest, deployment receipt và số liệu thực địa có quyền truy cập phù hợp |

Ba phương án đã cân nhắc:

1. **Mở rộng thư viện yêu cầu theo từng công cụ mới:** chi phí ban đầu thấp, nhưng dự án vẫn phải tự nối cấu hình và bằng chứng. Phù hợp làm nguồn tham khảo, chưa đủ mục tiêu giao hàng lặp lại. Đây là hiện trạng (mỗi đợt stored → research note → ID SHOULD).
2. **Một nền tảng tập trung quản toàn bộ agent/build/deploy:** có thể thống nhất trải nghiệm, nhưng tăng quyền tập trung, vận hành và migration trước khi chứng minh được tuyến sản phẩm; trái ADR-0010 (khung kéo về, dự án không cần token ghi) và "mặc định tự host" (AGENTS.md §4).
3. **Lõi hiện có + gói sản phẩm/adapter có phiên bản + điều phối nhiều dự án ở mức cần thiết:** tận dụng CLI/CI, quyền riêng từng repo và feedback đã có. Đây là phương án đề xuất; đổi cấu trúc/công cụ chỉ thực hiện qua ADR riêng sau khi chốt phạm vi.

Giữ lõi CLI stdlib và một nhà cho policy theo các ADR hiện hành. Gói stack có thể khai dependency theo hệ sinh thái của sản phẩm, có pin/license/owner; không biến chúng thành dependency bắt buộc của CLI khung. Tự host là đường phát triển mặc định theo AGENTS.md §4 (ADR-0008); tích hợp bắt buộc cần tài khoản riêng có adapter giả và contract test, còn nghiệm thu production vẫn phải kiểm trên đích thật.

### 3b. Đối chiếu với quyết định hiện hành (bản 2)

Đề xuất chỉ đứng được nếu không lặng lẽ đảo các quyết định đã có. Bảng dưới là điều kiện ràng buộc cho ADR-0068 và các lát §7:

| Quyết định đã có | Nội dung ràng buộc | Hệ quả cho đề xuất |
|---|---|---|
| [D-142](../docs/autopilot/DECISIONS-2026-10.md) (2026-10-23) + [ADR-0043](../docs/adr/0043-size-budget.md)/[ADR-0050](../docs/adr/0050-raise-dir-size-caps.md) | Đóng băng bề mặt 3.x: trần tổng byte theo nhóm (`tests/test_docs_budget.py`); **không làm**: tách `xt.py`, song song worktree, merge queue, reviewer LLM mọi PR, thu nhỏ guard | Mã adapter kết quả (§6) ở trong `xt.py` (nhóm `scripts` đo 2026-11-04: 1.045.208 B / trần 1.760.431 B — còn ≈ 715 KB); gói sản phẩm **không** nằm trong nhóm bị trần (`framework/templates/` chưa có trần) nhưng mỗi gói là mã/cấu hình phải bảo trì → tối đa **một** gói trong 3.x; registry nhiều sản phẩm (lát E) chỉ là file YAML/JSON + lệnh đọc, không nền tảng riêng |
| [ADR-0064](../docs/adr/0064-multi-provider-harness.md) (D-303) | Giữ `.claude/hooks/guard.py` là nhà luật trong 3.x; xét dời ở **4.0 cùng mốc 2027-01-21**; adapter chưa chạy thật từng host | Lát D (host thật) gắn vào mốc xét lại 2027-01-21 và `T-3642`…`T-3644`; không mở lát D trước khi có fixture thật của ≥ 1 host |
| [ADR-0058](../docs/adr/0058-product-stages-machine-lock.md) (D-239; từ 2026-11-04 [ADR-0069](../docs/adr/0069-agent-stage-approval.md) cho agent tự duyệt khi `stage_approval: agent`) | `stage approve` **chỉ người** (hoặc agent theo ADR-0069); `by` lấy từ `git config` — "không phải chữ ký"; "GO của máy, nghiệm thu của người, quyền deploy và đã deploy là **bốn việc khác nhau**"; chữ ký thật (SLSA/in-toto, tag ký, tree-hash) là việc sau | Nhóm *Quyết định* và *Triển khai* ở §6 chính là hai việc còn thiếu trong bốn việc đó; identity người duyệt trong repo một chủ **không phân biệt được với agent** bằng GitHub (ADR-0058 phương án 3) → quyền promote phải nằm ở CI/IAM/environment của hệ đích, khung chỉ ghi receipt |
| [ADR-0042](../docs/adr/0042-release-check-attack-and-perf.md), [ADR-0062 §6](../docs/adr/0062-review-once-risk-tiers.md) | Hàng `attack`/`perf`/`migration_check`/`acceptance`/`rollback` của `release-check` chạy lệnh `xt.yaml`, PASS/FAIL theo exit code; chưa khai ở M/L → N/A BLOCKER (việc của người) | Hợp đồng kết quả có kiểu (§6) **mở rộng** các hàng này, không thay: hàng cũ giữ ngữ nghĩa, hàng mới đọc report theo adapter |
| [ADR-0010](../docs/adr/0010-feedback-from-target-projects.md), `LOOP-FB-*` | Khung kéo phản hồi về, mở PR nháp, người duyệt; ngưỡng sửa ≥ 2 dự án hoặc có bước tái hiện | Vòng học của xưởng (§7 lát E) là mở rộng của `feedback aggregate`, dùng cùng ngưỡng; không tạo kênh báo cáo thứ hai |
| [ADR-0001](../docs/adr/0001-framework-as-id-library-with-machine-composition.md), ADR-0003/0004/0012 | Khung = thư viện yêu cầu có ID; blueprint theo S/M/L; trần 4 MUST/module ở M | Gói sản phẩm là **lớp trên** profile/industry/scale, tham chiếu ID, không cấp ID mới và không đổi mức; yêu cầu mới (nếu có) vẫn qua `conventions.md` |
| #436 (D-341): bài học stored `XT-H-027…116` đã vào khung | `QA-STRAT-024` (SHOULD) đã ghi hợp đồng kết quả cổng test/scan theo XT-H-113: adapter + định dạng/phiên bản report, target/config, trạng thái hoàn tất, số test đã chạy; thiếu report/0 test/only-report/unknown không tính đạt | Phần "chữ" của §6 nhóm *Phạm vi*/*Kết quả* đã có nhà là `QA-STRAT-024`; đề xuất chỉ còn phần **máy** (adapter trong `release-check`) và các nhóm *Định danh*/*Artifact*/*Quyết định*/*Triển khai* |

## 4. Chuyển 34 chuyên mục thành năng lực xưởng

| Mục stored | Năng lực X-Templates nhận | Artifact/cổng tại repo sản phẩm |
|---|---|---|
| 28–29 | Discovery, đặc tả, kiến trúc và hợp đồng | Acceptance IDs → ADR/API/schema → compatibility và test truy vết |
| 06, 13, 30, 34 | Gói nền UI/API/data có thể dựng và nâng | Môi trường, dependency pin, DB/migration, auth/tenant, unit/integration/E2E |
| 01–05, 11–12, 17, 20–21 | Agent/harness/tự động hóa theo quyền và ngân sách | Task evidence, sandbox probes, tool policy, replay/idempotency, host conformance |
| 07, 10, 14–15, 24–26 | Gói tùy chọn AI/data | Corpus/version/quyền dữ liệu, baseline, eval, chi phí và phục hồi job |
| 19, 22, 27 | Gói media/motion/CAD theo môi trường đích | Asset/model license, timebase/unit, output invariants và host read-back |
| 09, 31–32 | Supply chain và phát hành | SBOM/provenance, verify identity/digest, rollout/rollback và release decision |
| 33 | Vận hành và phục hồi | SLO, export telemetry đã lọc, alert/restore drill và deployment inventory |
| 08, 16, 18, 23 | Học tập, tài liệu, bối cảnh Việt Nam và bài học | Hướng dẫn có phép kiểm, nguồn có ngày, regression và thông báo nâng cấp |

(Bản 2 đã đối chiếu: 34/34 mục có mặt đúng một lần; nhóm khớp bảng §1–§2 của FACTORY.md.)

Mỗi công cụ đi qua lựa chọn có phạm vi: đọc nguồn → đối chiếu control → thử ở repo tích hợp → adapter/fixture → gói được hỗ trợ. Chỉ mở thêm lựa chọn khi có nhu cầu thực tế và người duy trì; dùng đường nhỏ đáp ứng tác vụ trước.

## 5. Hợp đồng gói sản phẩm được hỗ trợ

Gói được đề xuất là một lớp phía trên profile/industry hiện có, không đổi nghĩa các slug đang dùng. Gói chứa hoặc tham chiếu:

- ID/version, owner, thời hạn hỗ trợ và compatibility với core, runtime, hệ điều hành và host đã kiểm.
- Profile/industry/features và control ID được tái sử dụng; loại bằng chứng máy, người hoặc bên ngoài cho từng control áp dụng.
- Code khởi đầu, toolchain/dependency locks, môi trường và lệnh `xt.yaml` đã xác minh cho một stack cụ thể.
- Acceptance suite cho critical journeys, fixture âm, dữ liệu thử đại diện và artifact schema/version.
- CI/build/release, migration, rollback, restore, telemetry và runbook theo phạm vi sản phẩm.
- Owned paths, cách giữ tùy biến, kế hoạch nâng N → N+1, conflict/drift report và đường lùi.

Nền đã có để dựng gói mà không thêm cơ chế mới: `framework/templates/` (mẫu `ci.yml`, `xt.yaml`, `AGENTS.md`, tài liệu G0–G8, `git-hooks/`, `harness/`, `ui-gates/`) + `install.py` (manifest hash, copy-if-absent, `.xtemplates-new`, `--plan`) + profile `02-profiles/web-app.md`, `api-service.md`. Gói = một thư mục thêm *code khởi đầu + lock + acceptance suite* lên trên bộ này; `install.py --pack <tên>` là phần mở rộng tự nhiên của `--harness`/`--with-github`.

**Tuyến đầu đề xuất: Web/API nghiệp vụ nhiều tenant.** Nghiệm thu một lát dọc: tạo repo → dựng môi trường/DB thật cho kiểm tích hợp → đăng nhập → tạo dữ liệu → chặn tenant khác → migration → staging → promote đúng digest → rollback/restore → kiểm dữ liệu và quyền còn đúng. Dùng dữ liệu thử, không suy test fixture thành xác nhận mọi dữ liệu production.

Tuyến thứ hai chọn theo nhu cầu dự án: API/worker phải thử duplicate/timeout/crash và reconcile; AI/data phải có baseline, corpus/eval có phiên bản, quyền dữ liệu và ngân sách. Chỉ đóng gói các phiên bản đã kiểm; không mặc nhiên công bố hỗ trợ mọi framework.

## 6. Bằng chứng và quyết định phát hành có kiểu

Giữ evidence v2 và source-tree fingerprint hiện tại, mở rộng bằng schema có phiên bản thay vì âm thầm đổi ý nghĩa trường cũ.

| Nhóm | Trường/hành vi đề xuất | Ca phải từ chối hoặc chờ | Nhà hiện có (ID / mã) |
|---|---|---|---|
| Định danh | Source SHA, candidate digest, workflow/run ID, producer identity | Artifact đổi byte, báo cáo từ candidate khác | `evidence_fp`/`candidate_head` (gói nghiệm thu); `OPS-DEPLOY-001`, `WF-ENV-006`, `WF-REL-005` (build một lần, cùng digest) — **thiếu**: digest artifact trong gói nghiệm thu |
| Phạm vi | Target/suite, config, environment/tool/dataset revision | Sai target, thiếu kiểm bắt buộc hoặc môi trường chưa phù hợp | `QA-STRAT-024` (chữ), evidence v2 `scope`/`req_rev` (máy, mức task) |
| Kết quả | PASS/FAIL/PENDING/BLOCKED/INCONCLUSIVE/NOT-APPLICABLE; số test thực chạy khi áp dụng | 0 test, cancelled, timeout hạ tầng, scan chưa xong hoặc dữ liệu scan thiếu | `QA-STRAT-024` (chữ); `LOOP-HARNESS-023` (sàn no-op); máy: `zero_tests_red` chỉ regex `Ran 0 tests` của unittest, `_release_run` chỉ exit code — **thiếu** adapter đọc report (JUnit/SARIF/JSON) |
| Artifact bằng chứng | URI, checksum, quyền xem, thời điểm và hiệu lực theo loại kiểm | Mất artifact, hết hiệu lực, checksum sai | `BASE-GATE-014` (SHOULD, lưu ≥ 30 ngày); `SEC-SUPPLY-013/014/033` (ký, provenance, verify) — **thiếu**: `release-check` đọc artifact/checksum |
| Quyết định | Verdict, người/identity có quyền, subject digest, ngoại lệ có owner/expiry | Đang chờ, bị từ chối, sai subject, ngoại lệ hết hạn | `stage approve` (ADR-0058: `by` tự khai, không chữ ký), GO-NO-GO §5 (`_go_no_go_signed`: dòng tên + ngày), miễn trừ `— Miễn:` có `Duyệt:` — **thiếu**: subject digest và hạn của ngoại lệ |
| Triển khai | Service/environment, digest, deployment ID/time, smoke/health result | Bản đang chạy khác bản đã kiểm hoặc thiếu xác nhận sau deploy | `OPS-DEPLOY-005` (MUST@L, marker deploy) — **thiếu**: khung không đọc receipt nào; `prod_switch` là quyết định, không phải receipt |

Ngưỡng và tập kiểm do risk/critical journeys quyết định. Cổng tĩnh không có test count cần điều kiện riêng. Control cần người xác nhận có receipt/quyền tương ứng; không ép mọi yêu cầu thành một lệnh luôn xanh. Dữ liệu nhạy cảm được lọc trước khi lưu/truyền; quyền phát hành do CI/IAM/environment thực thi.

Ba điểm đọc mã cần được giữ đúng khi thiết kế (xác minh lại 2026-11-04 trên `9c03257`, cùng số dòng):

1. [`_release_run`](https://github.com/seeker19110/X-Templates/blob/e0ea0a6c97576f96611e42dad05d21907745c4f7/scripts/xt.py#L12186) dùng exit status của lệnh cấu hình để tạo hàng PASS/FAIL. Adapter cần bổ sung ngữ nghĩa kết quả của từng loại kiểm.
2. [`release_check`](https://github.com/seeker19110/X-Templates/blob/e0ea0a6c97576f96611e42dad05d21907745c4f7/scripts/xt.py#L12289) trả `go = not fails` nên `go=true` cùng `verdict: "GO (chờ người)"` khi còn hàng N/A BLOCKER; [`cmd_release_check`](https://github.com/seeker19110/X-Templates/blob/e0ea0a6c97576f96611e42dad05d21907745c4f7/scripts/xt.py#L12322) trả **exit 0** trong trường hợp đó. Consumer hiện tại phải đọc cả `human` và `verdict`; hợp đồng mới cần trạng thái promotion rõ ràng và kế hoạch tương thích ngược.
3. [`_go_no_go_signed`](https://github.com/seeker19110/X-Templates/blob/e0ea0a6c97576f96611e42dad05d21907745c4f7/scripts/xt.py#L12213) nhận diện dòng tên/ngày ở mục ký, còn [`_release_go_no_go`](https://github.com/seeker19110/X-Templates/blob/e0ea0a6c97576f96611e42dad05d21907745c4f7/scripts/xt.py#L12232) đối chiếu VERSION. Đường kiểm này chưa là xác minh quyền người ký, nội dung quyết định hoặc digest candidate; phần mở rộng cần kiểm các yếu tố đó ở hệ có quyền phù hợp.

Fixture âm của hợp đồng mới phải chứng minh lỗi đã biết làm cổng tương ứng không cho promote. Build một candidate rồi đưa cùng digest qua các môi trường; rebuild tạo candidate mới phải có bằng chứng cho candidate đó.

## 7. Lộ trình theo bằng chứng, chưa ấn định lịch phát hành

| Lát đề xuất | Phạm vi | Điều kiện nghiệm thu trước khi nhân rộng | Ứng viên/nền đã có (bản 2) |
|---|---|---|---|
| A · hợp đồng kết quả/phát hành | Schema có version, adapter cho một bộ runner/scan nhỏ, receipt và compatibility | Sai digest, report thiếu, 0 test, scan pending, approval chờ/từ chối/hết hạn đều không promote; có positive fixture | Mở rộng `RELEASE_RUN_KEYS`/`_release_run` và gói nghiệm thu; bộ runner đầu: unittest/pytest (JUnit XML), SARIF (CodeQL/gitleaks đã dùng ở CI khung), `pip-audit` JSON (đã có ở `dep-audit`); fixture ở `tests/fixtures/` |
| B · tuyến Web/API đầu tiên | Một stack cụ thể, self-host development, acceptance/CI/data/release/ops | Repo sạch chạy được lát dọc ở §5; ca auth/tenant, contract/migration cố tình sai làm cổng đỏ | Tiền lệ CI: job `app-e2e` (Playwright ghim hash qua `requirements-e2e.txt`, `tests_e2e/`); profile `web-app` + `api-service`; mẫu `framework/templates/` |
| C · nâng dự án hiện hữu | Chọn một repo đích phù hợp, giữ stack/tùy biến, thử nâng gói | Cài lại idempotent; N → N+1 giữ sửa đổi, lộ conflict/drift và có rollback; kiểm lại critical journeys | [TARGETS.md](../docs/ops/TARGETS.md): hotel-manager (3.15.1, 188 FB — nhiều tín hiệu nhất), X-Company (3.15.1, 91 FB), dhcb (3.15.3), xboss (2.0.0); PR nâng 3.14 còn chờ chủ dự án (hotel-manager #117, X-Company #65) — lát C chỉ bắt đầu sau khi hai PR đó có kết luận |
| D · tuyến thứ hai và host thật | API/worker hoặc AI/data; kiểm các host/version được chọn | Corpus/side-effect recovery theo tuyến; host trust, hook failure/timeout và sandbox probes có kết quả thực | `T-3642`…`T-3644` (fixture payload thật, cầu nối file hướng dẫn) còn mở ở PLAN-upgrade-2026-11-02; thứ tự host theo ADR-0064: Codex, Gemini trước; mốc 2027-01-21 |
| E · nhiều sản phẩm | Registry và tổng hợp dựa trên CLI/CI/feedback sẵn có | Truy ra phiên bản core/gói/digest/owner; incident thành regression và đợt nâng có phạm vi | Mở rộng `docs/ops/TARGETS.md` thành registry (thêm cột core/gói/version/owner/release gần nhất); `feedback aggregate --from` đã gộp 4 repo (2026-10-23, T-2410) |

A và B được thực hiện thành các PR nhỏ theo dependency; C cần phiên bản gói có thể nâng, E cần bằng chứng từ nhiều dự án. Không lấy thứ tự bảng làm lý do trì hoãn lỗi an toàn đã xác nhận ở dự án đang chạy. Mọi thay đổi hành vi, schema công khai, policy hoặc dependency đều cần ADR/kiểm riêng theo quy trình hiện hành. Việc đang mở của khung (T-3636, T-3669…3671 ở PLAN-upgrade-2026-11-02; perf trial T-3551/3552/3557) đi trước lát A — không chen vào mốc 3.30.0.

Registry ban đầu có thể là YAML/JSON: repo, owner, loại sản phẩm, risk, core/gói/version, service/environment, budget/SLO, release gần nhất và ngoại lệ còn hạn. Dashboard là lớp đọc (`xt.py app` đã là app cục bộ stdlib — ADR-0038 — có thể thêm một trang đọc registry); credential vẫn tách theo dự án và môi trường. Bảo toàn feedback aggregation hiện có, mở rộng đường incident → nguyên nhân → control → regression → bản gói sửa → dự án cần nâng.

## 8. Chỉ số và baseline đã có

Theo dõi thời gian từ yêu cầu được chấp nhận tới release được nghiệm thu; critical-journey/outcome theo baseline; tỷ lệ ca lỗi đã biết bị bắt; promote đúng digest; độ mới/đầy đủ bằng chứng; restore theo RPO/RTO đã chọn; chi phí mỗi tác vụ được chấp nhận; thời gian nâng gói và số repo drift. Ghi cửa sổ đo, mẫu số, lỗi hạ tầng và phần chưa chạy. Các mục tiêu số cần baseline từ dự án, không coi thông lượng task/PR là bằng chứng giá trị cuối.

Baseline đã có ở repo khung (không cần công cụ mới để bắt đầu đo):

| Chỉ số xưởng | Phép đo đang có | Giá trị gần nhất |
|---|---|---|
| Dòng giao hàng (lead time, run CI/PR, xanh lần đầu) | `xt.py pr stats --days 7` | 2026-11-03: 123 PR merge; lead time trung vị 0,63 giờ · P95 5,51 giờ; xanh ngay lần push đầu 96/123 (PROGRESS.md §Bàn giao) |
| Tỉ lệ giao việc / xanh lần đầu theo tầng agent | `xt.py loop stats` (`LOOP-ORCH-020`, ADR-0061) | tích luỹ từ PLAN-upgrade; chưa có số công bố |
| Tỷ lệ ca lỗi đã biết bị bắt (hàng rào) | `xt.py autonomy-bench` ([AUTONOMY-BASELINE.md](../docs/ops/AUTONOMY-BASELINE.md)); `mutate-guard` 37/37 | corpus guard 1.069 ca (ADR-0064 ghi chú 2026-11-03) |
| Phản hồi dự án đích | `feedback aggregate` | 2026-10-23: 63 nhóm đủ ngưỡng, 10 `cong-cu` chờ phân loại |
| Promote đúng digest · restore RPO/RTO · chi phí/tác vụ | **chưa có phép đo** | cần lát A (receipt) và một dự án đích có deploy thật |

## 9. Đề xuất trả lời bốn câu hỏi mở (bản 2)

Theo AGENTS.md §4, mỗi câu dưới đây có ≥ 2 phương án và một đề xuất theo tiêu chí chất lượng cuối (đúng/an toàn → đường lùi → bền/đơn giản → trải nghiệm → tốc độ). Đây là **đề xuất của phiên khung**; chủ dự án đã chốt 2026-11-04 đúng bốn đề xuất (1a · 2a hotel-manager · 3a · 4a — D-353, ADR-0068).

**Câu 1 — Phương án lõi + gói + adapter, và nơi lưu gói.**
Phương án: (a) gói nằm trong repo khung tại `framework/templates/packs/<stack>/`, phiên bản theo `VERSION` của khung; (b) mỗi gói một repo riêng, khung chỉ giữ registry + hợp đồng; (c) không có gói, chỉ thêm ID/mẫu như hiện nay.
**Đề xuất (a) cho gói đầu tiên, chuyển (b) khi có ≥ 2 gói hoặc owner khác chủ khung.** Lý do: một gói, một owner, một `VERSION` — `install.py` đã có manifest/`.xtemplates-new` nên nâng N → N+1 dùng cơ chế sẵn có (tiêu chí 3); đường lùi là xoá thư mục gói (tiêu chí 2); (b) sớm tạo chi phí đồng bộ phiên bản chéo repo chưa cần; (c) không đạt mục tiêu "lát dọc chạy được từ repo sạch". Ràng buộc: gói không kéo dependency vào CLI stdlib; mã adapter kết quả ở `xt.py` trong trần nhóm `scripts` (§3b).

**Câu 2 — Stack và repo thử cho tuyến Web/API.**
Phương án: (a) stack của dự án đích sẽ nâng ở lát C (hotel-manager, theo TARGETS.md: nhiều phản hồi nhất) — B và C dùng chung một gói; (b) TypeScript theo hàng 1 của FACTORY.md §5 bất kể stack dự án đích; (c) Python/FastAPI theo hệ sinh thái của chính khung.
**Đề xuất (a); stack cụ thể "(chưa xác minh)" — phiên khung không đọc được repo hotel-manager trong phiên này.** Lý do: một gói phục vụ cả repo sạch (B) lẫn brownfield (C) là bằng chứng mạnh nhất với chi phí một stack (tiêu chí 3, 5); nếu stack hotel-manager không phải Web/API nhiều tenant thì lấy X-Company; (b)/(c) chỉ khi không dự án đích nào phù hợp. Owner bảo trì gói: chủ dự án (một người giữ nhiều vai, theo FACTORY.md §3). Critical journeys đại diện: lát dọc §5 (đăng nhập → dữ liệu → cách ly tenant → migration → promote digest → rollback/restore).

**Câu 3 — Phiên bản/schema bằng chứng, trạng thái chờ/đã duyệt, tương thích CLI cũ.**
Phương án: (a) evidence v3 **thêm trường** (`schema: 3`, `artifacts[]{uri, sha256, kind, expires}`, `results[]{adapter, status, executed, run_id}`), evidence v2 vẫn đọc được như trước (`evidence_stale` chỉ đòi chạy lại khi thiếu trường v2 — giữ); `release-check --json` thêm `promotion: approved|pending_human|rejected|inconclusive` và `subject: {head, evidence_fp, artifact_digest}`, **giữ** `go`/`verdict`/`human` ít nhất một bản minor; (b) đổi ngữ nghĩa `go` thành "đã duyệt" (phá consumer: `signoff-package`, `_step_signoff`, Stop hook); (c) sổ riêng `docs/autopilot/RELEASE.json` kiểu STAGE.json.
**Đề xuất (a).** Lý do: không đổi nghĩa trường cũ (tiêu chí 1, bài học `evidence_stale`/AUTO-02); exit code của `cmd_release_check` giữ nguyên tới khi có bản major; "đã duyệt" vẫn chỉ là `stage approve`/GO-NO-GO §5 của người theo ADR-0058 — máy không tự nâng `pending_human` thành `approved`. (c) là lựa chọn ở lát A nếu receipt cần lịch sử phát lại như STAGE.json; quyết ở PR lát A với test đỏ trước.

**Câu 4 — Tuyến thứ hai, host/version, điều kiện công bố mức kiểm chứng.**
Phương án: (a) API/worker (cùng stack với gói đầu, thêm duplicate/timeout/crash/reconcile) rồi mới AI/data; (b) AI/data trước vì stored có nhiều mục AI nhất; (c) không tuyến thứ hai trong 3.x.
**Đề xuất (a); host: Codex và Gemini CLI trước (OSI, thứ tự ADR-0064), mỗi host công bố mức theo thang của stored METHOD.md §2 (`docs-read` → `code-read` → `checks-run` → `reproduced`) và chỉ ghi "hỗ trợ" khi đạt `checks-run` với fixture payload thật của bản đã ghi.** Lý do: API/worker tái dùng gói, DB và acceptance của tuyến đầu (tiêu chí 3); AI/data cần corpus/quyền dữ liệu thật mà chủ dự án phải cung cấp (điểm dừng "dữ liệu người dùng thật", AGENTS.md §5) — làm sau khi có một dự án đích có nhu cầu; (c) để ngỏ nếu lát A/B tiêu hết ngân sách trước mốc 2027-01-21.

Không tạo task triển khai hoặc cấp ID yêu cầu mới trong PR này. Sau khi định hướng được duyệt (ADR-0068 → *Đã chấp nhận*), mở PLAN riêng và các lát theo §7; các gói chưa vượt nghiệm thu tiếp tục được ghi là thử nghiệm.

## 10. Nhật ký xác minh (bản 2, 2026-11-04)

| Mục | Cách kiểm | Kết quả |
|---|---|---|
| Số dòng `xt.py` của 6 liên kết §2/§6 | `grep -n "^def "` trên `9c03257` | khớp: `evidence_meta` 2260, `_step_signoff` 8033, `feedback_aggregate` 11196, `_release_run` 12186, `_go_no_go_signed` 12213, `_release_go_no_go` 12232, `release_check` **12289** (bản 1 trỏ 12309 — giữa thân hàm; đã sửa), `cmd_release_check` 12322 |
| `release-check` exit 0 khi "GO (chờ người)" | đọc `cmd_release_check` dòng 12335: `return 0 if out["go"] else 1`; `go = not fails` | đúng như §6 điểm 2 |
| `zero_tests_red` chỉ regex | `xt.py` dòng 2725–2729 (`ZERO_TESTS_RE`, `Ran 0 tests`) | đúng (khớp XT-H-113 `existing_coverage`) |
| `QA-STRAT-024` đã có sau #436 | `git show 9c03257 -- framework/14-testing-quality/test-strategy.md` | có, mức SHOULD; là nhà của phần chữ XT-H-113 |
| 34 mục ở §4 | đối chiếu từng số với bảng §2 FACTORY.md | 34/34, không trùng, không thiếu |
| Số hồ sơ stored (1.040; 37 mới; 16 đọc sâu) | README stored dòng 15 và 386 tại `5d8f8a6` | khớp |
| PR seeker19110/stored#131 đã merge | API GitHub của stored ngoài phạm vi phiên; github.com qua proxy trả 403 | **chưa xác minh**; nội dung tại commit `5d8f8a6` đọc được qua raw |
| Trần byte nhóm `scripts` | `git ls-files -z -- 'scripts/*.py' scripts/xt_app/ \| xargs -0 cat \| wc -c` | 1.045.208 B / 1.760.431 B |
| Stack của hotel-manager, X-Company | không có repo trong phiên; research/docs khung không ghi stack | **chưa xác minh** (ghi ở câu 2) |
