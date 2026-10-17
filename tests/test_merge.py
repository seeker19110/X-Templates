"""Test cho `xt.py merge-check` — máy quyết khi nào merge PR đã mở (ADR-0013)."""

from __future__ import annotations

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
