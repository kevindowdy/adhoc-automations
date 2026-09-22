"""Filter open SDLC vulnerability exports down to past-due vulnerabilities.

Reads one or more open-vulnerability Excel exports (one per reporting
month), keeps only the rows that are past their remediation due date,
tags each row with the reporting month it came from, and writes every
month onto its own sheet in a single consolidated workbook. A final
"Summary" sheet totals the past-due vulnerability count for each month.
"""

import logging
from pathlib import Path
from typing import Final, TypedDict

import pandas as pd

# =============================================================================
# CONFIGURATION
# =============================================================================

# Column in the open-vulnerability export whose value is the number of days
# a vulnerability is past its remediation due date. A value greater than
# zero means the vulnerability is past due.
DAYS_PAST_DUE_COLUMN: Final[str] = "Days Past Due"

# Column added to each filtered dataset to record which report it came from.
MONTH_COLUMN: Final[str] = "Month"

MONTH_SHEET_NAME_MAX_LENGTH: Final[int] = 31  # Excel sheet-name limit.

SUMMARY_SHEET_NAME: Final[str] = "Summary"
SUMMARY_COUNT_COLUMN: Final[str] = "Past Due Vulnerabilities"


class InputFile(TypedDict):
    """One open-vulnerability export to process, and the month it covers."""

    filePath: str
    month: str


INPUT_FILES: Final[list[InputFile]] = [
    {"filePath": "data/input/open_vulnerabilities_2026_07.xlsx", "month": "July"},
    {"filePath": "data/input/open_vulnerabilities_2026_08.xlsx", "month": "August"},
    {"filePath": "data/input/open_vulnerabilities_2026_09.xlsx", "month": "September"},
]

OUTPUT_FILE: Final[Path] = Path("data/output/past_due_vulnerabilities.xlsx")

APP_NAME = "filter-past-due-vulnerabilities"

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


def filter_past_due_vulnerabilities(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Filter an open-vulnerability dataset down to past-due vulnerabilities.

    A vulnerability is considered past due when its ``DAYS_PAST_DUE_COLUMN``
    value is numeric and greater than zero. Rows with a missing or
    non-numeric value in that column are treated as not past due.

    Args:
        dataframe: Open vulnerabilities dataset. Must contain
            ``DAYS_PAST_DUE_COLUMN``.

    Returns:
        A new DataFrame containing only the past-due rows, with the
        original index preserved.

    Raises:
        KeyError: If ``DAYS_PAST_DUE_COLUMN`` is not present in
            ``dataframe``.
    """
    if DAYS_PAST_DUE_COLUMN not in dataframe.columns:
        raise KeyError(
            f"Expected column '{DAYS_PAST_DUE_COLUMN}' not found in dataset. "
            f"Available columns: {list(dataframe.columns)}"
        )

    days_past_due = pd.to_numeric(dataframe[DAYS_PAST_DUE_COLUMN], errors="coerce")
    return dataframe.loc[days_past_due > 0].copy()


def _sheet_name_for_month(month: str) -> str:
    """Build a valid, unique-per-month Excel sheet name from a month label.

    Excel sheet names are capped at 31 characters and cannot contain
    ``[]:*?/\\``. Reporting month labels are short in practice, but this
    keeps the writer from raising on an unexpected input.

    Args:
        month: The reporting month label from ``INPUT_FILES``.

    Returns:
        A sanitized sheet name safe to pass to an Excel writer.
    """
    invalid_characters = r"[]:*?/\\"
    sanitized = "".join(
        character for character in month if character not in invalid_characters
    )
    return sanitized[:MONTH_SHEET_NAME_MAX_LENGTH] or "Sheet"


def _read_input_file(input_file: InputFile) -> pd.DataFrame:
    """Validate and read one configured input file into a DataFrame.

    Args:
        input_file: Entry from ``INPUT_FILES`` with a ``filePath`` and
            ``month``.

    Returns:
        The parsed dataset for that month.

    Raises:
        FileNotFoundError: If ``filePath`` does not exist.
    """
    file_path = Path(input_file["filePath"])

    if not file_path.is_file():
        raise FileNotFoundError(
            f"Input file for month '{input_file['month']}' not found: {file_path}"
        )

    logger.info(f"Reading '{input_file['month']}' vulnerabilities from {file_path}")
    return pd.read_excel(file_path)


def main() -> None:
    """Build a consolidated past-due vulnerabilities workbook.

    For every entry in ``INPUT_FILES``, reads the open-vulnerability
    export, filters it down to past-due vulnerabilities, tags the result
    with its reporting month, and writes it to its own sheet in
    ``OUTPUT_FILE``. A trailing "Summary" sheet totals the past-due count
    per month. The workbook is written atomically: results are staged to
    a temporary file and only moved into place once every sheet has been
    written successfully.

    Raises:
        FileNotFoundError: If a configured input file does not exist.
        KeyError: If a configured input file is missing the past-due
            column.
    """
    logger.info("=" * 80)
    logger.info("Filter-Past-Due-Vulnerabilities SCRIPT STARTED")
    logger.info(f"Input files: {INPUT_FILES}")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    temp_output_file = OUTPUT_FILE.with_suffix(f"{OUTPUT_FILE.suffix}.tmp")

    month_totals: list[dict[str, object]] = []

    try:
        with pd.ExcelWriter(temp_output_file, engine="openpyxl") as writer:
            for input_file in INPUT_FILES:
                dataframe = _read_input_file(input_file)
                past_due_vulnerabilities = filter_past_due_vulnerabilities(dataframe)
                past_due_vulnerabilities[MONTH_COLUMN] = input_file["month"]

                sheet_name = _sheet_name_for_month(input_file["month"])
                logger.info(
                    f"'{input_file['month']}': "
                    f"{len(past_due_vulnerabilities)} past-due vulnerabilities "
                    f"-> sheet '{sheet_name}'"
                )

                past_due_vulnerabilities.to_excel(
                    writer, sheet_name=sheet_name, index=False
                )

                month_totals.append(
                    {
                        MONTH_COLUMN: input_file["month"],
                        SUMMARY_COUNT_COLUMN: len(past_due_vulnerabilities),
                    }
                )

            summary = pd.DataFrame(month_totals)
            summary.to_excel(writer, sheet_name=SUMMARY_SHEET_NAME, index=False)

        temp_output_file.replace(OUTPUT_FILE)

    finally:
        temp_output_file.unlink(missing_ok=True)

    logger.info(f"Wrote consolidated workbook to {OUTPUT_FILE}")
    logger.info("Past-due totals by month:")
    for row in month_totals:
        logger.info(f"  {row[MONTH_COLUMN]}: {row[SUMMARY_COUNT_COLUMN]}")

    logger.info("SCRIPT COMPLETED SUCCESSFULLY")


if __name__ == "__main__":
    main()
