"""Manage private workspace directories for CodeView developers."""

import os
from pathlib import Path


# Root directory for developer workspaces.
WORKSPACE_ROOT = Path(
    os.environ.get(
        "CODEVIEW_WORKSPACE_ROOT",
        "/var/lib/codeview/workspaces",
    )
)


def validate_workspace_id(value):
    """Validate a developer or group ID."""

    # IDs must be positive integers, not booleans.
    if type(value) is not int or value <= 0:
        raise ValueError(
            "Workspace IDs must be positive integers."
        )

    return value


def get_workspace_path(developer_id, group_id):
    """Build the workspace path for a developer and group."""

    # Validate the developer ID.
    developer_id = validate_workspace_id(developer_id)

    # Validate the group ID.
    group_id = validate_workspace_id(group_id)

    # Build the developer's private workspace path.
    return (
        WORKSPACE_ROOT
        / f"developer_{developer_id}"
        / f"group_{group_id}"
    )


def create_workspace(developer_id, group_id):
    """Create a workspace directory if it does not exist."""

    # Get the validated workspace path.
    workspace_path = get_workspace_path(
        developer_id,
        group_id,
    )

    # Create directories when they do not already exist.
    workspace_path.mkdir(
        parents=True,
        exist_ok=True,
        mode=0o700,
    )

    # Restrict access to the directory owner.
    workspace_path.chmod(0o700)

    # Return the workspace location.
    return workspace_path