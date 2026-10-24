# Phụ thuộc và license (`BASE-DEP-005`)

> Xác minh ngày **2026-10-20** (`shellcheck-py`: **2026-10-21**). Phạm vi: mọi gói, kể cả bắc cầu, trong ba file ghim kèm hash: `requirements-dev.txt`
> (cổng chất lượng: ruff, mypy, coverage, shellcheck-py), `requirements-audit.txt` (pip-audit, job quét phụ thuộc) và
> `requirements-e2e.txt` (Playwright, job `app-e2e` — xác minh 2026-10-21), cùng mã chép vào repo của E2E (axe-core). Khung chạy
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
  Hash: `uv pip compile --python-version 3.11 --generate-hashes --universal` trên `req.in` có thêm
  `shellcheck-py==0.11.0.1`, rồi chỉ chép khối `shellcheck-py` vào file khoá (giữ nguyên ghim cũ); đối chiếu sha256 với
  `https://pypi.org/pypi/shellcheck-py/0.11.0.1/json` (4 wheel macOS x86_64/arm64, manylinux x86_64, win_amd64 + sdist)
  và cài thử `pip install --require-hashes -r requirements-dev.txt` trong venv tạm. Linux aarch64 không có wheel → pip
  dựng từ sdist (tải binary lúc build — chưa thử trên aarch64).
- **Python CI mặc định 3.14, sàn 3.11 (T-1831):** `setup-python` cài `3.11` + `3.14` trong mỗi job (3.13 chỉ còn vá bảo mật
  từ 2026-10-01 — xác minh 2026-10-21, research §4.3). `requirements-dev.txt` (khoá `--universal`, tạo bằng 3.11) đã có hash
  wheel cp314 cho đủ 9 gói: `uv pip install --python <venv 3.14.6> --require-hashes --only-binary=:all: -r requirements-dev.txt`
  exit 0, không gói nào phải dựng từ sdist (kiểm cục bộ 2026-10-21). `COVERAGE_CORE=sysmon` bật ở shard `test` và job
  `coverage`: cục bộ trên 3.14.6 `dev-task.sh test` vẫn 100 % dòng + nhánh (exit 0), chưa đo trên CI; CI `coverage` đỏ dưới
  100 % thì bỏ biến và ghi D-NNN.
- **zizmor 1.31.1 trong `requirements-audit.txt` (T-1833, CL-5):** lint workflow GitHub Actions (MIT, wheel manylinux trên PyPI;
  xác minh 2026-10-21, research §4.3). Job `dep-audit` chạy `zizmor --offline --persona regular --min-severity high
  .github/workflows` (không gọi API, không cần token; đỏ khi có finding high). Máy dev chạy bằng `zizmor` trần phải đặt
  `ZIZMOR_OFFLINE=true` hoặc có token GitHub, nếu không audit `artipacked` báo 401 khi liệt kê tag. Cục bộ 2026-10-21:
  cài `--require-hashes` vào venv tạm exit 0; quét 9 workflow: 0 finding (16 ignored, 13 suppressed). Chỉ chạy trên runner CI/dev, không phân phối kèm.
- **E2E app cục bộ (T-1992, D-133):** `requirements-e2e.txt` (Playwright for Python và bắc cầu) chỉ cài ở job CI
  `app-e2e` và máy dev chạy `tests_e2e/`; không nằm trong `xt.yaml` (`test`/`gate`), không phải phụ thuộc runtime của
  `xt.py app` (vẫn chỉ stdlib), không phân phối kèm khung hay dự án đích. Hash = sha256 từ PyPI JSON từng phiên bản (xác
  minh 2026-10-21), mọi wheel Linux x86_64 cho CPython 3.11–3.14; `pyee` tách theo marker (`13.0.1` cho Python < 3.12,
  `14.0.0` cho ≥ 3.12 — `pyee` 14 đòi ≥ 3.12, Playwright 1.64.0 đòi `pyee>=13,<15`). Kiểm cục bộ 2026-10-21:
  `pip install --require-hashes -r requirements-e2e.txt` vào venv 3.13 và 3.11 exit 0; `license-check --requirements
  requirements-e2e.txt` exit 0 ở cả hai; `pip-audit --require-hashes --strict --disable-pip -r requirements-e2e.txt` 0 lỗ
  hổng. Trình duyệt (Chrome Headless Shell bản Playwright ghim, `playwright install --with-deps --only-shell chromium`)
  chỉ tải trên runner, không vào repo. Telemetry Playwright: chưa có tuyên bố chính thức (research
  `research/2026-10-21-app-e2e.md` §1.14).
- **axe-core 4.14.0 (MPL-2.0) — mã chép vào repo, không phải gói pip:** `tests_e2e/vendor/axe/axe.min.js` nguyên văn từ
  tarball npm (sha256 `20c09fe157a8a34a30e241aaa1fcdade657734f08ab379ecfbeb7d45cc46e878`), kèm `LICENSE`,
  `LICENSE-3RD-PARTY.txt` (từ tarball) và `SOURCE` (URL, phiên bản, sha256, `License:`) theo `CMP-LIC-022`; kiểm
  `python3 scripts/xt.py vendor-check --dirs tests_e2e/vendor --strict` exit 0. Chỉ test nạp nó (qua `page.route`, cùng
  origin, CSP của app không đổi); không nằm trong `scripts/app`, không chép sang dự án đích; không sửa tệp nên nghĩa vụ
  MPL-2.0 là giữ nguyên tệp + thông báo bản quyền và chỉ nguồn. `license-check` chỉ đọc gói pip nên không cần ngoại lệ
  trong `license-allow.json`. Quyết định D-133.
- Gói mới hoặc đổi license khi Dependabot nâng phiên bản: cập nhật bảng này trong cùng PR (`BASE-DEP-006`).
- Máy kiểm: allowlist và ngoại lệ (`approved_by`, `expires`) ở [`license-allow.json`](../../license-allow.json);
  `python3 scripts/xt.py license-check` (trong `lint` của `xt.yaml`) đối chiếu gói đã cài của `requirements-dev.txt`,
  vi phạm hoặc ngoại lệ quá hạn → exit 1. `requirements-audit.txt` kiểm khi đã cài: `--requirements requirements-audit.txt`.

## `requirements-dev.txt`

| Gói | Bản | License |
|---|---|---|
| ast-serialize | 0.13.0 | MIT |
| coverage | 7.16.2 | Apache-2.0 |
| librt | 0.16.0 | MIT |
| mypy | 2.4.0 | MIT |
| mypy-extensions | 1.1.0 | MIT |
| pathspec | 1.1.1 | MPL-2.0 (classifier PyPI; chấp nhận — xem trên) |
| ruff | 0.17.1 | MIT |
| shellcheck-py | 0.11.0.1 | MIT (binary `shellcheck` kèm theo: GPL-3.0, chỉ chạy dev/CI — xem trên) |
| typing-extensions | 4.16.0 | PSF-2.0 |

## `requirements-audit.txt`

| Gói | Bản | License |
|---|---|---|
| boolean-py | 5.0 | BSD-2-Clause |
| cachecontrol | 0.14.4 | Apache-2.0 |
| certifi | 2026.10.19 | MPL-2.0 (chấp nhận — xem trên) |
| charset-normalizer | 3.5.2 | MIT |
| cyclonedx-python-lib | 11.12.0 | Apache-2.0 |
| defusedxml | 0.7.1 | PSFL |
| filelock | 4.2.4 | MIT |
| idna | 3.20 | BSD-3-Clause |
| license-expression | 30.4.4 | Apache-2.0 |
| markdown-it-py | 4.2.0 | MIT |
| mdurl | 0.1.2 | MIT |
| msgpack | 1.2.3 | Apache-2.0 |
| packageurl-python | 0.17.6 | MIT |
| packaging | 26.3 | Apache-2.0 OR BSD-2-Clause |
| pip | 26.2.1 | MIT |
| pip-api | 0.0.35 | Apache-2.0 |
| pip-audit | 2.10.1 | Apache-2.0 |
| pip-requirements-parser | 32.0.1 | MIT |
| platformdirs | 4.13.3 | MIT |
| py-serializable | 2.1.0 | Apache-2.0 |
| pygments | 2.21.0 | BSD-2-Clause |
| pyparsing | 3.3.3 | MIT |
| requests | 2.34.2 | Apache-2.0 |
| rich | 15.0.0 | MIT |
| sortedcontainers | 2.4.0 | Apache-2.0 |
| tomli | 2.5.0 | MIT |
| tomli-w | 1.2.0 | MIT |
| typing-extensions | 4.16.0 | PSF-2.0 |
| urllib3 | 2.8.0 | MIT |
| zizmor | 1.31.1 | MIT |

## `requirements-e2e.txt` và mã vendored của E2E

| Gói | Bản | License | Dùng ở |
|---|---|---|---|
| playwright | 1.64.0 | Apache-2.0 | job CI `app-e2e`, máy dev (`tests_e2e/`) |
| greenlet | 3.5.6 | MIT AND PSF-2.0 | như trên (bắc cầu của playwright) |
| pyee | 13.0.1 (Python < 3.12) · 14.0.0 (≥ 3.12) | MIT | như trên (bắc cầu) |
| typing-extensions | 4.16.0 | PSF-2.0 | như trên (bắc cầu của pyee) |
| axe-core (vendored, `tests_e2e/vendor/axe/`) | 4.14.0 | MPL-2.0 (chấp nhận — xem trên) | chỉ test E2E, không phân phối kèm |

## Cách tạo lại

```bash
python3 -m venv /tmp/lic && /tmp/lic/bin/pip install --require-hashes -r requirements-dev.txt
/tmp/lic/bin/python -c "import importlib.metadata as m; [print(d.metadata['Name'], d.version, d.metadata.get('License-Expression') or d.metadata.get('License'), [c for c in d.metadata.get_all('Classifier', []) if c.startswith('License')]) for d in m.distributions()]"
```
