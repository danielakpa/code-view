"""Service layer for CodeView's sandbox controller."""

from server_runner.sandbox_controller.security import (
    get_controller_security_config,
)


class SandboxControllerService:
    """Coordinate internal sandbox controller operations."""

    def __init__(self):
        """Initialize the controller service."""

        # Load the controller's sandbox security configuration.
        self.security = get_controller_security_config()

    def health_check(self):
        """Return the controller's health information."""

        return {
            "service": "codeview-sandbox-controller",
            "status": "healthy",
        }

    def get_security_summary(self):
        """
        Return non-secret sandbox security settings.

        This does not create a sandbox.
        """

        return {
            "memory_limit_mb": self.security.memory_limit_mb,
            "cpu_limit": self.security.cpu_limit,
            "process_limit": self.security.process_limit,
            "execution_timeout_seconds": (
                self.security.execution_timeout_seconds
            ),
            "network_enabled": self.security.network_enabled,
            "no_new_privileges": self.security.no_new_privileges,
            "read_only_root": self.security.read_only_root,
            "run_as_non_root": self.security.run_as_non_root,
        }