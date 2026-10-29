"""Internal FastAPI application for the CodeView sandbox controller."""

from fastapi import Depends, FastAPI

from server_runner.sandbox_controller.authentication import (
    verify_controller_token,
)

from server_runner.sandbox_controller.service import (
    SandboxControllerService,
)


# Create the internal controller application.
app = FastAPI(
    title="CodeView Sandbox Controller",

    # Disable automatic API documentation endpoints.
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)


# Initialize the controller service.
controller = SandboxControllerService()


@app.get("/health")
def health_check():
    """
    Return the controller's health status.

    This endpoint does not expose secrets or Docker operations.
    """

    return controller.health_check()


@app.get("/internal/security")
def security_summary(
    authenticated: bool = Depends(verify_controller_token),
):
    """
    Return security configuration to an authenticated service.

    The authentication dependency must succeed first.
    """

    return controller.get_security_summary()