"""
Sign API helper utilities for envelope operations.
"""

from __future__ import annotations

import csv
import json
import time
import zipfile
from datetime import datetime
from pathlib import Path  # noqa: TC003
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from api.sign_api import SignAPIClient


def create_employee_folder_name(employee_name: str) -> str:
    """Convert employee name to folder-safe name.

    Args:
        employee_name: Full name like "John Doe"

    Returns:
        Folder-safe name like "john-doe"
    """
    return employee_name.lower().replace(" ", "-").replace(".", "")


def load_employees_from_csv(csv_path: Path) -> list[dict]:
    """Load employee list from CSV file.

    Args:
        csv_path: Path to CSV file with columns: name, email

    Returns:
        List of employee dictionaries with 'name' and 'email'

    Raises:
        ValueError: If CSV format is invalid
    """
    if not csv_path.exists():
        raise ValueError(f"CSV file not found: {csv_path}")

    employees = []

    with csv_path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)

        # Validate CSV has required columns
        if "name" not in reader.fieldnames or "email" not in reader.fieldnames:
            raise ValueError('CSV must have "name" and "email" columns')

        for row in reader:
            name = row["name"].strip()
            email = row["email"].strip()

            if name and email and "@" in email:
                employees.append({"name": name, "email": email})

    if not employees:
        raise ValueError("No valid employees found in CSV")

    return employees


def load_policy_documents_from_folder(policies_folder: Path) -> list[dict]:
    """Load all PDF files from the policies folder.

    Args:
        policies_folder: Path to folder containing policy PDFs

    Returns:
        List of document dictionaries with 'name', 'binary', and 'path'
    """
    policy_files = list(policies_folder.glob("*.pdf"))

    if not policy_files:
        raise ValueError(f"No PDF files found in {policies_folder}")

    print(f"📂 Found {len(policy_files)} policy document(s)\n")

    documents = []
    for pf in policy_files:
        with pf.open("rb") as f:
            binary_data = f.read()

        documents.append({"name": pf.name, "binary": binary_data, "path": str(pf)})

    return documents


def create_signature_envelope(
    sign_client: SignAPIClient,
    documents: list[dict],
    employee_name: str,
    _employee_email: str,
) -> tuple[str, list[str]]:
    """Create envelope and upload documents.

    Args:
        sign_client: Sign API client instance
        documents: List of document dicts with 'name', 'binary', 'path'
        employee_name: Full name of employee
        employee_email: Email address of employee

    Returns:
        Tuple of (envelope_id, list of document_ids)
    """
    # Create empty envelope
    envelope_data = {
        "name": f"Company Policies - {employee_name}",
        "mode": "parallel",
        "notification": {
            "subject": "Please sign: Company Policies",
            "body": (
                f"Hello {employee_name}, please review and sign the attached "
                "company policy documents."
            ),
        },
    }

    envelope = sign_client.create_envelope(envelope_data)
    envelope_id = envelope["ID"]

    # Upload documents to envelope
    document_ids = []

    for doc in documents:
        doc_name = doc["name"]
        doc_binary = doc["binary"]

        # Prepare metadata as JSON string
        metadata = json.dumps({"name": doc_name})

        # Prepare form-data with binary content
        files = {
            "metadata": ("metadata", metadata, "application/json"),
            "payload": (doc_name, doc_binary, "application/pdf"),
        }

        headers = {"Authorization": f"Bearer {sign_client._get_token()}"}

        import httpx

        response = httpx.post(
            f"{sign_client.base_url}/sign/envelopes/{envelope_id}/documents",
            headers=headers,
            files=files,
        )

        response.raise_for_status()
        document = response.json()

        document_id = document["ID"]
        document_ids.append(document_id)

    return envelope_id, document_ids


def add_signature_fields_to_documents(
    sign_client: SignAPIClient,
    envelope_id: str,
    document_ids: list[str],
    participant_id: str,
) -> None:
    """Add signature and date fields to all documents in envelope.

    Args:
        sign_client: Sign API client instance
        envelope_id: ID of the envelope
        document_ids: List of document IDs to add fields to
        participant_id: ID of the participant who will sign
    """
    for doc_id in document_ids:
        # Add signature field
        signature_field_data = {
            "participantID": participant_id,
            "type": "signature",
            "label": "Your Signature",
            "page": 1,
            "boundingBox": [200, 300, 60, 40],
            "required": True,
        }
        sign_client.create_field(envelope_id, doc_id, signature_field_data)

        # Add date field
        date_field_data = {
            "participantID": participant_id,
            "type": "date",
            "label": "Date Signed",
            "page": 1,
            "boundingBox": [320, 650, 150, 50],
            "required": True,
            "format": "MM/DD/YYYY",
        }
        sign_client.create_field(envelope_id, doc_id, date_field_data)


def send_and_monitor_envelope(
    sign_client: SignAPIClient, envelope_id: str, email: str, timeout_minutes: int = 60
) -> str:
    """Send envelope and monitor until signed or timeout.

    Args:
        sign_client: Sign API client instance
        envelope_id: ID of envelope to send
        email: Email address of recipient
        timeout_minutes: Maximum time to wait

    Returns:
        Final status: 'sealed', 'cancelled', 'timeout', or 'error'
    """
    # Send envelope
    sign_client.send_for_signing(envelope_id)

    # Log send time and status
    send_time = datetime.now(tz=datetime.UTC).strftime("%Y-%m-%d %H:%M:%S")
    print(f"     ✅ Sent at: {send_time}")
    print(f"     📧 Email sent to: {email}")
    print(f"     🔗 Envelope ID: {envelope_id}")

    # Check initial status
    envelope = sign_client.get_envelope(envelope_id)
    print(f"     📊 Status: {envelope['status']}")

    # Monitor for completion
    print("  ⏳ Waiting for signature...")
    print(f"     ⏱️  Checking every 30 seconds (timeout: {timeout_minutes} minutes)")

    status = monitor_envelope(sign_client, envelope_id, timeout_minutes)

    # Log final status
    completion_time = datetime.now(tz=datetime.UTC).strftime("%Y-%m-%d %H:%M:%S")
    print(f"     📊 Final status: {status}")
    print(f"     🕐 Completed at: {completion_time}")

    return status


def monitor_envelope(
    sign_client: SignAPIClient, envelope_id: str, timeout_minutes: int = 60
) -> str:
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
            status = envelope["status"]

            if status == "sealed":
                return "sealed"
            if status in ["cancelled", "rejected", "deleted"]:
                return "cancelled"

            if i < max_checks - 1:
                time.sleep(check_interval)

        except Exception as e:  # noqa: BLE001
            print(f"      ⚠️  Error checking status: {e}")
            return "error"

    return "timeout"


def download_signed_document(
    sign_client: SignAPIClient, envelope_id: str, output_folder: Path, document_name: str
) -> Path:
    """Download sealed envelope and extract signed documents.

    The API returns a ZIP file containing:
    - All signed PDF documents
    - Audit trail document

    This function extracts the contents and removes the ZIP file.

    Args:
        sign_client: Sign API client instance
        envelope_id: ID of sealed envelope
        output_folder: Employee-specific output folder
        document_name: Name for the saved file (should end with .zip)

    Returns:
        Path to extracted documents folder
    """
    # Download sealed envelope (returns ZIP file)
    zip_bytes = sign_client.download_sealed_envelope(envelope_id)

    # Save as temporary ZIP file
    if not document_name.endswith(".zip"):
        document_name = document_name.replace(".pdf", ".zip")

    temp_zip_path = output_folder / document_name
    temp_zip_path.write_bytes(zip_bytes)

    # Extract the ZIP contents
    extract_folder = output_folder / "signed-documents"
    extract_folder.mkdir(exist_ok=True)

    with zipfile.ZipFile(temp_zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_folder)

    # Delete the ZIP file after extraction
    temp_zip_path.unlink()

    # Save envelope metadata
    envelope = sign_client.get_envelope(envelope_id)
    json_path = output_folder / "envelope-info.json"
    json_path.write_text(json.dumps(envelope, indent=2))

    print(f"     💾 Extracted to: {extract_folder}")

    return extract_folder


def log_step(message: str) -> None:
    """Log a processing step with consistent formatting.

    Args:
        message: The message to log
    """
    print(f"  {message}")
