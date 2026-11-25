"""06 - EDA 8 to 10: returns, inventory and ABC/Pareto analysis."""

import pandas as pd
import numpy as np
from config import OUTPUT_DIR
from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path

def get_inputs():
    path = Path(__file__).with_name("02_clean_and_validate.py")
    spec = spec_from_file_location("clean_module", path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.clean_tables(module.load_workbook())


def run_eda_8_to_10(cleaned):
    sales = cleaned["sales"].copy()
    inventory = cleaned["inventory"].copy()
    products = cleaned["products"].copy()
    results = {}

    # EDA 8 - Returns and order status
    if "Order_Status" in sales.columns:
        results["Order_Status"] = sales.groupby("Order_Status", dropna=False, as_index=False).agg(
            Transaction_Rows=("Order_Status", "size"),
            Revenue=("Sales_Amount", "sum") if "Sales_Amount" in sales else ("Quantity", "sum"),
        )
    if "Returned" in sales.columns:
        results["Returns_Analysis"] = sales.groupby("Returned", dropna=False, as_index=False).agg(
            Transaction_Rows=("Returned", "size"),
            Revenue=("Sales_Amount", "sum") if "Sales_Amount" in sales else ("Quantity", "sum"),
        )

    # EDA 9 - Inventory health
    if {"Stock_On_Hand", "Reorder_Level"}.issubset(inventory.columns):
        inventory["Low_Stock_Flag"] = inventory["Stock_On_Hand"].le(inventory["Reorder_Level"])
    if {"Stock_On_Hand", "Max_Stock"}.issubset(inventory.columns):
        inventory["Over_Max_Stock_Flag"] = inventory["Stock_On_Hand"].gt(inventory["Max_Stock"])
    if {"Stock_On_Hand", "Reorder_Level", "Max_Stock"}.issubset(inventory.columns):
        inventory["Invalid_Inventory_Flag"] = (
            inventory["Stock_On_Hand"].lt(0) |
            inventory["Reorder_Level"].lt(0) |
            inventory["Max_Stock"].lt(inventory["Reorder_Level"])
        )
    if "Product_ID" in inventory.columns and "Product_ID" in products.columns:
        inventory = inventory.merge(
            products[[c for c in ["Product_ID", "Product_Name", "Category", "Brand"] if c in products.columns]]
            .drop_duplicates("Product_ID"),
            on="Product_ID", how="left"
        )
    results["Inventory_Analysis"] = inventory

    # EDA 10 - Product ABC / Pareto analysis based on recognized revenue.
    if "Order_Status" in sales.columns:
        status = sales["Order_Status"].astype("string").str.lower()
        recognized = sales.loc[status.eq("delivered")].copy()
    else:
        recognized = sales.copy()

    if "Returned" in recognized.columns:
        returned = recognized["Returned"].astype("string").str.lower()
        recognized = recognized.loc[~returned.isin(["yes", "true", "1", "returned"])]

    product_key = "Product_ID" if "Product_ID" in recognized.columns else "Product_Name"
    if product_key in recognized.columns:
        revenue_col = "Sales_Amount" if "Sales_Amount" in recognized.columns else "Unit_Price"
        abc = recognized.groupby(product_key, dropna=False, as_index=False)[revenue_col].sum()
        abc = abc.rename(columns={revenue_col: "Revenue"}).sort_values("Revenue", ascending=False)
        total = abc["Revenue"].sum()
        abc["Revenue_Share_%"] = np.where(total != 0, abc["Revenue"] / total * 100, np.nan)
        abc["Cumulative_Share_%"] = abc["Revenue_Share_%"].cumsum()
        abc["ABC_Class"] = np.select(
            [abc["Cumulative_Share_%"].le(80),
             abc["Cumulative_Share_%"].le(95)],
            ["A", "B"], default="C"
        )
        results["Product_ABC"] = abc

    for name, table in results.items():
        table.to_csv(OUTPUT_DIR / f"{name}.csv", index=False)
    return results


if __name__ == "__main__":
    analysis = run_eda_8_to_10(get_inputs())
    for name, table in analysis.items():
        print(f"\n{name}\n", table.head(10).to_string(index=False))
