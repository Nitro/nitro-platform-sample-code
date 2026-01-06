#!/usr/bin/env python3
"""
📁 BATCH DOCUMENT CONVERSION
=============================

This script shows a standard workflow for document format standardization.

As an IT administrator, you must convert many documents to standard
formats for archiving, compliance, or system integration. Manual conversion
with desktop applications takes a long time and is not practical for large
document sets. It can also cause inconsistent results and wasted effort.

This workflow automates bulk document conversion. The script scans the input
folder for files that match a specified pattern and processes each file one
by one. For each document, the script converts the file to the target format,
such as PDF, DOCX, XLSX, PNG, or JPG, using high-quality conversion methods.

Each converted file is saved in the output folder with the same base name and a new
format extension. The result is a complete set of standardized documents that are
ready for use.

BATCH CONVERSION FEATURES:
  ✓ Multiple format support (PDF, DOCX, XLSX, PNG, JPG, etc.)
  ✓ Flexible file pattern matching (*.docx, *.xlsx, *.pptx, *.pdf.)

USAGE:
  python batch_process.py <input_folder> <output_folder> <format> [pattern]

EXAMPLES:
  python batch_process.py ../../test_files/test-batch ./output pdf "*.docx"
  python batch_process.py ./documents ./converted png "*"
"""

from enum import Enum
from pathlib import Path
from typing import Annotated

import typer

from api.platform_api import PlatformAPIClient
from helper_functions.document_helpers import validate_and_setup


class OutputFormat(str, Enum):
    """Supported output formats for document conversion."""

    PDF = "pdf"
    DOCX = "docx"
    XLSX = "xlsx"
    PPTX = "pptx"

app = typer.Typer()


@app.command()
def main(
    input_folder: Annotated[
        Path, typer.Argument(help="Input folder containing documents to convert")
    ],
    output_folder: Annotated[Path, typer.Argument(help="Output folder for converted documents")],
    to_format: Annotated[
        OutputFormat,
        typer.Argument(help="Target format for conversion"),
    ],
    pattern: Annotated[
        str,
        typer.Argument(help="File pattern to match (e.g., '*.docx', '*.pdf', '*')"),
    ] = "*",
) -> None:
    """Process multiple documents in batch, converting them to a specified format."""
    # Validate and setup with custom pattern
    files = validate_and_setup(input_folder, output_folder, file_patterns=[pattern])
    typer.echo(f"📋 Found {len(files)} file(s) matching '{pattern}'\n")

    # Initialize API client (loads credentials from .env)
    client = PlatformAPIClient()

    # Process each document
    success_count = 0
    failed_count = 0

    for i, file_path in enumerate(files, 1):
        typer.echo(f"[{i}/{len(files)}] Processing: {file_path.name}")

        try:
            # Convert to target format
            typer.echo(f"  🔄 Converting to {to_format.value.upper()}...")
            converted = client.convert(file_path, to_format.value)

            # Save converted file
            output_file = output_folder / f"{file_path.stem}.{to_format.value}"
            output_file.write_bytes(converted)

            typer.echo(f"  ✅ Converted: {output_file.name}\n")
            success_count += 1

        except Exception as e:  # noqa: BLE001  # pylint: disable=broad-exception-caught
            typer.echo(f"  ❌ FAILED: {e}\n")
            failed_count += 1

    # Display summary
    typer.echo("=" * 60)
    typer.echo(f"✅ {success_count} file(s) converted to {to_format.value.upper()}")
    if failed_count > 0:
        typer.echo(f"⚠️  {failed_count} file(s) FAILED to convert!")
    typer.echo(f"📂 Output: {output_folder.absolute()}")
    typer.echo("=" * 60)


if __name__ == "__main__":
    app()
