"""Coordinate validated source code and temporary Docker execution."""

# ============================================================
# 1. IMPORTS
# ============================================================

# Used to identify a sandbox uniquely.
from uuid import UUID

# Validate and prepare the submitted source code.
from server_runner.sandbox_controller.code_snapshot import (
    prepare_code_snapshot,
)

# Create and clean up temporary execution workspaces.
from server_runner.sandbox_controller.execution_workspace import (
    temporary_execution_workspace,
)

# Execute programs using the existing Docker execution service.
from server_runner.sandbox_controller.sandbox_execution import (
    SandboxExecutionResult,
    SandboxExecutionService,
)


# ============================================================
# 2. CODE EXECUTION PIPELINE
# ============================================================

class CodeExecutionPipeline:
    """
    Coordinate code execution using CodeView's sandbox components.

    Execution process:

    1. Validate the sandbox ID.
    2. Validate and prepare the source code.
    3. Create a temporary workspace.
    4. Execute the program using Docker.
    5. Return the execution result.
    """

    def __init__(
        self,
        execution_service: SandboxExecutionService | None = None,
    ):
        """
        Initialize the execution pipeline.

        An execution service can be supplied during testing.
        Otherwise, create the default SandboxExecutionService.
        """

        # Reuse the provided execution service when available.
        if execution_service is not None:
            self.execution_service = execution_service

        else:
            # Create the default Docker execution service.
            self.execution_service = SandboxExecutionService()

    def execute(
        self,
        sandbox_id: UUID,
        language: str,
        source: str,
    ) -> SandboxExecutionResult:
        """
        Execute validated source code in a temporary container.

        Args:
            sandbox_id: UUID identifying the sandbox.
            language: Programming language to execute.
            source: Source code submitted by the developer.

        Returns:
            SandboxExecutionResult containing the execution outcome.
        """

        # ----------------------------------------------------
        # STEP 1: VALIDATE THE SANDBOX ID
        # ----------------------------------------------------

        # Reject values that are not valid UUID objects.
        if not isinstance(sandbox_id, UUID):
            raise ValueError("Invalid sandbox ID.")

        # Reject the all-zero UUID.
        if sandbox_id.int == 0:
            raise ValueError("Invalid sandbox ID.")

        # ----------------------------------------------------
        # STEP 2: PREPARE THE SOURCE CODE
        # ----------------------------------------------------

        # Validate the language and source code.
        #
        # This function creates a snapshot describing
        # the program that will be executed.
        snapshot = prepare_code_snapshot(
            language=language,
            source=source,
        )

        # ----------------------------------------------------
        # STEP 3: CREATE A TEMPORARY WORKSPACE
        # ----------------------------------------------------

        # The context manager creates the workspace and
        # cleans it up when execution finishes or fails.
        with temporary_execution_workspace(snapshot) as workspace:

            # ------------------------------------------------
            # STEP 4: EXECUTE THE PROGRAM
            # ------------------------------------------------

            # Delegate execution to the existing Docker service.
            #
            # Docker resource limits and isolation must be
            # enforced by SandboxExecutionService.
            result = self.execution_service.run_temporary_program(
                sandbox_id=sandbox_id,
                workspace_path=workspace,
                language=snapshot.language,
            )

            # ------------------------------------------------
            # STEP 5: RETURN THE EXECUTION RESULT
            # ------------------------------------------------

            # Return the result to the Sandbox Controller.
            return result