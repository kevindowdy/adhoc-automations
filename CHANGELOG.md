# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `count_by_categories.py`: builds a hierarchical raw row-count table from
  any dataset (CSV, TSV, or Excel) and any ordered list of grouping
  columns, passed via `--columns`. Each column becomes a nesting level,
  with sub-rows indented directly under their matching parent row and a
  trailing `Grand Total` row, generalizing the top-level/sub-level rollup
  pattern used in the vulnerability tracking report to an arbitrary number
  of columns. Values are raw row counts only; no filtering or
  categorization logic is applied. Output can be written to `.csv` or a
  styled `.xlsx` and is written atomically.
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
