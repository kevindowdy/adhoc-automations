# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `calculate_on_time_remediation.py`: computes on-time vs. late
  remediation stats for closed vulnerabilities. Each configured input file
  (already closed-only) is processed independently: rows are filtered down
  to `SEVERITY_LEVELS` (defaults to `["Critical", "High"]`), then split
  into "late" (`DaysPastDue` > 0, matching the existing past-due
  definition in `filter_past_due_vulnerabilities.py`) and "on time"
  (everything else -- zero, negative, or missing/non-numeric `DaysPastDue`
  values all count as on time, so the two counts always add up to the
  total). A one-sentence summary per file is logged, e.g. "As of today,
  for September: 42 Critical/High vulnerabilities have been remediated. 5
  were remediated late and 37 were remediated on time. The on-time
  remediation rate is 37/42 (88.1%)." Nothing is written to disk -- the
  deliverable is the logged summary, not a report file. Input files may be
  `.csv`, `.tsv`, `.xlsx`, `.xls`, or `.parquet`.
- `tests/unit/test_calculate_on_time_remediation.py` and
  `tests/integration/test_calculate_on_time_remediation_logging.py`: unit
  coverage for the severity filter, stats calculation, and summary
  formatting, plus end-to-end integration tests that run `main()` against
  real CSV/Excel/Parquet input files and assert on the logged summaries.

### Fixed

- `count_by_categories.py`: the internal nesting-level marker (previously
  written as a misleadingly-named
  `saltminer.inventory_asset.attributes.appmap.cio` column, always `0` with
  the current single-level `GROUP_COLUMNS` config) is no longer written to
  the output workbook. It's still tracked internally for row shading and
  category indentation, it just doesn't appear as a column anymore.

### Added

- `count_by_categories.py`: uses vulnerability.severity as the severity identification field
- `count_by_categories.py`: each report row can now optionally carry a
  severity breakdown and/or a days-past-due breakdown alongside the raw
  count, e.g. `Application Owner | Total Past Due | Very Critical |
  Critical | High | 1-30 Days | 31-60 Days | 61-180 Days | 181-365 Days |
  >365 Days`. Both are independently configurable and optional:
  `SEVERITY_COLUMN`/`SEVERITY_LEVELS` control the severity columns and
  `DAYS_PAST_DUE_COLUMN`/`DAY_BUCKETS` control the day-bucket columns
  (each bucket is an inclusive `{label, min_days, max_days}` range, with
  `max_days: None` for an open-ended top bucket); setting either column
  constant to `None` skips that breakdown entirely. The categorization
  logic lives in two standalone, independently testable functions --
  `categorize_severity()` (case-insensitive match against
  `SEVERITY_LEVELS`) and `categorize_days_past_due()` (buckets a numeric
  days-past-due value) -- so either can be tweaked without touching the
  report-building logic.

### Changed

- `count_by_categories.py`: converted from a CLI tool (`--columns`,
  `--output`, `--sheet-name`) into a config-driven automation, matching
  `filter_past_due_vulnerabilities.py`. `INPUT_FILES` at the top of the
  script now lists any number of `{filePath, sheetName}` pairs; each is
  summarized independently using the shared `GROUP_COLUMNS` list and
  written to its own (auto-deduplicated) sheet in a single consolidated
  `OUTPUT_FILE` workbook, instead of one file/sheet per run. Also fixed a
  bug where a missing/invalid first input file raised a confusing
  `IndexError` from an empty Excel workbook instead of surfacing the
  underlying error, by building every report before opening the output
  workbook.

### Added

- `count_by_categories.py`: builds a hierarchical raw row-count table from
  any dataset (CSV, TSV, or Excel) and any ordered list of grouping
  columns. Each column becomes a nesting level, with sub-rows indented
  directly under their matching parent row and a trailing `Grand Total`
  row, generalizing the top-level/sub-level rollup pattern used in the
  vulnerability tracking report to an arbitrary number of columns. Values
  are raw row counts only; no filtering or categorization logic is
  applied. The output workbook is written atomically.
- `tests/unit/test_count_by_categories.py` and
  `tests/integration/test_count_by_categories_workbook.py`: unit coverage
  for the counting logic and sheet-naming helpers, plus an end-to-end
  integration test that runs `main()` against real CSV/Excel input files
  and asserts on the resulting multi-sheet workbook.
- `filter_past_due_vulnerabilities.py`: filters one or more open SDLC
  vulnerability exports down to past-due vulnerabilities (rows where
  `Days Past Due` > 0), tags each result with its reporting month, and
  writes a consolidated Excel workbook with one sheet per month plus a
  `Summary` sheet totaling past-due counts by month.
- `requirements.txt` with `pandas` and `openpyxl`, needed to read/write
  Excel workbooks.

## [0.1.0] - 2026-09-21

### Added

- Initial project template: source layout, test scaffolding, CI/CD
  workflows, and contributor documentation.
