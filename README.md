# Nitro Platform API Integrations

This repository provides examples and tools for integrating with the Nitro Platform API, enabling document conversion, extraction, transformation, and workflow automation.

## What is the Platform API?

The Nitro Platform API provides programmatic access to document processing capabilities including:
- **Document Conversions**: Convert between formats (Word↔PDF, Excel→PDF, PowerPoint→PDF, etc.)
- **Data Extraction**: Extract text, form data, tables, and detect PII from documents
- **Document Transformations**: Compress, merge, split, redact, password protect, and more
- **Async Processing**: Handle large documents with job-based workflows

## Repository Structure

```
├── postman/                    # Postman collection and environment
├── power-automate/            # Custom connector and sample flows
├── samples/
│   └── python/               # Python examples
└── docs/                     # API documentation and guides
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

#### Using Power Automate
1. Create a custom connector using instructions in `power-automate/`
2. Configure API key authentication
3. Build flows for document processing workflows

#### Using Sample Code
- **Python**: See `samples/python/README.md`

## Authentication

The API uses OAuth2 authentication:
1. Exchange client credentials for an access token via `POST /oauth/token`
2. Include the token in requests: `Authorization: Bearer <ACCESS_TOKEN>`

See the [authentication documentation](https://developers.gonitro.com/docs/api-reference/authentication/get-access-token) for details.

## Common Workflows

- **Document Conversion**: Upload a file → Get converted result
- **Async Processing**: Start job → Poll status → Download result
- **Data Extraction**: Upload PDF → Extract text/tables/forms
- **Document Transformation**: Upload PDF → Apply operations → Download result

## Support

For API documentation and support, visit the [developer portal](https://developers.gonitro.dev).
