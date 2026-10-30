"""Tests for CodeView's Code Board Run endpoint."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from community.models import (
    ProjectGroup,
    GroupCodeBoard,
    GroupMember,
)


User = get_user_model()


class RunCodeBoardTests(TestCase):
    """Verify that only authorized developers can run their own code."""

    def setUp(self):
        """Prepare test developers, a private group, and Code Boards."""

        # Create two developers.
        self.owner = User.objects.create_user(
            username="developer_one",
            password="TestPassword123!",
        )

        self.other_user = User.objects.create_user(
            username="developer_two",
            password="TestPassword123!",
        )

        # Create a valid private development group.
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

    def test_owner_can_request_execution(self):
        """The Code Board owner should be authorized."""

        # Log in as the owner.
        self.client.force_login(self.owner)

        # Send a POST request to the Run endpoint.
        response = self.client.post(self.url)

        # Check that authorization succeeds.
        self.assertEqual(response.status_code, 200)

        # Confirm the endpoint returns the expected status.
        self.assertEqual(
            response.json()["status"],
            "authorized",
        )

    def test_anonymous_user_cannot_execute(self):
        """Developers must log in before requesting execution."""

        response = self.client.post(self.url)

        # Django redirects anonymous users to the login page.
        self.assertEqual(response.status_code, 302)

    def test_other_developer_cannot_execute_owner_board(self):
        """A different developer cannot execute the owner's board."""

        # Log in as another developer.
        self.client.force_login(self.other_user)

        response = self.client.post(self.url)

        # The endpoint must not execute the owner's Code Board.
        self.assertEqual(response.status_code, 404)

    def test_get_request_is_rejected(self):
        """The Run endpoint accepts POST requests only."""

        self.client.force_login(self.owner)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 405)

    def test_unsupported_language_is_rejected(self):
        """Only Python, Go, and JavaScript are supported initially."""

        # Change the Code Board language.
        self.board.language = "java"
        self.board.save()

        self.client.force_login(self.owner)

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 400)

    def test_supported_javascript_is_authorized(self):
        """JavaScript Code Boards should pass authorization."""

        self.board.language = "javascript"
        self.board.save()

        self.client.force_login(self.owner)

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.json()["language"],
            "javascript",
        )