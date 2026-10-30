"""Tests for CodeView's temporary code execution pipeline."""

import unittest

from unittest.mock import MagicMock
from uuid import uuid4

from server_runner.sandbox_controller.code_execution_pipeline import (
    CodeExecutionPipeline,
)

from server_runner.sandbox_controller.sandbox_execution import (
    SandboxExecutionResult,
)


class CodeExecutionPipelineTests(unittest.TestCase):
    """Verify execution preparation for supported languages."""

    def setUp(self):
        """Prepare a fake Docker execution service."""

        self.sandbox_id = uuid4()

        # Mock Docker so unit tests do not start real containers.
        self.execution_service = MagicMock()

        self.execution_service.run_temporary_program.return_value = (
            SandboxExecutionResult(
                return_code=0,
                stdout="Hello CodeView\n",
                stderr="",
                timed_out=False,
            )
        )

        self.pipeline = CodeExecutionPipeline(
            execution_service=self.execution_service,
        )

    def test_python_execution(self):
        """Prepare Python code for execution."""

        result = self.pipeline.execute(
            sandbox_id=self.sandbox_id,
            language="python",
            source='print("Hello CodeView")',
        )

        self.assertEqual(result.stdout, "Hello CodeView\n")

        self.assertEqual(
            self.execution_service.run_temporary_program.call_args.kwargs[
                "language"
            ],
            "python",
        )

    def test_go_execution(self):
        """Prepare Go code for execution."""

        self.pipeline.execute(
            sandbox_id=self.sandbox_id,
            language="go",
            source=(
                'package main\n'
                'import "fmt"\n'
                'func main() { fmt.Println("Hello CodeView") }\n'
            ),
        )

        self.assertEqual(
            self.execution_service.run_temporary_program.call_args.kwargs[
                "language"
            ],
            "go",
        )

    def test_javascript_execution(self):
        """Prepare JavaScript code for execution."""

        self.pipeline.execute(
            sandbox_id=self.sandbox_id,
            language="javascript",
            source='console.log("Hello CodeView");',
        )

        self.assertEqual(
            self.execution_service.run_temporary_program.call_args.kwargs[
                "language"
            ],
            "javascript",
        )

    def test_unsupported_language_rejected(self):
        """Reject unsupported programming languages."""

        with self.assertRaises(ValueError):
            self.pipeline.execute(
                sandbox_id=self.sandbox_id,
                language="php",
                source="<?php echo 'Hello'; ?>",
            )

        self.execution_service.run_temporary_program.assert_not_called()

    def test_invalid_sandbox_id_rejected(self):
        """Reject invalid sandbox identifiers."""

        with self.assertRaises(ValueError):
            self.pipeline.execute(
                sandbox_id="invalid",
                language="python",
                source="print(123)",
            )

        self.execution_service.run_temporary_program.assert_not_called()

    def test_workspace_cleaned_after_execution(self):
        """Remove temporary source files after execution."""

        self.pipeline.execute(
            sandbox_id=self.sandbox_id,
            language="python",
            source="print(123)",
        )

        # Retrieve the workspace path passed to our mocked executor.
        workspace = (
            self.execution_service.run_temporary_program
            .call_args.kwargs["workspace_path"]
        )

        # The temporary workspace must no longer exist.
        self.assertFalse(workspace.exists())

    def test_workspace_cleaned_after_execution_failure(self):
        """Remove temporary files even when Docker execution fails."""

        captured_paths = []

        def fail_execution(**kwargs):
            """Record the workspace before simulating a failure."""

            workspace = kwargs["workspace_path"]
            captured_paths.append(workspace)

            self.assertTrue(workspace.exists())

            raise RuntimeError("Simulated Docker failure.")

        self.execution_service.run_temporary_program.side_effect = (
            fail_execution
        )

        with self.assertRaises(RuntimeError):
            self.pipeline.execute(
                sandbox_id=self.sandbox_id,
                language="python",
                source="print(123)",
            )

        self.assertEqual(len(captured_paths), 1)
        self.assertFalse(captured_paths[0].exists())