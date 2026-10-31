# PLAN-harden-2026-10-31.md — Khung X-Templates · sửa 🟠 audit delta `6799550..78fb359` trước 3.30.0

> Lập ngày 2026-10-31 theo `/complete` (pha harden), sau [`AUDIT-REPORT-2026-10-31-delta.md`](../ops/AUDIT-REPORT-2026-10-31-delta.md).
> Duyệt: D-268 (phiên chính tự duyệt, `xt.py loop decide`).
>
> **Cú pháp bắt buộc cho máy:** mỗi task một dòng `- [ ] \`T-NNNN\` <việc> — Gate: \`<lệnh>\``.

## Tóm tắt (cổng duyệt)
- Hiện trạng: `main` `78fb359` + #359; audit delta 8 nhóm `đã quét`, 0 🔴, 10 🟠 mở (6 audit, 2 review #359, AUD-SEC-180/181 có từ trước), 🟢 nợ review #357 (AUD-SEC-177…179, 182, 183).
- Phạm vi: lát A guard dấu review (🟠 180/181/186 + 🟢 nợ #357) · lát B guard sổ giai đoạn + cờ gộp `gh pr` · lát C `xt.py` monorepo (vân tay, `pr debt`) · lát D gói nghiệm thu · lát E tài liệu (2 🟠 review #359 + 🟢 tài liệu). Sau đó cắt 3.30.0 (33 mục mới, 7 MUST@L — AGENTS.md §7).
- Không làm trong PLAN này: 🟢 audit còn lại ngoài các lát trên (giữ `mở`, chủ: `/complete` kế); `perf trial` (lát 3 PLAN-harden-2026-10-27-loops, D-258).
- Cách làm: mỗi lát một PR ≤ ~150 dòng mã, test tái hiện đỏ trước khi sửa; `executor-deep` viết (guard/monorepo là rủi ro cao), `reviewer-alt` rà ở head; lát độc lập về file chạy song song trong worktree, PR tuần tự (một nhánh).
- Rủi ro: luật guard chặt hơn → chặn oan; đỡ bằng `autonomy-bench` (0 chặn oan) + ca dương trong test. Đường lùi: revert PR của lát.

## Ngân sách (4 con số)
- Số vòng tối đa: 120 · Chi phí: 0 đồng ngoài phiên · Timeout Gate: 900 giây · Hạn: 24 giờ sau `loop init`

## Điểm dừng bắt buộc (`loop defer`)
- Ký GO-NO-GO 3.30.0 (dòng 20) — người.

## Task
### Lát A — guard: dấu review đăng tay
- [ ] `T-3588` Sửa AUD-SEC-180 🟠: stdin của `gh` chuyển hướng ở cấp shell/nhóm lệnh (`exec < f; gh …`, `{ gh …; } < f`) là nguồn thân (exec: deep; files: .claude/hooks/guard.py, tests/test_guard_audit1019.py) — Gate: `python3 -m unittest -q -k test_review_marker_shell_stdin tests.test_guard_audit1019`
- [ ] `T-3589` Sửa AUD-SEC-181 🟠: backtick lệch cặp do backtick nguyên văn đứng trước — không ghép được thì coi nguồn không đọc được → chặn (sau: T-3588; exec: deep; files: .claude/hooks/guard.py, tests/test_guard_audit1019.py) — Gate: `python3 -m unittest -q -k test_review_marker_backtick_skew tests.test_guard_audit1019`
- [ ] `T-3592` Sửa AUD-SEC-186 🟠: mọi file là đối số (không phải tuỳ chọn) của lệnh trong `$(…)`/backtick của đối số `gh` đăng chữ là nguồn thân (`grep . f`, `sed '' f`, `awk 1 f`, `cut`, `more`) (sau: T-3589; exec: deep; files: .claude/hooks/guard.py, tests/test_guard_audit1019.py) — Gate: `python3 -m unittest -q -k test_review_marker_any_reader tests.test_guard_audit1019 && python3 scripts/xt.py autonomy-bench`
- [ ] `T-3594` Trả nợ review #357 🟢 AUD-SEC-177/178/179/182/183 (trần 256 KiB chặn oan, tên file có ngoặc, `xargs -I{}`, quét chữ thô, `/dev/null` symlink) (sau: T-3592; exec: deep; files: .claude/hooks/guard.py, tests/test_guard_audit1019.py) — Gate: `python3 -m unittest -q -k test_review_marker_debt_357 tests.test_guard_audit1019 && python3 scripts/xt.py autonomy-bench`
### Lát B — guard: sổ giai đoạn, cờ gộp `gh pr`
- [ ] `T-3583` Sửa AUD-HAR-154 🟠: thư mục tổ tiên của `docs/autopilot/STAGE.json` (rm/mv/git rm/git mv/checkout pathspec) và đích là thư mục có sẵn của cp/mv/ln/install (nối basename) là evidence (sau: T-3594; exec: deep; files: .claude/hooks/guard.py, tests/test_stage.py) — Gate: `python3 -m unittest -q -k test_stage_ledger_parent_dir tests.test_stage && python3 scripts/xt.py autonomy-bench`
- [ ] `T-3593` Sửa AUD-SEC-188 🟠: `_gh_pr_text_args` đọc cờ ngắn gộp kiểu pflag (`-dt`, `-db`, `-dF`) như `_gh_pr_titles` (sau: T-3583; files: .claude/hooks/guard.py, tests/test_hooks.py) — Gate: `python3 -m unittest -q -k test_attribution_combined_short_flags tests.test_hooks`
### Lát C — `xt.py` khi dự án ở thư mục con
- [ ] `T-3581` Sửa AUD-HAR-149 🟠: `evidence_fingerprint`/`_changed_since`/`_stage_changed` so đường dẫn tính từ dự án (`ls-tree … -- .`, `--relative`) (exec: deep; files: scripts/xt.py, tests/test_next_step.py) — Gate: `python3 -m unittest -q -k test_monorepo_fingerprint tests.test_next_step`
- [ ] `T-3584` Sửa AUD-HAR-155 🟠: `_review_drift` đọc sổ `head:./…` và miễn sổ theo tiền tố dự án (sau: T-3581; exec: deep; files: scripts/xt.py, tests/test_merge.py) — Gate: `python3 -m unittest -q -k test_debt_monorepo tests.test_merge`
### Lát D — gói nghiệm thu
- [ ] `T-3582` Sửa AUD-HAR-151 🟠: gói còn khớp vân tay hợp thêm `rel.human` mới khi kết quả `release-check` tươi (sau: T-3584; files: scripts/xt.py, tests/test_next_step.py) — Gate: `python3 -m unittest -q -k test_signoff_fresh_release_human tests.test_next_step`
### Lát E — tài liệu (review #359)
- [ ] `T-3579` Sửa AUD-DOC-123 🟠 + AUD-DOC-125: `LOOP-CI-020` canary đọc sentinel bằng công cụ agent được cấp, kiểm `tool_use` trong log cùng job; trigger mặc định là nhánh mặc định (files: framework/11-autonomous-loop/self-healing-ci.md) — Gate: `python3 scripts/xt.py validate && python3 scripts/check-links.py && grep -q 'tool_use' framework/11-autonomous-loop/self-healing-ci.md`
- [ ] `T-3580` Sửa AUD-DOC-124 🟠 + AUD-DOC-126/127/129: `AI-PROTO-019` từ cấm gồm `card`/`pass`/`passcode`/`passphrase`/`pwd`/`pin`/`cvc`/`iban` + số nhiều; `AI-GUARD-018` U+180E, CONTEXTJ (RFC 5892), variation selector; nguồn có ngày (AUD-DOC-128) (files: framework/13-ai-engineering/protocols-mcp-a2a.md, framework/13-ai-engineering/guardrails-and-safety.md, framework/11-autonomous-loop/self-healing-ci.md, framework/12-security/supply-chain.md, framework/07-frontend/performance-web-vitals.md, framework/10-workflow/ci-cd-pipeline.md) — Gate: `python3 scripts/xt.py validate && python3 scripts/check-links.py && grep -q 'passphrase' framework/13-ai-engineering/protocols-mcp-a2a.md && grep -q '5892' framework/13-ai-engineering/guardrails-and-safety.md`
