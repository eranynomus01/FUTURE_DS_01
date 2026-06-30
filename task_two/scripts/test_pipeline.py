import pandas as pd
import numpy as np
import os
import sys

print("Running pipeline integrity tests...")

clean_csv_path = "data/cleaned_customer_data.csv"
raw_csv_path = "data/raw_customer_data.csv"

# Check file existence
if not os.path.exists(raw_csv_path):
    print(f"FAIL: Raw data file does not exist at {raw_csv_path}.")
    sys.exit(1)

if not os.path.exists(clean_csv_path):
    print(f"FAIL: Cleaned data file does not exist at {clean_csv_path}.")
    sys.exit(1)

df = pd.read_csv(clean_csv_path)

# Test 1: Shape and Deduplication
expected_records = 5000
actual_records = len(df)
if actual_records != expected_records:
    print(f"FAIL: Expected exactly {expected_records} records, but found {actual_records}.")
    sys.exit(1)

unique_ids = df["Customer ID"].nunique()
if unique_ids != expected_records:
    print(f"FAIL: Expected {expected_records} unique Customer IDs, but found {unique_ids}.")
    sys.exit(1)
print("PASS: Deduplication and dataset size verified.")

# Test 2: Date Formats and Chronology
try:
    signup_dates = pd.to_datetime(df["Signup Date"], format="%Y-%m-%d")
    churn_dates = pd.to_datetime(df["Churn Date"].dropna(), format="%Y-%m-%d")
except Exception as e:
    print(f"FAIL: Date format is incorrect. Error: {e}")
    sys.exit(1)

# Check that Churn Date >= Signup Date
df_dates = df.dropna(subset=["Churn Date"]).copy()
df_dates["Signup Date DT"] = pd.to_datetime(df_dates["Signup Date"])
df_dates["Churn Date DT"] = pd.to_datetime(df_dates["Churn Date"])
date_anomaly = df_dates[df_dates["Churn Date DT"] < df_dates["Signup Date DT"]]
if len(date_anomaly) > 0:
    print(f"FAIL: Found {len(date_anomaly)} records where Churn Date is earlier than Signup Date.")
    sys.exit(1)
print("PASS: Date formats and chronology verified.")

# Test 3: Casing and Categoriess
allowed_plans = {"Basic", "Pro", "Enterprise"}
allowed_intervals = {"Monthly", "Annually"}
allowed_statuses = {"Active", "Churned"}

if not set(df["Plan"].unique()).issubset(allowed_plans):
    print(f"FAIL: Invalid plans found: {df['Plan'].unique()}")
    sys.exit(1)

if not set(df["Billing Interval"].unique()).issubset(allowed_intervals):
    print(f"FAIL: Invalid billing intervals found: {df['Billing Interval'].unique()}")
    sys.exit(1)

if not set(df["Status"].unique()).issubset(allowed_statuses):
    print(f"FAIL: Invalid statuses found: {df['Status'].unique()}")
    sys.exit(1)
print("PASS: Categorical fields and string casing harmonized.")

# Test 4: Pricing and Mathematical Consistency
plan_base_prices = {
    "Basic": 29.00,
    "Pro": 79.00,
    "Enterprise": 249.00
}

for idx, row in df.iterrows():
    plan = row["Plan"]
    interval = row["Billing Interval"]
    monthly = row["Monthly Charges"]
    total = row["Total Charges"]
    months = row["Months Active"]
    
    # Check monthly charges
    expected_monthly = plan_base_prices[plan]
    if interval == "Annually":
        expected_monthly *= 0.8
    expected_monthly = round(expected_monthly, 2)
    
    if abs(monthly - expected_monthly) > 0.01:
        print(f"FAIL: Monthly charges inconsistency at row {idx} (ID: {row['Customer ID']}). Expected {expected_monthly}, found {monthly}")
        sys.exit(1)
        
    # Check total charges
    expected_total = round(monthly * months, 2)
    if abs(total - expected_total) > 0.05: # allow small roundoff
        print(f"FAIL: Total charges inconsistency at row {idx} (ID: {row['Customer ID']}). Expected {expected_total}, found {total}")
        sys.exit(1)

print("PASS: Pricing logic and mathematical calculations verified.")

# Test 5: Logical Contradiction Resolution
# Active users must have no Churn Date and no Churn Reason
active_df = df[df["Status"] == "Active"]
if active_df["Churn Date"].notna().sum() > 0 or active_df["Churn Reason"].notna().sum() > 0:
    print("FAIL: Found active users with Churn Date or Churn Reason.")
    sys.exit(1)

# Churned users must have Churn Date and Churn Reason
churned_df = df[df["Status"] == "Churned"]
if churned_df["Churn Date"].isna().sum() > 0 or churned_df["Churn Reason"].isna().sum() > 0:
    print("FAIL: Found churned users with missing Churn Date or Churn Reason.")
    sys.exit(1)
print("PASS: Status and churn details logical consistency verified.")

# Test 6: Metrics Boundaries
if (df["Support Tickets"] < 0).sum() > 0:
    print("FAIL: Found negative support tickets.")
    sys.exit(1)

if (df["Usage Frequency"] < 0).sum() > 0:
    print("FAIL: Found negative usage frequency.")
    sys.exit(1)

nps_valid = df["NPS Score"].dropna()
if ((nps_valid < 1) | (nps_valid > 10)).sum() > 0:
    print("FAIL: Found NPS scores outside [1, 10] range.")
    sys.exit(1)

print("PASS: Metrics ranges and boundaries verified.")
print("\nALL INTEGRITY TESTS PASSED SUCCESSFULLY!")
