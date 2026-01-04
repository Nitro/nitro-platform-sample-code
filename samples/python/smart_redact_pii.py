#!/usr/bin/env python3
"""
🔒 SMART PII REDACTION
======================

The script exemplifies a typical workflow for protecting sensitive customer information.
As a compliance officer, it's essential to review and redact
personally identifiable information (PII) from documents before sharing them with
third parties, storing them in public systems, or using them for analysis. Manual
redaction is time-consuming and error-prone, potentially missing sensitive data like
social security numbers, phone numbers, addresses, or email addresses.

This workflow automates compliant document redaction. The script processes each PDF
file individually - for every document in the input folder, it uses AI-powered PII
detection to identify all instances of sensitive information across all pages, then
automatically applies redactions to permanently remove this data. Each processed file
is saved to the output folder with all PII securely redacted, ready for safe sharing
or archival.

PRIVACY COMPLIANCE STANDARDS:
  ✓ AI-powered PII detection (SSN, phone, email, address)
  ✓ Automatic redaction (permanent removal)
  ✓ Batch processing (entire folders)

USAGE:
  python smart_redact_pii.py <input_folder> <output_folder>

EXAMPLE:
  python smart_redact_pii.py ../../test_files/test-pdfs ./output
"""

from pathlib import Path
from typing import Annotated

import typer

from api.platform_api import PlatformAPIClient
from helper_functions.document_helpers import validate_and_setup

app = typer.Typer()


@app.command()
def main(
    input_folder: Annotated[Path, typer.Argument(help='Input folder containing PDF documents')],
    output_folder: Annotated[Path, typer.Argument(help='Output folder for redacted PDFs')],
) -> None:
    """Automatically detect and redact PII (personally identifiable information) from PDFs."""

    # Validate and setup (only process PDF files)
    files = validate_and_setup(input_folder, output_folder, file_patterns=["*.pdf"])
    print(f"📋 Found {len(files)} PDF document(s) to process")

    # Initialize API client
    client = PlatformAPIClient()

    # Process each document
    success_count = 0
    failed_count = 0
    total_pii_count = 0

    for i, pdf_file in enumerate(files, 1):
        print(f"[{i}/{len(files)}] Processing: {pdf_file.name}")

        try:
            # Step 1: Detect PII in the document
            print("  🔍 Detecting PII...")
            pii_data = client.detect_pii(pdf_file)

            # Extract PII bounding boxes from response
            pii_boxes = pii_data.get("result", {}).get("PIIBoxes", [])

            if not pii_boxes:
                print("  ℹ️  No PII detected - copying original file")  # noqa: RUF001

                # Copy original file to output if no PII found
                output_file = output_folder / pdf_file.name
                output_file.write_bytes(pdf_file.read_bytes())

                print(f"  ✅ Saved: {output_file.name}")

                success_count += 1
                continue

            print(f"  🎯 Found {len(pii_boxes)} PII instance(s)")
            total_pii_count += len(pii_boxes)

            # Step 2: Prepare redaction coordinates
            print("  🔒 Applying redactions...")
            redactions = [
                {"pageIndex": box["pageIndex"], "boundingBox": box["boundingBox"]}
                for box in pii_boxes
            ]

            # Step 3: Apply redactions to document
            redacted_pdf = client.redact(pdf_file, redactions)

            # Save redacted PDF
            output_file = output_folder / pdf_file.name
            output_file.write_bytes(redacted_pdf)

            print(f"  ✅ Redacted: {output_file.name}")
            success_count += 1

        except Exception as e:  # noqa: BLE001
            print(f"  ❌ FAILED: {e}")
            failed_count += 1

    # Display summary
    print("=" * 60)
    print(f"✅ {success_count} document(s) processed")
    print(f"🔒 {total_pii_count} total PII instance(s) redacted")
    if failed_count > 0:
        print(f"⚠️  {failed_count} document(s) FAILED - review manually!")
    print(f"📂 Output: {output_folder.absolute()}")
    print("=" * 60)


if __name__ == '__main__':
    app()
