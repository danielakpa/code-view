"""Tests for sandbox lifecycle database operations."""

import unittest

from unittest.mock import MagicMock

from uuid import uuid4

from server_runner.runner_service.sandbox.repository import (
    claim_sandbox_start,
    update_sandbox_status,
)


class TestSandboxRepository(unittest.TestCase):
    """Test sandbox lifecycle persistence logic."""

    def setUp(self):
        """Prepare a mock database and sandbox."""

        self.db = MagicMock()

        self.sandbox_id = uuid4()

        self.sandbox = MagicMock()

        self.sandbox.sandbox_id = self.sandbox_id
        self.sandbox.developer_id = 12
        self.sandbox.group_id = 5
        self.sandbox.status = "prepared"

        # Simulate PostgreSQL returning the sandbox.
        self.db.execute.return_value.scalar_one_or_none.return_value = (
            self.sandbox
        )

    def test_prepared_to_starting(self):
        """Allow a prepared sandbox to start."""

        result = update_sandbox_status(
            self.db,
            self.sandbox_id,
            "starting",
        )

        self.assertEqual(result.status, "starting")
        self.db.commit.assert_called_once()

    def test_starting_to_running(self):
        """Allow a starting sandbox to become running."""

        self.sandbox.status = "starting"

        result = update_sandbox_status(
            self.db,
            self.sandbox_id,
            "running",
        )

        self.assertEqual(result.status, "running")
        self.db.commit.assert_called_once()

    def test_invalid_transition(self):
        """Reject an invalid lifecycle transition."""

        with self.assertRaises(ValueError):
            update_sandbox_status(
                self.db,
                self.sandbox_id,
                "running",
            )

        self.db.commit.assert_not_called()
        self.db.rollback.assert_called_once()

    def test_missing_sandbox(self):
        """Reject a sandbox that doesn't exist."""

        self.db.execute.return_value.scalar_one_or_none.return_value = None

        with self.assertRaises(ValueError):
            update_sandbox_status(
                self.db,
                self.sandbox_id,
                "starting",
            )

        self.db.commit.assert_not_called()

    def test_claim_sandbox_start(self):
        """Claim startup for an owned sandbox."""

        result = claim_sandbox_start(
            db=self.db,
            sandbox_id=self.sandbox_id,
            developer_id=12,
            group_id=5,
        )

        self.assertEqual(result.status, "starting")
        self.db.commit.assert_called_once()

    def test_duplicate_start_rejected(self):
        """Reject starting a sandbox already starting."""

        self.sandbox.status = "starting"

        with self.assertRaises(ValueError):
            claim_sandbox_start(
                db=self.db,
                sandbox_id=self.sandbox_id,
                developer_id=12,
                group_id=5,
            )

        self.db.commit.assert_not_called()

    def test_wrong_developer_rejected(self):
        """Reject invalid developer identity."""

        with self.assertRaises(ValueError):
            claim_sandbox_start(
                db=self.db,
                sandbox_id=self.sandbox_id,
                developer_id=0,
                group_id=5,
            )

        self.db.commit.assert_not_called()

    def test_stopped_sandbox_can_restart(self):
        """Allow restarting a stopped sandbox."""

        self.sandbox.status = "stopped"

        result = claim_sandbox_start(
            db=self.db,
            sandbox_id=self.sandbox_id,
            developer_id=12,
            group_id=5,
        )

        self.assertEqual(result.status, "starting")


if __name__ == "__main__":
    unittest.main()