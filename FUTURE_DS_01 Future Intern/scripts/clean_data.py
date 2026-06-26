import pandas as pd
import numpy as np
import os

print("Starting data cleaning pipeline...")

raw_path = "d:/futureintern tasks/data/raw_sales_data.csv"
clean_csv_path = "d:/futureintern tasks/data/cleaned_sales_data.csv"
clean_xlsx_path = "d:/futureintern tasks/data/cleaned_sales_data.xlsx"

# Load the raw dataset
if not os.path.exists(raw_path):
    raise FileNotFoundError(f"Raw data file not found at {raw_path}. Please run generate_data.py first.")

df = pd.read_csv(raw_path)
initial_rows = len(df)
print(f"Loaded {initial_rows} records from raw data.")

# 1. Deduplicate records
df = df.drop_duplicates()
dedup_rows = len(df)
print(f"Removed {initial_rows - dedup_rows} duplicate rows. Remaining: {dedup_rows}")

# 2. Fix Date Format Inconsistencies
def parse_date(date_str):
    if pd.isna(date_str):
        return pd.NaT
    date_str = str(date_str).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
        try:
            return pd.to_datetime(date_str, format=fmt)
        except ValueError:
            continue
    # Fallback to pandas automatic parser if formats above fail
    try:
        return pd.to_datetime(date_str)
    except:
        return pd.NaT

df["Order Date"] = df["Order Date"].apply(parse_date)
df["Ship Date"] = df["Ship Date"].apply(parse_date)

# Drop rows with invalid order dates (if any)
invalid_dates = df["Order Date"].isna().sum()
if invalid_dates > 0:
    print(f"Warning: Dropping {invalid_dates} rows with unparseable Order Dates.")
    df = df.dropna(subset=["Order Date"])

# 3. Clean Ship Mode
# Fill missing Ship Mode with the most common ship mode
most_common_ship = df["Ship Mode"].mode()[0] if not df["Ship Mode"].mode().empty else "Standard Class"
df["Ship Mode"] = df["Ship Mode"].fillna(most_common_ship)
df["Ship Mode"] = df["Ship Mode"].replace("", most_common_ship)

# 4. Clean Customer Information (Resolve missing customer name/segment using customer ID mapping)
# Create mapping dictionaries from rows where data is complete
id_name_map = df[df["Customer Name"].notna() & (df["Customer Name"] != "")].set_index("Customer ID")["Customer Name"].to_dict()
id_segment_map = df[df["Segment"].notna() & (df["Segment"] != "")].set_index("Customer ID")["Segment"].to_dict()

# Apply mapping to fill missing fields
df["Customer Name"] = df.apply(
    lambda row: id_name_map.get(row["Customer ID"], "Unknown Customer") if pd.isna(row["Customer Name"]) or row["Customer Name"] == "" else row["Customer Name"],
    axis=1
)
df["Segment"] = df.apply(
    lambda row: id_segment_map.get(row["Customer ID"], "Consumer") if pd.isna(row["Segment"]) or row["Segment"] == "" else row["Segment"],
    axis=1
)

# 5. Correct logical errors in Quantity and Unit Price
# Convert quantity and unit price to numeric, coercing errors
df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce").fillna(1).astype(int)
df["Unit Price"] = pd.to_numeric(df["Unit Price"], errors="coerce").fillna(0.0)

# If quantity is negative or zero, convert to absolute value (assume sign input error)
df["Quantity"] = df["Quantity"].apply(lambda q: abs(q) if q != 0 else 1)

# 6. Clean Discount values
df["Discount"] = pd.to_numeric(df["Discount"], errors="coerce").fillna(0.0)
# If discount is greater than 1.0 (e.g. 1.5 for 1.5% or 150%), check if it should be divided by 100
df["Discount"] = df["Discount"].apply(lambda d: d / 100.0 if d > 1.0 else d)
df["Discount"] = df["Discount"].clip(0.0, 0.85)  # Cap discount at 85%

# 7. Recalculate Sales and Profit for mathematical consistency
# Sales = Unit Price * Quantity * (1 - Discount)
df["Sales"] = (df["Unit Price"] * df["Quantity"] * (1 - df["Discount"])).round(2)

# Define margin mapping to calculate Profit consistently
margin_mapping = {
    # Technology
    "Phones": 0.25, "Accessories": 0.45, "Copiers": 0.30, "Machines": 0.20,
    # Furniture
    "Chairs": 0.12, "Bookcases": 0.10, "Tables": 0.08, "Furnishings": 0.35,
    # Office Supplies
    "Paper": 0.30, "Art": 0.45, "Binders": 0.60, "Storage": 0.20, "Appliances": 0.18
}

def calculate_profit(row):
    subcat = row["Sub-Category"]
    sales = row["Sales"]
    discount = row["Discount"]
    base_margin = margin_mapping.get(subcat, 0.20)
    # Discounts reduce profit margin directly
    effective_margin = base_margin - (discount * 0.25)
    return round(sales * effective_margin, 2)

df["Profit"] = df.apply(calculate_profit, axis=1)

# Add Profit Margin column: Profit / Sales
df["Profit Margin"] = df.apply(lambda row: round(row["Profit"] / row["Sales"], 4) if row["Sales"] > 0 else 0.0, axis=1)

# 8. Sort records chronologically
df = df.sort_values(by="Order Date").reset_index(drop=True)

# 9. Format dates as strings for CSV/Excel export
df["Order Date"] = df["Order Date"].dt.strftime("%Y-%m-%d")
df["Ship Date"] = df["Ship Date"].dt.strftime("%Y-%m-%d")

# Save cleaned files
df.to_csv(clean_csv_path, index=False)
df.to_excel(clean_xlsx_path, index=False)

print(f"Data cleaning complete! Cleaned dataset contains {len(df)} rows.")
print(f"Cleaned CSV saved to: {clean_csv_path}")
print(f"Cleaned Excel saved to: {clean_xlsx_path}")
