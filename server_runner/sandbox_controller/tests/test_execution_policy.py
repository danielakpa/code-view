"""Tests for CodeView execution policies."""

import unittest

from server_runner.sandbox_controller.execution_policy import (
    ExecutionMode,
    get_execution_policy,
)


class TestExecutionPolicy(unittest.TestCase):
    """Verify the rules for each execution mode."""

    def test_run_has_30_second_timeout(self):
        """Run mode should have a short execution limit."""

        policy = get_execution_policy(ExecutionMode.RUN)

        self.assertEqual(
            policy.execution_timeout_seconds,
            30,
        )

        self.assertIsNone(
            policy.idle_timeout_seconds,
        )

    def test_terminal_has_no_execution_timeout(self):
        """Interactive terminals should support long-running commands."""

        policy = get_execution_policy(ExecutionMode.TERMINAL)

        self.assertIsNone(
            policy.execution_timeout_seconds,
        )

    def test_terminal_has_30_minute_idle_timeout(self):
        """Inactive terminals should eventually be stopped."""

        policy = get_execution_policy(ExecutionMode.TERMINAL)

        self.assertEqual(
            policy.idle_timeout_seconds,
            1800,
        )

    def test_invalid_mode_is_rejected(self):
        """Unknown execution modes must not be accepted."""

        with self.assertRaises(ValueError):
            get_execution_policy("invalid")


if __name__ == "__main__":
    unittest.main()