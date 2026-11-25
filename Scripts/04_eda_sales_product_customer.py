"""04 - EDA 1 to 4: sales, product, regional and customer analysis."""

import pandas as pd
from config import OUTPUT_DIR
from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path

def get_fact():
    path = Path(__file__).with_name("03_build_fact_sales.py")
    spec = spec_from_file_location("fact_module", path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    cleaner, loader = module.clean_tables, module.load_workbook
    cleaned = cleaner(loader())
    return module.build_fact_tables(cleaned)[0]


def run_eda_1_to_4(fact):
    recognized = fact.loc[fact["Is_Recognized"]].copy()
    results = {}

    # EDA 1 - Sales performance
    if "Order_Date" in recognized.columns:
        recognized["Order_Month"] = recognized["Order_Date"].dt.to_period("M").astype(str)
        monthly = recognized.groupby("Order_Month", as_index=False).agg(
            Revenue=("Recognized_Revenue", "sum"),
            Profit=("Recognized_Profit", "sum"),
            Orders=("Order_ID", "nunique") if "Order_ID" in recognized else ("Recognized_Revenue", "size"),
            Units=("Recognized_Quantity", "sum"),
        )
        results["Monthly_Analysis"] = monthly

    # EDA 2 - Product and category performance
    group_cols = [c for c in ["Product_ID", "Product_Name"] if c in recognized.columns]
    if group_cols:
        results["Product_Analysis"] = recognized.groupby(group_cols, dropna=False, as_index=False).agg(
            Revenue=("Recognized_Revenue", "sum"),
            Profit=("Recognized_Profit", "sum"),
            Units=("Recognized_Quantity", "sum"),
        ).sort_values("Revenue", ascending=False)

    if "Category" in recognized.columns:
        results["Category_Analysis"] = recognized.groupby("Category", dropna=False, as_index=False).agg(
            Revenue=("Recognized_Revenue", "sum"),
            Profit=("Recognized_Profit", "sum"),
            Units=("Recognized_Quantity", "sum"),
        ).sort_values("Revenue", ascending=False)

    if "Brand" in recognized.columns:
        results["Brand_Analysis"] = recognized.groupby("Brand", dropna=False, as_index=False).agg(
            Revenue=("Recognized_Revenue", "sum"),
            Profit=("Recognized_Profit", "sum"),
            Units=("Recognized_Quantity", "sum"),
        ).sort_values("Revenue", ascending=False)

    # EDA 3 - Regional analysis
    if "Region" in recognized.columns:
        results["Regional_Analysis"] = recognized.groupby("Region", dropna=False, as_index=False).agg(
            Revenue=("Recognized_Revenue", "sum"),
            Profit=("Recognized_Profit", "sum"),
            Units=("Recognized_Quantity", "sum"),
        ).sort_values("Revenue", ascending=False)

    # EDA 4 - Customer analysis
    customer_cols = [c for c in ["Customer_ID", "Customer_Type", "Loyalty_Tier"] if c in recognized.columns]
    if "Customer_ID" in customer_cols:
        results["Customer_Analysis"] = recognized.groupby(customer_cols, dropna=False, as_index=False).agg(
            Revenue=("Recognized_Revenue", "sum"),
            Orders=("Order_ID", "nunique") if "Order_ID" in recognized else ("Recognized_Revenue", "size"),
            Units=("Recognized_Quantity", "sum"),
        ).sort_values("Revenue", ascending=False)

    for name, table in results.items():
        table.to_csv(OUTPUT_DIR / f"{name}.csv", index=False)
    return results


if __name__ == "__main__":
    analysis = run_eda_1_to_4(get_fact())
    for name, table in analysis.items():
        print(f"\n{name}\n", table.head(10).to_string(index=False))
