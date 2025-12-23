#!/usr/bin/env python
"""Sign API client for Nitro Sign integrations (eSignature operations)."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import httpx
from dotenv import load_dotenv

if TYPE_CHECKING:
    from pathlib import Path

load_dotenv()


@dataclass
class SignAPIClient:
    """Synchronous client for Nitro Sign API operations (eSignature/envelopes)."""

    base_url: str = field(
        default_factory=lambda: os.getenv("PLATFORM_BASE_URL", "https://api.gonitro.dev")
    )
    client_id: str = field(default_factory=lambda: os.getenv("PLATFORM_CLIENT_ID"))
    client_secret: str = field(default_factory=lambda: os.getenv("PLATFORM_CLIENT_SECRET"))
    _token: str | None = field(default=None, init=False)
    _token_expiry: float = field(default=0, init=False)

    def _get_token(self) -> str:
        """Get or refresh OAuth2 access token."""
        if self._token and time.time() < self._token_expiry:
            return self._token

        response = httpx.post(
            f"{self.base_url}/oauth/token",
            json={"clientID": self.client_id, "clientSecret": self.client_secret},
        )
        response.raise_for_status()
        data = response.json()
        self._token = data["accessToken"]
        self._token_expiry = time.time() + data.get("expiresIn", 3600) - 60
        return self._token

    def _request(
        self,
        method: str,
        endpoint: str,
        json_data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make authenticated API request returning JSON."""
        headers = {"Authorization": f"Bearer {self._get_token()}"}

        response = httpx.request(
            method=method,
            url=f"{self.base_url}{endpoint}",
            headers=headers,
            json=json_data,
            params=params,
        )

        try:
            response.raise_for_status()
        except httpx.HTTPError:
            # Try to get error details from response
            try:
                error_detail = response.json()
                print(f"   ❌ API Error Response: {error_detail}")
            except Exception:  # noqa: BLE001
                print(f"   ❌ API Error (no JSON): {response.text}")
            raise

        return response.json()

    def _request_bytes(
        self, method: str, endpoint: str, params: dict[str, Any] | None = None
    ) -> bytes:
        """Make authenticated API request returning binary data."""
        headers = {"Authorization": f"Bearer {self._get_token()}"}

        response = httpx.request(
            method=method, url=f"{self.base_url}{endpoint}", headers=headers, params=params
        )

        response.raise_for_status()
        return response.content

    # ========== Envelope Management ==========

    def list_envelopes(
        self, page_after: str | None = None, page_before: str | None = None
    ) -> dict[str, Any]:
        """List all envelopes with cursor-based pagination.

        Args:
            page_after: Cursor token to get items after the last item from previous response
            page_before: Cursor token to get items before the last item from previous response

        Returns:
            Dict with 'items' (list of envelopes) and optional 'nextPage' (cursor token)
        """
        params = {}
        if page_after:
            params["pageAfter"] = page_after
        elif page_before:
            params["pageBefore"] = page_before

        return self._request("GET", "/sign/envelopes", params=params)

    def create_envelope(self, envelope_data: dict[str, Any]) -> dict[str, Any]:
        """Create a new envelope.

        Args:
            envelope_data: Envelope configuration including name, documents, participants, fields

        Returns:
            Created envelope with ID and status
        """
        return self._request("POST", "/sign/envelopes", json_data=envelope_data)

    def get_envelope(self, envelope_id: str) -> dict[str, Any]:
        """Get envelope details by ID.

        Args:
            envelope_id: UUID of the envelope

        Returns:
            Envelope details including status, participants, documents
        """
        return self._request("GET", f"/sign/envelopes/{envelope_id}")

    def update_envelope(self, envelope_id: str, updates: dict[str, Any]) -> dict[str, Any]:
        """Update an envelope.

        Args:
            envelope_id: UUID of the envelope
            updates: Fields to update (name, participants, etc.)

        Returns:
            Updated envelope data
        """
        return self._request("PATCH", f"/sign/envelopes/{envelope_id}", json_data=updates)

    def delete_envelope(self, envelope_id: str) -> None:
        """Delete an envelope by ID.

        Args:
            envelope_id: UUID of the envelope
        """
        headers = {"Authorization": f"Bearer {self._get_token()}"}
        response = httpx.delete(f"{self.base_url}/sign/envelopes/{envelope_id}", headers=headers)
        response.raise_for_status()

    # ========== Document Management ==========

    def create_document(
        self, envelope_id: str, file_path: Path, document_name: str | None = None
    ) -> dict[str, Any]:
        """Upload a document to an envelope using form-data.

        Args:
            envelope_id: ID of the envelope
            file_path: Path to the PDF file to upload
            document_name: Optional custom name for the document

        Returns:
            Created document with ID
        """
        if document_name is None:
            document_name = file_path.name

        # Read the binary content of the PDF file
        with file_path.open("rb") as f:
            pdf_binary = f.read()

        # Prepare metadata as JSON string
        metadata = json.dumps({"name": document_name})

        # Prepare form-data with binary content
        files = {
            "metadata": ("metadata", metadata, "application/json"),
            "payload": (file_path.name, pdf_binary, "application/pdf"),
        }

        headers = {"Authorization": f"Bearer {self._get_token()}"}

        response = httpx.post(
            f"{self.base_url}/sign/envelopes/{envelope_id}/documents", headers=headers, files=files
        )

        response.raise_for_status()
        return response.json()

    # ========== Participant Management ==========

    def create_participant(
        self, envelope_id: str, participant_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Add a participant to an envelope.

        Args:
            envelope_id: ID of the envelope
            participant_data: Participant configuration with role, email, name

        Returns:
            Created participant with ID
        """
        return self._request(
            "POST", f"/sign/envelopes/{envelope_id}/participants", json_data=participant_data
        )

    # ========== Field Management ==========

    def create_field(
        self, envelope_id: str, document_id: str, field_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Add a signature field to a document in an envelope.

        Args:
            envelope_id: ID of the envelope
            document_id: ID of the document
            field_data: Field configuration with boundingBox, participantID, type, page

        Returns:
            Created field with ID
        """
        return self._request(
            "POST",
            f"/sign/envelopes/{envelope_id}/documents/{document_id}/fields",
            json_data=field_data,
        )

    # ========== Envelope Actions ==========

    def send_for_signing(self, envelope_id: str) -> dict[str, Any]:
        """Send envelope to participants for signing.

        This transitions the envelope from 'drafted' to 'sent' status.

        Args:
            envelope_id: UUID of the envelope

        Returns:
            Updated envelope with 'sent' status
        """
        # The correct endpoint uses a colon before 'send-for-signing'
        return self._request("POST", f"/sign/envelopes/{envelope_id}:send-for-signing")

    def cancel_envelope(self, envelope_id: str) -> dict[str, Any]:
        """Cancel an envelope that was sent for signing.

        Args:
            envelope_id: UUID of the envelope

        Returns:
            Envelope with 'cancelled' status
        """
        return self._request("PUT", f"/sign/envelopes/{envelope_id}/cancel")

    def send_reminders(self, envelope_id: str) -> dict[str, Any]:
        """Send reminder notifications to pending signers.

        Args:
            envelope_id: UUID of the envelope

        Returns:
            Confirmation of reminder sent
        """
        return self._request("POST", f"/sign/envelopes/{envelope_id}/reminders")

    # ========== Document Downloads ==========

    def download_sealed_envelope(self, envelope_id: str) -> bytes:
        """Download the sealed (signed and completed) envelope.

        Args:
            envelope_id: UUID of the envelope

        Returns:
            PDF bytes of the sealed document
        """
        # The correct endpoint uses a colon before 'download-sealed'
        return self._request_bytes("GET", f"/sign/envelopes/{envelope_id}:download-sealed")

    def download_original_envelope(self, envelope_id: str) -> bytes:
        """Download the original (unsigned) envelope documents.

        Args:
            envelope_id: UUID of the envelope

        Returns:
            Original document bytes
        """
        # The correct endpoint uses a colon before 'download-original'
        return self._request_bytes("GET", f"/sign/envelopes/{envelope_id}:download-original")
