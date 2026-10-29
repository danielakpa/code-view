"""Tests for PostgreSQL-backed sandbox replay protection."""

import unittest

from unittest.mock import Mock
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


class FakePostgresError(Exception):
    """Simulate a PostgreSQL error with SQLSTATE information."""

    def __init__(self, sqlstate, constraint_name=None):
        super().__init__("Simulated PostgreSQL error")

        self.sqlstate = sqlstate

        self.diag = Mock()
        self.diag.sqlstate = sqlstate
        self.diag.constraint_name = constraint_name


class TestDatabaseReplayStore(unittest.TestCase):
    """Test database-backed request ID claiming."""

    def setUp(self):
        """Create a fake database session and request."""

        self.db = Mock()

        self.store = DatabaseReplayStore(self.db)

        self.request = SandboxOperationRequest(
            request_id=uuid4(),
            sandbox_id=uuid4(),
            developer_id=12,
            group_id=1,
            operation=SandboxOperation.START,
        )

    def test_new_request_is_saved(self):
        """Save a new request successfully."""

        result = self.store.claim_request(self.request)

        self.assertTrue(result)

        self.db.execute.assert_called_once()
        self.db.commit.assert_called_once()

    def test_duplicate_request_is_rejected(self):
        """Reject a duplicate request ID."""

        postgres_error = FakePostgresError(
            sqlstate="23505",
            constraint_name="sandbox_operation_requests_pkey",
        )

        self.db.execute.side_effect = IntegrityError(
            statement="INSERT",
            params={},
            orig=postgres_error,
        )

        with self.assertRaises(ReplayProtectionError):
            self.store.claim_request(self.request)

        self.db.rollback.assert_called_once()

    def test_other_integrity_error_is_not_called_replay(self):
        """Do not disguise unrelated database errors."""

        postgres_error = FakePostgresError(
            sqlstate="23503",
            constraint_name="some_foreign_key",
        )

        self.db.execute.side_effect = IntegrityError(
            statement="INSERT",
            params={},
            orig=postgres_error,
        )

        with self.assertRaises(IntegrityError):
            self.store.claim_request(self.request)

        self.db.rollback.assert_called_once()

    def test_database_failure_rolls_back(self):
        """Roll back when PostgreSQL encounters another error."""

        self.db.execute.side_effect = RuntimeError(
            "Database unavailable"
        )

        with self.assertRaises(RuntimeError):
            self.store.claim_request(self.request)

        self.db.rollback.assert_called_once()

    def test_invalid_request_is_rejected(self):
        """Reject invalid request objects before database access."""

        with self.assertRaises(ValueError):
            self.store.claim_request("invalid")

        self.db.execute.assert_not_called()


if __name__ == "__main__":
    unittest.main()