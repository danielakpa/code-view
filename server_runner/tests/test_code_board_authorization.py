"""Test authorization for executing private Code Boards."""

from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from server_runner.services import authorize_code_board_execution


class TestCodeBoardExecutionAuthorization(SimpleTestCase):
    """Verify that only authorized developers can execute Code Boards."""

    def setUp(self):
        """Create fake developers, a group, and a Code Board."""

        # Developer who owns the Code Board.
        self.owner = Mock()
        self.owner.pk = 12
        self.owner.is_authenticated = True

        # Another developer in the same group.
        self.other_developer = Mock()
        self.other_developer.pk = 20
        self.other_developer.is_authenticated = True

        # Developer who has not logged in.
        self.anonymous_user = Mock()
        self.anonymous_user.is_authenticated = False

        # Private development group.
        self.group = Mock()
        self.group.pk = 5
        self.group.is_private = True
        self.group.owner_id = 12

        # Private Code Board belonging to developer 12.
        self.board = Mock()
        self.board.pk = 15
        self.board.owner_id = 12
        self.board.group = self.group

    @patch("server_runner.services.authorize_private_group_access")
    @patch("server_runner.services.GroupCodeBoard.objects")
    def test_owner_can_execute(
        self,
        mock_boards,
        mock_group_access,
    ):
        """Allow the authenticated owner to execute their Code Board."""

        mock_boards.select_related.return_value.filter.return_value.first.return_value = (
            self.board
        )

        result = authorize_code_board_execution(
            user=self.owner,
            board_id=15,
        )

        self.assertEqual(result, self.board)

        mock_group_access.assert_called_once_with(
            user=self.owner,
            group=self.group,
        )

    @patch("server_runner.services.authorize_private_group_access")
    @patch("server_runner.services.GroupCodeBoard.objects")
    def test_other_group_member_cannot_execute(
        self,
        mock_boards,
        mock_group_access,
    ):
        """Reject another developer trying to execute the owner's board."""

        mock_boards.select_related.return_value.filter.return_value.first.return_value = (
            self.board
        )

        with self.assertRaises(PermissionError):
            authorize_code_board_execution(
                user=self.other_developer,
                board_id=15,
            )

    @patch("server_runner.services.authorize_private_group_access")
    @patch("server_runner.services.GroupCodeBoard.objects")
    def test_developer_outside_group_cannot_execute(
        self,
        mock_boards,
        mock_group_access,
    ):
        """Reject developers without permission to access the group."""

        mock_boards.select_related.return_value.filter.return_value.first.return_value = (
            self.board
        )

        # Simulate the group authorization function rejecting access.
        mock_group_access.side_effect = PermissionError(
            "Developer is not a group member."
        )

        with self.assertRaises(PermissionError):
            authorize_code_board_execution(
                user=self.other_developer,
                board_id=15,
            )

    @patch("server_runner.services.GroupCodeBoard.objects")
    def test_anonymous_developer_cannot_execute(self, mock_boards):
        """Reject developers who are not authenticated."""

        with self.assertRaises(PermissionError):
            authorize_code_board_execution(
                user=self.anonymous_user,
                board_id=15,
            )

        # Anonymous users must be rejected before querying the Code Board.
        mock_boards.select_related.assert_not_called()

    @patch("server_runner.services.GroupCodeBoard.objects")
    def test_nonexistent_board_is_rejected(self, mock_boards):
        """Reject Code Boards that do not exist."""

        mock_boards.select_related.return_value.filter.return_value.first.return_value = (
            None
        )

        with self.assertRaises(PermissionError):
            authorize_code_board_execution(
                user=self.owner,
                board_id=999,
            )