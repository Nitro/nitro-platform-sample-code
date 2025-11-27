#!/usr/bin/env python
"""Extract forms and tables from documents."""

import sys
import json
from pathlib import Path
from platform_api import PlatformAPIClient

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python extract_data.py <forms|tables> <input.pdf> <output.json>")
        sys.exit(1)
    
    mode = sys.argv[1]
    input_path = Path(sys.argv[2])
    output_path = Path(sys.argv[3])
    
    client = PlatformAPIClient()
    
    if mode == "forms":
        print(f"📋 Extracting form data from {input_path.name}...")
        data = client.extract_forms(input_path)
    elif mode == "tables":
        print(f"📊 Extracting table data from {input_path.name}...")
        data = client.extract_tables(input_path)
    else:
        print("❌ Mode must be 'forms' or 'tables'")
        sys.exit(1)
    
    output_path.write_text(json.dumps(data, indent=2))
    print(f"✅ Saved to {output_path}")
