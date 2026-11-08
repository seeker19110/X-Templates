# Pilot xác minh artifact xboss · 2026-11-08

**Pilot đạt** trên commit xboss `ab7389aa9901d329cd7f1081311e498c3c4ba5ed`. Hai lượt GitHub Actions tách biệt build và staging, tải theo ID artifact, kiểm SHA-256 archive trước giải nén rồi xác minh cây đã cài và app Next đang phục vụ. Hai biên nhận `verified` đã được tải và đối chiếu độc lập với metadata của từng run.

| Run | Trigger | Giờ Việt Nam | SHA-256 archive đã đối chiếu | Build ID quan sát | Probe HTTP đạt |
| --- | ------- | ------------ | --------------------------- | ----------------- | -------------- |
| [42436743483](https://github.com/seeker19110/xboss/actions/runs/42436743483) | `push` | 09:05:08 | `733adeb7a3985ecde3d842fecb592a1c588ce56496df3a76bf10978ce7548b18` | `lklL1GSSR2WD9sJiNCaXD` | 4/4 |
| [42436772427](https://github.com/seeker19110/xboss/actions/runs/42436772427) | `pull_request` | 09:05:13 | `389ae789981972330a2368ef6cae37fbe813e3265471ee5c117b356fd124b7bf` | `_E79LxoJV4pqRyo8-G8eI` | 4/4 |

Cả hai lượt cùng scope `staging-isolated`, dùng PostgreSQL dùng một lần và địa chỉ loopback. Mỗi biên nhận khớp SHA nguồn, run ID/attempt, digest archive, digest manifest và Build ID. Marker cố định, asset Next thật, health và readiness đều trả HTTP 200. Production tiếp tục dùng cổng duyệt hiện hành.

## Kiểm đối kháng và hồi quy

- `node --test tests/artifact-pilot.test.ts` exit 0, 9 test. Có ca archive bị sửa, SHA sai, symlink thoát phạm vi, cây cài đổi, marker bản cũ, asset sai, readiness lỗi, redirect và timeout.
- [Run đầu](https://github.com/seeker19110/xboss/actions/runs/42436408338) dừng trước staging vì build thật có symlink dependencies. Bản sửa ghi và kiểm đích symlink tương đối trong manifest. Hai run cuối đều chạy qua bước cài, xác minh runtime và upload biên nhận.
- Bản build Next chạy cục bộ từ archive, trên DB dùng một lần sau migration, cũng trả `verified`. Đây là lần kiểm bổ sung, tách khỏi hai biên nhận CI.
- [PR xboss #719](https://github.com/seeker19110/xboss/pull/719) là nhánh pilot. So diff với main xác nhận workflow VPS, release, `deploy.sh` và GO-NO-GO giữ nguyên. GitHub không ghi deployment Preview hoặc Production cho SHA pilot.
- PR X-Templates #474 gia cố cổng release riêng. 67 test trên Python 3.14 và 38 test mục tiêu trên Python 3.11 exit 0. Dòng và nhánh thay đổi đều được đo coverage. Cả hai job GitHub Actions `quality` và `coverage` đều đạt. Bản vá ở checkout gốc được giữ nguyên. [PR #474](https://github.com/seeker19110/X-Templates/pull/474) · [Run 42436533849](https://github.com/seeker19110/X-Templates/actions/runs/42436533849)

## Xác minh lại sau khi gia cố PR

Trên commit pilot ban đầu, CI chung báo lệch định dạng đặc tả và kiểm kê route tự sinh. CodeQL nêu một khoảng đua giữa kiểm tra và đọc manifest cùng một lời gọi handler theo khóa HTTP trong fixture. Bản sửa đọc và kiểm loại manifest trên cùng file descriptor với `O_NOFOLLOW`, dùng `Map.get` cho fixture và sinh lại kiểm kê theo `main` đã cập nhật. [CI ban đầu](https://github.com/seeker19110/xboss/actions/runs/42436772424) · [Bản sửa](https://github.com/seeker19110/xboss/commit/7e149760)

Commit `c64020edc1ae9c3049273d33b962d5df9804885f` đạt thêm hai lượt độc lập. Cả hai biên nhận `verified` khớp SHA nguồn, run/attempt, digest archive, digest manifest, Build ID và đủ bốn probe HTTP 200.

| Run | Trigger | Giờ Việt Nam | SHA-256 archive đã đối chiếu | Build ID quan sát | Probe HTTP đạt |
| --- | ------- | ------------ | --------------------------- | ----------------- | -------------- |
| [42438366638](https://github.com/seeker19110/xboss/actions/runs/42438366638) | `push` | 09:26:21 | `3bab7126315b5209e59349f2ccaf580b44da767f07d61d31dd8bdc281ad8ad8c` | `Ym9AqRS7ArSR9TzrjlPQT` | 4/4 |
| [42438370093](https://github.com/seeker19110/xboss/actions/runs/42438370093) | `pull_request` | 09:26:34 | `254d6c413f97e319d12d0e86f836b21e131e370ade2d2272e6f186fcf13625dd` | `EeH125OO2XUtf50UQ3YYC` | 4/4 |

Workflow duyệt và triển khai production tiếp tục theo cấu hình trên `main`. [CI chung](https://github.com/seeker19110/xboss/actions/runs/42438370125) · [CodeQL](https://github.com/seeker19110/xboss/actions/runs/42438370186)

## Diễn tập sau khi pilot đạt

Hai diễn tập dùng commit đã đạt pilot ban đầu `ab7389aa9901d329cd7f1081311e498c3c4ba5ed`.

### Rollback ứng dụng

Hai archive CI của lượt pilot ban đầu được tải và cài riêng, kiểm digest archive, manifest và Build ID với biên nhận gốc. A dùng run `42436743483`, B dùng run `42436772427`. Cả hai chạy Next trên cùng PostgreSQL giả đã migrate. Tuyến loopback phục vụ A rồi B và verifier xác nhận đủ bốn probe ở cả hai lượt.

Dừng B khiến readiness qua tuyến chung trả HTTP 502. Chuyển lại A đang chạy sẵn khôi phục HTTP 200 sau 0,022 giây và trả `verified` sau 1,437 giây. Digest, Build ID và cả bốn probe của A khớp lượt trước khi chuyển. Lượt tải đầu hết hạn ở 120 giây. Lượt tải lại hoàn tất và đo thời gian kể từ lúc dừng B, sau khi cả hai bản đã sẵn sàng. Hai archive khác nhau cùng SHA nguồn, nên tương thích schema giữa các commit và rollback trên VPS là phép kiểm riêng.

### Restore PostgreSQL

Lượt đầu dừng vì policy `offline_device_maint_read` tham chiếu `xboss_vault_maint`, trong khi `pg_dump` không mang theo role cấp cluster. Lượt tiếp theo tạo role `NOLOGIN NOSUPERUSER NOBYPASSRLS` trên đích cô lập mới trước khi restore. [Migration chứa policy](https://github.com/seeker19110/xboss/blob/ab7389aa9901d329cd7f1081311e498c3c4ba5ed/migrations/0170_offline_vault_bao_tri.sql)

Lượt sau đạt trên hai container PostgreSQL 16 dùng một lần. SHA-256 dump là `9db23d0ab67b6979a3578c9cd049c95cd98dbe8354ef80457ebfb466ea3776c5`. Danh sách 176 migration khớp. Dòng mốc trước backup được phục hồi, dòng ghi sau backup chỉ còn ở nguồn và role `NOBYPASSRLS` chỉ thấy dữ liệu tenant được cấp. App dùng role đọc riêng trả `/api/ready` HTTP 200 với schema `ok`.

`pg_restore` mất 9,145 giây, từ bắt đầu restore đến khi app sẵn sàng mất 11,165 giây. Mốc ghi được khôi phục cách thời điểm sự cố giả 0,480 giây, với một dòng giả nằm ngoài backup. Phép đo bắt đầu sau khi đã dựng đích và tạo role. Diễn tập gọi `pg_dump` và `pg_restore` trực tiếp. Luồng `restore-check.sh`, recovery set có uploads, PITR và RTO/RPO vận hành cần phép kiểm riêng. [Runbook backup và restore](https://github.com/seeker19110/xboss/blob/ab7389aa9901d329cd7f1081311e498c3c4ba5ed/docs/ops/backup.md)

## Phạm vi phép đo

Bốn lượt xác nhận bốn bước nhóm deploy trong PLAN trên staging cô lập. Mốc 90% của cả vòng đời cần đo qua các chu kỳ thật như đã định trong PLAN. Pilot dùng artifact cùng workflow run và SHA-256 metadata nối giữa hai job. Việc ký provenance và kiểm trên môi trường deploy bền là mốc riêng.

PLAN tại [đây](../autopilot/PLAN-harden-2026-11-08-artifact-pilot.md). Quyết định D-398 ghi trong [sổ quyết định](../autopilot/DECISIONS.md).
