"""Coordinate trusted Docker sandbox execution."""

from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

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

from server_runner.sandbox_controller.temporary_container_executor import (
    TemporaryContainerExecutor,
    TemporaryContainerResult,
)


@dataclass(frozen=True)
class SandboxExecutionResult:
    """Represent the result of a sandbox program execution."""

    return_code: int | None
    stdout: str
    stderr: str
    timed_out: bool


class SandboxExecutionService:
    """Coordinate program execution using approved Docker operations."""

    def __init__(
        self,
        runtime: DockerRuntime | None = None,
        executor: CommandExecutor | None = None,
        temporary_executor: TemporaryContainerExecutor | None = None,
    ):
        """Initialize the Docker runtime and execution services."""

        # Build Docker commands without executing them directly.
        self.runtime = runtime or DockerRuntime()

        # Existing command executor for trusted operations.
        self.executor = executor or CommandExecutor()

        # Executor for short-lived, isolated Run containers.
        self.temporary_executor = (
            temporary_executor
            if temporary_executor is not None
            else TemporaryContainerExecutor(runtime=self.runtime)
        )

    def run_program(
        self,
        container_id: str,
        language: str,
        filename: str,
    ) -> SandboxExecutionResult:
        """Run a program inside an existing sandbox container.

        Legacy internal execution path.

        This method must not be exposed to untrusted developer requests.
        The Run button should use run_temporary_program() instead.
        """

        # Build the approved command for the existing container.
        command = self.runtime.build_run_command(
            container_id=container_id,
            language=language,
            filename=filename,
        )

        # Execute using the existing Run policy.
        result: CommandResult = self.executor.execute(
            command=command,
            mode=ExecutionMode.RUN,
        )

        # Return a consistent execution result.
        return SandboxExecutionResult(
            return_code=result.return_code,
            stdout=result.stdout,
            stderr=result.stderr,
            timed_out=result.timed_out,
        )

    def run_temporary_program(
        self,
        sandbox_id: UUID,
        workspace_path: Path,
        language: str,
    ) -> SandboxExecutionResult:
        """Run a program inside a temporary Docker container.

        This is the execution path intended for CodeView's Run button.

        The caller must independently verify:
        - The developer's identity.
        - Their permission to access the sandbox.
        - Their permission to execute code in the workspace.

        This method does not perform authorization itself.
        """

        # Execute the program using a temporary Docker container.
        result: TemporaryContainerResult = (
            self.temporary_executor.execute(
                sandbox_id=sandbox_id,
                workspace_path=workspace_path,
                language=language,
            )
        )

        # Convert the temporary executor result into the
        # standard result format used by CodeView.
        return SandboxExecutionResult(
            return_code=result.return_code,
            stdout=result.stdout,
            stderr=result.stderr,
            timed_out=result.timed_out,
        )