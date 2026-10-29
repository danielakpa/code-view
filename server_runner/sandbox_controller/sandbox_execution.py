"""Coordinate trusted Docker sandbox execution."""

from dataclasses import dataclass

from server_runner.sandbox_controller.command_executor import (
    CommandExecutor,
    CommandResult,
)

from server_runner.sandbox_controller.execution_policy import (
    ExecutionMode,
)

from server_runner.sandbox_controller.runtime import (
    DockerRuntime,
)


@dataclass(frozen=True)
class SandboxExecutionResult:
    """Represent a sandbox program execution result."""

    return_code: int | None
    stdout: str
    stderr: str
    timed_out: bool


class SandboxExecutionService:
    """Run approved programs through the Docker runtime."""

    def __init__(
        self,
        runtime: DockerRuntime | None = None,
        executor: CommandExecutor | None = None,
    ):
        """Initialize the runtime and command executor."""

        self.runtime = runtime or DockerRuntime()
        self.executor = executor or CommandExecutor()

    def run_program(
        self,
        container_id: str,
        language: str,
        filename: str,
    ) -> SandboxExecutionResult:
        """Run a supported program inside its sandbox."""

        # Build the approved Docker command.
        command = self.runtime.build_run_command(
            container_id=container_id,
            language=language,
            filename=filename,
        )

        # Apply the existing 30-second Run policy.
        result: CommandResult = self.executor.execute(
            command=command,
            mode=ExecutionMode.RUN,
        )

        return SandboxExecutionResult(
            return_code=result.return_code,
            stdout=result.stdout,
            stderr=result.stderr,
            timed_out=result.timed_out,
        )