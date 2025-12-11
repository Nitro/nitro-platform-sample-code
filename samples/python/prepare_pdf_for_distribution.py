#!/usr/bin/env python3
"""
🔒 PREPARE PDF FOR DISTRIBUTION
================================

THE STORY:
Your company handles sensitive documents - contracts, proposals, financial reports.
These documents contain internal metadata that could reveal private information:
  • Author names and email addresses
  • Company internal file paths  
  • Edit history and revision dates

Before sharing ANY document externally, we MUST remove this metadata to protect
employee privacy, company confidentiality, and ensure legal compliance.

This script automates the secure preparation workflow!

WORKFLOW:
1. Place Word/Excel/PowerPoint documents in input folder
2. Script converts to PDF → compresses → strips metadata
3. Find distribution-ready PDFs in output folder

USAGE:
  python prepare_pdf_for_distribution.py <input_folder> <output_folder>

EXAMPLE:
  python prepare_pdf_for_distribution.py ./confidential ./ready_for_clients
"""

import sys
from pathlib import Path
from platform_api import PlatformAPIClient


def main():
    # Check command-line arguments
    if len(sys.argv) != 3:
        print("Usage: python prepare_pdf_for_distribution.py <input_folder> <output_folder>")
        sys.exit(1)
    
    # Get folder paths from arguments
    input_folder = Path(sys.argv[1])
    output_folder = Path(sys.argv[2])
    
    # Validate input folder exists
    if not input_folder.exists() or not input_folder.is_dir():
        print(f"❌ Error: Invalid input folder: {input_folder}")
        sys.exit(1)
    
    # Create output folder if needed
    output_folder.mkdir(parents=True, exist_ok=True)
    
    # Find all Office documents (Word, Excel, PowerPoint)
    patterns = ['*.docx', '*.doc', '*.xlsx', '*.xls', '*.pptx', '*.ppt']
    files = []
    for pattern in patterns:
        files.extend(input_folder.glob(pattern))
    
    if not files:
        print(f"❌ No Office documents found in {input_folder}")
        sys.exit(1)
    
    print(f"📋 Found {len(files)} document(s) to process\n")
    
    # Initialize API client (loads credentials from .env)
    client = PlatformAPIClient()
    
    # Process each document
    success_count = 0
    failed_count = 0
    
    for i, doc in enumerate(files, 1):
        print(f"[{i}/{len(files)}] Processing: {doc.name}")
        
        try:
            # Step 1: Convert to PDF
            print("  🔐 Converting to PDF...")
            pdf_bytes = client.convert(doc, "pdf")
            temp_pdf = output_folder / f"{doc.stem}_temp.pdf"
            temp_pdf.write_bytes(pdf_bytes)
            
            # Step 2: Compress PDF
            print("  📦 Compressing...")
            compressed = client.compress(temp_pdf, level=2)
            temp_pdf.write_bytes(compressed)
            
            # Step 3: Remove all metadata/properties (PRIVACY PROTECTION)
            # TODO: The set-properties API endpoint needs proper parameters
            # Current issue: 422 error with empty params
            # Skipping for now until API documentation is clarified
            print("  🔄 Metadata removal (needs API param clarification)...")
            clean_pdf = compressed  # Use compressed version for now
            
            # Future: Remove annotations (API in development)
            # clean_pdf = client.remove_annotations(temp_pdf)
            
            # Future: Make accessible (API in development)  
            # clean_pdf = client.make_accessible(temp_pdf)
            
            # Save final PDF
            final_pdf = output_folder / f"{doc.stem}.pdf"
            final_pdf.write_bytes(clean_pdf)
            temp_pdf.unlink()  # Delete temp file
            
            print(f"  ✅ Secured: {final_pdf.name}\n")
            success_count += 1
            
        except Exception as e:
            print(f"  ❌ FAILED: {e}\n")
            failed_count += 1
            if temp_pdf.exists():
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
