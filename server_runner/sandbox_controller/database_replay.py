"""Persistent replay protection using PostgreSQL."""

from uuid import UUID

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from server_runner.sandbox_controller.operation import (
    SandboxOperationRequest,
)

from server_runner.sandbox_controller.replay import (
    ReplayProtectionError,
)


class DatabaseReplayStore:
    """Claim sandbox operation requests using PostgreSQL."""

    def __init__(self, db: Session):
        """Receive an existing SQLAlchemy database session."""

        self.db = db

    def claim_request(self, request: SandboxOperationRequest):
        """
        Save a request ID exactly once.

        PostgreSQL's primary key prevents duplicate claims,
        including simultaneous requests from different processes.
        """

        # Validate the incoming request model.
        if not isinstance(request, SandboxOperationRequest):
            raise ValueError("Invalid sandbox operation request.")

        # Validate the request UUID.
        if not isinstance(request.request_id, UUID):
            raise ValueError("Invalid request ID.")

        try:
            # Insert the request into PostgreSQL.
            self.db.execute(
                text(
                    """
                    INSERT INTO runner.sandbox_operation_requests (
                        request_id,
                        sandbox_id,
                        developer_id,
                        group_id,
                        operation
                    )
                    VALUES (
                        :request_id,
                        :sandbox_id,
                        :developer_id,
                        :group_id,
                        :operation
                    )
                    """
                ),
                {
                    "request_id": request.request_id,
                    "sandbox_id": request.sandbox_id,
                    "developer_id": request.developer_id,
                    "group_id": request.group_id,
                    "operation": request.operation.value,
                },
            )

            # Commit the claim.
            self.db.commit()

        except IntegrityError as error:

            # PostgreSQL requires a rollback after a failed insert.
            self.db.rollback()

            # A primary-key collision means the request was used already.
            # Other integrity errors should not be mislabeled as replay.
            sqlstate = getattr(
                getattr(error.orig, "diag", None),
                "sqlstate",
                None,
            ) or getattr(error.orig, "sqlstate", None)

            constraint_name = getattr(
                getattr(error.orig, "diag", None),
                "constraint_name",
                None,
            )

            if (
                sqlstate == "23505"
                and constraint_name == "sandbox_operation_requests_pkey"
            ):
                raise ReplayProtectionError(
                    "Sandbox operation request has already been used."
                ) from error

            raise

        except Exception:

            # Roll back any other database failure.
            self.db.rollback()

            raise

        return True