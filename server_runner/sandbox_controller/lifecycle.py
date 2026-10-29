"""Manage the lifecycle states of CodeView developer sandboxes."""

from enum import Enum


class SandboxStatus(str, Enum):
    """Supported sandbox lifecycle states."""

    PREPARED = "prepared"
    STARTING = "starting"
    RUNNING = "running"
    STOPPED = "stopped"
    FAILED = "failed"


class SandboxLifecycleError(ValueError):
    """Raised when a sandbox lifecycle transition is invalid."""


# Define which state changes are permitted.
ALLOWED_TRANSITIONS = {
    SandboxStatus.PREPARED: {
        SandboxStatus.STARTING,
    },

    SandboxStatus.STARTING: {
        SandboxStatus.RUNNING,
        SandboxStatus.FAILED,
    },

    SandboxStatus.RUNNING: {
        SandboxStatus.STOPPED,
        SandboxStatus.FAILED,
    },

    SandboxStatus.STOPPED: {
        SandboxStatus.STARTING,
    },

    SandboxStatus.FAILED: {
        SandboxStatus.STARTING,
    },
}


class SandboxLifecycle:
    """Validate sandbox state changes."""

    def validate_transition(
        self,
        current_status: str,
        new_status: str,
    ) -> bool:
        """Check whether a sandbox can move to a new state."""

        # Convert the current status into a supported enum value.
        try:
            current = SandboxStatus(current_status)
            new = SandboxStatus(new_status)

        except ValueError as error:
            raise SandboxLifecycleError(
                "Unknown sandbox lifecycle status."
            ) from error

        # Find the allowed next states.
        allowed = ALLOWED_TRANSITIONS[current]

        # Reject unsupported state changes.
        if new not in allowed:
            raise SandboxLifecycleError(
                f"Cannot change sandbox from "
                f"'{current.value}' to '{new.value}'."
            )

        return True

    def transition(
        self,
        current_status: str,
        new_status: str,
    ) -> str:
        """Validate a transition and return the new status."""

        # Ensure the requested change is allowed.
        self.validate_transition(
            current_status,
            new_status,
        )

        # Return the validated status.
        return new_status