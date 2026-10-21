"""Test scripts/xt_app/api_plan.py — GET /api/plans, /api/plan (SPEC-app §3, T-1951)."""

from __future__ import annotations

import http.client
import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import xt
from xt_app import api_plan, server

PLAN = """# PLAN

## Lát 1
- [x] `T-001` xong (files: a/x.py)
- [ ] `T-002` mở A — Gate: `true` (sau: T-001; files: src/a.py)
- [ ] `T-003` mở B (exec: deep) (sau: T-001; files: src/b.py)
- [ ] `T-004` giao với B (files: src/b.py)
- [~] `T-005` bỏ

### Lát 2
- [ ] `T-006` vòng (sau: T-007; files: c)
- [ ] `T-007` vòng (sau: T-006; files: d)
- [ ] `T-008` lạ (sau: T-099; files: e)
- [ ] `T-009` hỏng (sau T-001) (files: f)
- [ ] `T-010` bị defer (files: g)
"""
NOSEC = "- [ ] `T-020` không mục\n"


def ctx_for(base: Path, query: Optional[Dict[str, List[str]]] = None) -> server.Ctx:
    return server.Ctx(xt, base=base, framework=ROOT / "framework", query=query or {}, body=None)


class PlanApiTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def put(self, rel: str, text: str) -> None:
        p = self.base / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    def state(self, st: Any) -> None:
        self.put(".autopilot/state.json", json.dumps(st))

    def plans(self) -> Any:
        return api_plan.ROUTES[("GET", "/api/plans")](ctx_for(self.base))

    def plan(self, **q: str) -> Any:
        return api_plan.ROUTES[("GET", "/api/plan")](ctx_for(self.base, {k: [v] for k, v in q.items()}))

    def test_plans_counts_sorted_active(self) -> None:
        self.put("docs/autopilot/PLAN-b.md", PLAN)
        self.put("docs/autopilot/PLAN.md", "- [x] `T-001` a\n- [~] `T-002` b\n")
        self.put("docs/autopilot/NOTES.md", PLAN)
        self.state({"plan": "docs/autopilot/PLAN-b.md"})
        code, body = self.plans()
        self.assertEqual(code, 200)
        self.assertEqual([p["path"] for p in body["plans"]], ["docs/autopilot/PLAN-b.md", "docs/autopilot/PLAN.md"])
        first, second = body["plans"]
        self.assertEqual((first["open"], first["done"], first["dropped"], first["active"]), (8, 1, 1, True))
        self.assertEqual((second["open"], second["done"], second["dropped"], second["active"]), (0, 1, 1, False))

    def test_plans_no_loop_no_dir_unreadable_and_dirs(self) -> None:
        self.assertEqual(self.plans(), (200, {"plans": []}))
        self.put("docs/autopilot/PLAN-bad.md", "")
        (self.base / "docs/autopilot/PLAN-bad.md").write_bytes(b"\xff\xfe- [ ] `T-001`")
        (self.base / "docs/autopilot/PLAN-dir.md").mkdir()
        self.put("docs/autopilot/PLAN-ok.md", "- [ ] `T-001` a\n")
        code, body = self.plans()
        self.assertEqual([(p["path"], p["active"]) for p in body["plans"]], [("docs/autopilot/PLAN-ok.md", False)])

    def test_plans_skip_symlink_outside(self) -> None:
        with tempfile.TemporaryDirectory() as other:
            out = Path(other) / "PLAN-x.md"
            out.write_text("- [ ] `T-001` a\n", encoding="utf-8")
            (self.base / "docs/autopilot").mkdir(parents=True)
            (self.base / "docs/autopilot/PLAN-x.md").symlink_to(out)
            self.assertEqual(self.plans(), (200, {"plans": []}))

    def test_plan_full(self) -> None:
        self.put("docs/autopilot/PLAN.md", PLAN + NOSEC.replace("T-020", "T-011"))
        self.state({"plan": "docs/autopilot/PLAN.md", "deferred": {"T-010": {"reason": "cần khoá", "at": "t"}}})
        code, body = self.plan(path="docs/autopilot/PLAN.md", max="2")
        self.assertEqual(code, 200)
        self.assertEqual(body["path"], "docs/autopilot/PLAN.md")
        self.assertEqual([s["title"] for s in body["sections"]], ["Lát 1", "Lát 2"])
        t3 = body["sections"][0]["tasks"][2]
        self.assertEqual(
            t3,
            {
                "id": "T-003",
                "state": " ",
                "title": t3["title"],
                "gate": None,
                "after": ["T-001"],
                "files": ["src/b.py"],
                "tier": "deep",
            },
        )
        self.assertEqual(body["sections"][0]["tasks"][1]["gate"], "true")
        tasks = xt.parse_plan(self.base / "docs/autopilot/PLAN.md")
        exp = xt.plan_waves(tasks, {"T-010": {"reason": "cần khoá"}}, 2)
        self.assertEqual((body["waves"], body["blocked"]), (exp["waves"], exp["blocked"]))
        self.assertEqual(body["cycles"], ["T-006", "T-007"])
        self.assertEqual(body["unknown_after"], {"T-008": ["T-099"]})
        self.assertEqual(list(body["bad_links"]), ["T-009"])
        self.assertEqual(body["deferred"], {"T-010": "cần khoá"})
        self.assertEqual(body["overlaps"], [{"tasks": ["T-003", "T-004"], "files": ["src/b.py"]}])
        json.dumps(body)

    def test_plan_deferred_plain_string_and_bad_state(self) -> None:
        self.put("p.md", "- [ ] `T-001` a (files: x)\n")
        self.state({"deferred": {"T-001": "lý do"}})
        self.assertEqual(self.plan(path="p.md")[1]["deferred"], {"T-001": "lý do"})
        self.state([1, 2])
        self.assertEqual(self.plan(path="p.md")[1]["deferred"], {})

    def test_plan_section_none(self) -> None:
        self.put("p.md", NOSEC + "## S\n- [ ] `T-021` b\n")
        secs = self.plan(path="p.md")[1]["sections"]
        self.assertEqual([s["title"] for s in secs], [None, "S"])
        self.put("q.md", NOSEC + "## S\n- [ ] `T-021` b\n" + NOSEC.replace("020", "022"))
        secs = self.plan(path="q.md")[1]["sections"]
        self.assertEqual([len(s["tasks"]) for s in secs], [1, 2])

    def test_plan_path_errors(self) -> None:
        self.put("p.md", "- [ ] `T-001` a\n")
        self.put("n.txt", "x")
        for bad in ("/etc/passwd.md", "../x.md", "a/../p.md", "p.txt", "a\\b.md", "a\x00.md", "n.txt"):
            self.assertEqual(self.plan(path=bad)[0], 400, bad)
        with tempfile.TemporaryDirectory() as other:
            (Path(other) / "o.md").write_text("- [ ] `T-001` a\n", encoding="utf-8")
            (self.base / "link.md").symlink_to(Path(other) / "o.md")
            self.assertEqual(self.plan(path="link.md")[0], 400)
        self.assertEqual(self.plan(path="")[0], 400)
        self.assertEqual(self.plan(path="none.md")[0], 404)
        (self.base / "d.md").mkdir()
        self.assertEqual(self.plan(path="d.md")[0], 404)
        (self.base / "bin.md").write_bytes(b"\xff\xfe")
        self.assertEqual(self.plan(path="bin.md")[0], 404)

    def test_plan_max_errors(self) -> None:
        self.put("p.md", "- [ ] `T-001` a\n")
        for bad in ("0", "11", "x", "", "-1", "٣", "1.5"):
            self.assertEqual(self.plan(path="p.md", max=bad)[0], 400, bad)
        for good in ("1", "10"):
            self.assertEqual(self.plan(path="p.md", max=good)[0], 200, good)

    def test_plan_default_active_then_plan_md_then_empty(self) -> None:
        empty = {
            "path": None,
            "sections": [],
            "waves": [],
            "blocked": [],
            "overlaps": [],
            "cycles": [],
            "unknown_after": {},
            "bad_links": {},
            "deferred": {},
        }
        self.assertEqual(self.plan(), (200, empty))
        self.state({"plan": "docs/autopilot/PLAN-x.md"})  # state trỏ file không có
        self.assertEqual(self.plan(), (200, empty))
        self.put("docs/autopilot/PLAN.md", "- [ ] `T-001` a\n")
        self.assertEqual(self.plan()[1]["path"], "docs/autopilot/PLAN.md")
        self.put("docs/autopilot/PLAN-x.md", "- [ ] `T-002` b\n")
        self.assertEqual(self.plan()[1]["path"], "docs/autopilot/PLAN-x.md")
        self.state({"plan": "../evil.md"})
        self.assertEqual(self.plan()[1]["path"], "docs/autopilot/PLAN.md")
        self.state({"plan": 7})
        self.assertEqual(self.plan()[1]["path"], "docs/autopilot/PLAN.md")

    def test_default_plan_symlink_outside_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as other:
            (Path(other) / "o.md").write_text("- [ ] `T-001` a\n", encoding="utf-8")
            (self.base / "docs/autopilot").mkdir(parents=True)
            (self.base / "docs/autopilot/PLAN.md").symlink_to(Path(other) / "o.md")
            self.assertIsNone(self.plan()[1]["path"])

    def test_no_smoke(self) -> None:
        self.assertFalse(hasattr(api_plan, "SMOKE"))

    def test_http_end_to_end(self) -> None:
        self.put("docs/autopilot/PLAN.md", PLAN)
        srv, token = server.make_server(
            xt,
            self.base,
            ROOT / "framework",
            static_root=self.base,
            routes={**server.ROUTES, **api_plan.ROUTES},
        )
        srv.quiet = True
        port = srv.server_address[1]
        thread = threading.Thread(target=srv.serve_forever, args=(0.02,), daemon=True)
        thread.start()
        try:
            out = []
            for target in ("/api/plans", "/api/plan?path=docs/autopilot/PLAN.md&max=3"):
                conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
                conn.request("GET", target, headers={"Host": f"127.0.0.1:{port}", "X-XT-Token": token})
                resp = conn.getresponse()
                out.append((resp.status, json.loads(resp.read())))
                conn.close()
        finally:
            srv.shutdown()
            srv.server_close()
            thread.join(5)
        self.assertEqual(out[0][0], 200)
        self.assertEqual(out[0][1]["plans"][0]["open"], 8)
        self.assertEqual(out[1][0], 200)
        self.assertEqual(out[1][1]["sections"][0]["title"], "Lát 1")


if __name__ == "__main__":
    unittest.main()
