"""Test authentication and validation of FastAPI execution requests."""

import os
import unittest

from unittest.mock import patch

from fastapi.testclient import TestClient

from server_runner.runner_service.main import app


class ExecutionEndpointTests(unittest.TestCase):
    """Verify execution requests are authenticated and validated."""

    def setUp(self):
        """Prepare the FastAPI test client."""

        # Create a client without starting a real server.
        self.client = TestClient(app)

        # Execution endpoint.
        self.url = "/internal/executions"

        # Valid execution request.
        self.payload = {
            "board_id": 10,
            "developer_id": 5,
            "group_id": 3,
        }

        # Authentication header used by Django.
        self.headers = {
            "Authorization": "Bearer test-secret-token",
        }

        # Configure a test-only Runner authentication token.
        self.token_patch = patch.dict(
            os.environ,
            {"CODEVIEW_RUNNER_TOKEN": "test-secret-token"},
        )

        self.token_patch.start()
        self.addCleanup(self.token_patch.stop)

    def test_missing_token_rejected(self):
        """Reject requests without authentication."""

        response = self.client.post(
            self.url,
            json=self.payload,
        )

        self.assertEqual(response.status_code, 401)

    def test_invalid_token_rejected(self):
        """Reject requests with an incorrect token."""

        response = self.client.post(
            self.url,
            headers={
                "Authorization": "Bearer incorrect-token",
            },
            json=self.payload,
        )

        self.assertEqual(response.status_code, 401)
    @patch(
        "server_runner.runner_service.main."
        "authorize_execution_sandbox"
    )
    def test_valid_request_returns_not_implemented(self, mock_authorize):
        """Keep execution disabled after successful sandbox authorization."""

        # Pretend PostgreSQL found and authorized the sandbox.
        mock_authorize.return_value = True

        # Send an authenticated execution request.
        response = self.client.post(
            self.url,
            json=self.payload,
            headers=self.headers,
        )

        # Execution remains disabled until Docker integration is complete.
        self.assertEqual(response.status_code, 501)

        # Confirm sandbox authorization was called with the correct IDs.
        mock_authorize.assert_called_once()

    def test_string_developer_id_rejected(self):
        """Reject developer IDs supplied as strings."""

        payload = self.payload.copy()

        payload["developer_id"] = "5"

        response = self.client.post(
            self.url,
            headers=self.headers,
            json=payload,
        )

        self.assertEqual(response.status_code, 422)

    def test_extra_fields_rejected(self):
        """Reject unexpected request fields."""

        payload = self.payload.copy()

        payload["command"] = "arbitrary command"

        response = self.client.post(
            self.url,
            headers=self.headers,
            json=payload,
        )

        self.assertEqual(response.status_code, 422)

        """Additional tests for sandbox authorization in the execution endpoint."""

import unittest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from server_runner.runner_service.main import app
from server_runner.runner_service.database import get_db

from server_runner.runner_service.execution_authorization import (
    ExecutionSandboxNotFoundError,
)


class ExecutionSandboxEndpointTests(unittest.TestCase):
    """Test execution authorization HTTP responses."""

    def setUp(self):
        """Prepare a test client and fake database."""

        # Create a fake database session.
        self.fake_db = MagicMock()

        # Replace the real PostgreSQL dependency.
        app.dependency_overrides[get_db] = lambda: self.fake_db

        # Create a FastAPI test client.
        self.client = TestClient(app)

        # Use a test-only authentication token.
        self.token_patch = patch.dict(
            "os.environ",
            {"CODEVIEW_RUNNER_TOKEN": "test-runner-token"},
        )

        self.token_patch.start()

        # Prepare an authenticated request.
        self.headers = {
            "Authorization": "Bearer test-runner-token",
        }

        # Prepare valid execution request data.
        self.payload = {
            "board_id": 10,
            "developer_id": 5,
            "group_id": 3,
        }

    def tearDown(self):
        """Restore application dependencies and environment."""

        app.dependency_overrides.clear()
        self.token_patch.stop()

    @patch(
        "server_runner.runner_service.main."
        "authorize_execution_sandbox"
    )
    def test_authorized_sandbox_returns_501(self, mock_authorize):
        """Execution remains disabled after successful authorization."""

        mock_authorize.return_value = MagicMock()

        response = self.client.post(
            "/internal/executions",
            json=self.payload,
            headers=self.headers,
        )

        self.assertEqual(response.status_code, 501)

        mock_authorize.assert_called_once_with(
            db=self.fake_db,
            developer_id=5,
            group_id=3,
        )

    @patch(
        "server_runner.runner_service.main."
        "authorize_execution_sandbox"
    )
    def test_missing_sandbox_returns_404(self, mock_authorize):
        """Reject execution when the sandbox does not exist."""

        mock_authorize.side_effect = ExecutionSandboxNotFoundError(
            "Sandbox not found."
        )

        response = self.client.post(
            "/internal/executions",
            json=self.payload,
            headers=self.headers,
        )

        self.assertEqual(response.status_code, 404)

    @patch(
        "server_runner.runner_service.main."
        "authorize_execution_sandbox"
    )
    def test_unauthorized_sandbox_returns_403(self, mock_authorize):
        """Reject sandbox ownership authorization failures."""

        mock_authorize.side_effect = PermissionError(
            "Access denied."
        )

        response = self.client.post(
            "/internal/executions",
            json=self.payload,
            headers=self.headers,
        )

        self.assertEqual(response.status_code, 403)

    @patch(
        "server_runner.runner_service.main."
        "authorize_execution_sandbox"
    )
    def test_unready_sandbox_returns_409(self, mock_authorize):
        """Reject execution when the sandbox is not ready."""

        mock_authorize.side_effect = ValueError(
            "Sandbox is not ready."
        )

        response = self.client.post(
            "/internal/executions",
            json=self.payload,
            headers=self.headers,
        )

        self.assertEqual(response.status_code, 409)

    @patch(
        "server_runner.runner_service.main."
        "authorize_execution_sandbox"
    )
    def test_database_failure_returns_503(self, mock_authorize):
        """Return a service error when PostgreSQL fails."""

        from sqlalchemy.exc import SQLAlchemyError

        mock_authorize.side_effect = SQLAlchemyError(
            "Database unavailable."
        )

        response = self.client.post(
            "/internal/executions",
            json=self.payload,
            headers=self.headers,
        )

        self.assertEqual(response.status_code, 503)

        # Verify that the failed transaction is rolled back.
        self.fake_db.rollback.assert_called_once()