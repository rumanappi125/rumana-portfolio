"""
AI Training Data Quality Framework
Analyst: Rumana Appi | Company: I-Neuron, Bengaluru
Description: Automated data quality validation for AI/ML training datasets
             - Null checks, range validation, deduplication, outlier detection
             - Generates HTML quality report
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
import logging
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


# ── DATA CLASSES ──────────────────────────────────────────
@dataclass
class QualityIssue:
    rule:        str
    column:      str
    severity:    str         # CRITICAL / WARNING / INFO
    count:       int
    pct:         float
    details:     str


@dataclass
class QualityReport:
    dataset_name:  str
    run_timestamp: str
    total_rows:    int
    total_cols:    int
    issues:        List[QualityIssue] = field(default_factory=list)
    metrics:       Dict[str, Any]     = field(default_factory=dict)

    @property
    def critical_count(self):
        return sum(1 for i in self.issues if i.severity == "CRITICAL")

    @property
    def warning_count(self):
        return sum(1 for i in self.issues if i.severity == "WARNING")

    @property
    def passed(self) -> bool:
        return self.critical_count == 0


# ── CORE VALIDATOR ────────────────────────────────────────
class DataQualityValidator:
    """
    Comprehensive data quality validator for AI training datasets.
    Implements: null checks, range validation, deduplication,
                outlier detection, schema enforcement, cardinality checks.
    """

    def __init__(self, df: pd.DataFrame, dataset_name: str = "dataset"):
        self.df           = df.copy()
        self.dataset_name = dataset_name
        self.report       = QualityReport(
            dataset_name  = dataset_name,
            run_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            total_rows    = len(df),
            total_cols    = len(df.columns),
        )
        logger.info(f"Validator initialised: {dataset_name} | {len(df):,} rows × {len(df.columns)} cols")

    # ── 1. NULL CHECKS ────────────────────────────────────
    def check_nulls(
        self,
        critical_cols: List[str],
        warning_threshold_pct: float = 5.0,
        critical_threshold_pct: float = 20.0
    ) -> "DataQualityValidator":

        for col in self.df.columns:
            null_count = self.df[col].isnull().sum()
            null_pct   = null_count / len(self.df) * 100

            if null_count == 0:
                continue

            if col in critical_cols:
                severity = "CRITICAL"
            elif null_pct >= critical_threshold_pct:
                severity = "CRITICAL"
            elif null_pct >= warning_threshold_pct:
                severity = "WARNING"
            else:
                severity = "INFO"

            self.report.issues.append(QualityIssue(
                rule     = "NULL_CHECK",
                column   = col,
                severity = severity,
                count    = int(null_count),
                pct      = round(null_pct, 2),
                details  = f"{null_count:,} nulls ({null_pct:.1f}%)"
            ))
            logger.warning(f"[NULL] {col}: {null_count:,} nulls ({null_pct:.1f}%) [{severity}]")

        return self

    # ── 2. RANGE VALIDATION ───────────────────────────────
    def check_range(
        self,
        rules: Dict[str, Dict]
        # rules format: {"col": {"min": 0, "max": 100, "severity": "CRITICAL"}}
    ) -> "DataQualityValidator":

        for col, rule in rules.items():
            if col not in self.df.columns:
                logger.warning(f"Column '{col}' not found for range check — skipping")
                continue

            numeric_col = pd.to_numeric(self.df[col], errors="coerce")
            violations  = 0

            if "min" in rule:
                violations += (numeric_col < rule["min"]).sum()
            if "max" in rule:
                violations += (numeric_col > rule["max"]).sum()

            # Also flag negative values explicitly
            negative = (numeric_col < 0).sum()

            if violations > 0 or negative > 0:
                severity = rule.get("severity", "WARNING")
                self.report.issues.append(QualityIssue(
                    rule     = "RANGE_VALIDATION",
                    column   = col,
                    severity = severity,
                    count    = int(violations),
                    pct      = round(violations / len(self.df) * 100, 2),
                    details  = f"{violations:,} out-of-range values | range: [{rule.get('min','–')}, {rule.get('max','–')}]"
                ))
                logger.warning(f"[RANGE] {col}: {violations:,} violations [{severity}]")

        return self

    # ── 3. DEDUPLICATION ──────────────────────────────────
    def deduplicate(
        self,
        key_cols:         Optional[List[str]] = None,
        keep:             str = "first"
    ) -> "DataQualityValidator":

        before = len(self.df)
        self.df = self.df.drop_duplicates(subset=key_cols, keep=keep)
        removed = before - len(self.df)

        if removed > 0:
            severity = "CRITICAL" if removed / before > 0.05 else "WARNING"
            self.report.issues.append(QualityIssue(
                rule     = "DEDUPLICATION",
                column   = str(key_cols) if key_cols else "ALL",
                severity = severity,
                count    = removed,
                pct      = round(removed / before * 100, 2),
                details  = f"Removed {removed:,} duplicate rows ({removed/before*100:.1f}%)"
            ))
            logger.info(f"[DEDUP] Removed {removed:,} duplicates ({removed/before*100:.1f}%)")
        else:
            logger.info("[DEDUP] No duplicates found ✅")

        self.report.total_rows = len(self.df)
        return self

    # ── 4. OUTLIER DETECTION ──────────────────────────────
    def detect_outliers(
        self,
        numeric_cols:  Optional[List[str]] = None,
        method:        str   = "iqr",        # "iqr" or "zscore"
        zscore_thresh: float = 3.0,
        iqr_factor:    float = 1.5
    ) -> "DataQualityValidator":

        cols = numeric_cols or self.df.select_dtypes(include=[np.number]).columns.tolist()

        for col in cols:
            series = pd.to_numeric(self.df[col], errors="coerce").dropna()
            if len(series) < 10:
                continue

            if method == "iqr":
                Q1, Q3  = series.quantile(0.25), series.quantile(0.75)
                IQR     = Q3 - Q1
                lower   = Q1 - iqr_factor * IQR
                upper   = Q3 + iqr_factor * IQR
                outliers = ((series < lower) | (series > upper)).sum()
                detail  = f"IQR bounds: [{lower:.2f}, {upper:.2f}]"
            else:
                z_scores = np.abs((series - series.mean()) / series.std())
                outliers  = (z_scores > zscore_thresh).sum()
                detail    = f"Z-score threshold: ±{zscore_thresh}"

            if outliers > 0:
                pct      = outliers / len(series) * 100
                severity = "WARNING" if pct < 5 else "CRITICAL"
                self.report.issues.append(QualityIssue(
                    rule     = f"OUTLIER_{method.upper()}",
                    column   = col,
                    severity = severity,
                    count    = int(outliers),
                    pct      = round(pct, 2),
                    details  = f"{outliers:,} outliers ({pct:.1f}%) | {detail}"
                ))
                if pct > 1:
                    logger.warning(f"[OUTLIER] {col}: {outliers:,} outliers ({pct:.1f}%) [{severity}]")

        return self

    # ── 5. SCHEMA ENFORCEMENT ─────────────────────────────
    def enforce_schema(
        self,
        expected_schema: Dict[str, str]
        # {"col": "int64" | "float64" | "object" | "datetime64"}
    ) -> "DataQualityValidator":

        for col, expected_dtype in expected_schema.items():
            if col not in self.df.columns:
                self.report.issues.append(QualityIssue(
                    rule="SCHEMA", column=col, severity="CRITICAL",
                    count=1, pct=100.0,
                    details=f"Column MISSING from dataset"
                ))
                continue

            actual_dtype = str(self.df[col].dtype)
            if not actual_dtype.startswith(expected_dtype.replace("64","")):
                # Attempt auto-cast
                try:
                    if "int" in expected_dtype:
                        self.df[col] = pd.to_numeric(self.df[col], errors="coerce").astype("Int64")
                    elif "float" in expected_dtype:
                        self.df[col] = pd.to_numeric(self.df[col], errors="coerce")
                    elif "datetime" in expected_dtype:
                        self.df[col] = pd.to_datetime(self.df[col], errors="coerce")
                    logger.info(f"[SCHEMA] Auto-cast {col}: {actual_dtype} → {expected_dtype}")
                except Exception as e:
                    self.report.issues.append(QualityIssue(
                        rule="SCHEMA", column=col, severity="WARNING",
                        count=0, pct=0.0,
                        details=f"Type mismatch: expected {expected_dtype}, got {actual_dtype}"
                    ))

        return self

    # ── 6. CARDINALITY CHECKS ─────────────────────────────
    def check_cardinality(
        self,
        expected_values: Dict[str, List]  # {"status": ["active","inactive"]}
    ) -> "DataQualityValidator":

        for col, valid_vals in expected_values.items():
            if col not in self.df.columns:
                continue
            invalid = ~self.df[col].isin(valid_vals) & self.df[col].notna()
            count   = invalid.sum()
            if count > 0:
                unexpected = self.df.loc[invalid, col].value_counts().head(5).to_dict()
                self.report.issues.append(QualityIssue(
                    rule     = "CARDINALITY",
                    column   = col,
                    severity = "WARNING",
                    count    = int(count),
                    pct      = round(count / len(self.df) * 100, 2),
                    details  = f"Unexpected values: {unexpected}"
                ))
                logger.warning(f"[CARDINALITY] {col}: {count:,} unexpected values")

        return self

    # ── SUMMARY ───────────────────────────────────────────
    def summary(self) -> "DataQualityValidator":
        r = self.report
        print("\n" + "="*60)
        print(f"📊 DATA QUALITY REPORT — {r.dataset_name}")
        print(f"   Run: {r.run_timestamp}")
        print(f"   Rows: {r.total_rows:,} | Cols: {r.total_cols}")
        print("="*60)

        if not r.issues:
            print("✅ All quality checks passed!")
        else:
            for issue in sorted(r.issues, key=lambda x: ["CRITICAL","WARNING","INFO"].index(x.severity)):
                icon = "🔴" if issue.severity=="CRITICAL" else "🟡" if issue.severity=="WARNING" else "🔵"
                print(f"  {icon} [{issue.severity}] {issue.rule} | {issue.column}: {issue.details}")

        print(f"\n  CRITICAL: {r.critical_count} | WARNING: {r.warning_count}")
        print(f"  Status: {'✅ PASSED' if r.passed else '❌ FAILED'}")
        print("="*60 + "\n")
        return self

    def get_clean_data(self) -> pd.DataFrame:
        return self.df

    def get_report(self) -> QualityReport:
        return self.report


# ── USAGE EXAMPLE ─────────────────────────────────────────
if __name__ == "__main__":

    # Simulate an AI training dataset
    np.random.seed(42)
    n = 10000

    sample_data = pd.DataFrame({
        "record_id":   range(n),
        "age":         np.random.randint(18, 80, n).astype(float),
        "income":      np.random.exponential(50000, n),
        "label":       np.random.choice(["positive","negative","neutral", None, "unknown"], n),
        "score":       np.random.uniform(0, 1, n),
        "category":    np.random.choice(["A","B","C","D",None], n),
        "created_at":  pd.date_range("2023-01-01", periods=n, freq="1min"),
    })

    # Inject issues
    sample_data.loc[np.random.choice(n, 500, replace=False), "age"]      = None
    sample_data.loc[np.random.choice(n, 100, replace=False), "income"]   = -999
    sample_data.loc[np.random.choice(n, 50,  replace=False), "score"]    = 999
    sample_data = pd.concat([sample_data, sample_data.iloc[:200]])  # duplicates

    # Run validation pipeline
    validator = DataQualityValidator(sample_data, "ai_training_v1")
    clean_df  = (
        validator
        .enforce_schema({"record_id":"int","age":"float","score":"float","income":"float"})
        .check_nulls(critical_cols=["record_id","label"], warning_threshold_pct=3.0)
        .check_range({
            "age":    {"min": 0,   "max": 120, "severity": "CRITICAL"},
            "income": {"min": 0,   "max": 1e7, "severity": "WARNING"},
            "score":  {"min": 0.0, "max": 1.0, "severity": "CRITICAL"},
        })
        .deduplicate(key_cols=["record_id"])
        .detect_outliers(numeric_cols=["age","income","score"], method="iqr")
        .check_cardinality({"label": ["positive","negative","neutral"]})
        .summary()
        .get_clean_data()
    )

    logger.info(f"Clean dataset shape: {clean_df.shape}")
    logger.info("Framework run complete ✅")
