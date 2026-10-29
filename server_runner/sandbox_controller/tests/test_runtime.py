"""Tests for the CodeView Docker runtime."""

import tempfile
import unittest

from pathlib import Path
from uuid import uuid4

from server_runner.sandbox_controller.runtime import (
    DEVELOPER_IMAGE,
    DockerRuntime,
    SandboxRuntimeError,
)


class TestDockerRuntime(unittest.TestCase):
    """Test restricted Docker command construction."""

    def setUp(self):
        """Create the Docker runtime."""

        self.runtime = DockerRuntime()

    def test_create_command(self):
        """Verify that container creation includes security restrictions."""

        with tempfile.TemporaryDirectory() as directory:

            sandbox_id = uuid4()
            workspace = Path(directory)

            command = self.runtime.build_create_command(
                sandbox_id,
                workspace,
            )

            self.assertEqual(command[0:2], ["docker", "create"])

            self.assertIn("--memory", command)
            self.assertIn("--cpus", command)
            self.assertIn("--pids-limit", command)
            self.assertIn("--network", command)
            self.assertIn("none", command)
            self.assertIn("--cap-drop", command)
            self.assertIn("ALL", command)
            self.assertIn("--read-only", command)
            self.assertIn("--user", command)

            self.assertIn(DEVELOPER_IMAGE, command)

            # Ensure the command does not execute anything.
            self.assertEqual(command[-2:], ["sleep", "infinity"])

    def test_create_command_rejects_invalid_id(self):
        """Reject an invalid sandbox ID."""

        with tempfile.TemporaryDirectory() as directory:

            with self.assertRaises(SandboxRuntimeError):
                self.runtime.build_create_command(
                    "invalid",
                    Path(directory),
                )

    def test_create_command_rejects_missing_workspace(self):
        """Reject a workspace that doesn't exist."""

        with self.assertRaises(SandboxRuntimeError):
            self.runtime.build_create_command(
                uuid4(),
                Path("/nonexistent-codeview-workspace"),
            )

    def test_start_command(self):
        """Build a command to start a container."""

        container_id = "a" * 64

        command = self.runtime.build_start_command(container_id)

        self.assertEqual(
            command,
            ["docker", "start", container_id],
        )

    def test_stop_command(self):
        """Build a command to stop a container."""

        container_id = "b" * 64

        command = self.runtime.build_stop_command(container_id)

        self.assertEqual(
            command,
            ["docker", "stop", "--time", "10", container_id],
        )

    def test_inspect_command(self):
        """Build a command to inspect a container."""

        container_id = "c" * 64

        command = self.runtime.build_inspect_command(container_id)

        self.assertEqual(
            command,
            [
                "docker",
                "inspect",
                "--format",
                "{{.State.Status}}",
                container_id,
            ],
        )

    def test_invalid_container_id(self):
        """Reject malformed container IDs."""

        with self.assertRaises(SandboxRuntimeError):
            self.runtime.build_start_command("invalid")

    def test_docker_socket_is_not_mounted(self):
        """Ensure the Docker socket is not exposed to a sandbox."""

        with tempfile.TemporaryDirectory() as directory:

            command = self.runtime.build_create_command(
                uuid4(),
                Path(directory),
            )

            command_text = " ".join(command)

            self.assertNotIn(
                "/var/run/docker.sock",
                command_text,
            )


if __name__ == "__main__":
    unittest.main()