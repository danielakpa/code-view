"""Client for communicating with the CodeView Runner Service."""

# Read configuration from Django settings.
from django.conf import settings

# HTTPX allows Python applications to make HTTP requests.
import httpx


class RunnerUnavailableError(Exception):
    """Raised when the runner service cannot be reached or fails."""


class TerminalRunnerClient:
    """Handle communication between Django and the runner service."""

    def __init__(self):
        """Configure the runner service connection."""

        # Read the runner service URL from Django settings.
        self.base_url = settings.CODEVIEW_RUNNER_URL.rstrip("/")

        # Read the shared authentication token.
        self.token = settings.CODEVIEW_RUNNER_TOKEN

    async def get_status(self):
        """Check the authenticated runner service status."""

        # Include the secret token in the Authorization header.
        headers = {
            "Authorization": f"Bearer {self.token}",
        }

        try:
            # Create an asynchronous HTTP client.
            async with httpx.AsyncClient(timeout=10.0) as client:

                # Send an authenticated request to the runner.
                response = await client.get(
                    f"{self.base_url}/internal/status",
                    headers=headers,
                )

                # Raise an error if the request failed.
                response.raise_for_status()

                # Return the JSON response as a Python dictionary.
                return response.json()

        except httpx.HTTPError as error:
            # Convert network and HTTP errors into our own exception.
            raise RunnerUnavailableError(
                "CodeView Runner Service is unavailable."
            ) from error
            
    async def create_session(self, session_id, developer_id, group_id):
        """Register a developer terminal session with FastAPI."""

        # Prepare authentication headers.
        headers = {
            "Authorization": f"Bearer {self.token}"
        }

        # Prepare the terminal session information.
        payload = {
            "session_id": str(session_id),
            "developer_id": developer_id,
            "group_id": group_id,
        }

        try:
            # Create an asynchronous HTTP client.
            async with httpx.AsyncClient(timeout=10.0) as client:

                # Send the session information to FastAPI.
                response = await client.post(
                    f"{self.base_url}/internal/sessions",
                    headers=headers,
                    json=payload,
                )

                # Raise an error if FastAPI rejects the request.
                response.raise_for_status()

                # Return FastAPI's response to Django.
                return response.json()

        except httpx.HTTPError as error:
            # Handle connection failures and HTTP errors.
            raise RunnerUnavailableError(
                "Failed to register terminal session with FastAPI."
            ) from error