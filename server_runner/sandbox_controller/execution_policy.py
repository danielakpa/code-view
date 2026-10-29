"""Define execution rules for CodeView sandboxes."""

from dataclasses import dataclass
from enum import Enum

from server_runner.sandbox_controller.security import (
    get_controller_security_config,
)


class ExecutionMode(str, Enum):
    """Supported execution modes."""

    RUN = "run"
    TERMINAL = "terminal"


@dataclass(frozen=True)
class ExecutionPolicy:
    """Timeout rules for a developer execution mode."""

    mode: ExecutionMode
    execution_timeout_seconds: int | None
    idle_timeout_seconds: int | None


def get_execution_policy(mode: ExecutionMode) -> ExecutionPolicy:
    """Return the correct policy for the requested mode."""

    # Reject unknown execution modes.
    if not isinstance(mode, ExecutionMode):
        raise ValueError("Unsupported execution mode.")

    # Load our existing security settings.
    security = get_controller_security_config()

    if mode == ExecutionMode.RUN:
        return ExecutionPolicy(
            mode=mode,
            execution_timeout_seconds=security.execution_timeout_seconds,
            idle_timeout_seconds=None,
        )

    if mode == ExecutionMode.TERMINAL:
        return ExecutionPolicy(
            mode=mode,
            execution_timeout_seconds=None,
            idle_timeout_seconds=1800,  # 30 minutes
        )

    raise ValueError("Unsupported execution mode.")