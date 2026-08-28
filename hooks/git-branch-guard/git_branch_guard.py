#!/usr/bin/env python3
import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

ASSIGNMENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
GIT_OPTS_WITH_VALUE = {"-C", "-c", "--git-dir", "--work-tree", "--namespace"}

SEPARATORS = {";", "&", "&&", "||", "|", "(", ")"}
PUNCT_CHARS = set("();&|")


def main():
    config_path = resolve_config_path()
    cfg = load_config(config_path)
    if cfg is None or not cfg.get("blockedCommands"):
        sys.exit(0)

    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)
    command = (data.get("tool_input") or {}).get("command") or ""
    if not command:
        sys.exit(0)

    repo_root = git_output("rev-parse", "--show-toplevel")
    if not repo_root:
        sys.exit(0)
    if repo_root in cfg.get("exemptRepos", []):
        sys.exit(0)

    blocked = ""
    for words in split_commands(command):
        sc = git_subcommand(words)
        if sc and sc in cfg["blockedCommands"]:
            blocked = sc
            break
    if not blocked:
        sys.exit(0)

    branch = git_output("rev-parse", "--abbrev-ref", "HEAD")
    if not branch or branch not in cfg.get("protectedBranches", []):
        sys.exit(0)

    deny(branch, config_path)


def resolve_config_path() -> str:
    if len(sys.argv) > 1 and sys.argv[1]:
        return sys.argv[1]
    if os.environ.get("GIT_GUARD_CONFIG"):
        return os.environ["GIT_GUARD_CONFIG"]
    script_dir = Path(__file__).resolve().parent
    return str(script_dir / ".." / "config" / "git-guard.json")


def load_config(path: str):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def git_output(*args: str) -> str:
    try:
        out = subprocess.run(
            ["git", *args], capture_output=True, text=True, check=True
        )
    except (subprocess.CalledProcessError, OSError):
        return ""
    return out.stdout.strip()


def split_commands(cmd: str) -> list[list[str]]:
    tokens = tokenize(cmd)
    commands: list[list[str]] = []
    cur: list[str] = []
    for t in tokens:
        if t in SEPARATORS:
            if cur:
                commands.append(cur)
                cur = []
            continue
        cur.append(t)
    if cur:
        commands.append(cur)
    return commands


def tokenize(cmd: str) -> list[str]:
    lexer = shlex.shlex(cmd, posix=True, punctuation_chars="();&|")
    lexer.whitespace_split = True
    tokens = []
    for tok in lexer:
        if tok and all(c in PUNCT_CHARS for c in tok):
            tokens.extend(split_punctuation(tok))
        else:
            tokens.append(tok)
    return tokens


def split_punctuation(tok: str) -> list[str]:
    out = []
    i = 0
    while i < len(tok):
        c = tok[i]
        if c in ("&", "|") and i + 1 < len(tok) and tok[i + 1] == c:
            out.append(c + c)
            i += 2
        else:
            out.append(c)
            i += 1
    return out


def git_subcommand(words: list[str]) -> str:
    i = 0
    while i < len(words) and ASSIGNMENT_RE.match(words[i]):
        i += 1
    if i >= len(words) or words[i] != "git":
        return ""
    i += 1
    while i < len(words):
        a = words[i]
        if a.startswith("-"):
            if a in GIT_OPTS_WITH_VALUE and "=" not in a:
                i += 1
            i += 1
            continue
        return a
    return ""


def deny(branch: str, config_path: str):
    reason = (
        f"Comando bloqueado na branch protegida '{branch}' (config: {config_path}). "
        "Crie e mude para outra branch antes (git checkout -b <nome>), ou ajuste "
        "protectedBranches/blockedCommands/exemptRepos no JSON."
    )
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }
    json.dump(output, sys.stdout)
    sys.exit(0)


if __name__ == "__main__":
    main()
