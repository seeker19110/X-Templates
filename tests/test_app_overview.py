"""Test cho scripts/xt_app/api_overview.py (SPEC-app §3 `GET /api/overview`)."""

from __future__ import annotations

import http.client
import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import xt
from xt_app import api_overview, server

BLUEPRINT = """# Blueprint

- [x] `A-001` **MUST** đã xong
- [ ] `A-002` **MUST** chưa xong
- [~] `A-003` **MUST** bỏ — Miễn: không cần — Duyệt: chủ dự án
- [ ] `A-004` **SHOULD** chưa
"""
PLAN = "## Lát 1\n\n- [x] `T-001` xong\n- [ ] `T-002` mở\n- [ ] `T-003` mở nữa\n"


def call(base: Path) -> Dict[str, Any]:
    ctx = server.Ctx(xt, base=base, framework=base / "framework", query={}, body=None)
    code, body = api_overview.ROUTES[("GET", "/api/overview")](ctx)
    assert code == 200
    return body


def write(base: Path, rel: str, text: str) -> None:
    p = base / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def state(base: Path, **kw: Any) -> None:
    write(base, ".autopilot/state.json", json.dumps({"active": True, **kw}))


class OverviewTest(unittest.TestCase):
    def test_empty_project(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            base = Path(d) / "dự-án"
            base.mkdir()
            got = call(base)
        self.assertEqual(got["project"], "dự-án")
        self.assertIsNone(got["version"])
        self.assertEqual(got["loop"]["verdict"], "inactive")
        self.assertTrue(got["loop"]["reason"])
        self.assertIsNone(got["blueprint"])
        self.assertIsNone(got["plan"])
        self.assertEqual(got["pending_human"], 0)

    def test_full_project(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            write(base, "BLUEPRINT.md", BLUEPRINT)
            write(base, "docs/autopilot/PLAN-x.md", PLAN)
            write(base, ".xtemplates/VERSION", "9.9.9\n")
            state(
                base,
                plan="docs/autopilot/PLAN-x.md",
                deferred={"T-002": {"reason": "cần khoá", "at": "x"}, "T-003": {"reason": "tiền", "at": "y"}},
            )
            got = call(base)
        self.assertEqual(got["version"], "9.9.9")
        self.assertEqual(got["blueprint"], {"must_done": 1, "must_total": 3})
        self.assertEqual(got["plan"], {"path": "docs/autopilot/PLAN-x.md", "open": 2})
        self.assertEqual(got["pending_human"], 2)

    def test_state_plan_missing_falls_back(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            write(base, "docs/autopilot/PLAN.md", PLAN)
            state(base, plan="docs/autopilot/khong-co.md")
            self.assertEqual(call(base)["plan"], {"path": "docs/autopilot/PLAN.md", "open": 2})

    def test_state_plan_unsafe_or_wrong_type(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            base = root / "p"
            write(base, "docs/autopilot/PLAN.md", PLAN)
            write(root, "ngoai.md", PLAN)
            for bad in ("../ngoai.md", str(root / "ngoai.md"), 5, "", None):
                state(base, plan=bad)
                got = call(base)
                self.assertEqual(got["plan"]["path"], "docs/autopilot/PLAN.md", bad)

    def test_deferred_wrong_type_and_bad_plan(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            write(base, "docs/autopilot/PLAN.md", PLAN)
            state(base, deferred=["T-1"])
            self.assertEqual(call(base)["pending_human"], 0)
            (base / "docs/autopilot/PLAN.md").write_bytes(b"\xff\xfe\x00bad")
            self.assertIsNone(call(base)["plan"])

    def test_corrupt_blueprint(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            (base / "BLUEPRINT.md").write_bytes(b"\xff\xfe\xfa not utf8")
            self.assertIsNone(call(base)["blueprint"])

    def test_blueprint_is_directory(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            (base / "BLUEPRINT.md").mkdir()
            self.assertIsNone(call(base)["blueprint"])

    def test_blueprint_unexpected_shape(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            write(base, "BLUEPRINT.md", BLUEPRINT)
            fake = type("X", (), {"blueprint_status": staticmethod(lambda p: {"levels": {}})})
            ctx = server.Ctx(fake, base=base, framework=base, query={}, body=None)
            self.assertIsNone(api_overview._blueprint(ctx))


class OverviewHttpTest(unittest.TestCase):
    def test_http(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            write(base, "BLUEPRINT.md", BLUEPRINT)
            routes = {**server.ROUTES, **api_overview.ROUTES}
            srv, token = server.make_server(xt, base, base / "framework", base / "static", routes=routes)
            srv.quiet = True
            th = threading.Thread(target=srv.serve_forever, daemon=True)
            th.start()
            try:
                host = f"127.0.0.1:{srv.server_address[1]}"
                conn = http.client.HTTPConnection("127.0.0.1", srv.server_address[1], timeout=10)
                conn.putrequest("GET", "/api/overview", skip_host=True)
                conn.putheader("Host", host)
                conn.putheader("X-XT-Token", token)
                conn.endheaders()
                resp = conn.getresponse()
                body = json.loads(resp.read())
                conn.close()
            finally:
                srv.shutdown()
                srv.server_close()
                th.join(5)
        self.assertEqual(resp.status, 200)
        self.assertEqual(body["blueprint"], {"must_done": 1, "must_total": 3})
        self.assertEqual(body["loop"]["verdict"], "inactive")


if __name__ == "__main__":
    unittest.main()
