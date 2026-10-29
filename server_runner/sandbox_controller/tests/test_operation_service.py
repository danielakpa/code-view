"""Tests for CodeView sandbox operation authorization."""

import unittest

from uuid import uuid4

from server_runner.sandbox_controller.authorization import (
    SandboxAuthorizationError,
    SandboxIdentity,
)

from server_runner.sandbox_controller.operation import (
    SandboxOperation,
    SandboxOperationRequest,
)

from server_runner.sandbox_controller.operation_service import (
    SandboxOperationService,
)

from server_runner.sandbox_controller.replay import (
    ReplayProtectionError,
)


class TestSandboxOperationService(unittest.TestCase):
    """Test sandbox operation validation and replay protection."""

    def setUp(self):
        """Prepare a trusted sandbox identity."""

        self.sandbox_id = uuid4()

        self.identity = SandboxIdentity(
            sandbox_id=self.sandbox_id,
            developer_id=12,
            group_id=1,
        )

        self.service = SandboxOperationService()

    def make_request(
        self,
        developer_id=12,
        group_id=1,
        sandbox_id=None,
        request_id=None,
    ):
        """Create a valid sandbox operation request."""

        return SandboxOperationRequest(
            request_id=request_id or uuid4(),
            sandbox_id=sandbox_id or self.sandbox_id,
            developer_id=developer_id,
            group_id=group_id,
            operation=SandboxOperation.START,
        )

    def test_authorized_request_is_accepted(self):
        """Accept a request matching the trusted identity."""

        request = self.make_request()

        result = self.service.validate_and_claim(
            request,
            self.identity,
        )

        self.assertEqual(result, request)

    def test_wrong_developer_is_rejected(self):
        """Reject another developer."""

        request = self.make_request(developer_id=99)

        with self.assertRaises(SandboxAuthorizationError):
            self.service.validate_and_claim(
                request,
                self.identity,
            )

    def test_wrong_group_is_rejected(self):
        """Reject another group."""

        request = self.make_request(group_id=99)

        with self.assertRaises(SandboxAuthorizationError):
            self.service.validate_and_claim(
                request,
                self.identity,
            )

    def test_wrong_sandbox_is_rejected(self):
        """Reject a different sandbox."""

        request = self.make_request(sandbox_id=uuid4())

        with self.assertRaises(PermissionError):
            self.service.validate_and_claim(
                request,
                self.identity,
            )

    def test_duplicate_request_is_rejected(self):
        """Reject the same request ID twice."""

        request_id = uuid4()

        first_request = self.make_request(
            request_id=request_id,
        )

        second_request = self.make_request(
            request_id=request_id,
        )

        # First request succeeds.
        self.service.validate_and_claim(
            first_request,
            self.identity,
        )

        # Second request must fail.
        with self.assertRaises(ReplayProtectionError):
            self.service.validate_and_claim(
                second_request,
                self.identity,
            )

    def test_unauthorized_request_does_not_claim_id(self):
        """Ensure rejected requests don't consume request IDs."""

        request_id = uuid4()

        unauthorized = self.make_request(
            developer_id=99,
            request_id=request_id,
        )

        with self.assertRaises(SandboxAuthorizationError):
            self.service.validate_and_claim(
                unauthorized,
                self.identity,
            )

        authorized = self.make_request(
            request_id=request_id,
        )

        result = self.service.validate_and_claim(
            authorized,
            self.identity,
        )

        self.assertEqual(result, authorized)


if __name__ == "__main__":
    unittest.main()