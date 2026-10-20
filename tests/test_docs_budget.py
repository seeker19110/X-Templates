"""Trần kích thước file hướng dẫn nạp đầu phiên (PLAN-3.12-lean Lát 1, D-111): giữ lâu dài sau khi PLAN đóng — review #190
chỉ ra Gate của PLAN không còn chạy khi task đã tick. Vượt trần → cắt chữ, chuyển nội dung về "nhà", không nới trần."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CAPS = {  # byte; nhà của từng trần: PLAN-3.12-lean T-1701…T-1704
    "AGENTS.md": 7168,
    "framework/templates/AGENTS.md": 8192,
    "CLAUDE.md": 2048,
    "framework/templates/CLAUDE.md": 2560,
    ".claude/skills/autopilot/SKILL.md": 6144,
    "framework/11-autonomous-loop/README.md": 12288,
}


class DocsBudgetTest(unittest.TestCase):
    def test_guidance_files_stay_under_caps(self):
        for rel, cap in CAPS.items():
            with self.subTest(rel):
                size = (ROOT / rel).stat().st_size
                self.assertLessEqual(size, cap, f"{rel}: {size} B > {cap} B — cắt chữ, không nới trần")

    def test_agents_md_keeps_nine_sections(self):
        for rel in ("AGENTS.md", "framework/templates/AGENTS.md"):
            with self.subTest(rel):
                heads = [ln for ln in (ROOT / rel).read_text(encoding="utf-8").splitlines() if ln.startswith("## ")]
                self.assertEqual(len(heads), 9, heads)


if __name__ == "__main__":
    unittest.main()
