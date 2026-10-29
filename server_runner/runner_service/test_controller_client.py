"""Tests for the CodeView Sandbox Controller HTTP client."""

import os
import unittest

from unittest.mock import patch

import httpx

from server_runner.runner_service.controller_client import (
    SandboxControllerClient,
    SandboxControllerError,
)


class TestSandboxControllerClient(unittest.TestCase):
    """Test authenticated communication with the controller."""

    def setUp(self):
        """Prepare test environment settings."""

        self.environment = {
            "CODEVIEW_CONTROLLER_URL": "http://127.0.0.1:9100",
            "CODEVIEW_CONTROLLER_TOKEN": "test-controller-token",
        }

    def test_missing_controller_url(self):
        """Reject a missing controller URL."""

        with patch.dict(
            os.environ,
            {
                "CODEVIEW_CONTROLLER_URL": "",
                "CODEVIEW_CONTROLLER_TOKEN": "test-token",
            },
        ):
            with self.assertRaises(SandboxControllerError):
                SandboxControllerClient()

    def test_missing_controller_token(self):
        """Reject a missing controller token."""

        with patch.dict(
            os.environ,
            {
                "CODEVIEW_CONTROLLER_URL": "http://127.0.0.1:9100",
                "CODEVIEW_CONTROLLER_TOKEN": "",
            },
        ):
            with self.assertRaises(SandboxControllerError):
                SandboxControllerClient()

    def test_authentication_header(self):
        """Verify that the authentication header is correct."""

        with patch.dict(os.environ, self.environment):
            client = SandboxControllerClient()

        self.assertEqual(
            client._headers(),
            {
                "Authorization": "Bearer test-controller-token",
            },
        )

    def test_successful_security_request(self):
        """Verify that a successful HTTP request returns JSON."""

        # This function simulates the controller's response.
        def mock_handler(request):

            # Check the authentication token.
            self.assertEqual(
                request.headers["Authorization"],
                "Bearer test-controller-token",
            )

            # Check the requested endpoint.
            self.assertEqual(
                request.url.path,
                "/internal/security",
            )

            # Return a simulated successful response.
            return httpx.Response(
                200,
                json={
                    "memory_limit_mb": 512,
                    "network_enabled": False,
                },
            )

        # Create a fake HTTP transport.
        transport = httpx.MockTransport(mock_handler)

        # Create the real HTTP client BEFORE patching it.
        fake_client = httpx.Client(
            base_url=self.environment["CODEVIEW_CONTROLLER_URL"],
            transport=transport,
        )

        try:
            with patch.dict(os.environ, self.environment):

                client = SandboxControllerClient()

                # Replace only the HTTP client used by our code.
                with patch(
                    "server_runner.runner_service.controller_client.httpx.Client"
                ) as mocked_client:

                    # Return our prepared client from the context manager.
                    mocked_client.return_value.__enter__.return_value = (
                        fake_client
                    )

                    # Call the actual CodeView client method.
                    result = client.get_security_config()

            # Verify the response data.
            self.assertEqual(
                result["memory_limit_mb"],
                512,
            )

            self.assertFalse(
                result["network_enabled"],
            )

        finally:
            fake_client.close()

    def test_http_error_is_handled(self):
        """Verify that HTTP errors are handled correctly."""

        # Simulate an unauthorized response.
        def mock_handler(request):
            return httpx.Response(
                401,
                json={
                    "detail": "Unauthorized",
                },
            )

        # Create a fake transport.
        transport = httpx.MockTransport(mock_handler)

        # Create the HTTP client BEFORE patching.
        fake_client = httpx.Client(
            base_url=self.environment["CODEVIEW_CONTROLLER_URL"],
            transport=transport,
        )

        try:
            with patch.dict(os.environ, self.environment):

                client = SandboxControllerClient()

                with patch(
                    "server_runner.runner_service.controller_client.httpx.Client"
                ) as mocked_client:

                    mocked_client.return_value.__enter__.return_value = (
                        fake_client
                    )

                    # A 401 response must raise our custom exception.
                    with self.assertRaises(SandboxControllerError):
                        client.get_security_config()

        finally:
            fake_client.close()


if __name__ == "__main__":
    unittest.main()