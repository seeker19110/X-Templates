# PLAN-3.20-install-dedupe.md — Khung X-Templates · gom mệnh đề "Dự án đích" trùng của `install.py` → bản 3.18.3

> Lập ngày 2026-10-24. Chủ repo yêu cầu làm nợ 🟢 #191 (PROGRESS "Nợ 🟢"). Phiên chính tự duyệt (D-159).
>
> **Cú pháp bắt buộc cho máy:** mỗi task một dòng `- [ ] \`T-NNNN\` <việc> — Gate: \`<lệnh>\``.

## Tóm tắt (cổng duyệt — phiên chính tự duyệt, D-159)
- Phạm vi: khi nâng nhiều bản một lúc, `install.py` in "Bước làm tay từ CHANGELOG" theo từng mục bản; chỉ gộp mệnh đề
  trùng hệt trong CÙNG mục. Trên CHANGELOG thật: 108 mệnh đề, 7 cái trùng hệt ở nhiều bản (vd `Dự án đích: chạy lại
  \`install.py\` (hook \`guard.py\`).` ×3) → người nâng thấy cùng một bước nhiều lần.
- Cách: `upgrade_steps` gộp trùng hệt xuyên mục, giữ lần xuất hiện đầu theo thứ tự CHANGELOG (bản mới nhất); mục hết
  mệnh đề thì bỏ. Không gộp theo ngữ nghĩa (phải đoán câu tự do, có thể nuốt chi tiết) — mệnh đề khác chữ giữ nguyên.
- Không làm: sửa mệnh đề trong CHANGELOG cũ; đổi định dạng in; nợ khác của PROGRESS.
- Rủi ro: mệnh đề giữ ở bản mới hơn → người nâng từ bản giữa vẫn thấy (mọi bản > đã cài đều được xét). Đường lùi: bỏ
  tập `seen` trong `upgrade_steps`.

## Ngân sách (4 con số)
- Số vòng tối đa: `max(40, 8 × task)` (`loop init --single-session` tính)
- Chi phí: 0 đồng ngoài phiên (không phụ thuộc mới)
- Timeout mỗi lệnh Gate: 1800 giây (`XT_RECORD_TIMEOUT` mặc định)
- Ngày hết hạn: 4 giờ sau `loop init` (`--hours 4`)

## Điểm dừng bắt buộc (`loop defer`; `loop block` khi mọi việc còn lại phụ thuộc)
- Nâng khung ở dự án đích (PR `install.py`): chủ dự án merge

## Task

### Lát 1 — Gom trùng xuyên mục
- [x] `T-2801` `install.py` `upgrade_steps`: mệnh đề trùng hệt xuyên mục in một lần (giữ lần đầu theo thứ tự CHANGELOG, mục rỗng bỏ); test đơn vị + trên CHANGELOG thật không còn trùng; CHANGELOG + VERSION 3.18.3 (files: scripts/install.py, tests/test_install.py, CHANGELOG.md, VERSION) — Gate: `python3 -m unittest discover -s tests -k upgrade_steps`
