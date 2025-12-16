# Python Examples

Python examples for integrating with the Nitro Platform API.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Copy and configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

3. Run the quickstart example:
   ```bash
   python quickstart.py
   ```

## Files

- `platform_api.py` - Main API client library
- `quickstart.py` - Authentication test
- `convert_cli.py` - Document conversion
- `extract_data.py` - Extract forms and tables
- `smart_redact_pii.py` - Auto-detect and redact PII
- `redact_by_keyword.py` - Redact specific keywords
- `batch_process.py` - Batch convert documents
- `bulk_password_protect.py` - Password protect multiple PDFs

## Usage Examples

### Authentication
```bash
python quickstart.py
```

### Convert Documents
```bash
# Convert DOCX to PDF
python convert_cli.py input.docx output.pdf pdf

# Convert PDF to DOCX
python convert_cli.py input.pdf output.docx docx
```

### Extract Data
```bash
# Extract tables
python extract_data.py tables input.pdf output.json

# Extract forms
python extract_data.py forms input.pdf output.json
```

### Redact Content
```bash
# Auto-detect and redact PII
python smart_redact_pii.py input.pdf output.pdf

# Redact specific keywords
python redact_by_keyword.py input.pdf output.pdf "confidential" "secret"
```

### Batch Operations
```bash
# Convert all DOCX files to PDF
python batch_process.py ./input ./output pdf "*.docx"

# Password protect all PDFs
python bulk_password_protect.py ./input ./output "MyPassword123"
```

## Using the API Client

```python
from pathlib import Path
from api.platform_api import PlatformAPIClient

client = PlatformAPIClient()

# Convert document
converted = client.convert(Path("input.docx"), "pdf")
Path("output.pdf").write_bytes(converted)

# Extract text
text_data = client.extract_text(Path("document.pdf"))

# Detect PII
pii_data = client.detect_pii(Path("document.pdf"))

# Redact content
redactions = [{"pageIndex": 0, "boundingBox": {...}}]
redacted = client.redact(Path("document.pdf"), redactions)
```

## Sample Files

Sample files for testing are available in the `test_files/` folder at the repository root.

## Getting Your Credentials

1. Go to [https://admin.gonitro.com](https://admin.gonitro.com)
2. Navigate to **Settings** → **API**
3. Click **Create Application**
4. Save the Client ID and Client Secret to your `.env` file
