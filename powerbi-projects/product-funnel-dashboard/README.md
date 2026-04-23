# Product Funnel Dashboard — Target
**Analyst:** Rumana Appi | **Client:** Target (via E-Mech Solutions)
**Tool:** Power BI Desktop | **Data:** 230K+ funnel events · 78K+ orders · 50K users

---

## Sample Data & Build Guide

All sample data and DAX measures are included in this folder so the dashboard can be fully reproduced:

| File | Description |
|------|-------------|
| `generate_sample_data.py` | Run this to generate all 6 CSV data files |
| `dax_measures.md` | All DAX measures — copy into Power BI |
| `data/dim_date.csv` | 182 rows — date dimension |
| `data/dim_users.csv` | 50,000 rows — user profiles |
| `data/dim_products.csv` | 200 rows — product catalogue |
| `data/dim_regions.csv` | 5 rows — regions with RLS manager emails |
| `data/fact_funnel_events.csv` | 230,000+ rows — funnel event log |
| `data/fact_orders.csv` | 78,000+ rows — completed transactions |

**To regenerate data:** `pip install pandas numpy && python generate_sample_data.py`

---

# Original Project Documentation

# 🛒 Product Funnel Dashboard | Power BI — Target Retail

## Project Overview

Designed and built a **Product Funnel Dashboard** for Target (via E-Mech Solutions) to visualise user journeys across signup → explore → checkout → payment pages. Identified critical drop-off stages, enabling product teams to act and **increase checkout completions by 15%**.

**Tools:** Power BI, DAX, SQL (AWS Redshift), Power Query  
**Domain:** E-Commerce / Retail  
**Company:** E-Mech Solutions → Client: Target  
**Dataset:** Multi-terabyte user behaviour logs

---

## 📊 Key Results

| KPI | Result |
|---|---|
| Checkout Completion Improvement | +15% |
| KPIs Defined & Tracked | 100+ |
| Automated Reporting Time Saved | 9 hrs/week |
| Query Optimisation Gain | 35% faster execution |

---

## 📐 Dashboard Pages

### Page 1: Funnel Overview
- Total users entering each funnel stage
- Conversion rate between each step
- Overall funnel conversion (Signup → Payment)
- Drop-off % at each stage

### Page 2: Segment Analysis
- Funnel performance by device (Mobile / Desktop / App)
- Funnel performance by new vs returning users
- Funnel performance by product category

### Page 3: Trend Analysis
- Daily / Weekly funnel conversion trends
- MoM and WoW comparisons
- Anomaly detection on drop-off spikes

### Page 4: KPI Scorecard
- DAU, MAU, Session Duration
- Revenue, AOV, Transactions
- Retention, Churn, Repeat Purchase Rate

---

## 🔢 DAX Measures

### Core Funnel Metrics

```dax
-- Total Users at each stage
Signup_Users = CALCULATE(DISTINCTCOUNT(Events[user_id]), Events[stage] = "Signup")
Explore_Users = CALCULATE(DISTINCTCOUNT(Events[user_id]), Events[stage] = "Explore")
Checkout_Users = CALCULATE(DISTINCTCOUNT(Events[user_id]), Events[stage] = "Checkout")
Payment_Users = CALCULATE(DISTINCTCOUNT(Events[user_id]), Events[stage] = "Payment")

-- Stage Conversion Rates
Signup_to_Explore_Rate =
    DIVIDE([Explore_Users], [Signup_Users], 0) * 100

Explore_to_Checkout_Rate =
    DIVIDE([Checkout_Users], [Explore_Users], 0) * 100

Checkout_to_Payment_Rate =
    DIVIDE([Payment_Users], [Checkout_Users], 0) * 100

Overall_Conversion_Rate =
    DIVIDE([Payment_Users], [Signup_Users], 0) * 100

-- Drop-off
Checkout_Dropoff_Rate = 100 - [Checkout_to_Payment_Rate]
```

### Time Intelligence

```dax
-- MoM Conversion Change
MoM_Conversion_Change =
    VAR current_month = [Overall_Conversion_Rate]
    VAR prev_month = CALCULATE(
        [Overall_Conversion_Rate],
        DATEADD(DateTable[Date], -1, MONTH)
    )
    RETURN current_month - prev_month

-- Rolling 7-Day DAU
DAU_7Day_Rolling =
    CALCULATE(
        [Daily_Active_Users],
        DATESINPERIOD(DateTable[Date], LASTDATE(DateTable[Date]), -7, DAY)
    )

-- YoY Revenue Growth
Revenue_YoY_Growth =
    DIVIDE(
        [Total_Revenue] - CALCULATE([Total_Revenue], SAMEPERIODLASTYEAR(DateTable[Date])),
        CALCULATE([Total_Revenue], SAMEPERIODLASTYEAR(DateTable[Date])),
        0
    ) * 100
```

### Customer KPIs

```dax
-- Churn Rate
Monthly_Churn_Rate =
    DIVIDE(
        CALCULATE(DISTINCTCOUNT(Users[user_id]), Users[status] = "Churned"),
        CALCULATE(DISTINCTCOUNT(Users[user_id]), PREVIOUSMONTH(DateTable[Date])),
        0
    ) * 100

-- Retention Rate
Retention_Rate = 100 - [Monthly_Churn_Rate]

-- Average Order Value
AOV =
    DIVIDE([Total_Revenue], [Total_Transactions], 0)

-- Repeat Purchase Rate
Repeat_Purchase_Rate =
    DIVIDE(
        CALCULATE(DISTINCTCOUNT(Orders[user_id]),
            FILTER(Orders, CALCULATE(COUNTROWS(Orders)) > 1)),
        DISTINCTCOUNT(Orders[user_id]),
        0
    ) * 100
```

---

## 🗄️ SQL — Data Preparation (Redshift)

```sql
-- Funnel stage aggregation query for Power BI DirectQuery
WITH funnel_events AS (
    SELECT
        user_id,
        session_id,
        event_date,
        stage,
        device_type,
        user_type,        -- new / returning
        product_category,
        ROW_NUMBER() OVER (PARTITION BY user_id, session_id, stage
                           ORDER BY event_timestamp) AS stage_rank
    FROM user_events
    WHERE event_date >= DATEADD(day, -90, CURRENT_DATE)
      AND stage IN ('Signup','Explore','Checkout','Payment')
),
deduped AS (
    SELECT * FROM funnel_events WHERE stage_rank = 1
)
SELECT
    event_date,
    stage,
    device_type,
    user_type,
    product_category,
    COUNT(DISTINCT user_id) AS unique_users,
    COUNT(DISTINCT session_id) AS sessions
FROM deduped
GROUP BY event_date, stage, device_type, user_type, product_category
ORDER BY event_date, stage;
```

---

## 💡 Interview Talking Points

- **Row Level Security (RLS):** Implemented RLS so regional managers only see their region's funnel data using `USERPRINCIPALNAME()` in DAX
- **DirectQuery vs Import:** Used Import mode with scheduled refresh (every 4 hrs) since Redshift queries were too slow for DirectQuery at this data volume
- **15% Impact:** The dashboard revealed that Mobile users dropped off at checkout at 2.3× the rate of Desktop — leading to a UX fix on the mobile checkout form that drove the 15% improvement
- **100+ KPIs:** Organised KPIs into a semantic layer in Power BI's data model so business teams could self-serve without writing DAX
