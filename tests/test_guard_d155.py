"""D-155 (PLAN-3.21-guard-d155): giới hạn guard xoá gốc dự án đã biết — tên lệnh qua glob (`fi?d`, `r?`), công cụ khác
(`fd -X rm`, `bfs`, `gfind`), `~user`. Guard là lớp chặn sai lầm, không phải sandbox (D-015)."""

from __future__ import annotations

import os
import pwd
import sys
import time
import unittest
import unittest.mock as mock
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.environ.setdefault("XT_GUARD_PHASE", "harden")


def _load_guard():
    sys.path.insert(0, str(ROOT / ".claude" / "hooks"))
    import guard as g

    return g


guard = _load_guard()
R = str(ROOT)


def policy(cmd: str, cwd: str | None = None, root: str = R) -> dict:
    """Kết quả ở chính sách mặc định (không hỏi): `decision` deny hoặc rỗng."""
    with mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": root, "XT_GUARD_POLICY": ""}):
        return dict(guard.apply_policy(guard.bash_decision(cmd, root, cwd)))


class GlobCommandNameTest(unittest.TestCase):
    """T-2811: shell mở glob ở tên lệnh (`/usr/bin/fi?d` → `find`), guard so tên theo chữ nên từng bỏ lọt."""

    def test_guard_glob_command_name_denied(self):
        for cmd in (
            f"/usr/bin/fi?d {R} -delete",
            f"/usr/bin/f[i]nd {R} -delete",
            f"/usr/bin/fin* {R} -delete",
            "/usr/bin/fi?d . -delete",
            f"/usr/bin/fi?d {R} \\( -name a \\) -delete",  # shlex cắt `\(`: chỉ chuỗi gốc thấy `-delete`
            f"/bin/r? -rf {R}",
            f"/bin/[r]m -rf {R}",
            f"/bin/r* -rf {R}",
            f"/bin/r? -rf {R}/.git",
            f"nohup /bin/r? -rf {R}",
            f"env X=1 /bin/r? -rf {R}",
            f"ti?e rm -rf {R}",  # wrapper qua glob rồi lệnh thật
            "/bin/r? -rf ~",
            # Review #247: glob ở sau wrapper/từ khoá, `[^x]`, lớp POSIX, shell và eval qua glob
            f"nohup /usr/bin/fi?d {R} \\( -name a \\) -delete",
            f"time /usr/bin/fi?d {R} \\( -name a \\) -delete",
            f"if /bin/r? -rf {R}; then :; fi",
            f"{{ /bin/r? -rf {R}; }}",
            f"/bin/[^x]m -rf {R}",
            f"/bin/[[:lower:]]m -rf {R}",
            f"/bin/ba?h -c 'rm -rf {R}'",
            f"/bin/s? -c 'rm -rf {R}'",
            f"ev?l 'rm -rf {R}'",
            "/usr/bin/s?do ls",
            "/usr/bin/[^x]udo ls",
            "/usr/bin/[[:lower:]]udo ls",
            "/usr/bin/su[[:alpha:]]o ls",
            "/usr/bin/[!x]udo ls",
        ):
            with self.subTest(cmd=cmd):
                self.assertEqual(policy(cmd)["decision"], "deny")

    def test_guard_glob_command_name_not_overblocked(self):
        for cmd in (
            "ls",
            "/usr/bin/fi?d . -name x",  # find không hành động xoá
            "/bin/r? /tmp/x",  # rm không đệ quy
            "/bin/r? -rf /tmp/xx",  # thư mục tạm
            "[ -f x ] && echo ok",
            "[[ -f x ]] && echo ok",
            "./scripts/dev-task.* gate-fast",  # glob không khớp tên nhạy cảm nào
            "echo '/bin/r? -rf x'",  # trong chuỗi nháy là dữ liệu
            # Review #247 🔴: mẫu nhánh `case` không phải tên lệnh — `*)`, `s*)` từng bị đọc là sudo/doas
            'case "$x" in a) echo a;; *) echo other;; esac',
            "case $x in (*) echo u;; esac",
            "case $x in -*) echo f;; s*) echo s;; esac",
            'case "$f" in *.py) ruff format "$f" ;; *) : ;; esac',
            "* --help",
            "?? --help",
            "s*",
        ):
            with self.subTest(cmd=cmd):
                self.assertEqual(policy(cmd)["decision"], "")

    def test_guard_glob_nested_wrappers_stay_within_scan_budget(self):
        """Review #247 🔴: 7 wrapper khớp `[bcenx]*` từng quét 52 s (bậc mũ, ngoài `ScanBudget`); nay chạm ngân sách → chặn."""
        cmd = " ".join(["[bcenx]*"] * 7) + " true"
        start = time.monotonic()
        out = policy(cmd)
        self.assertLess(time.monotonic() - start, 15)
        self.assertEqual(out["decision"], "deny")

    def test_guard_glob_names_closed_list(self):
        self.assertEqual(guard._glob_names("ls"), [])  # không glob
        self.assertEqual(guard._glob_names("["), [])  # `[` của test
        self.assertEqual(guard._glob_names("*"), [])  # toàn `*`/`?` không đoán
        self.assertEqual(guard._glob_names("??"), [])
        self.assertEqual(guard._glob_names("r?"), ["rm"])
        self.assertEqual(guard._glob_names("[r]m"), ["rm"])
        self.assertEqual(guard._glob_names("[^x]m"), ["rm"])  # bash: `[^…]` = `[!…]`
        self.assertEqual(guard._glob_names("[[:lower:]]m"), ["rm"])  # lớp POSIX = một ký tự bất kỳ
        self.assertIn("find", guard._glob_names("fin?"))
        self.assertIn("bash", guard._glob_names("ba?h"))
        self.assertIn("eval", guard._glob_names("ev?l"))

    def test_guard_glob_rewrites_one_variant_per_name(self):
        self.assertEqual(guard._glob_rewrites(guard.tokenize("ls -l")), [])
        self.assertEqual(guard._glob_rewrites([]), [])
        self.assertEqual(guard._glob_rewrites(guard.tokenize("s*")), [])  # không đối số
        self.assertEqual(guard._glob_rewrites(guard.tokenize("FOO=1 /bin/r? -rf x")), ["FOO=1 rm -rf x"])
        self.assertEqual(guard._glob_rewrites(guard.tokenize("echo a; fin? . -delete")), ["echo a ; find . -delete"])


class TildeUserTest(unittest.TestCase):
    """T-2811: `~user` mở ra home của user đó — home là cha/chính gốc dự án thì xoá đệ quy bị chặn; user không tồn tại
    thì shell giữ nguyên chữ (thư mục tương đối) nên guard không đổi."""

    FAKE = {"dev": os.path.dirname(R), "me": R, "other": "/srv/other"}

    def _getpwnam(self, name: str):
        if name not in self.FAKE:
            raise KeyError(name)
        return pwd.struct_passwd((name, "x", 1000, 1000, "", self.FAKE[name], "/bin/sh"))

    def test_guard_tilde_user_wipes_denied(self):
        with mock.patch("pwd.getpwnam", self._getpwnam):
            for cmd in (
                "rm -rf ~dev",
                "rm -rf ~dev/",
                "rm -rf ~dev/*",
                "rm -r ~dev",
                f"rm -rf ~dev/{ROOT.name}",
                "rm -rf ~me",
                "rm -rf ~me/*",
                "rm -rf ~me/.git",
                "find ~dev -delete",
            ):
                with self.subTest(cmd=cmd):
                    self.assertEqual(policy(cmd)["decision"], "deny")

    def test_guard_tilde_unknown_user_is_relative_path(self):
        with mock.patch("pwd.getpwnam", self._getpwnam):
            self.assertEqual(policy("rm -rf ~nouser/x")["decision"], "")


if __name__ == "__main__":
    unittest.main()
