"""Manage CodeView developer terminal sessions."""

# Dataclass helps us create classes that store structured data.
from dataclasses import dataclass, field

# Generate unique session identifiers.
from uuid import uuid4

# Record when a session was created.
from datetime import datetime, timezone


@dataclass
class TerminalSession:
    """Represent a developer's terminal session."""

    # ID of the group the developer belongs to.
    group_id: int

    # ID of the developer who owns this session.
    developer_id: int

    # Generate a unique identifier for each session.
    session_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    # Record when the session was created.
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    # Track the current session state.
    status: str = "created"

    def get_workspace_key(self):
        """Return a unique workspace identifier."""

        return f"group-{self.group_id}-developer-{self.developer_id}"

    def connect(self):
        """Mark the session as connected."""

        self.status = "connected"

    def disconnect(self):
        """Mark the session as disconnected."""

        self.status = "disconnected"