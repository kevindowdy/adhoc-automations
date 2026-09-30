from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Sequence, TypedDict

import pandas as pd

INPUT_FILE = r"C:\Users\fbfepde\Documents\Temporary\FIG_Closed_Vulnerabilities\FIG_Closed_Vulnerabilities_20260929.parquet"

all_closed_vulns = pd.read_parquet(INPUT_FILE)

# Column holding each row's severity. Raw values are matched against
# SEVERITY_LEVELS case-insensitively (see filter_to_configured_severities()).
SEVERITY_COLUMN: Final[str] = "vulnerability.severity"

# Only rows whose severity matches one of these are included in the stats.
SEVERITY_LEVELS: Final[list[str]] = ["critical", "high"]

CLASS_LEVELS = ["class 1", "class 2", "class 3"]

# Column holding each row's numeric days-past-due value at remediation time.
DAYS_PAST_DUE_COLUMN: Final[str] = "saltminer.attributes.DaysPastDue"

normalized_severity = (
        all_closed_vulns[SEVERITY_COLUMN].astype(str).str.strip().str.casefold()
    )

print(normalized_severity.head)

ch_closed_vulnerabilities = all_closed_vulns.loc[normalized_severity.isin(SEVERITY_LEVELS)].copy()

print(len(ch_closed_vulnerabilities))

#####

normalized_classes = (
        ch_closed_vulnerabilities["saltminer.inventory_asset.attributes.appmap.class"].astype(str).str.strip().str.casefold()
    )

print(normalized_classes.head)

ch_closed_vulnerabilities_classes123 = ch_closed_vulnerabilities.loc[normalized_classes.isin(CLASS_LEVELS)].copy()

print(len(ch_closed_vulnerabilities_classes123))

###

CLOSED_DATE_COLUMN: Final[str] = "saltminer.attributes.DateClosed"

closed_dates = pd.to_datetime(
    ch_closed_vulnerabilities_classes123[CLOSED_DATE_COLUMN],
    errors="coerce",
)

ch_closed_vulnerabilities_classes123 = (
    ch_closed_vulnerabilities_classes123.loc[
        (closed_dates.dt.year == 2026)
        & (closed_dates.dt.month == 9)
    ].copy()
)

print(
    f"Rows closed in January: {len(ch_closed_vulnerabilities_classes123)}"
)

###

total = len(ch_closed_vulnerabilities_classes123)
days_past_due = pd.to_numeric(ch_closed_vulnerabilities_classes123["saltminer.attributes.DaysPastDue"], errors="coerce")
on_time_count = int((days_past_due <= 0).sum())

on_time_percentage = (on_time_count / total) * 100

print("The on-time remediation rate is " + f"{on_time_count}/{total} ({on_time_percentage:.1f}%).")

ch_closed_vulnerabilities_classes123.to_clipboard()

