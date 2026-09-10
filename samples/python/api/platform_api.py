#!/usr/bin/env python
"""Platform API client for Nitro Platform integrations."""

import json
import uuid
from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated, Any, Literal

import httpx2
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn

from .base_client import BaseOAuthClient, FatalError

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path


class _JobEventBase(BaseModel):
    """Fields shared by every job status-stream SSE event."""

    model_config = ConfigDict(extra="ignore", frozen=True)


class ProgressUpdate(_JobEventBase):
    """The job is still running, with a progress fraction."""

    event: Literal["progress-update"]
    status: Literal["running"]
    progress: float = Field(ge=0.0, le=1.0)


class StatusUpdate(_JobEventBase):
    """A plain status update; ``progress`` is only present while running."""

    event: Literal["status-update"]
    status: Literal["running", "completed", "failed"]
    progress: float | None = Field(default=None, ge=0.0, le=1.0)


class Redirect(_JobEventBase):
    """The terminal event: where to fetch the result or the error detail."""

    event: Literal["redirect"]
    status: Literal["completed", "failed"]
    location: str


type JobEvent = Annotated[ProgressUpdate | StatusUpdate | Redirect, Field(discriminator="event")]


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


class ProblemDetail(BaseModel):
    """A Platform API error body: either ``{type, title}`` directly, or nested under ``error``."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    type: str | None = None
    title: str | None = None
    error: ProblemDetail | None = None


def _problem_detail(body: bytes) -> tuple[str | None, str | None]:
    """Pull (error type, human message) out of a Platform API error body."""
    try:
        problem = ProblemDetail.model_validate_json(body)
    except ValidationError:
        return None, None
    if problem.error is not None:
        return problem.error.type, problem.error.title
    return problem.type, problem.title


def _get_mime_type_from_path(path: Path) -> str:
    """Look up the standard MIME type for a file's extension."""
    extension_mime_type_map = {
        "pdf": "application/pdf",
        "doc": "application/msword",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "xls": "application/vnd.ms-excel",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "ppt": "application/vnd.ms-powerpoint",
        "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "txt": "text/plain",
        "csv": "text/csv",
        "html": "text/html",
        "htm": "text/html",
        "zip": "application/zip",
    }
    extension = path.suffix.lower().removeprefix(".")
    if not extension:
        raise FatalError(
            f"{path.name!r} has no file extension; give it a proper name — "
            "we can't guess a content type without one."
        )
    mime_type = extension_mime_type_map.get(extension)
    if mime_type is None:
        raise FatalError(f"Unsupported file type: .{extension}")
    return mime_type


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
        response = self._client.post(
            endpoint,
            files={
                "file": self._upload(file_path, _get_mime_type_from_path(file_path), file_path.name)
            },
            data={"method": method, "params": json.dumps(params or {})},
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
        response = self._client.post(
            endpoint,
            files={
                "file": self._upload(file_path, _get_mime_type_from_path(file_path), file_path.name)
            },
            data={"method": method, "params": json.dumps(params or {})},
        )

        response.raise_for_status()
        result = response.json()

        # Download from S3 URL
        download_url = result["result"]["file"]["URL"]
        return self._download_from_url(download_url, description=f"Downloading {file_path.name}...")

    def _iter_job_events(
        self, status_url: str, request_id: str, *, job_timeout_seconds: float = 300
    ) -> Iterator[JobEvent]:
        """Yield job events from the server-sent-events status stream."""
        headers = {"X-Analytics-Session-Id": request_id}
        type_adapter = TypeAdapter[JobEvent](JobEvent)
        timeout = httpx2.Timeout(30.0, read=job_timeout_seconds)
        with self._client.sse(status_url, headers=headers, timeout=timeout) as event_source:
            response = event_source.response
            if response.status_code != httpx2.codes.OK.value:
                response.read()
                error_type, title = _problem_detail(response.content)
                raise JobFailedError(
                    title or f"Job status request failed with HTTP {response.status_code}",
                    status_code=response.status_code,
                    error_type=error_type,
                    request_id=request_id,
                )
            for sse in event_source:
                yield type_adapter.validate_json(sse.data)

    def _await_job(
        self, status_url: str, request_id: str, *, description: str = "Running..."
    ) -> Redirect:
        """Follow a job to completion, showing a progress bar. Returns the terminal event."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            transient=True,
        ) as progress:
            task = progress.add_task(description, total=1.0)
            for event in self._iter_job_events(status_url, request_id):
                if isinstance(event, Redirect):
                    progress.update(task, completed=1.0)
                    return event
                if event.progress is not None:
                    progress.update(task, completed=event.progress)
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
        request_id = str(uuid.uuid7())
        response = self._client.post(
            endpoint,
            headers={"Prefer": "respond-async", "X-Analytics-Session-Id": request_id},
            files={
                "file": self._upload(file_path, _get_mime_type_from_path(file_path), file_path.name)
            },
            data={"method": method, "params": json.dumps(params or {})},
        )
        if response.status_code != httpx2.codes.ACCEPTED.value:
            error_type, title = _problem_detail(response.content)
            raise JobFailedError(
                title or f"Job submission failed with HTTP {response.status_code}",
                status_code=response.status_code,
                error_type=error_type,
                request_id=request_id,
            )

        status_url = response.headers["Location"]
        redirect = self._await_job(
            status_url, request_id, description=f"Running {file_path.name}..."
        )
        analytics_header = {"X-Analytics-Session-Id": request_id}

        if redirect.status == "failed":
            error = self._client.get(redirect.location, headers=analytics_header)
            error_type, title = _problem_detail(error.content)
            raise JobFailedError(
                title or "The job failed.",
                status_code=error.status_code,
                error_type=error_type,
                request_id=request_id,
            )

        result = self._client.get(redirect.location, headers=analytics_header)
        if result.status_code != httpx2.codes.OK.value:
            error_type, title = _problem_detail(result.content)
            raise JobFailedError(
                title or f"Result download failed with HTTP {result.status_code}",
                status_code=result.status_code,
                error_type=error_type,
                request_id=request_id,
            )

        # Download from S3 URL
        download_url = result.json()["result"]["file"]["URL"]
        return self._download_from_url(
            download_url, description=f"Downloading result for {file_path.name}..."
        )

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
        return self._request_bytes("transformations", "set-properties", file_path, properties)

    def merge(self, file_paths: list[Path]) -> bytes:
        """Merge multiple PDFs."""
        files = [
            (
                "file",
                self._upload(file_path, _get_mime_type_from_path(file_path), file_path.name),
            )
            for file_path in file_paths
        ]
        response = self._client.post(
            "/transformations",
            files=files,
            data={"method": "merge", "params": "{}"},
        )
        response.raise_for_status()
        return response.content
