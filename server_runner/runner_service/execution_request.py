"""Validate Code Board execution requests received by FastAPI."""

from pydantic import BaseModel, ConfigDict, Field


class CodeExecutionRequest(BaseModel):
    """Describe a request to execute a developer's Code Board."""

    # Reject unexpected fields and incorrect data types.
    model_config = ConfigDict(
        extra="forbid",
        strict=True,
    )

    # The Code Board Django has authorized.
    board_id: int = Field(gt=0)

    # The authenticated developer's database ID.
    developer_id: int = Field(gt=0)

    # The authorized private group's database ID.
    group_id: int = Field(gt=0)