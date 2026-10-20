"""Review PR #186 lần 1: lọt còn lại sau AUD-SEC-088/089 — cd tới thư mục guard không giải được (cờ ghép, chuyển hướng
đầu lệnh, CDPATH) và script trình thông dịch ghi đường dẫn được canh qua API ngoài danh sách. Sửa theo D-105 (script
nhắc đường dẫn được canh: mặc định chặn, trừ khi toàn script chỉ đọc) và D-106 (cwd không biết: thử mọi thư mục canh)."""

from __future__ import annotations

import os
import sys
import unittest
import unittest.mock as mock
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load_guard():
    sys.path.insert(0, str(ROOT / ".claude" / "hooks"))
    import guard as g

    return g


guard = _load_guard()


def policy(cmd: str, cwd: str | None = None) -> dict:
    """Kết quả ở chính sách mặc định (không hỏi): `decision` deny hoặc rỗng, kèm `code`."""
    with mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(ROOT), "XT_GUARD_POLICY": ""}):
        return dict(guard.apply_policy(guard.bash_decision(cmd, str(ROOT), cwd)))


class CdUnresolvedTest(unittest.TestCase):
    """D-106: `cd` guard không giải được → cwd không biết; đích ghi tương đối thử ở mọi thư mục canh."""

    def test_guard_cd_unresolved_denied(self):
        cases = {
            "cd -LP .claude && echo x > settings.json": "HOOK_BYPASS",
            "cd -Pe .claude && echo x > settings.json": "HOOK_BYPASS",
            "cd -e@ .claude/hooks && echo x > guard.py": "HOOK_BYPASS",
            "2>/dev/null cd .claude && echo x > settings.json": "HOOK_BYPASS",
            ">/dev/null pushd .autopilot && echo {} > verified.json": "EVIDENCE_HANDWRITE",
            f"CDPATH={ROOT}/.claude cd hooks && echo x > guard.py": "HOOK_BYPASS",
            f"export CDPATH={ROOT}/.claude; cd hooks && echo x > guard.py": "HOOK_BYPASS",
            f"CDPATH={ROOT}/.claude; cd hooks && echo x > guard.py": "HOOK_BYPASS",
            # biến/`cd -`/`pushd +N`: không biết → thử mọi thư mục canh
            'cd "$X" && echo x > settings.json': "HOOK_BYPASS",
            "cd $PWD && echo x > guard.py": "HOOK_BYPASS",
            "cd - && echo {} > verified.json": "EVIDENCE_HANDWRITE",
            "pushd +1 && echo x > config": "HOOK_BYPASS",
            "cd $X && echo x > pre-commit": "HOOK_BYPASS",
            "cd $X && echo K=1 > .env": "SECRET_WRITE",
            "cd $X && echo x > $PWD/settings.json": "HOOK_BYPASS",
            "cd - && echo x > ${CLAUDE_PROJECT_DIR}/.claude/settings.json": "HOOK_BYPASS",
            # đường script và shell lồng cũng theo cwd không biết
            "cd $X && bash -c 'echo x > guard.py'": "HOOK_BYPASS",
            "popd; echo x > settings.local.json": "HOOK_BYPASS",
        }
        for cmd, code in cases.items():
            with self.subTest(cmd=cmd):
                res = policy(cmd)
                self.assertEqual((res["decision"], res.get("code")), ("deny", code), res)

    def test_guard_sec090_now_covered(self):
        """AUD-SEC-090: `cd "$PWD/…"` (thư mục không biết) và đường dẫn trong phần tử list nay bị chặn."""
        cases = {
            'cd "$PWD/.claude" && echo x > settings.json': "HOOK_BYPASS",
        }
        for cmd, code in cases.items():
            with self.subTest(cmd=cmd):
                res = policy(cmd)
                self.assertEqual((res["decision"], res.get("code")), ("deny", code), res)

    def test_guard_cd_unresolved_controls(self):
        for cmd in (
            "cd docs 2>/dev/null && echo x > a.md",
            "cd -LP /tmp && echo x > a.txt",
            "cd unknown_dir && echo x > notes.txt",
            "cd $X && echo x > notes.txt",
            "cd $X && echo x > /tmp/settings.json",
            'echo "print(1)" | python3',
            "cd $X && python3 -c \"open('out.txt','w').write('x')\"",
            "cd - && cat settings.json",
            "2>/dev/null cd docs && echo x > settings.json",
            f"CDPATH={ROOT}/.claude cd /tmp && echo x > guard.py",
        ):
            with self.subTest(cmd=cmd):
                self.assertEqual(policy(cmd)["decision"], "", cmd)

    def test_cd_target_parsing(self):
        here = "/p"
        self.assertEqual(guard._cd_target(["cd", "-LP", "a"], here), "/p/a")
        self.assertEqual(guard._cd_target(["cd", "-Pe@", "--", "a"], here), "/p/a")
        self.assertIsNone(guard._cd_target(["cd", "-Lx", "a"], here))  # cờ lạ trong cờ ghép: không đoán
        self.assertIsNone(guard._cd_target(["cd", "a"], here, cdpath=True))
        self.assertEqual(guard._cd_target(["cd", "/x"], here, cdpath=True), "/x")
        self.assertEqual(guard._cd_target(["cd", "/x"], None), "/x")  # tuyệt đối: biết dù trước đó không biết
        self.assertIsNone(guard._cd_target(["cd", "a"], None))
        self.assertEqual(guard.normalize(guard.tokenize("2>/dev/null cd a")), ["cd", "a"])
        self.assertEqual(guard.normalize(guard.tokenize(">/dev/null 2>&1 rm -rf x")), ["rm", "-rf", "x"])

    def test_leading_redirect_rules_apply(self):
        """Chuyển hướng đặt đầu lệnh không che lệnh thật (`>/dev/null rm -rf ~`)."""
        res = policy(">/dev/null rm -rf ~")
        self.assertEqual(res["decision"], "deny", res)


if __name__ == "__main__":
    unittest.main()
