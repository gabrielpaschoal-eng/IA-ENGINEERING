#!/usr/bin/env python3
import json
import os
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ASSIGNMENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
GIT_OPTS_WITH_VALUE = {"-C", "-c", "--git-dir", "--work-tree", "--namespace"}
SEPARATORS = {";", "&", "&&", "||", "|", "(", ")"}
PUNCT_CHARS = set("();&|")


@dataclass(frozen=True, slots=True)
class GuardConfig:
    protected_branches: frozenset[str] = frozenset()
    blocked_commands: frozenset[str] = frozenset()
    exempt_repos: frozenset[str] = frozenset()

    @classmethod
    def load(cls, path: str) -> "GuardConfig | None":
        try:
            data = json.loads(Path(path).read_text())
        except (OSError, json.JSONDecodeError):
            return None
        return cls(
            protected_branches=frozenset(data.get("protectedBranches", [])),
            blocked_commands=frozenset(data.get("blockedCommands", [])),
            exempt_repos=frozenset(data.get("exemptRepos", [])),
        )

    def is_active(self) -> bool:
        return bool(self.blocked_commands)

    def exempts(self, repo_root: str) -> bool:
        return repo_root in self.exempt_repos

    def blocks(self, subcommand: str) -> bool:
        return subcommand in self.blocked_commands

    def protects(self, branch: str) -> bool:
        return branch in self.protected_branches


class GitRepo:
    def __init__(self):
        self.root = self._run("rev-parse", "--show-toplevel")
        self._branch: str | None = None

    @property
    def branch(self) -> str:
        if self._branch is None:
            self._branch = self._run("rev-parse", "--abbrev-ref", "HEAD")
        return self._branch

    @staticmethod
    def _run(*args: str) -> str:
        try:
            result = subprocess.run(
                ["git", *args], capture_output=True, text=True, check=True
            )
        except (subprocess.CalledProcessError, OSError):
            return ""
        return result.stdout.strip()


def tokenize(command: str) -> list[str]:
    lexer = shlex.shlex(command, posix=True, punctuation_chars="();&|")
    lexer.whitespace_split = True
    tokens = []
    for tok in lexer:
        if tok and all(c in PUNCT_CHARS for c in tok):
            tokens.extend(_split_punctuation(tok))
        else:
            tokens.append(tok)
    return tokens


def _split_punctuation(tok: str) -> list[str]:
    out, i = [], 0
    while i < len(tok):
        c = tok[i]
        if c in "&|" and tok[i : i + 2] == c * 2:
            out.append(c * 2)
            i += 2
        else:
            out.append(c)
            i += 1
    return out


def split_commands(command: str) -> list[list[str]]:
    commands: list[list[str]] = []
    current: list[str] = []
    for token in tokenize(command):
        if token in SEPARATORS:
            if current:
                commands.append(current)
                current = []
        else:
            current.append(token)
    if current:
        commands.append(current)
    return commands


def git_subcommand(words: list[str]) -> str:
    i = 0
    while i < len(words) and ASSIGNMENT_RE.match(words[i]):
        i += 1
    if i >= len(words) or words[i] != "git":
        return ""
    i += 1
    while i < len(words):
        word = words[i]
        if word.startswith("-"):
            i += 2 if word in GIT_OPTS_WITH_VALUE and "=" not in word else 1
            continue
        return word
    return ""


def blocked_subcommand(config: GuardConfig, command: str) -> str:
    for words in split_commands(command):
        subcommand = git_subcommand(words)
        if subcommand and config.blocks(subcommand):
            return subcommand
    return ""


def deny_reason(branch: str, config_path: str) -> str:
    return (
        f"Comando bloqueado na branch protegida '{branch}' (config: {config_path}). "
        "Crie e mude para outra branch antes (git checkout -b <nome>), ou ajuste "
        "protectedBranches/blockedCommands/exemptRepos no JSON."
    )


def resolve_config_path() -> str:
    if len(sys.argv) > 1 and sys.argv[1]:
        return sys.argv[1]
    if os.environ.get("GIT_GUARD_CONFIG"):
        return os.environ["GIT_GUARD_CONFIG"]
    return str(Path(__file__).resolve().parent / ".." / "config" / "git-guard.json")


def main() -> None:
    config_path = resolve_config_path()
    config = GuardConfig.load(config_path)
    if config is None or not config.is_active():
        return

    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return
    command = (payload.get("tool_input") or {}).get("command") or ""
    if not command:
        return

    repo = GitRepo()
    if not repo.root or config.exempts(repo.root):
        return

    if not blocked_subcommand(config, command):
        return

    if not repo.branch or not config.protects(repo.branch):
        return

    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": deny_reason(repo.branch, config_path),
                }
            }
        )
    )


if __name__ == "__main__":
    main()
