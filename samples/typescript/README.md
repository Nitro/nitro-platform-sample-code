# TypeScript Examples

TypeScript examples for integrating with the Nitro Platform API.

## Prerequisites

- Node.js 18.0.0 or higher
- npm or yarn package manager

## Setup

1. **Install dependencies:**
   ```bash
   cd samples/typescript
   npm install
   ```

2. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

3. **Get your API credentials:**
   - Go to https://admin.gonitro.com
   - Navigate to Settings → API
   - Click "Create Application"
   - Name your application and save the Client ID and Client Secret
   - Add these to your `.env` file:
     ```
     PLATFORM_CLIENT_ID=your-client-id-here
     PLATFORM_CLIENT_SECRET=your-client-secret-here
     PLATFORM_BASE_URL=https://api.gonitro.dev
     ```

4. **Test your setup:**
   ```bash
   npm run quickstart
   ```

## Development

### Running Scripts

All scripts can be run using npm scripts or directly with tsx:

```bash
# Using npm scripts (recommended)
npm run quickstart
npm run convert -- input.docx output.pdf pdf
npm run batch -- ./documents ./output pdf "*.docx"

# Using tsx directly
tsx src/scripts/quickstart.ts
tsx src/scripts/convert-cli.ts input.docx output.pdf pdf
```

### Building the Project

To compile TypeScript to JavaScript:

```bash
npm run build
```

This will create compiled JavaScript files in the `dist/` directory.

### Development Mode

For development with auto-reloading:

```bash
npm run dev
```

## Architecture

### API Client Structure

The TypeScript SDK follows a clean, object-oriented architecture similar to the Python SDK:

```
src/
├── api/
│   ├── base-client.ts       # BaseOAuthClient - Shared OAuth2 authentication
│   ├── platform-api.ts      # PlatformAPIClient - Document operations
│   └── sign-api.ts          # SignAPIClient - eSignature operations
├── helpers/
│   ├── document-helpers.ts  # File validation and setup utilities
│   └── sign-helpers.ts      # Sign workflow orchestration helpers
└── scripts/
    ├── quickstart.ts
    ├── convert-cli.ts
    ├── batch-process.ts
    ├── extract-data.ts
    ├── smart-redact-pii.ts
    ├── employee-policy-onboarding.ts
    ├── bulk-password-protect.ts
    ├── redact-by-keyword.ts
    └── prepare-pdf-for-distribution.ts
```

**BaseOAuthClient**: Base class providing OAuth2 authentication for all API clients
- Automatic token management with expiry buffer
- Connection pooling via axios
- Loads credentials from environment variables or .env file

**PlatformAPIClient**: Client for document conversions, extractions, and transformations
- Inherits authentication from BaseOAuthClient
- Methods: `convert()`, `extractText()`, `detectPii()`, `redact()`, `compress()`, etc.
- Uses FormData for file uploads

**SignAPIClient**: Client for eSignature/envelope operations
- Inherits authentication from BaseOAuthClient
- Methods: `createEnvelope()`, `createParticipant()`, `sendForSigning()`, etc.
- Full envelope lifecycle management

## Available Scripts

### Platform API Tools

#### quickstart.ts
Test authentication and API connection.
```bash
npm run quickstart
```

#### convert-cli.ts
Convert a single document to another format.
```bash
npm run convert -- <input-file> <output-file> <format>

# Examples:
npm run convert -- document.docx document.pdf pdf
npm run convert -- presentation.pptx slide.png png
```

**Supported formats:** pdf, docx, xlsx, pptx, png

#### batch-process.ts
Batch convert multiple documents in a folder.
```bash
npm run batch -- <input-folder> <output-folder> <format> [pattern]

# Examples:
npm run batch -- ./documents ./output pdf "*.docx"
npm run batch -- ./spreadsheets ./pdfs pdf "*.xlsx"
```

#### extract-data.ts
Extract structured data (forms or tables) from PDFs.
```bash
npm run extract -- <mode> <input-pdf> <output-json>

# Examples:
npm run extract -- forms application.pdf data.json
npm run extract -- tables invoice.pdf tables.json
```

**Modes:**
- `forms` - Extract form fields (name-value pairs)
- `tables` - Extract table data (rows and columns)

#### smart-redact-pii.ts
Automatically detect and redact personally identifiable information (PII).
```bash
npm run smart-redact -- <input-folder> <output-folder>

# Example:
npm run smart-redact -- ./documents ./redacted
```

Detects and redacts:
- Social Security Numbers
- Phone numbers
- Email addresses
- Physical addresses
- Other PII patterns

#### redact-by-keyword.ts
Redact specific keywords or phrases from PDFs.
```bash
npm run redact-keyword -- <input-pdf> <output-pdf> <keyword1> [keyword2 ...]

# Examples:
npm run redact-keyword -- contract.pdf redacted.pdf "confidential" "proprietary"
npm run redact-keyword -- report.pdf clean.pdf "Project Zeus" "Client ABC"
```

#### bulk-password-protect.ts
Apply password protection to multiple PDFs.
```bash
npm run bulk-password -- <input-folder> <output-folder> <password>

# Example:
npm run bulk-password -- ./documents ./protected "MySecureP@ss123"
```

**Note:** Password must be at least 6 characters long.

#### prepare-pdf-for-distribution.ts
Prepare documents for external distribution (convert to PDF, compress, remove metadata).
```bash
npm run prepare-pdf -- <input-folder> <output-folder>

# Example:
npm run prepare-pdf -- ./brochures ./distribution
```

This script:
1. Converts documents to PDF format
2. Compresses PDFs to reduce file size
3. Removes all metadata properties (author, title, etc.)

### Sign API Tools

#### employee-policy-onboarding.ts
Complete HR onboarding workflow: send company policies to employees for signature.

```bash
npm run employee-policy -- <policies-folder> <employees-csv>

# Example:
npm run employee-policy -- ./policies ./employees.csv
```

**CSV Format:**
```csv
name,email
John Doe,john.doe@company.com
Jane Smith,jane.smith@company.com
```

**This script:**
1. Loads employee list from CSV
2. Loads policy documents from folder
3. For each employee:
   - Creates a signature envelope
   - Uploads all policy documents
   - Adds the employee as a signer
   - Configures signature fields
   - Sends the envelope via email
   - Monitors signing status (up to 60 minutes)
   - Downloads signed documents when complete
4. Organizes output by employee folder

**Output Structure:**
```
output/
├── john-doe/
│   ├── signed-documents/
│   │   ├── policy-1-signed.pdf
│   │   ├── policy-2-signed.pdf
│   │   └── audit-trail.pdf
│   └── envelope-info.json
├── jane-smith/
    ├── signed-documents/
    └── envelope-info.json
```

## Testing with Sample Files

The repository includes test files you can use to try out the scripts. All test files are located in the `../../test_files/` directory (relative to the TypeScript samples folder).

### Quick Test Commands

#### 1. Test Authentication
```bash
npm run quickstart
# Expected: ✅ Authentication successful! Token: eyJ0...
```

#### 2. Convert Single Document
```bash
# Convert Word document to PDF
npm run convert -- ../../test_files/test-batch/Analysis.docx output.pdf pdf

# Convert Excel to PDF
npm run convert -- ../../test_files/test-batch/Feedback.xlsx output.pdf pdf

# Convert PowerPoint to PNG
npm run convert -- ../../test_files/SamplePPTX.pptx output.png png
```

#### 3. Batch Document Conversion
```bash
# Convert all Word documents in test-batch to PDF
npm run batch -- ../../test_files/test-batch ./output pdf "*.docx"

# Convert all Excel files
npm run batch -- ../../test_files/test-batch ./output pdf "*.xlsx"
```

#### 4. Extract Data from PDFs
```bash
# Extract form fields from student loan application
npm run extract -- forms "../../test_files/test-pdfs/BOB - Student-Loan-Application-Form.pdf" forms-output.json

# Extract tables from PDF
npm run extract -- tables "../../test_files/test-pdfs/Sample Tables.pdf" tables-output.json
```

#### 5. Smart PII Redaction
```bash
# Automatically detect and redact PII from resume
npm run smart-redact -- ../../test_files/test-pdfs ./redacted-output
```

#### 6. Keyword-Based Redaction
```bash
# Redact specific keywords from resume
npm run redact-keyword -- ../../test_files/test-pdfs/SampleResume.pdf redacted.pdf "resume" "contact"
```

#### 7. Bulk Password Protection
```bash
# Password protect all PDFs in test-pdfs folder
npm run bulk-password -- ../../test_files/test-pdfs ./protected-output "SecurePass123"
```

#### 8. Prepare PDFs for Distribution
```bash
# Convert marketing brochures to optimized PDFs with metadata removed
npm run prepare-pdf -- ../../test_files/pdf-distribution ./distribution-output
```

#### 9. Employee Policy Onboarding (Sign API)
```bash
# Send company policies for signature to employees
npm run employee-policy -- ../../test_files/test-sign ../../test_files/test-sign/employees.csv

# Note: This sends real signature requests to email addresses in the CSV!
# Check the CSV file first: ../../test_files/test-sign/employees.csv
```

### Available Test Files

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

- **Sign API Testing**: The `employee-policy-onboarding` script sends real signature requests via email. Make sure the email addresses in `employees.csv` are valid and you have permission to send them test requests.
- **Output Folders**: All scripts automatically create output folders if they don't exist.
- **File Paths**: Use quotes around file paths with spaces (e.g., `"Sample Tables.pdf"`).
- **Large Files**: Some operations may take longer with large or complex documents.

## Code Style & Conventions

### Naming Conventions
- **Files:** kebab-case (e.g., `base-client.ts`, `convert-cli.ts`)
- **Classes:** PascalCase (e.g., `BaseOAuthClient`, `PlatformAPIClient`)
- **Functions/Variables:** camelCase (e.g., `getToken`, `convertDocument`)
- **Constants:** SCREAMING_SNAKE_CASE (e.g., `TOKEN_EXPIRY_BUFFER_SECONDS`)
- **Types/Interfaces:** PascalCase (e.g., `Settings`, `TokenResponse`)

### Module System
This project uses ES Modules (ESM). All imports must use the `.js` extension:
```typescript
import { BaseOAuthClient } from './base-client.js';
```

### Error Handling
Always use try-catch blocks and provide meaningful error messages:
```typescript
try {
  const result = await client.convert(filePath, OutputFormat.PDF);
  console.log('✅ Success');
} catch (error: any) {
  console.error(`❌ Error: ${error.message}`);
  process.exit(1);
}
```

## TypeScript Configuration

The project uses strict TypeScript settings:
- Target: ES2022
- Module: ESNext
- Strict mode enabled
- Source maps for debugging

See `tsconfig.json` for complete configuration.

## Differences from Python SDK

While the TypeScript SDK maintains functional parity with the Python SDK, there are some differences:

1. **Module System:** Uses ES Modules instead of Python imports
2. **Async/Await:** All API calls are asynchronous (using async/await)
3. **Type Safety:** Full TypeScript type checking
4. **CLI Framework:** Uses commander instead of typer
5. **File Operations:** Uses Node.js fs/promises instead of pathlib
6. **HTTP Client:** Uses axios instead of httpx

## Dependencies

### Production Dependencies
- **axios** - HTTP client with connection pooling
- **commander** - CLI framework
- **dotenv** - Environment variable management
- **form-data** - Multipart form data for file uploads
- **csv-parse** - CSV file parsing
- **adm-zip** - ZIP file extraction
- **mime-types** - MIME type detection

### Development Dependencies
- **typescript** - TypeScript compiler
- **tsx** - TypeScript execution and development
- **@types/node** - Node.js type definitions

## Troubleshooting

### "Missing required environment variables"
Make sure you've created a `.env` file with your API credentials. Copy `.env.example` and fill in your values.

### "ENOENT: no such file or directory"
Check that your input file paths are correct and the files exist.

### "401 Unauthorized"
Your API credentials may be incorrect or expired. Double-check your `PLATFORM_CLIENT_ID` and `PLATFORM_CLIENT_SECRET` in the `.env` file.

### "Network error" or timeout
Check your internet connection and verify that `PLATFORM_BASE_URL` is correct in your `.env` file.

### TypeScript compilation errors
Make sure all dependencies are installed:
```bash
npm install
```

## Further Resources

- [Nitro Platform API Documentation](https://developers.gonitro.com/docs)
- [Nitro Admin Portal](https://admin.gonitro.com)
- [TypeScript Documentation](https://www.typescriptlang.org/docs/)
- [Node.js Documentation](https://nodejs.org/docs/)

## Support

For questions or issues:
- Check the [Python SDK examples](../python/README.md) for additional context
- Review the [API documentation](https://developers.gonitro.com/docs)
- Contact Nitro support through the admin portal
