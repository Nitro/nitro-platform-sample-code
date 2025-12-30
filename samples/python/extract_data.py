#!/usr/bin/env python3
"""
📊 DOCUMENT DATA EXTRACTION
============================

The script exemplifies a typical workflow for intelligent document data extraction.
As a data analyst, you need to extract structured
data from PDF documents - whether form fields from applications, surveys, and
questionnaires, or table data from reports, invoices, and financial statements.
Manual data entry is error-prone and time-consuming, especially when processing
hundreds of documents for analysis or database import.

This workflow automates data extraction using AI-powered document understanding.
The script analyzes PDF documents and intelligently identifies and extracts either
form fields (with field names and values) or table structures (with rows, columns,
and cell contents). The extracted data is saved as structured JSON, ready for
immediate integration with databases, spreadsheets, or analytics pipelines.

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
  python extract_data.py tables invoice.pdf tables.json
"""

import json
import sys
from pathlib import Path

from api.platform_api import PlatformAPIClient


def main() -> None:
    """Extract structured data (forms or tables) from PDF documents."""
    # Check command-line arguments
    if len(sys.argv) != 4:
        print("Usage: python extract_data.py <mode> <input_pdf> <output_json>")
        print("Modes: forms, tables")
        print("Example: python extract_data.py forms application.pdf data.json")
        sys.exit(1)

    # Get mode and file paths from arguments
    mode = sys.argv[1].lower()
    input_path = Path(sys.argv[2])
    output_path = Path(sys.argv[3])

    # Validate mode
    if mode not in ["forms", "tables"]:
        print("❌ Error: Mode must be 'forms' or 'tables'")
        sys.exit(1)

    # Validate input file exists
    if not input_path.exists():
        print(f"❌ Error: Input file not found: {input_path}")
        sys.exit(1)

    # Validate input is a PDF
    if input_path.suffix.lower() != ".pdf":
        print("❌ Error: Input must be a PDF file")
        sys.exit(1)

    # Create output directory if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Initialize API client (loads credentials from .env)
    client = PlatformAPIClient()

    try:
        # Extract data based on mode
        if mode == "forms":
            print(f"📋 Extracting form fields from {input_path.name}...")
            data = client.extract_forms(input_path)
            data_type = "form fields"

        else:  # mode == "tables"
            print(f"📊 Extracting table data from {input_path.name}...")
            data = client.extract_tables(input_path)
            data_type = "tables"

        # Count extracted items
        result = data.get("result", {})
        if mode == "forms":
            item_count = len(result.get("fields", []))
        else:
            item_count = len(result.get("tables", []))

        # Save extracted data as JSON
        output_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

        # Display success message
        print("✅ Extraction successful!")
        print(f"📊 Extracted: {item_count} {data_type}")
        print(f"📄 Input:  {input_path.name}")
        print(f"📄 Output: {output_path.name}")
        print(f"📂 Saved to: {output_path.absolute()}")

    except Exception as e:  # noqa: BLE001
        print(f"❌ Extraction FAILED: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
