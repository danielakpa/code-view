"""Coordinate validated source code and temporary Docker execution."""

from uuid import UUID

from server_runner.sandbox_controller.code_snapshot import (
    prepare_code_snapshot,
)

from server_runner.sandbox_controller.execution_workspace import (
    temporary_execution_workspace,
)

from server_runner.sandbox_controller.sandbox_execution import (
    SandboxExecutionResult,
    SandboxExecutionService,
)


class CodeExecutionPipeline:
    """Prepare and execute code using existing sandbox components."""

    def __init__(
        self,
        execution_service: SandboxExecutionService | None = None,
    ):
        """Initialize the existing execution service."""

        self.execution_service = (
            execution_service
            if execution_service is not None
            else SandboxExecutionService()
        )

    def execute(
        self,
        sandbox_id: UUID,
        language: str,
        source: str,
    ) -> SandboxExecutionResult:
        """Execute validated source code in a temporary container."""

        # Step 1: Validate the sandbox ID.
        if not isinstance(sandbox_id, UUID) or sandbox_id.int == 0:
            raise ValueError("Invalid sandbox ID.")

        # Step 2: Validate the programming language and source code.
        snapshot = prepare_code_snapshot(
            language=language,
            source=source,
        )

        # Step 3: Create a temporary workspace.
        with temporary_execution_workspace(snapshot) as workspace:

            # Step 4: Run the program using the existing Docker executor.
            result = self.execution_service.run_temporary_program(
                sandbox_id=sandbox_id,
                workspace_path=workspace,
                language=snapshot.language,
            )

            # Step 5: Return the program output.
            return result