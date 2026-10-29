"""Manage CodeView developer sandbox preparation."""

# Import the function that saves sandbox records.
from server_runner.runner_service.sandbox.repository import save_sandbox

from dataclasses import dataclass, replace
from pathlib import Path

# Import the sandbox security configuration.
from server_runner.runner_service.sandbox.security import (
    SandboxSecurityConfig,
    get_sandbox_security_config,
)

# Import the workspace functions.
from server_runner.runner_service.sandbox.workspace import (
    create_workspace,
    validate_workspace_id,
)


@dataclass(frozen=True)
class Sandbox:
    """Represent a prepared developer sandbox."""

    # Developer who owns this sandbox.
    developer_id: int

    # Private CodeView group.
    group_id: int

    # Location of the developer's files.
    workspace_path: Path

    # Security settings intended for this sandbox.
    security: SandboxSecurityConfig

    # Current sandbox lifecycle status.
    status: str = "prepared"


class SandboxManager:
    """Prepare and describe developer sandbox environments."""

    def __init__(self):
        """Initialize the sandbox manager."""

        # Load the default security configuration.
        self.security = get_sandbox_security_config()

    def prepare_sandbox(self, developer_id, group_id):
        """Prepare a workspace and return sandbox information."""

        # Step 1: Validate the developer ID.
        developer_id = validate_workspace_id(developer_id)

        # Step 2: Validate the group ID.
        group_id = validate_workspace_id(group_id)

        # Step 3: Create the developer's workspace.
        workspace_path = create_workspace(
            developer_id=developer_id,
            group_id=group_id,
        )

        # Step 4: Create a sandbox description.
        sandbox = Sandbox(
            developer_id=developer_id,
            group_id=group_id,
            workspace_path=workspace_path,
            security=self.security,
        )

        

        # Step 5: Return the prepared sandbox.
        return sandbox

    def update_sandbox_status(self, sandbox, new_status):
        """Update a sandbox's lifecycle status."""

        # Define which status changes are allowed.
        allowed_transitions = {
            "prepared": {"starting"},
            "starting": {"running", "failed"},
            "running": {"stopped", "failed"},
            "stopped": set(),
            "failed": set(),
        }

        # Reject unknown statuses.
        if new_status not in allowed_transitions:
            raise ValueError("Invalid sandbox status.")

        # Check whether the requested change is allowed.
        if new_status not in allowed_transitions.get(
            sandbox.status, set()
        ):
            raise ValueError(
                f"Cannot change sandbox from "
                f"{sandbox.status} to {new_status}."
            )

        # Return a new Sandbox object with the updated status.
        return replace(
            sandbox,
            status=new_status,
        )

    def prepare_and_save_sandbox(self, db, developer_id, group_id):
        """Prepare a workspace and save its sandbox record."""

        # Step 1: Prepare the developer's workspace.
        sandbox = self.prepare_sandbox(
            developer_id=developer_id,
            group_id=group_id,
        )

        # Step 2: Save the sandbox information in PostgreSQL.
        sandbox_record = save_sandbox(
            db=db,
            developer_id=sandbox.developer_id,
            group_id=sandbox.group_id,
        )

        # Step 3: Return both the workspace and database record.
        return sandbox, sandbox_record