#!/usr/bin/env python3
import json
import os
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

ASSIGNMENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
GIT_OPTS_WITH_VALUE = {"-c", "--work-tree", "--namespace"}
SEPARATORS = {";", "&", "&&", "||", "|", "(", ")"}
PUNCT_CHARS = set("();&|")


@dataclass(frozen=True, slots=True)
class AlwaysBlockedRule:
    subcommand: str
    any_flags: tuple[str, ...] = ()
    unless_flags: tuple[str, ...] = ()
    first_arg: str | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "AlwaysBlockedRule":
        return cls(
            subcommand=data.get("subcommand", ""),
            any_flags=tuple(data.get("anyFlags", [])),
            unless_flags=tuple(data.get("unlessFlags", [])),
            first_arg=data.get("firstArg"),
        )

    def matches(self, subcommand: str, rest: list[str]) -> bool:
        if not self.subcommand or self.subcommand != subcommand:
            return False
        if self.first_arg is not None:
            positional = next((w for w in rest if not w.startswith("-")), None)
            if positional != self.first_arg:
                return False
        if self.unless_flags and any(has_flag(rest, f) for f in self.unless_flags):
            return False
        if self.any_flags and not any(has_flag(rest, f) for f in self.any_flags):
            return False
        return True

    def describe(self) -> str:
        parts = [f"git {self.subcommand}"]
        if self.first_arg:
            parts.append(self.first_arg)
        if self.any_flags:
            parts.append("/".join(self.any_flags))
        return " ".join(parts)


def has_flag(words: list[str], flag: str) -> bool:
    if flag == "--" or flag.startswith("--"):
        return flag in words
    letter = flag[1:]
    if not letter:
        return False
    return any(
        w.startswith("-") and not w.startswith("--") and letter in w[1:]
        for w in words
    )


@dataclass(frozen=True, slots=True)
class GuardConfig:
    protected_branches: frozenset[str] = frozenset()
    blocked_commands: frozenset[str] = frozenset()
    exempt_repos: frozenset[str] = frozenset()
    always_blocked: tuple[AlwaysBlockedRule, ...] = ()
    blocked_flags: frozenset[str] = frozenset()

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
            always_blocked=tuple(
                AlwaysBlockedRule.from_dict(r) for r in data.get("alwaysBlocked", [])
            ),
            blocked_flags=frozenset(data.get("blockedFlagsAnywhere", [])),
        )

    def is_active(self) -> bool:
        return bool(self.blocked_commands or self.always_blocked or self.blocked_flags)

    def exempts(self, repo_root: str) -> bool:
        return repo_root in self.exempt_repos

    def blocks(self, subcommand: str) -> bool:
        return subcommand in self.blocked_commands

    def protects(self, branch: str) -> bool:
        return branch in self.protected_branches

    def matched_flag(self, rest: list[str]) -> str:
        for flag in self.blocked_flags:
            if has_flag(rest, flag):
                return flag
        return ""

    def matched_always_rule(
        self, subcommand: str, rest: list[str]
    ) -> AlwaysBlockedRule | None:
        for rule in self.always_blocked:
            if rule.matches(subcommand, rest):
                return rule
        return None


class GitRepo:
    def __init__(self, cwd: str | None = None, git_dir: str | None = None):
        self._cwd = cwd
        self._extra_args = ["--git-dir", git_dir] if git_dir else []
        self.root = self._run("rev-parse", "--show-toplevel")
        self._branch: str | None = None

    @property
    def branch(self) -> str:
        if self._branch is None:
            self._branch = self._run("rev-parse", "--abbrev-ref", "HEAD")
        return self._branch

    def _run(self, *args: str) -> str:
        try:
            result = subprocess.run(
                ["git", *self._extra_args, *args],
                capture_output=True,
                text=True,
                check=True,
                cwd=self._cwd,
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


@dataclass(frozen=True, slots=True)
class GitInvocation:
    subcommand: str
    rest: list[str] = field(default_factory=list)
    repo_dir: str | None = None
    git_dir: str | None = None


def parse_git_invocation(words: list[str]) -> GitInvocation | None:
    i = 0
    while i < len(words) and ASSIGNMENT_RE.match(words[i]):
        i += 1
    if i >= len(words) or words[i] != "git":
        return None
    i += 1

    repo_dir: str | None = None
    git_dir: str | None = None
    while i < len(words):
        word = words[i]
        if not word.startswith("-"):
            break
        if word == "-C":
            if i + 1 < len(words):
                repo_dir = (
                    words[i + 1] if repo_dir is None else os.path.join(repo_dir, words[i + 1])
                )
            i += 2
            continue
        if word == "--git-dir" or word.startswith("--git-dir="):
            git_dir = word.split("=", 1)[1] if "=" in word else words[i + 1] if i + 1 < len(words) else None
            i += 1 if "=" in word else 2
            continue
        if word in GIT_OPTS_WITH_VALUE and "=" not in word:
            i += 2
            continue
        i += 1

    if i >= len(words):
        return GitInvocation(subcommand="", rest=[], repo_dir=repo_dir, git_dir=git_dir)

    return GitInvocation(
        subcommand=words[i], rest=words[i + 1 :], repo_dir=repo_dir, git_dir=git_dir
    )


def deny_reason_protected(branch: str, config_path: str) -> str:
    return (
        f"Comando bloqueado na branch protegida '{branch}' (config: {config_path}). "
        "Crie e mude para outra branch antes (git checkout -b <nome>), ou ajuste "
        "protectedBranches/blockedCommands/exemptRepos no JSON."
    )


def deny_reason_always(rule: AlwaysBlockedRule, config_path: str) -> str:
    return (
        f"Comando destrutivo bloqueado sempre: '{rule.describe()}' (config: {config_path}). "
        "Perde commits/arquivos sem recuperação fácil. Se necessário, ajuste "
        "alwaysBlocked/exemptRepos no JSON e rode manualmente fora do agente."
    )


def deny_reason_flag(flag: str, config_path: str) -> str:
    return (
        f"Flag bloqueada '{flag}' (config: {config_path}). "
        "Pula hooks de verificação (lint/test/commit-msg). Ajuste blockedFlagsAnywhere "
        "no JSON se for intencional."
    )


def resolve_config_path() -> str:
    if len(sys.argv) > 1 and sys.argv[1]:
        return sys.argv[1]
    if os.environ.get("GIT_GUARD_CONFIG"):
        return os.environ["GIT_GUARD_CONFIG"]
    return str(Path(__file__).resolve().parent / ".." / "config" / "git-guard.json")


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

    for words in split_commands(command):
        invocation = parse_git_invocation(words)
        if invocation is None or not invocation.subcommand:
            continue

        repo = GitRepo(cwd=invocation.repo_dir, git_dir=invocation.git_dir)
        if not repo.root or config.exempts(repo.root):
            continue

        flag = config.matched_flag(invocation.rest)
        if flag:
            deny(deny_reason_flag(flag, config_path))
            return

        rule = config.matched_always_rule(invocation.subcommand, invocation.rest)
        if rule:
            deny(deny_reason_always(rule, config_path))
            return

        if (
            config.blocks(invocation.subcommand)
            and repo.branch
            and config.protects(repo.branch)
        ):
            deny(deny_reason_protected(repo.branch, config_path))
            return


if __name__ == "__main__":
    main()
