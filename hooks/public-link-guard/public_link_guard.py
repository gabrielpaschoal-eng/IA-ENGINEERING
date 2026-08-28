#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path


def resolve_config_path() -> str:
    if len(sys.argv) > 1 and sys.argv[1]:
        return sys.argv[1]
    if os.environ.get("PUBLIC_LINK_GUARD_CONFIG"):
        return os.environ["PUBLIC_LINK_GUARD_CONFIG"]
    return str(Path(__file__).resolve().parent / ".." / "config" / "public-link-guard.json")


def block_publish(path: str) -> bool:
    try:
        data = json.loads(Path(path).read_text())
    except (OSError, json.JSONDecodeError):
        return True
    return bool(data.get("blockPublish", True))


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
    if not block_publish(config_path):
        return

    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        payload = {}

    mode = (payload.get("tool_input") or {}).get("mode") or "check"
    if mode == "delete":
        return

    deny(
        f"Publicação de link público (ShareOnboardingGuide, mode='{mode}') bloqueada por "
        f"padrão (config: {config_path}). Isso gera URL acessível fora desta máquina. Só "
        "prossiga se o usuário pediu essa publicação explicitamente agora — nesse caso, "
        "confirme com ele e ajuste blockPublish: false no JSON pra essa chamada, depois "
        "volte pra true."
    )


if __name__ == "__main__":
    main()
