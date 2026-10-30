"""Validate code execution requests received by the Sandbox Controller."""

# ============================================================
# 1. IMPORTS
# ============================================================

# Restrict programming languages to supported values.
from typing import Literal

# Validate incoming request data.
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)

# Import the sandbox operation request model.
from server_runner.sandbox_controller.operation import (
    SandboxOperationRequest,
)


# ============================================================
# 2. CONTROLLER EXECUTION REQUEST
# ============================================================

class ControllerExecutionRequest(BaseModel):
    """
    Describe a code execution request sent by the FastAPI Runner.

    The request contains:

    1. Sandbox operation and ownership information.
    2. The programming language.
    3. The source code to execute.
    """

    # Reject unexpected fields and incorrect data types.
    model_config = ConfigDict(
        extra="forbid",
        strict=True,
    )

    # Information used for sandbox authorization
    # and replay protection.
    operation_request: SandboxOperationRequest

    # Only allow supported programming languages.
    language: Literal[
        "python",
        "go",
        "javascript",
    ]

    # Source code must contain at least one character.
    #
    # The validator below also checks whitespace and byte size.
    source: str = Field(min_length=1)

    # ========================================================
    # 3. VALIDATE EXECUTION REQUEST
    # ========================================================

    @model_validator(mode="after")
    def validate_execution_request(self):
        """Check the requested operation and source code."""

        # STEP 1: Only the "run" operation can execute code.
        if self.operation_request.operation != "run":
            raise ValueError(
                "Code execution requires the run operation."
            )

        # STEP 2: Reject empty or whitespace-only source code.
        if not self.source.strip():
            raise ValueError(
                "Source code cannot be empty."
            )

        # STEP 3: Limit source code to 256 KiB.
        #
        # UTF-8 encoding measures the actual number of bytes.
        source_size = len(
            self.source.encode("utf-8")
        )

        if source_size > 256 * 1024:
            raise ValueError(
                "Source code exceeds the 256 KiB limit."
            )

        # STEP 4: Return the validated request.
        return self