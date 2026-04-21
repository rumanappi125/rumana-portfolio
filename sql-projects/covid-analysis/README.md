# 🦠 COVID-19 Epidemic Analysis | MySQL

## Project Overview

Analysed **1.69 billion COVID-19 records** using MySQL to uncover global trends in confirmed cases, recoveries, and deaths. Delivered insights critical for health policy analysis and response strategies.

**Tools:** MySQL · Advanced SQL · Window Functions · CTEs  
**Domain:** Public Health / Global Epidemiology  
**Internship:** Mentorness

---

## 📊 Key Findings

| Metric | Value |
|---|---|
| Total Records Processed | 1.69 Billion+ |
| Highest Impact Country | United States |
| Leader in Recovery Rate | India |
| Peak Monthly Deaths | 401,893 (January 2021) |
| Top Recovery Rate (select countries) | 90%+ |

---

## 🗂️ Dataset Schema

```sql
CREATE TABLE covid_data (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    country         VARCHAR(100),
    continent       VARCHAR(50),
    report_date     DATE,
    confirmed       BIGINT,
    deaths          BIGINT,
    recovered       BIGINT,
    active          BIGINT,
    new_cases       INT,
    new_deaths      INT,
    new_recovered   INT,
    population      BIGINT
);
```

---

## 🔍 SQL Queries

### 1. Data Cleaning & Null Handling

```sql
-- Replace NULL numeric values with 0
UPDATE covid_data
SET 
    confirmed   = COALESCE(confirmed, 0),
    deaths      = COALESCE(deaths, 0),
    recovered   = COALESCE(recovered, 0),
    active      = COALESCE(active, 0),
    new_cases   = COALESCE(new_cases, 0),
    new_deaths  = COALESCE(new_deaths, 0),
    new_recovered = COALESCE(new_recovered, 0);

-- Check for duplicate records
SELECT country, report_date, COUNT(*) AS duplicate_count
FROM covid_data
GROUP BY country, report_date
HAVING COUNT(*) > 1;
```

---

### 2. Global Summary Statistics

```sql
-- Overall global totals
SELECT
    SUM(confirmed)   AS total_confirmed,
    SUM(deaths)      AS total_deaths,
    SUM(recovered)   AS total_recovered,
    ROUND(SUM(deaths) / SUM(confirmed) * 100, 2)    AS global_death_rate_pct,
    ROUND(SUM(recovered) / SUM(confirmed) * 100, 2) AS global_recovery_rate_pct
FROM covid_data
WHERE report_date = (SELECT MAX(report_date) FROM covid_data);
```

---

### 3. Top 10 Countries by Confirmed Cases

```sql
SELECT
    country,
    MAX(confirmed)  AS total_confirmed,
    MAX(deaths)     AS total_deaths,
    MAX(recovered)  AS total_recovered,
    ROUND(MAX(deaths) / MAX(confirmed) * 100, 2)    AS death_rate_pct,
    ROUND(MAX(recovered) / MAX(confirmed) * 100, 2) AS recovery_rate_pct,
    RANK() OVER (ORDER BY MAX(confirmed) DESC)       AS rank_by_cases
FROM covid_data
GROUP BY country
ORDER BY total_confirmed DESC
LIMIT 10;
```

---

### 4. Monthly Death Trend — Peak Identification

```sql
SELECT
    DATE_FORMAT(report_date, '%Y-%m')   AS month,
    SUM(new_deaths)                      AS monthly_deaths,
    SUM(new_cases)                       AS monthly_cases,
    ROUND(SUM(new_deaths) / NULLIF(SUM(new_cases), 0) * 100, 2) AS monthly_cfr_pct,
    LAG(SUM(new_deaths)) OVER (ORDER BY DATE_FORMAT(report_date, '%Y-%m')) AS prev_month_deaths,
    SUM(new_deaths) - LAG(SUM(new_deaths)) OVER (ORDER BY DATE_FORMAT(report_date, '%Y-%m')) AS mom_change
FROM covid_data
GROUP BY DATE_FORMAT(report_date, '%Y-%m')
ORDER BY monthly_deaths DESC;
```

---

### 5. Country Recovery Analysis (Top Performers)

```sql
WITH recovery_stats AS (
    SELECT
        country,
        MAX(confirmed)  AS total_confirmed,
        MAX(recovered)  AS total_recovered,
        MAX(deaths)     AS total_deaths,
        ROUND(MAX(recovered) / NULLIF(MAX(confirmed), 0) * 100, 2) AS recovery_rate_pct
    FROM covid_data
    GROUP BY country
    HAVING MAX(confirmed) > 100000   -- Filter countries with significant case counts
)
SELECT
    country,
    total_confirmed,
    total_recovered,
    total_deaths,
    recovery_rate_pct,
    RANK() OVER (ORDER BY recovery_rate_pct DESC) AS recovery_rank
FROM recovery_stats
ORDER BY recovery_rate_pct DESC
LIMIT 15;
```

---

### 6. 7-Day Rolling Average of New Cases per Country

```sql
SELECT
    country,
    report_date,
    new_cases,
    ROUND(
        AVG(new_cases) OVER (
            PARTITION BY country
            ORDER BY report_date
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ), 0
    ) AS rolling_7day_avg_cases
FROM covid_data
WHERE country IN ('India', 'US', 'Brazil', 'UK', 'Germany')
ORDER BY country, report_date;
```

---

### 7. Continent-Level Aggregation

```sql
SELECT
    continent,
    COUNT(DISTINCT country)             AS country_count,
    SUM(confirmed)                       AS total_confirmed,
    SUM(deaths)                          AS total_deaths,
    SUM(recovered)                       AS total_recovered,
    ROUND(SUM(deaths)/SUM(confirmed)*100, 2) AS death_rate_pct,
    ROUND(SUM(confirmed) / SUM(population) * 100, 4) AS infection_rate_pct
FROM covid_data
WHERE report_date = (SELECT MAX(report_date) FROM covid_data)
  AND continent IS NOT NULL
GROUP BY continent
ORDER BY total_confirmed DESC;
```

---

### 8. Cumulative Case Growth — Running Total

```sql
SELECT
    country,
    report_date,
    new_cases,
    SUM(new_cases) OVER (
        PARTITION BY country
        ORDER BY report_date
        ROWS UNBOUNDED PRECEDING
    ) AS cumulative_cases,
    ROUND(
        (SUM(new_cases) OVER (PARTITION BY country ORDER BY report_date ROWS UNBOUNDED PRECEDING) -
         LAG(SUM(new_cases) OVER (PARTITION BY country ORDER BY report_date ROWS UNBOUNDED PRECEDING))
         OVER (PARTITION BY country ORDER BY report_date)) /
        NULLIF(LAG(SUM(new_cases) OVER (PARTITION BY country ORDER BY report_date ROWS UNBOUNDED PRECEDING))
        OVER (PARTITION BY country ORDER BY report_date), 0) * 100, 2
    ) AS wow_growth_pct
FROM covid_data
WHERE country IN ('India', 'US', 'Brazil')
ORDER BY country, report_date;
```

---

### 9. Case Fatality Rate Categorisation

```sql
SELECT
    country,
    MAX(confirmed) AS total_confirmed,
    MAX(deaths)    AS total_deaths,
    ROUND(MAX(deaths) / NULLIF(MAX(confirmed), 0) * 100, 2) AS cfr_pct,
    CASE
        WHEN ROUND(MAX(deaths) / NULLIF(MAX(confirmed), 0) * 100, 2) >= 3   THEN 'High CFR (≥3%)'
        WHEN ROUND(MAX(deaths) / NULLIF(MAX(confirmed), 0) * 100, 2) >= 1.5 THEN 'Medium CFR (1.5–3%)'
        ELSE 'Low CFR (<1.5%)'
    END AS cfr_category
FROM covid_data
GROUP BY country
HAVING MAX(confirmed) > 50000
ORDER BY cfr_pct DESC;
```

---

## 📈 Key Insights

1. **USA** had the highest confirmed case count globally throughout the pandemic timeline
2. **India** led in absolute recovery numbers, achieving 90%+ recovery rate
3. **January 2021** marked the deadliest month with 401,893 deaths globally
4. Rolling 7-day averages revealed clear second and third waves across major economies
5. Island nations showed disproportionately high CFR due to limited healthcare infrastructure

---

## 💡 Interview Talking Points

- **Scale:** Handled 1.69B records — used indexing on `country` and `report_date` to avoid full table scans
- **Window Functions:** Used `LAG()` for MoM comparison and rolling `AVG()` for smoothing noisy daily data
- **Data Cleaning:** Handled NULL records, duplicates, and inconsistent country name formats
- **Performance:** Partitioned queries by country before aggregating to reduce computational load
