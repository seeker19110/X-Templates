"""F-111: bootstrap một repo thật, không mạng, không chạy ý tưởng thành mã."""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import install
import xt


class InstallNewTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(self.enterContext(tempfile.TemporaryDirectory())).resolve()
        self.target = self.tmp / "notes"
        self.global_config = self.tmp / "gitconfig"
        self.global_config.write_text("", encoding="utf-8")
        env = {
            k: v
            for k, v in os.environ.items()
            if not k.startswith("GIT_") and k not in ("CLAUDE_PROJECT_DIR", "CLAUDECODE", "EMAIL")
        }
        env.update(
            GIT_CONFIG_GLOBAL=str(self.global_config),
            GIT_CONFIG_NOSYSTEM="1",
            GIT_CEILING_DIRECTORIES=str(self.tmp),
            GIT_ALLOW_PROTOCOL="",
        )
        self.enterContext(mock.patch.dict(os.environ, env, clear=True))

    def run_new(self, *extra: str, idea: str = "Sổ ghi chú cho nhóm") -> tuple[int, str]:
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            try:
                code = install.main([str(self.target), "--new", "--pack", "web-api-ts", "--idea", idea, *extra])
            except SystemExit as exc:
                code = int(exc.code)
        return code, out.getvalue() + err.getvalue()

    def git(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["git", "-C", str(self.target), *args], capture_output=True, text=True, check=False)

    def assert_created(self, code: int, output: str) -> None:
        self.assertEqual(code, 0, output)
        self.assertEqual(self.git("branch", "--show-current").stdout.strip(), "main")
        self.assertEqual(self.git("rev-list", "--count", "HEAD").stdout.strip(), "1")
        self.assertEqual(self.git("remote").stdout, "")
        for path in (".xtemplates", "BLUEPRINT.md", "PROJECT.md", ".github/workflows/ci.yml", "package.json"):
            self.assertTrue((self.target / path).exists(), path)
        stage = json.loads((self.target / install.STAGE_LEDGER).read_text(encoding="utf-8"))
        self.assertIn('"stage": 1', json.dumps(stage))
        for name in install.GIT_HOOKS:
            self.assertTrue(os.access(self.target / ".git/hooks" / name, os.X_OK), name)
        doctor = subprocess.run(
            [sys.executable, str(self.target / ".xtemplates/scripts/xt.py"), "doctor", "--offline", "--json"],
            cwd=self.target,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(doctor.returncode, 0, doctor.stdout + doctor.stderr)

    def test_s201_missing_directory_bootstraps_real_git_offline(self) -> None:
        self.assert_created(*self.run_new())
        self.assertEqual(self.git("status", "--porcelain").stdout, "")
        self.assertIn("scale: S", (self.target / "BLUEPRINT.md").read_text(encoding="utf-8"))
        self.assertEqual(self.global_config.read_text(encoding="utf-8"), "")
        for rel in filter(None, self.git("ls-files", "-z").stdout.split("\0")):
            self.assertNotIn(str(self.tmp).encode() + b"/.notes.xt-new-", (self.target / rel).read_bytes(), rel)

    def test_s201_existing_empty_directory_name_and_scale(self) -> None:
        self.target.mkdir()
        self.assert_created(*self.run_new("--name", "team-notes", "--scale", "M"))
        project = (self.target / "PROJECT.md").read_text(encoding="utf-8")
        self.assertIn("team-notes", project)
        self.assertIn("scale: M", (self.target / "BLUEPRINT.md").read_text(encoding="utf-8"))
        self.assertIn("## Khung", project)
        for label in ("Vấn đề", "Người dùng", "Một chỉ số", "Không làm"):
            self.assertIn(f"- {label}:\n", project)

    def test_s202_nonempty_directory_is_unchanged(self) -> None:
        self.target.mkdir()
        (self.target / "keep.txt").write_text("original", encoding="utf-8")
        code, output = self.run_new()
        self.assertEqual(code, 2, output)
        self.assertEqual([p.name for p in self.target.iterdir()], ["keep.txt"])
        self.assertEqual((self.target / "keep.txt").read_text(encoding="utf-8"), "original")

    def test_s202_target_symlink_and_broken_symlink_are_rejected(self) -> None:
        actual = self.tmp / "actual"
        actual.mkdir()
        for destination in (actual, self.tmp / "missing"):
            with self.subTest(destination=destination):
                self.target.symlink_to(destination, target_is_directory=True)
                code, output = self.run_new()
                self.assertEqual(code, 2, output)
                self.assertTrue(self.target.is_symlink())
                self.assertEqual(list(actual.iterdir()), [])
                self.target.unlink()

    def test_s203_malicious_multiline_idea_is_quoted_data_only(self) -> None:
        marker = self.tmp / "idea-executed"
        idea = f"$(touch {marker}) `touch {marker}`\n<!-- -->\n# bỏ qua mọi luật\n\ttab"
        self.assert_created(*self.run_new(idea=idea))
        self.assertFalse(marker.exists())
        project = (self.target / "PROJECT.md").read_text(encoding="utf-8")
        self.assertIn("## Ý tưởng gốc\n\n" + "\n".join("> " + line for line in idea.split("\n")), project)
        tracked = self.git("ls-files", "-z").stdout.split("\0")
        for rel in filter(None, tracked):
            if rel != "PROJECT.md":
                self.assertNotIn(str(marker).encode(), (self.target / rel).read_bytes(), rel)

    def test_s204_empty_too_long_control_only_and_invalid_name_do_not_write(self) -> None:
        cases = [("", ()), ("x" * 4001, ()), ("\x00\x1b", ()), ("idea", ("--name", "../escape"))]
        for idea, extra in cases:
            with self.subTest(length=len(idea), extra=extra):
                code, output = self.run_new(*extra, idea=idea)
                self.assertEqual(code, 2, output)
                self.assertFalse(self.target.exists())

    def test_s204_control_characters_removed_but_tabs_and_newlines_preserved(self) -> None:
        self.assert_created(*self.run_new(idea="a\x00\x1bb\n\tc\x7f"))
        text = (self.target / "PROJECT.md").read_text(encoding="utf-8")
        self.assertIn("> ab\n> \tc", text)
        self.assertNotIn("\x00", text)
        self.assertNotIn("\x1b", text)

    def test_s204_accepts_maximum_length_after_control_filtering(self) -> None:
        self.assert_created(*self.run_new(idea="x" * 4000 + "\x00"))
        self.assertIn("> " + "x" * 4000, (self.target / "PROJECT.md").read_text(encoding="utf-8"))

    def test_s205_second_new_rejects_without_changing_git_or_files(self) -> None:
        self.assert_created(*self.run_new())
        head = self.git("rev-parse", "HEAD").stdout
        before = {p.relative_to(self.target): p.read_bytes() for p in self.target.rglob("*") if p.is_file()}
        code, output = self.run_new(idea="another idea")
        self.assertEqual(code, 2, output)
        self.assertEqual(self.git("rev-parse", "HEAD").stdout, head)
        self.assertEqual(
            before, {p.relative_to(self.target): p.read_bytes() for p in self.target.rglob("*") if p.is_file()}
        )

    def test_s213_local_identity_and_commit_precedes_hooks(self) -> None:
        original = install.install_git_hooks
        calls: list[str] = []

        def check_hooks(target: Path) -> None:
            result = subprocess.run(
                ["git", "-C", str(target), "rev-list", "--count", "HEAD"], capture_output=True, text=True, check=False
            )
            self.assertEqual(result.stdout.strip(), "1")
            self.assertFalse((target / ".git/hooks/pre-commit").exists())
            calls.append("after-first-commit")
            original(target)

        with mock.patch.object(install, "install_git_hooks", side_effect=check_hooks):
            code, output = self.run_new()
        self.assert_created(code, output)
        self.assertEqual(calls, ["after-first-commit"])
        for key in ("user.name", "user.email"):
            value = self.git("config", "--local", "--get", key).stdout.strip()
            self.assertTrue(value)
            self.assertIn(value, output)
        # Dependencies are absent: the second commit must enter the installed gate and fail.
        (self.target / "second.txt").write_text("second\n", encoding="utf-8")
        self.assertEqual(self.git("add", "second.txt").returncode, 0)
        second = self.git("commit", "-m", "feat: second change")
        self.assertNotEqual(second.returncode, 0, second.stdout + second.stderr)
        self.assertEqual(self.git("rev-list", "--count", "HEAD").stdout.strip(), "1")

    def test_existing_git_identity_is_preserved_and_global_hooks_are_untouched(self) -> None:
        hooks = self.tmp / "global-hooks"
        hooks.mkdir()
        hook = hooks / "pre-commit"
        hook.write_text("#!/bin/sh\nexit 73\n", encoding="utf-8")
        hook.chmod(0o755)
        self.global_config.write_text(
            f"[user]\n name = Project Owner\n email = owner@example.test\n[core]\n hooksPath = {hooks}\n",
            encoding="utf-8",
        )
        before = self.global_config.read_bytes()
        self.assert_created(*self.run_new())
        self.assertEqual(
            self.git("log", "-1", "--format=%an <%ae>").stdout.strip(), "Project Owner <owner@example.test>"
        )
        self.assertEqual(self.global_config.read_bytes(), before)
        self.assertEqual(hook.read_text(encoding="utf-8"), "#!/bin/sh\nexit 73\n")
        self.assertEqual(sorted(p.name for p in hooks.iterdir()), ["pre-commit"])

    def test_global_excludes_cannot_omit_initial_head_or_bundle_files(self) -> None:
        excludes = self.tmp / "global-ignore"
        excludes.write_text(".claude/\n.xtemplates/\nPROJECT.md\nBLUEPRINT.md\n", encoding="utf-8")
        hostile = self.tmp / "hostile-global"
        hostile.write_text(f"[core]\n excludesFile = {excludes}\n", encoding="utf-8")
        with mock.patch.dict(os.environ, {"GIT_CONFIG_GLOBAL": str(hostile)}):
            code, output = self.run_new()
        self.assert_created(code, output)
        critical = (
            ".claude/settings.json",
            ".xtemplates/scripts/xt.py",
            ".xtemplates/manifest.json",
            "PROJECT.md",
            "BLUEPRINT.md",
            "docs/autopilot/STAGE.json",
        )
        tracked = self.git("ls-tree", "-r", "--name-only", "HEAD").stdout.splitlines()
        self.assertTrue(set(critical).issubset(tracked), tracked)
        bundle = self.tmp / "project.bundle"
        self.assertEqual(self.git("bundle", "create", str(bundle), "--all").returncode, 0)
        clone = self.tmp / "bundle-copy"
        env = dict(os.environ, GIT_ALLOW_PROTOCOL="file")
        copied = subprocess.run(
            ["git", "clone", "--template=", str(bundle), str(clone)],
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(copied.returncode, 0, copied.stderr)
        for rel in critical:
            self.assertEqual((clone / rel).read_bytes(), (self.target / rel).read_bytes(), rel)

    def test_global_monitor_signing_and_command_overrides_never_run(self) -> None:
        marker = self.tmp / "ambient-command-ran"
        command = self.tmp / "ambient-command"
        command.write_text(f'#!/bin/sh\nprintf executed > "{marker}"\nexit 71\n', encoding="utf-8")
        command.chmod(0o755)
        hostile = self.tmp / "hostile-global"
        hostile.write_text(
            f"[user]\n name = Trusted Owner\n email = trusted@example.test\n"
            f"[core]\n fsmonitor = {command}\n hooksPath = {command}\n"
            f"[gpg]\n program = {command}\n[commit]\n gpgSign = true\n[init]\n templateDir = {command}\n",
            encoding="utf-8",
        )
        before = hostile.read_bytes()
        inherited = {
            "GIT_CONFIG_GLOBAL": str(hostile),
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_KEY_0": "commit.gpgSign",
            "GIT_CONFIG_VALUE_0": "true",
            "GIT_DIR": str(self.tmp / "decoy/.git"),
        }
        with mock.patch.dict(os.environ, inherited):
            environment = dict(os.environ)
            code, output = self.run_new()
            self.assertEqual(dict(os.environ), environment)
        self.assert_created(code, output)
        self.assertFalse(marker.exists())
        self.assertEqual(hostile.read_bytes(), before)
        self.assertEqual(
            self.git("log", "-1", "--format=%an <%ae>").stdout.strip(), "Trusted Owner <trusted@example.test>"
        )

    def test_system_config_is_metadata_only_with_global_identity_precedence(self) -> None:
        marker = self.tmp / "system-command-ran"
        command = self.tmp / "system-command"
        command.write_text(f'#!/bin/sh\nprintf executed > "{marker}"\nexit 71\n', encoding="utf-8")
        command.chmod(0o755)
        excludes = self.tmp / "system-ignore"
        excludes.write_text("*\n", encoding="utf-8")
        system = self.tmp / "system-config"
        system.write_text(
            f"[user]\n name = System Owner\n email = system@example.test\n"
            f"[core]\n excludesFile = {excludes}\n fsmonitor = {command}\n"
            f"[commit]\n gpgSign = true\n[gpg]\n program = {command}\n",
            encoding="utf-8",
        )
        global_config = self.tmp / "global-identity"
        global_config.write_text("[user]\n email = global@example.test\n", encoding="utf-8")
        configuration = {
            "GIT_CONFIG_GLOBAL": str(global_config),
            "GIT_CONFIG_SYSTEM": str(system),
            "GIT_CONFIG_NOSYSTEM": "0",
        }
        with mock.patch.dict(os.environ, configuration):
            environment = dict(os.environ)
            code, output = self.run_new()
            self.assertEqual(dict(os.environ), environment)
        self.assert_created(code, output)
        self.assertFalse(marker.exists())
        self.assertEqual(self.git("config", "--local", "user.name").stdout.strip(), "System Owner")
        self.assertEqual(self.git("config", "--local", "user.email").stdout.strip(), "global@example.test")
        for key in ("core.excludesFile", "core.fsmonitor", "commit.gpgSign", "gpg.program"):
            self.assertEqual(self.git("config", "--local", "--get", key).returncode, 1, key)
        self.assertIn(".claude/settings.json", self.git("ls-tree", "-r", "--name-only", "HEAD").stdout.splitlines())

    def test_default_xdg_ignore_and_attributes_cannot_change_bootstrap_content(self) -> None:
        xdg = self.tmp / "xdg"
        (xdg / "git").mkdir(parents=True)
        (xdg / "git/ignore").write_text(".claude/\n.xtemplates/\nPROJECT.md\nBLUEPRINT.md\n", encoding="utf-8")
        (xdg / "git/attributes").write_text("PROJECT.md working-tree-encoding=UTF-16\n", encoding="utf-8")
        with mock.patch.dict(os.environ, {"XDG_CONFIG_HOME": str(xdg)}):
            code, output = self.run_new()
        self.assert_created(code, output)
        critical = (".claude/settings.json", ".xtemplates/scripts/xt.py", "PROJECT.md", "BLUEPRINT.md")
        for path in critical:
            recorded = self.git("show", f"HEAD:{path}")
            self.assertEqual(recorded.returncode, 0, recorded.stderr)
            self.assertEqual(recorded.stdout, (self.target / path).read_text(encoding="utf-8"), path)

    def test_identity_reader_rejects_control_metadata_and_restores_environment_on_failure(self) -> None:
        for key, value in (("user.name", ""), ("user.name", "one\ntwo"), ("user.email", "x y@example.test")):
            with self.subTest(key=key, value=value):
                self.assertFalse(install.new_identity_value(key, value))
        inherited = dict(os.environ)
        with mock.patch.object(install.subprocess, "run", side_effect=OSError("git unavailable")):
            with install.new_project_environment() as identity:
                self.assertEqual(identity, {})
                self.assertEqual(os.environ["GIT_CONFIG_GLOBAL"], os.devnull)
                self.assertEqual(os.environ["GIT_CONFIG_SYSTEM"], os.devnull)
                self.assertEqual(os.environ["GIT_CONFIG_NOSYSTEM"], "1")
        self.assertEqual(dict(os.environ), inherited)

    def test_non_utf8_global_identity_falls_back_without_dumping_bytes(self) -> None:
        original = b"[user]\n name = Ren\xe9\n email = owner@example.test\n"
        self.global_config.write_bytes(original)
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/install.py"),
                str(self.target),
                "--new",
                "--pack",
                "web-api-ts",
                "--idea",
                "notes",
            ],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assert_created(result.returncode, result.stdout + result.stderr)
        self.assertEqual(self.git("config", "--local", "--get", "user.name").stdout.strip(), "Project bootstrap")
        self.assertEqual(self.git("config", "--local", "--get", "user.email").stdout.strip(), "owner@example.test")
        self.assertNotIn("UnicodeDecodeError", result.stderr)
        self.assertNotIn("\\xe9", result.stdout + result.stderr)
        self.assertEqual(self.global_config.read_bytes(), original)

    def test_missing_target_loses_exclusive_mkdir_without_adopting_racer(self) -> None:
        mkdir = Path.mkdir
        created: list[int] = []

        def race(path: Path, *args: object, **kwargs: object) -> None:
            mkdir(path, *args, **kwargs)
            if path == self.target.parent and not created:
                mkdir(self.target)
                created.append(self.target.stat().st_ino)

        with mock.patch.object(Path, "mkdir", race):
            code, _ = self.run_new()
        self.assertEqual(code, 2)
        self.assertTrue(created)
        self.assertEqual(self.target.stat().st_ino, created[0])
        self.assertEqual(list(self.target.iterdir()), [])

    def test_missing_target_appearing_during_validation_is_not_adopted(self) -> None:
        validate = install.new_target_error
        created: list[int] = []

        def race(path: Path) -> str | None:
            error = validate(path)
            if path == self.target and not created:
                path.mkdir()
                created.append(path.stat().st_ino)
            return error

        with (
            mock.patch.object(install, "new_target_error", side_effect=race),
            mock.patch.object(install, "new_bootstrap") as bootstrap,
        ):
            code, output = self.run_new()
        self.assertEqual(code, 2, output)
        bootstrap.assert_not_called()
        self.assertEqual(self.target.stat().st_ino, created[0])
        self.assertEqual(list(self.target.iterdir()), [])

    def test_missing_target_claim_precedes_real_bootstrap_and_preserves_held_inode(self) -> None:
        bootstrap = install.new_bootstrap
        held: list[int] = []
        claimed_before_bootstrap: list[bool] = []

        def race(*args: object, **kwargs: object) -> int:
            try:
                self.target.mkdir()
                claimed_before_bootstrap.append(False)
            except FileExistsError:
                claimed_before_bootstrap.append(True)
            held.append(os.open(self.target, os.O_RDONLY))
            return bootstrap(*args, **kwargs)

        try:
            with mock.patch.object(install, "new_bootstrap", side_effect=race):
                code, output = self.run_new()
            self.assertEqual(code, 0, output)
            self.assertEqual(claimed_before_bootstrap, [True])
            self.assertEqual(os.fstat(held[0]).st_ino, self.target.stat().st_ino)
            self.assertTrue((self.target / "PROJECT.md").is_file())
        finally:
            for descriptor in held:
                os.close(descriptor)

    def test_default_name_uses_normalized_destination_for_dot(self) -> None:
        self.target.mkdir()
        original = Path.cwd()
        try:
            os.chdir(self.target)
            code, output = self.run_new_for_dot()
        finally:
            os.chdir(original)
        self.assert_created(code, output)
        self.assertIn("# PROJECT.md — notes", (self.target / "PROJECT.md").read_text(encoding="utf-8"))

    def run_new_for_dot(self) -> tuple[int, str]:
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = install.main([".", "--new", "--pack", "web-api-ts", "--idea", "notes"])
        return code, out.getvalue() + err.getvalue()

    def test_existing_caller_shell_sees_project_through_relative_paths(self) -> None:
        self.target.mkdir()
        inode = self.target.stat().st_ino
        script = """cd -- "$1" || exit 2
"$2" "$3" . --new --pack web-api-ts --idea notes || exit $?
test -f PROJECT.md && test -d .git
"""
        result = subprocess.run(
            ["bash", "-c", script, "_", str(self.target), sys.executable, str(ROOT / "scripts/install.py")],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.target.stat().st_ino, inode)
        self.assert_created(0, "")

    def test_existing_empty_target_claim_has_one_winner_and_preserves_inode(self) -> None:
        self.target.mkdir()
        inode = self.target.stat().st_ino
        command = [
            sys.executable,
            str(ROOT / "scripts/install.py"),
            str(self.target),
            "--new",
            "--pack",
            "web-api-ts",
            "--idea",
            "notes",
        ]
        processes = [
            subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for _ in range(2)
        ]
        output = [process.communicate(timeout=120) for process in processes]
        self.assertEqual(sorted(process.returncode for process in processes), [0, 2], output)
        self.assertEqual(self.target.stat().st_ino, inode)
        self.assert_created(0, "")

    def test_existing_target_failure_preserves_partial_and_concurrent_output(self) -> None:
        self.target.mkdir()
        inode = self.target.stat().st_ino
        original = install.install_git_hooks

        def fail(target: Path) -> None:
            original(target)
            (target / "concurrent-data").write_text("keep", encoding="utf-8")
            raise OSError("injected failure")

        with mock.patch.object(install, "install_git_hooks", side_effect=fail):
            code, output = self.run_new()
        self.assertEqual(code, 2, output)
        self.assertEqual(self.target.stat().st_ino, inode)
        self.assertTrue((self.target / ".git").is_dir())
        self.assertEqual((self.target / "concurrent-data").read_text(encoding="utf-8"), "keep")
        self.assertIn("giữ", output.lower())

    def test_existing_target_replacement_symlink_cannot_receive_bootstrap_writes(self) -> None:
        outside = self.tmp / "outside"
        outside.mkdir()
        original = install.new_project_document
        for kind in ("symlink", "directory"):
            with self.subTest(kind=kind):
                self.target.mkdir()
                moved = self.tmp / ("owned-moved-" + kind)

                def replace(target: Path, name: str, idea: str) -> None:
                    self.target.rename(moved)
                    if kind == "symlink":
                        self.target.symlink_to(outside, target_is_directory=True)
                    else:
                        self.target.mkdir()
                    original(target, name, idea)

                with mock.patch.object(install, "new_project_document", side_effect=replace):
                    code, output = self.run_new()
                self.assertEqual(code, 2, output)
                self.assertEqual(list(outside.iterdir()), [])
                self.assertTrue((moved / ".git").is_dir())
                self.assertTrue((moved / "PROJECT.md").is_file())
                self.assertIn("giữ", output.lower())
                if kind == "symlink":
                    self.assertTrue(self.target.is_symlink())
                    self.target.unlink()
                else:
                    self.assertEqual(list(self.target.iterdir()), [])
                    self.target.rmdir()

    def test_existing_target_nonzero_result_keeps_claim_and_restores_context(self) -> None:
        self.target.mkdir()
        directory, environment = Path.cwd(), dict(os.environ)
        with mock.patch.object(install, "new_bootstrap", return_value=1):
            code, output = self.run_new()
        self.assertEqual(code, 1, output)
        self.assertEqual(Path.cwd(), directory)
        self.assertEqual(dict(os.environ), environment)
        self.assertTrue((self.target / ".git").is_dir())
        self.assertIn("giữ", output.lower())

    def test_existing_target_occupied_before_claim_preserves_concurrent_file(self) -> None:
        self.target.mkdir()
        original = install.new_current_directory

        @contextmanager
        def occupied(destination: Path):
            with original(destination):
                Path("concurrent-data").write_text("keep", encoding="utf-8")
                yield

        with mock.patch.object(install, "new_current_directory", occupied):
            code, output = self.run_new()
        self.assertEqual(code, 2, output)
        self.assertEqual((self.target / "concurrent-data").read_text(encoding="utf-8"), "keep")
        self.assertFalse((self.target / ".git").exists())

    def test_existing_root_replaced_before_claim_preserves_replacement_data(self) -> None:
        self.target.mkdir()
        moved = self.tmp / "before-claim-moved"
        enter = install.new_current_directory

        @contextmanager
        def replace(destination: Path):
            destination.rename(moved)
            destination.mkdir()
            (destination / "user-data").write_text("keep", encoding="utf-8")
            with enter(destination):
                yield

        with (
            mock.patch.object(install, "new_current_directory", replace),
            mock.patch.object(install, "new_bootstrap") as bootstrap,
        ):
            code, output = self.run_new()
        self.assertEqual(code, 2, output)
        bootstrap.assert_not_called()
        self.assertEqual((self.target / "user-data").read_text(encoding="utf-8"), "keep")
        self.assertFalse((self.target / ".git").exists())
        self.assertEqual(list(moved.iterdir()), [])

    @unittest.skipUnless(hasattr(os, "fchdir"), "kernel POSIX cho phép giữ cwd của thư mục đã mất liên kết")
    def test_external_removal_of_empty_owned_root_still_reports_failure_and_restores_cwd(self) -> None:
        self.target.mkdir()
        previous = Path.cwd()

        def removed(*args: object, **kwargs: object) -> int:
            Path(".git").rmdir()
            self.target.rmdir()
            return 1

        with mock.patch.object(install, "new_bootstrap", side_effect=removed):
            code, output = self.run_new()
        self.assertEqual(code, 1, output)
        self.assertEqual(Path.cwd(), previous)
        self.assertIn(str(self.target), output)
        self.assertIn("giữ", output.lower())

    def test_cwd_restore_without_fchdir_support(self) -> None:
        self.target.mkdir()
        original = Path.cwd()
        with mock.patch.object(os, "fchdir"):
            del os.fchdir
            with install.new_current_directory(self.target):
                self.assertEqual(Path.cwd(), self.target)
            self.assertEqual(Path.cwd(), original)

    def test_template_hooks_and_inherited_git_location_cannot_escape_new_repo(self) -> None:
        template = self.tmp / "template"
        (template / "hooks").mkdir(parents=True)
        marker = self.tmp / "template-executed"
        hook = template / "hooks/pre-commit"
        hook.write_text(f'#!/bin/sh\ntouch "{marker}"\nexit 72\n', encoding="utf-8")
        hook.chmod(0o755)
        decoy = self.tmp / "decoy"
        decoy.mkdir()
        subprocess.run(["git", "init", "--initial-branch=main", str(decoy)], capture_output=True, check=True)
        before = {p.relative_to(decoy): p.read_bytes() for p in decoy.rglob("*") if p.is_file()}
        self.global_config.write_text(f"[init]\n templateDir = {template}\n", encoding="utf-8")
        inherited = {"GIT_DIR": str(decoy / ".git"), "GIT_WORK_TREE": str(decoy), "GIT_TEMPLATE_DIR": str(template)}
        with mock.patch.dict(os.environ, inherited):
            code, output = self.run_new()
            self.assertEqual({key: os.environ[key] for key in inherited}, inherited)
        self.assert_created(code, output)
        self.assertFalse(marker.exists())
        self.assertEqual(before, {p.relative_to(decoy): p.read_bytes() for p in decoy.rglob("*") if p.is_file()})

    def test_missing_target_claim_race_preserves_content_and_symlink(self) -> None:
        # D-460 thay publication bằng mkdir độc quyền trước bootstrap; dữ liệu của bên thắng luôn phải giữ nguyên.
        mkdir = Path.mkdir
        outside = self.tmp / "outside"
        outside.mkdir()
        for kind in ("content", "symlink"):
            with self.subTest(kind=kind):

                def race(path: Path, *args: object, **kwargs: object) -> None:
                    if path == self.target:
                        if kind == "symlink":
                            self.target.symlink_to(outside, target_is_directory=True)
                        else:
                            mkdir(self.target)
                            (self.target / "winner.txt").write_text("keep", encoding="utf-8")
                    mkdir(path, *args, **kwargs)

                with mock.patch.object(Path, "mkdir", race), mock.patch.object(install, "new_bootstrap") as bootstrap:
                    code, output = self.run_new()
                self.assertEqual(code, 2, output)
                bootstrap.assert_not_called()
                if kind == "symlink":
                    self.assertTrue(self.target.is_symlink())
                    self.assertEqual(list(outside.iterdir()), [])
                    self.target.unlink()
                else:
                    self.assertEqual((self.target / "winner.txt").read_text(encoding="utf-8"), "keep")
                    (self.target / "winner.txt").unlink()
                    self.target.rmdir()
                self.assertEqual(list(self.tmp.glob(".notes.xt-new-*")), [])

    def test_two_real_new_processes_publish_exactly_one_project(self) -> None:
        command = [
            sys.executable,
            str(ROOT / "scripts/install.py"),
            str(self.target),
            "--new",
            "--pack",
            "web-api-ts",
            "--idea",
            "notes",
        ]
        processes = [
            subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for _ in range(2)
        ]
        output = [process.communicate(timeout=120) for process in processes]
        self.assertEqual(sorted(process.returncode for process in processes), [0, 2], output)
        self.assert_created(0, "")
        self.assertEqual(list(self.tmp.glob(".notes.xt-new-*")), [])

    def test_missing_target_mkdir_race_preserves_held_empty_directory_inode(self) -> None:
        # Không rename đè ngay cả thư mục còn rỗng: một caller có thể đã giữ cwd/fd của inode này (D-460).
        mkdir = Path.mkdir
        held: list[int] = []

        def race(path: Path, *args: object, **kwargs: object) -> None:
            if path == self.target:
                mkdir(path)
                held.append(os.open(path, os.O_RDONLY))
            mkdir(path, *args, **kwargs)

        try:
            with mock.patch.object(Path, "mkdir", race), mock.patch.object(install, "new_bootstrap") as bootstrap:
                code, output = self.run_new()
            self.assertEqual(code, 2, output)
            bootstrap.assert_not_called()
            self.assertTrue(held)
            self.assertEqual(os.fstat(held[0]).st_ino, self.target.stat().st_ino)
            self.assertEqual(list(self.target.iterdir()), [])
        finally:
            for descriptor in held:
                os.close(descriptor)

    def test_doctor_failure_is_reported_and_partial_repository_preserved(self) -> None:
        original = install.install_git_hooks

        def broken_hook(target: Path) -> None:
            original(target)
            (target / ".claude/hooks/pre-edit-guard.sh").write_text("if (\n", encoding="utf-8")

        with mock.patch.object(install, "install_git_hooks", side_effect=broken_hook):
            code, output = self.run_new()
        self.assertEqual(code, 1, output)
        self.assertIn("pre-edit-guard.sh", output)
        self.assertIn("✗", output)
        self.assertTrue((self.target / ".git").is_dir())
        self.assertIn("giữ", output.lower())

    def test_missing_target_bootstrap_failures_preserve_claim_without_cleanup(self) -> None:
        # D-460 công bố thư mục bằng mkdir trước bootstrap; lỗi phải giữ output dở, không còn hợp đồng dọn staging.
        for result in (1, 2):
            self.target = self.tmp / f"notes-{result}"
            with self.subTest(result=result), mock.patch.object(install, "new_bootstrap", return_value=result):
                code, output = self.run_new()
                self.assertEqual(code, result, output)
                self.assertTrue((self.target / ".git").is_dir())
                self.assertIn("giữ", output.lower())
                self.assertEqual(list(self.tmp.glob(".notes.xt-new-*")), [])

    def test_pack_requires_a_profile_before_writing(self) -> None:
        pack = install.load_pack("web-api-ts")
        pack["profiles"] = []
        with mock.patch.object(install, "load_pack", return_value=pack):
            self.assertEqual(self.run_new()[0], 2)
        self.assertFalse(self.target.exists())

    def test_invalid_default_directory_slug_is_rejected_before_creation(self) -> None:
        self.target = self.tmp / "not a slug"
        code, output = self.run_new()
        self.assertEqual(code, 2, output)
        self.assertIn("--name", output)
        self.assertFalse(self.target.exists())

    def test_missing_ancestors_are_created_and_parent_files_are_preserved(self) -> None:
        self.target = self.tmp / "missing-parent/nested/notes"
        self.assert_created(*self.run_new())
        parent_file = self.tmp / "parent-file"
        parent_file.write_text("keep", encoding="utf-8")
        self.target = parent_file / "notes"
        self.assertEqual(self.run_new()[0], 2)
        self.assertEqual(parent_file.read_text(encoding="utf-8"), "keep")

    def test_parent_permission_error_and_bootstrap_failure_preserve_ancestors(self) -> None:
        self.target = self.tmp / "new-parent/notes"
        mkdir = Path.mkdir

        def denied(path: Path, *args: object, **kwargs: object) -> None:
            if path == self.target.parent:
                raise PermissionError("parent denied")
            mkdir(path, *args, **kwargs)

        with mock.patch.object(Path, "mkdir", denied):
            code, output = self.run_new()
        self.assertEqual(code, 2, output)
        self.assertIn("parent denied", output)
        self.assertFalse(self.target.parent.exists())
        with mock.patch.object(install, "new_bootstrap", return_value=1):
            self.assertEqual(self.run_new()[0], 1)
        self.assertTrue(self.target.parent.is_dir())
        self.assertTrue((self.target / ".git").is_dir())
        marker = self.target.parent / "concurrent"
        marker.write_text("keep", encoding="utf-8")
        self.target = self.target.parent / "more-notes"
        with mock.patch.object(install, "new_bootstrap", return_value=1):
            self.assertEqual(self.run_new()[0], 1)
        self.assertEqual(marker.read_text(encoding="utf-8"), "keep")

    def test_stage_init_failure_stops_bootstrap(self) -> None:
        self.target.mkdir()
        failure = subprocess.CompletedProcess([], 1, "", "stage denied")
        with (
            mock.patch.object(install, "install", return_value=0),
            mock.patch.object(install, "run_stage", return_value=failure),
            redirect_stderr(io.StringIO()) as output,
        ):
            code = install.new_bootstrap(self.target, install.load_pack("web-api-ts"), "notes", "idea", "S")
        self.assertEqual(code, 1)
        self.assertIn("stage denied", output.getvalue())

    def test_installer_failure_stops_bootstrap_before_stage_init(self) -> None:
        self.target.mkdir()
        with (
            mock.patch.object(install, "install", return_value=2),
            mock.patch.object(install, "run_stage") as stage,
            redirect_stderr(io.StringIO()),
        ):
            code = install.new_bootstrap(self.target, install.load_pack("web-api-ts"), "notes", "idea", "S")
        self.assertEqual(code, 2)
        stage.assert_not_called()

    def test_missing_pack_idea_and_unsupported_combination_are_usage_errors(self) -> None:
        cases = [
            ["--new", "--idea", "idea"],
            ["--new", "--pack", "web-api-ts"],
            ["--idea", "idea"],
            ["--new", "--pack", "web-api-ts", "--idea", "idea", "--no-git-hooks"],
            ["--new", "--pack", "web-api-ts", "--idea", "idea", "--plan"],
        ]
        for args in cases:
            with self.subTest(args=args), redirect_stderr(io.StringIO()), redirect_stdout(io.StringIO()):
                try:
                    code = install.main([str(self.target), *args])
                except SystemExit as exc:
                    code = int(exc.code)
                self.assertEqual(code, 2)
                self.assertFalse(self.target.exists())


class DoctorOfflineTest(unittest.TestCase):
    def test_offline_skips_network_and_keeps_local_deep_findings(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            failure = xt.Finding("framework", "error", "local failure")
            with (
                mock.patch.object(xt, "_doctor_version", side_effect=AssertionError("network probe")) as network,
                mock.patch.object(xt, "_doctor_framework", return_value=[failure]) as framework,
                mock.patch.object(xt, "_doctor_guard_canary", return_value=[]) as guard,
                mock.patch.object(xt, "_doctor_settings", return_value=[]) as settings,
            ):
                findings = xt.doctor_findings(base, ROOT / "framework", offline=True)
            self.assertIn(failure, findings)
            network.assert_not_called()
            framework.assert_called_once_with(ROOT / "framework")
            guard.assert_called_once_with(base)
            settings.assert_called_once_with(base, True)

    def test_default_doctor_keeps_version_probe(self) -> None:
        with (
            tempfile.TemporaryDirectory() as temporary,
            mock.patch.object(xt, "_doctor_version", return_value=[]) as network,
        ):
            xt.doctor_findings(Path(temporary), ROOT / "framework")
            network.assert_called_once()

    def test_offline_cli_propagates_to_fix_and_rejects_drift(self) -> None:
        with (
            mock.patch.object(xt, "doctor_findings", return_value=[]) as findings,
            mock.patch.object(xt, "doctor_fix", return_value=([], [])),
            redirect_stdout(io.StringIO()),
            redirect_stderr(io.StringIO()),
        ):
            self.assertEqual(xt.main(["doctor", "--offline", "--fix", "--json"]), 0)
            self.assertEqual(findings.call_count, 2)
            self.assertTrue(all(call.kwargs["offline"] for call in findings.call_args_list))
            self.assertEqual(xt.main(["doctor", "--offline", "--drift"]), 2)
            self.assertEqual(findings.call_count, 2)


if __name__ == "__main__":
    unittest.main()
