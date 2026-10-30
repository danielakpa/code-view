"""Authorize CodeView execution against persistent sandbox records."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from server_runner.runner_service.models import SandboxRecord

from server_runner.runner_service.sandbox.repository import (
    validate_identity,
)

from server_runner.runner_service.sandbox.database_authorization import (
    authorize_database_sandbox_operation,
)


class ExecutionSandboxNotFoundError(LookupError):
    """Raised when an execution sandbox does not exist."""


def authorize_execution_sandbox(
    db: Session,
    developer_id: int,
    group_id: int,
):
    """
    Find and authorize a developer's existing sandbox for execution.

    IMPORTANT:
    Developer and group IDs must come from an authenticated,
    independently authorized Django request.
    """

    # Step 1: Reject invalid developer and group IDs.
    validate_identity(
        developer_id=developer_id,
        group_id=group_id,
    )

    # Step 2: Find the sandbox belonging to this developer and group.
    statement = select(SandboxRecord).where(
        SandboxRecord.developer_id == developer_id,
        SandboxRecord.group_id == group_id,
    )

    sandbox = db.execute(statement).scalar_one_or_none()

    # Step 3: Reject requests without an existing sandbox.
    if sandbox is None:
        raise ExecutionSandboxNotFoundError(
            "Execution sandbox was not found."
        )

    # Step 4: Reuse our existing database authorization.
    authorized_sandbox = authorize_database_sandbox_operation(
        db=db,
        sandbox_id=sandbox.sandbox_id,
        developer_id=developer_id,
        group_id=group_id,
        operation="run",
    )

    # Step 5: Only allow sandboxes in suitable states.
    allowed_statuses = {
        "prepared",
        "running",
        "stopped",
    }

    if authorized_sandbox.status not in allowed_statuses:
        raise ValueError(
            "Sandbox is not ready for code execution."
        )

    # Step 6: Return the authorized sandbox.
    return authorized_sandbox