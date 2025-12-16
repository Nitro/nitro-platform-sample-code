#!/usr/bin/env python3
"""
📁 BATCH DOCUMENT CONVERSION
=============================

The script exemplifies a typical workflow for document format standardization.
As a IT administrator, it's essential to convert 
large collections of documents into standardized formats for archival, compliance, 
or system integration purposes. Manually converting individual files through desktop 
applications is time-consuming and impractical for large document sets, often leading 
to inconsistent results and wasted effort.

This workflow automates bulk document conversion. The script processes files 
individually - for every document matching the specified pattern in the input folder, 
it converts the file to the target format (PDF, DOCX, XLSX, PNG, JPG, etc.) using 
high-fidelity conversion algorithms. Each converted file is saved to the output 
folder with the same base name but the new format extension, resulting in a 
complete batch of standardized documents.

BATCH CONVERSION FEATURES:
  ✓ Multiple format support (PDF, DOCX, XLSX, PNG, JPG, etc.)
  ✓ Flexible file pattern matching (*.docx, *.xlsx, *.pptx, *.pdf.)

USAGE:
  python batch_process.py <input_folder> <output_folder> <format> [pattern]

EXAMPLES:
  python batch_process.py ../../test_files/test-batch ./output pdf "*.docx"
  python batch_process.py ./documents ./converted png "*"
"""

import sys
from pathlib import Path
from api.platform_api import PlatformAPIClient
from helper_functions.document_helpers import validate_and_setup


# Supported output formats
SUPPORTED_FORMATS = ['pdf', 'docx', 'xlsx', 'pptx']


def main():
    # Check command-line arguments
    if len(sys.argv) < 4:
        print("Usage: python batch_process.py <input_folder> <output_folder> <format> [pattern]")
        print(f"Supported formats: {', '.join(SUPPORTED_FORMATS)}")
        print("Example: python batch_process.py ./docs ./output pdf '*.docx'")
        sys.exit(1)
    
    # Get folder paths and format from arguments
    input_folder = Path(sys.argv[1])
    output_folder = Path(sys.argv[2])
    to_format = sys.argv[3].lower()
    pattern = sys.argv[4] if len(sys.argv) > 4 else "*"
    
    # Validate output format
    if to_format not in SUPPORTED_FORMATS:
        print(f"❌ Error: Unsupported format '{to_format}'")
        print(f"Supported formats: {', '.join(SUPPORTED_FORMATS)}")
        sys.exit(1)
    
    # Validate and setup with custom pattern
    files = validate_and_setup(input_folder, output_folder, file_patterns=[pattern])
    print(f"📋 Found {len(files)} file(s) matching '{pattern}'\n")
    
    # Initialize API client (loads credentials from .env)
    client = PlatformAPIClient()
    
    # Process each document
    success_count = 0
    failed_count = 0
    
    for i, file_path in enumerate(files, 1):
        print(f"[{i}/{len(files)}] Processing: {file_path.name}")
        
        try:
            # Convert to target format
            print(f"  🔄 Converting to {to_format.upper()}...")
            converted = client.convert(file_path, to_format)
            
            # Save converted file
            output_file = output_folder / f"{file_path.stem}.{to_format}"
            output_file.write_bytes(converted)
            
            print(f"  ✅ Converted: {output_file.name}\n")
            success_count += 1
            
        except Exception as e:
            print(f"  ❌ FAILED: {e}\n")
            failed_count += 1
    
    # Display summary
    print("=" * 60)
    print(f"✅ {success_count} file(s) converted to {to_format.upper()}")
    if failed_count > 0:
        print(f"⚠️  {failed_count} file(s) FAILED to convert!")
    print(f"📂 Output: {output_folder.absolute()}")
    print("=" * 60)


if __name__ == "__main__":
    main()
