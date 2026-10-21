"""Test cho scripts/xt_app/api_compose.py (SPEC-app §3, T-1931) và `xt.compose_write`."""

from __future__ import annotations

import http.client
import json
import re
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import unittest.mock as mock
from urllib.parse import parse_qs

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import xt
from xt_app import api_compose, server

FW = ROOT / "framework"
TOKEN = "t0k3n-for-tests_ABCDEFGHIJKLMNOPQRSTUVWXYZ012"
ITEM_LINE = re.compile(r"^- \[ \] `([A-Z0-9-]+)` \*\*MUST\*\*", re.M)


def cli(*args: str, cwd: Optional[Path] = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "xt.py"), "--framework", str(FW), *args],
        capture_output=True,
        text=True,
        cwd=cwd,
        check=False,
    )


def ctx(base: Path, query: Optional[Dict[str, List[str]]] = None, body: Optional[Dict[str, Any]] = None) -> server.Ctx:
    return server.Ctx(xt, base=base, framework=FW, query=query or {}, body=body)


def table(markdown: str, level: str) -> int:
    m = re.search(rf"^\| {level} \| (\d+) \|$", markdown, re.M)
    assert m is not None
    return int(m.group(1))


class OptionsTest(unittest.TestCase):
    def _cli_list(self, what: str) -> List[Tuple[str, str]]:
        out = cli("list", what).stdout
        rows = []
        for line in out.splitlines():
            head, _, _rest = line.rpartition("  (")
            key, _, title = head.partition(" ")
            rows.append((key, title.strip()))
        return rows

    def test_options_match_cli_list(self) -> None:
        status, body = api_compose._options(ctx(ROOT))
        self.assertEqual(status, 200)
        self.assertEqual([(p["slug"], p["title"]) for p in body["profiles"]], self._cli_list("profiles"))
        self.assertEqual([(p["slug"], p["title"]) for p in body["industries"]], self._cli_list("industries"))
        self.assertEqual(body["modules"], [k for k, _ in self._cli_list("modules")])
        self.assertEqual(body["features"], list(xt.FEATURE_FACTS))
        self.assertEqual(body["scales"], ["S", "M", "L"])
        self.assertIn("cli-tool", [p["slug"] for p in body["profiles"]])


class ComposeTest(unittest.TestCase):
    def test_counts_match_cli(self) -> None:
        args = ["--profile", "web-app", "--scale", "M", "--industry", "fintech", "--feature", "oauth"]
        args += ["--feature", "pii", "--add", "13-ai-engineering/*"]
        res = cli("compose", *args)
        self.assertEqual(res.returncode, 0, res.stderr)
        q = {"profile": ["web-app"], "scale": ["M"], "industry": ["fintech"], "feature": ["oauth", "pii"]}
        q["add"] = ["13-ai-engineering/*"]
        status, body = api_compose._compose(ctx(ROOT, q))
        self.assertEqual(status, 200, body)
        self.assertEqual(body["markdown"], res.stdout)
        self.assertFalse(body["truncated"])
        self.assertEqual(body["counts"]["MUST"], table(res.stdout, "MUST"))
        self.assertEqual(body["counts"]["SHOULD"], table(res.stdout, "SHOULD"))
        self.assertEqual(body["counts"]["MAY"], 0)  # như CLI mặc định: không --include-may
        self.assertEqual(body["counts"]["MUST"], len(ITEM_LINE.findall(res.stdout)))
        promoted = re.search(r"lên MUST ở quy mô M \(.*?\): (.*)$", res.stderr, re.M)
        self.assertIsNotNone(promoted)
        assert promoted is not None
        self.assertEqual(body["promoted"], promoted.group(1).split(", "))

    def test_smoke_query(self) -> None:
        status, body = api_compose._compose(ctx(ROOT, parse_qs(api_compose.SMOKE["/api/compose"])))
        self.assertEqual(status, 200)
        self.assertGreater(body["counts"]["MUST"], 0)
        self.assertEqual(body["promoted"], [])

    def test_truncate_on_char_boundary(self) -> None:
        with mock.patch.object(api_compose, "MAX_MARKDOWN", 5):
            self.assertEqual(api_compose._truncate("ăăă"), ("ăă", True))  # 6 byte, cắt giữa ký tự thứ 3
            self.assertEqual(api_compose._truncate("ăă"), ("ăă", False))
            self.assertEqual(api_compose._truncate(""), ("", False))

    def test_truncated_preview(self) -> None:
        with mock.patch.object(api_compose, "MAX_MARKDOWN", 1001):
            status, body = api_compose._compose(ctx(ROOT, {"profile": ["cli-tool"], "scale": ["S"]}))
        self.assertEqual(status, 200)
        self.assertTrue(body["truncated"])
        self.assertLessEqual(len(body["markdown"].encode("utf-8")), 1001)
        self.assertGreater(body["counts"]["MUST"], 0)  # đếm trên bản đủ

    def test_bad_params(self) -> None:
        cases: List[Dict[str, List[str]]] = [
            {"scale": ["S"]},
            {"profile": ["cli-tool"]},
            {"profile": ["cli-tool", "web-app"], "scale": ["S"]},
            {"profile": [""], "scale": ["S"]},
            {"profile": ["cli-tool"], "scale": ["X"]},
            {"profile": ["khong-co"], "scale": ["S"]},
            {"profile": ["cli-tool"], "scale": ["S"], "industry": ["khong-co"]},
            {"profile": ["cli-tool"], "scale": ["S"], "add": ["99-khong/co"]},
            {"profile": ["cli-tool"], "scale": ["S"], "add": [""]},
            {"profile": ["cli-tool"], "scale": ["S"], "feature": ["bay"]},
        ]
        for q in cases:
            with self.subTest(q=q):
                status, body = api_compose._compose(ctx(ROOT, q))
                self.assertEqual(status, 400)
                self.assertTrue(body["error"])

    def test_value_error_is_400(self) -> None:
        fake = mock.Mock()
        fake.SCALES = xt.SCALES
        fake.compose_split.side_effect = ValueError("hỏng")
        c = server.Ctx(fake, base=ROOT, framework=FW, query={"profile": ["x"], "scale": ["S"]}, body=None)
        self.assertEqual(api_compose._compose(c), (400, {"error": "hỏng"}))


class BlueprintPostTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.base = self.root / "proj"
        self.base.mkdir()

    def post(self, **body: Any) -> Tuple[int, Dict[str, Any]]:
        return api_compose._blueprint(ctx(self.base, body=body))

    def test_write_matches_cli_and_keeps_ticks(self) -> None:
        status, res = self.post(profile="cli-tool", scale="S", industry=[], add=[], feature=[], out="BLUEPRINT.md")
        self.assertEqual(status, 200, res)
        self.assertEqual(
            res, {"written": ["BLUEPRINT.md", "BLUEPRINT-BACKLOG.md"], "kept": 0, "dropped": 0, "stale": 0}
        )
        cli_dir = self.root / "cli"
        cli_dir.mkdir()
        self.assertEqual(
            cli("compose", "--profile", "cli-tool", "--scale", "S", "--out", "BLUEPRINT.md", cwd=cli_dir).returncode, 0
        )
        for name in ("BLUEPRINT.md", "BLUEPRINT-BACKLOG.md"):
            self.assertEqual((self.base / name).read_bytes(), (cli_dir / name).read_bytes())
        # Tick một mục, đổi chữ một mục đã tick (→ stale), rồi ghép lại.
        bp = self.base / "BLUEPRINT.md"
        text = bp.read_text(encoding="utf-8")
        ids = ITEM_LINE.findall(text)
        first, second = ids[0], ids[1]
        text = text.replace(f"- [ ] `{first}`", f"- [x] `{first}`", 1)
        lines = text.split("\n")
        for i, line in enumerate(lines):
            if line.startswith(f"- [ ] `{second}`"):
                lines[i] = f"- [x] `{second}` **MUST** Yêu cầu cũ đã khác. — Bằng chứng: a.txt"
            elif line.startswith(f"- [x] `{first}`"):
                lines[i] = line + " — Kiểm: `true`"
        bp.write_text("\n".join(lines), encoding="utf-8")
        status, res = self.post(profile="cli-tool", scale="S")
        self.assertEqual(status, 200, res)
        self.assertEqual((res["kept"], res["stale"], res["dropped"]), (1, 1, 0))
        after = bp.read_text(encoding="utf-8")
        self.assertRegex(after, rf"- \[x\] `{first}` .*— Kiểm: `true`")
        self.assertRegex(after, rf"- \[ \] `{second}` .*— Cũ \(rev [0-9a-f]{{8}}, trước đó \[x\]\)")
        # Lần ba cùng tham số: cùng nội dung (idempotent, S-006).
        self.assertEqual(self.post(profile="cli-tool", scale="S")[0], 200)
        self.assertEqual(bp.read_text(encoding="utf-8"), after)

    def test_subdir_out(self) -> None:
        (self.base / "real").mkdir()
        (self.base / "inside").symlink_to(self.base / "real")
        status, res = self.post(profile="cli-tool", scale="S", out="docs/BP.md")
        self.assertEqual((status, res["written"]), (200, ["docs/BP.md", "docs/BP-BACKLOG.md"]))
        status, res = self.post(profile="cli-tool", scale="S", out="inside/./BP.md")
        self.assertEqual((status, res["written"]), (200, ["real/BP.md", "real/BP-BACKLOG.md"]))

    def test_bad_requests_write_nothing(self) -> None:
        outside = self.root / "outside"
        outside.mkdir()
        (outside / "t.md").write_text("ngoài\n", encoding="utf-8")
        (self.base / "lnk.md").symlink_to(outside / "t.md")
        (self.base / "B.md").write_text("", encoding="utf-8")
        (self.base / "B-BACKLOG.md").symlink_to(outside / "t.md")
        (self.base / "dir.md").mkdir()
        (self.base / "out").symlink_to(outside)
        before = sorted(p.name for p in self.base.iterdir())
        ok = {"profile": "cli-tool", "scale": "S"}
        cases: List[Dict[str, Any]] = [
            {**ok, "out": "../x.md"},
            {**ok, "out": "a/../../x.md"},
            {**ok, "out": "/tmp/x.md"},
            {**ok, "out": "x.txt"},
            {**ok, "out": ".hidden.md"},
            {**ok, "out": ".autopilot/x.md"},
            {**ok, "out": "a\\b.md"},
            {**ok, "out": "a\x00.md"},
            {**ok, "out": 5},
            {**ok, "out": "lnk.md"},
            {**ok, "out": "B.md"},
            {**ok, "out": "dir.md"},
            {**ok, "out": "out/x.md"},
            {**ok, "extra": True},
            {**ok, "industry": "fintech"},
            {**ok, "add": [1]},
            {**ok, "feature": [None]},
            {"scale": "S"},
            {"profile": 3, "scale": "S"},
            {"profile": "cli-tool", "scale": "XL"},
            {"profile": "cli-tool"},
            {**ok, "profile": "khong-co"},
            {**ok, "industry": ["khong-co"]},
            {**ok, "add": ["99-x/y"]},
            {**ok, "feature": ["bay"]},
        ]
        for body in cases:
            with self.subTest(body=body):
                status, res = self.post(**body)
                self.assertEqual(status, 400)
                self.assertTrue(res["error"])
        self.assertEqual(sorted(p.name for p in self.base.iterdir()), before)
        self.assertEqual((outside / "t.md").read_text(encoding="utf-8"), "ngoài\n")
        self.assertEqual(sorted(p.name for p in outside.iterdir()), ["t.md"])
        self.assertEqual(api_compose._blueprint(ctx(self.base, body=None))[0], 400)

    def test_concurrent_posts_keep_tick(self) -> None:
        self.assertEqual(self.post(profile="cli-tool", scale="S")[0], 200)
        bp = self.base / "BLUEPRINT.md"
        text = bp.read_text(encoding="utf-8")
        first = ITEM_LINE.findall(text)[0]
        bp.write_text(text.replace(f"- [ ] `{first}`", f"- [x] `{first}`", 1), encoding="utf-8")
        results: List[Tuple[int, Dict[str, Any]]] = []

        def worker() -> None:
            results.append(self.post(profile="cli-tool", scale="S"))

        threads = [threading.Thread(target=worker) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(60)
        self.assertEqual([s for s, _ in results], [200] * 4)
        self.assertEqual({r["kept"] for _, r in results}, {1})
        self.assertIn(f"- [x] `{first}`", bp.read_text(encoding="utf-8"))
        self.assertEqual([p.name for p in self.base.iterdir() if p.name.endswith(".tmp")], [])


class ComposeWriteTest(unittest.TestCase):
    def test_full_and_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "BP.md"
            res = xt.compose_write(FW, "cli-tool", [], "S", False, out, full=True, quiet=True)
            self.assertEqual(res["written"], [out])
            self.assertFalse((Path(tmp) / "BP-BACKLOG.md").exists())
            self.assertEqual((res["kept"], res["dropped"], res["stale"], res["promoted"]), (0, 0, 0, []))


class HttpTest(unittest.TestCase):
    def test_end_to_end(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            routes = {**server.ROUTES, **api_compose.ROUTES}
            srv, token = server.make_server(xt, base, FW, static_root=base, token=TOKEN, routes=routes)
            srv.quiet = True
            thread = threading.Thread(target=srv.serve_forever, daemon=True)
            thread.start()
            try:
                host = f"127.0.0.1:{srv.server_address[1]}"

                def call(method: str, target: str, payload: Optional[Dict[str, Any]] = None) -> Tuple[int, Any]:
                    conn = http.client.HTTPConnection("127.0.0.1", srv.server_address[1], timeout=30)
                    data = json.dumps(payload).encode("utf-8") if payload is not None else None
                    conn.putrequest(method, target, skip_host=True)
                    conn.putheader("Host", host)
                    conn.putheader("X-XT-Token", token)
                    if data is not None:
                        conn.putheader("Content-Type", "application/json")
                        conn.putheader("Content-Length", str(len(data)))
                    conn.endheaders(data)
                    resp = conn.getresponse()
                    out = (resp.status, json.loads(resp.read().decode("utf-8")))
                    conn.close()
                    return out

                status, opts = call("GET", "/api/compose/options")
                self.assertEqual(status, 200)
                self.assertIn("cli-tool", [p["slug"] for p in opts["profiles"]])
                status, prev = call("GET", "/api/compose?" + api_compose.SMOKE["/api/compose"])
                self.assertEqual(status, 200)
                self.assertIn("# Blueprint dự án", prev["markdown"])
                status, res = call(
                    "POST", "/api/blueprint", {"profile": "cli-tool", "scale": "S", "out": "BLUEPRINT.md"}
                )
                self.assertEqual((status, res["written"]), (200, ["BLUEPRINT.md", "BLUEPRINT-BACKLOG.md"]))
                self.assertTrue((base / "BLUEPRINT.md").is_file())
                status, res = call("POST", "/api/blueprint", {"profile": "cli-tool", "scale": "S", "out": "../x.md"})
                self.assertEqual(status, 400)
                self.assertFalse((base.parent / "x.md").exists())
            finally:
                srv.shutdown()
                srv.server_close()
                thread.join(5)


if __name__ == "__main__":
    unittest.main()
