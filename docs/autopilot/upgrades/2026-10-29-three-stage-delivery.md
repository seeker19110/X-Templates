# Giao hàng ba giai đoạn trên một chu trình sản phẩm thống nhất

Ngày: 2026-10-29. Phạm vi yêu cầu: **mọi dự án đích** của X-Templates, không phụ thuộc loại phần mềm hoặc stack.

**Trạng thái: lát A+B đã triển khai bằng máy ([ADR-0058](../../adr/0058-product-stages-machine-lock.md), D-239)** — `xt.py stage`, sổ `docs/autopilot/STAGE.json`, khoá ở `loop init/next/record`, hàng `stage` của `release-check`, guard chặn agent duyệt/ghi tay sổ; test `tests/test_stage.py`. Lát C–F (§8) **chưa** làm: các mục khác bên dưới vẫn là thiết kế đề xuất, không phải khả năng đang có. Dự án chỉ chịu khoá khi có sổ (`xt.py stage init`); chưa dự án đích nào được nâng.

## 1. Hợp đồng sản phẩm đã chốt

Giữ nguyên chu trình tổng thể, đúng thứ tự:

**Ý tưởng → Nghiên cứu → Đặc tả → Thiết kế → Lập trình → Kiểm thử → Audit → Tối ưu → Production → Vận hành → Tăng trưởng.**

Áp dụng chu trình đó qua ba giai đoạn trưởng thành **tuần tự**:

1. **MVP:** bản chạy thử để chủ dự án duyệt và chỉnh sửa.
2. **Sản phẩm hoàn thiện:** đáp ứng phạm vi đã duyệt và điều kiện sử dụng thực tế.
3. **Tối ưu hiệu suất, tính năng, mã nguồn:** cải tiến có đo lường trên nền sản phẩm đã hoàn thiện.

Ba giai đoạn không thay thế chu trình 11 bước, cũng không chia nó thành ba đoạn rời. Mỗi giai đoạn có phạm vi, vòng lặp, bằng chứng và cổng hoàn thành riêng. Các bước được thực hiện với độ sâu phù hợp; không bắt nghiên cứu/viết lại toàn bộ tài liệu đã còn đúng ở mỗi vòng.

**Giai đoạn trước chưa hoàn thành thì giai đoạn sau bị khóa.** Chỉ một giai đoạn sản phẩm hoạt động trong một chu kỳ. Có thể ghi ý tưởng/roadmap tương lai, nhưng không được giao task thực thi của giai đoạn chưa mở khóa, kể cả lấy lý do đang chờ duyệt hoặc muốn chạy song song.

Ưu tiên tốc độ bằng cách giảm phạm vi sớm, thời gian chờ, công việc đang làm và review lặp; không bỏ cổng an toàn, sửa giả bằng chứng hoặc hạ tiêu chí để báo xong.

## 2. Đối chiếu hiện trạng X-Templates

Đã đọc `main` tại `c3a7e563795e43a8ef68f3b5bc17b78152732ed9`, ngày 2026-10-29:

- [`lifecycle.md`](../../../framework/00-method/lifecycle.md) có G0–G8 và `delivery_phase: build|harden`; đó là bước kỹ thuật và chế độ kiểm soát, chưa phải ba giai đoạn sản phẩm trên.
- [`/autopilot`](../../../.claude/skills/autopilot/SKILL.md) hiện lặp build → audit → build tới khi hết MUST ngoài chờ người. Cần giới hạn vào phạm vi MVP thay vì chờ hết backlog sản phẩm mới trình bản thử.
- [`/complete`](../../../.claude/skills/complete/SKILL.md) hiện xem vòng build `done` hoặc `done-pending-human` là tiền đề. Xong đợt không chứng minh MVP đã được chủ dự án duyệt.
- [`/optimize`](../../../.claude/skills/optimize/SKILL.md) hiện tập trung ngân sách hiệu năng đang đỏ; yêu cầu mới rộng hơn, gồm tính năng và mã nguồn, cả cải tiến có mục tiêu khi chưa vi phạm sàn.
- [`xt.yaml`](../../../xt.yaml) của **repo khung** vẫn là `delivery_phase: harden`. Không hạ về build hoặc nới review/coverage để triển khai bản nâng cấp.
- [`test_docs_budget.py`](../../../tests/test_docs_budget.py) giới hạn byte hướng dẫn. Skill phải ngắn, liên kết về một nguồn quy tắc; không tăng trần để nhét thêm văn bản.

Đây là đối chiếu nội dung đã đọc, không phải kết quả benchmark hoặc kiểm thử engine.

## 3. Ma trận chu trình 11 bước × ba giai đoạn

| Bước giữ nguyên | Giai đoạn 1 — MVP | Giai đoạn 2 — Hoàn thiện | Giai đoạn 3 — Tối ưu |
|---|---|---|---|
| **Ý tưởng** | Chọn vấn đề, người dùng, luồng giá trị cốt lõi | Chốt phạm vi sản phẩm dựa trên MVP đã duyệt | Chọn cơ hội cải tiến từ số đo và phản hồi |
| **Nghiên cứu** | Đọc repo, kiểm giả định/khả thi, tìm giải pháp có thể dùng lại | Làm rõ ca biên, tích hợp, vận hành và rủi ro còn thiếu | Phân tích bottleneck, hành vi, chi phí, nợ mã nguồn |
| **Đặc tả** | Tiêu chí MVP, không làm gì, cách chạy thử | Tiêu chí release đầy đủ, giới hạn tải và chất lượng bắt buộc | Giả thuyết, baseline, mục tiêu, điều kiện bác bỏ và không hồi quy |
| **Thiết kế** | Luồng UX, dữ liệu, API và kiến trúc tối thiểu có đường mở rộng | Hoàn thiện trải nghiệm, quyền, dữ liệu và phương án vận hành | Thiết kế đúng phần cần cải tiến; không viết lại toàn hệ thống mặc định |
| **Lập trình** | Lát dọc chạy xuyên suốt, ưu tiên có bản thử sớm | Bổ sung yêu cầu đã duyệt, ca lỗi/biên và tích hợp | Thay đổi nhỏ, tách mục tiêu hiệu suất/tính năng/mã nguồn |
| **Kiểm thử** | Tự động liên tục; smoke và nghiệp vụ chính; sàn an toàn | Unit/integration/E2E, quyền, bảo mật, tải, phục hồi theo rủi ro | Regression, tương đương hành vi, benchmark và nghiệm thu tính năng |
| **Audit** | Rà phạm vi MVP và an toàn trước bản trình duyệt | Audit tổng thể trước nghiệm thu, trả nợ review bắt buộc | Audit phần thay đổi và ảnh hưởng; full audit khi rủi ro yêu cầu |
| **Tối ưu** | Vừa đủ để demo dùng được; sửa nghẽn chặn luồng, không tối ưu vi mô | Đạt sàn production và khả năng bảo trì đã cam kết | Tối ưu sâu, chủ động, có mục tiêu và số trước/sau |
| **Production** | **Chưa mở cho phát hành chính thức**; preview/demo là môi trường thử, không gọi là production | GO/NO-GO, quyền phát hành, đưa bản đã nghiệm thu tới đích bàn giao | Phát hành bản cải tiến an toàn, có rollback; chỉ sau cổng release |
| **Vận hành** | Chạy và hỗ trợ môi trường thử, ghi lỗi demo | Giám sát, sao lưu/khôi phục, hỗ trợ, runbook và ổn định bản phát hành | Đo tác động thực tế, chi phí, độ tin cậy; sửa hồi quy |
| **Tăng trưởng** | Xác định chỉ số và học từ nhóm thử; không mở rộng người dùng đại trà | Thiết lập đo lường, onboarding và đón người dùng có kiểm soát | Cải thiện giữ chân, chuyển đổi và khả năng mở rộng theo mục tiêu sản phẩm |

**Production không bị đổi tên thành preview.** Bước Production vẫn tồn tại trong chu trình nhưng bị chặn trong giai đoạn MVP nội bộ. Preview là nhánh thử nghiệm dùng để nghiệm thu trước bước đó. Nếu một bản gọi là “MVP” tiếp xúc người dùng/dữ liệu/tiền thật, mức kiểm soát phải theo rủi ro thực, không theo tên MVP; không dùng giai đoạn 1 để lách điều kiện phát hành.

**Tối ưu là một bước ở mọi giai đoạn; giai đoạn 3 là chương trình cải tiến chuyên sâu.** Sửa lỗi hiệu năng làm sản phẩm không dùng được trong giai đoạn 1/2 vẫn thuộc giai đoạn hiện tại, không phải nhảy sang giai đoạn 3.

**Vận hành/Tăng trưởng không bị trì hoãn hoàn toàn tới giai đoạn 3.** Trong giai đoạn 1 là vận hành thử và kiểm chứng giá trị; giai đoạn 2 là sẵn sàng vận hành thật và bắt đầu đo; giai đoạn 3 là cải thiện/mở rộng dựa trên dữ liệu. Với công cụ nội bộ/thư viện, tăng trưởng có thể là mức sử dụng, hiệu quả công việc hoặc độ chấp nhận, không ép KPI doanh thu/SEO.

Thứ tự chu trình là trật tự logic để quản lý đầu ra, không phải hàng rào buộc kiểm thử/bảo mật chỉ bắt đầu sau khi viết hết mã. Kiểm thử liên tục trong khi lập trình; audit tổng thể ở mốc nghiệm thu. Một thay đổi sau audit hoặc tối ưu phải quay lại kiểm thử và audit phần ảnh hưởng trước Production.

## 4. Ba vòng lặp độc lập và điều kiện thoát

### Giai đoạn 1 — MVP

**Vòng:** ý tưởng/phản hồi → nghiên cứu phần chưa rõ → đặc tả MVP → thiết kế vừa đủ → code lát dọc → kiểm thử → audit MVP → tối ưu vừa đủ → bản preview → chạy thử/thu phản hồi → sửa trong cùng vòng.

Tài liệu khởi đầu gọn: vấn đề, đối tượng, luồng chính, tiêu chí nghiệm thu, ngoài phạm vi và cách chạy thử. Tận dụng code/stack hiện có; mô phỏng dịch vụ phải được ghi rõ, không giả lập kết quả của chính nghiệp vụ cốt lõi cần kiểm chứng.

**Hoàn thành khi:** luồng MVP chạy được xuyên suốt trên bản xác định; tiêu chí MVP có bằng chứng; CI/sàn an toàn đạt; lỗi chặn demo và phản hồi bắt buộc đã sửa; giới hạn được công khai; **chủ dự án đã duyệt đúng bản và phạm vi MVP**.

Đủ kỹ thuật nhưng chưa duyệt = `awaiting_approval`, không phải `completed`. Chủ dự án yêu cầu sửa = quay lại `active` của giai đoạn 1. Không lấp thời gian chờ bằng code chức năng của giai đoạn 2.

Ví dụ khách sạn: danh sách phòng → đặt phòng → nhận/trả phòng → hóa đơn cơ bản. Báo cáo nâng cao hay đa kênh chưa được chọn thì không tự thành phạm vi MVP.

### Giai đoạn 2 — Sản phẩm hoàn thiện

**Điều kiện vào:** giai đoạn 1 đã hoàn thành và có phạm vi release đã duyệt.

**Vòng:** tiếp nhận yêu cầu còn thiếu → nghiên cứu/đặc tả/thiết kế phần bổ sung → lập trình → kiểm thử → audit tổng thể theo mốc → sửa và tối ưu đạt sàn → kiểm lại → Production theo quyền → vận hành xác minh → phản hồi/đo mức sử dụng → sửa trong cùng giai đoạn.

Phải bao quát chức năng đã cam kết, trạng thái lỗi/rỗng/biên, phân quyền/cách ly dữ liệu, nghiệp vụ tiền/trạng thái, tích hợp, UX cần thiết, E2E, bảo mật, migration, quan sát, tài liệu, backup/restore, rollback và tải theo rủi ro.

**Hoàn thành khi:** mọi tiêu chí release bắt buộc đạt; không còn blocker/lỗi nghiêm trọng chưa xử lý; nợ review bắt buộc đã trả; cổng phát hành hiện hành đạt; sản phẩm được nghiệm thu; nghĩa vụ bàn giao/vận hành đã chốt có bằng chứng. Nếu deploy và xác minh vận hành nằm trong phạm vi bắt buộc thì thiếu quyền deploy nghĩa là vẫn chờ ở giai đoạn 2. Với bàn giao offline/thư viện, đích release là gói phát hành và kiểm tra tương ứng, không bắt dựng server cho mọi dự án.

GO của máy, nghiệm thu của người, quyền deploy và đã deploy là bốn việc khác nhau. Một việc không tự chứng minh các việc còn lại. Không cần tối ưu chuyên sâu giai đoạn 3 xong mới được phát hành sản phẩm đã đạt chuẩn ở giai đoạn 2.

Hiệu năng tối thiểu là việc giai đoạn 2: timeout, lỗi dữ liệu hoặc không chịu được tải mục tiêu phải sửa ngay tại đây. “Hoàn thiện” nghĩa là đúng phạm vi được duyệt, không phải làm hết mọi ý tưởng; ý tưởng mới vào backlog riêng, không âm thầm kéo dài vòng hiện tại.

### Giai đoạn 3 — Tối ưu hiệu suất, tính năng và mã nguồn

**Điều kiện vào:** giai đoạn 2 hoàn thành; có baseline ổn định và tiêu chí cải tiến được chốt.

**Vòng:** ý tưởng từ số đo/phản hồi → nghiên cứu nguyên nhân → đặc tả mục tiêu → thiết kế thay đổi → lập trình → kiểm thử đối chiếu → audit delta → tối ưu/đo lại → phát hành bản cải tiến → vận hành đo thật → tăng trưởng → mục tiêu kế.

Ba nhánh mục tiêu:

- **Hiệu suất/chi phí:** latency p95, throughput, truy vấn, bộ nhớ, kích thước tải hoặc chi phí giao dịch; baseline và bản sau phải đo trong điều kiện tương đương.
- **Tính năng/trải nghiệm:** hoàn thành tác vụ, số bước thao tác, chất lượng kết quả, phản hồi hoặc tỷ lệ chuyển đổi khi có đủ dữ liệu; đổi hành vi phải có tiêu chí và nghiệm thu.
- **Mã nguồn:** test giữ hành vi, giảm phức tạp/trùng lặp có mục đích, ranh giới module rõ, thời gian build/test và khả năng bảo trì. Ít dòng hơn không tự động tốt hơn.

Một giả thuyết, một thay đổi có thể đo. Không đổi ngưỡng/bộ đo trong cùng task để làm đẹp kết quả. Không hi sinh độ chính xác, bảo mật, khả năng sử dụng hoặc ngân sách ngoài thỏa thuận.

Đạt mục tiêu và không hồi quy → giữ. Không cải thiện/không đủ bằng chứng/hồi quy → hoàn tác hoặc điều tra lại; ghi kết quả thất bại. Hoàn tác thành công không có nghĩa mục tiêu tối ưu đã hoàn tất. Hết ngân sách → bàn giao cùng giai đoạn; không báo thành công giả.

Có thể cải tiến khi các chỉ số chưa đỏ nếu có mục tiêu giá trị rõ; điều này phải được cập nhật chính thức vào `/optimize` và các luật liên quan, không diễn giải lại luật hiện tại một cách âm thầm. Tính năng lớn đổi bài toán sản phẩm phải thành chu kỳ phiên bản mới đi đủ 1→2→3, không lách bằng nhãn “tối ưu”.

## 5. Tách bốn loại trạng thái

| Khái niệm | Trách nhiệm |
|---|---|
| Chu trình 11 bước | Giữ logic Ý tưởng đến Tăng trưởng, lặp khi có phản hồi |
| Giai đoạn sản phẩm | `mvp → complete → optimize`, quyết định phạm vi và quyền mở vòng sau |
| Chế độ kiểm soát hiện có | `delivery_phase: build|harden`, quyết định luật review/merge; không đồng nhất với stage |
| Đợt thực thi | PLAN/task có ngân sách và bằng chứng; nhiều đợt có thể nằm trong một stage |

Trạng thái stage đề xuất: `locked → active → verifying → awaiting_approval → completed`. Có thể quay từ verifying/awaiting_approval về active khi cần sửa. `blocked` và `budget_exhausted` là lý do dừng, không phải hoàn thành.

**Đã triển khai (ADR-0058):** sổ chỉ lưu `active | awaiting_approval | completed`. `locked` không ghi riêng — mọi giai đoạn sau giai đoạn đang mở là khoá. `verifying` gộp vào `active`: bằng chứng kiểm là của máy (`loop verify --all`, `release-check`), không phải một trạng thái người đọc. `blocked`/`budget_exhausted` vẫn là verdict của vòng (`loop status`), không chạm sổ. `completed` chỉ có sau khi người duyệt giai đoạn 3 — đóng chu kỳ; bài toán lớn mới mở chu kỳ kế bằng `stage new-cycle`. Ánh xạ thêm từ nghiên cứu: quyết định gate kiểu Stage-Gate (Go/Kill/Hold/Recycle) chỉ dùng **Go** (`approve`) và **Recycle** (`reopen`); Kill/Hold là quyết định của chủ dự án ngoài máy (dừng vòng, `loop block`). Kết quả "red" của GOV.UK service assessment = ở lại giai đoạn hiện tại — đúng nghĩa `reopen`.

Chỉ `completed(1)` hợp lệ mở stage 2, chỉ `completed(2)` hợp lệ mở stage 3. Không có đường `1→3`. Không dùng CI xanh, hết task, hết phiên, hết tiền/token, `done-pending-human` hoặc sự im lặng của chủ dự án làm giấy phép chuyển stage.

G0–G8 vẫn được tái sử dụng bên trong mô hình; không tạo thêm chín cổng duyệt thủ công. Bước nghiên cứu/thiết kế đã có đầu ra còn phù hợp được dùng lại; thay đổi chỉ cập nhật phần ảnh hưởng.

### Khóa bằng máy — lát A+B đã triển khai (ADR-0058), phần còn lại chưa

Hồ sơ mỗi chu kỳ cần version schema, cycle ID, stage, revision phạm vi, tham chiếu PLAN, baseline và lịch sử. Task phải thuộc stage/cycle hiện tại; scheduler không được chọn task tương lai dù dependency trống hoặc tên PLAN bị sửa.

Biên nhận hoàn thành phải gắn stage/cycle/phạm vi, bản build hoặc artefact được thử, fingerprint Gate, kết quả kiểm tra và nguồn phê duyệt có thể xác minh. Chuỗi `approved: true`, tên người trong Markdown, quyết định do agent tự ghi hay lời “ok” trước khi bản thử tồn tại không đủ. Thiếu phương tiện xác minh thì giữ chờ duyệt, không tự nâng quyền.

Mọi entry point — CLI/API, `loop init`, `loop next-step`, scheduler, Stop hook, `/autopilot`, `/complete`, `/optimize` — phải dùng chung luật stage. Chặn trước side effect. Transition dùng khóa/rev/ghi nguyên tử hiện có, không tự ghi `.autopilot/` hoặc tạo cờ force vượt cổng.

Tách rõ `batch_done`, `stage_ready_for_approval`, `stage_completed`. `loop next-step` chỉ đề xuất bước hợp lệ; đề xuất không tự thực hiện chuyển stage. Resume/đổi PLAN/init lại/hết ngân sách không reset lịch sử hoặc mở stage bị khóa.

Biên nhận stage trước là mốc lịch sử: commit hợp lệ của stage sau không tự làm mất nghiệm thu cũ. Nhưng thay đổi phạm vi nền tảng, regression hoặc bằng chứng không còn phù hợp phải được xác minh lại; biên nhận cũ không che được lỗi mới.

`release-check` cần kiểm stage/biên nhận mà vẫn giữ toàn bộ cổng hiện tại. Không cho deploy production ở MVP nội bộ; không đòi xong stage 3 mới được phát hành ở stage 2. Quyền deploy độc lập với quyền chuyển stage.

## 6. Tổ chức để nhanh, không tạo ba vòng waterfall nặng

Một người điều phối giữ phạm vi/kiến trúc và trạng thái; một nhóm kỹ sư làm lát dọc; kiểm chứng độc lập theo rủi ro; platform/UX/security/data tham gia theo nhu cầu. Đây là vai trò logic, không phải mười mấy agent luôn chạy đồng thời.

Lập kế hoạch đủ cho lát sắp làm; nghiên cứu sâu chỉ ở bất định có ảnh hưởng. Chốt hợp đồng dữ liệu/API trước khi chia việc song song. Chỉ song song những task độc lập **trong cùng stage**; một chủ sở hữu mỗi lát, tích hợp thường xuyên.

Commit/PR nhỏ; audit tổng thể ở mốc nghiệm thu không có nghĩa gom toàn stage thành một PR khổng lồ. Test tự động liên tục, cổng nhanh tại máy và cổng đầy đủ ở CI theo chính sách hiện có. Cache/shard/kiểm phần ảnh hưởng để giảm chờ, nhưng không tái sử dụng kết quả xanh khi fingerprint đầu vào/bộ test/môi trường đã thay đổi.

Reviewer trả một danh sách tổng hợp, phân loại blocker và việc cải thiện. Vòng tiếp theo rà bản sửa và ảnh hưởng, không mở lại toàn repo vô cớ. Hai lượt chưa hội tụ thì đổi cách/chia lát hoặc chuyển người giải quyết; không bỏ qua blocker để đạt trần lượt. Lỗi có sẵn không liên quan không tự chặn PR, nhưng lỗi nghiêm trọng có liên quan đến bản phát hành vẫn phải xử lý ở cổng release.

Auth, quyền, tiền, migration, secrets, thay đổi cổng/hook và rủi ro cao phải kiểm sớm theo chính sách; không chờ audit cuối stage. Không tự hạ chế độ harden, coverage hoặc chất lượng test để lấy tốc độ.

**Ranh giới vận hành:** khóa stage ngăn phát triển sản phẩm vượt pha, không được tắt giám sát, backup hoặc cản xử lý sự cố khẩn cấp của bản đã phát hành. Sự cố là luồng vận hành được ủy quyền, không phải lý do mở khóa stage 2/3 của chu kỳ đang làm. Chạy xong phải cập nhật bằng chứng hồi quy và baseline liên quan.

## 7. Áp dụng cho mọi dự án đích

**Dự án mới:** hồ sơ bắt đầu stage 1, stage 2/3 khóa. Template chỉ rõ chu trình 11 bước, cách đọc trạng thái và điều kiện duyệt. Chưa có engine thì không được tuyên bố stage lock đã hoạt động.

**Dự án đang phát triển:** xác định stage bằng bằng chứng, không đoán từ tên nhánh/độ dài code. Giữ việc đang làm và chuyển backlog vào đúng stage; không áp stack mới, không viết lại sản phẩm mặc định.

**Dự án đã production:** đối chiếu và công nhận bằng chứng lịch sử stage 1/2 qua cơ chế adoption có xác nhận, không ép chạy lại từ đầu hoặc hạ production về MVP. Thiếu nghiệm thu thì bổ sung phần thiếu; tag release tự nó không đủ để tạo mọi biên nhận.

**Installer/migration:** giữ cấu hình, quyền và state của dự án; template copy-if-absent không cập nhật file đã sửa nên phải có diff/migration và kiểm sau cài. Không chỉ cập nhật repo khung rồi nói mọi repo đã nhận chính sách.

**Chu kỳ phiên bản mới:** feature nhỏ trong phạm vi tối ưu tiếp tục vòng stage 3; bài toán/module lớn mở chu kỳ mới 1→2→3. Vẫn giữ production ổn định trong khi chu kỳ mới phát triển; không dùng nhiều cycle giả để thực thi trước stage bị khóa của cùng một thay đổi.

## 8. Kế hoạch triển khai kỹ thuật

Lát A+B đã có mã + test (ADR-0058); C–F là việc cần làm, **chưa có bằng chứng hoàn tất bằng mã**.

| Lát | Phạm vi | Nghiệm thu |
|---|---|---|
| A — hợp đồng ✅ | ADR-0058, `schema: 1` stage/cycle/approval, mapping 11 bước (§3), `tests/test_stage.py` | phân biệt batch/stage/control mode; schema có version; sổ hỏng/lịch sử lệch → chặn, không đoán |
| B — máy trạng thái ✅ (trừ `next-step`) | `xt.py stage`, khoá `state.lock`, `loop init/next/record`, `release-check` | chặn 1→3, 2 trước 1, 3 trước 2 ở mọi lối vào vòng; từ chối không ghi sổ/bằng chứng. Còn: `loop next-step` đề xuất `stage submit` khi hết việc giai đoạn 1 |
| C — MVP và duyệt | bản thử/artefact, Gate MVP, approval xác thực | đủ task nhưng chưa duyệt vẫn ở stage 1; yêu cầu sửa mở lại vòng stage 1 |
| D — hoàn thiện và tối ưu | routing skill, release-check, mục tiêu performance/feature/code | stage 2 xử lý sàn; stage 3 có baseline/no-regression/rollback; giữ cổng phát hành |
| E — mẫu và migration | installer, AGENTS, tài liệu, API/UI liên quan | dự án mới khóa đúng; dự án cũ giữ quyền/state; báo diff và đường lùi |
| F — nghiệm thu và áp dụng | test xuyên suốt, CI, review độc lập, release khung và nâng từng target | có bằng chứng từng bước; không nới ngưỡng/hook; kiểm target sau nâng |

Chỉ giao các lát phụ thuộc khi tiền đề đạt; không mở cả sáu lát song song. Thay đổi chính sách có ADR và CHANGELOG theo quy ước khung; không sửa đè ADR cũ. Không thêm lock/state/approval engine riêng nếu có thể mở rộng cơ chế hiện hành.

### Ma trận test tối thiểu cho engine

| Tình huống | Kết quả bắt buộc |
|---|---|
| Stage 1 active, gọi complete hoặc optimize trực tiếp | chặn trước tạo task/chạy tool/đổi state |
| Hết task MVP và CI xanh nhưng chưa duyệt | awaiting_approval; stage 2/3 khóa |
| Chủ dự án yêu cầu sửa demo | tiếp tục stage 1, giữ lịch sử |
| Hết ngân sách/lỗi lặp/đổi phiên | dừng hoặc resume cùng stage, không tự completed |
| Giả approved bằng file/quyết định của agent | từ chối, đòi nguồn phê duyệt có thẩm quyền |
| Duyệt sai repo/cycle/revision/artefact | từ chối, nêu bằng chứng lệch |
| init lại/force/đổi PLAN/task không dependency | không vượt stage |
| Hai phiên advance đồng thời | một transition hợp lệ, phiên còn lại đọc lại rev |
| Stage 2 perf sàn đỏ | sửa trong stage 2, không mở optimize stage 3 |
| Preview MVP được gắn nhãn production | release gate chặn; không coi demo là production |
| Có GO kỹ thuật nhưng thiếu quyền deploy | không deploy và không bịa bằng chứng vận hành |
| Có thay đổi sau audit/tối ưu | chạy lại test và audit vùng ảnh hưởng trước release |
| Tối ưu nhanh hơn nhưng sai kết quả/hồi quy | bác bỏ/rollback, không tuyên bố cải thiện |
| Mục tiêu tính năng/code có baseline | được xét stage 3 mà không cần giả lỗi performance |
| Dự án đã production nâng khung | giữ hoạt động/backup; adoption không tự skip hoặc phá state |
| Chờ MVP nhưng bản cũ có sự cố | cho xử lý qua luồng vận hành được ủy quyền, không mở stage phát triển |
| Chu kỳ mới thay đổi bài toán lớn | đi đúng 1→2→3; bản production cũ không bị reset |

## 9. Chỉ số và giới hạn kết luận

Đo trước/sau trên công việc tương đương: thời gian tới demo chạy được, thời gian tới nghiệm thu stage 1/2, thời gian máy làm tách khỏi chờ người, CI p95, số lượt review, lượng làm lại sau MVP, lỗi lọt production và chi phí/tokens trên task được chấp nhận. Mục tiêu số lần chuyển stage trái phép là 0.

Ở stage 3 phải tách số lab và field. Chưa có dữ liệu production thì ghi chưa đo; không bịa tác động tăng trưởng hoặc tốc độ. Không dùng số dòng code, số agent hoặc số task tick làm bằng chứng năng suất chính.

Không đặt cam kết nhanh hơn theo phần trăm khi chưa có baseline. Nhanh hơn nhưng tăng lỗi nghiêm trọng hoặc phải viết lại nhiều là chưa đạt mục tiêu.

## 10. Nghiên cứu tham khảo

Đối chiếu ngày 2026-10-29. Ba giai đoạn và chu trình 11 bước là thiết kế theo yêu cầu chủ dự án, không phải một tiêu chuẩn bắt buộc từ các nguồn sau.

- **DORA — Working in small batches:** việc nhỏ, có thể kiểm chứng và phản hồi sớm; áp dụng bên trong từng stage, không gom lại thành một PR lớn. <https://dora.dev/capabilities/working-in-small-batches/>
- **DORA — Continuous integration:** tích hợp thường xuyên, test nhanh và xử lý build hỏng; cơ sở cho kiểm tra liên tục thay vì đợi viết xong toàn stage. <https://dora.dev/capabilities/continuous-integration/>
- **DORA — Continuous delivery:** kiểm thử/bảo mật/quan sát trong vòng đời; sẵn sàng phát hành khác tự động deploy mọi thay đổi. <https://dora.dev/capabilities/continuous-delivery/>
- **Anthropic — Building effective agents:** bắt đầu bằng workflow đơn giản; evaluator–optimizer cần tiêu chí rõ và điều phối theo nhu cầu. Bài gốc 2024, dùng nguyên tắc thiết kế, không lấy làm hướng dẫn phiên bản công cụ hiện tại. <https://www.anthropic.com/research/building-effective-agents>
- **Anthropic — Effective harnesses for long-running agents:** tiến triển tăng dần, bàn giao rõ và test xuyên suốt để tránh tự kết luận hoàn tất. Bài gốc 2025. <https://www.anthropic.com/research/effective-harnesses-for-long-running-agents>
- **GOV.UK — Beta / Live:** thử với nhóm giới hạn, lặp theo phản hồi, chuẩn bị vận hành rồi tiếp tục cải tiến sau phát hành; tham khảo cách tách trưởng thành và vòng lặp, không sao chép thủ tục hành chính. <https://www.gov.uk/service-manual/agile-delivery/how-the-beta-phase-works> và <https://www.gov.uk/service-manual/agile-delivery/how-the-live-phase-works>

- **Stage-Gate (Cooper):** gate là điểm quyết định đầu tư do người giữ nguồn lực; kết quả Go/Kill/Hold/Recycle; bản lai Agile–Stage-Gate (RTM 59(1), 2016) giữ gate, chạy sprint bên trong stage. Nguồn vendor (Stage-Gate International), nghĩa Hold/Recycle chưa xác minh từ nguồn gốc. <https://www.stage-gate.com/blog/the-stage-gate-model-an-overview/>
- **GOV.UK alpha + service assessment:** alpha "should not be available for the public to use"; kết quả đánh giá green (sang giai đoạn kế) / amber (đi tiếp, sửa trong ~3 tháng) / red (ở lại, đánh giá lại). <https://www.gov.uk/service-manual/agile-delivery/how-the-alpha-phase-works>, <https://www.gov.uk/service-manual/service-assessments/how-service-assessments-work>
- **Eric Ries — MVP:** "that version of a new product which allows a team to collect the maximum amount of validated learning about customers" — mục đích MVP là học, nên giai đoạn 1 kết thúc ở duyệt/phản hồi, không ở phát hành. <https://leanstartup.co/what-is-an-mvp/>
- **GitHub Environments:** required reviewers; người kích hoạt tự duyệt được khi tắt "Prevent self-review", admin bypass mặc định bật — ở repo một chủ, hành động GitHub của agent cùng tài khoản với chủ nên không làm nguồn phê duyệt (lý do chọn terminal ngoài phiên agent, ADR-0058). <https://docs.github.com/en/actions/managing-workflow-runs-and-deployments/managing-deployments/managing-environments-for-deployment>
- **Google SRE — Reliable Product Launches:** Launch Coordination Engineering "acting as gatekeepers and signing off on launches"; checklist theo nhóm (dung lượng, failover, giám sát, bảo mật, rollout) — tham chiếu cho cổng giai đoạn 2. <https://sre.google/sre-book/reliable-product-launches/>
- **DORA 2025:** AI là bộ khuếch đại điểm mạnh/yếu sẵn có; tăng throughput nhưng vẫn gắn với bất ổn khi thiếu test tự động, kiểm soát phiên bản, phản hồi nhanh — lý do giữ nguyên sàn an toàn ở cả ba giai đoạn. <https://dora.dev/research/2025/dora-report/>, chỉ số rework rate: <https://dora.dev/guides/dora-metrics/>
- **SLSA attestation:** mệnh đề có xác thực gồm chủ thể (artefact) + vị ngữ (metadata), ký bởi bên tạo — hướng nâng cấp nếu cần chữ ký thật cho `approve` (hiện `by` là `git config` tự khai). <https://slsa.dev/spec/v1.0/attestation-model>
- **Shape Up:** appetite = thời gian sẵn sàng bỏ ra, định hình phạm vi; circuit breaker = hết chu kỳ thì mặc định không gia hạn — khớp luật hết ngân sách không tự `completed`. <https://basecamp.com/shapeup/1.2-chapter-03>, <https://basecamp.com/shapeup/2.2-chapter-08>

Nghiên cứu bổ sung đối chiếu 2026-10-29 qua `researcher` (WebFetch tóm tắt, không chép nguyên văn); mục ghi "chưa xác minh" giữ nguyên mức đó.

## 11. Trạng thái bàn giao

**Cập nhật 2026-10-29 (ADR-0058):** lát A+B có mã, test và guard; PR riêng. Vẫn chưa: Gate MVP/preview (C), định tuyến `/complete`/`/optimize` theo giai đoạn ngoài dòng nhắc trong skill và `/optimize` cho mục tiêu tính năng/mã nguồn (D), installer/migration (E), nâng dự án đích (F). Phần dưới là trạng thái của PR đặc tả gốc.


PR này hoàn tất phần nghiên cứu/đặc tả: chu trình 11 bước được giữ nguyên, ma trận ba giai đoạn, vòng lặp/cổng, điểm tích hợp, migration và test cases. **Chưa sửa mã engine; chưa chạy kiểm thử engine mới; chưa phát hành; chưa áp dụng sang dự án đích.** Khi triển khai phải báo riêng: tài liệu, mã, test, merge, phát hành và target đã nâng. Không gọi tài liệu hoặc lời nhắc trong prompt là cơ chế khóa bằng máy.
