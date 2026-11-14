# ADR-0077: Receipt ghi nhận bản đang phục vụ theo môi trường

- **Trạng thái:** Đã chấp nhận ngày 2026-11-14 theo các quyết định D-422, D-423 và D-424.
- **Trạng thái triển khai:** Chưa có mã. T-3842 đến T-3844 triển khai và kiểm bản dev, T-3860 triển khai đường production.
  [Kế hoạch xưởng đầu-cuối](../autopilot/PLAN-factory-e2e.md)
- **Đặc tả:** Khoá cấu hình, trình tự, schema receipt và các kịch bản nghiệm thu nằm trong
  [SPEC-factory-deploy](../specs/SPEC-factory-deploy.md).

## Bối cảnh

`release-check` đã nhận diện cây nguồn và artifact của ứng viên. Để nghiệm thu bản chạy, cần bằng chứng rằng đích đang
phục vụ chính ứng viên ấy sau smoke test, và biết bản nào đang chạy nếu phải quay lui. Bản dev cần dựng lại được trên
máy phát triển hoặc runner CI trước khi chủ dự án cấu hình đích production. [ADR-0075](0075-end-to-end-factory.md),
[nghiên cứu T-3866 ngày 2026-11-12](../../research/2026-11-12-dev-self-host-live-sources.md)

## Yếu tố quyết định

- Cổng đọc cùng định danh ứng viên với `release-check` và chỉ công nhận digest quan sát từ bản đang phục vụ.
- Dự án tự khai đích triển khai và giữ được bản quay lui. Gói mẫu có bản dev dùng được với toolchain sẵn có.
- Bằng chứng có cấu trúc, theo dự án và đọc được sau khi môi trường dev đã tắt.

## Các phương án đã cân nhắc

1. Receipt theo git và lệnh theo môi trường trong `xt.yaml`. Khung dùng chung định danh và cổng với luồng phát hành,
   dự án chịu trách nhiệm triển khai và thăm dò bản đang chạy.
2. Dùng log hoặc bản ghi của một dịch vụ triển khai làm bằng chứng chính. Dịch vụ có sẵn lịch sử triển khai nhưng
   đưa thêm phụ thuộc tài khoản và cần chuyển đổi dữ liệu riêng cho từng nhà cung cấp.
3. Cho `release-check` tự dựng và kiểm bản dev. Lời gọi thuận tiện hơn nhưng gây hiệu ứng ngay khi CI hoặc người dùng
   đọc kết quả nghiệm thu, làm khó việc xác định và chạy lại riêng bước lỗi.

## Quyết định

Chọn receipt schema 1 trong `docs/ops/DEPLOYS.json` và các lệnh theo môi trường khai trong `xt.yaml`. Bước triển khai
dùng lại `release_artifacts` và cách tính `subject` của `release-check`. Receipt gắn kết quả, môi trường, ứng viên,
thời điểm, lần chạy và digest quan sát từ dịch vụ. [Đặc tả §2.1–2.4 và §5](../specs/SPEC-factory-deploy.md)

Mỗi môi trường khai lệnh triển khai, smoke, đọc digest và quay lui. Chỉ cập nhật `current` thành ứng viên khi smoke
đạt và digest đọc độc lập từ đích khớp ứng viên. Nếu phải quay lui, xác nhận bản trước bằng cùng phép kiểm. Khi đã chạm
đích mà chưa xác nhận được bản đang chạy, sổ ghi trạng thái chưa biết. Với đích ngoài dev, áp dụng điều kiện quyền và
nguồn mã từ nhánh chính remote cho cả triển khai lẫn quay lui. [Đặc tả §2.3–2.4](../specs/SPEC-factory-deploy.md)

`release-check` đọc sổ. Khi dự án khai môi trường, hàng `deploy` là BLOCKER và chỉ PASS nếu receipt `dev.current`
đã triển khai có `subject.digest` và `subject.content` cùng khớp ứng viên. Dự án bật tích hợp bằng `deploy_envs`.
Loại trừ đúng đường dẫn sổ khỏi `subject.content` để có thể commit receipt của ứng viên. Registry đọc kết quả từ
cùng sổ theo hợp đồng hiện có. [Đặc tả §2.4–2.5](../specs/SPEC-factory-deploy.md)

Bản dev mặc định của gói `web-api-ts` dùng Docker Engine và Compose cho app cùng Postgres. Ảnh app dựng từ artifact
đã kiểm, điểm kiểm sức khoẻ trả digest của bản được phục vụ và workflow kiểm receipt trong cùng job triển khai.
Địa chỉ của bản dev có hiệu lực trong thời gian môi trường chạy.
[Đặc tả §2.6](../specs/SPEC-factory-deploy.md), [nghiên cứu T-3866 §1 và §3](../../research/2026-11-12-dev-self-host-live-sources.md)

## Hệ quả và xác nhận

Receipt phản ánh lần xác nhận gần nhất. Trạng thái hiện tại của đích có thể đổi sau phép kiểm, nên nghiệm thu CI dựa
vào phép thử triển khai và đọc sổ trong cùng job. T-3842 kiểm artifact lệch, digest trả về khác ứng viên và quay lui
khi smoke lỗi. T-3843 kiểm receipt cũ hoặc của bản đã quay lui, cùng trường hợp dự án chưa bật tính năng. T-3844 chạy
lát dọc của gói từ cây sạch tới bản dev có receipt. [Kịch bản nghiệm thu](../specs/SPEC-factory-deploy.md#3-tiêu-chí-chấp-nhận)
