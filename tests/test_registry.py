"""`xt.py registry` + `GET /api/registry` (ADR-0068 lát E, T-3691): schema 1, lệch core/gói so với VERSION khung, ngoại
lệ hết hạn, `--json`/`--strict`, file thiếu/hỏng, màn app chỉ đọc (token đúng/sai, gọi đồng thời)."""

from __future__ import annotations

import contextlib
import copy
import datetime as _dt
import http.client
import io
import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
import unittest.mock as mock
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import xt
from xt_app import api_registry, server

TODAY = "2026-11-05"


def product(**kw: Any) -> Dict[str, Any]:
    base: Dict[str, Any] = {
        "repo": "o/a",
        "owner": "chủ",
        "type": None,
        "risk": None,
        "core": None,
        "pack": None,
        "environments": [],
        "slo": "",
        "release": None,
        "exceptions": [],
    }
    base.update(kw)
    return base


def registry(*products: Dict[str, Any]) -> Dict[str, Any]:
    return {"schema": 1, "products": list(products)}


class Sandbox:
    """Dự án tạm (`CLAUDE_PROJECT_DIR`) + khung tạm `<tmp>/fw/framework` với `<tmp>/fw/VERSION`."""

    def __init__(self, version: Optional[str] = "3.29.2", packs: Optional[List[str]] = None) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        self.base = root / "dự-án"
        self.framework = root / "fw" / "framework"
        self.framework.mkdir(parents=True)
        self.base.mkdir()
        if version is not None:
            (self.framework.parent / "VERSION").write_text(version + "\n", encoding="utf-8")
        if packs is not None:
            (self.framework / "templates" / "packs").mkdir(parents=True)
        for pid in packs or []:
            (self.framework / "templates" / "packs" / pid).mkdir()
            (self.framework / "templates" / "packs" / pid / "pack.json").write_text("{}", encoding="utf-8")
        self.file = self.base / "docs" / "ops" / "registry.json"

    def write(self, data: Any) -> None:
        self.file.parent.mkdir(parents=True, exist_ok=True)
        text = data if isinstance(data, str) else json.dumps(data, ensure_ascii=False)
        self.file.write_text(text, encoding="utf-8")

    def run(self, *args: str) -> Tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        env = {"CLAUDE_PROJECT_DIR": str(self.base)}
        with mock.patch.dict(os.environ, env), contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = xt.main(["--framework", str(self.framework), "registry", *args])
        return rc, out.getvalue(), err.getvalue()

    def report(self, data: Dict[str, Any]) -> Dict[str, Any]:
        self.write(data)
        rc, out, err = self.run("--json", "--today", TODAY)
        assert rc == 0, err
        result: Dict[str, Any] = json.loads(out)
        return result

    def __enter__(self) -> "Sandbox":
        return self

    def __exit__(self, *exc: Any) -> None:
        self._tmp.cleanup()


class SchemaTest(unittest.TestCase):
    def errors(self, data: Any) -> List[str]:
        return xt.registry_errors(data)

    def test_valid_full_product(self) -> None:
        p = product(
            type="web-api",
            risk="high",
            core="3.29.2",
            pack={"id": "web-api-ts", "version": "3.29.2"},
            environments=["staging", "prod"],
            slo="99.9 % / 30 ngày",
            release={"version": "1.2.0", "date": "2026-10-01", "digest": "sha256:ab"},
            exceptions=[{"id": "EX-1", "until": "2026-12-01", "why": "chờ nâng"}],
        )
        self.assertEqual(self.errors(registry(p, product(repo="o/b"))), [])
        self.assertEqual(self.errors(registry()), [])

    def test_root_errors(self) -> None:
        schema_err = ['gốc phải là object có "schema": 1']
        for bad in ([], None, {"products": []}, {"schema": True, "products": []}, {"schema": 1.0, "products": []}):
            with self.subTest(bad=bad):
                self.assertEqual(self.errors(bad), schema_err)
        self.assertEqual(self.errors({"schema": 2, "products": []}), schema_err)
        self.assertEqual(self.errors({"schema": 1, "products": {}}), ["products: phải là mảng"])
        self.assertEqual(self.errors({"schema": 1, "products": [], "x\x1b": 1}), ["khoá lạ ở gốc 'x\\x1b'"])

    def test_version_digits_bounded_ascii(self) -> None:
        """Review lát E: số rất dài từng làm `int()` văng (exit 1, API 500); chữ số không ASCII, 0 đứng đầu bị nhận."""
        for bad in ("9" * 5000 + ".0.0", "٣.٢٩.٢", "３.２９.２", "03.029.002", "1234567890.0.0"):
            with self.subTest(core=bad):
                self.assertEqual(
                    self.errors(registry(product(core=bad))), ["products[0].core: phải là X.Y.Z hoặc null"]
                )
        self.assertEqual(self.errors(registry(product(core="0.10.999999999"))), [])

    def test_text_fields_printable(self) -> None:
        for bad in ("\ud800", "a\x1bb", "a\nb"):
            with self.subTest(owner=bad):
                self.assertEqual(
                    self.errors(registry(product(owner=bad))), ["products[0].owner: phải là chuỗi không rỗng"]
                )

    def test_product_shape(self) -> None:
        self.assertEqual(self.errors(registry("x")), ["products[0]: phải là object"])
        p = product()
        del p["slo"]
        p["extra"] = 1
        self.assertEqual(self.errors(registry(p)), ["products[0]: thiếu khoá slo", "products[0]: khoá lạ 'extra'"])

    def test_each_field(self) -> None:
        cases = {
            "repo": ["a", "a/b/c", "", 1, "a b/c"],
            "owner": ["", "  ", None],
            "type": ["", 1],
            "risk": ["critical", ["low"]],
            "core": ["3.1", "v3.1.0", "3.1.0-rc1", 3],
            "pack": ["web", []],
            "environments": [[""], "prod", [1]],
            "slo": [None, 1],
            "release": ["1.0.0", []],
            "exceptions": [{}, [1], [None]],
        }
        for key, values in cases.items():
            for v in values:
                with self.subTest(key=key, v=v):
                    got = self.errors(registry(product(**{key: v})))
                    self.assertEqual(len(got), 1, got)
                    self.assertTrue(got[0].startswith(f"products[0].{key}: "), got)

    def test_nested(self) -> None:
        good_pack = {"id": "web-api-ts", "version": "1.0.0"}
        good_rel = {"version": "1.0.0", "date": "2026-10-01", "digest": None}
        good_exc = {"id": "EX-1", "until": "2026-12-01", "why": "lý do"}
        cases = [
            ("pack", {**good_pack, "id": "../x"}, "pack.id"),
            ("pack", {**good_pack, "id": "Web"}, "pack.id"),
            ("pack", {**good_pack, "version": "1.0"}, "pack.version"),
            ("release", {**good_rel, "version": ""}, "release.version"),
            ("release", {**good_rel, "date": "2026-02-30"}, "release.date"),
            ("release", {**good_rel, "date": "20261001"}, "release.date"),
            ("release", {**good_rel, "digest": ""}, "release.digest"),
            ("exceptions", [{**good_exc, "id": "a b"}], "exceptions[0].id"),
            ("exceptions", [good_exc, {**good_exc, "until": "2026-12-01\n"}], "exceptions[1].until"),
            ("exceptions", [{**good_exc, "why": " "}], "exceptions[0].why"),
        ]
        for key, value, where in cases:
            with self.subTest(where=where, value=value):
                got = self.errors(registry(product(**{key: value})))
                self.assertEqual(len(got), 1, got)
                self.assertTrue(got[0].startswith(f"products[0].{where}: "), got)
        missing = {"id": "x"}
        self.assertEqual(
            self.errors(registry(product(pack={**missing, "k": 1}))),
            ["products[0].pack: thiếu khoá version", "products[0].pack: khoá lạ 'k'"],
        )

    def test_duplicate_repo(self) -> None:
        got = self.errors(registry(product(), product(repo="o/b"), product()))
        self.assertEqual(got, ["repo trùng 'o/a'"])

    def test_duplicate_repo_check_is_linear(self) -> None:
        """Kiểm repo trùng không so từng cặp (AUD-CODE-050: `repos.count` O(n²), 20 000 sản phẩm 6,1 s): đếm phép `==`."""
        calls = [0]

        class Counted(str):
            __hash__ = str.__hash__

            def __eq__(self, other: object) -> bool:
                calls[0] += 1
                return str.__eq__(self, other)

        n = 300
        data = registry(*(product(repo=Counted(f"o/r{i}")) for i in range(n)))
        self.assertEqual(self.errors(data), [])
        self.assertLessEqual(calls[0], 2 * n, "kiểm repo trùng so từng cặp")
        dup = registry(product(repo=Counted("o/a")), product(repo=Counted("o/a")))
        self.assertEqual(self.errors(dup), ["repo trùng 'o/a'"])

    def test_duplicate_exception_id_in_product(self) -> None:
        """Id ngoại lệ trùng trong một sản phẩm là lỗi (AUD-HAR-228: màn Registry đánh dấu hết hạn theo id); khác sản
        phẩm thì được."""
        exc = {"id": "EX-1", "until": "2026-01-01", "why": "a"}
        later = {**exc, "until": "2099-01-01"}
        got = self.errors(registry(product(exceptions=[exc, later, {**exc, "id": "EX-2"}])))
        self.assertEqual(got, ["products[0].exceptions: id trùng 'EX-1'"])
        ok = registry(product(exceptions=[exc]), product(repo="o/b", exceptions=[later]))
        self.assertEqual(self.errors(ok), [])
        bad_inner = registry(product(exceptions=[exc, {**later, "why": ""}]))
        self.assertEqual(self.errors(bad_inner), ["products[0].exceptions[1].why: phải là chuỗi không rỗng"])


class DriftTest(unittest.TestCase):
    def test_each_core_class(self) -> None:
        cores = {"o/cur": "3.29.2", "o/pat": "3.29.1", "o/min": "3.28.9", "o/maj": "2.99.99", "o/ahd": "3.30.0"}
        expect = {"o/cur": "current", "o/pat": "patch", "o/min": "minor", "o/maj": "major", "o/ahd": "ahead"}
        with Sandbox() as sb:
            got = sb.report(registry(*(product(repo=r, core=c) for r, c in cores.items()), product(repo="o/unk")))
        self.assertEqual(got["version"], "3.29.2")
        self.assertEqual({r["repo"]: r["core_drift"] for r in got["products"]}, {**expect, "o/unk": "unknown"})
        self.assertEqual((got["drift"], got["expired"]), (5, 0))

    def test_prerelease_and_unknown_version(self) -> None:
        self.assertEqual(xt._reg_drift("3.30.0", ("3.30.0-rc1", (3, 30, 0), True)), "ahead")
        self.assertEqual(xt._reg_drift("3.29.0", ("3.30.0-rc1", (3, 30, 0), True)), "minor")
        for version in (None, "không phải số"):
            with self.subTest(version=version), Sandbox(version=version) as sb:
                got = sb.report(registry(product(core="3.29.2")))
                self.assertIsNone(got["version"])
                self.assertEqual(got["products"][0]["core_drift"], "unknown")

    def test_version_not_utf8_is_unknown(self) -> None:
        with Sandbox() as sb:
            (sb.framework.parent / "VERSION").write_bytes(b"\xff\xfe3.29.2")
            got = sb.report(registry(product(core="3.29.2")))
        self.assertEqual((got["version"], got["products"][0]["core_drift"]), (None, "unknown"))

    def test_version_label_with_suffix(self) -> None:
        with Sandbox(version="3.29.2 (abc1234)") as sb:
            got = sb.report(registry(product(core="3.29.2")))
        self.assertEqual((got["version"], got["products"][0]["core_drift"], got["drift"]), ("3.29.2", "current", 0))

    def test_pack_without_packs_dir_is_unknown(self) -> None:
        p = product(core="3.29.2", pack={"id": "web-api-ts", "version": "3.29.2"})
        with Sandbox() as sb:
            got = sb.report(registry(p, product(repo="o/b", core="3.29.2")))
        rows = got["products"]
        self.assertEqual((rows[0]["pack_drift"], rows[1]["pack_drift"]), ("unknown", None))
        self.assertEqual(rows[0]["pack"], {"id": "web-api-ts", "version": "3.29.2"})
        self.assertEqual(got["drift"], 1)  # gói chưa kiểm được là lệch; không gói thì không

    def test_pack_with_packs_dir(self) -> None:
        cur = product(repo="o/a", core="3.29.2", pack={"id": "web-api-ts", "version": "3.29.2"})
        old = product(repo="o/b", core="3.29.2", pack={"id": "web-api-ts", "version": "3.27.0"})
        with Sandbox(packs=["web-api-ts"]) as sb:
            got = sb.report(registry(cur, old))
        self.assertEqual([r["pack_drift"] for r in got["products"]], ["current", "minor"])
        self.assertEqual(got["drift"], 1)

    def test_unknown_pack_id_is_error_when_packs_dir_exists(self) -> None:
        p = product(pack={"id": "khong-co", "version": "3.29.2"})
        with Sandbox(packs=["web-api-ts"]) as sb:
            sb.write(registry(p))
            rc, out, err = sb.run()
        self.assertEqual((rc, out), (2, ""))
        self.assertIn("✗ products[0].pack.id: không có gói 'khong-co' (cần templates/packs/khong-co/pack.json)", err)
        self.assertNotIn(str(sb.base), err)  # không lộ đường tuyệt đối (API `xt.py app` dùng cùng thông điệp)

    def test_expired_exceptions(self) -> None:
        exc = [
            {"id": "EX-old", "until": "2026-11-04", "why": "quá hạn"},
            {"id": "EX-today", "until": TODAY, "why": "hết hôm nay, chưa quá"},
            {"id": "EX-new", "until": "2027-01-01", "why": "còn hạn"},
        ]
        with Sandbox() as sb:
            got = sb.report(registry(product(core="3.29.2", exceptions=exc)))
        self.assertEqual(got["products"][0]["expired"], ["EX-old"])
        self.assertEqual((got["drift"], got["expired"]), (0, 1))


class CliTest(unittest.TestCase):
    def test_json_shape(self) -> None:
        p = product(core="3.29.2", pack={"id": "web-api-ts", "version": "3.29.2"}, owner="x", slo="s")
        with Sandbox() as sb:
            got = sb.report(registry(p))
        self.assertEqual(
            got,
            {
                "schema": 1,
                "version": "3.29.2",
                "products": [
                    {
                        "repo": "o/a",
                        "core": "3.29.2",
                        "core_drift": "current",
                        "pack": {"id": "web-api-ts", "version": "3.29.2"},
                        "pack_drift": "unknown",
                        "expired": [],
                    }
                ],
                "drift": 1,
                "expired": 0,
            },
        )

    def test_text_table(self) -> None:
        exc = [{"id": "EX-1", "until": "2020-01-01", "why": "x"}, {"id": "EX-2", "until": "2020-01-02", "why": "y"}]
        a = product(core="3.28.0", pack={"id": "web-api-ts", "version": "3.29.2"}, exceptions=exc)
        with Sandbox() as sb:
            sb.write(registry(a, product(repo="o/b")))
            rc, out, err = sb.run("--today", TODAY)
        self.assertEqual((rc, err), (0, ""))
        lines = out.splitlines()
        self.assertEqual(lines[0], "registry docs/ops/registry.json — khung 3.29.2")
        self.assertIn("ngoại lệ hết hạn", lines[1])
        self.assertRegex(lines[2], r"^  o/a +3\.28\.0 +minor +web-api-ts@3\.29\.2 +unknown +EX-1, EX-2$")
        self.assertRegex(lines[3], r"^  o/b +— +unknown +— +— +—$")
        self.assertEqual(lines[4], "2 sản phẩm · lệch 2 · ngoại lệ hết hạn 2")

    def test_text_empty_and_no_version(self) -> None:
        with Sandbox(version=None) as sb:
            sb.write(registry())
            rc, out, _ = sb.run("--strict")
        self.assertEqual(rc, 0)
        self.assertEqual(out.splitlines()[0], "registry docs/ops/registry.json — khung không rõ VERSION")
        self.assertEqual(out.splitlines()[-1], "0 sản phẩm · lệch 0 · ngoại lệ hết hạn 0")

    def test_strict_exit_codes(self) -> None:
        clean = product(core="3.29.2", exceptions=[{"id": "EX-1", "until": "2099-01-01", "why": "còn hạn"}])
        drift = product(repo="o/b", core="3.29.1")
        expired = product(repo="o/c", core="3.29.2", exceptions=[{"id": "EX-9", "until": "2026-01-01", "why": "x"}])
        cases = [((clean,), 0, 0), ((clean, drift), 0, 1), ((clean, expired), 0, 1)]
        for prods, plain, strict in cases:
            with self.subTest(repos=[p["repo"] for p in prods]), Sandbox() as sb:
                sb.write(registry(*prods))
                self.assertEqual(sb.run("--today", TODAY)[0], plain)
                self.assertEqual(sb.run("--today", TODAY, "--strict")[0], strict)
                self.assertEqual(sb.run("--today", TODAY, "--strict", "--json")[0], strict)

    def test_default_today(self) -> None:
        exc = [{"id": "EX-1", "until": "2000-01-01", "why": "x"}, {"id": "EX-2", "until": "2999-01-01", "why": "y"}]
        with Sandbox() as sb:
            sb.write(registry(product(core="3.29.2", exceptions=exc)))
            rc, out, _ = sb.run("--json")
        self.assertEqual((rc, json.loads(out)["products"][0]["expired"]), (0, ["EX-1"]))

    def test_bad_today(self) -> None:
        with Sandbox() as sb:
            sb.write(registry())
            for bad in ("2026-02-30", "20261105", "hôm nay"):
                with self.subTest(bad=bad):
                    rc, out, err = sb.run("--today", bad)
                    self.assertEqual((rc, out), (2, ""))
                    self.assertIn("✗ --today phải là YYYY-MM-DD", err)

    def test_unreadable_inputs_exit_2(self) -> None:
        with Sandbox() as sb:
            rc, out, err = sb.run()
            self.assertEqual((rc, out), (2, ""))
            self.assertIn("✗ không đọc được registry", err)
            for text, why in (("{", "JSON hỏng"), ("[" * 200000, "JSON hỏng"), ('{"schema": 2}', '"schema": 1')):
                with self.subTest(why=why, n=len(text)):
                    sb.write(text)
                    rc, out, err = sb.run()
                    self.assertEqual((rc, out), (2, ""))
                    self.assertIn(why, err)
            sb.file.write_bytes(b'{"schema": 1, "products": ["\xff"]}')
            rc, _, err = sb.run()
            self.assertEqual(rc, 2)
            self.assertIn("✗ không đọc được registry", err)

    def test_schema_errors_listed(self) -> None:
        with Sandbox() as sb:
            sb.write(registry(product(core="3.1"), product(repo="bad")))
            rc, out, err = sb.run("--json")
        self.assertEqual((rc, out), (2, ""))
        self.assertEqual(
            err.splitlines(),
            ["✗ products[0].core: phải là X.Y.Z hoặc null", "✗ products[1].repo: phải là owner/name"],
        )

    def test_file_flag_relative_to_project(self) -> None:
        with Sandbox() as sb:
            (sb.base / "khác.json").write_text(json.dumps(registry(product(core="3.29.2"))), encoding="utf-8")
            rc, out, _ = sb.run("--file", "khác.json", "--strict")
        self.assertEqual(rc, 0)
        self.assertTrue(out.startswith("registry khác.json — khung 3.29.2"))


def target_repos(text: str) -> List[str]:
    """Repo ở mục `## Danh sách` của TARGETS.md (dòng `- owner/repo — …`); mục khác (`Đã xét, không đưa vào`) bỏ qua."""
    section = text.split("\n## Danh sách\n", 1)[-1].split("\n## ", 1)[0] if "\n## Danh sách\n" in text else ""
    return [ln[2:].split(" — ", 1)[0] for ln in section.splitlines() if ln.startswith("- ")]


class TargetReposTest(unittest.TestCase):
    def test_only_list_section(self) -> None:
        text = "# T\n\n## Danh sách\n\n- o/a — có\n- o/b — có\nchữ\n\n## Đã xét, không đưa vào\n\n- o/c — không\n"
        self.assertEqual(target_repos(text), ["o/a", "o/b"])
        self.assertEqual(target_repos("# T\n- o/a — x\n"), [])


class RealRegistryTest(unittest.TestCase):
    """`docs/ops/registry.json` của repo khung hợp lệ và chỉ chứa dữ kiện đọc được (không bịa digest/SLO)."""

    def test_real_file_validates(self) -> None:
        data, errors = xt.registry_load(ROOT / "docs" / "ops" / "registry.json", ROOT / "framework")
        self.assertEqual(errors, [])
        assert data is not None
        repos = [p["repo"] for p in data["products"]]
        self.assertIn("seeker19110/hotel-manager", repos)
        targets = (ROOT / "docs" / "ops" / "TARGETS.md").read_text(encoding="utf-8")
        # hai chiều (AUD-TEST-064): repo thêm vào TARGETS.md mà quên registry cũng đỏ
        self.assertEqual(sorted(target_repos(targets)), sorted(repos))
        for p in data["products"]:
            with self.subTest(repo=p["repo"]):
                self.assertIn(f"- {p['repo']} — có `.xtemplates/` ({p['core']})", targets)
                self.assertEqual((p["slo"], p["release"]), ("", None))

    def test_real_file_cli(self) -> None:
        env = {**os.environ, "CLAUDE_PROJECT_DIR": str(ROOT)}
        r = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "xt.py"), "registry", "--json"],
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        got = json.loads(r.stdout)
        self.assertEqual(got["version"], (ROOT / "VERSION").read_text(encoding="utf-8").strip())
        # số lệch tính độc lập từ registry.json + VERSION: core hoặc gói khác VERSION khung (dữ kiện thật đổi theo dự án
        # đích — không giả định "mọi dự án đều cũ"; review #461)
        data = json.loads((ROOT / "docs" / "ops" / "registry.json").read_text(encoding="utf-8"))
        want = sum(
            p["core"] != got["version"] or (p["pack"] is not None and p["pack"]["version"] != got["version"])
            for p in data["products"]
        )
        self.assertEqual(want, got["drift"])


def call(base: Path, framework: Path) -> Dict[str, Any]:
    ctx = server.Ctx(xt, base=base, framework=framework, query={}, body=None)
    code, body = api_registry.ROUTES[("GET", "/api/registry")](ctx)
    assert code == 200
    return body


def snapshot(root: Path) -> Dict[str, Tuple[int, int]]:
    return {str(p): (p.stat().st_mtime_ns, p.stat().st_size) for p in sorted(root.rglob("*"))}


class AppTest(unittest.TestCase):
    def test_missing_file(self) -> None:
        with Sandbox() as sb:
            got = call(sb.base, sb.framework)
        self.assertEqual(
            got,
            {
                "available": False,
                "path": "docs/ops/registry.json",
                "reason": "chưa có docs/ops/registry.json",
                "errors": [],
            },
        )

    def test_invalid_file_hides_absolute_path(self) -> None:
        with Sandbox() as sb:
            sb.write("{")
            got = call(sb.base, sb.framework)
            self.assertIs(got["available"], False)
            self.assertEqual(got["reason"], "docs/ops/registry.json không hợp lệ")
            self.assertTrue(got["errors"][0].startswith("docs/ops/registry.json: JSON hỏng"), got)
            self.assertNotIn(str(sb.base), json.dumps(got, ensure_ascii=False))
            sb.write(registry(*(product(repo=f"o/{i}", core="x") for i in range(80))))
            got = call(sb.base, sb.framework)
        self.assertEqual(len(got["errors"]), api_registry.MAX_ERRORS)

    def test_valid_rows_carry_details(self) -> None:
        exc = [{"id": "EX-1", "until": "2000-01-01", "why": "<script>alert(1)</script>"}]
        rel = {"version": "1.0.0", "date": "2026-10-01", "digest": None}
        p = product(core="3.29.2", owner="chủ", type="web-api", risk="high", release=rel, exceptions=exc)
        with Sandbox() as sb:
            sb.write(registry(p))
            got = call(sb.base, sb.framework)
        self.assertEqual((got["available"], got["path"], got["version"]), (True, "docs/ops/registry.json", "3.29.2"))
        row = got["products"][0]
        self.assertEqual(
            (row["core_drift"], row["expired"], row["owner"], row["risk"]), ("current", ["EX-1"], "chủ", "high")
        )
        self.assertEqual((row["release"], row["exceptions"]), (rel, exc))  # dữ liệu thô; màn hiện bằng textContent
        self.assertEqual((got["drift"], got["expired"]), (0, 1))

    def test_concurrent_reads_same_result_no_write(self) -> None:
        with Sandbox() as sb:
            sb.write(registry(product(core="3.28.0"), product(repo="o/b", core="3.29.2")))
            before = snapshot(sb.base)
            results: List[Dict[str, Any]] = []
            lock = threading.Lock()

            def worker() -> None:
                body = call(sb.base, sb.framework)
                with lock:
                    results.append(body)

            threads = [threading.Thread(target=worker) for _ in range(16)]
            for t in threads:
                t.start()
            for t in threads:
                t.join(10)
            self.assertEqual(snapshot(sb.base), before)
        self.assertEqual(len(results), 16)
        self.assertTrue(all(r == results[0] for r in results))
        self.assertEqual(results[0]["drift"], 1)

    def test_route_loaded_and_http_token(self) -> None:
        self.assertIn(("GET", "/api/registry"), server.load_routes())
        with Sandbox() as sb:
            sb.write(registry(product(core="3.29.2")))
            srv, token = server.make_server(xt, sb.base, sb.framework, sb.base / "static", routes=api_registry.ROUTES)
            srv.quiet = True
            th = threading.Thread(target=srv.serve_forever, daemon=True)
            th.start()
            got: Dict[str, Tuple[int, Any]] = {}
            try:
                for name, method, tok in (("ok", "GET", token), ("no-token", "GET", "sai"), ("post", "POST", token)):
                    conn = http.client.HTTPConnection("127.0.0.1", srv.server_address[1], timeout=30)
                    conn.putrequest(method, "/api/registry", skip_host=True)
                    conn.putheader("Host", f"127.0.0.1:{srv.server_address[1]}")
                    conn.putheader("X-XT-Token", tok)
                    conn.putheader("Content-Length", "0")
                    conn.endheaders()
                    resp = conn.getresponse()
                    got[name] = (resp.status, json.loads(resp.read()))
                    conn.close()
            finally:
                srv.shutdown()
                srv.server_close()
                th.join(5)
        self.assertEqual(got["ok"][0], 200)
        self.assertIs(got["ok"][1]["available"], True)
        self.assertEqual(got["no-token"], (401, {"error": "thiếu hoặc sai token"}))
        self.assertEqual(got["post"][0], 405)  # chỉ đọc: không có route ghi

    def test_module_is_read_only(self) -> None:
        src = (ROOT / "scripts" / "xt_app" / "api_registry.py").read_text(encoding="utf-8")
        for bad in ("write_text", "write_bytes", "open(", "subprocess", "os.", "unlink", "cmd_"):
            self.assertNotIn(bad, src)
        self.assertNotRegex(src, r"^\s*import xt\b|^\s*from xt import", "dùng ctx.xt")


class SmallHelpersTest(unittest.TestCase):
    def test_reg_date(self) -> None:
        self.assertEqual(xt._reg_date("2026-11-05"), _dt.date(2026, 11, 5))
        for bad in ("2026-11-5", "20261105", 20261105, None, "2026-13-01"):
            self.assertIsNone(xt._reg_date(bad))

    def test_registry_errors_do_not_mutate(self) -> None:
        data = registry(product(core="3.29.2"))
        before = copy.deepcopy(data)
        xt.registry_errors(data)
        self.assertEqual(data, before)


if __name__ == "__main__":
    unittest.main()
