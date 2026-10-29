"""Tests for CodeView sandbox operation request validation."""

import unittest

from uuid import UUID, uuid4

from pydantic import ValidationError

from server_runner.sandbox_controller.operation import (
    SandboxOperation,
    SandboxOperationRequest,
)


class TestSandboxOperationRequest(unittest.TestCase):
    """Test sandbox operation request validation."""

    def setUp(self):
        """Prepare valid operation request data."""

        self.valid_data = {
            "request_id": uuid4(),
            "sandbox_id": uuid4(),
            "developer_id": 12,
            "group_id": 1,
            "operation": SandboxOperation.START,
        }

    def test_valid_request(self):
        """Accept a correctly structured request."""

        request = SandboxOperationRequest(**self.valid_data)

        self.assertEqual(request.developer_id, 12)
        self.assertEqual(request.operation, SandboxOperation.START)

    def test_invalid_developer_id(self):
        """Reject a developer ID of zero."""

        data = self.valid_data.copy()
        data["developer_id"] = 0

        with self.assertRaises(ValidationError):
            SandboxOperationRequest(**data)

    def test_invalid_group_id(self):
        """Reject a negative group ID."""

        data = self.valid_data.copy()
        data["group_id"] = -1

        with self.assertRaises(ValidationError):
            SandboxOperationRequest(**data)

    def test_boolean_developer_id(self):
        """Reject True as a developer ID."""

        data = self.valid_data.copy()
        data["developer_id"] = True

        with self.assertRaises(ValidationError):
            SandboxOperationRequest(**data)

    def test_invalid_operation(self):
        """Reject an unsupported operation."""

        data = self.valid_data.copy()
        data["operation"] = "delete_everything"

        with self.assertRaises(ValidationError):
            SandboxOperationRequest(**data)

    def test_extra_field(self):
        """Reject unexpected request fields."""

        data = self.valid_data.copy()
        data["is_admin"] = True

        with self.assertRaises(ValidationError):
            SandboxOperationRequest(**data)

    def test_nil_request_id(self):
        """Reject an empty request UUID."""

        data = self.valid_data.copy()
        data["request_id"] = UUID(int=0)

        with self.assertRaises(ValidationError):
            SandboxOperationRequest(**data)

    def test_nil_sandbox_id(self):
        """Reject an empty sandbox UUID."""

        data = self.valid_data.copy()
        data["sandbox_id"] = UUID(int=0)

        with self.assertRaises(ValidationError):
            SandboxOperationRequest(**data)


if __name__ == "__main__":
    unittest.main()