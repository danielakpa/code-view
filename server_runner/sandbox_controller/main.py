"""Internal FastAPI application for the CodeView sandbox controller."""

# ============================================================
# 1. IMPORTS
# ============================================================

# FastAPI components.
from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Request,
)

# Pydantic validation errors.
from pydantic import ValidationError

# SQLAlchemy database errors and sessions.
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

# Controller authentication.
from server_runner.sandbox_controller.authentication import (
    verify_controller_token,
)

# Existing controller service.
from server_runner.sandbox_controller.service import (
    SandboxControllerService,
)

# Database session dependency.
from server_runner.runner_service.database import (
    get_db,
)

# Validate incoming code execution requests.
from server_runner.sandbox_controller.execution_request import (
    ControllerExecutionRequest,
)

# Authorize sandbox operations and prevent replay attacks.
from server_runner.sandbox_controller.operation_handler import (
    SandboxOperationHandler,
)

# Execute code using the existing Docker execution system.
from server_runner.sandbox_controller.code_execution_pipeline import (
    CodeExecutionPipeline,
)


# ============================================================
# 2. CREATE FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="CodeView Sandbox Controller",

    # Disable automatic API documentation endpoints.
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)


# ============================================================
# 3. INITIALIZE CONTROLLER SERVICE
# ============================================================

controller = SandboxControllerService()


# ============================================================
# 4. HEALTH CHECK ENDPOINT
# ============================================================

@app.get("/health")
def health_check():
    """
    Return the controller's health status.

    This endpoint does not expose secrets or Docker operations.
    """

    return controller.health_check()


# ============================================================
# 5. SECURITY SUMMARY ENDPOINT
# ============================================================

@app.get("/internal/security")
def security_summary(
    authenticated: bool = Depends(verify_controller_token),
):
    """
    Return security configuration to an authenticated service.

    The authentication dependency must succeed first.
    """

    return controller.get_security_summary()


# ============================================================
# 6. CODE EXECUTION ENDPOINT
# ============================================================

@app.post("/internal/executions")
async def execute_code(
    http_request: Request,

    # Verify the internal Controller token before processing.
    authenticated: bool = Depends(verify_controller_token),

    # Provide a database session for authorization.
    db: Session = Depends(get_db),
):
    """
    Authorize and execute source code in a temporary Docker container.

    Execution flow:

    1. Authenticate the calling service.
    2. Validate the JSON request.
    3. Verify sandbox ownership and lifecycle status.
    4. Prevent replayed operation requests.
    5. Execute code using the Docker pipeline.
    6. Return the execution result.
    """

    # --------------------------------------------------------
    # STEP 1: VALIDATE THE REQUEST BODY
    # --------------------------------------------------------

    try:
        # Read the incoming JSON request.
        request_body = await http_request.body()

        # Validate JSON using Pydantic.
        #
        # JSON validation correctly handles UUID strings
        # even when strict validation is enabled.
        execution_request = (
            ControllerExecutionRequest.model_validate_json(
                request_body
            )
        )

    except ValidationError as error:

        # Return a validation error without exposing
        # unnecessary internal application details.
        raise HTTPException(
            status_code=422,
            detail="Invalid code execution request.",
        ) from error

    # --------------------------------------------------------
    # STEP 2: AUTHORIZE THE SANDBOX OPERATION
    # --------------------------------------------------------

    try:
        # Create the operation handler.
        operation_handler = SandboxOperationHandler(db)

        # Verify ownership, lifecycle rules, and replay protection.
        #
        # This records the authorized operation in PostgreSQL.
        operation_handler.handle(
            execution_request.operation_request
        )

    except PermissionError as error:

        # Reject requests that cannot access the sandbox.
        raise HTTPException(
            status_code=403,
            detail=str(error),
        ) from error

    except ValueError as error:

        # Reject invalid sandbox lifecycle operations.
        raise HTTPException(
            status_code=409,
            detail=str(error),
        ) from error

    except SQLAlchemyError as error:

        # Database failures prevent authorization.
        raise HTTPException(
            status_code=503,
            detail="Sandbox authorization database unavailable.",
        ) from error

    # --------------------------------------------------------
    # STEP 3: EXECUTE THE SOURCE CODE
    # --------------------------------------------------------

    try:
        # Initialize the existing Docker execution pipeline.
        pipeline = CodeExecutionPipeline()

        # Run code in a temporary Docker container.
        result = pipeline.execute(
            sandbox_id=execution_request.operation_request.sandbox_id,
            language=execution_request.language,
            source=execution_request.source,
        )

        # Return the execution result.
        return result

    except ValueError as error:

        # Reject invalid execution parameters.
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    except RuntimeError as error:

        # Report Docker execution infrastructure failures.
        raise HTTPException(
            status_code=503,
            detail="Code execution service unavailable.",
        ) from error