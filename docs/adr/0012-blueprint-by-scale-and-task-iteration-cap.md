# ADR-0012: BLUEPRINT.md chỉ chứa MUST theo quy mô; trần vòng một phiên chỉ đếm task

- **Trạng thái:** Đã chấp nhận
- **Trạng thái triển khai:** Đã triển khai (`scripts/xt.py` `compose_split`, `compose --full`, `blueprint_backlog`,
  `blueprint_files`, `blueprint_status` đọc backlog, `audit plan` soi bằng chứng cả backlog, `_loop_init`; test
  `tests/test_xt.py::ComposeTest`, `tests/test_xt_cli.py`)
- **Ngày:** 2026-10-16
- **Thay một phần:** ADR-0009 §Quyết định 3 (công thức trần vòng).
- **Thay một phần bởi:** ADR-0022 (hệ số trần vòng x2: `max(40, 8 × task chưa làm)`, D-027) — công thức trong thân ADR này là bản cũ

## Bối cảnh

Đo bằng `xt.py compose` ngày 2026-10-16, hồ sơ `web-app` + ngành `ecommerce`, không `--include-may`:

| Quy mô | Bản một file | Số MUST | Chỉ phần MUST (file chính mới) | Backlog SHOULD |
|---|---|---|---|---|
| S | 693.662 B | 82 | 41.296 B (−94%) | 654.872 B |
| M | 692.859 B | 484 | 228.935 B (−67%) | 485.715 B |
| L | 691.547 B | 1.140 | 483.161 B (−30%) | 230.176 B |

Quy mô chỉ đổi **nhãn** MUST/SHOULD, không đổi nội dung, nên agent đọc `BLUEPRINT.md` ở S tốn token như ở L
(~690 KB ≈ 190k token mỗi lần đọc trọn). Verdict, `blueprint-status --strict` và cổng phát hành chỉ xét MUST.

Trần vòng của `loop init --single-session` là `max(20, 4 × (task chưa làm + MUST mở))`. Ở M với 484 MUST mở thì trần
≈ 2.000 vòng — gần như không có trần. MUST của blueprint đã được gom vào task của PLAN (task nêu ID mục nó đóng),
nên cộng thêm là đếm hai lần.

## Quyết định

1. `xt.py compose --out FILE` ghi **hai** file: `FILE` chỉ chứa mục MUST hiệu lực ở quy mô (bảng đếm vẫn đủ ba mức),
   `<tên>-BACKLOG.md` cạnh nó chứa SHOULD/MAY. Frontmatter của file chính khai `backlog: <tên>-BACKLOG.md`. Phần
   không còn mục MUST nào không in vào file chính. ID và chữ của mục không đổi.
2. Ghép lại giữ trạng thái + ghi chú theo ID từ **mọi** file cũ (bản một file trước ADR này, hoặc chính + backlog):
   đổi quy mô làm mục chuyển file thì trạng thái đi theo. Mục riêng của dự án về cuối file chính.
3. `blueprint-status` (và verdict, `_still_open`) đọc cả backlog khai ở frontmatter; khai mà mất file → `bad_lines`
   (`--strict` đỏ). Miễn trừ thiếu lý do trong backlog vẫn bị báo, kèm tên file. `audit plan` soi bằng chứng cũ ở
   cả hai file.
4. `--full` giữ hành vi cũ (một file mọi mức). Không `--out`: stdout chỉ in file chính, stderr nói số mục SHOULD/MAY
   không in.
5. Trần vòng một phiên: `max(20, 4 × task chưa làm)` — chỉ đếm task `[ ]` trong PLAN.

## Lý do

- File agent đọc mỗi vòng nên chỉ chứa thứ chặn "xong". SHOULD/MAY vẫn ở repo, cùng ID, cùng luật trạng thái.
- Hai file thay vì bỏ SHOULD: mục SHOULD có thể đã có tick/miễn trừ/bằng chứng; bỏ đi là mất công audit.
- Frontmatter khai backlog thay vì đoán tên file: đọc được bằng máy, đổi tên `--out` không làm mất liên kết.
- Trần theo task: một vòng có thể đóng nhiều MUST; PLAN là đơn vị công việc mà vòng lặp đếm.

## Các phương án đã cân nhắc

- **Giữ một file, rút gọn chữ của SHOULD (chỉ ID):** vẫn ~800 dòng ở S; mất phần *Kiểm* khi cần làm SHOULD. Loại.
- **Chỉ ghi MUST, bỏ hẳn SHOULD/MAY:** mất trạng thái SHOULD đã tick khi ghép lại. Loại.
- **Trần `4 × task + MUST/10`:** con số 10 là đoán, không có dữ liệu. Để sau, khi có số đo dự án thật.

## Hệ quả

- Dự án đích: ghép lại bằng đúng lệnh `compose ... --out BLUEPRINT.md` để tách; trạng thái giữ theo ID. Mục SHOULD
  chuyển sang file mới nên `git blame` của dòng bằng chứng SHOULD bắt đầu lại — `audit plan` có thể bỏ sót bằng chứng
  SHOULD cũ một lần. MUST không bị ảnh hưởng.
- Blueprint của chính repo khung (`BLUEPRINT.md`, S, 70 MUST · 803 SHOULD) chưa ghép lại trong thay đổi này.
