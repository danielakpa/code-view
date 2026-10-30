"""Validate Code Board execution requests received by FastAPI."""

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)


class CodeExecutionRequest(BaseModel):
    """Describe a developer's Code Board execution request."""

    # Reject unexpected fields and incorrect data types.
    model_config = ConfigDict(
        extra="forbid",
        strict=True,
    )

    # Identify the authorized Code Board.
    board_id: int = Field(gt=0)

    # Identify the developer requesting execution.
    developer_id: int = Field(gt=0)

    # Identify the developer's private group.
    group_id: int = Field(gt=0)

    # Programming language used by the Code Board.
    language: str

    # Source code retrieved from the authorized Code Board.
    source: str

    @model_validator(mode="after")
    def validate_execution_code(self):
        """Validate the language and source code."""

        # STEP 1: Define supported programming languages.
        supported_languages = {
            "python",
            "go",
            "javascript",
        }

        # STEP 2: Reject unsupported languages.
        if self.language not in supported_languages:
            raise ValueError(
                "Code execution supports Python, Go, and JavaScript."
            )

        # STEP 3: Reject empty source code.
        if not self.source.strip():
            raise ValueError(
                "Source code cannot be empty."
            )

        # STEP 4: Reject source code larger than 256 KiB.
        if len(self.source.encode("utf-8")) > 256 * 1024:
            raise ValueError(
                "Source code exceeds the 256 KiB limit."
            )

        # STEP 5: Return the validated request.
        return self