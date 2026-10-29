"""Tests for sandbox program execution."""

import unittest

from unittest.mock import MagicMock

from server_runner.sandbox_controller.command_executor import (
    CommandResult,
)

from server_runner.sandbox_controller.execution_policy import (
    ExecutionMode,
)

from server_runner.sandbox_controller.sandbox_execution import (
    SandboxExecutionService,
)


class TestSandboxExecutionService(unittest.TestCase):
    """Verify sandbox execution coordination."""

    def setUp(self):
        """Create mocked runtime and executor."""

        self.runtime = MagicMock()
        self.executor = MagicMock()

        self.runtime.build_run_command.return_value = [
            "docker",
            "exec",
            "container-id",
            "python3",
            "main.py",
        ]

        self.executor.execute.return_value = CommandResult(
            return_code=0,
            stdout="Hello CodeView\n",
            stderr="",
            timed_out=False,
        )

        self.service = SandboxExecutionService(
            runtime=self.runtime,
            executor=self.executor,
        )

    def test_run_program_uses_docker(self):
        """Program execution must use the Docker command builder."""

        result = self.service.run_program(
            container_id="a" * 64,
            language="python",
            filename="main.py",
        )

        self.runtime.build_run_command.assert_called_once()

        self.assertEqual(
            result.stdout,
            "Hello CodeView\n",
        )

    def test_run_program_uses_run_policy(self):
        """Program execution must use the Run timeout policy."""

        self.service.run_program(
            container_id="a" * 64,
            language="python",
            filename="main.py",
        )

        self.executor.execute.assert_called_once_with(
            command=self.runtime.build_run_command.return_value,
            mode=ExecutionMode.RUN,
        )

    def test_timeout_is_reported(self):
        """Return the timeout result to the caller."""

        self.executor.execute.return_value = CommandResult(
            return_code=-9,
            stdout="",
            stderr="Execution timed out",
            timed_out=True,
        )

        result = self.service.run_program(
            container_id="a" * 64,
            language="python",
            filename="main.py",
        )

        self.assertTrue(result.timed_out)


if __name__ == "__main__":
    unittest.main()