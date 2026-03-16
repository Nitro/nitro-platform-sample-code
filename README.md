# Nitro Platform Sample Code

This repository provides production-ready examples and tools for integrating with the Nitro Platform API and Nitro Sign API, enabling document conversion, extraction, transformation, workflow automation, and eSignature capabilities.

## What's Included

This repository contains everything you need to start integrating with Nitro's APIs:

- **API Client SDKs** (Python & TypeScript) - Production-quality clients with OAuth2 authentication
- **Postman Collection** - Complete API reference with pre-configured examples for all endpoints
- **Production Workflow Examples** - Real-world CLI tools demonstrating complete business workflows
- **Documentation** - Comprehensive guides covering workflows, API reference, and setup instructions
- **Test Files** - Sample documents for testing all API operations

## API Capabilities

### Platform API - Document Processing

The Nitro Platform API provides programmatic access to document processing capabilities including:
- **Document Conversions**: Convert between formats (Word↔PDF, Excel→PDF, PowerPoint→PDF, Image→PDF, PDF→Word/Excel/Image)
- **Data Extraction**: Extract text, form data, tables, and detect PII from documents
- **Document Transformations**: Compress, merge, split, redact, password protect, rotate, flatten, and more
- **Async Processing**: Handle large documents with job-based workflows

### Sign API - eSignature & Envelopes

The Nitro Sign API provides eSignature capabilities including:
- **Envelope Management**: Create, send, track, and manage signature envelopes
- **Document Upload**: Add multiple documents to envelopes
- **Participant Management**: Add signers with roles and routing
- **Field Placement**: Programmatically place signature fields on documents
- **Workflow Automation**: Send reminders, track status, download signed documents

## Repository Structure

```
├── samples/
│   ├── python/                 # Python SDK and CLI workflow examples
│   └── typescript/             # TypeScript SDK and examples
├── postman/                    # Postman collection for API testing
├── docs/                       # API documentation and workflow guides
└── test_files/                 # Sample documents for testing
```

## Getting Started

### Prerequisites

1. **API Access**: Get OAuth2 client credentials:
   - Go to [https://admin.gonitro.com](https://admin.gonitro.com)
   - Navigate to **Settings** → **API**
   - Click **Create Application**
   - Name your application and save the Client ID and Client Secret

2. **Environment Setup**: Set the following variables:
   ```bash
   export PLATFORM_BASE_URL=https://api.gonitro.dev
   export PLATFORM_CLIENT_ID=<YOUR_CLIENT_ID>
   export PLATFORM_CLIENT_SECRET=<YOUR_CLIENT_SECRET>
   ```

### Quick Start Options

#### Using Postman
1. Import the collection from `postman/Platform-API.postman_collection.json`
2. Configure collection variables (see `postman/README.md`)
3. Get a bearer token
4. Select test files for each request
5. Run the sample requests

The Postman collection includes pre-configured examples for:
- Document conversions (Word↔PDF, Excel→PDF, PowerPoint→PDF, Image→PDF)
- Data extraction (text, forms, tables, PII detection)
- Document transformations (compress, merge, split, redact, password protection)
- Sign API operations (create envelopes, add participants, send for signing)

#### Using Python SDK
See `samples/python/README.md` for setup instructions. Key example scripts include:


#### Using TypeScript SDK
See `samples/typescript/` for TypeScript/Node.js integration examples with the same functionality as Python.

## Authentication

The API uses OAuth2 authentication:
1. Exchange client credentials for an access token via `POST /oauth/token`
2. Include the token in requests: `Authorization: Bearer <ACCESS_TOKEN>`

See the [authentication documentation](https://developers.gonitro.com/docs/api-reference/authentication/get-access-token) for details.

## Example Workflows

This repository demonstrates complete business workflows through working code examples:

### Document Processing Examples
- **quickstart.py** - Validates API credentials and tests OAuth2 authentication
- **convert_cli.py** - Single document conversion with CLI for any supported format
- **batch_process.py** - Processes entire folders with pattern matching and progress tracking
- **extract_data.py** - Extracts form fields, tables, or plain text from PDFs as structured JSON
- **smart_redact_pii.py** - AI-powered detection and redaction of PII (SSN, emails, addresses) for GDPR/HIPAA compliance
- **redact_by_keyword.py** - Finds and permanently redacts specific keywords across documents
- **bulk_password_protect.py** - Adds password protection to multiple PDFs in batch
- **prepare_pdf_for_distribution.py** - Marketing workflow that converts Word to PDF, compresses files, and removes metadata for external sharing

### eSignature Example
- **employee_policy_onboarding.py** - HR workflow that reads employee data from CSV, creates signature envelopes with policy documents, sends for signing, tracks status, and downloads signed documents organized by employee

See `docs/workflow-examples.md` for detailed implementation guides.

## API Client Architecture

The repository includes production-ready SDKs in both Python and TypeScript:

- **BaseOAuthClient** - Shared OAuth2 authentication with automatic token refresh
- **PlatformAPIClient** - Document conversion, extraction, and transformation operations
- **SignAPIClient** - Complete eSignature and envelope workflow management

Both SDKs provide identical functionality, allowing you to choose your preferred language.

## Testing

The `test_files/` directory contains sample documents for testing all API operations:
- Office documents (Word, Excel, PowerPoint) for conversion testing
- PDFs with forms, tables, and text for extraction testing
- Sample policies and employee data for eSignature workflow testing

All example scripts include references to these test files for immediate hands-on testing.

## Support

For API documentation and support, visit the [developer portal](https://developers.gonitro.dev).
