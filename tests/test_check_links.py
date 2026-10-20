"""Test scripts/check-links.py nạp như module (đo coverage trong tiến trình) — ca CLI nằm ở test_install.py."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import tempfile
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from types import ModuleType
import unittest.mock as mock

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "check-links.py"


def load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("check_links_under_test", SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class CheckLinksModuleTest(unittest.TestCase):
    def setUp(self):
        self.cl = load_module()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.repo = Path(tmp.name)

    def write(self, rel: str, text: str) -> None:
        p = self.repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    def test_root_is_project_when_installed_under_xtemplates(self):
        # Bản cài ở <dự án>/.xtemplates/scripts/ → gốc là dự án; biên dịch với tên file thật để coverage đếm đúng file.
        fake = self.repo.resolve() / ".xtemplates" / "scripts" / "check-links.py"
        ns: dict[str, object] = {"__file__": str(fake), "__name__": "check_links_installed"}
        exec(compile(SCRIPT.read_text(encoding="utf-8"), str(SCRIPT), "exec"), ns)
        self.assertEqual(ns["ROOT"], self.repo.resolve())
        self.assertEqual(self.cl.ROOT, ROOT)  # chạy từ repo khung: gốc là repo

    def test_iter_md_skips_tooling_dirs(self):
        for rel in ("a.md", "docs/b.md", "node_modules/x.md", ".git/y.md", "sub/.xtemplates/z.md", ".venv/w.md"):
            self.write(rel, "x\n")
        names = [p.relative_to(self.repo).as_posix() for p in self.cl.iter_md(self.repo)]
        self.assertEqual(names, ["a.md", "docs/b.md"])

    def test_check_reports_broken_with_file_and_line(self):
        self.write("docs/ok.md", "x\n")
        self.write("a.md", "dòng 1\n[tốt](docs/ok.md#neo) [hỏng](docs/mat.md)\n")
        self.assertEqual(self.cl.check(self.repo), ["a.md:2: liên kết hỏng -> docs/mat.md"])

    def test_check_accepts_root_absolute_and_skips_urls_anchors(self):
        self.write("docs/ok.md", "x\n")
        self.write(
            "sub/a.md",
            "[abs](/docs/ok.md) [neo](#muc) [url](https://x.invalid/a) [mail](mailto:a@b.c) [dir](../docs)\n",
        )
        self.assertEqual(self.cl.check(self.repo), [])

    def test_check_absolute_link_missing_is_error(self):
        self.write("a.md", "[x](/khong/co.md)\n")
        self.assertEqual(self.cl.check(self.repo), ["a.md:1: liên kết hỏng -> /khong/co.md"])

    def test_check_fence_nesting_is_respected(self):
        # ``` mở thì ~~~ bên trong không đóng; sau khi đóng đúng loại, link ngoài fence lại được kiểm.
        self.write("a.md", "```\n~~~\n[in](a1.md)\n~~~\n```\n[out](a2.md)\n")
        self.assertEqual(self.cl.check(self.repo), ["a.md:6: liên kết hỏng -> a2.md"])

    def test_main_success_and_failure_output(self):
        self.write("ok.md", "[a](ok.md)\n")
        out = io.StringIO()
        with mock.patch("sys.argv", ["check-links.py", str(self.repo)]), contextlib.redirect_stdout(out):
            self.assertEqual(self.cl.main(), 0)
        self.assertIn("✓ Mọi liên kết Markdown nội bộ", out.getvalue())
        self.write("bad.md", "[a](nope.md)\n[b](nope2.md)\n")
        out = io.StringIO()
        with mock.patch("sys.argv", ["check-links.py", str(self.repo)]), contextlib.redirect_stdout(out):
            self.assertEqual(self.cl.main(), 1)
        self.assertIn("✗ bad.md:1: liên kết hỏng -> nope.md", out.getvalue())
        self.assertIn("2 liên kết hỏng.", out.getvalue())

    def test_main_defaults_to_repo_root(self):
        out = io.StringIO()
        with (
            mock.patch("sys.argv", ["check-links.py"]),
            mock.patch.object(self.cl, "ROOT", self.repo),
            contextlib.redirect_stdout(out),
        ):
            self.assertEqual(self.cl.main(), 0)
        self.assertIn("✓", out.getvalue())
        self.write("bad.md", "[x](missing.md)\n")  # cùng ROOT, giờ có link hỏng → phải đỏ (chứng minh đã quét ROOT)
        out = io.StringIO()
        with (
            mock.patch("sys.argv", ["check-links.py"]),
            mock.patch.object(self.cl, "ROOT", self.repo),
            contextlib.redirect_stdout(out),
        ):
            self.assertEqual(self.cl.main(), 1)
        self.assertIn("bad.md:1", out.getvalue())


class FakeResp:
    def __init__(self, status: int):
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class FakeOpener:
    """Opener giả: `script` là danh sách (method, kết quả) theo thứ tự gọi; kết quả int = trả status, int âm = HTTPError."""

    def __init__(self, script):
        self.script = list(script)
        self.calls: list[str] = []

    def open(self, req, timeout=None):
        self.calls.append(req.get_method())
        kind, val = self.script.pop(0)
        assert kind == req.get_method()
        if isinstance(val, Exception):
            raise val
        return FakeResp(val)


def http_err(code: int) -> urllib.error.HTTPError:
    return urllib.error.HTTPError("http://x", code, "m", {}, None)  # type: ignore[arg-type]


class LinkClassificationTest(unittest.TestCase):
    def setUp(self):
        self.cl = load_module()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.repo = Path(tmp.name)

    def test_link_classification_status_table(self):
        for status, want in [
            (200, "ok"), (206, "ok"), (301, "moved"), (308, "moved"), (403, "unverified"), (429, "unverified"),
            (404, "dead"), (410, "dead"), (400, "dead"), (100, "dead"), (408, "transient"), (500, "transient"),
            (503, "transient"), (599, "transient"),
        ]:  # fmt: skip
            self.assertEqual(self.cl.classify_status(status), want, status)

    def test_link_classification_retries_transient_then_gives_up(self):
        sleeps: list[float] = []
        calls: list[str] = []

        def fetch(url, timeout):
            calls.append(url)
            return 503

        got = self.cl.check_url("http://h/a", fetch, retries=2, sleep=sleeps.append)
        self.assertEqual(got, ("transient", "HTTP 503"))
        self.assertEqual(len(calls), 3)
        self.assertEqual(sleeps, [1.0, 2.0])

    def test_link_classification_recovers_after_transient(self):
        results = iter([500, 429, 200])
        got = self.cl.check_url("http://h/a", lambda u, t: next(results), retries=3, sleep=lambda s: None)
        self.assertEqual(got, ("ok", "HTTP 200"))

    def test_link_classification_timeout_is_transient_and_zero_retries(self):
        n = []

        def fetch(url, timeout):
            n.append(1)
            raise TimeoutError("t")

        got = self.cl.check_url("http://h/a", fetch, retries=0, sleep=lambda s: None)
        self.assertEqual(got, ("transient", "timeout/lỗi mạng (TimeoutError)"))
        self.assertEqual(len(n), 1)

    def test_link_classification_no_retry_for_dead_moved_403(self):
        for status, cat in [(404, "dead"), (301, "moved"), (403, "unverified")]:
            n = []

            def fetch(url, timeout, status=status, n=n):
                n.append(1)
                return status

            self.assertEqual(self.cl.check_url("http://h", fetch, retries=3, sleep=lambda s: None)[0], cat)
            self.assertEqual(len(n), 1, status)

    def test_link_classification_429_exhausted_is_unverified(self):
        got = self.cl.check_url("http://h", lambda u, t: 429, retries=1, sleep=lambda s: None)
        self.assertEqual(got, ("unverified", "HTTP 429"))

    def test_link_classification_external_urls_dedup_skip_fence_and_hosts(self):
        self.write(
            "a.md",
            "[a](https://x.org/p#s) [b](https://x.org/p) [c](https://example.com/z) [d](http://localhost:1/)"
            " [e](https://h.invalid/q) [f](docs/x.md) [g](mailto:a@b.c)\n```\n[h](https://fence.org/)\n```\n"
            "[i](https://Y.org/Ünï)\n",
        )
        self.write("sub/b.md", "[j](https://x.org/p)\n")
        urls = self.cl.external_urls(self.repo)
        self.assertEqual(urls, {"https://x.org/p": "a.md:1", "https://Y.org/Ünï": "a.md:5"})

    def write(self, rel: str, text: str) -> None:
        p = self.repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    def test_link_classification_autolink_and_bare_urls_found_code_spans_skipped(self):
        self.write(
            "a.md",
            "Nguồn: <https://auto.org/a> · <https://auto.org/b#neo>; xem https://bare.org/x. và (https://bare.org/p_(1))\n"
            "Ví dụ `![x](https://evil/?d=1)` và `![](https://attacker/?q=<secret>)` và ``a ` <https://span.org/z>``\n"
            "[https://text.org/](https://dich.org/) [ref]: https://ref.org/r, rồi **https://bold.org/b**\n"
            "```\n<https://fence.org/>\n```\n"
            "<https://example.com/x> <mailto:a@b.c> <http://h.test/> ổn <https://Ü.org/ä>\n",
        )
        urls = self.cl.external_urls(self.repo)
        self.assertEqual(
            urls,
            {
                "https://auto.org/a": "a.md:1",
                "https://auto.org/b": "a.md:1",
                "https://bare.org/x": "a.md:1",
                "https://bare.org/p_(1)": "a.md:1",
                "https://dich.org/": "a.md:3",
                "https://ref.org/r": "a.md:3",
                "https://bold.org/b": "a.md:3",
                "https://Ü.org/ä": "a.md:7",
            },
        )
        self.assertEqual(self.cl.line_urls(""), [])
        self.assertEqual(self.cl.line_urls("`https://a.org/` `` `x` ``"), [])

    def test_link_classification_dead_autolink_reported_code_span_ignored(self):
        self.write("a.md", "Nguồn: <https://h.org/gone>\nVí dụ: `<https://h.org/span>` https://h.org/ok\n")
        fetched: list[str] = []

        def fetch(url, timeout):
            fetched.append(url)
            return 404 if url.endswith("gone") else 200

        rep = self.cl.check_external(self.repo, fetch, retries=0, workers=1)
        self.assertEqual(rep, {"dead": ["a.md:1: https://h.org/gone — HTTP 404"]})
        self.assertEqual(sorted(fetched), ["https://h.org/gone", "https://h.org/ok"])
        out = io.StringIO()
        with mock.patch.object(self.cl, "http_status", fetch), contextlib.redirect_stdout(out):
            self.assertEqual(self.cl.main([str(self.repo), "--external", "--retries", "0"]), 1)
        self.assertIn("✗ chết (sửa/bỏ link): a.md:1: https://h.org/gone — HTTP 404", out.getvalue())

    def test_link_classification_check_external_report_groups(self):
        self.write(
            "a.md",
            "[1](http://h/ok) [2](http://h/gone) [3](http://h/moved) [4](http://h/bot) [5](http://h/down)\n",
        )
        codes = {"/ok": 200, "/gone": 404, "/moved": 301, "/bot": 403, "/down": 502}

        def fetch(url, timeout):
            return codes[url[len("http://h") :]]

        rep = self.cl.check_external(self.repo, fetch, retries=0, workers=2)
        self.assertEqual(set(rep), {"dead", "moved", "unverified", "transient"})
        self.assertEqual(rep["dead"], ["a.md:1: http://h/gone — HTTP 404"])
        self.assertNotIn("ok", rep)

    def test_link_classification_main_external_exit_codes_and_output(self):
        self.write("a.md", "[1](http://h/ok) [2](http://h/moved)\n")
        out = io.StringIO()
        with (
            mock.patch.object(self.cl, "http_status", lambda u, t: 301 if u.endswith("moved") else 200),
            contextlib.redirect_stdout(out),
        ):
            self.assertEqual(self.cl.main([str(self.repo), "--external", "--retries", "-5"]), 0)
        self.assertIn("! đã đổi (cập nhật URL): a.md:1: http://h/moved — HTTP 301", out.getvalue())
        self.assertIn("✓ Không có liên kết ngoài chết", out.getvalue())
        out = io.StringIO()
        with mock.patch.object(self.cl, "http_status", lambda u, t: 404), contextlib.redirect_stdout(out):
            self.assertEqual(self.cl.main([str(self.repo), "--external"]), 1)
        self.assertIn("✗ chết (sửa/bỏ link): a.md:1: http://h/ok — HTTP 404", out.getvalue())
        self.assertIn("2 liên kết ngoài chết.", out.getvalue())

    def test_link_classification_main_without_external_ignores_urls(self):
        self.write("a.md", "[1](http://h/never-fetched)\n")
        with mock.patch.object(self.cl, "http_status", side_effect=AssertionError("không được gọi mạng")):
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(self.cl.main([str(self.repo)]), 0)

    def test_link_classification_http_status_head_then_get_fallback(self):
        op = FakeOpener([("HEAD", http_err(405)), ("GET", 200)])
        self.assertEqual(self.cl.http_status("http://h", 1.0, op), 200)
        self.assertEqual(op.calls, ["HEAD", "GET"])
        op = FakeOpener([("HEAD", 301)])
        self.assertEqual(self.cl.http_status("http://h", 1.0, op), 301)
        self.assertEqual(op.calls, ["HEAD"])

    def test_review173_head_4xx_retried_with_get(self):
        """PR #173: HEAD 4xx (trừ 404/410) không đủ kết luận chết — thử GET; 401 là `unverified`."""
        for head, get, want in [(400, 200, 200), (401, 401, 401), (418, 404, 404), (429, 200, 200)]:
            with self.subTest(head=head):
                op = FakeOpener([("HEAD", http_err(head)), ("GET", get if get < 400 else http_err(get))])
                self.assertEqual(self.cl.http_status("http://h", 1.0, op), want)
                self.assertEqual(op.calls, ["HEAD", "GET"])
        for gone in (404, 410):
            op = FakeOpener([("HEAD", http_err(gone))])
            self.assertEqual(self.cl.http_status("http://h", 1.0, op), gone)
            self.assertEqual(op.calls, ["HEAD"])
        self.assertEqual(self.cl.classify_status(401), "unverified")
        self.assertEqual(self.cl.classify_status(410), "dead")

    def test_link_classification_http_status_error_codes(self):
        op = FakeOpener([("HEAD", http_err(404))])
        self.assertEqual(self.cl.http_status("http://h", 1.0, op), 404)
        op = FakeOpener([("HEAD", http_err(403)), ("GET", http_err(403))])
        self.assertEqual(self.cl.http_status("http://h", 1.0, op), 403)
        op = FakeOpener([("HEAD", urllib.error.URLError("dns"))])
        with self.assertRaises(OSError):
            self.cl.http_status("http://h", 1.0, op)

    def test_link_classification_http_status_default_opener_does_not_follow_redirects(self):
        handler = self.cl._NoRedirect()
        req = urllib.request.Request("http://h/a")
        self.assertIsNone(handler.redirect_request(req, None, 301, "m", {}, "http://h/b"))
        with mock.patch("urllib.request.build_opener") as bo:
            bo.return_value = FakeOpener([("HEAD", 204)])
            self.assertEqual(self.cl.http_status("http://h", 1.0), 204)
        bo.assert_called_once_with(self.cl._NoRedirect)


class AutonomyPolicySingleHomeTest(unittest.TestCase):
    HOME = ROOT / "framework" / "11-autonomous-loop" / "stop-points-and-escalation.md"
    MARKERS = ("### Mức tự chủ L0–L4", "| L3 Tự chủ làn chuẩn", "| L2 Tự chủ làn nhanh", '### Vị từ "làn nhanh"')

    def md_files(self):
        skip = {".git", "node_modules", ".venv", ".autopilot", "__pycache__", ".xtemplates"}
        for p in sorted(ROOT.rglob("*.md")):
            parts = p.relative_to(ROOT).parts
            # .claude/worktrees: bản sao repo của subagent, không phải nội dung của repo
            if not any(part in skip for part in parts) and parts[:2] != (".claude", "worktrees"):
                yield p

    def test_autonomy_policy_single_home_markers_only_in_home(self):
        home = self.HOME.read_text(encoding="utf-8")
        for marker in self.MARKERS:
            self.assertEqual(home.count(marker), 1, marker)
        others = [p for p in self.md_files() if p != self.HOME]
        self.assertGreater(len(others), 50)  # chắc chắn đã quét repo, không quét rỗng
        for p in others:
            text = p.read_text(encoding="utf-8")
            for marker in self.MARKERS:
                self.assertNotIn(marker, text, f"{p.relative_to(ROOT)} chép chính sách tự chủ; chỉ liên kết tới nhà")

    def test_autonomy_policy_single_home_readme_links_home(self):
        readme = (ROOT / "framework" / "11-autonomous-loop" / "README.md").read_text(encoding="utf-8")
        self.assertIn("## Chính sách tự chủ: một nhà", readme)
        self.assertIn("(stop-points-and-escalation.md)", readme.split("## Chính sách tự chủ: một nhà", 1)[1])

    def test_autonomy_policy_single_home_detects_duplicate(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "x.md").write_text("| L3 Tự chủ làn chuẩn | copy |\n", encoding="utf-8")
            text = (Path(d) / "x.md").read_text(encoding="utf-8")
            self.assertTrue(any(m in text for m in self.MARKERS))


if __name__ == "__main__":
    unittest.main()
