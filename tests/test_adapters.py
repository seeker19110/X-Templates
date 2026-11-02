"""Adapter hook cho công cụ agent khác (ADR-0064 lát B, T-3642…3644): `scripts/xt_adapter.py <host>` đổi payload của host
sang schema trung lập của guard rồi trả quyết định theo giao thức chặn của host. Payload theo docs/schema chính chủ đọc
2026-11-02 (research §9): Codex `tool_name`/`tool_input`, Gemini `run_shell_command`/`write_file`, Cursor `Shell`/
`Write`/`MCP:<tool>`, Copilot camelCase `toolName`/`toolArgs`, Grok `toolName`/`toolInput`, OpenCode `tool`/`args`."""

from __future__ import annotations

import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import unittest.mock as mock
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import install
import xt_adapter as ad

ENV = ROOT / ".env"
LEDGER = ROOT / ".autopilot" / "state.json"
NOTES = ROOT / "docs" / "notes-khong-co.md"


def payloads(host: str) -> list[tuple[str, dict, bool]]:
    """(tên ca, payload của host, phải chặn?) — ≥ 10 ca mỗi host: lệnh nguy hiểm, ghi bí mật/sổ, MCP merge, và đối chứng."""
    cwd = str(ROOT)

    def shell(cmd: str) -> dict:
        if host == "gemini":
            return {"tool_name": "run_shell_command", "tool_input": {"command": cmd}, "cwd": cwd}
        if host == "cursor":
            return {"tool_name": "Shell", "tool_input": {"command": cmd, "working_directory": cwd}, "cwd": cwd}
        if host == "copilot":
            return {"toolName": "bash", "toolArgs": {"command": cmd}, "cwd": cwd, "sessionId": "s"}
        if host == "grok":
            return {"toolName": "run_terminal_command", "toolInput": {"command": cmd}, "cwd": cwd, "sessionId": "s"}
        if host == "opencode":
            return {"tool": "bash", "args": {"command": cmd}, "cwd": cwd, "sessionID": "s"}
        return {"tool_name": "Bash", "tool_input": {"command": cmd}, "cwd": cwd, "session_id": "s"}

    def write(path: Path) -> dict:
        name = {"gemini": "write_file", "cursor": "Write", "copilot": "create", "grok": "search_replace"}.get(
            host, "Write"
        )
        if host == "opencode":
            return {"tool": "write", "args": {"filePath": str(path), "content": "x"}, "cwd": cwd}
        if host == "codex":
            patch = f"*** Begin Patch\n*** Add File: {path.relative_to(ROOT)}\n+x\n*** End Patch\n"
            return {"tool_name": "apply_patch", "tool_input": {"command": patch}, "cwd": cwd}
        key = "toolArgs" if host == "copilot" else "toolInput" if host == "grok" else "tool_input"
        tool_key = "toolName" if host in ("copilot", "grok") else "tool_name"
        return {tool_key: name, key: {"file_path": str(path), "content": "x"}, "cwd": cwd}

    def mcp(tool: str) -> dict:
        name = {
            "gemini": f"mcp_github_{tool}",
            "cursor": f"MCP:{tool}",
            "grok": f"github__{tool}",
            "copilot": f"github__{tool}",
            "opencode": f"mcp__github__{tool}",
        }.get(host, f"mcp__github__{tool}")
        if host == "opencode":
            return {"tool": name, "args": {"owner": "o", "repo": "r", "pullNumber": 1}, "cwd": cwd}
        tool_key = "toolName" if host in ("copilot", "grok") else "tool_name"
        key = "toolArgs" if host == "copilot" else "toolInput" if host == "grok" else "tool_input"
        return {tool_key: name, key: {"owner": "o", "repo": "r", "pullNumber": 1}, "cwd": cwd}

    return [
        ("push main", shell("git push origin main"), True),
        ("rm home", shell("rm -rf ~"), True),
        ("no-verify", shell("git commit --no-verify -m x"), True),
        ("auto-merge", shell("gh pr merge 5 --auto"), True),
        ("ghi .env", write(ENV), True),
        ("ghi sổ autopilot", write(LEDGER), True),
        ("mcp merge", mcp("merge_pull_request"), True),
        ("ls", shell("ls -la"), False),
        ("git status", shell("git status"), False),
        ("ghi tài liệu", write(NOTES), False),
        ("mcp đọc", mcp("get_file_contents"), False),
    ]


def verdict(host: str, out: str, code: int) -> bool:
    """Host có chặn theo output này không (đúng giao thức từng host)."""
    doc = json.loads(out) if out else {}
    if host == "codex":
        return doc.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"
    if host == "cursor":
        return doc["permission"] == "deny"
    if host == "copilot":
        return doc.get("permissionDecision") == "deny" or code == 2
    return doc.get("decision") == "deny"


class AdapterHostTest(unittest.TestCase):
    def test_every_host_blocks_and_allows(self):
        for host in ad.HOSTS:
            for name, raw, deny in payloads(host):
                with self.subTest(host=host, case=name):
                    out, code = ad.run(host, raw)
                    self.assertEqual(code, 0)
                    self.assertEqual(verdict(host, out, code), deny, out)
                    if deny:
                        self.assertIn("[", out)  # lý do kèm mã guard để người đọc biết luật nào

    def test_render_allow_shapes(self):
        self.assertEqual(ad.render("cursor", False, ""), ('{"permission": "allow"}', 0))  # JSON hỏng = Cursor chặn
        self.assertEqual(ad.render("gemini", False, ""), ('{"decision": "allow"}', 0))
        for host in ("codex", "copilot", "grok", "opencode"):
            self.assertEqual(ad.render(host, False, ""), ("", 0))

    def test_parse_variants(self):
        tool, args, cwd, session = ad.parse(
            "copilot", {"toolName": "bash", "toolArgs": '{"command": "ls"}', "sessionId": "x"}
        )
        self.assertEqual((tool, args, session), ("bash", {"command": "ls"}, "x"))
        self.assertEqual(ad.parse("copilot", {"toolName": "bash", "toolArgs": "ls -la"})[1], {"command": "ls -la"})
        self.assertEqual(ad.parse("cursor", {"tool_name": "Shell", "workspace_roots": ["/w"]})[2], "/w")
        self.assertEqual(ad.parse("codex", [1])[0], "")
        self.assertEqual(ad.mcp_name("codex", "Bash"), None)
        self.assertEqual(ad.mcp_name("gemini", "mcp_x"), None)  # không có tool sau server

    def test_patch_checks_every_file(self):
        patch = "*** Begin Patch\n*** Update File: README.md\n*** Add File: .env\n*** End Patch\n"
        out, _ = ad.run("codex", {"tool_name": "apply_patch", "tool_input": {"command": patch}, "cwd": str(ROOT)})
        self.assertTrue(verdict("codex", out, 0))
        cores = ad.to_core("codex", "apply_patch", {"command": patch}, str(ROOT), str(ROOT))
        self.assertEqual([c["path"] for c in cores], [str(ROOT / "README.md"), str(ROOT / ".env")])
        self.assertEqual(ad.to_core("cursor", "Delete", {}, "/w", "/w")[0]["path"], "")
        self.assertEqual(ad.to_core("cursor", "Read", {"file_path": "x"}, "/w", "/w"), [])  # đọc: không xét

    def test_no_guard_allows_and_rule_error_fails_open_except_merge(self):
        self.assertEqual(
            ad.run("grok", {"toolName": "Bash", "toolInput": {"command": "rm -rf ~"}}, lambda r: None), ("", 0)
        )
        g = ad.load_guard(str(ROOT))
        assert g is not None
        with mock.patch.object(g, "_core_decision", side_effect=RuntimeError("hỏng")):
            self.assertFalse(ad.decide(g, [{"tool": "bash", "command": "ls"}])[0])
            self.assertTrue(ad.decide(g, [{"tool": "bash", "command": "gh pr merge 5"}])[0])
        self.assertIsNone(ad.load_guard(tempfile.gettempdir()))

    def test_project_root_outside_git(self):
        tmp = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.assertEqual(ad.project_root(str(tmp)), str(tmp))
        with mock.patch.object(ad.subprocess, "run", side_effect=OSError("không có git")):
            self.assertEqual(ad.project_root(str(ROOT)), str(ROOT))

    def test_cli(self):
        r = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "xt_adapter.py"), "codex"],
            input=json.dumps(
                {"tool_name": "Bash", "tool_input": {"command": "git push origin main"}, "cwd": str(ROOT)}
            ),
            capture_output=True,
            text=True,
        )
        self.assertEqual(r.returncode, 0)
        self.assertTrue(verdict("codex", r.stdout, 0))
        err = io.StringIO()
        with redirect_stderr(err):
            self.assertEqual(ad.main(["lạ"]), 2)
        self.assertIn("host phải là", err.getvalue())
        out = io.StringIO()
        with mock.patch.object(sys, "stdin", io.StringIO("{hỏng")), redirect_stdout(out):
            self.assertEqual(ad.main(["cursor"]), 0)
        self.assertEqual(json.loads(out.getvalue()), {"permission": "allow"})
        with mock.patch.object(sys, "argv", ["xt_adapter.py"]), redirect_stderr(io.StringIO()):
            self.assertEqual(ad.main(), 2)

    @unittest.skipIf(shutil.which("bun") is None, "cần bun để chạy plugin OpenCode")
    def test_opencode_plugin_throws_on_deny(self):
        work = Path(self.enterContext(tempfile.TemporaryDirectory()))
        (work / ".xtemplates" / "scripts").mkdir(parents=True)
        (work / ".claude" / "hooks").mkdir(parents=True)
        os.symlink(ROOT / "scripts" / "xt_adapter.py", work / ".xtemplates" / "scripts" / "xt_adapter.py")
        os.symlink(ROOT / ".claude" / "hooks" / "guard.py", work / ".claude" / "hooks" / "guard.py")
        plugin = ROOT / "framework" / "templates" / "harness" / "opencode-xt.ts"
        script = work / "run.ts"
        script.write_text(
            f'import {{ XtGuard }} from "{plugin}"\n'
            f'const h = await XtGuard({{ $: Bun.$, worktree: "{work}" }} as any)\n'
            "const call = (cmd: string) => h['tool.execute.before']!({ tool: 'bash', sessionID: 's', callID: 'c' }, { args: { command: cmd } } as any)\n"
            "await call('ls -la')\n"
            "try { await call('git push origin main'); console.log('ALLOWED') } catch (e) { console.log('DENIED ' + (e as Error).message) }\n",
            encoding="utf-8",
        )
        r = subprocess.run(["bun", str(script)], capture_output=True, text=True, timeout=120, cwd=work)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("DENIED", r.stdout)
        self.assertIn("PUSH_MAIN", r.stdout)


class InstallAdaptersTest(unittest.TestCase):
    def setUp(self):
        self.target = Path(self.enterContext(tempfile.TemporaryDirectory())).resolve()

    def install(self, *args: str) -> tuple[int, str]:
        err = io.StringIO()
        with redirect_stderr(err):
            rc = install.main([str(self.target), "--label", "t", *args])
        return rc, err.getvalue()

    def test_harness_flag_copies_every_host_and_merges_gemini(self):
        gem = self.target / ".gemini" / "settings.json"
        gem.parent.mkdir()
        gem.write_text(
            json.dumps({"theme": "x", "hooks": {"BeforeTool": [{"matcher": "a", "hooks": []}]}}), encoding="utf-8"
        )
        rc, out = self.install("--harness", ",".join(install.ADAPTERS))
        self.assertEqual(rc, 0, out)
        for host, (_, rel) in install.ADAPTERS.items():
            with self.subTest(host=host):
                self.assertTrue((self.target / rel).is_file())
                self.assertIn(f"adapter {host}:", out)
        data = json.loads(gem.read_text(encoding="utf-8"))
        self.assertEqual(data["theme"], "x")
        self.assertEqual([e["matcher"] for e in data["hooks"]["BeforeTool"]][0], "a")
        self.assertEqual(json.dumps(data).count("xt-guard"), 1)
        self.install("--harness", "gemini")  # cài lại: thay bản của khung, không nhân đôi
        self.assertEqual(gem.read_text(encoding="utf-8").count("xt-guard"), 1)
        self.assertTrue((self.target / ".xtemplates" / "scripts" / "xt_adapter.py").is_file())

    def test_bad_host_gemini_unreadable_and_no_harness_warning(self):
        rc, out = self.install("--harness", "codex,lạ")
        self.assertEqual(rc, 2)
        self.assertIn("không biết lạ", out)
        gem = self.target / ".gemini" / "settings.json"
        gem.parent.mkdir()
        gem.write_text("{hỏng", encoding="utf-8")
        rc, out = self.install("--no-harness", "--harness", "gemini")
        self.assertEqual(rc, 0)
        self.assertIn("adapter gemini: .gemini/settings.json (kept)", out)
        self.assertIn("adapter cần harness", out)
        self.assertEqual(gem.read_text(encoding="utf-8"), "{hỏng")
        gem.write_text(json.dumps({"hooks": "lạ"}), encoding="utf-8")
        self.assertIn("(kept)", self.install("--harness", "gemini")[1])


if __name__ == "__main__":
    unittest.main()
