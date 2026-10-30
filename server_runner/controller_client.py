"""HTTP client for communicating with the CodeView Sandbox Controller."""

# ============================================================
# 1. PYTHON BUILT-IN MODULES
# ============================================================

# Read Controller configuration from environment variables.
import os

# Work with unique execution and sandbox identifiers.
from uuid import UUID


# ============================================================
# 2. THIRD-PARTY LIBRARIES
# ============================================================

# Send HTTP requests to the Sandbox Controller.
import httpx


# ============================================================
# 3. SANDBOX CONTROLLER CLIENT
# ============================================================

class ControllerClient:
    """
    Send authenticated execution requests to the Sandbox Controller.

    Communication flow:

    Django
       |
       v
    FastAPI Runner
       |
       v
    ControllerClient
       |
       v
    Sandbox Controller
       |
       v
    Docker
    """

    def __init__(self):
        """Load the Sandbox Controller's connection settings."""

        # Read the Controller's internal URL.
        self.base_url = os.environ.get(
            "CODEVIEW_CONTROLLER_URL",
            "http://127.0.0.1:8002",
        ).rstrip("/")

        # Read the authentication token.
        self.token = os.environ.get("CODEVIEW_CONTROLLER_TOKEN")

    def execute_code(
        self,
        request_id: UUID,
        sandbox_id: UUID,
        developer_id: int,
        group_id: int,
        language: str,
        source: str,
    ) -> dict:
        """Request code execution inside an authorized sandbox."""

        # ----------------------------------------------------
        # STEP 1: VERIFY CONTROLLER CONFIGURATION
        # ----------------------------------------------------

        # Never send an unauthenticated execution request.
        if not self.token:
            raise RuntimeError(
                "Sandbox Controller authentication is not configured."
            )

        # ----------------------------------------------------
        # STEP 2: BUILD THE EXECUTION REQUEST
        # ----------------------------------------------------

        # The Controller expects sandbox operation information
        # together with the programming language and source code.
        payload = {
            "operation_request": {
                # Unique ID used for replay protection.
                "request_id": str(request_id),

                # Sandbox selected by the Runner.
                "sandbox_id": str(sandbox_id),

                # Developer who owns the sandbox.
                "developer_id": developer_id,

                # Private group containing the sandbox.
                "group_id": group_id,

                # Request permission to run code.
                "operation": "run",
            },

            # Supported programming language.
            "language": language,

            # Code retrieved from Django's authorized Code Board.
            "source": source,
        }

        # ----------------------------------------------------
        # STEP 3: BUILD AUTHENTICATION HEADERS
        # ----------------------------------------------------

        headers = {
            "Authorization": f"Bearer {self.token}",
        }

        # ----------------------------------------------------
        # STEP 4: SEND THE REQUEST
        # ----------------------------------------------------

        # Use a timeout so the Runner cannot wait indefinitely.
        with httpx.Client(timeout=45.0) as client:

            response = client.post(
                f"{self.base_url}/internal/executions",
                headers=headers,
                json=payload,
            )

            # Raise an error for unsuccessful HTTP responses.
            response.raise_for_status()

            # Return the Controller's JSON response.
            return response.json()