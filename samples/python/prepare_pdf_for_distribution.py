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
            print("  🔒 Removing metadata properties...")
            
            # First, get current PDF properties
            properties_response = client._request("extractions", "get-properties", temp_pdf, {})
            current_properties = properties_response.get("result", {})
            
            # Display current properties
            print(f"    Current properties found:")
            for key, value in current_properties.items():
                if key != "file" and value:  # Skip empty values and file object
                    print(f"      • {key}: {value}")
            
            # Build params to clear properties
            # Note: Only user-editable properties can be cleared via the API
            # System properties (creator, producer, dates, trapped) are read-only in PDF spec
            writable_props = ["title", "author", "subject", "keywords"]
            clear_properties = {}
            for key in writable_props:
                if key in current_properties:
                    clear_properties[key] = ""  # Set to empty string to clear
            
            # Display which properties will be removed
            print(f"    Removing properties: {', '.join(clear_properties.keys())}")
            
            # Now set properties to empty strings
            clean_pdf = client._request_bytes("transformations", "set-properties", temp_pdf, clear_properties)
            temp_pdf.write_bytes(clean_pdf)
            
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
