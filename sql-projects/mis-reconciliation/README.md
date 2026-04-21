# 🔄 Automated MIS Reporting & CRM/LMS Reconciliation | SQL

## Project Overview

Built and maintained **automated data reconciliation workflows** between CRM, LMS, and billing systems at **Physics Wallah**. Eliminated data discrepancies across systems and saved **6+ hours of manual effort weekly**.

**Tools:** SQL Server, MySQL, Excel, Stored Procedures, Views  
**Domain:** EdTech  
**Company:** PW — Physics Wallah, Noida

---

## 📊 Key Results

| Metric | Outcome |
|---|---|
| Manual Effort Saved | 6+ hours/week |
| Data Discrepancies | Eliminated |
| Processing Time Reduction | -20% |
| Efficiency Improvement | +20% |
| Dashboards Built | 20+ |

---

## 🔍 SQL Queries

### 1. Cross-System Data Reconciliation

```sql
-- Find records present in CRM but missing from LMS
SELECT
    c.student_id,
    c.name,
    c.enrolled_course,
    c.enrollment_date,
    'In CRM, Missing from LMS' AS discrepancy_type
FROM crm_enrollments c
LEFT JOIN lms_enrollments l ON c.student_id = l.student_id
                             AND c.enrolled_course = l.course_id
WHERE l.student_id IS NULL

UNION ALL

-- Find records in LMS but missing from CRM
SELECT
    l.student_id,
    l.student_name,
    l.course_id,
    l.enroll_date,
    'In LMS, Missing from CRM' AS discrepancy_type
FROM lms_enrollments l
LEFT JOIN crm_enrollments c ON l.student_id = c.student_id
                             AND l.course_id = c.enrolled_course
WHERE c.student_id IS NULL;
```

### 2. Billing vs LMS Revenue Reconciliation

```sql
WITH billing_summary AS (
    SELECT student_id, course_id,
           SUM(amount_paid) AS total_billed,
           COUNT(*) AS payment_count
    FROM billing_transactions
    WHERE status = 'Completed'
    GROUP BY student_id, course_id
),
lms_summary AS (
    SELECT student_id, course_id,
           fee_charged AS total_lms_fee,
           access_granted
    FROM lms_enrollments
)
SELECT
    b.student_id,
    b.course_id,
    b.total_billed,
    l.total_lms_fee,
    ABS(b.total_billed - l.total_lms_fee) AS discrepancy_amount,
    CASE
        WHEN b.total_billed > l.total_lms_fee THEN 'Overbilled'
        WHEN b.total_billed < l.total_lms_fee THEN 'Underbilled'
        ELSE 'Match'
    END AS reconciliation_status
FROM billing_summary b
JOIN lms_summary l ON b.student_id = l.student_id
                   AND b.course_id = l.course_id
WHERE ABS(b.total_billed - l.total_lms_fee) > 0
ORDER BY discrepancy_amount DESC;
```

### 3. Daily Automated Reconciliation Procedure

```sql
DELIMITER $$

CREATE PROCEDURE RunDailyReconciliation()
BEGIN
    -- Log start
    INSERT INTO reconciliation_log (run_date, status, notes)
    VALUES (CURDATE(), 'Running', 'Daily reconciliation started');

    -- Clear previous day staging
    TRUNCATE TABLE recon_staging;

    -- Insert discrepancies into staging
    INSERT INTO recon_staging (student_id, course_id, discrepancy_type, system_a, system_b, run_date)
    SELECT c.student_id, c.enrolled_course,
           'Enrollment Mismatch', 'CRM', 'LMS', CURDATE()
    FROM crm_enrollments c
    LEFT JOIN lms_enrollments l ON c.student_id = l.student_id
    WHERE l.student_id IS NULL AND c.enrollment_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY);

    -- Update log
    UPDATE reconciliation_log
    SET status = 'Completed',
        records_processed = (SELECT COUNT(*) FROM recon_staging WHERE run_date = CURDATE()),
        notes = CONCAT('Completed: ', (SELECT COUNT(*) FROM recon_staging WHERE run_date = CURDATE()), ' discrepancies found')
    WHERE run_date = CURDATE();
END$$

DELIMITER ;
```

---

## 💡 Interview Talking Points

- **System Integration:** Reconciled 3 disparate systems (CRM, LMS, Billing) with no shared primary key — used composite keys (student_id + course_id + date)
- **Automation ROI:** Replaced a daily 2-hour manual Excel VLOOKUP process with a stored procedure running on a scheduled SQL Agent job
- **Data Quality:** Reduced weekly discrepancy count from ~200 to near-zero within 3 months of implementation
