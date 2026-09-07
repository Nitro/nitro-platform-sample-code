#!/usr/bin/env python3
"""
📉 OPTIMIZE API BENCHMARK
=========================

This script shows how well the Nitro Optimize API compresses your own PDFs.

When you are evaluating a PDF compression service, published numbers only go
so far: what matters is how much smaller YOUR documents get. This script runs
a folder of PDFs through the Optimize API and reports the size reduction for
every file, so you can judge the results on your own content.

Each PDF is submitted as an asynchronous optimization job (so large documents
work too), the optimized file is saved to the output folder, and the run ends
with three artefacts: a per-file CSV, a per-profile summary CSV, and a
self-contained HTML report with the headline numbers, a distribution chart
and a filterable per-file table. The report opens in your browser when done.

BENCHMARK FEATURES:
  ✓ Runs every optimization profile you select (default: minimal-file-size)
  ✓ Per-file size reduction, timing and failure detail
  ✓ Self-contained HTML report you can share as one file

USAGE:
  python optimize_benchmark.py <input_folder> <output_folder> [--profile ...]

EXAMPLES:
  python optimize_benchmark.py ./sample_pdfs ./output
  python optimize_benchmark.py ./sample_pdfs ./output -p minimal-file-size -p web
"""

import webbrowser
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Annotated

import typer

from api.platform_api import PlatformAPIClient
from benchmark import run_optimize, summarise, write_csv, write_html, write_summary_csv
from benchmark.operations import PROFILES
from helper_functions.document_helpers import validate_and_setup

if TYPE_CHECKING:
    from benchmark import OperationResult


class Profile(str, Enum):
    """Optimization profiles offered by the Optimize API."""

    MINIMAL_FILE_SIZE = "minimal-file-size"
    WEB = "web"
    PRINT = "print"
    ARCHIVE = "archive"
    MIXED_RASTER_CONTENT = "mixed-raster-content"


app = typer.Typer()

HTTP_UNAUTHORIZED = 401


def _echo_profiles(profiles: list[Profile]) -> None:
    """Show which profiles will run, with what each is suited for."""
    typer.echo("Profiles to run:")
    for profile in profiles:
        typer.echo(f"  • {profile.value} — {PROFILES[profile.value]}")
    typer.echo("")


def _run_all(
    client: PlatformAPIClient,
    files: list[Path],
    profiles: list[Profile],
    output_folder: Path,
) -> list[OperationResult]:
    """Run every file through every selected profile, echoing progress."""
    results: list[OperationResult] = []
    total_runs = len(files) * len(profiles)
    run = 0
    for chosen in profiles:
        for file_path in files:
            run += 1
            typer.echo(f"[{run}/{total_runs}] {file_path.name} ({chosen.value}) ...", nl=False)
            result = run_optimize(client, file_path, chosen.value, output_folder)
            if result.status == "success" and result.reduction_pct is not None:
                typer.echo(f" ✅ {result.reduction_pct:.1f}% smaller")
            else:
                typer.echo(f" ❌ FAILED: {result.error_message}")
            results.append(result)
            if result.http_status == HTTP_UNAUTHORIZED and "/oauth/token" in (
                result.error_message or ""
            ):
                typer.echo(
                    "\n❌ Authentication failed - check PLATFORM_CLIENT_ID and "
                    "PLATFORM_CLIENT_SECRET in your .env file."
                )
                raise typer.Exit(1)
    return results


@app.command()
def main(
    input_folder: Annotated[Path, typer.Argument(help="Folder containing the PDFs to benchmark")],
    output_folder: Annotated[Path, typer.Argument(help="Folder for optimized PDFs and the report")],
    profile: Annotated[
        list[Profile] | None,
        typer.Option(
            "--profile",
            "-p",
            help="Optimization profile to run; repeat to benchmark several",
        ),
    ] = None,
    *,
    open_report: Annotated[
        bool, typer.Option(help="Open the HTML report in a browser when done")
    ] = True,
) -> None:
    """Benchmark the Optimize API on a folder of PDFs and produce an HTML report."""
    profiles = profile or [Profile.MINIMAL_FILE_SIZE]
    files = sorted(validate_and_setup(input_folder, output_folder, file_patterns=["*.pdf"]))
    typer.echo(f"📋 Found {len(files)} PDF(s) in {input_folder}\n")
    _echo_profiles(profiles)

    # Initialize API client (loads credentials from .env)
    client = PlatformAPIClient()
    results = _run_all(client, files, profiles, output_folder)

    summary = summarise(results)
    report_path = output_folder / "report.html"
    write_csv(results, output_folder / "results.csv")
    write_summary_csv(summary, output_folder / "summary.csv")
    write_html(results, summary, report_path, default_variant=profiles[0].value)

    succeeded = sum(1 for r in results if r.status == "success")
    typer.echo("\n" + "=" * 60)
    typer.echo(f"✅ {succeeded}/{len(results)} run(s) succeeded")
    typer.echo(f"📊 Report: {report_path.absolute()}")
    typer.echo("=" * 60)

    if open_report:
        webbrowser.open(report_path.absolute().as_uri())


if __name__ == "__main__":
    app()
