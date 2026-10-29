"""Tests for authorized sandbox operation preparation."""

import unittest

from types import SimpleNamespace
from unittest.mock import Mock, patch
from uuid import UUID, uuid4

from server_runner.runner_service.sandbox.operation_dispatch import (
    SandboxOperationDispatcher,
)

from server_runner.sandbox_controller.authorization import (
    SandboxAuthorizationError,
)

from server_runner.sandbox_controller.operation import (
    SandboxOperation,
)


class TestSandboxOperationDispatcher(unittest.TestCase):
    """Test sandbox operation preparation."""

    def setUp(self):
        """Prepare a fake database and sandbox."""

        self.db = Mock()

        self.sandbox_id = uuid4()

        self.sandbox_record = SimpleNamespace(
            sandbox_id=self.sandbox_id,
            developer_id=12,
            group_id=1,
            status="prepared",
        )

        self.dispatcher = SandboxOperationDispatcher(self.db)

    @patch(
        "server_runner.runner_service.sandbox.operation_dispatch."
        "authorize_database_sandbox_operation"
    )
    def test_owner_can_prepare_start_request(self, mock_authorize):
        """Allow the verified sandbox owner."""

        mock_authorize.return_value = self.sandbox_record

        request = self.dispatcher.prepare_operation(
            sandbox_id=self.sandbox_id,
            authenticated_developer_id=12,
            authorized_group_id=1,
            operation=SandboxOperation.START,
        )

        self.assertIsInstance(request.request_id, UUID)
        self.assertEqual(request.sandbox_id, self.sandbox_id)
        self.assertEqual(request.developer_id, 12)
        self.assertEqual(request.group_id, 1)
        self.assertEqual(request.operation, SandboxOperation.START)

        mock_authorize.assert_called_once_with(
            db=self.db,
            sandbox_id=self.sandbox_id,
            developer_id=12,
            group_id=1,
            operation="start",
        )

    @patch(
        "server_runner.runner_service.sandbox.operation_dispatch."
        "authorize_database_sandbox_operation"
    )
    def test_wrong_owner_is_rejected(self, mock_authorize):
        """Reject requests for another developer's sandbox."""

        mock_authorize.side_effect = SandboxAuthorizationError(
            "Developer does not own this sandbox."
        )

        with self.assertRaises(SandboxAuthorizationError):
            self.dispatcher.prepare_operation(
                sandbox_id=self.sandbox_id,
                authenticated_developer_id=99,
                authorized_group_id=1,
                operation=SandboxOperation.START,
            )

    @patch(
        "server_runner.runner_service.sandbox.operation_dispatch."
        "authorize_database_sandbox_operation"
    )
    def test_wrong_group_is_rejected(self, mock_authorize):
        """Reject operations outside the authorized group."""

        mock_authorize.side_effect = SandboxAuthorizationError(
            "Sandbox does not belong to this group."
        )

        with self.assertRaises(SandboxAuthorizationError):
            self.dispatcher.prepare_operation(
                sandbox_id=self.sandbox_id,
                authenticated_developer_id=12,
                authorized_group_id=99,
                operation=SandboxOperation.START,
            )

    def test_invalid_operation_is_rejected(self):
        """Reject unsupported operation types."""

        with self.assertRaises(ValueError):
            self.dispatcher.prepare_operation(
                sandbox_id=self.sandbox_id,
                authenticated_developer_id=12,
                authorized_group_id=1,
                operation="delete_everything",
            )

    @patch(
        "server_runner.runner_service.sandbox.operation_dispatch."
        "authorize_database_sandbox_operation"
    )
    def test_each_request_has_unique_id(self, mock_authorize):
        """Give separate requests different IDs."""

        mock_authorize.return_value = self.sandbox_record

        first = self.dispatcher.prepare_operation(
            self.sandbox_id,
            12,
            1,
            SandboxOperation.START,
        )

        second = self.dispatcher.prepare_operation(
            self.sandbox_id,
            12,
            1,
            SandboxOperation.START,
        )

        self.assertNotEqual(
            first.request_id,
            second.request_id,
        )


if __name__ == "__main__":
    unittest.main()