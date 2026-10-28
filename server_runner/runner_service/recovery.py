"""Recovery utilities for CodeView runner sessions."""

# Work with dates and times.
from datetime import datetime, timezone, timedelta

# Query PostgreSQL using SQLAlchemy.
from sqlalchemy import select

# Access our runner database.
from server_runner.runner_service.database import SessionLocal

# Access stored terminal sessions.
from server_runner.runner_service.models import RunnerSessionRecord


def find_stale_sessions(minutes=30):
    """Find registered sessions that have not been updated recently."""

    # Calculate the time before which sessions are considered stale.
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)

    # Open a PostgreSQL database session.
    with SessionLocal() as db:

        # Find registered sessions older than the cutoff.
        statement = select(RunnerSessionRecord).where(
            RunnerSessionRecord.status == "registered",
            RunnerSessionRecord.updated_at < cutoff,
        )

        # Execute the query.
        sessions = db.scalars(statement).all()

        # Return session information as dictionaries.
        return [
            {
                "session_id": str(session.session_id),
                "developer_id": session.developer_id,
                "group_id": session.group_id,
                "status": session.status,
            }
            for session in sessions
        ]