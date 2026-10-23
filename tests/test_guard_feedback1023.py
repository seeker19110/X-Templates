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
            (f"find {R} -name '*.pyc' -delete", None),
            (f"find {R} -name '*.pyc' -exec rm -f {{}} +", None),
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

    def test_guard_wipe_project_root_find_type(self):
        """Review 5ef1a14 M1: `-type` (như độ sâu, `-xdev`) không phải bộ lọc tên — vẫn xoá cả cây."""
        for cmd in (f"find {R} -type f -delete", "find . -type f -delete", "find . -xdev -type d -maxdepth 1 -delete"):
            with self.subTest(cmd=cmd):
                self.assertEqual(policy(cmd)["decision"], "deny")
        for cmd in ("find . -name '*.pyc' -delete", "find . -type f -name '*.pyc' -delete"):
            with self.subTest(cmd=cmd):
                self.assertEqual(policy(cmd)["decision"], "", cmd)

    def test_guard_wipe_project_root_find_broad_test(self):
        """Review bb606aa: test tên/đường khớp mọi thứ hay khớp `.git`, phủ định, `-o` với nhánh rộng → không lọc."""
        for cmd in (
            f"find {R} -path '*' -delete",
            "find . -name '*' -delete",
            "find . -type f -name '*' -delete",
            "find . -regex '.*' -delete",
            "find . -iregex '.*/\\.GIT' -delete",
            "find . -regex '[' -delete",  # regex hỏng: chiều chặt
            "find . -name '.*' -delete",
            "find . -iname '.GIT' -delete",
            "find . -name .git -exec rm -rf {} +",
            "find . -type d -name .git -exec rm -rf {} +",
            "find . -name '.git' -delete",
            f"find {R} -name .git -delete",
            "find . -path './.git' -delete",
            f"find {R} -wholename '*/.git' -delete",
            "find . ! -name x -delete",
            "find . -not -name '*.pyc' -delete",
            "find . -name '*.pyc' -o -name '*' -delete",
            "cd scripts && find . -name '*' -delete",  # không phải gốc: luật `find .` không lọc
        ):
            with self.subTest(cmd=cmd):
                self.assertEqual(policy(cmd)["decision"], "deny")
        for cmd in (
            "find . -name '*.pyc' -delete",
            "find . -type f -name '*.log' -delete",
            "find . -type d -empty -delete",
            "find . -name node_modules -prune -o -print",
            "find . -name '*.pyc' -name '*' -delete",  # AND: còn một lọc tin được
            "find . -path './build/*' -delete",
            "find . -regex '.*\\.pyc' -delete",
            "find . -lname '*' -delete",  # chỉ symlink
        ):
            with self.subTest(cmd=cmd):
                self.assertEqual(policy(cmd)["decision"], "", cmd)

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
