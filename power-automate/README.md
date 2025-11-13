# Power Automate Integration

This folder contains instructions for creating a custom connector to integrate the Nitro Platform API with Microsoft Power Automate.

## Creating Your Custom Connector

### 1. Create New Custom Connector

1. Go to [Power Automate](https://make.powerautomate.com)
2. Navigate to **Data** → **Custom connectors**
3. Click **New custom connector** → **Create from blank**
4. Name it "Nitro Platform API"

### 2. Configure General Settings

- **Description**: Document processing API for conversions, extractions, and transformations
- **Host**: `api.gonitro.dev`
- **Base URL**: `/`

### 3. Configure Security

1. Set **Authentication type** to **API Key**
2. **Parameter label**: API Key
3. **Parameter name**: `X-API-Key`
4. **Parameter location**: Header

### 4. Add Key Operations

Add these essential operations:

#### Convert Document
- **Operation ID**: `convert-document`
- **Summary**: Convert Document
- **Verb**: POST
- **URL**: `/platform/conversions`
- **Request**: 
  - Body type: `multipart/form-data`
  - Parameter: `file` (file upload)
  - Parameter: `params` (string, JSON parameters)

#### Extract Text
- **Operation ID**: `extract-text`
- **Summary**: Extract PDF Text
- **Verb**: POST
- **URL**: `/platform/extractions/pdf-text`
- **Request**: Body with `file` parameter

#### Get Job Status
- **Operation ID**: `get-job-status`
- **Summary**: Get Job Status
- **Verb**: GET
- **URL**: `/jobs/{jobId}/status`
- **Parameter**: `jobId` (path parameter)

### 5. Test Your Connector

1. Go to **Test** tab
2. Create a new connection with your API key
3. Test the "Get Job Status" operation with a sample job ID

## Sample Flows

### Document Conversion Flow

**Trigger**: When a file is added to SharePoint
1. **Get file content** from SharePoint
2. **Convert Document** using your custom connector
3. **Create file** in SharePoint with converted result

### Batch Processing Flow

**Trigger**: Scheduled (daily)
1. **List files** from SharePoint folder
2. **Apply to each** file:
   - **Convert Document**
   - **Get Job Status** (with delay/retry logic)
   - **Get Job Result** when complete
   - **Update file** in destination folder

## Best Practices

- **Error Handling**: Add try-catch blocks around API calls
- **Async Jobs**: Use "Do until" loops to poll job status
- **Rate Limits**: Add 1-2 second delays between API calls
- **File Size**: Check file size limits before processing

## Authentication

Get your API key from the Nitro platform dashboard and use it when creating connections to your custom connector.
