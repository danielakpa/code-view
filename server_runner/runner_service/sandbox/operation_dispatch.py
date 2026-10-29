"""Prepare authorized sandbox operation requests for the controller."""

from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from server_runner.runner_service.sandbox.database_authorization import (
    authorize_database_sandbox_operation,
)

from server_runner.sandbox_controller.operation import (
    SandboxOperation,
    SandboxOperationRequest,
)


class SandboxOperationDispatcher:
    """Prepare sandbox operations after trusted identity checks."""

    def __init__(self, db: Session):
        """Receive the Runner's PostgreSQL session."""

        self.db = db

    def prepare_operation(
        self,
        sandbox_id: UUID,
        authenticated_developer_id: int,
        authorized_group_id: int,
        operation: SandboxOperation,
    ) -> SandboxOperationRequest:
        """
        Prepare an operation for an authenticated developer.

        The caller must obtain:
        - authenticated_developer_id from trusted authentication.
        - authorized_group_id from a verified group membership check.

        Neither value may come directly from an untrusted request body.
        """

        # Reject unsupported operation values.
        if not isinstance(operation, SandboxOperation):
            raise ValueError("Invalid sandbox operation.")

        # Verify sandbox ownership using PostgreSQL.
        sandbox_record = authorize_database_sandbox_operation(
            db=self.db,
            sandbox_id=sandbox_id,
            developer_id=authenticated_developer_id,
            group_id=authorized_group_id,
            operation=operation.value,
        )

        # Create a new request ID for replay protection.
        request_id = uuid4()

        # Use IDs from the verified database record.
        return SandboxOperationRequest(
            request_id=request_id,
            sandbox_id=sandbox_record.sandbox_id,
            developer_id=sandbox_record.developer_id,
            group_id=sandbox_record.group_id,
            operation=operation,
        )