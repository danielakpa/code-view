"""Prevent repeated CodeView sandbox operation requests."""

from threading import Lock

from server_runner.sandbox_controller.operation import (
    SandboxOperationRequest,
)


class ReplayProtectionError(PermissionError):
    """Raised when a request has already been used."""


class InMemoryReplayStore:
    """
    Store accepted request IDs.

    Development and testing only.
    """

    def __init__(self):
        """Create the replay store."""

        # Keep track of accepted request IDs.
        self._request_ids = set()

        # Prevent simultaneous threads from claiming the same ID.
        self._lock = Lock()

    def claim_request(self, request: SandboxOperationRequest):
        """Accept an operation request only once."""

        # Require a validated operation request.
        if not isinstance(request, SandboxOperationRequest):
            raise ValueError("Invalid sandbox operation request.")

        request_id = request.request_id

        # Protect the check and update from concurrent threads.
        with self._lock:

            # Reject duplicate request IDs.
            if request_id in self._request_ids:
                raise ReplayProtectionError(
                    "Sandbox operation request has already been used."
                )

            # Remember the accepted request ID.
            self._request_ids.add(request_id)

        return True