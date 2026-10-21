"""Test đối kháng cho scripts/xt_app/server.py (ADR-0038 §2, SPEC-app §2) — máy chủ cổng 0 trong thread, `http.client`."""

from __future__ import annotations

import http.client
import io
import json
import os
import socket
import sys
import tempfile
import threading
import time
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from xt_app import server

TOKEN = "t0k3n-for-tests_ABCDEFGHIJKLMNOPQRSTUVWXYZ012"
SEC = {name.lower(): value for name, value in server.SECURITY_HEADERS}
DEFAULT = object()
Resp = Tuple[int, Dict[str, str], bytes]


def _query(ctx: server.Ctx) -> Tuple[int, Dict[str, Any]]:
    return 200, {"query": ctx.query, "xt": ctx.xt, "base": ctx.base.name, "fw": ctx.framework.name, "body": ctx.body}


def _echo(ctx: server.Ctx) -> Tuple[int, Dict[str, Any]]:
    return 200, {"got": ctx.body}


def _boom(ctx: server.Ctx) -> Tuple[int, Dict[str, Any]]:
    raise RuntimeError("nổ " + TOKEN[:0])


def _unserializable(ctx: server.Ctx) -> Tuple[int, Dict[str, Any]]:
    return 200, {"x": object()}


def _missing(ctx: server.Ctx) -> Tuple[int, Dict[str, Any]]:
    return 404, {"error": "không có tài nguyên"}


BARRIER = threading.Barrier(4, timeout=5)


def _barrier(ctx: server.Ctx) -> Tuple[int, Dict[str, Any]]:
    BARRIER.wait()
    return 200, {"ok": True}


FAKE_ROUTES: server.Routes = {
    **server.ROUTES,
    ("GET", "/api/q"): _query,
    ("POST", "/api/echo"): _echo,
    ("GET", "/api/boom"): _boom,
    ("GET", "/api/bad"): _unserializable,
    ("GET", "/api/nf"): _missing,
    ("GET", "/api/barrier"): _barrier,
}


def make_tree(tmp: Path) -> Tuple[Path, Path, Path]:
    """(base, framework, static_root) — static có symlink file/thư mục, đuôi lạ; base có VERSION ở cha framework."""
    base = tmp / "proj"
    fw = base / "framework"
    fw.mkdir(parents=True)
    (base / "VERSION").write_text("9.9.9\n", encoding="utf-8")
    static = tmp / "static"
    (static / "views").mkdir(parents=True)
    (static / "index.html").write_text("<!doctype html><title>x</title>", encoding="utf-8")
    (static / "app.css").write_text("body{}", encoding="utf-8")
    (static / "views" / "a.js").write_text("export {};", encoding="utf-8")
    (static / "notes.txt").write_text("đuôi lạ", encoding="utf-8")
    outside = tmp / "outside"
    outside.mkdir()
    (outside / "secret.js").write_text("SECRET", encoding="utf-8")
    (static / "link.js").symlink_to(outside / "secret.js")
    (static / "linkdir").symlink_to(outside, target_is_directory=True)
    os.mkfifo(static / "pipe.js")
    return base, fw, static


class ServerCase(unittest.TestCase):
    routes: Optional[server.Routes] = FAKE_ROUTES

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.base, self.fw, self.static = make_tree(self.tmp)
        self.srv, self.token = server.make_server(
            "XT", self.base, self.fw, self.static, token=TOKEN, routes=self.routes
        )
        self.srv.quiet = True
        self.port = self.srv.server_address[1]
        self.thread = threading.Thread(target=self.srv.serve_forever, args=(0.02,), daemon=True)
        self.thread.start()

    def tearDown(self) -> None:
        self.srv.shutdown()
        self.srv.server_close()
        self.thread.join(5)
        self._tmp.cleanup()

    # --- trợ giúp --------------------------------------------------------------------------------------------------
    def host(self) -> str:
        return f"127.0.0.1:{self.port}"

    def check_common(self, path: str, headers: Dict[str, str]) -> None:
        for name, value in SEC.items():
            self.assertEqual(headers.get(name), value, f"{name} trên {path}")
        self.assertEqual(headers.get("server"), "xt-app")
        if path.startswith("/api/"):
            self.assertEqual(headers.get("cache-control"), "no-store", path)
        else:
            self.assertNotIn("cache-control", headers, path)

    def req(
        self,
        method: str,
        path: str,
        headers: Optional[List[Tuple[str, str]]] = None,
        body: Optional[bytes] = None,
        host: Any = DEFAULT,
        token: bool = False,
        conn: Optional[http.client.HTTPConnection] = None,
    ) -> Resp:
        own = conn is None
        c = conn or http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        try:
            c.putrequest(method, path, skip_host=True, skip_accept_encoding=True)
            if host is DEFAULT:
                c.putheader("Host", self.host())
            elif host is not None:
                c.putheader("Host", host)
            if token:
                c.putheader("X-XT-Token", TOKEN)
            for name, value in headers or []:
                c.putheader(name, value)
            c.endheaders(body)
            resp = c.getresponse()
            data = resp.read()
            hdrs = {k.lower(): v for k, v in resp.getheaders()}
        finally:
            if own:
                c.close()
        self.check_common(path.split("?")[0] if path.startswith("/") else "", hdrs)
        self.assertEqual(hdrs.get("content-length"), str(len(data)) if method != "HEAD" else hdrs.get("content-length"))
        return resp.status, hdrs, data

    def post(self, body: bytes, ctype: str = "application/json", extra: Optional[List[Tuple[str, str]]] = None) -> Resp:
        headers = [("Content-Type", ctype), ("Content-Length", str(len(body)))] + (extra or [])
        return self.req("POST", "/api/echo", headers, body, token=True)

    def raw(self, payload: bytes) -> bytes:
        with socket.create_connection(("127.0.0.1", self.port), timeout=10) as s:
            s.sendall(payload)
            chunks = []
            while True:
                chunk = s.recv(65536)
                if not chunk:
                    break
                chunks.append(chunk)
        return b"".join(chunks)

    def assertError(self, resp: Resp, status: int) -> Dict[str, Any]:
        self.assertEqual(resp[0], status, resp[2])
        self.assertTrue(resp[1]["content-type"].startswith("application/json"))
        payload = json.loads(resp[2].decode("utf-8"))
        self.assertIsInstance(payload["error"], str)
        self.assertNotIn(TOKEN, resp[2].decode("utf-8"))
        return payload


class BindAndTokenTest(ServerCase):
    def test_bind_loopback_and_threads(self) -> None:
        self.assertEqual(self.srv.server_address[0], "127.0.0.1")
        self.assertTrue(self.srv.daemon_threads)
        self.assertIsInstance(self.srv, server.ThreadingHTTPServer)

    def test_token_required_on_api(self) -> None:
        self.assertError(self.req("GET", "/api/health"), 401)
        self.assertError(self.req("GET", "/api/health", [("X-XT-Token", "sai")]), 401)
        self.assertError(self.req("GET", "/api/health", [("X-XT-Token", TOKEN + "x")]), 401)
        self.assertError(self.req("GET", "/api/health", [("X-XT-Token", "tökèn")]), 401)
        self.assertError(self.req("GET", "/api/health", [("X-XT-Token", TOKEN), ("X-XT-Token", TOKEN)]), 401)
        status, _, data = self.req("GET", "/api/health", token=True)
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(data), {"ok": True, "version": "9.9.9", "project": "proj"})

    def test_static_needs_no_token(self) -> None:
        status, hdrs, data = self.req("GET", "/")
        self.assertEqual((status, data), (200, b"<!doctype html><title>x</title>"))
        self.assertEqual(hdrs["content-type"], "text/html; charset=utf-8")
        status, hdrs, data = self.req("GET", "/views/a.js?v=1#f")
        self.assertEqual((status, data, hdrs["content-type"]), (200, b"export {};", "text/javascript; charset=utf-8"))
        self.assertEqual(self.req("GET", "/app.css")[1]["content-type"], "text/css; charset=utf-8")

    def test_unknown_api_is_404_before_token(self) -> None:
        self.assertError(self.req("GET", "/api/khong-co"), 404)


class HostOriginTest(ServerCase):
    def test_host(self) -> None:
        self.assertError(self.req("GET", "/", host="evil.example"), 421)
        self.assertError(self.req("GET", "/", host=f"evil.example:{self.port}"), 421)
        self.assertError(self.req("GET", "/", host="127.0.0.1"), 421)
        self.assertError(self.req("GET", "/", host=None), 421)
        self.assertError(self.req("GET", "/", [("Host", self.host())]), 421)  # hai Host
        self.assertEqual(self.req("GET", "/", host=f"localhost:{self.port}")[0], 200)
        self.assertEqual(self.req("GET", "/", host=self.host())[0], 200)

    def test_origin(self) -> None:
        self.assertError(self.req("GET", "/", [("Origin", "http://evil.example")]), 403)
        self.assertError(self.req("GET", "/", [("Origin", "null")]), 403)
        self.assertError(self.req("GET", "/", [("Origin", f"https://127.0.0.1:{self.port}")]), 403)
        self.assertError(
            self.req("GET", "/", [("Origin", f"http://{self.host()}"), ("Origin", f"http://{self.host()}")]), 403
        )
        self.assertEqual(self.req("GET", "/", [("Origin", f"http://{self.host()}")])[0], 200)
        resp = self.req("GET", "/api/health", [("Origin", f"http://localhost:{self.port}")], token=True)
        self.assertEqual(resp[0], 200)

    def test_host_checked_before_origin_and_path(self) -> None:
        self.assertError(self.req("GET", "/khong-co", [("Origin", "http://evil.example")], host="evil.example"), 421)
        self.assertError(self.req("GET", "/khong-co", [("Origin", "http://evil.example")]), 403)
        self.assertError(self.req("FOO", "/app.css", host="evil.example"), 421)


class PathTest(ServerCase):
    def test_traversal_and_symlink_are_404(self) -> None:
        for path in (
            "/../etc/passwd",
            "/%2e%2e/x",
            "/views/../app.css",
            "/views/%2e%2e/app.css",
            "/%2Fapp.css",
            "/link.js",
            "/linkdir/secret.js",
            "/notes.txt",
            "/pipe.js",
            "/views",
            "/views/",
            "//evil.example/app.css",
            "http://evil.example/app.css",
            "//[x",
            "http://[x/app.css",
            "*",
        ):
            with self.subTest(path=path):
                self.assertError(self.req("GET", path), 404)
        self.assertNotIn("/link.js", self.srv.static)
        self.assertNotIn("/linkdir/secret.js", self.srv.static)


class MethodTest(ServerCase):
    def test_static_methods(self) -> None:
        for method in ("PUT", "DELETE", "TRACE", "OPTIONS", "PATCH", "POST", "FOO"):
            with self.subTest(method=method):
                status, hdrs, _ = self.req(method, "/app.css")
                self.assertEqual(status, 405)
                self.assertEqual(hdrs["allow"], "GET, HEAD")

    def test_api_methods_before_token(self) -> None:
        status, hdrs, _ = self.req("PUT", "/api/health")
        self.assertEqual((status, hdrs["allow"]), (405, "GET, HEAD"))
        status, hdrs, _ = self.req("GET", "/api/echo")
        self.assertEqual((status, hdrs["allow"]), (405, "POST"))
        status, hdrs, _ = self.req("HEAD", "/api/echo", token=True)
        self.assertEqual((status, hdrs["allow"]), (405, "POST"))

    def test_head(self) -> None:
        status, hdrs, data = self.req("HEAD", "/app.css")
        self.assertEqual((status, data, hdrs["content-length"]), (200, b"", "6"))
        status, hdrs, data = self.req("HEAD", "/api/health", token=True)
        self.assertEqual((status, data), (200, b""))
        self.assertGreater(int(hdrs["content-length"]), 0)


class PostTest(ServerCase):
    def test_post_ok(self) -> None:
        status, _, data = self.post('{"a": "ư"}'.encode("utf-8"), "application/json; charset=utf-8")
        self.assertEqual((status, json.loads(data)), (200, {"got": {"a": "ư"}}))
        status, _, _ = self.post(b"{}", extra=[("Sec-Fetch-Site", "same-origin")])
        self.assertEqual(status, 200)

    def test_post_needs_token_first(self) -> None:
        resp = self.req("POST", "/api/echo", [("Content-Type", "text/plain"), ("Content-Length", "2")], b"{}")
        self.assertError(resp, 401)

    def test_content_type(self) -> None:
        self.assertError(self.post(b"{}", "text/plain"), 415)
        self.assertError(self.post(b"{}", "application/jsonx"), 415)
        resp = self.req("POST", "/api/echo", [("Content-Length", "2")], b"{}", token=True)
        self.assertError(resp, 415)

    def test_length(self) -> None:
        def send(headers: List[Tuple[str, str]], body: Optional[bytes] = None) -> Resp:
            return self.req("POST", "/api/echo", [("Content-Type", "application/json")] + headers, body, token=True)

        self.assertError(send([("Content-Length", str(server.MAX_BODY + 1))]), 413)
        self.assertError(send([]), 413)
        self.assertError(send([("Content-Length", "abc")]), 413)
        self.assertError(send([("Content-Length", "-1")]), 413)
        self.assertError(send([("Content-Length", "²")]), 413)
        self.assertError(send([("Content-Length", "2"), ("Content-Length", "2")], b"{}"), 413)
        self.assertError(send([("Transfer-Encoding", "chunked")], b"2\r\n{}\r\n0\r\n\r\n"), 413)
        big = b'{"x": "' + b"a" * (server.MAX_BODY - 9) + b'"}'
        self.assertEqual(len(big), server.MAX_BODY)
        self.assertEqual(send([("Content-Length", str(len(big)))], big)[0], 200)

    def test_sec_fetch_site(self) -> None:
        for site in ("cross-site", "same-site", "none"):
            with self.subTest(site=site):
                self.assertError(self.post(b"{}", extra=[("Sec-Fetch-Site", site)]), 403)

    def test_body_must_be_json_object(self) -> None:
        for body in (b"not json", b"[1]", b"null", b"\xff\xfe{}", b"[" * 30000 + b"]" * 30000, b""):
            with self.subTest(body=body[:10]):
                self.assertError(self.post(body), 400)

    def test_keep_alive_and_close(self) -> None:
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        try:
            ok = [("Content-Type", "application/json"), ("Content-Length", "2")]
            self.assertEqual(self.req("POST", "/api/echo", ok, b"{}", token=True, conn=conn)[0], 200)
            status, hdrs, _ = self.req("GET", "/app.css", conn=conn)
            self.assertEqual(status, 200)
            self.assertNotIn("connection", hdrs)
            # Thân chưa đọc (lỗi trước khi đọc) → đóng kết nối, không để thân bị hiểu là request kế.
            status, hdrs, _ = self.req("POST", "/app.css", [("Content-Length", "2")], b"{}", conn=conn)
            self.assertEqual((status, hdrs.get("connection")), (405, "close"))
        finally:
            conn.close()


class RouteTest(ServerCase):
    def test_query_and_ctx(self) -> None:
        status, _, data = self.req("GET", "/api/q?a=1&a=2&b=&c=%C6%B0#frag", token=True)
        self.assertEqual(status, 200)
        self.assertEqual(
            json.loads(data),
            {
                "query": {"a": ["1", "2"], "b": [""], "c": ["ư"]},
                "xt": "XT",
                "base": "proj",
                "fw": "framework",
                "body": None,
            },
        )

    def test_handler_status_passthrough(self) -> None:
        self.assertEqual(
            self.assertError(self.req("GET", "/api/nf", token=True), 404), {"error": "không có tài nguyên"}
        )

    def test_handler_exception_is_500(self) -> None:
        err = io.StringIO()
        with redirect_stderr(err):
            boom = self.req("GET", "/api/boom", token=True)
            bad = self.req("GET", "/api/bad", token=True)
        self.assertEqual(self.assertError(boom, 500), {"error": "lỗi máy chủ"})
        self.assertEqual(self.assertError(bad, 500), {"error": "lỗi máy chủ"})
        self.assertIn("RuntimeError", err.getvalue())
        self.assertNotIn(TOKEN, err.getvalue())

    def test_concurrent_requests(self) -> None:
        results: List[int] = []
        lock = threading.Lock()

        def call() -> None:
            status = self.req("GET", "/api/barrier", token=True)[0]
            with lock:
                results.append(status)

        threads = [threading.Thread(target=call) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(10)
        self.assertEqual(results, [200] * 4)


class RawProtocolTest(ServerCase):
    def parse(self, raw: bytes) -> Tuple[int, Dict[str, str], bytes]:
        head, _, body = raw.partition(b"\r\n\r\n")
        lines = head.decode("latin-1").split("\r\n")
        hdrs = {k.lower(): v.strip() for k, _, v in (line.partition(":") for line in lines[1:])}
        self.check_common("", hdrs)
        return int(lines[0].split()[1]), hdrs, body

    def test_garbage_request_line(self) -> None:
        status, hdrs, body = self.parse(self.raw(b"GARBAGE\r\n\r\n"))
        self.assertEqual(status, 400)
        self.assertEqual(hdrs["connection"], "close")
        self.assertEqual(json.loads(body), {"error": "yêu cầu không hợp lệ"})

    def test_http09_request_still_gets_headers(self) -> None:
        status, hdrs, _ = self.parse(self.raw(b"GET /\r\n\r\n"))
        self.assertEqual((status, hdrs["connection"]), (400, "close"))
        status, _, _ = self.parse(self.raw(b"POST /api/echo\r\n\r\n"))
        self.assertEqual(status, 400)

    def test_request_line_too_long(self) -> None:
        status, _, _ = self.parse(self.raw(b"GET /" + b"a" * 70000 + b" HTTP/1.1\r\n\r\n"))
        self.assertEqual(status, 414)

    def test_slow_body_times_out(self) -> None:
        self.srv.request_timeout = 0.3
        self.srv.quiet = False
        err = io.StringIO()
        req = (
            f"POST /api/echo HTTP/1.1\r\nHost: {self.host()}\r\nX-XT-Token: {TOKEN}\r\n"
            "Content-Type: application/json\r\nContent-Length: 50\r\n\r\n{"
        ).encode()
        with redirect_stderr(err):
            started = time.monotonic()
            self.assertEqual(self.raw(req), b"")
        self.assertLess(time.monotonic() - started, 5)
        self.assertIn("timed out", err.getvalue())
        self.assertNotIn(TOKEN, err.getvalue())


class LogTest(ServerCase):
    def test_log_has_no_token_query_or_control_chars(self) -> None:
        self.srv.quiet = False
        err = io.StringIO()
        with redirect_stderr(err):
            self.req("GET", "/api/health?secret=1#x", token=True)
            self.req("GET", "/api/health")
            self.raw(f"GET /a\x7fb HTTP/1.1\r\nHost: {self.host()}\r\nConnection: close\r\n\r\n".encode("latin-1"))
            self.raw(b"GARBAGE\r\n\r\n")
        log = err.getvalue()
        self.assertIn("GET /api/health 200", log)
        self.assertIn("GET /api/health 401", log)
        self.assertIn("GET /a?b 404", log)
        self.assertIn("- ", log)
        self.assertNotIn(TOKEN, log)
        self.assertNotIn("secret", log)
        self.assertNotIn("X-XT-Token", log)

    def test_quiet(self) -> None:
        err = io.StringIO()
        with redirect_stderr(err):
            self.req("GET", "/")
        self.assertEqual(err.getvalue(), "")


class HealthVersionTest(unittest.TestCase):
    def ctx(self, base: Path, fw: Path) -> server.Ctx:
        return server.Ctx(None, base, fw, {}, None)

    def test_versions(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            base = Path(d) / "dich"
            fw = base / ".xtemplates" / "framework"
            fw.mkdir(parents=True)
            self.assertEqual(
                server._health(self.ctx(base, fw)), (200, {"ok": True, "version": None, "project": "dich"})
            )
            (base / ".xtemplates" / "VERSION").write_text("1.2.3\n", encoding="utf-8")
            self.assertEqual(server._health(self.ctx(base, fw))[1]["version"], "1.2.3")
            # Repo khung: framework/ cạnh VERSION; không có VERSION ở đó → rơi về .xtemplates/VERSION.
            fw2 = base / "framework"
            fw2.mkdir()
            self.assertEqual(server._health(self.ctx(base, fw2))[1]["version"], "1.2.3")
            (base / "VERSION").write_text("4.5.6", encoding="utf-8")
            self.assertEqual(server._health(self.ctx(base, fw2))[1]["version"], "4.5.6")


class StaticTableTest(unittest.TestCase):
    def test_missing_root_and_symlink_root(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(server.static_table(Path(d) / "khong-co"), {})
            real = Path(d) / "real"
            real.mkdir()
            (real / "app.css").write_text("x", encoding="utf-8")
            (Path(d) / "link").symlink_to(real, target_is_directory=True)
            self.assertEqual(server.static_table(Path(d) / "link"), {})
            (Path(d) / "file.css").write_text("x", encoding="utf-8")
            self.assertEqual(server.static_table(Path(d) / "file.css"), {})

    def test_table_contents(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "s"
            (root / "img").mkdir(parents=True)
            for name in ("a.json", "img/b.svg", "img/c.png", "f.woff2", "UP.CSS", "x.py", ".hidden"):
                (root / name).write_bytes(b"1")
            table = server.static_table(root)
            self.assertNotIn("/", table)
            self.assertEqual(
                {k: v[1] for k, v in table.items()},
                {
                    "/a.json": "application/json",
                    "/img/b.svg": "image/svg+xml",
                    "/img/c.png": "image/png",
                    "/f.woff2": "font/woff2",
                    "/UP.CSS": "text/css; charset=utf-8",
                },
            )

    def test_read_regular_refuses_symlink_and_missing(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / "t.js"
            target.write_text("x", encoding="utf-8")
            link = Path(d) / "l.js"
            link.symlink_to(target)
            self.assertIsNone(server._read_regular(str(link)))
            self.assertIsNone(server._read_regular(str(Path(d) / "khong-co")))
            self.assertEqual(server._read_regular(str(target)), b"x")


class MakeServerTest(unittest.TestCase):
    def test_default_token_and_routes(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            srv, token = server.make_server(None, Path(d), Path(d) / "framework", Path(d) / "khong-co")
            srv2, token2 = server.make_server(None, Path(d), Path(d) / "framework", Path(d) / "khong-co")
            try:
                self.assertGreaterEqual(len(token), 43)
                self.assertNotEqual(token, token2)
                self.assertIn(("GET", "/api/health"), srv.routes)
                self.assertEqual(srv.server_address[0], "127.0.0.1")
                self.assertNotEqual(srv.server_address[1], 0)
            finally:
                srv.server_close()
                srv2.server_close()

    def test_empty_token_rejected(self) -> None:
        with self.assertRaises(ValueError):
            server.make_server(None, Path("."), Path("."), Path("khong-co"), token="")


class LoadRoutesTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        sys.path.insert(0, str(self.tmp))

    def tearDown(self) -> None:
        sys.path.remove(str(self.tmp))
        for name in list(sys.modules):
            if name.split(".")[0] in ("pkgok", "pkgdup", "pkghealth", "notpkg"):
                del sys.modules[name]
        self._tmp.cleanup()

    def make_pkg(self, name: str, modules: Dict[str, str]) -> None:
        pkg = self.tmp / name
        pkg.mkdir()
        (pkg / "__init__.py").write_text("", encoding="utf-8")
        for mod, src in modules.items():
            (pkg / f"{mod}.py").write_text(src, encoding="utf-8")

    def test_real_package(self) -> None:
        routes = server.load_routes()
        self.assertIs(routes[("GET", "/api/health")], server.ROUTES[("GET", "/api/health")])

    def test_fake_package(self) -> None:
        route = "def h(ctx):\n    return 200, {}\nROUTES = {('GET', '/api/x'): h}\n"
        self.make_pkg(
            "pkgok",
            {
                "api_a": route,
                "api_none": "X = 1\n",
                "api_empty": "ROUTES = {}\n",
                "other": "ROUTES = {('GET', '/api/health'): None}\n",
            },
        )
        routes = server.load_routes("pkgok")
        self.assertEqual(sorted(routes), [("GET", "/api/health"), ("GET", "/api/x")])

    def test_duplicate_key(self) -> None:
        route = "ROUTES = {('GET', '/api/x'): print}\n"
        self.make_pkg("pkgdup", {"api_a": route, "api_b": route})
        with self.assertRaisesRegex(ValueError, "GET /api/x"):
            server.load_routes("pkgdup")
        self.make_pkg("pkghealth", {"api_h": "ROUTES = {('GET', '/api/health'): print}\n"})
        with self.assertRaisesRegex(ValueError, "/api/health"):
            server.load_routes("pkghealth")

    def test_plain_module(self) -> None:
        (self.tmp / "notpkg.py").write_text("", encoding="utf-8")
        self.assertEqual(sorted(server.load_routes("notpkg")), [("GET", "/api/health")])


if __name__ == "__main__":
    unittest.main()


class SmokeAndErrorTest(unittest.TestCase):
    """`SMOKE` của module api gom vào `srv.smoke` (SPEC-app §2.4); client đóng kết nối không in traceback."""

    def test_load_smoke_and_make_server(self) -> None:
        self.assertEqual(server.load_smoke().get("/api/catalog/module"), "rel=00-method/conventions")
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            real, _ = server.make_server(None, base, base, base)
            injected, _ = server.make_server(None, base, base, base, routes=dict(server.ROUTES))
            try:
                self.assertIn("/api/catalog/module", real.smoke)
                self.assertEqual(injected.smoke, {})
            finally:
                real.server_close()
                injected.server_close()

    def test_handle_error_silences_disconnect_only(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            srv, _ = server.make_server(None, Path(td), Path(td), Path(td), routes={})
            try:
                for exc, printed in (
                    (ConnectionResetError(), False),
                    (BrokenPipeError(), False),
                    (ValueError("x"), True),
                ):
                    err = io.StringIO()
                    with self.subTest(exc=type(exc).__name__), redirect_stderr(err):
                        try:
                            raise exc
                        except Exception:
                            srv.handle_error(None, ("127.0.0.1", 0))
                    self.assertEqual("ValueError" in err.getvalue(), printed)
            finally:
                srv.server_close()
