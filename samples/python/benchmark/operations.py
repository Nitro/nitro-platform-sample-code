"""Running one optimization job and recording an honest result for it.

The point of this module is that a result is only ever recorded as a success
when the API actually returned a usable PDF for the profile that was asked for.
Anything else, including an empty or non-PDF response, is recorded as a failure
with the detail needed to diagnose it.
"""

import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

import httpx2

from api.platform_api import JobFailedError

if TYPE_CHECKING:
    from pathlib import Path

    from services import OptimizerService

PDF_MAGIC = b"%PDF-"

# Optimization profiles, with what each one is suited for.
PROFILES: dict[str, str] = {
    "minimal-file-size": (
        "Aggressively downsamples images and strips redundant data to produce the "
        "smallest possible file. Use when size is the priority."
    ),
    "web": (
        "Balances file size against on-screen quality. Use for web publishing, "
        "email and online viewing."
    ),
    "print": (
        "Keeps print-resolution images, favouring fidelity over size. Use when the "
        "document will be printed at high quality."
    ),
    "archive": (
        "Reduces size while keeping the document suitable for long-term storage and "
        "conversion to PDF/A. Use for archival and compliance."
    ),
    "mixed-raster-content": (
        "MRC compression, which separates text from the background layer. Use for "
        "scanned documents."
    ),
}


@dataclass(slots=True, kw_only=True)
class _OperationBase:
    """Fields common to every operation result, success or failure."""

    file: str
    operation: str
    variant: str  # the profile that actually produced this row, never assumed
    input_bytes: int
    duration_ms: int


@dataclass(slots=True, kw_only=True)
class OperationSuccess(_OperationBase):
    """A successful run: the API returned a usable PDF for the profile asked for."""

    output_bytes: int
    reduction_pct: float
    output_path: str
    status: Literal["success"] = "success"


@dataclass(slots=True, kw_only=True)
class OperationFailure(_OperationBase):
    """A failed run, with the detail needed to diagnose it."""

    http_status: int | None
    error_type: str | None
    error_message: str
    request_id: str | None
    job_id: str | None = None
    status: Literal["failed"] = "failed"


type OperationResult = OperationSuccess | OperationFailure


def _is_pdf(content: bytes) -> bool:
    """Report whether the bytes look like a real, non-empty PDF."""
    return len(content) > 0 and content.lstrip()[:5] == PDF_MAGIC


def _failure(
    pdf_path: Path,
    profile: str,
    input_bytes: int,
    duration_ms: int,
    *,
    http_status: int | None,
    error_type: str | None,
    error_message: str,
    request_id: str | None,
) -> OperationFailure:
    """Build a failed result."""
    return OperationFailure(
        file=pdf_path.name,
        operation="optimize",
        variant=profile,
        input_bytes=input_bytes,
        duration_ms=duration_ms,
        http_status=http_status,
        error_type=error_type,
        error_message=error_message,
        request_id=request_id,
    )


def run_optimize(
    optimizer_service: OptimizerService, pdf_path: Path, profile: str, output_dir: Path
) -> OperationResult:
    """Optimize one PDF with one profile and record what actually happened.

    Args:
        optimizer_service: The Optimizer service to run the job through.
        pdf_path: The PDF to optimize.
        profile: The optimization profile to apply.
        output_dir: Where the optimized PDF is written.

    Returns:
        An OperationResult, marked failed unless a valid PDF came back.
    """
    input_bytes = pdf_path.stat().st_size
    started = time.perf_counter()

    try:
        content = optimizer_service.optimize(pdf_path, profile)
    except JobFailedError as exc:
        return _failure(
            pdf_path,
            profile,
            input_bytes,
            int((time.perf_counter() - started) * 1000),
            http_status=exc.status_code,
            error_type=exc.error_type,
            error_message=exc.message,
            request_id=exc.request_id,
        )
    except httpx2.HTTPStatusError as exc:
        # e.g. a 401 from the token endpoint: caught here so a failed run is
        # recorded rather than the traceback (with its locals) being dumped.
        return _failure(
            pdf_path,
            profile,
            input_bytes,
            int((time.perf_counter() - started) * 1000),
            http_status=exc.response.status_code,
            error_type="HTTPStatusError",
            error_message=f"HTTP {exc.response.status_code} from {exc.request.url.path}",
            request_id=None,
        )
    except httpx2.HTTPError as exc:
        return _failure(
            pdf_path,
            profile,
            input_bytes,
            int((time.perf_counter() - started) * 1000),
            http_status=None,
            error_type=type(exc).__name__,
            error_message=str(exc) or "The request could not be completed.",
            request_id=None,
        )

    duration_ms = int((time.perf_counter() - started) * 1000)

    # A 2xx is not a success on its own: the body has to be a usable PDF.
    if not _is_pdf(content):
        return _failure(
            pdf_path,
            profile,
            input_bytes,
            duration_ms,
            http_status=200,
            error_type="InvalidOutput",
            error_message=f"The response was not a valid PDF ({len(content)} bytes).",
            request_id=None,
        )

    target_dir = output_dir / "optimize" / profile
    target_dir.mkdir(parents=True, exist_ok=True)
    output_path = target_dir / pdf_path.name
    output_path.write_bytes(content)

    output_bytes = len(content)
    reduction = (1.0 - output_bytes / input_bytes) * 100.0 if input_bytes else 0.0

    return OperationSuccess(
        file=pdf_path.name,
        operation="optimize",
        variant=profile,
        input_bytes=input_bytes,
        output_bytes=output_bytes,
        reduction_pct=round(reduction, 2),
        duration_ms=duration_ms,
        output_path=str(output_path),
    )
