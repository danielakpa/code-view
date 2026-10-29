"""Integration tests for real Docker container execution.

These tests use actual Docker containers.

Run them only in a controlled development environment.
They are skipped unless CODEVIEW_DOCKER_INTEGRATION=1.
"""

import os
import shutil
import subprocess
import tempfile
import unittest

from pathlib import Path
from uuid import uuid4
from unittest.mock import patch

from server_runner.sandbox_controller.temporary_container_executor import (
    TemporaryContainerExecutor,
)

from server_runner.sandbox_controller.execution_policy import (
    ExecutionMode,
    ExecutionPolicy,
)

from server_runner.sandbox_controller.runtime import (
    DEVELOPER_IMAGE,
)


@unittest.skipUnless(
    os.getenv("CODEVIEW_DOCKER_INTEGRATION") == "1",
    "Real Docker integration tests are disabled.",
)
class TestTemporaryContainerIntegration(unittest.TestCase):
    """Test temporary execution using real Docker."""

    @classmethod
    def setUpClass(cls):
        """Check Docker and the developer image."""

        if shutil.which("docker") is None:
            raise unittest.SkipTest("Docker is not installed.")

        # Check Docker daemon access.
        docker_info = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )

        if docker_info.returncode != 0:
            raise unittest.SkipTest(
                "Docker daemon is unavailable to this user."
            )

        # Check that our developer image exists locally.
        image_check = subprocess.run(
            ["docker", "image", "inspect", DEVELOPER_IMAGE],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )

        if image_check.returncode != 0:
            raise unittest.SkipTest(
                "CodeView developer image is not available."
            )

    def setUp(self):
        """Create an isolated workspace for each test."""

        self.sandbox_id = uuid4()

        self.temp_directory = tempfile.TemporaryDirectory()

        self.workspace_path = Path(self.temp_directory.name)

        # Make the workspace readable by the container user.
        self.workspace_path.chmod(0o755)

        self.executor = TemporaryContainerExecutor()

    def tearDown(self):
        """Remove the temporary test workspace."""

        self.temp_directory.cleanup()

    def assert_no_temporary_container(self):
        """Check that this test's containers were removed."""

        result = subprocess.run(
            [
                "docker",
                "ps",
                "-a",
                "--filter",
                f"name=codeview-run-{self.sandbox_id.hex}-",
                "--format",
                "{{.Names}}",
            ],
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        )

        self.assertEqual(
            result.stdout.strip(),
            "",
            "Temporary Docker container was not removed.",
        )

    def test_python_program_runs_and_is_removed(self):
        """Execute Python and verify cleanup."""

        source_file = self.workspace_path / "main.py"

        source_file.write_text(
            'print("Hello from CodeView")\n'
        )

        result = self.executor.execute(
            sandbox_id=self.sandbox_id,
            workspace_path=self.workspace_path,
            language="python",
        )

        self.assertFalse(result.timed_out)

        self.assertEqual(result.return_code, 0)

        self.assertIn(
            "Hello from CodeView",
            result.stdout,
        )

        # Source code must remain unchanged.
        self.assertEqual(
            source_file.read_text(),
            'print("Hello from CodeView")\n',
        )

        self.assert_no_temporary_container()

    def test_timeout_terminates_container(self):
        """Verify that long-running code is terminated."""

        source_file = self.workspace_path / "main.py"

        source_file.write_text(
            "import time\n"
            "while True:\n"
            "    time.sleep(1)\n"
        )

        # Use a short timeout for integration testing.
        short_policy = ExecutionPolicy(
            mode=ExecutionMode.RUN,
            execution_timeout_seconds=2,
            idle_timeout_seconds=None,
        )

        with patch(
            "server_runner.sandbox_controller."
            "temporary_container_executor.get_execution_policy",
            return_value=short_policy,
        ):
            result = self.executor.execute(
                sandbox_id=self.sandbox_id,
                workspace_path=self.workspace_path,
                language="python",
            )

        self.assertTrue(result.timed_out)

        # Verify Docker no longer lists the temporary container.
        self.assert_no_temporary_container()

        # The source file must remain intact.
        self.assertTrue(source_file.exists())


if __name__ == "__main__":
    unittest.main()