"""Handle authorized sandbox operation requests."""

from sqlalchemy.orm import Session

from server_runner.runner_service.sandbox.database_authorization import (
    authorize_database_sandbox_operation,
)

from server_runner.sandbox_controller.authorization import (
    SandboxIdentity,
)

from server_runner.sandbox_controller.database_replay import (
    DatabaseReplayStore,
)

from server_runner.sandbox_controller.operation import (
    SandboxOperationRequest,
)

from server_runner.sandbox_controller.operation_service import (
    SandboxOperationService,
)


class SandboxOperationHandler:
    """Validate and record sandbox operation requests."""

    def __init__(self, db: Session):
        """Receive the PostgreSQL database session."""

        self.db = db

        # Use PostgreSQL instead of the in-memory replay store.
        replay_store = DatabaseReplayStore(db)

        # Connect replay protection to operation validation.
        self.operation_service = SandboxOperationService(
            replay_store=replay_store
        )

    def handle(self, request: SandboxOperationRequest):
        """
        Validate and record a sandbox operation request.

        No Docker operation is performed here.
        """

        # Step 1: Find the sandbox in PostgreSQL.
        # Check whether its stored ownership matches the request.
        sandbox_record = authorize_database_sandbox_operation(
            db=self.db,
            sandbox_id=request.sandbox_id,
            developer_id=request.developer_id,
            group_id=request.group_id,
            operation=request.operation.value,
        )

        # Step 2: Build the trusted identity from database data.
        trusted_identity = SandboxIdentity(
            sandbox_id=sandbox_record.sandbox_id,
            developer_id=sandbox_record.developer_id,
            group_id=sandbox_record.group_id,
        )

        # Step 3: Validate the operation and claim its request ID.
        self.operation_service.validate_and_claim(
            request=request,
            trusted_identity=trusted_identity,
        )

        # Step 4: Return an acknowledgment.
        # This does NOT mean Docker has started.
        return {
            "request_id": str(request.request_id),
            "sandbox_id": str(request.sandbox_id),
            "operation": request.operation.value,
            "status": "recorded",
        }