# API Overview

The Nitro Platform API provides document processing capabilities through a RESTful interface.

## Base URL

All API requests are made to: `https://api.gonitro.dev`

## Authentication

The API uses OAuth2 client credentials flow:

1. **Get Credentials**: Create an application at [admin.gonitro.com](https://admin.gonitro.com) → Settings → API
2. **Get Token**: Exchange credentials for access token via `POST /oauth/token`
3. **Use Token**: Include in requests as `Authorization: Bearer <ACCESS_TOKEN>`

## Request/Response Patterns

### Synchronous Operations
- Submit request with file
- Get immediate response with result
- Best for: Small files, simple operations

### Asynchronous Operations
- Submit request, get job ID
- Poll `/jobs/{jobId}/status` for progress
- Download result when complete
- Best for: Large files, complex operations

## API Categories

### Conversions (`/platform/conversions`)
Convert documents between formats:
- Word ↔ PDF
- Excel → PDF  
- PowerPoint → PDF
- Images → PDF

### Extractions (`/platform/extractions`)
Extract data from documents:
- Text extraction
- Form data extraction
- Table data extraction
- PII detection

### Transformations (`/platform/transformations`)
Modify PDF documents:
- Compress, merge, split
- Redact content
- Password protect/remove
- Rotate/delete pages

### Jobs (`/jobs`)
Manage asynchronous operations:
- Check job status
- Download job results
- Handle job errors

## Error Handling

The API returns standard HTTP status codes:
- `200` - Success
- `400` - Bad Request (invalid parameters)
- `401` - Unauthorized (invalid/missing token)
- `404` - Not Found (invalid endpoint/job ID)
- `500` - Internal Server Error

Error responses include details:
```json
{
  "error": "Invalid file format",
  "message": "Only PDF files are supported for this operation"
}
```
