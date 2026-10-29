"""Tests for CodeView sandbox replay protection."""

import unittest

from uuid import uuid4

from server_runner.sandbox_controller.operation import (
    SandboxOperation,
    SandboxOperationRequest,
)

from server_runner.sandbox_controller.replay import (
    InMemoryReplayStore,
    ReplayProtectionError,
)


class TestReplayProtection(unittest.TestCase):
    """Test duplicate request prevention."""

    def setUp(self):
        """Create a fresh replay store."""

        self.store = InMemoryReplayStore()

    def make_request(self, request_id=None):
        """Create a valid operation request."""

        return SandboxOperationRequest(
            request_id=request_id or uuid4(),
            sandbox_id=uuid4(),
            developer_id=12,
            group_id=1,
            operation=SandboxOperation.START,
        )

    def test_new_request_is_accepted(self):
        """Accept a new request."""

        request = self.make_request()

        self.assertTrue(
            self.store.claim_request(request)
        )

    def test_duplicate_request_is_rejected(self):
        """Reject the same request ID twice."""

        request_id = uuid4()

        first_request = self.make_request(request_id)
        second_request = self.make_request(request_id)

        self.store.claim_request(first_request)

        with self.assertRaises(ReplayProtectionError):
            self.store.claim_request(second_request)

    def test_different_requests_are_accepted(self):
        """Accept requests with different IDs."""

        self.assertTrue(
            self.store.claim_request(self.make_request())
        )

        self.assertTrue(
            self.store.claim_request(self.make_request())
        )

    def test_invalid_request_is_rejected(self):
        """Reject invalid request objects."""

        with self.assertRaises(ValueError):
            self.store.claim_request("invalid")

    def test_nil_request_id_is_rejected(self):
        """Reject a request containing an empty UUID."""

        from uuid import UUID
        from pydantic import ValidationError

        with self.assertRaises(ValidationError):
            SandboxOperationRequest(
                request_id=UUID(int=0),
                sandbox_id=uuid4(),
                developer_id=12,
                group_id=1,
                operation=SandboxOperation.START,
            )


if __name__ == "__main__":
    unittest.main()