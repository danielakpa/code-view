"""Tests for communication between the Runner and Sandbox Controller."""

# ============================================================
# 1. IMPORTS
# ============================================================

# Access environment variables.
import os

# Python's built-in testing framework.
import unittest

# Create fake objects and replace external dependencies.
from unittest.mock import MagicMock, patch

# Generate unique request and sandbox identifiers.
from uuid import uuid4

# Handle HTTP requests and HTTP errors.
import httpx

# Import the Controller client we want to test.
from server_runner.controller_client import ControllerClient


# ============================================================
# 2. CONTROLLER CLIENT TESTS
# ============================================================

class ControllerClientTests(unittest.TestCase):
    """Verify authenticated Runner-to-Controller communication."""

    def setUp(self):
        """Prepare valid Controller configuration and execution data."""

        # Configure the Controller URL and authentication token.
        self.environment_patch = patch.dict(
            os.environ,
            {
                "CODEVIEW_CONTROLLER_URL": "http://controller-test:8002",
                "CODEVIEW_CONTROLLER_TOKEN": "test-controller-token",
            },
        )

        self.environment_patch.start()

        # Create the Controller client.
        self.controller = ControllerClient()

        # Generate unique identifiers.
        self.request_id = uuid4()
        self.sandbox_id = uuid4()

        # Prepare the arguments used for execution.
        self.execution_data = {
            "request_id": self.request_id,
            "sandbox_id": self.sandbox_id,
            "developer_id": 5,
            "group_id": 3,
            "language": "python",
            "source": 'print("Hello CodeView")',
        }

    def tearDown(self):
        """Restore environment variables after each test."""

        self.environment_patch.stop()

    # --------------------------------------------------------
    # TEST 1: SUCCESSFUL EXECUTION REQUEST
    # --------------------------------------------------------

    @patch("server_runner.controller_client.httpx.Client")
    def test_successful_execution_request(self, mock_client_class):
        """Send the correct authenticated request to the Controller."""

        # Create a fake successful HTTP response.
        response = MagicMock()

        response.raise_for_status.return_value = None

        response.json.return_value = {
            "status": "completed",
            "stdout": "Hello CodeView\n",
            "stderr": "",
            "exit_code": 0,
        }

        # Create a fake HTTP client.
        fake_client = MagicMock()

        fake_client.post.return_value = response

        # Return the fake client when entering the context manager.
        mock_client_class.return_value.__enter__.return_value = fake_client

        # Request code execution.
        result = self.controller.execute_code(
            **self.execution_data
        )

        # Verify the returned execution result.
        self.assertEqual(result["status"], "completed")

        self.assertEqual(
            result["stdout"],
            "Hello CodeView\n",
        )

        # Verify the HTTP request contains the correct information.
        fake_client.post.assert_called_once_with(
            "http://controller-test:8002/internal/executions",
            headers={
                "Authorization": "Bearer test-controller-token",
            },
            json={
                "operation_request": {
                    "request_id": str(self.request_id),
                    "sandbox_id": str(self.sandbox_id),
                    "developer_id": 5,
                    "group_id": 3,
                    "operation": "run",
                },
                "language": "python",
                "source": 'print("Hello CodeView")',
            },
        )

        # Verify unsuccessful responses would be checked.
        response.raise_for_status.assert_called_once()

    # --------------------------------------------------------
    # TEST 2: MISSING AUTHENTICATION TOKEN
    # --------------------------------------------------------

    @patch("server_runner.controller_client.httpx.Client")
    def test_missing_controller_token_rejected(self, mock_client_class):
        """Reject execution when Controller authentication is missing."""

        # Remove the authentication token.
        with patch.dict(
            os.environ,
            {"CODEVIEW_CONTROLLER_TOKEN": ""},
        ):

            # Create a client with the missing token.
            controller = ControllerClient()

            # Execution must fail before sending an HTTP request.
            with self.assertRaises(RuntimeError):

                controller.execute_code(
                    **self.execution_data
                )

        # No HTTP client should have been created.
        mock_client_class.assert_not_called()

    # --------------------------------------------------------
    # TEST 3: CONTROLLER HTTP ERROR
    # --------------------------------------------------------

    @patch("server_runner.controller_client.httpx.Client")
    def test_controller_http_error_propagates(self, mock_client_class):
        """Preserve HTTP errors so the Runner can handle them."""

        # Create the HTTP request.
        request = httpx.Request(
            "POST",
            "http://controller-test:8002/internal/executions",
        )

        # Simulate an authorization failure.
        response = httpx.Response(
            status_code=403,
            request=request,
        )

        # Create a fake HTTP client.
        fake_client = MagicMock()

        fake_client.post.return_value = response

        # Configure the context manager.
        mock_client_class.return_value.__enter__.return_value = fake_client

        # The Controller client must raise the HTTP error.
        with self.assertRaises(httpx.HTTPStatusError):

            self.controller.execute_code(
                **self.execution_data
            )


# ============================================================
# 3. RUN TESTS
# ============================================================

if __name__ == "__main__":
    unittest.main()