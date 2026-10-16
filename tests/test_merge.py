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
        self.assertEqual(xt.merge_decision(pr(mergeStateStatus="BEHIND"), 2)["next"], "gh pr update-branch 7")

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
        self.assertEqual((none["verdict"], none["reasons"]), ("human", ["không có check CI nào — không có bằng chứng"]))

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
        self.assertEqual(d["reasons"], ["nhãn rủi ro: risk:payment"])
        d = xt.merge_decision(pr(), 2, risk_paths=["src/cart/*"])
        self.assertEqual(d["reasons"], ["đường dẫn nhạy cảm (merge_risk_paths): src/cart/total.py"])

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

    def test_fetches_with_gh(self):
        done = subprocess.CompletedProcess([], 0, json.dumps(pr()), "")
        with unittest.mock.patch.object(xt.subprocess, "run", return_value=done) as run:
            rc, _, _ = run_main("merge-check", "--pr", "7")
        self.assertEqual(rc, 0)
        self.assertEqual(run.call_args[0][0][:4], ["gh", "pr", "view", "7"])
        self.assertIn("statusCheckRollup", run.call_args[0][0][5])
        with unittest.mock.patch.object(xt.subprocess, "run", return_value=done) as run:
            run_main("merge-check")
        self.assertEqual(run.call_args[0][0][:4], ["gh", "pr", "view", "--json"])

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


if __name__ == "__main__":
    unittest.main()
