# PLAN-factory-BE.md — ADR-0068 lát B–E · gói Web/API, nâng dự án, worker, registry

> Lập 2026-11-05 trên nhánh `claude/amazing-brahmagupta-9jqbg1` (chủ dự án: "làm lát B-E trước"; không mở PR, không merge).
> Duyệt: D-359 (phiên chính tự duyệt, ADR-0008). Nguồn: [ADR-0068](../../adr/0068-software-factory-direction.md) §Quyết định
> B–E + §Xác nhận; research [`2026-11-04-software-factory-direction.md`](../../../research/2026-11-04-software-factory-direction.md)
> §5, §7. Stack đọc từ `seeker19110/hotel-manager@30492c9` (2026-11-05): Node 24, pnpm 12, TypeScript, Postgres qua
> `pg` + `kysely` (RLS theo tenant), `vitest`, `biome`; web là Next.js 16 (không đưa vào gói đầu — D-359).
>
> **Cú pháp bắt buộc cho máy:** mỗi task một dòng `- [ ] \`T-NNNN\` <việc> — Gate: \`<lệnh>\``.

## Tóm tắt (cổng duyệt)
- Gói `framework/templates/packs/web-api-ts/`: `pack.json` (id, owner, hạn hỗ trợ, compat, profile, control ID, khoá
  `xt.yaml`), `starter/` (mã khởi đầu + lock, chỉ chép vào repo sạch), `managed/` (file gói sở hữu, nâng theo hash manifest),
  `mutants.json` (ca sai cố ý cho CI, không cài). Phiên bản gói = `VERSION` của khung (ADR-0068 câu 1).
- Lát dọc (research §5) chạy bằng `vitest` với Postgres thật: migrate → đăng nhập → tạo dữ liệu → chặn tenant khác (API và
  RLS) → migration lùi/tiến → sao lưu/khôi phục (`pg_dump`/`pg_restore`) → dữ liệu và quyền còn đúng → build artifact có
  digest → `release-check` hàng `artifacts` PASS, `promotion` ≠ `approved` khi chưa ký.
- Ba ca sai cố ý (tenant chéo, `down` hỏng, contract đổi không tương thích) phải làm cổng đỏ — workflow
  `.github/workflows/pack-web-api.yml`.
- C: `install.py --pack <id>`; repo có `package.json` = brownfield (không chép starter); managed: chưa sửa → cập nhật, đã
  sửa → `.xtemplates-new` + drift trong `--plan`; lùi = cài lại bằng bản khung cũ. Kiểm trên bản clone hotel-manager
  (không đẩy). PR vào dự án đích: việc người.
- D: worker hàng đợi trong gói (khoá ý định chống trùng, lease hết hạn → lấy lại, crash giữa chừng, reconcile tác dụng phụ
  đúng một lần). Fixture payload host thật (Codex/Gemini) cần chạy CLI bằng tài khoản trả phí của chủ → `loop defer`.
- E: `docs/ops/registry.json` + `xt.py registry` (lệch core/gói, ngoại lệ hết hạn) + trang đọc trong `xt.py app`.

## Ngân sách (4 con số)
- Số vòng tối đa: bỏ trống · Chi phí: 0 đồng ngoài phiên · Timeout Gate: 1200 giây · Hạn: 24 giờ

## Điểm dừng bắt buộc về hành động
- Mở PR, merge, cắt bản, PR vào dự án đích, chạy CLI host bằng tài khoản của chủ: việc người (chủ dự án 2026-11-05).

## Task
- [x] `T-3685` B gói `web-api-ts`: `pack.json` + starter (node:http, kysely/pg, RLS, scrypt, migration up/down) + lock — Gate: `python3 -m unittest tests.test_packs`
- [x] `T-3686` B lát dọc `vitest` với Postgres thật + sao lưu/khôi phục + artifact digest (sau: T-3685) — Gate: `python3 -m unittest tests.test_packs`
- [x] `T-3687` B workflow `pack-web-api.yml`: repo sạch từ `install.py --pack`, lát dọc xanh, ba ca `mutants.json` đỏ (sau: T-3686, T-3688) — Gate: `python3 scripts/xt.py ci-check .github/workflows`
- [x] `T-3688` C `install.py --pack`: starter chỉ repo sạch, managed theo hash, drift trong `--plan`, idempotent, lùi bằng bản cũ — Gate: `python3 -m unittest tests.test_install_pack`
- [x] `T-3689` C chạy `install.py --plan --pack web-api-ts` trên bản clone hotel-manager, ghi kết quả vào báo cáo (sau: T-3688) — Gate: `python3 -m unittest tests.test_install_pack`
- [x] `T-3690` D worker: khoá ý định, lease, crash, reconcile trong gói + test (sau: T-3686) — Gate: `python3 -m unittest tests.test_packs`
- [x] `T-3691` E `docs/ops/registry.json` + `xt.py registry` + trang `xt.py app` — Gate: `python3 -m unittest tests.test_registry`
- [x] `T-3692` Tài liệu: ADR-0068 trạng thái, `packs/README.md`, CHANGELOG, harness/README (mức hỗ trợ), sổ nợ (sau: T-3687, T-3689, T-3690, T-3691) — Gate: `scripts/dev-task.sh gate-fast`

## Kết quả (bằng chứng cục bộ 2026-11-05)
- B: bản cài sạch từ `install.py --pack` với `postgres:17.11` — lint, typecheck, `vitest` 18/18 xanh; 4/4 ca
  `mutants.json` đỏ đúng test (`tests/pack_mutants.py check`); build hai lần cùng digest; `release-check` artifacts PASS,
  `promotion` chưa `approved` khi chưa ký.
- C: bản clone `seeker19110/hotel-manager@30492c9` (không đẩy): `--plan --pack` = brownfield, starter 22/22
  `skipped-brownfield`; workflow managed lúc đầu làm `ci-gates.test.mjs` đỏ (AUD-HAR-225) → sửa thành đề xuất
  `.xtemplates-new`; `blueprint-status --run` trước = sau (33 kiểm, 6 đỏ có sẵn của môi trường, 73 MUST mở); cài lại
  không đổi gì. PR nâng thật vào hotel-manager: việc người.
- D: worker trong gói; fixture payload host thật (Codex/Gemini) chưa làm — cần chạy CLI bằng tài khoản trả phí của chủ.
- Review (`reviewer-alt`): lát B–D 1 🔴 · 4 🟠 · 1 🟢 đã sửa ở `f3fe754`; nợ AUD-SEC-502, AUD-HAR-227. Lát E:
  APPROVE, 2 🟠 sửa ở `d2a779e`; nợ AUD-HAR-228, AUD-CODE-050, AUD-TEST-064.
- Trả nợ (sau gộp 3.30.0): AUD-HAR-227/228, AUD-CODE-050, AUD-TEST-064 đã sửa ở `f629e81`; AUD-SEC-502 sửa phần kiểu
  request, còn mở phần `baseline.json` chép đè cùng PR (cần quyết thiết kế).
