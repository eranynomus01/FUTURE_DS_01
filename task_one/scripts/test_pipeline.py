import os
import pandas as pd
import json

def test_pipeline():
    print("==========================================")
    print("RUNNING PIPELINE VERIFICATION TESTS")
    print("==========================================")
    
    raw_path = "data/raw_sales_data.csv"
    clean_csv_path = "data/cleaned_sales_data.csv"
    clean_xlsx_path = "data/cleaned_sales_data.xlsx"
    analysis_dir = "data/analysis"
    js_data_path = "web/data.js"
    
    # 1. Assert Raw Data Exists and has Expected Issues
    assert os.path.exists(raw_path), "Raw data CSV does not exist!"
    df_raw = pd.read_csv(raw_path)
    raw_rows = len(df_raw)
    print(f"[OK] Raw data loaded: {raw_rows} records.")
    
    # Assert raw has duplicates
    raw_duplicates = df_raw.duplicated().sum()
    print(f"[OK] Raw duplicates count: {raw_duplicates} (expected ~100)")
    assert raw_duplicates > 0, "Raw dataset should contain duplicates for testing deduplication!"
    
    # Assert raw has missing customer names/segments
    raw_missing_segment = df_raw["Segment"].isna().sum() + (df_raw["Segment"] == "").sum()
    raw_missing_cust = df_raw["Customer Name"].isna().sum() + (df_raw["Customer Name"] == "").sum()
    print(f"[OK] Raw missing segments: {raw_missing_segment}, missing customer names: {raw_missing_cust}")
    assert raw_missing_segment > 0, "Raw dataset should contain missing segments!"
    assert raw_missing_cust > 0, "Raw dataset should contain missing customer names!"
    
    # Assert raw has negative quantities
    raw_negative_qty = (df_raw["Quantity"] < 0).sum()
    print(f"[OK] Raw negative quantities: {raw_negative_qty}")
    assert raw_negative_qty > 0, "Raw dataset should contain negative quantities!"

    # 2. Assert Clean Data is Deduplicated and Cleaned
    assert os.path.exists(clean_csv_path), "Cleaned CSV does not exist!"
    assert os.path.exists(clean_xlsx_path), "Cleaned Excel does not exist!"
    df_clean = pd.read_csv(clean_csv_path)
    clean_rows = len(df_clean)
    print(f"[OK] Cleaned data loaded: {clean_rows} records.")
    
    # Deduplication test
    assert df_clean.duplicated().sum() == 0, "Cleaned dataset contains duplicates!"
    print("[OK] Deduplication: PASSED")
    
    # Missing customer segment/name correction test
    clean_missing_segment = df_clean["Segment"].isna().sum() + (df_clean["Segment"] == "").sum()
    clean_missing_cust = df_clean["Customer Name"].isna().sum() + (df_clean["Customer Name"] == "").sum()
    assert clean_missing_segment == 0, f"Cleaned dataset still has {clean_missing_segment} missing segments!"
    assert clean_missing_cust == 0, f"Cleaned dataset still has {clean_missing_cust} missing customer names!"
    print("[OK] Customer Name & Segment Completion: PASSED")
    
    # Quantity normalization test
    clean_negative_qty = (df_clean["Quantity"] <= 0).sum()
    assert clean_negative_qty == 0, "Cleaned dataset contains zero or negative quantities!"
    print("[OK] Quantity Correction: PASSED")
    
    # Discount cap test
    clean_invalid_discounts = (df_clean["Discount"] > 0.85).sum()
    assert clean_invalid_discounts == 0, "Cleaned dataset contains discounts above 85% cap!"
    print("[OK] Discount Validation: PASSED")
    
    # Margin test (check that profit matches computed margins)
    margin_diffs = (abs(df_clean["Profit"] / df_clean["Sales"] - df_clean["Profit Margin"]) > 0.005).sum()
    assert margin_diffs == 0, f"Cleaned dataset contains inconsistent profit margin columns in {margin_diffs} rows!"
    print("[OK] Profit/Sales Calculation Consistency: PASSED")

    # 3. Assert Analysis JSON outputs exist and are valid
    kpis_path = os.path.join(analysis_dir, "kpis.json")
    trends_path = os.path.join(analysis_dir, "revenue_trends.json")
    top_products_path = os.path.join(analysis_dir, "top_products.json")
    
    for path in [kpis_path, trends_path, top_products_path]:
        assert os.path.exists(path), f"Analysis output {path} is missing!"
        with open(path, "r") as f:
            data = json.load(f)
            assert data, f"JSON file {path} is empty or invalid!"
    print("[OK] Aggregate Data Outputs: PASSED")

    # 4. Assert JS Data is successfully created and has transactions
    assert os.path.exists(js_data_path), "Web data.js is missing!"
    with open(js_data_path, "r") as f:
        content = f.read().strip()
        assert content.startswith("const SALES_DATA = {"), "data.js does not start with expected prefix!"
        assert content.endswith("};"), "data.js does not end with expected suffix!"
    print("[OK] Web data.js Structure: PASSED")

    print("\n==========================================")
    print("ALL PIPELINE VERIFICATION TESTS PASSED!")
    print("==========================================")

if __name__ == "__main__":
    test_pipeline()
