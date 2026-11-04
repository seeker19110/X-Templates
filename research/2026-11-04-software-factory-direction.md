---
title: Đề xuất X-Templates thành xưởng phần mềm dựa trên 34 chuyên mục stored
kind: research
updated: 2026-11-04
---

# Đề xuất định hướng xưởng phát triển phần mềm

> **Trạng thái: đề xuất để thảo luận, chưa là quyết định kiến trúc đã chấp nhận.** PR này chỉ thêm nghiên cứu và liên kết chỉ mục; chưa thêm ID, đổi mức yêu cầu, cấu hình mặc định, hành vi CLI, schema hay dependency. Các đường chạy và tiêu chí dưới đây là mục tiêu triển khai ở các PR riêng, chưa là kết quả đã kiểm chứng.

## 1. Mục tiêu và phạm vi bằng chứng

Định vị đề xuất: **X-Templates là bộ máy giao hàng phần mềm có kiểm chứng**, giúp biến yêu cầu thành sản phẩm có thể phát hành, vận hành, nâng cấp và phục hồi. Đơn vị thành công là một lát nghiệp vụ được nghiệm thu trên sản phẩm, gắn với artifact và kết quả thực địa.

Đối chiếu ngày 2026-11-04:

- X-Templates **3.29.0**, commit [e0ea0a6c97576f96611e42dad05d21907745c4f7](https://github.com/seeker19110/X-Templates/tree/e0ea0a6c97576f96611e42dad05d21907745c4f7): đọc tài liệu, implementation và CI; chưa chạy sản phẩm/deployment để xác minh các tuyến đề xuất.
- stored, commit [5d8f8a6d6a5245fa3cf543cac57d2d2bb5b8f2d9](https://github.com/seeker19110/stored/tree/5d8f8a6d6a5245fa3cf543cac57d2d2bb5b8f2d9), [PR #131 đã merge](https://github.com/seeker19110/stored/pull/131): 34 chuyên mục, 1.040 hồ sơ; đợt mới có 37 hồ sơ mới và 16 đọc sâu, không xác minh lại toàn bộ lịch sử.
- Đầu vào chính: [FACTORY.md](https://github.com/seeker19110/stored/blob/5d8f8a6d6a5245fa3cf543cac57d2d2bb5b8f2d9/FACTORY.md), [GUIDES.md](https://github.com/seeker19110/stored/blob/5d8f8a6d6a5245fa3cf543cac57d2d2bb5b8f2d9/GUIDES.md), [phương pháp](https://github.com/seeker19110/stored/blob/5d8f8a6d6a5245fa3cf543cac57d2d2bb5b8f2d9/METHOD.md) và [bàn giao XT-H-113…116](https://github.com/seeker19110/stored/blob/5d8f8a6d6a5245fa3cf543cac57d2d2bb5b8f2d9/data/xt-handoff.json).

Kết quả kiểm tài liệu/CLI của repo khung, nếu có trong PR, chỉ chứng minh thay đổi này giữ hợp đồng hiện tại; không chứng minh xưởng đã vận hành. Các vị trí nguồn trong bảng dưới áp dụng snapshot X-Templates đã nêu.

## 2. Nền hiện có và phần nên làm sâu

| Năng lực | Đã có ở snapshot | Phần nâng tiếp được đề xuất |
|---|---|---|
| Vòng đời và composition | G0–G8, S/M/L, build/harden; `compose` sinh blueprint/backlog, giữ ID và đánh dấu mục đổi nội dung | Một gói sản phẩm ghép đúng control với stack, cấu hình chạy và acceptance suite; giữ quy trình hiện có |
| Cài và nâng khung | Installer cài thư viện, CLI, harness, Git hooks và CI; hash/manifest giữ file tùy chỉnh, có `--plan` và bản `.xtemplates-new` khi cần gộp | Mở rộng ownership, compatibility và migration sang phiên bản gói sản phẩm; kiểm cả repo mới và brownfield |
| Bằng chứng task | Evidence v2 gắn command hash, scope, revision yêu cầu và digest file | Bổ sung environment/tool/dataset và kết quả có kiểu; nối đến artifact build/deploy |
| Phát hành | `release-check`, gói nghiệm thu có `candidate_head`/`evidence_fp`, stage ledger tùy chọn | Quyết định phát hành rõ trạng thái và chủ thể; receipt của artifact/môi trường thực sự triển khai |
| Agent host | Lõi guard chung, sáu adapter ngoài Claude, Git hook sàn và vòng lặp ngoài | Conformance theo host/version trên công cụ thật, trust activation và ranh giới sandbox được kiểm |
| Vòng học | Feedback aggregation nhiều dự án và control về metrics, budget, SLO | Incident → control → fixture regression → bản gói sửa lỗi → danh sách dự án cần nâng |

Nguồn: [composition](../framework/00-method/composition.md), [installer](../scripts/install.py), [evidence](https://github.com/seeker19110/X-Templates/blob/e0ea0a6c97576f96611e42dad05d21907745c4f7/scripts/xt.py#L2260), [signoff](https://github.com/seeker19110/X-Templates/blob/e0ea0a6c97576f96611e42dad05d21907745c4f7/scripts/xt.py#L8033), [ADR-0064](../docs/adr/0064-multi-provider-harness.md), [giới hạn adapter](../framework/templates/harness/README.md), [feedback](https://github.com/seeker19110/X-Templates/blob/e0ea0a6c97576f96611e42dad05d21907745c4f7/scripts/xt.py#L11196).

Các khoảng cần nâng dưới đây được kết luận từ những đường gọi đã đọc; không khẳng định toàn repo không có cơ chế tương tự. Đặc biệt, adapter đã có implementation/test payload; chính ADR-0064 ghi chưa chạy thật từng host. Mức hỗ trợ công bố nên phản ánh bằng chứng này.

## 3. Phân vai và lựa chọn kiến trúc

| Thành phần | Trách nhiệm | Hợp đồng bàn giao |
|---|---|---|
| stored | Nghiên cứu lựa chọn, cơ chế, license, nguồn và giới hạn | Hồ sơ có SHA, phạm vi, mức bằng chứng, alternative và bài học đối chiếu ID |
| X-Templates | Controls, composition, adapter, gói được hỗ trợ, chính sách và nâng cấp | Gói có phiên bản/owner, phép nghiệm thu, fixture âm, compatibility và migration notes |
| Repo sản phẩm | Nghiệp vụ, implementation, hạ tầng và vận hành cụ thể | Acceptance results, artifact digest, deployment receipt và số liệu thực địa có quyền truy cập phù hợp |

Ba phương án đã cân nhắc:

1. **Mở rộng thư viện yêu cầu theo từng công cụ mới:** chi phí ban đầu thấp, nhưng dự án vẫn phải tự nối cấu hình và bằng chứng. Phù hợp làm nguồn tham khảo, chưa đủ mục tiêu giao hàng lặp lại.
2. **Một nền tảng tập trung quản toàn bộ agent/build/deploy:** có thể thống nhất trải nghiệm, nhưng tăng quyền tập trung, vận hành và migration trước khi chứng minh được tuyến sản phẩm.
3. **Lõi hiện có + gói sản phẩm/adapter có phiên bản + điều phối nhiều dự án ở mức cần thiết:** tận dụng CLI/CI, quyền riêng từng repo và feedback đã có. Đây là phương án đề xuất; đổi cấu trúc/công cụ chỉ thực hiện qua ADR riêng sau khi chốt phạm vi.

Giữ lõi CLI stdlib và một nhà cho policy theo các ADR hiện hành. Gói stack có thể khai dependency theo hệ sinh thái của sản phẩm, có pin/license/owner; không biến chúng thành dependency bắt buộc của CLI khung. Tự host là đường phát triển mặc định theo ADR-0008; tích hợp bắt buộc cần tài khoản riêng có adapter giả và contract test, còn nghiệm thu production vẫn phải kiểm trên đích thật.

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

Mỗi công cụ đi qua lựa chọn có phạm vi: đọc nguồn → đối chiếu control → thử ở repo tích hợp → adapter/fixture → gói được hỗ trợ. Chỉ mở thêm lựa chọn khi có nhu cầu thực tế và người duy trì; dùng đường nhỏ đáp ứng tác vụ trước.

## 5. Hợp đồng gói sản phẩm được hỗ trợ

Gói được đề xuất là một lớp phía trên profile/industry hiện có, không đổi nghĩa các slug đang dùng. Gói chứa hoặc tham chiếu:

- ID/version, owner, thời hạn hỗ trợ và compatibility với core, runtime, hệ điều hành và host đã kiểm.
- Profile/industry/features và control ID được tái sử dụng; loại bằng chứng máy, người hoặc bên ngoài cho từng control áp dụng.
- Code khởi đầu, toolchain/dependency locks, môi trường và lệnh `xt.yaml` đã xác minh cho một stack cụ thể.
- Acceptance suite cho critical journeys, fixture âm, dữ liệu thử đại diện và artifact schema/version.
- CI/build/release, migration, rollback, restore, telemetry và runbook theo phạm vi sản phẩm.
- Owned paths, cách giữ tùy biến, kế hoạch nâng N → N+1, conflict/drift report và đường lùi.

**Tuyến đầu đề xuất: Web/API nghiệp vụ nhiều tenant.** Nghiệm thu một lát dọc: tạo repo → dựng môi trường/DB thật cho kiểm tích hợp → đăng nhập → tạo dữ liệu → chặn tenant khác → migration → staging → promote đúng digest → rollback/restore → kiểm dữ liệu và quyền còn đúng. Dùng dữ liệu thử, không suy test fixture thành xác nhận mọi dữ liệu production.

Tuyến thứ hai chọn theo nhu cầu dự án: API/worker phải thử duplicate/timeout/crash và reconcile; AI/data phải có baseline, corpus/eval có phiên bản, quyền dữ liệu và ngân sách. Chỉ đóng gói các phiên bản đã kiểm; không mặc nhiên công bố hỗ trợ mọi framework.

## 6. Bằng chứng và quyết định phát hành có kiểu

Giữ evidence v2 và source-tree fingerprint hiện tại, mở rộng bằng schema có phiên bản thay vì âm thầm đổi ý nghĩa trường cũ.

| Nhóm | Trường/hành vi đề xuất | Ca phải từ chối hoặc chờ |
|---|---|---|
| Định danh | Source SHA, candidate digest, workflow/run ID, producer identity | Artifact đổi byte, báo cáo từ candidate khác |
| Phạm vi | Target/suite, config, environment/tool/dataset revision | Sai target, thiếu kiểm bắt buộc hoặc môi trường chưa phù hợp |
| Kết quả | PASS/FAIL/PENDING/BLOCKED/INCONCLUSIVE/NOT-APPLICABLE; số test thực chạy khi áp dụng | 0 test, cancelled, timeout hạ tầng, scan chưa xong hoặc dữ liệu scan thiếu |
| Artifact bằng chứng | URI, checksum, quyền xem, thời điểm và hiệu lực theo loại kiểm | Mất artifact, hết hiệu lực, checksum sai |
| Quyết định | Verdict, người/identity có quyền, subject digest, ngoại lệ có owner/expiry | Đang chờ, bị từ chối, sai subject, ngoại lệ hết hạn |
| Triển khai | Service/environment, digest, deployment ID/time, smoke/health result | Bản đang chạy khác bản đã kiểm hoặc thiếu xác nhận sau deploy |

Ngưỡng và tập kiểm do risk/critical journeys quyết định. Cổng tĩnh không có test count cần điều kiện riêng. Control cần người xác nhận có receipt/quyền tương ứng; không ép mọi yêu cầu thành một lệnh luôn xanh. Dữ liệu nhạy cảm được lọc trước khi lưu/truyền; quyền phát hành do CI/IAM/environment thực thi.

Ba điểm đọc mã cần được giữ đúng khi thiết kế:

1. [`_release_run`](https://github.com/seeker19110/X-Templates/blob/e0ea0a6c97576f96611e42dad05d21907745c4f7/scripts/xt.py#L12186) dùng exit status của lệnh cấu hình để tạo hàng PASS/FAIL. Adapter cần bổ sung ngữ nghĩa kết quả của từng loại kiểm.
2. [`release_check`](https://github.com/seeker19110/X-Templates/blob/e0ea0a6c97576f96611e42dad05d21907745c4f7/scripts/xt.py#L12309) có thể trả `go=true`/exit 0 cùng `GO (chờ người)`. Consumer hiện tại phải đọc cả `human` và `verdict`; hợp đồng mới cần trạng thái promotion rõ ràng và kế hoạch tương thích ngược.
3. [`_go_no_go_signed`](https://github.com/seeker19110/X-Templates/blob/e0ea0a6c97576f96611e42dad05d21907745c4f7/scripts/xt.py#L12213) nhận diện dòng tên/ngày ở mục ký, còn [`_release_go_no_go`](https://github.com/seeker19110/X-Templates/blob/e0ea0a6c97576f96611e42dad05d21907745c4f7/scripts/xt.py#L12232) đối chiếu VERSION. Đường kiểm này chưa là xác minh quyền người ký, nội dung quyết định hoặc digest candidate; phần mở rộng cần kiểm các yếu tố đó ở hệ có quyền phù hợp.

Fixture âm của hợp đồng mới phải chứng minh lỗi đã biết làm cổng tương ứng không cho promote. Build một candidate rồi đưa cùng digest qua các môi trường; rebuild tạo candidate mới phải có bằng chứng cho candidate đó.

## 7. Lộ trình theo bằng chứng, chưa ấn định lịch phát hành

| Lát đề xuất | Phạm vi | Điều kiện nghiệm thu trước khi nhân rộng |
|---|---|---|
| A · hợp đồng kết quả/phát hành | Schema có version, adapter cho một bộ runner/scan nhỏ, receipt và compatibility | Sai digest, report thiếu, 0 test, scan pending, approval chờ/từ chối/hết hạn đều không promote; có positive fixture |
| B · tuyến Web/API đầu tiên | Một stack cụ thể, self-host development, acceptance/CI/data/release/ops | Repo sạch chạy được lát dọc ở §5; ca auth/tenant, contract/migration cố tình sai làm cổng đỏ |
| C · nâng dự án hiện hữu | Chọn một repo đích phù hợp, giữ stack/tùy biến, thử nâng gói | Cài lại idempotent; N → N+1 giữ sửa đổi, lộ conflict/drift và có rollback; kiểm lại critical journeys |
| D · tuyến thứ hai và host thật | API/worker hoặc AI/data; kiểm các host/version được chọn | Corpus/side-effect recovery theo tuyến; host trust, hook failure/timeout và sandbox probes có kết quả thực |
| E · nhiều sản phẩm | Registry và tổng hợp dựa trên CLI/CI/feedback sẵn có | Truy ra phiên bản core/gói/digest/owner; incident thành regression và đợt nâng có phạm vi |

A và B được thực hiện thành các PR nhỏ theo dependency; C cần phiên bản gói có thể nâng, E cần bằng chứng từ nhiều dự án. Không lấy thứ tự bảng làm lý do trì hoãn lỗi an toàn đã xác nhận ở dự án đang chạy. Mọi thay đổi hành vi, schema công khai, policy hoặc dependency đều cần ADR/kiểm riêng theo quy trình hiện hành.

Registry ban đầu có thể là YAML/JSON: repo, owner, loại sản phẩm, risk, core/gói/version, service/environment, budget/SLO, release gần nhất và ngoại lệ còn hạn. Dashboard là lớp đọc; credential vẫn tách theo dự án và môi trường. Bảo toàn feedback aggregation hiện có, mở rộng đường incident → nguyên nhân → control → regression → bản gói sửa → dự án cần nâng.

## 8. Chỉ số và quyết định cần chốt

Theo dõi thời gian từ yêu cầu được chấp nhận tới release được nghiệm thu; critical-journey/outcome theo baseline; tỷ lệ ca lỗi đã biết bị bắt; promote đúng digest; độ mới/đầy đủ bằng chứng; restore theo RPO/RTO đã chọn; chi phí mỗi tác vụ được chấp nhận; thời gian nâng gói và số repo drift. Ghi cửa sổ đo, mẫu số, lỗi hạ tầng và phần chưa chạy. Các mục tiêu số cần baseline từ dự án, không coi thông lượng task/PR là bằng chứng giá trị cuối.

PR đề xuất này cần thảo luận và chốt trước khi lập kế hoạch triển khai:

1. Chọn phương án lõi + gói có phiên bản + adapter; ranh giới và nơi lưu code/gói cụ thể sẽ do ADR quyết định.
2. Chọn stack và repo thử cho tuyến Web/API, owner bảo trì và critical journeys đại diện.
3. Chốt phiên bản/schema bằng chứng, cách phân biệt quyết định chờ/đã duyệt và phạm vi tương thích CLI cũ.
4. Chọn tuyến thứ hai, host/version cần hỗ trợ và điều kiện công bố mức kiểm chứng.

Không tạo task triển khai hoặc cấp ID yêu cầu mới trong PR này. Sau khi định hướng được duyệt, mở ADR và các lát theo §7; các gói chưa vượt nghiệm thu tiếp tục được ghi là thử nghiệm.
