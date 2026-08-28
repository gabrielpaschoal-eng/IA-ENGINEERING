#!/usr/bin/env bash
# PreToolUse guard for Bash: blocks configured git commands on configured branches.
# Config path: arg1, else $GIT_GUARD_CONFIG, else <this script's dir>/config/git-guard.json

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG="${1:-${GIT_GUARD_CONFIG:-$SCRIPT_DIR/config/git-guard.json}}"
[ -f "$CONFIG" ] || exit 0

input=$(cat)
command=$(printf '%s' "$input" | jq -r '.tool_input.command // empty')
[ -z "$command" ] && exit 0

repo_root=$(git rev-parse --show-toplevel 2>/dev/null)
[ -z "$repo_root" ] && exit 0

# repo opted out entirely
if jq -e --arg r "$repo_root" '.exemptRepos // [] | index($r)' "$CONFIG" >/dev/null 2>&1; then
  exit 0
fi

blocked_cmds=$(jq -r '.blockedCommands // [] | join("|")' "$CONFIG")
[ -z "$blocked_cmds" ] && exit 0

if printf '%s' "$command" | grep -qE "(^|[;&|]+[[:space:]]*)git[[:space:]]+($blocked_cmds)([[:space:]]|\$)"; then
  branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
  is_protected=$(jq -r --arg b "$branch" '.protectedBranches // [] | index($b) != null' "$CONFIG")
  if [ "$is_protected" = "true" ]; then
    reason="Comando bloqueado na branch protegida '$branch' (config: $CONFIG). Crie e mude para outra branch antes (git checkout -b <nome>), ou ajuste protectedBranches/blockedCommands/exemptRepos no JSON."
    printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"%s"}}\n' "$reason"
    exit 0
  fi
fi
exit 0
