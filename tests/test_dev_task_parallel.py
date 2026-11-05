"""T-3708 (D-367, D-369): lệnh test TỰ DÒ của `scripts/dev-task.sh` — pytest có xdist chạy song song
(`python3 -m pytest -q -n <JOBS>`) trừ khi cấu hình tắt xdist; unittest giữ `discover -s tests` tuần tự như cũ;
`XT_JOBS` chọn số tiến trình (1 = `pytest -q`, rác = `auto`, trần 4×số nhân). Lệnh khai báo trong xt.yaml không đổi.
Dự án giả trong thư mục tạm, PATH chỉ gồm công cụ cần thiết (không lọt pytest/ruff của máy), xdist giả qua PYTHONPATH;
"không có xdist" = `python3 -S` (che site-packages của máy) và không có xdist giả."""

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
TOOLS = "bash sh dirname basename grep sed awk tail head mktemp tee rm cat xargs getconf sort ls sleep touch env"
NPROC = 2  # `nproc` giả → trần XT_JOBS = 8
FAKE_PYTEST = '#!/bin/sh\necho "PYTEST-ARGS: $*"\n'
# `python3 -m pytest` (có xdist): module giả trên PYTHONPATH — in dấu khác lệnh `pytest` trên PATH để biết lệnh nào chạy.
FAKE_PYTEST_MODULE = 'import sys\n\nprint("PYTEST-MODULE-ARGS: " + " ".join(sys.argv[1:]))\n'
OK_MODULE = "import unittest\n\n\nclass A(unittest.TestCase):\n    def test_ok(self):\n        pass\n"
HINT = "cài pytest-xdist để chạy test song song"


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
        self.script(self.bin / "nproc", f"#!/bin/sh\necho {NPROC}\n")
        self.python(site=True)
        self.pypath = self.tmp / ".py"
        self.pypath.mkdir()

    @staticmethod
    def script(path: Path, body: str) -> None:
        path.write_text(body, encoding="utf-8")
        path.chmod(0o755)

    def python(self, site: bool) -> None:
        flag = "" if site else " -S"  # -S: không nạp site-packages → xdist thật của máy (nếu có) không thấy được
        self.script(self.bin / "python3", f'#!/bin/sh\nexec "{sys.executable}"{flag} "$@"\n')

    def pytest(self, xdist: bool) -> None:
        self.script(self.bin / "pytest", FAKE_PYTEST)
        (self.pypath / "pytest.py").write_text(FAKE_PYTEST_MODULE, encoding="utf-8")
        if xdist:
            (self.pypath / "xdist").mkdir(exist_ok=True)
            (self.pypath / "xdist" / "__init__.py").write_text("", encoding="utf-8")
        self.python(site=False)  # xdist chỉ từ PYTHONPATH giả

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

    def make_tests(self, **mods: str) -> None:  # không đặt tên `test…`: unittest sẽ gom hàm phụ thành test
        d = self.tmp / "tests"
        d.mkdir(exist_ok=True)
        for name, body in mods.items():
            (d / f"{name}.py").write_text(body, encoding="utf-8")

    # --- pytest ---------------------------------------------------------------------------------------------------
    def test_pytest_with_xdist_runs_n_jobs(self):
        """Có xdist → `python3 -m pytest`: cùng interpreter vừa tìm thấy xdist (pytest trên PATH có thể là pipx/venv
        khác không có xdist → `-n` lỗi "unrecognized arguments")."""
        self.pytest(xdist=True)
        for jobs, flag in ((None, "-n auto"), ("3", "-n 3"), ("8", "-n 8"), ("abc", "-n auto"), ("0", "-n auto")):
            with self.subTest(jobs=jobs):
                r = self.dt("test", jobs=jobs)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertEqual(self.ran(r), f"python3 -m pytest -q {flag}")
                self.assertIn(f"PYTEST-MODULE-ARGS: -q {flag}", r.stdout)
                self.assertNotIn("PYTEST-ARGS", r.stdout)  # không chạy pytest trên PATH
                self.assertNotIn(HINT, r.stderr)
                self.assertNotIn("vượt trần", r.stderr)
        self.assertIn("XT_JOBS='abc' không phải số nguyên dương", self.dt("test", jobs="abc").stderr)

    def test_pytest_jobs_above_cap_is_capped(self):
        self.pytest(xdist=True)
        for jobs in ("9", "100000", "999999"):
            with self.subTest(jobs=jobs):
                r = self.dt("test", jobs=jobs)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertEqual(self.ran(r), f"python3 -m pytest -q -n {4 * NPROC}")
                self.assertEqual(r.stderr.count(f"XT_JOBS={jobs} vượt trần 4×số nhân — dùng {4 * NPROC}"), 1, r.stderr)

    def test_pytest_jobs_one_is_sequential(self):
        for xdist in (True, False):
            with self.subTest(xdist=xdist):
                self.pytest(xdist=xdist)
                r = self.dt("test", jobs="1")
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertEqual(self.ran(r), "pytest -q")
                self.assertIn("PYTEST-ARGS: -q\n", r.stdout)
                self.assertNotIn(HINT, r.stderr)  # đã chọn tuần tự: không gợi ý

    def test_pytest_without_xdist_hints_once(self):
        self.pytest(xdist=False)
        (self.tmp / "xt.yaml").write_text('lint: "true | cat"\ntypecheck: ""\nbuild: ""\n', encoding="utf-8")
        for task in ("test", "gate", "gate-par"):
            with self.subTest(task=task):
                r = self.dt(task)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertEqual(self.ran(r), "pytest -q")
                self.assertIn("PYTEST-ARGS: -q\n", r.stdout + r.stderr)
                self.assertEqual(r.stderr.count(HINT), 1, r.stderr)

    def test_pytest_xdist_disabled_by_config_runs_plain(self):
        """Cấu hình tắt xdist có chủ ý → `pytest -q` như cũ, không `-n` (pytest sẽ lỗi "unrecognized arguments"), không
        gợi ý cài xdist."""
        cases = {
            "pyproject addopts": (
                "pyproject.toml",
                "[project]\nname = 'x'\n[tool.pytest.ini_options]\naddopts = \"-p no:xdist\"\n",
                {},
            ),
            "pytest.ini": ("pytest.ini", "[pytest]\naddopts = -p no:xdist\n", {}),
            "setup.cfg": ("setup.cfg", "[tool:pytest]\naddopts = -pno:xdist\n", {}),
            "tox.ini": ("tox.ini", "[pytest]\naddopts = -p no:xdist\n", {}),
            "autoload env": (None, "", {"PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"}),
            "addopts env": (None, "", {"PYTEST_ADDOPTS": "-q -p no:xdist"}),
        }
        for xdist in (True, False):
            for name, (cfg, body, env) in cases.items():
                with self.subTest(xdist=xdist, case=name):
                    self.pytest(xdist=xdist)
                    path = self.tmp / cfg if cfg else None
                    old = path.read_text(encoding="utf-8") if path and path.exists() else None
                    if path:
                        path.write_text(body, encoding="utf-8")
                    r = self.dt("test", **env)
                    if path and old is None:
                        path.unlink()
                    elif path and old is not None:
                        path.write_text(old, encoding="utf-8")
                    self.assertEqual(r.returncode, 0, r.stderr)
                    self.assertEqual(self.ran(r), "pytest -q")
                    self.assertIn("PYTEST-ARGS: -q\n", r.stdout)
                    self.assertNotIn(HINT, r.stderr)

    def test_pytest_root_module_shadowing_falls_back_to_plain(self):
        """D-371: `python3 -m` thêm cwd vào `sys.path` → `pytest.py`/`xdist.py` (tệp hay gói) ở gốc che pytest/xdist thật;
        rơi về `pytest -q` không `-n`, có log lý do. `conftest.py` là cấu hình hợp lệ — không rơi."""
        self.pytest(xdist=True)
        for name, make in (
            ("pytest.py", lambda p: p.write_text("", encoding="utf-8")),
            ("xdist.py", lambda p: p.write_text("", encoding="utf-8")),
            ("pytest", lambda p: (p.mkdir(), (p / "__init__.py").write_text("", encoding="utf-8"))),
            ("xdist", lambda p: (p.mkdir(), (p / "__init__.py").write_text("", encoding="utf-8"))),
        ):
            with self.subTest(shadow=name):
                path = self.tmp / name
                make(path)
                r = self.dt("test")
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertEqual(self.ran(r), "pytest -q")
                self.assertNotIn("-n ", self.ran(r))
                self.assertIn("che pytest/xdist", r.stderr)
                self.assertIn("PYTEST-ARGS: -q\n", r.stdout)
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()
        (self.tmp / "conftest.py").write_text("", encoding="utf-8")
        (self.tmp / "pytest").mkdir()  # thư mục không có __init__.py: không phải gói
        r = self.dt("test")
        self.assertEqual(self.ran(r), "python3 -m pytest -q -n auto")
        self.assertNotIn("che pytest/xdist", r.stderr)

    def test_pytest_empty_autoload_env_is_not_disabled(self):
        self.pytest(xdist=True)
        r = self.dt("test", PYTEST_DISABLE_PLUGIN_AUTOLOAD="", PYTEST_ADDOPTS="-q")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.ran(r), "python3 -m pytest -q -n auto")

    def test_declared_test_command_unchanged(self):
        self.pytest(xdist=True)
        (self.tmp / "xt.yaml").write_text("test: python3 -c 'print(\"DECL\")'\n", encoding="utf-8")
        r = self.dt("test")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.ran(r), "python3 -c 'print(\"DECL\")'")
        self.assertNotIn("PYTEST-ARGS", r.stdout)

    # --- unittest: discover tuần tự như cũ (D-369) -----------------------------------------------------------------
    def test_unittest_keeps_sequential_discover(self):
        self.make_tests(test_a=OK_MODULE)
        for jobs in (None, "1", "4", "abc"):
            with self.subTest(jobs=jobs):
                r = self.dt("test", jobs=jobs)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertEqual(self.ran(r), "python3 -m unittest discover -s tests")
                self.assertNotIn("xargs", r.stderr)
                self.assertNotIn(HINT, r.stderr)

    def test_unittest_setupclass_skip_is_green(self):
        """S1 của review #444: setUpClass ném SkipTest — discover xanh (bộ chia theo module cũ ra exit 5)."""
        self.make_tests(
            test_a=OK_MODULE,
            test_integ="import unittest\n\n\nclass Integ(unittest.TestCase):\n    @classmethod\n"
            "    def setUpClass(cls):\n        raise unittest.SkipTest('no docker')\n\n"
            "    def test_x(self):\n        pass\n",
        )
        r = self.dt("test", jobs="4")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("skipped=1", r.stderr)

    def test_unittest_contract_class_from_other_module_is_red(self):
        """S11 của review #444: lớp test sinh từ module phụ (contract) — discover chạy nó và đỏ đúng lỗi (bộ chia theo
        module cũ bỏ sót lớp → xanh giả)."""
        (self.tmp / "stores.py").write_text(
            "class Mem:\n    def __init__(self):\n        self.d = {}\n\n    def put(self, k, v):\n"
            "        self.d[k] = v\n\n    def get(self, k):\n        return self.d[k]\n\n\n"
            "class Broken(Mem):\n    def get(self, k):\n        return None\n",
            encoding="utf-8",
        )
        self.make_tests(
            contract="import unittest\n\n\ndef contract_for(cls):\n    class C(unittest.TestCase):\n"
            "        def test_roundtrip(self):\n            s = cls()\n            s.put('k', 1)\n"
            "            self.assertEqual(s.get('k'), 1)\n\n    C.__name__ = cls.__name__ + 'Contract'\n    return C\n",
            test_stores="from contract import contract_for\nfrom stores import Broken, Mem\n\n"
            "MemContract = contract_for(Mem)\nBrokenContract = contract_for(Broken)\n",
        )
        r = self.dt("test", jobs="4")
        self.assertEqual(r.returncode, 1, r.stderr)
        self.assertIn("Ran 2 tests", r.stderr)
        self.assertIn("FAILED (failures=1)", r.stderr)

    def test_unittest_import_error_is_red(self):
        self.make_tests(test_a=OK_MODULE, test_broken="import khong_co_module_nay\n")
        r = self.dt("test")
        self.assertEqual(r.returncode, 1, r.stderr)
        self.assertIn("khong_co_module_nay", r.stderr)

    def test_unittest_no_tests_is_red_like_before(self):
        self.make_tests(helper="X = 1\n")
        r = self.dt("test")
        self.assertEqual(r.returncode, 5, r.stderr)
        self.assertIn("Ran 0 tests", r.stderr)

    def test_detected_commands_pass_guard(self):
        """Dự án đích có xt.py + guard cạnh dev-task.sh → lệnh tự dò qua `guard-check` (LOOP-STOP-027): lệnh mới được
        chạy ở cả chính sách mặc định lẫn strict; guard vẫn sống (lệnh khai báo bị cấm → 126, không chạy)."""
        shutil.copy(ROOT / "scripts" / "xt.py", self.tmp / "scripts" / "xt.py")
        shutil.copytree(ROOT / ".claude" / "hooks", self.tmp / ".claude" / "hooks")
        self.make_tests(test_a=OK_MODULE)
        for policy in ("default", "strict"):
            with self.subTest(policy=policy):
                r = self.dt("test", XT_GUARD_POLICY=policy)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertEqual(self.ran(r), "python3 -m unittest discover -s tests")
                (self.tmp / "xt.yaml").write_text("test: git push --force origin main\n", encoding="utf-8")
                r = self.dt("test", XT_GUARD_POLICY=policy)
                self.assertEqual(r.returncode, 126, r.stderr)
                (self.tmp / "xt.yaml").unlink()
        self.pytest(xdist=True)
        for policy in ("default", "strict"):
            with self.subTest(policy=policy, runner="pytest"):
                r = self.dt("test", jobs="3", XT_GUARD_POLICY=policy)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertIn("PYTEST-MODULE-ARGS: -q -n 3", r.stdout)


if __name__ == "__main__":
    unittest.main()
