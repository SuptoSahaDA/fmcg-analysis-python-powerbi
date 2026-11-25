from pathlib import Path

# Keep the Excel workbook in the project root folder.
PROJECT_DIR = Path(__file__).resolve().parents[1]
INPUT_FILE = PROJECT_DIR / "FMCG_Real_World_Data_Analyst_Practice(1).xlsx"
OUTPUT_DIR = PROJECT_DIR / "outputs"
FIGURE_DIR = OUTPUT_DIR / "figures"
POWERBI_FILE = OUTPUT_DIR / "FMCG_PowerBI_Dashboard_Data.xlsx"

SHEETS = {
    "sales": "Raw_Sales",
    "products": "Product_Master",
    "customers": "Customer_Master",
    "inventory": "Inventory_Data",
}

for folder in [OUTPUT_DIR, FIGURE_DIR]:
    folder.mkdir(parents=True, exist_ok=True)
