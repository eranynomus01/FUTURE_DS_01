import pandas as pd
import numpy as np
import json
import os

# Force working directory to be the parent of this script (task_three)
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("Starting marketing funnel data analysis and aggregation...")

clean_csv_path = "data/cleaned_funnel_data.csv"
analysis_dir = "data/analysis"
os.makedirs(analysis_dir, exist_ok=True)

if not os.path.exists(clean_csv_path):
    raise FileNotFoundError(f"Cleaned CSV not found at {clean_csv_path}. Please run clean_data.py first.")

df = pd.read_csv(clean_csv_path)

# Cost metrics settings for channels to calculate Spend, CPL, CAC
channel_click_costs = {
    "Paid Search": 2.50,
    "Paid Social": 1.80,
    "Email": 0.05,
    "Organic Search": 0.00,
    "Referral": 0.00,
    "Direct": 0.00
}

# --- 1. Core KPIs ---
visitors = int(len(df))
leads = int(df["Lead Form Submitted"].notna().sum())
trials = int(df["Trial Started"].notna().sum())
customers = int(df["Subscription Purchased"].notna().sum())

# Spend estimations
df["Click Cost"] = df["Traffic Source"].map(channel_click_costs)
total_spend = float(df["Click Cost"].sum())
cpl_overall = float(total_spend / leads) if leads > 0 else 0.0
cac_overall = float(total_spend / customers) if customers > 0 else 0.0

kpi_data = {
    "visitors": int(visitors),
    "leads": int(leads),
    "trials": int(trials),
    "customers": int(customers),
    "total_spend": round(total_spend, 2),
    "cpl": round(cpl_overall, 2),
    "cac": round(cac_overall, 2),
    "conv_visitor_to_lead": round(leads / visitors, 4) if visitors > 0 else 0.0,
    "conv_lead_to_trial": round(trials / leads, 4) if leads > 0 else 0.0,
    "conv_trial_to_customer": round(customers / trials, 4) if trials > 0 else 0.0,
    "conv_overall": round(customers / visitors, 4) if visitors > 0 else 0.0
}

with open(os.path.join(analysis_dir, "kpis.json"), "w") as f:
    json.dump(kpi_data, f, indent=4)

# --- 2. Channel Performance ---
def get_funnel_stats(groupby_col):
    agg = df.groupby(groupby_col).agg(
        visitors=("Session ID", "count"),
        leads=("Lead Form Submitted", lambda x: x.notna().sum()),
        trials=("Trial Started", lambda x: x.notna().sum()),
        customers=("Subscription Purchased", lambda x: x.notna().sum()),
        spend=("Click Cost", "sum")
    ).reset_index()
    
    res = []
    for _, row in agg.iterrows():
        vis = int(row["visitors"])
        lds = int(row["leads"])
        tls = int(row["trials"])
        cust = int(row["customers"])
        spd = float(row["spend"])
        
        res.append({
            "segment": str(row[groupby_col]),
            "visitors": vis,
            "leads": lds,
            "trials": tls,
            "customers": cust,
            "spend": round(spd, 2),
            "cpl": round(spd / lds, 2) if lds > 0 else 0.0,
            "cac": round(spd / cust, 2) if cust > 0 else 0.0,
            "conv_visitor_to_lead": round(lds / vis, 4) if vis > 0 else 0.0,
            "conv_lead_to_trial": round(tls / lds, 4) if lds > 0 else 0.0,
            "conv_trial_to_customer": round(cust / tls, 4) if tls > 0 else 0.0,
            "conv_overall": round(cust / vis, 4) if vis > 0 else 0.0
        })
    return res

channel_performance = get_funnel_stats("Traffic Source")
with open(os.path.join(analysis_dir, "channel_performance.json"), "w") as f:
    json.dump(channel_performance, f, indent=4)

# --- 3. Campaign Performance ---
campaign_performance = get_funnel_stats("Campaign")
# Filter out "None" if desired, or keep it to show benchmark metrics
with open(os.path.join(analysis_dir, "campaign_performance.json"), "w") as f:
    json.dump(campaign_performance, f, indent=4)

# --- 4. Device Performance ---
device_performance = get_funnel_stats("Device")
with open(os.path.join(analysis_dir, "device_performance.json"), "w") as f:
    json.dump(device_performance, f, indent=4)

# --- 5. Monthly Funnel Trends ---
df["YearMonth"] = df["Session Start"].str.slice(0, 7)
monthly_trends = get_funnel_stats("YearMonth")
monthly_trends = sorted(monthly_trends, key=lambda x: x["segment"])

with open(os.path.join(analysis_dir, "monthly_trends.json"), "w") as f:
    json.dump(monthly_trends, f, indent=4)

# --- 6. Drop-offs analysis ---
dropoffs = {
    "visitor_to_lead": {
        "dropoff_volume": visitors - leads,
        "dropoff_rate": round((visitors - leads) / visitors, 4) if visitors > 0 else 0.0
    },
    "lead_to_trial": {
        "dropoff_volume": leads - trials,
        "dropoff_rate": round((leads - trials) / leads, 4) if leads > 0 else 0.0
    },
    "trial_to_customer": {
        "dropoff_volume": trials - customers,
        "dropoff_rate": round((trials - customers) / trials, 4) if trials > 0 else 0.0
    }
}
with open(os.path.join(analysis_dir, "dropoffs.json"), "w") as f:
    json.dump(dropoffs, f, indent=4)

# --- 7. Full Session Preview for Explorer ---
# Select latest 300 rows for preview
df_sorted = df.sort_values(by="Session Start", ascending=False)
explorer_preview = []
for _, row in df_sorted.head(300).iterrows():
    explorer_preview.append({
        "session_id": row["Session ID"],
        "user_id": row["User ID"],
        "source": row["Traffic Source"],
        "campaign": row["Campaign"],
        "device": row["Device"],
        "session_start": row["Session Start"],
        "lead_time": "" if pd.isna(row["Lead Form Submitted"]) else row["Lead Form Submitted"],
        "trial_time": "" if pd.isna(row["Trial Started"]) else row["Trial Started"],
        "purchase_time": "" if pd.isna(row["Subscription Purchased"]) else row["Subscription Purchased"]
    })

with open(os.path.join(analysis_dir, "funnel_preview.json"), "w") as f:
    json.dump(explorer_preview, f, indent=4)

# Full clean sessions list for interactive filters
full_sessions_list = []
for _, row in df.iterrows():
    full_sessions_list.append({
        "session_id": row["Session ID"],
        "user_id": row["User ID"],
        "source": row["Traffic Source"],
        "campaign": row["Campaign"],
        "device": row["Device"],
        "session_start": row["Session Start"],
        "lead_time": "" if pd.isna(row["Lead Form Submitted"]) else row["Lead Form Submitted"],
        "trial_time": "" if pd.isna(row["Trial Started"]) else row["Trial Started"],
        "purchase_time": "" if pd.isna(row["Subscription Purchased"]) else row["Subscription Purchased"],
        "click_cost": float(row["Click Cost"])
    })

# --- 8. Export JS File for Web Dashboard ---
web_dir = "web"
os.makedirs(web_dir, exist_ok=True)
js_data = {
    "kpis": kpi_data,
    "channels": channel_performance,
    "campaigns": campaign_performance,
    "devices": device_performance,
    "trends": monthly_trends,
    "dropoffs": dropoffs,
    "sessions": full_sessions_list  # Full clean data for JS filter engine
}

with open(os.path.join(web_dir, "data.js"), "w") as f:
    f.write(f"const FUNNEL_DATA = {json.dumps(js_data, indent=4)};")

print(f"Data analysis and summary generation complete. Files exported to {analysis_dir} and {web_dir}/data.js")
