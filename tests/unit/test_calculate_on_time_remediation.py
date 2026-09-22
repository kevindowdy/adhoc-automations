"""Unit tests for the pure/helper logic in ``calculate_on_time_remediation``."""

from __future__ import annotations

import pandas as pd
import pytest

import calculate_on_time_remediation as otr

# =============================================================================
# filter_to_configured_severities()
# =============================================================================


def test_filter_keeps_only_configured_severities() -> None:
    dataframe = pd.DataFrame({"Severity": ["Critical", "High", "Low", "Medium"]})

    filtered = otr.filter_to_configured_severities(
        dataframe, "Severity", ["Critical", "High"]
    )

    assert list(filtered["Severity"]) == ["Critical", "High"]


def test_filter_matches_case_insensitively_and_trims_whitespace() -> None:
    dataframe = pd.DataFrame({"Severity": ["critical ", " HIGH", "low"]})

    filtered = otr.filter_to_configured_severities(
        dataframe, "Severity", ["Critical", "High"]
    )

    assert list(filtered["Severity"]) == ["critical ", " HIGH"]


def test_filter_preserves_original_index() -> None:
    dataframe = pd.DataFrame(
        {"Severity": ["Low", "Critical", "Low", "High"]}, index=[10, 11, 12, 13]
    )

    filtered = otr.filter_to_configured_severities(
        dataframe, "Severity", ["Critical", "High"]
    )

    assert list(filtered.index) == [11, 13]


def test_filter_missing_column_raises_key_error() -> None:
    dataframe = pd.DataFrame({"Other": ["Critical"]})

    with pytest.raises(KeyError, match="Severity"):
        otr.filter_to_configured_severities(dataframe, "Severity", ["Critical"])


def test_filter_empty_severity_levels_raises_value_error() -> None:
    dataframe = pd.DataFrame({"Severity": ["Critical"]})

    with pytest.raises(ValueError, match="severity_levels must not be empty"):
        otr.filter_to_configured_severities(dataframe, "Severity", [])


def test_filter_does_not_mutate_input() -> None:
    dataframe = pd.DataFrame({"Severity": ["Critical", "Low"]})
    original = dataframe.copy()

    otr.filter_to_configured_severities(dataframe, "Severity", ["Critical"])

    pd.testing.assert_frame_equal(dataframe, original)


# =============================================================================
# calculate_on_time_remediation_stats()
# =============================================================================


def test_stats_splits_late_and_on_time_by_days_past_due() -> None:
    dataframe = pd.DataFrame({"DaysPastDue": [10, 0, -5, 1, -100]})

    stats = otr.calculate_on_time_remediation_stats(dataframe, "DaysPastDue")

    assert stats.total == 5
    assert stats.late_count == 2  # 10, 1
    assert stats.on_time_count == 3  # 0, -5, -100


def test_stats_treats_missing_and_non_numeric_values_as_on_time() -> None:
    dataframe = pd.DataFrame({"DaysPastDue": [10, None, "not a number", 5]})

    stats = otr.calculate_on_time_remediation_stats(dataframe, "DaysPastDue")

    assert stats.total == 4
    assert stats.late_count == 2  # 10, 5
    assert stats.on_time_count == 2  # None, "not a number"


def test_stats_total_always_equals_late_plus_on_time() -> None:
    dataframe = pd.DataFrame({"DaysPastDue": [10, 0, -5, None, "bad", 1, 999, -1]})

    stats = otr.calculate_on_time_remediation_stats(dataframe, "DaysPastDue")

    assert stats.total == stats.late_count + stats.on_time_count


def test_stats_empty_dataframe_returns_zero_counts() -> None:
    dataframe = pd.DataFrame({"DaysPastDue": []})

    stats = otr.calculate_on_time_remediation_stats(dataframe, "DaysPastDue")

    assert stats == otr.OnTimeRemediationStats(total=0, late_count=0, on_time_count=0)


def test_stats_missing_column_raises_key_error() -> None:
    dataframe = pd.DataFrame({"Other": [1, 2]})

    with pytest.raises(KeyError, match="DaysPastDue"):
        otr.calculate_on_time_remediation_stats(dataframe, "DaysPastDue")


# =============================================================================
# format_on_time_remediation_summary()
# =============================================================================


def test_format_normal_summary_reports_counts_and_percentage() -> None:
    stats = otr.OnTimeRemediationStats(total=10, late_count=3, on_time_count=7)

    summary = otr.format_on_time_remediation_summary(
        "September", ["Critical", "High"], stats
    )

    assert "September" in summary
    assert "Critical/High" in summary
    assert "10 Critical/High vulnerabilities have been remediated" in summary
    assert "3 were remediated late" in summary
    assert "7 were remediated on time" in summary
    assert "7/10 (70.0%)" in summary


def test_format_zero_total_reports_no_vulnerabilities_found() -> None:
    stats = otr.OnTimeRemediationStats(total=0, late_count=0, on_time_count=0)

    summary = otr.format_on_time_remediation_summary(
        "September", ["Critical", "High"], stats
    )

    assert summary == (
        "As of today, for September: no Critical/High closed " "vulnerabilities found."
    )
    assert "%" not in summary


def test_format_percentage_rounds_to_one_decimal_place() -> None:
    stats = otr.OnTimeRemediationStats(total=3, late_count=1, on_time_count=2)

    summary = otr.format_on_time_remediation_summary("Q1", ["Critical"], stats)

    assert "(66.7%)" in summary
