# Python Examples

Python examples for integrating with the Nitro Platform API.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Copy and configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

3. Run the quickstart example:
   ```bash
   python quickstart.py
   ```

## Files

- `quickstart.py` - Basic authentication and API call example
- `convert_document.py` - Document conversion example
- `async_job.py` - Async job processing example
- `requirements.txt` - Python dependencies
- `.env.example` - Environment variables template

## Examples

### Basic Authentication
```python
token = get_access_token(client_id, client_secret)
```

### Convert Document
```python
result = convert_document(token, file_path, output_format='pdf')
```

### Handle Async Jobs
```python
job_id = start_conversion_job(token, file_path)
result = poll_job_until_complete(token, job_id)
```
