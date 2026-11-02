"""Mẫu tài liệu khớp lệnh Kiểm của mục MUST nó phục vụ (review #412): dự án chép mẫu nguyên văn phải qua được Kiểm máy
của mục đó, không đỏ ngay dòng mẫu."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FW = ROOT / "framework"


def template_block(name: str, lang: str = "markdown") -> str:
    """Khối ````<lang> đầu tiên của mẫu — phần dự án chép sang."""
    text = (FW / "templates" / name).read_text(encoding="utf-8")
    m = re.search(rf"^````{lang}\n(.*?)^````$", text, re.M | re.S)
    assert m, f"{name}: không có khối ````{lang}"
    return m.group(1)


ISO_DURATION_RE = re.compile(r"P(?!$)(\d+Y)?(\d+M)?(\d+W)?(\d+D)?(T(?=\d)(\d+H)?(\d+M)?(\d+S)?)?")


def item_line(item_id: str) -> str:
    for p in FW.rglob("*.md"):
        for line in p.read_text(encoding="utf-8").splitlines():
            if line.startswith(f"- [ ] `{item_id}` "):
                return line
    raise AssertionError(f"không thấy mục {item_id}")


class TemplateContractTest(unittest.TestCase):
    def test_risks_template_ids_match_pm_risk_001_check(self):
        """`PM-RISK-001` Kiểm `rg -n "^\\| RK-[0-9]{3}" docs/RISKS.md …`: mẫu từng dùng `R-001` (trùng không gian ID
        `R-NNN` của PROJECT.md) nên chép nguyên văn là đỏ MUST."""
        self.assertIn('"^\\| RK-[0-9]{3}"', item_line("PM-RISK-001"))
        rows = template_block("RISKS.md").splitlines()
        self.assertTrue([r for r in rows if re.match(r"^\| RK-[0-9]{3}", r)])
        self.assertFalse([r for r in rows if re.match(r"^\| R-[0-9]{3}", r)])

    def test_privacy_data_map_matches_cmp_priv_001_002(self):
        """AUD-DOC-218: `retention` của mẫu theo đúng lint `CMP-PRIV-002` (ISO 8601 duration hoặc `until-account-deleted`)
        và mẫu có trường "nơi sao chép" (`copies`) mà `CMP-PRIV-001` đòi."""
        self.assertIn("ISO 8601 duration hoặc `until-account-deleted`", item_line("CMP-PRIV-002"))
        self.assertIn("nơi sao chép", item_line("CMP-PRIV-001"))
        block = template_block("PRIVACY-DATA-MAP.md", "yaml")
        retention = re.findall(r"^\s*retention:\s*<([^>]*)>", block, re.M)
        self.assertTrue(retention, block)
        for value in retention:
            for choice in (c.strip() for c in value.split("|")):
                self.assertTrue(choice == "until-account-deleted" or ISO_DURATION_RE.fullmatch(choice), choice)
        self.assertRegex(block, r"(?m)^\s*copies:\s*\[")

    def test_slo_file_name_is_one(self):
        """AUD-DOC-217: một tên file SLO ở `OPS-SLO-001` (nhà), mẫu, chỉ mục mẫu và mục ngành — `slo.md` ≠ `SLO.md` trên
        Linux."""
        want = "`docs/ops/SLO.md`"
        for item in ("OPS-SLO-001", "IND-SAAS-013", "IND-GOV-018"):
            self.assertIn(want, item_line(item), item)
        self.assertIn("# Mẫu docs/ops/SLO.md\n", (FW / "templates" / "SLO.md").read_text(encoding="utf-8"))
        index = (FW / "templates" / "README.md").read_text(encoding="utf-8")
        self.assertIn(f"| [`SLO.md`](SLO.md) | {want} ", index)
        self.assertNotIn("docs/ops/slo.md", "\n".join(p.read_text(encoding="utf-8") for p in FW.rglob("*.md")))


if __name__ == "__main__":
    unittest.main()
