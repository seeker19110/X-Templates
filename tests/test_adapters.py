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


# Hình payload theo host (nghiên cứu 2026-11-02 §9): (khoá tên tool, khoá tham số), tên tool shell/ghi/MCP, khoá phiên.
KEYS = {"copilot": ("toolName", "toolArgs"), "grok": ("toolName", "toolInput"), "opencode": ("tool", "args")}
SHELL_NAME = {
    "gemini": "run_shell_command",
    "cursor": "Shell",
    "copilot": "bash",
    "grok": "run_terminal_command",
    "opencode": "bash",
}
WRITE_NAME = {
    "gemini": "write_file",
    "cursor": "Write",
    "copilot": "create",
    "grok": "search_replace",
    "opencode": "write",
}
# OpenCode đặt tên MCP `<server>_<tool>` (docs OpenCode mcp-servers, đọc 2026-11-02) — review #411: bảng cũ dùng
# `mcp__github__…` mà OpenCode không phát nên ca "mcp merge" xanh không chứng minh gì.
MCP_NAME = {
    "gemini": "mcp_github_{}",
    "cursor": "MCP:{}",
    "grok": "github__{}",
    "copilot": "github__{}",
    "opencode": "github_{}",
}
SESSION_KEY = {"codex": "session_id", "copilot": "sessionId", "grok": "sessionId", "opencode": "sessionID"}


def _event(host: str, name: str, args: dict, cwd: str) -> dict:
    tool_key, args_key = KEYS.get(host, ("tool_name", "tool_input"))
    return {tool_key: name, args_key: args, "cwd": cwd}


def _shell(host: str, cmd: str, cwd: str) -> dict:
    args = {"command": cmd} | ({"working_directory": cwd} if host == "cursor" else {})
    ev = _event(host, SHELL_NAME.get(host, "Bash"), args, cwd)
    if host in SESSION_KEY:
        ev[SESSION_KEY[host]] = "s"
    return ev


def _write(host: str, path: Path, cwd: str) -> dict:
    if host == "codex":
        patch = f"*** Begin Patch\n*** Add File: {path.relative_to(ROOT)}\n+x\n*** End Patch\n"
        return _event(host, "apply_patch", {"command": patch}, cwd)
    key = "filePath" if host == "opencode" else "file_path"
    return _event(host, WRITE_NAME.get(host, "Write"), {key: str(path), "content": "x"}, cwd)


def _mcp(host: str, tool: str, cwd: str) -> dict:
    name = MCP_NAME.get(host, "mcp__github__{}").format(tool)
    return _event(host, name, {"owner": "o", "repo": "r", "pullNumber": 1}, cwd)


def payloads(host: str) -> list[tuple[str, dict, bool]]:
    """(tên ca, payload của host, phải chặn?) — ≥ 10 ca mỗi host: lệnh nguy hiểm, ghi bí mật/sổ, MCP merge, và đối chứng."""
    cwd = str(ROOT)
    return [
        ("push main", _shell(host, "git push origin main", cwd), True),
        ("rm home", _shell(host, "rm -rf ~", cwd), True),
        ("no-verify", _shell(host, "git commit --no-verify -m x", cwd), True),
        ("auto-merge", _shell(host, "gh pr merge 5 --auto", cwd), True),
        ("ghi .env", _write(host, ENV, cwd), True),
        ("ghi sổ autopilot", _write(host, LEDGER, cwd), True),
        ("mcp merge", _mcp(host, "merge_pull_request", cwd), True),
        ("ls", _shell(host, "ls -la", cwd), False),
        ("git status", _shell(host, "git status", cwd), False),
        ("ghi tài liệu", _write(host, NOTES, cwd), False),
        ("mcp đọc", _mcp(host, "get_file_contents", cwd), False),
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
        self.assertEqual(ad.to_core("cursor", "Delete", {}, "/w", "/w")[0]["tool"], ad.UNPARSED)  # AUD-SEC-351
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

    def test_broken_guard_denies_on_every_host(self):
        """Review #411 🔴: guard của dự án không nạp được (SyntaxError, ImportError…) hay lõi ném lỗi ngoài luật → deny
        tường minh theo giao thức host (Codex/Gemini/Grok/OpenCode coi lỗi hook là cho qua), không traceback."""

        def broken(_root: str) -> None:
            raise SyntaxError("guard.py hỏng")

        for host in ad.HOSTS:
            with self.subTest(host=host):
                raw = payloads(host)[7][1]  # "ls": lệnh vô hại vẫn bị chặn khi không có luật để áp
                out, code = ad.run(host, raw, broken)
                self.assertTrue(verdict(host, out, code), (host, out))
                self.assertIn("BROKEN_GUARD", out)
        g = ad.load_guard(str(ROOT))
        assert g is not None
        with (
            mock.patch.object(g, "_failure_decision", side_effect=RuntimeError("hỏng nốt")),
            mock.patch.object(g, "_core_decision", side_effect=RuntimeError("hỏng")),
        ):
            out, code = ad.run("codex", payloads("codex")[7][1], lambda r: g)
        self.assertTrue(verdict("codex", out, code), out)

    def test_unparsed_shell_or_edit_denies(self):
        """AUD-SEC-351 (nợ review #411): tool shell/ghi mà adapter không trích được lệnh/đường (khoá đối số lệch) → deny
        UNPARSED, không cho qua im lặng; khoá thay thế đã biết (`cmd`, `file`, `filename`, `paths`, `patch`) được đọc."""
        cwd = str(ROOT)
        for host, raw in (
            ("grok", {"toolName": "run_terminal_command", "toolInput": {"cwd": cwd}}),
            ("cursor", {"tool_name": "Delete", "tool_input": {}}),
            ("copilot", {"toolName": "edit", "toolArgs": {"old_str": "a", "new_str": "b"}}),
            ("codex", {"tool_name": "exec_command", "tool_input": {"command": ""}}),
            ("codex", {"tool_name": "apply_patch", "tool_input": {"input": "không phải patch"}}),
            ("gemini", {"tool_name": "write_file", "tool_input": {"content": "x"}}),
        ):
            with self.subTest(host=host, raw=raw):
                out, code = ad.run(host, {**raw, "cwd": cwd})
                self.assertTrue(verdict(host, out, code), out)
                self.assertIn("UNPARSED", out)
        for host, raw, deny in (
            ("grok", {"toolName": "run_terminal_command", "toolInput": {"cmd": "rm -rf ~"}}, True),
            ("grok", {"toolName": "run_terminal_command", "toolInput": {"cmd": "ls -la"}}, False),
            ("codex", {"tool_name": "exec_command", "tool_input": {"cmd": "git push origin main"}}, True),
            ("grok", {"toolName": "search_replace", "toolInput": {"file": str(ENV)}}, True),
            ("copilot", {"toolName": "edit", "toolArgs": {"filename": str(LEDGER)}}, True),
            ("copilot", {"toolName": "edit", "toolArgs": {"filename": str(NOTES)}}, False),
            ("cursor", {"tool_name": "Delete", "tool_input": {"paths": [str(NOTES), str(ENV)]}}, True),
            ("cursor", {"tool_name": "Delete", "tool_input": {"paths": [str(NOTES)]}}, False),
            ("codex", {"tool_name": "apply_patch", "tool_input": {"patch": "*** Add File: .env\n+x\n"}}, True),
            ("codex", {"tool_name": "apply_patch", "tool_input": {"patch": "*** Add File: a.md\n+x\n"}}, False),
        ):
            with self.subTest(host=host, raw=raw):
                out, code = ad.run(host, {**raw, "cwd": cwd})
                self.assertEqual(verdict(host, out, code), deny, out)

    def test_push_no_verify_denied(self):
        """AUD-SEC-352 (nợ review #411): `git push --no-verify` bỏ sàn git hook `pre-push` (nhánh chính, xoá nhánh từ xa)
        như `commit --no-verify` → deny NO_VERIFY ở mọi host; push thường và `push -n` (thử) vẫn chạy."""
        for host in ad.HOSTS:
            for cmd, deny in (
                ("git push --no-verify origin :feat", True),
                ("git push origin feat --no-verify", True),
                ("git -c core.hooksPath=/dev/null push origin feat", True),
                ("git push --no-veri origin feat", True),
                ("cd /tmp && git push --no-verify origin feat", True),
                ("bash -c 'git push --no-verify origin feat'", True),
                # AUD-SEC-352 (review lượt 2): git đọc `-c` từ biến này (`git config --get core.hooksPath` in /dev/null)
                ("GIT_CONFIG_PARAMETERS=\"'core.hooksPath'='/dev/null'\" git push origin :feat", True),
                ("GIT_CONFIG_PARAMETERS=\"'CORE.HOOKSPATH'='/x'\" git push origin feat", True),
                ("GIT_CONFIG_PARAMETERS=\"'core.hooksPath'='/dev/null'\" git commit -m x", True),
                ("GIT_CONFIG_PARAMETERS=\"'user.name'='x'\" git push origin feat", False),
                ("git push origin feat", False),
                ("git push -n origin feat", False),
                # sau `--` là refspec, không phải cờ; đích ghi rõ — không refspec thì guard lấy nhánh hiện tại (CI checkout
                # khác máy dev, từng đỏ ở py311 #420)
                ("git push origin feat -- --no-verify", False),
            ):
                with self.subTest(host=host, cmd=cmd):
                    out, code = ad.run(host, _shell(host, cmd, str(ROOT)))
                    self.assertEqual(verdict(host, out, code), deny, out)
                    if deny:
                        self.assertIn("NO_VERIFY", out)

    def test_config_env_hooks_path_denied(self):
        """AUD-SEC-383/389 (review #420): `git --config-env=core.hooksPath=HOME push|commit` — dạng `=` dính liền — git
        nhận như `-c core.hooksPath=$HOME` nên bỏ git hook như `--no-verify`; khoá khác qua `--config-env=` vẫn chạy."""
        for host in ad.HOSTS:
            for cmd, deny in (
                ("git --config-env=core.hooksPath=HOME push origin feat", True),
                ("git --config-env=CORE.HOOKSPATH=HOME push origin feat", True),
                ("git --config-env=core.hooksPath=HOME commit -m x", True),
                ("git --config-env core.hooksPath=HOME commit -m x", True),
                ("git --config-env=user.name=USER push origin feat", False),
                ("git --config-env=user.name=USER commit -m x", False),
            ):
                with self.subTest(host=host, cmd=cmd):
                    out, code = ad.run(host, _shell(host, cmd, str(ROOT)))
                    self.assertEqual(verdict(host, out, code), deny, out)
                    if deny:
                        self.assertIn("NO_VERIFY", out)

    def test_opencode_mcp_names(self):
        self.assertEqual(ad.mcp_name("opencode", "github_merge_pull_request"), "mcp__github__merge_pull_request")
        self.assertEqual(ad.mcp_name("opencode", "_github_get_me_"), "mcp__github__get_me")
        self.assertIsNone(ad.mcp_name("opencode", "todowrite"))

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

    # CI đặt XT_REQUIRE_BUN=1 (job `test` cài bun ghim sha256): thiếu bun ở đó là đỏ, không skip (AUD-TEST-056).
    @unittest.skipIf(
        shutil.which("bun") is None and not os.environ.get("XT_REQUIRE_BUN"), "cần bun để chạy plugin OpenCode"
    )
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
