#!/usr/bin/env python3
"""
🔄 SINGLE DOCUMENT CONVERSION
==============================

This script demonstrates a simple and efficient way to convert documents between formats.

In daily work, you may need to convert individual files for sharing,
presenting, or ensuring compatibility with different systems. For example,
you might convert a Word document to a PDF for easy distribution, an Excel
spreadsheet to a CSV file for data processing, or a presentation into images
for use on a website. Doing this manually across multiple applications can be
time-consuming and inconvenient.

This workflow simplifies the process by providing instant document
conversion. You supply a single input file and choose the desired output
format. The script handles the conversion automatically using high-quality
conversion methods.

The resulting file maintains the original layout, structure, and content
accuracy, so it is ready to use right away.

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

from api import FatalError
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
        raise FatalError(f'Input file not found: {input_file}')

    # Create output directory if needed
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Initialize API client (loads credentials from .env)
    with PlatformAPIClient.build() as client:
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
            raise FatalError(f'Conversion FAILED: {e}') from None


if __name__ == '__main__':
    app()
