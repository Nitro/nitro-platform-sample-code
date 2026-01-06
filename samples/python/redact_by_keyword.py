#!/usr/bin/env python3
"""
🔍 KEYWORD-BASED REDACTION
===========================

This script shows a standard workflow for targeted content redaction.

As a compliance officer, you must remove sensitive information from
documents before you share them outside the organization or release them to
the public. This information can include client names, project code names,
financial values, or proprietary terms. Finding and removing this content
by hand can be slow and difficult. You can also miss some instances, which
can expose confidential information.

This workflow automates keyword-based redaction. The script searches the
full PDF document for all specified keywords and phrases. It finds each
instance on every page. The script then applies permanent redactions to
remove the content.

You can process multiple keywords in one run that ensures full and
consistent coverage. The result is a clean, redacted document that is safe
to share.

KEYWORD REDACTION FEATURES:
  ✓ Multi-keyword search (process multiple terms)
  ✓ Whole document scanning (all pages)
  ✓ Exact location detection
  ✓ Permanent redaction (unrecoverable)
  ⏳ Case-insensitive matching (feature in development)
  ⏳ Regex pattern support (feature in development)

USAGE:
  python redact_by_keyword.py <input_pdf> <output_pdf> <keyword1> [keyword2 ...]

EXAMPLES:
  python redact_by_keyword.py contract.pdf redacted.pdf "confidential" "proprietary"
  python redact_by_keyword.py report.pdf clean.pdf "Project Zeus" "Client ABC"
"""

from pathlib import Path
from typing import Annotated

import typer

from api.platform_api import PlatformAPIClient

app = typer.Typer()


@app.command()
def main(
    input_pdf: Annotated[Path, typer.Argument(help='Input PDF file to redact')],
    output_pdf: Annotated[Path, typer.Argument(help='Output PDF file with redactions')],
    keywords: Annotated[list[str], typer.Argument(help='Keywords to search for and redact')],
) -> None:
    """Redact specific keywords from PDF documents using text search."""
    # Validate input file exists
    if not input_pdf.exists():
        print(f'❌ Error: Input file not found: {input_pdf}')
        raise typer.Exit(code=1)

    # Validate input is a PDF
    if input_pdf.suffix.lower() != '.pdf':
        print('❌ Error: Input must be a PDF file')
        raise typer.Exit(code=1)

    # Create output directory if needed
    output_pdf.parent.mkdir(parents=True, exist_ok=True)

    # Initialize API client (loads credentials from .env)
    client = PlatformAPIClient()

    try:
        # Step 1: Search for keywords in document
        print(f'🔍 Searching for {len(keywords)} keyword(s) in {input_pdf.name}...')
        print(f"   Keywords: {', '.join(repr(k) for k in keywords)}")

        bbox_data = client.find_text_boxes(input_pdf, keywords)

        # Extract text box locations from response
        text_boxes = bbox_data.get('result', {}).get('textBoxes', [])

        if not text_boxes:
            print('ℹ️  No keyword matches found - copying original file')  # noqa: RUF001
            # Copy original file to output if no keywords found
            output_pdf.write_bytes(input_pdf.read_bytes())
            print(f'✅ Saved: {output_pdf.name}')
            print(f'📂 Output: {output_pdf.absolute()}')
            return

        print(f'🎯 Found {len(text_boxes)} keyword instance(s) to redact')

        # Step 2: Prepare redaction coordinates
        print("🔒 Applying redactions...")
        redactions = [
            {"pageIndex": box["pageIndex"], "boundingBox": box["boundingBox"]} for box in text_boxes
        ]

        # Step 3: Apply redactions to document
        redacted_pdf = client.redact(input_pdf, redactions)

        # Save redacted PDF
        output_pdf.write_bytes(redacted_pdf)

        # Display success message
        print('✅ Redaction successful!')
        print(f'🔒 Redacted: {len(text_boxes)} instance(s)')
        print(f'📄 Input:  {input_pdf.name}')
        print(f'📄 Output: {output_pdf.name}')
        print(f'📂 Saved to: {output_pdf.absolute()}')

    except Exception as e:  # noqa: BLE001
        print(f'❌ Redaction FAILED: {e}')
        raise typer.Exit(code=1) from None


if __name__ == '__main__':
    app()
