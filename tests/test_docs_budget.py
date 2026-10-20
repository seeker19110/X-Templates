"""Trần kích thước file hướng dẫn nạp đầu phiên (PLAN-3.12-lean Lát 1, D-111): giữ lâu dài sau khi PLAN đóng — review #190
chỉ ra Gate của PLAN không còn chạy khi task đã tick. Vượt trần → cắt chữ, chuyển nội dung về "nhà", không nới trần."""

import subprocess
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

    def test_tracked_text_files_are_clean_utf8(self):
        """Dự án đích (hotel-manager) kiểm mọi file văn bản: UTF-8, không BOM, không U+FFFD — file khung cài sang phải
        qua được (3.11.0 `guard.py` từng chứa ký tự U+FFFD thật trong `clean_text`)."""
        tracked = subprocess.run(
            ["git", "-C", str(ROOT), "ls-files", "-z"], capture_output=True, check=True
        ).stdout.split(b"\0")
        bad = []
        for rel in tracked:
            if not rel or rel.endswith((b".png", b".jpg", b".ico", b".pyc", b".zip", b".gz")):
                continue
            data = (ROOT / rel.decode()).read_bytes()
            if b"\0" in data:
                continue  # nhị phân
            try:
                text = data.decode("utf-8")
            except UnicodeDecodeError:
                bad.append((rel.decode(), "không phải UTF-8"))
                continue
            if data.startswith(b"\xef\xbb\xbf"):
                bad.append((rel.decode(), "BOM"))
            if "\ufffd" in text:
                bad.append((rel.decode(), "U+FFFD"))
        self.assertEqual(bad, [])

    def test_agents_md_keeps_nine_sections(self):
        for rel in ("AGENTS.md", "framework/templates/AGENTS.md"):
            with self.subTest(rel):
                heads = [ln for ln in (ROOT / rel).read_text(encoding="utf-8").splitlines() if ln.startswith("## ")]
                self.assertEqual(len(heads), 9, heads)


if __name__ == "__main__":
    unittest.main()
