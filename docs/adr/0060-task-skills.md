# ADR-0060: Sáu skill theo tác vụ phát triển (debug, tdd, ui-verify, upgrade, migrate-db, incident)

- **Trạng thái:** Đã chấp nhận (chủ repo yêu cầu 2026-10-31: "nhiều kỹ năng xuất sắc hơn, giỏi hơn trong từng tác vụ phát triển phần
  mềm", "tự động nâng nền phần mềm ổn định nhất", "tự chủ ở mức cao nhất"; phiên chính tự duyệt thiết kế theo tiêu chí chất lượng cuối, ADR-0008)
- **Trạng thái triển khai:** Đã triển khai — `.claude/skills/{debug,tdd,ui-verify,upgrade,migrate-db,incident}/SKILL.md`; danh sách
  skill ở `AGENTS.md` §8, `CLAUDE.md`, `framework/templates/AGENTS.md`.
- **Ngày:** 2026-10-31
- **Làm rõ:** ADR-0046 (`/autopilot` build, `/complete` harden), ADR-0048 (`/optimize`), `BASE-DEP-019/020`, `QA-E2E-030`,
  `XC-DOCAI-024` (thêm ở bản Unreleased, `research/2026-10-31-stored-delta-autonomy.md`).

## Bối cảnh

Mười skill hiện có đều là **quy trình** (lập kế hoạch, vòng lặp, cổng, review, audit, bàn giao). Phần làm từng tác vụ —
gỡ lỗi, viết test, kiểm UI, nâng phụ thuộc, đổi schema, xử lý sự cố — chỉ có luật rải ở các module (`DB-MIG-*`, `OPS-IR-*`,
`QA-UNIT-*`, `BASE-DEP-*`, `FE-TEST-006`), agent phải tự ghép. Nghiên cứu 2026-10-31 (research note §3) cho thấy các bộ skill lớn
(`obra/superpowers`, `mattpocock/skills`, `claude-plugins-official`) có skill tốt cho debug/TDD/xác minh/review, nhưng **không có**
skill tốt cho migration CSDL, nâng phụ thuộc, sự cố/RCA.

## Phương án đã xét

- **A — chỉ thêm mục checklist:** không đổi hành vi agent ở lúc làm việc (luật vẫn phải tự ghép). Loại.
- **B — vendor skill của bộ ngoài** (superpowers, mattpocock): giọng và quy trình riêng xung đột với vòng của khung (`XC-DOCAI-018`),
  license/ổn định phải theo `SEC-SUPPLY-016`, và ba tác vụ khoảng trống vẫn không có. Loại.
- **C — sáu skill của khung, mỏng, trỏ về ID** (chọn): mỗi skill 28–36 dòng, không chép luật (một chủ đề một nhà), học cơ chế từ
  nguồn đã kiểm (cổng "chưa có lệnh đỏ thì chưa sửa" của debug; xem test đỏ vì đúng lý do của TDD; CLI + profile cô lập của
  playwright-cli), và lấp ba khoảng trống bằng chính luật của khung.

## Quyết định

1. Skill **tùy chọn** (không vào `DOCTOR_SKILLS`): dự án đích nhận qua `install.py` (copy-if-absent) như mọi skill; thiếu không làm
   `doctor` đỏ.
2. `/upgrade` là cách thực thi `BASE-DEP-019` (chỉ bản ổn định, theo dõi toolchain) và `BASE-DEP-020` (major tự làm khi
   `merge_autonomy: L3` + `merge_hard_exceptions: auto`); runtime, engine CSDL, thư viện auth/mật mã vẫn theo `BASE-DEP-012`.
3. Điểm dừng không đổi: `/migrate-db` và `/incident` chạm dữ liệu/tiền thật thì `loop defer` (`LOOP-STOP-005`); `/ui-verify` không
   ghi tay `.autopilot/` (guard chặn), ảnh bằng chứng ở `docs/evidence/`.
4. Skill mới chưa bật hành vi mặc định nào (không hook, không chèn context): không thuộc phạm vi eval bật/tắt `LOOP-DESIGN-025`.
   Test kích hoạt tất định cho mọi skill (`XC-DOCAI-025`) đi ở PR riêng.

## Hệ quả

- (+) Agent có quy trình cụ thể cho sáu tác vụ thường gặp nhất, cùng cổng bằng chứng (`loop record`) và điểm dừng của khung.
- (+) Tự chủ cao hơn có kiểm soát: PR nâng major đi trọn trong vòng khi chủ dự án đã chọn L3.
- (−) Thêm sáu `description` vào listing skill mỗi phiên (~2,9 KB UTF-8); bù lại `AGENTS.md`/template rút gọn danh sách để giữ trần byte.
- (−) Chưa có số đo hiệu quả từng skill; đo bằng `claude plugin eval --ablation with-without` khi có ngân sách (research note §3).
