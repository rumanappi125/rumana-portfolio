"""
ETL Pipeline — PySpark + AWS Redshift + S3
Analyst: Rumana Appi | Client: Target (via E-Mech Solutions)
Description: Scalable multi-terabyte data pipeline for retail analytics
"""

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType,
    DoubleType, TimestampType, LongType
)
from pyspark.sql.window import Window
import logging
import sys
from datetime import datetime

# ── LOGGING ───────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


# ── SPARK SESSION ─────────────────────────────────────────
def create_spark_session(app_name: str = "RetailETL") -> SparkSession:
    """Create optimised Spark session for large-scale processing."""
    spark = (
        SparkSession.builder
        .appName(app_name)
        .config("spark.sql.shuffle.partitions", "400")
        .config("spark.default.parallelism", "400")
        .config("spark.sql.adaptive.enabled", "true")
        .config("spark.sql.adaptive.coalescePartitions.enabled", "true")
        .config("spark.sql.adaptive.skewJoin.enabled", "true")
        .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer")
        .config("spark.sql.parquet.compression.codec", "snappy")
        # Redshift connector
        .config("spark.jars", "redshift-jdbc42.jar,spark-redshift.jar")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")
    logger.info(f"Spark session created: {app_name}")
    return spark


# ── SCHEMAS ───────────────────────────────────────────────
ORDERS_SCHEMA = StructType([
    StructField("order_id",        StringType(),    False),
    StructField("user_id",         StringType(),    False),
    StructField("product_id",      StringType(),    False),
    StructField("category",        StringType(),    True),
    StructField("quantity",        IntegerType(),   True),
    StructField("unit_price",      DoubleType(),    True),
    StructField("discount_pct",    DoubleType(),    True),
    StructField("order_timestamp", TimestampType(), True),
    StructField("device_type",     StringType(),    True),
    StructField("region",          StringType(),    True),
    StructField("payment_method",  StringType(),    True),
    StructField("status",          StringType(),    True),
])

EVENTS_SCHEMA = StructType([
    StructField("event_id",        StringType(),    False),
    StructField("user_id",         StringType(),    False),
    StructField("session_id",      StringType(),    False),
    StructField("event_type",      StringType(),    True),
    StructField("page",            StringType(),    True),
    StructField("event_timestamp", TimestampType(), True),
    StructField("device_type",     StringType(),    True),
    StructField("product_id",      StringType(),    True),
])


# ── INGESTION ─────────────────────────────────────────────
class DataIngestion:
    """Handles reading from S3 in various formats."""

    def __init__(self, spark: SparkSession):
        self.spark = spark

    def read_csv(self, s3_path: str, schema=None) -> "DataFrame":
        logger.info(f"Reading CSV from: {s3_path}")
        return (
            self.spark.read
            .option("header", "true")
            .option("inferSchema", schema is None)
            .schema(schema)
            .csv(s3_path)
        )

    def read_json(self, s3_path: str) -> "DataFrame":
        logger.info(f"Reading JSON from: {s3_path}")
        return (
            self.spark.read
            .option("multiline", "true")
            .json(s3_path)
        )

    def read_parquet(self, s3_path: str) -> "DataFrame":
        logger.info(f"Reading Parquet from: {s3_path}")
        return self.spark.read.parquet(s3_path)


# ── DATA QUALITY ──────────────────────────────────────────
class DataQualityChecker:
    """
    Applies data quality rules:
    - Null checks on critical columns
    - Range validation
    - Deduplication
    """

    def __init__(self, df, table_name: str):
        self.df = df
        self.table_name = table_name
        self.issues = []

    def check_nulls(self, critical_columns: list) -> "DataQualityChecker":
        for col in critical_columns:
            null_count = self.df.filter(F.col(col).isNull()).count()
            if null_count > 0:
                self.issues.append(f"NULL: {col} has {null_count} null values")
                logger.warning(f"[{self.table_name}] NULL check failed: {col} → {null_count} nulls")
        return self

    def check_range(self, col: str, min_val, max_val) -> "DataQualityChecker":
        out_of_range = self.df.filter(
            (F.col(col) < min_val) | (F.col(col) > max_val)
        ).count()
        if out_of_range > 0:
            self.issues.append(f"RANGE: {col} has {out_of_range} values outside [{min_val},{max_val}]")
            logger.warning(f"[{self.table_name}] Range violation: {col} → {out_of_range} records")
        return self

    def deduplicate(self, key_columns: list) -> "DataQualityChecker":
        before = self.df.count()
        self.df = self.df.dropDuplicates(key_columns)
        removed = before - self.df.count()
        if removed > 0:
            logger.info(f"[{self.table_name}] Deduplication: removed {removed} duplicate rows")
        return self

    def report(self):
        if self.issues:
            logger.error(f"[{self.table_name}] Data Quality Issues: {self.issues}")
        else:
            logger.info(f"[{self.table_name}] All data quality checks passed ✅")
        return self.df


# ── TRANSFORMATIONS ───────────────────────────────────────
class OrdersTransformer:
    """Business transformations for orders data."""

    def __init__(self, df):
        self.df = df

    def clean_and_cast(self) -> "OrdersTransformer":
        self.df = (
            self.df
            .withColumn("unit_price",   F.when(F.col("unit_price") <= 0, None).otherwise(F.col("unit_price")))
            .withColumn("quantity",     F.when(F.col("quantity") <= 0, None).otherwise(F.col("quantity")))
            .withColumn("discount_pct", F.when(F.col("discount_pct").isNull(), 0.0).otherwise(F.col("discount_pct")))
            .withColumn("status",       F.upper(F.trim(F.col("status"))))
            .withColumn("category",     F.lower(F.trim(F.col("category"))))
            # Date parts for partitioning
            .withColumn("order_date",   F.to_date(F.col("order_timestamp")))
            .withColumn("order_year",   F.year(F.col("order_timestamp")))
            .withColumn("order_month",  F.month(F.col("order_timestamp")))
            .withColumn("order_week",   F.weekofyear(F.col("order_timestamp")))
        )
        return self

    def add_revenue_metrics(self) -> "OrdersTransformer":
        self.df = (
            self.df
            .withColumn("gross_revenue",
                        F.col("quantity") * F.col("unit_price"))
            .withColumn("discount_amount",
                        F.col("gross_revenue") * F.col("discount_pct") / 100)
            .withColumn("net_revenue",
                        F.col("gross_revenue") - F.col("discount_amount"))
        )
        return self

    def add_customer_features(self) -> "OrdersTransformer":
        window_user = Window.partitionBy("user_id").orderBy("order_timestamp")
        window_user_all = Window.partitionBy("user_id")

        self.df = (
            self.df
            .withColumn("order_rank",
                        F.row_number().over(window_user))
            .withColumn("is_first_order",
                        F.when(F.col("order_rank") == 1, True).otherwise(False))
            .withColumn("total_orders",
                        F.count("order_id").over(window_user_all))
            .withColumn("is_repeat_customer",
                        F.when(F.col("total_orders") > 1, True).otherwise(False))
            .withColumn("days_since_prev_order",
                        F.datediff(
                            F.col("order_date"),
                            F.lag("order_date", 1).over(window_user)
                        ))
        )
        return self

    def build(self):
        return self.df


# ── AGGREGATIONS (Fact Tables) ────────────────────────────
def build_daily_sales_fact(orders_df) -> "DataFrame":
    """Build daily sales fact table for Power BI."""
    return (
        orders_df
        .filter(F.col("status") == "COMPLETED")
        .groupBy("order_date", "category", "region", "device_type", "payment_method")
        .agg(
            F.countDistinct("order_id").alias("total_orders"),
            F.countDistinct("user_id").alias("unique_buyers"),
            F.sum("gross_revenue").alias("gross_revenue"),
            F.sum("net_revenue").alias("net_revenue"),
            F.sum("discount_amount").alias("total_discounts"),
            F.sum("quantity").alias("units_sold"),
            F.avg("net_revenue").alias("avg_order_value"),
            F.countDistinct(
                F.when(F.col("is_first_order"), F.col("user_id"))
            ).alias("new_customers"),
            F.countDistinct(
                F.when(F.col("is_repeat_customer"), F.col("user_id"))
            ).alias("returning_customers"),
        )
        .withColumn("gross_margin_pct",
                    F.round(F.col("net_revenue") / F.nullif(F.col("gross_revenue"), 0) * 100, 2))
        .orderBy("order_date")
    )


def build_funnel_fact(events_df) -> "DataFrame":
    """Build funnel conversion fact table."""
    stages = ["Signup", "Explore", "Checkout", "Payment"]
    return (
        events_df
        .filter(F.col("event_type").isin(stages))
        .groupBy(
            F.to_date("event_timestamp").alias("event_date"),
            "event_type", "device_type"
        )
        .agg(
            F.countDistinct("user_id").alias("unique_users"),
            F.countDistinct("session_id").alias("sessions")
        )
        .withColumn("stage_order",
                    F.when(F.col("event_type") == "Signup",   1)
                    .when(F.col("event_type") == "Explore",   2)
                    .when(F.col("event_type") == "Checkout",  3)
                    .when(F.col("event_type") == "Payment",   4))
        .orderBy("event_date", "stage_order")
    )


# ── REDSHIFT WRITER ───────────────────────────────────────
class RedshiftWriter:
    """Writes DataFrames to AWS Redshift via S3 staging."""

    def __init__(self, redshift_url: str, s3_temp_dir: str, iam_role: str):
        self.redshift_url = redshift_url
        self.s3_temp_dir  = s3_temp_dir
        self.iam_role     = iam_role

    def write(self, df, table: str, mode: str = "append"):
        logger.info(f"Writing to Redshift: {table} (mode={mode})")
        (
            df.write
            .format("io.github.spark_redshift_utils.spark.RedshiftRelation")
            .option("url",          self.redshift_url)
            .option("dbtable",      table)
            .option("tempdir",      self.s3_temp_dir)
            .option("aws_iam_role", self.iam_role)
            .mode(mode)
            .save()
        )
        logger.info(f"✅ Written to Redshift: {table}")

    def write_partitioned(self, df, table: str, partition_cols: list):
        """Write with distribution key for Redshift performance."""
        logger.info(f"Writing partitioned: {table} on {partition_cols}")
        (
            df.write
            .format("io.github.spark_redshift_utils.spark.RedshiftRelation")
            .option("url",              self.redshift_url)
            .option("dbtable",          table)
            .option("tempdir",          self.s3_temp_dir)
            .option("aws_iam_role",     self.iam_role)
            .option("distkey",          partition_cols[0])
            .option("sortkeyspec",      f"SORTKEY({','.join(partition_cols)})")
            .mode("overwrite")
            .save()
        )


# ── MAIN PIPELINE ─────────────────────────────────────────
def run_pipeline(
    s3_orders_path: str,
    s3_events_path: str,
    redshift_url:   str,
    s3_temp_dir:    str,
    iam_role:       str
):
    start = datetime.now()
    logger.info("=" * 60)
    logger.info("Starting Retail ETL Pipeline")
    logger.info("=" * 60)

    spark    = create_spark_session("RetailETL_Target")
    ingester = DataIngestion(spark)
    writer   = RedshiftWriter(redshift_url, s3_temp_dir, iam_role)

    # ── ORDERS ──────────────────────────────────────────
    logger.info("Processing orders...")
    orders_raw = ingester.read_csv(s3_orders_path, ORDERS_SCHEMA)

    orders_clean = (
        DataQualityChecker(orders_raw, "orders")
        .check_nulls(["order_id", "user_id", "product_id"])
        .check_range("unit_price", 0.01, 100000)
        .check_range("quantity", 1, 10000)
        .deduplicate(["order_id"])
        .report()
    )

    orders_transformed = (
        OrdersTransformer(orders_clean)
        .clean_and_cast()
        .add_revenue_metrics()
        .add_customer_features()
        .build()
    )

    daily_sales = build_daily_sales_fact(orders_transformed)
    writer.write_partitioned(daily_sales, "fact_daily_sales", ["order_date", "category"])

    # ── EVENTS ──────────────────────────────────────────
    logger.info("Processing events...")
    events_raw = ingester.read_json(s3_events_path)

    events_clean = (
        DataQualityChecker(events_raw, "events")
        .check_nulls(["event_id", "user_id", "event_timestamp"])
        .deduplicate(["event_id"])
        .report()
    )

    funnel_fact = build_funnel_fact(events_clean)
    writer.write(funnel_fact, "fact_funnel_daily", mode="append")

    elapsed = (datetime.now() - start).seconds
    logger.info(f"Pipeline complete in {elapsed}s ✅")
    spark.stop()


# ── ENTRY POINT ───────────────────────────────────────────
if __name__ == "__main__":
    run_pipeline(
        s3_orders_path = "s3://target-data-lake/raw/orders/",
        s3_events_path = "s3://target-data-lake/raw/events/",
        redshift_url   = "jdbc:redshift://target-cluster.xxx.redshift.amazonaws.com:5439/analytics",
        s3_temp_dir    = "s3://target-data-lake/temp/spark/",
        iam_role       = "arn:aws:iam::123456789:role/RedshiftS3Role"
    )
