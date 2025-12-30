"""
Common helper utilities for document processing scripts.
"""

from __future__ import annotations

import sys
from pathlib import Path  # noqa: TC003


def validate_and_setup(
    input_folder: Path, output_folder: Path, file_patterns: list[str] | None = None
) -> list[Path]:
    """
    Validate input folder and setup output folder. Returns list of files to process.

    Args:
        input_folder: Path to the input directory containing files to process
        output_folder: Path to the output directory for processed files
        file_patterns: List of glob patterns to match files (e.g., ['*.docx', '*.pdf'])
                      If None, defaults to common Office document formats

    Returns:
        List of Path objects for files matching the patterns
    """
    # Default patterns for Office documents if none provided
    if file_patterns is None:
        file_patterns = ["*.docx", "*.doc", "*.xlsx", "*.xls", "*.pptx", "*.ppt"]

    # Validate input folder exists
    if not input_folder.exists() or not input_folder.is_dir():
        print(f"❌ Error: Invalid input folder: {input_folder}")
        sys.exit(1)

    # Create output folder if needed
    output_folder.mkdir(parents=True, exist_ok=True)

    # Find all matching files
    files: list[Path] = []
    for pattern in file_patterns:
        files.extend(input_folder.glob(pattern))

    if not files:
        print(f"❌ No files matching patterns {file_patterns} found in {input_folder}")
        sys.exit(1)

    return files
