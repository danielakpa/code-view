"""Database-backed authorization for CodeView developer sandboxes."""

from uuid import UUID

from sqlalchemy.orm import Session

from server_runner.runner_service.models import SandboxRecord

from server_runner.sandbox_controller.authorization import (
    SandboxIdentity,
    authorize_sandbox_operation,
)


class SandboxNotFoundError(LookupError):
    """Raised when a sandbox cannot be found."""


def authorize_database_sandbox_operation(
    db: Session,
    sandbox_id: UUID,
    developer_id: int,
    group_id: int,
    operation: str,
):
    """
    Authorize a sandbox operation using its PostgreSQL record.

    IMPORTANT:
    The developer and group IDs must already be verified by
    the authenticated Runner request and Django membership checks.
    """

    # Validate the sandbox ID before querying PostgreSQL.
    if not isinstance(sandbox_id, UUID):
        raise ValueError("Invalid sandbox ID.")

    # Reject invalid developer IDs.
    if type(developer_id) is not int or developer_id <= 0:
        raise ValueError("Invalid developer ID.")

    # Reject invalid group IDs.
    if type(group_id) is not int or group_id <= 0:
        raise ValueError("Invalid group ID.")

    # Retrieve the sandbox from PostgreSQL.
    sandbox_record = db.get(
        SandboxRecord,
        sandbox_id,
    )

    # Reject unknown sandbox IDs.
    if sandbox_record is None:
        raise SandboxNotFoundError(
            "Sandbox was not found."
        )

    # Build an identity from trusted database information.
    trusted_identity = SandboxIdentity(
        sandbox_id=sandbox_record.sandbox_id,
        developer_id=sandbox_record.developer_id,
        group_id=sandbox_record.group_id,
    )

    # Apply the existing authorization policy.
    authorize_sandbox_operation(
        sandbox=trusted_identity,
        developer_id=developer_id,
        group_id=group_id,
        operation=operation,
    )

    # Return the database record after authorization succeeds.
    return sandbox_record