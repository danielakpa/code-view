"""Tests for CodeView sandbox authorization."""

import unittest

from uuid import uuid4

from server_runner.sandbox_controller.authorization import (
    SandboxIdentity,
    SandboxAuthorizationError,
    authorize_sandbox_operation,
    validate_sandbox_identity,
)


class TestSandboxAuthorization(unittest.TestCase):
    """Verify sandbox authorization rules."""

    def setUp(self):
        """Create a sample sandbox identity."""

        self.sandbox = SandboxIdentity(
            sandbox_id=uuid4(),
            developer_id=12,
            group_id=1,
        )

    def test_valid_sandbox_identity(self):
        """Accept a correctly structured identity."""

        result = validate_sandbox_identity(self.sandbox)

        self.assertEqual(result, self.sandbox)

    def test_owner_can_start_sandbox(self):
        """Allow matching developer and group IDs."""

        result = authorize_sandbox_operation(
            sandbox=self.sandbox,
            developer_id=12,
            group_id=1,
            operation="start",
        )

        self.assertTrue(result)

    def test_owner_can_stop_sandbox(self):
        """Allow a matching developer to stop their sandbox."""

        result = authorize_sandbox_operation(
            sandbox=self.sandbox,
            developer_id=12,
            group_id=1,
            operation="stop",
        )

        self.assertTrue(result)

    def test_other_developer_cannot_access_sandbox(self):
        """Reject a different developer ID."""

        with self.assertRaises(SandboxAuthorizationError):
            authorize_sandbox_operation(
                sandbox=self.sandbox,
                developer_id=99,
                group_id=1,
                operation="start",
            )

    def test_wrong_group_cannot_access_sandbox(self):
        """Reject operations targeting the wrong group."""

        with self.assertRaises(SandboxAuthorizationError):
            authorize_sandbox_operation(
                sandbox=self.sandbox,
                developer_id=12,
                group_id=99,
                operation="start",
            )

    def test_unsupported_operation_is_rejected(self):
        """Reject operations outside the allowlist."""

        with self.assertRaises(ValueError):
            authorize_sandbox_operation(
                sandbox=self.sandbox,
                developer_id=12,
                group_id=1,
                operation="delete_everything",
            )

    def test_invalid_developer_id_is_rejected(self):
        """Reject invalid developer IDs."""

        with self.assertRaises(ValueError):
            authorize_sandbox_operation(
                sandbox=self.sandbox,
                developer_id=0,
                group_id=1,
                operation="start",
            )

    def test_invalid_group_id_is_rejected(self):
        """Reject invalid group IDs."""

        with self.assertRaises(ValueError):
            authorize_sandbox_operation(
                sandbox=self.sandbox,
                developer_id=12,
                group_id=-1,
                operation="start",
            )

    def test_boolean_id_is_rejected(self):
        """Ensure True is not accepted as developer ID 1."""

        with self.assertRaises(ValueError):
            authorize_sandbox_operation(
                sandbox=self.sandbox,
                developer_id=True,
                group_id=1,
                operation="start",
            )

    def test_invalid_sandbox_uuid_is_rejected(self):
        """Reject identities with incorrectly typed sandbox IDs."""

        invalid_sandbox = SandboxIdentity(
            sandbox_id="not-a-uuid",
            developer_id=12,
            group_id=1,
        )

        with self.assertRaises(ValueError):
            validate_sandbox_identity(invalid_sandbox)


if __name__ == "__main__":
    unittest.main()