"""`xt.py license-check` (BASE-DEP-005): license gói đã cài của file requirements ghim đối chiếu allowlist
`license-allow.json`; ngoại lệ có người duyệt và hạn; vi phạm hoặc ngoại lệ quá hạn → exit 1."""

from __future__ import annotations

import contextlib
import datetime as dt
import io
import json
import sys
import tempfile
import unittest
from email.message import Message
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import xt

TODAY = dt.date(2026, 10, 20)
EXC = {"package": "pathspec", "license": "MPL-2.0", "approved_by": "chủ repo", "expires": "2027-10-20"}


def meta(**fields: Any) -> Message:
    m = Message()
    for k, v in fields.items():
        for x in v if isinstance(v, list) else [v]:
            m[k.replace("_", "-")] = x
    return m


def run(*argv: str) -> Tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = xt.main(["license-check", *argv])
    return rc, out.getvalue(), err.getvalue()


class LicenseParseTest(unittest.TestCase):
    def test_requirements_pins_and_markers(self):
        text = (
            "# chú thích\nruff==0.17.1 \\\n    --hash=sha256:aa\n    # via -r req.in\n"
            "librt==0.16.0 ; platform_python_implementation != 'PyPy' \\\n-r other.txt\nflask>=2\n"
        )
        self.assertEqual(xt.license_requirements(text), [("ruff", "0.17.1", False), ("librt", "0.16.0", True)])

    def test_requirements_extras_spaces_and_markers(self):
        text = (
            "requests[security,socks]==2.32.0 \\\n    --hash=sha256:aa\n"
            "pkg == 1.2.3\n"
            "other  [extra]  ==  4.5 ; python_version >= '3.11' \\\n"
            "tool[x]==0.1; sys_platform == 'win32'\n"
            "loose[x]>=1\nbroken[==1\n"
        )
        self.assertEqual(
            xt.license_requirements(text),
            [
                ("requests", "2.32.0", False),
                ("pkg", "1.2.3", False),
                ("other", "4.5", True),
                ("tool", "0.1", True),
            ],
        )

    def test_policy_valid_and_errors(self):
        allowed, exc = xt.license_policy(
            json.dumps({"allow": ["MIT"], "exceptions": [{**EXC, "package": "Path_Spec"}]})
        )
        self.assertEqual((allowed, list(exc)), ({"MIT"}, ["path-spec"]))
        self.assertEqual(xt.license_policy('{"allow": ["MIT"]}'), ({"MIT"}, {}))
        bad = (
            "{",
            "[]",
            '{"allow": "MIT", "exceptions": []}',
            '{"allow": [""], "exceptions": []}',
            '{"allow": ["MIT"], "exceptions": {}}',
            json.dumps({"allow": ["MIT"], "exceptions": ["x"]}),
            json.dumps({"allow": ["MIT"], "exceptions": [{**EXC, "approved_by": " "}]}),
            json.dumps({"allow": ["MIT"], "exceptions": [{**EXC, "expires": "mai"}]}),
        )
        for text in bad:
            with self.subTest(text=text), self.assertRaises(xt.LicenseConfigError):
                xt.license_policy(text)

    def test_license_of(self):
        self.assertEqual(xt.license_of(meta(License_Expression="MIT", License="BSD")), "MIT")
        self.assertEqual(xt.license_of(meta(License="Apache-2.0")), "Apache-2.0")
        long_text = meta(
            License="Permission is hereby granted " * 5, Classifier="License :: OSI Approved :: MIT License"
        )
        self.assertEqual(xt.license_of(long_text), "MIT")
        multi = meta(
            License="a\nb",
            Classifier=[
                "Programming Language :: Python",
                "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
                "License :: OSI Approved :: BSD License",
            ],
        )
        self.assertEqual(xt.license_of(multi), "? OR MPL-2.0")
        self.assertEqual(xt.license_of(meta()), "")

    def test_license_allowed(self):
        allowed = {"MIT", "Apache-2.0", "BSD-2-Clause"}
        cases = {
            "": False,
            "MIT": True,
            "GPL-3.0-only": False,
            "Apache-2.0 OR BSD-2-Clause": True,
            "GPL-3.0-only OR MIT": True,
            "MIT AND Apache-2.0": True,
            "MIT AND GPL-3.0-only": False,
            "MIT AND (Apache-2.0 OR BSD-2-Clause)": True,
            "MIT AND (Apache-2.0 OR GPL-3.0-only)": False,  # ngoặc → bảo thủ: mọi định danh phải được
            "()": False,
            "? OR MIT": True,
            "?": False,
        }
        for expr, ok in cases.items():
            with self.subTest(expr=expr):
                self.assertEqual(xt.license_allowed(expr, allowed), ok)


class LicenseCheckTest(unittest.TestCase):
    def check(
        self, reqs: List[Tuple[str, str, bool]], dists: Dict[str, Tuple[str, Message]], today: dt.date = TODAY
    ) -> Tuple[List[str], List[str]]:
        lookup: Any = lambda n: dists.get(n)  # noqa: E731
        return xt.license_check(reqs, {"MIT"}, {"pathspec": EXC}, today, lookup)

    def test_allowed_exception_and_drift(self):
        dists = {
            "ruff": ("0.17.1", meta(License_Expression="MIT")),
            "pathspec": ("1.1.1", meta(Classifier="License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)")),
            "mypy": ("2.5.0", meta(License_Expression="MIT")),
        }
        bad, info = self.check(
            [("ruff", "0.17.1", False), ("pathspec", "1.1.1", False), ("mypy", "2.4.0", False)], dists
        )
        self.assertEqual(bad, [])
        self.assertIn("✓ ruff 0.17.1: MIT", info)
        self.assertIn("ngoại lệ (chủ repo; tới 2027-10-20)", info[1])
        self.assertIn("(đã cài 2.5.0, ghim 2.4.0)", info[2])

    def test_violations(self):
        dists: Dict[str, Tuple[str, Message]] = {
            "gplpkg": ("1.0", meta(License_Expression="GPL-3.0-only")),
            "pathspec": ("2.0", meta(License_Expression="GPL-3.0-only")),  # ngoại lệ chỉ cho đúng license đã duyệt
            "blank": ("1.0", meta()),
        }
        reqs = [("gplpkg", "1.0", False), ("pathspec", "2.0", False), ("blank", "1.0", False), ("gone", "1", False)]
        bad, _ = self.check([*reqs, ("librt", "0.16.0", True)], dists)
        self.assertEqual(len(bad), 4, bad)
        self.assertIn("gplpkg 1.0: license `GPL-3.0-only` ngoài allowlist", bad[0])
        self.assertIn("pathspec 2.0", bad[1])
        self.assertIn("`không khai`", bad[2])
        self.assertIn("gone==1: chưa cài", bad[3])
        _, info = self.check([("librt", "0.16.0", True)], {})
        self.assertIn("có marker nền tảng", info[0])

    def test_expired_exception_is_violation(self):
        dists = {"pathspec": ("1.1.1", meta(License_Expression="MPL-2.0"))}
        self.assertEqual(self.check([("pathspec", "1.1.1", False)], dists, dt.date(2027, 10, 20))[0], [])
        bad, _ = self.check([("pathspec", "1.1.1", False)], dists, dt.date(2027, 10, 21))
        self.assertEqual(len(bad), 2)
        self.assertIn("hết hạn 2027-10-20", bad[0])
        self.assertIn("không có ngoại lệ", bad[1])
        self.assertIn("hết hạn", self.check([], {}, dt.date(2030, 1, 1))[0][0])  # cả ngoại lệ không dùng tới

    def test_installed_dist(self):
        got: Optional[Tuple[str, Any]] = xt._installed_dist("pip")
        self.assertIsNotNone(got)
        self.assertIsNone(xt._installed_dist("xt-khong-co-goi-nay"))


class LicenseCheckCliTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.d = Path(tmp.name)
        self.allow = self.d / "allow.json"
        self.allow.write_text(json.dumps({"allow": ["MIT"], "exceptions": []}), encoding="utf-8")
        self.req = self.d / "req.txt"

    def test_repo_allowlist_passes(self):
        """Allowlist thật của repo với requirements-dev.txt. Trình thông dịch đã cài gói (job `lint`, máy dev) → exit 0; job
        `py311` chạy test bằng 3.11 mà gói cài cho 3.13 → chỉ được phép báo "chưa cài", không vi phạm license nào."""
        rc, out, _ = run(
            "--allow", str(ROOT / "license-allow.json"), "--requirements", str(ROOT / "requirements-dev.txt")
        )
        errors = [line for line in out.splitlines() if line.startswith("✗")]
        # Đếm gói ghim từ requirements-dev.txt thay vì ghi cứng (thêm shellcheck-py ở T-1812 từng làm test đỏ).
        lines = (ROOT / "requirements-dev.txt").read_text(encoding="utf-8").splitlines()
        pinned = sum(1 for line in lines if line[:1].isalnum() and "==" in line.split(" ", 1)[0])
        passed = rc == 0 and f"✓ license-check: {pinned} gói ghim" in out
        only_missing = rc == 1 and bool(errors) and all(": chưa cài" in line for line in errors)
        self.assertTrue(passed or only_missing, out)

    def test_violation_exit_1(self):
        self.req.write_text("xt-khong-co-goi-nay==1.0\n", encoding="utf-8")
        rc, out, _ = run("--allow", str(self.allow), "--requirements", str(self.req), "--today", "2026-10-20")
        self.assertEqual(rc, 1)
        self.assertIn("✗ xt-khong-co-goi-nay==1.0: chưa cài", out)

    def test_config_errors_exit_2(self):
        self.req.write_text("", encoding="utf-8")
        for argv in (
            ("--allow", str(self.d / "khong-co.json"), "--requirements", str(self.req)),
            ("--allow", str(self.allow), "--requirements", str(self.d / "khong-co.txt")),
            ("--allow", str(self.allow), "--requirements", str(self.req), "--today", "hôm nay"),
        ):
            with self.subTest(argv=argv):
                rc, _, err = run(*argv)
                self.assertEqual(rc, 2)
                self.assertIn("✗ license-check:", err)

    def test_default_requirements_file(self):
        self.req.write_text("", encoding="utf-8")
        with contextlib.chdir(self.d):
            (self.d / "requirements-dev.txt").write_text("", encoding="utf-8")
            rc, out, _ = run("--allow", str(self.allow))
        self.assertEqual((rc, out.strip()), (0, f"✓ license-check: 0 gói ghim khớp allowlist {self.allow}."))


if __name__ == "__main__":
    unittest.main()
