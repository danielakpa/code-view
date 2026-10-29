"""Tests for database-backed sandbox authorization."""

import unittest

from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

from server_runner.runner_service.sandbox.database_authorization import (
    SandboxNotFoundError,
    authorize_database_sandbox_operation,
)

from server_runner.sandbox_controller.authorization import (
    SandboxAuthorizationError,
)


class TestDatabaseSandboxAuthorization(unittest.TestCase):
    """Test authorization against trusted database records."""

    def setUp(self):
        """Prepare a fake database and sandbox record."""

        # Create a unique sandbox ID.
        self.sandbox_id = uuid4()

        # Simulate a sandbox loaded from PostgreSQL.
        self.sandbox_record = SimpleNamespace(
            sandbox_id=self.sandbox_id,
            developer_id=12,
            group_id=1,
            status="prepared",
        )

        # Create a fake database session.
        self.db = Mock()

        # Return the simulated record when db.get() is called.
        self.db.get.return_value = self.sandbox_record

    def test_owner_can_access_sandbox(self):
        """Allow the correct developer and group."""

        result = authorize_database_sandbox_operation(
            db=self.db,
            sandbox_id=self.sandbox_id,
            developer_id=12,
            group_id=1,
            operation="start",
        )

        self.assertEqual(
            result,
            self.sandbox_record,
        )

    def test_other_developer_is_rejected(self):
        """Reject another developer attempting access."""

        with self.assertRaises(SandboxAuthorizationError):
            authorize_database_sandbox_operation(
                db=self.db,
                sandbox_id=self.sandbox_id,
                developer_id=99,
                group_id=1,
                operation="start",
            )

    def test_wrong_group_is_rejected(self):
        """Reject an incorrect group."""

        with self.assertRaises(SandboxAuthorizationError):
            authorize_database_sandbox_operation(
                db=self.db,
                sandbox_id=self.sandbox_id,
                developer_id=12,
                group_id=99,
                operation="start",
            )

    def test_missing_sandbox_is_rejected(self):
        """Reject a sandbox that does not exist."""

        self.db.get.return_value = None

        with self.assertRaises(SandboxNotFoundError):
            authorize_database_sandbox_operation(
                db=self.db,
                sandbox_id=self.sandbox_id,
                developer_id=12,
                group_id=1,
                operation="start",
            )

    def test_invalid_sandbox_id_is_rejected(self):
        """Reject an invalid sandbox identifier."""

        with self.assertRaises(ValueError):
            authorize_database_sandbox_operation(
                db=self.db,
                sandbox_id="invalid-id",
                developer_id=12,
                group_id=1,
                operation="start",
            )

        # Invalid IDs should not trigger a database lookup.
        self.db.get.assert_not_called()

    def test_unsupported_operation_is_rejected(self):
        """Reject operations outside the allowed set."""

        with self.assertRaises(ValueError):
            authorize_database_sandbox_operation(
                db=self.db,
                sandbox_id=self.sandbox_id,
                developer_id=12,
                group_id=1,
                operation="delete_everything",
            )


if __name__ == "__main__":
    unittest.main()