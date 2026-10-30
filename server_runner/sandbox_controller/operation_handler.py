"""Coordinate sandbox operations and PostgreSQL lifecycle changes."""

# ============================================================
# 1. DATABASE IMPORTS
# ============================================================

# Build database queries.
from sqlalchemy import select

# Manage PostgreSQL database sessions.
from sqlalchemy.orm import Session


# ============================================================
# 2. CODEVIEW IMPORTS
# ============================================================

# Database model representing a developer's sandbox.
from server_runner.runner_service.models import SandboxRecord

# Represent trusted sandbox ownership information.
from server_runner.sandbox_controller.authorization import (
    SandboxIdentity,
)

# Store operation request IDs in PostgreSQL for replay protection.
from server_runner.sandbox_controller.database_replay import (
    DatabaseReplayStore,
)

# Enforce valid sandbox lifecycle transitions.
from server_runner.sandbox_controller.lifecycle import (
    SandboxLifecycle,
)

# Define supported sandbox operations and request validation.
from server_runner.sandbox_controller.operation import (
    SandboxOperation,
    SandboxOperationRequest,
)

# Validate operations and claim request IDs.
from server_runner.sandbox_controller.operation_service import (
    SandboxOperationService,
)


# ============================================================
# 3. SANDBOX OPERATION HANDLER
# ============================================================

class SandboxOperationHandler:
    """Authorize, validate, and record sandbox operations atomically."""

    def __init__(self, db: Session):
        """Initialize the handler with a PostgreSQL database session."""

        # Store the database session.
        self.db = db

        # Use PostgreSQL to prevent replayed operation requests.
        self.operation_service = SandboxOperationService(
            replay_store=DatabaseReplayStore(db)
        )

        # Reuse CodeView's existing sandbox lifecycle rules.
        self.lifecycle = SandboxLifecycle()

    def handle(self, request: SandboxOperationRequest):
        """
        Validate and record an authorized sandbox operation.

        This method does not execute Docker commands.

        SECURITY:
        Developer and group IDs supplied in a request are not proof
        of authentication. The calling service must be authenticated.
        """

        # ----------------------------------------------------
        # STEP 1: VALIDATE THE REQUEST TYPE
        # ----------------------------------------------------

        if not isinstance(request, SandboxOperationRequest):
            raise ValueError(
                "Invalid sandbox operation request."
            )

        try:
            # ------------------------------------------------
            # STEP 2: FIND AND LOCK THE SANDBOX
            # ------------------------------------------------

            # Lock the matching database row until the transaction
            # finishes. This helps prevent concurrent operations
            # from changing the sandbox at the same time.
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

            # Reject missing sandboxes and ownership mismatches.
            if sandbox is None:
                raise PermissionError(
                    "Sandbox not found or access denied."
                )

            # ------------------------------------------------
            # STEP 3: BUILD TRUSTED SANDBOX IDENTITY
            # ------------------------------------------------

            # Use ownership information retrieved from PostgreSQL.
            trusted_identity = SandboxIdentity(
                sandbox_id=sandbox.sandbox_id,
                developer_id=sandbox.developer_id,
                group_id=sandbox.group_id,
            )

            # ------------------------------------------------
            # STEP 4: CHECK THE REQUESTED OPERATION
            # ------------------------------------------------

            if request.operation == SandboxOperation.START:

                # Ask the lifecycle system to validate starting.
                new_status = self.lifecycle.transition(
                    sandbox.status,
                    "starting",
                )

            elif request.operation == SandboxOperation.STOP:

                # Ask the lifecycle system to validate stopping.
                new_status = self.lifecycle.transition(
                    sandbox.status,
                    "stopped",
                )

            elif request.operation == SandboxOperation.INSPECT:

                # Inspection does not change sandbox status.
                new_status = sandbox.status

            elif request.operation == SandboxOperation.RUN:

                # Code execution uses a separate temporary
                # container rather than the main sandbox.

                allowed_statuses = {
                    "prepared",
                    "running",
                    "stopped",
                }

                # Reject sandboxes that are not ready.
                if sandbox.status not in allowed_statuses:
                    raise ValueError(
                        "Sandbox is not ready for code execution."
                    )

                # Temporary execution does not change status.
                new_status = sandbox.status

            elif request.operation == SandboxOperation.CREATE:

                # Sandbox creation is handled separately.
                # Reject attempts to recreate an active sandbox.
                if sandbox.status != "prepared":
                    raise ValueError(
                        "Sandbox is already prepared or active."
                    )

                new_status = sandbox.status

            else:
                raise ValueError(
                    "Unsupported sandbox operation."
                )

            # ------------------------------------------------
            # STEP 5: AUTHORIZE AND CLAIM THE REQUEST ID
            # ------------------------------------------------

            # Verify the operation against the trusted identity.
            #
            # The replay store records the request ID to prevent
            # the same operation from being processed again.
            self.operation_service.validate_and_claim(
                request=request,
                trusted_identity=trusted_identity,
            )

            # ------------------------------------------------
            # STEP 6: SAVE THE LIFECYCLE CHANGE
            # ------------------------------------------------

            # Update the sandbox status.
            sandbox.status = new_status

            # Commit the operation claim and lifecycle update
            # in the same PostgreSQL transaction.
            self.db.commit()

            # ------------------------------------------------
            # STEP 7: RETURN THE OPERATION RESULT
            # ------------------------------------------------

            return {
                "request_id": str(request.request_id),
                "sandbox_id": str(request.sandbox_id),
                "operation": request.operation.value,
                "status": "recorded",
                "sandbox_status": sandbox.status,
            }

        except Exception:

            # Undo all database changes if any operation fails.
            #
            # This includes unsuccessful lifecycle transitions
            # and replay-protection claims.
            self.db.rollback()

            raise