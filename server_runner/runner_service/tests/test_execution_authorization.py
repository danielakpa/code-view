"""Tests for CodeView execution sandbox authorization."""

import unittest

from unittest.mock import MagicMock, patch
from uuid import uuid4

from server_runner.runner_service.execution_authorization import (
    authorize_execution_sandbox,
    ExecutionSandboxNotFoundError,
)


class ExecutionAuthorizationTests(unittest.TestCase):
    """Verify sandbox ownership and execution readiness."""

    def setUp(self):
        """Prepare a fake PostgreSQL session and sandbox."""

        self.db = MagicMock()

        self.sandbox = MagicMock()
        self.sandbox.sandbox_id = uuid4()
        self.sandbox.developer_id = 5
        self.sandbox.group_id = 3
        self.sandbox.status = "prepared"

        self.db.execute.return_value.scalar_one_or_none.return_value = (
            self.sandbox
        )

    @patch(
        "server_runner.runner_service.execution_authorization."
        "authorize_database_sandbox_operation"
    )
    def test_valid_sandbox_authorized(self, mock_authorize):
        """Allow an existing sandbox when authorization succeeds."""

        mock_authorize.return_value = self.sandbox

        result = authorize_execution_sandbox(
            db=self.db,
            developer_id=5,
            group_id=3,
        )

        self.assertEqual(result, self.sandbox)

        mock_authorize.assert_called_once_with(
            db=self.db,
            sandbox_id=self.sandbox.sandbox_id,
            developer_id=5,
            group_id=3,
            operation="run",
        )

    def test_missing_sandbox_rejected(self):
        """Reject execution when no sandbox exists."""

        self.db.execute.return_value.scalar_one_or_none.return_value = None

        with self.assertRaises(ExecutionSandboxNotFoundError):
            authorize_execution_sandbox(
                db=self.db,
                developer_id=5,
                group_id=3,
            )

    def test_invalid_developer_id_rejected(self):
        """Reject invalid developer IDs."""

        with self.assertRaises(ValueError):
            authorize_execution_sandbox(
                db=self.db,
                developer_id=-5,
                group_id=3,
            )

    @patch(
        "server_runner.runner_service.execution_authorization."
        "authorize_database_sandbox_operation"
    )
    def test_unready_sandbox_rejected(self, mock_authorize):
        """Reject sandboxes that are not ready for execution."""

        self.sandbox.status = "starting"
        mock_authorize.return_value = self.sandbox

        with self.assertRaises(ValueError):
            authorize_execution_sandbox(
                db=self.db,
                developer_id=5,
                group_id=3,
            )

    @patch(
        "server_runner.runner_service.execution_authorization."
        "authorize_database_sandbox_operation"
    )
    def test_authorization_failure_propagates(self, mock_authorize):
        """Reject execution when database authorization fails."""

        mock_authorize.side_effect = PermissionError(
            "Sandbox ownership mismatch."
        )

        with self.assertRaises(PermissionError):
            authorize_execution_sandbox(
                db=self.db,
                developer_id=5,
                group_id=3,
            )