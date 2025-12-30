#!/usr/bin/env python3
"""
🔒 PREPARE PDF FOR DISTRIBUTION
================================

The script exemplifies a typical workflow of marketing brochure distribution.
As a marketing professional, it's necessary to share company brochures externally
while ensuring they comply with corporate distribution standards. Word document
properties can expose internal information such as author names, template paths,
revision history, and company file structures that should remain confidential.

This workflow automates compliant document preparation. The script processes each
file individually - for every brochure in the input folder, it converts the Word
document into PDF format, then compresses the file to reduce size and optimize
transmission, and finally removes all metadata properties to ensure privacy and
confidentiality. Each processed file is saved to the output folder, resulting in
distribution-ready brochures.

COMPANY DISTRIBUTION STANDARDS:
  ✓ PDF format (prevents editing)
  ✓ Compressed (optimized file size)
  ✓ Properties removed (no metadata exposure)
  ⏳ Annotations removed (feature in development)
  ⏳ Accessibility enabled (feature in development)

USAGE:
  python prepare_pdf_for_distribution.py <input_folder> <output_folder>

EXAMPLE:
  python prepare_pdf_for_distribution.py ../../test_files/test-batch ./output
"""

import sys
from pathlib import Path

from api.platform_api import PlatformAPIClient
from helper_functions.document_helpers import validate_and_setup

# Configuration: Properties to remove from PDFs
PROPERTIES_TO_REMOVE = ["title", "author", "subject", "keywords", "creator", "producer"]


def main() -> None:
    """Prepare documents for distribution by converting to PDF and removing metadata."""
    # Check command-line arguments
    if len(sys.argv) != 3:
        print("Usage: python prepare_pdf_for_distribution.py <input_folder> <output_folder>")
        sys.exit(1)

    # Get folder paths from arguments
    input_folder = Path(sys.argv[1])
    output_folder = Path(sys.argv[2])

    # Validate and setup
    files = validate_and_setup(input_folder, output_folder)
    print(f"📋 Found {len(files)} document(s) to process\n")

    # Initialize API client (loads credentials from .env)
    client = PlatformAPIClient()

    # Process each document
    success_count = 0
    failed_count = 0

    for i, doc in enumerate(files, 1):
        print(f"[{i}/{len(files)}] Processing: {doc.name}")

        temp_pdf = None
        try:
            # Step 1: Convert to PDF
            print("  🔐 Converting to PDF...")
            pdf_bytes = client.convert(doc, "pdf")

            temp_pdf = output_folder / f"{doc.stem}_temp.pdf"
            temp_pdf.write_bytes(pdf_bytes)

            # Step 2: Compress PDF
            print("  📦 Compressing...")
            compressed_pdf = client.compress(temp_pdf, level=2)

            temp_pdf.write_bytes(compressed_pdf)

            # Step 3: Remove metadata properties
            print("  🔒 Removing metadata...")
            properties_to_clear = dict.fromkeys(PROPERTIES_TO_REMOVE, "")
            clean_pdf = client.set_properties(temp_pdf, properties_to_clear)

            # Save final PDF
            final_pdf = output_folder / f"{doc.stem}.pdf"
            final_pdf.write_bytes(clean_pdf)
            temp_pdf.unlink()

            print(f"  ✅ Secured: {final_pdf.name}\n")
            success_count += 1

        except Exception as e:  # noqa: BLE001
            print(f"  ❌ FAILED: {e}\n")
            failed_count += 1
            if temp_pdf and temp_pdf.exists():
                temp_pdf.unlink()

    # Display summary
    print("=" * 60)
    print(f"✅ {success_count} document(s) secured")
    if failed_count > 0:
        print(f"⚠️  {failed_count} document(s) FAILED - do NOT distribute!")
    print(f"📂 Output: {output_folder.absolute()}")
    print("=" * 60)


if __name__ == "__main__":
    main()
