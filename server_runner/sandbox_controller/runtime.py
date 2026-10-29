"""Docker runtime for CodeView developer sandboxes.

This module prepares Docker commands.

IMPORTANT:
Docker commands are NOT executed in this step.
"""

import re
from pathlib import Path
from uuid import UUID

from server_runner.sandbox_controller.security import (
    get_controller_security_config,
)


# Use a fixed developer image rather than accepting arbitrary images.
DEVELOPER_IMAGE = "ghcr.io/danielakpa/codeview-developer:dev"

# Docker container IDs contain 64 hexadecimal characters.
CONTAINER_ID_PATTERN = re.compile(r"^[a-f0-9]{64}$")


class SandboxRuntimeError(RuntimeError):
    """Raised when sandbox runtime configuration is invalid."""


class DockerRuntime:
    """Build restricted Docker commands for developer sandboxes."""

    def __init__(self):
        """Load the controller's security configuration."""

        self.security = get_controller_security_config()

    def build_create_command(
        self,
        sandbox_id: UUID,
        workspace_path: Path,
    ) -> list[str]:
        """Build a Docker command to create a sandbox container."""

        # Validate the sandbox identifier.
        if not isinstance(sandbox_id, UUID) or sandbox_id.int == 0:
            raise SandboxRuntimeError("Invalid sandbox ID.")

        # Require a Path object.
        if not isinstance(workspace_path, Path):
            raise SandboxRuntimeError("Invalid workspace path.")

        # Require an existing absolute directory.
        if not workspace_path.is_absolute():
            raise SandboxRuntimeError(
                "Workspace path must be absolute."
            )

        if not workspace_path.is_dir():
            raise SandboxRuntimeError(
                "Workspace directory does not exist."
            )

        # Create a predictable Docker container name.
        container_name = f"codeview-{sandbox_id.hex}"

        # Build the Docker command as a list.
        command = [
            "docker",
            "create",

            # Name the container.
            "--name",
            container_name,

            # Limit memory.
            "--memory",
            f"{self.security.memory_limit_mb}m",

            # Limit CPU usage.
            "--cpus",
            str(self.security.cpu_limit),

            # Limit the number of processes.
            "--pids-limit",
            str(self.security.process_limit),

            # Disable network access.
            "--network",
            "none",

            # Prevent privilege escalation.
            "--security-opt",
            "no-new-privileges",

            # Drop Linux capabilities.
            "--cap-drop",
            "ALL",

            # Use a read-only container filesystem.
            "--read-only",

            # Run the container as an unprivileged user.
            "--user",
            "10001:10001",

            # Provide a temporary writable /tmp directory.
            "--tmpfs",
            "/tmp:rw,nosuid,nodev,size=64m",

            # Mount the developer's private workspace.
            "--mount",
            (
                "type=bind,"
                f"source={workspace_path},"
                "target=/workspace"
            ),

            # Set the container's working directory.
            "--workdir",
            "/workspace",

            # Use the approved developer image.
            DEVELOPER_IMAGE,

            # Keep the sandbox container running.
            "sleep",
            "infinity",
        ]

        return command

    def build_start_command(self, container_id: str) -> list[str]:
        """Build the command to start an existing container."""

        self._validate_container_id(container_id)

        return [
            "docker",
            "start",
            container_id,
        ]

    def build_stop_command(self, container_id: str) -> list[str]:
        """Build the command to stop an existing container."""

        self._validate_container_id(container_id)

        return [
            "docker",
            "stop",
            "--time",
            "10",
            container_id,
        ]

    def build_inspect_command(self, container_id: str) -> list[str]:
        """Build the command to inspect container status."""

        self._validate_container_id(container_id)

        return [
            "docker",
            "inspect",
            "--format",
            "{{.State.Status}}",
            container_id,
        ]

    def _validate_container_id(self, container_id: str):
        """Reject invalid Docker container identifiers."""

        if (
            not isinstance(container_id, str)
            or CONTAINER_ID_PATTERN.fullmatch(container_id) is None
        ):
            raise SandboxRuntimeError(
                "Invalid Docker container ID."
            )

        return True