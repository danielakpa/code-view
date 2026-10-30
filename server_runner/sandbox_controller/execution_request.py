"""Validate code execution requests received by the Controller."""

from pydantic import BaseModel, ConfigDict, model_validator

from server_runner.sandbox_controller.code_snapshot import (
    prepare_code_snapshot,
)

from server_runner.sandbox_controller.operation import (
    SandboxOperation,
    SandboxOperationRequest,
)


class ControllerExecutionRequest(BaseModel):
    """Represent a code execution request from the trusted Runner."""

    # Reject unexpected request fields.
    model_config = ConfigDict(extra="forbid")

    # Identify the sandbox, developer, group, and operation.
    operation_request: SandboxOperationRequest

    # Programming language selected in the Code Board.
    language: str

    # Source code submitted for execution.
    source: str

    @model_validator(mode="after")
    def validate_execution(self):
        """Verify the operation and source code."""

        # This endpoint only accepts RUN operations.
        if self.operation_request.operation != SandboxOperation.RUN:
            raise ValueError(
                "Only RUN operations are allowed."
            )

        # Reuse the existing source-code validation.
        prepare_code_snapshot(
            language=self.language,
            source=self.source,
        )

        return self