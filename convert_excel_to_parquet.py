"""
Convert CSV or Excel data to an parquet file named:

Rename the first worksheet to:
    FIG Open Vulnerabilities
"""
from pathlib import Path
from datetime import datetime
import pandas as pd
import getpass


username = getpass.getuser()

FILENAME = "FIG Open Vulnerabilities_20260923.xlsx"

BASE_PATH = f"C:/Users/{username}/Downloads"

FILEPATH = f"{BASE_PATH}/{FILENAME}"

print(f"Opening: {FILEPATH}")

if "xlsx" in FILEPATH:
    df = pd.read_excel(fr"{FILEPATH}", dtype=str)
else:
    df = pd.read_csv(fr"{FILEPATH}", dtype=str)


object_cols = df.select_dtypes(include=["object"]).columns

for col in object_cols:
    df[col] = df[col].fillna("").astype(str)


df.to_parquet(fr"{FILENAME.split(".")[0]}.parquet", index=False)

print(f"Created: {FILENAME.split(".")[0]}.parquet")

