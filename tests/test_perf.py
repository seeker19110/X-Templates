"""Test cho `xt.py perf` (compare · sample · guard): thống kê so mẫu đo và chặn gian lận số đo (LOOP-OPT-*)."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import time
import unittest
import unittest.mock
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import xt
from test_xt_cli import run_main

SLOW = [1.00, 1.02, 0.99, 1.01, 1.00, 0.98, 1.03, 1.00, 1.01, 0.99, 1.02, 1.00]
FAST = [0.80, 0.81, 0.79, 0.80, 0.82, 0.80, 0.78, 0.80, 0.81, 0.79, 0.80, 0.80]


class PerfStatsTest(unittest.TestCase):
    def test_load_formats_and_errors(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / "arr.json").write_text("[1, 2.5, 3]")
            (p / "obj.json").write_text('{"samples": [4, 5]}')
            (p / "txt").write_text("1 2,3\n4")
            (p / "scalar.json").write_text("7")
            (p / "bad").write_text("1 abc")
            (p / "inf.json").write_text("[1, 1e999]")
            (p / "nosamples.json").write_text('{"x": 1}')
            self.assertEqual(xt.perf_load(str(p / "arr.json")), [1.0, 2.5, 3.0])
            self.assertEqual(xt.perf_load(str(p / "obj.json")), [4.0, 5.0])
            self.assertEqual(xt.perf_load(str(p / "txt")), [1.0, 2.0, 3.0, 4.0])
            self.assertEqual(xt.perf_load(str(p / "scalar.json")), [7.0])
            with self.assertRaisesRegex(ValueError, "không phải số"):
                xt.perf_load(str(p / "bad"))
            with self.assertRaisesRegex(ValueError, "không hữu hạn"):
                xt.perf_load(str(p / "inf.json"))
            with self.assertRaisesRegex(ValueError, "không phải số"):
                xt.perf_load(str(p / "nosamples.json"))

    def test_mann_whitney(self):
        self.assertAlmostEqual(xt.mann_whitney_p([1.0] * 5, [1.0] * 5), 1.0)  # mọi giá trị bằng nhau
        self.assertLess(xt.mann_whitney_p(SLOW, FAST), 0.001)
        self.assertGreater(xt.mann_whitney_p(SLOW, SLOW), 0.9)
        self.assertAlmostEqual(xt.mann_whitney_p(SLOW, FAST), xt.mann_whitney_p(FAST, SLOW))  # hai phía, đối xứng
        ties = xt.mann_whitney_p([1, 1, 2, 2, 3], [2, 2, 3, 3, 4])  # có trùng hạng
        self.assertTrue(0.0 < ties < 1.0)

    def test_rel_change(self):
        self.assertAlmostEqual(xt._rel_change(2.0, 1.0), -0.5)
        self.assertEqual(xt._rel_change(0.0, 0.0), 0.0)
        self.assertEqual(xt._rel_change(0.0, 3.0), float("inf"))
        self.assertEqual(xt._rel_change(0.0, -3.0), float("-inf"))

    def test_compare_verdicts(self):
        self.assertEqual(xt.perf_compare(SLOW, FAST)["verdict"], "improved")
        self.assertEqual(xt.perf_compare(FAST, SLOW)["verdict"], "regressed")
        self.assertEqual(xt.perf_compare(SLOW, SLOW)["verdict"], "neutral")
        # càng cao càng tốt: đảo chiều
        self.assertEqual(xt.perf_compare(FAST, SLOW, higher_is_better=True)["verdict"], "improved")
        self.assertEqual(xt.perf_compare(SLOW, FAST, higher_is_better=True)["verdict"], "regressed")

    def test_compare_noise_floor_and_min_effect(self):
        noisy = [1.0, 1.4, 0.7, 1.3, 0.8, 1.2, 0.9, 1.5, 0.6, 1.1, 1.0, 1.0]
        shifted = [x * 0.97 for x in noisy]  # −3 %: có ý nghĩa thống kê (cặp đôi) nhưng nhỏ hơn nhiễu máy đo
        self.assertEqual(xt.perf_compare(noisy, shifted)["verdict"], "neutral")
        small = [x * 0.99 for x in SLOW]  # −1 % < sàn 2 %
        self.assertEqual(xt.perf_compare(SLOW, small, min_effect=0.02)["verdict"], "neutral")
        self.assertEqual(xt.perf_compare(SLOW, small, min_effect=0.001, alpha=0.5)["verdict"], "improved")

    def test_compare_insufficient_and_exact(self):
        r = xt.perf_compare(SLOW[:5], FAST)
        self.assertEqual(r["verdict"], "insufficient")
        self.assertIn("≥ 10", r["reason"])
        self.assertEqual(xt.perf_compare([], [1.0], exact=True)["verdict"], "insufficient")
        self.assertEqual(xt.perf_compare([1000.0], [900.0], exact=True)["verdict"], "improved")
        self.assertEqual(xt.perf_compare([900.0], [1000.0], exact=True)["verdict"], "regressed")
        self.assertEqual(xt.perf_compare([1000.0], [995.0], exact=True)["verdict"], "neutral")
        self.assertIsNone(xt.perf_compare([1.0], [2.0], exact=True)["p"])

    def test_compare_zero_median(self):
        z = [0.0] * 12
        self.assertEqual(xt.perf_compare(z, z)["verdict"], "neutral")
        self.assertEqual(xt.perf_compare(z, [1.0] * 12)["verdict"], "regressed")


class PerfSampleTest(unittest.TestCase):
    def test_sample_runs_and_discards_warmup(self):
        out = xt.perf_sample([sys.executable, "-c", "pass"], runs=3, warmup=1, timeout=60)
        self.assertEqual(len(out), 3)
        self.assertTrue(all(x > 0 for x in out))

    def test_sample_failing_command(self):
        with self.assertRaisesRegex(RuntimeError, "thoát 3 ở lần 1"):
            xt.perf_sample([sys.executable, "-c", "raise SystemExit(3)"], runs=2, warmup=0, timeout=60)

    def test_sample_timeout(self):
        with self.assertRaisesRegex(RuntimeError, "quá 0.2 s ở lần 1"):
            xt.perf_sample([sys.executable, "-c", "import time; time.sleep(5)"], runs=1, warmup=0, timeout=0.2)


def git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True)


class PerfGuardTest(unittest.TestCase):
    def make_repo(self) -> Path:
        d = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(d, ignore_errors=True))
        git(d, "init", "-q", "-b", "main")
        git(d, "config", "user.email", "t@t")
        git(d, "config", "user.name", "t")
        (d / "bench").mkdir()
        (d / "dir with space").mkdir()
        (d / "dir with space" / "b é.py").write_text("x\n")
        (d / "bench" / "run.py").write_text("print(1)\n")
        (d / "app.py").write_text("def f(x):\n    return x\n")
        git(d, "add", ".")
        git(d, "commit", "-qm", "init")
        return d

    def test_diff_parses_files_and_added_lines(self):
        d = self.make_repo()
        (d / "app.py").write_text("def f(x):\n    return x + 1\n")
        (d / "new.py").write_text("a = 1\n")
        git(d, "add", "new.py")
        (d / "bench" / "run.py").unlink()
        (d / "dir with space" / "b é.py").unlink()
        files, added = xt.perf_diff(d, "HEAD")
        self.assertIn("app.py", files)
        self.assertIn("new.py", files)
        self.assertIn("bench/run.py", files)
        self.assertNotIn("/dev/null", files)
        self.assertIn("dir with space/b é.py", files)
        self.assertEqual(len(files), 4)
        self.assertIn(("app.py", "    return x + 1"), added)

    def test_diff_bad_ref(self):
        d = self.make_repo()
        with self.assertRaisesRegex(RuntimeError, "git diff nonexistent lỗi"):
            xt.perf_diff(d, "nonexistent")

    def test_guard_locked_and_suspect(self):
        files = ["bench/run.py", "app.py", "tests/equiv/t.py"]
        added = [
            ("app.py", "@functools.lru_cache(maxsize=None)"),
            ("app.py", "    time.sleep(0.1)"),
            ("app.py", "perf_counter = lambda: 0.0"),
            ("app.py", "if a == b:"),
            ("app.py", "x = perf_counter() - t0"),
            ("app.py", "frame = sys._getframe(1)"),
            ("app.py", "memoize(f)"),
        ]
        touched, suspect = xt.perf_guard(files, added, ["bench/*", "tests/equiv/*"])
        self.assertEqual(touched, ["bench/run.py", "tests/equiv/t.py"])
        self.assertEqual(len(suspect), 5)
        self.assertEqual(xt.perf_guard(files, [], [])[0], [])

    def test_guard_regex_is_linear(self):
        line = "perf_counter" + " " * 50000 + "x"
        start = time.perf_counter()
        self.assertIsNone(xt.PERF_SUSPECT_RE.search(line))
        self.assertLess(time.perf_counter() - start, 1.0)


class PerfCliTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(self.tmp, ignore_errors=True))
        (self.tmp / "slow.json").write_text(json.dumps(SLOW))
        (self.tmp / "fast.json").write_text(json.dumps(FAST))

    def p(self, name: str) -> str:
        return str(self.tmp / name)

    def test_compare_exit_codes_and_output(self):
        rc, out, _ = run_main("perf", "compare", self.p("slow.json"), self.p("fast.json"))
        self.assertEqual(rc, 0)
        self.assertIn("improved", out)
        rc, out, _ = run_main("perf", "compare", self.p("fast.json"), self.p("slow.json"))
        self.assertEqual(rc, 1)
        self.assertIn("regressed", out)
        rc, _, _ = run_main("perf", "compare", self.p("slow.json"), self.p("slow.json"))
        self.assertEqual(rc, 1)  # neutral không đủ để khẳng định đã tối ưu
        rc, _, _ = run_main("perf", "compare", self.p("slow.json"), self.p("slow.json"), "--no-regress")
        self.assertEqual(rc, 0)
        rc, out, _ = run_main("perf", "compare", self.p("slow.json"), self.p("fast.json"), "--json")
        self.assertEqual(json.loads(out)["verdict"], "improved")
        rc, out, _ = run_main("perf", "compare", self.p("fast.json"), self.p("slow.json"), "--higher-is-better")
        self.assertEqual(rc, 0)

    def test_compare_exact_and_insufficient_output(self):
        (self.tmp / "one.txt").write_text("1000")
        (self.tmp / "two.txt").write_text("900")
        rc, out, _ = run_main("perf", "compare", self.p("one.txt"), self.p("two.txt"), "--exact")
        self.assertEqual(rc, 0)
        self.assertIn("tất định", out)
        rc, out, _ = run_main("perf", "compare", self.p("one.txt"), self.p("two.txt"))
        self.assertEqual(rc, 1)
        self.assertIn("thiếu mẫu", out)

    def test_compare_bad_file(self):
        (self.tmp / "bad").write_text("abc")
        rc, _, err = run_main("perf", "compare", self.p("bad"), self.p("fast.json"))
        self.assertEqual(rc, 2)
        self.assertIn("không phải số", err)

    def test_sample_writes_file(self):
        out_file = self.p("s.json")
        rc, out, _ = run_main(
            "perf", "sample", "--out", out_file, "--runs", "3", "--warmup", "0", "--", sys.executable, "-c", "pass"
        )
        self.assertEqual(rc, 0)
        self.assertIn("3 mẫu", out)
        doc = json.loads(Path(out_file).read_text())
        self.assertEqual(len(doc["samples"]), 3)
        self.assertEqual(doc["unit"], "s")
        self.assertIn("commit", doc)
        self.assertEqual(len(xt.perf_load(out_file)), 3)

    def test_sample_errors(self):
        rc, _, err = run_main("perf", "sample", "--out", self.p("s.json"))
        self.assertEqual(rc, 2)
        self.assertIn("thiếu lệnh", err)
        rc, _, err = run_main(
            "perf", "sample", "--out", self.p("s.json"), "--runs", "1", "--warmup", "0", sys.executable, "-c", "exit(2)"
        )
        self.assertEqual(rc, 1)
        self.assertIn("thoát 2", err)

    def test_sample_commit_empty_outside_git(self):
        bad = subprocess.CompletedProcess([], 128, "", "not a repo")
        with unittest.mock.patch.object(xt, "_git", return_value=bad):
            rc, _, _ = run_main(
                "perf",
                "sample",
                "--out",
                self.p("s.json"),
                "--runs",
                "1",
                "--warmup",
                "0",
                sys.executable,
                "-c",
                "pass",
            )
        self.assertEqual(rc, 0)
        self.assertEqual(json.loads(Path(self.p("s.json")).read_text())["commit"], "")

    def test_guard_cli(self):
        d = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(d, ignore_errors=True))
        git(d, "init", "-q", "-b", "main")
        git(d, "config", "user.email", "t@t")
        git(d, "config", "user.name", "t")
        (d / "bench.py").write_text("print(1)\n")
        (d / "app.py").write_text("x = 1\n")
        git(d, "add", ".")
        git(d, "commit", "-qm", "init")
        env = {"CLAUDE_PROJECT_DIR": str(d)}
        with unittest.mock.patch.dict("os.environ", env):
            rc, out, _ = run_main("perf", "guard", "--base", "HEAD")
            self.assertEqual(rc, 0)
            self.assertIn("không đụng file khoá", out)
            (d / "app.py").write_text("import functools\n@functools.lru_cache\ndef f(): pass\n")
            rc, out, _ = run_main("perf", "guard", "--base", "HEAD", "--locked", "bench.py")
            self.assertEqual(rc, 0)
            self.assertIn("⚠", out)
            rc, _, _ = run_main("perf", "guard", "--base", "HEAD", "--strict")
            self.assertEqual(rc, 1)
            (d / "bench.py").write_text("print(2)\n")
            rc, out, _ = run_main("perf", "guard", "--base", "HEAD", "--locked", "bench.py")
            self.assertEqual(rc, 1)
            self.assertIn("✗ đụng file khoá", out)
            rc, _, err = run_main("perf", "guard", "--base", "no-such-ref")
            self.assertEqual(rc, 2)
            self.assertIn("git diff no-such-ref lỗi", err)


if __name__ == "__main__":
    unittest.main()
