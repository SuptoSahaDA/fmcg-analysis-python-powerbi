"""07 - Create portfolio-ready charts from the generated analysis tables."""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from config import OUTPUT_DIR, FIGURE_DIR
from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path

sns.set_theme(style="whitegrid", palette="deep")
plt.rcParams["figure.figsize"] = (11, 6)
plt.rcParams["axes.titleweight"] = "bold"


def save_bar_chart(data, category, value, title, filename, horizontal=False):
    if data.empty or category not in data.columns or value not in data.columns:
        return
    chart_data = data.dropna(subset=[category, value]).copy()
    if chart_data.empty:
        return
    chart_data = chart_data.sort_values(value, ascending=horizontal)
    fig, ax = plt.subplots()
    if horizontal:
        bars = ax.barh(chart_data[category].astype(str), chart_data[value])
        ax.bar_label(bars, fmt="%.0f", padding=3)
    else:
        bars = ax.bar(chart_data[category].astype(str), chart_data[value])
        ax.bar_label(bars, fmt="%.0f", padding=3)
        ax.tick_params(axis="x", rotation=35)
    ax.set_title(title)
    ax.set_ylabel(value.replace("_", " "))
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / filename, dpi=300, bbox_inches="tight")
    plt.close(fig)


def create_charts():
    product_path = OUTPUT_DIR / "Product_Analysis.csv"
    category_path = OUTPUT_DIR / "Category_Analysis.csv"
    region_path = OUTPUT_DIR / "Regional_Analysis.csv"
    channel_path = OUTPUT_DIR / "Channel_Analysis.csv"
    monthly_path = OUTPUT_DIR / "Monthly_Analysis.csv"

    if product_path.exists():
        d = pd.read_csv(product_path).head(10)
        label = "Product_Name" if "Product_Name" in d else d.columns[0]
        save_bar_chart(d, label, "Revenue", "Top 10 Products by Revenue",
                       "top_10_products_revenue.png", horizontal=True)
    if category_path.exists():
        d = pd.read_csv(category_path)
        save_bar_chart(d, "Category", "Revenue", "Revenue by Category",
                       "revenue_by_category.png")
    if region_path.exists():
        d = pd.read_csv(region_path)
        save_bar_chart(d, "Region", "Revenue", "Revenue by Region",
                       "revenue_by_region.png")
    if channel_path.exists():
        d = pd.read_csv(channel_path)
        save_bar_chart(d, "Sales_Channel", "Profit_Margin_%", "Profit Margin by Sales Channel",
                       "profit_margin_by_channel.png")
    if monthly_path.exists():
        d = pd.read_csv(monthly_path)
        if {"Order_Month", "Revenue"}.issubset(d.columns):
            fig, ax = plt.subplots()
            ax.plot(d["Order_Month"], d["Revenue"], marker="o")
            ax.set_title("Monthly Recognized Revenue Trend")
            ax.set_xlabel("Month")
            ax.set_ylabel("Revenue")
            ax.tick_params(axis="x", rotation=45)
            fig.tight_layout()
            fig.savefig(FIGURE_DIR / "monthly_revenue_trend.png", dpi=300, bbox_inches="tight")
            plt.close(fig)

    print(f"Charts saved to: {FIGURE_DIR}")


if __name__ == "__main__":
    create_charts()
