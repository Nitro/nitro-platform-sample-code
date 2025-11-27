#!/usr/bin/env python
"""Batch process documents from CLI."""

import sys
from pathlib import Path
from platform_api import PlatformAPIClient

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python batch_process.py <input_dir> <output_dir> <format> [pattern]")
        print("Example: python batch_process.py ./docs ./output pdf '*.docx'")
        sys.exit(1)
    
    input_dir = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])
    to_format = sys.argv[3]
    pattern = sys.argv[4] if len(sys.argv) > 4 else "*"
    
    output_dir.mkdir(exist_ok=True)
    files = list(input_dir.glob(pattern))
    
    if not files:
        print(f"❌ No files matching '{pattern}' found in {input_dir}")
        sys.exit(1)
    
    client = PlatformAPIClient()
    print(f"📁 Processing {len(files)} files...")
    
    for i, file_path in enumerate(files, 1):
        try:
            print(f"[{i}/{len(files)}] Converting {file_path.name}...")
            converted = client.convert(file_path, to_format)
            output_path = output_dir / f"{file_path.stem}.{to_format}"
            output_path.write_bytes(converted)
            print(f"  ✅ Saved to {output_path.name}")
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    print(f"✅ Batch processing complete")
