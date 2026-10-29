"""Validate and claim CodeView sandbox operation requests."""

from server_runner.sandbox_controller.authorization import (
    SandboxIdentity,
    authorize_sandbox_operation,
)

from server_runner.sandbox_controller.operation import (
    SandboxOperationRequest,
)

from server_runner.sandbox_controller.replay import (
    InMemoryReplayStore,
)


class SandboxOperationService:
    """Coordinate sandbox authorization and replay protection."""

    def __init__(self, replay_store=None):
        """Initialize the operation service."""

        # Use the provided replay store.
        # Default is for development and tests only.
        self.replay_store = (
            replay_store
            if replay_store is not None
            else InMemoryReplayStore()
        )

    def validate_and_claim(
        self,
        request: SandboxOperationRequest,
        trusted_identity: SandboxIdentity,
    ):
        """
        Validate an operation and claim its request ID.

        trusted_identity must come from verified server-side records.
        """

        # Require the correct request type.
        if not isinstance(request, SandboxOperationRequest):
            raise ValueError("Invalid operation request.")

        # Ensure the operation targets the correct sandbox.
        if request.sandbox_id != trusted_identity.sandbox_id:
            raise PermissionError(
                "Operation targets a different sandbox."
            )

        # Verify developer, group, and operation permissions.
        authorize_sandbox_operation(
            sandbox=trusted_identity,
            developer_id=request.developer_id,
            group_id=request.group_id,
            operation=request.operation.value,
        )

        # Save the complete request using the configured replay store.
        self.replay_store.claim_request(request)

        return request