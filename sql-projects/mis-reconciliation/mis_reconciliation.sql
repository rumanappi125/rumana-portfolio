-- ============================================================
-- Automated MIS Reporting & CRM/LMS Reconciliation
-- Analyst: Rumana Appi | Company: Physics Wallah, Noida
-- ============================================================

USE edtech_analytics;

-- ── 1. SCHEMA SETUP ──────────────────────────────────────

CREATE TABLE crm_enrollments (
    crm_id          VARCHAR(20) PRIMARY KEY,
    student_id      VARCHAR(20),
    name            VARCHAR(100),
    enrolled_course VARCHAR(50),
    enrollment_date DATE,
    fees_paid       DECIMAL(10,2),
    channel         VARCHAR(30),   -- Online, Offline, App
    counselor_id    VARCHAR(20)
);

CREATE TABLE lms_enrollments (
    lms_id          VARCHAR(20) PRIMARY KEY,
    student_id      VARCHAR(20),
    student_name    VARCHAR(100),
    course_id       VARCHAR(50),
    enroll_date     DATE,
    fee_charged     DECIMAL(10,2),
    access_granted  TINYINT DEFAULT 1,
    last_login      DATETIME
);

CREATE TABLE billing_transactions (
    txn_id          VARCHAR(20) PRIMARY KEY,
    student_id      VARCHAR(20),
    course_id       VARCHAR(50),
    amount_paid     DECIMAL(10,2),
    payment_date    DATE,
    payment_mode    VARCHAR(30),
    status          VARCHAR(20)    -- Completed, Failed, Refunded
);

CREATE TABLE recon_staging (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    student_id      VARCHAR(20),
    course_id       VARCHAR(50),
    discrepancy_type VARCHAR(100),
    system_a        VARCHAR(30),
    system_b        VARCHAR(30),
    run_date        DATE
);

CREATE TABLE reconciliation_log (
    log_id              INT AUTO_INCREMENT PRIMARY KEY,
    run_date            DATE,
    status              VARCHAR(20),
    records_processed   INT DEFAULT 0,
    notes               TEXT,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for join performance
CREATE INDEX idx_crm_student  ON crm_enrollments (student_id);
CREATE INDEX idx_lms_student  ON lms_enrollments (student_id);
CREATE INDEX idx_billing_student ON billing_transactions (student_id, course_id);

-- ── 2. ENROLLMENT DISCREPANCY DETECTION ───────────────────

-- CRM has enrollment, LMS does not (access not provisioned)
SELECT
    c.student_id,
    c.name,
    c.enrolled_course  AS course_id,
    c.enrollment_date,
    c.fees_paid,
    'CRM_ONLY - LMS Access Not Provisioned' AS issue
FROM crm_enrollments c
LEFT JOIN lms_enrollments l
    ON c.student_id = l.student_id
   AND c.enrolled_course = l.course_id
WHERE l.student_id IS NULL
  AND c.enrollment_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)

UNION ALL

-- LMS has enrollment, CRM does not (ghost enrollments)
SELECT
    l.student_id,
    l.student_name,
    l.course_id,
    l.enroll_date,
    l.fee_charged,
    'LMS_ONLY - No CRM Record (Ghost Enrollment)' AS issue
FROM lms_enrollments l
LEFT JOIN crm_enrollments c
    ON l.student_id = c.student_id
   AND l.course_id = c.enrolled_course
WHERE c.student_id IS NULL
  AND l.enroll_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
ORDER BY enrollment_date DESC;

-- ── 3. BILLING vs LMS RECONCILIATION ─────────────────────

WITH billing_agg AS (
    SELECT
        student_id,
        course_id,
        SUM(CASE WHEN status = 'Completed' THEN amount_paid ELSE 0 END) AS total_paid,
        SUM(CASE WHEN status = 'Refunded'  THEN amount_paid ELSE 0 END) AS total_refunded,
        COUNT(CASE WHEN status = 'Completed' THEN 1 END)                AS payment_count
    FROM billing_transactions
    GROUP BY student_id, course_id
),
net_billing AS (
    SELECT student_id, course_id,
           total_paid - total_refunded AS net_paid,
           total_paid, total_refunded, payment_count
    FROM billing_agg
)
SELECT
    nb.student_id,
    nb.course_id,
    nb.net_paid           AS amount_in_billing,
    l.fee_charged         AS amount_in_lms,
    nb.net_paid - l.fee_charged AS difference,
    ABS(nb.net_paid - l.fee_charged) AS abs_difference,
    CASE
        WHEN ABS(nb.net_paid - l.fee_charged) = 0   THEN '✅ Match'
        WHEN nb.net_paid > l.fee_charged              THEN '⚠️ Overbilled'
        WHEN nb.net_paid < l.fee_charged              THEN '⚠️ Underpaid'
        WHEN l.fee_charged IS NULL                    THEN '❌ No LMS Record'
    END AS status,
    nb.payment_count
FROM net_billing nb
LEFT JOIN lms_enrollments l
    ON nb.student_id = l.student_id
   AND nb.course_id = l.course_id
ORDER BY abs_difference DESC;

-- ── 4. STUDENT ENGAGEMENT KPI DASHBOARD ──────────────────

SELECT
    l.course_id,
    COUNT(DISTINCT l.student_id)                           AS enrolled_students,
    COUNT(DISTINCT CASE WHEN l.last_login >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
                        THEN l.student_id END)             AS active_last_7d,
    COUNT(DISTINCT CASE WHEN l.last_login >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
                        THEN l.student_id END)             AS active_last_30d,
    COUNT(DISTINCT CASE WHEN l.last_login < DATE_SUB(CURDATE(), INTERVAL 30 DAY)
                         OR l.last_login IS NULL
                        THEN l.student_id END)             AS dormant_students,
    ROUND(
        COUNT(DISTINCT CASE WHEN l.last_login >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
                            THEN l.student_id END)
        / COUNT(DISTINCT l.student_id) * 100, 2
    ) AS mau_rate_pct,
    ROUND(
        COUNT(DISTINCT CASE WHEN l.last_login >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
                            THEN l.student_id END)
        / COUNT(DISTINCT l.student_id) * 100, 2
    ) AS wau_rate_pct
FROM lms_enrollments l
GROUP BY l.course_id
ORDER BY enrolled_students DESC;

-- ── 5. WEEKLY MIS SUMMARY VIEW ────────────────────────────

CREATE OR REPLACE VIEW vw_weekly_mis_summary AS
SELECT
    DATE_FORMAT(b.payment_date, '%Y-%u') AS year_week,
    COUNT(DISTINCT b.student_id)          AS new_enrollments,
    SUM(CASE WHEN b.status='Completed' THEN b.amount_paid ELSE 0 END) AS gross_revenue,
    SUM(CASE WHEN b.status='Refunded'  THEN b.amount_paid ELSE 0 END) AS refunds,
    SUM(CASE WHEN b.status='Completed' THEN b.amount_paid ELSE 0 END)
    - SUM(CASE WHEN b.status='Refunded' THEN b.amount_paid ELSE 0 END) AS net_revenue,
    COUNT(DISTINCT b.course_id) AS courses_sold
FROM billing_transactions b
GROUP BY DATE_FORMAT(b.payment_date, '%Y-%u')
ORDER BY year_week DESC;

-- ── 6. AUTOMATED DAILY RECONCILIATION PROCEDURE ──────────

DELIMITER $$

CREATE PROCEDURE RunDailyReconciliation()
BEGIN
    DECLARE v_discrepancy_count INT DEFAULT 0;

    -- Log start
    INSERT INTO reconciliation_log (run_date, status, notes)
    VALUES (CURDATE(), 'Running', 'Daily recon started');

    -- Clear today's staging
    DELETE FROM recon_staging WHERE run_date = CURDATE();

    -- Insert enrollment mismatches
    INSERT INTO recon_staging (student_id, course_id, discrepancy_type, system_a, system_b, run_date)
    SELECT c.student_id, c.enrolled_course, 'Enrollment_CRM_Only', 'CRM', 'LMS', CURDATE()
    FROM crm_enrollments c
    LEFT JOIN lms_enrollments l ON c.student_id = l.student_id AND c.enrolled_course = l.course_id
    WHERE l.student_id IS NULL
      AND c.enrollment_date = CURDATE();

    -- Insert billing mismatches
    INSERT INTO recon_staging (student_id, course_id, discrepancy_type, system_a, system_b, run_date)
    SELECT b.student_id, b.course_id, 'Billing_Amount_Mismatch', 'Billing', 'LMS', CURDATE()
    FROM billing_transactions b
    JOIN lms_enrollments l ON b.student_id = l.student_id AND b.course_id = l.course_id
    WHERE b.status = 'Completed'
      AND ABS(b.amount_paid - l.fee_charged) > 1
      AND b.payment_date = CURDATE();

    -- Count discrepancies
    SELECT COUNT(*) INTO v_discrepancy_count
    FROM recon_staging
    WHERE run_date = CURDATE();

    -- Update log
    UPDATE reconciliation_log
    SET status = 'Completed',
        records_processed = v_discrepancy_count,
        notes = CONCAT('Completed. Discrepancies found: ', v_discrepancy_count)
    WHERE run_date = CURDATE() AND status = 'Running';

    -- Return summary
    SELECT * FROM recon_staging WHERE run_date = CURDATE();
END$$

DELIMITER ;

-- Schedule via SQL Agent / Event Scheduler:
-- CREATE EVENT daily_reconciliation
-- ON SCHEDULE EVERY 1 DAY STARTS '2024-01-01 06:00:00'
-- DO CALL RunDailyReconciliation();
