"""Validate Code Board source code before isolated execution."""

from dataclasses import dataclass


# Supported languages and their required entry-point filenames.
LANGUAGE_FILES = {
    "python": "main.py",
    "go": "main.go",
    "javascript": "main.js",
}

# Maximum source-code size: 256 KiB.
MAX_CODE_BYTES = 256 * 1024


@dataclass(frozen=True)
class CodeSnapshot:
    """Represent validated source code ready for file preparation."""

    language: str
    filename: str
    source: str


def prepare_code_snapshot(language: str, source: str) -> CodeSnapshot:
    """Validate code and prepare its execution metadata."""

    # Reject unsupported languages.
    if language not in LANGUAGE_FILES:
        raise ValueError(
            "Code execution supports Python, Go, and JavaScript only."
        )

    # Source code must be text.
    if not isinstance(source, str):
        raise ValueError("Source code must be a string.")

    # Reject empty or whitespace-only programs.
    if not source.strip():
        raise ValueError("Source code cannot be empty.")

    # Check the actual UTF-8 size, not just character count.
    if len(source.encode("utf-8")) > MAX_CODE_BYTES:
        raise ValueError("Source code exceeds the maximum allowed size.")

    # Select a fixed filename instead of accepting a user-supplied path.
    filename = LANGUAGE_FILES[language]

    # Return validated execution data.
    return CodeSnapshot(
        language=language,
        filename=filename,
        source=source,
    )