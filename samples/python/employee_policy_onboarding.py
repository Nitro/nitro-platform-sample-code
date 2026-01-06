#!/usr/bin/env python3
"""
📝 EMPLOYEE POLICY ONBOARDING
==============================

HR staff must make sure that all new employees review and sign required
company policies before their start date. Manual distribution and manual
tracking of signed documents takes a lot of time and can cause errors. This
is especially true when you onboard many employees at the same time.

This workflow automates the distribution of policies and the collection of signatures.

The script processes one employee at a time. For each employee listed in the CSV file, the script:

Creates a signature envelope that contains all required company policy documents

Sends the envelope by email with signature fields already set

Tracks the signature status

Downloads the signed documents when the signing process is complete

The script saves each employee's signed documents in a separate folder.
This creates an organized and audit-ready record of onboarding
documents.


NOTE: To run this script and view the full workflow, you must provide a
CSV file with valid employee names and email addresses. The script sends
real signature requests to these email addresses and waits for the
employees to sign the documents.


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

from pathlib import Path
from typing import Annotated, Any

import typer

from api.sign_api import SignAPIClient
from helper_functions.sign_helpers import (
    add_signature_fields_to_documents,
    create_employee_folder_name,
    create_signature_envelope,
    download_signed_document,
    load_employees_from_csv,
    load_policy_documents_from_folder,
    log_step,
    send_and_monitor_envelope,
)


class EnvelopeNotSignedError(Exception):
    """Raised when an envelope was not signed in time."""


app = typer.Typer()


def _validate_and_setup_inputs(
    policies_folder: Path, employees_csv: Path
) -> tuple[Path, list[dict[str, str]], list[dict[str, Any]]]:
    """Validate inputs and load data.

    Args:
        policies_folder: Path to folder containing policy PDFs
        employees_csv: Path to CSV file with employee data

    Returns:
        Tuple of (output_folder, employees, documents)
    """
    # Validate inputs
    if not policies_folder.exists() or not policies_folder.is_dir():
        print(f'❌ Policies folder not found: {policies_folder}')
        raise typer.Exit(code=1)

    if not employees_csv.exists():
        print(f'❌ Employees CSV not found: {employees_csv}')
        raise typer.Exit(code=1)

    # Display header
    output_folder = Path('output')
    print('=' * 60)
    print('📝 SEND POLICIES TO EMPLOYEES')
    print('=' * 60)
    print(f'Policies: {policies_folder}')
    print(f'Employees: {employees_csv}')
    print(f'Output: {output_folder}')
    print('=' * 60)
    print()

    # Load employees and documents
    employees = load_employees_from_csv(employees_csv)
    print(f'👥 Found {len(employees)} employee(s)\n')

    documents = load_policy_documents_from_folder(policies_folder)

    # Create output folder
    output_folder.mkdir(parents=True, exist_ok=True)

    return output_folder, employees, documents


def _process_employee_onboarding(
    sign_client: SignAPIClient,
    employee: dict[str, str],
    documents: list[dict[str, Any]],
    output_folder: Path,
    *,
    employee_num: int,
    total_employees: int,
) -> None:
    """Process onboarding workflow for a single employee.

    Args:
        sign_client: Sign API client instance
        employee: Employee data dict with 'name' and 'email'
        documents: List of policy documents to send
        output_folder: Base output folder for signed documents
        employee_num: Current employee number (for display)
        total_employees: Total number of employees (for display)

    Raises:
        EnvelopeNotSignedError: If envelope is not signed within timeout
        Exception: For other errors during processing
    """
    name = employee['name']
    email = employee['email']

    print(f'\n[{employee_num}/{total_employees}] {name}')

    # Create employee-specific output folder
    employee_folder = output_folder / create_employee_folder_name(name)
    employee_folder.mkdir(parents=True, exist_ok=True)

    # Create envelope and upload documents
    log_step('📝 Creating envelope...')
    envelope_id, document_ids = create_signature_envelope(sign_client, documents, name, email)

    # Add participant (signer)
    log_step('👤 Adding signer...')
    participant_id = sign_client.create_participant(
        envelope_id, {'email': email, 'role': 'signer', 'name': name}
    )['ID']

    # Add signature fields to all documents
    log_step('✍️  Adding fields...')
    add_signature_fields_to_documents(sign_client, envelope_id, document_ids, participant_id)

    # Send and monitor envelope
    log_step('📤 Sending...')
    status = send_and_monitor_envelope(sign_client, envelope_id, email, timeout_minutes=60)

    if status != 'sealed':
        raise EnvelopeNotSignedError(f'Envelope not signed: {status}')

    # Download signed documents
    log_step('📥 Downloading...')
    download_signed_document(sign_client, envelope_id, employee_folder, 'signed-policies.zip')

    print('  ✅ Completed\n')


@app.command()
def main(
    policies_folder: Annotated[
        Path, typer.Argument(help='Folder containing policy PDF documents')
    ],
    employees_csv: Annotated[
        Path, typer.Argument(help='CSV file with employee data (name,email columns)')
    ],
) -> None:
    """Send company policy documents to employees for electronic signature via Sign API."""
    try:
        # Validate inputs and load data
        output_folder, employees, documents = _validate_and_setup_inputs(
            policies_folder, employees_csv
        )

        # Initialize Sign API client
        sign_client = SignAPIClient()

        # Process each employee
        print("=" * 60)
        print(f"📤 PROCESSING {len(employees)} EMPLOYEE(S)")
        print("=" * 60)

        success_count = 0
        failed_count = 0

        for i, employee in enumerate(employees, 1):
            try:
                _process_employee_onboarding(
                    sign_client,
                    employee,
                    documents,
                    output_folder,
                    employee_num=i,
                    total_employees=len(employees),
                )
                success_count += 1

            except Exception as e:  # noqa: BLE001
                print(f"  ❌ FAILED: {e}\n")
                failed_count += 1

        # Display summary
        print("=" * 60)
        print(f"✅ {success_count} employee(s) completed")
        if failed_count > 0:
            print(f"❌ {failed_count} failed")
        print(f"📂 Output: {output_folder.absolute()}")
        print("=" * 60)

    except KeyboardInterrupt:
        print('\n\n⚠️  Interrupted by user')
        raise typer.Exit(code=1) from None
    except Exception as e:  # noqa: BLE001
        print(f'\n❌ Error: {e}')
        raise typer.Exit(code=1) from None


if __name__ == '__main__':
    app()
