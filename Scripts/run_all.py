"""Run the FMCG analysis workflow in the correct order."""

from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def load_script(filename, module_name):
    path = SCRIPT_DIR / filename
    spec = spec_from_file_location(module_name, path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    load_module = load_script("01_load_and_inspect.py", "load_module")
    clean_module = load_script("02_clean_and_validate.py", "clean_module")
    fact_module = load_script("03_build_fact_sales.py", "fact_module")
    eda14_module = load_script("04_eda_sales_product_customer.py", "eda14_module")
    eda57_module = load_script("05_eda_channel_discount_profit.py", "eda57_module")
    eda810_module = load_script("06_eda_returns_inventory_abc.py", "eda810_module")
    visual_module = load_script("07_visualize_business_performance.py", "visual_module")
    export_module = load_script("08_export_powerbi.py", "export_module")

    source = load_module.load_workbook()
    load_module.inspect_tables(source)

    cleaned = clean_module.clean_tables(source)
    for name in ["sales", "products", "customers", "inventory"]:
        cleaned[name].to_csv(clean_module.OUTPUT_DIR / f"clean_{name}.csv", index=False)

    fact, recognized = fact_module.build_fact_tables(cleaned)
    eda14_module.run_eda_1_to_4(fact)
    eda57_module.run_eda_5_to_7(fact)
    eda810_module.run_eda_8_to_10(cleaned)

    visual_module.create_charts()
    export_module.export_powerbi_workbook()
    print("\nFMCG analysis workflow completed.")


if __name__ == "__main__":
    main()
