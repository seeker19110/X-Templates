"""Test cho `xt.py merge-check` — máy quyết khi nào merge PR đã mở (ADR-0013)."""

from __future__ import annotations

import base64
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
import unittest.mock
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import xt

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
        ["commit", "-qm", "x"],
        ["update-ref", "refs/remotes/origin/main", "HEAD"],
    ):
        subprocess.run([*git, *args], check=True, capture_output=True)
    if working is not None:
        (base / "xt.yaml").write_text(working, encoding="utf-8")


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
        raw: dict | None = None,
    ):
        self.pull = {
            "number": 7,
            "state": "open",
            "merged": False,
            "draft": False,
            "mergeable": True,
            "mergeable_state": "clean",
            "head": {"sha": self.SHA},
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
        self.raw = raw or {}
        self.calls: list[list[str]] = []

    def paths(self) -> list[str]:
        return [c[-1] for c in self.calls]

    def respond(self, cmd: list[str], **_: Any) -> subprocess.CompletedProcess:
        if cmd[0] == "git":  # merge_hard_mode đọc xt.yaml ở nhánh đích — không có repo → human
            return subprocess.CompletedProcess(cmd, 128, "", "not a git repository")
        self.calls.append(cmd)
        path = cmd[-1]
        files = [
            {"filename": f["path"], "additions": f["additions"], "deletions": f["deletions"]} for f in pr()["files"]
        ]
        routes = {
            f"{self.REPO}/pulls/7": json.dumps(self.pull),
            f"{self.REPO}/pulls/7/files?per_page=100": json.dumps(files[:2]) + json.dumps(files[2:]),
            f"{self.REPO}/pulls/7/reviews?per_page=100": json.dumps(self.reviews),
            f"{self.REPO}/commits/{self.SHA}/check-runs?per_page=100": json.dumps({"check_runs": self.runs[:1]})
            + "\n"
            + json.dumps({"check_runs": self.runs[1:]}),
            f"{self.REPO}/commits/{self.SHA}/status?per_page=100": json.dumps({"statuses": self.statuses}),
        }
        if path in self.raw:
            out = self.raw[path]
        elif "/pulls?head=" in path:
            out = json.dumps(self.open_prs)
        else:
            out = routes[path]
        return subprocess.CompletedProcess(cmd, 0, out, "")

    def patch(self) -> Any:
        return unittest.mock.patch.object(xt.subprocess, "run", side_effect=self.respond)


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
        # `update` bằng git (gh pr update-branch cần GraphQL — phiên Claude Code chặn)
        self.assertEqual(
            xt.merge_decision(pr(mergeStateStatus="BEHIND", baseRefName="dev"), 2)["next"],
            "git fetch origin dev && git merge origin/dev && git push (hoặc gh pr update-branch 7)",
        )

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

    def test_touches_hard_key(self):
        """Diff xt.yaml chạm khoá, hoặc thiếu patch (diff lớn — không xác minh được) → chạm; file khác → không."""
        self.assertTrue(xt._touches_hard_key({"filename": "xt.yaml", "patch": "+merge_hard_exceptions: auto"}))
        self.assertTrue(xt._touches_hard_key({"filename": "x.yml", "previous_filename": "xt.yaml"}))
        self.assertFalse(xt._touches_hard_key({"filename": "xt.yaml", "patch": "+lint: x"}))
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
        (self.base / "xt.yaml").write_text("merge_autonomy: L2\n", encoding="utf-8")

    def test_hard_auto_from_xt_yaml(self):
        hot = pr(files=[{"path": "src/payment/charge.py", "additions": 1, "deletions": 0}])
        commit_base_xt(self.base, "merge_autonomy: L3\nmerge_hard_exceptions: auto\n")
        rc, out, _ = run_main("merge-check", "--json", "--pr-json", "-", stdin=json.dumps(hot))
        d = json.loads(out)
        self.assertEqual((rc, d["verdict"], d["hard"], d["notes"]), (0, "merge", [], []))
        self.assertTrue(d["hard_waived"])
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
        gh = FakeGh()
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
            self.assertEqual(xt._pr_rest("7"), pr(reviewDecision=""))  # cùng dict với fixture `gh pr view`
        cases = {
            "merged": ({"merged": True, "state": "closed"}, "state", "MERGED"),
            "đang tính": ({"mergeable": None, "mergeable_state": "unknown"}, "mergeable", "UNKNOWN"),
            "xung đột": ({"mergeable": False, "mergeable_state": "dirty"}, "mergeStateStatus", "DIRTY"),
            "nháp": ({"draft": True}, "isDraft", True),
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
    """ADR-0016: guard không bật auto-merge (L3) cho PR thuộc ngoại lệ cứng — kể cả lúc mới mở, CI còn chạy."""

    def test_guard_auto_merge_refuses_hard_exception(self):
        sys.path.insert(0, str(ROOT / ".claude" / "hooks"))
        import guard

        base = {"verdict": "wait", "autonomy": 3, "stacked": False, "repo": "o/r", "hard": []}
        with unittest.mock.patch.object(guard, "merge_check", return_value=base):
            self.assertEqual(guard._auto_merge_verdict(["7"], ".", "o/r")[0], "allow")
        hard = {**base, "hard": ["đường dẫn nhạy cảm (auth): src/auth/x.py"]}
        with unittest.mock.patch.object(guard, "merge_check", return_value=hard):
            dec, why = guard._auto_merge_verdict(["7"], ".", "o/r")
        self.assertEqual(dec, "ask")
        self.assertIn("LOOP-STOP-005", why)


if __name__ == "__main__":
    unittest.main()


class MergeWatchTest(unittest.TestCase):
    """ADR-0021: `merge-watch` gọi merge-check định kỳ (mặc định 30 s) tới khi verdict ≠ wait."""

    def setUp(self):
        self.base = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.enterContext(unittest.mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(self.base)}))
        (self.base / "xt.yaml").write_text("merge_autonomy: L2\n", encoding="utf-8")
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
        with unittest.mock.patch.object(xt, "_merge_check_json", side_effect=lambda pr: next(seq)):
            rc, out, _ = run_main("merge-watch", "--pr", "7", *extra)
        return rc, out

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
        with FakeGh().patch():
            rc, d, err = xt._merge_check_json("7")
        self.assertEqual((rc, d["verdict"], err), (0, "merge", ""))
        with unittest.mock.patch.object(xt, "load_pr", side_effect=xt.PrInputError("hỏng")):
            rc, d, err = xt._merge_check_json("7")
        self.assertEqual((rc, d), (2, {}))
        self.assertIn("hỏng", err)
