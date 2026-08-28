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
import secret_guard as g  # noqa: E402

CONFIG_PATH = str(Path(__file__).resolve().parent.parent / "config" / "secret-guard.json")


def git(*args, cwd):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


def run_guard(command: str, cwd: str, config_path: str = CONFIG_PATH) -> dict | None:
    payload = json.dumps({"tool_input": {"command": command}, "cwd": cwd})
    old_argv, old_stdin = sys.argv, sys.stdin
    sys.argv = ["secret_guard.py", config_path]
    sys.stdin = io.StringIO(payload)
    try:
        with contextlib.redirect_stdout(io.StringIO()) as out:
            g.main()
        output = out.getvalue().strip()
    finally:
        sys.argv, sys.stdin = old_argv, old_stdin
    return json.loads(output) if output else None


def deny_reason(result: dict | None) -> str:
    return result["hookSpecificOutput"]["permissionDecisionReason"] if result else ""


class TestGuardConfig(unittest.TestCase):
    def test_filename_pattern_with_negation(self):
        config = g.GuardConfig(
            blocked_filename_patterns=(".env", ".env.*"),
            allowed_filename_patterns=(".env.example",),
        )
        self.assertEqual(config.blocked_filename(".env"), ".env")
        self.assertEqual(config.blocked_filename(".env.local"), ".env.*")
        self.assertEqual(config.blocked_filename(".env.example"), "")
        self.assertEqual(config.blocked_filename("app.py"), "")

    def test_content_pattern_match(self):
        config = g.GuardConfig(content_patterns=(g.re.compile(r"AKIA[0-9A-Z]{16}"),))
        self.assertEqual(
            config.matched_content_pattern("key = AKIAABCDEFGHIJKLMNOP"),
            "AKIA[0-9A-Z]{16}",
        )
        self.assertEqual(config.matched_content_pattern("no secret here"), "")

    def test_loads_real_config(self):
        config = g.GuardConfig.load(CONFIG_PATH)
        self.assertIsNotNone(config)
        self.assertTrue(config.is_active())
        self.assertEqual(config.blocked_filename(".env"), ".env")
        self.assertEqual(config.blocked_filename(".env.example"), "")


class TestEndToEnd(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.repo = self.tmpdir.name
        git("init", "-q", cwd=self.repo)
        git("config", "user.email", "t@t.com", cwd=self.repo)
        git("config", "user.name", "t", cwd=self.repo)
        git("commit", "-q", "--allow-empty", "-m", "init", cwd=self.repo)

    def tearDown(self):
        self.tmpdir.cleanup()

    def write(self, relpath: str, content: str) -> None:
        (Path(self.repo) / relpath).write_text(content)

    def test_blocks_add_of_dotenv_by_name(self):
        self.write(".env", "SECRET=x\n")
        result = run_guard(f"git -C {self.repo} add .env", cwd=self.repo)
        self.assertIsNotNone(result)
        self.assertIn(".env", deny_reason(result))

    def test_allows_add_of_dotenv_example(self):
        self.write(".env.example", "PORT=1234\n")
        self.assertIsNone(run_guard(f"git -C {self.repo} add .env.example", cwd=self.repo))

    def test_allows_add_of_clean_file(self):
        self.write("app.py", "print('hi')\n")
        self.assertIsNone(run_guard(f"git -C {self.repo} add app.py", cwd=self.repo))

    def test_add_dash_A_catches_dotenv_via_status(self):
        self.write(".env", "SECRET=x\n")
        self.write("app.py", "print('hi')\n")
        result = run_guard(f"git -C {self.repo} add -A", cwd=self.repo)
        self.assertIsNotNone(result)

    def test_blocks_add_when_file_content_has_aws_key(self):
        self.write("config.py", "AWS_KEY = 'AKIAABCDEFGHIJKLMNOP'\n")
        result = run_guard(f"git -C {self.repo} add config.py", cwd=self.repo)
        self.assertIsNotNone(result)
        self.assertNotIn("AKIAABCDEFGHIJKLMNOP", deny_reason(result))

    def test_blocks_commit_when_already_staged_content_has_secret(self):
        self.write("config.py", "password = \"correct-horse-battery-staple-123\"\n")
        git("add", "config.py", cwd=self.repo)
        result = run_guard(f"git -C {self.repo} commit -m x", cwd=self.repo)
        self.assertIsNotNone(result)

    def test_commit_of_clean_staged_file_is_allowed(self):
        self.write("app.py", "print('clean')\n")
        git("add", "app.py", cwd=self.repo)
        self.assertIsNone(run_guard(f"git -C {self.repo} commit -m x", cwd=self.repo))

    def test_non_git_add_commands_are_ignored(self):
        self.assertIsNone(run_guard(f"git -C {self.repo} status", cwd=self.repo))


if __name__ == "__main__":
    unittest.main()
