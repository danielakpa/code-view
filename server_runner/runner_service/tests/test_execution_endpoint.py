"""Tests for CodeView Runner's authenticated code execution endpoint."""

# ============================================================
# 1. IMPORTS
# ============================================================

import os
import unittest

from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4

import httpx

from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from server_runner.runner_service.main import app
from server_runner.runner_service.database import get_db
from server_runner.runner_service.execution_authorization import (
    ExecutionSandboxNotFoundError,
)


# ============================================================
# 2. EXECUTION ENDPOINT TESTS
# ============================================================

class ExecutionEndpointTests(unittest.TestCase):
    """Verify authentication, authorization, and Controller communication."""

    def setUp(self):
        """Prepare a valid request and mock database connection."""

        # Create a fake database session.
        self.db = MagicMock()

        # Replace FastAPI's real database dependency.
        app.dependency_overrides[get_db] = lambda: self.db

        # Create the HTTP test client.
        self.client = TestClient(app)

        # Configure the internal Runner authentication token.
        self.token_patch = patch.dict(
            os.environ,
            {"CODEVIEW_RUNNER_TOKEN": "test-runner-token"},
        )
        self.token_patch.start()

        # Prepare valid execution request data.
        self.payload = {
            "board_id": 10,
            "developer_id": 5,
            "group_id": 3,
            "language": "python",
            "source": 'print("Hello CodeView")',
        }

        # Authentication header used by Django.
        self.headers = {
            "Authorization": "Bearer test-runner-token",
        }

        # Prepare an authorized sandbox.
        self.sandbox = MagicMock()
        self.sandbox.sandbox_id = uuid4()

    def tearDown(self):
        """Remove test configuration and database overrides."""

        self.client.close()

        app.dependency_overrides.clear()

        self.token_patch.stop()

    # --------------------------------------------------------
    # TEST 1: MISSING AUTHENTICATION TOKEN
    # --------------------------------------------------------

    def test_missing_token_rejected(self):
        """Reject requests without authentication."""

        response = self.client.post(
            "/internal/executions",
            json=self.payload,
        )

        self.assertEqual(response.status_code, 401)

    # --------------------------------------------------------
    # TEST 2: INVALID AUTHENTICATION TOKEN
    # --------------------------------------------------------

    def test_invalid_token_rejected(self):
        """Reject requests with an incorrect Runner token."""

        response = self.client.post(
            "/internal/executions",
            headers={
                "Authorization": "Bearer wrong-token",
            },
            json=self.payload,
        )

        self.assertEqual(response.status_code, 401)

    # --------------------------------------------------------
    # TEST 3: EXTRA REQUEST FIELDS
    # --------------------------------------------------------

    def test_extra_fields_rejected(self):
        """Reject unexpected execution request fields."""

        payload = self.payload.copy()

        payload["is_admin"] = True

        response = self.client.post(
            "/internal/executions",
            headers=self.headers,
            json=payload,
        )

        self.assertEqual(response.status_code, 422)

    # --------------------------------------------------------
    # TEST 4: STRING DEVELOPER ID
    # --------------------------------------------------------

    def test_string_developer_id_rejected(self):
        """Reject developer IDs supplied as strings."""

        payload = self.payload.copy()

        payload["developer_id"] = "5"

        response = self.client.post(
            "/internal/executions",
            headers=self.headers,
            json=payload,
        )

        self.assertEqual(response.status_code, 422)

    # --------------------------------------------------------
    # TEST 5: SUCCESSFUL CODE EXECUTION
    # --------------------------------------------------------

    @patch(
        "server_runner.runner_service.main.ControllerClient"
    )
    @patch(
        "server_runner.runner_service.main.authorize_execution_sandbox"
    )
    def test_authorized_execution_reaches_controller(
        self,
        mock_authorize,
        mock_controller_class,
    ):
        """Forward authorized code to the Sandbox Controller."""

        # Simulate successful sandbox authorization.
        mock_authorize.return_value = self.sandbox

        # Simulate the Controller successfully executing code.
        mock_controller = mock_controller_class.return_value

        mock_controller.execute_code.return_value = {
            "status": "completed",
            "stdout": "Hello CodeView\n",
            "stderr": "",
            "exit_code": 0,
        }

        response = self.client.post(
            "/internal/executions",
            headers=self.headers,
            json=self.payload,
        )

        # Runner should return the Controller's result.
        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.json()["stdout"],
            "Hello CodeView\n",
        )

        # Verify sandbox ownership was checked.
        mock_authorize.assert_called_once_with(
            db=self.db,
            developer_id=5,
            group_id=3,
        )

        # Verify Controller execution was requested once.
        mock_controller.execute_code.assert_called_once()

        # Inspect the arguments sent to the Controller.
        arguments = mock_controller.execute_code.call_args.kwargs

        self.assertIsInstance(arguments["request_id"], UUID)

        self.assertEqual(
            arguments["sandbox_id"],
            self.sandbox.sandbox_id,
        )

        self.assertEqual(arguments["developer_id"], 5)
        self.assertEqual(arguments["group_id"], 3)
        self.assertEqual(arguments["language"], "python")

        self.assertEqual(
            arguments["source"],
            'print("Hello CodeView")',
        )

    # --------------------------------------------------------
    # TEST 6: MISSING SANDBOX
    # --------------------------------------------------------

    @patch(
        "server_runner.runner_service.main.authorize_execution_sandbox"
    )
    def test_missing_sandbox_returns_404(self, mock_authorize):
        """Reject execution when no sandbox exists."""

        mock_authorize.side_effect = ExecutionSandboxNotFoundError(
            "Sandbox not found."
        )

        response = self.client.post(
            "/internal/executions",
            headers=self.headers,
            json=self.payload,
        )

        self.assertEqual(response.status_code, 404)

    # --------------------------------------------------------
    # TEST 7: UNAUTHORIZED SANDBOX
    # --------------------------------------------------------

    @patch(
        "server_runner.runner_service.main.authorize_execution_sandbox"
    )
    def test_unauthorized_sandbox_returns_403(self, mock_authorize):
        """Reject execution when sandbox ownership verification fails."""

        mock_authorize.side_effect = PermissionError(
            "Sandbox access denied."
        )

        response = self.client.post(
            "/internal/executions",
            headers=self.headers,
            json=self.payload,
        )

        self.assertEqual(response.status_code, 403)

    # --------------------------------------------------------
    # TEST 8: SANDBOX NOT READY
    # --------------------------------------------------------

    @patch(
        "server_runner.runner_service.main.authorize_execution_sandbox"
    )
    def test_unready_sandbox_returns_409(self, mock_authorize):
        """Reject execution when the sandbox is not ready."""

        mock_authorize.side_effect = ValueError(
            "Sandbox is not ready."
        )

        response = self.client.post(
            "/internal/executions",
            headers=self.headers,
            json=self.payload,
        )

        self.assertEqual(response.status_code, 409)

    # --------------------------------------------------------
    # TEST 9: DATABASE FAILURE
    # --------------------------------------------------------

    @patch(
        "server_runner.runner_service.main.authorize_execution_sandbox"
    )
    def test_database_failure_returns_503(self, mock_authorize):
        """Handle PostgreSQL authorization failures."""

        mock_authorize.side_effect = OperationalError(
            "SELECT sandbox",
            {},
            Exception("Database unavailable"),
        )

        response = self.client.post(
            "/internal/executions",
            headers=self.headers,
            json=self.payload,
        )

        self.assertEqual(response.status_code, 503)

        self.db.rollback.assert_called_once()

    # --------------------------------------------------------
    # TEST 10: CONTROLLER CONNECTION FAILURE
    # --------------------------------------------------------

    @patch(
        "server_runner.runner_service.main.ControllerClient"
    )
    @patch(
        "server_runner.runner_service.main.authorize_execution_sandbox"
    )
    def test_controller_connection_failure_returns_503(
        self,
        mock_authorize,
        mock_controller_class,
    ):
        """Return HTTP 503 when the Controller cannot be reached."""

        mock_authorize.return_value = self.sandbox

        mock_controller = mock_controller_class.return_value

        mock_controller.execute_code.side_effect = httpx.ConnectError(
            "Connection refused."
        )

        response = self.client.post(
            "/internal/executions",
            headers=self.headers,
            json=self.payload,
        )

        self.assertEqual(response.status_code, 503)

    # --------------------------------------------------------
    # TEST 11: CONTROLLER AUTHORIZATION FAILURE
    # --------------------------------------------------------

    @patch(
        "server_runner.runner_service.main.ControllerClient"
    )
    @patch(
        "server_runner.runner_service.main.authorize_execution_sandbox"
    )
    def test_controller_authorization_failure_returns_403(
        self,
        mock_authorize,
        mock_controller_class,
    ):
        """Preserve HTTP 403 when the Controller rejects sandbox access."""

        mock_authorize.return_value = self.sandbox

        controller_request = httpx.Request(
            "POST",
            "http://controller-test:8002/internal/executions",
        )

        controller_response = httpx.Response(
            status_code=403,
            request=controller_request,
        )

        mock_controller = mock_controller_class.return_value

        mock_controller.execute_code.side_effect = (
            httpx.HTTPStatusError(
                "Forbidden",
                request=controller_request,
                response=controller_response,
            )
        )

        response = self.client.post(
            "/internal/executions",
            headers=self.headers,
            json=self.payload,
        )

        self.assertEqual(response.status_code, 403)

    # --------------------------------------------------------
    # TEST 12: CONTROLLER CONFIGURATION FAILURE
    # --------------------------------------------------------

    @patch(
        "server_runner.runner_service.main.ControllerClient"
    )
    @patch(
        "server_runner.runner_service.main.authorize_execution_sandbox"
    )
    def test_controller_configuration_failure_returns_503(
        self,
        mock_authorize,
        mock_controller_class,
    ):
        """Return HTTP 503 when Controller authentication is missing."""

        mock_authorize.return_value = self.sandbox

        mock_controller = mock_controller_class.return_value

        mock_controller.execute_code.side_effect = RuntimeError(
            "Controller token is not configured."
        )

        response = self.client.post(
            "/internal/executions",
            headers=self.headers,
            json=self.payload,
        )

        self.assertEqual(response.status_code, 503)


# ============================================================
# 3. RUN TESTS
# ============================================================

if __name__ == "__main__":
    unittest.main()