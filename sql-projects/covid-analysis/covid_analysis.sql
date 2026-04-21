-- ============================================================
-- COVID-19 Epidemic Analysis | MySQL
-- Analyst: Rumana Appi | Internship: Mentorness
-- Dataset: 1.69 Billion records
-- ============================================================

-- ── 1. DATABASE SETUP ──────────────────────────────────────

CREATE DATABASE IF NOT EXISTS covid_analysis;
USE covid_analysis;

CREATE TABLE covid_data (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    country         VARCHAR(100),
    continent       VARCHAR(50),
    report_date     DATE,
    confirmed       BIGINT DEFAULT 0,
    deaths          BIGINT DEFAULT 0,
    recovered       BIGINT DEFAULT 0,
    active          BIGINT DEFAULT 0,
    new_cases       INT    DEFAULT 0,
    new_deaths      INT    DEFAULT 0,
    new_recovered   INT    DEFAULT 0,
    population      BIGINT
);

-- Index for query performance
CREATE INDEX idx_country_date ON covid_data (country, report_date);
CREATE INDEX idx_continent    ON covid_data (continent);
CREATE INDEX idx_date         ON covid_data (report_date);

-- ── 2. DATA CLEANING ───────────────────────────────────────

-- Replace NULLs with 0
UPDATE covid_data
SET 
    confirmed     = COALESCE(confirmed, 0),
    deaths        = COALESCE(deaths, 0),
    recovered     = COALESCE(recovered, 0),
    active        = COALESCE(active, 0),
    new_cases     = COALESCE(new_cases, 0),
    new_deaths    = COALESCE(new_deaths, 0),
    new_recovered = COALESCE(new_recovered, 0);

-- Fix negative new_cases/new_deaths (data entry errors)
UPDATE covid_data SET new_cases    = 0 WHERE new_cases    < 0;
UPDATE covid_data SET new_deaths   = 0 WHERE new_deaths   < 0;
UPDATE covid_data SET new_recovered= 0 WHERE new_recovered< 0;

-- Remove exact duplicate rows
DELETE c1 FROM covid_data c1
INNER JOIN covid_data c2
    ON c1.country = c2.country
   AND c1.report_date = c2.report_date
   AND c1.id > c2.id;

-- ── 3. GLOBAL SUMMARY ─────────────────────────────────────

SELECT
    SUM(confirmed)   AS total_confirmed,
    SUM(deaths)      AS total_deaths,
    SUM(recovered)   AS total_recovered,
    ROUND(SUM(deaths)    / NULLIF(SUM(confirmed), 0) * 100, 2) AS global_death_rate_pct,
    ROUND(SUM(recovered) / NULLIF(SUM(confirmed), 0) * 100, 2) AS global_recovery_rate_pct,
    (SELECT MAX(report_date) FROM covid_data) AS data_as_of
FROM covid_data
WHERE report_date = (SELECT MAX(report_date) FROM covid_data);

-- ── 4. TOP 10 COUNTRIES BY CONFIRMED CASES ────────────────

SELECT
    country,
    MAX(confirmed)  AS total_confirmed,
    MAX(deaths)     AS total_deaths,
    MAX(recovered)  AS total_recovered,
    ROUND(MAX(deaths)    / NULLIF(MAX(confirmed), 0) * 100, 2) AS death_rate_pct,
    ROUND(MAX(recovered) / NULLIF(MAX(confirmed), 0) * 100, 2) AS recovery_rate_pct,
    RANK() OVER (ORDER BY MAX(confirmed) DESC) AS rank_confirmed
FROM covid_data
GROUP BY country
ORDER BY total_confirmed DESC
LIMIT 10;

-- ── 5. MONTHLY TREND — DEATHS & CASES ────────────────────

SELECT
    DATE_FORMAT(report_date, '%Y-%m') AS month,
    SUM(new_cases)   AS monthly_new_cases,
    SUM(new_deaths)  AS monthly_new_deaths,
    ROUND(SUM(new_deaths) / NULLIF(SUM(new_cases), 0) * 100, 2) AS monthly_cfr_pct,
    LAG(SUM(new_deaths)) OVER (ORDER BY DATE_FORMAT(report_date, '%Y-%m')) AS prev_month_deaths,
    SUM(new_deaths) -
        LAG(SUM(new_deaths)) OVER (ORDER BY DATE_FORMAT(report_date, '%Y-%m')) AS mom_death_change
FROM covid_data
GROUP BY DATE_FORMAT(report_date, '%Y-%m')
ORDER BY month;

-- ── 6. COUNTRY RECOVERY RANKING (CTEs) ────────────────────

WITH recovery_stats AS (
    SELECT
        country,
        MAX(confirmed) AS total_confirmed,
        MAX(recovered) AS total_recovered,
        MAX(deaths)    AS total_deaths,
        ROUND(MAX(recovered) / NULLIF(MAX(confirmed), 0) * 100, 2) AS recovery_rate_pct
    FROM covid_data
    GROUP BY country
    HAVING MAX(confirmed) > 100000
),
ranked AS (
    SELECT *,
        RANK() OVER (ORDER BY recovery_rate_pct DESC) AS recovery_rank,
        RANK() OVER (ORDER BY total_confirmed DESC)   AS case_rank
    FROM recovery_stats
)
SELECT * FROM ranked ORDER BY recovery_rank LIMIT 20;

-- ── 7. 7-DAY ROLLING AVERAGE ──────────────────────────────

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
    ) AS rolling_7day_avg_cases,
    ROUND(
        AVG(new_deaths) OVER (
            PARTITION BY country
            ORDER BY report_date
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ), 0
    ) AS rolling_7day_avg_deaths
FROM covid_data
WHERE country IN ('India', 'US', 'Brazil', 'United Kingdom', 'Germany')
ORDER BY country, report_date;

-- ── 8. CUMULATIVE CASES + WoW GROWTH RATE ─────────────────

WITH cumulative AS (
    SELECT
        country,
        report_date,
        new_cases,
        SUM(new_cases) OVER (
            PARTITION BY country ORDER BY report_date
            ROWS UNBOUNDED PRECEDING
        ) AS cumulative_cases
    FROM covid_data
)
SELECT
    country,
    report_date,
    new_cases,
    cumulative_cases,
    LAG(cumulative_cases, 7) OVER (PARTITION BY country ORDER BY report_date) AS cases_7days_ago,
    ROUND(
        (cumulative_cases - LAG(cumulative_cases, 7) OVER (PARTITION BY country ORDER BY report_date))
        / NULLIF(LAG(cumulative_cases, 7) OVER (PARTITION BY country ORDER BY report_date), 0) * 100, 2
    ) AS wow_growth_pct
FROM cumulative
WHERE country IN ('India', 'US', 'Brazil')
ORDER BY country, report_date;

-- ── 9. CONTINENT SUMMARY ──────────────────────────────────

SELECT
    continent,
    COUNT(DISTINCT country)                               AS countries_affected,
    SUM(confirmed)                                         AS total_confirmed,
    SUM(deaths)                                            AS total_deaths,
    SUM(recovered)                                         AS total_recovered,
    ROUND(SUM(deaths)    / NULLIF(SUM(confirmed), 0) * 100, 2) AS death_rate_pct,
    ROUND(SUM(recovered) / NULLIF(SUM(confirmed), 0) * 100, 2) AS recovery_rate_pct,
    ROUND(SUM(confirmed) / NULLIF(SUM(population), 0) * 100, 4) AS infection_rate_pct
FROM covid_data
WHERE report_date = (SELECT MAX(report_date) FROM covid_data)
  AND continent IS NOT NULL
GROUP BY continent
ORDER BY total_confirmed DESC;

-- ── 10. CFR CATEGORISATION ────────────────────────────────

SELECT
    country,
    MAX(confirmed) AS total_confirmed,
    MAX(deaths)    AS total_deaths,
    ROUND(MAX(deaths) / NULLIF(MAX(confirmed), 0) * 100, 2) AS cfr_pct,
    CASE
        WHEN ROUND(MAX(deaths) / NULLIF(MAX(confirmed), 0) * 100, 2) >= 3.0   THEN 'High CFR (≥3%)'
        WHEN ROUND(MAX(deaths) / NULLIF(MAX(confirmed), 0) * 100, 2) >= 1.5   THEN 'Medium CFR (1.5–3%)'
        ELSE 'Low CFR (<1.5%)'
    END AS cfr_category
FROM covid_data
GROUP BY country
HAVING MAX(confirmed) > 50000
ORDER BY cfr_pct DESC;

-- ── 11. ACTIVE CASES TREND (DERIVED) ─────────────────────

SELECT
    country,
    report_date,
    confirmed,
    deaths,
    recovered,
    (confirmed - deaths - recovered) AS active_cases_derived,
    active                            AS active_cases_reported,
    ABS((confirmed - deaths - recovered) - active) AS discrepancy
FROM covid_data
WHERE country IN ('India', 'US', 'Brazil')
  AND report_date >= '2021-01-01'
ORDER BY country, report_date;

-- ── 12. STORED PROCEDURE — COUNTRY REPORT ────────────────

DELIMITER $$

CREATE PROCEDURE GetCountryReport(IN p_country VARCHAR(100))
BEGIN
    -- Summary stats
    SELECT
        country,
        MAX(confirmed)   AS peak_confirmed,
        MAX(deaths)      AS peak_deaths,
        MAX(recovered)   AS peak_recovered,
        ROUND(MAX(deaths)    / NULLIF(MAX(confirmed), 0) * 100, 2) AS death_rate_pct,
        ROUND(MAX(recovered) / NULLIF(MAX(confirmed), 0) * 100, 2) AS recovery_rate_pct,
        MIN(report_date) AS first_case_date,
        MAX(report_date) AS latest_report_date
    FROM covid_data
    WHERE country = p_country;

    -- Monthly breakdown
    SELECT
        DATE_FORMAT(report_date, '%Y-%m') AS month,
        SUM(new_cases)  AS new_cases,
        SUM(new_deaths) AS new_deaths
    FROM covid_data
    WHERE country = p_country
    GROUP BY DATE_FORMAT(report_date, '%Y-%m')
    ORDER BY month;
END$$

DELIMITER ;

-- Usage:
-- CALL GetCountryReport('India');
-- CALL GetCountryReport('US');
