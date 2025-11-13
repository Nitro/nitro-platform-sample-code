# Postman Collection

This folder contains the Postman collection for the Nitro Platform API with examples for all major endpoints.

## Getting Started

### 1. Import the Collection

1. Open Postman
2. Click **Import** in the top left
3. Select `Platform-API.postman_collection.json`
4. The collection will appear in your workspace

### 2. Configure Environment Variables

Create a new environment in Postman with these variables:

| Postman Variable | Python .env Variable | Description | Example Value |
|------------------|---------------------|-------------|---------------|
| `baseUrl` | `PLATFORM_BASE_URL` | API base URL | `https://api.gonitro.dev` |
| `clientID` | `PLATFORM_CLIENT_ID` | Your client ID | `your-client-id` |
| `clientSecret` | `PLATFORM_CLIENT_SECRET` | Your client secret | `your-client-secret` |
| `token` | (auto-populated) | Bearer token | `eyJ0eXAiOiJKV1Q...` |

**Note**: If you're also using the Python samples, you can use the same credential values from your `.env` file - just use the Postman variable names shown above.

### 3. Get Authentication Token

1. Navigate to **Authorization** → **Get Bearer Token**
2. Ensure your `clientID` and `clientSecret` are set
3. Send the POST request
4. The `token` variable will be automatically set for subsequent requests

### 4. Run Sample Requests

The collection is organized into folders:

- **Authorization**: Get OAuth2 bearer tokens
- **Conversions**: Convert documents between formats
- **Extractions**: Extract text, form data, tables, and PII
- **Transformations**: Modify PDFs (compress, merge, split, etc.)
- **Jobs**: Check status and get results for async operations

## Example Workflow

1. **Get Token**: Run "Get Bearer Token" request
2. **Convert Document**: Use "Word → PDF" with a sample .docx file
3. **Extract Data**: Use "Extract PDF Text" on the converted PDF
4. **Transform**: Use "Compress" to reduce file size

## File Upload

Many endpoints require file uploads. In Postman:
1. Select **Body** → **form-data**
2. Set key to `file` (or as specified in the request)
3. Change type to **File**
4. Select your document

## Async Operations

Some operations return a job ID for async processing:
1. Submit the request and note the `jobId` in the response
2. Use **Jobs** → **Get Async Job Status** to check progress
3. When status is `completed`, use **Get Async Job Result** to download the result

## Getting Your Credentials

To get your API credentials:
1. Go to [https://admin.gonitro.com](https://admin.gonitro.com)
2. Navigate to **Settings** → **API**
3. Click **Create Application**
4. Name your application and save the Client ID and Client Secret
