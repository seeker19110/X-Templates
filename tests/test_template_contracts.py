"""Mẫu tài liệu khớp lệnh Kiểm của mục MUST nó phục vụ (review #412): dự án chép mẫu nguyên văn phải qua được Kiểm máy
của mục đó, không đỏ ngay dòng mẫu."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FW = ROOT / "framework"


def template_block(name: str) -> str:
    """Khối ````markdown đầu tiên của mẫu — phần dự án chép sang."""
    text = (FW / "templates" / name).read_text(encoding="utf-8")
    m = re.search(r"^````markdown\n(.*?)^````$", text, re.M | re.S)
    assert m, f"{name}: không có khối ````markdown"
    return m.group(1)


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


if __name__ == "__main__":
    unittest.main()
