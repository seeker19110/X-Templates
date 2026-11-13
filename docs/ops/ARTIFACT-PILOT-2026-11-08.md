# Pilot xác minh artifact xboss · 2026-11-08

Báo cáo 2026-11-08 ghi nhận **pilot đạt** trên xboss `ab7389aa9901d329cd7f1081311e498c3c4ba5ed`: build/staging ở hai job, tải theo ID, kiểm SHA-256 trước giải nén, kiểm cây cài và Next đang phục vụ. Hai receipt `verified` được báo cáo khớp metadata run.

**Bằng chứng rà 2026-11-13:** receipt CI chưa có bản sao trong repo. Metadata hai artifact phục hồi báo hạn
2026-12-08; tải ZIP bị `Forbidden`, nên nội dung receipt và số đo CI dưới đây **(chưa tái xác minh)**. Trước nghiệm
thu/phát hành phải tải, đối chiếu và lưu bền; run xanh/metadata chưa chứng minh các trường receipt.

| Run | Trigger | Giờ Việt Nam | SHA-256 archive đã đối chiếu | Build ID quan sát | Probe HTTP đạt |
| --- | ------- | ------------ | --------------------------- | ----------------- | -------------- |
| [42436743483](https://github.com/seeker19110/xboss/actions/runs/42436743483) | `push` | 09:05:08 | `733adeb7a3985ecde3d842fecb592a1c588ce56496df3a76bf10978ce7548b18` | `lklL1GSSR2WD9sJiNCaXD` | 4/4 |
| [42436772427](https://github.com/seeker19110/xboss/actions/runs/42436772427) | `pull_request` | 09:05:13 | `389ae789981972330a2368ef6cae37fbe813e3265471ee5c117b356fd124b7bf` | `_E79LxoJV4pqRyo8-G8eI` | 4/4 |

Hai lượt dùng scope `staging-isolated`, PostgreSQL dùng một lần và loopback. Receipt được báo cáo khớp SHA nguồn, run/attempt, digest archive/manifest và Build ID; marker, asset Next, health/readiness đều HTTP 200. Cổng production ghi riêng bên dưới.

## Kiểm đối kháng và hồi quy

- `node --test tests/artifact-pilot.test.ts` exit 0, 9 test. Có ca archive bị sửa, SHA sai, symlink thoát phạm vi, cây cài đổi, marker bản cũ, asset sai, readiness lỗi, redirect và timeout.
- [Run đầu](https://github.com/seeker19110/xboss/actions/runs/42436408338) dừng vì symlink dependencies; bản sửa kiểm đích tương đối trong manifest. Hai run cuối qua cài, runtime và upload receipt.
- **(chưa xác minh)** Next cục bộ từ archive/DB dùng một lần sau migration được báo cáo `verified`; thiếu log/receipt máy đọc, không tính là bằng chứng pilot.
- [PR #719](https://github.com/seeker19110/xboss/pull/719) chỉ đổi pilot, giữ workflow VPS/release, `deploy.sh`, GO-NO-GO; báo cáo không có deployment Preview/Production cho SHA pilot.
- X-Templates #474 gia cố cổng release: báo cáo 67 test Python 3.14, 38 test Python 3.11 exit 0, coverage dòng/nhánh đổi và CI `quality`/`coverage` đạt; bản vá checkout gốc giữ nguyên. [PR #474](https://github.com/seeker19110/X-Templates/pull/474) · [Run 42436533849](https://github.com/seeker19110/X-Templates/actions/runs/42436533849)

## Xác minh lại sau khi gia cố PR

CI đầu báo lệch định dạng đặc tả/kiểm kê route. CodeQL báo race kiểm/đọc manifest và handler theo khóa HTTP. Bản sửa dùng cùng file descriptor với `O_NOFOLLOW`, sinh lại kiểm kê theo main; fixture đổi `Map.get` thành phản hồi lỗi cố định. CodeQL cuối báo thành công, 0 cảnh báo mới. [CI ban đầu](https://github.com/seeker19110/xboss/actions/runs/42436772424) · [CodeQL bản cuối](https://github.com/seeker19110/xboss/actions/runs/42438780319)

Commit cuối `7e831ce123bc638217770d4ee1e32692977f1eee` có hai lượt độc lập được báo cáo receipt `verified` khớp nguồn/run/digest/Build ID và 4 probe HTTP 200. Commit trung gian `c64020ed` cũng có hai lượt staging đạt. [Push trung gian](https://github.com/seeker19110/xboss/actions/runs/42438366638) · [PR trung gian](https://github.com/seeker19110/xboss/actions/runs/42438370093)

| Run | Trigger | Giờ Việt Nam | SHA-256 archive đã đối chiếu | Build ID quan sát | Probe HTTP đạt |
| --- | ------- | ------------ | --------------------------- | ----------------- | -------------- |
| [42438776670](https://github.com/seeker19110/xboss/actions/runs/42438776670) | `push` | 09:32:50 | `65ecc5128abbb6ad142fe4557ad42843dd37f53ad5876070caae6a3f7c348fed` | `6JB6HIM6JxgUMOBew7_M_` | 4/4 |
| [42438780299](https://github.com/seeker19110/xboss/actions/runs/42438780299) | `pull_request` | 09:32:37 | `ec602839f2d8d12fd5a56b60deaa66db634d9306c6f8445027c96cffd2d2810d` | `MUvSfOFfRNeHAg-YEXwm9` | 4/4 |

Báo cáo không có deployment Preview/Production cho SHA cuối. [CI chung bản cuối](https://github.com/seeker19110/xboss/actions/runs/42438780309)

## Diễn tập sau khi pilot đạt

Diễn tập tay dùng SHA pilot ban đầu nêu ở đầu báo cáo.

**(chưa xác minh)** Kết quả, digest và số đo hai diễn tập tay dưới đây thiếu log/receipt máy đọc; giữ để truy vết,
không tính là bằng chứng đạt hoặc RTO/RPO vận hành. Link policy/runbook không chứng minh lần chạy.

### Rollback ứng dụng

Archive A từ run `42436743483`, B từ `42436772427` được báo cáo khớp digest/manifest/Build ID gốc, chạy Next trên cùng PostgreSQL giả đã migrate; loopback lần lượt phục vụ A/B với 4 probe đạt.

Số đo được báo cáo: dừng B → readiness HTTP 502; chuyển về A chạy sẵn → HTTP 200 sau 0,022 giây, `verified` sau 1,437 giây, digest/Build ID/4 probe khớp A trước chuyển. Tải đầu timeout 120 giây; tải lại xong rồi mới đo từ lúc dừng B khi A/B sẵn sàng. Hai archive cùng SHA nguồn; tương thích schema khác commit và rollback VPS chưa được kiểm.

### Restore PostgreSQL

Lượt đầu thiếu role cluster `xboss_vault_maint` cho policy `offline_device_maint_read` (`pg_dump` không giữ role). Lượt sau tạo role `NOLOGIN NOSUPERUSER NOBYPASSRLS` ở đích cô lập trước restore. [Migration chứa policy](https://github.com/seeker19110/xboss/blob/ab7389aa9901d329cd7f1081311e498c3c4ba5ed/migrations/0170_offline_vault_bao_tri.sql)

Lượt sau được báo cáo đạt ở hai container PostgreSQL 16 dùng một lần: dump SHA-256 `9db23d0ab67b6979a3578c9cd049c95cd98dbe8354ef80457ebfb466ea3776c5`, khớp 176 migration; phục hồi mốc trước backup, mốc sau chỉ ở nguồn; `NOBYPASSRLS` thấy đúng tenant. App role đọc riêng trả `/api/ready` HTTP 200, schema `ok`.

Số đo được báo cáo: `pg_restore` 9,145 giây, restore tới app sẵn sàng 11,165 giây, mốc phục hồi cách sự cố giả 0,480 giây, một dòng ngoài backup. Đo sau dựng đích/tạo role; gọi `pg_dump`/`pg_restore` trực tiếp. Chưa kiểm `restore-check.sh`, recovery set có uploads, PITR hay RTO/RPO vận hành. [Runbook backup và restore](https://github.com/seeker19110/xboss/blob/ab7389aa9901d329cd7f1081311e498c3c4ba5ed/docs/ops/backup.md)

## Diễn tập tự động trong CI staging

CI #719 đạt trên `7e831ce1` trước bước phục hồi. Bản `5b3fbd50bd303f0466782e43810ce3b563325591` chạy rollback/restore ở hai run. Báo cáo ghi hai receipt `verified` khớp repo/môi trường/SHA/run/attempt, metadata artifact và probe. [CI trước khi mở mốc](https://github.com/seeker19110/xboss/actions/runs/42438780309) · [CodeQL bản cuối](https://github.com/seeker19110/xboss/actions/runs/42441082183)

| Run | Trigger | Rollback RTO | Restore RTO | RPO giả lập | Biên nhận CI |
| --- | ------- | -----------: | ----------: | ----------: | ------------ |
| [42441075174](https://github.com/seeker19110/xboss/actions/runs/42441075174) | `push` | 1,856 giây | 6,106 giây | 0,384 giây | [Artifact](https://github.com/seeker19110/xboss/actions/runs/42441075174/artifacts/13601718062) |
| [42441082287](https://github.com/seeker19110/xboss/actions/runs/42441082287) | `pull_request` | 1,244 giây | 5,171 giây | 0,301 giây | [Artifact](https://github.com/seeker19110/xboss/actions/runs/42441082287/artifacts/13602135106) |

Rollback về A chạy sẵn; A/B cùng SHA, khác Build ID/digest. Restore trên đích riêng kiểm role tối thiểu, 176 migration, mốc trước/sau backup, RLS hai tenant và 4 probe artifact CI. Ngưỡng staging: 60/180/60 giây; RPO tính từ commit quan sát sau ghi dữ liệu giả. Artifact chỉ giữ 30 ngày; trạng thái bằng chứng hiện tại theo đầu báo cáo.

Báo cáo pilot 2026-11-08 ghi main có 0 approval, `Production` có 0 required reviewer, VPS tự deploy khi CI main đạt: **chưa có cổng phê duyệt production**. Diễn tập chỉ ở nhánh pilot, dịch vụ/dữ liệu dùng một lần. [Workflow VPS](https://github.com/seeker19110/xboss/blob/5b3fbd50bd303f0466782e43810ce3b563325591/.github/workflows/deploy.yml)

## Cổng production xác minh ngày 2026-11-13

- [Environment Production](https://api.github.com/repos/seeker19110/xboss/environments/Production): reviewer bắt buộc
  `seeker19110`, `can_admins_bypass: false`; cổng deployment độc lập với approval PR, phải kiểm lại trước mỗi deploy.
- [Workflow trên main `35783572`](https://github.com/seeker19110/xboss/blob/35783572408fe8d82465e4e828c41518b03b0454/.github/workflows/deploy.yml)
  gắn job VPS với `environment: Production`; cần chủ dự án duyệt đúng deployment/run, không suy ra đã duyệt từ cấu hình.
- [PR #722](https://github.com/seeker19110/xboss/pull/722) còn mở; chưa xác nhận quảng bá artifact lên VPS. Receipt
  staging không chứng minh artifact/Build ID đang phục vụ trên VPS.

## Phạm vi phép đo

Sáu lượt/ba commit được báo cáo cho bốn bước deploy staging; mức bằng chứng theo đầu báo cáo. Mốc 90% cần chu kỳ thật theo PLAN. Pilot nối hai job bằng artifact cùng run và SHA-256 metadata; ký provenance và kiểm trên đích bền là mốc riêng.

PLAN tại [đây](../autopilot/PLAN-harden-2026-11-08-artifact-pilot.md). Quyết định D-398 ghi trong [sổ quyết định](../autopilot/DECISIONS.md).
