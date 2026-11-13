"""Fixture Git không được đổi repo/cấu hình hay chạy hook của môi trường gọi test."""

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tests"))
from git_fixture import fixture_git, init_git_fixture, isolated_git_environment


def snapshot(root: Path) -> tuple[str, str, str, str]:
    files = sorted(p for p in root.rglob("*") if p.is_file() and ".git" not in p.relative_to(root).parts)
    tree = b"".join(p.relative_to(root).as_posix().encode() + b"\0" + p.read_bytes() for p in files)
    return (
        fixture_git(root, "rev-parse", "HEAD").stdout.strip(),
        hashlib.sha256((root / ".git/index").read_bytes()).hexdigest(),
        hashlib.sha256((root / ".git/config").read_bytes()).hexdigest(),
        hashlib.sha256(tree).hexdigest(),
    )


class GitFixtureIsolationTest(unittest.TestCase):
    def test_import_contexts_without_running_discovered_tests(self):
        code = """
import importlib, pathlib, runpy, sys, unittest
start, pattern, mode = pathlib.Path(sys.argv[1]), sys.argv[2], sys.argv[3]
if mode == 'discover':
    loader = unittest.TestLoader()
    suite = loader.discover(str(start), pattern=pattern, top_level_dir=str(start))
    assert not loader.errors, 'fixture consumer discovery import failed'
    assert suite.countTestCases() > 0, 'fixture consumer discovery loaded no tests'
elif mode == 'package':
    sys.path.insert(0, str(start.parent))
    importlib.import_module('tests.' + pathlib.Path(pattern).stem)
else:
    runpy.run_path(str(start / pattern), run_name='fixture_import_only')
"""
        for name in ("test_git_fixture.py", "test_hooks.py", "test_guard_strict.py"):
            for mode in ("discover", "package", "direct"):
                with self.subTest(module=name, mode=mode):
                    result = subprocess.run(
                        [sys.executable, "-I", "-c", code, str(ROOT / "tests"), name, mode],
                        capture_output=True,
                        text=True,
                        timeout=15,
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)

    def test_foreign_repo_and_caller_environment_unchanged(self):
        base = Path(self.enterContext(tempfile.TemporaryDirectory())).resolve()
        foreign, owned = base / "foreign", base / "owned"
        foreign.mkdir()
        owned.mkdir()
        with isolated_git_environment():
            init_git_fixture(foreign)
            (foreign / "tracked").write_text("keep\n")
            fixture_git(foreign, "add", "tracked")
            fixture_git(foreign, "commit", "-qm", "foreign")
            (foreign / "tracked").write_text("unstaged\n")
            (foreign / "staged").write_text("staged\n")
            fixture_git(foreign, "add", "staged")
            before = snapshot(foreign)
        poison = base / "config"
        poison.write_text("[commit]\n gpgsign = true\n[gpg]\n program = /bin/false\n[init]\n templateDir = missing\n")
        with mock.patch.dict(
            os.environ,
            {
                "GIT_DIR": str(foreign / ".git"),
                "GIT_COMMON_DIR": str(foreign / ".git"),
                "GIT_WORK_TREE": str(foreign),
                "GIT_INDEX_FILE": str(foreign / ".git/index"),
                "GIT_CONFIG_GLOBAL": str(poison),
                "GIT_CONFIG_COUNT": "1",
                "GIT_CONFIG_KEY_0": "commit.gpgsign",
                "GIT_CONFIG_VALUE_0": "true",
            },
        ):
            caller = dict(os.environ)
            with isolated_git_environment():
                init_git_fixture(owned)
                global_config = subprocess.run(
                    ["git", "-C", str(owned), "config", "--global", "--get", "commit.gpgsign"],
                    capture_output=True,
                    text=True,
                    timeout=15,
                )
                self.assertEqual(global_config.returncode, 1, "caller global configuration leaked")
                (owned / "xt.yaml").write_text("delivery_phase: build\n")
                fixture_git(owned, "add", "xt.yaml")
                fixture_git(owned, "commit", "-qm", "owned")
                self.assertTrue(
                    fixture_git(owned, "rev-parse", "--show-toplevel").stdout.strip() == str(owned),
                    "Git fixture escaped its worktree",
                )
                result = subprocess.run(
                    [sys.executable, str(ROOT / ".claude/hooks/guard.py"), "core"],
                    input=json.dumps({"tool": "bash", "command": "git status", "project_dir": str(owned)}),
                    capture_output=True,
                    text=True,
                    timeout=15,
                )
                self.assertEqual((result.returncode, json.loads(result.stdout)["decision"]), (0, "allow"))
                self.assertEqual(before, snapshot(foreign))
            self.assertTrue(dict(os.environ) == caller, "caller environment was not restored")
