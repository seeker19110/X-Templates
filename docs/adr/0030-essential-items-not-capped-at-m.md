# ADR-0030: Ngữ nghĩa chọn mục theo quy mô — mục thiết yếu không bị trần MUST ở M khi fact bật

- **Trạng thái:** Đã chấp nhận
- **Trạng thái triển khai:** Đã triển khai — `scripts/xt.py` `FEATURE_FACTS`, `MAX_ESSENTIAL`, `_check_essential`,
  `essential_ids`, `effective_level(..., essential)`, `essential_promoted`, `compose --feature`; thí điểm
  `framework/08-backend/authn-authz.md` (`BE-AUTH-003/006/008/015`); test `tests/test_xt.py::EssentialNotCappedTest`.
- **Ngày:** 2026-10-20
- **Làm rõ:** ADR-0003 (S chỉ sàn), ADR-0004 (trần 4 MUST/module ở M), ADR-0012 (BLUEPRINT chỉ MUST theo quy mô).
  Nguồn việc: REC-05 trong `docs/ops/REMEDIATION-PLAN-2026-10-19.md`.

## Bối cảnh

Mức hiệu lực của một mục hôm nay chỉ phụ thuộc **(mức gốc, ngưỡng `@S/@M/@L`, `kind` của file, quy mô)**:

| Quy mô | `baseline`/`profile`/`industry` | `module`/`standard` |
|---|---|---|
| S | MUST trơn → MUST; `MUST@M/@L` → SHOULD | mọi MUST → SHOULD (ADR-0003) |
| M | MUST trơn, `MUST@M` → MUST; `MUST@L` → SHOULD | như cột trái, và `validate` giữ ≤ 4 MUST/file (ADR-0004) |
| L | mọi MUST → MUST | mọi MUST → MUST |

Trần ADR-0004 buộc module rộng chọn 4 mục; phần còn lại thành `MUST@L`. Với `08-backend/authn-authz.md`, bốn mục giữ
là băm mật khẩu, phiên, kiểm quyền endpoint, IDOR (`BE-AUTH-001/004/009/010`). Hệ quả: dự án M **có đăng nhập** nhận
khoá theo tài khoản và phản hồi chung (`BE-AUTH-003`), kiểm JWT (`BE-AUTH-006`, RFC 8725 §3.1/§3.9), OAuth chỉ
Authorization Code + PKCE (`BE-AUTH-008`, RFC 9700) và token quên mật khẩu dùng một lần (`BE-AUTH-015`, OWASP Forgot
Password Cheat Sheet) ở mức SHOULD — bỏ được chỉ bằng một dòng lý do. Đó là những lỗ hổng chiếm tài khoản trực tiếp
khi tính năng **có mặt**; còn khi tính năng vắng mặt (không JWT, không OAuth) thì mục đó vô nghĩa. Trần theo file không
phân biệt hai trường hợp, vì khung không biết dự án dùng gì.

Số đo trước thay đổi (`compose --profile web-app`, 2026-10-20): MUST S 70 · M 473 · L 1.146.

## Quyết định

1. **Fact tính năng**: tập đóng `FEATURE_FACTS = auth, jwt, oauth, reset, payment, pii`. Dự án khai bằng
   `xt.py compose --feature <fact>` (lặp được); blueprint ghi `features: [...]` ở frontmatter và một dòng `> Feature:`
   ở đầu trang — chỉ khi có fact, nên blueprint ghép không `--feature` giữ nguyên từng byte.
2. **Mục thiết yếu**: module/chuẩn khai ở frontmatter `essential: [<ID>@<fact>, …]` (frontmatter của khung là YAML
   phẳng nên không có `essential: true` theo từng mục; một ID có thể khai với nhiều fact — bật fact nào cũng đủ).
   `validate` chặn: dùng ở `baseline`/`profile`/`industry` (sàn không bị trần, không cần), sai dạng, fact ngoài tập,
   ID không thuộc file, mục không phải `MUST@L`, quá `MAX_ESSENTIAL = 4` ID mỗi file.
3. **Ngữ nghĩa chọn**: mục thiết yếu có ít nhất một fact bật là **MUST ở quy mô M** dù ghi `MUST@L`. S không đổi
   (ADR-0003: S chỉ sàn); L đã là MUST. Không fact → mọi quy mô như trước. Quy mô vẫn quyết định độ sâu bằng chứng
   (phần `→ Kiểm:` của mục), fact chỉ quyết mục có thuộc "thiếu là chưa đạt" hay không.
4. **Trần ADR-0004 đếm mức không fact**: `essential` không làm file vượt trần trong `validate`, nhưng ở blueprint M
   một module có thể có tới `4 + MAX_ESSENTIAL` MUST — chỉ khi dự án tự khai tính năng tương ứng.
5. **Báo cáo diff**: `compose` in stderr các ID được đưa lên MUST (`↑ N mục thiết yếu…`); fact bật ở S/L mà không đổi
   mục nào thì in `ℹ`. Ghép lại phải truyền lại đúng `--feature` — trạng thái mục giữ theo ID như ADR-0012.
6. **Thí điểm** chỉ `08-backend/authn-authz.md`: `BE-AUTH-003@auth`, `BE-AUTH-006@jwt`, `BE-AUTH-008@oauth`,
   `BE-AUTH-015@reset`. `payment`/`pii` có trong tập fact nhưng chưa module nào khai — mở rộng là thay đổi riêng, mỗi
   mục ghi CHANGELOG theo ID.

## Lý do

- Đúng và an toàn (tiêu chí 1, AGENTS.md §4): mục chống chiếm tài khoản trở lại MUST đúng lúc lỗ hổng có thể xảy ra,
  không thêm gánh cho dự án không có tính năng đó.
- Đường lùi: không fact → không đổi gì; bỏ một ID khỏi `essential` → về hành vi cũ; mức gốc và ID không đổi.
- Kiểm được bằng máy: tập fact đóng, ràng buộc `MUST@L`, trần `MAX_ESSENTIAL` — tác giả không lách trần đại trà bằng
  cách đánh dấu cả module.
- Fact do dự án khai (cờ CLI) thay vì đoán từ code: `compose` chạy ở G1–G2 khi chưa có code; dò stack sai làm
  blueprint đổi im lặng giữa hai lần ghép.

## Các phương án đã cân nhắc

- **Nâng trần lên 6–8 MUST/module:** mọi dự án M đều gánh thêm, kể cả không có tính năng; ADR-0004 đã đo 6 vẫn để
  ~660 MUST. Loại.
- **Chuyển bốn mục sang MUST trơn, hạ mục khác xuống `MUST@L`:** mục JWT/OAuth vô nghĩa với dự án không dùng chúng,
  và mục bị hạ (phiên, IDOR) đều thiết yếu hơn với số đông. Loại.
- **Module riêng theo tính năng (`authn-jwt.md`, `authn-oauth.md`) ghép bằng `--add`:** đúng hơn về cấu trúc nhưng đổi
  nhà của ID (`BE-AUTH-*` phải đổi prefix hoặc tách file giữ prefix trùng — `validate` cấm prefix trùng), vỡ trạng thái
  blueprint đã có. Để sau nếu thí điểm cho thấy cần.
- **Đọc fact từ `features:` của blueprint cũ khi ghép lại:** tiện nhưng là trạng thái ngầm; lệnh ghép không còn tự mô
  tả. Loại — lệnh ghép mang đủ cờ.

## Hệ quả

- Tốt: dự án M có đăng nhập/JWT/OAuth/quên mật khẩu nhận đúng MUST chống chiếm tài khoản; blueprint không fact, mọi
  hồ sơ, mọi quy mô không đổi một byte (đo lại 2026-10-20: `web-app` M 473 → 474 với `auth`, 477 với cả bốn fact;
  S 70 và L 1.146 không đổi).
- Xấu: thêm một khái niệm (fact) mà người ghép phải nhớ truyền lại; quên thì bốn mục về SHOULD — `compose` không cảnh
  báo việc thiếu cờ so với lần trước (giữ lệnh tự mô tả — phương án cuối ở trên).
- Theo dõi: ứng viên khai `payment`/`pii` (thanh toán, dữ liệu cá nhân) khi audit dự án thật cho thấy mục `MUST@L`
  tương ứng hay bị bỏ; `conventions.md` cần ghi khoá frontmatter `essential` (ngoài phạm vi thay đổi này).
