# Workflow Examples

Common end-to-end workflows using the Platform API.

## Document Conversion Workflow

**Goal**: Convert Word documents to PDF

### Using Postman
1. Run "Get Bearer Token" request
2. Use "Word → PDF" request with your .docx file
3. Download the converted PDF from response

### Using Python
```python
token = get_access_token(client_id, client_secret)
with open('document.docx', 'rb') as f:
    result = convert_to_pdf(token, f)
with open('document.pdf', 'wb') as f:
    f.write(result)
```

### Using Power Automate
1. **Trigger**: When file added to SharePoint
2. **Action**: Convert using custom connector
3. **Action**: Save result back to SharePoint

## Data Extraction Workflow

**Goal**: Extract text and tables from PDF invoices

### Steps
1. **Upload PDF**: Submit to `/platform/extractions/pdf-text`
2. **Extract Tables**: Submit to `/platform/extractions/pdf-table-data`
3. **Process Data**: Parse extracted JSON for relevant fields
4. **Store Results**: Save to database/spreadsheet

### Use Cases
- Invoice processing
- Form data extraction
- Document analysis
- Content migration

## Async Processing Workflow

**Goal**: Process large documents without timeouts

### Steps
1. **Submit Job**: POST to conversion/extraction endpoint
2. **Get Job ID**: Note the `jobId` from response
3. **Poll Status**: GET `/jobs/{jobId}/status` until `status: "completed"`
4. **Download Result**: GET `/jobs/{jobId}/result`

### Implementation Pattern
```python
# Submit job
job_response = submit_conversion_job(token, file_data)
job_id = job_response['jobId']

# Poll until complete
while True:
    status = get_job_status(token, job_id)
    if status['status'] == 'completed':
        break
    elif status['status'] == 'failed':
        raise Exception(f"Job failed: {status['message']}")
    time.sleep(5)  # Wait 5 seconds before next check

# Download result
result = get_job_result(token, job_id)
```

## Batch Processing Workflow

**Goal**: Process multiple documents efficiently

### Strategy
1. **Queue Jobs**: Submit all files as async jobs
2. **Track Progress**: Monitor all job IDs
3. **Download Results**: Collect completed results
4. **Handle Errors**: Retry failed jobs

### Best Practices
- Use async processing for files > 10MB
- Add delays between API calls (rate limiting)
- Implement retry logic for failed requests
- Log all operations for debugging

## Document Pipeline Workflow

**Goal**: Complete document processing pipeline

### Example: Invoice Processing
1. **Convert**: Word/Excel invoices → PDF
2. **Extract**: Text and table data from PDFs
3. **Validate**: Check extracted data quality
4. **Transform**: Redact sensitive information
5. **Store**: Save processed documents and data

### Integration Points
- **Input**: SharePoint, OneDrive, email attachments
- **Processing**: Platform API operations
- **Output**: Database, CRM, accounting system
- **Notifications**: Email, Teams, Slack alerts
