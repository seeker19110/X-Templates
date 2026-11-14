# Fixture report: output thật của công cụ (AUD-TEST-061)

Dùng bởi `tests/test_report_fixtures.py` (adapter `report_result` của `scripts/xt.py`). Các fixture ngoài CodeQL
sinh ngày 2026-11-07 trên Linux (WSL2), Python 3.14.6, venv tạm. Không thêm phụ thuộc vào repo. Khi công cụ đổi
định dạng, sinh lại fixture rồi đổi bản trong tên file và bảng.

| File | Công cụ, bản | Lệnh sinh hoặc nguồn |
|---|---|---|
| `pytest-9.2.0-pass.xml` | pytest 9.2.0 | `pytest -q -p no:cacheprovider --junitxml=<f> test_sample.py` (2 test qua, 1 `skip`) |
| `pytest-9.2.0-fail.xml` | pytest 9.2.0 | như trên (1 qua, 1 `assert 1 + 1 == 3` hỏng) |
| `gitleaks-8.30.1-clean.sarif` | gitleaks 8.30.1 | `gitleaks git --config gl.toml --report-format=sarif --report-path=<f> <repo>` (repo git tạm sạch) |
| `gitleaks-8.30.1-leak.sarif` | gitleaks 8.30.1 | như trên thêm `--redact`; repo có một dòng `aws_access_key_id = AKIA…` GIẢ ngẫu nhiên |
| `pip-audit-2.10.1-clean.json` | pip-audit 2.10.1 | `pip-audit --no-deps --disable-pip -r <req> -f json -o <f>` với `idna==3.20` |
| `pip-audit-2.10.1-vuln.json` | pip-audit 2.10.1 | như trên với `requests==2.19.0` (CVE-2018-18074…; cần mạng) |
| `codeql-2.27.4-clean.sarif` | CodeQL 2.27.4 | SARIF trích từ [phân tích CI 2166341363](https://api.github.com/repos/seeker19110/X-Templates/code-scanning/analyses/2166341363) |

Ghi chú sinh:
- gitleaks dùng cấu hình tối giản một luật `aws-access-key-id` (regex `\b(AKIA[A-Z0-9]{16})\b`): bộ luật mặc định làm
  SARIF ~48 KB toàn danh sách rule. Khoá ví dụ chính thức của AWS bị allowlist mặc định của gitleaks bỏ qua nên
  dùng khoá giả ngẫu nhiên khác (không phải khoá thật); `--redact` che nội dung. `partialFingerprints` chứa tác giả
  giả `t` / `t@example.com`.
- SARIF của gitleaks ghi `tool.driver.semanticVersion` là `v8.0.0` — giá trị gitleaks ghi cứng, không phải bản chạy
  (bản thật 8.30.1); tên file mang bản thật.
- Rút gọn pytest XML: `hostname` đổi thành `localhost`. Nội dung `<skipped>`/`<failure>` đã bỏ đường dẫn
  tuyệt đối của thư mục tạm. Mọi trường khác giữ nguyên.
- CodeQL chạy ngày 2026-11-14 trên `refs/pull/539/merge`, commit `981daa8ca78b5d275f82ac4615eb3d98dff99d0b`.
  API phân tích trả báo cáo gốc khi đặt header `Accept: application/sarif+json`. SHA-256 của báo cáo gốc là
  `3eca6f97d2db1a92a8e467b5b61b57202a57bbdab1fae530b150c3a5fd77014d`.
  Fixture giữ nguyên giá trị `$schema`, `version`, `runs[0].tool.driver` và `runs[0].results` (`[]`). Báo cáo gốc
  có một run và vắng trường `invocations`. Phần trích lược bỏ danh mục rule, metadata chạy và thông tin đường dẫn.
