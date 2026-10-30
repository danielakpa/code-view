"""Test the Sandbox Controller database connection."""

import os
import unittest

from unittest.mock import MagicMock, patch

from server_runner.sandbox_controller import database


class TestControllerDatabase(unittest.TestCase):
    """Verify database configuration and session cleanup."""

    def setUp(self):
        """Clear cached factories before each test."""
        database.create_controller_session_factory.cache_clear()

    def tearDown(self):
        """Clear cached factories after each test."""
        database.create_controller_session_factory.cache_clear()

    def test_missing_database_url(self):
        """Reject missing Controller database configuration."""

        with patch.dict(
            os.environ,
            {"CODEVIEW_CONTROLLER_DATABASE_URL": ""},
        ):
            with self.assertRaises(RuntimeError):
                database.create_controller_session_factory()

    @patch("server_runner.sandbox_controller.database.create_engine")
    @patch("server_runner.sandbox_controller.database.sessionmaker")
    def test_session_factory(self, mock_sessionmaker, mock_engine):
        """Create the engine using Controller credentials."""

        with patch.dict(
            os.environ,
            {
                "CODEVIEW_CONTROLLER_DATABASE_URL":
                    "postgresql://controller:password@localhost/codeview_db"
            },
        ):
            first = database.create_controller_session_factory()
            second = database.create_controller_session_factory()

        # The factory is reused.
        self.assertIs(first, second)

        # The engine is created only once.
        mock_engine.assert_called_once_with(
            "postgresql://controller:password@localhost/codeview_db",
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=5,
        )

        mock_sessionmaker.assert_called_once()

    @patch(
        "server_runner.sandbox_controller.database."
        "create_controller_session_factory"
    )
    def test_database_session_closes(self, mock_factory):
        """Close the session after the request finishes."""

        mock_session = MagicMock()
        mock_factory.return_value.return_value = mock_session

        generator = database.get_controller_db()

        session = next(generator)

        self.assertIs(session, mock_session)

        with self.assertRaises(StopIteration):
            next(generator)

        mock_session.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()