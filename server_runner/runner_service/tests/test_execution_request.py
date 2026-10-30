"""Tests for FastAPI Code Board execution request validation."""

import unittest

from pydantic import ValidationError

from server_runner.runner_service.execution_request import (
    CodeExecutionRequest,
)


class CodeExecutionRequestTests(unittest.TestCase):
    """Check that execution requests contain valid IDs."""

    def test_valid_request(self):
        """Accept valid positive integer IDs."""

        request = CodeExecutionRequest(
            board_id=10,
            developer_id=5,
            group_id=3,
        )

        self.assertEqual(request.board_id, 10)
        self.assertEqual(request.developer_id, 5)
        self.assertEqual(request.group_id, 3)

    def test_negative_id_rejected(self):
        """Reject negative database IDs."""

        with self.assertRaises(ValidationError):
            CodeExecutionRequest(
                board_id=-10,
                developer_id=5,
                group_id=3,
            )

    def test_string_id_rejected(self):
        """Reject string values instead of integer IDs."""

        with self.assertRaises(ValidationError):
            CodeExecutionRequest(
                board_id="10",
                developer_id=5,
                group_id=3,
            )

    def test_unexpected_field_rejected(self):
        """Reject fields that do not belong in the request."""

        with self.assertRaises(ValidationError):
            CodeExecutionRequest(
                board_id=10,
                developer_id=5,
                group_id=3,
                command="rm -rf /",
            )

    def test_missing_field_rejected(self):
        """Reject requests missing required information."""

        with self.assertRaises(ValidationError):
            CodeExecutionRequest(
                board_id=10,
                developer_id=5,
            )