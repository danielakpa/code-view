"""
CodeView — Private Developer Terminal Sessions.

Responsibilities:
1. Identify each developer's private terminal session.
2. Keep terminal sessions separate between developers.
3. Keep sessions separate between project groups.
4. Represent the state of a terminal connection.

NOTE:
This file does not execute Linux commands.
Command execution will happen inside an isolated runner.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass
class TerminalSession:
    """Represent one developer's private terminal session."""

    # The project group this terminal belongs to.
    group_id: int

    # The developer who owns this terminal.
    developer_id: int

    # Unique identifier for this terminal session.
    session_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    # Whether the terminal is connected to its runner.
    is_connected: bool = False

    # When this session object was created.
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def get_workspace_key(self):
        """Return a unique workspace identifier for this developer and group."""

        return f"group_{self.group_id}_developer_{self.developer_id}"

    def connect(self):
        """Mark the terminal session as connected."""

        self.is_connected = True

    def disconnect(self):
        """Mark the terminal session as disconnected."""

        self.is_connected = False