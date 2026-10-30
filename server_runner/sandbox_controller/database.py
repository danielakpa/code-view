"""Database connection for the CodeView Sandbox Controller."""

import os

from collections.abc import Generator
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


# Locate CodeView's project directory.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load environment variables.
load_dotenv(BASE_DIR / ".env")


@lru_cache(maxsize=1)
def create_controller_session_factory():
    """
    Create one reusable database session factory.

    SQLAlchemy manages a connection pool behind the engine.
    """

    # Read the Controller's dedicated database URL.
    database_url = os.getenv(
        "CODEVIEW_CONTROLLER_DATABASE_URL"
    )

    # Reject missing configuration.
    if not database_url:
        raise RuntimeError(
            "CODEVIEW_CONTROLLER_DATABASE_URL is not configured."
        )

    # Create the engine once per application process.
    engine = create_engine(
        database_url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=5,
    )

    # Create the reusable session factory.
    return sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )


def get_controller_db() -> Generator[Session, None, None]:
    """Provide a database session for one Controller request."""

    # Reuse the existing session factory.
    session_factory = create_controller_session_factory()

    # Create a separate session for this request.
    db = session_factory()

    try:
        # Give the session to the endpoint.
        yield db

    finally:
        # Always close the session.
        db.close()