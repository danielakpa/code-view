"""Test CodeView's sandbox execution service."""

import unittest

from pathlib import Path
from unittest.mock import MagicMock
from uuid import uuid4

from server_runner.sandbox_controller.sandbox_execution import (
    SandboxExecutionService,
    SandboxExecutionResult,
)

from server_runner.sandbox_controller.temporary_container_executor import (
    TemporaryContainerResult,
    TemporaryContainerExecutionError,
)


class TestSandboxExecutionService(unittest.TestCase):
    """Test how the execution service handles temporary programs."""

    def setUp(self):
        """Prepare fake dependencies for each test."""

        # Generate a sandbox identifier.
        self.sandbox_id = uuid4()

        # Use a sample workspace path.
        self.workspace_path = Path("/workspace/test")

        # Mock the temporary container executor.
        # No real Docker containers are created.
        self.temporary_executor = MagicMock()

        # Create the service using the mocked executor.
        self.service = SandboxExecutionService(
            temporary_executor=self.temporary_executor,
        )

    def test_successful_temporary_execution(self):
        """Verify that successful execution returns the correct result."""

        # Simulate successful Docker execution.
        self.temporary_executor.execute.return_value = (
            TemporaryContainerResult(
                return_code=0,
                stdout="Hello CodeView\n",
                stderr="",
                timed_out=False,
            )
        )

        # Call the execution service.
        result = self.service.run_temporary_program(
            sandbox_id=self.sandbox_id,
            workspace_path=self.workspace_path,
            language="python",
        )

        # Verify the returned result type.
        self.assertIsInstance(
            result,
            SandboxExecutionResult,
        )

        # Verify the program output.
        self.assertEqual(result.return_code, 0)
        self.assertEqual(result.stdout, "Hello CodeView\n")
        self.assertEqual(result.stderr, "")
        self.assertFalse(result.timed_out)

        # Verify the executor received the correct arguments.
        self.temporary_executor.execute.assert_called_once_with(
            sandbox_id=self.sandbox_id,
            workspace_path=self.workspace_path,
            language="python",
        )

    def test_temporary_execution_timeout(self):
        """Verify that execution timeouts are reported."""

        # Simulate a program exceeding its time limit.
        self.temporary_executor.execute.return_value = (
            TemporaryContainerResult(
                return_code=-9,
                stdout="",
                stderr="",
                timed_out=True,
            )
        )

        result = self.service.run_temporary_program(
            sandbox_id=self.sandbox_id,
            workspace_path=self.workspace_path,
            language="python",
        )

        # Verify timeout information is preserved.
        self.assertTrue(result.timed_out)
        self.assertEqual(result.return_code, -9)

    def test_temporary_execution_failure(self):
        """Verify that container execution errors are propagated."""

        # Simulate Docker failing to execute the program.
        self.temporary_executor.execute.side_effect = (
            TemporaryContainerExecutionError(
                "Temporary container execution failed."
            )
        )

        # The service must not hide execution failures.
        with self.assertRaises(
            TemporaryContainerExecutionError
        ):
            self.service.run_temporary_program(
                sandbox_id=self.sandbox_id,
                workspace_path=self.workspace_path,
                language="python",
            )

    def test_javascript_execution(self):
        """Verify that JavaScript requests reach the executor."""

        self.temporary_executor.execute.return_value = (
            TemporaryContainerResult(
                return_code=0,
                stdout="Hello JavaScript\n",
                stderr="",
                timed_out=False,
            )
        )

        result = self.service.run_temporary_program(
            sandbox_id=self.sandbox_id,
            workspace_path=self.workspace_path,
            language="javascript",
        )

        self.assertEqual(result.stdout, "Hello JavaScript\n")

        self.temporary_executor.execute.assert_called_once_with(
            sandbox_id=self.sandbox_id,
            workspace_path=self.workspace_path,
            language="javascript",
        )


if __name__ == "__main__":
    unittest.main()