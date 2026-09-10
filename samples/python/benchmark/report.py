"""Reporting: per-file CSV, aggregate summary, and a self-contained HTML report.

The HTML report has no external dependencies. The stylesheet and script live
alongside this module in ``assets/`` and are inlined at build time, as is the
logo and every chart, so the finished report is one file that opens straight
from disk and can be handed to someone else as-is.
"""

import base64
import csv
import html
import json
import math
import statistics
from collections import defaultdict
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from .operations import OperationResult, OperationSuccess

if TYPE_CHECKING:
    from collections.abc import Sequence

# Every field either variant can produce; a variant that lacks a given field
# just leaves that CSV column blank (csv.DictWriter's default for missing keys).
CSV_FIELDS = [
    "file",
    "operation",
    "variant",
    "status",
    "input_bytes",
    "output_bytes",
    "reduction_pct",
    "duration_ms",
    "output_path",
    "http_status",
    "error_type",
    "error_message",
    "request_id",
    "job_id",
]
HERE = Path(__file__).resolve().parent
ASSETS = HERE / "assets"
LOGO_PATH = ASSETS / "nitro_logo.png"

# Nitro brand palette.
ORANGE = "#f54811"
ORANGE_SOFT = "#fde9e1"
INK = "#1b1f2e"
INK_SOFT = "#3d4257"
MUTED = "#6b7084"
LINE = "#e6e7ec"
SURFACE = "#ffffff"
CANVAS = "#f6f6f8"
BAR = "#f3946e"  # softer orange for chart bars; brand orange stays for accents
BAD = "#b9bdcb"
# Per-profile series colours, used when several profiles are charted together.
SERIES_COLORS = ("#f3946e", "#4c72b0", "#55a868", "#8172b3", "#c9a227")

BYTES_PER_MB = 1_048_576
BYTES_PER_KB = 1024
DEFAULT_PAGE_SIZE = 10
MAX_COMPLEXITY_BINS = 100

_TABLE_HEADERS = (
    "#",
    "File",
    "Profile",
    "Status",
    "Input",
    "Output",
    "Reduction",
    "Time",
    "Failure detail",
)


# ----------------------------------------------------------------------- csv --
def write_csv(results: list[OperationResult], path: Path) -> None:
    """Write one CSV row per file and profile."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for result in results:
            writer.writerow(asdict(result))


def summarise(results: list[OperationResult]) -> list[dict[str, object]]:
    """Aggregate the results into one row per profile."""
    groups: dict[tuple[str, str], list[OperationResult]] = defaultdict(list)
    for result in results:
        groups[result.operation, result.variant].append(result)

    rows: list[dict[str, object]] = []
    for (operation, variant), items in sorted(groups.items()):
        succeeded = [r for r in items if r.status == "success"]
        reductions = [r.reduction_pct for r in succeeded]
        total_in = sum(r.input_bytes for r in succeeded)
        total_out = sum(r.output_bytes for r in succeeded)
        overall = round((1 - total_out / total_in) * 100, 2) if total_in else None
        mean_duration = (
            round(statistics.mean(r.duration_ms for r in items) / 1000, 2) if items else None
        )
        rows.append({
            "operation": operation,
            "variant": variant,
            "files": len(items),
            "succeeded": len(succeeded),
            "failed": len(items) - len(succeeded),
            "mean_reduction_pct": round(statistics.mean(reductions), 2) if reductions else None,
            "median_reduction_pct": (
                round(statistics.median(reductions), 2) if reductions else None
            ),
            "total_input_mb": round(total_in / BYTES_PER_MB, 2),
            "total_output_mb": round(total_out / BYTES_PER_MB, 2),
            "overall_reduction_pct": overall,
            "mean_duration_s": mean_duration,
        })
    return rows


def write_summary_csv(summary: list[dict[str, object]], path: Path) -> None:
    """Write the aggregate summary as CSV."""
    if not summary:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary[0].keys()))
        writer.writeheader()
        writer.writerows(summary)


# ------------------------------------------------------------------- helpers --
def _logo_data_uri() -> str | None:
    """Return the Nitro logo as a data URI, or None if it cannot be read."""
    try:
        encoded = base64.b64encode(LOGO_PATH.read_bytes()).decode("ascii")
    except OSError:
        return None
    return f"data:image/png;base64,{encoded}"


def _fmt_pct(value: object) -> str:
    """Format a percentage, or a dash when there is nothing to show."""
    return f"{value:.1f}%" if isinstance(value, (int, float)) else "-"


def _fmt_bytes(value: object) -> str:
    """Format a byte count in human-readable units."""
    if not isinstance(value, (int, float)):
        return "-"
    if value >= BYTES_PER_MB:
        return f"{value / BYTES_PER_MB:.2f} MB"
    if value >= BYTES_PER_KB:
        return f"{value / BYTES_PER_KB:.1f} KB"
    return f"{int(value)} B"


def _table(headers: Sequence[str], rows: Sequence[Sequence[str]]) -> str:
    """Render a plain HTML table."""
    head = "".join(f"<th>{html.escape(h)}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>" for row in rows)
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


# -------------------------------------------------------------------- charts --
def _bin_labels(bin_width: float, n_bins: int, *, has_growth: bool) -> list[str]:
    """Build the x-axis labels: an optional growth bin, then 0-100% in steps."""
    steps = n_bins - (1 if has_growth else 0)
    labels = ["< 0"] if has_growth else []
    labels.extend(f"{int(i * bin_width)}-{int((i + 1) * bin_width)}" for i in range(steps))
    return labels


def _bin_counts(
    values: list[float], bin_width: float, n_bins: int, *, has_growth: bool
) -> list[int]:
    """Count values into the fixed bins."""
    offset = 1 if has_growth else 0
    steps = n_bins - offset
    counts = [0] * n_bins
    for value in values:
        if value < 0:
            counts[0] += 1
        else:
            counts[min(steps - 1, int(value // bin_width)) + offset] += 1
    return counts


def _axis_and_grid(pad_l: int, pad_t: int, plot_w: int, plot_h: int, y_top: int) -> list[str]:
    """Draw the horizontal gridlines and their y-axis labels."""
    parts: list[str] = []
    for step in range(5):
        value = y_top * step / 4
        y = pad_t + plot_h - (value / y_top) * plot_h
        parts.append(
            f'<line x1="{pad_l}" y1="{y:.1f}" x2="{pad_l + plot_w}" y2="{y:.1f}" stroke="{LINE}"/>'
        )
        parts.append(
            f'<text x="{pad_l - 8}" y="{y + 4:.1f}" text-anchor="end" '
            f'fill="{MUTED}">{value:.0f}</text>'
        )
    return parts


def _legend(names: Sequence[str]) -> list[str]:
    """Draw a colour legend, one entry per profile."""
    parts: list[str] = []
    x = 0.0
    for index, name in enumerate(names):
        colour = SERIES_COLORS[index % len(SERIES_COLORS)]
        parts.append(f'<rect x="{x:.1f}" y="52" width="11" height="11" rx="2.5" fill="{colour}"/>')
        parts.append(f'<text x="{x + 16:.1f}" y="62" fill="{INK_SOFT}">{html.escape(name)}</text>')
        x += 16 + len(name) * 6.6 + 20
    return parts


def _hist_svg(series: dict[str, list[float]], title: str, bin_width: float = 10.0) -> str:
    """Render the distribution of size reduction as an inline SVG histogram.

    ``series`` maps profile name to that profile's per-file reduction
    percentages. One profile gives a plain histogram; several gives grouped
    bars with a legend, so the distributions can be compared side by side.

    The x-axis is always 0-100%. A single leading "< 0" bin is added only if
    some file actually came out larger than its input.
    """
    populated = {name: values for name, values in series.items() if values}
    if not populated:
        return ""

    names = list(populated)
    multi = len(names) > 1
    all_values = [v for values in populated.values() for v in values]
    has_growth = any(v < 0 for v in all_values)

    steps = round(MAX_COMPLEXITY_BINS / bin_width)
    n_bins = steps + (1 if has_growth else 0)
    labels = _bin_labels(bin_width, n_bins, has_growth=has_growth)
    binned = {
        name: _bin_counts(values, bin_width, n_bins, has_growth=has_growth)
        for name, values in populated.items()
    }

    max_count = max((c for counts in binned.values() for c in counts), default=0) or 1
    # Headroom above the tallest bar so its count label never crowds the title.
    y_top = max(4, math.ceil(max_count * 1.25))
    y_top += -y_top % 4  # round up to a multiple of 4 for whole-number gridlines

    legend_h = 22 if multi else 0
    pad_l, pad_r, pad_t, pad_b = 46, 16, 66 + legend_h, 46
    plot_w, plot_h = 720, 250
    width, height = pad_l + plot_w + pad_r, pad_t + plot_h + pad_b
    group_w = plot_w / n_bins

    subtitle = (
        f"{len(all_values)} results across {len(names)} profiles &middot; bins of {bin_width:g}%"
        if multi
        else f"{len(all_values)} files &middot; bins of {bin_width:g}%"
    )
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'font-family="Inter,system-ui,-apple-system,Segoe UI,sans-serif" font-size="12">',
        f'<text x="0" y="18" font-weight="700" font-size="15" fill="{INK}">'
        f"{html.escape(title)}</text>",
        f'<text x="0" y="37" font-size="12" fill="{MUTED}">{subtitle}</text>',
    ]
    if multi:
        parts.extend(_legend(names))
    parts.extend(_axis_and_grid(pad_l, pad_t, plot_w, plot_h, y_top))
    parts.extend(
        _bars(
            binned=binned,
            labels=labels,
            names=names,
            geometry=(pad_l, pad_t, plot_h, group_w),
            y_top=y_top,
            multi=multi,
            has_growth=has_growth,
        )
    )
    centre_x = pad_l + plot_w / 2
    centre_y = pad_t + plot_h / 2
    parts.append(
        f'<text x="{centre_x:.1f}" y="{height - 8}" text-anchor="middle" '
        f'fill="{MUTED}">size reduction (%)</text>'
    )
    parts.append(
        f'<text x="14" y="{centre_y:.1f}" text-anchor="middle" fill="{MUTED}" '
        f'transform="rotate(-90 14 {centre_y:.1f})">files</text>'
    )
    parts.append("</svg>")
    return "".join(parts)


def _bars(
    *,
    binned: dict[str, list[int]],
    labels: Sequence[str],
    names: Sequence[str],
    geometry: tuple[int, int, int, float],
    y_top: int,
    multi: bool,
    has_growth: bool,
) -> list[str]:
    """Draw the bars and their x-axis labels."""
    pad_l, pad_t, plot_h, group_w = geometry
    inner_pad = 2.0
    slot_w = (group_w - 2 * inner_pad) / len(names)
    parts: list[str] = []

    for index, label in enumerate(labels):
        group_x = pad_l + index * group_w
        for series_index, name in enumerate(names):
            count = binned[name][index]
            bar_h = (count / y_top) * plot_h
            y = pad_t + plot_h - bar_h
            x = group_x + inner_pad + series_index * slot_w
            if multi:
                colour = SERIES_COLORS[series_index % len(SERIES_COLORS)]
            else:
                colour = BAD if (has_growth and index == 0) else BAR
            bar_w = max(slot_w - (1.5 if multi else 4), 1.5)
            tooltip = f"{html.escape(name)}: {count} file(s), {html.escape(label)}%"
            parts.append(
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{bar_h:.1f}" '
                f'rx="{3 if multi else 4}" fill="{colour}"><title>{tooltip}</title></rect>'
            )
            if count and not multi:
                parts.append(
                    f'<text x="{x + bar_w / 2:.1f}" y="{y - 5:.1f}" text-anchor="middle" '
                    f'font-weight="600" fill="{INK}">{count}</text>'
                )
        parts.append(
            f'<text x="{group_x + group_w / 2:.1f}" y="{pad_t + plot_h + 18}" '
            f'text-anchor="middle" fill="{INK_SOFT}">{html.escape(label)}</text>'
        )
    return parts


# ---------------------------------------------------------------- html pieces --
def _report_css() -> str:
    """Load the stylesheet and substitute the palette."""
    css = (ASSETS / "report.css").read_text(encoding="utf-8")
    tokens = {
        "__ORANGE__": ORANGE,
        "__ORANGE_SOFT__": ORANGE_SOFT,
        "__INK__": INK,
        "__INK_SOFT__": INK_SOFT,
        "__MUTED__": MUTED,
        "__LINE__": LINE,
        "__SURFACE__": SURFACE,
        "__CANVAS__": CANVAS,
    }
    for token, colour in tokens.items():
        css = css.replace(token, colour)
    return css


def _report_js(rows: list[dict[str, object]]) -> str:
    """Load the script and embed the result data in it."""
    script = (ASSETS / "report.js").read_text(encoding="utf-8")
    # Escaping "</" keeps a stray sequence in the data from closing the tag.
    payload = json.dumps(rows).replace("</", "<\\/")
    return script.replace("__DATA__", payload)


def _kpis(results: list[OperationResult]) -> str:
    """Render the headline numbers."""
    total = len(results)
    succeeded = [r for r in results if r.status == "success"]
    total_in = sum(r.input_bytes for r in succeeded)
    total_out = sum(r.output_bytes for r in succeeded)
    reductions = [r.reduction_pct for r in succeeded]

    mean_reduction = f"{statistics.mean(reductions):.1f}%" if reductions else "-"
    overall = f"{(1 - total_out / total_in) * 100:.1f}%" if total_in else "-"
    saved_mb = (total_in - total_out) / BYTES_PER_MB if total_in else 0.0
    failed = total - len(succeeded)

    cells = [
        ("hl", mean_reduction, "mean reduction per file"),
        ("", overall, "overall size reduction"),
        ("", f"{saved_mb:.1f} MB", "saved across successful files"),
        ("", str(len({r.file for r in results})), "input files"),
        ("", f"{len(succeeded)} / {total}", "successful runs"),
        ("", str(failed), "failed runs"),
    ]
    tiles = "".join(
        f'<div class="kpi {cls}"><b>{value}</b><span>{label}</span></div>'
        for cls, value, label in cells
    )
    return f'<div class="card"><div class="kpis">{tiles}</div></div>'


def _summary_card(summary: list[dict[str, object]]) -> str:
    """Render the per-profile summary table, shown only for multi-profile runs."""
    if len(summary) <= 1:
        return ""
    rows = [
        [
            f'<span class="pill">{html.escape(str(row["variant"]))}</span>',
            str(row["files"]),
            str(row["succeeded"]),
            f'<span class="{"bad" if row["failed"] else ""}">{row["failed"]}</span>',
            f"<b>{_fmt_pct(row['mean_reduction_pct'])}</b>",
            _fmt_pct(row["median_reduction_pct"]),
            f"{row['total_input_mb']} MB",
            f"{row['total_output_mb']} MB",
            f"<b>{_fmt_pct(row['overall_reduction_pct'])}</b>",
            f"{row['mean_duration_s']} s" if row["mean_duration_s"] is not None else "-",
        ]
        for row in summary
    ]
    headers = (
        "Profile",
        "Files",
        "OK",
        "Failed",
        "Mean reduction",
        "Median reduction",
        "Total in",
        "Total out",
        "Overall reduction",
        "Mean time / file",
    )
    table = _table(headers, rows)
    return f'<div class="card"><h2>Summary by profile</h2><div class="scroll">{table}</div></div>'


def _chart_card(series: dict[str, list[float]], selected: str | None) -> str:
    """Render one chart per profile plus a comparison view, with a picker."""
    if not series:
        return ""
    names = list(series)
    chosen = selected if selected in series else names[0]

    boxes: list[str] = []
    options: list[str] = []
    for name in names:
        svg = _hist_svg({name: series[name]}, f"Distribution of size reduction: {name}")
        hidden = "" if name == chosen else " hidden"
        boxes.append(f'<div class="chartbox" data-chart="{html.escape(name)}"{hidden}>{svg}</div>')
        selected_attr = " selected" if name == chosen else ""
        options.append(
            f'<option value="{html.escape(name)}"{selected_attr}>{html.escape(name)}</option>'
        )

    if len(names) > 1:
        combined = _hist_svg(series, "Distribution of size reduction by profile")
        boxes.append(f'<div class="chartbox" data-chart="__all__" hidden>{combined}</div>')
        options.append('<option value="__all__">All profiles (compare)</option>')
        picker = f'<label>Profile <select id="chartProfile">{"".join(options)}</select></label>'
    else:
        picker = ""

    head = f'<div class="chart-head"><div class="grow"></div>{picker}</div>'
    return f'<div class="card">{head}{"".join(boxes)}</div>'


def _rows_for_table(
    results: list[OperationResult], preferred: str | None
) -> list[dict[str, object]]:
    """Flatten the results for the table, with the chosen profile listed first."""

    def sort_key(result: OperationResult) -> tuple[bool, str, float, str]:
        reduction = result.reduction_pct if isinstance(result, OperationSuccess) else -1e9
        return (
            result.variant != preferred,
            result.variant,
            -reduction,
            result.file,
        )

    def to_row(r: OperationResult) -> dict[str, object]:
        common: dict[str, object] = {
            "file": r.file,
            "profile": r.variant,
            "status": r.status,
            "input_bytes": r.input_bytes,
            "duration_s": round(r.duration_ms / 1000, 1),
        }
        if isinstance(r, OperationSuccess):
            return common | {
                "output_bytes": r.output_bytes,
                "reduction_pct": r.reduction_pct,
                "http_status": None,
                "error_type": None,
                "error_message": None,
                "request_id": None,
                "job_id": None,
            }
        return common | {
            "output_bytes": None,
            "reduction_pct": None,
            "http_status": r.http_status,
            "error_type": r.error_type,
            "error_message": r.error_message,
            "request_id": r.request_id,
            "job_id": r.job_id,
        }

    return [to_row(r) for r in sorted(results, key=sort_key)]


def _initial_tbody(rows: list[dict[str, object]]) -> str:
    """Render the first page of rows server-side.

    The table therefore still shows data where scripts do not run, such as
    preview panes and some mail clients. The script takes over from there.
    """
    out: list[str] = []
    for index, row in enumerate(rows[:DEFAULT_PAGE_SIZE], start=1):
        succeeded = row["status"] == "success"
        status = (
            '<span class="ok">&#9679; success</span>'
            if succeeded
            else '<span class="bad">&#9679; failed</span>'
        )
        detail = (
            ""
            if succeeded
            else html.escape(
                f"HTTP {row['http_status'] if row['http_status'] is not None else '-'} "
                f"| {row['error_type'] or ''} | {row['error_message'] or ''} "
                f"| req {row['request_id'] or '-'}"
            )
        )
        reduction = f"<b>{_fmt_pct(row['reduction_pct'])}</b>" if succeeded else "-"
        cls = "" if succeeded else ' class="fail"'
        out.append(
            f"<tr{cls}><td>{index}</td><td>{html.escape(str(row['file']))}</td>"
            f'<td><span class="pill">{html.escape(str(row["profile"]))}</span></td>'
            f"<td>{status}</td><td>{_fmt_bytes(row['input_bytes'])}</td>"
            f"<td>{_fmt_bytes(row['output_bytes'])}</td><td>{reduction}</td>"
            f"<td>{row['duration_s']} s</td><td>{detail}</td></tr>"
        )
    return "".join(out)


def _table_card(rows: list[dict[str, object]], variants: Sequence[str]) -> str:
    """Render the per-file table with its filters, pager and export button."""
    profile_filter = ""
    if len(variants) > 1:
        options = "".join(
            f'<option value="{html.escape(v)}">{html.escape(v)}</option>' for v in variants
        )
        profile_filter = (
            f'<label>Profile <select id="fVariant"><option value="">All</option>'
            f"{options}</select></label>"
        )

    shown = min(DEFAULT_PAGE_SIZE, len(rows))
    initial_range = f"Showing 1-{shown} of {len(rows)}" if rows else "0 rows"
    pages = max(1, math.ceil(len(rows) / DEFAULT_PAGE_SIZE))
    next_disabled = " disabled" if pages <= 1 else ""
    headers = "".join(f"<th>{html.escape(h)}</th>" for h in _TABLE_HEADERS)

    return (
        '<div class="card">'
        '<div class="toolbar">'
        '<h2 style="margin:0">Per-file results</h2><div class="grow"></div>'
        f"{profile_filter}"
        '<label>Status <select id="fStatus"><option value="">All</option>'
        '<option value="success">Success</option><option value="failed">Failed</option>'
        "</select></label>"
        '<label>Show <select id="pageSize"><option selected>10</option><option>25</option>'
        '<option>50</option><option>100</option><option value="all">All</option></select></label>'
        '<button class="sm" id="dl">Download CSV</button>'
        "</div>"
        f'<div class="scroll"><table><thead><tr>{headers}</tr></thead>'
        f'<tbody id="rows">{_initial_tbody(rows)}</tbody></table></div>'
        f'<div class="pager"><span id="range">{initial_range}</span>'
        '<button id="prev" disabled>&lsaquo; Prev</button>'
        f'<span id="pageInfo">Page 1 / {pages}</span>'
        f'<button id="next"{next_disabled}>Next &rsaquo;</button></div>'
        "</div>"
    )


def _hero(title: str, profiles: Sequence[str]) -> str:
    """Render the header banner, naming every profile that was actually run."""
    logo = _logo_data_uri()
    logo_html = (
        f'<img class="logo" src="{logo}" alt="Nitro">'
        if logo
        else '<div class="logo-fallback">N</div>'
    )
    generated = datetime.now(tz=UTC).astimezone().strftime("%d %b %Y, %H:%M")
    label = "profile" if len(profiles) == 1 else "profiles"
    names = ", ".join(profiles) if profiles else "-"
    return (
        f'<div class="hero"><div class="wrap">{logo_html}'
        f"<div><h1>{html.escape(title)}</h1>"
        f'<p class="sub">Generated {generated} &middot; {label}: '
        f"<b>{html.escape(names)}</b></p></div>"
        "</div></div>"
    )


def _profiles_in_run_order(results: list[OperationResult]) -> list[str]:
    """List the profiles in the order they were run, for the header and chart."""
    profiles: list[str] = []
    for result in results:
        if result.variant not in profiles:
            profiles.append(result.variant)
    return profiles


def _reduction_series(
    results: list[OperationResult], profiles: list[str]
) -> dict[str, list[float]]:
    """Collect each profile's successful reduction percentages for the chart."""
    succeeded = [r for r in results if r.status == "success"]
    series: dict[str, list[float]] = {}
    for name in profiles:
        values = [r.reduction_pct for r in succeeded if r.variant == name]
        if values:
            series[name] = values
    return series


# ----------------------------------------------------------------------- html --
def write_html(
    results: list[OperationResult],
    summary: list[dict[str, object]],
    path: Path,
    *,
    title: str = "Nitro Optimize API Benchmark Report",
    default_variant: str | None = None,
) -> None:
    """Write the self-contained HTML report.

    Args:
        results: Every per-file result from the run.
        summary: The aggregate rows from ``summarise``.
        path: Where the report is written.
        title: The report heading.
        default_variant: The profile to show first in the chart and table.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    variants = sorted({r.variant for r in results})
    preferred = (
        default_variant if default_variant in variants else (variants[0] if variants else None)
    )

    profiles_in_run = _profiles_in_run_order(results)
    series = _reduction_series(results, profiles_in_run)
    rows = _rows_for_table(results, preferred)
    body = "".join([
        _kpis(results),
        _summary_card(summary),
        _chart_card(series, preferred),
        _table_card(rows, variants),
        '<p class="foot">Nitro Optimize API Benchmark &middot; '
        "results.csv and summary.csv accompany this report</p>",
    ])

    doc = (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{html.escape(title)}</title>"
        f"<style>{_report_css()}</style></head><body>"
        f"{_hero(title, profiles_in_run)}"
        f'<div class="wrap content">{body}</div>'
        f"<script>{_report_js(rows)}</script>"
        "</body></html>"
    )
    path.write_text(doc, encoding="utf-8")
