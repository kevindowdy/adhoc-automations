"""Build hierarchical row-count tables for a configured list of datasets.

Generalizes the top-level / indented-sub-level rollup used in the
vulnerability tracking report (one grouping column nested under another,
each row showing how many raw rows match it) to any dataset and any
number of grouping columns.

Each entry in ``INPUT_FILES`` names a source file and the sheet to read
from it. Every entry is summarized independently using the same
``GROUP_COLUMNS`` and written to its own sheet in a single consolidated
output workbook, mirroring the per-month sheet layout used by
``filter_past_due_vulnerabilities.py``. No filtering, date parsing, or
categorization logic lives here -- input files are expected to already
contain only the rows that belong in the count.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from pathlib import Path
from typing import Final, TypedDict

import pandas as pd

# =============================================================================
# CONFIGURATION
# =============================================================================


class InputFile(TypedDict):
    """One dataset to summarize: a file path and the sheet to read from it."""

    filePath: str
    sheetName: str


# Each entry becomes one sheet (named after ``sheetName``) in OUTPUT_FILE.
# ``sheetName`` is ignored for CSV/TSV input, which has no sheets to select.
INPUT_FILES = [
    # {"filePath": r"data\output\past_due_vulnerabilities.xlsx", "sheetName": "January"},
    # {"filePath": r"data\output\past_due_vulnerabilities.xlsx", "sheetName": "February"},
    # {"filePath": r"data\output\past_due_vulnerabilities.xlsx", "sheetName": "March"},
    # {"filePath": r"data\output\past_due_vulnerabilities.xlsx", "sheetName": "April"},
    # {"filePath": r"data\output\past_due_vulnerabilities.xlsx", "sheetName": "May"},
    # {"filePath": r"data\output\past_due_vulnerabilities.xlsx", "sheetName": "June"},
    # {"filePath": r"data\output\past_due_vulnerabilities.xlsx", "sheetName": "July"},
    # {"filePath": r"data\output\past_due_vulnerabilities.xlsx", "sheetName": "August"},
    # {"filePath": r"data\output\past_due_vulnerabilities.xlsx", "sheetName": "September"},
    {"filePath": r"data\output\all_past_due_vulnerabilities.xlsx", "sheetName": "Today"},
]

# Grouping columns, top-to-bottom nesting order, applied to every input.
GROUP_COLUMNS: Final[list[str]] = ["saltminer.inventory_asset.attributes.appmap.application_owner_mc_2"]

OUTPUT_FILE: Final[Path] = Path("data/output/category_counts.xlsx")

# Placeholder substituted for missing/blank values in a grouping column so
# they still get their own counted row instead of being silently dropped.
BLANK_LABEL: Final[str] = "(Blank)"

# How far each nested level is indented in the rendered "Category" text.
INDENT_SPACES_PER_LEVEL: Final[int] = 2

GRAND_TOTAL_LABEL: Final[str] = "Grand Total"

SHEET_NAME_MAX_LENGTH: Final[int] = 31  # Excel sheet-name limit.

CATEGORY_COLUMN: Final[str] = "Application Owner"
LEVEL_COLUMN: Final[str] = "saltminer.inventory_asset.attributes.appmap.cio"
COUNT_COLUMN: Final[str] = (
    "Total Past Due"
)

APP_NAME = "count-by-categories"

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


def _normalize_group_column(series: pd.Series, blank_label: str) -> pd.Series:
    """Coerce a grouping column to trimmed strings with blanks labeled.

    Args:
        series: The column to normalize.
        blank_label: Value substituted for missing or empty-string entries,
            so they group into a single visible row instead of being
            dropped by ``groupby``/``unique``.

    Returns:
        A new string Series with no NaN or empty-string values.
    """
    return series.fillna(blank_label).astype(str).str.strip().replace("", blank_label)


def _build_rows(
    dataframe: pd.DataFrame, remaining_columns: Sequence[str], level: int
) -> list[dict[str, object]]:
    """Recursively build indented count rows for the remaining columns.

    Args:
        dataframe: The (already column-normalized) subset of rows to
            break down further.
        remaining_columns: Grouping columns still to be applied, in
            top-to-bottom nesting order.
        level: Current nesting depth (0 = top level), used for indentation.

    Returns:
        A list of row dicts, each with ``Level``, ``Category``, and
        ``Count`` keys, in the order they should appear in the report
        (each row's descendants immediately follow it).
    """
    if not remaining_columns:
        return []

    column, deeper_columns = remaining_columns[0], remaining_columns[1:]
    indent = " " * (INDENT_SPACES_PER_LEVEL * level)

    rows: list[dict[str, object]] = []
    for value in sorted(dataframe[column].unique()):
        value_df = dataframe[dataframe[column] == value]
        rows.append(
            {
                LEVEL_COLUMN: level,
                CATEGORY_COLUMN: f"{indent}{value}",
                COUNT_COLUMN: len(value_df),
            }
        )
        rows.extend(_build_rows(value_df, deeper_columns, level + 1))

    return rows


def count_by_categories(
    dataframe: pd.DataFrame,
    group_columns: Sequence[str],
    blank_label: str = BLANK_LABEL,
) -> pd.DataFrame:
    """Build a hierarchical raw row-count table for a dataset.

    One row is produced per distinct value at each grouping level, nested
    directly under its parent row, followed by a trailing "Grand Total"
    row. Counts are raw row counts -- no filtering or other business logic
    is applied here; that is expected to happen before the dataset reaches
    this function.

    Args:
        dataframe: The dataset to summarize. Not mutated.
        group_columns: One or more column names, in top-to-bottom nesting
            order. A single column produces a flat one-level table; two or
            more nest each subsequent column's rows under the matching row
            above it.
        blank_label: Value substituted for missing/blank entries in any
            grouping column.

    Returns:
        A DataFrame with columns ``Level``, ``Category``, and ``Count``,
        one row per group value (indented under its parent by
        ``INDENT_SPACES_PER_LEVEL`` spaces per level in ``Category``) plus
        a final Grand Total row.

    Raises:
        ValueError: If ``group_columns`` is empty or contains duplicates.
        KeyError: If any column in ``group_columns`` is not present in
            ``dataframe``.
    """
    if not group_columns:
        raise ValueError("At least one group-by column is required.")

    if len(set(group_columns)) != len(group_columns):
        raise ValueError(
            f"group_columns must not contain duplicates: {group_columns!r}"
        )

    missing_columns = [col for col in group_columns if col not in dataframe.columns]
    if missing_columns:
        raise KeyError(
            f"Column(s) not found in dataset: {missing_columns}. "
            f"Available columns: {list(dataframe.columns)}"
        )

    working = dataframe.copy()
    for column in group_columns:
        working[column] = _normalize_group_column(working[column], blank_label)

    rows = _build_rows(working, group_columns, level=0)
    rows.append(
        {
            LEVEL_COLUMN: "",
            CATEGORY_COLUMN: GRAND_TOTAL_LABEL,
            COUNT_COLUMN: len(working),
        }
    )

    return pd.DataFrame(rows, columns=[LEVEL_COLUMN, CATEGORY_COLUMN, COUNT_COLUMN])


def _read_input_file(input_file: InputFile) -> pd.DataFrame:
    """Validate and read one configured input file into a string-typed DataFrame.

    Every column is read as string dtype so grouping treats equal-looking
    values consistently.

    Args:
        input_file: Entry from ``INPUT_FILES`` with a ``filePath`` and the
            ``sheetName`` to read (ignored for CSV/TSV input).

    Returns:
        The parsed dataset.

    Raises:
        FileNotFoundError: If ``filePath`` does not exist.
        ValueError: If ``filePath`` has an unsupported extension.
    """
    file_path = Path(input_file["filePath"])
    if not file_path.is_file():
        raise FileNotFoundError(f"Input file not found: {file_path}")

    suffix = file_path.suffix.lower()
    logger.info(f"Reading {file_path} [{input_file['sheetName']}]")

    if suffix == ".csv":
        return pd.read_csv(file_path, dtype=str)
    if suffix == ".tsv":
        return pd.read_csv(file_path, dtype=str, sep="\t")
    if suffix in (".xlsx", ".xls"):
        return pd.read_excel(file_path, dtype=str, sheet_name=input_file["sheetName"])

    raise ValueError(
        f"Unsupported input file extension {suffix!r} for {file_path}. "
        "Supported extensions: .csv, .tsv, .xlsx, .xls"
    )


def _sanitize_sheet_name(name: str) -> str:
    """Strip characters Excel disallows in sheet names and cap the length.

    Args:
        name: Desired sheet name.

    Returns:
        A sheet name safe to pass to an Excel writer, falling back to
        ``"Sheet"`` if nothing valid remains.
    """
    invalid_characters = r"[]:*?/\\"
    sanitized = "".join(
        character for character in name if character not in invalid_characters
    )
    return sanitized[:SHEET_NAME_MAX_LENGTH] or "Sheet"


def _unique_sheet_name(desired_name: str, used_names: set[str]) -> str:
    """Disambiguate a sheet name against names already used in the workbook.

    Args:
        desired_name: The sheet name to use if it is not already taken.
        used_names: Sheet names already assigned in the output workbook.
            Mutated to add the returned name.

    Returns:
        ``desired_name`` if unused, otherwise ``desired_name`` with a
        numeric suffix (``" (2)"``, ``" (3)"``, ...) making it unique,
        truncated to stay within Excel's sheet-name length limit.
    """
    sanitized = _sanitize_sheet_name(desired_name)
    if sanitized not in used_names:
        used_names.add(sanitized)
        return sanitized

    suffix_number = 2
    while True:
        suffix = f" ({suffix_number})"
        candidate = sanitized[: SHEET_NAME_MAX_LENGTH - len(suffix)] + suffix
        if candidate not in used_names:
            used_names.add(candidate)
            return candidate
        suffix_number += 1


def _style_worksheet(worksheet, report_df: pd.DataFrame) -> None:
    """Apply header, indentation, and Grand Total styling to a report sheet.

    Args:
        worksheet: The openpyxl worksheet the report was just written to.
        report_df: The report DataFrame that was written, used to look up
            each row's nesting level for styling.
    """
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter

    DARK_BLUE = "1F4E79"
    LIGHT_BLUE = "D6E4F0"
    WHITE = "FFFFFF"

    for cell in worksheet[1]:
        cell.fill = PatternFill(
            start_color=DARK_BLUE, end_color=DARK_BLUE, fill_type="solid"
        )
        cell.font = Font(color=WHITE, bold=True)
        cell.alignment = Alignment(
            horizontal="center", vertical="center", wrap_text=True
        )
    worksheet.row_dimensions[1].height = 32

    for row_idx, level in enumerate(report_df[LEVEL_COLUMN].tolist(), start=2):
        is_grand_total = level == ""
        is_top_level = level == 0

        for col_idx, cell in enumerate(worksheet[row_idx], start=1):
            if is_grand_total:
                cell.fill = PatternFill(
                    start_color=DARK_BLUE, end_color=DARK_BLUE, fill_type="solid"
                )
                cell.font = Font(color=WHITE, bold=True)
                cell.alignment = Alignment(horizontal="center")
            elif is_top_level:
                cell.fill = PatternFill(
                    start_color=LIGHT_BLUE, end_color=LIGHT_BLUE, fill_type="solid"
                )
                cell.font = Font(bold=True)
                cell.alignment = Alignment(horizontal="center")
                if col_idx == 2:
                    cell.alignment = Alignment(horizontal="left")
            else:
                cell.alignment = Alignment(horizontal="center")
                if col_idx == 2:
                    cell.alignment = Alignment(horizontal="left", indent=int(level))

    for col_idx, col_cells in enumerate(worksheet.columns, start=1):
        max_len = max((len(str(cell.value or "")) for cell in col_cells), default=0)
        col_letter = get_column_letter(col_idx)
        worksheet.column_dimensions[col_letter].width = (
            min(max_len + 3, 60) if col_idx == 2 else max(9, min(max_len + 2, 18))
        )

    worksheet.freeze_panes = "A2"


def main() -> None:
    """Build a consolidated category-counts workbook for every input file.

    For every entry in ``INPUT_FILES``, reads the configured sheet, builds
    its hierarchical count report using ``GROUP_COLUMNS``, and writes it
    to its own sheet in ``OUTPUT_FILE``. The workbook is written
    atomically: results are staged to a temporary file and only moved
    into place once every sheet has been written successfully.

    Raises:
        FileNotFoundError: If a configured input file does not exist.
        KeyError: If a configured input file is missing a group column.
        ValueError: If a configured input file has an unsupported
            extension, or ``GROUP_COLUMNS`` is empty or has duplicates.
    """
    logger.info("=" * 80)
    logger.info("Count-By-Categories SCRIPT STARTED")
    logger.info(f"Input files: {INPUT_FILES}")
    logger.info(f"Group columns: {GROUP_COLUMNS}")
    logger.info(f"Output file: {OUTPUT_FILE}")

    # Build every report before touching the output file, so a bad input
    # (missing file, missing column, ...) fails loudly instead of leaving a
    # half-written workbook or an empty one behind.
    used_sheet_names: set[str] = set()
    reports: list[tuple[str, pd.DataFrame]] = []

    for input_file in INPUT_FILES:
        dataframe = _read_input_file(input_file)
        logger.info(f"  {len(dataframe):,} rows loaded")

        report_df = count_by_categories(dataframe, GROUP_COLUMNS, BLANK_LABEL)
        sheet_name = _unique_sheet_name(input_file["sheetName"], used_sheet_names)
        reports.append((sheet_name, report_df))

        logger.info(
            f"  Report built: {len(report_df):,} rows across "
            f"{len(GROUP_COLUMNS)} level(s) -> sheet '{sheet_name}'"
        )

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    temp_output_file = OUTPUT_FILE.with_suffix(f"{OUTPUT_FILE.suffix}.tmp")

    try:
        with pd.ExcelWriter(temp_output_file, engine="openpyxl") as writer:
            for sheet_name, report_df in reports:
                report_df.to_excel(writer, sheet_name=sheet_name, index=False)
                _style_worksheet(writer.sheets[sheet_name], report_df)

        temp_output_file.replace(OUTPUT_FILE)
    finally:
        temp_output_file.unlink(missing_ok=True)

    logger.info(f"Wrote consolidated workbook to {OUTPUT_FILE}")
    logger.info("SCRIPT COMPLETED SUCCESSFULLY")


if __name__ == "__main__":
    main()
