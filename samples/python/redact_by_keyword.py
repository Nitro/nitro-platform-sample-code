#!/usr/bin/env python3
"""
🔍 KEYWORD-BASED REDACTION
===========================

The script exemplifies a typical workflow for targeted content redaction.
As a compliance officer, you need to redact specific
sensitive terms from documents before external sharing or public disclosure.
Whether removing client names, project codenames, financial figures, or
proprietary terminology, manually searching through pages and applying redactions
is tedious and risks missing instances, potentially exposing confidential information.

This workflow automates keyword-based redaction. The script searches the entire
PDF document for all specified keywords and phrases, identifies their exact
locations across all pages, then automatically applies permanent redactions to
remove them. Multiple keywords can be processed in a single pass, ensuring
comprehensive coverage. The result is a thoroughly redacted document ready for
safe distribution.

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

import sys
from pathlib import Path

from api.platform_api import PlatformAPIClient


def main() -> None:
    # Check command-line arguments
    if len(sys.argv) < 4:
        print(
            "Usage: python redact_by_keyword.py <input_pdf> <output_pdf> <keyword1> [keyword2 ...]"
        )
        print(
            "Example: python redact_by_keyword.py document.pdf redacted.pdf 'confidential' 'secret'"
        )
        sys.exit(1)

    # Get file paths and keywords from arguments
    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    keywords = sys.argv[3:]

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
        # Step 1: Search for keywords in document
        print(f"🔍 Searching for {len(keywords)} keyword(s) in {input_path.name}...")
        print(f"   Keywords: {', '.join(repr(k) for k in keywords)}")

        bbox_data = client.find_text_boxes(input_path, keywords)

        # Extract text box locations from response
        text_boxes = bbox_data.get("result", {}).get("textBoxes", [])

        if not text_boxes:
            print("ℹ️  No keyword matches found - copying original file")  # noqa: RUF001
            # Copy original file to output if no keywords found
            output_path.write_bytes(input_path.read_bytes())
            print(f"✅ Saved: {output_path.name}")
            print(f"📂 Output: {output_path.absolute()}")
            return

        print(f"🎯 Found {len(text_boxes)} keyword instance(s) to redact")

        # Step 2: Prepare redaction coordinates
        print("🔒 Applying redactions...")
        redactions = [
            {"pageIndex": box["pageIndex"], "boundingBox": box["boundingBox"]} for box in text_boxes
        ]

        # Step 3: Apply redactions to document
        redacted_pdf = client.redact(input_path, redactions)

        # Save redacted PDF
        output_path.write_bytes(redacted_pdf)

        # Display success message
        print("✅ Redaction successful!")
        print(f"🔒 Redacted: {len(text_boxes)} instance(s)")
        print(f"📄 Input:  {input_path.name}")
        print(f"📄 Output: {output_path.name}")
        print(f"📂 Saved to: {output_path.absolute()}")

    except Exception as e:  # noqa: BLE001
        print(f"❌ Redaction FAILED: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
