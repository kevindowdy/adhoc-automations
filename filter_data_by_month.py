import pandas as pd

# ============================================================================
# File Paths
# ============================================================================
suppressed_file = fr"C:\Users\fbfepde\Documents\Temporary\FIG_Suppressed_Vulnerabilities\FIG Suppressed Vulnerabilities_20261007.parquet"
closed_file = fr"C:\Users\fbfepde\Documents\Temporary\FIG_Closed_Vulnerabilities\FIG_Closed_Vulnerabilities_20261007.parquet"

# ============================================================================
# Open suppressed vulnerabilities
# ============================================================================
df_suppressed = pd.read_parquet(suppressed_file)

# ============================================================================
# Open closed vulnerabilities
# ============================================================================
df_closed = pd.read_parquet(closed_file)

# ============================================================================
# Convert date columns
# Adjust column names if necessary
# ============================================================================
df_closed["saltminer.attributes.DateClosed"] = pd.to_datetime(df_closed["saltminer.attributes.DateClosed"], errors="coerce")
df_suppressed["Suppressed Date"] = pd.to_datetime(df_suppressed["Suppressed Date"], format="mixed", errors="coerce")

# ============================================================================
# Get vulnerabilities closed in month of August
# ============================================================================
closed_august = df_closed[df_closed["saltminer.attributes.DateClosed"].dt.month == 8]

# ============================================================================
# Get vulnerabilities closed in month of September
# ============================================================================
closed_september = df_closed[df_closed["saltminer.attributes.DateClosed"].dt.month == 9]

# ============================================================================
# Get vulnerabilities suppressed in month of August
# ============================================================================
suppressed_august = df_suppressed[
    df_suppressed["Suppressed Date"].dt.month == 8
]

# ============================================================================
# Get vulnerabilities suppressed in month of September
# ============================================================================
suppressed_september = df_suppressed[
    df_suppressed["Suppressed Date"].dt.month == 9
]

# ============================================================================
# Combined data for all months and statuses
# ============================================================================
df_closed["Status"] = "Closed"
df_suppressed["Status"] = "Suppressed"

combined_df = pd.concat(
    [df_closed, df_suppressed],
    ignore_index=True,
    sort=False
)

# ============================================================================
# Print vulnerabilities closed or suppressed in August
# ============================================================================
august_combined = pd.concat(
    [closed_august, suppressed_august],
    ignore_index=True,
    sort=False
)

print("\n=== Closed or Suppressed in August ===")
print(f"Count: {len(august_combined):,}")

# ============================================================================
# Print vulnerabilities closed or suppressed in September
# ============================================================================
september_combined = pd.concat(
    [closed_september, suppressed_september],
    ignore_index=True,
    sort=False
)

print("\n=== Closed or Suppressed in September ===")
print(f"Count: {len(september_combined):,}")

# ============================================================================
# Optional detailed counts
# ============================================================================
print("\n--- August ---")
print(f"Closed:      {len(closed_august):,}")
print(f"Suppressed:  {len(suppressed_august):,}")

print("\n--- September ---")
print(f"Closed:      {len(closed_september):,}")
print(f"Suppressed:  {len(suppressed_september):,}")


print("\n=== August Closed Severity ===")
print(
    closed_august["vulnerability.severity"]
    .value_counts(dropna=False)
)

print("\n=== August Suppressed Severity ===")
print(
    suppressed_august["vulnerability.severity"]
    .value_counts(dropna=False)
)

print("\n=== September Closed Severity ===")
print(
    closed_september["vulnerability.severity"]
    .value_counts(dropna=False)
)

print("\n=== September Suppressed Severity ===")
print(
    suppressed_september["vulnerability.severity"]
    .value_counts(dropna=False)
)
