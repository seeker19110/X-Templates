"""Test cho `xt.py perf` (compare · sample · guard): thống kê so mẫu đo và chặn gian lận số đo (LOOP-OPT-*)."""

from __future__ import annotations

import io
import json
import os
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
        # không đổi gì thì không thể là cải thiện, kể cả khi sàn = 0
        self.assertEqual(xt.perf_compare([5.0], [5.0], exact=True, min_effect=0)["verdict"], "neutral")

    def test_compare_zero_median(self):
        z = [0.0] * 12
        self.assertEqual(xt.perf_compare(z, z)["verdict"], "neutral")
        self.assertEqual(xt.perf_compare(z, [1.0] * 12)["verdict"], "regressed")


class PerfSampleTest(unittest.TestCase):
    def test_timeout_kills_the_whole_process_group(self):
        with tempfile.TemporaryDirectory() as d:
            pidfile = Path(d) / "pid"
            script = f"sleep 30 & echo $! > {pidfile}; wait"
            with self.assertRaisesRegex(RuntimeError, "quá"):
                xt.perf_sample(["sh", "-c", script], runs=1, warmup=0, timeout=1)
            pid = int(pidfile.read_text())
        self.assert_dead(pid)

    def assert_dead(self, pid: int) -> None:
        for _ in range(50):
            try:
                state = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[0]
            except OSError:  # đã biến mất (hoặc không có /proc: thử kill 0)
                try:
                    os.kill(pid, 0)
                except ProcessLookupError:
                    return
                state = "?"
            if state == "Z":  # zombie chưa được init thu dọn vẫn là đã chết
                return
            time.sleep(0.1)
        os.kill(pid, 9)
        self.fail("tiến trình cháu vẫn chạy")

    def test_background_leftovers_are_killed_after_normal_exit(self):
        with tempfile.TemporaryDirectory() as d:
            pidfile = Path(d) / "pid"
            xt.perf_sample(["sh", "-c", f"sleep 30 & echo $! > {pidfile}; exit 0"], runs=1, warmup=0, timeout=30)
            pid = int(pidfile.read_text())
        self.assert_dead(pid)

    def test_interrupt_kills_and_reraises(self):
        real_wait = subprocess.Popen.wait
        calls: list[int] = []

        def wait(proc, timeout=None):
            calls.append(1)
            if len(calls) == 1:
                raise KeyboardInterrupt
            return real_wait(proc, timeout)

        with unittest.mock.patch.object(subprocess.Popen, "wait", wait):
            with self.assertRaises(KeyboardInterrupt):
                xt._perf_run([sys.executable, "-c", "import time; time.sleep(30)"], 30)
        self.assertEqual(len(calls), 2)  # sau khi giết nhóm vẫn wait để không để zombie

    def test_group_already_gone(self):
        with unittest.mock.patch.object(os, "killpg", side_effect=ProcessLookupError):
            with self.assertRaises(subprocess.TimeoutExpired):
                xt._perf_run([sys.executable, "-c", "import time; time.sleep(1)"], 0.1)

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


ISOLATED = {
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_SYSTEM": os.devnull,
}  # không để cấu hình git của máy lọt vào test


def git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True, env={**os.environ, **ISOLATED})


class PerfGuardTest(unittest.TestCase):
    def setUp(self):
        patcher = unittest.mock.patch.dict(os.environ, ISOLATED)
        patcher.start()
        self.addCleanup(patcher.stop)

    def make_repo(self) -> Path:
        d = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(d, ignore_errors=True))
        git(d, "init", "-q", "-b", "main")
        git(d, "config", "user.email", "t@t")
        git(d, "config", "user.name", "t")
        git(d, "config", "commit.gpgsign", "false")
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

    def test_diff_independent_of_user_git_config(self):
        d = self.make_repo()
        (d / "bench" / "run.py").write_text("print(2)\n")
        for key in ("diff.noprefix", "diff.mnemonicPrefix"):
            with unittest.mock.patch.dict(
                os.environ, {"GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": key, "GIT_CONFIG_VALUE_0": "true"}
            ):
                files, added = xt.perf_diff(d, "HEAD")
            self.assertEqual(files, ["bench/run.py"], key)
            self.assertEqual(added, [("bench/run.py", "print(2)")], key)

    def test_diff_quoted_names_are_listed(self):
        d = self.make_repo()
        names = ['bench/q"x.py', "bench/back\\slash.py"]
        for n in names:
            (d / n).write_text("x\n")
        git(d, "add", ".")
        git(d, "commit", "-qm", "odd")
        for n in names:
            (d / n).write_text("print(2)\n")
        files, added = xt.perf_diff(d, "HEAD")
        self.assertEqual(sorted(files), sorted(names))
        self.assertEqual([f for f, _ in added], [xt.PERF_ODD_NAME] * 2)
        touched, _ = xt.perf_guard(files, added, ["bench/*"])
        self.assertEqual(sorted(touched), sorted(names))

    def test_untracked_symlink_to_fifo_does_not_hang(self):
        d = self.make_repo()
        fifo = d.parent / (d.name + ".fifo")
        os.mkfifo(fifo)
        self.addCleanup(lambda: fifo.unlink())
        os.symlink(fifo, d / "bench" / "l")
        done = []
        th = __import__("threading").Thread(target=lambda: done.append(xt.perf_diff(d, "HEAD")), daemon=True)
        th.start()
        th.join(10)
        self.assertEqual(len(done), 1, "perf_diff treo trên symlink → FIFO")
        files, added = done[0]
        self.assertEqual(files, ["bench/l"])
        self.assertEqual(added, [("bench/l", str(fifo))])  # quét chuỗi đích, không đọc nội dung đích

    def test_untracked_non_regular_and_vanished(self):
        d = self.make_repo()
        self.assertEqual(xt._perf_untracked_lines(d, ["bench"]), [])  # thư mục: không phải file thường
        self.assertEqual(xt._perf_untracked_lines(d, ["no-such"]), [])  # biến mất giữa hai lệnh git

    def test_untracked_files_are_checked(self):
        d = self.make_repo()
        (d / "bench" / "sitecustomize.py").write_text("import functools\nf = functools.lru_cache\n")
        os.symlink(d / "gone", d / "bench" / "dangling")  # symlink hỏng: tính là file đổi, không có dòng để quét
        files, added = xt.perf_diff(d, "HEAD")
        self.assertEqual(sorted(files), ["bench/dangling", "bench/sitecustomize.py"])
        touched, suspect = xt.perf_guard(files, added, ["bench/*"])
        self.assertEqual(len(touched), 2)
        self.assertEqual(len(suspect), 1)

    def test_known_and_match(self):
        d = self.make_repo()
        (d / "new.py").write_text("x\n")
        self.assertEqual(sorted(xt.perf_known(d)), ["app.py", "bench/run.py", "dir with space/b é.py", "new.py"])
        self.assertTrue(xt.perf_match("bench/run.py", "bench/*"))
        self.assertTrue(xt.perf_match("bench/a/b.py", "bench/*"))  # `*` đi qua `/`: khoá cả cây
        self.assertTrue(xt.perf_match("bench/run.py", "bench/**/*.py"))  # `**/` nhận cả không thư mục con
        self.assertTrue(xt.perf_match("bench/a/run.py", "./bench/**/*.py"))
        self.assertFalse(xt.perf_match("app.py", "bench/*"))

    def test_diff_bad_ref(self):
        d = self.make_repo()
        with self.assertRaisesRegex(RuntimeError, "git diff lỗi"):
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

    def test_suspect_regex_new_forms(self):
        for line in (
            "time.perf_counter_ns = fake",
            "time.perf_counter =",
            'mock.patch("time.perf_counter")',
            'setattr(time, "perf_counter", f)',
        ):
            self.assertTrue(xt.PERF_SUSPECT_RE.search(line), line)
        for line in ("@functools.cached_property", "if perf_counter == 3:", "monkeypatch.setenv('A', 'b')"):
            self.assertFalse(xt.PERF_SUSPECT_RE.search(line), line)

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

    def test_compare_refuses_different_commands(self):
        for name, cmd in (("a.json", ["x"]), ("b.json", ["y"]), ("c.json", ["x"])):
            (self.tmp / name).write_text(json.dumps({"samples": SLOW, "cmd": cmd}))
        rc, _, err = run_main("perf", "compare", self.p("a.json"), self.p("b.json"))
        self.assertEqual(rc, 2)
        self.assertIn("hai lệnh khác nhau", err)
        rc, _, _ = run_main("perf", "compare", self.p("a.json"), self.p("c.json"), "--no-regress")
        self.assertEqual(rc, 0)
        rc, _, _ = run_main("perf", "compare", self.p("a.json"), self.p("slow.json"), "--no-regress")
        self.assertEqual(rc, 0)  # một bên không ghi lệnh (tay làm): không chặn
        self.assertIsNone(xt.perf_cmd_of(self.p("slow.json")))  # mảng JSON, không phải đối tượng
        (self.tmp / "t.txt").write_text("1 2 3")
        self.assertIsNone(xt.perf_cmd_of(self.p("t.txt")))

    def test_runs_must_be_positive(self):
        for argv in (
            ("perf", "sample", "--out", self.p("s.json"), "--runs", "0", "--", "true"),
            ("perf", "sample", "--out", self.p("s.json"), "--warmup", "-1", "--", "true"),
            ("perf", "sample", "--out", self.p("s.json"), "--warmup", "x", "--", "true"),
            ("perf", "compare", self.p("slow.json"), self.p("fast.json"), "--min-runs", "0"),
            ("perf", "compare", self.p("slow.json"), self.p("fast.json"), "--min-runs", "x"),
        ):
            with self.assertRaises(SystemExit) as cm, unittest.mock.patch.object(sys, "stderr", io.StringIO()):
                run_main(*argv)
            self.assertEqual(cm.exception.code, 2)

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

    def test_guard_outside_git_repo(self):
        old_cwd = os.getcwd()
        self.addCleanup(os.chdir, old_cwd)
        os.chdir(self.tmp)
        with unittest.mock.patch.dict("os.environ", {**ISOLATED, "GIT_CEILING_DIRECTORIES": str(self.tmp.parent)}):
            rc, _, err = run_main("perf", "guard", "--base", "HEAD")
        self.assertEqual(rc, 2)
        self.assertIn("không ở trong repo git", err)

    def test_guard_works_from_subdirectory(self):
        d = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(d, ignore_errors=True))
        for args in (("init", "-q", "-b", "main"), ("config", "user.email", "t@t"), ("config", "user.name", "t")):
            git(d, *args)
        git(d, "config", "commit.gpgsign", "false")
        (d / "sub").mkdir()
        (d / "sub" / "a.py").write_text("x\n")
        git(d, "add", ".")
        git(d, "commit", "-qm", "i")
        (d / "sub" / "a.py").write_text("y\n")
        old_cwd = os.getcwd()
        self.addCleanup(os.chdir, old_cwd)
        os.chdir(d / "sub")
        with unittest.mock.patch.dict("os.environ", ISOLATED):
            rc, out, _ = run_main("perf", "guard", "--base", "HEAD", "--locked", "sub/a.py")
        self.assertEqual(rc, 1)
        self.assertIn("sub/a.py", out)

    def test_guard_ignores_git_env_pointing_elsewhere(self):
        d = Path(tempfile.mkdtemp())
        clean = Path(tempfile.mkdtemp())
        for p in (d, clean):
            self.addCleanup(lambda p=p: __import__("shutil").rmtree(p, ignore_errors=True))
        for args in (("init", "-q", "-b", "main"), ("config", "user.email", "t@t"), ("config", "user.name", "t")):
            git(d, *args)
        git(d, "config", "commit.gpgsign", "false")
        (d / "bench.py").write_text("x\n")
        git(d, "add", ".")
        git(d, "commit", "-qm", "i")
        subprocess.run(["git", "clone", "-q", str(d), str(clean)], check=True, env={**os.environ, **ISOLATED})
        (d / "bench.py").write_text("y\n")  # cây agent sửa file khoá; GIT_DIR/GIT_WORK_TREE trỏ clone sạch
        old_cwd = os.getcwd()
        self.addCleanup(os.chdir, old_cwd)
        os.chdir(d)
        env = {**ISOLATED, "GIT_DIR": str(clean / ".git"), "GIT_WORK_TREE": str(clean)}
        with unittest.mock.patch.dict("os.environ", env):
            rc, out, _ = run_main("perf", "guard", "--base", "HEAD", "--locked", "bench.py")
        self.assertEqual(rc, 1)
        self.assertIn("✗ đụng file khoá", out)

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
        git(d, "config", "commit.gpgsign", "false")
        # CLAUDE_PROJECT_DIR trỏ chỗ khác (như khi chạy xt.py của worktree gốc): guard vẫn rà thư mục đang đứng
        env = {"CLAUDE_PROJECT_DIR": str(self.tmp), **ISOLATED}
        old_cwd = os.getcwd()
        self.addCleanup(os.chdir, old_cwd)
        os.chdir(d)
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
            rc, _, err = run_main("perf", "guard", "--base", "HEAD", "--locked", "bech/*")
            self.assertEqual(rc, 2)
            self.assertIn("không khớp file nào", err)
            rc, _, _ = run_main("perf", "guard", "--base", "HEAD", "--locked", "./**/bench.py")
            self.assertEqual(rc, 1)
            rc, _, err = run_main("perf", "guard", "--base", "no-such-ref")
            self.assertEqual(rc, 2)
            self.assertIn("git diff lỗi", err)


if __name__ == "__main__":
    unittest.main()
