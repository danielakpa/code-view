"""Manage temporary Docker containers for CodeView Run requests.

This component belongs in the trusted sandbox controller.
Do not expose it directly to developer requests.
"""

import os
import signal
import subprocess

from dataclasses import dataclass
from pathlib import Path
from uuid import UUID, uuid4

from server_runner.sandbox_controller.execution_policy import (
    ExecutionMode,
    get_execution_policy,
)

from server_runner.sandbox_controller.runtime import (
    DockerRuntime,
)


class TemporaryContainerExecutionError(RuntimeError):
    """Raised when container execution or cleanup fails."""


@dataclass(frozen=True)
class TemporaryContainerResult:
    """Represent the result of running a program."""

    return_code: int | None
    stdout: str
    stderr: str
    timed_out: bool


class TemporaryContainerExecutor:
    """Create, run, and clean up temporary containers."""

    def __init__(self, runtime: DockerRuntime | None = None):
        """Initialize the existing Docker runtime."""

        self.runtime = runtime or DockerRuntime()

    def execute(
        self,
        sandbox_id: UUID,
        workspace_path: Path,
        language: str,
    ) -> TemporaryContainerResult:
        """Execute a program inside a temporary container."""

        # Generate a unique name before creating the container.
        container_name = (
            f"codeview-run-{sandbox_id.hex}-{uuid4().hex[:12]}"
        )

        # Build the approved Docker creation command.
        create_command = self.runtime.build_temporary_create_command(
            sandbox_id=sandbox_id,
            workspace_path=workspace_path,
            language=language,
            container_name=container_name,
        )

        # Read the existing 30-second Run timeout.
        policy = get_execution_policy(ExecutionMode.RUN)
        timeout = policy.execution_timeout_seconds

        if timeout is None or timeout <= 0:
            raise TemporaryContainerExecutionError(
                "Run mode requires a positive timeout."
            )

        container_id = None
        process = None
        result = None
        execution_error = None
        cleanup_error = None

        try:
            # STEP 1: Create the temporary Docker container.
            created = subprocess.run(
                create_command,
                capture_output=True,
                text=True,
                timeout=45,
                check=True,
            )

            # Get the container ID returned by Docker.
            container_id = created.stdout.strip()

            # Validate the Docker-generated container ID.
            self.runtime._validate_container_id(container_id)

            # STEP 2: Build the command to start the container.
            start_command = (
                self.runtime.build_temporary_start_command(
                    container_id
                )
            )

            # STEP 3: Start the container and collect its output.
            process = subprocess.Popen(
                start_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=False,
                start_new_session=True,
            )

            try:
                # Wait for the program to finish within 30 seconds.
                stdout, stderr = process.communicate(
                    timeout=timeout
                )

                # Save the successful execution result.
                result = TemporaryContainerResult(
                    return_code=process.returncode,
                    stdout=stdout,
                    stderr=stderr,
                    timed_out=False,
                )

            except subprocess.TimeoutExpired:
                # The program exceeded the execution time limit.

                # STEP 4: Try to stop the Docker container.
                # Docker kill may fail if the container already stopped.
                try:
                    subprocess.run(
                        self.runtime.build_temporary_kill_command(
                            container_id
                        ),
                        capture_output=True,
                        text=True,
                        timeout=10,
                        check=False,
                    )

                except (OSError, subprocess.SubprocessError):
                    # Continue stopping the host-side Docker process.
                    pass

                # STEP 5: Terminate the host-side Docker process.
                if process.poll() is None:
                    try:
                        os.killpg(
                            process.pid,
                            signal.SIGKILL,
                        )

                    except ProcessLookupError:
                        pass

                # STEP 6: Collect any remaining output.
                try:
                    stdout, stderr = process.communicate(
                        timeout=5
                    )

                except subprocess.TimeoutExpired as error:
                    raise TemporaryContainerExecutionError(
                        "Docker client did not terminate after timeout."
                    ) from error

                # Save the timeout result.
                result = TemporaryContainerResult(
                    return_code=process.returncode,
                    stdout=stdout,
                    stderr=stderr,
                    timed_out=True,
                )

        except Exception as error:
            # Remember execution errors.
            # Cleanup must still happen.
            execution_error = error

        finally:
            # STEP 7: Stop the host-side Docker process
            # if it is still running.
            if process is not None and process.poll() is None:
                try:
                    os.killpg(
                        process.pid,
                        signal.SIGKILL,
                    )

                    # Wait briefly for the process to terminate.
                    process.communicate(timeout=5)

                except (
                    ProcessLookupError,
                    subprocess.SubprocessError,
                ):
                    pass

            # STEP 8: Remove the temporary container.
            # Use its unique name so cleanup still works
            # if Docker created it but failed to return its ID.
            cleanup_target = container_name

            try:
                subprocess.run(
                    [
                        "docker",
                        "rm",
                        "--force",
                        cleanup_target,
                    ],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    check=False,
                )

                # STEP 9: Verify that the container no longer exists.
                # Ask Docker to list the exact container name.
                list_result = subprocess.run(
                    self.runtime.build_temporary_list_command(
                        container_name
                    ),
                    capture_output=True,
                    text=True,
                    timeout=10,
                    check=False,
                )

                # A Docker error means we cannot verify cleanup.
                if list_result.returncode != 0:
                    raise TemporaryContainerExecutionError(
                        "Docker could not verify container cleanup."
                    )

                # If Docker lists the container, cleanup failed.
                remaining_containers = list_result.stdout.strip()

                if remaining_containers:
                    raise TemporaryContainerExecutionError(
                        "Temporary container still exists after cleanup."
                    )

            except (
                OSError,
                subprocess.SubprocessError,
                TemporaryContainerExecutionError,
            ) as error:
                # Record cleanup errors instead of ignoring them.
                cleanup_error = error

        # Never silently ignore cleanup failures.
        if cleanup_error is not None:
            raise TemporaryContainerExecutionError(
                "Container cleanup failed; manual recovery may be required."
            ) from cleanup_error

        # Report any execution errors after attempting cleanup.
        if execution_error is not None:
            raise TemporaryContainerExecutionError(
                "Temporary container execution failed."
            ) from execution_error

        # Ensure execution produced a result.
        if result is None:
            raise TemporaryContainerExecutionError(
                "Execution did not produce a result."
            )

        # Return the program output and execution status.
        return result