"""02 - Clean, standardize and validate the four source tables."""

import pandas as pd
import numpy as np
from config import OUTPUT_DIR
from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path

# Load the shared workbook loader from script 01.
_path = Path(__file__).with_name("01_load_and_inspect.py")
_spec = spec_from_file_location("load_module", _path)
_load_module = module_from_spec(_spec)
_spec.loader.exec_module(_load_module)
load_workbook = _load_module.load_workbook


def clean_text(series):
    result = series.astype("string").str.strip()
    return result.replace("", pd.NA)


def to_number(series):
    cleaned = (
        series.astype("string")
        .str.replace(r"[$,]", "", regex=True)
        .str.replace(r"\s", "", regex=True)
    )
    return pd.to_numeric(cleaned, errors="coerce")


def standardize_discount(series):
    values = to_number(series)
    # Values greater than 1 are treated as percentages (e.g. 10 -> 0.10).
    values = values.where(values <= 1, values / 100)
    return values.where(values.between(0, 1))


def clean_tables(tables):
    sales = tables["sales"].copy()
    products = tables["products"].copy()
    customers = tables["customers"].copy()
    inventory = tables["inventory"].copy()

    original_sales_rows = len(sales)
    sales = sales.drop_duplicates().copy()

    # Standardize common text columns when they exist.
    text_columns = {
        "sales": ["City", "Region", "Sales_Channel", "Category", "Brand",
                  "Product_Name", "Payment_Method", "Order_Status", "Returned"],
        "products": ["Category", "Brand", "Product_Name"],
        "customers": ["City", "Customer_Type", "Loyalty_Tier"],
    }
    frames = {"sales": sales, "products": products, "customers": customers}
    for table_name, columns in text_columns.items():
        for col in columns:
            if col in frames[table_name].columns:
                frames[table_name][col] = clean_text(frames[table_name][col])

    sales, products, customers = frames["sales"], frames["products"], frames["customers"]

    # Normalize categorical spelling/case.
    for df in [sales, products]:
        for col in ["Category", "Brand", "Product_Name", "City", "Region"]:
            if col in df.columns:
                df[col] = df[col].astype("string").str.title()

    if "Sales_Channel" in sales.columns:
        sales["Sales_Channel"] = sales["Sales_Channel"].str.title().replace(
            {"Distributer": "Distributor"}
        )
    if "Payment_Method" in sales.columns:
        sales["Payment_Method"] = sales["Payment_Method"].str.title().replace(
            {"Credit Card": "Card"}
        )
    if "Order_Status" in sales.columns:
        sales["Order_Status"] = sales["Order_Status"].str.lower().str.title().replace(
            {"Canceled": "Cancelled"}
        )
    if "Customer_Type" in customers.columns:
        customers["Customer_Type"] = customers["Customer_Type"].str.title().replace(
            {"Super Market": "Supermarket"}
        )
    if "Loyalty_Tier" in customers.columns:
        customers["Loyalty_Tier"] = customers["Loyalty_Tier"].str.title()

    # Parse dates.
    for df, col in [
        (sales, "Order_Date"),
        (customers, "Join_Date"),
        (inventory, "Last_Stock_Update"),
    ]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce", format="mixed")
            df[f"{col}_Invalid_Flag"] = df[col].isna()

    # Convert numeric fields.
    numeric_columns = {
        "sales": ["Quantity", "Unit_Price", "Sales_Amount", "Cost_Amount",
                  "Profit", "Discount_Pct"],
        "products": ["Unit_Price", "Unit_Cost"],
        "inventory": ["Stock_On_Hand", "Reorder_Level", "Max_Stock"],
    }
    frames = {"sales": sales, "products": products, "inventory": inventory}
    for table_name, columns in numeric_columns.items():
        for col in columns:
            if col in frames[table_name].columns:
                if col == "Discount_Pct":
                    frames[table_name][col] = standardize_discount(frames[table_name][col])
                else:
                    frames[table_name][col] = to_number(frames[table_name][col])

    sales, products, inventory = frames["sales"], frames["products"], frames["inventory"]

    # Validation flags: retain questionable rows for review rather than silently deleting them.
    if "Quantity" in sales.columns:
        sales["Quantity_Invalid_Flag"] = sales["Quantity"].isna() | sales["Quantity"].le(0)
    if "Unit_Price" in sales.columns:
        sales["Unit_Price_Invalid_Flag"] = sales["Unit_Price"].isna() | sales["Unit_Price"].le(0)
    if "Discount_Pct" in sales.columns:
        sales["Discount_Invalid_Flag"] = (
            sales["Discount_Pct"].isna() | ~sales["Discount_Pct"].between(0, 1)
        )

    if "Product_ID" in products.columns:
        products["Duplicate_Product_ID_Flag"] = products["Product_ID"].duplicated(keep=False)
    if "Customer_ID" in customers.columns:
        customers["Duplicate_Customer_ID_Flag"] = customers["Customer_ID"].duplicated(keep=False)

    if {"Stock_On_Hand", "Reorder_Level"}.issubset(inventory.columns):
        inventory["Low_Stock_Flag"] = inventory["Stock_On_Hand"].le(inventory["Reorder_Level"])
    if {"Stock_On_Hand", "Max_Stock"}.issubset(inventory.columns):
        inventory["Over_Max_Stock_Flag"] = inventory["Stock_On_Hand"].gt(inventory["Max_Stock"])

    quality = pd.DataFrame([
        ["Exact duplicate sales rows removed", original_sales_rows - len(sales)],
        ["Sales rows retained after exact deduplication", len(sales)],
        ["Invalid quantity rows", int(sales["Quantity_Invalid_Flag"].sum()) if "Quantity_Invalid_Flag" in sales else 0],
        ["Invalid unit price rows", int(sales["Unit_Price_Invalid_Flag"].sum()) if "Unit_Price_Invalid_Flag" in sales else 0],
        ["Invalid discount rows", int(sales["Discount_Invalid_Flag"].sum()) if "Discount_Invalid_Flag" in sales else 0],
        ["Invalid order dates", int(sales["Order_Date_Invalid_Flag"].sum()) if "Order_Date_Invalid_Flag" in sales else 0],
        ["Duplicate product IDs", int(products["Duplicate_Product_ID_Flag"].sum()) if "Duplicate_Product_ID_Flag" in products else 0],
        ["Duplicate customer IDs", int(customers["Duplicate_Customer_ID_Flag"].sum()) if "Duplicate_Customer_ID_Flag" in customers else 0],
    ], columns=["Quality_Check", "Rows"])

    quality.to_csv(OUTPUT_DIR / "02_data_quality_summary.csv", index=False)

    return {
        "sales": sales,
        "products": products,
        "customers": customers,
        "inventory": inventory,
        "quality": quality,
    }


if __name__ == "__main__":
    cleaned = clean_tables(load_workbook())
    for name in ["sales", "products", "customers", "inventory"]:
        cleaned[name].to_csv(OUTPUT_DIR / f"clean_{name}.csv", index=False)
    print(cleaned["quality"].to_string(index=False))
    print("\nCleaned tables saved in outputs/.")
