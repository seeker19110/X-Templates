"""Test cho scripts/xt_app/api_pr.py (SPEC-app §3 `GET /api/prs`, `GET /api/pr-stats`) — màn PR CHỈ ĐỌC GitHub
(ADR-0038 §2 "App không chạy lệnh", RK-3 của PLAN-3.14): mọi lời gọi gh là `gh api <đường>` (GET), không ghi sổ review,
không merge, không gắn nhãn, không đăng comment; `scripts/xt_app/` không chạy tiến trình."""

from __future__ import annotations

import datetime as _dt
import http.client
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple
import unittest.mock as mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import xt
from xt_app import api_pr, server

SHA7, SHA8, BASE = "a" * 40, "c" * 40, "b" * 40
NOW = _dt.datetime.now(_dt.timezone.utc)


def iso(days_ago: float) -> str:
    return (NOW - _dt.timedelta(days=days_ago)).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def pr_json(n: int, sha: str, title: str) -> Dict[str, Any]:
    return {
        "number": n,
        "title": title,
        "state": "open",
        "draft": False,
        "mergeable": True,
        "mergeable_state": "clean",
        "changed_files": 1,
        "user": {"login": "dev"},
        "author_association": "OWNER",
        "head": {"sha": sha, "repo": {"full_name": "o/r"}},
        "base": {"ref": "main", "sha": BASE, "repo": {"full_name": "o/r", "default_branch": "main"}},
    }


CLOSED = [
    {"number": 3, "title": "docs: a", "created_at": iso(3), "merged_at": iso(2), "head": {"ref": "x", "sha": "d" * 40}},
    {"number": 2, "title": 'Revert "x"', "created_at": iso(50), "merged_at": iso(40), "head": {"ref": "y"}},
    {"number": 1, "title": "chore: c", "created_at": iso(5), "merged_at": None, "head": {"ref": "z"}},
]
RUNS = {
    "workflow_runs": [
        {"id": 1, "head_branch": "x", "head_sha": "d" * 40, "created_at": iso(2.5), "conclusion": "failure"}
    ]
}


def gh_pages(path: str) -> List[Any]:
    """Trang JSON giả theo đường REST (một lần `gh api`)."""
    table: List[Tuple[str, List[Any]]] = [
        (
            r"/pulls\?state=open",
            [
                [
                    {"number": 7, "title": "docs: sửa", "head": {"sha": SHA7}},
                    {"number": 8, "title": "feat: mã", "head": {"sha": SHA8}},
                    {"number": 9, "title": "lỗi", "head": {}},
                ]
            ],
        ),
        (r"/pulls\?state=closed", [CLOSED]),
        (r"/actions/workflows/ci\.yml/runs\?", [RUNS]),
        (r"/pulls/7$", [pr_json(7, SHA7, "docs: sửa")]),
        (r"/pulls/8$", [pr_json(8, SHA8, "feat: mã")]),
        (r"/pulls/7/files", [[{"filename": "docs/a.md", "additions": 2, "deletions": 0, "status": "modified"}]]),
        (r"/pulls/8/files", [[{"filename": "scripts/a.py", "additions": 5, "deletions": 1, "status": "modified"}]]),
        (
            r"/commits/a+/check-runs",
            [
                {
                    "check_runs": [
                        {"id": 1, "name": "gate", "status": "completed", "conclusion": "success", "app": {"id": 1}}
                    ]
                }
            ],
        ),
        (
            r"/commits/c+/check-runs",
            [
                {
                    "check_runs": [
                        {"id": 2, "name": "gate", "status": "completed", "conclusion": "failure", "app": {"id": 1}}
                    ]
                }
            ],
        ),
        (r"/commits/\w+/status", [{"statuses": []}]),
    ]
    for rx, pages in table:
        if re.search(rx, path.split("&page=")[0].split("?page=")[0]):
            return pages
    if re.search(r"/pulls/9$", path):
        raise xt.PrInputError("gh api pulls/9 lỗi: HTTP 404")
    return [[]]


GH_FORBIDDEN = re.compile(r"(^|\s)(-X|--method|-f|-F|--field|--raw-field|--input)(\s|=|$)")


class GhSpy:
    """Thay `xt._gh_api`: ghi mọi lời gọi, từ chối mọi dấu hiệu không phải GET."""

    def __init__(self, fail: Optional[BaseException] = None) -> None:
        self.calls: List[Tuple[Any, ...]] = []
        self.fail = fail
        self.lock = threading.Lock()

    def __call__(self, *args: Any, **kwargs: Any) -> List[Any]:
        with self.lock:
            self.calls.append((args, kwargs))
        path = args[0]
        assert isinstance(path, str) and not path.startswith("-") and not GH_FORBIDDEN.search(path), path
        assert set(kwargs) <= {"paginate"} and len(args) <= 2, (args, kwargs)
        if self.fail is not None:
            raise self.fail
        return gh_pages(path)


WRITERS = (
    "_write_reviews",
    "write_atomic",
    "_steward_run",
    "_steward_apply",
    "_steward_dispatch_ci",
    "_steward_dispatch_tag",
    "_steward_one",
    "_publish_review",
    "_pr_reviewed",
    "cmd_pr",
    "cmd_pr_steward",
    "cmd_merge_check",
    "cmd_merge_watch",
)
GIT_READ = {"show", "cat-file", "rev-parse", "merge-tree", "ls-files", "log", "diff", "merge-base", "config"}


class ProcSpy:
    """Thay `xt.subprocess.run`: `gh api <đường>` trả JSON giả (chỉ đúng 3 đối số — không cờ ghi); git chỉ lệnh đọc
    (trả 128 = không đọc được → khung tự lùi về cấu hình mặc định); mọi lệnh khác → lỗi."""

    def __init__(self, gh_error: Optional[BaseException] = None) -> None:
        self.cmds: List[List[str]] = []
        self.gh_error = gh_error

    def __call__(self, cmd: List[str], *args: Any, **kwargs: Any) -> "subprocess.CompletedProcess[str]":
        self.cmds.append(list(cmd))
        if cmd[:2] == ["gh", "api"]:
            assert len(cmd) == 3 and not cmd[2].startswith("-"), cmd
            if self.gh_error is not None:
                raise self.gh_error
            try:
                pages = gh_pages(cmd[2])
            except xt.PrInputError as exc:
                return subprocess.CompletedProcess(cmd, 1, "", str(exc))
            return subprocess.CompletedProcess(cmd, 0, "\n".join(json.dumps(p) for p in pages), "")
        if cmd[0] == "git":
            rest = cmd[1:]  # bỏ cờ toàn cục: `--no-replace-objects`, `-c k=v`, `-C dir` (`GIT_SAFE_READ`, AUD-SEC-158)
            while rest and rest[0].startswith("-"):
                rest = rest[2:] if rest[0] in ("-c", "-C") else rest[1:]
            sub = rest[0]
            assert sub in GIT_READ, cmd
            return subprocess.CompletedProcess(cmd, 128, "", "fatal: giả")
        raise AssertionError(f"lệnh lạ: {cmd}")


class Sandbox:
    """Thư mục dự án tạm + vá: CLAUDE_PROJECT_DIR, mọi hàm ghi của xt → mock ném lỗi (ghi lại để assert không gọi)."""

    def __init__(self, gh: Optional[Callable[..., Any]] = None, proc: Optional[ProcSpy] = None) -> None:
        self.gh, self.proc = gh, proc or ProcSpy()
        self.writers: Dict[str, mock.Mock] = {}

    def __enter__(self) -> "Sandbox":
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        (self.base / "xt.yaml").write_text("project: demo\n", encoding="utf-8")
        self._patches: List[Any] = [mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(self.base)})]
        self._patches.append(mock.patch.object(xt.subprocess, "run", self.proc))
        if self.gh is not None:
            self._patches.append(mock.patch.object(xt, "_gh_api", self.gh))
        for name in WRITERS:
            if hasattr(xt, name):
                m = mock.Mock(side_effect=AssertionError(f"app gọi hàm ghi {name}"))
                self.writers[name] = m
                self._patches.append(mock.patch.object(xt, name, m))
        for p in self._patches:
            p.start()
        return self

    def __exit__(self, *exc: Any) -> None:
        for p in reversed(self._patches):
            p.stop()
        self._tmp.cleanup()

    def call(self, path: str, query: Optional[Dict[str, List[str]]] = None) -> Tuple[int, Dict[str, Any]]:
        ctx = server.Ctx(xt, base=self.base, framework=self.base / "framework", query=query or {}, body=None)
        return api_pr.ROUTES[("GET", path)](ctx)

    def assert_no_write(self, tc: unittest.TestCase) -> None:
        for name, m in self.writers.items():
            tc.assertFalse(m.called, name)
        tc.assertFalse((self.base / ".autopilot").exists())


def files_in(base: Path) -> Iterator[str]:
    return (p.relative_to(base).as_posix() for p in sorted(base.rglob("*")))


class PrsTest(unittest.TestCase):
    def test_lists_open_prs_with_pr_next_action(self) -> None:
        spy = GhSpy()
        with Sandbox(gh=spy) as sb:
            before = list(files_in(sb.base))
            code, body = sb.call("/api/prs")
            sb.assert_no_write(self)
            self.assertEqual(list(files_in(sb.base)), before)
        self.assertEqual(code, 200)
        self.assertIs(body["available"], True)
        prs = {p["number"]: p for p in body["prs"]}
        self.assertEqual(sorted(prs), [7, 8, 9])
        for p in prs.values():
            self.assertEqual(set(p), {"number", "title", "head_sha", "lane", "action", "reasons"})
            self.assertTrue(all(isinstance(r, str) for r in p["reasons"]))
        self.assertEqual((prs[7]["title"], prs[7]["head_sha"], prs[7]["lane"]), ("docs: sửa", SHA7, "nhanh"))
        self.assertEqual((prs[8]["head_sha"], prs[8]["lane"], prs[8]["action"]), (SHA8, "chuẩn", "fix"))
        self.assertTrue(prs[8]["reasons"])
        self.assertEqual((prs[9]["action"], prs[9]["lane"], prs[9]["head_sha"]), ("error", "", ""))
        self.assertIn("404", prs[9]["reasons"][0])
        self.assertEqual(prs[7]["action"], "defer-human")  # L1 mặc định: người merge
        self.assertTrue(spy.calls)

    def test_matches_pr_next_without_ledger_write(self) -> None:
        """Hành động = `pr next` của CLI (cùng chuỗi hàm), nhưng `cmd_pr` ghi `standard_seen` vào sổ còn app thì không."""
        with Sandbox(gh=GhSpy()) as sb:
            _, body = sb.call("/api/prs")
            pr = xt._pr_rest("8")
            d, _ = xt._merge_eval(pr)
            want = xt.pr_next(d, False, xt.with_published({"standard_seen": True}, None, False))
            sb.assert_no_write(self)
        row = next(p for p in body["prs"] if p["number"] == 8)
        self.assertEqual(row["action"], want["action"])
        self.assertEqual(row["reasons"][0], want["why"])

    def test_passes_rethink_cap_like_cli(self) -> None:
        """Review #380: màn PR truyền trần `max_rethink` (chặt hơn giữa cây và nhánh đích) như `pr next` — không mặc định."""
        real = xt.pr_next
        with Sandbox(gh=GhSpy()) as sb, mock.patch.object(xt, "pr_rethink_cap", return_value=7) as cap:
            with mock.patch.object(xt, "pr_next", side_effect=real) as spy:
                sb.call("/api/prs")
        self.assertTrue(cap.called)
        self.assertTrue(spy.call_args_list)
        self.assertTrue(all(c.args[3] == 7 for c in spy.call_args_list))

    def test_ledger_is_read_not_written(self) -> None:
        with Sandbox(gh=GhSpy()) as sb:
            led = sb.base / ".autopilot" / "reviews.json"
            led.parent.mkdir()
            led.write_text(json.dumps({"8": {"reviews": "hỏng"}}), encoding="utf-8")
            mtime = led.stat().st_mtime_ns
            code, body = sb.call("/api/prs")
            for m in sb.writers.values():
                self.assertFalse(m.called)
            self.assertEqual(led.stat().st_mtime_ns, mtime)
            self.assertEqual(json.loads(led.read_text(encoding="utf-8")), {"8": {"reviews": "hỏng"}})
        self.assertEqual(code, 200)
        self.assertEqual(len(body["prs"]), 3)

    def test_labelled_standard_and_odd_data(self) -> None:
        """Nhãn `xt-standard-lane` → strict trong bộ nhớ; dòng danh sách thiếu `head`/`title` vẫn không 500."""

        def gh(path: str, paginate: bool = False) -> List[Any]:
            if "state=open" in path:
                return [[{"number": 7}]]
            pages = gh_pages(path)
            if path.endswith("/pulls/7"):
                return [{**pages[0], "labels": [{"name": xt.STANDARD_LABEL}]}]
            return pages

        with Sandbox(gh=gh) as sb:
            code, body = sb.call("/api/prs")
            sb.assert_no_write(self)
        self.assertEqual(code, 200)
        self.assertEqual(body["prs"][0]["title"], "")
        self.assertEqual(body["prs"][0]["head_sha"], SHA7)
        self.assertNotEqual(body["prs"][0]["action"], "error")

    def test_reasons_helper(self) -> None:
        self.assertEqual(api_pr._reasons({"why": ""}, {"reasons": ["a"]}), ["a"])
        self.assertEqual(api_pr._reasons({"why": "a; b"}, {"reasons": ["a", "c"]}), ["a; b", "c"])
        self.assertEqual(api_pr._reasons({}, {}), [])

    def test_unavailable_variants(self) -> None:
        cases: List[BaseException] = [
            xt.PrInputError("không chạy được gh — cài/đăng nhập gh"),
            ValueError("JSON\nhỏng"),
            xt.PrInputError(""),
        ]
        for exc in cases:
            with self.subTest(exc=repr(exc)), Sandbox(gh=GhSpy(fail=exc)) as sb:
                code, body = sb.call("/api/prs")
                sb.assert_no_write(self)
            self.assertEqual(code, 200)
            self.assertEqual(set(body), {"available", "reason"})
            self.assertIs(body["available"], False)
            self.assertNotIn("\n", body["reason"])
            self.assertTrue(body["reason"])

    def test_no_gh_binary_timeout_and_not_logged_in(self) -> None:
        """Đường thật `_gh_api` → `subprocess.run`: không có gh, hết giờ, gh exit ≠ 0 → 200 available false."""
        errs: List[BaseException] = [
            FileNotFoundError(2, "No such file or directory: 'gh'"),
            subprocess.TimeoutExpired(["gh"], 60),
        ]
        for err in errs:
            with self.subTest(err=repr(err)), Sandbox(proc=ProcSpy(gh_error=err)) as sb:
                for path in ("/api/prs", "/api/pr-stats"):
                    code, body = sb.call(path)
                    self.assertEqual((code, body["available"]), (200, False), path)
                    self.assertIn("gh", body["reason"])
                sb.assert_no_write(self)

        def not_logged(cmd: List[str], *a: Any, **k: Any) -> "subprocess.CompletedProcess[str]":
            return subprocess.CompletedProcess(cmd, 4, "", "To get started with GitHub CLI, please run:  gh auth login")

        with Sandbox() as sb, mock.patch.object(xt.subprocess, "run", not_logged):
            code, body = sb.call("/api/prs")
        self.assertEqual((code, body["available"]), (200, False))
        self.assertIn("gh auth login", body["reason"])

    def test_real_gh_argv_is_get_only(self) -> None:
        """Không vá `_gh_api`: mọi argv tới tiến trình là `gh api <đường>` (3 phần tử) hoặc git đọc — không lệnh ghi."""
        proc = ProcSpy()
        with Sandbox(proc=proc) as sb:
            code, body = sb.call("/api/prs")
            code2, body2 = sb.call("/api/pr-stats", {"days": ["30"]})
            sb.assert_no_write(self)
        self.assertEqual((code, code2, body["available"], body2["available"]), (200, 200, True, True))
        gh = [c for c in proc.cmds if c[0] == "gh"]
        self.assertTrue(gh)
        for c in gh:
            self.assertEqual(c[:2], ["gh", "api"])
            self.assertEqual(len(c), 3, c)
        self.assertFalse([c for c in proc.cmds if c[0] not in ("gh", "git")])

    def test_concurrent_requests(self) -> None:
        """ThreadingHTTPServer: hai request song song cho cùng kết quả, không ghi gì."""
        spy = GhSpy()
        out: List[Tuple[int, Dict[str, Any]]] = []
        with Sandbox(gh=spy) as sb:
            ref = sb.call("/api/prs")
            ths = [threading.Thread(target=lambda: out.append(sb.call("/api/prs"))) for _ in range(4)]
            for t in ths:
                t.start()
            for t in ths:
                t.join(30)
            sb.assert_no_write(self)
        self.assertEqual(len(out), 4)
        for got in out:
            self.assertEqual(got, ref)


class PrStatsTest(unittest.TestCase):
    def test_default_days_matches_pr_stats(self) -> None:
        with Sandbox(gh=GhSpy()) as sb:
            code, body = sb.call("/api/pr-stats")
            sb.assert_no_write(self)
        self.assertEqual(code, 200)
        self.assertIs(body.pop("available"), True)
        self.assertEqual(body["days"], 7)
        self.assertEqual(body["merged"], 1)
        self.assertEqual(body["runs_failure"], 1)
        prs, runs = CLOSED, RUNS["workflow_runs"]
        now = _dt.datetime.fromisoformat(body["since"]) + _dt.timedelta(days=7)
        want = xt.pr_stats(prs, runs, now, 7)
        self.assertEqual(set(body), set(want))
        self.assertEqual(body["prs"], want["prs"])

    def test_days_param(self) -> None:
        with Sandbox(gh=GhSpy()) as sb:
            for raw, days in (("1", 1), ("90", 90), (" 45 ", 45)):
                code, body = sb.call("/api/pr-stats", {"days": [raw]})
                self.assertEqual((code, body["days"]), (200, days))
            self.assertEqual(sb.call("/api/pr-stats", {"days": ["90"]})[1]["merged"], 2)
            for bad in ("0", "91", "-1", "abc", "", "7.5", "١٢"):
                code, body = sb.call("/api/pr-stats", {"days": [bad]})
                self.assertEqual(code, 400, bad)
                self.assertIn("days", body["error"])
            sb.assert_no_write(self)

    def test_no_merged_prs(self) -> None:
        def gh(path: str, paginate: bool = False) -> List[Any]:
            return [[]]

        with Sandbox(gh=gh) as sb:
            code, body = sb.call("/api/pr-stats")
        self.assertEqual((code, body["available"], body["merged"], body["runs_seen"]), (200, True, 0, 0))

    def test_unavailable(self) -> None:
        with Sandbox(gh=GhSpy(fail=xt.PrInputError("gh api lỗi: HTTP 401 Bad credentials"))) as sb:
            code, body = sb.call("/api/pr-stats", {"days": ["3"]})
            sb.assert_no_write(self)
        self.assertEqual(code, 200)
        self.assertEqual(body, {"available": False, "reason": "gh api lỗi: HTTP 401 Bad credentials"})


FORBIDDEN_SRC = re.compile(
    r"\bsubprocess\b|\bos\.system\b|\bos\.popen\b|\bpty\b|\bPopen\b|\bos\.exec\w*|\bos\.spawn\w*"
)


class StaticNoProcessTest(unittest.TestCase):
    def test_xt_app_runs_no_process(self) -> None:
        """RK-3: không module nào của `scripts/xt_app/` chạy tiến trình (gh chỉ qua `xt._gh_api` nằm trong xt.py)."""
        srcs = sorted((ROOT / "scripts" / "xt_app").glob("*.py"))
        self.assertIn("api_pr.py", [p.name for p in srcs])
        for p in srcs:
            hits = FORBIDDEN_SRC.findall(p.read_text(encoding="utf-8"))
            self.assertEqual(hits, [], p.name)

    def test_api_pr_reads_github_only_through_gh_api(self) -> None:
        src = (ROOT / "scripts" / "xt_app" / "api_pr.py").read_text(encoding="utf-8")
        for bad in ("_steward", "_write_reviews", "write_atomic", "_publish_review", "cmd_", "urllib", "http.client"):
            self.assertNotIn(bad, src)
        self.assertNotRegex(src, r"^\s*import xt\b|^\s*from xt import", "dùng ctx.xt")


class PrHttpTest(unittest.TestCase):
    def test_http(self) -> None:
        with Sandbox(gh=GhSpy()) as sb:
            routes = {**server.ROUTES, **api_pr.ROUTES}
            srv, token = server.make_server(xt, sb.base, sb.base / "framework", sb.base / "static", routes=routes)
            srv.quiet = True
            th = threading.Thread(target=srv.serve_forever, daemon=True)
            th.start()
            got: Dict[str, Tuple[int, Dict[str, Any]]] = {}
            try:
                for path in ("/api/prs", "/api/pr-stats?days=14"):
                    conn = http.client.HTTPConnection("127.0.0.1", srv.server_address[1], timeout=30)
                    conn.putrequest("GET", path, skip_host=True)
                    conn.putheader("Host", f"127.0.0.1:{srv.server_address[1]}")
                    conn.putheader("X-XT-Token", token)
                    conn.endheaders()
                    resp = conn.getresponse()
                    got[path] = (resp.status, json.loads(resp.read()))
                    conn.close()
            finally:
                srv.shutdown()
                srv.server_close()
                th.join(5)
            sb.assert_no_write(self)
        self.assertEqual(got["/api/prs"][0], 200)
        self.assertIs(got["/api/prs"][1]["available"], True)
        self.assertEqual(len(got["/api/prs"][1]["prs"]), 3)
        self.assertEqual((got["/api/pr-stats?days=14"][0], got["/api/pr-stats?days=14"][1]["days"]), (200, 14))


if __name__ == "__main__":
    unittest.main()


class LocalCheckTest(unittest.TestCase):
    """App gọi `_pr_rest(local_check=False)`: PR GitHub chưa tính `mergeable` không kéo `git fetch`/`merge-tree` cục bộ;
    CLI (`local_check` mặc định) vẫn kiểm như cũ."""

    def test_unknown_mergeable_skips_local_conflict_check_only_in_app(self) -> None:
        def gh(path: str, *a: Any, **k: Any) -> List[Any]:
            if re.search(r"/pulls/7$", path):
                return [{**pr_json(7, SHA7, "docs: sửa"), "mergeable": None, "mergeable_state": "unknown"}]
            return GhSpy()(path, *a, **k)

        local = mock.Mock(return_value=None)
        with Sandbox(gh=gh) as sb, mock.patch.object(xt, "local_merge_conflicts", local):
            _, body = sb.call("/api/prs")
            self.assertFalse(local.called)
            self.assertEqual(next(p for p in body["prs"] if p["number"] == 7)["head_sha"], SHA7)
            xt._pr_rest("7")
            self.assertTrue(local.called)
