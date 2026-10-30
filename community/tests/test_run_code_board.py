"""Tests for CodeView's browser-based Code Board execution."""

from unittest.mock import AsyncMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from community.models import ProjectGroup, GroupCodeBoard
from server_runner.client import RunnerUnavailableError


User = get_user_model()


class RunCodeBoardTests(TestCase):
    """Test permissions, validation, and execution requests."""

    def setUp(self):
        """Create developers, a private group, and a Code Board."""

        self.owner = User.objects.create_user(
            username="developer_one",
            password="TestPassword123!",
        )

        self.other_user = User.objects.create_user(
            username="developer_two",
            password="TestPassword123!",
        )

        self.group = ProjectGroup.objects.create(
            name="Python Developers",
            description="A private group for developers.",
            owner=self.owner,
            is_private=True,
            join_policy="approval",
        )

        self.board = GroupCodeBoard.objects.create(
            group=self.group,
            owner=self.owner,
            language="python",
            code="Old saved code",
        )

        self.url = reverse(
            "run_code_board",
            kwargs={"group_id": self.group.pk},
        )

    # ========================================================
    # TEST 1: PYTHON EXECUTION
    # ========================================================

    @patch(
        "community.views.CodeExecutionRunnerClient.request_execution",
        new_callable=AsyncMock,
    )
    def test_owner_can_execute_python(self, mock_execution):
        """The owner can execute Python code from the browser."""

        mock_execution.return_value = {
            "status": "completed",
            "stdout": "Hello CodeView\n",
            "stderr": "",
            "exit_code": 0,
        }

        self.client.force_login(self.owner)

        response = self.client.post(
            self.url,
            {
                "language": "python",
                "code": 'print("Hello CodeView")',
            },
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.json()["stdout"],
            "Hello CodeView\n",
        )

        # Verify the Runner receives browser-submitted code.
        mock_execution.assert_awaited_once_with(
            board_id=self.board.pk,
            developer_id=self.owner.pk,
            group_id=self.group.pk,
            language="python",
            source='print("Hello CodeView")',
        )

        # Verify that execution does not overwrite saved code.
        self.board.refresh_from_db()

        self.assertEqual(
            self.board.code,
            "Old saved code",
        )

    # ========================================================
    # TEST 2: ANONYMOUS DEVELOPER
    # ========================================================

    @patch(
        "community.views.CodeExecutionRunnerClient.request_execution",
        new_callable=AsyncMock,
    )
    def test_anonymous_user_cannot_execute(self, mock_execution):
        """Anonymous users cannot execute code."""

        response = self.client.post(
            self.url,
            {
                "language": "python",
                "code": 'print("Hello")',
            },
        )

        self.assertEqual(response.status_code, 302)
        mock_execution.assert_not_awaited()

    # ========================================================
    # TEST 3: UNAUTHORIZED DEVELOPER
    # ========================================================

    @patch(
        "community.views.CodeExecutionRunnerClient.request_execution",
        new_callable=AsyncMock,
    )
    def test_other_developer_cannot_execute(self, mock_execution):
        """A developer cannot execute another owner's board."""

        self.client.force_login(self.other_user)

        response = self.client.post(
            self.url,
            {
                "language": "python",
                "code": 'print("Unauthorized")',
            },
        )

        self.assertEqual(response.status_code, 404)
        mock_execution.assert_not_awaited()

    # ========================================================
    # TEST 4: GET REQUEST
    # ========================================================

    @patch(
        "community.views.CodeExecutionRunnerClient.request_execution",
        new_callable=AsyncMock,
    )
    def test_get_request_is_rejected(self, mock_execution):
        """Execution must use POST."""

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
        """Reject unsupported programming languages."""

        self.client.force_login(self.owner)

        response = self.client.post(
            self.url,
            {
                "language": "java",
                "code": 'System.out.println("Hello");',
            },
        )

        self.assertEqual(response.status_code, 400)
        mock_execution.assert_not_awaited()

    # ========================================================
    # TEST 6: JAVASCRIPT EXECUTION
    # ========================================================

    @patch(
        "community.views.CodeExecutionRunnerClient.request_execution",
        new_callable=AsyncMock,
    )
    def test_javascript_execution(self, mock_execution):
        """JavaScript code can be executed."""

        mock_execution.return_value = {
            "status": "completed",
            "stdout": "Hello JavaScript\n",
            "stderr": "",
            "exit_code": 0,
        }

        self.client.force_login(self.owner)

        response = self.client.post(
            self.url,
            {
                "language": "javascript",
                "code": 'console.log("Hello JavaScript");',
            },
        )

        self.assertEqual(response.status_code, 200)

        mock_execution.assert_awaited_once_with(
            board_id=self.board.pk,
            developer_id=self.owner.pk,
            group_id=self.group.pk,
            language="javascript",
            source='console.log("Hello JavaScript");',
        )

    # ========================================================
    # TEST 7: RUNNER UNAVAILABLE
    # ========================================================

    @patch(
        "community.views.CodeExecutionRunnerClient.request_execution",
        new_callable=AsyncMock,
    )
    def test_runner_unavailable_returns_503(
        self,
        mock_execution,
    ):
        """Handle FastAPI connection failures."""

        mock_execution.side_effect = RunnerUnavailableError(
            "Runner unavailable."
        )

        self.client.force_login(self.owner)

        response = self.client.post(
            self.url,
            {
                "language": "python",
                "code": 'print("Hello")',
            },
        )

        self.assertEqual(response.status_code, 503)
        mock_execution.assert_awaited_once()

    # ========================================================
    # TEST 8: EMPTY SOURCE
    # ========================================================

    @patch(
        "community.views.CodeExecutionRunnerClient.request_execution",
        new_callable=AsyncMock,
    )
    def test_empty_source_is_rejected(self, mock_execution):
        """Empty code must not reach FastAPI."""

        self.client.force_login(self.owner)

        response = self.client.post(
            self.url,
            {
                "language": "python",
                "code": "   ",
            },
        )

        self.assertEqual(response.status_code, 400)
        mock_execution.assert_not_awaited()

    # ========================================================
    # TEST 9: OVERSIZED SOURCE
    # ========================================================

    @patch(
        "community.views.CodeExecutionRunnerClient.request_execution",
        new_callable=AsyncMock,
    )
    def test_oversized_source_is_rejected(self, mock_execution):
        """Reject source code larger than 256 KiB."""

        self.client.force_login(self.owner)

        response = self.client.post(
            self.url,
            {
                "language": "python",
                "code": "x" * (256 * 1024 + 1),
            },
        )

        self.assertEqual(response.status_code, 400)
        mock_execution.assert_not_awaited()

    # ========================================================
    # TEST 10: GO EXECUTION
    # ========================================================

    @patch(
        "community.views.CodeExecutionRunnerClient.request_execution",
        new_callable=AsyncMock,
    )
    def test_go_execution(self, mock_execution):
        """Go code can be sent to the Runner."""

        go_code = (
            'package main\n'
            'import "fmt"\n'
            'func main() { fmt.Println("Hello Go") }\n'
        )

        mock_execution.return_value = {
            "status": "completed",
            "stdout": "Hello Go\n",
            "stderr": "",
            "exit_code": 0,
        }

        self.client.force_login(self.owner)

        response = self.client.post(
            self.url,
            {
                "language": "go",
                "code": go_code,
            },
        )

        self.assertEqual(response.status_code, 200)

        mock_execution.assert_awaited_once_with(
            board_id=self.board.pk,
            developer_id=self.owner.pk,
            group_id=self.group.pk,
            language="go",
            source=go_code,
        )