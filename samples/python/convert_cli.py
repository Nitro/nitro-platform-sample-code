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

import sys
from pathlib import Path

from api.platform_api import PlatformAPIClient

# Supported output formats
SUPPORTED_FORMATS = ["pdf", "docx", "xlsx", "pptx", "png"]


def main() -> None:
    """Convert a document from one format to another using the Platform API."""
    # Check command-line arguments
    if len(sys.argv) != 4:
        print("Usage: python convert_cli.py <input_file> <output_file> <format>")
        print(f"Supported formats: {', '.join(SUPPORTED_FORMATS)}")
        print("Example: python convert_cli.py document.docx document.pdf pdf")
        sys.exit(1)

    # Get file paths and format from arguments
    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    to_format = sys.argv[3].lower()

    # Validate input file exists
    if not input_path.exists():
        print(f"❌ Error: Input file not found: {input_path}")
        sys.exit(1)

    # Validate output format
    if to_format not in SUPPORTED_FORMATS:
        print(f"❌ Error: Unsupported format '{to_format}'")
        print(f"Supported formats: {', '.join(SUPPORTED_FORMATS)}")
        sys.exit(1)

    # Create output directory if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Initialize API client (loads credentials from .env)
    client = PlatformAPIClient()

    try:
        # Convert document
        print(f"🔄 Converting {input_path.name} to {to_format.upper()}...")
        converted = client.convert(input_path, to_format)

        # Save converted file
        output_path.write_bytes(converted)

        # Display success message
        print("✅ Conversion successful!")
        print(f"📄 Input:  {input_path.name} ({input_path.stat().st_size:,} bytes)")
        print(f"📄 Output: {output_path.name} ({len(converted):,} bytes)")
        print(f"📂 Saved to: {output_path.absolute()}")

    except Exception as e:  # noqa: BLE001
        print(f"❌ Conversion FAILED: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
