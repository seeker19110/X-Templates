"""Test scripts/install.py và scripts/check-links.py."""

from __future__ import annotations

import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
import unittest.mock as mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import install
import xt


def stored(data: bytes) -> str:
    """Hash của `data` đúng dạng install.py ghi vào manifest: `sha256:<hex>` (T-1743)."""
    return install.hash_label(install.sha256(data))


class InstallTest(unittest.TestCase):
    def setUp(self):
        self.target = Path(self.enterContext(tempfile.TemporaryDirectory()))

    def run_install(self, *extra) -> int:
        return install.main([str(self.target), "--label", "test", *extra])

    def test_fresh_install_layout(self):
        self.assertEqual(self.run_install(), 0)
        self.assertTrue((self.target / ".xtemplates" / "framework" / "00-method" / "conventions.md").exists())
        self.assertTrue((self.target / ".xtemplates" / "scripts" / "xt.py").exists())
        self.assertEqual((self.target / ".xtemplates" / "VERSION").read_text(encoding="utf-8").strip(), "test")
        self.assertTrue((self.target / ".claude" / "settings.json").exists())
        self.assertTrue((self.target / ".claude" / "hooks" / "stop-guard.sh").exists())
        self.assertTrue((self.target / ".claude" / "skills" / "autopilot" / "SKILL.md").exists())
        self.assertIn(".autopilot/", (self.target / ".gitignore").read_text(encoding="utf-8"))
        for name in ("AGENTS.md", "CLAUDE.md", "PROGRESS.md", "xt.yaml"):
            self.assertTrue((self.target / name).exists(), name)
            self.assertFalse(
                (self.target / name).read_text(encoding="utf-8").startswith("---"), f"{name} còn frontmatter"
            )

    def test_installed_progress_is_body_of_template(self):
        # Mẫu PROGRESS bọc 4 mục trong ```markdown — dự án đích phải nhận đúng 4 mục, không phải trang hướng dẫn.
        self.run_install()
        text = (self.target / "PROGRESS.md").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("# PROGRESS.md"), text[:80])
        self.assertEqual(tuple(n for n, _ in xt.progress_sections(text)), xt.PROGRESS_SECTIONS)

    def test_progress_gets_head_sha_in_git_repo(self):  # AUD-HAR-053
        subprocess.run(["git", "init", "-q", str(self.target)], check=True)
        (self.target / "a.txt").write_text("a\n", encoding="utf-8")
        git = ["git", "-C", str(self.target), "-c", "user.name=t", "-c", "user.email=t@t"]
        subprocess.run([*git, "add", "a.txt"], check=True)
        subprocess.run([*git, "commit", "-qm", "init"], check=True)
        head = subprocess.run([*git, "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
        self.run_install()
        text = (self.target / "PROGRESS.md").read_text(encoding="utf-8")
        self.assertIn(f"`{head}`", text)
        self.assertNotIn("<SHA đầy đủ>", text)
        # nhánh PR / dự án lồng trong repo cha: không ghi HEAD (review #97)
        sub = self.target / "apps" / "web"
        sub.mkdir(parents=True)
        self.assertEqual(install.progress_with_head("`<SHA đầy đủ>`", sub), "`<SHA đầy đủ>`")
        subprocess.run([*git, "checkout", "-qb", "feat"], check=True)
        self.assertEqual(install.progress_with_head("`<SHA đầy đủ>`", self.target), "`<SHA đầy đủ>`")

    def test_progress_keeps_placeholder_without_commits(self):
        self.run_install()
        self.assertIn("<SHA đầy đủ>", (self.target / "PROGRESS.md").read_text(encoding="utf-8"))
        for exc in (OSError("không có git"), subprocess.TimeoutExpired("git", 10)):
            with mock.patch.object(install.subprocess, "run", side_effect=exc):
                self.assertEqual(install.progress_with_head("`<SHA đầy đủ>`", self.target), "`<SHA đầy đủ>`")

    def test_dev_task_root_in_target_project(self):
        # AUD-HAR-001: thiếu CLAUDE_PROJECT_DIR, .xtemplates/scripts/dev-task.sh từng lấy gốc = .xtemplates/ → "xanh giả".
        self.run_install()
        (self.target / "xt.yaml").write_text('build: ""\ntypecheck: ""\nlint: ""\ntest: "false"\n', encoding="utf-8")
        env = {k: v for k, v in os.environ.items() if k != "CLAUDE_PROJECT_DIR"}
        script = self.target / ".xtemplates" / "scripts" / "dev-task.sh"
        r = subprocess.run(["bash", str(script), "gate"], capture_output=True, text=True, env=env, cwd="/")
        self.assertNotEqual(r.returncode, 0, r.stderr)
        self.assertIn("GATE ĐỎ ở 'test'", r.stderr)
        (self.target / "xt.yaml").write_text('test: "true"\n', encoding="utf-8")
        r = subprocess.run(["bash", str(script), "gate"], capture_output=True, text=True, env=env, cwd="/")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("GATE XANH (1 lệnh)", r.stderr)

    def test_dev_task_noop_is_not_reported_green(self):
        self.run_install()
        (self.target / "xt.yaml").write_text('build: ""\ntypecheck: ""\nlint: ""\ntest: ""\n', encoding="utf-8")
        env = {k: v for k, v in os.environ.items() if k != "CLAUDE_PROJECT_DIR"}
        r = subprocess.run(
            ["bash", str(self.target / ".xtemplates/scripts/dev-task.sh"), "gate"],
            capture_output=True,
            text=True,
            env=env,
        )
        self.assertEqual(r.returncode, 0)
        self.assertIn("KHÔNG CHẠY LỆNH NÀO", r.stderr)
        self.assertNotIn("GATE XANH", r.stderr)

    def test_check_links_fence_angle_and_outside_root(self):
        # AUD-DOC-019: ~~~ fence, link <có dấu cách>, link ra ngoài gốc repo.
        repo = Path(self.enterContext(tempfile.TemporaryDirectory()))
        outside = repo.parent / (repo.name + "-ngoai.md")
        outside.write_text("x", encoding="utf-8")
        self.addCleanup(outside.unlink)
        (repo / "có dấu cách.md").write_text("x", encoding="utf-8")
        (repo / "a.md").write_text(
            "~~~\n[x](khong-co.md)\n~~~\n[ok](<có dấu cách.md>)\n[hỏng](<không có.md>)\n[ngoài](../"
            + outside.name
            + ")\n",
            encoding="utf-8",
        )
        r = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "check-links.py"), str(repo)], capture_output=True, text=True
        )
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertNotIn("khong-co.md", r.stdout)
        self.assertIn("không có.md", r.stdout)
        self.assertIn("ra ngoài repo", r.stdout)
        self.assertEqual(r.stdout.count("✗"), 2)

    def test_installed_check_links_uses_project_root(self):
        self.run_install()
        (self.target / "doc.md").write_text("[hỏng](khong-co.md)\n", encoding="utf-8")
        r = subprocess.run(
            [sys.executable, str(self.target / ".xtemplates/scripts/check-links.py")], capture_output=True, text=True
        )
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("doc.md:1", r.stdout)

    def test_installed_xt_validates_and_composes(self):
        self.run_install()
        xt = self.target / ".xtemplates" / "scripts" / "xt.py"
        r = subprocess.run([sys.executable, str(xt), "validate"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout)
        r = subprocess.run(
            [
                sys.executable,
                str(xt),
                "compose",
                "--profile",
                "web-app",
                "--scale",
                "M",
                "--out",
                str(self.target / "BLUEPRINT.md"),
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("kind: blueprint", (self.target / "BLUEPRINT.md").read_text(encoding="utf-8"))

    def test_does_not_overwrite_user_files(self):
        self.run_install()
        agents = self.target / "AGENTS.md"
        agents.write_text("của tôi\n", encoding="utf-8")
        hook = self.target / ".claude" / "hooks" / "stop-guard.sh"
        hook.write_text("# hook tôi đã sửa\n", encoding="utf-8")
        self.run_install()
        self.assertEqual(agents.read_text(encoding="utf-8"), "của tôi\n")
        self.assertEqual(hook.read_text(encoding="utf-8"), "# hook tôi đã sửa\n")
        # T-1732: mẫu không đổi từ lần cài trước → `kept-own`, không có gì mới để gộp nên không ghi `.xtemplates-new`
        # (trường hợp mẫu đổi: InstallUpgradeTest)
        self.assertFalse(hook.with_name("stop-guard.sh.xtemplates-new").exists())
        self.assertFalse(agents.with_name("AGENTS.md.xtemplates-new").exists())
        self.run_install("--force-harness")
        self.assertNotEqual(hook.read_text(encoding="utf-8"), "# hook tôi đã sửa\n")
        self.assertEqual(agents.read_text(encoding="utf-8"), "của tôi\n")  # --force-harness không đụng file gốc

    def test_install_merges_hooks_into_existing_settings(self):
        # AUD-HAR-003: settings.json có sẵn từng chỉ sinh .xtemplates-new → hook copy mà không chạy.
        settings = self.target / ".claude" / "settings.json"
        settings.parent.mkdir(parents=True)
        perms = {"allow": ["Bash(make *)"], "ask": ["Bash(git merge *)", "Bash(make deploy*)"], "deny": ["Bash(rm *)"]}
        settings.write_text(json.dumps({"permissions": perms}), encoding="utf-8")
        # REC-09: chỉ gỡ ask khi manifest.json chứng minh khung đã đặt — ở đây khung từng đặt `git merge`.
        (self.target / ".xtemplates").mkdir()
        (self.target / ".xtemplates" / "manifest.json").write_text(
            json.dumps({"rules": {"ask": ["Bash(git merge *)"]}}), encoding="utf-8"
        )
        self.run_install()
        d = json.loads(settings.read_text(encoding="utf-8"))
        # ADR-0018: thêm `Bash` + deny của khung, gỡ ask do khung đặt; quyền riêng của dự án giữ.
        ours = json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))["permissions"]
        self.assertEqual(d["permissions"]["allow"], ["Bash(make *)", "Bash"])
        self.assertEqual(d["permissions"]["ask"], ["Bash(make deploy*)"])
        self.assertEqual(d["permissions"]["deny"], ["Bash(rm *)", *ours["deny"]])
        self.assertIn("PreToolUse", d["hooks"])
        before = settings.read_text(encoding="utf-8")
        self.run_install()  # chạy lại: không nhân đôi hook
        self.assertEqual(settings.read_text(encoding="utf-8"), before)

    def test_install_updates_pristine_harness(self):
        # AUD-HAR-004: hook đã cài mà người dùng chưa sửa phải được cập nhật khi khung có bản mới.
        self.run_install()
        hook = self.target / ".claude" / "hooks" / "stop-guard.sh"
        manifest = json.loads((self.target / ".xtemplates" / "harness.sha256.json").read_text(encoding="utf-8"))
        self.assertIn(".claude/hooks/stop-guard.sh", manifest)
        old = "# bản khung cũ\n"
        hook.write_text(old, encoding="utf-8")
        manifest[".claude/hooks/stop-guard.sh"] = install.sha256(old.encode())  # giả lập: lần cài trước là bản cũ
        (self.target / ".xtemplates" / "harness.sha256.json").write_text(json.dumps(manifest), encoding="utf-8")
        self.run_install()
        self.assertEqual(
            hook.read_text(encoding="utf-8"), (ROOT / ".claude/hooks/stop-guard.sh").read_text(encoding="utf-8")
        )
        self.assertFalse(hook.with_name("stop-guard.sh.xtemplates-new").exists())

    def test_install_symlink_not_followed(self):
        # AUD-HAR-010: symlink treo ở đích không được đi theo ra ngoài dự án.
        outside = Path(self.enterContext(tempfile.TemporaryDirectory()))
        (self.target / "CLAUDE.md").symlink_to(outside / "pwn.md")
        self.run_install()
        self.assertFalse((outside / "pwn.md").exists())
        self.assertTrue((self.target / "CLAUDE.md").is_symlink())

    def test_with_github_ruleset_template_minimal_and_parallel(self):
        """D-116/D-117/D-122: ruleset mẫu chỉ đòi 2 check mà workflow mẫu cung cấp (không treo PR ngày đầu;
        `protection-guard` là job con của `quality`; `merge-gate` đã bỏ), không đòi "up to date" (PR merge song song); repo
        khung giữ ruleset riêng. Vẫn giữ cấm xoá, cấm force-push, PR bắt buộc."""
        err = io.StringIO()
        with redirect_stderr(err):
            self.assertEqual(self.run_install("--with-github"), 0)
        self.assertNotIn("required check chưa có job", err.getvalue())
        self.assertEqual(install.ruleset_required_checks(), ["quality", "gitleaks"])
        self.assertLessEqual(set(install.ruleset_required_checks()), install.provided_checks())
        rs = json.loads((self.target / ".github" / "rulesets" / "main.json").read_text(encoding="utf-8"))
        status = next(r for r in rs["rules"] if r["type"] == "required_status_checks")["parameters"]
        self.assertIs(status["strict_required_status_checks_policy"], False)
        self.assertEqual(rs["bypass_actors"], [])
        self.assertEqual([r["type"] for r in rs["rules"]][:3], ["deletion", "non_fast_forward", "pull_request"])
        own = json.loads((ROOT / ".github" / "rulesets" / "main.json").read_text(encoding="utf-8"))
        self.assertNotEqual(own, rs)

    def test_with_github_warns_checks_without_job(self):
        """AUD-CI-003: ruleset mẫu đòi check không có job → cảnh báo nêu đúng tên đó."""
        ruleset = json.dumps(
            {
                "rules": [
                    {
                        "type": "required_status_checks",
                        "parameters": {"required_status_checks": [{"context": "merge-gate"}, {"context": "dep-audit"}]},
                    }
                ]
            }
        )
        src = make_fake_src(Path(self.enterContext(tempfile.TemporaryDirectory())), ruleset=ruleset)
        target = self.target / "dich"
        target.mkdir()
        err = io.StringIO()
        with mock.patch.object(install, "SRC", src), redirect_stderr(err):
            self.assertEqual(install.main([str(target), "--label", "t", "--with-github"]), 0)
        line = err.getvalue().split("required check chưa có job:")[1].split("\n")[0]
        self.assertEqual(line.split("—")[0].strip(), "merge-gate, dep-audit")  # khung giả: workflow không có job

    def test_with_github_copies_guardrails_without_overwrite(self):
        self.assertEqual(self.run_install(), 0)
        self.assertFalse((self.target / ".github").exists())
        self.assertEqual(self.run_install("--with-github"), 0)
        rs = self.target / ".github" / "rulesets" / "main.json"
        self.assertTrue(rs.exists())
        # Mẫu PR và Dependabot là bản cho dự án đích (khối ```markdown của mẫu, chỉ hệ github-actions), không phải bản của
        # repo khung (mục "module/hồ sơ/ngành", hệ pip cho requirements-dev.txt mà dự án đích không có).
        pr = (self.target / ".github" / "pull_request_template.md").read_text(encoding="utf-8")
        self.assertTrue(pr.startswith("<!-- Tiêu đề PR"), pr[:80])
        self.assertNotIn("```", pr)
        self.assertNotIn("xt.py validate", pr)
        dep = (self.target / ".github" / "dependabot.yml").read_text(encoding="utf-8")
        self.assertIn("package-ecosystem: github-actions", dep)
        self.assertNotIn("package-ecosystem: pip", dep)
        # D-122/ADR-0036: stub `merge-gate.yml` vẫn phát (đúng bản của khung) để giữ context cũ tới khi ruleset sống của
        # dự án đích gỡ — bản cũ gọi `xt.py merge-gate` đã gỡ thì làm đỏ mọi PR
        self.assertEqual(
            (self.target / ".github" / "workflows" / "merge-gate.yml").read_bytes(),
            (ROOT / ".github" / "workflows" / "merge-gate.yml").read_bytes(),
        )
        # ADR-0027: PR đủ tiêu chuẩn tự vào nhánh chính khi không còn phiên agent
        self.assertTrue((self.target / ".github" / "workflows" / "pr-steward.yml").exists())
        # CI song song + `quality` tổng hợp và quét bí mật là mẫu không phụ thuộc stack (bản cho dự án đích)
        for wf in ("ci.yml", "secret-scan.yml"):
            self.assertEqual(
                (self.target / ".github" / "workflows" / wf).read_bytes(),
                (ROOT / "framework" / "templates" / wf).read_bytes(),
            )
        rs.write_text("{}\n", encoding="utf-8")
        self.run_install("--with-github")
        self.assertEqual(rs.read_text(encoding="utf-8"), "{}\n")
        # T-1732: mẫu không đổi từ lần cài trước → `kept-own`, không `.xtemplates-new`; mẫu đổi (hash lần trước khác) → có
        self.assertFalse(rs.with_name("main.json.xtemplates-new").exists())
        mf = self.target / ".xtemplates" / "harness.sha256.json"
        legacy = json.loads(mf.read_text(encoding="utf-8"))
        legacy[".github/rulesets/main.json"] = install.sha256(b"ruleset khung cu\n")
        mf.write_text(json.dumps(legacy), encoding="utf-8")
        self.run_install("--with-github")
        self.assertEqual(rs.read_text(encoding="utf-8"), "{}\n")
        self.assertTrue(rs.with_name("main.json.xtemplates-new").exists())

    def manifests(self) -> tuple[dict, dict]:
        xt_dir = self.target / ".xtemplates"
        legacy = json.loads((xt_dir / "harness.sha256.json").read_text(encoding="utf-8"))
        return legacy, json.loads((xt_dir / "manifest.json").read_text(encoding="utf-8"))["files"]

    def test_with_github_keeps_project_ci_and_records_hashes(self):
        own = self.target / ".github" / "workflows" / "ci.yml"
        own.parent.mkdir(parents=True)
        own.write_text("name: CI riêng của dự án\n", encoding="utf-8")
        with redirect_stderr(io.StringIO()):
            self.assertEqual(self.run_install("--with-github"), 0)
        self.assertEqual(own.read_text(encoding="utf-8"), "name: CI riêng của dự án\n")  # không đè
        tmpl = ROOT / "framework" / "templates" / "ci.yml"
        self.assertEqual(own.with_name("ci.yml.xtemplates-new").read_bytes(), tmpl.read_bytes())
        for files in self.manifests():
            # D-114: file của dự án ra `.xtemplates-new` → ghi hash MẪU (không phải hash file dự án, nên không bao giờ
            # bị coi là "chưa sửa" mà đè)
            self.assertEqual(files[".github/workflows/ci.yml"], stored(tmpl.read_bytes()))
            for gh in (".github/workflows/secret-scan.yml", ".github/pull_request_template.md"):
                # hash = nội dung ĐÃ ghi (mẫu .md đã bỏ frontmatter) → `doctor --drift` so được với file thật
                self.assertEqual(files[gh], stored((self.target / gh).read_bytes()), gh)
        # Cài lại khi mẫu không đổi sau `updated-new` → `kept-own`: không ghi lại `.xtemplates-new`, không đè file dự án
        own.with_name("ci.yml.xtemplates-new").unlink()
        err = io.StringIO()
        with redirect_stderr(err):
            self.run_install("--with-github")
        self.assertIn(".github/workflows/ci.yml: kept-own", err.getvalue())
        self.assertFalse(own.with_name("ci.yml.xtemplates-new").exists())
        self.assertEqual(own.read_text(encoding="utf-8"), "name: CI riêng của dự án\n")
        # File khung chưa sửa (đúng hash lần cài trước) → cập nhật tại chỗ khi khung có bản mới
        scan = self.target / ".github" / "workflows" / "secret-scan.yml"
        scan.write_text("# bản khung cũ\n", encoding="utf-8")
        legacy, _ = self.manifests()
        legacy[".github/workflows/secret-scan.yml"] = install.sha256(scan.read_bytes())  # hex trần như manifest cũ
        (self.target / ".xtemplates" / "harness.sha256.json").write_text(json.dumps(legacy), encoding="utf-8")
        with redirect_stderr(io.StringIO()):
            self.run_install("--with-github")
        self.assertEqual(scan.read_bytes(), (ROOT / "framework" / "templates" / "secret-scan.yml").read_bytes())
        self.assertFalse(scan.with_name("secret-scan.yml.xtemplates-new").exists())
        # Cài lại không --with-github: hash `.github/` vẫn giữ trong manifest
        with redirect_stderr(io.StringIO()):
            self.run_install()
        for files in self.manifests():
            self.assertIn(".github/workflows/secret-scan.yml", files)

    def test_with_github_no_harness_creates_manifest(self):
        with redirect_stderr(io.StringIO()):
            self.assertEqual(self.run_install("--no-harness", "--with-github"), 0)
        self.assertFalse((self.target / ".claude").exists())
        legacy, files = self.manifests()
        self.assertEqual(legacy, files)
        # ngoài `.github/` chỉ có hash file gốc (T-1732), không file harness nào
        self.assertEqual({k for k in files if not k.startswith(".github/")}, set(install.ROOT_TEMPLATES))
        self.assertIn(".github/workflows/ci.yml", files)
        m = json.loads((self.target / ".xtemplates" / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(m["rules"], {"allow": [], "ask": [], "deny": []})

    def test_with_github_hash_only_when_target_is_framework_copy(self):
        """Hash khung vào manifest chỉ khi file đích đúng bằng bản khung: file có sẵn trùng bản khung (`kept`) → ghi;
        `kept` mà nội dung đích khác bản khung (file người dùng) → không ghi."""
        scan = self.target / ".github" / "workflows" / "secret-scan.yml"
        scan.parent.mkdir(parents=True)
        tmpl = (ROOT / "framework" / "templates" / "secret-scan.yml").read_bytes()
        scan.write_bytes(tmpl)  # dự án đã có đúng bản khung
        with redirect_stderr(io.StringIO()):
            self.assertEqual(self.run_install("--no-harness", "--with-github"), 0)
        _, files = self.manifests()
        self.assertEqual(files[".github/workflows/secret-scan.yml"], stored(tmpl))
        shutil.rmtree(self.target / ".xtemplates")
        scan.write_text("# CI quét bí mật của dự án\n", encoding="utf-8")
        real = install.copy_if_absent

        def kept_for_scan(src, dst, *a, **k):  # copy_if_absent trả `kept` cho file người dùng (khác bản khung)
            return "kept" if dst == scan else real(src, dst, *a, **k)

        with redirect_stderr(io.StringIO()), mock.patch.object(install, "copy_if_absent", side_effect=kept_for_scan):
            self.assertEqual(self.run_install("--no-harness", "--with-github"), 0)
        _, files = self.manifests()
        self.assertNotIn(".github/workflows/secret-scan.yml", files)
        self.assertIn(".github/workflows/ci.yml", files)
        self.assertEqual(scan.read_text(encoding="utf-8"), "# CI quét bí mật của dự án\n")

    def test_workflow_job_names(self):
        text = (
            "name: x\njobs:\n  a:\n    name: quality\n    runs-on: u\n\n  b-c:\n    runs-on: u\n  d:\n    name: 'g'\n"
        )
        self.assertEqual(install.workflow_job_names(text), {"quality", "b-c", "g"})
        self.assertEqual(install.workflow_job_names("name: merge-gate\n"), set())

    def test_refuses_self_and_missing(self):
        self.assertEqual(install.main([str(ROOT), "--label", "x"]), 2)
        self.assertEqual(install.main([str(self.target / "khong-co"), "--label", "x"]), 2)


class InstallAuditFixTest(unittest.TestCase):
    """Audit 2026-10-21: AUD-CI-012 (`--with-github` vào thư mục con của repo git ghi workflow GitHub không chạy) và
    AUD-CFG-003 (installer ghi xuyên symlink trong `.xtemplates/` và `.gitignore` ra file ngoài dự án)."""

    def setUp(self):
        self.tmp = Path(self.enterContext(tempfile.TemporaryDirectory())).resolve()
        self.outside = self.tmp / "outside"
        self.outside.mkdir()

    def quiet(self, *argv: str) -> tuple[int, str]:
        err = io.StringIO()
        with redirect_stderr(err), redirect_stdout(io.StringIO()):
            rc = install.main(list(argv))
        return rc, err.getvalue()

    def test_with_github_subdir_of_git_repo_refused(self):
        mono = self.tmp / "mono"
        web = mono / "apps" / "web"
        web.mkdir(parents=True)
        subprocess.run(["git", "init", "-q", str(mono)], check=True)
        for extra in ((), ("--plan",)):
            with self.subTest(extra=extra):
                rc, err = self.quiet(str(web), "--label", "t", "--with-github", *extra)
                self.assertEqual(rc, 2)
                self.assertIn("không phải gốc repo git", err)
                self.assertIn(str(mono / ".github"), err)
        self.assertFalse((web / ".github").exists())
        self.assertFalse((web / ".xtemplates").exists())  # từ chối trước khi ghi gì
        self.assertEqual(self.quiet(str(web), "--label", "t")[0], 0)  # không kèm --with-github: cài được
        self.assertEqual(self.quiet(str(mono), "--label", "t", "--with-github")[0], 0)  # ở gốc repo: như cũ
        self.assertTrue((mono / ".github" / "workflows" / "ci.yml").is_file())

    def test_with_github_outside_git_or_git_error_not_blocked(self):
        plain = self.tmp / "plain"
        plain.mkdir()
        env = mock.patch.dict(os.environ, {"GIT_CEILING_DIRECTORIES": str(self.tmp)})
        with env:
            self.assertIsNone(install.github_root_error(plain))
        with mock.patch.object(install.subprocess, "run", side_effect=OSError("git")):
            self.assertIsNone(install.github_root_error(plain))

    def test_symlink_in_xtemplates_not_followed(self):
        target = self.tmp / "proj"
        target.mkdir()
        self.assertEqual(self.quiet(str(target), "--label", "t")[0], 0)
        xt_dir = target / ".xtemplates"
        victims = {}
        for rel in ("VERSION", "README.md", "scripts/xt.py", "scripts/dev-task.sh"):
            victim = self.outside / rel.replace("/", "_")
            victim.write_text("ORIG", encoding="utf-8")
            (xt_dir / rel).unlink()
            (xt_dir / rel).symlink_to(victim)
            victims[rel] = victim
        rc, err = self.quiet(str(target), "--label", "t2")
        self.assertEqual(rc, 0)
        self.assertIn("là symlink — gỡ liên kết", err)
        for rel, victim in victims.items():
            with self.subTest(rel=rel):
                self.assertEqual(victim.read_text(encoding="utf-8"), "ORIG")  # file ngoài dự án không bị ghi
                self.assertFalse((xt_dir / rel).is_symlink())
        self.assertEqual((xt_dir / "VERSION").read_text(encoding="utf-8"), "t2\n")

    def test_symlink_dirs_and_gitignore_not_followed(self):
        target = self.tmp / "proj"
        target.mkdir()
        self.assertEqual(self.quiet(str(target), "--label", "t")[0], 0)
        xt_dir = target / ".xtemplates"
        shutil.rmtree(xt_dir / "scripts")
        (self.outside / "scripts").mkdir()
        (xt_dir / "scripts").symlink_to(self.outside / "scripts")
        shutil.rmtree(xt_dir / "framework")
        (self.outside / "fw").mkdir()
        (self.outside / "fw" / "keep.md").write_text("ORIG", encoding="utf-8")
        (xt_dir / "framework").symlink_to(self.outside / "fw")
        (target / ".gitignore").unlink()
        (self.outside / "gi").write_text("ORIG\n", encoding="utf-8")
        (target / ".gitignore").symlink_to(self.outside / "gi")
        rc, err = self.quiet(str(target), "--label", "t2")
        self.assertEqual(rc, 0, err)
        self.assertEqual(list((self.outside / "scripts").iterdir()), [])
        self.assertEqual((self.outside / "fw" / "keep.md").read_text(encoding="utf-8"), "ORIG")
        self.assertTrue((xt_dir / "framework" / "00-method").is_dir() and not (xt_dir / "framework").is_symlink())
        self.assertEqual((self.outside / "gi").read_text(encoding="utf-8"), "ORIG\n")
        self.assertIn("bỏ qua symlink", err)
        shutil.rmtree(xt_dir)
        (self.outside / "xt").mkdir()
        xt_dir.symlink_to(self.outside / "xt")
        rc, err = self.quiet(str(target), "--label", "t3")
        self.assertEqual(rc, 2)
        self.assertIn(".xtemplates là symlink", err)
        self.assertEqual(list((self.outside / "xt").iterdir()), [])


class LegacyMigrationTest(unittest.TestCase):
    """ADR-0007: dự án cài bản ≤ 2.x (`.xstored/`, `xs.yaml`) chạy lại install là sang tên mới."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.target = Path(tmp.name).resolve()

    def install_quiet(self) -> tuple[int, str]:
        err = io.StringIO()
        with redirect_stderr(err):
            code = install.main([str(self.target), "--label", "t"])
        return code, err.getvalue()

    def make_legacy_install(self) -> Path:
        """Cài bản hiện tại rồi đổi về bố cục 2.x; hook stop-guard giả lập bản cũ chưa sửa (hash khớp manifest)."""
        self.install_quiet()
        legacy = self.target / ".xstored"
        (self.target / ".xtemplates").rename(legacy)
        (self.target / "xt.yaml").rename(self.target / "xs.yaml")
        (self.target / "xs.yaml").write_text('test: "true"\n', encoding="utf-8")
        hook = self.target / ".claude" / "hooks" / "stop-guard.sh"
        old = 'XS="$(xs_py)" || exit 0  # .xstored/scripts/xs.py\n'
        hook.write_text(old, encoding="utf-8")
        manifest = json.loads((legacy / "harness.sha256.json").read_text(encoding="utf-8"))
        manifest[".claude/hooks/stop-guard.sh"] = install.sha256(old.encode())
        (legacy / "harness.sha256.json").write_text(json.dumps(manifest), encoding="utf-8")
        (self.target / "AGENTS.md").write_text("Chạy `python3 .xstored/scripts/xs.py list`.\n", encoding="utf-8")
        return hook

    def test_upgrade_moves_dir_yaml_and_updates_pristine_hook(self):
        hook = self.make_legacy_install()
        code, err = self.install_quiet()
        self.assertEqual(code, 0, err)
        self.assertFalse((self.target / ".xstored").exists())
        self.assertTrue((self.target / ".xtemplates" / "scripts" / "xt.py").is_file())
        self.assertFalse((self.target / "xs.yaml").exists())
        # dòng của dự án giữ nguyên; khoá mới của mẫu nối dạng chú thích (T-1732) nên khoá có hiệu lực không đổi
        yaml = (self.target / "xt.yaml").read_text(encoding="utf-8")
        self.assertTrue(yaml.startswith('test: "true"\n\n# Khoá mới của khung (bản t)'), yaml[:80])
        self.assertEqual(xt._yaml_keys(yaml), {"test": "true"})
        self.assertEqual(hook.read_text(encoding="utf-8"), (ROOT / ".claude/hooks/stop-guard.sh").read_text("utf-8"))
        self.assertIn(".xstored/ → .xtemplates/", err)
        self.assertIn("xs.yaml → xt.yaml", err)
        self.assertIn("còn nhắc tên cũ", err)
        self.assertIn("AGENTS.md", err)
        self.assertNotIn("stop-guard.sh", err.split("còn nhắc tên cũ")[1])

    def test_new_manifest_wins_and_legacy_dir_without_manifest_is_removed(self):
        self.install_quiet()
        manifest = (self.target / ".xtemplates" / "harness.sha256.json").read_text(encoding="utf-8")
        (self.target / ".xstored").mkdir()
        (self.target / ".xstored" / "harness.sha256.json").write_text("{}", encoding="utf-8")
        self.install_quiet()
        self.assertEqual((self.target / ".xtemplates" / "harness.sha256.json").read_text(encoding="utf-8"), manifest)
        (self.target / ".xstored").mkdir()
        code, err = self.install_quiet()
        self.assertEqual(code, 0)
        self.assertFalse((self.target / ".xstored").exists())
        self.assertNotIn("còn nhắc tên cũ", err)

    def test_both_yaml_files_are_kept_with_warning(self):
        self.install_quiet()
        (self.target / "xs.yaml").write_text("test: cu\n", encoding="utf-8")
        code, err = self.install_quiet()
        self.assertEqual(code, 0)
        self.assertEqual((self.target / "xs.yaml").read_text(encoding="utf-8"), "test: cu\n")
        self.assertIn("có cả xs.yaml và xt.yaml", err)

    def test_legacy_symlink_is_not_followed(self):
        outside = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, outside, ignore_errors=True)
        (outside / "giu.txt").write_text("x", encoding="utf-8")
        (self.target / ".xstored").symlink_to(outside)
        code, _ = self.install_quiet()
        self.assertEqual(code, 0)
        self.assertTrue((self.target / ".xstored").is_symlink())
        self.assertTrue((outside / "giu.txt").exists())

    def test_legacy_refs_scans_workflows_and_skips_binary(self):
        wf = self.target / ".github" / "workflows"
        wf.mkdir(parents=True)
        (wf / "ci.yml").write_text("run: XS_DEBUG=1 bash scripts/dev-task.sh gate\n", encoding="utf-8")
        (self.target / ".claude" / "bin").mkdir(parents=True)
        (self.target / ".claude" / "bin" / "blob").write_bytes(b"\xff\xfe.xstored")
        (self.target / "README.md").write_text("Dùng .xtemplates/scripts/xt.py và xt.yaml.\n", encoding="utf-8")
        self.assertEqual(install.legacy_refs(self.target), [".github/workflows/ci.yml"])


def make_fake_src(base: Path, ruleset: str | None = None) -> Path:
    """Khung giả tối thiểu: không research/, không VERSION, templates/ chỉ có mẫu GitHub (khi có ruleset) — để chạm nhánh 'thiếu'."""
    src = base / "khung"
    (src / "framework").mkdir(parents=True)
    (src / "framework" / "x.md").write_text("x\n", encoding="utf-8")
    (src / "scripts").mkdir()
    for f in ("xt.py", "dev-task.sh", "check-links.py"):
        (src / "scripts" / f).write_text("# giả\n", encoding="utf-8")
    (src / ".claude").mkdir()
    (src / ".claude" / "settings.json").write_text('{"hooks": {}}\n', encoding="utf-8")
    for d in install.HARNESS_DIRS:
        (src / ".claude" / d).mkdir()
    if ruleset is not None:
        (src / "framework" / "templates").mkdir(parents=True, exist_ok=True)
        (src / "framework" / "templates" / "ruleset-main.json").write_text(ruleset, encoding="utf-8")
        (src / "framework" / "templates" / "PULL-REQUEST.md").write_text("pr\n", encoding="utf-8")
        (src / "framework" / "templates" / "dependabot.yml").write_text("version: 2\n", encoding="utf-8")
        for wf in ("ci.yml", "secret-scan.yml"):
            (src / "framework" / "templates" / wf).write_text("name: x\n", encoding="utf-8")
        (src / ".github" / "workflows").mkdir(parents=True)
        (src / ".github" / "workflows" / "merge-gate.yml").write_text("name: merge-gate\n", encoding="utf-8")
        (src / ".github" / "workflows" / "pr-steward.yml").write_text("name: pr-steward\n", encoding="utf-8")
    return src


class InstallEdgeTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name).resolve()
        # git không được dò ngược lên thư mục cha (TMPDIR nằm trong một repo → framework_label nhặt nhầm SHA)
        ceiling = mock.patch.dict(os.environ, {"GIT_CEILING_DIRECTORIES": str(self.tmp.parent)})
        ceiling.start()
        self.addCleanup(ceiling.stop)
        self.target = self.tmp / "dich"
        self.target.mkdir()

    def install_quiet(self, *extra) -> tuple[int, str]:
        err = io.StringIO()
        with redirect_stderr(err):
            code = install.main([str(self.target), "--label", "t", *extra])
        return code, err.getvalue()

    def test_strip_frontmatter_unclosed_keeps_text(self):
        self.assertEqual(install.strip_frontmatter("---\ntitle: x\nkhông đóng\n"), "---\ntitle: x\nkhông đóng\n")
        self.assertEqual(install.strip_frontmatter("---\na: 1\n---\n\nthân\n"), "thân\n")
        self.assertEqual(install.strip_frontmatter(""), "")

    def test_write_atomic_writes_and_cleans_temp_on_failure(self):
        f = self.tmp / "out.json"
        install.write_atomic(f, "nội dung Đ\n")
        self.assertEqual(f.read_text(encoding="utf-8"), "nội dung Đ\n")
        with mock.patch.object(install.os, "replace", side_effect=OSError("đĩa đầy")):
            with self.assertRaises(OSError):
                install.write_atomic(f, "mới\n")
        self.assertEqual(f.read_text(encoding="utf-8"), "nội dung Đ\n")  # bản cũ còn nguyên
        self.assertEqual([p.name for p in self.tmp.iterdir() if p.name.endswith(".tmp")], [])  # không rác

    def test_merge_hooks_symlink_destination_is_skipped(self):
        outside = self.tmp / "ngoai.json"
        outside.write_text("{}", encoding="utf-8")
        dst = self.tmp / "settings.json"
        dst.symlink_to(outside)
        src = self.tmp / "src.json"
        src.write_text('{"hooks": {"Stop": [{"hooks": [{"command": "x"}]}]}}', encoding="utf-8")
        with redirect_stderr(io.StringIO()) as err:
            self.assertEqual(install.merge_hooks(src, dst), "skipped-symlink")
        self.assertIn("bỏ qua symlink", err.getvalue())
        self.assertEqual(outside.read_text(encoding="utf-8"), "{}")

    def test_merge_hooks_updates_framework_matcher_only(self):
        """D-057: hook của khung đã đăng ký với matcher cũ → cập nhật; mục có lệnh riêng của dự án → giữ nguyên."""
        cmd, own = "bash pre-mcp-guard.sh", "bash rieng.sh"
        src = self.tmp / "src.json"
        new = {"matcher": "mcp__.*(merge|create_pull_request).*", "hooks": [{"command": cmd}]}
        src.write_text(json.dumps({"hooks": {"PreToolUse": [new]}}), encoding="utf-8")
        dst = self.tmp / "settings.json"
        old = {"hooks": {"PreToolUse": [{"matcher": "mcp__.*merge.*", "hooks": [{"command": cmd}]}]}}
        dst.write_text(json.dumps(old), encoding="utf-8")
        self.assertEqual(install.merge_hooks(src, dst), "merged-hooks")
        self.assertEqual(
            json.loads(dst.read_text(encoding="utf-8"))["hooks"]["PreToolUse"][0]["matcher"], new["matcher"]
        )
        self.assertEqual(install.merge_hooks(src, dst), "kept")
        mixed = {"matcher": "mcp__.*merge.*", "hooks": [{"command": cmd}, {"command": own}]}
        dst.write_text(json.dumps({"hooks": {"PreToolUse": [mixed]}}), encoding="utf-8")
        self.assertEqual(install.merge_hooks(src, dst), "kept")
        self.assertEqual(
            json.loads(dst.read_text(encoding="utf-8"))["hooks"]["PreToolUse"][0]["matcher"], "mcp__.*merge.*"
        )

    def test_merge_hooks_invalid_or_missing_json_is_reported(self):
        src = self.tmp / "src.json"
        src.write_text('{"hooks": {}}', encoding="utf-8")
        dst = self.tmp / "settings.json"
        dst.write_text("{không phải json", encoding="utf-8")
        with redirect_stderr(io.StringIO()) as err:
            self.assertEqual(install.merge_hooks(src, dst), "invalid-json")
        self.assertIn("HOOK CHƯA ĐĂNG KÝ", err.getvalue())
        self.assertEqual(dst.read_text(encoding="utf-8"), "{không phải json")  # không đè
        with redirect_stderr(io.StringIO()):
            self.assertEqual(install.merge_hooks(src, self.tmp / "khong-co.json"), "invalid-json")

    def test_install_with_invalid_existing_settings_keeps_it(self):
        settings = self.target / ".claude" / "settings.json"
        settings.parent.mkdir()
        settings.write_text("{hỏng", encoding="utf-8")
        code, err = self.install_quiet()
        self.assertEqual(code, 0)
        self.assertEqual(settings.read_text(encoding="utf-8"), "{hỏng")
        self.assertIn("invalid-json 1", err)

    def test_framework_label_variants(self):
        self.assertEqual(install.framework_label("v9"), "v9")
        src = self.tmp / "khung"
        src.mkdir()
        with mock.patch.object(install, "SRC", src):
            self.assertEqual(install.framework_label(None), "unknown")  # thiếu VERSION, không phải git repo
            (src / "VERSION").write_text("1.2.3\n", encoding="utf-8")
            ok = subprocess.CompletedProcess([], 0, stdout="abc1234\n", stderr="")
            with mock.patch.object(install.subprocess, "run", return_value=ok) as run:
                self.assertEqual(install.framework_label(None), "1.2.3 (abc1234)")
            self.assertIn(str(src), run.call_args.args[0])
            for result in (
                subprocess.CompletedProcess([], 128, stdout="", stderr="not a repo"),
                subprocess.CompletedProcess([], 0, stdout="  \n", stderr=""),
            ):
                with mock.patch.object(install.subprocess, "run", return_value=result):
                    self.assertEqual(install.framework_label(None), "1.2.3")
            for exc in (OSError("không có git"), subprocess.TimeoutExpired("git", 10)):
                with mock.patch.object(install.subprocess, "run", side_effect=exc):
                    self.assertEqual(install.framework_label(None), "1.2.3")

    def test_no_harness_skips_claude_dir_and_harness_hashes(self):
        code, _ = self.install_quiet("--no-harness")
        self.assertEqual(code, 0)
        self.assertFalse((self.target / ".claude").exists())
        # manifest vẫn ghi để file gốc nâng được không gộp tay (T-1732) — chỉ hash file gốc, không có file harness
        legacy = json.loads((self.target / ".xtemplates" / "harness.sha256.json").read_text(encoding="utf-8"))
        self.assertEqual(set(legacy), set(install.ROOT_TEMPLATES))
        self.assertTrue((self.target / ".xtemplates" / "framework").is_dir())
        self.assertTrue((self.target / "AGENTS.md").exists())

    def test_own_root_file_message_is_not_edited_old_copy(self):  # AUD-HAR-052
        (self.target / "AGENTS.md").write_text("# luật riêng\n", encoding="utf-8")
        hook = self.target / ".claude" / "hooks" / "guard.py"
        hook.parent.mkdir(parents=True)
        hook.write_text("# của tôi\n", encoding="utf-8")
        code, err = self.install_quiet()
        self.assertEqual(code, 0)
        self.assertNotIn("bạn đã sửa bản cũ", err)
        self.assertIn("AGENTS.md: giữ file của dự án", err)
        self.assertIn("hàng rào", err)

    def test_preexisting_modified_hook_gets_new_file_once_and_template_hash(self):
        hook = self.target / ".claude" / "hooks" / "stop-guard.sh"
        hook.parent.mkdir(parents=True)
        hook.write_text("# của tôi\n", encoding="utf-8")
        code, err = self.install_quiet()
        self.assertEqual(code, 0)
        self.assertEqual(hook.read_text(encoding="utf-8"), "# của tôi\n")
        new = hook.with_name("stop-guard.sh.xtemplates-new")
        self.assertTrue(new.exists())
        self.assertIn(".xtemplates-new", err)
        manifest = json.loads((self.target / ".xtemplates" / "harness.sha256.json").read_text(encoding="utf-8"))
        # D-114: `updated-new` ghi hash MẪU mới (không phải hash file của dự án) → lần sau mẫu không đổi thì im lặng
        self.assertEqual(
            manifest[".claude/hooks/stop-guard.sh"], stored((ROOT / ".claude/hooks/stop-guard.sh").read_bytes())
        )
        self.assertIn(".claude/hooks/session-start.sh", manifest)
        new.unlink()  # dự án đã xem/gộp bản mới
        code, err = self.install_quiet()
        self.assertEqual(code, 0)
        self.assertFalse(new.exists())  # `kept-own`: không ghi lại `.xtemplates-new`
        self.assertRegex(err, r"✓ \.claude/: .*kept-own 1")
        self.assertNotIn("có file .xtemplates-new", err)
        self.assertEqual(hook.read_text(encoding="utf-8"), "# của tôi\n")

    def test_harness_symlink_is_skipped_and_hash_kept(self):
        """AUD-HAR-010 cho file harness: đích là symlink → `skipped-symlink`, không ghi qua liên kết; chưa có hash thì
        không ghi, đã có hash thì giữ nguyên (symlink không thuộc `HASHED`) — hex trần của manifest cũ ghi lại dạng
        `sha256:<hex>`."""
        outside = self.tmp / "ngoai.sh"
        hook = self.target / ".claude" / "hooks" / "stop-guard.sh"
        hook.parent.mkdir(parents=True)
        hook.symlink_to(outside)
        code, err = self.install_quiet()
        self.assertEqual(code, 0)
        self.assertFalse(outside.exists())
        self.assertRegex(err, r"✓ \.claude/: .*skipped-symlink 1")
        mf = self.target / ".xtemplates" / "harness.sha256.json"
        manifest = json.loads(mf.read_text(encoding="utf-8"))
        self.assertNotIn(".claude/hooks/stop-guard.sh", manifest)
        manifest[".claude/hooks/stop-guard.sh"] = install.sha256(b"ban cu\n")
        mf.write_text(json.dumps(manifest), encoding="utf-8")
        self.install_quiet()
        self.assertEqual(json.loads(mf.read_text(encoding="utf-8"))[".claude/hooks/stop-guard.sh"], stored(b"ban cu\n"))
        self.assertFalse(outside.exists())

    def test_missing_root_template_is_skipped(self):
        with mock.patch.dict(install.ROOT_TEMPLATES, {"KHONG-CO.md": "KHONG-CO.md"}):
            code, _ = self.install_quiet()
        self.assertEqual(code, 0)
        self.assertFalse((self.target / "KHONG-CO.md").exists())
        self.assertTrue((self.target / "AGENTS.md").exists())

    def test_gitignore_is_appended_not_replaced(self):
        gi = self.target / ".gitignore"
        gi.write_text("node_modules/\n", encoding="utf-8")
        code, err = self.install_quiet()
        self.assertEqual(code, 0)
        self.assertEqual(
            gi.read_text(encoding="utf-8"),
            "node_modules/\n\n# X-Templates: trạng thái autopilot cục bộ\n.autopilot/\n",
        )
        self.assertIn("thêm .autopilot/", err)
        self.install_quiet()  # chạy lại: đã có dòng → không nhân đôi
        self.assertEqual(gi.read_text(encoding="utf-8").count(".autopilot/"), 1)

    def test_minimal_framework_without_research_templates_or_version(self):
        with mock.patch.object(install, "SRC", make_fake_src(self.tmp)):
            code, err = self.install_quiet()
        self.assertEqual(code, 0, err)
        xt_dir = self.target / ".xtemplates"
        self.assertFalse((xt_dir / "research").exists())
        self.assertTrue((xt_dir / "framework" / "x.md").exists())
        self.assertEqual((xt_dir / "VERSION").read_text(encoding="utf-8"), "t\n")
        self.assertFalse((self.target / "AGENTS.md").exists())  # không có mẫu → không tạo
        self.assertTrue((self.target / ".claude" / "settings.json").exists())

    def test_with_github_unreadable_or_checkless_ruleset_has_no_warning(self):
        cases = {
            "không phải json": "{không phải json",
            "thiếu khoá rules": "{}",
            "rules không có check": '{"rules": [{"type": "deletion"}]}',
        }
        for name, content in cases.items():
            with self.subTest(name):
                target = self.tmp / ("dich-" + str(len(name)))
                target.mkdir()
                src = make_fake_src(self.tmp / ("src-" + str(len(name))), ruleset=content)
                err = io.StringIO()
                with mock.patch.object(install, "SRC", src), redirect_stderr(err):
                    self.assertEqual(install.main([str(target), "--label", "t", "--with-github"]), 0)
                self.assertNotIn("required check", err.getvalue())
                self.assertEqual((target / ".github" / "rulesets" / "main.json").read_text(encoding="utf-8"), content)
                self.assertTrue((target / ".github" / "dependabot.yml").exists())

    def test_run_as_script(self):
        r = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "install.py"), str(self.target), "--label", "cli", "--no-harness"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual((self.target / ".xtemplates" / "VERSION").read_text(encoding="utf-8"), "cli\n")
        self.assertIn("[install] Xong.", r.stderr)


class InstallPlanTest(unittest.TestCase):
    """`--plan` + manifest.json (REC-09): kế hoạch không ghi gì; chỉ gỡ `ask` mà manifest chứng minh do khung đặt."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.target = Path(tmp.name).resolve() / "dich"
        self.target.mkdir()
        self.settings = self.target / ".claude" / "settings.json"

    def install(self, *extra) -> int:
        with redirect_stderr(io.StringIO()):
            return install.main([str(self.target), "--label", "t", *extra])

    def plan(self, *extra) -> dict:
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = install.main([str(self.target), "--plan", *extra])
        self.assertEqual(code, 0, err.getvalue())
        return json.loads(out.getvalue())

    def snapshot(self) -> dict[str, bytes]:
        return {p.relative_to(self.target).as_posix(): p.read_bytes() for p in self.target.rglob("*") if p.is_file()}

    def write_settings(self, perms: dict, **extra) -> None:
        self.settings.parent.mkdir(parents=True, exist_ok=True)
        self.settings.write_text(json.dumps({"permissions": perms, **extra}), encoding="utf-8")

    def manifest(self) -> dict:
        return json.loads((self.target / ".xtemplates" / "manifest.json").read_text(encoding="utf-8"))

    def test_install_plan_fresh_writes_nothing(self):
        before = self.snapshot()
        plan = self.plan("--with-github")
        self.assertEqual(self.snapshot(), before)
        self.assertFalse((self.target / ".xtemplates").exists())
        self.assertEqual(plan["schema"], 1)
        self.assertEqual(plan["settings"], {"action": "copied"})
        actions = {f["path"]: f["action"] for f in plan["files"]}
        self.assertEqual(actions[".claude/hooks/stop-guard.sh"], "copied")
        self.assertEqual(actions["AGENTS.md"], "copied")
        self.assertEqual(actions[".github/rulesets/main.json"], "copied")
        self.assertEqual(actions[".github/workflows/ci.yml"], "copied")
        self.assertEqual(actions[".github/workflows/secret-scan.yml"], "copied")
        self.assertFalse(plan["legacy_migration"])
        self.assertFalse(plan["manifest"]["present"])

    def test_install_plan_matches_real_install_actions(self):
        self.install()
        hook = self.target / ".claude" / "hooks" / "stop-guard.sh"
        hook.write_text("# của tôi\n", encoding="utf-8")
        (self.target / "AGENTS.md").unlink()
        (self.target / "CLAUDE.md").write_text("# luật riêng\n", encoding="utf-8")
        before = self.snapshot()
        plan = self.plan()
        self.assertEqual(self.snapshot(), before)
        actions = {f["path"]: f["action"] for f in plan["files"]}
        # T-1732: mẫu không đổi từ lần cài trước → file dự án đã sửa (hook lẫn file gốc) là `kept-own`
        self.assertEqual(actions[".claude/hooks/stop-guard.sh"], "kept-own")
        self.assertEqual(actions["CLAUDE.md"], "kept-own")
        self.assertEqual(actions["AGENTS.md"], "copied")
        self.assertEqual(actions["PROGRESS.md"], "kept")
        self.assertEqual(plan["settings"]["action"], "kept")
        self.assertTrue(plan["manifest"]["present"])
        forced = self.plan("--force-harness")
        self.assertEqual({f["path"]: f["action"] for f in forced["files"]}[".claude/hooks/stop-guard.sh"], "copied")
        self.assertEqual(forced["settings"], {"action": "copied"})
        self.install()
        self.assertEqual(sorted(p.name for p in self.target.rglob("*.xtemplates-new")), [])
        self.assertEqual((self.target / "CLAUDE.md").read_text(encoding="utf-8"), "# luật riêng\n")
        # mẫu đổi so với lần cài trước (hash lần trước khác) → kế hoạch `updated-new`, bản thật ghi `.xtemplates-new`
        mf = self.target / ".xtemplates" / "harness.sha256.json"
        m = json.loads(mf.read_text(encoding="utf-8"))
        m[".claude/hooks/stop-guard.sh"] = m["CLAUDE.md"] = install.sha256(b"ban khung cu\n")
        mf.write_text(json.dumps(m), encoding="utf-8")
        actions = {f["path"]: f["action"] for f in self.plan()["files"]}
        self.assertEqual((actions[".claude/hooks/stop-guard.sh"], actions["CLAUDE.md"]), ("updated-new",) * 2)
        self.install()
        self.assertTrue(hook.with_name("stop-guard.sh.xtemplates-new").exists())
        self.assertTrue((self.target / "CLAUDE.md.xtemplates-new").exists())

    def test_install_plan_github_matches_real_install(self):
        own = self.target / ".github" / "workflows" / "ci.yml"
        own.parent.mkdir(parents=True)
        own.write_text("name: CI riêng\n", encoding="utf-8")
        actions = {f["path"]: f["action"] for f in self.plan("--with-github")["files"]}
        self.assertEqual(actions[".github/workflows/ci.yml"], "updated-new")  # file dự án: giữ, mẫu ra .xtemplates-new
        self.assertEqual(actions[".github/workflows/secret-scan.yml"], "copied")
        self.install("--with-github")
        actions = {f["path"]: f["action"] for f in self.plan("--with-github")["files"]}
        self.assertEqual(actions[".github/workflows/secret-scan.yml"], "kept")
        self.assertTrue(own.with_name("ci.yml.xtemplates-new").exists())
        self.assertFalse([f for f in self.plan()["files"] if f["path"].startswith(".github/")])  # chỉ khi --with-github

    def test_install_plan_reports_permission_and_hook_diff(self):
        self.write_settings({"allow": ["Bash(make *)"], "ask": ["Bash(git merge *)"], "deny": []})
        (self.target / ".xtemplates").mkdir()
        (self.target / ".xtemplates" / "manifest.json").write_text(
            json.dumps({"rules": {"ask": ["Bash(git merge *)"]}}), encoding="utf-8"
        )
        before = self.snapshot()
        plan = self.plan()
        self.assertEqual(self.snapshot(), before)
        st = plan["settings"]
        ours = json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
        self.assertEqual(st["action"], "merged-hooks")
        self.assertEqual(st["permissions"]["allow_add"], ["Bash"])
        self.assertEqual(st["permissions"]["deny_add"], ours["permissions"]["deny"])
        self.assertEqual(st["permissions"]["ask_remove"], ["Bash(git merge *)"])
        self.assertEqual(st["permissions"]["ask_unproven"], [])
        self.assertIn("PreToolUse", {h["event"] for h in st["hooks_added"]})
        self.assertEqual(st["hooks_matcher_updated"], [])

    def test_install_plan_reports_matcher_update(self):
        ours = json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
        old = json.loads(json.dumps(ours))
        for entries in old["hooks"].values():
            for e in entries:
                if "matcher" in e:
                    e["matcher"] = "Cu"
        self.settings.parent.mkdir(parents=True)
        self.settings.write_text(json.dumps(old), encoding="utf-8")
        st = self.plan()["settings"]
        self.assertTrue(st["hooks_matcher_updated"])
        self.assertEqual(st["hooks_matcher_updated"][0]["matcher_from"], "Cu")

    def test_install_plan_unproven_ask_is_kept_and_reported(self):
        # Trùng chuỗi `ask` của khung cũ nhưng không có trong manifest → rule của dự án: giữ + báo (REC-09).
        self.write_settings({"ask": ["Bash(git merge *)", "Bash(make deploy*)"]})
        st = self.plan()["settings"]
        self.assertEqual(st["permissions"]["ask_remove"], [])
        self.assertEqual(st["permissions"]["ask_unproven"], ["Bash(git merge *)"])
        err = io.StringIO()
        with redirect_stderr(err):
            self.assertEqual(install.main([str(self.target), "--label", "t"]), 0)
        self.assertEqual(
            json.loads(self.settings.read_text(encoding="utf-8"))["permissions"]["ask"],
            ["Bash(git merge *)", "Bash(make deploy*)"],
        )
        self.assertIn("manifest không chứng minh", err.getvalue())

    def test_install_plan_manifest_records_framework_rules(self):
        self.install()
        m = self.manifest()
        ours = json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))["permissions"]
        self.assertEqual(m["schema"], 1)
        self.assertEqual(m["policy"], {"ask_removal": "manifest-only"})
        self.assertEqual(m["rules"]["deny"], ours["deny"])
        self.assertEqual(m["rules"]["allow"], ours["allow"])
        self.assertIn(".claude/hooks/stop-guard.sh", m["files"])
        self.assertEqual(m["files"], json.loads((self.target / ".xtemplates/harness.sha256.json").read_text()))
        before = (self.target / ".xtemplates" / "manifest.json").read_text(encoding="utf-8")
        self.install()  # idempotent
        self.assertEqual((self.target / ".xtemplates" / "manifest.json").read_text(encoding="utf-8"), before)

    def test_review173_manifest_rules_do_not_grow(self):
        """PR #173: rule khung bị gỡ rồi cài lại (khung thêm lại) không làm `rules.deny` phình; trùng sẵn có được khử."""
        self.install()
        first = self.manifest()["rules"]
        for _ in range(2):
            data = json.loads(self.settings.read_text(encoding="utf-8"))
            data["permissions"]["deny"] = data["permissions"]["deny"][1:]
            data["permissions"]["allow"] = []
            self.settings.write_text(json.dumps(data), encoding="utf-8")
            self.install()
        self.assertEqual(self.manifest()["rules"], first)
        out = install.update_provenance(
            {"allow": ["a", "a"], "ask": ["q", "q", "r"], "deny": ["d"]},
            {"permissions": {"allow_add": ["b", "a"], "deny_add": ["d", "e"], "ask_remove": ["r"]}},
        )
        self.assertEqual(out, {"allow": ["a", "b"], "ask": ["q"], "deny": ["d", "e"]})

    def test_install_plan_manifest_keeps_user_preexisting_rule_out(self):
        # Rule deny người dùng đã có sẵn trùng của khung: không do khung thêm → không vào manifest.
        ours = json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))["permissions"]
        mine = ours["deny"][0]
        self.write_settings({"deny": [mine]})
        self.install()
        self.assertNotIn(mine, self.manifest()["rules"]["deny"])
        self.assertIn(ours["deny"][1], self.manifest()["rules"]["deny"])

    def test_install_plan_removes_ask_only_when_framework_no_longer_sets_it(self):
        self.install()
        m = self.manifest()
        m["rules"]["ask"] = ["Bash(old *)"]
        (self.target / ".xtemplates" / "manifest.json").write_text(json.dumps(m), encoding="utf-8")
        data = json.loads(self.settings.read_text(encoding="utf-8"))
        data["permissions"]["ask"] = ["Bash(old *)", "Bash(mine *)"]
        self.settings.write_text(json.dumps(data), encoding="utf-8")
        self.install()
        self.assertEqual(json.loads(self.settings.read_text(encoding="utf-8"))["permissions"]["ask"], ["Bash(mine *)"])
        self.assertEqual(self.manifest()["rules"]["ask"], [])

    def test_install_removes_framework_deny_moved_to_guard(self):
        """ADR-0040: deny tĩnh khung từng đặt (manifest chứng minh) mà khung bỏ → gỡ; deny riêng của dự án giữ."""
        self.install()
        m = self.manifest()
        m["rules"]["deny"] = [*m["rules"]["deny"], "Bash(git reset --hard *)"]
        (self.target / ".xtemplates" / "manifest.json").write_text(json.dumps(m), encoding="utf-8")
        data = json.loads(self.settings.read_text(encoding="utf-8"))
        data["permissions"]["deny"] += ["Bash(git reset --hard *)", "Bash(git clean -*)"]
        self.settings.write_text(json.dumps(data), encoding="utf-8")
        self.install()
        deny = json.loads(self.settings.read_text(encoding="utf-8"))["permissions"]["deny"]
        self.assertNotIn("Bash(git reset --hard *)", deny)
        self.assertIn("Bash(git clean -*)", deny)  # không có trong manifest → rule của dự án
        self.assertNotIn("Bash(git reset --hard *)", self.manifest()["rules"]["deny"])

    def test_install_plan_load_rules_tolerates_bad_manifest(self):
        empty = {"allow": [], "ask": [], "deny": []}
        mf = self.target / ".xtemplates" / "manifest.json"
        self.assertEqual(install.load_rules(self.target), empty)
        mf.parent.mkdir()
        for text in ("{không phải json", "[]", '{"rules": 5}', '{"rules": {"ask": 5}}'):
            mf.write_text(text, encoding="utf-8")
            self.assertEqual(install.load_rules(self.target), empty, text)
        mf.write_text('{"rules": {"ask": ["a", 3, null]}}', encoding="utf-8")
        self.assertEqual(install.load_rules(self.target)["ask"], ["a"])

    def test_install_plan_settings_edge_cases(self):
        self.settings.parent.mkdir(parents=True)
        self.settings.write_text("{hỏng", encoding="utf-8")
        self.assertEqual(self.plan()["settings"], {"action": "invalid-json"})
        self.settings.unlink()
        self.settings.symlink_to(self.target / "khong-co.json")  # symlink treo
        self.assertEqual(self.plan()["settings"], {"action": "skipped-symlink"})
        with redirect_stderr(io.StringIO()):
            self.assertEqual(install.main([str(self.target), "--label", "t"]), 0)
        self.assertTrue(self.settings.is_symlink())
        self.assertFalse(self.settings.exists())
        self.assertEqual(self.manifest()["rules"], {"allow": [], "ask": [], "deny": []})

    def test_install_plan_no_harness_and_legacy(self):
        (self.target / ".xstored").mkdir()
        plan = self.plan("--no-harness")
        self.assertEqual(plan["settings"], {"action": "skipped"})
        self.assertTrue(plan["legacy_migration"])
        self.assertTrue(all(not f["path"].startswith(".claude/") for f in plan["files"]))
        self.assertTrue((self.target / ".xstored").is_dir())

    def test_install_plan_invalid_target(self):
        err = io.StringIO()
        with redirect_stderr(err):
            self.assertEqual(install.main([str(self.target / "khong-co"), "--plan"]), 2)
        self.assertIn("không phải thư mục", err.getvalue())


class InstallUpgradeTest(unittest.TestCase):
    """T-1732: nâng bản không gộp tay — file gốc có hash trong manifest (`kept-own` khi dự án đã sửa mà mẫu không đổi,
    `.xtemplates-new` một lần khi mẫu đổi), in bước "Dự án đích" của CHANGELOG, khoá mới của `xt.yaml` dạng chú thích."""

    MARKER = '# Khoá mới của khung (bản t) — bật bằng cách bỏ "# "; vắng khoá = hành vi cũ'

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name).resolve()
        # đích không phải repo git (kể cả khi TMPDIR nằm trong repo) → PROGRESS không nhận SHA HEAD, hash ổn định
        ceiling = mock.patch.dict(os.environ, {"GIT_CEILING_DIRECTORIES": str(self.tmp.parent)})
        ceiling.start()
        self.addCleanup(ceiling.stop)
        self.target = self.tmp / "dich"
        self.target.mkdir()

    def install_quiet(self, *extra) -> tuple[int, str]:
        err = io.StringIO()
        with redirect_stderr(err):
            code = install.main([str(self.target), "--label", "t", *extra])
        self.assertEqual(code, 0, err.getvalue())
        return code, err.getvalue()

    def plan(self, *extra: str) -> dict[str, dict]:
        out = io.StringIO()
        with redirect_stdout(out), redirect_stderr(io.StringIO()):
            self.assertEqual(install.main([str(self.target), "--plan", *extra]), 0)
        return {f["path"]: f for f in json.loads(out.getvalue())["files"]}

    def files(self) -> dict[str, str]:
        """Map `files` — `harness.sha256.json` và `manifest.json` phải giống nhau."""
        xt_dir = self.target / ".xtemplates"
        legacy = json.loads((xt_dir / "harness.sha256.json").read_text(encoding="utf-8"))
        self.assertEqual(json.loads((xt_dir / "manifest.json").read_text(encoding="utf-8"))["files"], legacy)
        return legacy

    def set_installed_hash(self, rel: str, content: bytes) -> None:
        """Giả lập: lần cài trước là bản khung `content` (mẫu đã đổi kể từ đó) — ghi hex trần như manifest cũ; dạng
        `sha256:<hex>`: `test_manifest_*`."""
        mf = self.target / ".xtemplates" / "harness.sha256.json"
        m = json.loads(mf.read_text(encoding="utf-8"))
        m[rel] = install.sha256(content)
        mf.write_text(json.dumps(m), encoding="utf-8")

    @staticmethod
    def template(name: str) -> bytes:
        return install.source_bytes(ROOT / "framework" / "templates" / name, install.template_body)

    def test_kept_own_when_template_unchanged(self):
        """Dự án sửa AGENTS.md + một hook, cài lại với mẫu không đổi → `kept-own`: không `.xtemplates-new`, không cảnh
        báo gộp tay, file và hash giữ nguyên."""
        _, err = self.install_quiet()
        self.assertNotIn("Bước làm tay", err)  # cài mới (chưa có VERSION) → không in bước CHANGELOG
        agents = self.target / "AGENTS.md"
        hook = self.target / ".claude" / "hooks" / "stop-guard.sh"
        agents.write_text("# luật riêng của dự án — Đ\n", encoding="utf-8")
        hook.write_text("# hook đã sửa\n", encoding="utf-8")
        before = self.files()
        _, err = self.install_quiet()
        self.assertEqual(agents.read_text(encoding="utf-8"), "# luật riêng của dự án — Đ\n")
        self.assertEqual(hook.read_text(encoding="utf-8"), "# hook đã sửa\n")
        self.assertEqual(sorted(p.name for p in self.target.rglob("*.xtemplates-new")), [])
        self.assertIn("AGENTS.md: kept-own", err)
        self.assertRegex(err, r"✓ \.claude/: .*kept-own 1")
        self.assertNotIn("có file .xtemplates-new", err)
        self.assertEqual(self.files(), before)
        self.assertNotIn("Bước làm tay", err)  # nhãn "t" không đọc được X.Y.Z → bỏ qua

    def test_template_changed_and_edited_writes_new_once(self):
        """Mẫu đổi + dự án đã sửa → `.xtemplates-new` MỘT lần, hash mẫu mới vào manifest; lần cài sau mẫu không đổi →
        im lặng (`kept-own`)."""
        self.install_quiet()
        agents = self.target / "AGENTS.md"
        agents.write_text("# luật riêng\n", encoding="utf-8")
        self.set_installed_hash("AGENTS.md", b"# mau AGENTS cu\n")
        _, err = self.install_quiet()
        new = agents.with_name("AGENTS.md.xtemplates-new")
        self.assertEqual(new.read_bytes(), self.template("AGENTS.md"))
        self.assertEqual(agents.read_text(encoding="utf-8"), "# luật riêng\n")
        self.assertIn("AGENTS.md: giữ file của dự án; mẫu khung ở AGENTS.md.xtemplates-new", err)
        self.assertEqual(self.files()["AGENTS.md"], stored(self.template("AGENTS.md")))
        new.unlink()  # dự án đã gộp phần của khung
        _, err = self.install_quiet()
        self.assertFalse(new.exists())
        self.assertIn("AGENTS.md: kept-own", err)
        self.assertEqual(agents.read_text(encoding="utf-8"), "# luật riêng\n")

    def test_pristine_root_file_updated_in_place(self):
        """File gốc còn đúng hash lần cài trước (chưa sửa) + mẫu đổi → cập nhật tại chỗ, không `.xtemplates-new`."""
        self.install_quiet()
        claude = self.target / "CLAUDE.md"
        claude.write_bytes(b"# mau CLAUDE cu\n")
        self.set_installed_hash("CLAUDE.md", b"# mau CLAUDE cu\n")
        _, err = self.install_quiet()
        self.assertEqual(claude.read_bytes(), self.template("CLAUDE.md"))
        self.assertFalse(claude.with_name("CLAUDE.md.xtemplates-new").exists())
        self.assertIn("CLAUDE.md: updated", err)
        self.assertEqual(self.files()["CLAUDE.md"], stored(self.template("CLAUDE.md")))

    def test_manifest_records_root_file_hashes(self):
        """Hash file gốc = nội dung mẫu đã ghi (sau biến đổi) trong CÙNG map `files` với harness; cài lại không đổi gì
        thì manifest không đổi; file gốc là symlink → bỏ qua, giữ hash cũ."""
        self.install_quiet()
        files = self.files()
        for name in install.ROOT_TEMPLATES:
            self.assertEqual(files[name], stored((self.target / name).read_bytes()), name)
        self.assertIn(".claude/hooks/stop-guard.sh", files)
        manifest = (self.target / ".xtemplates" / "manifest.json").read_text(encoding="utf-8")
        self.install_quiet()
        self.assertEqual((self.target / ".xtemplates" / "manifest.json").read_text(encoding="utf-8"), manifest)
        outside = self.tmp / "ngoai.md"
        (self.target / "CLAUDE.md").unlink()
        (self.target / "CLAUDE.md").symlink_to(outside)
        self.set_installed_hash("CLAUDE.md", b"# mau CLAUDE cu\n")
        _, err = self.install_quiet()
        self.assertIn("CLAUDE.md: skipped-symlink", err)
        self.assertFalse(outside.exists())
        self.assertEqual(self.files()["CLAUDE.md"], stored(b"# mau CLAUDE cu\n"))

    BARE_HEX = re.compile(r'"[0-9a-f]{64}"')  # giá trị hex trần trong JSON — dạng gitleaks `generic-api-key` bắt

    def to_bare_hex(self, extra: dict[str, str] | None = None) -> None:
        """Giả lập manifest ≤ 3.11.0: mọi hash ở cả hai file về hex trần (+ `extra` đè lên)."""
        xt_dir = self.target / ".xtemplates"
        for mf in (xt_dir / "harness.sha256.json", xt_dir / "manifest.json"):
            doc = json.loads(mf.read_text(encoding="utf-8"))
            files = doc.get("files", doc)
            files.update({rel: install.manifest_hash(v) for rel, v in files.items()})
            files.update(extra or {})
            mf.write_text(json.dumps(doc), encoding="utf-8")
            self.assertIsNotNone(self.BARE_HEX.search(mf.read_text(encoding="utf-8")), mf.name)

    def test_manifest_labels_every_hash_sha256(self):
        """T-1743: gitleaks (`generic-api-key`) bắt hex trần sau khoá `…/secret-scan.yml` → mọi hash ghi `sha256:<hex>`
        ở cả hai file manifest — harness, file gốc lẫn `.github/`; giá trị là hash nội dung đã ghi."""
        self.install_quiet("--with-github")
        files = self.files()
        for rel in (".claude/hooks/stop-guard.sh", "AGENTS.md", ".github/workflows/secret-scan.yml"):
            self.assertEqual(files[rel], stored((self.target / rel).read_bytes()), rel)
        self.assertLessEqual({*install.GITHUB_FILES, *install.ROOT_TEMPLATES}, set(files))
        self.assertEqual([v for v in files.values() if not re.fullmatch(r"sha256:[0-9a-f]{64}", v)], [])

    def test_manifest_hash_forms_and_load_manifest(self):
        """`manifest_hash` bỏ tiền tố `sha256:` (hex trần giữ nguyên), `hash_label` không nhân đôi tiền tố;
        `classify_copy` nhận cả hai dạng (kể cả trộn) cho `installed_hash`/`template_hash`; `load_manifest` trả hex, bỏ
        giá trị không phải chuỗi, JSON không phải object → rỗng."""
        h = install.sha256(b"x")
        self.assertEqual([install.manifest_hash(v) for v in (h, "sha256:" + h, "")], [h, h, ""])
        self.assertEqual({install.hash_label(h), install.hash_label("sha256:" + h)}, {"sha256:" + h})
        src, dst = self.tmp / "khung.sh", self.tmp / "dich.sh"
        src.write_bytes(b"ban moi\n")
        dst.write_bytes(b"ban cu\n")
        for form in (install.sha256, stored):
            with self.subTest(form=form.__name__):
                for installed, want in (
                    (b"ban cu\n", "updated"),
                    (b"ban moi\n", "kept-own"),
                    (b"khac\n", "updated-new"),
                ):
                    self.assertEqual(install.classify_copy(src, dst, installed_hash=form(installed))[0], want)
                got = install.classify_copy(src, dst, installed_hash=stored(b"mau\n"), template_hash=form(b"mau\n"))
                self.assertEqual(got[0], "kept-own")
        mf = self.target / ".xtemplates" / "harness.sha256.json"
        mf.parent.mkdir()
        mf.write_text(json.dumps({"a": "sha256:" + h, "b": h, "c": 5, "d": None, "e": [h]}), encoding="utf-8")
        self.assertEqual(install.load_manifest(self.target), {"a": h, "b": h})
        mf.write_text(json.dumps([h]), encoding="utf-8")
        self.assertEqual(install.load_manifest(self.target), {})

    def test_manifest_legacy_bare_hex_still_pristine(self):
        """Manifest cũ (hex trần): file còn đúng hash lần cài trước vẫn là "chưa sửa" → cập nhật tại chỗ (harness, file
        gốc, `.github/`); đã sửa mà mẫu không đổi → `kept-own`; `--plan` khớp; cài xong ghi `sha256:<hex>`, cài lại
        không đổi manifest; hash dạng mới của bản cũ cũng là "chưa sửa"."""
        self.install_quiet("--with-github")
        old = b"# ban khung cu\n"
        expect = {
            ".claude/hooks/stop-guard.sh": (ROOT / ".claude/hooks/stop-guard.sh").read_bytes(),
            "CLAUDE.md": self.template("CLAUDE.md"),
            ".github/workflows/secret-scan.yml": (ROOT / "framework/templates/secret-scan.yml").read_bytes(),
        }
        for rel in expect:
            (self.target / rel).write_bytes(old)
        agents = self.target / "AGENTS.md"
        agents.write_text("# luật riêng\n", encoding="utf-8")
        self.to_bare_hex(dict.fromkeys(expect, install.sha256(old)))
        plan = self.plan("--with-github")
        want = {**dict.fromkeys(expect, "updated"), "AGENTS.md": "kept-own"}
        self.assertEqual({rel: plan[rel]["action"] for rel in want}, want)
        _, err = self.install_quiet("--with-github")
        self.assertEqual({rel: (self.target / rel).read_bytes() for rel in expect}, expect)
        self.assertEqual(sorted(p.name for p in self.target.rglob("*.xtemplates-new")), [])
        self.assertEqual(agents.read_text(encoding="utf-8"), "# luật riêng\n")
        self.assertIn("AGENTS.md: kept-own", err)
        files = self.files()
        self.assertEqual({rel: files[rel] for rel in expect}, {rel: stored(data) for rel, data in expect.items()})
        self.assertEqual(files["AGENTS.md"], stored(self.template("AGENTS.md")))
        self.assertEqual([v for v in files.values() if not v.startswith("sha256:")], [])
        manifest = (self.target / ".xtemplates" / "manifest.json").read_text(encoding="utf-8")
        self.install_quiet("--with-github")
        self.assertEqual((self.target / ".xtemplates" / "manifest.json").read_text(encoding="utf-8"), manifest)
        hook = self.target / ".claude/hooks/stop-guard.sh"
        hook.write_bytes(old)
        mf = self.target / ".xtemplates" / "harness.sha256.json"
        mf.write_text(json.dumps({**self.files(), ".claude/hooks/stop-guard.sh": stored(old)}), encoding="utf-8")
        self.assertEqual(self.plan()[".claude/hooks/stop-guard.sh"]["action"], "updated")
        self.install_quiet()
        self.assertEqual(hook.read_bytes(), expect[".claude/hooks/stop-guard.sh"])

    def test_manifest_no_bare_hex_after_carry_over(self):
        """Regex trên file: manifest vừa ghi không còn giá trị `"<64 hex>"` trần — kể cả hash chỉ GIỮ LẠI từ manifest cũ
        mà không băm lại: `.github/` khi cài lại không `--with-github`, file `kept-own`, đích symlink."""
        self.install_quiet("--with-github")
        xt_dir = self.target / ".xtemplates"
        manifests = (xt_dir / "harness.sha256.json", xt_dir / "manifest.json")
        self.assertEqual([mf.name for mf in manifests if self.BARE_HEX.search(mf.read_text(encoding="utf-8"))], [])
        self.to_bare_hex()
        (self.target / ".claude/hooks/stop-guard.sh").write_text("# đã sửa\n", encoding="utf-8")  # kept-own
        link = self.target / ".claude/hooks/session-start.sh"
        link.unlink()
        link.symlink_to(self.tmp / "ngoai.sh")  # skipped-symlink: giữ hash cũ
        _, err = self.install_quiet()
        self.assertRegex(err, r"✓ \.claude/: .*kept-own 1 .*skipped-symlink 1")
        self.assertEqual([mf.name for mf in manifests if self.BARE_HEX.search(mf.read_text(encoding="utf-8"))], [])
        files = self.files()
        scan = ".github/workflows/secret-scan.yml"
        self.assertEqual(files[scan], stored((self.target / scan).read_bytes()))
        for rel in (".claude/hooks/stop-guard.sh", ".claude/hooks/session-start.sh"):
            self.assertEqual(files[rel], stored((ROOT / rel).read_bytes()), rel)

    def test_manifest_mixed_forms_after_interrupted_write(self):
        """Nâng từ manifest hex trần bị ngắt giữa hai lần ghi (`harness.sha256.json` đã `sha256:`, `manifest.json` còn hex
        trần) — trạng thái người đọc đồng thời có thể thấy: `--plan` và `doctor --drift` vẫn đúng (không `modified` oan),
        lần cài sau ghi cả hai file dạng `sha256:`."""
        self.install_quiet("--with-github")
        self.to_bare_hex()
        real = install.write_atomic

        def fail_v2(path: Path, text: str) -> None:
            if path.name == "manifest.json":
                raise OSError("ngắt giữa chừng")
            real(path, text)

        with mock.patch.object(install, "write_atomic", side_effect=fail_v2), redirect_stderr(io.StringIO()):
            self.assertRaises(OSError, install.main, [str(self.target), "--label", "t"])
        xt_dir = self.target / ".xtemplates"
        legacy = json.loads((xt_dir / "harness.sha256.json").read_text(encoding="utf-8"))
        v2 = json.loads((xt_dir / "manifest.json").read_text(encoding="utf-8"))["files"]
        self.assertEqual({rel: install.manifest_hash(v) for rel, v in legacy.items()}, v2)
        self.assertTrue(all(v.startswith("sha256:") for v in legacy.values()))
        self.assertFalse(any(v.startswith("sha256:") for v in v2.values()))
        self.assertEqual({f["action"] for f in self.plan("--with-github").values()}, {"kept"})
        report = xt.drift_report(self.target, "v0.0.1")
        self.assertEqual((report["ok"], report["drift"]), (True, []))
        self.install_quiet("--with-github")
        self.assertEqual([v for v in self.files().values() if not v.startswith("sha256:")], [])

    def test_progress_hash_is_template_before_head_sha(self):
        """PROGRESS.md (D-114): hash vào manifest là mẫu TRƯỚC khi thay SHA HEAD, nên HEAD đổi không làm mẫu "đổi" — cài
        lại sau commit mới: PROGRESS còn SHA cũ hay dự án đã sửa đều `kept-own`, không `.xtemplates-new`."""
        subprocess.run(["git", "init", "-q", "-b", "main", str(self.target)], check=True)
        git = ["git", "-C", str(self.target), "-c", "user.name=t", "-c", "user.email=t@t"]

        def commit(msg: str) -> str:
            (self.target / "a.txt").write_text(msg, encoding="utf-8")
            subprocess.run([*git, "add", "a.txt"], check=True)
            subprocess.run([*git, "commit", "-qm", msg], check=True)
            return subprocess.run(
                [*git, "rev-parse", "HEAD"], capture_output=True, text=True, check=True
            ).stdout.strip()

        first = commit("1")
        self.install_quiet()
        progress = self.target / "PROGRESS.md"
        self.assertIn(f"`{first}`", progress.read_text(encoding="utf-8"))  # AUD-HAR-053 giữ nguyên
        basis = install.sha256(self.template("PROGRESS.md"))
        self.assertEqual(self.files()["PROGRESS.md"], install.hash_label(basis))
        self.assertNotEqual(install.sha256(progress.read_bytes()), basis)
        commit("2")
        _, err = self.install_quiet()
        self.assertIn("PROGRESS.md: kept-own", err)
        self.assertIn(f"`{first}`", progress.read_text(encoding="utf-8"))
        progress.write_text(progress.read_text(encoding="utf-8") + "- ghi chú của dự án\n", encoding="utf-8")
        commit("3")
        self.assertEqual(self.plan()["PROGRESS.md"]["action"], "kept-own")
        _, err = self.install_quiet()
        self.assertIn("PROGRESS.md: kept-own", err)
        self.assertFalse(progress.with_name("PROGRESS.md.xtemplates-new").exists())
        self.assertEqual(self.files()["PROGRESS.md"], install.hash_label(basis))

    def test_upgrade_from_install_without_root_hashes_infers_old_template(self):
        """Dự án cài từ bản chưa có hash file gốc (giả 3.7.1): hash lần cài trước suy từ `.xtemplates/framework/templates/`
        CŨ, trước khi khung mới thay nó (D-114) — AGENTS.md chưa sửa → `updated` tại chỗ; xt.yaml đã sửa + mẫu đổi →
        `updated-new` + nối khoá; PROGRESS đã sửa + mẫu không đổi → `kept-own`; manifest có hash thì thắng hash suy;
        `--plan` khớp; sau đó manifest ghi hash mẫu mới."""
        self.install_quiet()
        xt_dir = self.target / ".xtemplates"
        for mf in (xt_dir / "harness.sha256.json", xt_dir / "manifest.json"):
            doc = json.loads(mf.read_text(encoding="utf-8"))
            for name in ("AGENTS.md", "PROGRESS.md", "xt.yaml"):  # CLAUDE.md giữ hash: kiểm manifest thắng hash suy
                doc.get("files", doc).pop(name)
            mf.write_text(json.dumps(doc), encoding="utf-8")
        (xt_dir / "VERSION").write_text("3.7.1 (9433792)\n", encoding="utf-8")
        old = xt_dir / "framework" / "templates"
        (old / "AGENTS.md").write_text("---\ntitle: Mẫu AGENTS cũ\n---\n\n# AGENTS cũ\n", encoding="utf-8")
        agents = self.target / "AGENTS.md"
        agents.write_text("# AGENTS cũ\n", encoding="utf-8")  # đúng bản mẫu cũ đã cài (bỏ frontmatter) — chưa sửa
        (old / "xt.yaml").write_text('lint: ""\ntest: ""\n', encoding="utf-8")
        y = self.target / "xt.yaml"
        y.write_text("lint: ruff check .\ntest: pytest -q\n", encoding="utf-8")
        progress = self.target / "PROGRESS.md"  # mẫu PROGRESS cũ = mẫu hiện tại
        progress.write_text(progress.read_text(encoding="utf-8") + "- việc của dự án\n", encoding="utf-8")
        claude = self.target / "CLAUDE.md"
        claude.write_text("# luật riêng\n", encoding="utf-8")
        (old / "CLAUDE.md").write_text("# CLAUDE cũ khác\n", encoding="utf-8")  # suy từ đây sẽ ra `updated-new`
        expected = {
            "AGENTS.md": "updated",
            "CLAUDE.md": "kept-own",
            "PROGRESS.md": "kept-own",
            "xt.yaml": "updated-new",
        }
        plan = self.plan()
        self.assertEqual({name: plan[name]["action"] for name in install.ROOT_TEMPLATES}, expected)
        _, err = self.install_quiet()
        self.assertEqual(agents.read_bytes(), self.template("AGENTS.md"))
        self.assertIn("AGENTS.md: updated", err)
        self.assertIn("PROGRESS.md: kept-own", err)
        self.assertIn("CLAUDE.md: kept-own", err)
        self.assertEqual(claude.read_text(encoding="utf-8"), "# luật riêng\n")
        self.assertEqual(sorted(p.name for p in self.target.glob("*.xtemplates-new")), ["xt.yaml.xtemplates-new"])
        self.assertTrue(
            y.read_text(encoding="utf-8").startswith(f"lint: ruff check .\ntest: pytest -q\n\n{self.MARKER}")
        )
        files = self.files()
        for name in install.ROOT_TEMPLATES:
            self.assertEqual(files[name], stored(self.template(name)), name)
        self.assertIn("[install] Bước làm tay từ CHANGELOG (3.7.1 (9433792) → t):\n", err)

    def test_infer_root_hashes_skips_missing_symlink_and_unreadable(self):
        old = self.target / ".xtemplates" / "framework" / "templates"
        self.assertEqual(install.infer_root_hashes(self.target), {})  # chưa cài
        old.mkdir(parents=True)
        (old / "AGENTS.md").write_text("---\na: 1\n---\n# a\n", encoding="utf-8")
        (old / "CLAUDE.md").write_bytes(b"\xff\xfe")  # không phải UTF-8
        (self.tmp / "ngoai.yaml").write_text("lint: x\n", encoding="utf-8")
        (old / "xt.yaml").symlink_to(self.tmp / "ngoai.yaml")  # symlink (kể cả trỏ file có thật) → không đọc
        self.assertEqual(install.infer_root_hashes(self.target), {"AGENTS.md": install.sha256(b"# a\n")})

    def test_upgrade_steps_from_real_changelog(self):
        """Nâng từ 3.5.0 (nhãn kèm SHA): CHANGELOG thật của khung → mỗi mục bản > 3.5.0 có bước in `[bản]` MỘT lần, rồi
        mỗi bước là MỘT dòng `- Dự án đích …` (mệnh đề tới hết câu, D-114), trước dòng "Xong."; mục ≤ 3.5.0 không in."""
        (self.target / ".xtemplates").mkdir()
        (self.target / ".xtemplates" / "VERSION").write_text("3.5.0 (abc)\n", encoding="utf-8")
        _, err = self.install_quiet()
        head = "[install] Bước làm tay từ CHANGELOG (3.5.0 (abc) → t):\n"
        self.assertIn(head, err)
        self.assertNotIn("Xong.", err.split(head, 1)[0])
        lines = err.split(head, 1)[1].split("[install] Xong.", 1)[0].splitlines()
        sections = [ln[len("[install]   [") : -1] for ln in lines if ln.startswith("[install]   [")]
        self.assertTrue(all(re.fullmatch(r"\[install\]   (\[[^]]+\]|- Dự án đích.*)", ln) for ln in lines), lines)
        self.assertEqual(len(sections), len(set(sections)))  # mỗi mục in [bản] một lần
        released = [s for s in sections if s != "Unreleased"]
        self.assertEqual(released[-7:], ["3.10.0", "3.9.0", "3.8.0", "3.7.1", "3.7.0", "3.6.0", "3.5.1"])
        self.assertTrue(all(tuple(map(int, s.split("."))) > (3, 5, 0) for s in released))
        # trích dẫn nhiều dòng của 3.8.0 → một dòng: bỏ `>` và `**` (ngoài mã), tới dấu chấm hết câu
        self.assertIn(
            "[install]   - Dự án đích khi nâng từ 3.7.x: chạy lại `install.py` (guard, `_lib.sh`, `pre-mcp-guard.sh`, "
            "matcher hook MCP trong `settings.json`, `xt.py`, mẫu, `.claude/agents/*.md` đổi).",
            lines,
        )
        self.assertFalse([ln for ln in lines if "khi nâng từ 3.4.1" in ln])  # bước của 3.5.0 (≤ bản đã cài)
        per_section: dict[str, list[str]] = {}
        for ln in lines:
            if ln.startswith("[install]   ["):
                current = per_section.setdefault(ln, [])
            else:
                current.append(ln)
        self.assertTrue(all(len(v) == len(set(v)) for v in per_section.values()))  # trùng hệt trong mục in một lần

    def test_upgrade_steps_clauses_versions_and_unicode(self):
        """Mệnh đề = từ "Dự án đích" tới hết câu (dấu chấm + khoảng trắng/hết khối; `1.` của danh sách không phải hết câu),
        khối nhiều dòng gộp một dòng (bỏ thụt lề, `>`, `**` ngoài mã); nhắc tên trong ngoặc bỏ qua; trùng hệt trong mục
        in một lần; mục ≤ đã cài, tiêu đề `## ` khác, dòng ngoài mục bỏ; NFD vẫn khớp (ra NFC); giữ thứ tự CHANGELOG."""
        text = "\n".join(
            [
                "# Changelog",
                "Dự án đích: dòng ngoài mục — không lấy.",
                "## [Unreleased]",
                "### Added",
                "- u1 **Dự án đích:** chạy lại `install.py`",
                "  (guard đổi). Câu sau không lấy.",
                "- u2 không có bước",
                "  nối tiếp u2",
                "- u3 **Dự án đích:** chạy lại `install.py` (guard đổi).",
                '- u5 in các bước "Dự án đích" của CHANGELOG. Dự án đích: chạy lại.',
                "- u6 Dự án đích: chép `.github/**/*.yml` vào **dự án**.",
                unicodedata.normalize("NFD", "u7 Dự án đích dạng tổ hợp"),
                "",
                "## [3.6.0] - 2026-01-02",
                "> **Dự án đích khi nâng từ 3.5.x:** chạy lại `install.py`",
                "> (guard). Guard chặn thêm.",
                "",
                "> **Dự án đích khi nâng từ 3.0.x:**",
                "> 1. Chạy lại `install.py`.",
                "> 2. Ghép lại.",
                "",
                "Đoạn p1 có Dự án đích: làm X",
                "p1 tiếp. Hết.",
                "",
                "    khối thụt lề, Dự án đích: Y",
                "    dòng hai",
                "## Ghi chú",
                "- n1 Dự án đích dưới tiêu đề lạ — không lấy.",
                "## [v3.5.1] - 2026-01-01",
                "Dự án đích: bản có tiền tố v.",
                "## [3.5.0] - 2026-01-01",
                "- c1 Dự án đích: bằng bản đã cài — không lấy.",
                "## [2.0.0]",
                "- d1 Dự án đích: cũ hơn — không lấy.",
            ]
        )
        unreleased = (
            "Unreleased",
            [
                "Dự án đích: chạy lại `install.py` (guard đổi).",
                "Dự án đích: chạy lại.",
                "Dự án đích: chép `.github/**/*.yml` vào dự án.",
                unicodedata.normalize("NFC", "Dự án đích dạng tổ hợp"),
            ],
        )
        self.assertEqual(
            install.upgrade_steps(text, (3, 5, 0)),
            [
                unreleased,
                (
                    "3.6.0",
                    [
                        "Dự án đích khi nâng từ 3.5.x: chạy lại `install.py` (guard).",
                        "Dự án đích khi nâng từ 3.0.x: 1. Chạy lại `install.py`.",
                        "Dự án đích: làm X p1 tiếp.",
                        "Dự án đích: Y dòng hai",
                    ],
                ),
                ("v3.5.1", ["Dự án đích: bản có tiền tố v."]),
            ],
        )
        self.assertEqual(install.upgrade_steps(text, (9, 0, 0)), [unreleased])
        self.assertEqual(
            install.text_blocks(["- a", "- b", "> q", "  q nối", "", "  c"]),
            [["- a"], ["- b"], ["> q", "  q nối"], ["  c"]],
        )

    def report(self, previous: str | None, version: str | None, changelog: bytes | None) -> str:
        """`report_upgrade_steps` với khung giả chỉ có VERSION/CHANGELOG (None = không có file)."""
        src = self.tmp / "khung-gia"
        shutil.rmtree(src, ignore_errors=True)
        src.mkdir()
        if version is not None:
            (src / "VERSION").write_text(version, encoding="utf-8")
        if changelog is not None:
            (src / "CHANGELOG.md").write_bytes(changelog)
        err = io.StringIO()
        with mock.patch.object(install, "SRC", src), redirect_stderr(err):
            install.report_upgrade_steps(previous, "mới")
        return err.getvalue()

    def test_upgrade_steps_skip_none_downgrade_and_unreadable(self):
        """Cài mới/nhãn lạ/VERSION hỏng → im lặng; nâng bản mà không có bước → "không có"; cài lại cùng bản không có
        bước → im lặng (review #191); hạ bản → một dòng; CHANGELOG thiếu hoặc không phải UTF-8 → một dòng, không lỗi
        (fail-open)."""
        log = "## [Unreleased]\n- a không có bước\n## [3.6.0]\n- b Dự án đích: chạy lại\n"
        for previous in (None, "", "nhãn-lạ", "v3"):
            self.assertEqual(self.report(previous, "3.6.0", log.encode()), "", previous)
        (self.target / ".xtemplates").mkdir()
        (self.target / ".xtemplates" / "VERSION").write_bytes(b"\xff\xfe3.5.0")
        self.assertIsNone(install.installed_label(self.target / ".xtemplates"))
        self.assertEqual(self.report("3.6.0 (abc)", "3.6.0", log.encode()), "")  # cài lại cùng bản: im lặng
        self.assertEqual(
            self.report("3.5.0 (abc)", "3.6.0", b"## [Unreleased]\n- a\n## [3.6.0]\n- b\n"),
            "[install] Bước làm tay từ CHANGELOG (3.5.0 (abc) → mới): không có\n",
        )
        out = self.report("3.5.0", None, log.encode())  # khung không có VERSION → không biết hạ bản, vẫn in
        self.assertEqual(out.splitlines()[1:], ["[install]   [3.6.0]", "[install]   - Dự án đích: chạy lại"])
        changelog = (
            "## [Unreleased]\n- a **Dự án đích:** chạy lại `install.py`.\n- b **Dự án đích:** chạy lại `install.py`.\n"
            "## [3.6.0] - 2026-01-02\n> **Dự án đích khi nâng từ 3.5.x:** chạy lại\n> `install.py` (guard). Thêm.\n"
        )
        self.assertEqual(  # dạng ra đầy đủ: tiêu đề, `[bản]` một lần mỗi mục, mỗi bước một dòng
            self.report("3.5.0 (abc)", "3.6.0", changelog.encode()),
            "[install] Bước làm tay từ CHANGELOG (3.5.0 (abc) → mới):\n"
            "[install]   [Unreleased]\n"
            "[install]   - Dự án đích: chạy lại `install.py`.\n"
            "[install]   [3.6.0]\n"
            "[install]   - Dự án đích khi nâng từ 3.5.x: chạy lại `install.py` (guard).\n",
        )
        out = self.report("v9.0.0", "3.6.0\n", log.encode())
        self.assertEqual(
            out,
            "[install] Bước làm tay từ CHANGELOG (v9.0.0 → mới): bỏ qua — bản khung 3.6.0 cũ hơn bản đã cài (hạ bản)\n",
        )
        for changelog in (None, b"## [3.6.0]\n- \xff Du an dich\n"):
            out = self.report("3.5.0", "3.6.0", changelog)
            self.assertEqual(len(out.splitlines()), 1, out)
            self.assertIn("(3.5.0 → mới): không đọc được CHANGELOG.md của khung", out)

    def test_xt_yaml_new_keys_appended_as_comments_idempotent(self):
        """xt.yaml của dự án (`kept-own`): khoá của mẫu mà dự án chưa có (`khoá:` lẫn `# khoá:`) nối cuối file dạng chú
        thích sau MỘT dòng đánh dấu; dòng cũ giữ nguyên byte; khoá có hiệu lực không đổi; `--plan` chỉ báo; cài lần hai
        không nối thêm."""
        self.install_quiet()
        y = self.target / "xt.yaml"
        own = 'lint: ruff check .\ntest: "pytest -q"\n#delivery_phase: harden\n'
        y.write_text(own, encoding="utf-8")
        template = self.template("xt.yaml").decode("utf-8")
        tmpl = {m[1]: ln for ln in template.splitlines() if (m := re.match(r"([a-z0-9_]+):", ln))}
        expected = [k for k in tmpl if k not in ("lint", "test", "delivery_phase")]
        self.assertIn("e2e_affected", expected)  # khoá có chữ số cũng là khoá của mẫu
        entry = self.plan()["xt.yaml"]
        self.assertEqual((entry["action"], entry["keys_add"]), ("kept-own", expected))
        self.assertEqual(y.read_text(encoding="utf-8"), own)  # --plan không ghi
        _, err = self.install_quiet()
        text = y.read_text(encoding="utf-8")
        self.assertTrue(text.startswith(own), text[:120])
        self.assertEqual(text[len(own) :].splitlines(), ["", self.MARKER, *(f"# {tmpl[k]}" for k in expected)])
        self.assertIn(f"xt.yaml: nối {len(expected)} khoá mới của khung dạng chú thích ({', '.join(expected)})", err)
        self.assertEqual(set(xt._yaml_keys(text)), {"lint", "test"})  # vắng khoá = hành vi cũ
        self.assertFalse(y.with_name("xt.yaml.xtemplates-new").exists())
        _, err = self.install_quiet()
        self.assertEqual(y.read_text(encoding="utf-8"), text)
        self.assertNotIn("khoá mới của khung dạng chú thích", err)
        self.assertEqual(self.plan()["xt.yaml"]["keys_add"], [])

    def test_xt_yaml_keys_crlf_updated_new_and_unreadable(self):
        """Mẫu đổi + xt.yaml của dự án (`updated-new`): vừa `.xtemplates-new` vừa nối khoá; giữ CRLF và dòng cuối thiếu
        xuống dòng; lần sau `kept-own` không nối thêm. Không phải UTF-8 → log, không ghi; lỗi ghi → log (fail-open)."""
        self.install_quiet()
        y = self.target / "xt.yaml"
        y.write_bytes(b"lint: x\r\ntest: y")
        self.set_installed_hash("xt.yaml", b'lint: ""\n')
        _, err = self.install_quiet()
        self.assertTrue(y.with_name("xt.yaml.xtemplates-new").exists())
        data = y.read_bytes()
        self.assertTrue(data.startswith(b"lint: x\r\ntest: y\r\n\r\n" + self.MARKER.encode() + b"\r\n# "), data[:80])
        self.assertTrue(data.endswith(b"\r\n"))
        self.assertNotIn(b"\n", data.replace(b"\r\n", b""))
        self.assertEqual(self.files()["xt.yaml"], stored(self.template("xt.yaml")))  # hash mẫu MỚI
        _, err = self.install_quiet()
        self.assertEqual(y.read_bytes(), data)
        self.assertIn("xt.yaml: kept-own", err)
        y.write_bytes(b"lint: \xff\n")
        self.assertEqual(self.plan()["xt.yaml"], {"path": "xt.yaml", "action": "kept-own", "keys_add": []})
        _, err = self.install_quiet()
        self.assertEqual(y.read_bytes(), b"lint: \xff\n")
        self.assertIn("⚠ xt.yaml: không đọc được", err)
        y.write_bytes(b"")
        real_open = Path.open

        def no_append(path, mode="r", *a, **k):
            if mode == "ab":
                raise OSError("đĩa đầy")
            return real_open(path, mode, *a, **k)

        err_io = io.StringIO()
        with mock.patch.object(Path, "open", no_append), redirect_stderr(err_io):
            install.append_yaml_keys(y, 'lint: ""\n', "t")
        self.assertEqual(y.read_bytes(), b"")
        self.assertIn("⚠ xt.yaml: không nối được khoá mới của khung (đĩa đầy)", err_io.getvalue())

    def test_yaml_block_layout(self):
        marker = self.MARKER
        self.assertEqual(install.yaml_block("", ["a: 1"], "t"), f"{marker}\n# a: 1\n")
        self.assertEqual(install.yaml_block("x: 1\n", ["a: 1"], "t"), f"\n{marker}\n# a: 1\n")
        self.assertEqual(install.yaml_block("x: 1", ["a: 1", "b: 2"], "t"), f"\n\n{marker}\n# a: 1\n# b: 2\n")
        self.assertEqual(install.yaml_block("x: 1\r\n", ["a: 1"], "t"), f"\r\n{marker}\r\n# a: 1\r\n")
        self.assertEqual(install.missing_yaml_keys("a: 1\n# b: 2\nc: 3\nc: 4\n", "# a: x\n  c: y\n"), [("c", "c: 3")])


class CheckLinksTest(unittest.TestCase):
    def test_repo_links_ok(self):
        r = subprocess.run([sys.executable, str(ROOT / "scripts" / "check-links.py")], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_detects_broken(self):
        tmp = Path(self.enterContext(tempfile.TemporaryDirectory()))
        (tmp / "a.md").write_text(
            "[x](b.md) [ok](#h) [url](https://x) `[no](c.md)`\n```\n[in-fence](d.md)\n```\n", encoding="utf-8"
        )
        r = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "check-links.py"), str(tmp)], capture_output=True, text=True
        )
        self.assertEqual(r.returncode, 1)
        self.assertIn("b.md", r.stdout)
        self.assertNotIn("d.md", r.stdout)


if __name__ == "__main__":
    unittest.main()
