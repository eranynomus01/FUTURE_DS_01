# %% [markdown]
# # Retail Sales Data Exploration
# This notebook/script demonstrates how to load, inspect, and analyze the retail sales dataset.

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
# You can load either 'data/raw_sales_data.csv' or 'data/cleaned_sales_data.csv'
data_path = "data/cleaned_sales_data.csv"
print(f"Loading data from: {data_path}")
df = pd.read_csv(data_path)

# %%
# Display the first 5 rows (df.head())
# This matches the interactive output shown in your Jupyter Notebook / pandas view
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
# Example Visualization: Total Sales and Profit by Customer Segment
print("\nGenerating visualization for Sales by Segment...")
segment_data = df.groupby("Segment")[["Sales", "Profit"]].sum().reset_index()

fig, ax = plt.subplots(figsize=(8, 5))
x = np.arange(len(segment_data["Segment"]))
width = 0.35

rects1 = ax.bar(x - width/2, segment_data["Sales"], width, label='Sales', color='#4f46e5')
rects2 = ax.bar(x + width/2, segment_data["Profit"], width, label='Profit', color='#10b981')

ax.set_ylabel('Amount ($)')
ax.set_title('Sales and Profit by Customer Segment')
ax.set_xticks(x)
ax.set_xticklabels(segment_data["Segment"])
ax.legend()
ax.grid(axis='y', linestyle='--', alpha=0.5)

plt.tight_layout()
plt.show()
