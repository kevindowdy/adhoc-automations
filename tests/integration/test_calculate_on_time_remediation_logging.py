"""Integration test: main() logs one on-time remediation summary per file."""

from __future__ import annotations

import logging

import pandas as pd

import calculate_on_time_remediation as otr


def test_main_logs_one_summary_per_input_file_independently(
    tmp_path, monkeypatch, caplog
) -> None:
    # September: 2 Critical/High vulns, 1 late (DaysPastDue=5) and 1 on time
    # (DaysPastDue=0). A Low-severity row must be excluded from the stats.
    september_file = tmp_path / "september.csv"
    september_file.write_text(
        "vulnerability.severity,saltminer.attributes.DaysPastDue\n"
        "Critical,5\n"
        "High,0\n"
        "Low,99\n"
    )

    # October: 3 Critical/High vulns, all on time (0, -5, and a blank
    # DaysPastDue value, which must count as on time, not late).
    october_file = tmp_path / "october.xlsx"
    with pd.ExcelWriter(october_file, engine="openpyxl") as writer:
        pd.DataFrame(
            {
                "vulnerability.severity": ["Critical", "High", "High"],
                "saltminer.attributes.DaysPastDue": [0, -5, None],
            }
        ).to_excel(writer, sheet_name="Sheet1", index=False)

    monkeypatch.setattr(
        otr,
        "INPUT_FILES",
        [
            {"filePath": str(september_file), "label": "September"},
            {"filePath": str(october_file), "label": "October"},
        ],
    )
    monkeypatch.setattr(otr, "SEVERITY_LEVELS", ["Critical", "High"])

    with caplog.at_level(logging.INFO, logger="calculate_on_time_remediation"):
        otr.main()

    messages = [record.message for record in caplog.records]

    assert any(
        "As of today, for September: 2 Critical/High vulnerabilities have "
        "been remediated. 1 were remediated late and 1 were remediated on "
        "time. The on-time remediation rate is 1/2 (50.0%)." in message
        for message in messages
    )
    assert any(
        "As of today, for October: 3 Critical/High vulnerabilities have "
        "been remediated. 0 were remediated late and 3 were remediated on "
        "time. The on-time remediation rate is 3/3 (100.0%)." in message
        for message in messages
    )


def test_main_reads_parquet_input_files(tmp_path, monkeypatch, caplog) -> None:
    # 2 Critical/High vulns, 1 late (DaysPastDue=12) and 1 on time
    # (DaysPastDue=-2). A Low-severity row must be excluded from the stats.
    parquet_file = tmp_path / "december.parquet"
    pd.DataFrame(
        {
            "vulnerability.severity": ["Critical", "High", "Low"],
            "saltminer.attributes.DaysPastDue": [12, -2, 99],
        }
    ).to_parquet(parquet_file)

    monkeypatch.setattr(
        otr, "INPUT_FILES", [{"filePath": str(parquet_file), "label": "December"}]
    )
    monkeypatch.setattr(otr, "SEVERITY_LEVELS", ["Critical", "High"])

    with caplog.at_level(logging.INFO, logger="calculate_on_time_remediation"):
        otr.main()

    messages = [record.message for record in caplog.records]

    assert any(
        "As of today, for December: 2 Critical/High vulnerabilities have "
        "been remediated. 1 were remediated late and 1 were remediated on "
        "time. The on-time remediation rate is 1/2 (50.0%)." in message
        for message in messages
    )


def test_main_reports_no_vulnerabilities_found_when_file_has_no_matches(
    tmp_path, monkeypatch, caplog
) -> None:
    low_only_file = tmp_path / "low_only.csv"
    low_only_file.write_text(
        "vulnerability.severity,saltminer.attributes.DaysPastDue\nLow,10\n"
    )

    monkeypatch.setattr(
        otr, "INPUT_FILES", [{"filePath": str(low_only_file), "label": "November"}]
    )
    monkeypatch.setattr(otr, "SEVERITY_LEVELS", ["Critical", "High"])

    with caplog.at_level(logging.INFO, logger="calculate_on_time_remediation"):
        otr.main()

    messages = [record.message for record in caplog.records]

    assert any(
        "As of today, for November: no Critical/High closed vulnerabilities "
        "found." in message
        for message in messages
    )


def test_main_raises_when_an_input_file_is_missing(tmp_path, monkeypatch) -> None:
    missing_file = tmp_path / "does_not_exist.csv"

    monkeypatch.setattr(
        otr, "INPUT_FILES", [{"filePath": str(missing_file), "label": "December"}]
    )

    try:
        otr.main()
        assert False, "expected FileNotFoundError"
    except FileNotFoundError:
        pass


def test_main_writes_no_files_to_disk(tmp_path, monkeypatch) -> None:
    csv_file = tmp_path / "closed.csv"
    csv_file.write_text(
        "vulnerability.severity,saltminer.attributes.DaysPastDue\nCritical,1\n"
    )

    monkeypatch.setattr(
        otr, "INPUT_FILES", [{"filePath": str(csv_file), "label": "December"}]
    )
    monkeypatch.chdir(tmp_path)

    otr.main()

    assert list(tmp_path.iterdir()) == [csv_file]
