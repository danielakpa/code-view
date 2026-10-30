"""Prepare private temporary source files for isolated CodeView execution."""

import subprocess
import tempfile

from contextlib import contextmanager
from pathlib import Path

from server_runner.sandbox_controller.code_snapshot import (
    CodeSnapshot,
    prepare_code_snapshot,
)


# The unprivileged developer user inside our Docker image.
DOCKER_DEVELOPER_UID = 10001


class ExecutionWorkspaceError(ValueError):
    """Raised when execution workspace preparation fails."""


def grant_docker_read_access(workspace: Path, source_file: Path):
    """Allow only the Docker developer user to read the source code."""

    try:
        # Give Docker's developer user permission to enter the directory.
        subprocess.run(
            [
                "setfacl",
                "-m",
                f"u:{DOCKER_DEVELOPER_UID}:rx",
                str(workspace),
            ],
            check=True,
            capture_output=True,
            timeout=5,
        )

        # Give Docker's developer user read-only access to the file.
        subprocess.run(
            [
                "setfacl",
                "-m",
                f"u:{DOCKER_DEVELOPER_UID}:r",
                str(source_file),
            ],
            check=True,
            capture_output=True,
            timeout=5,
        )

    except (OSError, subprocess.SubprocessError) as error:
        raise ExecutionWorkspaceError(
            "Failed to configure private execution permissions."
        ) from error


@contextmanager
def temporary_execution_workspace(snapshot: CodeSnapshot):
    """Create a private temporary workspace for Docker execution."""

    # Step 1: Require a CodeSnapshot.
    if not isinstance(snapshot, CodeSnapshot):
        raise ExecutionWorkspaceError(
            "A validated CodeSnapshot is required."
        )

    # Step 2: Revalidate the source code and language.
    validated = prepare_code_snapshot(
        language=snapshot.language,
        source=snapshot.source,
    )

    # Step 3: Reject unexpected filenames.
    if snapshot.filename != validated.filename:
        raise ExecutionWorkspaceError(
            "Invalid execution filename."
        )

    # Step 4: Create a temporary workspace.
    with tempfile.TemporaryDirectory(
        prefix="codeview-run-",
    ) as directory:

        workspace = Path(directory)
        source_file = workspace / validated.filename

        # Step 5: Write the developer's source code.
        source_file.write_text(
            validated.source,
            encoding="utf-8",
        )

        # Step 6: Restrict access to the workspace owner.
        workspace.chmod(0o700)
        source_file.chmod(0o600)

        # Step 7: Grant Docker's developer user read-only access.
        grant_docker_read_access(
            workspace=workspace,
            source_file=source_file,
        )

        # Step 8: Return the workspace for execution.
        # TemporaryDirectory removes it when the context ends.
        yield workspace