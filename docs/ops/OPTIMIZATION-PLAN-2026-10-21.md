# Kế hoạch tối ưu khung và bộ mẫu — 2026-10-21

> Cơ sở: [audit tại `ec4c7d2`](AUDIT-REPORT-2026-10-21.md). Yêu cầu: code nhanh, chạy song song tối đa hữu ích, tối thiểu job và mã, chất lượng cao. Đây là kế hoạch đề xuất; chưa thay đổi CI/công cụ và chưa chuyển pha build/harden.

Thứ tự chọn giải pháp: đúng và an toàn → thời gian hoàn tất → số job/chi phí → lượng mã cần bảo trì. Tái sử dụng entry point hiện có, giữ mã ngắn và dễ đọc, giảm số nơi phải sửa đồng bộ. Song song theo tài nguyên và quan hệ phụ thuộc.

## Phương án CI để benchmark

| Phạm vi | Hiện tại | Phương án |
|---|---|---|
| CI chính khung | 14 job sau matrix | Thử 3 job `gate`, `quality`, `protection-guard`; task độc lập song song trong `gate` |
| CI mẫu | 3 job `gate`, `e2e`, `quality` | Giữ cấu trúc; chỉ thêm shard khi đo thấy cải thiện đường chạy dài nhất |

Secret scan và workflow bảo mật khác tính riêng; 3 job ở bảng không phải tổng mọi workflow. Giữ tên các required check đang có hiệu lực, gồm `quality`, `protection-guard`, `gitleaks`, `dep-audit` của khung. Chuyển kiến trúc cần ADR và kiểm ruleset đồng bộ trước khi nhận thay đổi.

Tái sử dụng `dev-task.sh gate-par`: `typecheck ∥ lint ∥ (build → test → test_floor)`. Không thêm runner mới khi lệnh hiện có đáp ứng được; phần nào dùng chung output có phụ thuộc thì giữ thứ tự. Nhánh `build → test → test_floor` hiện vẫn tuần tự, nên phải đo nó trước khi kỳ vọng lợi ích từ gom job.

Giới hạn tổng worker theo CPU quota/RAM, tính cả song song lồng trong test. Máy đo có affinity 5 CPU nhưng quota 4 CPU. Cache theo lockfile/runtime; giữ cài dependency khóa/hash và không tái dùng bằng chứng cho HEAD khác.

## Thứ tự triển khai

1. **Bằng chứng Gate:** sửa AUD-CODE-014; regression đỏ trước/xanh sau cho quote, expansion và khử trùng lặp.
2. **Cổng nhất quán:** xử lý AUD-XFEAT-013 và sàn CI khai riêng; dùng chung outcome giữa commit/full/parallel/shard/CI/loop. Giữ đủ test và coverage, không nhận 0 test.
3. **Guard/reviewer:** sửa AUD-SEC-102; diff không đầy đủ phải inconclusive trước khi bật reviewer/harden.
4. **An toàn installer và cấu hình:** Git root, symlink, runtime và phần tài liệu quyền còn lệch theo audit.
5. **Hiệu năng/bảo trì:** benchmark phương án gom job, worker/cache và tách mô-đun dần khi có ADR. Thêm abstraction chỉ khi giảm phần lặp mà vẫn dễ truy vết.

Mỗi đợt một PR nhỏ, có Gate máy; giữ các điều kiện chất lượng theo [quy trình hiện hành](../../AGENTS.md), không hạ ngưỡng/tắt assertion để nhận tối ưu.

## Tiêu chí nhận tối ưu

- So cùng đầu vào/HEAD, runtime, CPU và trạng thái cache; tách cold/warm, giữ nguyên bộ kiểm tra và xác nhận số test/coverage trước/sau.
- Đo thời gian có kết quả, thời gian từng nhóm, runner-minutes, số job sau matrix và phần cấu hình lặp. Phân biệt cloud cục bộ với GitHub Actions.
- Chỉ nhận mục tiêu 14 → 3 khi giữ contract required check và thời gian hoàn tất đạt ngân sách đã chọn. Nếu nhánh test dài hơn ngân sách, chọn số shard nhỏ nhất đạt ngân sách.
- Giữ mypy strict, lint/format/shell/link/license, toàn bộ test, coverage dòng + nhánh 100% của khung và sàn Python 3.11. Mọi nhóm bắt buộc đỏ/cancelled/skipped phải làm cổng tổng hợp đỏ.
- Không kết luận phần trăm tăng tốc từ một mẫu hoặc khi thiếu baseline tương đương.

## Bằng chứng hiện có

`gate-par` trên Python 3.14.8: exit 0, đủ 5 task; 234 lớp/1.363 test trên 3.14 và 234 lớp/1.363 test sàn 3.11, coverage dòng/nhánh 100%. Một lượt đo cục bộ **179,53 giây**; chưa có cặp baseline đủ điều kiện để kết luận tăng tốc. Xem [receipt](evidence/audit-2026-10-21.json).

Chưa có số đo GitHub Actions cho phương án 3 job của khung; chưa triển khai phương án đó. Các phát hiện mở trong audit cần được xử lý trước khi dùng cổng hiện tại làm bảo chứng hoàn tất.
