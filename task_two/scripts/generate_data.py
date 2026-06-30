import csv
import random
import os
from datetime import datetime, timedelta

# Force working directory to be the parent of this script (task_two)
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Ensure target directory exists
os.makedirs("data", exist_ok=True)

# Master lists for generation
regions = ["East", "West", "Central", "South"]
plans = ["Basic", "Pro", "Enterprise"]
intervals = ["Monthly", "Annually"]
statuses = ["Active", "Churned"]
churn_reasons = [
    "Competitor offered better price",
    "Product lacks required features",
    "Customer service was unsatisfactory",
    "Difficult to use / poor UX",
    "Company went out of business / budget cuts",
    "No longer needed",
    "Onboarding experience was poor"
]

# Base monthly prices for plans
plan_base_prices = {
    "Basic": 29.00,
    "Pro": 79.00,
    "Enterprise": 249.00
}

# Generate Customer Profiles
first_names = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda", "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica", "Thomas", "Sarah", "Charles", "Karen"]
last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin"]

# Create 5,000 unique customers with fixed profile attributes
customers_db = []
for i in range(1, 5001):
    cust_id = f"CS-{i:05d}"
    name = f"{random.choice(first_names)} {random.choice(last_names)}"
    region = random.choice(regions)
    customers_db.append({"id": cust_id, "name": name, "region": region})

# Date range: 2023-01-01 to 2025-12-31
start_date = datetime(2023, 1, 1)
end_date = datetime(2025, 12, 31)
date_delta = (end_date - start_date).days

print("Generating raw customer subscription data...")

raw_data_path = "data/raw_customer_data.csv"
with open(raw_data_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    # Header
    writer.writerow([
        "Customer ID", "Customer Name", "Region", "Signup Date", 
        "Plan", "Billing Interval", "Status", "Churn Date", 
        "Churn Reason", "Monthly Charges", "Total Charges", 
        "Support Tickets", "Usage Frequency", "NPS Score"
    ])
    
    records_list = []
    
    for cust in customers_db:
        cust_id = cust["id"]
        cust_name = cust["name"]
        region = cust["region"]
        
        # Signup Date
        rand_days = random.randint(0, date_delta)
        signup_dt = start_date + timedelta(days=rand_days)
        
        # Choose billing parameters
        plan = random.choice(plans)
        interval = random.choice(intervals)
        
        # Decide churn status based on behavior variables (correlation modeling)
        # We will model behavior scores
        # Pro and Enterprise are less likely to churn
        # Annual billing is less likely to churn
        # High support tickets increases churn
        # High usage frequency decreases churn
        support_tickets = random.randint(0, 15)
        usage_frequency = random.randint(1, 30)
        
        # Churn score
        churn_score = 0.15
        if plan == "Basic":
            churn_score += 0.15
        elif plan == "Enterprise":
            churn_score -= 0.05
            
        if interval == "Monthly":
            churn_score += 0.20
            
        churn_score += (support_tickets * 0.04)
        churn_score -= (usage_frequency * 0.015)
        
        # Clamp score between 0.02 and 0.95
        churn_score = max(0.02, min(0.95, churn_score))
        
        status = "Active"
        if random.random() < churn_score:
            status = "Churned"
            
        # Determine Churn Date if Churned
        churn_dt = None
        churn_reason = ""
        if status == "Churned":
            # Churn must happen after signup and before end_date
            days_active_max = (end_date - signup_dt).days
            if days_active_max > 30:
                days_to_churn = random.randint(30, days_active_max)
                churn_dt = signup_dt + timedelta(days=days_to_churn)
            else:
                churn_dt = signup_dt + timedelta(days=5) # quick churn
                
            churn_reason = random.choice(churn_reasons)
            
        # Calculate monthly charges based on Plan & Billing Interval
        base_price = plan_base_prices[plan]
        if interval == "Annually":
            # 20% discount
            monthly_charge = base_price * 0.8
        else:
            monthly_charge = base_price
            
        # Calculate months active
        end_period_dt = churn_dt if status == "Churned" else end_date
        days_active = (end_period_dt - signup_dt).days
        months_active = max(1.0, round(days_active / 30.4, 1))
        total_charge = monthly_charge * months_active
        
        # NPS Score (correlated with churn)
        # NPS is empty for ~15% of users (they ignored the survey)
        nps = ""
        if random.random() > 0.15:
            if status == "Churned":
                nps = max(1, min(10, int(random.normalvariate(4.5, 2.0))))
            else:
                nps = max(1, min(10, int(random.normalvariate(8.0, 1.5))))
                
        # --- INJECT ANOMALIES & DIRTiness ---
        # 1. Date format anomalies: ~10% rows will have DD/MM/YYYY format for signup_dt and churn_dt
        if random.random() < 0.10:
            signup_date_str = signup_dt.strftime("%d/%m/%Y")
            churn_date_str = churn_dt.strftime("%d/%m/%Y") if churn_dt else ""
        else:
            signup_date_str = signup_dt.strftime("%Y-%m-%d")
            churn_date_str = churn_dt.strftime("%Y-%m-%d") if churn_dt else ""
            
        # 2. String casing inconsistencies
        # Plan
        plan_str = plan
        if random.random() < 0.05:
            plan_str = plan.lower()
        elif random.random() < 0.05:
            plan_str = plan.upper()
            
        # Billing Interval
        interval_str = interval
        if random.random() < 0.05:
            interval_str = interval.lower()
        elif random.random() < 0.05:
            interval_str = "Annual" if interval == "Annually" else "Monthly"
        if random.random() < 0.02:
            interval_str += "  "  # trailing space
            
        # Status
        status_str = status
        if random.random() < 0.05:
            status_str = status.lower()
        elif random.random() < 0.05:
            status_str = status.upper()
            
        # 3. Missing customer details (that can be resolved)
        # ~1.5% missing names
        if random.random() < 0.015:
            cust_name = ""
        # ~1% missing regions
        if random.random() < 0.01:
            region = ""
            
        # 4. Charge errors
        monthly_charge_str = f"{monthly_charge:.2f}"
        total_charge_str = f"{total_charge:.2f}"
        # ~0.5% negative monthly charge
        if random.random() < 0.005:
            monthly_charge_str = f"-{monthly_charge:.2f}"
        # ~1% missing monthly charges (empty)
        if random.random() < 0.01:
            monthly_charge_str = ""
        # ~0.5% extreme outlier
        if random.random() < 0.005:
            monthly_charge_str = "9999.00"
            
        # 5. Contradictory Status / Dates
        # ~1% active users will have a churn date set
        if status == "Active" and random.random() < 0.01:
            churn_date_str = (signup_dt + timedelta(days=60)).strftime("%Y-%m-%d")
            # And maybe a churn reason
            if random.random() < 0.5:
                churn_reason = random.choice(churn_reasons)
        # ~1% churned users will have empty churn date
        elif status == "Churned" and random.random() < 0.01:
            churn_date_str = ""
            
        row = [
            cust_id, cust_name, region, signup_date_str, 
            plan_str, interval_str, status_str, churn_date_str, 
            churn_reason, monthly_charge_str, total_charge_str, 
            support_tickets, usage_frequency, nps
        ]
        
        records_list.append(row)
        writer.writerow(row)
        
    # Inject duplicated records (~2% duplicates = 100 rows)
    duplicates = random.sample(records_list, 100)
    for dup in duplicates:
        writer.writerow(dup)

print(f"Data generation complete. Raw data saved to {raw_data_path}")
print(f"Total records generated: {len(records_list) + len(duplicates)}")
