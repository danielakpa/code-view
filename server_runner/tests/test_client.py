"""Tests for the CodeView Runner Service client."""

import unittest

from unittest.mock import AsyncMock, patch

from django.test import SimpleTestCase, override_settings

from server_runner.client import TerminalRunnerClient


@override_settings(
    CODEVIEW_RUNNER_URL="http://127.0.0.1:9000",
    CODEVIEW_RUNNER_TOKEN="test-secret-token",
)
class TestTerminalRunnerClient(SimpleTestCase):
    """Test communication with the runner service."""

    @patch("server_runner.client.httpx.AsyncClient")
    async def test_get_status(self, mock_client):
        """Check that Django sends an authenticated request."""

        # Create the expected runner response.
        expected_data = {
            "service": "codeview-runner",
            "authenticated": True,
            "status": "ready",
        }

        # Mock the HTTP response.
        mock_response = AsyncMock()

        # JSON parsing is synchronous, so return a normal dictionary.
        mock_response.json = lambda: expected_data

        # Mock the asynchronous HTTP client.
        mock_http_client = AsyncMock()

        mock_http_client.get.return_value = mock_response

        # Configure the async context manager.
        mock_client.return_value.__aenter__.return_value = mock_http_client

        # Create the runner client.
        client = TerminalRunnerClient()

        # Call the runner status endpoint.
        result = await client.get_status()

        # Verify the returned response.
        self.assertEqual(result, expected_data)

        # Verify the correct token was included.
        mock_http_client.get.assert_awaited_once_with(
            "http://127.0.0.1:9000/internal/status",
            headers={
                "Authorization": "Bearer test-secret-token",
            },
        )