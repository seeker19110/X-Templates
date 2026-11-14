# PLAN-harden-2026-11-08-artifact-pilot — tự động hóa tuần 1–2

> Chủ dự án duyệt ngày 2026-11-08. Pilot xác minh artifact sau deploy trên xboss staging cô lập, dữ liệu giả, dùng đúng archive CI. Production dùng cổng environment `Production` nêu ở mục Điểm dừng; phải xác minh cổng và phê duyệt đúng run trước khi triển khai. Rollback và restore mở sau mốc pilot đạt.
>
> Mốc kiểm lúc lập PLAN gồm X-Templates `50be630` và xboss `4e365442`. Quyết định kỹ thuật D-398. Cơ sở là [ADR-0068](../adr/0068-software-factory-direction.md) và [thiết kế bằng chứng](../../research/2026-11-04-software-factory-direction.md).
>
> Cú pháp mỗi task là `- [ ] T-NNNN <việc> — Gate: <lệnh>`, với ID và lệnh trong backtick.

## Phạm vi và thứ tự

1. Đưa bản sửa index vào lát độc lập trên main mới, kiểm trạng thái release khi Git lỗi hoặc index che thay đổi.
2. Pilot xboss trên job staging riêng. Build một lần từ SHA ghim, tải lại archive theo đúng run/attempt, đối chiếu SHA-256 trước cài. Tiến trình Next thật phục vụ marker cố định từ chính artifact đã cài, asset tĩnh, health và readiness.
3. Ghi biên nhận theo repo, staging, SHA nguồn, archive/manifest digest, build ID quan sát được, run/attempt/deployment ID, thời gian và probe. `verified` đòi mọi probe bắt buộc qua. `failed` và `inconclusive` đều chặn kết luận pilot đạt.
4. Dùng hai workflow run khác nhau để chốt pilot. Chạy thêm ca cũ/sai digest, đích sai, readiness lỗi và timeout. Biên nhận của staging dùng một lần không đại diện cho VPS hay Vercel.

## Mẫu số

Mốc dài hạn là ít nhất 18/20 loại bước có tự động hóa được kiểm và ít nhất 90% lượt bước đủ điều kiện đạt qua 10 chu kỳ thật ở hai repo. Năm nhóm bốn bước dùng để đo lần đầu.

| Nhóm | Bốn bước được ghi |
| ---- | ----------------- |
| Lập kế hoạch | Đọc cấu hình · xác định phạm vi · chọn gate · tính việc tiếp theo |
| Code và CI | Chọn test · build/test · ghi kết quả máy đọc · phân loại CI đỏ |
| Review và release | Ghim review vào head · kiểm điều kiện merge · build artifact · xác minh phê duyệt/digest |
| Deploy | Nhận đúng artifact · quan sát bản đang phục vụ · smoke/readiness · lưu biên nhận |
| Phục hồi | Chọn bản đã xác minh · lùi và kiểm ứng dụng · restore DB cô lập · đo và lưu bằng chứng |

Đếm bước một lần mỗi chu kỳ. Lỗi, thiếu bằng chứng và can thiệp ngoài kế hoạch tính chưa đạt. Phê duyệt production và chuyển kết nối DB thật được ghi riêng. Pilot tuần 1–2 đo nhóm deploy và thu baseline, chưa dùng để kết luận đạt 90%.

## Ngân sách

- Số vòng sửa cùng lỗi tối đa 3 · Chi phí ngoài phiên 0 đồng · Timeout Gate 1.200 giây · Hạn dự kiến 2 tuần.

## Điểm dừng

- Đích cho phép là môi trường dùng một lần với dữ liệu giả. Bằng chứng của đích thiếu hoặc có thể trỏ sang production làm dừng pilot.
- Cổng production cụ thể (đọc lại ngày 2026-11-13): job VPS của xboss gắn `environment: Production`; environment có required reviewer `seeker19110` và `can_admins_bypass: false` ([nguồn và mốc cấu hình](../ops/ARTIFACT-PILOT-2026-11-08.md#cổng-production-xác-minh-ngày-2026-11-13)). Trước mỗi lần deploy phải kiểm lại ba điều kiện và bằng chứng chủ dự án duyệt đúng deployment/run. Thiếu cổng, không đọc được cấu hình hoặc chưa có phê duyệt thì dừng production, không dựa vào approval PR hay tự duyệt thay.
- Cấu hình lịch sử lúc pilot có 0 required reviewer, nên khi đó chưa có cổng duyệt production; staging thành công không trao quyền production. Bằng chứng pilot đã đối chiếu và lưu bền mới là điều kiện mở mốc rollback/restore. Restore dữ liệu thật và chuyển kết nối là hành động có quyền riêng.

## Task

- [x] `T-3710` Chốt scope staging cô lập, contract biên nhận và danh mục đo — Gate: `python3 scripts/check-links.py`
- [x] `T-3711` Release-check chặn Git đọc lỗi và cờ index che thay đổi, giữ hợp đồng JSON cũ (files: scripts/xt.py, tests/test_release_contract.py, CHANGELOG.md) — Gate: `gh pr checks 474 -R seeker19110/X-Templates --required`
- [x] `T-3712` xboss đóng gói và kiểm archive, dùng marker/asset từ bản đang phục vụ và phát biên nhận (sau: T-3710) — Gate: `gh api 'repos/seeker19110/xboss/actions/runs?head_sha=7e831ce123bc638217770d4ee1e32692977f1eee' --jq '[.workflow_runs[] | select(.name == "Staging artifact pilot" and .conclusion == "success") | .id] | unique | length >= 2' | grep -qx true`
- [x] `T-3713` Rà hai biên nhận staging từ hai run khác nhau, kiểm ca đối kháng và ghi số liệu baseline (sau: T-3712) — Gate: `test -s docs/ops/ARTIFACT-PILOT-2026-11-08.md`

## Mốc sau

T-3713 đạt với hai biên nhận staging. [Báo cáo pilot và diễn tập](../ops/ARTIFACT-PILOT-2026-11-08.md)

Rollback và restore đã chạy tự động trên hai run staging của #719. Rollback đối chiếu digest, Build ID và probe khi đổi tuyến về bản giữ sẵn cùng SHA nguồn. Restore xác minh dữ liệu mốc, role RLS, migration và app trên đích PostgreSQL riêng. Báo cáo giữ số đo lịch sử và liên kết CI; ngày 2026-11-13 chỉ đọc được metadata, ngày 2026-11-14 đối chiếu sáu ZIP staging. Diễn tập tay thiếu log, artifact chỉ giữ 30 ngày. Trước nghiệm thu phải đối chiếu và lưu biên nhận bền theo trạng thái bằng chứng đầu báo cáo. Phạm vi đo tiếp theo của kế hoạch gồm chuyển phiên bản có thay đổi schema và mục tiêu phục hồi của môi trường vận hành.
