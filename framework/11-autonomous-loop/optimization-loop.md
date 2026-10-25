---
title: Vòng tối ưu hiệu năng trong autopilot: đo → profile → một thay đổi → máy quyết giữ/hoàn tác
kind: module
prefix: LOOP-OPT
applies_to: [all]
updated: 2026-10-25
---

# Vòng tối ưu hiệu năng trong autopilot

> Tối ưu là việc agent **dễ làm giả nhất**: số đo là tín hiệu thưởng, và nghiên cứu về agent tối ưu mã đều ghi nhận
> chúng ăn gian khi có thể (cache kết quả, hard-code input, đổi đồng hồ, sửa hàm chấm). Module này đặt **một
> vòng cố định do máy quyết** cho task tối ưu. *Đo cái gì, ngưỡng bao nhiêu* là nhà của
> [`XC-PERF`](../18-cross-cutting/performance-engineering.md), [`QA-PERF`](../14-testing-quality/performance-and-load.md),
> [`FE-PERF`](../07-frontend/performance-web-vitals.md); module này chỉ là **quy trình trong vòng lặp** và công cụ `xt.py perf`.

## Vòng cho một task tối ưu

Mỗi task tối ưu là một dòng `T-NNN` thường trong `PLAN.md` (parser không đổi); Gate là lệnh gói các bước 2–6.

1. **Mở task chỉ khi có mục tiêu số** (`XC-PERF-001`) hoặc ngân sách đang bị vượt. Không số thì không tối ưu (tránh tối ưu sớm, vi tối ưu không đo được).
2. **Khoá bộ đo trước khi sửa** (kiểu `prepare.py` của autoresearch): harness đo, bộ test tương đương hành vi, input đo nằm ngoài quyền sửa của agent; `xt.py perf guard --base <ref> --locked <glob>…` đỏ khi diff đụng — kể cả **xoá** — chúng.
3. **Baseline đo lại trong chính lượt Gate, trên commit gốc** (`git worktree` của `--base`), cùng máy với lượt đo sau: `xt.py perf sample --out before.json -- <lệnh đo>` (≥ 10 lần, bỏ warm-up) hoặc số tất định (lệnh, byte, truy vấn, token). Không đọc baseline từ file trong cây agent sửa được; baseline đã lưu thì commit vào đường dẫn khoá. `perf compare` từ chối hai file đo hai lệnh khác nhau.
4. **Profile, rồi mới chọn điểm nóng** (flamegraph, `EXPLAIN (ANALYZE, BUFFERS)`, `pg_stat_statements`, py-spy…). Chỉ nhận ứng viên có **trần tăng tốc** Amdahl `1/((1−p)+p/s)` đủ cho mục tiêu: tăng tốc 10 000× phần chiếm 10 % chỉ cho ≈ 1,11×.
5. **Một giả thuyết, một thay đổi:** ghi kỳ vọng và *falsifier* (số nào thì bỏ) **trước** khi đo.
6. **Máy quyết:** đo bản sau cùng máy/điều kiện ngay sau baseline (xen kẽ nếu được), `xt.py perf compare before.json after.json`:
   `improved` (p < 0,05 **và** đổi ≥ max(2 %, MAD/trung vị) — nhiễu máy đo là sàn) → *có thể giữ*; `neutral`/`regressed`/`insufficient` → **hoàn tác**. Giữ chỉ khi toàn bộ test xanh và chỉ số phụ không xấu đi.
7. **Ghi sổ, siết ratchet:** thử nào cũng vào `docs/autopilot/PERF-LOG.md` (giữ hay bỏ); giữ thì commit baseline/ngân sách mới, không nới.
8. **Dừng:** đạt mục tiêu thì dừng (không tối ưu vượt); 3 lần liên tiếp không `improved` cùng điểm nóng → đổi điểm nóng hoặc `loop defer`.

Gate ví dụ — **script Gate và công cụ chấm cũng là bộ đo khoá** (agent sửa được `xt.py` hay script thì `perf compare` nói gì cũng được): Gate trong `PLAN.md` lấy script từ commit gốc — ``Gate: `bash <(git show origin/main:scripts/perf-gate.sh)` `` — script dùng `xt.py` của commit gốc trong worktree (commit gốc phải có khung ở `.xtemplates/`; repo khung: `scripts/xt.py`). `perf guard`/`perf sample` làm việc trên gốc repo git của cwd, không theo `CLAUDE_PROJECT_DIR`, bỏ qua `GIT_DIR`/`GIT_WORK_TREE`/`GIT_INDEX_FILE` — script chạy từ cây agent sửa thì rà đúng cây đó:

```bash
# scripts/perf-gate.sh (dự án tự viết)
set -euo pipefail
base=origin/main
wt="$(mktemp -d)"; trap 'git worktree remove --force "$wt"' EXIT
git worktree add -q --detach "$wt" "$base"
XT="python3 $wt/.xtemplates/scripts/xt.py"          # công cụ chấm của commit gốc, không phải của cây agent sửa
$XT perf guard --base "$base" --locked 'bench/*' --locked 'tests/equiv/*' --locked 'scripts/perf-gate.sh' --strict
(cd "$wt" && $XT perf sample --out "$OLDPWD/before.json" -- ./bench/run.sh)   # baseline trên commit gốc, cùng lượt
$XT perf sample --out after.json -- ./bench/run.sh
$XT perf compare before.json after.json
```

Vị trí trong vòng đời: **G5** khoá bộ đo + baseline · **G6** mỗi task tối ưu theo vòng trên, một PR mỗi lát · **G7** nhóm "hiệu năng" của `/audit` và số đo trong GO/NO-GO (`QA-PERF-006`) · **G8** field data/SLO dẫn dắt backlog tối ưu kế tiếp (`LOOP-DESIGN-019`). Skill `/optimize` (ADR-0048) nối các bước này; chỉ khi có ngân sách đỏ.

## Công cụ `xt.py perf`

| Lệnh | Việc | Exit |
|---|---|---|
| `perf sample --out F [--runs 10 --warmup 2 --timeout 300] -- <lệnh>` | chạy lệnh nhiều lần, ghi thời gian tường (s) + commit + môi trường; lệnh lỗi/quá giờ thì không ghi | 0 · 1 lệnh lỗi · 2 thiếu lệnh |
| `perf compare B A [--exact] [--no-regress] [--higher-is-better] [--min-effect 0.02] [--json]` | so hai bộ mẫu bằng Mann-Whitney U + sàn nhiễu MAD; `--exact` cho đại lượng tất định | 0 = `improved` (`--no-regress`: cả `neutral`) · 1 còn lại · 2 file hỏng |
| `perf guard --base REF [--locked GLOB…] [--strict]` | worktree so với `REF`, gồm cả file chưa theo dõi: file khoá bị đụng/xoá → đỏ; dòng thêm đáng ngờ (cache/memoize, `sleep`, gán đè/patch đồng hồ, `_getframe`/`inspect.stack`, `-O3`) → ⚠ (`--strict`: đỏ) | 0 · 1 · 2 `git diff` lỗi hoặc glob khoá không khớp file nào |

File mẫu: mảng JSON, `{"samples": [...]}` hoặc các số cách nhau bằng khoảng trắng/dấu phẩy. `--locked` khớp kiểu `fnmatch` (`*` đi qua `/`: `bench/*` khoá cả cây; `**/` nhận cả không thư mục con; bỏ `./` đầu). Giới hạn đã biết: p xấp xỉ chuẩn → **bảo thủ** với n = 10 so với p chính xác của `benchstat`; sàn nhiễu MAD như `criterion`; file chưa theo dõi lọc theo `.gitignore` đã commit ở `--base` (guard tin file này); `.gitignore` đổi/mới → kiểm khoá trên mọi file chưa theo dõi và báo ⚠; không dùng `core.excludesFile`/`.git/info/exclude` — file sinh khi đo (`__pycache__`…) phải trong `.gitignore` của repo; file chưa theo dõi quét 1 MiB đầu, symlink chỉ quét chuỗi đích; `perf sample` giết cả nhóm tiến trình khi xong/quá giờ/Ctrl-C, không bắt SIGTERM gửi thẳng `xt.py`; `guard` bắt dấu hiệu, không chứng minh vô tội — reviewer vẫn phải rà.

## Checklist

- [ ] `LOOP-OPT-001` **MUST** Task tối ưu chỉ mở khi có **mục tiêu số kèm điều kiện đo** ([`XC-PERF-001`](../18-cross-cutting/performance-engineering.md)) hoặc ngân sách đang bị vượt; không có số thì không tối ưu. → Kiểm: dòng task trong `PLAN.md` nêu mục tiêu số và Gate chứa `perf compare`. · Nguồn: ý "ngân sách trước, đo sau" của `QA-PERF`.
- [ ] `LOOP-OPT-002` **MUST** **Bộ đo khoá:** harness đo, bộ test tương đương hành vi, input đo, **script Gate và công cụ chấm (`xt.py perf`)** nằm ngoài quyền sửa của agent — Gate chạy bản của commit gốc và `perf guard --locked …`, đỏ khi diff đụng chúng (kể cả xoá). → Kiểm: Gate lấy từ commit gốc (`git show <base>:…`) và chạy `perf guard --base <base> --locked '<glob bộ đo>' --locked '<script Gate>'` exit 0 bằng `xt.py` của commit gốc. · Nguồn: autoresearch (`prepare.py` "không sửa"); METR 2025-06-05 (hàm chấm bị ghi đè/thay stub).
- [ ] `LOOP-OPT-003` **MUST** **Máy quyết giữ hay hoàn tác:** chỉ giữ thay đổi khi `perf compare` = `improved` trên ≥ 10 mẫu mỗi bên (hoặc `--exact` cho đại lượng tất định), baseline đo lại trên commit gốc cùng lượt và cùng máy, **và** toàn bộ test xanh; còn lại hoàn tác — agent không tự nhận "nhanh hơn". → Kiểm: evidence `loop record` của Gate có exit 0 từ `perf compare`; Gate không đọc baseline từ file agent sửa được. · Nguồn: benchstat (Mann-Whitney U, α = 0,05, ≥ 10 lần); autoresearch (giữ nếu metric tốt hơn).
- [ ] `LOOP-OPT-004` **MUST@L** **Một giả thuyết, một thay đổi, một lần đo:** ghi kỳ vọng và falsifier trước khi đo ([`LOOP-DESIGN-021`](loop-design.md) áp dụng cho số đo); gộp nhiều thay đổi thì không biết cái nào có tác dụng, cái nào gây hại. → Kiểm: mô tả PR/`PERF-LOG.md` có giả thuyết + falsifier có trước số đo (đối chiếu thứ tự commit).
- [ ] `LOOP-OPT-005` **MUST@M** **Chống gian lận số đo:** mọi dòng `perf guard` báo ⚠ phải được `reviewer` (năng lực cao hơn người viết, `LOOP-ORCH-005`) trả lời từng dòng trước khi giữ; ngoài ra reviewer **tự rà** các kiểu máy không bắt được — hard-code shape/giá trị input, thoát sớm, tắt đồng bộ, hàm kiểm bị thay bằng stub, kết quả tái dùng giữa các lần đo. Lời nhắc "đừng gian lận" không đủ — chỉ giảm tỉ lệ, không loại bỏ. → Kiểm: `pr reviewed --clean` có ghi chú trả lời từng ⚠ và từng kiểu tự rà. · Nguồn: METR 2025-06-05 (30,4 % lượt RE-Bench có hack; nhắc không gian lận chỉ giảm nhẹ); GSO/SWE-fficiency (memoize, hard-code shape/dtype, monkey-patch).
- [ ] `LOOP-OPT-006` **SHOULD** **Profile trước khi sửa:** điểm nóng lấy từ profile/`EXPLAIN (ANALYZE, BUFFERS)`/`pg_stat_statements`, và trần tăng tốc Amdahl của nó đủ cho mục tiêu; không sửa chỗ không chiếm thời gian. → Kiểm: PR đính kèm profile hoặc ghi lý do không áp dụng ([`XC-PERF-005`](../18-cross-cutting/performance-engineering.md)). · Nguồn: định luật Amdahl.
- [ ] `LOOP-OPT-007` **SHOULD** **Đo trên input chưa thấy:** trước khi giữ, đo lại trên tập input/shape không nằm trong bộ đo mà agent đã nhìn (held-out), để bắt đường tắt chỉ đúng với input cũ. → Kiểm: Gate có lượt `perf compare` thứ hai trên tập held-out. · Nguồn: GSO, SWE-fficiency (đường tắt theo shape).
- [ ] `LOOP-OPT-008` **SHOULD** **Chỉ số phụ không xấu đi:** bộ nhớ, p99, kích thước, chi phí được đo cùng lượt và không vượt ngưỡng ghi trong `PROJECT.md`; không đổi chỉ số này lấy chỉ số kia. → Kiểm: Gate có `perf compare --no-regress` cho từng chỉ số phụ.
- [ ] `LOOP-OPT-009` **SHOULD** **Ưu tiên đại lượng tất định:** số lệnh (Cachegrind `Ir`), byte, số truy vấn, số token đo bằng `--exact`; thời gian tường chỉ dùng khi nhiễu được kiểm soát (ghim máy/lõi, xen kẽ trước/sau, MAD nhỏ). → Kiểm: Gate nêu đại lượng và cách kiểm soát nhiễu. · Nguồn: Valgrind Cachegrind (đếm lệnh lặp lại cao, thời gian lệch vài phần trăm); SWE-fficiency (ghim lõi, biến thiên < 0,5 %).
- [ ] `LOOP-OPT-010` **SHOULD** **Sổ thử:** `docs/autopilot/PERF-LOG.md` ghi mỗi lần thử (giả thuyết, số trước/sau, giữ hay bỏ, lý do); thử thất bại cũng ghi để vòng sau không thử lại. → Kiểm: file có dòng cho mỗi task tối ưu đã chạy.
- [ ] `LOOP-OPT-011` **SHOULD** **Trần và điều kiện dừng:** đạt mục tiêu thì dừng; 3 lần liên tiếp không `improved` cùng điểm nóng → đổi điểm nóng hoặc `loop defer`. → Kiểm: `loop stats`/`PERF-LOG.md` không có > 3 lần liên tiếp cùng điểm nóng. · Nguồn: nguyên tắc 4 của [`loop-design.md`](loop-design.md) (cùng chữ ký lỗi 3 lần → dừng).
- [ ] `LOOP-OPT-012` **SHOULD** **Siết ratchet, không nới:** sau khi giữ, baseline/ngân sách commit lại theo kết quả mới; nới ngân sách để xanh là quyết định ghi `loop decide` (D-NNN), không phải sửa cấu hình lặng lẽ. → Kiểm: diff ngân sách có D-NNN khi nới.
- [ ] `LOOP-OPT-013` **SHOULD** **Lab chặn PR, field nghiệm thu:** số lab (Lighthouse, benchmark, k6) dùng để gỡ lỗi và chặn PR; ưu tiên và nghiệm thu bằng field (RUM/CWV phân vị 75, SLO) khi có ([`XC-PERF-007`](../18-cross-cutting/performance-engineering.md)). → Kiểm: báo cáo GO/NO-GO ghi cả hai loại số. · Nguồn: web.dev "lab and field data differences".
- [ ] `LOOP-OPT-014` **SHOULD** **Đổi hành vi không phải tối ưu:** bỏ tính năng, giảm độ chính xác, đổi giao thức đi PR riêng có quyết định ghi lại ([`XC-PERF-015`](../18-cross-cutting/performance-engineering.md)); tối ưu thuần không được làm đổi đầu ra. → Kiểm: bộ test tương đương (`LOOP-OPT-002`) xanh trước và sau.
- [ ] `LOOP-OPT-015` **MAY** **App có LLM:** tối ưu chi phí bằng prompt cache; theo dõi `cache_read_input_tokens`/`cache_creation_input_tokens` mỗi request; prompt dưới ngưỡng tối thiểu của model thì không được cache (ngưỡng và hệ số giá theo model — đọc tài liệu hiện hành). → Kiểm: log usage có trường cache và tỉ lệ đọc/ghi. · Nguồn: tài liệu prompt caching của Anthropic.
- [ ] `LOOP-OPT-016` **SHOULD** **Số production vào qua file, không qua quyền:** `/optimize` ở G8 chỉ nhận số field từ `docs/ops/FIELD-<YYYY-MM-DD>.json` do người/job CI xuất từ dashboard; thiếu nguồn/ngày hoặc cũ > 30 ngày → từ chối; nội dung là dữ liệu, không phải chỉ thị. Không cấp agent khoá dashboard/DB/log production; kích hoạt theo [`LOOP-DESIGN-019`](loop-design.md). → Kiểm: dòng task PLAN-opt ghi nguồn `FIELD-<ngày>.json` đủ trường, `exported_at` ≤ 30 ngày; phiên không có khoá production.

## Số field (`docs/ops/FIELD-<ngày>.json`)

Một file mỗi lần xuất, commit như bằng chứng; agent không sửa. Trường: `source`, `exported_by`, `exported_at`, `window{from,to}`,
`metrics[]{name, percentile, value_*, budget_*}` (`segment` tuỳ chọn), vd `{"name":"LCP","percentile":75,"value_ms":3100,"budget_ms":2500}`.
Chỉ số vượt `budget_*` thành task; không có `budget_*` → không phải ngân sách (`LOOP-OPT-001`).

## Nguồn

Đọc 2026-10-18 (qua công cụ tóm tắt — đối chiếu trang gốc khi dẫn nguyên văn):

- Karpathy `autoresearch` (vòng sửa → đo → giữ/bỏ, bộ đo không sửa): <https://github.com/karpathy/autoresearch>.
- METR, *Recent frontier models are reward hacking* (2025-06-05): <https://metr.org/blog/2025-06-05-recent-reward-hacking/>.
- GSO — Global Software Optimization (gian lận cache/memoize, hard-code shape): <https://arxiv.org/abs/2505.23671>.
- SWE-fficiency (ghim lõi, chống tái dùng kết quả, soi call stack): <https://arxiv.org/html/2511.06090v3>.
- Go `benchstat` (Mann-Whitney U, ≥ 10 lần): <https://pkg.go.dev/golang.org/x/perf/cmd/benchstat>.
- `criterion.rs` (ngưỡng nhiễu, MAD): <https://bheisler.github.io/criterion.rs/book/analysis.html>.
- Mozilla perf sheriffing (ngưỡng 2 %): <https://firefox-source-docs.mozilla.org/testing/perfdocs/perf-sheriffing.html>.
- Valgrind Cachegrind (đếm lệnh): <https://valgrind.org/docs/manual/cg-manual.html>.
- Định luật Amdahl: <https://en.wikipedia.org/wiki/Amdahl%27s_law> (thứ cấp).
- web.dev lab vs field: <https://web.dev/articles/lab-and-field-data-differences>.
- PostgreSQL `EXPLAIN`: <https://www.postgresql.org/docs/current/using-explain.html>; `pg_stat_statements`: <https://www.postgresql.org/docs/current/pgstatstatements.html>.
- Prompt caching: <https://platform.claude.com/docs/en/build-with-claude/prompt-caching>.
- Chưa xác minh: tín hiệu thưởng AlphaEvolve, audit KernelBench, chống gian lận autoresearch, quy trình chính thống baseline → profile → một thay đổi.
- Stored (`seeker19110/stored`, `a1a1f51`): mục 23 (coverage ratchet, mutation test, tối đa 3 lần sửa cùng lỗi), 03 (evaluator–optimizer; lời khai không phải bằng chứng), 07 (Overmind: bản thắng là một git diff).
