"""Save, retrieve, and manage CodeView developer sandbox records."""

import re

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from server_runner.runner_service.models import SandboxRecord

from server_runner.sandbox_controller.lifecycle import (
    SandboxLifecycle,
)


# Reuse the lifecycle rules instead of defining them again.
lifecycle = SandboxLifecycle()


def validate_identity(developer_id: int, group_id: int):
    """Validate developer and group identifiers."""

    # Reject booleans, strings, zero, and negative numbers.
    if type(developer_id) is not int or developer_id <= 0:
        raise ValueError("Invalid developer ID.")

    if type(group_id) is not int or group_id <= 0:
        raise ValueError("Invalid group ID.")


def save_sandbox(
    db: Session,
    developer_id: int,
    group_id: int,
):
    """Create a new sandbox record in PostgreSQL."""

    validate_identity(developer_id, group_id)

    sandbox = SandboxRecord(
        developer_id=developer_id,
        group_id=group_id,
        status="prepared",
    )

    try:
        db.add(sandbox)
        db.commit()
        db.refresh(sandbox)

        return sandbox

    except Exception:
        db.rollback()
        raise


def get_owned_sandbox(
    db: Session,
    sandbox_id: UUID,
    developer_id: int,
    group_id: int,
):
    """Return a sandbox only when ownership matches."""

    validate_identity(developer_id, group_id)

    sandbox = db.get(SandboxRecord, sandbox_id)

    if sandbox is None:
        raise ValueError("Sandbox not found or access denied.")

    if sandbox.developer_id != developer_id:
        raise ValueError("Sandbox not found or access denied.")

    if sandbox.group_id != group_id:
        raise ValueError("Sandbox not found or access denied.")

    return sandbox


def authorize_sandbox_operation(
    db: Session,
    sandbox_id: UUID,
    developer_id: int,
    group_id: int,
    operation: str,
):
    """Validate sandbox ownership and requested operation."""

    allowed_operations = {
        "start",
        "stop",
        "inspect",
    }

    if operation not in allowed_operations:
        raise ValueError("Invalid sandbox operation.")

    return get_owned_sandbox(
        db=db,
        sandbox_id=sandbox_id,
        developer_id=developer_id,
        group_id=group_id,
    )


def update_sandbox_status(
    db: Session,
    sandbox_id: UUID,
    new_status: str,
):
    """Validate and save a sandbox lifecycle transition."""

    try:
        # Lock the database row until the update is committed.
        statement = (
            select(SandboxRecord)
            .where(SandboxRecord.sandbox_id == sandbox_id)
            .with_for_update()
        )

        sandbox = db.execute(statement).scalar_one_or_none()

        if sandbox is None:
            raise ValueError("Sandbox not found.")

        # Validate the transition using our existing lifecycle class.
        validated_status = lifecycle.transition(
            sandbox.status,
            new_status,
        )

        # Update the database record.
        sandbox.status = validated_status

        # Save the change and release the row lock.
        db.commit()
        db.refresh(sandbox)

        return sandbox

    except Exception:
        # Undo changes if validation or saving fails.
        db.rollback()
        raise


def save_container_id(
    db: Session,
    sandbox_id: UUID,
    developer_id: int,
    group_id: int,
    container_id: str,
):
    """Associate a Docker container with an owned sandbox."""

    if (
        not isinstance(container_id, str)
        or re.fullmatch(r"[a-fA-F0-9]{64}", container_id) is None
    ):
        raise ValueError("Invalid Docker container ID.")

    validate_identity(developer_id, group_id)

    try:
        # Lock the sandbox before assigning a container.
        statement = (
            select(SandboxRecord)
            .where(
                SandboxRecord.sandbox_id == sandbox_id,
                SandboxRecord.developer_id == developer_id,
                SandboxRecord.group_id == group_id,
            )
            .with_for_update()
        )

        sandbox = db.execute(statement).scalar_one_or_none()

        if sandbox is None:
            raise ValueError("Sandbox not found or access denied.")

        if sandbox.container_id is not None:
            raise ValueError("Sandbox already has a container.")

        sandbox.container_id = container_id.lower()

        db.commit()
        db.refresh(sandbox)

        return sandbox

    except Exception:
        db.rollback()
        raise


def get_or_create_sandbox(
    db: Session,
    developer_id: int,
    group_id: int,
):
    """Retrieve an existing sandbox or create one."""

    validate_identity(developer_id, group_id)

    statement = select(SandboxRecord).where(
        SandboxRecord.developer_id == developer_id,
        SandboxRecord.group_id == group_id,
    )

    existing = db.execute(statement).scalar_one_or_none()

    if existing is not None:
        return existing

    sandbox = SandboxRecord(
        developer_id=developer_id,
        group_id=group_id,
        status="prepared",
    )

    try:
        db.add(sandbox)
        db.commit()
        db.refresh(sandbox)

        return sandbox

    except IntegrityError:
        # Another request may have created the sandbox first.
        db.rollback()

        existing = db.execute(statement).scalar_one_or_none()

        if existing is not None:
            return existing

        raise

    except Exception:
        db.rollback()
        raise


def claim_sandbox_start(
    db: Session,
    sandbox_id: UUID,
    developer_id: int,
    group_id: int,
):
    """Claim sandbox startup while preventing simultaneous claims."""

    validate_identity(developer_id, group_id)

    try:
        # Lock the sandbox row.
        statement = (
            select(SandboxRecord)
            .where(
                SandboxRecord.sandbox_id == sandbox_id,
                SandboxRecord.developer_id == developer_id,
                SandboxRecord.group_id == group_id,
            )
            .with_for_update()
        )

        sandbox = db.execute(statement).scalar_one_or_none()

        if sandbox is None:
            raise ValueError("Sandbox not found or access denied.")

        # Use the same lifecycle rules as other status updates.
        sandbox.status = lifecycle.transition(
            sandbox.status,
            "starting",
        )

        # Commit the startup claim.
        db.commit()
        db.refresh(sandbox)

        return sandbox

    except Exception:
        db.rollback()
        raise