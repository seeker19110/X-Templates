"""`xt.py mutate-guard` (T-3655, AUD-TEST-051): đột biến chính sách guard bằng stdlib, mỗi mutant một tiến trình con.

Guard giả nhỏ trong thư mục tạm: bộ test mạnh giết mọi mutant (exit 0), bộ test yếu để mutant sống (exit 1), bộ test đỏ
từ đầu hay không có chỗ đột biến → exit 2; test treo khi chính sách đổi → hết giờ = bị giết."""

from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import xt

FAKE_GUARD = '''
def decide(x):
    """Quyết định giả: rỗng → deny; "ok" → cho qua; còn lại → ask."""
    if not x:
        return "deny"
    n = -1
    if 0 < n < 2:
        return "khác"
    return "" if x == "ok" and x is not None else "ask"


def policy(x):
    return decide(x) in ("deny",) or False


def other():
    return "deny"
'''

STRONG = """
import unittest
import fakeguard as g


class T(unittest.TestCase):
    def test_all(self):
        self.assertEqual(g.decide(None), "deny")
        self.assertEqual(g.decide("ok"), "")
        self.assertEqual(g.decide("z"), "ask")
        self.assertIs(g.policy(None), True)
        self.assertIs(g.policy("z"), False)
"""

WEAK = """
import unittest
import fakeguard as g


class T(unittest.TestCase):
    def test_deny(self):
        self.assertEqual(g.decide(None), "deny")
"""

RED = """
import unittest


class T(unittest.TestCase):
    def test_red(self):
        self.fail("đỏ sẵn")
"""

HANG = """
import time
import unittest
import fakeguard as g


class T(unittest.TestCase):
    def test_hang_when_changed(self):
        if g.decide("ok") != "":
            time.sleep(30)
        self.assertEqual(g.decide(None), "deny")
        self.assertEqual(g.decide("z"), "ask")
        self.assertIs(g.policy(None), True)
        self.assertIs(g.policy("z"), False)
"""


class MutateGuardTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(self.enterContext(tempfile.TemporaryDirectory())).resolve()
        self.guard = self.tmp / "fakeguard.py"
        self.guard.write_text(FAKE_GUARD, encoding="utf-8")
        for name, body in (("t_strong", STRONG), ("t_weak", WEAK), ("t_red", RED), ("t_hang", HANG)):
            (self.tmp / f"{name}.py").write_text(textwrap.dedent(body), encoding="utf-8")

    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        env = {**os.environ, "CLAUDE_PROJECT_DIR": str(self.tmp)}
        cmd = [sys.executable, str(ROOT / "scripts" / "xt.py"), "mutate-guard", "--guard", str(self.guard), *args]
        return subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=300)

    def test_sites_only_inside_target_functions(self):
        m = xt.GuardMutator(["decide", "policy"])
        m.visit(ast.parse(FAKE_GUARD))
        # decide: `not`, 'deny', Eq, IsNot, And, '', 'ask'; policy: 'deny', In, Or — `0 < n < 2` (hai phép so), `-1`,
        # chữ không phải quyết định ('khác', 'ok', docstring) và mọi thứ trong other() không đột biến
        self.assertEqual(len(m.sites), 10, m.sites)
        self.assertIn("bỏ `not`", m.sites[0])
        self.assertIn("And → Or", m.sites[4])
        r = self.run_cli("--functions", "decide,policy", "--tests", "t_strong", "--list")
        self.assertEqual((r.returncode, len(r.stdout.splitlines())), (0, 10), r.stderr)

    def test_strong_tests_kill_every_mutant(self):
        r = self.run_cli("--functions", "decide,policy", "--tests", "t_strong", "--jobs", "2")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("10 mutant · giết 10 · sống 0", r.stdout)

    def test_weak_tests_leave_survivors(self):
        r = self.run_cli("--functions", "decide,policy", "--tests", "t_weak", "--json")
        self.assertEqual(r.returncode, 1, r.stderr)
        data = json.loads(r.stdout)
        self.assertEqual(data["mutants"], 10)
        self.assertTrue(data["survived"])
        self.assertEqual(len(data["outcomes"]), 10)
        r = self.run_cli("--functions", "decide,policy", "--tests", "t_weak")
        self.assertEqual(r.returncode, 1)
        self.assertRegex(r.stdout, r"✗ sống — dòng \d+: ")

    def test_red_baseline_or_no_sites_is_error(self):
        r = self.run_cli("--functions", "decide", "--tests", "t_red")
        self.assertEqual(r.returncode, 2)
        self.assertIn("đỏ hoặc treo khi CHƯA đột biến", r.stderr)
        r = self.run_cli("--functions", "khong_co", "--tests", "t_strong")
        self.assertEqual(r.returncode, 2)
        self.assertIn("không có chỗ đột biến", r.stderr)

    def test_hanging_mutant_counts_as_killed(self):
        r = self.run_cli("--functions", "decide,policy", "--tests", "t_hang", "--timeout", "8", "--json")
        data = json.loads(r.stdout)
        self.assertIn("timeout", data["outcomes"])
        self.assertEqual((r.returncode, data["survived"]), (0, []), r.stderr)

    def test_weekly_workflow_runs_mutate_guard(self):
        body = (ROOT / ".github" / "workflows" / "mutation.yml").read_text(encoding="utf-8")
        self.assertRegex(body, r"schedule:\n\s+- cron: \"[\d*]+ [\d*]+ \* \* [0-6]\"")
        self.assertIn("python3 scripts/xt.py mutate-guard", body)
        self.assertIn("persist-credentials: false", body)

    def test_default_targets_exist_in_real_guard(self):
        m = xt.GuardMutator(xt.MUTATE_FUNCS)
        m.visit(ast.parse((ROOT / ".claude" / "hooks" / "guard.py").read_text(encoding="utf-8")))
        self.assertGreater(len(m.sites), 20)


if __name__ == "__main__":
    unittest.main()
