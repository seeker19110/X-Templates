"""Test cho `xt.py merge-check` — máy quyết khi nào merge PR đã mở (ADR-0013)."""

from __future__ import annotations

import base64
import contextlib
import datetime
import io
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
import time
import unittest
import unittest.mock
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import xt

REAL_RUN = subprocess.run

GREEN = [
    {"__typename": "CheckRun", "name": "test", "status": "COMPLETED", "conclusion": "SUCCESS"},
    {"__typename": "CheckRun", "name": "lint", "status": "COMPLETED", "conclusion": "SKIPPED"},
    {"__typename": "StatusContext", "context": "ci/legacy", "state": "SUCCESS"},
]


def pr(**over: Any) -> dict:
    """PR làn nhanh, CI xanh, sẵn sàng — mỗi test đổi đúng một trường."""
    base = {
        "number": 7,
        "state": "OPEN",
        "isDraft": False,
        "mergeable": "MERGEABLE",
        "mergeStateStatus": "CLEAN",
        "reviewDecision": "",
        "headRefOid": "abc1234def",
        "labels": [],
        "statusCheckRollup": GREEN,
        "files": [
            {"path": "src/cart/total.py", "additions": 20, "deletions": 4},
            {"path": "tests/test_total.py", "additions": 30, "deletions": 0},
            {"path": "CHANGELOG.md", "additions": 1, "deletions": 0},
        ],
    }
    base.update(over)
    return base


def commit_base_xt(base: Path, committed: str, working: str | None = None) -> None:
    """Repo git tạm: `origin/main` có xt.yaml = `committed`; cây làm việc = `working` (mặc định như commit) — ADR-0020
    đọc khoá ở nhánh đích, không ở cây làm việc."""
    (base / "xt.yaml").write_text(committed, encoding="utf-8")
    git = ["git", "-C", str(base), "-c", "user.email=t@t", "-c", "user.name=t", "-c", "commit.gpgsign=false"]
    for args in (
        ["init", "-q"],
        ["add", "xt.yaml"],
        ["commit", "-qm", "x", "--allow-empty"],
        ["update-ref", "refs/remotes/origin/main", "HEAD"],
    ):
        subprocess.run([*git, *args], check=True, capture_output=True)
    if working is not None:
        (base / "xt.yaml").write_text(working, encoding="utf-8")


REQUIRED_TEST = [{"type": "required_status_checks", "parameters": {"required_status_checks": [{"context": "test"}]}}]


class FakeGh:
    """Giả `gh api` (REST) theo đường dẫn; mặc định trả đúng PR của fixture `pr()` (files và check-run chia 2 trang)."""

    SHA = "abc1234def"
    REPO = "repos/{owner}/{repo}"

    def __init__(
        self,
        pull: dict | None = None,
        reviews: list | None = None,
        runs: list | None = None,
        statuses: list | None = None,
        open_prs: list | None = None,
        comments: list | None = None,
        raw: dict | None = None,
        rules: list | None = None,
        branch: dict | None = None,
        real_git: bool = False,
    ):
        self.pull = {
            "number": 7,
            "state": "open",
            "merged": False,
            "draft": False,
            "mergeable": True,
            "mergeable_state": "clean",
            "head": {"sha": self.SHA},
            "base": {"ref": "main"},
            "labels": [],
            **(pull or {}),
        }
        self.reviews = reviews or []
        self.runs = (
            runs
            if runs is not None
            else [
                {"name": "test", "status": "completed", "conclusion": "success"},
                {"name": "lint", "status": "completed", "conclusion": "skipped"},
            ]
        )
        self.statuses = statuses if statuses is not None else [{"context": "ci/legacy", "state": "success"}]
        self.open_prs = open_prs if open_prs is not None else [{"number": 7}]
        self.comments = comments or []
        self.rules = rules if rules is not None else REQUIRED_TEST  # check bắt buộc của nhánh đích (REC-08)
        self.branch = branch or {}
        self.raw = raw or {}
        self.real_git = real_git
        self.calls: list[list[str]] = []
        xt._CHAIN_CACHE.clear()  # cache của xt: mỗi FakeGh một bộ dữ liệu giả

    def paths(self) -> list[str]:
        return [_unpage(c[-1])[0] for c in self.calls]

    def respond(self, cmd: list[str], **kw: Any) -> subprocess.CompletedProcess:
        if cmd[0] == "git":  # xt.yaml ở nhánh đích: mặc định không có repo → human/L1; `real_git` = repo tạm của test
            if self.real_git:
                return REAL_RUN(cmd, **kw)
            return subprocess.CompletedProcess(cmd, 128, "", "not a git repository")
        self.calls.append(cmd)
        path, later = _unpage(cmd[-1])
        if later:  # phân trang tự làm (FB-001): trang ≥ 2 rỗng
            return subprocess.CompletedProcess(cmd, 0, "[]", "")
        files = [
            {"filename": f["path"], "additions": f["additions"], "deletions": f["deletions"]} for f in pr()["files"]
        ]
        routes = {
            f"{self.REPO}/pulls/7": json.dumps(self.pull),
            f"{self.REPO}/pulls/7/files?per_page=100": json.dumps(files[:2]) + json.dumps(files[2:]),
            f"{self.REPO}/pulls/7/reviews?per_page=100": json.dumps(self.reviews),
            f"{self.REPO}/issues/7/comments?per_page=100": json.dumps(self.comments),
            f"{self.REPO}/rules/branches/main": json.dumps(self.rules),
            f"{self.REPO}/branches/main": json.dumps(self.branch),
            f"{self.REPO}/commits/{self.SHA}/check-runs?per_page=100": json.dumps({"check_runs": self.runs[:1]})
            + "\n"
            + json.dumps({"check_runs": self.runs[1:]}),
            f"{self.REPO}/commits/{self.SHA}/status?per_page=100": json.dumps({"statuses": self.statuses}),
        }
        if path in self.raw:
            out = self.raw[path]
        elif "/pulls?head=" in path or "/pulls?state=open" in path:
            out = json.dumps(self.open_prs)
        elif path in routes:
            out = routes[path]
        elif "/compare/" in path or re.fullmatch(r".*/commits/[0-9a-zA-Z]+", path):
            out = "{}"  # không có compare/commit giả: không mang review sang head mới (D-061)
        elif "/rules/branches/" in path:
            out = "[]"  # nhánh đích khác `main` trong test: không có ruleset
        elif "/branches/" in path:
            out = "{}"
        else:
            out = routes[path]
        return subprocess.CompletedProcess(cmd, 0, out, "")

    def patch(self) -> Any:
        return unittest.mock.patch.object(xt.subprocess, "run", side_effect=self.respond)


def _unpage(path: str) -> tuple[str, bool]:
    """Route không mang `page=N` của phân trang tự làm; True khi là trang ≥ 2."""
    m = re.search(r"[?&]page=(\d+)$", path)
    return (path[: m.start()], int(m.group(1)) > 1) if m else (path, False)


def run_main(*args: str, stdin: str | None = None) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        if stdin is None:
            rc = xt.main(list(args))
        else:
            with unittest.mock.patch.object(sys, "stdin", io.StringIO(stdin)):
                rc = xt.main(list(args))
    return rc, out.getvalue(), err.getvalue()


class MergeDecisionTest(unittest.TestCase):
    def test_fast_lane_green_at_l2_merges_with_head_guard(self):
        d = xt.merge_decision(pr(), autonomy=2)
        self.assertEqual((d["verdict"], d["lane"]), ("merge", "nhanh"))
        self.assertEqual(d["next"], "gh pr merge 7 --squash --match-head-commit abc1234def")
        self.assertEqual(d["head"], "abc1234def")  # guard so với --match-head-commit của lệnh merge

    def test_default_autonomy_l1_leaves_merge_to_human(self):
        d = xt.merge_decision(pr())
        self.assertEqual((d["verdict"], d["lane"]), ("human", "nhanh"))
        self.assertIn("mức tự chủ L1", d["reasons"][0])

    def test_l3_merges_standard_lane_and_reports_autonomy(self):
        """ADR-0015: L3 tự merge cả làn chuẩn khi CI xanh; người vẫn quyết khi ruleset đòi review; PR chồng → wait."""
        hot = pr(files=[{"path": ".claude/hooks/guard.py", "additions": 900, "deletions": 0}])
        self.assertEqual(xt.merge_decision(hot, 2)["verdict"], "human")
        d = xt.merge_decision(hot, 3)
        self.assertEqual((d["verdict"], d["lane"], d["autonomy"], d["stacked"]), ("merge", "chuẩn", 3, False))
        self.assertEqual(xt.merge_decision(pr(reviewDecision="REVIEW_REQUIRED"), 3)["verdict"], "human")
        st = xt.merge_decision(pr(baseRefName="feat/a", defaultBranch="main"), 3)
        self.assertEqual((st["verdict"], st["stacked"]), ("wait", True))

    def test_state_order(self):
        cases = {
            "đóng": (pr(state="MERGED"), "closed", "PR đã MERGED"),
            "nháp": (pr(isDraft=True), "wait", "PR nháp"),
            "tiêu đề không conventional": (pr(title="Sửa guard", mergeable="CONFLICTING"), "fix", "tiêu đề PR phải"),
            "tiêu đề > 72": (pr(title="fix: " + "a" * 68), "fix", "≤ 72 ký tự"),
            "tiêu đề nhiều dòng": (pr(title="fix: a\nb"), "fix", "gh pr edit 7 --title"),
            "xung đột": (pr(mergeable="CONFLICTING"), "fix", "xung đột với nhánh đích"),
            "dirty": (pr(mergeStateStatus="DIRTY"), "fix", "xung đột với nhánh đích"),
            "đổi yêu cầu": (pr(reviewDecision="CHANGES_REQUESTED"), "fix", "reviewer yêu cầu sửa"),
            "tụt sau": (pr(mergeStateStatus="BEHIND"), "update", "nhánh tụt sau nhánh đích"),
            "chưa tính": (pr(mergeable="UNKNOWN"), "wait", "GitHub chưa tính xong mergeable"),
            "cần review": (pr(reviewDecision="REVIEW_REQUIRED"), "human", "ruleset đòi review của người"),
        }
        for name, (p, verdict, reason) in cases.items():
            with self.subTest(name):
                d = xt.merge_decision(p, autonomy=2)
                self.assertEqual(d["verdict"], verdict)
                self.assertIn(reason, " · ".join(d["reasons"]))
        for ok in ("fix(guard): a", "feat!: b", "chore(release/x.y): 3.5.0", "fix: " + "a" * 67):
            with self.subTest(ok):
                self.assertEqual(xt.merge_decision(pr(title=ok), autonomy=2)["verdict"], "merge")
        # `update` bằng git (gh pr update-branch cần GraphQL — phiên Claude Code chặn)
        self.assertEqual(
            xt.merge_decision(pr(mergeStateStatus="BEHIND", baseRefName="dev"), 2)["next"],
            "gh api -X PUT repos/{owner}/{repo}/pulls/7/update-branch -f expected_head_sha=abc1234def"
            " (hoặc git merge origin/dev && git push)",
        )

    def test_required_check_executed(self):
        """T-1504 (REC-08): GitHub tính required check skipped/neutral là đạt; máy không — check bắt buộc SKIPPED/NEUTRAL/
        CANCELLED/STALE hoặc chỉ có bản của app khác → `not_run` → `human`; check không bắt buộc không bị ảnh hưởng."""

        def run(name: str, concl: str, app: int | None = None) -> dict:
            return {
                "__typename": "CheckRun",
                "name": name,
                "status": "COMPLETED",
                "conclusion": concl,
                **({"appId": app} if app is not None else {}),
            }

        req = [("test", None)]
        for concl in ("SKIPPED", "NEUTRAL", "CANCELLED", "STALE"):
            red, pend, green, not_run = xt._ci_buckets([run("test", concl), run("lint", "SUCCESS")], req)
            self.assertEqual((red, pend, green, not_run), ([], [], ["lint"], ["test"]), concl)
        # không bắt buộc: skipped chỉ là không có bằng chứng; cancelled vẫn đỏ như trước
        self.assertEqual(xt._ci_buckets([run("test", "SKIPPED")], [])[3], [])
        self.assertEqual(xt._ci_buckets([run("lint", "CANCELLED")], req)[0], ["lint"])
        # bản hợp lệ thắng bản skipped cùng tên; vắng hẳn → không phải not_run (việc của missingRequired)
        self.assertEqual(xt._ci_buckets([run("test", "SKIPPED"), run("test", "SUCCESS")], req)[2:], (["test"], []))
        self.assertEqual(xt._ci_buckets([run("lint", "SUCCESS")], req)[3], [])
        # app: ruleset đòi integration_id 15368; bản của app 99 không thay được, dù xanh
        got = xt._ci_buckets([run("test", "SUCCESS", 99), run("lint", "SUCCESS")], [("test", 15368)])
        self.assertEqual((got[2], got[3]), (["lint"], ["test"]))
        got = xt._ci_buckets([run("test", "SUCCESS", 15368), run("lint", "SUCCESS")], [("test", 15368)])
        self.assertEqual((got[2], got[3]), (["test", "lint"], []))
        legacy = {"__typename": "StatusContext", "context": "test", "state": "SUCCESS"}  # commit status không có app
        self.assertEqual(xt._ci_buckets([legacy], [("test", 15368)])[2:], (["test"], []))
        # merge_decision: PR "xanh" nhưng check bắt buộc bị skip → human, không phải merge
        p = pr(
            statusCheckRollup=[run("test", "SKIPPED"), run("lint", "SUCCESS")],
            requiredChecks=[{"context": "test"}, {"context": "lint", "appId": 15368}, "rác"],
        )
        d = xt.merge_decision(p, 3)
        self.assertEqual(d["verdict"], "human")
        self.assertIn("check bắt buộc không chạy thật (skipped/neutral/huỷ/sai app): test —", d["reasons"][0])
        foreign = pr(
            statusCheckRollup=[
                run("test", "SUCCESS"),
                run("lint", "SUCCESS", 99),
            ],  # lint do app 99 sinh, ruleset đòi 15368
            requiredChecks=[{"context": "test"}, {"context": "lint", "appId": 15368}],
        )
        d = xt.merge_decision(foreign, 3)
        self.assertEqual(d["verdict"], "human")
        self.assertIn("sai app): lint —", d["reasons"][0])
        ok = pr(
            statusCheckRollup=[run("test", "SUCCESS"), run("lint", "SUCCESS", 15368)],
            requiredChecks=p["requiredChecks"][:2],
        )
        self.assertEqual(xt.merge_decision(ok, 3)["verdict"], "merge")
        self.assertEqual(xt.merge_decision(pr(), 3)["verdict"], "merge")  # không khai requiredChecks: như cũ
        # CI đỏ/đang chạy vẫn thắng not_run
        mixed = {**p, "statusCheckRollup": [run("test", "SKIPPED"), run("lint", "FAILURE", 15368)]}
        self.assertEqual(xt.merge_decision(mixed, 3)["verdict"], "fix")

    def test_required_check_executed_rest_maps_app_and_ruleset(self):
        """`_pr_rest` đưa `appId` của check-run và `requiredChecks` (context + integration_id) của ruleset vào PR."""
        rules = [
            {
                "type": "required_status_checks",
                "parameters": {
                    "required_status_checks": [{"context": "test", "integration_id": 15368}, {"context": "lint"}]
                },
            }
        ]
        runs = [
            {"id": 1, "name": "test", "status": "completed", "conclusion": "success", "app": {"id": 99}},
            {"id": 2, "name": "lint", "status": "completed", "conclusion": "success"},
        ]
        with FakeGh(rules=rules, runs=runs, statuses=[]).patch():
            p = xt._pr_rest("7")
        self.assertEqual(p["requiredChecks"], [{"context": "test", "appId": 15368}, {"context": "lint"}])
        self.assertEqual([c.get("appId") for c in p["statusCheckRollup"]], [99, None])
        d = xt.merge_decision(p, 3)
        self.assertEqual(d["verdict"], "human")
        self.assertIn("không chạy thật", d["reasons"][0])
        self.assertIn("test", d["reasons"][0])
        with FakeGh(rules=[]).patch():  # không đọc được/không có ruleset → không khoá requiredChecks
            self.assertNotIn("requiredChecks", xt._pr_rest("7"))

    def test_local_conflict_check_decides_before_github(self):
        """Xung đột tính cục bộ (`localConflicts` từ `git merge-tree`): GitHub chưa tính xong mà cục bộ thấy xung đột → `fix`
        kèm file + lệnh merge nhánh đích; cục bộ sạch → không `wait`; GitHub báo xung đột mà cục bộ sạch → vẫn tin GitHub."""
        d = xt.merge_decision(pr(mergeable="UNKNOWN", localConflicts=["a.py", "docs/b.md"]), autonomy=2)
        self.assertEqual(d["verdict"], "fix")
        self.assertIn("xung đột với nhánh đích ở a.py, docs/b.md", d["reasons"][0])
        self.assertEqual(
            d["next"],
            "git fetch origin main && git merge origin/main → giải xung đột, chạy cổng, push, chạy lại merge-check",
        )
        self.assertEqual(xt.merge_decision(pr(mergeable="UNKNOWN", localConflicts=[]), autonomy=2)["verdict"], "merge")
        d = xt.merge_decision(pr(mergeable="CONFLICTING", localConflicts=[]), autonomy=2)
        self.assertEqual(
            (d["verdict"], d["reasons"][0]), ("fix", "xung đột với nhánh đích — merge nhánh đích vào rồi giải")
        )
        self.assertEqual(xt.merge_decision(pr(mergeable="UNKNOWN", localConflicts="x"), autonomy=2)["verdict"], "wait")
        self.assertEqual(xt.merge_decision(pr(mergeable="UNKNOWN"), autonomy=2)["next"], "chờ rồi chạy lại merge-check")

    def test_local_merge_conflicts_real_git_and_errors(self):
        """`local_merge_conflicts`: repo thật — nhánh đích và head sửa cùng dòng → file xung đột; sửa khác file → []; commit
        thiếu → fetch `origin <base> refs/pull/N/head`, fetch hỏng/git cũ/không phải repo → None (fail-open)."""
        d = Path(self.enterContext(tempfile.TemporaryDirectory()))
        subprocess.run(["git", "-C", str(d), "init", "-q"], check=True)
        for k, v in (("user.email", "t@x"), ("user.name", "t"), ("commit.gpgsign", "false")):
            subprocess.run(["git", "-C", str(d), "config", k, v], check=True)

        def commit(msg: str) -> str:
            subprocess.run(["git", "-C", str(d), "add", "-A"], check=True)
            subprocess.run(["git", "-C", str(d), "commit", "-qm", msg], check=True)
            return subprocess.run(
                ["git", "-C", str(d), "rev-parse", "HEAD"], capture_output=True, text=True
            ).stdout.strip()

        (d / "a.txt").write_text("1\n")
        (d / "b.txt").write_text("1\n")
        root = commit("root")
        (d / "a.txt").write_text("head\n")
        head = commit("head")
        subprocess.run(["git", "-C", str(d), "checkout", "-q", "-b", "base", root], check=True)
        (d / "b.txt").write_text("base\n")
        base_ok = commit("base ok")
        self.assertEqual(xt.local_merge_conflicts("base", base_ok, head, "7", d), [])
        (d / "a.txt").write_text("base\n")
        base_bad = commit("base bad")
        self.assertEqual(xt.local_merge_conflicts("base", base_bad, head, "7", d), ["a.txt"])
        self.assertIsNone(xt.local_merge_conflicts("base", "", head, "7", d))
        subprocess.run(["git", "-C", str(d), "checkout", "-q", "-b", "u1", root], check=True)
        (d / "tên có dấu.txt").write_text("1\n")
        u1 = commit("u1")
        subprocess.run(["git", "-C", str(d), "checkout", "-q", "-b", "u2", root], check=True)
        (d / "tên có dấu.txt").write_text("2\n")
        u2 = commit("u2")
        self.assertEqual(xt.local_merge_conflicts("u1", u1, u2, "7", d), ["tên có dấu.txt"])  # -z: không quote bát phân
        missing = "0" * 39 + "1"
        with unittest.mock.patch.object(xt, "_git", wraps=xt._git) as g:
            self.assertIsNone(
                xt.local_merge_conflicts("base", base_bad, missing, "7", d)
            )  # fetch (không có origin) hỏng
        fetches = [c for c in g.call_args_list if c.args[1] == "fetch"]
        self.assertEqual(fetches[0].args[1:], ("fetch", "-q", "--no-tags", "origin", "base", "refs/pull/7/head"))
        self.assertIsNone(xt.local_merge_conflicts("", base_bad, missing, "", d))  # không biết lấy ở đâu → không fetch
        with unittest.mock.patch.object(xt, "_git") as g:  # fetch xong mà commit vẫn thiếu → None
            g.side_effect = lambda *a, **k: subprocess.CompletedProcess(a, 0 if a[1] == "fetch" else 128, "", "")
            self.assertIsNone(xt.local_merge_conflicts("base", base_bad, missing, "7", d))
        seen: list[str] = []

        def fetch_then_ok(
            *a: Any, **k: Any
        ) -> subprocess.CompletedProcess:  # cat-file thiếu → fetch OK → có commit → sạch
            seen.append(a[1])
            first_probe = a[1] == "cat-file" and "fetch" not in seen
            return subprocess.CompletedProcess(a, 1 if first_probe else 0, "", "")

        with unittest.mock.patch.object(xt, "_git", side_effect=fetch_then_ok):
            self.assertEqual(xt.local_merge_conflicts("base", base_bad, missing, "7", d), [])
        self.assertEqual(seen, ["cat-file", "cat-file", "rev-parse", "fetch", "cat-file", "cat-file", "merge-tree"])
        old_git = subprocess.CompletedProcess([], 129, "", "unknown option")  # git cũ: không có --write-tree
        with unittest.mock.patch.object(xt, "_git") as g:
            g.side_effect = lambda *a, **k: (
                old_git if a[1] == "merge-tree" else subprocess.CompletedProcess(a, 0, "", "")
            )
            self.assertIsNone(xt.local_merge_conflicts("base", base_bad, head, "7", d))
        odd = subprocess.CompletedProcess([], 1, "tree-only\0", "")
        with unittest.mock.patch.object(xt, "_git") as g:
            g.side_effect = lambda *a, **k: odd if a[1] == "merge-tree" else subprocess.CompletedProcess(a, 0, "", "")
            self.assertIsNone(xt.local_merge_conflicts("base", base_bad, head, "7", d))  # exit 1 mà không có file
        tree_then_msgs = subprocess.CompletedProcess(
            [], 1, "t\0x.py\0tên có dấu.txt\0\0msg\0", ""
        )  # -z: trường rỗng rồi thông điệp
        with unittest.mock.patch.object(xt, "_git") as g:
            g.side_effect = lambda *a, **k: (
                tree_then_msgs if a[1] == "merge-tree" else subprocess.CompletedProcess(a, 0, "", "")
            )
            self.assertEqual(xt.local_merge_conflicts("base", base_bad, head, "7", d), ["x.py", "tên có dấu.txt"])
        shallow = subprocess.CompletedProcess([], 0, "true\n", "")  # repo nông (CI depth 1): không fetch lịch sử về
        with unittest.mock.patch.object(xt, "_git") as g:
            g.side_effect = lambda *a, **k: (
                shallow
                if a[1] == "rev-parse"
                else subprocess.CompletedProcess(a, 1 if a[1] == "cat-file" else 0, "", "")
            )
            self.assertIsNone(xt.local_merge_conflicts("base", base_bad, missing, "7", d))
        self.assertNotIn("fetch", [c.args[1] for c in g.call_args_list])
        empty = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.assertIsNone(xt.local_merge_conflicts("base", base_bad, head, "7", empty))  # không phải repo git

    def test_local_merge_conflicts_non_utf8_name_and_real_shallow_clone(self):
        """Review #165: tên file KHÔNG phải UTF-8 (`lat\\xe9`) ở xung đột — `-z` in byte thô, không được sập
        UnicodeDecodeError (steward/merge-watch chết); clone nông thật: commit `main` thiếu → không fetch (kể cả khi fetch sẽ thành công) → None."""
        d = Path(self.enterContext(tempfile.TemporaryDirectory()))

        def git(*a: str) -> str:
            r = subprocess.run(
                ["git", "-C", str(d), "-c", "user.name=t", "-c", "user.email=t@x", "-c", "commit.gpgsign=false", *a],
                capture_output=True,
                text=True,
            )
            self.assertEqual(r.returncode, 0, r.stderr)
            return r.stdout.strip()

        git("init", "-q")
        name = os.fsdecode(b"lat\xe9")
        (d / name).write_text("1")
        git("add", "-A")
        git("commit", "-qm", "r")
        root = git("rev-parse", "HEAD")
        git("checkout", "-q", "-b", "m")
        (d / name).write_text("2")
        git("commit", "-qam", "m")
        main = git("rev-parse", "HEAD")
        git("checkout", "-q", "-b", "b", root)
        (d / name).write_text("3")
        git("commit", "-qam", "b")
        head = git("rev-parse", "HEAD")
        got = xt.local_merge_conflicts("m", main, head, "1", d)
        self.assertEqual(len(got or []), 1)
        self.assertTrue(got and got[0].startswith("lat"))
        clone = Path(self.enterContext(tempfile.TemporaryDirectory())) / "c"
        subprocess.run(
            ["git", "clone", "-q", "--depth", "1", "--no-local", f"file://{d}", str(clone)],
            check=True,
            capture_output=True,
        )
        with unittest.mock.patch.object(
            xt, "_git", wraps=xt._git
        ) as g:  # number="" → fetch `m` sẽ thành công nếu có chạy
            self.assertIsNone(xt.local_merge_conflicts("m", main, head, "", clone))
        self.assertNotIn("fetch", [c.args[1] for c in g.call_args_list])  # nông: không fetch, không kiểm được

    def test_rest_adds_local_conflicts_when_github_undecided(self):
        """`_pr_rest`: chỉ hỏi kiểm cục bộ khi GitHub chưa khẳng định MERGEABLE; không kiểm được → không có khoá."""
        with FakeGh(
            pull={"mergeable": None, "mergeable_state": "unknown", "base": {"ref": "main", "sha": "b" * 40}}
        ).patch():
            with unittest.mock.patch.object(xt, "local_merge_conflicts", return_value=["a.py"]) as lmc:
                got = xt._pr_rest("7")
        self.assertEqual(got["localConflicts"], ["a.py"])
        self.assertEqual(lmc.call_args.args, ("main", "b" * 40, FakeGh.SHA, "7"))
        with FakeGh(pull={"mergeable": None, "mergeable_state": "unknown"}).patch():  # git giả trả 128 → None
            self.assertNotIn("localConflicts", xt._pr_rest("7"))
        with FakeGh().patch(), unittest.mock.patch.object(xt, "local_merge_conflicts") as lmc:
            self.assertNotIn("localConflicts", xt._pr_rest("7"))
        lmc.assert_not_called()

    def test_stacked_pr_waits_for_bottom(self):
        """Reviewer #59: PR chồng nhắm nhánh khác nhánh mặc định → chờ, không merge vào nhánh sắp chết."""
        d = xt.merge_decision(pr(baseRefName="feat/a", defaultBranch="main"), 2)
        self.assertEqual(d["verdict"], "wait")
        self.assertIn("PR chồng", d["reasons"][0])
        ok = xt.merge_decision(pr(baseRefName="main", defaultBranch="main"), 2)
        self.assertEqual(ok["verdict"], "merge")
        self.assertEqual(
            ok["next_rest"], "gh api -X PUT repos/{owner}/{repo}/pulls/7/merge -f sha=abc1234def -f merge_method=squash"
        )
        self.assertNotIn("next_rest", d)
        raw = {
            "repos/{owner}/{repo}/pulls/7": json.dumps(
                {**FakeGh().pull, "base": {"ref": "feat/a", "repo": {"full_name": "o/r", "default_branch": "main"}}}
            )
        }
        with FakeGh(raw=raw).patch():
            got = xt._pr_rest("7")
        self.assertEqual((got["repo"], got["baseRefName"], got["defaultBranch"]), ("o/r", "feat/a", "main"))

    def test_ci_states(self):
        red = [*GREEN, {"__typename": "CheckRun", "name": "e2e", "status": "COMPLETED", "conclusion": "FAILURE"}]
        err = [*GREEN, {"__typename": "StatusContext", "context": "deploy", "state": "ERROR"}]
        running = [*GREEN, {"__typename": "CheckRun", "name": "build", "status": "IN_PROGRESS", "conclusion": ""}]
        waiting = [*GREEN, {"__typename": "StatusContext", "context": "ext", "state": "PENDING"}]
        self.assertEqual(xt.merge_decision(pr(statusCheckRollup=red), 2)["reasons"], ["CI đỏ: e2e"])
        self.assertEqual(xt.merge_decision(pr(statusCheckRollup=err), 2)["verdict"], "fix")
        self.assertEqual(xt.merge_decision(pr(statusCheckRollup=running), 2)["reasons"], ["CI đang chạy: build"])
        self.assertEqual(xt.merge_decision(pr(statusCheckRollup=waiting), 2)["verdict"], "wait")
        none = xt.merge_decision(pr(statusCheckRollup=[]), 2)
        self.assertEqual(
            (none["verdict"], none["reasons"]), ("human", ["không có check CI nào xanh — không có bằng chứng"])
        )

    def test_merge_gate_not_ci_evidence(self):
        """AUD-HAR-058: `pr-steward` và stub `merge-gate` (luôn xanh, ADR-0036 §5) không kiểm mã — một mình chúng xanh
        không phải bằng chứng CI (dự án đích chưa có CI riêng từng được merge khi chưa test nào chạy)."""
        gate = {"__typename": "CheckRun", "name": "merge-gate", "status": "COMPLETED", "conclusion": "SUCCESS"}
        steward = {**gate, "name": "pr-steward"}
        for rollup in ([gate], [gate, steward], [{**gate, "name": "Merge-Gate"}]):
            d = xt.merge_decision(pr(statusCheckRollup=rollup), 3)
            self.assertEqual(d["verdict"], "human")
            self.assertIn("không kiểm mã", d["reasons"][0])
        self.assertEqual(xt.merge_decision(pr(statusCheckRollup=[*GREEN, gate]), 2)["verdict"], "merge")

    def test_subproject_hard_key_and_risk_paths(self):
        """AUD-XFEAT-003/004: khung cài ở dự án con (`apps/web`) — xt.yaml của dự án con là khoá ngoại lệ cứng, glob
        `merge_risk_paths` viết theo gốc dự án vẫn khớp đường file của PR (tính từ gốc repo)."""
        repo = Path(self.enterContext(tempfile.TemporaryDirectory()))
        web = repo / "apps" / "web"
        web.mkdir(parents=True)
        (web / "xt.yaml").write_text('merge_risk_paths: "src/exports/*"\n', encoding="utf-8")
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        with unittest.mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(web)}):
            self.assertEqual(xt.project_prefix(), "apps/web/")
            self.assertTrue(xt._gated_file({"filename": "apps/web/xt.yaml"}, "apps/web/"))
            self.assertFalse(xt._gated_file({"filename": "xt.yaml"}, "apps/web/"))  # xt.yaml gốc repo không áp vào
            with unittest.mock.patch.object(xt, "_hard_key_changed", return_value=True) as changed:
                self.assertTrue(xt._touches_hard_key({"filename": "apps/web/xt.yaml"}, "o/r", "a", "b", "apps/web/"))
                changed.assert_called_once_with("o/r", "a", "b", "apps/web/")
            with unittest.mock.patch.object(
                xt, "_contents_read", return_value=("merge_hard_exceptions: human\n", False)
            ) as rd:
                xt._hard_key_changed("o/r", "a", "b", "apps/web/")
                self.assertEqual(rd.call_args_list[0].args[1], "apps/web/xt.yaml")
            globs = xt.merge_risk_globs(web, "origin/main")
            self.assertEqual(globs, ["src/exports/*", "apps/web/src/exports/*"])
            d = xt.merge_decision(pr(files=[{"path": "apps/web/src/exports/c.ts", "additions": 1}]), 3, globs)
            self.assertIn("merge_risk_paths", " ".join(d["hard"]))
        with unittest.mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(repo / "khong-git")}):
            (repo / "khong-git").mkdir()
            with unittest.mock.patch.object(xt, "_git", return_value=subprocess.CompletedProcess([], 128, "", "")):
                self.assertEqual(xt.project_prefix(), "")

    def test_agent_harness_session_is_not_hard_auth(self):
        """D-020: `session`/`permission` trong harness agent là phiên/quyền của agent, không phải auth của ứng dụng — không
        thuộc ngoại lệ cứng, vẫn làn chuẩn (cổng/CI); code phiên của ứng dụng và bí mật trong harness vẫn là ngoại lệ cứng."""

        def files(*paths: str) -> list[dict]:
            return [{"path": x, "additions": 1, "deletions": 0} for x in paths]

        harness = pr(files=files(".claude/hooks/session-start.sh", ".xtemplates/framework/permissions.md"))
        self.assertEqual(xt.merge_hard_reasons(harness, []), [])
        reasons = xt.merge_lane_reasons(harness, [])
        self.assertTrue(any("(cổng/CI)" in r for r in reasons), reasons)
        self.assertFalse(any("(auth)" in r for r in reasons), reasons)
        for path, tag in (
            ("src/session_store.py", "(auth)"),
            ("app/.claude-like/session.ts", "(auth)"),
            (".claude/.env", "(bí mật)"),
        ):
            with self.subTest(path):
                self.assertIn(tag, " ".join(xt.merge_hard_reasons(pr(files=files(path)), [])))

    def test_standard_lane_reasons(self):
        f = [{"path": "tests/test_x.py", "additions": 1, "deletions": 0}]
        cases = {
            "auth": ([{"path": "src/auth/login.py", "additions": 2, "deletions": 0}, *f], "đường dẫn nhạy cảm (auth)"),
            "migration": ([{"path": "db/migrations/0002.sql", "additions": 2, "deletions": 0}, *f], "(schema)"),
            "cổng": ([{"path": ".github/workflows/ci.yml", "additions": 2, "deletions": 0}, *f], "(cổng/CI)"),
            "phụ thuộc": ([{"path": "package.json", "additions": 1, "deletions": 1}, *f], "(phụ thuộc)"),
            "lớn": ([{"path": "src/a.py", "additions": 140, "deletions": 20}, *f], "161 dòng > 150"),
            "hai gói": (
                [
                    {"path": "packages/web/a.ts", "additions": 1, "deletions": 0},
                    {"path": "packages/api/b.ts", "additions": 1, "deletions": 0},
                    *f,
                ],
                "nhiều gói: packages/api, packages/web",
            ),
            "không test": ([{"path": "src/a.py", "additions": 3, "deletions": 0}], "đổi mã mà không đổi test"),
        }
        for name, (files, reason) in cases.items():
            with self.subTest(name):
                d = xt.merge_decision(pr(files=files), 2)
                self.assertEqual((d["verdict"], d["lane"]), ("human", "chuẩn"))
                self.assertIn(reason, " · ".join(d["reasons"]))
        d = xt.merge_decision(pr(labels=[{"name": "risk:payment"}, {"name": "ui"}]), 2)
        self.assertEqual(d["reasons"], ["ngoại lệ cứng (LOOP-STOP-005): nhãn rủi ro: risk:payment"])
        d = xt.merge_decision(pr(), 2, risk_paths=["src/cart/*"])
        self.assertEqual(
            d["reasons"], ["ngoại lệ cứng (LOOP-STOP-005): đường dẫn nhạy cảm (merge_risk_paths): src/cart/total.py"]
        )

    def test_merge_gate_paths(self):
        """AUD-HAR-021: luật agent và file cổng (cả ở thư mục con) luôn để người merge — cùng danh sách với guard."""
        f = [{"path": "tests/test_x.py", "additions": 1, "deletions": 0}]
        for path in (
            "AGENTS.md",
            "CLAUDE.md",
            "packages/api/AGENTS.md",
            "scripts/dev-task.sh",
            "vitest.config.ts",
            ".pre-commit-config.yaml",
            ".gitleaks.toml",
            "ruff.toml",
            "apps/web/tsconfig.json",
            ".claude/skills/gate/SKILL.md",
        ):
            with self.subTest(path):
                d = xt.merge_decision(pr(files=[{"path": path, "additions": 2, "deletions": 1}, *f]), 2)
                self.assertEqual((d["verdict"], d["lane"]), ("human", "chuẩn"))
                self.assertIn("(cổng/CI)", " · ".join(d["reasons"]))

    def test_merge_gate_paths_cover_guard(self):
        """Một khái niệm hai nhà phải khớp: mọi mẫu cổng của guard (hỏi khi sửa) cũng là đường dẫn nhạy cảm khi merge."""
        sys.path.insert(0, str(ROOT / ".claude" / "hooks"))
        import guard

        self.assertEqual(sorted(set(guard.GATE_PATTERNS) - set(xt.MERGE_GATE_GLOBS)), [])
        # Năng lực agent (LOOP-STOP-023): mọi mẫu của guard là đường dẫn nhạy cảm khi merge (glob rộng hơn được)
        for pat in (*guard.CAPABILITY_PATTERNS, *guard.TARGET_CAPABILITY_PATTERNS):
            path = pat.replace("*", "x")
            reasons = xt.merge_lane_reasons(pr(files=[{"path": path, "additions": 1, "deletions": 0}]), [])
            self.assertIn(f"(cổng/CI): {path}", " · ".join(reasons))

    def test_merge_capability_and_infra_paths(self):
        """Rà stored 2026-10-16: PR chỉ đổi cấu hình MCP/plugin, nguồn gói hay ảnh container + một test không vào làn nhanh."""
        test = [{"path": "tests/test_a.py", "additions": 1, "deletions": 0}]
        cases = {
            ".mcp.json": "cổng/CI",
            "apps/web/.codex/config.toml": "cổng/CI",
            "skills/x/SKILL.md": "cổng/CI",
            "e2e/home.spec.ts-snapshots/a.png": "cổng/CI",
            ".npmrc": "nguồn gói",
            "pip.conf": "nguồn gói",
            "Dockerfile.prod": "ảnh/container",
            "deploy/compose.yaml": "ảnh/container",
        }
        for path, tag in cases.items():
            with self.subTest(path):
                reasons = xt.merge_lane_reasons(pr(files=[{"path": path, "additions": 1, "deletions": 0}, *test]), [])
                self.assertIn(f"({tag}): {path}", " · ".join(reasons))

    def test_merge_renamed_risk_path(self):
        """AUD-HAR-022: đổi tên file nhạy cảm ra ngoài vùng nhạy cảm vẫn là làn chuẩn (xét cả tên cũ)."""
        moved = [
            {
                "path": "scripts/quality.yml.off",
                "previous": ".github/workflows/quality.yml",
                "additions": 0,
                "deletions": 0,
            },
            {"path": "tests/test_x.py", "additions": 1, "deletions": 0},
        ]
        d = xt.merge_decision(pr(files=moved), 2)
        self.assertEqual(d["verdict"], "human")
        self.assertIn(".github/workflows/quality.yml", " · ".join(d["reasons"]))
        renamed = {"filename": "x.off", "previous_filename": ".github/workflows/ci.yml", "additions": 0, "deletions": 0}
        raw = {"repos/{owner}/{repo}/pulls/7/files?per_page=100": json.dumps([renamed])}
        with FakeGh(raw=raw).patch():
            files = xt._pr_rest("7")["files"]
        self.assertEqual(
            files, [{"path": "x.off", "previous": ".github/workflows/ci.yml", "additions": 0, "deletions": 0}]
        )

    def test_merge_skipped_only(self):
        """AUD-HAR-023: chỉ có check SKIPPED/NEUTRAL không phải bằng chứng CI xanh."""
        for concl in ("SKIPPED", "NEUTRAL"):
            with self.subTest(concl):
                rollup = [{"__typename": "CheckRun", "name": "t", "status": "COMPLETED", "conclusion": concl}]
                d = xt.merge_decision(pr(statusCheckRollup=rollup), 2)
                self.assertEqual(
                    (d["verdict"], d["reasons"]), ("human", ["không có check CI nào xanh — không có bằng chứng"])
                )

    def test_lockfiles_and_docs_do_not_count_as_size_or_package(self):
        files = [
            {"path": "docs/guide.md", "additions": 400, "deletions": 0},
            {"path": "README.md", "additions": 5, "deletions": 0},
            {"path": "src/cart/total.py", "additions": 2, "deletions": 0},
            {"path": "tests/test_total.py", "additions": 2, "deletions": 0},
        ]
        self.assertEqual(xt.merge_decision(pr(files=files), 2)["verdict"], "merge")
        docs_only = xt.merge_decision(pr(files=[{"path": "docs/a.md", "additions": 9, "deletions": 0}]), 2)
        self.assertEqual(docs_only["verdict"], "merge")  # chỉ tài liệu: không có mã nên không đòi test
        lock = [*files, {"path": "uv.lock", "additions": 900, "deletions": 50}]
        d = xt.merge_decision(pr(files=lock), 2)
        self.assertEqual(d["reasons"], ["đường dẫn nhạy cảm (phụ thuộc): uv.lock"])  # không tính 950 dòng


class MergeConfigTest(unittest.TestCase):
    def setUp(self):
        self.base = Path(self.enterContext(tempfile.TemporaryDirectory()))

    def test_reads_xt_yaml(self):
        self.assertEqual(xt.merge_config(self.base), (1, [], []))
        (self.base / "xt.yaml").write_text(
            'lint: x\nmerge_autonomy: L2\nmerge_risk_paths: "src/cart/*, infra/**"\n', encoding="utf-8"
        )
        self.assertEqual(xt.merge_config(self.base), (2, ["src/cart/*", "infra/**"], []))
        (self.base / "xt.yaml").write_text("merge_autonomy: tự động\nmerge_risk_paths: ''\n", encoding="utf-8")
        self.assertEqual(
            xt.merge_config(self.base), (1, [], ["merge_autonomy 'tự động' không hợp lệ (L0–L4) — dùng L1"])
        )

    def test_framework_repo_risk_paths(self):
        """D-031 → D-080: ở repo khung, PR nhỏ sửa bộ máy merge (`scripts/xt.py` + test) hay mẫu dự án đích vẫn vào làn
        chuẩn (review trước khi bật auto-merge); tài liệu thuần (luật vòng tự động, ADR) đi làn nhanh — `merge_risk_paths`
        của `xt.yaml` repo."""
        _, globs, _ = xt.merge_config(ROOT)
        small = [
            {"path": "scripts/xt.py", "additions": 20, "deletions": 4},
            {"path": "tests/test_xt_core.py", "additions": 20, "deletions": 0},
        ]
        self.assertEqual(xt.merge_decision(pr(files=small), 3, [], hard_auto=True)["lane"], "nhanh")
        for files in (small, [{"path": "framework/templates/PLAN.md", "additions": 5, "deletions": 0}]):
            d = xt.merge_decision(pr(files=files), 3, globs, hard_auto=True)
            self.assertEqual((d["lane"], d["hard"]), ("chuẩn", []))
            self.assertTrue(d["hard_waived"])
        docs = [{"path": "framework/11-autonomous-loop/loop-design.md", "additions": 100, "deletions": 0}]
        docs += [{"path": "docs/adr/0031-x.md", "additions": 40, "deletions": 0}]
        self.assertEqual(xt.merge_decision(pr(files=docs), 3, globs, hard_auto=True)["lane"], "nhanh")

    def test_hard_mode(self):
        """ADR-0020: khoá đọc ở nhánh đích đã commit; không có ref/thiếu khoá → human; giá trị lạ → human kèm ghi chú;
        cây làm việc sửa tại chỗ không đổi kết quả (agent không tự gỡ được chốt)."""
        self.assertEqual(xt.merge_hard_mode(self.base, "origin/main"), (False, []))  # không có repo/ref
        commit_base_xt(self.base, "lint: x\n", working="merge_hard_exceptions: auto\n")
        self.assertEqual(xt.merge_hard_mode(self.base, "origin/main"), (False, []))
        for raw, want in (("auto", (True, [])), ("human", (False, []))):
            commit_base_xt(self.base, f"merge_hard_exceptions: {raw}\n")
            self.assertEqual(xt.merge_hard_mode(self.base, "origin/main"), want)
        commit_base_xt(self.base, "merge_hard_exceptions: off\n")
        self.assertEqual(
            xt.merge_hard_mode(self.base, "origin/main"),
            (False, ["merge_hard_exceptions 'off' không hợp lệ (human|auto) — dùng human"]),
        )

    def test_merge_base(self):
        """Đáy của PR = merge-base từ REST compare; thiếu sha, lỗi đọc hay JSON lạ → "" (không xác minh được → hard)."""
        with unittest.mock.patch.object(xt, "_gh_one", return_value={"merge_base_commit": {"sha": "mb"}}) as one:
            self.assertEqual(xt._merge_base("repos/o/r", "tip", "head"), "mb")
            self.assertEqual(one.call_args.args, ("repos/o/r/compare/tip...head?per_page=1",))
            self.assertEqual(xt._merge_base("repos/o/r", "", "head"), "")
        for side in ({"merge_base_commit": None}, {"merge_base_commit": {}}, xt.PrInputError("gh api lỗi: 502")):
            with self.subTest(side), unittest.mock.patch.object(xt, "_gh_one", side_effect=[side]):
                self.assertEqual(xt._merge_base("repos/o/r", "tip", "head"), "")

    def test_pr_rest_compares_against_merge_base(self):
        """Review #105: nhánh đích đổi sau lần đồng bộ cuối (base.sha = tip cũ) — so với merge-base, không với tip."""

        def enc(text: str) -> str:
            body = base64.b64encode(text.encode()).decode()
            return json.dumps({"type": "file", "path": "xt.yaml", "encoding": "base64", "content": body})

        repo = FakeGh.REPO
        files = json.dumps([{"filename": "xt.yaml", "additions": 1, "deletions": 1}])
        raw = {
            f"{repo}/pulls/7/files?per_page=100": files,
            f"{repo}/compare/tip...{FakeGh.SHA}?per_page=1": json.dumps({"merge_base_commit": {"sha": "mb"}}),
            f"{repo}/contents/xt.yaml?ref=mb": enc("merge_hard_exceptions: human\n"),
            f"{repo}/contents/xt.yaml?ref=tip": enc("merge_hard_exceptions: auto\n"),
            f"{repo}/contents/xt.yaml?ref={FakeGh.SHA}": enc("merge_hard_exceptions: auto\n"),
        }
        gh = FakeGh(pull={"base": {"sha": "tip", "ref": "main"}}, raw=raw)
        with gh.patch():
            self.assertTrue(xt._pr_rest("7")["files"][0].get("hard_key"))
        self.assertNotIn(f"{repo}/contents/xt.yaml?ref=tip", gh.paths())
        plain = FakeGh(pull={"base": {"sha": "tip", "ref": "main"}})
        with plain.patch():
            xt._pr_rest("7")
        self.assertFalse([p for p in plain.paths() if "/compare/" in p])  # không có file cần so → không hỏi merge-base

    def test_autonomy_is_min_of_working_tree_and_base(self):
        """D-033: sửa tại chỗ chỉ hạ được mức tự chủ; nâng phải qua PR đã merge vào nhánh đích; không có ref → L1."""
        (self.base / "xt.yaml").write_text("merge_autonomy: L3\n", encoding="utf-8")
        level, notes = xt.merge_autonomy_level(self.base, "origin/main")  # chưa có repo/ref
        self.assertEqual((level, notes), (1, ["không đọc được xt.yaml ở origin/main < cây làm việc L3 — dùng L1"]))
        commit_base_xt(self.base, "merge_autonomy: L1\n", working="merge_autonomy: L3\n")
        self.assertEqual(
            xt.merge_autonomy_level(self.base, "origin/main"),
            (1, ["merge_autonomy ở origin/main là L1 < cây làm việc L3 — dùng L1"]),
        )
        commit_base_xt(self.base, "merge_autonomy: L3\n", working="merge_autonomy: L2\n")
        self.assertEqual(xt.merge_autonomy_level(self.base, "origin/main"), (2, []))  # hạ tại chỗ được
        commit_base_xt(self.base, "merge_autonomy: L3\n")
        self.assertEqual(xt.merge_autonomy_level(self.base, "origin/main"), (3, []))
        commit_base_xt(self.base, "merge_autonomy: x\n", working="merge_autonomy: L1\n")
        self.assertEqual(
            xt.merge_autonomy_level(self.base, "origin/main"),
            (1, ["merge_autonomy 'x' không hợp lệ (L0–L4) ở nhánh đích — dùng L1"]),
        )

    def test_risk_globs_union_with_base(self):
        """Checkout cũ/sửa tại chỗ không làm rơi `merge_risk_paths` của nhánh đích; glob thêm tại chỗ vẫn giữ (chặt hơn)."""
        self.assertEqual(xt.merge_risk_globs(self.base, "origin/main"), [])  # không có repo/ref, không có xt.yaml
        commit_base_xt(self.base, 'merge_risk_paths: "scripts/*, docs/adr/*"\n', working="lint: x\n")
        self.assertEqual(xt.merge_risk_globs(self.base, "origin/main"), ["scripts/*", "docs/adr/*"])
        (self.base / "xt.yaml").write_text('merge_risk_paths: "infra/*, scripts/*"\n', encoding="utf-8")
        self.assertEqual(xt.merge_risk_globs(self.base, "origin/main"), ["infra/*", "scripts/*", "docs/adr/*"])

    def test_merge_eval_reads_risk_paths_from_base(self):
        """Đường thật của `merge-check`: PR nhỏ sửa `scripts/xt.py` + test, cây làm việc cũ chưa có glob → vẫn làn chuẩn."""
        commit_base_xt(self.base, 'merge_autonomy: L3\nmerge_risk_paths: "scripts/*"\n', working="merge_autonomy: L3\n")
        small = [
            {"path": "scripts/xt.py", "additions": 5, "deletions": 1},
            {"path": "tests/test_xt_core.py", "additions": 5, "deletions": 0},
        ]
        with unittest.mock.patch.object(xt, "project_dir", return_value=self.base):
            d, _ = xt._merge_eval(pr(files=small, baseRefName="main"))
        self.assertEqual((d["lane"], d["hard"]), ("chuẩn", ["đường dẫn nhạy cảm (merge_risk_paths): scripts/xt.py"]))

    def test_merge_eval_pr_touching_xt_yaml_is_harden(self):
        """D-137: steward chạy trên checkout nhánh đích (build) không thấy xt.yaml của PR — PR sửa xt.yaml tính harden."""
        commit_base_xt(self.base, "delivery_phase: build\n", working="delivery_phase: build\n")
        other = [{"path": "src/a.py", "additions": 200, "deletions": 0}]
        with unittest.mock.patch.object(xt, "project_dir", return_value=self.base):
            d, notes = xt._merge_eval(pr(files=other, baseRefName="main"))
            self.assertEqual(d["delivery_phase"], "build")
            d, notes = xt._merge_eval(pr(files=[*other, {"path": "xt.yaml", "additions": 1, "deletions": 1}]))
        self.assertEqual(d["delivery_phase"], "harden")
        self.assertIn("PR sửa xt.yaml — tính pha harden (D-137)", notes)
        # review #215: đổi tên (tên cũ), dự án con trong monorepo, mục không phải dict
        renamed = [*other, {"path": "old/x.yaml", "previous": "xt.yaml"}, "xt.yaml", None]
        sub = [*other, {"path": "apps/web/xt.yaml"}]
        with unittest.mock.patch.object(xt, "project_dir", return_value=self.base):
            self.assertEqual(xt._merge_eval(pr(files=renamed))[0]["delivery_phase"], "harden")
            with unittest.mock.patch.object(xt, "project_prefix", return_value="apps/web/"):
                self.assertEqual(xt._merge_eval(pr(files=sub))[0]["delivery_phase"], "harden")
            self.assertEqual(xt._merge_eval(pr(files=sub))[0]["delivery_phase"], "build")  # xt.yaml của dự án khác

    def test_touches_hard_key(self):
        """So giá trị hiệu lực `merge_hard_exceptions` (thiếu = human) của xt.yaml gốc ở đáy/đầu PR, không dò chuỗi patch
        (review #103: dòng ngữ cảnh/comment nhắc tên khoá báo nhầm); không xác minh được → chạm; file khác → không."""
        auto, human = "merge_hard_exceptions: auto\n", "merge_hard_exceptions: human\n"
        mod = {"filename": "xt.yaml", "status": "modified", "patch": " merge_hard_exceptions: auto\n+lint: y"}
        cases = {
            "chỉ ngữ cảnh/comment nhắc khoá": (
                auto + "lint: x\n",
                auto + "lint: y\n# merge_hard_exceptions: human\n",
                False,
            ),
            "auto → human": (auto, human, True),
            "human → auto": (human, auto, True),
            "thêm auto": ("lint: x\n", "lint: x\n" + auto, True),
            "xoá auto": (auto, "lint: x\n", True),
            "thêm human tường minh": ("lint: x\n", human, True),  # chặt hơn: mọi dòng khoá đổi là chạm
            "thêm auto bị dòng sau che": (human, auto + human, True),  # review #105: merge 3 chiều làm lộ ra
            "xoá human thừa": ("lint: x\n" + human, "lint: x\n", True),
            "đổi cách viết": (auto, "merge_hard_exceptions: 'auto'  # giữ\n", False),
            "khoá lặp, dòng sau thắng": (auto, auto + "merge_hard_exceptions: human\n", True),
            "khoá lặp có sẵn, chỉ dời dòng": (auto + "a: 1\n" + human, "a: 1\n" + auto + human, True),  # review #105
        }
        for name, (before, after, want) in cases.items():
            with self.subTest(name):
                self.assertEqual(self.changed(mod, {("xt.yaml", "base"): before, ("xt.yaml", "head"): after}), want)
        both = {("xt.yaml", "base"): auto, ("xt.yaml", "head"): auto}
        self.assertTrue(self.changed(mod, both, broken=("base",)))  # lỗi đọc ≠ vắng → coi như đổi
        self.assertTrue(self.changed(mod, both, broken=("head",)))
        self.assertTrue(self.changed(mod, {}))  # vắng ở cả hai đầu mà nằm trong diff → token không đọc được
        moved = {"filename": "x.yml", "previous_filename": "xt.yaml", "status": "renamed"}
        self.assertTrue(self.changed(moved, {("xt.yaml", "base"): auto}))  # dời đi: auto → (vắng) human
        self.assertFalse(self.changed(moved, {("xt.yaml", "base"): "lint: x\n"}))  # vẫn human
        self.assertTrue(xt._touches_hard_key({"filename": "xt.yaml", "patch": "+lint: x"}))  # thiếu repo/sha
        self.assertFalse(xt._touches_hard_key({"filename": "src/merge_hard_exceptions.py"}))

    PLAN_FILE = "docs/autopilot/PLAN.md"
    NOT_FOUND = "gh api … lỗi: gh: Not Found (HTTP 404)"

    @staticmethod
    def contents(files: dict, broken: tuple = ()):
        """`_gh_one` giả cho REST contents theo (đường, ref): vắng → 404 như gh; ref trong `broken` → lỗi khác (timeout)."""

        def fake(api_path: str) -> dict:
            path, ref = api_path.split("/contents/", 1)[1].rsplit("?ref=", 1)
            if ref in broken:
                raise xt.PrInputError("gh api lỗi: timeout")
            if (path, ref) not in files:
                raise xt.PrInputError(MergeConfigTest.NOT_FOUND)
            body = base64.b64encode(files[path, ref].encode()).decode()
            return {"type": "file", "path": path, "encoding": "base64", "content": body}

        return fake

    def changed(self, f: dict, files: dict, broken: tuple = ()) -> bool:
        with unittest.mock.patch.object(xt, "_gh_one", side_effect=self.contents(files, broken)):
            return xt._touches_hard_key(f, "repos/o/r", "base", "head")

    def modified(self, before: str, after: str) -> bool:
        files = {(self.PLAN_FILE, "base"): before, (self.PLAN_FILE, "head"): after}
        return self.changed({"filename": self.PLAN_FILE, "status": "modified"}, files)

    def test_plan_grant_effect_changes_are_hard(self):
        """ADR-0022: so HIỆU LỰC ủy quyền đáy/đầu PR — fence, viết hoa, xoá dòng đều bị bắt (review: regex trên patch lọt)."""
        sand = "- grant: payments | mode=sandbox | max_per_txn=0\n"
        live = "- grant: payments | mode=live | max_per_txn=1e9\n"
        cases = {
            "thêm dòng": (sand, sand + "- grant: secrets | read_values=false\n", True),
            "sửa dòng": (sand, live, True),
            "viết hoa": (sand, live.replace("grant", "GRANT").replace("mode", "MODE"), True),
            "xoá dòng": (sand, "", True),
            "bỏ fence": ("```\n" + sand + "```\n", sand, True),
            "thêm fence mở": (sand, "```\n" + sand, True),
            "đảo fence": (sand + "```\n" + live + "```\n", "```\n" + sand + "```\n" + live + "```\n", True),
            "chỉ tick task": (sand + "- [ ] `T-001` việc\n", sand + "- [x] `T-001` việc\n", False),
            # review #105: grant lặp bị dòng sau che / dời dòng — hiệu lực không đổi nhưng merge 3 chiều lật được
            "chèn live bị sandbox che": ("x\n" + sand, live + "x\n" + sand, True),
            "dời dòng grant duy nhất": ("x\n" + sand, sand + "x\n", False),  # mỗi nhóm một dòng: merge chỉ ra tập con
            "grant trong fence ở đầu PR": ("```\n" + live + "```\n", "```\n" + live + "```\n# ghi chú\n", True),
            "grant lặp có sẵn": (sand + sand, sand + sand + "# ghi chú\n", True),
            "thêm ghi chú": (sand, "# ghi chú\n" + sand, False),
        }
        for name, (before, after, want) in cases.items():
            with self.subTest(name):
                self.assertEqual(self.modified(before, after), want)

    def test_rename_or_copy_into_plan_is_hard(self):
        """Review lần hai: đáy là CHÍNH đường PLAN, không phải tên file cũ — chuỗi PR dời file có grant vào PLAN.md bị bắt."""
        live = "- grant: payments | mode=live | max_per_txn=1000000\n"
        for status in ("renamed", "copied"):
            with self.subTest(status):
                f = {"filename": self.PLAN_FILE, "previous_filename": "docs/notes.md", "status": status}
                files = {("docs/notes.md", "base"): live, (self.PLAN_FILE, "head"): live}  # PLAN.md chưa có ở đáy
                self.assertTrue(self.changed(f, files))
        moved_away = {"filename": "docs/PLAN2.md", "previous_filename": self.PLAN_FILE, "status": "renamed"}
        self.assertTrue(self.changed(moved_away, {(self.PLAN_FILE, "base"): live}))  # dời đi = grant biến mất
        self.assertFalse(self.changed(moved_away, {(self.PLAN_FILE, "base"): "# PLAN\n"}))  # không có grant nào

    def test_plan_added_removed_and_unreadable(self):
        g = "- grant: payments | mode=sandbox | max_per_txn=0\n"
        add = {"filename": self.PLAN_FILE, "status": "added"}
        rm = {"filename": self.PLAN_FILE, "status": "removed"}
        self.assertTrue(self.changed(add, {(self.PLAN_FILE, "head"): g}))
        self.assertFalse(self.changed(add, {(self.PLAN_FILE, "head"): "# PLAN\n"}))
        self.assertTrue(self.changed(rm, {(self.PLAN_FILE, "base"): g}))
        self.assertFalse(self.changed(rm, {(self.PLAN_FILE, "base"): "# PLAN\n"}))
        mod = {"filename": self.PLAN_FILE, "status": "modified"}
        both = {(self.PLAN_FILE, "base"): g, (self.PLAN_FILE, "head"): g}
        self.assertFalse(self.changed(mod, both))
        self.assertTrue(self.changed(mod, both, broken=("base",)))  # lỗi đọc ≠ vắng → coi như đổi
        self.assertTrue(self.changed(mod, both, broken=("head",)))
        self.assertTrue(xt._touches_hard_key({"filename": self.PLAN_FILE}, "repos/o/r", "", "head"))  # thiếu sha đáy
        self.assertFalse(xt._touches_hard_key({"filename": "docs/other/NOTES.md"}, "repos/o/r", "base", "head"))

    def test_plan_grants_reader_rejects_bad_content(self):
        ok = {"type": "file", "path": self.PLAN_FILE, "encoding": "base64"}

        def read(resp: dict):
            with unittest.mock.patch.object(xt, "_gh_one", return_value=resp):
                return xt._plan_grants("repos/o/r", self.PLAN_FILE, "head")

        body = base64.b64encode(b"- grant: secrets | read_values=false\n").decode()
        for name, bad in {
            "base64 hỏng": {**ok, "content": "!!!"},
            "file lớn": {**ok, "content": "", "encoding": "none"},
            "thiếu encoding": {"type": "file", "path": self.PLAN_FILE, "content": "e30="},
            "không phải UTF-8": {**ok, "content": base64.b64encode(b"\xff\xfe").decode()},
            # Review lần ba: API contents đi theo symlink và trả file ĐÍCH (type file, path khác) → không xác minh được
            "symlink tới file khác": {**ok, "path": "docs/notes.md", "content": body},
            "symlink chưa theo": {"type": "symlink", "path": self.PLAN_FILE, "target": "../notes.md"},
            "thư mục": {"type": "dir", "path": self.PLAN_FILE},
        }.items():
            with self.subTest(name):
                self.assertIsNone(read(bad))
        wrapped = base64.encodebytes(b"- grant: secrets | read_values=false\n" * 3).decode()  # có xuống dòng như GitHub
        self.assertEqual(read({**ok, "content": wrapped}), {"secrets": {"read_values": "false"}})
        with unittest.mock.patch.object(xt, "_gh_one") as one:
            self.assertIsNone(xt._plan_grants("repos/o/r", self.PLAN_FILE, ""))  # ref rỗng = nhánh mặc định: không dùng
            one.assert_not_called()
            one.return_value = {**ok, "content": base64.b64encode(b"").decode()}
            self.assertEqual(xt._plan_grants("repos/o/r", self.PLAN_FILE, None), {})  # ref=None: nhánh mặc định
            self.assertEqual(one.call_args.args, (f"repos/o/r/contents/{self.PLAN_FILE}",))  # không có ?ref=

    def test_404_only_from_gh_http_status(self):
        """Review lần ba: chỉ tin `(HTTP 404)` ở phần stderr của gh — sha có chữ `404` không biến lỗi 502 thành "file vắng"."""
        sha = "a404cccc" + "0" * 32

        def err(msg: str):
            with unittest.mock.patch.object(xt, "_gh_one", side_effect=xt.PrInputError(msg)):
                return xt._plan_grants("repos/o/r", self.PLAN_FILE, sha)

        path = f"repos/o/r/contents/{self.PLAN_FILE}?ref={sha}"
        self.assertIsNone(err(f"gh api {path} lỗi: gh: Server Error (HTTP 502)"))
        self.assertIsNone(err(f"không chạy được gh (timeout {path})"))
        self.assertEqual(err(f"gh api {path} lỗi: gh: Not Found (HTTP 404)"), {})
        # Review lần bốn: 404 do ref sai không phải "file vắng"
        self.assertIsNone(err(f"gh api {path} lỗi: gh: No commit found for the ref {sha} (HTTP 404)"))
        # Chỉ phần stderr sau ` lỗi: ` được tin: chuỗi 404 nằm trong phần lệnh/đường dẫn không làm 502 thành "vắng"
        self.assertIsNone(err("gh api x/Not Found (HTTP 404)/y lỗi: gh: Server Error (HTTP 502)"))

    def test_plan_absent_at_both_ends_is_hard(self):
        """Review lần bốn: file trong diff mà 404 ở cả đáy lẫn đầu = token không đọc được contents (404 thay 403)."""
        self.assertTrue(self.changed({"filename": self.PLAN_FILE, "status": "modified"}, {}))
        self.assertEqual(xt._plan_read("repos/o/r", self.PLAN_FILE, ""), (None, False))

    def test_truncated_file_list_is_hard_and_unwaivable(self):
        """Review lần hai: REST cắt danh sách file ở 3000 → PLAN.md/xt.yaml có thể lọt → luôn người merge, kể cả `auto`."""
        self.assertEqual(xt.merge_hard_reasons(pr(filesTruncated=True), []), [xt.TRUNCATED_REASON])
        d = xt.merge_decision(pr(filesTruncated=True), 3, hard_auto=True)
        self.assertEqual((d["verdict"], d["hard"], d["hard_waived"]), ("human", [xt.TRUNCATED_REASON], []))
        gh = FakeGh(pull={"changed_files": 4000})
        with gh.patch():
            self.assertTrue(xt._pr_rest("7")["filesTruncated"])
        with FakeGh(pull={"changed_files": 3}).patch():
            self.assertNotIn("filesTruncated", xt._pr_rest("7"))  # 3 file trả về = changed_files


class MergeDoctorTest(unittest.TestCase):
    def test_warns_when_l2_but_settings_still_asks_merge(self):
        base = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.assertEqual(xt._doctor_merge(base), [])
        (base / ".claude").mkdir()
        settings = base / ".claude" / "settings.json"
        settings.write_text(json.dumps({"permissions": {"ask": ["Bash(gh pr merge *)"]}}), encoding="utf-8")
        self.assertEqual(xt._doctor_merge(base), [])  # L1: người merge, luật ask không cản gì
        (base / "xt.yaml").write_text("merge_autonomy: L2\n", encoding="utf-8")
        f = xt._doctor_merge(base)
        self.assertEqual((len(f), f[0].code, f[0].level), (1, "merge", "warn"))
        self.assertIn("Bash(gh pr merge *)", f[0].msg)
        settings.write_text(json.dumps({"permissions": {"ask": ["Bash(npm publish*)"]}}), encoding="utf-8")
        self.assertEqual(xt._doctor_merge(base), [])
        settings.write_text("[]", encoding="utf-8")
        self.assertEqual(xt._doctor_merge(base), [])


class MergeCheckCliTest(unittest.TestCase):
    def setUp(self):
        self.base = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.enterContext(unittest.mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(self.base)}))
        commit_base_xt(self.base, "merge_autonomy: L2\n")  # mức tự chủ đọc ở nhánh đích đã commit (D-033)

    def test_hard_auto_from_xt_yaml(self):
        hot = pr(files=[{"path": "src/payment/charge.py", "additions": 1, "deletions": 0}])
        commit_base_xt(self.base, "merge_autonomy: L3\nmerge_hard_exceptions: auto\n")
        rc, out, _ = run_main("merge-check", "--json", "--pr-json", "-", stdin=json.dumps(hot))
        d = json.loads(out)
        # miễn người (ADR-0020) nhưng vẫn cần review sạch ở head: merge-check không gợi merge (AUD-XFEAT-010)
        self.assertEqual((rc, d["verdict"], d["hard"], d["notes"]), (1, "review", [], []))
        self.assertTrue(d["hard_waived"])
        hot_ok = {**hot, "xtReviews": [{"head": "abc1234def", "clean": True, "at": "2026-10-19T10:00:00Z"}]}
        rc, out, _ = run_main("merge-check", "--json", "--pr-json", "-", stdin=json.dumps(hot_ok))
        self.assertEqual((rc, json.loads(out)["verdict"]), (0, "merge"))
        commit_base_xt(self.base, "merge_autonomy: L3\nmerge_hard_exceptions: x\n")
        rc, out, _ = run_main("merge-check", "--pr-json", "-", stdin=json.dumps(hot))
        self.assertEqual(rc, 1)
        self.assertIn("merge_hard_exceptions 'x' không hợp lệ", out)

    def test_pr_json_from_stdin_text_and_json(self):
        rc, out, err = run_main("merge-check", "--pr-json", "-", stdin=json.dumps(pr()))
        self.assertEqual((rc, err), (0, ""))
        self.assertIn("MERGE · PR #7 · làn nhanh", out)
        self.assertIn("→ gh pr merge 7 --squash --match-head-commit abc1234def", out)
        rc, out, _ = run_main("merge-check", "--json", "--pr-json", "-", stdin=json.dumps(pr(isDraft=True)))
        self.assertEqual(rc, 1)
        self.assertEqual(json.loads(out)["verdict"], "wait")
        rc, out, _ = run_main("merge-check", "--pr-json", "-", stdin=json.dumps(pr(state="CLOSED")))
        self.assertEqual((rc, out), (1, "CLOSED · PR #7 · làn nhanh\n  - PR đã CLOSED\n"))  # không có bước kế

    def test_pr_json_file_and_config_note(self):
        f = self.base / "pr.json"
        f.write_text(json.dumps(pr()), encoding="utf-8")
        (self.base / "xt.yaml").write_text("merge_autonomy: L9\n", encoding="utf-8")
        rc, out, _ = run_main("merge-check", "--pr-json", str(f))
        self.assertEqual(rc, 1)
        self.assertIn("HUMAN · PR #7 · làn nhanh", out)
        self.assertIn("merge_autonomy 'L9' không hợp lệ", out)

    def test_fetches_with_rest_only(self):
        gh = FakeGh(real_git=True)
        with gh.patch():
            rc, out, err = run_main("merge-check", "--pr", "7")
        self.assertEqual((rc, err), (0, ""))
        self.assertIn("MERGE · PR #7 · làn nhanh", out)
        self.assertIn("--match-head-commit abc1234def", out)
        self.assertTrue(all(c[:2] == ["gh", "api"] for c in gh.calls))  # không gh pr view, không GraphQL
        self.assertFalse(any("graphql" in " ".join(c) for c in gh.calls))
        self.assertIn("repos/{owner}/{repo}/commits/abc1234def/check-runs?per_page=100", gh.paths())

    def test_rest_is_mapped_like_gh_pr_view(self):
        gh = FakeGh()
        with gh.patch():
            self.assertEqual(
                xt._pr_rest("7"),
                pr(reviewDecision="", baseRefName="main", requiredChecks=[{"context": "test"}]),
            )  # như fixture `gh pr view`
        cases = {
            "merged": ({"merged": True, "state": "closed"}, "state", "MERGED"),
            "đang tính": ({"mergeable": None, "mergeable_state": "unknown"}, "mergeable", "UNKNOWN"),
            "xung đột": ({"mergeable": False, "mergeable_state": "dirty"}, "mergeStateStatus", "DIRTY"),
            "nháp": ({"draft": True}, "isDraft", True),
            "tiêu đề": ({"title": "fix: a"}, "title", "fix: a"),
        }
        for name, (over, key, want) in cases.items():
            with self.subTest(name), FakeGh(pull=over).patch():
                self.assertEqual(xt._pr_rest("7")[key], want)
        runs = [{"name": "e2e", "status": "in_progress", "conclusion": None}]
        with FakeGh(runs=runs, statuses=[{"context": "ci/old", "state": "failure"}]).patch():
            got = xt.merge_decision(xt._pr_rest("7"), autonomy=2)
        self.assertEqual((got["verdict"], got["reasons"]), ("fix", ["CI đỏ: ci/old"]))

    def test_rerun_check_uses_latest_run(self):
        """#58: sửa tiêu đề PR chạy lại `quality` trên CÙNG head — lần cũ đỏ không được che lần mới xanh (như GitHub)."""
        runs = [
            {"id": 1, "name": "quality", "status": "completed", "conclusion": "failure"},
            {"id": 2, "name": "quality", "status": "completed", "conclusion": "success"},
        ]
        with FakeGh(runs=runs).patch():
            got = xt.merge_decision(xt._pr_rest("7"), autonomy=2)
        self.assertEqual(got["verdict"], "merge")
        with FakeGh(runs=list(reversed(runs)), statuses=[]).patch():  # thứ tự trả về không quyết định
            self.assertEqual(xt.merge_decision(xt._pr_rest("7"), autonomy=2)["verdict"], "merge")
        newer_red = [{**runs[0], "id": 3}, runs[1]]
        with FakeGh(runs=newer_red).patch():
            self.assertEqual(xt.merge_decision(xt._pr_rest("7"), autonomy=2)["verdict"], "fix")

    def test_review_decision_from_latest_review_per_user(self):
        def rv(user: str, state: str) -> dict:
            return {"user": {"login": user}, "state": state}

        cases = {
            "không review": ([], "clean", ""),
            "duyệt": ([rv("a", "COMMENTED"), rv("a", "APPROVED")], "clean", "APPROVED"),
            "đòi sửa còn hiệu lực": ([rv("a", "APPROVED"), rv("b", "CHANGES_REQUESTED")], "clean", "CHANGES_REQUESTED"),
            "đòi sửa rồi duyệt": ([rv("b", "CHANGES_REQUESTED"), rv("b", "APPROVED")], "clean", "APPROVED"),
            "đòi sửa bị dismiss": ([rv("b", "CHANGES_REQUESTED"), rv("b", "DISMISSED")], "clean", ""),
            "bị chặn bởi protection": ([rv("a", "COMMENTED")], "blocked", "REVIEW_REQUIRED"),
            "thiếu user": ([{"state": "CHANGES_REQUESTED"}], "clean", ""),
        }
        for name, (reviews, state, want) in cases.items():
            with self.subTest(name), FakeGh(reviews=reviews, pull={"mergeable_state": state}).patch():
                self.assertEqual(xt._pr_rest("7")["reviewDecision"], want)
        with FakeGh(pull={"mergeable_state": "blocked"}).patch():
            got = xt.merge_decision(xt._pr_rest("7"), autonomy=2)
        self.assertEqual((got["verdict"], got["reasons"]), ("human", ["ruleset đòi review của người"]))

    def test_pr_target_number_url_branch(self):
        gh = FakeGh()
        with gh.patch():
            self.assertEqual(xt._pr_target("#7"), ("repos/{owner}/{repo}", "7"))
            self.assertEqual(xt._pr_target("https://github.com/o/r/pull/9"), ("repos/o/r", "9"))
            self.assertEqual(xt._pr_target("feat/x y"), ("repos/{owner}/{repo}", "7"))
            self.assertEqual(xt._pr_target(None), ("repos/{owner}/{repo}", "7"))
        lookups = [p for p in gh.paths() if "/pulls?head=" in p]
        self.assertEqual(
            lookups,
            [
                "repos/{owner}/{repo}/pulls?head={owner}:feat/x%20y&state=open&per_page=100",
                "repos/{owner}/{repo}/pulls?head={owner}:{branch}&state=open&per_page=100",
            ],
        )
        with FakeGh(open_prs=[]).patch():
            rc, _, err = run_main("merge-check")
        self.assertEqual(rc, 2)
        self.assertIn("không có PR mở cho nhánh hiện tại", err)

    def test_rest_bad_data_is_exit_2(self):
        with FakeGh(pull={"head": None}).patch():
            rc, _, err = run_main("merge-check", "--pr", "7")
        self.assertEqual(rc, 2)
        self.assertIn("thiếu `head`", err)
        with FakeGh(raw={"repos/{owner}/{repo}/pulls/7": "[]"}).patch():  # không phải object → {} → thiếu head
            self.assertEqual(run_main("merge-check", "--pr", "7")[0], 2)
        with FakeGh(raw={"repos/{owner}/{repo}/pulls/7": "{hỏng"}).patch():
            rc, _, err = run_main("merge-check", "--pr", "7")
        self.assertEqual(rc, 2)
        self.assertIn("JSON của PR không đọc được", err)

    def test_gh_and_input_errors_are_exit_2(self):
        fail = subprocess.CompletedProcess([], 1, "", "no pull requests found\n")
        cases = {
            "gh lỗi": (unittest.mock.patch.object(xt.subprocess, "run", return_value=fail), "no pull requests found"),
            "thiếu gh": (
                unittest.mock.patch.object(xt.subprocess, "run", side_effect=OSError("gh")),
                "không chạy được gh",
            ),
            "quá giờ": (
                unittest.mock.patch.object(xt.subprocess, "run", side_effect=subprocess.TimeoutExpired("gh", 30)),
                "không chạy được gh",
            ),
        }
        for name, (patch, msg) in cases.items():
            with self.subTest(name), patch:
                rc, out, err = run_main("merge-check", "--pr", "7")
                self.assertEqual((rc, out), (2, ""))
                self.assertIn(msg, err)
        for bad in ("không phải json", "[1, 2]"):
            with self.subTest(bad):
                rc, _, err = run_main("merge-check", "--pr-json", "-", stdin=bad)
                self.assertEqual(rc, 2)
                self.assertIn("JSON của PR không đọc được", err)
        rc, _, err = run_main("merge-check", "--pr-json", str(self.base / "khong-co.json"))
        self.assertEqual(rc, 2)
        self.assertIn("JSON của PR không đọc được", err)


class HardExceptionL3Test(unittest.TestCase):
    """Audit delta đợt B (AUD-HAR-042, D-012, ADR-0016): L3 vẫn để người merge ngoại lệ cứng của `LOOP-STOP-005`."""

    def test_l3_hard_exceptions(self):
        for files, labels in (
            ([{"path": "src/auth/login.py", "additions": 1, "deletions": 0}], []),
            ([{"path": "src/payment/charge.py", "additions": 1, "deletions": 0}], []),
            ([{"path": "src/util/jwt.py", "additions": 1, "deletions": 0}], []),
            ([{"path": "config/.env.production", "additions": 1, "deletions": 0}], []),
            (pr()["files"], [{"name": "risk:pii"}]),
            (pr()["files"], [{"name": "risk:admin"}]),
        ):
            with self.subTest(files[0]["path"], labels=labels):
                d = xt.merge_decision(pr(files=files, labels=labels), 3)
                self.assertEqual((d["verdict"], d["lane"]), ("human", "chuẩn"))
                self.assertTrue(d["hard"])
                self.assertIn("LOOP-STOP-005", d["reasons"][0])
        pending = [{"__typename": "CheckRun", "name": "test", "status": "IN_PROGRESS", "conclusion": ""}]
        early = xt.merge_decision(
            pr(files=[{"path": "src/auth/x.py", "additions": 1, "deletions": 0}], statusCheckRollup=pending), 3
        )
        self.assertEqual((early["verdict"], bool(early["hard"])), ("wait", True))  # guard đọc `hard` ngay lúc mở PR

    def test_l3_soft_standard_lane_still_merges_with_honest_reason(self):
        """AUD-CODE-010: ở L3 làn chuẩn (không ngoại lệ cứng) vẫn merge, lý do ghi đúng làn."""
        for files, labels in (
            ([{"path": ".github/workflows/ci.yml", "additions": 3, "deletions": 1}], []),
            (pr()["files"], [{"name": "risk:upload"}]),
        ):
            d = xt.merge_decision(pr(files=files, labels=labels), 3)
            self.assertEqual((d["verdict"], d["lane"], d["hard"]), ("merge", "chuẩn", []))
            self.assertIn("L3", d["reasons"][0])
            self.assertNotIn("làn nhanh", d["reasons"][0])
        self.assertEqual(xt.merge_decision(pr(), 3)["reasons"], ["làn nhanh, CI xanh, không xung đột"])

    def test_merge_risk_paths_are_hard(self):
        d = xt.merge_decision(pr(), 3, ["src/cart/*"])
        self.assertEqual(d["verdict"], "human")
        self.assertTrue(d["hard"])

    def test_hard_auto_merges_and_keeps_reasons(self):
        """ADR-0020: `merge_hard_exceptions: auto` — ngoại lệ cứng không giữ người ở L3; lý do còn ở `hard_waived`."""
        auth = pr(files=[{"path": "src/auth/login.py", "additions": 1, "deletions": 0}], labels=[{"name": "risk:pii"}])
        d = xt.merge_decision(auth, 3, hard_auto=True)
        self.assertEqual((d["verdict"], d["lane"], d["hard"]), ("merge", "chuẩn", []))
        self.assertEqual(len(d["hard_waived"]), 2)
        self.assertIn("ADR-0020", d["reasons"][-1])
        low = xt.merge_decision(auth, 2, hard_auto=True)
        self.assertEqual(low["verdict"], "human")  # dưới L3 vẫn làn chuẩn
        self.assertIn("ADR-0020", low["reasons"][-1])  # lý do miễn hiện cả khi chưa merge
        key = pr(files=[{"path": "xt.yaml", "additions": 1, "deletions": 0, "hard_key": True}])
        d = xt.merge_decision(key, 3, hard_auto=True)  # PR đổi chính khoá: không tự miễn
        self.assertEqual((d["verdict"], d["hard"], d["hard_waived"]), ("human", [xt.HARD_KEY_REASON], []))
        self.assertEqual(xt.merge_decision(pr(), 3, hard_auto=True)["hard_waived"], [])
        self.assertEqual(xt.merge_decision(auth, 3)["hard_waived"], [])

    def test_same_name_check_from_other_app_not_hidden(self):
        """AUD-CODE-007: check-run cùng tên từ app khác không bị gộp (chỉ lần chạy lại cùng app mới thay lần cũ)."""
        runs = [
            {"id": 10, "name": "test", "status": "completed", "conclusion": "failure", "app": {"id": 1}},
            {"id": 11, "name": "test", "status": "completed", "conclusion": "success", "app": {"id": 2}},
        ]
        with FakeGh(runs=runs).patch():
            self.assertEqual(xt.merge_decision(xt._pr_rest("7"), autonomy=2)["verdict"], "fix")
        rerun = [{**runs[0], "app": {"id": 2}}, runs[1]]
        with FakeGh(runs=rerun).patch():
            self.assertEqual(xt.merge_decision(xt._pr_rest("7"), autonomy=2)["verdict"], "merge")


class GuardHardExceptionTest(unittest.TestCase):
    """ADR-0036 §3: guard chặn phẳng việc bật auto-merge — mọi mức tự chủ, mọi PR (cả ngoại lệ cứng lúc mới mở, CI còn
    chạy), không gọi merge-check; tắt auto-merge vẫn qua. Ngoại lệ cứng với merge ghim head: người merge (ADR-0016)."""

    def test_guard_auto_merge_refuses_hard_exception(self):
        sys.path.insert(0, str(ROOT / ".claude" / "hooks"))
        import guard

        base = {"verdict": "merge", "autonomy": 3, "stacked": False, "repo": "o/r", "hard": [], "eligible": True}
        hard = {**base, "verdict": "human", "hard": ["đường dẫn nhạy cảm (auth): src/auth/x.py"], "eligible": False}
        for d in (base, hard):
            for cmd in ("gh pr merge 7 --auto --squash", "gh pr merge --auto 7 --admin -R o/r"):
                with self.subTest(hard=bool(d["hard"]), cmd=cmd):
                    with unittest.mock.patch.object(guard, "merge_check", return_value=d) as mc:
                        res = dict(guard.apply_policy(guard.bash_decision(cmd, ".")))
                    self.assertEqual((res["decision"], res["code"]), ("deny", "AUTO_MERGE_ENABLE"))
                    mc.assert_not_called()
        with unittest.mock.patch.object(guard, "merge_check", return_value=hard):
            res = dict(
                guard.apply_policy(guard.bash_decision(f"gh pr merge 7 --squash --match-head-commit {'a' * 40}", "."))
            )
        self.assertNotEqual(res["decision"], "allow")  # ngoại lệ cứng: merge ghim head vẫn không tự qua
        dis = dict(guard.apply_policy(guard.bash_decision("gh pr merge 7 --disable-auto", ".")))
        self.assertNotEqual(dis["decision"], "deny")


if __name__ == "__main__":
    unittest.main()


class MergeWatchTest(unittest.TestCase):
    """ADR-0021: `merge-watch` gọi merge-check định kỳ (mặc định 30 s) tới khi verdict ≠ wait."""

    def setUp(self):
        self.base = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.enterContext(unittest.mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(self.base)}))
        commit_base_xt(self.base, "merge_autonomy: L2\n")  # mức tự chủ đọc ở nhánh đích đã commit (D-033)
        self.clock = [0.0]
        self.sleeps: list[int] = []

        def sleep(sec: int) -> None:
            self.sleeps.append(sec)
            self.clock[0] += sec

        self.enterContext(unittest.mock.patch.object(xt.time, "sleep", side_effect=sleep))
        self.enterContext(unittest.mock.patch.object(xt.time, "monotonic", side_effect=lambda: self.clock[0]))

    def watch(self, results: list, *extra: str) -> tuple[int, str]:
        """Chạy merge-watch với chuỗi kết quả merge-check giả: (rc, data, err) hoặc verdict ngắn gọn."""
        seq = iter(results)
        self.pr_next_calls: list[str] = []
        with (
            unittest.mock.patch.object(xt, "_merge_check_json", side_effect=lambda pr: next(seq)),
            unittest.mock.patch.object(xt, "_watch_pr_next", side_effect=self.pr_next_calls.append),
        ):
            rc, out, _ = run_main("merge-watch", "--pr", "7", *extra)
        return rc, out

    def test_watch_prints_pr_next_when_pr_still_open(self):
        """T-1719: merge-watch thoát → in luôn kết quả `pr next` (agent không gọi thêm); PR đã đóng thì không; `pr next`
        không hỏi được PR (exit ≠ 0, lỗi) → im lặng."""
        self.watch([self.d("fix", "CI đỏ", "sửa")])
        self.assertEqual(self.pr_next_calls, ["7"])
        self.watch([self.d("closed", "PR đã MERGED")])
        self.assertEqual(self.pr_next_calls, [])
        out = io.StringIO()
        with (
            unittest.mock.patch.object(
                xt, "cmd_pr", side_effect=lambda a: print("ENABLE-AUTO-MERGE · PR #7\n→ gh x") or 0
            ),
            redirect_stdout(out),
        ):
            xt._watch_pr_next("7")
        self.assertEqual(out.getvalue(), "pr next → ENABLE-AUTO-MERGE · PR #7\n  → gh x\n")
        for bad in (lambda a: 2, unittest.mock.Mock(side_effect=OSError("mạng"))):
            out = io.StringIO()
            with unittest.mock.patch.object(xt, "cmd_pr", side_effect=bad), redirect_stdout(out):
                xt._watch_pr_next("7")
            self.assertEqual(out.getvalue(), "")

    @staticmethod
    def d(verdict: str, reason: str = "x", nxt: str = "") -> tuple[int, dict, str]:
        return 0, {"pr": 7, "verdict": verdict, "reasons": [reason], "next": nxt}, ""

    def test_waits_every_thirty_seconds_then_merge(self):
        rc, out = self.watch([self.d("wait", "CI đang chạy: test")] * 2 + [self.d("merge", "xanh", "gh pr merge 7")])
        self.assertEqual((rc, self.sleeps), (0, [30, 30]))
        self.assertIn("WAIT · PR #7 — CI đang chạy: test", out)
        self.assertIn("→ gh pr merge 7", out)

    def test_merged_exits_zero_without_next_step(self):
        rc, out = self.watch([self.d("wait"), self.d("closed", "PR đã MERGED")])
        self.assertEqual((rc, self.sleeps), (0, [30]))
        self.assertNotIn("→", out)

    def test_action_verdicts_exit_one(self):
        for verdict, reason in (("fix", "CI đỏ: e2e"), ("human", "ngoại lệ cứng"), ("closed", "PR đã CLOSED")):
            with self.subTest(verdict):
                self.sleeps.clear()
                rc, _ = self.watch([self.d(verdict, reason, "làm gì đó")])
                self.assertEqual((rc, self.sleeps), (1, []))

    def test_read_errors_retry_then_give_up(self):
        err = (2, {}, "✗ lỗi mạng\n")
        rc, out = self.watch([err, err, self.d("merge")])  # hồi phục giữa chừng → đếm lại từ đầu
        self.assertEqual((rc, self.sleeps), (0, [30, 30]))
        self.assertIn("lỗi đọc PR (2/3): ✗ lỗi mạng", out)
        self.sleeps.clear()
        rc, out = self.watch([err, err, err])
        self.assertEqual((rc, self.sleeps), (2, [30, 30]))
        self.assertIn("(3/3)", out)

    def test_timeout_exits_three_and_flags_override(self):
        rc, out = self.watch([self.d("wait")] * 10, "--interval", "60", "--max-minutes", "3")
        self.assertEqual((rc, self.sleeps), (3, [60, 60, 60]))  # kiểm ở phút 0,1,2,3; ngủ thêm là quá hạn 3 phút
        self.assertIn("hết 3 phút", out)

    def test_merge_check_json_reuses_merge_check_path(self):
        """Đường thật: `_merge_check_json` = `merge-check --json` (xt.yaml, REST) — không có luật riêng."""
        with FakeGh(real_git=True).patch():
            rc, d, err = xt._merge_check_json("7")
        self.assertEqual((rc, d["verdict"], err), (0, "merge", ""))
        with unittest.mock.patch.object(xt, "load_pr", side_effect=xt.PrInputError("hỏng")):
            rc, d, err = xt._merge_check_json("7")
        self.assertEqual((rc, d), (2, {}))
        self.assertIn("hỏng", err)


class MergeConditionTest(unittest.TestCase):
    """ADR-0028/0036: MỘT điều kiện merge cho merge-check/pr next/guard/steward; stub `merge-gate` chỉ giữ context."""

    AUTO = {"enabledBy": {"login": "a"}, "mergeMethod": "SQUASH"}

    def test_single_merge_condition(self):
        """`merge_eligibility` là MỘT hàm thuần cho merge-check/pr next/guard/steward: pr_next và guard đọc cùng
        `review_gate` nên không thể lệch nhau về "đã đủ review ở head chưa"."""
        d = {"head": "H3", "lane": "chuẩn", "verdict": "merge", "hard": [], "base_merge_of": ["H2"]}

        def r(head: str, clean: bool, at: str) -> dict:
            return {"head": head, "clean": clean, "at": at}

        cases = {
            "thiếu": ([], "missing", False, False),
            "sạch ở head": ([r("H3", True, "1")], "ok", True, True),
            "chặn ở head": ([r("H3", False, "1")], "blocking", False, False),
            "sạch mang qua": ([r("H2", True, "1")], "ok", True, True),
            "chặn ở head thắng sạch mang qua": ([r("H3", False, "1"), r("H2", True, "2")], "blocking", False, False),
            "sạch ở head cũ khác": ([r("H1", True, "1")], "missing", False, False),
        }
        for name, (reviews, state, eligible, auto_ok) in cases.items():
            with self.subTest(name):
                e = xt.merge_eligibility(d, reviews)
                self.assertEqual((e["review"], e["eligible"], e["auto_merge_ok"]), (state, eligible, auto_ok))
                rec = {"reviews": reviews}  # `pr next` đi cùng cổng: thiếu → review, chặn → fix, ok → merge ghim head
                act = xt.pr_next({**d, "pr": 7, "autonomy": 3}, False, rec)["action"]
                self.assertEqual(act, {"missing": "review", "blocking": "fix", "ok": "merge"}[state])
                waiting = xt.pr_next({**d, "pr": 7, "autonomy": 3, "verdict": "wait"}, False, rec)["action"]
                self.assertEqual(waiting, {"missing": "review", "blocking": "fix", "ok": "wait"}[state])
        fast = {**d, "lane": "nhanh"}  # làn nhanh không strict: bỏ qua review (trừ khi từng có review chặn)
        self.assertEqual(xt.merge_eligibility(fast, [])["review"], "na")
        self.assertEqual(xt.merge_eligibility(fast, [r("H0", False, "1")])["review"], "missing")
        self.assertEqual(xt.merge_eligibility(fast, [], standard_seen=True)["review"], "missing")
        hard = {**d, "hard": ["x"], "verdict": "human"}
        e = xt.merge_eligibility(hard, [r("H3", True, "1")])
        self.assertEqual((e["eligible"], e["auto_merge_ok"]), (False, False))

    def test_rest_reads_auto_merge(self):
        """`autoMergeRequest` (REST `auto_merge`) — auto-merge do người bật; `pr next`/steward cần để tắt (ADR-0036)."""
        with FakeGh(pull={"auto_merge": self.AUTO}).patch():
            self.assertEqual(xt._pr_rest("7")["autoMergeRequest"], self.AUTO)
        with FakeGh(pull={"auto_merge": None}).patch():
            self.assertNotIn("autoMergeRequest", xt._pr_rest("7"))

    def test_workflow_runs_base_code_only(self):
        """ADR-0036 §4–§5: `merge-gate.yml` là stub `pull_request` trần, một job `merge-gate`, không chạy mã, không action
        ngoài, token chỉ đọc; ruleset repo khung không còn đòi `merge-gate`."""
        wf = (ROOT / ".github" / "workflows" / "merge-gate.yml").read_text(encoding="utf-8")
        on = wf.split("\non:", 1)[1].split("\npermissions:", 1)[0]
        self.assertEqual(on.strip(), "pull_request:")  # trần: không branches/paths/types — PR nào cũng có check-run
        self.assertNotIn("pull_request_target", wf)
        self.assertNotIn("uses:", wf)
        self.assertNotIn("secrets.", wf)
        self.assertNotIn("xt.py", wf)
        self.assertNotIn("write", wf.split("\npermissions:", 1)[1].split("\njobs:", 1)[0])
        self.assertRegex(wf, r"\njobs:\n  merge-gate:\n")
        self.assertEqual(xt.ci_check_text(wf), [])
        rules = json.loads((ROOT / ".github" / "rulesets" / "main.json").read_text(encoding="utf-8"))["rules"]
        checks = [
            c["context"]
            for r in rules
            if r["type"] == "required_status_checks"
            for c in r["parameters"]["required_status_checks"]
        ]
        self.assertNotIn("merge-gate", checks)
        self.assertIn("quality", checks)
        self.assertIn("merge-gate", xt.NON_CI_CHECKS)  # stub còn đó: xanh không phải bằng chứng CI (AUD-HAR-058)


class PrNextTest(unittest.TestCase):
    """ADR-0025 (D-038): `pr next` chọn MỘT hành động theo merge theo làn (ADR-0024) — hàm thuần + sổ review."""

    H = "a" * 40
    H2 = "b" * 40

    def d(self, **over: Any) -> dict:
        base = {
            "pr": 7,
            "head": self.H,
            "verdict": "wait",
            "lane": "chuẩn",
            "stacked": False,
            "hard": [],
            "reasons": ["CI"],
        }
        base.update({"next": "chờ", "autonomy": 3})
        base.update(over)
        return base

    def act(self, auto: bool = False, rec: dict | None = None, **over: Any) -> dict:
        return xt.pr_next(self.d(**over), auto, rec or {})

    def test_closed_hard_stacked_push_and_human(self):
        self.assertEqual(self.act(verdict="closed", reasons=["PR đã MERGED"])["action"], "done")
        self.assertEqual(self.act(verdict="closed", reasons=["PR đã CLOSED"])["action"], "closed")
        self.assertEqual(self.act(True, hard=["tiền"])["action"], "disable-auto-merge")  # (7) ADR-0036
        self.assertEqual(self.act(hard=["tiền"])["action"], "defer-human")
        self.assertEqual(self.act(True, stacked=True)["action"], "disable-auto-merge")
        self.assertEqual(self.act(stacked=True)["action"], "retarget")
        for v in ("update", "fix"):  # (3) tắt auto-merge TRƯỚC push
            self.assertEqual(self.act(True, verdict=v)["action"], "disable-auto-merge")
            r = self.act(verdict=v, next="làm đi")
            self.assertEqual((r["action"], r["do"]), (v, "làm đi"))
        self.assertEqual(self.act(verdict="human", reasons=["ruleset đòi review của người"])["action"], "defer-human")
        # Review #110: PR dành cho người mà auto-merge đang bật → GitHub sẽ tự merge; tắt trước.
        self.assertEqual(self.act(True, verdict="human")["action"], "disable-auto-merge")

    def test_fast_lane_merges_pinned_or_waits(self):
        r = self.act(lane="nhanh")
        self.assertEqual((r["action"], r["strict"], r["do"]), ("wait", False, "chạy nền xt.py merge-watch --pr 7"))
        self.assertNotIn("fallback", r)  # ADR-0036: khoá `fallback` bỏ — lệnh ghim head nằm trong `do`
        r = self.act(
            lane="nhanh",
            verdict="merge",
            next=f"gh pr merge 7 --squash --match-head-commit {self.H}",
            next_rest="gh api X",
        )
        self.assertEqual(r["action"], "merge")
        self.assertIn(f"--match-head-commit {self.H}", r["do"])
        self.assertIn(f"expectedHeadSha={self.H}", r["do"])  # MCP
        self.assertIn("REST: gh api X", r["do"])  # phiên chặn GraphQL
        self.assertEqual(self.act(True, lane="nhanh")["action"], "disable-auto-merge")  # người bật, chưa đủ: tắt
        # người bật mà đã đủ điều kiện: merge ghim head ngay, an toàn hơn chờ GitHub (D-063)
        self.assertEqual(self.act(True, lane="nhanh", verdict="merge")["action"], "merge")

    def test_standard_lane_needs_clean_review_at_head(self):
        r = self.act()
        self.assertEqual(r["action"], "review")
        self.assertIn("rà cả PR", r["why"])
        stale = {"reviews": [{"head": self.H2, "clean": True}]}
        r = self.act(rec=stale)
        self.assertEqual(r["action"], "review")
        self.assertIn(f"{self.H2}..{self.H}", r["do"])  # (3) head mới → rà H..head
        self.assertEqual(self.act(True, rec=stale)["action"], "disable-auto-merge")  # lỡ push khi còn bật
        dirty = {"reviews": [{"head": self.H, "clean": False}]}
        self.assertEqual(self.act(rec=dirty)["action"], "fix")
        self.assertEqual(self.act(True, rec=dirty)["action"], "disable-auto-merge")
        clean = {"reviews": [{"head": self.H2, "clean": False}, {"head": self.H, "clean": True}]}
        r = self.act(rec=clean)
        self.assertEqual(r["action"], "wait")  # (4) review sạch, CI chưa xanh: chờ
        self.assertTrue(r["why"].startswith("review sạch ở head — chờ: CI"))
        r = self.act(rec=clean, verdict="merge")
        self.assertEqual(
            (r["action"], r["why"]), ("merge", "review sạch ở head — merge-check = merge — merge ghim head")
        )
        self.assertEqual(self.act(True, rec=clean)["action"], "disable-auto-merge")
        self.assertEqual(self.act(True, rec=clean, verdict="merge")["action"], "merge")

    def test_never_enables_auto_merge(self):
        # ADR-0036 §2: một luật mọi mức — merge ghim head khi merge-check = merge, auto-merge người bật mà chưa đủ thì
        # tắt, còn lại chờ; không mức nào bật auto-merge.
        for level in (1, 2, 3):
            with self.subTest(level=level):
                self.assertEqual(self.act(lane="nhanh", autonomy=level)["action"], "wait")
                r = self.act(lane="nhanh", autonomy=level, verdict="merge", next="gh pr merge 7 --match-head-commit x")
                self.assertEqual(
                    (r["action"], r["do"].split(" · ")[0]), ("merge", "gh pr merge 7 --match-head-commit x")
                )
                self.assertEqual(self.act(True, lane="nhanh", autonomy=level)["action"], "disable-auto-merge")
                for v in ("wait", "merge", "update", "fix", "human", "closed"):
                    for auto in (False, True):
                        self.assertNotIn("enable", self.act(auto, lane="nhanh", autonomy=level, verdict=v)["action"])
        clean = {"reviews": [{"head": self.H, "clean": True}]}
        self.assertEqual(self.act(rec=clean, autonomy=2)["action"], "wait")  # L2 làn chuẩn: merge-check vốn trả human

    def test_once_standard_or_blocking_stays_strict(self):
        # (3): PR từng vào làn chuẩn / từng có review báo lỗi chặn → làn nhanh hiện tại vẫn cần review sạch ở head.
        for rec in ({"standard_seen": True}, {"reviews": [{"head": self.H2, "clean": False}, "rác"]}):
            with self.subTest(rec=rec):
                r = self.act(rec=rec, lane="nhanh")
                self.assertEqual((r["action"], r["strict"]), ("review", True))

    def test_review_round_budget_stops_fix_review_loop(self):
        """ADR-0053 (D-209): hai review chưa sạch (một toàn PR + một delta) mà head chưa sạch → `rethink`, không review lần
        ba; review sạch đặt lại đếm; `inconclusive` cũng tính; `pr rethink` mở thêm hai lượt; merge vẫn cần review sạch."""
        b1 = {"head": self.H2, "clean": False, "at": "2026-10-27T01:00:00Z"}
        b2 = {"head": self.H, "clean": False, "at": "2026-10-27T02:00:00Z"}
        self.assertEqual(self.act(rec={"reviews": [b1]})["action"], "review")  # lượt delta còn trong ngân sách
        r = self.act(rec={"reviews": [b1, b2]})
        self.assertEqual(r["action"], "rethink")  # thay `fix`
        self.assertIn("2 lượt review chưa sạch (trần 2", r["why"])
        self.assertIn("xt.py pr rethink --pr 7 --decision D-NNN", r["do"])
        b2_old = {**b2, "head": self.H2}
        self.assertEqual(self.act(rec={"reviews": [b1, b2_old]})["action"], "rethink")  # thay review lần ba
        self.assertEqual(self.act(True, rec={"reviews": [b1, b2]})["action"], "disable-auto-merge")
        inc = {**b1, "inconclusive": True}
        self.assertEqual(self.act(rec={"reviews": [inc, b2]})["action"], "rethink")
        clean_mid = {"head": self.H2, "clean": True, "at": "2026-10-27T01:30:00Z"}
        self.assertEqual(self.act(rec={"reviews": [b1, clean_mid, b2]})["action"], "fix")  # sạch đặt lại đếm
        clean_head = {"head": self.H, "clean": True, "at": "2026-10-27T03:00:00Z"}
        self.assertEqual(self.act(rec={"reviews": [b1, b2, clean_head]}, verdict="merge")["action"], "merge")
        after = [{"decision": "D-009", "at": "2026-10-27T02:30:00+00:00"}]
        self.assertEqual(self.act(rec={"reviews": [b1, b2], "rethinks": after})["action"], "fix")  # mở thêm lượt
        b3 = {"head": self.H, "clean": False, "at": "2026-10-27T04:00:00Z"}
        b4 = {**b3, "at": "2026-10-27T05:00:00Z"}
        self.assertEqual(self.act(rec={"reviews": [b1, b2, b3, b4], "rethinks": after})["action"], "rethink")
        before = [{"decision": "D-008", "at": "2026-10-27T00:00:00+00:00"}, "rác"]
        self.assertEqual(self.act(rec={"reviews": [b1, b2], "rethinks": before})["action"], "rethink")
        self.assertEqual(self.act(rec={"reviews": [b1, b2], "rethinks": "rác"})["action"], "rethink")
        # mốc rethink hỏng không mở lượt (sổ hỏng chỉ chặt hơn); nhiều mốc → mốc MUỘN nhất
        for at in (None, "x", "9999", "2026-10-27T02:30:00"):
            with self.subTest(at=at):
                self.assertEqual(self.act(rec={"reviews": [b1, b2], "rethinks": [{"at": at}]})["action"], "rethink")
        two = [after[0], {"decision": "D-010", "at": "2026-10-27T04:30:00+00:00"}]
        self.assertEqual(self.act(rec={"reviews": [b1, b2, b3, b4], "rethinks": two})["action"], "fix")
        self.assertEqual(self.act(rec={"reviews": [b1, b2, b3, b4], "rethinks": two[::-1]})["action"], "fix")
        self.assertEqual(xt.review_rounds([{"clean": False}, {"clean": False}], after), 2)  # thiếu `at` vẫn tính
        # review cùng giây với mốc rethink tính là trước nó (không đếm); muộn hơn một giây thì đếm
        self.assertEqual(xt.review_rounds([{"clean": False, "at": "2026-10-27T02:30:00Z"}], after), 0)
        self.assertEqual(xt.review_rounds([{"clean": False, "at": "2026-10-27T02:30:01Z"}], after), 1)
        # pha build: chưa có review kết luận chặn → hoãn thành nợ, `inconclusive` không chặn; review chặn vẫn đếm lượt
        self.assertEqual(self.act(lane="chuẩn", delivery_phase="build")["action"], "wait")
        incs = {"reviews": [inc, {**b2, "inconclusive": True}]}
        self.assertEqual(self.act(rec=incs, delivery_phase="build", verdict="merge")["action"], "merge")
        self.assertEqual(self.act(rec={"reviews": [b1, b2]}, delivery_phase="build")["action"], "rethink")


MODELS = ("--reviewer-model", "claude-fable-5-1", "--author-model", "claude-opus-5-5")  # bậc cao hơn (D-161)


class PrNextCliTest(unittest.TestCase):
    def setUp(self):
        self.base = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.enterContext(unittest.mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(self.base)}))
        # Không bao giờ gọi GitHub thật từ test: đăng review được thử riêng ở PrStewardTest với subprocess giả.
        self.published = self.enterContext(unittest.mock.patch.object(xt, "_publish_review", return_value=0))
        commit_base_xt(self.base, "merge_autonomy: L3\n")
        self.head = "c" * 40
        self.big = pr(headRefOid=self.head, files=[{"path": "src/a.py", "additions": 400, "deletions": 0}])

    def nxt(self, p: dict, *extra: str) -> tuple[int, str, str]:
        """`_publish_review` giả = đăng thành công: PR mang dấu của các review đã ghi (`xtReviews`, như REST đọc lại) —
        trừ khi có `review_identity` (dấu của tác giả không phải review). Nguồn review của `pr next` là dấu đã đăng."""
        if "xtReviews" not in p and not p.get("reviewIdentity"):
            rec = xt.read_reviews(self.base).get(str(p.get("number", 7))) or {}
            keys = ("head", "clean", "at", "inconclusive")
            p = {**p, "xtReviews": [{k: r[k] for k in keys if k in r} for r in rec.get("reviews", [])]}
        return run_main("pr", "next", *extra, "--pr-json", "-", stdin=json.dumps(p))

    def test_flow_review_then_merge_and_ledger(self):
        rc, out, _ = self.nxt(self.big)
        self.assertEqual(rc, 0)
        self.assertTrue(out.startswith(f"REVIEW · PR #7 · head {self.head[:7]} — làn chuẩn: rà cả PR"))
        self.assertIn(
            f"→ giao reviewer (năng lực cao hơn) rà cả PR; xong: xt.py pr reviewed --pr 7 --head {self.head}", out
        )
        self.assertTrue(xt.read_reviews(self.base)["7"]["standard_seen"])
        rc, _, err = run_main("pr", "reviewed", "--pr", "7", "--head", "abc1234", "--clean", *MODELS)
        self.assertEqual(rc, 2)
        self.assertIn("SHA đủ 40 ký tự", err)
        rc, out, _ = run_main("pr", "reviewed", "--pr", "7", "--head", self.head, "--blocking")
        self.assertEqual((rc, out), (0, f"✓ PR #7: review còn lỗi chặn ở {self.head[:7]}\n"))
        self.assertEqual(json.loads(self.nxt(self.big, "--json")[1])["action"], "fix")
        run_main("pr", "reviewed", "--pr", "7", "--head", self.head, "--clean", *MODELS)
        rc, out, _ = self.nxt(self.big)
        self.assertIn("MERGE · PR #7", out)
        self.assertIn(f"→ gh pr merge 7 --squash --match-head-commit {self.head} · REST: gh api -X PUT", out)
        self.assertNotIn("--auto", out)
        self.assertNotIn("không được thì", out)
        self.assertEqual(len(xt.read_reviews(self.base)["7"]["reviews"]), 2)

    def marks(self) -> list:
        rec = xt.read_reviews(self.base).get("7") or {}
        return [{k: r[k] for k in ("head", "clean", "at", "inconclusive") if k in r} for r in rec.get("reviews", [])]

    def rethink(self, did: str, p: dict | None = None) -> tuple[int, str, str]:
        p = {"xtReviews": self.marks(), **(p or self.big)}
        return run_main("pr", "rethink", "--pr-json", "-", "--decision", did, stdin=json.dumps(p))

    def decisions(self, root: Path, *lines: str) -> None:
        log = root / "docs/autopilot/DECISIONS.md"
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text("# Nhật ký\n\n" + "\n".join(lines) + "\n", encoding="utf-8")

    @staticmethod
    def soon(seconds: int) -> str:
        """Mốc ISO cách bây giờ `seconds` giây (âm = quá khứ) — quyết định ghi sau review nhưng không ở tương lai xa."""
        now = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
        return (now + datetime.timedelta(seconds=seconds)).isoformat()

    def test_rethink_needs_new_decision_naming_pr(self):
        """ADR-0053 (review #298, D-210/D-211): `pr rethink` chỉ khi `pr next` = `rethink`, D-NNN đúng dạng, câu hỏi nhắc #N,
        mốc không ở tương lai và SAU mọi review chưa sạch đã đăng — D-NNN cũ hay của việc khác không mở lại được; ghi
        `rethinks[]` → `pr next` về `fix`."""
        rc, _, err = self.rethink("D-001")
        self.assertEqual(rc, 2)
        self.assertIn("`pr next` của PR #7 là `review`, không phải `rethink` — làm bước đó trước", err)
        run_main("pr", "reviewed", "--pr", "7", "--head", "d" * 40, "--blocking")
        run_main("pr", "reviewed", "--pr", "7", "--head", self.head, "--blocking")
        r = json.loads(self.nxt(self.big, "--json")[1])
        self.assertEqual(r["action"], "rethink")
        self.assertIn("xt.py loop decide --question 'PR #7: …'", r["do"])  # `do` nói luật #N (review #298)
        later = self.soon(2)
        self.decisions(
            self.base,
            "### D-001 · 2026-01-01T00:00:00+00:00 · PR #7: chọn thư viện log?",  # cũ hơn review
            f"### D-002 · {later} · chọn thư viện log?",  # không nhắc #7
            f"### D-003 · {later} · PR #70 tách?",  # #70 không phải #7
            "### D-004 · hỏng · PR #7 tách?",  # mốc hỏng
            "### D-006 · 2099-01-01T00:00:00+00:00 · PR #7 tách?",  # mốc tương lai: dùng lại được mãi (review #298)
            f"### D-007 · {self.soon(600)} · PR #7 tách?",  # quá độ lệch 5 phút
            f"### D-005 · {later} · PR #7 quá trần review: tách PR?",
        )
        missing = "không có trong docs/autopilot/DECISIONS.md (worktree đang sửa hoặc dự án) với câu hỏi nhắc #7"
        for did, why in (
            ("D-001", "D-001 không ghi SAU review chưa sạch cuối của PR #7 (trước hoặc cùng giây)"),
            ("D-002", missing),
            ("D-003", missing),
            ("D-004", missing),
            ("D-009", missing),
            ("D-006", "D-006 có mốc ở tương lai (2099-01-01T00:00:00+00:00)"),
            ("D-007", "D-007 có mốc ở tương lai"),
            ("D-5", "--decision phải dạng D-NNN, không phải 'D-5'"),
            ("D-005|.*", "--decision phải dạng D-NNN"),
        ):
            with self.subTest(did=did):
                rc, _, err = self.rethink(did)
                self.assertEqual(rc, 2)
                self.assertIn(why, err)
        bad_at = {**self.big, "xtReviews": [{"head": self.head, "clean": False}, {"head": self.head, "clean": False}]}
        self.assertIn("review đã đăng của PR #7 thiếu/hỏng mốc `at`", self.rethink("D-005", bad_at)[2])  # chặt
        auto = {**self.big, "autoMergeRequest": {"enabledAt": "x"}}
        self.assertIn("là `disable-auto-merge`, không phải `rethink`", self.rethink("D-005", auto)[2])
        rc, out, _ = self.rethink("D-005")
        self.assertEqual(
            (rc, out), (0, "✓ PR #7: mở thêm 2 lượt review theo D-005 — chạy lại `xt.py pr next --pr 7`\n")
        )
        self.assertEqual(xt.read_reviews(self.base)["7"]["rethinks"][0]["decision"], "D-005")
        self.assertEqual(json.loads(self.nxt(self.big, "--json")[1])["action"], "fix")
        rc, _, err = self.rethink("D-005")
        self.assertEqual(rc, 2)
        self.assertIn("là `fix`, không phải `rethink`", err)
        self.assertEqual(run_main("pr", "rethink", "--pr-json", "-", "--decision", "D-005", stdin="[]")[0], 2)

    def test_rethink_decision_must_follow_every_unclean_review(self):
        """Review #298 lượt 2: quyết định ghi GIỮA hai review chưa sạch (cũ hơn review cuối) không mở được trần; một D-NNN
        không mở trần hai lần cho cùng PR (kể cả khi mốc của nó sau các review mới, trong độ lệch giờ cho phép)."""
        r1 = {"head": "d" * 40, "clean": False, "at": "2026-10-27T01:00:00Z"}
        r2 = {"head": self.head, "clean": False, "at": "2026-10-27T03:00:00Z"}
        p = {**self.big, "xtReviews": [r1, r2]}
        self.decisions(
            self.base,
            "### D-020 · 2026-10-27T02:00:00+00:00 · PR #7: giữa hai review?",
            f"### D-021 · {self.soon(180)} · PR #7 quá trần: tách?",
        )
        rc, _, err = self.rethink("D-020", p)
        self.assertEqual(rc, 2)
        self.assertIn("D-020 không ghi SAU review chưa sạch cuối của PR #7", err)
        tie = {**self.big, "xtReviews": [r1, {**r2, "at": "2026-10-27T02:00:00Z"}]}  # cùng giây với D-020 → từ chối
        self.assertIn("(trước hoặc cùng giây)", self.rethink("D-020", tie)[2])
        self.assertEqual(self.rethink("D-021", p)[0], 0)
        r3 = {"head": self.head, "clean": False, "at": self.soon(60)}  # sau mốc rethink, trước mốc D-021
        r4 = {**r3, "at": self.soon(120)}
        p2 = {**self.big, "xtReviews": [r1, r2, r3, r4]}
        self.assertEqual(json.loads(self.nxt(p2, "--json")[1])["action"], "rethink")
        rc, _, err = self.rethink("D-021", p2)
        self.assertEqual(rc, 2)
        self.assertIn("D-021 đã mở thêm lượt cho PR #7 — cần quyết định mới", err)

    def test_rethink_reads_decision_of_worktree(self):
        """Review #298 🟠1: `loop decide` gõ trong worktree khác của cùng repo ghi sổ của worktree (`loop_root`) —
        `pr rethink` phải thấy quyết định đó; quyết định ở sổ của dự án vẫn được tra khi đứng trong worktree."""
        run_main("pr", "reviewed", "--pr", "7", "--head", "d" * 40, "--blocking")
        run_main("pr", "reviewed", "--pr", "7", "--head", self.head, "--blocking")
        wt = Path(self.enterContext(tempfile.TemporaryDirectory())) / "wt"
        subprocess.run(["git", "-C", str(self.base), "worktree", "add", "-q", "-b", "lat", str(wt)], check=True)
        decide = ("loop", "decide", "--question", "PR #7 quá trần review: tách?", "--option", "a", "--option", "b")
        with contextlib.chdir(wt), unittest.mock.patch.object(xt, "now_iso", return_value=self.soon(2)):
            self.assertEqual(run_main(*decide, "--choice", "1", "--why", "x", "--revert", "y")[0], 0)
        self.assertTrue((wt / "docs/autopilot/DECISIONS.md").is_file())
        self.assertFalse((self.base / "docs/autopilot/DECISIONS.md").exists())
        r3 = {"head": self.head, "clean": False, "at": self.soon(10)}  # hai lượt mới sau lần rethink đầu
        p2 = {**self.big, "xtReviews": [*self.marks(), r3, {**r3, "at": self.soon(20)}]}
        self.decisions(self.base, f"### D-030 · {self.soon(30)} · PR #7 quá trần lần hai (sổ dự án)?")
        with contextlib.chdir(wt):
            self.assertEqual(self.rethink("D-001")[0], 0)  # sổ của worktree đang sửa
            self.assertEqual(json.loads(self.nxt(p2, "--json")[1])["action"], "rethink")
            self.assertEqual(self.rethink("D-030", p2)[0], 0)  # sổ dự án, đứng trong worktree
        self.assertEqual([r["decision"] for r in xt.read_reviews(self.base)["7"]["rethinks"]], ["D-001", "D-030"])

    def test_reviewed_rerun_is_idempotent(self):
        """AUD-HAR-071 (BASE-DATA-008): chạy lại `pr reviewed` cùng kết quả (thông báo lỗi khuyên chạy lại) không thêm bản
        ghi thứ hai và không đăng comment trùng; lần đăng trước lỗi thì lần chạy lại chỉ đăng bù. Kết quả khác → bản mới."""
        args = ("pr", "reviewed", "--pr", "7", "--head", self.head, "--clean", *MODELS)

        def reviews() -> list:
            return xt.read_reviews(self.base)["7"]["reviews"]

        self.published.return_value = 3  # đăng lỗi: sổ cục bộ vẫn ghi, chưa đánh dấu đã đăng
        self.assertEqual(run_main(*args)[0], 3)
        self.assertEqual((len(reviews()), reviews()[0].get("published")), (1, None))
        self.published.return_value = 0
        rc, out, _ = run_main(*args)  # chạy lại theo lời khuyên: đăng bù, không thêm bản ghi
        self.assertEqual(rc, 0)
        self.assertIn("đã ghi trước đó", out)
        self.assertEqual((len(reviews()), reviews()[0]["published"], self.published.call_count), (1, True, 2))
        at = reviews()[0]["at"]
        self.assertEqual(run_main(*args)[0], 0)  # lần ba: không ghi, không đăng
        self.assertEqual((len(reviews()), reviews()[0]["at"], self.published.call_count), (1, at, 2))
        self.assertEqual(run_main(*args, "--no-publish")[0], 0)
        self.assertEqual(len(reviews()), 1)
        # kết quả khác (lỗi chặn), rồi sạch lại ở cùng head: mỗi lần đổi là một bản ghi mới, đăng lại
        run_main("pr", "reviewed", "--pr", "7", "--head", self.head, "--blocking")
        run_main(*args)
        self.assertEqual([r["clean"] for r in reviews()], [True, False, True])
        self.assertEqual(self.published.call_count, 4)
        # cùng kết quả, khai model khác → bản ghi mới (người rà khác)
        run_main("pr", "reviewed", "--pr", "7", "--head", self.head, "--clean", "--reviewer-model", "gpt-5",
                 "--author-model", "claude-opus-5-5")  # fmt: skip
        self.assertEqual(len(reviews()), 4)

    def test_review_identity_ignores_local_ledger(self):
        """Review #168: có `review_identity` thì `pr next`/steward chỉ tính review đã đăng của reviewer — sổ cục bộ do chính
        tác giả ghi (`pr reviewed --clean`) không mở được merge; cùng một sự thật với `merge_eligibility`."""
        run_main("pr", "reviewed", "--pr", "7", "--head", self.head, "--clean", *MODELS)
        pinned = {**self.big, "reviewIdentity": "rev-bot"}
        got = json.loads(self.nxt(self.big, "--json")[1])
        self.assertEqual(got["action"], "merge")  # không cấu hình: như cũ
        self.assertNotIn("fallback", got)
        self.assertEqual(json.loads(self.nxt(pinned, "--json")[1])["action"], "review")
        published = {**pinned, "xtReviews": [{"head": self.head, "clean": True, "at": "2026-10-19T01:00:00Z"}]}
        self.assertEqual(json.loads(self.nxt(published, "--json")[1])["action"], "merge")
        rec = {"reviews": [{"head": self.head, "clean": True, "at": "1"}]}
        self.assertEqual(xt.with_published(rec, [], True), {"reviews": [], "local_reviews": []})
        self.assertEqual(xt.with_published(rec, [], False), {"reviews": [], "local_reviews": rec["reviews"]})

    def test_review_identity_edited_mark_is_ignored(self):
        def by(updated: str) -> dict:
            return {
                **mark("a" * 40, "clean", "2026-10-19T01:00:00Z", "NONE"),
                "user": {"login": "rev-bot"},
                "updated_at": updated,
            }

        same, edited = by("2026-10-19T01:00:00Z"), by("2026-10-19T02:00:00Z")
        self.assertEqual(len(xt.published_reviews([same], identity="rev-bot")), 1)
        self.assertFalse(xt.published_reviews([edited], identity="rev-bot")[0]["clean"])  # sửa sau khi đăng: không sạch
        self.assertEqual(
            len(xt.published_reviews([{**edited, "author_association": "OWNER"}])), 1
        )  # không cấu hình: như cũ

    def test_review_identity_falls_back_to_working_tree_config(self):
        """Review #168: không đọc được `origin/<base>` (PR chồng, fetch hỏng) thì lấy `review_identity` ở cây làm việc —
        không bỏ trống làm dấu của tác giả được tin."""
        self.assertEqual(xt.review_config(self.base, "origin/nope"), {})
        (self.base / "xt.yaml").write_text("review_identity: rev-bot\n", encoding="utf-8")
        self.assertEqual(xt.review_config(self.base, "origin/nope"), {"review_identity": "rev-bot"})
        self.assertEqual(xt.review_config(self.base, "origin/main"), {})  # ref đọc được: cấu hình đã commit thắng

    def test_inconclusive_review_means_review_again(self):
        """ADR-0029: `pr reviewed --inconclusive` (diff bị cắt, hết ngân sách) không sạch, không chặn: sổ ghi
        `inconclusive`, dấu đăng `verdict=inconclusive`, `review_gate` coi là `missing` → `pr next` đòi review khác ở head;
        review sạch sau đó mở lại; dấu đã đăng được đọc lại thành `inconclusive`."""
        self.nxt(self.big)  # vào làn chuẩn
        rc, out, _ = run_main("pr", "reviewed", "--pr", "7", "--head", self.head, "--inconclusive")
        self.assertEqual((rc, out), (0, f"✓ PR #7: review chưa kết luận (cần review khác) ở {self.head[:7]}\n"))
        self.published.assert_called_with("7", "7", self.head, False, True)
        rec = xt.read_reviews(self.base)["7"]["reviews"][-1]
        self.assertEqual((rec["clean"], rec["inconclusive"]), (False, True))
        d = json.loads(self.nxt(self.big, "--json")[1])
        self.assertEqual(d["action"], "review")
        gate = xt.review_gate({"head": self.head, "lane": "chuẩn"}, [rec])
        self.assertEqual((gate["strict"], gate["state"]), (True, "missing"))
        self.assertFalse(xt.merge_eligibility({"head": self.head, "verdict": "merge"}, [rec])["auto_merge_ok"])
        body = xt.review_comment_body(self.head, False, True)
        self.assertIn("chưa kết luận được", body)
        self.assertIn("verdict=inconclusive -->", body)
        pub = xt.published_reviews(
            [{"body": body, "author_association": "OWNER", "created_at": "2026-10-19T00:00:00Z"}]
        )
        self.assertEqual(pub, [{"head": self.head, "clean": False, "at": "2026-10-19T00:00:00Z", "inconclusive": True}])
        self.assertEqual(xt.review_gate({"head": self.head}, pub)["state"], "missing")  # đã đăng cũng không chặn
        with self.assertRaises(SystemExit):  # --clean/--blocking/--inconclusive loại trừ nhau
            run_main("pr", "reviewed", "--pr", "7", "--head", self.head, "--inconclusive", "--clean", *MODELS)
        run_main("pr", "reviewed", "--pr", "7", "--head", self.head, "--clean", *MODELS)
        self.assertEqual(json.loads(self.nxt(self.big, "--json")[1])["action"], "merge")

    def test_clean_review_needs_valid_models(self):
        def run(*extra: str) -> tuple:
            return run_main("pr", "reviewed", "--pr", "7", "--head", self.head, *extra)

        rc, _, err = run("--clean")
        self.assertEqual(rc, 2)
        self.assertIn("--clean cần --reviewer-model và --author-model", err)
        rc, _, err = run("--clean", "--reviewer-model", "Opus 5.5", "--author-model", "claude-opus-5-5")
        self.assertEqual(rc, 2)
        self.assertIn("cùng họ model", err)
        self.assertNotIn("7", xt.read_reviews(self.base))  # bị từ chối: không ghi gì vào sổ
        rc, _, err = run("--clean", "--reviewer-model", "  ", "--author-model", "opus")
        self.assertEqual(rc, 2)
        self.assertIn("không nhận diện được tên model", err)
        self.assertEqual(run("--clean", "--reviewer-model", "o3", "--author-model", "claude-opus-5-5")[0], 0)  # #162
        # AUD-HAR-064: tên không lộ họ model → không so được; `graphic`/`commander` không chứa họ `phi`/`command` (review #162)
        for vague in ("claude", "reviewer", "Claude Code", "graphic", "commander", "novaX"):
            rc, _, err = run("--clean", "--reviewer-model", vague, "--author-model", "claude-opus-5-5")
            self.assertEqual(rc, 2, vague)
            self.assertIn("không nhận diện được họ model", err)
        self.assertEqual(run("--blocking")[0], 0)  # báo lỗi chặn không cần khai model
        self.assertEqual(run("--clean", *MODELS)[0], 0)
        last = xt.read_reviews(self.base)["7"]["reviews"][-1]
        self.assertEqual((last["reviewer_model"], last["author_model"]), ("claude-fable-5-1", "claude-opus-5-5"))
        self.assertEqual(xt.model_family("claude-sonnet-5-5"), "sonnet")
        self.assertEqual(xt.model_family("My-Model 2"), "mymodel")
        for name, fam in (("phi-4", "phi"), ("o3-mini", "o3"), ("GLM 4.5", "glm"), ("phi4", "phi"), ("glm4.5", "glm")):
            self.assertEqual(xt.model_family(name), fam, name)
        for name in ("command_r", "nova_pro", "o3mini", "GLM_4"):  # review #164: thẻ thật không có dấu ngăn
            self.assertTrue(xt.MODEL_FAMILY_RE.search(name), name)

    def test_clean_review_judges_name_tail(self):
        """Review #249: họ model xét ở đoạn sau `/` cuối (tiền tố nhà cung cấp bỏ) — kiểm tên mơ hồ cũng vậy, không thì
        `haiku/reviewer` lọt như một họ lạ khác nhà cung cấp."""

        def run(rev: str, aut: str) -> int:
            args = ("pr", "reviewed", "--pr", "7", "--head", self.head, "--clean")
            return run_main(*args, "--reviewer-model", rev, "--author-model", aut)[0]

        for rev, aut in (("haiku/reviewer", "claude-opus-5-5"), ("sonnet", "opus/executor-deep"),
                         ("Qwen/QwQ-32B", "Qwen/Qwen3-235B-A22B"), ("ollama/qwq", "llama3.1:70b"),
                         ("opus/", "sonnet"), ("ollama:qwen3-coder", "qwen3-coder"),
                         ("ollama-qwq", "qwq-32b"), ("llamacpp:llama3.1", "llama3.1:70b"),
                         ("gpt4all:gpt-oss", "gpt-oss"), ("llamacpp:qwen3-coder", "qwen3-coder"),
                         ("gpt4all:qwen3-coder", "qwen3-coder"), ("OLLAMA:qwen3-coder", "qwen3-coder"),
                         ("llama.cpp:qwen3-coder", "qwen3-coder"), ("llamafile:qwen3-coder", "qwen3-coder"),
                         ("ollama qwen3-coder", "qwen3-coder"), ("llama.cpp qwen3-coder", "qwen3-coder"),
                         ("ollama.qwen3-coder", "qwen3-coder"), ("llama-server:qwen3-coder", "qwen3-coder"),
                         ("Ollama Qwen3-Coder", "qwen3-coder"), ("ollama", "qwen3-coder"), ("ollama:llamacpp:qwen3-coder", "qwen3-coder")):  # fmt: skip  # AUD-SEC-105: tiền tố bộ chạy không phải họ
            self.assertEqual(run(rev, aut), 2, (rev, aut))
        self.assertEqual(run("openrouter/anthropic/claude-fable-5-1", "anthropic/claude-opus-4-1"), 0)
        self.assertEqual(run("ollama-gemma3:27b", "gemma3:27b"), 2)  # cùng họ gemma sau khi bỏ tiền tố
        self.assertEqual(run("ollama:gemma3:27b", "llama3.1:70b"), 0)  # khác nhà cung cấp vẫn nhận
        cfg = {"author_model_family": "opus", "reviewer_model_family": "haiku/reviewer"}
        self.assertIn("không nhận diện được họ model", xt.review_family_config_error(cfg) or "")

    def test_clean_review_needs_higher_capability(self):
        """D-161 (LOOP-ORCH-005): review sạch do reviewer năng lực CAO HƠN người viết — khác họ Claude so bậc
        haiku < sonnet < opus < fable (effort không bù bậc); cùng họ chỉ nhận khi khai cả hai effort và effort reviewer
        cao hơn; khác nhà cung cấp/họ không có bậc thì máy không xếp hạng được → nhận như D-045."""

        def run(*extra: str) -> tuple:
            return run_main("pr", "reviewed", "--pr", "7", "--head", self.head, "--clean", *extra)

        def last() -> dict:
            return xt.read_reviews(self.base)["7"]["reviews"][-1]

        opus = ("--author-model", "claude-opus-5-5")
        rc, _, err = run("--reviewer-model", "sonnet", *opus)
        self.assertEqual(rc, 2)
        self.assertIn("bậc thấp hơn", err)
        self.assertIn("reviewer phải có năng lực cao hơn người viết (LOOP-ORCH-005)", err)
        low = ("--reviewer-effort", "max", "--author-effort", "low")
        self.assertEqual(
            run("--reviewer-model", "haiku", "--author-model", "sonnet", *low)[0], 2
        )  # effort không bù bậc
        for eff in ((), ("--reviewer-effort", "max"), ("--author-effort", "low"), ("--reviewer-effort", "high",
                    "--author-effort", "high"), ("--reviewer-effort", "low", "--author-effort", "high")):  # fmt: skip
            rc, _, err = run("--reviewer-model", "Opus 5.5", *opus, *eff)
            self.assertEqual(rc, 2, eff)
            self.assertIn("cùng họ", err)
            self.assertIn("--reviewer-effort > --author-effort", err)
        self.assertNotIn("7", xt.read_reviews(self.base))  # bị từ chối: không ghi gì vào sổ
        with self.assertRaises(SystemExit):  # effort ngoài 5 mức: argparse từ chối
            run("--reviewer-model", "opus", *opus, "--reviewer-effort", "ultra", "--author-effort", "low")
        self.assertEqual(run("--reviewer-model", "claude-fable-5-1", *opus)[0], 0)  # bậc cao hơn
        self.assertEqual(run("--reviewer-model", "Fable 5.1", "--author-model", "Opus 5.5")[0], 0)  # tên có dấu cách
        sp = xt.pr_next(  # review #249: lệnh đăng lại trích dẫn giá trị (shlex) — tên có dấu cách không gãy lệnh
            {"pr": 7, "head": self.head, "verdict": "merge", "lane": "chuẩn", "hard": []},
            False,
            xt.with_published({"reviews": [last()]}, []),
        )["do"]
        self.assertIn("--reviewer-model 'Fable 5.1' --author-model 'Opus 5.5'", sp)
        self.assertEqual(run(*shlex.split(sp.split(" --clean", 1)[1]))[0], 0)  # chạy lại đúng lệnh đó: nhận
        self.assertNotIn("reviewer_effort", last())
        rev = ("--reviewer-effort", "low", "--author-effort", "max")
        self.assertEqual(run("--reviewer-model", "opus", "--author-model", "sonnet", *rev)[0], 0)  # so bậc trước effort
        self.assertEqual((last()["reviewer_effort"], last()["author_effort"]), ("low", "max"))
        hi = ("--reviewer-effort", "max", "--author-effort", "high")
        self.assertEqual(run("--reviewer-model", "opus", *opus, *hi)[0], 0)  # cùng họ, effort reviewer cao hơn
        self.assertEqual((last()["reviewer_model"], last()["reviewer_effort"], last()["author_effort"]),
                         ("opus", "max", "high"))  # fmt: skip
        self.assertEqual(run("--reviewer-model", "gpt-5", "--author-model", "gpt-5", *hi)[0], 0)  # họ không bậc
        cross = (("gpt-5", "claude-opus-5-5"), ("claude-haiku-4-5", "gpt-5"), ("mythos", "gpt-5"), ("gemma-3", "o3"))
        for rv, au in cross:  # khác nhà cung cấp: máy không xếp hạng được → nhận
            self.assertEqual(run("--reviewer-model", rv, "--author-model", au)[0], 0, (rv, au))
        # review #247, #249: khác họ CÙNG nhà cung cấp mà một họ chưa có bậc → từ chối, không đoán bậc
        same_vendor = (
            ("claude-haiku-4-5", "claude-mythos-5-1", "mythos"),
            ("Mythos 5", "claude-fable-5-1", "mythos"),
            ("gemma-3-4b", "gemini-2.5-pro", "gemma"),
            ("o4-mini", "gpt-5", "o4"),
            ("codex-mini", "gpt-5", "codex"),
            ("gpt-4o-mini", "o3", "gpt"),
        )
        for rv, au, fam in same_vendor:
            rc, _, err = run("--reviewer-model", rv, "--author-model", au, "--reviewer-effort", "max")
            self.assertEqual(rc, 2, (rv, au))
            self.assertIn(f"họ {fam} chưa có bậc", err)
            self.assertIn("xt.py feedback", err)
            self.assertNotIn("MODEL_TIER", err)  # dự án đích không sửa được (install.py ghi đè)
        self.assertEqual((xt.model_vendor("o4"), xt.model_vendor("llama")), ("openai", "llama"))
        self.assertEqual(
            (xt.model_family("ollama_chat/gpt-oss:20b"), xt.model_family("gemini/gemma-3-27b-it")), ("gpt", "gemma")
        )
        self.assertIsNone(xt.review_capability_error("mythos", "claude-mythos-5-1", "max", "low"))  # cùng họ: effort
        # review #247: chữ Unicode gập hoa/thường ra Latin (`ſ` → s) không làm lộ họ model
        for odd in ("claude-opuſ-5-5", "ſonnet"):
            self.assertIsNone(xt.MODEL_FAMILY_RE.search(odd), odd)
            rc, _, err = run("--reviewer-model", "claude-fable-5-1", "--author-model", odd)
            self.assertEqual(rc, 2, odd)
            self.assertIn("không nhận diện được họ model", err)
        self.assertEqual(xt.review_capability_error("opus", "sonnet"), None)
        self.assertIn("cùng họ", xt.review_capability_error("mythos", "Mythos 2", "high", "high") or "")

    def test_config_effort_follows_config_model(self):
        """Review #247: workflow `pr-review` truyền model reviewer thật bằng cờ, họ tác giả lấy từ xt.yaml — effort cấu
        hình chỉ đi kèm model cấu hình: model từ cờ thì `reviewer_effort` cấu hình không áp, không được ghi vào sổ."""

        def run(*extra: str) -> tuple:
            return run_main("pr", "reviewed", "--pr", "7", "--head", self.head, "--clean", *extra)

        cfg = "merge_autonomy: L3\nauthor_model_family: opus\nauthor_effort: high\nreviewer_effort: max\n"
        (self.base / "xt.yaml").write_text(cfg, encoding="utf-8")
        rc, _, err = run("--reviewer-model", "claude-opus-5-5")
        self.assertEqual(rc, 2)
        self.assertIn("cùng họ", err)
        self.assertIn("effort ?", err)  # effort reviewer cấu hình không áp cho model khai bằng cờ
        self.assertNotIn("7", xt.read_reviews(self.base))
        self.assertEqual(run("--reviewer-model", "claude-opus-5-5", "--reviewer-effort", "max")[0], 0)
        last = xt.read_reviews(self.base)["7"]["reviews"][-1]
        self.assertEqual(
            (last["reviewer_effort"], last["author_model"], last["author_effort"]), ("max", "opus", "high")
        )
        (self.base / "xt.yaml").write_text(cfg + "reviewer_model_family: claude-opus-5-5\n", encoding="utf-8")
        self.assertEqual(run()[0], 0)  # model và effort cùng từ cấu hình → dùng
        last = xt.read_reviews(self.base)["7"]["reviews"][-1]
        self.assertEqual((last["reviewer_model"], last["reviewer_effort"]), ("claude-opus-5-5", "max"))

    def test_reviewed_rerun_with_effort_is_idempotent(self):
        """D-161: effort là một phần danh tính người rà — chạy lại cùng effort không thêm bản ghi, đổi effort thì thêm."""
        args = ("pr", "reviewed", "--pr", "7", "--head", self.head, "--clean", "--reviewer-model", "opus")
        same = (*args, "--author-model", "claude-opus-5-5", "--author-effort", "medium")
        self.assertEqual(run_main(*same, "--reviewer-effort", "high")[0], 0)
        rc, out, _ = run_main(*same, "--reviewer-effort", "high")
        self.assertEqual(rc, 0)
        self.assertIn("đã ghi trước đó", out)
        self.assertEqual(len(xt.read_reviews(self.base)["7"]["reviews"]), 1)
        self.assertEqual(run_main(*same, "--reviewer-effort", "max")[0], 0)
        reviews = xt.read_reviews(self.base)["7"]["reviews"]
        self.assertEqual([r["reviewer_effort"] for r in reviews], ["high", "max"])
        self.assertEqual(self.published.call_count, 2)

    def test_done_prints_no_command(self):
        """Hành động không có lệnh (`done`/`closed`): chỉ in dòng kết luận, không dòng `→` rỗng; không còn `fallback`."""
        rc, out, _ = self.nxt(pr(state="MERGED"))
        self.assertEqual((rc, out), (0, f"DONE · PR #7 · head {pr()['headRefOid'][:7]} — PR đã MERGED\n"))

    def test_small_pr_after_standard_stays_strict_and_bad_input(self):
        self.nxt(self.big)  # ghi standard_seen
        small = pr(headRefOid=self.head)
        self.assertEqual(json.loads(self.nxt(small, "--json")[1])["action"], "review")
        rc, out, _ = self.nxt(pr(number=8))  # PR khác, làn nhanh, chưa từng chuẩn
        self.assertIn("MERGE · PR #8", out)
        self.assertIn("→ gh pr merge 8 --squash --match-head-commit abc1234def", out)  # CI đã xanh
        url = "https://github.com/o/r/pull/8/"  # URL → cùng khoá số PR với `pr next`
        rc, out, _ = run_main("pr", "reviewed", "--pr", url, "--head", self.head, "--clean", *MODELS)
        self.assertEqual(out, f"✓ PR #8: review sạch ở {self.head[:7]}\n")
        self.assertIn("8", xt.read_reviews(self.base))
        for ref in ("#8", "https://github.com/o/r/pull/8#issuecomment-1", "https://github.com/o/r/pull/8/files"):
            rc, out, _ = run_main("pr", "reviewed", "--pr", ref, "--head", self.head, "--clean", *MODELS)
            self.assertEqual(rc, 0, ref)  # cùng khoá "8", cùng kết quả: chạy lại idempotent (AUD-HAR-071)
            self.assertTrue(out.startswith(f"✓ PR #8: review sạch ở {self.head[:7]} (đã ghi trước đó"), (ref, out))
        for bad in ("https://github.com/o/r/issues/9", "abc", "8a"):  # không ghi khoá rác vào sổ (nợ review #110)
            rc, _, err = run_main("pr", "reviewed", "--pr", bad, "--head", self.head, "--clean", *MODELS)
            self.assertEqual(rc, 2, bad)
            self.assertIn("--pr phải là số PR, #N hoặc URL …/pull/N", err)
        for ref in ("08", "８"):  # số 0 đầu, chữ số Unicode → cùng khoá "8" với `pr next` (review #112)
            self.assertEqual(run_main("pr", "reviewed", "--pr", ref, "--head", self.head, "--clean", *MODELS)[0], 0)
        self.assertEqual(sorted(xt.read_reviews(self.base)), ["7", "8"])
        rc, _, err = run_main("pr", "next", "--pr-json", "-", stdin="[1]")
        self.assertEqual(rc, 2)
        self.assertIn("không phải object", err)


class MissingRequiredCheckTest(unittest.TestCase):
    """BLOCKED vì ruleset đòi check không có trên head (không workflow nào sinh) — không phải "cần review" (X-Company#23)."""

    RULES = [
        {"type": "pull_request", "parameters": {"required_approving_review_count": 0}},
        {
            "type": "required_status_checks",
            "parameters": {
                "required_status_checks": [{"context": "test"}, {"context": "dast"}, {"context": "dast"}, {}]
            },
        },
    ]

    def setUp(self):
        self.base = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.enterContext(unittest.mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(self.base)}))
        commit_base_xt(self.base, "merge_autonomy: L3\n")

    def rest(self, **kw):
        with FakeGh(real_git=True, **kw).patch():
            return xt._pr_rest("7")

    def test_blocked_by_missing_check_is_not_review(self):
        p = self.rest(pull={"mergeable_state": "blocked"}, rules=self.RULES)
        self.assertEqual(p["missingRequired"], ["dast"])
        self.assertNotEqual(p["reviewDecision"], "REVIEW_REQUIRED")
        d = xt.merge_decision(p, 3)
        self.assertEqual(d["verdict"], "human")
        self.assertIn("ruleset đòi check bắt buộc không có trên head: dast", d["reasons"][0])
        self.assertIn("GitHub báo BLOCKED vì thiếu check", d["reasons"][0])
        changes = {**p, "reviewDecision": "CHANGES_REQUESTED"}
        self.assertEqual(xt.merge_decision(changes, 3)["verdict"], "fix")  # review đòi sửa vẫn được báo trước

    def test_blocked_without_missing_check_stays_review(self):
        rules = [{"type": "required_status_checks", "parameters": {"required_status_checks": [{"context": "test"}]}}]
        p = self.rest(pull={"mergeable_state": "blocked"}, rules=rules)
        self.assertNotIn("missingRequired", p)
        self.assertEqual(p["reviewDecision"], "REVIEW_REQUIRED")
        self.assertEqual(xt.merge_decision(p, 3)["reasons"], ["ruleset đòi review của người"])

    def test_not_blocked_does_not_read_rules_and_pending_wins(self):
        gh = FakeGh(real_git=True, rules=self.RULES)
        with gh.patch():
            p = xt._pr_rest("7")
        self.assertNotIn("missingRequired", p)
        # rules chỉ đọc một lần (requiredChecks, REC-08) — không đọc thêm để tìm check thiếu khi không BLOCKED
        self.assertEqual(sum("rules/branches" in c for c in gh.paths()), 1)
        pending = {**pr(), "missingRequired": ["dast"]}
        pending["statusCheckRollup"] = [{"__typename": "CheckRun", "name": "x", "status": "IN_PROGRESS"}]
        self.assertEqual(xt.merge_decision(pending, 3)["verdict"], "wait")  # còn check chạy: chờ, chưa kết luận

    def test_rules_unreadable_falls_back(self):
        with unittest.mock.patch.object(xt, "_gh_items", side_effect=xt.PrInputError("403")):
            self.assertEqual(xt._required_specs("repos/o/r", "main"), [])
        with FakeGh(raw={"repos/{owner}/{repo}/rules/branches/rel%2F1": json.dumps([{"type": "x"}])}).patch():
            self.assertEqual(xt._required_specs("repos/{owner}/{repo}", "rel/1"), [])


class BaseMergeCarryTest(unittest.TestCase):
    """D-061: head chỉ là "cập nhật nhánh" sạch của head đã review → review mang sang; steward tự cập nhật nhánh."""

    R = "repos/{owner}/{repo}"
    H, M1 = "1" * 40, "2" * 40

    def setUp(self):
        self.base = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.enterContext(unittest.mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(self.base)}))
        os.environ.pop("GITHUB_STEP_SUMMARY", None)
        commit_base_xt(self.base, "merge_autonomy: L3\n")
        os.environ.pop("GITHUB_ACTIONS", None)  # CI chạy test trong Actions: mặc định cập nhật nhánh khác đi
        os.environ.pop("XT_STEWARD_UPDATE", None)
        xt._CHAIN_CACHE.clear()
        self.addCleanup(xt._CHAIN_CACHE.clear)

    def files(self, blob: str = "b1") -> str:
        return json.dumps({"files": [{"filename": "a.py", "status": "modified", "sha": blob}]})

    def raw(self, **over: str) -> dict:
        r = self.R
        out = {
            f"{r}/commits/{FakeGh.SHA}": json.dumps({"parents": [{"sha": self.M1}, {"sha": "b0"}]}),
            f"{r}/commits/{self.M1}": json.dumps({"parents": [{"sha": self.H}, {"sha": "b9"}]}),
            f"{r}/commits/{self.H}": json.dumps({"parents": [{"sha": "x"}]}),
            f"{r}/compare/base...{FakeGh.SHA}": self.files(),
            f"{r}/compare/base...{self.M1}": self.files(),
            f"{r}/compare/base...{self.H}": self.files(),
        }
        return {**out, **over}

    def chain(self, **over: str) -> list:
        xt._CHAIN_CACHE.clear()  # mỗi ca một bộ dữ liệu giả cho cùng (repo, base, head)
        with FakeGh(raw=self.raw(**over)).patch():
            return xt._base_merge_chain(self.R, "base", FakeGh.SHA)

    def test_chain_rules(self):
        self.assertEqual(self.chain(), [self.M1, self.H])  # hai lần cập nhật nhánh liên tiếp
        self.assertEqual(self.chain(**{f"{self.R}/compare/base...{self.H}": self.files("khac")}), [self.M1])
        self.assertEqual(self.chain(**{f"{self.R}/compare/base...{self.M1}": self.files("khac")}), [])  # đổi phần PR
        self.assertEqual(self.chain(**{f"{self.R}/commits/{FakeGh.SHA}": json.dumps({"parents": [{"sha": "p"}]})}), [])
        many = json.dumps({"files": [{"filename": f"f{i}", "sha": "s"} for i in range(xt.COMPARE_FILES_MAX)]})
        self.assertEqual(self.chain(**{f"{self.R}/compare/base...{FakeGh.SHA}": many}), [])  # bị cắt: không tin
        with unittest.mock.patch.object(xt, "_gh_one", side_effect=xt.PrInputError("403")):
            self.assertEqual(xt._base_merge_chain(self.R, "base", FakeGh.SHA), [])
        self.assertEqual(xt._base_merge_chain(self.R, "", FakeGh.SHA), [])  # không biết nhánh đích: không hỏi
        with unittest.mock.patch.object(
            xt, "_gh_one", side_effect=[{"parents": [{"sha": "a"}, {"sha": "b"}]}, xt.PrInputError("x")]
        ):
            self.assertEqual(xt._base_merge_chain(self.R, "base", FakeGh.SHA), [])

    def test_base_touching_pr_files_blocks_carry(self):
        # review #153: nhánh đích sửa a.py, merge giữ blob của PR ("ours") → tập thay đổi như cũ nhưng gỡ thay đổi của
        # nhánh đích — không mang review
        touch = json.dumps({"files": [{"filename": "a.py", "status": "modified", "sha": "m"}]})
        self.assertEqual(self.chain(**{f"{self.R}/compare/{self.M1}...base": touch}), [])
        self.assertEqual(self.chain(**{f"{self.R}/compare/{self.H}...base": touch}), [self.M1])
        renamed = json.dumps({"files": [{"filename": "b.py", "previous_filename": "a.py", "status": "renamed"}]})
        self.assertEqual(self.chain(**{f"{self.R}/compare/{self.M1}...base": renamed}), [])
        # base.sha của API cũ hơn base thật đã merge vào head: xét cả cha thứ hai của merge commit
        self.assertEqual(self.chain(**{f"{self.R}/compare/{self.M1}...b0": touch}), [])
        other = json.dumps({"files": [{"filename": "z.py", "status": "modified", "sha": "z"}]})
        self.assertEqual(self.chain(**{f"{self.R}/compare/{self.M1}...base": other}), [self.M1, self.H])
        many = json.dumps({"files": [{"filename": f"f{i}", "sha": "s"} for i in range(xt.COMPARE_FILES_MAX)]})
        with FakeGh(raw={f"{self.R}/compare/h...b": many}).patch():
            self.assertTrue(xt._base_touches(self.R, "h", "b", {"a.py"}))  # bị cắt: coi như chạm
        with unittest.mock.patch.object(xt, "_gh_one", side_effect=xt.PrInputError("403")):
            self.assertTrue(xt._base_touches(self.R, "h", "b", {"a.py"}))

    def test_chain_cached_per_head(self):
        self.assertEqual(self.chain(), [self.M1, self.H])  # chain() xoá cache trước khi gọi, rồi nhớ kết quả
        with unittest.mock.patch.object(xt, "_gh_one", side_effect=AssertionError("không gọi lại")):
            self.assertEqual(xt._base_merge_chain(self.R, "base", FakeGh.SHA), [self.M1, self.H])

    def test_pr_rest_and_pr_next_carry_review(self):
        pull = {"base": {"sha": "base", "ref": "main"}}
        with FakeGh(pull=pull, raw=self.raw()).patch():
            p = xt._pr_rest("7")
        self.assertEqual(p["baseMergeOf"], [self.M1, self.H])
        d = xt.merge_decision({**p, "files": [{"path": "src/a.py", "additions": 400, "deletions": 0}]}, 3)
        self.assertEqual(d["lane"], "chuẩn")
        clean = {"reviews": [{"head": self.H, "clean": True}]}
        self.assertEqual(xt.pr_next(d, False, clean)["action"], "merge")  # review ở H mang sang head
        dirty = {"reviews": [{"head": self.H, "clean": False}]}
        self.assertEqual(xt.pr_next(d, False, dirty)["action"], "review")  # review báo lỗi không mang sang
        self.assertEqual(xt.pr_next({**d, "base_merge_of": []}, False, clean)["action"], "review")

    def test_blocking_at_head_wins(self):
        """AUD-HAR-059: review báo lỗi chặn ở đúng head hiện tại không bị review sạch đến muộn ở head cũ (mang qua merge
        nhánh đích) che; review mới hơn ở cùng head vẫn thắng review cũ ở head đó."""
        head, old = "b" * 40, "a" * 40
        d = {"pr": 7, "head": head, "lane": "chuẩn", "verdict": "merge", "autonomy": 3, "base_merge_of": [old]}
        late_clean = {
            "reviews": [
                {"head": head, "clean": False, "at": "2026-10-19T10:00:00Z"},
                {"head": old, "clean": True, "at": "2026-10-19T10:05:00Z"},
            ]
        }
        self.assertEqual(xt.pr_next(d, False, late_clean)["action"], "fix")
        fixed = {"reviews": [*late_clean["reviews"], {"head": head, "clean": True, "at": "2026-10-19T10:09:00Z"}]}
        self.assertEqual(xt.pr_next(d, False, fixed)["action"], "merge")
        self.assertEqual(xt.pr_next(d, False, {"reviews": late_clean["reviews"][1:]})["action"], "merge")

    def test_steward_updates_branch(self):
        cmds = xt._steward_command({"pr": 7, "head": "h", "action": "update"}, "repos/o/r")
        self.assertEqual(
            cmds, [["gh", "api", "-X", "PUT", "repos/o/r/pulls/7/update-branch", "-f", "expected_head_sha=h"]]
        )
        behind = {"mergeable_state": "behind"}
        gh = StewardGh(pull=behind)
        with gh.patch():
            rc, out, _ = run_main("pr", "steward", "--apply")
        self.assertEqual(rc, 0)
        self.assertIn("#7 update ✓", out)
        self.assertEqual(gh.writes[-1][4], f"{self.R}/pulls/7/update-branch")
        # auto-merge đang bật: tắt rồi cập nhật trong cùng lượt
        gh = StewardGh(pull={**behind, "auto_merge": {"merge_method": "squash"}})
        with gh.patch():
            rc, out, _ = run_main("pr", "steward", "--apply")
        self.assertIn("#7 disable-auto-merge ✓ → update ✓", out)
        self.assertEqual(
            [w[2] if w[1] == "pr" else w[4] for w in gh.writes], ["merge", f"{self.R}/pulls/7/update-branch"]
        )
        gh = StewardGh(pull={**behind, "auto_merge": {"merge_method": "squash"}}, fail={"gh api -X PUT": "conflict"})
        with gh.patch():
            rc, out, _ = run_main("pr", "steward", "--apply")
        self.assertEqual(rc, 1)
        self.assertIn("→ update ✗ conflict", out)

    def test_steward_can_update_flag(self):
        cases = [
            ({}, True),
            ({"GITHUB_ACTIONS": "true"}, False),
            ({"GITHUB_ACTIONS": "true", "XT_STEWARD_UPDATE": "on"}, True),
            ({"XT_STEWARD_UPDATE": "off"}, False),
            ({"XT_STEWARD_UPDATE": "lạ"}, False),
            ({"XT_STEWARD_UPDATE": "true"}, True),
            ({"XT_STEWARD_UPDATE": "0"}, False),
        ]
        for env, want in cases:
            with unittest.mock.patch.dict(os.environ, env):
                self.assertEqual(xt._steward_can_update(), want, env)

    def test_steward_no_update_with_github_token(self):
        # review #153: commit cập nhật nhánh do GITHUB_TOKEN tạo không kích CI → workflow đặt XT_STEWARD_UPDATE=off
        self.enterContext(unittest.mock.patch.dict(os.environ, {"XT_STEWARD_UPDATE": "off"}))
        behind = {"mergeable_state": "behind"}
        gh = StewardGh(pull=behind)
        with gh.patch():
            rc, out, _ = run_main("pr", "steward", "--apply")
        self.assertEqual((rc, gh.writes), (0, []))
        self.assertIn("XT_STEWARD_TOKEN", out)
        gh = StewardGh(pull={**behind, "auto_merge": {"merge_method": "squash"}})
        with gh.patch():
            rc, out, _ = run_main("pr", "steward", "--apply")
        self.assertIn("#7 disable-auto-merge ✓ —", out)
        self.assertEqual([w[2] for w in gh.writes], ["merge"])


class StewardGh(FakeGh):
    """FakeGh + lệnh ghi (POST/PUT, `gh pr merge`): ghi lại, trả mã theo `fail` (tiền tố lệnh → stderr lỗi)."""

    def __init__(self, fail: dict | None = None, **kw: Any):
        kw["pull"] = {
            "author_association": "OWNER",
            "user": {"login": "chu"},
            **(kw.get("pull") or {}),
        }
        super().__init__(**{"real_git": True, **kw})  # xt.yaml ở nhánh đích (L3) đọc từ repo tạm của test
        self.fail = fail or {}
        self.writes: list[list[str]] = []

    def respond(self, cmd: list[str], **kw: Any) -> subprocess.CompletedProcess:
        if cmd[:3] == ["gh", "pr", "merge"] or "-X" in cmd:
            self.writes.append(cmd)
            for prefix, err in self.fail.items():
                if " ".join(cmd).startswith(prefix):
                    if err == "oserror":
                        raise OSError("gh vắng")
                    return subprocess.CompletedProcess(cmd, 1, "", err)
            return subprocess.CompletedProcess(cmd, 0, "", "")
        return super().respond(cmd, **kw)


TRUSTED = "OWNER"


def mark(head: str, verdict: str, at: str, assoc: str = TRUSTED) -> dict:
    return {
        "body": f"Review\n\n<!-- xt-review v1 head={head} verdict={verdict} -->",
        "author_association": assoc,
        "created_at": at,
    }


class PrStewardTest(unittest.TestCase):
    """ADR-0027 (D-054): sổ review đăng lên PR + `pr steward` quản PR không cần phiên agent."""

    H = "d" * 40

    def setUp(self):
        self.base = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.enterContext(unittest.mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(self.base)}))
        os.environ.pop("GITHUB_STEP_SUMMARY", None)
        for key in ("GITHUB_ACTIONS", "XT_STEWARD_UPDATE"):  # CI chạy test trong Actions: steward dispatch CI (T-2402)
            os.environ.pop(key, None)
        commit_base_xt(self.base, "merge_autonomy: L3\n")

    def test_comment_marks_only_from_trusted_authors(self):
        body = xt.review_comment_body(self.H, True)
        self.assertIn("sạch", body)
        self.assertNotRegex(body, xt.MODEL_FAMILY_RE)  # không tên model trong artefact (ai_attribution)
        self.assertIn("còn lỗi chặn", xt.review_comment_body(self.H, False))
        comments = [
            mark("e" * 40, "clean", "2026-10-19T02:00:00Z"),
            mark(self.H, "blocking", "2026-10-19T01:00:00Z", "MEMBER"),
            mark("d" * 40, "blocking", "2026-10-19T01:30:00Z", "COLLABORATOR"),
            mark(self.H, "clean", "2026-10-19T03:00:00Z", "NONE"),  # người ngoài: bỏ
            {"body": None, "author_association": TRUSTED},
        ]
        got = xt.published_reviews(comments)
        # MEMBER của org có thể chỉ có quyền đọc: dấu lúc 01:00 bỏ, của COLLABORATOR lúc 01:30 giữ
        self.assertEqual(
            [(r["head"][0], r["clean"], r["at"][11:16]) for r in got], [("d", False, "01:30"), ("e", True, "02:00")]
        )
        rec = {"reviews": [{"head": "f" * 40, "clean": True, "at": "2026-10-19T02:30:00+00:00"}]}
        merged = xt.with_published(rec, got)  # một nguồn (AUD-XFEAT-011): review = dấu đã đăng; sổ cục bộ để đăng lại
        self.assertEqual([r["head"][0] for r in merged["reviews"]], ["d", "e"])
        self.assertEqual(merged["local_reviews"], rec["reviews"])
        self.assertEqual(xt.with_published(rec, None)["reviews"], [])
        self.assertEqual(xt.with_published(rec, ["rác"])["reviews"], [])

    def test_pr_rest_reads_marks_and_pr_next_uses_them(self):
        big = [{"path": "src/a.py", "additions": 400, "deletions": 0}]
        pull = {"head": {"sha": FakeGh.SHA}}
        with FakeGh(pull=pull, comments=[mark("a" * 40, "clean", "2026-10-19T01:00:00Z")]).patch():
            self.assertEqual(xt._pr_rest("7")["xtReviews"][0]["head"], "a" * 40)
        with unittest.mock.patch.object(xt, "_gh_items", side_effect=xt.PrInputError("403")):
            self.assertEqual(xt._published_marks("repos/o/r", "7"), [])  # thiếu quyền đọc comment: chặt hơn, không lỗi
        p = pr(headRefOid=self.H, files=big, xtReviews=[{"head": self.H, "clean": True, "at": "2026-10-19T01:00:00Z"}])
        rc, out, _ = run_main("pr", "next", "--json", "--pr-json", "-", stdin=json.dumps(p))
        self.assertEqual((rc, json.loads(out)["action"]), (0, "merge"))

    def test_publish_review(self):
        args = ("pr", "reviewed", "--pr", "7", "--head", self.H, "--blocking")
        gh = StewardGh()
        with gh.patch():
            rc, out, _ = run_main(*args)
        self.assertEqual(rc, 0)
        self.assertIn("đã đăng review lên PR #7", out)
        post = gh.writes[0]
        self.assertEqual(post[:5], ["gh", "api", "-X", "POST", "repos/{owner}/{repo}/issues/7/comments"])
        self.assertIn(f"head={self.H} verdict=blocking", post[-1])
        gh = StewardGh()
        with gh.patch():  # chạy lại cùng kết quả đã đăng: không đăng trùng (AUD-HAR-071)
            self.assertEqual(run_main(*args)[0], 0)
        self.assertEqual(gh.writes, [])
        h2 = "e" * 40
        gh = StewardGh()
        with gh.patch():
            run_main("pr", "reviewed", "--pr", "https://github.com/o/r/pull/7", "--head", h2, "--blocking")
        self.assertEqual(gh.writes[0][4], "repos/o/r/issues/7/comments")
        for i, fail in enumerate(("gh api -X POST", "oserror")):
            with (
                self.subTest(fail),
                StewardGh(fail={"gh api -X POST": "HTTP 403" if fail != "oserror" else fail}).patch(),
            ):
                rc, _, err = run_main("pr", "reviewed", "--pr", "7", "--head", "f0"[i] * 40, "--blocking")
            self.assertEqual(rc, 3)
            self.assertIn("chưa đăng được review lên PR #7", err)
        gh = StewardGh()
        with gh.patch():
            rc, out, _ = run_main(*args, "--no-publish")
        self.assertEqual((rc, gh.writes), (0, []))
        reviews = xt.read_reviews(self.base)["7"]["reviews"]
        self.assertEqual(len(reviews), 5)  # sổ cục bộ luôn ghi, kể cả khi đăng lỗi
        self.assertEqual([r.get("published") for r in reviews], [True, True, None, None, None])

    def test_steward_dry_run_and_apply(self):
        gh = StewardGh()
        with gh.patch():
            rc, out, _ = run_main("pr", "steward")
        self.assertEqual(rc, 0)
        self.assertTrue(out.startswith("#7 merge — làn nhanh"))
        self.assertEqual(gh.writes, [])  # không --apply: chỉ báo
        summary = self.base / "summary.md"
        gh = StewardGh()
        with gh.patch(), unittest.mock.patch.dict(os.environ, {"GITHUB_STEP_SUMMARY": str(summary)}):
            rc, out, _ = run_main("pr", "steward", "--apply")
        self.assertEqual(rc, 0)
        self.assertIn("#7 merge ✓", out)
        self.assertEqual(
            gh.writes,
            [
                [
                    "gh",
                    "api",
                    "-X",
                    "PUT",
                    "repos/{owner}/{repo}/pulls/7/merge",
                    "-f",
                    "merge_method=squash",
                    "-f",
                    f"sha={FakeGh.SHA}",
                ]
            ],
        )  # merge ghim head, không bật auto-merge (ADR-0036)
        self.assertIn("## pr-steward", summary.read_text(encoding="utf-8"))

    def test_steward_waits_without_required_checks(self):
        """ADR-0036 §2: nhánh đích có hay không có check bắt buộc, luật như nhau — CI chưa xong thì chờ, không ghi gì;
        xanh thì merge ghim head (D-062 hết đối tượng: không còn auto-merge để kìm)."""
        running = [{"name": "test", "status": "in_progress", "conclusion": None}]
        for rules in ([{"type": "pull_request"}], REQUIRED_TEST):
            gh = StewardGh(rules=rules, runs=running)
            with self.subTest(rules=rules), gh.patch():
                rc, out, _ = run_main("pr", "steward", "--apply")
            self.assertEqual((rc, gh.writes), (0, []))
            self.assertIn("#7 wait — làn nhanh — chờ: CI đang chạy: test", out)
            gh = StewardGh(rules=rules)
            with gh.patch():
                rc, out, _ = run_main("pr", "steward", "--apply")
            self.assertEqual(
                (rc, gh.writes),
                (
                    0,
                    [
                        [
                            "gh",
                            "api",
                            "-X",
                            "PUT",
                            "repos/{owner}/{repo}/pulls/7/merge",
                            "-f",
                            "merge_method=squash",
                            "-f",
                            f"sha={FakeGh.SHA}",
                        ]
                    ],
                ),
            )

    def test_pr_next_merges_when_eligible(self):
        # D-063: đủ điều kiện (merge-check = merge) là merge ghim head — cả khi người đã bật auto-merge
        d = xt.merge_decision(pr(), 3)
        self.assertEqual(d["verdict"], "merge")
        self.assertNotIn("base_has_required", d)
        for auto in (False, True):
            got = xt.pr_next(d, auto, {})
            self.assertEqual(
                (got["action"], got["why"]), ("merge", "làn nhanh — merge-check = merge — merge ghim head")
            )
            self.assertIn(f"expectedHeadSha={d['head']}", got["do"])
        pending = xt.merge_decision(
            pr(statusCheckRollup=[{"__typename": "CheckRun", "name": "x", "status": "IN_PROGRESS"}]), 3
        )
        got = xt.pr_next(pending, True, {})  # người bật, CI còn chạy: tắt — auto-merge không ghim head
        self.assertEqual(
            (got["action"], got["do"]),
            ("disable-auto-merge", "gh pr merge 7 --disable-auto (MCP disable_pr_auto_merge)"),
        )
        self.assertEqual(xt.pr_next(pending, False, {})["action"], "wait")

    def test_steward_errors_and_other_actions(self):
        gh = StewardGh(fail={"gh pr merge": "x", "gh api -X PUT": "y"})
        with gh.patch():
            rc, out, _ = run_main("pr", "steward", "--apply")
        self.assertEqual(rc, 1)
        self.assertIn("#7 merge ✗ y", out)
        with StewardGh(fail={"gh pr merge": "oserror", "gh api -X PUT": "oserror"}).patch():
            self.assertEqual(run_main("pr", "steward", "--apply")[0], 1)
        with StewardGh(open_prs=[]).patch():
            self.assertEqual(run_main("pr", "steward")[1], "không có PR mở\n")
        with unittest.mock.patch.object(xt, "_gh_items", side_effect=xt.PrInputError("gh api lỗi")):
            rc, _, err = run_main("pr", "steward")
        self.assertEqual((rc, err), (2, "✗ gh api lỗi\n"))
        with StewardGh(raw={"repos/{owner}/{repo}/pulls/7": "{}"}).patch():  # thiếu head → PrInputError
            rc, out, _ = run_main("pr", "steward", "--pr", "7")
        self.assertEqual(rc, 1)
        self.assertIn("#7 error", out)
        cases = {  # (auto_merge, verdict…) → lệnh steward
            "disable": ({"action": "disable-auto-merge"}, [["gh", "pr", "merge", "7", "--disable-auto"]]),
            "merge": ({"action": "merge"}, 1),
            "enable (không còn hành động này)": ({"action": "enable-auto-merge"}, []),
            "review": ({"action": "review"}, []),
        }
        for name, (over, want) in cases.items():
            with self.subTest(name):
                cmds = xt._steward_command({"pr": 7, "head": self.H, **over}, "repos/o/r")
                self.assertEqual(len(cmds) if isinstance(want, int) else cmds, want)
        self.assertEqual(xt._steward_run([]), "không có lệnh")
        listing = {
            "repos/o/r/pulls?state=open&per_page=100": json.dumps([{"number": 7}]),
            "repos/o/r/rules/branches/main": json.dumps(REQUIRED_TEST),
        }
        one = {"pr": 7, "head": self.H, "action": "wait", "why": "chờ", "applied": False}
        with StewardGh(raw=listing).patch(), unittest.mock.patch.object(xt, "_steward_one", return_value=one) as m:
            self.assertEqual(run_main("pr", "steward", "--repo", "o/r")[1], "#7 wait — chờ\n")
        self.assertEqual(m.call_args[0][:2], ("https://github.com/o/r/pull/7", "repos/o/r"))


class PrStewardTrustTest(unittest.TestCase):
    """Review #141: steward không tự merge PR từ fork/người ngoài; nhãn làn chuẩn bền; `-R` khi --repo."""

    def setUp(self):
        self.base = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.enterContext(unittest.mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(self.base)}))
        os.environ.pop("GITHUB_STEP_SUMMARY", None)
        for key in ("GITHUB_ACTIONS", "XT_STEWARD_UPDATE"):  # CI chạy test trong Actions: steward dispatch CI (T-2402)
            os.environ.pop(key, None)
        commit_base_xt(self.base, "merge_autonomy: L3\n")

    def steward(self, pull: dict, *extra: str) -> tuple[int, str, StewardGh]:
        gh = StewardGh(pull=pull)
        with gh.patch():
            rc, out, _ = run_main("pr", "steward", "--apply", *extra)
        return rc, out, gh

    def test_untrusted_prs_are_left_to_humans(self):
        fork = {
            "head": {"sha": FakeGh.SHA, "repo": {"full_name": "la/r"}},
            "base": {"repo": {"full_name": "o/r", "default_branch": "main"}, "ref": "main"},
        }
        cases = {
            "fork": (fork, "PR từ fork la/r"),
            "người ngoài": ({"author_association": "CONTRIBUTOR", "user": {"login": "x"}}, "tác giả x (CONTRIBUTOR)"),
            "không rõ": ({"author_association": None, "user": None}, "tác giả ? (không rõ)"),
        }
        for name, (pull, why) in cases.items():
            with self.subTest(name):
                rc, out, gh = self.steward(pull)
                self.assertEqual((rc, gh.writes), (0, []))
                self.assertIn(f"#7 defer-human — {why}", out)
        rc, out, gh = self.steward({"author_association": "NONE", "user": {"login": "dependabot[bot]"}})
        self.assertIn("#7 merge ✓", out)
        self.assertEqual(xt.steward_untrusted({"headRepo": "o/r", "repo": "o/r", "authorAssociation": "owner"}), "")

    def test_standard_label_is_added_and_keeps_pr_strict(self):
        big = [{"filename": "src/a.py", "additions": 400, "deletions": 0}]
        raw = {"repos/{owner}/{repo}/pulls/7/files?per_page=100": json.dumps(big)}
        gh = StewardGh(raw=raw)
        with gh.patch():
            rc, out, _ = run_main("pr", "steward", "--apply")
        self.assertIn("#7 review", out)
        self.assertEqual(gh.writes[0][4:], ["repos/{owner}/{repo}/issues/7/labels", "-f", "labels[]=xt-standard-lane"])
        # nhãn có rồi: diff nhỏ lại (làn nhanh) vẫn cần review sạch ở head — không merge
        gh = StewardGh(pull={"labels": [{"name": "xt-standard-lane"}]})
        with gh.patch():
            rc, out, _ = run_main("pr", "steward", "--apply")
        self.assertIn("#7 review", out)
        self.assertEqual(gh.writes, [])
        p = pr(labels=[{"name": "xt-standard-lane"}])
        rc, out, _ = run_main("pr", "next", "--json", "--pr-json", "-", stdin=json.dumps(p))
        self.assertEqual(json.loads(out)["action"], "review")

    def test_repo_flag_pins_gh_pr_merge_and_is_validated(self):
        listing = {
            "repos/o/r/pulls?state=open&per_page=100": json.dumps([{"number": 7}]),
            "repos/o/r/rules/branches/main": json.dumps(REQUIRED_TEST),
        }
        auto = {"merge_method": "squash"}
        gh = StewardGh(raw=listing, pull={"auto_merge": auto})
        listing["repos/o/r/pulls/7"] = json.dumps(gh.pull)  # đọc lại PR trước khi làm (AUTO-05)
        one = {"pr": 7, "head": FakeGh.SHA, "action": "disable-auto-merge", "why": "x"}
        self.assertEqual(xt._steward_command(one, "repos/o/r")[0][:3], ["gh", "pr", "merge"])
        running = [{"__typename": "CheckRun", "name": "test", "status": "IN_PROGRESS", "conclusion": ""}]
        rest = {**pr(statusCheckRollup=running), "author": "chu", "authorAssociation": "OWNER", "baseRefName": "main"}
        with unittest.mock.patch.object(xt, "_pr_rest", return_value={**rest, "autoMergeRequest": auto}), gh.patch():
            rc, out, _ = run_main("pr", "steward", "--apply", "--repo", "o/r")
        # `gh pr merge` duy nhất còn lại (tắt auto-merge người bật) ghim đúng repo đã đánh giá (review #141)
        self.assertEqual(gh.writes[0], ["gh", "pr", "merge", "-R", "o/r", "7", "--disable-auto"])
        rc, _, err = run_main("pr", "steward", "--repo", "https://github.com/o/r")
        self.assertEqual(rc, 2)
        self.assertIn("--repo phải dạng owner/repo", err)


class SeqGh(StewardGh):
    """StewardGh mà `pulls/7` trả lần lượt từng trạng thái (cái cuối lặp lại): mô phỏng GitHub đổi giữa lúc steward xét
    PR và lúc làm (lượt song song đã làm, push mới, merge); "FAIL" = gh lỗi."""

    def __init__(self, states: list, **kw: Any):
        super().__init__(**kw)
        self.states = [s if s == "FAIL" else {**self.pull, **s} for s in states]

    def respond(self, cmd: list[str], **kw: Any) -> subprocess.CompletedProcess:
        if cmd[:2] == ["gh", "api"] and cmd[-1].endswith("/pulls/7"):
            self.calls.append(cmd)
            state = self.states.pop(0) if len(self.states) > 1 else self.states[0]
            if state == "FAIL":
                return subprocess.CompletedProcess(cmd, 1, "", "HTTP 502")
            return subprocess.CompletedProcess(cmd, 0, json.dumps(state), "")
        return super().respond(cmd, **kw)


class StewardEventsTest(unittest.TestCase):
    """AUTO-05 (T-1517): steward theo sự kiện `check_suite`/`workflow_run`; hành động idempotent theo (repo, PR, head,
    hành động) — đọc lại trạng thái GitHub trước khi làm; sự kiện lặp/sai thứ tự/chạy lại sau restart không lặp tác dụng
    phụ."""

    OLD = "0" * 40

    def setUp(self):
        self.base = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.enterContext(unittest.mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(self.base)}))
        os.environ.pop("GITHUB_STEP_SUMMARY", None)
        for key in ("GITHUB_ACTIONS", "XT_STEWARD_UPDATE"):  # CI chạy test trong Actions: steward dispatch CI (T-2402)
            os.environ.pop(key, None)
        commit_base_xt(self.base, "merge_autonomy: L3\n")

    def event(self, payload: Any, name: str = "event.json") -> str:
        path = self.base / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return str(path)

    def check_suite(self, *heads: str) -> dict:
        return {
            "action": "completed",
            "check_suite": {
                "head_sha": FakeGh.SHA,
                "pull_requests": [{"number": 7, **({"head": {"sha": h}} if h else {})} for h in heads],
            },
        }

    def test_steward_events_payload_parsing(self):
        self.assertEqual(xt.steward_event_prs(self.check_suite("")), {"7": FakeGh.SHA})  # thiếu head PR: head sự kiện
        run = {
            "workflow_run": {
                "head_sha": "b" * 40,
                "pull_requests": [
                    {"number": 9, "head": {"sha": "c" * 40}},
                    {"number": True},  # bool không phải số PR
                    {"number": 0},
                    {"number": "7"},  # chuỗi: payload lạ, bỏ
                    "rác",
                ],
            }
        }
        self.assertEqual(xt.steward_event_prs(run), {"9": "c" * 40})
        for junk in (
            {},
            {"check_suite": None},
            {"check_suite": {"pull_requests": {"number": 7}}},
            {"workflow_run": []},
        ):
            with self.subTest(junk=junk):
                self.assertEqual(xt.steward_event_prs(junk), {})  # không gắn PR → mọi PR mở

    def test_steward_events_only_event_prs_are_reconciled(self):
        gh = StewardGh(open_prs=[{"number": 7}, {"number": 8}])
        with gh.patch():
            rc, out, _ = run_main("pr", "steward", "--apply", "--event", self.event(self.check_suite(FakeGh.SHA)))
        self.assertEqual(rc, 0)
        self.assertEqual(out, f"#7 merge ✓ — {out.split(' — ', 1)[1]}")
        self.assertFalse(any("pulls?state=open" in p for p in gh.paths()))  # không quét mọi PR
        self.assertEqual(
            gh.writes,
            [
                [
                    "gh",
                    "api",
                    "-X",
                    "PUT",
                    "repos/{owner}/{repo}/pulls/7/merge",
                    "-f",
                    "merge_method=squash",
                    "-f",
                    f"sha={FakeGh.SHA}",
                ]
            ],
        )
        # sự kiện không gắn PR (push lên nhánh đích, PR từ fork) hoặc payload không phải object → quét mọi PR mở như lịch
        for payload in ({"check_suite": {"head_sha": FakeGh.SHA, "pull_requests": []}}, ["không phải object"]):
            gh = StewardGh()
            with self.subTest(payload=payload), gh.patch():
                rc, out, _ = run_main("pr", "steward", "--event", self.event(payload))
            self.assertEqual(rc, 0)
            self.assertTrue(any("pulls?state=open" in p for p in gh.paths()))
        # `--pr` thắng `--event`
        gh = StewardGh()
        with gh.patch():
            rc, out, _ = run_main("pr", "steward", "--pr", "7", "--event", str(self.base / "vắng.json"))
        self.assertEqual(rc, 0)

    def test_steward_events_bad_payload_file(self):
        bad = self.base / "bad.json"
        bad.write_text("{không phải json", encoding="utf-8")
        for path in (str(bad), str(self.base / "vắng.json")):
            with self.subTest(path=path), StewardGh().patch():
                rc, _, err = run_main("pr", "steward", "--apply", "--event", path)
            self.assertEqual(rc, 2)
            self.assertIn("không đọc được payload sự kiện", err)

    def test_steward_events_out_of_order_acts_on_current_head(self):
        # sự kiện của head cũ đến sau push mới: không làm theo head trong payload, xét và ghim head hiện tại
        gh = StewardGh()
        with gh.patch():
            rc, out, _ = run_main(
                "pr", "steward", "--apply", "--json", "--event", self.event(self.check_suite(self.OLD))
            )
        got = json.loads(out)[0]
        self.assertEqual((rc, got["action"], got["applied"]), (0, "merge", True))
        self.assertIn("sự kiện cho head cũ 0000000 — đã xét head hiện tại abc1234", got["note"])
        self.assertEqual(got["key"], f"{{owner}}/{{repo}}#7@{FakeGh.SHA}:merge")
        self.assertEqual(gh.writes[0][-1], f"sha={FakeGh.SHA}")
        self.assertNotIn(self.OLD, json.dumps(gh.writes))

    def test_steward_events_duplicate_or_restart_does_not_repeat(self):
        ev = self.event(self.check_suite(FakeGh.SHA))
        on = {"auto_merge": {"merge_method": "squash"}}
        running = [{"name": "test", "status": "in_progress", "conclusion": None}]
        # CI chưa xong: chờ ở mọi lượt (sự kiện lặp / re-run sau restart), không ghi gì
        for _ in range(2):
            gh = StewardGh(runs=running)
            with gh.patch():
                rc, out, _ = run_main("pr", "steward", "--apply", "--event", ev)
            self.assertEqual((rc, gh.writes), (0, []))
            self.assertIn("#7 wait", out)
        # người bật auto-merge khi CI còn chạy: lần 1 tắt; GitHub ghi nhận → lần 2 (sự kiện lặp) chỉ chờ
        first, second = StewardGh(runs=running, pull=on), StewardGh(runs=running)
        for gh in (first, second):
            with gh.patch():
                rc, out, _ = run_main("pr", "steward", "--apply", "--event", ev)
            self.assertEqual(rc, 0)
        self.assertEqual(first.writes, [["gh", "pr", "merge", "7", "--disable-auto"]])
        self.assertEqual(second.writes, [])
        self.assertIn("#7 wait", out)
        # lượt song song đã tắt giữa lúc xét và lúc làm: đọc lại thấy đã tắt → bỏ qua, không lỗi
        gh = SeqGh([on, {}], runs=running)
        with gh.patch():
            rc, out, _ = run_main("pr", "steward", "--apply", "--event", ev)
        self.assertEqual((rc, gh.writes), (0, []))
        self.assertIn(f"bỏ qua {{owner}}/{{repo}}#7@{FakeGh.SHA}:disable-auto-merge — auto-merge đã tắt", out)
        # lượt song song đã merge giữa lúc xét và lúc làm: không merge lần hai
        gh = SeqGh([{}, {"merged": True, "state": "closed"}])
        with gh.patch():
            rc, out, _ = run_main("pr", "steward", "--apply", "--event", ev)
        self.assertEqual((rc, gh.writes), (0, []))
        self.assertIn(f"bỏ qua {{owner}}/{{repo}}#7@{FakeGh.SHA}:merge — PR đã đóng/merge", out)
        # restart sau khi PR đã merge: steward thấy done, không ghi gì
        gh = StewardGh(pull={"merged": True, "state": "closed"})
        with gh.patch():
            rc, out, _ = run_main("pr", "steward", "--apply", "--event", ev)
        self.assertEqual((rc, gh.writes), (0, []))

    def test_steward_events_state_changed_before_action(self):
        on = {"auto_merge": {"merge_method": "squash"}}
        cases = {
            "head đổi": ([{}, {"head": {"sha": "f" * 40}}], "head đổi abc1234 → fffffff"),
            "đã merge": ([{}, {"merged": True, "state": "closed"}], "PR đã đóng/merge"),
            "đã đóng": ([{}, {"state": "closed"}], "PR đã đóng/merge"),
            "head vắng": ([{}, {"head": None}], "→ ?"),
        }
        for name, (states, why) in cases.items():
            gh = SeqGh(states)
            with self.subTest(name), gh.patch():
                rc, out, _ = run_main("pr", "steward", "--apply")
            self.assertEqual((rc, gh.writes), (0, []))
            self.assertIn(why, out)
        # tắt auto-merge mà lượt khác đã tắt → bỏ qua; còn bật → tắt
        hold = {"pr": 7, "head": FakeGh.SHA, "action": "disable-auto-merge", "why": "giữ"}
        for states, writes in (([{}], 0), ([on], 1)):
            gh = SeqGh(states)
            with gh.patch(), unittest.mock.patch.object(xt, "pr_next", return_value=dict(hold)):
                rc, out, _ = run_main("pr", "steward", "--apply")
            self.assertEqual((rc, len(gh.writes)), (0, writes))
        self.assertIn("✓", out)
        # merge khi PR còn mở, đúng head: làm
        gh = SeqGh([{}])
        merge = {**hold, "action": "merge"}
        with gh.patch(), unittest.mock.patch.object(xt, "pr_next", return_value=merge):
            rc, out, _ = run_main("pr", "steward", "--apply")
        self.assertEqual((rc, len(gh.writes)), (0, 1))
        # không đọc lại được PR: không làm mù, run đỏ để lượt sau thử lại
        gh = SeqGh([{}, "FAIL"])
        with gh.patch():
            rc, out, _ = run_main("pr", "steward", "--apply")
        self.assertEqual((rc, gh.writes), (1, []))
        self.assertIn("không đọc lại được PR trước khi làm", out)

    def test_steward_events_workflow_triggers(self):
        text = (ROOT / ".github/workflows/pr-steward.yml").read_text(encoding="utf-8")
        self.assertEqual(xt.ci_check_text(text), [])
        on = text.split("\non:\n", 1)[1].split("\npermissions:", 1)[0]
        self.assertIn("check_suite:\n    types: [completed]", on)
        self.assertRegex(on, r"workflow_run:[^\n]*\n    workflows: \[CI\]\n    types: \[completed\]")
        for trigger in (
            "issue_comment",
            "workflow_run",
        ):  # AUD-CI-015: ghi lý do bỏ qua dangerous-triggers
            self.assertRegex(on, rf"\n  {trigger}: # zizmor: ignore\[dangerous-triggers\] — \S")
        self.assertNotRegex(on, r"pull_request(_target)?:")  # không chạy trong ngữ cảnh PR
        self.assertIn('--event "$GITHUB_EVENT_PATH"', text)
        self.assertIn("pr-steward-${{", text)  # nhóm concurrency theo PR: sự kiện PR khác không thay lượt đang chờ


class StewardFollowupTest(unittest.TestCase):
    """Mục 🟢 sau #140/#141: MEMBER của org có quyền ghi; lỗi gắn nhãn hiện ra summary."""

    PERM = "repos/{owner}/{repo}/collaborators/chu/permission"

    def setUp(self):
        self.base = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.enterContext(unittest.mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(self.base)}))
        os.environ.pop("GITHUB_STEP_SUMMARY", None)
        for key in ("GITHUB_ACTIONS", "XT_STEWARD_UPDATE"):  # CI chạy test trong Actions: steward dispatch CI (T-2402)
            os.environ.pop(key, None)
        commit_base_xt(self.base, "merge_autonomy: L3\n")
        xt._WRITER_CACHE.clear()
        self.addCleanup(xt._WRITER_CACHE.clear)

    def steward(self, permission: str, **kw: Any) -> tuple[int, str, StewardGh]:
        raw = {self.PERM: json.dumps({"permission": permission}), **kw.pop("raw", {})}
        gh = StewardGh(pull={"author_association": "MEMBER", "user": {"login": "chu"}}, raw=raw, **kw)
        with gh.patch():
            rc, out, _ = run_main("pr", "steward", "--apply")
        return rc, out, gh

    def test_org_member_with_write_access_is_trusted(self):
        for perm in ("admin", "write"):
            with self.subTest(perm):
                xt._WRITER_CACHE.clear()
                rc, out, gh = self.steward(perm)
                self.assertIn("#7 merge ✓", out)
                self.assertIn(self.PERM, gh.paths())
        xt._WRITER_CACHE.clear()
        rc, out, gh = self.steward("read")
        self.assertEqual(gh.writes, [])
        self.assertIn("#7 defer-human — tác giả chu (MEMBER)", out)
        with unittest.mock.patch.object(xt, "_gh_one", side_effect=xt.PrInputError("403")):
            self.assertFalse(xt.repo_writer("repos/o/r", "chu"))  # không hỏi được quyền → không tin
        self.assertIsNone(xt._member_can_write("repos/o/r", "CONTRIBUTOR", "chu"))  # không hỏi khi không phải MEMBER

    def test_permission_roles_and_cache(self):
        cases = {  # (permission cũ, role_name) → quyền ghi
            ("write", "maintain"): True,
            ("read", "maintain"): True,  # role_name mới đủ
            ("read", "triage"): False,
            ("none", ""): False,
        }
        for (perm, role), want in cases.items():
            with (
                self.subTest(role=role),
                unittest.mock.patch.object(xt, "_gh_one", return_value={"permission": perm, "role_name": role}),
            ):
                xt._WRITER_CACHE.clear()
                self.assertIs(xt.repo_writer("repos/o/r", "chu"), want)
        xt._WRITER_CACHE.clear()
        with unittest.mock.patch.object(xt, "_gh_one", side_effect=xt.PrInputError("403")) as one:
            xt.repo_writer("repos/o/r", "chu")
            xt.repo_writer("repos/o/r", "chu")
        self.assertEqual(one.call_count, 2)  # lỗi không được nhớ
        with unittest.mock.patch.object(xt, "_gh_one", return_value={"permission": "write"}) as one:
            self.assertTrue(xt.repo_writer("repos/o/r", "chu"))
            self.assertTrue(xt.repo_writer("repos/o/r", "chu"))
            self.assertEqual(one.call_count, 1)  # nhớ trong WRITER_TTL
            with unittest.mock.patch.object(xt.time, "monotonic", return_value=time.monotonic() + xt.WRITER_TTL + 1):
                xt.repo_writer("repos/o/r", "chu")
            self.assertEqual(one.call_count, 2)  # hết hạn → hỏi lại

    def test_member_review_marks_count_only_with_write_access(self):
        def member(login: str) -> dict:
            return {**mark("a" * 40, "clean", "2026-10-19T01:00:00Z", "MEMBER"), "user": {"login": login}}

        raw = {
            "repos/{owner}/{repo}/collaborators/ghi/permission": json.dumps({"permission": "write"}),
            "repos/{owner}/{repo}/collaborators/doc/permission": json.dumps({"permission": "read"}),
        }
        with FakeGh(raw=raw, comments=[member("ghi"), member("doc"), member("")]).patch():
            got = xt._published_marks("repos/{owner}/{repo}", "7")
        self.assertEqual(len(got), 1)
        self.assertEqual(xt.published_reviews([member("ghi")], {"ghi"})[0]["head"], "a" * 40)
        self.assertEqual(xt.published_reviews([member("ghi")]), [])

    def test_published_reviews_identity(self):
        def by(login: str, assoc: str = TRUSTED) -> dict:
            return {**mark("a" * 40, "clean", "2026-10-19T01:00:00Z", assoc), "user": {"login": login}}

        # có `review_identity`: chỉ đúng tài khoản reviewer (không phân biệt hoa/thường); chủ repo/tác giả đăng dấu không tính
        got = xt.published_reviews([by("Rev-Bot", "NONE"), by("chu")], identity="rev-bot")
        self.assertEqual(len(got), 1)
        self.assertEqual(xt.published_reviews([by("chu")], identity="rev-bot"), [])
        self.assertEqual(xt.published_reviews([{**by("x"), "user": None}], identity="rev-bot"), [])
        # không cấu hình: giữ hành vi theo author_association
        self.assertEqual(len(xt.published_reviews([by("chu")])), 1)
        with FakeGh(comments=[by("chu"), by("rev-bot", "NONE")]).patch():
            self.assertEqual(len(xt._published_marks("repos/{owner}/{repo}", "7", "rev-bot")), 1)

    def test_review_identity_read_from_committed_xt_yaml(self):
        base = Path(self.enterContext(tempfile.TemporaryDirectory()))
        commit_base_xt(
            base, "review_identity: rev-bot\nauthor_model_family: opus\nreviewer_model_family: gpt\n", "x: 1\n"
        )
        cfg = xt.review_config(base, "HEAD")
        self.assertEqual(
            cfg, {"review_identity": "rev-bot", "author_model_family": "opus", "reviewer_model_family": "gpt"}
        )
        self.assertEqual(xt.review_config(base, "origin/nope"), {})  # không đọc được ref → vắng

    def test_same_family_rejected(self):
        keys = {"author_model_family": "claude-opus-5-5", "reviewer_model_family": "Opus 5.5"}
        self.assertIn("cùng họ", xt.review_family_config_error(keys) or "")
        self.assertIn("không nhận diện", xt.review_family_config_error({**keys, "reviewer_model_family": "xyz"}) or "")
        self.assertIsNone(xt.review_family_config_error({**keys, "reviewer_model_family": "gpt-5"}))
        self.assertIsNone(xt.review_family_config_error({"author_model_family": "opus"}))  # khai thiếu → không kiểm
        ns = unittest.mock.Mock(
            clean=True, reviewer_model=None, author_model=None, reviewer_effort=None, author_effort=None
        )
        self.assertIn("cùng họ", xt._review_models_error(ns, keys) or "")
        ns = unittest.mock.Mock(
            clean=True, reviewer_model=None, author_model=None, reviewer_effort=None, author_effort=None
        )
        self.assertIsNone(xt._review_models_error(ns, {**keys, "reviewer_model_family": "gpt-5"}))
        self.assertEqual((ns.reviewer_model, ns.author_model), ("gpt-5", "claude-opus-5-5"))  # lấy họ từ cấu hình

    def test_config_capability_rule(self):
        """D-161: cấu hình xt.yaml theo cùng luật năng lực — `reviewer_effort`/`author_effort` là mặc định khi không truyền
        cờ (như `*_model_family`); effort ngoài 5 mức là lỗi cấu hình, kể cả khi chưa khai họ model."""
        err = xt.review_family_config_error
        keys = {"author_model_family": "opus", "reviewer_model_family": "opus"}
        eff = {"reviewer_effort": "max", "author_effort": "high"}
        self.assertIn("cùng họ", err(keys) or "")
        self.assertIsNone(err({**keys, **eff}))
        self.assertIn("cùng họ", err({**keys, "reviewer_effort": "high", "author_effort": "high"}) or "")
        self.assertIn("cùng họ", err({**keys, "reviewer_effort": "max"}) or "")  # thiếu effort tác giả
        self.assertIn("reviewer_effort 'ultra'", err({**keys, **eff, "reviewer_effort": "ultra"}) or "")
        self.assertIn("author_effort 'High'", err({"author_effort": "High"}) or "")
        self.assertIn("bậc thấp hơn", err({"author_model_family": "opus", "reviewer_model_family": "sonnet"}) or "")
        self.assertIsNone(err({"author_model_family": "sonnet", "reviewer_model_family": "opus"}))
        self.assertIsNone(err({"author_model_family": "opus", "reviewer_model_family": "gpt"}))
        ns = unittest.mock.Mock(
            clean=True, reviewer_model=None, author_model=None, reviewer_effort=None, author_effort=None
        )
        self.assertIsNone(xt._review_models_error(ns, {**keys, **eff}))
        self.assertEqual((ns.reviewer_effort, ns.author_effort), ("max", "high"))  # effort lấy từ cấu hình
        ns = unittest.mock.Mock(
            clean=True, reviewer_model=None, author_model=None, reviewer_effort="low", author_effort=None
        )
        self.assertIn("cùng họ", xt._review_models_error(ns, {**keys, **eff}) or "")  # cờ CLI thắng cấu hình
        self.assertEqual((ns.reviewer_effort, ns.author_effort), ("low", "high"))
        # review #247: model khai bằng cờ → effort cấu hình của phía đó không áp (không ghi effort chưa từng chạy)
        ns = unittest.mock.Mock(
            clean=True, reviewer_model="claude-opus-5-5", author_model=None, reviewer_effort=None, author_effort=None
        )
        self.assertIn("cùng họ", xt._review_models_error(ns, {**keys, **eff}) or "")
        self.assertEqual((ns.reviewer_effort, ns.author_effort), (None, "high"))
        ns = unittest.mock.Mock(
            clean=True, reviewer_model=None, author_model="opus", reviewer_effort=None, author_effort=None
        )
        self.assertIn("cùng họ", xt._review_models_error(ns, {**keys, **eff}) or "")  # effort tác giả cấu hình không áp
        self.assertEqual((ns.reviewer_effort, ns.author_effort), ("max", None))

    def test_config_capability_rule_in_ci_check(self):
        base = Path(self.enterContext(tempfile.TemporaryDirectory()))
        cfg = "author_model_family: opus\nreviewer_model_family: opus\n"
        wf = base / "wf"  # thư mục workflow rỗng: chỉ kiểm cấu hình, không phụ thuộc workflow của repo
        wf.mkdir()
        for extra, want in (("reviewer_effort: max\nauthor_effort: high\n", 0), ("reviewer_effort: turbo\n", 1)):
            (base / "xt.yaml").write_text(cfg + extra, encoding="utf-8")
            with unittest.mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(base)}):
                rc, out, _ = run_main("ci-check", str(wf))
            self.assertEqual(rc, want, out)
            self.assertNotIn("cùng họ", out)
            if want:
                self.assertIn("reviewer_effort 'turbo'", out)
        (base / "xt.yaml").write_text("author_model_family: claude-mythos-5-1\nreviewer_model_family: haiku\n")
        with unittest.mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(base)}):
            rc, out, _ = run_main("ci-check", str(wf))
        self.assertEqual(rc, 1)
        self.assertIn("họ mythos chưa có bậc", out)

    def test_same_family_rejected_by_ci_check(self):
        base = Path(self.enterContext(tempfile.TemporaryDirectory()))
        (base / "xt.yaml").write_text("author_model_family: opus\nreviewer_model_family: opus\n", encoding="utf-8")
        with unittest.mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(base)}):
            rc, out, _ = run_main("ci-check")
        self.assertEqual(rc, 1)
        self.assertIn("cùng họ", out)

    def test_label_failure_is_reported(self):
        big = [{"filename": "src/a.py", "additions": 400, "deletions": 0}]
        summary = self.base / "summary.md"
        raw = {"repos/{owner}/{repo}/pulls/7/files?per_page=100": json.dumps(big)}
        gh = StewardGh(raw=raw, fail={"gh api -X POST": "HTTP 403"})
        with gh.patch(), unittest.mock.patch.dict(os.environ, {"GITHUB_STEP_SUMMARY": str(summary)}):
            rc, out, _ = run_main("pr", "steward", "--apply")
        self.assertEqual(rc, 1)
        self.assertIn("⚠ không gắn được nhãn xt-standard-lane: HTTP 403", out)
        self.assertIn("không gắn được nhãn", summary.read_text(encoding="utf-8"))
        # review đã sạch nhưng nhãn lỗi: lượt này không merge (lượt sau gắn lại nhãn rồi mới merge)
        ready = {"pr": 7, "head": FakeGh.SHA, "action": "merge", "why": "sạch"}
        gh = StewardGh(raw=raw, fail={"gh api -X POST": "HTTP 403"})
        with gh.patch(), unittest.mock.patch.object(xt, "pr_next", return_value=ready):
            rc, out, _ = run_main("pr", "steward", "--apply")
        self.assertEqual(rc, 1)
        self.assertEqual([w[3] for w in gh.writes], ["POST"])  # chỉ lần gắn nhãn, không PUT merge
        self.assertIn("#7 merge — sạch ⚠", out)
        hold = {**ready, "action": "disable-auto-merge"}  # giữ PR lại vẫn chạy dù nhãn lỗi
        gh = StewardGh(raw=raw, fail={"gh api -X POST": "HTTP 403"}, pull={"auto_merge": {"merge_method": "squash"}})
        with gh.patch(), unittest.mock.patch.object(xt, "pr_next", return_value=hold):
            rc, out, _ = run_main("pr", "steward", "--apply")
        self.assertEqual(rc, 1)
        self.assertEqual(gh.writes[-1], ["gh", "pr", "merge", "7", "--disable-auto"])

    def test_merge_fields_include_author(self):
        self.assertIn("author", xt.MERGE_FIELDS.split(","))


class PrTitleExemptTest(unittest.TestCase):
    """Review #140: tiêu đề do máy đặt (bot, nút Revert) được miễn; `pr_title_check: off` tắt luật ở dự án."""

    def test_bot_and_revert_titles_are_exempt(self):
        for p in (
            pr(title="Bump lodash from 4.17.20 to 4.17.21", author={"login": "dependabot[bot]"}),
            pr(title="Update dependency x to v2", author="renovate[bot]"),
            pr(title='Revert "feat: x"'),
        ):
            with self.subTest(p["title"]):
                self.assertEqual(xt.merge_decision(p, 2)["verdict"], "merge")
        self.assertEqual(xt.merge_decision(pr(title="Bump x", author={"login": "người"}), 2)["verdict"], "fix")

    def test_title_check_off_in_xt_yaml(self):
        base = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.enterContext(unittest.mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(base)}))
        commit_base_xt(base, "merge_autonomy: L2\npr_title_check: off\n")
        rc, out, _ = run_main("merge-check", "--json", "--pr-json", "-", stdin=json.dumps(pr(title="Sửa guard")))
        self.assertEqual((rc, json.loads(out)["verdict"]), (0, "merge"))
        commit_base_xt(base, "merge_autonomy: L2\n")
        rc, out, _ = run_main("merge-check", "--json", "--pr-json", "-", stdin=json.dumps(pr(title="Sửa guard")))
        self.assertEqual(json.loads(out)["verdict"], "fix")
        # PR tự thêm `off` vào xt.yaml trên nhánh của nó (cây làm việc) không tắt được luật — nhánh đích quyết
        commit_base_xt(base, "merge_autonomy: L2\n", "merge_autonomy: L2\npr_title_check: off\n")
        rc, out, _ = run_main("merge-check", "--json", "--pr-json", "-", stdin=json.dumps(pr(title="Sửa guard")))
        self.assertEqual(json.loads(out)["verdict"], "fix")
        commit_base_xt(base, "merge_autonomy: L2\npr_title_check: off\n", "merge_autonomy: L2\n")  # sửa tại chỗ: chặt
        rc, out, _ = run_main("merge-check", "--json", "--pr-json", "-", stdin=json.dumps(pr(title="Sửa guard")))
        self.assertEqual(json.loads(out)["verdict"], "fix")


class GhApiPaginationTest(unittest.TestCase):
    """FB-001 (X-Company): `_gh_api(path, True)` tự phân trang bằng `page=N` trên đường `repos/…` — không `gh --paginate`
    (đi theo header Link tới `repositories/{id}/…` bị proxy của phiên chặn 403)."""

    def fake(self, total: int, per: int = 5, key: str | None = None):
        calls: list[list[str]] = []

        def run(cmd, **kw):
            calls.append(list(cmd))
            self.assertNotIn("--paginate", cmd)
            m = re.search(r"[?&]page=(\d+)", cmd[-1])
            page = int(m.group(1)) if m else 1
            lo, hi = (page - 1) * per, min(page * per, total)
            items = [{"id": i} for i in range(lo, hi)]
            body = {key: items, "total_count": total} if key else items
            return subprocess.CompletedProcess(cmd, 0, json.dumps(body), "")

        return calls, unittest.mock.patch("xt.subprocess.run", side_effect=run)

    def test_gh_api_pages_until_short_page(self):
        calls, patch = self.fake(12)
        with patch:
            pages = xt._gh_api("repos/o/r/pulls/7/files?per_page=5", True)
            self.assertEqual(len(xt._gh_items("repos/o/r/pulls/7/files?per_page=5")), 12)
        self.assertEqual([len(p) for p in pages], [5, 5, 2])
        self.assertEqual(
            [c[-1] for c in calls][:3], [f"repos/o/r/pulls/7/files?per_page=5&page={n}" for n in (1, 2, 3)]
        )

    def test_gh_api_exact_multiple_reads_one_empty_page_then_stops(self):
        calls, patch = self.fake(10)
        with patch:
            pages = xt._gh_api("repos/o/r/pulls/7/commits?per_page=5", True)
        self.assertEqual([len(p) for p in pages], [5, 5, 0])
        self.assertEqual(len(calls), 3)

    def test_gh_api_empty_and_default_per_page(self):
        calls, patch = self.fake(0)
        with patch:
            self.assertEqual(xt._gh_api("repos/o/r/pulls/7/files", True), [[]])
        self.assertEqual(calls[0][-1], "repos/o/r/pulls/7/files?page=1")  # không có `?` → thêm `?page=`
        calls, patch = self.fake(31, per=30)
        with patch:
            pages = xt._gh_api("repos/o/r/pulls/7/files", True)  # per_page vắng = 30 (mặc định GitHub)
        self.assertEqual([len(p) for p in pages], [30, 1])

    def test_gh_api_object_with_array_paginates_and_cap(self):
        calls, patch = self.fake(7, key="check_runs")
        with patch:
            pages = xt._gh_api("repos/o/r/commits/abc/check-runs?per_page=5", True)
        self.assertEqual([len(p["check_runs"]) for p in pages], [5, 2])
        calls, patch = self.fake(10**6, per=5)  # API lặp trang mãi → dừng ở trần GH_MAX_PAGES
        with patch:
            pages = xt._gh_api("repos/o/r/x?per_page=5", True)
        self.assertEqual(len(pages), xt.GH_MAX_PAGES)
        self.assertEqual(xt._gh_page_len("lạ"), 0)

    def test_gh_api_single_call_without_paginate(self):
        calls, patch = self.fake(3)
        with patch:
            self.assertEqual(xt._gh_api("repos/o/r/pulls/7"), [[{"id": 0}, {"id": 1}, {"id": 2}]])
        self.assertEqual(calls[0][-1], "repos/o/r/pulls/7")


class PrStatsTest(unittest.TestCase):
    """`xt.py pr stats` (TD-4): số đo PR đã merge từ REST — hàm thuần `pr_stats` + I/O qua REST giả có phân trang
    `page=N` như `GhApiPaginationTest` (không `--paginate`, không GraphQL)."""

    NOW = xt._dt.datetime(2026, 10, 21, 12, tzinfo=xt._dt.timezone.utc)

    @staticmethod
    def at(hours_ago: float, now: Any = None) -> str:
        t = (now or PrStatsTest.NOW) - xt._dt.timedelta(hours=hours_ago)
        return t.strftime("%Y-%m-%dT%H:%M:%SZ")

    def mk_pr(self, n: int, opened: float, merged: float | None, now: Any = None, **over: Any) -> dict:
        p = {
            "number": n,
            "title": f"feat: việc {n}",
            "created_at": self.at(opened, now),
            "merged_at": None if merged is None else self.at(merged, now),
            "head": {"ref": f"nhanh-{n}", "sha": f"sha{n}"},
            "labels": [],
        }
        p.update(over)
        return p

    def mk_run(self, branch: str, sha: str, hours_ago: float, concl: str | None = "success", now: Any = None) -> dict:
        return {"head_branch": branch, "head_sha": sha, "created_at": self.at(hours_ago, now), "conclusion": concl}

    def corpus(self, now: Any = None) -> tuple[list[dict], list[dict]]:
        prs = [
            self.mk_pr(1, 30, 20, now, labels=[{"name": "xt-standard-lane"}, "lạ"]),  # lead 10 giờ
            self.mk_pr(2, 5, 3, now, title='Revert "feat: việc 1"'),  # lead 2 giờ
            self.mk_pr(3, 50, 2, now, title="revert(cli)!: bỏ cờ"),  # lead 48 giờ
            self.mk_pr(4, 2000, 1000, now),  # merge trước kỳ 30 ngày → bỏ
            self.mk_pr(5, 10, None, now),  # đóng không merge → bỏ
            {**self.mk_pr(6, 4, 1, now), "created_at": "hỏng"},  # giờ mở hỏng → bỏ
        ]
        runs = [
            self.mk_run("nhanh-1", "cu", 29, "failure", now),  # push trước, SHA khác, trong lúc PR mở
            self.mk_run("nhanh-1", "sha1", 21, "success", now),
            self.mk_run("nhanh-1", "khac", 5, "success", now),  # tên nhánh dùng lại sau merge → không tính
            self.mk_run("nhanh-2", "sha2", 4, "cancelled", now),
            self.mk_run("nhanh-2", "sha2", 4.5, None, now),  # đang chạy (conclusion null)
            self.mk_run("nhanh-2", "x", 0, "failure", now) | {"created_at": "hỏng"},  # giờ hỏng, SHA khác → bỏ
            self.mk_run("nhanh-9", "sha1", 25, "failure", now),  # nhánh khác dù trùng SHA → bỏ
        ]
        return prs, runs

    def test_pr_stats_pure_numbers(self):
        prs, runs = self.corpus()
        s = xt.pr_stats(prs, runs, self.NOW, 30)
        self.assertEqual([r["number"] for r in s["prs"]], [1, 2, 3])
        self.assertEqual(s["merged"], 3)
        self.assertEqual(s["lead_time_hours"], {"median": 10.0, "p95": 48.0})
        self.assertEqual([r["runs"] for r in s["prs"]], [2, 2, 0])
        self.assertEqual(s["runs_per_pr"], {"median": 2.0, "p95": 2.0, "total": 4})
        self.assertEqual((s["runs_failure"], s["runs_cancelled"], s["bad_run_rate"]), (1, 1, 0.5))
        self.assertEqual((s["standard_lane"], s["reverts"], s["runs_seen"]), (1, 2, len(runs)))
        self.assertEqual(s["since"], "2026-09-21T12:00:00+00:00")

    def test_pr_stats_empty_and_missing_head(self):
        s = xt.pr_stats([], [], self.NOW, 7)
        self.assertEqual((s["merged"], s["bad_run_rate"]), (0, None))
        self.assertEqual(s["lead_time_hours"], {"median": None, "p95": None})
        table = xt.pr_stats_table(s)
        self.assertIn("| PR merge trong 7 ngày (từ 2026-10-14) | Giá trị |", table)
        self.assertIn("| — · — |", table)
        no_head = {**self.mk_pr(8, 3, 1), "head": None, "title": None, "labels": None}
        s = xt.pr_stats([no_head], [self.mk_run("nhanh-8", "sha8", 2)], self.NOW, 7)
        self.assertEqual((s["prs"][0]["runs"], s["prs"][0]["revert"], s["runs_per_pr"]["total"]), (0, False, 0))

    def test_pr_stats_table_values(self):
        table = xt.pr_stats_table(xt.pr_stats(*self.corpus(), self.NOW, 30))
        self.assertIn("| PR đã merge | 3 |", table)
        self.assertIn("| 10 giờ · 48 giờ |", table)
        self.assertIn("| 2 · 2 · 4 |", table)
        self.assertIn("| 1 · 1 (50%) |", table)
        self.assertIn("(`xt-standard-lane`) | 1 |", table)
        self.assertIn("| PR revert | 2 |", table)

    def fake_rest(self, prs: list[dict], runs: list[dict], fail: str = "", total: int | None = None):
        """REST giả: `pulls` là mảng, `actions/workflows/<ci>/runs` là object `workflow_runs` lọc theo `created=<ngày>`
        (T-2409); cắt trang theo `per_page`/`page`; `total` ép `total_count` (ngày chạm trần listing)."""
        calls: list[str] = []

        def run(cmd, **kw):
            path = cmd[-1]
            calls.append(path)
            self.assertNotIn("--paginate", cmd)
            self.assertNotIn("graphql", cmd)
            if fail and fail in path:
                return subprocess.CompletedProcess(cmd, 1, "", "HTTP 403: Resource not accessible")
            page = int(re.search(r"[?&]page=(\d+)", path)[1])
            per = int(re.search(r"[?&]per_page=(\d+)", path)[1])
            is_runs = "/actions/" in path
            src = prs
            if is_runs:
                day = re.search(r"created=([\d-]+)", path)[1]
                src = [r for r in runs if str(r.get("created_at")).startswith(day)]
            chunk = src[(page - 1) * per : page * per]
            body = {"total_count": len(src) if total is None else total, "workflow_runs": chunk} if is_runs else chunk
            return subprocess.CompletedProcess(cmd, 0, json.dumps(body), "")

        return calls, unittest.mock.patch("xt.subprocess.run", side_effect=run)

    def test_pr_stats_cli_rest_paginated_json_and_table(self):
        now = xt._dt.datetime.now(xt._dt.timezone.utc)
        prs, runs = self.corpus(now)
        filler = [self.mk_pr(100 + i, 9000, 8000, now) for i in range(100)]  # trang 1 đủ 100 → đọc trang 2
        runs_full = runs + [self.mk_run("khac", "z", 1, "success", now)] * 100
        calls, patch = self.fake_rest(filler + prs, runs_full)
        with patch:
            rc, out, err = run_main("pr", "stats", "--json")
        self.assertEqual((rc, err), (0, ""))
        s = json.loads(out)
        self.assertEqual((s["merged"], s["runs_per_pr"]["total"], s["runs_seen"]), (3, 4, len(runs_full) - 1))
        self.assertEqual(
            calls[:2],
            [
                f"repos/{{owner}}/{{repo}}/pulls?state=closed&sort=updated&direction=desc&per_page=100&page={n}"
                for n in (1, 2)
            ],
        )
        self.assertTrue(
            all("/actions/workflows/ci.yml/runs?event=pull_request&created=" in c for c in calls[2:]), calls
        )
        calls, patch = self.fake_rest(prs, runs)
        with patch:
            rc, out, _ = run_main("pr", "stats", "--days", "30", "--repo", "o/r")
        self.assertEqual(rc, 0)
        self.assertTrue(out.startswith("| PR merge trong 30 ngày"), out)
        self.assertIn("| PR revert | 2 |", out)
        self.assertTrue(all(c.startswith("repos/o/r/") for c in calls), calls)

    @staticmethod
    def day_of(now: Any, hours_ago: float) -> str:
        return (now - xt._dt.timedelta(hours=hours_ago)).date().isoformat()

    def test_pr_stats_pushes_per_day_queries_dedup_and_truncation(self):
        now = xt._dt.datetime.now(xt._dt.timezone.utc)
        prs = [self.mk_pr(1, 50, 1, now)]
        runs = [
            self.mk_run("nhanh-1", "a", 49, "success", now) | {"id": 1},
            self.mk_run("nhanh-1", "a", 49, "success", now) | {"id": 1},  # trùng id → bỏ
            self.mk_run("nhanh-1", "b", 2, "success", now) | {"id": 2},
            self.mk_run("nhanh-1", "c", 1, "success", now),  # không id → giữ
        ]
        calls, patch = self.fake_rest(prs, runs)
        with patch:
            rc, out, _ = run_main("pr", "stats", "--days", "3", "--json")
        s = json.loads(out)
        self.assertEqual((rc, s["runs_truncated"]), (0, False))
        first, today = xt._dt.date.fromisoformat(self.day_of(now, 50)), now.date()
        want = [(first + xt._dt.timedelta(days=k)).isoformat() for k in range((today - first).days + 1)]
        got = [re.search(r"created=([\d-]+)", c)[1] for c in calls if "/actions/" in c]
        self.assertEqual(got, want)
        self.assertGreaterEqual(len(want), 2)
        self.assertEqual(s["runs_seen"], 3)
        self.assertEqual(s["pushes"]["total"], 3)
        _, patch = self.fake_rest(prs, runs, total=1000)  # mọi ngày chạm trần
        with patch:
            _, out, _ = run_main("pr", "stats", "--days", "3", "--json")
        self.assertIs(json.loads(out)["runs_truncated"], True)
        _, patch = self.fake_rest(prs, runs, total=1000)
        with patch:
            _, out, _ = run_main("pr", "stats", "--days", "3")
        self.assertIn("⚠ runs_truncated", out)
        # review T-2409: PR mở 60 ngày trước kỳ 3 ngày → chỉ đọc tới 30 ngày trước đầu kỳ, số liệu thiếu thì cờ cắt
        calls, patch = self.fake_rest([self.mk_pr(1, 60 * 24, 1, now)], runs)
        with patch:
            _, out, _ = run_main("pr", "stats", "--days", "3", "--json")
        days = [c for c in calls if "/actions/" in c]
        self.assertEqual(len(days), xt.PR_STATS_LOOKBACK_DAYS + 3 + 1, days[:2])
        self.assertIs(json.loads(out)["runs_truncated"], True)

    def test_pr_stats_pushes_truncated_by_page_cap_and_env_workflow(self):
        now = xt._dt.datetime.now(xt._dt.timezone.utc)
        prs = [self.mk_pr(1, 1, 0.5, now)]
        runs = [self.mk_run("nhanh-1", "a", 0.8, "success", now) | {"id": 1}]
        _, patch = self.fake_rest(prs, runs)
        with (
            patch,
            unittest.mock.patch.object(xt, "GH_MAX_PAGES", 1),
            unittest.mock.patch.dict(os.environ, {"XT_CI_WORKFLOW": "build.yaml"}),
        ):
            xt_calls: list[str] = []
            orig = xt._gh_api_once
            with unittest.mock.patch.object(xt, "_gh_api_once", side_effect=lambda p: xt_calls.append(p) or orig(p)):
                prs_, runs_, cut = xt._pr_stats_fetch("repos/o/r", now - xt._dt.timedelta(days=1))
        self.assertTrue(cut)
        self.assertEqual(len(runs_), 1)
        self.assertTrue(any("/actions/workflows/build.yaml/runs?" in c for c in xt_calls), xt_calls)
        with unittest.mock.patch.dict(os.environ, {"XT_CI_WORKFLOW": "../x"}), self.assertRaises(xt.PrInputError):
            xt._pr_stats_runs("repos/o/r", now.date(), now.date())

    def test_pr_stats_pushes_numbers_and_edges(self):
        def r(sha: Any, h: float, concl: Any = "success") -> dict:
            return self.mk_run("nhanh-1", sha, h, concl) | ({} if sha else {"head_sha": None})

        pr = self.mk_pr(1, 30, 1)
        s = xt.pr_stats(
            [pr], [r("a", 20, "failure"), r("a", 19, "cancelled"), r("b", 10), r("c", 5, "cancelled")], self.NOW, 7
        )
        row = s["prs"][0]
        self.assertEqual((row["pushes"], row["first_push_green"], row["cancelled_same_sha"]), (3, False, 1))
        self.assertEqual((s["pushes"], s["cancelled_same_sha"]), ({"median": 3.0, "p95": 3.0, "total": 3}, 1))
        self.assertEqual(s["first_push_green"], {"green": 0, "of": 1, "rate": 0.0})
        self.assertFalse(s["runs_truncated"])
        table = xt.pr_stats_table(s)
        self.assertIn("| 3 · 3 · 3 |", table)
        self.assertIn("| 0/1 (0%) |", table)
        self.assertIn("cùng SHA với run khác | 1 |", table)
        self.assertNotIn("runs_truncated", table)
        # review T-2409: run đầu đã chạy lại (listing chỉ giữ kết luận lần cuối) — không phải xanh lần đầu
        s = xt.pr_stats([pr], [r("a", 20) | {"run_attempt": 2}, r("b", 10)], self.NOW, 7)
        self.assertIs(s["prs"][0]["first_push_green"], False)
        # xanh ngay lần đầu; sắp theo giờ tạo, không theo thứ tự đầu vào
        s = xt.pr_stats([pr], [r("b", 10, "failure"), r("a", 20)], self.NOW, 7)
        self.assertEqual((s["prs"][0]["first_push_green"], s["prs"][0]["pushes"]), (True, 2))
        self.assertEqual(s["first_push_green"]["rate"], 1.0)
        # PR không run, run không head_sha, mọi run huỷ
        s = xt.pr_stats([pr], [], self.NOW, 7)
        self.assertEqual(
            (s["pushes"]["total"], s["first_push_green"], s["pushes"]["median"]),
            (0, {"green": 0, "of": 0, "rate": None}, 0.0),
        )
        self.assertIn("| 0/0 (—) |", xt.pr_stats_table(s))
        s = xt.pr_stats([pr], [r(None, 5, "cancelled")], self.NOW, 7)
        self.assertEqual(
            (s["prs"][0]["pushes"], s["prs"][0]["first_push_green"], s["prs"][0]["cancelled_same_sha"]), (0, None, 0)
        )
        s = xt.pr_stats([pr], [r("a", 5, "cancelled"), r("b", 6, "cancelled")], self.NOW, 7, True)
        self.assertEqual((s["prs"][0]["cancelled_same_sha"], s["runs_truncated"]), (0, True))
        self.assertIn("⚠ runs_truncated", xt.pr_stats_table(s))

    def test_pr_stats_cli_no_merged_pr_skips_runs(self):
        now = xt._dt.datetime.now(xt._dt.timezone.utc)
        calls, patch = self.fake_rest([self.mk_pr(5, 10, None, now)], [])
        with patch:
            rc, out, _ = run_main("pr", "stats", "--days", "1", "--json")
        self.assertEqual((rc, json.loads(out)["merged"]), (0, 0))
        self.assertFalse(any("actions/runs" in c for c in calls), calls)

    def test_pr_stats_cli_errors(self):
        for args in (("--days", "0"), ("--repo", "khong hop le")):
            rc, _, err = run_main("pr", "stats", *args)
            self.assertEqual(rc, 2, args)
            self.assertIn("--days phải ≥ 1", err)
        now = xt._dt.datetime.now(xt._dt.timezone.utc)
        prs, runs = self.corpus(now)
        for fail in ("/pulls", "/actions/workflows"):  # token thiếu quyền (403) ở từng endpoint → lỗi rõ, exit 2
            _, patch = self.fake_rest(prs, runs, fail=fail)
            with patch:
                rc, out, err = run_main("pr", "stats")
            self.assertEqual((rc, out), (2, ""), fail)
            self.assertIn("HTTP 403", err)


class StewardDispatchCiTest(unittest.TestCase):
    """T-2402: steward merge bằng GITHUB_TOKEN (không `XT_STEWARD_TOKEN`) không kích workflow `push` → sau merge thành công
    gọi `workflow_dispatch` của CI trên nhánh đích (GitHub cho GITHUB_TOKEN tạo `workflow_dispatch`); có token riêng thì
    `push` đã kích CI → không dispatch (không chạy đôi)."""

    DISPATCH = [
        "gh",
        "api",
        "-X",
        "POST",
        "repos/{owner}/{repo}/actions/workflows/ci.yml/dispatches",
        "-f",
        "ref=main",
    ]

    def setUp(self):
        self.base = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.enterContext(unittest.mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(self.base)}))
        for key in ("GITHUB_STEP_SUMMARY", "GITHUB_ACTIONS", "XT_STEWARD_UPDATE", "XT_CI_WORKFLOW"):
            os.environ.pop(key, None)
        commit_base_xt(self.base, "merge_autonomy: L3\n")

    def github_token(self, **extra: str) -> None:
        """Như pr-steward.yml khi thiếu secret `XT_STEWARD_TOKEN`: trong Actions, `XT_STEWARD_UPDATE=off`."""
        os.environ.update({"GITHUB_ACTIONS": "true", "XT_STEWARD_UPDATE": "off", **extra})

    def steward(self, *extra: str, **kw: Any) -> tuple[int, str, StewardGh]:
        gh = StewardGh(**kw)
        with gh.patch():
            rc, out, _ = run_main("pr", "steward", "--apply", *extra)
        return rc, out, gh

    def test_steward_dispatch_ci_after_merge_without_token(self):
        self.github_token()
        rc, out, gh = self.steward()
        self.assertEqual(rc, 0, out)
        self.assertIn("#7 merge ✓ → dispatch CI ✓", out)
        self.assertEqual([w[3] for w in gh.writes], ["PUT", "POST"])  # merge trước, dispatch sau
        self.assertEqual(gh.writes[1], self.DISPATCH)  # ref = nhánh đích của PR (`base.ref`)

    def test_steward_dispatch_ci_helper_ref_and_workflow_name(self):
        gh = StewardGh()
        out: dict = {}
        with gh.patch():
            xt._steward_dispatch_ci(out, "repos/o/r", "trunk")
        self.assertEqual(
            gh.writes, [["gh", "api", "-X", "POST", "repos/o/r/actions/workflows/ci.yml/dispatches", "-f", "ref=trunk"]]
        )
        self.assertEqual(out, {"then": "dispatch CI ✓"})
        os.environ["XT_CI_WORKFLOW"] = " build.yaml "  # dự án đích đặt tên khác
        gh = StewardGh()
        with gh.patch():
            xt._steward_dispatch_ci(out, "repos/o/r", "main")
        self.assertEqual(gh.writes[0][4], "repos/o/r/actions/workflows/build.yaml/dispatches")
        for bad in ("../ci.yml", "ci.yml/x", "ci.json", "ci yml.yml", "cí.yml"):  # kiểm chặt: không dispatch tên lạ
            with self.subTest(bad):
                os.environ["XT_CI_WORKFLOW"] = bad
                gh, out = StewardGh(), {"warn": "trước"}
                with gh.patch():
                    xt._steward_dispatch_ci(out, "repos/o/r", "main")
                self.assertEqual(gh.writes, [])
                self.assertTrue(out["then"].startswith("dispatch CI ✗"), out)
                self.assertTrue(out["warn"].startswith("trước; "), out)  # không đè cảnh báo sẵn có
                self.assertIn("XT_CI_WORKFLOW", out["warn"])

    def test_steward_dispatch_ci_not_with_own_token(self):
        for env in (
            {"GITHUB_ACTIONS": "true", "XT_STEWARD_UPDATE": "on"},
            {},
        ):  # secret có / chạy cục bộ bằng gh của người
            with self.subTest(env=env), unittest.mock.patch.dict(os.environ, env):
                rc, out, gh = self.steward()
                self.assertEqual(rc, 0, out)
                self.assertIn("#7 merge ✓ —", out)
                self.assertEqual([w[3] for w in gh.writes], ["PUT"])

    def test_steward_dispatch_ci_failure_keeps_merge_applied(self):
        self.github_token()
        for err in ("HTTP 403: Resource not accessible by integration", "oserror"):
            with self.subTest(err):
                rc, out, gh = self.steward("--json", fail={"gh api -X POST": err})
                (res,) = json.loads(out)
                self.assertEqual(rc, 1)  # job đỏ để người thấy
                self.assertTrue(res["applied"])  # merge đã vào — không huỷ kết quả
                self.assertNotIn("error", res)
                self.assertTrue(res["then"].startswith("dispatch CI ✗"), res)
                self.assertIn("CI không chạy trên", res["warn"])
                self.assertEqual([w[3] for w in gh.writes], ["PUT", "POST"])
        rc, out, _ = self.steward(fail={"gh api -X POST": "HTTP 403"})
        self.assertIn("#7 merge ✓ → dispatch CI ✗ HTTP 403 —", out)
        self.assertIn("⚠ ", out)

    def test_steward_dispatch_ci_not_after_failed_merge(self):
        self.github_token()
        rc, out, gh = self.steward(fail={"gh api -X PUT": "HTTP 405 not mergeable"})
        self.assertEqual(rc, 1)
        self.assertIn("#7 merge ✗ HTTP 405 not mergeable", out)
        self.assertEqual([w[3] for w in gh.writes], ["PUT"])
        # dry-run (không --apply): không ghi gì
        gh = StewardGh()
        with gh.patch():
            run_main("pr", "steward")
        self.assertEqual(gh.writes, [])
        # PR đã merge giữa lúc xét và lúc làm (đọc lại): không merge, không dispatch
        gh = SeqGh([{}, {"merged": True, "state": "closed"}])
        with gh.patch():
            rc, out, _ = run_main("pr", "steward", "--apply")
        self.assertEqual(gh.writes, [])

    def test_steward_dispatch_ci_not_for_other_actions(self):
        self.github_token()
        rc, out, gh = self.steward(pull={"mergeable_state": "behind", "auto_merge": {"merge_method": "squash"}})
        self.assertIn("#7 disable-auto-merge ✓", out)
        self.assertNotIn("dispatch", out)
        self.assertEqual(gh.writes, [["gh", "pr", "merge", "7", "--disable-auto"]])
        for action in ("update", "review", "wait", "fix"):
            with self.subTest(action), unittest.mock.patch.object(xt, "_steward_dispatch_ci") as m:
                out = {"pr": 7, "head": "h", "action": action, "why": ""}
                with (
                    unittest.mock.patch.object(xt, "_steward_stale", return_value=""),
                    unittest.mock.patch.object(xt, "_steward_run", return_value=""),
                ):
                    xt._steward_apply(out, {}, "repos/o/r", [["gh", "x"]], "main")
                m.assert_not_called()

    MERGED = "9" * 40
    FILES = "repos/{owner}/{repo}/pulls/7/files?per_page=100"

    def version_pr(
        self, files: tuple[str, ...] = ("VERSION", "CHANGELOG.md", "tests/test_version.py"), workflow: bool = True
    ) -> dict:
        """PR đổi `files`; repo có `release-tag.yml` khi `workflow` (AUD-HAR-124)."""
        if workflow:
            wf = self.base / xt.RELEASE_WORKFLOW_FILE
            wf.parent.mkdir(parents=True, exist_ok=True)
            wf.write_text("on: push\n", encoding="utf-8")
        return {self.FILES: json.dumps([{"filename": f, "additions": 1, "deletions": 1} for f in files])}

    def test_steward_dispatch_tag_after_version_merge(self):
        """AUD-HAR-124 (#314): merge bằng GITHUB_TOKEN của PR đổi VERSION không kích `push` của release-tag.yml → steward
        dispatch nó, ghim commit merge đọc lại từ PR (không theo đầu nhánh)."""
        self.github_token()
        gh = SeqGh(
            [{}, {}, {"merged": True, "state": "closed", "merge_commit_sha": self.MERGED}], raw=self.version_pr()
        )
        with gh.patch():
            rc, out, _ = run_main("pr", "steward", "--apply")
        self.assertEqual(rc, 0, out)
        self.assertIn("dispatch CI ✓; dispatch tag ✓", out)
        tag = ["gh", "api", "-X", "POST", "repos/{owner}/{repo}/actions/workflows/release-tag.yml/dispatches"]
        self.assertEqual(gh.writes[2], tag + ["-f", "ref=main", "-f", f"inputs[sha]={self.MERGED}"])

    def test_steward_no_tag_dispatch_without_version_workflow_or_with_token(self):
        for name, raw, env in (
            ("không đổi VERSION", self.version_pr(("CHANGELOG.md", "tests/test_version.py")), "off"),
            ("có token riêng: push đã kích tag", self.version_pr(), "on"),
        ):
            with self.subTest(name):
                self.github_token(XT_STEWARD_UPDATE=env)
                rc, out, gh = self.steward(raw=raw)
                self.assertEqual(rc, 0, out)
                self.assertNotIn("dispatch tag", out)
                self.assertNotIn("release-tag.yml", " ".join(" ".join(w) for w in gh.writes))
        self.github_token()  # trả XT_STEWARD_UPDATE về off: đường dispatch sau merge phải chạy (review #316)
        (self.base / xt.RELEASE_WORKFLOW_FILE).unlink()  # dự án đích không có workflow tag
        rc, out, gh = self.steward(raw=self.version_pr(workflow=False))
        self.assertIn("dispatch CI ✓", out)
        self.assertNotIn("dispatch tag", out)
        self.assertNotIn("release-tag.yml", " ".join(" ".join(w) for w in gh.writes))
        for ref, want in (("main", True), ("develop", False)):  # như trigger `push` của release-tag.yml: chỉ main
            with self.subTest(ref=ref), unittest.mock.patch.object(xt, "_steward_apply", return_value={}) as m:
                gh = StewardGh(raw=self.version_pr(), pull={"base": {"ref": ref}})
                with gh.patch():
                    xt._steward_one("7", "repos/{owner}/{repo}", self.base, True, [])
                self.assertEqual(m.call_args.args[4:], (ref, want))

    def test_steward_dispatch_tag_unreadable_merge_warns(self):
        self.github_token()
        for last in (
            {"merged": False, "merge_commit_sha": self.MERGED},  # GitHub trả commit merge thử cho PR chưa merge
            {"merged": True, "merge_commit_sha": "không-phải-sha"},
            "FAIL",
        ):
            with self.subTest(last=last):
                gh = SeqGh([{}, {}, last], raw=self.version_pr())
                with gh.patch():
                    rc, out, _ = run_main("pr", "steward", "--apply", "--json")
                (res,) = json.loads(out)
                self.assertEqual(rc, 1)  # cảnh báo → job đỏ để người thấy
                self.assertTrue(res["applied"])  # merge đã vào — không huỷ
                self.assertIn("dispatch tag ✗", res["then"])
                self.assertIn("tag phát hành chưa gắn", res["warn"])
                self.assertEqual([w[3] for w in gh.writes], ["PUT", "POST"])  # merge + dispatch CI, không dispatch tag
        gh = SeqGh([{}, {}, {"merged": True, "merge_commit_sha": self.MERGED}], raw=self.version_pr())
        gh.fail = {"gh api -X POST repos/{owner}/{repo}/actions/workflows/release-tag.yml": "HTTP 404"}
        with gh.patch():
            rc, out, _ = run_main("pr", "steward", "--apply")
        self.assertIn("dispatch tag ✗ HTTP 404", out)
        self.assertIn(f"gh workflow run release-tag.yml -f sha={self.MERGED}", out)  # lệnh chạy tay chép dùng được

    def test_steward_dispatch_ci_workflows(self):
        for path in (ROOT / ".github/workflows/ci.yml", ROOT / "framework/templates/ci.yml"):
            with self.subTest(path=str(path.relative_to(ROOT))):
                text = path.read_text(encoding="utf-8")
                on = text.split("\non:\n", 1)[1].split("\npermissions:", 1)[0]
                self.assertRegex(on, r"(?m)^  workflow_dispatch:( \{\})?$")  # không input
                self.assertNotIn("inputs:", on)
                self.assertIn("github.head_ref || github.run_id", text)  # dispatch: nhóm run_id riêng, không bị huỷ
                self.assertIn("cancel-in-progress: ${{ github.event_name == 'pull_request' }}", text)
                self.assertNotRegex(text, r"if:[^\n]*github\.event_name")  # job/bước không lọc theo sự kiện
                self.assertEqual(xt.ci_check_text(text), [])
        steward = (ROOT / ".github/workflows/pr-steward.yml").read_text(encoding="utf-8")
        job = steward.split("\njobs:\n", 1)[1]
        perms = job.split("    permissions:\n", 1)[1].split("    steps:", 1)[0]
        self.assertRegex(perms, r"(?m)^      actions: write # \S")  # job-level, kèm lý do
        top = steward.split("\npermissions:\n", 1)[1].split("\n\n", 1)[0]
        self.assertEqual(top, "  contents: read")  # không nâng quyền mức workflow
        self.assertIn("XT_STEWARD_UPDATE: ${{ secrets.XT_STEWARD_TOKEN != '' && 'on' || 'off' }}", steward)
        self.assertIn("workflow_dispatch", steward.split("\non:\n", 1)[0])  # chú thích đầu file nói hành vi mới


def rest_run(
    cid: int, name: str, status: str, concl: str | None, started: str | None, suite: int, app: int = 15368
) -> dict:
    """Check-run đúng shape `GET commits/{sha}/check-runs` (các trường `rest_rollup` đọc + trường thật bên cạnh)."""
    return {
        "id": cid,
        "name": name,
        "status": status,
        "conclusion": concl,
        "started_at": started,
        "completed_at": None if status != "completed" else started,
        "check_suite": {"id": suite},
        "app": {"id": app, "slug": "github-actions"},
    }


class CiBlockerLatestRunTest(unittest.TestCase):
    """T-2404: steward báo `wait — CI đang chạy: gitleaks` khi check đã completed (run 39630751648, PR #208). Nhiều bản
    cùng tên trên cùng head (suite cũ, re-run): chỉ bản bắt đầu muộn nhất có hiệu lực; bản mới nhất đang chạy/đỏ vẫn chặn."""

    HEAD_208 = [
        rest_run(9101, "merge-gate", "completed", "success", "2026-10-21T15:58:20Z", 501),
        rest_run(9102, "pr-review", "completed", "skipped", "2026-10-21T15:58:23Z", 502),
        rest_run(9103, "gitleaks", "completed", "success", "2026-10-21T15:58:05Z", 503),
        rest_run(9104, "dep-audit", "completed", "success", "2026-10-21T15:58:10Z", 504),
        rest_run(9105, "quality", "completed", "success", "2026-10-21T15:59:40Z", 505),
        rest_run(9106, "codeql", "completed", "success", "2026-10-21T15:58:30Z", 506),
    ]
    REQUIRED = [{"context": c} for c in ("quality", "gitleaks", "dep-audit")]

    def blocker(self, runs: list, statuses: list | None = None) -> Any:
        rollup = xt.rest_rollup(runs, statuses or [])
        return xt._ci_blocker({"statusCheckRollup": rollup, "requiredChecks": self.REQUIRED})

    def test_ci_blocker_completed_not_wait_pr208_rest(self):
        # Suite cũ (503 → 499) để lại check-run `queued` với id lớn hơn nhưng bắt đầu SỚM hơn bản đã xong: trước đây
        # khoá id lớn nhất chọn bản treo → wait tới lượt cron sau.
        stale = rest_run(9199, "gitleaks", "queued", None, "2026-10-21T15:57:50Z", 499)
        self.assertIsNone(self.blocker([*self.HEAD_208, stale]))
        self.assertIsNone(self.blocker([stale, *self.HEAD_208]))  # thứ tự trang không đổi kết quả
        d = xt.merge_decision(pr(statusCheckRollup=xt.rest_rollup([*self.HEAD_208, stale], [])), 3)
        self.assertNotEqual(d["verdict"], "wait")

    def test_ci_blocker_completed_not_wait_graphql_rollup(self):
        # `--pr-json` (gh pr view): rollup GraphQL không khử trùng — bản IN_PROGRESS cũ không giữ PR ở wait
        old = {
            "__typename": "CheckRun",
            "name": "test",
            "status": "IN_PROGRESS",
            "conclusion": "",
            "startedAt": "2026-10-21T15:50:00Z",
        }
        new = {
            "__typename": "CheckRun",
            "name": "test",
            "status": "COMPLETED",
            "conclusion": "SUCCESS",
            "startedAt": "2026-10-21T15:58:00Z",
        }
        self.assertIsNone(xt._ci_blocker({"statusCheckRollup": [old, new]}))
        self.assertIsNone(xt._ci_blocker({"statusCheckRollup": [new, old]}))

    def test_ci_blocker_completed_not_wait_latest_running_still_waits(self):
        # Re-run: bản mới nhất đang chạy → vẫn wait, dù bản cũ xanh (REST và GraphQL)
        rerun = rest_run(9200, "gitleaks", "in_progress", None, "2026-10-21T16:10:00Z", 503)
        self.assertEqual(self.blocker([*self.HEAD_208, rerun]), ("wait", ["CI đang chạy: gitleaks"]))
        # bản mới nhất chưa có started_at (vừa xếp hàng): coi là mới nhất — chiều chặt
        queued = rest_run(9050, "gitleaks", "queued", None, None, 507)
        self.assertEqual(self.blocker([*self.HEAD_208, queued]), ("wait", ["CI đang chạy: gitleaks"]))
        old = {
            "__typename": "CheckRun",
            "name": "t",
            "status": "COMPLETED",
            "conclusion": "SUCCESS",
            "startedAt": "2026-10-21T15:50:00Z",
        }
        new = {"__typename": "CheckRun", "name": "t", "status": "QUEUED", "conclusion": ""}
        self.assertEqual(xt._ci_blocker({"statusCheckRollup": [new, old]}), ("wait", ["CI đang chạy: t"]))

    def test_ci_blocker_completed_not_wait_latest_red_still_blocks(self):
        red = rest_run(9201, "gitleaks", "completed", "failure", "2026-10-21T16:10:00Z", 508)
        self.assertEqual(self.blocker([*self.HEAD_208, red]), ("fix", ["CI đỏ: gitleaks"]))
        # bản bắt buộc mới nhất bị skip không được bản xanh cũ che (REC-08)
        skip = rest_run(9202, "gitleaks", "completed", "skipped", "2026-10-21T16:10:00Z", 508)
        self.assertEqual(self.blocker([*self.HEAD_208, skip])[0], "human")
        # bản cũ đỏ, bản mới xanh → không chặn (như #58)
        old_red = rest_run(9001, "quality", "completed", "failure", "2026-10-21T15:40:00Z", 400)
        self.assertIsNone(self.blocker([*self.HEAD_208, old_red]))

    def test_ci_blocker_completed_not_wait_keeps_strict_when_unordered(self):
        # Không có thời điểm/id để xếp: giữ mọi bản (như trước) — bản đang chạy vẫn chặn
        a = {"__typename": "CheckRun", "name": "t", "status": "IN_PROGRESS", "conclusion": ""}
        b = {"__typename": "CheckRun", "name": "t", "status": "COMPLETED", "conclusion": "SUCCESS"}
        self.assertEqual(xt._ci_blocker({"statusCheckRollup": [a, b]})[0], "wait")
        # khác app là check khác (AUD-CODE-007): bản app khác đang chạy không bị bản xanh mới che
        other = rest_run(9300, "gitleaks", "in_progress", None, "2026-10-21T15:50:00Z", 600, app=99)
        self.assertEqual(self.blocker([*self.HEAD_208, other]), ("wait", ["CI đang chạy: gitleaks"]))
        # commit status cùng tên không gộp với check-run (nguồn khác) — pending vẫn chặn
        self.assertEqual(
            self.blocker(self.HEAD_208, [{"context": "gitleaks", "state": "pending"}]),
            ("wait", ["CI đang chạy: gitleaks"]),
        )
        # rollup GraphQL không có appId: khác workflow cùng tên job là check khác — bản xanh của CI không che bản đỏ/
        # đang chạy của workflow khác (review T-2404)
        run = {"__typename": "CheckRun", "workflowName": "Other", "name": "test", "status": "IN_PROGRESS"}
        red = {**run, "status": "COMPLETED", "conclusion": "FAILURE"}
        green = {"__typename": "CheckRun", "workflowName": "CI", "name": "test", "status": "COMPLETED"}
        green.update(conclusion="SUCCESS", startedAt="2026-10-21T15:58:00Z")
        for old, verdict in ((run, "wait"), (red, "fix")):
            old = {**old, "startedAt": "2026-10-21T15:50:00Z"}
            self.assertEqual(xt._ci_blocker({"statusCheckRollup": [old, green]})[0], verdict)
