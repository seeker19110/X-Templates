"""Gói sản phẩm (ADR-0068 lát B, PLAN-factory-BE T-3685/T-3686/T-3690): cấu trúc gói đúng hợp đồng `packs/README.md`,
lock khớp `package.json`, mọi phiên bản ghim chính xác, ca sai cố ý áp được đúng một chỗ, và công cụ `tests/pack_mutants.py`.
Chạy bộ nghiệm thu thật (Node + Postgres) là việc của CI `pack-web-api.yml` — ở đây chỉ kiểm phần không cần stack."""

from __future__ import annotations

import io
import json
import re
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pack_mutants
import xt

PACKS = ROOT / "framework" / "templates" / "packs"
PACK = PACKS / "web-api-ts"
EXACT = re.compile(r"^\d+\.\d+\.\d+$")


def packs() -> list[Path]:
    return sorted(p for p in PACKS.iterdir() if (p / "pack.json").is_file())


class PackContractTest(unittest.TestCase):
    def test_every_pack_matches_contract(self):
        self.assertTrue(packs(), "không có gói nào")
        for pack in packs():
            with self.subTest(pack.name):
                meta = json.loads((pack / "pack.json").read_text(encoding="utf-8"))
                self.assertEqual(meta["schema"], 1)
                self.assertEqual(meta["id"], pack.name)
                self.assertRegex(meta["support_until"], r"^\d{4}-\d{2}-\d{2}$")
                self.assertTrue(meta["owner"])
                self.assertTrue(all(isinstance(v, str) for v in meta["xt_yaml"].values()))
                self.assertTrue((pack / "starter").is_dir())
                self.assertTrue((pack / "README.md").is_file())
                self.assertIn(f"`{pack.name}`", (PACKS / "README.md").read_text(encoding="utf-8"))

    def test_controls_are_known_ids(self):
        corpus = "\n".join(p.read_text(encoding="utf-8") for p in (ROOT / "framework").rglob("*.md"))
        for cid in json.loads((PACK / "pack.json").read_text(encoding="utf-8"))["controls"]:
            with self.subTest(cid):
                self.assertIn(cid, corpus)

    def test_versions_pinned_exactly_and_lock_matches(self):
        pkg = json.loads((PACK / "starter" / "package.json").read_text(encoding="utf-8"))
        lock = (PACK / "starter" / "pnpm-lock.yaml").read_text(encoding="utf-8")
        for group in ("dependencies", "devDependencies"):
            for name, version in pkg[group].items():
                with self.subTest(name):
                    self.assertRegex(version, EXACT, "ghim đúng phiên bản, không ^/~")
                    self.assertIn(
                        f"specifier: {version}",
                        lock.split(f"'{name}':" if name.startswith("@") else f"{name}:", 1)[1][:200],
                    )
        self.assertTrue(pkg["packageManager"].startswith("pnpm@"))

    def test_xt_yaml_commands_exist_in_package_scripts(self):
        pkg = json.loads((PACK / "starter" / "package.json").read_text(encoding="utf-8"))
        meta = json.loads((PACK / "pack.json").read_text(encoding="utf-8"))
        for key, cmd in meta["xt_yaml"].items():
            m = re.match(r"pnpm (\w+)", cmd)
            if m and m[1] not in ("install", "exec"):
                with self.subTest(key):
                    self.assertIn(m[1], pkg["scripts"])

    def test_tests_do_not_skip(self):
        for test in (PACK / "starter" / "test").glob("*.ts"):
            with self.subTest(test.name):
                self.assertNotRegex(test.read_text(encoding="utf-8"), r"\.(skip|only|todo)\(|skipIf|runIf")

    def test_every_migration_registered_and_reversible(self):
        mig = PACK / "starter" / "src" / "migrations"
        registry = (PACK / "starter" / "src" / "migrate.ts").read_text(encoding="utf-8")
        for f in sorted(mig.glob("*.ts")):
            with self.subTest(f.name):
                self.assertIn(f'"{f.stem}"', registry)
                text = f.read_text(encoding="utf-8")
                self.assertIn("export async function down", text)


class ReadmeIndexTest(unittest.TestCase):
    def test_pack_payload_trees_need_no_readme_but_others_do(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            for rel in ("templates/packs/p/starter/src", "templates/packs/p/managed/.github", "templates/other"):
                (root / rel).mkdir(parents=True)
            (root / "templates" / "README.md").write_text("x", encoding="utf-8")
            (root / "templates" / "packs" / "README.md").write_text("x", encoding="utf-8")
            self.assertEqual(
                xt._check_readmes(root),
                [
                    "templates/other/: thiếu README.md (chỉ mục thư mục)",
                    "templates/packs/p/: thiếu README.md (chỉ mục thư mục)",
                ],
            )


class MutantsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        shutil.copytree(PACK / "starter", self.tmp / "app")

    def run_main(self, *argv: str) -> tuple[int, str]:
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = pack_mutants.main(list(argv))
        return code, out.getvalue() + err.getvalue()

    def test_every_mutant_applies_exactly_once_and_changes_file(self):
        for mid, m in pack_mutants.load(PACK).items():
            with self.subTest(mid):
                app = self.tmp / mid
                shutil.copytree(PACK / "starter", app)
                before = (app / m["file"]).read_text(encoding="utf-8")
                self.assertEqual(self.run_main("apply", str(PACK), mid, str(app))[0], 0)
                self.assertNotEqual((app / m["file"]).read_text(encoding="utf-8"), before)
                self.assertTrue(m["expect_fail"] and m["why"])

    def test_apply_twice_fails(self):
        app = str(self.tmp / "app")
        self.assertEqual(self.run_main("apply", str(PACK), "tenant-leak", app)[0], 0)
        code, out = self.run_main("apply", str(PACK), "tenant-leak", app)
        self.assertEqual(code, 1)
        self.assertIn("0 lần", out)

    def junit(self, *cases: tuple[str, bool]) -> Path:
        body = "".join(
            f'<testcase classname="test/x.test.ts" name="{n}">{"<failure/>" if bad else ""}</testcase>'
            for n, bad in cases
        )
        path = self.tmp / "junit.xml"
        path.write_text(f"<testsuites><testsuite>{body}</testsuite></testsuites>", encoding="utf-8")
        return path

    def test_check_caught_survived_and_wrong_test(self):
        want = pack_mutants.load(PACK)["broken-down"]["expect_fail"]
        caught = self.junit((f"migration > {want}", True), ("khác", False))
        self.assertEqual(self.run_main("check", str(PACK), "broken-down", str(caught))[0], 0)
        survived = self.junit((want, False))
        code, out = self.run_main("check", str(PACK), "broken-down", str(survived))
        self.assertEqual((code, "SỐNG SÓT" in out), (1, True))
        wrong = self.junit(("test khác", True))
        code, out = self.run_main("check", str(PACK), "broken-down", str(wrong))
        self.assertEqual((code, "không ở test mong đợi" in out), (1, True))
        errored = self.tmp / "e.xml"
        errored.write_text(f'<testsuite><testcase name="{want}"><error/></testcase></testsuite>', encoding="utf-8")
        self.assertEqual(self.run_main("check", str(PACK), "broken-down", str(errored))[0], 0)

    def test_list_and_bad_args(self):
        code, out = self.run_main("list", str(PACK))
        self.assertEqual(code, 0)
        self.assertEqual(out.split(), list(pack_mutants.load(PACK)))
        self.assertEqual(self.run_main("apply", str(PACK))[0], 2)
        self.assertEqual(self.run_main("zap", "a", "b", "c")[0], 2)
        self.assertEqual(self.run_main("apply", str(PACK), "khong-co", str(self.tmp))[0], 2)

    def report(self, rows: list[dict[str, str]], digest: object, state: str) -> str:
        path = self.tmp / "release.json"
        path.write_text(
            json.dumps({"rows": rows, "subject": {"digest": digest}, "promotion": {"state": state}}), "utf-8"
        )
        return str(path)

    def test_promotion_report(self):
        ok_rows = [{"id": "artifacts", "result": "PASS"}]
        self.assertEqual(self.run_main("promotion", self.report(ok_rows, "ab", "pending_human"))[0], 0)
        self.assertEqual(self.run_main("promotion", self.report(ok_rows, "ab", "blocked"))[0], 0)
        cases = [
            (ok_rows, "ab", "approved", "khi chưa có chữ ký"),
            ([{"id": "artifacts", "result": "FAIL"}], "ab", "blocked", "cần PASS"),
            ([], "ab", "blocked", "None"),
            (ok_rows, None, "pending_human", "digest trống"),
        ]
        for rows, digest, state, msg in cases:
            with self.subTest(msg):
                code, out = self.run_main("promotion", self.report(rows, digest, state))
                self.assertEqual(code, 1)
                self.assertIn(msg, out)


if __name__ == "__main__":
    unittest.main()
