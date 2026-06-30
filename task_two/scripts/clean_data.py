import pandas as pd
import numpy as np
import os

# Force working directory to be the parent of this script (task_two)
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("Starting customer data cleaning pipeline...")

raw_path = "data/raw_customer_data.csv"
clean_csv_path = "data/cleaned_customer_data.csv"
clean_xlsx_path = "data/cleaned_customer_data.xlsx"

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
    if pd.isna(date_str) or str(date_str).strip() == "":
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

df["Signup Date"] = df["Signup Date"].apply(parse_date)
df["Churn Date"] = df["Churn Date"].apply(parse_date)

# Drop rows with invalid signup dates
invalid_signup_dates = df["Signup Date"].isna().sum()
if invalid_signup_dates > 0:
    print(f"Warning: Dropping {invalid_signup_dates} rows with unparseable Signup Dates.")
    df = df.dropna(subset=["Signup Date"])

# 3. Clean and Harmonize String Fields (Casing & Whitespace)
# Clean Plan
df["Plan"] = df["Plan"].astype(str).str.strip().str.title()
# Standardize Plan mapping
df["Plan"] = df["Plan"].replace({"Basic": "Basic", "Pro": "Pro", "Enterprise": "Enterprise"})
# Clean Billing Interval
def clean_interval(val):
    if pd.isna(val):
        return "Monthly"
    val = str(val).strip().lower()
    if "annual" in val:
        return "Annually"
    return "Monthly"

df["Billing Interval"] = df["Billing Interval"].apply(clean_interval)

# Clean Status
df["Status"] = df["Status"].astype(str).str.strip().str.title()
df["Status"] = df["Status"].replace({"Active": "Active", "Churned": "Churned"})

# 4. Clean Customer Information (Resolve missing customer name/region using Customer ID mapping)
# Create mapping dictionaries from rows where data is complete
id_name_map = df[df["Customer Name"].notna() & (df["Customer Name"] != "")].set_index("Customer ID")["Customer Name"].to_dict()
id_region_map = df[df["Region"].notna() & (df["Region"] != "")].set_index("Customer ID")["Region"].to_dict()

# Apply mapping to fill missing fields
df["Customer Name"] = df.apply(
    lambda row: id_name_map.get(row["Customer ID"], "Unknown Customer") if pd.isna(row["Customer Name"]) or str(row["Customer Name"]).strip() == "" else row["Customer Name"],
    axis=1
)
df["Region"] = df.apply(
    lambda row: id_region_map.get(row["Customer ID"], "East") if pd.isna(row["Region"]) or str(row["Region"]).strip() == "" else row["Region"],
    axis=1
)

# 5. Resolve Contradictory Status / Dates
# If Active, clear Churn Date and Churn Reason
active_mask = df["Status"] == "Active"
df.loc[active_mask, "Churn Date"] = pd.NaT
df.loc[active_mask, "Churn Reason"] = np.nan

# If Churned, ensure Churn Date exists (if missing, default to Signup Date + 180 days)
churned_mask = df["Status"] == "Churned"
missing_churn_date = df["Churn Date"].isna() & churned_mask
df.loc[missing_churn_date, "Churn Date"] = df.loc[missing_churn_date, "Signup Date"] + pd.Timedelta(days=180)

# If Churn Date is before Signup Date (logical anomaly), reset it to Signup Date + 30 days
invalid_churn_order = churned_mask & (df["Churn Date"] < df["Signup Date"])
df.loc[invalid_churn_order, "Churn Date"] = df.loc[invalid_churn_order, "Signup Date"] + pd.Timedelta(days=30)

# Fill missing churn reasons
df.loc[churned_mask & (df["Churn Reason"].isna() | (df["Churn Reason"] == "")), "Churn Reason"] = "Unknown / Other"

# 6. Correct pricing and charges for mathematical consistency
# Standard Plan pricing
plan_base_prices = {
    "Basic": 29.00,
    "Pro": 79.00,
    "Enterprise": 249.00
}

def recalculate_monthly_charge(row):
    plan = row["Plan"]
    interval = row["Billing Interval"]
    base_price = plan_base_prices.get(plan, 79.00)
    if interval == "Annually":
        # 20% discount
        return round(base_price * 0.8, 2)
    return round(base_price, 2)

df["Monthly Charges"] = df.apply(recalculate_monthly_charge, axis=1)

# Calculate Months Active
end_period_date = pd.to_datetime("2025-12-31")
df["EndDateDT"] = df.apply(
    lambda row: row["Churn Date"] if row["Status"] == "Churned" else end_period_date,
    axis=1
)
# Calculate tenure in months: days difference divided by average month length
df["Months Active"] = ((df["EndDateDT"] - df["Signup Date"]).dt.days / 30.4).round(1)
# Ensure at least 1 month active
df["Months Active"] = df["Months Active"].clip(lower=1.0)

# Recalculate Total Charges = Monthly Charges * Months Active
df["Total Charges"] = (df["Monthly Charges"] * df["Months Active"]).round(2)

# Drop helper column
df = df.drop(columns=["EndDateDT"])

# 7. Clean Support Tickets, Usage Frequency, and NPS
df["Support Tickets"] = pd.to_numeric(df["Support Tickets"], errors="coerce").fillna(0).astype(int).abs()
df["Usage Frequency"] = pd.to_numeric(df["Usage Frequency"], errors="coerce").fillna(10).astype(int).abs()
df["NPS Score"] = pd.to_numeric(df["NPS Score"], errors="coerce") # Keep float/nulls for NPS

# 8. Sort chronologically
df = df.sort_values(by="Signup Date").reset_index(drop=True)

# 9. Format dates as strings for export
df["Signup Date"] = df["Signup Date"].dt.strftime("%Y-%m-%d")
df["Churn Date"] = df["Churn Date"].dt.strftime("%Y-%m-%d")

# Save cleaned files
df.to_csv(clean_csv_path, index=False)
df.to_excel(clean_xlsx_path, index=False)

print(f"Data cleaning complete! Cleaned dataset contains {len(df)} rows.")
print(f"Cleaned CSV saved to: {clean_csv_path}")
print(f"Cleaned Excel saved to: {clean_xlsx_path}")
