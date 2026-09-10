#!/usr/bin/env python3
"""
📊 DOCUMENT DATA EXTRACTION
============================

This script shows how to automatically extract useful data from PDF documents.

If you work with PDFs, you often need to pull structured information from
them. This might include form fields from applications, surveys, or
questionnaires, as well as table data from reports, invoices, or financial
statements. Entering this information by hand can be slow and can lead to
mistakes, especially when you are processing a large number of documents.

This workflow makes the process faster and easier by automating data
extraction. The script analyzes PDF files and uses intelligent document
analysis to find and extract the information you need. It can capture form
fields with their names and values, or detect tables and extract their rows,
columns, and cell contents.

The extracted data is saved in a structured JSON format. This makes it
easy to load into databases, spreadsheets, or analytics tools so you can
start working with the data right away.

DATA EXTRACTION FEATURES:
  ✓ AI-powered form field extraction
  ✓ Intelligent table detection and extraction
  ✓ Structured JSON output format
  ✓ High accuracy recognition

USAGE:
  python extract_data.py <mode> <input_pdf> <output_json>

MODES:
  forms  - Extract form fields (name-value pairs)
  tables - Extract table data (rows and columns)

EXAMPLES:
  python extract_data.py forms application.pdf data.json
  python extract_data.py tables "../../test_files/test-pdfs/Sample Tables.pdf" tables.json
"""

import json
from pathlib import Path
from typing import Annotated

import typer

from api import FatalError
from api.platform_api import PlatformAPIClient

app = typer.Typer()


@app.command()
def main(
    mode: Annotated[str, typer.Argument(help="Extraction mode: 'forms' or 'tables'")],
    input_pdf: Annotated[Path, typer.Argument(help='Input PDF file')],
    output_json: Annotated[Path, typer.Argument(help='Output JSON file')],
) -> None:
    """Extract structured data (forms or tables) from PDF documents."""
    # Normalize mode to lowercase
    mode = mode.lower()

    # Validate mode
    if mode not in ['forms', 'tables']:
        raise FatalError("Mode must be 'forms' or 'tables'")

    # Validate input file exists
    if not input_pdf.exists():
        raise FatalError(f'Input file not found: {input_pdf}')

    # Validate input is a PDF
    if input_pdf.suffix.lower() != '.pdf':
        raise FatalError('Input must be a PDF file')

    # Create output directory if needed
    output_json.parent.mkdir(parents=True, exist_ok=True)

    # Initialize API client (loads credentials from .env)
    with PlatformAPIClient.build() as client:
        try:
            # Extract data based on mode
            if mode == 'forms':
                print(f'📋 Extracting form fields from {input_pdf.name}...')
                data = client.extract_forms(input_pdf)
                data_type = 'form fields'

            else:  # mode == 'tables'
                print(f'📊 Extracting table data from {input_pdf.name}...')
                data = client.extract_tables(input_pdf)
                data_type = 'tables'

            # Count extracted items
            result = data.get('result', {})
            if mode == 'forms':
                item_count = len(result.get('fields', []))
            else:
                item_count = len(result.get('tables', []))

            # Save extracted data as JSON
            output_json.write_text(json.dumps(data, indent=2), encoding='utf-8')

            # Display success message
            print('✅ Extraction successful!')
            print(f'📊 Extracted: {item_count} {data_type}')
            print(f'📄 Input:  {input_pdf.name}')
            print(f'📄 Output: {output_json.name}')
            print(f'📂 Saved to: {output_json.absolute()}')

        except Exception as e:  # noqa: BLE001
            raise FatalError(f'Extraction FAILED: {e}') from None


if __name__ == '__main__':
    app()
