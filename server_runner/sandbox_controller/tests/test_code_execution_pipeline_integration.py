"""Real Docker integration tests for CodeView execution."""

import os
import unittest

from uuid import uuid4

from server_runner.sandbox_controller.code_execution_pipeline import (
    CodeExecutionPipeline,
)


@unittest.skipUnless(
    os.environ.get("CODEVIEW_DOCKER_INTEGRATION") == "1",
    "Real Docker integration tests are disabled.",
)
class CodeExecutionPipelineIntegrationTests(unittest.TestCase):
    """Test Python, Go, and JavaScript inside Docker."""

    def setUp(self):
        """Prepare the existing execution pipeline."""

        self.pipeline = CodeExecutionPipeline()
        self.sandbox_id = uuid4()

    def test_python_execution(self):
        """Execute Python inside Docker."""

        result = self.pipeline.execute(
            sandbox_id=self.sandbox_id,
            language="python",
            source='print("Hello Python")',
        )

        self.assertEqual(result.return_code, 0)
        self.assertEqual(result.stdout.strip(), "Hello Python")
        self.assertFalse(result.timed_out)

    def test_go_execution(self):
        """Execute Go inside Docker."""

        result = self.pipeline.execute(
            sandbox_id=self.sandbox_id,
            language="go",
            source=(
                'package main\n'
                'import "fmt"\n'
                'func main() {\n'
                '    fmt.Println("Hello Go")\n'
                '}\n'
            ),
        )

        # Display Go's error message if execution fails.
        self.assertEqual(
            result.return_code,
            0,
            msg=f"Go execution failed:\n{result.stderr}\n{result.stdout}",
        )        
        self.assertEqual(result.stdout.strip(), "Hello Go")
        self.assertFalse(result.timed_out)

    def test_javascript_execution(self):
        """Execute JavaScript inside Docker."""

        result = self.pipeline.execute(
            sandbox_id=self.sandbox_id,
            language="javascript",
            source='console.log("Hello JavaScript");',
        )

        self.assertEqual(result.return_code, 0)
        self.assertEqual(result.stdout.strip(), "Hello JavaScript")
        self.assertFalse(result.timed_out)