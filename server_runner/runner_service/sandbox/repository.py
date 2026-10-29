"""Save and retrieve developer sandbox records."""

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