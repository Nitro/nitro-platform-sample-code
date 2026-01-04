#!/usr/bin/env python3
"""
📁 BATCH DOCUMENT CONVERSION
=============================

The script exemplifies a typical workflow for document format standardization.
As a IT administrator, it's essential to convert
large collections of documents into standardized formats for archival, compliance,
or system integration purposes. Manually converting individual files through desktop
applications is time-consuming and impractical for large document sets, often leading
to inconsistent results and wasted effort.

This workflow automates bulk document conversion. The script processes files
individually - for every document matching the specified pattern in the input folder,
it converts the file to the target format (PDF, DOCX, XLSX, PNG, JPG, etc.) using
high-fidelity conversion algorithms. Each converted file is saved to the output
folder with the same base name but the new format extension, resulting in a
complete batch of standardized documents.

BATCH CONVERSION FEATURES:
  ✓ Multiple format support (PDF, DOCX, XLSX, PNG, JPG, etc.)
  ✓ Flexible file pattern matching (*.docx, *.xlsx, *.pptx, *.pdf.)

USAGE:
  python batch_process.py <input_folder> <output_folder> <format> [pattern]

EXAMPLES:
  python batch_process.py ../../test_files/test-batch ./output pdf "*.docx"
  python batch_process.py ./documents ./converted png "*"
"""

from pathlib import Path
from typing import Annotated

import typer

from api.platform_api import PlatformAPIClient
from helper_functions.document_helpers import validate_and_setup

# Supported output formats
SUPPORTED_FORMATS = ["pdf", "docx", "xlsx", "pptx"]

app = typer.Typer()


@app.command()
def main(
    input_folder: Annotated[
        Path, typer.Argument(help="Input folder containing documents to convert")
    ],
    output_folder: Annotated[Path, typer.Argument(help="Output folder for converted documents")],
    to_format: Annotated[
        str,
        typer.Argument(
            help=f"Target format for conversion. Supported: {', '.join(SUPPORTED_FORMATS)}"
        ),
    ],
    pattern: Annotated[
        str,
        typer.Argument(help="File pattern to match (e.g., '*.docx', '*.pdf', '*')"),
    ] = "*",
) -> None:
    """Process multiple documents in batch, converting them to a specified format."""
    # Validate output format
    to_format_lower = to_format.lower()
    if to_format_lower not in SUPPORTED_FORMATS:
        typer.echo(f"❌ Error: Unsupported format '{to_format}'")
        typer.echo(f"Supported formats: {', '.join(SUPPORTED_FORMATS)}")
        raise typer.Exit(code=1)

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
            typer.echo(f"  🔄 Converting to {to_format_lower.upper()}...")
            converted = client.convert(file_path, to_format_lower)

            # Save converted file
            output_file = output_folder / f"{file_path.stem}.{to_format_lower}"
            output_file.write_bytes(converted)

            typer.echo(f"  ✅ Converted: {output_file.name}\n")
            success_count += 1

        except Exception as e:  # noqa: BLE001  # pylint: disable=broad-exception-caught
            typer.echo(f"  ❌ FAILED: {e}\n")
            failed_count += 1

    # Display summary
    typer.echo("=" * 60)
    typer.echo(f"✅ {success_count} file(s) converted to {to_format_lower.upper()}")
    if failed_count > 0:
        typer.echo(f"⚠️  {failed_count} file(s) FAILED to convert!")
    typer.echo(f"📂 Output: {output_folder.absolute()}")
    typer.echo("=" * 60)


if __name__ == "__main__":
    app()
