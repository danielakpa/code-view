"""Tests for transactional sandbox operation handling."""

import unittest

from unittest.mock import MagicMock

from uuid import uuid4

from server_runner.sandbox_controller.operation import (
    SandboxOperation,
    SandboxOperationRequest,
)

from server_runner.sandbox_controller.operation_handler import (
    SandboxOperationHandler,
)


class TestSandboxOperationHandler(unittest.TestCase):

    def setUp(self):
        """Prepare mocked PostgreSQL records."""

        self.db = MagicMock()

        self.sandbox_id = uuid4()

        self.sandbox = MagicMock()
        self.sandbox.sandbox_id = self.sandbox_id
        self.sandbox.developer_id = 12
        self.sandbox.group_id = 5
        self.sandbox.status = "prepared"

        self.db.execute.return_value.scalar_one_or_none.return_value = (
            self.sandbox
        )

        self.handler = SandboxOperationHandler(self.db)

        # Mock replay insertion while testing handler coordination.
        self.handler.operation_service.replay_store.claim_request = (
            MagicMock(return_value=True)
        )

    def make_request(self, operation):
        """Build a valid sandbox operation request."""

        return SandboxOperationRequest(
            request_id=uuid4(),
            sandbox_id=self.sandbox_id,
            developer_id=12,
            group_id=5,
            operation=operation,
        )

    def test_start_updates_status(self):
        """Record startup and change the sandbox to starting."""

        result = self.handler.handle(
            self.make_request(SandboxOperation.START)
        )

        self.assertEqual(result["sandbox_status"], "starting")
        self.assertEqual(self.sandbox.status, "starting")
        self.db.commit.assert_called_once()

    def test_inspect_does_not_change_status(self):
        """Inspect should not change lifecycle status."""

        result = self.handler.handle(
            self.make_request(SandboxOperation.INSPECT)
        )

        self.assertEqual(result["sandbox_status"], "prepared")
        self.db.commit.assert_called_once()

    def test_invalid_transition_rolls_back(self):
        """Reject invalid lifecycle changes."""

        self.sandbox.status = "running"

        with self.assertRaises(ValueError):
            self.handler.handle(
                self.make_request(SandboxOperation.START)
            )

        self.db.commit.assert_not_called()
        self.db.rollback.assert_called_once()

    def test_missing_sandbox_rejected(self):
        """Reject unknown sandbox records."""

        self.db.execute.return_value.scalar_one_or_none.return_value = None

        with self.assertRaises(PermissionError):
            self.handler.handle(
                self.make_request(SandboxOperation.START)
            )

        self.db.commit.assert_not_called()
        self.db.rollback.assert_called_once()

    def test_replay_failure_rolls_back(self):
        """Roll back lifecycle changes when replay insertion fails."""

        self.handler.operation_service.replay_store.claim_request.side_effect = (
            RuntimeError("Replay database failure")
        )

        with self.assertRaises(RuntimeError):
            self.handler.handle(
                self.make_request(SandboxOperation.START)
            )

        self.db.commit.assert_not_called()
        self.db.rollback.assert_called_once()

    def test_stopped_sandbox_can_restart(self):
        """Allow a stopped sandbox to start again."""

        self.sandbox.status = "stopped"

        result = self.handler.handle(
            self.make_request(SandboxOperation.START)
        )

        self.assertEqual(result["sandbox_status"], "starting")


if __name__ == "__main__":
    unittest.main()