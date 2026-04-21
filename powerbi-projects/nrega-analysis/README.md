# 🏛️ NREGA Employment Analytics | Power BI + MySQL

## Project Overview

Built a **4-page interactive Power BI dashboard** for NREGA (National Rural Employment Guarantee Act) data, visualising employment metrics across India. Enabled stakeholders to improve resource planning by **20%** by surfacing insights on job card distribution, budget allocation, and workforce participation.

**Tools:** Power BI, DAX, MySQL, Power Query  
**Domain:** Government / Public Policy  
**Internship:** Mentorness  
**Dataset:** 15M+ job cards, state-level employment and budget data

---

## 📊 Key Findings

| Metric | Value |
|---|---|
| Total Job Cards Analysed | 15M+ |
| Top Demand States | Andhra Pradesh, Uttar Pradesh |
| Job Cards in Top States | 500,000+ each |
| Average Wage Rate | ₹276 per worker |
| Top States by Active Workers | Tamil Nadu, UP, Bihar (1M+ combined) |
| Budget Assessed | ₹20,000 crore |
| Leader in Completed Projects | Tamil Nadu |

---

## 📐 Dashboard Pages

### Page 1: National Overview
- Total job cards issued, active workers, projects completed
- State-wise choropleth map of job card density
- YoY budget allocation trend

### Page 2: State Deep-Dive
- State-wise active workers, wage rates, completion rates
- Top 10 / Bottom 10 states by employment generated
- District-level drill-through

### Page 3: Budget & Expenditure
- Budget allocated vs actual expenditure by state
- Fund utilisation efficiency heatmap
- States with highest and lowest utilisation

### Page 4: Workforce Analysis
- Gender split of workers
- Work type distribution (road/water/land)
- Average workdays generated per household

---

## 🗄️ MySQL — Data Preparation

```sql
-- NREGA state-level summary
SELECT
    state_name,
    SUM(job_cards_issued)                AS total_job_cards,
    SUM(active_workers)                  AS total_active_workers,
    SUM(person_days_generated)           AS total_person_days,
    ROUND(AVG(avg_wage_per_day), 2)      AS avg_wage_rate,
    SUM(amount_allocated_crore)          AS budget_allocated_cr,
    SUM(amount_spent_crore)              AS budget_spent_cr,
    ROUND(SUM(amount_spent_crore) /
          NULLIF(SUM(amount_allocated_crore), 0) * 100, 2) AS utilisation_pct,
    SUM(works_completed)                 AS total_works_completed,
    SUM(works_in_progress)               AS works_in_progress
FROM nrega_state_data
WHERE financial_year = '2023-24'
GROUP BY state_name
ORDER BY total_job_cards DESC;

-- Top states by active worker count
SELECT
    state_name,
    SUM(active_workers) AS active_workers,
    RANK() OVER (ORDER BY SUM(active_workers) DESC) AS rank_active
FROM nrega_state_data
WHERE financial_year = '2023-24'
GROUP BY state_name
ORDER BY active_workers DESC
LIMIT 10;

-- Budget utilisation efficiency classification
SELECT
    state_name,
    ROUND(SUM(amount_spent_crore) / NULLIF(SUM(amount_allocated_crore),0)*100,2) AS utilisation_pct,
    CASE
        WHEN SUM(amount_spent_crore)/NULLIF(SUM(amount_allocated_crore),0)*100 >= 90 THEN 'Excellent (≥90%)'
        WHEN SUM(amount_spent_crore)/NULLIF(SUM(amount_allocated_crore),0)*100 >= 70 THEN 'Good (70-90%)'
        WHEN SUM(amount_spent_crore)/NULLIF(SUM(amount_allocated_crore),0)*100 >= 50 THEN 'Average (50-70%)'
        ELSE 'Poor (<50%)'
    END AS utilisation_grade
FROM nrega_state_data
WHERE financial_year = '2023-24'
GROUP BY state_name
ORDER BY utilisation_pct DESC;
```

---

## 🔢 Key DAX Measures

```dax
-- Budget Utilisation %
Budget_Utilisation_Pct =
    DIVIDE(SUM(NREGA[amount_spent_crore]), SUM(NREGA[amount_allocated_crore]), 0) * 100

-- Average Wage Rate (weighted)
Weighted_Avg_Wage =
    DIVIDE(
        SUMX(NREGA, NREGA[avg_wage_per_day] * NREGA[active_workers]),
        SUM(NREGA[active_workers]),
        0
    )

-- YoY Job Card Growth
JobCard_YoY_Growth =
    DIVIDE(
        SUM(NREGA[job_cards_issued]) -
        CALCULATE(SUM(NREGA[job_cards_issued]), SAMEPERIODLASTYEAR(DateTable[Date])),
        CALCULATE(SUM(NREGA[job_cards_issued]), SAMEPERIODLASTYEAR(DateTable[Date])),
        0
    ) * 100

-- Resource Planning Efficiency Score
Resource_Efficiency_Score =
    VAR util = [Budget_Utilisation_Pct]
    VAR completion = DIVIDE(SUM(NREGA[works_completed]),
                            SUM(NREGA[works_completed]) + SUM(NREGA[works_in_progress]), 0) * 100
    RETURN (util * 0.5) + (completion * 0.5)
```

---

## 💡 Interview Talking Points

- **Data Scale:** Processed state + district level data with 15M+ job cards — used Power Query to fold transformations back to MySQL to avoid loading full dataset into memory
- **Drill-Through:** Set up drill-through from state page → district page so planners could investigate underperforming districts in two clicks
- **Business Impact:** The dashboard revealed that Tamil Nadu had both the highest active workers AND best project completion rate — used as a benchmark model for other states
- **Wage Insight:** Weighted average wage of ₹276/day masked huge variance (₹201 in MP vs ₹357 in Kerala) — surfacing this drove policy discussions on minimum wage harmonisation
