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

    report = cbc.count_by_categories(
        dataframe, ["Owner"], severity_column=None, days_past_due_column=None
    )

    assert list(report[cbc.CATEGORY_COLUMN]) == ["Alice", "Bob", "Grand Total"]
    assert list(report[cbc.COUNT_COLUMN]) == [3, 1, 4]
    assert list(report[cbc.LEVEL_COLUMN]) == [0, 0, ""]
    assert list(report.columns) == [
        cbc.LEVEL_COLUMN,
        cbc.CATEGORY_COLUMN,
        cbc.COUNT_COLUMN,
    ]


def test_two_columns_nest_second_under_first_with_indentation() -> None:
    dataframe = pd.DataFrame(
        {
            "Owner": ["Alice", "Alice", "Bob"],
            "App": ["Payments", "Ledger", "Payments"],
        }
    )

    report = cbc.count_by_categories(
        dataframe, ["Owner", "App"], severity_column=None, days_past_due_column=None
    )

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

    report = cbc.count_by_categories(
        dataframe,
        ["Owner"],
        blank_label="(Blank)",
        severity_column=None,
        days_past_due_column=None,
    )

    rows = dict(zip(report[cbc.CATEGORY_COLUMN], report[cbc.COUNT_COLUMN]))
    assert rows["(Blank)"] == 2
    assert rows["Alice"] == 2
    assert rows["Grand Total"] == 4


def test_empty_group_columns_raises_value_error() -> None:
    dataframe = pd.DataFrame({"Owner": ["Alice"]})

    with pytest.raises(ValueError, match="At least one group-by column"):
        cbc.count_by_categories(
            dataframe, [], severity_column=None, days_past_due_column=None
        )


def test_duplicate_group_columns_raise_value_error() -> None:
    dataframe = pd.DataFrame({"Owner": ["Alice"]})

    with pytest.raises(ValueError, match="duplicates"):
        cbc.count_by_categories(
            dataframe,
            ["Owner", "Owner"],
            severity_column=None,
            days_past_due_column=None,
        )


def test_missing_group_column_raises_key_error() -> None:
    dataframe = pd.DataFrame({"Owner": ["Alice"]})

    with pytest.raises(KeyError, match="Nonexistent"):
        cbc.count_by_categories(
            dataframe,
            ["Nonexistent"],
            severity_column=None,
            days_past_due_column=None,
        )


def test_source_dataframe_is_not_mutated() -> None:
    dataframe = pd.DataFrame({"Owner": ["Alice", None]})
    original = dataframe.copy(deep=True)

    cbc.count_by_categories(
        dataframe, ["Owner"], severity_column=None, days_past_due_column=None
    )

    pd.testing.assert_frame_equal(dataframe, original)


# =============================================================================
# categorize_severity()
# =============================================================================


def test_categorize_severity_matches_case_and_whitespace_insensitively() -> None:
    assert cbc.categorize_severity("critical") == "Critical"
    assert cbc.categorize_severity(" CRITICAL ") == "Critical"
    assert cbc.categorize_severity("Very Critical") == "Very Critical"
    assert cbc.categorize_severity("High") == "High"


def test_categorize_severity_returns_trimmed_raw_value_when_unmatched() -> None:
    assert cbc.categorize_severity("Medium") == "Medium"
    assert cbc.categorize_severity("  Low  ") == "Low"


def test_categorize_severity_returns_empty_string_for_missing_value() -> None:
    assert cbc.categorize_severity(None) == ""
    assert cbc.categorize_severity(float("nan")) == ""


# =============================================================================
# categorize_days_past_due()
# =============================================================================


@pytest.mark.parametrize(
    ("days", "expected_label"),
    [
        (1, "1-30 Days"),
        (30, "1-30 Days"),
        (31, "31-60 Days"),
        (60, "31-60 Days"),
        (61, "61-180 Days"),
        (180, "61-180 Days"),
        (181, "181-365 Days"),
        (365, "181-365 Days"),
        (366, ">365 Days"),
        (10_000, ">365 Days"),
    ],
)
def test_categorize_days_past_due_buckets_by_inclusive_range(
    days: int, expected_label: str
) -> None:
    assert cbc.categorize_days_past_due(days) == expected_label


def test_categorize_days_past_due_accepts_numeric_strings() -> None:
    assert cbc.categorize_days_past_due("45") == "31-60 Days"


@pytest.mark.parametrize("days", [0, -5, "not-a-number", None, float("nan")])
def test_categorize_days_past_due_returns_none_when_not_past_due_or_invalid(
    days: object,
) -> None:
    assert cbc.categorize_days_past_due(days) is None


def test_categorize_days_past_due_uses_custom_buckets() -> None:
    custom_buckets: list[cbc.DayBucket] = [
        {"label": "Fresh", "min_days": 1, "max_days": 10},
        {"label": "Stale", "min_days": 11, "max_days": None},
    ]

    assert cbc.categorize_days_past_due(5, custom_buckets) == "Fresh"
    assert cbc.categorize_days_past_due(500, custom_buckets) == "Stale"


# =============================================================================
# count_by_categories() -- severity and days-past-due breakdowns
# =============================================================================


def _vulnerability_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Owner": ["Alice", "Alice", "Alice", "Bob", "Bob"],
            "Severity": ["Critical", "High", "High", "Very Critical", "Medium"],
            "DaysPastDue": [10, 45, 400, 200, 1],
        }
    )


def test_severity_breakdown_adds_one_column_per_configured_level() -> None:
    report = cbc.count_by_categories(
        _vulnerability_dataframe(),
        ["Owner"],
        severity_column="Severity",
        severity_levels=["Very Critical", "Critical", "High"],
        days_past_due_column=None,
    )

    rows = report.set_index(cbc.CATEGORY_COLUMN)
    assert rows.loc["Alice", "Very Critical"] == 0
    assert rows.loc["Alice", "Critical"] == 1
    assert rows.loc["Alice", "High"] == 2
    assert rows.loc["Bob", "Very Critical"] == 1
    assert rows.loc["Bob", "Critical"] == 0
    # "Medium" isn't a configured severity level, so it isn't counted in
    # any breakdown column, but the row's total still reflects it.
    assert rows.loc["Bob", "High"] == 0
    assert rows.loc["Bob", cbc.COUNT_COLUMN] == 2
    assert rows.loc["Grand Total", "Very Critical"] == 1
    assert rows.loc["Grand Total", "Critical"] == 1
    assert rows.loc["Grand Total", "High"] == 2


def test_days_past_due_breakdown_adds_one_column_per_configured_bucket() -> None:
    day_buckets: list[cbc.DayBucket] = [
        {"label": "1-30 Days", "min_days": 1, "max_days": 30},
        {"label": "31-60 Days", "min_days": 31, "max_days": 60},
        {"label": ">365 Days", "min_days": 366, "max_days": None},
    ]

    report = cbc.count_by_categories(
        _vulnerability_dataframe(),
        ["Owner"],
        severity_column=None,
        days_past_due_column="DaysPastDue",
        day_buckets=day_buckets,
    )

    rows = report.set_index(cbc.CATEGORY_COLUMN)
    assert rows.loc["Alice", "1-30 Days"] == 1
    assert rows.loc["Alice", "31-60 Days"] == 1
    assert rows.loc["Alice", ">365 Days"] == 1
    assert rows.loc["Bob", "1-30 Days"] == 1  # DaysPastDue=1
    assert rows.loc["Bob", "31-60 Days"] == 0
    assert rows.loc["Bob", ">365 Days"] == 0
    assert rows.loc["Grand Total", "1-30 Days"] == 2
    assert rows.loc["Grand Total", ">365 Days"] == 1


def test_severity_and_days_past_due_breakdowns_combine_with_expected_column_order() -> (
    None
):
    report = cbc.count_by_categories(
        _vulnerability_dataframe(),
        ["Owner"],
        severity_column="Severity",
        severity_levels=["Very Critical", "Critical", "High"],
        days_past_due_column="DaysPastDue",
        day_buckets=[
            {"label": "1-30 Days", "min_days": 1, "max_days": 30},
            {"label": ">30 Days", "min_days": 31, "max_days": None},
        ],
    )

    assert list(report.columns) == [
        cbc.LEVEL_COLUMN,
        cbc.CATEGORY_COLUMN,
        cbc.COUNT_COLUMN,
        "Very Critical",
        "Critical",
        "High",
        "1-30 Days",
        ">30 Days",
    ]


def test_missing_severity_column_raises_key_error() -> None:
    dataframe = pd.DataFrame({"Owner": ["Alice"]})

    with pytest.raises(KeyError, match="Severity"):
        cbc.count_by_categories(
            dataframe,
            ["Owner"],
            severity_column="Severity",
            days_past_due_column=None,
        )


def test_missing_days_past_due_column_raises_key_error() -> None:
    dataframe = pd.DataFrame({"Owner": ["Alice"]})

    with pytest.raises(KeyError, match="DaysPastDue"):
        cbc.count_by_categories(
            dataframe,
            ["Owner"],
            severity_column=None,
            days_past_due_column="DaysPastDue",
        )


def test_empty_severity_levels_with_severity_column_raises_value_error() -> None:
    with pytest.raises(ValueError, match="severity_levels"):
        cbc.count_by_categories(
            _vulnerability_dataframe(),
            ["Owner"],
            severity_column="Severity",
            severity_levels=[],
            days_past_due_column=None,
        )


def test_empty_day_buckets_with_days_past_due_column_raises_value_error() -> None:
    with pytest.raises(ValueError, match="day_buckets"):
        cbc.count_by_categories(
            _vulnerability_dataframe(),
            ["Owner"],
            severity_column=None,
            days_past_due_column="DaysPastDue",
            day_buckets=[],
        )


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
