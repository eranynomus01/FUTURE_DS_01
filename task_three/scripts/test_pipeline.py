import pandas as pd
import numpy as np
import os
import sys

# Force working directory to be the parent of this script (task_three)
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("Running pipeline integrity tests...")

clean_csv_path = "data/cleaned_funnel_data.csv"
raw_csv_path = "data/raw_funnel_data.csv"

# Check file existence
if not os.path.exists(raw_csv_path):
    print(f"FAIL: Raw data file does not exist at {raw_csv_path}.")
    sys.exit(1)

if not os.path.exists(clean_csv_path):
    print(f"FAIL: Cleaned data file does not exist at {clean_csv_path}.")
    sys.exit(1)

df = pd.read_csv(clean_csv_path)

# Test 1: Shape and Deduplication
expected_records = 10000
actual_records = len(df)
if actual_records != expected_records:
    print(f"FAIL: Expected exactly {expected_records} records, but found {actual_records}.")
    sys.exit(1)

unique_ids = df["Session ID"].nunique()
if unique_ids != expected_records:
    print(f"FAIL: Expected {expected_records} unique Session IDs, but found {unique_ids}.")
    sys.exit(1)
print("PASS: Deduplication and dataset size verified.")

# Test 2: Categorical Casing and Harmonization
allowed_sources = {"Organic Search", "Paid Search", "Paid Social", "Email", "Referral", "Direct"}
allowed_devices = {"Desktop", "Mobile", "Tablet"}

if not set(df["Traffic Source"].unique()).issubset(allowed_sources):
    print(f"FAIL: Invalid sources found: {df['Traffic Source'].unique()}")
    sys.exit(1)

if not set(df["Device"].unique()).issubset(allowed_devices):
    print(f"FAIL: Invalid devices found: {df['Device'].unique()}")
    sys.exit(1)
print("PASS: Categorical fields and string casing harmonized.")

# Test 3: Funnel Sequential Chronology
try:
    df_temp = df.copy()
    df_temp["Session Start DT"] = pd.to_datetime(df_temp["Session Start"])
    df_temp["Lead Form DT"] = pd.to_datetime(df_temp["Lead Form Submitted"])
    df_temp["Trial Started DT"] = pd.to_datetime(df_temp["Trial Started"])
    df_temp["Subscription Purchased DT"] = pd.to_datetime(df_temp["Subscription Purchased"])
except Exception as e:
    print(f"FAIL: Date format parsing failed. Error: {e}")
    sys.exit(1)

# Check order constraints
# Session Start <= Lead
lead_anomaly = df_temp[df_temp["Lead Form DT"] < df_temp["Session Start DT"]]
if len(lead_anomaly) > 0:
    print(f"FAIL: Found {len(lead_anomaly)} rows where Lead is before Session Start.")
    sys.exit(1)

# Lead <= Trial
trial_anomaly = df_temp[df_temp["Trial Started DT"] < df_temp["Lead Form DT"]]
if len(trial_anomaly) > 0:
    print(f"FAIL: Found {len(trial_anomaly)} rows where Trial is before Lead.")
    sys.exit(1)

# Trial <= Purchase
purch_anomaly = df_temp[df_temp["Subscription Purchased DT"] < df_temp["Trial Started DT"]]
if len(purch_anomaly) > 0:
    print(f"FAIL: Found {len(purch_anomaly)} rows where Purchase is before Trial.")
    sys.exit(1)

print("PASS: Funnel sequential chronology verified.")

# Test 4: Conversion Pipeline Dependency Consistency
# Customer -> must have Trial & Lead
cust_missing_stages = df[
    df["Subscription Purchased"].notna() & 
    (df["Trial Started"].isna() | df["Lead Form Submitted"].isna())
]
if len(cust_missing_stages) > 0:
    print(f"FAIL: Found {len(cust_missing_stages)} converted customers who missed Trial or Lead stage.")
    sys.exit(1)

# Trial -> must have Lead
trial_missing_lead = df[
    df["Trial Started"].notna() & 
    df["Lead Form Submitted"].isna()
]
if len(trial_missing_lead) > 0:
    print(f"FAIL: Found {len(trial_missing_lead)} trials without Lead submit recorded.")
    sys.exit(1)

print("PASS: Funnel stage dependency consistency verified.")
print("\nALL MARKETING FUNNEL INTEGRITY TESTS PASSED SUCCESSFULLY!")
