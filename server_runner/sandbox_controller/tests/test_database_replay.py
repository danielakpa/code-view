"""Tests for PostgreSQL sandbox replay protection."""

import unittest

from unittest.mock import MagicMock

from uuid import uuid4

from sqlalchemy.exc import IntegrityError

from server_runner.sandbox_controller.database_replay import (
    DatabaseReplayStore,
)

from server_runner.sandbox_controller.operation import (
    SandboxOperation,
    SandboxOperationRequest,
)

from server_runner.sandbox_controller.replay import (
    ReplayProtectionError,
)


class TestDatabaseReplayStore(unittest.TestCase):

    def setUp(self):
        """Create a mock database and replay store."""

        self.db = MagicMock()
        self.store = DatabaseReplayStore(self.db)

        self.request = SandboxOperationRequest(
            request_id=uuid4(),
            sandbox_id=uuid4(),
            developer_id=12,
            group_id=5,
            operation=SandboxOperation.START,
        )

    def test_new_request_is_inserted(self):
        """Insert an operation request without committing."""

        result = self.store.claim_request(self.request)

        self.assertTrue(result)
        self.db.execute.assert_called_once()
        self.db.commit.assert_not_called()

    def test_invalid_request_is_rejected(self):
        """Reject invalid request objects."""

        with self.assertRaises(ValueError):
            self.store.claim_request("invalid")

        self.db.execute.assert_not_called()
    def test_duplicate_request_is_rejected(self):
        """Identify duplicate request IDs."""

        # Simulate PostgreSQL reporting a duplicate key.
        original_error = Exception("duplicate key")

        # PostgreSQL error code for a unique constraint violation.
        original_error.sqlstate = "23505"

        # Simulate PostgreSQL diagnostic information.
        original_error.diag = MagicMock()

        # Explicitly set the diagnostic SQLSTATE.
        original_error.diag.sqlstate = "23505"

        # Identify the exact primary-key constraint.
        original_error.diag.constraint_name = (
            "sandbox_operation_requests_pkey"
        )

        # Simulate SQLAlchemy raising an IntegrityError.
        self.db.execute.side_effect = IntegrityError(
            "INSERT",
            {},
            original_error,
        )

        # Verify that duplicate requests are rejected.
        with self.assertRaises(ReplayProtectionError):
            self.store.claim_request(self.request)

        # The caller handles transaction rollback.
        self.db.rollback.assert_not_called()

    def test_database_failure_propagates(self):
        """Allow the caller to handle database failures."""

        self.db.execute.side_effect = RuntimeError(
            "Database unavailable"
        )

        with self.assertRaises(RuntimeError):
            self.store.claim_request(self.request)

        self.db.commit.assert_not_called()
        self.db.rollback.assert_not_called()


if __name__ == "__main__":
    unittest.main()