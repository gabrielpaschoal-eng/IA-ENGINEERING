#!/usr/bin/env python3
import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import git_branch_guard as g  # noqa: E402

CONFIG_PATH = str(Path(__file__).resolve().parent.parent / "config" / "git-guard.json")


def run_guard(command: str, config_path: str = CONFIG_PATH) -> dict | None:
    payload = json.dumps({"tool_input": {"command": command}})
    old_argv, old_stdin = sys.argv, sys.stdin
    sys.argv = ["git_branch_guard.py", config_path]
    sys.stdin = io.StringIO(payload)
    try:
        with contextlib.redirect_stdout(io.StringIO()) as out:
            g.main()
        output = out.getvalue().strip()
    finally:
        sys.argv, sys.stdin = old_argv, old_stdin
    return json.loads(output) if output else None


def deny_reason(result: dict | None) -> str:
    if result is None:
        return ""
    return result["hookSpecificOutput"]["permissionDecisionReason"]


class TestTokenize(unittest.TestCase):
    def test_splits_on_separators(self):
        words = g.tokenize("git commit -m foo && git push")
        self.assertIn("&&", words)
        self.assertEqual(g.split_commands("git commit -m foo && git push"), [
            ["git", "commit", "-m", "foo"],
            ["git", "push"],
        ])

    def test_quoted_string_stays_one_token(self):
        words = g.tokenize('git commit -m "fix: foo bar"')
        self.assertIn("fix: foo bar", words)


class TestParseGitInvocation(unittest.TestCase):
    def test_basic(self):
        inv = g.parse_git_invocation(["git", "commit", "-m", "x"])
        self.assertEqual(inv.subcommand, "commit")
        self.assertEqual(inv.rest, ["-m", "x"])
        self.assertIsNone(inv.repo_dir)

    def test_env_prefix_skipped(self):
        inv = g.parse_git_invocation(["FOO=bar", "git", "status"])
        self.assertEqual(inv.subcommand, "status")

    def test_non_git_returns_none(self):
        self.assertIsNone(g.parse_git_invocation(["echo", "hi"]))

    def test_dash_C_sets_repo_dir(self):
        inv = g.parse_git_invocation(["git", "-C", "/tmp/repo", "reset", "--hard"])
        self.assertEqual(inv.repo_dir, "/tmp/repo")
        self.assertEqual(inv.subcommand, "reset")
        self.assertEqual(inv.rest, ["--hard"])

    def test_dash_C_chained(self):
        inv = g.parse_git_invocation(["git", "-C", "/tmp", "-C", "repo", "status"])
        self.assertEqual(inv.repo_dir, "/tmp/repo")

    def test_git_dir_flag_and_equals_form(self):
        inv1 = g.parse_git_invocation(["git", "--git-dir", "/x/.git", "log"])
        self.assertEqual(inv1.git_dir, "/x/.git")
        inv2 = g.parse_git_invocation(["git", "--git-dir=/x/.git", "log"])
        self.assertEqual(inv2.git_dir, "/x/.git")


class TestHasFlag(unittest.TestCase):
    def test_long_flag_exact_match(self):
        self.assertTrue(g.has_flag(["--force"], "--force"))
        self.assertFalse(g.has_flag(["--force-with-lease"], "--force"))

    def test_short_flag_bundled(self):
        self.assertTrue(g.has_flag(["-fd"], "-f"))
        self.assertTrue(g.has_flag(["-fd"], "-d"))
        self.assertFalse(g.has_flag(["-x"], "-f"))

    def test_double_dash_separator(self):
        self.assertTrue(g.has_flag(["--", "file.txt"], "--"))
        self.assertFalse(g.has_flag(["file.txt"], "--"))


class TestAlwaysBlockedRule(unittest.TestCase):
    def test_any_flags(self):
        rule = g.AlwaysBlockedRule(subcommand="reset", any_flags=("--hard",))
        self.assertTrue(rule.matches("reset", ["--hard"]))
        self.assertFalse(rule.matches("reset", ["--soft"]))
        self.assertFalse(rule.matches("commit", ["--hard"]))

    def test_unless_flags(self):
        rule = g.AlwaysBlockedRule(subcommand="restore", unless_flags=("--staged",))
        self.assertTrue(rule.matches("restore", ["file.txt"]))
        self.assertFalse(rule.matches("restore", ["--staged", "file.txt"]))

    def test_first_arg(self):
        rule = g.AlwaysBlockedRule(subcommand="submodule", first_arg="deinit")
        self.assertTrue(rule.matches("submodule", ["deinit", "foo"]))
        self.assertFalse(rule.matches("submodule", ["update"]))

    def test_bare_subcommand_always_matches(self):
        rule = g.AlwaysBlockedRule(subcommand="filter-branch")
        self.assertTrue(rule.matches("filter-branch", ["--tree-filter", "true"]))


class TestGuardConfig(unittest.TestCase):
    def test_missing_file_returns_none(self):
        self.assertIsNone(g.GuardConfig.load("/no/such/file.json"))

    def test_loads_real_config(self):
        config = g.GuardConfig.load(CONFIG_PATH)
        self.assertIsNotNone(config)
        self.assertTrue(config.is_active())
        self.assertTrue(config.protects("main"))
        self.assertTrue(config.blocks("commit"))


class TestEndToEnd(unittest.TestCase):
    """Runs the real shipped config (hooks/config/git-guard.json) against a scratch repo."""

    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.TemporaryDirectory()
        cls.repo = cls.tmpdir.name
        subprocess.run(["git", "init", "-q", cls.repo], check=True)
        subprocess.run(
            ["git", "-C", cls.repo, "commit", "-q", "--allow-empty", "-m", "init"],
            check=True,
        )
        cls.branch = subprocess.run(
            ["git", "-C", cls.repo, "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()

    @classmethod
    def tearDownClass(cls):
        cls.tmpdir.cleanup()

    def test_allows_plain_status(self):
        self.assertIsNone(run_guard(f"git -C {self.repo} status"))

    def test_blocks_commit_on_protected_branch_via_dash_C(self):
        result = run_guard(f"git -C {self.repo} commit -m x")
        self.assertIsNotNone(result, "expected deny for commit on protected branch via -C")
        self.assertIn(self.branch, deny_reason(result))

    def test_always_blocks_reset_hard_regardless_of_branch(self):
        result = run_guard(f"git -C {self.repo} reset --hard")
        self.assertIsNotNone(result)
        self.assertIn("reset --hard", deny_reason(result))

    def test_always_blocks_force_push(self):
        result = run_guard(f"git -C {self.repo} push --force origin main")
        self.assertIsNotNone(result)

    def test_blocks_no_verify_flag(self):
        result = run_guard(f"git -C {self.repo} commit --no-verify -m x")
        self.assertIsNotNone(result)
        self.assertIn("--no-verify", deny_reason(result))

    def test_restore_with_staged_is_allowed(self):
        self.assertIsNone(run_guard(f"git -C {self.repo} restore --staged file.txt"))

    def test_non_git_repo_target_is_silently_ignored(self):
        with tempfile.TemporaryDirectory() as not_a_repo:
            self.assertIsNone(run_guard(f"git -C {not_a_repo} commit -m x"))


if __name__ == "__main__":
    unittest.main()
