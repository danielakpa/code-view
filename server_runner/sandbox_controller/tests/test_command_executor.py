"""Tests for trusted command execution timeouts."""

import sys
import unittest

from unittest.mock import patch

from server_runner.sandbox_controller.command_executor import (
    CommandExecutionError,
    CommandExecutor,
)

from server_runner.sandbox_controller.execution_policy import (
    ExecutionMode,
    ExecutionPolicy,
)


class TestCommandExecutor(unittest.TestCase):
    """Verify command execution rules."""

    def setUp(self):
        """Create the command executor."""

        self.executor = CommandExecutor()

    def test_short_command_completes(self):
        """A short trusted command should finish successfully."""

        result = self.executor.execute(
            [
                sys.executable,
                "-c",
                "print('Hello CodeView')",
            ]
        )

        self.assertEqual(result.return_code, 0)
        self.assertEqual(
            result.stdout.strip(),
            "Hello CodeView",
        )
        self.assertFalse(result.timed_out)

    def test_command_timeout(self):
        """A long-running trusted command should time out."""

        # Use a short timeout so this test runs quickly.
        short_policy = ExecutionPolicy(
            mode=ExecutionMode.RUN,
            execution_timeout_seconds=1,
            idle_timeout_seconds=None,
        )

        with patch(
            "server_runner.sandbox_controller.command_executor."
            "get_execution_policy",
            return_value=short_policy,
        ):
            result = self.executor.execute(
                [
                    sys.executable,
                    "-c",
                    "import time; time.sleep(10)",
                ]
            )

        self.assertTrue(result.timed_out)

    def test_terminal_mode_is_rejected(self):
        """Terminal mode must use a separate executor."""

        with self.assertRaises(CommandExecutionError):
            self.executor.execute(
                [sys.executable, "--version"],
                mode=ExecutionMode.TERMINAL,
            )

    def test_empty_command_is_rejected(self):
        """Reject empty command lists."""

        with self.assertRaises(CommandExecutionError):
            self.executor.execute([])

    def test_shell_string_is_rejected(self):
        """Reject raw shell command strings."""

        with self.assertRaises(CommandExecutionError):
            self.executor.execute("python3 main.py")


if __name__ == "__main__":
    unittest.main()