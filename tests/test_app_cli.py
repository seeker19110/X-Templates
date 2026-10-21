"""Lệnh `xt.py app` (T-1913): smoke, chạy thường, lỗi khởi động, import lười."""

from __future__ import annotations

import contextlib
import io
import os
import socket
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import xt  # noqa: E402
from xt_app import server  # noqa: E402


def run(argv: list[str]) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = xt.main(argv)
    return rc, out.getvalue(), err.getvalue()


class AppCliTest(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.addCleanup(os.chdir, os.getcwd())  # `xt.py app` chdir về gốc dự án — trả cwd trước khi xoá thư mục tạm
        patcher = mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": tmp.name})
        patcher.start()
        self.addCleanup(patcher.stop)

    def _smoke_health_only(self) -> tuple[int, str, str]:
        # Độc lập với module api_* khác: chỉ route lõi.
        real = server.make_server
        with mock.patch.object(server, "make_server", lambda **kw: real(routes=server.ROUTES, **kw)):
            return run(["app", "--smoke"])

    def test_smoke_green(self) -> None:
        rc, out, _ = self._smoke_health_only()
        self.assertEqual(rc, 0)
        self.assertIn("✓ /api/health 200", out)

    def test_smoke_red_and_skips_non_get(self) -> None:
        def boom(_ctx: server.Ctx) -> tuple[int, dict[str, object]]:
            raise RuntimeError("x")

        def post(_ctx: server.Ctx) -> tuple[int, dict[str, object]]:
            return 200, {}

        routes = {("GET", "/api/boom"): boom, ("POST", "/api/w"): post}
        real = server.make_server
        with mock.patch.object(server, "make_server", lambda **kw: real(routes=routes, **kw)):
            rc, out, _ = run(["app", "--smoke"])
        self.assertEqual(rc, 1)
        self.assertIn("✗ /api/boom 500", out)
        self.assertNotIn("/api/w", out)

    def _serve(self, argv: list[str], open_exc: Exception | None = None) -> tuple[int, str, mock.Mock]:
        opener = mock.Mock(side_effect=open_exc)
        with (
            mock.patch("webbrowser.open", opener),
            mock.patch.object(server.AppServer, "serve_forever", side_effect=KeyboardInterrupt),
        ):
            rc, out, _ = run(argv)
        return rc, out, opener

    def test_serve_opens_browser(self) -> None:
        rc, out, opener = self._serve(["app"])
        self.assertEqual(rc, 0)
        self.assertIn("http://127.0.0.1:", out)
        self.assertIn("/#t=", out)
        opener.assert_called_once()

    def test_serve_no_open(self) -> None:
        rc, out, opener = self._serve(["app", "--no-open"])
        self.assertEqual(rc, 0)
        self.assertIn("#t=", out)
        opener.assert_not_called()

    def test_serve_browser_error_warns(self) -> None:
        rc, out, _ = self._serve(["app"], RuntimeError("không có display"))
        self.assertEqual(rc, 0)
        self.assertIn("⚠", out)

    def test_bad_port(self) -> None:
        for bad in ("70000", "-1", "abc"):
            with self.subTest(bad=bad), self.assertRaises(SystemExit) as cm, contextlib.redirect_stderr(io.StringIO()):
                xt.main(["app", "--port", bad])
            self.assertEqual(cm.exception.code, 2)

    def test_port_busy(self) -> None:
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            sock.listen(1)
            rc, _, err = run(["app", "--port", str(sock.getsockname()[1])])
        self.assertEqual(rc, 2)
        self.assertIn("✗", err)

    def test_lazy_import(self) -> None:
        code = "import sys; sys.path.insert(0,'scripts'); import xt; xt.main(['stats']); print('xt_app' in sys.modules)"
        res = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True, check=True)
        self.assertEqual(res.stdout.strip().splitlines()[-1], "False")

    def test_path_already_in_sys_path(self) -> None:
        self.assertIn(str(xt.SCRIPT_DIR), sys.path)
        rc, _, _ = self._smoke_health_only()
        self.assertEqual(rc, 0)

    def test_adds_script_dir_to_sys_path(self) -> None:
        trimmed = [p for p in sys.path if p != str(xt.SCRIPT_DIR)]
        with mock.patch.object(sys, "path", trimmed):
            rc, _, _ = self._smoke_health_only()
            self.assertIn(str(xt.SCRIPT_DIR), sys.path)
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()


class AppCwdTest(unittest.TestCase):
    def test_app_chdirs_to_project_root(self) -> None:
        """API PR gọi `gh`/`git` theo cwd: `xt.py app` đặt cwd = gốc dự án dù chạy từ thư mục khác."""
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.addCleanup(os.chdir, os.getcwd())
        base = Path(tmp.name).resolve()
        (base / "sub").mkdir()
        os.chdir(base / "sub")
        with mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(base)}), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(xt.main(["app", "--smoke"]), 0)
        self.assertEqual(Path(os.getcwd()).resolve(), base)
