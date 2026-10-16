#!/usr/bin/env bash
# pre-mcp-guard.sh — PreToolUse hook (matcher: tool MCP merge PR). Merge qua MCP không đi qua `xt.py merge-check`
# (ADR-0013) nên hỏi người (AUD-SEC-020). Quyết định ở guard.py (`mcp`); thiếu python3 → vẫn hỏi (fail-closed cho merge).
set -uo pipefail
. "$(dirname "$0")/_lib.sh"

payload="$(cat)"
if ! command -v python3 >/dev/null 2>&1; then
  printf '%s\n' '{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "ask", "permissionDecisionReason": "Khung cần xác nhận: không có python3 nên guard không kiểm được merge qua MCP"}}'
  exit 0
fi
res="$(printf '%s' "$payload" | CLAUDE_PROJECT_DIR="$XT_ROOT" python3 "$(dirname "$0")/guard.py" mcp 2>/dev/null)" || exit 0
[ "$(json_field "$res" decision)" = "ask" ] && pretool_decision ask "Khung cần xác nhận: $(json_field "$res" reason)"
exit 0
