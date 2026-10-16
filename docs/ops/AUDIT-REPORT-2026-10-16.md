# AUDIT-REPORT — Khung X-Templates · 2026-10-16

> Commit: `58b8c8b` (`main` sau #57) · Phạm vi: delta `8e64aac`→`58b8c8b` (16 commit #43–#57, ~4.800 dòng mã) cho
> ARCH/SEC/CODE/TEST/PERF/CFG/DOC/XFEAT/HAR; CI từ `05ec95d` · Người quét: phiên chính + 3 subagent read-only
> (`reviewer` ×2, `Explore`) · Xác minh đối kháng: 2 `reviewer` model khác, tái hiện bằng script riêng
> · `xt.py audit check docs/ops/AUDIT-STATUS.md` → exit 0 (`--strict` đỏ: 15 🟠 mở)

## 1. Tóm tắt

| Mức | Mở | Đã sửa | Chấp nhận | Bác bỏ |
|---|---|---|---|---|
| 🔴 | 0 | | | |
| 🟠 | 15 | | | |
| 🟢 | 35 | | | |

Kết luận: không có gì chặn phát hành ở mặc định (`merge_autonomy: L1`). 15 🟠 tập trung ở ba chỗ:

- **Merge tự động** (6): bật L2 lúc này **không an toàn**, vì có các lối merge không qua `merge-check` và vị từ làn nhanh để lọt file cổng.
- **Guard Bash** (6): lệnh bọc trong shell, publish/deploy, xoá file hook hay test đều lọt.
- **Bằng chứng/cổng giả xanh, tài liệu** (3).

Lưu ý: bảng trên chỉ đếm phát hiện của lần quét này; sổ đếm cả các lần trước.

## 2. Phạm vi và tín hiệu (`xt.py audit plan`)

- 267 file · python 12, shell 8 · 8 file test · 7 workflow · 224 file `.md` · REPO KHUNG.
- Không có UI và CSDL → A11Y, DATA là N/A (lý do giữ nguyên trong sổ). PERF rút gọn: đo thời gian các lệnh chính.
- DEP không đổi manifest từ `5627657` → không quét lại; vẫn chạy pip-audit để chắc chắn (sạch).
- `stale_evidence`: 60 mục blueprint trích file đã đổi; kiểm 31 mục → 19 đúng, 9 lệch số dòng, 3 sai (AUD-HAR-033).
- Công cụ phải cài thêm cho lần quét (scratchpad, ghim phiên bản): shellcheck 0.11.0, gitleaks 8.28.0,
  actionlint 1.7.7, zizmor 1.14.2, bandit 1.8.6, vulture 2.14, pip-audit 2.10.1.

## 3. Lệnh đã chạy

| Nhóm | Lệnh | Exit | Kết quả chính |
|---|---|---|---|
| tất cả | `scripts/dev-task.sh gate` | 0 | 441 test OK, coverage dòng + nhánh 100% (3210 dòng, 1320 nhánh), 85 s |
| HAR | `python3 scripts/xt.py doctor --json` | 0 | 0 phát hiện |
| HAR | `python3 scripts/xt.py blueprint-status BLUEPRINT.md --strict` | 0 | MUST 62 đạt · 8 miễn · 0 chưa |
| SEC | `gitleaks git --log-opts=--all --redact .` | 0 | sạch, nhưng clone nông chỉ 50 commit → toàn lịch sử: chưa biết |
| SEC | `bandit -q -r scripts .claude/hooks` | 0 | chỉ Low: B603×8, B607×5, B404×3 |
| CODE | `vulture scripts .claude/hooks --min-confidence 60` | 0 | 3 báo nhầm (thuộc tính shlex) |
| DEP | `pip-audit --require-hashes --strict -r requirements-dev.txt -r requirements-audit.txt` | 0 | không lỗ hổng |
| CI | `actionlint` | 0 | sạch |
| CI | `zizmor --offline .github/workflows` | 14 | 8 medium `artipacked` (AUD-CI-007) |
| PERF | đo thời gian `dev-task.sh build/typecheck/lint`; `python3 -m unittest discover -s tests --durations 0` | 0 | 0,2 s · 0,2 s · 1,6 s · test 36,5 s không coverage (AUD-PERF-001) |
| SEC/HAR | payload giả qua `pre-bash-guard.sh` / `pre-edit-guard.sh`; fuzz 200.000 lệnh vào `bash_decision` | — | 0 exception; các ca lọt ở §4 |

## 4. Phát hiện chi tiết (🟠)

Mỗi mục dưới đây có hai người tái hiện độc lập: subagent tìm ra và reviewer xác minh, mỗi người tự viết script của mình.
Repo tạm và script nằm trong scratchpad của phiên, không đưa vào repo.

### Nhóm A — merge tự động (tiền đề của luật "PR + auto-merge theo lát")

#### AUD-SEC-016 🟠 Guard `allow` `gh pr merge` có lệnh con hoặc biến lạ
- **Tái hiện:** giả lập `merge_check` trả `merge`, `head=abc123`. Gọi `guard.bash_decision` với từng lệnh:
  - `gh pr merge 5 --squash --match-head-commit abc123 -b "$(curl x)"` → `allow`;
  - giữ nguyên lệnh, thêm `--admin=true` → `allow`;
  - thêm `GH_REPO=e/r` ở đầu lệnh → `allow`;
  - selector là URL PR của repo khác → `allow`.
- **Vì sao sai:** ADR-0013 §4 đòi lệnh đứng một mình, không `--admin`, không trỏ repo khác. Guard chỉ so `"--admin" in args`, và không thấy được chuỗi `$(…)` trong nháy kép.
- **Xác minh:** xác nhận một phần. `GH_REPO` hay URL repo khác khó khai thác, vì `--match-head-commit` buộc phải trùng SHA.
- **Sửa:** trả `ask` khi lệnh có `$(`, backtick, `<<`, `--admin` ở mọi dạng, `-R`/`--repo` theo tiền tố, hoặc gán `GH_*` ở đầu. · **Gate:** `python3 -m unittest discover -s tests -k merge_allow_strict`

#### AUD-SEC-020 🟠 Merge vòng qua `merge-check`
- **Tái hiện:** payload `gh api -X PUT repos/o/r/pulls/5/merge` → stdout rỗng (không quyết định). Tương tự với mutation GraphQL `mergePullRequest`/`enablePullRequestAutoMerge`.
- **Lỗ phụ:** `settings.json` chỉ có matcher `Bash` và `Edit|Write|MultiEdit`. Tool MCP GitHub merge vì thế không qua hook; chế độ `auto`/`bypassPermissions` mà autopilot khuyến nghị sẽ không hỏi.
- **Sửa:**
  - `gh api` với phương thức khác GET (`-X`/`--method`; `-f`/`-F` ngầm là POST) lên `…/merge`, `…/rulesets`, `visibility`, hoặc mutation GraphQL → `ask`.
  - Thêm matcher `mcp__.*` có luật cho tool merge/auto-merge.
- **Gate:** `python3 -m unittest discover -s tests -k guard_gh_api_merge`

#### AUD-HAR-021 🟠 Làn nhanh để lọt file luật agent và cổng
- **Tái hiện:** `xt.yaml` có `merge_autonomy: L2`. Chạy `xt.py merge-check --pr-json F --json`, CI xanh, `CLEAN` → `merge` với từng PR sau:
  - `AGENTS.md` +200/−80 cùng `CLAUDE.md`;
  - `scripts/dev-task.sh` cùng một test;
  - `vitest.config.ts`, `.pre-commit-config.yaml`, `.gitleaks.toml` hoặc `ruff.toml`, mỗi file kèm test.
- **Đối chứng:** PR sửa `.github/workflows/ci.yml` → `human`.
- **Nguyên nhân:** `RISK_PATH_RES` của xt.py lệch `GATE_PATTERNS` của guard — một khái niệm giữ ở hai nhà. Thêm vào đó, `.md` không được xét rủi ro.
- **Sửa:** dùng một nguồn danh sách đường dẫn cổng chung cho cả hai, gồm `AGENTS.md` và `CLAUDE.md`. · **Gate:** `python3 -m unittest discover -s tests -k merge_gate_paths`

#### AUD-HAR-022 🟠 Đổi tên workflow ra khỏi `.github/` vẫn làn nhanh
- **Tái hiện:** gh giả trả file `{"filename":"scripts/quality.yml.off","previous_filename":".github/workflows/quality.yml","status":"renamed"}` → `merge, lane: nhanh`. Xoá chính file đó → `human`.
- **Sửa:** `_pr_rest` giữ `previous_filename` và xét rủi ro trên cả hai tên. · **Gate:** `python3 -m unittest discover -s tests -k merge_renamed_risk_path`

#### AUD-HAR-023 🟠 Chỉ có check SKIPPED/NEUTRAL bị tính là CI xanh
- **Tái hiện:** rollup gồm 2 check `completed/skipped` → `merge`; dùng `neutral` → `merge`; không có check nào → `human`.
- **Sửa:** cần ít nhất một check SUCCESS, nếu không → `human`. · **Gate:** `python3 -m unittest discover -s tests -k merge_skipped_only`

### Nhóm B — guard Bash

#### AUD-SEC-015 🟠 Cổng commit chạy mã của repo lạ
- **Tái hiện:**
  1. `git init` một repo lạ, đặt `scripts/dev-task.sh` ghi ra một file.
  2. Gửi payload `cd <repo lạ> && git commit -m x` vào `pre-bash-guard.sh` → file được tạo, rc 0.
  3. Payload `git -C <repo lạ> commit -m x` → cùng kết quả.
- **Nguyên nhân:** `pre-bash-guard.sh:27-43` lấy gốc cổng là repo nhận commit. Bản sửa AUD-HAR-013 có chủ đích như vậy, nhưng không tính tới trường hợp repo không tin cậy.
- **Sửa:** repo nằm ngoài gốc dự án thì không chạy cổng của nó → `ask`. · **Gate:** `python3 -m unittest discover -s tests -k commit_gate_foreign_repo`

#### AUD-SEC-017 🟠 Lệnh phá huỷ bọc trong shell lọt
- **Tái hiện:** các lệnh sau đều không có quyết định:
  - `bash -c 'git push --force origin x'`, `sh -c "rm -rf ~"`, `zsh -c 'git push -f …'`;
  - `bash <<'E'` … `git reset --hard` … `E`;
  - `echo 'git reset --hard' | bash`.
- **Đối chứng:** cùng các lệnh gọi trực tiếp → `deny`.
- **Vì sao không phải giới hạn đã biết:** giới hạn ghi ở CHANGELOG chỉ có `eval`, alias và biến chứa cờ. Luật hook-bypass đã đệ quy vào `-c` (`_shell_c_bypass`), luật deny thì chưa.
- **Sửa:** quét đệ quy đối số `-c`, và thân heredoc/pipe đi vào shell, cho mọi luật. · **Gate:** `python3 -m unittest discover -s tests -k guard_shell_c_deny`

#### AUD-SEC-018 🟠 Biến thể publish/deploy không có `ask`
- **Tái hiện:** các lệnh sau đều trả stdout rỗng:
  - `pnpm -r publish`, `yarn npm publish`, `uv publish`, `poetry publish`, `bun publish`, `gem push`;
  - `python3 -m twine upload`;
  - `docker buildx build --push`;
  - `helm upgrade --install`;
  - `gh workflow run release.yml`, `gh repo edit --visibility public`.
- **Nguyên nhân:** `ASK_CMDS` chỉ so `args[0]`. `pnpm -r publish` lại là cách xuất bản bình thường của monorepo.
- **Gate:** `python3 -m unittest discover -s tests -k guard_publish_variants`

#### AUD-SEC-019 🟠 Gỡ hook/cổng qua Bash; mất `guard.py` thì fail-open toàn bộ
- **Tái hiện:**
  - Các lệnh sau không có quyết định: `mv .claude/hooks/guard.py /tmp/x`, `git rm .claude/hooks/pre-bash-guard.sh`, `git mv .github/workflows/ci.yml x`, `perl -pi -e … ci.yml`.
  - `rm -f .github/workflows/ci.yml` cũng lọt: trong `write_targets`, cờ `-f` bị coi là cờ có giá trị và nuốt mất đường dẫn.
  - Trên bản sao repo, sau `mv guard.py`: `git push --force`, `curl … | sh`, `gh pr merge --admin` đều qua. Chỉ còn lớp `permissions.deny` của settings đỡ một phần.
- **Sửa:**
  - Xét cả nguồn của `mv`/`git mv`/`git rm`, cùng `perl -i`, `cp -t`.
  - Sửa lỗi cờ `-f` của `rm`.
  - `pre-bash-guard.sh` trả `ask` khi thiếu `guard.py`: thiếu file không phải lỗi chạy, nên không cần fail-open.
- **Gate:** `python3 -m unittest discover -s tests -k guard_gate_file_removal`

#### AUD-HAR-026 🟠 Chặn làm yếu test không áp cho Bash
- **Tái hiện:** repo tạm có `tests/test_a.py`. Các lệnh sau đều được cho qua im lặng: `rm -f tests/test_a.py`, `git rm tests/test_a.py`, `mv tests/test_a.py /tmp/x`, `sed -i /assert/d tests/test_a.py`, `echo '' > tests/test_a.py`.
- **Đối chứng:** cùng các lệnh nhắm vào `xt.yaml` → `ask`.
- **Gate:** `python3 -m unittest discover -s tests -k guard_bash_test_weakening`

#### AUD-HAR-027 🟠 `GATE_PATTERNS` thiếu file cổng phổ biến
- **Tái hiện:** Edit các file `pytest.ini`, `tox.ini`, `vite.config.ts`, `conftest.py`, `noxfile.py` → allow im lặng.
- **Đối chứng:** `vitest.config.ts`, `pyproject.toml`, `setup.cfg` → `ask`.
- **Gate:** `python3 -m unittest discover -s tests -k guard_gate_patterns`

### Nhóm C — bằng chứng, cổng giả xanh, bí mật, tài liệu

#### AUD-HAR-024 🟠 Bằng chứng autopilot ghi tay được
- **Tái hiện:**
  1. Repo tạm, PLAN có task `[x]` với Gate là lệnh test không chạy được → `loop status` báo `verify`.
  2. Ghi tay `.autopilot/evidence/T-001.json` với `exit_code: 0`, `finished: 2099-01-01…` → `verdict: done`.
  3. Guard cho qua im lặng cả Write/Edit lẫn `echo >`, `tee`, `sed -i` vào `.autopilot/`.
- **Vì sao 🟠 chứ không 🔴:** phải có agent cố ý, hoặc dùng lối tắt khi `loop record` lỗi. Nhưng guard đã bảo vệ `xt.yaml` và chống tắt hook, nên bằng chứng cũng cần được bảo vệ tương tự.
- **Sửa:**
  - Thêm loại đường dẫn `evidence` (`.autopilot/*`) vào `classify_path` → `ask` khi ghi.
  - Verdict từ chối bằng chứng thiếu `head`/`started`, hoặc có `finished` ở tương lai.
- **Gate:** `python3 -m unittest discover -s tests -k evidence_tamper`

#### AUD-HAR-025 🟠 ADR-0011 bị lách bằng comment trong `xt.yaml`
- **Tái hiện:** `loop init --single-session` rồi `scripts/dev-task.sh gate`:

  | `lint:` / `test:` | Kết quả |
  |---|---|
  | `true` | ĐỎ (đúng) |
  | `lint: # TODO điền` | `GATE XANH (2 lệnh)`, rc 0, không cảnh báo |
  | `true  # TODO` | `GATE XANH (2 lệnh)`, rc 0, không cảnh báo |

- **Vì sao nặng:** đây chính là lỗ ADR-0011 muốn đóng, và xảy ra trên đường dùng bình thường (người điền mẫu `xt.yaml` có ghi chú).
- **Sửa:** bỏ ` #…` ngoài nháy trong `yaml_get` và `gate_noop_keys`; giá trị chỉ còn comment coi là rỗng. · **Gate:** `python3 -m unittest discover -s tests -k noop_trailing_comment`

#### AUD-CFG-002 🟠 Redact feedback lọt bí mật
- **Tái hiện:**
  - `xt.py feedback add --symptom 'redis://:hunter2pass@cache:6379 … npm_abcd… eyJhbGci….….' --fix 'mysql -phunter2'` → `FB-001.md` giữ nguyên các giá trị.
  - FB sửa tay có `password=hunter2` → `feedback aggregate` in nguyên văn ra cả bảng lẫn `--json`.
- **Vì sao cần sửa:** đầu ra của `aggregate` đi thẳng vào PR nháp của repo khung, mà repo này public.
- **Sửa:**
  - Thêm các mẫu còn thiếu: DSN có user rỗng, `npm_`, JWT, `-p…`, `curl -u`, `AIza…`, `hf_`, `pypi-`.
  - Gọi `redact` thêm một lần trong `aggregate`.
- **Gate:** `python3 -m unittest discover -s tests -k redact_more_secrets`

#### AUD-DOC-023 🟠 ADR-0008 áp chưa hết
- **Tái hiện:** `grep -rnE 'spec mâu thuẫn|mâu thuẫn spec|Bạn duyệt' README.md framework/10-workflow framework/17-product-project framework/11-autonomous-loop/orchestration-and-subagents.md` → 6 dòng vẫn coi mâu thuẫn spec hoặc duyệt PLAN là việc chờ người. Trong đó có `PM-PLAN-005` mức **MUST**. BLUEPRINT.md:961 chép lại câu chữ cũ đó.
- **Xác minh:** reviewer đề xuất 🟢. Tôi giữ 🟠, vì một mục MUST mâu thuẫn ADR sẽ khiến agent liệt kê sai điểm dừng trong PLAN (audit.md §4: "tài liệu sai gây làm sai").
- **Sửa:** giữ ID, sửa câu chữ, ghi CHANGELOG. · **Gate:** chính lệnh grep trên, sau khi sửa chỉ còn dạng phủ định.

### Hạ mức khi xác minh

| ID | Mức ban đầu → sau | Lý do |
|---|---|---|
| AUD-SEC-021 | 🟠 → 🟢 | chế độ quyền mặc định vẫn hỏi; thiếu python3 thì cả khung không chạy |
| AUD-CI-006 | 🟠 → 🟢 | mọi commit mới qua PR đều được quét; chỉ phần lịch sử trước khi bật workflow là chưa biết |
| AUD-HAR-029 | 🟠 → 🟢 | ADR-0011 §Hệ quả đã ghi là "việc riêng" |
| AUD-HAR-030 | 🟠 → 🟢 | chỉ làm cũ ngữ cảnh SessionStart, không làm sai cổng |
| AUD-CODE-004 | 🟠 → 🟢 | PR nháp phản hồi có người duyệt (ADR-0010) |
| AUD-HAR-028 | 🟠 → 🟢 (một phần) | heuristic regex không thể bắt đủ |

Không phát hiện nào bị bác bỏ.

## 5. Kế hoạch sửa theo đợt (chờ duyệt)

Mỗi đợt là một PR. Test tái hiện phải đỏ trước khi sửa và xanh sau khi sửa. Đợt 1 và 2 đi trước vì luật mới
"PR + auto-merge theo lát" (yêu cầu của chủ repo 2026-10-16) chỉ an toàn khi đã bịt hết lối merge vòng.

| Đợt | Phát hiện | PR dự kiến | Gate của đợt |
|---|---|---|---|
| 1 | AUD-SEC-016, SEC-020, HAR-021, HAR-022, HAR-023 (+ SEC-021: khôi phục `ask` cho `gh pr merge` khi < L2) | `fix(merge): bịt các đường merge vòng qua merge-check` | `scripts/dev-task.sh gate` + 5 test `-k` ở §4 |
| 2 | Luật mới: mỗi lát code một PR, tự merge khi `merge-check` cho phép (xem §7) | `feat(loop): PR theo lát + auto-merge (ADR-0014)` | `scripts/dev-task.sh gate` + test `merge_auto_lane` |
| 3 | AUD-SEC-015, SEC-017, SEC-018, SEC-019, HAR-026, HAR-027 | `fix(guard): shell lồng, publish, gỡ hook/test qua Bash` | `scripts/dev-task.sh gate` + 6 test `-k` |
| 4 | AUD-HAR-024, HAR-025, CFG-002 | `fix(loop): bảo vệ bằng chứng, no-op có comment, redact` | `scripts/dev-task.sh gate` + 3 test `-k` |
| 5 | AUD-DOC-023 + 🟢 tài liệu (DOC-024…030, HAR-030…033) | `docs: áp hết ADR-0008, đồng bộ tài liệu với mã` | `scripts/dev-task.sh gate` + grep AUD-DOC-023 |

Các PR đợt 1, 3 và 4 chạm `.claude/` hoặc `scripts/dev-task.sh`, tức vùng nhạy cảm (WF-REVIEW-007): **người merge**,
kể cả khi luật auto-merge đã có hiệu lực.

## 6. Nợ 🟢 giữ lại

Các 🟢 còn lại (SEC-022…026, CFG-003/004, CI-007/008, HAR-034…036, CODE-005/006, XFEAT-002, ARCH-001,
TEST-003/004, PERF-001) để `mở` và gom vào đợt 6. Nếu chủ repo muốn giữ lâu hơn thì chuyển sang `chấp nhận`,
kèm `chủ:` + `hạn:`.

## 7. Luật mới đề xuất: PR + auto-merge theo từng lát code

Yêu cầu của chủ repo (2026-10-16): "tạo PR và auto merge theo từng lát code". Hiện autopilot commit dồn trên một
nhánh rồi mới mở "PR cuối" (11-autonomous-loop/README.md bước 15); ADR-0013 chỉ cho máy merge làn nhanh ở L2.

**Phương án chọn**, ghi bằng ADR-0014 + D-NNN khi làm đợt 2:

1. **Lát = đơn vị PR.** Mỗi lát dọc chạy được (một task hoặc nhóm task PLAN có Gate xanh) có nhánh riêng tách từ
   `main` mới nhất và một PR riêng, nhỏ. Mở PR ngay khi Gate của lát xanh; bỏ "PR cuối".
2. **Auto-merge do máy quyết.** Sau khi mở PR, chạy `xt.py merge-check --pr N`:
   - `merge` → `gh pr merge N --squash --match-head-commit <sha>`;
   - verdict mới `auto` (mọi điều kiện đạt, chỉ còn CI đang chạy) → `gh pr merge N --auto --squash --match-head-commit <sha>`,
     để GitHub tự merge khi required check xanh;
   - `human` → `loop defer` và làm lát kế tiếp.
   
   Guard chỉ `allow` hai dạng lệnh trên, sau khi đã bịt các lối ở đợt 1.
3. **Ngoại lệ giữ nguyên:** vùng nhạy cảm (auth, thanh toán, migration, cổng/CI/hook, luật agent) luôn để người merge
   (WF-REVIEW-007 MUST). Lát kế tiếp phụ thuộc lát đang chờ người thì `defer`, không chồng nhánh.
4. **Bật cho repo này:** `xt.yaml` thêm `merge_autonomy: L2`. Đây là file cổng nên hook sẽ hỏi; lý do là yêu cầu trên.
   GitHub cần bật "Allow auto-merge" trong cài đặt repo — việc của chủ repo (admin, proxy của phiên không làm được).
5. **Cần xác minh trước khi làm (P2):** hành vi của `gh pr merge --auto` khi PR đã `CLEAN`, hoặc khi ruleset không có
   required check. Nếu nó merge ngay thì verdict `auto` phải đòi ruleset có required check.

**Phương án loại:** auto-merge mọi PR khi CI xanh, bỏ vị từ làn nhanh. Lý do: trái WF-REVIEW-007 MUST, và các lỗ của
nhóm A cho thấy chỉ "CI xanh" là chưa đủ.
