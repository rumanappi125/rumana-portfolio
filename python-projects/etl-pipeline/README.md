# ⚡ Scalable ETL Pipeline | PySpark + AWS Redshift + S3

## Project Overview

Engineered **scalable data preprocessing pipelines** for multi-terabyte datasets at Target (via E-Mech Solutions). Leveraged PySpark and AWS Redshift to achieve **40%+ improvement in data retrieval efficiency**, processing structured (CSV) and semi-structured (JSON) data at scale.

**Tools:** PySpark, Apache Spark, AWS Redshift, AWS S3, Python (Pandas, NumPy), Databricks  
**Domain:** E-Commerce / Retail Analytics  
**Company:** E-Mech Solutions → Client: Target

---

## 📊 Key Results

| Metric | Value |
|---|---|
| Data Retrieval Efficiency Gain | 40%+ |
| Query Execution Time Reduction | 35% |
| Dataset Size | Multi-Terabyte |
| Data Formats Handled | CSV, JSON, Parquet |
| Automated Reporting Time Saved | 9 hours/week |

---

## 🏗️ Pipeline Architecture

```
S3 Raw Zone (CSV/JSON)
        │
        ▼
  PySpark Ingestion
  (Schema Inference +
   Type Casting)
        │
        ▼
  Data Quality Layer
  (Null checks, Range
   validation, Dedup)
        │
        ▼
  Transformation Layer
  (Joins, Aggregations,
   Feature Engineering)
        │
        ▼
  Redshift Staging
  (COPY command via S3)
        │
        ▼
  Redshift Production
  (Star Schema Tables)
        │
        ▼
  Power BI / Metabase
  (Dashboard Refresh)
```
