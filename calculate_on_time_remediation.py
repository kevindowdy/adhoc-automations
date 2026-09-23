"""Calculate on-time vs. late remediation stats for closed vulnerabilities.

Reads one or more closed-vulnerability exports (each already containing
only remediated/closed rows), filters each down to the configured
severities (e.g. Critical and High), and logs a summary sentence per file
stating how many of those vulnerabilities were remediated on time vs. late
and the resulting on-time remediation rate. Each configured file is
processed independently -- results are not combined across files.

A vulnerability is "late" when its ``DAYS_PAST_DUE_COLUMN`` value is
greater than zero, matching the existing past-due definition used by
``filter_past_due_vulnerabilities.py``. Every other row -- including rows
where that value is zero, negative, or missing/non-numeric -- counts as
"on time", so the on-time and late counts always add up to the total.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Sequence, TypedDict

import pandas as pd

# =============================================================================
# CONFIGURATION
# =============================================================================


class InputFile(TypedDict):
    """One closed-vulnerability export to process, and its report label."""

    filePath: str
    label: str


INPUT_FILES: Final[list[InputFile]] = [
    {
        "filePath": r"C:\Users\fbfepde\Documents\Temporary\FIG_Closed_Vulnerabilities\FIG_Closed_Vulnerabilities_20260921.parquet",
        "label": "September",
    },
        {
        "filePath": r"C:\Users\fbfepde\Documents\Temporary\FIG_Closed_Vulnerabilities\FIG Closed Vulnerabilities_20260101_RemovedVulnsOpenedAfterJan1.xlsx",
        "label": "January",
    },
]

# Column holding each row's severity. Raw values are matched against
# SEVERITY_LEVELS case-insensitively (see filter_to_configured_severities()).
SEVERITY_COLUMN: Final[str] = "vulnerability.severity"

# Only rows whose severity matches one of these are included in the stats.
SEVERITY_LEVELS: Final[list[str]] = ["Critical", "High"]

# Column holding each row's numeric days-past-due value at remediation time.
DAYS_PAST_DUE_COLUMN: Final[str] = "saltminer.attributes.DaysPastDue"

APP_NAME = "calculate-on-time-remediation"

# =============================================================================
# LOGGING
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format=(
        '{"timestamp":"%(asctime)s","level":"%(levelname)s",'
        f'"message":"%(message)s","application":"{APP_NAME}"}}'
    ),
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class OnTimeRemediationStats:
    """On-time vs. late remediation counts for one (filtered) dataset."""

    total: int
    late_count: int
    on_time_count: int


def filter_to_configured_severities(
    dataframe: pd.DataFrame,
    severity_column: str,
    severity_levels: Sequence[str],
) -> pd.DataFrame:
    """Filter a dataset down to rows matching one of the configured severities.

    Matching is case-insensitive and ignores surrounding whitespace, so
    source data like ``"critical "`` or ``"CRITICAL"`` both match a
    configured ``"Critical"`` level.

    Args:
        dataframe: Closed-vulnerability dataset. Must contain
            ``severity_column``.
        severity_column: Column to read each row's severity from.
        severity_levels: Severity values to keep, e.g. ``["Critical",
            "High"]``.

    Returns:
        A new DataFrame containing only rows whose severity matches one of
        ``severity_levels``, with the original index preserved.

    Raises:
        KeyError: If ``severity_column`` is not present in ``dataframe``.
        ValueError: If ``severity_levels`` is empty.
    """
    if severity_column not in dataframe.columns:
        raise KeyError(
            f"Expected column '{severity_column}' not found in dataset. "
            f"Available columns: {list(dataframe.columns)}"
        )

    if not severity_levels:
        raise ValueError("severity_levels must not be empty.")

    normalized_levels = {level.strip().casefold() for level in severity_levels}
    normalized_severity = (
        dataframe[severity_column].astype(str).str.strip().str.casefold()
    )

    return dataframe.loc[normalized_severity.isin(normalized_levels)].copy()


def calculate_on_time_remediation_stats(
    dataframe: pd.DataFrame,
    days_past_due_column: str,
) -> OnTimeRemediationStats:
    """Split a (severity-filtered) dataset into on-time vs. late remediations.

    A row is "late" when its ``days_past_due_column`` value is numeric and
    greater than zero. ``on_time_count`` is computed as the complement
    (``total - late_count``) rather than a separate "<= 0" test, so rows
    with a zero, negative, missing, or non-numeric value are always
    counted as on time and ``total`` always equals ``late_count +
    on_time_count`` -- no row is double-counted or dropped.

    Args:
        dataframe: Severity-filtered closed-vulnerability dataset. Must
            contain ``days_past_due_column``.
        days_past_due_column: Column to read each row's numeric
            days-past-due value from.

    Returns:
        The total, late, and on-time counts for ``dataframe``.

    Raises:
        KeyError: If ``days_past_due_column`` is not present in
            ``dataframe``.
    """
    if days_past_due_column not in dataframe.columns:
        raise KeyError(
            f"Expected column '{days_past_due_column}' not found in dataset. "
            f"Available columns: {list(dataframe.columns)}"
        )

    total = len(dataframe)
    days_past_due = pd.to_numeric(dataframe[days_past_due_column], errors="coerce")
    late_count = int((days_past_due > 0).sum())
    on_time_count = total - late_count

    return OnTimeRemediationStats(
        total=total, late_count=late_count, on_time_count=on_time_count
    )


def format_on_time_remediation_summary(
    label: str,
    severity_levels: Sequence[str],
    stats: OnTimeRemediationStats,
) -> str:
    """Build the human-readable on-time remediation summary sentence.

    Args:
        label: Report label identifying which input this summary is for
            (e.g. a reporting month or export date).
        severity_levels: The severities the stats were filtered to, used to
            describe them in the sentence (e.g. ``"Critical/High"``).
        stats: Counts to report, from ``calculate_on_time_remediation_stats``.

    Returns:
        A one-sentence (or two-sentence) summary of the on-time remediation
        performance for ``label``. If ``stats.total`` is zero, returns a
        distinct "no vulnerabilities found" message instead of dividing by
        zero.
    """
    severities_label = "/".join(severity_levels)

    if stats.total == 0:
        return (
            f"As of today, for {label}: no {severities_label} closed "
            "vulnerabilities found."
        )

    on_time_percentage = (stats.on_time_count / stats.total) * 100

    return (
        f"As of today, for {label}: {stats.total} {severities_label} "
        "vulnerabilities have been remediated. "
        f"{stats.late_count} were remediated late and "
        f"{stats.on_time_count} were remediated on time. "
        "The on-time remediation rate is "
        f"{stats.on_time_count}/{stats.total} ({on_time_percentage:.1f}%)."
    )


def _read_input_file(input_file: InputFile) -> pd.DataFrame:
    """Validate and read one configured input file into a DataFrame.

    Args:
        input_file: Entry from ``INPUT_FILES`` with a ``filePath`` and
            ``label``.

    Returns:
        The parsed dataset for that input file.

    Raises:
        FileNotFoundError: If ``filePath`` does not exist.
        ValueError: If ``filePath`` has an unsupported extension.
    """
    file_path = Path(input_file["filePath"])

    if not file_path.is_file():
        raise FileNotFoundError(
            f"Input file for '{input_file['label']}' not found: {file_path}"
        )

    suffix = file_path.suffix.lower()
    logger.info(
        f"Reading '{input_file['label']}' closed vulnerabilities from {file_path}"
    )

    if suffix == ".csv":
        return pd.read_csv(file_path, dtype=str)
    if suffix == ".tsv":
        return pd.read_csv(file_path, dtype=str, sep="\t")
    if suffix in (".xlsx", ".xls"):
        return pd.read_excel(file_path, dtype=str)
    if suffix == ".parquet":
        # Parquet is a typed columnar format, so no dtype=str coercion here
        # (unlike the CSV/Excel branches above) -- filter_to_configured_severities
        # and calculate_on_time_remediation_stats already coerce the columns
        # they read regardless of the input dtype.
        return pd.read_parquet(file_path)

    raise ValueError(
        f"Unsupported input file extension {suffix!r} for {file_path}. "
        "Supported extensions: .csv, .tsv, .xlsx, .xls, .parquet"
    )


def main() -> None:
    """Log an on-time remediation summary for every configured input file.

    For every entry in ``INPUT_FILES``, reads the closed-vulnerability
    export, filters it down to ``SEVERITY_LEVELS``, computes on-time vs.
    late remediation stats from ``DAYS_PAST_DUE_COLUMN``, and logs the
    resulting summary sentence. Files are processed independently -- no
    results are combined across files, and nothing is written to disk.

    Raises:
        FileNotFoundError: If a configured input file does not exist.
        KeyError: If a configured input file is missing the severity or
            days-past-due column.
        ValueError: If a configured input file has an unsupported
            extension, or ``SEVERITY_LEVELS`` is empty.
    """
    logger.info("=" * 80)
    logger.info("Calculate-On-Time-Remediation SCRIPT STARTED")
    logger.info(f"Input files: {INPUT_FILES}")
    logger.info(f"Severity levels: {SEVERITY_LEVELS}")

    for input_file in INPUT_FILES:
        dataframe = _read_input_file(input_file)
        filtered = filter_to_configured_severities(
            dataframe, SEVERITY_COLUMN, SEVERITY_LEVELS
        )
        stats = calculate_on_time_remediation_stats(filtered, DAYS_PAST_DUE_COLUMN)
        summary = format_on_time_remediation_summary(
            input_file["label"], SEVERITY_LEVELS, stats
        )
        logger.info(summary)

    logger.info("SCRIPT COMPLETED SUCCESSFULLY")


if __name__ == "__main__":
    main()
