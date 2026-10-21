"""Test scripts/xt_app/api_blueprint.py — GET /api/blueprint (SPEC-app §3, T-1941)."""

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
from xt_app import api_blueprint, server

NOTE = " — Không áp dụng: không có"


def item(i: int, level: str, state: str, text: str = "Việc") -> str:
    return f"- [{state}] `T-ABC-{i:03d}` **{level}** {text}"


class BlueprintApiTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def put(self, name: str, lines: List[str], front: str = "") -> None:
        p = self.base / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(front + "\n".join(lines) + "\n", encoding="utf-8")

    def call(self, path: Optional[str] = None) -> Any:
        query: Dict[str, List[str]] = {} if path is None else {"path": [path]}
        ctx = server.Ctx(xt, base=self.base, framework=ROOT / "framework", query=query, body=None)
        return api_blueprint.ROUTES[("GET", "/api/blueprint")](ctx)

    def test_modules_levels_and_open_must(self) -> None:
        self.put(
            "BLUEPRINT.md",
            [
                "# Blueprint",
                "intro",
                item(1, "MUST", "x"),
                "## Mod Một",
                item(2, "MUST", "x"),
                item(3, "MUST", " ", "Chưa làm Việt Nam"),
                item(4, "MUST", "~", "Miễn" + NOTE),
                item(5, "SHOULD", "x"),
                item(6, "SHOULD", " "),
                item(7, "MAY", " "),
                "### Mod Hai ###",
                item(8, "MUST", " ", "x" * 400),
                "- không phải mục",
            ],
        )
        code, body = self.call()
        self.assertEqual(code, 200)
        self.assertEqual(body["path"], "BLUEPRINT.md")
        self.assertEqual(body["levels"], xt.blueprint_status(self.base / "BLUEPRINT.md")["levels"])
        self.assertEqual(body["levels"]["MUST"], {"open": 2, "done": 2, "waived": 1})
        mods = {m["module"]: m for m in body["modules"]}
        self.assertEqual(
            mods[api_blueprint.NO_MODULE],
            {"module": api_blueprint.NO_MODULE, "must_done": 1, "must_total": 1, "should_done": 0, "should_total": 0},
        )
        self.assertEqual(
            mods["Mod Một"],
            {"module": "Mod Một", "must_done": 2, "must_total": 3, "should_done": 1, "should_total": 2},
        )
        self.assertEqual(mods["Mod Hai"]["must_total"], 1)
        self.assertEqual([m["id"] for m in body["open_must"]], ["T-ABC-003", "T-ABC-008"])
        self.assertEqual(body["open_must"][0], {"id": "T-ABC-003", "module": "Mod Một", "text": "Chưa làm Việt Nam"})
        self.assertEqual(len(body["open_must"][1]["text"]), api_blueprint.MAX_TEXT)
        self.assertFalse(body["truncated"])
        self.assertEqual(body["bad_lines"], [])

    def test_truncated_over_200(self) -> None:
        self.put("BLUEPRINT.md", ["## M"] + [item(i, "MUST", " ") for i in range(1, 206)])
        code, body = self.call()
        self.assertEqual(code, 200)
        self.assertEqual(len(body["open_must"]), 200)
        self.assertTrue(body["truncated"])
        self.assertEqual(body["levels"]["MUST"]["open"], 205)

    def test_exactly_200_not_truncated(self) -> None:
        self.put("BLUEPRINT.md", [item(i, "MUST", " ") for i in range(1, 201)])
        _, body = self.call()
        self.assertEqual(len(body["open_must"]), 200)
        self.assertFalse(body["truncated"])

    def test_empty_file(self) -> None:
        self.put("BLUEPRINT.md", [])
        code, body = self.call()
        self.assertEqual(code, 200)
        self.assertEqual((body["modules"], body["open_must"], body["truncated"]), ([], [], False))

    def test_backlog_merged_and_missing(self) -> None:
        self.put("BLUEPRINT.md", ["## A", item(1, "MUST", "x")], front="---\nbacklog: BACKLOG.md\n---\n")
        code, body = self.call()
        self.assertEqual(code, 200)
        self.assertTrue(any("BACKLOG.md" in b for b in body["bad_lines"]))
        self.put("BACKLOG.md", ["## B", item(2, "SHOULD", " "), item(3, "MUST", " ")])
        _, body = self.call()
        self.assertEqual(body["bad_lines"], [])
        mods = {m["module"]: m for m in body["modules"]}
        self.assertEqual(mods["B"]["should_total"], 1)
        self.assertEqual([m["id"] for m in body["open_must"]], ["T-ABC-003"])
        self.assertEqual(body["levels"]["SHOULD"]["open"], 1)

    def test_bad_line_reported(self) -> None:
        self.put("BLUEPRINT.md", ["## A", "- [-] `T-ABC-001` **MUST** hỏng"])
        _, body = self.call()
        self.assertEqual(len(body["bad_lines"]), 1)

    def test_check_cmd_variants(self) -> None:
        self.put("docs/BP.md", [item(1, "MUST", "x")])
        _, body = self.call("docs/BP.md")
        self.assertEqual(body["check_cmd"], "python3 .xtemplates/scripts/xt.py blueprint-status docs/BP.md --strict")
        (self.base / "scripts").mkdir()
        (self.base / "scripts" / "xt.py").write_text("", encoding="utf-8")
        _, body = self.call("docs/BP.md")
        self.assertEqual(body["check_cmd"], "python3 scripts/xt.py blueprint-status docs/BP.md --strict")

    def test_bad_paths(self) -> None:
        self.put("BLUEPRINT.md", [item(1, "MUST", "x")])
        self.put("a.txt", ["x"])
        for p in ("../x.md", "/etc/x.md", "a.txt", "a/../../x.md", "a\\b.md", "x\x00.md", "BLUEPRINT", ""):
            with self.subTest(p=p):
                code, body = self.call(p)
                self.assertEqual(code, 400)
                self.assertIn("error", body)

    def test_symlink_outside_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as other:
            out = Path(other) / "out.md"
            out.write_text(item(1, "MUST", "x") + "\n", encoding="utf-8")
            (self.base / "link.md").symlink_to(out)
            code, _ = self.call("link.md")
        self.assertEqual(code, 400)

    def test_backlog_outside_rejected(self) -> None:
        self.put("BLUEPRINT.md", [item(1, "MUST", "x")], front="---\nbacklog: ../../etc/passwd\n---\n")
        code, body = self.call()
        self.assertEqual(code, 400)
        self.assertIn("backlog", body["error"])

    def test_not_found(self) -> None:
        code, body = self.call()  # vắng path, chưa có BLUEPRINT.md: 200 rỗng (smoke ở dự án mới cài)
        self.assertEqual((code, body["path"], body["modules"], body["check_cmd"]), (200, None, [], None))
        self.assertEqual(self.call("BLUEPRINT.md")[0], 404)
        (self.base / "dir.md").mkdir()
        self.assertEqual(self.call("dir.md")[0], 404)
        self.assertEqual(self.call("sub/none.md")[0], 404)

    def test_non_utf8(self) -> None:
        (self.base / "BLUEPRINT.md").write_bytes(b"\xff\xfe\x00bad")
        code, body = self.call()
        self.assertEqual(code, 400)
        self.assertIn("UTF-8", body["error"])

    def test_http_end_to_end(self) -> None:
        self.put("BLUEPRINT.md", ["## M", item(1, "MUST", " ")])
        srv, token = server.make_server(
            xt, self.base, ROOT / "framework", self.base / "static", routes={**server.ROUTES, **api_blueprint.ROUTES}
        )
        srv.quiet = True
        port = srv.server_address[1]
        thread = threading.Thread(target=srv.serve_forever, args=(0.02,), daemon=True)
        thread.start()
        try:
            conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
            conn.request(
                "GET", "/api/blueprint?path=BLUEPRINT.md", headers={"Host": f"127.0.0.1:{port}", "X-XT-Token": token}
            )
            resp = conn.getresponse()
            data = json.loads(resp.read())
            conn.close()
        finally:
            srv.shutdown()
            srv.server_close()
            thread.join(5)
        self.assertEqual(resp.status, 200)
        self.assertEqual(data["open_must"][0]["id"], "T-ABC-001")


if __name__ == "__main__":
    unittest.main()
