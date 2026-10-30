"""Test the Sandbox Controller's internal code execution endpoint."""

# ============================================================
# 1. IMPORTS
# ============================================================

import os
import unittest

from copy import deepcopy
from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from server_runner.runner_service.database import get_db

from server_runner.sandbox_controller.main import app

from server_runner.sandbox_controller.replay import (
    ReplayProtectionError,
)


# ============================================================
# 2. CONTROLLER EXECUTION ENDPOINT TESTS
# ============================================================

class TestControllerExecutionEndpoint(unittest.TestCase):
    """Test authentication, validation, authorization, and execution."""

    def setUp(self):
        """Prepare the test client and mock database."""

        # Create a fake database session.
        self.db = MagicMock()

        # Prevent tests from connecting to the real database.
        app.dependency_overrides[get_db] = lambda: self.db

        # Create a FastAPI test client.
        self.client = TestClient(app)

        # Prepare a valid execution request.
        self.payload = {
            "operation_request": {
                "request_id": str(uuid4()),
                "sandbox_id": str(uuid4()),
                "developer_id": 5,
                "group_id": 3,
                "operation": "run",
            },
            "language": "python",
            "source": "print('Hello CodeView')",
        }

        # Configure a temporary authentication token.
        self.token_patcher = patch.dict(
            os.environ,
            {
                "CODEVIEW_CONTROLLER_TOKEN": "test-controller-token",
            },
        )

        self.token_patcher.start()

    def tearDown(self):
        """Clean up after each test."""

        # Remove database dependency overrides.
        app.dependency_overrides.clear()

        # Restore the original environment.
        self.token_patcher.stop()

        # Close the test client.
        self.client.close()

    # ========================================================
    # 3. TEST HELPER
    # ========================================================

    def authenticated_post(self, payload=None):
        """Send an authenticated execution request."""

        return self.client.post(
            "/internal/executions",
            headers={
                "Authorization": "Bearer test-controller-token",
            },
            json=self.payload if payload is None else payload,
        )

    # ========================================================
    # 4. AUTHENTICATION TESTS
    # ========================================================

    def test_missing_token_is_rejected(self):
        """Reject requests without authentication."""

        response = self.client.post(
            "/internal/executions",
            json=self.payload,
        )

        self.assertEqual(response.status_code, 401)

    def test_invalid_token_is_rejected(self):
        """Reject requests with an incorrect token."""

        response = self.client.post(
            "/internal/executions",
            headers={
                "Authorization": "Bearer incorrect-token",
            },
            json=self.payload,
        )

        self.assertEqual(response.status_code, 401)

    # ========================================================
    # 5. VALIDATION TEST
    # ========================================================

    def test_invalid_request_is_rejected(self):
        """Reject unsupported programming languages."""

        # Copy the request without changing the original.
        payload = deepcopy(self.payload)

        # Supply an unsupported language.
        payload["language"] = "unsupported-language"

        response = self.authenticated_post(payload)

        self.assertEqual(response.status_code, 422)

    # ========================================================
    # 6. SUCCESSFUL EXECUTION TEST
    # ========================================================

    @patch(
        "server_runner.sandbox_controller.main.SandboxOperationHandler"
    )
    @patch(
        "server_runner.sandbox_controller.main.CodeExecutionPipeline"
    )
    def test_successful_execution(
        self,
        mock_pipeline_class,
        mock_handler_class,
    ):
        """Authorized requests must reach the execution pipeline."""

        expected_result = {
            "stdout": "Hello CodeView\n",
            "stderr": "",
            "exit_code": 0,
        }

        # Simulate successful Docker execution.
        mock_pipeline_class.return_value.execute.return_value = (
            expected_result
        )

        response = self.authenticated_post()

        # The endpoint should return the execution result.
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_result)

        # Authorization must happen.
        mock_handler_class.return_value.handle.assert_called_once()

        # Docker execution must happen exactly once.
        mock_pipeline_class.return_value.execute.assert_called_once_with(
            sandbox_id=UUID(
                self.payload["operation_request"]["sandbox_id"]
            ),
            language="python",
            source="print('Hello CodeView')",
        )

    # ========================================================
    # 7. AUTHORIZATION TEST
    # ========================================================

    @patch(
        "server_runner.sandbox_controller.main.SandboxOperationHandler"
    )
    @patch(
        "server_runner.sandbox_controller.main.CodeExecutionPipeline"
    )
    def test_unauthorized_sandbox_is_rejected(
        self,
        mock_pipeline_class,
        mock_handler_class,
    ):
        """Unauthorized sandbox access must return HTTP 403."""

        # Simulate an authorization failure.
        mock_handler_class.return_value.handle.side_effect = (
            PermissionError(
                "Sandbox not found or access denied."
            )
        )

        response = self.authenticated_post()

        self.assertEqual(response.status_code, 403)

        # Unauthorized requests must never execute code.
        mock_pipeline_class.return_value.execute.assert_not_called()

    # ========================================================
    # 8. DOCKER FAILURE TEST
    # ========================================================

    @patch(
        "server_runner.sandbox_controller.main.SandboxOperationHandler"
    )
    @patch(
        "server_runner.sandbox_controller.main.CodeExecutionPipeline"
    )
    def test_docker_failure_returns_service_unavailable(
        self,
        mock_pipeline_class,
        mock_handler_class,
    ):
        """Docker infrastructure failures must return HTTP 503."""

        # Simulate Docker being unavailable.
        mock_pipeline_class.return_value.execute.side_effect = (
            RuntimeError("Docker unavailable.")
        )

        response = self.authenticated_post()

        self.assertEqual(response.status_code, 503)

        # Authorization must have been attempted.
        mock_handler_class.return_value.handle.assert_called_once()

    # ========================================================
    # 9. REPLAY PROTECTION TEST
    # ========================================================

    @patch(
        "server_runner.sandbox_controller.main.SandboxOperationHandler"
    )
    @patch(
        "server_runner.sandbox_controller.main.CodeExecutionPipeline"
    )
    def test_replayed_request_is_rejected(
        self,
        mock_pipeline_class,
        mock_handler_class,
    ):
        """A replayed request must return HTTP 409 without execution."""

        # Simulate PostgreSQL detecting a previously used request ID.
        mock_handler_class.return_value.handle.side_effect = (
            ReplayProtectionError(
                "Sandbox operation request has already been used."
            )
        )

        response = self.authenticated_post()

        # Duplicate requests must return HTTP 409.
        self.assertEqual(response.status_code, 409)

        # Confirm the response describes the replay failure.
        self.assertIn(
            "already been used",
            response.json()["detail"],
        )

        # A replayed request must never reach Docker.
        mock_pipeline_class.return_value.execute.assert_not_called()

    # ========================================================
    # 10. INVALID LIFECYCLE TEST
    # ========================================================

    @patch(
        "server_runner.sandbox_controller.main.SandboxOperationHandler"
    )
    @patch(
        "server_runner.sandbox_controller.main.CodeExecutionPipeline"
    )
    def test_invalid_sandbox_lifecycle_is_rejected(
        self,
        mock_pipeline_class,
        mock_handler_class,
    ):
        """An unready sandbox must return HTTP 409."""

        # Simulate a sandbox that is not ready to execute code.
        mock_handler_class.return_value.handle.side_effect = (
            ValueError(
                "Sandbox is not ready for code execution."
            )
        )

        response = self.authenticated_post()

        self.assertEqual(response.status_code, 409)

        # Invalid lifecycle operations must not reach Docker.
        mock_pipeline_class.return_value.execute.assert_not_called()


if __name__ == "__main__":
    unittest.main()