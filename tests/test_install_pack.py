"""Test `install.py --pack` (ADR-0068 lát C, T-3688): starter chỉ vào repo sạch, managed nâng theo hash manifest, drift
trong `--plan`, idempotent, lùi bản bằng bản khung cũ. Gói giả dựng trong khung giả (`install.SRC`), không dùng gói thật."""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
import unittest.mock as mock
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import install

PACK = "demo"
STARTER_V1 = {"src/app.ts": "export const app = 1;\n", "README.md": "# Dự án mẫu\n"}
MANAGED_V1 = {
    "scripts/check.sh": "#!/bin/sh\necho v1\n",
    "ops/policy.json": '{"v": 1}\n',
    "ops/keep.txt": "giữ nguyên\n",
}
YAML_KEYS = {"lint": "pnpm lint", "e2e": "pnpm e2e"}


def pack_doc(**over: Any) -> dict[str, Any]:
    doc: dict[str, Any] = {
        "schema": 1,
        "id": PACK,
        "owner": "chủ dự án",
        "support_until": "2027-06-30",
        "compat": {"node": "24"},
        "profiles": ["web-api"],
        "controls": ["SEC-AUTH-001"],
        "xt_yaml": dict(YAML_KEYS),
    }
    doc.update(over)
    return doc


def write_tree(root: Path, files: dict[str, str]) -> None:
    for rel, text in files.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(text, encoding="utf-8")


def make_src(
    base: Path,
    name: str,
    managed: dict[str, str] | None = None,
    starter: dict[str, str] | None = None,
    doc: Any = None,
    xt_yaml: str | None = 'lint: ""\ntest: "make test"\n',
) -> Path:
    """Khung giả tối thiểu (như `make_fake_src` của test_install) + gói `demo` ở framework/templates/packs/."""
    src = base / name
    write_tree(src, {"framework/x.md": "x\n", "VERSION": "9.9.9\n"})
    write_tree(src, {f"scripts/{f}": "# giả\n" for f in ("xt.py", "dev-task.sh", "check-links.py")})
    write_tree(src, {".claude/settings.json": '{"hooks": {}}\n'})
    for d in install.HARNESS_DIRS:
        (src / ".claude" / d).mkdir()
    if xt_yaml is not None:
        write_tree(src, {"framework/templates/xt.yaml": xt_yaml})
    pack = src / install.PACKS_DIR / PACK
    pack.mkdir(parents=True)
    (pack / "pack.json").write_text(json.dumps(pack_doc() if doc is None else doc), encoding="utf-8")
    write_tree(pack / "starter", STARTER_V1 if starter is None else starter)
    write_tree(pack / "managed", MANAGED_V1 if managed is None else managed)
    return src


class PackBase(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name).resolve()
        # đích không phải repo git kể cả khi TMPDIR nằm trong một repo
        ceiling = mock.patch.dict(os.environ, {"GIT_CEILING_DIRECTORIES": str(self.tmp.parent)})
        ceiling.start()
        self.addCleanup(ceiling.stop)
        self.target = self.tmp / "dich"
        self.target.mkdir()
        self.v1 = make_src(self.tmp, "khung1")

    def run_main(self, src: Path, *args: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(install, "SRC", src), redirect_stdout(out), redirect_stderr(err):
            code = install.main([str(self.target), *args])
        return code, out.getvalue(), err.getvalue()

    def install(self, src: Path, label: str = "p1", *extra: str) -> str:
        code, _, err = self.run_main(src, "--label", label, "--no-git-hooks", "--pack", PACK, *extra)
        self.assertEqual(code, 0, err)
        return err

    def plan(self, src: Path, *extra: str) -> dict[str, Any]:
        code, out, err = self.run_main(src, "--plan", "--no-git-hooks", *extra)
        self.assertEqual(code, 0, err)
        plan: dict[str, Any] = json.loads(out)
        return plan

    def pack_plan(self, src: Path) -> dict[str, Any]:
        pack: dict[str, Any] = self.plan(src, "--pack", PACK)["pack"]
        return pack

    def manifest(self) -> dict[str, Any]:
        doc: dict[str, Any] = json.loads((self.target / install.MANIFEST_V2).read_text(encoding="utf-8"))
        legacy = json.loads((self.target / install.MANIFEST).read_text(encoding="utf-8"))
        self.assertEqual(doc["files"], legacy)  # hai manifest cùng map `files`
        return doc

    def read(self, rel: str) -> str:
        return (self.target / rel).read_text(encoding="utf-8")

    @staticmethod
    def actions(rows: list[dict[str, str]]) -> dict[str, str]:
        return {r["path"]: r["action"] for r in rows}


class PackFreshTest(PackBase):
    def test_fresh_install_copies_starter_managed_and_sets_yaml(self) -> None:
        plan = self.pack_plan(self.v1)
        self.assertEqual(plan["mode"], "fresh")
        self.assertEqual(set(self.actions(plan["starter"]).values()), {"copied"})
        self.assertEqual(set(self.actions(plan["managed"]).values()), {"copied"})
        self.assertEqual(plan["xt_yaml"], {"apply": YAML_KEYS})
        self.assertFalse((self.target / ".xtemplates").exists())  # --plan không ghi gì
        err = self.install(self.v1)
        for rel, text in {**STARTER_V1, **MANAGED_V1}.items():
            self.assertEqual(self.read(rel), text, rel)
        self.assertTrue(os.access(self.target / "scripts" / "check.sh", os.X_OK))  # giữ bit chạy `.sh`
        yaml = self.read("xt.yaml")
        self.assertIn('lint: "pnpm lint"\n', yaml)
        self.assertIn('test: "make test"\n', yaml)  # khoá không thuộc gói giữ nguyên
        self.assertTrue(yaml.endswith('e2e: "pnpm e2e"\n'))  # khoá chưa có → nối cuối
        doc = self.manifest()
        self.assertEqual(
            doc["packs"],
            {PACK: {"version": "p1", "starter": sorted(STARTER_V1), "managed": sorted(MANAGED_V1)}},
        )
        for rel, text in MANAGED_V1.items():
            self.assertEqual(doc["files"][rel], install.hash_label(install.sha256(text.encode())))
        self.assertFalse(set(STARTER_V1) & set(doc["files"]))  # starter không băm — là của dự án
        self.assertIn(f"gói {PACK}: fresh", err)
        self.assertIn(f"gói {PACK}/starter: copied 2", err)
        self.assertIn(f"gói {PACK}/managed: copied 3", err)
        self.assertIn(f"gói {PACK}/xt.yaml: đặt 2 khoá (lint, e2e)", err)

    def test_fresh_keeps_existing_files_of_project(self) -> None:
        """Repo sạch (không package.json) đã có vài file: starter copy-if-absent — giống → kept, khác → kept-own."""
        write_tree(self.target, {"README.md": "# của tôi\n", "src/app.ts": STARTER_V1["src/app.ts"]})
        self.assertEqual(
            self.actions(self.pack_plan(self.v1)["starter"]), {"README.md": "kept-own", "src/app.ts": "kept"}
        )
        err = self.install(self.v1)
        self.assertEqual(self.read("README.md"), "# của tôi\n")
        self.assertIn("starter: kept 1 · kept-own 1", err)
        self.assertEqual(self.manifest()["packs"][PACK]["starter"], [])  # chỉ ghi file đã chép

    def test_fresh_keeps_filled_yaml_keys_of_project(self) -> None:
        """Repo sạch mà xt.yaml đã điền lệnh riêng (Python…): chỉ đặt khoá vắng/rỗng, khoá đã điền giữ + báo (review 🟠)."""
        src = make_src(self.tmp, "khung-yaml-day", xt_yaml="lint: \"ruff check .\"  # của dự án\ne2e: ''\n")
        plan = self.pack_plan(src)  # chưa có xt.yaml ở đích: mọi khoá đều đặt
        self.assertEqual(plan["xt_yaml"], {"apply": YAML_KEYS})
        write_tree(self.target, {"xt.yaml": "lint: \"ruff check .\"  # của dự án\ne2e: ''\n"})
        self.assertEqual(
            self.pack_plan(src)["xt_yaml"],
            {"apply": {"e2e": "pnpm e2e"}, "kept": {"lint": {"own": '"ruff check ."', "pack": "pnpm lint"}}},
        )
        err = self.install(src)
        self.assertEqual(self.read("xt.yaml"), 'lint: "ruff check ."  # của dự án\ne2e: "pnpm e2e"\n')
        self.assertIn('giữ `lint: "ruff check ."` của dự án — gói đề nghị "pnpm lint"', err)
        self.assertIn("đặt 1 khoá (e2e)", err)

    def test_yaml_own_value_and_split(self) -> None:
        text = 'a: ""\nb:\nc: "x"  # chú thích\nd: # chỉ chú thích\ne: "pnpm lint"\n'
        self.assertEqual([install.yaml_own_value(text, k) for k in "abcdez"], ["", "", '"x"', "", '"pnpm lint"', None])
        apply, kept = install.pack_yaml_split(text, {"a": "1", "c": "2", "e": "pnpm lint", "z": "3"})
        self.assertEqual((apply, kept), ({"a": "1", "e": "pnpm lint", "z": "3"}, {"c": {"own": '"x"', "pack": "2"}}))
        empty: dict[str, str] = {}
        self.assertEqual(install.pack_yaml_split(text, empty), ({}, {}))
        write_tree(self.target, {"xt.yaml": "\xff"})  # không đọc được → coi như rỗng: đặt mọi khoá
        (self.target / "xt.yaml").write_bytes(b"\xff\xfe")
        with redirect_stderr(io.StringIO()):
            self.assertEqual(install.pack_yaml_plan(self.target, "fresh", {"a": "1"}), {"apply": {"a": "1"}})

    def test_fresh_merges_missing_gitignore_lines(self) -> None:
        src = make_src(self.tmp, "khung-gi", starter={**STARTER_V1, ".gitignore": "node_modules/\n.env\n"})
        write_tree(self.target, {".gitignore": "build/"})
        self.assertEqual(self.actions(self.pack_plan(src)["starter"])[".gitignore"], "merged")
        err = self.install(src)
        self.assertTrue(self.read(".gitignore").startswith("build/\nnode_modules/\n.env\n"))
        self.assertIn("merged 1", err)
        self.assertEqual(self.actions(self.pack_plan(src)["starter"])[".gitignore"], "owned-by-project")

    def test_gitignore_already_has_lines_or_unreadable(self) -> None:
        src = make_src(self.tmp, "khung-gi2", starter={".gitignore": "node_modules/\n"})
        write_tree(self.target, {".gitignore": "x\nnode_modules/\n"})
        self.assertEqual(self.actions(self.pack_plan(src)["starter"])[".gitignore"], "kept-own")
        (self.target / ".gitignore").write_bytes(b"\xff\xfe")
        self.assertEqual(self.actions(self.pack_plan(src)["starter"])[".gitignore"], "kept-own")

    def test_framework_copy_skips_pack_payloads(self) -> None:
        """`.xtemplates/framework` không chứa starter/managed của gói — test/`package.json` của gói không bị công cụ
        của dự án đích (vitest, workspace) nhặt nhầm (review lát B 🔴); `pack.json`/README vẫn có."""
        write_tree(self.v1 / "framework/templates/packs/demo", {"README.md": "x\n"})
        write_tree(self.v1 / "framework/other/starter", {"keep.md": "x\n"})  # chỉ thư mục con của packs/<id>/
        code, _, err = self.run_main(self.v1, "--label", "p1", "--no-git-hooks")
        self.assertEqual(code, 0, err)
        packs = self.target / ".xtemplates/framework/templates/packs/demo"
        self.assertEqual(sorted(p.name for p in packs.iterdir()), ["README.md", "pack.json"])
        self.assertTrue((self.target / ".xtemplates/framework/other/starter/keep.md").is_file())

    def test_fresh_without_yaml_template_creates_xt_yaml(self) -> None:
        src = make_src(self.tmp, "khung-khong-yaml", xt_yaml=None)
        self.install(src)
        self.assertEqual(self.read("xt.yaml"), 'lint: "pnpm lint"\ne2e: "pnpm e2e"\n')

    def test_pack_without_dirs_or_yaml_keys(self) -> None:
        src = make_src(self.tmp, "khung-rong", managed={}, starter={}, doc=pack_doc(xt_yaml={}))
        self.assertFalse((src / install.PACKS_DIR / PACK / "starter").exists())
        err = self.install(src)
        self.assertIn("starter: không có file", err)
        self.assertIn("managed: không có file", err)
        self.assertNotIn("/xt.yaml:", err)
        self.assertEqual(self.read("xt.yaml"), 'lint: ""\ntest: "make test"\n')
        self.assertEqual(self.manifest()["packs"][PACK], {"version": "p1", "starter": [], "managed": []})

    def test_pack_tree_skips_pycache(self) -> None:
        write_tree(self.v1 / install.PACKS_DIR / PACK / "managed", {"x/__pycache__/m.pyc": "bin"})
        with mock.patch.object(install, "SRC", self.v1):
            self.assertEqual([r for r, _ in install.pack_tree(PACK, "managed")], sorted(MANAGED_V1))


class PackBrownfieldTest(PackBase):
    def test_brownfield_skips_starter_and_suggests_yaml(self) -> None:
        write_tree(self.target, {"package.json": "{}\n"})
        plan = self.pack_plan(self.v1)
        self.assertEqual(plan["mode"], "brownfield")
        self.assertEqual(set(self.actions(plan["starter"]).values()), {"skipped-brownfield"})
        # dự án đang chạy: file managed mới chỉ là đề xuất — không đổi hành vi (workflow mới làm đỏ chính sách CI của
        # hotel-manager, lát C)
        self.assertEqual(set(self.actions(plan["managed"]).values()), {"updated-new"})
        self.assertEqual(plan["xt_yaml"], {"suggested": YAML_KEYS})
        err = self.install(self.v1)
        for rel in STARTER_V1:
            self.assertFalse((self.target / rel).exists(), rel)
        for rel, text in MANAGED_V1.items():
            self.assertFalse((self.target / rel).exists(), rel)
            self.assertEqual(self.read(rel + ".xtemplates-new"), text)
        self.assertEqual(self.read("xt.yaml"), 'lint: ""\ntest: "make test"\n')  # không đụng cấu hình dự án
        self.assertIn("gợi ý khoá lint, e2e — không ghi", err)
        self.assertIn("managed: updated-new 3", err)
        self.assertEqual(self.manifest()["packs"][PACK]["starter"], [])
        # nâng bản khi đề xuất chưa được nhận: vẫn là đề xuất; nhận (đổi tên) rồi thì nâng theo hash
        self.assertEqual(set(self.actions(self.pack_plan(self.v1)["managed"]).values()), {"updated-new"})
        (self.target / "ops/keep.txt.xtemplates-new").rename(self.target / "ops/keep.txt")
        self.assertEqual(self.actions(self.pack_plan(self.v1)["managed"])["ops/keep.txt"], "kept")

    def test_package_json_symlink_counts_as_brownfield(self) -> None:
        (self.target / "package.json").symlink_to(self.tmp / "khong-co")
        self.assertEqual(self.pack_plan(self.v1)["mode"], "brownfield")


class PackUpgradeTest(PackBase):
    def setUp(self) -> None:
        super().setUp()
        self.v2 = make_src(
            self.tmp,
            "khung2",
            managed={**MANAGED_V1, "scripts/check.sh": "#!/bin/sh\necho v2\n", "ops/policy.json": '{"v": 2}\n'},
            starter={**STARTER_V1, "src/app.ts": "export const app = 2;\n"},
        )

    def test_upgrade_updates_untouched_and_flags_customized(self) -> None:
        self.install(self.v1)
        write_tree(self.target, {"ops/policy.json": '{"v": "của dự án"}\n', "ops/keep.txt": "dự án sửa\n"})
        write_tree(self.target, {"src/app.ts": "// mã của dự án\n", "xt.yaml": 'lint: "biome check"\n'})
        plan = self.pack_plan(self.v2)
        self.assertEqual(plan["mode"], "upgrade")
        self.assertEqual(set(self.actions(plan["starter"]).values()), {"owned-by-project"})
        self.assertEqual(
            self.actions(plan["managed"]),
            {"ops/keep.txt": "kept-own", "ops/policy.json": "updated-new", "scripts/check.sh": "updated"},
        )
        self.assertEqual(plan["xt_yaml"], {"suggested": YAML_KEYS})
        err = self.install(self.v2, "p2")
        self.assertEqual(self.read("scripts/check.sh"), "#!/bin/sh\necho v2\n")
        self.assertEqual(self.read("ops/policy.json"), '{"v": "của dự án"}\n')
        self.assertEqual(self.read("ops/policy.json.xtemplates-new"), '{"v": 2}\n')
        self.assertEqual(self.read("ops/keep.txt"), "dự án sửa\n")
        self.assertEqual(self.read("src/app.ts"), "// mã của dự án\n")  # starter là của dự án
        self.assertTrue(self.read("xt.yaml").startswith('lint: "biome check"\n'))  # nâng bản không đặt khoá gói
        self.assertNotIn("pnpm", self.read("xt.yaml"))
        self.assertIn("managed: kept-own 1 · updated 1 · updated-new 1", err)
        self.assertIn(".xtemplates-new (dự án đã sửa file", err)
        doc = self.manifest()
        self.assertEqual(doc["packs"][PACK]["version"], "p2")
        self.assertEqual(doc["packs"][PACK]["starter"], sorted(STARTER_V1))  # giữ danh sách lần cài đầu
        self.assertEqual(doc["files"]["ops/policy.json"], install.hash_label(install.sha256(b'{"v": 2}\n')))
        # lần sau cùng bản v2: file đã sửa thành kept-own (không gộp tay lại)
        self.assertEqual(self.actions(self.pack_plan(self.v2)["managed"])["ops/policy.json"], "kept-own")

    def test_idempotent_rerun_writes_nothing(self) -> None:
        self.install(self.v1)
        before = self.manifest()
        stamps = {rel: (self.target / rel).stat().st_mtime_ns for rel in MANAGED_V1}
        self.assertEqual(set(self.actions(self.pack_plan(self.v1)["managed"]).values()), {"kept"})
        err = self.install(self.v1)
        self.assertIn("managed: kept 3", err)
        self.assertIn("starter: owned-by-project 2", err)
        self.assertEqual(self.manifest(), before)
        self.assertEqual({rel: (self.target / rel).stat().st_mtime_ns for rel in MANAGED_V1}, stamps)
        self.assertEqual(list(self.target.rglob("*.xtemplates-new")), [])

    def test_rollback_with_older_framework(self) -> None:
        """v1 → v2 → v1: file managed còn đúng hash v2 được đưa về v1 (`updated`), hash manifest về v1."""
        self.install(self.v1)
        self.install(self.v2, "p2")
        self.assertEqual(self.read("ops/policy.json"), '{"v": 2}\n')
        self.assertEqual(self.actions(self.pack_plan(self.v1)["managed"])["ops/policy.json"], "updated")
        self.install(self.v1, "p1")
        for rel, text in MANAGED_V1.items():
            self.assertEqual(self.read(rel), text, rel)
        doc = self.manifest()
        self.assertEqual(doc["files"]["ops/policy.json"], install.hash_label(install.sha256(b'{"v": 1}\n')))
        self.assertEqual(doc["packs"][PACK]["version"], "p1")

    def test_plain_reinstall_keeps_pack_hashes(self) -> None:
        """Cài lại không `--pack` (bước harness ghi lại manifest): hash managed và bản ghi gói còn nguyên."""
        self.install(self.v1)
        before = self.manifest()
        code, _, err = self.run_main(self.v1, "--label", "p1", "--no-git-hooks")
        self.assertEqual(code, 0, err)
        after = self.manifest()
        self.assertEqual(after["packs"], before["packs"])
        for rel in MANAGED_V1:
            self.assertEqual(after["files"][rel], before["files"][rel])
        self.assertEqual(set(self.actions(self.pack_plan(self.v1)["managed"]).values()), {"kept"})

    def test_corrupt_pack_record_still_upgrades(self) -> None:
        self.install(self.v1)
        doc = self.manifest()
        doc["packs"] = {PACK: "hỏng", "khac": {"managed": "không phải danh sách"}}
        (self.target / install.MANIFEST_V2).write_text(json.dumps(doc), encoding="utf-8")
        self.assertEqual(install.pack_managed_paths(self.target), set())
        self.install(self.v2, "p2")
        packs = self.manifest()["packs"]
        self.assertEqual(packs[PACK]["starter"], [])
        self.assertIn("khac", packs)  # gói khác giữ nguyên
        (self.target / install.MANIFEST_V2).write_text("[]", encoding="utf-8")
        self.assertEqual(install.recorded_packs(self.target), {})


class PackSymlinkTest(PackBase):
    def test_symlink_destinations_are_skipped(self) -> None:
        outside = self.tmp / "ngoai"
        outside.mkdir()
        (outside / "policy.json").write_text("của người khác\n", encoding="utf-8")
        (self.target / "ops").mkdir()
        (self.target / "ops" / "policy.json").symlink_to(outside / "policy.json")
        (self.target / "src").symlink_to(outside, target_is_directory=True)  # thư mục giữa là symlink
        plan = self.pack_plan(self.v1)
        self.assertEqual(self.actions(plan["managed"])["ops/policy.json"], "skipped-symlink")
        self.assertEqual(self.actions(plan["starter"])["src/app.ts"], "skipped-symlink")
        err = self.install(self.v1)
        self.assertEqual((outside / "policy.json").read_text(encoding="utf-8"), "của người khác\n")
        self.assertFalse((outside / "app.ts").exists())
        self.assertIn("skipped-symlink 1", err)
        self.assertNotIn("ops/policy.json", self.manifest()["files"])

    def test_xt_yaml_symlink_or_unreadable_not_written(self) -> None:
        outside = self.tmp / "ngoai.yaml"
        outside.write_text("lint: x\n", encoding="utf-8")
        (self.target / "xt.yaml").symlink_to(outside)
        err = io.StringIO()
        with redirect_stderr(err):
            install.install_pack_yaml(self.target, PACK, "fresh", YAML_KEYS)
        self.assertEqual(outside.read_text(encoding="utf-8"), "lint: x\n")
        self.assertIn("bỏ qua symlink", err.getvalue())
        (self.target / "xt.yaml").unlink()
        (self.target / "xt.yaml").write_bytes(b"lint: \xff\n")
        with redirect_stderr(io.StringIO()):
            install.install_pack_yaml(self.target, PACK, "fresh", YAML_KEYS)
        self.assertEqual((self.target / "xt.yaml").read_bytes(), b"lint: \xff\n")


class PackYamlTest(unittest.TestCase):
    def test_set_keys_keeps_crlf_and_replaces_whole_line(self) -> None:
        text = 'a: 1\r\nlint: "cũ" # chú thích\r\nlintx: y\r\n'
        self.assertEqual(
            install.yaml_set_keys(text, {"lint": 'pnpm "lint"', "b": "c"}),
            'a: 1\r\nlint: "pnpm \\"lint\\""\r\nlintx: y\r\nb: "c"\r\n',
        )
        self.assertEqual(install.yaml_set_keys("a: 1", {"b": "c"}), 'a: 1\nb: "c"\n')
        self.assertEqual(install.yaml_set_keys("", {"b": "c"}), 'b: "c"\n')


class PackGitRootTest(PackBase):
    """`--pack` có file managed dưới `.github/` vào thư mục con của repo git: GitHub không chạy workflow ở đó (AUD-HAR-227,
    như `--with-github` — AUD-CI-012) → từ chối trước khi ghi; gói không có `.github/` hoặc ở gốc repo → cài như cũ."""

    def setUp(self) -> None:
        super().setUp()
        self.mono = self.tmp / "mono"
        self.target = self.mono / "apps" / "web"
        self.target.mkdir(parents=True)
        subprocess.run(["git", "init", "-q", str(self.mono)], check=True)
        self.gh = make_src(self.tmp, "khung-gh", managed={**MANAGED_V1, ".github/workflows/pack.yml": "on: push\n"})

    def test_subdir_with_github_files_refused(self) -> None:
        for mode in ("--plan", "--label"):
            with self.subTest(mode=mode):
                args = (mode, "p1") if mode == "--label" else (mode,)
                code, out, err = self.run_main(self.gh, *args, "--no-git-hooks", "--pack", PACK)
                self.assertEqual((code, out), (2, ""), err)
                self.assertIn("không phải gốc repo git", err)
                self.assertIn(str(self.mono / ".github"), err)
        self.assertEqual(list(self.target.iterdir()), [])  # từ chối trước khi ghi gì

    def test_subdir_without_github_files_or_at_root_installs(self) -> None:
        self.install(self.v1)  # gói không ghi .github/: thư mục con được
        self.target = self.mono
        self.install(self.gh)
        self.assertTrue((self.mono / ".github" / "workflows" / "pack.yml").is_file())


class PackArgsTest(PackBase):
    def assert_rejected(self, src: Path, pack_id: str, reason: str) -> None:
        for mode in ("--plan", "--no-git-hooks"):
            code, out, err = self.run_main(src, mode, "--pack", pack_id)
            self.assertEqual(code, 2, err)
            self.assertEqual(out, "")
            self.assertIn("✗ --pack: ", err)
            self.assertIn(reason, err)
        self.assertEqual(list(self.target.iterdir()), [])  # không ghi gì

    def test_unknown_or_unsafe_id(self) -> None:
        (self.v1 / install.PACKS_DIR / "rong").mkdir()  # thư mục không có pack.json: không phải gói
        self.assert_rejected(self.v1, "khong-co", "không biết gói 'khong-co' — có: demo")
        self.assert_rejected(self.v1, "../packs/demo", "không biết gói")
        bare = make_src(self.tmp, "khung-khong-goi")
        (bare / install.PACKS_DIR / PACK / "pack.json").unlink()
        self.assert_rejected(bare, PACK, "chưa có gói nào")
        with mock.patch.object(install, "SRC", self.tmp / "khong-ton-tai"):
            self.assertEqual(install.available_packs(), [])

    def test_invalid_pack_json(self) -> None:
        cases: list[tuple[Any, str]] = [
            (["không phải object"], "không phải object JSON"),
            (pack_doc(schema=2), "schema 2"),
            (pack_doc(schema=True), "schema True"),
            (pack_doc(id="khac"), "id 'khac' khác tên thư mục 'demo'"),
            (pack_doc(xt_yaml=["lint"]), "xt_yaml phải là object"),
            (pack_doc(xt_yaml={"lint": 1}), "xt_yaml"),
            (pack_doc(xt_yaml={"lint": "a\nrm: x"}), "xt_yaml"),
            (pack_doc(xt_yaml={"lint": "a\rb"}), "xt_yaml"),
            (pack_doc(xt_yaml={"a b": "x"}), "xt_yaml"),
            # ghi bằng nháy JSON mà `yaml_get`/`yaml_scalar` không giải escape (AUD-HAR-227) → chặn ở pack.json
            (pack_doc(xt_yaml={"lint": 'pnpm "lint"'}), "xt_yaml"),
            (pack_doc(xt_yaml={"lint": "a\\b"}), "xt_yaml"),
            (pack_doc(xt_yaml={"lint": "a\tb"}), "xt_yaml"),
        ]
        for i, (doc, reason) in enumerate(cases):
            with self.subTest(reason=reason):
                self.assert_rejected(make_src(self.tmp, f"khung-sai-{i}", doc=doc), PACK, reason)
        broken = make_src(self.tmp, "khung-json-hong")
        (broken / install.PACKS_DIR / PACK / "pack.json").write_text("{", encoding="utf-8")
        self.assert_rejected(broken, PACK, "pack.json không đọc được")

    def test_plan_without_pack_has_no_pack_key(self) -> None:
        plan = self.plan(self.v1)
        self.assertNotIn("pack", plan)
        self.assertEqual(self.plan(self.v1, "--pack", "")["files"], plan["files"])  # `--pack ""` = không gói


if __name__ == "__main__":
    unittest.main()
