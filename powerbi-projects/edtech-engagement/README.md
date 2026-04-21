# 🎓 EdTech Student Engagement Dashboard | Power BI + Qlik Sense

## Project Overview

Performed student engagement and course performance analysis across **50K+ learner records** at **Physics Wallah**. Identified drop-off patterns and enabled category managers to redesign content delivery, **improving course completion rates by 18%**.

**Tools:** Power BI, Qlik Sense, SQL Server, Excel  
**Domain:** EdTech  
**Company:** PW — Physics Wallah, Noida  
**Dataset:** 50,000+ student records across multiple courses

---

## 📊 Key Results

| Metric | Outcome |
|---|---|
| Course Completion Rate Improvement | +18% |
| Business Metrics Built | 20+ |
| Manual Effort Saved (Recon) | 6+ hrs/week |
| Processing Time Reduction | -20% |

---

## 📐 Dashboard Pages

### Page 1: Engagement Overview
- DAU / WAU / MAU by course and cohort
- Active vs Dormant student split
- Login frequency distribution

### Page 2: Course Performance
- Completion rate by course and subject
- Drop-off funnel (Enrolled → Started → 50% → Completed)
- Average time-to-completion

### Page 3: Drop-off Analysis
- Lessons/modules with highest drop-off rates
- Time-of-day / Day-of-week engagement heatmap
- Correlation between video length and completion

### Page 4: Category Manager View
- Course-by-course KPI scorecard
- NPS proxy (rating data)
- Content revision recommendations flagging

---

## 🗄️ SQL — Engagement Analysis

```sql
-- Student engagement segmentation (RFM-style)
WITH engagement_base AS (
    SELECT
        s.student_id,
        s.course_id,
        s.enrolled_date,
        MAX(l.login_date)                           AS last_active_date,
        COUNT(DISTINCT l.login_date)                AS total_active_days,
        SUM(l.session_duration_min)                 AS total_minutes_spent,
        COUNT(DISTINCT l.lesson_id)                 AS lessons_accessed,
        COUNT(DISTINCT CASE WHEN l.completed = 1
              THEN l.lesson_id END)                  AS lessons_completed,
        COUNT(DISTINCT c.course_id)                  AS total_lessons_in_course
    FROM student_enrollments s
    LEFT JOIN lms_activity l    ON s.student_id = l.student_id
                                AND s.course_id  = l.course_id
    LEFT JOIN course_content c  ON s.course_id   = c.course_id
    GROUP BY s.student_id, s.course_id, s.enrolled_date
),
completion_rates AS (
    SELECT *,
        ROUND(lessons_completed / NULLIF(total_lessons_in_course,0)*100,2) AS completion_pct,
        DATEDIFF(CURDATE(), last_active_date)                               AS days_since_active,
        DATEDIFF(CURDATE(), enrolled_date)                                  AS days_since_enrolled
    FROM engagement_base
)
SELECT
    *,
    CASE
        WHEN completion_pct >= 80                               THEN 'Completed'
        WHEN completion_pct >= 50 AND days_since_active <= 7   THEN 'On Track'
        WHEN completion_pct >= 50 AND days_since_active > 14   THEN 'Stalled - Mid Course'
        WHEN completion_pct < 50  AND days_since_active > 30   THEN 'At Risk - Dropout'
        WHEN total_active_days = 0                              THEN 'Never Started'
        ELSE 'Early Stage'
    END AS engagement_segment
FROM completion_rates
ORDER BY days_since_active DESC;

-- Lesson-level drop-off analysis
SELECT
    l.lesson_id,
    l.lesson_title,
    l.module_name,
    l.video_length_min,
    COUNT(DISTINCT a.student_id)                            AS students_who_started,
    COUNT(DISTINCT CASE WHEN a.completed = 1
          THEN a.student_id END)                            AS students_who_completed,
    ROUND(COUNT(DISTINCT CASE WHEN a.completed = 1 THEN a.student_id END)
          / NULLIF(COUNT(DISTINCT a.student_id),0)*100, 2) AS completion_rate_pct,
    ROUND(AVG(a.watch_time_min), 2)                        AS avg_watch_time_min,
    ROUND(AVG(a.watch_time_min)
          / NULLIF(l.video_length_min,0)*100, 2)           AS avg_watch_pct
FROM lessons l
LEFT JOIN lms_activity a ON l.lesson_id = a.lesson_id
GROUP BY l.lesson_id, l.lesson_title, l.module_name, l.video_length_min
ORDER BY completion_rate_pct ASC;
```

---

## 🔢 Key DAX Measures

```dax
-- Course Completion Rate
Completion_Rate =
    DIVIDE(
        CALCULATE(DISTINCTCOUNT(Students[student_id]),
                  Students[completion_pct] >= 80),
        DISTINCTCOUNT(Students[student_id]),
        0
    ) * 100

-- 30-Day Active Students
MAU =
    CALCULATE(
        DISTINCTCOUNT(Activity[student_id]),
        Activity[login_date] >= TODAY() - 30
    )

-- At-Risk Students (enrolled > 14 days, <30% complete)
At_Risk_Students =
    CALCULATE(
        DISTINCTCOUNT(Students[student_id]),
        Students[days_since_enrolled] > 14,
        Students[completion_pct] < 30
    )

-- Average Time to Complete (days)
Avg_Days_to_Complete =
    AVERAGEX(
        FILTER(Students, Students[completion_pct] >= 80),
        Students[days_to_complete]
    )
```

---

## 💡 Interview Talking Points

- **Drop-off Insight:** Analysis revealed 68% of dropouts happened within the first 3 lessons — led to redesigning onboarding lessons to be shorter (<8 mins) and more interactive
- **Content Impact:** Identified that lessons over 20 minutes had 40% lower completion rates — this was the single biggest factor in the 18% completion improvement
- **Segmentation:** The 5-tier engagement segmentation (Completed / On Track / Stalled / At Risk / Never Started) was adopted by category managers as their weekly review framework
- **Qlik Sense vs Power BI:** Used Qlik Sense for associative exploration of drop-off patterns (its strength), then Power BI for the final stakeholder dashboard (better sharing/scheduling)
