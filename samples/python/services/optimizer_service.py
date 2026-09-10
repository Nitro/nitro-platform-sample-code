"""Service for running Optimize API jobs against a PDF."""

import contextlib
from collections.abc import Generator
from dataclasses import dataclass
from pathlib import Path
from typing import Self

from api.platform_api import PlatformAPIClient


@dataclass
class OptimizerService:
    """Optimize one PDF with a profile and save the result to disk."""

    _client: PlatformAPIClient

    @classmethod
    @contextlib.contextmanager
    def build(cls) -> Generator[Self]:
        """Build a service backed by an authenticated Platform API client."""
        with PlatformAPIClient.build() as client:
            yield cls(client)

    def optimize(self, pdf_path: Path, profile: str) -> bytes:
        """Optimize ``pdf_path`` with ``profile`` and return the resulting PDF bytes."""
        return self._client.optimize(pdf_path, profile)

    def run(self, pdf_path: Path, profile: str, output_dir: Path) -> Path:
        """Optimize ``pdf_path`` with ``profile`` and write the result into ``output_dir``.

        Args:
            pdf_path: The PDF to optimize.
            profile: The optimization profile to apply.
            output_dir: Directory the optimized PDF is written into.

        Returns:
            Path to the optimized PDF that was written.
        """
        optimized = self._client.optimize(pdf_path, profile)
        output_path = output_dir / pdf_path.name
        output_path.write_bytes(optimized)
        return output_path
