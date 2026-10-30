"""Define and validate CodeView sandbox operation requests."""

from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SandboxOperation(str, Enum):
    """List operations supported by the controller."""

    CREATE = "create"
    START = "start"
    STOP = "stop"
    INSPECT = "inspect"

    # Request to execute code in a temporary container.
    RUN = "run"


class SandboxOperationRequest(BaseModel):
    """
    Represent a sandbox operation request.

    This model validates the request's structure.
    It does not independently prove developer authorization.
    """

    # Reject unexpected fields.
    model_config = ConfigDict(extra="forbid", strict=True)

    # Unique identifier for this request.
    request_id: UUID

    # Unique identifier for the sandbox.
    sandbox_id: UUID

    # Developer associated with the sandbox.
    developer_id: int = Field(gt=0)

    # Group associated with the sandbox.
    group_id: int = Field(gt=0)

    # Requested sandbox operation.
    operation: SandboxOperation

    @model_validator(mode="after")
    def validate_request(self):
        """Perform additional validation of the request."""

        # Reject nil UUIDs.
        if self.request_id.int == 0:
            raise ValueError("Request ID cannot be empty.")

        if self.sandbox_id.int == 0:
            raise ValueError("Sandbox ID cannot be empty.")

        return self