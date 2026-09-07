#!/usr/bin/env python
"""Platform API client for Nitro Platform integrations."""

from __future__ import annotations

import json
import mimetypes
import uuid
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal, cast

import httpx

from .base_client import BaseOAuthClient

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

# How long to wait for an asynchronous job to finish, in seconds.
JOB_TIMEOUT_SECONDS = 900
HTTP_OK = 200
HTTP_ACCEPTED = 202


class JobFailedError(RuntimeError):
    """An asynchronous Platform API job failed.

    Carries the detail needed to diagnose the failure: the HTTP status, the
    error message returned by the API, and the request ID to quote to support.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        error_type: str | None = None,
        request_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_type = error_type
        self.request_id = request_id


def _str_or_none(value: object) -> str | None:
    """Return the value if it is a string, otherwise None."""
    return value if isinstance(value, str) else None


def _problem_detail(body: str) -> tuple[str | None, str | None]:
    """Pull (error type, human message) out of a Platform API error body."""
    try:
        payload: object = json.loads(body)
    except ValueError:
        return None, None
    if not isinstance(payload, dict):
        return None, None
    data = cast("dict[str, object]", payload)
    error = data.get("error")
    if isinstance(error, dict):
        nested = cast("dict[str, object]", error)
        return _str_or_none(nested.get("type")), _str_or_none(nested.get("title"))
    return _str_or_none(data.get("type")), _str_or_none(data.get("title"))


@dataclass
class PlatformAPIClient(BaseOAuthClient):
    """Synchronous client for Nitro Platform API operations."""

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

        response = self._client.post(
            f"{self._settings.platform_base_url}/{endpoint}",
            headers=headers,
            files=files,
            data=data,
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

        response = self._client.post(
            f"{self._settings.platform_base_url}/{endpoint}",
            headers=headers,
            files=files,
            data=data,
        )

        response.raise_for_status()
        result = response.json()

        # Download from S3 URL
        download_url = result["result"]["file"]["URL"]
        download_response = httpx.get(download_url)
        download_response.raise_for_status()
        return download_response.content

    def _iter_job_events(self, status_url: str, request_id: str) -> Iterator[dict[str, Any]]:
        """Yield job events from the server-sent-events status stream."""
        headers = {
            "Authorization": f"Bearer {self._get_token()}",
            "Accept": "text/event-stream",
            "X-Analytics-Session-Id": request_id,
        }
        timeout = httpx.Timeout(30.0, read=float(JOB_TIMEOUT_SECONDS))
        with self._client.stream("GET", status_url, headers=headers, timeout=timeout) as response:
            if response.status_code not in {200, 202}:
                response.read()
                error_type, title = _problem_detail(response.text)
                raise JobFailedError(
                    title or f"Job status request failed with HTTP {response.status_code}",
                    status_code=response.status_code,
                    error_type=error_type,
                    request_id=request_id,
                )
            data_lines: list[str] = []
            for raw_line in response.iter_lines():
                line = raw_line.rstrip("\r")
                if line:
                    if line.startswith("data:"):
                        data_lines.append(line[5:].lstrip())
                    continue
                if data_lines:
                    payload = "\n".join(data_lines).strip()
                    data_lines = []
                    if payload:
                        yield cast("dict[str, Any]", json.loads(payload))
            if data_lines:
                payload = "\n".join(data_lines).strip()
                if payload:
                    yield cast("dict[str, Any]", json.loads(payload))

    def _await_job(self, status_url: str, request_id: str) -> tuple[bool, str]:
        """Follow a job to completion. Returns (failed, result location)."""
        for event in self._iter_job_events(status_url, request_id):
            status = event.get("status")
            if status == "running":
                continue
            if status in {"completed", "failed"}:
                return status == "failed", str(event["location"])
        raise JobFailedError(
            "The job status stream closed before the job finished.",
            request_id=request_id,
        )

    def _request_async_bytes(
        self,
        endpoint: Literal["conversions", "extractions", "transformations"],
        method: str,
        file_path: Path,
        params: dict[str, Any] | None = None,
    ) -> bytes:
        """Run an operation as an asynchronous job and return the resulting bytes.

        Unlike the synchronous helpers, this submits the work with
        ``Prefer: respond-async`` and then follows the job to completion, so
        documents large enough to exceed the synchronous request window are
        processed successfully instead of timing out on the client.

        Raises:
            JobFailedError: if the submission, the job, or the download fails.
        """
        request_id = str(uuid.uuid4())
        headers = {
            "Authorization": f"Bearer {self._get_token()}",
            "Prefer": "respond-async",
            "X-Analytics-Session-Id": request_id,
        }
        mime_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
        files = {"file": (file_path.name, file_path.read_bytes(), mime_type)}
        data = {"method": method, "params": json.dumps(params or {})}

        submit = self._client.post(
            f"{self._settings.platform_base_url}/{endpoint}",
            headers=headers,
            files=files,
            data=data,
        )
        if submit.status_code != HTTP_ACCEPTED:
            error_type, title = _problem_detail(submit.text)
            raise JobFailedError(
                title or f"Job submission failed with HTTP {submit.status_code}",
                status_code=submit.status_code,
                error_type=error_type,
                request_id=request_id,
            )

        status_url = submit.headers.get("Location")
        if not status_url:
            raise JobFailedError(
                "The job was accepted but no Location header was returned.",
                status_code=submit.status_code,
                request_id=request_id,
            )

        failed, result_url = self._await_job(status_url, request_id)
        auth = {
            "Authorization": f"Bearer {self._get_token()}",
            "X-Analytics-Session-Id": request_id,
        }

        if failed:
            error = self._client.get(result_url, headers=auth)
            error_type, title = _problem_detail(error.text)
            raise JobFailedError(
                title or "The job failed.",
                status_code=error.status_code,
                error_type=error_type,
                request_id=request_id,
            )

        # Without this Accept header the result endpoint returns the job's
        # JSON representation rather than the output file itself.
        result = self._client.get(
            result_url, headers={**auth, "Accept": "application/octet-stream"}
        )
        if result.status_code != HTTP_OK:
            error_type, title = _problem_detail(result.text)
            raise JobFailedError(
                title or f"Result download failed with HTTP {result.status_code}",
                status_code=result.status_code,
                error_type=error_type,
                request_id=request_id,
            )
        return result.content

    def optimize(self, file_path: Path, profile: str = "minimal-file-size") -> bytes:
        """Optimize (compress) a PDF using an optimization profile.

        Profiles are ``minimal-file-size``, ``web``, ``print``, ``archive`` and
        ``mixed-raster-content``. This runs as an asynchronous job, so it works
        for large documents as well as small ones.

        Args:
            file_path: The PDF to optimize.
            profile: The optimization profile to apply.

        Returns:
            The optimized PDF as bytes.
        """
        return self._request_async_bytes(
            "transformations", "optimize", file_path, {"profile": profile}
        )

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

    def redact(self, file_path: Path, redactions: list[dict[str, Any]]) -> bytes:
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

    def set_properties(self, file_path: Path, properties: dict[str, str]) -> bytes:
        """Set or clear PDF metadata properties."""
        return self._request_bytes(
            "transformations", "set-properties", file_path, properties
        )

    def merge(self, file_paths: list[Path]) -> bytes:
        """Merge multiple PDFs."""
        headers = {"Authorization": f"Bearer {self._get_token()}"}

        # Open files with context manager
        opened_files = [fp.open("rb") for fp in file_paths]
        try:
            files = [("file", (f.name, f)) for f in opened_files]
            data = {"method": "merge", "params": "{}"}

            response = self._client.post(
                f"{self._settings.platform_base_url}/transformations",
                headers=headers,
                files=files,
                data=data,
            )
            response.raise_for_status()
            return response.content
        finally:
            for f in opened_files:
                f.close()
