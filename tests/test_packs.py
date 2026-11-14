"""Gói sản phẩm (ADR-0068 lát B, PLAN-factory-BE T-3685/T-3686/T-3690): cấu trúc gói đúng hợp đồng `packs/README.md`,
lock khớp `package.json`, mọi phiên bản ghim chính xác, ca sai cố ý áp được đúng một chỗ, và công cụ `tests/pack_mutants.py`.
Chạy bộ nghiệm thu thật (Node + Postgres) là việc của CI `pack-web-api.yml` — ở đây chỉ kiểm phần không cần stack."""

from __future__ import annotations

import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pack_baseline
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

    def test_migrations_bound_locks_and_rerun_is_noop(self):
        """Audit DATA (D-377): DDL không chờ khoá vô hạn — mỗi `up`/`down` mở bằng `SET LOCAL lock_timeout` +
        `statement_timeout` (DB-MIG-005; FK tới bảng đang phục vụ khoá bảng được trỏ); `up` lần hai là no-op
        (DB-MIG-004) có test."""
        lock = re.compile(r"sql`\s*SET LOCAL lock_timeout = '\d+s';\s*SET LOCAL statement_timeout = '\d+s';")
        for f in sorted((PACK / "starter" / "src" / "migrations").glob("*.ts")):
            with self.subTest(f.name):
                text = f.read_text(encoding="utf-8")
                self.assertEqual(len(lock.findall(text)), text.count("sql`"), "mọi khối SQL mở bằng giới hạn khoá")
        slice_test = (PACK / "starter" / "test" / "slice.test.ts").read_text(encoding="utf-8")
        self.assertIn('expect(await migrate(raw, "up")).toEqual([]);', slice_test)


INDEX_RE = re.compile(
    r"CREATE\s+(?:UNIQUE\s+)?INDEX\s+(?P<conc>CONCURRENTLY\s+)?(?:(?:IF\s+NOT\s+EXISTS\s+)?[\w.\"]+\s+)?ON\s+(?:ONLY\s+)?(?P<table>[\w.\"]+)",
    re.IGNORECASE,
)
TABLE_RE = re.compile(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?P<table>[\w.\"]+)", re.IGNORECASE)
# Migration đã phát hành (DB-MIG-003: không sửa tại chỗ) có `CREATE INDEX` thường trên bảng có sẵn — kèm dòng sổ AUDIT-STATUS.
LEGACY_PLAIN_INDEX = {"0005_sessions_expiry": "AUD-DATA-011"}


def plain_indexes_on_existing_tables(sql: str) -> list[str]:
    """Tên bảng có sẵn (không tạo cùng file) bị `CREATE INDEX` không CONCURRENTLY — khoá SHARE chặn ghi (DB-MIG-006)."""
    created = {m["table"] for m in TABLE_RE.finditer(sql)}
    return [m["table"] for m in INDEX_RE.finditer(sql) if not m["conc"] and m["table"] not in created]


class MigrationIndexTest(unittest.TestCase):
    """AUD-DATA-011/013 (DB-MIG-006): giữ đúng khả năng của migration chạy trong giao dịch."""

    def test_scanner(self):
        self.assertEqual(plain_indexes_on_existing_tables("CREATE INDEX i ON sessions (a);"), ["sessions"])
        self.assertEqual(plain_indexes_on_existing_tables("CREATE INDEX ON sessions (a);"), ["sessions"])
        self.assertEqual(
            plain_indexes_on_existing_tables("CREATE UNIQUE INDEX ON ONLY public.sessions (a);"), ["public.sessions"]
        )
        self.assertEqual(plain_indexes_on_existing_tables("CREATE INDEX CONCURRENTLY ON sessions (a);"), [])
        self.assertEqual(
            plain_indexes_on_existing_tables("create unique index if not exists i on public.t (a)"), ["public.t"]
        )
        self.assertEqual(plain_indexes_on_existing_tables("CREATE INDEX CONCURRENTLY i ON sessions (a);"), [])
        self.assertEqual(plain_indexes_on_existing_tables("CREATE TABLE n (a int); CREATE INDEX i ON n (a);"), [])
        self.assertEqual(
            plain_indexes_on_existing_tables("CREATE TABLE n (a int); CREATE INDEX i ON other (a);"), ["other"]
        )

    def test_transactional_migration_index_policy(self):
        cases = (
            ("CREATE INDEX CONCURRENTLY ON sessions (created_at);", "CONCURRENTLY"),
            ("CREATE TABLE n (a int); CREATE UNIQUE INDEX CONCURRENTLY i ON n (a);", "CONCURRENTLY"),
            ("CREATE INDEX IF NOT EXISTS sessions_created ON sessions (created_at);", "0006_index"),
            ("CREATE INDEX ON sessions (created_at);", "0006_index"),
            ("CREATE TABLE n (a int); CREATE INDEX IF NOT EXISTS i ON n (a);", ""),
            ("", ""),
        )
        with tempfile.TemporaryDirectory() as scratch:
            pack = Path(scratch)
            migrations = pack / "starter" / "src" / "migrations"
            migrations.mkdir(parents=True)
            for legacy in LEGACY_PLAIN_INDEX:
                shutil.copyfile(PACK / "starter" / "src" / "migrations" / f"{legacy}.ts", migrations / f"{legacy}.ts")
            for sql, expected_error in cases:
                with self.subTest(sql=sql), patch(f"{__name__}.PACK", pack):
                    (migrations / "0006_index.ts").write_text(sql, encoding="utf-8")
                    if expected_error:
                        with self.assertRaisesRegex(AssertionError, expected_error):
                            self.test_transactional_migrations_reject_unsupported_indexes()
                    else:
                        self.test_transactional_migrations_reject_unsupported_indexes()

    def test_transactional_migrations_reject_unsupported_indexes(self):
        bad: dict[str, list[str]] = {}
        concurrent: list[str] = []
        for f in sorted((PACK / "starter" / "src" / "migrations").glob("*.ts")):
            sql = f.read_text(encoding="utf-8")
            if any(m["conc"] for m in INDEX_RE.finditer(sql)):
                concurrent.append(f.stem)
            if found := plain_indexes_on_existing_tables(sql):
                bad[f.stem] = found
        self.assertEqual(concurrent, [], "CREATE INDEX CONCURRENTLY cần chạy ngoài giao dịch (DB-MIG-006)")
        self.assertEqual(set(bad), set(LEGACY_PLAIN_INDEX), "chỉ 0005 được dựng index thường trên bảng cũ (DB-MIG-006)")
        ledger = (ROOT / "docs" / "ops" / "AUDIT-STATUS.md").read_text(encoding="utf-8")
        for aud in LEGACY_PLAIN_INDEX.values():
            self.assertIn(f"| {aud} |", ledger, "mục ngoại lệ phải có dòng sổ")


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

    def test_ci_matrix_runs_every_mutant(self):
        """Ca thêm vào `mutants.json` mà quên ma trận CI thì không bao giờ chạy (AUD-SEC-502): ma trận = clean + mọi ca."""
        wf = (ROOT / ".github" / "workflows" / "pack-web-api.yml").read_text(encoding="utf-8")
        rows = [ln.split(":", 1)[1].strip() for ln in wf.splitlines() if ln.strip().startswith("case: [")]
        self.assertEqual(len(rows), 1, rows)
        cases = [c.strip() for c in rows[0].strip("[]").split(",")]
        self.assertEqual(cases, ["clean", *pack_mutants.load(PACK)])

    def test_every_expect_fail_names_an_existing_test(self):
        """AUD-TEST-086: `expect_fail` đổi tên/gõ sai thì `check` báo "không ở test mong đợi" chỉ khi CI chạy — kiểm sớm
        rằng chuỗi có trong một tên test của `starter/test/*.ts`."""
        corpus = "\n".join(p.read_text(encoding="utf-8") for p in (PACK / "starter" / "test").glob("*.ts"))
        names = re.findall(r"\b(?:it|test|describe)\(\s*\"([^\"]+)\"", corpus)
        self.assertTrue(names, "không đọc được tên test nào")
        for mid, m in pack_mutants.load(PACK).items():
            with self.subTest(mid):
                self.assertTrue(any(m["expect_fail"] in n for n in names), m["expect_fail"])

    def test_workflow_triggers_on_pack_changes(self):
        """AUD-TEST-086: bỏ `framework/templates/packs/**` khỏi `paths` thì đổi gói không chạy bộ nghiệm thu."""
        wf = (ROOT / ".github" / "workflows" / "pack-web-api.yml").read_text(encoding="utf-8")
        for event in ("pull_request:", "push:"):
            with self.subTest(event):
                block = wf.split(f"\n  {event}\n", 1)[1].split("\n  workflow_dispatch:", 1)[0]
                block = block.split("\n  push:\n", 1)[0]
                paths = block.split("    paths:\n", 1)[1]
                self.assertIn("      - framework/templates/packs/**\n", paths)

    def test_workflows_use_job_context_only_in_step_env(self):
        """Review #453: `${{ job.* }}` ở `jobs.<id>.env` làm CẢ workflow không hợp lệ (GitHub: ngữ cảnh `job` chỉ có ở
        `steps[*].env`) — run thất bại 0 s, `jobs: []`, mọi cổng trong đó chưa từng chạy. Dòng dùng `job.` phải thụt ≥ 10
        (khối `env:` của một step)."""
        files = [
            ROOT / ".github" / "workflows" / "pack-web-api.yml",
            PACK / "managed" / ".github" / "workflows" / "pack-acceptance.yml",
        ]
        for wf in files:
            with self.subTest(wf.name):
                lines = wf.read_text(encoding="utf-8").splitlines()
                uses = [ln for ln in lines if "${{ job." in ln]
                self.assertTrue(uses, "workflow phải truyền PG_TOOLS_CONTAINER cho test sao lưu/khôi phục")
                for ln in uses:
                    self.assertGreaterEqual(len(ln) - len(ln.lstrip()), 10, ln)

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


class ContractBaselineTest(unittest.TestCase):
    """AUD-SEC-502 (D-377): `baseline.json` của contract chỉ được đổi so với nhánh gốc khi PR tăng phiên bản gói (=
    `VERSION` của khung, ADR-0068) — đổi không tương thích kèm chép đè baseline trong cùng PR thì CI đỏ."""

    BASE = {"paths": {"/a": {"get": {}}}}

    def setUp(self):
        self.repo = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.repo)
        self.git("init", "-q", "-b", "main")
        self.pack = self.repo / "packs" / "p"
        self.write(version="0.1.0", baseline=self.BASE)
        self.git("add", "-A")
        self.git("commit", "-qm", "gốc")

    def git(self, *args: str) -> str:
        env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@x", "GIT_COMMITTER_NAME": "t"}
        env["GIT_COMMITTER_EMAIL"] = "t@x"
        cmd = ["git", "-C", str(self.repo), "-c", "commit.gpgsign=false", *args]
        return subprocess.run(cmd, check=True, capture_output=True, text=True, env=env).stdout

    def write(self, version: object = None, baseline: object = None) -> None:
        contract = self.pack / "starter" / "contract"
        contract.mkdir(parents=True, exist_ok=True)
        (self.repo / "VERSION").unlink(missing_ok=True)
        if version is not None:
            (self.repo / "VERSION").write_text(f"{version}\n", encoding="utf-8")
        if baseline is not None:
            (contract / "baseline.json").write_text(json.dumps(baseline, indent=1), encoding="utf-8")
            (contract / "openapi.json").write_text(json.dumps(baseline), encoding="utf-8")  # mốc chép từ contract

    def run_main(self, *argv: str) -> tuple[int, str]:
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = pack_baseline.main(list(argv))
        return code, out.getvalue() + err.getvalue()

    def check(self) -> tuple[int, str]:
        return self.run_main("check", str(self.pack), "main")

    def test_unchanged_or_reformatted_baseline_passes(self):
        self.assertEqual(self.check()[0], 0)
        (self.pack / "starter" / "contract" / "baseline.json").write_text(json.dumps(self.BASE), encoding="utf-8")
        self.assertEqual(self.check()[0], 0)  # chỉ đổi định dạng: cùng nội dung JSON

    def test_baseline_change_without_version_bump_fails(self):
        changed = {"paths": {}}
        for version in ("0.1.0", "0.0.9", None, "1.0", "v2.0.0", 2):
            with self.subTest(version=version):
                self.write(version=version, baseline=changed)
                code, out = self.check()
                self.assertEqual(code, 1, out)
                self.assertIn("AUD-SEC-502", out)

    def test_baseline_change_with_version_bump_passes(self):
        for version in ("0.1.1", "0.2.0", "1.0.0", "0.1.10"):
            with self.subTest(version=version):
                self.write(version=version, baseline={"paths": {}})
                self.assertEqual(self.check()[0], 0)

    def test_version_bump_with_baseline_not_from_contract_fails(self):
        """Lách AUD-SEC-502 (review #451): tăng VERSION kèm baseline tuỳ ý (`{"paths": {}}`) làm phép so rỗng mãi mãi."""
        self.write(version="0.1.1", baseline={"paths": {}})
        (self.pack / "starter" / "contract" / "openapi.json").write_text(json.dumps(self.BASE), encoding="utf-8")
        code, out = self.check()
        self.assertEqual(code, 1, out)
        self.assertIn("không trùng", out)
        (self.pack / "starter" / "contract" / "openapi.json").write_text("{", encoding="utf-8")
        code, out = self.check()
        self.assertEqual((code, "openapi.json không đọc được" in out), (1, True))

    def test_new_pack_or_base_without_version(self):
        self.write(version=None, baseline=self.BASE)
        self.git("commit", "-qam", "gốc không VERSION")
        self.write(version="0.0.1", baseline={"paths": {}})
        self.assertEqual(self.check()[0], 1)  # gốc không đọc được phiên bản: chặt
        fresh = self.repo / "packs" / "moi"
        (fresh / "starter" / "contract").mkdir(parents=True)
        (fresh / "starter" / "contract" / "baseline.json").write_text("{}", encoding="utf-8")
        self.assertEqual(self.run_main("check", str(fresh), "main")[0], 0)  # gói mới: chưa có baseline ở gốc

    def test_broken_inputs(self):
        (self.pack / "starter" / "contract" / "baseline.json").write_text("{", encoding="utf-8")
        code, out = self.check()
        self.assertEqual((code, "không đọc được" in out), (1, True))
        (self.pack / "starter" / "contract" / "baseline.json").unlink()
        code, out = self.check()
        self.assertEqual((code, "không đọc được" in out), (1, True))
        self.assertEqual(self.run_main("check", str(self.pack), "khong-co-ref")[0], 2)
        self.assertEqual(self.run_main("check", str(self.pack))[0], 2)
        self.assertEqual(self.run_main("zap", "a", "b")[0], 2)

    def test_real_repo_version_and_ci_runs_check(self):
        self.assertRegex((ROOT / "VERSION").read_text(encoding="utf-8").strip(), EXACT)
        self.assertEqual(self.run_main("check", str(PACK), "HEAD")[0], 0)
        wf = (ROOT / ".github" / "workflows" / "pack-web-api.yml").read_text(encoding="utf-8")
        self.assertIn('python3 tests/pack_baseline.py check "$PACK" "origin/$BASE_REF"', wf)
        self.assertIn("BASE_REF: ${{ github.base_ref }}", wf)
        self.assertIn("- tests/pack_baseline.py", wf)  # đổi script kiểm cũng chạy workflow


if __name__ == "__main__":
    unittest.main()
