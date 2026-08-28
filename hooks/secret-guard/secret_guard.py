#!/usr/bin/env python3
import fnmatch
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
MAX_SCAN_BYTES = 200_000


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


def run_git(cwd: str, git_dir: str | None, *args: str) -> str:
    extra = ["--git-dir", git_dir] if git_dir else []
    try:
        result = subprocess.run(
            ["git", *extra, *args], capture_output=True, text=True, check=True, cwd=cwd
        )
    except (subprocess.CalledProcessError, OSError):
        return ""
    return result.stdout


def repo_root(cwd: str, git_dir: str | None) -> str:
    return run_git(cwd, git_dir, "rev-parse", "--show-toplevel").strip()


@dataclass(frozen=True, slots=True)
class GuardConfig:
    blocked_filename_patterns: tuple[str, ...] = ()
    allowed_filename_patterns: tuple[str, ...] = ()
    content_patterns: tuple[re.Pattern, ...] = ()
    exempt_repos: frozenset[str] = frozenset()

    @classmethod
    def load(cls, path: str) -> "GuardConfig | None":
        try:
            data = json.loads(Path(path).read_text())
        except (OSError, json.JSONDecodeError):
            return None
        filename_patterns = data.get("blockedFilenamePatterns", [])
        blocked = tuple(p for p in filename_patterns if not p.startswith("!"))
        allowed = tuple(p[1:] for p in filename_patterns if p.startswith("!"))
        content_patterns = tuple(re.compile(p) for p in data.get("contentPatterns", []))
        return cls(
            blocked_filename_patterns=blocked,
            allowed_filename_patterns=allowed,
            content_patterns=content_patterns,
            exempt_repos=frozenset(data.get("exemptRepos", [])),
        )

    def is_active(self) -> bool:
        return bool(self.blocked_filename_patterns or self.content_patterns)

    def exempts(self, repo: str) -> bool:
        return repo in self.exempt_repos

    def blocked_filename(self, name: str) -> str:
        for pattern in self.blocked_filename_patterns:
            if fnmatch.fnmatch(name, pattern):
                if any(fnmatch.fnmatch(name, allow) for allow in self.allowed_filename_patterns):
                    continue
                return pattern
        return ""

    def matched_content_pattern(self, text: str) -> str:
        for pattern in self.content_patterns:
            if pattern.search(text):
                return pattern.pattern
        return ""


def candidate_files(invocation: GitInvocation, repo: str) -> list[str]:
    if invocation.subcommand == "add":
        pathspecs = [w for w in invocation.rest if not w.startswith("-")]
        if not pathspecs or any(p in (".", "-A", "--all", ":/") for p in pathspecs):
            out = run_git(repo, invocation.git_dir, "status", "--porcelain", "--untracked-files=all")
            return [line[3:].strip() for line in out.splitlines() if line.strip()]
        return pathspecs
    if invocation.subcommand == "commit":
        out = run_git(repo, invocation.git_dir, "diff", "--cached", "--name-only")
        files = [f for f in out.splitlines() if f]
        if any(w in ("-a", "--all") for w in invocation.rest):
            extra = run_git(repo, invocation.git_dir, "diff", "--name-only")
            files += [f for f in extra.splitlines() if f and f not in files]
        return files
    return []


def read_file_text(repo: str, relpath: str) -> str:
    p = Path(repo) / relpath
    try:
        if not p.is_file() or p.stat().st_size > MAX_SCAN_BYTES:
            return ""
        return p.read_text(errors="ignore")
    except OSError:
        return ""


def staged_added_lines(repo: str, git_dir: str | None, relpath: str) -> str:
    diff = run_git(repo, git_dir, "diff", "--cached", "-U0", "--", relpath)
    return "\n".join(
        line[1:] for line in diff.splitlines() if line.startswith("+") and not line.startswith("+++")
    )


def deny_reason_filename(relpath: str, pattern: str, config_path: str) -> str:
    return (
        f"Arquivo '{relpath}' bate com padrão de secret bloqueado ('{pattern}', "
        f"config: {config_path}). Não deveria ir pro git. Renomeie/ajuste .gitignore, "
        "ou edite blockedFilenamePatterns/exemptRepos no JSON se for intencional."
    )


def deny_reason_content(relpath: str, pattern: str, config_path: str) -> str:
    return (
        f"Conteúdo de '{relpath}' bate com padrão de secret ('{pattern}', config: "
        f"{config_path}) — valor não exibido aqui de propósito. Remova o secret antes "
        "de commitar, ou ajuste contentPatterns/exemptRepos no JSON se for falso positivo."
    )


def resolve_config_path() -> str:
    if len(sys.argv) > 1 and sys.argv[1]:
        return sys.argv[1]
    if os.environ.get("SECRET_GUARD_CONFIG"):
        return os.environ["SECRET_GUARD_CONFIG"]
    return str(Path(__file__).resolve().parent / ".." / "config" / "secret-guard.json")


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
    session_cwd = payload.get("cwd") or "."

    for words in split_commands(command):
        invocation = parse_git_invocation(words)
        if invocation is None or invocation.subcommand not in ("add", "commit"):
            continue

        base_cwd = invocation.repo_dir or session_cwd
        repo = repo_root(base_cwd, invocation.git_dir)
        if not repo or config.exempts(repo):
            continue

        for relpath in candidate_files(invocation, repo):
            name = os.path.basename(relpath)
            pattern = config.blocked_filename(name)
            if pattern:
                deny(deny_reason_filename(relpath, pattern, config_path))
                return

            text = (
                staged_added_lines(repo, invocation.git_dir, relpath)
                if invocation.subcommand == "commit"
                else read_file_text(repo, relpath)
            )
            if not text:
                continue
            content_pattern = config.matched_content_pattern(text)
            if content_pattern:
                deny(deny_reason_content(relpath, content_pattern, config_path))
                return


if __name__ == "__main__":
    main()
