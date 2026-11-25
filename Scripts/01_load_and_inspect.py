"""01 - Load the FMCG workbook and inspect source tables."""

import pandas as pd
from config import INPUT_FILE, SHEETS, OUTPUT_DIR


def load_workbook():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Workbook not found: {INPUT_FILE}\n"
            "Place the FMCG Excel workbook in the project root or update config.py."
        )

    tables = {}
    for table_name, sheet_name in SHEETS.items():
        tables[table_name] = pd.read_excel(INPUT_FILE, sheet_name=sheet_name)

    return tables


def inspect_tables(tables):
    rows = []
    for name, df in tables.items():
        rows.append({
            "Table": name,
            "Rows": len(df),
            "Columns": len(df.columns),
            "Duplicate_Rows": int(df.duplicated().sum()),
            "Missing_Cells": int(df.isna().sum().sum()),
        })
        print(f"\n{name.upper()} - Shape: {df.shape}")
        print(df.head())
        print("\nColumn data types:")
        print(df.dtypes)

    summary = pd.DataFrame(rows)
    summary.to_csv(OUTPUT_DIR / "01_source_table_profile.csv", index=False)
    return summary


if __name__ == "__main__":
    source_tables = load_workbook()
    profile = inspect_tables(source_tables)
    print("\nSource table profile:")
    print(profile.to_string(index=False))
