"""ADR-0022: `xt.py grant-check` — việc production có nằm trong mục Ủy quyền production của PLAN.md không."""

from __future__ import annotations

import io
import json
import os
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

- grant: payments | mode=sandbox,live | max_per_txn=50 | refund=false
- [ ] `T-001` việc — Gate: `true`
"""


def run_main(*args: str) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        rc = xt.main([str(a) for a in args])
    return rc, out.getvalue(), err.getvalue()


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

    def v(self, group: str, **req: str) -> list[str]:
        return xt.grant_violations(self.grants, group, req)

    def test_group_missing_is_denied(self):
        self.assertEqual(
            self.v("auth_crypto"), ["nhóm `auth_crypto` không có trong mục Ủy quyền production của PLAN.md"]
        )

    def test_numeric_cap(self):
        self.assertEqual(self.v("payments", per_txn="50"), [])
        self.assertEqual(self.v("payments", per_txn="50.01"), ["per_txn=50.01 vượt max_per_txn=50"])
        self.assertIn("không phải số", self.v("payments", per_txn="nhiều")[0])

    def test_boolean_and_list_values(self):
        self.assertEqual(self.v("payments", mode="LIVE"), [])  # hạ chữ thường
        self.assertEqual(self.v("payments", mode="prod"), ["mode=prod ngoài ủy quyền (sandbox,live)"])
        self.assertEqual(self.v("payments", refund="false"), [])  # false chỉ nhận false
        self.assertEqual(self.v("payments", refund="true"), ["refund=true ngoài ủy quyền (false)"])
        self.assertEqual(self.v("data_delete", soft_only="false"), [])  # true cho phép cả hai
        self.assertEqual(self.v("data_delete", soft_only="có"), ["soft_only=có không phải true/false"])

    def test_unknown_key_and_no_request_params(self):
        self.assertEqual(self.v("payments", currency="vnd"), ["`currency` không có trong ủy quyền của nhóm"])
        self.assertEqual(self.v("secrets"), [])  # nhóm có mặt, không tham số → được
        self.assertEqual(len(self.v("payments", per_txn="99", mode="prod")), 2)


class GrantCheckCliTest(unittest.TestCase):
    def setUp(self):
        self.base = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.enterContext(unittest.mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(self.base)}))
        (self.base / "docs" / "autopilot").mkdir(parents=True)

    def write(self, text: str) -> None:
        (self.base / "docs" / "autopilot" / "PLAN.md").write_text(text, encoding="utf-8")

    def test_within_grant(self):
        self.write(PLAN)
        rc, out, _ = run_main("grant-check", "payments", "per_txn=30", "mode=live")
        self.assertEqual((rc, out), (0, "✓ trong ủy quyền production: payments per_txn=30 mode=live\n"))
        rc, out, _ = run_main("grant-check", "secrets")
        self.assertEqual((rc, out), (0, "✓ trong ủy quyền production: secrets\n"))

    def test_outside_grant_says_defer(self):
        self.write(PLAN)
        rc, out, _ = run_main("grant-check", "payments", "per_txn=500")
        self.assertEqual(rc, 1)
        self.assertIn("NGOÀI ủy quyền production: payments", out)
        self.assertIn("per_txn=500 vượt max_per_txn=50", out)
        self.assertIn("loop defer", out)

    def test_missing_plan_or_section_denies(self):
        rc, out, _ = run_main("grant-check", "payments")  # không có PLAN.md
        self.assertEqual(rc, 1)
        self.assertIn("không có trong mục Ủy quyền production", out)
        self.write("# PLAN\n- [ ] `T-001` việc — Gate: `true`\n")  # có PLAN, không có mục
        self.assertEqual(run_main("grant-check", "payments")[0], 1)

    def test_json_and_bad_param_and_plan_flag(self):
        self.write(PLAN)
        rc, out, _ = run_main("grant-check", "payments", "mode=prod", "--json")
        d = json.loads(out)
        self.assertEqual(
            (rc, d["group"], d["ok"], d["reasons"]), (1, "payments", False, ["mode=prod ngoài ủy quyền (sandbox,live)"])
        )
        rc, out, _ = run_main("grant-check", "payments", "--json")
        self.assertEqual((rc, json.loads(out)["ok"]), (0, True))
        for bad in ("amount", "=5"):
            rc, _, err = run_main("grant-check", "payments", bad)
            self.assertEqual(rc, 2)
            self.assertIn("phải dạng khoá=giá trị", err)
        (self.base / "OTHER.md").write_text("- grant: secrets | read_values=false\n", encoding="utf-8")
        self.assertEqual(run_main("grant-check", "secrets", "--plan", "OTHER.md")[0], 0)


if __name__ == "__main__":
    unittest.main()
