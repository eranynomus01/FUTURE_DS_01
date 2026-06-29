import csv
import random
import os
from datetime import datetime, timedelta

# Ensure target directory exists
os.makedirs("data", exist_ok=True)

# Define master lists for generation
segments = ["Consumer", "Corporate", "Home Office"]
regions = ["East", "West", "Central", "South"]
region_states = {
    "East": [("New York", "New York City"), ("Pennsylvania", "Philadelphia"), ("Massachusetts", "Boston"), ("New York", "Buffalo"), ("Pennsylvania", "Pittsburgh")],
    "West": [("California", "Los Angeles"), ("California", "San Francisco"), ("Washington", "Seattle"), ("Oregon", "Portland"), ("California", "San Diego")],
    "Central": [("Texas", "Houston"), ("Illinois", "Chicago"), ("Texas", "Austin"), ("Ohio", "Columbus"), ("Texas", "Dallas")],
    "South": [("Florida", "Miami"), ("Georgia", "Atlanta"), ("North Carolina", "Charlotte"), ("Florida", "Tampa"), ("Florida", "Orlando")]
}
ship_modes = ["Standard Class", "Second Class", "First Class", "Same Day"]

# Product details: Category -> Sub-Category -> List of (Product Name, Base Unit Price, Base Profit Margin)
products_db = {
    "Technology": {
        "Phones": [
            ("iPhone 15 Pro Max", 1199.00, 0.25),
            ("Samsung Galaxy S24 Ultra", 1299.00, 0.22),
            ("Google Pixel 8 Pro", 999.00, 0.20),
            ("OnePlus 12", 799.00, 0.18)
        ],
        "Accessories": [
            ("Logitech MX Master 3S Mouse", 99.99, 0.45),
            ("Apple Magic Keyboard", 129.00, 0.40),
            ("Anker USB-C 8-in-1 Hub", 59.99, 0.50),
            ("SanDisk 1TB Portable SSD", 119.99, 0.35)
        ],
        "Copiers": [
            ("Canon ImageRUNNER Advanced", 2499.99, 0.30),
            ("HP LaserJet Enterprise Copier", 1899.99, 0.28),
            ("Brother Monochrome Laser Multifunction", 349.99, 0.25)
        ],
        "Machines": [
            ("Epson 3D Creator Printer", 799.00, 0.15),
            ("Star Micronics POS Receipt Printer", 229.00, 0.20),
            ("Zebra Desktop Barcode Label Printer", 310.00, 0.22)
        ]
    },
    "Furniture": {
        "Chairs": [
            ("Herman Miller Aeron Chair", 1499.00, 0.12),
            ("Steelcase Gesture Office Chair", 1299.00, 0.10),
            ("Hon Ignition 2.0 Ergonomic Chair", 419.00, 0.15),
            ("Serta Ergonomic Office Task Chair", 199.99, 0.18)
        ],
        "Bookcases": [
            ("IKEA Billy Bookcase - Birch", 89.00, 0.08),
            ("Bush Furniture 5-Shelf Bookcase", 159.99, 0.10),
            ("Sauder Select 5-Shelf Bookcase", 119.00, 0.12)
        ],
        "Tables": [
            ("ApexDesk Elite Series Standing Desk", 659.00, 0.08),
            ("Bush Furniture Conference Table", 549.99, 0.05),
            ("Rustic Wood Dining & Work Table", 450.00, 0.07)
        ],
        "Furnishings": [
            ("BenQ ScreenBar e-Reading LED Lamp", 109.00, 0.35),
            ("Geometric Area Rug 5x7", 89.99, 0.40),
            ("Frameless Wall Mirror", 49.99, 0.30),
            ("Desk Organizer Tray Set", 24.99, 0.50)
        ]
    },
    "Office Supplies": {
        "Paper": [
            ("Hammermill Printer Paper 20lb (Case)", 45.00, 0.30),
            ("Xerox Copy Paper (Ream)", 8.99, 0.35),
            ("Neenah Premium Cardstock (Pack)", 15.99, 0.40)
        ],
        "Art": [
            ("Prismacolor Premier Colored Pencils 72ct", 64.99, 0.45),
            ("Crayola Ultra-Clean Washable Markers", 9.99, 0.55),
            ("Faber-Castell Pitt Artist Pens 8ct", 28.00, 0.48),
            ("Sketchbook 9x12 Spiral Bound", 12.50, 0.50)
        ],
        "Binders": [
            ("Avery Heavy-Duty 3-Ring Binder 2-Inch", 7.49, 0.60),
            ("Wilson Jones 3-Ring View Binder 1-Inch", 4.99, 0.65),
            ("Heavy Duty Sheet Protectors 100pk", 11.99, 0.55)
        ],
        "Storage": [
            ("Sterilite 64 Qt Latching Storage Box", 14.99, 0.25),
            ("Lorell 2-Drawer File Cabinet Mobile", 119.99, 0.15),
            ("Bankers Box Storage Boxes 10pk", 29.99, 0.30)
        ],
        "Appliances": [
            ("Dyson V8 Absolute Cordless Vacuum", 449.99, 0.18),
            ("Keurig K-Classic Coffee Maker", 89.99, 0.22),
            ("Black+Decker Compact Mini Fridge", 159.00, 0.15)
        ]
    }
}

# Generate Customer Database
customers = []
first_names = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda", "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica", "Thomas", "Sarah", "Charles", "Karen"]
last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin"]

# Create 500 unique customers
for i in range(1, 501):
    c_id = f"CS-{i:05d}"
    c_name = f"{random.choice(first_names)} {random.choice(last_names)}"
    c_segment = random.choice(segments)
    customers.append({"id": c_id, "name": c_name, "segment": c_segment})

# Date range: 2023-01-01 to 2025-12-31
start_date = datetime(2023, 1, 1)
end_date = datetime(2025, 12, 31)
date_delta = (end_date - start_date).days

print("Generating raw sales data...")

# Open CSV for writing
raw_data_path = "data/raw_sales_data.csv"
with open(raw_data_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    # Header
    writer.writerow([
        "Order ID", "Order Date", "Ship Date", "Ship Mode", "Customer ID", 
        "Customer Name", "Segment", "Country", "City", "State", "Region", 
        "Product ID", "Category", "Sub-Category", "Product Name", 
        "Unit Price", "Quantity", "Discount", "Profit"
    ])
    
    orders_list = []
    
    # Generate 5,000 orders
    for o_idx in range(1, 5001):
        order_id = f"CA-202{random.randint(3,5)}-{100000 + o_idx}"
        
        # Order and Ship Dates
        rand_days = random.randint(0, date_delta)
        ord_dt = start_date + timedelta(days=rand_days)
        ship_days = random.choice([1, 2, 3, 4, 5, 7])
        shp_dt = ord_dt + timedelta(days=ship_days)
        
        # Introduce date format issues (mixed formats: YYYY-MM-DD vs DD/MM/YYYY)
        # ~10% of rows will have DD/MM/YYYY format
        if random.random() < 0.10:
            order_date_str = ord_dt.strftime("%d/%m/%Y")
            ship_date_str = shp_dt.strftime("%d/%m/%Y")
        else:
            order_date_str = ord_dt.strftime("%Y-%m-%d")
            ship_date_str = shp_dt.strftime("%Y-%m-%d")
            
        ship_mode = random.choice(ship_modes)
        # Inconsistent ship mode (some null values ~1%)
        if random.random() < 0.01:
            ship_mode = ""
            
        # Customer
        cust = random.choice(customers)
        cust_id = cust["id"]
        cust_name = cust["name"]
        cust_segment = cust["segment"]
        
        # Inconsistent Customer segment/name issues
        # ~2% missing segment
        if random.random() < 0.02:
            cust_segment = ""
        # ~1% missing customer name (but has ID, which can be resolved!)
        if random.random() < 0.01:
            cust_name = ""
            
        # Region, State, City
        region = random.choice(regions)
        state, city = random.choice(region_states[region])
        country = "United States"
        
        # Product
        category = random.choice(list(products_db.keys()))
        sub_category = random.choice(list(products_db[category].keys()))
        product = random.choice(products_db[category][sub_category])
        prod_name, unit_price, base_profit_margin = product
        prod_id = f"{category[:3]}-{sub_category[:3]}-{random.randint(1000, 9999)}"
        
        # Quantity
        quantity = random.randint(1, 10)
        # Inconsistent Quantity: inject some logical errors (~0.5% negative quantities)
        if random.random() < 0.005:
            quantity = -1 * quantity
            
        # Discount
        discount = random.choice([0.0, 0.0, 0.1, 0.2, 0.2, 0.3, 0.5, 0.7])
        # Inconsistent discount (~0.2% invalid discount like 1.5 i.e. 150%)
        if random.random() < 0.002:
            discount = 1.5
            
        # Compute Sales and Profit (Profit = Sales * Margin - Discount effect)
        # Sales = Unit Price * Quantity * (1 - Discount)
        sales_val = unit_price * abs(quantity) * (1 - discount if discount <= 1.0 else 0)
        profit_val = sales_val * base_profit_margin - (sales_val * discount * 0.1) # rough formula
        
        if random.random() < 0.02:
            profit_val_str = ""
        else:
            profit_val_str = f"{profit_val:.2f}"
            
        row = [
            order_id, order_date_str, ship_date_str, ship_mode, cust_id,
            cust_name, cust_segment, country, city, state, region,
            prod_id, category, sub_category, prod_name,
            f"{unit_price:.2f}", quantity, f"{discount:.2f}", profit_val_str
        ]
        
        orders_list.append(row)
        writer.writerow(row)
        
    # Inject duplicated records (~2% duplicates = 100 rows)
    duplicates = random.sample(orders_list, 100)
    for dup in duplicates:
        writer.writerow(dup)

print(f"Data generation complete. Raw data saved to {raw_data_path}")
print(f"Total records generated (including ~100 duplicates): {5000 + 100}")
