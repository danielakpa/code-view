"""Security configuration for CodeView developer sandboxes."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SandboxSecurityConfig:
    """Define resource limits for developer sandboxes."""

    # Maximum memory allocated to one sandbox (MB).
    memory_limit_mb: int = 512

    # Maximum CPU cores allocated to one sandbox.
    cpu_limit: float = 1.0

    # Maximum number of processes allowed.
    process_limit: int = 64

    # Maximum execution time for one command (seconds).
    execution_timeout: int = 30

    # Disable network access by default.
    network_enabled: bool = False

    # Prevent the container from gaining new privileges.
    no_new_privileges: bool = True

    # Run the container filesystem as read-only.
    read_only_root: bool = True

    # Run commands as a non-root user.
    run_as_non_root: bool = True


def get_sandbox_security_config():
    """Return the default CodeView sandbox security settings."""

    return SandboxSecurityConfig()