#!/usr/bin/env python
"""Document conversion from CLI."""

import sys
from pathlib import Path
from platform_api import PlatformAPIClient

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python convert_cli.py <input> <output> <format>")
        print("Formats: pdf, docx, xlsx, png, jpg")
        sys.exit(1)
    
    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    to_format = sys.argv[3]
    
    client = PlatformAPIClient()
    print(f"🔄 Converting {input_path.name} to {to_format}...")
    converted = client.convert(input_path, to_format)
    output_path.write_bytes(converted)
    print(f"✅ Saved to {output_path}")
