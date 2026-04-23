"""
NREGA Employment Analytics Dashboard — Complete Setup Script
Analyst: Rumana Appi
Generates sample data + full Power BI PBIP project structure.
Run: python setup_nrega_dashboard.py
"""

import json, os, uuid, math
import pandas as pd
import numpy as np
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

np.random.seed(42)
BASE   = os.path.dirname(os.path.abspath(__file__))
DATA   = os.path.join(BASE, "data")
SM_DIR = os.path.join(BASE, "NREGA-Dashboard.SemanticModel")
RP_DIR = os.path.join(BASE, "NREGA-Dashboard.Report")

# ── CONSTANTS ─────────────────────────────────────────────────────────────────

STATES = [
    # code, name, hindi, region,  notified_wage, sc%, st%, women%, demand_fulfil
    ('RJ','Rajasthan',       'राजस्थान',      'North',  255, .18,.12,.55,.92),
    ('UP','Uttar Pradesh',   'उत्तर प्रदेश', 'North',  230, .22,.08,.52,.78),
    ('WB','West Bengal',     'पश्चिम बंगाल', 'East',   236, .28,.06,.57,.88),
    ('MP','Madhya Pradesh',  'मध्य प्रदेश',  'Central',221, .20,.22,.54,.82),
    ('AP','Andhra Pradesh',  'आंध्र प्रदेश', 'South',  286, .22,.10,.56,.90),
    ('TN','Tamil Nadu',      'तमिलनाडु',     'South',  294, .20,.04,.54,.88),
    ('BR','Bihar',           'बिहार',         'East',   228, .18,.04,.50,.72),
    ('JH','Jharkhand',       'झारखंड',       'East',   237, .14,.38,.53,.80),
    ('OD','Odisha',          'ओडिशा',        'East',   237, .18,.28,.57,.85),
    ('CG','Chhattisgarh',    'छत्तीसगढ़',   'Central',221, .14,.42,.55,.86),
    ('MH','Maharashtra',     'महाराष्ट्र',  'West',   273, .12,.12,.52,.76),
    ('GJ','Gujarat',         'गुजरात',       'West',   254, .10,.16,.51,.82),
    ('KA','Karnataka',       'कर्नाटक',      'South',  316, .20,.08,.53,.84),
    ('TG','Telangana',       'तेलंगाना',     'South',  286, .20,.10,.54,.88),
    ('AS','Assam',           'असम',           'NE',     238, .08,.14,.52,.74),
]

DISTRICTS = {
    'RJ':['Barmer','Jaisalmer','Nagaur','Bikaner','Jodhpur'],
    'UP':['Sonbhadra','Mirzapur','Chitrakoot','Banda','Bahraich'],
    'WB':['Murshidabad','Purulia','Bankura','Birbhum','Malda'],
    'MP':['Sheopur','Tikamgarh','Panna','Satna','Mandla'],
    'AP':['Kurnool','Anantapur','Prakasam','Guntur','YSR Kadapa'],
    'TN':['Tirunelveli','Virudhunagar','Ramanathapuram','Dindigul','Madurai'],
    'BR':['Gaya','Nawada','Jamui','Araria','Sitamarhi'],
    'JH':['Gumla','Simdega','Lohardaga','Pakur','Dumka'],
    'OD':['Koraput','Kalahandi','Nuapada','Bolangir','Kandhamal'],
    'CG':['Bastar','Dantewada','Narayanpur','Bijapur','Sukma'],
    'MH':['Gadchiroli','Nandurbar','Dhule','Washim','Yavatmal'],
    'GJ':['Dahod','Panchmahal','Narmada','Tapi','Kutch'],
    'KA':['Yadgir','Raichur','Koppal','Bellary','Kalaburagi'],
    'TG':['Adilabad','Asifabad','Nirmal','Nizamabad','Karimnagar'],
    'AS':['Dhubri','Barpeta','Nalbari','Goalpara','Kokrajhar'],
}

WORK_CATEGORIES = [
    ('WC','Water Conservation','जल संरक्षण','Natural Resources'),
    ('RC','Rural Connectivity','ग्रामीण संपर्क','Infrastructure'),
    ('AG','Agriculture Support','कृषि सहायता','Agriculture'),
    ('LD','Land Development','भूमि विकास','Agriculture'),
    ('FL','Flood Control','बाढ़ नियंत्रण','Natural Resources'),
]

FINANCIAL_YEARS = ['FY2020','FY2021','FY2022','FY2023','FY2024']
FY_START = {'FY2020':date(2019,4,1),'FY2021':date(2020,4,1),
            'FY2022':date(2021,4,1),'FY2023':date(2022,4,1),'FY2024':date(2023,4,1)}

# YoY growth multipliers for realism
GROWTH = {'FY2020':1.0,'FY2021':0.85,'FY2022':1.10,'FY2023':1.18,'FY2024':1.22}

# ── DATA GENERATION ───────────────────────────────────────────────────────────

def gen_dim_date():
    rows = []
    d = date(2019,4,1)
    while d <= date(2024,3,31):
        fy_start_year = d.year if d.month >= 4 else d.year - 1
        fy = f"FY{fy_start_year+1}"
        fq_month = (d.month - 4) % 12
        fq = f"Q{fq_month // 3 + 1}"
        rows.append({
            'date': d.strftime('%Y-%m-%d'),
            'year': d.year, 'month_num': d.month,
            'month_name': d.strftime('%B'), 'month_short': d.strftime('%b'),
            'quarter': (d.month-1)//3+1,
            'financial_year': fy, 'financial_quarter': fq,
            'day_of_week': d.strftime('%A'), 'is_weekend': d.weekday()>=5,
            'year_month': d.strftime('%Y-%m'),
        })
        d += timedelta(days=1)
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(DATA,'dim_date.csv'), index=False)
    print(f"  dim_date.csv           — {len(df):,} rows")

def gen_dim_geography():
    rows = []
    for sc,sn,sh,region,*_ in STATES:
        for i,dn in enumerate(DISTRICTS[sc]):
            dc = f"{sc}_D{i+1:02d}"
            rows.append({'state_code':sc,'state_name':sn,'state_hindi':sh,
                         'district_code':dc,'district_name':dn,
                         'region':region,'zone':region})
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(DATA,'dim_geography.csv'), index=False)
    print(f"  dim_geography.csv      — {len(df):,} rows")

def gen_dim_work_category():
    rows = [{'category_id':cid,'category_name':cn,'category_hindi':ch,
             'major_category':mc} for cid,cn,ch,mc in WORK_CATEGORIES]
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(DATA,'dim_work_category.csv'), index=False)
    print(f"  dim_work_category.csv  — {len(df):,} rows")

def gen_fact_employment():
    rows = []
    state_map = {sc:(nw,scp,stp,wp,df) for sc,sn,sh,rg,nw,scp,stp,wp,df in STATES}
    for sc in state_map:
        nw,sc_p,st_p,w_p,df = state_map[sc]
        districts = DISTRICTS[sc]
        base_hh = np.random.randint(40000,120000)
        for fy in FINANCIAL_YEARS:
            g = GROWTH[fy]
            fy_start = FY_START[fy]
            for m in range(12):
                report_date = fy_start + relativedelta(months=m)
                season_mult = 1.0 + 0.4*math.sin((m+2)*math.pi/6)
                for i,dn in enumerate(districts):
                    dc = f"{sc}_D{i+1:02d}"
                    dist_var = np.random.uniform(0.7,1.3)
                    hh_jc = int(base_hh*dist_var*g)
                    hh_active_jc = int(hh_jc*np.random.uniform(0.75,0.90))
                    hh_demanded = int(hh_active_jc*np.random.uniform(0.40,0.70)*season_mult)
                    hh_employed = int(hh_demanded*df*np.random.uniform(0.90,1.0))
                    hh_100days = int(hh_employed*np.random.uniform(0.15,0.35))
                    pd_total = int(hh_employed*np.random.uniform(25,42)*season_mult)
                    pd_sc = int(pd_total*(sc_p+np.random.uniform(-0.03,0.03)))
                    pd_st = int(pd_total*(st_p+np.random.uniform(-0.03,0.03)))
                    pd_women = int(pd_total*(w_p+np.random.uniform(-0.03,0.03)))
                    pd_pwd = int(pd_total*np.random.uniform(0.01,0.03))
                    avg_days = round(pd_total/max(hh_employed,1),1)
                    rows.append({
                        'state_code':sc,'district_code':dc,
                        'report_date':report_date.strftime('%Y-%m-%d'),
                        'financial_year':fy,'month_num':report_date.month,
                        'job_cards_issued':hh_jc,'active_job_cards':hh_active_jc,
                        'households_demanded':hh_demanded,'households_employed':hh_employed,
                        'households_100days':hh_100days,
                        'person_days_total':pd_total,'person_days_sc':pd_sc,
                        'person_days_st':pd_st,'person_days_women':pd_women,
                        'person_days_pwd':pd_pwd,'avg_days_per_hh':avg_days,
                    })
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(DATA,'fact_employment.csv'), index=False)
    print(f"  fact_employment.csv    — {len(df):,} rows")

def gen_fact_wages():
    rows = []
    state_map = {sc:nw for sc,sn,sh,rg,nw,*_ in STATES}
    for sc,districts_list in DISTRICTS.items():
        nw = state_map[sc]
        for fy in FINANCIAL_YEARS:
            g = GROWTH[fy]
            fy_start = FY_START[fy]
            notified = nw*(1+0.03*(int(fy[2:])-2020))
            for m in range(12):
                report_date = fy_start + relativedelta(months=m)
                for i,dn in enumerate(districts_list):
                    dc = f"{sc}_D{i+1:02d}"
                    workers = int(np.random.randint(5000,25000)*g)
                    avg_wage = round(notified*np.random.uniform(0.92,1.02), 2)
                    total_wages = round(workers*avg_wage*np.random.uniform(20,35)/100000, 2)
                    pct_15days = np.random.uniform(0.55,0.92)
                    wages_15 = round(total_wages*pct_15days, 2)
                    pending = round(total_wages*np.random.uniform(0.05,0.20), 2)
                    rows.append({
                        'state_code':sc,'district_code':dc,
                        'report_date':report_date.strftime('%Y-%m-%d'),
                        'financial_year':fy,'month_num':report_date.month,
                        'workers_paid':workers,
                        'total_wages_lakhs':total_wages,
                        'wages_within_15days_lakhs':wages_15,
                        'pending_wages_lakhs':pending,
                        'avg_wage_rate':avg_wage,'notified_wage_rate':round(notified,2),
                    })
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(DATA,'fact_wages.csv'), index=False)
    print(f"  fact_wages.csv         — {len(df):,} rows")

def gen_fact_works():
    rows = []
    for sc,districts_list in DISTRICTS.items():
        base_works = np.random.randint(50,200)
        for fy in FINANCIAL_YEARS:
            g = GROWTH[fy]
            for i,dn in enumerate(districts_list):
                dc = f"{sc}_D{i+1:02d}"
                for cid,cn,*_ in WORK_CATEGORIES:
                    cat_mult = {'WC':1.4,'RC':1.2,'AG':1.0,'LD':0.8,'FL':0.7}[cid]
                    taken = int(base_works*cat_mult*g*np.random.uniform(0.7,1.3))
                    compl_rate = np.random.uniform(0.45,0.80)
                    completed = int(taken*compl_rate)
                    in_prog = int((taken-completed)*np.random.uniform(0.60,0.90))
                    exp = round(taken*np.random.uniform(8,22),2)
                    assets = int(completed*np.random.uniform(0.70,1.0))
                    report_date = date(int(fy[2:]),3,31)
                    rows.append({
                        'state_code':sc,'district_code':dc,
                        'financial_year':fy,'category_id':cid,
                        'report_date':report_date.strftime('%Y-%m-%d'),
                        'works_taken_up':taken,'works_completed':completed,
                        'works_in_progress':in_prog,
                        'expenditure_lakhs':exp,'assets_created':assets,
                    })
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(DATA,'fact_works.csv'), index=False)
    print(f"  fact_works.csv         — {len(df):,} rows")

# ── PBIP BOILERPLATE ──────────────────────────────────────────────────────────

def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path,'w',encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def write_text(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path,'w',encoding='utf-8') as f:
        f.write(text)

def create_pbip_boilerplate():
    # .pbip entry
    write_json(os.path.join(BASE,'NREGA-Dashboard.pbip'), {
        "$schema":"https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json",
        "version":"1.0",
        "artifacts":[{"report":{"path":"NREGA-Dashboard.Report"}}],
        "settings":{"enableAutoRecovery":True}
    })
    # SemanticModel .platform
    write_json(os.path.join(SM_DIR,'.platform'), {
        "$schema":"https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
        "metadata":{"type":"SemanticModel","displayName":"NREGA-Dashboard"},
        "config":{"version":"2.0","logicalId":str(uuid.uuid4())}
    })
    # SemanticModel definition.pbism
    write_json(os.path.join(SM_DIR,'definition.pbism'), {
        "$schema":"https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json",
        "version":"4.2","settings":{}
    })
    # Report .platform
    write_json(os.path.join(RP_DIR,'.platform'), {
        "$schema":"https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
        "metadata":{"type":"Report","displayName":"NREGA-Dashboard"},
        "config":{"version":"2.0","logicalId":str(uuid.uuid4())}
    })
    # Report definition.pbir
    write_json(os.path.join(RP_DIR,'definition.pbir'), {
        "$schema":"https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
        "version":"4.0",
        "datasetReference":{"byPath":{"path":"../NREGA-Dashboard.SemanticModel"}}
    })
    # Cultures
    write_text(os.path.join(SM_DIR,'definition','cultures','en-US.tmdl'),
               'cultureInfo en-US\n\n')
    # Database
    write_text(os.path.join(SM_DIR,'definition','database.tmdl'),
               'database\n\tcompatibilityLevel: 1600\n')
    print("  PBIP boilerplate files created")

# ── TMDL HELPERS ──────────────────────────────────────────────────────────────

def ltag(): return str(uuid.uuid4())

def csv_path(fname):
    return os.path.join(DATA, fname).replace('\\','\\\\')

def make_tmdl_column(name, dtype, summarize='none', is_key=False):
    fmt = '0' if dtype=='int64' else ('#,0.00' if dtype=='double' else '')
    lines = [f'\tcolumn {name}']
    lines.append(f'\t\tdataType: {dtype}')
    if fmt: lines.append(f'\t\tformatString: {fmt}')
    lines.append(f'\t\tlineageTag: {ltag()}')
    lines.append(f'\t\tsummarizeBy: {summarize}')
    lines.append(f'\t\tsourceColumn: {name}')
    lines.append(f'\t\tannotation SummarizationSetBy = Automatic')
    return '\n'.join(lines)

def make_tmdl_table(name, columns_def, csv_file, col_type_map):
    """columns_def: list of (col_name, dtype, summarize)"""
    lines = [f'table {name}', f'\tlineageTag: {ltag()}', '']
    for col,dt,sm in columns_def:
        lines.append(make_tmdl_column(col,dt,sm))
        lines.append('')
    # M source
    path = csv_path(csv_file)
    n_cols = len(columns_def)
    type_list = ', '.join([f'{{"{c}", {t}}}' for c,t in col_type_map])
    m_src = (
        f'\tpartition {name} = m\n'
        f'\t\tmode: import\n'
        f'\t\tsource =\n'
        f'\t\t\t\tlet\n'
        f'\t\t\t\t    Source = Csv.Document(File.Contents("{path}"),\n'
        f'\t\t\t\t        [Delimiter=",", Columns={n_cols}, Encoding=1252, QuoteStyle=QuoteStyle.None]),\n'
        f'\t\t\t\t    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),\n'
        f'\t\t\t\t    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers",{{{type_list}}})\n'
        f'\t\t\t\tin\n'
        f'\t\t\t\t    #"Changed Type"\n'
    )
    lines.append(m_src)
    lines.append('\tannotation PBI_NavigationStepName = Navigation')
    lines.append('\tannotation PBI_ResultType = Table')
    return '\n'.join(lines) + '\n'

# ── TMDL TABLE DEFINITIONS ────────────────────────────────────────────────────

def create_tmdl_tables():
    tbl_dir = os.path.join(SM_DIR,'definition','tables')

    # ── dim_date
    write_text(os.path.join(tbl_dir,'dim_date.tmdl'), make_tmdl_table(
        'dim_date',
        [('date','dateTime','none'),('year','int64','none'),('month_num','int64','none'),
         ('month_name','string','none'),('month_short','string','none'),
         ('quarter','int64','none'),('financial_year','string','none'),
         ('financial_quarter','string','none'),('day_of_week','string','none'),
         ('is_weekend','boolean','none'),('year_month','string','none')],
        'dim_date.csv',
        [('date','type date'),('year','Int64.Type'),('month_num','Int64.Type'),
         ('month_name','type text'),('month_short','type text'),('quarter','Int64.Type'),
         ('financial_year','type text'),('financial_quarter','type text'),
         ('day_of_week','type text'),('is_weekend','type logical'),('year_month','type text')]
    ))

    # ── dim_geography
    write_text(os.path.join(tbl_dir,'dim_geography.tmdl'), make_tmdl_table(
        'dim_geography',
        [('state_code','string','none'),('state_name','string','none'),
         ('state_hindi','string','none'),('district_code','string','none'),
         ('district_name','string','none'),('region','string','none'),('zone','string','none')],
        'dim_geography.csv',
        [('state_code','type text'),('state_name','type text'),('state_hindi','type text'),
         ('district_code','type text'),('district_name','type text'),
         ('region','type text'),('zone','type text')]
    ))

    # ── dim_work_category
    write_text(os.path.join(tbl_dir,'dim_work_category.tmdl'), make_tmdl_table(
        'dim_work_category',
        [('category_id','string','none'),('category_name','string','none'),
         ('category_hindi','string','none'),('major_category','string','none')],
        'dim_work_category.csv',
        [('category_id','type text'),('category_name','type text'),
         ('category_hindi','type text'),('major_category','type text')]
    ))

    # ── fact_employment
    write_text(os.path.join(tbl_dir,'fact_employment.tmdl'), make_tmdl_table(
        'fact_employment',
        [('state_code','string','none'),('district_code','string','none'),
         ('report_date','dateTime','none'),('financial_year','string','none'),
         ('month_num','int64','none'),('job_cards_issued','int64','sum'),
         ('active_job_cards','int64','sum'),('households_demanded','int64','sum'),
         ('households_employed','int64','sum'),('households_100days','int64','sum'),
         ('person_days_total','int64','sum'),('person_days_sc','int64','sum'),
         ('person_days_st','int64','sum'),('person_days_women','int64','sum'),
         ('person_days_pwd','int64','sum'),('avg_days_per_hh','double','average')],
        'fact_employment.csv',
        [('state_code','type text'),('district_code','type text'),
         ('report_date','type date'),('financial_year','type text'),
         ('month_num','Int64.Type'),('job_cards_issued','Int64.Type'),
         ('active_job_cards','Int64.Type'),('households_demanded','Int64.Type'),
         ('households_employed','Int64.Type'),('households_100days','Int64.Type'),
         ('person_days_total','Int64.Type'),('person_days_sc','Int64.Type'),
         ('person_days_st','Int64.Type'),('person_days_women','Int64.Type'),
         ('person_days_pwd','Int64.Type'),('avg_days_per_hh','type number')]
    ))

    # ── fact_wages
    write_text(os.path.join(tbl_dir,'fact_wages.tmdl'), make_tmdl_table(
        'fact_wages',
        [('state_code','string','none'),('district_code','string','none'),
         ('report_date','dateTime','none'),('financial_year','string','none'),
         ('month_num','int64','none'),('workers_paid','int64','sum'),
         ('total_wages_lakhs','double','sum'),('wages_within_15days_lakhs','double','sum'),
         ('pending_wages_lakhs','double','sum'),
         ('avg_wage_rate','double','average'),('notified_wage_rate','double','average')],
        'fact_wages.csv',
        [('state_code','type text'),('district_code','type text'),
         ('report_date','type date'),('financial_year','type text'),
         ('month_num','Int64.Type'),('workers_paid','Int64.Type'),
         ('total_wages_lakhs','type number'),('wages_within_15days_lakhs','type number'),
         ('pending_wages_lakhs','type number'),('avg_wage_rate','type number'),
         ('notified_wage_rate','type number')]
    ))

    # ── fact_works
    write_text(os.path.join(tbl_dir,'fact_works.tmdl'), make_tmdl_table(
        'fact_works',
        [('state_code','string','none'),('district_code','string','none'),
         ('financial_year','string','none'),('category_id','string','none'),
         ('report_date','dateTime','none'),('works_taken_up','int64','sum'),
         ('works_completed','int64','sum'),('works_in_progress','int64','sum'),
         ('expenditure_lakhs','double','sum'),('assets_created','int64','sum')],
        'fact_works.csv',
        [('state_code','type text'),('district_code','type text'),
         ('financial_year','type text'),('category_id','type text'),
         ('report_date','type date'),('works_taken_up','Int64.Type'),
         ('works_completed','Int64.Type'),('works_in_progress','Int64.Type'),
         ('expenditure_lakhs','type number'),('assets_created','Int64.Type')]
    ))

    print("  TMDL table files created")

# ── MEASURES ──────────────────────────────────────────────────────────────────

MEASURES_TMDL = f'''table _Measures
\tlineageTag: {ltag()}

\tmeasure 'Total Person Days' = SUM(fact_employment[person_days_total])
\t\tlineageTag: {ltag()}
\t\tformatString: #,0

\tmeasure 'SC Person Days' = SUM(fact_employment[person_days_sc])
\t\tlineageTag: {ltag()}
\t\tformatString: #,0

\tmeasure 'ST Person Days' = SUM(fact_employment[person_days_st])
\t\tlineageTag: {ltag()}
\t\tformatString: #,0

\tmeasure 'Women Person Days' = SUM(fact_employment[person_days_women])
\t\tlineageTag: {ltag()}
\t\tformatString: #,0

\tmeasure 'PwD Person Days' = SUM(fact_employment[person_days_pwd])
\t\tlineageTag: {ltag()}
\t\tformatString: #,0

\tmeasure '% SC Person Days' = DIVIDE([SC Person Days], [Total Person Days], 0)
\t\tlineageTag: {ltag()}
\t\tformatString: 0.0%;-0.0%;0.0%

\tmeasure '% ST Person Days' = DIVIDE([ST Person Days], [Total Person Days], 0)
\t\tlineageTag: {ltag()}
\t\tformatString: 0.0%;-0.0%;0.0%

\tmeasure '% Women Person Days' = DIVIDE([Women Person Days], [Total Person Days], 0)
\t\tlineageTag: {ltag()}
\t\tformatString: 0.0%;-0.0%;0.0%

\tmeasure '% PwD Person Days' = DIVIDE([PwD Person Days], [Total Person Days], 0)
\t\tlineageTag: {ltag()}
\t\tformatString: 0.0%;-0.0%;0.0%

\tmeasure 'Households Demanded' = SUM(fact_employment[households_demanded])
\t\tlineageTag: {ltag()}
\t\tformatString: #,0

\tmeasure 'Households Employed' = SUM(fact_employment[households_employed])
\t\tlineageTag: {ltag()}
\t\tformatString: #,0

\tmeasure 'Households 100 Days' = SUM(fact_employment[households_100days])
\t\tlineageTag: {ltag()}
\t\tformatString: #,0

\tmeasure 'Demand Fulfilment Rate' = DIVIDE([Households Employed], [Households Demanded], 0)
\t\tlineageTag: {ltag()}
\t\tformatString: 0.0%;-0.0%;0.0%

\tmeasure '% HH Completing 100 Days' = DIVIDE([Households 100 Days], [Households Employed], 0)
\t\tlineageTag: {ltag()}
\t\tformatString: 0.0%;-0.0%;0.0%

\tmeasure 'Avg Days per Household' = DIVIDE([Total Person Days], [Households Employed], 0)
\t\tlineageTag: {ltag()}
\t\tformatString: #,0.0

\tmeasure 'Job Cards Issued' = SUM(fact_employment[job_cards_issued])
\t\tlineageTag: {ltag()}
\t\tformatString: #,0

\tmeasure 'Active Job Cards' = SUM(fact_employment[active_job_cards])
\t\tlineageTag: {ltag()}
\t\tformatString: #,0

\tmeasure 'Job Card Utilisation' = DIVIDE([Households Demanded], [Job Cards Issued], 0)
\t\tlineageTag: {ltag()}
\t\tformatString: 0.0%;-0.0%;0.0%

\tmeasure 'Total Wages (Lakhs)' = SUM(fact_wages[total_wages_lakhs])
\t\tlineageTag: {ltag()}
\t\tformatString: #,0.00

\tmeasure 'Wages Within 15 Days (Lakhs)' = SUM(fact_wages[wages_within_15days_lakhs])
\t\tlineageTag: {ltag()}
\t\tformatString: #,0.00

\tmeasure '% Wages Within 15 Days' = DIVIDE([Wages Within 15 Days (Lakhs)], [Total Wages (Lakhs)], 0)
\t\tlineageTag: {ltag()}
\t\tformatString: 0.0%;-0.0%;0.0%

\tmeasure 'Pending Wages (Lakhs)' = SUM(fact_wages[pending_wages_lakhs])
\t\tlineageTag: {ltag()}
\t\tformatString: #,0.00

\tmeasure 'Avg Wage Rate' = AVERAGE(fact_wages[avg_wage_rate])
\t\tlineageTag: {ltag()}
\t\tformatString: #,0.00

\tmeasure 'Notified Wage Rate' = AVERAGE(fact_wages[notified_wage_rate])
\t\tlineageTag: {ltag()}
\t\tformatString: #,0.00

\tmeasure 'Wage Compliance %' = DIVIDE([Avg Wage Rate], [Notified Wage Rate], 0)
\t\tlineageTag: {ltag()}
\t\tformatString: 0.0%;-0.0%;0.0%

\tmeasure 'Works Taken Up' = SUM(fact_works[works_taken_up])
\t\tlineageTag: {ltag()}
\t\tformatString: #,0

\tmeasure 'Works Completed' = SUM(fact_works[works_completed])
\t\tlineageTag: {ltag()}
\t\tformatString: #,0

\tmeasure 'Works In Progress' = SUM(fact_works[works_in_progress])
\t\tlineageTag: {ltag()}
\t\tformatString: #,0

\tmeasure 'Works Completion Rate' = DIVIDE([Works Completed], [Works Taken Up], 0)
\t\tlineageTag: {ltag()}
\t\tformatString: 0.0%;-0.0%;0.0%

\tmeasure 'Total Expenditure (Lakhs)' = SUM(fact_works[expenditure_lakhs])
\t\tlineageTag: {ltag()}
\t\tformatString: #,0.00

\tmeasure 'Assets Created' = SUM(fact_works[assets_created])
\t\tlineageTag: {ltag()}
\t\tformatString: #,0

\tmeasure 'YoY Person Days Growth' =
\t\t\tVAR CY = [Total Person Days]
\t\t\tVAR PY = CALCULATE([Total Person Days], DATEADD(dim_date[date], -1, YEAR))
\t\t\tRETURN DIVIDE(CY - PY, PY, 0)
\t\tlineageTag: {ltag()}
\t\tformatString: +0.0%;-0.0%;0.0%

\tmeasure 'Person Days (Crore)' = DIVIDE([Total Person Days], 10000000)
\t\tlineageTag: {ltag()}
\t\tformatString: #,0.00

\tpartition _Measures = calculated
\t\tmode: import
\t\tsource = ""

\tannotation PBI_ResultType = Table
'''

# ── RELATIONSHIPS ─────────────────────────────────────────────────────────────

RELATIONSHIPS_TMDL = '''relationship rel_date_employment
\tfromColumn: fact_employment.report_date
\ttoColumn: dim_date.date

relationship rel_date_wages
\tfromColumn: fact_wages.report_date
\ttoColumn: dim_date.date

relationship rel_date_works
\tfromColumn: fact_works.report_date
\ttoColumn: dim_date.date

relationship rel_geo_employment
\tfromColumn: fact_employment.district_code
\ttoColumn: dim_geography.district_code

relationship rel_geo_wages
\tfromColumn: fact_wages.district_code
\ttoColumn: dim_geography.district_code

relationship rel_geo_works
\tfromColumn: fact_works.district_code
\ttoColumn: dim_geography.district_code

relationship rel_cat_works
\tfromColumn: fact_works.category_id
\ttoColumn: dim_work_category.category_id

'''

MODEL_TMDL = '''model Model
\tculture: en-US
\tdefaultPowerBIDataSourceVersion: powerBI_V3
\tsourceQueryCulture: en-IN
\tdataAccessOptions
\t\tlegacyRedirects
\t\treturnErrorValuesAsNull

annotation PBI_QueryOrder = ["_Measures","dim_date","dim_geography","dim_work_category","fact_employment","fact_wages","fact_works"]

annotation PBI_ProTooling = ["DevMode"]

ref table _Measures
ref table dim_date
ref table dim_geography
ref table dim_work_category
ref table fact_employment
ref table fact_wages
ref table fact_works

ref cultureInfo en-US

'''

# ── GoI BRANDING THEME ────────────────────────────────────────────────────────

GOI_THEME = {
    "name": "GoIBranding",
    "dataColors": ["#FF9933","#138808","#0066CC","#DC143C","#4682B4",
                   "#228B22","#DAA520","#8B0000","#2F4F4F","#FF6347",
                   "#20B2AA","#9370DB","#FF8C00","#006400","#4169E1"],
    "foreground": "#1A1A2E",
    "foregroundNeutralSecondary": "#5A5A7A",
    "foregroundNeutralTertiary": "#9090AA",
    "background": "#0D1628",
    "backgroundLight": "#162040",
    "backgroundNeutral": "#2A3A5A",
    "tableAccent": "#FF9933",
    "good": "#138808",
    "neutral": "#FF9933",
    "bad": "#DC143C",
    "maximum": "#138808",
    "center": "#FF9933",
    "minimum": "#DC143C",
    "null": "#5A5A7A",
    "hyperlink": "#0066CC",
    "visitedHyperlink": "#4682B4",
    "textClasses": {
        "callout": {"fontSize":28,"fontFace":"Segoe UI","color":"#FF9933"},
        "title": {"fontSize":13,"fontFace":"Segoe UI Semibold","color":"#F0F0FF"},
        "header": {"fontSize":12,"fontFace":"Segoe UI Semibold","color":"#9090BB"},
        "label": {"fontSize":10,"fontFace":"Segoe UI","color":"#9090BB"}
    },
    "visualStyles": {
        "*": {"*": {
            "*": [{"wordWrap":True}],
            "background": [{"show":True,"color":{"solid":{"color":"#162040"}},"transparency":5}],
            "border": [{"show":True,"color":{"solid":{"color":"#2A3A5A"}},"radius":8,"width":1}],
            "title": [{"show":True,"fontColor":{"solid":{"color":"#9090BB"}},"fontSize":11,"fontFamily":"Segoe UI","titleWrap":True,"background":{"solid":{"color":"#0D1628"}}}],
            "lineStyles": [{"strokeWidth":2}],
            "plotArea": [{"transparency":100}],
            "categoryAxis": [{"gridlineStyle":"dotted","gridlineColor":{"solid":{"color":"#2A3A5A"}},"labelColor":{"solid":{"color":"#9090BB"}},"fontSize":10,"showAxisTitle":False}],
            "valueAxis": [{"gridlineStyle":"dotted","gridlineColor":{"solid":{"color":"#2A3A5A"}},"labelColor":{"solid":{"color":"#9090BB"}},"fontSize":10,"showAxisTitle":False}],
            "legend": [{"show":True,"labelColor":{"solid":{"color":"#9090BB"}},"fontSize":10}]
        }},
        "card": {"*": {
            "background": [{"show":True,"color":{"solid":{"color":"#162040"}},"transparency":0}],
            "border": [{"show":True,"color":{"solid":{"color":"#2A3A5A"}},"radius":10,"width":1}],
            "title": [{"show":False}],
            "labels": [{"color":{"solid":{"color":"#FF9933"}},"fontSize":28,"fontFamily":"Segoe UI","bold":True}],
            "categoryLabels": [{"show":True,"color":{"solid":{"color":"#9090BB"}},"fontSize":11}]
        }},
        "columnChart": {"*": {
            "background": [{"show":True,"color":{"solid":{"color":"#162040"}},"transparency":0}],
            "dataPoint": [{"fill":{"solid":{"color":"#FF9933"}}}],
            "plotArea": [{"transparency":100}],
            "categoryAxis": [{"gridlineStyle":"none","labelColor":{"solid":{"color":"#9090BB"}},"fontSize":10,"showAxisTitle":False}],
            "valueAxis": [{"gridlineStyle":"dotted","gridlineColor":{"solid":{"color":"#2A3A5A"}},"labelColor":{"solid":{"color":"#9090BB"}},"fontSize":10,"showAxisTitle":False}]
        }},
        "barChart": {"*": {
            "background": [{"show":True,"color":{"solid":{"color":"#162040"}},"transparency":0}],
            "dataPoint": [{"fill":{"solid":{"color":"#138808"}}}],
            "plotArea": [{"transparency":100}],
            "categoryAxis": [{"gridlineStyle":"none","labelColor":{"solid":{"color":"#9090BB"}},"fontSize":10,"showAxisTitle":False}],
            "valueAxis": [{"gridlineStyle":"dotted","gridlineColor":{"solid":{"color":"#2A3A5A"}},"labelColor":{"solid":{"color":"#9090BB"}},"fontSize":10,"showAxisTitle":False}],
            "labels": [{"show":True,"color":{"solid":{"color":"#F0F0FF"}},"fontSize":9}]
        }},
        "lineChart": {"*": {
            "background": [{"show":True,"color":{"solid":{"color":"#162040"}},"transparency":0}],
            "dataPoint": [{"fill":{"solid":{"color":"#FF9933"}}}],
            "lineStyles": [{"strokeWidth":3,"lineStyle":"solid"}],
            "markers": [{"show":True}],
            "plotArea": [{"transparency":100}],
            "categoryAxis": [{"gridlineStyle":"none","labelColor":{"solid":{"color":"#9090BB"}},"fontSize":10,"showAxisTitle":False}],
            "valueAxis": [{"gridlineStyle":"dotted","gridlineColor":{"solid":{"color":"#2A3A5A"}},"labelColor":{"solid":{"color":"#9090BB"}},"fontSize":10,"showAxisTitle":False}]
        }},
        "donutChart": {"*": {
            "background": [{"show":True,"color":{"solid":{"color":"#162040"}},"transparency":0}],
            "legend": [{"show":True,"labelColor":{"solid":{"color":"#9090BB"}},"fontSize":10,"position":"Bottom"}],
            "labels": [{"show":False}]
        }},
        "funnel": {"*": {
            "background": [{"show":True,"color":{"solid":{"color":"#162040"}},"transparency":0}],
            "labels": [{"show":True,"color":{"solid":{"color":"#F0F0FF"}},"fontSize":11}],
            "percentBarLabel": [{"show":True,"color":{"solid":{"color":"#9090BB"}},"fontSize":10}]
        }},
        "slicer": {"*": {
            "background": [{"show":True,"color":{"solid":{"color":"#162040"}},"transparency":0}],
            "border": [{"show":True,"color":{"solid":{"color":"#2A3A5A"}},"radius":8}],
            "title": [{"show":False}],
            "items": [{"fontColor":{"solid":{"color":"#F0F0FF"}},"background":{"solid":{"color":"#1E2E4A"}}}]
        }},
        "matrix": {"*": {
            "background": [{"show":True,"color":{"solid":{"color":"#162040"}},"transparency":0}],
            "border": [{"show":True,"color":{"solid":{"color":"#2A3A5A"}}}],
            "columnHeaders": [{"fontColor":{"solid":{"color":"#FF9933"}},"backColor":{"solid":{"color":"#0D1628"}},"fontSize":11,"fontFamily":"Segoe UI Semibold","outline":"None"}],
            "rowHeaders": [{"fontColor":{"solid":{"color":"#F0F0FF"}},"backColor":{"solid":{"color":"#162040"}},"fontSize":10,"outline":"None"}],
            "values": [{"fontColor":{"solid":{"color":"#F0F0FF"}},"backColor":{"solid":{"color":"#162040"}},"fontSize":10,"outline":"None"}],
            "total": [{"fontColor":{"solid":{"color":"#FF9933"}},"backColor":{"solid":{"color":"#0D1628"}},"fontSize":11}],
            "grid": [{"gridVertical":False,"gridHorizontal":True,"gridHorizontalColor":{"solid":{"color":"#2A3A5A"}},"rowPadding":6}]
        }},
        "textbox": {"*": {"background":[{"show":False}],"border":[{"show":False}]}}
    }
}

# ── REPORT STRUCTURE ──────────────────────────────────────────────────────────

CY26_THEME_PATH = os.path.join(
    os.path.dirname(BASE),
    'product-funnel-dashboard',
    'Product-Funnel-Dashboard.Report',
    'StaticResources','SharedResources','BaseThemes','CY26SU04.json'
)

def create_report_files():
    theme_dir = os.path.join(RP_DIR,'StaticResources','SharedResources','BaseThemes')
    os.makedirs(theme_dir, exist_ok=True)

    # Copy CY26SU04 base theme
    if os.path.exists(CY26_THEME_PATH):
        import shutil
        shutil.copy(CY26_THEME_PATH, os.path.join(theme_dir,'CY26SU04.json'))

    # Write GoI theme
    write_json(os.path.join(theme_dir,'GoIBranding.json'), GOI_THEME)

    # version.json
    write_json(os.path.join(RP_DIR,'definition','version.json'), {
        "$schema":"https://developer.microsoft.com/json-schemas/fabric/item/report/definition/versionMetadata/1.0.0/schema.json",
        "version":"2.0.0"
    })

    # report.json
    write_json(os.path.join(RP_DIR,'definition','report.json'), {
        "$schema":"https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/3.2.0/schema.json",
        "themeCollection": {
            "baseTheme": {
                "name":"GoIBranding",
                "reportVersionAtImport":{"visual":"2.8.0","report":"3.2.0","page":"2.3.1"},
                "type":"SharedResources"
            }
        },
        "objects": {"section":[{"properties":{"verticalAlignment":{"expr":{"Literal":{"Value":"'Top'"}}}}}]},
        "resourcePackages": [{"name":"SharedResources","type":"SharedResources","items":[
            {"name":"CY26SU04","path":"BaseThemes/CY26SU04.json","type":"BaseTheme"},
            {"name":"GoIBranding","path":"BaseThemes/GoIBranding.json","type":"BaseTheme"}
        ]}],
        "settings": {
            "useStylableVisualContainerHeader":True,"exportDataMode":"AllowSummarized",
            "defaultDrillFilterOtherVisuals":True,"allowChangeFilterTypes":True,
            "useEnhancedTooltips":True,"useDefaultAggregateDisplayName":True
        }
    })
    print("  Report structure files created")

# ── VISUAL JSON HELPERS (reused from funnel project) ─────────────────────────

def m(name): return {"Measure":{"Expression":{"SourceRef":{"Entity":"_Measures"}},"Property":name}}
def col(entity,prop): return {"Column":{"Expression":{"SourceRef":{"Entity":entity}},"Property":prop}}
def col_agg(entity,prop,fn=5): return {"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Entity":entity}},"Property":prop}},"Function":fn}}
def proj(field,qref,active=True):
    p={"field":field,"queryRef":qref}
    if active: p["active"]=True
    return p

def card(vid,x,y,w,h,measure_name,tab=0):
    return {"id":vid,"position":{"x":x,"y":y,"z":0,"width":w,"height":h,"tabOrder":tab},
            "visual":{"visualType":"card","query":{"queryState":{"Values":{"projections":[proj(m(measure_name),f"_Measures.{measure_name}")]}}}}}

def bar(vid,x,y,w,h,cat_entity,cat_prop,y_measures,tab=0):
    return {"id":vid,"position":{"x":x,"y":y,"z":0,"width":w,"height":h,"tabOrder":tab},
            "visual":{"visualType":"barChart","query":{"queryState":{
                "Category":{"projections":[proj(col(cat_entity,cat_prop),f"{cat_entity}.{cat_prop}")]},
                "Y":{"projections":[proj(m(mn),f"_Measures.{mn}") for mn in y_measures]}}}}}

def column(vid,x,y,w,h,cat_entity,cat_prop,y_measures,tab=0):
    return {"id":vid,"position":{"x":x,"y":y,"z":0,"width":w,"height":h,"tabOrder":tab},
            "visual":{"visualType":"columnChart","query":{"queryState":{
                "Category":{"projections":[proj(col(cat_entity,cat_prop),f"{cat_entity}.{cat_prop}")]},
                "Y":{"projections":[proj(m(mn),f"_Measures.{mn}") for mn in y_measures]}}}}}

def line(vid,x,y,w,h,cat_entity,cat_prop,y_measures,tab=0):
    return {"id":vid,"position":{"x":x,"y":y,"z":0,"width":w,"height":h,"tabOrder":tab},
            "visual":{"visualType":"lineChart","query":{"queryState":{
                "Category":{"projections":[proj(col(cat_entity,cat_prop),f"{cat_entity}.{cat_prop}")]},
                "Y":{"projections":[proj(m(mn),f"_Measures.{mn}") for mn in y_measures]}}}}}

def donut(vid,x,y,w,h,cat_entity,cat_prop,y_measure,tab=0):
    return {"id":vid,"position":{"x":x,"y":y,"z":0,"width":w,"height":h,"tabOrder":tab},
            "visual":{"visualType":"donutChart","query":{"queryState":{
                "Category":{"projections":[proj(col(cat_entity,cat_prop),f"{cat_entity}.{cat_prop}")]},
                "Y":{"projections":[proj(m(y_measure),f"_Measures.{y_measure}")]}}}}}

def funnel_v(vid,x,y,w,h,cat_entity,cat_prop,tab=0):
    return {"id":vid,"position":{"x":x,"y":y,"z":0,"width":w,"height":h,"tabOrder":tab},
            "visual":{"visualType":"funnel","query":{"queryState":{
                "Category":{"projections":[proj(col(cat_entity,cat_prop),f"{cat_entity}.{cat_prop}")]},
                "Y":{"projections":[proj(col_agg(cat_entity,"households_employed",0),f"Sum({cat_entity}.households_employed)")]}}}}}

def slicer_v(vid,x,y,w,h,entity,prop,tab=0):
    return {"id":vid,"position":{"x":x,"y":y,"z":0,"width":w,"height":h,"tabOrder":tab},
            "visual":{"visualType":"slicer","query":{"queryState":{"Values":{"projections":[proj(col(entity,prop),f"{entity}.{prop}")]}}},"objects":{"general":[{"properties":{"orientation":{"expr":{"Literal":{"Value":"'Horizontal'"}}}}}]}}}

def matrix_v(vid,x,y,w,h,row_e,row_p,col_e,col_p,val_measures,tab=0):
    return {"id":vid,"position":{"x":x,"y":y,"z":0,"width":w,"height":h,"tabOrder":tab},
            "visual":{"visualType":"matrix","query":{"queryState":{
                "Rows":{"projections":[proj(col(row_e,row_p),f"{row_e}.{row_p}")]},
                "Columns":{"projections":[proj(col(col_e,col_p),f"{col_e}.{col_p}")]},
                "Values":{"projections":[proj(m(mn),f"_Measures.{mn}") for mn in val_measures]}}}}}

def make_visual_json(v):
    return {"$schema":"https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/1.4.0/schema.json",
            "name":v["id"],"position":v["position"],"visual":v["visual"]}

# ── PAGE DEFINITIONS ──────────────────────────────────────────────────────────

PAGES = {
    "p1_executive":    ("Executive Summary",           "p1execsummary0001"),
    "p2_employment":   ("Employment & Demand",         "p2employment00002"),
    "p3_equity":       ("Social Equity",               "p3socialequity003"),
    "p4_wages":        ("Wages & Payment",             "p4wagespayment004"),
    "p5_works":        ("Works & Assets",              "p5worksassets0005"),
}

def page_visuals():
    return {
        "p1_executive": [
            # Row 1 — National KPI cards
            card("p1c1", 20,20,220,90,"Person Days (Crore)",      tab=0),
            card("p1c2",250,20,220,90,"Households Employed",      tab=1),
            card("p1c3",480,20,220,90,"% HH Completing 100 Days", tab=2),
            card("p1c4",710,20,220,90,"Wage Compliance %",        tab=3),
            card("p1c5",940,20,220,90,"Works Completion Rate",    tab=4),
            card("p1c6",1170,20,90,90,"Demand Fulfilment Rate",   tab=5),
            # Main trend line
            line("p1ln",20,125,820,280,"dim_date","financial_year",["Total Person Days"],tab=6),
            # Social equity donut
            donut("p1dn",860,125,400,280,"dim_geography","region","Total Person Days",tab=7),
            # Top states bar
            bar("p1br",20,415,600,285,"dim_geography","state_name",["Total Person Days"],tab=8),
            # Works completion bar
            bar("p1wc",640,415,620,285,"dim_geography","state_name",["Works Completion Rate"],tab=9),
            # FY Slicer
            slicer_v("p1sl",20,620,1240,70,"dim_date","financial_year",tab=10),
        ],

        "p2_employment": [
            # KPI row
            card("p2c1", 20,20,280,90,"Households Demanded",    tab=0),
            card("p2c2",320,20,280,90,"Households Employed",    tab=1),
            card("p2c3",620,20,280,90,"Demand Fulfilment Rate", tab=2),
            card("p2c4",920,20,280,90,"Avg Days per Household", tab=3),
            # Job card funnel
            funnel_v("p2fn",20,120,520,340,"fact_employment","financial_year",tab=4),
            # Demand vs fulfilment by state
            bar("p2db",560,120,700,340,"dim_geography","state_name",
                ["Households Demanded","Households Employed"],tab=5),
            # Monthly trend
            column("p2mt",20,470,820,230,"dim_date","month_short",["Households Employed"],tab=6),
            # 100-day completion by state
            bar("p2hd",860,470,400,230,"dim_geography","state_name",["% HH Completing 100 Days"],tab=7),
            # Slicers
            slicer_v("p2sl1",20,620,600,70,"dim_date","financial_year",tab=8),
            slicer_v("p2sl2",640,620,620,70,"dim_geography","state_name",tab=9),
        ],

        "p3_equity": [
            # KPI row
            card("p3c1", 20,20,290,90,"% SC Person Days",    tab=0),
            card("p3c2",330,20,290,90,"% ST Person Days",    tab=1),
            card("p3c3",640,20,290,90,"% Women Person Days", tab=2),
            card("p3c4",950,20,290,90,"% PwD Person Days",   tab=3),
            # State-wise SC/ST/Women grouped bar
            bar("p3sb",20,120,820,280,"dim_geography","state_name",
                ["SC Person Days","ST Person Days","Women Person Days"],tab=4),
            # Donut: SC vs ST vs Others
            donut("p3dn",860,120,400,280,"dim_geography","region","Women Person Days",tab=5),
            # Women trend line by FY
            line("p3wl",20,415,820,280,"dim_date","financial_year",["Women Person Days"],tab=6),
            # Matrix: State x Category
            matrix_v("p3mx",860,415,400,280,"dim_geography","state_name",
                     "dim_date","financial_year",["% Women Person Days","% SC Person Days"],tab=7),
            # Slicers
            slicer_v("p3sl1",20,620,600,70,"dim_date","financial_year",tab=8),
            slicer_v("p3sl2",640,620,620,70,"dim_geography","region",tab=9),
        ],

        "p4_wages": [
            # KPI row
            card("p4c1", 20,20,220,90,"Avg Wage Rate",             tab=0),
            card("p4c2",250,20,220,90,"Notified Wage Rate",        tab=1),
            card("p4c3",480,20,220,90,"Wage Compliance %",         tab=2),
            card("p4c4",710,20,220,90,"% Wages Within 15 Days",    tab=3),
            card("p4c5",940,20,220,90,"Pending Wages (Lakhs)",     tab=4),
            card("p4c6",1170,20,90,90,"Total Wages (Lakhs)",       tab=5),
            # Wage rate vs notified by state
            bar("p4wb",20,120,820,280,"dim_geography","state_name",
                ["Avg Wage Rate","Notified Wage Rate"],tab=6),
            # % Wages within 15 days by state
            bar("p4pb",860,120,400,280,"dim_geography","state_name",["% Wages Within 15 Days"],tab=7),
            # Wage trend line
            line("p4wl",20,410,820,290,"dim_date","financial_year",["Avg Wage Rate","Notified Wage Rate"],tab=8),
            # Payment efficiency matrix
            matrix_v("p4mx",860,410,400,290,"dim_geography","state_name",
                     "dim_date","financial_year",["% Wages Within 15 Days"],tab=9),
            # Slicers
            slicer_v("p4sl1",20,620,600,70,"dim_date","financial_year",tab=10),
            slicer_v("p4sl2",640,620,620,70,"dim_geography","state_name",tab=11),
        ],

        "p5_works": [
            # KPI row
            card("p5c1", 20,20,280,90,"Works Taken Up",          tab=0),
            card("p5c2",320,20,280,90,"Works Completed",         tab=1),
            card("p5c3",620,20,280,90,"Works Completion Rate",   tab=2),
            card("p5c4",920,20,340,90,"Total Expenditure (Lakhs)",tab=3),
            # Works by category donut
            donut("p5dn",20,120,450,300,"dim_work_category","category_name","Works Taken Up",tab=4),
            # State-wise completion
            bar("p5sb",490,120,770,300,"dim_geography","state_name",["Works Completion Rate"],tab=5),
            # Expenditure by category
            column("p5ec",20,430,600,270,"dim_work_category","category_name",["Total Expenditure (Lakhs)"],tab=6),
            # Matrix: State x Category
            matrix_v("p5mx",640,430,620,270,"dim_geography","state_name",
                     "dim_work_category","category_name",["Works Completed","Expenditure (Lakhs)"],tab=7),
            # Slicers
            slicer_v("p5sl1",20,620,600,70,"dim_date","financial_year",tab=8),
            slicer_v("p5sl2",640,620,620,70,"dim_work_category","category_name",tab=9),
        ],
    }

# ── WRITE REPORT PAGES ────────────────────────────────────────────────────────

def create_report_pages():
    pages_dir = os.path.join(RP_DIR,'definition','pages')
    visuals_map = page_visuals()
    page_order = []

    for key,(display_name,pid) in PAGES.items():
        page_order.append(pid)
        page_folder = os.path.join(pages_dir, pid)
        os.makedirs(page_folder, exist_ok=True)

        # page.json (metadata only)
        write_json(os.path.join(page_folder,'page.json'), {
            "$schema":"https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json",
            "name":pid, "displayName":display_name,
            "displayOption":"FitToPage", "height":720, "width":1280
        })

        # individual visual files
        for v in visuals_map[key]:
            vis_folder = os.path.join(page_folder,'visuals',v["id"])
            os.makedirs(vis_folder, exist_ok=True)
            write_json(os.path.join(vis_folder,'visual.json'), make_visual_json(v))

        print(f"  Page: {display_name} ({len(visuals_map[key])} visuals)")

    # pages.json
    write_json(os.path.join(pages_dir,'pages.json'), {
        "$schema":"https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.0.0/schema.json",
        "pageOrder": page_order,
        "activePageName": page_order[0]
    })

# ── MAIN ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    try:
        from dateutil.relativedelta import relativedelta
    except ImportError:
        os.system("pip install python-dateutil")
        from dateutil.relativedelta import relativedelta

    os.makedirs(DATA, exist_ok=True)
    print("\n[1/5] Generating sample data...")
    gen_dim_date()
    gen_dim_geography()
    gen_dim_work_category()
    gen_fact_employment()
    gen_fact_wages()
    gen_fact_works()

    print("\n[2/5] Creating PBIP boilerplate...")
    create_pbip_boilerplate()

    print("\n[3/5] Creating TMDL model files...")
    create_tmdl_tables()
    tbl_dir = os.path.join(SM_DIR,'definition','tables')
    write_text(os.path.join(tbl_dir,'_Measures.tmdl'), MEASURES_TMDL)
    write_text(os.path.join(SM_DIR,'definition','relationships.tmdl'), RELATIONSHIPS_TMDL)
    write_text(os.path.join(SM_DIR,'definition','model.tmdl'), MODEL_TMDL)
    print("  TMDL measures + relationships + model written")

    print("\n[4/5] Creating report theme and structure...")
    create_report_files()

    print("\n[5/5] Creating 5 report pages with visuals...")
    create_report_pages()

    print("\nDone! Open NREGA-Dashboard.pbip in Power BI Desktop.")
    print(f"Files at: {BASE}")
