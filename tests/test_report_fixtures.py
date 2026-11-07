"""AUD-TEST-061: adapter `report_result` đọc output THẬT của công cụ (nguồn, bản, lệnh: fixtures/reports/README.md)."""

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))

import xt

FIX = HERE / "fixtures" / "reports"


class RealReportFixtureTest(unittest.TestCase):
    def get(self, name: str) -> dict:
        return xt.report_result(FIX / name)

    def check(self, name: str, want: tuple) -> dict:
        r = self.get(name)
        self.assertEqual((r["kind"], r["status"], r["total"], r["failed"]), want, r["detail"])
        return r

    def test_pytest_junit(self):
        r = self.check("pytest-9.2.0-pass.xml", ("junit", "PASS", 2, 0))
        self.assertIn("1 bỏ qua", r["detail"])
        self.check("pytest-9.2.0-fail.xml", ("junit", "FAIL", 2, 1))

    def test_gitleaks_sarif(self):
        self.check("gitleaks-8.30.1-clean.sarif", ("sarif", "PASS", 0, 0))

    def test_gitleaks_leak_is_fail(self):
        """D-391: output thật của gitleaks không ghi `level`; công cụ quét bí mật → mọi kết quả là error (không dựa
        vào exit code của công cụ, vd `--exit-code 0`)."""
        doc = (FIX / "gitleaks-8.30.1-leak.sarif").read_text(encoding="utf-8")
        self.assertNotIn('"level"', doc)
        self.assertNotIn("AKIA", doc)  # --redact
        self.check("gitleaks-8.30.1-leak.sarif", ("sarif", "FAIL", 1, 1))

    def test_secret_scanner_vs_other_tools(self):
        """Tổng hợp: run gitleaks (tên không phân biệt hoa thường) có level `note` vẫn FAIL; run công cụ khác không
        ghi level giữ luật cũ (warning → không phải error); tên driver không phải chuỗi → luật cũ."""
        result = [{"ruleId": "r", "level": "note"}]
        for name, want in (("gitleaks", "FAIL"), ("GitLeaks", "FAIL"), ("codeql", "PASS"), (None, "PASS")):
            with self.subTest(name=name):
                doc = {"runs": [{"tool": {"driver": {"name": name}}, "results": result}]}
                self.assertEqual(xt._sarif_result(doc)["status"], want)
        bare = {"runs": [{"tool": {"driver": {"name": "other"}}, "results": [{"ruleId": "r"}]}]}
        r = xt._sarif_result(bare)
        self.assertEqual((r["status"], r["total"], r["failed"]), ("PASS", 1, 0))

    def test_pip_audit_json(self):
        self.check("pip-audit-2.10.1-clean.json", ("pip-audit", "PASS", 1, 0))
        # 10 mục `vulns` nhưng 5 id duy nhất — pip-audit lặp mục từ nhiều nguồn; adapter đếm id (AUD-HAR-317)
        r = self.check("pip-audit-2.10.1-vuln.json", ("pip-audit", "FAIL", 1, 5))
        self.assertIn("5 lỗ hổng", r["detail"])


if __name__ == "__main__":
    unittest.main()
