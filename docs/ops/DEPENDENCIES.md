# Phụ thuộc và license (`BASE-DEP-005`)

> Xác minh ngày **2026-10-20**. Phạm vi: mọi gói, kể cả bắc cầu, trong hai file ghim kèm hash: `requirements-dev.txt`
> (cổng chất lượng: ruff, mypy, coverage) và `requirements-audit.txt` (pip-audit, job quét phụ thuộc). Khung chạy
> `scripts/xt.py` chỉ bằng thư viện chuẩn Python; các gói dưới đây chỉ chạy trên runner CI/máy dev, không phân phối
> kèm khung hay dự án đích, không sửa mã gói.
> Nguồn license: `requirements-dev.txt` — metadata gói đã cài (`importlib.metadata`: `License-Expression`, `License`,
> classifier); `requirements-audit.txt` — metadata PyPI đúng phiên bản ghim (`https://pypi.org/pypi/<gói>/<bản>/json`).

## Quyết định

- Allowlist: MIT · BSD-2-Clause · BSD-3-Clause · Apache-2.0 · PSF-2.0 · PSFL (`defusedxml`) — đều OSI/FSF chấp nhận.
- **Chấp nhận có điều kiện:** `pathspec` và `certifi` — MPL-2.0 (copyleft yếu, theo từng file). Dùng nguyên bản từ PyPI,
  không sửa, không phân phối lại, chỉ chạy trên runner CI/máy dev nên nghĩa vụ chia sẻ mã nguồn sửa đổi không phát sinh.
  Đổi cách dùng (nhúng/phân phối) thì phải xét lại. Quyết định D-103 (phiên chính tự duyệt theo ADR-0008, hạn 12 tháng; chủ repo đổi được).
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
| filelock | 4.2.0 | MIT |
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

## Cách tạo lại

```bash
python3 -m venv /tmp/lic && /tmp/lic/bin/pip install --require-hashes -r requirements-dev.txt
/tmp/lic/bin/python -c "import importlib.metadata as m; [print(d.metadata['Name'], d.version, d.metadata.get('License-Expression') or d.metadata.get('License'), [c for c in d.metadata.get_all('Classifier', []) if c.startswith('License')]) for d in m.distributions()]"
```
