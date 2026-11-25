"""03 - Build the analysis-ready fact table and recognized transaction view."""

import pandas as pd
import numpy as np
from config import OUTPUT_DIR
from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path

def _load_cleaner():
    path = Path(__file__).with_name("02_clean_and_validate.py")
    spec = spec_from_file_location("clean_module", path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.clean_tables, module.load_workbook

clean_tables, load_workbook = _load_cleaner()


def build_fact_tables(cleaned):
    sales = cleaned["sales"].copy()
    products = cleaned["products"].copy()
    customers = cleaned["customers"].copy()

    # Join master attributes only when the key exists in both tables.
    if "Product_ID" in sales.columns and "Product_ID" in products.columns:
        product_cols = [c for c in ["Product_ID", "Unit_Cost", "Category", "Brand", "Product_Name"]
                        if c in products.columns]
        product_lookup = products[product_cols].drop_duplicates("Product_ID")
        sales = sales.merge(product_lookup, on="Product_ID", how="left", suffixes=("", "_Master"))

    if "Customer_ID" in sales.columns and "Customer_ID" in customers.columns:
        customer_cols = [c for c in ["Customer_ID", "Customer_Type", "Loyalty_Tier", "Join_Date"]
                         if c in customers.columns]
        customer_lookup = customers[customer_cols].drop_duplicates("Customer_ID")
        sales = sales.merge(customer_lookup, on="Customer_ID", how="left", suffixes=("", "_Customer"))

    # Prefer transaction-level values; use master values only when transaction values are absent.
    for col in ["Category", "Brand", "Product_Name"]:
        master_col = f"{col}_Master"
        if master_col in sales.columns:
            if col in sales.columns:
                sales[col] = sales[col].fillna(sales[master_col])
            else:
                sales[col] = sales[master_col]

    # Calculate final revenue/cost where sufficient inputs are available.
    if {"Quantity", "Unit_Price"}.issubset(sales.columns):
        sales["Calculated_Revenue"] = sales["Quantity"] * sales["Unit_Price"]
    else:
        sales["Calculated_Revenue"] = np.nan

    if {"Quantity", "Unit_Cost"}.issubset(sales.columns):
        sales["Calculated_Cost"] = sales["Quantity"] * sales["Unit_Cost"]
    else:
        sales["Calculated_Cost"] = np.nan

    if "Sales_Amount" in sales.columns:
        sales["Sales_Amount_Final"] = sales["Calculated_Revenue"].where(
            sales["Calculated_Revenue"].notna(), sales["Sales_Amount"]
        )
    else:
        sales["Sales_Amount_Final"] = sales["Calculated_Revenue"]

    if "Cost_Amount" in sales.columns:
        sales["Cost_Amount_Final"] = sales["Calculated_Cost"].where(
            sales["Calculated_Cost"].notna(), sales["Cost_Amount"]
        )
    else:
        sales["Cost_Amount_Final"] = sales["Calculated_Cost"]

    sales["Profit_Calculated"] = sales["Sales_Amount_Final"] - sales["Cost_Amount_Final"]
    if "Profit" in sales.columns:
        sales["Profit_Final"] = sales["Profit_Calculated"].where(
            sales["Profit_Calculated"].notna(), sales["Profit"]
        )
    else:
        sales["Profit_Final"] = sales["Profit_Calculated"]

    # Recognition rule used in the analysis: delivered and not returned.
    status = sales.get("Order_Status", pd.Series("Delivered", index=sales.index))
    status = status.astype("string").str.lower().str.strip()
    returned = sales.get("Returned", pd.Series("No", index=sales.index))
    returned = returned.astype("string").str.lower().str.strip()

    sales["Is_Recognized"] = status.eq("delivered") & ~returned.isin(["yes", "true", "1", "returned"])
    sales["Recognized_Revenue"] = sales["Sales_Amount_Final"].where(sales["Is_Recognized"], 0)
    sales["Recognized_Cost"] = sales["Cost_Amount_Final"].where(sales["Is_Recognized"], 0)
    sales["Recognized_Profit"] = sales["Profit_Final"].where(sales["Is_Recognized"], 0)
    sales["Recognized_Quantity"] = sales.get("Quantity", 0).where(sales["Is_Recognized"], 0)

    recognized = sales.loc[sales["Is_Recognized"]].copy()

    # Mark records where cost is missing and reported profit is used as a fallback.
    sales["Profit_Fallback_Flag"] = (
        sales["Is_Recognized"] & sales["Cost_Amount_Final"].isna() &
        sales.get("Profit", pd.Series(np.nan, index=sales.index)).notna()
    )

    sales.to_csv(OUTPUT_DIR / "Fact_Sales.csv", index=False)
    recognized.to_csv(OUTPUT_DIR / "Recognized_Sales.csv", index=False)
    return sales, recognized


if __name__ == "__main__":
    cleaned = clean_tables(load_workbook())
    fact, recognized = build_fact_tables(cleaned)
    print("Fact sales rows:", len(fact))
    print("Recognized sales rows:", len(recognized))
