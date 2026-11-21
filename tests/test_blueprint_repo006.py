"""AUD-HAR-459 (D-535): lệnh kiểm BASE-REPO-006 của BLUEPRINT.md chạy thật trong repo git tạm.

Lệnh phải đọc được (không bị chú thích sau nó làm rỗng), xanh khi VERSION đã lên main mà chưa có tag nếu có GO-NO-GO của đúng
bản đó chờ chữ ký, và đỏ khi không có.
"""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import xt

OLD = "2026-11-01T00:00:00+00:00"  # quá cửa sổ 15 phút


def repo006_command() -> str:
    found = xt.blueprint_checks(ROOT / "BLUEPRINT.md")
    return next(c["cmd"] for c in found["checks"] if c["id"] == "BASE-REPO-006")


class Repo006Test(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.env = {
            **os.environ,
            "GIT_AUTHOR_NAME": "t",
            "GIT_AUTHOR_EMAIL": "t@localhost.invalid",
            "GIT_COMMITTER_NAME": "t",
            "GIT_COMMITTER_EMAIL": "t@localhost.invalid",
            "GIT_AUTHOR_DATE": OLD,
            "GIT_COMMITTER_DATE": OLD,
        }
        self.git("init", "-q", "-b", "main")
        (self.dir / "VERSION").write_text("3.35.0\n", encoding="utf-8")

    def git(self, *args: str) -> None:
        subprocess.run(["git", "-C", str(self.dir), *args], check=True, env=self.env, capture_output=True)

    def land(self, *names: str) -> None:
        for name in names:
            path = self.dir / name
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists():  # VERSION do setUp ghi, không ghi đè
                path.write_text("x\n", encoding="utf-8")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "release")
        self.git("update-ref", "refs/remotes/origin/main", "HEAD")

    def run_check(self) -> int:
        return subprocess.run(
            ["sh", "-c", repo006_command()], cwd=self.dir, env=self.env, capture_output=True
        ).returncode

    def test_command_is_readable(self) -> None:
        self.assertIn("git ls-files", repo006_command())

    def test_candidate_with_go_no_go_is_green_after_window(self) -> None:
        self.land("VERSION", "docs/ops/GO-NO-GO-2026-11-21-v3.35.0.md")
        self.assertEqual(self.run_check(), 0)

    def test_version_on_main_without_go_no_go_or_tag_is_red_after_window(self) -> None:
        self.land("VERSION")
        self.assertEqual(self.run_check(), 1)

    def test_go_no_go_of_another_version_does_not_count(self) -> None:
        self.land("VERSION", "docs/ops/GO-NO-GO-2026-11-21-v3.35.01.md", "docs/ops/GO-NO-GO-2026-11-20-v3.34.0.md")
        self.assertEqual(self.run_check(), 1)

    def test_annotated_tag_is_green(self) -> None:
        self.land("VERSION")
        self.git("tag", "-a", "v3.35.0", "-m", "v3.35.0")
        self.assertEqual(self.run_check(), 0)


if __name__ == "__main__":
    unittest.main()
