# Phụ thuộc và license (`BASE-DEP-005`)

> Phiên bản và hash đối chiếu khoá cùng metadata PyPI ngày **2026-11-14**. Phạm vi: mọi gói, kể cả bắc cầu, trong ba file ghim kèm hash: `requirements-dev.txt`
> (cổng chất lượng: ruff, mypy, coverage, shellcheck-py), `requirements-audit.txt` (pip-audit, job quét phụ thuộc) và
> `requirements-e2e.txt` (Playwright, job `app-e2e`), cùng mã chép vào repo của E2E (axe-core). Khung chạy
> `scripts/xt.py` chỉ bằng thư viện chuẩn Python; các gói dưới đây chỉ chạy trên runner CI/máy dev, không phân phối
> kèm khung hay dự án đích, không sửa mã gói.
> Nguồn license: `requirements-dev.txt` — metadata gói đã cài (`importlib.metadata`: `License-Expression`, `License`,
> classifier); `requirements-audit.txt` — metadata PyPI đúng phiên bản ghim (`https://pypi.org/pypi/<gói>/<bản>/json`).

## Quyết định

- Allowlist: MIT · BSD-2-Clause · BSD-3-Clause · Apache-2.0 · PSF-2.0 · PSFL (`defusedxml`) — đều OSI/FSF chấp nhận.
- **Chấp nhận có điều kiện:** `pathspec` và `certifi` — MPL-2.0 (copyleft yếu, theo từng file). Dùng nguyên bản từ PyPI,
  không sửa, không phân phối lại, chỉ chạy trên runner CI/máy dev nên nghĩa vụ chia sẻ mã nguồn sửa đổi không phát sinh.
  Đổi cách dùng (nhúng/phân phối) thì phải xét lại. Quyết định D-103 (phiên chính tự duyệt theo ADR-0008, hạn 12 tháng; chủ repo đổi được).
- **`shellcheck-py` (MIT) gói kèm binary `shellcheck` (GPL-3.0):** chỉ *chạy* binary trong `lint` trên máy dev/runner CI
  (kiểm `scripts/*.sh`), không liên kết, không sửa, không phân phối kèm khung hay dự án đích — GPL không áp nghĩa vụ lên
  mã của repo. `license-check` thấy metadata wrapper (MIT). Lý do ghim: CI từng dùng shellcheck 0.9.0 của runner, máy
  dev 0.11.0 — hai bản khác luật (research 2026-10-21 NH-2); `pip install` đặt `shellcheck` 0.11.0 vào `bin` của Python
  (đứng trước `/usr/bin` trên PATH sau `actions/setup-python`), nên `lint` cục bộ và CI cùng bản.
  Hash gốc: `uv pip compile --python-version 3.11 --generate-hashes --universal` trên `req.in` có thêm
  `shellcheck-py==0.11.0.1`, rồi chỉ chép khối `shellcheck-py` vào file khoá (giữ nguyên ghim cũ); đối chiếu sha256 với
  `https://pypi.org/pypi/shellcheck-py/0.11.0.1/json` (4 wheel macOS x86_64/arm64, manylinux x86_64, win_amd64 + sdist)
  và cài thử `pip install --require-hashes -r requirements-dev.txt` trong venv tạm. Linux aarch64 không có wheel → pip
  dựng từ sdist (tải binary lúc build — chưa thử trên aarch64).
- **CPython 3.15:** CI dùng bản ổn định 3.15.2 (phát hành 2026-10-26).
  Đối chiếu metadata `Requires-Python`, marker, phụ thuộc bắc cầu và hash wheel PyPI ngày 2026-11-14 trên Linux x86_64.
  Ba khoá giữ phiên bản của các gói dùng trên 3.15. `requirements-audit.txt` bỏ `typing-extensions` chỉ cần trước 3.13.
  Cài từng khoá vào venv CPython 3.15.2 bằng `pip install --require-hashes --only-binary=:all:` rồi chạy `pip check` đều
  exit 0 (9 gói dev, 29 gói audit, 4 gói E2E). Shard `test` và job `coverage` dùng `COVERAGE_CORE=sysmon` với ngưỡng 100 % dòng và nhánh.
  [Lịch phát hành CPython](https://peps.python.org/pep-0790/).
- **zizmor 1.32.0 trong `requirements-audit.txt` (T-1833, CL-5):** lint workflow GitHub Actions (MIT, wheel manylinux trên PyPI;
  xác minh 2026-11-14, lịch sử ở research §4.3). Job `dep-audit` chạy `zizmor --offline --persona regular --min-severity high
  .github/workflows` (không gọi API, không cần token; đỏ khi có finding high). Máy dev chạy bằng `zizmor` trần phải đặt
  `ZIZMOR_OFFLINE=true` hoặc có token GitHub, nếu không audit `artipacked` báo 401 khi liệt kê tag. Cục bộ 2026-10-21:
  cài `--require-hashes` vào venv tạm exit 0; quét 9 workflow: 0 finding (16 ignored, 13 suppressed). Chỉ chạy trên runner CI/dev, không phân phối kèm.
- **E2E app cục bộ (T-1992, D-133):** `requirements-e2e.txt` (Playwright for Python và bắc cầu) chỉ cài ở job CI
  `app-e2e` và máy dev chạy `tests_e2e/`; không nằm trong `xt.yaml` (`test`/`gate`), không phải phụ thuộc runtime của
  `xt.py app` (vẫn chỉ stdlib), không phân phối kèm khung hay dự án đích. Hash từ PyPI JSON từng phiên bản, đối chiếu
  2026-11-14. Khoá giữ 8 wheel Playwright 1.64.1 và chọn wheel Greenlet 3.5.6 cho CPython 3.15/3.15t Linux x86_64
  (manylinux và musllinux). Bản `pyee` 14.0.0 dùng trên 3.15 nằm trong dải `>=13,<15` của Playwright.
  Trình duyệt (Chrome Headless Shell bản Playwright ghim, `playwright install --with-deps --only-shell chromium`)
  chỉ tải trên runner, không vào repo. Telemetry Playwright: chưa có tuyên bố chính thức (research
  `research/2026-10-21-app-e2e.md` §1.14).
- **axe-core 4.14.0 (MPL-2.0) — mã chép vào repo, không phải gói pip:** `tests_e2e/vendor/axe/axe.min.js` nguyên văn từ
  tarball npm (sha256 `20c09fe157a8a34a30e241aaa1fcdade657734f08ab379ecfbeb7d45cc46e878`), kèm `LICENSE`,
  `LICENSE-3RD-PARTY.txt` (từ tarball) và `SOURCE` (URL, phiên bản, sha256, `License:`) theo `CMP-LIC-022`; kiểm
  `python3 scripts/xt.py vendor-check --dirs tests_e2e/vendor --strict` exit 0. Chỉ test nạp nó (qua `page.route`, cùng
  origin, CSP của app không đổi); không nằm trong `scripts/app`, không chép sang dự án đích; không sửa tệp nên nghĩa vụ
  MPL-2.0 là giữ nguyên tệp + thông báo bản quyền và chỉ nguồn. `license-check` chỉ đọc gói pip nên không cần ngoại lệ
  trong `license-allow.json`. Quyết định D-133.
- **SBOM và provenance (T-3654, AUD-DEP-010):** job `dep-audit` sinh SBOM CycloneDX (`pip-audit … -f cyclonedx-json -o
  sbom.cdx.json` — pip-audit 2.10.1 luôn ghi định dạng cyclonedx kể cả 0 lỗ hổng, đọc mã `_format/cyclonedx.py` 2026-11-02)
  và tải lên artefact `sbom-cyclonedx` (giữ 90 ngày). `release-tag.yml` ký provenance cho `git archive` của commit gắn tag
  bằng `actions/attest-build-provenance` **4.2.2** ghim `4d101475d8b20a2381f78447822ac1eab6504dd8` (MIT; tag nhẹ, phát hành
  2026-08-06; từ v4 là vỏ của `actions/attest` — README khuyên dùng `actions/attest` cho bản mới, chưa đổi vì vỏ vẫn được
  hỗ trợ; xác minh 2026-11-02). Quyền job: `id-token: write`, `attestations: write`; repo công khai dùng Sigstore
  public-good (chứng chỉ, bản ghi minh bạch công khai). Kiểm: `gh attestation verify X-Templates-vX.Y.Z.tar.gz --repo
  seeker19110/X-Templates`; tái tạo đúng byte bằng `git archive` ở máy khác: (chưa xác minh — gzip của git có thể khác
  theo bản). Chưa chạy thật trên CI tới lần cắt bản kế.
- Gói mới hoặc đổi license khi Dependabot nâng phiên bản: cập nhật bảng này trong cùng PR (`BASE-DEP-006`).
- Máy kiểm: allowlist và ngoại lệ (`approved_by`, `expires`) ở [`license-allow.json`](../../license-allow.json);
  `python3 scripts/xt.py license-check` (trong `lint` của `xt.yaml`) đối chiếu gói đã cài của `requirements-dev.txt`,
  vi phạm hoặc ngoại lệ quá hạn → exit 1. `requirements-audit.txt` kiểm khi đã cài: `--requirements requirements-audit.txt`.

## `requirements-dev.txt`

| Gói | Bản | License |
|---|---|---|
| ast-serialize | 0.13.1 | MIT |
| coverage | 7.17.2 | Apache-2.0 |
| librt | 0.16.0 | MIT |
| mypy | 2.4.1 | MIT |
| mypy-extensions | 1.2.0 | MIT |
| pathspec | 1.1.1 | MPL-2.0 (classifier PyPI; chấp nhận — xem trên) |
| ruff | 0.17.4 | MIT |
| shellcheck-py | 0.11.0.1 | MIT (binary `shellcheck` kèm theo: GPL-3.0, chỉ chạy dev/CI — xem trên) |
| typing-extensions | 4.16.0 | PSF-2.0 |

## `requirements-audit.txt`

| Gói | Bản | License |
|---|---|---|
| boolean-py | 5.0 | BSD-2-Clause |
| cachecontrol | 0.14.4 | Apache-2.0 |
| certifi | 2026.10.23 | MPL-2.0 (chấp nhận — xem trên) |
| charset-normalizer | 3.5.2 | MIT |
| cyclonedx-python-lib | 11.12.0 | Apache-2.0 |
| defusedxml | 0.7.1 | PSFL |
| filelock | 4.2.9 | MIT |
| idna | 3.20 | BSD-3-Clause |
| license-expression | 30.4.4 | Apache-2.0 |
| markdown-it-py | 4.2.0 | MIT |
| mdurl | 0.1.2 | MIT |
| msgpack | 1.2.4 | Apache-2.0 |
| packageurl-python | 0.17.6 | MIT |
| packaging | 26.3 | Apache-2.0 OR BSD-2-Clause |
| pip | 26.3 | MIT |
| pip-api | 0.0.35 | Apache-2.0 |
| pip-audit | 2.10.1 | Apache-2.0 |
| pip-requirements-parser | 32.0.1 | MIT |
| platformdirs | 4.14.5 | MIT |
| py-serializable | 2.2.0 | Apache-2.0 |
| pygments | 2.21.0 | BSD-2-Clause |
| pyparsing | 3.3.3 | MIT |
| requests | 2.34.2 | Apache-2.0 |
| rich | 15.0.0 | MIT |
| sortedcontainers | 2.4.0 | Apache-2.0 |
| tomli | 2.5.0 | MIT |
| tomli-w | 1.2.0 | MIT |
| urllib3 | 2.8.0 | MIT |
| zizmor | 1.32.0 | MIT |

## `requirements-e2e.txt` và mã vendored của E2E

| Gói | Bản | License | Dùng ở |
|---|---|---|---|
| playwright | 1.64.1 | Apache-2.0 | job CI `app-e2e`, máy dev (`tests_e2e/`) |
| greenlet | 3.5.6 | MIT AND PSF-2.0 | như trên (bắc cầu của playwright) |
| pyee | 14.0.0 | MIT | như trên (bắc cầu) |
| typing-extensions | 4.16.0 | PSF-2.0 | như trên (bắc cầu của pyee) |
| axe-core (vendored, `tests_e2e/vendor/axe/`) | 4.14.0 | MPL-2.0 (chấp nhận — xem trên) | chỉ test E2E, không phân phối kèm |

## Binary CI: bun (test plugin OpenCode), Gitleaks CLI (quét bí mật)

| Gói | Bản | License | Nguồn và hash | Dùng ở |
|---|---|---|---|---|
| `@oven/bun-linux-x64` | 1.4.4 | MIT (`license` của registry npm, đọc 2026-11-03) | tarball <https://registry.npmjs.org/@oven/bun-linux-x64/-/bun-linux-x64-1.4.4.tgz>; `BUN_SHA256` ghim trong `.github/workflows/ci.yml` (sha256 tính trên tarball, khớp `dist.integrity` sha512 của registry) | job CI chạy `tests.test_adapters` (plugin OpenCode, AUD-TEST-056); không phân phối kèm |
| Gitleaks CLI (`gitleaks_8.30.1_linux_x64.tar.gz`) | 8.30.1 | MIT (`LICENSE` upstream tại tag `v8.30.1`, đọc 2026-11-05) | <https://github.com/gitleaks/gitleaks/releases/download/v8.30.1/gitleaks_8.30.1_linux_x64.tar.gz>; `sha256` ghim trong `.github/workflows/secret-scan.yml` và `framework/templates/secret-scan.yml` (đối chiếu `checksums.txt` của bản phát hành) | job CI `gitleaks` (AUD-CI-027, AUD-CI-030) và mẫu cho dự án đích; không phân phối kèm |

Không bot nào nâng bản ghim này (Dependabot không đọc biến `env` của workflow) — nâng tay (AUD-DEP-011): chọn bản đã qua
cooldown `BASE-DEP-019`; `npm view @oven/bun-linux-x64@<X> license dist.tarball dist.integrity`; tải tarball, `sha256sum`,
đối chiếu sha512 với `dist.integrity`; sửa `BUN_VERSION` + `BUN_SHA256` trong `ci.yml` (cùng commit, nêu lý do chạm CI). Cache
tarball bằng `actions/cache` theo `BUN_SHA256`: đang cân nhắc (tải 4 lần/lượt CI), chưa làm.

Gitleaks cũng không có bot nào nâng (phiên bản và `sha256` nằm trong `run:`) — nâng tay: chọn bản đã qua cooldown `BASE-DEP-019`; đọc `checksums.txt` của bản phát hành trên trang releases; sửa `asset`, URL và `sha256` ở **cả hai** workflow (cùng commit, nêu lý do chạm CI); kiểm `LICENSE` upstream còn MIT.

## Cách tạo lại

```bash
python3 -m venv /tmp/lic && /tmp/lic/bin/pip install --require-hashes -r requirements-dev.txt
/tmp/lic/bin/python -c "import importlib.metadata as m; [print(d.metadata['Name'], d.version, d.metadata.get('License-Expression') or d.metadata.get('License'), [c for c in d.metadata.get_all('Classifier', []) if c.startswith('License')]) for d in m.distributions()]"
```
