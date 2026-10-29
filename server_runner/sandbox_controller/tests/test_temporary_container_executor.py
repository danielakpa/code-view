"""Tests for temporary Docker container execution."""

import subprocess
import tempfile
import unittest

from pathlib import Path
from unittest.mock import MagicMock, patch
from uuid import uuid4

from server_runner.sandbox_controller.temporary_container_executor import (
    TemporaryContainerExecutor,
    TemporaryContainerExecutionError,
)


class TestTemporaryContainerExecutor(unittest.TestCase):
    """Test temporary container execution and cleanup."""

    def setUp(self):
        """Prepare the test environment."""

        # Mock DockerRuntime so tests do not use real Docker.
        self.runtime = MagicMock()

        self.runtime.build_temporary_create_command.return_value = [
            "docker",
            "create",
        ]

        self.runtime.build_temporary_start_command.return_value = [
            "docker",
            "start",
        ]

        self.runtime.build_temporary_kill_command.return_value = [
            "docker",
            "kill",
        ]

        # Build the Docker command used to verify container cleanup.
        self.runtime.build_temporary_list_command.side_effect = (
            lambda name: [
                "docker",
                "ps",
                "--all",
                "--no-trunc",
                "--filter",
                f"name=^/{name}$",
                "--format",
                "{{.Names}}",
            ]
        )

        # Create the executor using our mocked runtime.
        self.executor = TemporaryContainerExecutor(
            runtime=self.runtime
        )

        self.sandbox_id = uuid4()

        # Create a temporary workspace for testing.
        self.temp_directory = tempfile.TemporaryDirectory()

        self.workspace_path = Path(
            self.temp_directory.name
        )

        # Simulate a valid Docker container ID.
        self.container_id = "a" * 64

    def tearDown(self):
        """Clean up the temporary workspace."""

        self.temp_directory.cleanup()
    def fake_docker_run(self, command, **kwargs):
        """Simulate Docker commands without running real containers."""

        # Docker successfully creates the container.
        if command[:2] == ["docker", "create"]:
            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout=self.container_id,
                stderr="",
            )

        # Docker successfully kills a container.
        if command[:2] == ["docker", "kill"]:
            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout=self.container_id,
                stderr="",
            )

        # Docker successfully removes a temporary container.
        if command[:3] == ["docker", "rm", "--force"]:
            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout=command[3],
                stderr="",
            )

        # Docker confirms no matching container exists.
        if command[:3] == ["docker", "ps", "--all"]:
            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout="",
                stderr="",
            )

        # Reject unexpected Docker commands.
        raise AssertionError(
            f"Unexpected Docker command: {command}"
        )

    @patch(
        "server_runner.sandbox_controller."
        "temporary_container_executor.subprocess.Popen"
    )
    @patch(
        "server_runner.sandbox_controller."
        "temporary_container_executor.subprocess.run"
    )
    def test_successful_execution_removes_container(
        self,
        mock_run,
        mock_popen,
    ):
        """A completed program must have its container removed."""

        # Use our fake Docker command handler.
        mock_run.side_effect = self.fake_docker_run

        # Simulate a program completing successfully.
        process = MagicMock()

        process.communicate.return_value = (
            "Hello CodeView\n",
            "",
        )

        process.returncode = 0
        process.poll.return_value = 0

        mock_popen.return_value = process

        # Execute the program.
        result = self.executor.execute(
            sandbox_id=self.sandbox_id,
            workspace_path=self.workspace_path,
            language="python",
        )

        # Verify the execution result.
        self.assertFalse(result.timed_out)

        self.assertEqual(
            result.stdout,
            "Hello CodeView\n",
        )

        self.assertEqual(result.return_code, 0)

        # Verify Docker removal was requested.
        removal_calls = [
            call
            for call in mock_run.call_args_list
            if call.args[0][:3] == [
                "docker",
                "rm",
                "--force",
            ]
        ]

        self.assertEqual(len(removal_calls), 1)

        # Verify cleanup verification was requested.
        self.runtime.build_temporary_list_command.assert_called_once()


    @patch(
        "server_runner.sandbox_controller."
        "temporary_container_executor.os.killpg"
    )
    @patch(
        "server_runner.sandbox_controller."
        "temporary_container_executor.subprocess.Popen"
    )
    @patch(
        "server_runner.sandbox_controller."
        "temporary_container_executor.subprocess.run"
    )
    def test_timeout_kills_and_removes_container(
        self,
        mock_run,
        mock_popen,
        mock_killpg,
    ):
        """A timed-out program must be killed and removed."""

        mock_run.side_effect = self.fake_docker_run

        # Simulate a program exceeding the execution timeout.
        process = MagicMock()

        process.communicate.side_effect = [
            subprocess.TimeoutExpired(
                cmd="docker start",
                timeout=30,
            ),
            ("", ""),
        ]

        # First poll: still running.
        # Second poll: process has terminated.
        process.poll.side_effect = [
            None,
            0,
        ]

        process.pid = 12345
        process.returncode = -9

        mock_popen.return_value = process

        # Execute the program.
        result = self.executor.execute(
            sandbox_id=self.sandbox_id,
            workspace_path=self.workspace_path,
            language="python",
        )

        # Verify the timeout was detected.
        self.assertTrue(result.timed_out)

        # Verify Docker kill was requested.
        self.runtime.build_temporary_kill_command.assert_called_once_with(
            self.container_id
        )

        # Verify the host-side process was terminated.
        mock_killpg.assert_called_once()

        # Verify the temporary container was removed.
        removal_calls = [
            call
            for call in mock_run.call_args_list
            if call.args[0][:3] == [
                "docker",
                "rm",
                "--force",
            ]
        ]

        self.assertEqual(len(removal_calls), 1)

        # Verify cleanup verification was requested.
        self.runtime.build_temporary_list_command.assert_called_once()

    @patch(
        "server_runner.sandbox_controller."
        "temporary_container_executor.subprocess.run"
    )
    def test_container_creation_failure_is_rejected(
        self,
        mock_run,
    ):
        """Reject container creation failures."""

        def fake_creation_failure(command, **kwargs):

            # Simulate Docker failing to create a container.
            if command[:2] == ["docker", "create"]:
                raise subprocess.CalledProcessError(
                    returncode=1,
                    cmd=command,
                )

            # Allow cleanup to attempt removal.
            if command[:3] == [
                "docker",
                "rm",
                "--force",
            ]:
                return subprocess.CompletedProcess(
                    args=command,
                    returncode=1,
                    stdout="",
                    stderr="Error: No such container",
                )

            # Docker confirms no matching container exists.
            if command[:3] == [
                "docker",
                "ps",
                "--all",
            ]:
                return subprocess.CompletedProcess(
                    args=command,
                    returncode=0,
                    stdout="",
                    stderr="",
                )

            # Reject unexpected commands.
            raise AssertionError(
                f"Unexpected Docker command: {command}"
            )

        mock_run.side_effect = fake_creation_failure

        # Container creation failure must raise an error.
        with self.assertRaises(
            TemporaryContainerExecutionError
        ):
            self.executor.execute(
                sandbox_id=self.sandbox_id,
                workspace_path=self.workspace_path,
                language="python",
            )

    @patch(
        "server_runner.sandbox_controller."
        "temporary_container_executor.subprocess.Popen"
    )
    @patch(
        "server_runner.sandbox_controller."
        "temporary_container_executor.subprocess.run"
    )
    def test_cleanup_failure_is_reported(
        self,
        mock_run,
        mock_popen,
    ):
        """Report an error if the container still exists."""

        def fake_cleanup_failure(command, **kwargs):

            # Simulate successful container creation.
            if command[:2] == ["docker", "create"]:
                return subprocess.CompletedProcess(
                    args=command,
                    returncode=0,
                    stdout=self.container_id,
                    stderr="",
                )

            # Simulate Docker failing to remove the container.
            if command[:3] == [
                "docker",
                "rm",
                "--force",
            ]:
                return subprocess.CompletedProcess(
                    args=command,
                    returncode=1,
                    stdout="",
                    stderr="Permission denied",
                )

            # Docker confirms the container still exists.
            if command[:3] == [
                "docker",
                "ps",
                "--all",
            ]:
                return subprocess.CompletedProcess(
                    args=command,
                    returncode=0,
                    stdout="codeview-run-test-container\n",
                    stderr="",
                )

            # Reject unexpected commands.
            raise AssertionError(
                f"Unexpected Docker command: {command}"
            )

        mock_run.side_effect = fake_cleanup_failure

        # Simulate a program completing successfully.
        process = MagicMock()

        process.communicate.return_value = (
            "Hello CodeView",
            "",
        )

        process.returncode = 0
        process.poll.return_value = 0

        mock_popen.return_value = process

        # Cleanup failure must raise an error.
        with self.assertRaises(
            TemporaryContainerExecutionError
        ):
            self.executor.execute(
                sandbox_id=self.sandbox_id,
                workspace_path=self.workspace_path,
                language="python",
            )


if __name__ == "__main__":
    unittest.main()