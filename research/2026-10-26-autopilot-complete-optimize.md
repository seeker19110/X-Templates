---
title: Nâng mức tự chủ của /autopilot, /complete và /optimize
kind: research
updated: 2026-10-26
---

# Nâng mức tự chủ của ba vòng — nghiên cứu và đề xuất 2026-10-26

> Mốc nghiên cứu ban đầu: X-Templates 3.26.1, `4e7bade7625ec9f70accfc9f293d533b905533a7`.
> Đối chiếu trước PR: `main` 3.27.0 tại `74c47aa34755df9e6c38bf74ede31179fb6ad04c`, nhánh `docs/research-three-loops`.
> Đầu vào: “nâng cấp tự động lên được nữa không? nghiên cứu sâu và đề xuất”, bổ sung cả `/complete` và `/optimize`.
> Trạng thái: **đề xuất, chưa triển khai hoặc chốt kiến trúc**. Chỉ thêm báo cáo và bằng chứng nghiên cứu; không đổi quyền, cổng, skill, runtime hay bản phát hành.

## 1. Kết luận và lựa chọn đề nghị

**Có thể nâng thêm cả ba vòng.** Dư địa lớn nhất là biến các bước agent đang phải nhớ thành chuyển trạng thái có bằng chứng: tự xác định việc còn thiếu, nối lại đúng chỗ, thu hồi lần thử không đạt và chuẩn bị hồ sơ nghiệm thu. Công cụ kiểm từng bước đã khá đầy đủ; điều phối giữa các bước và giữa các đợt còn phụ thuộc vào skill.

Đề nghị chọn hướng **máy quyết bước kế, agent thực hiện việc chuyên môn**, phát triển từ CLI/state hiện có. Bắt đầu bằng bộ tính bước kế chỉ đọc, chạy so sánh với phiên thực; chưa dựng dịch vụ điều phối ngoài phiên. Giữ ba điểm vào theo chủ ý của ADR-0046/0047/0048: build hết việc thì đề xuất `/complete`; người gọi `/complete` cho phép làm harden đến gói chờ ký; `/optimize` chỉ chạy khi có ngân sách đỏ có số.

Ba phương án đã so:

| Phương án | Đúng/an toàn | Đường lùi và bảo trì | Khả năng kiểm chứng | Kết luận |
|---|---|---|---|---|
| Chỉ thêm lời nhắc vào skill | Không giải quyết mất trạng thái hoặc bỏ bước | Rẻ ban đầu, skill đã sát trần | Khó biết agent thực sự theo đủ | Chỉ dùng cho hướng dẫn ngắn |
| Máy hóa bước kế và một lần thử, dùng công cụ sẵn có | Điều kiện chuyển trạng thái tường minh | Có thể thử chỉ đọc, sửa từng lát | Kiểm được bằng trace và fault injection | **Đề nghị** |
| Runner ngoài phiên tự gọi agent, sửa CI và phát hành | Có thể hoạt động lúc người dùng rời phiên | Thêm quyền, chi phí, trạng thái và vận hành | Cần pilot + sandbox thực | Chỉ xét sau khi đo chứng minh cần |

Đánh giá theo thứ tự của AGENTS: đúng/an toàn → giữ đường lùi → bền, đơn giản và test được → trải nghiệm → tốc độ/chi phí. Chưa có baseline vận hành để gán điểm số trọng số hoặc hứa tăng tốc bao nhiêu phần trăm.

## 2. Bằng chứng tại mốc nghiên cứu ban đầu

Nghiên cứu gồm bốn nhánh đọc độc lập: lõi vòng lặp; delivery/phản hồi; phản biện an toàn và phép đo; nguồn chính thức sống. Phiên chính đối chiếu code và tái hiện hai tình huống riêng trong bộ nhớ/thư mục tạm, không thay `.autopilot/` thật. Các nhánh cùng runtime không được tính là reviewer có năng lực cao hơn hoặc corpus đối kháng độc lập.

| Kiểm tra | Kết quả tại mốc trên | Giới hạn kết luận |
|---|---|---|
| `python3 scripts/xt.py autonomy-bench --json`, exit 0 | 478/478; false-green, false-red, mismatch, error đều 0 | Kiểm corpus hữu hạn; không chứng minh toàn luồng agent an toàn |
| Nguồn ca và phạm vi corpus | `adversarial-reviewer=0`; 90/153 ID có ca, 63 ngoài phạm vi có lý do | Không phải 63 lỗi chưa có test; nhiều ID được unittest khác kiểm |
| `python3 scripts/xt.py loop stats --all --json`, exit 0 | 0 task, 0 run; các tỷ lệ chưa đo là `null` | Checkout không mang lịch sử runtime, không suy ra repo chưa từng đo |
| Gọi `_loop_resume` với state giả, exit 0 | Đổi session xóa `deferred`, đặt lỗi lặp 2 → 0; giữ iterations và deadline | Hợp đồng resume hiện coi việc chờ đã được xử lý; chưa phải bằng chứng khai thác |
| `perf compare` với hai artifact giả, exit 0 | Cùng lệnh; 100 ms so với 0,1 s bị báo `improved`, change −99,9%; metadata môi trường cũng khác | Phép thử tính hợp lệ đầu vào, không phải benchmark tăng tốc; `perf sample` tự sinh luôn dùng giây |
| Đo byte theo đúng `tests/test_docs_budget.py` | Nhóm scripts còn **31 B**; hooks 824 B; mảng 11 còn 10 B | Thêm tính năng 3.x phải gỡ/gộp phần khác cùng nhóm, không lách đường dẫn |
| Skill còn chỗ | autopilot 1 B; complete 150 B; optimize 38 B; README mảng 11 hết dư | Không thể giải quyết bằng nối thêm checklist dài |

Bằng chứng JSON: [benchmark](evidence/2026-10-26-three-loops/autonomy-bench.json), [stats](evidence/2026-10-26-three-loops/loop-stats.json), [resume](evidence/2026-10-26-three-loops/resume.json), [metadata phép đo](evidence/2026-10-26-three-loops/perf-metadata.json), [byte budget](evidence/2026-10-26-three-loops/size-budgets.json).

### Đối chiếu `main` mới trước PR — 2026-10-26

Theo yêu cầu cập nhật `main`, đã fetch và tạo nhánh từ `74c47aa` (3.27.0), mới hơn mốc nghiên cứu năm commit. Giữ nguyên bảng và artefact cũ để có dấu vết; các số cũ **không phải hiện trạng của PR**. Đo lại trên `main` mới:

- `autonomy-bench --json` exit 0: **518/518**, false-green/false-red/mismatch/error đều 0; **33 ca `adversarial-reviewer`**, 92/155 ID có ca, 63 ngoài phạm vi có lý do, không có ID chưa được phân loại. T-3532 đã hoàn tất; đề nghị bổ sung eval đầu-cuối vẫn còn giá trị nhưng không còn nợ “0 ca reviewer”. Nguồn ca do corpus khai báo, không phải phép kiểm danh tính độc lập.
- T-3533 đã có [báo cáo spike mutation](../docs/ops/MUTATION-2026-10-26.md): 13.486 mutant được sinh, dừng khi thu thống kê, chưa có điểm killed/survived; D-197 không đưa mutmut vào CI ở dạng này. Không đề nghị làm lại spike hay mặc định thêm job mutation.
- [ADR-0050](../docs/adr/0050-raise-dir-size-caps.md) đã được chấp nhận và triển khai: mỗi trần thư mục thêm 1 MiB. Scripts còn **1.048.607 B**, hooks **1.048.505 B**, mảng 11 **1.048.586 B**. Đính chính kết luận chỗ trống: hiện không còn bị bó vào 31 B hoặc yêu cầu bù byte từng tính năng như trước. Trần từng file vẫn giữ: skill autopilot/complete/optimize còn lần lượt 1/150/38 B.
- `loop stats --all --json` exit 0 vẫn không có lịch sử runtime tại checkout này. `scripts/xt.py` và ba skill không đổi giữa hai mốc; tái hiện resume và metadata ở mốc cũ vẫn áp dụng cho cùng mã hiện tại. Bản vá guard/hook mới là thay đổi riêng đã có trên `main`.

Bằng chứng đo lại: [benchmark main](evidence/2026-10-26-three-loops/autonomy-bench-main.json), [stats main](evidence/2026-10-26-three-loops/loop-stats-main.json), [byte budget main](evidence/2026-10-26-three-loops/size-budgets-main.json). Thứ tự triển khai ở §8 đã điều chỉnh theo kết quả mới.

### Đã có thật — tận dụng trước khi xây mới

- `/autopilot`: DAG task, Gate đúng lệnh, evidence/fingerprint, verify cây cuối, checkpoint, nâng tầng executor, giới hạn lỗi, carry việc chờ sang đợt mới. ADR-0047 đã triển khai vòng build → audit → đợt kế ở skill và hỗ trợ `loop init`; không phải chưa có vòng này.
- `/complete`: audit theo SHA/phạm vi, nợ review, sàn M/L, `release-check` JSON gồm 10 hàng và mẫu GO-NO-GO. `release_check` tại `scripts/xt.py:8513` tách `fails` và `human`; `go=true` nghĩa không có FAIL máy chặn, vẫn có thể là `GO (chờ người)`.
- `/optimize`: sample/compare/guard, bộ đo khóa, test tương đương, giữ/bỏ theo số, chính sách chỉ làm ngân sách đỏ và nhận số field qua file. Không cần dựng lại một autoresearch chung chung.
- Delivery: steward đã nghe sự kiện và có cron dự phòng, merge ghim head; CI triage có episode và giới hạn. Installer đã có manifest hash, `--plan`, giữ custom và `.xtemplates-new`; `doctor --drift`, feedback aggregate và thống kê PR đã có.

## 3. Nền chung cần nâng trước

### A. Tách nối phiên khỏi giải quyết việc chờ — ưu tiên đầu

`scripts/xt.py:6940` luôn mở block, xóa chữ ký/số lần lỗi và danh sách deferred khi resume. Trong khi đó luồng đổi session cũng hướng dẫn dùng resume. PLAN không mất task, nhưng nhãn “đang chờ” và lịch sử chặn bị giải phóng rộng hơn nhu cầu chỉ nối phiên.

Đề nghị tách hai ý nghĩa: **gắn session mới** giữ nguyên deferred/lỗi/ngân sách; **giải quyết một việc hoặc mở block** cần ID/lý do riêng và lưu dấu vết. Tên CLI cụ thể sẽ chốt khi có ADR; chưa có lệnh mới trong bản nghiên cứu này.

Nghiệm thu: nối phiên không xóa bất kỳ deferred nào, không mở blocked; giải quyết một ID không ảnh hưởng ID khác; deadline, iterations và chi phí episode không tăng/reset ngoài chính sách. State cũ có đường chuyển tương thích. Rủi ro chính là đổi nghĩa CLI cũ; cần thông báo rõ thay vì âm thầm đổi.

### B. Một bộ quyết bước kế, ba mục tiêu kết thúc

Đề nghị bộ tính thuần nhận state/PLAN/blueprint/audit/PR/perf artifacts, trả `action`, lý do, bằng chứng còn thiếu và khóa định danh. Ba skill chỉ trình bày và gọi đường tương ứng; không tạo ba bộ luật merge/review/Gate khác nhau.

Mỗi mục tiêu có ngân sách chung sống qua đổi PLAN: thời gian, số lần thử, số đợt và thời gian không tiến triển. `iterations` hiện tăng ở Stop hook (`scripts/xt.py:2912`), không phải mọi tool call; giới hạn ba lỗi cùng chữ ký cũng không bao phủ lỗi A/B luân phiên. Thiếu nguồn chi phí thì ghi `null`, không ghi 0 hoặc hứa trần tiền mà runtime không cưỡng chế được.

Khi bổ sung tiến trình nền mới, phải có chủ ghi state và revision/khóa ngắn. `write_atomic` hiện chống file ghi dở; chưa chứng minh chống mất cập nhật từ hai snapshot cũ. Đây là rủi ro thiết kế **chưa tái hiện race**. Không giữ khóa qua Gate/network. Với hiệu ứng bên ngoài, ghi ý định và đối soát kết quả thực trước retry; không hứa exactly-once.

## 4. `/autopilot`: tự khép đợt, audit và lập đợt kế

**Khoảng thiếu:** `loop_verdict` (`scripts/xt.py:1830`) kiểm state/PLAN/blueprint; `hook_stop` (`:2893`) cho dừng khi đợt đã done và verify cuối đạt. Audit tiếp, PR đã được xử lý đủ chưa và đợt kế hiện do skill nối (`.claude/skills/autopilot/SKILL.md:29`). Máy đang xác nhận xong đợt, chưa xác nhận toàn mục tiêu đã hết việc.

Đề nghị trạng thái mục tiêu: làm task → verify → xử lý PR của lát → audit → có phát hiện/MUST mở thì lập đợt kế → audit full sạch → sẵn sàng đề xuất complete. PR chờ CI không chặn làm task độc lập nhưng phải được đối soát trước báo toàn mục tiêu đã xong. Audit vẫn do công cụ/reviewer thực hiện; máy kiểm phạm vi, SHA và hồ sơ, không tự chứng minh nội dung audit đúng.

**Nghiệm thu:** task xanh nhưng PR còn `fix/review/wait` chưa được báo hết việc; chưa audit thì trả audit; có 🔴/🟠 thì trả việc sửa; audit sạch nhưng còn MUST ngoài deferred thì tiếp tục; hết việc mới trả trạng thái sẵn sàng đề xuất `/complete`. Không tự đổi sang harden: D-178 đã chủ động giữ bước này cho người dùng.

Lợi ích kỳ vọng là bớt dừng sớm/bỏ bước sau `done`; chưa đo được mức giảm can thiệp. Rủi ro là audit/replan lặp mãi; ngân sách toàn mục tiêu và điều kiện không tiến triển phải đi cùng.

## 5. `/complete`: từ kiểm tra rời rạc tới gói nghiệm thu tự sinh

### C. Tự gom việc harden và trả nợ review

Hiện skill bước 2–4 yêu cầu agent đọc nhiều nguồn rồi tự ghép PLAN. Đề nghị gom finding audit, MUST chưa đạt, sàn đỏ và `release-check.fails` thành **danh sách việc nháp có ID ổn định**, nguồn và Gate đề nghị. Phiên chính vẫn tự duyệt cách sửa; máy không biến mô tả audit thành lệnh tùy ý. Hàng chờ quyền/người ký đi vào pending riêng, không tạo task “sửa code” vô hạn.

Nợ review chia theo PR/lát và SHA đã quét, ghim base/head và phạm vi. HEAD đổi thì xác định phần cần xem lại; không đánh dấu đã trả nợ chỉ vì có một comment “clean”. Dùng lại `review_debt` (`scripts/xt.py:8436`) và cơ chế review hiện có.

**Nghiệm thu:** chạy lại cùng đầu vào không sinh task trùng hoặc làm mất tick; finding mới chỉ thêm việc mới; thay head làm hết hạn đúng bằng chứng liên quan; còn FAIL máy thì tiếp tục sửa, chỉ còn việc người thì tập hợp một lần. Không tự đóng finding chỉ vì đã sinh task.

### D. Tự dựng hồ sơ phát hành, giữ nghiệm thu có thẩm quyền

Tự xuất phần máy của GO-NO-GO từ bằng chứng thật: SHA/bản ứng viên, CI run, audit phạm vi, review đã trả, test, attack/perf, đường lùi và phần chưa chứng minh. Giữ riêng ba khái niệm: **máy đã đạt**, **còn người xác nhận**, **đã được phép phát hành**. Không dùng riêng boolean `go` làm quyền deploy/publish.

Chữ ký/nhận xét người dùng là chủ ý của ADR-0048, không phải việc agent quên làm. Gói chờ ký phải cụ thể và có thể xem lại; người không cần tự chắp log. Xác nhận gắn với bản ứng viên và fingerprint bằng chứng; sửa mã sau nghiệm thu làm hết hạn phần liên quan, thay đổi chỉ tài liệu chữ ký không được gây vòng lặp vô tận.

**Nghiệm thu:** mỗi PASS có nguồn chạy thật; không điền cột “Người đã đọc” hoặc dòng 20 thay người; `human[]` không bị bỏ qua; GO-NO-GO không mang bằng chứng của bản cũ. Bản chỉ tối ưu chỉ dùng delta khi diff thỏa ADR-0048; chạm migration/schema/manifest/hạ tầng hoặc hành vi thì dùng gói đầy đủ.

## 6. `/optimize`: quản lý thử nghiệm và nghiệm thu hiệu quả

### E. Kiểm tính hợp lệ phép đo trước khi nhận cải thiện — ưu tiên đầu

`_perf_compare_cmd` (`scripts/xt.py:10618`) so lệnh khi cả hai file có `cmd`, rồi đọc samples; không so unit/platform/input/bộ đo. Thử nghiệm §2 cho thấy metadata không tương thích vẫn có thể thành improved. Hai phía có thể khác commit, hoặc cùng HEAD nhưng candidate có diff chưa commit; `perf sample` hiện chỉ ghi HEAD. Phải xác minh đúng **base SHA và fingerprint cây/diff candidate thực sự được đo**, không chỉ so hai SHA.

Đề nghị artifact chuẩn cho luồng tự động: metric + đơn vị + chiều tốt hơn + số mẫu/warm-up + hash input/harness/tool + môi trường đo + base SHA + candidate HEAD/fingerprint cây (gồm file chưa commit/chưa track liên quan) + ngưỡng đã định. Thiếu hoặc lệch trường trọng yếu thì kết luận **không đủ điều kiện so**, không chấm nhanh hơn. Có thể giữ khả năng nhập mảng thô cho dùng thủ công với giới hạn rõ ràng.

Ghim `origin/main` thành SHA bất biến lúc mở lần thử; hiện skill dùng ref có thể thay đổi giữa các lần fetch. Định trước số mẫu/ngân sách thử; đo xen kẽ trước/sau khi phù hợp, xác nhận candidate trên lượt/tập giữ lại. Không đo tiếp đến khi chọn được một lần xanh. `--no-regress` chấp nhận neutral nghĩa chưa phát hiện khác biệt, không tự chứng minh không suy giảm; chỉ số phụ vẫn cần trần tuyệt đối/tolerance đã định.

**Nghiệm thu:** ca 100 ms/0,1 s bị từ chối hoặc chuẩn hóa đúng, không báo tăng tốc; đổi input/máy/harness không được giữ candidate; thiếu mẫu hoặc nhiễu cao trả chưa kết luận; p99/bộ nhớ/chi phí vượt trần vẫn đỏ dù metric chính improved. Bộ đo và test tương đương vẫn nằm ngoài phần agent được sửa.

### F. Máy quản lý trọn một lần thử: chuẩn bị → đo → giữ/bỏ → ghi sổ

Hiện `perf compare` trả kết quả/exit code; hoàn tác, PERF-LOG, trần ba lần không cải thiện cùng điểm nóng và ratchet vẫn do agent theo skill (`.claude/skills/optimize/SKILL.md:25`). Lỗi benchmark khác nhau có thể có chữ ký khác, nên không thể lấy bộ đếm lỗi chung thay bộ đếm lần thử theo điểm nóng.

Đề nghị quản lý một candidate tuần tự: ghi giả thuyết/falsifier trước, ghim SHA/bộ đo, chạy equivalence + primary/secondary metrics, giữ hoặc thu hồi đúng diff của candidate, lưu cả lần thất bại. Dùng vùng thử thuộc sở hữu lần thử nếu cần; đây không phải cho nhiều lát chạy song song bằng worktree. Không hoàn tác bằng lệnh xóa sạch cây có sửa của người dùng.

**Nghiệm thu:** neutral/regressed/insufficient không để sót sửa thử; timeout/crash vẫn khôi phục và ghi kết quả chưa hoàn tất; resume không thử trùng candidate; ba lần không improved cùng điểm nóng được tính bền qua restart; đạt budget thì dừng. Chỉ siết ratchet sau khi giữ, không thay bộ đo/ngưỡng để xanh. Nếu guard chặn một cách thu hồi thì dừng/defer, không tìm tool khác để lách.

### G. Tách “lab đạt” khỏi “field xác nhận”; kích hoạt theo số thật khi đủ điều kiện

Trạng thái kết quả nên phân biệt `lab_improved` → chờ triển khai có phép → `awaiting_field` → `field_met` hoặc việc tiếp theo. Đã nhanh trong lab chưa phải người dùng thật đã được cải thiện. File field phải cùng chỉ số/đơn vị/phân vị/phân khúc/cửa sổ có thể so; không suy p95 toàn site từ benchmark một route.

**Chưa đề nghị viết field engine ngay.** ADR-0048 đã xét và hoãn máy kiểm FIELD đến khi có SLO 7 ngày thật. Khi dự án đích có dữ liệu, job tất định do chủ dự án cấu hình xuất aggregate không chứa dữ liệu người dùng; máy kiểm schema, nguồn, tuổi ≤ 30 ngày, window, threshold, dedupe và cooldown rồi sinh việc. Agent tối ưu không nhận khóa production. Lịch xuất tự động và cooldown cần lấy từ SLO thật, không chọn tùy ý trong báo cáo này.

**Nghiệm thu sau pilot:** file cũ/thiếu nguồn/khác phân khúc không kích hoạt hoặc nghiệm thu; chỉ số vẫn vượt budget sau triển khai thì không khai field đã đạt; một sự kiện không sinh nhiều PLAN. Bộ parser nhỏ vẫn có thể làm sau khi đã có file thật để kiểm, không xây collector/dashboard mới.

## 7. Delivery và phản hồi: chặng sau có điều kiện

Steward hiện tự merge/cập nhật một số trường hợp, nhưng `review/fix/retarget` còn là bước báo cáo (`scripts/xt.py:9197`). Có thể nâng bằng worker được cấp phạm vi hẹp, gọi theo `pr next`, dùng lại ngân sách triage; chỉ đáng làm khi đo cho thấy PR thường treo vì phiên đóng. Runner ngoài phiên cần ADR mới đối chiếu ADR-0009, chi phí inference, danh tính reviewer và quyền chủ repo cấu hình.

Trước khi bật workflow reviewer, cần sửa/kiểm bộ lọc: `.github/workflows/pr-review.yml:36` hiện chỉ xét enabled/draft/fork, chưa thấy điều kiện làn chuẩn/harden hoặc `pr next=review` trước bước gọi model. Đây là nhận định từ đọc cấu hình, **chưa chạy trên GitHub**. Không bật nguyên trạng rồi vô tình review LLM mọi PR, trái D-142.

Vòng nâng khung ở dự án đích nên dùng installer/manifest đã có: pin release SHA → `--plan` → một PR nâng bản → doctor/drift/Gate → steward của chính dự án quyết. Theo dõi PR đang mở trước khi tạo mới; custom/conflict/quyền thêm phải hiện rõ. Feedback đủ ngưỡng chỉ sinh một repro/task; lỗi đã sửa nhưng đích chưa nâng thì gắn PR nâng, không mở lại cùng lỗi. Công khai raw feedback vẫn theo quyền duyệt hiện hành; không coi redact là đủ.

## 8. Thứ tự triển khai và phép đo nghiệm thu

Các nhóm dưới là **lát dự kiến**, không phải PLAN đã tự động bắt đầu; số PR phụ thuộc diff và review thực tế.

| Thứ tự | Phạm vi | Điều kiện ra khỏi nhóm |
|---|---|---|
| 0 | Tận dụng T-3532/T-3533 đã hoàn tất trên main; bổ sung eval luồng và đo runtime thật | Không làm lại spike mutation hoặc nhận công là tính năng mới; kiểm tool → hook thật bằng sentinel vô hại; có đối chứng hợp lệ |
| 1 | Nối phiên an toàn; tính hợp lệ metadata perf và ghim base | Hai tái hiện §2 được kiểm bằng regression test + ca hợp lệ; không nới policy |
| 2 | Bộ bước kế chạy chỉ đọc cho autopilot và complete; sinh việc/gói nghiệm thu nháp | Replay cùng dữ liệu cùng action; nhận đủ trạng thái chờ người, audit, review và PR |
| 3 | Quản lý một lần thử optimize + sổ thử bền + thu hồi có phạm vi | Crash/timeout không mất sửa người dùng, không giữ candidate không đạt, không thử lại vô hạn |
| 4 | Pilot phiên thực rồi mới cho bộ bước kế ghi/chuyển trạng thái | Có dữ liệu trước/sau, giảm can thiệp mà không tăng false-done, lỗi sau merge hoặc chi phí quá mục tiêu |
| 5 | Field trigger, bot nâng bản, worker ngoài phiên | Có SLO/dữ liệu/quyền phù hợp và lợi ích đo được; ADR nếu đổi kiến trúc/chính sách |

**Corpus luồng cần thêm**, bổ sung cho 518 ca trên main mới: crash trước/sau record, đổi session, lỗi A/B luân phiên, done nhưng PR chờ, head đổi sau review, event trùng, audit cũ, PLAN đổi, FIELD cũ, unit sai, neutral/noisy, secondary budget đỏ, crash trước hoàn tác, và GO máy đạt nhưng người chưa ký. Tình huống mô phỏng không được gắn nhãn đã chứng minh trên GitHub/production thật.

Đo trên chính khung và ít nhất hai dự án đích: tỷ lệ mục tiêu tự kết thúc, số can thiệp theo nguyên nhân, P50/P95 thời gian task/CI/review/chờ quyền, số lần replan, thời gian tới gói chờ ký, tỷ lệ candidate giữ/thu hồi, lab→field, lỗi/revert sau merge và chi phí khi có nguồn. Khóa nối dữ liệu là `(repo, objective/loop, task, PR, head)`, không chỉ `T-001`. Báo rõ mẫu số gồm failed/deferred; thiếu dữ liệu là null.

Ngưỡng ≥10 task/nhóm × ≥2 vòng của LOOP-ORCH-020 là tối thiểu hiện có khi đổi mặc định giao việc, không đủ để tự khẳng định an toàn hoặc chứng minh hiệu quả field. Chỉ đặt mục tiêu giảm bao nhiêu % sau baseline. Chạy chế độ chỉ gợi ý trước, so action với quyết định thật rồi mới bật ghi.

Mỗi lát runtime giữ C901, strict types, coverage và cổng hiện hành. Theo ADR-0050, nhóm thư mục hiện có thêm chỗ, không cần bù từng byte; vẫn phải chọn cách gọn và bảo trì được, không chuyển mã qua thư mục ngoài bộ đếm hoặc tăng trần để qua. Trần từng file hướng dẫn không đổi: skill cần gỡ/gộp chữ thay vì nối dài. Chưa có lý do mặc định cần 4.x.

## 9. Nguồn sống xác minh ngày 2026-10-26

Đọc trực tiếp nguồn chính thức trên GitHub qua mạng được cho phép. SHA ghim dưới đây giữ nội dung có thể kiểm lại; hash bản tải ở [source-downloads.json](evidence/2026-10-26-three-loops/source-downloads.json). Chỉ dùng nguyên lý, không cài thêm các framework bên ngoài.

| Nguồn | Dữ kiện dùng | Điều nguồn không chứng minh |
|---|---|---|
| [Runtime CHANGELOG](https://github.com/anthropics/claude-code/blob/2eff7a8d21c80be48904f62ebdea36d945d7b504/CHANGELOG.md) | Có sửa resume chạy lại agent đã xong, retry read-only/idempotent, `onFailure:block`; `--bare` bỏ hook | Bản mới không mặc nhiên tăng hiệu quả hoặc giữ tương thích mọi hook của khung |
| [GitHub workflow events](https://github.com/github/docs/blob/02c25d16369fe27f9bdb28d1201f6b452f0d21dd/content/actions/reference/workflows-and-actions/events-that-trigger-workflows.md) | Schedule chỉ default branch, public không hoạt động 60 ngày có thể tắt; workflow_run không đồng nghĩa workflow trước thành công | Cron không phải bảo đảm tiến độ hay quyền chạy lại |
| [GitHub secure use](https://github.com/github/docs/blob/02c25d16369fe27f9bdb28d1201f6b452f0d21dd/content/actions/reference/security/secure-use.md) | Token tối thiểu; workflow_run đặc quyền không checkout PR không tin cậy; artifact cũng là dữ liệu không tin cậy | Không xác minh quyền/ruleset sống của các repo đích |
| [Persistence](https://github.com/langchain-ai/docs/blob/1f44f7efcc914cbd493dc2ccc1d850a4d0a01ca2/src/oss/langgraph/persistence.mdx) | Checkpoint theo định danh, lưu bền và retention; lưu trong RAM mất khi restart | Không phải lý do đưa LangGraph/DB mới vào khung stdlib |
| [autoresearch](https://github.com/karpathy/autoresearch/blob/228791fb499afffb54b46200aca536f79142f117/README.md) | Bộ đo cố định, metric/ngân sách định trước, giữ/bỏ từng thử; không so điểm giữa máy khác nhau | Không chứng minh speedup trên X-Templates hay cho phép tối ưu đổi hành vi |
| [Go benchstat](https://github.com/golang/perf/blob/be2c69fb417e05de5fec05c732911f4c5f172606/cmd/benchstat/main.go#L363) | Kiểm noise, đo xen kẽ, định trước số lần; không rerun đến khi significant; ý nghĩa thống kê khác ý nghĩa thực tế | Không áp ngưỡng mẫu của Go thành MUST chung cho mọi hồ sơ |

Nguồn nội bộ: [nghiên cứu trần 2026-10-23](2026-10-23-ceiling-analysis.md), [ADR-0043](../docs/adr/0043-size-budget.md), [ADR-0045](../docs/adr/0045-split-by-context-measure-before-fold.md), [ADR-0047](../docs/adr/0047-build-loop-until-audit-clean.md), [ADR-0048](../docs/adr/0048-optimize-skill-and-field-loop.md), [PLAN harden hiện có](../docs/autopilot/PLAN-harden-2026-10-26d.md), code/skill được dẫn ở các mục trên. Báo cáo này bổ sung các khoảng trống trên mốc mới, không thay sổ audit hoặc tự đóng nợ cũ.

## 10. Chưa xác minh và giới hạn

Chưa đọc trạng thái quyền/token/App/ruleset/PR sống của các dự án đích trong phiên này; snapshot TARGETS/PROGRESS không phải trạng thái hôm nay. Chưa chạy pilot ba vòng trên task thật, chưa đo token/chi phí, mức giảm can thiệp hay hiệu quả production. Chưa xác minh độc lập nội dung nghiên cứu ngoài cũ nếu không nằm trong sáu nguồn sống ở §9.

Không có cơ sở hứa “tự động 100%”, “nhanh gấp X” hoặc bỏ nghiệm thu spec/UX/bảo mật của người dùng. Mức tự chủ có thể nâng ngay là **tự chuẩn bị đầy đủ, tiếp tục đúng chỗ và dừng với gói chờ quyết cụ thể**; vận hành lúc không có phiên và tự kích hoạt từ production là chặng riêng cần dữ liệu và cấu hình quyền phù hợp.
