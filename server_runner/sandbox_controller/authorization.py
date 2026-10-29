"""Authorization rules for CodeView sandbox operations."""

from dataclasses import dataclass
from uuid import UUID


# Operations supported by the authorization policy.
ALLOWED_SANDBOX_OPERATIONS = frozenset({
    "create",
    "start",
    "stop",
    "inspect",
})


@dataclass(frozen=True)
class SandboxIdentity:
    """
    Represent a sandbox's trusted identity.

    These values must come from verified server-side records,
    not directly from untrusted developer input.
    """

    sandbox_id: UUID
    developer_id: int
    group_id: int


class SandboxAuthorizationError(PermissionError):
    """Raised when a sandbox operation is not authorized."""


def validate_sandbox_identity(identity: SandboxIdentity):
    """Validate the structure of a sandbox identity."""

    # Ensure the identity uses our expected data structure.
    if not isinstance(identity, SandboxIdentity):
        raise ValueError("Invalid sandbox identity.")

    # Ensure the sandbox ID is a UUID.
    if not isinstance(identity.sandbox_id, UUID):
        raise ValueError("Invalid sandbox ID.")

    # Ensure the developer ID is a positive integer.
    if type(identity.developer_id) is not int or identity.developer_id <= 0:
        raise ValueError("Invalid developer ID.")

    # Ensure the group ID is a positive integer.
    if type(identity.group_id) is not int or identity.group_id <= 0:
        raise ValueError("Invalid group ID.")

    return identity


def authorize_sandbox_operation(
    sandbox: SandboxIdentity,
    developer_id: int,
    group_id: int,
    operation: str,
):
    """
    Verify that an operation targets the expected developer and group.

    IMPORTANT:
    This function compares identities only.

    Its caller must first load the sandbox identity from a trusted
    database record and independently verify developer permissions.
    """

    # Validate the trusted sandbox identity.
    validate_sandbox_identity(sandbox)

    # Reject invalid developer IDs.
    if type(developer_id) is not int or developer_id <= 0:
        raise ValueError("Invalid developer ID.")

    # Reject invalid group IDs.
    if type(group_id) is not int or group_id <= 0:
        raise ValueError("Invalid group ID.")

    # Reject unsupported operations.
    if operation not in ALLOWED_SANDBOX_OPERATIONS:
        raise ValueError("Unsupported sandbox operation.")

    # Ensure the developer owns this sandbox.
    if sandbox.developer_id != developer_id:
        raise SandboxAuthorizationError(
            "Developer does not own this sandbox."
        )

    # Ensure the sandbox belongs to the expected group.
    if sandbox.group_id != group_id:
        raise SandboxAuthorizationError(
            "Sandbox does not belong to this group."
        )

    return True