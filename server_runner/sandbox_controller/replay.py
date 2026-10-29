"""Prevent repeated CodeView sandbox operation requests."""

from threading import Lock
from uuid import UUID


class ReplayProtectionError(PermissionError):
    """Raised when a request ID has already been used."""


class InMemoryReplayStore:
    """
    Store previously accepted request IDs.

    DEVELOPMENT ONLY:
    This store does not survive application restarts.
    """

    def __init__(self):
        """Initialize the replay store."""

        # Store accepted request IDs.
        self._request_ids = set()

        # Prevent two threads from claiming the same ID simultaneously.
        self._lock = Lock()

    def claim_request(self, request_id: UUID):
        """Accept a request ID once and reject duplicates."""

        # Check that the ID is a valid, nonempty UUID.
        if not isinstance(request_id, UUID) or request_id.int == 0:
            raise ValueError("Invalid request ID.")

        # Lock while checking and saving the ID.
        with self._lock:

            # Reject an ID that has already been used.
            if request_id in self._request_ids:
                raise ReplayProtectionError(
                    "Sandbox operation request has already been used."
                )

            # Save the new request ID.
            self._request_ids.add(request_id)

        return True