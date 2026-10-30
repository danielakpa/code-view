"""Prepare temporary source files for isolated CodeView execution."""

import tempfile

from contextlib import contextmanager
from pathlib import Path

from server_runner.sandbox_controller.code_snapshot import (
    CodeSnapshot,
)


class ExecutionWorkspaceError(ValueError):
    """Raised when execution workspace preparation fails."""


@contextmanager
def temporary_execution_workspace(snapshot: CodeSnapshot):
    """
    Create a temporary workspace containing validated source code.

    The workspace is automatically deleted when the context ends.

    IMPORTANT:
    This helper only prepares files. It does not authorize
    requests or execute Docker containers.
    """

    # Only accept validated CodeSnapshot objects.
    if not isinstance(snapshot, CodeSnapshot):
        raise ExecutionWorkspaceError(
            "A validated CodeSnapshot is required."
        )

    # Revalidate the snapshot because a dataclass can be
    # constructed directly without using prepare_code_snapshot().
    from server_runner.sandbox_controller.code_snapshot import (
        prepare_code_snapshot,
    )

    validated = prepare_code_snapshot(
        language=snapshot.language,
        source=snapshot.source,
    )

    # Reject snapshots containing unexpected filenames.
    if snapshot.filename != validated.filename:
        raise ExecutionWorkspaceError(
            "Invalid execution filename."
        )

    # Create an automatically cleaned-up temporary directory.
    with tempfile.TemporaryDirectory(
        prefix="codeview-run-",
    ) as directory:

        workspace = Path(directory)

        # Use the fixed filename selected by our validator.
        source_file = workspace / validated.filename

        # Write the source code using UTF-8 encoding.
        source_file.write_text(
            validated.source,
            encoding="utf-8",
        )

        # Make the source file readable by the container user.
        source_file.chmod(0o644)

        # Allow the container user to enter the directory.
        workspace.chmod(0o755)

        # Give the caller the temporary workspace path.
        yield workspace

        # TemporaryDirectory deletes the directory afterward.