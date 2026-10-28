"""Database models for CodeView terminal sessions."""

# Import Django's database models.
from django.db import models

# Import the configured user model.
from django.conf import settings

# Generate unique identifiers for terminal sessions.
import uuid


class DeveloperTerminalSession(models.Model):
    """Store a developer's terminal session information."""

    # Generate a unique session ID automatically.
    session_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    # Developer who owns this terminal session.
    developer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="terminal_sessions",
    )

    # Group this terminal session belongs to.
    group_id = models.PositiveBigIntegerField()

    # Current state of the terminal session.
    status = models.CharField(
        max_length=20,
        default="created",
    )

        # Track the runner's session registration state.
    runner_status = models.CharField(
        max_length=20,
        default="pending",
    )

    # Record when FastAPI last acknowledged the session.
    runner_registered_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    # Time the session was created.
    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    # Time the session was last updated.
    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        """Return a readable description of the session."""

        return f"{self.developer_id} - {self.session_id}"
        