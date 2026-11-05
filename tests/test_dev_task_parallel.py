"""T-3708 (D-367): lệnh test TỰ DÒ của `scripts/dev-task.sh` chạy song song theo số nhân — pytest có xdist → `-n`,
unittest → mỗi module một tiến trình qua `xargs -P`; `XT_JOBS` chọn số tiến trình (1 = tuần tự như cũ, rác = mặc định).
Lệnh khai báo trong xt.yaml không đổi. Dự án giả trong thư mục tạm, PATH chỉ gồm công cụ cần thiết (không lọt pytest/ruff
của máy), xdist giả qua PYTHONPATH."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS = "bash sh dirname basename grep sed awk tail head mktemp tee rm cat xargs nproc getconf sort ls sleep touch env"
FAKE_PYTEST = '#!/bin/sh\necho "PYTEST-ARGS: $*"\n'
# Mỗi module ghi mốc bắt đầu rồi chờ module kia — chạy tuần tự thì module đầu hết hạn và đỏ.
BARRIER = """import time, unittest
from pathlib import Path


class T(unittest.TestCase):
    def test_wait_peer(self):
        Path("started").mkdir(exist_ok=True)
        Path("started/{me}").touch()
        end = time.monotonic() + 15
        while not Path("started/{peer}").exists() and time.monotonic() < end:
            time.sleep(0.05)
        self.assertTrue(Path("started/{peer}").exists(), "module kia không chạy cùng lúc")
"""


@unittest.skipIf(shutil.which("bash") is None, "cần bash")
class DevTaskParallelTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(self.enterContext(tempfile.TemporaryDirectory()))
        (self.tmp / "scripts").mkdir()
        shutil.copy(ROOT / "scripts" / "dev-task.sh", self.tmp / "scripts" / "dev-task.sh")
        (self.tmp / "pyproject.toml").write_text("[project]\nname = 'x'\n", encoding="utf-8")
        self.bin = self.tmp / ".bin"
        self.bin.mkdir()
        for tool in TOOLS.split():
            path = shutil.which(tool)
            if path:
                (self.bin / tool).symlink_to(path)
        self.script(self.bin / "python3", f'#!/bin/sh\nexec "{sys.executable}" "$@"\n')
        self.pypath = self.tmp / ".py"
        self.pypath.mkdir()

    @staticmethod
    def script(path: Path, body: str) -> None:
        path.write_text(body, encoding="utf-8")
        path.chmod(0o755)

    def xdist(self, present: bool) -> None:
        body = "" if present else "raise ImportError('giả: không có xdist')\n"
        (self.pypath / "xdist.py").write_text(body, encoding="utf-8")  # che cả xdist thật nếu máy có

    def pytest(self, xdist: bool) -> None:
        self.script(self.bin / "pytest", FAKE_PYTEST)
        self.xdist(xdist)

    def dt(self, *args: str, jobs: str | None = None, **extra: str) -> subprocess.CompletedProcess[str]:
        env = {
            "PATH": str(self.bin),
            "HOME": str(self.tmp),
            "PYTHONPATH": str(self.pypath),
            "CLAUDE_PROJECT_DIR": str(self.tmp),
            **extra,
        }
        env.update({k: v for k, v in os.environ.items() if k.startswith("COVERAGE")})  # coverage subprocess của cổng
        if jobs is not None:
            env["XT_JOBS"] = jobs
        cmd = [shutil.which("bash") or "bash", str(self.tmp / "scripts" / "dev-task.sh"), *args]
        return subprocess.run(cmd, capture_output=True, text=True, cwd=self.tmp, env=env, timeout=120)

    def ran(self, r: subprocess.CompletedProcess[str]) -> str:
        m = re.search(r"^\[dev-task\] run \[test\]: (.*)$", r.stderr, re.M)
        self.assertIsNotNone(m, r.stderr)
        return m.group(1) if m else ""

    def tests_dir(self, **mods: str) -> None:
        d = self.tmp / "tests"
        d.mkdir(exist_ok=True)
        for name, body in mods.items():
            (d / f"{name}.py").write_text(body, encoding="utf-8")

    # --- pytest ---------------------------------------------------------------------------------------------------
    def test_pytest_with_xdist_runs_n_jobs(self):
        self.pytest(xdist=True)
        for jobs, flag in ((None, "-n auto"), ("3", "-n 3"), ("abc", "-n auto"), ("0", "-n auto"), ("-2", "-n auto")):
            with self.subTest(jobs=jobs):
                r = self.dt("test", jobs=jobs)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertEqual(self.ran(r), f"pytest -q {flag}")
                self.assertIn(f"PYTEST-ARGS: -q {flag}", r.stdout)
                self.assertNotIn("pytest-xdist", r.stderr)
        self.assertIn("XT_JOBS='abc' không phải số nguyên dương", self.dt("test", jobs="abc").stderr)

    def test_pytest_jobs_one_is_sequential(self):
        for xdist in (True, False):
            with self.subTest(xdist=xdist):
                self.pytest(xdist=xdist)
                r = self.dt("test", jobs="1")
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertEqual(self.ran(r), "pytest -q")
                self.assertNotIn("pytest-xdist", r.stderr)  # đã chọn tuần tự: không gợi ý

    def test_pytest_without_xdist_hints_once(self):
        self.pytest(xdist=False)
        (self.tmp / "xt.yaml").write_text('lint: "true | cat"\ntypecheck: ""\nbuild: ""\n', encoding="utf-8")
        for task in ("test", "gate", "gate-par"):
            with self.subTest(task=task):
                r = self.dt(task)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertEqual(self.ran(r), "pytest -q")
                self.assertIn("PYTEST-ARGS: -q\n", r.stdout + r.stderr)
                self.assertEqual(r.stderr.count("cài pytest-xdist để chạy song song"), 1, r.stderr)

    def test_declared_test_command_unchanged(self):
        self.pytest(xdist=True)
        (self.tmp / "xt.yaml").write_text("test: python3 -c 'print(\"DECL\")'\n", encoding="utf-8")
        r = self.dt("test")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.ran(r), "python3 -c 'print(\"DECL\")'")
        self.assertNotIn("PYTEST-ARGS", r.stdout)

    # --- unittest -------------------------------------------------------------------------------------------------
    def test_unittest_modules_run_concurrently(self):
        self.tests_dir(
            test_a=BARRIER.format(me="a", peer="b"),
            test_b=BARRIER.format(me="b", peer="a"),
            helper="X = 1\n",
            test_helper="import unittest\nimport helper\n\n\nclass H(unittest.TestCase):\n"
            "    def test_x(self):\n        self.assertEqual(helper.X, 1)\n",
        )
        r = self.dt("test", jobs="3")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertRegex(self.ran(r), r"\| xargs -r -P 3 -n 1 python3 -c ")
        self.assertEqual(sorted(p.name for p in (self.tmp / "started").iterdir()), ["a", "b"])
        self.assertEqual(r.stderr.count("\nOK"), 3, r.stderr)  # ba module, mỗi module một tiến trình

    def test_unittest_default_and_garbage_jobs_use_cpu_count(self):
        self.tests_dir(
            test_a="import unittest\n\n\nclass A(unittest.TestCase):\n    def test_ok(self):\n        pass\n"
        )
        for jobs in (None, "", "abc", "1.5"):
            with self.subTest(jobs=jobs):
                r = self.dt("test", jobs=jobs)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertRegex(self.ran(r), r"\| xargs -r -P [1-9][0-9]* -n 1 ")

    def test_unittest_red_module_fails_command(self):
        ok = "import unittest\nfrom pathlib import Path\n\n\nclass A(unittest.TestCase):\n    def test_ok(self):\n"
        self.tests_dir(
            test_a=ok + "        Path('ran-a').touch()\n",
            test_b="import unittest\n\n\nclass B(unittest.TestCase):\n    def test_red(self):\n        self.fail('đỏ')\n",
        )
        r = self.dt("test")
        self.assertNotEqual(r.returncode, 0, r.stderr)
        self.assertTrue((self.tmp / "ran-a").exists())  # module xanh vẫn chạy
        self.assertIn("AssertionError: đỏ", r.stderr)

    def test_unittest_import_error_is_red(self):
        self.tests_dir(
            test_a="import unittest\n\n\nclass A(unittest.TestCase):\n    def test_ok(self):\n        pass\n",
            test_broken="import khong_co_module_nay\n",
        )
        for jobs in (None, "1"):
            with self.subTest(jobs=jobs):
                r = self.dt("test", jobs=jobs)
                self.assertNotEqual(r.returncode, 0, r.stderr)
                self.assertIn("khong_co_module_nay", r.stderr)

    def test_unittest_skipped_module_is_not_red(self):
        self.tests_dir(
            test_a="import unittest\n\n\nclass A(unittest.TestCase):\n    def test_ok(self):\n        pass\n",
            test_skip="import unittest\n\nraise unittest.SkipTest('không áp dụng')\n",
        )
        r = self.dt("test")
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_unittest_jobs_one_keeps_discover(self):
        self.tests_dir(
            test_a="import unittest\n\n\nclass A(unittest.TestCase):\n    def test_ok(self):\n        pass\n"
        )
        r = self.dt("test", jobs="1")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.ran(r), "python3 -m unittest discover -s tests")

    def test_unittest_no_tests_is_red_like_before(self):
        self.tests_dir(helper="X = 1\n")
        for jobs in (None, "1"):
            with self.subTest(jobs=jobs):
                r = self.dt("test", jobs=jobs)
                self.assertEqual(r.returncode, 5, r.stderr)
                self.assertIn("Ran 0 tests", r.stderr)

    def test_detected_commands_pass_guard(self):
        """Dự án đích có xt.py + guard cạnh dev-task.sh → lệnh tự dò qua `guard-check` (LOOP-STOP-027): lệnh mới được
        chạy ở cả chính sách mặc định lẫn strict; guard vẫn sống (lệnh khai báo bị cấm → 126, không chạy)."""
        shutil.copy(ROOT / "scripts" / "xt.py", self.tmp / "scripts" / "xt.py")
        shutil.copytree(ROOT / ".claude" / "hooks", self.tmp / ".claude" / "hooks")
        self.tests_dir(
            test_a="import unittest\n\n\nclass A(unittest.TestCase):\n    def test_ok(self):\n        pass\n"
        )
        for policy in ("default", "strict"):
            with self.subTest(policy=policy):
                r = self.dt("test", XT_GUARD_POLICY=policy)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertIn("xargs -r -P", self.ran(r))
                (self.tmp / "xt.yaml").write_text("test: git push --force origin main\n", encoding="utf-8")
                r = self.dt("test", XT_GUARD_POLICY=policy)
                self.assertEqual(r.returncode, 126, r.stderr)
                (self.tmp / "xt.yaml").unlink()
        self.pytest(xdist=True)
        r = self.dt("test", XT_GUARD_POLICY="strict")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("PYTEST-ARGS: -q -n auto", r.stdout)


if __name__ == "__main__":
    unittest.main()
