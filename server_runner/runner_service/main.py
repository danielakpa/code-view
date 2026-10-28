"""Main entry point for the CodeView Runner Service."""

# Import os to read configuration from environment variables.
import os

# Import secrets for secure token comparison.
import secrets

# FastAPI creates our API application and handles HTTP requests.
from fastapi import Depends, FastAPI, Header, HTTPException, status

# Locate the project's root directory.
from pathlib import Path

# Load environment variables from a .env file.
from dotenv import load_dotenv


# Create the runner service application.
app = FastAPI(
    title="CodeView Runner Service",
    description="Private service for managing CodeView developer environments.",
    version="1.0.0",
)


def verify_runner_token(
    authorization: str | None = Header(default=None),
):
    """Verify that a request has the correct runner service token."""

    # Read the expected token from the environment.
    expected_token = os.environ.get("CODEVIEW_RUNNER_TOKEN")

    # Refuse requests if the service token is not configured.
    if not expected_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Runner authentication is not configured.",
        )

    # Require the Authorization header to use the Bearer scheme.
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header.",
        )

    # Extract the token supplied by the client.
    provided_token = authorization.removeprefix("Bearer ")

    # Compare tokens using a timing-safe comparison.
    if not secrets.compare_digest(provided_token, expected_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid runner service token.",
        )

    # Authentication succeeded.
    return True


@app.get("/health")
def health_check():
    """Check whether the runner service is running."""

    return {
        "service": "codeview-runner",
        "status": "running",
    }


@app.get("/internal/status")
def runner_status(
    authenticated: bool = Depends(verify_runner_token),
):
    """Return runner information to an authenticated internal client."""

    return {
        "service": "codeview-runner",
        "authenticated": authenticated,
        "status": "ready",
    }