import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Sequence, TypedDict

import pandas as pd

BASE_PATH = Path(r"C:\Users\fbfepde\Downloads")

INPUT_FILES = [
    {"filePath": fr"{BASE_PATH}\FIG Open Vulnerabilities_20260102.xlsx", "month": "January"},
    {"filePath": fr"{BASE_PATH}\FIG Open Vulnerabilities_20260202.xlsx", "month": "February"},
    {"filePath": fr"{BASE_PATH}\FIG Open Vulnerabilities_20260302.xlsx", "month": "March"},
    {"filePath": fr"{BASE_PATH}\FIG Open Vulnerabilities_20260401.xlsx", "month": "April"},
    {"filePath": fr"{BASE_PATH}\FIG Open Vulnerabilities_20260504.xlsx", "month": "May"},
    {"filePath": fr"{BASE_PATH}\FIG Open Vulnerabilities_20260601.xlsx", "month": "June"},
    {"filePath": fr"{BASE_PATH}\FIG Open Vulnerabilities_20260701.xlsx", "month": "July"},
    {"filePath": fr"{BASE_PATH}\FIG Open Vulnerabilities_20260803.xlsx", "month": "August"},
    {"filePath": fr"{BASE_PATH}\FIG Open Vulnerabilities_20260901.xlsx", "month": "September"},
    {"filePath": fr"{BASE_PATH}\FIG Open Vulnerabilities_20260922.xlsx", "month": "Today"},
]

def main():

    for input in INPUT_FILES:
        dataframe = pd.read_excel(input["filePath"], 0)

        print(f"Month: {input['month']}, Count: {len(dataframe)}")


if __name__ == "__main__":
    main()
