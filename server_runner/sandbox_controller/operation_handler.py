"""Coordinate sandbox operations and PostgreSQL lifecycle changes."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from server_runner.runner_service.models import SandboxRecord

from server_runner.sandbox_controller.authorization import (
    SandboxIdentity,
)

from server_runner.sandbox_controller.database_replay import (
    DatabaseReplayStore,
)

from server_runner.sandbox_controller.lifecycle import (
    SandboxLifecycle,
)

from server_runner.sandbox_controller.operation import (
    SandboxOperation,
    SandboxOperationRequest,
)

from server_runner.sandbox_controller.operation_service import (
    SandboxOperationService,
)


class SandboxOperationHandler:
    """Validate and record sandbox operations atomically."""

    def __init__(self, db: Session):
        """Initialize the operation handler."""

        self.db = db

        # Use PostgreSQL for replay protection.
        self.operation_service = SandboxOperationService(
            replay_store=DatabaseReplayStore(db)
        )

        # Reuse our existing lifecycle rules.
        self.lifecycle = SandboxLifecycle()

    def handle(self, request: SandboxOperationRequest):
        """
        Validate and record a sandbox operation.

        This method does not execute Docker commands.

        SECURITY:
        Do not expose this method to untrusted callers.
        Request developer/group IDs are not authentication.
        """

        # Validate the request type.
        if not isinstance(request, SandboxOperationRequest):
            raise ValueError("Invalid sandbox operation request.")

        try:
            # Lock the sandbox record while processing the operation.
            statement = (
                select(SandboxRecord)
                .where(
                    SandboxRecord.sandbox_id == request.sandbox_id,
                    SandboxRecord.developer_id == request.developer_id,
                    SandboxRecord.group_id == request.group_id,
                )
                .with_for_update()
            )

            sandbox = self.db.execute(
                statement
            ).scalar_one_or_none()

            # Reject missing or mismatched sandbox records.
            if sandbox is None:
                raise PermissionError(
                    "Sandbox not found or access denied."
                )

            # Build the identity using database information.
            trusted_identity = SandboxIdentity(
                sandbox_id=sandbox.sandbox_id,
                developer_id=sandbox.developer_id,
                group_id=sandbox.group_id,
            )

            # Decide which lifecycle transition is needed.
            if request.operation == SandboxOperation.START:

                new_status = self.lifecycle.transition(
                    sandbox.status,
                    "starting",
                )

            elif request.operation == SandboxOperation.STOP:

                new_status = self.lifecycle.transition(
                    sandbox.status,
                    "stopped",
                )
            elif request.operation == SandboxOperation.INSPECT:

                # Inspect does not change the sandbox's status.
                new_status = sandbox.status

            elif request.operation == SandboxOperation.RUN:

                # The Run button uses a separate temporary container.
                # It does not require the main sandbox to be running.

                # Define which sandbox states permit temporary execution.
                allowed_statuses = {
                    "prepared",
                    "running",
                    "stopped",
                }

                # Reject sandboxes that are not ready for execution.
                if sandbox.status not in allowed_statuses:
                    raise ValueError(
                        "Sandbox is not ready for code execution."
                    )

                # Temporary execution does not change the sandbox status.
                new_status = sandbox.status

            elif request.operation == SandboxOperation.CREATE:

                # Creating a sandbox is handled separately.
                # Do not create duplicate sandbox records here.
                if sandbox.status != "prepared":
                    raise ValueError(
                        "Sandbox is already prepared or active."
                    )

                new_status = sandbox.status

            elif request.operation == SandboxOperation.CREATE:

                # Creating a sandbox is handled separately.
                # Do not create duplicate sandbox records here.
                if sandbox.status != "prepared":
                    raise ValueError(
                        "Sandbox is already prepared or active."
                    )

                new_status = sandbox.status

            else:
                raise ValueError("Unsupported sandbox operation.")

            # Verify the operation and record its request ID.
            self.operation_service.validate_and_claim(
                request=request,
                trusted_identity=trusted_identity,
            )

            # Save the lifecycle change in the same transaction.
            sandbox.status = new_status

            # Commit the operation request and lifecycle update together.
            self.db.commit()

            return {
                "request_id": str(request.request_id),
                "sandbox_id": str(request.sandbox_id),
                "operation": request.operation.value,
                "status": "recorded",
                "sandbox_status": sandbox.status,
            }

        except Exception:
            # Undo both changes if anything fails.
            self.db.rollback()
            raise