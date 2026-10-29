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