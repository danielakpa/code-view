"""Tests for CodeView sandbox lifecycle management."""

import unittest

from server_runner.sandbox_controller.lifecycle import (
    SandboxLifecycle,
    SandboxLifecycleError,
)


class TestSandboxLifecycle(unittest.TestCase):
    """Test sandbox lifecycle state transitions."""

    def setUp(self):
        """Create the lifecycle manager."""

        self.lifecycle = SandboxLifecycle()

    def test_prepared_to_starting(self):
        """Allow a prepared sandbox to start."""

        result = self.lifecycle.transition(
            "prepared",
            "starting",
        )

        self.assertEqual(result, "starting")

    def test_starting_to_running(self):
        """Allow a starting sandbox to become running."""

        result = self.lifecycle.transition(
            "starting",
            "running",
        )

        self.assertEqual(result, "running")

    def test_running_to_stopped(self):
        """Allow a running sandbox to stop."""

        result = self.lifecycle.transition(
            "running",
            "stopped",
        )

        self.assertEqual(result, "stopped")

    def test_stopped_to_starting(self):
        """Allow a stopped sandbox to restart."""

        result = self.lifecycle.transition(
            "stopped",
            "starting",
        )

        self.assertEqual(result, "starting")

    def test_starting_to_failed(self):
        """Allow startup failures."""

        result = self.lifecycle.transition(
            "starting",
            "failed",
        )

        self.assertEqual(result, "failed")

    def test_prepared_to_running_rejected(self):
        """Prevent skipping the starting stage."""

        with self.assertRaises(SandboxLifecycleError):
            self.lifecycle.transition(
                "prepared",
                "running",
            )

    def test_running_to_starting_rejected(self):
        """Prevent starting an already running sandbox."""

        with self.assertRaises(SandboxLifecycleError):
            self.lifecycle.transition(
                "running",
                "starting",
            )

    def test_unknown_status_rejected(self):
        """Reject unknown sandbox states."""

        with self.assertRaises(SandboxLifecycleError):
            self.lifecycle.transition(
                "unknown",
                "running",
            )

    def test_same_status_rejected(self):
        """Prevent unnecessary repeated transitions."""

        with self.assertRaises(SandboxLifecycleError):
            self.lifecycle.transition(
                "running",
                "running",
            )


if __name__ == "__main__":
    unittest.main()