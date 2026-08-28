#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path


def resolve_config_path() -> str:
    if len(sys.argv) > 1 and sys.argv[1]:
        return sys.argv[1]
    if os.environ.get("JIRA_WRITE_GUARD_CONFIG"):
        return os.environ["JIRA_WRITE_GUARD_CONFIG"]
    return str(Path(__file__).resolve().parent / ".." / "config" / "jira-write-guard.json")


def load_blocked_suffixes(path: str) -> tuple[str, ...]:
    try:
        data = json.loads(Path(path).read_text())
    except (OSError, json.JSONDecodeError):
        return ()
    return tuple(data.get("blockedToolSuffixes", []))


def matched_suffix(tool_name: str, blocked_suffixes: tuple[str, ...]) -> str:
    for suffix in blocked_suffixes:
        if tool_name.endswith(suffix):
            return suffix
    return ""


def deny_reason(tool_name: str, suffix: str, config_path: str) -> str:
    return (
        f"Escrita bloqueada em task/épico do Jira: '{tool_name}' bate com o sufixo "
        f"bloqueado '{suffix}' (config: {config_path}). Nenhuma skill deste harness deve "
        "alterar issue do Jira — refinamento/contexto ficam em cache local "
        "(settings/jira/). Ajuste blockedToolSuffixes no JSON se for intencional."
    )


def deny(reason: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            }
        )
    )


def main() -> None:
    config_path = resolve_config_path()
    blocked_suffixes = load_blocked_suffixes(config_path)
    if not blocked_suffixes:
        return

    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return
    tool_name = payload.get("tool_name") or ""
    if not tool_name:
        return

    suffix = matched_suffix(tool_name, blocked_suffixes)
    if suffix:
        deny(deny_reason(tool_name, suffix, config_path))


if __name__ == "__main__":
    main()
