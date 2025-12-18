#!/usr/bin/env python3
"""
📝 SEND POLICY DOCUMENTS TO MULTIPLE EMPLOYEES
===============================================

This script sends multiple policy documents from a folder to multiple employees for their
signature and saves each signed copy in a dedicated folder per employee.

WORKFLOW:
  1. Load all policy documents from a folder (PDF, Word documents)
  2. Convert non-PDF documents to PDF automatically
  3. Read employee list from CSV file (name, email)
  4. For each employee:
     - Create signature envelope with ALL policy documents
     - Send for electronic signature
     - Monitor until signed
     - Save signed documents as ZIP (contains all signed PDFs + audit trail)

EMPLOYEE CSV FORMAT:
  name,email
  John Doe,john.doe@company.com
  Jane Smith,jane.smith@company.com
  Bob Johnson,bob.johnson@company.com

USAGE:
  python send_policies_to_employees.py <policies_folder> <employees_csv> <output_folder>

EXAMPLE:
  python send_policies_to_employees.py ./policies ./employees.csv ./newJoinersJanuary

OUTPUT STRUCTURE:
  newJoinersJanuary/
  ├── john-doe/
  │   ├── signed-policies.zip          # ZIP file with all signed documents
  │   ├── signed-documents/             # Extracted contents:
  │   │   ├── policy1-signed.pdf        #   - Signed policy documents
  │   │   ├── policy2-signed.pdf
  │   │   └── audit-trail.pdf           #   - Audit trail document
  │   ├── envelope-info.json
  │   └── envelope-id.txt
  ├── jane-smith/
  │   ├── signed-policies.zip
  │   ├── signed-documents/
  │   ├── envelope-info.json
  │   └── envelope-id.txt
  └── bob-johnson/
      ├── signed-policies.zip
      ├── signed-documents/
      ├── envelope-info.json
      └── envelope-id.txt

NOTE: The Nitro Sign API returns signed envelopes as ZIP files containing all signed PDFs
      plus an audit trail. The script automatically extracts the ZIP for convenience.
"""

import sys
import csv
import time
import json
import base64
from pathlib import Path
from api.sign_api import SignAPIClient


# def load_employees_from_csv(csv_path: Path) -> list[dict]:
#     """Load employee list from CSV file.
    
#     Args:
#         csv_path: Path to CSV file with columns: name, email
        
#     Returns:
#         List of employee dictionaries with 'name' and 'email'
#     """
#     employees = []
    
#     with open(csv_path, 'r', encoding='utf-8') as f:
#         reader = csv.DictReader(f)
        
#         # Validate CSV has required columns
#         if 'name' not in reader.fieldnames or 'email' not in reader.fieldnames:
#             raise ValueError('CSV must have "name" and "email" columns')
        
#         for row in reader:
#             name = row['name'].strip()
#             email = row['email'].strip()
            
#             if name and email and '@' in email:
#                 employees.append({'name': name, 'email': email})
#             else:
#                 print(f'  ⚠️  Skipping invalid row: {row}')
    
#     return employees


def create_employee_folder_name(employee_name: str) -> str:
    """Convert employee name to folder-safe name.
    
    Args:
        employee_name: Full name like "John Doe"
        
    Returns:
        Folder-safe name like "john-doe"
    """
    return employee_name.lower().replace(' ', '-').replace('.', '')

def load_policy_documents_from_folder(policies_folder: Path) -> list[dict]:
   
    print(f'📂 Loading policy documents from: {policies_folder}')
    
    # Find only PDF files (no conversion for now, keep it simple)
    policy_files = list(policies_folder.glob('*.pdf'))
    
    if not policy_files:
        raise ValueError(f'No PDF files found in {policies_folder}')
    
    print(f'  ✅ Found {len(policy_files)} PDF document(s)')
    
    documents = []
    for pf in policy_files:
        print(f'     • {pf.name}')
        
        # Read binary content
        with open(pf, 'rb') as f:
            binary_data = f.read()
        
        documents.append({
            'name': pf.name,
            'binary': binary_data,
            'path': str(pf)  # Convert PosixPath to string
        })
    
    print()
    return documents


def create_signature_envelope(
    sign_client: SignAPIClient,
    documents: list[Path],  # List of file paths
    employee_name: str,
    employee_email: str
) -> tuple[str, list[str]]:  # Returns envelope_id and list of document_ids
    """Create envelope and upload documents.
    
    Args:
        sign_client: Sign API client instance
        documents: List of Path objects to PDF files
        employee_name: Full name of employee
        employee_email: Email address of employee
        
    Returns:
        Tuple of (envelope_id, list of document_ids)
    """
    
    # ============================================================
    # STEP 1: Create empty envelope
    # ============================================================
    print(f'   📝 Step 1: Creating empty envelope...')

    envelope_data = {
        'name': f'Company Policies - {employee_name}',
        'mode': "parallel",
        'notification': {
            'subject': f'Please sign: Company Policies',
            'body': f'Hello {employee_name}, please review and sign the attached company policy documents.'
        }
    }
    print(f'   🔍 DEBUG - Sending: {envelope_data}')
    
    envelope = sign_client.create_envelope(envelope_data)
    envelope_id = envelope['ID']
    print(f'   ✅ Envelope created: {envelope_id}')
    
    # ============================================================
    # STEP 2: Upload documents to envelope
    # ============================================================
    print(f'\n   📄 Step 2: Uploading {len(documents)} document(s)...')
    document_ids = []
    
    for i, doc in enumerate(documents, 1):
        doc_name = doc['name']
        doc_binary = doc['binary']
        doc_path = doc['path']
        
        print(f'      [{i}/{len(documents)}] Uploading: {doc_name}')
        
        # Prepare metadata as JSON string
        import json
        metadata = json.dumps({'name': doc_name})
        
        # Prepare form-data with binary content
        files = {
            'metadata': ('metadata', metadata, 'application/json'),
            'payload': (doc_name, doc_binary, 'application/pdf')
        }
        
        headers = {'Authorization': f'Bearer {sign_client._get_token()}'}
        
        import requests
        response = requests.post(
            f'{sign_client.base_url}/sign/envelopes/{envelope_id}/documents',
            headers=headers,
            files=files
        )
        
        response.raise_for_status()
        document = response.json()
        
        document_id = document['ID']
        document_ids.append(document_id)
        print(f'      ✅ Uploaded: {document_id}')
    
    return envelope_id, document_ids



def monitor_envelope(sign_client: SignAPIClient, envelope_id: str, timeout_minutes: int = 60) -> str:
    """Monitor envelope until signed, cancelled, or timeout.
    
    Args:
        sign_client: Sign API client instance
        envelope_id: ID of envelope to monitor
        timeout_minutes: Maximum time to wait
        
    Returns:
        Final status: 'sealed', 'cancelled', 'timeout', or 'error'
    """
    check_interval = 30  # seconds
    max_checks = (timeout_minutes * 60) // check_interval
    
    for i in range(max_checks):
        try:
            envelope = sign_client.get_envelope(envelope_id)
            status = envelope['status']
            
            if status == 'sealed':
                return 'sealed'
            elif status in ['cancelled', 'rejected', 'deleted']:
                return 'cancelled'
            
            if i < max_checks - 1:
                time.sleep(check_interval)
                
        except Exception as e:
            print(f'      ⚠️  Error checking status: {e}')
            return 'error'
    
    return 'timeout'


def download_signed_document(
    sign_client: SignAPIClient,
    envelope_id: str,
    output_folder: Path,
    document_name: str
) -> Path:
    """Download sealed envelope to employee folder.
    
    The API returns a ZIP file containing:
    - All signed PDF documents
    - Audit trail document
    
    Args:
        sign_client: Sign API client instance
        envelope_id: ID of sealed envelope
        output_folder: Employee-specific output folder
        document_name: Name for the saved file (should end with .zip)
        
    Returns:
        Path to saved ZIP file
    """
    # Download sealed envelope (returns ZIP file)
    zip_bytes = sign_client.download_sealed_envelope(envelope_id)
    
    # Save as ZIP file
    if not document_name.endswith('.zip'):
        document_name = document_name.replace('.pdf', '.zip')
    
    output_path = output_folder / document_name
    output_path.write_bytes(zip_bytes)
    
    # Also extract the ZIP contents for convenience
    import zipfile
    extract_folder = output_folder / 'signed-documents'
    extract_folder.mkdir(exist_ok=True)
    
    with zipfile.ZipFile(output_path, 'r') as zip_ref:
        zip_ref.extractall(extract_folder)
    
    print(f'   📦 ZIP saved to: {output_path}')
    print(f'   📂 Extracted to: {extract_folder}')
    
    # Save envelope metadata
    envelope = sign_client.get_envelope(envelope_id)
    json_path = output_folder / 'envelope-info.json'
    json_path.write_text(json.dumps(envelope, indent=2))
    
    return output_path


def process_employee(
    sign_client: SignAPIClient,
    documents: list[str],
    employee: dict,
    base_output_folder: Path,
    timeout_minutes: int,
    wait_for_signatures: bool
) -> dict:
    """Process signature request for one employee with multiple documents.
    
    Args:
        sign_client: Sign API client instance
        documents: List of policy document dictionaries
        employee: Employee dict with 'name' and 'email'
        base_output_folder: Base folder for all signed documents
        timeout_minutes: How long to wait for signature
        wait_for_signatures: If True, wait for signature; if False, just send
        
    Returns:
        Result dictionary with status and details
    """
    name = employee['name']
    email = employee['email']
    
    print(f'\n📧 Processing: {name} ({email})')
    print(f'   {"─" * 60}')
    
    try:
        # Create employee-specific output folder
        folder_name = create_employee_folder_name(name)
        employee_folder = base_output_folder / folder_name
        employee_folder.mkdir(parents=True, exist_ok=True)
        
        # Documents are already loaded and passed as parameter
        # STEP 1 & 2: Create envelope and upload documents
        print(f'   📝 Creating envelope for {name}...')
        envelope_id, document_ids = create_signature_envelope(sign_client, documents, name, email)
        print(f'   ✅ Envelope created: {envelope_id}')
        print(f'   ✅ Documents uploaded: {len(document_ids)}')
        for i, doc_id in enumerate(document_ids, 1):
            print(f'      [{i}] {doc_id}')
        
        # ============================================================
        # STEP 3: Add participant (signer)
        # ============================================================
        print(f'\n   👤 Step 3: Adding participant...')
        
        participant_data = {
            'email': email,
            'role': 'signer',
            'name': name
        }
        
        print(f'   🔍 DEBUG - Participant data: {participant_data}')
        
        participant = sign_client.create_participant(envelope_id, participant_data)
        participant_id = participant['ID']
        print(f'   ✅ Participant added: {participant_id}')
        
        # ============================================================
        # STEP 4: Add signature fields to each document
        # ============================================================
        print(f'\n   ✍️  Step 4: Adding signature fields...')
        
        for i, doc_id in enumerate(document_ids, 1):
            print(f'      [{i}/{len(document_ids)}] Adding fields for document {doc_id}')
            
            # Add signature field
            signature_field_data = {
                'participantID': participant_id,
                'type': 'signature',
                'label': 'Your Signature',
                'page': 1,
                'boundingBox': [200, 300, 60, 40],  # [x, y, width, height]
                'required': True
            }        
     
            signature_field = sign_client.create_field(envelope_id, doc_id, signature_field_data)
            print(f'         ✅ Signature field: {signature_field["ID"]}')
        
            # Add date field
            date_field_data = {
                'participantID': participant_id,
                'type': 'date',
                'label': 'Date Signed',
                'page': 1,
                'boundingBox': [320, 650, 150, 50],  # [x, y, width, height]
                'required': True,
                'format': 'MM/DD/YYYY'  
            }
                        
            date_field = sign_client.create_field(envelope_id, doc_id, date_field_data)
            print(f'         ✅ Date field: {date_field["ID"]}')
        
        
        envelope = sign_client.get_envelope(envelope_id)
        print(f"!!!!!!!!!!!!!!!!!Envelope status: {envelope['status']}")
        # ============================================================
        # STEP 5: Send envelope for signing
        # ============================================================
        print(f'\n   📤 Step 5: Sending envelope for signing...')
        sign_client.send_for_signing(envelope_id)
        print(f'   ✅ Envelope sent to {email}')
        envelope = sign_client.get_envelope(envelope_id)

        print(f"!!!!!!!!!!!!!!!!!Envelope status: {envelope['status']}")
        
        # ============================================================
        # STEP 6: Monitor status and download signed document
        # ============================================================
        if wait_for_signatures:
            print(f'\n   ⏳ Step 6: Monitoring signing status...')
            print(f'   💡 Employee will receive email at {email}')
            print(f'   ⏱️  Checking every 30 seconds (timeout: {timeout_minutes} min)...')
            
            status = monitor_envelope(sign_client, envelope_id, timeout_minutes)
            
            if status == 'sealed':
                print(f'   ✅ Document signed!')
                print(f'   📥 Downloading signed document...')
                
                output_path = download_signed_document(
                    sign_client,
                    envelope_id,
                    employee_folder,
                    'signed-policies.pdf'
                )
                
                print(f'   💾 Saved to: {output_path}')
                
                return {
                    'status': 'success',
                    'name': name,
                    'email': email,
                    'envelope_id': envelope_id,
                    'output_path': str(output_path),
                    'num_documents': len(document_ids)
                }
            elif status == 'timeout':
                print(f'   ⏱️  Timeout - not signed yet')
                return {
                    'status': 'timeout',
                    'name': name,
                    'email': email,
                    'envelope_id': envelope_id,
                    'folder': str(employee_folder),
                    'num_documents': len(document_ids)
                }
            elif status == 'cancelled':
                print(f'   ❌ Envelope cancelled or rejected')
                return {
                    'status': 'cancelled',
                    'name': name,
                    'email': email,
                    'envelope_id': envelope_id
                }
            else:
                print(f'   ❌ Error monitoring envelope')
                return {
                    'status': 'error',
                    'name': name,
                    'email': email,
                    'envelope_id': envelope_id
                }
        else:
            # Not waiting for signatures
            print(f'   ✅ Envelope sent (not waiting for signature)')
            return {
                'status': 'sent',
                'name': name,
            'email': email,
            'envelope_id': envelope_id,
            'folder': str(employee_folder),
            'num_documents': len(documents)
        }
        
    
            
    except Exception as e:
        print(f'   ❌ Error: {e}')
        return {
            'status': 'failed',
            'name': name,
            'email': email,
            'error': str(e)
        }


def display_summary(results: list[dict], wait_for_signatures: bool):
    """Display final summary of all operations.
    
    Args:
        results: List of result dictionaries
        wait_for_signatures: Whether signatures were waited for
    """
    print('\n' + '=' * 70)
    print('📊 SUMMARY')
    print('=' * 70)
    
    success = [r for r in results if r['status'] == 'success']
    created = [r for r in results if r['status'] == 'created']  # NEW: for Step 1 testing
    sent = [r for r in results if r['status'] == 'sent']
    timeout = [r for r in results if r['status'] == 'timeout']
    cancelled = [r for r in results if r['status'] == 'cancelled']
    failed = [r for r in results if r['status'] == 'failed']
    
    # TESTING MODE: Show created envelopes
    print(f'✅ Envelopes created (Step 1): {len(created)}')
    print(f'✅ Completed and signed: {len(success)}')
    print(f'📤 Sent (not waiting): {len(sent)}')
    print(f'⏱️  Timeout: {len(timeout)}')
    print(f'❌ Cancelled/Rejected: {len(cancelled)}')
    print(f'❌ Failed: {len(failed)}')
    
    print()
    
    # Show created envelopes (Step 1 testing)
    if created:
        print('✅ Envelopes created (testing Step 1):')
        for r in created:
            num_docs = r.get('num_documents', 0)
            print(f"   • {r['name']}: envelope {r['envelope_id']} ({num_docs} documents pending)")
            print(f"     Folder: {r['folder']}")
        print()
    
    # Show successful completions
    if success:
        print('✅ Signed documents saved to:')
        for r in success:
            num_docs = r.get('num_documents', 0)
            print(f"   • {r['name']}: {r['output_path']} ({num_docs} documents)")
        print()
    
    # Show timeouts
    if timeout:
        print('⏱️  Not signed yet (check these later):')
        for r in timeout:
            print(f"   • {r['name']}: envelope {r['envelope_id']}")
            print(f"     Command: python download_envelope.py {r['envelope_id']} {r['folder']}/signed-policies.pdf")
        print()
    
    # Show sent (not waiting)
    if sent:
        print('📤 Envelopes sent (check status later):')
        for r in sent:
            num_docs = r.get('num_documents', 0)
            print(f"   • {r['name']}: envelope {r['envelope_id']} ({num_docs} documents)")
            print(f"     Folder: {r['folder']}")
        print()
    
    # Show failures
    if failed:
        print('❌ Failed to process:')
        for r in failed:
            print(f"   • {r['name']} ({r['email']}): {r.get('error', 'Unknown error')}")
        print()
    
    print('=' * 70)


def main():
    # Check command-line arguments
    if len(sys.argv) < 4:
        print('Usage: python send_policies_to_employees.py <policies_folder> <employees_csv> <output_folder> [--no-wait]')
        sys.exit(1)
    
    # Parse arguments
    policies_folder = Path(sys.argv[1])
    employees_csv = Path(sys.argv[2])
    output_folder = Path(sys.argv[3])
    wait_for_signatures = '--no-wait' not in sys.argv
    
    # Validate inputs
    if not policies_folder.exists() or not policies_folder.is_dir():
        print(f'❌ Policies folder not found: {policies_folder}')
        sys.exit(1)
    
    if not employees_csv.exists():
        print(f'❌ Employees CSV not found: {employees_csv}')
        sys.exit(1)
    
    # Display header
    print('=' * 70)
    print('📝 SEND POLICY DOCUMENTS TO MULTIPLE EMPLOYEES')
    print('=' * 70)
    print(f'Policies folder: {policies_folder}')
    print(f'Employees list: {employees_csv}')
    print(f'Output folder: {output_folder}')
    print(f'Wait for signatures: {"Yes" if wait_for_signatures else "No (send only)"}')
    print('=' * 70)
    print()
    
    try:
        # Load employees
        print('👥 Loading employees from CSV...')
        employees = [{'name': "Isadora", 'email': "isamap2410@gmail.com"}, ]
                    #  {'name': "John Doe", 'email': "john.doe@example.com"}
        
        
        # load_employees_from_csv(employees_csv)
        print(f'  ✅ Found {len(employees)} employee(s)')
        
        if len(employees) == 0:
            print('❌ No valid employees found in CSV')
            sys.exit(1)
        
        # Load and prepare all policy documents
        print()
        documents = load_policy_documents_from_folder(policies_folder)
        
        # Create output folder
        output_folder.mkdir(parents=True, exist_ok=True)
        
        # Initialize Sign API client
        sign_client = SignAPIClient()
        
        # Process each employee
        print()
        print('=' * 70)
        print(f'📤 SENDING TO {len(employees)} EMPLOYEE(S)')
        print('=' * 70)
        
        timeout_minutes = 60 if wait_for_signatures else 0
        results = []
        
        for i, employee in enumerate(employees, 1):
            print(f'[{i}/{len(employees)}]', end=' ')
            result = process_employee(
                sign_client,
                documents,
                employee,
                output_folder,
                timeout_minutes,
                wait_for_signatures
            )
            results.append(result)
        
        # Display summary
        display_summary(results, wait_for_signatures)
        
        # Save results to JSON
        results_file = output_folder / 'processing-results.json'
        results_file.write_text(json.dumps(results, indent=2))
        print(f'📋 Full results saved to: {results_file}')
        print()
        
    except KeyboardInterrupt:
        print('\n\n⚠️  Interrupted by user')
        sys.exit(1)
    except Exception as e:
        print(f'\n❌ Error: {e}')
        sys.exit(1)


if __name__ == '__main__':
    main()
