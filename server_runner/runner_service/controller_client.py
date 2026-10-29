"""HTTP client for communicating with the CodeView Sandbox Controller."""

import os

import httpx


class SandboxControllerError(RuntimeError):
    """Raised when communication with the controller fails."""


class SandboxControllerClient:
    """Send authenticated internal requests to the sandbox controller."""

    def __init__(self):
        """Load controller connection settings."""

        # Controller URL must come from a trusted environment variable.
        self.base_url = os.environ.get(
            "CODEVIEW_CONTROLLER_URL",
            "",
        ).rstrip("/")

        # Controller authentication token.
        self.token = os.environ.get(
            "CODEVIEW_CONTROLLER_TOKEN",
            "",
        )

        # Fail if the controller URL is not configured.
        if not self.base_url:
            raise SandboxControllerError(
                "CODEVIEW_CONTROLLER_URL is not configured."
            )

        # Fail if the controller token is missing.
        if not self.token:
            raise SandboxControllerError(
                "CODEVIEW_CONTROLLER_TOKEN is not configured."
            )

    def _headers(self):
        """Build authentication headers for internal requests."""

        return {
            "Authorization": f"Bearer {self.token}",
        }

    def _get(self, path: str):
        """Send an authenticated GET request."""

        try:
            # Connect to the trusted internal controller.
            with httpx.Client(
                base_url=self.base_url,
                timeout=5.0,
                follow_redirects=False,
                trust_env=False,
            ) as client:

                # Send the request.
                response = client.get(
                    path,
                    headers=self._headers(),
                )

                # Raise an exception for HTTP errors.
                response.raise_for_status()

                # Return the JSON response.
                return response.json()

        except (httpx.HTTPError, ValueError) as error:
            raise SandboxControllerError(
                "Sandbox Controller request failed."
            ) from error

    def get_security_config(self):
        """Retrieve the controller's security configuration."""

        return self._get("/internal/security")