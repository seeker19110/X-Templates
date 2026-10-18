"""ADR-0022: `xt.py grant-check` — việc production có nằm trong mục Ủy quyền production (PLAN.md ở nhánh mặc định) không."""

from __future__ import annotations

import base64
import io
import json
import sys
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


def fake_default_branch(plans: dict[str, str]):
    """`_gh_one` giả: chỉ có nội dung REST của NHÁNH MẶC ĐỊNH (không `?ref=`); đường vắng → 404 như gh."""

    def fake(path: str) -> dict:
        key = path.split("/contents/", 1)[1]
        assert "?ref=" not in key, "grant-check không được đọc ref cục bộ/tuỳ chọn"
        if key not in plans:
            raise xt.PrInputError(f"gh api {path} lỗi: gh: Not Found (HTTP 404)")
        body = base64.b64encode(plans[key].encode()).decode()
        return {"type": "file", "path": key, "encoding": "base64", "content": body}

    return fake


PLAN_PATH = "docs/autopilot/PLAN.md"


class GrantCheckCliTest(unittest.TestCase):
    def use(self, plans: dict[str, str] | None = None, **kw):
        """Giả REST nhánh mặc định; trả mock để xem lời gọi."""
        side = fake_default_branch(plans if plans is not None else {PLAN_PATH: PLAN})
        return self.enterContext(unittest.mock.patch.object(xt, "_gh_one", side_effect=kw.get("side", side)))

    def check(self, group: str, *params: str, extra: tuple[str, ...] = ()) -> tuple[int, str, str]:
        return run_main("grant-check", group, *params, *extra)

    def test_within_grant_reads_default_branch_via_rest(self):
        one = self.use()
        rc, out, _ = self.check("payments", "per_txn=30", "mode=live", "refund=false")
        self.assertEqual((rc, out), (0, "✓ trong ủy quyền production: payments per_txn=30 mode=live refund=false\n"))
        self.assertEqual(one.call_args.args, (f"repos/{{owner}}/{{repo}}/contents/{PLAN_PATH}",))  # không ref
        self.assertEqual(self.check("secrets", "read_values=false")[0], 0)

    def test_outside_grant_says_defer(self):
        self.use()
        rc, out, _ = self.check("payments", "per_txn=500", "mode=sandbox", "refund=false")
        self.assertEqual(rc, 1)
        self.assertIn("NGOÀI ủy quyền production: payments", out)
        self.assertIn("per_txn=500 vượt max_per_txn=50", out)
        self.assertIn("loop defer", out)

    def test_missing_file_or_section_denies(self):
        self.use({})  # PLAN.md chưa có ở nhánh mặc định (PR duyệt kế hoạch chưa merge)
        rc, out, _ = self.check("payments", "mode=sandbox")
        self.assertEqual(rc, 1)
        self.assertIn("không có trong mục Ủy quyền production", out)
        self.assertNotIn("không đọc được", out)  # 404 là "vắng", không phải lỗi đọc
        self.use({PLAN_PATH: "# PLAN\n- [ ] `T-001` việc — Gate: `true`\n"})  # có PLAN, không có mục
        self.assertEqual(self.check("payments", "mode=sandbox")[0], 1)

    def test_unreadable_denies_and_says_so(self):
        """gh/mạng lỗi, hoặc file lớn (content rỗng + encoding none) → không xác minh được → ngoài ủy quyền."""

        def boom(path: str) -> dict:
            raise xt.PrInputError("gh api lỗi: timeout")

        self.use(side=boom)
        rc, out, _ = self.check("secrets", "read_values=false")
        self.assertEqual(rc, 1)
        self.assertIn("không đọc được PLAN.md ở nhánh mặc định", out)
        self.use(side=lambda path: {"content": "", "encoding": "none"})
        rc, out, _ = self.check("secrets", "read_values=false")
        self.assertEqual(rc, 1)
        self.assertIn("không đọc được PLAN.md ở nhánh mặc định", out)

    def test_plan_flag_locked_to_plan_path(self):
        """Chỉ đường PLAN mà merge-check giữ cho người merge; file khác (docs/notes.md) không được dùng làm nguồn ủy quyền."""
        self.use({"docs/notes.md": PLAN, f"sub/{PLAN_PATH}": PLAN, PLAN_PATH: "# PLAN\n"})
        rc, _, err = self.check("secrets", "read_values=false", extra=("--plan", "docs/notes.md"))
        self.assertEqual(rc, 2)
        self.assertIn("kết thúc bằng docs/autopilot/PLAN.md", err)
        self.assertEqual(self.check("secrets", "read_values=false", extra=("--plan", f"sub/{PLAN_PATH}"))[0], 0)
        self.assertEqual(self.check("secrets", "read_values=false")[0], 1)  # PLAN mặc định không có grant
        for bad in (f"../{PLAN_PATH}", f"a/../{PLAN_PATH}", f"a//{PLAN_PATH}", f"./{PLAN_PATH}", f"/{PLAN_PATH}"):
            with self.subTest(bad):
                rc, _, err = self.check("secrets", "read_values=false", extra=("--plan", bad))
                self.assertEqual(rc, 2)
                self.assertIn("không có `..`", err)

    def test_symlinked_plan_is_unreadable(self):
        """Review lần ba: PLAN.md là symlink → API trả file đích (path khác) → không xác minh được → ngoài ủy quyền."""
        body = base64.b64encode(PLAN.encode()).decode()
        self.use(side=lambda path: {"type": "file", "path": "docs/notes.md", "encoding": "base64", "content": body})
        rc, out, _ = self.check("secrets", "read_values=false")
        self.assertEqual(rc, 1)
        self.assertIn("không đọc được PLAN.md ở nhánh mặc định", out)

    def test_json_and_bad_param(self):
        self.use()
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


if __name__ == "__main__":
    unittest.main()
