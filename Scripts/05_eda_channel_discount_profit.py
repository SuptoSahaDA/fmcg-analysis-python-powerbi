"""05 - EDA 5 to 7: channel, discount and profitability analysis."""

import pandas as pd
import numpy as np
from config import OUTPUT_DIR
from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path

def get_fact():
    path = Path(__file__).with_name("03_build_fact_sales.py")
    spec = spec_from_file_location("fact_module", path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.build_fact_tables(module.clean_tables(module.load_workbook()))[0]


def run_eda_5_to_7(fact):
    data = fact.loc[fact["Is_Recognized"]].copy()
    results = {}

    # EDA 5 - Sales channel performance
    if "Sales_Channel" in data.columns:
        channel = data.groupby("Sales_Channel", dropna=False, as_index=False).agg(
            Revenue=("Recognized_Revenue", "sum"),
            Profit=("Recognized_Profit", "sum"),
            Orders=("Order_ID", "nunique") if "Order_ID" in data else ("Recognized_Revenue", "size"),
            Units=("Recognized_Quantity", "sum"),
        )
        channel["Profit_Margin_%"] = np.where(
            channel["Revenue"].ne(0), channel["Profit"] / channel["Revenue"] * 100, np.nan
        )
        results["Channel_Analysis"] = channel.sort_values("Revenue", ascending=False)

    # EDA 6 - Discount analysis
    if "Discount_Pct" in data.columns:
        data["Discount_Band"] = pd.cut(
            data["Discount_Pct"],
            bins=[-0.001, 0, 0.05, 0.10, 0.20, 1],
            labels=["No Discount", "0-5%", "5-10%", "10-20%", "Above 20%"],
            include_lowest=True,
        )
        discount = data.groupby("Discount_Band", observed=False, dropna=False, as_index=False).agg(
            Revenue=("Recognized_Revenue", "sum"),
            Profit=("Recognized_Profit", "sum"),
            Units=("Recognized_Quantity", "sum"),
        )
        results["Discount_Analysis"] = discount

    # EDA 7 - Profitability analysis
    dimensions = [c for c in ["Category", "Brand", "Sales_Channel", "Region"] if c in data.columns]
    for dimension in dimensions:
        table = data.groupby(dimension, dropna=False, as_index=False).agg(
            Revenue=("Recognized_Revenue", "sum"),
            Cost=("Recognized_Cost", "sum"),
            Profit=("Recognized_Profit", "sum"),
        )
        table["Profit_Margin_%"] = np.where(
            table["Revenue"].ne(0), table["Profit"] / table["Revenue"] * 100, np.nan
        )
        results[f"Profitability_by_{dimension}"] = table.sort_values("Profit", ascending=False)

    total_revenue = data["Recognized_Revenue"].sum()
    total_profit = data["Recognized_Profit"].sum()
    results["KPI_Summary"] = pd.DataFrame({
        "KPI": ["Recognized Revenue", "Recognized Profit", "Profit Margin (%)",
                "Recognized Orders", "Recognized Units"],
        "Value": [
            total_revenue,
            total_profit,
            total_profit / total_revenue * 100 if total_revenue else np.nan,
            data["Order_ID"].nunique() if "Order_ID" in data else len(data),
            data["Recognized_Quantity"].sum(),
        ],
    })

    for name, table in results.items():
        table.to_csv(OUTPUT_DIR / f"{name}.csv", index=False)
    return results


if __name__ == "__main__":
    analysis = run_eda_5_to_7(get_fact())
    for name, table in analysis.items():
        print(f"\n{name}\n", table.head(10).to_string(index=False))
