# DAX Measures — Product Funnel Dashboard
**Analyst:** Rumana Appi | **Client:** Target

Paste these into Power BI Desktop → Table view → New Measure.

---

## PAGE 1 — FUNNEL ANALYSIS

```dax
-- Total users at each funnel stage
Signup Users =
CALCULATE(DISTINCTCOUNT(fact_funnel_events[user_id]),
    fact_funnel_events[event_type] = "Signup")

Explore Users =
CALCULATE(DISTINCTCOUNT(fact_funnel_events[user_id]),
    fact_funnel_events[event_type] = "Explore")

Checkout Users =
CALCULATE(DISTINCTCOUNT(fact_funnel_events[user_id]),
    fact_funnel_events[event_type] = "Checkout")

Payment Users =
CALCULATE(DISTINCTCOUNT(fact_funnel_events[user_id]),
    fact_funnel_events[event_type] = "Payment")

-- Conversion rates between stages
Signup to Explore Rate =
DIVIDE([Explore Users], [Signup Users], 0)

Explore to Checkout Rate =
DIVIDE([Checkout Users], [Explore Users], 0)

Checkout to Payment Rate =
DIVIDE([Payment Users], [Checkout Users], 0)

Overall Conversion Rate =
DIVIDE([Payment Users], [Signup Users], 0)

-- Drop-off counts
Explore Drop-off =
[Signup Users] - [Explore Users]

Checkout Drop-off =
[Explore Users] - [Checkout Users]

Payment Drop-off =
[Checkout Users] - [Payment Users]
```

---

## PAGE 2 — REVENUE & ORDERS

```dax
Total Orders =
CALCULATE(COUNTROWS(fact_orders),
    fact_orders[status] = "Completed")

Gross Revenue =
CALCULATE(SUM(fact_orders[gross_revenue]),
    fact_orders[status] = "Completed")

Net Revenue =
CALCULATE(SUM(fact_orders[net_revenue]),
    fact_orders[status] = "Completed")

Total Discounts =
CALCULATE(SUM(fact_orders[discount_amount]),
    fact_orders[status] = "Completed")

Average Order Value =
DIVIDE([Net Revenue], [Total Orders], 0)

Gross Margin % =
DIVIDE([Net Revenue], [Gross Revenue], 0)

-- New vs Returning revenue
New Customer Revenue =
CALCULATE([Net Revenue], fact_orders[is_first_order] = TRUE())

Returning Customer Revenue =
CALCULATE([Net Revenue], fact_orders[is_first_order] = FALSE())

New Customer % =
DIVIDE([New Customer Revenue], [Net Revenue], 0)
```

---

## PAGE 3 — ENGAGEMENT & TRENDS

```dax
-- DAU / MAU / WAU
DAU =
CALCULATE(
    DISTINCTCOUNT(fact_funnel_events[user_id]),
    FILTER(fact_funnel_events,
        fact_funnel_events[event_date] = MAX(dim_date[date]))
)

MAU =
CALCULATE(
    DISTINCTCOUNT(fact_funnel_events[user_id]),
    DATESINPERIOD(dim_date[date], LASTDATE(dim_date[date]), -30, DAY)
)

WAU =
CALCULATE(
    DISTINCTCOUNT(fact_funnel_events[user_id]),
    DATESINPERIOD(dim_date[date], LASTDATE(dim_date[date]), -7, DAY)
)

Stickiness (DAU/MAU) =
DIVIDE([DAU], [MAU], 0)

-- MoM Revenue Growth
MoM Revenue Growth =
VAR CurrentMonth = [Net Revenue]
VAR PrevMonth =
    CALCULATE([Net Revenue],
        DATEADD(dim_date[date], -1, MONTH))
RETURN
    DIVIDE(CurrentMonth - PrevMonth, PrevMonth, 0)

-- WoW Conversion Change
WoW Checkout Rate Change =
VAR CurrentWeek = [Checkout to Payment Rate]
VAR PrevWeek =
    CALCULATE([Checkout to Payment Rate],
        DATEADD(dim_date[date], -7, DAY))
RETURN
    CurrentWeek - PrevWeek

-- Rolling 7-day revenue
Revenue 7-Day Rolling Avg =
AVERAGEX(
    DATESINPERIOD(dim_date[date], LASTDATE(dim_date[date]), -7, DAY),
    [Net Revenue]
)
```

---

## PAGE 4 — KPI SCORECARD

```dax
-- Retention (users active in both current and previous month)
Retained Users =
VAR CurrentUsers =
    CALCULATETABLE(VALUES(fact_funnel_events[user_id]),
        DATESINPERIOD(dim_date[date], LASTDATE(dim_date[date]), -30, DAY))
VAR PrevUsers =
    CALCULATETABLE(VALUES(fact_funnel_events[user_id]),
        DATESINPERIOD(dim_date[date], LASTDATE(dim_date[date]) - 30, -30, DAY))
RETURN
    COUNTROWS(INTERSECT(CurrentUsers, PrevUsers))

Retention Rate =
DIVIDE([Retained Users], [MAU], 0)

Churn Rate =
1 - [Retention Rate]

-- Revenue per user
Revenue per MAU =
DIVIDE([Net Revenue], [MAU], 0)

-- Cancellation rate
Cancellation Rate =
DIVIDE(
    CALCULATE(COUNTROWS(fact_orders), fact_orders[status] = "Cancelled"),
    COUNTROWS(fact_orders),
    0
)

-- Top category by revenue
Top Category =
CALCULATE(
    FIRSTNONBLANK(fact_orders[category], 1),
    TOPN(1,
        SUMMARIZE(fact_orders, fact_orders[category],
            "Rev", SUM(fact_orders[net_revenue])),
        [Rev], DESC)
)
```

---

## ROW LEVEL SECURITY (RLS)

In Power BI Desktop → Modeling → Manage Roles:

**Role: RegionManager**
```dax
-- On dim_regions table:
[manager_email] = USERPRINCIPALNAME()
```

Then relate `dim_regions[region]` to both `fact_orders[region]`
and `fact_funnel_events[region]` so the filter cascades.

---

## DATA MODEL RELATIONSHIPS

```
dim_date[date]        → fact_funnel_events[event_date]   (1:*)
dim_date[date]        → fact_orders[order_date]          (1:*)
dim_users[user_id]    → fact_funnel_events[user_id]      (1:*)
dim_users[user_id]    → fact_orders[user_id]             (1:*)
dim_products[product_id] → fact_orders[product_id]       (1:*)
dim_regions[region]   → fact_funnel_events[region]       (1:*)
dim_regions[region]   → fact_orders[region]              (1:*)
```
