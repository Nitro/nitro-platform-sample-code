# Postman Collection

This folder contains the Postman collection for the Nitro Platform API with examples for all major endpoints.

## Getting Started

### 1. Import the Collection

1. Open Postman
2. Click **Import** in the top left
3. Select `Platform-API.postman_collection.json`
4. The collection will appear in your workspace

### 2. Configure Collection Variables

1. Click on the collection name in the sidebar
2. Go to the **Variables** tab
3. Set the **CURRENT VALUE** for these variables:

| Variable | Description | Example Value |
|----------|-------------|---------------|
| `baseUrl` | API base URL | `https://api.gonitro.dev` |
| `clientID` | Your client ID | `your-client-id` |
| `clientSecret` | Your client secret | `your-client-secret` |
| `repoPath` | Absolute path to this repo | `/Users/you/github/nitro-platform-integrations` |
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

To run them:
1. Select any request (e.g., **Word → PDF**)
2. Go to **Body** tab → **form-data**
3. **Manually select the file** using the file picker:
   - Click on the file field
   - Navigate to your `repoPath` folder
   - Select the appropriate file from the [File Reference Guide](#file-reference-guide) below
4. Click **Send**

### Example Workflow

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

**Sample Files**: The repository includes sample files in the `test_files/` folder at the root level that you can use for testing:
- `Analysis.docx` - Word document
- `Feedback.xlsx` - Excel spreadsheet
- `SamplePPTX.pptx` - PowerPoint presentation
- `SampleResume.pdf` - PDF with text and PII
- `Sample Tables.pdf` - PDF with tables
- `BOB - Student-Loan-Application-Form.pdf` - PDF with form fields

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

## Test Files Reference

When testing endpoints in Postman, use these test files for each operation:

### Conversions

| Endpoint | Test File | Location |
|----------|-----------|----------|
| Word → PDF | Analysis.docx | `test_files/test-batch/Analysis.docx` |
| Excel → PDF | Feedback.xlsx | `test_files/test-batch/Feedback.xlsx` |
| PowerPoint → PDF | SamplePPTX.pptx | `test_files/SamplePPTX.pptx` |
| Image → PDF | GoNitro.png | `test_files/GoNitro.png` |
| PDF → Word | SampleResume.pdf | `test_files/test-pdfs/SampleResume.pdf` |
| PDF → Excel | Sample Tables.pdf | `test_files/test-pdfs/Sample Tables.pdf` |
| PDF → Image | SampleResume.pdf | `test_files/test-pdfs/SampleResume.pdf` |

### Extractions

| Endpoint | Test File | Location |
|----------|-----------|----------|
| Extract PDF Text | SampleResume.pdf | `test_files/test-pdfs/SampleResume.pdf` |
| Extract PDF Form Data | BOB - Student-Loan-Application-Form.pdf | `test_files/test-pdfs/BOB - Student-Loan-Application-Form.pdf` |
| Extract PDF Table Data | Sample Tables.pdf | `test_files/test-pdfs/Sample Tables.pdf` |
| Extract and Autodetect Bounding Boxes for PII | SampleResume.pdf | `test_files/test-pdfs/SampleResume.pdf` |
| Extract Bounding Boxes for Strings | SampleResume.pdf | `test_files/test-pdfs/SampleResume.pdf` |
| Get PDF Properties | SampleResume.pdf | `test_files/test-pdfs/SampleResume.pdf` |
| Set PDF Properties | SampleResume.pdf | `test_files/test-pdfs/SampleResume.pdf` |

### Transformations

| Endpoint | Test File | Location |
|----------|-----------|----------|
| Redact Bounding boxes (scrub PII) | SampleResume.pdf | `test_files/test-pdfs/SampleResume.pdf` |
| Compress | BOB - Student-Loan-Application-Form.pdf | `test_files/test-pdfs/BOB - Student-Loan-Application-Form.pdf` |
| Flatten | Sample Tables.pdf | `test_files/test-pdfs/Sample Tables.pdf` |
| Rotate Pages | SampleResume.pdf | `test_files/test-pdfs/SampleResume.pdf` |
| Delete Pages | SampleResume.pdf | `test_files/test-pdfs/SampleResume.pdf` |
| Split | SampleResume.pdf | `test_files/test-pdfs/SampleResume.pdf` |
| Merge | Sample Tables.pdf + SampleResume.pdf | `test_files/test-pdfs/` (multiple files) |
| Password Protect | SampleResume.pdf | `test_files/test-pdfs/SampleResume.pdf` |
| Password Remove | PDF-withpassword.pdf | `test_files/PDF-withpassword.pdf` |

### Available Test Files

All test files are located in the `test_files/` directory:
```
test_files/
├── test-pdfs/
│   ├── SampleResume.pdf              # Resume with text and PII
│   ├── Sample Tables.pdf             # PDF with table data
│   └── BOB - Student-Loan-Application-Form.pdf  # PDF with form fields
├── test-batch/
│   ├── Analysis.docx                 # Word document
│   └── Feedback.xlsx                 # Excel spreadsheet
├── SamplePPTX.pptx                   # PowerPoint presentation
├── GoNitro.png                       # Sample image
└── PDF-withpassword.pdf              # Password-protected PDF
```