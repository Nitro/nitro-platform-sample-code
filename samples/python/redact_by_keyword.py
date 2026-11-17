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
  ✓ Case-sensitive literal matching (the API also supports regular
    expressions and case-insensitive matching via isRegex/regexFlags)

USAGE:
  python redact_by_keyword.py <input_pdf> <output_pdf> <keyword1> [keyword2 ...]

EXAMPLES:
  python redact_by_keyword.py contract.pdf redacted.pdf "confidential" "proprietary"
  python redact_by_keyword.py report.pdf clean.pdf "Project Zeus" "Client ABC"
"""

from pathlib import Path
from typing import Annotated, Any

import typer

from api import FatalError
from api.platform_api import PlatformAPIClient

app = typer.Typer()


def search_result_to_redactions(search_response: dict[str, Any]) -> list[dict[str, Any]]:
    """Collect the boxes of a text-bounding-boxes result into Redact's `redactions`.

    Boxes are nested as textBoxes[].matches[].boxes[] (one entry per query, then one
    per match, then one box per line of the match). `groups` is ignored: its boxes
    cover parts of the match. Identical boxes, which only occur when two keywords
    match the same text, are sent once.
    """
    search_result = search_response.get('result', search_response)
    seen: set[tuple[int, tuple[float, ...]]] = set()
    redactions: list[dict[str, Any]] = []
    for query_result in search_result['textBoxes']:
        for match in query_result['matches']:
            for box in match['boxes']:
                key = (box['pageIndex'], tuple(box['boundingBox']))
                if key in seen:
                    continue
                seen.add(key)
                redactions.append(
                    {'pageIndex': box['pageIndex'], 'boundingBox': box['boundingBox']}
                )
    return redactions


@app.command()
def main(
    input_pdf: Annotated[Path, typer.Argument(help='Input PDF file to redact')],
    output_pdf: Annotated[Path, typer.Argument(help='Output PDF file with redactions')],
    keywords: Annotated[list[str], typer.Argument(help='Keywords to search for and redact')],
) -> None:
    """Redact specific keywords from PDF documents using text search."""
    # Validate input file exists
    if not input_pdf.exists():
        raise FatalError(f'Input file not found: {input_pdf}')

    # Validate input is a PDF
    if input_pdf.suffix.lower() != '.pdf':
        raise FatalError('Input must be a PDF file')

    # Create output directory if needed
    output_pdf.parent.mkdir(parents=True, exist_ok=True)

    # Initialize API client (loads credentials from .env)
    with PlatformAPIClient.build() as client:
        try:
            # Step 1: Search for keywords in document
            print(f'🔍 Searching for {len(keywords)} keyword(s) in {input_pdf.name}...')
            print(f"   Keywords: {', '.join(repr(k) for k in keywords)}")

            bbox_data = client.find_text_boxes(input_pdf, keywords)

            # Step 2: Collect the matches' boxes into redaction coordinates
            redactions = search_result_to_redactions(bbox_data)

            if not redactions:
                print('ℹ️  No keyword matches found - copying original file')  # noqa: RUF001
                # Copy original file to output if no keywords found
                output_pdf.write_bytes(input_pdf.read_bytes())
                print(f'✅ Saved: {output_pdf.name}')
                print(f'📂 Output: {output_pdf.absolute()}')
                return

            print(f'🎯 Found {len(redactions)} area(s) to redact')
            print('🔒 Applying redactions...')

            # Step 3: Apply redactions to document
            redacted_pdf = client.redact(input_pdf, redactions)

            # Save redacted PDF
            output_pdf.write_bytes(redacted_pdf)

            # Display success message
            print('✅ Redaction successful!')
            print(f'🔒 Redacted: {len(redactions)} area(s)')
            print(f'📄 Input:  {input_pdf.name}')
            print(f'📄 Output: {output_pdf.name}')
            print(f'📂 Saved to: {output_pdf.absolute()}')

        except Exception as e:  # noqa: BLE001
            raise FatalError(f'Redaction FAILED: {e}') from None


if __name__ == '__main__':
    app()
