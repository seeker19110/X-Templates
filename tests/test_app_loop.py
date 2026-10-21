"""Test cho scripts/xt_app/api_loop.py (SPEC-app §3, T-1961)."""

from __future__ import annotations

import http.client
import json
import re
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
from xt_app import api_loop, server

TOKEN = "t0k3n-for-tests_ABCDEFGHIJKLMNOPQRSTUVWXYZ012"

DECISIONS = """# Nhật ký

> mô tả

### D-001 · 2026-10-15T14:17:22+00:00 · Chọn Ánh xạ

- Phương án: (1) Một · (2) Hai · (3) Ba
- Chọn: Hai
- Lý do (tiêu chí chất lượng cuối): Tiêu chí 1: đúng.
- Đường lùi: Quay lại Một
- Khi chạy thật (đề xuất, chủ dự án quyết ở G7): dịch vụ X

### D-002 · 2026-10-16T01:00:00+00:00 · Câu hỏi thứ hai

- Phương án: (1) Alpha
- Chọn: Alpha
- Lý do (tiêu chí chất lượng cuối): ĐẶC BIỆT
- Đường lùi: không

### Không phải quyết định

- Chọn: nhầm

### D-003 · 2026-10-17T01:00:00+00:00 · Mục trống
"""

ADR_OK = "# ADR-0002: Tiêu đề hai\n\n- **Trạng thái:** Đã chấp nhận\n- **Trạng thái triển khai:** chưa\n"
ADR_NO_STATUS = "# ADR-0001: Không trạng thái\n\nnội dung\n"


def ctx(base: Path, query: Optional[Dict[str, List[str]]] = None) -> server.Ctx:
    return server.Ctx(xt, base=base, framework=base, query=query or {}, body=None)


def put_state(base: Path, state: Dict[str, Any]) -> None:
    (base / ".autopilot").mkdir(exist_ok=True)
    (base / ".autopilot" / "state.json").write_text(json.dumps(state), encoding="utf-8")


class LoopTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.base = Path(self._tmp.name)

    def test_no_loop_is_inactive(self) -> None:
        status, body = api_loop._loop(ctx(self.base))
        self.assertEqual(status, 200)
        self.assertEqual(body["verdict"], "inactive")
        self.assertEqual(body["deferred"], [])
        for k in ("iterations", "max_iterations", "deadline", "checkpoint", "stats"):
            self.assertIsNone(body[k], k)

    def test_corrupt_state_file_is_inactive(self) -> None:
        (self.base / ".autopilot").mkdir()
        (self.base / ".autopilot" / "state.json").write_text("{không phải json", encoding="utf-8")
        _, body = api_loop._loop(ctx(self.base))
        self.assertEqual(body["verdict"], "inactive")

    def test_state_with_defer_and_checkpoint(self) -> None:
        cp = {"at": "2026-10-21T00:00:00+00:00", "verdict": "continue"}
        put_state(
            self.base,
            {
                "active": True,
                "started": "S1",
                "iterations": 7,
                "max_iterations": 50,
                "deadline": "2999-01-01T00:00:00+00:00",
                "blocked": True,
                "blocked_reason": "cần người",
                "checkpoint": cp,
                "deferred": {"T-9": {"reason": "cần khoá thật", "at": "2026-10-20"}, "T-8": "hỏng"},
            },
        )
        (self.base / ".autopilot" / "runs.jsonl").write_text(
            json.dumps({"task": "T-9", "exit_code": 0, "loop": "S1"}) + "\n", encoding="utf-8"
        )
        status, body = api_loop._loop(ctx(self.base))
        self.assertEqual(status, 200)
        self.assertEqual((body["verdict"], body["reason"]), ("blocked", "cần người"))
        self.assertEqual((body["iterations"], body["max_iterations"]), (7, 50))
        self.assertEqual(body["deadline"], "2999-01-01T00:00:00+00:00")
        self.assertEqual(body["checkpoint"], cp)
        self.assertEqual(
            body["deferred"],
            [
                {"id": "T-9", "reason": "cần khoá thật", "at": "2026-10-20"},
                {"id": "T-8", "reason": "", "at": ""},
            ],
        )
        self.assertEqual(body["stats"]["runs"], 1)

    def test_active_without_runs_has_null_stats(self) -> None:
        put_state(self.base, {"active": True, "started": "S1", "blocked": True})
        _, body = api_loop._loop(ctx(self.base))
        self.assertIsNone(body["stats"])
        self.assertEqual(body["iterations"], None)

    def test_broken_state_types_give_blocked(self) -> None:
        put_state(self.base, {"active": True, "started": "S1", "iterations": 1, "max_iterations": "x"})
        status, body = api_loop._loop(ctx(self.base))
        self.assertEqual(status, 200)
        self.assertEqual(body["verdict"], "blocked")
        self.assertEqual(body["reason"], "không đọc được trạng thái vòng: TypeError")

    def test_stats_error_and_read_state_error(self) -> None:
        put_state(self.base, {"active": True, "started": "S1", "blocked": True})
        with mock.patch.object(xt, "loop_stats", side_effect=ValueError("x")):
            _, body = api_loop._loop(ctx(self.base))
        self.assertIsNone(body["stats"])
        with mock.patch.object(xt, "read_state", side_effect=OSError("x")):
            _, body = api_loop._loop(ctx(self.base))
        self.assertEqual(body["verdict"], "blocked")
        self.assertEqual(body["deferred"], [])


class DecisionsTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.base = Path(self._tmp.name)

    def write(self, text: str) -> None:
        f = self.base / api_loop.DECISIONS_FILE
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(text, encoding="utf-8")

    def test_missing_file(self) -> None:
        self.assertEqual(api_loop._decisions(ctx(self.base)), (200, {"decisions": [], "truncated": False}))

    def test_undecodable_file(self) -> None:
        f = self.base / api_loop.DECISIONS_FILE
        f.parent.mkdir(parents=True)
        f.write_bytes(b"\xff\xfe\x00bad")
        self.assertEqual(api_loop._decisions(ctx(self.base))[1]["decisions"], [])

    def test_parse_newest_first(self) -> None:
        self.write(DECISIONS)
        status, body = api_loop._decisions(ctx(self.base))
        self.assertEqual(status, 200)
        self.assertFalse(body["truncated"])
        self.assertEqual([d["id"] for d in body["decisions"]], ["D-003", "D-002", "D-001"])
        d1 = body["decisions"][2]
        self.assertEqual(
            d1,
            {
                "id": "D-001",
                "at": "2026-10-15T14:17:22+00:00",
                "question": "Chọn Ánh xạ",
                "options": ["Một", "Hai", "Ba"],
                "choice": "Hai",
                "why": "Tiêu chí 1: đúng.",
                "revert": "Quay lại Một",
            },
        )
        self.assertEqual(body["decisions"][1]["options"], ["Alpha"])
        empty = body["decisions"][0]
        self.assertEqual((empty["options"], empty["choice"], empty["why"], empty["revert"]), ([], "", "", ""))

    def test_filter_q(self) -> None:
        self.write(DECISIONS)

        def ids(q: str) -> List[str]:
            return [d["id"] for d in api_loop._decisions(ctx(self.base, {"q": [q]}))[1]["decisions"]]

        self.assertEqual(ids("đặc biệt"), ["D-002"])  # không phân biệt hoa thường, mọi trường
        self.assertEqual(ids("ÁNH"), ["D-001"])
        self.assertEqual(ids("quay lại"), ["D-001"])
        self.assertEqual(ids("ba"), ["D-001"])  # option
        self.assertEqual(ids("2026-10-17"), ["D-003"])
        self.assertEqual(ids("không-có"), [])
        self.assertEqual(ids("  "), ["D-003", "D-002", "D-001"])
        self.assertEqual(len(api_loop._decisions(ctx(self.base))[1]["decisions"]), 3)

    def test_truncates_at_200(self) -> None:
        for n, truncated in ((200, False), (201, True)):
            self.write("".join(f"### D-{i:03d} · t · câu {i}\n\n- Chọn: x\n\n" for i in range(1, n + 1)))
            _, body = api_loop._decisions(ctx(self.base))
            self.assertEqual((len(body["decisions"]), body["truncated"]), (200, truncated))
            self.assertEqual(body["decisions"][0]["id"], f"D-{n:03d}")

    def test_real_repo_decisions(self) -> None:
        text = (ROOT / api_loop.DECISIONS_FILE).read_text(encoding="utf-8")
        headings = len(re.findall(r"^### D-", text, re.M))
        self.assertGreater(headings, 100)
        _, body = api_loop._decisions(ctx(ROOT))
        self.assertEqual(len(body["decisions"]), min(headings, 200))
        self.assertEqual(body["truncated"], headings > 200)
        self.assertEqual(len(xt.DECISION_ID_RE.findall(text)), headings)
        for d in body["decisions"]:
            self.assertTrue(d["question"] and d["choice"] and d["why"] and d["revert"], d["id"])
            self.assertGreaterEqual(len(d["options"]), 2, d["id"])


class AdrsTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.base = Path(self._tmp.name)

    def test_no_dir(self) -> None:
        self.assertEqual(api_loop._adrs(ctx(self.base)), (200, {"adrs": []}))

    def test_adrs(self) -> None:
        d = self.base / "docs" / "adr"
        d.mkdir(parents=True)
        (d / "0002-hai.md").write_text(ADR_OK, encoding="utf-8")
        (d / "0001-mot.md").write_text(ADR_NO_STATUS, encoding="utf-8")
        (d / "0003-hong.md").write_bytes(b"\xff\xfe")
        (d / "README.md").write_text("# chỉ mục\n", encoding="utf-8")
        (d / "0004-dir.md").mkdir()
        _, body = api_loop._adrs(ctx(self.base))
        self.assertEqual(
            body["adrs"],
            [
                {"number": 1, "title": "Không trạng thái", "status": "", "path": "docs/adr/0001-mot.md"},
                {"number": 2, "title": "Tiêu đề hai", "status": "Đã chấp nhận", "path": "docs/adr/0002-hai.md"},
                {"number": 3, "title": "", "status": "", "path": "docs/adr/0003-hong.md"},
            ],
        )

    def test_real_repo_adrs(self) -> None:
        _, body = api_loop._adrs(ctx(ROOT))
        files = sorted((ROOT / "docs" / "adr").glob("0*.md"))
        self.assertEqual([a["number"] for a in body["adrs"]], [int(f.name[:4]) for f in files])
        self.assertTrue(all(a["title"] and a["status"] for a in body["adrs"]))


class HttpTest(unittest.TestCase):
    def test_http_end_to_end(self) -> None:
        with tempfile.TemporaryDirectory() as t:
            base = Path(t)
            (base / "docs" / "autopilot").mkdir(parents=True)
            (base / "docs" / "autopilot" / "DECISIONS.md").write_text(DECISIONS, encoding="utf-8")
            (base / "docs" / "adr").mkdir()
            (base / "docs" / "adr" / "0002-hai.md").write_text(ADR_OK, encoding="utf-8")
            routes = {**server.ROUTES, **api_loop.ROUTES}
            srv, token = server.make_server(xt, base, base, static_root=base, token=TOKEN, routes=routes)
            srv.quiet = True
            thread = threading.Thread(target=srv.serve_forever, daemon=True)
            thread.start()
            try:
                host = f"127.0.0.1:{srv.server_address[1]}"
                for target, check in (
                    ("/api/loop", lambda b: b["verdict"] == "inactive"),
                    ("/api/decisions?q=alpha", lambda b: [d["id"] for d in b["decisions"]] == ["D-002"]),
                    ("/api/adrs", lambda b: b["adrs"][0]["number"] == 2),
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
