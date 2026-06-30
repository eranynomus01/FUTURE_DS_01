import pandas as pd
import numpy as np
import json
import os

# Force working directory to be the parent of this script (task_two)
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("Starting customer churn and retention analysis...")

clean_csv_path = "data/cleaned_customer_data.csv"
analysis_dir = "data/analysis"
os.makedirs(analysis_dir, exist_ok=True)

if not os.path.exists(clean_csv_path):
    raise FileNotFoundError(f"Cleaned CSV not found at {clean_csv_path}. Please run clean_data.py first.")

df = pd.read_csv(clean_csv_path)

# Convert dates to datetime objects for calculations
df["Signup Date DT"] = pd.to_datetime(df["Signup Date"])
df["Churn Date DT"] = pd.to_datetime(df["Churn Date"])

# --- 1. Core KPIs ---
total_customers = int(df["Customer ID"].nunique())
churned_customers = int(df[df["Status"] == "Churned"]["Customer ID"].nunique())
active_customers = int(df[df["Status"] == "Active"]["Customer ID"].nunique())
overall_churn_rate = float(churned_customers / total_customers) if total_customers > 0 else 0.0

# Tenure calculations (in months)
avg_tenure_overall = float(df["Months Active"].mean())
avg_tenure_churned = float(df[df["Status"] == "Churned"]["Months Active"].mean())
avg_tenure_active = float(df[df["Status"] == "Active"]["Months Active"].mean())

# Financials
mrr = float(df[df["Status"] == "Active"]["Monthly Charges"].sum())
total_revenue = float(df["Total Charges"].sum())
empirical_ltv = float(df["Total Charges"].mean())  # Historical average revenue per customer
projected_ltv = float(df["Monthly Charges"].mean() / overall_churn_rate) if overall_churn_rate > 0 else 0.0

kpi_data = {
    "total_customers": total_customers,
    "active_customers": active_customers,
    "churned_customers": churned_customers,
    "overall_churn_rate": round(overall_churn_rate, 4),
    "avg_tenure_overall": round(avg_tenure_overall, 2),
    "avg_tenure_churned": round(avg_tenure_churned, 2),
    "avg_tenure_active": round(avg_tenure_active, 2),
    "mrr": round(mrr, 2),
    "total_revenue": round(total_revenue, 2),
    "empirical_ltv": round(empirical_ltv, 2),
    "projected_ltv": round(projected_ltv, 2)
}

with open(os.path.join(analysis_dir, "kpis.json"), "w") as f:
    json.dump(kpi_data, f, indent=4)

# --- 2. Monthly Trends (Active Customers, Churn, Churn Rate over Time) ---
# Generate months from 2023-01 to 2025-12
months = pd.date_range(start="2023-01-01", end="2025-12-31", freq="MS").strftime("%Y-%m").tolist()
monthly_trends = []

for m in months:
    m_start = pd.to_datetime(f"{m}-01")
    # Next month start
    m_year, m_month = map(int, m.split("-"))
    if m_month == 12:
        m_end = pd.to_datetime(f"{m_year+1}-01-01")
    else:
        m_end = pd.to_datetime(f"{m_year}-{m_month+1:02d}-01")
        
    # Active in this month: signed up before/during this month, AND (active or churned after this month start)
    active_in_month = df[
        (df["Signup Date DT"] < m_end) & 
        ((df["Status"] == "Active") | (df["Churn Date DT"] >= m_start))
    ]
    active_count = int(active_in_month["Customer ID"].nunique())
    
    # Signed up in this month
    signups = int(df[df["Signup Date"].str.startswith(m)]["Customer ID"].nunique())
    
    # Churned in this month
    churns = int(df[(df["Status"] == "Churned") & (df["Churn Date"].str.startswith(m))]["Customer ID"].nunique())
    
    # Monthly churn rate = churns in month / active at start of month (or active in month)
    m_churn_rate = float(churns / active_count) if active_count > 0 else 0.0
    
    # Monthly MRR = sum of monthly charges for active users in this month
    m_mrr = float(active_in_month["Monthly Charges"].sum())
    
    monthly_trends.append({
        "month": m,
        "active_customers": active_count,
        "signups": signups,
        "churns": churns,
        "churn_rate": round(m_churn_rate, 4),
        "mrr": round(m_mrr, 2)
    })

with open(os.path.join(analysis_dir, "monthly_trends.json"), "w") as f:
    json.dump(monthly_trends, f, indent=4)

# --- 3. Cohort Retention Analysis ---
# Cohort is defined by Signup Month
df["Signup Month"] = df["Signup Date DT"].dt.strftime("%Y-%m")

cohort_groups = df.groupby("Signup Month")
cohort_analysis = []

for cohort_month, group in cohort_groups:
    cohort_size = int(group["Customer ID"].nunique())
    retention_counts = []
    
    # Let's track retention for months 0 to 12
    for age in range(13):
        # Customers who are active for at least 'age' months
        retained = int(group[group["Months Active"] >= age]["Customer ID"].nunique())
        retained_pct = float(retained / cohort_size) if cohort_size > 0 else 0.0
        retention_counts.append({
            "age": age,
            "retained_count": retained,
            "retention_rate": round(retained_pct, 4)
        })
        
    cohort_analysis.append({
        "cohort_month": cohort_month,
        "cohort_size": cohort_size,
        "retention": retention_counts
    })

# Sort cohort analysis by cohort month chronologically
cohort_analysis = sorted(cohort_analysis, key=lambda x: x["cohort_month"])

with open(os.path.join(analysis_dir, "cohort_retention.json"), "w") as f:
    json.dump(cohort_analysis, f, indent=4)

# --- 4. Segment Churn Analysis ---
def get_churn_by_col(col_name):
    agg = df.groupby(col_name).agg(
        total=("Customer ID", "count"),
        churned=("Status", lambda x: (x == "Churned").sum())
    ).reset_index()
    agg["churn_rate"] = (agg["churned"] / agg["total"]).round(4)
    
    res = []
    for _, row in agg.iterrows():
        res.append({
            "segment": str(row[col_name]),
            "total_customers": int(row["total"]),
            "churned_customers": int(row["churned"]),
            "churn_rate": float(row["churn_rate"])
        })
    return res

plan_churn = get_churn_by_col("Plan")
interval_churn = get_churn_by_col("Billing Interval")
region_churn = get_churn_by_col("Region")

# NPS Segment Churn
def get_nps_category(score):
    if pd.isna(score):
        return "No Response"
    if score <= 6:
        return "Detractors (1-6)"
    if score <= 8:
        return "Passives (7-8)"
    return "Promoters (9-10)"

df["NPS Category"] = df["NPS Score"].apply(get_nps_category)
nps_churn = get_churn_by_col("NPS Category")

segment_churn_data = {
    "plan": plan_churn,
    "billing_interval": interval_churn,
    "region": region_churn,
    "nps": nps_churn
}

with open(os.path.join(analysis_dir, "segment_churn.json"), "w") as f:
    json.dump(segment_churn_data, f, indent=4)

# --- 5. Churn Reasons & Retention Drivers ---
churn_reasons_counts = df[df["Status"] == "Churned"]["Churn Reason"].value_counts().reset_index()
churn_reasons_counts.columns = ["reason", "count"]
churn_reasons_counts["percentage"] = (churn_reasons_counts["count"] / churned_customers).round(4)

churn_reasons_data = []
for _, row in churn_reasons_counts.iterrows():
    churn_reasons_data.append({
        "reason": row["reason"],
        "count": int(row["count"]),
        "percentage": float(row["percentage"])
    })

# Support Tickets vs Churn
support_tickets_churn = df.groupby("Status")["Support Tickets"].mean().to_dict()
usage_frequency_churn = df.groupby("Status")["Usage Frequency"].mean().to_dict()

# Churn Rate by Ticket Bands
def ticket_band(t):
    if t <= 2: return "0-2 tickets"
    if t <= 5: return "3-5 tickets"
    if t <= 9: return "6-9 tickets"
    return "10+ tickets"
df["Ticket Band"] = df["Support Tickets"].apply(ticket_band)
ticket_band_churn = get_churn_by_col("Ticket Band")

# Churn Rate by Usage Bands
def usage_band(u):
    if u <= 5: return "Low Usage (<5 logins/mo)"
    if u <= 15: return "Medium Usage (6-15 logins/mo)"
    if u <= 25: return "High Usage (16-25 logins/mo)"
    return "Very High Usage (26+ logins/mo)"
df["Usage Band"] = df["Usage Frequency"].apply(usage_band)
usage_band_churn = get_churn_by_col("Usage Band")

drivers_data = {
    "churn_reasons": churn_reasons_data,
    "average_support_tickets": {k.lower(): round(float(v), 2) for k, v in support_tickets_churn.items()},
    "average_usage_frequency": {k.lower(): round(float(v), 2) for k, v in usage_frequency_churn.items()},
    "churn_by_support_tickets": ticket_band_churn,
    "churn_by_usage_frequency": usage_band_churn
}

with open(os.path.join(analysis_dir, "retention_drivers.json"), "w") as f:
    json.dump(drivers_data, f, indent=4)

# --- 6. Recent Customer Preview (Latest 200) ---
latest_customers = df.sort_values(by="Signup Date DT", ascending=False).head(200)
cust_cols = [
    "Customer ID", "Customer Name", "Region", "Signup Date", 
    "Plan", "Billing Interval", "Status", "Churn Date", 
    "Churn Reason", "Monthly Charges", "Total Charges", 
    "Support Tickets", "Usage Frequency", "NPS Score"
]

cust_preview_data = []
for _, row in latest_customers[cust_cols].iterrows():
    cust_preview_data.append({
        "customer_id": row["Customer ID"],
        "customer_name": row["Customer Name"],
        "region": row["Region"],
        "signup_date": row["Signup Date"],
        "plan": row["Plan"],
        "billing_interval": row["Billing Interval"],
        "status": row["Status"],
        "churn_date": "" if pd.isna(row["Churn Date"]) else str(row["Churn Date"]),
        "churn_reason": "" if pd.isna(row["Churn Reason"]) else str(row["Churn Reason"]),
        "monthly_charges": float(row["Monthly Charges"]),
        "total_charges": float(row["Total Charges"]),
        "support_tickets": int(row["Support Tickets"]),
        "usage_frequency": int(row["Usage Frequency"]),
        "nps_score": None if pd.isna(row["NPS Score"]) else int(row["NPS Score"])
    })

with open(os.path.join(analysis_dir, "customers_preview.json"), "w") as f:
    json.dump(cust_preview_data, f, indent=4)

# Complete customers data for interactive JavaScript analysis
full_customers_data = []
for _, row in df[cust_cols].iterrows():
    full_customers_data.append({
        "customer_id": row["Customer ID"],
        "customer_name": row["Customer Name"],
        "region": row["Region"],
        "signup_date": row["Signup Date"],
        "plan": row["Plan"],
        "billing_interval": row["Billing Interval"],
        "status": row["Status"],
        "churn_date": "" if pd.isna(row["Churn Date"]) else str(row["Churn Date"]),
        "churn_reason": "" if pd.isna(row["Churn Reason"]) else str(row["Churn Reason"]),
        "monthly_charges": float(row["Monthly Charges"]),
        "total_charges": float(row["Total Charges"]),
        "support_tickets": int(row["Support Tickets"]),
        "usage_frequency": int(row["Usage Frequency"]),
        "nps_score": None if pd.isna(row["NPS Score"]) else int(row["NPS Score"])
    })

# --- 7. Export JS File for Web Dashboard ---
web_dir = "web"
os.makedirs(web_dir, exist_ok=True)
js_data = {
    "kpis": kpi_data,
    "trends": monthly_trends,
    "cohorts": cohort_analysis,
    "segments": segment_churn_data,
    "drivers": drivers_data,
    "customers": full_customers_data  # Full clean data for JS filter/search engine
}

with open(os.path.join(web_dir, "data.js"), "w") as f:
    f.write(f"const CUSTOMER_DATA = {json.dumps(js_data, indent=4)};")

print(f"Data analysis and summary generation complete. Files exported to {analysis_dir} and {web_dir}/data.js")
