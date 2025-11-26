#!/usr/bin/env python
"""Password protect PDFs in bulk."""

import sys
from pathlib import Path
from platform_api import PlatformAPIClient

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python bulk_password_protect.py <input_dir> <output_dir> <password>")
        sys.exit(1)
    
    input_dir = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])
    password = sys.argv[3]
    
    output_dir.mkdir(exist_ok=True)
    files = list(input_dir.glob("*.pdf"))
    
    if not files:
        print(f"❌ No PDF files found in {input_dir}")
        sys.exit(1)
    
    client = PlatformAPIClient()
    print(f"🔒 Protecting {len(files)} PDFs with password...")
    
    for i, file_path in enumerate(files, 1):
        try:
            print(f"[{i}/{len(files)}] Protecting {file_path.name}...")
            protected = client.password_protect(file_path, password)
            output_path = output_dir / file_path.name
            output_path.write_bytes(protected)
            print(f"  ✅ Saved to {output_path.name}")
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    print(f"✅ Bulk password protection complete")
