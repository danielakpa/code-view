"""Tests for CodeView Runner execution request validation."""

# ============================================================
# 1. IMPORTS
# ============================================================

# Python's built-in testing framework.
import unittest

# Pydantic raises this error when request validation fails.
from pydantic import ValidationError

# Import the request model we want to test.
from server_runner.runner_service.execution_request import (
    CodeExecutionRequest,
)


# ============================================================
# 2. EXECUTION REQUEST TESTS
# ============================================================

class CodeExecutionRequestTests(unittest.TestCase):
    """Verify that execution requests are validated correctly."""

    def setUp(self):
        """Prepare a valid execution request for each test."""

        # This represents an authorized Python Code Board.
        self.valid_request = {
            "board_id": 10,
            "developer_id": 5,
            "group_id": 3,
            "language": "python",
            "source": 'print("Hello CodeView")',
        }

    # --------------------------------------------------------
    # TEST 1: VALID EXECUTION REQUEST
    # --------------------------------------------------------

    def test_valid_execution_request(self):
        """Accept a request containing all required fields."""

        request = CodeExecutionRequest(
            **self.valid_request
        )

        self.assertEqual(request.board_id, 10)
        self.assertEqual(request.developer_id, 5)
        self.assertEqual(request.group_id, 3)
        self.assertEqual(request.language, "python")
        self.assertEqual(
            request.source,
            'print("Hello CodeView")',
        )

    # --------------------------------------------------------
    # TEST 2: SUPPORTED PROGRAMMING LANGUAGES
    # --------------------------------------------------------

    def test_supported_languages(self):
        """Accept Python, Go, and JavaScript."""

        supported_languages = [
            "python",
            "go",
            "javascript",
        ]

        for language in supported_languages:

            with self.subTest(language=language):

                request_data = self.valid_request.copy()

                request_data["language"] = language

                request = CodeExecutionRequest(
                    **request_data
                )

                self.assertEqual(
                    request.language,
                    language,
                )

    # --------------------------------------------------------
    # TEST 3: UNSUPPORTED LANGUAGE
    # --------------------------------------------------------

    def test_unsupported_language_rejected(self):
        """Reject languages that are not supported."""

        request_data = self.valid_request.copy()

        request_data["language"] = "java"

        with self.assertRaises(ValidationError):

            CodeExecutionRequest(
                **request_data
            )

    # --------------------------------------------------------
    # TEST 4: EMPTY SOURCE CODE
    # --------------------------------------------------------

    def test_empty_source_rejected(self):
        """Reject empty or whitespace-only source code."""

        invalid_sources = [
            "",
            " ",
            "\n\t",
        ]

        for source in invalid_sources:

            with self.subTest(source=source):

                request_data = self.valid_request.copy()

                request_data["source"] = source

                with self.assertRaises(ValidationError):

                    CodeExecutionRequest(
                        **request_data
                    )

    # --------------------------------------------------------
    # TEST 5: SOURCE CODE SIZE LIMIT
    # --------------------------------------------------------

    def test_oversized_source_rejected(self):
        """Reject source code larger than 256 KiB."""

        request_data = self.valid_request.copy()

        # Create source code larger than the allowed limit.
        request_data["source"] = "x" * (256 * 1024 + 1)

        with self.assertRaises(ValidationError):

            CodeExecutionRequest(
                **request_data
            )

    # --------------------------------------------------------
    # TEST 6: INVALID IDENTIFIERS
    # --------------------------------------------------------

    def test_invalid_identifiers_rejected(self):
        """Reject zero, negative, and string identifiers."""

        identifier_fields = [
            "board_id",
            "developer_id",
            "group_id",
        ]

        invalid_values = [
            0,
            -1,
            "10",
            True,
        ]

        for field in identifier_fields:

            for value in invalid_values:

                with self.subTest(
                    field=field,
                    value=value,
                ):

                    request_data = self.valid_request.copy()

                    request_data[field] = value

                    with self.assertRaises(ValidationError):

                        CodeExecutionRequest(
                            **request_data
                        )

    # --------------------------------------------------------
    # TEST 7: EXTRA FIELDS
    # --------------------------------------------------------

    def test_extra_fields_rejected(self):
        """Reject unexpected request fields."""

        request_data = self.valid_request.copy()

        # A client must not add unauthorized fields.
        request_data["is_admin"] = True

        with self.assertRaises(ValidationError):

            CodeExecutionRequest(
                **request_data
            )

    # --------------------------------------------------------
    # TEST 8: MISSING REQUIRED FIELDS
    # --------------------------------------------------------

    def test_missing_required_fields_rejected(self):
        """Reject requests missing required information."""

        required_fields = [
            "board_id",
            "developer_id",
            "group_id",
            "language",
            "source",
        ]

        for field in required_fields:

            with self.subTest(field=field):

                request_data = self.valid_request.copy()

                # Remove one required field.
                del request_data[field]

                with self.assertRaises(ValidationError):

                    CodeExecutionRequest(
                        **request_data
                    )


# ============================================================
# 3. RUN TESTS
# ============================================================

if __name__ == "__main__":
    unittest.main()