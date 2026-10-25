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
    ".claude/skills/complete/SKILL.md": 6144,  # ADR-0046: skill pha harden, cùng trần với /autopilot
    ".claude/skills/optimize/SKILL.md": 6144,  # ADR-0048: skill tối ưu, cùng trần
    "framework/11-autonomous-loop/README.md": 12288,
}
# Trần TỔNG byte theo thư mục (ADR-0043, T-2407): đóng băng bề mặt 3.x = kích thước tại 2026-10-23 + 5 %. Thêm mã/chữ thì
# cắt chỗ khác trong cùng nhóm; mở băng cần ADR mới — không nới số ở đây. Chỉ đếm file git theo dõi (bỏ cache/sinh ra).
DIR_CAPS = {  # nhóm → (pathspec git, trần byte); đo: `git ls-files -z -- <spec> | xargs -0 cat | wc -c`
    "scripts (xt.py, install.py, xt_app)": (("scripts/*.py", "scripts/xt_app/"), 711855),  # 677958 B
    ".claude/hooks": ((".claude/hooks/",), 369393),  # 351803 B
    "framework/11-autonomous-loop": (("framework/11-autonomous-loop/",), 232307),  # 221245 B
}


def tracked_bytes(specs: "tuple[str, ...]") -> int:
    out = subprocess.run(["git", "-C", str(ROOT), "ls-files", "-z", "--", *specs], capture_output=True, check=True)
    return sum((ROOT / rel.decode()).stat().st_size for rel in out.stdout.split(b"\0") if rel)


class DocsBudgetTest(unittest.TestCase):
    def test_dir_totals_stay_under_caps(self):
        for group, (specs, cap) in DIR_CAPS.items():
            with self.subTest(group):
                size = tracked_bytes(specs)
                self.assertGreater(size, 0, f"{group}: không thấy file nào — pathspec sai")
                self.assertLessEqual(
                    size, cap, f"{group}: {size} B > {cap} B — cắt chỗ khác (ADR-0043), không nới trần"
                )

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
            if rel.startswith(b"tests_e2e/vendor/"):
                continue  # D-135: tệp bên thứ ba nguyên văn (hash ghim, vendor-check), không cài sang dự án đích
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
