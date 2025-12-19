#!/usr/bin/env python3
"""
📝 EMPLOYEE POLICY ONBOARDING
==============================

This script exemplifies a typical HR onboarding workflow for new employees.
As an HR professional, it's necessary to ensure all new hires review and sign 
required company policies before their start date. Manual distribution and 
tracking of signatures is time-consuming and error-prone, especially when 
onboarding multiple employees simultaneously.

This workflow automates policy distribution and signature collection. The script 
processes each new employee individually - for every person in the CSV file, it 
creates a signature envelope containing all company policy documents, sends it 
via email with signature fields pre-configured, monitors the signing status, and 
automatically downloads the signed documents once completed. Each employee's 
signed policies are organized in their own folder, creating an audit-ready 
archive of onboarding documentation.


NOTE: To run this script and see the complete workflow, you must provide a CSV file 
with valid employee names and email addresses. The script will send actual signature 
requests to these email addresses and wait for them to be signed.

EMPLOYEE CSV FORMAT:
  name,email
  John Doe,john.doe@company.com
  Jane Smith,jane.smith@company.com
  Bob Johnson,bob.johnson@company.com

USAGE:
  python employee_policy_onboarding.py <policies_folder> <employees_csv>

EXAMPLE:
  python employee_policy_onboarding.py ./policies ./new_hires_jan2025.csv

OUTPUT STRUCTURE:
  output/
  ├── john-doe/
  │   ├── signed-documents/
  │       ├── code-of-conduct-signed.pdf
  │       ├── confidentiality-agreement-signed.pdf
  │       └── audit-trail.pdf
  ├── jane-smith/
      ├── signed-documents/
"""

import sys
import csv
import time
import json
import base64
from pathlib import Path
from api.sign_api import SignAPIClient
from helper_functions.sign_helpers import (
    load_employees_from_csv,
    load_policy_documents_from_folder,
    create_employee_folder_name,
    create_signature_envelope,
    add_signature_fields_to_documents,
    send_and_monitor_envelope,
    download_signed_document,
    log_step
)







def main():
    # Check command-line arguments
    if len(sys.argv) != 3:
        print('Usage: python send_policies_to_employees.py <policies_folder> <employees_csv>')
        sys.exit(1)
    
    # Parse arguments
    policies_folder = Path(sys.argv[1])
    employees_csv = Path(sys.argv[2])
    output_folder = Path('output')
    
    # Validate inputs
    if not policies_folder.exists() or not policies_folder.is_dir():
        print(f'❌ Policies folder not found: {policies_folder}')
        sys.exit(1)
    
    if not employees_csv.exists():
        print(f'❌ Employees CSV not found: {employees_csv}')
        sys.exit(1)
    
    # Display header
    print('=' * 60)
    print('📝 SEND POLICIES TO EMPLOYEES')
    print('=' * 60)
    print(f'Policies: {policies_folder}')
    print(f'Employees: {employees_csv}')
    print(f'Output: {output_folder}')
    print('=' * 60)
    print()
    
    try:
        # Load employees and documents
        employees = load_employees_from_csv(employees_csv)
        print(f'👥 Found {len(employees)} employee(s)\n')
        
        documents = load_policy_documents_from_folder(policies_folder)
        
        # Create output folder
        output_folder.mkdir(parents=True, exist_ok=True)
        
        # Initialize Sign API client
        sign_client = SignAPIClient()
        
        # Process each employee
        print('=' * 60)
        print(f'📤 PROCESSING {len(employees)} EMPLOYEE(S)')
        print('=' * 60)
        
        success_count = 0
        failed_count = 0
        
        for i, employee in enumerate(employees, 1):
            name = employee['name']
            email = employee['email']
            
            print(f"\n[{i}/{len(employees)}] {name}")
            
            try:
                # Create employee-specific output folder
                folder_name = create_employee_folder_name(name)
                employee_folder = output_folder / folder_name
                employee_folder.mkdir(parents=True, exist_ok=True)
                
                # Create envelope and upload documents
                log_step('📝 Creating envelope...')
                envelope_id, document_ids = create_signature_envelope(sign_client, documents, name, email)
                
                # Add participant (signer)
                log_step('👤 Adding signer...')
                participant_data = {'email': email, 'role': 'signer', 'name': name}
                participant = sign_client.create_participant(envelope_id, participant_data)
                participant_id = participant['ID']
                
                # Add signature fields to all documents
                log_step('✍️  Adding fields...')
                add_signature_fields_to_documents(sign_client, envelope_id, document_ids, participant_id)
                
                # Send and monitor envelope
                log_step('📤 Sending...')
                status = send_and_monitor_envelope(sign_client, envelope_id, email, timeout_minutes=60)
                
                if status != 'sealed':
                    raise Exception(f'Envelope not signed: {status}')
                
                # Download signed documents
                log_step('📥 Downloading...')
                download_signed_document(sign_client, envelope_id, employee_folder, 'signed-policies.zip')
                
                print(f"  ✅ Completed\n")
                success_count += 1
                
            except Exception as e:
                print(f"  ❌ FAILED: {e}\n")
                failed_count += 1
        
        # Display summary
        print('=' * 60)
        print(f"✅ {success_count} employee(s) completed")
        if failed_count > 0:
            print(f"❌ {failed_count} failed")
        print(f"📂 Output: {output_folder.absolute()}")
        print('=' * 60)
        
    except KeyboardInterrupt:
        print('\n\n⚠️  Interrupted by user')
        sys.exit(1)
    except Exception as e:
        print(f'\n❌ Error: {e}')
        sys.exit(1)


if __name__ == '__main__':
    main()
