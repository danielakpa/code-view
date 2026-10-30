"""Test validation of Controller code execution requests."""

import unittest
from uuid import uuid4

from pydantic import ValidationError

from server_runner.sandbox_controller.operation import (
    SandboxOperation,
)

from server_runner.sandbox_controller.execution_request import (
    ControllerExecutionRequest,
)


class TestControllerExecutionRequest(unittest.TestCase):
    """Test valid and invalid code execution requests."""

    def setUp(self):
        """Prepare a valid execution request."""

        self.request_data = {
            "operation_request": {
                # Generate actual UUID objects.
                "request_id": uuid4(),
                "sandbox_id": uuid4(),

                # Identify the developer and group.
                "developer_id": 1,
                "group_id": 1,

                # Use the existing operation enum.
                "operation": SandboxOperation.RUN,
            },

            # Default programming language.
            "language": "python",

            # Default source code.
            "source": 'print("Hello CodeView")',
        }
    def test_valid_python_execution(self):
        """Accept valid Python source code."""

        request = ControllerExecutionRequest(
            **self.request_data
        )

        self.assertEqual(request.language, "python")
        self.assertEqual(
            request.source,
            'print("Hello CodeView")',
        )

    def test_valid_go_execution(self):
        """Accept valid Go source code."""

        self.request_data["language"] = "go"
        self.request_data["source"] = (
            'package main\n'
            'import "fmt"\n'
            'func main() { fmt.Println("Hello") }'
        )

        request = ControllerExecutionRequest(
            **self.request_data
        )

        self.assertEqual(request.language, "go")

    def test_valid_javascript_execution(self):
        """Accept valid JavaScript source code."""

        self.request_data["language"] = "javascript"
        self.request_data["source"] = (
            'console.log("Hello CodeView");'
        )

        request = ControllerExecutionRequest(
            **self.request_data
        )

        self.assertEqual(request.language, "javascript")

    def test_reject_unsupported_language(self):
        """Reject unsupported programming languages."""

        self.request_data["language"] = "php"

        with self.assertRaises(ValidationError):
            ControllerExecutionRequest(
                **self.request_data
            )

    def test_reject_empty_source(self):
        """Reject empty source code."""

        self.request_data["source"] = "   "

        with self.assertRaises(ValidationError):
            ControllerExecutionRequest(
                **self.request_data
            )

    def test_reject_oversized_source(self):
        """Reject code exceeding the 256 KiB limit."""

        self.request_data["source"] = "a" * (256 * 1024 + 1)

        with self.assertRaises(ValidationError):
            ControllerExecutionRequest(
                **self.request_data
            )

    def test_reject_non_run_operation(self):
        """Reject operations other than RUN."""

        self.request_data["operation_request"]["operation"] = SandboxOperation.STOP

        with self.assertRaises(ValidationError):
            ControllerExecutionRequest(
                **self.request_data
            )

    def test_reject_extra_fields(self):
        """Reject unexpected request information."""

        self.request_data["unexpected_field"] = "value"

        with self.assertRaises(ValidationError):
            ControllerExecutionRequest(
                **self.request_data
            )


if __name__ == "__main__":
    unittest.main()