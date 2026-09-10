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
from pathlib import Path
from typing import Annotated, Literal, cast, get_args

import typer

from benchmark import (
    OperationResult,
    run_optimize,
    summarise,
    write_csv,
    write_html,
    write_summary_csv,
)
from benchmark.operations import PROFILES
from helper_functions.document_helpers import validate_and_setup
from services import OptimizerService

Profile = Literal[
    "minimal-file-size",
    "web",
    "print",
    "archive",
    "mixed-raster-content",
]


def _validate_profiles(values: list[str]) -> list[str]:
    """Reject any --profile value that isn't a supported Optimize profile.

    typer can't type a repeatable option as list[Literal[...]] directly (it
    only supports "complex" sub-types for single-value options), so the CLI
    surface stays list[str] and this callback is the actual gate.
    """
    valid = set(get_args(Profile))
    for value in values:
        if value not in valid:
            msg = f"{value!r} is not a valid profile; choose from {', '.join(sorted(valid))}"
            raise typer.BadParameter(msg)
    return values


def _echo_profiles(profiles: list[Profile]) -> None:
    """Show which profiles will run, with what each is suited for."""
    typer.echo("Profiles to run:")
    for profile in profiles:
        typer.echo(f"  • {profile} — {PROFILES[profile]}")
    typer.echo("")


def _run_all(
    optimizer_service: OptimizerService,
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
            result = run_optimize(optimizer_service, file_path, chosen, output_folder)
            prefix = f"[{run}/{total_runs}] {file_path.name} ({chosen}) ..."
            took = f"🚀 took ~{result.duration_ms / 1000:.1f}s"
            if result.status == "success":
                typer.echo(f"{prefix} ✅ {result.reduction_pct:.1f}% smaller, {took}")
            else:
                typer.echo(f"{prefix} ❌ FAILED: {result.error_message}, {took}")
            results.append(result)
    return results


def main(
    input_folder: Annotated[Path, typer.Argument(help="Folder containing the PDFs to benchmark")],
    output_folder: Annotated[Path, typer.Argument(help="Folder for optimized PDFs and the report")],
    profiles: Annotated[
        tuple[str],
        typer.Option(
            "--profile",
            "-p",
            help="Optimization profile to run; repeat to benchmark several",
            callback=_validate_profiles,
        ),
    ] = ("minimal-file-size",),
    *,
    open_report: Annotated[
        bool, typer.Option(help="Open the HTML report in a browser when done")
    ] = False,
) -> None:
    """Benchmark the Optimize API on a folder of PDFs and produce an HTML report."""
    validated_profiles = cast(list[Profile], list(profiles))
    files = sorted(validate_and_setup(input_folder, output_folder, file_patterns=["*.pdf"]))
    typer.echo(f"📋 Found {len(files)} PDF(s) in {input_folder}\n")
    _echo_profiles(validated_profiles)

    # Initialize API client (loads credentials from .env)
    with OptimizerService.build() as optimizer_service:
        results = _run_all(optimizer_service, files, validated_profiles, output_folder)

    summary = summarise(results)
    report_path = output_folder / "report.html"
    write_csv(results, output_folder / "results.csv")
    write_summary_csv(summary, output_folder / "summary.csv")
    write_html(results, summary, report_path, default_variant=validated_profiles[0])

    succeeded = sum(1 for r in results if r.status == "success")
    typer.echo("\n" + "=" * 60)
    typer.echo(f"✅ {succeeded}/{len(results)} run(s) succeeded")
    typer.echo(f"📊 Report: {report_path.absolute()}")
    typer.echo("=" * 60)

    if open_report:
        webbrowser.open(report_path.absolute().as_uri())


if __name__ == "__main__":
    typer.run(main)
