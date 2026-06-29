import pandas as pd
import json
import os

print("Starting exploratory data analysis and summary generation...")

clean_csv_path = "data/cleaned_sales_data.csv"
analysis_dir = "data/analysis"
os.makedirs(analysis_dir, exist_ok=True)

if not os.path.exists(clean_csv_path):
    raise FileNotFoundError(f"Cleaned CSV not found at {clean_csv_path}. Please run clean_data.py first.")

df = pd.read_csv(clean_csv_path)

# Ensure Order Date is datetime for parsing
df["Order Date DT"] = pd.to_datetime(df["Order Date"])

# --- 1. Global KPIs ---
total_sales = float(df["Sales"].sum())
total_profit = float(df["Profit"].sum())
avg_margin = float(df["Profit"].sum() / df["Sales"].sum()) if df["Sales"].sum() > 0 else 0.0
total_orders = int(df["Order ID"].nunique())

kpi_data = {
    "total_sales": round(total_sales, 2),
    "total_profit": round(total_profit, 2),
    "avg_margin": round(avg_margin, 4),
    "total_orders": total_orders
}

with open(os.path.join(analysis_dir, "kpis.json"), "w") as f:
    json.dump(kpi_data, f, indent=4)

# --- 2. Revenue and Profit Trends over Time (Monthly & Yearly) ---
# Monthly
df["YearMonth"] = df["Order Date DT"].dt.strftime("%Y-%m")
monthly_agg = df.groupby("YearMonth").agg(
    sales=("Sales", "sum"),
    profit=("Profit", "sum"),
    orders=("Order ID", "nunique")
).reset_index()

monthly_data = []
for _, row in monthly_agg.sort_values(by="YearMonth").iterrows():
    monthly_data.append({
        "month": row["YearMonth"],
        "sales": round(float(row["sales"]), 2),
        "profit": round(float(row["profit"]), 2),
        "orders": int(row["orders"])
    })

# Yearly
df["Year"] = df["Order Date DT"].dt.year
yearly_agg = df.groupby("Year").agg(
    sales=("Sales", "sum"),
    profit=("Profit", "sum"),
    orders=("Order ID", "nunique")
).reset_index()

yearly_data = []
for _, row in yearly_agg.sort_values(by="Year").iterrows():
    yearly_data.append({
        "year": int(row["Year"]),
        "sales": round(float(row["sales"]), 2),
        "profit": round(float(row["profit"]), 2),
        "orders": int(row["orders"])
    })

trend_data = {
    "monthly": monthly_data,
    "yearly": yearly_data
}

with open(os.path.join(analysis_dir, "revenue_trends.json"), "w") as f:
    json.dump(trend_data, f, indent=4)

# --- 3. Category and Sub-Category Performance ---
cat_subcat_agg = df.groupby(["Category", "Sub-Category"]).agg(
    sales=("Sales", "sum"),
    profit=("Profit", "sum"),
    quantity=("Quantity", "sum")
).reset_index()

cat_subcat_data = {}
for cat in df["Category"].unique():
    cat_df = cat_subcat_agg[cat_subcat_agg["Category"] == cat]
    cat_sales = float(df[df["Category"] == cat]["Sales"].sum())
    cat_profit = float(df[df["Category"] == cat]["Profit"].sum())
    cat_qty = int(df[df["Category"] == cat]["Quantity"].sum())
    
    subcats = []
    for _, row in cat_df.iterrows():
        s_sales = float(row["sales"])
        s_profit = float(row["profit"])
        subcats.append({
            "sub_category": row["Sub-Category"],
            "sales": round(s_sales, 2),
            "profit": round(s_profit, 2),
            "quantity": int(row["quantity"]),
            "margin": round(s_profit / s_sales, 4) if s_sales > 0 else 0.0
        })
        
    cat_subcat_data[cat] = {
        "sales": round(cat_sales, 2),
        "profit": round(cat_profit, 2),
        "quantity": cat_qty,
        "margin": round(cat_profit / cat_sales, 4) if cat_sales > 0 else 0.0,
        "sub_categories": subcats
    }

with open(os.path.join(analysis_dir, "category_analysis.json"), "w") as f:
    json.dump(cat_subcat_data, f, indent=4)

# --- 4. Regional Performance (Region -> State -> City) ---
region_agg = df.groupby("Region").agg(
    sales=("Sales", "sum"),
    profit=("Profit", "sum"),
    quantity=("Quantity", "sum")
).reset_index()

regional_data = {}
for _, r_row in region_agg.iterrows():
    reg = r_row["Region"]
    reg_sales = float(r_row["sales"])
    reg_profit = float(r_row["profit"])
    
    # State-level breakdown inside region
    state_df = df[df["Region"] == reg].groupby("State").agg(
        sales=("Sales", "sum"),
        profit=("Profit", "sum")
    ).reset_index().sort_values(by="sales", ascending=False).head(5)
    
    states_data = []
    for _, s_row in state_df.iterrows():
        states_data.append({
            "state": s_row["State"],
            "sales": round(float(s_row["sales"]), 2),
            "profit": round(float(s_row["profit"]), 2)
        })
        
    regional_data[reg] = {
        "sales": round(reg_sales, 2),
        "profit": round(reg_profit, 2),
        "quantity": int(r_row["quantity"]),
        "margin": round(reg_profit / reg_sales, 4) if reg_sales > 0 else 0.0,
        "top_states": states_data
    }

with open(os.path.join(analysis_dir, "regional_analysis.json"), "w") as f:
    json.dump(regional_data, f, indent=4)

# --- 5. Customer Segment Performance ---
segment_agg = df.groupby("Segment").agg(
    sales=("Sales", "sum"),
    profit=("Profit", "sum"),
    quantity=("Quantity", "sum"),
    orders=("Order ID", "nunique")
).reset_index()

segment_data = []
for _, row in segment_agg.iterrows():
    seg_sales = float(row["sales"])
    seg_profit = float(row["profit"])
    segment_data.append({
        "segment": row["Segment"],
        "sales": round(seg_sales, 2),
        "profit": round(seg_profit, 2),
        "quantity": int(row["quantity"]),
        "orders": int(row["orders"]),
        "margin": round(seg_profit / seg_sales, 4) if seg_sales > 0 else 0.0
    })

with open(os.path.join(analysis_dir, "segment_analysis.json"), "w") as f:
    json.dump(segment_data, f, indent=4)

# --- 6. Top Selling Products ---
product_agg = df.groupby(["Product ID", "Product Name", "Category", "Sub-Category"]).agg(
    sales=("Sales", "sum"),
    profit=("Profit", "sum"),
    quantity=("Quantity", "sum")
).reset_index()

top_by_sales = product_agg.sort_values(by="sales", ascending=False).head(15)
top_products_data = []
for _, row in top_by_sales.iterrows():
    p_sales = float(row["sales"])
    p_profit = float(row["profit"])
    top_products_data.append({
        "product_id": row["Product ID"],
        "product_name": row["Product Name"],
        "category": row["Category"],
        "sub_category": row["Sub-Category"],
        "sales": round(p_sales, 2),
        "profit": round(p_profit, 2),
        "quantity": int(row["quantity"]),
        "margin": round(p_profit / p_sales, 4) if p_sales > 0 else 0.0
    })

with open(os.path.join(analysis_dir, "top_products.json"), "w") as f:
    json.dump(top_products_data, f, indent=4)

# --- 7. Recent Transactions Preview (Latest 200) ---
latest_tx = df.sort_values(by="Order Date DT", ascending=False).head(200)
tx_cols = [
    "Order ID", "Order Date", "Ship Mode", "Customer Name", "Segment", 
    "City", "State", "Region", "Category", "Sub-Category", "Product Name", 
    "Sales", "Quantity", "Discount", "Profit"
]
tx_preview_df = latest_tx[tx_cols]
tx_preview_data = []
for _, row in tx_preview_df.iterrows():
    tx_preview_data.append({
        "order_id": row["Order ID"],
        "order_date": row["Order Date"],
        "ship_mode": row["Ship Mode"],
        "customer_name": row["Customer Name"],
        "segment": row["Segment"],
        "city": row["City"],
        "state": row["State"],
        "region": row["Region"],
        "category": row["Category"],
        "sub_category": row["Sub-Category"],
        "product_name": row["Product Name"],
        "sales": float(row["Sales"]),
        "quantity": int(row["Quantity"]),
        "discount": float(row["Discount"]),
        "profit": float(row["Profit"])
    })

with open(os.path.join(analysis_dir, "transactions_preview.json"), "w") as f:
    json.dump(tx_preview_data, f, indent=4)

# Create full transactions data for interactive Javascript analysis
tx_full_data = []
for _, row in df[tx_cols].iterrows():
    tx_full_data.append({
        "order_id": row["Order ID"],
        "order_date": row["Order Date"],
        "ship_mode": row["Ship Mode"],
        "customer_name": row["Customer Name"],
        "segment": row["Segment"],
        "city": row["City"],
        "state": row["State"],
        "region": row["Region"],
        "category": row["Category"],
        "sub_category": row["Sub-Category"],
        "product_name": row["Product Name"],
        "sales": float(row["Sales"]),
        "quantity": int(row["Quantity"]),
        "discount": float(row["Discount"]),
        "profit": float(row["Profit"])
    })

# --- 8. Export JS File for CORS-free local execution ---
web_dir = "web"
os.makedirs(web_dir, exist_ok=True)
js_data = {
    "kpis": kpi_data,
    "trends": trend_data,
    "category": cat_subcat_data,
    "regional": regional_data,
    "segment": segment_data,
    "top_products": top_products_data,
    "transactions": tx_full_data # Full clean data for JS filter engine
}
with open(os.path.join(web_dir, "data.js"), "w") as f:
    f.write(f"const SALES_DATA = {json.dumps(js_data, indent=4)};")

print(f"Data analysis and summary generation complete. Files exported to {analysis_dir} and {web_dir}/data.js")
