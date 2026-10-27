# Kế hoạch: một lượt review chính ở cuối pha

> Ngày: 2026-10-27 · Trạng thái: **ĐỀ XUẤT, CHƯA TRIỂN KHAI**.
> Phạm vi PR này: chỉ thêm kế hoạch; không đổi mã, cấu hình, hook, workflow, quyền merge hay cổng phát hành.
> Cơ sở khảo sát: `main` tại `9dc4f6a5eb9150d0ecd7c1e8b49604a482c45037`. Khi triển khai phải đối chiếu lại HEAD và PR đang mở.
> Đây không phải PLAN đang chạy: không thay PLAN-harden hiện hữu, không tự khởi tạo vòng lặp, không ghi `.autopilot/` bằng tay.

## 1. Kết quả cần đạt và giới hạn

Mặc định tương lai: **code trọn một pha chức năng → kiểm tự động liên tục → một lượt review tổng hợp → sửa theo lô → xác minh phần sửa → kết thúc pha**. Không gọi reviewer khi xong từng task, từng commit hoặc từng lỗi lint/test. Không dựng orchestrator thứ hai.

“Một lần” là **một lượt review toàn phạm vi đã chốt**, không phải cam kết chỉ một lời gọi công cụ cho mọi kích thước thay đổi. Một lượt có thể đọc nhiều phần liên quan; mọi lần gọi reviewer, kể cả chuyên gia và xác minh delta, đều phải được tính chi phí. Không giấu nhiều vòng dưới một tên mới.

Ưu tiên: giảm gọi reviewer và đọc lại ngữ cảnh, không giảm test, không dùng trần vòng lặp để cho code chưa an toàn đi qua. Mục tiêu một lượt không áp đảo yêu cầu review độc lập ở HEAD mới khi chính sách hiện hành còn bắt buộc.

## 2. Hiện trạng đã đối chiếu

| Điểm hiện hữu | Hệ quả cho kế hoạch |
|---|---|
| [`xt.yaml`](../../xt.yaml): `delivery_phase: harden`, `commit_gate: fast`, typecheck strict và coverage 100% | Không đổi repo khung về build để né review; giữ nguyên ngưỡng và cổng. |
| [ADR-0037](../adr/0037-reviewers-only-in-harden.md): build đã hoãn review, harden cần review sạch đúng head theo làn | Tái sử dụng review debt và bộ quyết định merge; không làm thêm một cơ chế hoãn song song. |
| [`/complete`](../../.claude/skills/complete/SKILL.md): audit, trả nợ theo cụm, review ngoại lệ trước PR, review khi `pr next` yêu cầu | Có nhiều điểm kích hoạt cần hợp nhất theo phạm vi/SHA; đây là khả năng trùng việc, chưa phải kết luận đo được. |
| [`/review`](../../.claude/skills/review/SKILL.md): diff trên 150 dòng đề nghị tách; `/complete` giới hạn mỗi lát 150 dòng | Muốn review pha lớn phải có ADR cập nhật quy tắc này. Không âm thầm bỏ giới hạn bằng prompt. |
| [`reviewer`](../../.claude/agents/reviewer.md): đọc diff thật, kiểm phần bị ảnh hưởng, trả INCONCLUSIVE khi thiếu bằng chứng | Giữ nguyên tính độc lập và quyền chỉ đọc; context bị cắt không được thành APPROVE. |
| [`orchestration-and-subagents.md`](../../framework/11-autonomous-loop/orchestration-and-subagents.md): một điều phối viên, Gate có bằng chứng | Gắn vào vòng lặp hiện hữu; không thêm tầng điều phối/reviewer thường trực. |

PR #296 đang mở tại lúc khảo sát, liên quan nối phiên và unblock. PR kế hoạch này không sửa các file của công việc đó. Không coi ghi chú trạng thái hoặc lời khai agent là bằng chứng hoàn tất.

## 3. Quyết định thiết kế đề xuất

**Chọn:** review theo pha có ranh giới nghiệm thu, kèm xác minh delta có điều kiện. **Không chọn:** review sau từng task; hoặc gom cả sản phẩm thành một diff khổng lồ rồi mới kiểm.

- Pha có một mục tiêu người dùng, acceptance criteria, hợp đồng API/schema, phạm vi ảnh hưởng, cách kiểm và đường lùi. Pha khác với `delivery_phase: build|harden`; kết thúc pha không tự đổi cấu hình giao hàng.
- Chốt phạm vi trước code. Task/commit vẫn nhỏ, tích hợp và chạy kiểm thường xuyên. Pha không được định nghĩa bằng “cứ đủ 10–30 task”. Vượt khả năng đọc/kiểm thì tách theo hành vi trước khi bắt đầu audit.
- Build: dùng PR nhỏ và review debt đã có; không gọi reviewer theo task. Mốc kết thúc pha gom phạm vi chưa được rà vào một audit. Audit pha phải được đăng ký để `/complete` không rà lại phần đã có bằng chứng còn hiệu lực.
- Harden/production: không merge task chưa đủ điều kiện vào nhánh được bảo vệ. Đề xuất một PR cho một pha có phạm vi gắn kết, bên trong là commit/task nhỏ; phải được ADR mới cho phép trước khi thay luật PR/lát hiện tại. Trong thời gian chuyển tiếp vẫn theo chính sách cũ.
- Mọi xung đột với G0–G8, ruleset, yêu cầu người ký, năng lực reviewer và release-check phải được giải quyết tường minh ở ADR/kiểm thử. PR này không cấp quyền miễn các yêu cầu đó.

## 4. Luồng vận hành và điều kiện dừng

| Trạng thái đề xuất | Điều kiện/chuyển tiếp | Gọi reviewer |
|---|---|---|
| `implementing` | Chốt contract; code/test/tích hợp; CI đỏ thì sửa trong phạm vi task | Không theo từng task |
| `ready_for_audit` | Task trong pha có bằng chứng; Gate đầy đủ đạt; diff, tiêu chí và dependency manifest đã chốt | Chưa gọi khi thiếu đầu vào |
| `auditing` | Một lượt độc lập bao phủ phạm vi, các đường nối và rủi ro; trả một batch findings cùng coverage manifest | 1 lượt chính |
| `batch_fix` | Điều phối viên xác minh finding, gom theo nguyên nhân/phụ thuộc; thêm regression rồi sửa | Không cho mỗi finding |
| `verifying` | Kiểm lại finding và delta bị ảnh hưởng; chạy lại kiểm phù hợp ở HEAD mới | 0 hoặc 1 lượt delta có điều kiện |
| `accepted` | Không blocker; bằng chứng và verdict hợp lệ đúng phạm vi/HEAD; cổng hiện hữu đều đạt | Không audit lại toàn pha |
| `blocked` | Còn blocker, bằng chứng thiếu, hết ngân sách, sai scope hoặc lặp không tiến triển | Dừng tự động, không tự restart |

Ngân sách mặc định đề xuất: **1 full audit + tối đa 1 delta verification tự động/pha**. Reviewer chính đồng thời kiểm các rủi ro thuộc năng lực của mình; không tự gọi thêm reviewer thứ hai “cho chắc”. Chuyên gia chỉ tham gia vì rủi ro cụ thể hoặc thiếu năng lực, phải ghi lý do, phạm vi và chi phí riêng.

Sau một lần batch fix và delta verification vẫn chưa đạt: chuyển `blocked`, ghi nguyên nhân và phương án thay đổi; không mở lại full audit hoặc luân phiên reviewer vô hạn. Quyết định tiếp tục phải có người/điều phối viên được cấp quyền, chiến lược mới và ngân sách mới được ghi nhận. Đổi tên pha, đổi phiên hoặc push commit không được làm mất bộ đếm. Lỗi nghiêm trọng vẫn chặn phát hành dù ngân sách đã hết.

Không đưa ra một trần sửa lỗi vô hạn cho security: dừng vòng tự động và xử lý có trách nhiệm. Thay đổi auth, phân quyền, tenant, tiền, migration dữ liệu, guard hoặc quyền merge phải được định tuyến rủi ro trước; thiếu kiểm chứng phù hợp thì dừng, không đợi đến cuối để coi như ngoại lệ được miễn.

## 5. Hợp đồng review, findings và bằng chứng

**Gói review tối thiểu:** phase ID/revision, base SHA, head SHA, danh sách file/đường phụ thuộc, acceptance criteria, diff thật, kết quả kiểm do máy ghi, rủi ro và phần chưa kiểm. Reviewer được đọc mã ngoài diff khi bị ảnh hưởng. Không chỉ đọc bản tóm tắt của người viết, không nạp lại toàn repo theo thói quen, không nhận lập luận tự bảo vệ của người viết.

**Mỗi finding:** ID ổn định, fingerprint theo nguyên nhân + vị trí ngữ nghĩa (không chỉ số dòng), mức độ, tác động, tiêu chí vi phạm, file/dòng hoặc đường dữ liệu, bằng chứng, cách xác minh sau sửa và owner. Lỗi không thể tái hiện bằng test phải có lập luận kỹ thuật kiểm chứng được và được đánh dấu để xác minh độc lập; không ép mọi rủi ro kiến trúc/bảo mật thành test giả.

| Loại | Xử lý |
|---|---|
| Blocker có bằng chứng: sai nghiệp vụ/contract đã chốt, mất dữ liệu, bảo mật, kiểm bắt buộc thất bại | Sửa trước khi chấp nhận pha; không hạ severity để đạt ngân sách |
| Thiếu dữ kiện hoặc nghi ngờ | Xác minh có mục tiêu; rủi ro chưa phân giải có thể giữ trạng thái INCONCLUSIVE, không tự chấp nhận |
| Gợi ý style/refactor/tối ưu không thuộc điều kiện bắt buộc | Ghi backlog có owner; không kích hoạt vòng sửa/review mới |

Finding cũ được liên kết với commit sửa và bằng chứng đóng; kết quả trùng không tạo task mới. Regression thực sự vẫn được mở lại. Vòng delta chỉ xét lỗi đã nêu, phần sửa và ảnh hưởng của nó; vấn đề mới nghiêm trọng hoặc vi phạm acceptance criteria vẫn phải được ghi nhận. Không “đóng băng findings” theo cách che lỗi thật.

**Đóng bằng máy** chỉ khi finding thuộc lớp kiểm được: test tái hiện thất bại đúng nguyên nhân trên revision lỗi, đạt sau sửa, regression liên quan đạt, không giảm assertion/skip test/hạ cổng. Bằng chứng do runner ghi, không tin đoạn log do executor tự chép. Finding được đóng không đồng nghĩa review của toàn PR đã được approve.

**Đúng HEAD:** review có khóa theo repo, phase revision, base/head, digest phạm vi/phụ thuộc, phiên bản policy và cấu hình kiểm. Sau batch fix ở harden, nếu cổng yêu cầu review sạch HEAD mới thì phải có reviewer độc lập xác minh delta và ghi verdict hợp lệ tại HEAD đó. Không sao chép APPROVE cũ, không biến test xanh thành review độc lập. Cache chỉ tránh đọc lại phần không đổi; không tự thỏa yêu cầu approval của GitHub.

Thay đổi contract, dependency, test/cấu hình kiểm, vùng nhạy cảm, nội dung chưa được rà, merge-base hoặc phần liên quan trên nhánh đích phải làm mất hiệu lực bằng chứng bị ảnh hưởng. Chỉ tiếp tục dùng phần còn hiệu lực khi máy chứng minh được phạm vi; không chắc thì INCONCLUSIVE. Kiểm trước merge và release vẫn ghim đúng head, không dùng kết quả stale.

**Chống review trùng:** review trước PR và sau PR dùng chung khóa/bản ghi hợp lệ; audit pha và audit release dùng chung coverage manifest. Không có thay đổi đầu vào thì không spawn reviewer lại. Full audit vẫn đọc toàn bộ phạm vi một lần; delta verification không phải full audit trá hình. Không viết tay trạng thái/bằng chứng `.autopilot/`.

## 6. Kế hoạch triển khai theo lát

Các mã `RV-01`…`RV-07` chỉ dùng trong tài liệu này, chưa phải task đã duyệt/chạy trong PLAN. Khi triển khai, cấp task ID/ADR mới không trùng, dùng mẫu PLAN hiện hữu và Gate thật; không đưa pseudo-config vào `xt.yaml`.

| Lát / phụ thuộc | Công việc và điểm chạm dự kiến | Nghiệm thu |
|---|---|---|
| RV-01 / không | Đối chiếu mã `scripts/xt.py`, đường `pr next`/`pr reviewed`/merge-check/release-check, `/autopilot`, `/complete`, `/audit`; đo baseline; lập ADR so sánh các phương án, xác định phạm vi cập nhật luật 150 dòng và PR/lát | Sơ đồ trigger trước/sau; danh sách policy xung đột; baseline có SHA/log hoặc ghi chưa đo; ADR được chấp nhận trước đổi hành vi |
| RV-02 / RV-01 | Hợp đồng phase/finding/evidence, version và chuyển trạng thái trong engine hiện hữu; migration dữ liệu cũ, khóa theo head, atomic update/chống chạy trùng | Dữ liệu cũ vẫn dùng được; không sửa bằng chứng tay; cùng event chạy hai lần không tạo hai review; resume không xóa ngân sách |
| RV-03 / RV-02 | Gom trigger cuối pha; một reviewer chính, batch findings; tái sử dụng bằng chứng review trước/sau PR; cập nhật skill và template từ một nguồn quy tắc | Fixture nhiều task cùng pha không gọi reviewer theo task; đúng một full audit; thiếu coverage/context trả INCONCLUSIVE |
| RV-04 / RV-03 | Batch fix, đóng finding bằng máy khi đủ điều kiện; verifier delta; fingerprint chống trùng; circuit breaker cho chu kỳ không tiến triển | Lỗi hợp lệ đóng có bằng chứng; lỗi lặp không tạo task trùng; hết ngân sách còn blocker thì blocked; không auto-approve HEAD mới |
| RV-05 / RV-02, RV-04 | Nối review debt, audit coverage và cổng merge/release; giữ làn/ruleset/ngưỡng; kiểm thay đổi base/head và trusted policy từ nhánh đích | Chặn stale verdict, chính sách tự nới trong PR, CI đỏ, nợ chưa trả và thiếu chữ ký bắt buộc; không review lại phần thực sự còn hiệu lực |
| RV-06 / RV-03…RV-05 | Test đối kháng, tích hợp, tài liệu vận hành và rollback; đối chiếu tương tác công việc loop attach/resolve/unblock đang có | Tất cả ca ở §7 đạt; full Gate/CI hiện hành xanh; không sửa/hạ test, coverage hay giới hạn tài liệu để qua |
| RV-07 / RV-06 | Pilot có opt-in tường minh ở môi trường không production; ghi token/thời gian/escaped defects; cập nhật release notes, template/version khi thực sự đổi nghĩa vụ dự án đích | Báo cáo trước/sau có dữ liệu; chỉ đổi mặc định sau quyết định rollout; đường lùi đã diễn tập, không mất findings/debt |

Phân công: điều phối viên chốt kiến trúc/policy và tiêu chí; executor thường làm wiring/tài liệu/fixture rõ; executor sâu làm state, evidence, merge/release và ca đối kháng. Reviewer chỉ đọc/kiểm, độc lập với tác giả và đáp ứng yêu cầu năng lực hiện hành. Các lát sửa cùng `scripts/xt.py`/hợp đồng state đi tuần tự, không chạy đua file.

## 7. Ma trận kiểm thử bắt buộc khi triển khai

| Ca | Kết quả phải chứng minh |
|---|---|
| Một pha 10 task thông thường, không blocker | Không review từng task; một full audit; không delta khi không cần |
| Finding kiểm được, policy không yêu cầu review lại | Test đỏ đúng nguyên nhân trước sửa, xanh sau sửa; auto-close finding; không gọi reviewer thừa |
| Harden: sửa code sau verdict | Verdict cũ không dùng ở HEAD mới; một delta review độc lập khi bắt buộc |
| Pre-PR review và `pr next` cùng phạm vi/head | Không review trùng; chỉ dùng bằng chứng độc lập hợp lệ, không lời khai |
| Base/merge-base đổi, dependency hoặc test policy đổi | Invalidated đúng phần; chạy kiểm/xác minh lại; không cache-hit giả |
| Diff bị cắt, thiếu file/caller hoặc thiếu budget | INCONCLUSIVE; không APPROVE phần chưa đọc |
| Finding lặp, đổi số dòng, sửa A làm hỏng B | Dedupe đúng; regression B được ghi/chặn; không mở vòng full mới tự động |
| Một lượt full + một lượt delta vẫn còn blocker | blocked; cần quyết định mới, không đổi reviewer/phase ID để reset |
| Security/auth/tenant/migration/guard | Kiểm phù hợp và độc lập; không tự đóng chỉ vì unit test xanh |
| Resume/attach, retry event, hai worker đồng thời | Không mất ledger/budget; không spawn trùng; cập nhật state nguyên tử |
| PR tự chuyển `harden` sang `build` hoặc sửa policy cho chính nó | Không được miễn review/merge nhờ cấu hình tự nới |
| Build còn debt; release thiếu kiểm/chữ ký; CI đỏ | Vẫn NO-GO theo cổng hiện hữu; phase accepted không đồng nghĩa release approved |

Gates sau triển khai: `scripts/dev-task.sh gate`, `python3 scripts/xt.py checks`, các test tích hợp mới, và release-check trong fixture phù hợp; giữ `mypy --strict`, coverage dòng/nhánh 100% và kiểm ngân sách tài liệu. Đó là tiêu chí tương lai, không phải báo cáo đã chạy trong PR kế hoạch.

## 8. Đo hiệu quả, rollout và đường lùi

Đo theo pha và tách mức rủi ro/kích thước: số full/delta/expert review, số lần spawn, token vào/ra/cached, chi phí thực nếu có bảng giá, tổng thời gian và thời gian chờ review, số finding hợp lệ/trùng/mở lại, số lần sửa, escaped defects và sự cố release. Tính cả chi phí batch fix/test/điều phối để tránh “tiết kiệm reviewer nhưng tốn hơn toàn hệ thống”.

Baseline ưu tiên các pha gần đây có đủ log; log thiếu thì đo tiến về trước, không suy từ số comment. Pilot tối thiểu 5 pha thông thường và toàn bộ fixture rủi ro cao; đây là mẫu thăm dò, không đủ để khẳng định an toàn thống kê. Mục tiêu thử nghiệm: không review từng task, một full audit/pha thường, median chi phí reviewer và thời gian chờ giảm ít nhất 50% so với nhóm tương đương. Đây là mục tiêu đề xuất, chưa phải kết quả đo hoặc cam kết.

Bất kỳ bằng chứng bypass cổng, stale approval, mất ledger hoặc lỗi nghiêm trọng do cơ chế hoãn review đều dừng rollout ngay. Chưa đủ dữ liệu chất lượng thì không tuyên bố tương đương; mở rộng quan sát trước khi đổi mặc định. Rollback quay về chính sách reviewer trước đó qua thay đổi được duyệt, giữ toàn bộ findings/debt/evidence, không đổi về build và không hạ cổng để mở đường.

## 9. Cơ sở nghiên cứu và mức chắc chắn

Nguồn kiểm tra ngày **2026-10-27**; các kết luận dưới đây là nguyên tắc tham khảo, không phải benchmark cho X-Templates:

- [Google — Small CLs](https://google.github.io/eng-practices/review/developer/small-cls.html): thay đổi nhỏ dễ kiểm/hoàn tác; không chứng minh rằng một diff khổng lồ review một lần sẽ tốt hơn. Suy ra: gộp lịch gọi reviewer, không gộp vô hạn phạm vi.
- [Google — Standard of Code Review](https://google.github.io/eng-practices/review/reviewer/standard.html): không đòi hoàn hảo; phân biệt gợi ý nhỏ với yêu cầu bắt buộc, dùng bằng chứng khi bất đồng. Suy ra: findings có contract, non-blocking không kéo thêm vòng.
- [Continuous Integration](https://martinfowler.com/articles/continuousIntegration.html): tích hợp thường xuyên kèm build/test tự động. Suy ra: giảm tần suất review không có nghĩa hoãn tích hợp/kiểm đến cuối pha; chỉ test nhánh riêng không tự đồng nghĩa CI trên main.
- [GitHub — Protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches): thay đổi diff/base có thể làm approval hết hiệu lực; có yêu cầu approval cho push mới nhất. Suy ra: cache không thay được approval mà ruleset đòi.

Phương án phase-gated và các ngân sách/threshold ở đây là **thiết kế đề xuất cần pilot**. Không dùng trích dẫn để khẳng định đã giảm token, đã tăng chất lượng hay chỉ cần đúng một lời gọi review trong mọi tình huống.

## 10. Tiêu chí hoàn tất PR kế hoạch này

Chỉ tài liệu mới, các liên kết/nội dung được kiểm tra, không thay cấu hình hay ghi nhận triển khai xong. PR nêu rõ kiểm nào đã chạy và kiểm nào chưa chạy; giữ mở để duyệt, không tự merge hoặc bật auto-merge. Khi được triển khai, bắt đầu RV-01, đối chiếu HEAD/PR hiện hành và dùng quy trình hiện hữu cho tới khi chính sách mới thực sự được chấp nhận.
