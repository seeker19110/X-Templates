# ADR-0067: Guard là lớp phân tích tĩnh có giới hạn — lớp lách bằng tên/mã dựng lúc chạy chấp nhận có hạn, ranh giới cứng ở lớp ngoài

- **Trạng thái:** Đã chấp nhận 2026-11-03 (phiên chính tự duyệt theo tiêu chí chất lượng cuối, ADR-0008 — **D-331**).
- **Trạng thái triển khai:** đã làm (sổ + tài liệu, PR kế sau #427); việc đánh giá sandbox mở ở `PROGRESS.md` *Tiếp theo*.
- **Ngày:** 2026-11-03.
- **Giữ:** ADR-0002 (fail-closed hành động nguy hiểm), ADR-0063/0065/0066 (guard chỉ cho chạy tập con đọc chắc; danh
  sách trắng mở rộng động; tệp tự ghi theo tên nhắc lại) — mọi luật hiện có giữ nguyên, không nới.
- **Liên quan:** ADR-0018/0019 (guard không hỏi người), ADR-0061 (`max_rethink`), ADR-0064 (sandbox kiểm bằng `doctor`),
  D-322, D-326, D-329; mốc xét lại hàng rào 2027-01-21 (`LOOP-DESIGN-014`).

## Bối cảnh

Từ #420 tới #427 (2026-11-02…03), mỗi lượt review đối kháng guard (bash 5.2.21 + stub `git`, chạy thật) đều tìm thêm dạng
lách cùng một lớp: lệnh dựng TÊN hoặc MÃ lúc chạy mà phân tích tĩnh không giải được, rồi chạy nó — tách từ theo `IFS`
(AUD-SEC-388), mảng/tham số vị trí từ dữ liệu (399/405), ghi tệp rồi chạy (400/404/406), tên mô-đun dựng lúc chạy
(`python3 -m "${y:-x}"`, `__import__("X".lower())`), tên tệp nạp ngầm (`> Makefile; make`, `> conftest.py; pytest`,
`> ~/.bashrc; bash -ic`), đổi `HOME`/`CDPATH` trước `cd` (AUD-SEC-414). Ba lần vá cũng tự mở lỗ mới (hồi quy #426/#427,
D-326/D-329). Sổ còn hai 🔴 `mở` của lớp này (AUD-SEC-406 phần tên dựng/ngầm, AUD-SEC-414) — `audit check --strict` đỏ
nên không cắt được bản nào, dù mọi dạng NGUYÊN VĂN đã chặn.

Lớp ngoài hiện có (đọc 2026-11-03): ruleset GitHub của repo bật `non_fast_forward` + `deletion` + `pull_request` cho nhánh
chính (`.github/rulesets/main.json`, Kiểm BASE-REPO-008/013) — force-push/xoá nhánh chính bị máy chủ từ chối dù guard bị
lách; CI là cổng đầy đủ, merge ghim head sau review (ADR-0036/0062); phiên cloud chạy trong container tạm. Sandbox Bash
của Claude Code (<https://code.claude.com/docs/en/sandboxing>, đọc 2026-11-03): mặc định TẮT, giới hạn ghi trong thư mục
làm việc + temp, mạng qua proxy theo `allowedDomains`; Linux cần bubblewrap + socat; không khởi động được thì mặc định
chạy KHÔNG sandbox (trừ `sandbox.failIfUnavailable`); không che công cụ ghi tệp/hook/MCP.

## Yếu tố quyết định

- (1) đúng và an toàn: không khai "đóng" khi còn lọt; không nới luật nào đang chặn.
- (2) đường lùi: quyết định chỉ đổi trạng thái sổ, đảo được bằng một dòng.
- (3) bền: dừng vòng vá vô hạn (bài học #372, ADR-0061) — phân tích tĩnh của shell không đầy đủ được theo nguyên lý
  (tên/mã dựng lúc chạy là tính toán tuỳ ý).

## Các phương án đã cân nhắc

1. **Vá tiếp từng dạng** — mỗi lượt lộ dạng mới và hồi quy; không điểm dừng; trái (3), và (1) vì hồi quy.
2. **Chặn mọi mở rộng không nháy/mọi tệp ghi trong lệnh có chạy mã** — chặn oan ước > 20 % lệnh thật (số đo #426/#427:
   6 % chỉ với luật hẹp hơn), agent phải tách mọi lệnh; trái (4) nặng, không đóng được tên ngầm.
3. **Bật sandbox bắt buộc trong `.claude/settings.json` của khung** — container cloud có thể thiếu bubblewrap (rơi về
   không sandbox), `allowedDomains` rỗng làm hỏng pip/gh/curl; không chặn force-push (mạng tới GitHub là việc thường).
   Cần đánh giá riêng, chưa áp được ngay.
4. **Chấp nhận có hạn lớp "lách bằng tên/mã dựng lúc chạy"** (chọn): ghi rõ giới hạn, dựa ranh giới cứng ở lớp ngoài,
   hạn = mốc xét lại hàng rào, kèm việc đánh giá sandbox opt-in.

## Quyết định

Chọn **4**. Guard là lớp phân tích tĩnh **chặn dạng nguyên văn và dạng thường gặp** (kể cả vô ý); nó **không** là ranh
giới chống agent cố ý làm rối lệnh. Phát hiện thuộc đúng lớp "tên hoặc mã dựng lúc chạy rồi chạy" mà mọi dạng nguyên văn
của nó đã chặn được ghi `chấp nhận` (giữ mức gốc, `chủ:` phiên chính, `hạn:` 2027-01-21, lý do trỏ ADR này), không ghi
`đã sửa`. Không áp cho: hồi quy (head cho qua mà base chặn), lỗ do miễn trừ mới, hay dạng nguyên văn — các loại đó vẫn là
🔴 phải sửa trong PR (ADR-0062).

## Hệ quả

- AUD-SEC-406 (phần tên dựng/ngầm) và AUD-SEC-414 → `chấp nhận` (D-331); hai 🟢 chặn oan AUD-SEC-410/413 → `chấp nhận`
  cùng hạn (sửa cần miễn theo giá trị đã chứng minh — vòng sau). `audit check --strict` xanh trở lại.
- Mức an toàn thực tế của dự án đích phụ thuộc lớp ngoài: ruleset nhánh chính (đã có trong mẫu `install.py`), CI là cổng
  đầy đủ, review trước merge; máy dev cá nhân nên bật sandbox (`/sandbox`) — ghi vào `PROGRESS.md` *Tiếp theo*: đánh giá
  sandbox opt-in cho khung (`doctor` cảnh báo khi tắt, ADR-0064) trước 2027-01-21.
- Hết hạn 2027-01-21 mà chưa có sandbox/lớp mới → `audit check` đỏ lại (chấp nhận quá hạn) — buộc xét lại.
- Đường lùi: đổi các dòng về `mở`.
