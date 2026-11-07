# Fixture report: output thật của công cụ (AUD-TEST-061)

Sinh ngày 2026-11-07 trên Linux (WSL2), Python 3.14.6, venv tạm; không thêm phụ thuộc vào repo. Dùng bởi
`tests/test_report_fixtures.py` (adapter `report_result` của `scripts/xt.py`). Sinh lại khi công cụ đổi định dạng:
đổi bản trong tên file và bảng này.

| File | Công cụ, bản | Lệnh sinh (trong thư mục tạm) |
|---|---|---|
| `pytest-9.2.0-pass.xml` | pytest 9.2.0 | `pytest -q -p no:cacheprovider --junitxml=<f> test_sample.py` (2 test qua, 1 `skip`) |
| `pytest-9.2.0-fail.xml` | pytest 9.2.0 | như trên (1 qua, 1 `assert 1 + 1 == 3` hỏng) |
| `gitleaks-8.30.1-clean.sarif` | gitleaks 8.30.1 | `gitleaks git --config gl.toml --report-format=sarif --report-path=<f> <repo>` (repo git tạm sạch) |
| `gitleaks-8.30.1-leak.sarif` | gitleaks 8.30.1 | như trên thêm `--redact`; repo có một dòng `aws_access_key_id = AKIA…` GIẢ ngẫu nhiên |
| `pip-audit-2.10.1-clean.json` | pip-audit 2.10.1 | `pip-audit --no-deps --disable-pip -r <req> -f json -o <f>` với `idna==3.20` |
| `pip-audit-2.10.1-vuln.json` | pip-audit 2.10.1 | như trên với `requests==2.19.0` (CVE-2018-18074…; cần mạng) |

Ghi chú sinh:
- gitleaks dùng cấu hình tối giản một luật `aws-access-key-id` (regex `\b(AKIA[A-Z0-9]{16})\b`): bộ luật mặc định làm
  SARIF ~48 KB toàn danh sách rule. Khoá ví dụ chính thức `AKIAIOSFODNN7EXAMPLE` bị allowlist mặc định của gitleaks
  bỏ qua nên dùng khoá giả ngẫu nhiên khác (không phải khoá thật); `--redact` che nội dung. `partialFingerprints`
  chứa tác giả giả `t` / `t@example.com`.
- Rút gọn thủ công duy nhất (pytest XML): `hostname` đổi thành `localhost`, và đường tuyệt đối của thư mục tạm bị
  cắt khỏi nội dung `<skipped>`/`<failure>`. Mọi thứ khác nguyên văn.
- CodeQL: chưa có fixture (không chạy được cục bộ; không giả lập).
