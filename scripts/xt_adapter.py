#!/usr/bin/env python3
"""Adapter hook cho công cụ agent khác Claude Code (ADR-0064 lát B): `xt_adapter.py codex|gemini|cursor|copilot|grok|
opencode`. Đọc payload của host ở stdin, đổi sang schema trung lập của guard (`{tool, command|path|tool_name, input, cwd,
project_dir}`), chạy bộ luật của guard TRONG tiến trình (nạp `.claude/hooks/guard.py` của dự án từ nguồn, như `py_run` —
AUD-SEC-074), rồi trả quyết định theo giao thức của host. Payload và giao thức từng host: research 2026-11-02 §9.

Lời gọi sửa nhiều file (Codex `apply_patch`) xét từng file — một file bị chặn là chặn cả lời gọi. Không có guard (dự án
chưa cài harness) → cho qua. Lỗi giữa chừng → `_failure_decision` của guard (fail-open về luồng, merge thì chặn —
ADR-0002, AUD-SEC-032).
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import types
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

Core = Dict[str, Any]

# Tên tool của host → chế độ của guard. Khoá chữ thường; không có ở đây và không phải MCP → không xét (cho qua).
SHELL_TOOLS = {"bash", "shell", "run_shell_command", "run_terminal_command", "exec_command", "powershell"}
EDIT_TOOLS = {
    *("edit", "write", "multiedit", "write_file", "replace", "create", "search_replace", "str_replace_editor"),
    *("delete", "notebookedit"),
}
PATCH_TOOLS = {"apply_patch"}  # Codex, OpenCode: đường file nằm trong thân patch
PATCH_PATH_RE = re.compile(r"^\*\*\* (?:Add File|Update File|Delete File|Move to): (.+?)\s*$", re.M)
PATH_KEYS = ("file_path", "filePath", "path", "target_file")
HOSTS = ("codex", "gemini", "cursor", "copilot", "grok", "opencode")


def project_root(cwd: str) -> str:
    """Gốc repo git chứa `cwd` (host chạy hook ở thư mục làm việc của phiên); không phải repo → `cwd`."""
    try:
        r = subprocess.run(
            ["git", "-C", cwd, "rev-parse", "--show-toplevel"], capture_output=True, text=True, timeout=10
        )
    except (OSError, subprocess.SubprocessError):
        return cwd
    return r.stdout.strip() if r.returncode == 0 and r.stdout.strip() else cwd


def load_guard(root: str) -> Optional[types.ModuleType]:
    """`<root>/.claude/hooks/guard.py` biên dịch từ nguồn mỗi lần (không pyc — AUD-SEC-074); không có → None."""
    p = Path(root) / ".claude" / "hooks" / "guard.py"
    if not p.is_file():
        return None
    m = types.ModuleType("guard")
    m.__file__ = str(p)
    sys.modules["guard"] = m
    exec(compile(p.read_bytes(), str(p), "exec", dont_inherit=True), m.__dict__)
    return m


def mcp_name(host: str, name: str) -> Optional[str]:
    """Tên MCP của host → `mcp__<server>__<tool>` mà luật MCP của guard đọc; không phải MCP → None. Gemini
    `mcp_<server>_<tool>` tách ở `_` đầu (server có `_` thì tách sai — giới hạn đã biết); Cursor `MCP:<tool>` không nêu
    server; Grok `server__tool` không tiền tố."""
    if name.startswith("mcp__"):
        return name
    if name.startswith("MCP:"):
        return f"mcp__{host}__{name[4:]}"
    if host == "gemini" and name.startswith("mcp_") and "_" in name[4:]:
        server, _, tool = name[4:].partition("_")
        return f"mcp__{server}__{tool}"
    if host in ("grok", "copilot") and "__" in name.strip("_"):
        return f"mcp__{name}"
    return None


def _paths(args: Dict[str, Any]) -> List[str]:
    return [v for k in PATH_KEYS for v in [args.get(k)] if isinstance(v, str) and v]


def to_core(host: str, tool: str, args: Any, cwd: str, root: str) -> List[Core]:
    """Một lời gọi tool của host → các payload trung lập cần xét (rỗng = không có gì để chặn)."""
    args = args if isinstance(args, dict) else {}
    base: Core = {"cwd": cwd, "project_dir": root}
    low = tool.lower()
    if low in SHELL_TOOLS:
        return [{**base, "tool": "bash", "command": args.get("command")}]
    if low in PATCH_TOOLS:
        text = args.get("command") or args.get("patchText") or args.get("input") or ""
        return [{**base, "tool": "edit", "path": os.path.join(cwd, p)} for p in PATCH_PATH_RE.findall(str(text))]
    if low in EDIT_TOOLS:
        return [{**base, "tool": "edit", "path": p, "input": args} for p in _paths(args)] or [
            {**base, "tool": "edit", "path": "", "input": args}
        ]
    name = mcp_name(host, tool)
    return [{**base, "tool": "mcp", "tool_name": name, "input": args}] if name else []


def parse(host: str, raw: Any) -> Tuple[str, Any, str, str]:
    """(tool, args, cwd, phiên) từ payload của host. Copilot camelCase (`toolName`/`toolArgs`), Grok (`toolName`/
    `toolInput`), OpenCode (`tool`/`args` do plugin dựng); còn lại kiểu Claude (`tool_name`/`tool_input`)."""
    raw = raw if isinstance(raw, dict) else {}
    tool = raw.get("tool_name") or raw.get("toolName") or raw.get("tool") or ""
    args = raw.get("tool_input", raw.get("toolInput", raw.get("toolArgs", raw.get("args"))))
    if isinstance(args, str):  # Copilot/Cursor có lúc gửi chuỗi JSON
        try:
            args = json.loads(args)
        except ValueError:
            args = {"command": args}
    cwd = raw.get("cwd") or raw.get("workspaceRoot") or (raw.get("workspace_roots") or [""])[0] or os.getcwd()
    session = raw.get("session_id") or raw.get("sessionId") or raw.get("conversation_id") or raw.get("sessionID") or ""
    return str(tool), args, str(cwd), str(session)


def decide(guard: types.ModuleType, cores: List[Core]) -> Tuple[bool, str, str]:
    """(chặn?, mã, lý do) — chặn ngay ở payload đầu tiên bị deny."""
    for core in cores:
        try:
            out = guard.apply_policy(guard._core_decision(core))
        except Exception:  # bộ luật lỗi giữa chừng: như guard.main — fail-open trừ merge
            mode = "bash" if core["tool"] == "bash" else core["tool"]
            payload = {"tool_name": core.get("tool_name"), "tool_input": {"command": core.get("command")}}
            out = guard.apply_policy(guard._failure_decision(mode, payload, str(core.get("command") or "")))
        if out.get("decision") == "deny":
            return True, str(out.get("code") or ""), str(out.get("reason") or "")
        if out.get("commit") and out.get("no_verify"):  # Claude Code: hook Bash tự chạy cổng; host khác chỉ có git hook
            why = "`git commit --no-verify` bỏ qua sàn git hook — host này không có cổng commit của hook Claude (ADR-0064 lát C)"
            return True, "NO_VERIFY", why
    return False, "", ""


def render(host: str, deny: bool, reason: str) -> Tuple[str, int]:
    """(stdout, exit) theo giao thức chặn của host (research §9): JSON deny là chính; Cursor đòi JSON hợp lệ cả khi
    cho qua (JSON hỏng = chặn), Gemini cho qua nói rõ."""
    if host == "codex":
        body = {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": reason}
        return (json.dumps({"hookSpecificOutput": body}, ensure_ascii=False) if deny else ""), 0
    if host == "cursor":
        out = (
            {"permission": "deny", "user_message": reason, "agent_message": reason} if deny else {"permission": "allow"}
        )
        return json.dumps(out, ensure_ascii=False), 0
    if host == "copilot":
        doc = {"permissionDecision": "deny", "permissionDecisionReason": reason}
        return (json.dumps(doc, ensure_ascii=False) if deny else ""), 0
    if host == "gemini":
        return json.dumps(
            {"decision": "deny", "reason": reason} if deny else {"decision": "allow"}, ensure_ascii=False
        ), 0
    return (json.dumps({"decision": "deny", "reason": reason}, ensure_ascii=False) if deny else ""), 0  # grok, opencode


def run(host: str, raw: Any, loader: Callable[[str], Optional[types.ModuleType]] = load_guard) -> Tuple[str, int]:
    tool, args, cwd, _ = parse(host, raw)
    root = project_root(cwd)
    guard = loader(root)
    if guard is None:  # dự án chưa cài harness của khung: không có luật để áp
        return render(host, False, "")
    deny, code, reason = decide(guard, to_core(host, tool, args, cwd, root))
    return render(host, deny, f"{reason} [{code}]" if deny and code else reason)


def main(argv: Optional[List[str]] = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    host = argv[0] if argv else ""
    if host not in HOSTS:
        sys.stderr.write(f"xt_adapter: host phải là một trong {', '.join(HOSTS)}\n")
        return 2
    try:
        raw = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        raw = {}
    out, code = run(host, raw)
    sys.stdout.write(out)
    return code


if __name__ == "__main__":
    sys.exit(main())
