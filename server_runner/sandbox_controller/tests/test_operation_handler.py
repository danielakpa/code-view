"""Tests for CodeView sandbox operation handling."""

import unittest

from types import SimpleNamespace
from unittest.mock import Mock, patch
from uuid import uuid4

from server_runner.sandbox_controller.operation import (
    SandboxOperation,
    SandboxOperationRequest,
)

from server_runner.sandbox_controller.operation_handler import (
    SandboxOperationHandler,
)

from server_runner.sandbox_controller.replay import (
    ReplayProtectionError,
)


class TestSandboxOperationHandler(unittest.TestCase):
    """Test sandbox operation authorization and recording."""

    def setUp(self):
        """Prepare test database and operation request."""

        self.db = Mock()

        self.sandbox_id = uuid4()

        self.request = SandboxOperationRequest(
            request_id=uuid4(),
            sandbox_id=self.sandbox_id,
            developer_id=12,
            group_id=1,
            operation=SandboxOperation.START,
        )

        self.sandbox_record = SimpleNamespace(
            sandbox_id=self.sandbox_id,
            developer_id=12,
            group_id=1,
            status="prepared",
        )

    @patch(
        "server_runner.sandbox_controller.operation_handler."
        "authorize_database_sandbox_operation"
    )
    def test_valid_request_is_recorded(self, mock_authorize):
        """Record a valid operation request."""

        mock_authorize.return_value = self.sandbox_record

        handler = SandboxOperationHandler(self.db)

        # Simulate successful PostgreSQL insertion.
        with patch.object(
            handler.operation_service.replay_store,
            "claim_request",
            return_value=True,
        ) as mock_claim:

            result = handler.handle(self.request)

        self.assertEqual(result["status"], "recorded")
        self.assertEqual(result["operation"], "start")

        mock_authorize.assert_called_once()
        mock_claim.assert_called_once_with(self.request)

    @patch(
        "server_runner.sandbox_controller.operation_handler."
        "authorize_database_sandbox_operation"
    )
    def test_missing_sandbox_is_rejected(self, mock_authorize):
        """Reject an operation when the sandbox does not exist."""

        from server_runner.runner_service.sandbox.database_authorization import (
            SandboxNotFoundError,
        )

        mock_authorize.side_effect = SandboxNotFoundError(
            "Sandbox was not found."
        )

        handler = SandboxOperationHandler(self.db)

        with self.assertRaises(SandboxNotFoundError):
            handler.handle(self.request)

        self.db.execute.assert_not_called()

    @patch(
        "server_runner.sandbox_controller.operation_handler."
        "authorize_database_sandbox_operation"
    )
    def test_duplicate_request_is_rejected(self, mock_authorize):
        """Reject a request ID already recorded in PostgreSQL."""

        mock_authorize.return_value = self.sandbox_record

        handler = SandboxOperationHandler(self.db)

        with patch.object(
            handler.operation_service.replay_store,
            "claim_request",
            side_effect=ReplayProtectionError("Duplicate request."),
        ):
            with self.assertRaises(ReplayProtectionError):
                handler.handle(self.request)

    @patch(
        "server_runner.sandbox_controller.operation_handler."
        "authorize_database_sandbox_operation"
    )
    def test_wrong_owner_is_rejected(self, mock_authorize):
        """Reject a request that fails database ownership checks."""

        from server_runner.sandbox_controller.authorization import (
            SandboxAuthorizationError,
        )

        mock_authorize.side_effect = SandboxAuthorizationError(
            "Developer does not own this sandbox."
        )

        handler = SandboxOperationHandler(self.db)

        with self.assertRaises(SandboxAuthorizationError):
            handler.handle(self.request)

        self.db.execute.assert_not_called()


if __name__ == "__main__":
    unittest.main()