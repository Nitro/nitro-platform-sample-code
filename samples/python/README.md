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
- `optimize_benchmark.py` - Benchmark the Optimize API on a folder of PDFs, with CSVs and a self-contained HTML report

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

### Benchmark PDF Compression
```bash
# Run every PDF in a folder through the Optimize API (default profile: minimal-file-size)
uv run python optimize_benchmark.py ./pdfs ./output

# Benchmark several profiles side by side
uv run python optimize_benchmark.py ./pdfs ./output -p minimal-file-size -p web

# Or use Task command
task optimize-benchmark INPUT_DIR=./pdfs OUTPUT_DIR=./output
```

The run writes the optimized PDFs, `results.csv`, `summary.csv` and a
self-contained `report.html` (headline numbers, a size-reduction distribution
chart and a filterable per-file table) that opens in your browser when done.

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

## Testing with Sample Files

The repository includes test files you can use to try out the scripts. All test files are located in the `../../test_files/` directory (relative to the Python samples folder).

### Quick Test Commands

#### 1. Test Authentication
```bash
uv run python quickstart.py
# Expected: ✅ Authentication successful! Token: eyJ0...
```

#### 2. Convert Single Document
```bash
# Convert Word document to PDF
uv run python convert_cli.py ../../test_files/test-batch/Analysis.docx output/test_output.pdf pdf

# Convert Excel to PDF
uv run python convert_cli.py ../../test_files/test-batch/Feedback.xlsx output/test_output.pdf pdf

# Convert PowerPoint to PNG
uv run python convert_cli.py ../../test_files/SamplePPTX.pptx output/test_output.png png
```

#### 3. Batch Document Conversion
```bash
# Convert all Word documents in test-batch to PDF
uv run python batch_process.py \
  ../../test_files/test-batch \
  output/batch_results \
  pdf \
  "*.docx"

# Convert all Excel files
uv run python batch_process.py \
  ../../test_files/test-batch \
  output/batch_results \
  pdf \
  "*.xlsx"
```

#### 4. Extract Data from PDFs
```bash
# Extract form fields from student loan application
uv run python extract_data.py \
  forms \
  "../../test_files/test-pdfs/BOB - Student-Loan-Application-Form.pdf" \
  output/forms_output.json

# Extract tables from PDF
uv run python extract_data.py \
  tables \
  "../../test_files/test-pdfs/Sample Tables.pdf" \
  output/tables_output.json
```

#### 5. Smart PII Redaction
```bash
# Automatically detect and redact PII from PDFs
uv run python smart_redact_pii.py \
  ../../test_files/test-pdfs \
  output/pii_redacted
```

#### 6. Keyword-Based Redaction
```bash
# Redact specific keywords from resume
uv run python redact_by_keyword.py \
  ../../test_files/test-pdfs/SampleResume.pdf \
  output/redacted.pdf \
  "resume" "contact"
```

#### 7. Bulk Password Protection
```bash
# Password protect all PDFs in test-pdfs folder
uv run python bulk_password_protect.py \
  ../../test_files/test-pdfs \
  output/protected \
  "SecurePass123"
```

#### 8. Prepare PDFs for Distribution
```bash
# Convert marketing brochures to optimized PDFs with metadata removed
uv run python prepare_pdf_for_distribution.py \
  ../../test_files/pdf-distribution \
  output/distribution
```

#### 9. Employee Policy Onboarding (Sign API)
```bash
# Send company policies for signature to employees
uv run python employee_policy_onboarding.py \
  ../../test_files/test-sign \
  ../../test_files/test-sign/employees.csv

# Note: This sends real signature requests to email addresses in the CSV!
# Check the CSV file first: ../../test_files/test-sign/employees.csv
```

### Using Task Commands

All the above can also be run using Task commands for convenience:

```bash
# Convert
task convert INPUT=../../test_files/test-batch/Analysis.docx OUTPUT=output/test.pdf FORMAT=pdf

# Batch process
task batch INPUT_DIR=../../test_files/test-batch OUTPUT_DIR=output/batch FORMAT=pdf PATTERN='*.docx'

# Extract data
task extract MODE=tables INPUT="../../test_files/test-pdfs/Sample Tables.pdf" OUTPUT=output/tables.json

# Smart redact
task smart-redact INPUT_DIR=../../test_files/test-pdfs OUTPUT_DIR=output/redacted

# Prepare PDFs
task prepare-distribution INPUT_DIR=../../test_files/pdf-distribution OUTPUT_DIR=output/distribution

# Employee onboarding
task onboard-employees POLICIES_DIR=../../test_files/test-sign CSV=../../test_files/test-sign/employees.csv
```

### Available Test Files

Sample files for testing are available in the `test_files/` folder at the repository root.

#### Batch Conversion (`test_files/test-batch/`)
- `Analysis.docx` - Word document
- `Feedback.xlsx` - Excel spreadsheet

#### PDF Operations (`test_files/test-pdfs/`)
- `SampleResume.pdf` - Resume with PII (for redaction testing)
- `Sample Tables.pdf` - PDF with tables (for extraction)
- `BOB - Student-Loan-Application-Form.pdf` - Form with fields (for extraction)

#### Distribution (`test_files/pdf-distribution/`)
- `Marketing_Brochure_Product_A_Rich.docx`
- `Marketing_Brochure_Product_B_Rich.docx`
- `Marketing_Brochure_Product_C_Rich.docx`

#### Sign API (`test_files/test-sign/`)
- `company-policies.pdf` - Company policy document
- `confidentiality-agreement.pdf` - NDA template
- `sample-company-policies.pdf` - Additional policy
- `employees.csv` - Sample employee list for testing

### Important Notes

- **Sign API Testing**: The `employee_policy_onboarding` script sends real signature requests via email. Make sure the email addresses in `employees.csv` are valid and you have permission to send them test requests.
- **Output Folders**: All scripts automatically create output folders if they don't exist.
- **File Paths**: Use quotes around file paths with spaces (e.g., `"Sample Tables.pdf"`).
- **Large Files**: Some operations may take longer with large or complex documents.


## Getting Your Credentials

1. Go to [https://admin.gonitro.com](https://admin.gonitro.com)
2. Navigate to **Settings** → **API**
3. Click **Create Application**
4. Save the Client ID and Client Secret to your `.env` file
