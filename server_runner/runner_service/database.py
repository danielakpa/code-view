"""Database connection for the CodeView Runner Service."""

# Read environment variables.
import os

# Locate the project directory.
from pathlib import Path

# Load environment variables from .env.
from dotenv import load_dotenv

# SQLAlchemy database utilities.
from sqlalchemy import create_engine

# Create database sessions.
from sqlalchemy.orm import sessionmaker


# Locate CodeView's project root.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load the project's environment variables.
load_dotenv(BASE_DIR / ".env")


# Read the runner's PostgreSQL connection URL.
DATABASE_URL = os.getenv("CODEVIEW_RUNNER_DATABASE_URL")

# Stop startup if the database URL is missing.
if not DATABASE_URL:
    raise RuntimeError(
        "CODEVIEW_RUNNER_DATABASE_URL is not configured."
    )


# Create the PostgreSQL database engine.
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)


# Create a factory for database sessions.
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def get_db():
    """Provide a database session for each FastAPI request."""

    # Open a database session.
    db = SessionLocal()

    try:
        # Give the database session to the endpoint.
        yield db

    finally:
        # Close the database session after the request.
        db.close()
        

def create_runner_tables():
    """Create runner database tables if they do not exist."""

    # Import our SQLAlchemy database model.
    from server_runner.runner_service.models import Base

    # Create missing tables in PostgreSQL.
    Base.metadata.create_all(bind=engine)