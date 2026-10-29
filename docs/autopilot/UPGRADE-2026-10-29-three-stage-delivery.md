# Nâng cấp giao hàng: ba giai đoạn tuần tự, ưu tiên tốc độ

Ngày: 2026-10-29. Phạm vi: **mọi dự án đích** của X-Templates, không phụ thuộc loại ứng dụng hoặc stack.

**Trạng thái: đặc tả nâng cấp, CHƯA phải tính năng đã triển khai.** Tài liệu này không thay đổi `xt.yaml`, engine, hook, cổng CI hay chính sách merge hiện hành. Các trường và lệnh mới bên dưới là giao diện đề xuất; chưa được dùng như lệnh có sẵn. Không được tuyên bố đã cưỡng chế ba giai đoạn bằng máy chỉ vì tài liệu được merge.

## 1. Yêu cầu đã chốt

Chủ dự án yêu cầu ưu tiên tốc độ, chia toàn bộ quá trình phát triển sản phẩm thành:

1. **MVP:** có bản chạy thử để chủ dự án duyệt, yêu cầu chỉnh sửa và thử lại.
2. **Sản phẩm hoàn thiện:** hoàn thành phạm vi sản phẩm đã duyệt, đủ điều kiện sử dụng thực tế.
3. **Tối ưu:** cải thiện hiệu suất, tính năng và mã nguồn dựa trên tiêu chí đo được.

**Mỗi giai đoạn có vòng lặp riêng. Giai đoạn trước chưa hoàn thành thì không được thực thi giai đoạn sau.** Chỉ một giai đoạn hoạt động trong một chu kỳ sản phẩm; không dùng từ “song song” để triển khai trước công việc của giai đoạn 2/3. Được lập roadmap sơ bộ cho tương lai, nhưng chưa được mở task thực thi của giai đoạn chưa mở khóa.

“Ưu tiên tốc độ” nghĩa là giảm phạm vi sớm, thời gian chờ, bàn giao, review lặp và công việc chưa cần; không có nghĩa bỏ kiểm thử, quyền truy cập, bảo vệ dữ liệu hoặc làm giả bằng chứng.

## 2. Hiện trạng đã đọc

Nguồn: `main` tại `c3a7e563795e43a8ef68f3b5bc17b78152732ed9`; đọc ngày 2026-10-29.

- [`../../..//framework/00-method/lifecycle.md`](../../../framework/00-method/lifecycle.md) mô tả G0–G8 và `delivery_phase: build|harden`; đây là các bước kỹ thuật và chế độ kiểm soát, chưa phải ba giai đoạn sản phẩm mà người dùng yêu cầu.
- [`../../../.claude/skills/autopilot/SKILL.md`](../../../.claude/skills/autopilot/SKILL.md) hiện lặp build → audit → build tới khi hết MUST ngoài chờ người rồi mới đề xuất `/complete`. Phạm vi rộng này có thể trì hoãn thời điểm trình MVP.
- [`../../../.claude/skills/complete/SKILL.md`](../../../.claude/skills/complete/SKILL.md) hiện cho vào harden khi vòng build `done` hoặc `done-pending-human`. Trạng thái xong đợt chưa chứng minh chủ dự án đã duyệt MVP.
- [`../../../.claude/skills/optimize/SKILL.md`](../../../.claude/skills/optimize/SKILL.md) hiện tập trung ngân sách hiệu năng đang đỏ; chưa bao quát toàn bộ cải thiện tính năng/mã nguồn của giai đoạn 3.
- [`../../../xt.yaml`](../../../xt.yaml) của **repo khung** giữ `delivery_phase: harden`. Không đổi repo khung về build để tăng tốc bản nâng cấp này.
- [`../../../tests/test_docs_budget.py`](../../../tests/test_docs_budget.py) đặt trần byte cho hướng dẫn. Cập nhật skill phải rút gọn, liên kết về một nguồn quy tắc, không nâng trần cho vừa nội dung.

Các nhận định trên là đối chiếu tài liệu/cấu hình đã đọc, **không phải kết quả benchmark hay kiểm thử engine**.

## 3. Mô hình ba tầng, không đánh đồng

| Tầng | Ý nghĩa | Ví dụ |
|---|---|---|
| Giai đoạn sản phẩm | Mục tiêu giao hàng và điều kiện mở khóa giai đoạn kế | `mvp` → `complete` → `optimize` |
| Chế độ kiểm soát | Chính sách merge/review, hàng rào phát hành hiện có | `delivery_phase: build|harden` |
| Đợt thực thi | Một PLAN và một vòng lặp có ngân sách, task, bằng chứng | Nhiều đợt trong cùng một giai đoạn |

G0–G8 vẫn được tái sử dụng bên trong ba giai đoạn; không tạo thêm chín cửa duyệt thủ công. Hoàn thành một task không đồng nghĩa hoàn thành một đợt; hoàn thành một đợt không đồng nghĩa hoàn thành giai đoạn; hoàn thành MVP không đồng nghĩa được phát hành production.

Trạng thái đề xuất của mỗi giai đoạn:

`locked → active → verifying → awaiting_approval → completed`

Từ `verifying` hoặc `awaiting_approval`, phản hồi yêu cầu sửa đưa **cùng giai đoạn** về `active`. `blocked`, `budget_exhausted` và `awaiting_approval` là trạng thái dừng có lý do, không được diễn giải thành hoàn thành. Không có đường tắt `mvp → optimize`.

Quy tắc chuyển: chỉ `completed(n)` có bằng chứng hợp lệ mới cho phép `active(n+1)`. `completed` phải do bộ chuyển trạng thái kiểm chứng, không tin cờ do model tự viết. Hết task, hết phiên, hết token, hết ngân sách, CI xanh hoặc người dùng im lặng đều không thay cho điều kiện hoàn thành.

## 4. Giai đoạn 1 — MVP để chạy thử và duyệt

**Đích:** bản nhỏ nhất chứng minh đúng luồng giá trị cốt lõi, có thể chạy lại và sửa nhanh theo phản hồi. MVP không chỉ là ảnh giao diện hoặc các nút chưa hoạt động.

Vòng lặp:

`Chốt phạm vi MVP → dựng một lát chạy xuyên suốt → kiểm tra tự động → trình bản thử → nhận phản hồi → sửa đúng phạm vi → kiểm tra lại → trình lại`

**Đầu vào tối thiểu:** vấn đề, người dùng, luồng chính, tiêu chí nghiệm thu, ngoài phạm vi, môi trường demo. Đọc và tận dụng repo có sẵn trước khi chọn stack; không đổi kiến trúc chỉ để làm mới.

**Làm ngay:** dữ liệu/lưu trữ cần cho luồng chính; UI đủ thao tác; xử lý lỗi cốt lõi; lệnh khởi chạy hoặc bản preview; test nghiệp vụ chính; smoke test xuyên suốt; bảo vệ secrets, kiểm đầu vào và phân quyền khi có tài khoản; dữ liệu mẫu, cấu hình demo tách production. Dịch vụ giả lập phải được ghi rõ và không thay cho kiểm chứng luồng cốt lõi cần được duyệt.

**Chưa làm:** tính năng ngoài MVP; thiết kế mở rộng xa chưa có nhu cầu; tối ưu vi mô; trang trí phụ; refactor toàn repo. Nếu thay đổi nhỏ là điều kiện để MVP chạy đúng/an toàn thì làm trong giai đoạn 1, không gán nhãn “tối ưu” rồi trì hoãn.

**Cổng hoàn thành MVP:**

- Mọi tiêu chí MVP của revision hiện tại có bằng chứng chạy được; bản thử gắn với mã nguồn/artefact xác định.
- Sàn an toàn và CI bắt buộc xanh; không còn lỗi chặn luồng demo hoặc rủi ro nghiêm trọng trong phạm vi tiếp xúc thực tế.
- Các phản hồi bắt buộc đã xử lý, giới hạn/mô phỏng được công khai; không tự đổi phản hồi bắt buộc thành backlog tương lai.
- **Chủ dự án duyệt rõ ràng đúng bản MVP và phạm vi đó.** Agent không được tự ký thay hoặc dùng lời “ok” từ trước khi bản thử tồn tại.

Đang chờ duyệt: giữ giai đoạn 1; không xây thêm tính năng giai đoạn 2 để “tận dụng thời gian”. Bản demo thay đổi ảnh hưởng tiêu chí đã duyệt thì cần bằng chứng và xác nhận tương ứng, không tái sử dụng phê duyệt cũ một cách mù quáng.

Ví dụ khách sạn: danh sách phòng → đặt phòng → nhận/trả phòng → hóa đơn cơ bản. Báo cáo nâng cao hay kết nối nhiều kênh không tự động trở thành việc MVP.

## 5. Giai đoạn 2 — Sản phẩm hoàn thiện

**Điều kiện vào:** giai đoạn 1 đã `completed`; có phạm vi sản phẩm/release đã chốt. Không mở chỉ vì PLAN-MVP đã hết task hoặc vòng lặp đang `done-pending-human`.

Vòng lặp:

`Lấy yêu cầu còn thiếu trong phạm vi → triển khai theo lát → kiểm thử liên tục → audit mốc lớn → gom lỗi → sửa → xác minh delta → nghiệm thu`

**Phải hoàn thiện:** chức năng đã cam kết; ca lỗi/rỗng/biên; quyền và cách ly dữ liệu; nghiệp vụ tiền/trạng thái; tích hợp thật cần cho release; UX cần thiết; E2E các luồng chính; bảo mật; migration; quan sát lỗi; hướng dẫn vận hành; sao lưu/khôi phục, rollback và kiểm tải theo rủi ro ứng dụng.

**Hiệu năng tối thiểu thuộc giai đoạn này.** Một sản phẩm gây timeout, mất dữ liệu, vượt ngân sách bắt buộc hoặc không chịu được tải mục tiêu không được gọi là hoàn thiện rồi chuyển vấn đề sang giai đoạn 3. Việc sửa để đạt sàn là task giai đoạn 2, không phải mở vòng giai đoạn 3.

**Cổng hoàn thành sản phẩm:** mọi tiêu chí release bắt buộc đạt; không còn BLOCKER và lỗi nghiêm trọng chưa xử lý; nợ review bắt buộc đã trả; `release-check` hiện hành đạt điều kiện máy; nghiệm thu chủ dự án và quyền phát hành được ghi rõ. GO của máy, nghiệm thu sản phẩm, cho phép deploy và đã deploy là những sự kiện khác nhau, không suy diễn thay nhau.

“Hoàn thiện” là hoàn thiện **phạm vi đã duyệt**, không phải mọi ý tưởng có thể nảy sinh. Đề xuất mới vào backlog riêng; không âm thầm phình phạm vi để vòng lặp không bao giờ kết thúc. Việc bắt buộc chỉ được bỏ khỏi phạm vi qua quyết định có thẩm quyền và lý do, không tự hạ mức để xanh.

## 6. Giai đoạn 3 — Hiệu suất, tính năng, mã nguồn

**Điều kiện vào:** giai đoạn 2 `completed`; bản nền ổn định, có test và số đo cơ sở. Chưa có dữ liệu thực tế thì dùng lab đúng điều kiện và ghi rõ, không bịa hiệu quả production.

Vòng lặp:

`Đo hiện trạng/thu phản hồi → chọn một mục tiêu giá trị → nêu giả thuyết → sửa nhỏ → đo và kiểm thử lại → giữ hoặc bỏ → mục tiêu kế`

| Nhánh cải tiến | Bằng chứng quyết định |
|---|---|
| Hiệu suất/chi phí | p95 latency, truy vấn, bộ nhớ, kích thước tải, throughput hoặc chi phí mỗi giao dịch; cùng môi trường, tải và bộ đo |
| Tính năng/trải nghiệm | tiêu chí hành vi đã duyệt, số bước thao tác, tỷ lệ hoàn thành hoặc phản hồi người dùng; thay hành vi phải được nghiệm thu |
| Mã nguồn | test giữ hành vi, giảm trùng lặp/phức tạp có mục đích, cải thiện thời gian build/test, ranh giới module rõ; ít dòng hơn không tự động là tốt hơn |

Tách từng loại cải tiến để đo được nguyên nhân. Không đổi bộ đo/ngưỡng trong cùng task để tự tạo “cải thiện”. Không giảm độ chính xác, bảo mật, tính năng đã cam kết hay tăng chi phí ngoài ngân sách để lấy một chỉ số đẹp.

Giai đoạn 3 không bị giới hạn vào lỗi đang đỏ: có thể đặt mục tiêu cải tiến cao hơn khi có giá trị và baseline. Điều này **cần cập nhật có chủ đích** quy tắc `/optimize` hiện tại, không được âm thầm diễn giải khác các luật đang áp dụng.

**Kết thúc một vòng tối ưu:** mục tiêu của vòng đạt và không hồi quy; hoặc thí nghiệm bị bác bỏ và đã hoàn tác an toàn. Bác bỏ thí nghiệm không có nghĩa hoàn thành mục tiêu: chỉ đóng/đổi mục tiêu qua quyết định có lý do. Hết ngân sách thì bàn giao, không tự đánh dấu thành công.

Giai đoạn 3 có thể tiếp tục nhiều vòng. Một mô-đun/tính năng lớn làm thay đổi sản phẩm phải được xếp thành chu kỳ phiên bản mới `MVP → hoàn thiện → tối ưu`, không lén xây sản phẩm chưa được duyệt dưới nhãn tối ưu.

## 7. Tăng tốc bên trong giai đoạn, không vượt giai đoạn

1. **Một backlog đang hoạt động:** task có `stage`, revision, tiêu chí chấp nhận, phụ thuộc, phạm vi file và Gate. Scheduler không trả task của giai đoạn khóa, kể cả khi task đó không khai phụ thuộc.
2. **Lát dọc nhỏ:** giao một luồng giá trị có thể chạy thử, không chờ làm xong toàn bộ frontend rồi mới backend. Commit/PR nhỏ vẫn cần thiết; audit tổng thể cuối pha không đồng nghĩa một PR khổng lồ.
3. **Song song có giới hạn:** chỉ task trong cùng giai đoạn, độc lập file/hợp đồng dữ liệu. Một chủ sở hữu mỗi lát; tích hợp thường xuyên. Mặc định thử ít executor rồi đo hàng đợi/va chạm trước khi tăng, không nhân bản phòng ban thành hàng chục agent thường trực.
4. **Cổng nhanh và cổng đầy đủ:** kiểm tra liên quan tại máy; CI đầy đủ theo chính sách đang có; cache/shard và tái sử dụng kết quả chỉ khi fingerprint mã, môi trường, phụ thuộc và bộ test khớp. Không tái dùng kết quả xanh sau thay đổi liên quan.
5. **Review theo rủi ro:** kiểm tự động liên tục; gom audit tổng thể ở mốc nghiệm thu. Thay đổi quyền, tiền, migration, bảo mật hoặc cổng phải rà ngay theo chính sách. Không tự bỏ review bắt buộc của pha harden.
6. **Giảm vòng lặp reviewer:** một báo cáo gom phát hiện; phân biệt lỗi do diff và lỗi có sẵn; lần sau rà bản sửa và vùng ảnh hưởng thay vì tìm lại toàn repo. Hai lượt không hội tụ thì đổi phương án/chia lát; không tăng vô hạn reviewer và cũng không bỏ qua blocker để đạt trần lượt.
7. **Giới hạn công việc đang làm:** ưu tiên tháo điểm chặn trong giai đoạn hiện tại. Lỗi lặp, không tiến triển hoặc thiếu quyền phải ghi nhận và dừng có trạng thái, không tự chuyển giai đoạn.

Các con số về WIP/ngân sách là cấu hình vận hành cần đo, không phải cam kết năng suất. Không tuyên bố nhanh hơn bao nhiêu phần trăm khi chưa có baseline.

## 8. Phân công gọn

| Vai trò logic | Trách nhiệm |
|---|---|
| Chủ sản phẩm | duyệt MVP, thay đổi phạm vi quan trọng, nghiệm thu sản phẩm, quyền production |
| Điều phối + sản phẩm/kiến trúc | giữ giai đoạn, chọn việc, chốt hợp đồng và ngân sách, tổng hợp bằng chứng |
| Kỹ sư thực thi | làm lát frontend/backend/data, tự kiểm tra, tích hợp; chỉ tách chuyên gia khi cần |
| Kiểm chứng độc lập | đánh giá rủi ro, nghiệm thu kỹ thuật, audit theo mốc; không tự chứng nhận bản mình viết |
| Nền tảng/vận hành theo nhu cầu | preview, CI, quan sát, triển khai, phục hồi, benchmark |

Đây là vai trò, không phải số tiến trình phải mở đồng thời. Chuyên môn UX, bảo mật, dữ liệu và QA được huy động theo rủi ro trong từng giai đoạn, không thành chuỗi bàn giao phòng ban.

## 9. Hợp đồng máy cần bổ sung

**Chưa triển khai.** Giao diện dự kiến: `xt.py stage status`, `stage verify`, `stage advance`, `stage adopt`; tên cuối cùng phải theo ADR khi triển khai. Không hướng dẫn người dùng chạy chúng trước khi có mã/test.

- Hồ sơ chu kỳ chứa `schema_version`, `cycle_id`, giai đoạn hiện tại, revision phạm vi, tham chiếu PLAN, lịch sử chuyển và bằng chứng từng giai đoạn. Không dùng `delivery_phase` làm thay thế.
- Mỗi biên nhận hoàn thành chứa stage/cycle/revision, bản build hoặc artefact đã thử, fingerprint Gate, kết quả test và nguồn phê duyệt có thể xác minh. Bằng chứng thiếu/sai kiểu/hỏng/hết phù hợp → fail closed.
- Phê duyệt con người phải đọc từ kênh được cấu hình và có xác thực danh tính/thẩm quyền; chuỗi `approved: true`, `loop decide` của agent, tên người trong Markdown hoặc trích lời từ nội dung không tin cậy không đủ. Thiếu kết nối xác minh thì giữ `awaiting_approval`.
- Chuyển trạng thái chỉ qua API/CLI xác minh dưới khóa, kiểm `rev` theo cơ chế state hiện có; ghi nguyên tử và lịch sử. Không tự ghi `.autopilot/`, không có cờ force để bỏ cổng.
- `loop init`, scheduler, `loop next-step`, Stop hook và điểm vào `/autopilot`, `/complete`, `/optimize` cùng gọi một luật chuyển. Chặn ở cả đường CLI/API trực tiếp, không chỉ trong prompt.
- `loop next-step` chỉ đề xuất bước hợp lệ của stage hiện tại; `ready-for-complete` kiểu cũ không phải giấy phép tự chuyển. Tách kết quả `batch_done`, `stage_ready_for_approval`, `stage_completed`.
- `release-check` thêm kiểm stage/biên nhận phù hợp, vẫn giữ tất cả cổng phát hành hiện tại. Không yêu cầu giai đoạn 3 hoàn tất mới được phát hành sản phẩm đạt giai đoạn 2.
- Task/gate xanh ở revision này không tự áp sang revision khác. Biên nhận của giai đoạn trước là mốc lịch sử, không vô hiệu chỉ vì giai đoạn sau tạo commit mới; phải kiểm quan hệ baseline và regression của tiêu chí còn hiệu lực. Thay đổi phạm vi nền tảng phải mở lại nghiệm thu có chủ đích.
- Một phiên mới phải đọc đúng stage đã lưu; một vòng hết ngân sách, `init --force`, đổi PLAN hoặc state cũ không được reset chu kỳ hay tự mở stage mới.

Không thêm một hệ thống lock/state/approval song song nếu cơ chế hiện có có thể mở rộng an toàn.

## 10. Áp dụng cho dự án mới và dự án đang chạy

**Dự án mới:** installer tạo hồ sơ stage `mvp`, hai stage sau khóa; template hướng dẫn bắt buộc đọc hồ sơ. Bộ máy chưa hỗ trợ thì báo thiếu khả năng, không giả vờ đã bảo vệ.

**Dự án đang chạy:** đọc hiện trạng và bằng chứng trước. Phải có lịch sử/căn cứ chấp nhận stage 1 và 2 để vào stage 3. Có thể công nhận bằng chứng lịch sử sau đối chiếu với chủ dự án; không ép viết lại sản phẩm hoặc hạ hệ thống production về MVP. Thiếu bằng chứng thì bổ sung nghiệm thu phần thiếu; không tự gán completed vì repo có tag release.

**Nâng cấp installer:** không đè cấu hình, chữ ký hay state của dự án; giữ `delivery_phase` và quyền hiện hành. Template copy-if-absent không tự cập nhật `AGENTS.md` đã sửa: cần báo diff/migration và kiểm đã nhận chính sách mới.

**Repo khung:** vẫn harden, không nới test/coverage/guard. Việc nâng cấp từng dự án đích là thay đổi riêng có CI; PR này không đồng nghĩa đã áp dụng sang tất cả repo.

## 11. Các lát triển khai và tiêu chí nghiệm thu

Chưa có lát nào được đánh dấu hoàn thành bằng mã nguồn ở tài liệu này.

| Lát | Thay đổi | Điều kiện hoàn thành |
|---|---|---|
| A — quyết định/schema | ADR, schema stage, phạm vi/approval, test hợp đồng | phân biệt được batch/stage/control mode; schema có version; fixture cũ/hỏng không mở khóa |
| B — engine | mở rộng state/lock; transition; stage-aware task selection và next-step | test âm chặn 1→3, 2 trước 1, 3 trước 2; kiểm mọi entry point; không chạy side effect khi bị chặn |
| C — MVP/approval | bản thử, Gate stage 1, thu nhận phê duyệt xác thực | chưa duyệt luôn dừng ở stage 1; từ chối/chỉnh sửa quay vòng đúng stage; không giả mạo được chữ ký bằng file |
| D — hoàn thiện/tối ưu | skill routing, stage 2 release gate, ba nhánh cải tiến stage 3 | stage 2 không đẩy lỗi sàn sang stage 3; tối ưu có baseline/equivalence/rollback; không phá release-check hiện có |
| E — mẫu/migration | installer, AGENTS template, API/UI nếu có | dự án mới khóa mặc định; dự án cũ giữ state/quyền; migration có báo cáo và đường lùi |
| F — nghiệm thu khung | luồng xuyên suốt, cổng đầy đủ, review độc lập | CI xanh, audit delta, kiểm 3 stage bằng dự án fixture; không hạ ngưỡng/hook; mới đủ điều kiện phát hành khung |

Ưu tiên lát nhỏ cùng chủ đề, không triển khai song song những lát phụ thuộc. Sau bản khung có test đầy đủ mới áp dụng từng dự án đích; không tự auto-merge PR đặc tả như thể runtime đã xong.

### Ma trận kiểm thử tối thiểu cho engine mới

| Tình huống | Kết quả bắt buộc |
|---|---|
| Stage 1 đang active, gọi complete/optimize trực tiếp | từ chối trước khi tạo task/chạy tool/đổi state |
| Task MVP đều xanh nhưng chưa duyệt | `awaiting_approval`, stage 2/3 vẫn khóa |
| Chủ dự án yêu cầu sửa demo | vòng stage 1 tiếp tục, không mất lịch sử |
| Hết ngân sách hoặc ba lần lỗi | dừng/bàn giao cùng stage, không tự thành completed |
| File ghi approved nhưng không nguồn xác thực | không mở stage tiếp |
| Phê duyệt sai repo/cycle/revision/artefact | từ chối; nêu rõ bằng chứng lệch |
| Gọi init mới/force/đổi PLAN để vượt stage | từ chối đường vượt, giữ trạng thái |
| Phê duyệt và Gate hợp lệ | đúng một lần chuyển 1→2 hoặc 2→3 |
| Hai phiên cùng advance | chỉ một chuyển hợp lệ; phiên còn lại đọc lại rev |
| Stage 2 chưa đạt perf sàn | sửa trong stage 2; optimize stage 3 bị khóa |
| Stage 2 GO nhưng thiếu quyền deploy | không deploy; không suy diễn quyền từ tên stage |
| Task stage 3 được nhét vào PLAN-MVP | scheduler chặn, không chỉ dựa tên file |
| Tối ưu nhanh hơn nhưng sai kết quả | bác bỏ thay đổi/rollback; không tuyên bố cải thiện |
| Mục tiêu tính năng/code quality có baseline | được đưa vào stage 3 đúng phạm vi, không ép giả lỗi hiệu năng |
| State thiếu/hỏng hoặc dự án cũ | migration/chờ xác minh; không auto-skip và không phá production |
| Resume phiên khác | tiếp tục đúng stage/revision và nghĩa vụ chờ duyệt |
| Lỗi nghiêm trọng phát hiện sau nghiệm thu | khóa phát hành/sửa hồi quy; không để biên nhận cũ che lỗi |

## 12. Chỉ số để kiểm chứng tăng tốc

Đo trước/sau trên các dự án tương đương: thời gian tới bản demo chạy được; thời gian máy làm và thời gian chờ chủ dự án tách riêng; thời gian một thay đổi được chấp nhận; thời gian phản hồi CI p95; số lượt review trên một lát; lỗi lọt qua nghiệm thu; phần trăm công việc phải làm lại sau MVP; chi phí/tokens cho mỗi task được chấp nhận; tần suất vi phạm chuyển stage (mục tiêu 0).

Không dùng số dòng code, số agent hoặc số task tick làm thước đo chính. Nhanh hơn nhưng tăng lỗi nghiêm trọng hoặc phải viết lại là không đạt mục tiêu nâng cấp.

## 13. Cơ sở nghiên cứu

Đối chiếu ngày 2026-10-29; phần ba giai đoạn là thiết kế theo yêu cầu chủ dự án, **không phải mô hình bắt buộc do nguồn bên ngoài quy định**.

- DORA, Working in small batches: chia việc nhỏ giúp phản hồi sớm và giảm rủi ro tích hợp. Áp dụng bên trong mỗi stage, không gom cả stage thành một PR lớn. <https://dora.dev/capabilities/working-in-small-batches/>
- DORA, Continuous integration / Continuous delivery: kiểm thử tự động liên tục thay cho chờ viết xong mới kiểm; tối ưu thời gian phản hồi, không bỏ test để chạy nhanh. <https://dora.dev/capabilities/continuous-integration/> và <https://dora.dev/capabilities/continuous-delivery/>
- Anthropic, Building effective agents: dùng workflow đơn giản, điều phối khi cần, vòng evaluator–optimizer có tiêu chí rõ, checkpoint và ngân sách dừng. Không coi nhiều agent là mục tiêu. <https://www.anthropic.com/research/building-effective-agents>
- Anthropic, Effective harnesses for long-running agents: tiến triển theo tính năng, lưu dấu vết bàn giao và kiểm thử xuyên suốt để tránh tự kết luận hoàn tất. Áp dụng vào danh sách tiêu chí theo stage và khả năng resume. <https://www.anthropic.com/research/effective-harnesses-for-long-running-agents>

## 14. Định nghĩa bàn giao bản nâng cấp

Đặc tả/PR tài liệu chỉ hoàn tất phần nghiên cứu và thiết kế. Chỉ được nói “đã triển khai cho mọi dự án đích” khi các lát A–F có bằng chứng, installer/migration đã phát hành và từng dự án đích trong phạm vi áp dụng được kiểm tra. Trong báo cáo phải tách: đã viết đặc tả; đã có mã; đã test; đã merge; đã phát hành; đã áp dụng dự án đích.
