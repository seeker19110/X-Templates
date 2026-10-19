"""Audit 2026-10-19 (delta #94–#157): lỗ guard ở chính sách mặc định (ADR-0018) — mỗi lớp một phát hiện AUD-SEC-*."""

from __future__ import annotations

import os
import shlex
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


def final(cmd: str, root: Path = ROOT) -> str:
    """Quyết định cuối ở chính sách mặc định (không hỏi): `deny` hoặc rỗng (cho chạy)."""
    with mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(root), "XT_GUARD_POLICY": ""}):
        return str(guard.apply_policy(guard.bash_decision(cmd, str(root)))["decision"])


def nest(cmd: str, times: int) -> str:
    for _ in range(times):
        cmd = "bash -c " + shlex.quote(cmd)
    return cmd


class NestTooDeepDeniedTest(unittest.TestCase):
    """AUD-SEC-063: shell lồng sâu hơn `MAX_NEST` không quét hết → chặn, không cho qua im lặng."""

    def test_nest_too_deep_denied(self):
        for inner in ("rm -rf ~", "git push origin main", "gh repo delete o/r --yes", "true"):
            for n in (4, 5, 6):
                with self.subTest(inner=inner, n=n):
                    self.assertEqual(final(nest(inner, n)), "deny")
        self.assertEqual(final(nest("ls -la", 2)), "")  # lồng nông vô hại vẫn chạy

    def test_nest_too_deep_strict_still_asks(self):
        res = guard.bash_decision(nest("true", 5), str(ROOT))
        self.assertEqual(res["decision"], "ask")


class BraceExpansionTest(unittest.TestCase):
    """AUD-SEC-064: bash bung `{a,b}` trước khi chạy — guard xét từng biến thể."""

    def test_brace_expansion_denied(self):
        for cmd in (
            "git push origin {feat/x,main}",
            "git push origin HEAD:{main,x}",
            "git push origin HEAD:refs/heads/{main,dev}",
            "rm -rf {dist,~/.cache}",
            "rm -rf {dist,build,~}",
            "git stash {drop,}",
            "gh repo {delete,} o/r --yes",
            "kubectl {delete,} ns prod",
            "terraform {destroy,}",
            "docker run --{privileged,} alpine",
            "codex --{full-auto,}",
            "echo ok && rm -rf {a,{b,~/x}}",
            "rm -rf ~/{.ssh,.aws}",
            "rm -rf /{a..b}",
        ):
            with self.subTest(cmd):
                self.assertEqual(final(cmd), "deny")

    def test_brace_expansion_harmless_passes(self):
        for cmd in (
            "mkdir -p src/{a,b}",
            "cp file.txt{,.bak}",
            "echo {1..3}",
            "echo '{a,b}' \"{x,y}\"",
            "echo ${HOME} ${a:-x,y}",
            "{ ls; echo x; }",
            "find . -name '*.py' -exec ruff check {} +",
            "awk '{print $1,$2}' f.txt",
            'cat > f.json <<E\n{"a":1,"b":2}\nE',
            "echo \\{a,b\\}",
        ):
            with self.subTest(cmd):
                self.assertEqual(final(cmd), "")

    def test_brace_variants(self):
        self.assertEqual(guard.brace_variants("echo hi"), [])
        self.assertEqual(guard.brace_variants("echo {a}"), [])  # không dấu phẩy/`..` → chữ
        self.assertEqual(guard.brace_variants("echo {a, b}"), [])  # khoảng trắng → không bung
        self.assertEqual(guard.brace_variants("echo {a,b"), [])  # không đóng
        self.assertEqual(sorted(guard.brace_variants("x {a,b}")), ["x a", "x a b", "x b"])
        self.assertEqual(sorted(guard.brace_variants("x p{a,b}s")), ["x pas", "x pas pbs", "x pbs"])
        self.assertIn("x 1", guard.brace_variants("x {1..9}"))
        self.assertIn("x 9", guard.brace_variants("x {1..9..2}"))
        self.assertIn("x 'a b'", guard.brace_variants("x {'a b',c}"))  # nháy trong nhóm giữ khoảng trắng
        self.assertIn("x a\\,b", guard.brace_variants("x {a\\,b,c}"))  # dấu phẩy thoát không tách
        self.assertIsNone(guard.brace_variants("x " + "{a,b}" * 7))  # 2^7 > trần → không quét hết

    def test_brace_too_many_variants_denied(self):
        self.assertEqual(final("echo " + "{a,b}" * 7), "deny")


if __name__ == "__main__":
    unittest.main()
