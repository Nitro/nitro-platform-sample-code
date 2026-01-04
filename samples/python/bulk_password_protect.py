#!/usr/bin/env python3
"""
🔐 BULK PASSWORD PROTECTION
============================

The script exemplifies a typical workflow for securing confidential documents.
As a security professional, it's essential to protect sensitive
documents with passwords before distributing them to authorized personnel, storing
them in shared drives, or archiving them for compliance purposes. Manually setting
passwords on individual files is tedious and inconsistent, leading to weak passwords
or missed files that remain unprotected.

This workflow automates secure document protection. The script processes each PDF
file individually - for every document in the input folder, it applies robust
password encryption using a consistent password across all files. Each protected
file is saved to the output folder with the same filename, ensuring that the entire
batch of documents maintains uniform security standards. The result is a complete
set of password-protected PDFs ready for secure distribution or storage.

DOCUMENT SECURITY STANDARDS:
  ✓ Password encryption (AES-256)
  ✓ Batch processing (entire folders)
  ✓ Consistent security (uniform password policy)

USAGE:
  python bulk_password_protect.py <input_folder> <output_folder> <password>

EXAMPLE:
  python bulk_password_protect.py ../../test_files/test-pdfs ./output MySecureP@ss123
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
    output_folder: Annotated[Path, typer.Argument(help='Output folder for protected PDFs')],
    password: Annotated[str, typer.Argument(help='Password for protection (min 6 characters)')],
) -> None:
    """Apply password protection to all PDF files in a directory."""
    # Validate password strength
    if len(password) < 6:
        print('❌ Error: Password must be at least 6 characters long')
        raise typer.Exit(code=1)

    # Validate and setup (only process PDF files)
    files = validate_and_setup(input_folder, output_folder, file_patterns=["*.pdf"])
    print(f"📋 Found {len(files)} PDF document(s) to protect\n")

    # Initialize API client (loads credentials from .env)
    client = PlatformAPIClient()

    # Process each document
    success_count = 0
    failed_count = 0

    for i, pdf_file in enumerate(files, 1):
        print(f"[{i}/{len(files)}] Processing: {pdf_file.name}")

        try:
            # Apply password protection
            print("  🔐 Applying password protection...")
            protected_pdf = client.password_protect(pdf_file, password)

            # Save protected PDF
            output_file = output_folder / pdf_file.name
            output_file.write_bytes(protected_pdf)

            print(f"  ✅ Protected: {output_file.name}\n")
            success_count += 1

        except Exception as e:  # noqa: BLE001
            print(f"  ❌ FAILED: {e}\n")
            failed_count += 1

    # Display summary
    print("=" * 60)
    print(f"✅ {success_count} document(s) password protected")
    if failed_count > 0:
        print(f"⚠️  {failed_count} document(s) FAILED - remain unprotected!")
    print(f"📂 Output: {output_folder.absolute()}")
    print(f"🔑 Password: {'*' * len(password)} ({len(password)} characters)")
    print("=" * 60)


if __name__ == '__main__':
    app()
