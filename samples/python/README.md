# Python Examples

Python examples for integrating with the Nitro Platform API.

## Setup

### Option 1: Using uv (Recommended)

This project uses [uv](https://docs.astral.sh/uv/) for fast, reliable Python package management.

1. Install uv if you haven't already:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Sync dependencies:
   ```bash
   cd samples/python
   uv sync
   ```

3. Copy and configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

4. Run the quickstart example:
   ```bash
   uv run python quickstart.py
   ```

   Or use the Task command:
   ```bash
   task quickstart
   ```

### Option 2: Using pip

1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -e .  # Installs from pyproject.toml
   ```

3. Copy and configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

4. Run the quickstart example:
   ```bash
   python quickstart.py
   ```

## Development

### Running Scripts with uv

All Python scripts should be run using `uv run` to ensure they use the correct dependencies:

```bash
uv run python script.py
```

### Code Quality Tools

This project uses multiple linting and type checking tools configured in `pyproject.toml`:

#### Ruff (Fast Python linter)
```bash
# Check for linting issues
uvx ruff check

# Auto-fix issues
uvx ruff check --fix

# Format code
uvx ruff format
```

#### Pylint (Comprehensive linter)
```bash
# Check all Python files
uv run pylint *.py api/*.py helper_functions/*.py

# Check specific file
uv run pylint convert_cli.py
```

#### Pyright (Type checker)
```bash
# Type check all files
uv run pyright

# Type check specific file
uv run pyright convert_cli.py
```

#### Run All Quality Checks
```bash
# Run all three tools
uvx ruff check && uv run pylint *.py api/*.py helper_functions/*.py && uv run pyright
```

## Architecture

### API Client Structure

The Python SDK uses a clean, object-oriented architecture:

```
api/
├── __init__.py              # Package exports
├── base_client.py           # BaseOAuthClient - Shared OAuth2 authentication
├── platform_api.py          # PlatformAPIClient - Document operations
└── sign_api.py             # SignAPIClient - eSignature operations
```

**BaseOAuthClient**: Base class providing OAuth2 authentication for all API clients
- Automatic token management and refresh
- Public `get_token()` method for accessing authentication tokens
- Shared by both Platform and Sign API clients

**PlatformAPIClient**: Client for document conversions, extractions, and transformations
- Inherits authentication from BaseOAuthClient
- Methods: `convert()`, `extract_text()`, `detect_pii()`, `redact()`, `compress()`, etc.

**SignAPIClient**: Client for eSignature/envelope operations
- Inherits authentication from BaseOAuthClient  
- Methods: `create_envelope()`, `create_participant()`, `send_envelope()`, etc.
- See [SIGN_API.md](SIGN_API.md) for detailed documentation

## CLI Tools

### Platform API Tools
- `quickstart.py` - Authentication test
- `convert_cli.py` - Document conversion
- `extract_data.py` - Extract forms and tables from PDFs
- `smart_redact_pii.py` - Auto-detect and redact PII
- `redact_by_keyword.py` - Redact specific keywords
- `batch_process.py` - Batch convert documents
- `bulk_password_protect.py` - Password protect multiple PDFs
- `prepare_pdf_for_distribution.py` - Prepare PDFs for external distribution (convert, compress, remove metadata)

### Sign API Tools (eSignature)
- `employee_policy_onboarding.py` - Complete HR workflow: send policy documents to employees for signature

## Usage Examples

### Authentication
```bash
# Run directly
uv run python quickstart.py

# Or use Task command
task quickstart
```

### Convert Documents
```bash
# Convert DOCX to PDF
uv run python convert_cli.py input.docx output.pdf pdf

# Or use Task command
task convert INPUT=input.docx OUTPUT=output.pdf FORMAT=pdf
```

### Extract Data
```bash
# Extract tables
uv run python extract_data.py tables input.pdf output.json

# Or use Task command
task extract MODE=tables INPUT=input.pdf OUTPUT=output.json
```

### Redact Content
```bash
# Auto-detect and redact PII
uv run python smart_redact_pii.py input_folder output_folder

# Or use Task command
task smart-redact INPUT_DIR=./input OUTPUT_DIR=./output
```

### Batch Operations
```bash
# Convert all DOCX files to PDF
uv run python batch_process.py ./input ./output pdf "*.docx"

# Or use Task command
task batch INPUT_DIR=./input OUTPUT_DIR=./output FORMAT=pdf PATTERN='*.docx'
```

## Using the API Client

### Platform API Client

```python
from pathlib import Path
from api.platform_api import PlatformAPIClient

# Initialize client (loads credentials from .env)
client = PlatformAPIClient()

# Get authentication token (if needed)
token = client.get_token()
print(f"Access token: {token[:20]}...")

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

### Sign API Client

```python
from pathlib import Path
from api.sign_api import SignAPIClient

# Initialize client (loads credentials from .env)
sign_client = SignAPIClient()

# Create an envelope
envelope_data = {
    "name": "Contract Signature",
    "mode": "parallel",
    "notification": {
        "subject": "Please sign the contract",
        "body": "Review and sign the attached document."
    }
}
envelope = sign_client.create_envelope(envelope_data)
envelope_id = envelope["ID"]

# Add participant
participant_data = {
    "email": "signer@example.com",
    "role": "signer",
    "name": "John Doe"
}
participant = sign_client.create_participant(envelope_id, participant_data)

# Send envelope
sign_client.send_envelope(envelope_id)

print(f"Envelope {envelope_id} sent successfully!")
```

### Shared Authentication

Both clients inherit from `BaseOAuthClient`, so they share the same authentication mechanism:

```python
from api.platform_api import PlatformAPIClient
from api.sign_api import SignAPIClient

# Both clients use the same credentials from .env
platform_client = PlatformAPIClient()
sign_client = SignAPIClient()

# Both can access tokens via the public API
platform_token = platform_client.get_token()
sign_token = sign_client.get_token()
```

## Code Quality

This project maintains high code quality standards:

- **Type Checking**: Strict type checking with Pyright (0 errors)
- **Linting**: Modern Python patterns with Ruff  
- **Code Quality**: Pylint score of 9.81/10
- **Python Version**: Requires Python 3.14+

### Running Linters

```bash
# Type checking
pyright

# Modern Python patterns
uv run --with ruff ruff check .

# Code quality analysis
uv run pylint *.py api/*.py helper_functions/*.py
```

## Testing

A comprehensive test suite is available in `TEST_SUITE.txt` with commands for testing all scripts and functionality. Run tests with:

```bash
# Individual script tests
python quickstart.py
python convert_cli.py ../../test_files/test-batch/Analysis.docx /tmp/output.pdf pdf

# Or use the automated test script (see TEST_SUITE.txt)
./test_all.sh
```

## Sample Files

Sample files for testing are available in the `test_files/` folder at the repository root.

## Getting Your Credentials

1. Go to [https://admin.gonitro.com](https://admin.gonitro.com)
2. Navigate to **Settings** → **API**
3. Click **Create Application**
4. Save the Client ID and Client Secret to your `.env` file
