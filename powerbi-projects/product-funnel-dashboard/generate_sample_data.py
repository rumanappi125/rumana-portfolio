"""
Product Funnel Dashboard — Sample Data Generator
Analyst: Rumana Appi | Client: Target (E-Mech Solutions)
Generates realistic retail funnel + orders data for Power BI dashboard.

Run: python generate_sample_data.py
Output: data/ folder with 6 CSV files ready to load into Power BI
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import random

np.random.seed(42)
random.seed(42)

OUTPUT_DIR = "data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── CONFIG ────────────────────────────────────────────────
START_DATE   = datetime(2024, 10, 1)
END_DATE     = datetime(2025, 3, 31)
N_USERS      = 50_000
N_EVENTS     = 500_000

REGIONS      = ["North", "South", "East", "West", "Central"]
DEVICES      = ["Mobile", "Desktop", "Tablet", "App"]
CATEGORIES   = ["Electronics", "Clothing", "Home & Living", "Beauty", "Sports", "Food & Grocery", "Books", "Toys"]
FUNNEL_STEPS = ["Signup", "Explore", "Checkout", "Payment"]

# Funnel drop-off rates (cumulative reach)
FUNNEL_RATES = {"Signup": 1.0, "Explore": 0.74, "Checkout": 0.45, "Payment": 0.31}

# Region managers for RLS
REGION_MANAGERS = {
    "North":   "north.manager@target.com",
    "South":   "south.manager@target.com",
    "East":    "east.manager@target.com",
    "West":    "west.manager@target.com",
    "Central": "central.manager@target.com",
}

print("Generating data... this takes ~30 seconds.")


# ── 1. DIM DATE ───────────────────────────────────────────
def gen_dim_date():
    dates = pd.date_range(START_DATE, END_DATE, freq="D")
    df = pd.DataFrame({"date": dates})
    df["date_key"]      = df["date"].dt.strftime("%Y%m%d").astype(int)
    df["year"]          = df["date"].dt.year
    df["quarter"]       = df["date"].dt.quarter
    df["month_num"]     = df["date"].dt.month
    df["month_name"]    = df["date"].dt.strftime("%B")
    df["month_short"]   = df["date"].dt.strftime("%b")
    df["week_num"]      = df["date"].dt.isocalendar().week.astype(int)
    df["day_of_week"]   = df["date"].dt.day_name()
    df["is_weekend"]    = df["date"].dt.dayofweek >= 5
    df["year_month"]    = df["date"].dt.strftime("%Y-%m")
    df["year_week"]     = df["date"].dt.strftime("%Y-W%V")
    df["date"]          = df["date"].dt.strftime("%Y-%m-%d")
    df.to_csv(f"{OUTPUT_DIR}/dim_date.csv", index=False)
    print(f"  dim_date.csv          — {len(df):,} rows")


# ── 2. DIM USERS ──────────────────────────────────────────
def gen_dim_users():
    signup_dates = [
        (START_DATE + timedelta(days=random.randint(0, (END_DATE - START_DATE).days))).strftime("%Y-%m-%d")
        for _ in range(N_USERS)
    ]
    df = pd.DataFrame({
        "user_id":          [f"USR{str(i).zfill(6)}" for i in range(1, N_USERS + 1)],
        "signup_date":      signup_dates,
        "age_group":        np.random.choice(["18-24", "25-34", "35-44", "45-54", "55+"],
                                             N_USERS, p=[0.18, 0.32, 0.25, 0.15, 0.10]),
        "gender":           np.random.choice(["Male", "Female", "Other"], N_USERS, p=[0.44, 0.53, 0.03]),
        "region":           np.random.choice(REGIONS, N_USERS, p=[0.22, 0.20, 0.18, 0.25, 0.15]),
        "device_preference":np.random.choice(DEVICES, N_USERS, p=[0.48, 0.30, 0.10, 0.12]),
        "loyalty_tier":     np.random.choice(["Bronze", "Silver", "Gold", "Platinum"],
                                             N_USERS, p=[0.40, 0.30, 0.20, 0.10]),
        "is_new_user":      np.random.choice([True, False], N_USERS, p=[0.35, 0.65]),
    })
    df.to_csv(f"{OUTPUT_DIR}/dim_users.csv", index=False)
    print(f"  dim_users.csv         — {len(df):,} rows")
    return df


# ── 3. DIM PRODUCTS ───────────────────────────────────────
def gen_dim_products():
    products = []
    for cat in CATEGORIES:
        for i in range(1, 26):
            products.append({
                "product_id":   f"PRD-{cat[:3].upper()}-{str(i).zfill(3)}",
                "product_name": f"{cat} Item {i}",
                "category":     cat,
                "subcategory":  f"{cat} Sub {(i % 3) + 1}",
                "price_range":  np.random.choice(["Budget (<₹500)", "Mid (₹500–2000)", "Premium (>₹2000)"],
                                                  p=[0.35, 0.45, 0.20]),
                "avg_price":    round(np.random.uniform(200, 8000), 2),
                "is_active":    True,
            })
    df = pd.DataFrame(products)
    df.to_csv(f"{OUTPUT_DIR}/dim_products.csv", index=False)
    print(f"  dim_products.csv      — {len(df):,} rows")
    return df


# ── 4. DIM REGIONS (for RLS) ─────────────────────────────
def gen_dim_regions():
    df = pd.DataFrame([
        {"region": r, "manager_email": m, "region_head": f"{r} Head", "active": True}
        for r, m in REGION_MANAGERS.items()
    ])
    df.to_csv(f"{OUTPUT_DIR}/dim_regions.csv", index=False)
    print(f"  dim_regions.csv       — {len(df):,} rows")


# ── 5. FACT FUNNEL EVENTS ─────────────────────────────────
def gen_fact_funnel(users_df):
    records = []
    date_range = pd.date_range(START_DATE, END_DATE, freq="D")

    # Simulate weekly traffic with weekday boost + seasonal spikes
    for idx, row in users_df.iterrows():
        if idx % 10000 == 0:
            print(f"    Funnel progress: {idx:,}/{N_USERS:,}...")

        # Each user has 1–5 sessions
        n_sessions = np.random.choice([1, 2, 3, 4, 5], p=[0.40, 0.28, 0.17, 0.10, 0.05])
        for s in range(n_sessions):
            session_date = random.choice(date_range)
            session_id   = f"SES{random.randint(1000000, 9999999)}"
            device       = np.random.choice(DEVICES, p=[0.48, 0.30, 0.10, 0.12])

            # Walk down funnel with drop-off
            reached_payment = False
            for step in FUNNEL_STEPS:
                if random.random() > FUNNEL_RATES[step]:
                    break
                records.append({
                    "event_id":       f"EVT{len(records):08d}",
                    "user_id":        row["user_id"],
                    "session_id":     session_id,
                    "event_type":     step,
                    "event_date":     session_date.strftime("%Y-%m-%d"),
                    "device_type":    device,
                    "region":         row["region"],
                    "product_category": random.choice(CATEGORIES),
                    "page_time_sec":  int(np.random.exponential(45)),
                })
                if step == "Payment":
                    reached_payment = True

    df = pd.DataFrame(records)
    df.to_csv(f"{OUTPUT_DIR}/fact_funnel_events.csv", index=False)
    print(f"  fact_funnel_events.csv — {len(df):,} rows")
    return df


# ── 6. FACT ORDERS ────────────────────────────────────────
def gen_fact_orders(users_df, products_df):
    records = []
    date_range = pd.date_range(START_DATE, END_DATE, freq="D")

    for _, user in users_df.iterrows():
        n_orders = np.random.choice(
            [0, 1, 2, 3, 4, 5],
            p=[0.30, 0.25, 0.20, 0.12, 0.08, 0.05]
        )
        for _ in range(n_orders):
            product   = products_df.sample(1).iloc[0]
            order_date = random.choice(date_range)
            unit_price = round(product["avg_price"] * np.random.uniform(0.85, 1.15), 2)
            quantity   = np.random.choice([1, 2, 3], p=[0.70, 0.22, 0.08])
            discount   = round(np.random.choice([0, 5, 10, 15, 20], p=[0.50, 0.15, 0.20, 0.10, 0.05]) / 100, 2)

            gross   = round(unit_price * quantity, 2)
            disc_amt = round(gross * discount, 2)
            net     = round(gross - disc_amt, 2)

            records.append({
                "order_id":        f"ORD{len(records):08d}",
                "user_id":         user["user_id"],
                "product_id":      product["product_id"],
                "category":        product["category"],
                "order_date":      order_date.strftime("%Y-%m-%d"),
                "region":          user["region"],
                "device_type":     user["device_preference"],
                "unit_price":      unit_price,
                "quantity":        quantity,
                "gross_revenue":   gross,
                "discount_pct":    discount,
                "discount_amount": disc_amt,
                "net_revenue":     net,
                "status":          np.random.choice(["Completed","Cancelled","Returned"],
                                                    p=[0.88, 0.07, 0.05]),
                "payment_method":  np.random.choice(["Credit Card","Debit Card","UPI","Wallet","COD"],
                                                    p=[0.28, 0.22, 0.30, 0.12, 0.08]),
                "is_first_order":  False,
            })

    # Mark first orders
    df = pd.DataFrame(records)
    first_orders = df.groupby("user_id")["order_date"].idxmin()
    df.loc[first_orders, "is_first_order"] = True

    df.to_csv(f"{OUTPUT_DIR}/fact_orders.csv", index=False)
    print(f"  fact_orders.csv       — {len(df):,} rows")


# ── RUN ───────────────────────────────────────────────────
if __name__ == "__main__":
    gen_dim_date()
    users_df    = gen_dim_users()
    products_df = gen_dim_products()
    gen_dim_regions()
    gen_fact_funnel(users_df)
    gen_fact_orders(users_df, products_df)

    print(f"\nAll files saved to ./{OUTPUT_DIR}/")
    print("Load all 6 CSVs into Power BI Desktop to build the dashboard.")
