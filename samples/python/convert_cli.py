#!/usr/bin/env python3
"""
🔄 SINGLE DOCUMENT CONVERSION
==============================

The script exemplifies a typical workflow for quick document format conversion.
As a business professional, you often need to convert individual
documents between formats for sharing, presentations, or compatibility requirements.
Whether converting a Word document to PDF for distribution, an Excel spreadsheet to
CSV for data processing, or a presentation to images for web display, manual
conversion through multiple applications is inefficient.

This workflow provides instant document conversion. The script takes a single input
file and converts it to the specified output format using professional-grade
conversion algorithms. The result is a high-quality converted file that preserves
formatting, structure, and content fidelity, ready for immediate use.

CONVERSION FEATURES:
  ✓ Multiple format support (PDF, DOCX, XLSX, PNG, etc.)
  ✓ High-fidelity conversion (preserves formatting)

USAGE:
  python convert_cli.py <input_file> <output_file> <format>

EXAMPLES:
  python convert_cli.py document.docx document.pdf pdf
  python convert_cli.py presentation.pptx slide.pdf pdf
  python convert_cli.py spreadsheet.xlsx data.pdf pdf
"""

from enum import Enum
from pathlib import Path
from typing import Annotated

import typer

from api.platform_api import PlatformAPIClient

class OutputFormat(str, Enum):
    """Supported output formats for document conversion."""

    PDF = "pdf"
    DOCX = "docx"
    XLSX = "xlsx"
    PPTX = "pptx"
    PNG = "png"


app = typer.Typer()


@app.command()
def main(
    input_file: Annotated[Path, typer.Argument(help='Input file to convert')],
    output_file: Annotated[Path, typer.Argument(help='Output file path')],
    to_format: Annotated[
        OutputFormat,
        typer.Argument(help="Target format for conversion"),
    ],
) -> None:
    """Convert a document from one format to another using the Platform API."""
    # Validate input file exists
    if not input_file.exists():
        print(f'❌ Error: Input file not found: {input_file}')
        raise typer.Exit(code=1)

    # Create output directory if needed
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Initialize API client (loads credentials from .env)
    client = PlatformAPIClient()

    try:
        # Convert document
        print(f'🔄 Converting {input_file.name} to {to_format.value.upper()}...')
        converted = client.convert(input_file, to_format.value)

        # Save converted file
        output_file.write_bytes(converted)

        # Display success message
        print('✅ Conversion successful!')
        print(f'📄 Input:  {input_file.name} ({input_file.stat().st_size:,} bytes)')
        print(f'📄 Output: {output_file.name} ({len(converted):,} bytes)')
        print(f'📂 Saved to: {output_file.absolute()}')

    except Exception as e:  # noqa: BLE001
        print(f'❌ Conversion FAILED: {e}')
        raise typer.Exit(code=1) from None


if __name__ == '__main__':
    app()
