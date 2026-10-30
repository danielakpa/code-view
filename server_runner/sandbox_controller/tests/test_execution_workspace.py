"""Tests for temporary CodeView execution workspaces."""

import unittest

from pathlib import Path

from server_runner.sandbox_controller.code_snapshot import (
    CodeSnapshot,
    prepare_code_snapshot,
)

from server_runner.sandbox_controller.execution_workspace import (
    ExecutionWorkspaceError,
    temporary_execution_workspace,
)


class ExecutionWorkspaceTests(unittest.TestCase):
    """Verify temporary execution file preparation and cleanup."""

    def test_python_source_file_created(self):
        """Create a Python file containing the correct source code."""

        snapshot = prepare_code_snapshot(
            language="python",
            source='print("Hello CodeView")',
        )

        with temporary_execution_workspace(snapshot) as workspace:
            source_file = workspace / "main.py"

            self.assertTrue(source_file.exists())

            self.assertEqual(
                source_file.read_text(encoding="utf-8"),
                'print("Hello CodeView")',
            )

    def test_go_source_file_created(self):
        """Create a Go source file."""

        snapshot = prepare_code_snapshot(
            language="go",
            source="package main\nfunc main() {}",
        )

        with temporary_execution_workspace(snapshot) as workspace:
            self.assertTrue(
                (workspace / "main.go").exists()
            )

    def test_javascript_source_file_created(self):
        """Create a JavaScript source file."""

        snapshot = prepare_code_snapshot(
            language="javascript",
            source='console.log("Hello CodeView")',
        )

        with temporary_execution_workspace(snapshot) as workspace:
            self.assertTrue(
                (workspace / "main.js").exists()
            )

    def test_workspace_deleted_after_use(self):
        """Delete temporary files after the context finishes."""

        snapshot = prepare_code_snapshot(
            language="python",
            source="print(123)",
        )

        with temporary_execution_workspace(snapshot) as workspace:
            saved_path = Path(workspace)

            self.assertTrue(saved_path.exists())

        self.assertFalse(saved_path.exists())

    def test_workspace_deleted_after_exception(self):
        """Clean up even when execution raises an exception."""

        snapshot = prepare_code_snapshot(
            language="python",
            source="print(123)",
        )

        saved_path = None

        with self.assertRaises(RuntimeError):
            with temporary_execution_workspace(snapshot) as workspace:
                saved_path = Path(workspace)

                raise RuntimeError("Simulated execution failure.")

        self.assertIsNotNone(saved_path)
        self.assertFalse(saved_path.exists())

    def test_invalid_snapshot_rejected(self):
        """Reject objects that are not CodeSnapshot instances."""

        with self.assertRaises(ExecutionWorkspaceError):
            with temporary_execution_workspace("invalid"):
                pass

    def test_unexpected_filename_rejected(self):
        """Reject snapshots containing an unsafe filename."""

        snapshot = CodeSnapshot(
            language="python",
            filename="../../danger.py",
            source="print(123)",
        )

        with self.assertRaises(ExecutionWorkspaceError):
            with temporary_execution_workspace(snapshot):
                pass