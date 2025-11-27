#!/usr/bin/env python
"""Smart redact PII from documents."""

import sys
from pathlib import Path
from platform_api import PlatformAPIClient

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python smart_redact_pii.py <input.pdf> <output.pdf>")
        sys.exit(1)
    
    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    
    client = PlatformAPIClient()
    
    print(f"🔍 Detecting PII in {input_path.name}...")
    pii_data = client.detect_pii(input_path)
    
    pii_boxes = pii_data.get('result', {}).get('PIIBoxes', [])
    if not pii_boxes:
        print("✅ No PII detected")
        sys.exit(0)
    
    print(f"🎯 Found {len(pii_boxes)} PII instances")
    print(f"🔒 Redacting PII...")
    
    redactions = [{"pageIndex": box["pageIndex"], "boundingBox": box["boundingBox"]} 
                  for box in pii_boxes]
    
    redacted = client.redact(input_path, redactions)
    output_path.write_bytes(redacted)
    print(f"✅ Saved to {output_path}")
