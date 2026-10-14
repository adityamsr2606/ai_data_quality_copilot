import csv
import random
from datetime import datetime, timedelta

random.seed(42)

customers = [f"C{i:04d}" for i in range(1, 201)]
products = [f"P{i:03d}" for i in range(1, 51)]

cities = [
    "Delhi",
    "Noida",
    "Gurugram",
    "Ghaziabad",
    "Lucknow",
    "Jaipur",
    "Mumbai",
    "Bengaluru",
]

payment_methods = [
    "UPI",
    "Card",
    "Cash",
    "Net Banking",
]

start_date = datetime(2026, 9, 1)

rows = []

for order_id in range(1, 1001):

    customer_id = random.choice(customers)
    product_id = random.choice(products)

    order_date = start_date + timedelta(
        days=random.randint(0, 30)
    )

    quantity = random.randint(1, 5)

    unit_price = round(
        random.uniform(100, 5000),
        2
    )

    city = random.choice(cities)
    payment_method = random.choice(payment_methods)

    rows.append([
        f"O{order_id:05d}",
        customer_id,
        product_id,
        order_date.strftime("%Y-%m-%d"),
        quantity,
        unit_price,
        city,
        payment_method,
    ])


# -------------------------------------------------
# Introduce intentional data-quality problems
# -------------------------------------------------

# 1. Missing customer_id
for i in random.sample(range(1000), 15):
    rows[i][1] = ""


# 2. Negative quantity
for i in random.sample(range(1000), 8):
    rows[i][4] = -random.randint(1, 3)


# 3. Missing unit_price
for i in random.sample(range(1000), 10):
    rows[i][5] = ""


# 4. Invalid payment method
for i in random.sample(range(1000), 7):
    rows[i][7] = "Bitcoin"


# 5. Duplicate order IDs
duplicate_indexes = random.sample(range(1000), 10)

for i in duplicate_indexes:
    source_index = random.randint(0, 999)
    rows[i][0] = rows[source_index][0]


# -------------------------------------------------
# Write CSV
# -------------------------------------------------

with open(
    "orders.csv",
    "w",
    newline="",
    encoding="utf-8"
) as file:

    writer = csv.writer(file)

    writer.writerow([
        "order_id",
        "customer_id",
        "product_id",
        "order_date",
        "quantity",
        "unit_price",
        "city",
        "payment_method",
    ])

    writer.writerows(rows)


print("orders.csv created successfully!")
print(f"Total records: {len(rows)}")