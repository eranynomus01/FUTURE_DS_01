import pandas as pd
import numpy as np
import os

# Force working directory to be the parent of this script (task_three)
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("Starting marketing funnel data cleaning pipeline...")

raw_path = "data/raw_funnel_data.csv"
clean_csv_path = "data/cleaned_funnel_data.csv"
clean_xlsx_path = "data/cleaned_funnel_data.xlsx"

# Load raw dataset
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
def parse_datetime(dt_str):
    if pd.isna(dt_str) or str(dt_str).strip() == "":
        return pd.NaT
    dt_str = str(dt_str).strip()
    # Try different formats
    for fmt in ("%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M:%S", "%m/%d/%Y %H:%M:%S"):
        try:
            return pd.to_datetime(dt_str, format=fmt)
        except ValueError:
            continue
    # Fallback to automatic pandas parser
    try:
        return pd.to_datetime(dt_str)
    except:
        return pd.NaT

df["Session Start"] = df["Session Start"].apply(parse_datetime)
df["Lead Form Submitted"] = df["Lead Form Submitted"].apply(parse_datetime)
df["Trial Started"] = df["Trial Started"].apply(parse_datetime)
df["Subscription Purchased"] = df["Subscription Purchased"].apply(parse_datetime)

# Drop rows with invalid session start times
invalid_sessions = df["Session Start"].isna().sum()
if invalid_sessions > 0:
    print(f"Warning: Dropping {invalid_sessions} rows with unparseable Session Start times.")
    df = df.dropna(subset=["Session Start"])

# 3. Clean and Harmonize String Fields (Casing & Categories)
# Clean Traffic Source
def clean_source(val):
    if pd.isna(val):
        return "Direct"
    val = str(val).strip().replace("_", " ").lower()
    
    # Map sources to standard titles
    if "organic" in val: return "Organic Search"
    if "paid search" in val: return "Paid Search"
    if "paid social" in val: return "Paid Social"
    if "email" in val: return "Email"
    if "referral" in val: return "Referral"
    return "Direct"

df["Traffic Source"] = df["Traffic Source"].apply(clean_source)

# Clean Device
df["Device"] = df["Device"].astype(str).str.strip().str.title()
df["Device"] = df["Device"].replace({"Desktop": "Desktop", "Mobile": "Mobile", "Tablet": "Tablet"})

# Clean Campaign
def clean_campaign(row):
    src = row["Traffic Source"]
    camp = row["Campaign"]
    if pd.isna(camp) or str(camp).strip() == "" or str(camp).strip().lower() in ["none", "null", "nan"]:
        if src in ["Paid Search", "Paid Social", "Email"]:
            return "Uncategorized Paid Campaign"
        return "None"
    return str(camp).strip().title()

df["Campaign"] = df.apply(clean_campaign, axis=1)

# 4. Resolve Funnel Logic & Chronological Contradictions
# For each session, timestamps must satisfy: Session Start <= Lead <= Trial <= Purchase.
# If intermediate steps are missing but subsequent steps exist, we fill them.

def resolve_funnel_dates(row):
    sess = row["Session Start"]
    lead = row["Lead Form Submitted"]
    trial = row["Trial Started"]
    purch = row["Subscription Purchased"]
    
    # Case A: User purchased, but has missing intermediate stages
    if pd.notna(purch):
        # Ensure purchase is after session start. If not, reset purchase to session start + 10 days
        if purch < sess:
            purch = sess + pd.Timedelta(days=10)
            
        if pd.isna(trial):
            # Set trial to purchase - 7 days (standard trial length)
            trial = purch - pd.Timedelta(days=7)
            if trial < sess:
                trial = sess + pd.Timedelta(days=1)
                
        if pd.isna(lead):
            # Set lead to trial - 2 days
            lead = trial - pd.Timedelta(days=2)
            if lead < sess:
                lead = sess + pd.Timedelta(minutes=15)
                
    # Case B: User has a trial, but has missing lead
    if pd.notna(trial):
        if trial < sess:
            # Force trial to be after session start
            trial = sess + pd.Timedelta(days=1)
            
        if pd.isna(lead):
            lead = sess + pd.Timedelta(minutes=15)
            
    # Case C: User submitted lead form
    if pd.notna(lead):
        if lead < sess:
            # Swap or force lead to be after session start
            lead = sess + pd.Timedelta(minutes=10)
            
    # Now enforce order constraints
    if pd.notna(lead) and pd.notna(trial) and trial < lead:
        # Swap dates if they go backward
        lead, trial = trial, lead
        
    if pd.notna(trial) and pd.notna(purch) and purch < trial:
        purch = trial + pd.Timedelta(days=7)
        
    # Ensure active lead is before trial, and session is before lead
    if pd.notna(lead) and lead < sess:
        lead = sess + pd.Timedelta(minutes=5)
    if pd.notna(trial) and trial < lead:
        trial = lead + pd.Timedelta(hours=12)

    return pd.Series([lead, trial, purch])

df[["Lead Form Submitted", "Trial Started", "Subscription Purchased"]] = df.apply(resolve_funnel_dates, axis=1)

# 5. Sort chronologically by Session Start
df = df.sort_values(by="Session Start").reset_index(drop=True)

# 6. Format dates back to string format
df["Session Start"] = df["Session Start"].dt.strftime("%Y-%m-%d %H:%M:%S")
df["Lead Form Submitted"] = df["Lead Form Submitted"].dt.strftime("%Y-%m-%d %H:%M:%S")
df["Trial Started"] = df["Trial Started"].dt.strftime("%Y-%m-%d %H:%M:%S")
df["Subscription Purchased"] = df["Subscription Purchased"].dt.strftime("%Y-%m-%d %H:%M:%S")

# Save cleaned files
df.to_csv(clean_csv_path, index=False)
df.to_excel(clean_xlsx_path, index=False)

print(f"Data cleaning complete! Cleaned dataset contains {len(df)} rows.")
print(f"Cleaned CSV saved to: {clean_csv_path}")
print(f"Cleaned Excel saved to: {clean_xlsx_path}")
