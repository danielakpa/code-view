"""Automated tests for the CodeView sandbox controller."""

import os
import unittest

from unittest.mock import patch

from fastapi.testclient import TestClient

from server_runner.sandbox_controller.main import app


class TestSandboxController(unittest.TestCase):
    """Test controller health, authentication, and configuration."""

    def setUp(self):
        """Prepare a test client and test authentication token."""

        self.client = TestClient(app)

        self.test_token = "codeview-controller-test-token"

    def test_health_check(self):
        """Verify that the health endpoint works."""

        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(
            data["service"],
            "codeview-sandbox-controller",
        )

        self.assertEqual(
            data["status"],
            "healthy",
        )

    def test_security_requires_authentication(self):
        """Reject requests without a controller token."""

        with patch.dict(
            os.environ,
            {"CODEVIEW_CONTROLLER_TOKEN": self.test_token},
        ):
            response = self.client.get("/internal/security")

        self.assertEqual(response.status_code, 401)

    def test_security_rejects_wrong_token(self):
        """Reject requests containing an incorrect token."""

        with patch.dict(
            os.environ,
            {"CODEVIEW_CONTROLLER_TOKEN": self.test_token},
        ):
            response = self.client.get(
                "/internal/security",
                headers={
                    "Authorization": "Bearer wrong-token",
                },
            )

        self.assertEqual(response.status_code, 401)

    def test_security_accepts_correct_token(self):
        """Allow an authenticated internal request."""

        with patch.dict(
            os.environ,
            {"CODEVIEW_CONTROLLER_TOKEN": self.test_token},
        ):
            response = self.client.get(
                "/internal/security",
                headers={
                    "Authorization": (
                        f"Bearer {self.test_token}"
                    ),
                },
            )

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(
            data["memory_limit_mb"],
            512,
        )

        self.assertEqual(
            data["process_limit"],
            64,
        )

        self.assertFalse(
            data["network_enabled"],
        )

        self.assertTrue(
            data["run_as_non_root"],
        )

    def test_missing_server_token_fails_closed(self):
        """Reject protected requests when no server token is configured."""

        with patch.dict(os.environ, {}, clear=True):
            response = self.client.get(
                "/internal/security",
                headers={
                    "Authorization": "Bearer anything",
                },
            )

        self.assertEqual(response.status_code, 503)

    def test_api_documentation_disabled(self):
        """Verify that automatic documentation endpoints are disabled."""

        response = self.client.get("/docs")

        self.assertEqual(response.status_code, 404)

        response = self.client.get("/openapi.json")

        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()