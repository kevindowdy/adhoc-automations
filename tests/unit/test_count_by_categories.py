"""Unit tests for the pure/helper logic in ``count_by_categories``."""

from __future__ import annotations

import pandas as pd
import pytest

import count_by_categories as cbc

# =============================================================================
# count_by_categories()
# =============================================================================


def test_single_column_counts_and_grand_total() -> None:
    dataframe = pd.DataFrame({"Owner": ["Alice", "Bob", "Alice", "Alice"]})

    report = cbc.count_by_categories(dataframe, ["Owner"])

    assert list(report[cbc.CATEGORY_COLUMN]) == ["Alice", "Bob", "Grand Total"]
    assert list(report[cbc.COUNT_COLUMN]) == [3, 1, 4]
    assert list(report[cbc.LEVEL_COLUMN]) == [0, 0, ""]


def test_two_columns_nest_second_under_first_with_indentation() -> None:
    dataframe = pd.DataFrame(
        {
            "Owner": ["Alice", "Alice", "Bob"],
            "App": ["Payments", "Ledger", "Payments"],
        }
    )

    report = cbc.count_by_categories(dataframe, ["Owner", "App"])

    # Alice -> Ledger, Alice -> Payments (sorted), Bob -> Payments, Grand Total.
    assert list(report[cbc.CATEGORY_COLUMN]) == [
        "Alice",
        "  Ledger",
        "  Payments",
        "Bob",
        "  Payments",
        "Grand Total",
    ]
    assert list(report[cbc.COUNT_COLUMN]) == [2, 1, 1, 1, 1, 3]
    assert list(report[cbc.LEVEL_COLUMN]) == [0, 1, 1, 0, 1, ""]


def test_blank_and_missing_values_grouped_under_blank_label() -> None:
    dataframe = pd.DataFrame({"Owner": ["Alice", None, "  ", "Alice"]})

    report = cbc.count_by_categories(dataframe, ["Owner"], blank_label="(Blank)")

    rows = dict(zip(report[cbc.CATEGORY_COLUMN], report[cbc.COUNT_COLUMN]))
    assert rows["(Blank)"] == 2
    assert rows["Alice"] == 2
    assert rows["Grand Total"] == 4


def test_empty_group_columns_raises_value_error() -> None:
    dataframe = pd.DataFrame({"Owner": ["Alice"]})

    with pytest.raises(ValueError, match="At least one group-by column"):
        cbc.count_by_categories(dataframe, [])


def test_duplicate_group_columns_raise_value_error() -> None:
    dataframe = pd.DataFrame({"Owner": ["Alice"]})

    with pytest.raises(ValueError, match="duplicates"):
        cbc.count_by_categories(dataframe, ["Owner", "Owner"])


def test_missing_group_column_raises_key_error() -> None:
    dataframe = pd.DataFrame({"Owner": ["Alice"]})

    with pytest.raises(KeyError, match="Nonexistent"):
        cbc.count_by_categories(dataframe, ["Nonexistent"])


def test_source_dataframe_is_not_mutated() -> None:
    dataframe = pd.DataFrame({"Owner": ["Alice", None]})
    original = dataframe.copy(deep=True)

    cbc.count_by_categories(dataframe, ["Owner"])

    pd.testing.assert_frame_equal(dataframe, original)


# =============================================================================
# _read_input_file()
# =============================================================================


def test_read_input_file_missing_path_raises(tmp_path) -> None:
    missing = tmp_path / "does_not_exist.csv"

    with pytest.raises(FileNotFoundError, match="not found"):
        cbc._read_input_file({"filePath": str(missing), "sheetName": ""})


def test_read_input_file_unsupported_extension_raises(tmp_path) -> None:
    bad_file = tmp_path / "data.txt"
    bad_file.write_text("Owner\nAlice\n")

    with pytest.raises(ValueError, match="Unsupported input file extension"):
        cbc._read_input_file({"filePath": str(bad_file), "sheetName": ""})


def test_read_input_file_reads_csv_as_strings(tmp_path) -> None:
    csv_file = tmp_path / "data.csv"
    csv_file.write_text("Owner,Count\nAlice,1\nBob,2\n")

    dataframe = cbc._read_input_file({"filePath": str(csv_file), "sheetName": ""})

    assert list(dataframe["Owner"]) == ["Alice", "Bob"]
    assert list(dataframe["Count"]) == ["1", "2"]  # read as strings, not ints
    assert pd.api.types.is_string_dtype(dataframe["Count"])


def test_read_input_file_reads_named_excel_sheet(tmp_path) -> None:
    xlsx_file = tmp_path / "data.xlsx"
    with pd.ExcelWriter(xlsx_file, engine="openpyxl") as writer:
        pd.DataFrame({"Owner": ["Alice"]}).to_excel(
            writer, sheet_name="First", index=False
        )
        pd.DataFrame({"Owner": ["Bob", "Carol"]}).to_excel(
            writer, sheet_name="Second", index=False
        )

    dataframe = cbc._read_input_file(
        {"filePath": str(xlsx_file), "sheetName": "Second"}
    )

    assert list(dataframe["Owner"]) == ["Bob", "Carol"]


# =============================================================================
# sheet naming helpers
# =============================================================================


def test_sanitize_sheet_name_strips_invalid_characters_and_truncates() -> None:
    assert cbc._sanitize_sheet_name("Q1/Report:2026") == "Q1Report2026"
    assert cbc._sanitize_sheet_name("x" * 50) == "x" * cbc.SHEET_NAME_MAX_LENGTH


def test_sanitize_sheet_name_falls_back_when_nothing_valid_remains() -> None:
    assert cbc._sanitize_sheet_name("[]:*?/\\") == "Sheet"


def test_unique_sheet_name_returns_desired_name_when_unused() -> None:
    used: set[str] = set()

    assert cbc._unique_sheet_name("Sheet1", used) == "Sheet1"
    assert used == {"Sheet1"}


def test_unique_sheet_name_disambiguates_collisions() -> None:
    used = {"Sheet1"}

    first_collision = cbc._unique_sheet_name("Sheet1", used)
    second_collision = cbc._unique_sheet_name("Sheet1", used)

    assert first_collision == "Sheet1 (2)"
    assert second_collision == "Sheet1 (3)"
    assert used == {"Sheet1", "Sheet1 (2)", "Sheet1 (3)"}


def test_unique_sheet_name_stays_within_length_limit_when_disambiguated() -> None:
    used = {"x" * cbc.SHEET_NAME_MAX_LENGTH}

    disambiguated = cbc._unique_sheet_name("x" * 50, used)

    assert len(disambiguated) <= cbc.SHEET_NAME_MAX_LENGTH
    assert disambiguated.endswith(" (2)")
