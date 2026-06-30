# %% [markdown]
# # Customer Churn and Retention Data Exploration
# This script demonstrates how to load, inspect, and analyze the subscription dataset.

# %%
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os

# %%
# Adjust working directory if running inside the scripts directory
if os.path.basename(os.getcwd()) == "scripts":
    os.chdir("..")

# %%
# Load the dataset
# You can load either 'data/raw_customer_data.csv' or 'data/cleaned_customer_data.csv'
data_path = "data/cleaned_customer_data.csv"
print(f"Loading data from: {data_path}")
df = pd.read_csv(data_path)

# %%
# Display the first 5 rows
print("\n--- First 5 rows of the dataset (df.head()) ---")
print(df.head())

# %%
# Display basic information about the dataset columns and types
print("\n--- Dataset Summary Info ---")
df.info()

# %%
# Display statistical summary of numerical columns
print("\n--- Descriptive Statistics ---")
print(df.describe())

# %%
# Display Churn Rate by Plan
print("\n--- Churn Rate by Subscription Plan ---")
plan_stats = df.groupby("Plan").agg(
    total=("Customer ID", "count"),
    churned=("Status", lambda x: (x == "Churned").sum())
)
plan_stats["churn_rate"] = (plan_stats["churned"] / plan_stats["total"] * 100).round(2)
print(plan_stats)

# %%
# Example Visualization: Churn Rate by Billing Interval
print("\nGenerating visualization for Churn Rate by Billing Interval...")
interval_stats = df.groupby("Billing Interval").agg(
    total=("Customer ID", "count"),
    churned=("Status", lambda x: (x == "Churned").sum())
)
interval_stats["churn_rate"] = (interval_stats["churned"] / interval_stats["total"] * 100).round(2)

fig, ax = plt.subplots(figsize=(6, 4))
bars = ax.bar(interval_stats.index, interval_stats["churn_rate"], color=['#ef4444', '#10b981'], width=0.5)

# Add values on top of bars
for bar in bars:
    height = bar.get_height()
    ax.annotate(f'{height:.1f}%',
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3),  # 3 points vertical offset
                textcoords="offset points",
                ha='center', va='bottom', fontweight='bold')

ax.set_ylabel('Churn Rate (%)')
ax.set_title('Churn Rate by Billing Interval')
ax.set_ylim(0, max(interval_stats["churn_rate"]) + 10)
ax.grid(axis='y', linestyle='--', alpha=0.5)

plt.tight_layout()
plt.show()
