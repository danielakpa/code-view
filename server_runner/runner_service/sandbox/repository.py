"""Save and retrieve developer sandbox records."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

# Import SQLAlchemy's database session.
from sqlalchemy.orm import Session

# Import the sandbox database model.
from server_runner.runner_service.models import SandboxRecord


def save_sandbox(db: Session, developer_id: int, group_id: int):
    """Create a sandbox record in PostgreSQL."""

    # Create a new sandbox database record.
    sandbox = SandboxRecord(
        developer_id=developer_id,
        group_id=group_id,
        status="prepared",
    )

    # Add the sandbox to the database session.
    db.add(sandbox)

    try:
        # Save the record permanently.
        db.commit()

        # Reload the record from PostgreSQL.
        db.refresh(sandbox)

    except Exception:
        # Undo the transaction if saving fails.
        db.rollback()
        raise

    # Return the saved sandbox record.
    return sandbox

def update_sandbox_status(db: Session, sandbox_id, new_status: str):
    """Update a sandbox's status in PostgreSQL."""

    # Define which status changes are allowed.
    allowed_transitions = {
        "prepared": {"starting"},
        "starting": {"running", "failed"},
        "running": {"stopped", "failed"},
        "stopped": set(),
        "failed": set(),
    }

    # Find the sandbox in PostgreSQL using its ID.
    sandbox = db.get(SandboxRecord, sandbox_id)

    # Raise an error if the sandbox doesn't exist.
    if sandbox is None:
        raise ValueError("Sandbox not found.")

    # Check whether the requested status is valid.
    if new_status not in allowed_transitions:
        raise ValueError("Invalid sandbox status.")

    # Check whether the transition is allowed.
    if new_status not in allowed_transitions[sandbox.status]:
        raise ValueError(
            f"Cannot change sandbox from {sandbox.status} to {new_status}."
        )

    # Update the sandbox's status.
    sandbox.status = new_status

    try:
        # Save the updated status in PostgreSQL.
        db.commit()

        # Reload the updated record.
        db.refresh(sandbox)

    except Exception:
        # Undo database changes if saving fails.
        db.rollback()
        raise

    # Return the updated sandbox.
    return sandbox

def get_owned_sandbox(
    db: Session,
    sandbox_id,
    developer_id: int,
    group_id: int,
):
    """Find a sandbox only when it belongs to the given developer and group."""

    # Validate the developer ID.
    if type(developer_id) is not int or developer_id <= 0:
        raise ValueError("Invalid developer ID.")

    # Validate the group ID.
    if type(group_id) is not int or group_id <= 0:
        raise ValueError("Invalid group ID.")

    # Find the sandbox using its ID.
    sandbox = db.get(SandboxRecord, sandbox_id)

    # Reject missing sandboxes.
    if sandbox is None:
        raise ValueError("Sandbox not found or access denied.")

    # Check whether the developer owns the sandbox.
    if sandbox.developer_id != developer_id:
        raise ValueError("Sandbox not found or access denied.")

    # Check whether the sandbox belongs to the requested group.
    if sandbox.group_id != group_id:
        raise ValueError("Sandbox not found or access denied.")

    # Return the sandbox only when ownership matches.
    return sandbox

def authorize_sandbox_operation(
    db: Session,
    sandbox_id,
    developer_id: int,
    group_id: int,
    operation: str,
):
    """Authorize a developer's requested sandbox operation."""

    # Define the sandbox operations we recognize.
    allowed_operations = {
        "start",
        "stop",
        "inspect",
    }

    # Reject unknown operations.
    if operation not in allowed_operations:
        raise ValueError("Invalid sandbox operation.")

    # Verify that the sandbox belongs to this developer and group.
    sandbox = get_owned_sandbox(
        db=db,
        sandbox_id=sandbox_id,
        developer_id=developer_id,
        group_id=group_id,
    )

    # Return the authorized sandbox record.
    return sandbox

def save_container_id(
    db: Session,
    sandbox_id,
    developer_id: int,
    group_id: int,
    container_id: str,
):
    """Save a Docker container ID after verifying sandbox ownership."""

    import re

    # Accept only a full Docker container ID.
    if not isinstance(container_id, str) or not re.fullmatch(
        r"[a-fA-F0-9]{64}",
        container_id,
    ):
        raise ValueError("Invalid Docker container ID.")

    # Verify that the sandbox belongs to the developer and group.
    sandbox = get_owned_sandbox(
        db=db,
        sandbox_id=sandbox_id,
        developer_id=developer_id,
        group_id=group_id,
    )

    # Prevent replacing an existing container ID.
    if sandbox.container_id is not None:
        raise ValueError("Sandbox already has a container.")

    # Associate the container with this sandbox.
    sandbox.container_id = container_id

    try:
        # Save the change in PostgreSQL.
        db.commit()

        # Reload the updated record.
        db.refresh(sandbox)

    except Exception:
        # Undo the failed database transaction.
        db.rollback()
        raise

    return sandbox

def get_or_create_sandbox(
    db: Session,
    developer_id: int,
    group_id: int,
):
    """Get an existing sandbox or create a new one."""

    # Validate the developer ID.
    if type(developer_id) is not int or developer_id <= 0:
        raise ValueError("Invalid developer ID.")

    # Validate the group ID.
    if type(group_id) is not int or group_id <= 0:
        raise ValueError("Invalid group ID.")

    # Search for the developer's sandbox in this group.
    statement = select(SandboxRecord).where(
        SandboxRecord.developer_id == developer_id,
        SandboxRecord.group_id == group_id,
    )

    # Check whether the sandbox already exists.
    existing = db.execute(statement).scalar_one_or_none()

    # Reuse the existing sandbox.
    if existing is not None:
        return existing

    # Create a new sandbox record.
    sandbox = SandboxRecord(
        developer_id=developer_id,
        group_id=group_id,
        status="prepared",
    )

    try:
        # Add the sandbox to the database.
        db.add(sandbox)

        # Save the new record.
        db.commit()

        # Reload the saved record.
        db.refresh(sandbox)

        # Return the new sandbox.
        return sandbox

    except IntegrityError:
        # Another request may have created the sandbox first.
        db.rollback()

        # Check for that existing sandbox.
        existing = db.execute(statement).scalar_one_or_none()

        if existing is not None:
            return existing

        # Raise the error if no sandbox was found.
        raise

    except Exception:
        # Undo other failed database operations.
        db.rollback()
        raise

def claim_sandbox_start(
    db: Session,
    sandbox_id,
    developer_id: int,
    group_id: int,
):
    """Claim a sandbox for startup without allowing duplicate claims."""

    # Validate the developer ID.
    if type(developer_id) is not int or developer_id <= 0:
        raise ValueError("Invalid developer ID.")

    # Validate the group ID.
    if type(group_id) is not int or group_id <= 0:
        raise ValueError("Invalid group ID.")

    try:
        # Lock this sandbox record until the transaction completes.
        statement = (
            select(SandboxRecord)
            .where(
                SandboxRecord.sandbox_id == sandbox_id,
                SandboxRecord.developer_id == developer_id,
                SandboxRecord.group_id == group_id,
            )
            .with_for_update()
        )

        # Find and lock the sandbox.
        sandbox = db.execute(statement).scalar_one_or_none()

        # Reject missing or unauthorized sandboxes.
        if sandbox is None:
            raise ValueError("Sandbox not found or access denied.")

        # Only prepared or stopped sandboxes can be claimed.
        if sandbox.status not in {"prepared", "stopped"}:
            raise ValueError(
                f"Sandbox cannot start from status: {sandbox.status}"
            )

        # Mark the sandbox as starting.
        # Other requests will see this status after the transaction commits.
        sandbox.status = "starting"

        # Save the new status and release the database lock.
        db.commit()

        # Reload the updated sandbox.
        db.refresh(sandbox)

        return sandbox

    except Exception:
        # Undo changes and release the lock if anything fails.
        db.rollback()
        raise