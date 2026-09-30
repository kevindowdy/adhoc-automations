"""
Convert today's CSV data to an Excel file named:
    FIG Open Vulnerabilities_[YYYYMMDD].xlsx

Rename the first worksheet to:
    FIG Open Vulnerabilities
"""
from pathlib import Path
from datetime import datetime
import pandas as pd

username = "fbfepde" ## REPLACE WITH USERNAME

BASE_PATH = f"C:/Users/{username}/Documents/Temporary/FIG_Open_Vulnerabilities"

FILEPATH = f"{BASE_PATH}/FIG Open Vulnerabilities_20260923.xlsx"

if "xlsx" in FILEPATH:
    df = pd.read_excel(fr"{FILEPATH}", dtype=str)
else:
    df = pd.read_csv(fr"{FILEPATH}", dtype=str)


print(f"Created: {FILEPATH}.xlsx")

object_cols = df.select_dtypes(include=["object"]).columns

for col in object_cols:
    df[col] = df[col].fillna("").astype(str)

output_filename = FILEPATH.split(".")[0]

df.to_parquet(fr"{output_filename}.parquet", index=False)

print(f"Created: {output_filename}.parquet")

