#!/usr/bin/env python
"""Redact by keyword search."""

import sys
from pathlib import Path
from platform_api import PlatformAPIClient

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python redact_by_keyword.py <input.pdf> <output.pdf> <keyword1> [keyword2 ...]")
        sys.exit(1)
    
    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    keywords = sys.argv[3:]
    
    client = PlatformAPIClient()
    
    print(f"🔍 Finding keywords in {input_path.name}...")
    bbox_data = client.find_text_boxes(input_path, keywords)
    
    text_boxes = bbox_data.get('result', {}).get('textBoxes', [])
    if not text_boxes:
        print("✅ No keywords found")
        sys.exit(0)
    
    print(f"🎯 Found {len(text_boxes)} keyword instances")
    print(f"🔒 Redacting keywords...")
    
    redactions = [{"pageIndex": box["pageIndex"], "boundingBox": box["boundingBox"]} 
                  for box in text_boxes]
    
    redacted = client.redact(input_path, redactions)
    output_path.write_bytes(redacted)
    print(f"✅ Saved to {output_path}")
