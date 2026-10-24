"""D-155 (PLAN-3.21-guard-d155): giới hạn guard xoá gốc dự án đã biết — tên lệnh qua glob (`fi?d`, `r?`), công cụ khác
(`fd -X rm`, `bfs`, `gfind`), `~user`. Guard là lớp chặn sai lầm, không phải sandbox (D-015)."""

from __future__ import annotations

import os
import pwd
import sys
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
        ):
            with self.subTest(cmd=cmd):
                self.assertEqual(policy(cmd)["decision"], "")

    def test_guard_glob_name_variants_are_closed_list(self):
        self.assertEqual(guard._glob_name_variants(["ls", "-l"]), [])
        self.assertEqual(guard._glob_name_variants([]), [])
        self.assertEqual(guard._glob_name_variants(["["]), [])
        self.assertEqual(
            guard._glob_name_variants(["FOO=1", "/bin/r?", "-rf", "x"]),
            [["FOO=1", "rm", "-rf", "x"]],
        )
        self.assertIn(["find", ".", "-delete"], guard._glob_name_variants(["fin?", ".", "-delete"]))


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
