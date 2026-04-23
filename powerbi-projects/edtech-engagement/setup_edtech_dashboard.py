"""
EdTech Student Engagement Dashboard — Complete Setup Script
Analyst: Rumana Appi | Company: Physics Wallah (PW), Noida
Generates sample data + full Power BI PBIP project structure.
Run: python setup_edtech_dashboard.py
"""

import json, os, uuid, math
import pandas as pd
import numpy as np
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

np.random.seed(42)
BASE   = os.path.dirname(os.path.abspath(__file__))
DATA   = os.path.join(BASE, "data")
SM_DIR = os.path.join(BASE, "EdTech-Dashboard.SemanticModel")
RP_DIR = os.path.join(BASE, "EdTech-Dashboard.Report")

# ── CONSTANTS ─────────────────────────────────────────────────────────────────

COURSES = [
    # id, name, subject, grade_level, difficulty, total_videos, total_hrs, instructor
    ('PH01','Physics Foundation',     'Physics',     '9-10',  'Foundation',  120, 60,  'Dr. Alakh Pandey'),
    ('PH02','Physics Standard',       'Physics',     '11-12', 'Standard',    180, 90,  'Dr. Alakh Pandey'),
    ('PH03','Physics JEE Advanced',   'Physics',     '12+',   'Advanced',    240, 140, 'Dr. Alakh Pandey'),
    ('CH01','Chemistry Foundation',   'Chemistry',   '9-10',  'Foundation',  100, 55,  'Dr. Sachin Singh'),
    ('CH02','Chemistry Standard',     'Chemistry',   '11-12', 'Standard',    160, 85,  'Dr. Sachin Singh'),
    ('CH03','Chemistry JEE Advanced', 'Chemistry',   '12+',   'Advanced',    210, 130, 'Dr. Sachin Singh'),
    ('MA01','Mathematics Foundation', 'Mathematics', '9-10',  'Foundation',  130, 70,  'Vinay Sir'),
    ('MA02','Mathematics Standard',   'Mathematics', '11-12', 'Standard',    190, 100, 'Vinay Sir'),
    ('MA03','Mathematics JEE Advanced','Mathematics','12+',   'Advanced',    260, 150, 'Vinay Sir'),
    ('BI01','Biology Foundation',     'Biology',     '9-10',  'Foundation',  110, 58,  'Dr. Anita Gupta'),
    ('BI02','Biology NEET Prep',      'Biology',     '11-12', 'Standard',    200, 110, 'Dr. Anita Gupta'),
    ('BI03','Biology Advanced NEET',  'Biology',     '12+',   'Advanced',    230, 135, 'Dr. Anita Gupta'),
    ('CS01','Programming Basics',     'Computer Science','9-10','Foundation', 80,  40,  'Saurabh Sir'),
    ('CS02','Data Structures',        'Computer Science','11-12','Standard',  120, 65,  'Saurabh Sir'),
    ('CS03','Web Development',        'Computer Science','12+', 'Advanced',   100, 55,  'Saurabh Sir'),
]

STATES = [
    ('MH','Maharashtra'),('UP','Uttar Pradesh'),('BR','Bihar'),
    ('TN','Tamil Nadu'),('KA','Karnataka'),('WB','West Bengal'),
    ('RJ','Rajasthan'),('GJ','Gujarat'),('MP','Madhya Pradesh'),('DL','Delhi'),
]

GRADES       = ['Grade 9','Grade 10','Grade 11','Grade 12']
CITY_TIERS   = ['Tier 1','Tier 2','Tier 3']
SUBSCRIPTIONS= ['Free','Basic','Premium']
GENDERS      = ['Male','Female','Other']
CONTENT_TYPES= ['Video Lecture','Live Class','Practice Quiz','Study Notes','Mock Test']

N_STUDENTS = 10000
START_DATE = date(2023, 1, 1)
END_DATE   = date(2024, 12, 31)

# Subject engagement profiles: (completion_rate, avg_score, dropout_risk)
SUBJECT_PROFILE = {
    'Physics':          (0.42, 68, 0.35),
    'Chemistry':        (0.48, 71, 0.30),
    'Mathematics':      (0.38, 65, 0.40),
    'Biology':          (0.55, 74, 0.25),
    'Computer Science': (0.62, 78, 0.20),
}

# Subscription engagement multipliers
SUB_MULT = {'Free': 0.55, 'Basic': 0.85, 'Premium': 1.20}

# ── DATA GENERATION ───────────────────────────────────────────────────────────

def gen_dim_date():
    rows = []
    d = START_DATE
    while d <= END_DATE:
        rows.append({
            'date':        d.strftime('%Y-%m-%d'),
            'year':        d.year,
            'month_num':   d.month,
            'month_name':  d.strftime('%B'),
            'month_short': d.strftime('%b'),
            'quarter':     (d.month-1)//3+1,
            'week_num':    d.isocalendar()[1],
            'day_of_week': d.strftime('%A'),
            'is_weekend':  d.weekday()>=5,
            'year_month':  d.strftime('%Y-%m'),
            'academic_year': f"AY{d.year}-{str(d.year+1)[-2:]}" if d.month>=6 else f"AY{d.year-1}-{str(d.year)[-2:]}"
        })
        d += timedelta(days=1)
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(DATA,'dim_date.csv'), index=False)
    print(f"  dim_date.csv            — {len(df):,} rows")

def gen_dim_courses():
    rows = []
    for cid,cn,sub,gl,diff,tv,th,inst in COURSES:
        comp_r, avg_sc, dropout = SUBJECT_PROFILE[sub]
        rows.append({
            'course_id':      cid, 'course_name': cn, 'subject': sub,
            'grade_level':    gl,  'difficulty':  diff,
            'total_videos':   tv,  'total_hours': th,
            'instructor':     inst,
            'target_completion_rate': round(comp_r, 2),
            'avg_score_benchmark':    round(avg_sc, 1),
        })
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(DATA,'dim_courses.csv'), index=False)
    print(f"  dim_courses.csv         — {len(df):,} rows")

def gen_dim_students():
    rows = []
    for i in range(1, N_STUDENTS+1):
        state_code, state_name = STATES[i % len(STATES)]
        tier  = np.random.choice(CITY_TIERS, p=[0.25,0.45,0.30])
        sub   = np.random.choice(SUBSCRIPTIONS,
                    p=[0.50,0.30,0.20] if tier=='Tier 3' else
                      [0.35,0.40,0.25] if tier=='Tier 2' else
                      [0.20,0.40,0.40])
        grade = np.random.choice(GRADES, p=[0.20,0.22,0.30,0.28])
        enroll_dt = START_DATE + timedelta(days=np.random.randint(0,365))
        rows.append({
            'student_id':        f"STU{i:06d}",
            'grade':             grade,
            'state_code':        state_code,
            'state_name':        state_name,
            'city_tier':         tier,
            'subscription_type': sub,
            'gender':            np.random.choice(GENDERS, p=[0.52,0.45,0.03]),
            'age_group':         '14-15' if grade in ['Grade 9','Grade 10'] else '16-18',
            'enrollment_cohort': enroll_dt.strftime('%Y-%m'),
            'is_jee_aspirant':   grade in ['Grade 11','Grade 12'] and np.random.random()<0.55,
            'is_neet_aspirant':  grade in ['Grade 11','Grade 12'] and np.random.random()<0.40,
        })
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(DATA,'dim_students.csv'), index=False)
    print(f"  dim_students.csv        — {len(df):,} rows")
    return df

def gen_fact_enrollment(students_df):
    rows = []
    course_map = {c[0]: c for c in COURSES}

    for _, stu in students_df.iterrows():
        # Each student enrolled in 1-3 courses
        n_courses = np.random.choice([1,2,3], p=[0.40,0.40,0.20])
        grade = stu['grade']
        sub   = stu['subscription_type']
        tier  = stu['city_tier']

        # Filter courses relevant to grade
        eligible = [c for c in COURSES if
                    (grade in ['Grade 9','Grade 10']  and c[3]=='9-10') or
                    (grade in ['Grade 11','Grade 12'] and c[3] in ['11-12','12+'])]
        if not eligible: eligible = COURSES[:5]

        selected = np.random.choice(len(eligible), min(n_courses, len(eligible)), replace=False)

        for idx in selected:
            c = eligible[idx]
            cid, cn, subj, gl, diff, tv, th, _ = c
            comp_r, avg_sc, dropout_r = SUBJECT_PROFILE[subj]

            sm = SUB_MULT[sub]
            tier_m = 1.15 if tier=='Tier 1' else 1.0 if tier=='Tier 2' else 0.85

            completion_pct = min(100, round(
                comp_r * sm * tier_m * np.random.uniform(0.5, 1.8) * 100, 1))
            is_completed  = completion_pct >= 80
            is_at_risk    = not is_completed and completion_pct < 30 and np.random.random() < dropout_r
            is_active     = not is_at_risk and np.random.random() < 0.65

            enroll_dt  = START_DATE + timedelta(days=np.random.randint(0,365))
            total_sess = int(max(1, tv * (completion_pct/100) * np.random.uniform(0.8,1.2)))
            watch_mins = int(th * 60 * (completion_pct/100) * np.random.uniform(0.7,1.1))
            avg_score  = round(min(100, avg_sc * sm * tier_m * np.random.uniform(0.7,1.2)), 1)
            fees       = (0 if sub=='Free' else np.random.choice([999,1499,2999]) if sub=='Basic'
                          else np.random.choice([3999,5999,9999]))

            rows.append({
                'student_id':      stu['student_id'],
                'course_id':       cid,
                'enrollment_date': enroll_dt.strftime('%Y-%m-%d'),
                'subscription_type': sub,
                'fees_paid':       fees,
                'completion_pct':  completion_pct,
                'total_sessions':  total_sess,
                'total_watch_mins':watch_mins,
                'avg_score_pct':   avg_score,
                'videos_watched':  int(tv * completion_pct/100),
                'quizzes_attempted':int(max(0, total_sess * 0.6 * np.random.uniform(0.5,1.5))),
                'last_active_date':(enroll_dt + timedelta(days=np.random.randint(1,365))).strftime('%Y-%m-%d'),
                'days_enrolled':   np.random.randint(7, 365),
                'is_completed':    is_completed,
                'is_active':       is_active,
                'is_at_risk':      is_at_risk,
                'drop_week':       0 if is_completed else np.random.choice([1,2,3,4,6,8,12],
                                   p=[0.15,0.20,0.18,0.15,0.12,0.10,0.10]),
            })

    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(DATA,'fact_enrollment.csv'), index=False)
    print(f"  fact_enrollment.csv     — {len(df):,} rows")

def gen_fact_weekly_engagement():
    rows = []
    weeks = pd.date_range(START_DATE, END_DATE, freq='W-MON')

    for cid, cn, subj, gl, diff, tv, th, _ in COURSES:
        comp_r, avg_sc, dropout_r = SUBJECT_PROFILE[subj]
        base_enrolled = np.random.randint(800, 3000)

        for i, week_start in enumerate(weeks):
            growth = 1.0 + 0.005 * i
            season = 1.0 + 0.3*math.sin(week_start.month * math.pi / 6)

            for tier in CITY_TIERS:
                tier_m = {'Tier 1':1.2,'Tier 2':1.0,'Tier 3':0.75}[tier]
                enrolled = int(base_enrolled * tier_m * growth * season * np.random.uniform(0.85,1.15) / 3)
                active   = int(enrolled * np.random.uniform(0.40, 0.70))
                sessions = int(active * np.random.uniform(2.5, 5.0))
                watch_m  = int(active * np.random.uniform(45, 150))
                videos   = int(active * np.random.uniform(1.5, 4.0))
                eng_score= round(np.random.uniform(40, 85) * tier_m, 1)

                rows.append({
                    'course_id':          cid,
                    'week_start_date':    week_start.strftime('%Y-%m-%d'),
                    'city_tier':          tier,
                    'enrolled_students':  enrolled,
                    'active_students':    active,
                    'new_enrollments':    int(enrolled * np.random.uniform(0.02, 0.08)),
                    'total_sessions':     sessions,
                    'total_watch_mins':   watch_m,
                    'videos_watched':     videos,
                    'quizzes_submitted':  int(sessions * np.random.uniform(0.3, 0.6)),
                    'avg_engagement_score': eng_score,
                    'dropouts_this_week': int(enrolled * dropout_r * np.random.uniform(0.01, 0.04)),
                })

    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(DATA,'fact_weekly_engagement.csv'), index=False)
    print(f"  fact_weekly_engagement.csv — {len(df):,} rows")

def gen_fact_assessments():
    rows = []
    months = pd.date_range(START_DATE, END_DATE, freq='MS')
    assessment_types = ['Chapter Quiz','Unit Test','Mock Exam','Full Syllabus Test']

    for cid, cn, subj, gl, diff, tv, th, _ in COURSES:
        comp_r, avg_sc, _ = SUBJECT_PROFILE[subj]

        for mdt in months:
            for atype in assessment_types:
                diff_m = {'Foundation':1.05,'Standard':0.97,'Advanced':0.88}[diff]
                attempted = np.random.randint(200, 2000)
                avg_score = round(min(98, avg_sc * diff_m * np.random.uniform(0.85,1.15)), 1)
                pass_rate = round(min(0.98, (avg_score/100)*1.2*np.random.uniform(0.8,1.1)), 2)

                rows.append({
                    'course_id':         cid,
                    'assessment_date':   mdt.strftime('%Y-%m-%d'),
                    'assessment_type':   atype,
                    'students_attempted':attempted,
                    'avg_score_pct':     avg_score,
                    'pass_rate':         pass_rate,
                    'top_scorers_pct':   round(np.random.uniform(0.05, 0.20), 2),
                    'avg_attempts':      round(np.random.uniform(1.2, 2.8), 1),
                    'avg_time_mins':     round(np.random.uniform(25, 90), 1),
                })

    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(DATA,'fact_assessments.csv'), index=False)
    print(f"  fact_assessments.csv    — {len(df):,} rows")

def gen_fact_content():
    rows = []
    for cid, cn, subj, gl, diff, tv, th, _ in COURSES:
        comp_r, avg_sc, _ = SUBJECT_PROFILE[subj]

        for ctype in CONTENT_TYPES:
            vol_m = {'Video Lecture':0.45,'Live Class':0.15,'Practice Quiz':0.20,
                     'Study Notes':0.12,'Mock Test':0.08}[ctype]
            pieces   = max(1, int(tv * vol_m))
            dur_mins = (th * 60 * vol_m / max(1, pieces)) if ctype in ['Video Lecture','Live Class'] else 15
            comp_pct = round(min(100, comp_r * 100 * np.random.uniform(0.8,1.3) *
                                 (1.1 if ctype=='Video Lecture' else 0.85)), 1)
            rating   = round(np.random.uniform(3.5, 4.8), 1)

            rows.append({
                'course_id':          cid,
                'content_type':       ctype,
                'pieces_count':       pieces,
                'avg_duration_mins':  round(dur_mins, 1),
                'total_duration_hrs': round(pieces * dur_mins / 60, 1),
                'avg_completion_pct': comp_pct,
                'avg_rating':         rating,
                'total_views':        int(pieces * np.random.randint(500,3000)),
            })

    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(DATA,'fact_content.csv'), index=False)
    print(f"  fact_content.csv        — {len(df):,} rows")

# ── PBIP BOILERPLATE ──────────────────────────────────────────────────────────

def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path,'w',encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def write_text(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path,'w',encoding='utf-8') as f:
        f.write(text)

def ltag(): return str(uuid.uuid4())

def csv_path(fname):
    return os.path.join(DATA, fname).replace('\\','\\\\')

def create_pbip_boilerplate():
    write_json(os.path.join(BASE,'EdTech-Dashboard.pbip'), {
        "$schema":"https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json",
        "version":"1.0",
        "artifacts":[{"report":{"path":"EdTech-Dashboard.Report"}}],
        "settings":{"enableAutoRecovery":True}
    })
    write_json(os.path.join(SM_DIR,'.platform'), {
        "$schema":"https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
        "metadata":{"type":"SemanticModel","displayName":"EdTech-Dashboard"},
        "config":{"version":"2.0","logicalId":str(uuid.uuid4())}
    })
    write_json(os.path.join(SM_DIR,'definition.pbism'), {
        "$schema":"https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json",
        "version":"4.2","settings":{}
    })
    write_json(os.path.join(RP_DIR,'.platform'), {
        "$schema":"https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
        "metadata":{"type":"Report","displayName":"EdTech-Dashboard"},
        "config":{"version":"2.0","logicalId":str(uuid.uuid4())}
    })
    write_json(os.path.join(RP_DIR,'definition.pbir'), {
        "$schema":"https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
        "version":"4.0",
        "datasetReference":{"byPath":{"path":"../EdTech-Dashboard.SemanticModel"}}
    })
    write_text(os.path.join(SM_DIR,'definition','cultures','en-US.tmdl'), 'cultureInfo en-US\n\n')
    write_text(os.path.join(SM_DIR,'definition','database.tmdl'), 'database\n\tcompatibilityLevel: 1600\n')
    print("  PBIP boilerplate files created")

# ── TMDL HELPERS ──────────────────────────────────────────────────────────────

def make_tmdl_col(name, dtype, sm='none'):
    fmt = '0' if dtype=='int64' else ('#,0.00' if dtype=='double' else
          ('0.0%;-0.0%;0.0%' if 'rate' in name.lower() or 'pct' in name.lower() else ''))
    lines = [f'\tcolumn {name}', f'\t\tdataType: {dtype}']
    if fmt: lines.append(f'\t\tformatString: {fmt}')
    lines += [f'\t\tlineageTag: {ltag()}', f'\t\tsummarizeBy: {sm}',
              f'\t\tsourceColumn: {name}', f'\t\tannotation SummarizationSetBy = Automatic']
    return '\n'.join(lines)

def make_tmdl_table(name, cols_def, csv_file, col_type_map):
    lines = [f'table {name}', f'\tlineageTag: {ltag()}', '']
    for c,dt,sm in cols_def:
        lines.append(make_tmdl_col(c,dt,sm))
        lines.append('')
    path   = csv_path(csv_file)
    n_cols = len(cols_def)
    tlist  = ', '.join([f'{{"{c}", {t}}}' for c,t in col_type_map])
    lines.append(
        f'\tpartition {name} = m\n'
        f'\t\tmode: import\n'
        f'\t\tsource =\n'
        f'\t\t\t\tlet\n'
        f'\t\t\t\t    Source = Csv.Document(File.Contents("{path}"),\n'
        f'\t\t\t\t        [Delimiter=",", Columns={n_cols}, Encoding=1252, QuoteStyle=QuoteStyle.None]),\n'
        f'\t\t\t\t    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),\n'
        f'\t\t\t\t    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers",{{{tlist}}})\n'
        f'\t\t\t\tin\n'
        f'\t\t\t\t    #"Changed Type"\n'
    )
    lines += ['\tannotation PBI_NavigationStepName = Navigation', '\tannotation PBI_ResultType = Table']
    return '\n'.join(lines) + '\n'

def create_tmdl_tables():
    tbl = os.path.join(SM_DIR,'definition','tables')

    write_text(os.path.join(tbl,'dim_date.tmdl'), make_tmdl_table('dim_date',
        [('date','dateTime','none'),('year','int64','none'),('month_num','int64','none'),
         ('month_name','string','none'),('month_short','string','none'),('quarter','int64','none'),
         ('week_num','int64','none'),('day_of_week','string','none'),('is_weekend','boolean','none'),
         ('year_month','string','none'),('academic_year','string','none')],
        'dim_date.csv',
        [('date','type date'),('year','Int64.Type'),('month_num','Int64.Type'),
         ('month_name','type text'),('month_short','type text'),('quarter','Int64.Type'),
         ('week_num','Int64.Type'),('day_of_week','type text'),('is_weekend','type logical'),
         ('year_month','type text'),('academic_year','type text')]
    ))

    write_text(os.path.join(tbl,'dim_courses.tmdl'), make_tmdl_table('dim_courses',
        [('course_id','string','none'),('course_name','string','none'),('subject','string','none'),
         ('grade_level','string','none'),('difficulty','string','none'),
         ('total_videos','int64','sum'),('total_hours','double','sum'),
         ('instructor','string','none'),('target_completion_rate','double','none'),
         ('avg_score_benchmark','double','none')],
        'dim_courses.csv',
        [('course_id','type text'),('course_name','type text'),('subject','type text'),
         ('grade_level','type text'),('difficulty','type text'),('total_videos','Int64.Type'),
         ('total_hours','type number'),('instructor','type text'),
         ('target_completion_rate','type number'),('avg_score_benchmark','type number')]
    ))

    write_text(os.path.join(tbl,'dim_students.tmdl'), make_tmdl_table('dim_students',
        [('student_id','string','none'),('grade','string','none'),
         ('state_code','string','none'),('state_name','string','none'),
         ('city_tier','string','none'),('subscription_type','string','none'),
         ('gender','string','none'),('age_group','string','none'),
         ('enrollment_cohort','string','none'),('is_jee_aspirant','boolean','none'),
         ('is_neet_aspirant','boolean','none')],
        'dim_students.csv',
        [('student_id','type text'),('grade','type text'),('state_code','type text'),
         ('state_name','type text'),('city_tier','type text'),('subscription_type','type text'),
         ('gender','type text'),('age_group','type text'),('enrollment_cohort','type text'),
         ('is_jee_aspirant','type logical'),('is_neet_aspirant','type logical')]
    ))

    write_text(os.path.join(tbl,'fact_enrollment.tmdl'), make_tmdl_table('fact_enrollment',
        [('student_id','string','none'),('course_id','string','none'),
         ('enrollment_date','dateTime','none'),('subscription_type','string','none'),
         ('fees_paid','int64','sum'),('completion_pct','double','average'),
         ('total_sessions','int64','sum'),('total_watch_mins','int64','sum'),
         ('avg_score_pct','double','average'),('videos_watched','int64','sum'),
         ('quizzes_attempted','int64','sum'),('last_active_date','dateTime','none'),
         ('days_enrolled','int64','average'),('is_completed','boolean','none'),
         ('is_active','boolean','none'),('is_at_risk','boolean','none'),
         ('drop_week','int64','none')],
        'fact_enrollment.csv',
        [('student_id','type text'),('course_id','type text'),('enrollment_date','type date'),
         ('subscription_type','type text'),('fees_paid','Int64.Type'),
         ('completion_pct','type number'),('total_sessions','Int64.Type'),
         ('total_watch_mins','Int64.Type'),('avg_score_pct','type number'),
         ('videos_watched','Int64.Type'),('quizzes_attempted','Int64.Type'),
         ('last_active_date','type date'),('days_enrolled','Int64.Type'),
         ('is_completed','type logical'),('is_active','type logical'),
         ('is_at_risk','type logical'),('drop_week','Int64.Type')]
    ))

    write_text(os.path.join(tbl,'fact_weekly_engagement.tmdl'), make_tmdl_table('fact_weekly_engagement',
        [('course_id','string','none'),('week_start_date','dateTime','none'),
         ('city_tier','string','none'),('enrolled_students','int64','sum'),
         ('active_students','int64','sum'),('new_enrollments','int64','sum'),
         ('total_sessions','int64','sum'),('total_watch_mins','int64','sum'),
         ('videos_watched','int64','sum'),('quizzes_submitted','int64','sum'),
         ('avg_engagement_score','double','average'),('dropouts_this_week','int64','sum')],
        'fact_weekly_engagement.csv',
        [('course_id','type text'),('week_start_date','type date'),('city_tier','type text'),
         ('enrolled_students','Int64.Type'),('active_students','Int64.Type'),
         ('new_enrollments','Int64.Type'),('total_sessions','Int64.Type'),
         ('total_watch_mins','Int64.Type'),('videos_watched','Int64.Type'),
         ('quizzes_submitted','Int64.Type'),('avg_engagement_score','type number'),
         ('dropouts_this_week','Int64.Type')]
    ))

    write_text(os.path.join(tbl,'fact_assessments.tmdl'), make_tmdl_table('fact_assessments',
        [('course_id','string','none'),('assessment_date','dateTime','none'),
         ('assessment_type','string','none'),('students_attempted','int64','sum'),
         ('avg_score_pct','double','average'),('pass_rate','double','average'),
         ('top_scorers_pct','double','average'),('avg_attempts','double','average'),
         ('avg_time_mins','double','average')],
        'fact_assessments.csv',
        [('course_id','type text'),('assessment_date','type date'),('assessment_type','type text'),
         ('students_attempted','Int64.Type'),('avg_score_pct','type number'),
         ('pass_rate','type number'),('top_scorers_pct','type number'),
         ('avg_attempts','type number'),('avg_time_mins','type number')]
    ))

    write_text(os.path.join(tbl,'fact_content.tmdl'), make_tmdl_table('fact_content',
        [('course_id','string','none'),('content_type','string','none'),
         ('pieces_count','int64','sum'),('avg_duration_mins','double','average'),
         ('total_duration_hrs','double','sum'),('avg_completion_pct','double','average'),
         ('avg_rating','double','average'),('total_views','int64','sum')],
        'fact_content.csv',
        [('course_id','type text'),('content_type','type text'),
         ('pieces_count','Int64.Type'),('avg_duration_mins','type number'),
         ('total_duration_hrs','type number'),('avg_completion_pct','type number'),
         ('avg_rating','type number'),('total_views','Int64.Type')]
    ))

    print("  TMDL table files created")

# ── MEASURES ──────────────────────────────────────────────────────────────────

MEASURES_TMDL = f'''table _Measures
\tlineageTag: {ltag()}

\tmeasure 'Total Students' = DISTINCTCOUNT(fact_enrollment[student_id])
\t\tlineageTag: {ltag()}
\t\tformatString: #,0

\tmeasure 'Total Enrollments' = COUNTROWS(fact_enrollment)
\t\tlineageTag: {ltag()}
\t\tformatString: #,0

\tmeasure 'Active Students' =
\t\t\tCALCULATE(DISTINCTCOUNT(fact_enrollment[student_id]),
\t\t\t    fact_enrollment[is_active] = TRUE())
\t\tlineageTag: {ltag()}
\t\tformatString: #,0

\tmeasure 'Completed Students' =
\t\t\tCALCULATE(DISTINCTCOUNT(fact_enrollment[student_id]),
\t\t\t    fact_enrollment[is_completed] = TRUE())
\t\tlineageTag: {ltag()}
\t\tformatString: #,0

\tmeasure 'At-Risk Students' =
\t\t\tCALCULATE(DISTINCTCOUNT(fact_enrollment[student_id]),
\t\t\t    fact_enrollment[is_at_risk] = TRUE())
\t\tlineageTag: {ltag()}
\t\tformatString: #,0

\tmeasure 'Course Completion Rate' =
\t\t\tDIVIDE([Completed Students], [Total Students], 0)
\t\tlineageTag: {ltag()}
\t\tformatString: 0.0%;-0.0%;0.0%

\tmeasure 'Active Rate' =
\t\t\tDIVIDE([Active Students], [Total Students], 0)
\t\tlineageTag: {ltag()}
\t\tformatString: 0.0%;-0.0%;0.0%

\tmeasure 'Drop-off Rate' =
\t\t\t1 - [Course Completion Rate]
\t\tlineageTag: {ltag()}
\t\tformatString: 0.0%;-0.0%;0.0%

\tmeasure 'Avg Completion %' = AVERAGE(fact_enrollment[completion_pct])
\t\tlineageTag: {ltag()}
\t\tformatString: 0.0

\tmeasure 'Avg Score %' = AVERAGE(fact_enrollment[avg_score_pct])
\t\tlineageTag: {ltag()}
\t\tformatString: 0.0

\tmeasure 'Avg Score (Assessments)' = AVERAGE(fact_assessments[avg_score_pct])
\t\tlineageTag: {ltag()}
\t\tformatString: 0.0

\tmeasure 'Pass Rate' = AVERAGE(fact_assessments[pass_rate])
\t\tlineageTag: {ltag()}
\t\tformatString: 0.0%;-0.0%;0.0%

\tmeasure 'Top Scorer Rate' = AVERAGE(fact_assessments[top_scorers_pct])
\t\tlineageTag: {ltag()}
\t\tformatString: 0.0%;-0.0%;0.0%

\tmeasure 'Avg Attempts' = AVERAGE(fact_assessments[avg_attempts])
\t\tlineageTag: {ltag()}
\t\tformatString: 0.0

\tmeasure 'Total Watch Hours' =
\t\t\tROUND(DIVIDE(SUM(fact_enrollment[total_watch_mins]), 60), 0)
\t\tlineageTag: {ltag()}
\t\tformatString: #,0

\tmeasure 'Avg Watch Hours per Student' =
\t\t\tROUND(DIVIDE([Total Watch Hours], [Total Students], 0), 1)
\t\tlineageTag: {ltag()}
\t\tformatString: #,0.0

\tmeasure 'Total Sessions' = SUM(fact_enrollment[total_sessions])
\t\tlineageTag: {ltag()}
\t\tformatString: #,0

\tmeasure 'Avg Sessions per Student' =
\t\t\tDIVIDE([Total Sessions], [Total Students], 0)
\t\tlineageTag: {ltag()}
\t\tformatString: 0.0

\tmeasure 'Total Videos Watched' = SUM(fact_enrollment[videos_watched])
\t\tlineageTag: {ltag()}
\t\tformatString: #,0

\tmeasure 'Videos per Student' =
\t\t\tDIVIDE([Total Videos Watched], [Total Students], 0)
\t\tlineageTag: {ltag()}
\t\tformatString: 0.0

\tmeasure 'Total Quizzes Attempted' = SUM(fact_enrollment[quizzes_attempted])
\t\tlineageTag: {ltag()}
\t\tformatString: #,0

\tmeasure 'Total Revenue (Lakhs)' =
\t\t\tROUND(DIVIDE(SUM(fact_enrollment[fees_paid]), 100000), 2)
\t\tlineageTag: {ltag()}
\t\tformatString: #,0.00

\tmeasure 'Weekly Active Students' = SUM(fact_weekly_engagement[active_students])
\t\tlineageTag: {ltag()}
\t\tformatString: #,0

\tmeasure 'Weekly New Enrollments' = SUM(fact_weekly_engagement[new_enrollments])
\t\tlineageTag: {ltag()}
\t\tformatString: #,0

\tmeasure 'Avg Engagement Score' = AVERAGE(fact_weekly_engagement[avg_engagement_score])
\t\tlineageTag: {ltag()}
\t\tformatString: 0.0

\tmeasure 'Total Dropouts' = SUM(fact_weekly_engagement[dropouts_this_week])
\t\tlineageTag: {ltag()}
\t\tformatString: #,0

\tmeasure 'Avg Content Completion %' = AVERAGE(fact_content[avg_completion_pct])
\t\tlineageTag: {ltag()}
\t\tformatString: 0.0%;-0.0%;0.0%

\tmeasure 'Total Content Hours' = SUM(fact_content[total_duration_hrs])
\t\tlineageTag: {ltag()}
\t\tformatString: #,0.0

\tmeasure 'Avg Content Rating' = AVERAGE(fact_content[avg_rating])
\t\tlineageTag: {ltag()}
\t\tformatString: 0.00

\tmeasure 'Total Content Views' = SUM(fact_content[total_views])
\t\tlineageTag: {ltag()}
\t\tformatString: #,0

\tmeasure 'JEE Aspirants' =
\t\t\tCALCULATE(COUNTROWS(dim_students), dim_students[is_jee_aspirant] = TRUE())
\t\tlineageTag: {ltag()}
\t\tformatString: #,0

\tmeasure 'NEET Aspirants' =
\t\t\tCALCULATE(COUNTROWS(dim_students), dim_students[is_neet_aspirant] = TRUE())
\t\tlineageTag: {ltag()}
\t\tformatString: #,0

\tpartition _Measures = calculated
\t\tmode: import
\t\tsource = ""

\tannotation PBI_ResultType = Table
'''

RELATIONSHIPS_TMDL = '''relationship rel_date_enrollment
\tfromColumn: fact_enrollment.enrollment_date
\ttoColumn: dim_date.date

relationship rel_date_engagement
\tfromColumn: fact_weekly_engagement.week_start_date
\ttoColumn: dim_date.date

relationship rel_date_assessment
\tfromColumn: fact_assessments.assessment_date
\ttoColumn: dim_date.date

relationship rel_course_enrollment
\tfromColumn: fact_enrollment.course_id
\ttoColumn: dim_courses.course_id

relationship rel_course_engagement
\tfromColumn: fact_weekly_engagement.course_id
\ttoColumn: dim_courses.course_id

relationship rel_course_assessment
\tfromColumn: fact_assessments.course_id
\ttoColumn: dim_courses.course_id

relationship rel_course_content
\tfromColumn: fact_content.course_id
\ttoColumn: dim_courses.course_id

relationship rel_student_enrollment
\tfromColumn: fact_enrollment.student_id
\ttoColumn: dim_students.student_id

'''

MODEL_TMDL = '''model Model
\tculture: en-US
\tdefaultPowerBIDataSourceVersion: powerBI_V3
\tsourceQueryCulture: en-IN
\tdataAccessOptions
\t\tlegacyRedirects
\t\treturnErrorValuesAsNull

annotation PBI_QueryOrder = ["_Measures","dim_date","dim_courses","dim_students","fact_enrollment","fact_weekly_engagement","fact_assessments","fact_content"]

annotation PBI_ProTooling = ["DevMode"]

ref table _Measures
ref table dim_date
ref table dim_courses
ref table dim_students
ref table fact_enrollment
ref table fact_weekly_engagement
ref table fact_assessments
ref table fact_content

ref cultureInfo en-US

'''

# ── EDTECH THEME ──────────────────────────────────────────────────────────────

EDTECH_THEME = {
    "name": "EdTechVibrant",
    "dataColors": ["#6C63FF","#FF6B6B","#4ECDC4","#FFD166","#06D6A0",
                   "#4D96FF","#FF9F1C","#C77DFF","#48CAE4","#F72585"],
    "foreground": "#F0EEFF",
    "foregroundNeutralSecondary": "#B0A8CC",
    "foregroundNeutralTertiary": "#7070A0",
    "background": "#0A0818",
    "backgroundLight": "#111230",
    "backgroundNeutral": "#1E1A4A",
    "tableAccent": "#6C63FF",
    "good": "#06D6A0",
    "neutral": "#FFD166",
    "bad": "#FF6B6B",
    "maximum": "#06D6A0",
    "center": "#FFD166",
    "minimum": "#FF6B6B",
    "null": "#7070A0",
    "hyperlink": "#6C63FF",
    "visitedHyperlink": "#C77DFF",
    "textClasses": {
        "callout":{"fontSize":28,"fontFace":"Segoe UI","color":"#6C63FF"},
        "title":  {"fontSize":13,"fontFace":"Segoe UI Semibold","color":"#F0EEFF"},
        "header": {"fontSize":12,"fontFace":"Segoe UI Semibold","color":"#B0A8CC"},
        "label":  {"fontSize":10,"fontFace":"Segoe UI","color":"#B0A8CC"}
    },
    "visualStyles": {
        "*": {"*": {
            "*": [{"wordWrap":True}],
            "background": [{"show":True,"color":{"solid":{"color":"#111230"}},"transparency":5}],
            "border": [{"show":True,"color":{"solid":{"color":"#1E1A4A"}},"radius":10,"width":1}],
            "title": [{"show":True,"fontColor":{"solid":{"color":"#B0A8CC"}},"fontSize":11,"fontFamily":"Segoe UI","titleWrap":True,"background":{"solid":{"color":"#0A0818"}}}],
            "lineStyles": [{"strokeWidth":2}],
            "plotArea": [{"transparency":100}],
            "categoryAxis": [{"gridlineStyle":"dotted","gridlineColor":{"solid":{"color":"#1E1A4A"}},"labelColor":{"solid":{"color":"#B0A8CC"}},"fontSize":10,"showAxisTitle":False}],
            "valueAxis": [{"gridlineStyle":"dotted","gridlineColor":{"solid":{"color":"#1E1A4A"}},"labelColor":{"solid":{"color":"#B0A8CC"}},"fontSize":10,"showAxisTitle":False}],
            "legend": [{"show":True,"labelColor":{"solid":{"color":"#B0A8CC"}},"fontSize":10}],
            "tooltip": [{"show":True,"background":{"solid":{"color":"#1E1A4A"}},"backgroundColor":{"solid":{"color":"#1E1A4A"}},"transparency":0,"fontColor":{"solid":{"color":"#FFFFFF"}},"labelColor":{"solid":{"color":"#6C63FF"}},"fontSize":12,"fontFamily":"Segoe UI"}],
            "outspacePane": [{"backgroundColor":{"solid":{"color":"#1E1A4A"}},"foregroundColor":{"solid":{"color":"#FFFFFF"}},"transparency":0,"border":True,"borderColor":{"solid":{"color":"#6C63FF"}}}]
        }},
        "card": {"*": {
            "background": [{"show":True,"color":{"solid":{"color":"#111230"}},"transparency":0}],
            "border": [{"show":True,"color":{"solid":{"color":"#1E1A4A"}},"radius":12,"width":1}],
            "title": [{"show":False}],
            "labels": [{"color":{"solid":{"color":"#6C63FF"}},"fontSize":28,"fontFamily":"Segoe UI","bold":True}],
            "categoryLabels": [{"show":True,"color":{"solid":{"color":"#B0A8CC"}},"fontSize":11}]
        }},
        "columnChart": {"*": {
            "background": [{"show":True,"color":{"solid":{"color":"#111230"}},"transparency":0}],
            "dataPoint": [{"fill":{"solid":{"color":"#6C63FF"}}}],
            "plotArea": [{"transparency":100}],
            "categoryAxis": [{"gridlineStyle":"none","labelColor":{"solid":{"color":"#B0A8CC"}},"fontSize":10}],
            "valueAxis": [{"gridlineStyle":"dotted","gridlineColor":{"solid":{"color":"#1E1A4A"}},"labelColor":{"solid":{"color":"#B0A8CC"}},"fontSize":10}]
        }},
        "barChart": {"*": {
            "background": [{"show":True,"color":{"solid":{"color":"#111230"}},"transparency":0}],
            "dataPoint": [{"fill":{"solid":{"color":"#4ECDC4"}}}],
            "plotArea": [{"transparency":100}],
            "categoryAxis": [{"gridlineStyle":"none","labelColor":{"solid":{"color":"#B0A8CC"}},"fontSize":10}],
            "valueAxis": [{"gridlineStyle":"dotted","gridlineColor":{"solid":{"color":"#1E1A4A"}},"labelColor":{"solid":{"color":"#B0A8CC"}},"fontSize":10}],
            "labels": [{"show":True,"color":{"solid":{"color":"#F0EEFF"}},"fontSize":9}]
        }},
        "lineChart": {"*": {
            "background": [{"show":True,"color":{"solid":{"color":"#111230"}},"transparency":0}],
            "dataPoint": [{"fill":{"solid":{"color":"#6C63FF"}}}],
            "lineStyles": [{"strokeWidth":3}],
            "markers": [{"show":True}],
            "plotArea": [{"transparency":100}],
            "categoryAxis": [{"gridlineStyle":"none","labelColor":{"solid":{"color":"#B0A8CC"}},"fontSize":10}],
            "valueAxis": [{"gridlineStyle":"dotted","gridlineColor":{"solid":{"color":"#1E1A4A"}},"labelColor":{"solid":{"color":"#B0A8CC"}},"fontSize":10}]
        }},
        "donutChart": {"*": {
            "background": [{"show":True,"color":{"solid":{"color":"#111230"}},"transparency":0}],
            "legend": [{"show":True,"labelColor":{"solid":{"color":"#B0A8CC"}},"fontSize":10,"position":"Bottom"}],
            "labels": [{"show":False}]
        }},
        "funnel": {"*": {
            "background": [{"show":True,"color":{"solid":{"color":"#111230"}},"transparency":0}],
            "labels": [{"show":True,"color":{"solid":{"color":"#F0EEFF"}},"fontSize":11}],
            "percentBarLabel": [{"show":True,"color":{"solid":{"color":"#B0A8CC"}},"fontSize":10}]
        }},
        "slicer": {"*": {
            "background": [{"show":True,"color":{"solid":{"color":"#111230"}},"transparency":0}],
            "border": [{"show":True,"color":{"solid":{"color":"#1E1A4A"}},"radius":8}],
            "title": [{"show":False}],
            "items": [{"fontColor":{"solid":{"color":"#F0EEFF"}},"background":{"solid":{"color":"#1A1640"}}}]
        }},
        "matrix": {"*": {
            "background": [{"show":True,"color":{"solid":{"color":"#111230"}},"transparency":0}],
            "border": [{"show":True,"color":{"solid":{"color":"#1E1A4A"}}}],
            "columnHeaders": [{"fontColor":{"solid":{"color":"#6C63FF"}},"backColor":{"solid":{"color":"#0A0818"}},"fontSize":11,"fontFamily":"Segoe UI Semibold","outline":"None"}],
            "rowHeaders": [{"fontColor":{"solid":{"color":"#F0EEFF"}},"backColor":{"solid":{"color":"#111230"}},"fontSize":10,"outline":"None"}],
            "values": [{"fontColor":{"solid":{"color":"#F0EEFF"}},"backColor":{"solid":{"color":"#111230"}},"fontSize":10,"outline":"None"}],
            "total": [{"fontColor":{"solid":{"color":"#6C63FF"}},"backColor":{"solid":{"color":"#0A0818"}},"fontSize":11}],
            "grid": [{"gridVertical":False,"gridHorizontal":True,"gridHorizontalColor":{"solid":{"color":"#1E1A4A"}},"rowPadding":6}]
        }},
        "textbox": {"*": {"background":[{"show":False}],"border":[{"show":False}]}}
    }
}

# ── REPORT FILES ──────────────────────────────────────────────────────────────

def create_report_files():
    theme_dir = os.path.join(RP_DIR,'StaticResources','SharedResources','BaseThemes')
    os.makedirs(theme_dir, exist_ok=True)

    CY_SRC = os.path.join(BASE,'..','product-funnel-dashboard',
                          'Product-Funnel-Dashboard.Report','StaticResources',
                          'SharedResources','BaseThemes','CY26SU04.json')
    if os.path.exists(CY_SRC):
        import shutil; shutil.copy(CY_SRC, os.path.join(theme_dir,'CY26SU04.json'))

    write_json(os.path.join(theme_dir,'EdTechVibrant.json'), EDTECH_THEME)

    write_json(os.path.join(RP_DIR,'definition','version.json'), {
        "$schema":"https://developer.microsoft.com/json-schemas/fabric/item/report/definition/versionMetadata/1.0.0/schema.json",
        "version":"2.0.0"
    })
    write_json(os.path.join(RP_DIR,'definition','report.json'), {
        "$schema":"https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/3.2.0/schema.json",
        "themeCollection": {"baseTheme": {
            "name":"EdTechVibrant",
            "reportVersionAtImport":{"visual":"2.8.0","report":"3.2.0","page":"2.3.1"},
            "type":"SharedResources"
        }},
        "objects": {"section":[{"properties":{"verticalAlignment":{"expr":{"Literal":{"Value":"'Top'"}}}}}]},
        "resourcePackages": [{"name":"SharedResources","type":"SharedResources","items":[
            {"name":"CY26SU04","path":"BaseThemes/CY26SU04.json","type":"BaseTheme"},
            {"name":"EdTechVibrant","path":"BaseThemes/EdTechVibrant.json","type":"BaseTheme"}
        ]}],
        "settings": {"useStylableVisualContainerHeader":True,"exportDataMode":"AllowSummarized",
                     "defaultDrillFilterOtherVisuals":True,"allowChangeFilterTypes":True,
                     "useEnhancedTooltips":True,"useDefaultAggregateDisplayName":True}
    })
    print("  Report theme + structure files created")

# ── VISUAL HELPERS ────────────────────────────────────────────────────────────

def m(n): return {"Measure":{"Expression":{"SourceRef":{"Entity":"_Measures"}},"Property":n}}
def col(e,p): return {"Column":{"Expression":{"SourceRef":{"Entity":e}},"Property":p}}
def col_agg(e,p,fn=5): return {"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Entity":e}},"Property":p}},"Function":fn}}
def proj(field,qref,active=True):
    p={"field":field,"queryRef":qref}
    if active: p["active"]=True
    return p

def card(vid,x,y,w,h,mn,tab=0):
    return {"id":vid,"position":{"x":x,"y":y,"z":0,"width":w,"height":h,"tabOrder":tab},
            "visual":{"visualType":"card","query":{"queryState":{"Values":{"projections":[proj(m(mn),f"_Measures.{mn}")]}}}}}

def bar_v(vid,x,y,w,h,ce,cp,ys,tab=0):
    return {"id":vid,"position":{"x":x,"y":y,"z":0,"width":w,"height":h,"tabOrder":tab},
            "visual":{"visualType":"barChart","query":{"queryState":{
                "Category":{"projections":[proj(col(ce,cp),f"{ce}.{cp}")]},
                "Y":{"projections":[proj(m(mn),f"_Measures.{mn}") for mn in ys]}}}}}

def col_v(vid,x,y,w,h,ce,cp,ys,tab=0):
    return {"id":vid,"position":{"x":x,"y":y,"z":0,"width":w,"height":h,"tabOrder":tab},
            "visual":{"visualType":"columnChart","query":{"queryState":{
                "Category":{"projections":[proj(col(ce,cp),f"{ce}.{cp}")]},
                "Y":{"projections":[proj(m(mn),f"_Measures.{mn}") for mn in ys]}}}}}

def line_v(vid,x,y,w,h,ce,cp,ys,tab=0):
    return {"id":vid,"position":{"x":x,"y":y,"z":0,"width":w,"height":h,"tabOrder":tab},
            "visual":{"visualType":"lineChart","query":{"queryState":{
                "Category":{"projections":[proj(col(ce,cp),f"{ce}.{cp}")]},
                "Y":{"projections":[proj(m(mn),f"_Measures.{mn}") for mn in ys]}}}}}

def donut_v(vid,x,y,w,h,ce,cp,yn,tab=0):
    return {"id":vid,"position":{"x":x,"y":y,"z":0,"width":w,"height":h,"tabOrder":tab},
            "visual":{"visualType":"donutChart","query":{"queryState":{
                "Category":{"projections":[proj(col(ce,cp),f"{ce}.{cp}")]},
                "Y":{"projections":[proj(m(yn),f"_Measures.{yn}")]}}}}}

def funnel_v(vid,x,y,w,h,ce,cp,tab=0):
    return {"id":vid,"position":{"x":x,"y":y,"z":0,"width":w,"height":h,"tabOrder":tab},
            "visual":{"visualType":"funnel","query":{"queryState":{
                "Category":{"projections":[proj(col(ce,cp),f"{ce}.{cp}")]},
                "Y":{"projections":[proj(col_agg(ce,"completion_pct",0),f"Sum({ce}.completion_pct)")]}}}}}

def matrix_v(vid,x,y,w,h,re,rp,ce,cp,vms,tab=0):
    return {"id":vid,"position":{"x":x,"y":y,"z":0,"width":w,"height":h,"tabOrder":tab},
            "visual":{"visualType":"matrix","query":{"queryState":{
                "Rows":{"projections":[proj(col(re,rp),f"{re}.{rp}")]},
                "Columns":{"projections":[proj(col(ce,cp),f"{ce}.{cp}")]},
                "Values":{"projections":[proj(m(mn),f"_Measures.{mn}") for mn in vms]}}}}}

def slicer_v(vid,x,y,w,h,entity,prop,tab=0):
    return {"id":vid,"position":{"x":x,"y":y,"z":0,"width":w,"height":h,"tabOrder":tab},
            "visual":{"visualType":"slicer",
                      "query":{"queryState":{"Values":{"projections":[proj(col(entity,prop),f"{entity}.{prop}")]}}},
                      "objects":{"data":[{"properties":{"mode":{"expr":{"Literal":{"Value":"'Dropdown'"}}}}}],
                                 "header":[{"properties":{"show":{"expr":{"Literal":{"Value":"true"}}},"fontColor":{"solid":{"color":{"expr":{"Literal":{"Value":"'#6C63FF'"}}}}}}}]}}}

def make_visual_json(v):
    return {"$schema":"https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/1.4.0/schema.json",
            "name":v["id"],"position":v["position"],"visual":v["visual"]}

# ── 5 PAGES ───────────────────────────────────────────────────────────────────

SL_Y, SL_H, SL_W = 628, 67, 238
SL_X = [10, 260, 510, 760, 1010]

PAGES = {
    "p1_executive":  ("Executive Summary",    "et01execsummary001"),
    "p2_engagement": ("Student Engagement",   "et02engagement0002"),
    "p3_performance":("Course Performance",   "et03performance003"),
    "p4_dropout":    ("Drop-off & Retention", "et04dropretention4"),
    "p5_content":    ("Content Analytics",    "et05contentanalyc5"),
}

def page_visuals():
    return {
        "p1_executive": [
            # KPI row
            card("e1c1", 20, 20,230, 90,"Total Students",           tab=0),
            card("e1c2",260, 20,230, 90,"Active Rate",              tab=1),
            card("e1c3",500, 20,230, 90,"Course Completion Rate",   tab=2),
            card("e1c4",740, 20,230, 90,"Avg Score %",              tab=3),
            card("e1c5",980, 20,280, 90,"Total Revenue (Lakhs)",    tab=4),
            # Enrollment trend by month
            line_v("e1ln", 20,120,820,280,"dim_date","year_month",["Total Enrollments","Weekly New Enrollments"],tab=5),
            # Subject distribution donut
            donut_v("e1dn",860,120,400,280,"dim_courses","subject","Total Students",tab=6),
            # Top courses by enrollment
            bar_v("e1br", 20,410,600,195,"dim_courses","course_name",["Total Enrollments"],tab=7),
            # Performance by city tier
            bar_v("e1tr",640,410,620,195,"dim_students","city_tier",["Course Completion Rate","Avg Score %"],tab=8),
            # Slicers
            slicer_v("e1sl1",SL_X[0],SL_Y,SL_W,SL_H,"dim_date","academic_year",tab=10),
            slicer_v("e1sl2",SL_X[1],SL_Y,SL_W,SL_H,"dim_date","month_short",tab=11),
            slicer_v("e1sl3",SL_X[2],SL_Y,SL_W,SL_H,"dim_courses","subject",tab=12),
            slicer_v("e1sl4",SL_X[3],SL_Y,SL_W,SL_H,"dim_students","grade",tab=13),
            slicer_v("e1sl5",SL_X[4],SL_Y,SL_W,SL_H,"dim_students","subscription_type",tab=14),
        ],

        "p2_engagement": [
            # KPI row
            card("e2c1", 20, 20,290, 90,"Weekly Active Students",  tab=0),
            card("e2c2",320, 20,290, 90,"Avg Engagement Score",    tab=1),
            card("e2c3",620, 20,290, 90,"Avg Sessions per Student",tab=2),
            card("e2c4",920, 20,340, 90,"Avg Watch Hours per Student",tab=3),
            # Weekly active trend
            line_v("e2ln", 20,120,820,280,"dim_date","year_month",["Weekly Active Students","Total Dropouts"],tab=4),
            # Engagement by city tier
            donut_v("e2dn",860,120,400,280,"dim_students","city_tier","Weekly Active Students",tab=5),
            # Sessions by grade
            col_v("e2gr", 20,410,400,195,"dim_students","grade",["Avg Sessions per Student"],tab=6),
            # Watch time by subject
            bar_v("e2wt",440,410,820,195,"dim_courses","subject",["Avg Watch Hours per Student","Total Watch Hours"],tab=7),
            # Slicers
            slicer_v("e2sl1",SL_X[0],SL_Y,SL_W,SL_H,"dim_date","academic_year",tab=10),
            slicer_v("e2sl2",SL_X[1],SL_Y,SL_W,SL_H,"dim_date","quarter",tab=11),
            slicer_v("e2sl3",SL_X[2],SL_Y,SL_W,SL_H,"dim_courses","subject",tab=12),
            slicer_v("e2sl4",SL_X[3],SL_Y,SL_W,SL_H,"dim_students","grade",tab=13),
            slicer_v("e2sl5",SL_X[4],SL_Y,SL_W,SL_H,"dim_students","city_tier",tab=14),
        ],

        "p3_performance": [
            # KPI row
            card("e3c1", 20, 20,290, 90,"Avg Score (Assessments)", tab=0),
            card("e3c2",320, 20,290, 90,"Pass Rate",               tab=1),
            card("e3c3",620, 20,290, 90,"Top Scorer Rate",         tab=2),
            card("e3c4",920, 20,340, 90,"Avg Attempts",            tab=3),
            # Score by subject bar
            bar_v("e3sb", 20,120,820,280,"dim_courses","subject",["Avg Score (Assessments)","Avg Score %"],tab=4),
            # Pass rate donut
            donut_v("e3dn",860,120,400,280,"dim_courses","difficulty","Pass Rate",tab=5),
            # Score trend line
            line_v("e3ln", 20,410,600,195,"dim_date","year_month",["Avg Score (Assessments)","Pass Rate"],tab=6),
            # Matrix: Course x Grade score
            matrix_v("e3mx",640,410,620,195,"dim_courses","subject","dim_students","grade",["Avg Score %"],tab=7),
            # Slicers
            slicer_v("e3sl1",SL_X[0],SL_Y,SL_W,SL_H,"dim_date","academic_year",tab=10),
            slicer_v("e3sl2",SL_X[1],SL_Y,SL_W,SL_H,"dim_courses","subject",tab=11),
            slicer_v("e3sl3",SL_X[2],SL_Y,SL_W,SL_H,"dim_students","grade",tab=12),
            slicer_v("e3sl4",SL_X[3],SL_Y,SL_W,SL_H,"fact_assessments","assessment_type",tab=13),
            slicer_v("e3sl5",SL_X[4],SL_Y,SL_W,SL_H,"dim_courses","difficulty",tab=14),
        ],

        "p4_dropout": [
            # KPI row
            card("e4c1", 20, 20,290, 90,"Course Completion Rate",  tab=0),
            card("e4c2",320, 20,290, 90,"Drop-off Rate",           tab=1),
            card("e4c3",620, 20,290, 90,"At-Risk Students",        tab=2),
            card("e4c4",920, 20,340, 90,"Completed Students",      tab=3),
            # Drop-off funnel by completion bracket
            funnel_v("e4fn", 20,120,480,340,"fact_enrollment","subscription_type",tab=4),
            # At-risk by subject bar
            bar_v("e4ar",520,120,740,340,"dim_courses","subject",["At-Risk Students","Drop-off Rate"],tab=5),
            # Drop-off week distribution
            col_v("e4dw", 20,470,600,140,"fact_enrollment","drop_week",["Total Enrollments"],tab=6),
            # Completion by subscription
            bar_v("e4sb",640,470,620,140,"dim_students","subscription_type",["Course Completion Rate","Active Rate"],tab=7),
            # Slicers
            slicer_v("e4sl1",SL_X[0],SL_Y,SL_W,SL_H,"dim_date","academic_year",tab=10),
            slicer_v("e4sl2",SL_X[1],SL_Y,SL_W,SL_H,"dim_courses","subject",tab=11),
            slicer_v("e4sl3",SL_X[2],SL_Y,SL_W,SL_H,"dim_students","grade",tab=12),
            slicer_v("e4sl4",SL_X[3],SL_Y,SL_W,SL_H,"dim_students","subscription_type",tab=13),
            slicer_v("e4sl5",SL_X[4],SL_Y,SL_W,SL_H,"dim_students","city_tier",tab=14),
        ],

        "p5_content": [
            # KPI row
            card("e5c1", 20, 20,290, 90,"Total Content Hours",     tab=0),
            card("e5c2",320, 20,290, 90,"Avg Content Completion %",tab=1),
            card("e5c3",620, 20,290, 90,"Total Content Views",     tab=2),
            card("e5c4",920, 20,340, 90,"Avg Content Rating",      tab=3),
            # Content completion by type
            bar_v("e5cb", 20,120,600,280,"fact_content","content_type",["Avg Content Completion %","Avg Content Rating"],tab=4),
            # Content type donut
            donut_v("e5dn",640,120,400,280,"fact_content","content_type","Total Content Views",tab=5),
            # Subject-wise content hours
            bar_v("e5sh", 20,410,820,195,"dim_courses","subject",["Total Content Hours","Avg Content Completion %"],tab=6),
            # Instructor effectiveness
            bar_v("e5it",860,410,400,195,"dim_courses","instructor",["Avg Content Completion %"],tab=7),
            # Slicers
            slicer_v("e5sl1",SL_X[0],SL_Y,SL_W,SL_H,"dim_date","academic_year",tab=10),
            slicer_v("e5sl2",SL_X[1],SL_Y,SL_W,SL_H,"dim_courses","subject",tab=11),
            slicer_v("e5sl3",SL_X[2],SL_Y,SL_W,SL_H,"fact_content","content_type",tab=12),
            slicer_v("e5sl4",SL_X[3],SL_Y,SL_W,SL_H,"dim_students","grade",tab=13),
            slicer_v("e5sl5",SL_X[4],SL_Y,SL_W,SL_H,"dim_courses","difficulty",tab=14),
        ],
    }

# ── WRITE PAGES ───────────────────────────────────────────────────────────────

def create_report_pages():
    pages_dir = os.path.join(RP_DIR,'definition','pages')
    visuals_map = page_visuals()
    page_order  = []

    for key,(display_name,pid) in PAGES.items():
        page_order.append(pid)
        page_folder = os.path.join(pages_dir, pid)
        os.makedirs(page_folder, exist_ok=True)

        write_json(os.path.join(page_folder,'page.json'), {
            "$schema":"https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json",
            "name":pid, "displayName":display_name,
            "displayOption":"FitToPage", "height":720, "width":1280
        })

        for v in visuals_map[key]:
            vis_folder = os.path.join(page_folder,'visuals',v["id"])
            os.makedirs(vis_folder, exist_ok=True)
            write_json(os.path.join(vis_folder,'visual.json'), make_visual_json(v))

        print(f"  Page: {display_name} ({len(visuals_map[key])} visuals)")

    write_json(os.path.join(pages_dir,'pages.json'), {
        "$schema":"https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.0.0/schema.json",
        "pageOrder": page_order, "activePageName": page_order[0]
    })

# ── MAIN ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    try:
        from dateutil.relativedelta import relativedelta
    except ImportError:
        os.system("pip install python-dateutil"); from dateutil.relativedelta import relativedelta

    os.makedirs(DATA, exist_ok=True)

    print("\n[1/5] Generating EdTech sample data...")
    gen_dim_date()
    gen_dim_courses()
    students_df = gen_dim_students()
    gen_fact_enrollment(students_df)
    gen_fact_weekly_engagement()
    gen_fact_assessments()
    gen_fact_content()

    print("\n[2/5] Creating PBIP boilerplate...")
    create_pbip_boilerplate()

    print("\n[3/5] Creating TMDL model files...")
    create_tmdl_tables()
    tbl_dir = os.path.join(SM_DIR,'definition','tables')
    write_text(os.path.join(tbl_dir,'_Measures.tmdl'), MEASURES_TMDL)
    write_text(os.path.join(SM_DIR,'definition','relationships.tmdl'), RELATIONSHIPS_TMDL)
    write_text(os.path.join(SM_DIR,'definition','model.tmdl'), MODEL_TMDL)
    print("  _Measures + relationships + model written")

    print("\n[4/5] Creating EdTechVibrant theme + report structure...")
    create_report_files()

    print("\n[5/5] Creating 5 report pages with visuals...")
    create_report_pages()

    print(f"\nDone! Open EdTech-Dashboard.pbip in Power BI Desktop.")
    print(f"Files at: {BASE}")
