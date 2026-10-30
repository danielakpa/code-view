"""Tests for CodeView source-code snapshot validation."""

import unittest

from server_runner.sandbox_controller.code_snapshot import (
    MAX_CODE_BYTES,
    prepare_code_snapshot,
)


class CodeSnapshotTests(unittest.TestCase):
    """Test source-code validation before execution."""

    def test_python_snapshot(self):
        """Prepare Python source code."""

        snapshot = prepare_code_snapshot(
            language="python",
            source='print("Hello CodeView")',
        )

        self.assertEqual(snapshot.filename, "main.py")
        self.assertEqual(snapshot.language, "python")

    def test_go_snapshot(self):
        """Prepare Go source code."""

        snapshot = prepare_code_snapshot(
            language="go",
            source='package main\nfunc main() {}',
        )

        self.assertEqual(snapshot.filename, "main.go")

    def test_javascript_snapshot(self):
        """Prepare JavaScript source code."""

        snapshot = prepare_code_snapshot(
            language="javascript",
            source='console.log("Hello CodeView")',
        )

        self.assertEqual(snapshot.filename, "main.js")

    def test_unsupported_language_rejected(self):
        """Reject unsupported languages."""

        with self.assertRaises(ValueError):
            prepare_code_snapshot(
                language="php",
                source="<?php echo 'Hello'; ?>",
            )

    def test_empty_source_rejected(self):
        """Reject empty source code."""

        with self.assertRaises(ValueError):
            prepare_code_snapshot(
                language="python",
                source="   ",
            )

    def test_non_string_source_rejected(self):
        """Reject source code that is not text."""

        with self.assertRaises(ValueError):
            prepare_code_snapshot(
                language="python",
                source=123,
            )

    def test_oversized_source_rejected(self):
        """Reject source code exceeding the size limit."""

        with self.assertRaises(ValueError):
            prepare_code_snapshot(
                language="python",
                source="a" * (MAX_CODE_BYTES + 1),
            )