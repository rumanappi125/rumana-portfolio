# 🏦 Insurance Policy Churn & Retention Analysis | SQL + Power BI

## Project Overview

Conducted **customer churn and retention analysis** on policyholder data at **Max Life Insurance** using cohort modelling and segmentation techniques. Delivered actionable insights that contributed to a **12% improvement in policy renewal rates**.

**Tools:** SQL (Advanced), Power BI, Excel, Stored Procedures, CTEs  
**Domain:** Insurance / FinTech  
**Company:** Randstad → Client: Max Life Insurance  
**Dataset Size:** 10M+ rows

---

## 📊 Key Results

| Metric | Outcome |
|---|---|
| Policy Renewal Rate Improvement | +12% |
| Decision-Making Speed | +30% |
| Manual Reporting Effort Reduction | -40% |
| Data Processing Efficiency Gain | +10% |
| Dataset Size | 10M+ policyholder records |

---

## 🗂️ Dataset Schema

```sql
CREATE TABLE policyholders (
    policy_id        VARCHAR(20) PRIMARY KEY,
    customer_id      VARCHAR(20),
    policy_type      VARCHAR(50),   -- Term, ULIP, Endowment, Health
    premium_amount   DECIMAL(12,2),
    sum_assured      DECIMAL(15,2),
    start_date       DATE,
    maturity_date    DATE,
    renewal_date     DATE,
    status           VARCHAR(20),   -- Active, Lapsed, Surrendered, Matured
    agent_id         VARCHAR(20),
    region           VARCHAR(50),
    age_band         VARCHAR(20),   -- 18-25, 26-35, 36-45, 46-55, 55+
    tenure_years     INT,
    last_payment_date DATE,
    payment_mode     VARCHAR(20),   -- Monthly, Quarterly, Annual
    channel          VARCHAR(30)    -- Agent, Online, Bancassurance
);

CREATE TABLE renewal_history (
    renewal_id    VARCHAR(20) PRIMARY KEY,
    policy_id     VARCHAR(20),
    due_date      DATE,
    paid_date     DATE,
    amount_paid   DECIMAL(12,2),
    status        VARCHAR(20),   -- Renewed, Lapsed, Grace
    reminder_sent INT
);

CREATE TABLE agent_performance (
    agent_id       VARCHAR(20),
    month_year     VARCHAR(7),
    policies_sold  INT,
    renewals_done  INT,
    lapsed_count   INT,
    premium_collected DECIMAL(15,2),
    region         VARCHAR(50)
);
```

---

## 🔍 SQL Queries

### 1. Churn Rate Calculation by Policy Type

```sql
SELECT
    policy_type,
    COUNT(*)                                                AS total_policies,
    SUM(CASE WHEN status = 'Lapsed' THEN 1 ELSE 0 END)    AS lapsed_count,
    SUM(CASE WHEN status = 'Active' THEN 1 ELSE 0 END)    AS active_count,
    ROUND(SUM(CASE WHEN status = 'Lapsed' THEN 1 ELSE 0 END) 
          / COUNT(*) * 100, 2)                              AS churn_rate_pct,
    ROUND(AVG(premium_amount), 2)                          AS avg_premium,
    ROUND(SUM(CASE WHEN status = 'Lapsed' THEN premium_amount ELSE 0 END), 2) AS revenue_at_risk
FROM policyholders
GROUP BY policy_type
ORDER BY churn_rate_pct DESC;
```

### 2. Cohort Retention Analysis

```sql
WITH cohort_base AS (
    SELECT
        customer_id,
        DATE_FORMAT(start_date, '%Y-%m') AS cohort_month,
        start_date
    FROM policyholders
),
renewal_cohort AS (
    SELECT
        cb.customer_id,
        cb.cohort_month,
        TIMESTAMPDIFF(MONTH, cb.start_date, r.due_date) AS months_since_start,
        r.status AS renewal_status
    FROM cohort_base cb
    LEFT JOIN renewal_history r ON cb.customer_id = r.policy_id -- simplified join
),
cohort_size AS (
    SELECT cohort_month, COUNT(DISTINCT customer_id) AS cohort_count
    FROM cohort_base
    GROUP BY cohort_month
)
SELECT
    rc.cohort_month,
    cs.cohort_count,
    rc.months_since_start,
    COUNT(DISTINCT CASE WHEN rc.renewal_status = 'Renewed' THEN rc.customer_id END) AS retained_customers,
    ROUND(
        COUNT(DISTINCT CASE WHEN rc.renewal_status = 'Renewed' THEN rc.customer_id END)
        / cs.cohort_count * 100, 2
    ) AS retention_rate_pct
FROM renewal_cohort rc
JOIN cohort_size cs ON rc.cohort_month = cs.cohort_month
GROUP BY rc.cohort_month, cs.cohort_count, rc.months_since_start
ORDER BY rc.cohort_month, rc.months_since_start;
```

### 3. At-Risk Policy Identification (Upcoming Renewals)

```sql
WITH upcoming_renewals AS (
    SELECT
        p.policy_id,
        p.customer_id,
        p.policy_type,
        p.premium_amount,
        p.renewal_date,
        p.agent_id,
        p.region,
        p.age_band,
        p.payment_mode,
        DATEDIFF(p.renewal_date, CURDATE()) AS days_to_renewal,
        COUNT(rh.renewal_id) AS total_past_renewals,
        SUM(CASE WHEN rh.status = 'Lapsed' THEN 1 ELSE 0 END) AS past_lapses
    FROM policyholders p
    LEFT JOIN renewal_history rh ON p.policy_id = rh.policy_id
    WHERE p.renewal_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 90 DAY)
      AND p.status = 'Active'
    GROUP BY p.policy_id, p.customer_id, p.policy_type, p.premium_amount,
             p.renewal_date, p.agent_id, p.region, p.age_band, p.payment_mode
),
risk_scored AS (
    SELECT *,
        CASE
            WHEN past_lapses >= 2 AND days_to_renewal <= 30  THEN 'Critical'
            WHEN past_lapses >= 1 AND days_to_renewal <= 60  THEN 'High Risk'
            WHEN days_to_renewal <= 30                        THEN 'Medium Risk'
            ELSE 'Low Risk'
        END AS risk_category
    FROM upcoming_renewals
)
SELECT * FROM risk_scored
ORDER BY 
    FIELD(risk_category, 'Critical', 'High Risk', 'Medium Risk', 'Low Risk'),
    days_to_renewal;
```

### 4. Agent Performance Dashboard Query

```sql
SELECT
    a.agent_id,
    a.region,
    SUM(a.policies_sold)                                          AS total_policies_sold,
    SUM(a.renewals_done)                                          AS total_renewals,
    SUM(a.lapsed_count)                                           AS total_lapses,
    SUM(a.premium_collected)                                      AS total_premium,
    ROUND(SUM(a.renewals_done) / NULLIF(SUM(a.renewals_done) + SUM(a.lapsed_count), 0) * 100, 2) 
                                                                   AS renewal_success_rate,
    RANK() OVER (PARTITION BY a.region ORDER BY SUM(a.premium_collected) DESC) AS regional_rank
FROM agent_performance a
WHERE a.month_year >= DATE_FORMAT(DATE_SUB(CURDATE(), INTERVAL 6 MONTH), '%Y-%m')
GROUP BY a.agent_id, a.region
ORDER BY total_premium DESC;
```

### 5. Lapse Prediction Segmentation

```sql
WITH policy_features AS (
    SELECT
        p.policy_id,
        p.policy_type,
        p.premium_amount,
        p.tenure_years,
        p.age_band,
        p.payment_mode,
        p.channel,
        COUNT(rh.renewal_id)                                         AS total_renewals,
        SUM(CASE WHEN rh.status = 'Lapsed' THEN 1 ELSE 0 END)       AS lapse_count,
        SUM(CASE WHEN rh.status = 'Grace'  THEN 1 ELSE 0 END)       AS grace_count,
        MAX(CASE WHEN rh.status = 'Lapsed' THEN rh.due_date END)     AS last_lapse_date,
        ROUND(SUM(CASE WHEN rh.status = 'Lapsed' THEN 1 ELSE 0 END)
              / NULLIF(COUNT(rh.renewal_id), 0) * 100, 2)            AS historical_lapse_rate,
        p.status
    FROM policyholders p
    LEFT JOIN renewal_history rh ON p.policy_id = rh.policy_id
    GROUP BY p.policy_id, p.policy_type, p.premium_amount, p.tenure_years,
             p.age_band, p.payment_mode, p.channel, p.status
)
SELECT
    *,
    CASE
        WHEN historical_lapse_rate >= 50 AND tenure_years < 2  THEN 'Very High Lapse Risk'
        WHEN historical_lapse_rate >= 30                        THEN 'High Lapse Risk'
        WHEN grace_count >= 2                                   THEN 'Medium Lapse Risk'
        WHEN payment_mode = 'Monthly' AND premium_amount > 5000 THEN 'Monitor'
        ELSE 'Stable'
    END AS lapse_risk_segment
FROM policy_features
ORDER BY historical_lapse_rate DESC;
```

### 6. Automated MIS Report — Premium Collection Summary

```sql
-- Stored Procedure for auto-generating monthly MIS report
DELIMITER $$

CREATE PROCEDURE GenerateMISReport(IN report_month VARCHAR(7))
BEGIN
    -- Premium collection summary
    SELECT
        'Premium Collection Summary' AS report_section,
        policy_type,
        payment_mode,
        COUNT(*)                      AS policies_due,
        SUM(premium_amount)           AS expected_premium,
        SUM(CASE WHEN status = 'Active' THEN premium_amount ELSE 0 END) AS collected_premium,
        ROUND(
            SUM(CASE WHEN status = 'Active' THEN premium_amount ELSE 0 END)
            / NULLIF(SUM(premium_amount), 0) * 100, 2
        ) AS collection_efficiency_pct
    FROM policyholders
    WHERE DATE_FORMAT(renewal_date, '%Y-%m') = report_month
    GROUP BY policy_type, payment_mode
    ORDER BY policy_type, payment_mode;

    -- Lapse summary for the month
    SELECT
        'Lapse Summary' AS report_section,
        region,
        COUNT(*) AS lapsed_policies,
        SUM(premium_amount) AS premium_lost,
        ROUND(AVG(tenure_years), 1) AS avg_tenure_at_lapse
    FROM policyholders
    WHERE status = 'Lapsed'
      AND DATE_FORMAT(renewal_date, '%Y-%m') = report_month
    GROUP BY region
    ORDER BY premium_lost DESC;
END$$

DELIMITER ;

-- Call: CALL GenerateMISReport('2024-11');
```

---

## 💡 Interview Talking Points

- **Cohort Modelling:** Built month-of-acquisition cohorts and tracked 12-month retention curves — revealed that policies sold via Bancassurance had 18% higher retention than agent-sold
- **Risk Scoring:** Created a 4-tier lapse risk segmentation (Critical → Low) used by the retention team to prioritise outreach
- **Automation:** Stored procedure replaced a 3-hour manual Excel process with a 2-minute SQL call
- **Business Impact:** The 12% renewal improvement translated to ₹X crore in retained premium — framing SQL work in business terms is key in interviews
