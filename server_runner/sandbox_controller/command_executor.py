"""Execute approved commands with an enforced timeout.

SECURITY:
This component is for trusted controller commands only.

Never pass developer-submitted code or shell commands directly
to this executor. Developer code must execute inside an
appropriately isolated sandbox.
"""

import os
import signal
import subprocess

from dataclasses import dataclass

from server_runner.sandbox_controller.execution_policy import (
    ExecutionMode,
    get_execution_policy,
)


class CommandExecutionError(RuntimeError):
    """Raised when a controller command cannot execute safely."""


@dataclass(frozen=True)
class CommandResult:
    """Represent the result of an executed command."""

    return_code: int | None
    stdout: str
    stderr: str
    timed_out: bool


class CommandExecutor:
    """Execute trusted commands and enforce execution timeouts."""

    def execute(
        self,
        command: list[str],
        mode: ExecutionMode = ExecutionMode.RUN,
    ) -> CommandResult:
        """Execute a trusted command using its execution policy."""

        # Only accept Run mode.
        # Interactive terminals need a separate streaming implementation.
        if mode != ExecutionMode.RUN:
            raise CommandExecutionError(
                "Interactive terminal execution is not supported here."
            )

        # Require a nonempty command list.
        if (
            not isinstance(command, list)
            or not command
            or any(
                not isinstance(argument, str)
                or not argument
                for argument in command
            )
        ):
            raise CommandExecutionError(
                "Command must be a nonempty list of strings."
            )

        # Read the existing 30-second timeout policy.
        policy = get_execution_policy(mode)

        timeout = policy.execution_timeout_seconds

        if timeout is None or timeout <= 0:
            raise CommandExecutionError(
                "Run mode requires a positive execution timeout."
            )

        try:
            # Start a new process group so timeout cleanup can
            # signal the command and its child processes.
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=False,
                start_new_session=True,
                close_fds=True,
            )

        except OSError as error:
            raise CommandExecutionError(
                "Failed to start the approved controller command."
            ) from error

        try:
            # Wait until the command finishes or times out.
            stdout, stderr = process.communicate(
                timeout=timeout
            )

            return CommandResult(
                return_code=process.returncode,
                stdout=stdout,
                stderr=stderr,
                timed_out=False,
            )

        except subprocess.TimeoutExpired:
            # Terminate the process group.
            # This is best-effort cleanup, not a security boundary.
            try:
                os.killpg(
                    process.pid,
                    signal.SIGKILL,
                )
            except ProcessLookupError:
                pass

            # Collect remaining output after termination.
            stdout, stderr = process.communicate()

            return CommandResult(
                return_code=process.returncode,
                stdout=stdout,
                stderr=stderr,
                timed_out=True,
            )