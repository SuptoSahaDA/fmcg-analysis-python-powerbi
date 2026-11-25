"""08 - Export Power BI-ready tables into a single Excel workbook."""

import pandas as pd
from config import OUTPUT_DIR, POWERBI_FILE
from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path

EXPORT_FILES = {
    "Fact_Sales": "Fact_Sales.csv",
    "Recognized_Sales": "Recognized_Sales.csv",
    "Data_Quality": "02_data_quality_summary.csv",
    "Category_Analysis": "Category_Analysis.csv",
    "Brand_Analysis": "Brand_Analysis.csv",
    "Product_Analysis": "Product_Analysis.csv",
    "Order_Status": "Order_Status.csv",
    "Product_ABC": "Product_ABC.csv",
    "Customer_Analysis": "Customer_Analysis.csv",
    "Anomaly_Analysis": "Anomaly_Analysis.csv",
    "Outlier_Analysis": "Outlier_Analysis.csv",
    "Monthly_Analysis": "Monthly_Analysis.csv",
    "KPI_Summary": "KPI_Summary.csv",
    "Discount_Analysis": "Discount_Analysis.csv",
    "Regional_Analysis": "Regional_Analysis.csv",
    "Channel_Analysis": "Channel_Analysis.csv",
    "Inventory_Analysis": "Inventory_Analysis.csv",
}


def export_powerbi_workbook():
    with pd.ExcelWriter(POWERBI_FILE, engine="openpyxl") as writer:
        exported = 0
        for sheet_name, filename in EXPORT_FILES.items():
            path = OUTPUT_DIR / filename
            if path.exists():
                pd.read_csv(path).to_excel(writer, sheet_name=sheet_name[:31], index=False)
                exported += 1

        # Add a helpful note when a section has not produced a CSV.
        if exported == 0:
            pd.DataFrame({"Message": ["Run the analysis scripts before exporting."]}).to_excel(
                writer, sheet_name="Read_Me", index=False
            )

    print(f"Power BI workbook created: {POWERBI_FILE}")


if __name__ == "__main__":
    export_powerbi_workbook()
