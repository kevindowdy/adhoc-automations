import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Sequence, TypedDict

import pandas as pd

BASE_PATH = Path(r"C:\Users\fbfepde\Downloads")

INPUT_FILES = [
    # {"filePath": fr"{BASE_PATH}\FIG Open Vulnerabilities_20260102.xlsx", "month": "January"},
    # {"filePath": fr"{BASE_PATH}\FIG Open Vulnerabilities_20260202.xlsx", "month": "February"},
    # {"filePath": fr"{BASE_PATH}\FIG Open Vulnerabilities_20260302.xlsx", "month": "March"},
    # {"filePath": fr"{BASE_PATH}\FIG Open Vulnerabilities_20260401.xlsx", "month": "April"},
    # {"filePath": fr"{BASE_PATH}\FIG Open Vulnerabilities_20260504.xlsx", "month": "May"},
    # {"filePath": fr"{BASE_PATH}\FIG Open Vulnerabilities_20260601.xlsx", "month": "June"},
    # {"filePath": fr"{BASE_PATH}\FIG Open Vulnerabilities_20260701.xlsx", "month": "July"},
    # {"filePath": fr"{BASE_PATH}\FIG Open Vulnerabilities_20260803.xlsx", "month": "August"},
    # {"filePath": fr"{BASE_PATH}\FIG Open Vulnerabilities_20260901.xlsx", "month": "September"},
    {"filePath": fr"{BASE_PATH}\FIG Open Vulnerabilities_20260922.xlsx", "month": "Today"},
]

OUTPUT_FILE = "data/output/filtered_vulnerabilities.xlsx"

"""
    These filters work for any combination of string values you are searching for.
    Results may differ when searching for dates values
"""
FILTERS = {
    # "saltminer.inventory_asset.attributes.appmap.apm_number": ["APM0001026", "APM0001024"],
    "vulnerability.severity": ["Critical"],
    "saltminer.attributes.DaysPastDue": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "30"]
}


def filter_vulnerabilities(df):
    mask = pd.Series(True, index=df.index)

    for column, values in FILTERS.items():
        mask &= df[column].isin(values)

    return df[mask]


def main():

    for input in INPUT_FILES:
        dataframe = pd.read_excel(input["filePath"], 0)
        filtered_df = filter_vulnerabilities(dataframe)
        print(f"Month: {input['month']}, Count: {len(filtered_df)}")

        try:
            with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
                    filtered_df.to_excel(writer, index=False)
        finally:
            print("isssues found")

if __name__ == "__main__":
    main()
