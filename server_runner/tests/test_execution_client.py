"""Tests for Django-to-FastAPI Code Board execution requests."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from django.test import SimpleTestCase, override_settings

from server_runner.client import (
    CodeExecutionRunnerClient,
    RunnerUnavailableError,
)


@override_settings(
    CODEVIEW_RUNNER_URL="http://runner-test:8001",
    CODEVIEW_RUNNER_TOKEN="test-secret-token",
)
class CodeExecutionRunnerClientTests(SimpleTestCase):
    """Test Runner communication without contacting FastAPI."""

    def setUp(self):
        """Create the client used by each test."""

        self.runner = CodeExecutionRunnerClient()

    async def test_successful_execution_request(self):
        """Check that the correct execution request is sent."""

        # Create a fake successful HTTP response.
        response = MagicMock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "status": "accepted",
            "execution_id": "execution-123",
        }

        # Create a fake asynchronous HTTP client.
        fake_client = AsyncMock()
        fake_client.post.return_value = response

        # Replace the real HTTP client with our fake client.
        with patch(
            "server_runner.client.httpx.AsyncClient"
        ) as mock_client:

            # Return our fake client when entering async with.
            mock_client.return_value.__aenter__.return_value = fake_client

            # Request execution.
            result = await self.runner.request_execution(
                board_id=10,
                developer_id=5,
                group_id=3,
            )

        # Check FastAPI's response.
        self.assertEqual(result["status"], "accepted")

        # Check the exact request Django would send.
        fake_client.post.assert_awaited_once_with(
            "http://runner-test:8001/internal/executions",
            headers={
                "Authorization": "Bearer test-secret-token",
            },
            json={
                "board_id": 10,
                "developer_id": 5,
                "group_id": 3,
            },
        )

    async def test_runner_connection_failure(self):
        """Convert network failures into RunnerUnavailableError."""

        # Create a fake HTTP client.
        fake_client = AsyncMock()

        # Simulate a connection failure.
        fake_client.post.side_effect = httpx.ConnectError(
            "Connection refused"
        )

        with patch(
            "server_runner.client.httpx.AsyncClient"
        ) as mock_client:

            mock_client.return_value.__aenter__.return_value = fake_client

            # Confirm that our application raises its own error.
            with self.assertRaises(RunnerUnavailableError):

                await self.runner.request_execution(
                    board_id=10,
                    developer_id=5,
                    group_id=3,
                )

    async def test_runner_rejects_execution(self):
        """Convert unsuccessful HTTP responses into an application error."""

        # Create a fake HTTP request.
        request = httpx.Request(
            "POST",
            "http://runner-test:8001/internal/executions",
        )

        # Create a fake HTTP 403 response.
        response = httpx.Response(
            status_code=403,
            request=request,
        )

        # Simulate FastAPI rejecting the request.
        fake_client = AsyncMock()
        fake_client.post.return_value = response

        with patch(
            "server_runner.client.httpx.AsyncClient"
        ) as mock_client:

            mock_client.return_value.__aenter__.return_value = fake_client

            with self.assertRaises(RunnerUnavailableError):

                await self.runner.request_execution(
                    board_id=10,
                    developer_id=5,
                    group_id=3,
                )