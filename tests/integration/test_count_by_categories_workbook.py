"""Integration test: main() consolidates multiple inputs into one workbook."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

import count_by_categories as cbc


def test_main_writes_one_sheet_per_input_file(tmp_path, monkeypatch) -> None:
    csv_file = tmp_path / "team_a.csv"
    csv_file.write_text("Owner\nAlice\nAlice\nBob\n")

    xlsx_file = tmp_path / "team_b.xlsx"
    with pd.ExcelWriter(xlsx_file, engine="openpyxl") as writer:
        pd.DataFrame({"Owner": ["Carol", "Dave", "Dave"]}).to_excel(
            writer, sheet_name="Raw", index=False
        )

    # Two entries deliberately share a sheet name to exercise disambiguation.
    duplicate_name_file = tmp_path / "team_c.xlsx"
    with pd.ExcelWriter(duplicate_name_file, engine="openpyxl") as writer:
        pd.DataFrame({"Owner": ["Erin"]}).to_excel(
            writer, sheet_name="Raw", index=False
        )

    output_file = tmp_path / "output" / "category_counts.xlsx"

    monkeypatch.setattr(
        cbc,
        "INPUT_FILES",
        [
            {"filePath": str(csv_file), "sheetName": "Team A"},
            {"filePath": str(xlsx_file), "sheetName": "Raw"},
            {"filePath": str(duplicate_name_file), "sheetName": "Raw"},
        ],
    )
    monkeypatch.setattr(cbc, "GROUP_COLUMNS", ["Owner"])
    monkeypatch.setattr(cbc, "OUTPUT_FILE", output_file)

    cbc.main()

    assert output_file.is_file()

    workbook = pd.read_excel(output_file, sheet_name=None)
    assert list(workbook.keys()) == ["Team A", "Raw", "Raw (2)"]

    team_a = workbook["Team A"]
    assert list(team_a[cbc.CATEGORY_COLUMN]) == ["Alice", "Bob", "Grand Total"]
    assert list(team_a[cbc.COUNT_COLUMN]) == [2, 1, 3]

    raw = workbook["Raw"]
    assert list(raw[cbc.CATEGORY_COLUMN]) == ["Carol", "Dave", "Grand Total"]
    assert list(raw[cbc.COUNT_COLUMN]) == [1, 2, 3]

    raw2 = workbook["Raw (2)"]
    assert list(raw2[cbc.CATEGORY_COLUMN]) == ["Erin", "Grand Total"]
    assert list(raw2[cbc.COUNT_COLUMN]) == [1, 1]


def test_main_writes_output_atomically_leaving_no_temp_file(
    tmp_path, monkeypatch
) -> None:
    csv_file = tmp_path / "team_a.csv"
    csv_file.write_text("Owner\nAlice\n")

    output_file = tmp_path / "output" / "category_counts.xlsx"

    monkeypatch.setattr(
        cbc, "INPUT_FILES", [{"filePath": str(csv_file), "sheetName": "Team A"}]
    )
    monkeypatch.setattr(cbc, "GROUP_COLUMNS", ["Owner"])
    monkeypatch.setattr(cbc, "OUTPUT_FILE", output_file)

    cbc.main()

    remaining_files = set(Path(output_file.parent).iterdir())
    assert remaining_files == {output_file}


def test_main_raises_and_leaves_no_output_when_an_input_file_is_missing(
    tmp_path, monkeypatch
) -> None:
    missing_file = tmp_path / "does_not_exist.csv"
    output_file = tmp_path / "output" / "category_counts.xlsx"

    monkeypatch.setattr(
        cbc,
        "INPUT_FILES",
        [{"filePath": str(missing_file), "sheetName": "Team A"}],
    )
    monkeypatch.setattr(cbc, "GROUP_COLUMNS", ["Owner"])
    monkeypatch.setattr(cbc, "OUTPUT_FILE", output_file)

    try:
        cbc.main()
        assert False, "expected FileNotFoundError"
    except FileNotFoundError:
        pass

    assert not output_file.exists()
    assert not any(output_file.parent.glob("*.tmp"))
