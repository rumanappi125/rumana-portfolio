-- ============================================================
-- Insurance Policy Churn & Retention Analysis
-- Analyst: Rumana Appi | Client: Max Life Insurance
-- Platform: MySQL / SQL Server
-- ============================================================

USE insurance_analytics;

-- ── 1. CHURN RATE BY POLICY TYPE ──────────────────────────

SELECT
    policy_type,
    COUNT(*)                                                             AS total_policies,
    SUM(CASE WHEN status = 'Lapsed'     THEN 1 ELSE 0 END)             AS lapsed,
    SUM(CASE WHEN status = 'Active'     THEN 1 ELSE 0 END)             AS active,
    SUM(CASE WHEN status = 'Surrendered'THEN 1 ELSE 0 END)             AS surrendered,
    ROUND(SUM(CASE WHEN status IN ('Lapsed','Surrendered') THEN 1 ELSE 0 END)
          / COUNT(*) * 100, 2)                                          AS churn_rate_pct,
    ROUND(AVG(premium_amount), 2)                                       AS avg_premium,
    ROUND(SUM(CASE WHEN status IN ('Lapsed','Surrendered')
              THEN premium_amount ELSE 0 END), 2)                      AS revenue_at_risk
FROM policyholders
GROUP BY policy_type
ORDER BY churn_rate_pct DESC;

-- ── 2. CHURN BY AGE BAND ──────────────────────────────────

SELECT
    age_band,
    COUNT(*)                                                             AS total,
    SUM(CASE WHEN status = 'Lapsed' THEN 1 ELSE 0 END)                 AS lapsed,
    ROUND(SUM(CASE WHEN status = 'Lapsed' THEN 1 ELSE 0 END)
          / COUNT(*) * 100, 2)                                          AS lapse_rate_pct,
    ROUND(AVG(premium_amount), 2)                                       AS avg_premium,
    ROUND(AVG(tenure_years), 1)                                         AS avg_tenure
FROM policyholders
GROUP BY age_band
ORDER BY lapse_rate_pct DESC;

-- ── 3. COHORT RETENTION ANALYSIS ──────────────────────────

WITH cohort_base AS (
    SELECT
        customer_id,
        MIN(start_date) AS first_policy_date,
        DATE_FORMAT(MIN(start_date), '%Y-%m') AS cohort_month
    FROM policyholders
    GROUP BY customer_id
),
cohort_activity AS (
    SELECT
        cb.customer_id,
        cb.cohort_month,
        TIMESTAMPDIFF(MONTH, cb.first_policy_date, p.renewal_date) AS period_number,
        p.status
    FROM cohort_base cb
    JOIN policyholders p ON cb.customer_id = p.customer_id
    WHERE TIMESTAMPDIFF(MONTH, cb.first_policy_date, p.renewal_date) >= 0
),
cohort_sizes AS (
    SELECT cohort_month, COUNT(DISTINCT customer_id) AS cohort_size
    FROM cohort_base
    GROUP BY cohort_month
)
SELECT
    ca.cohort_month,
    cs.cohort_size,
    ca.period_number,
    COUNT(DISTINCT CASE WHEN ca.status = 'Active' THEN ca.customer_id END) AS active_customers,
    ROUND(
        COUNT(DISTINCT CASE WHEN ca.status = 'Active' THEN ca.customer_id END)
        / cs.cohort_size * 100, 2
    ) AS retention_rate_pct
FROM cohort_activity ca
JOIN cohort_sizes cs ON ca.cohort_month = cs.cohort_month
GROUP BY ca.cohort_month, cs.cohort_size, ca.period_number
ORDER BY ca.cohort_month, ca.period_number;

-- ── 4. AT-RISK POLICY DASHBOARD ──────────────────────────

WITH renewal_stats AS (
    SELECT
        policy_id,
        COUNT(*)                                             AS total_renewals,
        SUM(CASE WHEN status = 'Lapsed' THEN 1 ELSE 0 END) AS lapse_count,
        SUM(CASE WHEN status = 'Grace'  THEN 1 ELSE 0 END) AS grace_count,
        MAX(CASE WHEN status = 'Lapsed' THEN due_date END)  AS last_lapse_date
    FROM renewal_history
    GROUP BY policy_id
)
SELECT
    p.policy_id,
    p.customer_id,
    p.policy_type,
    p.premium_amount,
    p.renewal_date,
    p.region,
    p.age_band,
    p.agent_id,
    DATEDIFF(p.renewal_date, CURDATE())   AS days_to_renewal,
    COALESCE(rs.lapse_count, 0)           AS past_lapses,
    COALESCE(rs.grace_count, 0)           AS grace_periods,
    CASE
        WHEN COALESCE(rs.lapse_count,0) >= 2
             AND DATEDIFF(p.renewal_date, CURDATE()) <= 30  THEN 'Critical'
        WHEN COALESCE(rs.lapse_count,0) >= 1
             AND DATEDIFF(p.renewal_date, CURDATE()) <= 60  THEN 'High Risk'
        WHEN DATEDIFF(p.renewal_date, CURDATE()) <= 30      THEN 'Medium Risk'
        ELSE 'Low Risk'
    END AS risk_category
FROM policyholders p
LEFT JOIN renewal_stats rs ON p.policy_id = rs.policy_id
WHERE p.renewal_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 90 DAY)
  AND p.status = 'Active'
ORDER BY
    FIELD(risk_category, 'Critical', 'High Risk', 'Medium Risk', 'Low Risk'),
    days_to_renewal;

-- ── 5. AGENT PERFORMANCE METRICS ──────────────────────────

SELECT
    a.agent_id,
    a.region,
    SUM(a.policies_sold)        AS total_sold,
    SUM(a.renewals_done)        AS total_renewed,
    SUM(a.lapsed_count)         AS total_lapsed,
    SUM(a.premium_collected)    AS total_premium,
    ROUND(
        SUM(a.renewals_done) /
        NULLIF(SUM(a.renewals_done) + SUM(a.lapsed_count), 0) * 100, 2
    ) AS renewal_success_rate,
    RANK() OVER (PARTITION BY a.region ORDER BY SUM(a.premium_collected) DESC) AS regional_rank,
    RANK() OVER (ORDER BY SUM(a.premium_collected) DESC) AS overall_rank
FROM agent_performance a
WHERE a.month_year >= DATE_FORMAT(DATE_SUB(CURDATE(), INTERVAL 6 MONTH), '%Y-%m')
GROUP BY a.agent_id, a.region
ORDER BY total_premium DESC;

-- ── 6. POLICY RENEWAL TREND (MoM) ────────────────────────

SELECT
    DATE_FORMAT(due_date, '%Y-%m')           AS month,
    COUNT(*)                                  AS total_due,
    SUM(CASE WHEN status = 'Renewed' THEN 1 ELSE 0 END) AS renewed,
    SUM(CASE WHEN status = 'Lapsed'  THEN 1 ELSE 0 END) AS lapsed,
    SUM(CASE WHEN status = 'Grace'   THEN 1 ELSE 0 END) AS in_grace,
    ROUND(
        SUM(CASE WHEN status = 'Renewed' THEN 1 ELSE 0 END)
        / COUNT(*) * 100, 2
    ) AS renewal_rate_pct,
    LAG(ROUND(SUM(CASE WHEN status='Renewed' THEN 1 ELSE 0 END)/COUNT(*)*100,2))
        OVER (ORDER BY DATE_FORMAT(due_date,'%Y-%m')) AS prev_month_rate,
    ROUND(
        SUM(CASE WHEN status='Renewed' THEN 1 ELSE 0 END)/COUNT(*)*100 -
        LAG(SUM(CASE WHEN status='Renewed' THEN 1 ELSE 0 END)/COUNT(*)*100)
            OVER (ORDER BY DATE_FORMAT(due_date,'%Y-%m')), 2
    ) AS mom_change_pp
FROM renewal_history
GROUP BY DATE_FORMAT(due_date, '%Y-%m')
ORDER BY month;

-- ── 7. LAPSE RISK SEGMENTATION ────────────────────────────

WITH lapse_features AS (
    SELECT
        p.policy_id,
        p.policy_type,
        p.premium_amount,
        p.tenure_years,
        p.age_band,
        p.payment_mode,
        p.channel,
        p.status,
        COUNT(rh.renewal_id)                                             AS renewals_total,
        SUM(CASE WHEN rh.status = 'Lapsed' THEN 1 ELSE 0 END)          AS lapse_count,
        SUM(CASE WHEN rh.status = 'Grace'  THEN 1 ELSE 0 END)          AS grace_count,
        ROUND(
            SUM(CASE WHEN rh.status = 'Lapsed' THEN 1 ELSE 0 END)
            / NULLIF(COUNT(rh.renewal_id), 0) * 100, 2
        ) AS hist_lapse_rate
    FROM policyholders p
    LEFT JOIN renewal_history rh ON p.policy_id = rh.policy_id
    GROUP BY p.policy_id, p.policy_type, p.premium_amount, p.tenure_years,
             p.age_band, p.payment_mode, p.channel, p.status
)
SELECT
    *,
    CASE
        WHEN hist_lapse_rate >= 50 AND tenure_years <= 2  THEN 'Very High'
        WHEN hist_lapse_rate >= 30                         THEN 'High'
        WHEN grace_count >= 2                              THEN 'Medium'
        WHEN payment_mode = 'Monthly' AND premium_amount > 10000 THEN 'Watch'
        ELSE 'Low'
    END AS lapse_risk_band
FROM lapse_features
ORDER BY hist_lapse_rate DESC;

-- ── 8. AUTOMATED MIS STORED PROCEDURE ────────────────────

DELIMITER $$

CREATE PROCEDURE GenerateMISReport(IN p_month VARCHAR(7))
BEGIN
    SELECT 'Premium Collection' AS section,
        policy_type, payment_mode,
        COUNT(*) AS policies_due,
        ROUND(SUM(premium_amount),2) AS expected_premium,
        ROUND(SUM(CASE WHEN status='Active' THEN premium_amount ELSE 0 END),2) AS collected,
        ROUND(SUM(CASE WHEN status='Active' THEN premium_amount ELSE 0 END)
              / NULLIF(SUM(premium_amount),0)*100,2) AS efficiency_pct
    FROM policyholders
    WHERE DATE_FORMAT(renewal_date,'%Y-%m') = p_month
    GROUP BY policy_type, payment_mode;

    SELECT 'Lapse Summary' AS section,
        region,
        COUNT(*) AS lapsed_count,
        ROUND(SUM(premium_amount),2) AS premium_lost,
        ROUND(AVG(tenure_years),1) AS avg_tenure
    FROM policyholders
    WHERE status='Lapsed'
      AND DATE_FORMAT(renewal_date,'%Y-%m') = p_month
    GROUP BY region ORDER BY premium_lost DESC;

    SELECT 'Agent Leaderboard' AS section,
        agent_id, region,
        SUM(renewals_done) AS renewals,
        ROUND(SUM(premium_collected),2) AS premium
    FROM agent_performance
    WHERE month_year = p_month
    GROUP BY agent_id, region
    ORDER BY premium DESC LIMIT 10;
END$$

DELIMITER ;
