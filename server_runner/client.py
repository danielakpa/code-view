"""
CodeView — Isolated Terminal Runner Client.

Responsibilities:
1. Represent communication with the isolated runner.
2. Keep runner configuration separate from Django consumers.
3. Provide an interface for opening terminal sessions.
4. Provide an interface for sending terminal input.
5. Provide an interface for closing terminal sessions.

IMPORTANT:
This file does not execute Linux commands.
The isolated runner service will be implemented separately.
"""


class RunnerUnavailableError(Exception):
    """Raised when the isolated terminal runner is unavailable."""


class TerminalRunnerClient:
    """Communicate with CodeView's isolated terminal runner."""

    def __init__(self):
        """Initialize the terminal runner client."""

        # The runner service is not connected yet.
        self.is_connected = False

    async def open_session(self, session):
        """Request a private terminal session from the runner."""

        # Do not pretend that a runner session exists.
        raise RunnerUnavailableError(
            "The isolated terminal runner is not configured yet."
        )

    async def send_input(self, session_id, data):
        """Forward terminal keyboard input to the runner."""

        # Commands must never execute on the Django host.
        raise RunnerUnavailableError(
            "Cannot send input: terminal runner is unavailable."
        )

    async def resize_terminal(self, session_id, columns, rows):
        """Request a terminal size change."""

        # Terminal resizing requires a running PTY.
        raise RunnerUnavailableError(
            "Cannot resize terminal: runner is unavailable."
        )

    async def close_session(self, session_id):
        """Request that the runner close a terminal session."""

        # Runner cleanup will be implemented with the runner service.
        raise RunnerUnavailableError(
            "Cannot close session: runner is unavailable."
        )