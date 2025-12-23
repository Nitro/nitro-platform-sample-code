#!/usr/bin/env python
"""Platform API client for Nitro Platform integrations."""

import json
import mimetypes
import os
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal

import requests
from dotenv import load_dotenv

if TYPE_CHECKING:
    from pathlib import Path

load_dotenv()


@dataclass
class PlatformAPIClient:
    """Synchronous client for Nitro Platform API operations."""

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

        response = requests.post(
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
        endpoint: Literal["conversions", "extractions", "transformations"],
        method: str,
        file_path: Path,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make API request with file upload."""
        headers = {"Authorization": f"Bearer {self._get_token()}"}

        # Detect MIME type or use octet-stream as fallback
        mime_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"

        # Read file into memory and include content-type
        files = {"file": (file_path.name, file_path.read_bytes(), mime_type)}
        data = {"method": method, "params": json.dumps(params or {})}

        response = requests.post(
            f"{self.base_url}/{endpoint}", headers=headers, files=files, data=data
        )

        response.raise_for_status()
        return response.json()

    def _request_bytes(
        self,
        endpoint: Literal["conversions", "extractions", "transformations"],
        method: str,
        file_path: Path,
        params: dict[str, Any] | None = None,
    ) -> bytes:
        """Make API request and return raw bytes."""
        headers = {"Authorization": f"Bearer {self._get_token()}"}

        # Detect MIME type or use octet-stream as fallback
        mime_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"

        # Read file into memory and include content-type
        files = {"file": (file_path.name, file_path.read_bytes(), mime_type)}
        data = {"method": method, "params": json.dumps(params or {})}

        response = requests.post(
            f"{self.base_url}/{endpoint}", headers=headers, files=files, data=data
        )

        response.raise_for_status()
        result = response.json()

        # Download from S3 URL
        download_url = result["result"]["file"]["URL"]
        download_response = requests.get(download_url)
        download_response.raise_for_status()
        return download_response.content

    def convert(self, file_path: Path, to_format: str) -> bytes:
        """Convert document to specified format."""
        return self._request_bytes("conversions", "convert", file_path, {"to": to_format})

    def extract_text(self, file_path: Path) -> dict[str, Any]:
        """Extract text from document."""
        return self._request("extractions", "extract-text", file_path)

    def extract_forms(self, file_path: Path) -> dict[str, Any]:
        """Extract form data from PDF."""
        return self._request("extractions", "extract-forms", file_path)

    def extract_tables(self, file_path: Path) -> dict[str, Any]:
        """Extract table data from PDF."""
        return self._request("extractions", "extract-tables", file_path)

    def detect_pii(self, file_path: Path, language: str = "en") -> dict[str, Any]:
        """Detect PII and return bounding boxes."""
        return self._request(
            "extractions", "extract-pii-bounding-boxes", file_path, {"language": language}
        )

    def find_text_boxes(self, file_path: Path, texts: list[str]) -> dict[str, Any]:
        """Find bounding boxes for specified text strings."""
        return self._request(
            "extractions", "extract-text-bounding-boxes", file_path, {"texts": texts}
        )

    def redact(self, file_path: Path, redactions: list[dict]) -> bytes:
        """Redact specified bounding boxes."""
        return self._request_bytes(
            "transformations", "redact", file_path, {"redactions": redactions}
        )

    def password_protect(self, file_path: Path, password: str) -> bytes:
        """Add password protection to PDF."""
        return self._request_bytes(
            "transformations",
            "protect",
            file_path,
            {"ownerPassword": password, "userPassword": password},
        )

    def compress(self, file_path: Path, level: int = 2) -> bytes:
        """Compress PDF (level 1-3)."""
        return self._request_bytes("transformations", "compress", file_path, {"level": level})

    def merge(self, file_paths: list[Path]) -> bytes:
        """Merge multiple PDFs."""
        headers = {"Authorization": f"Bearer {self._get_token()}"}

        # Open files with context manager
        opened_files = [fp.open("rb") for fp in file_paths]
        try:
            files = [("file", f) for f in opened_files]
            data = {"method": "merge", "params": "{}"}

            response = requests.post(
                f"{self.base_url}/transformations", headers=headers, files=files, data=data
            )
            response.raise_for_status()
            return response.content
        finally:
            for f in opened_files:
                f.close()
