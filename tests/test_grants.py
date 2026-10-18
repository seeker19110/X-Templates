"""ADR-0022: `xt.py grant-check` — việc production có nằm trong mục Ủy quyền production (PLAN.md đã commit) không."""

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

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import xt  # noqa: E402

PLAN = """# PLAN

## Ủy quyền production

- grant: payments | mode=sandbox,live | max_per_txn=50 | refund=false
- grant: data_delete | soft_only=true | max_rows=100
  - grant: secrets | read_values=false

```
- grant: outbound_messages | live=true | max_per_hour=9999
```

- [ ] `T-001` việc — Gate: `true`
"""

# Yêu cầu đầy đủ (khai mọi khoá của nhóm) trong hạn — mỗi test chỉ đổi đúng một khoá.
FULL = {
    "payments": {"mode": "sandbox", "per_txn": "0", "refund": "false"},
    "data_delete": {"soft_only": "true", "rows": "1"},
    "secrets": {"read_values": "false"},
}


def run_main(*args: str) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        rc = xt.main([str(a) for a in args])
    return rc, out.getvalue(), err.getvalue()


def commit_plan(base: Path, committed: str, working: str | None = None, branch: str = "main") -> None:
    """Repo git tạm: `origin/<branch>` có PLAN.md = `committed`; cây làm việc = `working` (mặc định như commit)."""
    plan = base / "docs" / "autopilot" / "PLAN.md"
    plan.parent.mkdir(parents=True, exist_ok=True)
    plan.write_text(committed, encoding="utf-8")
    git = ["git", "-C", str(base), "-c", "user.email=t@t", "-c", "user.name=t", "-c", "commit.gpgsign=false"]
    for args in (
        ["init", "-q"],
        ["add", "-A"],
        ["commit", "-qm", "x"],
        ["update-ref", f"refs/remotes/origin/{branch}", "HEAD"],
    ):
        subprocess.run([*git, *args], check=True, capture_output=True)
    if working is not None:
        plan.write_text(working, encoding="utf-8")


class ParseGrantsTest(unittest.TestCase):
    def test_parses_outside_fences_lowercases_and_last_wins(self):
        g = xt.parse_grants(PLAN + "- grant: payments | MODE=Sandbox | max_per_txn = 5\n")
        self.assertEqual(set(g), {"payments", "data_delete", "secrets"})  # nhóm trong code fence bị bỏ qua
        self.assertEqual(g["payments"], {"mode": "sandbox", "max_per_txn": "5"})  # dòng sau thắng
        self.assertEqual(g["secrets"], {"read_values": "false"})  # thụt lề vẫn nhận (đã strip)

    def test_no_grants_means_nothing_granted(self):
        self.assertEqual(xt.parse_grants("# PLAN\n- [ ] `T-001` việc — Gate: `true`\n"), {})
        self.assertEqual(xt.parse_grants("- grant: payments | bad line without equals\n"), {})


class ViolationsTest(unittest.TestCase):
    grants = xt.parse_grants(PLAN)

    def v(self, group: str, **over: str) -> list[str]:
        return xt.grant_violations(self.grants, group, {**FULL.get(group, {}), **over})

    def test_group_missing_is_denied(self):
        self.assertEqual(
            xt.grant_violations(self.grants, "auth_crypto", {}),
            ["nhóm `auth_crypto` không có trong mục Ủy quyền production của PLAN.md"],
        )

    def test_full_request_within_grant(self):
        for group in FULL:
            self.assertEqual(self.v(group), [], group)

    def test_numeric_cap_rejects_over_negative_and_non_finite(self):
        self.assertEqual(self.v("payments", per_txn="50"), [])
        self.assertEqual(self.v("payments", per_txn="50.01"), ["per_txn=50.01 vượt max_per_txn=50"])
        self.assertIn("không phải số", self.v("payments", per_txn="nhiều")[0])
        for bad in ("-500", "nan", "inf", "-inf"):
            self.assertEqual(self.v("payments", per_txn=bad), [f"per_txn={bad} không phải số hữu hạn ≥ 0"], bad)
        self.assertEqual(self.v("payments", per_txn="1e9"), ["per_txn=1e9 vượt max_per_txn=50"])

    def test_boolean_and_list_values(self):
        self.assertEqual(self.v("payments", mode="LIVE"), [])  # hạ chữ thường
        self.assertEqual(self.v("payments", mode="prod"), ["mode=prod ngoài ủy quyền (sandbox,live)"])
        self.assertEqual(self.v("payments", refund="true"), ["refund=true ngoài ủy quyền (false)"])
        self.assertEqual(self.v("data_delete", soft_only="false"), [])  # true cho phép cả hai
        self.assertEqual(self.v("data_delete", soft_only="có"), ["soft_only=có không phải true/false"])

    def test_unknown_key_and_key_case(self):
        self.assertEqual(self.v("payments", currency="vnd"), ["`currency` không có trong ủy quyền của nhóm"])
        self.assertEqual(
            xt.grant_violations(self.grants, "payments", {"MODE": "LIVE", "Per_Txn": "5", "REFUND": "false"}), []
        )

    def test_must_declare_every_constrained_key(self):
        """Khoá không khai không được coi là trong hạn (review ADR-0022): `grant-check payments` trống không được qua."""
        miss = xt.grant_violations(self.grants, "payments", {})
        self.assertEqual(len(miss), 3)
        self.assertTrue(all("thiếu khoá" in m for m in miss))
        self.assertEqual(
            xt.grant_violations(self.grants, "payments", {"per_txn": "10"}),
            [
                "thiếu khoá `mode` (ủy quyền ràng buộc nó — khai đủ mọi khoá của nhóm)",
                "thiếu khoá `refund` (ủy quyền ràng buộc nó — khai đủ mọi khoá của nhóm)",
            ],
        )
        self.assertEqual(len(xt.grant_violations(self.grants, "secrets", {})), 1)
        self.assertEqual(len(self.v("payments", per_txn="99", mode="prod")), 2)


class GrantCheckCliTest(unittest.TestCase):
    def setUp(self):
        self.base = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.enterContext(unittest.mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(self.base)}))

    def check(self, group: str, *params: str, extra: tuple[str, ...] = ()) -> tuple[int, str, str]:
        return run_main("grant-check", group, *params, *extra)

    def test_within_grant(self):
        commit_plan(self.base, PLAN)
        rc, out, _ = self.check("payments", "per_txn=30", "mode=live", "refund=false")
        self.assertEqual((rc, out), (0, "✓ trong ủy quyền production: payments per_txn=30 mode=live refund=false\n"))
        self.assertEqual(self.check("secrets", "read_values=false")[0], 0)

    def test_outside_grant_says_defer(self):
        commit_plan(self.base, PLAN)
        rc, out, _ = self.check("payments", "per_txn=500", "mode=sandbox", "refund=false")
        self.assertEqual(rc, 1)
        self.assertIn("NGOÀI ủy quyền production: payments", out)
        self.assertIn("per_txn=500 vượt max_per_txn=50", out)
        self.assertIn("loop defer", out)

    def test_reads_committed_branch_not_working_tree(self):
        """Lỗ review ADR-0022: agent sửa PLAN.md tại chỗ (chưa commit) không được tự cấp ủy quyền."""
        sandbox = "- grant: payments | mode=sandbox | max_per_txn=0 | refund=false\n"
        live = "- grant: payments | mode=live | max_per_txn=1e9 | refund=true\n"
        commit_plan(self.base, sandbox, working=live)
        rc, out, _ = self.check("payments", "mode=live", "per_txn=5000", "refund=true")
        self.assertEqual(rc, 1)
        self.assertIn("mode=live ngoài ủy quyền (sandbox)", out)
        self.assertEqual(self.check("payments", "mode=sandbox", "per_txn=0", "refund=false")[0], 0)

    def test_missing_branch_file_or_section_denies(self):
        rc, out, _ = self.check("payments")  # không phải repo git
        self.assertEqual(rc, 1)
        self.assertIn("không có trong mục Ủy quyền production", out)
        commit_plan(self.base, "# PLAN\n- [ ] `T-001` việc — Gate: `true`\n")  # có PLAN, không có mục
        self.assertEqual(self.check("payments", "mode=sandbox")[0], 1)

    def test_plan_path_and_ref_flags_and_default_ref(self):
        commit_plan(self.base, PLAN, branch="master")
        self.assertEqual(self.check("secrets", "read_values=false")[0], 1)  # origin/main không tồn tại
        self.assertEqual(self.check("secrets", "read_values=false", extra=("--ref", "origin/master"))[0], 0)
        subprocess.run(
            ["git", "-C", str(self.base), "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/master"],
            check=True,
            capture_output=True,
        )
        self.assertEqual(xt._default_ref(self.base), "origin/master")
        self.assertEqual(self.check("secrets", "read_values=false")[0], 0)  # theo origin/HEAD
        self.assertEqual(self.check("secrets", "read_values=false", extra=("--plan", "../PLAN.md"))[0], 1)
        self.assertEqual(self.check("secrets", "read_values=false", extra=("--plan", "no/such.md"))[0], 1)

    def test_json_and_bad_param(self):
        commit_plan(self.base, PLAN)
        rc, out, _ = run_main("grant-check", "payments", "mode=prod", "per_txn=0", "refund=false", "--json")
        d = json.loads(out)
        self.assertEqual(
            (rc, d["group"], d["ok"], d["reasons"]), (1, "payments", False, ["mode=prod ngoài ủy quyền (sandbox,live)"])
        )
        rc, out, _ = run_main("grant-check", "secrets", "read_values=false", "--json")
        self.assertEqual((rc, json.loads(out)["ok"]), (0, True))
        for bad in ("amount", "=5"):
            rc, _, err = self.check("payments", bad)
            self.assertEqual(rc, 2)
            self.assertIn("phải dạng khoá=giá trị", err)

    def test_default_ref_without_origin_head(self):
        commit_plan(self.base, PLAN)
        self.assertEqual(xt._default_ref(self.base), "origin/main")


if __name__ == "__main__":
    unittest.main()
