import csv
import random
import os
from datetime import datetime, timedelta

# Force working directory to be the parent of this script (task_three)
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Ensure target directory exists
os.makedirs("data", exist_ok=True)

# Master lists for generation
sources = ["Organic Search", "Paid Search", "Paid Social", "Email", "Referral", "Direct"]
campaigns = ["Winter Sale", "Spring Promo", "Retargeting Ads", "Brand Awareness", "Product Launch", "Newsletter Vol 12"]
devices = ["Desktop", "Mobile", "Tablet"]

# User profiles mapping
user_ids = [f"USR-{200000 + i}" for i in range(8000)]

# Date range: 2026-01-01 to 2026-06-30
start_date = datetime(2026, 1, 1)
end_date = datetime(2026, 6, 30)
date_delta_seconds = int((end_date - start_date).total_seconds())

print("Generating raw marketing funnel and lead data...")

raw_data_path = "data/raw_funnel_data.csv"
with open(raw_data_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    # Header
    writer.writerow([
        "Session ID", "User ID", "Traffic Source", "Campaign", "Device",
        "Session Start", "Lead Form Submitted", "Trial Started", "Subscription Purchased"
    ])
    
    records_list = []
    
    # Generate 10,000 sessions
    for i in range(1, 10001):
        sess_id = f"SESS-{100000 + i}"
        user_id = random.choice(user_ids)
        
        # Determine source, campaign, device
        source = random.choice(sources)
        device = random.choice(devices)
        
        campaign = "None"
        if source in ["Paid Search", "Paid Social"]:
            campaign = random.choice(campaigns[:5])  # Winter Sale, Spring Promo, Retargeting Ads, Brand Awareness, Product Launch
        elif source == "Email":
            campaign = "Newsletter Vol 12"
            
        # Session start timestamp
        rand_sec = random.randint(0, date_delta_seconds)
        session_dt = start_date + timedelta(seconds=rand_sec)
        
        # Funnel stage decisions based on source and device (correlation modeling)
        # Mobile users are less likely to submit lead forms
        # Paid Search and Email have higher conversion rates
        lead_score = 0.20
        if source == "Paid Search":
            lead_score += 0.12
        elif source == "Email":
            lead_score += 0.08
        elif source == "Direct":
            lead_score -= 0.05
            
        if device == "Mobile":
            lead_score -= 0.06
        elif device == "Desktop":
            lead_score += 0.04
            
        has_lead = random.random() < lead_score
        
        lead_dt = None
        trial_dt = None
        purchase_dt = None
        
        if has_lead:
            # Lead submitted 2 to 45 mins after session start
            lead_dt = session_dt + timedelta(minutes=random.randint(2, 45))
            
            # Trial started decision (approx 40% of leads start a trial)
            trial_score = 0.40
            if source == "Paid Social":
                trial_score += 0.10  # Social retargeting works well for trials
            has_trial = random.random() < trial_score
            
            if has_trial:
                # Trial starts 0 to 3 days after lead
                trial_dt = lead_dt + timedelta(days=random.randint(0, 3), hours=random.randint(1, 23))
                
                # Purchase decision (approx 30% of trials purchase a subscription)
                purchase_score = 0.30
                if plan_discount := (random.random() < 0.20):  # Promos convert better
                    purchase_score += 0.15
                has_purchase = random.random() < purchase_score
                
                if has_purchase:
                    # Purchase happens 7 or 14 days after trial (standard trial periods)
                    trial_period_days = random.choice([7, 14])
                    purchase_dt = trial_dt + timedelta(days=trial_period_days, hours=random.randint(-12, 12))
                    
        # --- INJECT ANOMALIES & DIRTiness ---
        # 1. Date format anomalies: ~10% rows will have DD/MM/YYYY HH:MM:SS format
        use_inconsistent_date = random.random() < 0.10
        
        def format_dt(dt):
            if dt is None:
                return ""
            if use_inconsistent_date:
                return dt.strftime("%d/%m/%Y %H:%M:%S")
            return dt.strftime("%Y-%m-%d %H:%M:%S")
            
        session_str = format_dt(session_dt)
        lead_str = format_dt(lead_dt)
        trial_str = format_dt(trial_dt)
        purchase_str = format_dt(purchase_dt)
        
        # 2. String casing inconsistencies
        # Traffic Source
        source_str = source
        if random.random() < 0.05:
            source_str = source.lower()
        elif random.random() < 0.05:
            source_str = source.upper()
        elif random.random() < 0.03:
            source_str = source.replace(" ", "_") # e.g. Paid_Search
            
        # Device
        device_str = device
        if random.random() < 0.05:
            device_str = device.lower()
        elif random.random() < 0.05:
            device_str = device.upper()
            
        # 3. Missing paid campaigns
        # ~3% of paid campaigns have empty/missing value
        campaign_str = campaign
        if source in ["Paid Search", "Paid Social", "Email"] and random.random() < 0.03:
            campaign_str = ""
            
        # 4. Funnel logic / Sequential errors
        # A. Trial started before Lead (~0.5% errors)
        if lead_dt and trial_dt and random.random() < 0.005:
            # swap dates
            lead_str, trial_str = trial_str, lead_str
        # B. Purchase without Trial (~0.5% errors)
        if purchase_dt and trial_dt and random.random() < 0.005:
            trial_str = ""  # missing trial stage but has purchase
        # C. Purchase date before session date (~0.5% errors)
        if purchase_dt and random.random() < 0.005:
            purchase_str = format_dt(session_dt - timedelta(days=5))
            
        row = [
            sess_id, user_id, source_str, campaign_str, device_str,
            session_str, lead_str, trial_str, purchase_str
        ]
        
        records_list.append(row)
        writer.writerow(row)
        
    # Inject duplicated records (~2% duplicates = 200 rows)
    duplicates = random.sample(records_list, 200)
    for dup in duplicates:
        writer.writerow(dup)

print(f"Data generation complete. Raw data saved to {raw_data_path}")
print(f"Total records generated: {len(records_list) + len(duplicates)}")
