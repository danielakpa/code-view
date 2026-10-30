"""Tests for CodeView's Code Board Run endpoint."""

# ============================================================
# 1. IMPORTS
# ============================================================

# Mock external services without starting FastAPI or Docker.
from unittest.mock import AsyncMock, patch

# Get Django's configured user model.
from django.contrib.auth import get_user_model

# Django's database-backed testing tools.
from django.test import TestCase

# Generate URLs from Django route names.
from django.urls import reverse

# Import the Runner communication exception.
from server_runner.client import RunnerUnavailableError

# Import CodeView database models.
from community.models import (
    ProjectGroup,
    GroupCodeBoard,
    GroupMember,
)


User = get_user_model()


# ============================================================
# 2. CODE BOARD EXECUTION TESTS
# ============================================================

class RunCodeBoardTests(TestCase):
    """Verify Code Board permissions and Runner integration."""

    def setUp(self):
        """Prepare developers, a private group, and a Code Board."""

        # Create the developer who owns the group and Code Board.
        self.owner = User.objects.create_user(
            username="developer_one",
            password="TestPassword123!",
        )

        # Create another developer.
        self.other_user = User.objects.create_user(
            username="developer_two",
            password="TestPassword123!",
        )

        # Create a private development group.
        self.group = ProjectGroup.objects.create(
            name="Python Developers",
            description="A private group for Python developers.",
            owner=self.owner,
            is_private=True,
            join_policy="approval",
        )

        # Create the owner's Code Board.
        self.board = GroupCodeBoard.objects.create(
            group=self.group,
            owner=self.owner,
            language="python",
            code='print("Hello CodeView")',
        )

        # Build the Run endpoint URL.
        self.url = reverse(
            "run_code_board",
            kwargs={"group_id": self.group.pk},
        )

    # ========================================================
    # TEST 1: AUTHORIZED PYTHON EXECUTION
    # ========================================================

    @patch(
        "community.views.CodeExecutionRunnerClient.request_execution",
        new_callable=AsyncMock,
    )
    def test_owner_can_request_execution(self, mock_execution):
        """The owner can execute their Code Board through FastAPI."""

        # Simulate a successful response from FastAPI.
        mock_execution.return_value = {
            "status": "completed",
            "stdout": "Hello CodeView\n",
            "stderr": "",
            "exit_code": 0,
        }

        # Log in as the Code Board owner.
        self.client.force_login(self.owner)

        # Send a Run Code request to Django.
        response = self.client.post(self.url)

        # Django should return a successful response.
        self.assertEqual(response.status_code, 200)

        # Check the execution result.
        self.assertEqual(
            response.json()["status"],
            "completed",
        )

        self.assertEqual(
            response.json()["stdout"],
            "Hello CodeView\n",
        )

        # Verify Django sent the correct information to FastAPI.
        mock_execution.assert_awaited_once_with(
            board_id=self.board.pk,
            developer_id=self.owner.pk,
            group_id=self.group.pk,
            language="python",
            source='print("Hello CodeView")',
        )

    # ========================================================
    # TEST 2: ANONYMOUS USER
    # ========================================================

    @patch(
        "community.views.CodeExecutionRunnerClient.request_execution",
        new_callable=AsyncMock,
    )
    def test_anonymous_user_cannot_execute(self, mock_execution):
        """Developers must log in before executing code."""

        # Do not log in.
        response = self.client.post(self.url)

        # Django should redirect to the login page.
        self.assertEqual(response.status_code, 302)

        # No execution request should reach FastAPI.
        mock_execution.assert_not_awaited()

    # ========================================================
    # TEST 3: ANOTHER DEVELOPER'S CODE BOARD
    # ========================================================

    @patch(
        "community.views.CodeExecutionRunnerClient.request_execution",
        new_callable=AsyncMock,
    )
    def test_other_developer_cannot_execute_owner_board(
        self,
        mock_execution,
    ):
        """Developers cannot execute another developer's Code Board."""

        # Log in as another developer.
        self.client.force_login(self.other_user)

        # Attempt to run the owner's board.
        response = self.client.post(self.url)

        # Do not reveal another developer's private board.
        self.assertEqual(response.status_code, 404)

        # FastAPI must never receive this request.
        mock_execution.assert_not_awaited()

    # ========================================================
    # TEST 4: GET REQUEST
    # ========================================================

    @patch(
        "community.views.CodeExecutionRunnerClient.request_execution",
        new_callable=AsyncMock,
    )
    def test_get_request_is_rejected(self, mock_execution):
        """Code execution must use POST requests."""

        self.client.force_login(self.owner)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 405)

        mock_execution.assert_not_awaited()

    # ========================================================
    # TEST 5: UNSUPPORTED LANGUAGE
    # ========================================================

    @patch(
        "community.views.CodeExecutionRunnerClient.request_execution",
        new_callable=AsyncMock,
    )
    def test_unsupported_language_is_rejected(
        self,
        mock_execution,
    ):
        """Reject languages not supported by the Runner."""

        # Change the board to an unsupported language.
        self.board.language = "java"
        self.board.save()

        self.client.force_login(self.owner)

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 400)

        # Unsupported languages must not reach FastAPI.
        mock_execution.assert_not_awaited()

    # ========================================================
    # TEST 6: JAVASCRIPT EXECUTION
    # ========================================================

    @patch(
        "community.views.CodeExecutionRunnerClient.request_execution",
        new_callable=AsyncMock,
    )
    def test_supported_javascript_is_authorized(
        self,
        mock_execution,
    ):
        """JavaScript Code Boards can request execution."""

        # Save JavaScript code on the board.
        self.board.language = "javascript"
        self.board.code = 'console.log("Hello CodeView");'
        self.board.save()

        # Simulate the Runner's successful response.
        mock_execution.return_value = {
            "status": "completed",
            "stdout": "Hello CodeView\n",
            "stderr": "",
            "exit_code": 0,
        }

        self.client.force_login(self.owner)

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 200)

        # Confirm JavaScript was sent to FastAPI.
        mock_execution.assert_awaited_once_with(
            board_id=self.board.pk,
            developer_id=self.owner.pk,
            group_id=self.group.pk,
            language="javascript",
            source='console.log("Hello CodeView");',
        )

    # ========================================================
    # TEST 7: RUNNER SERVICE UNAVAILABLE
    # ========================================================

    @patch(
        "community.views.CodeExecutionRunnerClient.request_execution",
        new_callable=AsyncMock,
    )
    def test_runner_unavailable_returns_503(
        self,
        mock_execution,
    ):
        """Return HTTP 503 when the Runner cannot be reached."""

        # Simulate a network or service failure.
        mock_execution.side_effect = RunnerUnavailableError(
            "Runner is unavailable."
        )

        self.client.force_login(self.owner)

        response = self.client.post(self.url)

        # Django should handle the failure gracefully.
        self.assertEqual(response.status_code, 503)

        # Verify Django attempted execution.
        mock_execution.assert_awaited_once()

    # ========================================================
    # TEST 8: EMPTY SOURCE CODE
    # ========================================================

    @patch(
        "community.views.CodeExecutionRunnerClient.request_execution",
        new_callable=AsyncMock,
    )
    def test_empty_source_code_is_rejected(
        self,
        mock_execution,
    ):
        """Empty source code must not reach the Runner."""

        # Remove the saved source code.
        self.board.code = ""
        self.board.save()

        self.client.force_login(self.owner)

        response = self.client.post(self.url)

        # Empty source code is invalid.
        self.assertEqual(response.status_code, 400)

        # FastAPI must not receive the request.
        mock_execution.assert_not_awaited()