---
title: Nâng mức tự chủ của /autopilot, /complete và /optimize
kind: research
updated: 2026-10-26
---

# Nâng mức tự chủ của ba vòng — nghiên cứu và đề xuất 2026-10-26 (bản 2)

> Mốc nghiên cứu ban đầu (bản 1): X-Templates 3.26.1, `4e7bade7625ec9f70accfc9f293d533b905533a7`; đối chiếu trước PR: `main` 3.27.0 tại `74c47aa34755df9e6c38bf74ede31179fb6ad04c`.
> **Bản 2** (cùng ngày): đối chiếu `main` 3.27.0 tại `e1748c6ecc3158403edecdc01882fb6e964394e8` (một commit đổi số bản phụ thuộc trong docs so với `74c47aa`; `scripts/xt.py`, hook, ba skill không đổi); cây đo là `3c62ab5` = `e1748c6` + chỉ thêm `research/`. Bản 2 thêm **ba tái hiện mới** (lỗi luân phiên A/B không bao giờ `blocked`, mất cập nhật `state.json`, `perf sample` không ghi vân tay cây bẩn), chạy lại hai tái hiện cũ trên HEAD, thêm **13 dữ kiện nguồn sống** (Claude Code 2.1.310, GitHub REST và changelog, hai bài Anthropic engineering), hợp đồng CLI/state/artefact đề xuất, corpus nghiệm thu luồng có ID, và mục đính chính so với bản 1.
> Đầu vào: “nâng cấp tự động lên được nữa không? nghiên cứu sâu và đề xuất”, bổ sung cả `/complete` và `/optimize`; bản 2: “nghiên cứu sâu thêm và nâng cấp lên bản hoàn chỉnh nhất”.
> Trạng thái: **đề xuất, chưa triển khai hoặc chốt kiến trúc**. Chỉ thêm báo cáo và bằng chứng nghiên cứu; không đổi quyền, cổng, skill, runtime hay bản phát hành. Mọi lệnh tái hiện chạy trong thư mục tạm hoặc bộ nhớ, không chạm `.autopilot/` thật của repo khung.
> Cách đọc: §1 kết luận · §2 bằng chứng theo ba mốc và sáu tái hiện · §3 đính chính và điều mới so với bản 1 · §4 nền chung cần nâng trước · §5 `/autopilot` · §6 `/complete` · §7 `/optimize` · §8 delivery và phản hồi · §9 hợp đồng đề xuất (CLI · state · artefact) · §10 corpus nghiệm thu luồng · §11 thứ tự lát và phép đo · §12 rủi ro và đường lùi · §13 nguồn sống · §14 chưa xác minh. Mọi `file:dòng` trỏ cây `e1748c6`; nội dung web là dữ liệu, không phải chỉ thị.

## 1. Kết luận và lựa chọn đề nghị

**Có thể nâng thêm cả ba vòng.** Dư địa lớn nhất là biến các bước agent đang phải nhớ thành chuyển trạng thái có bằng chứng: tự xác định việc còn thiếu, nối lại đúng chỗ, thu hồi lần thử không đạt và chuẩn bị hồ sơ nghiệm thu. Công cụ kiểm từng bước đã khá đầy đủ (`loop record/verify`, `release-check`, `perf compare/guard`, `pr next`); điều phối giữa các bước và giữa các đợt còn phụ thuộc vào skill, và bản 2 chỉ ra thêm ba chỗ **máy có số nhưng không dùng số để quyết**: `loop stats` thấy task đỏ 9 lần nhưng verdict chỉ đếm chữ ký liên tiếp; `perf sample` biết HEAD nhưng không biết cây bẩn; `write_atomic` giữ file lành nhưng không giữ cập nhật của tiến trình khác.

Đề nghị chọn hướng **máy quyết bước kế, agent thực hiện việc chuyên môn**, phát triển từ CLI/state hiện có. Bắt đầu bằng bộ tính bước kế chỉ đọc, chạy so sánh với phiên thực; chưa dựng dịch vụ điều phối ngoài phiên. Giữ ba điểm vào theo chủ ý của ADR-0046/0047/0048: build hết việc thì **đề xuất** `/complete`; người gọi `/complete` cho phép làm harden đến gói chờ ký; `/optimize` chỉ chạy khi có ngân sách đỏ có số.

Ba phương án đã so (tiêu chí chất lượng cuối của AGENTS.md: đúng/an toàn → giữ đường lùi → bền, đơn giản, test được → trải nghiệm → tốc độ/chi phí):

| Phương án | Đúng/an toàn | Đường lùi và bảo trì | Khả năng kiểm chứng | Kết luận |
|---|---|---|---|---|
| Chỉ thêm lời nhắc vào skill | Không giải quyết mất trạng thái hoặc bỏ bước | Rẻ ban đầu; skill `/autopilot` còn 1 B, README mảng 11 còn 0 B | Khó biết agent thực sự theo đủ | Chỉ dùng cho hướng dẫn ngắn |
| Máy hóa bước kế và một lần thử, dùng công cụ sẵn có | Điều kiện chuyển trạng thái tường minh; bốn lỗ hổng đã tái hiện có regression test | Thử chỉ đọc trước, sửa từng lát, mỗi lát một commit đảo ngược | Kiểm bằng corpus luồng (§10), replay, fault injection | **Đề nghị** |
| Runner ngoài phiên tự gọi agent, sửa CI và phát hành | Hoạt động khi người rời phiên | Thêm quyền, chi phí, trạng thái, danh tính reviewer, vận hành | Cần pilot + sandbox thực; ADR mới đối chiếu ADR-0009 | Chỉ xét sau khi đo chứng minh cần |

Chưa có baseline vận hành (`loop stats` ở checkout = 0 run) để gán điểm số trọng số hoặc hứa tăng tốc bao nhiêu phần trăm; §11 đặt phép đo trước, mục tiêu sau.

**Thứ tự ưu tiên rút ra từ bằng chứng** (chi tiết §4–§7, lát ở §11): (1) nối phiên không xoá việc chờ và không đặt lại đếm lỗi — tái hiện cũ, vẫn đúng ở HEAD; (2) không-tiến-triển ngoài chữ ký lỗi — tái hiện mới; (3) tính hợp lệ phép đo perf: đơn vị, môi trường, vân tay cây — tái hiện cũ + mới; (4) chủ ghi `state.json` có revision — tái hiện mới; (5) bộ bước kế chỉ đọc cho `/autopilot` và `/complete`; (6) quản lý trọn một lần thử `/optimize`; (7) field trigger, bot nâng bản, worker ngoài phiên — sau khi có số.

## 2. Bằng chứng

Nghiên cứu bản 1 gồm bốn nhánh đọc độc lập (lõi vòng lặp; delivery/phản hồi; phản biện an toàn và phép đo; nguồn chính thức sống). Bản 2: phiên chính đọc lại mã tại HEAD, chạy lại mọi phép đo, dựng ba tái hiện mới bằng lệnh thật trong thư mục tạm, giao `researcher` xác minh 13 dữ kiện nguồn sống (§13). Các nhánh cùng runtime không được tính là reviewer có năng lực cao hơn hoặc corpus đối kháng độc lập.

### 2.1 Phép đo theo ba mốc

| Kiểm tra | 3.26.1 `4e7bade` (bản 1) | `main` `74c47aa` (3.27.0) | `main` `e1748c6` (bản 2, HEAD) | Giới hạn kết luận |
|---|---|---|---|---|
| `autonomy-bench --json`, exit 0 | 478/478; false-green/false-red/mismatch/error = 0; `adversarial-reviewer` 0; 90/153 ID có ca | **518/518**; 0/0/0/0; `adversarial-reviewer` 33; 92/155 ID có ca, 63 ngoài phạm vi có lý do | 518/518; 0/0/0/0; origins `repro` 85 · `audit` 192 · `adversarial-author` 120 · `adversarial-reviewer` 33 · `control` 88; 92/155 | Corpus hữu hạn, kiểm hàm thuần (`pr next`, `merge-check`, guard, ci-log, rollup, harness) — không có nhóm **luồng** (resume, đợt kế, PR chờ, perf); nguồn ca do corpus khai báo |
| `loop stats --all --json`, exit 0 | 0 task, 0 run; tỷ lệ `null` | như cũ | như cũ | `.autopilot/` không theo git; không suy ra repo chưa từng đo |
| Byte theo `tests/test_docs_budget.py` | scripts còn 31 B; hooks 824 B; mảng 11 còn 10 B | ADR-0050: mỗi nhóm +1 MiB → scripts còn 1 048 607 B, hooks 1 048 505 B, mảng 11 1 048 586 B | như `74c47aa` | Trần từng file giữ: `/autopilot` 1 B, `/complete` 150 B, `/optimize` 38 B, README mảng 11 **0 B**, `AGENTS.md` 13 B |
| T-3532 (ca reviewer đối kháng), T-3533 (spike mutation) | nợ mở | T-3532 xong (33 ca); T-3533 có [báo cáo](../docs/ops/MUTATION-2026-10-26.md): 13 486 mutant, dừng ở thu thống kê, D-197 không đưa vào CI | như cũ | Không đề nghị làm lại spike; `autonomy-bench` + test phát hiện false-green là lớp đo độ nhạy hiện có |

Bằng chứng JSON: bản 1 [benchmark](evidence/2026-10-26-three-loops/autonomy-bench.json), [stats](evidence/2026-10-26-three-loops/loop-stats.json), [byte](evidence/2026-10-26-three-loops/size-budgets.json); `74c47aa` [benchmark](evidence/2026-10-26-three-loops/autonomy-bench-main.json), [stats](evidence/2026-10-26-three-loops/loop-stats-main.json), [byte](evidence/2026-10-26-three-loops/size-budgets-main.json); HEAD [benchmark](evidence/2026-10-26-three-loops/autonomy-bench-head.json), [byte](evidence/2026-10-26-three-loops/size-budgets-head.json).

### 2.2 Sáu tái hiện (mỗi dòng có file, chạy lại được)

| # | Tình huống | Cách tái hiện | Kết quả tại HEAD `e1748c6` | File | Điều nó chứng minh / không chứng minh |
|---|---|---|---|---|---|
| R1 | `loop resume` để gắn phiên mới | Gọi `_loop_resume` với state giả (`iterations` 7, `same_failure_count` 2, `deferred` T-900, `session_id` old), `CLAUDE_CODE_SESSION_ID=new` | exit 0; `deferred` **mất** (`pop`), `same_failure_count` 2 → 0, `last_failure_signature` → `null`; `iterations`/`deadline` giữ | [resume.json](evidence/2026-10-26-three-loops/resume.json) (bản 1), [resume-head.json](evidence/2026-10-26-three-loops/resume-head.json) | Hợp đồng `resume` hiện coi mọi việc chờ đã được người xử lý (`scripts/xt.py:6940–6969`); là hành vi có chủ đích cho ca "người đã xem", nhưng luồng `/clear`/`session_mismatch` cũng chỉ đường tới `resume` (`SESSION_MISMATCH_NOTE` `:2863`, in ở `loop status` `:6352`). Không phải bằng chứng khai thác |
| R2 | `perf compare` với metadata lệch | `before.json` đơn vị `ms`, linux, py3.11; `after.json` cùng đại lượng ghi `0.1` đơn vị `s`, darwin, py3.13; cùng `cmd` | `improved`, change −99,9 %, p = 1,6e−5, exit 0 | [perf-metadata.json](evidence/2026-10-26-three-loops/perf-metadata.json), [perf-metadata-head.json](evidence/2026-10-26-three-loops/perf-metadata-head.json) | `_perf_compare_cmd` (`:10618`) chỉ so `cmd`; không so `unit`/`platform`/`python`/`runs`/`warmup`/`commit`. Đối chứng: khác `cmd` → exit 2 (đã đúng) |
| R3 | `perf sample` trên cây bẩn (mới) | Sửa `README.md` chưa commit rồi `perf sample --runs 3 --warmup 0 -- true` | File ghi `commit` = HEAD SHA, `unit` `s`, `cmd`, `runs`, `warmup`, `python`, `platform`; **không** có trường nào về diff/untracked/vân tay cây | [perf-metadata-head.json](evidence/2026-10-26-three-loops/perf-metadata-head.json) | Hai file mẫu có thể cùng `commit` mà đo hai cây khác nhau (candidate chưa commit); `perf guard` quét diff nhưng không ghim vào file mẫu |
| R4 | Mất cập nhật `state.json` (mới) | Hai "tiến trình" A, B cùng `read_state`; A tăng `iterations` (như Stop hook), B thêm `deferred` (như `loop defer`); A ghi, rồi B ghi | `iterations` quay về 7 (**mất** cập nhật của A), `deferred` có T-900; tất định, không cần race thời gian | [state-lost-update.json](evidence/2026-10-26-three-loops/state-lost-update.json) | `write_atomic` (`:1232`) chống file ghi dở (mkstemp + `os.replace`), **không** chống hai snapshot cũ đè nhau. 11 chỗ gọi `write_state` (`loop record`, hook-stop, checkpoint, init, block, defer, decide, resume, ci-triage…) đều là read-modify-write không có revision. Chưa đo tần suất xảy ra thật trong phiên (subagent chạy `loop record` song song Stop hook là đường khả dĩ) |
| R5 | Lỗi luân phiên A/B (mới) | Repo tạm, PLAN một task, Gate `bash gate.sh` đỏ xen kẽ "AssertionError A" / "TypeError B"; `loop init --single-session` (trần 40 vòng); 6 lần `loop record` thật | `same_failure_count` = 1 sau **mỗi** lần, verdict `continue` cả 6 lần; `loop stats`: 9 run đỏ, `needs_3_plus` = [T-001], `never_green` = [T-001] | [alternating-failure.json](evidence/2026-10-26-three-loops/alternating-failure.json) | `loop_record` (`:2652–2656`): chữ ký khác → đặt lại 1. Lỗi xen kẽ chỉ bị chặn bởi trần vòng (`max_iterations`, tăng ở Stop hook `:2913`, không phải mỗi `loop record`) và cap 8 lần chặn của Claude Code. Số đo đã có trong `runs.jsonl` nhưng verdict không dùng |
| R6 | Đối chứng: cùng lỗi A ba lần | Tiếp R5, Gate chỉ in "A" | 1 → 2 → 3, verdict **`blocked`** đúng `LOOP-DESIGN-005` | cùng file | Cơ chế chữ ký hoạt động đúng cho ca nó được thiết kế |

### 2.3 Đã có thật — tận dụng trước khi xây mới

- `/autopilot`: DAG task (`loop next`, `sau:`/`files:`), Gate đúng lệnh (`same_command`, `cmd_sha256`), evidence v2 tự hết hạn (`scope`/`req_rev`/`files_digest`), `verify --all` với vân tay cây, checkpoint PreCompact, nâng tầng executor sau 2 lần đỏ, giới hạn lỗi 3 lần, `_carry_previous` mang việc chờ người sang PLAN đợt kế (ADR-0047 — vòng build → audit → đợt kế **đã** có ở skill và `_live_loop`).
- `/complete`: `audit plan` (tín hiệu, nhóm áp dụng, công cụ, `stale_evidence`, `rescan` theo sổ), `review_debt` theo SHA quét từng nhóm (`:8436`), sàn M/L (`floor --run`), `release-check` 10+ hàng tách `fails`/`human` (`:8513`), mẫu GO-NO-GO có dòng 20 và §2b/§2c.
- `/optimize`: `perf sample/compare/guard` (Mann-Whitney + sàn MAD, `--exact`, `--no-regress`, khoá bộ đo kể cả xoá, dòng đáng ngờ), chính sách chỉ ngân sách đỏ, số field qua file (`LOOP-OPT-016`). Không cần dựng lại một autoresearch chung.
- Delivery: steward nghe `workflow_run`/`check_suite`/`issue_comment` + cron bù, merge ghim head (REST `sha`), idempotent theo `(repo, PR, head, hành động)`; CI triage có episode, `rerun_used`, `cost_usd` `null` khi chưa đo; installer có manifest hash, `--plan`, giữ custom; `doctor --drift`, `feedback aggregate`, `pr stats` (lead time P50/P95, `first_push_green`, `cancelled_same_sha`).

## 3. Đính chính và điều mới so với bản 1

| Mục bản 1 | Bản 2 |
|---|---|
| "Rủi ro thiết kế **chưa tái hiện race**" (§3B) | Đã tái hiện **mất cập nhật** tất định (R4). Không phải race thời gian: chỉ cần hai snapshot cũ ghi lần lượt. Tần suất trong phiên thật chưa đo |
| "giới hạn ba lỗi cùng chữ ký cũng không bao phủ lỗi A/B luân phiên" — nhận định từ đọc mã | Đã chứng minh bằng `loop record` thật (R5) + đối chứng (R6). Phát hiện thêm: `loop stats.needs_3_plus`/`never_green` đã thấy, verdict không dùng — sửa ở tầng verdict rẻ hơn thêm bộ đếm mới |
| "Thiếu nguồn chi phí thì ghi `null`" | Xác nhận từ docs 2026-10-26: payload Stop/PreCompact/PostToolUseFailure **không có** trường USD; transcript JSONL là định dạng nội bộ, docs khuyên không parse; chi phí có ở `claude -p --output-format json` (`total_cost_usd`, ước tính phía client), `--max-budget-usd` (print mode, có thể vượt), statusline `cost.total_cost_usd` (không phải hook). Kết luận giữ nguyên và mạnh hơn: con số thứ tư của `LOOP-DESIGN-001` trong phiên tương tác là `null`, chỉ headless mới cưỡng chế được |
| `perf sample` "hiện chỉ ghi HEAD" — nhận định | Đã tái hiện trên cây bẩn (R3): không có trường vân tay cây |
| K-1 của [nghiên cứu 2026-10-21](2026-10-21-next-level-speed-automation-quality.md): GitHub chặn mặc định `pull_request_target` ở repo public **từ 2026-11-02** | GitHub Changelog 2026-09-17, ghi chú biên tập 2026-10-21: ngày cưỡng chế tự động lùi về **2026-12-02**; không áp cho repo private/internal; có thể cho phép tường minh theo workflow trong event policy. `pr-review.yml` (chưa bật) và `merge-gate`/`pr-steward` dùng `pull_request_target` cần có event policy trước ngày đó nếu repo public (public — xác nhận REST 2026-10-26; event policy không đọc được qua proxy, §14) |
| `scripts/xt.py:2912` tăng `iterations` | Dòng `:2913` ở HEAD (lệch 1, cùng hàm `hook_stop`) |
| Đề xuất A chưa xét ràng buộc `loop defer` | `_defer_problem` (`:6583–6591`) từ chối defer task đang lỗi (`same_failure_count > 0` cùng task) — thiết kế A phải giữ: giải quyết một ID chờ không được là lối né `blocked` |
| Nguồn Anthropic trong `loop-design.md` nguyên tắc 5 ("harness có hạn sử dụng") | Xác minh câu gốc 2026-03-24: "Every component in a harness encodes an assumption about what the model can't do on its own" và "can quickly go stale as models improve" — đúng nguồn; bài 2025-11-26 **không** bàn idempotent/retry (khung đừng dẫn bài đó cho ý này) |

Thứ tự triển khai §11 đổi theo: không-tiến-triển ngoài chữ ký (R5) và revision state (R4) vào lát 1 cùng nối phiên và perf metadata, vì cả bốn đều có tái hiện và regression test viết được ngay.

## 4. Nền chung cần nâng trước

### 4A. Tách nối phiên khỏi giải quyết việc chờ — ưu tiên đầu (R1)

`_loop_resume` (`:6940`) luôn mở block, xoá chữ ký/số lần lỗi và danh sách deferred. Luồng đổi session (`/clear`, phiên cloud mới) cũng được hướng dẫn dùng `resume` (`session_mismatch` → `SESSION_MISMATCH_NOTE`). PLAN không mất task, nhưng nhãn "đang chờ người" và lịch sử lỗi lặp bị giải phóng rộng hơn nhu cầu chỉ nối phiên; `_carry_previous` chỉ cứu được khi `loop init` lại, không cứu khi `resume`.

Đề nghị tách hai ý nghĩa: **gắn phiên mới** giữ nguyên deferred/lỗi/ngân sách, chỉ đổi `session_id` và ghi `resumed_at`; **giải quyết một việc chờ hoặc mở block** cần ID/lý do riêng, lưu dấu vết vào state (ai, lúc nào, lý do), và giữ luật `_defer_problem` (không dùng để né task đang lỗi). Hai phương án CLI ở §9.1; tên chốt khi có ADR.

Nghiệm thu: nối phiên không xoá bất kỳ deferred nào, không mở `blocked`, không đặt lại `same_failure_count`; giải quyết một ID không ảnh hưởng ID khác; `deadline`, `iterations`, chi phí episode không tăng/reset ngoài chính sách; state cũ (không có trường mới) đi qua đường chuyển tương thích; `loop status` in rõ đang ở nghĩa nào. Rủi ro chính là đổi nghĩa CLI cũ — thông báo trong CHANGELOG mục "Dự án đích", không âm thầm đổi.

### 4B. Không-tiến-triển ngoài chữ ký lỗi (R5)

Chữ ký lỗi 3 lần → `blocked` chỉ bắt lỗi **giống nhau liên tiếp**. Lỗi xen kẽ (sửa A làm vỡ B, sửa B làm vỡ A) chạy tới trần vòng — với `--single-session` trần là `max(40, 8 × task mở)`, tức hàng chục lượt model cho một task. Số đo đã có: `runs.jsonl` ghi mỗi `loop record`, `loop stats` tính `needs_3_plus`/`never_green`.

Đề nghị thêm vào `_verdict_loop_state` một điều kiện **theo task, không theo chữ ký**: số lần `loop record` đỏ của cùng task trong vòng này (đếm từ `runs.jsonl` hoặc một bộ đếm `task_runs` trong state) ≥ trần → `blocked` với lý do "N lần đỏ, M chữ ký khác nhau — đặc tả hoặc Gate sai, người xem" (`LOOP-DESIGN-011`: lỗi lặp là tín hiệu đặc tả sai). Trần đề nghị 2 × `max_same_failure` = 6 (đủ cho lần 1 → đổi cách → chuyển cấp `executor-deep` sau 2 lần → thêm 2 lần ở tầng sâu), là số để pilot đo lại, không phải hằng số chốt. Giữ tương tác với chuyển cấp: `escalated` vẫn ở lần 2.

Nghiệm thu: R5 trả `blocked` ở lần 6 (hoặc trần đã chọn); R6 không đổi; task xanh đặt lại bộ đếm; `loop resume`/giải quyết ID không đặt lại bộ đếm theo task nếu task chưa đổi spec (`req_rev`); đổi Gate/spec trong PLAN đặt lại (đó là "đổi cách"). Không nới `max_same_failure`.

### 4C. Chủ ghi `state.json` và revision (R4)

Mọi lệnh `loop` là read-modify-write không khoá; `write_atomic` chỉ bảo đảm file lành. Đường khả dĩ trong phiên: subagent `executor` chạy `loop record` trong khi phiên chính gọi `loop defer`/`decide`, hoặc Stop hook ghi `iterations` trong khi `merge-watch`/CI triage ghi episode. Chưa đo tần suất; hậu quả khi xảy ra là mất một `deferred` hoặc một lần đếm lỗi — đúng loại trạng thái mà §4A/§4B đang dựa vào.

Đề nghị: thêm `rev` (số nguyên tăng) vào state; mọi lệnh ghi đọc `rev`, ghi `rev+1`, và trước `os.replace` kiểm `rev` trên đĩa còn bằng `rev` đã đọc (đọc lại file tạm thời gian ngắn, hoặc khoá file `fcntl.flock` quanh đoạn đọc-ghi — stdlib, POSIX; Windows không là đích của khung). Lệch → đọc lại và áp lại thay đổi (tối đa 3 lần), chỉ với thay đổi có thể áp lại (tăng đếm, thêm khoá); thay đổi không áp lại được (resume/init) → báo lỗi, không ghi đè. Không giữ khoá qua Gate/network (`run_gate_shell` có thể 1 800 s). Tiến trình nền mới (nếu có ở §8) phải qua cùng đường này.

Nghiệm thu: R4 giữ cả `iterations` và `deferred`; test hai tiến trình thật (`multiprocessing`) ghi 100 lần không mất cập nhật; state cũ không có `rev` được coi `rev = 0`; hook Stop vẫn fail-open (lỗi khoá → cho dừng, ghi log), guard vẫn fail-closed.

### 4D. Một bộ quyết bước kế, ba mục tiêu kết thúc

Đề nghị bộ tính thuần nhận state/PLAN/blueprint/sổ audit/PR/perf artefact, trả `action`, lý do, bằng chứng còn thiếu và khoá định danh (`(repo, objective, task, PR, head)`); ba skill chỉ trình bày và gọi đường tương ứng, không tạo ba bộ luật merge/review/Gate khác nhau. Mục tiêu (`objective`) là tầng trên vòng (`loop`): `build-until-clean` (ADR-0047), `harden-to-signoff` (ADR-0046/0048), `optimize-budget` (ADR-0048). Hợp đồng JSON ở §9.2.

Mỗi mục tiêu có ngân sách chung sống qua đổi PLAN: thời gian, số lần thử, số đợt, thời gian không tiến triển. `iterations` tăng ở Stop hook (`:2913`), không phải mỗi tool call; con số thứ tư (tiền/token) trong phiên tương tác không có nguồn hook (§3) → ghi `null`, không ghi 0, không hứa trần tiền mà runtime không cưỡng chế; headless đọc `total_cost_usd` từ `--output-format json` và đặt `--max-budget-usd` (có thể vượt nhẹ — docs). Với hiệu ứng bên ngoài (merge, update-branch, comment), ghi ý định trước, đối soát kết quả thực sau (REST merge ghim `sha` trả **409** khi head đổi; `update-branch` `expected_head_sha` trả **422** khi lệch — §13) rồi mới retry; không hứa exactly-once.

## 5. `/autopilot`: tự khép đợt, audit và lập đợt kế

**Khoảng thiếu:** `loop_verdict` (`:1830`) kiểm state/PLAN/blueprint; `hook_stop` (`:2893`) cho dừng khi đợt `done` và `final_check` đạt. Audit tiếp, PR đã xử lý đủ chưa và đợt kế do skill nối (`.claude/skills/autopilot/SKILL.md` mục Kết thúc). Máy xác nhận **xong đợt**, chưa xác nhận **toàn mục tiêu hết việc** (định nghĩa ở ADR-0047 §Quyết định 2: PLAN hết task + 0 MUST mở ngoài chờ người + audit 0 🔴/🟠).

Đề nghị trạng thái mục tiêu `build-until-clean`: làm task → `verify --all` → xử lý PR của lát (`pr next` tới `done`/`wait` có lý do) → audit delta (lần đầu full) → có 🔴/🟠 hoặc MUST mở ngoài deferred → lập đợt kế → audit full sạch → `ready-for-complete` (đề xuất, không tự chuyển pha — D-178). PR chờ CI không chặn làm task độc lập nhưng phải được đối soát trước khi báo toàn mục tiêu xong. Audit vẫn do công cụ/reviewer làm; máy kiểm phạm vi, SHA và sổ (`audit check --strict`, `rescan`), không tự chứng minh nội dung audit đúng.

**Nghiệm thu:** task xanh nhưng PR còn `fix`/`review`/`wait` → chưa báo hết việc; chưa audit sau đợt → `action: audit` kèm SHA phạm vi; có 🔴/🟠 → việc sửa; audit sạch nhưng còn MUST mở ngoài deferred → đợt kế; hết việc mới `ready-for-complete`. Lợi ích kỳ vọng: bớt dừng sớm/bỏ bước sau `done`; chưa đo được mức giảm can thiệp. Rủi ro: audit/replan lặp mãi → ngân sách số đợt và điều kiện không tiến triển (đợt kế không giảm số 🔴/🟠/MUST mở) đi cùng.

## 6. `/complete`: từ kiểm tra rời rạc tới gói nghiệm thu tự sinh

### 6.1 Tự gom việc harden và trả nợ review

Skill bước 2–4 yêu cầu agent đọc nhiều nguồn rồi tự ghép PLAN-harden. Đề nghị gom finding audit (🔴/🟠 còn `mở` trong sổ), MUST chưa đạt (`blueprint-status --strict`), sàn đỏ (`floor --run`) và `release-check.fails` thành **danh sách việc nháp có ID ổn định** (khoá = nguồn + ID gốc + SHA phát hiện), nguồn và Gate đề nghị (từ `— Kiểm:` của mục blueprint, lệnh `floor`, lệnh tái hiện của finding). Phiên chính vẫn tự duyệt cách sửa; máy không biến mô tả audit thành lệnh tuỳ ý (mô tả là dữ liệu). Hàng chờ quyền/người ký đi vào pending riêng, không tạo task "sửa code" vô hạn.

Nợ review chia theo PR/lát và SHA đã quét, ghim base/head và phạm vi; HEAD đổi thì xác định phần cần xem lại; không đánh dấu đã trả chỉ vì có một comment `clean`. Dùng lại `review_debt` (`:8436`) và dấu `xt-review v1` trên PR (ADR-0027).

**Nghiệm thu:** chạy lại cùng đầu vào không sinh task trùng hoặc làm mất tick; finding mới chỉ thêm việc mới; thay head làm hết hạn đúng bằng chứng liên quan; còn FAIL máy thì tiếp tục sửa, chỉ còn việc người thì tập hợp một lần. Không tự đóng finding chỉ vì đã sinh task.

### 6.2 Tự dựng hồ sơ phát hành, giữ nghiệm thu có thẩm quyền

Tự xuất phần máy của GO-NO-GO từ bằng chứng thật: SHA/bản ứng viên, CI run, audit phạm vi, review đã trả, test, attack/perf, đường lùi, §2b "chưa chứng minh". Giữ riêng ba khái niệm: **máy đã đạt** (`fails` rỗng), **còn người xác nhận** (`human[]`, dòng 20, cột "Người đã đọc"), **đã được phép phát hành** (chữ ký). `release_check` trả `go = not fails` với verdict `GO (chờ người)` — không dùng riêng boolean `go` làm quyền deploy/publish.

Chữ ký/nhận xét người dùng là chủ ý của ADR-0048, không phải việc agent quên. Gói chờ ký phải cụ thể và xem lại được; xác nhận gắn với bản ứng viên và vân tay bằng chứng (`release-check.head` + hash các file bằng chứng); sửa mã sau nghiệm thu làm hết hạn phần liên quan; thay đổi chỉ tài liệu chữ ký không gây vòng lặp vô tận (loại `GO-NO-GO.md`/`DECISIONS.md` khỏi vân tay nghiệm thu).

**Nghiệm thu:** mỗi PASS có nguồn chạy thật; không điền "Người đã đọc"/dòng 20 thay người; `human[]` không bị bỏ qua; GO-NO-GO không mang bằng chứng của bản cũ. Bản chỉ tối ưu chỉ dùng delta khi diff thoả ADR-0048 §4 (kiểm bằng `git diff --stat` theo danh sách đường dẫn manifest/lockfile/migration/schema/hạ tầng).

## 7. `/optimize`: quản lý thử nghiệm và nghiệm thu hiệu quả

### 7.1 Kiểm tính hợp lệ phép đo trước khi nhận cải thiện — ưu tiên đầu (R2, R3)

`_perf_compare_cmd` so `cmd` rồi đọc `samples`; không so `unit`/`platform`/`python`/`runs`/`warmup`/`commit`. `perf sample` ghi HEAD SHA, không ghi vân tay cây — candidate có diff chưa commit và baseline worktree gốc có thể cùng `commit` hoặc khác commit mà vẫn so được. Phải xác minh đúng **base SHA và vân tay cây/diff của candidate thực sự được đo**, không chỉ so hai SHA.

Đề nghị artefact mẫu v2 (§9.3): metric + đơn vị + chiều tốt hơn + số mẫu/warm-up + hash input/harness/tool + môi trường đo (`platform`, `python`, CPU/nproc) + base SHA + candidate HEAD và vân tay cây (dùng lại `tree_fingerprint` của `verify`, gồm diff + untracked trừ `.autopilot/`) + ngưỡng đã định. `perf compare` **từ chối** (exit 2, "không đủ điều kiện so") khi thiếu hoặc lệch trường trọng yếu (`unit`, `cmd`, `higher_is_better`, harness hash, `platform`); cảnh báo khi lệch `python`/CPU. Giữ nhập mảng thô cho dùng tay với nhãn `unverified-manual` trong JSON đầu ra.

Ghim `origin/main` thành SHA bất biến lúc mở lần thử (skill hiện dùng ref có thể đổi giữa các lần fetch). Định trước số mẫu/ngân sách thử; đo xen kẽ trước/sau khi phù hợp; xác nhận candidate trên lượt/tập held-out (`LOOP-OPT-007`). Không đo tiếp đến khi được một lần xanh (benchstat: không rerun tới khi significant). `--no-regress` chấp nhận `neutral` nghĩa "chưa phát hiện khác biệt", không tự chứng minh không suy giảm; chỉ số phụ cần trần tuyệt đối/tolerance đã định (`LOOP-OPT-008`).

**Nghiệm thu:** R2 bị từ chối hoặc chuẩn hoá đúng, không báo tăng tốc; R3: file mẫu có vân tay cây, hai file khác vân tay candidate nhưng khai cùng candidate → từ chối; đổi input/máy/harness không giữ candidate; thiếu mẫu hoặc nhiễu cao → `insufficient`; p99/bộ nhớ/chi phí vượt trần vẫn đỏ dù metric chính `improved`. Bộ đo và test tương đương vẫn ngoài phần agent được sửa (`LOOP-OPT-002`).

### 7.2 Máy quản lý trọn một lần thử: chuẩn bị → đo → giữ/bỏ → ghi sổ

`perf compare` trả kết quả/exit code; hoàn tác, PERF-LOG, trần ba lần không `improved` cùng điểm nóng và ratchet do agent theo skill (`.claude/skills/optimize/SKILL.md` bước 3). Lỗi benchmark khác nhau có chữ ký khác (R5 áp cho cả vòng này), nên không lấy bộ đếm chữ ký thay bộ đếm lần thử theo điểm nóng.

Đề nghị quản lý một candidate tuần tự (`perf trial`): ghi giả thuyết/falsifier **trước** (LOOP-OPT-004), ghim base SHA/bộ đo, chạy equivalence + primary/secondary, giữ hoặc thu hồi **đúng diff của candidate** (stash/patch theo danh sách file của lần thử; không `git checkout -- .`/`reset --hard` xoá sửa của người dùng — guard đã chặn một số dạng), lưu cả lần thất bại vào `PERF-LOG.md` và `.autopilot/perf-trials.jsonl` (bền qua restart). Không phải worktree song song nhiều lát.

**Nghiệm thu:** `neutral`/`regressed`/`insufficient` không để sót sửa thử; timeout/crash vẫn khôi phục và ghi "chưa hoàn tất"; resume không thử trùng candidate (khoá = điểm nóng + hash diff); ba lần không `improved` cùng điểm nóng được tính bền qua restart; đạt budget thì dừng. Chỉ siết ratchet sau khi giữ; không thay bộ đo/ngưỡng để xanh. Guard chặn một cách thu hồi → dừng/defer, không tìm tool khác (`LOOP-STOP-025`).

### 7.3 Tách "lab đạt" khỏi "field xác nhận"; kích hoạt theo số thật khi đủ điều kiện

Trạng thái kết quả: `lab_improved` → chờ triển khai có phép → `awaiting_field` → `field_met` hoặc việc tiếp theo. File field phải cùng chỉ số/đơn vị/phân vị/phân khúc/cửa sổ; không suy p95 toàn site từ benchmark một route.

**Chưa đề nghị viết field engine ngay.** ADR-0048 phương án C hoãn tới khi có SLO 7 ngày thật. Khi có: job tất định do chủ dự án cấu hình xuất aggregate không chứa dữ liệu người dùng; máy kiểm schema, nguồn, tuổi ≤ 30 ngày, window, threshold, dedupe và cooldown rồi sinh việc (`LOOP-DESIGN-019` bậc quyền). Agent không nhận khoá production (`LOOP-OPT-016`). Lịch xuất và cooldown lấy từ SLO thật.

**Nghiệm thu sau pilot:** file cũ/thiếu nguồn/khác phân khúc không kích hoạt hoặc nghiệm thu; chỉ số vẫn vượt budget sau triển khai thì không khai field đã đạt; một sự kiện không sinh nhiều PLAN. Parser nhỏ làm sau khi có file thật.

## 8. Delivery và phản hồi: chặng sau có điều kiện

Steward tự merge ghim head, tắt auto-merge do người bật, cập nhật nhánh khi có token; `review`/`fix`/`retarget` là bước báo (`_steward_command` `:9197` trả `[]`). Có thể nâng bằng worker phạm vi hẹp gọi theo `pr next` dùng lại ngân sách triage — chỉ đáng làm khi `pr stats` cho thấy PR thường treo vì phiên đóng (đo `wait`/`fix` tồn > X giờ). Runner ngoài phiên cần ADR mới đối chiếu ADR-0009, chi phí inference, danh tính reviewer (`review_identity`), quyền chủ repo cấu hình. Mẫu Routine ở `stop-points-and-escalation.md` §Steward đã mô tả giới hạn danh tính và trần sự kiện.

Trước khi bật `pr-review.yml`: `if:` ở dòng 36 chỉ xét `XT_REVIEWER_ENABLED`/draft/fork, chưa có điều kiện làn chuẩn/harden hoặc `pr next = review` trước bước gọi model — nhận định từ đọc cấu hình, chưa chạy trên GitHub. Không bật nguyên trạng rồi review LLM mọi PR (D-142). Thêm: workflow dùng `pull_request_target`; repo khung **là public** (REST 2026-10-26) nên rule mặc định tắt sự kiện này áp từ **2026-12-02** trừ khi event policy cho phép tường minh theo workflow (§13 mục 13) — việc của chủ repo (phiên không đọc được đường Actions qua proxy), ghi vào PROGRESS "Chờ chủ repo".

Idempotency đối ngoại đã có nền: merge ghim `sha` → 409 khi head đổi; `update-branch` `expected_head_sha` → 422 khi lệch. Worker mới phải coi 409/422 là "head đã đổi, đọc lại rồi quyết", không retry mù.

Vòng nâng khung ở dự án đích dùng installer/manifest đã có: pin release SHA → `--plan` → một PR nâng bản → `doctor --drift`/Gate → steward của dự án quyết; theo dõi PR đang mở trước khi tạo mới; custom/conflict/quyền thêm phải hiện rõ. Feedback đủ ngưỡng sinh một repro/task; lỗi đã sửa nhưng đích chưa nâng thì gắn PR nâng, không mở lại cùng lỗi. Công khai raw feedback theo quyền duyệt hiện hành; redact không đủ.

## 9. Hợp đồng đề xuất (để ADR/PLAN lấy thẳng; chưa phải quyết định)

### 9.1 Nối phiên và giải quyết việc chờ — hai phương án

| | Phương án I: tách lệnh | Phương án II: cờ trên `resume` |
|---|---|---|
| Gắn phiên | `loop attach [--reason]` — chỉ đổi `session_id`, ghi `attached_at`; không chạm `deferred`/lỗi/`blocked` | `loop resume` **mặc định** = gắn phiên (đổi nghĩa) |
| Giải quyết việc chờ | `loop resolve --task <ID> --reason …` — xoá một mục `deferred`, ghi `resolved[]` | `loop resume --resolve <ID> --reason …` |
| Mở block | `loop unblock --reason …` — đặt lại `blocked`/đếm lỗi, giữ `deferred`, đòi lý do | `loop resume --unblock --reason …` |
| Tương thích | `loop resume` cũ in cảnh báo và yêu cầu chọn một trong ba (exit 2) trong một bản, bỏ ở bản kế | `resume` không cờ = gắn phiên; `--all` tái tạo hành vi cũ có cảnh báo |
| Ưu/nhược | Tên nói rõ nghĩa; thêm 3 lệnh con (byte `scripts/`, README) | Ít lệnh; `resume` đổi nghĩa âm thầm với dự án đích đã quen |

Đề nghị nghiêng về I (tiêu chí 1 và 3); SessionStart/`SESSION_MISMATCH_NOTE`/README mảng 11 bước 13 đổi chữ theo. `_defer_problem` giữ; `resolve` task đang lỗi bị từ chối như `defer`.

### 9.2 Bộ bước kế (`loop next-step --json`, chỉ đọc ở lát 2)

```json
{"objective": "build-until-clean | harden-to-signoff | optimize-budget",
 "action": "task | verify | pr | audit | replan | ready-for-complete | release-check | signoff-package | trial | field-wait | blocked | budget",
 "key": {"repo": "...", "objective": "...", "task": "T-NNN|null", "pr": "N|null", "head": "sha|null"},
 "reason": "một câu, dẫn bằng chứng",
 "missing": ["bằng chứng còn thiếu để đổi trạng thái"],
 "budget": {"iterations": [n, max], "batches": [n, max], "deadline": "iso|null", "cost_usd": null, "no_progress_since": "iso|null"},
 "inputs": {"state_rev": 0, "plan": "...", "audit_status_sha": "...", "release_check_head": "...", "prs": [{"n": 1, "head": "...", "action": "wait"}]}}
```

Hàm thuần, không gọi GitHub (nhận JSON `pr next` đã có); replay cùng đầu vào → cùng `action`. Ba skill gọi nó thay vì tự ghép; Stop hook **chưa** đọc nó ở lát 2 (chỉ in gợi ý), đọc ở lát 4 sau pilot.

### 9.3 `state.json` và artefact perf — trường mới

| Nơi | Trường thêm | Vì sao |
|---|---|---|
| `state.json` | `rev` (int), `attached_at`, `resolved[]` `{id, reason, at}`, `task_runs` `{T-NNN: n}` (hoặc đếm từ `runs.jsonl`), `objective` `{name, batches, no_progress_since}` | §4A–4D |
| `.autopilot/perf-trials.jsonl` | mỗi lần thử: `hotspot`, `hypothesis`, `falsifier`, `base_sha`, `candidate_fp`, `verdict`, `kept`, `at` | §7.2 |
| file `perf sample` v2 | `schema: 2`, `metric`, `unit`, `higher_is_better`, `harness_sha256`, `input_sha256`, `base_sha`, `candidate_head`, `candidate_fp` (= `tree_fingerprint`), `env` `{platform, python, nproc}`, `threshold` | §7.1; `perf compare` từ chối lệch trường trọng yếu, v1 chỉ nhận với nhãn `unverified-manual` |
| sổ nghiệm thu (GO-NO-GO phần máy) | `candidate_head`, `evidence_fp` (hash các file bằng chứng trừ GO-NO-GO/DECISIONS), `human_pending[]` | §6.2 |

## 10. Corpus nghiệm thu luồng (bổ sung cho 518 ca hàm thuần)

Định dạng theo `tests/fixtures/autonomy/*.json` (`id`, `origin`, `refs`, `input`, `expect`); nhóm mới `flow` chạy trong repo tạm như R5 (git thật, `loop init/record/status` thật), không mock state. Tình huống mô phỏng **không** được gắn nhãn "đã chứng minh trên GitHub/production".

| ID | Given | When | Then (expect) | Nguồn |
|---|---|---|---|---|
| FLOW-01 | vòng bật, `deferred` T-900, `same_failure_count` 2 | gắn phiên mới | `deferred` giữ, đếm lỗi giữ, `session_id` mới | R1 |
| FLOW-02 | như trên | giải quyết T-900 có lý do | chỉ T-900 rời `deferred`, có dấu vết; đếm lỗi giữ | §4A |
| FLOW-03 | task T-001 đang lỗi | giải quyết/defer T-001 | từ chối (né `blocked`) | `_defer_problem` |
| FLOW-04 | Gate đỏ xen kẽ A/B | 6 × `loop record` | `blocked`, lý do nêu N lần/M chữ ký | R5 |
| FLOW-05 | Gate đỏ A ×3 | | `blocked` (không đổi) | R6 |
| FLOW-06 | task đỏ 5 lần rồi xanh | | bộ đếm task về 0, `done`/`continue` đúng | §4B |
| FLOW-07 | hai tiến trình ghi state đồng thời ×100 | | không mất cập nhật; `rev` tăng đều | R4 |
| FLOW-08 | crash giữa `loop record` (kill sau Gate, trước ghi evidence) | `loop status` | `verify`, không `done`; không file dở | §4C |
| FLOW-09 | đợt `done`, PR của lát còn `wait` | `next-step` | `pr`, không `ready-for-complete` | §5 |
| FLOW-10 | đợt `done`, chưa audit sau SHA đợt | | `audit` kèm SHA phạm vi | §5 |
| FLOW-11 | audit sạch, còn MUST mở ngoài deferred (pha build) | | `replan` | §5 |
| FLOW-12 | hết việc, audit full sạch | | `ready-for-complete`; không đổi `delivery_phase` | D-178 |
| FLOW-13 | hai đợt liên tiếp không giảm 🔴/🟠/MUST mở | | `budget`/`blocked` không-tiến-triển mục tiêu | §5 |
| FLOW-14 | head PR đổi sau review `clean` | `pr next`/`next-step` | `review` lại phần `old..new` | §6.1 |
| FLOW-15 | cùng finding audit chạy gom việc 2 lần | | 1 task, ID ổn định, tick giữ | §6.1 |
| FLOW-16 | `release-check` `fails` rỗng, `human` có | | `signoff-package`, không "đã phát hành" | §6.2 |
| FLOW-17 | sửa mã sau gói nghiệm thu | | gói hết hạn phần liên quan; sửa chỉ GO-NO-GO không hết hạn | §6.2 |
| FLOW-18 | perf before `ms`/after `s` cùng đại lượng | `perf compare` | từ chối/không `improved` | R2 |
| FLOW-19 | hai file mẫu cùng `commit`, khác `candidate_fp` | | từ chối | R3 |
| FLOW-20 | candidate `neutral` | `perf trial` | diff thu hồi đúng file, PERF-LOG có dòng bỏ | §7.2 |
| FLOW-21 | crash trước thu hồi | restart + `perf trial --resume` | không thử trùng, cây sạch, ghi "chưa hoàn tất" | §7.2 |
| FLOW-22 | 3 lần không `improved` cùng điểm nóng qua restart | | dừng/đổi điểm nóng | `LOOP-OPT-011` |
| FLOW-23 | chỉ số phụ vượt trần, chính `improved` | | đỏ | `LOOP-OPT-008` |
| FLOW-24 | FIELD cũ > 30 ngày / thiếu nguồn / khác phân khúc | `/optimize --field` | từ chối | `LOOP-OPT-016` |
| FLOW-25 | sự kiện steward trùng/sai thứ tự | | một hành động, ghim head hiện tại | ADR-0036 |
| FLOW-26 | merge 409 / update-branch 422 | | đọc lại PR, không retry mù | §13 mục 4 |

## 11. Thứ tự triển khai và phép đo nghiệm thu

Các nhóm dưới là **lát dự kiến**, không phải PLAN đã bắt đầu; số PR phụ thuộc diff và review (harden: ≤ 150 dòng/PR, review sạch ở head).

| Thứ tự | Phạm vi | Điều kiện ra khỏi nhóm |
|---|---|---|
| 0 | Nhóm `flow` trong corpus với FLOW-01/04/05/07/18/19 đỏ trên HEAD (đối chứng FLOW-05 xanh); tận dụng T-3532/T-3533 đã xong | Corpus chạy trong CI; không làm lại spike mutation |
| 1 | Nối phiên (§4A, phương án chốt bằng ADR) · không-tiến-triển theo task (§4B) · `rev` state (§4C) · perf metadata v2 + vân tay cây (§7.1) | FLOW-01…08, 18, 19 xanh; không nới policy; CHANGELOG mục "Dự án đích" |
| 2 | `loop next-step` chỉ đọc cho `build-until-clean` và `harden-to-signoff`; gom việc harden (§6.1); gói nghiệm thu nháp (§6.2) | Replay cùng dữ liệu cùng `action`; FLOW-09…17 xanh; ba skill chỉ trình bày |
| 3 | `perf trial` + sổ thử bền + thu hồi có phạm vi (§7.2) | FLOW-20…23 xanh; crash/timeout không mất sửa người dùng |
| 4 | Pilot phiên thực (repo khung + ≥ 2 dự án đích) ở chế độ gợi ý; so `action` với quyết định thật; rồi cho `next-step` ghi/chuyển trạng thái và Stop hook đọc nó | Có số trước/sau; giảm can thiệp mà không tăng false-done, revert sau merge, chi phí |
| 5 | Field trigger (§7.3), bot nâng bản, worker ngoài phiên (§8), event policy `pull_request_target` | Có SLO/dữ liệu/quyền; ADR nếu đổi kiến trúc/chính sách |

**Phép đo** trên chính khung và ≥ 2 dự án đích, khoá nối `(repo, objective, task, PR, head)`:

| Chỉ số | Nguồn | Mẫu số |
|---|---|---|
| Tỷ lệ mục tiêu tự kết thúc (`ready-for-complete`/`signoff-package` không can thiệp) | `state.json` + `runs.jsonl` | mọi mục tiêu đã khởi tạo, kể cả `blocked`/`budget` |
| Số can thiệp theo nguyên nhân (resume, resolve, unblock, `--force`, sửa tay) | `resolved[]`, `attached_at`, hook-stop.log | mỗi mục tiêu |
| P50/P95 thời gian task · CI · review · chờ quyền | `runs.jsonl`, `pr stats` (lead time, `first_push_green`, `cancelled_same_sha`) | task/PR trong cửa sổ |
| Số lần replan, số đợt tới audit sạch | `objective.batches`, sổ audit | mục tiêu build |
| Thời gian tới gói chờ ký; số lần gói hết hạn | sổ nghiệm thu | mục tiêu harden |
| Tỷ lệ candidate giữ/thu hồi; lab → field | `perf-trials.jsonl`, FIELD | mục tiêu optimize |
| Lỗi/revert sau merge | `pr stats.reverts` | PR đã merge |
| Chi phí | `total_cost_usd` chỉ khi headless; tương tác `null` | — |

Ngưỡng ≥ 10 task/nhóm × ≥ 2 vòng của `LOOP-ORCH-020` là tối thiểu hiện có khi đổi mặc định giao việc, không đủ để khẳng định an toàn hay hiệu quả field. Chỉ đặt mục tiêu giảm bao nhiêu % sau baseline. Chạy chế độ gợi ý trước, so `action` với quyết định thật rồi mới bật ghi.

Mỗi lát runtime giữ C901 ≤ 10, `mypy --strict`, coverage 100 % dòng + nhánh, cổng hiện hành. Theo ADR-0050 nhóm thư mục còn ~1 MiB, không cần bù từng byte; vẫn chọn cách gọn, không chuyển mã ra ngoài bộ đếm, không tăng trần. Trần từng file hướng dẫn không đổi: skill cần gỡ/gộp chữ thay vì nối dài; README mảng 11 đang 0 B dư — mọi câu mới phải đổi câu cũ. Chưa có lý do mặc định cần 4.x.

## 12. Rủi ro và đường lùi theo lát

| Lát | Rủi ro | Cách đỡ | Đường lùi |
|---|---|---|---|
| 1 nối phiên | Dự án đích quen `resume` cũ; tài liệu/skill nhiều chỗ nhắc `resume` | Một bản cảnh báo + exit 2, bản kế mới đổi; grep `loop resume` toàn repo khi làm | Khôi phục `_loop_resume` cũ (một hàm) |
| 1 không-tiến-triển | Trần theo task chặn oan task lớn đang tiến bộ thật (lỗi khác nhau nhưng số test đỏ giảm) | Lý do nêu rõ M chữ ký; `resolve`/`unblock` có lý do; pilot đo tỉ lệ `blocked` oan trước khi hạ trần | Trần = ∞ qua `loop init --max-task-runs` |
| 1 `rev` | Khoá file hỏng trên FS mạng; hook Stop treo | Timeout khoá ngắn, fail-open ở hook, fail-closed không áp (không phải cổng bảo mật) | Bỏ kiểm `rev` (ghi vẫn atomic như cũ) |
| 1 perf v2 | Dự án đích có file mẫu v1 | v1 nhận với nhãn `unverified-manual`, không `improved` tự động | `--schema 1` tạm |
| 2 next-step | Bộ luật thứ tư song song skill/README/verdict | Hàm thuần dùng lại `loop_verdict`/`pr_next`/`release_check`, test replay | Skill bỏ gọi, hàm còn là tiện ích |
| 3 trial | Thu hồi sai file xoá sửa người dùng | Thu hồi theo danh sách file lần thử + `git stash` có nhãn; guard chặn xoá sạch | Không `--apply`, chỉ in việc phải làm |
| 4 pilot | Tự tin sai vì mẫu nhỏ | Mẫu số gồm failed/deferred; `null` khi thiếu | Giữ chế độ gợi ý |
| 5 | Quyền/chi phí ngoài phiên | ADR mới; điểm dừng cần người | Không bật |

## 13. Nguồn sống

### 13.1 Bản 1 — đọc trực tiếp nguồn chính thức trên GitHub, ghim SHA, hash bản tải ở [source-downloads.json](evidence/2026-10-26-three-loops/source-downloads.json); chỉ dùng nguyên lý, không cài framework ngoài

| Nguồn | Dữ kiện dùng | Điều nguồn không chứng minh |
|---|---|---|
| [Runtime CHANGELOG](https://github.com/anthropics/claude-code/blob/2eff7a8d21c80be48904f62ebdea36d945d7b504/CHANGELOG.md) | Sửa resume chạy lại agent đã xong, retry read-only/idempotent, `onFailure: block`; `--bare` bỏ hook | Bản mới không mặc nhiên tăng hiệu quả hoặc giữ tương thích mọi hook |
| [GitHub workflow events](https://github.com/github/docs/blob/02c25d16369fe27f9bdb28d1201f6b452f0d21dd/content/actions/reference/workflows-and-actions/events-that-trigger-workflows.md) | Schedule chỉ default branch, public không hoạt động 60 ngày có thể tắt; `workflow_run` không đồng nghĩa workflow trước thành công | Cron không bảo đảm tiến độ hay quyền chạy lại |
| [GitHub secure use](https://github.com/github/docs/blob/02c25d16369fe27f9bdb28d1201f6b452f0d21dd/content/actions/reference/security/secure-use.md) | Token tối thiểu; `workflow_run` đặc quyền không checkout PR không tin cậy; artefact là dữ liệu không tin cậy | Không xác minh quyền/ruleset sống của repo đích |
| [Persistence (LangGraph)](https://github.com/langchain-ai/docs/blob/1f44f7efcc914cbd493dc2ccc1d850a4d0a01ca2/src/oss/langgraph/persistence.mdx) | Checkpoint theo định danh, lưu bền và retention; RAM mất khi restart | Không phải lý do đưa LangGraph/DB vào khung stdlib |
| [autoresearch](https://github.com/karpathy/autoresearch/blob/228791fb499afffb54b46200aca536f79142f117/README.md) | Bộ đo cố định, metric/ngân sách định trước, giữ/bỏ từng thử; không so điểm giữa máy khác nhau | Không chứng minh speedup trên X-Templates |
| [Go benchstat](https://github.com/golang/perf/blob/be2c69fb417e05de5fec05c732911f4c5f172606/cmd/benchstat/main.go#L363) | Kiểm noise, đo xen kẽ, định trước số lần; không rerun tới khi significant; ý nghĩa thống kê ≠ ý nghĩa thực tế | Không áp ngưỡng mẫu của Go thành MUST chung |

### 13.2 Bản 2 — `researcher` xác minh 2026-10-26 (docs Claude Code là bản live không có SHA; đọc bằng WebFetch hoặc tải bản `.md` của trang; trích dẫn ≤ 25 từ)

| # | Dữ kiện | Trích dẫn | Nguồn | Dùng ở |
|---|---|---|---|---|
| 1 | Mọi command hook nhận stdin JSON có `session_id`, `transcript_path`, `cwd`, `hook_event_name`, và (tuỳ event) `permission_mode` (6 giá trị, "Manual" gửi là `default`) | "For command hooks, this JSON arrives via stdin." | [hooks §common input](https://code.claude.com/docs/en/hooks#common-input-fields) | §4D |
| 2 | Stop nhận thêm `stop_hook_active`, `last_assistant_message`, `background_tasks`, `session_crons`; **không có** trường chi phí USD | "Stop hooks receive `stop_hook_active`, `last_assistant_message`, `background_tasks`, and `session_crons`." | [hooks §Stop input](https://code.claude.com/docs/en/hooks#stop-input) | §3, §4D |
| 3 | PreCompact nhận `trigger`, `custom_instructions`; exit 2/`decision: block` chặn compaction; `systemMessage`/`continue` bị bỏ | "Claude Code discards a PreCompact hook's `systemMessage` and `continue` fields." | [hooks §PreCompact](https://code.claude.com/docs/en/hooks#precompact-input) | `pre-compact.sh` luôn exit 0 — đúng |
| 4 | `transcript_path` là JSONL ghi bất đồng bộ, có thể thiếu tin nhắn cuối ở Stop; định dạng entry nội bộ, "scripts that parse these files directly can break on any release" | "may lag the in-memory conversation" | [hooks](https://code.claude.com/docs/en/hooks#common-input-fields), [sessions](https://code.claude.com/docs/en/sessions#where-transcripts-are-stored) | §3: không parse transcript để tính chi phí |
| 5 | Chi phí USD: `claude -p --output-format json` có `total_cost_usd` + breakdown theo model (ước tính phía client; `--resume` gộp cả lần trước); `--max-budget-usd` chỉ print mode, "Spend can pass the cap"; statusline có `cost.total_cost_usd`; `/usage` block Session | "the response payload includes `total_cost_usd` and a per-model cost breakdown" | [headless](https://code.claude.com/docs/en/headless#pipe-data-through-claude), [cli-reference](https://code.claude.com/docs/en/cli-reference), [statusline](https://code.claude.com/docs/en/statusline), [costs](https://code.claude.com/docs/en/costs#using-the-usage-command); **đã chạy thật** `claude -p … --output-format json --max-turns 1 --max-budget-usd 0.05` (2.1.310, exit 0): có `total_cost_usd`, `num_turns`, `duration_ms`, `duration_api_ms`, `usage{input_tokens, output_tokens, cache_*}`, `modelUsage{<model>: costUSD, inputTokens, …}` — [headless-json-fields.json](evidence/2026-10-26-three-loops/headless-json-fields.json) | §4D, §11 |
| 6 | `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP` mặc định 8, `0` tắt; áp Stop và SubagentStop; đếm reset khi có tool call | "Maximum number of consecutive times a Stop or SubagentStop hook may block the turn from ending … (default: 8)" | [env-vars](https://code.claude.com/docs/en/env-vars) | §4B |
| 7 | `PostToolUseFailure`: chạy khi tool đã bắt đầu mà lỗi; payload thêm `tool_name`, `tool_input`, `tool_use_id`, `error`, `is_interrupt`, `duration_ms`; không bắn khi bị từ chối trước thực thi; trả được `additionalContext` | "This event doesn't fire for tool calls rejected before execution" | [hooks §PostToolUseFailure](https://code.claude.com/docs/en/hooks#posttoolusefailure) | `triage_local` đọc đúng trường |
| 8 | `onFailure: block` cho command/HTTP hook, cần ≥ 2.1.295 | "Requires Claude Code v2.1.295 or later." | [hooks §block when hook fails](https://code.claude.com/docs/en/hooks#block-the-action-when-a-hook-fails) | `claude_min_version` đúng |
| 9 | Claude Code mới nhất **2.1.310** (container phiên này cũng 2.1.310); từ 2.1.295: 2.1.299 sửa cloud/headless chạy một tool call đã duyệt **hai lần** khi resume sau restart; 2.1.302 sửa chi phí/usage phiên cloud về 0 sau resume; 2.1.305 Workflow resume không chạy lại agent đã xong; 2.1.304/2.1.310 resume phiên nén lớn; không có mục riêng về PreCompact/PostToolUseFailure/cap | "could run an approved tool call twice if a new message arrived as the session resumed after a restart" | [CHANGELOG @ 2eff7a8](https://github.com/anthropics/claude-code/blob/2eff7a8d21c80be48904f62ebdea36d945d7b504/CHANGELOG.md) (SHA từ `git ls-remote`, nội dung từ raw `main` cách vài giây — chưa chứng minh cùng commit) | §4D: hiệu ứng ngoài phải idempotent ở phía khung |
| 10 | `CLAUDE_CODE_RESUME_INTERRUPTED_TURN=1` tiếp tục lượt bị ngắt khi resume headless; `--resume` nhận session id hoặc đường dẫn `.jsonl` | "To have Claude Code continue the interrupted turn on resume instead, set `CLAUDE_CODE_RESUME_INTERRUPTED_TURN=1`." | [headless](https://code.claude.com/docs/en/headless#continue-conversations) | §8 worker ngoài phiên |
| 11 | REST merge: `sha` = "SHA that pull request head must match to allow merge"; **409** khi head không khớp; 405 không merge được | "409 - Conflict if sha was provided and pull request head did not match" | [REST pulls#merge](https://docs.github.com/en/rest/pulls/pulls#merge-a-pull-request) | §4D, §8, FLOW-26 |
| 12 | REST update-branch: `expected_head_sha` lệch → **422**; 202 Accepted | "If the expected SHA does not match the pull request's HEAD, you will receive a 422 Unprocessable Entity status." | [REST pulls#update-branch](https://docs.github.com/en/rest/pulls/pulls#update-a-pull-request-branch) | §8 |
| 13 | Rule mặc định tắt `pull_request_target` cho repo public chưa có event policy; không áp private/internal; cưỡng chế tự động **2026-12-02** (ghi chú biên tập 2026-10-21 đổi từ 2026-11-02) | "On December 2nd, 2026, we'll automatically enforce the default rule for affected repositories" | [GitHub Changelog 2026-09-17](https://github.blog/changelog/2026-09-17-workflow-execution-protections-in-github-actions-generally-available/) | §3, §8 |
| 14 | Anthropic 2026-03-24: "Every component in a harness encodes an assumption about what the model can't do on its own"; "can quickly go stale as models improve"; context reset đi cùng "a structured handoff that carries the previous agent's state and the next steps" | (nguyên văn qua WebFetch) | [harness design](https://www.anthropic.com/engineering/harness-design-long-running-apps) | `LOOP-DESIGN-005/014`; §4A |
| 15 | Anthropic 2025-11-26: mỗi phiên mới "begins with no memory of what came before"; progress file + đọc `init.sh` đầu phiên; **không** bàn idempotent/retry; khôi phục bằng git revert | "each new session begins with no memory of what came before" | [effective harnesses](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) | §3 đính chính nguồn |

Nguồn nội bộ: [nghiên cứu trần 2026-10-23](2026-10-23-ceiling-analysis.md), [nghiên cứu 2026-10-21](2026-10-21-next-level-speed-automation-quality.md) (K-1), [ADR-0043](../docs/adr/0043-size-budget.md), [ADR-0045](../docs/adr/0045-split-by-context-measure-before-fold.md), [ADR-0046](../docs/adr/0046-autopilot-build-complete-harden.md), [ADR-0047](../docs/adr/0047-build-loop-until-audit-clean.md), [ADR-0048](../docs/adr/0048-optimize-skill-and-field-loop.md), [ADR-0050](../docs/adr/0050-raise-dir-size-caps.md), [PLAN harden hiện có](../docs/autopilot/PLAN-harden-2026-10-26d.md), [báo cáo mutation](../docs/ops/MUTATION-2026-10-26.md), [`loop-design.md`](../framework/11-autonomous-loop/loop-design.md), [`optimization-loop.md`](../framework/11-autonomous-loop/optimization-loop.md), [`stop-points-and-escalation.md`](../framework/11-autonomous-loop/stop-points-and-escalation.md). Báo cáo này bổ sung khoảng trống trên mốc mới, không thay sổ audit hoặc tự đóng nợ cũ.

## 14. Chưa xác minh và giới hạn

- Đọc được qua REST công khai không xác thực 2026-10-26: `seeker19110/X-Templates` là **public** (`private: false`), ruleset chỉ có một (`main`, target branch, active); event policy Actions không đọc được từ phiên này (proxy chặn đường `/actions/permissions`, 403). Vậy rule mặc định tắt `pull_request_target` **sẽ áp** từ 2026-12-02 trừ khi chủ repo đặt event policy; `pr-review.yml` là workflow duy nhất của repo khung dùng sự kiện này (chưa bật). Chưa đọc quyền/token/App của dự án đích; snapshot TARGETS/PROGRESS không phải trạng thái hôm nay.
- Chưa chạy pilot ba vòng trên task thật, chưa đo token/chi phí, mức giảm can thiệp hay hiệu quả production. Tần suất thật của R4 (mất cập nhật) trong phiên chưa đo; R5 là ca dựng, không phải log phiên thật.
- Output `claude -p --output-format json` đã chạy một lần (§13.2 mục 5) — một mẫu, không phải hợp đồng; nhiều trường đo tiến trình docs không liệt kê, không dựa vào. `usage` trong từng dòng transcript chỉ có bằng chứng gián tiếp (changelog 2.1.307); `/cost` còn là lệnh hay alias chưa rõ (docs costs chỉ nêu `/usage`); changelog thiếu mục 2.1.297/298 không rõ lý do; hai bài Anthropic trích qua WebFetch, dùng chính thức phải đọc lại trang gốc.
- Chưa xác minh độc lập nội dung nghiên cứu ngoài cũ nếu không nằm trong 21 dòng nguồn ở §13. Số trần 6 lần/task (§4B) và cấu trúc JSON §9 là đề xuất để pilot đo, không phải số đã chứng minh.

Không có cơ sở hứa "tự động 100 %", "nhanh gấp X" hoặc bỏ nghiệm thu spec/UX/bảo mật của người dùng. Mức tự chủ có thể nâng ngay là **tự chuẩn bị đầy đủ, tiếp tục đúng chỗ, dừng đúng lúc khi không tiến triển, và dừng với gói chờ quyết cụ thể**; vận hành lúc không có phiên và tự kích hoạt từ production là chặng riêng cần dữ liệu và cấu hình quyền phù hợp.
