# %% [markdown]
# # Marketing Funnel & Lead Conversion Exploration
# This script demonstrates how to load, inspect, and analyze the marketing conversion funnel dataset.

# %%
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os

# %%
# Force working directory to be the script's directory so relative paths work
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# %%
# Load the dataset
data_path = "data/cleaned_funnel_data.csv"
print(f"Loading data from: {data_path}")
df = pd.read_csv(data_path)

# %%
# Display the first 5 rows
print("\n--- First 5 rows of the dataset (df.head()) ---")
print(df.head())

# %%
# Display basic information about the columns
print("\n--- Dataset Summary Info ---")
df.info()

# %%
# Funnel Stage Counts
visitors = len(df)
leads = df["Lead Form Submitted"].notna().sum()
trials = df["Trial Started"].notna().sum()
customers = df["Subscription Purchased"].notna().sum()

print("\n--- Funnel Stage Counts ---")
print(f"Visitors: {visitors}")
print(f"Leads:    {leads} ({leads/visitors*100:.2f}% conversion from visitor)")
print(f"Trials:   {trials} ({trials/leads*100:.2f}% conversion from lead)")
print(f"Customer: {customers} ({customers/trials*100:.2f}% conversion from trial)")
print(f"Overall Visitor-to-Customer: {customers/visitors*100:.2f}%")

# %%
# Example Visualization: Funnel Conversion Progression
stages = ["Visitors", "Leads", "Trials", "Customers"]
counts = [visitors, leads, trials, customers]
conversions = [100.0, (leads/visitors)*100, (trials/visitors)*100, (customers/visitors)*100]

fig, ax1 = plt.subplots(figsize=(8, 5))

# Plot bar chart for counts
color = '#4f46e5'
ax1.set_xlabel('Funnel Stage')
ax1.set_ylabel('Sessions Count', color=color)
bars = ax1.bar(stages, counts, color=color, alpha=0.7, width=0.5)
ax1.tick_params(axis='y', labelcolor=color)

# Create second y-axis for percentage
ax2 = ax1.twinx()  
color = '#06b6d4'
ax2.set_ylabel('Overall Conversion Rate (%)', color=color)
ax2.plot(stages, conversions, color=color, marker='o', linewidth=2.5, label='Overall Conv %')
ax2.tick_params(axis='y', labelcolor=color)
ax2.set_ylim(0, 110)

# Add values on top of bars
for bar in bars:
    height = bar.get_height()
    ax1.annotate(f'{height:,}',
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3),  
                textcoords="offset points",
                ha='center', va='bottom', fontweight='bold')

plt.title('Marketing Conversion Funnel Progression')
plt.tight_layout()
plt.show()
