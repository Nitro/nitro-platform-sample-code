#!/usr/bin/env python3
"""
🔐 BULK PASSWORD PROTECTION
============================

This script shows a standard workflow to protect confidential documents.

Security staff must protect sensitive documents with passwords before they
share them with authorized users, save them in shared drives, or store them
for compliance. Manually adding passwords to individual files takes a lot of
time and can cause errors. This can result in weak passwords or files that are
not protected. This workflow automates document protection.

The script processes one PDF file at a time. For each PDF file in the input folder, the script:

Applies password encryption

Uses the same password for all files

Saves the protected file to the output folder with the same file
name

This process ensures that all documents follow the same security standard.
The result is a set of password-protected PDF files ready for secure
sharing or storage.

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
