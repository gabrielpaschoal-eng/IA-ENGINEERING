#!/usr/bin/env python3
import json

MESSAGE = (
    "Serena MCP disponível neste harness (registrado via .mcp.json). Ao trabalhar "
    "em código de um repositório real (não no TOOLS/ em si), prefira as ferramentas "
    "mcp__serena__* (find_symbol, find_referencing_symbols, replace_symbol_body, "
    "get_symbols_overview, etc.) a Read/Grep para navegação e edição de código. "
    "Chame mcp__serena__initial_instructions e mcp__serena__activate_project antes "
    "de começar uma tarefa de código nesse repositório."
)

print(
    json.dumps(
        {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": MESSAGE,
            }
        }
    )
)
