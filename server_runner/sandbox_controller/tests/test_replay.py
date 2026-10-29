"""Tests for CodeView sandbox replay protection."""

import unittest

from uuid import UUID, uuid4

from server_runner.sandbox_controller.replay import (
    InMemoryReplayStore,
    ReplayProtectionError,
)


class TestReplayProtection(unittest.TestCase):
    """Test duplicate request prevention."""

    def setUp(self):
        """Create a fresh replay store."""

        self.store = InMemoryReplayStore()

    def test_new_request_is_accepted(self):
        """Accept a new request ID."""

        result = self.store.claim_request(uuid4())

        self.assertTrue(result)

    def test_duplicate_request_is_rejected(self):
        """Reject the same request ID twice."""

        request_id = uuid4()

        self.store.claim_request(request_id)

        with self.assertRaises(ReplayProtectionError):
            self.store.claim_request(request_id)

    def test_different_requests_are_accepted(self):
        """Accept two different request IDs."""

        self.assertTrue(self.store.claim_request(uuid4()))
        self.assertTrue(self.store.claim_request(uuid4()))

    def test_invalid_request_id_is_rejected(self):
        """Reject an incorrectly typed request ID."""

        with self.assertRaises(ValueError):
            self.store.claim_request("invalid")

    def test_nil_request_id_is_rejected(self):
        """Reject an empty UUID."""

        with self.assertRaises(ValueError):
            self.store.claim_request(UUID(int=0))


if __name__ == "__main__":
    unittest.main()