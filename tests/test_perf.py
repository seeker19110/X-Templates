"""Test cho `xt.py perf` (compare · sample · guard): thống kê so mẫu đo và chặn gian lận số đo (LOOP-OPT-*)."""

from __future__ import annotations

import io
import json
import re
import shutil
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
import cpu_budget
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

    def test_ignore_rules_cannot_hide_new_locked_files(self):
        d = self.make_repo()
        (d / "bench" / "new.py").write_text("x\n")
        ex = d.parent / (d.name + ".ex")
        ex.write_text("*\n")
        self.addCleanup(ex.unlink)
        (d / ".git" / "info").mkdir(exist_ok=True)
        (d / ".git" / "info" / "exclude").write_text("bench/\n")
        env = {"GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "core.excludesFile", "GIT_CONFIG_VALUE_0": str(ex)}
        with unittest.mock.patch.dict(os.environ, env):
            files, added = xt.perf_diff(d, "HEAD")
            known = xt.perf_known(d)
        touched, _ = xt.perf_guard(files, added, ["bench/*"])
        self.assertEqual(touched, ["bench/new.py"])  # excludesFile/info/exclude không giấu được
        self.assertIn("bench/new.py", known)
        (d / ".gitignore").write_text("bench/new.py\n")  # .gitignore mới ở thư mục cha không khoá: không giấu được
        files, added = xt.perf_diff(d, "HEAD")
        touched, suspect = xt.perf_guard(files, added, ["bench/*"])
        self.assertEqual(touched, ["bench/new.py"])
        self.assertEqual(suspect, [".gitignore: đổi luật ignore — có thể giấu file mới trong vùng khoá"])

    def test_perf_guard_self_ignored(self):
        """AUD-XFEAT-005: `.gitignore` mới tự che chính nó (`*`) trong vùng khoá vẫn bị thấy — file chưa theo dõi đổi phép
        đo (`bench/conftest.py`) không lọt."""
        d = self.make_repo()
        (d / "bench" / ".gitignore").write_text("*\n")
        (d / "bench" / "conftest.py").write_text("import functools\n")
        files, added = xt.perf_diff(d, "HEAD")
        touched, suspect = xt.perf_guard(files, added, ["bench/*"])
        self.assertIn("bench/conftest.py", touched)
        self.assertIn("bench/.gitignore", touched)
        self.assertTrue(suspect)

    def test_perf_guard_ignored_dir_gitignore_is_not_a_rule_change(self):
        """Review #162: `.gitignore` nằm trong thư mục đã bị ignore (`.venv/.gitignore` do venv sinh, gói trong
        `node_modules/`) không phải luật ignore mới — không báo ⚠, không kéo mọi file chưa theo dõi vào danh sách đổi."""
        d = self.make_repo()
        (d / ".gitignore").write_text(".venv/\nnode_modules/\n")
        git(d, "add", ".gitignore")
        git(d, "commit", "-qm", "ignore")
        (d / ".venv").mkdir()
        (d / ".venv" / ".gitignore").write_text("*\n")
        (d / "node_modules" / "pkg").mkdir(parents=True)
        (d / "node_modules" / "pkg" / ".gitignore").write_text("dist\n")
        (d / "node_modules" / "pkg" / "x.js").write_text("1\n")
        files, added = xt.perf_diff(d, "HEAD")
        self.assertEqual(xt.perf_guard(files, added, ["bench/*"]), ([], []))
        self.assertEqual(xt._perf_self_hidden_rules(d), [])

    def test_perf_guard_self_ignored_in_new_subdir(self):
        """Review #162 (lần 2): thư mục con MỚI `bench/sub/` chỉ có `.gitignore` = `*` + `conftest.py` — `git check-ignore`
        báo `bench/sub/` bị ignore bởi chính `.gitignore` chưa theo dõi đó; `info/exclude` cũng không được tin. Chỉ
        `.gitignore` ĐÃ THEO DÕI mới làm thư mục cha thành "đã ignore sẵn"; mẫu phủ định `!` không ignore."""
        d = self.make_repo()
        (d / "bench" / "sub").mkdir()
        (d / "bench" / "sub" / ".gitignore").write_text("*\n")
        (d / "bench" / "sub" / "conftest.py").write_text("import functools\n")
        files, added = xt.perf_diff(d, "HEAD")
        touched, suspect = xt.perf_guard(files, added, ["bench/*"])
        self.assertEqual(touched, ["bench/sub/.gitignore", "bench/sub/conftest.py"])
        self.assertTrue(suspect)
        (d / ".git" / "info" / "exclude").write_text("bench/sub/\n")
        self.assertEqual(xt._perf_self_hidden_rules(d), ["bench/sub/.gitignore"])
        (d / ".gitignore").write_text("bench/sub/\n!bench/sub/\n")  # phủ định ở .gitignore đã theo dõi: không ignore
        git(d, "add", ".gitignore")
        git(d, "commit", "-qm", "ignore")
        (d / "bench" / "sub" / ".gitignore").write_text(".gitignore\n")  # chỉ che chính nó, không che thư mục
        self.assertEqual(xt._perf_self_hidden_rules(d), ["bench/sub/.gitignore"])
        (d / ".gitignore").write_text("bench/sub/\n")  # .gitignore đã theo dõi ignore thư mục: không phải luật mới
        git(d, "add", ".gitignore")
        git(d, "commit", "-qm", "ignore2")
        self.assertEqual(xt._perf_self_hidden_rules(d), [])

    def test_perf_guard_non_utf8_name_is_suspect(self):
        """Review #165: `_git` giải mã `errors=replace` nên tên file `bench\\xe9.py` thành `bench\\ufffd.py` — không mở lại
        được để quét nội dung; không được qua lặng lẽ (trước đó sập, nay phải báo đáng ngờ)."""
        d = self.make_repo()
        (d / os.fsdecode(b"bench\xe9.py")).write_text("import functools\n@functools.lru_cache\n")
        files, added = xt.perf_diff(d, "HEAD")
        _touched, suspect = xt.perf_guard(files, added, ["bench/*"])
        self.assertEqual(len(suspect), 1)
        self.assertIn("không phải UTF-8", suspect[0])
        (d / "plain.py").write_text("@functools.lru_cache\n")
        files, added = xt.perf_diff(d, "HEAD")
        self.assertEqual(len(xt.perf_guard(files, added, ["bench/*"])[1]), 2)

    def test_perf_self_hidden_root_and_git_error(self):
        d = self.make_repo()
        (d / ".gitignore").write_text("*\n")  # `.gitignore` gốc chưa theo dõi tự che: vẫn là luật ignore mới
        self.assertEqual(xt._perf_self_hidden_rules(d), [".gitignore"])
        fail = subprocess.CompletedProcess([], 128, "", "fatal: x")
        with unittest.mock.patch.object(xt, "_perf_git_names", return_value=["a/.gitignore"]):
            with unittest.mock.patch.object(xt, "_git", return_value=fail):
                with self.assertRaises(RuntimeError):
                    xt._perf_self_hidden_rules(d)

    def test_generated_files_ignored_in_tree_are_not_lock_touches(self):
        d = self.make_repo()
        (d / ".gitignore").write_text("__pycache__/\n")
        git(d, "add", ".gitignore")
        git(d, "commit", "-qm", "ignore")
        (d / "bench" / "__pycache__").mkdir()
        (d / "bench" / "__pycache__" / "run.cpython-313.pyc").write_bytes(b"\x00")
        files, added = xt.perf_diff(d, "HEAD")
        self.assertEqual(xt.perf_guard(files, added, ["bench/*"]), ([], []))

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
        self.assertIsNone(xt.PERF_SUSPECT_RE.search("perf_counter" + " " * 50000 + "x"))
        cpu_budget.assert_not_quadratic(
            self, lambda n: xt.PERF_SUSPECT_RE.search("perf_counter" + " " * n + "x"), 12500
        )


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
        self.assertIsNone(xt.perf_cmd_of((self.tmp / "slow.json").read_text()))  # mảng JSON, không phải đối tượng
        (self.tmp / "t.txt").write_text("1 2 3")
        self.assertIsNone(xt.perf_cmd_of((self.tmp / "t.txt").read_text()))

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
        self.assertIn("head", doc)
        self.assertEqual(len(xt.perf_load(out_file)), 3)

    def test_sample_commit_ignores_git_env(self):
        d = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(d, ignore_errors=True))
        for args in (("init", "-q", "-b", "main"), ("config", "user.email", "t@t"), ("config", "user.name", "t")):
            git(d, *args)
        git(d, "config", "commit.gpgsign", "false")
        git(d, "commit", "-q", "--allow-empty", "-m", "i")
        head = subprocess.run(["git", "-C", str(d), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
        old_cwd = os.getcwd()
        self.addCleanup(os.chdir, old_cwd)
        os.chdir(d)
        with unittest.mock.patch.dict(os.environ, {"GIT_DIR": str(self.tmp)}):
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
        self.assertEqual(json.loads(Path(self.p("s.json")).read_text())["head"], head)

    def test_sample_errors(self):
        rc, _, err = run_main("perf", "sample", "--out", self.p("s.json"))
        self.assertEqual(rc, 2)
        self.assertIn("thiếu lệnh", err)
        rc, _, err = run_main(
            "perf", "sample", "--out", self.p("s.json"), "--runs", "1", "--warmup", "0", sys.executable, "-c", "exit(2)"
        )
        self.assertEqual(rc, 1)
        self.assertIn("thoát 2", err)

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
            self.assertIn("--base no-such-ref: không phân giải được thành commit", err)


class PerfGuardTextAttrTest(unittest.TestCase):
    """AUD-SEC-116/115 (T-3560): thuộc tính `-diff` không giấu được dòng thêm; `.gitattributes` đổi → ⚠; `--base` phân
    giải thành SHA trước khi tới `git diff` (không thành tuỳ chọn)."""

    def setUp(self):
        patcher = unittest.mock.patch.dict(os.environ, ISOLATED)
        patcher.start()
        self.addCleanup(patcher.stop)
        old_cwd = os.getcwd()
        self.addCleanup(os.chdir, old_cwd)
        self.fresh()

    def fresh(self) -> Path:
        """Repo mới (cwd chuyển vào): mỗi subtest một repo để luật/thuộc tính của ca trước không lọt sang ca sau."""
        self.d = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.d, True)
        git(self.d, "init", "-q", "-b", "main")
        for k, v in (("user.email", "t@t"), ("user.name", "t"), ("commit.gpgsign", "false")):
            git(self.d, "config", k, v)
        (self.d / "bench").mkdir()
        (self.d / "bench" / "run.py").write_text("print(1)\n")
        (self.d / "app.py").write_text("x = 1\n")
        git(self.d, "add", ".")
        git(self.d, "commit", "-qm", "init")
        os.chdir(self.d)
        return self.d

    def guard(self, *args: str) -> "tuple[int, str, str]":
        return run_main("perf", "guard", "--strict", *args)

    def test_guard_text_attr_binary_attr_cannot_hide_lines(self):
        def tree(d: Path) -> dict:  # luật đã commit ở --base: không ⚠ đổi luật, chỉ còn dòng lru_cache để bắt
            (d / ".gitattributes").write_text("app.py -diff\n")
            git(d, "add", ".gitattributes")
            git(d, "commit", "-qm", "attrs")
            return {}

        def config(d: Path) -> dict:
            attrs = d / ".git" / "attrs"  # ngoài cây: không phải file chưa theo dõi
            attrs.write_text("app.py -diff\n")
            return {
                "GIT_CONFIG_COUNT": "1",
                "GIT_CONFIG_KEY_0": "core.attributesFile",
                "GIT_CONFIG_VALUE_0": str(attrs),
            }

        def info(d: Path) -> dict:
            (d / ".git" / "info" / "attributes").write_text("app.py binary\n")
            return {}

        sources = {"tree": tree, "info": info, "config": config}
        for name, plant in sources.items():
            with self.subTest(name):
                d = self.fresh()  # repo riêng: `.gitattributes` của "tree" không được che hộ ca sau (F4)
                env = plant(d)
                (d / "app.py").write_text("import functools\n@functools.lru_cache\ndef f(): pass\n")
                with unittest.mock.patch.dict(os.environ, env):
                    rc, out, _ = self.guard("--base", "HEAD")
                self.assertEqual(rc, 1, out)
                self.assertIn("⚠", out)
                self.assertIn("lru_cache", out)
                self.assertNotIn(".gitattributes", out)

    def test_guard_text_attr_line_separators_cannot_hide_lines(self):
        """`git diff` đọc dạng bytes, tách theo `\\n`: `\\r` (universal newlines) và dấu ngắt dòng Unicode
        (`str.splitlines`) trong một dòng thật không cắt mất tiền tố `+` của phần sau (F2)."""
        for sep in ("\r", "\x0b", "\x0c", "\x1c", "\x1d", "\x1e", "\x85", "\u2028", "\u2029", "\r\n"):
            with self.subTest(repr(sep)):
                body = f'x = 1{sep}@__import__("functools").lru_cache{sep}def f(): pass\n'
                (self.d / "app.py").write_bytes(body.encode("utf-8"))
                rc, out, _ = self.guard("--base", "HEAD")
                self.assertEqual(rc, 1, out)
                self.assertIn("lru_cache", out)
                if sep != "\r\n":  # ca đối chứng `\r\n`: hai dòng thật; còn lại là MỘT dòng thật
                    self.assertIn("app.py: x = 1", out)
                git(self.d, "checkout", "-q", "--", "app.py")

    def test_guard_text_attr_fake_diff_header_in_content(self):
        """Tiêu đề `diff --git` chỉ nhận ở đầu dòng thật; nội dung giả tiêu đề (sau `\\r`) không đổi/xoá tên file
        hiện hành, nên dòng thêm sau đó vẫn được quét (F2)."""
        for fake in ("diff --git a/", "diff --git a/bench/run.py b/bench/run.py", 'diff --git "a/x" "b/x"'):
            with self.subTest(fake):
                (self.d / "app.py").write_bytes(f"x = 2\r{fake}\n@functools.lru_cache\ndef f(): pass\n".encode())
                rc, out, _ = self.guard("--base", "HEAD")
                self.assertEqual(rc, 1, out)
                self.assertIn("app.py: @functools.lru_cache", out)
                git(self.d, "checkout", "-q", "--", "app.py")
        added = xt._perf_diff_lines(
            b"diff --git a/a.py b/a.py\n--- a/a.py\n+++ b/a.py\n@@ -1 +1,2 @@\n-x\n+++ y\n+\xff\rz\n"
            b"+diff --git a/b b/b\n\\ No newline at end of file\n"
        )
        self.assertEqual(added, [("a.py", "++ y"), ("a.py", "\ufffd\rz"), ("a.py", "diff --git a/b b/b")])

    def test_guard_text_attr_plus_prefixed_line_is_not_header(self):
        """Dòng thêm bắt đầu bằng `++ ` (diff in `+++ …`) là nội dung, không phải tiêu đề `+++ b/…`: `++ 0 if setattr(…)`
        là Python hợp lệ."""
        (self.d / "app.py").write_text('import time\n++ 0 if setattr(time, "perf_counter", lambda: 0) else 0\n')
        rc, out, _ = self.guard("--base", "HEAD")
        self.assertEqual(rc, 1, out)
        self.assertIn("setattr(time", out)

    def test_guard_text_attr_content_attrs_warn(self):
        """Thuộc tính làm git đổi nội dung đọc từ worktree (`working-tree-encoding`, `filter` + clean, `ident`) che được
        dòng thêm kể cả với `--text`: guard báo ⚠ theo `git check-attr` (F1)."""
        warn = "thuộc tính đổi nội dung git đọc — dòng thêm có thể bị che"
        hide = {"GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "filter.hide.clean", "GIT_CONFIG_VALUE_0": "sed /lru_/d"}
        cases = {
            "app.py working-tree-encoding=IBM037": ({}, "working-tree-encoding=IBM037"),
            "app.py working-tree-encoding=UTF-16LE": ({}, "working-tree-encoding=UTF-16LE"),
            "*.py filter=hide": (hide, "filter=hide"),
            "app.py ident": ({}, "ident"),
        }
        for rule, (env, label) in cases.items():
            with self.subTest(rule):
                d = self.fresh()
                (d / ".git" / "info" / "attributes").write_text(rule + "\n")
                (d / "app.py").write_text("import functools\n@functools.lru_cache\ndef f(): pass\n")
                with unittest.mock.patch.dict(os.environ, env):
                    rc, out, _ = self.guard("--base", "HEAD")
                self.assertEqual(rc, 1, out)
                self.assertIn(f"— reviewer phải rà: app.py: {warn} ({label})", out)
                self.assertEqual(run_main("perf", "guard", "--base", "HEAD")[0], 0)  # không --strict: chỉ báo
        # clean filter khai qua GIT_CONFIG_* trỏ core.attributesFile ngoài cây (guard không chặn được env) vẫn bị thấy
        d = self.fresh()
        attrs = d / ".git" / "attrs"
        attrs.write_text("app.py filter=hide\n")
        env = {
            **hide,
            "GIT_CONFIG_COUNT": "2",
            "GIT_CONFIG_KEY_1": "core.attributesFile",
            "GIT_CONFIG_VALUE_1": str(attrs),
        }
        (d / "app.py").write_text("@functools.lru_cache\n")
        with unittest.mock.patch.dict(os.environ, env):
            rc, out, _ = self.guard("--base", "HEAD")
        self.assertEqual(rc, 1, out)
        self.assertIn(f"app.py: {warn} (filter=hide)", out)

    def test_guard_text_attr_content_attrs_harmless_values(self):
        """unset/unspecified không báo; file xoá, file chưa theo dõi cũng được hỏi thuộc tính."""
        rules = (
            "app.py -working-tree-encoding -filter -ident",
            "app.py !working-tree-encoding !filter",
        )
        for rule in rules:
            with self.subTest(rule):
                d = self.fresh()
                (d / ".git" / "info" / "attributes").write_text(rule + "\n")
                (d / "app.py").write_text("x = 2\n")
                rc, out, _ = self.guard("--base", "HEAD")
                self.assertEqual(rc, 0, out)
        d = self.fresh()
        (d / ".git" / "info" / "attributes").write_text("*.py ident\n")
        (d / "bench" / "run.py").unlink()
        (d / "new.py").write_text("y = 1\n")
        _rc, out, _ = self.guard("--base", "HEAD")
        self.assertIn("bench/run.py: thuộc tính", out)
        self.assertIn("new.py: thuộc tính", out)
        self.assertEqual(xt.perf_content_attrs(d, []), [])
        outside = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, outside, True)
        with unittest.mock.patch.dict(os.environ, {"GIT_CEILING_DIRECTORIES": str(outside.parent)}):
            with self.assertRaisesRegex(RuntimeError, "git check-attr lỗi"):
                xt.perf_content_attrs(outside, ["x"])  # ngoài repo git → guard exit 2

    def test_guard_text_attr_lfs_filter_warns(self):
        """`filter=lfs` không được miễn (G0): clean filter `lfs` đến từ config system/global (git-lfs cài sẵn) hoặc
        `GIT_CONFIG_*`, nên một dòng `info/attributes` là che được dòng thêm → ⚠, `--strict` exit 1."""
        lfs = {"GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "filter.lfs.clean", "GIT_CONFIG_VALUE_0": "sed /lru_/d"}
        (self.d / ".git" / "info" / "attributes").write_text("*.py filter=lfs\n")
        (self.d / "app.py").write_text("import functools\n@functools.lru_cache\ndef f(): pass\n")
        with unittest.mock.patch.dict(os.environ, lfs):
            rc, out, _ = self.guard("--base", "HEAD")
            loose = run_main("perf", "guard", "--base", "HEAD")[0]
        self.assertEqual(rc, 1, out)
        self.assertEqual(loose, 0)  # không --strict: chỉ báo
        self.assertIn("app.py: thuộc tính đổi nội dung git đọc — dòng thêm có thể bị che (filter=lfs)", out)
        self.assertNotIn("lru_cache", out)  # clean filter đã xoá dòng khỏi diff: chỉ còn ⚠ thuộc tính

    def test_guard_text_attr_binary_content_skipped(self):
        """NUL trong 8000 byte đầu của nội dung worktree (heuristic của git, không theo thuộc tính) → không khớp mẫu:
        `-O3` trong dữ liệu nhị phân không báo oan (G1). NUL sau 8000 byte → vẫn là văn bản, vẫn quét."""
        blob = b"\x00\x01" + b"CFLAGS = -O3\n" * 3
        (self.d / "app.py").write_bytes(blob)  # đã theo dõi, bị sửa
        (self.d / "data.bin").write_bytes(blob)  # chưa theo dõi
        rc, out, _ = self.guard("--base", "HEAD")
        self.assertEqual(rc, 0, out)
        late = b"x" * 8000 + b"\x00\nCFLAGS = -O3\n"
        for name in ("app.py", "data.bin"):
            with self.subTest(name):
                (self.d / "app.py").write_bytes(blob)
                (self.d / "data.bin").write_bytes(blob)
                (self.d / name).write_bytes(late)
                rc, out, _ = self.guard("--base", "HEAD")
                self.assertEqual(rc, 1, out)
                self.assertIn(f"{name}: CFLAGS = -O3", out)
                self.assertEqual(out.count("-O3"), 1, out)

    def test_guard_text_attr_binary_probe_sources(self):
        """Đọc ≤ 8000 byte: worktree; file không còn → blob ở base; symlink, tên giả PERF_ODD_NAME, không có ở đâu → văn bản
        (vẫn quét — fail-closed)."""
        d = self.d
        (d / "bin.dat").write_bytes(b"\x00" + b"y" * 20000)
        git(d, "add", "bin.dat")
        git(d, "commit", "-qm", "bin")
        sha = xt.perf_rev("HEAD")
        self.assertEqual(xt._perf_blob_head(d, f"{sha}:bin.dat"), b"\x00" + b"y" * 7999)
        self.assertTrue(xt._perf_binary(d, sha, "bin.dat"))  # worktree
        (d / "bin.dat").unlink()
        self.assertTrue(xt._perf_binary(d, sha, "bin.dat"))  # đã xoá → blob base
        (d / "app.py").unlink()
        self.assertFalse(xt._perf_binary(d, sha, "app.py"))
        self.assertFalse(xt._perf_binary(d, sha, "nope.py"))  # không ở worktree lẫn base
        (d / xt.PERF_ODD_NAME).write_bytes(b"\x00")  # file thật trùng tên giả không che được dòng của tên bị quote
        self.assertFalse(xt._perf_binary(d, sha, xt.PERF_ODD_NAME))
        (d / "link").symlink_to(xt.PERF_ODD_NAME)
        self.assertFalse(xt._perf_binary(d, sha, "link"))

    def test_guard_text_attr_snippet_around_match(self):
        """Đoạn trích trong ⚠ lấy quanh chỗ khớp — dòng 130 `#` rồi mới tới `lru_cache` vẫn in chỗ khớp — và escape ký
        tự không in được: `\\r`, ESC không ra terminal thô (G4)."""
        (self.d / "app.py").write_text("#" * 130 + " lru_cache\nx = 1\r@lru_cache\x1b[2K\u202e\n")
        rc, out, _ = self.guard("--base", "HEAD")
        self.assertEqual(rc, 1, out)
        self.assertIn("app.py: …" + "#" * 59 + " lru_cache", out)
        self.assertIn("app.py: x = 1\\r@lru_cache\\x1b[2K\\u202e", out)
        for raw in ("\r", "\x1b", "\u202e"):
            self.assertNotIn(raw, out)

    def test_guard_text_attr_diff_raw_git_errors(self):
        with self.assertRaisesRegex(RuntimeError, "git diff lỗi"):
            xt._perf_git_raw(self.d, "diff", "no-such-ref", "--")
        timeout = subprocess.TimeoutExpired(["git"], 1)
        with unittest.mock.patch.object(xt.subprocess, "run", side_effect=timeout):
            with self.assertRaisesRegex(RuntimeError, "git diff quá"):
                xt._perf_git_raw(self.d, "diff")

    def test_guard_text_attr_o3_word_boundary(self):
        """`-O3` chỉ tính khi là cờ đứng riêng (F3): dữ liệu nhị phân/chuỗi dài chứa `-O3` không báo oan."""
        for hit in ("CFLAGS = -O3", "gcc -O3 x.c", "opts=['-O3']", '"-O3"', "-O3"):
            self.assertTrue(xt.PERF_SUSPECT_RE.search(hit), hit)
        for miss in ("x-O3", "a_-O3", "--O3", "-O30", "-O3x", "ab-O3_", "\x00\x01QZ-O3a"):
            self.assertFalse(xt.PERF_SUSPECT_RE.search(miss), miss)

    def test_guard_text_attr_rule_file_change_warns(self):
        warn = "đổi luật thuộc tính — có thể giấu dòng"
        (self.d / ".gitattributes").write_text("*.py text\n")  # mới, chưa theo dõi
        rc, out, _ = self.guard("--base", "HEAD")
        self.assertEqual(rc, 1)
        self.assertIn(f".gitattributes: {warn}", out)
        git(self.d, "add", ".gitattributes")
        git(self.d, "commit", "-qm", "attrs")
        self.assertEqual(self.guard("--base", "HEAD")[0], 0)  # đã commit ở --base: không còn là đổi luật
        (self.d / ".gitattributes").write_text("*.py -diff\n")  # đã theo dõi, bị sửa
        rc, out, _ = self.guard("--base", "HEAD")
        self.assertEqual(rc, 1)
        self.assertIn(f".gitattributes: {warn}", out)
        git(self.d, "checkout", "-q", "--", ".gitattributes")
        # tự ẩn: `.gitignore` đã commit che tên `.gitattributes` ở thư mục con — vẫn bị thấy
        (self.d / ".gitignore").write_text(".gitattributes\n.venv/\n")
        git(self.d, "add", ".gitignore")
        git(self.d, "commit", "-qm", "ignore")
        (self.d / "bench" / ".gitattributes").write_text("run.py -diff\n")
        rc, out, _ = self.guard("--base", "HEAD", "--locked", "bench/*")
        self.assertEqual(rc, 1)
        self.assertIn("✗ đụng file khoá (bộ đo/test tương đương): bench/.gitattributes", out)
        self.assertIn(f"bench/.gitattributes: {warn}", out)
        (self.d / "bench" / ".gitattributes").unlink()
        # trong thư mục đã ignore bởi `.gitignore` đã theo dõi (gói trong `.venv/`): không phải luật mới
        (self.d / ".venv").mkdir()
        (self.d / ".venv" / ".gitattributes").write_text("* -diff\n")
        rc, out, _ = self.guard("--base", "HEAD")
        self.assertEqual(rc, 0, out)
        self.assertEqual(xt._perf_self_hidden_rules(self.d), [])

    def test_guard_text_attr_base_is_not_an_option(self):
        target = self.d.parent / (self.d.name + ".out")
        self.addCleanup(lambda: target.unlink(missing_ok=True))
        for bad in (f"--output={target}", "-p", "HEAD^{tree}", "no-such-ref"):
            with self.subTest(bad):
                rc, out, err = self.guard(f"--base={bad}")
                self.assertEqual((rc, out), (2, ""))
                self.assertIn(f"--base {bad}: không phân giải được thành commit", err)
                self.assertFalse(target.exists())

    def test_guard_text_attr_valid_bases_still_work(self):
        head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
        git(self.d, "update-ref", "refs/remotes/origin/main", head)
        (self.d / "bench" / "run.py").write_text("print(2)\n")
        for base in ("HEAD", "main", head, head[:7], "origin/main"):
            with self.subTest(base):
                self.assertEqual(self.guard("--base", base)[0], 0)
                rc, out, _ = self.guard("--base", base, "--locked", "bench/*")
                self.assertEqual(rc, 1)
                self.assertIn("✗ đụng file khoá (bộ đo/test tương đương): bench/run.py", out)


class PerfSampleV2Test(unittest.TestCase):
    """Mẫu perf v2 (ADR-0052 §4, T-3544): head/dirty/tree_fp đo trước lần chạy đầu, harness_sha256, git lỗi → exit 2."""

    def setUp(self):
        patcher = unittest.mock.patch.dict(os.environ, ISOLATED)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(self.tmp, ignore_errors=True))
        self.repo = self.tmp / "repo"
        self.repo.mkdir()
        old_cwd = os.getcwd()
        self.addCleanup(os.chdir, old_cwd)
        os.chdir(self.repo)

    def init_repo(self, commit: bool = True) -> None:
        for args in (("init", "-q", "-b", "main"), ("config", "user.email", "t@t"), ("config", "user.name", "t")):
            git(self.repo, *args)
        git(self.repo, "config", "commit.gpgsign", "false")
        (self.repo / "bench").mkdir()
        (self.repo / "bench" / "run.py").write_text("print(1)\n")
        (self.repo / "app.py").write_text("x = 1\n")
        if commit:
            git(self.repo, "add", ".")
            git(self.repo, "commit", "-qm", "init")

    def sample(
        self, *extra: str, out: Path | None = None, code: str = "pass", keep: bool = False
    ) -> tuple[int, str, dict]:
        """`perf sample` một lần đo; trả (exit, stderr, mẫu — {} khi không ghi file). `keep`: giữ file `--out` cũ."""
        dest = out or self.tmp / "s.json"
        if not keep:
            dest.unlink(missing_ok=True)
        argv = (
            "perf",
            "sample",
            "--out",
            dest,
            "--runs",
            "1",
            "--warmup",
            "0",
            *extra,
            "--",
            sys.executable,
            "-c",
            code,
        )
        rc, _, err = run_main(*argv)
        return rc, err, json.loads(dest.read_text()) if dest.exists() else {}

    def test_sample_v2_fields_clean_repo(self):
        self.init_repo()
        rc, err, doc = self.sample("--harness", "bench/*")
        self.assertEqual(rc, 0, err)
        head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
        self.assertEqual((doc["schema"], doc["unit"], doc["runs"], doc["warmup"]), (2, "s", 1, 0))
        self.assertEqual((doc["head"], doc["dirty"], doc["higher_is_better"]), (head, False, False))
        self.assertEqual(doc["cmd"], [sys.executable, "-c", "pass"])
        nproc = len(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else os.cpu_count()
        self.assertEqual(doc["env"], {"platform": sys.platform, "python": sys.version.split()[0], "nproc": nproc})
        self.assertEqual(doc["tree_fp"], xt.tree_fingerprint(self.repo))  # cùng vân tay với `loop verify`
        self.assertRegex(doc["harness_sha256"], r"^[0-9a-f]{64}$")
        self.assertNotIn("unverified-manual", doc)
        self.assertNotIn("commit", doc)
        self.assertEqual(len(xt.perf_load(str(self.tmp / "s.json"))), 1)
        self.assertEqual(xt.perf_cmd_of((self.tmp / "s.json").read_text()), doc["cmd"])
        self.assertNotIn("⚠", err)

    def test_sample_v2_nproc_uses_affinity(self):
        with unittest.mock.patch.object(xt.os, "sched_getaffinity", lambda _pid: {0, 1}, create=True):
            self.assertEqual(xt.perf_nproc(), 2)  # lõi được phép chạy (taskset/cgroup), không phải lõi của máy
        with unittest.mock.patch.object(xt.os, "sched_getaffinity", None, create=True):
            self.assertEqual(xt.perf_nproc(), os.cpu_count())

    def test_sample_v2_from_subdirectory(self):
        self.init_repo()
        _, _, ref = self.sample()
        os.chdir(self.repo / "bench")
        rc, err, doc = self.sample("--harness", "app.py", out=Path("s.json"))  # --out tương đối, trong cây con
        self.assertEqual(rc, 0, err)
        self.assertEqual((doc["head"], doc["dirty"], doc["tree_fp"]), (ref["head"], False, ref["tree_fp"]))
        self.assertTrue((self.repo / "bench" / "s.json").is_file())

    def test_sample_v2_git_config_cannot_hide_changes(self):
        self.init_repo()
        (self.repo / ".gitattributes").write_text("app.py diff=same\n")
        git(self.repo, "add", ".gitattributes")
        git(self.repo, "commit", "-qm", "attrs")
        git(self.repo, "config", "diff.same.textconv", "sh -c 'echo same' --")
        _, _, clean = self.sample()
        self.assertFalse(clean["dirty"])

        cases = {
            "ext-diff": ({"GIT_EXTERNAL_DIFF": "true"}, lambda: (self.repo / "app.py").write_text("x = 2\n")),
            "textconv": ({}, lambda: (self.repo / "app.py").write_text("x = 3\n")),
        }
        for name, (env, change) in cases.items():
            with self.subTest(name):
                git(self.repo, "checkout", "-q", "--", "app.py")
                change()
                with unittest.mock.patch.dict(os.environ, env):
                    _, err, doc = self.sample()
                    self.assertEqual(doc["tree_fp"], xt.tree_fingerprint(self.repo))
                self.assertTrue(doc["dirty"], err)
                self.assertNotEqual(doc["tree_fp"], clean["tree_fp"])

    def test_sample_v2_higher_is_better(self):
        self.init_repo()
        self.assertTrue(self.sample("--higher-is-better")[2]["higher_is_better"])

    def test_sample_v2_out_in_tree_and_autopilot_not_dirty(self):
        self.init_repo()
        _, _, ref = self.sample()
        (self.repo / ".autopilot").mkdir()
        (self.repo / ".autopilot" / "state.json").write_text("{}")
        (self.repo / "out").mkdir()
        dest = self.repo / "out" / "a*b.json"  # tên có ký tự glob: loại đúng file, không loại theo mẫu
        dest.write_text("cũ")  # mẫu cũ còn nằm trong cây
        rc, err, doc = self.sample(out=dest, keep=True)
        self.assertEqual(rc, 0, err)
        self.assertEqual((doc["dirty"], doc["tree_fp"]), (False, ref["tree_fp"]))
        old_cwd = os.getcwd()
        self.addCleanup(os.chdir, old_cwd)
        os.chdir(dest.parent)  # chạy lại từ thư mục con, `--out` tương đối, mẫu lần trước còn đó
        rc, err, doc = self.sample(out=Path(dest.name), keep=True)
        self.assertEqual((rc, doc["dirty"], doc["tree_fp"]), (0, False, ref["tree_fp"]), err)
        os.chdir(old_cwd)
        (self.repo / "out" / "aXb.json").write_text("khác")  # file khác khớp nếu coi tên là glob
        self.assertTrue(self.sample(out=dest)[2]["dirty"])

    def test_sample_v2_tree_measured_before_first_run(self):
        self.init_repo()
        _, _, ref = self.sample()
        make = "open('made.txt', 'w').write('x')"  # lệnh đo tạo file trong cây (lần warmup đầu tiên)
        rc, err, doc = self.sample("--warmup", "1", code=make)
        self.assertEqual(rc, 0, err)
        self.assertEqual((doc["dirty"], doc["tree_fp"]), (False, ref["tree_fp"]))
        _, _, after = self.sample()
        self.assertTrue(after["dirty"])
        self.assertNotEqual(after["tree_fp"], ref["tree_fp"])
        (self.repo / "made.txt").unlink()
        (self.repo / "app.py").write_text("x = 2\n")  # thay đổi file đã track cũng là bẩn
        self.assertTrue(self.sample()[2]["dirty"])

    def test_sample_v2_untracked_non_file_is_dirty(self):
        self.init_repo()
        (self.repo / "dangling").symlink_to(self.tmp / "missing")  # git sẽ commit symlink này dù đích không có
        self.assertTrue(self.sample()[2]["dirty"])

    def test_sample_v2_outside_repo_labels_unverified(self):
        with unittest.mock.patch.dict(os.environ, {"GIT_CEILING_DIRECTORIES": str(self.tmp)}):
            rc, err, doc = self.sample()
            self.assertEqual(rc, 0, err)
            self.assertEqual((doc["head"], doc["unverified-manual"]), ("", True))
            self.assertIsNone(doc["dirty"])
            self.assertIsNone(doc["tree_fp"])
            rc, err, doc = self.sample("--harness", "*")
        self.assertEqual((rc, doc), (2, {}))
        self.assertIn("--harness cần repo git", err)

    def test_sample_v2_git_missing_exit_2(self):
        self.init_repo()
        with unittest.mock.patch.dict(os.environ, {"PATH": str(self.tmp)}):
            rc, err, doc = self.sample()
        self.assertEqual((rc, doc), (2, {}))
        self.assertIn("không chạy được git", err)

    def test_sample_v2_dubious_ownership_exit_2(self):
        self.init_repo()
        with unittest.mock.patch.dict(os.environ, {"GIT_TEST_ASSUME_DIFFERENT_OWNER": "1"}):
            rc, err, doc = self.sample()
        self.assertEqual((rc, doc), (2, {}))
        self.assertIn("dubious ownership", err)

    def test_sample_v2_unborn_head_exit_2(self):
        self.init_repo(commit=False)
        rc, err, doc = self.sample()
        self.assertEqual((rc, doc), (2, {}))
        self.assertIn("HEAD chưa có commit", err)

    def test_sample_v2_tree_git_error_exit_2(self):
        self.init_repo()
        real = xt._git

        def broken(cwd: Path, *args: str, env: object = None, stdin: object = None) -> subprocess.CompletedProcess:
            if args[:1] == ("ls-files",):
                return subprocess.CompletedProcess([], 128, "", "fatal: index file corrupt")
            return real(cwd, *args, env=env, stdin=stdin)

        with unittest.mock.patch.object(xt, "_git", side_effect=broken):
            rc, err, doc = self.sample()
        self.assertEqual((rc, doc), (2, {}))
        self.assertIn("index file corrupt", err)

    def test_sample_v2_harness_hash(self):
        self.init_repo()
        _, err, bare = self.sample()
        self.assertIn("⚠ không có --harness", err)
        _, _, h1 = self.sample("--harness", "bench/*", "--harness", "app.py")
        self.assertNotEqual(h1["harness_sha256"], bare["harness_sha256"])
        _, _, other_cmd = self.sample("--harness", "bench/*", "--harness", "app.py", code="pass  # khác")
        self.assertNotEqual(other_cmd["harness_sha256"], h1["harness_sha256"])
        clone = self.tmp / "clone"  # cùng nội dung ở thư mục khác (worktree gốc vs cây agent): cùng hash
        subprocess.run(["git", "clone", "-q", str(self.repo), str(clone)], check=True, env={**os.environ, **ISOLATED})
        os.chdir(clone)
        self.assertEqual(
            self.sample("--harness", "app.py", "--harness", "bench/*")[2]["harness_sha256"], h1["harness_sha256"]
        )
        (clone / "bench" / "run.py").write_text("print(2)\n")
        self.assertNotEqual(
            self.sample("--harness", "bench/*", "--harness", "app.py")[2]["harness_sha256"], h1["harness_sha256"]
        )

    def test_sample_v2_harness_symlink_fifo_missing(self):
        self.init_repo()
        target = self.tmp / "outside.txt"
        target.write_text("a")
        (self.repo / "bench" / "link").symlink_to(target)  # băm chuỗi đích như git, không đi theo symlink
        h1 = self.sample("--harness", "bench/*")[2]["harness_sha256"]
        target.write_text("b")
        self.assertEqual(self.sample("--harness", "bench/*")[2]["harness_sha256"], h1)
        (self.repo / "bench" / "link").unlink()
        (self.repo / "bench" / "link").symlink_to(self.tmp / "other.txt")
        self.assertNotEqual(self.sample("--harness", "bench/*")[2]["harness_sha256"], h1)
        (self.repo / "bench" / "run.py").unlink()  # file đã track bị xoá: không băm được → không ghi mẫu
        rc, err, doc = self.sample("--harness", "bench/*")
        self.assertEqual((rc, doc), (2, {}))
        self.assertIn("✗ không ghi mẫu: --harness không đọc được bench/run.py", err)
        os.mkfifo(
            self.repo / "bench" / "run.py"
        )  # FIFO: không mở (không treo) — git diff đã chặn ở CLI, kiểm hàm trực tiếp
        with self.assertRaisesRegex(RuntimeError, "không phải file thường hay symlink: bench/run.py"):
            xt._perf_harness_digest(self.repo, "bench/run.py")
        git(self.repo, "checkout", "-q", "--", "bench/run.py")

    def test_sample_v2_harness_gitlink_exit_2(self):
        self.init_repo()
        sub = self.repo / "bench" / "sub"  # gitlink (thư mục) khớp `bench/*`: không băm được như file → không ghi mẫu
        sub.mkdir()
        for args in (("init", "-q", "-b", "main"), ("config", "user.email", "t@t"), ("config", "user.name", "t")):
            git(sub, *args)
        (sub / "f").write_text("1\n")
        git(sub, "add", "f")
        git(sub, "commit", "-qm", "a")
        git(self.repo, "add", "bench/sub")
        git(self.repo, "commit", "-qm", "gitlink")
        rc, err, doc = self.sample("--harness", "bench/*")
        self.assertEqual((rc, doc), (2, {}))
        self.assertIn("✗ không ghi mẫu: --harness khớp thứ không phải file thường hay symlink: bench/sub", err)

    def test_sample_v2_harness_rejects_out_and_skips_autopilot(self):
        self.init_repo()
        rc, err, doc = self.sample("--harness", "bench/*", out=self.repo / "bench" / "s.json")
        self.assertEqual((rc, doc), (2, {}))
        self.assertIn("--out bench/s.json nằm trong --harness", err)
        (self.repo / ".autopilot").mkdir()
        (self.repo / ".autopilot" / "state.json").write_text("{}")
        h1 = self.sample("--harness", "*")[2]["harness_sha256"]
        (self.repo / ".autopilot" / "state.json").write_text('{"rev": 1}')
        self.assertEqual(self.sample("--harness", "*")[2]["harness_sha256"], h1)
        rc, err, _ = self.sample("--harness", ".autopilot/*")
        self.assertEqual(rc, 2)
        self.assertIn("không khớp file nào", err)

    def test_sample_v2_harness_dead_glob_exit_2(self):
        self.init_repo()
        rc, err, doc = self.sample("--harness", "bench/*", "--harness", "bech/*")
        self.assertEqual((rc, doc), (2, {}))
        self.assertIn("--harness không khớp file nào trong repo: bech/*", err)


REFUSE = "không đủ điều kiện so"
V2 = {
    "schema": 2,
    "cmd": ["./bench/run.sh"],
    "unit": "s",
    "higher_is_better": False,
    "env": {"platform": "linux", "python": "3.12.1", "nproc": 4},
    "head": "a" * 40,
    "dirty": False,
    "tree_fp": "f" * 64,
    "harness_sha256": "1" * 64,
}


class PerfCompareV2Test(unittest.TestCase):
    """`perf compare` với mẫu v2 (ADR-0052 §4, T-3545): lệch trường trọng yếu, baseline bẩn, `--base` lệch → exit 2;
    v1/mảng thô/mẫu đo ngoài repo → so như cũ, nhãn `unverified-manual`."""

    def setUp(self):
        patcher = unittest.mock.patch.dict(os.environ, ISOLATED)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(self.tmp, ignore_errors=True))
        old_cwd = os.getcwd()
        self.addCleanup(os.chdir, old_cwd)
        os.chdir(self.tmp)

    def put(self, name: str, data: object) -> str:
        (self.tmp / name).write_text(json.dumps(data))
        return str(self.tmp / name)

    def pair(self, b_over: dict | None = None, a_over: dict | None = None) -> tuple[str, str]:
        b = self.put("b.json", {**V2, **(b_over or {}), "samples": SLOW})
        return b, self.put("a.json", {**V2, **(a_over or {}), "samples": FAST})

    def compare(self, before: str, after: str, *extra: str) -> tuple[int, dict, str]:
        rc, out, err = run_main("perf", "compare", before, after, "--json", *extra)
        return rc, json.loads(out) if out else {}, err

    def test_v2_same_meta_compares_without_label(self):
        rc, doc, err = self.compare(*self.pair({}, {"dirty": True, "head": "b" * 40, "tree_fp": "e" * 64}))
        self.assertEqual((rc, doc["verdict"]), (0, "improved"), err)  # after bẩn/head khác: không xét (candidate)
        self.assertNotIn("unverified-manual", doc)
        self.assertEqual(err, "")

    def test_v2_refuses_each_key_mismatch(self):
        env2 = {**V2["env"], "platform": "darwin"}
        for key, val in (
            ("unit", "ms"),
            ("cmd", ["./bench/other.sh"]),
            ("harness_sha256", "2" * 64),
            ("env.platform", env2),
        ):
            with self.subTest(key):
                rc, doc, err = self.compare(*self.pair({}, {key.partition(".")[0]: val}))
                self.assertEqual((rc, doc), (2, {}))
                self.assertIn(REFUSE, err)
                self.assertIn(key, err)

    def test_v2_higher_is_better_sample_vs_flag(self):
        rc, _, err = self.compare(*self.pair({}, {"higher_is_better": True}), "--higher-is-better")
        self.assertEqual(rc, 2)  # hai mẫu lệch nhau: cờ không gỡ được
        self.assertIn("higher_is_better", err)
        both = {"higher_is_better": True}
        rc, _, err = self.compare(*self.pair(both, both))
        self.assertEqual(rc, 2)  # mẫu nói cao là tốt, cờ vắng → chặt: từ chối, không đoán chiều
        self.assertIn("--higher-is-better", err)
        rc, doc, _ = self.compare(*self.pair(both, both), "--higher-is-better")
        self.assertEqual((rc, doc["verdict"]), (1, "regressed"))
        rc, _, err = self.compare(*self.pair(), "--higher-is-better")
        self.assertEqual(rc, 2)
        self.assertIn(REFUSE, err)

    def test_v2_python_nproc_only_warn(self):
        env2 = {"platform": "linux", "python": "3.13.0", "nproc": 8}
        rc, doc, err = self.compare(*self.pair({}, {"env": env2}))
        self.assertEqual((rc, doc["verdict"]), (0, "improved"))
        self.assertIn("⚠ lệch env.python: '3.12.1' ≠ '3.13.0'", err)
        self.assertIn("⚠ lệch env.nproc: 4 ≠ 8", err)

    def test_v2_dirty_baseline_refused(self):
        rc, _, err = self.compare(*self.pair({"dirty": True}))
        self.assertEqual(rc, 2)
        self.assertIn(REFUSE, err)
        self.assertIn("bẩn", err)

    def test_v2_manual_sample_labelled_and_base_refused(self):
        manual = {"head": "", "dirty": None, "tree_fp": None, "unverified-manual": True}
        for b_over, a_over in ((manual, {}), ({}, manual)):
            with self.subTest(before=bool(b_over)):
                rc, doc, _ = self.compare(*self.pair(b_over, a_over))
                self.assertEqual((rc, doc["unverified-manual"]), (0, True))  # null không phải "sạch"
        git(self.tmp, "init", "-q", "-b", "main")
        git(self.tmp, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--allow-empty", "-m", "x")
        rc, _, err = self.compare(*self.pair(manual), "--base", "HEAD")
        self.assertEqual(rc, 2)  # head rỗng ≠ base
        self.assertIn("before.head '' ≠ --base", err)

    def test_v1_and_mixed_labelled_unverified(self):
        slow, fast = self.put("slow.json", SLOW), self.put("fast.json", FAST)
        b2, a2 = self.pair()
        for before, after in ((slow, fast), (b2, fast), (slow, a2)):
            with self.subTest(before=before, after=after):
                rc, doc, err = self.compare(before, after)
                self.assertEqual((rc, doc["verdict"], doc["unverified-manual"]), (0, "improved", True), err)
        (self.tmp / "one.txt").write_text("1000 1001")  # số thô, không phải JSON
        (self.tmp / "two.txt").write_text("900 901")
        rc, doc, _ = self.compare(str(self.tmp / "one.txt"), str(self.tmp / "two.txt"), "--exact")
        self.assertEqual((rc, doc["unverified-manual"]), (0, True))
        rc, out, _ = run_main("perf", "compare", slow, fast)
        self.assertIn("[unverified-manual]", out)
        rc, out, _ = run_main("perf", "compare", b2, a2)
        self.assertNotIn("unverified-manual", out)
        v1cmd = self.put("v1cmd.json", {"samples": FAST, "cmd": ["./bench/other.sh"]})
        rc, _, err = self.compare(b2, v1cmd)
        self.assertEqual(rc, 2)  # một bên v1: `cmd` lệch vẫn chặn như trước
        self.assertIn("hai lệnh khác nhau", err)

    def test_v2_bad_schema_or_fields_exit_2(self):
        for name, data, msg in (
            ("s3", {**V2, "schema": 3}, "schema 3 không hỗ trợ"),
            ("sstr", {**V2, "schema": "2"}, "schema '2' không hỗ trợ"),
            ("sbool", {**V2, "schema": True}, "schema True không hỗ trợ"),
            ("noharness", {k: v for k, v in V2.items() if k != "harness_sha256"}, "harness_sha256"),
            ("nodirty", {k: v for k, v in V2.items() if k != "dirty"}, "dirty"),
            ("dirtystr", {**V2, "dirty": "no"}, "dirty"),
            ("cmdstr", {**V2, "cmd": "make bench"}, "cmd"),
            ("envlist", {**V2, "env": []}, "env"),
            ("noplatform", {**V2, "env": {"python": "3.12"}}, "env.platform"),
        ):
            with self.subTest(name):
                bad = self.put(f"{name}.json", {**data, "samples": SLOW})
                for before, after in ((bad, self.pair()[1]), (self.pair()[0], bad)):
                    rc, doc, err = self.compare(before, after)
                    self.assertEqual((rc, doc), (2, {}))
                    self.assertIn(msg, err)

    def test_base_mismatch_and_resolution(self):
        git(self.tmp, "init", "-q", "-b", "main")
        for msg in ("one", "two"):
            git(self.tmp, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--allow-empty", "-m", msg)
        head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
        rc, doc, err = self.compare(*self.pair({"head": head}), "--base", "main")
        self.assertEqual((rc, doc["verdict"]), (0, "improved"), err)
        rc, _, err = self.compare(*self.pair({"head": head}), "--base", "HEAD~1")
        self.assertEqual(rc, 2)
        self.assertIn(f"before.head '{head}' ≠ --base HEAD~1", err)
        for ref in ("nope", "--help", "HEAD~9"):
            with self.subTest(ref):
                rc, _, err = self.compare(*self.pair({"head": head}), f"--base={ref}")
                self.assertEqual(rc, 2)
                self.assertIn(f"--base {ref}: không phân giải được thành commit", err)
        slow = self.put("slow.json", SLOW)
        rc, _, err = self.compare(slow, self.pair()[1], "--base", "main")
        self.assertEqual(rc, 2)  # v1 không có head: không chứng minh được baseline là --base
        self.assertIn("before.head None ≠ --base main", err)

    def test_v2_strict_against_raw_array(self):
        """Hai lựa chọn chặt khi bên kia là mảng thô (v1): bên v2 vẫn bị xét — baseline bẩn, chiều tốt lệch cờ → exit 2."""
        raw = self.put("raw.json", FAST)
        for name, over, msg in (
            ("dirty", {"dirty": True}, "before.dirty"),
            ("hib", {"higher_is_better": True}, "--higher"),
        ):
            with self.subTest(name):
                before = self.put(f"b-{name}.json", {**V2, **over, "samples": SLOW})
                rc, doc, err = self.compare(before, raw)
                self.assertEqual((rc, doc), (2, {}))
                self.assertIn(REFUSE, err)
                self.assertIn(msg, err)

    def test_compare_reads_pipe_once(self):
        """`perf compare <(cat b.json) a.json`: ống chỉ đọc được một lần — mẫu v2 qua ống vẫn là v2 (luật từ chối áp,
        không nhãn `unverified-manual`), cả bên trước lẫn bên sau."""

        def via_pipe(data: dict) -> str:
            r, w = os.pipe()
            self.addCleanup(os.close, r)
            os.write(w, json.dumps(data).encode())
            os.close(w)
            return f"/dev/fd/{r}"

        bad = {**V2, "dirty": True, "harness_sha256": "2" * 64, "samples": SLOW}
        rc, _, err = self.compare(via_pipe(bad), self.pair()[1])
        self.assertEqual(rc, 2)
        self.assertIn("before.dirty", err)
        self.assertIn("lệch harness_sha256", err)
        rc, _, err = self.compare(self.pair()[0], via_pipe({**V2, "harness_sha256": "2" * 64, "samples": FAST}))
        self.assertEqual(rc, 2)
        self.assertIn("lệch harness_sha256", err)
        rc, doc, err = self.compare(via_pipe({**V2, "samples": SLOW}), via_pipe({**V2, "samples": FAST}))
        self.assertEqual((rc, doc["verdict"]), (0, "improved"), err)
        self.assertNotIn("unverified-manual", doc)

    def test_base_outside_repo_exit_2(self):
        with unittest.mock.patch.dict(os.environ, {"GIT_CEILING_DIRECTORIES": str(self.tmp)}):
            rc, _, err = self.compare(*self.pair(), "--base", "HEAD")
        self.assertEqual(rc, 2)
        self.assertIn("--base HEAD: không phân giải được thành commit", err)

    def test_gate_example_runs_unchanged(self):
        """Gate mẫu của optimization-loop.md: baseline `perf sample` ở worktree commit gốc (out ghi ra cây agent), candidate
        ở cây agent chưa commit (bẩn) → so được, không nhãn `unverified-manual`; `--base` là ref gốc khớp `before.head`."""
        repo, wt = self.tmp / "repo", self.tmp / "wt"
        repo.mkdir()
        git(repo, "init", "-q", "-b", "main")
        (repo / "bench").mkdir()
        (repo / "bench" / "run.py").write_text("pass\n")
        git(repo, "add", ".")
        git(repo, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "init")
        git(repo, "worktree", "add", "-q", "--detach", str(wt), "main")
        (repo / "app.py").write_text("x = 2\n")  # thay đổi của agent, chưa commit
        cmd = ("--runs", "3", "--warmup", "0", "--harness", "bench/*", "--", sys.executable, "bench/run.py")
        os.chdir(wt)
        self.assertEqual(run_main("perf", "sample", "--out", str(repo / "before.json"), *cmd)[0], 0)
        os.chdir(repo)
        self.assertEqual(run_main("perf", "sample", "--out", "after.json", *cmd)[0], 0)
        rc, doc, err = self.compare("before.json", "after.json", "--base", "main", "--min-runs", "3")
        self.assertIn(rc, (0, 1), err)
        self.assertNotIn("unverified-manual", doc)
        self.assertTrue(json.loads((repo / "after.json").read_text())["dirty"])


if __name__ == "__main__":
    unittest.main()


class CpuBudgetTest(unittest.TestCase):
    """AUD-TEST-008: test độ phức tạp so tỉ lệ đo cùng tiến trình (`tests/cpu_budget.py`), không ngưỡng giây cứng."""

    def fake_clock(self, seconds_for: object) -> tuple:
        now = [0.0]

        def clock() -> float:
            return now[0]

        def work(n: int) -> None:
            now[0] += seconds_for(n)  # type: ignore[operator]  # đồng hồ giả: list một phần tử

        return clock, work

    def test_linear_passes_quadratic_fails(self):
        for name, per_n, ok in (
            ("tuyến tính", lambda n: n * 1e-5, True),  # 0,1 s → 0,4 s
            ("tuyến tính rất nhanh", lambda n: n * 1e-9, True),  # dưới sàn: không đỏ vì nhiễu
            ("bậc hai", lambda n: n * n * 1e-8, False),  # 1 s → 16 s
            ("bậc hai vừa đủ nhạy", lambda n: n * n * 9e-10, False),  # 0,09 s → 1,44 s
        ):
            with self.subTest(name):
                clock, work = self.fake_clock(per_n)
                if ok:
                    cpu_budget.assert_not_quadratic(self, work, 10_000, clock=clock)
                else:
                    with self.assertRaises(AssertionError) as cm:
                        cpu_budget.assert_not_quadratic(self, work, 10_000, clock=clock)
                    self.assertIn("bậc hai?", str(cm.exception))
        clock, work = self.fake_clock(lambda n: n * n * 1e-8)  # canh hàm mũ: cho phép bậc hai (16 lần)…
        cpu_budget.assert_not_quadratic(self, work, 10_000, clock=clock, ratio=40)
        clock, work = self.fake_clock(lambda n: 2.0 ** (n / 1000) * 1e-3)  # …nhưng hàm mũ vẫn đỏ
        with self.assertRaises(AssertionError):
            cpu_budget.assert_not_quadratic(self, work, 10_000, clock=clock, ratio=40)
        self.assertGreaterEqual(cpu_budget.cost(lambda n: sum(range(n)), 10), 0.0)  # đồng hồ thật

    def test_no_hard_cpu_thresholds_left(self):
        hard = re.compile(r"assertLess\(\s*time\.process_time\(\)\s*-\s*\w+\s*,\s*[0-9.]+\s*\)")
        found = [
            f"{p.name}:{i}"
            for p in sorted((ROOT / "tests").glob("test*.py"))
            for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1)
            if hard.search(line)
        ]
        self.assertEqual(found, [], "ngưỡng CPU cứng — dùng cpu_budget.assert_not_quadratic")
