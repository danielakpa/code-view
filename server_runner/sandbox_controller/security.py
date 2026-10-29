"""Security configuration for CodeView developer sandboxes."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ControllerSecurityConfig:
    """
    Define the default security restrictions for a sandbox.

    These values are configuration only.
    The runtime must enforce them when creating a sandbox.
    """

    # Maximum memory available to a sandbox.
    memory_limit_mb: int = 512

    # Maximum CPU allocation.
    cpu_limit: float = 1.0

    # Maximum number of processes.
    process_limit: int = 64

    # Maximum execution time in seconds.
    execution_timeout_seconds: int = 30

    # Disable network access by default.
    network_enabled: bool = False

    # Prevent processes from gaining additional privileges.
    no_new_privileges: bool = True

    # Make the container's root filesystem read-only.
    read_only_root: bool = True

    # Run developer code as a non-root user.
    run_as_non_root: bool = True


def get_controller_security_config():
    """Return CodeView's default sandbox security configuration."""

    return ControllerSecurityConfig()