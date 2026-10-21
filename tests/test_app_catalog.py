"""Test cho scripts/xt_app/api_catalog.py (SPEC-app §3, T-1922)."""

from __future__ import annotations

import http.client
import json
import os
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import xt
from xt_app import api_catalog, server

TOKEN = "t0k3n-for-tests_ABCDEFGHIJKLMNOPQRSTUVWXYZ012"

MOD_A = """---
title: Mô-đun Ánh
kind: module
prefix: AAA
updated: 2026-01-01
---

# A

## Checklist

- [ ] `AAA-001` **MUST** Băm mật khẩu bằng Argon2id. → Kiểm: test đơn vị. · Nguồn: ASVS 5.0 V6
- [ ] `AAA-002` **MUST@L** Nhật ký truy cập. → Kiểm: grep log.
- [ ] `AAA-003` **SHOULD** Chữ thường thôi · Nguồn: RFC 1
- [ ] `AAA-004` **MAY** Tuỳ chọn ĐẶC BIỆT.
"""
README = "---\ntitle: Mảng một\nkind: index\nupdated: 2026-01-01\n---\n\n# R\n"
TOP = "---\ntitle: Gốc\nkind: method\nupdated: 2026-01-01\n---\n\n# Top\n"
BROKEN = "---\nkind: module\n"


def make_fw(tmp: Path) -> Path:
    fw = tmp / "framework"
    (fw / "01-one").mkdir(parents=True)
    (fw / "02-two").mkdir()
    (fw / "01-one" / "README.md").write_text(README, encoding="utf-8")
    (fw / "01-one" / "a.md").write_text(MOD_A, encoding="utf-8")
    (fw / "02-two" / "b.md").write_text(TOP.replace("Gốc", "Bê"), encoding="utf-8")
    (fw / "02-two" / "broken.md").write_text(BROKEN, encoding="utf-8")
    (fw / "top.md").write_text(TOP, encoding="utf-8")
    return fw


def ctx(fw: Path, query: Optional[Dict[str, List[str]]] = None) -> server.Ctx:
    return server.Ctx(xt, base=fw.parent, framework=fw, query=query or {}, body=None)


class CatalogTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.fw = make_fw(Path(self._tmp.name))
        api_catalog._CACHE.clear()

    def test_tree(self) -> None:
        status, body = api_catalog._catalog(ctx(self.fw))
        self.assertEqual(status, 200)
        self.assertNotIn("hits", body)
        dirs = [a["dir"] for a in body["areas"]]
        self.assertEqual(dirs, [".", "01-one", "02-two"])
        one = body["areas"][1]
        self.assertEqual(one["title"], "Mảng một")
        self.assertEqual(body["areas"][2]["title"], "02-two")  # không có README → tên thư mục
        self.assertEqual(
            one["modules"],
            [
                {
                    "rel": "01-one/a",
                    "title": "Mô-đun Ánh",
                    "kind": "module",
                    "prefix": "AAA",
                    "counts": {"MUST": 2, "SHOULD": 1, "MAY": 1},
                }
            ],
        )
        self.assertEqual(body["areas"][0]["modules"][0]["prefix"], "")
        self.assertEqual([m["rel"] for m in body["areas"][2]["modules"]], ["02-two/b"])  # broken.md bị bỏ

    def test_search(self) -> None:
        _, body = api_catalog._catalog(ctx(self.fw, {"q": ["  aaa-00 "]}))
        self.assertEqual([h["id"] for h in body["hits"]], ["AAA-001", "AAA-002", "AAA-003", "AAA-004"])
        self.assertFalse(body["truncated"])
        _, body = api_catalog._catalog(ctx(self.fw, {"q": ["đặc biệt"]}))  # Unicode, không phân biệt hoa thường
        self.assertEqual(
            body["hits"], [{"id": "AAA-004", "level": "MAY", "rel": "01-one/a", "text": "Tuỳ chọn ĐẶC BIỆT."}]
        )
        _, body = api_catalog._catalog(ctx(self.fw, {"q": ["argon2id"]}))
        self.assertEqual(body["hits"][0]["text"], "Băm mật khẩu bằng Argon2id.")
        _, body = api_catalog._catalog(ctx(self.fw, {"q": ["không-có-đâu"]}))
        self.assertEqual((body["hits"], body["truncated"]), ([], False))

    def test_search_short_is_400(self) -> None:
        for q in ("", " a ", "   "):
            status, body = api_catalog._catalog(ctx(self.fw, {"q": [q]}))
            self.assertEqual(status, 400, q)
            self.assertIn("error", body)

    def test_search_truncates(self) -> None:
        lines = "".join(f"- [ ] `AAA-{i:03d}` **MAY** mục số {i}\n" for i in range(1, 251))
        (self.fw / "01-one" / "a.md").write_text(MOD_A.split("- [ ]")[0] + lines, encoding="utf-8")
        _, body = api_catalog._catalog(ctx(self.fw, {"q": ["mục số"]}))
        self.assertEqual((len(body["hits"]), body["truncated"]), (200, True))

    def test_search_exactly_max_not_truncated(self) -> None:
        lines = "".join(f"- [ ] `AAA-{i:03d}` **MAY** mục số {i}\n" for i in range(1, 201))
        (self.fw / "01-one" / "a.md").write_text(MOD_A.split("- [ ]")[0] + lines, encoding="utf-8")
        _, body = api_catalog._catalog(ctx(self.fw, {"q": ["mục số"]}))
        self.assertEqual((len(body["hits"]), body["truncated"]), (200, False))

    def test_module(self) -> None:
        status, body = api_catalog._module_view(ctx(self.fw, {"rel": ["01-one/a"]}))
        self.assertEqual(status, 200)
        self.assertEqual((body["rel"], body["title"], body["kind"]), ("01-one/a", "Mô-đun Ánh", "module"))
        by_id = {i["id"]: i for i in body["items"]}
        self.assertEqual(
            by_id["AAA-001"],
            {
                "id": "AAA-001",
                "level": "MUST",
                "scale": None,
                "text": "Băm mật khẩu bằng Argon2id.",
                "check": "test đơn vị.",
                "source": "ASVS 5.0 V6",
            },
        )
        self.assertEqual((by_id["AAA-002"]["scale"], by_id["AAA-002"]["source"]), ("L", ""))
        self.assertEqual(
            (by_id["AAA-003"]["text"], by_id["AAA-003"]["check"], by_id["AAA-003"]["source"]),
            ("Chữ thường thôi", "", "RFC 1"),
        )
        self.assertEqual(by_id["AAA-004"]["check"], "")

    def test_module_errors(self) -> None:
        self.assertEqual(api_catalog._module_view(ctx(self.fw))[0], 400)
        self.assertEqual(api_catalog._module_view(ctx(self.fw, {"rel": ["  "]}))[0], 400)
        for rel in ("../x", "/etc/passwd", "01-one/../../x", "nope", "01-one/a.md", "01-one/README", "02-two/broken"):
            status, body = api_catalog._module_view(ctx(self.fw, {"rel": [rel]}))
            self.assertEqual(status, 404, rel)
            self.assertIn("error", body)

    def test_cache_reload_on_mtime(self) -> None:
        with mock.patch.object(xt, "load_docs", wraps=xt.load_docs) as spy:
            api_catalog._catalog(ctx(self.fw))
            api_catalog._catalog(ctx(self.fw))
            self.assertEqual(spy.call_count, 1)
            path = self.fw / "01-one" / "a.md"
            path.write_text(MOD_A.replace("Mô-đun Ánh", "Mới"), encoding="utf-8")
            st = path.stat()
            os.utime(path, ns=(st.st_atime_ns, st.st_mtime_ns + 5_000_000_000))
            _, body = api_catalog._catalog(ctx(self.fw))
            self.assertEqual(spy.call_count, 2)
            self.assertEqual(body["areas"][1]["modules"][0]["title"], "Mới")
            (self.fw / "02-two" / "b.md").unlink()  # xoá file: số file đổi → nạp lại
            api_catalog._catalog(ctx(self.fw))
            self.assertEqual(spy.call_count, 3)

    def test_cache_keyed_by_framework(self) -> None:
        other = make_fw(Path(self._tmp.name) / "o")
        with mock.patch.object(xt, "load_docs", wraps=xt.load_docs) as spy:
            api_catalog._catalog(ctx(self.fw))
            api_catalog._catalog(ctx(other))
            self.assertEqual(spy.call_count, 2)

    def test_stat_error_is_ignored(self) -> None:
        real = Path.stat

        def flaky(self: Path, *a: Any, **k: Any) -> os.stat_result:
            if self.name == "a.md":
                raise OSError("biến mất")
            return real(self, *a, **k)

        with mock.patch.object(Path, "stat", flaky):
            self.assertEqual(api_catalog._stamp(self.fw)[1], 5)

    def test_empty_framework(self) -> None:
        empty = Path(self._tmp.name) / "empty"
        empty.mkdir()
        self.assertEqual(api_catalog._catalog(ctx(empty)), (200, {"areas": []}))

    def test_real_framework_size(self) -> None:
        status, body = api_catalog._catalog(ctx(ROOT / "framework"))
        self.assertEqual(status, 200)
        size = len(json.dumps(body, ensure_ascii=False).encode("utf-8"))
        # Đo trên framework thật (2026-10-21): ~37 KB cho cây /api/catalog (không q); trần 300 KB.
        self.assertLess(size, 300 * 1024)
        self.assertGreater(len(body["areas"]), 10)

    def test_http_end_to_end(self) -> None:
        routes = {**server.ROUTES, **api_catalog.ROUTES}
        srv, token = server.make_server(
            xt, self.fw.parent, self.fw, static_root=Path(self._tmp.name), token=TOKEN, routes=routes
        )
        srv.quiet = True
        thread = threading.Thread(target=srv.serve_forever, daemon=True)
        thread.start()
        try:
            host = f"127.0.0.1:{srv.server_address[1]}"
            for target, check in (
                ("/api/catalog?q=argon", lambda b: b["hits"][0]["id"] == "AAA-001"),
                ("/api/catalog/module?rel=01-one/a", lambda b: len(b["items"]) == 4),
            ):
                conn = http.client.HTTPConnection("127.0.0.1", srv.server_address[1], timeout=5)
                conn.putrequest("GET", target, skip_host=True)
                conn.putheader("Host", host)
                conn.putheader("X-XT-Token", token)
                conn.endheaders()
                resp = conn.getresponse()
                self.assertEqual(resp.status, 200)
                self.assertTrue(check(json.loads(resp.read())))
                conn.close()
        finally:
            srv.shutdown()
            srv.server_close()
            thread.join(5)


if __name__ == "__main__":
    unittest.main()
